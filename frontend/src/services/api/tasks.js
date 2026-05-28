import { get, post, put, patch, del, rawRequest } from './_client'

const BASE = '/api/v1/tasks'
const AUCTIONS_BASE = '/api/v1/task-auctions'
const PENALTY_RULES_BASE = '/api/v1/penalty-rules'

/**
 * Список задач. Возвращает raw axios response (не .data),
 * т.к. колл-сайты читают `X-Total-Count` из заголовков.
 */
export const list = (params, options) =>
  rawRequest({ method: 'get', url: `${BASE}/`, params, ...options })

export const getById = (id, options) =>
  get(`${BASE}/${id}`, undefined, options)

export const create = (payload, options) =>
  post(`${BASE}/`, payload, options)

export const update = (id, payload, options) =>
  put(`${BASE}/${id}`, payload, options)

export const remove = (id, options) =>
  del(`${BASE}/${id}`, options)

export const reorderMatrix = (payload, options) =>
  put(`${BASE}/matrix/reorder`, payload, options)

export const recalculatePenalty = (id, options) =>
  post(`${BASE}/${id}/recalculate-penalty`, undefined, options)

// ===== Attachments =====
export const uploadAttachments = (taskId, formData, options) =>
  post(`${BASE}/${taskId}/attachments`, formData, options)

export const removeAttachment = (taskId, path, options) =>
  del(`${BASE}/${taskId}/attachments`, { params: { path }, ...options })

// ===== Chat / Messages =====
export const listMessages = (taskId, options) =>
  get(`${BASE}/${taskId}/messages`, undefined, options)

export const sendMessage = (taskId, formData, options) =>
  post(`${BASE}/${taskId}/messages`, formData, options)

export const updateMessage = (messageId, payload, options) =>
  patch(`${BASE}/messages/${messageId}`, payload, options)

export const deleteMessage = (messageId, options) =>
  del(`${BASE}/messages/${messageId}`, options)

// ===== Chat unread counters =====
// Bulk-возвращает {task_id: count} для непрочитанных от других юзеров.
// Путь содержит ДВА сегмента после `/tasks/` (`/chat/unread-counts`) —
// без этого FastAPI ловил роут как `/tasks/{task_id}` (task_id =
// "chat-unread-counts") в tasks-роутере и отвечал 400 ещё до того, как
// task_messages-роутер мог получить запрос.
export const listChatUnreadCounts = (options) =>
  get(`${BASE}/chat/unread-counts`, undefined, options)

// Помечает чат задачи как прочитанный (last_read_at = now) — обнуляет
// бейдж в Tasks list/kanban. Вызывается при открытии модалки задачи.
export const markChatRead = (taskId, options) =>
  post(`${BASE}/${taskId}/chat/mark-read`, undefined, options)

// ===== Subtasks (checklist) =====
export const listSubtasks = (taskId, options) =>
  get(`${BASE}/${taskId}/subtasks`, undefined, options)

export const createSubtask = (taskId, payload, options) =>
  post(`${BASE}/${taskId}/subtasks`, payload, options)

export const updateSubtask = (subtaskId, payload, options) =>
  patch(`${BASE}/subtasks/${subtaskId}`, payload, options)

export const deleteSubtask = (subtaskId, options) =>
  del(`${BASE}/subtasks/${subtaskId}`, options)

export const reorderSubtasks = (taskId, ids, options) =>
  post(`${BASE}/${taskId}/subtasks/reorder`, { ids }, options)

// ===== Auctions =====
export const listAuctions = (params, options) =>
  get(`${AUCTIONS_BASE}/`, params, options)

export const createAuction = (payload, options) =>
  post(`${AUCTIONS_BASE}/`, payload, options)

export const updateAuction = (auctionId, payload, options) =>
  patch(`${AUCTIONS_BASE}/${auctionId}`, payload, options)

export const cancelAuction = (auctionId, options) =>
  del(`${AUCTIONS_BASE}/${auctionId}`, options)

export const deleteAuctionHard = (auctionId, options) =>
  del(`${AUCTIONS_BASE}/${auctionId}/hard`, options)

export const listAuctionBids = (auctionId, options) =>
  get(`${AUCTIONS_BASE}/${auctionId}/bids`, undefined, options)

export const submitAuctionBid = (auctionId, userId, payload, options) =>
  post(`${AUCTIONS_BASE}/${auctionId}/bids`, payload, { params: { user_id: userId }, ...options })

export const selectAuctionWinner = (auctionId, payload, options) =>
  post(`${AUCTIONS_BASE}/${auctionId}/select-winner`, payload, options)

export const rateAuctionTask = (taskId, payload, options) =>
  post(`${AUCTIONS_BASE}/tasks/${taskId}/rate`, payload, options)

// ===== Penalty rules =====
export const listPenaltyRules = (options) =>
  get(`${PENALTY_RULES_BASE}/`, undefined, options)

export const updatePenaltyRule = (ruleId, payload, options) =>
  patch(`${PENALTY_RULES_BASE}/${ruleId}`, payload, options)

export const seedDefaultPenaltyRules = (options) =>
  post(`${PENALTY_RULES_BASE}/seed-defaults`, undefined, options)
