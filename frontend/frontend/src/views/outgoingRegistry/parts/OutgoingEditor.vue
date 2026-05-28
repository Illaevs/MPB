<template>
  <div class="flex-grow-1 overflow-auto p-4 custom-scrollbar">
    <!-- Row 1: Recipient + Our company + Pull -->
    <div v-if="!isLetterKind" class="outgoing-form-row mb-3">
      <div class="form-group" style="flex: 2;">
        <label>Получатель</label>
        <CompanySmartSelect
          :model-value="form.recipient_company_id"
          :options="companies"
          placeholder="Найти получателя"
          @update:model-value="updateForm('recipient_company_id', $event)"
        />
      </div>
      <div class="form-group" style="flex: 1;">
        <label>Наша компания</label>
        <select :value="form.our_company_key" class="form-control" :disabled="ourCompanyLocked" @change="updateForm('our_company_key', $event.target.value)">
          <option v-for="company in ourCompanies" :key="company.value" :value="company.value">{{ company.label }}</option>
        </select>
        <small v-if="ourCompanyLocked" class="text-muted">Фиксируется после создания</small>
      </div>
      <div class="form-group" style="flex: 0 0 auto; align-self: flex-end;">
        <button
          class="btn btn-sm btn-outline-secondary"
          type="button"
          :disabled="!form.recipient_company_id"
          title="Заполнит поля ниже по контрагенту"
          @click="$emit('fill-recipient')"
        >
          <i class="fas fa-database mr-1"></i> Подгрузить
        </button>
      </div>
    </div>

    <!-- Row 2: recipient details -->
    <div class="outgoing-form-row mb-3">
      <div class="form-group" style="flex: 1;">
        <label>ЕИО</label>
        <input :value="form.recipient_eio" type="text" class="form-control" @input="updateForm('recipient_eio', $event.target.value)" />
      </div>
      <div class="form-group" style="flex: 1;">
        <label>Краткое наименование</label>
        <input :value="form.recipient_short_name" type="text" class="form-control" @input="updateForm('recipient_short_name', $event.target.value)" />
      </div>
      <div v-if="isLetterKind" class="form-group" style="flex: 1;">
        <label>Кому</label>
        <input :value="form.recipient_to_name" type="text" class="form-control" @input="updateForm('recipient_to_name', $event.target.value)" />
      </div>
      <div v-else class="form-group" style="flex: 1;">
        <label>Кем</label>
        <input :value="form.recipient_genitive_name" type="text" class="form-control" placeholder="родительный падеж" @input="updateForm('recipient_genitive_name', $event.target.value)" />
      </div>
      <div v-if="hasEditableNumberSuffix" class="form-group" style="flex: 1;">
        <label>Обращение</label>
        <input :value="form.recipient_appeal" type="text" class="form-control" @input="updateForm('recipient_appeal', $event.target.value)" />
      </div>
      <div v-if="isLetterKind" class="form-group" style="flex: 1;">
        <label>Форма обращения</label>
        <select :value="form.recipient_salutation" class="form-control" @change="updateForm('recipient_salutation', $event.target.value)">
          <option value="">—</option>
          <option value="Уважаемый">Уважаемый</option>
          <option value="Уважаемая">Уважаемая</option>
        </select>
      </div>
    </div>

    <!-- Row 3: Deal + Contract + Date + Suffix -->
    <div class="outgoing-form-row mb-3">
      <div class="form-group" style="flex: 1;">
        <label>Сделка</label>
        <select :value="form.deal_id" class="form-control" @change="updateForm('deal_id', $event.target.value)">
          <option value="">Без сделки</option>
          <option v-for="deal in deals" :key="deal.id" :value="deal.id">{{ deal.title }}</option>
        </select>
      </div>
      <div class="form-group" style="flex: 1;">
        <label>Договор</label>
        <select :value="form.contract_id" class="form-control" :disabled="!form.deal_id" @change="updateForm('contract_id', $event.target.value)">
          <option value="">Без договора</option>
          <option v-for="contract in dealContracts" :key="contract.id" :value="contract.id">
            {{ contract.contract_number }} от {{ formatDate(contract.contract_date) }}
          </option>
        </select>
      </div>
      <div class="form-group" style="flex: 1;">
        <label>Дата</label>
        <input :value="form.letter_date" type="date" class="form-control" @input="updateForm('letter_date', $event.target.value)" />
      </div>
      <div v-if="isLetterKind" class="form-group" style="flex: 1;">
        <label>Период номера (после /)</label>
        <input :value="form.outgoing_number_suffix" type="text" class="form-control" placeholder="YYYY-MM" @input="updateForm('outgoing_number_suffix', $event.target.value)" />
        <small v-if="activeDocumentId" class="text-muted">Текущий номер: {{ displayOutgoingNumber(activeDocument) }}</small>
      </div>
    </div>

    <div class="outgoing-form-row mb-3">
      <div class="form-group" style="flex: 1;">
        <label>Банковские реквизиты получателя</label>
        <select
          :value="form.bank_account_index"
          class="form-control"
          :disabled="!recipientBankAccounts.length"
          @change="updateForm('bank_account_index', $event.target.value === '' ? null : Number($event.target.value))"
        >
          <option v-if="!recipientBankAccounts.length" :value="null">Нет реквизитов</option>
          <option v-for="(account, index) in recipientBankAccounts" :key="index" :value="index">
            {{ bankAccountLabel(account, index) }}
          </option>
        </select>
        <small v-if="recipientBankAccounts.length > 1" class="bank-warning">
          У контрагента несколько банковских реквизитов. По умолчанию выбран первый.
        </small>
      </div>
    </div>

    <div class="form-group mb-3">
      <label>{{ isLetterKind ? 'Тема письма' : 'Основание документа / комментарий' }}</label>
      <input :value="form.subject" type="text" class="form-control" @input="updateForm('subject', $event.target.value)" />
    </div>

    <div v-if="requiresStageLinks" class="form-group mb-3">
      <label>Этапы сделки</label>
      <div class="stage-link-list">
        <label v-for="stage in dealStages" :key="stage.id" class="stage-link-item">
          <input :value="stage.id" :checked="(form.linked_stage_ids || []).includes(stage.id)" type="checkbox" @change="toggleStage(stage.id, $event.target.checked)" />
          <span>{{ stage.name }}</span>
          <small>{{ formatDate(stage.date_start) }} — {{ formatDate(stage.date_end) }}</small>
        </label>
        <div v-if="form.deal_id && !dealStages.length" class="text-muted small">Этапы по сделке не найдены</div>
        <div v-if="!form.deal_id" class="text-muted small">Сначала выберите сделку</div>
      </div>
    </div>

    <div v-if="requiresPaymentLinks" class="form-group mb-3">
      <label>{{ isActKind ? 'Платежи / зачет аванса' : 'Платеж по счету' }}</label>
      <div class="payment-link-list">
        <div v-for="(item, index) in form.linked_payment_items" :key="index" class="payment-link-row">
          <select :value="item.entry_id" class="form-control" @change="updatePaymentItem(index, 'entry_id', $event.target.value)">
            <option value="">Выберите платеж</option>
            <option
              v-for="payment in dealPayments"
              :key="payment.id"
              :value="payment.id"
              :disabled="getPaymentAvailableAmount(payment, index) <= 0 && String(item.entry_id || '') !== String(payment.id)"
            >
              {{ paymentOptionLabel(payment, index) }}
            </option>
          </select>
          <input :value="item.amount" type="number" min="0" step="0.01" class="form-control" placeholder="Сумма" @input="updatePaymentItem(index, 'amount', $event.target.value === '' ? null : Number($event.target.value))" />
          <input :value="item.note" type="text" class="form-control" placeholder="Комментарий" @input="updatePaymentItem(index, 'note', $event.target.value)" />
          <button type="button" class="btn btn-sm btn-outline-danger" @click="$emit('remove-payment-link', index)">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <button type="button" class="btn btn-sm btn-outline-primary" @click="$emit('add-payment-link')">
          <i class="fas fa-plus mr-1"></i> Добавить платеж
        </button>
        <div v-if="form.deal_id && !dealPayments.length" class="text-muted small mt-2">Платежи по сделке не найдены</div>
      </div>
    </div>

    <div v-if="isLetterKind" class="form-group mb-3">
      <label>Текст письма</label>
      <div class="rich-editor-toolbar">
        <button type="button" class="toolbar-btn" :class="{ active: editorInList }" title="Маркированный список" @click="$emit('format-list')">
          <i class="fas fa-list-ul"></i>
        </button>
        <button type="button" class="toolbar-btn" title="Отступ красной строки 1.25см" @click="$emit('format-indent')">
          <i class="fas fa-indent"></i> <span class="toolbar-label">1.25</span>
        </button>
        <button
          type="button"
          class="toolbar-btn"
          :disabled="introParagraphBusy || !form.deal_id || (!form.recipient_company_id && !form.recipient_short_name)"
          title="Добавить вводный абзац по сделке и основному договору"
          @click="$emit('insert-intro-paragraph')"
        >
          <i class="fas" :class="introParagraphBusy ? 'fa-spinner fa-spin' : 'fa-file-signature'"></i>
          <span class="toolbar-label">Вводный абзац</span>
        </button>
        <button type="button" class="toolbar-btn" title="Вставить таблицу" @click="$emit('open-table-modal')">
          <i class="fas fa-table"></i>
        </button>
        <button type="button" class="toolbar-btn" :class="{ active: showFormattingMarks }" title="Показать служебные символы" @click="$emit('toggle-formatting-marks')">
          <i class="fas fa-paragraph"></i>
        </button>
      </div>
      <div
        :ref="bindEditorRef"
        class="rich-editor-area"
        :class="{ 'show-formatting': showFormattingMarks }"
        contenteditable="true"
        @input="$emit('editor-input', $event)"
        @paste="$emit('editor-paste', $event)"
        @mouseup="$emit('capture-editor-selection')"
        @keyup="$emit('capture-editor-selection')"
        @focus="$emit('capture-editor-selection')"
        @mousemove="$emit('editor-mouse-move', $event)"
        @mouseleave="$emit('editor-mouse-leave')"
        @scroll="$emit('update-table-controls-position')"
      ></div>
    </div>

    <div v-if="isLetterKind" class="form-group mb-3">
      <label>Список приложений</label>
      <div class="rich-editor-toolbar attachments-toolbar">
        <button type="button" class="toolbar-btn" :class="{ active: attachmentsInList }" title="Маркированный список" @click="$emit('format-attachments-list')">
          <i class="fas fa-list-ul"></i>
        </button>
        <button type="button" class="toolbar-btn" title="Абзац" @click="$emit('format-attachments-indent')">
          <i class="fas fa-paragraph"></i>
        </button>
      </div>
      <div
        :ref="bindAttachmentsEditorRef"
        class="rich-editor-area attachments-editor"
        :class="{ 'show-formatting': showFormattingMarks }"
        contenteditable="true"
        @input="$emit('attachments-input')"
        @paste="$emit('attachments-paste', $event)"
        @mouseup="$emit('refresh-toolbar-states')"
        @keyup="$emit('refresh-toolbar-states')"
        @focus="$emit('refresh-toolbar-states')"
      ></div>
    </div>

    <div v-if="isLetterKind" class="form-group mb-3">
      <label>Файлы приложений</label>
      <div class="d-flex align-center gap-2 mb-2">
        <label class="btn btn-sm btn-outline-primary m-0 cursor-pointer">
          <i class="fas fa-paperclip"></i> Выбрать файлы
          <input type="file" hidden multiple @change="$emit('handle-file-change', $event)" />
        </label>
        <span v-if="!pendingFiles.length" class="small text-muted">Файлы не выбраны</span>
      </div>
      <div v-if="pendingFiles.length" class="d-flex flex-wrap gap-2">
        <div v-for="file in pendingFiles" :key="file.name" class="file-badge">
          <i class="fas fa-file mr-1"></i> {{ file.name }}
        </div>
      </div>
      <div v-if="restoredPendingFileNames.length" class="draft-files-note mt-2">
        <i class="fas fa-info-circle mr-1"></i>
        Локальный черновик содержал файлы: {{ restoredPendingFileNames.join(', ') }}. Их нужно прикрепить заново.
      </div>
    </div>

    <div class="structured-editor-section mt-4">
      <div class="structured-editor-section__header">
        <div>
          <div class="structured-editor-section__title">Document Draft</div>
          <div class="structured-editor-section__subtitle">Слой структурированного документа для шаблонов, печати и будущего AI.</div>
        </div>
        <div class="structured-editor-section__controls">
          <label class="structured-editor-section__mode-label">
            <span>Режим</span>
            <select :value="form.editor_mode" class="form-control form-control-sm" @change="updateForm('editor_mode', $event.target.value)">
              <option value="classic">Классический</option>
              <option value="structured">Структурированный</option>
            </select>
          </label>
          <button type="button" class="btn btn-sm btn-outline-secondary" @click="$emit('reset-editor-draft')">
            <i class="fas fa-rotate-left mr-1"></i> Сбросить структуру
          </button>
        </div>
      </div>

      <StructuredDocumentEditor
        v-if="form.editor_mode === 'structured'"
        :model-value="form.editor_draft"
        :document-kind="form.document_kind || activeKind"
        :block-catalog="editorBlockCatalog"
        :fields="editorFields"
        :template-blocks="editorTemplateBlocks"
        :resolved-fields="editorResolvedFields"
        :validation="form.editor_validation"
        :ai-enabled="aiEnabled"
        :ai-model="aiModel"
        :ai-handler="requestOutgoingAiAssist"
        :disabled="saving || editorSchemaLoading"
        @update:model-value="updateForm('editor_draft', $event)"
      />
      <div v-else class="structured-editor-section__classic-note">
        Для писем можно продолжать работать в классическом режиме. Структурированный draft сохранится отдельно и позже позволит подключить AI-подстановки и новый редактор без миграции документов.
      </div>

      <div v-if="form.editor_mode === 'structured'" class="structured-live-preview mt-3">
        <div class="structured-live-preview__header">
          <div>
            <div class="structured-live-preview__title">Live Preview</div>
            <div class="structured-live-preview__subtitle">Предпросмотр несохраненного draft без создания версии документа.</div>
          </div>
          <div class="structured-live-preview__controls">
            <button
              type="button"
              class="btn btn-sm"
              :class="liveStructuredPreviewMode === 'pdf' ? 'btn-primary' : 'btn-outline-secondary'"
              @click="$emit('set-structured-preview-mode', 'pdf')"
            >PDF</button>
            <button
              type="button"
              class="btn btn-sm"
              :class="liveStructuredPreviewMode === 'docx' ? 'btn-primary' : 'btn-outline-secondary'"
              @click="$emit('set-structured-preview-mode', 'docx')"
            >DOCX</button>
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="$emit('refresh-structured-live-preview')">
              <i class="fas fa-sync-alt mr-1"></i> Обновить
            </button>
          </div>
        </div>

        <div class="structured-live-preview__body">
          <div v-if="liveStructuredPreviewLoading" class="structured-live-preview__state">
            <div class="spinner mb-2"></div>
            <span>Формируем предпросмотр...</span>
          </div>
          <div v-else-if="liveStructuredPreviewError" class="structured-live-preview__state structured-live-preview__state--error">
            <i class="fas fa-exclamation-triangle mb-2"></i>
            <span>{{ liveStructuredPreviewError }}</span>
          </div>
          <div v-else-if="!canRenderStructuredPreview" class="structured-live-preview__state">
            <i class="fas fa-file-alt mb-2"></i>
            <span>Для live preview выберите получателя.</span>
          </div>
          <iframe
            v-else-if="liveStructuredPreviewMode === 'pdf' && liveStructuredPreviewPdfSrc"
            :src="liveStructuredPreviewPdfSrc"
            class="structured-live-preview__frame"
            title="Live preview PDF"
          ></iframe>
          <div
            v-else-if="liveStructuredPreviewMode === 'docx'"
            :ref="bindStructuredDocxRef"
            class="structured-live-preview__docx"
          ></div>
          <div v-else class="structured-live-preview__state">
            <i class="fas fa-file-alt mb-2"></i>
            <span>Предпросмотр пока недоступен.</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CompanySmartSelect from '../../../components/ui/CompanySmartSelect.vue'
import StructuredDocumentEditor from '../../../components/outgoing/StructuredDocumentEditor.vue'

export default {
  name: 'OutgoingEditor',
  components: { CompanySmartSelect, StructuredDocumentEditor },
  props: {
    form: { type: Object, required: true },
    isLetterKind: { type: Boolean, default: false },
    isActKind: { type: Boolean, default: false },
    hasEditableNumberSuffix: { type: Boolean, default: false },
    requiresStageLinks: { type: Boolean, default: false },
    requiresPaymentLinks: { type: Boolean, default: false },
    activeKind: { type: String, required: true },
    activeDocumentId: { default: null },
    activeDocument: { type: Object, default: () => ({}) },
    displayOutgoingNumber: { type: Function, required: true },
    companies: { type: Array, default: () => [] },
    ourCompanies: { type: Array, default: () => [] },
    ourCompanyLocked: { type: Boolean, default: false },
    deals: { type: Array, default: () => [] },
    dealContracts: { type: Array, default: () => [] },
    dealStages: { type: Array, default: () => [] },
    dealPayments: { type: Array, default: () => [] },
    recipientBankAccounts: { type: Array, default: () => [] },
    bankAccountLabel: { type: Function, required: true },
    formatDate: { type: Function, required: true },
    getPaymentAvailableAmount: { type: Function, required: true },
    paymentOptionLabel: { type: Function, required: true },
    pendingFiles: { type: Array, default: () => [] },
    restoredPendingFileNames: { type: Array, default: () => [] },
    showFormattingMarks: { type: Boolean, default: false },
    editorInList: { type: Boolean, default: false },
    attachmentsInList: { type: Boolean, default: false },
    introParagraphBusy: { type: Boolean, default: false },
    saving: { type: Boolean, default: false },
    editorSchemaLoading: { type: Boolean, default: false },
    editorBlockCatalog: { type: Array, default: () => [] },
    editorFields: { type: Array, default: () => [] },
    editorTemplateBlocks: { type: Array, default: () => [] },
    editorResolvedFields: { type: Object, default: () => ({}) },
    aiEnabled: { type: Boolean, default: false },
    aiModel: { type: String, default: '' },
    requestOutgoingAiAssist: { type: Function, required: true },
    liveStructuredPreviewMode: { type: String, default: 'pdf' },
    liveStructuredPreviewLoading: { type: Boolean, default: false },
    liveStructuredPreviewError: { type: String, default: '' },
    liveStructuredPreviewPdfSrc: { type: String, default: '' },
    canRenderStructuredPreview: { type: Boolean, default: false },
    /**
     * Callback setters from the parent — invoked with the DOM element when
     * the contenteditable / docx preview mounts/unmounts. Avoids passing Vue
     * refs through props (which would be auto-unwrapped).
     */
    setEditorEl: { type: Function, required: true },
    setAttachmentsEditorEl: { type: Function, required: true },
    setStructuredDocxEl: { type: Function, required: true },
  },
  emits: [
    'update:form',
    'fill-recipient', 'add-payment-link', 'remove-payment-link',
    'format-list', 'format-indent', 'insert-intro-paragraph',
    'open-table-modal', 'toggle-formatting-marks',
    'editor-input', 'editor-paste', 'capture-editor-selection',
    'editor-mouse-move', 'editor-mouse-leave', 'update-table-controls-position',
    'format-attachments-list', 'format-attachments-indent',
    'attachments-input', 'attachments-paste', 'refresh-toolbar-states',
    'handle-file-change', 'reset-editor-draft',
    'set-structured-preview-mode', 'refresh-structured-live-preview',
  ],
  setup(props, { emit }) {
    const updateForm = (key, value) => {
      emit('update:form', { ...props.form, [key]: value })
    }
    const toggleStage = (stageId, checked) => {
      const current = Array.isArray(props.form.linked_stage_ids) ? [...props.form.linked_stage_ids] : []
      const idx = current.indexOf(stageId)
      if (checked && idx === -1) current.push(stageId)
      else if (!checked && idx !== -1) current.splice(idx, 1)
      emit('update:form', { ...props.form, linked_stage_ids: current })
    }
    const updatePaymentItem = (index, key, value) => {
      const list = Array.isArray(props.form.linked_payment_items)
        ? props.form.linked_payment_items.map((item) => ({ ...item }))
        : []
      if (!list[index]) return
      list[index][key] = value
      emit('update:form', { ...props.form, linked_payment_items: list })
    }
    const bindEditorRef = (el) => { props.setEditorEl(el) }
    const bindAttachmentsEditorRef = (el) => { props.setAttachmentsEditorEl(el) }
    const bindStructuredDocxRef = (el) => { props.setStructuredDocxEl(el) }
    return { updateForm, toggleStage, updatePaymentItem, bindEditorRef, bindAttachmentsEditorRef, bindStructuredDocxRef }
  },
}
</script>

<style scoped>
.outgoing-form-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.bank-warning {
  display: block;
  margin-top: 5px;
  color: #b45309;
  font-size: 0.78rem;
}

.stage-link-list,
.payment-link-list {
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 14px;
  padding: 10px;
  background: var(--md-sys-color-surface-container-lowest);
}

.stage-link-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 9px;
  align-items: center;
  padding: 7px 8px;
  border-radius: 10px;
  cursor: pointer;
}
.stage-link-item:hover { background: var(--md-sys-color-surface-container); }
.stage-link-item span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 600;
}
.stage-link-item small { color: var(--md-sys-color-on-surface-variant); }

.payment-link-row {
  display: grid;
  grid-template-columns: minmax(180px, 1.4fr) 130px minmax(160px, 1fr) auto;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.structured-editor-section {
  margin-top: 6px;
  padding-top: 14px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
}
.structured-editor-section__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 12px;
}
.structured-editor-section__title {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--md-sys-color-on-surface);
}
.structured-editor-section__subtitle {
  font-size: 0.82rem;
  color: var(--md-sys-color-on-surface-variant);
  margin-top: 6px;
}
.structured-editor-section__controls {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}
.structured-editor-section__mode-label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 180px;
}
.structured-editor-section__mode-label span {
  font-size: 0.75rem;
  color: var(--md-sys-color-on-surface-variant);
  font-weight: 600;
}
.structured-editor-section__classic-note {
  border: 1px dashed var(--md-sys-color-outline-variant);
  border-radius: 18px;
  padding: 16px 18px;
  background: var(--md-sys-color-surface-container-lowest);
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.86rem;
  line-height: 1.45;
}

.structured-live-preview {
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 16px;
  background: var(--md-sys-color-surface-container-lowest);
  overflow: hidden;
}
.structured-live-preview__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  min-height: 48px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}
.structured-live-preview__title {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--md-sys-color-on-surface);
}
.structured-live-preview__subtitle {
  margin-top: 4px;
  font-size: 0.8rem;
  color: var(--md-sys-color-on-surface-variant);
}
.structured-live-preview__controls {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.structured-live-preview__body {
  min-height: 620px;
  background: #eef3fb;
}
.structured-live-preview__frame {
  width: 100%;
  min-height: 620px;
  border: 0;
  display: block;
  background: #eef3fb;
}
.structured-live-preview__docx {
  min-height: 620px;
  overflow: auto;
  background: #eef3fb;
  padding: 18px;
}
.structured-live-preview__docx :deep(.docx-wrapper) {
  padding: 18px !important;
  background: transparent !important;
}
.structured-live-preview__docx :deep(.docx) {
  margin: 0 auto !important;
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.12) !important;
}
.structured-live-preview__state {
  min-height: 620px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: var(--md-sys-color-on-surface-variant);
}
.structured-live-preview__state--error { color: #b42318; }

.rich-editor-toolbar {
  display: flex;
  gap: 4px;
  padding: 6px 8px;
  border: 1px solid var(--md-sys-color-outline);
  border-bottom: none;
  border-radius: var(--radius-md, 8px) var(--radius-md, 8px) 0 0;
  background: var(--md-sys-color-surface);
}

.toolbar-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 6px;
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-on-surface);
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.15s;
}
.toolbar-btn:hover { background: var(--md-sys-color-primary-container); }
.toolbar-btn.active {
  background: var(--md-sys-color-primary-container);
  border-color: var(--md-sys-color-primary);
  color: var(--md-sys-color-primary);
}
.toolbar-label { font-size: 0.7rem; opacity: 0.7; }

.rich-editor-area {
  min-height: 300px;
  padding: 12px 14px;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 0 0 var(--radius-md, 8px) var(--radius-md, 8px);
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-on-surface);
  overflow-y: auto;
  word-break: break-word;
  overflow-wrap: break-word;
  outline: none;
  line-height: 1.6;
}
.rich-editor-area.attachments-editor {
  min-height: 120px;
  max-height: 220px;
}
.rich-editor-area:focus {
  border-color: var(--md-sys-color-primary);
  box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.15);
}
.rich-editor-area p,
.rich-editor-area div,
.rich-editor-area li { margin: 0 0 0.45rem; }
.rich-editor-area ul,
.rich-editor-area ol {
  margin: 0.35rem 0 0.7rem;
  padding-left: 0;
  margin-left: 0;
  list-style: none !important;
}
.rich-editor-area ol { counter-reset: editor-ordered-list; }
.rich-editor-area li {
  margin: 0.2rem 0;
  position: relative;
  padding-left: 1.9rem;
}
.rich-editor-area ul > li::before,
.rich-editor-area ol > li::before {
  position: absolute;
  left: 0.55rem;
  top: 0.02rem;
  color: var(--md-sys-color-primary);
  font-size: 1.02em;
  font-weight: 700;
}
.rich-editor-area ul > li::before { content: "•"; }
.rich-editor-area ol > li { counter-increment: editor-ordered-list; }
.rich-editor-area ol > li::before { content: counter(editor-ordered-list) "."; }

.rich-editor-area.show-formatting {
  background-image:
    repeating-linear-gradient(
      to bottom,
      transparent 0,
      transparent calc(1.6em - 1px),
      color-mix(in srgb, var(--md-sys-color-primary) 10%, transparent) calc(1.6em - 1px),
      color-mix(in srgb, var(--md-sys-color-primary) 10%, transparent) 1.6em
    );
  background-origin: content-box;
  background-clip: padding-box;
}
.rich-editor-area.show-formatting p,
.rich-editor-area.show-formatting div,
.rich-editor-area.show-formatting li {
  position: relative;
  min-height: 1.45em;
}
.rich-editor-area.show-formatting p::after,
.rich-editor-area.show-formatting li::after,
.rich-editor-area.show-formatting div::after {
  content: "¶";
  display: inline-block;
  margin-left: 6px;
  color: color-mix(in srgb, var(--md-sys-color-primary) 72%, transparent);
  font-size: 0.92em;
  font-weight: 700;
  vertical-align: middle;
}
.rich-editor-area.show-formatting p:has(> br:only-child),
.rich-editor-area.show-formatting div:has(> br:only-child),
.rich-editor-area.show-formatting li:has(> br:only-child) {
  min-height: 1.8em;
  border-radius: 6px;
  background:
    linear-gradient(
      to bottom,
      transparent calc(50% - 1px),
      color-mix(in srgb, var(--md-sys-color-primary) 14%, transparent) calc(50% - 1px),
      color-mix(in srgb, var(--md-sys-color-primary) 14%, transparent) calc(50% + 1px),
      transparent calc(50% + 1px)
    );
}
.rich-editor-area.show-formatting p:has(> br:only-child)::before,
.rich-editor-area.show-formatting div:has(> br:only-child)::before,
.rich-editor-area.show-formatting li:has(> br:only-child)::before {
  content: "¶";
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  color: color-mix(in srgb, var(--md-sys-color-primary) 72%, transparent);
  font-size: 0.92em;
  font-weight: 700;
  background: var(--md-sys-color-surface);
  padding-right: 6px;
}
.rich-editor-area.show-formatting p[style*="text-indent"]::before,
.rich-editor-area.show-formatting div[style*="text-indent"]::before {
  content: "↹";
  position: absolute;
  left: -14px;
  top: 0;
  color: color-mix(in srgb, var(--md-sys-color-primary) 55%, transparent);
  font-size: 0.8em;
  font-weight: 700;
}
.rich-editor-area.show-formatting ul,
.rich-editor-area.show-formatting ol {
  outline: 1px dashed color-mix(in srgb, var(--md-sys-color-primary) 18%, transparent);
  outline-offset: 2px;
  border-radius: 8px;
  padding-top: 0.15rem;
  padding-bottom: 0.15rem;
}
.rich-editor-area table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
}
.rich-editor-area th,
.rich-editor-area td {
  border: 1px solid var(--md-sys-color-outline-variant);
  padding: 8px 10px;
  vertical-align: top;
}
.rich-editor-area th {
  background: var(--md-sys-color-surface-container-low);
  font-weight: 700;
}

.file-badge {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.8rem;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container, var(--md-sys-color-primary));
}
.draft-files-note {
  padding: 8px 10px;
  border-radius: 8px;
  font-size: 0.82rem;
  background: color-mix(in srgb, var(--md-sys-color-secondary-container) 72%, transparent);
  color: var(--md-sys-color-on-secondary-container, var(--md-sys-color-on-surface));
}

.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--md-sys-color-outline-variant);
  border-top-color: var(--md-sys-color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.cursor-pointer { cursor: pointer; }

.custom-scrollbar::-webkit-scrollbar { width: 6px; height: 6px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(128, 128, 128, 0.3); border-radius: 3px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }

@media (max-width: 768px) {
  .outgoing-form-row { flex-wrap: wrap; }
  .outgoing-form-row > .form-group {
    flex: 1 1 100% !important;
    min-width: 0;
  }
}
</style>
