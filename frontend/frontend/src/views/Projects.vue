<template>
  <div class="projects-view">
    <div class="list-card">
      <div class="list-card__toolbar">
    <section class="projects-toolbar-compact">
      <div class="projects-toolbar-compact__title">
        <h1>Сделки</h1>
        <span class="projects-toolbar-compact__count">{{ projects.length }} {{ getProjectsCountText(projects.length) }}</span>
      </div>

      <label class="projects-toolbar-compact__search">
        <i class="fas fa-search"></i>
        <input
          v-model="searchQuery"
          type="text"
          class="form-control"
          placeholder="Поиск по сделке, объекту или адресу..."
          @input="debouncedSearch"
        >
      </label>

      <UiChipFilter
        v-model="statusFilter"
        :options="STATUS_OPTIONS"
        placeholder="Все статусы"
        empty-icon="fas fa-circle-half-stroke"
        @update:model-value="loadProjects"
      />

      <UiChipFilter
        v-model="ourCompanyFilter"
        :options="ourCompanyOptions"
        placeholder="Наша компания"
        empty-icon="fas fa-building"
        @update:model-value="loadProjects"
      />

      <label class="projects-toolbar-compact__field projects-toolbar-compact__field--company projects-toolbar-compact__field--customer">
        <span>Заказчик</span>
        <CompanySmartSelect
          input-id="projects_customer_filter"
          :model-value="customerFilter"
          :options="customerCompanies"
          fetch-url="/api/v1/companies/"
          :fetch-params="{ company_type: 'customer' }"
          :fetch-limit="100"
          :max-results="12"
          placeholder="Найти"
          @update:model-value="setCustomerFilter"
        />
      </label>

      <label class="projects-toolbar-compact__field projects-toolbar-compact__field--narrow projects-toolbar-compact__field--from">
        <span>От</span>
        <input
          v-model.number="minContractValue"
          type="number"
          class="form-control"
          placeholder="Мин\."
          @blur="loadProjects"
        >
      </label>

      <label class="projects-toolbar-compact__field projects-toolbar-compact__field--narrow projects-toolbar-compact__field--to">
        <span>До</span>
        <input
          v-model.number="maxContractValue"
          type="number"
          class="form-control"
          placeholder="Макс."
          @blur="loadProjects"
        >
      </label>

      <div class="projects-toolbar-compact__view">
        <button
          type="button"
          class="projects-toolbar-compact__view-btn"
          :class="{ 'projects-toolbar-compact__view-btn--active': viewMode === 'table' }"
          @click="viewMode = 'table'"
        >
          <i class="fas fa-list"></i>
          <span>Список</span>
        </button>
        <button
          type="button"
          class="projects-toolbar-compact__view-btn"
          :class="{ 'projects-toolbar-compact__view-btn--active': viewMode === 'kanban' }"
          @click="viewMode = 'kanban'"
        >
          <i class="fas fa-columns"></i>
          <span>Канбан</span>
        </button>
      </div>

      <button type="button" class="projects-toolbar-compact__clear" @click="clearFilters">
        <i class="fas fa-rotate-left"></i>
        <span>Сбросить</span>
      </button>

      <button class="btn btn-primary projects-toolbar-compact__create" @click="showCreateModal = true">
        <i class="fas fa-plus"></i>
        <span>Новая сделка</span>
      </button>
    </section>
      </div>
      <div class="list-card__body">
      <!-- Loading State -->
      <div v-if="loading" class="d-flex flex-column gap-2 card">
        <SkeletonLoader height="60px" v-for="i in 5" :key="i" />
      </div>
      
      <!-- Empty State -->
      <div v-else-if="projects.length === 0" class="d-flex flex-column align-center py-5 card">
        <i class="fas fa-folder-open fa-3x text-muted mb-3"></i>
        <h4 style="margin: 0;">Нет сделок</h4>
        <p class="text-muted">Создайте первую сделку</p>
      </div>

      <!-- Table View -->
      <div v-else-if="viewMode === 'table'" class="table-container card">
        <table class="table">
          <thead>
            <tr>
              <th>Название</th>
              <th>{{ customerColumnLabel }}</th>
              <th>{{ ourCompanyColumnLabel }}</th>
              <th>{{ objectColumnLabel }}</th>
              <th>Адрес</th>
              <th>Статус</th>
              <th>Договорная стоимость</th>
              <th style="width: 100px;"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="project in paginatedProjects" :key="project.id">
              <td style="font-weight: 500;">
                <router-link :to="`/projects/${project.id}`" style="color: var(--md-sys-color-primary); text-decoration: none;">
                  {{ project.title }}
                </router-link>
                <button
                  v-if="getProjectHealthCount(project.id).total"
                  type="button"
                  class="project-health-count"
                  :class="{ 'project-health-count--error': getProjectHealthCount(project.id).errors }"
                  @click.stop="openProjectHealth(project)"
                >
                  <i class="fas fa-triangle-exclamation"></i>
                  <span>{{ getProjectHealthCount(project.id).total }}</span>
                </button>
              </td>
              <td class="text-muted">{{ getProjectCustomerLabel(project) }}</td>
              <td class="text-muted">{{ getProjectOurCompanyLabel(project) }}</td>
              <td class="text-muted">{{ project.obj_name || '-' }}</td>
              <td class="text-muted">{{ project.address || '-' }}</td>
              <td>
                <span class="badge" :class="getStatusClass(project.status)">
                  {{ getStatusText(project.status) }}
                </span>
              </td>
              <td style="font-family: monospace; font-size: 0.9rem;">
                <span v-if="project.total_contract_value">
                  {{ formatCurrency(project.total_contract_value) }}
                </span>
                <span v-else class="text-muted">-</span>
              </td>
              <td>
                <div class="d-flex gap-2 justify-end">
                  <button class="btn btn-sm btn-outline-primary" @click="editProject(project)">
                    <i class="fas fa-edit"></i>
                  </button>
                  <button class="btn btn-sm btn-danger" style="background: transparent; color: var(--color-danger); border: 1px solid var(--color-danger);" @click="deleteProject(project)">
                    <i class="fas fa-trash"></i>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="totalPages > 1" class="d-flex justify-between align-center p-2 border-top">
          <small class="text-muted">{{ paginationStart }}-{{ paginationEnd }} / {{ projects.length }}</small>
          <div class="d-flex align-center gap-2">
            <button class="btn btn-sm btn-outline-secondary" :disabled="!canGoPrev" @click="goToPage(currentPage - 1)">
              <i class="fas fa-chevron-left"></i>
            </button>
            <span class="small text-muted">{{ currentPage }} / {{ totalPages }}</span>
            <button class="btn btn-sm btn-outline-secondary" :disabled="!canGoNext" @click="goToPage(currentPage + 1)">
              <i class="fas fa-chevron-right"></i>
            </button>
          </div>
        </div>
      </div>

      <!-- Kanban View -->
      <div v-else-if="viewMode === 'kanban'" class="kanban-board">
         <div v-for="status in kanbanStatuses" :key="status.key" class="kanban-column">
            <div class="kanban-header">
               <span class="badge" :class="status.badgeClass">{{ status.label }}</span>
               <span class="text-muted small ml-2">{{ projectsByStatus[status.key].length }}</span>
            </div>
            
            <draggable
               class="kanban-items"
               :list="projectsByStatus[status.key]"
               item-key="id"
               :group="{ name: 'projects-kanban', pull: true, put: true }"
               :animation="180"
               :delay="isTouchDevice ? 160 : 0"
               :delay-on-touch-only="true"
               :force-fallback="isTouchDevice"
               fallback-on-body
               @change="onProjectKanbanChange($event, status.key)"
            >
               <template #item="{ element: project }">
               <div 
                  class="kanban-card"
                  @click="$router.push(`/projects/${project.id}`)"
               >
                  <div class="d-flex justify-between align-start mb-2">
                     <div class="fw-600 project-title">
                        <span>{{ project.title }}</span>
                        <button
                          v-if="getProjectHealthCount(project.id).total"
                          type="button"
                          class="project-health-count project-health-count--compact"
                          :class="{ 'project-health-count--error': getProjectHealthCount(project.id).errors }"
                          @click.stop="openProjectHealth(project)"
                        >
                          <i class="fas fa-triangle-exclamation"></i>
                          <span>{{ getProjectHealthCount(project.id).total }}</span>
                        </button>
                     </div>
                     <button class="btn btn-sm btn-icon text-muted" @click.stop="editProject(project)">
                        <i class="fas fa-ellipsis-v"></i>
                     </button>
                  </div>
                  
                  <div class="small text-muted mb-2">
                     <i class="fas fa-map-marker-alt mr-1"></i> {{ project.address_short || 'Адрес не указан' }}
                  </div>
                  
                  <div class="d-flex justify-between align-center mt-3 pt-2 border-top">
                     <span class="font-mono small">{{ formatCurrency(project.total_contract_value || 0) }}</span>
                     <div class="avatar-circle small" style="background: var(--md-sys-color-secondary-container); color: var(--md-sys-color-on-secondary-container);">
                        {{ (project.customer_name || 'C').charAt(0) }}
                     </div>
                  </div>
               </div>
               </template>
            </draggable>
         </div>
      </div>
      </div>
    </div>

    <!-- Модальное окно — компактная компоновка по образцу LeadFormModal -->
    <div v-if="showCreateModal" class="modal-overlay project-modal-overlay" @click.self="closeModal">
      <div class="project-modal" @click.stop>
        <div class="project-modal__header">
          <h3 class="project-modal__title m-0">{{ isEditing ? 'Редактировать сделку' : 'Новая сделка' }}</h3>
          <button type="button" class="project-modal__icon-btn" @click="closeModal" aria-label="Закрыть"><i class="fas fa-times"></i></button>
        </div>

        <form class="project-modal__body" @submit.prevent="saveProject">
          <div class="project-modal__row">
            <div class="project-modal__field project-modal__field--wide">
              <label for="title">Название <span class="req">*</span></label>
              <input id="title" v-model="projectForm.title" type="text" class="form-control" required />
            </div>
            <div class="project-modal__field">
              <label for="status">Статус</label>
              <select id="status" v-model="projectForm.status" class="form-control">
                <option value="active">Активный</option>
                <option value="completed">Завершён</option>
                <option value="on_hold">Приостановлен</option>
              </select>
            </div>
          </div>

          <div class="project-modal__row">
            <div class="project-modal__field project-modal__field--wide">
              <label for="obj_name">Наименование объекта</label>
              <input id="obj_name" v-model="projectForm.obj_name" type="text" class="form-control" />
            </div>
            <div class="project-modal__field">
              <label for="object_type">Тип объекта</label>
              <select id="object_type" v-model="projectForm.object_type" class="form-control">
                <option value="">Не выбран</option>
                <option v-for="option in objectTypeOptions" :key="option" :value="option">{{ option }}</option>
              </select>
            </div>
          </div>

          <div class="project-modal__field">
            <label for="address">Адрес объекта</label>
            <input id="address" v-model="projectForm.address" type="text" class="form-control" />
          </div>

          <div class="project-modal__row">
            <div class="project-modal__field">
              <label for="customer_id">Заказчик</label>
              <CompanySmartSelect
                input-id="customer_id"
                v-model="projectForm.customer_id"
                :options="companies"
                placeholder="Найти заказчика"
              />
            </div>
            <div class="project-modal__field">
              <label for="our_company_id">Наша компания</label>
              <CompanySmartSelect
                input-id="our_company_id"
                v-model="projectForm.our_company_id"
                :options="internalCompanies"
                placeholder="Найти нашу компанию"
              />
            </div>
          </div>

          <div class="project-modal__field">
            <label for="object_area">Площадь (м²)</label>
            <input id="object_area" v-model.number="projectForm.object_area" type="number" class="form-control" step="0.01" min="0" />
          </div>
        </form>

        <div class="project-modal__footer">
          <button type="button" class="btn btn-secondary" @click="closeModal">Отмена</button>
          <button type="button" class="btn btn-primary" :disabled="saving" @click="saveProject">
            <i v-if="saving" class="fas fa-spinner fa-spin mr-1"></i>
            <i v-else class="fas fa-check mr-1"></i>
            {{ isEditing ? 'Сохранить' : 'Создать' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { api } from '@/services/api'
import draggable from 'vuedraggable'
import SkeletonLoader from '../components/ui/SkeletonLoader.vue'
import CompanySmartSelect from '../components/ui/CompanySmartSelect.vue'
import UiChipFilter from '../components/ui/UiChipFilter.vue'
import { useToast } from '../composables/useToast'
import { useCompaniesStore } from '../stores/companies'

const STATUS_OPTIONS = [
  { value: 'active',    label: 'Активные',     color: '#22c55e' },
  { value: 'completed', label: 'Завершённые',  color: '#3b82f6' },
  { value: 'on_hold',   label: 'На паузе',     color: '#f59e0b' },
]

export default {
  name: 'Projects',
  components: { SkeletonLoader, CompanySmartSelect, UiChipFilter, draggable },
  setup() {
    const router = useRouter()
    const toast = useToast()
    const companiesStore = useCompaniesStore()
    const isTouchDevice = typeof window !== 'undefined' && (
      (window.matchMedia && window.matchMedia('(pointer: coarse)').matches) ||
      navigator.maxTouchPoints > 0
    )
    const projects = ref([])
    const projectHealthCounts = ref({})
    const companies = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const showCreateModal = ref(false)
    const showStageModal = ref(false)
    const isEditing = ref(false)
    const selectedProject = ref(null)
    const objectTypeOptions = [
      'Линейные - метрополитен',
      'Линейные - дороги, эстакады',
      'Линейные - инженерные сети',
      'Образовательные учреждения',
      'Объекты здравоохранения',
      'Спортивные сооружения',
      'Административные здания',
      'Жилые комплексы',
      'Торговые центры',
      'Паркинги',
      'Аэропорты',
      'Промышленные объекты',
      'Складские/архивные здания'
    ]

    // Filter variables
    const searchQuery = ref('')
    const statusFilter = ref('')
    const ourCompanyFilter = ref('')
    const customerFilter = ref('')
    const minContractValue = ref(null)
    const maxContractValue = ref(null)
    const customerColumnLabel = '\u0417\u0430\u043A\u0430\u0437\u0447\u0438\u043A'
    const ourCompanyColumnLabel = '\u041D\u0430\u0448\u0430 \u043A\u043E\u043C\u043F\u0430\u043D\u0438\u044F'
    const objectColumnLabel = '\u041E\u0431\u044A\u0435\u043A\u0442'
    const pageSize = 10
    const currentPage = ref(1)

    const projectForm = ref({
      title: '',
      obj_name: '',
      address: '',
      object_type: '',
      object_area: null,
      customer_id: '',
      our_company_id: '',
      total_contract_value: 0,
      status: 'active'
    })

    const internalCompanies = computed(() => companies.value.filter(company => company.type === 'internal'))
    const customerCompanies = computed(() => companies.value.filter(company => company.type === 'customer'))

    // Опции для UiChipFilter (наша компания) — генерируем из справочника.
    const ourCompanyOptions = computed(() =>
      internalCompanies.value.map((company) => ({
        value: company.id,
        label: company.short_name || company.name,
      }))
    )

    // Debounce timer
    let searchTimeout = null

    const loadProjectHealthCounts = async () => {
      const ids = projects.value.map(project => project.id).filter(Boolean)
      if (!ids.length) {
        projectHealthCounts.value = {}
        return
      }
      try {
        const params = new URLSearchParams()
        ids.forEach(id => params.append('deal_ids', id))
        const response = await axios.get(`/api/v1/data-health/deal-counts?${params.toString()}`)
        const counts = {}
        for (const item of response.data?.items || []) {
          counts[item.deal_id] = item
        }
        projectHealthCounts.value = counts
      } catch (error) {
        console.error('Error loading project health counts:', error)
        projectHealthCounts.value = {}
      }
    }

    const loadProjects = async () => {
      loading.value = true
      try {
        // Build query parameters
        const params = new URLSearchParams()

        if (statusFilter.value) {
          params.append('status', statusFilter.value)
        }
        if (ourCompanyFilter.value) {
          params.append('our_company_id', ourCompanyFilter.value)
        }
        if (customerFilter.value) {
          params.append('customer_id', customerFilter.value)
        }
        if (minContractValue.value !== null && minContractValue.value !== '') {
          params.append('min_contract_value', minContractValue.value.toString())
        }
        if (maxContractValue.value !== null && maxContractValue.value !== '') {
          params.append('max_contract_value', maxContractValue.value.toString())
        }
        if (searchQuery.value.trim()) {
          params.append('search', searchQuery.value.trim())
        }

        params.append('_t', String(Date.now()))
        const data = await api.deals.list(params)
        projects.value = data
        currentPage.value = 1
        await loadProjectHealthCounts()
      } catch (error) {
        console.error('Error loading projects:', error)
        toast.error('Ошибка загрузки сделок')
      } finally {
        loading.value = false
      }
    }

    const debouncedSearch = () => {
      clearTimeout(searchTimeout)
      searchTimeout = setTimeout(() => {
        loadProjects()
      }, 500) // 500ms delay
    }

    const setCustomerFilter = (value) => {
      customerFilter.value = value || ''
      loadProjects()
    }

    const clearFilters = () => {
      searchQuery.value = ''
      statusFilter.value = ''
      ourCompanyFilter.value = ''
      customerFilter.value = ''
      minContractValue.value = null
      maxContractValue.value = null
      loadProjects()
    }

    const getProjectsCountText = (count) => {
      if (count % 10 === 1 && count % 100 !== 11) {
        return 'сделку'
      } else if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) {
        return 'сделки'
      } else {
        return 'сделок'
      }
    }

    const totalPages = computed(() => Math.max(1, Math.ceil(projects.value.length / pageSize)))
    const paginatedProjects = computed(() => {
      const start = (currentPage.value - 1) * pageSize
      return projects.value.slice(start, start + pageSize)
    })
    const canGoPrev = computed(() => currentPage.value > 1)
    const canGoNext = computed(() => currentPage.value < totalPages.value)
    const paginationStart = computed(() => (projects.value.length ? ((currentPage.value - 1) * pageSize) + 1 : 0))
    const paginationEnd = computed(() => Math.min(currentPage.value * pageSize, projects.value.length))
    const goToPage = (page) => {
      currentPage.value = Math.min(Math.max(1, page), totalPages.value)
    }

    const getProjectHealthCount = (projectId) => {
      return projectHealthCounts.value?.[projectId] || { total: 0, errors: 0, warnings: 0, ignored: 0 }
    }

    const openProjectHealth = (project) => {
      if (!project?.id) return
      router.push(`/projects/${project.id}?tab=problems`)
    }

    watch(() => projects.value.length, () => {
      if (currentPage.value > totalPages.value) {
        currentPage.value = totalPages.value
      }
    })

    const saveProject = async (event) => {
      if (saving.value) {
        console.log('Already saving, ignoring...')
        return
      }

      console.log('Starting save project...')
      if (!projectForm.value.title.trim()) {
        toast.error('Название сделки обязательно')
        return
      }

      const wasEditing = isEditing.value
      saving.value = true
      try {
        let response
        if (wasEditing) {
          console.log('Updating project:', projectForm.value.id)
          response = await api.deals.update(projectForm.value.id, projectForm.value)
        } else {
          console.log('Creating new project:', projectForm.value)
          response = await api.deals.create(projectForm.value)
        }

        await loadProjects()
        closeModal()
        toast.success(wasEditing ? 'Сделка обновлена' : 'Сделка создана')
      } catch (error) {
        console.error('Error saving project:', error)
        if (error.response) {
          toast.error(`Ошибка сохранения: ${error.response.data.detail || 'Неизвестная ошибка'}`)
        } else {
          toast.error('Ошибка сети. Проверьте подключение к серверу.')
        }
      } finally {
        saving.value = false
      }
    }

    const normalizeId = (value) => {
      if (!value) return ''
      return String(value).replace(/-/g, '').toLowerCase()
    }

    const companyByIdMap = computed(() => {
      const map = new Map()
      ;(companies.value || []).forEach((company) => {
        const key = normalizeId(company?.id)
        if (key) map.set(key, company)
      })
      return map
    })

    const getCompanyNameById = (id) => {
      const key = normalizeId(id)
      if (!key) return '-'
      return companyByIdMap.value.get(key)?.name || '-'
    }

    const getProjectCustomerLabel = (project) => {
      return project?.customer_name || project?.customer?.name || getCompanyNameById(project?.customer_id)
    }

    const getProjectOurCompanyLabel = (project) => {
      return project?.our_company_name || project?.our_company?.name || getCompanyNameById(project?.our_company_id)
    }

    const editProject = (project) => {
      projectForm.value = {
        ...project,
        customer_id: normalizeId(project.customer_id),
        our_company_id: normalizeId(project.our_company_id)
      }
      isEditing.value = true
      showCreateModal.value = true
    }

    const deleteProject = async (project) => {
      if (!confirm(`Удалить сделку "${project.title}"?`)) {
        return
      }

      try {
        await api.deals.remove(project.id)
        await loadProjects()
      } catch (error) {
        console.error('Error deleting project:', error)
        toast.error('Ошибка удаления сделки')
      }
    }

    const loadCompanies = async () => {
      try {
        await companiesStore.ensureLoaded()
        companies.value = companiesStore.items
      } catch (error) {
        console.error('Error loading companies:', error)
      }
    }

    const closeModal = () => {
      showCreateModal.value = false
      isEditing.value = false
      projectForm.value = {
        title: '',
        obj_name: '',
        address: '',
        object_type: '',
        object_area: null,
        customer_id: '',
        our_company_id: '',
        total_contract_value: 0,
        status: 'active'
      }
    }

    const formatCurrency = (value) => {
      return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 0
      }).format(value)
    }

    const getStatusClass = (status) => {
      const classes = {
        active: 'badge-success',
        completed: 'badge-info',
        on_hold: 'badge-warning'
      }
      return classes[status] || 'badge-secondary'
    }

    const getStatusText = (status) => {
      const texts = {
        active: 'Активный',
        completed: 'Завершен',
        on_hold: 'Приостановлен'
      }
      return texts[status] || status
    }

    const viewMode = ref('table')

    const kanbanStatuses = [
       { key: 'active', label: 'Активные', badgeClass: 'badge-success' },
       { key: 'on_hold', label: 'Приостановлены', badgeClass: 'badge-warning' },
       { key: 'completed', label: 'Завершены', badgeClass: 'badge-info' },
    ]

    const projectsByStatus = computed(() => {
       const grouped = { active: [], on_hold: [], completed: [] }
       projects.value.forEach(p => {
          if (grouped[p.status]) {
             grouped[p.status].push(p)
          } else {
             // Fallback for unknown status
             grouped.active.push(p) 
          }
       })
       return grouped
    })

    const onProjectKanbanChange = async (event, newStatus) => {
       const project = event?.added?.element || null
       if (project && project.status !== newStatus) {
          // Optimistic update
          const oldStatus = project.status
          project.status = newStatus
          
          try {
             await api.deals.update(project.id, {
                ...project,
                status: newStatus
             })
             // Refresh to sync fully
             // await loadProjects() // Optional, maybe too heavy
          } catch (error) {
             console.error('Error updating status:', error)
             // Revert
             project.status = oldStatus
             toast.error('Не удалось обновить статус')
          }
       }
    }

    onMounted(async () => {
      await Promise.all([
        loadProjects(),
        loadCompanies()
      ])
    })

    return {
      projects,
      companies,
      loading,
      saving,
      showCreateModal,
      showStageModal,
      isEditing,
      selectedProject,
      projectForm,
      searchQuery,
      statusFilter,
      ourCompanyFilter,
      customerFilter,
      minContractValue,
      maxContractValue,
      customerColumnLabel,
      ourCompanyColumnLabel,
      objectColumnLabel,
      currentPage,
      totalPages,
      paginatedProjects,
      canGoPrev,
      canGoNext,
      isTouchDevice,
      paginationStart,
      paginationEnd,
      goToPage,
      getProjectHealthCount,
      openProjectHealth,
      STATUS_OPTIONS,
      ourCompanyOptions,
      loadProjects,
      saveProject,
      editProject,
      deleteProject,
      loadCompanies,
      closeModal,
      debouncedSearch,
      setCustomerFilter,
      clearFilters,
      formatCurrency,
      getStatusClass,
      getStatusText,
      getProjectCustomerLabel,
      getProjectOurCompanyLabel,
      getProjectsCountText,
      internalCompanies,
      customerCompanies,
      objectTypeOptions,
      viewMode,
      kanbanStatuses,
      projectsByStatus,
      onProjectKanbanChange
    }
  }
}
</script>

<style scoped>
/* ============================================================
   Bring projects list under the Tasks reference design system.
   Page → toolbar card → body card, single visual rectangle.
   ============================================================ */

/* Outer page: zero padding/gap so the card fills content-body */
.projects-view {
  padding: 0;
  gap: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* Single .list-card wraps both toolbar and body */
.projects-view :deep(.list-card) {
  margin: 0;
  border-radius: var(--radius-lg);
  border-color: var(--color-border-subtle);
  box-shadow: none;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.projects-view :deep(.list-card__toolbar) {
  padding: 14px 20px;
  gap: var(--space-2);
  border-bottom: 1px solid var(--color-border-subtle);
}

.projects-toolbar-compact {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: nowrap;
  overflow: visible;
  position: relative;
  z-index: 5;
  width: 100%;
  min-width: 0;
}

@media (max-width: 1280px) {
  .projects-toolbar-compact {
    flex-wrap: wrap;
  }
}

.project-health-count {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-height: 22px;
  margin-left: 8px;
  padding: 0 8px;
  border: 1px solid rgba(245, 158, 11, 0.28);
  border-radius: 999px;
  background: rgba(245, 158, 11, 0.12);
  color: #b45309;
  font-size: 0.78rem;
  font-weight: 800;
  cursor: pointer;
}

.project-health-count--error {
  border-color: rgba(239, 68, 68, 0.28);
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
}

.project-health-count--compact {
  margin-left: 6px;
  transform: translateY(-1px);
}

.projects-toolbar-compact > * {
  min-width: 0;
}

.projects-toolbar-compact__title,
.projects-toolbar-compact__search,
.projects-toolbar-compact__field,
.projects-toolbar-compact__view,
.projects-toolbar-compact__view-btn,
.projects-toolbar-compact__clear {
  display: flex;
  align-items: center;
}

.projects-toolbar-compact__title {
  flex: 0 0 auto;
  gap: var(--space-2);
  margin-right: 4px;
  white-space: nowrap;
}

.projects-toolbar-compact__title h1 {
  margin: 0;
  font-size: var(--text-xl);
  font-weight: var(--fw-bold);
  color: var(--color-text);
}

.projects-toolbar-compact__count {
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: var(--text-xs);
  font-weight: var(--fw-bold);
  white-space: nowrap;
}

/* Search — mirrors Tasks .tb__search */
.projects-toolbar-compact__search {
  flex: 1 1 0;
  gap: 8px;
  min-width: 160px;
  height: 38px;
  padding: 0 14px;
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
  color: var(--color-text);
  transition: border-color var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out);
}
.projects-toolbar-compact__search:focus-within {
  border-color: var(--color-primary);
  background: var(--color-surface);
  box-shadow: var(--shadow-focus);
}

.projects-toolbar-compact__search i {
  color: var(--color-text-subtle);
}

.projects-toolbar-compact__search .form-control {
  min-width: 0;
  height: 100%;
  border: none;
  background: transparent;
  box-shadow: none;
  padding-left: 0;
  padding-right: 0;
  font-size: var(--text-md);
  color: var(--color-text);
}

.projects-toolbar-compact__search .form-control::placeholder {
  color: var(--color-text-subtle);
}

/* Inline label + control pill */
.projects-toolbar-compact__field {
  flex: 0 0 auto;
  gap: 6px;
  height: 38px;
  width: max-content;
  padding: 0 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.projects-toolbar-compact__field span {
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  color: var(--color-text-muted);
  white-space: nowrap;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.projects-toolbar-compact__field .form-control {
  width: auto;
  flex: 0 0 auto;
  min-width: 0;
  height: 100%;
  padding: 0 4px;
  border: none;
  background: transparent;
  box-shadow: none;
  font-size: var(--text-sm);
  color: var(--color-text);
}

.projects-toolbar-compact__field .form-control::placeholder {
  color: inherit;
}

.projects-toolbar-compact__field--status .form-control {
  width: 92px;
}

.projects-toolbar-compact__field--company .form-control {
  width: 118px;
}

.projects-toolbar-compact__field--customer .smart-select {
  width: 170px;
}

.projects-toolbar-compact__field--customer .form-control {
  width: 170px;
}

.projects-toolbar-compact__field--narrow .form-control {
  width: 74px;
}

/* Segmented view-switcher — mirrors Tasks .tb__segmented */
.projects-toolbar-compact__view {
  flex: 0 0 auto;
  align-items: center;
  gap: 0;
  height: 38px;
  padding: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  overflow: hidden;
}

.projects-toolbar-compact__view-btn,
.projects-toolbar-compact__clear {
  gap: 6px;
  border: none;
  font: inherit;
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}

.projects-toolbar-compact__view-btn {
  height: 100%;
  padding: 0 12px;
  background: transparent;
  color: var(--color-text-muted);
  white-space: nowrap;
  font-size: var(--text-sm);
}
.projects-toolbar-compact__view-btn + .projects-toolbar-compact__view-btn {
  border-left: 1px solid var(--color-border-subtle);
}
.projects-toolbar-compact__view-btn:hover { background: var(--color-surface-2); color: var(--color-text); }

.projects-toolbar-compact__view-btn--active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-weight: var(--fw-semibold);
}

/* Clear button — secondary ghost */
.projects-toolbar-compact__clear {
  height: 38px;
  min-width: 38px;
  padding: 0 12px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-muted);
  white-space: nowrap;
  flex: 0 0 auto;
  font-size: var(--text-sm);
}
.projects-toolbar-compact__clear:hover {
  background: var(--color-surface-2);
  color: var(--color-text);
}

/* На широких экранах скрываем подпись — оставляем только иконку, чтобы
   toolbar помещался в одну строку. На узких возвращаем подпись. */
@media (min-width: 1281px) {
  .projects-toolbar-compact__clear span {
    display: none;
  }
  .projects-toolbar-compact__clear {
    padding: 0 12px;
  }
}

/* Primary "Новая сделка" button — sized like Tasks .tb__btn--primary */
.projects-toolbar-compact__create {
  white-space: nowrap;
  flex: 0 0 auto;
  width: max-content;
  height: 38px;
  padding: 0 14px;
  border-radius: var(--radius-md);
  font-size: var(--text-md);
  font-weight: var(--fw-medium);
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

/* ============================================================
   Table — mirrors Tasks list grid: tinted header band, compact rows
   ============================================================ */
.projects-view :deep(.list-card__body),
.projects-view .table-container {
  padding: 0 !important;
  margin: 0 !important;
  border: 0 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  background: var(--color-surface) !important;
  overflow: auto;
  flex: 1 1 auto;
  min-height: 0;
}

.projects-view .table-container .table {
  margin-bottom: 0;
  width: 100%;
  border-collapse: collapse;
}

.projects-view .table-container th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: var(--color-surface-2);
  color: var(--color-text-muted);
  text-align: left;
  padding: 10px 14px;
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  letter-spacing: 0.4px;
  text-transform: uppercase;
  white-space: nowrap;
  border-bottom: 1px solid var(--color-border);
}

.projects-view .table-container td {
  padding: 12px 14px;
  vertical-align: middle;
  font-size: var(--text-base);
  color: var(--color-text);
  border-bottom: 1px solid var(--color-border-subtle);
}

.projects-view .table-container tbody tr {
  transition: background var(--dur-fast) var(--ease-out);
  cursor: pointer;
}

.projects-view .table-container tbody tr:hover {
  background: var(--color-surface-2);
}

.projects-view .table-container .border-top {
  padding: 10px 14px !important;
  border-top: 1px solid var(--color-border-subtle) !important;
}

.projects-toolbar-compact__field--customer :deep(.form-control) {
  width: 170px;
  height: 100%;
  border: none;
  background: transparent;
  box-shadow: none;
  color: inherit;
}

.projects-toolbar-compact__field--customer :deep(.form-control::placeholder) {
  color: inherit;
}

.projects-toolbar-compact__field--customer :deep(.smart-select__dropdown) {
  margin-top: 8px;
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 10px;
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.12);
}

.projects-toolbar-compact__field--customer :deep(.smart-select__item:hover) {
  background: rgba(63, 140, 255, 0.08);
}

.projects-toolbar-compact__field--customer :deep(.smart-select__title) {
  color: inherit;
}

.projects-toolbar-compact__field--customer :deep(.smart-select__subtitle),
.projects-toolbar-compact__field--customer :deep(.smart-select__empty) {
  color: var(--md-sys-color-on-surface-variant);
}

/* ============================================================
   Kanban — same column/spacing language as Tasks and Leads kanban
   ============================================================ */
.kanban-board {
  display: flex;
  align-items: stretch;
  min-height: 100%;
  min-width: max-content;
  gap: var(--space-3);
  padding: var(--space-3);
  overflow-x: auto;
}

.kanban-column {
  flex: 0 0 280px;
  width: 280px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: var(--space-2);
  background: var(--color-surface-2);
  border: 0;
  border-radius: var(--radius-md);
  box-shadow: none;
  min-height: 100%;
}

.kanban-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-2);
  margin: 0;
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface);
  border: 0;
  border-radius: var(--radius-sm);
  font-weight: var(--fw-semibold);
  font-size: var(--text-base);
  color: var(--color-text);
  flex-shrink: 0;
}
.kanban-header > .small.text-muted {
  font-size: var(--text-xs);
  font-weight: var(--fw-bold);
  color: var(--color-text-muted);
  background: var(--color-surface-3);
  padding: 1px var(--space-2);
  border-radius: var(--radius-pill);
  margin-left: 0 !important;
}

.kanban-items {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  overflow-y: auto;
  min-height: 0;
}

.kanban-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-3);
  box-shadow: none;
  cursor: grab;
  transition: border-color var(--dur-fast) var(--ease-out), box-shadow var(--dur-fast) var(--ease-out);
}

.kanban-card:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-xs, 0 1px 2px rgba(15, 23, 42, 0.06));
}

.kanban-card:active { cursor: grabbing; }

/* ============================================================
   Create / edit modal — mirrors LeadFormModal.vue compact layout
   ============================================================ */
.project-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.42);
  z-index: 9100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.project-modal {
  width: min(680px, 100%);
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-radius: 14px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.22);
  overflow: hidden;
}

.project-modal__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid var(--color-border-subtle);
  flex-shrink: 0;
}
.project-modal__title { font-size: 1.05rem; font-weight: var(--fw-bold); color: var(--color-text); }

.project-modal__icon-btn {
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: var(--color-text-muted);
}
.project-modal__icon-btn:hover { background: var(--color-surface-2); color: var(--color-text); }

.project-modal__body {
  padding: 14px 18px;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.project-modal__row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.project-modal__field { margin: 0; display: flex; flex-direction: column; min-width: 0; }
.project-modal__field--wide { grid-column: span 1; }
.project-modal__field label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  color: var(--color-text-muted);
  font-weight: 600;
  margin-bottom: 4px;
}
.project-modal__field .req { color: #c62828; }
.project-modal__field .form-control {
  width: 100%;
  height: 36px;
  padding: 6px 10px;
  font-size: var(--text-sm);
  color: var(--color-text);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: border-color var(--dur-fast) var(--ease-out), box-shadow var(--dur-fast) var(--ease-out);
}
.project-modal__field .form-control:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}

.project-modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 18px;
  border-top: 1px solid var(--color-border-subtle);
  flex-shrink: 0;
}

@media (max-width: 720px) {
  .project-modal__row { grid-template-columns: 1fr; }
}

/* Dark theme */
:root[data-theme="dark"] .project-modal { background: var(--color-surface); }
:root[data-theme="dark"] .project-modal__header,
:root[data-theme="dark"] .project-modal__footer { border-color: var(--color-border); }
:root[data-theme="dark"] .project-modal__icon-btn:hover { background: rgba(255, 255, 255, 0.06); }
:root[data-theme="dark"] .project-modal__field .form-control {
  background: var(--color-surface-2);
  border-color: var(--color-border);
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) .project-modal { background: var(--color-surface); }
  :root:not([data-theme="light"]) .project-modal__header,
  :root:not([data-theme="light"]) .project-modal__footer { border-color: var(--color-border); }
  :root:not([data-theme="light"]) .project-modal__field .form-control {
    background: var(--color-surface-2);
    border-color: var(--color-border);
  }
}

.project-title {
   display: flex;
   align-items: center;
   gap: 6px;
   flex-wrap: wrap;
   font-size: 0.95rem;
   line-height: 1.3;
}

@media (max-width: 900px) {
   .kanban-board {
      display: flex;
      flex-direction: column;
   }
}

@media (max-width: 768px) {
  .projects-toolbar-compact {
    display: flex;
    align-items: stretch;
    gap: 10px;
    padding: 12px;
    overflow: visible;
  }

  .projects-toolbar-compact__title,
  .projects-toolbar-compact__search,
  .projects-toolbar-compact__field,
  .projects-toolbar-compact__view,
  .projects-toolbar-compact__clear,
  .projects-toolbar-compact__create {
    width: 100%;
    justify-self: stretch;
  }

  .projects-toolbar-compact__title,
  .projects-toolbar-compact__search,
  .projects-toolbar-compact__field,
  .projects-toolbar-compact__view,
  .projects-toolbar-compact__clear,
  .projects-toolbar-compact__create {
    grid-area: auto;
  }

  .projects-toolbar-compact__title {
    justify-content: space-between;
    flex-wrap: wrap;
  }

  .projects-toolbar-compact__search {
    min-width: 100%;
  }

  .projects-toolbar-compact__field {
    justify-content: space-between;
  }

  .projects-toolbar-compact__field .form-control,
  .projects-toolbar-compact__field--narrow .form-control {
    min-width: 0;
    flex: 1;
  }

  .projects-toolbar-compact__view {
    justify-content: stretch;
  }

  .projects-toolbar-compact__view-btn {
    flex: 1;
    justify-content: center;
  }

  .projects-toolbar-compact__clear,
  .projects-toolbar-compact__create {
    justify-content: center;
    min-height: 42px;
  }
  
  /* Table scroll */
  .table-container {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  
  .kanban-column {
    min-height: 200px;
  }
  
  .kanban-card {
    padding: 10px;
  }

  .projects-view .table-container table {
    min-width: 720px;
  }

  .projects-view .table-container th:nth-child(2),
  .projects-view .table-container td:nth-child(2),
  .projects-view .table-container th:nth-child(3),
  .projects-view .table-container td:nth-child(3),
  .projects-view .table-container th:nth-child(4),
  .projects-view .table-container td:nth-child(4) {
    display: none;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .form-grid .full-span {
    grid-column: span 1;
  }
}

@media (max-width: 480px) {
  .projects-toolbar-compact__title {
    align-items: flex-start;
    flex-direction: column;
    gap: 6px;
  }

  .projects-toolbar-compact__view-btn span,
  .projects-toolbar-compact__clear span,
  .projects-toolbar-compact__create span {
    font-size: 0.82rem;
  }

  .projects-view .table-container table {
    min-width: 620px;
  }

  .projects-view .table-container th:nth-child(5),
  .projects-view .table-container td:nth-child(5) {
    display: none;
  }
}
</style>

