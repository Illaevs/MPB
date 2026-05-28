<template>
  <div class="data-health-view">
    <div class="dh-card">
    <header class="data-health-header">
      <div class="data-health-header__main">
        <h1>Контроль данных</h1>
        <div class="data-health-header__stats">
          <span class="data-health-stat data-health-stat--total">{{ summary.total || totalIssues || 0 }} проблем</span>
          <span class="data-health-header__divider">/</span>
          <span class="data-health-stat data-health-stat--error">{{ summary.errors || 0 }} ошибок</span>
          <span class="data-health-header__divider">/</span>
          <span class="data-health-stat data-health-stat--warning">{{ summary.warnings || 0 }} предупр.</span>
          <span class="data-health-header__divider">/</span>
          <span class="data-health-stat data-health-stat--ignored">{{ summary.ignored || 0 }} игнор</span>
        </div>
      </div>
      <div class="data-health-header__updated">
        Последнее обновление: {{ lastUpdatedLabel }}
      </div>
    </header>

    <section class="data-health-filters">
      <div class="data-health-filters__search">
        <UiInput
          v-model.trim="search"
          icon-left="fas fa-search"
          placeholder="Поиск по проблеме, сделке или модулю..."
          @update:modelValue="debouncedLoad"
        />
      </div>

      <div class="data-health-filters__field">
        <span>Статус</span>
        <UiSelect v-model="statusFilter" :options="statusOptions" @change="loadIssues(false)" />
      </div>

      <div class="data-health-filters__field">
        <span>Критичность</span>
        <UiSelect v-model="severityFilter" :options="severityOptions" @change="loadIssues(false)" />
      </div>

      <div class="data-health-filters__field">
        <span>Модуль</span>
        <UiSelect v-model="moduleFilter" :options="moduleOptions" @change="loadIssues(false)" />
      </div>

      <div class="data-health-filters__actions">
        <UiButton variant="secondary" icon-left="fas fa-rotate-left" @click="resetFilters">
          Сбросить
        </UiButton>
        <UiButton variant="primary" icon-left="fas fa-sync-alt" :loading="loading" @click="loadIssues(true)">
          Перепроверить
        </UiButton>
        <UiButton variant="ghost" icon-left="fas fa-layer-group" @click="toggleGroupedView">
          {{ groupedView ? 'Группы' : 'Список' }}
        </UiButton>
        <UiButton variant="ghost" icon-left="fas fa-file-pdf" :loading="reportDownloading" :disabled="reportDownloading" @click="downloadReport">
          PDF
        </UiButton>
      </div>
    </section>

    <section class="data-health-board">
      <div class="data-health-board__head">
        <div>Реестр проблем</div>
        <div>Модуль</div>
        <div>Дата обновления</div>
        <div>Действия</div>
      </div>

      <div v-if="loading" class="data-health-loading">
        <SkeletonLoader v-for="i in 6" :key="`health-skel-${i}`" height="68px" />
      </div>

      <UiEmptyState
        v-else-if="!paginatedIssues.length"
        class="data-health-empty"
        icon="fas fa-shield-heart"
        title="Активных проблем не найдено"
        description="После новых проверок сюда попадут найденные несоответствия."
      />

      <div v-else class="data-health-board__body">
        <article
          v-for="issue in paginatedIssues"
          :key="issue.group_key || issue.id"
          class="data-health-issue"
          :class="{ 'data-health-issue--expanded': isGroupedIssue(issue) && isGroupExpanded(issue) }"
        >
          <div
            role="button"
            tabindex="0"
            class="data-health-issue__row"
            @click="openIssue(issue)"
            @keydown.enter="openIssue(issue)"
          >
            <div class="data-health-issue__main">
              <div class="data-health-issue__badges">
                <UiBadge :variant="severityBadgeVariant(issue.severity)" size="sm">
                  {{ severityLabel(issue.severity) }}
                </UiBadge>
                <UiBadge v-if="isGroupedIssue(issue)" variant="neutral" size="sm" outline>
                  {{ issue.count }} шт.
                </UiBadge>
              </div>
              <h3>{{ issue.title }}</h3>
              <p>{{ issue.description }}</p>
              <div class="data-health-issue__meta">
                <span v-if="issue.deal_title">Сделка: {{ issue.deal_title }}</span>
                <span v-if="issue.payload?.stage_name">Этап: {{ issue.payload.stage_name }}</span>
                <span v-if="issue.payload?.product_name">Товар: {{ issue.payload.product_name }}</span>
                <span v-if="issue.payload?.contract_number">Договор: {{ issue.payload.contract_number }}</span>
                <span v-if="issue.payload?.outgoing_number">Письмо: {{ issue.payload.outgoing_number }}</span>
              </div>
            </div>

            <div class="data-health-issue__module">
              <span>{{ moduleLabel(issue.module) }}</span>
            </div>

            <div class="data-health-issue__date">
              <i class="fas fa-clock"></i>
              <span>{{ formatDateTime(issue.last_detected_at || issue.first_detected_at) }}</span>
            </div>

            <div class="data-health-issue__actions" @click.stop>
              <UiButton size="xs" variant="primary" @click="openIssue(issue)">Исправить</UiButton>
              <UiButton
                v-if="isGroupedIssue(issue)"
                size="xs"
                variant="secondary"
                @click="toggleGroup(issue)"
              >
                {{ isGroupExpanded(issue) ? 'Скрыть' : 'Детали' }}
              </UiButton>
              <UiButton
                v-else-if="issue.status !== 'ignored'"
                size="xs"
                variant="secondary"
                @click="openIgnoreModal(issue)"
              >
                Игнор
              </UiButton>
              <UiButton
                v-else
                size="xs"
                variant="ghost"
                @click="setIssueStatus(issue, 'open')"
              >
                Вернуть
              </UiButton>
            </div>
          </div>

          <div v-if="isGroupedIssue(issue) && isGroupExpanded(issue)" class="data-health-issue__details">
            <div class="data-health-issue__details-grid">
              <div>
                <div class="data-health-issue__details-title">Описание инцидента</div>
                <div class="data-health-issue__details-card">{{ issue.description || issue.title }}</div>
              </div>
              <div>
                <div class="data-health-issue__details-title">Связанные объекты</div>
                <button
                  v-for="child in issue.items"
                  :key="child.id"
                  type="button"
                  class="data-health-child"
                  @click="openIssue(child)"
                >
                  <span>{{ child.payload?.product_name || child.payload?.stage_name || child.description || child.title }}</span>
                  <small>{{ formatDateTime(child.last_detected_at || child.first_detected_at) }}</small>
                </button>
              </div>
            </div>
          </div>
        </article>
      </div>

      <footer v-if="issues.length" class="data-health-pagination">
        <div>
          Показано {{ pageStart }}-{{ pageEnd }} из {{ issues.length }}
        </div>
        <div class="data-health-pagination__controls">
          <UiIconButton
            icon="fas fa-chevron-left"
            label="Назад"
            size="sm"
            :disabled="currentPage <= 1"
            @click="goToPage(currentPage - 1)"
          />
          <span>{{ currentPage }} / {{ totalPages }}</span>
          <UiIconButton
            icon="fas fa-chevron-right"
            label="Вперёд"
            size="sm"
            :disabled="currentPage >= totalPages"
            @click="goToPage(currentPage + 1)"
          />
        </div>
      </footer>
    </section>
    </div>

    <UiModal
      v-model="ignoreModal.visible"
      title="Игнорировать проблему"
      size="sm"
      :closable="!ignoreModal.saving"
      :close-on-overlay="!ignoreModal.saving"
      @close="closeIgnoreModal"
    >
      <div class="data-health-ignore-form">
        <div class="data-health-ignore-form__field">
          <span class="data-health-ignore-form__label">Проблема</span>
          <div class="data-health-ignore-modal__title">{{ ignoreModal.issue?.title }}</div>
        </div>

        <UiTextarea
          v-model.trim="ignoreModal.reason"
          label="Причина"
          :rows="4"
          placeholder="Почему проблему можно временно не учитывать"
        />

        <UiInput
          v-model="ignoreModal.until"
          type="datetime-local"
          label="Игнорировать до"
          hint="Если срок не указан, проблема останется в игноре до ручного возврата."
        />
      </div>

      <template #footer>
        <UiButton variant="secondary" :disabled="ignoreModal.saving" @click="closeIgnoreModal">Отмена</UiButton>
        <UiButton variant="primary" :loading="ignoreModal.saving" @click="confirmIgnoreIssue">
          Игнорировать
        </UiButton>
      </template>
    </UiModal>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api'
import debounce from 'lodash/debounce'
import SkeletonLoader from '../components/ui/SkeletonLoader.vue'
import {
  UiBadge,
  UiButton,
  UiEmptyState,
  UiIconButton,
  UiInput,
  UiModal,
  UiSelect,
  UiTextarea
} from '../components/ui'

const STATUS_OPTIONS = [
  { value: 'active', label: 'Активные' },
  { value: 'open', label: 'Открытые' },
  { value: 'ignored', label: 'Игнор' },
  { value: 'resolved', label: 'Решенные' }
]

const SEVERITY_OPTIONS = [
  { value: '', label: 'Все' },
  { value: 'error', label: 'Ошибка' },
  { value: 'warning', label: 'Предупреждение' },
  { value: 'info', label: 'Инфо' }
]

const MODULE_OPTIONS = [
  { value: '', label: 'Все' },
  { value: 'projects', label: 'Сделки' },
  { value: 'stages', label: 'Этапы' },
  { value: 'contracting', label: 'Контрактация' },
  { value: 'outgoing', label: 'Письма' },
  { value: 'contracts', label: 'Договоры' }
]

const router = useRouter()

const issues = ref([])
const loading = ref(false)
const totalIssues = ref(0)
const search = ref('')
const severityFilter = ref('')
const moduleFilter = ref('')
const statusFilter = ref('active')
const groupedView = ref(true)
const reportDownloading = ref(false)
const expandedGroups = ref([])
const currentPage = ref(1)
const pageSize = 10
const lastUpdatedAt = ref(null)
const ignoreModal = ref({
  visible: false,
  issue: null,
  reason: '',
  until: '',
  saving: false
})
const summary = ref({
  total: 0,
  open: 0,
  ignored: 0,
  resolved: 0,
  errors: 0,
  warnings: 0,
  infos: 0
})

const statusOptions = STATUS_OPTIONS
const severityOptions = SEVERITY_OPTIONS
const moduleOptions = MODULE_OPTIONS

const totalPages = computed(() => Math.max(1, Math.ceil(issues.value.length / pageSize)))
const paginatedIssues = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return issues.value.slice(start, start + pageSize)
})
const pageStart = computed(() => (issues.value.length ? (currentPage.value - 1) * pageSize + 1 : 0))
const pageEnd = computed(() => Math.min(currentPage.value * pageSize, issues.value.length))
const lastUpdatedLabel = computed(() => lastUpdatedAt.value ? formatDateTime(lastUpdatedAt.value) : 'не выполнялось')

const goToPage = (page) => {
  currentPage.value = Math.min(Math.max(Number(page) || 1, 1), totalPages.value)
}

const loadIssues = async (refresh = false, options = {}) => {
  const shouldRefresh = refresh === true
  const previousPage = currentPage.value
  loading.value = true
  try {
    const params = {
      refresh: shouldRefresh,
      search: search.value || undefined,
      severity: severityFilter.value || undefined,
      module: moduleFilter.value || undefined,
      status: statusFilter.value || 'active',
      limit: groupedView.value ? 200 : 500
    }
    const data = groupedView.value
      ? await api.dataHealth.listIssueGroups(params)
      : await api.dataHealth.listIssues(params)
    issues.value = data.items || []
    expandedGroups.value = []
    summary.value = data.summary || summary.value
    totalIssues.value = Number(summary.value?.total || data.total || 0)
    lastUpdatedAt.value = new Date().toISOString()
    currentPage.value = options.preservePage ? Math.min(previousPage, totalPages.value) : 1
  } catch (error) {
    console.error('Error loading data health issues:', error)
    issues.value = []
    totalIssues.value = 0
    currentPage.value = 1
  } finally {
    loading.value = false
  }
}

const debouncedLoad = debounce(() => loadIssues(false), 300)

const toggleGroupedView = () => {
  groupedView.value = !groupedView.value
  loadIssues(false)
}

const isGroupedIssue = (issue) => Boolean(groupedView.value && Number(issue?.count || 0) > 1)

const isGroupExpanded = (issue) => expandedGroups.value.includes(issue?.group_key || issue?.id)

const toggleGroup = (issue) => {
  const key = issue?.group_key || issue?.id
  if (!key) return
  if (expandedGroups.value.includes(key)) {
    expandedGroups.value = expandedGroups.value.filter((item) => item !== key)
  } else {
    expandedGroups.value = [...expandedGroups.value, key]
  }
}

const downloadReport = async () => {
  reportDownloading.value = true
  try {
    const response = await api.dataHealth.downloadReportPdf({
      refresh: false,
      search: search.value || undefined,
      severity: severityFilter.value || undefined,
      module: moduleFilter.value || undefined,
      status: statusFilter.value || 'active',
      grouped: groupedView.value
    })
    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `data-health-${new Date().toISOString().slice(0, 10)}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Error downloading data health report:', error)
  } finally {
    reportDownloading.value = false
  }
}

const resetFilters = () => {
  search.value = ''
  severityFilter.value = ''
  moduleFilter.value = ''
  statusFilter.value = 'active'
  loadIssues(false)
}

const setIssueStatus = async (issue, status) => {
  try {
    if (status === 'ignored') {
      await api.dataHealth.ignoreIssue(issue.id)
    } else {
      await api.dataHealth.openIssue(issue.id)
    }
    await loadIssues(false, { preservePage: true })
  } catch (error) {
    console.error('Error updating data health issue status:', error)
  }
}

const openIgnoreModal = (issue) => {
  ignoreModal.value = {
    visible: true,
    issue,
    reason: issue?.ignored_reason || '',
    until: '',
    saving: false
  }
}

const closeIgnoreModal = () => {
  if (ignoreModal.value.saving) return
  ignoreModal.value = {
    visible: false,
    issue: null,
    reason: '',
    until: '',
    saving: false
  }
}

const confirmIgnoreIssue = async () => {
  const issue = ignoreModal.value.issue
  if (!issue) return
  ignoreModal.value.saving = true
  try {
    await api.dataHealth.ignoreIssue(issue.id, {
      reason: ignoreModal.value.reason || null,
      ignored_until: ignoreModal.value.until ? new Date(ignoreModal.value.until).toISOString() : null
    })
    closeIgnoreModal()
    await loadIssues(false, { preservePage: true })
  } catch (error) {
    console.error('Error ignoring data health issue:', error)
    ignoreModal.value.saving = false
  }
}

const openIssue = (issue) => {
  if (!issue?.navigation_path) {
    if (isGroupedIssue(issue)) {
      toggleGroup(issue)
    }
    return
  }
  router.push({
    path: issue.navigation_path,
    query: issue.navigation_query || {}
  })
}

const formatDateTime = (value) => {
  if (!value) return 'Без даты'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

const severityLabel = (value) => {
  if (value === 'error') return 'Ошибка'
  if (value === 'warning') return 'Предупреждение'
  return 'Инфо'
}

const severityBadgeVariant = (value) => {
  if (value === 'error') return 'danger'
  if (value === 'warning') return 'warning'
  return 'info'
}

const moduleLabel = (value) => {
  if (value === 'projects') return 'Сделки'
  if (value === 'stages') return 'Этапы'
  if (value === 'contracting') return 'Контрактация'
  if (value === 'outgoing') return 'Письма'
  if (value === 'contracts') return 'Договоры'
  return value || 'Прочее'
}

onMounted(() => {
  loadIssues(true)
})
</script>

<style scoped>
/* ── Tasks reference standard: single unified card (toolbar header →
   filters band → board body), white chrome, soft shadow, max density ── */
.data-health-view {
  --apr-card-bg: rgba(255, 255, 255, 0.97);
  --apr-card-border: rgba(216, 224, 240, 0.92);
  --apr-card-shadow: 0 18px 42px rgba(15, 23, 42, 0.06);
  --apr-radius: 20px;
  --apr-ink: #0a1629;
  --apr-muted: #7d8592;
  --apr-soft: #f6f8fb;
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 84px);
  padding: 12px;
  color: var(--color-text);
}

.dh-card {
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

.data-health-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  flex-wrap: wrap;
  padding: 10px 16px;
  border-bottom: 1px solid var(--apr-card-border);
}

.data-health-header__main {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.data-health-header h1 {
  margin: 0;
  color: var(--apr-ink);
  font-size: 1.15rem;
  font-weight: 800;
}

.data-health-header__stats {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  color: var(--apr-muted);
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  flex-wrap: wrap;
}

.data-health-header__divider {
  color: var(--color-text-subtle);
}

.data-health-header__updated {
  color: var(--apr-muted);
  font-size: 0.72rem;
  font-weight: 700;
  white-space: nowrap;
}

.data-health-stat {
  display: inline-flex;
  align-items: center;
  min-height: 20px;
  padding: 0 7px;
  border-radius: var(--radius-xs);
}

.data-health-stat--total {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.data-health-stat--error {
  color: var(--color-danger);
  background: var(--color-danger-soft);
}

.data-health-stat--warning {
  color: var(--color-warning);
  background: var(--color-warning-soft);
}

.data-health-stat--ignored {
  color: var(--color-text-muted);
  background: var(--color-surface-2);
}

.data-health-filters {
  display: flex;
  align-items: end;
  gap: 10px;
  flex-wrap: wrap;
  padding: 8px 16px;
  border-bottom: 1px solid var(--apr-card-border);
  background: var(--apr-soft);
}

.data-health-filters__search {
  flex: 1 1 320px;
  min-width: 220px;
}

.data-health-filters__field {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 140px;
}

.data-health-filters__field span,
.data-health-issue__details-title {
  color: var(--apr-muted);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.data-health-filters__actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.data-health-board {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.data-health-board__head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 140px 180px 200px;
  gap: 16px;
  padding: 8px 16px;
  border-bottom: 1px solid var(--apr-card-border);
  background: var(--apr-soft);
  color: var(--apr-muted);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.data-health-board__head > div:last-child {
  text-align: right;
}

.data-health-loading {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 10px 16px;
}

.data-health-board__body {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: auto;
}

.data-health-issue {
  border-bottom: 1px solid var(--apr-card-border);
  transition: background-color var(--dur-fast) ease;
}

.data-health-issue:last-child {
  border-bottom: 0;
}

.data-health-issue:hover,
.data-health-issue--expanded {
  background: var(--apr-soft);
}

.data-health-issue__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 140px 180px 200px;
  gap: 16px;
  align-items: center;
  width: 100%;
  padding: 9px 16px;
  border: 0;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.data-health-issue__main {
  min-width: 0;
}

.data-health-issue__badges {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0 8px 0 0;
  flex-wrap: wrap;
  vertical-align: middle;
}

.data-health-issue__main h3 {
  display: inline;
  margin: 0;
  color: var(--apr-ink);
  font-size: 0.9rem;
  font-weight: 700;
  line-height: var(--leading-tight);
}

.data-health-issue__main p {
  display: -webkit-box;
  margin: 3px 0 0;
  overflow: hidden;
  color: var(--apr-muted);
  font-size: 0.8rem;
  line-height: var(--leading-normal);
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
}

.data-health-issue__meta {
  display: flex;
  gap: 10px;
  margin-top: 3px;
  overflow: hidden;
  color: var(--apr-muted);
  font-size: 0.72rem;
  white-space: nowrap;
}

.data-health-issue__meta span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.data-health-issue__module {
  display: flex;
  align-items: center;
}

.data-health-issue__module span {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 0 8px;
  border-radius: var(--radius-xs);
  background: var(--apr-soft);
  color: #5f6b7c;
  font-size: 0.72rem;
  font-weight: 700;
}

.data-health-issue__date {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--apr-muted);
  font-size: 0.78rem;
  font-weight: 600;
}

.data-health-issue__date i {
  color: var(--color-text-subtle);
  font-size: 0.78rem;
}

.data-health-issue__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.data-health-issue__details {
  overflow: hidden;
  border-top: 1px solid var(--apr-card-border);
  background: var(--apr-soft);
}

.data-health-issue__details-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 0.8fr);
  gap: 16px;
  padding: 14px 16px;
}

.data-health-issue__details-card {
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: var(--text-base);
  line-height: var(--leading-normal);
}

.data-health-child {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  margin-bottom: var(--space-2);
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  text-align: left;
}

.data-health-child:hover {
  border-color: var(--color-primary);
}

.data-health-child small {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  white-space: nowrap;
}

.data-health-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: 8px 16px;
  border-top: 1px solid var(--apr-card-border);
  background: var(--apr-soft);
  color: var(--apr-muted);
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.data-health-pagination__controls {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.data-health-ignore-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.data-health-ignore-form__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.data-health-ignore-form__label {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
}

.data-health-ignore-modal__title {
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
  color: var(--color-text);
  font-weight: var(--fw-semibold);
}

.data-health-empty {
  flex: 1;
}

@media (max-width: 1280px) {
  .data-health-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .data-health-board__head,
  .data-health-issue__row {
    grid-template-columns: minmax(0, 1fr) 128px 164px;
  }

  .data-health-board__head > div:last-child {
    display: none;
  }

  .data-health-issue__actions {
    grid-column: 1 / -1;
    justify-content: flex-start;
  }
}

@media (max-width: 980px) {
  .data-health-board__head {
    display: none;
  }

  .data-health-issue__row {
    grid-template-columns: 1fr;
  }

  .data-health-issue__details-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .data-health-header__main,
  .data-health-header__stats,
  .data-health-filters,
  .data-health-pagination {
    align-items: stretch;
    flex-direction: column;
  }

  .data-health-header__stats {
    align-items: flex-start;
  }

  .data-health-header__divider {
    display: none;
  }

  .data-health-filters__search,
  .data-health-filters__field {
    min-width: 0;
  }

  .data-health-filters__actions {
    width: 100%;
  }

  .data-health-pagination__controls {
    justify-content: space-between;
    width: 100%;
  }
}
</style>
