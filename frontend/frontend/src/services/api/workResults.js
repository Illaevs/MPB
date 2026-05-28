import { get, post, put, patch, del } from './_client'

/**
 * Work-results / result-reviews API.
 */

const BASE = '/api/v1/result-reviews'

export const list = (params, options) =>
  get(`${BASE}/`, params, options)

export const getById = (id, options) =>
  get(`${BASE}/${id}`, undefined, options)

export const create = (payload, options) =>
  post(`${BASE}/`, payload, options)

export const update = (id, payload, options) =>
  put(`${BASE}/${id}`, payload, options)

export const patchReview = (id, payload, options) =>
  patch(`${BASE}/${id}`, payload, options)

export const remove = (id, options) =>
  del(`${BASE}/${id}`, options)

export const listVersions = (params, options) =>
  get(`${BASE}/versions`, params, options)
