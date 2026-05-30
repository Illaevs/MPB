import { get, post, patch, del } from './_client'

/**
 * Feed API — корпоративная лента новостей.
 *
 * Читают/комментируют/лайкают все авторизованные. Публиковать,
 * править и удалять посты может только роль с `feed.edit_all`
 * (бэкенд вернёт 403 остальным; фронт прячет composer).
 */

const BASE = '/api/v1/feed'

// Лента: закреплённые сверху, далее по дате.
// params: { limit, offset, tab: 'all'|'news'|'polls'|'mentions' }.
export const list = (params = {}, options) =>
  get(`${BASE}`, params, options)

// Сколько новых незакреплённых постов после `after` (ISO created_at).
// Для polling-плашки «N новых записей». Возвращает { count, latest }.
export const since = (params = {}, options) =>
  get(`${BASE}/since`, params, options)

// Топ постов за период (для виджета «Популярное»).
export const popular = (params = {}, options) =>
  get(`${BASE}/popular`, params, options)

export const create = (payload = {}, options) =>
  post(`${BASE}`, payload, options)

export const patchPost = (id, payload = {}, options) =>
  patch(`${BASE}/${id}`, payload, options)

export const remove = (id, options) =>
  del(`${BASE}/${id}`, undefined, options)

// Отметить просмотр (идемпотентно).
export const markView = (id, options) =>
  post(`${BASE}/${id}/view`, undefined, options)

// Переключить (toggle) эмодзи-реакцию. Возвращает { reactions: [...] }.
export const react = (id, emoji, options) =>
  post(`${BASE}/${id}/react`, { emoji }, options)

// Проголосовать в опросе. optionIds — массив id вариантов.
export const vote = (id, optionIds = [], options) =>
  post(`${BASE}/${id}/vote`, { option_ids: optionIds }, options)

// Досрочно закрыть опрос (автор поста или feed.edit_all). Возвращает
// обновлённый опрос с итогами (result).
export const closePoll = (id, options) =>
  post(`${BASE}/${id}/poll/close`, undefined, options)

// Комментарии.
export const comments = (id, options) =>
  get(`${BASE}/${id}/comments`, undefined, options)

export const addComment = (id, payload = {}, options) =>
  post(`${BASE}/${id}/comments`, payload, options)

export const removeComment = (commentId, options) =>
  del(`${BASE}/comments/${commentId}`, undefined, options)

// Загрузка картинки поста. Принимает FormData с полем `file`,
// возвращает { url, name, kind: "image" } для добавления в attachments.
export const uploadImage = (formData, options) =>
  post(`${BASE}/upload-image`, formData, options)

// Загрузка произвольного файла (документ/архив/CAD/медиа).
// Принимает FormData с полем `file`, возвращает
// { url, name, size, kind: "file" } для добавления в attachments.
export const uploadFile = (formData, options) =>
  post(`${BASE}/upload-file`, formData, options)
