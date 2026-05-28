import { get, post, put, del } from './_client'

const BASE = '/api/v1/products'

/* ---- Каталог товаров (товары как сущности) ---- */

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

/* ---- Товары лида ---- */

export const listLeadProducts = (leadId, options) =>
  get(`${BASE}/lead/${leadId}`, undefined, options)

export const createLeadProduct = (payload, options) =>
  post(`${BASE}/lead/`, payload, options)

export const updateLeadProduct = (id, payload, options) =>
  put(`${BASE}/lead/${id}`, payload, options)

export const removeLeadProduct = (id, options) =>
  del(`${BASE}/lead/${id}`, options)

/* ---- Товары сделки ---- */

export const listDealProducts = (dealId, options) =>
  get(`${BASE}/deal/${dealId}`, undefined, options)

export const createDealProduct = (payload, options) =>
  post(`${BASE}/deal/`, payload, options)

export const updateDealProduct = (id, payload, options) =>
  put(`${BASE}/deal/${id}`, payload, options)

export const removeDealProduct = (id, options) =>
  del(`${BASE}/deal/${id}`, options)

export const quickAddToDeal = (dealId, productId, payload, options) =>
  post(`${BASE}/deal/${dealId}/quick-add/${productId}`, payload, options)
