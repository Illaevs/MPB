<template>
  <!-- Нижняя таб-навигация: только на телефоне (≤768). Быстрый доступ к
       частым разделам + «Ещё» открывает полное off-canvas меню (сайдбар),
       так что разделы вне таб-бара остаются доступны. Вкладки скрыты по
       правам (как в сайдбаре). -->
  <nav v-if="isMobileViewport" class="bottom-tabbar" aria-label="Быстрая навигация">
    <router-link
      v-for="t in visibleTabs"
      :key="t.to"
      :to="t.to"
      class="bottom-tabbar__item"
    >
      <i class="fas" :class="t.icon"></i>
      <span>{{ t.label }}</span>
    </router-link>
    <button
      type="button"
      class="bottom-tabbar__item bottom-tabbar__more"
      :class="{ 'is-active': isMobileMenuOpen }"
      :aria-expanded="isMobileMenuOpen ? 'true' : 'false'"
      @click="toggleMobileMenu"
    >
      <i class="fas fa-bars"></i>
      <span>Ещё</span>
    </button>
  </nav>
</template>

<script>
import { computed } from 'vue'
import { useSidebar } from '../../composables/useSidebar'
import { hasSectionAccess } from '../../utils/permissions'

// Дефолтный набор частых разделов CRM. Легко поменять список здесь.
// access — ключ секции прав (как в config/nav.js); null — всегда видим.
const TABS = [
  { to: '/', icon: 'fa-home', label: 'Главная', access: null },
  { to: '/tasks', icon: 'fa-tasks', label: 'Задачи', access: 'tasks' },
  { to: '/projects', icon: 'fa-project-diagram', label: 'Проекты', access: 'projects' },
  { to: '/leads', icon: 'fa-bullhorn', label: 'Лиды', access: 'leads' },
]

export default {
  name: 'BottomTabBar',
  setup() {
    const { isMobileViewport, isMobileMenuOpen, toggleMobileMenu } = useSidebar()
    const visibleTabs = computed(() =>
      TABS.filter((t) => !t.access || hasSectionAccess(t.access))
    )
    return { isMobileViewport, isMobileMenuOpen, toggleMobileMenu, visibleTabs }
  },
}
</script>

<style scoped>
.bottom-tabbar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1090;
  display: flex;
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
  /* Безопасная зона под жест-баром iOS. */
  padding-bottom: env(safe-area-inset-bottom);
  box-shadow: 0 -2px 12px rgba(15, 23, 42, 0.08);
}
.bottom-tabbar__item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  min-height: 52px;
  padding: 6px 2px;
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--color-text-muted);
  font-size: 0.66rem;
  font-weight: 600;
  font-family: inherit;
  text-decoration: none;
}
.bottom-tabbar__item i {
  font-size: 1.15rem;
}
.bottom-tabbar__item.router-link-active,
.bottom-tabbar__item.is-active {
  color: var(--color-primary);
}
</style>
