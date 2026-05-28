<template>
  <div class="tenders-sub-view">
    <div class="tenders-sub-toolbar">
      <div>
        <h2 class="tenders-sub-toolbar__title">Тендеры подрядчика</h2>
        <p class="tenders-sub-toolbar__caption">Отвечайте на тендерные предложения</p>
      </div>
      <div class="tenders-sub-toolbar__controls">
        <UiSelect
          v-model="selectedCompanyId"
          class="tenders-sub-toolbar__select"
          :options="subcontractorOptions"
          placeholder="Выберите подрядчика"
          size="sm"
          @update:modelValue="loadTenders"
        />
        <UiIconButton icon="fas fa-sync" label="Обновить" size="sm" @click="loadTenders" />
      </div>
    </div>

    <div v-if="loading" class="tenders-sub-loading">
      <UiSpinner size="lg" />
    </div>

    <UiEmptyState
      v-else-if="!selectedCompanyId"
      icon="fas fa-building"
      title="Выберите компанию"
      description="Выберите подрядчика из списка выше, чтобы увидеть доступные тендеры"
    />

    <UiEmptyState
      v-else-if="!tenders.length"
      icon="fas fa-inbox"
      title="Нет тендеров"
      description="Для выбранного подрядчика нет активных тендеров"
    />

    <div v-else class="tender-grid">
      <div
        v-for="row in tenders"
        :key="row.offer_id"
        class="tender-card"
        :class="{ 'is-winner': row.offer_status === 'winner', 'is-archived': row.tender_status === 'archived' }"
      >
        <div class="tender-card-header">
          <div class="tender-info">
            <div class="tender-object">{{ row.obj_name || 'Без объекта' }}</div>
            <div class="tender-deal">{{ row.deal_title || '-' }}</div>
          </div>
          <div class="tender-status">
            <span class="status-badge" :class="getStatusClass(row)">
              {{ getStatusLabel(row) }}
            </span>
          </div>
        </div>

        <div class="tender-product">
          <i class="fas fa-box" aria-hidden="true"></i>
          <span class="tender-product-label">Том/работа:</span>
          <span class="product-name">{{ row.product_name || '-' }}</span>
          <span class="product-price">{{ formatCurrency(row.our_price || 0) }}</span>
        </div>

        <div class="tender-form">
          <div class="form-row">
            <UiInput
              v-model.number="row.proposed_amount"
              label="Ваша цена"
              type="number"
              min="0"
              placeholder="0"
              :disabled="isReadOnly(row)"
            />
            <UiInput
              v-model="row.proposed_deadline"
              label="Срок"
              type="date"
              :disabled="isReadOnly(row)"
            />
          </div>
          <UiInput
            v-model="row.comment"
            label="Комментарий"
            placeholder="Условия, примечания..."
            :disabled="isReadOnly(row)"
          />
        </div>

        <div class="tender-card-footer">
          <div v-if="row.offer_status === 'winner'" class="winner-badge">
            <i class="fas fa-trophy" aria-hidden="true"></i>Победитель
          </div>
          <div v-else-if="row.offer_status === 'responded'" class="responded-badge">
            <i class="fas fa-check" aria-hidden="true"></i>Отправлено
          </div>
          <div v-else></div>

          <UiButton
            variant="primary"
            size="sm"
            icon-left="fas fa-paper-plane"
            :loading="submitting === row.offer_id"
            :disabled="isReadOnly(row) || submitting === row.offer_id"
            @click="submitOffer(row)"
          >
            {{ row.offer_status === 'responded' ? 'Обновить' : 'Отправить' }}
          </UiButton>
        </div>
      </div>
    </div>

    <div v-if="toast.show" class="toast-notification" :class="toast.type">
      <i :class="toast.type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'" aria-hidden="true"></i>
      {{ toast.message }}
    </div>
  </div>
</template>

<script>
import { computed, onMounted, ref } from 'vue'
import { api } from '@/services/api'
import { UiButton, UiEmptyState, UiIconButton, UiInput, UiSelect, UiSpinner } from '../components/ui'
import { useCompaniesStore } from '../stores/companies'

export default {
  name: 'TendersSubcontractor',
  components: { UiButton, UiEmptyState, UiIconButton, UiInput, UiSelect, UiSpinner },
  setup() {
    const companiesStore = useCompaniesStore()
    const subcontractors = ref([])
    const selectedCompanyId = ref('')
    const tenders = ref([])
    const loading = ref(false)
    const submitting = ref(null)

    const toast = ref({ show: false, message: '', type: 'success' })
    const showToast = (message, type = 'success') => {
      toast.value = { show: true, message, type }
      setTimeout(() => { toast.value.show = false }, 3000)
    }

    const subcontractorOptions = computed(() =>
      subcontractors.value.map((company) => ({ value: company.id, label: company.name }))
    )

    const loadCompanies = async () => {
      try {
        await companiesStore.ensureLoaded()
        subcontractors.value = companiesStore.items.filter((company) => company.type === 'subcontractor')
      } catch (error) {
        console.error(error)
      }
    }

    const loadTenders = async () => {
      if (!selectedCompanyId.value) {
        tenders.value = []
        return
      }
      loading.value = true
      try {
        const res = await api.tenders.listForCompany(selectedCompanyId.value)
        tenders.value = res || []
      } catch (error) {
        console.error(error)
        showToast('Ошибка загрузки тендеров', 'error')
      } finally {
        loading.value = false
      }
    }

    const submitOffer = async (row) => {
      if (!row.proposed_amount || row.proposed_amount <= 0) {
        showToast('Укажите вашу цену', 'error')
        return
      }
      submitting.value = row.offer_id
      try {
        await api.tenders.updateOffer(row.offer_id, {
          status: 'responded',
          proposed_amount: row.proposed_amount,
          proposed_deadline: row.proposed_deadline || null,
          comment: row.comment || null
        })
        showToast('Отклик успешно отправлен')
        await loadTenders()
      } catch (error) {
        console.error(error)
        showToast('Не удалось отправить отклик', 'error')
      } finally {
        submitting.value = null
      }
    }

    // submission_closed (с бэка) = срок подачи прошёл И эта компания не
    // подала заявку → тендер для неё больше не активен.
    const isReadOnly = (row) =>
      row.tender_status === 'archived' || row.offer_status === 'winner' || row.submission_closed

    const getStatusLabel = (row) => {
      if (row.offer_status === 'winner') return 'Победа'
      if (row.offer_status === 'responded') return 'Отправлено'
      if (row.submission_closed) return 'Приём закрыт'
      if (row.tender_status === 'archived') return 'Архив'
      if (row.tender_status === 'review') return 'На рассмотрении'
      return 'Новый'
    }

    const getStatusClass = (row) => {
      if (row.offer_status === 'winner') return 'badge-success'
      if (row.offer_status === 'responded') return 'badge-primary'
      if (row.submission_closed) return 'badge-neutral'
      if (row.tender_status === 'archived') return 'badge-neutral'
      if (row.tender_status === 'review') return 'badge-warning'
      return 'badge-info'
    }

    const formatCurrency = (value) =>
      new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 0
      }).format(value || 0)

    onMounted(loadCompanies)

    return {
      subcontractors,
      subcontractorOptions,
      selectedCompanyId,
      tenders,
      loading,
      submitting,
      loadTenders,
      submitOffer,
      isReadOnly,
      getStatusLabel,
      getStatusClass,
      formatCurrency,
      toast
    }
  }
}
</script>

<style scoped>
.tenders-sub-view {
  padding: var(--space-5);
}

.tenders-sub-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
  flex-wrap: wrap;
}

.tenders-sub-toolbar__title {
  margin: 0;
  font-size: var(--text-2xl);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.tenders-sub-toolbar__caption {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.tenders-sub-toolbar__controls {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.tenders-sub-toolbar__select {
  min-width: 240px;
}

.tenders-sub-loading {
  display: flex;
  justify-content: center;
  padding: var(--space-10) 0;
}

.tender-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: var(--space-5);
}

.tender-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: transform var(--dur-base) var(--ease-out), box-shadow var(--dur-base) ease;
  box-shadow: var(--shadow-sm);
}

.tender-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.tender-card.is-winner {
  border-color: #4caf50;
  background: linear-gradient(to bottom, #e8f5e9 0%, var(--color-surface) 100%);
}

.tender-card.is-archived {
  opacity: 0.72;
}

.tender-card-header {
  padding: var(--space-4);
  background: var(--color-surface-2);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-3);
}

.tender-object {
  font-weight: var(--fw-semibold);
  font-size: var(--text-md);
  margin-bottom: var(--space-1);
}

.tender-deal {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.status-badge {
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-pill);
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  white-space: nowrap;
}

.badge-success { background: #e8f5e9; color: #2e7d32; }
.badge-primary { background: #e3f2fd; color: #1565c0; }
.badge-warning { background: #fff3e0; color: #e65100; }
.badge-info { background: #e1f5fe; color: #0277bd; }
.badge-neutral { background: #eceff1; color: #546e7a; }

.tender-product {
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-3);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-base);
}

.tender-product-label {
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  color: var(--color-text-muted);
  white-space: nowrap;
}

.product-name {
  flex-grow: 1;
  font-weight: var(--fw-medium);
}

.product-price {
  font-family: var(--font-mono);
  font-weight: var(--fw-semibold);
  color: var(--color-primary);
}

.tender-form {
  padding: var(--space-4);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.tender-card-footer {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--color-border-subtle);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-3);
}

.winner-badge,
.responded-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-base);
}

.winner-badge {
  color: #2e7d32;
  font-weight: var(--fw-semibold);
}

.responded-badge {
  color: #1565c0;
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
  .tenders-sub-view {
    padding: var(--space-3);
  }

  .tender-grid {
    grid-template-columns: 1fr;
    gap: var(--space-3);
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .tenders-sub-toolbar__select {
    min-width: 0;
    width: 100%;
  }

  .toast-notification {
    left: var(--space-4);
    right: var(--space-4);
    bottom: var(--space-4);
  }
}
</style>
