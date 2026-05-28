import { get, post, put, patch, del } from './_client'

/**
 * Treasury / Казначейство API.
 *
 * Покрывает:
 *   - транзакции (list/create/update/delete/bulk-action)
 *   - allocations (создание, обновление, удаление, привязка к ДДС)
 *   - linked payments (привязка платежей друг к другу)
 *   - правила автокатегоризации
 *   - импорт банковских выписок
 */

const TX_BASE = '/api/v1/finance/treasury/transactions'
const ALLOC_BASE = '/api/v1/finance/treasury/allocations'
const RULES_BASE = '/api/v1/finance/treasury/rules'
const IMPORT_BASE = '/api/v1/finance/import-bank-statement'

// ---------------- Transactions ----------------

export const list = (params, options) =>
  get(`${TX_BASE}`, params, options)

export const getById = (id, options) =>
  get(`${TX_BASE}/${id}`, undefined, options)

export const create = (payload, options) =>
  post(`${TX_BASE}`, payload, options)

export const update = (id, payload, options) =>
  patch(`${TX_BASE}/${id}`, payload, options)

export const remove = (id, options) =>
  del(`${TX_BASE}/${id}`, options)

export const bulkAction = (payload, options) =>
  post(`${TX_BASE}/bulk-action`, payload, options)

// ---------------- Linked payments (TX <-> TX) ----------------

export const listLinked = (txId, options) =>
  get(`${TX_BASE}/${txId}/linked`, undefined, options)

export const linkTransaction = (txId, payload, options) =>
  post(`${TX_BASE}/${txId}/link`, payload, options)

export const unlinkTransaction = (txId, linkedId, options) =>
  del(`${TX_BASE}/${txId}/link/${linkedId}`, options)

// ---------------- Allocations ----------------

export const createAllocation = (txId, payload, options) =>
  post(`${TX_BASE}/${txId}/allocations`, payload, options)

export const updateAllocation = (allocationId, payload, options) =>
  patch(`${ALLOC_BASE}/${allocationId}`, payload, options)

export const removeAllocation = (allocationId, options) =>
  del(`${ALLOC_BASE}/${allocationId}`, options)

// ---------------- Rules ----------------

export const listRules = (params, options) =>
  get(`${RULES_BASE}`, params, options)

export const createRule = (payload, options) =>
  post(`${RULES_BASE}`, payload, options)

export const updateRule = (id, payload, options) =>
  put(`${RULES_BASE}/${id}`, payload, options)

export const removeRule = (id, options) =>
  del(`${RULES_BASE}/${id}`, options)

export const applyRuleToAll = (id, options) =>
  post(`${RULES_BASE}/${id}/apply-all`, undefined, options)

// ---------------- Import bank statement ----------------

export const importPreview = (formData, params, options) =>
  post(`${IMPORT_BASE}/preview`, formData, { params, ...options })

export const importConfirm = (formData, params, options) =>
  post(`${IMPORT_BASE}/confirm`, formData, { params, ...options })
