import { ref, onBeforeUnmount } from 'vue'

const STORAGE_KEY = 'crm-theme'

/**
 * Глобальный singleton темы. Применяется к <html data-theme="...">.
 * Слушает system prefers-color-scheme до тех пор, пока пользователь
 * не выбрал тему явно.
 */
const theme = ref('light')
let initialised = false
let mq = null
let mqListener = null
let userOverride = false

function applyTheme(value) {
  theme.value = value
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-theme', value)
  }
}

function initOnce() {
  if (initialised || typeof window === 'undefined') return
  initialised = true

  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved === 'dark' || saved === 'light') {
    userOverride = true
    applyTheme(saved)
  } else if (window.matchMedia) {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    applyTheme(prefersDark ? 'dark' : 'light')
  } else {
    applyTheme('light')
  }

  if (window.matchMedia) {
    mq = window.matchMedia('(prefers-color-scheme: dark)')
    mqListener = (event) => {
      if (userOverride) return
      applyTheme(event.matches ? 'dark' : 'light')
    }
    if (mq.addEventListener) mq.addEventListener('change', mqListener)
    else if (mq.addListener) mq.addListener(mqListener)
  }
}

export function useTheme() {
  initOnce()

  function setTheme(value) {
    if (value !== 'dark' && value !== 'light') return
    userOverride = true
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, value)
    }
    applyTheme(value)
  }

  function toggleTheme() {
    setTheme(theme.value === 'dark' ? 'light' : 'dark')
  }

  function clearOverride() {
    userOverride = false
    if (typeof window !== 'undefined') {
      localStorage.removeItem(STORAGE_KEY)
      if (window.matchMedia) {
        applyTheme(window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
      }
    }
  }

  onBeforeUnmount(() => {
    // глобальный singleton — слушатели не снимаем при размонтировании,
    // они живут на всё время жизни приложения.
  })

  return { theme, setTheme, toggleTheme, clearOverride }
}
