<template>
  <div class="users-view">
    <div class="users-card">
    <div class="users-header">
      <div class="users-header__copy">
        <h1 class="users-title">Пользователи <span>({{ users.length }})</span></h1>
        <p class="users-subtitle">Управление ролями, привязками и активным пользователем</p>
      </div>

      <div class="users-header__actions">
        <UiIconButton
          icon="fas fa-sync"
          label="Обновить список"
          size="md"
          @click="loadUsers"
        />
        <UiButton
          variant="primary"
          size="md"
          icon-left="fas fa-user-plus"
          @click="openCreate"
        >
          Новый пользователь
        </UiButton>
      </div>
    </div>

    <div class="users-list-shell">
      <div v-if="loading" class="users-list users-list--loading">
        <SkeletonLoader v-for="i in 10" :key="i" height="52px" />
      </div>

      <UiEmptyState
        v-else-if="!users.length"
        class="users-empty-state"
        icon="fas fa-user-slash"
        title="Пользователей пока нет"
        description="Создайте первого пользователя, чтобы назначать роли и привязки к компаниям."
      >
        <template #actions>
          <UiButton variant="primary" size="sm" icon-left="fas fa-user-plus" @click="openCreate">
            Создать пользователя
          </UiButton>
        </template>
      </UiEmptyState>

      <div v-else class="users-list">
        <article
          v-for="user in users"
          :key="user.id"
          class="user-card"
          :class="{ 'is-current': user.id === activeUserId }"
        >
          <div class="user-card__main">
            <div class="user-card__identity">
              <div class="user-avatar-wrap">
                <UiAvatar :name="user.full_name" :src="user.avatar_url" size="lg" />
                <span
                  class="user-avatar__status"
                  :class="user.is_active ? 'is-active' : 'is-inactive'"
                  :title="user.is_active ? 'Активен' : 'Отключен'"
                ></span>
              </div>

              <div class="user-card__identity-text">
                <div class="user-card__name-row">
                  <h3>{{ user.full_name }}</h3>
                  <span v-if="user.id === activeUserId" class="user-card__current-badge">Выбран</span>
                </div>
                <a class="user-card__email" :href="'mailto:' + user.email">{{ user.email }}</a>
              </div>
            </div>

            <div class="user-card__field">
              <span class="user-card__label">Роль</span>
              <div class="user-card__value">
                <span class="user-role-pill">{{ getRoleName(user.role_id) }}</span>
              </div>
            </div>

            <div class="user-card__field">
              <span class="user-card__label">Руководитель</span>
              <div class="user-card__links">
                <span
                  v-for="link in getUserLinks(user.id, 'leader')"
                  :key="link.id"
                  class="company-chip"
                >
                  <span class="company-chip__text">{{ link.company_name || link.company_id }}</span>
                  <button class="company-chip__remove" type="button" title="Удалить привязку" @click.stop="removeCompanyLink(link)">
                    <i class="fas fa-times"></i>
                  </button>
                </span>
                <button class="company-chip company-chip--add" type="button" title="Добавить привязку" @click="openLinkModal(user, 'leader')">
                  <i class="fas fa-plus"></i>
                </button>
              </div>
            </div>

            <div class="user-card__field">
              <span class="user-card__label">Сотрудник</span>
              <div class="user-card__links">
                <span
                  v-for="link in getUserLinks(user.id, 'employee')"
                  :key="link.id"
                  class="company-chip"
                >
                  <span class="company-chip__text">{{ link.company_name || link.company_id }}</span>
                  <button class="company-chip__remove" type="button" title="Удалить привязку" @click.stop="removeCompanyLink(link)">
                    <i class="fas fa-times"></i>
                  </button>
                </span>
                <button class="company-chip company-chip--add" type="button" title="Добавить привязку" @click="openLinkModal(user, 'employee')">
                  <i class="fas fa-plus"></i>
                </button>
              </div>
            </div>

            <div class="user-card__field">
              <span class="user-card__label">Заказчик</span>
              <div class="user-card__links">
                <span
                  v-for="link in getUserLinks(user.id, 'customer')"
                  :key="link.id"
                  class="company-chip"
                >
                  <span class="company-chip__text">{{ link.company_name || link.company_id }}</span>
                  <button class="company-chip__remove" type="button" title="Удалить привязку" @click.stop="removeCompanyLink(link)">
                    <i class="fas fa-times"></i>
                  </button>
                </span>
                <button class="company-chip company-chip--add" type="button" title="Добавить привязку" @click="openLinkModal(user, 'customer')">
                  <i class="fas fa-plus"></i>
                </button>
              </div>
            </div>
          </div>

          <div class="user-card__actions">
            <UiIconButton
              icon="fas fa-check"
              :label="user.id === activeUserId ? 'Текущий активный пользователь' : 'Сделать активным'"
              :variant="user.id === activeUserId ? 'primary' : 'default'"
              :disabled="user.id === activeUserId"
              @click="setActiveUser(user)"
            />
            <UiIconButton
              icon="fas fa-edit"
              label="Редактировать"
              @click="editUser(user)"
            />
            <UiIconButton
              icon="fas fa-trash"
              label="Удалить"
              variant="danger"
              @click="deleteUser(user)"
            />
          </div>
        </article>
      </div>
    </div>
    </div>

    <UiModal
      v-model="showModal"
      :title="isEditing ? 'Редактировать пользователя' : 'Создать пользователя'"
      size="sm"
    >
      <div class="users-form">
        <UiInput v-model="userForm.full_name" label="ФИО *" required />
        <UiInput v-model="userForm.email" type="email" label="Email *" required />
        <UiSelect v-model="userForm.role_id" label="Роль" :options="roleOptions" />
        <UiInput
          v-model="userForm.password"
          type="password"
          :label="isEditing ? 'Пароль (оставьте пустым, чтобы не менять)' : 'Пароль *'"
          :required="!isEditing"
        />
        <label class="users-checkbox">
          <input v-model="userForm.is_active" type="checkbox">
          <span>Пользователь активен</span>
        </label>
      </div>

      <template #footer>
        <UiButton variant="secondary" @click="closeModal">Отмена</UiButton>
        <UiButton variant="primary" :loading="saving" @click="saveUser">
          {{ isEditing ? 'Сохранить' : 'Создать' }}
        </UiButton>
      </template>
    </UiModal>

    <UiModal
      v-model="showLinkModal"
      :title="linkModalTitle"
      size="sm"
    >
      <div class="users-form">
        <div class="users-form__field">
          <label class="users-form__label">Контрагент *</label>
          <CompanySmartSelect
            v-model="linkForm.company_id"
            :options="linkModalCompanies"
            placeholder="Найти контрагента"
          />
        </div>
      </div>

      <template #footer>
        <UiButton variant="secondary" @click="closeLinkModal">Отмена</UiButton>
        <UiButton variant="primary" :loading="linkSaving" @click="saveCompanyLink">
          Добавить
        </UiButton>
      </template>
    </UiModal>
  </div>
</template>

<script>
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'
import SkeletonLoader from '../components/ui/SkeletonLoader.vue'
import CompanySmartSelect from '../components/ui/CompanySmartSelect.vue'
import {
  UiAvatar,
  UiButton,
  UiEmptyState,
  UiIconButton,
  UiInput,
  UiModal,
  UiSelect
} from '../components/ui'
import { getActiveUser, saveActiveUser } from '../utils/permissions'
import { useToast } from '../composables/useToast'
import { api } from '../services/api'
import { useUsersStore } from '../stores/users'
import { useRolesStore } from '../stores/roles'
import { useCompaniesStore } from '../stores/companies'

export default {
  name: 'Users',
  components: {
    SkeletonLoader,
    CompanySmartSelect,
    UiAvatar,
    UiButton,
    UiEmptyState,
    UiIconButton,
    UiInput,
    UiModal,
    UiSelect
  },
  setup() {
    const { success: toastSuccess, error: toastError } = useToast()
    const usersStore = useUsersStore()
    const rolesStore = useRolesStore()
    const companiesStore = useCompaniesStore()

    const users = ref([])
    const roles = ref([])
    const companies = ref([])
    const companyLinks = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const showModal = ref(false)
    const isEditing = ref(false)
    const activeUserId = ref(getActiveUser()?.id || '')
    const showLinkModal = ref(false)
    const linkSaving = ref(false)

    const userForm = ref({
      id: '',
      full_name: '',
      email: '',
      role_id: '',
      password: '',
      is_active: true
    })

    const linkForm = ref({
      user_id: '',
      link_type: '',
      company_id: ''
    })

    const linkModalTitle = computed(() => {
      if (linkForm.value.link_type === 'leader') return 'Привязка руководителя'
      if (linkForm.value.link_type === 'employee') return 'Привязка сотрудника'
      if (linkForm.value.link_type === 'customer') return 'Привязка заказчика'
      return 'Привязка к контрагенту'
    })

    const linkModalCompanies = computed(() => {
      if (linkForm.value.link_type !== 'customer') {
        return companies.value
      }
      return companies.value.filter((company) => company.type === 'customer')
    })

    const roleOptions = computed(() => [
      { value: '', label: 'Без роли' },
      ...roles.value.map((role) => ({ value: role.id, label: role.name }))
    ])

    const loadUsers = async () => {
      loading.value = true
      try {
        await usersStore.refresh()
        users.value = usersStore.items
      } catch (error) {
        console.error('Error loading users:', error)
        users.value = []
        toastError('Не удалось загрузить пользователей')
      } finally {
        loading.value = false
      }
    }

    const loadRoles = async () => {
      try {
        await rolesStore.ensureLoaded()
        roles.value = rolesStore.items
      } catch (error) {
        console.error('Error loading roles:', error)
        roles.value = []
      }
    }

    const loadCompanies = async () => {
      try {
        await companiesStore.ensureLoaded()
        companies.value = companiesStore.items
      } catch (error) {
        console.error('Error loading companies:', error)
        companies.value = []
      }
    }

    const loadCompanyLinks = async () => {
      try {
        companyLinks.value = await api.users.listCompanyLinks()
      } catch (error) {
        console.error('Error loading company links:', error)
        companyLinks.value = []
      }
    }

    const openCreate = () => {
      showModal.value = true
      isEditing.value = false
      userForm.value = {
        id: '',
        full_name: '',
        email: '',
        role_id: '',
        password: '',
        is_active: true
      }
    }

    const editUser = (user) => {
      showModal.value = true
      isEditing.value = true
      userForm.value = {
        id: user.id,
        full_name: user.full_name,
        email: user.email,
        role_id: user.role_id || '',
        password: '',
        is_active: user.is_active
      }
    }

    const getUserLinks = (userId, linkType) => {
      return companyLinks.value.filter(
        (link) => link.user_id === userId && link.link_type === linkType
      )
    }

    const openLinkModal = (user, linkType) => {
      linkForm.value = {
        user_id: user.id,
        link_type: linkType,
        company_id: ''
      }
      showLinkModal.value = true
    }

    const closeLinkModal = () => {
      showLinkModal.value = false
      linkForm.value = {
        user_id: '',
        link_type: '',
        company_id: ''
      }
    }

    const saveCompanyLink = async () => {
      if (!linkForm.value.user_id || !linkForm.value.link_type || !linkForm.value.company_id) {
        toastError('Выберите контрагента')
        return
      }

      const exists = getUserLinks(linkForm.value.user_id, linkForm.value.link_type)
        .some((link) => link.company_id === linkForm.value.company_id)
      if (exists) {
        toastError('Этот контрагент уже добавлен')
        return
      }

      linkSaving.value = true
      try {
        await api.users.addCompanyLink(linkForm.value.user_id, {
          company_id: linkForm.value.company_id,
          link_type: linkForm.value.link_type
        })
        await loadCompanyLinks()
        closeLinkModal()
        toastSuccess('Привязка добавлена')
      } catch (error) {
        console.error('Error saving company link:', error)
        toastError('Ошибка сохранения привязки')
      } finally {
        linkSaving.value = false
      }
    }

    const removeCompanyLink = async (link) => {
      if (!window.confirm('Удалить привязку к контрагенту?')) {
        return
      }
      try {
        await api.users.removeCompanyLink(link.user_id, link.id)
        await loadCompanyLinks()
        toastSuccess('Привязка удалена')
      } catch (error) {
        console.error('Error deleting company link:', error)
        toastError('Ошибка удаления привязки')
      }
    }

    const saveUser = async () => {
      if (!userForm.value.full_name.trim() || !userForm.value.email.trim()) {
        toastError('Имя и email обязательны')
        return
      }

      saving.value = true
      try {
        if (isEditing.value) {
          const payload = {
            full_name: userForm.value.full_name,
            email: userForm.value.email,
            role_id: userForm.value.role_id || null,
            is_active: userForm.value.is_active
          }
          if (userForm.value.password) {
            payload.password = userForm.value.password
          }
          await api.users.update(userForm.value.id, payload)
        } else {
          await api.users.create({
            full_name: userForm.value.full_name,
            email: userForm.value.email,
            role_id: userForm.value.role_id || null,
            password: userForm.value.password,
            is_active: userForm.value.is_active
          })
        }

        await loadUsers()
        closeModal()
        toastSuccess(isEditing.value ? 'Пользователь сохранен' : 'Пользователь создан')
      } catch (error) {
        console.error('Error saving user:', error)
        toastError('Ошибка сохранения пользователя')
      } finally {
        saving.value = false
      }
    }

    const deleteUser = async (user) => {
      if (!window.confirm(`Удалить пользователя "${user.full_name}"?`)) {
        return
      }
      try {
        await api.users.remove(user.id)
        await loadUsers()
        toastSuccess('Пользователь удален')
      } catch (error) {
        console.error('Error deleting user:', error)
        toastError('Ошибка удаления пользователя')
      }
    }

    const buildPermissionsMap = (list) => {
      const map = {}
      list.forEach((p) => {
        map[p.section] = { read_all: !!p.read_all, read_assigned: !!p.read_assigned }
      })
      return map
    }

    const setActiveUser = async (user) => {
      let permissions = {}
      if (user.role_id) {
        try {
          const permsList = await api.roles.getPermissions(user.role_id)
          permissions = buildPermissionsMap(permsList || [])
        } catch (error) {
          console.error('Error loading permissions:', error)
          permissions = {}
        }
      }
      saveActiveUser(
        {
          id: user.id,
          full_name: user.full_name,
          email: user.email,
          role_id: user.role_id || null,
          avatar_url: user.avatar_url || null,
          rating: user.rating || 0,
          rating_count: user.rating_count || 0
        },
        permissions
      )
      activeUserId.value = user.id
      toastSuccess(`Активный пользователь: ${user.full_name}`)
    }

    const closeModal = () => {
      showModal.value = false
      isEditing.value = false
    }

    const getRoleName = (roleId) => {
      if (!roleId) return 'Без роли'
      const role = roles.value.find((item) => item.id === roleId)
      return role?.name || 'Без роли'
    }

    onMounted(() => {
      loadUsers()
      loadRoles()
      loadCompanies()
      loadCompanyLinks()
      activeUserId.value = getActiveUser()?.id || ''
    })

    return {
      users,
      roles,
      companies,
      linkModalCompanies,
      companyLinks,
      loading,
      saving,
      showModal,
      isEditing,
      activeUserId,
      showLinkModal,
      linkSaving,
      userForm,
      linkForm,
      linkModalTitle,
      roleOptions,
      loadUsers,
      openCreate,
      editUser,
      saveUser,
      deleteUser,
      setActiveUser,
      closeModal,
      getUserLinks,
      openLinkModal,
      closeLinkModal,
      saveCompanyLink,
      removeCompanyLink,
      getRoleName
    }
  }
}
</script>

<style scoped>
/* ── Tasks reference standard: one unified card, compact header band,
   flush dense list rows. ── */
.users-view {
  --apr-card-bg: rgba(255, 255, 255, 0.97);
  --apr-card-border: rgba(216, 224, 240, 0.92);
  --apr-card-shadow: 0 18px 42px rgba(15, 23, 42, 0.06);
  --apr-radius: 20px;
  --apr-ink: #0a1629;
  --apr-muted: #7d8592;
  --apr-soft: #f6f8fb;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  padding: 12px;
}

/* The single card */
.users-card {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  background: var(--apr-card-bg);
  border: 1px solid var(--apr-card-border);
  border-radius: var(--apr-radius);
  box-shadow: var(--apr-card-shadow);
  overflow: hidden;
}

/* Header band */
.users-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  flex-wrap: wrap;
  padding: 10px 16px;
  border-bottom: 1px solid var(--apr-card-border);
}

.users-header__copy {
  min-width: 0;
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
}

.users-title {
  margin: 0;
  font-size: 1.15rem;
  line-height: var(--leading-tight);
  font-weight: 800;
  color: var(--apr-ink);
}

.users-title span {
  color: var(--apr-muted);
  font-weight: 700;
}

.users-subtitle {
  margin: 0;
  color: var(--apr-muted);
  font-size: 0.8rem;
}

.users-header__actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.users-list-shell {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.users-list {
  display: flex;
  flex-direction: column;
  gap: 0;
  overflow: auto;
  flex: 1;
}

.users-list--loading {
  gap: 1px;
  padding: 0;
}

.user-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-3);
  padding: 9px 16px;
  background: transparent;
  border: 0;
  border-bottom: 1px solid var(--apr-card-border);
  transition: background-color var(--dur-fast) var(--ease-out);
}

.user-card:hover {
  background: var(--apr-soft);
}

.user-card.is-current {
  background: var(--color-primary-soft);
  box-shadow: inset 3px 0 0 var(--color-primary);
}

.user-card__main {
  display: grid;
  grid-template-columns: minmax(240px, 1.35fr) minmax(140px, 0.7fr) minmax(200px, 1fr) minmax(200px, 1fr) minmax(200px, 1fr);
  gap: var(--space-3);
  align-items: center;
  min-width: 0;
}

.user-card__identity {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
}

.user-avatar-wrap {
  position: relative;
  flex-shrink: 0;
}

.user-avatar__status {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid var(--color-surface);
  box-shadow: var(--shadow-xs);
}

.user-avatar__status.is-active {
  background: var(--color-success);
}

.user-avatar__status.is-inactive {
  background: var(--color-danger);
}

.user-card__identity-text {
  min-width: 0;
}

.user-card__name-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
}

.user-card__name-row h3 {
  margin: 0;
  font-size: 0.92rem;
  line-height: var(--leading-tight);
  font-weight: 700;
  color: var(--apr-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-card__current-badge {
  display: inline-flex;
  align-items: center;
  min-height: 20px;
  padding: 0 8px;
  border-radius: var(--radius-pill);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 0.66rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.user-card__email {
  display: inline-block;
  margin-top: 1px;
  max-width: 100%;
  color: var(--apr-muted);
  font-size: 0.78rem;
  text-decoration: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-card__email:hover {
  color: var(--color-primary);
}

.user-card__field {
  min-width: 0;
}

.user-card__label {
  display: block;
  margin-bottom: 3px;
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--apr-muted);
}

.user-card__value {
  min-height: 24px;
  display: flex;
  align-items: center;
}

.user-role-pill {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 0 10px;
  border-radius: var(--radius-pill);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 0.72rem;
  font-weight: 700;
}

.user-card__links {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  align-items: center;
  min-height: 26px;
}

.company-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
  min-height: 24px;
  padding: 0 9px;
  border-radius: var(--radius-pill);
  background: var(--apr-soft);
  border: 1px solid var(--apr-card-border);
  color: #5f6b7c;
  font-size: 0.72rem;
  font-weight: 600;
}

.company-chip__text {
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.company-chip__remove {
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  padding: 0;
  line-height: 1;
  cursor: pointer;
}

.company-chip__remove:hover {
  color: var(--color-danger);
}

.company-chip--add {
  justify-content: center;
  min-width: 32px;
  color: var(--color-primary);
  background: var(--color-primary-soft);
  border-color: var(--color-primary-soft-strong);
  cursor: pointer;
}

.user-card__actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.users-empty-state {
  flex: 1 1 auto;
}

.users-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.users-form__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.users-form__label {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
}

.users-checkbox {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text);
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  cursor: pointer;
}

.users-checkbox input {
  width: 16px;
  height: 16px;
  accent-color: var(--color-primary);
}

@media (max-width: 1400px) {
  .user-card__main {
    grid-template-columns: minmax(240px, 1.3fr) minmax(140px, 0.75fr) minmax(190px, 1fr) minmax(190px, 1fr) minmax(190px, 1fr);
  }
}

@media (max-width: 1180px) {
  .user-card {
    grid-template-columns: 1fr;
  }

  .user-card__actions {
    justify-content: flex-end;
  }

  .user-card__main {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  }

  .user-card__identity {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  .users-view {
    padding: var(--space-3);
    border-radius: var(--radius-xl);
  }

  .users-header {
    flex-direction: column;
    align-items: stretch;
  }

  .users-header__actions {
    width: 100%;
  }

  .users-title {
    font-size: var(--text-2xl);
  }

  .user-card {
    padding: var(--space-4);
  }

  .user-card__main {
    grid-template-columns: 1fr;
    gap: var(--space-3);
  }

  .user-card__identity {
    grid-column: auto;
  }

  .user-card__actions {
    width: 100%;
    justify-content: flex-end;
  }

  .company-chip__text {
    max-width: 140px;
  }
}
</style>
