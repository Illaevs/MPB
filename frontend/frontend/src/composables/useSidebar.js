import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const SECTIONS_STORAGE_KEY = 'crm-sidebar-sections'

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

function readPersistedSections() {
  if (typeof localStorage === 'undefined') return { ...DEFAULT_SECTIONS }
  try {
    const raw = localStorage.getItem(SECTIONS_STORAGE_KEY)
    const saved = raw ? JSON.parse(raw) : {}
    const merged = { ...DEFAULT_SECTIONS }
    for (const key of Object.keys(DEFAULT_SECTIONS)) {
      if (typeof saved?.[key] === 'boolean') merged[key] = saved[key]
    }
    return merged
  } catch {
    return { ...DEFAULT_SECTIONS }
  }
}

// Глобальное состояние сайдбара — один на всё приложение.
const isSidebarOpen = ref(true)
const isMobileMenuOpen = ref(false)
const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1440)
const collapsedSections = ref(readPersistedSections())

let resizeListener = null
let resizeBound = false

function onResize() {
  viewportWidth.value = window.innerWidth
  if (viewportWidth.value > 1024) {
    isMobileMenuOpen.value = false
  }
}

function bindResize() {
  if (resizeBound || typeof window === 'undefined') return
  resizeBound = true
  resizeListener = onResize
  window.addEventListener('resize', resizeListener, { passive: true })
}

function unbindResize() {
  if (!resizeBound || typeof window === 'undefined') return
  window.removeEventListener('resize', resizeListener)
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

function persistSections() {
  if (typeof localStorage === 'undefined') return
  try {
    localStorage.setItem(SECTIONS_STORAGE_KEY, JSON.stringify(collapsedSections.value))
  } catch { /* localStorage full / disabled — игнорируем */ }
}

function toggleSection(key) {
  collapsedSections.value = {
    ...collapsedSections.value,
    [key]: !collapsedSections.value[key],
  }
  persistSections()
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
