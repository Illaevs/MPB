import { get, post, put, patch, del } from './_client'

/**
 * Income/Expense (ДДС) API.
 */

const BASE = '/api/v1/income-expense'

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

export const count = (params, options) =>
  get(`${BASE}/count`, params, options)

export const bulkUpdate = (payload, options) =>
  patch(`${BASE}/bulk/update`, payload, options)
