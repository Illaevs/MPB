<template>
  <div class="audit-logs-view">
    <div class="audit-logs-toolbar">
      <h2 class="audit-logs-toolbar__title">Журнал действий</h2>
      <UiIconButton icon="fas fa-sync" label="Обновить" size="sm" @click="loadLogs(false)" />
    </div>

    <UiCard class="audit-logs-card">
      <div class="audit-logs-filters">
        <div class="audit-logs-filters__grid">
          <UiChipFilter
            v-model="filters.entityType"
            :options="entityChipOptions"
            placeholder="Все сущности"
            empty-icon="fas fa-layer-group"
          />
          <UiChipFilter
            v-model="filters.source"
            :options="sourceChipOptions"
            placeholder="Все записи"
            empty-icon="fas fa-list"
          />
          <UiInput v-model="filters.action" size="sm" placeholder="Действие" />
          <UiInput v-model="filters.entityId" size="sm" placeholder="ID объекта" />
          <UiInput v-model="filters.userId" size="sm" placeholder="ID пользователя" />
          <div class="audit-logs-filters__date-row">
            <UiInput v-model="filters.dateFrom" size="sm" type="date" />
            <UiInput v-model="filters.dateTo" size="sm" type="date" />
          </div>
        </div>
        <div class="audit-logs-filters__actions">
          <UiButton variant="primary" size="sm" @click="applyFilters">Применить</UiButton>
          <UiButton variant="secondary" size="sm" @click="resetFilters">Сбросить</UiButton>
        </div>
      </div>

      <div v-if="loading" class="audit-logs-loading">
        <SkeletonLoader v-for="i in 6" :key="`audit-skel-${i}`" height="60px" />
      </div>

      <UiEmptyState
        v-else-if="errorMessage"
        icon="fas fa-ban"
        title="Доступ ограничен"
        :description="errorMessage"
      />

      <UiEmptyState
        v-else-if="!logs.length"
        icon="fas fa-clipboard-list"
        title="Записей пока нет"
        description="События появятся после изменений в системе"
      />

      <div v-else class="audit-logs-table-wrap">
        <table class="audit-logs-table">
          <thead>
            <tr>
              <th style="width: 12%;">Сущность</th>
              <th style="width: 18%;">Событие</th>
              <th style="width: 18%;">Объект</th>
              <th style="width: 16%;">Пользователь</th>
              <th style="width: 22%;">Описание</th>
              <th style="width: 14%;">Дата</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in logs" :key="item.id" @click="openEntity(item)">
              <td>
                <UiBadge variant="neutral" size="sm" outline>{{ entityLabel(item.entity_type) }}</UiBadge>
              </td>
              <td>
                <div class="audit-logs-event">
                  <UiBadge :variant="sourceBadgeVariant(item.details)" size="sm">
                    {{ sourceLabel(item.details) }}
                  </UiBadge>
                  <span class="audit-logs-event__label">{{ actionLabel(item.action) }}</span>
                </div>
              </td>
              <td class="text-muted text-truncate" style="max-width: 220px;">
                <div class="fw-600 text-truncate">{{ objectLabel(item) }}</div>
                <div class="small text-muted">{{ shortId(item.entity_id) }}</div>
              </td>
              <td class="text-muted text-truncate" style="max-width: 200px;">
                <div class="fw-600 text-truncate">{{ userLabel(item.user_id) }}</div>
                <div class="small text-muted">{{ shortId(item.user_id) }}</div>
              </td>
              <td class="text-muted text-truncate" style="max-width: 320px;">
                {{ detailsPreview(item.details) }}
              </td>
              <td>{{ formatDateTime(item.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="hasMore && !loading && !errorMessage" class="audit-logs-more">
        <UiButton
          variant="outline"
          size="sm"
          icon-left="fas fa-spinner"
          :loading="loadingMore"
          @click="loadMore"
        >
          Показать еще
        </UiButton>
      </div>
    </UiCard>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api'
import SkeletonLoader from '../components/ui/SkeletonLoader.vue'
import { UiBadge, UiButton, UiCard, UiEmptyState, UiIconButton, UiInput, UiSelect } from '../components/ui'
import UiChipFilter from '../components/ui/UiChipFilter.vue'
import { useUsersStore } from '../stores/users'
import { formatDateTime as fmtDateTime } from '../utils/format'

export default {
  name: 'AuditLogs',
  components: { SkeletonLoader, UiBadge, UiButton, UiCard, UiEmptyState, UiIconButton, UiInput, UiSelect, UiChipFilter },
  setup() {
    const router = useRouter()
    const usersStore = useUsersStore()
    const logs = ref([])
    const loading = ref(false)
    const loadingMore = ref(false)
    const hasMore = ref(false)
    const errorMessage = ref('')
    const pageSize = 50
    const skip = ref(0)

    const filters = ref({
      entityType: '',
      source: 'event_log',
      action: '',
      entityId: '',
      userId: '',
      dateFrom: '',
      dateTo: ''
    })
    const userMap = ref({})

    const entityOptions = [
      { value: 'deal', label: 'Проекты' },
      { value: 'task', label: 'Задачи' },
      { value: 'document', label: 'Документы' },
      { value: 'outgoing', label: 'Исходящие' },
      { value: 'contract', label: 'Договоры' },
      { value: 'income_expense', label: 'ДДС' },
      { value: 'upload', label: 'Загрузки' },
      { value: 'notification', label: 'Уведомления' }
    ]
    const sourceOptions = [
      { value: 'event_log', label: 'События' },
      { value: 'snapshot', label: 'Снимки' },
      { value: '', label: 'Все записи' }
    ]

    // Цветовые опции для UiChipFilter
    const entityChipOptions = [
      { value: 'deal',           label: 'Проекты',      color: '#22c55e' },
      { value: 'task',           label: 'Задачи',       color: '#3b82f6' },
      { value: 'document',       label: 'Документы',    color: '#a855f7' },
      { value: 'outgoing',       label: 'Исходящие',    color: '#0ea5e9' },
      { value: 'contract',       label: 'Договоры',     color: '#f59e0b' },
      { value: 'income_expense', label: 'ДДС',          color: '#10b981' },
      { value: 'upload',         label: 'Загрузки',     color: '#6b7280' },
      { value: 'notification',   label: 'Уведомления',  color: '#ef4444' },
    ]
    const sourceChipOptions = [
      { value: 'event_log', label: 'События', color: '#3b82f6' },
      { value: 'snapshot',  label: 'Снимки',  color: '#f59e0b' },
    ]

    const entityLabel = (value) => {
      const map = {
        deal: 'Проект',
        task: 'Задача',
        document: 'Документ',
        outgoing: 'Исходящие',
        contract: 'Договор',
        income_expense: 'ДДС',
        upload: 'Загрузка',
        notification: 'Уведомление'
      }
      return map[value] || value || '—'
    }

    const actionLabel = (value) => {
      const map = {
        'deal.create': 'Создана сделка',
        'deal.update': 'Обновлена сделка',
        'task.create': 'Создана задача',
        'task.update': 'Обновлена задача',
        'task.assign': 'Назначена задача',
        'task.overdue': 'Просрочка задачи',
        'outgoing.create': 'Создан исходящий',
        'outgoing.version': 'Новая версия',
        'document.create': 'Создан документ',
        'document.update': 'Обновлен документ',
        'document.sent': 'Документ отправлен',
        'document.received': 'Документ получен',
        'document.overdue': 'Просрочка документа',
        'result_review.update': 'Согласование РР',
        'upload.error': 'Ошибка загрузки',
        snapshot: 'Снимок состояния'
      }
      return map[value] || value || '—'
    }

    const sourceLabel = (details) => {
      const source = details?.meta?.source
      if (source === 'snapshot') return 'Снимок'
      if (source === 'event_log') return 'Событие'
      return 'Лог'
    }

    const sourceBadgeVariant = (details) => {
      const source = details?.meta?.source
      if (source === 'snapshot') return 'warning'
      if (source === 'event_log') return 'info'
      return 'neutral'
    }

    const formatDateTime = (value) => {
      if (!value) return '-'
      return fmtDateTime(value, {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    const shortId = (value) => {
      if (!value) return '—'
      const text = String(value)
      return text.length > 8 ? `${text.slice(0, 8)}…` : text
    }

    const userLabel = (userId) => {
      if (!userId) return '—'
      return userMap.value[userId] || shortId(userId)
    }

    const snapshotTitle = (snap, fallback) => {
      if (!snap) return fallback
      return snap.title || snap.subject || snap.outgoing_number || snap.contract_number || snap.number || fallback
    }

    const objectLabel = (item) => {
      const details = item?.details || {}
      if (details.snapshot) return snapshotTitle(details.snapshot, entityLabel(item.entity_type))
      if (details.details) {
        const payload = details.details
        if (payload.snapshot) return snapshotTitle(payload.snapshot, entityLabel(item.entity_type))
        return (
          payload.task_title ||
          payload.deal_title ||
          payload.document_title ||
          payload.outgoing_number ||
          payload.file_name ||
          payload.contract_number ||
          entityLabel(item.entity_type)
        )
      }
      return entityLabel(item.entity_type)
    }

    const truncate = (value, max = 120) => {
      if (!value) return '—'
      return value.length > max ? `${value.slice(0, max)}…` : value
    }

    const snapshotDescription = (snap) => {
      if (!snap) return '—'
      if (snap.contract_number || snap.contract_date) {
        const num = snap.contract_number || '—'
        const date = snap.contract_date || '—'
        return truncate(`Договор: ${num}, дата ${date}`)
      }
      if (snap.outgoing_number || snap.subject) {
        const num = snap.outgoing_number ? `№ ${snap.outgoing_number}` : ''
        const subject = snap.subject || snap.title || 'Без темы'
        return truncate(`Исходящий ${num}: ${subject}`.trim())
      }
      if (snap.doc_type || snap.title) {
        const title = snap.title || 'Документ'
        const status = snap.status ? ` (${snap.status})` : ''
        return truncate(`${title}${status}`)
      }
      if (snap.direction || snap.amount) {
        const direction = snap.direction === 'expense' ? 'Расход' : 'Доход'
        const amount = snap.amount ? `, сумма ${snap.amount}` : ''
        const plan = snap.plan_date ? `, план ${snap.plan_date}` : ''
        return truncate(`${direction}${amount}${plan}`)
      }
      if (snap.title || snap.name) return truncate(snap.title || snap.name)
      return 'Снимок объекта'
    }

    const detailsPreview = (details) => {
      if (!details) return '—'
      if (details.diff) {
        const keys = Object.keys(details.diff)
        return truncate(`Изменено: ${keys.slice(0, 6).join(', ')}`)
      }
      if (details.details) {
        const payload = details.details
        if (payload.snapshot) return snapshotDescription(payload.snapshot)
        if (payload.task_title) return truncate(`Задача: ${payload.task_title}`)
        if (payload.deal_title) return truncate(`Проект: ${payload.deal_title}`)
        if (payload.document_title) return truncate(`Документ: ${payload.document_title}`)
        if (payload.outgoing_number) return truncate(`Исходящий: ${payload.outgoing_number}`)
        if (payload.error_message) return truncate(`Ошибка: ${payload.error_message}`)
        return truncate(typeof payload === 'string' ? payload : JSON.stringify(payload))
      }
      if (details.snapshot) return snapshotDescription(details.snapshot)
      return truncate(JSON.stringify(details))
    }

    const applySourceFilter = (items) => {
      if (!filters.value.source) return items
      return items.filter((item) => item.details?.meta?.source === filters.value.source)
    }

    const buildParams = () => {
      const params = { skip: skip.value, limit: pageSize }
      if (filters.value.entityType) params.entity_type = filters.value.entityType
      if (filters.value.action) params.action = filters.value.action
      if (filters.value.entityId) params.entity_id = filters.value.entityId
      if (filters.value.userId) params.user_id = filters.value.userId
      if (filters.value.dateFrom) params.date_from = new Date(`${filters.value.dateFrom}T00:00:00`).toISOString()
      if (filters.value.dateTo) params.date_to = new Date(`${filters.value.dateTo}T23:59:59`).toISOString()
      return params
    }

    const loadLogs = async (append) => {
      if (append) loadingMore.value = true
      else {
        loading.value = true
        skip.value = 0
      }
      errorMessage.value = ''
      try {
        const data = await api.audit.list(buildParams())
        const rawItems = data || []
        const nextItems = applySourceFilter(rawItems)
        logs.value = append ? [...logs.value, ...nextItems] : nextItems
        hasMore.value = rawItems.length === pageSize
        if (rawItems.length > 0) skip.value += rawItems.length
      } catch (error) {
        if (error?.response?.status === 403) errorMessage.value = 'Доступ только для администраторов.'
        else errorMessage.value = 'Не удалось загрузить журнал.'
        if (!append) logs.value = []
      } finally {
        loading.value = false
        loadingMore.value = false
      }
    }

    const loadMore = () => loadLogs(true)

    const applyFilters = () => loadLogs(false)

    const resetFilters = () => {
      filters.value = {
        entityType: '',
        source: 'event_log',
        action: '',
        entityId: '',
        userId: '',
        dateFrom: '',
        dateTo: ''
      }
      loadLogs(false)
    }

    const openEntity = (item) => {
      if (!item?.entity_id) return
      const entityType = item.entity_type
      if (entityType === 'deal') return router.push(`/projects/${item.entity_id}`)
      if (entityType === 'task') return router.push(`/tasks?task_id=${item.entity_id}`)
      if (entityType === 'document') return router.push('/document-registry')
      if (entityType === 'outgoing') return router.push('/outgoing-registry')
      if (entityType === 'contract') return router.push(`/contracts/${item.entity_id}`)
      if (entityType === 'income_expense') return router.push('/income-expense')
    }

    const loadUsers = async () => {
      try {
        await usersStore.ensureLoaded()
        const map = {}
        usersStore.items.forEach((user) => {
          if (user?.id) map[user.id] = user.full_name || user.email || shortId(user.id)
        })
        userMap.value = map
      } catch (error) {
        userMap.value = {}
      }
    }

    loadUsers()
    loadLogs(false)

    return {
      logs,
      loading,
      loadingMore,
      hasMore,
      errorMessage,
      filters,
      entityOptions,
      sourceOptions,
      entityChipOptions,
      sourceChipOptions,
      entityLabel,
      actionLabel,
      sourceLabel,
      sourceBadgeVariant,
      formatDateTime,
      detailsPreview,
      shortId,
      userLabel,
      objectLabel,
      loadLogs,
      loadMore,
      applyFilters,
      resetFilters,
      openEntity
    }
  }
}
</script>

<style scoped>
.audit-logs-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-2);
}

.audit-logs-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.audit-logs-toolbar__title {
  margin: 0;
  font-size: var(--text-2xl);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.audit-logs-card {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.audit-logs-filters {
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-border-subtle);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.audit-logs-filters__grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: var(--space-2);
}

.audit-logs-filters__date-row {
  display: flex;
  gap: var(--space-2);
}

.audit-logs-filters__actions {
  display: flex;
  gap: var(--space-2);
}

.audit-logs-loading {
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.audit-logs-table-wrap {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.audit-logs-table {
  width: 100%;
  border-collapse: collapse;
}

.audit-logs-table th {
  position: sticky;
  top: 0;
  background-color: var(--color-surface);
  z-index: 10;
  padding: var(--space-3);
  border-bottom: 1px solid var(--color-border-subtle);
  text-align: left;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.audit-logs-table td {
  padding: var(--space-3);
  border-bottom: 1px solid var(--color-border-subtle);
}

.audit-logs-table tbody tr {
  cursor: pointer;
}

.audit-logs-table tbody tr:hover {
  background: var(--color-surface-2);
}

.audit-logs-event {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.audit-logs-event__label {
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.audit-logs-more {
  padding: var(--space-3);
  text-align: center;
  border-top: 1px solid var(--color-border-subtle);
}

@media (max-width: 1200px) {
  .audit-logs-filters__grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .audit-logs-view {
    padding: var(--space-2);
  }

  .audit-logs-filters__grid {
    grid-template-columns: 1fr;
  }

  .audit-logs-filters__date-row {
    flex-direction: column;
  }

  .audit-logs-table {
    min-width: 980px;
  }
}
</style>
