<template>
  <div class="legal-work-view">
    <div class="legal-work-toolbar">
      <h2 class="legal-work-toolbar__title">Юридическая работа</h2>
      <UiButton variant="primary" icon-left="fas fa-plus" @click="openCaseModal()">
        Новое дело
      </UiButton>
    </div>

    <div v-if="loading" class="legal-work-loading">
      <SkeletonLoader height="180px" v-for="i in 4" :key="i" />
    </div>

    <UiEmptyState
      v-else-if="cases.length === 0"
      class="legal-empty-state"
      icon="fas fa-scale-balanced"
      title="Дел пока нет"
      description="Создайте первое юридическое дело для отслеживания судебных процессов"
    >
      <template #actions>
        <UiButton variant="primary" icon-left="fas fa-plus" @click="openCaseModal()">
          Создать дело
        </UiButton>
      </template>
    </UiEmptyState>

    <div v-else class="legal-grid">
      <UiCard v-for="caseItem in cases" :key="caseItem.id" class="legal-card" padding="md">
        <div class="legal-card-header">
          <div class="case-badge">
            <i class="fas fa-gavel"></i>
          </div>
          <div class="case-number-block">
            <span class="case-number-label">№ дела</span>
            <span class="case-number-value">{{ formatMultiline(caseItem.case_number, 'Без номера') }}</span>
          </div>
          <div class="case-actions-top">
            <UiIconButton icon="fas fa-edit" label="Редактировать" @click="openCaseModal(caseItem)" />
            <UiIconButton icon="fas fa-trash" label="Удалить" variant="danger" @click="deleteCase(caseItem)" />
          </div>
        </div>

        <div class="case-info-row">
          <div class="case-info-item">
            <i class="fas fa-user-tie text-primary"></i>
            <div>
              <span class="info-label">Судья</span>
              <span class="info-value">{{ formatMultiline(caseItem.judge) }}</span>
            </div>
          </div>
          <div class="case-info-item">
            <i class="fas fa-landmark text-muted"></i>
            <div>
              <span class="info-label">Подсудность</span>
              <span class="info-value">{{ formatMultiline(caseItem.jurisdiction) }}</span>
            </div>
          </div>
        </div>

        <div class="parties-block">
          <div class="party-row">
            <span class="party-role party-role-plaintiff">Истец</span>
            <span class="party-name">{{ caseItem.plaintiff_name || '-' }}</span>
          </div>
          <div class="party-row">
            <span class="party-role party-role-defendant">Ответчик</span>
            <span class="party-name">{{ caseItem.defendant_name || '-' }}</span>
          </div>
        </div>

        <div v-if="caseItem.judge_assistant" class="assistant-block">
          <i class="fas fa-headset text-muted"></i>
          <div>
            <span class="assistant-name">{{ caseItem.judge_assistant }}</span>
            <span v-if="caseItem.judge_assistant_phone" class="assistant-phone">
              <i class="fas fa-phone-alt"></i> {{ formatMultiline(caseItem.judge_assistant_phone, '') }}
            </span>
          </div>
        </div>

        <div class="hearing-block" v-if="getLatestHearingDate(caseItem) !== '-'">
          <i class="fas fa-calendar-check text-success"></i>
          <div>
            <span class="hearing-label">Ближайшее заседание</span>
            <span class="hearing-date">{{ getLatestHearingDate(caseItem) }}</span>
          </div>
        </div>

        <div class="legal-card-footer">
          <UiButton variant="primary" block @click="openCaseDetail(caseItem)">
            Открыть
          </UiButton>
        </div>
      </UiCard>
    </div>

    <UiModal
      v-model="showCaseModal"
      :title="editingCase ? 'Редактировать дело' : 'Новое дело'"
      size="md"
      @close="closeCaseModal"
    >
      <div class="legal-form">
        <UiInput v-model="caseForm.case_number" label="№ дела" />
        <UiInput v-model="caseForm.judge" label="Судья" />
        <UiInput v-model="caseForm.jurisdiction" label="Подсудность" />
        <UiInput v-model="caseForm.judge_assistant" label="Помощник судьи" />
        <UiInput v-model="caseForm.judge_assistant_phone" label="Телефон помощника" />

        <div class="legal-form__field">
          <label class="legal-form__label">Истец</label>
          <CompanySmartSelect
            v-model="caseForm.plaintiff_id"
            :options="companies"
            fetch-url="/api/v1/companies/"
            :fetch-limit="200"
            :max-results="200"
            placeholder="Выберите контрагента"
          />
        </div>

        <div class="legal-form__field">
          <label class="legal-form__label">Ответчик</label>
          <CompanySmartSelect
            v-model="caseForm.defendant_id"
            :options="companies"
            fetch-url="/api/v1/companies/"
            :fetch-limit="200"
            :max-results="200"
            placeholder="Выберите контрагента"
          />
        </div>

        <UiTextarea v-model="caseForm.description" label="Описание" :rows="4" />
      </div>

      <template #footer>
        <UiButton variant="secondary" @click="closeCaseModal">Отмена</UiButton>
        <UiButton variant="primary" :loading="savingCase" @click="saveCase">
          {{ editingCase ? 'Сохранить' : 'Создать' }}
        </UiButton>
      </template>
    </UiModal>

    <UiModal
      v-model="showTaskModal"
      :title="taskMode === 'existing' ? 'Привязать задачу' : 'Новая задача'"
      size="md"
      @close="closeTaskModal"
    >
      <div class="legal-form">
        <UiTabs
          v-model="taskMode"
          variant="segment"
          size="sm"
          :tabs="[
            { value: 'new', label: 'Новая' },
            { value: 'existing', label: 'Существующая' }
          ]"
        />

        <template v-if="taskMode === 'existing'">
          <UiSelect v-model="existingDealId" label="Фильтр по сделке" :options="projectOptionsWithAll" />
          <UiInput v-model="taskSearch" label="Поиск по задачам" placeholder="Начните вводить" />
          <UiSelect
            v-model="existingTaskId"
            label="Задача"
            :options="existingTaskOptions"
            :disabled="tasksLoading"
          />
          <div v-if="!tasksLoading && !filteredExistingTasks.length" class="legal-form__hint">
            Нет подходящих задач
          </div>
        </template>

        <template v-else>
          <UiInput v-model="taskForm.title" label="Название *" required />
          <UiSelect v-model="taskForm.deal_id" label="Сделка *" required :options="projectOptions" />
          <UiTextarea v-model="taskForm.description" label="Описание" :rows="3" />
          <UiInput v-model="taskForm.due_date" type="date" label="Срок" />
          <UiSelect v-model="taskForm.work_category" label="Категория задачи" :options="workCategoryOptions" />
        </template>
      </div>

      <template #footer>
        <UiButton variant="secondary" @click="closeTaskModal">Отмена</UiButton>
        <UiButton variant="primary" :loading="savingTask" @click="saveTask">
          {{ taskMode === 'existing' ? 'Привязать' : 'Создать' }}
        </UiButton>
      </template>
    </UiModal>
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api'
import SkeletonLoader from '../components/ui/SkeletonLoader.vue'
import CompanySmartSelect from '../components/ui/CompanySmartSelect.vue'
import { UiButton, UiCard, UiEmptyState, UiIconButton, UiInput, UiModal, UiSelect, UiTabs, UiTextarea } from '../components/ui'
import { useCompaniesStore } from '../stores/companies'

export default {
  name: 'LegalWork',
  components: {
    SkeletonLoader,
    CompanySmartSelect,
    UiButton,
    UiCard,
    UiEmptyState,
    UiIconButton,
    UiInput,
    UiModal,
    UiSelect,
    UiTabs,
    UiTextarea
  },
  setup() {
    const router = useRouter()
    const companiesStore = useCompaniesStore()
    const loading = ref(false)
    const savingCase = ref(false)
    const savingTask = ref(false)
    const cases = ref([])
    const companies = ref([])
    const projects = ref([])
    const eventDrafts = ref({})
    const showCaseModal = ref(false)
    const showTaskModal = ref(false)
    const editingCase = ref(null)
    const activeCaseId = ref(null)
    const taskMode = ref('new')
    const existingTasks = ref([])
    const existingTaskId = ref('')
    const existingDealId = ref('')
    const taskSearch = ref('')
    const tasksLoading = ref(false)

    const workCategories = ['Юридическая', 'Производственная', 'Административная']
    const hearingType = 'Заседание'
    const eventTypes = [
      'Исковое заявление', 'Ходатайство', 'Письменные объяснения', 'Отзыв',
      'Заседание', 'Резолютивная часть решения', 'Мотивированное решение',
      'Апелляционная жалоба', 'Кассационная жалоба', 'Событие', 'Определение'
    ]

    const caseForm = ref({
      case_number: '', judge: '', jurisdiction: '',
      judge_assistant: '', judge_assistant_phone: '',
      plaintiff_id: '', defendant_id: '', description: ''
    })

    const taskForm = ref({
      title: '', description: '', deal_id: '', due_date: '', work_category: workCategories[0]
    })

    const projectOptions = computed(() => projects.value.map((project) => ({
      value: project.id,
      label: project.title
    })))
    const projectOptionsWithAll = computed(() => [
      { value: '', label: 'Все сделки' },
      ...projectOptions.value
    ])
    const workCategoryOptions = computed(() => [
      { value: '', label: 'Не указана' },
      ...workCategories.map((category) => ({ value: category, label: category }))
    ])
    const existingTaskOptions = computed(() => [
      { value: '', label: 'Выберите задачу' },
      ...filteredExistingTasks.value.map((task) => ({
        value: task.id,
        label: formatTaskOption(task)
      }))
    ])

    const ensureEventDraft = (caseId) => {
      if (!eventDrafts.value[caseId]) {
        eventDrafts.value[caseId] = { event_type: '', event_date: '' }
      }
    }

    const loadCases = async () => {
      loading.value = true
      try {
        const data = await api.legal.list()
        cases.value = data || []
        cases.value.forEach((item) => ensureEventDraft(item.id))
      } catch (e) { console.error(e) }
      finally { loading.value = false }
    }

    const loadCompanies = async () => {
      try {
        await companiesStore.ensureLoaded()
        companies.value = companiesStore.items
      } catch (e) { console.error(e) }
    }

    const loadProjects = async () => {
      try {
        const data = await api.deals.list()
        projects.value = data || []
      } catch (e) { console.error(e) }
    }

    const openCaseModal = (caseItem = null) => {
      editingCase.value = caseItem
      caseForm.value = {
        case_number: caseItem?.case_number || '',
        judge: caseItem?.judge || '',
        jurisdiction: caseItem?.jurisdiction || '',
        judge_assistant: caseItem?.judge_assistant || '',
        judge_assistant_phone: caseItem?.judge_assistant_phone || '',
        plaintiff_id: caseItem?.plaintiff_id || '',
        defendant_id: caseItem?.defendant_id || '',
        description: caseItem?.description || ''
      }
      showCaseModal.value = true
    }

    const closeCaseModal = () => { showCaseModal.value = false; editingCase.value = null }

    const saveCase = async () => {
      savingCase.value = true
      try {
        if (editingCase.value) {
          await api.legal.update(editingCase.value.id, caseForm.value)
        } else {
          await api.legal.create(caseForm.value)
        }
        await loadCases()
        closeCaseModal()
      } catch (e) { console.error(e); alert('Ошибка сохранения') }
      finally { savingCase.value = false }
    }

    const deleteCase = async (caseItem) => {
      if (!confirm('Удалить дело?')) return
      try {
        await api.legal.remove(caseItem.id)
        await loadCases()
      } catch (e) { console.error(e); alert('Ошибка удаления') }
    }

    const openCaseDetail = (caseItem) => { router.push({ path: `/legal-work/${caseItem.id}` }) }

    const openTaskModal = (caseItem) => {
      activeCaseId.value = caseItem.id
      taskMode.value = 'new'
      existingTaskId.value = ''
      existingDealId.value = ''
      taskSearch.value = ''
      existingTasks.value = []
      taskForm.value = { title: '', description: '', deal_id: '', due_date: '', work_category: workCategories[0] }
      showTaskModal.value = true
    }

    const closeTaskModal = () => { showTaskModal.value = false; activeCaseId.value = null }

    const saveTask = async () => {
      if (!activeCaseId.value) return
      if (taskMode.value === 'existing') {
        if (!existingTaskId.value) return alert('Выберите задачу')
        savingTask.value = true
        try {
          await api.legal.linkTask(activeCaseId.value, { task_id: existingTaskId.value })
          await loadCases()
          closeTaskModal()
        } catch (e) { console.error(e); alert(e.response?.data?.detail || 'Ошибка привязки задачи') }
        finally { savingTask.value = false }
        return
      }
      if (!taskForm.value.title.trim() || !taskForm.value.deal_id) return alert('Название и сделка обязательны')
      savingTask.value = true
      try {
        const payload = {
          title: taskForm.value.title,
          description: taskForm.value.description,
          deal_id: taskForm.value.deal_id,
          due_date: taskForm.value.due_date || null,
          work_category: taskForm.value.work_category || null
        }
        const created = await api.tasks.create(payload)
        await api.legal.linkTask(activeCaseId.value, { task_id: created.id })
        await loadCases()
        closeTaskModal()
      } catch (e) { console.error(e); alert(e.response?.data?.detail || 'Ошибка создания задачи') }
      finally { savingTask.value = false }
    }

    const loadExistingTasks = async () => {
      tasksLoading.value = true
      try {
        const params = { limit: 200 }
        if (existingDealId.value) params.deal_id = existingDealId.value
        const res = await api.tasks.list(params)
        existingTasks.value = res.data || []
      } catch (e) { console.error(e); existingTasks.value = [] }
      finally { tasksLoading.value = false }
    }

    const filteredExistingTasks = computed(() => {
      const q = taskSearch.value.trim().toLowerCase()
      const list = existingTasks.value || []
      if (!q) return list.slice(0, 50)
      return list.filter(task => {
        const title = (task.title || '').toLowerCase()
        const dealTitle = (task.deal_title || '').toLowerCase()
        return title.includes(q) || dealTitle.includes(q)
      }).slice(0, 50)
    })

    const formatTaskOption = (task) => {
      const dealTitle = task.deal_title ? ` (${task.deal_title})` : ''
      return `${task.title}${dealTitle}`
    }

    const formatMultiline = (value, fallback = '-') => {
      if (!value) return fallback
      return String(value)
        .replace(/[\u00A6\u2502\uFF5C|]+/g, '\n')
        .split(/\r?\n+/)
        .map((part) => part.trim())
        .filter(Boolean)
        .join('\n')
    }

    watch(taskMode, (mode) => { if (mode === 'existing') loadExistingTasks() })
    watch(existingDealId, () => { if (taskMode.value === 'existing') loadExistingTasks() })

    const formatDate = (value) => (value ? new Date(value).toLocaleDateString('ru-RU') : '-')
    const formatTime = (value) => {
      if (!value) return ''
      if (typeof value === 'string') return value.slice(0, 5)
      return String(value).slice(0, 5)
    }

    const getLatestHearingDate = (caseItem) => {
      const events = caseItem?.events || []
      const hearings = events.filter(event => event.event_type === hearingType && event.event_date)
      if (!hearings.length) return '-'
      const latest = hearings.reduce((acc, current) => {
        if (!acc) return current
        return new Date(current.event_date) > new Date(acc.event_date) ? current : acc
      }, null)
      if (!latest) return '-'
      const datePart = formatDate(latest.event_date)
      const timePart = formatTime(latest.event_time)
      const hallPart = latest.courtroom ? `зал ${latest.courtroom}` : ''
      return [datePart, timePart, hallPart].filter(Boolean).join(' ')
    }

    onMounted(async () => {
      await Promise.all([loadCases(), loadCompanies(), loadProjects()])
    })

    return {
      loading, cases, companies, projects, eventDrafts, eventTypes, workCategories, getLatestHearingDate,
      showCaseModal, showTaskModal, editingCase, caseForm, taskForm, taskMode,
      existingTasks, existingTaskId, existingDealId, taskSearch, tasksLoading, filteredExistingTasks,
      savingCase, savingTask, projectOptions, projectOptionsWithAll, workCategoryOptions, existingTaskOptions,
      openCaseModal, closeCaseModal, saveCase, deleteCase,
      openTaskModal, closeTaskModal, saveTask, openCaseDetail, formatTaskOption, formatMultiline, formatDate
    }
  }
}
</script>

<style scoped>
.legal-work-view {
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.legal-work-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.legal-work-toolbar__title {
  margin: 0;
  font-size: var(--text-2xl);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.legal-work-loading {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.legal-empty-state {
  max-width: 420px;
  margin: 60px auto;
}

.legal-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: var(--space-5);
}

.legal-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.legal-card-header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
}

.case-badge {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-active) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.case-badge i {
  font-size: var(--text-lg);
  color: #fff;
}

.case-number-block {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.case-number-label,
.info-label,
.hearing-label,
.legal-form__label {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-muted);
  font-weight: var(--fw-semibold);
}

.case-number-value {
  font-size: var(--text-lg);
  font-weight: var(--fw-bold);
  color: var(--color-text);
  white-space: pre-line;
  word-break: break-word;
  line-height: 1.35;
}

.case-actions-top {
  display: flex;
  gap: var(--space-1);
}

.case-info-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
}

.case-info-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
}

.case-info-item > i {
  margin-top: 2px;
  font-size: var(--text-md);
}

.case-info-item > div,
.assistant-block > div,
.hearing-block > div {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.info-value,
.assistant-name,
.party-name,
.hearing-date {
  font-size: var(--text-md);
  font-weight: var(--fw-medium);
  color: var(--color-text);
  white-space: pre-line;
  word-break: break-word;
  line-height: 1.35;
}

.parties-block,
.assistant-block {
  background: var(--color-surface-2);
  border-radius: var(--radius-md);
  padding: var(--space-3);
}

.parties-block {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.party-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.party-role {
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-xs);
  min-width: 80px;
  text-align: center;
}

.party-role-plaintiff {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.party-role-defendant {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.assistant-phone {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  white-space: pre-line;
  word-break: break-word;
}

.assistant-phone i {
  font-size: 10px;
  margin-right: var(--space-1);
}

.hearing-block {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  background: var(--color-success-soft);
  border: 1px solid var(--color-success-soft);
  border-radius: var(--radius-md);
}

.hearing-date {
  color: var(--color-success);
  font-weight: var(--fw-semibold);
}

.legal-card-footer {
  margin-top: auto;
  padding-top: var(--space-2);
  border-top: 1px solid var(--color-border-subtle);
}

.legal-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.legal-form__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.legal-form__hint {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

@media (max-width: 768px) {
  .legal-grid {
    grid-template-columns: 1fr;
  }

  .case-info-row {
    grid-template-columns: 1fr;
    gap: var(--space-3);
  }

  .party-role {
    min-width: 70px;
  }

  .legal-work-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
