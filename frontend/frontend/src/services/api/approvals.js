import { get, post, put, del } from './_client'

const BASE = '/api/v1/approvals'

export const meta = (options) => get(`${BASE}/meta`, undefined, options)

export const listTemplates = (options) => get(`${BASE}/templates`, undefined, options)

export const listRuntimeTemplates = (params, options) =>
  get(`${BASE}/templates/runtime`, params, options)

export const createTemplate = (payload, options) =>
  post(`${BASE}/templates`, payload, options)

export const updateTemplate = (id, payload, options) =>
  put(`${BASE}/templates/${id}`, payload, options)

export const removeTemplate = (id, options) =>
  del(`${BASE}/templates/${id}`, options)

export const duplicateTemplate = (id, options) =>
  post(`${BASE}/templates/${id}/duplicate`, undefined, options)

export const templateUsage = (id, options) =>
  get(`${BASE}/templates/${id}/usage`, undefined, options)

export const inbox = (params, options) =>
  get(`${BASE}/inbox`, params, options)

export const listInstances = (params, options) =>
  get(`${BASE}/instances`, params, options)

export const createInstance = (payload, options) =>
  post(`${BASE}/instances`, payload, options)

export const getInstance = (instanceId, options) =>
  get(`${BASE}/instances/${instanceId}`, undefined, options)

export const approveInstance = (instanceId, payload, options) =>
  post(`${BASE}/instances/${instanceId}/approve`, payload, options)

export const rejectInstance = (instanceId, payload, options) =>
  post(`${BASE}/instances/${instanceId}/reject`, payload, options)
