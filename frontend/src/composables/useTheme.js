import { useUiPreferences } from './useUiPreferences'

/**
 * Тонкий адаптер над useUiPreferences — сохраняет прежний публичный API
 * ({ theme, setTheme, toggleTheme, clearOverride }), но единым источником
 * правды и местом хранения теперь является useUiPreferences (гибрид
 * localStorage + бэкенд-синхронизация).
 *
 * `theme` — это вычисляемое эффективное значение 'light' | 'dark'
 * (режим 'auto' раскрывается по prefers-color-scheme).
 */
export function useTheme() {
  const { effectiveTheme, setThemeMode, toggleTheme } = useUiPreferences()

  function setTheme(value) {
    if (value !== 'dark' && value !== 'light') return
    setThemeMode(value)
  }

  function clearOverride() {
    setThemeMode('auto')
  }

  return { theme: effectiveTheme, setTheme, toggleTheme, clearOverride }
}
