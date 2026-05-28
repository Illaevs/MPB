<template>
  <div class="flex-grow-1 overflow-hidden d-flex flex-column">
    <div v-if="!activeDocumentId" class="flex-grow-1 d-flex align-center justify-center preview-empty">
      <div class="text-center text-muted">
        <i class="fas fa-envelope-open-text fa-3x mb-3 icon-muted"></i>
        <p>Выберите документ из списка или создайте новый</p>
      </div>
    </div>
    <div v-else class="flex-grow-1 d-flex flex-column min-h-0">
      <div class="preview-toolbar d-flex justify-between align-center gap-2 px-3 py-2 border-bottom">
        <div class="btn-group btn-group-sm">
          <button
            class="btn"
            :class="previewMode === 'fit-page' ? 'btn-primary' : 'btn-outline-secondary'"
            @click="$emit('set-preview-mode', 'fit-page')"
          >Страница</button>
          <button
            class="btn"
            :class="previewMode === 'fit-width' ? 'btn-primary' : 'btn-outline-secondary'"
            @click="$emit('set-preview-mode', 'fit-width')"
          >По ширине</button>
          <button
            class="btn"
            :class="previewMode === 'actual' ? 'btn-primary' : 'btn-outline-secondary'"
            @click="$emit('set-preview-mode', 'actual')"
          >100%</button>
        </div>
        <div class="text-muted small">Масштаб {{ previewScaleLabel }}%</div>
      </div>
      <div class="docx-preview-container flex-grow-1" :class="previewMode">
        <iframe
          v-if="previewFrameSrc"
          :src="previewFrameSrc"
          class="pdf-preview-frame"
          title="Предпросмотр документа"
        ></iframe>
      </div>
      <div v-if="!previewReady && !previewLoading && !loading" class="preview-fallback">
        <i class="fas fa-file-pdf fa-3x mb-3 icon-muted"></i>
        <p>Не удалось сформировать предпросмотр документа</p>
        <button class="btn btn-sm btn-outline-primary mt-2" @click="$emit('refresh-preview')">
          <i class="fas fa-sync"></i> Обновить предпросмотр
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'OutgoingPreview',
  props: {
    activeDocumentId: { default: null },
    previewMode: { type: String, default: 'fit-page' },
    previewFrameSrc: { type: String, default: '' },
    previewScaleLabel: { type: [String, Number], default: 100 },
    previewReady: { type: Boolean, default: false },
    previewLoading: { type: Boolean, default: false },
    loading: { type: Boolean, default: false },
  },
  emits: ['set-preview-mode', 'refresh-preview'],
}
</script>

<style scoped>
.preview-toolbar {
  background: var(--md-sys-color-surface);
  backdrop-filter: var(--glass-blur);
  position: sticky;
  top: 0;
  z-index: 5;
}

.docx-preview-container {
  position: relative;
  overflow-x: auto;
  overflow-y: auto;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 16px 12px 28px;
  background: #dfe3e8;
  min-height: 0;
}
.docx-preview-container.fit-page,
.docx-preview-container.actual { align-items: flex-start; }
.docx-preview-container.fit-width { overflow-x: auto; overflow-y: auto; }

.pdf-preview-frame {
  width: 100%;
  height: 100%;
  min-height: 100%;
  border: 0;
  background: #ffffff;
  border-radius: 12px;
}

.preview-empty { background: var(--md-sys-color-background); }

.preview-fallback {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--md-sys-color-on-surface-variant);
  pointer-events: none;
}
.preview-fallback button { pointer-events: all; }

.icon-muted {
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.5;
}

.min-h-0 { min-height: 0; }
</style>
