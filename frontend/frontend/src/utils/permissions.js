import { normalizeUserAvatar } from './avatar'

const ACTIVE_USER_KEY = 'crm_active_user'
const PERMISSIONS_KEY = 'crm_role_permissions'

export const getActiveUser = () => {
  try {
    const raw = sessionStorage.getItem(ACTIVE_USER_KEY)
    return raw ? normalizeUserAvatar(JSON.parse(raw)) : null
  } catch (e) {
    return null
  }
}

export const getStoredPermissions = () => {
  try {
    const raw = sessionStorage.getItem(PERMISSIONS_KEY)
    return raw ? JSON.parse(raw) : null
  } catch (e) {
    return null
  }
}

export const hasSectionAccess = (section, permissionsOverride = null) => {
  const activeUser = getActiveUser()
  const permissions = permissionsOverride || getStoredPermissions()
  const isSuper = Boolean(permissions?.__superuser__?.read_all)
  if (isSuper) return true
  if (!permissions) {
    return section === 'global_chat' && !!activeUser
  }
  const permission = permissions[section]
  if (!permission && section === 'global_chat') {
    return !!activeUser
  }
  return !!(permission && (permission.read_all || permission.read_assigned))
}

export const saveActiveUser = (user, permissions) => {
  sessionStorage.setItem(ACTIVE_USER_KEY, JSON.stringify(normalizeUserAvatar(user) || null))
  sessionStorage.setItem(PERMISSIONS_KEY, JSON.stringify(permissions || {}))
  localStorage.removeItem(ACTIVE_USER_KEY)
  localStorage.removeItem(PERMISSIONS_KEY)
  window.dispatchEvent(new Event('permissions-updated'))
}

export const clearActiveUser = () => {
  sessionStorage.removeItem(ACTIVE_USER_KEY)
  sessionStorage.removeItem(PERMISSIONS_KEY)
  localStorage.removeItem(ACTIVE_USER_KEY)
  localStorage.removeItem(PERMISSIONS_KEY)
  window.dispatchEvent(new Event('permissions-updated'))
}
