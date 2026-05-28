/**
 * "calendar" — это представление, использующее tasks + legal-work.
 * Для удобства миграции прокидываем тонкие шорткаты к нужным эндпоинтам.
 */
import { get, post, put } from './_client'

const TASKS = '/api/v1/tasks/'

export const listTasks = (params, options) => get(TASKS, params, options)
export const createTask = (payload, options) => post(TASKS, payload, options)
export const updateTask = (taskId, payload, options) =>
  put(`${TASKS}${taskId}`, payload, options)

export const listLegalCases = (options) =>
  get('/api/v1/legal-work', undefined, options)
