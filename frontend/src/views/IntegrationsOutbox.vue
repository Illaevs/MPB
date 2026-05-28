<template>
  <div class="event-outbox-view p-3">
    <div class="d-flex justify-between align-center mb-3">
      <h2 class="m-0">Outbox событий</h2>
      <div class="d-flex gap-2 align-center">
        <select v-model="statusFilter" class="form-control form-control-sm" @change="load">
          <option value="">Все статусы</option>
          <option value="pending">pending</option>
          <option value="delivered">delivered</option>
          <option value="failed">failed</option>
          <option value="dlq">DLQ</option>
        </select>
        <input
          v-model.trim="eventTypeFilter"
          type="text"
          class="form-control form-control-sm"
          placeholder="event_type (например deal.after_create)"
          style="min-width: 280px;"
          @keyup.enter="load"
        />
        <button class="btn btn-sm btn-primary" :disabled="loading" @click="load">
          <i v-if="loading" class="fas fa-spinner fa-spin mr-1"></i>
          <i v-else class="fas fa-sync mr-1"></i>
          Обновить
        </button>
      </div>
    </div>

    <!-- V1.5: summary-карточки. Дают мгновенное «здоровье шины» —
         если pending копится или DLQ ненулевой → worker лежит / consumer молчит. -->
    <div v-if="stats" class="stats-grid mb-3">
      <button
        v-for="card in statsCards"
        :key="card.key"
        type="button"
        class="stat-card"
        :class="[card.tone, { active: statusFilter === card.filter }]"
        :title="card.label + ': кликни чтобы отфильтровать таблицу'"
        @click="quickFilter(card.filter)"
      >
        <div class="stat-card__value">{{ card.value }}</div>
        <div class="stat-card__label">{{ card.label }}</div>
      </button>
    </div>

    <div v-if="loading && !items.length" class="text-muted">Загрузка…</div>
    <div v-else-if="!items.length" class="text-muted text-center py-5">Нет событий по фильтрам</div>
    <div v-else class="table-container card overflow-auto">
      <table class="table table-sm">
        <thead>
          <tr>
            <th>Время</th>
            <th>Событие</th>
            <th>Сущность</th>
            <th>Статус</th>
            <th class="text-right">Попыток</th>
            <th>Ошибка</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in items" :key="row.id">
            <td class="text-muted small">{{ formatDateTime(row.created_at) }}</td>
            <td class="fw-500 font-monospace">{{ row.event_type }}</td>
            <td class="font-monospace small">
              {{ row.entity_type }}
              <span class="text-muted">/</span>
              <span class="text-muted">{{ shortId(row.entity_id) }}</span>
            </td>
            <td>
              <span class="badge badge-sm" :class="statusClass(row.status)">{{ row.status }}</span>
              <span v-if="row.delivered_at" class="text-muted small ml-1">
                {{ formatTime(row.delivered_at) }}
              </span>
            </td>
            <td class="text-right">{{ row.attempt_count }}</td>
            <td class="small text-danger" :title="row.last_error">{{ truncate(row.last_error, 60) }}</td>
            <td class="text-right">
              <button
                v-if="row.status === 'dlq' || row.status === 'failed'"
                class="btn btn-sm btn-outline-primary"
                :disabled="retryingId === row.id"
                @click="retry(row)"
              >
                <i v-if="retryingId === row.id" class="fas fa-spinner fa-spin"></i>
                <i v-else class="fas fa-redo"></i>
              </button>
              <button
                class="btn btn-sm btn-icon ml-1"
                title="Полный payload"
                @click="openDetail(row)"
              >
                <i class="fas fa-eye"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Детали с payload -->
    <div v-if="detailRow" class="modal-overlay" v-modal-close="() => detailRow = null">
      <div class="modal-content modal-glass" @click.stop style="max-width: 720px;">
        <div class="modal-glass-header">
          <h4 class="m-0">{{ detailRow.event_type }}</h4>
          <button class="btn btn-sm btn-icon btn-ghost" @click="detailRow = null">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="info-grid">
            <div class="info-row"><span class="text-muted">event_id</span><span class="font-monospace small text-right">{{ detailRow.event_id }}</span></div>
            <div class="info-row"><span class="text-muted">Сущность</span><span class="font-monospace small text-right">{{ detailRow.entity_type }} / {{ detailRow.entity_id }}</span></div>
            <div class="info-row"><span class="text-muted">Статус</span><span class="text-right">{{ detailRow.status }}</span></div>
            <div class="info-row"><span class="text-muted">Попыток</span><span class="text-right">{{ detailRow.attempt_count }}</span></div>
            <div class="info-row"><span class="text-muted">Создано</span><span class="text-right">{{ formatDateTime(detailRow.created_at) }}</span></div>
            <div v-if="detailRow.delivered_at" class="info-row"><span class="text-muted">Доставлено</span><span class="text-right">{{ formatDateTime(detailRow.delivered_at) }}</span></div>
            <div v-if="detailRow.scheduled_at" class="info-row"><span class="text-muted">Следующая попытка</span><span class="text-right">{{ formatDateTime(detailRow.scheduled_at) }}</span></div>
            <div v-if="detailRow.last_error" class="info-row"><span class="text-muted">Ошибка</span><span class="text-right text-danger small">{{ detailRow.last_error }}</span></div>
            <div v-if="detailRow.causation_chain?.length" class="info-row">
              <span class="text-muted">Причинная цепочка</span>
              <span class="text-right font-monospace small">
                <span v-for="(ev, i) in detailRow.causation_chain" :key="ev" class="chain-link">
                  <span :title="ev">{{ shortId(ev) }}</span>
                  <span v-if="i < detailRow.causation_chain.length - 1" class="text-muted">→</span>
                </span>
              </span>
            </div>
          </div>
          <h5 class="mt-3">Payload (v{{ detailRow.payload_version }})</h5>
          <pre class="payload-box">{{ formatJson(detailRow.payload) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/services/api'
import { useToast } from '@/composables/useToast'
import { formatDateTime as fmtDateTime, formatTime as fmtTime } from '@/utils/format'

export default {
  name: 'IntegrationsOutbox',
  setup() {
    const toast = useToast()
    const items = ref([])
    const stats = ref(null)
    const loading = ref(false)
    const statusFilter = ref('')
    const eventTypeFilter = ref('')
    const retryingId = ref(null)
    const detailRow = ref(null)

    const load = async () => {
      loading.value = true
      try {
        const params = { limit: 200 }
        if (statusFilter.value) params.status = statusFilter.value
        if (eventTypeFilter.value) params.event_type = eventTypeFilter.value
        // Параллельно тянем сами события и агрегаты — оба запроса лёгкие.
        const [list, summary] = await Promise.all([
          api.eventBus.listOutbox(params),
          api.eventBus.getStats().catch(() => null),  // stats — best-effort
        ])
        items.value = Array.isArray(list) ? list : []
        if (summary) stats.value = summary
      } catch (e) {
        toast.error(e?.response?.data?.detail || 'Не удалось загрузить outbox')
        items.value = []
      } finally {
        loading.value = false
      }
    }

    // Карточки сверху — кликабельные мини-фильтры по статусу.
    // Toned-классы (success/warning/danger/secondary) применяют цвет
    // через CSS — здесь же выбираем какой по смыслу куда подходит.
    const statsCards = computed(() => {
      if (!stats.value) return []
      const c = stats.value.counts || {}
      return [
        { key: 'pending',   label: 'Pending',   value: c.pending   || 0, filter: 'pending',   tone: 'tone-secondary' },
        { key: 'delivered', label: 'Delivered', value: c.delivered || 0, filter: 'delivered', tone: 'tone-success' },
        { key: 'failed',    label: 'Failed',    value: c.failed    || 0, filter: 'failed',    tone: 'tone-warning' },
        { key: 'dlq',       label: 'DLQ',       value: c.dlq       || 0, filter: 'dlq',       tone: 'tone-danger' },
        { key: 'subs',      label: 'Подписок',  value: stats.value.totals?.subscriptions || 0, filter: '__noop',  tone: 'tone-info' },
      ]
    })

    const quickFilter = (f) => {
      if (f === '__noop') return
      // Toggle: если уже активен — снять.
      statusFilter.value = (statusFilter.value === f) ? '' : f
      load()
    }

    const retry = async (row) => {
      retryingId.value = row.id
      try {
        await api.eventBus.retryOutbox(row.id)
        toast.success('Сброшено в pending — worker подхватит на следующем тике')
        await load()
      } catch (e) {
        toast.error(e?.response?.data?.detail || 'Не удалось перезапустить')
      } finally {
        retryingId.value = null
      }
    }

    const openDetail = (row) => { detailRow.value = row }

    const statusClass = (s) => ({
      pending: 'badge-secondary',
      delivering: 'badge-info',
      delivered: 'badge-success',
      failed: 'badge-warning',
      dlq: 'badge-danger',
    }[s] || 'badge-secondary')

    const formatDateTime = (v) => v ? fmtDateTime(v) : '—'
    const formatTime = (v) => v ? fmtTime(v) : ''
    const shortId = (id) => id ? String(id).slice(0, 8) : ''
    const truncate = (s, n) => !s ? '' : (s.length > n ? s.slice(0, n) + '…' : s)
    const formatJson = (obj) => JSON.stringify(obj || {}, null, 2)

    onMounted(load)
    return {
      items, stats, statsCards, loading, statusFilter, eventTypeFilter, retryingId, detailRow,
      load, retry, openDetail, quickFilter,
      statusClass, formatDateTime, formatTime, shortId, truncate, formatJson,
    }
  }
}
</script>

<style scoped>
.event-outbox-view { height: 100%; overflow: auto; }
.payload-box {
  background: var(--md-sys-color-surface-container-low, #f6f8fa);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 8px;
  padding: 12px;
  font-size: 0.82rem;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 360px;
  overflow: auto;
}
.font-monospace { font-family: ui-monospace, 'JetBrains Mono', Menlo, Consolas, monospace; }

/* === V1.5: stat-cards (summary над таблицей) ============================ */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}
.stat-card {
  background: var(--md-sys-color-surface, #fff);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 10px;
  padding: 12px 14px;
  text-align: left;
  cursor: pointer;
  transition: transform 0.12s ease, box-shadow 0.12s ease, border-color 0.12s ease;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat-card:hover { transform: translateY(-1px); box-shadow: 0 2px 6px rgba(0,0,0,0.08); }
.stat-card.active { border-color: var(--md-sys-color-primary); box-shadow: 0 0 0 2px var(--md-sys-color-primary-container, rgba(33,150,243,0.15)); }
.stat-card__value { font-size: 1.6rem; font-weight: 700; line-height: 1.1; }
.stat-card__label { font-size: 0.78rem; color: var(--md-sys-color-on-surface-variant); text-transform: uppercase; letter-spacing: 0.04em; }
/* Тоновые акценты вдоль левой границы — сразу понятно где «горит» */
.tone-success    { border-left: 3px solid var(--color-success, #2e7d32); }
.tone-warning    { border-left: 3px solid var(--color-warning, #ed6c02); }
.tone-danger     { border-left: 3px solid var(--color-danger, #d32f2f); }
.tone-info       { border-left: 3px solid var(--md-sys-color-primary, #1976d2); }
.tone-secondary  { border-left: 3px solid var(--md-sys-color-outline, #9aa0a6); }
@media (max-width: 1100px) {
  .stats-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 720px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}

/* === causation chain в деталях ========================================== */
.chain-link { display: inline-flex; align-items: center; gap: 4px; margin-right: 6px; }
.chain-link span:first-child {
  background: var(--md-sys-color-surface-container-low, #f6f8fa);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 6px;
  padding: 1px 6px;
}
</style>
