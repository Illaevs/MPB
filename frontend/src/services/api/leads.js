import { get, post, put, del } from './_client'

const BASE = '/api/v1/leads'

/* ---- CRUD ---- */

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

/* ---- Конвертация в сделку ---- */

export const convert = (id, payload, options) =>
  post(`${BASE}/${id}/convert`, payload, options)

/* ---- Лента активности / таймлайн ---- */

export const timeline = (id, params, options) =>
  get(`${BASE}/${id}/timeline`, params, options)

export const addComment = (id, payload, options) =>
  post(`${BASE}/${id}/comments`, payload, options)

export const addTask = (id, payload, options) =>
  post(`${BASE}/${id}/tasks`, payload, options)

export const uploadFile = (id, formData, options) =>
  post(`${BASE}/${id}/files`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    ...options,
  })

export const removeActivity = (activityId, options) =>
  del(`${BASE}/activities/${activityId}`, options)
