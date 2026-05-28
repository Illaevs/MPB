<template>
  <div class="leads-view d-flex flex-column h-100">
    <div class="list-card flex-grow-1 d-flex flex-column overflow-hidden">
      <!-- Compact single-line toolbar -->
      <div class="list-card__toolbar toolbar-card">
      <div class="toolbar-row">
        <h2 class="m-0 toolbar-title">Лиды</h2>

        <!-- Status filter dropdown -->
        <UiChipFilter
          v-model="filters.status"
          :options="LEAD_STATUS_OPTIONS"
          placeholder="Все статусы"
          empty-icon="fas fa-flag"
          @update:model-value="resetAndLoad"
        />

        <div class="leads-search-wrap">
          <UiInput
            v-model="filters.search"
            size="sm"
            placeholder="Поиск по названию, объекту, адресу..."
            icon-left="fas fa-search"
            clearable
            @update:modelValue="debouncedSearch"
            @clear="resetAndLoad"
          />
        </div>

        <div class="more-filter-wrap">
          <button class="btn btn-sm" :class="hasMoreFilters ? 'btn-primary' : 'btn-icon'" @click="moreFiltersOpen = !moreFiltersOpen" title="Доп. фильтры">
            <i class="fas fa-sliders-h"></i>
            <span v-if="hasMoreFilters" class="filter-active-dot">{{ activeMoreFiltersCount }}</span>
          </button>
          <transition name="pop">
            <div v-if="moreFiltersOpen" class="advanced-filters-pop" v-click-outside="() => moreFiltersOpen = false">
              <div class="advanced-filters-pop__head">
                <span><i class="fas fa-sliders-h mr-1"></i>Доп. фильтры</span>
                <button v-if="hasMoreFilters" class="filter-pill filter-pill--clear" @click="clearAdvancedFilters">
                  <i class="fas fa-rotate-left mr-1"></i>Сбросить
                </button>
              </div>
              <div class="advanced-filters">
                <div class="form-group form-group--full">
                  <label>Наша компания</label>
                  <CompanySmartSelect v-model="filters.our_company_id" :options="internalCompanies" placeholder="Любая" @update:modelValue="resetAndLoad" />
                </div>
                <div class="form-group form-group--full">
                  <label>Заказчик</label>
                  <CompanySmartSelect v-model="filters.customer_id" :options="customerCompanies" placeholder="Любой" @update:modelValue="resetAndLoad" />
                </div>
              </div>
            </div>
          </transition>
        </div>

        <div class="leads-pager">
          <UiIconButton
            icon="fas fa-chevron-left"
            label="Назад"
            size="sm"
            :disabled="page === 1 || loading"
            @click="goToPage(page - 1)"
          />
          <span class="pager-label">{{ page }}<span class="text-muted">/{{ totalPages }}</span></span>
          <UiIconButton
            icon="fas fa-chevron-right"
            label="Вперёд"
            size="sm"
            :disabled="page >= totalPages || loading"
            @click="goToPage(page + 1)"
          />
          <select v-model.number="pageSize" class="pager-size" @change="onPageSizeChange">
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
            <option :value="200">200</option>
          </select>
        </div>

        <div class="view-switcher">
          <button
            type="button"
            class="view-btn"
            :class="{ active: viewMode === 'table' }"
            @click="setViewMode('table')"
            title="Список"
          ><i class="fas fa-list"></i></button>
          <button
            type="button"
            class="view-btn"
            :class="{ active: viewMode === 'kanban' }"
            @click="setViewMode('kanban')"
            title="Канбан"
          ><i class="fas fa-table-columns"></i></button>
        </div>

        <UiButton variant="primary" size="sm" icon-left="fas fa-plus" @click="openCreateModal">
          Новый
        </UiButton>
      </div>

      <!-- Active filter pills -->
      <div v-if="hasActiveFilters" class="filter-pills">
        <span v-if="filters.search" class="filter-pill">
          Поиск: «{{ filters.search }}»
          <button type="button" @click="filters.search = ''; resetAndLoad()"><i class="fas fa-times"></i></button>
        </span>
        <span v-if="filters.status" class="filter-pill" :class="`lead-status-${filters.status}`">
          {{ statusLabel(filters.status) }}
          <button type="button" @click="setStatus('')"><i class="fas fa-times"></i></button>
        </span>
        <span v-if="filters.our_company_id" class="filter-pill">
          Наша: {{ getCompanyName(filters.our_company_id) }}
          <button type="button" @click="filters.our_company_id = ''; resetAndLoad()"><i class="fas fa-times"></i></button>
        </span>
        <span v-if="filters.customer_id" class="filter-pill">
          Заказчик: {{ getCompanyName(filters.customer_id) }}
          <button type="button" @click="filters.customer_id = ''; resetAndLoad()"><i class="fas fa-times"></i></button>
        </span>
        <button type="button" class="filter-pill filter-pill--clear" @click="clearAllFilters">
          <i class="fas fa-rotate-left mr-1"></i>Сбросить все
        </button>
      </div>
      </div>

    <!-- Floating bulk-bar -->
    <transition name="bulk-bar">
      <div v-if="selectedIds.size > 0" class="bulk-bar">
        <div class="bulk-bar__info">
          <i class="fas fa-check-square"></i>
          <span>Выбрано: <b>{{ selectedIds.size }}</b></span>
        </div>
        <div class="bulk-bar__actions">
          <select class="bulk-bar__select" @change="bulkSetStatus($event.target.value); $event.target.value = ''" :disabled="bulkBusy">
            <option value="" disabled selected>Сменить статус...</option>
            <option v-for="s in KANBAN_STATUSES.filter(s => s.key !== 'converted')" :key="s.key" :value="s.key">{{ s.label }}</option>
          </select>
          <button class="btn btn-sm btn-outline-danger" :disabled="bulkBusy" @click="bulkDelete">
            <i class="fas fa-trash mr-1"></i> Удалить
          </button>
          <button class="btn btn-sm btn-outline-secondary" @click="clearSelection">Снять выбор</button>
        </div>
      </div>
    </transition>

    <!-- Content -->
    <div class="list-card__body leads-content-card flex-grow-1 overflow-hidden d-flex flex-column">
      <div v-if="loading" class="p-3 d-flex flex-column gap-2">
        <SkeletonLoader v-for="i in 6" :key="i" height="48px" />
      </div>

      <UiEmptyState
        v-else-if="!leads.length"
        icon="fas fa-folder-open"
        :title="hasActiveFilters ? 'Ничего не найдено по фильтру' : 'Лидов пока нет'"
        :description="hasActiveFilters ? 'Попробуйте изменить или сбросить фильтры' : 'Создайте первый лид, чтобы начать работу'"
      >
        <template #actions>
          <UiButton
            v-if="hasActiveFilters"
            variant="secondary"
            size="sm"
            icon-left="fas fa-rotate-left"
            @click="clearAllFilters"
          >Сбросить фильтры</UiButton>
          <UiButton
            variant="primary"
            size="sm"
            icon-left="fas fa-plus"
            @click="openCreateModal"
          >Создать лид</UiButton>
        </template>
      </UiEmptyState>

      <!-- TABLE VIEW -->
      <div v-else-if="viewMode === 'table'" class="leads-table-scroll">
        <table class="leads-table">
          <thead>
            <tr>
              <th class="check-col">
                <input
                  type="checkbox"
                  :checked="allOnPageSelected"
                  :indeterminate.prop="someOnPageSelected && !allOnPageSelected"
                  @change="toggleAllOnPage"
                />
              </th>
              <th class="sortable" @click="toggleSort('title')">
                <span>Название</span>
                <i v-if="sortBy === 'title'" class="fas" :class="sortDir === 'asc' ? 'fa-arrow-up-short-wide' : 'fa-arrow-down-wide-short'"></i>
              </th>
              <th>Объект</th>
              <th class="sortable" @click="toggleSort('status')">
                <span>Статус</span>
                <i v-if="sortBy === 'status'" class="fas" :class="sortDir === 'asc' ? 'fa-arrow-up-short-wide' : 'fa-arrow-down-wide-short'"></i>
              </th>
              <th>Заказчик</th>
              <th>Ответственный</th>
              <th class="text-right sortable" @click="toggleSort('total_value')">
                <span>Сумма</span>
                <i v-if="sortBy === 'total_value'" class="fas" :class="sortDir === 'asc' ? 'fa-arrow-up-short-wide' : 'fa-arrow-down-wide-short'"></i>
              </th>
              <th class="sortable" @click="toggleSort('created_at')">
                <span>Создан</span>
                <i v-if="sortBy === 'created_at'" class="fas" :class="sortDir === 'asc' ? 'fa-arrow-up-short-wide' : 'fa-arrow-down-wide-short'"></i>
              </th>
              <th class="actions-th"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="lead in leads"
              :key="lead.id"
              class="leads-row"
              :class="{ selected: selectedIds.has(lead.id) }"
              @click="openDetail(lead)"
            >
              <td class="check-col" @click.stop>
                <input type="checkbox" :checked="selectedIds.has(lead.id)" @change="toggleSelected(lead.id)" />
              </td>
              <td class="leads-title-cell">
                <div class="leads-title-cell__primary">{{ lead.title }}</div>
                <div v-if="lead.address" class="leads-title-cell__address">
                  <i class="fas fa-map-marker-alt"></i>{{ lead.address }}
                </div>
              </td>
              <td class="text-muted">{{ lead.obj_name || '—' }}</td>
              <td @click.stop>
                <div class="inline-status-wrap">
                  <button
                    type="button"
                    class="lead-status-badge lead-status-badge--editable"
                    :class="`lead-status-${lead.status}`"
                    :disabled="inlineStatusBusyId === lead.id"
                    @click.stop="inlineStatusOpenId = inlineStatusOpenId === lead.id ? null : lead.id"
                  >
                    <span class="status-dot"></span>{{ statusLabel(lead.status) }}
                    <i v-if="inlineStatusBusyId === lead.id" class="fas fa-spinner fa-spin ml-1"></i>
                    <i v-else class="fas fa-caret-down ml-1"></i>
                  </button>
                  <transition name="pop">
                    <div
                      v-if="inlineStatusOpenId === lead.id"
                      class="inline-status-menu"
                      v-click-outside="() => inlineStatusOpenId = null"
                    >
                      <button
                        v-for="opt in KANBAN_STATUSES.filter(s => s.key !== 'converted')"
                        :key="opt.key"
                        type="button"
                        class="inline-status-menu__item"
                        :class="[`lead-status-${opt.key}`, { active: lead.status === opt.key }]"
                        @click.stop="changeLeadStatus(lead, opt.key)"
                      >
                        <span class="status-dot"></span>{{ opt.label }}
                        <i v-if="lead.status === opt.key" class="fas fa-check ml-auto"></i>
                      </button>
                    </div>
                  </transition>
                </div>
              </td>
              <td class="text-muted">{{ getCompanyName(lead.customer_id) || '—' }}</td>
              <td class="leads-assignee-cell">
                <template v-if="lead.responsible_user_id">
                  <span class="user-avatar xs" :class="`avatar-${avatarColor(getUserName(lead.responsible_user_id))}`">
                    {{ initials(getUserName(lead.responsible_user_id)) }}
                  </span>
                  <span class="text-muted small">{{ getUserName(lead.responsible_user_id) }}</span>
                </template>
                <span v-else class="text-muted">—</span>
              </td>
              <td class="text-right leads-amount">
                <span v-if="lead.total_value">{{ formatCurrency(lead.total_value) }}</span>
                <span v-else class="text-muted">—</span>
              </td>
              <td class="leads-date text-muted">{{ formatDate(lead.created_at) }}</td>
              <td class="actions-cell" @click.stop>
                <UiIconButton
                  icon="fas fa-ellipsis-vertical"
                  label="Действия"
                  size="sm"
                  @click.stop="onRowMenuToggle($event, lead.id)"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- KANBAN VIEW -->
      <div v-else class="kanban-board">
        <div
          v-for="status in KANBAN_STATUSES"
          :key="status.key"
          class="kanban-column"
          :class="{ 'kanban-column--drop': dragOverStatus === status.key }"
          @dragover.prevent="dragOverStatus = status.key"
          @dragleave="dragOverStatus = null"
          @drop="onKanbanDrop($event, status.key)"
        >
          <div class="kanban-header" :class="`lead-status-${status.key}`">
            <span class="status-dot"></span>
            <span class="kanban-header__label">{{ status.label }}</span>
            <span class="kanban-header__count">{{ leadsByStatus[status.key].length }}</span>
          </div>
          <div class="kanban-items">
            <div
              v-for="lead in leadsByStatus[status.key]"
              :key="lead.id"
              class="kanban-card"
              draggable="true"
              @dragstart="onDragStart($event, lead)"
              @click="openDetail(lead)"
            >
              <div class="kanban-card__head">
                <span class="kanban-card__title">{{ lead.title }}</span>
                <UiIconButton
                  icon="fas fa-ellipsis-vertical"
                  label="Действия"
                  size="xs"
                  @click.stop="onRowMenuToggle($event, lead.id)"
                />
              </div>
              <div v-if="lead.address" class="kanban-card__meta">
                <i class="fas fa-map-marker-alt"></i>{{ lead.address }}
              </div>
              <div class="kanban-card__foot">
                <span class="kanban-card__amount">{{ lead.total_value ? formatCurrency(lead.total_value) : '—' }}</span>
                <span v-if="lead.responsible_user_id" class="user-avatar xs" :class="`avatar-${avatarColor(getUserName(lead.responsible_user_id))}`" :title="getUserName(lead.responsible_user_id)">
                  {{ initials(getUserName(lead.responsible_user_id)) }}
                </span>
              </div>
            </div>
            <div v-if="!leadsByStatus[status.key].length" class="kanban-empty">Перетащите сюда</div>
          </div>
        </div>
      </div>

      <div v-if="!loading && leads.length" class="leads-footer">
        <span class="text-muted small">Показано {{ Math.min((page - 1) * pageSize + 1, total) }}–{{ Math.min(page * pageSize, total) }} из {{ total }}</span>
      </div>
    </div>
    </div>

    <!-- Teleported row action menu -->
    <Teleport to="body">
      <transition name="pop">
        <div
          v-if="openRowMenuId && rowMenuTarget"
          class="more-menu more-menu--floating"
          :style="{ top: rowMenuCoords.top + 'px', left: rowMenuCoords.left + 'px' }"
          v-click-outside="() => openRowMenuId = null"
          @click.stop
        >
          <button type="button" class="more-menu-item" @click="openDetail(rowMenuTarget); openRowMenuId = null">
            <i class="fas fa-up-right-from-square mr-2"></i>Открыть карточку
          </button>
          <button type="button" class="more-menu-item" @click="openEditModal(rowMenuTarget); openRowMenuId = null">
            <i class="fas fa-edit mr-2"></i>Редактировать
          </button>
          <button
            v-if="rowMenuTarget.status !== 'converted'"
            type="button"
            class="more-menu-item"
            @click="convertLead(rowMenuTarget); openRowMenuId = null"
          >
            <i class="fas fa-arrow-right-arrow-left mr-2"></i>Конвертировать в сделку
          </button>
          <div class="more-menu-divider"></div>
          <button type="button" class="more-menu-item more-menu-item--danger" @click="deleteLead(rowMenuTarget); openRowMenuId = null">
            <i class="fas fa-trash mr-2"></i>Удалить
          </button>
        </div>
      </transition>
    </Teleport>

    <!-- Lead form modal -->
    <LeadFormModal
      v-model="showFormModal"
      :lead="editingLead"
      :companies="companies"
      :internal-companies="internalCompanies"
      :users="users"
      :statuses="KANBAN_STATUSES_FOR_FORM"
      :saving="saving"
      @submit="onFormSubmit"
      @cancel="showFormModal = false"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, rawRequest } from '@/services/api'
import SkeletonLoader from '../components/ui/SkeletonLoader.vue'
import CompanySmartSelect from '../components/ui/CompanySmartSelect.vue'
import UiChipFilter from '../components/ui/UiChipFilter.vue'
import LeadFormModal from '../components/leads/LeadFormModal.vue'
import {
  UiButton,
  UiIconButton,
  UiInput,
  UiEmptyState,
} from '../components/ui'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'
import { getActiveUser, getStoredPermissions } from '../utils/permissions'
import { useCompaniesStore } from '../stores/companies'
import { useUsersStore } from '../stores/users'

const KANBAN_STATUSES = [
  { key: 'incoming',                  label: 'Входящие' },
  { key: 'no_work',                   label: 'В простое' },
  { key: 'proposal',                  label: 'Подготовка КП' },
  { key: 'waiting',                   label: 'Ожидание' },
  { key: 'customer_reject_internal',  label: 'Откл. (внутр.)' },
  { key: 'customer_reject_our',       label: 'Откл. (наши)' },
  { key: 'we_reject',                 label: 'Откл. нами' },
  { key: 'converted',                 label: 'Конверсия' },
]

const LEAD_STATUS_OPTIONS = [
  { value: 'incoming',                 label: 'Входящие',       color: '#1976d2' },
  { value: 'no_work',                  label: 'В простое',      color: '#607d8b' },
  { value: 'proposal',                 label: 'Подготовка КП',  color: '#f59e0b' },
  { value: 'waiting',                  label: 'Ожидание',       color: '#d97706' },
  { value: 'customer_reject_internal', label: 'Откл. (внутр.)', color: '#ef4444' },
  { value: 'customer_reject_our',      label: 'Откл. (наши)',   color: '#b91c1c' },
  { value: 'we_reject',                label: 'Откл. нами',     color: '#6b7280' },
  { value: 'converted',                label: 'Конверсия',      color: '#22c55e' },
]

const clickOutside = {
  beforeMount(el, binding) {
    el._co = (e) => { if (!(el === e.target || el.contains(e.target))) binding.value(e) }
    setTimeout(() => document.addEventListener('click', el._co), 0)
  },
  unmounted(el) { document.removeEventListener('click', el._co) }
}

export default {
  name: 'Leads',
  components: {
    SkeletonLoader, CompanySmartSelect, UiChipFilter, LeadFormModal,
    UiButton, UiIconButton, UiInput, UiEmptyState,
  },
  directives: { 'click-outside': clickOutside },
  setup() {
    const toast = useToast()
    const { confirm } = useConfirm()
    const route = useRoute()
    const router = useRouter()
    const companiesStore = useCompaniesStore()
    const usersStore = useUsersStore()

    const leads = ref([])
    const companies = ref([])
    const users = ref([])
    const total = ref(0)
    const loading = ref(false)
    const saving = ref(false)

    const filters = ref({
      search: '',
      status: '',
      our_company_id: '',
      customer_id: '',
    })

    const page = ref(1)
    const pageSize = ref(parseInt(localStorage.getItem('leads-page-size') || '20', 10) || 20)
    const sortBy = ref('created_at')
    const sortDir = ref('desc')
    const viewMode = ref(localStorage.getItem('leads-view') || 'table')

    const statusFilterOpen = ref(false)
    const moreFiltersOpen = ref(false)
    const showFormModal = ref(false)
    const editingLead = ref(null)

    const selectedIds = ref(new Set())
    const bulkBusy = ref(false)
    const inlineStatusOpenId = ref(null)
    const inlineStatusBusyId = ref(null)
    const openRowMenuId = ref(null)
    const rowMenuCoords = ref({ top: 0, left: 0 })
    const dragOverStatus = ref(null)
    let draggedLead = null
    let searchTimer = null

    const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
    const internalCompanies = computed(() => companies.value.filter(c => c.type === 'internal'))
    const customerCompanies = computed(() => companies.value.filter(c => c.type === 'customer'))

    const KANBAN_STATUSES_FOR_FORM = KANBAN_STATUSES.filter(s => s.key !== 'converted')

    const hasMoreFilters = computed(() => !!(filters.value.our_company_id || filters.value.customer_id))
    const activeMoreFiltersCount = computed(() => (filters.value.our_company_id ? 1 : 0) + (filters.value.customer_id ? 1 : 0))
    const hasActiveFilters = computed(() => !!(
      filters.value.search || filters.value.status || hasMoreFilters.value
    ))

    const normalizeId = (v) => v ? String(v).replace(/-/g, '').toLowerCase() : ''
    const statusLabel = (key) => KANBAN_STATUSES.find(s => s.key === key)?.label || key
    const getCompanyName = (id) => {
      if (!id) return ''
      const c = companies.value.find(item => normalizeId(item.id) === normalizeId(id))
      return c ? (c.name || c.short_name || '—') : ''
    }
    const getUserName = (id) => {
      if (!id) return ''
      const u = users.value.find(x => normalizeId(x.id) === normalizeId(id))
      return u ? (u.full_name || u.email || '—') : ''
    }
    const initials = (name) => {
      if (!name) return '?'
      const parts = String(name).trim().split(/\s+/).filter(Boolean)
      if (!parts.length) return '?'
      if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
      return (parts[0][0] + parts[1][0]).toUpperCase()
    }
    const avatarColor = (name) => {
      const palette = ['blue', 'teal', 'amber', 'pink', 'purple', 'green', 'red', 'indigo']
      if (!name) return palette[0]
      let h = 0
      for (let i = 0; i < name.length; i += 1) h = (h * 31 + name.charCodeAt(i)) | 0
      return palette[Math.abs(h) % palette.length]
    }
    const formatCurrency = (v) => new Intl.NumberFormat('ru-RU', {
      style: 'currency', currency: 'RUB', minimumFractionDigits: 0, maximumFractionDigits: 0,
    }).format(Number(v || 0))
    const formatDate = (v) => v ? new Date(v).toLocaleDateString('ru-RU') : '—'

    // URL sync
    const syncToUrl = () => {
      const q = {}
      if (filters.value.search) q.q = filters.value.search
      if (filters.value.status) q.status = filters.value.status
      if (filters.value.our_company_id) q.our = filters.value.our_company_id
      if (filters.value.customer_id) q.customer = filters.value.customer_id
      if (page.value > 1) q.page = String(page.value)
      if (pageSize.value !== 20) q.size = String(pageSize.value)
      if (sortBy.value !== 'created_at' || sortDir.value !== 'desc') q.sort = `${sortBy.value}:${sortDir.value}`
      if (viewMode.value !== 'table') q.view = viewMode.value
      router.replace({ query: q }).catch(() => {})
    }
    const restoreFromUrl = () => {
      const q = route.query || {}
      if (q.q) filters.value.search = String(q.q)
      if (q.status) filters.value.status = String(q.status)
      if (q.our) filters.value.our_company_id = String(q.our)
      if (q.customer) filters.value.customer_id = String(q.customer)
      if (q.page) page.value = parseInt(q.page, 10) || 1
      if (q.size) pageSize.value = parseInt(q.size, 10) || pageSize.value
      if (q.view === 'kanban') viewMode.value = 'kanban'
      if (q.sort) {
        const [by, dir] = String(q.sort).split(':')
        if (by) sortBy.value = by
        if (dir) sortDir.value = dir
      }
    }

    const loadLeads = async () => {
      loading.value = true
      try {
        const params = {
          skip: (page.value - 1) * pageSize.value,
          limit: pageSize.value,
          sort_by: sortBy.value,
          sort_dir: sortDir.value,
        }
        const f = filters.value
        if (f.search) params.search = f.search
        if (f.status) params.status = f.status
        if (f.our_company_id) params.our_company_id = f.our_company_id
        if (f.customer_id) params.customer_id = f.customer_id

        const permissions = getStoredPermissions()
        const leadPerms = permissions?.leads
        const activeUser = getActiveUser()
        if (leadPerms && !leadPerms.read_all && leadPerms.read_assigned && activeUser?.id) {
          params.responsible_user_id = activeUser.id
        }

        const response = await rawRequest({ method: 'get', url: '/api/v1/leads/', params })
        leads.value = Array.isArray(response.data) ? response.data : []
        const headerTotal = response.headers?.['x-total-count']
        total.value = headerTotal !== undefined ? (parseInt(headerTotal, 10) || 0) : leads.value.length
        syncToUrl()

        if (selectedIds.value.size) {
          const onPage = new Set(leads.value.map(l => l.id))
          const next = new Set()
          selectedIds.value.forEach(id => { if (onPage.has(id)) next.add(id) })
          selectedIds.value = next
        }
      } catch (error) {
        console.error('Leads load error:', error)
        toast.error('Не удалось загрузить лиды')
        leads.value = []
      } finally {
        loading.value = false
      }
    }

    const loadCompanies = async () => {
      try {
        await companiesStore.ensureLoaded()
        companies.value = companiesStore.items
      } catch (e) { /* noop */ }
    }
    const loadUsers = async () => {
      try {
        await usersStore.ensureLoaded()
        users.value = usersStore.items
      } catch (e) { /* noop */ }
    }

    const debouncedSearch = () => {
      clearTimeout(searchTimer)
      searchTimer = setTimeout(() => { page.value = 1; loadLeads() }, 300)
    }
    const resetAndLoad = () => { page.value = 1; loadLeads() }
    const setStatus = (s) => { filters.value.status = s; resetAndLoad() }
    const clearAdvancedFilters = () => { filters.value.our_company_id = ''; filters.value.customer_id = ''; resetAndLoad() }
    const clearAllFilters = () => {
      filters.value = { search: '', status: '', our_company_id: '', customer_id: '' }
      resetAndLoad()
    }
    const onPageSizeChange = () => {
      page.value = 1
      localStorage.setItem('leads-page-size', String(pageSize.value))
      loadLeads()
    }
    const goToPage = (p) => {
      page.value = Math.max(1, Math.min(p, totalPages.value))
      loadLeads()
    }
    const toggleSort = (field) => {
      if (sortBy.value === field) sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
      else { sortBy.value = field; sortDir.value = field === 'title' ? 'asc' : 'desc' }
      page.value = 1
      loadLeads()
    }

    const setViewMode = (mode) => {
      viewMode.value = mode
      localStorage.setItem('leads-view', mode)
      syncToUrl()
    }

    // CRUD
    const openCreateModal = () => { editingLead.value = null; showFormModal.value = true }
    const openEditModal = (lead) => { editingLead.value = lead; showFormModal.value = true }
    const openDetail = (lead) => router.push(`/leads/${lead.id}`)

    const onFormSubmit = async ({ isEditing, payload }) => {
      saving.value = true
      try {
        // Do not include id, created_at, updated_at in PUT body
        const { id, created_at, updated_at, ...basePayload } = payload
        if (isEditing) {
          await api.leads.update(editingLead.value.id, basePayload)
        } else {
          await api.leads.create(basePayload)
        }
        toast.success(isEditing ? 'Лид сохранён' : 'Лид создан')
        showFormModal.value = false
        editingLead.value = null
        await loadLeads()
      } catch (e) {
        toast.error(e?.response?.data?.detail || 'Не удалось сохранить лид')
      } finally {
        saving.value = false
      }
    }

    const deleteLead = async (lead) => {
      const ok = await confirm({
        title: 'Удалить лид?',
        message: `«${lead.title}» будет удалён безвозвратно.`,
        confirmText: 'Удалить',
        variant: 'danger',
      })
      if (!ok) return
      try {
        await api.leads.remove(lead.id)
        toast.success('Лид удалён')
        if (leads.value.length === 1 && page.value > 1) page.value -= 1
        await loadLeads()
      } catch (e) {
        toast.error(e?.response?.data?.detail || 'Не удалось удалить лид')
      }
    }

    const convertLead = async (lead) => {
      const ok = await confirm({
        title: 'Конвертировать в сделку?',
        message: `На основе лида «${lead.title}» будет создана сделка с теми же данными и продуктами. Это действие необратимо.`,
        confirmText: 'Конвертировать',
        variant: 'primary',
      })
      if (!ok) return
      try {
        const data = await api.leads.convert(lead.id)
        toast.success('Сделка создана')
        await loadLeads()
        if (data?.deal_id) router.push(`/deals?deal_id=${data.deal_id}`)
      } catch (e) {
        toast.error(e?.response?.data?.detail || 'Не удалось конвертировать')
      }
    }

    // Inline status
    const changeLeadStatus = async (lead, newStatus) => {
      inlineStatusOpenId.value = null
      if (lead.status === newStatus) return
      if (newStatus === 'converted') {
        await convertLead(lead)
        return
      }
      const prev = lead.status
      lead.status = newStatus
      inlineStatusBusyId.value = lead.id
      try {
        await api.leads.update(lead.id, { status: newStatus })
        toast.success(`Статус: ${statusLabel(newStatus)}`)
      } catch (e) {
        lead.status = prev
        toast.error(e?.response?.data?.detail || 'Не удалось изменить статус')
      } finally {
        inlineStatusBusyId.value = null
      }
    }

    // Bulk
    const toggleSelected = (id) => {
      const next = new Set(selectedIds.value)
      if (next.has(id)) next.delete(id); else next.add(id)
      selectedIds.value = next
    }
    const allOnPageSelected = computed(() => leads.value.length > 0 && leads.value.every(l => selectedIds.value.has(l.id)))
    const someOnPageSelected = computed(() => leads.value.some(l => selectedIds.value.has(l.id)))
    const toggleAllOnPage = () => {
      const next = new Set(selectedIds.value)
      if (allOnPageSelected.value) leads.value.forEach(l => next.delete(l.id))
      else leads.value.forEach(l => next.add(l.id))
      selectedIds.value = next
    }
    const clearSelection = () => { selectedIds.value = new Set() }

    const bulkSetStatus = async (status) => {
      const ids = Array.from(selectedIds.value)
      if (!ids.length || !status) return
      const ok = await confirm({
        title: `Перевести ${ids.length} лид(ов) в «${statusLabel(status)}»?`,
        confirmText: 'Применить',
      })
      if (!ok) return
      bulkBusy.value = true
      let failed = 0
      const settle = await Promise.allSettled(ids.map(id => api.leads.update(id, { status })))
      settle.forEach(r => { if (r.status === 'rejected') failed += 1 })
      bulkBusy.value = false
      clearSelection()
      await loadLeads()
      if (!failed) toast.success(`Готово: ${ids.length}`)
      else toast.warning(`Готово: ${ids.length - failed}, ошибок: ${failed}`)
    }
    const bulkDelete = async () => {
      const ids = Array.from(selectedIds.value)
      if (!ids.length) return
      const ok = await confirm({
        title: `Удалить ${ids.length} лид(ов)?`,
        message: 'Действие необратимо.',
        confirmText: 'Удалить',
        variant: 'danger',
      })
      if (!ok) return
      bulkBusy.value = true
      let failed = 0
      const settle = await Promise.allSettled(ids.map(id => api.leads.remove(id)))
      settle.forEach(r => { if (r.status === 'rejected') failed += 1 })
      bulkBusy.value = false
      clearSelection()
      await loadLeads()
      if (!failed) toast.success(`Удалено: ${ids.length}`)
      else toast.warning(`Удалено: ${ids.length - failed}, ошибок: ${failed}`)
    }

    // Kanban
    const leadsByStatus = computed(() => {
      const grouped = {}
      KANBAN_STATUSES.forEach(s => { grouped[s.key] = [] })
      leads.value.forEach(l => {
        if (grouped[l.status]) grouped[l.status].push(l)
        else grouped.incoming.push(l)
      })
      return grouped
    })
    const onDragStart = (e, lead) => {
      draggedLead = lead
      e.dataTransfer.effectAllowed = 'move'
      try { e.dataTransfer.setData('text/plain', lead.id) } catch (_) {}
    }
    const onKanbanDrop = async (event, newStatus) => {
      dragOverStatus.value = null
      const lead = draggedLead || leads.value.find(l => l.id === event.dataTransfer.getData('text/plain'))
      draggedLead = null
      if (!lead || lead.status === newStatus) return
      if (newStatus === 'converted') {
        await convertLead(lead)
        return
      }
      const prev = lead.status
      lead.status = newStatus
      try {
        await api.leads.update(lead.id, { status: newStatus })
        toast.success(`Перенесён в «${statusLabel(newStatus)}»`)
      } catch (e) {
        lead.status = prev
        toast.error('Не удалось обновить статус')
      }
    }

    // Row menu (teleported)
    const rowMenuTarget = computed(() => {
      if (!openRowMenuId.value) return null
      return leads.value.find(l => l.id === openRowMenuId.value) || null
    })
    const onRowMenuToggle = (event, id) => {
      if (openRowMenuId.value === id) { openRowMenuId.value = null; return }
      const rect = event.currentTarget.getBoundingClientRect()
      const menuWidth = 240
      let left = rect.right - menuWidth
      let top = rect.bottom + 6
      if (left < 8) left = 8
      if (left + menuWidth > window.innerWidth - 8) left = window.innerWidth - menuWidth - 8
      const menuHeight = 200
      if (top + menuHeight > window.innerHeight - 8) top = rect.top - menuHeight - 6
      rowMenuCoords.value = { top, left }
      openRowMenuId.value = id
    }

    onMounted(async () => {
      restoreFromUrl()
      await Promise.all([loadCompanies(), loadUsers()])
      await loadLeads()
    })

    return {
      KANBAN_STATUSES, KANBAN_STATUSES_FOR_FORM, LEAD_STATUS_OPTIONS,
      leads, companies, users, internalCompanies, customerCompanies,
      total, totalPages, loading, saving,
      filters, page, pageSize, sortBy, sortDir, viewMode,
      statusFilterOpen, moreFiltersOpen, showFormModal, editingLead,
      selectedIds, bulkBusy, inlineStatusOpenId, inlineStatusBusyId,
      openRowMenuId, rowMenuCoords, rowMenuTarget, dragOverStatus,
      hasMoreFilters, activeMoreFiltersCount, hasActiveFilters,
      allOnPageSelected, someOnPageSelected,
      leadsByStatus,
      // helpers
      statusLabel, getCompanyName, getUserName, initials, avatarColor, formatCurrency, formatDate,
      // actions
      debouncedSearch, resetAndLoad, setStatus, clearAdvancedFilters, clearAllFilters,
      onPageSizeChange, goToPage, toggleSort, setViewMode,
      openCreateModal, openEditModal, openDetail, onFormSubmit, deleteLead, convertLead,
      changeLeadStatus,
      toggleSelected, toggleAllOnPage, clearSelection, bulkSetStatus, bulkDelete,
      onDragStart, onKanbanDrop, onRowMenuToggle,
    }
  }
}
</script>

<style scoped>
/* Outer page: zero padding/gap to mirror Tasks view */
.leads-view { padding: 0; gap: 0; }

/* The single .list-card wraps both toolbar and body; mirror Tasks
   reference: edge-to-edge in the content area, rounded only as a
   whole rectangle (not separate cards). */
.leads-view :deep(.list-card) {
  margin: 0;
  border-radius: var(--radius-lg);
  border-color: var(--color-border-subtle);
  box-shadow: none;
}
.leads-view :deep(.list-card__toolbar) {
  padding: 14px 20px;
  gap: var(--space-2);
  /* Separator from the body — same line that splits tasks toolbar from list */
  border-bottom: 1px solid var(--color-border-subtle);
}

/* ============================================================
   Toolbar
   ============================================================ */
.toolbar-card {
  overflow: visible;
  position: relative;
  z-index: 50;
  /* Establish stacking context above body so popovers (status menu,
     filter popover) overlay the table beneath. */
}
.toolbar-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  /* Keep everything on a single row on desktop — mirrors Tasks toolbar.
     Wrapping kicks in only on narrow viewports (see @media below). */
  flex-wrap: nowrap;
  min-width: 0;
  /* Fill the parent .list-card__toolbar width — without this the row
     sizes to its content and the `flex: 1` search has no space to grow. */
  flex: 1 1 100%;
  width: 100%;
}
@media (max-width: 900px) {
  .toolbar-row { flex-wrap: wrap; }
}
.toolbar-title {
  font-size: var(--text-xl);
  font-weight: var(--fw-bold);
  color: var(--color-text);
  white-space: nowrap;
  margin-right: 4px;
}

.status-filter-wrap, .more-filter-wrap { position: relative; }
.status-filter-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 32px;
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  font-size: var(--text-sm);
  cursor: pointer;
  white-space: nowrap;
  color: var(--color-text);
}
.status-filter-btn:hover { background: var(--color-surface-2); border-color: var(--color-text-muted); }
.status-filter-btn__icon { color: var(--color-text-muted); font-size: var(--text-sm); }
.status-filter-btn__label { font-weight: var(--fw-semibold); }

.status-filter-menu {
  position: absolute;
  top: calc(100% + var(--space-1));
  left: 0;
  z-index: 200;
  min-width: 220px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-1);
  box-shadow: var(--shadow-lg);
}
.status-filter-menu__item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-2) var(--space-3);
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: var(--radius-xs);
  font-size: var(--text-base);
  text-align: left;
  color: var(--color-text);
}
.status-filter-menu__item:hover { background: var(--color-surface-3); }
.status-filter-menu__item.active { font-weight: var(--fw-bold); }
.status-filter-menu__divider { height: 1px; background: var(--color-border-subtle); margin: var(--space-1) 0; }
.ml-auto { margin-left: auto; }

/* Status colors (single source via dot + class) */
.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
  opacity: 0.85;
}
.lead-status-incoming                 { color: #1976d2; }
.lead-status-no_work                  { color: #607d8b; }
.lead-status-proposal                 { color: #f59e0b; }
.lead-status-waiting                  { color: #d97706; }
.lead-status-customer_reject_internal { color: #ef4444; }
.lead-status-customer_reject_our      { color: #b91c1c; }
.lead-status-we_reject                { color: #6b7280; }
.lead-status-converted                { color: #22c55e; }

.status-filter-btn.lead-status-incoming                 { background: rgba(25,118,210,0.08);  border-color: rgba(25,118,210,0.4); }
.status-filter-btn.lead-status-no_work                  { background: rgba(96,125,139,0.08); border-color: rgba(96,125,139,0.4); }
.status-filter-btn.lead-status-proposal                 { background: rgba(245,158,11,0.08); border-color: rgba(245,158,11,0.4); }
.status-filter-btn.lead-status-waiting                  { background: rgba(217,119,6,0.08);  border-color: rgba(217,119,6,0.4); }
.status-filter-btn.lead-status-customer_reject_internal { background: rgba(239,68,68,0.08);  border-color: rgba(239,68,68,0.4); }
.status-filter-btn.lead-status-customer_reject_our      { background: rgba(185,28,28,0.08);  border-color: rgba(185,28,28,0.4); }
.status-filter-btn.lead-status-we_reject                { background: rgba(107,114,128,0.08); border-color: rgba(107,114,128,0.4); }
.status-filter-btn.lead-status-converted                { background: rgba(34,197,94,0.08);  border-color: rgba(34,197,94,0.4); }

/* Search — wrapper for layout; visual styles come from UiInput */
/* Search grows to fill space, but can also shrink so the row stays on
   a single line — matches Tasks .tb__search { flex: 1 } behaviour. */
.leads-search-wrap {
  flex: 1 1 0;
  min-width: 160px;
}
.leads-search-wrap > * { width: 100%; }

.filter-active-dot {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: var(--space-1);
  background: rgba(255,255,255,0.25);
  border-radius: var(--radius-pill);
  padding: 1px var(--space-2);
  font-size: var(--text-xs);
  font-weight: var(--fw-bold);
}

/* Advanced filters popover — mirrors Tasks .tb__filter-popover */
.advanced-filters-pop {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 600;
  width: 340px;
  padding: var(--space-3);
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
}
.advanced-filters-pop__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-3);
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}
.advanced-filters {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-2);
}
.advanced-filters label {
  display: block;
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.4px;
  color: var(--color-text-muted);
  font-weight: var(--fw-semibold);
  margin-bottom: var(--space-1);
}

/* Pager — mirrors Tasks .tb__pager proportions */
.leads-pager {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 8px;
  height: 34px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  font-size: var(--text-sm);
}
.pager-label {
  font-variant-numeric: tabular-nums;
  font-family: inherit;
  font-weight: var(--fw-medium);
  min-width: 44px;
  text-align: center;
  color: var(--color-text);
}
.pager-size {
  border: none;
  background: transparent;
  font-size: var(--text-sm);
  outline: none;
  cursor: pointer;
  padding: 0 var(--space-1);
  border-left: 1px solid var(--color-border-subtle);
  margin-left: 4px;
  color: var(--color-text);
}

/* View-switcher — mirrors Tasks .tb__segmented */
.view-switcher {
  display: inline-flex;
  align-items: center;
  height: 34px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  overflow: hidden;
}
.view-btn {
  height: 100%;
  width: 36px;
  border: 0;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-md);
  transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}
.view-btn + .view-btn { border-left: 1px solid var(--color-border-subtle); }
.view-btn:hover:not(.active) { background: var(--color-surface-2); color: var(--color-text); }
.view-btn.active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

/* Filter pills */
/* Active filters row — mirrors Tasks `.tb__row--chips`.
   `flex-basis: 100%` forces a full-row in the parent .list-card__toolbar
   flex container so chips sit BELOW toolbar-row, not beside it. */
.filter-pills {
  flex: 0 0 100%;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin: 10px -20px -14px -20px;
  padding: 10px 20px;
  border-top: 1px solid var(--color-border-subtle);
}
.filter-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 4px 4px 10px;
  border-radius: var(--radius-pill);
  background: var(--color-primary-soft);
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  color: var(--color-primary);
}
.filter-pill button {
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 0 6px;
  color: inherit;
  border-radius: var(--radius-pill);
  font-size: 0.7rem;
}
.filter-pill button:hover { background: rgba(15, 23, 42, 0.08); }
.filter-pill--clear {
  background: transparent;
  padding: 4px 10px;
  cursor: pointer;
  border: none;
  color: var(--color-text-muted);
  font-weight: var(--fw-medium);
}
.filter-pill--clear:hover { background: var(--color-surface-2); color: var(--color-text); }
/* Status-coloured variants override the primary tint */
.filter-pill.lead-status-incoming { background: rgba(25,118,210,0.15); color: #01579b; }
.filter-pill.lead-status-proposal { background: rgba(245,158,11,0.15); color: #b45309; }
.filter-pill.lead-status-converted { background: rgba(34,197,94,0.15);  color: #166534; }

/* Bulk bar */
.bulk-bar {
  position: fixed;
  bottom: var(--space-6);
  left: 50%;
  transform: translateX(-50%);
  z-index: 1500;
  background: var(--color-primary);
  color: var(--color-on-primary);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  box-shadow: var(--shadow-lg);
  flex-wrap: wrap;
}
.bulk-bar__info { display: flex; align-items: center; gap: var(--space-2); }
.bulk-bar__actions { display: flex; gap: var(--space-2); flex-wrap: wrap; }
.bulk-bar__select {
  height: 30px;
  padding: var(--space-1) var(--space-2);
  font-size: var(--text-sm);
  border-radius: var(--radius-xs);
  border: 1px solid rgba(255,255,255,0.4);
  background: rgba(255,255,255,0.12);
  color: #fff;
}
.bulk-bar__select option { color: var(--color-text); }
.bulk-bar .btn-outline-danger {
  background: rgba(255,255,255,0.12);
  border-color: rgba(255,255,255,0.4);
  color: #fff;
}
.bulk-bar .btn-outline-danger:hover { background: var(--color-danger); border-color: var(--color-danger); }
.bulk-bar .btn-outline-secondary {
  background: transparent;
  border-color: rgba(255,255,255,0.4);
  color: #fff;
}
.bulk-bar .btn-outline-secondary:hover { background: rgba(255,255,255,0.12); }
.bulk-bar-enter-active, .bulk-bar-leave-active { transition: opacity var(--dur-base) ease, transform var(--dur-base) ease; }
.bulk-bar-enter-from, .bulk-bar-leave-to { opacity: 0; transform: translateX(-50%) translateY(20px); }

/* ============================================================
   Table
   ============================================================ */
.leads-content-card { padding: 0 !important; }
.leads-table-scroll { flex: 1; min-height: 0; overflow: auto; }
.leads-table { width: 100%; border-collapse: collapse; }
.leads-table thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  text-align: left;
  background: var(--color-surface-2);
  color: var(--color-text-muted);
  font-weight: var(--fw-semibold);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.4px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--color-border);
}
.leads-table thead th.sortable { cursor: pointer; user-select: none; }
.leads-table thead th.sortable:hover { color: var(--color-text); }
.leads-table thead th.sortable i { font-size: var(--text-sm); margin-left: var(--space-1); color: var(--color-primary); }
.leads-table .check-col { width: 36px; padding-left: 14px !important; padding-right: 0 !important; }
.leads-table .actions-th, .leads-table .actions-cell { width: 56px; padding-right: 14px; }
.leads-table .text-right { text-align: right; }

.leads-row {
  border-bottom: 1px solid var(--color-border-subtle);
  cursor: pointer;
  transition: background var(--dur-fast) ease;
}
.leads-row:hover { background: var(--color-surface-2); }
.leads-row.selected { background: var(--color-primary-soft); }
.leads-row td { padding: 12px 14px; font-size: var(--text-base); vertical-align: middle; }

.leads-title-cell__primary {
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}
.leads-title-cell__address {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: 2px;
  display: flex;
  align-items: center;
  gap: var(--space-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 280px;
}
.leads-assignee-cell {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.leads-amount {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-weight: var(--fw-semibold);
  white-space: nowrap;
}
.leads-date {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

/* Inline status badge */
.lead-status-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 2px var(--space-2);
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  white-space: nowrap;
  border: 1px solid currentColor;
}
.lead-status-badge--editable { cursor: pointer; background: transparent; }
.lead-status-badge--editable:hover:not(:disabled) { filter: brightness(0.95); }
.lead-status-badge .fa-caret-down { font-size: 0.6rem; opacity: 0.7; }

.lead-status-badge.lead-status-incoming                 { background: rgba(25,118,210,0.12);  }
.lead-status-badge.lead-status-no_work                  { background: rgba(96,125,139,0.12); }
.lead-status-badge.lead-status-proposal                 { background: rgba(245,158,11,0.15); }
.lead-status-badge.lead-status-waiting                  { background: rgba(217,119,6,0.15);  }
.lead-status-badge.lead-status-customer_reject_internal { background: rgba(239,68,68,0.15);  }
.lead-status-badge.lead-status-customer_reject_our      { background: rgba(185,28,28,0.15);  }
.lead-status-badge.lead-status-we_reject                { background: rgba(107,114,128,0.15); }
.lead-status-badge.lead-status-converted                { background: rgba(34,197,94,0.15);  }

.inline-status-wrap { position: relative; display: inline-block; }
.inline-status-menu {
  position: absolute;
  top: calc(100% + var(--space-1));
  left: 0;
  z-index: 100;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-1);
  min-width: 220px;
  box-shadow: var(--shadow-lg);
}
.inline-status-menu__item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-2) var(--space-3);
  border: none;
  background: transparent;
  border-radius: var(--radius-xs);
  cursor: pointer;
  font-size: var(--text-base);
  text-align: left;
}
.inline-status-menu__item:hover { background: var(--color-surface-3); }
.inline-status-menu__item.active { font-weight: var(--fw-bold); }

/* Row floating menu (teleported) */
.more-menu--floating {
  position: fixed;
  z-index: 9500;
  min-width: 240px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-1);
  box-shadow: var(--shadow-lg);
}
.more-menu-item {
  display: flex;
  align-items: center;
  width: 100%;
  padding: var(--space-2) var(--space-3);
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: var(--radius-xs);
  font-size: var(--text-base);
  text-align: left;
  color: var(--color-text);
}
.more-menu-item:hover { background: var(--color-surface-3); }
.more-menu-item--danger { color: var(--color-danger); }
.more-menu-item--danger:hover { background: var(--color-danger-soft); }
.more-menu-divider { height: 1px; background: var(--color-border-subtle); margin: var(--space-1) 0; }
.pop-enter-active, .pop-leave-active { transition: opacity var(--dur-fast) ease, transform var(--dur-fast) ease; }
.pop-enter-from, .pop-leave-to { opacity: 0; transform: translateY(-4px); }

.user-avatar {
  width: 24px; height: 24px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.62rem;
  font-weight: 700;
  color: #fff;
  background: #607d8b;
  flex-shrink: 0;
}
.user-avatar.xs { width: 22px; height: 22px; font-size: 0.58rem; }
.avatar-blue { background: #1976d2; }
.avatar-teal { background: #00897b; }
.avatar-amber { background: #f57c00; }
.avatar-pink { background: #d81b60; }
.avatar-purple { background: #6a1b9a; }
.avatar-green { background: #2e7d32; }
.avatar-red { background: #c62828; }
.avatar-indigo { background: #3949ab; }

.leads-footer {
  padding: var(--space-2) var(--space-4);
  border-top: 1px solid var(--color-border-subtle);
  text-align: right;
}

/* ============================================================
   Kanban
   ============================================================ */
.kanban-board {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-3);
  overflow-x: auto;
  flex: 1;
  min-height: 0;
}
.kanban-column {
  flex: 0 0 280px;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  background: var(--color-surface-2);
  border-radius: var(--radius-md);
  padding: var(--space-2);
  min-height: 100%;
  transition: background var(--dur-fast) ease, outline-color var(--dur-fast) ease;
}
.kanban-column--drop {
  background: var(--color-primary-soft);
  outline: 2px dashed var(--color-primary);
  outline-offset: -4px;
}
.kanban-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface);
  border-radius: var(--radius-sm);
  font-weight: var(--fw-semibold);
  font-size: var(--text-base);
}
.kanban-header__label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.kanban-header__count {
  font-size: var(--text-xs);
  background: var(--color-surface-3);
  padding: 1px var(--space-2);
  border-radius: var(--radius-pill);
  font-weight: var(--fw-bold);
  color: var(--color-text-muted);
}
.kanban-items {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  overflow-y: auto;
  flex: 1;
}
.kanban-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-3);
  cursor: grab;
  transition: border-color var(--dur-fast) ease, box-shadow var(--dur-fast) ease;
}
.kanban-card:hover { border-color: var(--color-primary); box-shadow: var(--shadow-xs); }
.kanban-card:active { cursor: grabbing; }
.kanban-card__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-2);
}
.kanban-card__title {
  font-weight: var(--fw-semibold);
  font-size: var(--text-base);
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.kanban-card__meta {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: var(--space-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.kanban-card__foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--space-2);
  padding-top: var(--space-2);
  border-top: 1px dashed var(--color-border);
}
.kanban-card__amount {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}
.kanban-empty {
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--space-5) var(--space-3);
  text-align: center;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}
.d-none { display: none; }
</style>
