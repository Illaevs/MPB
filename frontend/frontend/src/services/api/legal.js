import { get, post, put, del } from './_client'

const BASE = '/api/v1/legal-work'

export const list = (options) => get(`${BASE}/`, undefined, options)

export const getById = (caseId, options) => get(`${BASE}/${caseId}`, undefined, options)

export const create = (payload, options) => post(`${BASE}/`, payload, options)

export const update = (caseId, payload, options) => put(`${BASE}/${caseId}`, payload, options)

export const remove = (caseId, options) => del(`${BASE}/${caseId}`, options)

export const addEvent = (caseId, payload, options) =>
  post(`${BASE}/${caseId}/events`, payload, options)

export const removeEvent = (eventId, options) =>
  del(`${BASE}/events/${eventId}`, options)

export const downloadEventFileMeta = (fileId, options) =>
  get(`${BASE}/events/files/${fileId}/download`, undefined, options)

export const removeEventFile = (fileId, options) =>
  del(`${BASE}/events/files/${fileId}`, options)

export const linkTask = (caseId, payload, options) =>
  post(`${BASE}/${caseId}/tasks/link`, payload, options)

export const unlinkTask = (caseId, taskId, options) =>
  del(`${BASE}/${caseId}/tasks/${taskId}`, options)
