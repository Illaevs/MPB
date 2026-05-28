import { get, post, del } from './_client'

const BASE = '/api/v1/files-catalog'

/**
 * CRUD для каталога файлов реализован через несколько action-эндпоинтов
 * (list / mkdir / rename / move / delete). Сохраняем семантику оригинальных
 * URL, но даём «привычные» имена list/getById/create/update/remove там,
 * где это разумно.
 */

// --- Listing ---
export const list = (params, options) =>
  get(`${BASE}/list`, params, options)

// Алиасы для соответствия общему контракту модулей (нет concept «getById»
// для путей, поэтому мапим в list по конкретному пути).
export const getById = (path, options) =>
  get(`${BASE}/list`, { path }, options)

// --- Download (returns { href } or external link) ---
export const getDownloadLink = (params, options) =>
  get(`${BASE}/download`, params, options)

// --- Mutations ---
export const createFolder = (payload, options) =>
  post(`${BASE}/mkdir`, payload, options)

// «create» в смысле общего контракта — создание папки.
export const create = createFolder

export const rename = (payload, options) =>
  post(`${BASE}/rename`, payload, options)

// «update» — переименование (единственная mutating-операция над метаданными).
export const update = rename

export const move = (payload, options) =>
  post(`${BASE}/move`, payload, options)

export const remove = (params, options) =>
  del(BASE, { params, ...options })

/**
 * URL загрузки. Возвращается строкой — реальная загрузка делается через
 * XMLHttpRequest для нативного прогресса (см. FilesCatalog.vue::uploadFormData).
 */
export const uploadUrl = (path) =>
  `${BASE}/upload?path=${encodeURIComponent(path)}`

// --- Storage usage (живёт под другим префиксом, но логически принадлежит модулю) ---
export const getStorageUsage = (options) =>
  get('/api/v1/storage/usage', undefined, options)
