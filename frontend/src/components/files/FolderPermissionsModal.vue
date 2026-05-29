<template>
  <Teleport to="body">
    <div v-if="open" class="ffp-modal-overlay" @click.self="onClose">
      <div class="ffp-modal" role="dialog" aria-modal="true">
        <!-- Header -->
        <header class="ffp-header">
          <div class="ffp-header__icon">
            <i class="fas fa-lock"></i>
          </div>
          <div class="ffp-header__copy">
            <h3>Права доступа</h3>
            <code class="ffp-header__path" :title="path">{{ displayPath }}</code>
          </div>
          <button class="ffp-icon-btn" @click="onClose" aria-label="Закрыть">
            <i class="fas fa-times"></i>
          </button>
        </header>

        <!-- Body -->
        <div class="ffp-body">
          <!-- Loading -->
          <div v-if="loading" class="ffp-loading">
            <div class="ffp-spinner"></div>
            <span>Загрузка прав…</span>
          </div>

          <!-- Error -->
          <div v-else-if="errorMessage" class="ffp-error">
            <i class="fas fa-exclamation-triangle"></i>
            <span>{{ errorMessage }}</span>
          </div>

          <!-- Entity path -->
          <div v-else-if="data?.is_entity_path" class="ffp-info">
            <i class="fas fa-info-circle"></i>
            <div>
              <strong>Доступ управляется через связанную сущность.</strong>
              <p>
                Эта папка относится к разделу системы (сделка/договор/документ
                и т.п.). Per-folder ACL здесь отключён — управляйте доступом
                через соответствующую запись.
              </p>
            </div>
          </div>

          <!-- Normal path -->
          <template v-else-if="data">
            <!-- Effective for me -->
            <section class="ffp-section">
              <h4 class="ffp-section__title">Мои эффективные права</h4>
              <div class="ffp-flags">
                <span
                  v-for="flag in effectiveChips"
                  :key="flag.key"
                  class="ffp-flag"
                  :class="{ 'ffp-flag--on': flag.on }"
                  :title="flag.title"
                >
                  <i :class="flag.on ? 'fas fa-check' : 'fas fa-times'"></i>
                  {{ flag.label }}
                </span>
              </div>
            </section>

            <!-- Add / Edit form -->
            <section v-if="formOpen" class="ffp-form ffp-section">
              <div class="ffp-section__title-row">
                <h4 class="ffp-section__title">
                  {{ editingRule ? 'Редактировать правило' : 'Новое правило' }}
                </h4>
                <button class="ffp-text-btn" @click="cancelForm">Отмена</button>
              </div>

              <!-- Principal -->
              <div v-if="!editingRule" class="ffp-field">
                <label>Кому даём права</label>
                <div class="ffp-tabs">
                  <button
                    class="ffp-tab"
                    :class="{ 'ffp-tab--active': form.principal_type === 'user' }"
                    @click="setPrincipalType('user')"
                  >
                    <i class="fas fa-user"></i> Пользователь
                  </button>
                  <button
                    class="ffp-tab"
                    :class="{ 'ffp-tab--active': form.principal_type === 'role' }"
                    @click="setPrincipalType('role')"
                  >
                    <i class="fas fa-shield-alt"></i> Роль
                  </button>
                </div>
                <input
                  v-model="principalQuery"
                  type="text"
                  class="ffp-input"
                  placeholder="Поиск..."
                />
                <div class="ffp-principal-list">
                  <button
                    v-for="p in filteredPrincipals"
                    :key="p.id"
                    class="ffp-principal-option"
                    :class="{ 'ffp-principal-option--active': form.principal_id === String(p.id) }"
                    @click="form.principal_id = String(p.id)"
                  >
                    <UiAvatar
                      v-if="form.principal_type === 'user'"
                      :name="p.full_name || p.email || ''"
                      :src="p.avatar_url || null"
                      size="sm"
                    />
                    <span v-else class="ffp-role-badge">
                      <i class="fas fa-shield-alt"></i>
                    </span>
                    <span class="ffp-principal-copy">
                      <strong>{{ p.full_name || p.name || p.email || p.id }}</strong>
                      <small v-if="p.email">{{ p.email }}</small>
                    </span>
                    <i
                      v-if="form.principal_id === String(p.id)"
                      class="fas fa-check ffp-principal-check"
                    ></i>
                  </button>
                  <div v-if="!filteredPrincipals.length" class="ffp-empty-mini">
                    Ничего не нашли
                  </div>
                </div>
              </div>

              <div v-else class="ffp-field">
                <label>Кому даём права</label>
                <div class="ffp-principal-readonly">
                  <UiAvatar
                    v-if="editingRule.principal_type === 'user'"
                    :name="editingRule.principal_label || ''"
                    :src="editingRule.principal_avatar_url || null"
                    size="sm"
                  />
                  <span v-else class="ffp-role-badge">
                    <i class="fas fa-shield-alt"></i>
                  </span>
                  <span>
                    <strong>{{ editingRule.principal_label || editingRule.principal_id }}</strong>
                    <small>{{ editingRule.principal_type === 'user' ? 'Пользователь' : 'Роль' }}</small>
                  </span>
                </div>
              </div>

              <!-- Flags -->
              <div class="ffp-field">
                <label>Что разрешаем</label>
                <div class="ffp-checks">
                  <label class="ffp-check">
                    <input type="checkbox" v-model="form.can_read" />
                    <span><i class="fas fa-eye"></i> Чтение</span>
                  </label>
                  <label class="ffp-check">
                    <input type="checkbox" v-model="form.can_write" />
                    <span><i class="fas fa-edit"></i> Запись</span>
                  </label>
                  <label class="ffp-check">
                    <input type="checkbox" v-model="form.can_delete" />
                    <span><i class="fas fa-trash"></i> Удаление</span>
                  </label>
                  <label class="ffp-check">
                    <input type="checkbox" v-model="form.can_manage_perms" />
                    <span><i class="fas fa-key"></i> Управление правами</span>
                  </label>
                </div>
              </div>

              <div class="ffp-field">
                <label class="ffp-check ffp-check--row">
                  <input type="checkbox" v-model="form.inherit_to_subfolders" />
                  <span>
                    <i class="fas fa-sitemap"></i>
                    Распространять на вложенные папки
                  </span>
                </label>
              </div>

              <div class="ffp-form__actions">
                <button class="ffp-btn ffp-btn--secondary" @click="cancelForm">
                  Отмена
                </button>
                <button
                  class="ffp-btn ffp-btn--primary"
                  :disabled="!canSubmit || saving"
                  @click="submitForm"
                >
                  <i v-if="saving" class="fas fa-spinner fa-spin"></i>
                  <i v-else class="fas fa-check"></i>
                  Сохранить
                </button>
              </div>
            </section>

            <!-- Explicit rules -->
            <section class="ffp-section">
              <div class="ffp-section__title-row">
                <h4 class="ffp-section__title">Заданные явно на этой папке</h4>
                <button
                  v-if="!formOpen"
                  class="ffp-text-btn ffp-text-btn--primary"
                  @click="openAddForm"
                >
                  <i class="fas fa-plus"></i> Добавить правило
                </button>
              </div>
              <div v-if="!data.explicit?.length" class="ffp-empty">
                Здесь пока нет правил. Действуют только унаследованные ниже.
              </div>
              <ul v-else class="ffp-rules">
                <li v-for="rule in data.explicit" :key="rule.id" class="ffp-rule">
                  <div class="ffp-rule__principal">
                    <UiAvatar
                      v-if="rule.principal_type === 'user'"
                      :name="rule.principal_label || ''"
                      :src="rule.principal_avatar_url || null"
                      size="sm"
                    />
                    <span v-else class="ffp-role-badge">
                      <i class="fas fa-shield-alt"></i>
                    </span>
                    <div class="ffp-rule__copy">
                      <strong>{{ rule.principal_label || rule.principal_id }}</strong>
                      <small>
                        {{ rule.principal_type === 'user' ? 'Пользователь' : 'Роль' }}
                        <template v-if="rule.inherit_to_subfolders"> · вглубь</template>
                      </small>
                    </div>
                  </div>
                  <div class="ffp-rule__flags">
                    <span
                      v-for="flag in ruleFlags(rule)"
                      :key="flag.key"
                      class="ffp-mini-flag"
                      :class="{ 'ffp-mini-flag--on': flag.on }"
                      :title="flag.title"
                    >
                      <i :class="flag.icon"></i>
                    </span>
                  </div>
                  <div class="ffp-rule__actions">
                    <button
                      class="ffp-icon-btn"
                      title="Редактировать"
                      @click="openEditForm(rule)"
                    >
                      <i class="fas fa-pen"></i>
                    </button>
                    <button
                      class="ffp-icon-btn ffp-icon-btn--danger"
                      title="Удалить"
                      :disabled="deletingId === rule.id"
                      @click="deleteRule(rule)"
                    >
                      <i
                        :class="deletingId === rule.id ? 'fas fa-spinner fa-spin' : 'fas fa-trash'"
                      ></i>
                    </button>
                  </div>
                </li>
              </ul>
            </section>

            <!-- Inherited rules -->
            <section v-if="data.inherited?.length" class="ffp-section">
              <h4 class="ffp-section__title">Унаследовано от родительских папок</h4>
              <ul class="ffp-rules">
                <li
                  v-for="rule in data.inherited"
                  :key="rule.id"
                  class="ffp-rule ffp-rule--inherited"
                >
                  <div class="ffp-rule__principal">
                    <UiAvatar
                      v-if="rule.principal_type === 'user'"
                      :name="rule.principal_label || ''"
                      :src="rule.principal_avatar_url || null"
                      size="sm"
                    />
                    <span v-else class="ffp-role-badge">
                      <i class="fas fa-shield-alt"></i>
                    </span>
                    <div class="ffp-rule__copy">
                      <strong>{{ rule.principal_label || rule.principal_id }}</strong>
                      <small>
                        ← из <code>{{ rule.source_path }}</code>
                      </small>
                    </div>
                  </div>
                  <div class="ffp-rule__flags">
                    <span
                      v-for="flag in ruleFlags(rule)"
                      :key="flag.key"
                      class="ffp-mini-flag"
                      :class="{ 'ffp-mini-flag--on': flag.on }"
                      :title="flag.title"
                    >
                      <i :class="flag.icon"></i>
                    </span>
                  </div>
                </li>
              </ul>
            </section>
          </template>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script>
import { ref, reactive, computed, watch, nextTick } from 'vue'
import * as ffpApi from '../../services/api/fileFolderPermissions'
import * as usersApi from '../../services/api/users'
import * as rolesApi from '../../services/api/roles'
import { useToast } from '../../composables/useToast'
import UiAvatar from '../ui/UiAvatar.vue'

const EMPTY_FORM = {
  principal_type: 'user',
  principal_id: '',
  can_read: true,
  can_write: false,
  can_delete: false,
  can_manage_perms: false,
  inherit_to_subfolders: true,
}

export default {
  name: 'FolderPermissionsModal',
  components: { UiAvatar },
  props: {
    open: { type: Boolean, default: false },
    path: { type: String, default: '' },
  },
  emits: ['close'],
  setup(props, { emit }) {
    const toast = useToast()

    const loading = ref(false)
    const saving = ref(false)
    const deletingId = ref(null)
    const errorMessage = ref('')

    const data = ref(null) // FolderPermissionsResponse
    const users = ref([])
    const roles = ref([])
    const principalsLoaded = ref(false)

    const formOpen = ref(false)
    const editingRule = ref(null)
    const form = reactive({ ...EMPTY_FORM })
    const principalQuery = ref('')

    const displayPath = computed(() => {
      const raw = (props.path || '').replace(/^disk:/, '')
      return raw || '/'
    })

    const effectiveChips = computed(() => {
      const flags = data.value?.effective_for_me || {}
      return [
        { key: 'read', label: 'Чтение', title: 'Видеть содержимое папки', on: !!flags.can_read },
        { key: 'write', label: 'Запись', title: 'Создавать/загружать/переименовывать', on: !!flags.can_write },
        { key: 'delete', label: 'Удаление', title: 'Удалять файлы и подпапки', on: !!flags.can_delete },
        { key: 'manage', label: 'Управление', title: 'Менять правила доступа этой папки', on: !!flags.can_manage_perms },
      ]
    })

    const filteredPrincipals = computed(() => {
      const q = principalQuery.value.trim().toLowerCase()
      const list = form.principal_type === 'user' ? users.value : roles.value
      if (!q) return list.slice(0, 60)
      return list
        .filter((p) => {
          const hay = `${p.full_name || ''} ${p.name || ''} ${p.email || ''}`.toLowerCase()
          return hay.includes(q)
        })
        .slice(0, 60)
    })

    const canSubmit = computed(() => {
      if (!form.principal_id) return false
      if (!form.can_read && !form.can_write && !form.can_delete && !form.can_manage_perms) {
        return false
      }
      return true
    })

    const ruleFlags = (rule) => [
      { key: 'read', icon: 'fas fa-eye', title: 'Чтение', on: !!rule.can_read },
      { key: 'write', icon: 'fas fa-edit', title: 'Запись', on: !!rule.can_write },
      { key: 'delete', icon: 'fas fa-trash', title: 'Удаление', on: !!rule.can_delete },
      { key: 'manage', icon: 'fas fa-key', title: 'Управление правами', on: !!rule.can_manage_perms },
    ]

    const loadPrincipals = async () => {
      if (principalsLoaded.value) return
      try {
        const [u, r] = await Promise.all([
          usersApi.list({ limit: 1000 }).catch(() => null),
          rolesApi.list().catch(() => null),
        ])
        users.value = Array.isArray(u) ? u : (u?.items || [])
        roles.value = Array.isArray(r) ? r : (r?.items || [])
        principalsLoaded.value = true
      } catch (e) {
        console.warn('Не удалось загрузить пользователей/роли:', e)
      }
    }

    const loadPermissions = async () => {
      if (!props.path) return
      loading.value = true
      errorMessage.value = ''
      data.value = null
      formOpen.value = false
      editingRule.value = null
      try {
        const result = await ffpApi.list(props.path)
        data.value = result
      } catch (e) {
        const status = e?.response?.status
        const detail = e?.response?.data?.detail
        if (status === 403) {
          errorMessage.value =
            detail || 'У вас нет прав на управление правами этой папки.'
        } else if (status === 404) {
          errorMessage.value = detail || 'Папка не найдена.'
        } else {
          errorMessage.value = detail || 'Не удалось загрузить права доступа.'
        }
      } finally {
        loading.value = false
      }
    }

    const setPrincipalType = (type) => {
      form.principal_type = type
      form.principal_id = ''
      principalQuery.value = ''
    }

    const resetForm = () => {
      Object.assign(form, EMPTY_FORM)
      principalQuery.value = ''
      editingRule.value = null
    }

    const openAddForm = async () => {
      resetForm()
      formOpen.value = true
      await loadPrincipals()
    }

    const openEditForm = (rule) => {
      editingRule.value = rule
      form.principal_type = rule.principal_type
      form.principal_id = String(rule.principal_id)
      form.can_read = !!rule.can_read
      form.can_write = !!rule.can_write
      form.can_delete = !!rule.can_delete
      form.can_manage_perms = !!rule.can_manage_perms
      form.inherit_to_subfolders = !!rule.inherit_to_subfolders
      formOpen.value = true
    }

    const cancelForm = () => {
      formOpen.value = false
      resetForm()
    }

    const submitForm = async () => {
      if (!canSubmit.value || saving.value) return
      saving.value = true
      try {
        await ffpApi.upsert({
          folder_path: props.path,
          principal_type: form.principal_type,
          principal_id: form.principal_id,
          can_read: form.can_read,
          can_write: form.can_write,
          can_delete: form.can_delete,
          can_manage_perms: form.can_manage_perms,
          inherit_to_subfolders: form.inherit_to_subfolders,
        })
        toast.success(editingRule.value ? 'Правило обновлено' : 'Правило добавлено')
        formOpen.value = false
        resetForm()
        await loadPermissions()
      } catch (e) {
        const detail = e?.response?.data?.detail
        toast.error(detail || 'Не удалось сохранить правило')
      } finally {
        saving.value = false
      }
    }

    const deleteRule = async (rule) => {
      if (deletingId.value) return
      if (!confirm(`Удалить правило для «${rule.principal_label || rule.principal_id}»?`)) {
        return
      }
      deletingId.value = rule.id
      try {
        await ffpApi.remove(rule.id)
        toast.success('Правило удалено')
        await loadPermissions()
      } catch (e) {
        const detail = e?.response?.data?.detail
        toast.error(detail || 'Не удалось удалить правило')
      } finally {
        deletingId.value = null
      }
    }

    const onClose = () => {
      if (saving.value) return
      emit('close')
    }

    // На каждое открытие — заново подтягиваем данные с бэкенда.
    watch(
      () => props.open,
      (val) => {
        if (val) {
          nextTick(() => loadPermissions())
        } else {
          data.value = null
          errorMessage.value = ''
          formOpen.value = false
          resetForm()
        }
      },
    )

    return {
      loading,
      saving,
      deletingId,
      errorMessage,
      data,
      formOpen,
      editingRule,
      form,
      principalQuery,
      displayPath,
      effectiveChips,
      filteredPrincipals,
      canSubmit,
      ruleFlags,
      setPrincipalType,
      openAddForm,
      openEditForm,
      cancelForm,
      submitForm,
      deleteRule,
      onClose,
    }
  },
}
</script>

<style scoped>
.ffp-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1500;
  backdrop-filter: blur(4px);
}

.ffp-modal {
  background: var(--md-sys-color-surface-thick);
  border-radius: 16px;
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  margin: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

/* Header */
.ffp-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px 20px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.ffp-header__icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #FEF3C7;
  color: #B45309;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
}

.ffp-header__copy {
  flex: 1;
  min-width: 0;
}

.ffp-header__copy h3 {
  margin: 0;
  font-size: 1.1rem;
  color: var(--md-sys-color-on-surface);
}

.ffp-header__path {
  display: block;
  font-size: 0.78rem;
  color: var(--md-sys-color-on-surface-variant);
  font-family: 'JetBrains Mono', 'Consolas', monospace;
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ffp-icon-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  transition: background 0.15s;
}

.ffp-icon-btn:hover:not(:disabled) {
  background: var(--md-sys-color-outline-variant);
}

.ffp-icon-btn--danger:hover:not(:disabled) {
  background: rgba(255, 59, 48, 0.12);
  color: var(--color-danger);
}

.ffp-icon-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Body */
.ffp-body {
  padding: 16px 20px;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ffp-loading,
.ffp-error,
.ffp-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 12px;
  background: var(--md-sys-color-surface);
  font-size: 0.9rem;
  color: var(--md-sys-color-on-surface-variant);
}

.ffp-error {
  background: rgba(255, 59, 48, 0.08);
  color: var(--color-danger);
}

.ffp-info {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container, var(--md-sys-color-primary));
  align-items: flex-start;
}

.ffp-info i {
  margin-top: 2px;
}

.ffp-info p {
  margin: 4px 0 0;
  font-size: 0.85rem;
  opacity: 0.85;
}

.ffp-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--md-sys-color-outline);
  border-top-color: var(--md-sys-color-primary);
  border-radius: 50%;
  animation: ffp-spin 1s linear infinite;
}

@keyframes ffp-spin {
  to { transform: rotate(360deg); }
}

/* Sections */
.ffp-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ffp-section__title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.ffp-section__title {
  margin: 0;
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--md-sys-color-on-surface-variant);
}

/* Effective flags */
.ffp-flags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.ffp-flag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-on-surface-variant);
  border: 1px solid var(--md-sys-color-outline-variant);
}

.ffp-flag--on {
  background: #DCFCE7;
  color: #166534;
  border-color: #BBF7D0;
}

/* Form */
.ffp-form {
  padding: 14px;
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 12px;
}

.ffp-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 10px;
}

.ffp-field:first-child {
  margin-top: 0;
}

.ffp-field > label {
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
}

.ffp-tabs {
  display: flex;
  gap: 6px;
}

.ffp-tab {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 10px;
  background: var(--md-sys-color-surface-thick);
  font-size: 0.85rem;
  color: var(--md-sys-color-on-surface);
  cursor: pointer;
  transition: all 0.15s;
}

.ffp-tab:hover {
  border-color: var(--md-sys-color-primary);
}

.ffp-tab--active {
  background: var(--md-sys-color-primary);
  color: white;
  border-color: var(--md-sys-color-primary);
}

.ffp-input {
  padding: 8px 12px;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 8px;
  background: var(--md-sys-color-surface-thick);
  font-size: 0.9rem;
  color: var(--md-sys-color-on-surface);
}

.ffp-input:focus {
  outline: none;
  border-color: var(--md-sys-color-primary);
}

.ffp-principal-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 10px;
  background: var(--md-sys-color-surface-thick);
}

.ffp-principal-option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 10px;
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.ffp-principal-option:last-child {
  border-bottom: none;
}

.ffp-principal-option:hover {
  background: var(--md-sys-color-primary-container);
}

.ffp-principal-option--active {
  background: var(--md-sys-color-primary-container);
}

.ffp-principal-copy {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.ffp-principal-copy strong {
  font-size: 0.85rem;
  color: var(--md-sys-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ffp-principal-copy small {
  font-size: 0.72rem;
  color: var(--md-sys-color-on-surface-variant);
}

.ffp-principal-check {
  color: var(--md-sys-color-primary);
  font-size: 0.85rem;
}

.ffp-principal-readonly {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: var(--md-sys-color-surface-thick);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 10px;
}

.ffp-principal-readonly span {
  display: flex;
  flex-direction: column;
}

.ffp-principal-readonly strong {
  font-size: 0.9rem;
  color: var(--md-sys-color-on-surface);
}

.ffp-principal-readonly small {
  font-size: 0.72rem;
  color: var(--md-sys-color-on-surface-variant);
}

.ffp-role-badge {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  background: #E0E7FF;
  color: #4F46E5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  flex-shrink: 0;
}

.ffp-empty-mini {
  padding: 16px;
  text-align: center;
  font-size: 0.85rem;
  color: var(--md-sys-color-on-surface-variant);
}

.ffp-checks {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.ffp-check {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 10px;
  background: var(--md-sys-color-surface-thick);
  font-size: 0.85rem;
  color: var(--md-sys-color-on-surface);
  cursor: pointer;
}

.ffp-check--row {
  width: 100%;
}

.ffp-check:hover {
  border-color: var(--md-sys-color-primary);
}

.ffp-check input {
  margin: 0;
}

.ffp-check span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.ffp-check span i {
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.78rem;
}

.ffp-form__actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 14px;
}

.ffp-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.15s;
}

.ffp-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.ffp-btn--primary {
  background: var(--md-sys-color-primary);
  color: white;
}

.ffp-btn--primary:hover:not(:disabled) {
  filter: brightness(1.05);
}

.ffp-btn--secondary {
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-on-surface);
  border-color: var(--md-sys-color-outline);
}

.ffp-btn--secondary:hover:not(:disabled) {
  background: var(--md-sys-color-surface-thick);
}

.ffp-text-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.8rem;
  color: var(--md-sys-color-on-surface-variant);
  padding: 4px 6px;
  border-radius: 6px;
}

.ffp-text-btn:hover {
  background: var(--md-sys-color-surface);
}

.ffp-text-btn--primary {
  color: var(--md-sys-color-primary);
  font-weight: 500;
}

/* Rules list */
.ffp-empty {
  padding: 14px;
  text-align: center;
  font-size: 0.85rem;
  color: var(--md-sys-color-on-surface-variant);
  background: var(--md-sys-color-surface);
  border-radius: 10px;
  border: 1px dashed var(--md-sys-color-outline-variant);
}

.ffp-rules {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ffp-rule {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 10px;
}

.ffp-rule--inherited {
  background: var(--md-sys-color-surface);
  opacity: 0.95;
  border-style: dashed;
}

.ffp-rule__principal {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.ffp-rule__copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.ffp-rule__copy strong {
  font-size: 0.88rem;
  color: var(--md-sys-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ffp-rule__copy small {
  font-size: 0.72rem;
  color: var(--md-sys-color-on-surface-variant);
}

.ffp-rule__copy small code {
  font-family: 'JetBrains Mono', 'Consolas', monospace;
  font-size: 0.7rem;
  color: var(--md-sys-color-on-surface-variant);
}

.ffp-rule__flags {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.ffp-mini-flag {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  background: var(--md-sys-color-surface-thick);
  color: var(--md-sys-color-on-surface-variant);
  border: 1px solid var(--md-sys-color-outline-variant);
}

.ffp-mini-flag--on {
  background: #DCFCE7;
  color: #166534;
  border-color: #BBF7D0;
}

.ffp-rule__actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

/* Mobile */
@media (max-width: 560px) {
  .ffp-modal {
    margin: 8px;
    max-height: 95vh;
  }
  .ffp-body {
    padding: 12px 14px;
  }
  .ffp-checks {
    grid-template-columns: 1fr;
  }
  .ffp-rule {
    flex-wrap: wrap;
  }
  .ffp-rule__principal {
    flex-basis: 100%;
  }
}
</style>
