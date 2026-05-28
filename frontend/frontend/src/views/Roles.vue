<template>
  <div class="roles-view access-matrix-view">
    <section class="access-matrix-shell">
      <header class="access-matrix-header">
        <div class="access-matrix-title">
          <span>Матрица доступа</span>
          <h1>Роли и права</h1>
        </div>

        <div class="access-matrix-header__search">
          <UiInput
            v-model.trim="sectionSearch"
            size="sm"
            icon-left="fas fa-search"
            placeholder="Быстрый поиск раздела..."
          />
        </div>
      </header>

      <div class="access-rolebar">
        <span class="access-rolebar__label">Роль:</span>

        <div class="access-rolebar__chips">
          <button
            v-for="role in roles"
            :key="role.id"
            class="access-role-chip"
            :class="{ 'access-role-chip--active': selectedRoleId === role.id }"
            @click="selectRole(role)"
          >
            {{ role.name }}
            <small v-if="role.is_system">Системная</small>
          </button>
        </div>

        <div class="access-rolebar__actions">
          <UiIconButton
            icon="fas fa-sync"
            label="Обновить"
            size="sm"
            @click="reloadAll"
          />
          <UiButton
            variant="primary"
            size="sm"
            icon-left="fas fa-plus"
            @click="openCreate"
          >
            Новая роль
          </UiButton>
        </div>
      </div>

      <div v-if="loadingRoles" class="access-loading">
        <SkeletonLoader v-for="i in 8" :key="i" height="34px" />
      </div>

      <UiEmptyState
        v-else-if="!roles.length"
        class="access-empty"
        icon="fas fa-user-shield"
        title="Ролей пока нет"
        description="Создайте первую роль и настройте матрицу доступа."
      >
        <template #actions>
          <UiButton variant="primary" size="sm" icon-left="fas fa-plus" @click="openCreate">
            Создать роль
          </UiButton>
        </template>
      </UiEmptyState>

      <div v-else class="access-matrix-card">
        <div class="access-selected-role">
          <div class="access-selected-role__info">
            <div class="access-selected-role__name">
              {{ selectedRole?.name || 'Роль не выбрана' }}
              <span v-if="selectedRole?.is_system">Системная роль</span>
            </div>
            <p>{{ selectedRole?.description || 'Описание не заполнено.' }}</p>
          </div>

          <div class="access-selected-role__actions">
            <UiButton
              variant="secondary"
              size="sm"
              icon-left="fas fa-pen"
              :disabled="!selectedRole"
              @click="editRole(selectedRole)"
            >
              Изменить
            </UiButton>
            <UiButton
              variant="danger"
              size="sm"
              icon-left="fas fa-trash"
              :disabled="!selectedRole || selectedRole.is_system"
              @click="deleteRole(selectedRole)"
            >
              Удалить
            </UiButton>
            <UiButton
              variant="primary"
              size="sm"
              icon-left="fas fa-save"
              :loading="savingPermissions"
              :disabled="!selectedRole || savingPermissions"
              @click="savePermissions"
            >
              Сохранить права
            </UiButton>
          </div>
        </div>

        <div class="access-table-wrap">
          <table class="access-table">
            <thead>
              <tr>
                <th>Раздел</th>
                <th v-for="column in permissionColumns" :key="column.key">
                  {{ column.label }}
                </th>
              </tr>
            </thead>
            <tbody>
              <template v-for="group in groupedSectionRows" :key="group.key">
                <tr v-if="group.rows.length" class="access-group-row">
                  <td :colspan="permissionColumns.length + 1">{{ group.label }}</td>
                </tr>
                <tr v-for="row in group.rows" :key="row.key">
                  <td>
                    <span class="access-section-name">{{ row.label }}</span>
                  </td>
                  <td v-for="column in permissionColumns" :key="`${row.key}-${column.key}`">
                    <label class="access-check" :title="permissionTitle(column.key)">
                      <input
                        type="checkbox"
                        :checked="permissionState(row.key, column.key)"
                        :disabled="!selectedRole"
                        @change="toggleMatrixPermission(row.key, column.key, $event.target.checked)"
                      >
                      <span></span>
                    </label>
                  </td>
                </tr>
              </template>
              <tr v-if="!filteredSectionRows.length">
                <td :colspan="permissionColumns.length + 1" class="access-no-results">
                  Разделы по запросу не найдены.
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <footer class="access-matrix-footer">
          <div class="access-legend">
            <span><i class="access-legend__on"></i> Включено</span>
            <span><i></i> Выключено</span>
          </div>

          <div class="access-bulk-actions">
            <UiButton variant="ghost" size="sm" :disabled="!selectedRole" @click="grantAllPermissions">
              Включить все
            </UiButton>
            <UiButton variant="ghost" size="sm" :disabled="!selectedRole" @click="clearAllPermissions">
              Снять все
            </UiButton>
          </div>
        </footer>
      </div>
    </section>

    <UiModal
      v-model="showModal"
      :title="isEditing ? 'Редактировать роль' : 'Создать роль'"
      size="sm"
    >
      <div class="access-role-form">
        <UiInput
          v-model.trim="roleForm.name"
          label="Название *"
          placeholder="Например, Руководитель проекта"
        />
        <UiTextarea
          v-model.trim="roleForm.description"
          label="Описание"
          placeholder="Кратко опишите назначение роли"
          :rows="4"
        />
      </div>

      <template #footer>
        <UiButton variant="secondary" @click="closeModal">Отмена</UiButton>
        <UiButton variant="primary" :loading="savingRole" @click="saveRole">
          {{ isEditing ? 'Сохранить' : 'Создать' }}
        </UiButton>
      </template>
    </UiModal>
  </div>
</template>

<script>
import { computed, onMounted, ref } from 'vue'
import SkeletonLoader from '../components/ui/SkeletonLoader.vue'
import { api } from '../services/api'
import { useRolesStore } from '../stores/roles'
import {
  UiButton,
  UiEmptyState,
  UiIconButton,
  UiInput,
  UiModal,
  UiTextarea
} from '../components/ui'

const SECTION_LABELS = {
  projects: 'Сделки',
  leads: 'Лиды',
  companies: 'Контрагенты',
  customer_portal: 'Кабинет заказчика',
  contracts: 'Договоры',
  catalog: 'Каталог',
  document_registry: 'Документация',
  files_catalog: 'Файлы',
  document_templates: 'Шаблоны документов',
  outgoing_registry: 'Исходящие',
  mail: 'Почта',
  tasks: 'Задачи',
  task_chat: 'Чат по задачам',
  global_chat: 'Общий чат',
  calendar: 'Календарь',
  executor: 'Панель исполнителя',
  work_results_reviews: 'Согласования результатов',
  legal_work: 'Юридическая работа',
  task_auctions_manage: 'Аукционы задач (управление)',
  task_auctions_bid: 'Аукционы задач (заявки)',
  tasks_penalties_manage: 'Штрафы и бонусы (правила)',
  tenders_admin: 'Тендеры (основные)',
  tenders_subcontractor: 'Тендеры (подрядчик)',
  accreditations_admin: 'Аккредитации (основные)',
  accreditations_subcontractor: 'Аккредитации (подрядчик)',
  finance: 'Финансы',
  treasury: 'Казначейство',
  income_expense: 'ДДС',
  users: 'Пользователи',
  roles: 'Роли и права'
}

const SECTION_GROUPS = [
  {
    key: 'crm',
    label: 'CRM',
    sections: ['projects', 'leads', 'companies', 'customer_portal']
  },
  {
    key: 'documents',
    label: 'Документооборот',
    sections: ['contracts', 'catalog', 'document_registry', 'files_catalog', 'document_templates', 'outgoing_registry', 'mail']
  },
  {
    key: 'planning',
    label: 'Задачи и коммуникации',
    sections: ['tasks', 'task_chat', 'global_chat', 'calendar', 'executor', 'work_results_reviews']
  },
  {
    key: 'legal',
    label: 'Юридический отдел',
    sections: ['legal_work']
  },
  {
    key: 'tenders',
    label: 'Тендеры и аккредитации',
    sections: ['task_auctions_manage', 'task_auctions_bid', 'tenders_admin', 'tenders_subcontractor', 'accreditations_admin', 'accreditations_subcontractor']
  },
  {
    key: 'finance',
    label: 'Финансы',
    sections: ['tasks_penalties_manage', 'finance', 'treasury', 'income_expense']
  },
  {
    key: 'admin',
    label: 'Администрирование',
    sections: ['users', 'roles']
  }
]

const PERMISSION_COLUMNS = [
  { key: 'read_all', label: 'Чтение всех' },
  { key: 'read_assigned', label: 'Чтение своих' }
]

export default {
  name: 'Roles',
  components: {
    SkeletonLoader,
    UiButton,
    UiEmptyState,
    UiIconButton,
    UiInput,
    UiModal,
    UiTextarea
  },
  setup() {
    const rolesStore = useRolesStore()
    const roles = ref([])
    const sections = ref([])
    const permissions = ref({})
    const loadingRoles = ref(false)
    const savingPermissions = ref(false)
    const savingRole = ref(false)
    const selectedRoleId = ref('')
    const showModal = ref(false)
    const isEditing = ref(false)
    const sectionSearch = ref('')

    const roleForm = ref({
      id: '',
      name: '',
      description: ''
    })

    const selectedRole = computed(() => roles.value.find((role) => role.id === selectedRoleId.value) || null)

    const sectionGroupByKey = computed(() => {
      const map = {}
      SECTION_GROUPS.forEach((group) => {
        group.sections.forEach((section) => {
          map[section] = group.key
        })
      })
      return map
    })

    const sectionRows = computed(() => sections.value.map((section) => ({
      key: section,
      label: SECTION_LABELS[section] || section,
      groupKey: sectionGroupByKey.value[section] || 'other'
    })))

    const filteredSectionRows = computed(() => {
      const query = sectionSearch.value.trim().toLowerCase()
      if (!query) return sectionRows.value
      return sectionRows.value.filter((row) => {
        const groupLabel = SECTION_GROUPS.find((group) => group.key === row.groupKey)?.label || 'Прочее'
        return [row.label, groupLabel].some((value) => value.toLowerCase().includes(query))
      })
    })

    const groupedSectionRows = computed(() => {
      const rowsByGroup = filteredSectionRows.value.reduce((acc, row) => {
        if (!acc[row.groupKey]) acc[row.groupKey] = []
        acc[row.groupKey].push(row)
        return acc
      }, {})

      const knownGroups = SECTION_GROUPS.map((group) => ({
        key: group.key,
        label: group.label,
        rows: (rowsByGroup[group.key] || []).sort((left, right) => left.label.localeCompare(right.label, 'ru'))
      }))

      const otherRows = rowsByGroup.other || []
      if (otherRows.length) {
        knownGroups.push({
          key: 'other',
          label: 'Прочее',
          rows: otherRows.sort((left, right) => left.label.localeCompare(right.label, 'ru'))
        })
      }
      return knownGroups
    })

    const ensurePermission = (section) => {
      const current = permissions.value[section] || { read_all: false, read_assigned: false }
      return {
        read_all: Boolean(current.read_all),
        read_assigned: Boolean(current.read_assigned)
      }
    }

    const loadRoles = async () => {
      loadingRoles.value = true
      try {
        await rolesStore.refresh()
        roles.value = rolesStore.items
      } catch (error) {
        console.error('Error loading roles:', error)
        roles.value = []
      } finally {
        loadingRoles.value = false
      }
    }

    const loadSections = async () => {
      try {
        sections.value = await api.roles.listSections() || []
      } catch (error) {
        console.error('Error loading sections:', error)
        sections.value = []
      }
    }

    const loadPermissions = async (roleId) => {
      if (!roleId) return
      try {
        const perms = await api.roles.getPermissions(roleId)
        const base = {}
        sections.value.forEach((section) => {
          base[section] = { read_all: false, read_assigned: false }
        })
        ;(perms || []).forEach((permission) => {
          base[permission.section] = {
            read_all: Boolean(permission.read_all),
            read_assigned: Boolean(permission.read_assigned)
          }
        })
        permissions.value = base
      } catch (error) {
        console.error('Error loading permissions:', error)
        permissions.value = {}
      }
    }

    const reloadAll = async () => {
      const currentRoleId = selectedRoleId.value
      await Promise.all([loadRoles(), loadSections()])
      const nextRole = roles.value.find((role) => role.id === currentRoleId) || roles.value[0]
      if (nextRole) await selectRole(nextRole)
    }

    const selectRole = async (role) => {
      if (!role) return
      selectedRoleId.value = role.id
      await loadPermissions(role.id)
    }

    const savePermissions = async () => {
      if (!selectedRole.value) return
      savingPermissions.value = true
      try {
        const payload = sections.value.map((section) => ({
          section,
          read_all: Boolean(permissions.value[section]?.read_all),
          read_assigned: Boolean(permissions.value[section]?.read_assigned)
        }))
        await api.roles.updatePermissions(selectedRole.value.id, payload)
        await loadPermissions(selectedRole.value.id)
      } catch (error) {
        console.error('Error saving permissions:', error)
        alert('Ошибка сохранения прав')
      } finally {
        savingPermissions.value = false
      }
    }

    const permissionState = (section, column) => {
      const permission = ensurePermission(section)
      return Boolean(permission[column])
    }

    const toggleMatrixPermission = (section, column, value) => {
      const next = ensurePermission(section)
      next[column] = value
      permissions.value = {
        ...permissions.value,
        [section]: next
      }
    }

    const grantAllPermissions = () => {
      const next = {}
      sections.value.forEach((section) => {
        next[section] = { read_all: true, read_assigned: true }
      })
      permissions.value = next
    }

    const clearAllPermissions = () => {
      const next = {}
      sections.value.forEach((section) => {
        next[section] = { read_all: false, read_assigned: false }
      })
      permissions.value = next
    }

    const permissionTitle = (column) => {
      if (column === 'read_all') return 'Полный доступ к разделу. Для write-операций backend использует это право.'
      return 'Доступ к назначенным/связанным сущностям раздела.'
    }

    const openCreate = () => {
      showModal.value = true
      isEditing.value = false
      roleForm.value = { id: '', name: '', description: '' }
    }

    const editRole = (role) => {
      if (!role) return
      showModal.value = true
      isEditing.value = true
      roleForm.value = {
        id: role.id,
        name: role.name,
        description: role.description || ''
      }
    }

    const saveRole = async () => {
      if (!roleForm.value.name.trim()) {
        alert('Название роли обязательно')
        return
      }
      savingRole.value = true
      try {
        const payload = {
          name: roleForm.value.name,
          description: roleForm.value.description
        }
        const saved = isEditing.value
          ? await api.roles.update(roleForm.value.id, payload)
          : await api.roles.create(payload)
        await loadRoles()
        closeModal()
        const savedRole = roles.value.find((role) => role.id === saved?.id)
        if (savedRole) await selectRole(savedRole)
      } catch (error) {
        console.error('Error saving role:', error)
        alert('Ошибка сохранения роли')
      } finally {
        savingRole.value = false
      }
    }

    const deleteRole = async (role) => {
      if (!role || role.is_system) return
      if (!confirm(`Удалить роль "${role.name}"?`)) return
      try {
        await api.roles.remove(role.id)
        await loadRoles()
        const nextRole = roles.value[0]
        if (nextRole) {
          await selectRole(nextRole)
        } else {
          selectedRoleId.value = ''
          permissions.value = {}
        }
      } catch (error) {
        console.error('Error deleting role:', error)
        alert('Ошибка удаления роли')
      }
    }

    const closeModal = () => {
      showModal.value = false
      isEditing.value = false
    }

    onMounted(async () => {
      await Promise.all([loadRoles(), loadSections()])
      if (roles.value.length) await selectRole(roles.value[0])
    })

    return {
      roles,
      permissions,
      loadingRoles,
      savingPermissions,
      savingRole,
      selectedRole,
      selectedRoleId,
      showModal,
      isEditing,
      roleForm,
      sectionSearch,
      permissionColumns: PERMISSION_COLUMNS,
      groupedSectionRows,
      filteredSectionRows,
      reloadAll,
      openCreate,
      editRole,
      saveRole,
      deleteRole,
      closeModal,
      selectRole,
      savePermissions,
      permissionState,
      toggleMatrixPermission,
      grantAllPermissions,
      clearAllPermissions,
      permissionTitle
    }
  }
}
</script>

<style scoped>
.access-matrix-view {
  min-height: calc(100vh - 80px);
  padding: var(--space-3);
  color: var(--color-text);
}

.access-matrix-shell {
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  background: var(--color-surface);
  box-shadow: var(--shadow-md);
}

.access-matrix-header,
.access-rolebar,
.access-selected-role,
.access-matrix-footer {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border-subtle);
}

.access-matrix-header {
  justify-content: space-between;
}

.access-matrix-title {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  min-width: 0;
}

.access-matrix-title span,
.access-group-row td,
.access-rolebar__label,
.access-legend span {
  color: var(--color-text-muted);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  font-weight: var(--fw-bold);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.access-matrix-title h1 {
  margin: 0;
  font-size: var(--text-xl);
  font-weight: var(--fw-bold);
  color: var(--color-text);
}

.access-matrix-header__search {
  flex: 0 1 320px;
  min-width: 220px;
}

.access-rolebar {
  flex-wrap: wrap;
}

.access-rolebar__chips {
  display: flex;
  flex: 1 1 auto;
  flex-wrap: wrap;
  gap: var(--space-2);
  min-width: 0;
}

.access-rolebar__actions,
.access-selected-role__actions,
.access-bulk-actions,
.access-legend {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.access-role-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  min-height: 32px;
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-pill);
  background: var(--color-surface-2);
  color: var(--color-text);
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  cursor: pointer;
  transition:
    background-color var(--dur-fast) ease,
    border-color var(--dur-fast) ease,
    color var(--dur-fast) ease,
    box-shadow var(--dur-fast) ease;
}

.access-role-chip:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

.access-role-chip small {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
}

.access-role-chip--active {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: var(--color-on-primary);
  box-shadow: var(--shadow-sm);
}

.access-role-chip--active small {
  color: rgba(255, 255, 255, 0.78);
}

.access-loading {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-4);
}

.access-empty {
  min-height: 320px;
}

.access-matrix-card {
  min-height: 540px;
}

.access-selected-role {
  justify-content: space-between;
  background: var(--color-surface-2);
}

.access-selected-role__info {
  min-width: 0;
}

.access-selected-role__name {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-lg);
  font-weight: var(--fw-bold);
  color: var(--color-text);
}

.access-selected-role__name span {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 var(--space-2);
  border-radius: var(--radius-pill);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
}

.access-selected-role p {
  margin: var(--space-1) 0 0;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.access-table-wrap {
  overflow: auto;
}

.access-table {
  width: 100%;
  min-width: 900px;
  border-collapse: collapse;
  table-layout: fixed;
}

.access-table th,
.access-table td {
  border-right: 1px solid var(--color-border-subtle);
  border-bottom: 1px solid var(--color-border-subtle);
}

.access-table th:last-child,
.access-table td:last-child {
  border-right: 0;
}

.access-table th {
  height: 32px;
  background: var(--color-surface-2);
  color: var(--color-text-muted);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  font-weight: var(--fw-bold);
  letter-spacing: 0.1em;
  text-align: center;
  text-transform: uppercase;
}

.access-table th:first-child {
  width: 260px;
  padding-left: var(--space-4);
  text-align: left;
}

.access-table td {
  height: 36px;
  padding: 0 var(--space-3);
  color: var(--color-text);
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  text-align: center;
}

.access-table td:first-child {
  text-align: left;
}

.access-table tbody tr:not(.access-group-row):hover {
  background: var(--color-primary-soft);
}

.access-group-row td {
  height: 28px;
  background: var(--color-surface-2);
  text-align: left;
}

.access-section-name {
  text-transform: uppercase;
}

.access-check {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.access-check input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.access-check span {
  width: 16px;
  height: 16px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-xs);
  background: var(--color-surface);
  transition:
    border-color var(--dur-fast) ease,
    background-color var(--dur-fast) ease,
    box-shadow var(--dur-fast) ease;
}

.access-check input:checked + span {
  border-color: var(--color-success);
  background: var(--color-success);
}

.access-check input:checked + span::after {
  display: block;
  color: #fff;
  content: '✓';
  font-size: var(--text-xs);
  font-weight: var(--fw-bold);
  line-height: 14px;
  text-align: center;
}

.access-no-results {
  height: 96px !important;
  color: var(--color-text-muted) !important;
  text-align: center !important;
  text-transform: none !important;
}

.access-matrix-footer {
  justify-content: space-between;
  border-bottom: 0;
  background: var(--color-surface-2);
}

.access-legend i {
  width: 10px;
  height: 10px;
  border: 1px solid var(--color-border-strong);
  border-radius: 2px;
  background: var(--color-surface);
}

.access-legend__on {
  border-color: var(--color-success) !important;
  background: var(--color-success) !important;
}

.access-role-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

@media (max-width: 980px) {
  .access-matrix-header,
  .access-rolebar,
  .access-selected-role,
  .access-matrix-footer {
    align-items: stretch;
    flex-direction: column;
  }

  .access-matrix-header__search {
    flex-basis: auto;
    width: 100%;
    min-width: 0;
  }
}
</style>
