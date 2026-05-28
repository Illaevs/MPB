import { get, post, patch, del } from './_client'

/**
 * Org structure (организационная структура — дерево) API.
 */

const BASE = '/api/v1/org-structure'

/** Дерево узлов (вложенное); flat=1 — плоский список. */
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

/** Привязка/снятие пользователя с узла. org_unit_id=null — снять. */
export const assign = (userId, orgUnitId, options) =>
  post(`${BASE}/assign`, { user_id: userId, org_unit_id: orgUnitId || null }, options)
