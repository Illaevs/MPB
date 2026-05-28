import { defineStore } from 'pinia'
import axios from 'axios'
import router from '../router'
import { api } from '../services/api'
import { saveActiveUser, clearActiveUser, getActiveUser, getStoredPermissions } from '../utils/permissions'
import { normalizeUserAvatar } from '../utils/avatar'
import { applyServerUiPreferences, disableUiSync } from '../composables/useUiPreferences'

const PENDING_2FA_KEY = 'crm_pending_2fa'
const PENDING_2FA_SETUP_KEY = 'crm_pending_2fa_setup'

const normalizePermissions = (permissions = {}, isSuperuser = false) => {
  const normalized = {}
  // Per-section: ensure 4 booleans + edit⇒read implication (defensive —
  // backend already normalizes, but storage may predate the 4-flag model).
  for (const [key, value] of Object.entries(permissions || {})) {
    if (key === '__superuser__') continue
    const v = value || {}
    const editAll = Boolean(v.edit_all)
    const editAssigned = Boolean(v.edit_assigned)
    normalized[key] = {
      read_all: Boolean(v.read_all) || editAll,
      read_assigned: Boolean(v.read_assigned) || editAssigned,
      edit_all: editAll,
      edit_assigned: editAssigned
    }
  }
  if (isSuperuser) {
    normalized.__superuser__ = {
      read_all: true, read_assigned: true,
      edit_all: true, edit_assigned: true
    }
  }
  return normalized
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: null,
    refreshToken: null,
    user: null,
    permissions: {},
    isSuperuser: false,
    pendingTwoFactor: null,
    pendingTwoFactorSetup: null,
    sessionChecked: false
  }),
  actions: {
    loadFromStorage() {
      this.accessToken = null
      this.refreshToken = null
      this.user = null
      this.permissions = getStoredPermissions() || {}
      this.isSuperuser = Boolean(this.permissions?.__superuser__?.read_all)
      this.sessionChecked = false
      try {
        const raw = sessionStorage.getItem(PENDING_2FA_KEY)
        this.pendingTwoFactor = raw ? JSON.parse(raw) : null
      } catch (e) {
        this.pendingTwoFactor = null
      }
      try {
        const raw = sessionStorage.getItem(PENDING_2FA_SETUP_KEY)
        this.pendingTwoFactorSetup = raw ? JSON.parse(raw) : null
      } catch (e) {
        this.pendingTwoFactorSetup = null
      }
      axios.defaults.withCredentials = true
    },
    _persistPendingTwoFactor(payload) {
      this.pendingTwoFactor = payload || null
      try {
        if (payload) {
          sessionStorage.setItem(PENDING_2FA_KEY, JSON.stringify(payload))
        } else {
          sessionStorage.removeItem(PENDING_2FA_KEY)
        }
      } catch (e) {
        // ignore storage errors
      }
    },
    _persistPendingTwoFactorSetup(payload) {
      this.pendingTwoFactorSetup = payload || null
      try {
        if (payload) {
          sessionStorage.setItem(PENDING_2FA_SETUP_KEY, JSON.stringify(payload))
        } else {
          sessionStorage.removeItem(PENDING_2FA_SETUP_KEY)
        }
      } catch (e) {
        // ignore storage errors
      }
    },
    _clearSessionState() {
      this.accessToken = null
      this.refreshToken = null
      this.user = null
      this.permissions = {}
      this.isSuperuser = false
      clearActiveUser()
      disableUiSync()
    },
    setSession({ user, permissions, is_superuser, requires_2fa_setup }) {
      const normalizedUser = normalizeUserAvatar(user || null)
      const normalizedPermissions = normalizePermissions(permissions, is_superuser)
      this.accessToken = normalizedUser ? 'cookie-session' : null
      this.refreshToken = normalizedUser ? 'cookie-session' : null
      this.user = normalizedUser || null
      this.permissions = normalizedPermissions
      this.isSuperuser = Boolean(is_superuser)
      this.sessionChecked = true
      this._persistPendingTwoFactor(null)
      // Бэк — единственный источник истины по необходимости setup 2FA.
      // Если он явно сказал «нужен setup» и юзер ещё без 2FA —
      // выставляем pending, чтобы router увёл на форму. Иначе —
      // принудительно очищаем, чтобы не зависать на устаревшем pending
      // из sessionStorage прошлой попытки.
      if (requires_2fa_setup === true
          && normalizedUser
          && normalizedUser.two_factor_enabled === false) {
        this._persistPendingTwoFactorSetup({
          email: normalizedUser.email || ''
        })
      } else {
        this._persistPendingTwoFactorSetup(null)
      }
      if (normalizedUser) {
        saveActiveUser(normalizedUser, normalizedPermissions)
        applyServerUiPreferences(normalizedUser.ui_preferences)
      } else {
        clearActiveUser()
        disableUiSync()
      }
    },
    setPendingTwoFactor({ challenge_token, email }) {
      this._clearSessionState()
      this.sessionChecked = true
      this._persistPendingTwoFactor({
        challenge_token,
        email: email || ''
      })
    },
    setPendingTwoFactorSetup({ email }) {
      this.accessToken = 'cookie-session'
      this.refreshToken = 'cookie-session'
      this.sessionChecked = true
      this._persistPendingTwoFactorSetup({
        email: email || ''
      })
    },
    cancelPendingTwoFactor() {
      this._persistPendingTwoFactor(null)
    },
    clearPendingTwoFactorSetup() {
      this._persistPendingTwoFactorSetup(null)
    },
    async restoreSession(force = false) {
      if (!force && this.sessionChecked && this.accessToken) return this.user
      if (!force && this.sessionChecked && !this.accessToken) return null
      try {
        const data = await api.auth.session()
        this.setSession(data || {})
        return this.user
      } catch (e) {
        // Сессии нет → также снимаем все «висящие» pending-флоу.
        // Без этого после смены БД (или сброса бэка) фронт упорно
        // ведёт юзера на форму setup 2FA, хотя setup-токен в бэке
        // давно просрочен — TOTP даёт 400 «неверный код».
        this._persistPendingTwoFactor(null)
        this._persistPendingTwoFactorSetup(null)
        this._clearSessionState()
        this.sessionChecked = true
        return null
      }
    },
    async login(email, password) {
      const data = (await api.auth.login({ email, password })) || {}
      if (data.requires_2fa && data.challenge_token) {
        this.setPendingTwoFactor({
          challenge_token: data.challenge_token,
          email
        })
        return data
      }
      if (data.requires_2fa_setup) {
        this.setSession(data)
        this.setPendingTwoFactorSetup({
          email: data?.user?.email || email
        })
        return data
      }
      // Если бэк больше не требует setup 2FA — снимаем любой
      // pendingTwoFactorSetup, висящий от предыдущей попытки. Иначе
      // фронт упорно ведёт на форму setup, хотя бэк уже выключил
      // требование (например, REQUIRE_TWO_FACTOR=false на локалке).
      this.clearPendingTwoFactorSetup()
      this.setSession(data)
      return data
    },
    async verifyTwoFactor(code) {
      if (!this.pendingTwoFactor?.challenge_token) {
        throw new Error('Не найден challenge token для 2FA.')
      }
      const data = await api.auth.verifyTwoFactor({
        challenge_token: this.pendingTwoFactor.challenge_token,
        code
      })
      this.setSession(data || {})
      return data
    },
    async refresh() {
      const data = await api.auth.refresh()
      this.setSession(data || {})
      return data
    },
    async impersonate(userId) {
      const data = await api.auth.impersonate(userId)
      this.setSession(data || {})
      return data
    },
    updateUserPatch(patch) {
      if (!this.user) return
      this.user = normalizeUserAvatar({ ...this.user, ...(patch || {}) })
      saveActiveUser(this.user, this.permissions)
    },
    async fetchTwoFactorStatus() {
      return await api.auth.twoFactorStatus()
    },
    async startTwoFactorSetup() {
      return await api.auth.startTwoFactorSetup()
    },
    async confirmTwoFactorSetup(secret, code) {
      const data = await api.auth.confirmTwoFactorSetup({ secret, code })
      this.updateUserPatch({
        two_factor_enabled: true,
        two_factor_enabled_at: data?.enabled_at || new Date().toISOString()
      })
      return data
    },
    async disableTwoFactor(password) {
      const data = await api.auth.disableTwoFactor({ password })
      this.updateUserPatch({
        two_factor_enabled: false,
        two_factor_enabled_at: null
      })
      return data
    },
    async regenerateTwoFactorBackupCodes(code) {
      return await api.auth.regenerateTwoFactorBackupCodes({ code })
    },
    async logout() {
      this._persistPendingTwoFactor(null)
      this._persistPendingTwoFactorSetup(null)
      try {
        await api.auth.logout()
      } catch (e) {
        // ignore logout failures
      } finally {
        this._clearSessionState()
        this.sessionChecked = true
      }
      router.push('/login')
    }
  }
})
