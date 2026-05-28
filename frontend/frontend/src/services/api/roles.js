import { get, post, put, del } from './_client'

const BASE = '/api/v1/roles'

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

/** Список доступных секций (для конфигурирования прав). */
export const listSections = (options) =>
  get(`${BASE}/sections`, undefined, options)

export const getPermissions = (roleId, options) =>
  get(`${BASE}/${roleId}/permissions`, undefined, options)

export const updatePermissions = (roleId, payload, options) =>
  put(`${BASE}/${roleId}/permissions`, payload, options)
