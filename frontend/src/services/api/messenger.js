import { get, post, patch, del } from './_client'

const BASE = '/api/v1/chat'

/**
 * Messenger / chat API.
 *
 * Покрывает два сценария:
 * - Полнофункциональный мессенджер (composables/useMessenger.js, ChatCenter.vue)
 *   с conversations + messages + members + reply/edit/pin/forward.
 * - Лёгкий "глобальный чат" (GlobalChatWidget.vue) — плоские
 *   /api/v1/chat/messages без conversation_id.
 */

// ---- conversations: list/getById/create/update/remove ----------------------

export const list = (params, options) =>
  get(`${BASE}/conversations`, params, options)

export const getById = (conversationId, options) =>
  get(`${BASE}/conversations/${conversationId}`, undefined, options)

export const create = (payload, options) =>
  post(`${BASE}/conversations`, payload, options)

export const update = (conversationId, payload, options) =>
  patch(`${BASE}/conversations/${conversationId}`, payload, options)

export const remove = (conversationId, options) =>
  del(`${BASE}/conversations/${conversationId}`, options)

// ---- conversation actions ---------------------------------------------------

export const createDirect = (userId, options) =>
  post(`${BASE}/conversations/direct`, { user_id: userId }, options)

export const addMembers = (conversationId, userIds, options) =>
  post(`${BASE}/conversations/${conversationId}/members`, { user_ids: userIds }, options)

export const removeMember = (conversationId, userId, options) =>
  del(`${BASE}/conversations/${conversationId}/members/${userId}`, options)

// ---- per-user conversation state (Stage 1 implicit DM) ---------------------

/**
 * PATCH /chat/conversations/{id}/me — мои настройки этого чата.
 * Поля опциональны; передаём только то, что меняем.
 *
 *   updateMyState(id, { is_archived: true })       // скрыть у себя
 *   updateMyState(id, { muted_forever: true })     // тишина навсегда
 *   updateMyState(id, { muted_until: '2026-...' }) // тишина до момента
 *   updateMyState(id, { muted_forever: false })    // снять mute
 */
export const updateMyState = (conversationId, payload, options) =>
  patch(`${BASE}/conversations/${conversationId}/me`, payload, options)

// ---- user search (для «написать коллеге») ---------------------------------

export const listSearchableUsers = (options) =>
  get(`${BASE}/users/searchable`, undefined, options)

// ---- conversation messages (мессенджер) ------------------------------------

export const listMessages = (conversationId, options) =>
  get(`${BASE}/conversations/${conversationId}/messages`, undefined, options)

/**
 * Отправка сообщения (FormData: body / mentions / files / reply_to_message_id /
 * forwarded_from_message_id). FormData — пусть axios сам выставит boundary.
 */
export const sendMessage = (conversationId, formData, options) =>
  post(`${BASE}/conversations/${conversationId}/messages`, formData, options)

// ---- messages CRUD (общая часть для мессенджера и глобального чата) --------

export const updateMessage = (messageId, payload, options) =>
  patch(`${BASE}/messages/${messageId}`, payload, options)

export const deleteMessage = (messageId, options) =>
  del(`${BASE}/messages/${messageId}`, options)

export const pinMessage = (messageId, options) =>
  post(`${BASE}/messages/${messageId}/pin`, undefined, options)

export const unpinMessage = (messageId, options) =>
  del(`${BASE}/messages/${messageId}/pin`, options)

// Phase B.3: эмодзи-реакции на сообщения.
// POST идемпотентно toggle'ит реакцию (me, emoji) — если уже стоит, снимет.
export const toggleReaction = (messageId, emoji, options) =>
  post(`${BASE}/messages/${messageId}/reactions`, { emoji }, options)

// Phase B.4: @-mention search для composer'а. Возвращает смешанный
// список users/deals/tasks с ACL-фильтром на бэке.
export const mentionSearch = (q, options) =>
  get(`${BASE}/mention-search`, { q }, options)

// ---- global chat (плоский /messages, без conversation_id) ------------------

export const listGlobalMessages = (options) =>
  get(`${BASE}/messages`, undefined, options)

export const sendGlobalMessage = (formData, options) =>
  post(`${BASE}/messages`, formData, options)
