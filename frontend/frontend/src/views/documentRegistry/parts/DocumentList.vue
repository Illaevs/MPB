<template>
  <div class="list-panel">
    <div class="list-header">
      <input
        :value="search"
        @input="$emit('update:search', $event.target.value); triggerSearch()"
        type="text"
        class="form-control form-control-sm"
        placeholder="🔍 Поиск..."
      >
      <select
        :value="selectedStatus"
        @change="$emit('update:selectedStatus', $event.target.value); changeFilters()"
        class="form-select form-select-sm"
      >
        <option value="all">Статус</option>
        <option value="draft">Проект</option>
        <option value="sent">Направлен</option>
        <option value="received">Получен</option>
      </select>
      <select
        :value="selectedType"
        @change="$emit('update:selectedType', $event.target.value); changeFilters()"
        class="form-select form-select-sm"
      >
        <option value="all">Тип</option>
        <option value="contract">📄 Договор</option>
        <option value="act">📋 Акт</option>
        <option value="outgoing_letter">✉️ Письмо</option>
      </select>
      <div class="date-range">
        <input
          :value="dateFrom"
          @change="$emit('update:dateFrom', $event.target.value); changeFilters()"
          type="date"
          class="form-control form-control-sm"
        >
        <span class="date-separator">—</span>
        <input
          :value="dateTo"
          @change="$emit('update:dateTo', $event.target.value); changeFilters()"
          type="date"
          class="form-control form-control-sm"
        >
      </div>
      <button type="button" class="btn btn-sm btn-outline-secondary" @click="clearFilters">Clear</button>
    </div>
    <div v-if="loading" class="list-loading">
      <SkeletonLoader height="48px" v-for="i in 6" :key="i" />
    </div>
    <div v-else-if="!documents.length" class="list-empty">
      <i class="fas fa-folder-open fa-2x text-muted"></i>
      <p>Нет документов</p>
    </div>
    <div v-else class="list-items">
      <div
        v-for="doc in documents"
        :key="doc.id"
        class="list-item"
        :class="{ active: selectedDoc?.id === doc.id }"
        @click="$emit('select-document', doc)"
        draggable="true"
        @dragstart="onDragStart($event, doc)"
      >
        <span class="item-icon">{{ getTypeIcon(doc.doc_type) }}</span>
        <div class="item-content">
          <div class="item-title">{{ doc.title }}</div>
          <div class="item-meta">{{ doc.number || '-' }} · {{ formatDate(doc.document_date) }}</div>
        </div>
        <button class="btn btn-sm btn-icon text-danger list-delete" @click.stop="$emit('delete-document', doc)">
          <i class="fas fa-trash"></i>
        </button>
        <span class="status-dot" :class="'status-' + doc.status"></span>
      </div>
    </div>
    <div class="list-footer">
      <button class="btn btn-sm btn-outline-secondary" :disabled="page === 1" @click="$emit('prev-page')">
        <i class="fas fa-chevron-left"></i>
      </button>
      <span>{{ page }}</span>
      <button class="btn btn-sm btn-outline-secondary" :disabled="!hasNext" @click="$emit('next-page')">
        <i class="fas fa-chevron-right"></i>
      </button>
    </div>
  </div>
</template>

<script>
import SkeletonLoader from '../../../components/ui/SkeletonLoader.vue'

export default {
  name: 'DocumentList',
  components: { SkeletonLoader },
  props: {
    documents: { type: Array, required: true },
    loading: { type: Boolean, default: false },
    selectedDoc: { type: Object, default: null },
    search: { type: String, default: '' },
    selectedStatus: { type: String, default: 'all' },
    selectedType: { type: String, default: 'all' },
    dateFrom: { type: String, default: '' },
    dateTo: { type: String, default: '' },
    page: { type: Number, default: 1 },
    hasNext: { type: Boolean, default: false },
    triggerSearch: { type: Function, required: true },
    changeFilters: { type: Function, required: true },
    clearFilters: { type: Function, required: true },
    onDragStart: { type: Function, required: true },
    getTypeIcon: { type: Function, required: true },
    formatDate: { type: Function, required: true }
  },
  emits: [
    'update:search',
    'update:selectedStatus',
    'update:selectedType',
    'update:dateFrom',
    'update:dateTo',
    'select-document',
    'delete-document',
    'prev-page',
    'next-page'
  ]
}
</script>

<style scoped>
.list-panel {
  display: flex;
  flex-direction: column;
  background: var(--md-sys-color-surface);
  border-radius: 16px;
  border: 1px solid var(--md-sys-color-outline-variant);
  overflow: hidden;
}

.list-header {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.list-header .form-control,
.list-header .form-select {
  font-size: 0.85rem;
}

.date-range {
  display: flex;
  align-items: center;
  gap: 6px;
}

.date-separator {
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.85rem;
}

.list-loading, .list-empty {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  justify-content: center;
}

.list-empty { color: var(--md-sys-color-on-surface-variant); }

.list-items {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.list-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: grab;
  transition: background 0.15s;
}

.list-item:active { cursor: grabbing; }

.list-item:hover { background: var(--md-sys-color-surface-variant); }
.list-item.active { background: rgba(var(--md-sys-color-primary-rgb), 0.12); }

.list-delete {
  margin-left: auto;
}

.item-icon { font-size: 1.3rem; }
.item-content { flex: 1; min-width: 0; }
.item-title { font-weight: 600; font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.item-meta { font-size: 0.75rem; color: var(--md-sys-color-on-surface-variant); }

.status-dot {
  width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
}
.status-dot.status-draft { background: #ffc107; }
.status-dot.status-sent { background: #17a2b8; }
.status-dot.status-received { background: #28a745; }
.status-dot.status-archived { background: #6c757d; }

.list-footer {
  padding: 8px 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
}

@media (max-width: 768px) {
  .list-header {
    flex-direction: column;
    gap: 8px;
  }

  .date-range {
    width: 100%;
  }
}

@media (max-width: 992px) {
  .list-panel {
    width: 100%;
    max-height: 300px;
  }
}
</style>
