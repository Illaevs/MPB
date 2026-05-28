<template>
  <div>
    <!-- Draft restore -->
    <Teleport to="body">
      <div v-if="draftRestoreModalOpen" class="modal-overlay">
        <div class="modal-glass">
          <div class="modal-glass-header">
            <h5 class="m-0">Найден локальный черновик</h5>
          </div>
          <div class="modal-glass-body">
            <p class="mb-2">
              Для этого письма найден локальный черновик, сохраненный
              <strong>{{ formatDateTime(draftRestoreCandidate?.saved_at) }}</strong>.
            </p>
            <p v-if="draftRestoreReason === 'session_expired'" class="draft-restore-alert mb-2">
              Сеанс истек во время сохранения. Текст письма сохранен локально.
            </p>
            <p v-if="draftRestoreCandidate?.pending_file_names?.length" class="text-muted small mb-0">
              Файлы из локального черновика автоматически не восстанавливаются. Их нужно будет прикрепить заново.
            </p>
          </div>
          <div class="modal-glass-footer">
            <button class="btn btn-outline-secondary btn-sm" @click="$emit('discard-draft-restore')">
              Оставить версию из системы
            </button>
            <button class="btn btn-primary btn-sm" @click="$emit('apply-draft-restore')">
              Восстановить черновик
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Delete confirm -->
    <Teleport to="body">
      <div v-if="deleteModalOpen" class="modal-overlay" @click.self="$emit('close-delete')">
        <div class="modal-glass">
          <div class="modal-glass-header">
            <h5 class="m-0">Удалить документ?</h5>
            <button class="btn btn-sm btn-icon btn-ghost" @click="$emit('close-delete')">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="modal-glass-body">
            <p class="m-0">Все версии и файлы будут удалены. Это действие необратимо.</p>
          </div>
          <div class="modal-glass-footer">
            <button class="btn btn-outline-secondary btn-sm" @click="$emit('close-delete')">Отмена</button>
            <button class="btn btn-danger btn-sm" @click="$emit('confirm-delete')">
              <i class="fas fa-trash mr-1"></i> Удалить
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Sequences -->
    <Teleport to="body">
      <div v-if="sequencesModalOpen" class="modal-overlay" @click.self="$emit('close-sequences')">
        <div class="modal-glass">
          <div class="modal-glass-header">
            <h5 class="m-0">Нумерация: {{ activeKindMeta.singular }}</h5>
            <button class="btn btn-sm btn-icon btn-ghost" @click="$emit('close-sequences')">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="modal-glass-body">
            <div v-if="sequenceLoading" class="d-flex justify-center py-4">
              <div class="spinner"></div>
            </div>
            <div v-else-if="sequences.length" class="d-flex flex-column gap-3">
              <div v-for="row in sequences" :key="row.our_company_key" class="d-flex align-center gap-3">
                <div class="flex-grow-1">
                  <div class="fw-600">{{ row.label }}</div>
                  <div class="text-muted small">
                    Следующий номер<span v-if="row.display_number">: {{ row.display_number }}</span>
                  </div>
                </div>
                <input
                  :value="sequenceForm[row.our_company_key]"
                  type="number"
                  class="form-control"
                  min="1"
                  style="width: 140px;"
                  @input="updateSequenceForm(row.our_company_key, $event.target.value === '' ? null : Number($event.target.value))"
                />
              </div>
            </div>
            <div v-else class="text-muted small py-3">
              Для этого типа документа номер считается из выбранного договора или не настраивается вручную.
            </div>
          </div>
          <div class="modal-glass-footer">
            <button class="btn btn-outline-secondary btn-sm" @click="$emit('close-sequences')">Закрыть</button>
            <button class="btn btn-primary btn-sm" :disabled="sequenceSaving" @click="$emit('save-sequences')">
              <i v-if="sequenceSaving" class="fas fa-spinner fa-spin mr-1"></i>
              Сохранить
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Table modal -->
    <Teleport to="body">
      <div v-if="tableModalOpen" class="modal-overlay" @click.self="$emit('close-table-modal')">
        <div class="modal-glass">
          <div class="modal-glass-header">
            <h5 class="m-0">Вставить таблицу</h5>
            <button type="button" class="btn-ghost" @click="$emit('close-table-modal')">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="modal-glass-body">
            <div class="d-flex gap-2 mb-3">
              <div class="form-group w-50 mb-0">
                <label>Строк</label>
                <input :value="tableForm.rows" type="number" min="1" max="20" class="form-control" @input="updateTableForm('rows', Number($event.target.value))" />
              </div>
              <div class="form-group w-50 mb-0">
                <label>Столбцов</label>
                <input :value="tableForm.cols" type="number" min="1" max="10" class="form-control" @input="updateTableForm('cols', Number($event.target.value))" />
              </div>
            </div>
            <label class="d-flex align-center gap-2 cursor-pointer">
              <input :checked="tableForm.includeHeader" type="checkbox" @change="updateTableForm('includeHeader', $event.target.checked)" />
              <span>Добавить строку заголовков</span>
            </label>
          </div>
          <div class="modal-glass-footer">
            <button type="button" class="btn btn-secondary" @click="$emit('close-table-modal')">Отмена</button>
            <button type="button" class="btn btn-primary" @click="$emit('insert-table')">Вставить</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Floating table controls -->
    <Teleport to="body">
      <div
        v-if="tableControls.visible"
        class="editor-table-controls"
        :style="{ left: `${tableControls.left}px`, top: `${tableControls.top}px` }"
        @mouseenter="$emit('table-controls-enter')"
        @mouseleave="$emit('table-controls-leave')"
      >
        <button type="button" class="editor-table-controls__btn" title="Добавить строку ниже" @click="$emit('add-table-row')">
          <i class="fas fa-plus"></i><span>Строка</span>
        </button>
        <button type="button" class="editor-table-controls__btn" title="Добавить столбец справа" @click="$emit('add-table-column')">
          <i class="fas fa-plus"></i><span>Столбец</span>
        </button>
        <button
          type="button"
          class="editor-table-controls__btn editor-table-controls__btn--danger"
          title="Удалить строку"
          :disabled="!tableControls.canDeleteRow"
          @click="$emit('remove-table-row')"
        >
          <i class="fas fa-minus"></i><span>Строка</span>
        </button>
        <button
          type="button"
          class="editor-table-controls__btn editor-table-controls__btn--danger"
          title="Удалить столбец"
          :disabled="!tableControls.canDeleteCol"
          @click="$emit('remove-table-column')"
        >
          <i class="fas fa-minus"></i><span>Столбец</span>
        </button>
      </div>
    </Teleport>
  </div>
</template>

<script>
export default {
  name: 'OutgoingModals',
  props: {
    draftRestoreModalOpen: { type: Boolean, default: false },
    draftRestoreCandidate: { type: Object, default: null },
    draftRestoreReason: { type: String, default: '' },
    deleteModalOpen: { type: Boolean, default: false },
    sequencesModalOpen: { type: Boolean, default: false },
    sequenceLoading: { type: Boolean, default: false },
    sequenceSaving: { type: Boolean, default: false },
    sequences: { type: Array, default: () => [] },
    sequenceForm: { type: Object, default: () => ({}) },
    activeKindMeta: { type: Object, required: true },
    tableModalOpen: { type: Boolean, default: false },
    tableForm: { type: Object, default: () => ({ rows: 2, cols: 3, includeHeader: true }) },
    tableControls: { type: Object, default: () => ({ visible: false, left: 0, top: 0, canDeleteRow: false, canDeleteCol: false }) },
    formatDateTime: { type: Function, required: true },
  },
  emits: [
    'apply-draft-restore', 'discard-draft-restore',
    'close-delete', 'confirm-delete',
    'close-sequences', 'save-sequences', 'update:sequenceForm',
    'close-table-modal', 'insert-table', 'update:tableForm',
    'table-controls-enter', 'table-controls-leave',
    'add-table-row', 'add-table-column', 'remove-table-row', 'remove-table-column',
  ],
  setup(props, { emit }) {
    const updateSequenceForm = (key, value) => {
      emit('update:sequenceForm', { ...props.sequenceForm, [key]: value })
    }
    const updateTableForm = (key, value) => {
      emit('update:tableForm', { ...props.tableForm, [key]: value })
    }
    return { updateSequenceForm, updateTableForm }
  },
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2100;
  animation: fadeIn 0.15s ease;
}
.modal-glass {
  width: 480px;
  max-width: 90vw;
  background: var(--md-sys-color-surface-thick, var(--md-sys-color-surface));
  backdrop-filter: var(--glass-blur);
  border-radius: 16px;
  border: 1px solid var(--glass-border-light, rgba(255, 255, 255, 0.3));
  box-shadow: var(--shadow-md, 0 12px 32px rgba(0, 0, 0, 0.15));
  display: flex;
  flex-direction: column;
  animation: scaleIn 0.2s ease;
}
.modal-glass-header {
  padding: 14px 18px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.modal-glass-body {
  padding: 18px;
  max-height: 60vh;
  overflow: auto;
}
.modal-glass-footer {
  padding: 12px 18px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}
.btn-ghost {
  background: none;
  border: none;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.15s;
}
.btn-ghost:hover { background: var(--md-sys-color-surface-container); }

.draft-restore-alert {
  padding: 10px 12px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--md-sys-color-error-container) 70%, transparent);
  color: var(--md-sys-color-on-error-container, var(--md-sys-color-error));
  font-size: 0.9rem;
}

.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--md-sys-color-outline-variant);
  border-top-color: var(--md-sys-color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.editor-table-controls {
  position: fixed;
  z-index: 2200;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 14px;
  background: color-mix(in srgb, var(--md-sys-color-surface) 94%, white 6%);
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.18);
  backdrop-filter: blur(10px);
}
.editor-table-controls__btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 10px;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 10px;
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-on-surface);
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 600;
  transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
}
.editor-table-controls__btn:hover:not(:disabled) {
  background: var(--md-sys-color-primary-container);
  border-color: var(--md-sys-color-primary);
  transform: translateY(-1px);
}
.editor-table-controls__btn--danger:hover:not(:disabled) {
  background: rgba(220, 38, 38, 0.12);
  border-color: rgba(220, 38, 38, 0.35);
  color: #b91c1c;
}
.editor-table-controls__btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  transform: none;
}

@keyframes spin { to { transform: rotate(360deg); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes scaleIn { from { transform: scale(0.95); opacity: 0; } to { transform: scale(1); opacity: 1; } }
</style>
