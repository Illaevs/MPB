import { get, post, patch, del } from './_client'

/**
 * Absences API — отпуска / больничные / командировки.
 *
 * Видимость зависит от роли:
 *  - `absences.read_all` (или users.edit_all/superuser) — все записи
 *  - иначе — только свои
 *
 * Свою запись юзер создаёт без `user_id` (бэк подставит me); админ
 * передаёт `user_id` чужого сотрудника.
 */

const BASE = '/api/v1/absences'

export const list = (params = {}, options) =>
  get(`${BASE}`, params, options)

export const create = (payload = {}, options) =>
  post(`${BASE}`, payload, options)

export const patchOne = (id, payload = {}, options) =>
  patch(`${BASE}/${id}`, payload, options)

export const remove = (id, options) =>
  del(`${BASE}/${id}`, undefined, options)
