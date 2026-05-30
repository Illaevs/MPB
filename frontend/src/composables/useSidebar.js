import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useUiPreferences } from './useUiPreferences'

const DEFAULT_SECTIONS = {
  work: false,
  comms: false,
  finance: false,
  docs: false,
  customer: false,
  contragents: false,
  subcontractor: false,
  admin: false,
}

// Свёрнутые разделы меню теперь живут в едином хранилище настроек
// (useUiPreferences: гибрид localStorage + бэкенд-синхронизация).
const { getCollapsedSections, setCollapsedSections } = useUiPreferences()

// Глобальное состояние сайдбара — один на всё приложение.
const isSidebarOpen = ref(true)
const isMobileMenuOpen = ref(false)
const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1440)
const collapsedSections = computed(() => {
  const saved = getCollapsedSections()
  const merged = { ...DEFAULT_SECTIONS }
  for (const key of Object.keys(DEFAULT_SECTIONS)) {
    if (typeof saved?.[key] === 'boolean') merged[key] = saved[key]
  }
  return merged
})

let resizeListener = null
let resizeBound = false

function onResize() {
  viewportWidth.value = window.innerWidth
  if (viewportWidth.value > 1024) {
    isMobileMenuOpen.value = false
  }
}

// Esc закрывает открытое off-canvas меню (доступность/удобство).
function onKeydown(e) {
  if (e.key === 'Escape' && isMobileMenuOpen.value) {
    isMobileMenuOpen.value = false
  }
}

// Пока мобильное меню открыто — блокируем скролл фона, чтобы контент
// под оверлеем не «уезжал» при свайпе. Реальный скролл-контейнер —
// `.content-body` (body глобально overflow:hidden), его и запираем;
// body трогаем заодно, на всякий случай. Глобальный синглтон-watcher.
if (typeof document !== 'undefined') {
  watch(isMobileMenuOpen, (open) => {
    const scroller = document.querySelector('.content-body')
    if (scroller) scroller.style.overflow = open ? 'hidden' : ''
    document.body.style.overflow = open ? 'hidden' : ''
  })
}

function bindResize() {
  if (resizeBound || typeof window === 'undefined') return
  resizeBound = true
  resizeListener = onResize
  window.addEventListener('resize', resizeListener, { passive: true })
  window.addEventListener('keydown', onKeydown)
}

function unbindResize() {
  if (!resizeBound || typeof window === 'undefined') return
  window.removeEventListener('resize', resizeListener)
  window.removeEventListener('keydown', onKeydown)
  resizeListener = null
  resizeBound = false
}

const isMobileViewport = computed(() => viewportWidth.value <= 768)
const isTabletViewport = computed(() => viewportWidth.value <= 1024)
const showSidebarExpandedContent = computed(
  () => isMobileViewport.value || isSidebarOpen.value || isMobileMenuOpen.value
)
const showCollapsedSidebarIcons = computed(
  () => !showSidebarExpandedContent.value && !isMobileViewport.value
)
const sidebarClasses = computed(() => ({
  collapsed: !showSidebarExpandedContent.value,
  open: isMobileMenuOpen.value,
}))

function toggleSection(key) {
  setCollapsedSections({
    ...collapsedSections.value,
    [key]: !collapsedSections.value[key],
  })
}

function toggleSidebar() {
  if (isMobileViewport.value) {
    isMobileMenuOpen.value = !isMobileMenuOpen.value
    return
  }
  isSidebarOpen.value = !isSidebarOpen.value
}

function toggleMobileMenu() {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

function closeMobileMenu() {
  isMobileMenuOpen.value = false
}

function handleSidebarNavClick(event) {
  const link = event?.target?.closest?.('a')
  if (link) closeMobileMenu()
}

export function useSidebar() {
  onMounted(bindResize)
  onBeforeUnmount(() => {
    // Слушатель глобальный — снимаем только если компонент-владелец
    // последний; для простоты оставляем висящим. Никаких утечек,
    // т.к. ссылок на компонент он не держит.
  })

  return {
    // state
    isSidebarOpen,
    isMobileMenuOpen,
    viewportWidth,
    collapsedSections,
    // computed
    isMobileViewport,
    isTabletViewport,
    showSidebarExpandedContent,
    showCollapsedSidebarIcons,
    sidebarClasses,
    // actions
    toggleSidebar,
    toggleMobileMenu,
    closeMobileMenu,
    toggleSection,
    handleSidebarNavClick,
  }
}

// Экспорт для случаев, когда нужно «снять» слушатель явно (например, в тестах).
export function __teardownSidebar() {
  unbindResize()
}
