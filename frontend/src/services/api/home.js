import { get } from './_client'

const BASE = '/api/v1/dashboard'

export const summary = (options) => get(`${BASE}/summary`, undefined, options)

export const activity = (params, options) => get(`${BASE}/activity`, params, options)

export const managerSummary = (options) =>
  get(`${BASE}/manager-summary`, undefined, options)

// Счётчики виджета «Мои задачи»: { doing, helping, assigned, watching }.
export const myTaskCounts = (options) =>
  get(`${BASE}/my-task-counts`, undefined, options)
