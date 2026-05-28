<template>
  <div class="outgoing-right-panel custom-scrollbar">
    <div class="mb-4">
      <ApprovalWidget
        entity-type="outgoing_document"
        :entity-id="activeDocumentId"
        :entity-label="displayOutgoingNumber(activeDocument) || activeDocument.subject || ''"
        title="Согласование документа"
        empty-text="Сначала сохраните документ, затем можно будет запустить маршрут согласования."
        @state-changed="$emit('approval-state-changed', $event)"
        @updated="$emit('approval-updated')"
      />
    </div>
    <div class="mb-4">
      <h5 class="panel-section-title">История версий</h5>
      <div v-if="versions.length === 0" class="text-muted small">Нет версий</div>
      <div v-else class="d-flex flex-column gap-2">
        <div v-for="version in versions" :key="version.id" class="version-card">
          <div class="d-flex justify-between align-center mb-1">
            <strong>v{{ version.version_number }}</strong>
            <span class="badge badge-sm badge-secondary">{{ version.status || 'draft' }}</span>
          </div>
          <div class="small text-muted mb-1">{{ formatDateTime(version.created_at) }}</div>
          <div v-if="version.comment" class="small text-muted mb-2">{{ version.comment }}</div>
          <button
            v-if="getVersionFile(version.id, 'pdf') || version.pdf_public_url || version.pdf_path"
            class="btn btn-sm btn-link p-0 cursor-pointer"
            @click="$emit('download-version-file', version, 'pdf')"
          >
            <i class="fas fa-file-pdf mr-1"></i> Скачать PDF
          </button>
          <button
            v-if="getVersionFile(version.id, 'docx')"
            class="btn btn-sm btn-link p-0 cursor-pointer"
            @click="$emit('download-version-file', version, 'docx')"
          >
            <i class="fas fa-file-word mr-1"></i> Скачать Word
          </button>
        </div>
      </div>
    </div>

    <div>
      <h5 class="panel-section-title">Файлы</h5>
      <div v-if="files.length === 0" class="text-muted small">Нет файлов</div>
      <div v-else class="d-flex flex-column gap-2">
        <button v-for="item in files" :key="item.id" class="file-item" @click="$emit('download-file', item)">
          <i class="fas fa-file text-primary"></i>
          <span class="text-truncate small">{{ item.file_name || item.file_type }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import ApprovalWidget from '../../../components/approvals/ApprovalWidget.vue'

export default {
  name: 'OutgoingRightPanel',
  components: { ApprovalWidget },
  props: {
    activeDocument: { type: Object, default: () => ({}) },
    activeDocumentId: { default: null },
    versions: { type: Array, default: () => [] },
    files: { type: Array, default: () => [] },
    displayOutgoingNumber: { type: Function, required: true },
    formatDateTime: { type: Function, required: true },
    getVersionFile: { type: Function, required: true },
  },
  emits: ['approval-state-changed', 'approval-updated', 'download-version-file', 'download-file'],
}
</script>

<style scoped>
.outgoing-right-panel {
  width: clamp(240px, 18vw, 300px);
  flex-shrink: 0;
  padding: 16px;
  border-left: 1px solid var(--md-sys-color-outline-variant);
  background: var(--md-sys-color-surface);
  overflow: auto;
}

.panel-section-title {
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--md-sys-color-on-surface);
}

.version-card {
  padding: 10px;
  border-radius: 8px;
  background: var(--md-sys-color-surface-container-low, var(--md-sys-color-background));
  border: 1px solid var(--md-sys-color-outline-variant);
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--md-sys-color-surface-container-low, var(--md-sys-color-background));
  border: 1px solid var(--md-sys-color-outline-variant);
  cursor: pointer;
  transition: all 0.15s;
  text-decoration: none;
  color: var(--md-sys-color-on-surface);
  font-size: inherit;
  text-align: left;
  width: 100%;
}
.file-item:hover { background: var(--md-sys-color-primary-container); }

.cursor-pointer { cursor: pointer; }
.text-primary { color: var(--md-sys-color-primary); }

.custom-scrollbar::-webkit-scrollbar { width: 6px; height: 6px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(128, 128, 128, 0.3); border-radius: 3px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }

@media (max-width: 1280px) {
  .outgoing-right-panel { width: clamp(220px, 18vw, 280px); }
}

@media (max-width: 992px) {
  .outgoing-right-panel {
    width: 100%;
    border-left: none;
    border-top: 1px solid var(--md-sys-color-outline-variant);
  }
}
</style>
