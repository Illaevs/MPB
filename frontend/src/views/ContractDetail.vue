<template>
  <div class="contract-detail contract-detail--page">
    <ContractHeader
      :contract="contract"
      :deal-title="dealTitle"
      :subcontractor-title="subcontractorTitle"
      :customer-name="customerName"
      :executor-name="executorName"
      :payment-summary="paymentSummary"
      :payment-completion-percent="paymentCompletionPercent"
      :status-menu-open="statusMenuOpen"
      :status-busy="statusBusy"
      :cd-status-options="cdStatusOptions"
      :contract-status-label="contractStatusLabel"
      :contract-type-label="contractTypeLabel"
      :format-date="formatDate"
      :format-amount="formatAmount"
      @toggle-status-menu="statusMenuOpen = !statusMenuOpen"
      @close-status-menu="statusMenuOpen = false"
      @change-status="onChangeStatus"
    />

    <ContractToolbar
      :active-tab="activeTab"
      :is-service-contract="isServiceContract"
      :payment-filters="paymentFilters"
      :document-filters="documentFilters"
      :doc-types="docTypes"
      @set-tab="setActiveTab"
      @reset-payment-filters="resetPaymentFilters"
      @reset-document-filters="resetDocumentFilters"
      @open-upload="(t) => openUploadModal(t)"
      @update-payment-filter="({ key, value }) => paymentFilters[key] = value"
      @update-document-filter="({ key, value }) => documentFilters[key] = value"
    />

    <div v-show="activeTab === 'data'">
      <ContractDataTab
        :loading="loading"
        :filtered-payments="filteredPayments"
        :filtered-stages="filteredStages"
        :payment-summary="paymentSummary"
        :stages-planned-amount="stagesPlannedAmount"
        :format-amount="formatAmount"
        :format-date="formatDate"
        :payment-status-class="paymentStatusClass"
        :payment-status-label="paymentStatusLabel"
        :stage-type-label="stageTypeLabel"
        :stage-status-class="stageStatusClass"
        :stage-status-label="stageStatusLabel"
      />
    </div>

    <div v-show="activeTab === 'expenses'">
      <ContractExpensesTab
        :loading-expenses="loadingExpenses"
        :expense-entries="expenseEntries"
        :expense-summary="expenseSummary"
        :expense-payer-name="expensePayerName"
        :expense-payee-name="expensePayeeName"
        :format-amount="formatAmount"
        :format-date="formatDate"
        @open-bulk="openBulkExpenseModal"
        @open-expense="openExpenseModal"
        @delete-expense="deleteExpense"
      />
    </div>

    <div v-show="activeTab === 'documents'">
      <ContractDocumentsTab
        :filtered-documents-list="filteredDocumentsList"
        :has-document-files="hasDocumentFiles"
        :downloading-zip="downloadingZip"
        :format-uploaded-at="formatUploadedAt"
        :document-amount-help-text="documentAmountHelpText"
        :document-type-badge-class="documentTypeBadgeClass"
        :document-type-label="documentTypeLabel"
        :document-amount-allowed="documentAmountAllowed"
        :document-amount-input-value="documentAmountInputValue"
        :on-document-amount-focus="onDocumentAmountFocus"
        :on-document-amount-input="onDocumentAmountInput"
        :on-document-amount-blur="onDocumentAmountBlur"
        :short-product-name="shortProductName"
        :doc-status-class="docStatusClass"
        :get-document-files="getDocumentFiles"
        :file-action-class="fileActionClass"
        :file-icon-class="fileIconClass"
        :file-name-parts="fileNameParts"
        @open-invoice-products="openInvoiceProductsModal"
        @update-status="updateDocumentStatus"
        @download="({ doc, kind, name }) => downloadDocument(doc, kind, name)"
        @download-zip="downloadDocumentsZip"
        @delete-file="({ doc, kind, name }) => deleteDocumentFile(doc, kind, name)"
        @open-upload="({ docType, doc, fileKind }) => openUploadModal(docType, doc, fileKind)"
        @delete-document="deleteDocument"
      />
    </div>

    <ExpenseModal
      :show="showExpenseModal"
      :form="expenseForm"
      :editing-expense="editingExpense"
      :expense-categories="expenseCategories"
      @close="closeExpenseModal"
      @save="saveExpense"
      @update-field="({ key, value }) => expenseForm[key] = value"
    />

    <BulkExpenseModal
      :show="showBulkExpenseModal"
      :form="bulkForm"
      :expense-categories="expenseCategories"
      @close="closeBulkExpenseModal"
      @save="createBulkExpenses"
      @update-field="({ key, value }) => bulkForm[key] = value"
    />

    <UploadDocumentModal
      :show="showUploadModal"
      :upload-form="uploadForm"
      :doc-types="docTypes"
      :uploading="uploading"
      :is-drop-active="isDropActive"
      :show-upload-amount-field="showUploadAmountField"
      :show-upload-invoice-products="showUploadInvoiceProducts"
      :upload-amount-input-value="uploadAmountInputValue"
      :upload-amount-help-text="uploadAmountHelpText"
      :deal-products="dealProducts"
      :sorted-deal-products="sortedDealProducts"
      :deal-product-name="dealProductName"
      :on-upload-amount-focus="onUploadAmountFocus"
      :on-upload-amount-input="onUploadAmountInput"
      :on-upload-amount-blur="onUploadAmountBlur"
      @close="closeUploadModal"
      @submit="submitUpload"
      @update-field="({ key, value }) => uploadForm[key] = value"
      @toggle-product="onToggleProductId"
      @drop-over="handleDropOver"
      @drop-leave="handleDropLeave"
      @drop-file="handleDropFile"
      @file-change="onUploadFileChange"
      @register-input="(el) => (uploadFileInput = el)"
    />

    <InvoiceProductsModal
      :show="showInvoiceProductsModal"
      :invoice-products-doc="invoiceProductsDoc"
      :invoice-product-ids="invoiceProductIds"
      :saving-invoice-products="savingInvoiceProducts"
      :deal-products="dealProducts"
      :sorted-deal-products="sortedDealProducts"
      :deal-product-name="dealProductName"
      @close="closeInvoiceProductsModal"
      @save="saveInvoiceProducts"
      @toggle-id="onToggleInvoiceId"
    />
  </div>
</template>

<script>
import { useContractDetailState } from './contractDetail/composables/useContractDetailState'
import ContractHeader from './contractDetail/parts/ContractHeader.vue'
import ContractToolbar from './contractDetail/parts/ContractToolbar.vue'
import ContractDataTab from './contractDetail/parts/ContractDataTab.vue'
import ContractExpensesTab from './contractDetail/parts/ContractExpensesTab.vue'
import ContractDocumentsTab from './contractDetail/parts/ContractDocumentsTab.vue'
import ExpenseModal from './contractDetail/parts/ExpenseModal.vue'
import BulkExpenseModal from './contractDetail/parts/BulkExpenseModal.vue'
import UploadDocumentModal from './contractDetail/parts/UploadDocumentModal.vue'
import InvoiceProductsModal from './contractDetail/parts/InvoiceProductsModal.vue'

export default {
  name: 'ContractDetail',
  components: {
    ContractHeader,
    ContractToolbar,
    ContractDataTab,
    ContractExpensesTab,
    ContractDocumentsTab,
    ExpenseModal,
    BulkExpenseModal,
    UploadDocumentModal,
    InvoiceProductsModal,
  },
  setup() {
    const state = useContractDetailState()

    const onToggleProductId = ({ id, checked }) => {
      const list = state.uploadForm.value.productIds
      if (checked) {
        if (!list.includes(id)) list.push(id)
      } else {
        const idx = list.indexOf(id)
        if (idx > -1) list.splice(idx, 1)
      }
    }

    const onToggleInvoiceId = ({ id, checked }) => {
      const list = state.invoiceProductIds.value
      if (checked) {
        if (!list.includes(id)) list.push(id)
      } else {
        const idx = list.indexOf(id)
        if (idx > -1) list.splice(idx, 1)
      }
    }

    return {
      ...state,
      onToggleProductId,
      onToggleInvoiceId,
    }
  }
}
</script>

<style scoped>
.contract-detail--page {
  display: flex;
  flex-direction: column;
  gap: 18px;
  margin: 8px 18px 18px;
  padding: 0 32px 28px;
  background: #fff;
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-radius: 18px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
  min-height: calc(100vh - 84px);
  overflow: hidden;
}

@media (max-width: 768px) {
  .contract-detail--page {
    gap: 12px;
    margin: 0;
    padding: 0 14px 20px;
    border-radius: 0;
    border-left: none;
    border-right: none;
  }
}

:global(:root[data-theme="dark"]) .contract-detail--page {
  background: linear-gradient(180deg, rgba(19, 28, 43, 0.96) 0%, rgba(13, 20, 32, 0.96) 100%);
  border-color: rgba(148, 163, 184, 0.18);
  box-shadow: 0 26px 48px rgba(0, 0, 0, 0.34);
}
</style>
