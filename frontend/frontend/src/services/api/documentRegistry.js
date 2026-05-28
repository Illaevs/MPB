import { get, post, put, del, rawRequest } from './_client'

const BASE = '/api/v1/document-registry'

/** Список документов реестра. */
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

// --- Relations ---
export const listRelations = (documentId, options) =>
  get(`${BASE}/${documentId}/relations`, undefined, options)

export const listParentRelations = (documentId, options) =>
  get(`${BASE}/${documentId}/parent-relations`, undefined, options)

export const addRelation = (documentId, payload, options) =>
  post(`${BASE}/${documentId}/relations`, payload, options)

export const removeRelation = (relationId, options) =>
  del(`${BASE}/relations/${relationId}`, options)

// --- Packages ---
export const listPackages = (params, options) =>
  get(`${BASE}/packages`, params, options)

export const createPackage = (payload, options) =>
  post(`${BASE}/packages`, payload, options)

export const updatePackage = (packageId, payload, options) =>
  put(`${BASE}/packages/${packageId}`, payload, options)

export const removePackage = (packageId, options) =>
  del(`${BASE}/packages/${packageId}`, options)

export const listPackageItems = (packageId, options) =>
  get(`${BASE}/packages/${packageId}/items`, undefined, options)

export const addPackageItem = (packageId, payload, options) =>
  post(`${BASE}/packages/${packageId}/items`, payload, options)

export const removePackageItem = (itemId, options) =>
  del(`${BASE}/packages/items/${itemId}`, options)

// --- Dispatches ---
export const listDispatches = (params, options) =>
  get(`${BASE}/dispatches`, params, options)

export const createDispatch = (payload, options) =>
  post(`${BASE}/dispatches`, payload, options)

export const removeDispatch = (dispatchId, options) =>
  del(`${BASE}/dispatches/${dispatchId}`, options)

export const listDispatchChannels = (dispatchId, options) =>
  get(`${BASE}/dispatches/${dispatchId}/channels`, undefined, options)

export const createDispatchChannel = (dispatchId, payload, options) =>
  post(`${BASE}/dispatches/${dispatchId}/channels`, payload, options)

export const updateDispatchChannel = (dispatchId, channelId, payload, options) =>
  put(`${BASE}/dispatches/${dispatchId}/channels/${channelId}`, payload, options)

export const removeDispatchChannel = (dispatchId, channelId, options) =>
  del(`${BASE}/dispatches/${dispatchId}/channels/${channelId}`, options)

// --- Channel files ---
export const listChannelFiles = (dispatchId, channelId, options) =>
  get(`${BASE}/dispatches/${dispatchId}/channels/${channelId}/files`, undefined, options)

export const removeChannelFile = (dispatchId, channelId, params, options) =>
  del(`${BASE}/dispatches/${dispatchId}/channels/${channelId}/files`, { params, ...options })

export const downloadChannelFile = (dispatchId, channelId, params, options) =>
  get(`${BASE}/dispatches/${dispatchId}/channels/${channelId}/download`, params, options)

/**
 * Загрузка файла в канал dispatch — multipart/form-data, поддерживает прогресс.
 * URL отличается от BASE (/api/v1/uploads/...), поэтому путь склеивается явно.
 * Используем rawRequest, чтобы пробросить onUploadProgress, и сами разворачиваем .data.
 */
export const uploadChannelFile = async (dispatchId, channelId, formData, options) => {
  const response = await rawRequest({
    method: 'post',
    url: `/api/v1/uploads/document-registry/dispatches/${dispatchId}/channels/${channelId}`,
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    ...options,
  })
  return response.data
}
