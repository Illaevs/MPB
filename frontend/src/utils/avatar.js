const normalizeUserIdLike = (value) => {
  const raw = String(value || '').trim()
  if (!raw) return ''
  const uuid32 = /^[0-9a-f]{32}$/i
  if (uuid32.test(raw)) {
    return `${raw.slice(0, 8)}-${raw.slice(8, 12)}-${raw.slice(12, 16)}-${raw.slice(16, 20)}-${raw.slice(20)}`
  }
  return raw
}

const extractUserIdFromAvatarUrl = (avatarUrl) => {
  const raw = String(avatarUrl || '').trim()
  if (!raw) return ''
  const fileName = raw.split('?', 1)[0].split('/').pop() || ''
  const stem = fileName.replace(/\.[^.]+$/, '')
  if (!stem.includes('-')) return ''
  const parts = stem.split('-')
  const last = parts[parts.length - 1] || ''
  if (/^[0-9a-f]{32}$/i.test(last)) {
    return normalizeUserIdLike(parts.slice(0, -1).join('-'))
  }
  return ''
}

export const normalizeAvatarUrl = (avatarUrl, userId = null) => {
  const raw = String(avatarUrl || '').trim()
  const normalizedUserId = normalizeUserIdLike(userId) || extractUserIdFromAvatarUrl(raw)
  if (!raw) return ''

  if (raw.startsWith('/api/v1/users/avatar-user/')) {
    return normalizedUserId
      ? `/api/v1/users/avatar-user/${encodeURIComponent(normalizedUserId)}`
      : raw
  }

  if (
    normalizedUserId &&
    (
      raw.startsWith('/api/v1/users/avatar/') ||
      raw.startsWith('/api/v1/users/avatar-file/') ||
      raw.startsWith('/static/avatars/')
    )
  ) {
    return `/api/v1/users/avatar-user/${encodeURIComponent(normalizedUserId)}`
  }

  return raw
}

export const normalizeUserAvatar = (user) => {
  if (!user || typeof user !== 'object') return user
  return {
    ...user,
    avatar_url: normalizeAvatarUrl(user.avatar_url, user.id)
  }
}
