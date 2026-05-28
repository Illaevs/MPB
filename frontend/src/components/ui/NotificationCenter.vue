<template>
  <teleport to="body">
    <transition name="nc-overlay">
      <div v-if="visible" class="nc-overlay" @click.self="close">
        <transition name="nc-panel">
          <div v-if="visible" class="nc-panel">
            <!-- Header -->
            <div class="nc-header">
              <div class="nc-header__left">
                <div class="nc-header__icon">
                  <i class="fas fa-bell"></i>
                </div>
                <div>
                  <h2 class="nc-header__title">Центр уведомлений</h2>
                  <p class="nc-header__subtitle">
                    {{ unreadCount }} непрочитанных
                  </p>
                </div>
              </div>
              <div class="nc-header__right">
                <button
                  class="nc-btn nc-btn--secondary"
                  :disabled="!unreadCount"
                  @click="markAllRead"
                >
                  <i class="fas fa-check-double"></i>
                  <span>Прочитать все</span>
                </button>
                <button class="nc-btn nc-btn--icon" @click="refresh" :disabled="loading">
                  <i class="fas fa-sync" :class="{ 'fa-spin': loading }"></i>
                </button>
                <button class="nc-btn nc-btn--icon" @click="close">
                  <i class="fas fa-times"></i>
                </button>
              </div>
            </div>

            <!-- Toolbar: tabs + search -->
            <div class="nc-toolbar">
              <div class="nc-tabs">
                <button
                  v-for="tab in tabs"
                  :key="tab.value"
                  class="nc-tab"
                  :class="{ active: activeTab === tab.value }"
                  @click="activeTab = tab.value"
                >
                  {{ tab.label }}
                  <span v-if="tab.count > 0" class="nc-tab__count">{{ tab.count }}</span>
                </button>
              </div>
              <div class="nc-search-wrap">
                <i class="fas fa-search nc-search-icon"></i>
                <input
                  v-model="searchQuery"
                  class="nc-search"
                  placeholder="Поиск..."
                  @input="onSearch"
                >
              </div>
            </div>

            <div class="nc-telegram" :class="{ 'nc-telegram--loading': telegramLoading }">
              <div class="nc-telegram__content">
                <div class="nc-telegram__title-row">
                  <div class="nc-telegram__title">Telegram</div>
                  <span class="nc-telegram__badge" :class="telegramQuickState.className">
                    {{ telegramQuickState.label }}
                  </span>
                </div>
                <div class="nc-telegram__text">
                  {{ telegramQuickState.description }}
                </div>
              </div>
              <div class="nc-telegram__actions">
                <button class="nc-btn nc-btn--secondary" @click="loadTelegramStatus" :disabled="telegramLoading">
                  <i class="fas" :class="telegramLoading ? 'fa-spinner fa-spin' : 'fa-sync'"></i>
                  <span>Проверить</span>
                </button>
                <button class="nc-btn nc-btn--primary" @click="openNotificationSettings">
                  <i class="fab fa-telegram-plane"></i>
                  <span>Настроить</span>
                </button>
              </div>
            </div>

            <!-- Feed -->
            <div class="nc-feed" ref="feedEl">
              <div v-if="loading && !notifications.length" class="nc-feed__loading">
                <div v-for="i in 5" :key="i" class="nc-skeleton"></div>
              </div>

              <div v-else-if="!filteredNotifications.length" class="nc-empty">
                <div class="nc-empty__icon">
                  <i class="fas fa-bell-slash"></i>
                </div>
                <div class="nc-empty__text">Нет уведомлений</div>
                <div class="nc-empty__hint">по заданным фильтрам</div>
              </div>

              <transition-group v-else name="nc-card" tag="div" class="nc-card-list">
                <div
                  v-for="item in filteredNotifications"
                  :key="item.id"
                  class="nc-card"
                  :class="{
                    'nc-card--unread': !item.is_read,
                    'nc-card--read': item.is_read
                  }"
                  @click="openNotification(item)"
                >
                  <!-- Type icon -->
                  <div class="nc-card__icon-wrap" :class="iconBg(item.type)">
                    <i :class="typeIcon(item.type)"></i>
                    <span v-if="!item.is_read" class="nc-card__dot"></span>
                  </div>

                  <!-- Content -->
                  <div class="nc-card__body">
                    <div class="nc-card__title" :class="{ 'nc-card__title--bold': !item.is_read }">
                      {{ item.title }}
                    </div>
                    <div v-if="item.message" class="nc-card__message">{{ item.message }}</div>
                    <div class="nc-card__date">{{ formatDateTime(item.created_at) }}</div>
                  </div>

                  <!-- Hover actions -->
                  <div class="nc-card__actions" @click.stop>
                    <button
                      v-if="!item.is_read"
                      class="nc-btn nc-btn--icon nc-btn--sm"
                      title="Прочитать"
                      @click="markRead(item)"
                    >
                      <i class="fas fa-check"></i>
                    </button>
                    <button
                      v-if="item.action_url"
                      class="nc-btn nc-btn--icon nc-btn--sm"
                      title="Открыть"
                      @click="openNotification(item)"
                    >
                      <i class="fas fa-external-link-alt"></i>
                    </button>
                    <button
                      class="nc-btn nc-btn--icon nc-btn--sm nc-btn--danger"
                      title="Удалить"
                      @click="deleteNotification(item)"
                    >
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                </div>
              </transition-group>

              <!-- Load more -->
              <div v-if="hasMore && !loading" class="nc-loadmore">
                <button class="nc-btn nc-btn--secondary" :disabled="loadingMore" @click="loadMore">
                  <i v-if="loadingMore" class="fas fa-spinner fa-spin"></i>
                  Показать ещё
                </button>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </transition>
  </teleport>
</template>

<script>
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as notificationsApi from '../../services/api/notifications'
import { useNotificationsStore } from '@/stores/notifications'

export default {
  name: 'NotificationCenter',
  props: {
    modelValue: { type: Boolean, default: false }
  },
  emits: ['update:modelValue', 'unread-count-changed'],
  setup(props, { emit }) {
    const router = useRouter()
    const store = useNotificationsStore()
    const visible = computed({
      get: () => props.modelValue,
      set: (v) => emit('update:modelValue', v)
    })
    // Дополнительные страницы для "Показать ещё" — основной список приходит из store.
    const extraItems = ref([])
    const loadingMore = ref(false)
    const hasMore = ref(false)
    const activeTab = ref('all')
    const searchQuery = ref('')
    const pageSize = 30
    const skip = ref(0)
    const feedEl = ref(null)
    const telegramLoading = ref(false)
    const telegramStatus = ref({
      bot_configured: false,
      is_connected: false,
      is_enabled: false,
      is_verified: false
    })

    // Объединённый список: store.items + догруженные страницы (по id, без дублей).
    const notifications = computed(() => {
      const base = store.items || []
      if (!extraItems.value.length) return base
      const seen = new Set(base.map((n) => String(n.id)))
      const tail = extraItems.value.filter((n) => !seen.has(String(n.id)))
      return [...base, ...tail]
    })
    const loading = computed(() => store.loading)
    const unreadCount = computed(() => store.unreadCount)

    const tabs = computed(() => [
      { label: 'Все', value: 'all', count: notifications.value.length },
      { label: 'Непрочитанные', value: 'unread', count: unreadCount.value },
      { label: 'Сообщения', value: 'message', count: notifications.value.filter(n => n.type === 'message' || n.type === 'info').length }
    ])

    const filteredNotifications = computed(() => {
      let list = notifications.value
      if (activeTab.value === 'unread') {
        list = list.filter(n => !n.is_read)
      } else if (activeTab.value === 'message') {
        list = list.filter(n => n.type === 'message' || n.type === 'info')
      }
      if (searchQuery.value.trim()) {
        const q = searchQuery.value.toLowerCase().trim()
        list = list.filter(n =>
          (n.title || '').toLowerCase().includes(q) ||
          (n.message || '').toLowerCase().includes(q)
        )
      }
      return list
    })

    const telegramQuickState = computed(() => {
      if (telegramLoading.value) {
        return {
          label: 'Проверка',
          className: 'nc-telegram__badge--muted',
          description: 'Загружаю статус Telegram-канала.'
        }
      }
      if (!telegramStatus.value.bot_configured) {
        return {
          label: 'Не настроен',
          className: 'nc-telegram__badge--muted',
          description: 'Бот на сервере пока не настроен. Нажми «Настроить», чтобы открыть полные параметры.'
        }
      }
      if (telegramStatus.value.is_connected) {
        return {
          label: 'Подключен',
          className: 'nc-telegram__badge--success',
          description: 'Канал Telegram подключен и готов к отправке уведомлений.'
        }
      }
      return {
        label: 'Не подключен',
        className: 'nc-telegram__badge--warning',
        description: 'Бот настроен, но текущий пользователь еще не привязал Telegram.'
      }
    })

    const close = () => { visible.value = false }

    const typeIcon = (type) => {
      const map = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-triangle',
        warning: 'fas fa-exclamation-circle',
        info: 'fas fa-info-circle',
        message: 'fas fa-comment-dots',
        system: 'fas fa-cog'
      }
      return map[type] || 'fas fa-info-circle'
    }

    const iconBg = (type) => {
      const map = {
        success: 'nc-icon--success',
        error: 'nc-icon--error',
        warning: 'nc-icon--warning',
        info: 'nc-icon--info',
        message: 'nc-icon--message',
        system: 'nc-icon--system'
      }
      return map[type] || 'nc-icon--info'
    }

    const formatDateTime = (value) => {
      if (!value) return ''
      const d = new Date(value)
      const now = new Date()
      const diff = now - d
      if (diff < 60000) return 'только что'
      if (diff < 3600000) return `${Math.floor(diff / 60000)} мин. назад`
      if (diff < 86400000) return `${Math.floor(diff / 3600000)} ч. назад`
      return d.toLocaleString('ru-RU', {
        day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
      })
    }

    const loadNotifications = async (append) => {
      if (append) {
        loadingMore.value = true
        try {
          const result = await notificationsApi.list({ skip: skip.value, limit: pageSize })
          const items = result || []
          const seen = new Set((store.items || []).map((n) => String(n.id)))
          extraItems.value = [
            ...extraItems.value,
            ...items.filter((n) => !seen.has(String(n.id)))
          ]
          hasMore.value = items.length === pageSize
          if (items.length > 0) skip.value += items.length
        } catch (error) {
          console.error('Error loading notifications:', error)
        } finally {
          loadingMore.value = false
        }
      } else {
        skip.value = 0
        extraItems.value = []
        try {
          await store.refresh()
          hasMore.value = (store.items || []).length >= pageSize
          skip.value = (store.items || []).length
        } catch (error) {
          console.error('Error loading notifications:', error)
        }
      }
    }

    const loadTelegramStatus = async () => {
      telegramLoading.value = true
      try {
        const result = await notificationsApi.getTelegramStatus()
        telegramStatus.value = {
          ...telegramStatus.value,
          ...(result || {})
        }
      } catch (error) {
        console.error('Error loading telegram quick status:', error)
      } finally {
        telegramLoading.value = false
      }
    }

    const refresh = () => loadNotifications(false)
    const loadMore = () => loadNotifications(true)

    const markRead = async (item) => {
      if (!item || item.is_read) return
      try {
        await store.markRead(item.id)
        // Sync аналогично — на догруженных страницах (extraItems) тоже отмечаем.
        extraItems.value = extraItems.value.map((n) =>
          String(n.id) === String(item.id) ? { ...n, is_read: true } : n
        )
      } catch (error) {
        console.error('Error marking notification read:', error)
      }
    }

    const markAllRead = async () => {
      if (!notifications.value.length) return
      try {
        await store.markAllRead()
        extraItems.value = extraItems.value.map((n) => ({ ...n, is_read: true }))
      } catch (error) {
        console.error('Error marking all read:', error)
      }
    }

    const deleteNotification = async (item) => {
      try {
        await notificationsApi.remove(item.id)
        extraItems.value = extraItems.value.filter((n) => n.id !== item.id)
        // Перечитаем store, чтобы основной список и unreadCount синхронизировались.
        await store.refresh({ silent: true })
      } catch (error) {
        console.error('Error deleting notification:', error)
      }
    }

    const openNotification = async (item) => {
      await markRead(item)
      if (item && item.action_url) {
        close()
        await nextTick()
        router.push(item.action_url)
      }
    }

    const openNotificationSettings = async () => {
      close()
      await nextTick()
      router.push('/notifications')
    }

    const onSearch = () => {} // reactive via searchQuery

    // Lock body scroll
    watch(visible, (v) => {
      if (v) {
        document.body.style.overflow = 'hidden'
        // Если в store ещё пусто — догрузить. Поллингом управляет App.vue.
        if (!(store.items && store.items.length)) {
          store.fetchList()
        }
        hasMore.value = (store.items || []).length >= pageSize
        skip.value = (store.items || []).length
        extraItems.value = []
        loadTelegramStatus()
      } else {
        document.body.style.overflow = ''
      }
    })

    // ESC to close
    const handleKeydown = (e) => {
      if (e.key === 'Escape' && visible.value) close()
    }
    if (typeof window !== 'undefined') {
      window.addEventListener('keydown', handleKeydown)
    }

    return {
      visible,
      notifications,
      filteredNotifications,
      loading,
      loadingMore,
      hasMore,
      telegramLoading,
      telegramQuickState,
      activeTab,
      searchQuery,
      unreadCount,
      tabs,
      feedEl,
      close,
      typeIcon,
      iconBg,
      formatDateTime,
      refresh,
      loadTelegramStatus,
      loadMore,
      markRead,
      markAllRead,
      deleteNotification,
      openNotification,
      openNotificationSettings,
      onSearch
    }
  }
}
</script>

<style scoped>
/* ===== OVERLAY ===== */
.nc-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.nc-overlay-enter-active { animation: nc-fade-in 0.2s ease; }
.nc-overlay-leave-active { animation: nc-fade-in 0.2s ease reverse; }
@keyframes nc-fade-in { from { opacity: 0; } to { opacity: 1; } }

/* ===== PANEL ===== */
.nc-panel {
  width: min(960px, calc(100vw - 48px));
  height: min(85vh, 760px);
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.90);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow:
    0 40px 80px -12px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  overflow: hidden;
}

:root[data-theme="dark"] .nc-panel {
  background: rgba(30, 30, 32, 0.88);
  border-color: rgba(255, 255, 255, 0.1);
}

.nc-panel-enter-active { animation: nc-pop-in 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
.nc-panel-leave-active { animation: nc-pop-in 0.2s ease reverse; }
@keyframes nc-pop-in {
  from { opacity: 0; transform: scale(0.95) translateY(16px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

/* ===== HEADER ===== */
.nc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
}

:root[data-theme="dark"] .nc-header {
  border-bottom-color: rgba(255, 255, 255, 0.08);
}

.nc-header__left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.nc-header__icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-active));
  color: var(--color-text-inverse);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.15rem;
}

.nc-header__title {
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--md-sys-color-on-surface);
  margin: 0;
  line-height: 1.2;
}

.nc-header__subtitle {
  font-size: 0.82rem;
  color: var(--md-sys-color-on-surface-variant);
  margin: 2px 0 0;
}

.nc-header__right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ===== BUTTONS ===== */
.nc-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: none;
  cursor: pointer;
  font-family: inherit;
  font-weight: 500;
  transition: all 0.15s ease;
}

.nc-btn--secondary {
  padding: 8px 14px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.05);
  color: var(--md-sys-color-on-surface);
  font-size: 0.82rem;
}

.nc-btn--secondary:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.09);
}

:root[data-theme="dark"] .nc-btn--secondary {
  background: rgba(255, 255, 255, 0.1);
  color: var(--color-text-inverse);
}

.nc-btn--primary {
  padding: 8px 14px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-active));
  color: var(--color-text-inverse);
  font-size: 0.82rem;
}

.nc-btn--primary:hover:not(:disabled) {
  filter: brightness(1.05);
}

.nc-btn--icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  padding: 0;
}

.nc-btn--icon:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.06);
}

.nc-btn--sm {
  width: 30px;
  height: 30px;
  font-size: 0.78rem;
  border-radius: 8px;
}

.nc-btn--danger:hover {
  background: var(--color-danger-soft) !important;
  color: var(--color-danger) !important;
}

.nc-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

/* ===== TOOLBAR ===== */
.nc-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  flex-shrink: 0;
}

:root[data-theme="dark"] .nc-toolbar {
  border-bottom-color: rgba(255, 255, 255, 0.06);
}

.nc-tabs {
  display: flex;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 10px;
  padding: 3px;
}

:root[data-theme="dark"] .nc-tabs {
  background: rgba(255, 255, 255, 0.08);
}

.nc-tab {
  padding: 6px 14px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: inherit;
}

.nc-tab.active {
  background: var(--color-surface);
  color: var(--md-sys-color-on-surface);
  box-shadow: var(--shadow-sm);
}

:root[data-theme="dark"] .nc-tab.active {
  background: rgba(255, 255, 255, 0.15);
  color: var(--color-text-inverse);
}

.nc-tab__count {
  font-size: 0.7rem;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  padding: 1px 6px;
  border-radius: 6px;
  font-weight: 600;
}

.nc-search-wrap {
  position: relative;
  min-width: 200px;
}

.nc-search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.8rem;
  opacity: 0.5;
}

.nc-search {
  width: 100%;
  padding: 8px 12px 8px 34px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.03);
  font-size: 0.85rem;
  color: var(--md-sys-color-on-surface);
  font-family: inherit;
  outline: none;
  transition: border-color 0.15s, background 0.15s;
}

.nc-search:focus {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

:root[data-theme="dark"] .nc-search {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.1);
  color: var(--color-text-inverse);
}

.nc-telegram {
  margin: 14px 24px 0;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid var(--color-primary-soft-strong);
  background: var(--color-primary-soft);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-shrink: 0;
}

:root[data-theme="dark"] .nc-telegram {
  border-color: var(--color-primary-soft-strong);
  background: var(--color-primary-soft);
}

.nc-telegram--loading {
  opacity: 0.8;
}

.nc-telegram__content {
  min-width: 0;
}

.nc-telegram__title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.nc-telegram__title {
  font-size: 0.96rem;
  font-weight: 700;
  color: var(--md-sys-color-on-surface);
}

.nc-telegram__text {
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.85rem;
  line-height: 1.35;
}

.nc-telegram__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.nc-telegram__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 0.75rem;
  font-weight: 700;
  white-space: nowrap;
}

.nc-telegram__badge--success {
  background: var(--color-success-soft);
  color: var(--color-success-hover);
}

.nc-telegram__badge--warning {
  background: var(--color-warning-soft);
  color: var(--color-warning-hover);
}

.nc-telegram__badge--muted {
  background: var(--color-surface-3);
  color: var(--color-text-muted);
}

/* ===== FEED ===== */
.nc-feed {
  flex: 1;
  overflow-y: auto;
  padding: 12px 24px 24px;
  scroll-behavior: smooth;
}

.nc-feed::-webkit-scrollbar {
  width: 6px;
}

.nc-feed::-webkit-scrollbar-track {
  background: transparent;
}

.nc-feed::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.12);
  border-radius: 3px;
}

.nc-card-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* ===== CARD ===== */
.nc-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.nc-card--unread {
  background: var(--color-surface);
  border-color: var(--color-primary-soft-strong);
  box-shadow: var(--shadow-sm);
}

:root[data-theme="dark"] .nc-card--unread {
  background: var(--color-surface-2);
  border-color: var(--color-primary-soft-strong);
}

.nc-card--read {
  background: var(--color-surface-overlay);
}

:root[data-theme="dark"] .nc-card--read {
  background: var(--overlay-paper-4);
}

.nc-card:hover {
  background: var(--color-primary-soft);
  border-color: var(--color-primary-soft-strong);
}

:root[data-theme="dark"] .nc-card:hover {
  background: var(--overlay-paper-8);
}

/* Icon */
.nc-card__icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
  position: relative;
}

.nc-icon--info { background: var(--color-primary-soft); color: var(--color-primary); }
.nc-icon--success { background: var(--color-success-soft); color: var(--color-success); }
.nc-icon--error { background: var(--color-danger-soft); color: var(--color-danger); }
.nc-icon--warning { background: var(--color-warning-soft); color: var(--color-warning); }
.nc-icon--message { background: var(--color-primary-soft); color: var(--color-primary-active); }
.nc-icon--system { background: var(--color-surface-3); color: var(--color-text-muted); }

.nc-card__dot {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-primary);
  border: 2px solid var(--color-surface);
}

:root[data-theme="dark"] .nc-card__dot {
  border-color: var(--color-surface);
}

/* Body */
.nc-card__body {
  flex: 1;
  min-width: 0;
}

.nc-card__title {
  font-size: 0.9rem;
  color: var(--md-sys-color-on-surface);
  line-height: 1.3;
  margin-bottom: 2px;
}

.nc-card__title--bold {
  font-weight: 600;
}

.nc-card__message {
  font-size: 0.82rem;
  color: var(--md-sys-color-on-surface-variant);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.nc-card__date {
  font-size: 0.72rem;
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.7;
  margin-top: 4px;
}

/* Hover actions */
.nc-card__actions {
  display: flex;
  align-items: center;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s ease;
  flex-shrink: 0;
}

.nc-card:hover .nc-card__actions {
  opacity: 1;
}

/* Card animations */
.nc-card-enter-active {
  animation: nc-card-in 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.nc-card-leave-active {
  animation: nc-card-out 0.2s ease;
}

.nc-card-move {
  transition: transform 0.3s ease;
}

@keyframes nc-card-in {
  from { opacity: 0; transform: translateY(-8px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes nc-card-out {
  from { opacity: 1; transform: scale(1); }
  to { opacity: 0; transform: scale(0.95) translateX(20px); }
}

/* ===== EMPTY STATE ===== */
.nc-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  text-align: center;
}

.nc-empty__icon {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  background: rgba(0, 0, 0, 0.04);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.6rem;
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.4;
  margin-bottom: 16px;
}

.nc-empty__text {
  font-size: 1rem;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
  margin-bottom: 4px;
}

.nc-empty__hint {
  font-size: 0.85rem;
  color: var(--md-sys-color-on-surface-variant);
}

/* ===== SKELETONS ===== */
.nc-feed__loading {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.nc-skeleton {
  height: 68px;
  border-radius: 16px;
  background: linear-gradient(90deg, rgba(0,0,0,0.04) 25%, rgba(0,0,0,0.08) 50%, rgba(0,0,0,0.04) 75%);
  background-size: 200% 100%;
  animation: nc-shimmer 1.5s ease infinite;
}

@keyframes nc-shimmer {
  from { background-position: 200% 0; }
  to { background-position: -200% 0; }
}

/* ===== LOAD MORE ===== */
.nc-loadmore {
  display: flex;
  justify-content: center;
  padding: 16px 0 8px;
}

/* ===== MOBILE ===== */
@media (max-width: 768px) {
  .nc-panel {
    width: 100vw;
    height: 100vh;
    border-radius: 0;
  }

  .nc-toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
    padding: 12px 16px;
  }

  .nc-telegram {
    margin: 12px 16px 0;
    flex-direction: column;
    align-items: stretch;
  }

  .nc-telegram__actions {
    justify-content: flex-end;
    flex-wrap: wrap;
  }

  .nc-search-wrap {
    min-width: 0;
  }

  .nc-header {
    padding: 16px;
  }

  .nc-header__right {
    width: 100%;
    flex-wrap: wrap;
    justify-content: flex-start;
  }

  .nc-header__right span {
    display: none;
  }

  .nc-header__right .nc-btn--secondary,
  .nc-header__right .nc-btn--icon {
    min-width: 44px;
    min-height: 44px;
  }

  .nc-header__right .nc-btn--secondary {
    flex: 1 1 100%;
    justify-content: center;
  }

  .nc-header__right .nc-btn--icon {
    flex: 0 0 44px;
  }

  .nc-btn--icon,
  .nc-btn--sm {
    width: 44px;
    height: 44px;
    min-width: 44px;
    min-height: 44px;
  }

  .nc-tabs {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .nc-tab {
    min-height: 44px;
  }

  .nc-feed {
    padding: 12px 12px 14px;
  }

  .nc-card__actions {
    opacity: 1;
    pointer-events: auto;
  }

  .nc-card {
    padding-right: 10px;
  }
}

@media (max-width: 480px) {
  .nc-header__right {
    gap: 6px;
  }

  .nc-header__right .nc-btn--secondary {
    font-size: 0.8rem;
  }
}

@media (max-width: 480px) {
  .nc-header__left {
    gap: 10px;
  }

  .nc-header__title {
    font-size: 1.05rem;
  }
}
</style>
