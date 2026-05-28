<template>
  <div class="outgoing-registry-view h-100 d-flex flex-column">
    <div class="outgoing-kind-tabs card mb-2">
      <button
        v-for="kind in state.documentKinds"
        :key="kind.value"
        class="kind-chip"
        :class="{ active: state.activeKind.value === kind.value }"
        type="button"
        @click="state.switchDocumentKind(kind.value)"
      >
        <i class="fas" :class="kind.icon"></i>
        <span>{{ kind.label }}</span>
      </button>
    </div>

    <div class="outgoing-layout flex-grow-1 min-h-0">
      <OutgoingList
        :documents="state.documents.value"
        :loading="state.loading.value"
        :filters="state.filters.value"
        :companies="state.companies.value"
        :our-companies="state.ourCompanies.value"
        :active-document-id="state.activeDocumentId.value"
        :active-kind-meta="state.activeKindMeta.value"
        :document-kind-meta="state.documentKindMeta"
        :display-outgoing-number="state.displayOutgoingNumber"
        :format-date="state.formatDate"
        :page="state.page.value"
        :has-next="state.hasNext.value"
        @update:filters="state.filters.value = $event"
        @apply-filters="state.applyFilters"
        @reset-filters="state.resetFilters"
        @start-new="state.startNewDocument"
        @select-document="state.selectDocument($event)"
        @list-keydown="state.onListKeydown"
        @prev-page="state.prevPage"
        @next-page="state.nextPage"
      />

      <section class="card h-100 mb-0 d-flex flex-column">
        <div class="card-header border-bottom py-3">
          <div class="d-flex justify-between align-center">
            <div>
              <h2 class="m-0 main-title">
                {{ state.isEditing.value
                  ? (state.activeDocumentId.value ? 'Редактирование' : `Новый документ: ${state.activeKindMeta.value.singular}`)
                  : (state.displayOutgoingNumber(state.activeDocument.value) || 'Выберите документ') }}
              </h2>
              <div class="text-muted small mt-1">
                {{ state.isEditing.value ? (state.form.value.subject || 'Без темы') : (state.activeDocument.value.subject || '') }}
              </div>
            </div>
            <div class="d-flex gap-2 header-actions">
              <template v-if="!state.isEditing.value && state.activeDocumentId.value">
                <button v-if="state.canEditSequences.value" class="btn btn-outline-secondary btn-sm" @click="state.openSequences">
                  <i class="fas fa-hashtag mr-1"></i> Номера
                </button>
                <button class="btn btn-primary btn-sm" @click="state.downloadDocx">
                  <i class="fas fa-file-word mr-1"></i> Скачать Word
                </button>
                <button class="btn btn-outline-primary btn-sm" @click="state.enableEditMode">
                  <i class="fas fa-edit mr-1"></i> Редактировать
                </button>
                <button class="btn btn-outline-secondary btn-sm" @click="state.createVersion">
                  <i class="fas fa-code-branch mr-1"></i> Версия
                </button>
                <button class="btn btn-outline-danger btn-sm" @click="state.confirmDelete">
                  <i class="fas fa-trash mr-1"></i> Удалить
                </button>
              </template>
              <template v-else-if="state.isEditing.value">
                <button class="btn btn-outline-secondary btn-sm" @click="state.cancelEdit">Отмена</button>
                <button class="btn btn-primary btn-sm" :disabled="state.saving.value" @click="state.saveDocument">
                  <i v-if="state.saving.value" class="fas fa-spinner fa-spin mr-1"></i>
                  <i v-else class="fas fa-save mr-1"></i> Сохранить
                </button>
              </template>
            </div>
          </div>
        </div>

        <div class="card-body d-flex gap-0 p-0 h-100 overflow-hidden">
          <OutgoingPreview
            v-if="!state.isEditing.value"
            :active-document-id="state.activeDocumentId.value"
            :preview-mode="state.previewMode.value"
            :preview-frame-src="state.previewFrameSrc.value"
            :preview-scale-label="state.previewScaleLabel.value"
            :preview-ready="state.previewReady.value"
            :preview-loading="state.previewLoading.value"
            :loading="state.loading.value"
            @set-preview-mode="state.setPreviewMode($event)"
            @refresh-preview="state.refreshPreview"
          />

          <OutgoingEditor
            v-else
            :form="state.form.value"
            :is-letter-kind="state.isLetterKind.value"
            :is-act-kind="state.isActKind.value"
            :has-editable-number-suffix="state.hasEditableNumberSuffix.value"
            :requires-stage-links="state.requiresStageLinks.value"
            :requires-payment-links="state.requiresPaymentLinks.value"
            :active-kind="state.activeKind.value"
            :active-document-id="state.activeDocumentId.value"
            :active-document="state.activeDocument.value"
            :display-outgoing-number="state.displayOutgoingNumber"
            :companies="state.companies.value"
            :our-companies="state.ourCompanies.value"
            :our-company-locked="state.ourCompanyLocked.value"
            :deals="state.deals.value"
            :deal-contracts="state.dealContracts.value"
            :deal-stages="state.dealStages.value"
            :deal-payments="state.dealPayments.value"
            :recipient-bank-accounts="state.recipientBankAccounts.value"
            :bank-account-label="state.bankAccountLabel"
            :format-date="state.formatDate"
            :get-payment-available-amount="state.getPaymentAvailableAmount"
            :payment-option-label="state.paymentOptionLabel"
            :pending-files="state.pendingFiles.value"
            :restored-pending-file-names="state.restoredPendingFileNames.value"
            :show-formatting-marks="state.showFormattingMarks.value"
            :editor-in-list="state.editorInList.value"
            :attachments-in-list="state.attachmentsInList.value"
            :intro-paragraph-busy="state.introParagraphBusy.value"
            :saving="state.saving.value"
            :editor-schema-loading="state.editorSchemaLoading.value"
            :editor-block-catalog="state.editorBlockCatalog.value"
            :editor-fields="state.editorFields.value"
            :editor-template-blocks="state.editorTemplateBlocks.value"
            :editor-resolved-fields="state.editorResolvedFields.value"
            :ai-enabled="state.aiEnabled.value"
            :ai-model="state.aiModel.value"
            :request-outgoing-ai-assist="state.requestOutgoingAiAssist"
            :live-structured-preview-mode="state.liveStructuredPreviewMode.value"
            :live-structured-preview-loading="state.liveStructuredPreviewLoading.value"
            :live-structured-preview-error="state.liveStructuredPreviewError.value"
            :live-structured-preview-pdf-src="state.liveStructuredPreviewPdfSrc.value"
            :can-render-structured-preview="state.canRenderStructuredPreview.value"
            :set-editor-el="setEditorEl"
            :set-attachments-editor-el="setAttachmentsEditorEl"
            :set-structured-docx-el="setStructuredDocxEl"
            @update:form="state.form.value = $event"
            @fill-recipient="state.fillRecipientFromCompany"
            @add-payment-link="state.addPaymentLink"
            @remove-payment-link="state.removePaymentLink($event)"
            @format-list="state.formatList"
            @format-indent="state.formatIndent"
            @insert-intro-paragraph="state.insertIntroParagraph"
            @open-table-modal="state.openTableModal"
            @toggle-formatting-marks="state.toggleFormattingMarks"
            @editor-input="state.onEditorInput($event)"
            @editor-paste="state.onEditorPaste($event)"
            @capture-editor-selection="state.captureEditorSelection"
            @editor-mouse-move="state.onEditorMouseMove($event)"
            @editor-mouse-leave="state.onEditorMouseLeave"
            @update-table-controls-position="state.updateTableControlsPosition"
            @format-attachments-list="state.formatAttachmentsList"
            @format-attachments-indent="state.formatAttachmentsIndent"
            @attachments-input="state.onAttachmentsInput"
            @attachments-paste="state.onAttachmentsPaste($event)"
            @refresh-toolbar-states="state.refreshToolbarStates"
            @handle-file-change="state.handleFileChange($event)"
            @reset-editor-draft="state.ensureEditorDraft({ forceDefault: true })"
            @set-structured-preview-mode="state.setStructuredPreviewMode($event)"
            @refresh-structured-live-preview="state.refreshStructuredLivePreview"
          />

          <OutgoingRightPanel
            v-if="state.activeDocumentId.value || state.isEditing.value"
            :active-document="state.activeDocument.value"
            :active-document-id="state.activeDocumentId.value"
            :versions="state.versions.value"
            :files="state.files.value"
            :display-outgoing-number="state.displayOutgoingNumber"
            :format-date-time="state.formatDateTime"
            :get-version-file="state.getVersionFile"
            @approval-state-changed="state.handleOutgoingApprovalState($event)"
            @approval-updated="state.refreshOutgoingAfterApproval"
            @download-version-file="state.downloadOutgoingVersionFile"
            @download-file="state.downloadOutgoingFile"
          />
        </div>
      </section>
    </div>

    <OutgoingModals
      :draft-restore-modal-open="state.draftRestoreModalOpen.value"
      :draft-restore-candidate="state.draftRestoreCandidate.value"
      :draft-restore-reason="state.draftRestoreReason.value"
      :delete-modal-open="state.deleteModalOpen.value"
      :sequences-modal-open="state.sequencesModalOpen.value"
      :sequence-loading="state.sequenceLoading.value"
      :sequence-saving="state.sequenceSaving.value"
      :sequences="state.sequences.value"
      :sequence-form="state.sequenceForm.value"
      :active-kind-meta="state.activeKindMeta.value"
      :table-modal-open="state.tableModalOpen.value"
      :table-form="state.tableForm.value"
      :table-controls="state.tableControls.value"
      :format-date-time="state.formatDateTime"
      @apply-draft-restore="state.applyDraftRestore"
      @discard-draft-restore="state.discardDraftRestore"
      @close-delete="state.deleteModalOpen.value = false"
      @confirm-delete="state.deleteDocument"
      @close-sequences="state.closeSequences"
      @save-sequences="state.saveSequences"
      @update:sequenceForm="state.sequenceForm.value = $event"
      @close-table-modal="state.closeTableModal"
      @insert-table="state.insertTable"
      @update:tableForm="state.tableForm.value = $event"
      @table-controls-enter="state.onTableControlsEnter"
      @table-controls-leave="state.onTableControlsLeave"
      @add-table-row="state.addTableRow"
      @add-table-column="state.addTableColumn"
      @remove-table-row="state.removeTableRow"
      @remove-table-column="state.removeTableColumn"
    />
  </div>
</template>

<script>
import OutgoingList from './outgoingRegistry/parts/OutgoingList.vue'
import OutgoingPreview from './outgoingRegistry/parts/OutgoingPreview.vue'
import OutgoingEditor from './outgoingRegistry/parts/OutgoingEditor.vue'
import OutgoingRightPanel from './outgoingRegistry/parts/OutgoingRightPanel.vue'
import OutgoingModals from './outgoingRegistry/parts/OutgoingModals.vue'
import { useOutgoingRegistryState } from './outgoingRegistry/composables/useOutgoingRegistryState'

export default {
  name: 'OutgoingRegistry',
  components: { OutgoingList, OutgoingPreview, OutgoingEditor, OutgoingRightPanel, OutgoingModals },
  setup() {
    const state = useOutgoingRegistryState()
    const setEditorEl = (el) => { state.editorRef.value = el }
    const setAttachmentsEditorEl = (el) => { state.attachmentsEditorRef.value = el }
    const setStructuredDocxEl = (el) => { state.liveStructuredPreviewDocxRef.value = el }
    return { state, setEditorEl, setAttachmentsEditorEl, setStructuredDocxEl }
  },
}
</script>

<style scoped>
.outgoing-kind-tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  flex-shrink: 0;
}

.kind-chip {
  border: 1px solid var(--md-sys-color-outline-variant);
  background: var(--md-sys-color-surface-container-low);
  color: var(--md-sys-color-on-surface-variant);
  border-radius: 999px;
  padding: 8px 12px;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 0.86rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.16s ease;
}
.kind-chip.active {
  background: var(--md-sys-color-primary);
  border-color: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.outgoing-layout {
  display: grid;
  grid-template-columns: clamp(260px, 18vw, 320px) minmax(0, 1fr);
  gap: 12px;
  min-height: 0;
}

.outgoing-registry-view .card-header { padding: 10px 14px; }

.main-title { font-size: 1.2rem; }

.header-actions {
  flex-wrap: wrap;
  justify-content: flex-end;
}

.min-h-0 { min-height: 0; }

@media (max-width: 992px) {
  .outgoing-layout { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .header-actions { gap: 4px; }
  .header-actions .btn {
    font-size: 0.75rem;
    padding: 4px 8px;
  }
}
</style>
