<template>
  <div class="contract-tab contract-tab--expenses">
    <div class="card p-3 mb-2 contract-summary-panel">
      <div class="d-flex justify-between align-center mb-2 contract-panel__header">
        <h3 class="card-title m-0"><i class="fas fa-coins text-muted mr-2"></i>Расходная карточка</h3>
        <div class="d-flex gap-2 flex-wrap contract-panel__controls">
          <button class="btn btn-sm btn-outline-secondary contract-toolbar-btn" @click="$emit('open-bulk')">
            Массовое создание
          </button>
          <button class="btn btn-sm btn-primary contract-toolbar-btn contract-toolbar-btn--primary" @click="$emit('open-expense', null)">
            <i class="fas fa-plus mr-1"></i> Расход
          </button>
        </div>
      </div>
      <div class="text-muted small contract-summary-panel__meta">
        Плательщик: {{ expensePayerName || '-' }} • Получатель: {{ expensePayeeName || '-' }}
      </div>
      <div class="stats-row mt-2">
        <div class="stat-box text-center contract-stat">
          <small class="text-muted d-block">Всего</small>
          <span class="fw-600 stat-value" :class="expenseSummary.total_amount > 0 ? 'text-primary' : 'text-muted'">
            {{ formatAmount(expenseSummary.total_amount) }}
          </span>
        </div>
        <div class="stat-box text-center contract-stat">
          <small class="text-muted d-block">Оплачено</small>
          <span class="fw-600 stat-value" :class="expenseSummary.paid_amount > 0 ? 'text-success' : 'text-muted'">
            {{ formatAmount(expenseSummary.paid_amount) }}
          </span>
        </div>
        <div class="stat-box text-center contract-stat">
          <small class="text-muted d-block">Остаток</small>
          <span class="fw-600 stat-value" :class="expenseSummary.pending_amount > 0 ? 'text-warning' : 'text-muted'">
            {{ formatAmount(expenseSummary.pending_amount) }}
          </span>
        </div>
      </div>
    </div>

    <div class="card p-3 contract-panel">
      <div v-if="loadingExpenses" class="text-center py-4">
        <i class="fas fa-spinner fa-spin fa-2x text-muted"></i>
      </div>
      <div v-else-if="!expenseEntries.length" class="empty-state">
        <i class="fas fa-coins"></i>
        <p>Расходов пока нет</p>
        <small class="text-muted">Добавьте записи, чтобы сформировать график расходов</small>
      </div>
      <div v-else class="table-container contract-table-wrap">
        <table class="table table-sm">
          <thead>
            <tr>
              <th>Категория</th>
              <th class="text-right">Сумма</th>
              <th>План</th>
              <th>Факт</th>
              <th class="text-right">Оплачено</th>
              <th class="text-right">Остаток</th>
              <th>Платежи</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entry in expenseEntries" :key="entry.id">
              <td>{{ entry.category_code || '-' }}</td>
              <td class="text-right">{{ formatAmount(entry.amount) }}</td>
              <td>{{ formatDate(entry.plan_date) }}</td>
              <td>{{ formatDate(entry.actual_date) }}</td>
              <td class="text-right">{{ formatAmount(entry.paid_amount || 0) }}</td>
              <td class="text-right">
                {{ formatAmount(Math.max((entry.amount || 0) - (entry.paid_amount || 0), 0)) }}
              </td>
              <td>
                <div v-if="entry.payments_history.length" class="d-flex flex-column gap-1">
                  <div
                    v-for="item in entry.payments_history"
                    :key="item.transaction_id + '-' + (item.allocation_id || '')"
                    class="small bg-light p-1 rounded"
                  >
                    {{ formatDate(item.transaction_date) }} - {{ formatAmount(item.amount) }}
                    <span v-if="item.doc_num" class="text-muted">({{ item.doc_num }})</span>
                    <span v-if="item.category_code" class="text-muted">— {{ item.category_code }}</span>
                  </div>
                </div>
                <div v-else class="text-muted small">Нет истории</div>
              </td>
              <td class="text-right">
                <button class="btn btn-sm btn-icon" @click="$emit('open-expense', entry)">
                  <i class="fas fa-pen"></i>
                </button>
                <button class="btn btn-sm btn-icon text-danger" @click="$emit('delete-expense', entry)">
                  <i class="fas fa-trash"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ContractExpensesTab',
  props: {
    loadingExpenses: Boolean,
    expenseEntries: { type: Array, required: true },
    expenseSummary: { type: Object, required: true },
    expensePayerName: { type: String, default: '' },
    expensePayeeName: { type: String, default: '' },
    formatAmount: { type: Function, required: true },
    formatDate: { type: Function, required: true },
  },
  emits: ['open-bulk', 'open-expense', 'delete-expense']
}
</script>

<style scoped>
.contract-tab {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.contract-panel,
.contract-summary-panel {
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
  padding: 0 !important;
}

.contract-panel__header { gap: 10px; }
.contract-panel__header .card-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #111827;
}
.contract-panel__controls { justify-content: flex-end; }
.contract-summary-panel__meta { color: #6b7280; }

.contract-toolbar-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 38px;
  border-radius: 10px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  background: #fff;
  color: #111827;
  font-weight: 600;
}
.contract-toolbar-btn--primary {
  background: #111827;
  border-color: #111827;
  color: #fff;
  padding-inline: 16px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0;
}

.contract-stat {
  padding: 8px 12px 0;
  border-radius: 0;
  border: none;
  background: transparent;
  position: relative;
}

.contract-stat + .contract-stat::before {
  content: "";
  position: absolute;
  left: 0;
  top: 10px;
  bottom: 4px;
  width: 1px;
  background: rgba(15, 23, 42, 0.08);
}

.stat-value { font-size: 1.02rem; line-height: 1.15; }

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
.empty-state i { font-size: 2.6rem; color: #c2ccd8; margin-bottom: 1rem; }
.empty-state p { margin: 0 0 0.5rem; font-size: 1rem; font-weight: 600; color: #1f2937; }

.contract-table-wrap {
  overflow: auto;
  border-top: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 0 0 14px 14px;
  background: rgba(255, 255, 255, 0.92);
}

:deep(.table) { margin: 0; min-width: 100%; }
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

@media (max-width: 980px) {
  .contract-panel__header,
  .contract-panel__controls,
  .stats-row {
    flex-direction: column;
    align-items: stretch;
  }
  .stats-row { display: grid; grid-template-columns: 1fr; }
}
</style>
