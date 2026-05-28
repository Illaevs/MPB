import { get, post, put, del, rawRequest } from './_client'

const BASE = '/api/v1/outgoing-registry'

/** Список документов исходящего реестра. */
export const list = (params, options) =>
  get(`${BASE}/`, params, options)

export const getById = (id, options) =>
  get(`${BASE}/${id}`, undefined, options)

/**
 * Создание документа. Серверная ручка ждёт multipart/form-data —
 * вызывающий код собирает FormData и передаёт её сюда.
 */
export const create = (formData, options) =>
  post(`${BASE}/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    ...options,
  })

export const update = (id, payload, options) =>
  put(`${BASE}/${id}`, payload, options)

export const remove = (id, options) =>
  del(`${BASE}/${id}`, options)

// --- Editor schema / context ---
export const getEditorSchema = (params, options) =>
  get(`${BASE}/editor/schema`, params, options)

export const getEditorContext = (documentId, options) =>
  get(`${BASE}/${documentId}/editor-context`, undefined, options)

export const resolveEditor = (payload, options) =>
  post(`${BASE}/editor/resolve`, payload, options)

/**
 * Live preview редактора (pdf/docx) — возвращает blob.
 * format: 'pdf' | 'docx'
 */
export const editorPreview = (format, payload, options) =>
  rawRequest({
    method: 'post',
    url: `${BASE}/editor/preview-${format}`,
    data: payload,
    responseType: 'blob',
    ...options,
  })

// --- Attachments ---
/**
 * Используем rawRequest, чтобы пробросить onUploadProgress.
 * Возвращаем response.data, чтобы соответствовать остальным методам модуля.
 */
export const uploadAttachments = async (documentId, formData, options) => {
  const response = await rawRequest({
    method: 'post',
    url: `${BASE}/${documentId}/attachments`,
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    ...options,
  })
  return response.data
}

// --- Versions ---
export const createVersion = (documentId, options) =>
  post(`${BASE}/${documentId}/versions`, undefined, options)

// --- Render cache ---
export const generateRenderCache = (documentId, options) =>
  post(`${BASE}/${documentId}/render-cache/generate`, undefined, options)

export const uploadRenderCache = (documentId, formData, options) =>
  post(`${BASE}/${documentId}/render-cache`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    ...options,
  })

// --- Preview / downloads ---
export const previewPdf = (documentId, options) =>
  rawRequest({
    method: 'get',
    url: `${BASE}/${documentId}/preview-pdf`,
    responseType: 'blob',
    params: { t: Date.now() },
    headers: {
      'Cache-Control': 'no-cache',
      Pragma: 'no-cache',
    },
    ...options,
  })

/**
 * Полный URL для downloadFromApi (DOCX-рендера).
 * Вспомогательный геттер: download.js использует свой собственный axios
 * для отслеживания прогресса, поэтому здесь просто экспортируем URL.
 */
export const renderDocxUrl = (documentId) =>
  `${BASE}/${documentId}/render-docx`

// --- Deal context ---
export const getClosingDocuments = (dealId, params, options) =>
  get(`${BASE}/deal/${dealId}/closing-documents`, params, options)

export const getDealIntro = (dealId, params, options) =>
  get(`${BASE}/deal-intro/${dealId}`, params, options)

// --- Sequences ---
export const listSequences = (params, options) =>
  get(`${BASE}/sequences`, params, options)

export const updateSequence = (ourCompanyKey, payload, options) =>
  put(`${BASE}/sequences/${ourCompanyKey}`, payload, options)

// --- Template v2 (new redesign) ---
export const listTemplatesV2 = (params, options) =>
  get(`${BASE}/templates/v2`, params, options)

export const getTemplateV2 = (templateId, options) =>
  get(`${BASE}/templates/v2/${templateId}`, undefined, options)

export const createTemplateV2 = (payload, options) =>
  post(`${BASE}/templates/v2`, payload, options)

export const updateTemplateV2 = (templateId, payload, options) =>
  put(`${BASE}/templates/v2/${templateId}`, payload, options)

export const deleteTemplateV2 = (templateId, options) =>
  del(`${BASE}/templates/v2/${templateId}`, options)

/** Download a stored version file (pdf|docx) as a blob. */
export const downloadVersionFile = (documentId, versionId, format, options) =>
  rawRequest({
    method: 'get',
    url: `${BASE}/${documentId}/versions/${versionId}/download`,
    params: { format },
    responseType: 'blob',
    ...options,
  })
