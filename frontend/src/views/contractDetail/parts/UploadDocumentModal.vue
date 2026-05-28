<template>
  <div v-if="show" class="modal-overlay" v-modal-close="() => $emit('close')">
    <div class="modal-content" style="max-width: 480px;" @click.stop>
      <div class="modal-header">
        <h3 class="m-0">{{ uploadForm.documentId ? 'Загрузить файл' : 'Новый документ' }}</h3>
        <button class="btn btn-sm btn-secondary" @click="$emit('close')">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <form class="modal-body" @submit.prevent="$emit('submit')">
        <div class="form-group">
          <label>Тип документа</label>
          <select
            :value="uploadForm.docType"
            class="form-control"
            :disabled="!!uploadForm.documentId"
            @change="updateField('docType', $event.target.value)"
          >
            <option v-for="type in docTypes" :key="type.key" :value="type.key">
              {{ type.label }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>Тип файла</label>
          <select
            :value="uploadForm.fileKind"
            class="form-control"
            @change="updateField('fileKind', $event.target.value)"
          >
            <option value="pdf">PDF</option>
            <option value="edit">Ред. формат</option>
          </select>
        </div>
        <div class="form-group" v-if="!uploadForm.documentId">
          <label>Статус</label>
          <select
            :value="uploadForm.status"
            class="form-control"
            @change="updateField('status', $event.target.value)"
          >
            <option value="draft">Черновик</option>
            <option value="signing">На подписании</option>
            <option value="signed">Подписан</option>
            <option value="canceled">Аннулирован</option>
          </select>
        </div>
        <div class="form-group" v-if="showUploadAmountField">
          <label class="contract-amount-label">
            Сумма
            <span class="contract-amount-help" :title="uploadAmountHelpText" tabindex="0">?</span>
          </label>
          <input
            :value="uploadAmountInputValue"
            type="text"
            inputmode="decimal"
            min="0"
            class="form-control"
            @focus="onUploadAmountFocus"
            @input="onUploadAmountInput"
            @blur="onUploadAmountBlur"
            @keydown.enter="$event.target.blur()"
          />
        </div>
        <div class="form-group" v-if="showUploadInvoiceProducts">
          <label>Товары сделки</label>
          <div v-if="dealProducts.length" class="invoice-product-selector">
            <label
              v-for="product in sortedDealProducts"
              :key="product.id"
              class="invoice-product-option"
            >
              <input
                type="checkbox"
                :value="product.id"
                :checked="uploadForm.productIds.includes(product.id)"
                @change="toggleProductId(product.id, $event.target.checked)"
              >
              <span>{{ dealProductName(product) }}</span>
            </label>
          </div>
          <small v-else class="text-muted">В сделке договора товары не найдены.</small>
        </div>
        <div class="form-group">
          <label>Файл</label>
          <div
            class="upload-dropzone"
            :class="{ 'is-dragover': isDropActive }"
            @click="triggerUploadFile"
            @dragenter.prevent="$emit('drop-over', $event)"
            @dragover.prevent="$emit('drop-over', $event)"
            @dragleave.prevent="$emit('drop-leave')"
            @drop.prevent="$emit('drop-file', $event)"
          >
            <input
              ref="uploadFileInputEl"
              type="file"
              class="d-none"
              @change="$emit('file-change', $event)"
            />
            <i class="fas fa-cloud-upload-alt"></i>
            <div class="upload-dropzone-text">
              <span v-if="uploadForm.file">{{ uploadForm.file.name }}</span>
              <span v-else>Перетащите файл сюда или нажмите для выбора</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="$emit('close')">Отмена</button>
          <button type="submit" class="btn btn-primary" :disabled="uploading">
            <i v-if="uploading" class="fas fa-spinner fa-spin"></i>
            Загрузить
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
export default {
  name: 'UploadDocumentModal',
  props: {
    show: Boolean,
    uploadForm: { type: Object, required: true },
    docTypes: { type: Array, required: true },
    uploading: Boolean,
    isDropActive: Boolean,
    showUploadAmountField: Boolean,
    showUploadInvoiceProducts: Boolean,
    uploadAmountInputValue: { type: String, default: '' },
    uploadAmountHelpText: { type: String, default: '' },
    dealProducts: { type: Array, required: true },
    sortedDealProducts: { type: Array, required: true },
    dealProductName: { type: Function, required: true },
    onUploadAmountFocus: { type: Function, required: true },
    onUploadAmountInput: { type: Function, required: true },
    onUploadAmountBlur: { type: Function, required: true },
  },
  emits: ['close', 'submit', 'update-field', 'toggle-product', 'drop-over', 'drop-leave', 'drop-file', 'file-change', 'register-input'],
  mounted() {
    if (this.$refs.uploadFileInputEl) {
      this.$emit('register-input', this.$refs.uploadFileInputEl)
    }
  },
  watch: {
    show(val) {
      if (val) {
        this.$nextTick(() => {
          if (this.$refs.uploadFileInputEl) {
            this.$emit('register-input', this.$refs.uploadFileInputEl)
          }
        })
      }
    }
  },
  methods: {
    updateField(key, value) {
      this.$emit('update-field', { key, value })
    },
    toggleProductId(id, checked) {
      this.$emit('toggle-product', { id, checked })
    },
    triggerUploadFile() {
      if (this.$refs.uploadFileInputEl) {
        this.$refs.uploadFileInputEl.click()
      }
    }
  }
}
</script>

<style scoped>
:deep(.modal-content) {
  border-radius: 18px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 28px 50px rgba(15, 23, 42, 0.16);
}
:deep(.form-control) {
  min-height: 36px;
  border-radius: 10px;
  border-color: rgba(15, 23, 42, 0.12);
  background: #fff;
  box-shadow: none;
}

.contract-amount-label {
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

.invoice-product-selector {
  display: grid;
  gap: 6px;
  max-height: 220px;
  overflow: auto;
  padding: 8px;
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-radius: 12px;
  background: rgba(248, 250, 252, 0.9);
}
.invoice-product-option {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 0;
  padding: 7px 8px;
  border-radius: 10px;
  cursor: pointer;
}
.invoice-product-option:hover {
  background: rgba(37, 99, 235, 0.08);
}

.upload-dropzone {
  border: 1px dashed rgba(59, 130, 246, 0.36);
  border-radius: 14px;
  padding: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  background: rgba(248, 250, 252, 0.92);
  transition: border-color 0.2s ease, background 0.2s ease;
}
.upload-dropzone i {
  font-size: 1.2rem;
  color: #2563eb;
}
.upload-dropzone-text {
  font-size: 0.92rem;
  color: #64748b;
  word-break: break-word;
}
.upload-dropzone.is-dragover {
  border-color: #2563eb;
  background: rgba(219, 234, 254, 0.72);
}
</style>
