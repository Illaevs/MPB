import { get, post } from './_client'

const BASE = '/api/v1/auth'

export const session = (options) => get(`${BASE}/session`, undefined, options)

export const login = (payload, options) => post(`${BASE}/login`, payload, options)

export const verifyTwoFactor = (payload, options) =>
  post(`${BASE}/verify-2fa`, payload, options)

export const refresh = (options) => post(`${BASE}/refresh`, {}, options)

export const impersonate = (userId, options) =>
  post(`${BASE}/impersonate/${userId}`, undefined, options)

export const logout = (options) => post(`${BASE}/logout`, undefined, options)

export const twoFactorStatus = (options) =>
  get(`${BASE}/2fa/status`, undefined, options)

export const startTwoFactorSetup = (options) =>
  post(`${BASE}/2fa/setup/start`, undefined, options)

export const confirmTwoFactorSetup = (payload, options) =>
  post(`${BASE}/2fa/setup/confirm`, payload, options)

export const disableTwoFactor = (payload, options) =>
  post(`${BASE}/2fa/disable`, payload, options)

export const regenerateTwoFactorBackupCodes = (payload, options) =>
  post(`${BASE}/2fa/regenerate-backup-codes`, payload, options)
