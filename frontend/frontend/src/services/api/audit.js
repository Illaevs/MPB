import { get } from './_client'

const BASE = '/api/v1/audit-logs'

export const list = (params, options) => get(`${BASE}/`, params, options)
