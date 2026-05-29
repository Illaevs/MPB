import { onBeforeUnmount, onMounted } from 'vue'
import { heartbeat as apiHeartbeat } from '../services/api/users'
import { getActiveUser } from '../utils/permissions'

/**
 * Phase C.2 — presence heartbeat.
 *
 * Шлёт POST /api/v1/users/me/heartbeat раз в 60 секунд, пока юзер
 * авторизован. Backend обновляет users.last_seen_at = NOW.
 *
 * Также шлёт пинг сразу при mount и при возврате вкладки в фокус —
 * чтобы зелёная точка появилась без задержки.
 *
 * Usage: вызвать `usePresence()` один раз в App.vue (или в layout-
 * корне). Несколько вызовов в разных компонентах безопасны — но
 * лишние не несут пользы.
 */

const INTERVAL_MS = 60 * 1000

export function usePresence() {
  let _timer = null
  let _onFocus = null
  let _onVisibility = null

  const ping = async () => {
    try {
      if (!getActiveUser()) return
      await apiHeartbeat()
    } catch (e) {
      // 401/403 — не залогинен; всё остальное — глотаем.
    }
  }

  const start = () => {
    if (_timer) return
    ping()
    _timer = setInterval(ping, INTERVAL_MS)
    // Ping при возврате вкладки в фокус — закрывает gap'ы > 60с
    // когда вкладка спала.
    if (typeof window !== 'undefined') {
      _onFocus = () => ping()
      _onVisibility = () => {
        if (!document.hidden) ping()
      }
      window.addEventListener('focus', _onFocus)
      document.addEventListener('visibilitychange', _onVisibility)
    }
  }

  const stop = () => {
    if (_timer) {
      clearInterval(_timer)
      _timer = null
    }
    if (typeof window !== 'undefined') {
      if (_onFocus) {
        window.removeEventListener('focus', _onFocus)
        _onFocus = null
      }
      if (_onVisibility) {
        document.removeEventListener('visibilitychange', _onVisibility)
        _onVisibility = null
      }
    }
  }

  onMounted(start)
  onBeforeUnmount(stop)

  return { ping, start, stop }
}
