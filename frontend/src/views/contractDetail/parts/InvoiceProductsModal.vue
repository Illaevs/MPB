<template>
  <div v-if="show" class="modal-overlay" v-modal-close="() => $emit('close')">
    <div class="modal-content" style="max-width: 620px;" @click.stop>
      <div class="modal-header">
        <h3 class="m-0">Товары накладной №{{ invoiceProductsDoc?.number_in_contract || '—' }}</h3>
        <button class="btn btn-sm btn-secondary" @click="$emit('close')">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <div class="modal-body">
        <div v-if="dealProducts.length" class="invoice-product-selector invoice-product-selector--modal">
          <label
            v-for="product in sortedDealProducts"
            :key="product.id"
            class="invoice-product-option"
          >
            <input
              type="checkbox"
              :value="product.id"
              :checked="invoiceProductIds.includes(product.id)"
              @change="toggleId(product.id, $event.target.checked)"
            >
            <span>{{ dealProductName(product) }}</span>
          </label>
        </div>
        <div v-else class="empty-state">
          <i class="fas fa-box-open"></i>
          <p>Товары сделки не найдены</p>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" @click="$emit('close')">Отмена</button>
        <button type="button" class="btn btn-primary" :disabled="savingInvoiceProducts" @click="$emit('save')">
          <i v-if="savingInvoiceProducts" class="fas fa-spinner fa-spin"></i>
          Сохранить
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'InvoiceProductsModal',
  props: {
    show: Boolean,
    invoiceProductsDoc: { type: Object, default: null },
    invoiceProductIds: { type: Array, required: true },
    savingInvoiceProducts: Boolean,
    dealProducts: { type: Array, required: true },
    sortedDealProducts: { type: Array, required: true },
    dealProductName: { type: Function, required: true },
  },
  emits: ['close', 'save', 'toggle-id'],
  methods: {
    toggleId(id, checked) {
      this.$emit('toggle-id', { id, checked })
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
.invoice-product-selector--modal { max-height: 420px; }
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
</style>
