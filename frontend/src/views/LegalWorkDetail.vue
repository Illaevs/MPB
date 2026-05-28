<template>
  <div class="legal-detail-view p-3">
    <div class="d-flex justify-between align-center mb-3">
      <div class="d-flex align-center gap-2">
        <button class="btn btn-sm btn-outline-secondary" @click="goBack">
          <i class="fas fa-arrow-left"></i>
        </button>
        <div>
          <h2 class="m-0">{{ uiText.title }}</h2>
          <div class="text-muted small">{{ caseItem?.case_number || '-' }}</div>
        </div>
      </div>
      <div class="d-flex gap-2">
        <button class="btn btn-sm btn-outline-primary" @click="openCaseModal(caseItem)" :disabled="!caseItem">
          <i class="fas fa-edit"></i>
        </button>
        <button class="btn btn-sm btn-outline-danger" @click="deleteCase(caseItem)" :disabled="!caseItem">
          <i class="fas fa-trash"></i>
        </button>
      </div>
    </div>

    <div v-if="loading" class="d-flex flex-column gap-2">
      <SkeletonLoader height="160px" v-for="i in 3" :key="i" />
    </div>

    <div v-else-if="!caseItem" class="card p-4 text-center text-muted">
      <i class="fas fa-scale-balanced fa-2x mb-2"></i>
      <div>{{ uiText.empty }}</div>
    </div>

    <div v-else class="detail-stack">
      <div class="card p-3">
        <div class="section-title">{{ uiText.infoTitle }}</div>
        <div class="case-row">
          <span class="label">{{ uiText.caseNumberLabel }}</span>
          <span>{{ caseItem.case_number || '-' }}</span>
        </div>
        <div class="case-row">
          <span class="label">{{ uiText.judgeLabel }}</span>
          <span>{{ caseItem.judge || '-' }}</span>
        </div>
        <div class="case-row">
          <span class="label">{{ uiText.plaintiffLabel }}</span>
          <span>{{ caseItem.plaintiff_name || '-' }}</span>
        </div>
        <div class="case-row">
          <span class="label">{{ uiText.defendantLabel }}</span>
          <span>{{ caseItem.defendant_name || '-' }}</span>
        </div>
        <div class="case-row">
          <span class="label">{{ uiText.jurisdictionLabel }}</span>
          <span>{{ caseItem.jurisdiction || '-' }}</span>
        </div>
        <div class="case-row">
          <span class="label">{{ uiText.assistantLabel }}</span>
          <span>{{ caseItem.judge_assistant || '-' }}</span>
        </div>
        <div class="case-row">
          <span class="label">{{ uiText.assistantPhoneLabel }}</span>
          <span>{{ caseItem.judge_assistant_phone || '-' }}</span>
        </div>
        <div class="case-row">
          <span class="label">{{ uiText.lastHearingLabel }}</span>
          <span>{{ getLatestHearingDate(caseItem) }}</span>
        </div>
        <div class="case-row" v-if="caseItem.description">
          <span class="label">{{ uiText.descriptionLabel }}</span>
          <span>{{ caseItem.description }}</span>
        </div>
      </div>

      <div class="detail-columns">
        <div class="card p-3">
          <div class="d-flex justify-between align-center mb-2">
            <div class="section-title">{{ uiText.timelineTitle }}</div>
          </div>
          <div class="event-form mb-3">
            <select v-model="eventForm.event_type" class="form-control">
              <option value="">{{ uiText.eventTypePlaceholder }}</option>
              <option v-for="type in eventTypes" :key="type" :value="type">{{ type }}</option>
            </select>
            <input type="date" v-model="eventForm.event_date" class="form-control" />
            <input
              v-if="eventForm.event_type === hearingType"
              type="time"
              v-model="eventForm.event_time"
              class="form-control"
            />
            <input
              v-if="eventForm.event_type === hearingType"
              v-model="eventForm.courtroom"
              class="form-control"
              :placeholder="uiText.courtroomPlaceholder"
            />
            <button class="btn btn-sm btn-primary" @click="addEvent" :disabled="savingEvent">
              <i v-if="savingEvent" class="fas fa-spinner fa-spin"></i>
              {{ uiText.addEventButton }}
            </button>
          </div>

          <div v-if="!caseItem.events?.length" class="empty-events">
            <i class="fas fa-clock"></i>
            <span>{{ uiText.noEvents }}</span>
          </div>
          <div v-else class="timeline">
            <div v-for="event in sortedEvents" :key="event.id" class="timeline-item">
              <div class="timeline-marker" :style="{ background: getEventTypeColor(event.event_type) }"></div>
              <div class="timeline-content">
                <div class="timeline-header">
                  <span class="timeline-badge" :style="{ background: getEventTypeColor(event.event_type) + '20', color: getEventTypeColor(event.event_type) }">{{ event.event_type }}</span>
                  <span class="timeline-date">{{ formatDate(event.event_date) }}</span>
                  <span v-if="isHearing(event) && event.event_time" class="timeline-time">
                    <i class="fas fa-clock"></i> {{ formatTime(event.event_time) }}
                  </span>
                  <span v-if="isHearing(event) && event.courtroom" class="timeline-courtroom">
                    <i class="fas fa-door-open"></i> зал {{ event.courtroom }}
                  </span>
                </div>
                <div class="timeline-files" v-if="event.files?.length || true">
                  <div class="file-chips">
                    <div
                      v-for="fileItem in event.files || []"
                      :key="fileItem.id"
                      class="file-chip"
                    >
                      <button class="file-chip-main" @click="downloadEventFile(fileItem)">
                        <i class="fas" :class="getFileIcon(fileItem.file_name)"></i>
                        <span>{{ fileItem.file_name }}</span>
                      </button>
                      <button
                        class="file-chip-delete"
                        title="Удалить"
                        @click.stop="deleteEventFile(fileItem)"
                      >
                        <i class="fas fa-times"></i>
                      </button>
                    </div>
                  </div>
                  <label class="btn btn-sm btn-outline-secondary">
                    <input type="file" class="d-none" multiple @change="uploadEventFiles(event, $event)" />
                    <i class="fas fa-upload mr-1"></i> Загрузить
                  </label>
                </div>
              </div>
              <button class="btn btn-sm btn-icon text-danger timeline-delete" @click="deleteEvent(event)">
                <i class="fas fa-trash"></i>
              </button>
            </div>
          </div>
        </div>

        <div class="card p-3">
          <div class="d-flex justify-between align-center mb-2">
            <div class="section-title">{{ uiText.tasksTitle }}</div>
            <button class="btn btn-sm btn-outline-primary" @click="openTaskModal">
              <i class="fas fa-plus"></i> {{ uiText.taskAddButton }}
            </button>
          </div>

          <div v-if="!caseItem.tasks?.length" class="text-muted small">
            {{ uiText.tasksEmpty }}
          </div>
          <div v-else class="task-list">
            <div v-for="task in caseItem.tasks" :key="task.id" class="task-item">
              <div class="task-info">
                <div class="task-title">{{ task.title }}</div>
                <div class="task-meta">
                  <span>{{ task.deal_title || '-' }}</span>
                  <span>{{ formatDate(task.due_date) }}</span>
                </div>
              </div>
              <span class="task-status" :class="'task-status--' + (task.status || 'new')">{{ getStatusText(task.status) }}</span>
              <div class="task-actions">
                <button class="btn btn-sm btn-outline-secondary" @click="openTask(task)">
                  {{ uiText.taskOpen }}
                </button>
                <button class="btn btn-sm btn-outline-danger" @click="unlinkTask(task)">
                  <i class="fas fa-unlink"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showCaseModal" class="modal-overlay" @click="closeCaseModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ editingCase ? uiText.editCaseTitle : uiText.newCaseTitle }}</h3>
          <button class="btn btn-sm btn-secondary" @click="closeCaseModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <form @submit.prevent="saveCase" class="modal-body">
          <div class="form-group">
            <label>{{ uiText.caseNumberInput }}</label>
            <input v-model="caseForm.case_number" class="form-control" />
          </div>
          <div class="form-group">
            <label>{{ uiText.judgeInput }}</label>
            <input v-model="caseForm.judge" class="form-control" />
          </div>
          <div class="form-group">
            <label>{{ uiText.jurisdictionInput }}</label>
            <input v-model="caseForm.jurisdiction" class="form-control" />
          </div>
          <div class="form-group">
            <label>{{ uiText.assistantInput }}</label>
            <input v-model="caseForm.judge_assistant" class="form-control" />
          </div>
          <div class="form-group">
            <label>{{ uiText.assistantPhoneInput }}</label>
            <input v-model="caseForm.judge_assistant_phone" class="form-control" />
          </div>
          <div class="form-group">
            <label>{{ uiText.plaintiffInput }}</label>
            <CompanySmartSelect
              v-model="caseForm.plaintiff_id"
              :options="companies"
              fetch-url="/api/v1/companies/"
              :fetch-limit="200"
              :max-results="200"
              :placeholder="uiText.companyPlaceholder"
            />
          </div>
          <div class="form-group">
            <label>{{ uiText.defendantInput }}</label>
            <CompanySmartSelect
              v-model="caseForm.defendant_id"
              :options="companies"
              fetch-url="/api/v1/companies/"
              :fetch-limit="200"
              :max-results="200"
              :placeholder="uiText.companyPlaceholder"
            />
          </div>
          <div class="form-group">
            <label>{{ uiText.descriptionInput }}</label>
            <textarea v-model="caseForm.description" class="form-control" rows="3"></textarea>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeCaseModal">
              {{ uiText.cancel }}
            </button>
            <button type="submit" class="btn btn-primary" :disabled="savingCase">
              <i v-if="savingCase" class="fas fa-spinner fa-spin"></i>
              {{ editingCase ? uiText.save : uiText.create }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showTaskModal" class="modal-overlay" @click="closeTaskModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ taskMode === 'existing' ? uiText.taskModalTitleLink : uiText.taskModalTitleNew }}</h3>
          <button class="btn btn-sm btn-secondary" @click="closeTaskModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <form @submit.prevent="saveTask" class="modal-body">
          <div class="btn-group mb-3">
            <button
              type="button"
              class="btn btn-sm"
              :class="taskMode === 'new' ? 'btn-primary' : 'btn-outline-secondary'"
              @click="taskMode = 'new'"
            >
              {{ uiText.taskModeNew }}
            </button>
            <button
              type="button"
              class="btn btn-sm"
              :class="taskMode === 'existing' ? 'btn-primary' : 'btn-outline-secondary'"
              @click="taskMode = 'existing'"
            >
              {{ uiText.taskModeLink }}
            </button>
          </div>

          <template v-if="taskMode === 'existing'">
            <div class="form-group">
              <label>{{ uiText.taskDealFilterLabel }}</label>
              <select v-model="existingDealId" class="form-control">
                <option value="">{{ uiText.taskDealFilterAll }}</option>
                <option v-for="project in projects" :key="project.id" :value="project.id">{{ project.title }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>{{ uiText.taskSearchLabel }}</label>
              <input v-model="taskSearch" class="form-control" :placeholder="uiText.taskSearchPlaceholder" />
            </div>
            <div class="form-group">
              <label>{{ uiText.taskSelectLabel }}</label>
              <select v-model="existingTaskId" class="form-control" :disabled="tasksLoading">
                <option value="">{{ uiText.taskSelectPlaceholder }}</option>
                <option v-for="task in filteredExistingTasks" :key="task.id" :value="task.id">
                  {{ formatTaskOption(task) }}
                </option>
              </select>
            </div>
            <div v-if="!tasksLoading && !filteredExistingTasks.length" class="text-muted small">
              {{ uiText.taskNoneFound }}
            </div>
          </template>

          <template v-else>
            <div class="form-group">
              <label>{{ uiText.taskTitleLabel }}</label>
              <input v-model="taskForm.title" class="form-control" required />
            </div>
            <div class="form-group">
              <label>{{ uiText.taskDealLabel }}</label>
              <select v-model="taskForm.deal_id" class="form-control" required>
                <option value="">{{ uiText.taskDealPlaceholder }}</option>
                <option v-for="project in projects" :key="project.id" :value="project.id">{{ project.title }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>{{ uiText.taskDescriptionLabel }}</label>
              <textarea v-model="taskForm.description" class="form-control" rows="3"></textarea>
            </div>
            <div class="form-group">
              <label>{{ uiText.taskDueDateLabel }}</label>
              <input type="date" v-model="taskForm.due_date" class="form-control" />
            </div>
            <div class="form-group">
              <label>{{ uiText.taskCategoryLabel }}</label>
              <select v-model="taskForm.work_category" class="form-control">
                <option value="">{{ uiText.taskCategoryNone }}</option>
                <option v-for="cat in workCategories" :key="cat" :value="cat">{{ cat }}</option>
              </select>
            </div>
          </template>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeTaskModal">{{ uiText.taskCancel }}</button>
            <button type="submit" class="btn btn-primary" :disabled="savingTask">
              <i v-if="savingTask" class="fas fa-spinner fa-spin"></i>
              {{ taskMode === 'existing' ? uiText.taskLinkButton : uiText.taskCreateButton }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
  import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import axios from 'axios'
  import { api } from '../services/api'
  import SkeletonLoader from '../components/ui/SkeletonLoader.vue'
  import CompanySmartSelect from '../components/ui/CompanySmartSelect.vue'
  import { useUploadQueueStore } from '../stores/uploadQueue'
  import { useCompaniesStore } from '../stores/companies'
  import { downloadFromHref } from '../utils/download'

export default {
  name: 'LegalWorkDetail',
  components: { SkeletonLoader, CompanySmartSelect },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const companiesStore = useCompaniesStore()
    const loading = ref(false)
    const savingCase = ref(false)
    const savingEvent = ref(false)
    const savingTask = ref(false)
    const caseItem = ref(null)
    const companies = ref([])
    const projects = ref([])
    const showCaseModal = ref(false)
    const showTaskModal = ref(false)
    const editingCase = ref(null)
    const taskMode = ref('new')
    const existingTasks = ref([])
    const existingTaskId = ref('')
    const existingDealId = ref('')
    const taskSearch = ref('')
    const tasksLoading = ref(false)
    const uploadQueue = useUploadQueueStore()

    const workCategories = [
      'Юридическая',
      'Производственная',
      'Административная'
    ]
    const hearingType = 'Заседание'
    const eventTypes = [
      '\u0418\u0441\u043a\u043e\u0432\u043e\u0435 \u0437\u0430\u044f\u0432\u043b\u0435\u043d\u0438\u0435',
      '\u0425\u043e\u0434\u0430\u0442\u0430\u0439\u0441\u0442\u0432\u043e',
      '\u041f\u0438\u0441\u044c\u043c\u0435\u043d\u043d\u044b\u0435 \u043e\u0431\u044a\u044f\u0441\u043d\u0435\u043d\u0438\u044f',
      '\u041e\u0442\u0437\u044b\u0432',
      '\u0417\u0430\u0441\u0435\u0434\u0430\u043d\u0438\u0435',
      '\u0420\u0435\u0437\u043e\u043b\u044e\u0442\u0438\u0432\u043d\u0430\u044f \u0447\u0430\u0441\u0442\u044c \u0440\u0435\u0448\u0435\u043d\u0438\u044f',
      '\u041c\u043e\u0442\u0438\u0432\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u043e\u0435 \u0440\u0435\u0448\u0435\u043d\u0438\u0435',
      '\u0410\u043f\u0435\u043b\u043b\u044f\u0446\u0438\u043e\u043d\u043d\u0430\u044f \u0436\u0430\u043b\u043e\u0431\u0430',
      '\u041a\u0430\u0441\u0441\u0430\u0446\u0438\u043e\u043d\u043d\u0430\u044f \u0436\u0430\u043b\u043e\u0431\u0430',
      '\u0421\u043e\u0431\u044b\u0442\u0438\u0435',
      '\u041e\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u0435'
    ]

    const uiText = {
      title: 'Юридическая работа',
      empty: 'Дело не найдено',
      infoTitle: 'Карточка дела',
      timelineTitle: 'Хронология событий',
      tasksTitle: 'Связанные задачи',
      caseNumberLabel: '№ дела:',
      judgeLabel: 'Судья:',
      plaintiffLabel: 'Истец:',
      defendantLabel: 'Ответчик:',
      descriptionLabel: 'Описание:',
      lastHearingLabel: 'Последнее заседание:',
      jurisdictionLabel: 'Подсудность:',
      assistantLabel: 'Помощник судьи:',
      assistantPhoneLabel: 'Телефон помощника:',
      eventTypePlaceholder: 'Тип события',
      courtroomPlaceholder: '№ зала',
      addEventButton: 'Добавить',
      noEvents: 'Событий пока нет',
      eventFilesHeader: 'Файлы',
      eventFilesEmpty: 'Нет файлов',
      eventUpload: 'Загрузить',
      tasksEmpty: 'Связанных задач пока нет',
      taskAddButton: 'Добавить',
      taskOpen: 'Открыть',
      editCaseTitle: 'Редактировать дело',
      newCaseTitle: 'Новое дело',
      caseNumberInput: '№ дела',
      judgeInput: 'Судья',
      jurisdictionInput: 'Подсудность',
      assistantInput: 'Помощник судьи',
      assistantPhoneInput: 'Телефон помощника',
      plaintiffInput: 'Истец',
      defendantInput: 'Ответчик',
      descriptionInput: 'Описание',
      companyPlaceholder: 'Выберите контрагента',
      cancel: 'Отмена',
      save: 'Сохранить',
      create: 'Создать',
      taskModalTitleNew: 'Новая задача',
      taskModalTitleLink: 'Привязать задачу',
      taskModeNew: 'Новая',
      taskModeLink: 'Существующая',
      taskTitleLabel: 'Название *',
      taskDealLabel: 'Сделка *',
      taskDealPlaceholder: 'Выберите сделку',
      taskDescriptionLabel: 'Описание',
      taskDueDateLabel: 'Срок',
      taskCategoryLabel: 'Категория задачи',
      taskCategoryNone: 'Не указана',
      taskDealFilterLabel: 'Фильтр по сделке',
      taskDealFilterAll: 'Все сделки',
      taskSearchLabel: 'Поиск по задачам',
      taskSearchPlaceholder: 'Начните вводить',
      taskSelectLabel: 'Задача',
      taskSelectPlaceholder: 'Выберите задачу',
      taskNoneFound: 'Нет подходящих задач',
      taskCancel: 'Отмена',
      taskCreateButton: 'Создать',
      taskLinkButton: 'Привязать',
      taskSelectAlert: 'Выберите задачу',
      taskRequiredAlert: 'Название и сделка обязательны',
      taskLinkError: 'Ошибка привязки задачи',
      taskCreateError: 'Ошибка создания задачи',
      eventUploadError: 'Ошибка загрузки файлов',
      eventDownloadError: 'Ошибка скачивания файла',
      eventFileDeleteError: 'Ошибка удаления файла',
      eventAddError: 'Ошибка добавления события',
      eventDeleteError: 'Ошибка удаления события',
      caseSaveError: 'Ошибка сохранения',
      caseDeleteError: 'Ошибка удаления'
    }

    const caseForm = ref({
      case_number: '',
      judge: '',
      jurisdiction: '',
      judge_assistant: '',
      judge_assistant_phone: '',
      plaintiff_id: '',
      defendant_id: '',
      description: ''
    })

    const eventForm = ref({
      event_type: '',
      event_date: '',
      event_time: '',
      courtroom: ''
    })

    const taskForm = ref({
      title: '',
      description: '',
      deal_id: '',
      due_date: '',
      work_category: workCategories[0]
    })

    const caseId = computed(() => route.params.id)

    const loadCase = async () => {
      if (!caseId.value) return
      loading.value = true
      try {
        const data = await api.legal.getById(caseId.value)
        caseItem.value = data
      } catch (e) {
        console.error('Error loading case:', e)
        caseItem.value = null
      } finally {
        loading.value = false
      }
    }

    const loadCompanies = async () => {
      try {
        await companiesStore.ensureLoaded()
        companies.value = companiesStore.items
      } catch (e) {
        console.error('Error loading companies:', e)
      }
    }

    const loadProjects = async () => {
      try {
        const data = await api.deals.list()
        projects.value = data || []
      } catch (e) {
        console.error('Error loading projects:', e)
      }
    }

    const openCaseModal = (item) => {
      if (!item) return
      editingCase.value = item
      caseForm.value = {
        case_number: item.case_number || '',
        judge: item.judge || '',
        jurisdiction: item.jurisdiction || '',
        judge_assistant: item.judge_assistant || '',
        judge_assistant_phone: item.judge_assistant_phone || '',
        plaintiff_id: item.plaintiff_id || '',
        defendant_id: item.defendant_id || '',
        description: item.description || ''
      }
      showCaseModal.value = true
    }

    const closeCaseModal = () => {
      showCaseModal.value = false
      editingCase.value = null
    }

    const saveCase = async () => {
      if (!editingCase.value) return
      savingCase.value = true
      try {
        await api.legal.update(editingCase.value.id, caseForm.value)
        await loadCase()
        closeCaseModal()
      } catch (e) {
        console.error(e)
        alert(uiText.caseSaveError)
      } finally {
        savingCase.value = false
      }
    }

    const deleteCase = async (item) => {
      if (!item) return
      if (!confirm('Удалить дело?')) return
      try {
        await api.legal.remove(item.id)
        router.push({ path: '/legal-work' })
      } catch (e) {
        console.error(e)
        alert(uiText.caseDeleteError)
      }
    }

    const addEvent = async () => {
      if (!caseItem.value) return
      if (!eventForm.value.event_type || !eventForm.value.event_date) {
        return alert('Заполните тип и дату')
      }
      savingEvent.value = true
      try {
        const payload = {
          event_type: eventForm.value.event_type,
          event_date: eventForm.value.event_date
        }
        if (eventForm.value.event_type === hearingType) {
          payload.event_time = eventForm.value.event_time || null
          payload.courtroom = eventForm.value.courtroom || null
        }
        await api.legal.addEvent(caseItem.value.id, payload)
        eventForm.value = { event_type: '', event_date: '', event_time: '', courtroom: '' }
        await loadCase()
      } catch (e) {
        console.error(e)
        alert(uiText.eventAddError)
      } finally {
        savingEvent.value = false
      }
    }

    const deleteEvent = async (event) => {
      if (!confirm('Удалить событие?')) return
      try {
        await api.legal.removeEvent(event.id)
        await loadCase()
      } catch (e) {
        console.error(e)
        alert(uiText.eventDeleteError)
      }
    }

    const uploadEventFiles = async (event, changeEvent) => {
      const input = changeEvent.target
      const files = Array.from(input.files || [])
      if (!files.length) return
      let hasSuccess = false
      for (const file of files) {
        const localId = uploadQueue.addLocalUpload({
          fileName: file.name,
          module: 'legal_work',
          entityId: event.id
        })
        try {
          const formData = new FormData()
          formData.append('file', file)
          const response = await axios.post(`/api/v1/uploads/legal-work/events/${event.id}`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            onUploadProgress: (eventProgress) => {
              if (!eventProgress.total) return
              const progress = (eventProgress.loaded / eventProgress.total) * 100
              uploadQueue.updateProgress(localId, progress)
            }
          })
          uploadQueue.markQueued(localId, response.data)
          hasSuccess = true
        } catch (e) {
          console.error(e)
          uploadQueue.markError(localId, e?.response?.data?.detail)
          alert(uiText.eventUploadError)
        }
      }
      if (hasSuccess) {
        void loadCase()
      }
      input.value = ''
    }

    const downloadEventFile = async (fileItem) => {
      try {
        const data = await api.legal.downloadEventFileMeta(fileItem.id)
        if (!data?.href) {
          throw new Error('Download link missing')
        }
        await downloadFromHref(data.href, fileItem.file_name || 'file')
      } catch (e) {
        console.error(e)
        alert(uiText.eventDownloadError)
      }
    }

    const deleteEventFile = async (fileItem) => {
      if (!confirm('Удалить файл?')) return
      try {
        await api.legal.removeEventFile(fileItem.id)
        await loadCase()
      } catch (e) {
        console.error(e)
        alert(uiText.eventFileDeleteError)
      }
    }

    const openTaskModal = () => {
      if (!caseItem.value) return
      taskMode.value = 'new'
      existingTaskId.value = ''
      existingDealId.value = ''
      taskSearch.value = ''
      existingTasks.value = []
      taskForm.value = {
        title: '',
        description: '',
        deal_id: '',
        due_date: '',
        work_category: workCategories[0]
      }
      showTaskModal.value = true
    }

    const closeTaskModal = () => {
      showTaskModal.value = false
    }

    const saveTask = async () => {
      if (!caseItem.value) return
      if (taskMode.value === 'existing') {
        if (!existingTaskId.value) {
          return alert(uiText.taskSelectAlert)
        }
        savingTask.value = true
        try {
          await api.legal.linkTask(caseItem.value.id, { task_id: existingTaskId.value })
          await loadCase()
          closeTaskModal()
        } catch (e) {
          console.error(e)
          alert(e.response?.data?.detail || uiText.taskLinkError)
        } finally {
          savingTask.value = false
        }
        return
      }
      if (!taskForm.value.title.trim() || !taskForm.value.deal_id) {
        return alert(uiText.taskRequiredAlert)
      }
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
        await api.legal.linkTask(caseItem.value.id, { task_id: created.id })
        await loadCase()
        closeTaskModal()
      } catch (e) {
        console.error(e)
        alert(e.response?.data?.detail || uiText.taskCreateError)
      } finally {
        savingTask.value = false
      }
    }

    const unlinkTask = async (task) => {
      if (!caseItem.value) return
      if (!confirm('Отвязать задачу?')) return
      try {
        await api.legal.unlinkTask(caseItem.value.id, task.id)
        await loadCase()
      } catch (e) {
        console.error(e)
        alert('Ошибка отвязки задачи')
      }
    }

    const openTask = (task) => {
      router.push({ path: '/tasks', query: { task_id: task.id } })
    }

    const loadExistingTasks = async () => {
      tasksLoading.value = true
      try {
        const params = { limit: 200 }
        if (existingDealId.value) {
          params.deal_id = existingDealId.value
        }
        const res = await api.tasks.list(params)
        existingTasks.value = res.data || []
      } catch (e) {
        console.error(e)
        existingTasks.value = []
      } finally {
        tasksLoading.value = false
      }
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

    watch(taskMode, (mode) => {
      if (mode === 'existing') {
        loadExistingTasks()
      }
    })

    watch(existingDealId, () => {
      if (taskMode.value === 'existing') {
        loadExistingTasks()
      }
    })

    watch(() => eventForm.value.event_type, (value) => {
      if (value !== hearingType) {
        eventForm.value.event_time = ''
        eventForm.value.courtroom = ''
      }
    })

    const formatDate = (value) => (value ? new Date(value).toLocaleDateString('ru-RU') : '-')
    const formatTime = (value) => {
      if (!value) return ''
      if (typeof value === 'string') return value.slice(0, 5)
      return String(value).slice(0, 5)
    }

    const isHearing = (event) => event?.event_type === hearingType

    const getLatestHearingDate = (item) => {
      const events = item?.events || []
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

    const sortedEvents = computed(() => {
      const events = caseItem.value?.events || []
      return [...events].sort((a, b) => new Date(b.event_date) - new Date(a.event_date))
    })

    const getEventTypeColor = (eventType) => {
      const colors = {
        'Заседание': '#dc2626',
        'Исковое заявление': '#2563eb',
        'Ходатайство': '#f59e0b',
        'Письменные объяснения': '#6366f1',
        'Отзыв': '#8b5cf6',
        'Резолютивная часть решения': '#16a34a',
        'Мотивированное решение': '#059669',
        'Апелляционная жалоба': '#ea580c',
        'Кассационная жалоба': '#dc2626',
        'Событие': '#64748b',
        'Определение': '#0891b2'
      }
      return colors[eventType] || '#64748b'
    }

    const getFileIcon = (filename) => {
      const ext = (filename || '').split('.').pop().toLowerCase()
      if (['pdf'].includes(ext)) return 'fa-file-pdf text-danger'
      if (['doc', 'docx'].includes(ext)) return 'fa-file-word text-primary'
      if (['xls', 'xlsx'].includes(ext)) return 'fa-file-excel text-success'
      if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) return 'fa-file-image text-info'
      if (['zip', 'rar', '7z'].includes(ext)) return 'fa-file-archive text-warning'
      return 'fa-file text-muted'
    }

    const getStatusText = (status) => ({
      new: 'Новая',
      in_progress: 'В работе',
      pending: 'Ожидает',
      completed: 'Завершена',
      cancelled: 'Отменена',
      deferred: 'Отложена'
    })[status] || status || '-'

    const goBack = () => {
      router.push({ path: '/legal-work' })
    }

    const onUploadJobDone = (payload) => {
      const job = payload?.detail
      if (!job || job.module !== 'legal_work') return
      if (!caseItem.value || String(job.entity_id) !== String(caseItem.value.id)) return
      loadCase()
    }

    onMounted(async () => {
      window.addEventListener('upload-job-done', onUploadJobDone)
      await Promise.all([loadCase(), loadCompanies(), loadProjects()])
    })

    onBeforeUnmount(() => {
      window.removeEventListener('upload-job-done', onUploadJobDone)
    })

    watch(() => caseId.value, () => {
      loadCase()
    })

    return {
      loading,
      caseItem,
      companies,
      projects,
      eventTypes,
      eventForm,
      workCategories,
      uiText,
      showCaseModal,
      showTaskModal,
      editingCase,
      caseForm,
      taskForm,
      taskMode,
      existingTasks,
      existingTaskId,
      existingDealId,
      taskSearch,
      tasksLoading,
      filteredExistingTasks,
      savingCase,
      savingEvent,
      savingTask,
      openCaseModal,
      closeCaseModal,
      saveCase,
      deleteCase,
      addEvent,
      deleteEvent,
      uploadEventFiles,
      downloadEventFile,
      deleteEventFile,
      openTaskModal,
      closeTaskModal,
      saveTask,
      unlinkTask,
      openTask,
      formatTaskOption,
      formatDate,
      formatTime,
      getStatusText,
      getLatestHearingDate,
      hearingType,
      isHearing,
      goBack,
      sortedEvents,
      getEventTypeColor,
      getFileIcon
    }
  }
}
</script>

<style scoped>
.detail-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-columns {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.section-title {
  font-weight: 600;
  margin-bottom: 12px;
}

.case-row {
  display: flex;
  gap: 8px;
  align-items: baseline;
  font-size: 0.95rem;
  margin-bottom: 6px;
}

.case-row .label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--md-sys-color-on-surface-variant);
  min-width: 120px;
}

.event-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)) auto;
  gap: 8px;
  align-items: center;
  padding: 12px;
  background: var(--md-sys-color-surface-container-low);
  border-radius: 12px;
}

/* Empty Events */
.empty-events {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 32px;
  color: var(--md-sys-color-on-surface-variant);
}

.empty-events i {
  font-size: 24px;
  opacity: 0.5;
}

/* Timeline */
.timeline {
  position: relative;
  padding-left: 24px;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 6px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: var(--md-sys-color-outline-variant);
  border-radius: 2px;
}

.timeline-item {
  position: relative;
  display: flex;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.timeline-item:last-child {
  border-bottom: none;
}

.timeline-marker {
  position: absolute;
  left: -24px;
  top: 20px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
  z-index: 1;
}

.timeline-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.timeline-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.timeline-badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 6px;
}

.timeline-date {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.timeline-time,
.timeline-courtroom {
  font-size: 0.8rem;
  color: var(--md-sys-color-on-surface-variant);
  display: flex;
  align-items: center;
  gap: 4px;
}

.timeline-time i,
.timeline-courtroom i {
  font-size: 10px;
}

.timeline-files {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.file-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.file-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: var(--md-sys-color-surface-container-low);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 8px;
  font-size: 0.8rem;
  transition: all 0.2s;
}

.file-chip:hover {
  background: var(--md-sys-color-surface-container);
  border-color: var(--md-sys-color-primary);
}

.file-chip-main {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  padding: 0;
}

.file-chip-delete {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  background: transparent;
  color: var(--md-sys-color-error);
  border-radius: 50%;
  cursor: pointer;
  font-size: 0.7rem;
}

.file-chip-delete:hover {
  background: rgba(255, 0, 0, 0.08);
}

.file-chip span {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.timeline-delete {
  align-self: flex-start;
  opacity: 0.5;
  transition: opacity 0.2s;
}

.timeline-item:hover .timeline-delete {
  opacity: 1;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--md-sys-color-surface-container-low);
  border: 1px solid var(--md-sys-color-outline-variant);
  transition: all 0.2s;
}

.task-item:hover {
  border-color: var(--md-sys-color-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.task-info {
  flex: 1;
  min-width: 0;
}

.task-title {
  font-weight: 600;
  margin-bottom: 2px;
}

.task-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.8rem;
}

.task-status {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 999px;
  white-space: nowrap;
}

.task-status--new {
  background: rgba(59, 130, 246, 0.15);
  color: #2563eb;
}

.task-status--in_progress {
  background: rgba(245, 158, 11, 0.15);
  color: #d97706;
}

.task-status--completed {
  background: rgba(34, 197, 94, 0.15);
  color: #16a34a;
}

.task-status--pending {
  background: rgba(107, 114, 128, 0.15);
  color: #4b5563;
}

.task-status--cancelled {
  background: rgba(239, 68, 68, 0.15);
  color: #dc2626;
}

.task-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

@media (max-width: 900px) {
  .detail-columns {
    grid-template-columns: 1fr;
  }

  .event-form {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .timeline {
    padding-left: 20px;
  }

  .timeline-marker {
    left: -20px;
    width: 12px;
    height: 12px;
  }

  .timeline-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }

  .timeline-files {
    flex-direction: column;
    align-items: flex-start;
  }

  .file-chip span {
    max-width: 200px;
  }

  .task-item {
    flex-direction: column;
    align-items: stretch;
  }

  .task-actions {
    justify-content: flex-end;
    padding-top: 8px;
    border-top: 1px solid var(--md-sys-color-outline-variant);
    margin-top: 8px;
  }
}
</style>
