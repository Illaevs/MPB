<template>
  <div class="approvals-page d-flex flex-column h-100">
    <div class="card toolbar-card flex-shrink-0">
      <div class="toolbar-row">
        <h2 class="m-0 toolbar-title">Мои согласования</h2>

        <div class="scope-tabs-ui" :class="{ 'scope-tabs-ui--urgent': pendingCountUrgent }">
          <UiTabs
            v-model="filters.scope"
            :tabs="scopeTabsUi"
            variant="segment"
            size="sm"
            @change="setScope"
          />
        </div>

        <div class="toolbar-filters">
          <div class="toolbar-search">
            <UiInput
              v-model="filters.search"
              type="search"
              size="sm"
              icon-left="fas fa-search"
              clearable
              placeholder="Поиск по объекту, шаблону, инициатору..."
              @update:modelValue="debouncedReload"
              @clear="loadInbox(true)"
            />
          </div>
          <div class="toolbar-select">
            <UiSelect
              v-model="filters.entityType"
              size="sm"
              :options="entityTypes"
              placeholder="Все модули"
              @change="loadInbox(true)"
            />
          </div>
        </div>

        <UiButton
          variant="secondary"
          size="sm"
          :loading="loadingInbox"
          icon-left="fas fa-rotate-right"
          @click="loadInbox(true)"
        >
          <span class="hide-md">Обновить</span>
        </UiButton>
      </div>
    </div>

    <section class="approvals-workspace flex-grow-1 overflow-hidden">
      <div class="approvals-feed">
        <div v-if="loadingInbox && !inbox.items.length" class="p-2 d-flex flex-column gap-2">
          <SkeletonLoader v-for="i in 8" :key="i" height="58px" />
        </div>

        <UiEmptyState
          v-else-if="!inbox.items.length"
          icon="fas fa-clipboard-check"
          title="Согласований по фильтру нет"
          description="Когда появятся активные маршруты, они соберутся здесь."
          size="sm"
          class="empty-state-card"
        />

        <div v-else class="approvals-list">
          <button
            v-for="item in inbox.items"
            :key="item.id"
            type="button"
            class="approvals-row"
            :class="{ 'is-selected': selectedInstanceId === item.id, 'is-mine': item.waiting_for_me }"
            @click="selectItem(item.id)"
          >
            <div class="row-leftrail" :class="`age-${stalenessKind(item)}`">
              <Tooltip :text="ageTooltip(item)">
                <span class="age-dot"></span>
              </Tooltip>
            </div>

            <div class="row-body">
              <div class="row-top">
                <span class="row-title">{{ item.entity_label || fallbackEntityLabel(item) }}</span>
                <span class="row-progress" :class="`progress-${item.status}`">
                  <span class="row-progress-bar">
                    <span class="row-progress-fill" :style="{ width: progressPct(item) + '%' }"></span>
                  </span>
                  <span class="row-progress-label">{{ item.progress_label }}</span>
                </span>
              </div>

              <div class="row-meta">
                <span class="row-module">{{ item.entity_type_label }}</span>
                <span class="row-sep">·</span>
                <span class="row-template">{{ item.template_name }}</span>
              </div>

              <div class="row-bottom">
                <Tooltip v-if="item.started_by_label" :text="`Инициатор: ${item.started_by_label}`">
                  <span class="row-author">
                    <UiAvatar
                      :name="item.started_by_label"
                      :src="resolveAvatar(item.started_by_avatar_url, item.started_by)"
                      size="xs"
                    />
                    <span class="row-author-name">{{ item.started_by_label }}</span>
                  </span>
                </Tooltip>
                <span class="row-stage text-muted">{{ item.current_stage_label }}</span>
                <span class="row-time text-muted">{{ relativeTime(item.started_at) }}</span>
                <UiBadge v-if="item.waiting_for_me" variant="primary" size="sm" pill>Ждёт меня</UiBadge>
              </div>
            </div>
          </button>
        </div>

        <div v-if="canLoadMore" class="load-more-row">
          <UiButton
            variant="secondary"
            size="sm"
            :loading="loadingInbox"
            icon-left="fas fa-chevron-down"
            @click="loadMore"
          >
            Показать ещё ({{ inbox.total - inbox.items.length }})
          </UiButton>
        </div>
      </div>

      <aside class="approvals-detail">
        <div v-if="loadingDetail" class="p-3 d-flex flex-column gap-2">
          <SkeletonLoader height="40px" />
          <SkeletonLoader height="60px" />
          <SkeletonLoader height="120px" />
          <SkeletonLoader height="180px" />
        </div>

        <UiEmptyState
          v-else-if="!selectedSummary"
          icon="fas fa-arrow-left"
          title="Выберите согласование слева"
          description="Здесь появятся стадия, маршрут и быстрые действия."
          size="sm"
          class="empty-state-card empty-detail"
        />

        <template v-else>
          <header class="detail-header">
            <div class="detail-title-block">
              <div class="detail-eyebrow">
                <span class="detail-module">{{ selectedSummary.entity_type_label }}</span>
                <UiBadge :variant="statusVariant(selectedSummary.status)" size="sm" pill>
                  {{ statusLabel(selectedSummary.status) }}
                </UiBadge>
              </div>
              <h3 class="detail-title">{{ selectedSummary.entity_label || fallbackEntityLabel(selectedSummary) }}</h3>
              <div class="detail-template text-muted small">{{ selectedSummary.template_name }}</div>
            </div>
            <UiIconButton
              v-if="selectedSummary.action_url"
              class="detail-open-btn"
              icon="fas fa-arrow-up-right-from-square"
              label="Открыть объект"
              @click="openEntity(selectedSummary)"
            />
          </header>

          <div class="detail-meta-row">
            <Tooltip v-if="selectedSummary.started_by_label" :text="`Инициатор: ${selectedSummary.started_by_label}`">
              <span class="detail-author">
                <UiAvatar
                  :name="selectedSummary.started_by_label"
                  :src="resolveAvatar(selectedSummary.started_by_avatar_url, selectedSummary.started_by)"
                  size="sm"
                />
                <span>{{ selectedSummary.started_by_label }}</span>
              </span>
            </Tooltip>
            <span v-if="selectedSummary.started_at" class="text-muted small">
              <i class="fas fa-clock mr-1"></i>{{ relativeTime(selectedSummary.started_at) }}
              <span class="text-muted ml-1">· {{ formatDateTime(selectedSummary.started_at) }}</span>
            </span>
            <span class="detail-progress-mini" :class="`progress-${selectedSummary.status}`">
              <span class="row-progress-bar">
                <span class="row-progress-fill" :style="{ width: progressPct(selectedSummary) + '%' }"></span>
              </span>
              <span>{{ selectedSummary.progress_label }} · {{ selectedSummary.current_stage_label }}</span>
            </span>
          </div>

          <div v-if="canAct" class="action-bar">
            <transition name="slide">
              <div v-if="actionMode" class="action-form">
                <UiTextarea
                  ref="actionTextarea"
                  v-model.trim="actionComment"
                  rows="3"
                  :placeholder="actionMode === 'reject'
                    ? 'Опишите причину отклонения (обязательно)'
                    : 'Комментарий (необязательно)'"
                />
                <div v-if="actionMode === 'reject' && !actionComment" class="action-error">
                  Комментарий обязателен при отклонении.
                </div>
                <div class="action-form-buttons">
                  <UiButton variant="secondary" size="sm" @click="cancelAction">Отмена</UiButton>
                  <UiButton
                    v-if="actionMode === 'approve'"
                    variant="success"
                    size="sm"
                    icon-left="fas fa-check"
                    :loading="acting"
                    :disabled="acting"
                    @click="approveSelected"
                  >
                    Согласовать
                  </UiButton>
                  <UiButton
                    v-if="actionMode === 'reject'"
                    variant="danger"
                    size="sm"
                    icon-left="fas fa-times"
                    :loading="acting"
                    :disabled="acting || !actionComment.trim()"
                    @click="rejectSelected"
                  >
                    Отклонить
                  </UiButton>
                </div>
              </div>
            </transition>

            <div v-if="!actionMode" class="action-buttons">
              <UiButton variant="success" size="sm" icon-left="fas fa-check" @click="startAction('approve')">
                Согласовать
              </UiButton>
              <UiButton variant="danger" size="sm" icon-left="fas fa-times" @click="startAction('reject')">
                Отклонить
              </UiButton>
            </div>
          </div>

          <section class="timeline-section">
            <h4 class="section-head">
              <i class="fas fa-route mr-1"></i>Маршрут согласования
              <span class="text-muted small">{{ selectedSteps.length }} шагов</span>
            </h4>

            <ol class="timeline">
              <li
                v-for="step in selectedSteps"
                :key="step.id"
                class="tl-step"
                :class="`tl-${step.status}`"
              >
                <div class="tl-rail">
                  <span class="tl-dot">
                    <i v-if="step.status === 'approved'" class="fas fa-check"></i>
                    <i v-else-if="step.status === 'rejected'" class="fas fa-times"></i>
                    <span v-else>{{ step.step_order }}</span>
                  </span>
                </div>
                <div class="tl-content">
                  <div class="tl-head">
                    <span class="tl-title">{{ step.title }}</span>
                    <UiBadge :variant="statusVariant(step.status)" size="sm" pill>
                      {{ statusLabel(step.status) }}
                    </UiBadge>
                  </div>
                  <div class="tl-meta text-muted small">
                    <span>
                      <i class="fas fa-user-tag mr-1"></i>{{ step.assignee_label || 'Без исполнителя' }}
                    </span>
                    <span v-if="step.acted_at" class="ml-2">
                      · {{ relativeTime(step.acted_at) }}
                    </span>
                  </div>
                  <p v-if="step.description" class="tl-description text-muted small">{{ step.description }}</p>
                  <div v-if="step.comment" class="tl-comment">
                    <UiAvatar :name="step.acted_by_label" size="sm" />
                    <div class="tl-comment-body">
                      <div class="tl-comment-head">
                        <b>{{ step.acted_by_label || 'Аноним' }}</b>
                        <span v-if="step.acted_at" class="text-muted small ml-2">{{ formatDateTime(step.acted_at) }}</span>
                      </div>
                      <div>{{ step.comment }}</div>
                    </div>
                  </div>
                </div>
              </li>

              <li
                v-for="entry in extraActions"
                :key="`a-${entry.id}`"
                class="tl-step tl-system"
              >
                <div class="tl-rail">
                  <span class="tl-dot">
                    <i class="fas" :class="actionIcon(entry.action)"></i>
                  </span>
                </div>
                <div class="tl-content">
                  <div class="tl-head">
                    <span class="tl-title">{{ actionLabel(entry.action) }}</span>
                    <span v-if="entry.created_at" class="text-muted small">{{ formatDateTime(entry.created_at) }}</span>
                  </div>
                  <div class="tl-meta text-muted small">
                    <i class="fas fa-user mr-1"></i>{{ entry.actor_label || 'Система' }}
                  </div>
                  <p v-if="entry.comment" class="tl-description">{{ entry.comment }}</p>
                </div>
              </li>
            </ol>
          </section>
        </template>
      </aside>
    </section>
  </div>
</template>

<script>
import { computed, defineComponent, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../services/api'
import { useAuthStore } from '../stores/auth'
import { useToast } from '../composables/useToast'
import SkeletonLoader from '../components/ui/SkeletonLoader.vue'
import Tooltip from '../components/ui/Tooltip.vue'
import {
  UiAvatar,
  UiBadge,
  UiButton,
  UiEmptyState,
  UiIconButton,
  UiInput,
  UiSelect,
  UiTabs,
  UiTextarea,
} from '../components/ui'
import { normalizeAvatarUrl } from '../utils/avatar'

const ENTITY_TYPES = [
  { value: 'outgoing_document', label: 'Исходящие документы' },
  { value: 'contract', label: 'Договоры' },
  { value: 'deal', label: 'Сделки' },
  { value: 'task', label: 'Задачи' },
  { value: 'income_expense_entry', label: 'Записи ДДС' },
  { value: 'treasury_transaction', label: 'Казначейство' },
]

const PAGE_LIMIT = 50

export default defineComponent({
  name: 'MyApprovals',
  components: {
    SkeletonLoader,
    Tooltip,
    UiAvatar,
    UiBadge,
    UiButton,
    UiEmptyState,
    UiIconButton,
    UiInput,
    UiSelect,
    UiTabs,
    UiTextarea,
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const authStore = useAuthStore()
    const { success: toastSuccess, error: toastError } = useToast()

    const filters = ref({
      scope: 'pending_me',
      entityType: '',
      search: '',
    })
    const inbox = ref({
      stats: { pending_me: 0, active: 0, history: 0, total_visible: 0 },
      items: [],
      total: 0,
      offset: 0,
      limit: PAGE_LIMIT,
    })
    const loadingInbox = ref(false)
    const loadingDetail = ref(false)
    const acting = ref(false)
    const selectedInstanceId = ref('')
    const selectedInstance = ref(null)
    const actionComment = ref('')
    const actionMode = ref('')
    const actionTextarea = ref(null)
    let searchTimer = null

    const entityTypes = ENTITY_TYPES

    const scopeTabs = computed(() => [
      { scope: 'pending_me', label: 'Ждут меня', value: inbox.value.stats.pending_me || 0 },
      { scope: 'active', label: 'Активные', value: inbox.value.stats.active || 0 },
      { scope: 'history', label: 'История', value: inbox.value.stats.history || 0 },
      { scope: 'all', label: 'Все', value: inbox.value.stats.total_visible || 0 },
    ])
    const scopeTabsUi = computed(() => scopeTabs.value.map((card) => ({
      value: card.scope,
      label: card.label,
      count: card.value,
    })))
    const pendingCountUrgent = computed(() => (inbox.value.stats.pending_me || 0) > 0)

    const selectedSummary = computed(() => inbox.value.items.find((item) => item.id === selectedInstanceId.value) || null)
    const selectedSteps = computed(() => selectedInstance.value?.steps || [])
    const currentStep = computed(() => selectedSteps.value.find((item) => item.status === 'pending') || null)
    const currentUserId = computed(() => String(authStore.user?.id || ''))
    const currentRoleId = computed(() => String(authStore.user?.role_id || ''))

    const stepActions = new Set(['approved', 'rejected'])
    const extraActions = computed(() => {
      const list = selectedInstance.value?.actions || []
      return list.filter((action) => !stepActions.has(action.action) || !action.instance_step_id)
    })

    const canAct = computed(() => {
      if (!currentStep.value) return false
      if (currentStep.value.assignee_type === 'user') {
        return String(currentStep.value.assignee_user_id || '') === currentUserId.value
      }
      if (currentStep.value.assignee_type === 'role') {
        return String(currentStep.value.assignee_role_id || '') === currentRoleId.value
      }
      return false
    })

    const canLoadMore = computed(() => inbox.value.items.length < (inbox.value.total || 0))

    const formatDateTime = (value) => {
      if (!value) return '—'
      try {
        return new Date(value).toLocaleString('ru-RU', {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        })
      } catch (error) {
        return value
      }
    }

    const relativeTime = (value) => {
      if (!value) return ''
      const date = new Date(value)
      if (Number.isNaN(date.getTime())) return ''
      const diffMs = Date.now() - date.getTime()
      const diffSec = Math.round(diffMs / 1000)
      const abs = Math.abs(diffSec)
      const sign = diffSec >= 0
      if (abs < 60) return sign ? 'только что' : 'через несколько секунд'
      const diffMin = Math.round(diffSec / 60)
      if (Math.abs(diffMin) < 60) return sign ? `${Math.abs(diffMin)} мин. назад` : `через ${Math.abs(diffMin)} мин.`
      const diffHour = Math.round(diffMin / 60)
      if (Math.abs(diffHour) < 24) return sign ? `${Math.abs(diffHour)} ч. назад` : `через ${Math.abs(diffHour)} ч.`
      const diffDay = Math.round(diffHour / 24)
      if (Math.abs(diffDay) < 30) return sign ? `${Math.abs(diffDay)} дн. назад` : `через ${Math.abs(diffDay)} дн.`
      const diffMon = Math.round(diffDay / 30)
      if (Math.abs(diffMon) < 12) return sign ? `${Math.abs(diffMon)} мес. назад` : `через ${Math.abs(diffMon)} мес.`
      const diffYear = Math.round(diffMon / 12)
      return sign ? `${Math.abs(diffYear)} г. назад` : `через ${Math.abs(diffYear)} г.`
    }

    const daysSince = (value) => {
      if (!value) return null
      const date = new Date(value)
      if (Number.isNaN(date.getTime())) return null
      return (Date.now() - date.getTime()) / (1000 * 60 * 60 * 24)
    }

    const stalenessKind = (item) => {
      if (item.status !== 'pending') return 'final'
      const days = daysSince(item.started_at)
      if (days === null) return 'none'
      if (days < 1) return 'fresh'
      if (days < 3) return 'hanging'
      if (days < 7) return 'warning'
      return 'overdue'
    }

    const ageTooltip = (item) => {
      const created = item.started_at ? formatDateTime(item.started_at) : '—'
      if (item.status !== 'pending') {
        return `Завершено: ${item.completed_at ? formatDateTime(item.completed_at) : '—'}\nЗапущено: ${created}`
      }
      const kind = stalenessKind(item)
      let line = ''
      if (kind === 'overdue') line = '\nПросрочено (>7 дн.) — требует срочного внимания'
      else if (kind === 'warning') line = '\nЗалежалось (3–7 дн.)'
      else if (kind === 'hanging') line = '\nВисит 1–3 дня'
      else if (kind === 'fresh') line = '\nСвежее (<1 дн.)'
      return `Запущено: ${created}${line}`
    }

    const statusLabel = (status) => {
      switch (status) {
        case 'pending': return 'На согласовании'
        case 'approved': return 'Согласовано'
        case 'rejected': return 'Отклонено'
        case 'waiting': return 'Ожидает'
        case 'cancelled': return 'Отменено'
        default: return status || 'Неизвестно'
      }
    }

    const statusVariant = (status) => {
      switch (status) {
        case 'approved': return 'success'
        case 'rejected': return 'danger'
        case 'pending': return 'warning'
        case 'waiting': return 'info'
        case 'cancelled': return 'neutral'
        default: return 'neutral'
      }
    }

    const actionIcon = (action) => {
      switch (action) {
        case 'started': return 'fa-play'
        case 'approved': return 'fa-check'
        case 'rejected': return 'fa-times'
        case 'cancelled': return 'fa-ban'
        default: return 'fa-circle-info'
      }
    }

    const actionLabel = (action) => {
      switch (action) {
        case 'started': return 'Запуск маршрута'
        case 'approved': return 'Согласовано'
        case 'rejected': return 'Отклонено'
        case 'cancelled': return 'Отменено'
        default: return action || 'Действие'
      }
    }

    const fallbackEntityLabel = (item) => `${item.entity_type_label} #${(item.entity_id || '').slice(0, 8)}`
    const resolveAvatar = (url, userId) => normalizeAvatarUrl(url, userId)

    const progressPct = (item) => {
      const total = item.total_steps || 0
      if (!total) return 0
      const done = item.completed_steps || 0
      if (item.status === 'approved') return 100
      if (item.status === 'rejected') {
        const order = item.current_step_order || done
        return Math.min(100, Math.round((order / total) * 100))
      }
      return Math.min(100, Math.round((done / total) * 100))
    }

    const loadInbox = async (reset = true, silent = false) => {
      if (!silent) loadingInbox.value = true
      try {
        const effectiveLimit = (silent && reset && inbox.value.items.length > PAGE_LIMIT)
          ? inbox.value.items.length
          : PAGE_LIMIT
        const data = await api.approvals.inbox({
          scope: filters.value.scope,
          entity_type: filters.value.entityType || undefined,
          search: filters.value.search || undefined,
          limit: effectiveLimit,
          offset: reset ? 0 : inbox.value.items.length,
        })

        if (reset) {
          inbox.value = {
            stats: data?.stats || { pending_me: 0, active: 0, history: 0, total_visible: 0 },
            items: data?.items || [],
            total: data?.total ?? (data?.items?.length || 0),
            offset: data?.offset ?? 0,
            limit: data?.limit ?? effectiveLimit,
          }
        } else {
          inbox.value.items = [...inbox.value.items, ...(data?.items || [])]
          inbox.value.total = data?.total ?? inbox.value.total
        }

        const requestedId = String(route.query.approvalInstance || '')
        const stillVisible = inbox.value.items.some((item) => item.id === selectedInstanceId.value)
        const requestedVisible = requestedId && inbox.value.items.some((item) => item.id === requestedId)
        const nextId = requestedVisible
          ? requestedId
          : stillVisible
            ? selectedInstanceId.value
            : (inbox.value.items[0]?.id || '')

        if (nextId) {
          await selectItem(nextId)
        } else {
          selectedInstanceId.value = ''
          selectedInstance.value = null
        }
      } catch (error) {
        console.error('Approvals inbox load error:', error)
        if (!silent) toastError(error?.response?.data?.detail || 'Не удалось загрузить мои согласования')
      } finally {
        if (!silent) loadingInbox.value = false
      }
    }

    const loadMore = () => loadInbox(false)

    const loadInstance = async (instanceId) => {
      if (!instanceId) {
        selectedInstance.value = null
        return
      }
      loadingDetail.value = true
      try {
        const data = await api.approvals.getInstance(instanceId)
        selectedInstance.value = data || null
      } catch (error) {
        console.error('Approval instance load error:', error)
        selectedInstance.value = null
        toastError(error?.response?.data?.detail || 'Не удалось открыть детали согласования')
      } finally {
        loadingDetail.value = false
      }
    }

    const selectItem = async (instanceId) => {
      if (!instanceId) return
      if (selectedInstanceId.value === instanceId && selectedInstance.value) return
      selectedInstanceId.value = instanceId
      cancelAction()
      await loadInstance(instanceId)
    }

    const setScope = async (scope) => {
      filters.value.scope = scope
      await loadInbox(true)
    }

    const debouncedReload = () => {
      if (searchTimer) clearTimeout(searchTimer)
      searchTimer = setTimeout(() => loadInbox(true), 250)
    }

    const openEntity = (item) => {
      if (!item?.action_url) return
      router.push(item.action_url)
    }

    const startAction = (mode) => {
      actionMode.value = mode
      actionComment.value = ''
      nextTick(() => actionTextarea.value?.$el?.querySelector('textarea')?.focus())
    }

    const cancelAction = () => {
      actionMode.value = ''
      actionComment.value = ''
    }

    const approveSelected = async () => {
      if (!selectedInstanceId.value) return
      acting.value = true
      try {
        await api.approvals.approveInstance(selectedInstanceId.value, {
          comment: actionComment.value || null,
        })
        toastSuccess('Согласовано')
        cancelAction()
        await loadInbox(true)
      } catch (error) {
        console.error('Inbox approve error:', error)
        toastError(error?.response?.data?.detail || 'Не удалось согласовать шаг')
      } finally {
        acting.value = false
      }
    }

    const rejectSelected = async () => {
      if (!selectedInstanceId.value) return
      if (!actionComment.value.trim()) {
        toastError('Добавьте комментарий к отклонению')
        return
      }
      acting.value = true
      try {
        await api.approvals.rejectInstance(selectedInstanceId.value, {
          comment: actionComment.value,
        })
        toastSuccess('Отклонено')
        cancelAction()
        await loadInbox(true)
      } catch (error) {
        console.error('Inbox reject error:', error)
        toastError(error?.response?.data?.detail || 'Не удалось отклонить согласование')
      } finally {
        acting.value = false
      }
    }

    watch(() => route.query.approvalInstance, async (value) => {
      const nextId = String(value || '')
      if (nextId && nextId !== selectedInstanceId.value) {
        await selectItem(nextId)
      }
    })

    const POLL_MS = 45000
    let pollTimer = null
    let pollInFlight = false

    const pollInbox = async () => {
      if (typeof document !== 'undefined' && document.hidden) return
      if (pollInFlight || acting.value || loadingInbox.value) return
      pollInFlight = true
      try {
        await loadInbox(true, true)
      } finally {
        pollInFlight = false
      }
    }

    const stopPolling = () => {
      if (pollTimer) {
        clearInterval(pollTimer)
        pollTimer = null
      }
    }

    const startPolling = () => {
      stopPolling()
      pollTimer = setInterval(pollInbox, POLL_MS)
    }

    const onVisibilityChange = () => {
      if (typeof document !== 'undefined' && !document.hidden) pollInbox()
    }

    onMounted(() => {
      loadInbox(true)
      startPolling()
      if (typeof document !== 'undefined') {
        document.addEventListener('visibilitychange', onVisibilityChange)
      }
    })
    onBeforeUnmount(() => {
      if (searchTimer) clearTimeout(searchTimer)
      stopPolling()
      if (typeof document !== 'undefined') {
        document.removeEventListener('visibilitychange', onVisibilityChange)
      }
    })

    return {
      filters,
      inbox,
      entityTypes,
      scopeTabsUi,
      pendingCountUrgent,
      loadingInbox,
      loadingDetail,
      acting,
      selectedInstanceId,
      selectedInstance,
      selectedSummary,
      selectedSteps,
      currentStep,
      canAct,
      canLoadMore,
      actionComment,
      actionMode,
      actionTextarea,
      extraActions,
      formatDateTime,
      relativeTime,
      stalenessKind,
      ageTooltip,
      statusLabel,
      statusVariant,
      actionLabel,
      actionIcon,
      fallbackEntityLabel,
      resolveAvatar,
      progressPct,
      loadInbox,
      loadMore,
      setScope,
      debouncedReload,
      selectItem,
      openEntity,
      startAction,
      cancelAction,
      approveSelected,
      rejectSelected,
    }
  },
})
</script>

<style scoped>
/* ── Tasks reference standard: white card chrome, soft shadow, light
   border, generous radius. Tuned for max info density / compactness. ── */
.approvals-page {
  --apr-card-bg: rgba(255, 255, 255, 0.97);
  --apr-card-border: rgba(216, 224, 240, 0.92);
  --apr-card-shadow: 0 18px 42px rgba(15, 23, 42, 0.06);
  --apr-radius: 20px;
  --apr-ink: #0a1629;
  --apr-muted: #7d8592;
  --apr-soft: #f6f8fb;
  padding: 12px;
  gap: 0;
}

/* One unified card: toolbar = header, workspace = body (Tasks pattern) */
.toolbar-card {
  padding: 0 !important;
  background: var(--apr-card-bg) !important;
  border: 1px solid var(--apr-card-border) !important;
  border-bottom: 1px solid var(--apr-card-border) !important;
  border-radius: var(--apr-radius) var(--apr-radius) 0 0 !important;
  box-shadow: none !important;
  margin: 0 !important;
}

.toolbar-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 10px 14px;
}

.toolbar-title {
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--apr-ink);
  white-space: nowrap;
  margin-right: 2px;
}

.scope-tabs-ui {
  flex-shrink: 0;
}

.scope-tabs-ui :deep(.ui-tabs--segment) {
  background: #f3f5f8;
  border: 1px solid rgba(228, 228, 228, 0.95);
  border-radius: 12px;
  padding: 3px;
}

.scope-tabs-ui :deep(.ui-tabs__tab) {
  font-weight: 700;
  border-radius: 9px;
}

.scope-tabs-ui :deep(.ui-tabs__tab.is-active) {
  background: #fff;
  color: var(--apr-ink);
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
}

.scope-tabs-ui.scope-tabs-ui--urgent :deep(.ui-tabs__tab:first-child .ui-tabs__count) {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.toolbar-filters {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1 1 auto;
  min-width: 0;
}

.toolbar-search {
  flex: 1 1 300px;
  min-width: 180px;
}

.toolbar-select {
  flex: 0 1 190px;
  min-width: 150px;
}

.hide-md {
  display: inline;
}

.approvals-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) 440px;
  gap: 0;
  min-height: 0;
  margin-top: 0;
  background: var(--apr-card-bg);
  border: 1px solid var(--apr-card-border);
  border-top: 0;
  border-radius: 0 0 var(--apr-radius) var(--apr-radius);
  box-shadow: var(--apr-card-shadow);
  overflow: hidden;
}

.approvals-feed,
.approvals-detail {
  background: transparent;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.approvals-feed {
  border-right: 1px solid var(--apr-card-border);
}

.approvals-detail {
  padding: 14px 16px;
  gap: 12px;
  overflow-y: auto;
}

.empty-state-card {
  height: 100%;
  min-height: 220px;
}

.approvals-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 8px;
  overflow-y: auto;
  flex: 1 1 auto;
}

.approvals-row {
  width: 100%;
  text-align: left;
  display: flex;
  gap: 10px;
  border: 1px solid transparent;
  border-radius: 12px;
  background: var(--apr-soft);
  padding: 8px 11px;
  cursor: pointer;
  transition: background-color var(--dur-fast) ease, box-shadow var(--dur-fast) ease;
}

.approvals-row:hover {
  background: #eef2f8;
}

.approvals-row:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

.approvals-row.is-selected {
  background: var(--color-primary-soft);
  border-color: rgba(63, 140, 255, 0.35);
}

.approvals-row.is-mine {
  box-shadow: inset 3px 0 0 var(--color-primary);
}

.row-leftrail {
  display: flex;
  align-items: flex-start;
  padding-top: 3px;
}

.age-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-border-strong);
  display: inline-block;
}

.age-fresh .age-dot { background: var(--color-success); }
.age-hanging .age-dot { background: var(--color-info); }
.age-warning .age-dot { background: var(--color-warning); }
.age-overdue .age-dot {
  background: var(--color-danger);
  box-shadow: 0 0 0 3px var(--color-danger-soft);
}
.age-final .age-dot,
.age-none .age-dot { background: var(--color-text-subtle); }

.row-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.row-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-2);
}

.row-title {
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--apr-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.row-progress,
.detail-progress-mini {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.row-progress-bar {
  width: 56px;
  height: 4px;
  border-radius: var(--radius-pill);
  background: var(--color-border-subtle);
  overflow: hidden;
  display: inline-block;
}

.detail-progress-mini .row-progress-bar {
  width: 80px;
}

.row-progress-fill {
  display: block;
  height: 100%;
  background: var(--color-primary);
  border-radius: inherit;
}

.row-progress.progress-approved .row-progress-fill,
.detail-progress-mini.progress-approved .row-progress-fill {
  background: var(--color-success);
}

.row-progress.progress-rejected .row-progress-fill,
.detail-progress-mini.progress-rejected .row-progress-fill {
  background: var(--color-danger);
}

.row-progress.progress-cancelled .row-progress-fill,
.detail-progress-mini.progress-cancelled .row-progress-fill {
  background: var(--color-text-subtle);
}

.row-progress-label {
  font-size: 0.72rem;
  font-family: var(--font-mono);
  font-weight: 700;
  color: var(--apr-muted);
}

.row-meta {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: 0.8rem;
  color: var(--apr-muted);
  font-weight: 600;
  min-width: 0;
}

.row-module {
  font-weight: 700;
  color: #5f6b7c;
}

.row-template {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.row-sep {
  opacity: 0.5;
}

.row-bottom {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: nowrap;
  min-width: 0;
  overflow: hidden;
  font-size: 0.8rem;
  color: var(--apr-muted);
}

.row-bottom > .row-author,
.row-bottom > .row-time,
.row-bottom > :deep(.ui-badge) {
  flex-shrink: 0;
}

.row-author,
.detail-author {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.row-author-name {
  color: #5f6b7c;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 130px;
}

.row-stage {
  flex: 1;
  min-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.load-more-row {
  padding: 10px;
  text-align: center;
  border-top: 1px solid var(--apr-card-border);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-2);
}

.detail-title-block {
  flex: 1;
  min-width: 0;
}

.detail-eyebrow {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-1);
}

.detail-module {
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--apr-muted);
}

.detail-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--apr-ink);
}

.detail-template {
  margin-top: 1px;
}

.detail-meta-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
  padding: 8px 12px;
  border-radius: 12px;
  background: var(--apr-soft);
  border: 1px solid var(--apr-card-border);
  font-size: 0.8rem;
}

.action-bar {
  background: var(--apr-soft);
  border: 1px solid var(--apr-card-border);
  border-radius: 12px;
  padding: 10px 12px;
}

.action-buttons {
  display: flex;
  gap: var(--space-2);
}

.action-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.action-error {
  font-size: var(--text-xs);
  color: var(--color-danger);
}

.action-form-buttons {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
}

.slide-enter-active,
.slide-leave-active {
  transition: all var(--dur-fast) ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.timeline-section {
  padding-top: 2px;
}

.section-head {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin: 0 0 var(--space-2);
  font-size: 0.74rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--apr-ink);
}

.section-head .text-muted {
  margin-left: auto;
  font-weight: var(--fw-medium);
  text-transform: none;
  letter-spacing: normal;
}

.timeline {
  list-style: none;
  margin: 0;
  padding: 0;
  position: relative;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 11px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: var(--color-border-subtle);
}

.tl-step {
  display: grid;
  grid-template-columns: 22px 1fr;
  gap: var(--space-2);
  padding: 6px 0;
  position: relative;
}

.tl-rail {
  position: relative;
  z-index: 1;
}

.tl-dot {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--color-surface-3);
  color: var(--color-text-muted);
  font-size: 0.7rem;
  font-weight: 800;
  border: 2px solid #fff;
}

.tl-pending .tl-dot { background: var(--color-warning); color: #fff; }
.tl-approved .tl-dot { background: var(--color-success); color: #fff; }
.tl-rejected .tl-dot { background: var(--color-danger); color: #fff; }
.tl-system .tl-dot { background: var(--color-primary); color: #fff; }

.tl-content {
  padding-top: 1px;
}

.tl-head {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.tl-title {
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--apr-ink);
}

.tl-meta {
  margin-top: 2px;
}

.tl-description {
  margin: var(--space-1) 0 0;
}

.tl-comment {
  margin-top: 6px;
  padding: 8px 10px;
  border-radius: 10px;
  background: var(--apr-soft);
  border: 1px solid var(--apr-card-border);
  display: flex;
  gap: var(--space-2);
  font-size: 0.82rem;
}

.tl-comment-body {
  flex: 1;
  min-width: 0;
}

.tl-comment-head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-1);
  margin-bottom: 2px;
  font-size: var(--text-sm);
}

@media (max-width: 1280px) {
  .approvals-workspace {
    grid-template-columns: minmax(0, 1fr) 400px;
  }
}

@media (max-width: 1100px) {
  .hide-md {
    display: none;
  }
}

@media (max-width: 980px) {
  .approvals-workspace {
    grid-template-columns: 1fr;
  }

  .approvals-feed {
    border-right: 0;
    border-bottom: 1px solid var(--apr-card-border);
  }

  .approvals-detail {
    max-height: 70vh;
  }
}

@media (max-width: 640px) {
  .toolbar-search,
  .toolbar-select {
    flex-basis: 100%;
    min-width: 0;
  }

  .scope-tabs-ui {
    width: 100%;
    overflow-x: auto;
  }

  .action-buttons,
  .action-form-buttons {
    width: 100%;
    flex-direction: column;
  }
}
</style>
