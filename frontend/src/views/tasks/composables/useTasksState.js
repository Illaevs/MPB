import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../../../stores/auth'
import { useCompaniesStore } from '../../../stores/companies'
import { useUsersStore } from '../../../stores/users'
import { hasSectionAccess, getActiveUser, saveActiveUser, getStoredPermissions } from '../../../utils/permissions'
import { normalizeAvatarUrl } from '../../../utils/avatar'
import { expenseCategories } from '../../../utils/categories'
import { useToast } from '../../../composables/useToast'
import { useConfirm } from '../../../composables/useConfirm'
import { downloadFromApi } from '../../../utils/download'
import * as apiTasks from '../../../services/api/tasks'
import { get as apiGet } from '../../../services/api/_client'

const AVATAR_THEMES = [
  { background: 'linear-gradient(135deg, #ffe2c1 0%, #f8c27e 100%)', color: '#9a4d00' },
  { background: 'linear-gradient(135deg, #dbeafe 0%, #9cc5ff 100%)', color: '#1d4ed8' },
  { background: 'linear-gradient(135deg, #ede9fe 0%, #c4b5fd 100%)', color: '#5b21b6' },
  { background: 'linear-gradient(135deg, #dcfce7 0%, #86efac 100%)', color: '#166534' },
  { background: 'linear-gradient(135deg, #fee2e2 0%, #fca5a5 100%)', color: '#b91c1c' }
]

/**
 * Tasks view shared state and methods.
 *
 * All previous direct `axios.*` calls have been migrated to `api.tasks.*` via
 * `services/api/tasks.js`. The only remaining `axios` import is the deals
 * listing call, which lives outside the tasks API module — handled via a
 * generic `_client.get`.
 *
 * No raw axios calls remain in this composable.
 */
export function useTasksState() {
  const { success: toastSuccess, error: toastError, warning: toastWarning } = useToast()
  const { confirm: askConfirm } = useConfirm()
  const companiesStore = useCompaniesStore()
  const usersStore = useUsersStore()
  const authStore = useAuthStore()
  const route = useRoute()

  const isTouchDevice = typeof window !== 'undefined' && (
    (window.matchMedia && window.matchMedia('(pointer: coarse)').matches) ||
    navigator.maxTouchPoints > 0
  )

  const brokenAvatarUrls = ref(new Set())
  const taskApprovalState = ref({
    activeInstance: null,
    latestInstance: null,
    latestStatus: null,
    templateCount: 0,
  })

  const showConfirm = async (title, text, action, opts = {}) => {
    const ok = await askConfirm({
      title,
      message: text,
      confirmText: opts.confirmText || 'Подтвердить',
      cancelText: opts.cancelText || 'Отмена',
      variant: opts.variant || 'danger',
    })
    if (ok && typeof action === 'function') await action()
  }

  // Permissions
  const canManageAuctions = computed(() => hasSectionAccess('task_auctions_manage'))
  const canBidAuctions = computed(() => hasSectionAccess('task_auctions_bid'))
  const canManagePenalties = computed(() => hasSectionAccess('tasks_penalties_manage'))

  // View mode
  const viewMode = ref('tasks')

  // Tasks state
  const tasks = ref([])
  const projects = ref([])
  const users = ref([])
  const companies = ref([])
  const loading = ref(false)
  const saving = ref(false)
  const initialTaskOpened = ref(false)
  const showCreateModal = ref(false)
  const isEditing = ref(false)
  const activeUser = ref(getActiveUser())
  const taskChatPermissions = ref(authStore.permissions?.task_chat || getStoredPermissions()?.task_chat || {})

  const syncTaskChatUser = () => {
    activeUser.value = getActiveUser()
    taskChatPermissions.value = authStore.permissions?.task_chat || getStoredPermissions()?.task_chat || {}
  }

  const handlePermissionsUpdate = () => {
    syncTaskChatUser()
  }

  const isSuperUser = computed(() => {
    if (authStore.isSuperuser) return true
    return Boolean(taskChatPermissions.value?.__superuser?.read_all || getStoredPermissions()?.__superuser?.read_all)
  })

  const getDefaultTaskForm = () => ({
    title: '', description: '', deal_id: '', stage_id: null,
    status: 'new', priority: 'normal', assigned_to_user_id: null, created_by_user_id: null,
    assignee_ids: [], watcher_ids: [],
    start_date: null, due_date: null, due_time: null,
    estimated_hours: 0, actual_hours: 0,
    budget: null, category_code: null, work_category: '', payer_id: '', payee_id: '',
    tags: [], attachments: [], notify_assigned: true, notify_overdue: true,
    executor_rating: null,
    final_budget: null, rating_coefficient: null, deadline_coefficient: null, penalty_amount: null
  })

  const taskForm = ref(getDefaultTaskForm())
  const taskFormSnapshot = ref('')
  const taskAttachmentInput = ref(null)
  const taskPendingFiles = ref([])
  const taskAttachmentDragActive = ref(false)

  const taskChatVisible = computed(() => {
    if (!isEditing.value || !taskForm.value?.id) return false
    if (isSuperUser.value) return true
    const perms = taskChatPermissions.value || {}
    if (perms.read_all) return true
    if (perms.read_assigned && taskForm.value.assigned_to_user_id) {
      const active = activeUser.value
      if (!active) return false
      return String(taskForm.value.assigned_to_user_id) === String(active.id)
    }
    return false
  })

  const taskModalStyle = computed(() => ({ maxWidth: '1320px' }))

  const getDefaultTaskFilters = () => ({
    deal_id: '', status: '', priority: '', assigned_to_user_id: '',
    due_date_from: '', due_date_to: '',
    overdue: false, has_budget: '', source: '',
    category_code: '', work_category: '',
    search: '',
  })

  const filters = ref(getDefaultTaskFilters())
  const taskFiltersDraft = ref(getDefaultTaskFilters())
  const showTaskFiltersModal = ref(false)
  let searchDebounceTimer = null

  const selectedTaskIds = ref(new Set())
  const bulkBusy = ref(false)

  const taskSheetAsideCollapsed = ref(localStorage.getItem('tasks-aside-collapsed') === '1')
  const asideTab = ref(localStorage.getItem('tasks-aside-tab') || 'approval')
  watch(asideTab, (val) => { localStorage.setItem('tasks-aside-tab', val) })
  const toggleTaskSheetAside = () => {
    taskSheetAsideCollapsed.value = !taskSheetAsideCollapsed.value
    localStorage.setItem('tasks-aside-collapsed', taskSheetAsideCollapsed.value ? '1' : '0')
  }

  let autoDraftTimer = null
  let autoDraftFired = false

  const avatarStyleCache = new Map()
  const taskValidation = ref({ title: '', date: '' })

  const loadErrors = ref({ tasks: '', projects: '', users: '', companies: '' })

  const taskPagination = ref({
    page: 1,
    pageSize: parseInt(localStorage.getItem('tasks-page-size') || '20', 10) || 20,
    hasNext: false,
    total: 0,
  })

  const totalPages = computed(() => {
    const ps = taskPagination.value.pageSize || 20
    const t = taskPagination.value.total || 0
    return Math.max(1, Math.ceil(t / ps))
  })

  const taskSort = ref({ by: 'created_at', dir: 'desc' })

  const taskLayout = ref(localStorage.getItem('tasks-layout') || 'kanban')
  const draggedTaskId = ref(null)
  const kanbanDropKey = ref('')
  const matrixDropKey = ref('')
  const updatingTaskId = ref(null)

  const taskKanbanColumnDefs = [
    { key: 'new', label: 'Новые', color: '#b1ab1d' },
    { key: 'in_progress', label: 'В работе', color: '#3f8cff' },
    { key: 'pending', label: 'Ожидает', color: '#d28e3d' },
    { key: 'deferred', label: 'Отложено', color: '#6d5dd3' },
    { key: 'completed', label: 'Завершено', color: '#2f9b64' },
    { key: 'cancelled', label: 'Отменено', color: '#af4b4b' }
  ]

  const taskMatrixColumnDefs = [
    { key: 'urgent_important', label: 'Срочно и важно', action: 'Сделать немедленно', color: '#ef4444', bg: 'rgba(254, 242, 242, 0.72)' },
    { key: 'not_urgent_important', label: 'Не срочно, но важно', action: 'Запланировать', color: '#3b82f6', bg: 'rgba(239, 246, 255, 0.72)' },
    { key: 'urgent_not_important', label: 'Срочно, но не важно', action: 'Делегировать', color: '#f97316', bg: 'rgba(255, 247, 237, 0.72)' },
    { key: 'not_urgent_not_important', label: 'Не срочно и не важно', action: 'Удалить / отложить', color: '#94a3b8', bg: 'rgba(248, 250, 252, 0.82)' }
  ]
  const makeEmptyMatrixColumns = () => taskMatrixColumnDefs.reduce((acc, item) => { acc[item.key] = []; return acc }, {})
  const matrixColumnTasks = ref(makeEmptyMatrixColumns())

  const workCategories = ['Юридическая', 'Производственная', 'Административная']

  // Auctions state
  const auctions = ref([])
  const auctionsLoading = ref(false)
  const showAuctionModal = ref(false)
  const editingAuction = ref(null)
  const savingAuction = ref(false)
  const auctionFilters = ref({ status: '', deal_id: '' })
  const expandedAuctionIds = ref([])
  const activeSubtaskId = ref(null)

  const getDefaultAuctionForm = () => ({
    title: '', description: '', budget: 0, deal_id: '', category_code: '',
    allow_custom_price: false, mode: 'single', items: []
  })
  const auctionForm = ref(getDefaultAuctionForm())
  const auctionFormSnapshot = ref('')

  const blockBudget = computed(() => (auctionForm.value.items || []).reduce((sum, item) => {
    const value = Number(item.budget || 0)
    return sum + (Number.isFinite(value) ? value : 0)
  }, 0))

  // Bids
  const showBidsModal = ref(false)
  const selectedAuction = ref(null)
  const auctionBids = ref([])
  const showAwardModal = ref(false)
  const awardForm = ref({ category_code: '', payer_id: '', payee_id: '', due_date: '' })
  const awardingBid = ref(null)
  const awardingWinner = ref(false)

  const showBidModal = ref(false)
  const bidForm = ref({ bid_price: 0, comment: '', block_mode: 'block_only' })
  const submittingBid = ref(false)

  // Rating
  const showRatingModal = ref(false)
  const ratingTask = ref(null)
  const selectedRating = ref(0)
  const submittingRating = ref(false)
  const recalculatingPenalty = ref(false)

  // Penalty Rules
  const penaltyRules = ref([])
  const rulesLoading = ref(false)
  const showRuleModal = ref(false)
  const editingRule = ref(null)
  const ruleForm = ref({
    rule_type: 'rating', condition_min: 0, condition_max: 0,
    coefficient: 1, description: '', is_active: true
  })
  const savingRule = ref(false)
  const seedingRules = ref(false)

  const ratingRules = computed(() => penaltyRules.value.filter(r => r.rule_type === 'rating'))
  const deadlineRules = computed(() => penaltyRules.value.filter(r => r.rule_type === 'deadline'))
  const canRecalculatePenalty = computed(() => {
    const budgetValue = Number(taskForm.value.budget || 0)
    return !!(canManagePenalties.value && isEditing.value &&
      taskForm.value.status === 'completed' && taskForm.value.executor_rating && budgetValue > 0)
  })

  const toComparable = (value) => JSON.stringify(value ?? {})
  const getTaskFormComparable = () => toComparable({
    ...taskForm.value,
    __pendingFiles: taskPendingFiles.value.map(file => ({
      name: file.name, size: file.size, lastModified: file.lastModified
    }))
  })
  const setTaskFormSnapshot = () => { taskFormSnapshot.value = getTaskFormComparable() }
  const setAuctionFormSnapshot = () => { auctionFormSnapshot.value = toComparable(auctionForm.value) }
  const hasTaskFormChanges = computed(() => showCreateModal.value && getTaskFormComparable() !== taskFormSnapshot.value)
  const hasAuctionFormChanges = computed(() => showAuctionModal.value && toComparable(auctionForm.value) !== auctionFormSnapshot.value)

  const priorityOrder = { low: 1, normal: 2, high: 3, urgent: 4 }
  const statusOrder = { new: 1, in_progress: 2, pending: 3, deferred: 4, completed: 5, cancelled: 6 }

  const sortedTasks = computed(() => {
    const by = taskSort.value.by
    const dir = taskSort.value.dir === 'asc' ? 1 : -1
    const list = [...tasks.value]
    const valueBy = (task) => {
      if (by === 'number') return Number(task.number ?? 0)
      if (by === 'priority') return priorityOrder[task.priority] ?? 0
      if (by === 'status') return statusOrder[task.status] ?? 0
      if (by === 'budget') return Number(task.budget ?? 0)
      if (by === 'due_date') return task.due_date ? new Date(task.due_date).getTime() : 0
      if (by === 'created_at') return task.created_at ? new Date(task.created_at).getTime() : 0
      if (by === 'title') return (task.title || '').toLowerCase()
      return task.created_at ? new Date(task.created_at).getTime() : 0
    }
    list.sort((a, b) => {
      const av = valueBy(a); const bv = valueBy(b)
      if (av < bv) return -1 * dir
      if (av > bv) return 1 * dir
      return 0
    })
    return list
  })

  const kanbanColumns = computed(() => taskKanbanColumnDefs.map((column) => ({
    ...column,
    tasks: sortedTasks.value.filter((task) => task.status === column.key)
  })))

  const resolveTaskMatrixQuadrant = (task) => {
    const explicit = task?.matrix_quadrant
    if (taskMatrixColumnDefs.some((item) => item.key === explicit)) return explicit
    const due = task?.due_date ? new Date(task.due_date) : null
    const today = new Date(); today.setHours(0, 0, 0, 0)
    const isUrgent = Boolean(due && !Number.isNaN(due.getTime()) && due <= today)
    const isImportant = ['high', 'urgent'].includes(task?.priority || 'normal')
    if (isUrgent && isImportant) return 'urgent_important'
    if (isImportant) return 'not_urgent_important'
    if (isUrgent) return 'urgent_not_important'
    return 'not_urgent_not_important'
  }

  const syncMatrixColumns = () => {
    const nextColumns = makeEmptyMatrixColumns()
    const sourceIndex = new Map(sortedTasks.value.map((task, index) => [String(task.id), index]))
    sortedTasks.value.forEach((task) => {
      const quadrant = resolveTaskMatrixQuadrant(task)
      nextColumns[quadrant].push(task)
    })
    taskMatrixColumnDefs.forEach((column) => {
      nextColumns[column.key].sort((left, right) => {
        const leftManual = left.matrix_sort_order !== null && left.matrix_sort_order !== undefined
        const rightManual = right.matrix_sort_order !== null && right.matrix_sort_order !== undefined
        if (leftManual !== rightManual) return leftManual ? -1 : 1
        if (leftManual && rightManual) {
          const diff = Number(left.matrix_sort_order || 0) - Number(right.matrix_sort_order || 0)
          if (diff !== 0) return diff
        }
        return (sourceIndex.get(String(left.id)) ?? 0) - (sourceIndex.get(String(right.id)) ?? 0)
      })
    })
    matrixColumnTasks.value = nextColumns
  }

  const matrixColumns = computed(() => taskMatrixColumnDefs.map((column) => ({
    ...column,
    tasks: matrixColumnTasks.value[column.key] || []
  })))

  // ===== TASKS API =====
  const loadTasks = async () => {
    loading.value = true
    loadErrors.value.tasks = ''
    try {
      const params = {}
      const f = filters.value
      if (f.deal_id) params.deal_id = f.deal_id
      if (f.status) params.status = f.status
      if (f.priority) params.priority = f.priority
      if (f.assigned_to_user_id) params.assigned_to_user_id = f.assigned_to_user_id
      if (f.due_date_from) params.due_date_from = f.due_date_from
      if (f.due_date_to) params.due_date_to = f.due_date_to
      if (f.overdue) params.overdue = true
      if (f.has_budget === true || f.has_budget === false) params.has_budget = f.has_budget
      if (f.source) params.source = f.source
      if (f.category_code) params.category_code = f.category_code
      if (f.work_category) params.work_category = f.work_category
      if (f.search) params.search = f.search
      params.skip = (taskPagination.value.page - 1) * taskPagination.value.pageSize
      params.limit = taskPagination.value.pageSize
      const res = await apiTasks.list(params)
      const items = Array.isArray(res.data) ? res.data : []
      tasks.value = items
      const headerTotal = res.headers?.['x-total-count'] ?? res.headers?.['X-Total-Count']
      taskPagination.value.total = headerTotal !== undefined && headerTotal !== null
        ? parseInt(headerTotal, 10) || 0
        : items.length
      taskPagination.value.hasNext = (taskPagination.value.page * taskPagination.value.pageSize) < taskPagination.value.total
      syncMatrixColumns()
      if (selectedTaskIds.value.size) {
        const onPage = new Set(items.map(t => String(t.id)))
        const next = new Set()
        selectedTaskIds.value.forEach(id => { if (onPage.has(String(id))) next.add(id) })
        selectedTaskIds.value = next
      }
    } catch (e) {
      console.error(e)
      tasks.value = []
      syncMatrixColumns()
      taskPagination.value.hasNext = false
      taskPagination.value.total = 0
      loadErrors.value.tasks = 'Не удалось загрузить задачи'
      toastError('Не удалось загрузить задачи')
    } finally { loading.value = false }
  }

  const loadProjects = async () => {
    loadErrors.value.projects = ''
    try {
      // Deals endpoint lives outside tasks domain — use generic _client.get
      const data = await apiGet('/api/v1/deals/')
      projects.value = Array.isArray(data) ? data : []
    } catch (e) {
      console.error(e)
      projects.value = []
      loadErrors.value.projects = 'Не удалось загрузить проекты'
    }
  }

  const loadUsers = async () => {
    loadErrors.value.users = ''
    try {
      await usersStore.ensureLoaded()
      users.value = usersStore.items
    } catch (e) {
      console.error(e)
      users.value = []
      loadErrors.value.users = 'Не удалось загрузить пользователей'
    }
  }

  const loadCompanies = async () => {
    loadErrors.value.companies = ''
    try {
      await companiesStore.ensureLoaded()
      companies.value = companiesStore.items
    } catch (e) {
      console.error(e)
      companies.value = []
      loadErrors.value.companies = 'Не удалось загрузить компании'
    }
  }

  const applyTaskFilters = () => { taskPagination.value.page = 1; loadTasks() }
  const openTaskFiltersModal = () => { taskFiltersDraft.value = { ...filters.value }; showTaskFiltersModal.value = true }
  const resetTaskFiltersDraft = () => { taskFiltersDraft.value = getDefaultTaskFilters() }
  const applyTaskFiltersFromModal = () => {
    filters.value = { ...taskFiltersDraft.value }
    showTaskFiltersModal.value = false
    applyTaskFilters()
  }
  const clearTaskFilters = () => {
    filters.value = getDefaultTaskFilters()
    taskFiltersDraft.value = getDefaultTaskFilters()
    applyTaskFilters()
  }
  const onTaskPageSizeChange = () => {
    taskPagination.value.page = 1
    localStorage.setItem('tasks-page-size', String(taskPagination.value.pageSize))
    loadTasks()
  }
  const onSearchInput = () => {
    if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
    searchDebounceTimer = setTimeout(() => {
      taskPagination.value.page = 1
      loadTasks()
    }, 300)
  }
  const onTaskSortByColumn = (column) => {
    if (taskSort.value.by === column) {
      taskSort.value.dir = taskSort.value.dir === 'asc' ? 'desc' : 'asc'
    } else {
      taskSort.value.by = column
      taskSort.value.dir = column === 'title' ? 'asc' : 'desc'
    }
    syncMatrixColumns()
  }

  // Bulk
  const isTaskSelected = (taskId) => selectedTaskIds.value.has(String(taskId))
  const toggleTaskSelected = (taskId) => {
    const id = String(taskId)
    const next = new Set(selectedTaskIds.value)
    if (next.has(id)) next.delete(id); else next.add(id)
    selectedTaskIds.value = next
  }
  const allOnPageSelected = computed(() => {
    if (!sortedTasks.value.length) return false
    return sortedTasks.value.every(t => selectedTaskIds.value.has(String(t.id)))
  })
  const someOnPageSelected = computed(() => sortedTasks.value.some(t => selectedTaskIds.value.has(String(t.id))))
  const toggleAllOnPage = () => {
    const next = new Set(selectedTaskIds.value)
    if (allOnPageSelected.value) sortedTasks.value.forEach(t => next.delete(String(t.id)))
    else sortedTasks.value.forEach(t => next.add(String(t.id)))
    selectedTaskIds.value = next
  }
  const clearTaskSelection = () => { selectedTaskIds.value = new Set() }

  const bulkSetStatus = async (status) => {
    const ids = Array.from(selectedTaskIds.value)
    if (!ids.length) return
    const ok = await askConfirm({
      title: `Перевести ${ids.length} задач в «${getStatusText(status)}»?`,
      message: 'Действие применится ко всем выбранным задачам.',
      confirmText: 'Применить',
    })
    if (!ok) return
    bulkBusy.value = true
    let failed = 0
    const original = new Map()
    ids.forEach((id) => {
      const idx = tasks.value.findIndex(t => String(t.id) === id)
      if (idx >= 0) { original.set(id, { ...tasks.value[idx] }); tasks.value[idx] = { ...tasks.value[idx], status } }
    })
    const settle = await Promise.allSettled(ids.map(id => apiTasks.update(id, { status })))
    settle.forEach((res, i) => {
      if (res.status === 'rejected') {
        failed += 1
        const id = ids[i]
        const idx = tasks.value.findIndex(t => String(t.id) === id)
        if (idx >= 0 && original.has(id)) tasks.value[idx] = original.get(id)
      }
    })
    syncMatrixColumns()
    bulkBusy.value = false
    clearTaskSelection()
    if (!failed) toastSuccess(`Готово: ${ids.length}`)
    else if (failed < ids.length) toastWarning(`Готово: ${ids.length - failed}, ошибок: ${failed}`)
    else toastError('Не удалось применить')
  }

  // Generic bulk apply. `payloadFor` is a constant object or fn(task)->object
  // (fn form lets us union assignee/watcher lists per task). Mirrors the
  // optimistic-update + rollback + toast pattern of bulkSetStatus.
  const runBulkApply = async (payloadFor, { confirmTitle, message, confirmText = 'Применить', variant, reload = false } = {}) => {
    const ids = Array.from(selectedTaskIds.value)
    if (!ids.length) return
    if (confirmTitle) {
      const ok = await askConfirm({
        title: confirmTitle,
        message: message || 'Действие применится ко всем выбранным задачам.',
        confirmText,
        variant,
      })
      if (!ok) return
    }
    bulkBusy.value = true
    let failed = 0
    const original = new Map()
    const payloads = new Map()
    ids.forEach((id) => {
      const idx = tasks.value.findIndex(t => String(t.id) === id)
      const task = idx >= 0 ? tasks.value[idx] : { id }
      const payload = typeof payloadFor === 'function' ? payloadFor(task) : payloadFor
      payloads.set(id, payload)
      if (idx >= 0) { original.set(id, { ...tasks.value[idx] }); tasks.value[idx] = { ...tasks.value[idx], ...payload } }
    })
    const settle = await Promise.allSettled(ids.map(id => apiTasks.update(id, payloads.get(id))))
    settle.forEach((res, i) => {
      if (res.status === 'rejected') {
        failed += 1
        const id = ids[i]
        const idx = tasks.value.findIndex(t => String(t.id) === id)
        if (idx >= 0 && original.has(id)) tasks.value[idx] = original.get(id)
      }
    })
    syncMatrixColumns()
    bulkBusy.value = false
    clearTaskSelection()
    if (reload) await loadTasks()
    if (!failed) toastSuccess(`Готово: ${ids.length}`)
    else if (failed < ids.length) toastWarning(`Готово: ${ids.length - failed}, ошибок: ${failed}`)
    else toastError('Не удалось применить')
  }

  const uniqStr = (arr) => Array.from(new Set((arr || []).map(String)))
  const taskAssigneeIds = (task) => {
    if (Array.isArray(task?.assignee_ids) && task.assignee_ids.length) return task.assignee_ids.map(String)
    return task?.assigned_to_user_id ? [String(task.assigned_to_user_id)] : []
  }

  const bulkSetPriority = (priority) => {
    if (!priority) return
    return runBulkApply({ priority }, {
      confirmTitle: `Приоритет «${getPriorityText(priority)}» для ${selectedTaskIds.value.size} задач?`,
    })
  }
  const bulkSetDeadline = (date) => {
    if (!date) return
    return runBulkApply({ due_date: date }, {
      confirmTitle: `Дедлайн ${date} для ${selectedTaskIds.value.size} задач?`,
    })
  }
  const bulkSetProject = (dealId) => {
    if (!dealId) return
    const proj = projects.value.find(p => String(p.id) === String(dealId))
    return runBulkApply({ deal_id: dealId }, {
      confirmTitle: `Проект «${proj?.title || dealId}» для ${selectedTaskIds.value.size} задач?`,
    })
  }
  const bulkAddAssignee = (userId) => {
    if (!userId) return
    const uid = String(userId)
    const name = users.value.find(u => String(u.id) === uid)?.full_name || 'исполнитель'
    return runBulkApply(
      (task) => {
        const payload = { assignee_ids: uniqStr([...taskAssigneeIds(task), uid]) }
        if (!task?.assigned_to_user_id) payload.assigned_to_user_id = uid
        return payload
      },
      { confirmTitle: `Добавить «${name}» в исполнители (${selectedTaskIds.value.size})?`, reload: true }
    )
  }
  const bulkAddWatcher = (userId) => {
    if (!userId) return
    const uid = String(userId)
    const name = users.value.find(u => String(u.id) === uid)?.full_name || 'наблюдатель'
    return runBulkApply(
      (task) => ({ watcher_ids: uniqStr([...(Array.isArray(task?.watcher_ids) ? task.watcher_ids : []), uid]) }),
      { confirmTitle: `Добавить «${name}» в наблюдатели (${selectedTaskIds.value.size})?`, reload: true }
    )
  }

  const bulkDelete = async () => {
    const ids = Array.from(selectedTaskIds.value)
    if (!ids.length) return
    const ok = await askConfirm({
      title: `Удалить ${ids.length} задач?`,
      message: 'Действие необратимо.',
      confirmText: 'Удалить',
      variant: 'danger',
    })
    if (!ok) return
    bulkBusy.value = true
    let failed = 0
    const settle = await Promise.allSettled(ids.map(id => apiTasks.remove(id)))
    settle.forEach(res => { if (res.status === 'rejected') failed += 1 })
    bulkBusy.value = false
    clearTaskSelection()
    await loadTasks()
    if (!failed) toastSuccess(`Удалено: ${ids.length}`)
    else if (failed < ids.length) toastWarning(`Удалено: ${ids.length - failed}, ошибок: ${failed}`)
    else toastError('Не удалось удалить')
  }

  const onTaskSortChange = () => { syncMatrixColumns() }
  const toggleTaskSortDir = () => {
    taskSort.value.dir = taskSort.value.dir === 'asc' ? 'desc' : 'asc'
    syncMatrixColumns()
  }
  const goToPrevTaskPage = () => {
    if (taskPagination.value.page <= 1) return
    taskPagination.value.page -= 1
    loadTasks()
  }
  const goToNextTaskPage = () => {
    if (!taskPagination.value.hasNext) return
    taskPagination.value.page += 1
    loadTasks()
  }
  const reloadTaskData = async () => {
    await Promise.all([loadProjects(), loadUsers(), loadCompanies()])
    await loadTasks()
  }
  const setTaskLayout = (layout) => {
    taskLayout.value = layout
    localStorage.setItem('tasks-layout', layout)
    if (layout === 'matrix') syncMatrixColumns()
  }

  const formatTaskCount = (count) => {
    const value = Number(count || 0)
    const mod10 = value % 10
    const mod100 = value % 100
    if (mod10 === 1 && mod100 !== 11) return `${value} задача`
    if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return `${value} задачи`
    return `${value} задач`
  }

  const getKanbanCardTags = (task) => {
    const tags = []
    if (task.work_category) tags.push({ label: task.work_category, type: 'category' })
    if (task.priority) tags.push({ label: getPriorityText(task.priority), type: task.priority })
    if (task.source_auction_id) tags.push({ label: 'Аукцион', type: 'auction' })
    return tags.slice(0, 3)
  }

  const getKanbanTagClass = (type) => ({
    low: 'task-kanban-chip--low', normal: 'task-kanban-chip--normal',
    high: 'task-kanban-chip--high', urgent: 'task-kanban-chip--urgent',
    category: 'task-kanban-chip--category', auction: 'task-kanban-chip--auction'
  })[type] || 'task-kanban-chip--category'

  const getTaskPreviewText = (task) => {
    if (task.description && task.description.trim()) return task.description.trim()
    if (task.deal_title) return `Проект: ${task.deal_title}`
    if (task.work_category) return `Категория: ${task.work_category}`
    return 'Откройте карточку, чтобы добавить описание и детали задачи.'
  }

  const getAvatarThemeBySeed = (seed) => {
    const key = String(seed || '?')
    const index = key.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0) % AVATAR_THEMES.length
    return AVATAR_THEMES[index]
  }

  const getUserById = (userId) => {
    if (!userId) return null
    return users.value.find((item) => String(item.id) === String(userId)) || null
  }
  const getTaskAssigneeUser = (task) => getUserById(task?.assigned_to_user_id)
  const getTaskAssigneeDisplayName = (task) => {
    const user = getTaskAssigneeUser(task)
    return user?.full_name || task?.assigned_to_user_name || task?.assigned_to_name || 'Не назначен'
  }
  const getTaskAssigneeMeta = (task) => {
    const user = getTaskAssigneeUser(task)
    if (user?.email) return user.email
    if (task?.assigned_to_name) return 'Назначенный участник'
    return 'Исполнитель не назначен'
  }
  const getTaskAvatarUrl = (task) => normalizeAvatarUrl(
    getTaskAssigneeUser(task)?.avatar_url || task?.assigned_to_user_avatar_url || '',
    task?.assigned_to_user_id || getTaskAssigneeUser(task)?.id || ''
  )
  const isAvatarBroken = (url) => {
    const normalized = String(url || '').trim()
    return normalized ? brokenAvatarUrls.value.has(normalized) : false
  }
  const markAvatarBroken = (url) => {
    const normalized = String(url || '').trim()
    if (!normalized || brokenAvatarUrls.value.has(normalized)) return
    brokenAvatarUrls.value = new Set([...brokenAvatarUrls.value, normalized])
  }
  const getTaskAvatarStyle = (task) => {
    if (getTaskAvatarUrl(task)) return null
    const cacheKey = String(task?.assigned_to_user_id || getTaskAssigneeDisplayName(task) || '?')
    if (avatarStyleCache.has(cacheKey)) return avatarStyleCache.get(cacheKey)
    const theme = getAvatarThemeBySeed(`${cacheKey}`)
    avatarStyleCache.set(cacheKey, theme)
    return theme
  }
  const getTaskAssigneeInitial = (task) => {
    const source = getTaskAssigneeDisplayName(task)
    const parts = String(source).trim().split(/\s+/).filter(Boolean)
    if (!parts.length) return '?'
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }
  const getTaskProjectLabel = (task) => {
    const explicitTitle = String(task?.deal_title || '').trim()
    if (explicitTitle) return explicitTitle
    if (!task?.deal_id) return 'Без проекта'
    const project = projects.value.find((item) => String(item.id) === String(task.deal_id))
    return project?.title || 'Без проекта'
  }
  const getCompanyLabel = (companyId) => {
    if (!companyId) return 'Не указан'
    const company = companies.value.find((item) => String(item.id) === String(companyId))
    return company?.name || company?.title || company?.full_name || String(companyId)
  }
  const getTaskListLineClass = (task) => ({
    'task-list-line--completed': task?.status === 'completed',
    'task-list-line--cancelled': task?.status === 'cancelled',
    'task-list-line--deferred': task?.status === 'deferred'
  })

  const currentTaskAssignee = computed(() => getTaskAssigneeUser(taskForm.value))
  const currentTaskAssigneeDisplayName = computed(() => getTaskAssigneeDisplayName(taskForm.value))
  const currentTaskAssigneeMeta = computed(() => getTaskAssigneeMeta(taskForm.value))
  const currentTaskAvatarUrl = computed(() => getTaskAvatarUrl(taskForm.value))
  const currentTaskAvatarStyle = computed(() => getTaskAvatarStyle(taskForm.value))
  const currentTaskProjectLabel = computed(() => getTaskProjectLabel(taskForm.value))
  const currentTaskCode = computed(() => {
    if (!taskForm.value?.id) return 'TASK-НОВАЯ'
    const raw = String(taskForm.value.id).replace(/[^a-zA-Z0-9]/g, '').toUpperCase()
    return `TASK-${raw.slice(0, 4) || 'NEW'}`
  })

  const validateTaskForm = () => {
    const v = { title: '', date: '' }
    if (!String(taskForm.value.title || '').trim()) v.title = 'Введите название задачи'
    if (taskForm.value.start_date && taskForm.value.due_date) {
      const s = new Date(taskForm.value.start_date)
      const d = new Date(taskForm.value.due_date)
      if (s > d) v.date = 'Дата окончания не может быть раньше даты начала'
    }
    taskValidation.value = v
    return !v.title && !v.date
  }
  const taskFormHasErrors = computed(() => !!(taskValidation.value.title || taskValidation.value.date))
  const currentTaskAttachmentsCount = computed(() => Array.isArray(taskForm.value.attachments) ? taskForm.value.attachments.length : 0)
  const currentTaskPayerLabel = computed(() => getCompanyLabel(taskForm.value.payer_id))
  const currentTaskPayeeLabel = computed(() => getCompanyLabel(taskForm.value.payee_id))
  const taskAttachmentItems = computed(() => Array.isArray(taskForm.value.attachments) ? taskForm.value.attachments : [])
  const taskAttachmentsTotalCount = computed(() => currentTaskAttachmentsCount.value + taskPendingFiles.value.length)

  const formatTaskAttachmentSize = (size) => {
    const value = Number(size)
    if (!Number.isFinite(value) || value <= 0) return ''
    if (value < 1024) return `${value} Б`
    if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} КБ`
    if (value < 1024 * 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(1)} МБ`
    return `${(value / (1024 * 1024 * 1024)).toFixed(1)} ГБ`
  }

  const normalizeTaskAttachment = (attachment) => {
    if (!attachment) return null
    if (typeof attachment === 'string') {
      const path = attachment
      const parts = path.split('/')
      return {
        name: parts[parts.length - 1] || 'Файл',
        path,
        download_url: `/api/v1/storage/download?path=${encodeURIComponent(path)}`
      }
    }
    const path = String(attachment.path || '').trim()
    return {
      ...attachment,
      name: attachment.name || (path ? path.split('/').pop() : 'Файл'),
      path: path || undefined,
      download_url: attachment.download_url || (path ? `/api/v1/storage/download?path=${encodeURIComponent(path)}` : '')
    }
  }
  const serializeTaskAttachments = (attachments = []) => (
    Array.isArray(attachments)
      ? attachments.map(normalizeTaskAttachment).filter(Boolean)
        .map(({ name, path, size, content_type }) => ({ name, path, size, content_type }))
      : []
  )

  const resetTaskPendingFiles = () => {
    taskPendingFiles.value = []
    taskAttachmentDragActive.value = false
    if (taskAttachmentInput.value) taskAttachmentInput.value.value = ''
  }
  const appendTaskPendingFiles = (files) => {
    const incoming = Array.from(files || []).filter(file => file instanceof File)
    if (!incoming.length) return
    const existingKeys = new Set(taskPendingFiles.value.map(file => `${file.name}:${file.size}:${file.lastModified}`))
    const appended = []
    for (const file of incoming) {
      const key = `${file.name}:${file.size}:${file.lastModified}`
      if (existingKeys.has(key)) continue
      existingKeys.add(key)
      appended.push(file)
    }
    if (appended.length) taskPendingFiles.value = [...taskPendingFiles.value, ...appended]
  }
  const openTaskAttachmentPicker = () => { taskAttachmentInput.value?.click() }
  const onTaskAttachmentPicked = (event) => {
    appendTaskPendingFiles(event?.target?.files)
    if (event?.target) event.target.value = ''
  }
  const onTaskAttachmentDragOver = () => { taskAttachmentDragActive.value = true }
  const onTaskAttachmentDragLeave = () => { taskAttachmentDragActive.value = false }
  const onTaskAttachmentDrop = (event) => {
    taskAttachmentDragActive.value = false
    appendTaskPendingFiles(event?.dataTransfer?.files)
  }
  const removePendingTaskFile = (index) => {
    taskPendingFiles.value = taskPendingFiles.value.filter((_, fileIndex) => fileIndex !== index)
  }

  const uploadPendingTaskFiles = async (taskId) => {
    if (!taskId || !taskPendingFiles.value.length) return taskAttachmentItems.value
    const formData = new FormData()
    taskPendingFiles.value.forEach((file) => { formData.append('files', file) })
    const response = await apiTasks.uploadAttachments(taskId, formData)
    const attachments = Array.isArray(response?.attachments)
      ? response.attachments.map(normalizeTaskAttachment).filter(Boolean)
      : []
    taskPendingFiles.value = []
    if (taskAttachmentInput.value) taskAttachmentInput.value.value = ''
    return attachments
  }

  const removeTaskAttachment = async (attachment) => {
    const normalized = normalizeTaskAttachment(attachment)
    if (!normalized?.path || !taskForm.value?.id) return
    try {
      const response = await apiTasks.removeAttachment(taskForm.value.id, normalized.path)
      taskForm.value = {
        ...taskForm.value,
        attachments: Array.isArray(response?.attachments)
          ? response.attachments.map(normalizeTaskAttachment).filter(Boolean)
          : []
      }
    } catch (error) {
      console.error(error)
      toastError(error?.response?.data?.detail || 'Не удалось удалить файл')
    }
  }

  const downloadTaskAttachment = async (attachment) => {
    const normalized = normalizeTaskAttachment(attachment)
    if (!normalized?.download_url) return
    try {
      await downloadFromApi(normalized.download_url, {}, normalized.name || 'file', {
        module: 'tasks', entityId: taskForm.value?.id
      })
    } catch (error) {
      console.error(error)
      toastError(error?.response?.data?.detail || 'Не удалось скачать файл')
    }
  }

  const onTaskDragStart = (task, event) => {
    draggedTaskId.value = task.id
    if (event?.dataTransfer) {
      event.dataTransfer.effectAllowed = 'move'
      event.dataTransfer.setData('text/plain', String(task.id))
    }
  }
  const onTaskDragEnd = () => {
    draggedTaskId.value = null
    kanbanDropKey.value = ''
    matrixDropKey.value = ''
  }
  const onKanbanSortStart = (columnKey) => { kanbanDropKey.value = columnKey }
  const onKanbanDragOver = (columnKey) => { kanbanDropKey.value = columnKey }
  const onKanbanDragLeave = (columnKey) => {
    if (kanbanDropKey.value === columnKey) kanbanDropKey.value = ''
  }

  const onKanbanDrop = async (columnKey) => {
    const task = tasks.value.find((item) => String(item.id) === String(draggedTaskId.value))
    onKanbanDragLeave(columnKey)
    if (!task || task.status === columnKey) {
      onTaskDragEnd()
      return
    }
    const previousStatus = task.status
    updatingTaskId.value = task.id
    tasks.value = tasks.value.map((item) => (
      String(item.id) === String(task.id) ? { ...item, status: columnKey } : item
    ))
    try {
      const updatedTask = await apiTasks.update(task.id, { status: columnKey }) || {}
      tasks.value = tasks.value.map((item) => (
        String(item.id) === String(task.id)
          ? { ...item, ...updatedTask, status: columnKey }
          : item
      ))
      if (taskForm.value?.id && String(taskForm.value.id) === String(task.id)) {
        taskForm.value = { ...taskForm.value, ...updatedTask, status: columnKey }
      }
      toastSuccess(`Статус задачи «${task.title}» обновлён`)
    } catch (e) {
      console.error(e)
      tasks.value = tasks.value.map((item) => (
        String(item.id) === String(task.id) ? { ...item, status: previousStatus } : item
      ))
      syncMatrixColumns()
      toastError(e.response?.data?.detail || 'Не удалось обновить статус задачи')
    } finally {
      updatingTaskId.value = null
      onTaskDragEnd()
    }
  }

  const onTaskKanbanChange = async (event, columnKey) => {
    const task = event?.added?.element || null
    if (!task) { kanbanDropKey.value = columnKey; return }
    draggedTaskId.value = task.id
    await onKanbanDrop(columnKey)
  }

  const patchTaskMatrixPosition = (taskId, quadrant, sortOrder) => {
    tasks.value = tasks.value.map((item) => (
      String(item.id) === String(taskId)
        ? { ...item, matrix_quadrant: quadrant, matrix_sort_order: sortOrder, matrix_manual: true }
        : item
    ))
    if (taskForm.value?.id && String(taskForm.value.id) === String(taskId)) {
      taskForm.value = {
        ...taskForm.value,
        matrix_quadrant: quadrant, matrix_sort_order: sortOrder, matrix_manual: true
      }
    }
  }

  const persistMatrixColumnOrder = async (columnKey) => {
    const columnTasks = matrixColumnTasks.value[columnKey] || []
    columnTasks.forEach((task, index) => { patchTaskMatrixPosition(task.id, columnKey, index) })
    await apiTasks.reorderMatrix({
      quadrant: columnKey,
      task_ids: columnTasks.map((task) => task.id)
    })
  }

  const onMatrixDragStart = (columnKey) => { matrixDropKey.value = columnKey }

  const onTaskMatrixChange = async (event, columnKey) => {
    const changedTask = event?.added?.element || event?.moved?.element || event?.removed?.element || null
    if (!changedTask) { matrixDropKey.value = columnKey; return }
    updatingTaskId.value = changedTask.id
    matrixDropKey.value = columnKey
    try {
      await persistMatrixColumnOrder(columnKey)
    } catch (e) {
      console.error(e)
      toastError(e?.response?.data?.detail || 'Не удалось сохранить матрицу')
      await loadTasks()
    } finally {
      updatingTaskId.value = null
      matrixDropKey.value = ''
    }
  }

  const saveTask = async () => {
    if (
      taskForm.value.status === 'completed' &&
      (taskApprovalState.value?.activeInstance || taskApprovalState.value?.latestStatus === 'rejected')
    ) {
      return toastError('Задачу нельзя завершить, пока согласование не завершено успешно.')
    }
    if (!validateTaskForm()) {
      return toastError(taskValidation.value.title || taskValidation.value.date)
    }

    saving.value = true
    try {
      const payload = {
        ...taskForm.value,
        attachments: serializeTaskAttachments(taskForm.value.attachments)
      }
      const savedTask = isEditing.value
        ? await apiTasks.update(taskForm.value.id, payload)
        : await apiTasks.create(payload)

      const savedTaskId = savedTask?.id || taskForm.value.id
      if (savedTaskId) {
        taskForm.value = {
          ...taskForm.value,
          ...savedTask,
          id: savedTaskId,
          attachments: Array.isArray(savedTask?.attachments)
            ? savedTask.attachments.map(normalizeTaskAttachment).filter(Boolean)
            : taskForm.value.attachments
        }
        isEditing.value = true
      }

      if (savedTaskId && taskPendingFiles.value.length) {
        try {
          const uploadedAttachments = await uploadPendingTaskFiles(savedTaskId)
          taskForm.value = { ...taskForm.value, attachments: uploadedAttachments }
        } catch (uploadError) {
          await loadTasks()
          toastError(uploadError?.response?.data?.detail || 'Задача сохранена, но файлы не удалось загрузить')
          console.error(uploadError)
          return
        }
      }

      await loadTasks()
      closeModal(true)
    } catch (e) {
      toastError(e?.response?.data?.detail || 'Ошибка сохранения задачи')
      console.error(e)
    } finally {
      saving.value = false
    }
  }

  const deleteTask = (task) => {
    showConfirm('Удалить задачу?', 'Задача будет удалена безвозвратно.', async () => {
      try {
        await apiTasks.remove(task.id)
        await loadTasks()
      } catch (e) { console.error(e); toastError('Ошибка удаления задачи') }
    })
  }

  const editTask = (task) => {
    taskApprovalState.value = { activeInstance: null, latestInstance: null, latestStatus: null, templateCount: 0 }
    taskForm.value = {
      ...task,
      assignee_ids: Array.isArray(task?.assignee_ids) ? task.assignee_ids.map(String) : (task?.assigned_to_user_id ? [String(task.assigned_to_user_id)] : []),
      watcher_ids: Array.isArray(task?.watcher_ids) ? task.watcher_ids.map(String) : [],
      attachments: Array.isArray(task?.attachments) ? task.attachments.map(normalizeTaskAttachment).filter(Boolean) : []
    }
    resetTaskPendingFiles()
    isEditing.value = true
    showCreateModal.value = true
    setTaskFormSnapshot()
    taskValidation.value = { title: '', date: '' }
    autoDraftFired = true
    if (autoDraftTimer) { clearTimeout(autoDraftTimer); autoDraftTimer = null }
  }

  const openCreateTaskModal = (presetStatus = null) => {
    taskForm.value = getDefaultTaskForm()
    // Постановщик по умолчанию — текущий пользователь (можно сменить в форме).
    const me = activeUser.value || getActiveUser()
    if (me?.id) taskForm.value.created_by_user_id = me.id
    if (presetStatus) taskForm.value.status = presetStatus
    taskApprovalState.value = { activeInstance: null, latestInstance: null, latestStatus: null, templateCount: 0 }
    resetTaskPendingFiles()
    isEditing.value = false
    showCreateModal.value = true
    setTaskFormSnapshot()
    taskValidation.value = { title: '', date: '' }
    autoDraftFired = false
  }

  const openTaskFromQuery = async () => {
    if (initialTaskOpened.value) return
    const taskId = route.query.task_id
    if (!taskId) return
    const match = tasks.value.find(task => String(task.id) === String(taskId))
    if (match) {
      editTask(match)
      initialTaskOpened.value = true
      return
    }
    try {
      const data = await apiTasks.getById(taskId)
      if (data?.id) {
        editTask(data)
        initialTaskOpened.value = true
      }
    } catch (e) { console.error(e) }
  }

  function closeModal(force = false) {
    if (!force && hasTaskFormChanges.value && !saving.value) {
      showConfirm('Закрыть без сохранения?', 'Изменения в задаче будут потеряны.', () => closeModal(true), { confirmText: 'Закрыть', variant: 'warning' })
      return
    }
    if (autoDraftTimer) { clearTimeout(autoDraftTimer); autoDraftTimer = null }
    autoDraftFired = false
    showCreateModal.value = false
    isEditing.value = false
    taskForm.value = getDefaultTaskForm()
    taskApprovalState.value = { activeInstance: null, latestInstance: null, latestStatus: null, templateCount: 0 }
    resetTaskPendingFiles()
    setTaskFormSnapshot()
    taskValidation.value = { title: '', date: '' }
  }

  const handleTaskApprovalState = (state) => {
    taskApprovalState.value = state || { activeInstance: null, latestInstance: null, latestStatus: null, templateCount: 0 }
  }

  const refreshTasksAfterApproval = async () => {
    await loadTasks()
    if (!taskForm.value?.id) return
    try {
      const data = await apiTasks.getById(taskForm.value.id)
      if (!data?.id) return
      taskForm.value = {
        ...taskForm.value,
        ...data,
        attachments: Array.isArray(data.attachments)
          ? data.attachments.map(normalizeTaskAttachment).filter(Boolean)
          : taskForm.value.attachments
      }
      setTaskFormSnapshot()
    } catch (e) { console.error(e) }
  }

  // ===== AUCTIONS =====
  const loadAuctions = async () => {
    auctionsLoading.value = true
    try {
      const params = { ...auctionFilters.value }
      Object.keys(params).forEach(key => params[key] === '' && delete params[key])
      const data = await apiTasks.listAuctions(params)
      auctions.value = data?.items || []
    } catch (e) { console.error(e) }
    finally { auctionsLoading.value = false }
  }

  const toggleAuctionExpanded = (auctionId) => {
    if (expandedAuctionIds.value.includes(auctionId)) {
      expandedAuctionIds.value = expandedAuctionIds.value.filter(id => id !== auctionId)
    } else {
      expandedAuctionIds.value = [...expandedAuctionIds.value, auctionId]
    }
  }
  const isAuctionExpanded = (auctionId) => expandedAuctionIds.value.includes(auctionId)
  const toggleSubtask = (subtaskId) => {
    activeSubtaskId.value = activeSubtaskId.value === subtaskId ? null : subtaskId
  }

  const setAuctionMode = (mode) => {
    auctionForm.value.mode = mode
    if (mode === 'block' && (!auctionForm.value.items || auctionForm.value.items.length === 0)) {
      auctionForm.value.items = [{ title: '', description: '', budget: 0, allow_custom_price: false }]
    }
  }
  const addAuctionItem = () => {
    auctionForm.value.items = [
      ...(auctionForm.value.items || []),
      { title: '', description: '', budget: 0, allow_custom_price: false }
    ]
  }
  const removeAuctionItem = (index) => {
    auctionForm.value.items = (auctionForm.value.items || []).filter((_, i) => i !== index)
    if (!auctionForm.value.items.length) {
      auctionForm.value.items = [{ title: '', description: '', budget: 0, allow_custom_price: false }]
    }
  }

  const switchToAuctions = () => { viewMode.value = 'auctions'; loadAuctions() }

  const viewModes = ['tasks', 'auctions', 'rules']
  const onViewKeydown = (e) => {
    const idx = viewModes.indexOf(viewMode.value)
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      e.preventDefault()
      const next = viewModes[(idx + 1) % viewModes.length]
      viewMode.value = next
      if (next === 'auctions') loadAuctions()
      if (next === 'rules') loadPenaltyRules()
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      e.preventDefault()
      const prev = viewModes[(idx - 1 + viewModes.length) % viewModes.length]
      viewMode.value = prev
      if (prev === 'auctions') loadAuctions()
      if (prev === 'rules') loadPenaltyRules()
    }
  }

  const openAuctionModal = (auction = null) => {
    if (auction) {
      editingAuction.value = auction
      auctionForm.value = {
        title: auction.title,
        description: auction.description || '',
        budget: auction.budget || 0,
        deal_id: auction.deal_id || '',
        category_code: auction.category_code || '',
        allow_custom_price: !!auction.allow_custom_price,
        mode: auction.is_block ? 'block' : 'single',
        items: (auction.children || []).map((child) => ({
          title: child.title,
          description: child.description || '',
          budget: child.budget || 0,
          allow_custom_price: !!child.allow_custom_price
        }))
      }
      if (auctionForm.value.mode === 'block' && !auctionForm.value.items.length) {
        auctionForm.value.items = [{ title: '', description: '', budget: 0, allow_custom_price: false }]
      }
    } else {
      editingAuction.value = null
      auctionForm.value = getDefaultAuctionForm()
    }
    showAuctionModal.value = true
    setAuctionFormSnapshot()
  }

  function closeAuctionModal(force = false) {
    if (!force && hasAuctionFormChanges.value && !savingAuction.value) {
      showConfirm('Закрыть без сохранения?', 'Изменения в аукционе будут потеряны.', () => closeAuctionModal(true))
      return
    }
    showAuctionModal.value = false
    editingAuction.value = null
    auctionForm.value = getDefaultAuctionForm()
    setAuctionFormSnapshot()
  }

  const saveAuction = async () => {
    if (!auctionForm.value.title || !auctionForm.value.title.trim()) {
      return toastError('Название обязательно')
    }
    if (auctionForm.value.mode === 'single' && !auctionForm.value.budget) {
      return toastError('Название и бюджет обязательны')
    }
    if (auctionForm.value.mode === 'block') {
      const items = (auctionForm.value.items || []).filter(item => item.title && Number.isFinite(Number(item.budget)))
      if (!items.length) return toastError('Добавьте хотя бы одну подзадачу')
    }

    savingAuction.value = true
    try {
      if (editingAuction.value) {
        if (editingAuction.value.is_block) {
          return toastError('Редактирование блока пока недоступно')
        }
        const payload = {
          title: auctionForm.value.title,
          description: auctionForm.value.description,
          budget: auctionForm.value.budget,
          deal_id: auctionForm.value.deal_id,
          category_code: auctionForm.value.category_code,
          allow_custom_price: auctionForm.value.allow_custom_price
        }
        await apiTasks.updateAuction(editingAuction.value.id, payload)
      } else if (auctionForm.value.mode === 'block') {
        const payload = {
          title: auctionForm.value.title,
          description: auctionForm.value.description,
          deal_id: auctionForm.value.deal_id,
          category_code: auctionForm.value.category_code,
          is_block: true,
          items: (auctionForm.value.items || []).filter(item => item.title && Number.isFinite(Number(item.budget))).map(item => ({
            title: item.title,
            description: item.description || null,
            budget: Number(item.budget || 0),
            allow_custom_price: !!item.allow_custom_price
          }))
        }
        await apiTasks.createAuction(payload)
      } else {
        const payload = {
          title: auctionForm.value.title,
          description: auctionForm.value.description,
          budget: auctionForm.value.budget,
          deal_id: auctionForm.value.deal_id,
          category_code: auctionForm.value.category_code,
          allow_custom_price: auctionForm.value.allow_custom_price
        }
        await apiTasks.createAuction(payload)
      }
      await loadAuctions()
      closeAuctionModal(true)
    } catch (e) { toastError('Ошибка сохранения аукциона'); console.error(e) }
    finally { savingAuction.value = false }
  }

  const cancelAuction = (auction) => {
    showConfirm('Отменить аукцион?', 'Аукцион будет отменён.', async () => {
      try {
        await apiTasks.cancelAuction(auction.id)
        await loadAuctions()
      } catch (e) { toastError('Ошибка отмены аукциона'); console.error(e) }
    })
  }

  const deleteAuction = (auction) => {
    showConfirm('Удалить аукцион?', 'Аукцион будет удалён безвозвратно.', async () => {
      try {
        await apiTasks.deleteAuctionHard(auction.id)
        await loadAuctions()
      } catch (e) { toastError('Ошибка удаления аукциона'); console.error(e) }
    })
  }

  const viewAuctionBids = async (auction) => {
    selectedAuction.value = auction
    try {
      const data = await apiTasks.listAuctionBids(auction.id)
      auctionBids.value = data?.items || []
    } catch (e) { auctionBids.value = []; console.error(e) }
    showBidsModal.value = true
  }

  const closeBidsModal = () => {
    showBidsModal.value = false
    selectedAuction.value = null
    auctionBids.value = []
  }

  const openAwardModal = (bid) => {
    awardingBid.value = bid
    awardForm.value = {
      category_code: selectedAuction.value?.category_code || '',
      payer_id: '', payee_id: '', due_date: ''
    }
    showAwardModal.value = true
  }
  const closeAwardModal = () => {
    showAwardModal.value = false
    awardingBid.value = null
  }

  const confirmAward = async () => {
    if (!awardingBid.value || !selectedAuction.value) return
    const budgetValue = Number(selectedAuction.value?.budget || 0)
    if (budgetValue > 0) {
      if (!awardForm.value.category_code || !awardForm.value.payer_id || !awardForm.value.payee_id || !awardForm.value.due_date) {
        return toastError('Заполните категорию затрат, плательщика, получателя и дату окончания')
      }
    }
    const winnerName = awardingBid.value.user?.full_name || 'участника'
    showConfirm('Подтвердить победителя?', `Выбрать ${winnerName} победителем?`, async () => {
      awardingWinner.value = true
      try {
        await apiTasks.selectAuctionWinner(selectedAuction.value.id, {
          bid_id: awardingBid.value.id,
          category_code: awardForm.value.category_code,
          payer_id: awardForm.value.payer_id,
          payee_id: awardForm.value.payee_id,
          due_date: awardForm.value.due_date
        })
        toastSuccess('Победитель выбран, задача создана!')
        closeAwardModal()
        closeBidsModal()
        await loadAuctions()
        await loadTasks()
      } catch (e) { toastError('Ошибка выбора победителя'); console.error(e) }
      finally { awardingWinner.value = false }
    })
  }

  // ===== BIDS =====
  const submitBid = (auction) => {
    selectedAuction.value = auction
    bidForm.value = { bid_price: auction.budget, comment: '', block_mode: 'block_only' }
    showBidModal.value = true
  }
  const closeBidModal = () => {
    showBidModal.value = false
    selectedAuction.value = null
  }
  const submitBidForm = async () => {
    submittingBid.value = true
    try {
      const active = getActiveUser()
      const userId = active?.id
      if (!userId) { toastError('Выберите активного пользователя'); return }
      const payload = { bid_price: bidForm.value.bid_price, comment: bidForm.value.comment }
      if (selectedAuction.value?.is_block) {
        payload.covers_children = bidForm.value.block_mode === 'block_and_children'
      }
      await apiTasks.submitAuctionBid(selectedAuction.value.id, userId, payload)
      toastSuccess('Заявка подана!')
      closeBidModal()
      await loadAuctions()
    } catch (e) { toastError(e.response?.data?.detail || 'Ошибка подачи заявки'); console.error(e) }
    finally { submittingBid.value = false }
  }

  // ===== RATING =====
  const openRatingModal = (task) => {
    ratingTask.value = task
    selectedRating.value = 0
    showRatingModal.value = true
  }
  const closeRatingModal = () => {
    showRatingModal.value = false
    ratingTask.value = null
    selectedRating.value = 0
  }
  const syncActiveUserRating = () => {
    const active = getActiveUser()
    if (!active) return
    const updated = users.value.find((item) => item.id === active.id)
    if (!updated) return
    const ratingChanged = (updated.rating ?? 0) !== (active.rating ?? 0)
    const countChanged = (updated.rating_count ?? 0) !== (active.rating_count ?? 0)
    if (!ratingChanged && !countChanged) return
    saveActiveUser(
      { ...active, rating: updated.rating ?? 0, rating_count: updated.rating_count ?? 0 },
      getStoredPermissions()
    )
  }
  const submitRating = async () => {
    if (!selectedRating.value) return
    submittingRating.value = true
    try {
      await apiTasks.rateAuctionTask(ratingTask.value.id, { rating: selectedRating.value })
      await Promise.all([loadTasks(), loadUsers()])
      syncActiveUserRating()
      toastSuccess('Оценка сохранена!')
      closeRatingModal()
    } catch (e) { toastError(e.response?.data?.detail || 'Ошибка сохранения оценки'); console.error(e) }
    finally { submittingRating.value = false }
  }
  const getRatingText = (r) => ({
    1: 'Плохо', 2: 'Удовлетворительно', 3: 'Нормально', 4: 'Хорошо', 5: 'Отлично'
  })[r] || ''

  const recalculatePenalty = () => {
    if (!taskForm.value.id) return
    showConfirm('Пересчитать?', 'Штраф/бонус будет пересчитан по текущей задаче.', async () => {
      recalculatingPenalty.value = true
      try {
        await apiTasks.recalculatePenalty(taskForm.value.id)
        await loadTasks()
        const updated = tasks.value.find(task => task.id === taskForm.value.id)
        if (updated) taskForm.value = { ...taskForm.value, ...updated }
      } catch (e) {
        toastError(e.response?.data?.detail || 'Ошибка пересчёта')
        console.error(e)
      } finally {
        recalculatingPenalty.value = false
      }
    })
  }

  // ===== PENALTY RULES =====
  async function loadPenaltyRules() {
    rulesLoading.value = true
    try {
      const data = await apiTasks.listPenaltyRules()
      penaltyRules.value = Array.isArray(data) ? data : []
    } catch (e) { console.error('Error loading penalty rules', e) }
    finally { rulesLoading.value = false }
  }

  const editRule = (rule) => {
    editingRule.value = rule
    ruleForm.value = {
      rule_type: rule.rule_type,
      condition_min: rule.condition_min,
      condition_max: rule.condition_max,
      coefficient: rule.coefficient,
      description: rule.description || '',
      is_active: rule.is_active
    }
    showRuleModal.value = true
  }

  const saveRule = async () => {
    if (!editingRule.value) return
    savingRule.value = true
    try {
      const payload = { ...ruleForm.value }
      if (payload.rule_type === 'rating') payload.condition_max = payload.condition_min
      if (payload.rule_type === 'deadline' && payload.condition_min > payload.condition_max) {
        savingRule.value = false
        return toastError('Условие: значение "от" не может быть больше "до"')
      }
      await apiTasks.updatePenaltyRule(editingRule.value.id, payload)
      showRuleModal.value = false
      await loadPenaltyRules()
    } catch (e) { console.error('Error saving rule', e); toastError('Ошибка сохранения правила') }
    finally { savingRule.value = false }
  }

  const seedDefaultRules = async () => {
    seedingRules.value = true
    try {
      await apiTasks.seedDefaultPenaltyRules()
      await loadPenaltyRules()
    } catch (e) { console.error('Error seeding rules', e) }
    finally { seedingRules.value = false }
  }

  // ===== HELPERS =====
  const formatDate = (v) => v ? new Date(v).toLocaleDateString('ru-RU') : '-'
  const formatCurrency = (v) => v !== null && v !== undefined ? new Intl.NumberFormat('ru-RU').format(v) + ' ₽' : '-'
  const formatCoefficient = (v) => v !== null && v !== undefined ? Number(v).toFixed(2) : '-'

  const getPenaltyClass = (task) => {
    const value = Number(task.penalty_amount || 0)
    if (value > 0) return 'text-danger'
    if (value < 0) return 'text-success'
    return 'text-muted'
  }
  const getPenaltyText = (task) => {
    if (task.penalty_amount === null || task.penalty_amount === undefined) return '-'
    const value = Number(task.penalty_amount || 0)
    if (!value) return '0'
    const sign = value > 0 ? '-' : '+'
    return `${sign}${formatCurrency(Math.abs(value))}`
  }

  function getStatusText(s) {
    return ({
      new: 'Новая', in_progress: 'В работе', pending: 'Ожидает',
      completed: 'Завершена', cancelled: 'Отменена', deferred: 'Отложена'
    })[s] || s
  }
  const getStatusClass = (s) => ({
    new: 'badge-secondary', in_progress: 'badge-primary', pending: 'badge-warning',
    completed: 'badge-success', cancelled: 'badge-danger', deferred: 'badge-info'
  })[s] || 'badge-secondary'
  const getTaskMatrixStatusClass = (s) => ({
    new: 'task-matrix-status--new', in_progress: 'task-matrix-status--progress',
    pending: 'task-matrix-status--pending', completed: 'task-matrix-status--completed',
    cancelled: 'task-matrix-status--cancelled', deferred: 'task-matrix-status--deferred'
  })[s] || 'task-matrix-status--new'
  function getPriorityText(s) {
    return ({ low: 'Низкий', normal: 'Нормальный', high: 'Высокий', urgent: 'Срочный' })[s] || s
  }
  const getPriorityClass = (s) => ({
    low: 'badge-light', normal: 'badge-info', high: 'badge-warning', urgent: 'badge-danger'
  })[s] || 'badge-light'
  const getDueDateClass = (d) => {
    if (!d) return ''
    const diff = Math.ceil((new Date(d) - new Date()) / (1000 * 60 * 60 * 24))
    if (diff < 0) return 'text-danger'
    if (diff <= 3) return 'text-warning'
    return 'text-success'
  }
  const getAuctionStatusText = (s) => ({
    new: 'Активен', awarded: 'Завершён', cancelled: 'Отменён'
  })[s] || s
  const getUserRatingText = (userId) => {
    if (!userId) return null
    const user = users.value.find((item) => item.id === userId)
    if (!user) return null
    const rating = user.rating ?? 0
    const count = user.rating_count ?? 0
    if (!rating && !count) return null
    return `${rating.toFixed(2)}★ (${count})`
  }
  const getProjectNameById = (projectId) => {
    if (!projectId) return ''
    return projects.value.find((item) => String(item.id) === String(projectId))?.title || String(projectId)
  }
  const getUserNameById = (userId) => {
    if (!userId) return ''
    return users.value.find((item) => String(item.id) === String(userId))?.full_name || String(userId)
  }

  const activeTaskFiltersSummary = computed(() => {
    const items = []
    const f = filters.value
    if (f.search) items.push({ key: 'search', label: `Поиск: «${f.search}»` })
    if (f.deal_id) items.push({ key: 'deal', label: `Проект: ${getProjectNameById(f.deal_id)}` })
    if (f.status) items.push({ key: 'status', label: `Статус: ${getStatusText(f.status)}` })
    if (f.priority) items.push({ key: 'priority', label: `Приоритет: ${getPriorityText(f.priority)}` })
    if (f.assigned_to_user_id) items.push({ key: 'assignee', label: `Ответственный: ${getUserNameById(f.assigned_to_user_id)}` })
    if (f.due_date_from || f.due_date_to) {
      const from = f.due_date_from ? f.due_date_from : '—'
      const to = f.due_date_to ? f.due_date_to : '—'
      items.push({ key: 'date', label: `Срок: ${from} — ${to}` })
    }
    if (f.overdue) items.push({ key: 'overdue', label: 'Только просроченные' })
    if (f.has_budget === true) items.push({ key: 'has_budget', label: 'С бюджетом' })
    else if (f.has_budget === false) items.push({ key: 'has_budget', label: 'Без бюджета' })
    if (f.source === 'auction') items.push({ key: 'source', label: 'Из аукциона' })
    else if (f.source === 'manual') items.push({ key: 'source', label: 'Создано вручную' })
    if (f.category_code) items.push({ key: 'category', label: `Категория: ${f.category_code}` })
    if (f.work_category) items.push({ key: 'work_category', label: f.work_category })
    return items
  })

  const hasActiveTaskFilters = computed(() => activeTaskFiltersSummary.value.length > 0)

  setTaskFormSnapshot()
  setAuctionFormSnapshot()

  // ──────────────────────────────────────────────────────────────
  // Auto-save: when editing an existing task, push field changes to
  // the backend with a small debounce. Covers status, dates, people,
  // description, files etc. Fails silently into a toast on error.
  // ──────────────────────────────────────────────────────────────
  let autoSaveTimer = null
  let autoSaveInflight = false
  let autoSavePending = false
  // Monotonic counter — bumped on every save attempt AND on every change
  // that arrives during an in-flight save. Only the response whose counter
  // equals the latest may merge into the form. Earlier responses are
  // discarded so they can't roll user-typed changes back.
  let autoSaveCounter = 0
  const autoSaving = ref(false)
  const autoSavedAt = ref(null)

  const performAutoSave = async () => {
    if (autoSaveInflight) {
      // Coalesce — another save in flight; mark that something changed
      // again so we re-run once it finishes. Also bump the counter so the
      // in-flight response won't merge stale data.
      autoSavePending = true
      autoSaveCounter += 1
      return
    }
    if (!showCreateModal.value || !isEditing.value) return
    if (saving.value) return  // manual save in progress
    if (!hasTaskFormChanges.value && !taskPendingFiles.value.length) return
    const title = String(taskForm.value?.title || '').trim()
    if (!title) return
    const taskId = taskForm.value?.id
    if (!taskId) return

    autoSaveInflight = true
    autoSaving.value = true
    const myReq = ++autoSaveCounter
    const isLatest = () => myReq === autoSaveCounter
    try {
      const payload = {
        ...taskForm.value,
        attachments: serializeTaskAttachments(taskForm.value.attachments)
      }
      const saved = await apiTasks.update(taskId, payload)
      if (!isLatest()) {
        // A newer save started while this one was in flight — drop the
        // response entirely. The follow-up save in `finally` will catch up.
        return
      }
      if (saved?.id) {
        taskForm.value = {
          ...taskForm.value,
          ...saved,
          attachments: Array.isArray(saved?.attachments)
            ? saved.attachments.map(normalizeTaskAttachment).filter(Boolean)
            : taskForm.value.attachments
        }
      }
      // Pending files upload (autosave should pick them up too).
      if (taskPendingFiles.value.length) {
        try {
          const uploaded = await uploadPendingTaskFiles(taskId)
          if (!isLatest()) return
          taskForm.value = { ...taskForm.value, attachments: uploaded }
        } catch (e) {
          toastError(e?.response?.data?.detail || 'Не удалось загрузить файлы')
          console.warn('autosave file upload failed', e)
        }
      }
      // Sync the row in the list.
      if (saved?.id) {
        const idx = tasks.value.findIndex(t => String(t.id) === String(saved.id))
        if (idx >= 0) tasks.value.splice(idx, 1, { ...tasks.value[idx], ...saved })
      }
      setTaskFormSnapshot()
      autoSavedAt.value = Date.now()
    } catch (e) {
      // Surface the first error to the user; subsequent silent retries via change watch.
      toastError(e?.response?.data?.detail || 'Не удалось автосохранить задачу')
      console.warn('autosave error', e)
    } finally {
      autoSaveInflight = false
      autoSaving.value = false
      if (autoSavePending) {
        autoSavePending = false
        // Flush immediately so quick consecutive edits feel snappy.
        flushAutoSave()
      }
    }
  }

  const scheduleAutoSave = (delay = 700) => {
    if (!showCreateModal.value || !isEditing.value) return
    if (autoSaveTimer) clearTimeout(autoSaveTimer)
    autoSaveTimer = setTimeout(() => { performAutoSave() }, delay)
  }

  // Skip the debounce — fire autosave right now. Called by people-row
  // toggles where the user expects an immediate persist per click.
  const flushAutoSave = () => {
    if (autoSaveTimer) { clearTimeout(autoSaveTimer); autoSaveTimer = null }
    performAutoSave()
  }

  // Watch deep changes on the task form while it's being edited.
  watch(
    () => [taskForm.value, taskPendingFiles.value.length],
    () => {
      if (!isEditing.value || !showCreateModal.value) return
      scheduleAutoSave()
    },
    { deep: true }
  )

  // Cancel any pending autosave when the modal closes.
  watch(showCreateModal, (open) => {
    if (!open) {
      if (autoSaveTimer) { clearTimeout(autoSaveTimer); autoSaveTimer = null }
      autoSavePending = false
    }
  })

  // Авто-черновик отключён: новую задачу создаём только явным «Сохранить».
  // Автосохранение работает лишь для уже существующих задач (isEditing).
  const triggerAutoDraftIfNeeded = () => {
    if (autoDraftTimer) { clearTimeout(autoDraftTimer); autoDraftTimer = null }
  }

  onMounted(async () => {
    syncTaskChatUser()
    window.addEventListener('permissions-updated', handlePermissionsUpdate)
    await Promise.all([loadProjects(), loadUsers(), loadCompanies()])
    await loadTasks()
    await openTaskFromQuery()
  })

  onBeforeUnmount(() => {
    window.removeEventListener('permissions-updated', handlePermissionsUpdate)
  })

  return {
    // view-mode
    viewMode, switchToAuctions, onViewKeydown,
    // tasks
    tasks, sortedTasks, projects, users, companies, loading, saving, showCreateModal, isEditing,
    filters, taskForm, loadTasks, saveTask, editTask, deleteTask, closeModal, openCreateTaskModal,
    handleTaskApprovalState, refreshTasksAfterApproval,
    autoSaving, autoSavedAt, flushAutoSave,
    loadErrors, reloadTaskData,
    taskPagination, totalPages, taskSort,
    applyTaskFilters, onTaskSortChange, toggleTaskSortDir, onTaskPageSizeChange,
    goToPrevTaskPage, goToNextTaskPage, onSearchInput, onTaskSortByColumn,
    showTaskFiltersModal, taskFiltersDraft,
    openTaskFiltersModal, resetTaskFiltersDraft, applyTaskFiltersFromModal,
    clearTaskFilters, activeTaskFiltersSummary, hasActiveTaskFilters,
    // bulk
    selectedTaskIds, isTaskSelected, toggleTaskSelected,
    allOnPageSelected, someOnPageSelected, toggleAllOnPage, clearTaskSelection,
    bulkBusy, bulkSetStatus, bulkDelete,
    bulkSetPriority, bulkSetDeadline, bulkSetProject, bulkAddAssignee, bulkAddWatcher,
    projects, users,
    // aside / draft
    taskSheetAsideCollapsed, toggleTaskSheetAside, asideTab, taskApprovalState,
    triggerAutoDraftIfNeeded,
    // validation
    taskValidation, taskFormHasErrors,
    // layouts
    taskLayout, setTaskLayout, kanbanColumns, matrixColumns, formatTaskCount,
    getKanbanCardTags, getKanbanTagClass, getTaskPreviewText, getTaskAssigneeInitial,
    getTaskAssigneeDisplayName, getTaskAvatarUrl, getTaskAvatarStyle, isAvatarBroken, markAvatarBroken,
    onTaskDragStart, onTaskDragEnd, onKanbanDragOver, onKanbanDrop, onKanbanDragLeave,
    kanbanDropKey, updatingTaskId,
    onKanbanSortStart, onTaskKanbanChange, onMatrixDragStart, onTaskMatrixChange,
    matrixDropKey, isTouchDevice,
    // task editor
    taskChatVisible, taskModalStyle, currentTaskAssignee, currentTaskAssigneeDisplayName,
    currentTaskAssigneeMeta, currentTaskAvatarUrl, currentTaskAvatarStyle,
    currentTaskProjectLabel, currentTaskCode, currentTaskAttachmentsCount,
    currentTaskPayerLabel, currentTaskPayeeLabel,
    taskAttachmentInput, taskPendingFiles, taskAttachmentDragActive,
    taskAttachmentItems, taskAttachmentsTotalCount,
    formatTaskAttachmentSize, openTaskAttachmentPicker, onTaskAttachmentPicked,
    onTaskAttachmentDragOver, onTaskAttachmentDragLeave, onTaskAttachmentDrop,
    removePendingTaskFile, removeTaskAttachment, downloadTaskAttachment,
    validateTaskForm,
    // auctions
    auctions, auctionsLoading, auctionFilters, loadAuctions,
    showAuctionModal, editingAuction, savingAuction, auctionForm, blockBudget,
    openAuctionModal, closeAuctionModal, saveAuction, cancelAuction, deleteAuction,
    toggleAuctionExpanded, isAuctionExpanded, activeSubtaskId, toggleSubtask,
    setAuctionMode, addAuctionItem, removeAuctionItem,
    // bids
    showBidsModal, selectedAuction, auctionBids, viewAuctionBids, closeBidsModal,
    showAwardModal, awardForm, openAwardModal, closeAwardModal, confirmAward, awardingWinner,
    showBidModal, bidForm, submittingBid, submitBid, closeBidModal, submitBidForm,
    // rating
    showRatingModal, ratingTask, selectedRating, submittingRating,
    openRatingModal, closeRatingModal, submitRating, getRatingText,
    recalculatePenalty, canRecalculatePenalty, recalculatingPenalty,
    // penalty rules
    penaltyRules, rulesLoading, showRuleModal, ruleForm, savingRule, seedingRules,
    ratingRules, deadlineRules, loadPenaltyRules, editRule, saveRule, seedDefaultRules,
    // permissions
    canManageAuctions, canBidAuctions, canManagePenalties,
    // categories
    expenseCategories, workCategories,
    // helpers
    formatDate, formatCurrency, formatCoefficient,
    getPenaltyClass, getPenaltyText,
    getStatusClass, getStatusText, getTaskMatrixStatusClass, getPriorityClass, getPriorityText,
    getDueDateClass, getAuctionStatusText, getUserRatingText, getTaskListLineClass,
  }
}
