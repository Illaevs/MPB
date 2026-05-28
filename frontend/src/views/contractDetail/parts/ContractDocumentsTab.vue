<template>
  <div class="contract-tab contract-tab--documents">
    <div class="contract-panel contract-flat-section contract-documents-table">
      <div class="contract-flat-section__header">
        <div>
          <h3 class="card-title m-0">Документы</h3>
          <small>{{ filteredDocumentsList.length }} записей</small>
        </div>
      </div>
      <div v-if="!filteredDocumentsList.length" class="empty-state">
        <i class="fas fa-file-alt"></i>
        <p>Документов нет</p>
        <small class="text-muted">Добавьте договор, акты, доп. соглашения и накладные</small>
      </div>
      <div v-else class="table-container contract-table-wrap contract-table-wrap--flat">
        <table class="table table-sm">
          <thead>
            <tr>
              <th class="contract-col-type">Тип документа</th>
              <th class="contract-col-number">№</th>
              <th class="contract-col-amount">
                <span class="contract-amount-heading">
                  Сумма
                  <span class="contract-amount-help" :title="documentAmountHelpText" tabindex="0">?</span>
                </span>
              </th>
              <th class="contract-col-products">Товары</th>
              <th class="contract-col-status">Статус</th>
              <th>Файлы</th>
              <th class="contract-col-action">PDF</th>
              <th class="contract-col-action">РЕД</th>
              <th class="contract-col-delete"></th>
            </tr>
          </thead>
          <tbody>
            <template v-for="doc in filteredDocumentsList" :key="doc.id">
              <tr>
                <td class="contract-col-type">
                  <span class="contract-type-pill" :class="documentTypeBadgeClass(doc.doc_type)">
                    {{ documentTypeLabel(doc.doc_type) }}
                  </span>
                </td>
                <td class="contract-col-number">{{ doc.number_in_contract || '—' }}</td>
                <td class="contract-col-amount">
                  <div v-if="documentAmountAllowed(doc.doc_type)" class="document-amount-cell">
                    <input
                      :value="documentAmountInputValue(doc)"
                      type="text"
                      inputmode="decimal"
                      min="0"
                      class="form-control form-control-sm text-right"
                      @focus="onDocumentAmountFocus(doc, $event)"
                      @input="onDocumentAmountInput(doc, $event)"
                      @blur="onDocumentAmountBlur(doc)"
                      @keydown.enter="$event.target.blur()"
                    >
                  </div>
                  <span v-else class="text-muted small">—</span>
                </td>
                <td class="contract-col-products">
                  <div v-if="doc.doc_type === 'invoice'" class="invoice-product-cell">
                    <div class="invoice-product-chips">
                      <span
                        v-for="product in (doc.linked_products || []).slice(0, 3)"
                        :key="`${doc.id}-${product.deal_product_id}`"
                        class="invoice-product-chip"
                        :title="product.product_name || product.custom_name"
                      >
                        {{ shortProductName(product.product_name || product.custom_name) }}
                      </span>
                      <span v-if="(doc.linked_products || []).length > 3" class="invoice-product-chip invoice-product-chip--more">
                        +{{ (doc.linked_products || []).length - 3 }}
                      </span>
                    </div>
                    <button class="btn btn-sm btn-outline-secondary invoice-products-edit" type="button" @click="$emit('open-invoice-products', doc)">
                      {{ (doc.linked_products || []).length ? 'Изм.' : 'Связать' }}
                    </button>
                  </div>
                  <span v-else class="text-muted small">—</span>
                </td>
                <td class="contract-col-status">
                  <select
                    class="form-control form-control-sm status-select"
                    :class="docStatusClass(doc.status)"
                    v-model="doc.status"
                    @change="$emit('update-status', doc)"
                  >
                    <option value="draft">Черновик</option>
                    <option value="signing">На подписании</option>
                    <option value="signed">Подписан</option>
                    <option value="canceled">Аннулирован</option>
                  </select>
                </td>
                <td class="contract-files-cell">
                  <div v-if="getDocumentFiles(doc).length" class="contract-files-list">
                    <div
                      v-for="file in getDocumentFiles(doc)"
                      :key="file.key"
                      class="contract-file-row"
                    >
                      <button
                        type="button"
                        class="contract-file-link"
                        :title="file.name"
                        @click="$emit('download', { doc, kind: file.kind, name: file.name })"
                      >
                        <span class="contract-file-link__icon" :class="fileActionClass(file.name, file.kind)">
                          <i class="fas" :class="fileIconClass(file.name, file.kind)"></i>
                        </span>
                        <span class="contract-file-link__name">
                          <span class="contract-file-link__base">{{ fileNameParts(file.name).base }}</span>
                          <span class="contract-file-link__ext">{{ fileNameParts(file.name).ext }}</span>
                        </span>
                      </button>
                      <button
                        type="button"
                        class="btn btn-sm btn-icon text-danger contract-file-remove"
                        :title="`Удалить ${file.name}`"
                        @click="$emit('delete-file', { doc, kind: file.kind, name: file.name })"
                      >
                        <i class="fas fa-trash"></i>
                      </button>
                    </div>
                  </div>
                  <span v-else class="text-muted small">Файлов нет</span>
                </td>
                <td class="contract-col-action">
                  <button
                    class="btn btn-sm contract-inline-action"
                    :class="doc.pdf_storage_path ? fileActionClass(doc.pdf_file_name || 'pdf') : 'btn-outline-primary'"
                    @click="doc.pdf_storage_path ? $emit('download', { doc, kind: 'pdf' }) : $emit('open-upload', { docType: doc.doc_type, doc, fileKind: 'pdf' })"
                  >
                    <i class="fas" :class="doc.pdf_storage_path ? 'fa-download' : 'fa-upload'"></i>
                    PDF
                  </button>
                </td>
                <td class="contract-col-action">
                  <button
                    class="btn btn-sm contract-inline-action"
                    :class="doc.edit_storage_path ? fileActionClass(doc.edit_file_name || 'edit') : 'btn-outline-primary'"
                    @click="doc.edit_storage_path ? $emit('download', { doc, kind: 'edit' }) : $emit('open-upload', { docType: doc.doc_type, doc, fileKind: 'edit' })"
                  >
                    <i class="fas" :class="doc.edit_storage_path ? 'fa-download' : 'fa-upload'"></i>
                    РЕД
                  </button>
                </td>
                <td class="contract-col-delete text-right">
                  <button class="btn btn-sm btn-icon text-danger" @click="$emit('delete-document', doc)">
                    <i class="fas fa-trash"></i>
                  </button>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ContractDocumentsTab',
  props: {
    filteredDocumentsList: { type: Array, required: true },
    documentAmountHelpText: { type: String, required: true },
    documentTypeBadgeClass: { type: Function, required: true },
    documentTypeLabel: { type: Function, required: true },
    documentAmountAllowed: { type: Function, required: true },
    documentAmountInputValue: { type: Function, required: true },
    onDocumentAmountFocus: { type: Function, required: true },
    onDocumentAmountInput: { type: Function, required: true },
    onDocumentAmountBlur: { type: Function, required: true },
    shortProductName: { type: Function, required: true },
    docStatusClass: { type: Function, required: true },
    getDocumentFiles: { type: Function, required: true },
    fileActionClass: { type: Function, required: true },
    fileIconClass: { type: Function, required: true },
    fileNameParts: { type: Function, required: true },
  },
  emits: ['open-invoice-products', 'update-status', 'download', 'delete-file', 'open-upload', 'delete-document']
}
</script>

<style scoped>
.contract-tab--documents { padding-top: 2px; display: flex; flex-direction: column; gap: 12px; }

.contract-panel {
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
  padding: 0 !important;
}

.contract-flat-section__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 0;
  padding: 16px 18px 12px;
}

.contract-type-pill {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 14px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 0.92rem;
  border: 1px solid transparent;
}
.contract-type-pill--violet {
  background: #f3ebff; color: #7c3aed; border-color: #ddccff;
}
.contract-type-pill--blue {
  background: #eef4ff; color: #2563eb; border-color: #cfe0ff;
}
.contract-type-pill--sky {
  background: #ebf5ff; color: #2563eb; border-color: #cbe0ff;
}
.contract-type-pill--orange {
  background: #fff3e3; color: #ea580c; border-color: #ffd8ad;
}
.contract-type-pill--gray {
  background: #f3f4f6; color: #6b7280; border-color: #e5e7eb;
}

.contract-inline-action {
  min-width: 96px;
  min-height: 34px;
  border-radius: 8px;
  box-shadow: none;
  gap: 6px;
  justify-content: center;
}

.contract-col-type { width: 1%; white-space: nowrap; }
.contract-col-number { width: 56px; white-space: nowrap; }
.contract-col-status { width: 214px; }
.contract-col-action { width: 108px; white-space: nowrap; }
.contract-col-delete { width: 48px; }
.contract-col-amount { width: 150px; min-width: 140px; }
.contract-col-products { width: 240px; min-width: 210px; }
.contract-files-cell { min-width: 0; }

.contract-files-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.contract-file-row {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}
.contract-file-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-width: 0;
  padding: 0;
  border: none;
  background: transparent;
  color: #334155;
  text-align: left;
}
.contract-file-link:hover .contract-file-link__name { color: #0f172a; }
.contract-file-link__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 7px;
  flex: 0 0 auto;
  border: 1px solid transparent;
  font-size: 0.85rem;
}
.contract-file-link__name {
  min-width: 0;
  display: inline-flex;
  align-items: baseline;
  gap: 0;
  font-size: 0.88rem;
  line-height: 1.2;
}
.contract-file-link__base {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.contract-file-link__ext {
  flex: 0 0 auto;
  white-space: nowrap;
  font-weight: 700;
}
.contract-file-remove {
  flex: 0 0 auto;
  width: 26px;
  height: 26px;
  border-radius: 7px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.file-action {
  border-width: 1px;
  border-style: solid;
  background: #fff;
}
.file-action--pdf { color: #dc2626; border-color: #fecaca; background: #fff5f5; }
.file-action--pdf:hover { background: #fee2e2; border-color: #fca5a5; }
.file-action--word { color: #2563eb; border-color: #bfdbfe; background: #eff6ff; }
.file-action--word:hover { background: #dbeafe; border-color: #93c5fd; }
.file-action--excel { color: #15803d; border-color: #bbf7d0; background: #f0fdf4; }
.file-action--excel:hover { background: #dcfce7; border-color: #86efac; }
.file-action--other { color: #4b5563; border-color: #d1d5db; background: #f9fafb; }
.file-action--other:hover { background: #f3f4f6; border-color: #cbd5e1; }

.contract-amount-heading {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.contract-amount-help {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: rgba(37, 99, 235, 0.12);
  color: #2563eb;
  font-size: 11px;
  font-weight: 700;
  cursor: help;
  line-height: 1;
}

.document-amount-cell { display: flex; align-items: center; }

.invoice-product-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.invoice-product-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  min-width: 0;
  max-width: 154px;
}
.invoice-product-chip {
  display: inline-flex;
  align-items: center;
  max-width: 86px;
  min-height: 22px;
  padding: 2px 7px;
  border-radius: 999px;
  background: rgba(245, 158, 11, 0.14);
  border: 1px solid rgba(245, 158, 11, 0.28);
  color: #92400e;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.invoice-product-chip--more {
  background: rgba(15, 23, 42, 0.08);
  border-color: rgba(15, 23, 42, 0.12);
  color: #475569;
}
.invoice-products-edit { white-space: nowrap; }

.contract-documents-table .contract-flat-section__header { display: none; }
.contract-documents-table { overflow: hidden; }
.contract-documents-table .contract-table-wrap {
  border-top: none;
  border-radius: 16px;
}

.contract-table-wrap {
  overflow: auto;
  border-top: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 0 0 14px 14px;
  background: rgba(255, 255, 255, 0.92);
}
.contract-table-wrap--flat {
  border-radius: 0 0 14px 14px;
  background: #fff;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 180px;
  padding: 1.25rem 1rem;
  border: 1px dashed rgba(148, 163, 184, 0.34);
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.82);
  text-align: center;
}
.empty-state i { font-size: 2.6rem; color: #c2ccd8; margin-bottom: 1rem; }
.empty-state p { margin: 0 0 0.5rem; font-size: 1rem; font-weight: 600; color: #1f2937; }

:deep(.table) { margin: 0; min-width: 100%; }
:deep(.table thead th) {
  padding: 14px 16px;
  border-top: none;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
  background: #fafbfd;
  color: #7b8798;
  font-size: 0.74rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  vertical-align: middle;
}
:deep(.table tbody td) {
  padding: 18px 16px;
  border-top: 1px solid rgba(15, 23, 42, 0.06);
  vertical-align: middle;
  color: #111827;
}
:deep(.table tbody tr:hover td) { background: rgba(248, 250, 252, 0.95); }

:deep(.form-control), .status-select {
  min-height: 36px;
  border-radius: 10px;
  border-color: rgba(15, 23, 42, 0.12);
  background: #fff;
  box-shadow: none;
}
:deep(.form-control:focus), .status-select:focus {
  border-color: rgba(37, 99, 235, 0.45);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.14);
}

.status-select.status-draft { border-color: #a8b1c7; background-color: #f4f6fb; }
.status-select.status-signing { border-color: #f6c26b; background-color: #fff7e6; }
.status-select.status-signed { border-color: #58c27d; background-color: #ecf9f0; }
.status-select.status-canceled { border-color: #f08a8a; background-color: #fdeeee; }

@media (max-width: 768px) {
  :deep(.table thead th), :deep(.table tbody td) { padding: 12px 12px; }
}
</style>
