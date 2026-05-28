import { get, post, put, del, rawRequest } from './_client'

const BASE = '/api/v1/companies'

/**
 * Список контрагентов.
 * Без аргументов — full list (limit:1000) — основной паттерн, используемый
 * множеством views для построения селектов.
 */
export const list = (params, options) =>
  get(`${BASE}/`, { limit: 1000, ...(params || {}) }, options)

export const search = (term, extraParams, options) =>
  get(`${BASE}/`, { search: term, limit: 50, ...(extraParams || {}) }, options)

export const getById = (id, options) =>
  get(`${BASE}/${id}`, undefined, options)

export const create = (payload, options) =>
  post(`${BASE}/`, payload, options)

export const update = (id, payload, options) =>
  put(`${BASE}/${id}`, payload, options)

export const remove = (id, options) =>
  del(`${BASE}/${id}`, options)

export const count = (params, options) =>
  get(`${BASE}/count`, params, options)

export const typesSummary = (params, options) =>
  get(`${BASE}/types-summary`, params, options)

export const refreshAll = (options) =>
  post(`${BASE}/refresh-all`, undefined, options)

export const getUsers = (companyId, options) =>
  get(`${BASE}/${companyId}/users`, undefined, options)

export const updateUsers = (companyId, payload, options) =>
  put(`${BASE}/${companyId}/users`, payload, options)

export const listDocuments = (companyId, options) =>
  get(`${BASE}/${companyId}/documents`, undefined, options)

export const uploadDocument = (companyId, formData, options) =>
  post(`${BASE}/${companyId}/documents/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    ...options,
  })

export const downloadDocument = (documentId, options) =>
  rawRequest({
    method: 'get',
    url: `${BASE}/documents/${documentId}/download`,
    responseType: 'blob',
    ...options,
  })

export const downloadDocumentMeta = (documentId, options) =>
  get(`${BASE}/documents/${documentId}/download`, undefined, options)

export const removeDocument = (documentId, options) =>
  del(`${BASE}/documents/${documentId}`, options)

export const relatedDeals = (companyId, options) =>
  get(`${BASE}/${companyId}/related-deals`, undefined, options)

/** Удобный хелпер для CompanySmartSelect-подобных мест. */
export const findByInn = (inn, options) =>
  get(`${BASE}/`, { search: inn, limit: 5 }, options)

/** Получить "нашу компанию" по флагу is_default; 404 если не настроена. */
export const getDefaultOurCompany = (options) =>
  get(`${BASE}/default-our-company`, undefined, options)

/** Назначить компанию (только internal) дефолтной "нашей". */
export const setDefaultOurCompany = (companyId, options) =>
  post(`${BASE}/${companyId}/set-default`, undefined, options)
