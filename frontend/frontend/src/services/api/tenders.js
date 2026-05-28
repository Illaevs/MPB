import { get, post, put, patch, del } from './_client'

/**
 * Tenders API — общий модуль для admin и subcontractor контекстов.
 */

const BASE = '/api/v1/tenders'

// ---------------- Admin context ----------------

/** Список deal-products c состоянием тендера (для админа). */
export const listItems = (params, options) =>
  get(`${BASE}/items`, params, options)

export const list = (params, options) =>
  get(`${BASE}/`, params, options)

export const getById = (tenderId, options) =>
  get(`${BASE}/${tenderId}`, undefined, options)

export const create = (payload, options) =>
  post(`${BASE}/`, payload, options)

export const update = (tenderId, payload, options) =>
  put(`${BASE}/${tenderId}`, payload, options)

export const remove = (tenderId, options) =>
  del(`${BASE}/${tenderId}`, options)

export const selectWinner = (tenderId, params, options) =>
  post(`${BASE}/${tenderId}/select-winner`, null, { params, ...options })

// ---------------- Subcontractor context ----------------

/** Тендеры, доступные компании-субподрядчику. */
export const listForCompany = (companyId, options) =>
  get(`${BASE}/company/${companyId}`, undefined, options)

/** Обновление оффера (subcontractor: подача отклика). */
export const updateOffer = (offerId, payload, options) =>
  patch(`${BASE}/offers/${offerId}`, payload, options)
