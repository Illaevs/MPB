import { get, post, del } from './_client'

const BASE = '/api/v1/executor'

export const listCards = (options) => get(`${BASE}/cards`, undefined, options)

export const getStage = (stageId, params, options) =>
  get(`${BASE}/stages/${stageId}`, params, options)

export const storageList = (params, options) =>
  get(`${BASE}/storage/list`, params, options)

export const storageDownload = (params, options) =>
  get(`${BASE}/storage/download`, params, options)

export const storageUpload = (formData, options) =>
  post(`${BASE}/storage/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    ...options,
  })

export const storageDelete = (params, options) =>
  del(`${BASE}/storage/delete`, { params, ...options })

export const listResults = (params, options) =>
  get(`${BASE}/results`, params, options)

export const removeResult = (resultId, options) =>
  del(`${BASE}/results/${resultId}`, options)

export const uploadResults = (formData, options) =>
  post('/api/v1/uploads/executor/results', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    ...options,
  })
