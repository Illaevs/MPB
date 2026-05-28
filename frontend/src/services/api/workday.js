import { get, post, patch } from './_client'

/**
 * Workday API — учёт рабочего времени (MVP).
 *
 * Эндпоинты «личные», на бэке гейтятся require_any_section_access
 * (т.е. любой авторизованный сотрудник). Дополнительно бэк проверяет
 * флаг роли `track_work_time`; для customer/admin без флага — 403,
 * но FE сам не вызывает /start/end без флага, поэтому UX чистый.
 */

const BASE = '/api/v1/workday'

// Текущее состояние трекера. Возвращает { session|null, track_work_time, idle_timeout_minutes }.
export const getActive = (options) =>
  get(`${BASE}/active`, undefined, options)

// Начать рабочий день. Идемпотентно: если активная уже есть — вернёт её.
export const start = (payload = {}, options) =>
  post(`${BASE}/start`, payload, options)

// Завершить активную. reason: 'manual' | 'idle'. Для idle FE передаёт
// ended_at = time of last activity, чтобы зачесть только реальные часы.
export const end = (payload = {}, options) =>
  post(`${BASE}/end`, payload, options)

// Heartbeat: каждые ~60с пока вкладка активна. Обновляет last_activity_at.
export const heartbeat = (options) =>
  post(`${BASE}/heartbeat`, undefined, options)

// ---- Stats (phase 3) -------------------------------------------------------

// Список пользователей с суммарным временем за период (для боковой панели).
// Админ (workday_admin) получает всех, обычный юзер — только себя.
export const list = (params = {}, options) =>
  get(`${BASE}/list`, params, options)

// Подробная статистика по одному юзеру: bucket'ы по day/week/month
// + список сессий внутри каждого. `user_id` пуст → собственные данные.
export const stats = (params = {}, options) =>
  get(`${BASE}/stats`, params, options)

// Табличный вид: по каждому сотруднику посуточная разбивка секунд
// { user_id, full_name, role_name, total_seconds, has_active, days:{iso:sec} }.
export const grid = (params = {}, options) =>
  get(`${BASE}/grid`, params, options)

// Админ-правка одной сессии задним числом (требует workday_admin).
export const patchSession = (sessionId, payload = {}, options) =>
  patch(`${BASE}/${sessionId}`, payload, options)
