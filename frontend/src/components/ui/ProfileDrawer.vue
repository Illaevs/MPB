<template>
  <UiDrawer
    :model-value="modelValue"
    size="lg"
    side="right"
    :closable="true"
    @update:model-value="onUpdate"
  >
    <template #header>
      <div class="pd-header">
        <h3>{{ editing ? 'Редактирование профиля' : 'Профиль' }}</h3>
        <button
          v-if="!editing && profile && canSelfEdit"
          type="button"
          class="pd-iconbtn"
          title="Редактировать"
          @click="enterEdit"
        >
          <i class="fas fa-pen"></i>
        </button>
      </div>
    </template>

    <div v-if="loading" class="pd-state"><UiSpinner /></div>

    <div v-else-if="!profile" class="pd-state pd-state--error">
      Не удалось загрузить профиль.
    </div>

    <div v-else class="pd">
      <!-- HERO -->
      <section class="pd-hero">
        <div class="pd-hero__avatar">
          <UiAvatar
            :src="profile.avatar_url"
            :name="profile.full_name"
            size="2xl"
          />
          <span v-if="currentAbsence" class="pd-hero__avatar-status" :class="`is-${currentAbsence.type}`" :title="absenceLabel(currentAbsence.type)">
            <i class="fas" :class="absenceIconClass(currentAbsence.type)"></i>
          </span>
        </div>
        <div class="pd-hero__meta">
          <div class="pd-hero__name">{{ profile.full_name || '—' }}</div>
          <div class="pd-hero__title">
            <span v-if="profile.job_title">{{ profile.job_title }}</span>
            <template v-if="profile.job_title && profile.department"> · </template>
            <span v-if="profile.department">{{ profile.department }}</span>
            <span v-if="!profile.job_title && !profile.department" class="muted">Должность не указана</span>
          </div>
          <div class="pd-hero__role">
            <i class="fas fa-shield-alt"></i>
            <span>{{ profile.role_name || 'Роль не назначена' }}</span>
          </div>
        </div>
      </section>

      <!-- Бейдж текущего отсутствия -->
      <div
        v-if="currentAbsence"
        class="pd-absence"
        :class="`is-${currentAbsence.type}`"
      >
        <i class="fas" :class="absenceIconClass(currentAbsence.type)"></i>
        <div class="pd-absence__text">
          <strong>{{ absenceLabel(currentAbsence.type) }}</strong>
          до {{ formatDate(currentAbsence.date_to) }}
          <div v-if="currentAbsence.comment" class="pd-absence__comment">
            {{ currentAbsence.comment }}
          </div>
        </div>
      </div>

      <!-- КОНТАКТЫ -->
      <section class="pd-section">
        <h4 class="pd-section__title">
          <i class="fas fa-address-card"></i>
          Контакты
        </h4>
        <div class="pd-rows">
          <div class="pd-row">
            <i class="far fa-envelope pd-row__icon"></i>
            <div class="pd-row__label">Email</div>
            <div class="pd-row__value">{{ profile.email || '—' }}</div>
          </div>
          <div class="pd-row">
            <i class="fab fa-telegram pd-row__icon"></i>
            <div class="pd-row__label">Telegram</div>
            <div class="pd-row__value">
              <template v-if="editing">
                <div class="pd-tg-input">
                  <span>@</span>
                  <input
                    type="text"
                    v-model="form.telegram_username"
                    maxlength="64"
                    placeholder="username"
                    class="pd-input"
                  />
                </div>
              </template>
              <template v-else-if="profile.telegram_username">
                <a :href="`https://t.me/${profile.telegram_username}`" target="_blank" rel="noopener">
                  @{{ profile.telegram_username }}
                </a>
              </template>
              <template v-else><span class="muted">не указано</span></template>
            </div>
          </div>
        </div>
      </section>

      <!-- РАБОТА -->
      <section class="pd-section">
        <h4 class="pd-section__title">
          <i class="fas fa-briefcase"></i>
          Работа
        </h4>
        <div class="pd-rows">
          <div class="pd-row">
            <i class="fas fa-id-badge pd-row__icon"></i>
            <div class="pd-row__label">Должность</div>
            <div class="pd-row__value">
              <input
                v-if="editing"
                type="text"
                v-model="form.job_title"
                :disabled="!canEditFormal"
                :placeholder="canEditFormal ? 'Например: ГИП' : 'правит администратор'"
                maxlength="255"
                class="pd-input"
              />
              <template v-else>
                {{ profile.job_title || (canEditFormal ? '—' : 'не указано') }}
              </template>
            </div>
          </div>
          <div class="pd-row">
            <i class="fas fa-sitemap pd-row__icon"></i>
            <div class="pd-row__label">Отдел</div>
            <div class="pd-row__value">
              <input
                v-if="editing"
                type="text"
                v-model="form.department"
                :disabled="!canEditFormal"
                :placeholder="canEditFormal ? 'Например: ПИР' : 'правит администратор'"
                maxlength="255"
                class="pd-input"
              />
              <template v-else>
                {{ profile.department || (canEditFormal ? '—' : 'не указано') }}
              </template>
            </div>
          </div>
          <div class="pd-row">
            <i class="fas fa-user-tie pd-row__icon"></i>
            <div class="pd-row__label">Руководитель</div>
            <div class="pd-row__value">
              <select
                v-if="editing && canEditFormal"
                v-model="form.manager_id"
                class="pd-input"
              >
                <option :value="null">— не назначен —</option>
                <option v-for="u in managerOptions" :key="u.id" :value="u.id">{{ u.full_name || u.email }}</option>
              </select>
              <template v-else>
                {{ profile.manager_full_name || (canEditFormal ? '—' : 'не указано') }}
              </template>
            </div>
          </div>
          <div class="pd-row">
            <i class="fas fa-calendar-check pd-row__icon"></i>
            <div class="pd-row__label">В компании с</div>
            <div class="pd-row__value">
              <input
                v-if="editing"
                type="date"
                v-model="form.hire_date"
                :disabled="!canEditFormal"
                class="pd-input"
              />
              <template v-else-if="profile.hire_date">
                {{ formatDate(profile.hire_date) }}
                <span class="pd-row__hint">{{ tenureLabel(profile.hire_date) }}</span>
              </template>
              <template v-else>—</template>
            </div>
          </div>
        </div>
      </section>

      <!-- ЛИЧНОЕ -->
      <section class="pd-section">
        <h4 class="pd-section__title">
          <i class="fas fa-user-circle"></i>
          Личное
        </h4>
        <div class="pd-rows">
          <div class="pd-row">
            <i class="fas fa-birthday-cake pd-row__icon"></i>
            <div class="pd-row__label">День рождения</div>
            <div class="pd-row__value">
              <div v-if="editing" class="pd-birth-edit">
                <input
                  type="date"
                  v-model="form.birth_date"
                  class="pd-input"
                />
                <label class="pd-check">
                  <input type="checkbox" v-model="form.birth_show_year" />
                  <span>показывать год</span>
                </label>
              </div>
              <template v-else-if="profile.birth_date">{{ formatBirth(profile.birth_date) }}</template>
              <template v-else><span class="muted">не указано</span></template>
            </div>
          </div>
          <div class="pd-row pd-row--block">
            <i class="fas fa-quote-left pd-row__icon"></i>
            <div class="pd-row__label">О себе</div>
            <div class="pd-row__value pd-row__value--bio">
              <textarea
                v-if="editing"
                v-model="form.bio"
                rows="3"
                maxlength="4000"
                class="pd-input pd-textarea"
                placeholder="Коротко: чем интересен, на чём специализируешься, что предпочитаешь по задачам…"
              ></textarea>
              <template v-else>
                <div v-if="profile.bio" class="pd-bio">{{ profile.bio }}</div>
                <span v-else class="muted">не заполнено</span>
              </template>
            </div>
          </div>
        </div>
      </section>

      <!-- КОМПЕТЕНЦИИ -->
      <section class="pd-section">
        <h4 class="pd-section__title">
          <i class="fas fa-tags"></i>
          Компетенции
        </h4>

        <div class="pd-chips-block">
          <div class="pd-chips-block__label">Навыки</div>
          <UiChipInput
            v-if="editing"
            v-model="form.skills"
            placeholder="Добавь навык и нажми Enter…"
          />
          <div v-else class="pd-chips">
            <span
              v-for="s in (profile.skills || [])"
              :key="`sk-${s}`"
              class="pd-chip is-skill"
            >{{ s }}</span>
            <span v-if="!(profile.skills || []).length" class="muted">пока пусто</span>
          </div>
          <div v-if="editing && skillSuggestions.length" class="pd-suggestions">
            <span class="pd-suggestions__label">часто:</span>
            <button
              v-for="s in skillSuggestions"
              :key="`sks-${s}`"
              type="button"
              class="pd-suggest"
              :disabled="(form.skills || []).includes(s)"
              @click="addChip('skills', s)"
            >{{ s }}</button>
          </div>
        </div>

        <div class="pd-chips-block">
          <div class="pd-chips-block__label">Интересы</div>
          <UiChipInput
            v-if="editing"
            v-model="form.interests"
            placeholder="Добавь интерес и нажми Enter…"
          />
          <div v-else class="pd-chips">
            <span
              v-for="s in (profile.interests || [])"
              :key="`in-${s}`"
              class="pd-chip is-interest"
            >{{ s }}</span>
            <span v-if="!(profile.interests || []).length" class="muted">пока пусто</span>
          </div>
          <div v-if="editing && interestSuggestions.length" class="pd-suggestions">
            <span class="pd-suggestions__label">часто:</span>
            <button
              v-for="s in interestSuggestions"
              :key="`ins-${s}`"
              type="button"
              class="pd-suggest"
              :disabled="(form.interests || []).includes(s)"
              @click="addChip('interests', s)"
            >{{ s }}</button>
          </div>
        </div>
      </section>
    </div>

    <template #footer>
      <template v-if="editing">
        <UiButton variant="ghost" size="sm" :disabled="saving" @click="cancelEdit">
          Отмена
        </UiButton>
        <UiButton
          variant="primary"
          size="sm"
          icon-left="fas fa-check"
          :loading="saving"
          @click="save"
        >
          Сохранить
        </UiButton>
      </template>
      <template v-else>
        <UiButton variant="ghost" size="sm" icon-left="fas fa-sign-out-alt" @click="onLogout">
          Выйти
        </UiButton>
      </template>
    </template>
  </UiDrawer>
</template>

<script>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../../services/api'
import { useToast } from '../../composables/useToast'
import { useAuthStore } from '../../stores/auth'
import UiDrawer from './UiDrawer.vue'
import UiAvatar from './UiAvatar.vue'
import UiButton from './UiButton.vue'
import UiSpinner from './UiSpinner.vue'
import UiChipInput from './UiChipInput.vue'

const ABSENCE_LABEL = {
  vacation: 'Отпуск',
  sick_leave: 'Больничный',
  business_trip: 'Командировка',
  other: 'Отсутствует',
}
const ABSENCE_ICON = {
  vacation: 'fa-umbrella-beach',
  sick_leave: 'fa-briefcase-medical',
  business_trip: 'fa-plane-departure',
  other: 'fa-clock',
}

function emptyForm() {
  return {
    birth_date: null,
    birth_show_year: true,
    bio: '',
    interests: [],
    skills: [],
    telegram_username: '',
    job_title: '',
    department: '',
    manager_id: null,
    hire_date: null,
  }
}

function toDateInput(value) {
  if (!value) return null
  const d = new Date(value)
  if (!Number.isFinite(d.getTime())) return null
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${dd}`
}

function fromProfile(p) {
  const f = emptyForm()
  if (!p) return f
  f.birth_date = toDateInput(p.birth_date)
  f.birth_show_year = p.birth_show_year !== false
  f.bio = p.bio || ''
  f.interests = Array.isArray(p.interests) ? [...p.interests] : []
  f.skills = Array.isArray(p.skills) ? [...p.skills] : []
  f.telegram_username = p.telegram_username || ''
  f.job_title = p.job_title || ''
  f.department = p.department || ''
  f.manager_id = p.manager_id || null
  f.hire_date = toDateInput(p.hire_date)
  return f
}

export default {
  name: 'ProfileDrawer',
  components: { UiDrawer, UiAvatar, UiButton, UiSpinner, UiChipInput },
  props: {
    modelValue: { type: Boolean, default: false },
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const router = useRouter()
    const auth = useAuthStore()
    const { success, error: toastError } = useToast()

    const loading = ref(false)
    const saving = ref(false)
    const editing = ref(false)
    const profile = ref(null)
    const form = ref(emptyForm())
    const skillSuggestions = ref([])
    const interestSuggestions = ref([])
    const managerOptions = ref([])
    const currentAbsence = ref(null)

    const canSelfEdit = computed(() => true) // личные поля всегда правит сам
    const canEditFormal = computed(() => {
      const u = auth.permissions?.users || {}
      return Boolean(u.edit_all) || auth.isSuperuser
    })

    const formatDate = (iso) => {
      if (!iso) return ''
      try {
        const d = new Date(iso)
        if (!Number.isFinite(d.getTime())) return ''
        return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
      } catch { return '' }
    }

    const formatBirth = (iso) => {
      if (!iso) return ''
      const d = new Date(iso)
      if (!Number.isFinite(d.getTime())) return iso
      // Бэк подменяет год на 1900, если пользователь скрыл его.
      if (d.getFullYear() < 1901) {
        return d.toLocaleDateString('ru-RU', { day: '2-digit', month: 'long' })
      }
      return d.toLocaleDateString('ru-RU', { day: '2-digit', month: 'long', year: 'numeric' })
    }

    const tenureLabel = (iso) => {
      const d = new Date(iso)
      if (!Number.isFinite(d.getTime())) return ''
      const now = new Date()
      let years = now.getFullYear() - d.getFullYear()
      const m = now.getMonth() - d.getMonth()
      if (m < 0 || (m === 0 && now.getDate() < d.getDate())) years -= 1
      if (years < 1) {
        const months = Math.max(0, (now.getFullYear() - d.getFullYear()) * 12 + (now.getMonth() - d.getMonth()))
        if (months < 1) return '· меньше месяца'
        return `· ${months} мес.`
      }
      const lastTwo = years % 100
      const last = years % 10
      let word = 'лет'
      if (lastTwo < 11 || lastTwo > 14) {
        if (last === 1) word = 'год'
        else if (last >= 2 && last <= 4) word = 'года'
      }
      return `· ${years} ${word}`
    }

    const absenceLabel = (t) => ABSENCE_LABEL[t] || ABSENCE_LABEL.other
    const absenceIconClass = (t) => ABSENCE_ICON[t] || ABSENCE_ICON.other

    const load = async () => {
      loading.value = true
      try {
        const [p, abs, sk, it] = await Promise.all([
          api.profiles.getMe(),
          api.absences.list({}).catch(() => []),
          api.profiles.suggest('skills', '', 12).catch(() => []),
          api.profiles.suggest('interests', '', 12).catch(() => []),
        ])
        profile.value = p
        form.value = fromProfile(p)
        skillSuggestions.value = sk || []
        interestSuggestions.value = it || []
        // Текущее отсутствие — пересекающее сегодня.
        const today = new Date(); today.setHours(0, 0, 0, 0)
        const ms = today.getTime()
        currentAbsence.value = (abs || []).find((a) => {
          if (a.user_id !== auth.user?.id) return false
          const from = new Date(a.date_from); from.setHours(0, 0, 0, 0)
          const to = new Date(a.date_to); to.setHours(23, 59, 59, 999)
          return from.getTime() <= ms && ms <= to.getTime()
        }) || null
        // Список юзеров для селекта «руководитель» нужен только админу.
        if (canEditFormal.value && !managerOptions.value.length) {
          try {
            const all = await api.users.list({ limit: 500 })
            const items = all?.items || all || []
            managerOptions.value = items.filter((u) => u.id !== auth.user?.id)
          } catch {
            managerOptions.value = []
          }
        }
      } catch (e) {
        profile.value = null
      } finally {
        loading.value = false
      }
    }

    const addChip = (field, value) => {
      const cur = Array.isArray(form.value[field]) ? form.value[field] : []
      if (cur.includes(value)) return
      form.value[field] = [...cur, value]
    }

    const enterEdit = () => {
      // Освежим форму со снэпшота профиля.
      form.value = fromProfile(profile.value)
      editing.value = true
    }
    const cancelEdit = () => {
      form.value = fromProfile(profile.value)
      editing.value = false
    }

    const buildSelfPayload = () => ({
      birth_date: form.value.birth_date || null,
      birth_show_year: !!form.value.birth_show_year,
      bio: (form.value.bio || '').trim() || null,
      interests: form.value.interests || [],
      skills: form.value.skills || [],
      telegram_username: (form.value.telegram_username || '').trim() || null,
    })
    const buildAdminPayload = () => ({
      ...buildSelfPayload(),
      job_title: (form.value.job_title || '').trim() || null,
      department: (form.value.department || '').trim() || null,
      manager_id: form.value.manager_id || null,
      hire_date: form.value.hire_date || null,
    })

    const save = async () => {
      if (saving.value) return
      saving.value = true
      try {
        if (canEditFormal.value) {
          await api.profiles.patchUser(auth.user.id, buildAdminPayload())
        } else {
          await api.profiles.patchMe(buildSelfPayload())
        }
        success('Профиль обновлён')
        editing.value = false
        await load()
      } catch (e) {
        toastError(e?.response?.data?.detail || 'Не удалось сохранить')
      } finally {
        saving.value = false
      }
    }

    const onUpdate = (val) => {
      // При закрытии — выходим из режима редактирования (без сохранения).
      if (!val && editing.value) {
        cancelEdit()
      }
      emit('update:modelValue', val)
    }
    const onLogout = async () => {
      emit('update:modelValue', false)
      try { await auth.logout() } catch { /* noop */ }
      router.push('/login')
    }

    watch(() => props.modelValue, (open) => {
      if (open) {
        editing.value = false
        load()
      }
    })

    return {
      loading, saving, editing,
      profile, form,
      canSelfEdit, canEditFormal,
      skillSuggestions, interestSuggestions, managerOptions,
      currentAbsence,
      formatDate, formatBirth, tenureLabel,
      absenceLabel, absenceIconClass,
      addChip, enterEdit, cancelEdit, save,
      onUpdate, onLogout,
    }
  },
}
</script>

<style scoped>
/* Хедер */
.pd-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.pd-header h3 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--color-text);
}
.pd-iconbtn {
  width: 32px; height: 32px;
  display: inline-flex; align-items: center; justify-content: center;
  background: transparent;
  border: 1px solid var(--color-border-strong, rgba(0,0,0,0.1));
  border-radius: 8px;
  color: var(--color-text-muted, #64748b);
  cursor: pointer;
  transition: background var(--dur-fast) ease, color var(--dur-fast) ease, border-color var(--dur-fast) ease;
}
.pd-iconbtn:hover {
  background: var(--color-primary-soft, rgba(99,102,241,0.1));
  color: var(--color-primary, #4338ca);
  border-color: var(--color-primary, #6366f1);
}

/* Состояния */
.pd-state {
  padding: 60px 0;
  text-align: center;
  color: var(--color-text-muted);
}
.pd-state--error { color: var(--color-danger, #b91c1c); }

/* Основной контейнер */
.pd {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* HERO */
.pd-hero {
  display: flex;
  gap: 18px;
  align-items: center;
  padding-bottom: 4px;
}
.pd-hero__avatar {
  position: relative;
  flex-shrink: 0;
}
.pd-hero__avatar-status {
  position: absolute;
  right: -2px;
  bottom: -2px;
  width: 30px; height: 30px;
  border-radius: 50%;
  background: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--color-surface, #fff);
  box-shadow: 0 2px 4px rgba(0,0,0,0.12);
}
.pd-hero__avatar-status i { font-size: 0.78rem; }
.pd-hero__avatar-status.is-vacation { background: #16a34a; color: #fff; }
.pd-hero__avatar-status.is-sick_leave { background: #dc2626; color: #fff; }
.pd-hero__avatar-status.is-business_trip { background: #6366f1; color: #fff; }
.pd-hero__avatar-status.is-other { background: #94a3b8; color: #fff; }

.pd-hero__meta { min-width: 0; flex: 1; display: flex; flex-direction: column; gap: 3px; }
.pd-hero__name {
  font-size: 1.25rem; font-weight: 700;
  color: var(--color-text);
  line-height: 1.2;
  overflow-wrap: anywhere;
}
.pd-hero__title {
  font-size: 0.95rem;
  color: var(--color-text-muted, #64748b);
}
.pd-hero__title .muted { font-style: italic; }
.pd-hero__role {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  font-size: 0.78rem;
  padding: 2px 10px;
  border-radius: 999px;
  width: fit-content;
  background: var(--color-primary-soft, rgba(99,102,241,0.1));
  color: var(--color-primary, #4338ca);
  font-weight: 500;
}

/* Бейдж текущего отсутствия */
.pd-absence {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(99,102,241,0.08);
  border: 1px solid rgba(99,102,241,0.35);
  color: #4338ca;
  font-size: 0.88rem;
}
.pd-absence i { font-size: 1.1rem; margin-top: 2px; }
.pd-absence__text { line-height: 1.4; }
.pd-absence__comment { color: var(--color-text-muted, #64748b); font-size: 0.82rem; margin-top: 2px; }
.pd-absence.is-vacation { background: rgba(34,197,94,0.1); border-color: rgba(34,197,94,0.4); color: #15803d; }
.pd-absence.is-sick_leave { background: rgba(220,38,38,0.1); border-color: rgba(220,38,38,0.4); color: #b91c1c; }
.pd-absence.is-business_trip { background: rgba(99,102,241,0.1); border-color: rgba(99,102,241,0.4); color: #4338ca; }
.pd-absence.is-other { background: rgba(148,163,184,0.14); border-color: rgba(148,163,184,0.45); color: #475569; }

/* Секции */
.pd-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 14px;
  border-top: 1px solid var(--color-border-subtle, rgba(0,0,0,0.06));
}
.pd-section__title {
  margin: 0;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: var(--color-text-muted, #64748b);
  display: flex;
  align-items: center;
  gap: 8px;
}
.pd-section__title i { color: var(--color-text-subtle, #94a3b8); }

/* Строки */
.pd-rows { display: flex; flex-direction: column; gap: 8px; }

.pd-row {
  display: grid;
  grid-template-columns: 20px 130px 1fr;
  gap: 10px;
  align-items: center;
  min-height: 32px;
}
.pd-row--block {
  grid-template-columns: 20px 130px 1fr;
  align-items: start;
}
.pd-row__icon { color: var(--color-text-subtle, #94a3b8); font-size: 0.95rem; text-align: center; }
.pd-row__label { color: var(--color-text-muted, #64748b); font-size: 0.82rem; }
.pd-row__value { font-size: 0.93rem; color: var(--color-text); overflow-wrap: anywhere; min-width: 0; }
.pd-row__value a { color: var(--color-primary, #4338ca); text-decoration: none; }
.pd-row__value a:hover { text-decoration: underline; }
.pd-row__value--bio { line-height: 1.45; }
.pd-row__hint { color: var(--color-text-muted, #64748b); font-size: 0.82rem; margin-left: 4px; }

/* Inputs */
.pd-input {
  width: 100%;
  padding: 6px 10px;
  background: var(--color-surface-2, #f8fafc);
  border: 1px solid var(--color-border-strong, rgba(0,0,0,0.12));
  border-radius: 6px;
  font-size: 0.92rem;
  font-family: inherit;
  color: var(--color-text);
}
.pd-input:focus {
  outline: none;
  border-color: var(--color-primary, #6366f1);
  box-shadow: 0 0 0 3px var(--color-primary-soft, rgba(99,102,241,0.18));
}
.pd-input:disabled {
  background: var(--color-surface-3, #e2e8f0);
  cursor: not-allowed;
  color: var(--color-text-muted, #64748b);
}
.pd-textarea { resize: vertical; line-height: 1.45; padding: 8px 10px; }

.pd-tg-input {
  display: inline-flex;
  align-items: center;
  width: 100%;
  background: var(--color-surface-2, #f8fafc);
  border: 1px solid var(--color-border-strong, rgba(0,0,0,0.12));
  border-radius: 6px;
  overflow: hidden;
}
.pd-tg-input span {
  padding: 6px 8px;
  background: var(--color-surface-3, #e2e8f0);
  color: var(--color-text-muted, #64748b);
  font-size: 0.92rem;
}
.pd-tg-input input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 6px 10px;
  font-size: 0.92rem;
  font-family: inherit;
  outline: none;
}

.pd-birth-edit {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.pd-check {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--color-text-muted, #64748b);
  font-size: 0.82rem;
}

.pd-bio { white-space: pre-wrap; }

.muted { color: var(--color-text-subtle, #94a3b8); font-style: italic; }

/* Чипы */
.pd-chips-block { display: flex; flex-direction: column; gap: 6px; }
.pd-chips-block__label {
  font-size: 0.78rem;
  color: var(--color-text-muted, #64748b);
  font-weight: 500;
}
.pd-chips { display: flex; flex-wrap: wrap; gap: 6px; min-height: 26px; align-items: center; }
.pd-chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 500;
}
.pd-chip.is-skill { background: var(--color-primary-soft, rgba(99,102,241,0.12)); color: var(--color-primary, #4338ca); }
.pd-chip.is-interest { background: rgba(34,197,94,0.14); color: #15803d; }

.pd-suggestions { display: flex; flex-wrap: wrap; gap: 4px; align-items: center; margin-top: 4px; }
.pd-suggestions__label { color: var(--color-text-subtle, #94a3b8); font-size: 0.72rem; margin-right: 4px; }
.pd-suggest {
  font-size: 0.76rem;
  padding: 2px 8px;
  border-radius: 999px;
  background: transparent;
  color: var(--color-text-muted, #64748b);
  border: 1px dashed var(--color-border-strong, rgba(0,0,0,0.18));
  cursor: pointer;
}
.pd-suggest:hover:not(:disabled) {
  background: var(--color-primary-soft, rgba(99,102,241,0.1));
  color: var(--color-primary, #4338ca);
  border-color: var(--color-primary, #6366f1);
}
.pd-suggest:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
