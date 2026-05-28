import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../services/api'

/**
 * Лёгкий store для мессенджера: список чатов + счётчик непрочитанных.
 *
 * Идея: useMessenger composable остаётся как есть и держит детальное состояние
 * текущего разговора (черновик, mention picker, edit, send). Для глобальных
 * вещей (бейдж непрочитанных в шапке, список чатов для GlobalChatWidget) —
 * один singleton-store.
 *
 * Полноценная интеграция useMessenger ↔ store произойдёт в Phase 7
 * (Telegram-style redesign), сейчас цель — убрать дубль fetch'ей чатов.
 */
export const useMessengerStore = defineStore('messenger', () => {
  const conversations = ref([])
  const loading = ref(false)
  let inFlight = null

  const byId = computed(() => {
    const map = new Map()
    for (const item of conversations.value) {
      if (item?.id) map.set(String(item.id), item)
    }
    return map
  })

  function getById(id) {
    return id ? byId.value.get(String(id)) || null : null
  }

  const LAST_SEEN_KEY_PREFIX = 'messenger_last_seen_'

  function getLastSeenAt(conversationId) {
    if (!conversationId) return 0
    try {
      return Number(localStorage.getItem(`${LAST_SEEN_KEY_PREFIX}${conversationId}`) || 0)
    } catch {
      return 0
    }
  }

  /**
   * Считаем чат непрочитанным, если последнее сообщение позже last_seen
   * и автор — не текущий пользователь. Лёгкое дублирование с useMessenger,
   * но без зависимости от его состояния — нужно для бейджа в хедере.
   */
  function isConversationUnread(conversation, currentUserId) {
    if (!conversation?.last_message?.created_at) return false
    if (String(conversation.last_message.user_id || '') === String(currentUserId || '')) return false
    const lastSeen = getLastSeenAt(conversation.id)
    return new Date(conversation.last_message.created_at).getTime() > lastSeen
  }

  function unreadCountForUser(currentUserId) {
    return conversations.value.filter((c) => isConversationUnread(c, currentUserId)).length
  }

  async function ensureLoaded({ silent = true } = {}) {
    if (inFlight) return inFlight
    if (!silent) loading.value = true
    inFlight = api.messenger.list()
      .then((data) => {
        conversations.value = Array.isArray(data) ? data : []
        return conversations.value
      })
      .catch(() => conversations.value)
      .finally(() => {
        if (!silent) loading.value = false
        inFlight = null
      })
    return inFlight
  }

  async function refresh(options = {}) {
    inFlight = null
    return ensureLoaded(options)
  }

  function upsert(conversation) {
    if (!conversation?.id) return
    const idx = conversations.value.findIndex((it) => String(it.id) === String(conversation.id))
    if (idx >= 0) {
      const next = conversations.value.slice()
      next[idx] = { ...next[idx], ...conversation }
      conversations.value = next
    } else {
      conversations.value = [...conversations.value, conversation]
    }
  }

  function removeLocal(id) {
    if (!id) return
    conversations.value = conversations.value.filter((it) => String(it.id) !== String(id))
  }

  function reset() {
    conversations.value = []
    inFlight = null
    loading.value = false
  }

  return {
    conversations,
    loading,
    byId,
    getById,
    getLastSeenAt,
    isConversationUnread,
    unreadCountForUser,
    ensureLoaded,
    refresh,
    upsert,
    removeLocal,
    reset,
  }
})
