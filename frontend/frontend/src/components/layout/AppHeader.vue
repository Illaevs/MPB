<template>
  <header class="content-header">
    <button class="content-header__search" type="button" @click="$emit('open-search')">
      <i class="fas fa-search"></i>
      <span class="content-header__search-label">Поиск по системе...</span>
      <span class="content-header__search-shortcut">Ctrl+K</span>
    </button>
    <div class="content-header__actions">
      <div class="content-header__tools">
        <button class="header-utility-btn" title="Калькулятор НДС" @click="$emit('open-vat')">
          <i class="fas fa-calculator"></i>
        </button>
        <button
          class="header-utility-btn"
          :disabled="!activeUser"
          title="Двухфакторная аутентификация"
          @click="$emit('open-two-factor')"
        >
          <i class="fas fa-shield-halved"></i>
        </button>
        <button
          class="header-utility-btn notification-bell"
          title="Уведомления"
          @click="$emit('open-notifications')"
        >
          <i class="fas fa-bell"></i>
          <span v-if="unreadCount" class="badge badge-danger badge-sm notification-badge">
            {{ unreadCount > 99 ? '99+' : unreadCount }}
          </span>
        </button>
        <input
          ref="wallpaperInput"
          type="file"
          class="user-avatar-input"
          accept="image/png,image/jpeg,image/gif"
          @change="onWallpaperPicked"
        >
        <button
          class="header-utility-btn"
          :class="{ 'is-active': !!activeUser?.wallpaper_url }"
          :disabled="!activeUser || uploadingWallpaper"
          :title="activeUser ? 'Загрузить обои интерфейса' : 'Пользователь не выбран'"
          @click="triggerWallpaperPicker"
        >
          <i class="fas" :class="uploadingWallpaper ? 'fa-spinner fa-spin' : 'fa-image'"></i>
        </button>
        <button
          v-if="activeUser?.wallpaper_url"
          class="header-utility-btn"
          :disabled="uploadingWallpaper"
          title="Вернуть стандартные обои"
          @click="clearWallpaper"
        >
          <i class="fas fa-image-slash"></i>
        </button>
      </div>
      <div class="content-header__divider"></div>
      <div
        v-if="(activeUser?.rating || 0) > 0 || (activeUser?.rating_count || 0) > 0"
        class="user-rating"
        title="Ваш рейтинг"
      >
        <span class="rating-value">{{ (activeUser?.rating || 0).toFixed(2) }}</span>
        <i class="fas fa-star text-warning"></i>
        <span class="rating-count">({{ activeUser?.rating_count || 0 }})</span>
      </div>
      <div class="content-header__time">{{ currentTimeLabel }}</div>
      <div class="user-profile content-header__profile d-flex align-center gap-2">
        <div class="user-profile__meta">
          <div class="user-profile__name">{{ activeUser?.full_name || 'Пользователь не выбран' }}</div>
          <div class="user-profile__hint">
            {{ activeUser ? 'Активный пользователь' : 'Выберите в разделе Пользователи' }}
          </div>
        </div>
        <input
          ref="avatarInput"
          type="file"
          class="user-avatar-input"
          accept="image/png,image/jpeg,image/webp,image/gif"
          @change="onAvatarPicked"
        >
        <button
          type="button"
          class="user-avatar-button"
          :disabled="!activeUser || uploadingAvatar"
          :title="activeUser ? 'Загрузить или изменить аватар' : 'Пользователь не выбран'"
          @click="triggerAvatarPicker"
        >
          <img
            v-if="activeUser?.avatar_url && !isAvatarBroken(activeUser.avatar_url)"
            :src="activeUser.avatar_url"
            :alt="activeUser?.full_name || 'Аватар пользователя'"
            class="user-avatar-button__image"
            @error="markAvatarBroken(activeUser.avatar_url)"
          >
          <span v-else class="user-avatar-button__fallback">{{ activeUserInitial }}</span>
          <span class="user-avatar-button__overlay">
            <i class="fas" :class="uploadingAvatar ? 'fa-spinner fa-spin' : 'fa-upload'"></i>
          </span>
          <span v-if="activeUser" class="user-avatar-button__status"></span>
        </button>
      </div>
    </div>
  </header>
</template>

<script>
import { computed, ref } from 'vue'
import { api } from '../../services/api'
import { useToast } from '../../composables/useToast'
import { useAuthStore } from '../../stores/auth'
import { getStoredPermissions, saveActiveUser } from '../../utils/permissions'

export default {
  name: 'AppHeader',
  props: {
    activeUser: { type: Object, default: null },
    unreadCount: { type: Number, default: 0 },
    currentTimeLabel: { type: String, default: '' },
  },
  emits: ['open-search', 'open-vat', 'open-two-factor', 'open-notifications', 'user-updated'],
  setup(props, { emit }) {
    const authStore = useAuthStore()
    const { success: toastSuccess, error: toastError } = useToast()

    const avatarInput = ref(null)
    const wallpaperInput = ref(null)
    const uploadingAvatar = ref(false)
    const uploadingWallpaper = ref(false)
    const brokenAvatarUrls = ref(new Set())

    const activeUserInitial = computed(() => {
      const source = props.activeUser?.full_name || props.activeUser?.email || '?'
      return String(source).trim().charAt(0).toUpperCase() || '?'
    })

    const isAvatarBroken = (url) => {
      const normalized = String(url || '').trim()
      return normalized ? brokenAvatarUrls.value.has(normalized) : false
    }

    const markAvatarBroken = (url) => {
      const normalized = String(url || '').trim()
      if (!normalized || brokenAvatarUrls.value.has(normalized)) return
      brokenAvatarUrls.value = new Set([...brokenAvatarUrls.value, normalized])
    }

    const persistUpdatedUser = (updatedUser) => {
      authStore.user = updatedUser
      saveActiveUser(updatedUser, getStoredPermissions() || authStore.permissions || {})
      emit('user-updated', updatedUser)
    }

    const triggerAvatarPicker = () => {
      if (!props.activeUser || uploadingAvatar.value) return
      avatarInput.value?.click()
    }

    const triggerWallpaperPicker = () => {
      if (!props.activeUser || uploadingWallpaper.value) return
      wallpaperInput.value?.click()
    }

    const onAvatarPicked = async (event) => {
      const input = event?.target
      const file = input?.files?.[0]
      if (input) input.value = ''
      if (!file || !props.activeUser) return
      const allowedTypes = ['image/png', 'image/jpeg', 'image/webp', 'image/gif']
      if (!allowedTypes.includes(file.type)) {
        toastError('Допустимы только JPG, PNG, WEBP или GIF')
        return
      }
      if (file.size > 5 * 1024 * 1024) {
        toastError('Максимальный размер аватара 5 МБ')
        return
      }

      uploadingAvatar.value = true
      try {
        const form = new FormData()
        form.append('file', file, file.name)
        const updatedUser = await api.users.updateMyAvatar(form)
        if (!updatedUser) throw new Error('Empty avatar response')
        persistUpdatedUser(updatedUser)
        toastSuccess('Аватар обновлен')
      } catch (error) {
        console.error('Error uploading avatar:', error)
        toastError(error.response?.data?.detail || 'Не удалось обновить аватар')
      } finally {
        uploadingAvatar.value = false
      }
    }

    const onWallpaperPicked = async (event) => {
      const input = event?.target
      const file = input?.files?.[0]
      if (input) input.value = ''
      if (!file || !props.activeUser) return
      const allowedTypes = ['image/png', 'image/jpeg', 'image/gif']
      if (!allowedTypes.includes(file.type)) {
        toastError('Допустимы только JPG, PNG или GIF')
        return
      }
      if (file.size > 12 * 1024 * 1024) {
        toastError('Максимальный размер обоев 12 МБ')
        return
      }

      uploadingWallpaper.value = true
      try {
        const form = new FormData()
        form.append('file', file, file.name)
        const updatedUser = await api.users.updateMyWallpaper(form)
        if (!updatedUser) throw new Error('Empty wallpaper response')
        persistUpdatedUser(updatedUser)
        toastSuccess('Обои обновлены')
      } catch (error) {
        console.error('Error uploading wallpaper:', error)
        toastError(error.response?.data?.detail || 'Не удалось обновить обои')
      } finally {
        uploadingWallpaper.value = false
      }
    }

    const clearWallpaper = async () => {
      if (!props.activeUser || uploadingWallpaper.value) return
      uploadingWallpaper.value = true
      try {
        const updatedUser = await api.users.removeMyWallpaper()
        if (!updatedUser) throw new Error('Empty wallpaper response')
        persistUpdatedUser(updatedUser)
        toastSuccess('Возвращены стандартные обои')
      } catch (error) {
        console.error('Error clearing wallpaper:', error)
        toastError(error.response?.data?.detail || 'Не удалось сбросить обои')
      } finally {
        uploadingWallpaper.value = false
      }
    }

    return {
      avatarInput,
      wallpaperInput,
      uploadingAvatar,
      uploadingWallpaper,
      activeUserInitial,
      isAvatarBroken,
      markAvatarBroken,
      triggerAvatarPicker,
      triggerWallpaperPicker,
      onAvatarPicked,
      onWallpaperPicked,
      clearWallpaper,
    }
  },
}
</script>

<style scoped>
/* Перенос исходных стилей из App.vue. Scoped, чтобы сохранить
   приоритет над main.css (которая определяет свой .content-header). */
.content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 48px;
  padding: 0 16px;
  background: rgba(28, 39, 53, 0.32);
  border-bottom: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
  backdrop-filter: blur(1px) saturate(100%);
  -webkit-backdrop-filter: blur(1px) saturate(100%);
}

:root[data-theme="dark"] .content-header {
  background: rgba(15, 23, 42, 0.76);
  border-bottom-color: var(--color-border);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.03);
}

.content-header__search {
  flex: 1 1 420px;
  min-width: 180px;
  max-width: 480px;
  margin-left: auto;
  height: 28px;
  padding: 0 10px;
  border: 1px solid rgba(194, 198, 214, 0.38);
  border-radius: 60px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.04);
  color: var(--color-text-muted);
  display: inline-flex;
  align-items: center;
  gap: 8px;
  text-align: left;
  backdrop-filter: blur(8px);
  transition:
    background var(--dur-fast) ease,
    border-color var(--dur-fast) ease,
    box-shadow var(--dur-fast) ease,
    transform var(--dur-fast) var(--ease-out);
}

.content-header__search:hover {
  background: rgba(255, 255, 255, 0.98);
  border-color: rgba(255, 255, 255, 0.42);
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
}

:root[data-theme="dark"] .content-header__search {
  background: rgba(15, 23, 42, 0.56);
}

:root[data-theme="dark"] .content-header__search:hover {
  background: rgba(15, 23, 42, 0.82);
}

.content-header__search i {
  font-size: 11px;
  color: #6b7280;
}

.content-header__search-label {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  color: #6b7280;
}

.content-header__search-shortcut {
  flex-shrink: 0;
  font-size: 8px;
  font-weight: 700;
  color: #7a8190;
  padding: 0 4px;
  border-radius: 5px;
  background: transparent;
  border: none;
}

.content-header__actions {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  min-width: 0;
  flex-shrink: 0;
}

.user-rating {
  display: none;
  align-items: center;
  gap: 4px;
  height: 22px;
  padding: 0 6px;
  background: linear-gradient(135deg, rgba(255, 247, 214, 0.96), rgba(255, 235, 179, 0.96));
  border: 1px solid rgba(255, 214, 102, 0.55);
  border-radius: 6px;
  font-weight: 600;
  box-shadow: none;
}

.rating-value {
  font-size: 10px;
  color: var(--color-warning);
}

.rating-count {
  font-size: 8px;
  color: var(--color-text-muted);
}

.notification-bell {
  position: relative;
  overflow: visible;
}

.content-header__tools {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 0 2px;
}

.header-utility-btn {
  position: relative;
  width: 44px;
  height: 44px;
  padding: 0;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: rgba(255, 255, 255, 0.98);
  font-size: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.18s ease, color 0.18s ease, transform 0.18s ease;
}

.header-utility-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.96);
}

:root[data-theme="dark"] .header-utility-btn:hover:not(:disabled) {
  background: rgba(15, 23, 42, 0.82);
}

.header-utility-btn.is-active {
  background: rgba(140, 197, 255, 0.18);
  color: rgba(228, 242, 255, 0.98);
}

.header-utility-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.content-header__divider {
  width: 1px;
  height: 14px;
  background: rgba(255, 255, 255, 0.18);
}

.content-header__time {
  min-width: 52px;
  text-align: right;
  font-size: 15px;
  line-height: 1;
  font-weight: 500;
  letter-spacing: 0.03em;
  color: rgba(214, 229, 255, 0.96);
}

.notification-badge {
  position: absolute;
  top: -6px;
  right: -10px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  line-height: 1;
  color: var(--color-text-inverse);
  background: var(--color-danger);
  border: 2px solid var(--color-surface);
  border-radius: 999px;
  pointer-events: none;
}

.user-profile {
  min-width: 0;
  max-width: 260px;
}

.content-header__profile {
  padding: 2px 4px 2px 10px;
  border-radius: 8px;
  background: transparent;
  transition: background var(--dur-fast) ease;
}

.content-header__profile:hover {
  background: rgba(255, 255, 255, 0.08);
}

:root[data-theme="dark"] .content-header__profile {
  background: rgba(15, 23, 42, 0.56);
}

.user-profile__meta {
  min-width: 0;
  text-align: right;
}

.user-profile__name {
  font-weight: 1200;
  font-size: 15px;
  color: rgba(255, 255, 255, 0.96);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-profile__hint {
  font-size: 0px;
  color: rgba(255, 255, 255, 0.48);
  white-space: nowrap;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.user-avatar-input {
  display: none;
}

.user-avatar-button {
  position: relative;
  width: 42px;
  height: 42px;
  padding: 0;
  border: 1px solid rgba(194, 198, 214, 0.55);
  border-radius: 50%;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.user-avatar-button:hover:not(:disabled),
.user-avatar-button:focus-visible {
  transform: translateY(-1px);
  border-color: var(--color-primary-soft-strong);
  box-shadow: var(--shadow-md);
  outline: none;
}

.user-avatar-button:disabled {
  cursor: default;
}

.user-avatar-button__image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-avatar-button__fallback {
  font-size: 1rem;
  font-weight: 700;
}

.user-avatar-button__overlay {
  position: absolute;
  inset: 0;
  background: rgba(10, 22, 41, 0.42);
  color: var(--color-text-inverse);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.18s ease;
}

.user-avatar-button:hover:not(:disabled) .user-avatar-button__overlay,
.user-avatar-button:focus-visible .user-avatar-button__overlay {
  opacity: 1;
}

.user-avatar-button__status {
  position: absolute;
  right: 1px;
  bottom: 1px;
  width: 10px;
  height: 10px;
  border: 2px solid var(--color-surface);
  border-radius: 50%;
  background: var(--color-primary);
}

@media (max-width: 900px) {
  .content-header {
    flex-wrap: wrap;
  }

  .content-header__search {
    width: 100%;
    margin-left: 0;
    order: 2;
  }

  .content-header__actions {
    width: 100%;
    justify-content: space-between;
  }
}

@media (max-width: 640px) {
  .content-header__divider,
  .content-header__time,
  .content-header__search-shortcut,
  .user-rating,
  .user-profile__hint {
    display: none;
  }

  .content-header__actions {
    gap: 8px;
  }
}
</style>
