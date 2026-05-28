<template>
  <div class="tabs-container contract-subtoolbar mb-2">
    <div class="contract-segmented" role="tablist" aria-label="Вкладки договора">
      <button
        class="contract-segmented__button"
        :class="{ 'contract-segmented__button--active': activeTab === 'data' }"
        @click="$emit('set-tab', 'data')"
      >
        Данные
      </button>
      <button
        v-if="isServiceContract"
        class="contract-segmented__button"
        :class="{ 'contract-segmented__button--active': activeTab === 'expenses' }"
        @click="$emit('set-tab', 'expenses')"
      >
        Расходная карточка
      </button>
      <button
        class="contract-segmented__button"
        :class="{ 'contract-segmented__button--active': activeTab === 'documents' }"
        @click="$emit('set-tab', 'documents')"
      >
        Документы
      </button>
    </div>

    <div v-if="activeTab === 'data'" class="contract-subtoolbar__actions">
      <div class="contract-toolbar-search">
        <i class="fas fa-search"></i>
        <input
          :value="paymentFilters.search"
          type="text"
          class="form-control form-control-sm"
          placeholder="Поиск по названию или контрагенту"
          @input="updatePaymentFilter('search', $event.target.value)"
        />
      </div>
      <div class="contract-toolbar-select contract-toolbar-select--icon">
        <i class="fas fa-filter"></i>
        <select :value="paymentFilters.direction" class="form-control form-control-sm" @change="updatePaymentFilter('direction', $event.target.value)">
          <option value="">Все типы</option>
          <option value="income">Доход</option>
          <option value="expense">Расход</option>
        </select>
      </div>
      <div class="contract-toolbar-select">
        <select :value="paymentFilters.status" class="form-control form-control-sm" @change="updatePaymentFilter('status', $event.target.value)">
          <option value="">Все статусы</option>
          <option value="unpaid">Не оплачено</option>
          <option value="partial">Частично</option>
          <option value="paid">Оплачено</option>
        </select>
      </div>
      <button class="btn btn-sm contract-toolbar-icon-btn" @click="$emit('reset-payment-filters')" title="Сброс фильтров">
        <i class="fas fa-times"></i>
      </button>
    </div>

    <div v-else-if="activeTab === 'documents'" class="contract-subtoolbar__actions">
      <div class="contract-toolbar-search">
        <i class="fas fa-search"></i>
        <input
          :value="documentFilters.search"
          type="text"
          class="form-control form-control-sm"
          placeholder="Поиск по названию или номеру"
          @input="updateDocumentFilter('search', $event.target.value)"
        />
      </div>
      <div class="contract-toolbar-select contract-toolbar-select--icon">
        <i class="fas fa-filter"></i>
        <select :value="documentFilters.docType" class="form-control form-control-sm" @change="updateDocumentFilter('docType', $event.target.value)">
          <option value="">Все типы</option>
          <option v-for="type in docTypes" :key="type.key" :value="type.key">
            {{ type.label }}
          </option>
        </select>
      </div>
      <div class="contract-toolbar-select">
        <select :value="documentFilters.status" class="form-control form-control-sm" @change="updateDocumentFilter('status', $event.target.value)">
          <option value="">Все статусы</option>
          <option value="draft">Черновик</option>
          <option value="signing">На подписании</option>
          <option value="signed">Подписан</option>
          <option value="canceled">Аннулирован</option>
        </select>
      </div>
      <button class="btn btn-sm contract-toolbar-icon-btn" @click="$emit('reset-document-filters')" title="Сброс фильтров">
        <i class="fas fa-times"></i>
      </button>
      <span class="contract-toolbar-divider" aria-hidden="true"></span>
      <button class="btn btn-sm contract-toolbar-btn contract-toolbar-btn--primary" @click="$emit('open-upload', 'contract')">
        <i class="fas fa-plus"></i> Добавить документ
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ContractToolbar',
  props: {
    activeTab: { type: String, required: true },
    isServiceContract: Boolean,
    paymentFilters: { type: Object, required: true },
    documentFilters: { type: Object, required: true },
    docTypes: { type: Array, required: true },
  },
  emits: ['set-tab', 'reset-payment-filters', 'reset-document-filters', 'open-upload', 'update-payment-filter', 'update-document-filter'],
  methods: {
    updatePaymentFilter(key, value) {
      this.$emit('update-payment-filter', { key, value })
    },
    updateDocumentFilter(key, value) {
      this.$emit('update-document-filter', { key, value })
    }
  }
}
</script>

<style scoped>
.contract-toolbar-btn,
.contract-toolbar-icon-btn {
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
  box-shadow: none;
  transition: border-color 0.18s ease, background 0.18s ease;
}
.contract-toolbar-btn:hover,
.contract-toolbar-icon-btn:hover {
  transform: none;
  box-shadow: none;
  background: #f8fafc;
}
.contract-toolbar-btn--primary {
  background: #111827;
  border-color: #111827;
  color: #fff;
  padding-inline: 16px;
}

.contract-subtoolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 4px 0 8px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
}

.contract-subtoolbar__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
  margin-left: auto;
}

.contract-toolbar-search,
.contract-toolbar-select {
  position: relative;
  display: flex;
  align-items: center;
}

.contract-toolbar-search { min-width: 208px; }

.contract-toolbar-search i,
.contract-toolbar-select--icon i {
  position: absolute;
  left: 12px;
  color: #9aa4b2;
  font-size: 0.82rem;
  pointer-events: none;
}

.contract-toolbar-search .form-control { padding-left: 34px !important; min-width: 208px; }
.contract-toolbar-select--icon .form-control { padding-left: 34px !important; }
.contract-toolbar-select .form-control { min-width: 156px; }

.contract-toolbar-divider {
  width: 1px;
  height: 24px;
  background: rgba(15, 23, 42, 0.12);
}

.contract-segmented {
  display: inline-flex;
  align-items: center;
  gap: 26px;
  padding: 0;
  border-radius: 0;
  background: transparent;
}
.contract-segmented__button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 42px;
  padding: 0 1px;
  border: none;
  border-radius: 0;
  background: transparent;
  color: #66768b;
  font-weight: 600;
  border-bottom: 2px solid transparent;
  transition: color 0.18s ease, border-color 0.18s ease;
}
.contract-segmented__button--active {
  background: transparent;
  color: #2563eb;
  border-bottom-color: #2563eb;
  box-shadow: none;
}

:deep(.form-control), :deep(.form-select) {
  min-height: 36px;
  border-radius: 10px;
  border-color: rgba(15, 23, 42, 0.12);
  background: #fff;
  box-shadow: none;
}

@media (max-width: 1200px) {
  .contract-subtoolbar {
    flex-direction: column;
    align-items: stretch;
  }
}
@media (max-width: 980px) {
  .contract-subtoolbar__actions {
    flex-direction: column;
    align-items: stretch;
  }
}
@media (max-width: 768px) {
  .contract-segmented {
    width: 100%;
    overflow-x: auto;
    gap: 16px;
    padding: 0;
  }
  .contract-segmented__button { white-space: nowrap; }
}
</style>
