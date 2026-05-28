<template>
  <button class="hamburger-btn" @click="toggleMobileMenu">
    <i class="fas" :class="isMobileMenuOpen ? 'fa-times' : 'fa-bars'"></i>
  </button>
  <div class="mobile-overlay" :class="{ active: isMobileMenuOpen }" v-modal-close="closeMobileMenu"></div>

  <aside class="sidebar" :class="sidebarClasses">
    <div class="sidebar-header">
      <div v-show="showSidebarExpandedContent" class="brand-lockup">
        <div class="brand-text">
          <span class="brand-text__primary">{{ appBrandPrimary }}</span>
          <span v-if="appBrandSecondary" class="brand-text__secondary"> {{ appBrandSecondary }}</span>
        </div>
      </div>
      <button class="sidebar-toggle" type="button" @click="toggleSidebar">
        <i class="fas" :class="showSidebarExpandedContent ? 'fa-chevron-left' : 'fa-bars'"></i>
      </button>
    </div>

    <nav class="sidebar-nav" @click="handleSidebarNavClick">
      <!-- Pinned (Главная и т.п.) -->
      <router-link
        v-for="item in pinnedVisible"
        :key="item.to"
        :to="item.to"
        class="nav-link"
      >
        <i class="fas" :class="item.icon"></i>
        <span v-show="showSidebarExpandedContent">{{ item.label }}</span>
      </router-link>

      <!-- Избранное (закреплённые пользователем пункты, drag-сортировка) -->
      <div
        v-if="showSidebarExpandedContent && favoritesModel.length"
        class="nav-section nav-section--fav"
      >
        <div class="nav-section-toggle nav-section-toggle--static">
          <span class="nav-section-title">Избранное</span>
        </div>
        <div class="nav-section-items">
          <draggable
            v-model="favoritesModel"
            item-key="to"
            handle=".nav-fav-grip"
            :animation="150"
          >
            <template #item="{ element }">
              <div class="nav-link-row">
                <router-link :to="element.to" class="nav-link nav-link--fav">
                  <i class="nav-fav-grip fas fa-grip-lines-vertical" title="Перетащите"></i>
                  <i class="fas" :class="element.icon"></i>
                  <span>{{ element.label }}</span>
                </router-link>
                <button
                  type="button"
                  class="nav-pin is-pinned"
                  title="Открепить"
                  @click.prevent="unpin(element.to)"
                >
                  <i class="fas fa-thumbtack"></i>
                </button>
              </div>
            </template>
          </draggable>
        </div>
      </div>

      <!-- Группы со сворачиваемыми заголовками (drag-сортировка разделов) -->
      <draggable
        v-show="showSidebarExpandedContent"
        v-model="sectionModel"
        tag="div"
        class="nav-sections"
        item-key="key"
        handle=".nav-sec-grip"
        :animation="150"
      >
        <template #item="{ element: section }">
          <div class="nav-section">
            <div class="nav-section__bar">
              <i
                class="fas fa-grip-vertical nav-sec-grip"
                title="Перетащить раздел"
              ></i>
              <button class="nav-section-toggle" @click="toggleSection(section.key)">
                <span class="nav-section-title">{{ section.title }}</span>
                <i
                  class="fas fa-chevron-down nav-section-arrow"
                  :class="{ collapsed: collapsedSections[section.key] }"
                ></i>
              </button>
            </div>
            <transition name="section-collapse">
              <div v-show="!collapsedSections[section.key]" class="nav-section-items">
                <draggable
                  :list="visibleItems(section)"
                  tag="div"
                  item-key="to"
                  handle=".nav-item-grip"
                  :animation="150"
                  @change="onItemMoved(section, $event)"
                >
                  <template #item="{ element: item }">
                    <div class="nav-link-row">
                      <i
                        class="fas fa-grip-vertical nav-item-grip"
                        title="Перетащить пункт"
                      ></i>
                      <router-link :to="item.to" class="nav-link">
                        <i class="fas" :class="item.icon"></i>
                        <span>{{ item.label }}</span>
                      </router-link>
                      <button
                        type="button"
                        class="nav-pin"
                        :class="{ 'is-pinned': isPinned(item.to) }"
                        :title="isPinned(item.to) ? 'Открепить' : 'Закрепить в избранном'"
                        @click.prevent="togglePinned(item.to)"
                      >
                        <i class="fas fa-thumbtack"></i>
                      </button>
                    </div>
                  </template>
                </draggable>
              </div>
            </transition>
          </div>
        </template>
      </draggable>

      <!-- Сжатый сайдбар: все иконки одним списком, без разделов -->
      <template v-if="showCollapsedSidebarIcons">
        <router-link
          v-for="item in flatVisible"
          :key="`flat-${item.to}`"
          :to="item.to"
          class="nav-link"
        >
          <i class="fas" :class="item.icon"></i>
        </router-link>
      </template>
    </nav>

    <div class="sidebar-footer">
      <button class="sidebar-footer__action" type="button" @click="toggleTheme">
        <i class="fas" :class="theme === 'dark' ? 'fa-moon' : 'fa-sun'"></i>
        <span v-show="showSidebarExpandedContent">{{ theme === 'dark' ? 'Dark' : 'Light' }}</span>
      </button>
    </div>
  </aside>
</template>

<script>
import { computed } from 'vue'
import draggable from 'vuedraggable'
import { useSidebar } from '../../composables/useSidebar'
import { useTheme } from '../../composables/useTheme'
import { useUiPreferences } from '../../composables/useUiPreferences'
import { hasSectionAccess } from '../../utils/permissions'
import { appBrandPrimary, appBrandSecondary } from '../../config/appVariant'
import { navPinned, navSections, navFlatItems, findNavLink } from '../../config/nav'

export default {
  name: 'AppSidebar',
  components: { draggable },
  props: {
    /**
     * Реактивная матрица прав. AppSidebar не подписывается на authStore
     * напрямую — App.vue передаёт permissions, чтобы изоляция сохранялась.
     */
    permissions: { type: Object, default: () => ({}) },
  },
  setup(props) {
    const {
      isMobileMenuOpen,
      collapsedSections,
      showSidebarExpandedContent,
      showCollapsedSidebarIcons,
      sidebarClasses,
      toggleSidebar,
      toggleMobileMenu,
      closeMobileMenu,
      toggleSection,
      handleSidebarNavClick,
    } = useSidebar()
    const { theme, toggleTheme } = useTheme()
    const {
      prefs: uiPrefs,
      isPinned,
      togglePinned,
      setPinnedOrder,
      unpin,
      getPinnedMeta,
      getSectionOrder,
      setSectionOrder,
      getItemOrder,
      setItemOrder,
    } = useUiPreferences()

    // Стабильная сортировка по сохранённому порядку ключей;
    // неизвестные (новые) элементы сохраняют исходную позицию в хвосте.
    const applyOrder = (list, savedOrder, keyOf) => {
      if (!Array.isArray(savedOrder) || !savedOrder.length) return list
      const idx = new Map(savedOrder.map((k, i) => [k, i]))
      return list
        .map((el, i) => ({ el, i }))
        .sort((a, b) => {
          const ia = idx.has(keyOf(a.el)) ? idx.get(keyOf(a.el)) : Infinity
          const ib = idx.has(keyOf(b.el)) ? idx.get(keyOf(b.el)) : Infinity
          return ia - ib || a.i - b.i
        })
        .map((x) => x.el)
    }

    const canAccess = (key) => {
      if (!key) return true
      return hasSectionAccess(key, props.permissions)
    }

    // Избранное: резолвим `to` из prefs в объекты ссылок, фильтруем по
    // доступу. v-model на draggable пишет новый порядок обратно.
    const favoritesModel = computed({
      get: () =>
        (Array.isArray(uiPrefs.nav.pinned) ? uiPrefs.nav.pinned : [])
          .map((to) => {
            const link = findNavLink(to)
            if (link) return link
            // Закреплённая сущность (проект/договор) — берём подпись/иконку
            // из pinnedMeta, чтобы не дёргать API ради названия.
            const meta = getPinnedMeta(to)
            if (meta) return { to, label: meta.label, icon: meta.icon, access: null }
            return null
          })
          .filter((link) => link && canAccess(link.access)),
      set: (list) => setPinnedOrder((list || []).map((l) => l.to)),
    })

    const pinnedVisible = computed(() =>
      navPinned.filter((item) => canAccess(item.access))
    )

    // Группа отображается только если у пользователя есть доступ хотя бы к
    // одной её вкладке. requireAny (если задан) — дополнительный необходимый
    // фильтр, но сам по себе пустой заголовок он не покажет. Это убирает
    // «висящие» пустые категории для ролей с 2–3 вкладками.
    const sectionsVisible = computed(() => {
      const ordered = applyOrder(navSections, getSectionOrder(), (s) => s.key)
      return ordered.filter((section) => {
        if (section.requireAny?.length && !section.requireAny.some((key) => canAccess(key))) {
          return false
        }
        return section.items.some((item) => canAccess(item.access))
      })
    })

    // v-model для draggable разделов: пишем полный порядок ключей
    // (скрытые по доступу — в хвост, их относительный порядок не важен).
    const sectionModel = computed({
      get: () => sectionsVisible.value,
      set: (list) => {
        const visibleKeys = (list || []).map((s) => s.key)
        const hiddenKeys = navSections
          .map((s) => s.key)
          .filter((k) => !visibleKeys.includes(k))
        setSectionOrder([...visibleKeys, ...hiddenKeys])
      },
    })

    const visibleItems = (section) =>
      applyOrder(section.items, getItemOrder(section.key), (it) => it.to)
        .filter((item) => canAccess(item.access))

    // Перетаскивание пунктов внутри раздела (режим :list — берём индексы
    // из события и пересобираем порядок от источника правды).
    const onItemMoved = (section, evt) => {
      const moved = evt && evt.moved
      if (!moved || moved.oldIndex == null || moved.newIndex == null) return
      const order = visibleItems(section).map((i) => i.to)
      const [m] = order.splice(moved.oldIndex, 1)
      order.splice(moved.newIndex, 0, m)
      const hidden = section.items
        .map((i) => i.to)
        .filter((to) => !order.includes(to))
      setItemOrder(section.key, [...order, ...hidden])
    }

    const flatVisible = computed(() =>
      navFlatItems.filter((item) => canAccess(item.access))
    )

    return {
      appBrandPrimary,
      appBrandSecondary,
      isMobileMenuOpen,
      collapsedSections,
      showSidebarExpandedContent,
      showCollapsedSidebarIcons,
      sidebarClasses,
      toggleSidebar,
      toggleMobileMenu,
      closeMobileMenu,
      toggleSection,
      handleSidebarNavClick,
      theme,
      toggleTheme,
      pinnedVisible,
      sectionsVisible,
      sectionModel,
      flatVisible,
      visibleItems,
      onItemMoved,
      favoritesModel,
      isPinned,
      togglePinned,
      unpin,
    }
  },
}
</script>

<style scoped>
/* ============================================================
   Sidebar (frame, brand, header, toggle, footer)
   Скопировано из App.vue для сохранения исходной специфичности
   (раньше работало через [data-v-xxx] App.vue; теперь sidebar
   живёт здесь — стили тоже).
   ============================================================ */
.sidebar {
  width: 250px;
  padding: 10px 0 12px;
  background: rgba(0, 0, 0, 0.25);
  border-right: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(1px) saturate(100%);
  -webkit-backdrop-filter: blur(1px) saturate(100%);
  transition: width var(--dur-slow) var(--ease-out);
}

:root[data-theme="dark"] .sidebar {
  background: rgba(15, 23, 42, 0.76);
  border-right-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.22);
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 0px;
  padding: 0 12px 4px 45px;
  margin-bottom: 4px;
}

.brand-lockup {
  display: flex;
  align-items: center;
  min-width: 0;
}

.brand-text {
  display: inline-flex;
  align-items: baseline;
  gap: 2px;
  min-width: 0;
  font-size: 22px;
  font-weight: 700;
  line-height: 1.1;
  white-space: nowrap;
}

.brand-text__primary {
  color: #d31313;
}

.brand-text__secondary {
  color: #111111;
}

.sidebar-toggle {
  width: 20px;
  height: 20px;
  margin-left: auto;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--color-text-muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition:
    background var(--dur-fast) ease,
    color var(--dur-fast) ease,
    border-color var(--dur-fast) ease,
    transform var(--dur-fast) var(--ease-out);
}

.sidebar-toggle:hover {
  background: rgba(255, 255, 255, 0.56);
  color: var(--color-text);
}

:root[data-theme="dark"] .sidebar-toggle {
  background: rgba(15, 23, 42, 0.56);
}

:root[data-theme="dark"] .sidebar-toggle:hover {
  background: rgba(15, 23, 42, 0.82);
}

.sidebar.collapsed {
  width: 62px;
}

.sidebar.collapsed .nav-link span {
  display: none;
}

.sidebar.collapsed .sidebar-header {
  justify-content: center;
  padding-left: 0;
  padding-right: 0;
}

.sidebar.collapsed .sidebar-header .brand-lockup {
  display: none;
}

.sidebar.collapsed .sidebar-toggle {
  margin-left: 0;
}

.sidebar.collapsed .nav-link {
  justify-content: center;
  padding: 8px 0;
  margin: 2px 10px;
}

.sidebar.collapsed .nav-link i {
  margin-right: 0;
}

.sidebar-footer {
  margin-top: auto;
  padding: 12px 12px 0;
  border-top: 1px solid rgba(255, 255, 255, 0.35);
}

.sidebar-footer__action {
  width: 100%;
  min-height: 30px;
  padding: 0 10px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: rgba(255, 255, 255, 0.9);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 14px;
  font-weight: var(--fw-medium);
  transition:
    background var(--dur-fast) ease,
    color var(--dur-fast) ease,
    border-color var(--dur-fast) ease;
}

.sidebar-footer__action:hover {
  background: rgba(255, 255, 255, 0.48);
  color: var(--color-text);
}

:root[data-theme="dark"] .sidebar-footer__action {
  background: rgba(15, 23, 42, 0.56);
}

:root[data-theme="dark"] .sidebar-footer__action:hover {
  background: rgba(15, 23, 42, 0.82);
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  margin: 2px 8px;
  border-left: 3px solid transparent;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.92);
  text-decoration: none;
  font-size: 15px;
  font-weight: var(--fw-medium);
  line-height: 1.15;
  transition:
    background var(--dur-fast) ease,
    color var(--dur-fast) ease,
    border-color var(--dur-fast) ease,
    transform var(--dur-fast) var(--ease-out);
}

.nav-link i {
  width: 14px;
  font-size: 12px;
  text-align: center;
  color: inherit;
  flex-shrink: 0;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.48);
  color: var(--color-text);
  transform: translateX(1px);
}

:root[data-theme="dark"] .nav-link:hover {
  background: rgba(15, 23, 42, 0.56);
}

.nav-link.router-link-active {
  background: #e7f0ff;
  border-left-color: transparent;
  color: var(--color-primary);
  font-weight: var(--fw-semibold);
}

.sidebar.collapsed .nav-link.router-link-active {
  border-left-color: transparent;
}

.nav-link:focus,
.nav-link:focus-visible {
  outline: none;
  box-shadow: none;
}

/* ============================================================
   Collapsible nav-section headers + collapse animation
   ============================================================ */
.nav-section {
  margin-top: 10px;
}

.nav-section-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 8px 12px 3px;
  margin: 0;
  border: none;
  background: none;
  cursor: pointer;
  user-select: none;
  -webkit-user-select: none;
}

.nav-section-toggle:focus,
.nav-section-toggle:focus-visible {
  outline: none;
  box-shadow: none;
}

.nav-section-toggle:hover .nav-section-title {
  opacity: 0.85;
}

.nav-section-toggle:hover .nav-section-arrow {
  opacity: 0.7;
}

.nav-section-title {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.62);
  opacity: 1;
  transition: opacity 0.15s ease;
  line-height: 1;
}

.nav-section-arrow {
  font-size: 12px;
  color: rgb(255, 255, 255, 0.62);
  opacity: 1;
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.15s ease;
  flex-shrink: 0;
}

.nav-section-arrow.collapsed {
  transform: rotate(-90deg);
}

.nav-section-items {
  overflow: hidden;
  padding-bottom: 4px;
}

.section-collapse-enter-active,
.section-collapse-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 500px;
  opacity: 1;
}

.section-collapse-enter-from,
.section-collapse-leave-to {
  max-height: 0;
  opacity: 0;
}

/* ============================================================
   Pinned / favorites (pin-кнопка + drag-сортировка)
   ============================================================ */
.nav-link-row {
  position: relative;
  display: flex;
  align-items: center;
}

.nav-link-row .nav-link {
  flex: 1 1 auto;
  min-width: 0;
}

.nav-pin {
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 22px;
  height: 22px;
  padding: 0;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: rgba(255, 255, 255, 0.55);
  font-size: 11px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  cursor: pointer;
  transition: opacity 0.15s ease, background 0.15s ease, color 0.15s ease;
}

.nav-link-row:hover .nav-pin {
  opacity: 1;
}

.nav-pin:hover {
  background: rgba(255, 255, 255, 0.22);
  color: #fff;
}

.nav-pin.is-pinned {
  opacity: 1;
  color: var(--color-primary);
}

.nav-section-toggle--static {
  cursor: default;
  padding-bottom: 3px;
}

.nav-fav-grip {
  cursor: grab;
  opacity: 0.5;
}

.nav-fav-grip:active {
  cursor: grabbing;
}

.nav-link--fav {
  padding-right: 28px;
}

/* drag-сортировка разделов и пунктов меню.
   Грипы позиционируются абсолютно — не занимают место в потоке,
   поэтому исходные отступы заголовков/пунктов сохраняются. */
.nav-section__bar {
  position: relative;
}

.nav-sec-grip {
  position: absolute;
  left: 0;
  top: 9px;
  width: 10px;
  font-size: 10px;
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
  opacity: 0;
  cursor: grab;
  transition: opacity 0.15s ease;
  z-index: 1;
}

.nav-section:hover .nav-sec-grip {
  opacity: 0.7;
}

.nav-sec-grip:active {
  cursor: grabbing;
}

.nav-item-grip {
  position: absolute;
  right: 38px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.42);
  opacity: 0;
  cursor: grab;
  transition: opacity 0.15s ease;
  z-index: 1;
}

.nav-link-row:hover .nav-item-grip {
  opacity: 0.7;
}

.nav-item-grip:active {
  cursor: grabbing;
}

.sortable-ghost {
  opacity: 0.4;
}

/* ============================================================
   Responsive: tablet / phone
   ============================================================ */
@media (max-width: 1024px) {
  .sidebar:not(.collapsed) {
    width: var(--app-shell-sidebar-width);
  }

  .sidebar:not(.collapsed) .brand-text {
    display: block;
  }

  .sidebar:not(.collapsed) .nav-link span {
    display: inline;
  }

  .sidebar:not(.collapsed) .sidebar-header {
    justify-content: space-between;
    padding: 0 20px;
  }

  .sidebar:not(.collapsed) .sidebar-toggle {
    margin-left: auto;
  }
}

@media (max-width: 768px) {
  .sidebar,
  .sidebar.collapsed {
    width: min(86vw, 320px);
  }

  .sidebar .brand-text {
    display: block;
  }

  .sidebar .nav-link span {
    display: inline;
  }

  .sidebar .sidebar-header {
    justify-content: space-between;
    padding: 0 20px 12px;
  }
}
</style>
