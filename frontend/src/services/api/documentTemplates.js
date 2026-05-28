import { get, post, put, del, rawRequest } from './_client'

const BASE = '/api/v1/document-templates'

/** Список шаблонов. */
export const list = (params, options) =>
  get(`${BASE}/`, params, options)

export const getById = (id, options) =>
  get(`${BASE}/${id}`, undefined, options)

/**
 * Создание шаблона. Серверная ручка принимает multipart/form-data
 * (файл + поля), поэтому вызывающий код собирает FormData.
 */
export const create = (formData, options) =>
  post(`${BASE}/`, formData, options)

export const update = (id, payload, options) =>
  put(`${BASE}/${id}`, payload, options)

export const remove = (id, options) =>
  del(`${BASE}/${id}`, options)

// --- Meta ---
export const getMeta = (options) =>
  get(`${BASE}/meta`, undefined, options)

export const listFields = (params, options) =>
  get(`${BASE}/fields`, params, options)

export const listFieldGroups = (options) =>
  get(`${BASE}/field-groups`, undefined, options)

// --- Versions ---
export const uploadVersion = (templateId, formData, options) =>
  post(`${BASE}/${templateId}/versions`, formData, options)

/**
 * Скачивание шаблона (DOCX) — возвращает полный axios response с blob,
 * чтобы можно было прочитать content-disposition.
 */
export const download = (templateId, params, options) =>
  rawRequest({
    method: 'get',
    url: `${BASE}/${templateId}/download`,
    params,
    responseType: 'blob',
    ...options,
  })
