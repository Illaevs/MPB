import { get, post, del, rawRequest } from './_client'

const BASE = '/api/v1/mail'

/**
 * Mail / inbox API.
 *
 * Базовые ресурсы:
 * - mailboxes (почтовые ящики пользователя)
 * - mailboxes/:id/folders
 * - mailboxes/:id/messages
 * - messages/:id (+ attachments, move)
 *
 * Реальный потребитель — views/Mail.vue (миграция отложена до Phase 5,
 * данный модуль введён в Phase 2 как единая точка входа для будущей замены).
 */

// ---- mailboxes (list/getById/create/update/remove минимум) -----------------

export const list = (options) =>
  get(`${BASE}/mailboxes`, undefined, options)

export const getById = (id, options) =>
  get(`${BASE}/mailboxes/${id}`, undefined, options)

export const create = (payload, options) =>
  post(`${BASE}/mailboxes`, payload, options)

// у бэка нет PUT для мейлбокса как такового — оставляем заглушку под общий контракт.
export const update = (id, payload, options) =>
  post(`${BASE}/mailboxes/${id}`, payload, options)

export const remove = (id, options) =>
  del(`${BASE}/mailboxes/${id}`, options)

// ---- mailbox actions --------------------------------------------------------

export const listFolders = (mailboxId, options) =>
  get(`${BASE}/mailboxes/${mailboxId}/folders`, undefined, options)

export const listMessages = (mailboxId, params, options) =>
  get(`${BASE}/mailboxes/${mailboxId}/messages`, params, options)

export const connect = (mailboxId, options) =>
  post(`${BASE}/mailboxes/${mailboxId}/connect`, undefined, options)

export const connectAppPassword = (mailboxId, payload, options) =>
  post(`${BASE}/mailboxes/${mailboxId}/connect-app-password`, payload, options)

export const sendMessage = (mailboxId, payload, options) =>
  post(`${BASE}/mailboxes/${mailboxId}/send`, payload, options)

/**
 * Экспорт писем (исторически возвращает blob — оборачиваем в rawRequest,
 * чтобы потребитель получил полный Response для скачивания файла).
 */
export const exportMailbox = (mailboxId, params, options) =>
  rawRequest({
    method: 'get',
    url: `${BASE}/mailboxes/${mailboxId}/export`,
    params,
    responseType: 'blob',
    ...options,
  })

// ---- messages ---------------------------------------------------------------

export const getMessage = (messageId, options) =>
  get(`${BASE}/messages/${messageId}`, undefined, options)

export const moveMessage = (messageId, payload, options) =>
  post(`${BASE}/messages/${messageId}/move`, payload, options)

export const downloadAttachment = (messageId, attachmentId, options) =>
  rawRequest({
    method: 'get',
    url: `${BASE}/messages/${messageId}/attachments/${encodeURIComponent(attachmentId)}`,
    responseType: 'blob',
    ...options,
  })

/**
 * Скачивание по уже готовому download_url, полученному с бэка.
 * Допускаем только URL внутри /api/v1/mail/ — проверка повторяет логику Mail.vue.
 */
export const downloadByUrl = (url, options) => {
  if (typeof url !== 'string' || !url.startsWith(`${BASE}/`)) {
    throw new Error('mail.downloadByUrl: url must start with /api/v1/mail/')
  }
  return rawRequest({
    method: 'get',
    url,
    responseType: 'blob',
    ...options,
  })
}
