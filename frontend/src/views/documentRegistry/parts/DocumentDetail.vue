<template>
  <div class="detail-panel" v-if="selectedDoc">
    <div class="detail-header">
      <div class="detail-title">
        <span>{{ getTypeIcon(selectedDoc.doc_type) }}</span>
        <h3>{{ selectedDoc.title }}</h3>
      </div>
      <div class="detail-actions">
        <button class="btn btn-sm btn-primary" @click="$emit('edit-document', selectedDoc)"><i class="fas fa-edit"></i></button>
        <button class="btn btn-sm btn-outline-danger" @click="$emit('delete-document', selectedDoc)"><i class="fas fa-trash"></i></button>
      </div>
    </div>
    <div class="detail-body">
      <div class="detail-split-view">
        <div class="detail-left">
          <div class="info-grid">
            <div class="info-item"><label>Номер</label><span>{{ selectedDoc.number || '—' }}</span></div>
            <div class="info-item"><label>Дата</label><span>{{ formatDate(selectedDoc.document_date) }}</span></div>
            <div class="info-item"><label>Тип</label><span>{{ getTypeText(selectedDoc.doc_type) }}</span></div>
            <div class="info-item"><label>Контрагент</label><span>{{ getCompanyName(selectedDoc.counterparty_id) }}</span></div>
            <div class="info-item"><label>Статус</label><span class="badge badge-sm" :class="getStatusClass(selectedDoc.status)">{{ getStatusText(selectedDoc.status) }}</span></div>
          </div>
        </div>
        <div class="detail-right">
          <div class="dispatch-timeline">
            <h4><i class="fas fa-paper-plane"></i> Отправка</h4>
            <div
              v-for="ch in channelKeys"
              :key="ch"
              class="timeline-channel"
              :class="{ active: selectedDocChannels[ch]?.enabled, expanded: expandedChannel === ch }"
            >
              <div class="timeline-row" @click="$emit('toggle-channel', ch)">
                <span class="ch-icon">{{ getChannelIcon(ch) }}</span>
                <span class="ch-name">{{ channelLabels[ch] }}</span>
                <div class="ch-line">
                  <div
                    v-if="selectedDocChannels[ch]?.enabled && selectedDocChannels[ch]?.date"
                    class="ch-dot"
                    :style="{ left: getChannelPosition(ch) + '%' }"
                  ></div>
                </div>
                <template v-if="selectedDocChannels[ch]?.enabled">
                  <span class="ch-date">{{ selectedDocChannels[ch].date }}</span>
                  <span v-if="ch === 'post' && selectedDocChannels[ch].track" class="ch-track">[{{ selectedDocChannels[ch].track }}]</span>
                  <span v-if="selectedDocChannels[ch].uploaded?.length" class="ch-files">📎{{ selectedDocChannels[ch].uploaded.length }}</span>
                </template>
                <span v-else class="ch-add">+ добавить</span>
                <i class="fas fa-chevron-down ch-arrow"></i>
              </div>
              <!-- Expanded Panel -->
              <div v-if="expandedChannel === ch" class="channel-edit-panel">
                <div class="channel-edit-row">
                  <label><input type="checkbox" v-model="selectedDocChannels[ch].enabled"> Активен</label>
                  <input type="date" v-model="selectedDocChannels[ch].date" class="form-control form-control-sm" :disabled="!selectedDocChannels[ch].enabled">
                  <input v-if="ch === 'post'" type="text" v-model="selectedDocChannels[ch].track" class="form-control form-control-sm" placeholder="Трек-номер" :disabled="!selectedDocChannels[ch].enabled">
                </div>
                <div v-if="selectedDocChannels[ch].uploaded?.length" class="channel-files-list">
                  <div v-for="file in selectedDocChannels[ch].uploaded" :key="file.path" class="channel-file">
                    <span>{{ file.name }}</span>
                    <div class="channel-file-actions">
                      <button class="btn btn-sm btn-icon" @click="$emit('download-detail-channel-file', ch, file)"><i class="fas fa-download"></i></button>
                      <button class="btn btn-sm btn-icon text-danger" @click="$emit('delete-detail-channel-file', ch, file)"><i class="fas fa-trash"></i></button>
                    </div>
                  </div>
                </div>

                <div
                  class="file-drop-zone"
                  :class="{ active: dragOverChannel === ch }"
                  @dragover.prevent="$emit('update:dragOverChannel', ch)"
                  @dragleave.prevent="$emit('update:dragOverChannel', null)"
                  @drop.prevent="$emit('handle-channel-file-drop', ch, $event)"
                >
                  <div v-if="pendingChannelFiles[ch]?.length" class="pending-files">
                    <div v-for="(file, idx) in pendingChannelFiles[ch]" :key="file.name + idx" class="pending-file">
                      <span>{{ file.name }}</span>
                      <button class="btn btn-sm btn-icon" type="button" @click="$emit('remove-pending-channel-file', ch, idx)">
                        <i class="fas fa-times"></i>
                      </button>
                    </div>
                  </div>
                  <div v-else class="drop-placeholder">
                    <span>Перетащите файлы сюда</span>
                    <label class="upload-link">
                      или выберите <input type="file" multiple @change="$emit('handle-detail-channel-upload', ch, $event)" hidden>
                    </label>
                  </div>
                </div>

                <div class="channel-actions mt-2" style="text-align: right;">
                  <button class="btn btn-primary btn-sm" @click="$emit('save-channel-changes', ch)">Сохранить</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Related Documents (Drag & Drop) -->
      <div
        class="related-docs-section"
        @dragover.prevent="$emit('update:isDropTarget', true)"
        @dragleave="$emit('update:isDropTarget', false)"
        @drop="$emit('drop-related-doc', $event)"
        :class="{ 'drop-active': isDropTarget }"
      >
        <h4><i class="fas fa-link"></i> Связанные документы</h4>
        <div v-if="selectedDocRelations.length" class="related-list">
          <div v-for="rel in selectedDocRelations" :key="rel.relationId" class="related-item">
            <span class="item-icon">{{ getTypeIcon(rel.doc_type) }}</span>
            <div class="item-content">
              <div class="item-title">
                <span v-if="rel.relationType === 'parent'" class="badge badge-warning-subtle mr-1" title="Этот документ ссылается на текущий">Родитель</span>
                {{ rel.title }}
              </div>
              <div class="item-meta">{{ rel.number || '—' }}</div>
              <div v-if="rel.relationType === 'child' && parentChannelFiles.length" class="related-channels">
                <span v-for="ch in parentChannelFiles" :key="ch.key" class="related-channel-chip">
                  {{ ch.label }}: {{ ch.count }}
                </span>
              </div>
            </div>
            <button class="btn btn-sm btn-icon text-danger" @click="$emit('remove-related-doc', rel.relationId)">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
        <div v-else class="drop-hint-area">
          <i class="fas fa-hand-point-left"></i>
          <span>Перетащите документы из списка слева</span>
        </div>
      </div>
    </div>
  </div>
  <div class="detail-panel empty" v-else>
    <i class="fas fa-file-alt fa-3x text-muted"></i>
    <p>Выберите документ</p>
  </div>
</template>

<script>
export default {
  name: 'DocumentDetail',
  props: {
    selectedDoc: { type: Object, default: null },
    selectedDocChannels: { type: Object, required: true },
    selectedDocRelations: { type: Array, required: true },
    expandedChannel: { type: String, default: null },
    channelKeys: { type: Array, required: true },
    channelLabels: { type: Object, required: true },
    pendingChannelFiles: { type: Object, required: true },
    parentChannelFiles: { type: Array, required: true },
    dragOverChannel: { type: String, default: null },
    isDropTarget: { type: Boolean, default: false },
    // Helpers passed from parent
    formatDate: { type: Function, required: true },
    getTypeIcon: { type: Function, required: true },
    getTypeText: { type: Function, required: true },
    getCompanyName: { type: Function, required: true },
    getStatusClass: { type: Function, required: true },
    getStatusText: { type: Function, required: true },
    getChannelIcon: { type: Function, required: true },
    getChannelPosition: { type: Function, required: true }
  },
  emits: [
    'edit-document',
    'delete-document',
    'toggle-channel',
    'download-detail-channel-file',
    'delete-detail-channel-file',
    'handle-channel-file-drop',
    'remove-pending-channel-file',
    'handle-detail-channel-upload',
    'save-channel-changes',
    'drop-related-doc',
    'remove-related-doc',
    'update:dragOverChannel',
    'update:isDropTarget'
  ]
}
</script>

<style scoped>
.fw-600 { font-weight: 600; }
.badge-sm { font-size: 0.75rem; padding: 0.25em 0.6em; }
.badge-warning-subtle { background-color: #fff3cd; color: #664d03; }
.badge-info-subtle { background-color: #cff4fc; color: #055160; }
.badge-success-subtle { background-color: #d1e7dd; color: #0f5132; }

/* Detail Panel */
.detail-panel {
  display: flex;
  flex-direction: column;
  background: var(--md-sys-color-surface);
  border-radius: 16px;
  border: 1px solid var(--md-sys-color-outline-variant);
  overflow: hidden;
}

.detail-panel.empty {
  align-items: center;
  justify-content: center;
  color: var(--md-sys-color-on-surface-variant);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.detail-title { display: flex; align-items: center; gap: 12px; }
.detail-title span { font-size: 1.5rem; }
.detail-title h3 { margin: 0; font-size: 1.2rem; }
.detail-actions { display: flex; gap: 8px; }

.detail-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.detail-split-view {
  display: flex;
  gap: 24px;
  align-items: flex-start;
  margin-bottom: 24px;
}

.detail-left {
  flex: 0 0 340px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-right {
  flex: 1;
  min-width: 0;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px 20px;
  background: var(--md-sys-color-surface-container);
  border-radius: 12px;
  padding: 16px;
}

.info-item label {
  display: block;
  font-size: 0.75rem;
  color: var(--md-sys-color-on-surface-variant);
  margin-bottom: 4px;
}

.info-item span { font-weight: 500; }

/* Dispatch Timeline */
.dispatch-timeline {
  background: var(--md-sys-color-surface-variant);
  border-radius: 12px;
  padding: 16px;
}

.dispatch-timeline h4 {
  margin: 0 0 12px 0;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.timeline-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  cursor: pointer;
}

.timeline-row.active { opacity: 1; }

.ch-icon { font-size: 1.1rem; }
.ch-name { width: 90px; font-size: 0.85rem; }
.ch-line { flex: 1; height: 1px; background: var(--md-sys-color-outline-variant); position: relative; margin: 0 12px; }
.timeline-channel.active .ch-line { background: var(--md-sys-color-primary); }
.ch-dot {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: inherit;
  border: 2px solid var(--md-sys-color-surface);
  box-shadow: 0 0 0 1px var(--md-sys-color-outline-variant);
}
.timeline-channel.active .ch-dot {
  box-shadow: 0 0 0 1px var(--md-sys-color-primary);
  background: var(--md-sys-color-primary);
}
.ch-date { font-size: 0.85rem; font-weight: 500; }
.ch-track { font-size: 0.75rem; color: var(--md-sys-color-on-surface-variant); }
.ch-files { font-size: 0.8rem; }
.ch-add { font-size: 0.8rem; color: var(--md-sys-color-primary); cursor: pointer; }
.ch-arrow { font-size: 0.7rem; margin-left: 8px; transition: transform 0.2s; }
.timeline-channel.expanded .ch-arrow { transform: rotate(180deg); }

.timeline-channel { border-radius: 8px; margin-bottom: 4px; }
.timeline-channel:hover { background: rgba(0,0,0,0.03); }
.timeline-channel.active { opacity: 1; }

.channel-edit-panel {
  background: var(--md-sys-color-surface);
  border-radius: 8px;
  padding: 12px;
  margin: 8px 0;
  border: 1px solid var(--md-sys-color-outline-variant);
}

.channel-edit-row {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.channel-edit-row label { display: flex; gap: 6px; align-items: center; font-size: 0.85rem; }
.channel-edit-row input[type="date"],
.channel-edit-row input[type="text"] { max-width: 160px; }

.channel-files-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.channel-file {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--md-sys-color-surface-variant);
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 0.85rem;
}
.channel-file-actions {
  display: inline-flex;
  gap: 6px;
}

/* Related Documents Section */
.related-docs-section {
  background: var(--md-sys-color-surface-variant);
  border-radius: 12px;
  padding: 16px;
  margin-top: 16px;
  border: 2px dashed transparent;
  transition: all 0.2s;
}

.related-docs-section.drop-active {
  border-color: var(--md-sys-color-primary);
  background: rgba(var(--md-sys-color-primary-rgb), 0.1);
}

.related-docs-section h4 {
  margin: 0 0 12px 0;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.related-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.related-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--md-sys-color-surface);
  border-radius: 10px;
}

.item-icon { font-size: 1.3rem; }
.item-content { flex: 1; min-width: 0; }
.item-title { font-weight: 600; font-size: 0.9rem; }
.item-meta { font-size: 0.75rem; color: var(--md-sys-color-on-surface-variant); }

.related-channels {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}

.related-channel-chip {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-primary);
  white-space: nowrap;
}

.drop-hint-area {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 20px;
  color: var(--md-sys-color-on-surface-variant);
  font-style: italic;
}

/* File Drop Zone */
.file-drop-zone {
  border: 2px dashed var(--md-sys-color-outline-variant);
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  margin-top: 10px;
  transition: all 0.2s;
  background: var(--md-sys-color-surface);
}

.file-drop-zone.active {
  border-color: var(--md-sys-color-primary);
  background: rgba(var(--md-sys-color-primary-rgb), 0.05);
}

.file-drop-zone.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.drop-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
}

.drop-placeholder:hover {
  color: var(--md-sys-color-primary);
}

.pending-file {
  background: var(--md-sys-color-surface-variant);
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 0.85rem;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

@media (max-width: 768px) {
  .detail-split-view {
    flex-direction: column;
  }

  .detail-left,
  .detail-right {
    width: 100%;
  }
}

@media (max-width: 992px) {
  .detail-panel {
    flex: 1;
  }
}
</style>
