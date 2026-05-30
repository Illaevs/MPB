<template>
  <div class="app-root">
    <div class="app-wallpaper" :style="wallpaperLayerStyle" aria-hidden="true"></div>
    <div class="app-wallpaper-dim" aria-hidden="true"></div>
    <div
      v-if="isAuthPage"
      class="auth-shell"
    >
      <div class="auth-overlay"></div>
      <div class="auth-content">
        <router-view />
      </div>
    </div>

    <div v-else class="app-layout">
      <AppSidebar :permissions="permissions" />

    <main class="main-content">
      <AppHeader
        :active-user="activeUser"
        :unread-count="unreadCount"
        :current-time-label="currentTimeLabel"
        @open-search="$refs.commandPalette?.open()"
        @open-vat="vatCalculatorOpen = true"
        @open-two-factor="openTwoFactorModal"
        @open-notifications="openNotifications"
        @user-updated="onUserUpdated"
      />

      <div class="content-body">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>

    <VatCalculatorModal v-model="vatCalculatorOpen" />
    <TwoFactorModal v-model="twoFactorModalOpen" />

    <!-- Global Components -->
    <ToastContainer />
    <ConfirmDialog />
    <CommandPalette ref="commandPalette" />
    <DownloadQueue v-if="!isAuthPage && activeUser" />
    <UploadQueue v-if="!isAuthPage && activeUser" />
    <ChatCenter
      v-if="!isAuthPage && activeUser && canAccess('global_chat')"
      v-model="chatCenterOpen"
    />
    <!-- GlobalAiAssistant временно скрыт (включить — раскомментировать строку ниже) -->
    <!-- <GlobalAiAssistant v-if="!isAuthPage && activeUser" /> -->
    <NotificationCenter
      v-if="!isAuthPage && activeUser"
      v-model="notificationCenterOpen"
      @unread-count-changed="onUnreadCountChanged"
    />
    <WorkdayStartModal v-if="!isAuthPage && activeUser" />
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useNotificationsStore } from './stores/notifications'
import { useWorkdayStore } from './stores/workday'
import { useIdleTracker } from './composables/useIdleTracker'
import { usePresence } from './composables/usePresence'
import WorkdayStartModal from './components/ui/WorkdayStartModal.vue'
import ToastContainer from './components/ui/ToastContainer.vue'
import ConfirmDialog from './components/ui/ConfirmDialog.vue'
import CommandPalette from './components/ui/CommandPalette.vue'
import DownloadQueue from './components/ui/DownloadQueue.vue'
import UploadQueue from './components/ui/UploadQueue.vue'
import TwoFactorModal from './components/ui/TwoFactorModal.vue'
import ChatCenter from './components/ui/ChatCenter.vue'
import NotificationCenter from './components/ui/NotificationCenter.vue'
import GlobalAiAssistant from './components/ui/GlobalAiAssistant.vue'
import VatCalculatorModal from './components/ui/VatCalculatorModal.vue'
import AppSidebar from './components/layout/AppSidebar.vue'
import AppHeader from './components/layout/AppHeader.vue'
import { hasSectionAccess } from './utils/permissions'
import { useAuthStore } from './stores/auth'
import { useToast } from './composables/useToast'
import { useTheme } from './composables/useTheme'
import { useSidebar } from './composables/useSidebar'
import { useUiPreferences } from './composables/useUiPreferences'
import { getWallpaperPreset } from './config/wallpaperPresets'
import { formatTime } from './utils/format'
import { serverDate, formatMsk } from './composables/useServerClock'
import { appBrandPrimary, appBrandSecondary, appSystemName } from './config/appVariant'
import bgImage from './assets/app-bg.jpg'

export default {
  name: 'App',
  components: {
    ToastContainer,
    ConfirmDialog,
    CommandPalette,
    DownloadQueue,
    UploadQueue,
    TwoFactorModal,
    ChatCenter,
    NotificationCenter,
    AppSidebar,
    AppHeader,
    VatCalculatorModal,
    GlobalAiAssistant,
    WorkdayStartModal
  },
  setup() {
    const authStore = useAuthStore()
    const workdayStore = useWorkdayStore()
    // Глобальный idle-трекер: каждое движение/клик/keydown обновляет
    // lastActivityAt у workday-стора. Композабл сам цепляется к window
    // и снимется на unmount компонента App.
    useIdleTracker(() => workdayStore.markActivity())
    // Phase C.2: presence heartbeat — пинг users/me/heartbeat раз в
    // 60с с любой страницы. Backend обновляет users.last_seen_at.
    usePresence()
    const route = useRoute()
    // Тему и состояние сайдбара ведут singleton-композаблы; AppSidebar читает их сам.
    useTheme()
    const { isTabletViewport, closeMobileMenu } = useSidebar()
    // Permissions из auth-стора — реактивно прокидываем в AppSidebar.
    const permissions = computed(() => authStore.permissions || {})

    // Уведомления: store ведёт fetch + поллинг + unreadCount;
    // App.vue только подписывается и эмитит toast для новых.
    const notificationsStore = useNotificationsStore()
    const unreadCount = computed(() => notificationsStore.unreadCount)

    const activeUser = ref(null)
    const twoFactorModalOpen = ref(false)
    const vatCalculatorOpen = ref(false)
    const isAuthPage = computed(() => route.name === 'Login')
    const isMessengerPage = computed(() => route.name === 'Messenger')
    const currentTimeLabel = ref('')

    const { add: addToast } = useToast()
    const { prefs: uiPrefs } = useUiPreferences()
    let clockTimer = null
    let lastNotificationAt = 0
    const seenNotifications = new Set()

    const updateCurrentTime = () => {
      // Часы в топбаре: серверное время, отображаем по МСК (UTC+3) —
      // независимо от часов и таймзоны устройства. Если у юзера ноут
      // отстаёт на 24 мин, часы всё равно покажут реальное московское.
      currentTimeLabel.value = formatMsk(serverDate())
    }

    // Фон-обои: отдельный фиксированный слой (.app-wallpaper) с независимым
    // размытием/затемнением (--ui-wp-blur / --ui-wp-dim из useUiPreferences).
    const wallpaperImageBroken = ref(false)
    const wallpaperImageUrl = computed(() =>
      String(activeUser.value?.wallpaper_url || '').trim()
    )

    watch(
      wallpaperImageUrl,
      (url) => {
        wallpaperImageBroken.value = false
        if (!url || typeof Image === 'undefined') return
        const probe = new Image()
        probe.onerror = () => { wallpaperImageBroken.value = true }
        probe.src = url
      },
      { immediate: true }
    )

    const wallpaperLayerStyle = computed(() => {
      const wp = uiPrefs.wallpaper || {}
      if (wp.mode === 'color' && wp.color) {
        return { background: wp.color }
      }
      if (wp.mode === 'preset') {
        const preset = getWallpaperPreset(wp.presetId)
        if (preset) return { backgroundImage: preset.css }
      }
      const src =
        wallpaperImageUrl.value && !wallpaperImageBroken.value
          ? wallpaperImageUrl.value
          : bgImage
      return { backgroundImage: `url(${src})` }
    })

    const handlePermissionsUpdate = () => {
      activeUser.value = authStore.user || null
    }

    const notificationCenterOpen = ref(false)
    const chatCenterOpen = ref(false)

    const openNotifications = () => {
      chatCenterOpen.value = false
      notificationCenterOpen.value = true
    }

    const openChatCenter = () => {
      notificationCenterOpen.value = false
      chatCenterOpen.value = true
    }

    const onUnreadCountChanged = (count) => {
      // NotificationCenter всё ещё эмитит счётчик; синхронизируем store,
      // чтобы шапка и центр уведомлений не расходились до полного перехода
      // NotificationCenter на store.
      notificationsStore.unreadCount = Number(count) || 0
    }

    const openTwoFactorModal = () => {
      if (!activeUser.value) return
      twoFactorModalOpen.value = true
    }

    // AppHeader управляет загрузкой аватара/обоев и сообщает обновлённого
    // пользователя сюда — синхронизируем wallpaper + activeUser.
    const onUserUpdated = (updatedUser) => {
      activeUser.value = updatedUser
    }

    const getNotificationTimestamp = (item) => {
      const value = item?.deliver_at || item?.created_at
      const ts = value ? new Date(value).getTime() : 0
      return Number.isFinite(ts) ? ts : 0
    }

    const getToastType = (item) => {
      const value = (item?.type || item?.priority || 'info').toLowerCase()
      if (['success', 'error', 'warning', 'info'].includes(value)) {
        return value
      }
      return 'info'
    }

    const buildToastMessage = (item) => {
      if (!item) return ''
      if (item.message) {
        return `${item.title}: ${item.message}`
      }
      return item.title || 'Новое уведомление'
    }

    // Сидим на изменениях items в store и эмитим toast для новых.
    // Первый прогон (showToasts=false) — просто заполняет seenNotifications,
    // дальше каждый новый id уезжает в toast.
    let toastInitialized = false
    const emitToastsForNew = (items) => {
      items.forEach((item) => {
        const ts = getNotificationTimestamp(item)
        if (seenNotifications.has(item.id)) {
          if (ts > lastNotificationAt) lastNotificationAt = ts
          return
        }
        seenNotifications.add(item.id)
        if (toastInitialized && ts > lastNotificationAt) {
          addToast(getToastType(item), buildToastMessage(item), 3500)
        }
        if (ts > lastNotificationAt) lastNotificationAt = ts
      })
      toastInitialized = true
    }

    watch(
      () => notificationsStore.items,
      (items) => {
        const unread = (items || []).filter((it) => !it.is_read)
        emitToastsForNew(unread)
      },
      { deep: false }
    )

    const startNotificationPolling = () => {
      notificationsStore.startPolling(uiPrefs.notifications?.pollSeconds)
    }

    // Workday: после логина подтягиваем активную сессию + запускаем
    // heartbeat/idle-таймеры в сторе. На logout — reset.
    const startWorkday = async () => {
      await workdayStore.fetchActive({ silent: true })
      workdayStore.startTimers()
    }
    const stopWorkday = () => {
      workdayStore.stopTimers()
      workdayStore.reset()
    }

    // Смена частоты опроса в настройках применяется на лету.
    watch(
      () => uiPrefs.notifications?.pollSeconds,
      (value) => notificationsStore.setPollSeconds(value)
    )

    // Смена локали/таймзоны — мгновенно перерисовываем часы в шапке.
    watch(
      () => [uiPrefs.locale?.dateFormat, uiPrefs.locale?.timezone],
      () => updateCurrentTime()
    )

    const stopNotificationPolling = () => {
      notificationsStore.stopPolling()
      seenNotifications.clear()
      lastNotificationAt = 0
      toastInitialized = false
    }

    onMounted(() => {
      handlePermissionsUpdate()
      updateCurrentTime()
      window.addEventListener('permissions-updated', handlePermissionsUpdate)
      window.addEventListener('storage', handlePermissionsUpdate)
      // Раз в секунду — чтобы при выпадении minutes между 30-сек тиками
      // часы не «прыгали». Серверный offset обновляется через HTTP-
      // interceptor, по тикам уже считываем актуальный.
      clockTimer = setInterval(updateCurrentTime, 1000)

      if (!isAuthPage.value && activeUser.value) {
        startNotificationPolling()
        startWorkday()
      }
    })

    onBeforeUnmount(() => {
      window.removeEventListener('permissions-updated', handlePermissionsUpdate)
      window.removeEventListener('storage', handlePermissionsUpdate)
      if (clockTimer) {
        clearInterval(clockTimer)
        clockTimer = null
      }
      stopNotificationPolling()
    })

    const canAccess = (section) => hasSectionAccess(section)

    watch(isAuthPage, (value) => {
      if (value) {
        stopNotificationPolling()
        notificationsStore.reset()
        stopWorkday()
        return
      }
      if (activeUser.value) {
        startNotificationPolling()
        startWorkday()
      }
    })

    watch(activeUser, (value) => {
      if (!value || isAuthPage.value) {
        stopNotificationPolling()
        notificationsStore.reset()
        stopWorkday()
        return
      }
      startNotificationPolling()
      startWorkday()
    })

    watch(() => route.fullPath, () => {
      if (isTabletViewport.value) {
        closeMobileMenu()
      }
    })

    return {
      // permissions — в AppSidebar
      permissions,
      // user / state
      activeUser,
      twoFactorModalOpen,
      vatCalculatorOpen,
      // header data
      currentTimeLabel,
      unreadCount,
      // brand
      appBrandPrimary,
      appBrandSecondary,
      appSystemName,
      // routing flags
      isAuthPage,
      isMessengerPage,
      // permissions check (для ChatCenter conditional и т.п.)
      canAccess,
      // global widgets
      openNotifications,
      openChatCenter,
      chatCenterOpen,
      notificationCenterOpen,
      onUnreadCountChanged,
      openTwoFactorModal,
      // AppHeader events
      onUserUpdated,
      // wallpaper layer
      wallpaperLayerStyle,
    }
  }
}
</script>

<style scoped>
.app-root {
  min-height: 100vh;        /* фолбэк для старых браузеров */
  min-height: 100dvh;       /* учитывает адресную строку моб. браузеров */
}

/* Фиксированный слой обоев: размытие/затемнение независимы от
   контентного scrim («Яркость фона»). */
.app-wallpaper {
  position: fixed;
  inset: 0;
  z-index: -2;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  filter: blur(var(--ui-wp-blur, 0px));
  transform: scale(1.06);
  transform-origin: center;
  pointer-events: none;
}

.app-wallpaper-dim {
  position: fixed;
  inset: 0;
  z-index: -1;
  background: #000;
  opacity: var(--ui-wp-dim, 0);
  pointer-events: none;
}
.auth-shell {
  position: relative;
  min-height: 100vh;
  min-height: 100dvh;
  max-height: 100vh;
  max-height: 100dvh;
  display: flex;
  align-items: safe center;
  justify-content: center;
  padding: 20px 40px;
  background:
    radial-gradient(circle at top left, rgba(255, 255, 255, 0.35), transparent 26%),
    radial-gradient(circle at bottom right, rgba(255, 255, 255, 0.3), transparent 24%),
    linear-gradient(180deg, rgba(244, 249, 253, 0.92), rgba(244, 249, 253, 0.84));
  overflow-y: auto;
}
.auth-overlay {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at top left, rgba(255, 255, 255, 0.4), transparent 28%),
    radial-gradient(circle at bottom right, rgba(255, 255, 255, 0.28), transparent 24%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.26));
  pointer-events: none;
}
.auth-content {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1440px;
  padding: 0;
}

@media (max-width: 760px) {
  .auth-shell {
    padding: 20px;
  }
}


.content-body {
  position: relative;
  min-height: calc(100vh - 64px);
  background: rgba(28, 39, 53, var(--ui-scrim, 0.32));
  backdrop-filter: blur(1px) saturate(100%);
  -webkit-backdrop-filter: blur(1px) saturate(100%);
}

:root[data-theme="dark"] .content-body {
  background: rgba(15, 23, 42, 0.76);
}

.content-body::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: transparent;
  z-index: 0;
  pointer-events: none;
}

.content-body > * {
  position: relative;
  z-index: 1;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

