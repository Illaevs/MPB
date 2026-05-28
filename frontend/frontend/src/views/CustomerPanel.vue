<template>
  <div class="customer-panel">
    <div class="customer-shell">
      <div class="customer-topbar">
        <div class="customer-breadcrumbs">
          <span class="customer-breadcrumbs-label">Проекты</span>
          <button
            v-for="project in projects"
            :key="project.id"
            class="customer-crumb"
            :class="{ active: project.id === activeProjectId }"
            @click="selectProject(project.id)"
          >
            {{ project.title }}
          </button>
        </div>

        <button class="customer-refresh" :disabled="loading" @click="reloadActiveProject" title="Обновить">
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
        </button>
      </div>

      <div v-if="loading && !detail" class="customer-empty">
        <i class="fas fa-spinner fa-spin"></i>
        <span>Загружаем проект заказчика...</span>
      </div>

      <div v-else-if="!projects.length" class="customer-empty">
        <i class="fas fa-folder-open"></i>
        <span>Для заказчика пока нет доступных проектов.</span>
      </div>

      <div v-else-if="errorMessage && !detail" class="customer-empty">
        <i class="fas fa-triangle-exclamation"></i>
        <span>{{ errorMessage }}</span>
      </div>

      <template v-else-if="detail">
        <section class="customer-hero">
          <div class="customer-hero-main">
            <div class="customer-hero-eyebrow">Кабинет заказчика</div>
            <h1 class="customer-title">{{ detail.deal.title }}</h1>
            <div class="customer-meta-grid">
              <div class="customer-meta-card">
                <div class="customer-meta-label">Наименование объекта</div>
                <div class="customer-meta-value">{{ detail.deal.obj_name || 'Не заполнено' }}</div>
              </div>
              <div class="customer-meta-card">
                <div class="customer-meta-label">Адрес объекта</div>
                <div class="customer-meta-value">{{ detail.deal.address || 'Не заполнено' }}</div>
              </div>
              <div class="customer-meta-card">
                <div class="customer-meta-label">Заказчик</div>
                <div class="customer-meta-value">{{ detail.deal.customer_name || 'Не указан' }}</div>
              </div>
              <div class="customer-meta-card">
                <div class="customer-meta-label">Наша компания</div>
                <div class="customer-meta-value">{{ detail.deal.our_company_name || 'Не указана' }}</div>
              </div>
            </div>
            <section class="customer-view-tabs customer-view-tabs--hero">
              <button
                class="customer-view-tab"
                :class="{ active: activeView === 'documents' }"
                type="button"
                @click="activeView = 'documents'"
              >
                Документы
              </button>
              <button
                class="customer-view-tab"
                :class="{ active: activeView === 'gantt' }"
                type="button"
                @click="activeView = 'gantt'"
              >
                Гант
              </button>
              <button
                class="customer-view-tab"
                :class="{ active: activeView === 'letters' }"
                type="button"
                @click="activeView = 'letters'"
              >
                Письма
              </button>
            </section>
          </div>

          <aside class="customer-summary-card">
            <div class="customer-summary-head">
              <span>Сводка проекта</span>
              <span class="customer-summary-status" :class="`is-${detail.deal.status || 'active'}`">
                {{ dealStatusLabel(detail.deal.status) }}
              </span>
            </div>
            <div class="customer-summary-metric">
              <span>Стоимость договора</span>
              <strong>{{ formatMoney(detail.deal.total_contract_value) }}</strong>
            </div>
            <div class="customer-summary-metric">
              <span>Оплачено</span>
              <strong>{{ formatMoney(detail.payment_summary?.paid_amount) }}</strong>
            </div>
            <div class="customer-summary-metric">
              <span>Ожидает</span>
              <strong>{{ formatMoney(detail.payment_summary?.pending_amount) }}</strong>
            </div>
            <div class="customer-summary-metric">
              <span>Платежей</span>
              <strong>{{ detail.payment_summary?.count || 0 }}</strong>
            </div>
            <div class="customer-summary-metric">
              <span>Писем</span>
              <strong>{{ detail.letters?.length || 0 }}</strong>
            </div>
            <div class="customer-summary-actions">
              <button
                class="customer-summary-toggle"
                :class="{ active: paymentsExpanded }"
                type="button"
                @click="paymentsExpanded = !paymentsExpanded"
              >
                <span>{{ paymentsExpanded ? 'Скрыть платежи' : 'Больше' }}</span>
                <i class="fas" :class="paymentsExpanded ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
              </button>
            </div>

            <div v-if="paymentsExpanded" class="customer-payments-popover">
              <div class="customer-payments-popover-head">
                <strong>Платежи по проекту</strong>
                <span>{{ detail.payment_summary?.count || 0 }}</span>
              </div>
              <div v-if="detail.payments?.length" class="customer-payments-popover-list">
                <div
                  v-for="payment in detail.payments"
                  :key="payment.id"
                  class="customer-payments-popover-item"
                >
                  <div class="customer-payments-popover-main">
                    <div class="customer-payments-popover-date">
                      {{ formatDate(payment.actual_date || payment.plan_date) }}
                    </div>
                    <div class="customer-payments-popover-direction">
                      {{ payment.direction === 'income' ? 'Входящий' : 'Исходящий' }}
                    </div>
                  </div>
                  <div class="customer-payments-popover-side">
                    <span class="customer-status-pill" :class="`is-${payment.payment_status || 'planned'}`">
                      {{ paymentStatusLabel(payment.payment_status) }}
                    </span>
                    <strong>{{ formatMoney(payment.amount) }}</strong>
                  </div>
                </div>
              </div>
              <div v-else class="customer-empty customer-empty--inline customer-empty--summary">
                <span>Платежей пока нет</span>
              </div>
            </div>
          </aside>
        </section>

        <template v-if="activeView === 'documents'">
          <section class="customer-docs-grid">
            <article
              v-for="section in detail.document_sections || []"
              :key="section.key"
              class="customer-card customer-doc-card"
            >
              <div class="customer-card-head">
                <h2>{{ section.label }}</h2>
                <div class="customer-card-actions">
                  <button
                    v-if="storageState[section.key]?.stack?.length"
                    class="customer-icon-btn"
                    title="Назад"
                    @click="goSectionBack(section.key)"
                  >
                    <i class="fas fa-arrow-left"></i>
                  </button>
                  <button
                    v-if="storageState[section.key]?.stack?.length"
                    class="customer-icon-btn"
                    title="Корень"
                    @click="goSectionRoot(section.key)"
                  >
                    <i class="fas fa-home"></i>
                  </button>
                </div>
              </div>
              <div v-if="storageState[section.key]?.stack?.length" class="customer-doc-breadcrumb">
                {{ sectionBreadcrumb(section.key, section.label) }}
              </div>
              <div v-if="storageState[section.key]?.loading" class="customer-empty customer-empty--inline">
                <i class="fas fa-spinner fa-spin"></i>
              </div>
              <div v-else-if="!(storageState[section.key]?.items || []).length" class="customer-empty customer-empty--inline">
                <span>Нет файлов</span>
              </div>
              <div v-else class="customer-doc-list">
                <button
                  v-for="item in storageState[section.key].items"
                  :key="item.path"
                  class="customer-doc-item"
                  @click="openSectionItem(section.key, item)"
                >
                  <i class="fas" :class="item.type === 'folder' ? 'fa-folder text-warning' : fileIcon(item.name)"></i>
                  <span :title="item.name">{{ item.name }}</span>
                </button>
              </div>
            </article>
          </section>
        </template>

        <section v-else-if="activeView === 'gantt'" class="customer-card customer-card--gantt">
          <div class="customer-card-head">
            <h2>Диаграмма Ганта по товарам</h2>
            <span class="customer-card-badge">{{ customerGanttGroups.length }}</span>
          </div>
          <ExecutionGantt
            :groups="customerGanttGroups"
            search-placeholder="Поиск по этапам, товарам и подзадачам..."
            empty-title="Нет данных для диаграммы"
            empty-hint="Когда по проекту появятся товары и сроки, здесь появится диаграмма."
            group-count-label="поз."
            export-filename="customer-gantt.csv"
          />
        </section>

        <section v-else class="customer-card">
          <div class="customer-card-head">
            <h2>Письма</h2>
            <span class="customer-card-badge">{{ detail.letters?.length || 0 }}</span>
          </div>
          <div class="customer-table-wrap">
            <table class="customer-table">
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Исх. №</th>
                  <th>Тема</th>
                  <th>Наша компания</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="letter in paginatedLetters" :key="letter.id">
                  <td>{{ formatDate(letter.letter_date) }}</td>
                  <td>{{ letter.outgoing_number }}</td>
                  <td>{{ letter.subject }}</td>
                  <td>{{ letter.our_company_label }}</td>
                  <td class="customer-table-action">
                    <button class="customer-link-btn" @click="downloadLetter(letter)">
                      Скачать PDF
                    </button>
                  </td>
                </tr>
                <tr v-if="!paginatedLetters.length">
                  <td colspan="5">
                    <div class="customer-empty customer-empty--inline customer-empty--summary">
                      <span>Писем пока нет</span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="lettersTotalPages > 1" class="customer-pagination">
            <button
              class="customer-pagination-btn"
              type="button"
              :disabled="lettersPage <= 1"
              @click="lettersPage = Math.max(1, lettersPage - 1)"
            >
              Назад
            </button>
            <span class="customer-pagination-status">{{ lettersPage }} / {{ lettersTotalPages }}</span>
            <button
              class="customer-pagination-btn"
              type="button"
              :disabled="lettersPage >= lettersTotalPages"
              @click="lettersPage = Math.min(lettersTotalPages, lettersPage + 1)"
            >
              Вперёд
            </button>
          </div>
        </section>
      </template>

      <div v-else class="customer-empty">
        <i class="fas fa-circle-info"></i>
        <span>{{ errorMessage || 'Не удалось загрузить данные проекта.' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { api } from '../services/api'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import ExecutionGantt from '../components/ExecutionGantt.vue'
import { downloadFromApi } from '../utils/download'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const projects = ref([])
const activeProjectId = ref('')
const detail = ref(null)
const loading = ref(false)
const errorMessage = ref('')
const activeView = ref('documents')
const paymentsExpanded = ref(false)
const lettersPage = ref(1)
const LETTERS_PAGE_SIZE = 10

const isUnauthorizedError = (error) => Number(error?.response?.status) === 401

const storageState = reactive({
  tz: { root: '', current: '', stack: [], items: [], loading: false },
  other: { root: '', current: '', stack: [], items: [], loading: false },
  results: { root: '', current: '', stack: [], items: [], loading: false }
})

const statusWeight = {
  overdue: 5,
  delayed: 5,
  partial: 4,
  in_progress: 3,
  completed: 2,
  paid: 2,
  planned: 1,
  not_started: 1,
  unpaid: 1
}

const normalizeStatus = (value) => {
  if (value === 'completed' || value === 'paid') return 'completed'
  if (value === 'in_progress' || value === 'partial') return 'in_progress'
  if (value === 'overdue' || value === 'delayed') return 'overdue'
  return 'planned'
}

const normalizeDate = (value) => {
  if (!value) return ''
  return String(value).slice(0, 10)
}

const formatDate = (value) => {
  const normalized = normalizeDate(value)
  if (!normalized) return '—'
  const [year, month, day] = normalized.split('-')
  return `${day}.${month}.${year}`
}

const formatMoney = (value) => {
  const number = Number(value || 0)
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 2
  }).format(number)
}

const paymentStatusLabel = (value) => {
  if (value === 'paid') return 'Оплачено'
  if (value === 'partial') return 'Частично'
  return 'Ожидает'
}

const dealStatusLabel = (value) => {
  if (value === 'completed') return 'Закрыт'
  if (value === 'active') return 'Активен'
  if (value === 'paused') return 'Пауза'
  return 'В работе'
}

const todayIso = () => new Date().toISOString().slice(0, 10)

const minIsoDate = (values = []) => {
  const filtered = values.map(normalizeDate).filter(Boolean)
  return filtered.length ? filtered.sort()[0] : ''
}

const maxIsoDate = (values = []) => {
  const filtered = values.map(normalizeDate).filter(Boolean)
  return filtered.length ? filtered.sort().at(-1) || '' : ''
}

const dateProgressPercent = (startValue, dueValue, status) => {
  if (status === 'completed') return 100
  const start = normalizeDate(startValue)
  const due = normalizeDate(dueValue)
  if (!start || !due) return 0
  const startDate = new Date(`${start}T00:00:00`)
  const dueDate = new Date(`${due}T00:00:00`)
  if (Number.isNaN(startDate.getTime()) || Number.isNaN(dueDate.getTime())) return 0
  const totalDays = Math.round((dueDate.getTime() - startDate.getTime()) / 86400000)
  if (totalDays <= 0) return new Date() >= dueDate ? 100 : 0
  const today = new Date()
  const elapsedDays = Math.round((today.getTime() - startDate.getTime()) / 86400000)
  const ratio = (elapsedDays / totalDays) * 100
  return Math.max(0, Math.min(100, Math.round(ratio)))
}

const aggregateStatus = (items = []) => {
  if (!items.length) return 'planned'
  const normalized = items.map((item) => normalizeStatus(item?.status))
  if (normalized.every((status) => status === 'completed')) return 'completed'
  return normalized.sort((a, b) => (statusWeight[b] || 0) - (statusWeight[a] || 0))[0] || 'planned'
}

const aggregateProgress = (rows = []) => {
  if (!rows.length) return 0
  return Math.round(rows.reduce((sum, row) => sum + Number(row.progress || 0), 0) / rows.length)
}

const customerGanttGroups = computed(() => {
  const execution = detail.value?.execution?.stages || []
  return execution.map((stage) => {
    const stageStart = normalizeDate(stage.date_start || stage.date_end || todayIso())
    const items = (stage.products || []).map((product) => {
      const assignments = product.assignments || []
      const assignmentRows = assignments.flatMap((assignment) => {
        const fallbackStart = normalizeDate(assignment.start_date || stageStart)
        const fallbackDue = normalizeDate(assignment.due_date || assignment.contract_due_date || stage.date_end || stageStart)
        return (assignment.subtasks || []).map((subtask, index) => ({
          id: subtask.id || `${assignment.id}-${index}`,
          name: subtask.title || `Подзадача ${index + 1}`,
          status: normalizeStatus(subtask.status),
          progress: dateProgressPercent(fallbackStart, subtask.due_date || fallbackDue, normalizeStatus(subtask.status)),
          startDate: fallbackStart,
          endDate: normalizeDate(subtask.due_date || fallbackDue),
          children: []
        }))
      })
      const startDate = minIsoDate(assignments.map((assignment) => assignment.start_date)) || stageStart
      const dueDate = maxIsoDate(assignments.map((assignment) => assignment.due_date)) || normalizeDate(stage.date_end || stageStart)
      const contractDueDate = maxIsoDate(assignments.map((assignment) => assignment.contract_due_date))
      const status = aggregateStatus(assignments)
      return {
        id: product.deal_product_id,
        name: product.name,
        status,
        progress: dateProgressPercent(startDate, dueDate || contractDueDate || stage.date_end || stageStart, status),
        startDate,
        endDate: dueDate || contractDueDate || normalizeDate(stage.date_end || stageStart),
        contractDueDate,
        children: assignmentRows
      }
    })

    return {
      id: stage.id,
      name: stage.name,
      status: aggregateStatus(items),
      progress: aggregateProgress(items),
      startDate: normalizeDate(stage.date_start || stageStart),
      endDate: normalizeDate(stage.date_end || maxIsoDate(items.map((item) => item.endDate)) || stageStart),
      items
    }
  })
})

const letters = computed(() => detail.value?.letters || [])

const lettersTotalPages = computed(() => {
  return Math.max(1, Math.ceil(letters.value.length / LETTERS_PAGE_SIZE))
})

const paginatedLetters = computed(() => {
  const start = (lettersPage.value - 1) * LETTERS_PAGE_SIZE
  return letters.value.slice(start, start + LETTERS_PAGE_SIZE)
})

const syncQuery = async (projectId) => {
  const nextQuery = { ...route.query }
  if (projectId) {
    nextQuery.project = projectId
  } else {
    delete nextQuery.project
  }
  if (nextQuery.project === route.query.project) return
  await router.replace({ query: nextQuery })
}

const resetStorageState = () => {
  for (const key of ['tz', 'other', 'results']) {
    storageState[key].root = ''
    storageState[key].current = ''
    storageState[key].stack = []
    storageState[key].items = []
    storageState[key].loading = false
  }
}

const loadStorageSection = async (sectionKey, path = '') => {
  if (!activeProjectId.value) return
  const state = storageState[sectionKey]
  if (!state) return
  state.loading = true
  try {
    const params = { section: sectionKey }
    if (path) params.path = path
    const data = await api.customer.projectStorageList(activeProjectId.value, params)
    state.root = data.root_path
    state.current = data.current_path
    state.items = data.items || []
    const rootPath = String(data.root_path || '')
    const currentPath = String(data.current_path || '')
    if (!currentPath || currentPath === rootPath) {
      state.stack = []
    } else {
      const relative = currentPath.slice(rootPath.length).replace(/^[/\\]+/, '')
      const parts = relative.split('/').filter(Boolean)
      state.stack = parts.map((name, index) => ({
        name,
        path: `${rootPath}/${parts.slice(0, index + 1).join('/')}`
      }))
    }
  } catch (error) {
    console.error(`Error loading customer storage section ${sectionKey}:`, error)
    state.items = []
  } finally {
    state.loading = false
  }
}

const loadProjects = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await api.customer.listProjects()
    projects.value = data || []
    if (!projects.value.length) {
      activeProjectId.value = ''
      detail.value = null
      resetStorageState()
      await syncQuery('')
      return
    }
    const requestedId = String(route.query.project || '')
    const resolvedId = projects.value.some((item) => item.id === requestedId) ? requestedId : projects.value[0].id
    await selectProject(resolvedId, false)
  } catch (error) {
    if (isUnauthorizedError(error)) {
      try {
        await authStore.restoreSession(true)
        const retryData = await api.customer.listProjects()
        projects.value = retryData || []
        if (!projects.value.length) {
          activeProjectId.value = ''
          detail.value = null
          resetStorageState()
          await syncQuery('')
          return
        }
        const requestedId = String(route.query.project || '')
        const resolvedId = projects.value.some((item) => item.id === requestedId) ? requestedId : projects.value[0].id
        await selectProject(resolvedId, false)
        return
      } catch (retryError) {
        console.error('Error loading customer projects after session restore:', retryError)
        error = retryError
      }
    }
    console.error('Error loading customer projects:', error)
    projects.value = []
    detail.value = null
    errorMessage.value = 'Не удалось загрузить проекты заказчика.'
  } finally {
    loading.value = false
  }
}

const loadProjectDetail = async (projectId) => {
  loading.value = true
  errorMessage.value = ''
  paymentsExpanded.value = false
  lettersPage.value = 1
  try {
    const data = await api.customer.getProject(projectId)
    detail.value = data
    await Promise.all((data.document_sections || []).map((section) => loadStorageSection(section.key)))
  } catch (error) {
    console.error('Error loading customer project detail:', error)
    detail.value = null
    errorMessage.value = 'Не удалось загрузить данные проекта.'
  } finally {
    loading.value = false
  }
}

const selectProject = async (projectId, updateQuery = true) => {
  if (!projectId) return
  if (activeProjectId.value === projectId && detail.value) {
    if (updateQuery) await syncQuery(projectId)
    return
  }
  activeProjectId.value = projectId
  activeView.value = 'documents'
  paymentsExpanded.value = false
  lettersPage.value = 1
  resetStorageState()
  if (updateQuery) await syncQuery(projectId)
  await loadProjectDetail(projectId)
}

const reloadActiveProject = async () => {
  if (!activeProjectId.value) return
  await loadProjectDetail(activeProjectId.value)
}

const sectionBreadcrumb = (sectionKey, label) => {
  const stack = storageState[sectionKey]?.stack || []
  return stack.map((item) => item.name).join(' / ')
}

const openSectionItem = async (sectionKey, item) => {
  if (!activeProjectId.value || !item?.path) return
  if (item.type === 'folder') {
    await loadStorageSection(sectionKey, item.path)
    return
  }
  await downloadFromApi(
    `/api/v1/customer/projects/${activeProjectId.value}/storage/download?section=${encodeURIComponent(sectionKey)}&path=${encodeURIComponent(item.path)}`,
    {},
    item.name || 'file'
  )
}

const goSectionBack = async (sectionKey) => {
  const state = storageState[sectionKey]
  if (!state?.stack?.length) return
  const nextStack = state.stack.slice(0, -1)
  const nextPath = nextStack.length ? nextStack.at(-1).path : state.root
  await loadStorageSection(sectionKey, nextPath || '')
}

const goSectionRoot = async (sectionKey) => {
  await loadStorageSection(sectionKey, '')
}

const downloadLetter = async (letter) => {
  if (!activeProjectId.value || !letter?.id) return
  await downloadFromApi(
    `/api/v1/customer/projects/${activeProjectId.value}/letters/${letter.id}/download`,
    {},
    letter.file_name || `${letter.outgoing_number || 'letter'}.pdf`
  )
}

const fileIcon = (name = '') => {
  const lower = String(name).toLowerCase()
  if (lower.endsWith('.pdf')) return 'fa-file-pdf text-danger'
  if (lower.endsWith('.doc') || lower.endsWith('.docx')) return 'fa-file-word text-primary'
  if (lower.endsWith('.xls') || lower.endsWith('.xlsx') || lower.endsWith('.csv')) return 'fa-file-excel text-success'
  return 'fa-file text-muted'
}

watch(
  () => route.query.project,
  async (value) => {
    const requestedId = String(value || '')
    if (!requestedId || !projects.value.some((item) => item.id === requestedId) || requestedId === activeProjectId.value) {
      return
    }
    await selectProject(requestedId, false)
  }
)

onMounted(async () => {
  await authStore.restoreSession(true)
  await loadProjects()
})
</script>

<style scoped>
.customer-panel {
  min-height: 100%;
  padding: 20px;
}

.customer-shell {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-height: calc(100vh - 120px);
}

.customer-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.customer-breadcrumbs {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.customer-breadcrumbs-label {
  font-size: 0.84rem;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.customer-crumb {
  border: 1px solid rgba(37, 99, 235, 0.14);
  background: rgba(255, 255, 255, 0.9);
  color: #1e293b;
  border-radius: 999px;
  padding: 9px 14px;
  font-size: 0.92rem;
  font-weight: 600;
  transition: 0.2s ease;
}

.customer-crumb.active {
  background: rgba(37, 99, 235, 0.12);
  color: #2563eb;
  border-color: rgba(37, 99, 235, 0.24);
}

.customer-refresh {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: rgba(255, 255, 255, 0.88);
  color: #1e293b;
}

.customer-hero,
.customer-card {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.15);
  border-radius: 22px;
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(18px);
}

.customer-hero {
  position: relative;
  z-index: 4;
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(280px, 0.9fr);
  gap: 18px;
  padding: 24px;
}

.customer-hero-main {
  min-width: 0;
}

.customer-hero-eyebrow {
  font-size: 0.78rem;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 8px;
}

.customer-title {
  margin: 0 0 16px;
  font-size: 2rem;
  line-height: 1.1;
  color: #0f172a;
}

.customer-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.customer-meta-card {
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 18px;
  padding: 14px 16px;
  background: rgba(248, 250, 252, 0.72);
}

.customer-meta-label {
  font-size: 0.78rem;
  color: #64748b;
  margin-bottom: 6px;
}

.customer-meta-value {
  font-size: 0.98rem;
  line-height: 1.45;
  color: #0f172a;
  font-weight: 600;
}

.customer-summary-card {
  position: relative;
  z-index: 8;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 20px;
  padding: 18px;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.92), rgba(241, 245, 249, 0.8));
}

.customer-summary-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  font-size: 0.88rem;
  color: #475569;
  font-weight: 700;
}

.customer-summary-status,
.customer-status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
  border: 1px solid transparent;
}

.customer-summary-metric {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-top: 1px solid rgba(148, 163, 184, 0.14);
}

.customer-summary-metric:first-of-type {
  border-top: none;
  padding-top: 0;
}

.customer-summary-metric span {
  color: #64748b;
}

.customer-summary-metric strong {
  color: #0f172a;
}

.customer-summary-actions {
  margin-top: 14px;
}

.customer-summary-toggle {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid rgba(37, 99, 235, 0.18);
  background: rgba(255, 255, 255, 0.88);
  color: #1d4ed8;
  font-size: 0.88rem;
  font-weight: 700;
}

.customer-summary-toggle.active {
  background: rgba(37, 99, 235, 0.08);
}

.customer-payments-popover {
  position: absolute;
  top: calc(100% + 12px);
  left: 0;
  right: 0;
  z-index: 40;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.14);
  backdrop-filter: blur(18px);
}

.customer-payments-popover-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: #475569;
  font-size: 0.84rem;
}

.customer-payments-popover-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 320px;
  overflow: auto;
}

.customer-payments-popover-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  background: rgba(248, 250, 252, 0.8);
}

.customer-payments-popover-main,
.customer-payments-popover-side {
  display: flex;
  align-items: center;
  gap: 10px;
}

.customer-payments-popover-date {
  font-weight: 700;
  color: #0f172a;
  white-space: nowrap;
}

.customer-payments-popover-direction {
  color: #64748b;
  font-size: 0.84rem;
}

.customer-payments-popover-side {
  margin-left: auto;
}

.customer-payments-popover-side strong {
  color: #0f172a;
  white-space: nowrap;
}

.customer-view-tabs {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  width: fit-content;
  padding: 6px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(16px);
}

.customer-view-tabs--hero {
  margin-top: 16px;
}

.customer-view-tab {
  border: none;
  background: transparent;
  color: #64748b;
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 0.9rem;
  font-weight: 700;
}

.customer-view-tab.active {
  background: rgba(37, 99, 235, 0.12);
  color: #2563eb;
}

.customer-docs-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.customer-card {
  padding: 20px;
}

.customer-card--gantt {
  padding-bottom: 16px;
}

.customer-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.customer-card-head h2 {
  margin: 0;
  font-size: 1.08rem;
  color: #0f172a;
}

.customer-card-badge {
  min-width: 28px;
  height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.1);
  color: #2563eb;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 700;
}

.customer-card-actions {
  display: flex;
  gap: 8px;
}

.customer-icon-btn {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.9);
  color: #475569;
}

.customer-table-wrap {
  overflow: auto;
}

.customer-table {
  width: 100%;
  border-collapse: collapse;
}

.customer-table th,
.customer-table td {
  padding: 12px 10px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
  text-align: left;
  font-size: 0.92rem;
}

.customer-table th {
  color: #64748b;
  font-size: 0.76rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.customer-table-action {
  text-align: right;
}

.customer-pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 14px;
}

.customer-pagination-btn {
  min-width: 102px;
  height: 38px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.88);
  color: #0f172a;
  font-weight: 700;
}

.customer-pagination-btn:disabled {
  opacity: 0.45;
  cursor: default;
}

.customer-pagination-status {
  min-width: 64px;
  text-align: center;
  color: #64748b;
  font-size: 0.9rem;
  font-weight: 700;
}

.customer-link-btn {
  border: none;
  background: transparent;
  color: #2563eb;
  font-weight: 700;
}

.customer-doc-card {
  min-height: 260px;
}

.customer-doc-breadcrumb {
  margin-bottom: 12px;
  color: #64748b;
  font-size: 0.82rem;
}

.customer-doc-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.customer-doc-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.72);
  padding: 10px 12px;
  color: #0f172a;
  text-align: left;
}

.customer-doc-item span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.customer-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 240px;
  border-radius: 20px;
  border: 1px dashed rgba(148, 163, 184, 0.24);
  background: rgba(255, 255, 255, 0.7);
  color: #64748b;
}

.customer-empty--inline {
  min-height: 140px;
}

.customer-empty--summary {
  min-height: 100px;
}

.customer-summary-status.is-active,
.customer-status-pill.is-completed {
  color: #15803d;
  background: rgba(220, 252, 231, 0.9);
  border-color: rgba(34, 197, 94, 0.25);
}

.customer-summary-status.is-paused,
.customer-status-pill.is-planned {
  color: #92400e;
  background: rgba(254, 243, 199, 0.9);
  border-color: rgba(245, 158, 11, 0.25);
}

.customer-summary-status.is-completed,
.customer-status-pill.is-in_progress {
  color: #1d4ed8;
  background: rgba(219, 234, 254, 0.9);
  border-color: rgba(59, 130, 246, 0.25);
}

.customer-status-pill.is-overdue {
  color: #b91c1c;
  background: rgba(254, 226, 226, 0.92);
  border-color: rgba(239, 68, 68, 0.24);
}

[data-theme="dark"] .customer-hero,
[data-theme="dark"] .customer-card,
[data-theme="dark"] .customer-refresh,
[data-theme="dark"] .customer-crumb,
[data-theme="dark"] .customer-view-tabs,
[data-theme="dark"] .customer-summary-toggle,
[data-theme="dark"] .customer-payments-popover,
[data-theme="dark"] .customer-icon-btn,
[data-theme="dark"] .customer-doc-item,
[data-theme="dark"] .customer-empty {
  background: rgba(15, 23, 42, 0.76);
  border-color: rgba(148, 163, 184, 0.14);
  color: #e2e8f0;
}

[data-theme="dark"] .customer-title,
[data-theme="dark"] .customer-meta-value,
[data-theme="dark"] .customer-summary-metric strong,
[data-theme="dark"] .customer-payments-popover-date,
[data-theme="dark"] .customer-payments-popover-side strong,
[data-theme="dark"] .customer-card-head h2,
[data-theme="dark"] .customer-doc-item,
[data-theme="dark"] .customer-table td {
  color: #f8fafc;
}

[data-theme="dark"] .customer-meta-card,
[data-theme="dark"] .customer-payments-popover-item {
  background: rgba(30, 41, 59, 0.75);
  border-color: rgba(148, 163, 184, 0.14);
}

[data-theme="dark"] .customer-pagination-btn {
  background: rgba(15, 23, 42, 0.76);
  border-color: rgba(148, 163, 184, 0.14);
  color: #f8fafc;
}

[data-theme="dark"] .customer-table th,
[data-theme="dark"] .customer-meta-label,
[data-theme="dark"] .customer-summary-metric span,
[data-theme="dark"] .customer-payments-popover-direction,
[data-theme="dark"] .customer-breadcrumbs-label,
[data-theme="dark"] .customer-doc-breadcrumb {
  color: #94a3b8;
}

@media (max-width: 1180px) {
  .customer-hero,
  .customer-docs-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1400px) {
  .customer-docs-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .customer-panel {
    padding: 12px;
  }

  .customer-shell {
    gap: 14px;
  }

  .customer-topbar {
    flex-direction: column;
    align-items: stretch;
  }

  .customer-meta-grid {
    grid-template-columns: 1fr;
  }

  .customer-view-tabs {
    width: 100%;
    justify-content: space-between;
  }

  .customer-payments-popover {
    position: static;
    margin-top: 12px;
  }

  .customer-payments-popover-item,
  .customer-payments-popover-main,
  .customer-payments-popover-side {
    flex-direction: column;
    align-items: flex-start;
  }

  .customer-payments-popover-side {
    margin-left: 0;
  }
}
</style>
