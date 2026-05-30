<template>
  <header class="content-header">
    <button
      class="content-header__burger"
      type="button"
      :aria-label="isMobileMenuOpen ? 'Закрыть меню' : 'Открыть меню'"
      :aria-expanded="isMobileMenuOpen ? 'true' : 'false'"
      @click="toggleMobileMenu"
    >
      <i class="fas" :class="isMobileMenuOpen ? 'fa-times' : 'fa-bars'"></i>
    </button>
    <button class="content-header__search" type="button" @click="$emit('open-search')">
      <i class="fas fa-search"></i>
      <span class="content-header__search-label">Поиск по системе...</span>
      <span class="content-header__search-shortcut">Ctrl+K</span>
    </button>
    <div class="content-header__actions">
      <WorkdayTopbarChip />
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
        <div ref="personalizeRoot" class="ui-personalize">
          <button
            class="header-utility-btn"
            :class="{ 'is-active': personalizeOpen }"
            title="Стилизация интерфейса"
            @click="togglePersonalize"
          >
            <i class="fas fa-sliders"></i>
          </button>
          <transition name="uip-fade">
            <div v-if="personalizeOpen" class="uip-pop">
              <div class="uip-head">Стилизация интерфейса</div>

              <div class="uip-row">
                <label>Тема</label>
                <div class="uip-seg">
                  <button
                    v-for="opt in themeOptions"
                    :key="opt.value"
                    type="button"
                    class="uip-seg__btn"
                    :class="{ 'is-active': themeMode === opt.value }"
                    :title="opt.label"
                    @click="setThemeMode(opt.value)"
                  >
                    <i class="fas" :class="opt.icon"></i>
                    <span>{{ opt.label }}</span>
                  </button>
                </div>
              </div>

              <div class="uip-row">
                <label>Акцентный цвет</label>
                <div class="uip-swatches">
                  <button
                    v-for="preset in accentPresets"
                    :key="preset.name"
                    type="button"
                    class="uip-swatch"
                    :class="{ 'is-active': isAccentActive(preset.value) }"
                    :style="{ background: preset.swatch }"
                    :title="preset.name"
                    @click="pickAccent(preset.value)"
                  >
                    <i v-if="isAccentActive(preset.value)" class="fas fa-check"></i>
                  </button>
                  <label class="uip-swatch uip-swatch--custom" title="Свой цвет">
                    <i class="fas fa-eye-dropper"></i>
                    <input
                      type="color"
                      :value="uiAccent || '#2563eb'"
                      @input="onCustomAccent"
                    >
                  </label>
                </div>
              </div>

              <div class="uip-row">
                <label>Плотность</label>
                <div class="uip-seg">
                  <button
                    type="button"
                    class="uip-seg__btn"
                    :class="{ 'is-active': uiDensity === 'comfortable' }"
                    @click="setDensity('comfortable')"
                  >
                    <span>Обычная</span>
                  </button>
                  <button
                    type="button"
                    class="uip-seg__btn"
                    :class="{ 'is-active': uiDensity === 'compact' }"
                    @click="setDensity('compact')"
                  >
                    <span>Компактная</span>
                  </button>
                </div>
              </div>

              <div class="uip-row">
                <label>Масштаб текста</label>
                <input
                  type="range" min="80" max="130" step="5"
                  v-model.number="uiFontScale"
                  @input="applyUiPrefs"
                >
                <span class="uip-val">{{ uiFontScale }}%</span>
              </div>

              <div class="uip-row">
                <label>Яркость фона</label>
                <input
                  type="range" min="50" max="150" step="1"
                  v-model.number="uiBrightness"
                  @input="applyUiPrefs"
                >
                <span class="uip-val">{{ uiBrightness }}%</span>
              </div>

              <div class="uip-row">
                <label>Блюр панелей</label>
                <input
                  type="range" min="0" max="24" step="1"
                  v-model.number="uiBarBlur"
                  @input="applyUiPrefs"
                >
                <span class="uip-val">{{ uiBarBlur }}px</span>
              </div>

              <div class="uip-sep"></div>

              <div class="uip-row">
                <label>Обои</label>
                <div class="uip-swatches">
                  <button
                    type="button"
                    class="uip-swatch uip-swatch--img"
                    :class="{ 'is-active': uiWpMode === 'image' }"
                    title="Загруженное изображение"
                    @click="setWallpaperMode('image')"
                  >
                    <i class="fas fa-image"></i>
                  </button>
                  <button
                    v-for="preset in wallpaperPresets"
                    :key="preset.id"
                    type="button"
                    class="uip-swatch"
                    :class="{ 'is-active': isPresetActive(preset.id) }"
                    :style="{ background: preset.css }"
                    :title="preset.name"
                    @click="setWallpaperPreset(preset.id)"
                  >
                    <i v-if="isPresetActive(preset.id)" class="fas fa-check"></i>
                  </button>
                  <label
                    class="uip-swatch uip-swatch--custom"
                    :class="{ 'is-active': uiWpMode === 'color' }"
                    title="Сплошной цвет"
                  >
                    <i class="fas fa-fill-drip"></i>
                    <input
                      type="color"
                      :value="uiWpColor || '#1e293b'"
                      @input="onWpColor"
                    >
                  </label>
                </div>
              </div>

              <div class="uip-row">
                <label>Размытие обоев</label>
                <input
                  type="range" min="0" max="40" step="1"
                  v-model.number="uiWpBlur"
                  @input="applyUiPrefs"
                >
                <span class="uip-val">{{ uiWpBlur }}px</span>
              </div>

              <div class="uip-row">
                <label>Затемнение обоев</label>
                <input
                  type="range" min="0" max="85" step="1"
                  v-model.number="uiWpDimPct"
                  @input="applyUiPrefs"
                >
                <span class="uip-val">{{ uiWpDimPct }}%</span>
              </div>

              <button type="button" class="uip-reset uip-reset--ghost" @click="resetWallpaper">
                Сбросить обои
              </button>

              <button
                v-if="activeUser?.wallpaper_url"
                type="button"
                class="uip-reset uip-reset--ghost"
                :disabled="uploadingWallpaper"
                @click="clearWallpaper"
              >
                <i class="fas fa-image-slash"></i>
                Вернуть стандартные обои
              </button>

              <div class="uip-sep"></div>

              <label class="uip-toggle">
                <input type="checkbox" v-model="uiHighContrast">
                <span>Высокий контраст</span>
              </label>

              <div class="uip-sep"></div>
              <div class="uip-head">Удобство</div>

              <div class="uip-row">
                <label>Стартовая страница</label>
                <select class="uip-select" v-model="uiStartPage">
                  <option value="/">Главная</option>
                  <option
                    v-for="link in startPageOptions"
                    :key="link.to"
                    :value="link.to"
                  >{{ link.label }}</option>
                </select>
              </div>

              <div class="uip-row">
                <label>Опрос уведомлений</label>
                <select class="uip-select" v-model.number="uiPollSeconds">
                  <option
                    v-for="opt in pollOptions"
                    :key="opt.value"
                    :value="opt.value"
                  >{{ opt.label }}</option>
                </select>
              </div>

              <label class="uip-toggle">
                <input type="checkbox" v-model="uiSoundEnabled">
                <span>Звук уведомлений</span>
              </label>
              <label class="uip-toggle">
                <input type="checkbox" v-model="uiMessengerSoundEnabled">
                <span>Звук сообщений мессенджера</span>
              </label>

              <div class="uip-row">
                <label>Часовой пояс</label>
                <select class="uip-select" v-model="uiTimezone">
                  <option
                    v-for="opt in tzOptions"
                    :key="opt.value"
                    :value="opt.value"
                  >{{ opt.label }}</option>
                </select>
              </div>

              <button type="button" class="uip-reset" @click="resetUiPrefs">
                Сбросить всё
              </button>
            </div>
          </transition>
        </div>
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
        <button
          type="button"
          class="user-profile__meta user-profile__meta-btn"
          :disabled="!activeUser"
          :title="activeUser ? 'Открыть мой профиль' : 'Пользователь не выбран'"
          @click="profileDrawerOpen = true"
        >
          <div class="user-profile__name">{{ activeUser?.full_name || 'Пользователь не выбран' }}</div>
          <div class="user-profile__hint">
            {{ activeUser ? (activeUser.role_name || 'Роль не назначена') : 'Выберите в разделе Пользователи' }}
          </div>
        </button>
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

  <!-- Профиль-драйвер: выезжает справа по клику на ФИО/роль в топбаре -->
  <ProfileDrawer v-model="profileDrawerOpen" />
</template>

<script>
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../../services/api'
import { useToast } from '../../composables/useToast'
import { useUiPreferences } from '../../composables/useUiPreferences'
import { useSidebar } from '../../composables/useSidebar'
import { WALLPAPER_PRESETS } from '../../config/wallpaperPresets'
import { navAllLinks } from '../../config/nav'
import { useAuthStore } from '../../stores/auth'
import { getStoredPermissions, saveActiveUser } from '../../utils/permissions'
import WorkdayTopbarChip from '../ui/WorkdayTopbarChip.vue'
import ProfileDrawer from '../ui/ProfileDrawer.vue'

export default {
  name: 'AppHeader',
  components: { WorkdayTopbarChip, ProfileDrawer },
  props: {
    activeUser: { type: Object, default: null },
    unreadCount: { type: Number, default: 0 },
    currentTimeLabel: { type: String, default: '' },
  },
  emits: ['open-search', 'open-vat', 'open-two-factor', 'open-notifications', 'user-updated'],
  setup(props, { emit }) {
    // Бургер мобильного меню — теперь живёт в хедере (in-flow).
    const { toggleMobileMenu, isMobileMenuOpen } = useSidebar()
    const authStore = useAuthStore()
    const { success: toastSuccess, error: toastError } = useToast()

    const avatarInput = ref(null)
    const wallpaperInput = ref(null)
    const uploadingAvatar = ref(false)
    const uploadingWallpaper = ref(false)
    const brokenAvatarUrls = ref(new Set())
    // Стейт правого drawer'а «Мой профиль». Открывается кликом по
    // ФИО/роли в топбаре; закрывается крестиком, кликом по оверлею
    // или Esc (логика внутри UiDrawer).
    const profileDrawerOpen = ref(false)

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

    /* ---- Персонализация интерфейса (единое хранилище: гибрид localStorage + бэкенд) ---- */
    const {
      prefs: uiPrefs,
      themeMode,
      setThemeMode,
      setBrightness,
      setBarBlur,
      setAccent,
      setDensity,
      setFontScale,
      setHighContrast,
      setWallpaperMode,
      setWallpaperPreset,
      setWallpaperColor,
      setWallpaperBlur,
      setWallpaperDim,
      setStartPage,
      setPollSeconds,
      setSoundEnabled,
      setMessengerSoundEnabled,
      setLocale,
      resetAppearance,
      resetWallpaper,
    } = useUiPreferences()
    const personalizeOpen = ref(false)
    const personalizeRoot = ref(null)

    const uiBrightness = computed({
      get: () => uiPrefs.appearance.brightness,
      set: (v) => setBrightness(v),
    })
    const uiBarBlur = computed({
      get: () => uiPrefs.appearance.barBlur,
      set: (v) => setBarBlur(v),
    })
    const uiFontScale = computed({
      get: () => uiPrefs.appearance.fontScale,
      set: (v) => setFontScale(v),
    })
    const uiDensity = computed(() => uiPrefs.appearance.density)
    const uiAccent = computed(() => uiPrefs.appearance.accent)
    const uiHighContrast = computed({
      get: () => uiPrefs.appearance.highContrast,
      set: (v) => setHighContrast(v),
    })

    const themeOptions = [
      { value: 'light', label: 'Светлая', icon: 'fa-sun' },
      { value: 'dark', label: 'Тёмная', icon: 'fa-moon' },
      { value: 'auto', label: 'Система', icon: 'fa-circle-half-stroke' },
    ]
    const accentPresets = [
      { name: 'По умолчанию', value: null, swatch: '#2563eb' },
      { name: 'Индиго', value: '#4f46e5', swatch: '#4f46e5' },
      { name: 'Бирюзовый', value: '#0d9488', swatch: '#0d9488' },
      { name: 'Зелёный', value: '#16a34a', swatch: '#16a34a' },
      { name: 'Фиолетовый', value: '#7c3aed', swatch: '#7c3aed' },
      { name: 'Розовый', value: '#db2777', swatch: '#db2777' },
      { name: 'Янтарный', value: '#d97706', swatch: '#d97706' },
      { name: 'Графит', value: '#475569', swatch: '#475569' },
    ]
    const isAccentActive = (value) => (uiAccent.value || null) === (value || null)
    const pickAccent = (value) => setAccent(value)
    const onCustomAccent = (event) => setAccent(event?.target?.value || null)

    /* ---- Обои ---- */
    const wallpaperPresets = WALLPAPER_PRESETS
    const uiWpMode = computed(() => uiPrefs.wallpaper.mode)
    const uiWpPresetId = computed(() => uiPrefs.wallpaper.presetId)
    const uiWpColor = computed(() => uiPrefs.wallpaper.color)
    const uiWpBlur = computed({
      get: () => uiPrefs.wallpaper.blur,
      set: (v) => setWallpaperBlur(v),
    })
    const uiWpDimPct = computed({
      get: () => Math.round((uiPrefs.wallpaper.dim || 0) * 100),
      set: (v) => setWallpaperDim((Number(v) || 0) / 100),
    })
    const isPresetActive = (id) =>
      uiPrefs.wallpaper.mode === 'preset' && uiPrefs.wallpaper.presetId === id
    const onWpColor = (event) => setWallpaperColor(event?.target?.value || null)

    /* ---- Продуктивность: стартовая страница, уведомления, локаль ---- */
    const startPageOptions = navAllLinks
    const uiStartPage = computed({
      get: () => uiPrefs.startPage || '/',
      set: (v) => setStartPage(v),
    })
    const pollOptions = [
      { value: 0, label: 'Вручную' },
      { value: 15, label: '15 сек' },
      { value: 30, label: '30 сек' },
      { value: 60, label: '1 мин' },
      { value: 300, label: '5 мин' },
    ]
    const uiPollSeconds = computed({
      get: () => uiPrefs.notifications.pollSeconds,
      set: (v) => setPollSeconds(Number(v)),
    })
    // Стейдж 2 имплицитного DM: звуковые уведомления (два независимых).
    const uiSoundEnabled = computed({
      get: () => uiPrefs.notifications.soundEnabled !== false,
      set: (v) => setSoundEnabled(v),
    })
    const uiMessengerSoundEnabled = computed({
      get: () => uiPrefs.notifications.messengerSoundEnabled !== false,
      set: (v) => setMessengerSoundEnabled(v),
    })
    const tzOptions = [
      { value: '', label: 'Системная' },
      { value: 'Europe/Moscow', label: 'Москва (MSK)' },
      { value: 'Europe/Kaliningrad', label: 'Калининград' },
      { value: 'Asia/Yekaterinburg', label: 'Екатеринбург' },
      { value: 'Asia/Novosibirsk', label: 'Новосибирск' },
      { value: 'Asia/Vladivostok', label: 'Владивосток' },
      { value: 'UTC', label: 'UTC' },
    ]
    const uiTimezone = computed({
      get: () => uiPrefs.locale.timezone || '',
      set: (v) => setLocale({ timezone: v || null }),
    })

    // Применение/persist/синхронизацию делает сам useUiPreferences —
    // здесь только заглушка для @input в шаблоне.
    const applyUiPrefs = () => {}
    const resetUiPrefs = () => resetAppearance()

    const togglePersonalize = () => { personalizeOpen.value = !personalizeOpen.value }
    const onDocClick = (event) => {
      if (!personalizeOpen.value) return
      if (personalizeRoot.value && !personalizeRoot.value.contains(event.target)) {
        personalizeOpen.value = false
      }
    }

    onMounted(() => {
      document.addEventListener('click', onDocClick, true)
    })
    onBeforeUnmount(() => {
      document.removeEventListener('click', onDocClick, true)
    })

    return {
      toggleMobileMenu,
      isMobileMenuOpen,
      avatarInput,
      wallpaperInput,
      uploadingAvatar,
      uploadingWallpaper,
      profileDrawerOpen,
      activeUserInitial,
      isAvatarBroken,
      markAvatarBroken,
      triggerAvatarPicker,
      triggerWallpaperPicker,
      onAvatarPicked,
      onWallpaperPicked,
      clearWallpaper,
      personalizeOpen,
      personalizeRoot,
      uiBrightness,
      uiBarBlur,
      uiFontScale,
      uiDensity,
      uiAccent,
      uiHighContrast,
      themeMode,
      themeOptions,
      setThemeMode,
      setDensity,
      accentPresets,
      isAccentActive,
      pickAccent,
      onCustomAccent,
      wallpaperPresets,
      uiWpMode,
      uiWpPresetId,
      uiWpColor,
      uiWpBlur,
      uiWpDimPct,
      isPresetActive,
      onWpColor,
      setWallpaperMode,
      setWallpaperPreset,
      resetWallpaper,
      startPageOptions,
      uiStartPage,
      pollOptions,
      uiPollSeconds,
      uiSoundEnabled,
      uiMessengerSoundEnabled,
      tzOptions,
      uiTimezone,
      applyUiPrefs,
      resetUiPrefs,
      togglePersonalize,
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

/* Когда .user-profile__meta — кнопка (клик открывает drawer профиля).
   Сбрасываем дефолтные кнопочные стили, оставляя визуал прежним. */
.user-profile__meta-btn {
  border: none;
  background: transparent;
  padding: 0;
  margin: 0;
  cursor: pointer;
  color: inherit;
  font: inherit;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  text-align: right;
}
.user-profile__meta-btn:disabled {
  cursor: default;
  opacity: 0.7;
}
.user-profile__meta-btn:focus-visible {
  outline: 2px solid var(--color-primary, #6366f1);
  outline-offset: 2px;
  border-radius: 6px;
}

.user-profile__name {
  font-weight: 700;
  font-size: 15px;
  color: rgba(255, 255, 255, 0.96);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-profile__hint {
  font-size: 10px;
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

/* ---- UI personalization popover ---- */
.ui-personalize {
  position: relative;
  display: inline-flex;
}

.uip-pop {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  z-index: 1400;
  width: 300px;
  max-height: min(78vh, 620px);
  overflow-y: auto;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(216, 224, 240, 0.92);
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.18);
  -webkit-backdrop-filter: blur(12px) saturate(140%);
  backdrop-filter: blur(12px) saturate(140%);
}

:root[data-theme="dark"] .uip-pop {
  background: rgba(20, 28, 44, 0.96);
  border-color: rgba(255, 255, 255, 0.08);
}

.uip-head {
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #7d8592;
  margin-bottom: 10px;
}

.uip-row {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 4px 8px;
  margin-bottom: 10px;
}

.uip-row label {
  grid-column: 1 / -1;
  font-size: 0.78rem;
  font-weight: 700;
  color: #0a1629;
}

:root[data-theme="dark"] .uip-row label {
  color: #e6ebf3;
}

.uip-row input[type="range"] {
  width: 100%;
  accent-color: var(--color-primary, #3f8cff);
  cursor: pointer;
}

.uip-val {
  min-width: 42px;
  text-align: right;
  font-size: 0.74rem;
  font-weight: 700;
  font-family: var(--font-mono, monospace);
  color: #7d8592;
}

/* segmented control (тема, плотность) */
.uip-seg {
  grid-column: 1 / -1;
  display: flex;
  gap: 4px;
  padding: 3px;
  border-radius: 10px;
  background: #eef2f8;
}

:root[data-theme="dark"] .uip-seg {
  background: rgba(255, 255, 255, 0.06);
}

.uip-seg__btn {
  flex: 1 1 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 6px 4px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: #5b6675;
  font-size: 0.72rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.uip-seg__btn i {
  font-size: 0.78rem;
}

.uip-seg__btn:hover {
  color: #0a1629;
}

.uip-seg__btn.is-active {
  background: #ffffff;
  color: var(--color-primary);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.14);
}

:root[data-theme="dark"] .uip-seg__btn {
  color: #aeb8c7;
}

:root[data-theme="dark"] .uip-seg__btn.is-active {
  background: rgba(255, 255, 255, 0.12);
  color: #e6ebf3;
}

/* свотчи акцентного цвета */
.uip-swatches {
  grid-column: 1 / -1;
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.uip-swatch {
  position: relative;
  width: 24px;
  height: 24px;
  padding: 0;
  border: 2px solid transparent;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 0 0 1px rgba(15, 23, 42, 0.12) inset;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.uip-swatch i {
  font-size: 0.62rem;
  color: #ffffff;
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.4);
}

.uip-swatch.is-active {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--color-primary-ring, rgba(37, 99, 235, 0.4));
}

.uip-swatch--custom {
  background: conic-gradient(red, yellow, lime, aqua, blue, magenta, red);
  overflow: hidden;
}

.uip-swatch--custom i {
  color: #ffffff;
}

.uip-swatch--custom input[type="color"] {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
  border: none;
  padding: 0;
}

/* тумблеры (контраст, анимация) */
.uip-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 0.78rem;
  font-weight: 700;
  color: #0a1629;
  cursor: pointer;
}

.uip-toggle input[type="checkbox"] {
  width: 15px;
  height: 15px;
  accent-color: var(--color-primary, #3f8cff);
  cursor: pointer;
}

:root[data-theme="dark"] .uip-toggle {
  color: #e6ebf3;
}

.uip-select {
  grid-column: 1 / -1;
  width: 100%;
  padding: 6px 8px;
  border: 1px solid rgba(216, 224, 240, 0.92);
  border-radius: 8px;
  background: #ffffff;
  color: #0a1629;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
}

:root[data-theme="dark"] .uip-select {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.12);
  color: #e6ebf3;
}

.uip-sep {
  height: 1px;
  margin: 4px 0 10px;
  background: rgba(216, 224, 240, 0.9);
}

:root[data-theme="dark"] .uip-sep {
  background: rgba(255, 255, 255, 0.08);
}

.uip-swatch--img {
  background: #e8edf5;
  color: #5b6675;
}

.uip-swatch--img i {
  color: #5b6675;
  text-shadow: none;
}

:root[data-theme="dark"] .uip-swatch--img {
  background: rgba(255, 255, 255, 0.1);
}

:root[data-theme="dark"] .uip-swatch--img i {
  color: #cbd5e1;
}

.uip-reset--ghost {
  margin-bottom: 6px;
  background: transparent;
}

.uip-reset--ghost:hover {
  background: #eef2f8;
}

:root[data-theme="dark"] .uip-reset--ghost {
  background: transparent;
}

.uip-reset {
  width: 100%;
  margin-top: 2px;
  padding: 6px 10px;
  border: 1px solid rgba(216, 224, 240, 0.92);
  border-radius: 9px;
  background: #f6f8fb;
  color: #0a1629;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s ease;
}

.uip-reset:hover {
  background: #eef2f8;
}

:root[data-theme="dark"] .uip-reset {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.1);
  color: #e6ebf3;
}

.uip-fade-enter-active,
.uip-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.uip-fade-enter-from,
.uip-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
