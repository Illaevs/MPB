import { get, post, put, patch, del } from './_client'

/**
 * Work-results / result-reviews API.
 */

const BASE = '/api/v1/result-reviews'

// Backend route is GET /api/v1/result-reviews (NO trailing slash). Using a
// trailing slash here triggers a 307 redirect to an absolute backend URL,
// which the page CSP (connect-src 'self' https:) then blocks.
export const list = (params, options) =>
  get(BASE, params, options)

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
