<template>
  <div class="contract-tab contract-tab--data">
    <div class="contract-flat-stack">
      <section class="contract-flat-section contract-panel">
        <div class="contract-flat-section__header">
          <div>
            <h3 class="card-title m-0">История оплат</h3>
            <small>{{ filteredPayments.length }} записей</small>
          </div>
          <small class="contract-flat-section__meta">Всего {{ formatAmount(paymentSummary.total_amount) }}</small>
        </div>
        <div v-if="loading" class="text-center py-4">
          <i class="fas fa-spinner fa-spin fa-2x text-muted"></i>
        </div>
        <div v-else-if="!filteredPayments.length" class="empty-state">
          <i class="fas fa-receipt"></i>
          <p>Платежей пока нет</p>
          <small class="text-muted">История оплат появится после распределения в казначействе</small>
        </div>
        <div v-else class="table-container contract-table-wrap contract-table-wrap--flat">
          <table class="table table-sm">
            <thead>
              <tr>
                <th>Тип</th>
                <th class="text-right">Сумма</th>
                <th>План</th>
                <th>Факт</th>
                <th>Плательщик</th>
                <th>Получатель</th>
                <th>Сделка</th>
                <th>Статус</th>
                <th class="text-right">Оплачено</th>
                <th>Платежи</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="entry in filteredPayments" :key="entry.id">
                <td>
                  <span class="contract-type-pill" :class="entry.direction === 'income' ? 'contract-type-pill--blue' : 'contract-type-pill--orange'">
                    {{ entry.direction === 'income' ? 'Доход' : 'Расход' }}
                  </span>
                </td>
                <td class="text-right">{{ formatAmount(entry.amount) }}</td>
                <td>{{ formatDate(entry.plan_date) }}</td>
                <td>{{ formatDate(entry.actual_date) }}</td>
                <td>{{ entry.payer_name || '-' }}</td>
                <td>{{ entry.payee_name || '-' }}</td>
                <td>{{ entry.deal_title || '-' }}</td>
                <td>
                  <span class="badge" :class="paymentStatusClass(entry.payment_status)">
                    {{ paymentStatusLabel(entry.payment_status) }}
                  </span>
                </td>
                <td class="text-right">{{ formatAmount(entry.paid_amount) }}</td>
                <td>
                  <div v-if="entry.payments_history.length" class="d-flex flex-column gap-1">
                    <div
                      v-for="item in entry.payments_history"
                      :key="item.transaction_id + '-' + (item.allocation_id || '')"
                      class="small contract-inline-note"
                    >
                      {{ formatDate(item.transaction_date) }} - {{ formatAmount(item.amount) }}
                      <span v-if="item.doc_num" class="text-muted">({{ item.doc_num }})</span>
                      <span v-if="item.category_code" class="text-muted">— {{ item.category_code }}</span>
                    </div>
                  </div>
                  <div v-else class="text-muted small">Нет истории</div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="contract-flat-section contract-panel">
        <div class="contract-flat-section__header">
          <div>
            <h3 class="card-title m-0">Этапы с суммой</h3>
            <small>{{ filteredStages.length }} этапов</small>
          </div>
          <small class="contract-flat-section__meta">План {{ formatAmount(stagesPlannedAmount) }}</small>
        </div>
        <div v-if="loading" class="text-center py-4">
          <i class="fas fa-spinner fa-spin fa-2x text-muted"></i>
        </div>
        <div v-else-if="!filteredStages.length" class="empty-state">
          <i class="fas fa-list-check"></i>
          <p>Этапов нет</p>
          <small class="text-muted">Этапы создаются в карточке сделки</small>
        </div>
        <div v-else class="table-container contract-table-wrap contract-table-wrap--flat">
          <table class="table table-sm">
            <thead>
              <tr>
                <th>Название</th>
                <th>Тип</th>
                <th>Даты</th>
                <th class="text-right">План</th>
                <th>Статус</th>
                <th>Закрыт</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="stage in filteredStages" :key="stage.id">
                <td>{{ stage.name }}</td>
                <td>
                  <span class="contract-type-pill" :class="`contract-type-pill--${stage.stage_type || 'gray'}`">
                    {{ stageTypeLabel(stage.stage_type) }}
                  </span>
                </td>
                <td>{{ formatDate(stage.date_start) }} - {{ formatDate(stage.date_end) }}</td>
                <td class="text-right">{{ formatAmount(stage.planned_cost) }}</td>
                <td>
                  <span class="badge" :class="stageStatusClass(stage.status)">
                    {{ stageStatusLabel(stage.status) }}
                  </span>
                </td>
                <td>
                  <span v-if="stage.is_closed === true" class="badge badge-success">Да</span>
                  <span v-else-if="stage.is_closed === false" class="badge badge-secondary">Нет</span>
                  <span v-else class="text-muted small">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ContractDataTab',
  props: {
    loading: Boolean,
    filteredPayments: { type: Array, required: true },
    filteredStages: { type: Array, required: true },
    paymentSummary: { type: Object, required: true },
    stagesPlannedAmount: { type: Number, default: 0 },
    formatAmount: { type: Function, required: true },
    formatDate: { type: Function, required: true },
    paymentStatusClass: { type: Function, required: true },
    paymentStatusLabel: { type: Function, required: true },
    stageTypeLabel: { type: Function, required: true },
    stageStatusClass: { type: Function, required: true },
    stageStatusLabel: { type: Function, required: true },
  }
}
</script>

<style scoped>
.contract-panel {
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
  padding: 0 !important;
}

.contract-tab {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.contract-tab--data { padding-top: 2px; }

.contract-flat-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.contract-flat-section { padding: 0 !important; }

.contract-flat-section__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 0;
  padding: 16px 18px 12px;
}
.contract-flat-section__header small {
  display: block;
  margin-top: 4px;
  color: #7b8798;
}
.contract-flat-section__meta {
  margin-top: 0 !important;
  color: #7b8798;
  font-size: 0.82rem;
  font-weight: 600;
  white-space: nowrap;
}

.contract-type-pill {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 14px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 0.92rem;
  border: 1px solid transparent;
}
.contract-type-pill--blue {
  background: #eef4ff;
  color: #2563eb;
  border-color: #cfe0ff;
}
.contract-type-pill--orange {
  background: #fff3e3;
  color: #ea580c;
  border-color: #ffd8ad;
}
.contract-type-pill--stage {
  background: #eef4ff;
  color: #2563eb;
  border-color: #cfe0ff;
}
.contract-type-pill--payment {
  background: #ebf8f0;
  color: #0f9f5f;
  border-color: #cbeed7;
}
.contract-type-pill--other,
.contract-type-pill--gray {
  background: #f3f4f6;
  color: #6b7280;
  border-color: #e5e7eb;
}

.contract-inline-note {
  padding: 6px 8px;
  border-radius: 8px;
  background: #f7f9fc;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 180px;
  padding: 1.25rem 1rem;
  border: 1px dashed rgba(148, 163, 184, 0.34);
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.82);
  text-align: center;
}
.empty-state i {
  font-size: 2.6rem;
  color: #c2ccd8;
  margin-bottom: 1rem;
}
.empty-state p {
  margin: 0 0 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
}

.contract-table-wrap {
  overflow: auto;
  border-top: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 0 0 14px 14px;
  background: rgba(255, 255, 255, 0.92);
}
.contract-table-wrap--flat {
  border-radius: 0 0 14px 14px;
  background: #fff;
}

:deep(.table) {
  margin: 0;
  min-width: 100%;
}
:deep(.table thead th) {
  padding: 14px 16px;
  border-top: none;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
  background: #fafbfd;
  color: #7b8798;
  font-size: 0.74rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  vertical-align: middle;
}
:deep(.table tbody td) {
  padding: 18px 16px;
  border-top: 1px solid rgba(15, 23, 42, 0.06);
  vertical-align: middle;
  color: #111827;
}
:deep(.table tbody tr:hover td) {
  background: rgba(248, 250, 252, 0.95);
}

@media (max-width: 980px) {
  .contract-flat-section__header {
    flex-direction: column;
    align-items: stretch;
  }
}
@media (max-width: 768px) {
  :deep(.table thead th), :deep(.table tbody td) {
    padding: 12px 12px;
  }
}
</style>
