<template>
  <div>
    <!-- Top bar (breadcrumb) -->
    <div class="contract-topbar">
      <nav class="breadcrumbs contract-breadcrumbs">
        <router-link to="/contracts" class="breadcrumb-link">Договоры</router-link>
        <i class="fas fa-chevron-right breadcrumb-sep"></i>
        <span class="breadcrumb-current">{{ contract?.contract_number || 'Загрузка...' }}</span>
      </nav>
    </div>

    <!-- Hero (left) + financial stats (right) -->
    <div class="header-row contract-shell mb-2">
      <div class="header-info contract-hero">
        <div class="d-flex align-center gap-2 flex-wrap mb-1 contract-hero__headline">
          <h2 class="m-0">Договор {{ contract?.contract_number || '' }}</h2>

          <!-- Inline status editor -->
          <div v-if="contract?.status" class="contract-status-wrap">
            <button
              type="button"
              class="cd-status-badge cd-status-badge--editable"
              :class="`cd-status-${contract.status}`"
              :disabled="statusBusy"
              @click="$emit('toggle-status-menu')"
            >
              <span class="cd-status-dot"></span>{{ contractStatusLabel(contract.status) }}
              <i v-if="statusBusy" class="fas fa-spinner fa-spin ml-1"></i>
              <i v-else class="fas fa-caret-down ml-1"></i>
            </button>
            <transition name="cd-pop">
              <div v-if="statusMenuOpen" class="cd-status-menu" v-click-outside="() => $emit('close-status-menu')">
                <button
                  v-for="opt in cdStatusOptions"
                  :key="opt.value"
                  type="button"
                  class="cd-status-menu__item"
                  :class="[`cd-status-${opt.value}`, { active: contract.status === opt.value }]"
                  @click="$emit('change-status', opt.value)"
                >
                  <span class="cd-status-dot"></span>{{ opt.label }}
                  <i v-if="contract.status === opt.value" class="fas fa-check ml-auto"></i>
                </button>
              </div>
            </transition>
          </div>

          <span v-if="contract?.contract_type" class="cd-type-badge" :class="`cd-type-${contract.contract_type}`">
            {{ contractTypeLabel(contract.contract_type) }}
          </span>
        </div>
        <div class="text-muted small contract-hero__meta">
          <span v-if="contract?.contract_date">Дата: {{ formatDate(contract.contract_date) }}</span>
          <span v-if="contract?.deal_id || dealTitle">
            Сделка:
            <router-link v-if="contract?.deal_id" :to="`/deals?deal_id=${contract.deal_id}`" class="cd-meta-link">
              {{ dealTitle || '—' }}
            </router-link>
            <template v-else>{{ dealTitle || '—' }}</template>
          </span>
          <span v-if="subcontractorTitle">Субподрядчик: {{ subcontractorTitle }}</span>
          <span v-if="contract?.customer_id || customerName">
            Заказчик:
            <router-link v-if="contract?.customer_id" :to="`/companies?company_id=${contract.customer_id}`" class="cd-meta-link">
              {{ customerName || '—' }}
            </router-link>
            <template v-else>{{ customerName || '—' }}</template>
          </span>
          <span v-if="contract?.executor_id || executorName">
            Исполнитель:
            <router-link v-if="contract?.executor_id" :to="`/companies?company_id=${contract.executor_id}`" class="cd-meta-link">
              {{ executorName || '—' }}
            </router-link>
            <template v-else>{{ executorName || '—' }}</template>
          </span>
          <span v-if="contract?.amount">Сумма: {{ formatAmount(contract.amount) }}</span>
        </div>
      </div>

      <div class="header-stats contract-stats">
        <div class="contract-stats__topline">
          <span class="contract-stats__caption">Финансовая сводка</span>
          <strong>{{ paymentCompletionPercent }}%</strong>
        </div>
        <div class="stats-row">
          <div class="stat-box text-center contract-stat">
            <small class="text-muted d-block">Всего</small>
            <span class="fw-600 stat-value" :class="paymentSummary.total_amount > 0 ? 'text-primary' : 'text-muted'">{{ formatAmount(paymentSummary.total_amount) }}</span>
          </div>
          <div class="stat-box text-center contract-stat">
            <small class="text-muted d-block">Оплачено</small>
            <span class="fw-600 stat-value" :class="paymentSummary.paid_amount > 0 ? 'text-success' : 'text-muted'">{{ formatAmount(paymentSummary.paid_amount) }}</span>
          </div>
          <div class="stat-box text-center contract-stat">
            <small class="text-muted d-block">Ожидает</small>
            <span class="fw-600 stat-value" :class="paymentSummary.pending_amount > 0 ? 'text-warning' : 'text-muted'">{{ formatAmount(paymentSummary.pending_amount) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { cdClickOutside } from '../composables/useContractDetailState'

export default {
  name: 'ContractHeader',
  directives: { 'click-outside': cdClickOutside },
  props: {
    contract: { type: Object, default: null },
    dealTitle: { type: String, default: '' },
    subcontractorTitle: { type: String, default: '' },
    customerName: { type: String, default: '' },
    executorName: { type: String, default: '' },
    paymentSummary: { type: Object, required: true },
    paymentCompletionPercent: { type: Number, default: 0 },
    statusMenuOpen: Boolean,
    statusBusy: Boolean,
    cdStatusOptions: { type: Array, required: true },
    contractStatusLabel: { type: Function, required: true },
    contractTypeLabel: { type: Function, required: true },
    formatDate: { type: Function, required: true },
    formatAmount: { type: Function, required: true },
  },
  emits: ['toggle-status-menu', 'close-status-menu', 'change-status']
}
</script>

<style scoped>
.cd-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
  border: 1px solid currentColor;
}
.cd-status-badge--editable {
  cursor: pointer;
  background: transparent;
}
.cd-status-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.85;
  flex-shrink: 0;
}
.cd-status-approval    { background: rgba(245,158,11,0.15); color: #b45309; }
.cd-status-in_progress { background: rgba(59,130,246,0.15); color: #1d4ed8; }
.cd-status-completed   { background: rgba(34,197,94,0.15); color: #166534; }
.cd-status-badge--editable .fa-caret-down { font-size: 0.6rem; opacity: 0.7; }

.contract-status-wrap { position: relative; display: inline-block; }
.cd-status-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  z-index: 100;
  background: var(--md-sys-color-surface, #fff);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 10px;
  padding: 4px;
  min-width: 200px;
  box-shadow: 0 12px 28px rgba(0,0,0,0.14);
}
.cd-status-menu__item {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 6px 10px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.82rem;
  text-align: left;
}
.cd-status-menu__item:hover { background: var(--md-sys-color-surface-variant, rgba(0,0,0,0.05)); }
.cd-status-menu__item.active { font-weight: 600; }
.cd-status-menu__item.cd-status-approval    { color: #b45309; }
.cd-status-menu__item.cd-status-in_progress { color: #1d4ed8; }
.cd-status-menu__item.cd-status-completed   { color: #166534; }
.cd-pop-enter-active, .cd-pop-leave-active { transition: opacity 0.12s ease, transform 0.12s ease; }
.cd-pop-enter-from, .cd-pop-leave-to { opacity: 0; transform: translateY(-4px); }
.ml-auto { margin-left: auto; }

.cd-type-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  white-space: nowrap;
}
.cd-type-general_contractor { background: rgba(2,119,189,0.15); color: #01579b; }
.cd-type-subcontractor      { background: rgba(245,124,0,0.15); color: #bf360c; }
.cd-type-services           { background: rgba(0,137,123,0.15); color: #00695c; }
.cd-type-labor              { background: rgba(106,27,154,0.15); color: #4a148c; }

.cd-meta-link {
  text-decoration: none;
  color: var(--md-sys-color-on-surface);
  display: inline-block;
  max-width: 100%;
}
.cd-meta-link strong { color: var(--md-sys-color-primary, #1976d2); }
.cd-meta-link:hover strong { text-decoration: underline; }

.contract-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 58px;
  padding: 0;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
}
.contract-breadcrumbs { margin: 0; }

.contract-shell {
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(336px, 0.58fr);
  gap: 22px;
  align-items: start;
}

.contract-hero,
.contract-stats {
  min-height: 100%;
}

.contract-hero {
  padding: 2px 0 0 !important;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 16px;
}

.contract-hero__headline h2 {
  font-size: 2.05rem;
  line-height: 1.08;
  font-weight: 800;
  color: #0f2747;
}

.contract-hero__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 24px;
  color: #74839a;
  padding: 14px 18px 12px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: 12px;
  background: #f7f9fc;
}

.contract-hero__meta span {
  display: inline-flex;
  align-items: center;
  min-height: auto;
  padding: 0;
  border-radius: 0;
  background: transparent;
  border: none;
  gap: 6px;
}

.contract-hero__meta span::before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: #cbd5e1;
  flex: 0 0 auto;
}

.breadcrumbs {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.875rem;
}
.breadcrumb-link {
  color: #2563eb;
  text-decoration: none;
  font-weight: 600;
}
.breadcrumb-link:hover { text-decoration: underline; }
.breadcrumb-sep { font-size: 0.65rem; color: #9aa4b2; }
.breadcrumb-current { color: #687385; font-weight: 600; }

.contract-stats {
  padding: 16px 18px 14px !important;
  min-width: 336px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
}

.contract-stats__topline {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.contract-stats__caption {
  color: #6d7b90;
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0;
  height: 100%;
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

.stat-value {
  font-size: 1.02rem;
  line-height: 1.15;
}

@media (max-width: 1200px) {
  .contract-shell {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 980px) {
  .stats-row {
    display: grid;
    grid-template-columns: 1fr;
  }
  .contract-topbar {
    flex-direction: column;
    align-items: stretch;
  }
}
@media (max-width: 768px) {
  .contract-hero__headline h2 {
    font-size: 1.55rem;
  }
}
</style>
