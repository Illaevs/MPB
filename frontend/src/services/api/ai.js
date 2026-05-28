import { get, post } from './_client'

const BASE = '/api/v1/ai'

export const status = (options) => get(`${BASE}/status`, undefined, options)

export const assistantChat = (payload, options) =>
  post(`${BASE}/assistant/chat`, payload, options)
