<template>
  <div class="my-profile">
    <header class="my-profile__head">
      <div class="my-profile__hero">
        <UiAvatar
          :src="profile?.avatar_url"
          :name="profile?.full_name"
          size="2xl"
        />
        <div>
          <h1>{{ profile?.full_name || 'Профиль' }}</h1>
          <div class="my-profile__sub">
            <span v-if="profile?.job_title">{{ profile.job_title }}</span>
            <span v-else class="muted">Должность не указана</span>
            <span v-if="profile?.role_name" class="my-profile__role">
              <i class="fas fa-shield-alt"></i> {{ profile.role_name }}
            </span>
          </div>
        </div>
      </div>
      <div class="my-profile__actions">
        <UiButton
          v-if="dirty"
          variant="primary"
          icon-left="fas fa-check"
          :loading="saving"
          @click="save"
        >
          Сохранить изменения
        </UiButton>
        <UiButton
          v-if="dirty"
          variant="ghost"
          icon-left="fas fa-rotate-left"
          :disabled="saving"
          @click="reset"
        >
          Отменить
        </UiButton>
      </div>
    </header>

    <div v-if="loading" class="my-profile__loading">Загрузка профиля…</div>

    <div v-else class="my-profile__grid">
      <!-- Левая колонка: личные поля (правит сам) -->
      <section class="my-profile__card">
        <h3 class="my-profile__card-title">Личные данные</h3>
        <p class="my-profile__card-hint">Эти поля редактируете вы сами.</p>

        <div class="my-profile__field">
          <label>Дата рождения</label>
          <div class="my-profile__row">
            <input
              type="date"
              v-model="form.birth_date"
              class="my-profile__input"
            />
            <label class="my-profile__check">
              <input type="checkbox" v-model="form.birth_show_year" />
              <span>Показывать год</span>
            </label>
          </div>
        </div>

        <div class="my-profile__field">
          <label>Telegram</label>
          <div class="my-profile__row">
            <span class="my-profile__prefix">@</span>
            <input
              type="text"
              v-model="form.telegram_username"
              placeholder="username"
              class="my-profile__input"
              maxlength="64"
            />
          </div>
        </div>

        <div class="my-profile__field">
          <label>О себе</label>
          <textarea
            v-model="form.bio"
            rows="4"
            maxlength="4000"
            class="my-profile__textarea"
            placeholder="Коротко о себе, опыте, чем интересен на работе…"
          ></textarea>
        </div>

        <div class="my-profile__field">
          <UiChipInput
            v-model="form.skills"
            label="Навыки"
            placeholder="Добавьте навык и нажмите Enter…"
            hint="Например: AutoCAD, ПИР, ГПР, переговоры…"
          />
          <div v-if="skillSuggestions.length" class="my-profile__suggestions">
            <span class="my-profile__suggestions-label">Часто:</span>
            <button
              v-for="s in skillSuggestions"
              :key="`sk-${s}`"
              type="button"
              class="my-profile__suggest-chip"
              :disabled="(form.skills || []).includes(s)"
              @click="addChip('skills', s)"
            >{{ s }}</button>
          </div>
        </div>

        <div class="my-profile__field">
          <UiChipInput
            v-model="form.interests"
            label="Интересы"
            placeholder="Добавьте интерес и нажмите Enter…"
            hint="Хобби, профессиональные интересы, темы для общения."
          />
          <div v-if="interestSuggestions.length" class="my-profile__suggestions">
            <span class="my-profile__suggestions-label">Часто:</span>
            <button
              v-for="s in interestSuggestions"
              :key="`int-${s}`"
              type="button"
              class="my-profile__suggest-chip"
              :disabled="(form.interests || []).includes(s)"
              @click="addChip('interests', s)"
            >{{ s }}</button>
          </div>
        </div>
      </section>

      <!-- Правая колонка: формальные поля (только админ) -->
      <section class="my-profile__card">
        <h3 class="my-profile__card-title">
          Должность и подразделение
          <span v-if="!canEditFormal" class="my-profile__card-lock" title="Эти поля редактирует администратор">
            <i class="fas fa-lock"></i>
          </span>
        </h3>
        <p class="my-profile__card-hint">
          Формальные сведения — заполняет администратор HR.
          {{ canEditFormal ? '' : 'У вас сейчас режим просмотра.' }}
        </p>

        <div class="my-profile__field">
          <label>Должность</label>
          <input
            type="text"
            v-model="form.job_title"
            :disabled="!canEditFormal"
            class="my-profile__input"
            placeholder="Например: Главный инженер проекта"
            maxlength="255"
          />
        </div>

        <div class="my-profile__field">
          <label>Подразделение</label>
          <input
            type="text"
            v-model="form.department"
            :disabled="!canEditFormal"
            class="my-profile__input"
            placeholder="Отдел / департамент"
            maxlength="255"
          />
        </div>

        <div class="my-profile__field">
          <label>Руководитель</label>
          <select
            v-model="form.manager_id"
            :disabled="!canEditFormal"
            class="my-profile__input"
          >
            <option :value="null">— не назначен —</option>
            <option
              v-for="u in managerOptions"
              :key="u.id"
              :value="u.id"
            >{{ u.full_name || u.email }}</option>
          </select>
        </div>

        <div class="my-profile__field">
          <label>Дата приёма на работу</label>
          <input
            type="date"
            v-model="form.hire_date"
            :disabled="!canEditFormal"
            class="my-profile__input"
          />
          <div v-if="form.hire_date" class="my-profile__field-hint">
            Стаж: {{ tenureLabel }}
          </div>
        </div>

        <div class="my-profile__field">
          <label>Системные</label>
          <dl class="my-profile__readonly">
            <div><dt>Email</dt><dd>{{ profile?.email || '—' }}</dd></div>
            <div><dt>Аккаунт создан</dt><dd>{{ formatDate(profile?.created_at) || '—' }}</dd></div>
            <div v-if="profile?.updated_at"><dt>Обновлён</dt><dd>{{ formatDate(profile.updated_at) }}</dd></div>
          </dl>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import { computed, onMounted, ref, watch } from 'vue'
import { api } from '../services/api'
import { useToast } from '../composables/useToast'
import { useAuthStore } from '../stores/auth'
import { UiAvatar, UiButton, UiChipInput } from '../components/ui'

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
  // YYYY-MM-DD (input[type=date])
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${dd}`
}

function toIsoOrNull(value) {
  if (!value) return null
  // input даст YYYY-MM-DD — Pydantic примет.
  return value
}

export default {
  name: 'MyProfile',
  components: { UiAvatar, UiButton, UiChipInput },
  setup() {
    const auth = useAuthStore()
    const { success, error: toastError } = useToast()
    const loading = ref(false)
    const saving = ref(false)
    const profile = ref(null)
    const form = ref(emptyForm())
    const original = ref(emptyForm())

    const skillSuggestions = ref([])
    const interestSuggestions = ref([])
    const managerOptions = ref([])

    const canEditFormal = computed(() => {
      // Грубо: «админ HR» — это `users.edit_all` в пермишинах текущего юзера.
      const perms = auth.permissions || {}
      const u = perms.users || {}
      return Boolean(u.edit_all)
    })

    const dirty = computed(() => {
      // Сравниваем «нормализованные» снимки. Простой shallow JSON-compare.
      try {
        return JSON.stringify(form.value) !== JSON.stringify(original.value)
      } catch { return true }
    })

    const tenureLabel = computed(() => {
      if (!form.value.hire_date) return ''
      const start = new Date(form.value.hire_date)
      if (!Number.isFinite(start.getTime())) return ''
      const now = new Date()
      let years = now.getFullYear() - start.getFullYear()
      const m = now.getMonth() - start.getMonth()
      if (m < 0 || (m === 0 && now.getDate() < start.getDate())) years -= 1
      if (years < 1) return 'меньше года'
      const lastTwo = years % 100
      const last = years % 10
      let word = 'лет'
      if (lastTwo < 11 || lastTwo > 14) {
        if (last === 1) word = 'год'
        else if (last >= 2 && last <= 4) word = 'года'
      }
      return `${years} ${word}`
    })

    const formatDate = (iso) => {
      if (!iso) return ''
      try {
        const d = new Date(iso)
        if (!Number.isFinite(d.getTime())) return ''
        return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
      } catch { return '' }
    }

    const fromProfile = (p) => {
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

    const load = async () => {
      loading.value = true
      try {
        profile.value = await api.profiles.getMe()
        form.value = fromProfile(profile.value)
        original.value = JSON.parse(JSON.stringify(form.value))
        // Suggest по чипам (топ-15 в каждой категории).
        const [sk, it] = await Promise.all([
          api.profiles.suggest('skills', '', 15).catch(() => []),
          api.profiles.suggest('interests', '', 15).catch(() => []),
        ])
        skillSuggestions.value = sk || []
        interestSuggestions.value = it || []
        // Список юзеров для селекта «руководитель» — только админу нужен.
        if (canEditFormal.value) {
          try {
            const all = await api.users.list({ limit: 500 })
            managerOptions.value = (all?.items || all || [])
              .filter((u) => u.id !== auth.user?.id)
          } catch {
            managerOptions.value = []
          }
        }
      } catch (e) {
        toastError('Не удалось загрузить профиль')
      } finally {
        loading.value = false
      }
    }

    const addChip = (field, value) => {
      const cur = Array.isArray(form.value[field]) ? form.value[field] : []
      if (cur.includes(value)) return
      form.value[field] = [...cur, value]
    }

    const buildSelfPatch = () => ({
      birth_date: toIsoOrNull(form.value.birth_date),
      birth_show_year: !!form.value.birth_show_year,
      bio: (form.value.bio || '').trim() || null,
      interests: form.value.interests || [],
      skills: form.value.skills || [],
      telegram_username: (form.value.telegram_username || '').trim() || null,
    })

    const buildAdminPatch = () => ({
      ...buildSelfPatch(),
      job_title: (form.value.job_title || '').trim() || null,
      department: (form.value.department || '').trim() || null,
      manager_id: form.value.manager_id || null,
      hire_date: toIsoOrNull(form.value.hire_date),
    })

    const save = async () => {
      if (saving.value) return
      saving.value = true
      try {
        if (canEditFormal.value) {
          await api.profiles.patchUser(auth.user.id, buildAdminPatch())
        } else {
          await api.profiles.patchMe(buildSelfPatch())
        }
        success('Профиль обновлён')
        await load()
      } catch (e) {
        toastError(e?.response?.data?.detail || 'Не удалось сохранить')
      } finally {
        saving.value = false
      }
    }

    const reset = () => {
      form.value = JSON.parse(JSON.stringify(original.value))
    }

    onMounted(load)

    return {
      loading, saving, profile, form,
      canEditFormal, dirty, tenureLabel, formatDate,
      skillSuggestions, interestSuggestions, managerOptions,
      addChip, save, reset,
    }
  },
}
</script>

<style scoped>
.my-profile { padding: 24px; max-width: 1200px; margin: 0 auto; }

.my-profile__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
}
.my-profile__hero { display: flex; gap: 16px; align-items: center; }
.my-profile__hero h1 { margin: 0; font-size: 1.6rem; color: var(--color-text); }
.my-profile__sub {
  display: flex; align-items: center; gap: 14px;
  color: var(--color-text-muted); font-size: 0.95rem; margin-top: 2px;
}
.my-profile__sub .muted { font-style: italic; }
.my-profile__role {
  display: inline-flex; align-items: center; gap: 4px; font-size: 0.85rem;
  padding: 2px 8px; border-radius: 12px;
  background: var(--color-primary-soft, rgba(99,102,241,0.1));
  color: var(--color-primary, #4338ca);
}
.my-profile__actions { display: flex; gap: 8px; }

.my-profile__loading { padding: 40px; text-align: center; color: var(--color-text-muted); }

.my-profile__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: start;
}
@media (max-width: 980px) {
  .my-profile__grid { grid-template-columns: 1fr; }
}

.my-profile__card {
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, rgba(0,0,0,0.06));
  border-radius: 12px;
  padding: 20px;
  box-shadow: var(--shadow-sm, 0 1px 2px rgba(0,0,0,0.04));
}
.my-profile__card-title {
  margin: 0 0 4px;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--color-text);
  display: flex; align-items: center; gap: 8px;
}
.my-profile__card-lock {
  color: var(--color-text-muted);
  font-size: 0.8rem;
}
.my-profile__card-hint {
  margin: 0 0 16px;
  color: var(--color-text-muted);
  font-size: 0.85rem;
}

.my-profile__field { margin-bottom: 14px; }
.my-profile__field label {
  display: block;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.3px;
  color: var(--color-text-muted);
  margin-bottom: 6px;
  text-transform: uppercase;
}
.my-profile__field-hint {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  margin-top: 4px;
}

.my-profile__row { display: flex; gap: 8px; align-items: center; }
.my-profile__check {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 0.85rem; color: var(--color-text-muted);
  text-transform: none; letter-spacing: 0;
  margin-bottom: 0;
}
.my-profile__check span { margin: 0; }

.my-profile__input,
.my-profile__textarea {
  width: 100%;
  padding: 8px 10px;
  background: var(--color-surface-2, #f8fafc);
  border: 1px solid var(--color-border-strong, rgba(0,0,0,0.12));
  border-radius: 8px;
  font-size: 0.95rem;
  font-family: inherit;
  color: var(--color-text);
}
.my-profile__textarea { resize: vertical; line-height: 1.45; }
.my-profile__input:focus, .my-profile__textarea:focus {
  outline: none;
  border-color: var(--color-primary, #6366f1);
  box-shadow: 0 0 0 3px var(--color-primary-soft, rgba(99,102,241,0.18));
}
.my-profile__input:disabled, .my-profile__textarea:disabled {
  background: var(--color-surface-3, #e2e8f0);
  cursor: not-allowed;
}

.my-profile__prefix {
  color: var(--color-text-muted);
  background: var(--color-surface-3, #e2e8f0);
  padding: 8px 10px;
  border: 1px solid var(--color-border-strong, rgba(0,0,0,0.12));
  border-right: none;
  border-radius: 8px 0 0 8px;
  margin-right: -10px;
}
.my-profile__prefix + .my-profile__input { border-radius: 0 8px 8px 0; }

.my-profile__suggestions {
  display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px;
  align-items: center;
}
.my-profile__suggestions-label {
  font-size: 0.75rem; color: var(--color-text-muted); margin-right: 4px;
}
.my-profile__suggest-chip {
  font-size: 0.78rem;
  padding: 2px 8px;
  border-radius: 999px;
  background: transparent;
  color: var(--color-text-muted);
  border: 1px dashed var(--color-border-strong, rgba(0,0,0,0.18));
  cursor: pointer;
}
.my-profile__suggest-chip:hover:not(:disabled) {
  background: var(--color-primary-soft, rgba(99,102,241,0.1));
  color: var(--color-primary, #4338ca);
  border-color: var(--color-primary, #6366f1);
}
.my-profile__suggest-chip:disabled { opacity: 0.4; cursor: not-allowed; }

.my-profile__readonly { margin: 0; }
.my-profile__readonly > div {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 8px;
  font-size: 0.88rem;
  padding: 4px 0;
}
.my-profile__readonly dt { color: var(--color-text-muted); }
.my-profile__readonly dd { margin: 0; color: var(--color-text); overflow-wrap: anywhere; }
</style>
