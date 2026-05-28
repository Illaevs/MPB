import { get, post, patch, del } from './_client'

/**
 * Accreditations API — общий модуль для admin и subcontractor контекстов.
 *
 * Upload документа идёт через `/api/v1/uploads/accreditations/documents`
 * (multipart form-data); скачивание возвращает JSON с `href`.
 */

const BASE = '/api/v1/accreditations'
const UPLOAD_BASE = '/api/v1/uploads/accreditations'

// ---------------- Accreditation records ----------------

export const list = (params, options) =>
  get(`${BASE}/`, params, options)

export const getById = (id, options) =>
  get(`${BASE}/${id}`, undefined, options)

export const create = (payload, options) =>
  post(`${BASE}/`, payload, options)

export const update = (id, payload, options) =>
  patch(`${BASE}/${id}`, payload, options)

export const remove = (id, options) =>
  del(`${BASE}/${id}`, options)

/** Subcontractor: запрос на аккредитацию по выбранным направлениям. */
export const requestAccreditations = (payload, options) =>
  post(`${BASE}/request`, payload, options)

// ---------------- Documents ----------------

export const listCompanyDocuments = (companyId, options) =>
  get(`${BASE}/companies/${companyId}/documents`, undefined, options)

export const updateDocument = (docId, payload, options) =>
  patch(`${BASE}/documents/${docId}`, payload, options)

export const removeDocument = (docId, options) =>
  del(`${BASE}/documents/${docId}`, options)

/** Возвращает JSON `{ href }` для последующей загрузки. */
export const getDocumentDownloadHref = (docId, options) =>
  get(`${BASE}/documents/${docId}/download`, undefined, options)

/** Multipart upload документа (через uploads-роутер). */
export const uploadDocument = (formData, options) =>
  post(`${UPLOAD_BASE}/documents`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    ...options,
  })
