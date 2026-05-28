<template>
  <button class="hamburger-btn" @click="toggleMobileMenu">
    <i class="fas" :class="isMobileMenuOpen ? 'fa-times' : 'fa-bars'"></i>
  </button>
  <div class="mobile-overlay" :class="{ active: isMobileMenuOpen }" @click="closeMobileMenu"></div>

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

      <!-- Группы со сворачиваемыми заголовками -->
      <div
        v-for="section in sectionsVisible"
        :key="section.key"
        v-show="showSidebarExpandedContent"
        class="nav-section"
      >
        <button class="nav-section-toggle" @click="toggleSection(section.key)">
          <span class="nav-section-title">{{ section.title }}</span>
          <i
            class="fas fa-chevron-down nav-section-arrow"
            :class="{ collapsed: collapsedSections[section.key] }"
          ></i>
        </button>
        <transition name="section-collapse">
          <div v-show="!collapsedSections[section.key]" class="nav-section-items">
            <router-link
              v-for="item in visibleItems(section)"
              :key="item.to"
              :to="item.to"
              class="nav-link"
            >
              <i class="fas" :class="item.icon"></i>
              <span>{{ item.label }}</span>
            </router-link>
          </div>
        </transition>
      </div>

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
import { useSidebar } from '../../composables/useSidebar'
import { useTheme } from '../../composables/useTheme'
import { hasSectionAccess } from '../../utils/permissions'
import { appBrandPrimary, appBrandSecondary } from '../../config/appVariant'
import { navPinned, navSections, navFlatItems } from '../../config/nav'

export default {
  name: 'AppSidebar',
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

    const canAccess = (key) => {
      if (!key) return true
      return hasSectionAccess(key, props.permissions)
    }

    const pinnedVisible = computed(() =>
      navPinned.filter((item) => canAccess(item.access))
    )

    const sectionsVisible = computed(() =>
      navSections.filter((section) => {
        if (section.requireAny?.length) {
          return section.requireAny.some((key) => canAccess(key))
        }
        return section.items.some((item) => canAccess(item.access))
      })
    )

    const visibleItems = (section) =>
      section.items.filter((item) => canAccess(item.access))

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
      flatVisible,
      visibleItems,
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
  border-left-color: var(--color-primary);
  color: var(--color-primary);
  font-weight: var(--fw-semibold);
}

.sidebar.collapsed .nav-link.router-link-active {
  border-left-color: transparent;
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
