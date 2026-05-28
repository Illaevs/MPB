/**
 * Event Bus management API — admin-only.
 *
 * - outbox: чтение строк outbox-таблицы, ручной retry для DLQ/failed
 * - subscriptions: CRUD внешних подписок (HMAC-secret, URL, glob-паттерн)
 * - testSink: synthetic webhook-receiver для smoke-прогона воркера
 */
import { get, post, put, del } from './_client'

const BASE = '/api/v1/event-bus'

/* ----- Outbox ----- */
export const listOutbox = (params, options) =>
  get(`${BASE}/outbox`, params, options)

export const getOutboxRow = (id, options) =>
  get(`${BASE}/outbox/${id}`, undefined, options)

export const retryOutbox = (id, options) =>
  post(`${BASE}/outbox/${id}/retry`, undefined, options)

/* ----- Subscriptions ----- */
export const listSubscriptions = (options) =>
  get(`${BASE}/subscriptions`, undefined, options)

export const createSubscription = (payload, options) =>
  post(`${BASE}/subscriptions`, payload, options)

export const updateSubscription = (id, payload, options) =>
  put(`${BASE}/subscriptions/${id}`, payload, options)

export const deleteSubscription = (id, options) =>
  del(`${BASE}/subscriptions/${id}`, options)

/* ----- Test sink (smoke) ----- */
export const testSinkLog = (options) =>
  get(`${BASE}/_test/webhook-sink/log`, undefined, options)

/* ----- V1.5 observability ----- */
// Сводка для admin observability страницы: counts по статусам,
// top event_types, per-subscription статистика, totals.
export const getStats = (options) =>
  get(`${BASE}/stats`, undefined, options)
