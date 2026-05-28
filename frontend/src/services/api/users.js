import { get, post, put, patch, del } from './_client'

const BASE = '/api/v1/users'

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

export const listCompanyLinks = (params, options) =>
  get(`${BASE}/company-links`, params, options)

export const addCompanyLink = (userId, payload, options) =>
  post(`${BASE}/${userId}/company-links`, payload, options)

export const removeCompanyLink = (userId, linkId, options) =>
  del(`${BASE}/${userId}/company-links/${linkId}`, options)

export const updateMyAvatar = (formData, options) =>
  post(`${BASE}/me/avatar`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    ...options,
  })

export const updateMyWallpaper = (formData, options) =>
  post(`${BASE}/me/wallpaper`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    ...options,
  })

export const removeMyWallpaper = (options) =>
  del(`${BASE}/me/wallpaper`, options)

export const getMyUiPreferences = (options) =>
  get(`${BASE}/me/ui-preferences`, undefined, options)

export const updateMyUiPreferences = (prefs, options) =>
  patch(`${BASE}/me/ui-preferences`, prefs, options)

/** URL аватарки/файла — для прямой подстановки в <img src>. */
export const avatarUserUrl = (userId) =>
  `${BASE}/avatar-user/${encodeURIComponent(String(userId || '').trim())}`
