import { get, post, put, del } from './_client'

const BASE = '/api/v1/notifications'
const PREFS_BASE = '/api/v1/notification-preferences'
const TELEGRAM_BASE = '/api/v1/telegram'

/**
 * Notifications API.
 *
 * Кроме самих уведомлений включает связные ресурсы из той же доменной плоскости:
 * - notification-preferences (каналы доставки)
 * - telegram (привязка/отвязка канала Telegram)
 *
 * Это удобно, чтобы NotificationCenter / Notifications.vue ходили через один модуль.
 */

// ---- list/getById/create/update/remove минимум ------------------------------

export const list = (params, options) =>
  get(`${BASE}/`, params, options)

export const getById = (id, options) =>
  get(`${BASE}/${id}`, undefined, options)

export const create = (payload, options) =>
  post(`${BASE}/`, payload, options)

export const update = (id, payload, options) =>
  put(`${BASE}/${id}`, payload, options)

export const remove = (id, options) =>
  del(`${BASE}/${id}`, options)

// ---- actions ----------------------------------------------------------------

export const unreadCount = (options) =>
  get(`${BASE}/unread-count`, undefined, options)

export const markRead = (id, options) =>
  post(`${BASE}/${id}/read`, undefined, options)

export const markAllRead = (options) =>
  post(`${BASE}/read-all`, undefined, options)

// ---- preferences ------------------------------------------------------------

export const getPreferences = (options) =>
  get(`${PREFS_BASE}/me`, undefined, options)

export const updatePreferences = (payload, options) =>
  put(`${PREFS_BASE}/me`, payload, options)

// ---- telegram channel -------------------------------------------------------

export const getTelegramStatus = (options) =>
  get(`${TELEGRAM_BASE}/me`, undefined, options)

export const createTelegramLink = (options) =>
  post(`${TELEGRAM_BASE}/link`, undefined, options)

export const disconnectTelegram = (options) =>
  del(`${TELEGRAM_BASE}/me`, options)
