import { get } from './_client'

/**
 * Finance dashboard / overview.
 *
 * Treasury и import-bank-statement живут в собственном модуле (`treasury.js`).
 */

const BASE = '/api/v1/finance'

export const overview = (params, options) =>
  get(`${BASE}/overview`, params, options)
