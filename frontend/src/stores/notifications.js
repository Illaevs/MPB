import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../services/api'

/**
 * Состояние уведомлений: список + счётчик непрочитанных + поллинг.
 *
 * Раньше App.vue сам поллил /api/v1/notifications и держал unreadCount,
 * NotificationCenter и Notifications.vue делали свои отдельные запросы.
 * Теперь — один источник правды и одна точка поллинга.
 *
 * Использование:
 *   const store = useNotificationsStore()
 *   store.startPolling() // в App.vue после логина
 *   store.stopPolling()  // в App.vue при logout
 *   store.unreadCount    // computed, реактивно
 *   store.items          // последняя загруженная порция
 *   await store.markRead(id)
 *   await store.markAllRead()
 */
export const useNotificationsStore = defineStore('notifications', () => {
  const items = ref([])
  const unreadCount = ref(0)
  const loading = ref(false)
  const polling = ref(false)
  let pollTimer = null
  let inFlightList = null
  let inFlightCount = null

  const DEFAULT_POLL_SECONDS = 30
  const LIST_LIMIT = 50
  let pollSeconds = DEFAULT_POLL_SECONDS

  // 0 = ручной режим (только разовый refresh, без таймера).
  function normalizeSeconds(value) {
    const n = Number(value)
    if (!Number.isFinite(n) || n < 0) return DEFAULT_POLL_SECONDS
    if (n === 0) return 0
    return Math.min(900, Math.max(10, Math.round(n)))
  }

  async function fetchList({ silent = false } = {}) {
    if (inFlightList) return inFlightList
    if (!silent) loading.value = true
    inFlightList = api.notifications.list({ limit: LIST_LIMIT })
      .then((data) => {
        items.value = Array.isArray(data) ? data : (data?.items || [])
        return items.value
      })
      .catch(() => items.value)
      .finally(() => {
        if (!silent) loading.value = false
        inFlightList = null
      })
    return inFlightList
  }

  async function fetchUnreadCount() {
    if (inFlightCount) return inFlightCount
    inFlightCount = api.notifications.unreadCount()
      .then((data) => {
        const value = typeof data === 'number'
          ? data
          : (data?.count ?? data?.unread ?? data?.unread_count ?? 0)
        unreadCount.value = Number(value) || 0
        return unreadCount.value
      })
      .catch(() => unreadCount.value)
      .finally(() => {
        inFlightCount = null
      })
    return inFlightCount
  }

  async function refresh({ silent = false } = {}) {
    await Promise.all([fetchList({ silent }), fetchUnreadCount()])
  }

  function startPolling(intervalSeconds) {
    if (pollTimer || polling.value) return
    if (intervalSeconds !== undefined) pollSeconds = normalizeSeconds(intervalSeconds)
    polling.value = true
    refresh({ silent: true })
    if (pollSeconds > 0) {
      pollTimer = setInterval(() => refresh({ silent: true }), pollSeconds * 1000)
    }
  }

  function stopPolling() {
    if (pollTimer) clearInterval(pollTimer)
    pollTimer = null
    polling.value = false
  }

  // Меняем частоту на лету: если активны — перезапускаем таймер.
  function setPollSeconds(intervalSeconds) {
    const next = normalizeSeconds(intervalSeconds)
    if (next === pollSeconds) return
    pollSeconds = next
    if (polling.value) {
      if (pollTimer) clearInterval(pollTimer)
      pollTimer = pollSeconds > 0
        ? setInterval(() => refresh({ silent: true }), pollSeconds * 1000)
        : null
    }
  }

  function reset() {
    stopPolling()
    items.value = []
    unreadCount.value = 0
  }

  async function markRead(id) {
    if (!id) return
    await api.notifications.markRead(id)
    items.value = items.value.map((it) =>
      String(it.id) === String(id) ? { ...it, is_read: true, read_at: new Date().toISOString() } : it
    )
    if (unreadCount.value > 0) unreadCount.value -= 1
  }

  async function markAllRead() {
    await api.notifications.markAllRead()
    const ts = new Date().toISOString()
    items.value = items.value.map((it) => ({ ...it, is_read: true, read_at: it.read_at || ts }))
    unreadCount.value = 0
  }

  const unreadItems = computed(() => items.value.filter((it) => !it.is_read))

  return {
    items,
    unreadItems,
    unreadCount,
    loading,
    polling,
    fetchList,
    fetchUnreadCount,
    refresh,
    startPolling,
    stopPolling,
    setPollSeconds,
    reset,
    markRead,
    markAllRead,
  }
})
