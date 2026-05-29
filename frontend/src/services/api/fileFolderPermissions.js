import { get, post, del } from './_client'

/**
 * Управление per-folder ACL для Files Catalog.
 *
 * Backend: backend/app/routers/file_folder_permissions.py (Stage 3).
 *  - GET    /api/v1/files-catalog/permissions?path=<folder>
 *  - POST   /api/v1/files-catalog/permissions
 *  - DELETE /api/v1/files-catalog/permissions/{id}
 *
 * Все три эндпоинта требуют MANAGE на folder_path (роутер кидает 403,
 * если у текущего пользователя его нет). Под entity-paths
 * (/deals/, /contracts/, …) POST вернёт 400, GET — пустой ответ с
 * флагом is_entity_path=true.
 */

const BASE = '/api/v1/files-catalog/permissions'

/**
 * GET — список правил по папке (explicit + inherited) + effective_for_me.
 * @param {string} path Полный путь к папке (включая опциональный disk:-префикс).
 */
export const list = (path, options) =>
  get(BASE, { path }, options)

/**
 * POST — идемпотентный upsert по unique key
 * (folder_path, principal_type, principal_id).
 *
 * @param {{folder_path: string, principal_type: 'user'|'role',
 *          principal_id: string, can_read: boolean, can_write: boolean,
 *          can_delete: boolean, can_manage_perms: boolean,
 *          inherit_to_subfolders: boolean}} payload
 */
export const upsert = (payload, options) =>
  post(BASE, payload, options)

/**
 * DELETE — удаление правила по id.
 */
export const remove = (ruleId, options) =>
  del(`${BASE}/${encodeURIComponent(String(ruleId))}`, options)
