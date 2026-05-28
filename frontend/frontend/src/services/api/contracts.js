import { get, post, put, patch, del, rawRequest } from './_client'

const BASE = '/api/v1/contracts'
const UPLOADS_BASE = '/api/v1/uploads/contracts'

/**
 * Список договоров. Возвращает уже распакованный response.data,
 * т.к. в текущих колл-сайтах используется либо массив, либо `{items, total, stats}`.
 *
 * Если потребуется доступ к заголовкам ответа — используйте `listRaw`.
 */
export const list = (params, options) =>
  get(`${BASE}/`, params, options)

export const listRaw = (params, options) =>
  rawRequest({ method: 'get', url: `${BASE}/`, params, ...options })

export const listByDeal = (dealId, options) =>
  get(`${BASE}/deal/${dealId}`, undefined, options)

export const getById = (id, options) =>
  get(`${BASE}/${id}`, undefined, options)

export const getCard = (contractId, options) =>
  get(`${BASE}/${contractId}/card`, undefined, options)

export const create = (payload, options) =>
  post(`${BASE}/`, payload, options)

export const update = (id, payload, options) =>
  put(`${BASE}/${id}`, payload, options)

export const remove = (id, options) =>
  del(`${BASE}/${id}`, options)

// ===== Documents =====
export const uploadDocument = (formData, options) =>
  post(`${UPLOADS_BASE}/documents`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    ...options,
  })

export const updateDocument = (docId, payload, options) =>
  patch(`${BASE}/documents/${docId}`, payload, options)

export const updateDocumentProducts = (docId, payload, options) =>
  patch(`${BASE}/documents/${docId}/products`, payload, options)

export const removeDocument = (docId, options) =>
  del(`${BASE}/documents/${docId}`, options)

export const removeDocumentFile = (docId, fileKind, options) =>
  del(`${BASE}/documents/${docId}/file`, { params: { file_kind: fileKind }, ...options })

export const downloadDocument = (docId, fileKind, options) =>
  rawRequest({
    method: 'get',
    url: `${BASE}/documents/${docId}/download`,
    params: { file_kind: fileKind },
    responseType: 'blob',
    ...options,
  })

// ===== Expenses =====
export const listExpenses = (contractId, options) =>
  get(`${BASE}/${contractId}/expenses`, undefined, options)

export const createExpense = (contractId, payload, options) =>
  post(`${BASE}/${contractId}/expenses`, payload, options)

export const updateExpense = (contractId, expenseId, payload, options) =>
  patch(`${BASE}/${contractId}/expenses/${expenseId}`, payload, options)

export const removeExpense = (contractId, expenseId, options) =>
  del(`${BASE}/${contractId}/expenses/${expenseId}`, options)

export const createBulkExpenses = (contractId, payload, options) =>
  post(`${BASE}/${contractId}/expenses/bulk`, payload, options)
