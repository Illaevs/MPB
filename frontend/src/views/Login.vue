<template>
  <section class="login-page">
    <div class="login-shell">
      <aside class="login-aside">
        <span class="login-aside__orb login-aside__orb--a" aria-hidden="true"></span>
        <span class="login-aside__orb login-aside__orb--b" aria-hidden="true"></span>
        <span class="login-aside__grid" aria-hidden="true"></span>

        <div class="login-aside__inner">
          <div class="login-brand">
            <span class="login-brand__logo">{{ appBrandPrimary.charAt(0) }}</span>
            <span class="login-brand__text">
              <span class="login-brand__primary">{{ appBrandPrimary }}</span>
              <span v-if="appBrandSecondary" class="login-brand__secondary">{{ appBrandSecondary }}</span>
            </span>
          </div>

          <div class="login-aside__hero">
            <span class="login-eyebrow">ERP workspace</span>
            <h1>Инновационное рабочее пространство</h1>
            <p>Сделки, задачи, документы, финансы и коммуникации в одной системе.</p>
          </div>

          <ul class="login-features">
            <li class="login-feature">
              <span class="login-feature__icon"><i class="fas fa-briefcase" aria-hidden="true"></i></span>
              <span class="login-feature__body">
                <span class="login-feature__title">Сделки и задачи в одном потоке</span>
                <span class="login-feature__hint">Воронки, статусы и сроки без переключения окон.</span>
              </span>
            </li>
            <li class="login-feature">
              <span class="login-feature__icon"><i class="fas fa-file-invoice-dollar" aria-hidden="true"></i></span>
              <span class="login-feature__body">
                <span class="login-feature__title">Документы и финансы под контролем</span>
                <span class="login-feature__hint">Договоры, счета и бюджеты с историей изменений.</span>
              </span>
            </li>
            <li class="login-feature">
              <span class="login-feature__icon"><i class="fas fa-comments" aria-hidden="true"></i></span>
              <span class="login-feature__body">
                <span class="login-feature__title">Командные коммуникации внутри системы</span>
                <span class="login-feature__hint">Обсуждения и уведомления рядом с задачами.</span>
              </span>
            </li>
          </ul>

          <div class="login-aside__foot">© {{ new Date().getFullYear() }} · {{ appSystemName }}</div>
        </div>
      </aside>

      <section class="login-main">
        <div class="login-card-glass">
          <div class="login-badge">
            <span class="login-badge__dot" aria-hidden="true"></span>
            {{ appSystemName }}
          </div>

          <header class="login-head">
            <h2 v-if="pendingTwoFactorSetup" class="login-title">Обязательная настройка 2FA</h2>
            <h2 v-else-if="activeUser" class="login-title">Сессия активна</h2>
            <h2 v-else-if="pendingTwoFactor" class="login-title">Подтвердите вход</h2>
            <h2 v-else class="login-title">Вход</h2>

            <p v-if="pendingTwoFactorSetup" class="login-copy">Для доступа к системе необходимо один раз включить двухфакторную аутентификацию.</p>
            <p v-else-if="activeUser" class="login-copy">Продолжите работу под текущим пользователем или завершите сессию.</p>
            <p v-else-if="pendingTwoFactor" class="login-copy">Введите код из приложения-аутентификатора или резервный код.</p>
            <p v-else class="login-copy">Авторизуйтесь, чтобы открыть рабочее пространство.</p>
          </header>

          <form v-if="pendingTwoFactorSetup" class="login-form" @submit.prevent="submitRequiredTwoFactorSetup">
            <div class="login-info">
              <div class="login-info__title">{{ pendingTwoFactorSetup.email }}</div>
              <div class="login-info__subtitle">Настройте 2FA, чтобы завершить вход.</div>
            </div>

            <div class="login-info">
              <div class="login-info__subtitle">
                Отсканируйте QR-код через Google Authenticator, Microsoft Authenticator, 1Password
                или другое TOTP-приложение.
              </div>
            </div>

            <div v-if="qrDataUrl" class="login-setup">
              <div class="login-setup__qr"><img :src="qrDataUrl" alt="QR-код для настройки двухфакторной аутентификации" /></div>
              <div class="login-setup__meta">
                <div class="login-field__label">Ручной ключ</div>
                <code class="login-secret">{{ setupSecret }}</code>
                <UiButton
                  type="button"
                  variant="secondary"
                  size="sm"
                  icon-left="fas fa-rotate"
                  :disabled="loading || setupCompleted"
                  @click="startRequiredTwoFactorSetup"
                >
                  Обновить QR
                </UiButton>
              </div>
            </div>

            <label v-if="!setupCompleted" class="login-field">
              <span class="login-field__label">Код из приложения</span>
              <UiInput
                v-model="setupCode"
                type="text"
                size="lg"
                icon-left="fas fa-shield-halved"
                autocomplete="one-time-code"
                placeholder="123456"
                maxlength="6"
              />
            </label>

            <div v-if="error" class="login-alert">
              <i class="fas fa-circle-exclamation" aria-hidden="true"></i>
              <span>{{ error }}</span>
            </div>

            <div v-if="backupCodes.length" class="login-info">
              <div class="login-info__title">Резервные коды</div>
              <div class="login-info__subtitle">Сохраните их в безопасном месте. Каждый код используется один раз.</div>
              <div class="login-codes">
                <code v-for="code in backupCodes" :key="code">{{ code }}</code>
              </div>
            </div>

            <div class="login-actions">
              <UiButton v-if="!setupCompleted" type="submit" variant="primary" size="lg" block class="login-submit" :loading="loading">
                {{ loading ? 'Подтверждение...' : 'Подтвердить и сохранить коды' }}
              </UiButton>
              <UiButton
                v-else
                type="button"
                variant="primary"
                size="lg"
                block
                class="login-submit"
                :loading="loading"
                @click="completeRequiredTwoFactorSetup"
              >
                {{ loading ? 'Подготовка...' : 'Продолжить в систему' }}
              </UiButton>
              <UiButton type="button" variant="secondary" size="lg" class="login-secondary" :disabled="loading" @click="logout">
                Выйти
              </UiButton>
            </div>
          </form>

          <template v-else-if="activeUser">
            <div class="login-account">
              <span class="login-account__avatar">{{ (activeUser.full_name || activeUser.email || '?').charAt(0) }}</span>
              <span class="login-account__body">
                <span class="login-account__name">{{ activeUser.full_name }}</span>
                <span class="login-account__mail">{{ activeUser.email }}</span>
              </span>
            </div>
            <div v-if="error" class="login-alert">
              <i class="fas fa-circle-exclamation" aria-hidden="true"></i>
              <span>{{ error }}</span>
            </div>
            <div class="login-actions">
              <UiButton variant="primary" size="lg" block class="login-submit" @click="goHome">Продолжить работу</UiButton>
              <UiButton variant="secondary" size="lg" class="login-secondary" @click="logout">Выйти</UiButton>
            </div>
          </template>

          <form v-else-if="pendingTwoFactor" class="login-form" @submit.prevent="submitTwoFactor">
            <div class="login-info">
              <div class="login-info__title">{{ pendingTwoFactor.email }}</div>
              <div class="login-info__subtitle">Проверка второго фактора перед выдачей доступа.</div>
            </div>
            <label class="login-field">
              <span class="login-field__label">Код подтверждения</span>
              <UiInput
                v-model="twoFactorCode"
                type="text"
                size="lg"
                icon-left="fas fa-shield-halved"
                autocomplete="one-time-code"
                placeholder="123456 или BACK-UP12"
                maxlength="16"
              />
            </label>
            <div class="login-info">
              <div class="login-info__subtitle">Подойдут коды из Google Authenticator, Microsoft Authenticator, 1Password и резервные backup codes.</div>
            </div>
            <div v-if="error" class="login-alert">
              <i class="fas fa-circle-exclamation" aria-hidden="true"></i>
              <span>{{ error }}</span>
            </div>
            <div class="login-actions">
              <UiButton type="submit" variant="primary" size="lg" block class="login-submit" :loading="loading">
                {{ loading ? 'Проверка...' : 'Подтвердить вход' }}
              </UiButton>
              <UiButton type="button" variant="secondary" size="lg" class="login-secondary" :disabled="loading" @click="cancelTwoFactor">
                Назад
              </UiButton>
            </div>
          </form>

          <form v-else class="login-form" @submit.prevent="submit">
            <label class="login-field">
              <span class="login-field__label">Логин</span>
              <UiInput
                v-model="email"
                type="email"
                size="lg"
                required
                icon-left="fas fa-envelope"
                autocomplete="email"
                placeholder="вашапочта@домен.ру"
              />
            </label>
            <label class="login-field">
              <span class="login-field__label">Пароль</span>
              <div class="login-password">
                <i class="fas fa-lock login-password__lead" aria-hidden="true"></i>
                <input
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  class="login-password__input"
                  required
                  autocomplete="current-password"
                  placeholder="••••••••"
                />
                <button type="button" class="login-password__toggle" :title="showPassword ? 'Скрыть пароль' : 'Показать пароль'" :aria-label="showPassword ? 'Скрыть пароль' : 'Показать пароль'" @click="showPassword = !showPassword">
                  <i class="fas" :class="showPassword ? 'fa-eye-slash' : 'fa-eye'" aria-hidden="true"></i>
                </button>
              </div>
            </label>
            <div v-if="error" class="login-alert">
              <i class="fas fa-circle-exclamation" aria-hidden="true"></i>
              <span>{{ error }}</span>
            </div>
            <UiButton type="submit" variant="primary" size="lg" block class="login-submit" :loading="loading">
              {{ loading ? 'Вход...' : 'Войти' }}
            </UiButton>
          </form>

          <div v-if="isSuperuser && activeUser" class="login-info login-impersonation">
            <div class="login-info__title">Выбрать пользователя</div>
            <div class="login-info__subtitle">Быстрое переключение для проверки ролей и сценариев.</div>
            <UiSelect v-model="selectedUser" :options="userOptions" placeholder="Выберите пользователя" />
            <UiButton variant="outline" size="lg" block :loading="impersonateLoading" :disabled="!selectedUser || impersonateLoading" @click="impersonate">
              Переключиться
            </UiButton>
          </div>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { api } from '../services/api'
import QRCode from 'qrcode'
import { useRoute, useRouter } from 'vue-router'
import { UiButton, UiInput, UiSelect } from '../components/ui'
import { useAuthStore } from '../stores/auth'
import { getActiveUser } from '../utils/permissions'
import { appBrandPrimary, appBrandSecondary, appSystemName, isTestPortalVariant } from '../config/appVariant'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const email = ref('')
const password = ref('')
const twoFactorCode = ref('')
const setupSecret = ref('')
const setupCode = ref('')
const qrDataUrl = ref('')
const backupCodes = ref([])
const setupCompleted = ref(false)
const showPassword = ref(false)
const loading = ref(false)
const impersonateLoading = ref(false)
const error = ref('')
const users = ref([])
const selectedUser = ref('')

const pendingTwoFactor = computed(() => auth.pendingTwoFactor)
const pendingTwoFactorSetup = computed(() => auth.pendingTwoFactorSetup)
const isSuperuser = computed(() => auth.isSuperuser)
const activeUser = computed(() => {
  if (pendingTwoFactorSetup.value) return null
  if (!auth.accessToken) return null
  return auth.user || getActiveUser()
})
const userOptions = computed(() => users.value.map((u) => ({
  value: u.id,
  label: `${u.full_name} — ${u.email}`
})))

const sanitizeRedirect = (redirect) => {
  if (typeof redirect !== 'string' || !redirect.startsWith('/')) return '/'
  if (redirect.startsWith('//') || redirect.includes('://') || redirect.startsWith('/\\')) return '/'
  return redirect
}

const goHome = () => router.push(sanitizeRedirect(route.query.redirect))

const resetRequiredTwoFactorSetup = () => {
  setupSecret.value = ''
  setupCode.value = ''
  qrDataUrl.value = ''
  backupCodes.value = []
  setupCompleted.value = false
}

const startRequiredTwoFactorSetup = async () => {
  if (!pendingTwoFactorSetup.value) return
  loading.value = true
  error.value = ''
  try {
    const data = await auth.startTwoFactorSetup()
    setupSecret.value = data.secret
    setupCode.value = ''
    backupCodes.value = []
    setupCompleted.value = false
    qrDataUrl.value = await QRCode.toDataURL(data.otpauth_url, { width: 220, margin: 1 })
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось начать настройку 2FA'
  } finally {
    loading.value = false
  }
}

const submit = async () => {
  loading.value = true
  error.value = ''
  try {
    const data = await auth.login(email.value, password.value)
    if (data?.requires_2fa) {
      password.value = ''
      twoFactorCode.value = ''
      return
    }
    if (data?.requires_2fa_setup) {
      password.value = ''
      twoFactorCode.value = ''
      await startRequiredTwoFactorSetup()
      return
    }
    if (auth.isSuperuser) await loadUsers()
    goHome()
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Ошибка авторизации'
  } finally {
    loading.value = false
  }
}

const submitTwoFactor = async () => {
  loading.value = true
  error.value = ''
  try {
    await auth.verifyTwoFactor(twoFactorCode.value)
    twoFactorCode.value = ''
    if (auth.isSuperuser) await loadUsers()
    goHome()
  } catch (e) {
    const detail = e?.response?.data?.detail || 'Не удалось подтвердить код'
    if (detail.includes('Срок подтверждения 2FA истек') || detail.includes('Недействительный токен подтверждения 2FA')) {
      auth.cancelPendingTwoFactor()
      twoFactorCode.value = ''
    }
    error.value = detail
  } finally {
    loading.value = false
  }
}

const submitRequiredTwoFactorSetup = async () => {
  if (!setupSecret.value || !setupCode.value.trim()) {
    error.value = 'Введите код из приложения-аутентификатора'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const data = await auth.confirmTwoFactorSetup(setupSecret.value, setupCode.value.trim())
    backupCodes.value = data?.backup_codes || []
    setupCompleted.value = true
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось подтвердить настройку 2FA'
  } finally {
    loading.value = false
  }
}

const completeRequiredTwoFactorSetup = async () => {
  loading.value = true
  error.value = ''
  try {
    await auth.refresh()
    auth.clearPendingTwoFactorSetup()
    if (auth.isSuperuser) await loadUsers()
    goHome()
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось завершить вход после настройки 2FA'
  } finally {
    loading.value = false
  }
}

const cancelTwoFactor = () => {
  auth.cancelPendingTwoFactor()
  twoFactorCode.value = ''
  error.value = ''
}

const loadUsers = async () => {
  impersonateLoading.value = true
  try {
    const data = await api.users.list()
    users.value = data || []
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось загрузить пользователей'
  } finally {
    impersonateLoading.value = false
  }
}

const impersonate = async () => {
  if (!selectedUser.value) return
  impersonateLoading.value = true
  error.value = ''
  try {
    await auth.impersonate(selectedUser.value)
    goHome()
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось переключиться'
  } finally {
    impersonateLoading.value = false
  }
}

const logout = () => auth.logout()

watch(pendingTwoFactorSetup, async (value) => {
  if (!value) {
    resetRequiredTwoFactorSetup()
    return
  }
  if (!setupSecret.value && !loading.value) await startRequiredTwoFactorSetup()
})

onMounted(async () => {
  if (!isTestPortalVariant && auth.accessToken && auth.user?.two_factor_enabled === false) {
    auth.setPendingTwoFactorSetup({ email: auth.user?.email || '' })
    await startRequiredTwoFactorSetup()
    return
  }
  if (auth.accessToken && auth.isSuperuser) await loadUsers()
})
</script>

<style scoped>
.login-page {
  width: 100%;
}

.login-shell {
  position: relative;
  min-height: min(760px, calc(100vh - 40px));
  display: grid;
  grid-template-columns: minmax(420px, 1.05fr) minmax(440px, 1fr);
  border-radius: var(--radius-2xl);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
}

/* ---------- Left showcase ---------- */
.login-aside {
  position: relative;
  isolation: isolate;
  padding: var(--space-12);
  color: var(--color-text-inverse);
  background:
    radial-gradient(120% 120% at 100% 0%, color-mix(in srgb, var(--color-primary-hover) 70%, #000 0%) 0%, transparent 55%),
    linear-gradient(160deg, var(--color-primary) 0%, var(--color-primary-hover) 100%);
  overflow: hidden;
}

.login-aside__orb {
  position: absolute;
  border-radius: var(--radius-pill);
  filter: blur(60px);
  opacity: 0.55;
  z-index: -1;
  pointer-events: none;
}

.login-aside__orb--a {
  width: 360px;
  height: 360px;
  top: -120px;
  right: -90px;
  background: rgba(255, 255, 255, 0.55);
}

.login-aside__orb--b {
  width: 300px;
  height: 300px;
  bottom: -110px;
  left: -80px;
  background: color-mix(in srgb, var(--color-primary) 40%, #fff 60%);
}

.login-aside__grid {
  position: absolute;
  inset: 0;
  z-index: -1;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.06) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: radial-gradient(120% 80% at 30% 20%, #000 0%, transparent 75%);
  -webkit-mask-image: radial-gradient(120% 80% at 30% 20%, #000 0%, transparent 75%);
  pointer-events: none;
}

.login-aside__inner {
  position: relative;
  z-index: 1;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--space-10);
}

.login-brand {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
}

.login-brand__logo {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.28);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  font-size: var(--text-xl);
  font-weight: var(--fw-bold);
  text-transform: uppercase;
}

.login-brand__text {
  display: inline-flex;
  align-items: baseline;
  gap: var(--space-1);
  font-size: var(--text-2xl);
  font-weight: var(--fw-bold);
  letter-spacing: -0.01em;
}

.login-brand__secondary {
  opacity: 0.65;
  font-weight: var(--fw-medium);
}

.login-aside__hero {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  max-width: 420px;
}

.login-eyebrow {
  align-self: flex-start;
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.22);
  font-size: var(--text-sm);
  font-weight: var(--fw-bold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.login-aside__hero h1 {
  margin: 0;
  font-size: clamp(1.9rem, 2.6vw, 2.7rem);
  line-height: var(--leading-tight);
  font-weight: var(--fw-bold);
}

.login-aside__hero p {
  margin: 0;
  max-width: 360px;
  line-height: var(--leading-relaxed);
  color: rgba(255, 255, 255, 0.82);
}

.login-features {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.login-feature {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
}

.login-feature__icon {
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  font-size: var(--text-lg);
}

.login-feature__body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.login-feature__title {
  font-weight: var(--fw-semibold);
}

.login-feature__hint {
  font-size: var(--text-sm);
  line-height: var(--leading-normal);
  color: rgba(255, 255, 255, 0.72);
}

.login-aside__foot {
  margin-top: auto;
  font-size: var(--text-sm);
  color: rgba(255, 255, 255, 0.7);
}

/* ---------- Right panel ---------- */
.login-main {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-10);
  background: linear-gradient(180deg, var(--color-surface) 0%, var(--color-surface-2) 100%);
}

.login-card-glass {
  width: 100%;
  max-width: 440px;
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  padding: var(--space-10);
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border);
  background: var(--color-surface-overlay);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  box-shadow: var(--shadow-lg);
}

.login-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  align-self: flex-start;
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-pill);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: var(--text-sm);
  font-weight: var(--fw-bold);
}

.login-badge__dot {
  width: 7px;
  height: 7px;
  border-radius: var(--radius-pill);
  background: var(--color-primary);
}

.login-head {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.login-title {
  margin: 0;
  font-size: var(--text-3xl);
  line-height: var(--leading-tight);
  font-weight: var(--fw-bold);
  color: var(--color-text-strong);
}

.login-copy {
  margin: 0;
  color: var(--color-text-muted);
  line-height: var(--leading-relaxed);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.login-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.login-field__label {
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  color: var(--color-text-muted);
}

/* Password input — mirrors UiInput "lg" */
.login-password {
  position: relative;
}

.login-password__lead {
  position: absolute;
  top: 50%;
  left: var(--space-4);
  transform: translateY(-50%);
  color: var(--color-text-subtle);
  font-size: var(--text-md);
  pointer-events: none;
}

.login-password__input {
  width: 100%;
  min-height: 44px;
  padding: var(--space-3) calc(var(--space-4) + 26px) var(--space-3) calc(var(--space-4) + 26px);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  box-shadow: var(--shadow-xs);
  font: inherit;
  transition: border-color var(--dur-fast) var(--ease-out), box-shadow var(--dur-fast) var(--ease-out);
}

.login-password__input::placeholder {
  color: var(--color-text-subtle);
}

.login-password__input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}

.login-password__toggle {
  position: absolute;
  top: 50%;
  right: var(--space-3);
  transform: translateY(-50%);
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-xs);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: color var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out);
}

.login-password__toggle:hover {
  color: var(--color-text-strong);
  background: var(--color-surface-2);
}

.login-password__toggle:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

/* Info blocks */
.login-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-2);
}

.login-info__title {
  font-size: var(--text-md);
  font-weight: var(--fw-bold);
  color: var(--color-text-strong);
}

.login-info__subtitle {
  color: var(--color-text-muted);
  line-height: var(--leading-normal);
}

/* Active account */
.login-account {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-2);
}

.login-account__avatar {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: var(--radius-pill);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-weight: var(--fw-bold);
  text-transform: uppercase;
}

.login-account__body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.login-account__name {
  font-weight: var(--fw-semibold);
  color: var(--color-text-strong);
}

.login-account__mail {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 2FA setup */
.login-setup {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: var(--space-5);
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-2);
}

.login-setup__qr {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: #ffffff;
  border: 1px solid var(--color-border);
}

.login-setup__qr img {
  display: block;
  width: 100%;
  max-width: 200px;
  border-radius: var(--radius-sm);
}

.login-setup__meta {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  align-items: flex-start;
}

.login-secret {
  display: block;
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-text-strong);
  font-family: var(--font-mono);
  font-size: var(--text-base);
  word-break: break-all;
}

.login-codes {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-2);
  margin-top: var(--space-2);
}

.login-codes code {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  font-family: var(--font-mono);
  font-size: var(--text-base);
  text-align: center;
}

/* Alert */
.login-alert {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-danger-soft);
  border: 1px solid color-mix(in srgb, var(--color-danger) 30%, transparent);
  color: var(--color-danger);
  line-height: var(--leading-normal);
}

.login-alert i {
  margin-top: 2px;
}

/* Actions */
.login-actions {
  display: flex;
  gap: var(--space-3);
}

.login-submit {
  flex: 1 1 auto;
}

.login-secondary {
  flex: 0 0 auto;
  min-width: 132px;
}

.login-impersonation {
  gap: var(--space-3);
}

/* ---------- Responsive ---------- */
@media (max-width: 1080px) {
  .login-shell {
    grid-template-columns: 1fr;
    min-height: 0;
  }

  .login-aside {
    padding: var(--space-8);
  }

  .login-aside__inner {
    gap: var(--space-6);
  }

  .login-features,
  .login-aside__foot {
    display: none;
  }

  .login-main {
    padding: var(--space-8);
  }
}

@media (max-width: 640px) {
  .login-aside {
    padding: var(--space-6);
  }

  .login-aside__hero h1 {
    font-size: clamp(1.6rem, 6vw, 2rem);
  }

  .login-card-glass {
    padding: var(--space-6);
  }

  .login-setup {
    grid-template-columns: 1fr;
  }

  .login-codes {
    grid-template-columns: 1fr;
  }

  .login-actions {
    flex-direction: column;
  }

  .login-secondary {
    flex: 1 1 auto;
  }
}

@media (prefers-reduced-motion: reduce) {
  .login-password__input,
  .login-password__toggle {
    transition: none;
  }
}
</style>
