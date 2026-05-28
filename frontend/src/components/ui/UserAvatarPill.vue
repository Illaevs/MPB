<template>
  <div class="user-pill" :class="{ 'user-pill--clickable': removable }">
    <span
      class="user-pill__avatar"
      :class="{ 'user-pill__avatar--image': !!avatarUrl }"
      :style="avatarUrl ? null : avatarStyle"
    >
      <img v-if="avatarUrl" :src="avatarUrl" :alt="displayName" />
      <span v-else>{{ initial }}</span>
    </span>
    <button
      v-if="removable"
      type="button"
      class="user-pill__remove"
      :title="'Убрать ' + displayName"
      @click.stop="$emit('remove')"
    >
      <i class="fas fa-times"></i>
    </button>
    <div class="user-pill__tooltip" role="tooltip">
      <strong>{{ displayName }}</strong>
      <span v-if="email" class="user-pill__tooltip-email">{{ email }}</span>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { normalizeAvatarUrl } from '../../utils/avatar'

const AVATAR_THEMES = [
  { background: 'linear-gradient(135deg, #d7e7ff 0%, #b4d0ff 100%)', color: '#2563eb' },
  { background: 'linear-gradient(135deg, #ffe4d3 0%, #ffc79c 100%)', color: '#b45309' },
  { background: 'linear-gradient(135deg, #e8ddff 0%, #c8b4ff 100%)', color: '#7c3aed' },
  { background: 'linear-gradient(135deg, #d9f7ec 0%, #a9e7cb 100%)', color: '#0f8f5d' },
  { background: 'linear-gradient(135deg, #ffe7ef 0%, #ffc3d3 100%)', color: '#be185d' }
]
function themeFor(seed) {
  const key = String(seed || '?')
  const idx = key.split('').reduce((sum, ch) => sum + ch.charCodeAt(0), 0) % AVATAR_THEMES.length
  return AVATAR_THEMES[idx]
}

export default {
  name: 'UserAvatarPill',
  props: {
    user: { type: Object, required: true },
    removable: { type: Boolean, default: true }
  },
  emits: ['remove'],
  setup(props) {
    const displayName = computed(() => {
      const u = props.user
      return u?.full_name || u?.email || String(u?.id || 'Пользователь')
    })
    const email = computed(() => props.user?.email || '')
    const initial = computed(() => String(displayName.value || '?').trim().charAt(0).toUpperCase() || '?')
    const avatarUrl = computed(() => {
      const u = props.user
      const raw = String(u?.avatar_url || '').trim()
      if (!raw) return ''
      try { return normalizeAvatarUrl(raw, u?.id) || '' } catch (_) { return raw }
    })
    const avatarStyle = computed(() => themeFor(`${props.user?.id || ''}${displayName.value || ''}`))
    return { displayName, email, initial, avatarUrl, avatarStyle }
  }
}
</script>

<style scoped>
.user-pill {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding-right: 2px;
}

.user-pill__avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
  font-weight: var(--fw-bold);
  overflow: hidden;
  border: 2px solid var(--color-surface);
  box-shadow: var(--shadow-xs);
  cursor: default;
}
.user-pill__avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-pill__remove {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 0;
  background: var(--color-surface-3);
  color: var(--color-text-muted);
  font-size: 9px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}
.user-pill:hover .user-pill__remove { opacity: 1; }
.user-pill__remove:hover { background: var(--color-danger-soft); color: var(--color-danger); }
.user-pill__remove:focus-visible {
  opacity: 1;
  outline: none;
  box-shadow: var(--shadow-focus);
}

/* Tooltip: appears on hover/focus of the pill */
.user-pill__tooltip {
  position: absolute;
  bottom: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%);
  background: var(--color-text);
  color: var(--color-text-inverse);
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-md);
  white-space: nowrap;
  font-size: var(--text-sm);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 1px;
  opacity: 0;
  pointer-events: none;
  transition: opacity var(--dur-fast) var(--ease-out), transform var(--dur-fast) var(--ease-out);
  z-index: 10;
  max-width: 320px;
}
.user-pill__tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 4px solid transparent;
  border-top-color: var(--color-text);
}
.user-pill__tooltip-email {
  font-weight: var(--fw-regular);
  color: var(--color-text-subtle);
  font-size: var(--text-xs);
}
.user-pill:hover .user-pill__tooltip,
.user-pill:focus-within .user-pill__tooltip {
  opacity: 1;
  transform: translateX(-50%) translateY(-2px);
}
</style>
