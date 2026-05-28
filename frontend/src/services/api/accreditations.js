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

/** Admin: id компаний, аккредитованных по ВСЕМ переданным направлениям.
 *  directionIds — массив id; status по умолчанию approved. */
export const accreditedCompanyIds = (directionIds, status = 'approved', options) =>
  get(`${BASE}/accredited-company-ids`, {
    direction_ids: (directionIds || []).join(','),
    status,
  }, options)

/** Admin: массовая аккредитация/отклонение НАПРАВЛЕНИЙ одной компании
 *  (upsert). status — query, comment — query (нужен при rejected). */
export const bulkSetDirections = (companyId, directionIds, status, comment, options) =>
  post(`${BASE}/bulk-directions`, {
    company_id: companyId,
    direction_ids: directionIds,
  }, {
    params: { status, ...(comment ? { comment } : {}) },
    ...options,
  })

/** Admin: массовое approve/reject по id записей аккредитаций. */
export const bulkAction = (ids, status, comment, options) =>
  post(`${BASE}/bulk`, { ids, status, comment: comment || null }, options)

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
