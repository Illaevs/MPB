import { get, post, put, del } from './_client'

const BASE = '/api/v1/projects'

/**
 * Доменный модуль "projects".
 *
 * NB: В текущей версии бэкенда основной CRUD по «проектам/сделкам» живёт на
 * /api/v1/deals/* — см. api.deals. Этот модуль зарезервирован под будущие
 * endpoints под префиксом /api/v1/projects/... и сейчас предоставляет лишь
 * базовый скелет, чтобы единая точка входа имела симметрию по доменам.
 */

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
