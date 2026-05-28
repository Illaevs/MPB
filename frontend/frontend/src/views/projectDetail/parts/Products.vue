<template>
          <div
             v-if="activeTab === 'products'"
             id="panel-products"
             class="card h-100 d-flex flex-column overflow-hidden"
             role="tabpanel"
             aria-labelledby="tab-products"
          >
             <div class="products-card h-100 d-flex flex-column overflow-hidden">
                <div class="flex-grow-1 overflow-auto p-0">
                   <div class="estimate-toolbar border-bottom p-3 d-flex gap-2 align-center">
                      <input
                         v-model.trim="productSearch"
                         type="text"
                         class="form-control form-control-sm estimate-search"
                         placeholder="Поиск по смете"
                      >
                      <select v-model="productSort" class="form-control form-control-sm estimate-sort">
                         <option value="name_asc">По названию (А-Я)</option>
                         <option value="name_desc">По названию (Я-А)</option>
                         <option value="amount_desc">По сумме (убыв.)</option>
                         <option value="amount_asc">По сумме (возр.)</option>
                      </select>
                      <button class="btn btn-sm btn-primary estimate-add-btn" @click="openAddProductModal">
                         <i class="fas fa-plus mr-1"></i> Добавить
                      </button>
                   </div>
                   <div v-if="dealProducts.length" class="border-bottom px-3 py-3 d-flex justify-between align-center gap-3 flex-wrap">
                      <div class="small text-muted">
                         Выберите позиции состава проекта и массово измените ставку и режим НДС
                      </div>
                      <div class="d-flex align-center gap-2 flex-wrap">
                         <span class="small text-muted">Выбрано: {{ selectedDealProductIds.length }}</span>
                         <select v-model.number="bulkDealTaxRate" class="form-control form-control-sm" style="width: 110px;" :disabled="dealTaxUpdating">
                            <option v-for="rate in vatRateOptions" :key="`deal-bulk-vat-${rate}`" :value="rate">{{ rate }}%</option>
                         </select>
                         <label class="form-check d-flex align-center gap-1 mb-0 small text-muted">
                            <input v-model="bulkDealTaxIncluded" type="checkbox" class="form-check-input" :disabled="dealTaxUpdating">
                            <span>НДС в цене</span>
                         </label>
                         <button class="btn btn-sm btn-outline-primary" :disabled="!selectedDealProductIds.length || dealTaxUpdating" @click="applyBulkDealTaxRate">
                            <i v-if="dealTaxUpdating" class="fas fa-spinner fa-spin mr-1"></i>
                            <span v-else>Применить</span>
                         </button>
                      </div>
                   </div>
                   <div v-if="loading" class="spinner mx-auto my-5"></div>
                   <div v-else-if="!dealProducts.length" class="text-center text-muted py-5">
                      <i class="fas fa-box-open fa-3x mb-3 text-light-gray"></i>
                      <p>Смета пуста</p>
                   </div>
                   <div v-else-if="!displayDealProducts.length" class="text-center text-muted py-5">
                      <i class="fas fa-search fa-2x mb-3 text-light-gray"></i>
                      <p>По вашему запросу ничего не найдено</p>
                   </div>
                   <table v-else class="table table-hover m-0">
                      <thead class="sticky-top bg-surface">
                         <tr>
                            <th style="width: 44px;">
                               <input type="checkbox" :checked="allDealProductsSelected" @change="toggleAllDealProducts">
                            </th>
                            <th>Наименование</th>
                            <th class="deal-product-invoices-col">Накладные</th>
                            <th class="text-right">Кол-во</th>
                            <th class="text-right">Цена</th>
                            <th class="text-center">НДС в цене</th>
                            <th class="text-right">НДС</th>
                            <th class="text-right">Сумма НДС</th>
                            <th class="text-right">Итого</th>
                            <th class="text-right" style="width: 80px;"></th>
                         </tr>
                      </thead>
                      <tbody>
                         <tr v-for="item in displayDealProducts" :key="item.id">
                            <td class="text-center">
                               <input v-model="selectedDealProductIds" type="checkbox" :value="item.id">
                            </td>
                            <td>
                               <div class="fw-500">{{ item.custom_name || item.product?.name || '-' }}</div>
                               <small v-if="item.custom_name && item.product" class="text-muted">Каталог: {{ item.product.name }}</small>
                            </td>
                            <td class="deal-product-invoices-col">
                               <div v-if="item.invoice_links && item.invoice_links.length" class="deal-product-invoice-chips">
                                  <span
                                     v-for="link in item.invoice_links.slice(0, 3)"
                                     :key="`${item.id}-${link.document_id}`"
                                     class="deal-product-invoice-chip"
                                     :title="invoiceChipLabel(link)"
                                  >
                                     {{ invoiceChipLabel(link) }}
                                  </span>
                                  <span v-if="item.invoice_links.length > 3" class="deal-product-invoice-chip deal-product-invoice-chip--more">
                                     +{{ item.invoice_links.length - 3 }}
                                  </span>
                               </div>
                               <span v-else class="text-muted small">—</span>
                            </td>
                            <td class="text-right">{{ item.quantity }} {{ item.unit }}</td>
                            <td class="text-right">{{ formatCurrency(item.unit_price) }}</td>
                            <td class="text-center">
                               <input
                                  type="checkbox"
                                  :checked="Boolean(item.tax_included)"
                                  :disabled="dealTaxUpdating"
                                  @change="updateDealProductTaxIncluded(item, $event.target.checked)"
                               >
                            </td>
                            <td class="text-right">
                               <select
                                  class="form-control form-control-sm d-inline-block"
                                  style="width: 88px;"
                                  :value="normalizeTaxRate(item.tax_rate)"
                                  :disabled="dealTaxUpdating"
                                  @change="updateDealProductTaxRate(item, $event.target.value)"
                               >
                                  <option v-for="rate in vatRateOptions" :key="`deal-row-vat-${item.id}-${rate}`" :value="rate">{{ rate }}%</option>
                               </select>
                            </td>
                            <td class="text-right">{{ formatCurrency(item.tax_amount || 0) }}</td>
                            <td class="text-right fw-600">{{ formatCurrency(item.final_price) }}</td>
                            <td class="text-right">
                               <div class="d-flex justify-end gap-1">
                                  <button class="btn btn-sm btn-icon" @click="editDealProduct(item)"><i class="fas fa-pen"></i></button>
                                  <button class="btn btn-sm btn-icon text-danger" @click="removeDealProduct(item)"><i class="fas fa-trash"></i></button>
                               </div>
                            </td>
                         </tr>
                      </tbody>
                      <tfoot class="bg-light fw-600">
                         <tr>
                            <td colspan="8" class="text-right">Без НДС:</td>
                            <td class="text-right">{{ formatCurrency(totalAmount) }}</td>
                            <td></td>
                         </tr>
                         <tr v-for="row in dealVatRows" :key="`deal-vat-row-${row.rate}`">
                            <td colspan="8" class="text-right">НДС ({{ row.rate }}%):</td>
                            <td class="text-right">{{ formatCurrency(row.taxAmount) }}</td>
                            <td></td>
                         </tr>
                         <tr>
                            <td colspan="8" class="text-right">НДС всего:</td>
                            <td class="text-right">{{ formatCurrency(vatAmount) }}</td>
                            <td></td>
                         </tr>
                         <tr>
                            <td colspan="8" class="text-right">Всего:</td>
                            <td class="text-right text-primary">{{ formatCurrency(totalWithVat) }}</td>
                            <td></td>
                         </tr>
                      </tfoot>
                   </table>
                </div>
             </div>
          </div>
</template>

<script>

export default {
  name: 'Products',
  
  props: { state: { type: Object, required: true } },
  setup(props) {
    return { ...props.state }
  }
}
</script>
