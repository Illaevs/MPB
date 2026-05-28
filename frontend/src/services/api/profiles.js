import { get, patch } from './_client'

/**
 * Profiles API — расширенная карточка сотрудника.
 *
 * Эндпоинты публично-читаемые (любой авторизованный видит любой
 * профиль), а правка делится:
 *  - `patchMe(...)`        — личные поля своего профиля
 *  - `patchUser(uid,...)`  — формальные поля (только админ, `users.edit_all`)
 *
 * `suggest(field, q)` — автокомплит чипов: возвращает массив строк
 * по полю `skills` | `interests`, отсортированный по частоте.
 */

const BASE = '/api/v1/profiles'

export const getMe = (options) =>
  get(`${BASE}/me`, undefined, options)

export const patchMe = (payload = {}, options) =>
  patch(`${BASE}/me`, payload, options)

export const getUser = (userId, options) =>
  get(`${BASE}/${userId}`, undefined, options)

export const patchUser = (userId, payload = {}, options) =>
  patch(`${BASE}/${userId}`, payload, options)

export const suggest = (field, q = '', limit = 20, options) =>
  get(`${BASE}/suggest`, { field, q: q || undefined, limit }, options)

// Ближайшие дни рождения сотрудников (окно в днях).
export const birthdays = (window = 30, options) =>
  get(`${BASE}/birthdays`, { window }, options)
