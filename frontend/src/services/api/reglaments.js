import { del, get, post, rawRequest } from './_client'

/**
 * Нормативная база (Reglaments Phase 0+1+2): СНиП / ГОСТ / СП / ФЗ / ПП.
 *
 * Изолированный домен от основного поиска — свои таблицы (reglament_fts,
 * reglament_embeddings), свой ranking. UI: страница /reglaments.
 *
 * Backend endpoints (см. backend/app/routers/reglaments.py):
 *  - GET   /api/v1/reglaments               — каталог (фильтры по doc_type/status/discipline/q)
 *  - GET   /api/v1/reglaments/{id}          — детальный документ + оглавление
 *  - GET   /api/v1/reglaments/sections/{id} — полный текст одной секции
 *  - POST  /api/v1/reglaments/search        — FTS5 + cosine hybrid search
 */

const BASE = '/api/v1/reglaments'

export const list = (params = {}, options) =>
  get(BASE, { ...params }, options)

export const getById = (id, options) =>
  get(`${BASE}/${id}`, undefined, options)

export const getSection = (sectionId, options) =>
  get(`${BASE}/sections/${sectionId}`, undefined, options)

export const search = (
  {
    query,
    limit = 20,
    offset = 0,
    doc_types = null,
    statuses = null,
    disciplines = null,
  } = {},
  options,
) =>
  post(
    `${BASE}/search`,
    { query, limit, offset, doc_types, statuses, disciplines },
    options,
  )

/** Phase 3 admin-only. */

/** Создать новую норму с метаданными (без файла). 409 если такой
 *  (doc_type, doc_number) уже существует. */
export const create = (payload, options) =>
  post(BASE, payload, options)

/** Залить PDF/DOCX к существующей норме. Парсинг и embedding запускаются
 *  на бэке (embedding — в background-task). Возвращает {sections_parsed,
 *  total_chars, embedding_scheduled}. */
export const uploadFile = (reglamentId, file, options) => {
  const fd = new FormData()
  fd.append('file', file)
  return rawRequest({
    method: 'post',
    url: `${BASE}/${reglamentId}/upload`,
    data: fd,
    headers: { 'Content-Type': 'multipart/form-data' },
    ...options,
  }).then(r => r.data)
}

/** Перезапустить embedding для всех секций нормы (после смены модели). */
export const reindex = (reglamentId, options) =>
  post(`${BASE}/${reglamentId}/reindex`, undefined, options)

/** Удалить норму со всеми секциями и embeddings. */
export const remove = (reglamentId, options) =>
  del(`${BASE}/${reglamentId}`, undefined, options)
