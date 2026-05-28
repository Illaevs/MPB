<template>
  <div class="notifications-view">
    <div class="notifications-toolbar">
      <h2 class="notifications-toolbar__title">Уведомления</h2>
      <div class="notifications-toolbar__actions">
        <UiIconButton icon="fas fa-sync" label="Обновить" size="sm" @click="loadNotifications(false)" />
        <UiButton
          variant="secondary"
          size="sm"
          :disabled="!notifications.length"
          @click="markAllRead"
        >
          Прочитать все
        </UiButton>
      </div>
    </div>

    <!-- Telegram-канал доставки временно отключён в UI (бот будет подключён позже) -->
    <UiCard v-if="false" class="notifications-settings-card">
      <template #header>
        <div class="notifications-settings-card__header">
          <div>
            <div class="notifications-settings-card__title">Telegram</div>
            <div class="notifications-settings-card__subtitle">High-signal уведомления по задачам и документам</div>
          </div>
          <span class="notifications-status-badge" :class="telegramState.className">
            {{ telegramState.label }}
          </span>
        </div>
      </template>

      <div v-if="settingsLoading" class="notifications-settings-card__body text-muted">
        Загрузка настроек...
      </div>

      <div v-else class="notifications-settings-card__body">
        <div class="notifications-settings-meta">
          <div class="notifications-settings-meta__item">
            <span class="notifications-settings-meta__label">Бот</span>
            <span class="notifications-settings-meta__value">
              {{ telegramStatus.bot_username ? `@${telegramStatus.bot_username}` : 'не настроен' }}
            </span>
          </div>
          <div class="notifications-settings-meta__item">
            <span class="notifications-settings-meta__label">Аккаунт</span>
            <span class="notifications-settings-meta__value">
              {{ telegramStatus.telegram_username || telegramStatus.chat_id_masked || 'не подключен' }}
            </span>
          </div>
          <div v-if="telegramStatus.linked_at" class="notifications-settings-meta__item">
            <span class="notifications-settings-meta__label">Подключен</span>
            <span class="notifications-settings-meta__value">{{ formatDateTime(telegramStatus.linked_at) }}</span>
          </div>
        </div>

        <label class="notifications-switch">
          <input
            type="checkbox"
            :checked="notificationPrefs.deliver_telegram"
            :disabled="!canToggleTelegram || telegramBusy"
            @change="updateTelegramDelivery($event.target.checked)"
          >
          <span>Отправлять уведомления в Telegram</span>
        </label>

        <div class="notifications-settings-actions">
          <UiButton
            variant="primary"
            size="sm"
            :disabled="telegramBusy || !telegramStatus.bot_configured"
            @click="createTelegramLink"
          >
            {{ telegramStatus.is_connected ? 'Переподключить' : 'Подключить Telegram' }}
          </UiButton>
          <UiButton
            variant="secondary"
            size="sm"
            :disabled="telegramBusy || !telegramStatus.bot_configured"
            @click="loadChannelSettings"
          >
            Проверить статус
          </UiButton>
          <UiButton
            v-if="telegramStatus.is_connected"
            variant="danger"
            size="sm"
            :disabled="telegramBusy"
            @click="disconnectTelegram"
          >
            Отключить
          </UiButton>
        </div>

        <div v-if="telegramLinkUrl" class="notifications-telegram-link">
          <div class="notifications-telegram-link__title">Ссылка привязки готова</div>
          <div class="notifications-telegram-link__hint">
            Открой бота, нажми Start и затем проверь статус в системе.
          </div>
          <div class="notifications-telegram-link__actions">
            <UiButton
              tag="a"
              variant="outline"
              size="sm"
              :href="telegramLinkUrl"
              target="_blank"
              rel="noopener noreferrer"
            >
              Открыть бота
            </UiButton>
            <UiButton variant="secondary" size="sm" @click="copyTelegramLink">
              Скопировать ссылку
            </UiButton>
            <span v-if="telegramLinkExpiresAt" class="notifications-telegram-link__expires">
              До {{ formatDateTime(telegramLinkExpiresAt) }}
            </span>
          </div>
        </div>

        <div
          v-if="telegramNotice"
          class="notifications-inline-notice"
          :class="`notifications-inline-notice--${telegramNoticeType}`"
        >
          {{ telegramNotice }}
        </div>
      </div>
    </UiCard>

    <UiCard class="notifications-feed-card" padding="none" flush-body>
      <template #header>
        <div class="notifications-filters">
          <div class="notifications-filters__row">
            <div class="notifications-filters__search">
              <UiInput v-model="filters.search" icon-left="fas fa-search" placeholder="Поиск по тексту" />
            </div>
            <UiSelect v-model="filters.unread" :options="unreadOptions" />
            <UiSelect v-model="filters.type" :options="typeOptions" />
            <UiSelect v-model="filters.priority" :options="priorityOptions" />
            <div class="notifications-filters__dates">
              <UiInput v-model="filters.dateFrom" type="date" />
              <UiInput v-model="filters.dateTo" type="date" />
            </div>
          </div>
          <div class="notifications-filters__actions">
            <UiButton variant="primary" size="sm" @click="applyFilters">Применить</UiButton>
            <UiButton variant="secondary" size="sm" @click="resetFilters">Сбросить</UiButton>
          </div>
        </div>
      </template>

      <div v-if="loading" class="notifications-loading">
        <SkeletonLoader height="60px" v-for="i in 6" :key="`notif-skel-${i}`" />
      </div>

      <UiEmptyState
        v-else-if="!notifications.length"
        class="notifications-empty"
        icon="fas fa-bell-slash"
        title="Уведомлений пока нет"
        description="Новые события будут появляться здесь автоматически"
      />

      <div v-else class="notifications-table-wrap">
        <table class="notifications-table sticky-header">
          <thead>
            <tr>
              <th style="width: 4%;"></th>
              <th style="width: 10%;">Тип</th>
              <th style="width: 28%;">Заголовок</th>
              <th style="width: 35%;">Сообщение</th>
              <th style="width: 13%;">Дата</th>
              <th style="width: 10%;" class="text-right">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in notifications"
              :key="item.id"
              :class="{ 'notification-unread': !item.is_read }"
              @click="openNotification(item)"
            >
              <td>
                <span class="status-dot" :class="item.is_read ? 'status-read' : 'status-unread'"></span>
              </td>
              <td>
                <UiBadge size="sm" :class="typeBadge(item.type)">
                  {{ typeLabel(item.type) }}
                </UiBadge>
              </td>
              <td class="fw-600 text-truncate notifications-table__title">
                {{ item.title }}
              </td>
              <td class="text-muted text-truncate notifications-table__message">
                {{ item.message || '—' }}
              </td>
              <td>{{ formatDateTime(item.created_at) }}</td>
              <td class="text-right" @click.stop>
                <div class="notifications-row-actions">
                  <UiButton
                    v-if="!item.is_read"
                    variant="secondary"
                    size="xs"
                    @click="markRead(item)"
                  >
                    Прочитать
                  </UiButton>
                  <UiButton variant="ghost" size="xs" @click="openNotification(item)">
                    Открыть
                  </UiButton>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <template v-if="hasMore && !loading" #footer>
        <div class="notifications-more">
          <UiButton variant="outline" size="sm" :loading="loadingMore" @click="loadMore">
            Показать еще
          </UiButton>
        </div>
      </template>
    </UiCard>
  </div>
</template>

<script>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as notificationsApi from '../services/api/notifications'
import SkeletonLoader from '../components/ui/SkeletonLoader.vue'
import { UiBadge, UiButton, UiCard, UiEmptyState, UiIconButton, UiInput, UiSelect } from '../components/ui'
import { formatMskDateTime } from '../composables/useServerClock'

export default {
  name: 'Notifications',
  components: { SkeletonLoader, UiBadge, UiButton, UiCard, UiEmptyState, UiIconButton, UiInput, UiSelect },
  setup() {
    const router = useRouter()
    const notifications = ref([])
    const loading = ref(false)
    const loadingMore = ref(false)
    const hasMore = ref(false)
    const pageSize = 50
    const skip = ref(0)
    const settingsLoading = ref(false)
    const telegramBusy = ref(false)
    const telegramNotice = ref('')
    const telegramNoticeType = ref('info')
    const telegramLinkUrl = ref('')
    const telegramLinkExpiresAt = ref('')
    const notificationPrefs = ref({
      deliver_in_app: true,
      deliver_telegram: false
    })
    const telegramStatus = ref({
      bot_configured: false,
      bot_username: '',
      is_connected: false,
      is_enabled: false,
      is_verified: false,
      telegram_username: '',
      chat_id_masked: '',
      linked_at: null,
      deliver_telegram: false
    })
    let telegramStatusPollTimer = null

    const filters = ref({
      unread: 'all',
      type: '',
      priority: '',
      search: '',
      dateFrom: '',
      dateTo: ''
    })

    const unreadOptions = [
      { value: 'all', label: 'Все' },
      { value: 'unread', label: 'Непрочитанные' },
      { value: 'read', label: 'Прочитанные' }
    ]
    const typeOptions = [
      { value: '', label: 'Все типы' },
      { value: 'info', label: 'Инфо' },
      { value: 'success', label: 'Успех' },
      { value: 'warning', label: 'Предупр.' },
      { value: 'error', label: 'Ошибка' }
    ]
    const priorityOptions = [
      { value: '', label: 'Все приоритеты' },
      { value: 'info', label: 'Инфо' },
      { value: 'success', label: 'Успех' },
      { value: 'warning', label: 'Предупр.' },
      { value: 'error', label: 'Ошибка' }
    ]

    const typeLabel = (value) => {
      const map = {
        success: 'Успех',
        error: 'Ошибка',
        warning: 'Предупр.',
        info: 'Инфо'
      }
      return map[value] || 'Инфо'
    }

    const typeBadge = (value) => ({
      success: 'badge-success-subtle',
      error: 'badge-danger',
      warning: 'badge-warning',
      info: 'badge-info-subtle'
    })[value] || 'badge-info-subtle'

    const telegramState = computed(() => {
      if (!telegramStatus.value.bot_configured) {
        return { label: 'Бот не настроен', className: 'notifications-status-badge--muted' }
      }
      if (telegramStatus.value.is_connected) {
        return { label: 'Подключен', className: 'notifications-status-badge--success' }
      }
      if (telegramLinkUrl.value) {
        return { label: 'Ожидает подтверждения', className: 'notifications-status-badge--warning' }
      }
      return { label: 'Не подключен', className: 'notifications-status-badge--muted' }
    })

    const canToggleTelegram = computed(() => {
      return telegramStatus.value.bot_configured && telegramStatus.value.is_connected
    })

    const formatDateTime = (value) => {
      // Серверное время: ISO без TZ → трактуем как Europe/Moscow
      // (бэкенд в MSK сохраняет datetime.now() без часового пояса).
      // Гарантирует, что юзеры с любой локальной TZ видят одинаковое
      // «серверное» время уведомлений.
      if (!value) return '-'
      return formatMskDateTime(value) || '-'
    }

    const buildParams = () => {
      const params = {
        skip: skip.value,
        limit: pageSize
      }
      if (filters.value.unread === 'unread') {
        params.unread = true
      }
      if (filters.value.unread === 'read') {
        params.unread = false
      }
      if (filters.value.type) {
        params.type = filters.value.type
      }
      if (filters.value.priority) {
        params.priority = filters.value.priority
      }
      if (filters.value.search) {
        params.search = filters.value.search
      }
      if (filters.value.dateFrom) {
        params.date_from = new Date(`${filters.value.dateFrom}T00:00:00`).toISOString()
      }
      if (filters.value.dateTo) {
        params.date_to = new Date(`${filters.value.dateTo}T23:59:59`).toISOString()
      }
      return params
    }

    const setTelegramNotice = (message, type = 'info') => {
      telegramNotice.value = message || ''
      telegramNoticeType.value = type || 'info'
    }

    const stopTelegramStatusPolling = () => {
      if (telegramStatusPollTimer) {
        clearInterval(telegramStatusPollTimer)
        telegramStatusPollTimer = null
      }
    }

    const startTelegramStatusPolling = () => {
      stopTelegramStatusPolling()
      if (!telegramLinkUrl.value || telegramStatus.value.is_connected) return
      telegramStatusPollTimer = setInterval(async () => {
        await loadTelegramStatus({ silent: true })
        if (telegramStatus.value.is_connected) {
          stopTelegramStatusPolling()
          telegramLinkUrl.value = ''
          telegramLinkExpiresAt.value = ''
          setTelegramNotice('Telegram подключен. Канал доставки активен.', 'success')
        }
      }, 5000)
    }

    const loadNotificationPreferences = async () => {
      const result = await notificationsApi.getPreferences()
      notificationPrefs.value = {
        ...notificationPrefs.value,
        ...(result || {})
      }
    }

    const loadTelegramStatus = async ({ silent = false } = {}) => {
      try {
        const result = await notificationsApi.getTelegramStatus()
        telegramStatus.value = {
          ...telegramStatus.value,
          ...(result || {})
        }
        if (!telegramStatus.value.is_connected && !silent && telegramLinkUrl.value && telegramLinkExpiresAt.value) {
          const expiresAt = new Date(telegramLinkExpiresAt.value).getTime()
          if (Number.isFinite(expiresAt) && expiresAt < Date.now()) {
            telegramLinkUrl.value = ''
            telegramLinkExpiresAt.value = ''
            stopTelegramStatusPolling()
          }
        }
      } catch (error) {
        console.error('Error loading telegram status:', error)
        if (!silent) {
          setTelegramNotice('Не удалось загрузить статус Telegram.', 'danger')
        }
      }
    }

    const loadChannelSettings = async () => {
      settingsLoading.value = true
      try {
        await Promise.all([
          loadNotificationPreferences(),
          loadTelegramStatus()
        ])
      } catch (error) {
        console.error('Error loading notification settings:', error)
        setTelegramNotice('Не удалось загрузить настройки уведомлений.', 'danger')
      } finally {
        settingsLoading.value = false
      }
    }

    const updateTelegramDelivery = async (enabled) => {
      if (enabled && !canToggleTelegram.value) {
        setTelegramNotice('Сначала подключи Telegram через бота.', 'warning')
        return
      }
      telegramBusy.value = true
      try {
        const result = await notificationsApi.updatePreferences({
          deliver_telegram: Boolean(enabled)
        })
        notificationPrefs.value = {
          ...notificationPrefs.value,
          ...(result || {})
        }
        setTelegramNotice(
          enabled ? 'Отправка уведомлений в Telegram включена.' : 'Отправка уведомлений в Telegram выключена.',
          'success'
        )
      } catch (error) {
        console.error('Error updating telegram delivery:', error)
        setTelegramNotice('Не удалось обновить канал доставки.', 'danger')
      } finally {
        telegramBusy.value = false
      }
    }

    const createTelegramLink = async () => {
      telegramBusy.value = true
      try {
        const result = await notificationsApi.createTelegramLink()
        const data = result || {}
        telegramLinkUrl.value = data.link_url || ''
        telegramLinkExpiresAt.value = data.expires_at || ''
        telegramStatus.value = {
          ...telegramStatus.value,
          bot_configured: Boolean(data.bot_configured),
          bot_username: data.bot_username || telegramStatus.value.bot_username || ''
        }
        if (!data.bot_configured) {
          setTelegramNotice('Telegram-бот еще не настроен на сервере.', 'warning')
          return
        }
        if (telegramLinkUrl.value) {
          window.open(telegramLinkUrl.value, '_blank', 'noopener')
          startTelegramStatusPolling()
          setTelegramNotice('Ссылка открыта. Подтверди привязку в Telegram и затем вернись в систему.', 'info')
        } else {
          setTelegramNotice('Не удалось получить ссылку привязки.', 'danger')
        }
      } catch (error) {
        console.error('Error creating telegram link:', error)
        setTelegramNotice('Не удалось создать ссылку привязки Telegram.', 'danger')
      } finally {
        telegramBusy.value = false
      }
    }

    const copyTelegramLink = async () => {
      if (!telegramLinkUrl.value) return
      try {
        await navigator.clipboard.writeText(telegramLinkUrl.value)
        setTelegramNotice('Ссылка привязки скопирована.', 'success')
      } catch (error) {
        console.error('Error copying telegram link:', error)
        setTelegramNotice('Не удалось скопировать ссылку. Открой бота кнопкой выше.', 'warning')
      }
    }

    const disconnectTelegram = async () => {
      telegramBusy.value = true
      try {
        await notificationsApi.disconnectTelegram()
        notificationPrefs.value.deliver_telegram = false
        telegramLinkUrl.value = ''
        telegramLinkExpiresAt.value = ''
        stopTelegramStatusPolling()
        await loadTelegramStatus({ silent: true })
        setTelegramNotice('Telegram отключен.', 'success')
      } catch (error) {
        console.error('Error disconnecting telegram:', error)
        setTelegramNotice('Не удалось отключить Telegram.', 'danger')
      } finally {
        telegramBusy.value = false
      }
    }

    const loadNotifications = async (append) => {
      if (append) {
        loadingMore.value = true
      } else {
        loading.value = true
        skip.value = 0
      }
      try {
        const result = await notificationsApi.list(buildParams())
        const items = result || []
        if (append) {
          notifications.value = [...notifications.value, ...items]
        } else {
          notifications.value = items
        }
        hasMore.value = items.length === pageSize
        if (items.length > 0) {
          skip.value += items.length
        }
      } catch (error) {
        console.error('Error loading notifications:', error)
        if (!append) {
          notifications.value = []
        }
      } finally {
        loading.value = false
        loadingMore.value = false
      }
    }

    const loadMore = () => loadNotifications(true)

    const applyFilters = () => {
      loadNotifications(false)
    }

    const resetFilters = () => {
      filters.value = {
        unread: 'all',
        type: '',
        priority: '',
        search: '',
        dateFrom: '',
        dateTo: ''
      }
      loadNotifications(false)
    }

    const markRead = async (item) => {
      if (!item || item.is_read) return
      try {
        await notificationsApi.markRead(item.id)
        item.is_read = true
      } catch (error) {
        console.error('Error marking notification read:', error)
      }
    }

    const markAllRead = async () => {
      if (!notifications.value.length) return
      try {
        await notificationsApi.markAllRead()
        notifications.value = notifications.value.map((item) => ({ ...item, is_read: true }))
      } catch (error) {
        console.error('Error marking all notifications read:', error)
      }
    }

    const openNotification = async (item) => {
      await markRead(item)
      if (item && item.action_url) {
        router.push(item.action_url)
      }
    }

    onMounted(() => {
      loadNotifications(false)
      loadChannelSettings()
    })

    onBeforeUnmount(() => {
      stopTelegramStatusPolling()
    })

    return {
      notifications,
      loading,
      loadingMore,
      hasMore,
      settingsLoading,
      telegramBusy,
      telegramNotice,
      telegramNoticeType,
      telegramLinkUrl,
      telegramLinkExpiresAt,
      notificationPrefs,
      telegramStatus,
      telegramState,
      canToggleTelegram,
      filters,
      unreadOptions,
      typeOptions,
      priorityOptions,
      typeLabel,
      typeBadge,
      formatDateTime,
      loadNotifications,
      loadChannelSettings,
      loadMore,
      applyFilters,
      resetFilters,
      markRead,
      markAllRead,
      openNotification,
      updateTelegramDelivery,
      createTelegramLink,
      copyTelegramLink,
      disconnectTelegram
    }
  }
}
</script>

<style scoped>
.notifications-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-2);
}

.notifications-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-3);
}

.notifications-toolbar__title {
  margin: 0;
  font-weight: var(--fw-semibold);
  font-size: var(--text-2xl);
  color: var(--color-text);
}

.notifications-toolbar__actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.notifications-settings-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
  width: 100%;
}

.notifications-settings-card__title {
  font-size: var(--text-lg);
  font-weight: var(--fw-bold);
  line-height: var(--leading-tight);
}

.notifications-settings-card__subtitle {
  margin-top: var(--space-1);
  color: var(--color-text-muted);
  font-size: var(--text-md);
}

.notifications-settings-card__body {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.notifications-settings-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--space-3);
}

.notifications-settings-meta__item {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.notifications-settings-meta__label {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.notifications-settings-meta__value {
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.notifications-switch {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-height: auto;
  margin: 0;
  color: var(--color-text);
  font-size: var(--text-md);
  font-weight: var(--fw-medium);
}

.notifications-switch input {
  width: 16px;
  height: 16px;
  margin: 0;
  accent-color: var(--color-primary);
}

.notifications-settings-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.notifications-status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-pill);
  padding: var(--space-1) var(--space-3);
  font-size: var(--text-sm);
  font-weight: var(--fw-bold);
  white-space: nowrap;
}

.notifications-status-badge--success {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.notifications-status-badge--warning {
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.notifications-status-badge--muted {
  background: var(--color-surface-3);
  color: var(--color-text-muted);
}

.notifications-telegram-link {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-3) var(--space-4);
  background: var(--color-primary-soft);
}

.notifications-telegram-link__title {
  font-weight: var(--fw-bold);
  margin-bottom: var(--space-1);
  color: var(--color-text);
}

.notifications-telegram-link__hint,
.notifications-telegram-link__expires {
  color: var(--color-text-muted);
}

.notifications-telegram-link__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  margin-top: var(--space-2);
}

.notifications-inline-notice {
  border-radius: var(--radius-md);
  padding: var(--space-3);
  font-size: var(--text-md);
  font-weight: var(--fw-medium);
}

.notifications-inline-notice--info {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.notifications-inline-notice--success {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.notifications-inline-notice--warning {
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.notifications-inline-notice--danger {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.notifications-filters {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  width: 100%;
}

.notifications-filters__row {
  display: grid;
  grid-template-columns: minmax(220px, 1.5fr) repeat(3, minmax(150px, 1fr)) minmax(220px, 1fr);
  gap: var(--space-2);
}

.notifications-filters__search,
.notifications-filters__dates {
  min-width: 0;
}

.notifications-filters__dates {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-2);
}

.notifications-filters__actions {
  display: flex;
  gap: var(--space-2);
}

.notifications-loading {
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.notifications-empty {
  flex: 1;
  min-height: 320px;
}

.notifications-table-wrap {
  flex: 1;
  overflow: auto;
}

.notifications-table {
  width: 100%;
  border-collapse: collapse;
}

.notifications-table th,
.notifications-table td {
  padding: var(--space-3);
  border-bottom: 1px solid var(--color-border-subtle);
  text-align: left;
}

.notifications-table th {
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  color: var(--color-text-muted);
}

.sticky-header th {
  position: sticky;
  top: 0;
  background-color: var(--color-surface);
  z-index: 10;
}

.notification-unread {
  background-color: var(--color-primary-soft);
}

.notifications-table__title {
  max-width: 260px;
}

.notifications-table__message {
  max-width: 360px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.status-unread {
  background: var(--color-primary);
}

.status-read {
  background: var(--color-border-strong);
}

.notifications-row-actions,
.notifications-more {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-2);
}

.notifications-more {
  justify-content: center;
  width: 100%;
}

.fw-600 {
  font-weight: var(--fw-semibold);
}

@media (max-width: 1100px) {
  .notifications-filters__row {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 768px) {
  .notifications-view {
    padding: var(--space-2);
  }

  .notifications-toolbar,
  .notifications-settings-card__header {
    flex-direction: column;
    align-items: stretch;
  }

  .notifications-filters__row,
  .notifications-filters__dates {
    grid-template-columns: 1fr;
  }

  .notifications-filters__actions {
    flex-wrap: wrap;
  }

  .notifications-table {
    min-width: 880px;
  }
}
</style>
