import { reactive, computed, watch } from 'vue'
import { api } from '../services/api'

/**
 * Единый источник правды по персональным настройкам интерфейса.
 *
 * Гибридное хранение:
 *  - localStorage (`crm-ui-prefs`) — мгновенный кэш, применяется до ответа сети;
 *  - бэкенд (`user.ui_preferences` через PATCH /api/v1/users/me/ui-preferences) —
 *    синхронизация между устройствами, как у обоев.
 *
 * Старые ключи (`crm-theme`, `ui-pref-brightness`, `ui-pref-bar-blur`,
 * `crm-sidebar-sections`) один раз мигрируются в новый объект.
 */

const LOCAL_KEY = 'crm-ui-prefs'
const LEGACY_THEME_KEY = 'crm-theme'
const LEGACY_BRIGHTNESS_KEY = 'ui-pref-brightness'
const LEGACY_BLUR_KEY = 'ui-pref-bar-blur'
const LEGACY_SIDEBAR_KEY = 'crm-sidebar-sections'

const SYNC_DEBOUNCE_MS = 800

const DEFAULTS = () => ({
  appearance: {
    themeMode: 'auto', // 'light' | 'dark' | 'auto'
    accent: null, // null = токен по умолчанию; иначе hex
    brightness: 100, // 50..150 (%)
    barBlur: 1, // 0..24 px
    density: 'comfortable', // 'comfortable' | 'compact'
    fontScale: 100, // 80..130 (%)
    reducedMotion: false,
    highContrast: false,
  },
  wallpaper: { mode: 'image', presetId: null, color: null, gradient: null, blur: 0, dim: 0 },
  nav: {
    pinned: [],
    order: [],
    collapsedSections: {},
    pinnedMeta: {},
    sectionOrder: [],
    itemOrder: {},
  },
  startPage: null,
  notifications: {
    pollSeconds: 30,
    // Звуковые уведомления — два независимых тумблера.
    // soundEnabled          — общий bell (любые системные пуши)
    // messengerSoundEnabled — новые сообщения в мессенджере
    soundEnabled: true,
    messengerSoundEnabled: true,
  },
  locale: { dateFormat: null, numberFormat: null, timezone: null },
  tableViews: {},
  dashboard: { hidden: [], sideOrder: ['portfolio', 'tasks', 'actions'] },
})

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v))

function isPlainObject(v) {
  return v != null && typeof v === 'object' && !Array.isArray(v)
}

/** Глубокий мёрж patch в target. Вложенные объекты сливаются, остальное — заменяется. */
function deepMerge(target, patch) {
  if (!isPlainObject(patch)) return target
  for (const key of Object.keys(patch)) {
    const value = patch[key]
    if (isPlainObject(value) && isPlainObject(target[key])) {
      deepMerge(target[key], value)
    } else {
      target[key] = value
    }
  }
  return target
}

// ---- Глобальный singleton ----
const prefs = reactive(DEFAULTS())

let initialised = false
let canSync = false
let syncTimer = null
let suppressWatch = false
let systemThemeMq = null

function safeLocalGet(key) {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function safeLocalSet(key, value) {
  try {
    localStorage.setItem(key, value)
  } catch {
    /* приватный режим / квота — игнорируем */
  }
}

function safeLocalRemove(key) {
  try {
    localStorage.removeItem(key)
  } catch {
    /* ignore */
  }
}

function writeLocal() {
  safeLocalSet(LOCAL_KEY, JSON.stringify(prefs))
}

function migrateLegacy() {
  const patch = {}

  const legacyTheme = safeLocalGet(LEGACY_THEME_KEY)
  if (legacyTheme === 'dark' || legacyTheme === 'light') {
    patch.appearance = { ...(patch.appearance || {}), themeMode: legacyTheme }
  }

  const legacyBrightness = Number(safeLocalGet(LEGACY_BRIGHTNESS_KEY))
  if (Number.isFinite(legacyBrightness) && legacyBrightness >= 50 && legacyBrightness <= 150) {
    patch.appearance = { ...(patch.appearance || {}), brightness: legacyBrightness }
  }

  const legacyBlur = Number(safeLocalGet(LEGACY_BLUR_KEY))
  if (Number.isFinite(legacyBlur) && legacyBlur >= 0 && legacyBlur <= 24) {
    patch.appearance = { ...(patch.appearance || {}), barBlur: legacyBlur }
  }

  const legacySidebarRaw = safeLocalGet(LEGACY_SIDEBAR_KEY)
  if (legacySidebarRaw) {
    try {
      const parsed = JSON.parse(legacySidebarRaw)
      if (isPlainObject(parsed)) {
        patch.nav = { collapsedSections: parsed }
      }
    } catch {
      /* битый ключ — пропускаем */
    }
  }

  if (Object.keys(patch).length) {
    deepMerge(prefs, patch)
  }
}

function loadLocal() {
  const raw = safeLocalGet(LOCAL_KEY)
  if (!raw) {
    // Нет нового ключа — пробуем поднять старые настройки.
    migrateLegacy()
    writeLocal()
    return
  }
  try {
    const parsed = JSON.parse(raw)
    if (isPlainObject(parsed)) deepMerge(prefs, parsed)
  } catch {
    /* битый кэш — остаёмся на дефолтах */
  }
}

function resolveSystemDark() {
  return Boolean(
    typeof window !== 'undefined' &&
      window.matchMedia &&
      window.matchMedia('(prefers-color-scheme: dark)').matches,
  )
}

function applyTheme() {
  if (typeof document === 'undefined') return
  const mode = prefs.appearance.themeMode
  const effective = mode === 'auto' ? (resolveSystemDark() ? 'dark' : 'light') : mode
  document.documentElement.setAttribute('data-theme', effective)
}

function applyAppearance() {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  const a = prefs.appearance

  // Тема
  applyTheme()

  // Яркость фона → scrim (формула сохранена из прежнего поповера)
  const b = clamp(Number(a.brightness) || 100, 50, 150)
  const scrim = clamp(0.32 + ((100 - b) / 100) * 0.5, 0, 0.85)
  root.style.setProperty('--ui-scrim', scrim.toFixed(3))

  // Блюр верхней/боковой панели
  const blur = clamp(Number(a.barBlur) || 0, 0, 24)
  root.style.setProperty('--ui-bar-blur', `${blur}px`)

  // Акцентный цвет (Этап 2 — пока null = токен по умолчанию)
  if (a.accent) {
    root.style.setProperty('--ui-accent', String(a.accent))
    root.setAttribute('data-accent', 'custom')
  } else {
    root.style.removeProperty('--ui-accent')
    root.removeAttribute('data-accent')
  }

  // Плотность / контраст / уменьшение анимации / масштаб шрифта
  // (нейтральные дефолты ничего не меняют — CSS-блоки добавляются на Этапе 2)
  if (a.density === 'compact') root.setAttribute('data-density', 'compact')
  else root.removeAttribute('data-density')

  if (a.highContrast) root.setAttribute('data-contrast', 'high')
  else root.removeAttribute('data-contrast')

  if (a.reducedMotion) root.setAttribute('data-reduced-motion', 'true')
  else root.removeAttribute('data-reduced-motion')

  const fs = clamp(Number(a.fontScale) || 100, 80, 130)
  if (fs !== 100) root.style.setProperty('--ui-font-scale', String(fs / 100))
  else root.style.removeProperty('--ui-font-scale')

  // Обои: размытие и затемнение фонового слоя (сам источник фона
  // выбирает App.vue по prefs.wallpaper.mode/presetId/color).
  const wp = prefs.wallpaper || {}
  root.style.setProperty('--ui-wp-blur', `${clamp(Number(wp.blur) || 0, 0, 40)}px`)
  root.style.setProperty('--ui-wp-dim', String(clamp(Number(wp.dim) || 0, 0, 0.85).toFixed(3)))
}

function scheduleServerSync() {
  if (!canSync) return
  if (syncTimer) clearTimeout(syncTimer)
  syncTimer = setTimeout(async () => {
    syncTimer = null
    try {
      await api.users.updateMyUiPreferences(JSON.parse(JSON.stringify(prefs)))
    } catch {
      /* офлайн/сетевая ошибка — настройки уже в localStorage, повторим при следующем изменении */
    }
  }, SYNC_DEBOUNCE_MS)
}

function bindSystemThemeListener() {
  if (systemThemeMq || typeof window === 'undefined' || !window.matchMedia) return
  systemThemeMq = window.matchMedia('(prefers-color-scheme: dark)')
  const listener = () => {
    if (prefs.appearance.themeMode === 'auto') applyTheme()
  }
  if (systemThemeMq.addEventListener) systemThemeMq.addEventListener('change', listener)
  else if (systemThemeMq.addListener) systemThemeMq.addListener(listener)
}

function initOnce() {
  if (initialised || typeof window === 'undefined') return
  initialised = true
  loadLocal()
  applyAppearance()
  bindSystemThemeListener()

  // Любое изменение настроек: применить → записать в кэш → запланировать sync.
  watch(
    prefs,
    () => {
      if (suppressWatch) return
      applyAppearance()
      writeLocal()
      scheduleServerSync()
    },
    { deep: true },
  )
}

/**
 * Вызывается из auth-стора при логине/восстановлении сессии.
 * Сервер приоритетнее локального кэша; после мёржа включаем синхронизацию.
 */
export function applyServerUiPreferences(serverPrefs) {
  initOnce()
  const hasServerPrefs = isPlainObject(serverPrefs) && Object.keys(serverPrefs).length
  if (hasServerPrefs) {
    suppressWatch = true
    deepMerge(prefs, serverPrefs)
    suppressWatch = false
    applyAppearance()
    writeLocal()
  }
  canSync = true
  // Сервер ещё не знает наших настроек (новый пользователь или прежде только
  // localStorage) — разово засеваем бэкенд из локального состояния, чтобы
  // настройки появились на других устройствах.
  if (!hasServerPrefs) scheduleServerSync()
}

/** Вызывается при логауте — прекращаем слать настройки на сервер. */
export function disableUiSync() {
  canSync = false
  if (syncTimer) {
    clearTimeout(syncTimer)
    syncTimer = null
  }
}

export function useUiPreferences() {
  initOnce()

  const themeMode = computed(() => prefs.appearance.themeMode)
  const effectiveTheme = computed(() =>
    prefs.appearance.themeMode === 'auto'
      ? resolveSystemDark()
        ? 'dark'
        : 'light'
      : prefs.appearance.themeMode,
  )

  function setThemeMode(mode) {
    if (!['light', 'dark', 'auto'].includes(mode)) return
    prefs.appearance.themeMode = mode
  }

  function toggleTheme() {
    setThemeMode(effectiveTheme.value === 'dark' ? 'light' : 'dark')
  }

  function setBrightness(value) {
    prefs.appearance.brightness = clamp(Number(value) || 100, 50, 150)
  }

  function setBarBlur(value) {
    prefs.appearance.barBlur = clamp(Number(value) || 0, 0, 24)
  }

  function setAccent(hex) {
    const v = typeof hex === 'string' && /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(hex.trim())
      ? hex.trim()
      : null
    prefs.appearance.accent = v
  }

  function setDensity(mode) {
    prefs.appearance.density = mode === 'compact' ? 'compact' : 'comfortable'
  }

  function setFontScale(value) {
    prefs.appearance.fontScale = clamp(Number(value) || 100, 80, 130)
  }

  function setReducedMotion(on) {
    prefs.appearance.reducedMotion = Boolean(on)
  }

  function setHighContrast(on) {
    prefs.appearance.highContrast = Boolean(on)
  }

  function setWallpaperMode(mode) {
    prefs.wallpaper.mode = ['image', 'preset', 'color'].includes(mode) ? mode : 'image'
  }

  function setWallpaperPreset(id) {
    prefs.wallpaper.presetId = id || null
    prefs.wallpaper.mode = 'preset'
  }

  function setWallpaperColor(hex) {
    const v = typeof hex === 'string' && /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(hex.trim())
      ? hex.trim()
      : null
    prefs.wallpaper.color = v
    if (v) prefs.wallpaper.mode = 'color'
  }

  function setWallpaperBlur(value) {
    prefs.wallpaper.blur = clamp(Number(value) || 0, 0, 40)
  }

  function setWallpaperDim(value) {
    prefs.wallpaper.dim = clamp(Number(value) || 0, 0, 0.85)
  }

  function resetAppearance() {
    Object.assign(prefs.appearance, DEFAULTS().appearance)
  }

  function resetWallpaper() {
    Object.assign(prefs.wallpaper, DEFAULTS().wallpaper)
  }

  function getCollapsedSections() {
    return prefs.nav.collapsedSections || {}
  }

  function setCollapsedSections(next) {
    prefs.nav.collapsedSections = { ...(next || {}) }
  }

  function isPinned(to) {
    return Array.isArray(prefs.nav.pinned) && prefs.nav.pinned.includes(to)
  }

  function togglePinned(to) {
    if (!to) return
    const list = Array.isArray(prefs.nav.pinned) ? prefs.nav.pinned.slice() : []
    const idx = list.indexOf(to)
    if (idx >= 0) list.splice(idx, 1)
    else list.push(to)
    prefs.nav.pinned = list
  }

  function setPinnedOrder(list) {
    prefs.nav.pinned = Array.isArray(list) ? list.filter(Boolean) : []
  }

  function unpin(to) {
    if (!to) return
    if (Array.isArray(prefs.nav.pinned)) {
      prefs.nav.pinned = prefs.nav.pinned.filter((x) => x !== to)
    }
    if (isPlainObject(prefs.nav.pinnedMeta) && to in prefs.nav.pinnedMeta) {
      const next = { ...prefs.nav.pinnedMeta }
      delete next[to]
      prefs.nav.pinnedMeta = next
    }
  }

  /**
   * Закрепить/открепить произвольную сущность (проект, договор).
   * meta: { label, icon, type } — чтобы сайдбар отрисовал без запроса.
   */
  function togglePinnedEntity(to, meta) {
    if (!to) return
    if (isPinned(to)) {
      unpin(to)
      return
    }
    const list = Array.isArray(prefs.nav.pinned) ? prefs.nav.pinned.slice() : []
    list.push(to)
    prefs.nav.pinned = list
    prefs.nav.pinnedMeta = {
      ...(isPlainObject(prefs.nav.pinnedMeta) ? prefs.nav.pinnedMeta : {}),
      [to]: {
        label: meta?.label || to,
        icon: meta?.icon || 'fa-star',
        type: meta?.type || 'entity',
      },
    }
  }

  function getPinnedMeta(to) {
    const m = prefs.nav.pinnedMeta
    return isPlainObject(m) && isPlainObject(m[to]) ? m[to] : null
  }

  /* ---- Порядок разделов и пунктов левого меню ---- */
  function getSectionOrder() {
    return Array.isArray(prefs.nav.sectionOrder) ? prefs.nav.sectionOrder : []
  }

  function setSectionOrder(keys) {
    prefs.nav.sectionOrder = Array.isArray(keys) ? keys.filter(Boolean) : []
  }

  function getItemOrder(sectionKey) {
    const m = prefs.nav.itemOrder
    return isPlainObject(m) && Array.isArray(m[sectionKey]) ? m[sectionKey] : []
  }

  function setItemOrder(sectionKey, toList) {
    if (!sectionKey) return
    prefs.nav.itemOrder = {
      ...(isPlainObject(prefs.nav.itemOrder) ? prefs.nav.itemOrder : {}),
      [sectionKey]: Array.isArray(toList) ? toList.filter(Boolean) : [],
    }
  }

  function resetNavOrder() {
    prefs.nav.sectionOrder = []
    prefs.nav.itemOrder = {}
  }

  function setStartPage(path) {
    prefs.startPage = path && path !== '/' ? String(path) : null
  }

  function setPollSeconds(seconds) {
    const n = Number(seconds)
    prefs.notifications.pollSeconds = Number.isFinite(n) && n >= 0 ? n : 30
  }

  function setSoundEnabled(value) {
    prefs.notifications.soundEnabled = !!value
  }

  function setMessengerSoundEnabled(value) {
    prefs.notifications.messengerSoundEnabled = !!value
  }

  function setLocale(patch) {
    if (!isPlainObject(patch)) return
    if ('dateFormat' in patch) prefs.locale.dateFormat = patch.dateFormat || null
    if ('numberFormat' in patch) prefs.locale.numberFormat = patch.numberFormat || null
    if ('timezone' in patch) prefs.locale.timezone = patch.timezone || null
  }

  /** Сохранённое представление таблицы (видимость колонок, сортировка). */
  function getTableView(key) {
    if (!key) return {}
    const v = prefs.tableViews && prefs.tableViews[key]
    return isPlainObject(v) ? v : {}
  }

  function setTableView(key, patch) {
    if (!key || !isPlainObject(patch)) return
    if (!isPlainObject(prefs.tableViews)) prefs.tableViews = {}
    const current = isPlainObject(prefs.tableViews[key]) ? prefs.tableViews[key] : {}
    prefs.tableViews = {
      ...prefs.tableViews,
      [key]: { ...current, ...patch },
    }
  }

  /** Кастомизация дашборда (видимость блоков + порядок боковых виджетов). */
  function isDashboardBlockVisible(id) {
    const hidden = prefs.dashboard?.hidden
    return !(Array.isArray(hidden) && hidden.includes(id))
  }

  function toggleDashboardBlock(id) {
    if (!id) return
    const hidden = Array.isArray(prefs.dashboard?.hidden) ? prefs.dashboard.hidden.slice() : []
    const idx = hidden.indexOf(id)
    if (idx >= 0) hidden.splice(idx, 1)
    else hidden.push(id)
    prefs.dashboard = { ...prefs.dashboard, hidden }
  }

  function getDashboardSideOrder() {
    const order = prefs.dashboard?.sideOrder
    return Array.isArray(order) && order.length
      ? order
      : DEFAULTS().dashboard.sideOrder
  }

  function setDashboardSideOrder(list) {
    prefs.dashboard = {
      ...prefs.dashboard,
      sideOrder: Array.isArray(list) ? list.filter(Boolean) : [],
    }
  }

  return {
    prefs,
    themeMode,
    effectiveTheme,
    setThemeMode,
    toggleTheme,
    setBrightness,
    setBarBlur,
    setAccent,
    setDensity,
    setFontScale,
    setReducedMotion,
    setHighContrast,
    setWallpaperMode,
    setWallpaperPreset,
    setWallpaperColor,
    setWallpaperBlur,
    setWallpaperDim,
    resetAppearance,
    resetWallpaper,
    getCollapsedSections,
    setCollapsedSections,
    isPinned,
    togglePinned,
    setPinnedOrder,
    unpin,
    togglePinnedEntity,
    getPinnedMeta,
    getSectionOrder,
    setSectionOrder,
    getItemOrder,
    setItemOrder,
    resetNavOrder,
    setStartPage,
    setPollSeconds,
    setSoundEnabled,
    setMessengerSoundEnabled,
    setLocale,
    getTableView,
    setTableView,
    isDashboardBlockVisible,
    toggleDashboardBlock,
    getDashboardSideOrder,
    setDashboardSideOrder,
  }
}
