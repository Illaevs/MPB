<template>
  <div class="tenders-admin-view">
    <div class="list-card">
    <div class="list-card__toolbar tenders-admin-toolbar">
      <h2 class="tenders-admin-toolbar__title">Тендеры</h2>
      <div class="tenders-admin-toolbar__controls">
        <UiSelect
          v-model="filters.status"
          class="tenders-admin-toolbar__select"
          :options="statusOptions"
          placeholder="Все статусы"
          size="sm"
          @update:modelValue="loadItems"
        />
        <UiIconButton icon="fas fa-sync" label="Обновить" size="sm" @click="loadItems" />
      </div>
    </div>

    <div class="list-card__body">
      <div v-if="loading" class="tenders-admin-loading">
        <UiSpinner size="lg" />
      </div>

      <UiEmptyState
        v-else-if="items.length === 0"
        icon="fas fa-gavel"
        title="Нет тендеров"
        description="Нет тендеров по выбранным критериям"
      />

      <div v-else class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>Сделка</th>
              <th>Объект</th>
              <th>Том/работа</th>
              <th class="text-right">Наша цена</th>
              <th>Подрядчик</th>
              <th class="text-right">Цена подрядчика</th>
              <th class="text-right">Прибыль</th>
              <th>Статус</th>
              <th class="text-center">Отклики</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.deal_product_id" class="tender-row">
              <td>
                <div class="fw-500">{{ item.deal_title || '-' }}</div>
                <div class="small text-muted">{{ shortId(item.deal_id) }}</div>
              </td>
              <td>
                <div class="fw-500">{{ item.obj_name || '-' }}</div>
                <div class="small text-muted">
                  {{ item.object_type || '-' }} · {{ item.object_area || '-' }} м²
                </div>
              </td>
              <td>
                <div class="fw-500">{{ item.product_name || '-' }}</div>
              </td>
              <td class="text-right font-mono">{{ formatCurrency(item.our_price || 0) }}</td>
              <td>
                <div v-if="item.winner_company_name" class="d-flex align-center gap-2">
                  <i class="fas fa-trophy text-warning"></i>
                  <span>{{ item.winner_company_name }}</span>
                </div>
                <span v-else class="text-muted">-</span>
              </td>
              <td class="text-right font-mono">
                {{ item.winner_amount != null ? formatCurrency(item.winner_amount) : '-' }}
              </td>
              <td class="text-right">
                <span
                  v-if="item.gross_profit != null"
                  :class="item.gross_profit >= 0 ? 'text-success' : 'text-danger'"
                  class="font-mono"
                >
                  {{ formatCurrency(item.gross_profit) }}
                </span>
                <span v-else class="text-muted">-</span>
              </td>
              <td>
                <span class="status-badge" :class="statusClass(item)">
                  {{ statusLabel(item) }}
                </span>
              </td>
              <td class="text-center">
                <span class="offers-count" :class="{ 'has-responses': (item.offers_responded || 0) > 0 }">
                  {{ item.offers_responded || 0 }} / {{ item.offers_count || 0 }}
                </span>
              </td>
              <td class="text-right">
                <UiButton
                  v-if="!item.tender_id"
                  variant="primary"
                  size="sm"
                  icon-left="fas fa-plus"
                  @click="openCreateModal(item)"
                >
                  Тендер
                </UiButton>
                <UiButton
                  v-else
                  variant="outline"
                  size="sm"
                  icon-left="fas fa-eye"
                  @click="openTender(item)"
                >
                  Открыть
                </UiButton>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    </div>

    <UiModal
      v-model="showCreateModal"
      title="Отправить на тендер"
      size="sm"
      @close="showCreateModal = false"
    >
      <div class="create-tender-form">
        <div class="small text-muted mb-2">
          {{ createTarget?.deal_title || '-' }} · {{ createTarget?.product_name || '-' }}
        </div>
        <label class="create-tender-form__label">
          Срок окончания подачи предложений
          <span class="text-muted">(необязательно)</span>
        </label>
        <input type="datetime-local" v-model="createDeadline" class="create-tender-form__input">
        <p class="create-tender-form__hint">
          После этого срока приём заканчивается: тендер перестаёт быть активным
          в панели подрядчика для тех, кто не подал заявку.
        </p>
      </div>
      <template #footer>
        <UiButton variant="secondary" @click="showCreateModal = false">Отмена</UiButton>
        <UiButton variant="primary" :loading="creating" @click="confirmCreateTender">
          Создать тендер
        </UiButton>
      </template>
    </UiModal>

    <UiModal
      v-model="showTenderModal"
      size="xl"
      @close="closeTender"
    >
      <template #header>
        <div class="modal-header">
          <div>
            <h3 class="m-0">Тендер по тому/работе</h3>
            <div class="small text-muted mt-1">
              {{ activeItem?.deal_title || '-' }} · {{ activeItem?.product_name || '-' }}
            </div>
          </div>
          <div class="d-flex align-center gap-3">
            <span class="status-badge" :class="statusClass(activeItem)">
              {{ statusLabel(activeItem) }}
            </span>
            <UiIconButton icon="fas fa-times" label="Закрыть" size="sm" @click="closeTender" />
          </div>
        </div>
      </template>

      <div class="tender-deadline-row">
        <label class="tender-deadline-row__label">
          <i class="fas fa-hourglass-end"></i>
          Срок окончания подачи предложений
        </label>
        <input
          type="datetime-local"
          v-model="tenderDeadline"
          class="tender-deadline-row__input"
        >
        <UiButton variant="primary" size="sm" :loading="savingDeadline" @click="saveTenderDeadline">
          Сохранить срок
        </UiButton>
        <UiButton
          v-if="tenderDeadline"
          variant="ghost"
          size="sm"
          @click="tenderDeadline = ''; saveTenderDeadline()"
        >
          Снять
        </UiButton>
      </div>

      <UiEmptyState
        v-if="offers.length === 0"
        icon="fas fa-inbox"
        title="Пока нет откликов"
        description="Ответы подрядчиков появятся здесь."
      />

      <div v-else class="offers-table">
        <table class="table">
          <thead>
            <tr>
              <th>Подрядчик</th>
              <th>Статус</th>
              <th class="text-right">Сумма</th>
              <th>Срок</th>
              <th>Комментарий</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="offer in offers" :key="offer.id" :class="{ 'winner-row': offer.status === 'winner' }">
              <td>
                <div class="d-flex align-center gap-2">
                  <i v-if="offer.status === 'winner'" class="fas fa-trophy text-warning"></i>
                  <span class="fw-500">{{ offer.company_name || '-' }}</span>
                </div>
              </td>
              <td>
                <span class="status-badge" :class="offerStatusClass(offer.status)">
                  {{ offerStatusLabel(offer.status) }}
                </span>
              </td>
              <td class="text-right font-mono">
                {{ offer.proposed_amount != null ? formatCurrency(offer.proposed_amount) : '-' }}
              </td>
              <td>{{ offer.proposed_deadline || '-' }}</td>
              <td class="comment-cell">{{ offer.comment || '-' }}</td>
              <td class="text-right">
                <UiButton
                  v-if="canSelectWinner(offer)"
                  variant="success"
                  size="sm"
                  icon-left="fas fa-crown"
                  @click="selectWinner(offer)"
                >
                  Выбрать
                </UiButton>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <template #footer>
        <UiButton variant="secondary" @click="closeTender">Закрыть</UiButton>
      </template>
    </UiModal>

    <div v-if="toast.show" class="toast-notification" :class="toast.type">
      <i :class="toast.type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'" aria-hidden="true"></i>
      {{ toast.message }}
    </div>
  </div>
</template>

<script>
import { onMounted, ref } from 'vue'
import { api } from '@/services/api'
import { UiButton, UiCard, UiEmptyState, UiIconButton, UiModal, UiSelect, UiSpinner } from '../components/ui'

export default {
  name: 'TendersAdmin',
  components: { UiButton, UiCard, UiEmptyState, UiIconButton, UiModal, UiSelect, UiSpinner },
  setup() {
    const items = ref([])
    const filters = ref({ status: '' })
    const showTenderModal = ref(false)
    const activeItem = ref(null)
    const offers = ref([])
    const loading = ref(false)

    // Create-with-deadline + deadline editing
    const showCreateModal = ref(false)
    const createTarget = ref(null)
    const createDeadline = ref('')
    const creating = ref(false)
    const tenderDeadline = ref('')
    const savingDeadline = ref(false)

    const toLocalInput = (iso) => (iso ? String(iso).slice(0, 16) : '')

    const statusOptions = [
      { value: 'no_tender', label: 'Без тендера' },
      { value: 'new', label: 'Новый' },
      { value: 'review', label: 'На рассмотрении' },
      { value: 'archived', label: 'Архив' }
    ]

    const toast = ref({ show: false, message: '', type: 'success' })

    const showToast = (message, type = 'success') => {
      toast.value = { show: true, message, type }
      setTimeout(() => { toast.value.show = false }, 3000)
    }

    const loadItems = async () => {
      loading.value = true
      try {
        const params = {}
        if (filters.value.status) params.status = filters.value.status
        const res = await api.tenders.listItems(params)
        items.value = res || []
      } catch (error) {
        console.error(error)
        showToast('Не удалось загрузить тендеры', 'error')
      } finally {
        loading.value = false
      }
    }

    const openCreateModal = (item) => {
      createTarget.value = item
      createDeadline.value = ''
      showCreateModal.value = true
    }

    const confirmCreateTender = async () => {
      if (!createTarget.value) return
      creating.value = true
      try {
        await api.tenders.create({
          deal_product_id: createTarget.value.deal_product_id,
          submission_deadline: createDeadline.value || null,
        })
        showToast('Тендер создан')
        showCreateModal.value = false
        await loadItems()
      } catch (error) {
        console.error(error)
        showToast('Не удалось создать тендер', 'error')
      } finally {
        creating.value = false
      }
    }

    const openTender = async (item) => {
      activeItem.value = item
      showTenderModal.value = true
      tenderDeadline.value = ''
      try {
        const res = await api.tenders.getById(item.tender_id)
        offers.value = res?.offers || []
        tenderDeadline.value = toLocalInput(res?.tender?.submission_deadline)
      } catch (error) {
        console.error(error)
      }
    }

    const saveTenderDeadline = async () => {
      if (!activeItem.value?.tender_id) return
      savingDeadline.value = true
      try {
        await api.tenders.update(activeItem.value.tender_id, {
          submission_deadline: tenderDeadline.value || null,
        })
        showToast('Срок подачи обновлён')
        await loadItems()
      } catch (error) {
        console.error(error)
        showToast('Не удалось сохранить срок', 'error')
      } finally {
        savingDeadline.value = false
      }
    }

    const closeTender = () => {
      showTenderModal.value = false
      activeItem.value = null
      offers.value = []
    }

    const selectWinner = async (offer) => {
      if (!activeItem.value) return
      try {
        await api.tenders.selectWinner(activeItem.value.tender_id, { offer_id: offer.id })
        showToast('Победитель выбран')
        await loadItems()
        await openTender(activeItem.value)
      } catch (error) {
        console.error(error)
        showToast('Не удалось выбрать победителя', 'error')
      }
    }

    const canSelectWinner = (offer) => {
      if (!activeItem.value || activeItem.value.tender_status === 'archived') return false
      return offer.status === 'responded'
    }

    const statusLabel = (item) => {
      if (!item?.tender_id) return 'Без тендера'
      if (item.tender_status === 'new') return 'Новый'
      if (item.tender_status === 'review') return 'Рассмотрение'
      if (item.tender_status === 'archived') return 'Архив'
      return item.tender_status || '-'
    }

    const statusClass = (item) => {
      if (!item?.tender_id) return 'badge-neutral'
      if (item.tender_status === 'new') return 'badge-warning'
      if (item.tender_status === 'review') return 'badge-primary'
      if (item.tender_status === 'archived') return 'badge-success'
      return 'badge-neutral'
    }

    const offerStatusLabel = (status) => {
      const labels = {
        invited: 'Приглашен',
        responded: 'Ответил',
        declined: 'Отказ',
        winner: 'Победитель'
      }
      return labels[status] || status
    }

    const offerStatusClass = (status) => {
      const classes = {
        invited: 'badge-neutral',
        responded: 'badge-primary',
        declined: 'badge-danger',
        winner: 'badge-success'
      }
      return classes[status] || 'badge-neutral'
    }

    const shortId = (id) => id ? String(id).slice(0, 8) : ''
    const formatCurrency = (value) =>
      new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 0
      }).format(value || 0)

    onMounted(loadItems)

    return {
      items,
      filters,
      statusOptions,
      showTenderModal,
      activeItem,
      offers,
      loading,
      loadItems,
      showCreateModal,
      createTarget,
      createDeadline,
      creating,
      openCreateModal,
      confirmCreateTender,
      tenderDeadline,
      savingDeadline,
      saveTenderDeadline,
      openTender,
      closeTender,
      selectWinner,
      canSelectWinner,
      statusLabel,
      statusClass,
      offerStatusLabel,
      offerStatusClass,
      shortId,
      formatCurrency,
      toast
    }
  }
}
</script>

<style scoped>
.tenders-admin-view {
  padding: var(--space-5);
}

.tenders-admin-toolbar {
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.tenders-admin-toolbar__title {
  margin: 0;
  font-size: var(--text-2xl);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.tenders-admin-toolbar__controls {
  display: flex;
  gap: var(--space-2);
  align-items: center;
  flex-wrap: wrap;
}

.tenders-admin-toolbar__select {
  min-width: 180px;
}

.tenders-admin-loading {
  display: flex;
  justify-content: center;
  padding: var(--space-10) 0;
}

.table-container {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  margin: 0;
}

.table th {
  background: var(--color-surface-3);
  padding: var(--space-3) var(--space-4);
  font-weight: var(--fw-semibold);
  font-size: var(--text-sm);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--color-text-muted);
  border-bottom: 1px solid var(--color-border-subtle);
}

.table td {
  padding: var(--space-3) var(--space-4);
  vertical-align: middle;
  border-bottom: 1px solid var(--color-border-subtle);
}

.table tbody tr:hover {
  background: var(--color-surface-2);
}

.winner-row {
  background: rgba(76, 175, 80, 0.08) !important;
}

.fw-500 { font-weight: var(--fw-medium); }
.font-mono { font-family: var(--font-mono); }

.status-badge {
  display: inline-flex;
  align-items: center;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-pill);
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  white-space: nowrap;
}

.badge-neutral { background: #e0e0e0; color: #616161; }
.badge-warning { background: #fff3e0; color: #e65100; }
.badge-primary { background: #e3f2fd; color: #1565c0; }
.badge-success { background: #e8f5e9; color: #2e7d32; }
.badge-danger { background: #ffebee; color: #c62828; }

.offers-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--text-base);
  background: var(--color-surface-3);
}

.offers-count.has-responses {
  background: #e3f2fd;
  color: #1565c0;
  font-weight: var(--fw-semibold);
}

.modal-header {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-4);
}

.offers-table {
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.comment-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.toast-notification {
  position: fixed;
  bottom: var(--space-8);
  right: var(--space-8);
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-5);
  border-radius: var(--radius-md);
  color: #fff;
  font-weight: var(--fw-medium);
  box-shadow: var(--shadow-lg);
  z-index: 2000;
  animation: slideIn var(--dur-slow) ease;
}

.toast-notification.success {
  background: #4caf50;
}

.toast-notification.error {
  background: #f44336;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@media (max-width: 768px) {
  .tenders-admin-view {
    padding: var(--space-3);
  }

  .tenders-admin-toolbar__select {
    min-width: 0;
    width: 100%;
  }

  .table {
    min-width: 900px;
  }

  .toast-notification {
    left: var(--space-4);
    right: var(--space-4);
    bottom: var(--space-4);
  }
}
</style>
