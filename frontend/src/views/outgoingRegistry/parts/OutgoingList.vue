<template>
  <aside class="outgoing-sidebar card d-flex flex-column h-100 mb-0">
    <div class="card-header border-bottom">
      <div class="d-flex justify-between align-center">
        <div>
          <h3 class="m-0 sidebar-title">Исходящие</h3>
          <small class="text-muted">{{ activeKindMeta.subtitle }}</small>
        </div>
        <button class="btn btn-sm btn-primary btn-icon" :title="`Новый документ: ${activeKindMeta.singular}`" @click="$emit('start-new')">
          <i class="fas fa-plus"></i>
        </button>
      </div>
    </div>
    <div class="outgoing-filters border-bottom p-2">
      <div class="form-group mb-2">
        <input
          :value="filters.search"
          type="text"
          class="form-control form-control-sm"
          placeholder="Поиск по номеру, теме, компании"
          @input="updateFilter('search', $event.target.value)"
          @keyup.enter="$emit('apply-filters')"
        />
      </div>
      <div class="d-flex gap-2 mb-2">
        <select :value="filters.status" class="form-control form-control-sm" @change="updateFilter('status', $event.target.value)">
          <option value="">Все статусы</option>
          <option value="draft">Черновик</option>
          <option value="sent">Отправлено</option>
        </select>
        <select :value="filters.our_company_key" class="form-control form-control-sm" @change="updateFilter('our_company_key', $event.target.value)">
          <option value="">Наша компания</option>
          <option v-for="company in ourCompanies" :key="company.value" :value="company.value">{{ company.label }}</option>
        </select>
      </div>
      <div class="form-group mb-2">
        <select :value="filters.recipient_company_id" class="form-control form-control-sm" @change="updateFilter('recipient_company_id', $event.target.value)">
          <option value="">Получатель</option>
          <option v-for="company in companies" :key="company.id" :value="company.id">{{ company.name }}</option>
        </select>
      </div>
      <div class="d-flex gap-2 mb-2">
        <input :value="filters.date_from" type="date" class="form-control form-control-sm" @input="updateFilter('date_from', $event.target.value)" />
        <input :value="filters.date_to" type="date" class="form-control form-control-sm" @input="updateFilter('date_to', $event.target.value)" />
      </div>
      <div class="d-flex gap-2">
        <button class="btn btn-sm btn-primary flex-grow-1" @click="$emit('apply-filters')">Найти</button>
        <button class="btn btn-sm btn-outline-secondary flex-grow-1" @click="$emit('reset-filters')">Сбросить</button>
      </div>
    </div>

    <div v-if="loading" class="d-flex justify-center py-4">
      <div class="spinner"></div>
    </div>

    <div
      v-else
      class="flex-grow-1 overflow-auto p-2 custom-scrollbar"
      tabindex="0"
      @keydown="$emit('list-keydown', $event)"
    >
      <div
        v-for="(doc, idx) in documents"
        :key="doc.id"
        class="letter-card"
        :class="{ 'active': doc.id === activeDocumentId }"
        :data-index="idx"
        @click="$emit('select-document', doc.id)"
      >
        <div class="letter-card-header">
          <div class="d-flex align-center gap-2">
            <i class="fas text-primary" :class="documentKindMeta(doc).icon"></i>
            <span class="letter-number">{{ displayOutgoingNumber(doc) }}</span>
          </div>
          <div class="d-flex align-center gap-2">
            <span class="status-dot" :class="doc.status === 'sent' ? 'sent' : 'draft'" :title="doc.status === 'sent' ? 'Отправлено' : 'Черновик'"></span>
            <small class="text-muted">{{ formatDate(doc.letter_date) }}</small>
          </div>
        </div>
        <div class="letter-subject-line">{{ doc.subject || 'Без темы' }}</div>
        <div class="letter-card-footer">
          <span class="letter-recipient">{{ doc.recipient_company_name || 'Без получателя' }}</span>
          <div class="letter-badges">
            <span v-if="doc.files_count" class="mini-badge" title="Приложения"><i class="fas fa-paperclip"></i> {{ doc.files_count }}</span>
            <span v-if="doc.versions_count > 1" class="mini-badge" title="Версии">v{{ doc.versions_count }}</span>
          </div>
        </div>
      </div>
    </div>
    <div class="outgoing-pagination border-top p-2 d-flex justify-between align-center">
      <button class="btn btn-sm btn-outline-secondary" :disabled="page <= 1" @click="$emit('prev-page')">
        <i class="fas fa-chevron-left"></i>
      </button>
      <span class="text-muted small">Страница {{ page }}</span>
      <button class="btn btn-sm btn-outline-secondary" :disabled="!hasNext" @click="$emit('next-page')">
        <i class="fas fa-chevron-right"></i>
      </button>
    </div>
  </aside>
</template>

<script>
export default {
  name: 'OutgoingList',
  props: {
    documents: { type: Array, required: true },
    loading: { type: Boolean, default: false },
    filters: { type: Object, required: true },
    companies: { type: Array, required: true },
    ourCompanies: { type: Array, required: true },
    activeDocumentId: { default: null },
    activeKindMeta: { type: Object, required: true },
    documentKindMeta: { type: Function, required: true },
    displayOutgoingNumber: { type: Function, required: true },
    formatDate: { type: Function, required: true },
    page: { type: Number, required: true },
    hasNext: { type: Boolean, default: false },
  },
  emits: [
    'update:filters', 'apply-filters', 'reset-filters',
    'start-new', 'select-document', 'list-keydown',
    'prev-page', 'next-page',
  ],
  setup(props, { emit }) {
    const updateFilter = (key, value) => {
      emit('update:filters', { ...props.filters, [key]: value })
    }
    return { updateFilter }
  },
}
</script>

<style scoped>
.outgoing-sidebar { min-width: 0; }

.outgoing-filters {
  background: var(--md-sys-color-surface);
  backdrop-filter: var(--glass-blur);
}
.outgoing-filters .form-control-sm {
  font-size: 0.8rem;
  padding: 0.25rem 0.5rem;
}

.card-header { padding: 10px 14px; }
.sidebar-title { font-size: 1.1rem; }

.letter-card {
  padding: 10px;
  margin-bottom: 8px;
  border-radius: 10px;
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline-variant);
  cursor: pointer;
  transition: all 0.2s;
}
.letter-card:hover {
  background: var(--md-sys-color-surface-container-low);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}
.letter-card.active {
  background: var(--md-sys-color-primary-container);
  border-color: var(--md-sys-color-primary);
}
.letter-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.letter-number { font-weight: 600; font-size: 0.9rem; }
.letter-subject-line {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 6px;
}
.letter-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.letter-recipient {
  font-size: 0.8rem;
  color: var(--md-sys-color-on-surface-variant);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 60%;
}
.letter-badges { display: flex; gap: 6px; }
.mini-badge {
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 500;
  background: var(--md-sys-color-surface-container);
  color: var(--md-sys-color-on-surface-variant);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.status-dot.draft { background: var(--md-sys-color-on-surface-variant); opacity: 0.5; }
.status-dot.sent { background: var(--color-success); }

.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--md-sys-color-outline-variant);
  border-top-color: var(--md-sys-color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.text-primary { color: var(--md-sys-color-primary); }

.custom-scrollbar::-webkit-scrollbar { width: 6px; height: 6px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(128, 128, 128, 0.3); border-radius: 3px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
</style>
