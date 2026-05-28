<template>
  <div v-if="modelValue" class="two-factor-modal" @click.self="close">
    <div class="two-factor-modal__dialog">
      <div class="two-factor-modal__header">
        <div>
          <div class="two-factor-modal__eyebrow">Безопасность</div>
          <h3>Двухфакторная аутентификация</h3>
        </div>
        <button type="button" class="two-factor-modal__close" @click="close">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div class="two-factor-modal__body">
        <div v-if="loadingStatus" class="two-factor-modal__state">
          <i class="fas fa-spinner fa-spin"></i>
          <span>Загружаю состояние 2FA...</span>
        </div>

        <template v-else>
          <div class="two-factor-summary">
            <div class="two-factor-summary__item">
              <span class="two-factor-summary__label">Пользователь</span>
              <strong>{{ auth.user?.email || '—' }}</strong>
            </div>
            <div class="two-factor-summary__item">
              <span class="two-factor-summary__label">Статус</span>
              <strong :class="status?.enabled ? 'text-success' : 'text-muted'">
                {{ status?.enabled ? 'Включена' : 'Выключена' }}
              </strong>
            </div>
            <div class="two-factor-summary__item">
              <span class="two-factor-summary__label">Резервных кодов</span>
              <strong>{{ status?.backup_codes_remaining ?? 0 }}</strong>
            </div>
          </div>

          <div v-if="error" class="two-factor-alert two-factor-alert--danger">
            {{ error }}
          </div>

          <div v-if="!status?.enabled && !setupSecret" class="two-factor-empty">
            <div class="two-factor-empty__icon">
              <i class="fas fa-shield-halved"></i>
            </div>
            <div class="two-factor-empty__content">
              <h4>Защитите вход TOTP-кодом</h4>
              <p>
                После включения 2FA система будет запрашивать код из
                приложения-аутентификатора после ввода пароля.
              </p>
            </div>
            <button type="button" class="btn btn-primary" :disabled="busy" @click="beginSetup">
              <i class="fas fa-qrcode mr-1"></i> Настроить 2FA
            </button>
          </div>

          <template v-else-if="setupSecret">
            <div class="two-factor-setup">
              <div class="two-factor-setup__qr">
                <img v-if="qrDataUrl" :src="qrDataUrl" alt="QR-код 2FA" />
              </div>
              <div class="two-factor-setup__content">
                <h4>Сканируйте QR-код</h4>
                <p>
                  Откройте Google Authenticator, Microsoft Authenticator,
                  1Password или другое TOTP-приложение и добавьте новую запись.
                </p>
                <div class="two-factor-code-block">
                  <span class="two-factor-code-block__label">Резервный ручной ключ</span>
                  <code>{{ setupSecret }}</code>
                  <button type="button" class="btn btn-sm btn-outline-secondary" @click="copyText(setupSecret, 'Секрет 2FA скопирован')">
                    <i class="far fa-copy mr-1"></i> Копировать
                  </button>
                </div>
                <label class="two-factor-field">
                  <span>Код из приложения</span>
                  <input
                    v-model="setupCode"
                    type="text"
                    inputmode="numeric"
                    maxlength="6"
                    class="form-control"
                    placeholder="123456"
                  />
                </label>
                <div class="two-factor-actions">
                  <button type="button" class="btn btn-primary" :disabled="busy" @click="confirmSetup">
                    <i class="fas" :class="busy ? 'fa-spinner fa-spin' : 'fa-check'"></i>
                    <span>{{ busy ? 'Подтверждение...' : 'Подтвердить и включить' }}</span>
                  </button>
                  <button type="button" class="btn btn-outline-secondary" :disabled="busy" @click="resetSetup">
                    Отмена
                  </button>
                </div>
              </div>
            </div>
          </template>

          <template v-else>
            <div class="two-factor-grid">
              <div class="two-factor-card">
                <h4>Активная защита</h4>
                <p>
                  Вход подтверждается TOTP-кодом после проверки пароля.
                </p>
                <div class="two-factor-chip-row">
                  <span class="two-factor-chip two-factor-chip--success">2FA включена</span>
                  <span v-if="status?.enabled_at" class="two-factor-chip">
                    С {{ formatDateTime(status.enabled_at) }}
                  </span>
                </div>
              </div>

              <div class="two-factor-card">
                <h4>Резервные коды</h4>
                <p>
                  Используйте их, если устройство с приложением временно недоступно.
                </p>
                <label class="two-factor-field">
                  <span>Текущий код из приложения</span>
                  <input
                    v-model="regenCode"
                    type="text"
                    inputmode="numeric"
                    maxlength="6"
                    class="form-control"
                    placeholder="123456"
                  />
                </label>
                <button type="button" class="btn btn-outline-primary" :disabled="busy" @click="regenerateBackupCodes">
                  <i class="fas" :class="busy ? 'fa-spinner fa-spin' : 'fa-rotate'"></i>
                  <span>{{ busy ? 'Генерация...' : 'Сгенерировать заново' }}</span>
                </button>
              </div>

              <div class="two-factor-card">
                <h4>Политика безопасности</h4>
                <p>
                  Двухфакторная аутентификация обязательна для всех пользователей системы.
                  Отключение недоступно.
                </p>
                <div class="two-factor-chip-row">
                  <span class="two-factor-chip two-factor-chip--success">2FA обязательна</span>
                </div>
              </div>
            </div>
          </template>

          <div v-if="backupCodes.length" class="two-factor-backup">
            <div class="two-factor-backup__header">
              <div>
                <h4>Резервные коды</h4>
                <p>Сохраните их в безопасном месте. Каждый код используется только один раз.</p>
              </div>
              <button type="button" class="btn btn-sm btn-outline-secondary" @click="copyText(backupCodes.join('\n'), 'Резервные коды скопированы')">
                <i class="far fa-copy mr-1"></i> Копировать все
              </button>
            </div>
            <div class="two-factor-backup__grid">
              <code v-for="code in backupCodes" :key="code">{{ code }}</code>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import QRCode from 'qrcode'
import { useAuthStore } from '../../stores/auth'
import { useToast } from '../../composables/useToast'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const auth = useAuthStore()
const { success: toastSuccess, error: toastError } = useToast()

const loadingStatus = ref(false)
const busy = ref(false)
const error = ref('')
const status = ref(null)
const setupSecret = ref('')
const setupCode = ref('')
const regenCode = ref('')
const disablePassword = ref('')
const backupCodes = ref([])
const qrDataUrl = ref('')

const close = () => emit('update:modelValue', false)

const formatDateTime = (value) => {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString('ru-RU')
}

const resetSetup = () => {
  setupSecret.value = ''
  setupCode.value = ''
  qrDataUrl.value = ''
  error.value = ''
}

const loadStatus = async () => {
  loadingStatus.value = true
  error.value = ''
  try {
    status.value = await auth.fetchTwoFactorStatus()
  } catch (err) {
    // Don't render a misleading "Выключена / Настроить 2FA" when the live
    // status call hiccups (e.g. right after the mandatory login-time setup
    // + session refresh). Fall back to the authoritative session flag so a
    // user whose 2FA is actually enabled isn't told it's off.
    status.value = {
      enabled: !!auth.user?.two_factor_enabled,
      enabled_at: auth.user?.two_factor_enabled_at || null,
      backup_codes_remaining: null
    }
    if (!auth.user?.two_factor_enabled) {
      error.value = err?.response?.data?.detail || 'Не удалось загрузить настройки 2FA'
    }
  } finally {
    loadingStatus.value = false
  }
}

const copyText = async (text, message) => {
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = text
      textarea.setAttribute('readonly', 'readonly')
      textarea.style.position = 'absolute'
      textarea.style.left = '-9999px'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    toastSuccess(message)
  } catch (err) {
    toastError('Не удалось скопировать данные')
  }
}

const beginSetup = async () => {
  busy.value = true
  error.value = ''
  try {
    const data = await auth.startTwoFactorSetup()
    setupSecret.value = data.secret
    setupCode.value = ''
    backupCodes.value = []
    qrDataUrl.value = await QRCode.toDataURL(data.otpauth_url, {
      width: 220,
      margin: 1
    })
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Не удалось начать настройку 2FA'
  } finally {
    busy.value = false
  }
}

const confirmSetup = async () => {
  if (!setupSecret.value || !setupCode.value.trim()) {
    error.value = 'Введите код из приложения-аутентификатора'
    return
  }
  busy.value = true
  error.value = ''
  try {
    const data = await auth.confirmTwoFactorSetup(setupSecret.value, setupCode.value.trim())
    status.value = {
      enabled: true,
      enabled_at: data.enabled_at,
      backup_codes_remaining: data.backup_codes_remaining
    }
    backupCodes.value = data.backup_codes || []
    resetSetup()
    toastSuccess('Двухфакторная аутентификация включена')
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Не удалось подтвердить настройку 2FA'
  } finally {
    busy.value = false
  }
}

const regenerateBackupCodes = async () => {
  if (!regenCode.value.trim()) {
    error.value = 'Введите текущий 2FA-код для генерации новых backup codes'
    return
  }
  busy.value = true
  error.value = ''
  try {
    const data = await auth.regenerateTwoFactorBackupCodes(regenCode.value.trim())
    status.value = {
      enabled: true,
      enabled_at: data.enabled_at,
      backup_codes_remaining: data.backup_codes_remaining
    }
    backupCodes.value = data.backup_codes || []
    regenCode.value = ''
    toastSuccess('Новые резервные коды созданы')
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Не удалось создать новые резервные коды'
  } finally {
    busy.value = false
  }
}

const disableTwoFactor = async () => {
  if (!disablePassword.value.trim()) {
    error.value = 'Введите текущий пароль'
    return
  }
  busy.value = true
  error.value = ''
  try {
    const data = await auth.disableTwoFactor(disablePassword.value)
    status.value = data
    backupCodes.value = []
    disablePassword.value = ''
    toastSuccess('Двухфакторная аутентификация отключена')
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Не удалось отключить 2FA'
  } finally {
    busy.value = false
  }
}

watch(
  () => props.modelValue,
  async (value) => {
    if (!value) return
    resetSetup()
    backupCodes.value = []
    regenCode.value = ''
    disablePassword.value = ''
    await loadStatus()
  }
)
</script>

<style scoped>
.two-factor-modal {
  position: fixed;
  inset: 0;
  z-index: 2400;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(10, 22, 41, 0.42);
  backdrop-filter: blur(10px);
}

.two-factor-modal__dialog {
  width: min(820px, 100%);
  max-height: calc(100vh - 48px);
  overflow: auto;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(216, 224, 240, 0.9);
  border-radius: 24px;
  box-shadow: 0 20px 70px rgba(10, 22, 41, 0.18);
}

[data-theme='dark'] .two-factor-modal__dialog {
  background: rgba(23, 31, 44, 0.96);
  border-color: rgba(74, 85, 104, 0.9);
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.45);
}

.two-factor-modal__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 24px 28px 18px;
  border-bottom: 1px solid rgba(216, 224, 240, 0.9);
}

[data-theme='dark'] .two-factor-modal__header {
  border-bottom-color: rgba(74, 85, 104, 0.9);
}

.two-factor-modal__eyebrow {
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #7d8592;
}

.two-factor-modal__header h3 {
  margin: 8px 0 0;
  font-size: 1.5rem;
  color: #0a1629;
}

[data-theme='dark'] .two-factor-modal__header h3 {
  color: #f3f6fb;
}

.two-factor-modal__close {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 12px;
  background: #f4f7fb;
  color: #53627c;
}

[data-theme='dark'] .two-factor-modal__close {
  background: rgba(255, 255, 255, 0.08);
  color: #d7dfeb;
}

.two-factor-modal__body {
  padding: 24px 28px 28px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.two-factor-modal__state {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: #7d8592;
}

.two-factor-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.two-factor-summary__item {
  padding: 16px;
  border-radius: 16px;
  background: #f7faff;
  border: 1px solid rgba(216, 224, 240, 0.8);
}

[data-theme='dark'] .two-factor-summary__item {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(74, 85, 104, 0.7);
}

.two-factor-summary__label {
  display: block;
  margin-bottom: 8px;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #7d8592;
}

.two-factor-alert {
  padding: 14px 16px;
  border-radius: 14px;
  font-size: 0.92rem;
}

.two-factor-alert--danger {
  background: rgba(220, 53, 69, 0.08);
  border: 1px solid rgba(220, 53, 69, 0.18);
  color: #b4232c;
}

.two-factor-empty,
.two-factor-setup,
.two-factor-card {
  border: 1px solid rgba(216, 224, 240, 0.9);
  border-radius: 20px;
  background: #fbfdff;
}

[data-theme='dark'] .two-factor-empty,
[data-theme='dark'] .two-factor-setup,
[data-theme='dark'] .two-factor-card {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(74, 85, 104, 0.85);
}

.two-factor-empty {
  padding: 22px;
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 18px;
  align-items: center;
}

.two-factor-empty__icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: rgba(63, 140, 255, 0.12);
  color: #3f8cff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
}

.two-factor-empty__content h4,
.two-factor-setup__content h4,
.two-factor-card h4,
.two-factor-backup__header h4 {
  margin: 0 0 8px;
  color: #0a1629;
}

[data-theme='dark'] .two-factor-empty__content h4,
[data-theme='dark'] .two-factor-setup__content h4,
[data-theme='dark'] .two-factor-card h4,
[data-theme='dark'] .two-factor-backup__header h4 {
  color: #f3f6fb;
}

.two-factor-empty__content p,
.two-factor-setup__content p,
.two-factor-card p,
.two-factor-backup__header p {
  margin: 0;
  color: #6d7c91;
  line-height: 1.6;
}

[data-theme='dark'] .two-factor-empty__content p,
[data-theme='dark'] .two-factor-setup__content p,
[data-theme='dark'] .two-factor-card p,
[data-theme='dark'] .two-factor-backup__header p {
  color: #a7b3c6;
}

.two-factor-setup {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 22px;
  padding: 22px;
}

.two-factor-setup__qr {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 240px;
  border-radius: 18px;
  background: #ffffff;
  border: 1px dashed rgba(63, 140, 255, 0.35);
}

.two-factor-setup__qr img {
  max-width: 220px;
  width: 100%;
  height: auto;
}

.two-factor-setup__content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.two-factor-code-block {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px 12px;
  padding: 14px 16px;
  border-radius: 14px;
  background: #f3f7fc;
}

[data-theme='dark'] .two-factor-code-block {
  background: rgba(255, 255, 255, 0.06);
}

.two-factor-code-block__label {
  width: 100%;
  color: #7d8592;
  font-size: 0.82rem;
  font-weight: 700;
}

.two-factor-code-block code,
.two-factor-backup__grid code {
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(63, 140, 255, 0.08);
  color: #12499a;
  font-size: 0.96rem;
  font-weight: 700;
}

.two-factor-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.two-factor-field span {
  color: #6d7c91;
  font-weight: 700;
  font-size: 0.9rem;
}

.two-factor-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.two-factor-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.two-factor-card {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.two-factor-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.two-factor-chip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  background: #eff4fa;
  color: #5d6d86;
  font-size: 0.82rem;
  font-weight: 700;
}

.two-factor-chip--success {
  background: rgba(41, 204, 106, 0.12);
  color: #1d8c4f;
}

.two-factor-backup {
  padding: 18px;
  border-radius: 18px;
  background: #f9fbff;
  border: 1px solid rgba(216, 224, 240, 0.9);
}

[data-theme='dark'] .two-factor-backup {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(74, 85, 104, 0.85);
}

.two-factor-backup__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 16px;
}

.two-factor-backup__grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 900px) {
  .two-factor-summary,
  .two-factor-grid {
    grid-template-columns: 1fr;
  }

  .two-factor-empty,
  .two-factor-setup {
    grid-template-columns: 1fr;
  }

  .two-factor-backup__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 620px) {
  .two-factor-modal {
    padding: 14px;
  }

  .two-factor-modal__dialog {
    max-height: calc(100vh - 28px);
  }

  .two-factor-modal__header,
  .two-factor-modal__body {
    padding-left: 18px;
    padding-right: 18px;
  }

  .two-factor-backup__header {
    flex-direction: column;
  }

  .two-factor-backup__grid {
    grid-template-columns: 1fr;
  }
}
</style>
