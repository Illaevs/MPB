import { get } from './_client'

const BASE = '/api/v1/customer'

export const listProjects = (options) => get(`${BASE}/projects`, undefined, options)

export const getProject = (projectId, options) =>
  get(`${BASE}/projects/${projectId}`, undefined, options)

export const projectStorageList = (projectId, params, options) =>
  get(`${BASE}/projects/${projectId}/storage/list`, params, options)
