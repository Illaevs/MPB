
<template>
  <div class="lead-detail-view h-100 d-flex flex-column">
    <!-- Unified header (по образцу ProjectDetail) -->
    <div class="unified-header flex-shrink-0">
      <div class="unified-header-inner">
        <div class="unified-header-left">
          <button class="unified-back-btn" @click="$router.push('/leads')" title="К списку лидов">
            <i class="fas fa-arrow-left"></i>
          </button>
          <div class="unified-title-group">
            <h1 class="unified-project-name">{{ lead.title || 'Загрузка...' }}</h1>
            <span v-if="lead.obj_name" class="unified-obj-name">{{ lead.obj_name }}</span>
          </div>
        </div>

        <nav class="unified-nav" @keydown="onTabKeydown" role="tablist" aria-label="Разделы лида">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            :id="`tab-${tab.id}`"
            type="button"
            class="unified-nav-item"
            :class="{ active: activeTab === tab.id }"
            role="tab"
            :aria-selected="activeTab === tab.id ? 'true' : 'false'"
            :tabindex="activeTab === tab.id ? 0 : -1"
            @click="setActiveTab(tab.id)"
          >
            <i :class="tab.icon" class="mr-1"></i>
            <span>{{ tab.name }}</span>
          </button>
        </nav>

        <div class="unified-header-right">
          <div v-if="lead.status" class="ld-status-wrap">
            <button
              type="button"
              class="ld-status-badge"
              :class="`ld-status-${lead.status}`"
              :disabled="ldStatusBusy"
              @click="ldStatusMenuOpen = !ldStatusMenuOpen"
            >
              <span class="ld-status-dot"></span>{{ getStatusText(lead.status) }}
              <i v-if="ldStatusBusy" class="fas fa-spinner fa-spin ml-1"></i>
              <i v-else class="fas fa-caret-down ml-1"></i>
            </button>
            <transition name="ld-pop">
              <div v-if="ldStatusMenuOpen" class="ld-status-menu" v-click-outside="() => ldStatusMenuOpen = false">
                <button
                  v-for="opt in statusOptions.filter(s => s.key !== 'converted')"
                  :key="opt.key"
                  type="button"
                  class="ld-status-menu__item"
                  :class="[`ld-status-${opt.key}`, { active: lead.status === opt.key }]"
                  @click="onChangeStatus(opt.key)"
                >
                  <span class="ld-status-dot"></span>{{ opt.label }}
                  <i v-if="lead.status === opt.key" class="fas fa-check ml-auto"></i>
                </button>
              </div>
            </transition>
          </div>

          <router-link
            v-if="lead.deal_id"
            class="btn btn-sm btn-outline-primary"
            :to="`/deals?deal_id=${lead.deal_id}`"
          >
            <i class="fas fa-up-right-from-square mr-1"></i>Сделка
          </router-link>
          <button
            v-else
            class="btn btn-sm btn-primary"
            :disabled="saving"
            title="Конвертировать в сделку"
            @click="convertLead"
          >
            <i v-if="saving" class="fas fa-spinner fa-spin mr-1"></i>
            <i v-else class="fas fa-arrow-right-arrow-left mr-1"></i>Конвертировать
          </button>

          <button class="unified-action-btn" title="Редактировать" @click="openEditModal">
            <i class="fas fa-edit"></i>
          </button>
          <button class="unified-action-btn unified-action-btn--danger" title="Удалить лид" @click="deleteLead">
            <i class="fas fa-trash"></i>
          </button>
        </div>
      </div>
    </div>

    <div class="flex-grow-1 overflow-hidden position-relative lead-detail-body">
      <div v-show="activeTab === 'info'" class="h-100 overflow-auto scroll-container p-1">
        <div v-if="loadingLead" class="spinner mx-auto my-5"></div>
        <div v-else class="dashboard-grid h-100">
          <div class="dashboard-left d-flex flex-column gap-3">
            <div class="card p-4">
              <h3 class="card-title mb-3">Основная информация</h3>
              <div class="info-grid">
                <div class="info-row info-row--editable" @click="beginEdit('title')">
                  <span class="text-muted">Название</span>
                  <input
                    v-if="editingField === 'title'"
                    ref="inlineInputRef"
                    v-model="editDraft"
                    type="text"
                    class="info-edit-input"
                    :disabled="inlineSaving"
                    @click.stop
                    @keydown.enter.prevent="saveEdit"
                    @keydown.esc.prevent="cancelEdit"
                    @blur="saveEdit"
                  />
                  <span v-else class="fw-500 text-right info-row__value">{{ lead.title || '—' }}</span>
                </div>
                <div class="info-row info-row--editable" @click="beginEdit('obj_name')">
                  <span class="text-muted">Наименование объекта</span>
                  <input
                    v-if="editingField === 'obj_name'"
                    ref="inlineInputRef"
                    v-model="editDraft"
                    type="text"
                    class="info-edit-input"
                    :disabled="inlineSaving"
                    @click.stop
                    @keydown.enter.prevent="saveEdit"
                    @keydown.esc.prevent="cancelEdit"
                    @blur="saveEdit"
                  />
                  <span v-else class="fw-500 text-right info-row__value">{{ lead.obj_name || '—' }}</span>
                </div>
                <div class="info-row info-row--editable" @click="beginEdit('address')">
                  <span class="text-muted">Адрес объекта</span>
                  <input
                    v-if="editingField === 'address'"
                    ref="inlineInputRef"
                    v-model="editDraft"
                    type="text"
                    class="info-edit-input"
                    :disabled="inlineSaving"
                    @click.stop
                    @keydown.enter.prevent="saveEdit"
                    @keydown.esc.prevent="cancelEdit"
                    @blur="saveEdit"
                  />
                  <span v-else class="fw-500 text-right info-row__value">{{ lead.address || '—' }}</span>
                </div>
                <div class="info-row info-row--editable" @click="beginEdit('object_type')">
                  <span class="text-muted">Тип объекта</span>
                  <select
                    v-if="editingField === 'object_type'"
                    ref="inlineInputRef"
                    v-model="editDraft"
                    class="info-edit-input"
                    :disabled="inlineSaving"
                    @click.stop
                    @change="saveEdit"
                    @keydown.esc.prevent="cancelEdit"
                    @blur="saveEdit"
                  >
                    <option value="">— не указан —</option>
                    <option v-for="t in objectTypes" :key="t" :value="t">{{ t }}</option>
                  </select>
                  <span v-else class="fw-500 text-right info-row__value">{{ lead.object_type || '—' }}</span>
                </div>
                <div class="info-row info-row--editable" @click="beginEdit('object_area')">
                  <span class="text-muted">Площадь</span>
                  <input
                    v-if="editingField === 'object_area'"
                    ref="inlineInputRef"
                    v-model="editDraft"
                    type="number"
                    min="0"
                    step="0.1"
                    class="info-edit-input"
                    :disabled="inlineSaving"
                    @click.stop
                    @keydown.enter.prevent="saveEdit"
                    @keydown.esc.prevent="cancelEdit"
                    @blur="saveEdit"
                  />
                  <span v-else class="fw-500 text-right info-row__value">{{ lead.object_area ? `${lead.object_area} м²` : '—' }}</span>
                </div>
                <div class="separator my-2"></div>
                <div class="info-row info-row--editable" @click="beginEdit('customer_id')">
                  <span class="text-muted">Заказчик</span>
                  <div
                    v-if="editingField === 'customer_id'"
                    class="info-edit-select"
                    @click.stop
                    @keydown.esc.prevent="cancelEdit"
                  >
                    <CompanySmartSelect
                      v-model="editDraft"
                      :options="customerCompanies"
                      placeholder="Не выбран"
                      @update:modelValue="saveEdit"
                    />
                    <button type="button" class="info-edit-cancel" title="Отмена" @click.stop="cancelEdit">
                      <i class="fas fa-times"></i>
                    </button>
                  </div>
                  <span v-else class="fw-500 text-right info-row__value">{{ getCompanyName(lead.customer_id) || '—' }}</span>
                </div>
                <div class="info-row info-row--editable" @click="beginEdit('responsible_user_id')">
                  <span class="text-muted">Ответственный</span>
                  <select
                    v-if="editingField === 'responsible_user_id'"
                    ref="inlineInputRef"
                    v-model="editDraft"
                    class="info-edit-input"
                    :disabled="inlineSaving"
                    @click.stop
                    @change="saveEdit"
                    @keydown.esc.prevent="cancelEdit"
                    @blur="saveEdit"
                  >
                    <option value="">Не назначен</option>
                    <option v-for="u in users" :key="u.id" :value="u.id">{{ u.full_name || u.email || u.id }}</option>
                  </select>
                  <span v-else class="fw-500 text-right info-row__value info-row__value--with-avatar">
                    <template v-if="lead.responsible_user_id && responsibleUser">
                      <UiAvatar
                        :src="responsibleUser.avatar_url"
                        :name="responsibleUser.full_name || responsibleUser.email || '?'"
                        size="xs"
                      />
                      <span>{{ responsibleUser.full_name || responsibleUser.email || '—' }}</span>
                    </template>
                    <span v-else>—</span>
                  </span>
                </div>
                <div class="separator my-2"></div>
                <div class="info-row info-row--editable" @click="beginEdit('advance_percent')">
                  <span class="text-muted">% аванса</span>
                  <input
                    v-if="editingField === 'advance_percent'"
                    ref="inlineInputRef"
                    v-model="editDraft"
                    type="number"
                    min="0"
                    max="100"
                    step="1"
                    class="info-edit-input"
                    :disabled="inlineSaving"
                    @click.stop
                    @keydown.enter.prevent="saveEdit"
                    @keydown.esc.prevent="cancelEdit"
                    @blur="saveEdit"
                  />
                  <span v-else class="fw-500 text-right info-row__value">{{ lead.advance_percent ?? 0 }}%</span>
                </div>
                <!--
                  Ставка НДС лида в info-row убрана: единой ставки больше
                  нет, каждый товар несёт свою (см. таблицу «Состав
                  проекта», колонка НДС). Итоговая по лиду — производная
                  от суммы tax_amount всех товаров.
                -->
                <div class="info-row">
                  <span class="text-muted">Стоимость</span>
                  <span class="fw-600 text-right text-primary">{{ formatCurrency(totalAmount) }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="dashboard-right card p-0 d-flex flex-column h-100 overflow-hidden">
            <div class="card-header border-bottom p-4 d-flex justify-between align-center">
              <h3 class="card-title m-0">История событий</h3>
            </div>
            <div class="flex-grow-1 overflow-auto p-2">
              <LeadTimeline
                :lead-id="route.params.id"
                :users="users"
                :current-user-id="currentUserId"
                @lead-updated="loadLead"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- KP tab — рабочее пространство КП (список / превью / версии). -->
      <div v-show="activeTab === 'kp'" class="h-100 p-2">
        <LeadKpWorkspace
          :lead-id="route.params.id"
          :kp-documents="kpDocuments"
          :kp-templates="kpTemplates"
          :kp-bindings="kpBindings"
          :can-manage-templates="canManageKpTemplates"
          :loading="loadingKp"
          @create-kp="openKpCreateModal"
          @open-templates="openKpTemplatesModal"
          @reload="loadKpDocuments"
        />
      </div>

      <!-- Composition tab (товары / услуги) -->
      <div v-show="activeTab === 'composition'" class="h-100 overflow-auto scroll-container p-2">
        <div class="card p-0 d-flex flex-column overflow-hidden">
          <div class="card-header border-bottom p-4 d-flex justify-between align-center">
            <h3 class="card-title m-0">Состав проекта / перечень услуг</h3>
            <button class="btn btn-sm btn-primary" @click="showAddProductModal = true">
              <i class="fas fa-plus mr-1"></i> Добавить
            </button>
          </div>
          <div class="overflow-auto p-0">
            <div v-if="productsLoading" class="spinner mx-auto my-5"></div>
            <div v-else-if="!leadProducts.length" class="text-center text-muted py-5">
              <i class="fas fa-box-open fa-3x mb-3 text-light-gray"></i>
              <p>Товаров нет</p>
            </div>
            <template v-else>
              <div class="border-bottom px-4 py-3 d-flex justify-between align-center gap-3 flex-wrap">
                <div class="small text-muted">
                  Отдельная ставка НДС на каждый товар
                </div>
                <div class="d-flex align-center gap-2 flex-wrap">
                  <span class="small text-muted">Выбрано: {{ selectedLeadProductIds.length }}</span>
                  <select v-model.number="bulkLeadTaxRate" class="form-control form-control-sm" style="width: 110px;" :disabled="leadTaxUpdating">
                    <option v-for="rate in vatRateOptions" :key="`lead-bulk-vat-${rate}`" :value="rate">{{ rate }}%</option>
                  </select>
                  <button class="btn btn-sm btn-outline-primary" :disabled="!selectedLeadProductIds.length || leadTaxUpdating" @click="applyBulkLeadTaxRate">
                    <i v-if="leadTaxUpdating" class="fas fa-spinner fa-spin mr-1"></i>
                    <span v-else>Применить</span>
                  </button>
                </div>
              </div>
              <table class="table table-hover m-0">
                <thead class="sticky-top bg-surface">
                  <tr>
                    <th style="width: 44px;">
                      <input type="checkbox" :checked="allLeadProductsSelected" @change="toggleAllLeadProducts">
                    </th>
                    <th>Наименование</th>
                    <th class="text-right">Кол-во</th>
                    <th class="text-right">Цена</th>
                    <th class="text-right">НДС</th>
                    <th class="text-right">Сумма НДС</th>
                    <th class="text-right">Итого</th>
                    <th class="text-right" style="width: 80px;"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in leadProducts" :key="item.id">
                    <td class="text-center">
                      <input v-model="selectedLeadProductIds" type="checkbox" :value="item.id">
                    </td>
                    <td>
                      <div class="fw-500">{{ item.custom_name || getProductName(item.product_id) || '-' }}</div>
                      <small v-if="item.custom_name && getProductName(item.product_id)" class="text-muted">
                        В каталоге: {{ getProductName(item.product_id) }}
                      </small>
                    </td>
                    <td class="text-right">{{ item.quantity }} {{ item.unit || '-' }}</td>
                    <td class="text-right">{{ formatCurrency(item.unit_price || 0) }}</td>
                    <td class="text-right">
                      <select
                        class="form-control form-control-sm d-inline-block"
                        style="width: 88px;"
                        :value="normalizeTaxRate(item.tax_rate)"
                        :disabled="leadTaxUpdating"
                        @change="updateLeadProductTaxRate(item, $event.target.value)"
                      >
                        <option v-for="rate in vatRateOptions" :key="`lead-row-vat-${item.id}-${rate}`" :value="rate">{{ rate }}%</option>
                      </select>
                    </td>
                    <td class="text-right">{{ formatCurrency(item.tax_amount || 0) }}</td>
                    <td class="text-right fw-600">{{ formatCurrency(item.final_price || 0) }}</td>
                    <td class="text-right">
                      <div class="d-flex justify-end gap-1">
                        <button class="btn btn-sm btn-icon" @click="editLeadProduct(item)"><i class="fas fa-pen"></i></button>
                        <button class="btn btn-sm btn-icon text-danger" @click="removeLeadProduct(item)"><i class="fas fa-trash"></i></button>
                      </div>
                    </td>
                  </tr>
                </tbody>
                <tfoot class="bg-light fw-600">
                  <tr>
                    <td colspan="6" class="text-right">Без НДС:</td>
                    <td class="text-right">{{ formatCurrency(totalWithoutVat) }}</td>
                    <td></td>
                  </tr>
                  <tr v-for="row in leadVatRows" :key="`lead-vat-row-${row.rate}`">
                    <td colspan="6" class="text-right">НДС ({{ row.rate }}%):</td>
                    <td class="text-right">{{ formatCurrency(row.taxAmount) }}</td>
                    <td></td>
                  </tr>
                  <tr>
                    <td colspan="6" class="text-right">НДС всего:</td>
                    <td class="text-right">{{ formatCurrency(totalVatAmount) }}</td>
                    <td></td>
                  </tr>
                  <tr>
                    <td colspan="6" class="text-right">Итого:</td>
                    <td class="text-right text-primary">{{ formatCurrency(totalAmount) }}</td>
                    <td></td>
                  </tr>
                </tfoot>
              </table>
            </template>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showAddProductModal" class="modal-overlay" v-modal-close="closeAddModal">
      <div class="modal-content modal-product" @click.stop style="max-width: 600px;">
        <div class="modal-header">
          <h4>Добавить товар</h4>
          <button class="btn-close" @click="closeAddModal"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="form-group mb-3">
            <label>Товар из каталога</label>
            <ProductSmartSelect
              input-id="lead-product-select"
              v-model="selectedProductId"
              :options="availableProducts"
              placeholder="Найти товар"
            />
          </div>

          <div v-if="selectedProduct" class="p-3 bg-light rounded">
            <div class="form-group mb-2">
              <label>Наименование (можно изменить)</label>
              <input v-model="leadProductForm.custom_name" class="form-control" :placeholder="selectedProduct.name">
            </div>
            <div class="d-flex gap-2 mb-2">
              <div class="form-group w-50">
                <label>Цена</label>
                <input type="number" step="0.01" v-model.number="leadProductForm.custom_price" class="form-control" :placeholder="selectedProduct.base_price || 0">
              </div>
              <div class="form-group w-50">
                <label>Ед. изм.</label>
                <input v-model="leadProductForm.unit" class="form-control">
              </div>
            </div>
            <div class="d-flex gap-2">
              <div class="form-group w-50">
                <label>Количество</label>
                <input type="number" step="0.01" v-model.number="leadProductForm.quantity" class="form-control">
              </div>
              <div class="form-group w-50">
                <label>Скидка (%)</label>
                <input type="number" step="0.01" v-model.number="leadProductForm.discount_percent" class="form-control">
              </div>
            </div>
            <div class="form-group mt-2 mb-0">
              <label>Ставка НДС</label>
              <select v-model.number="leadProductForm.tax_rate" class="form-control">
                <option v-for="rate in vatRateOptions" :key="`lead-form-vat-${rate}`" :value="rate">{{ rate }}%</option>
              </select>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeAddModal">Отмена</button>
          <button class="btn btn-primary" @click="addProductToLead" :disabled="!selectedProduct || productSaving">
            <i v-if="productSaving" class="fas fa-spinner fa-spin"></i>
            <span v-else>Добавить</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="showEditProductModal" class="modal-overlay" v-modal-close="closeEditModal">
      <div class="modal-content" @click.stop style="max-width: 600px;">
        <div class="modal-header">
          <h4>Редактировать товар</h4>
          <button class="btn-close" @click="closeEditModal"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="p-3 bg-light rounded">
            <div class="form-group mb-2">
              <label>Наименование (можно изменить)</label>
              <input v-model="leadProductForm.custom_name" class="form-control">
            </div>
            <div class="d-flex gap-2 mb-2">
              <div class="form-group w-50">
                <label>Цена</label>
                <input type="number" step="0.01" v-model.number="leadProductForm.custom_price" class="form-control">
              </div>
              <div class="form-group w-50">
                <label>Ед. изм.</label>
                <input v-model="leadProductForm.unit" class="form-control">
              </div>
            </div>
            <div class="d-flex gap-2">
              <div class="form-group w-50">
                <label>Количество</label>
                <input type="number" step="0.01" v-model.number="leadProductForm.quantity" class="form-control">
              </div>
              <div class="form-group w-50">
                <label>Скидка (%)</label>
                <input type="number" step="0.01" v-model.number="leadProductForm.discount_percent" class="form-control">
              </div>
            </div>
            <div class="form-group mt-2 mb-0">
              <label>Ставка НДС</label>
              <select v-model.number="leadProductForm.tax_rate" class="form-control">
                <option v-for="rate in vatRateOptions" :key="`lead-edit-vat-${rate}`" :value="rate">{{ rate }}%</option>
              </select>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeEditModal">Отмена</button>
          <button class="btn btn-primary" @click="updateLeadProduct" :disabled="productSaving">
            <i v-if="productSaving" class="fas fa-spinner fa-spin"></i>
            <span v-else>Сохранить</span>
          </button>
        </div>
      </div>
    </div>
    <LeadFormModal
      v-model="showEditLeadModal"
      :lead="lead"
      :companies="companies"
      :users="users"
      :statuses="statusOptions.filter(s => s.key !== 'converted')"
      :saving="saving"
      @submit="onLeadFormSubmit"
      @cancel="closeEditLeadModal"
    />

    <div v-if="showKpCreateModal" class="modal-overlay" v-modal-close="closeKpCreateModal">
      <div class="modal-content" @click.stop style="max-width: 520px;">
        <div class="modal-header">
          <h4>Создать КП</h4>
          <button class="btn-close" @click="closeKpCreateModal"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Шаблон КП</label>
            <select v-model="kpForm.template_id" class="form-control">
              <option value="">Автовыбор</option>
              <option v-for="tpl in templateOptions" :key="tpl.id" :value="tpl.id">
                {{ tpl.name }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>Ставка НДС</label>
            <select v-model.number="kpForm.vat_rate" class="form-control">
              <option v-for="rate in vatRateOptions" :key="`kp-vat-${rate}`" :value="rate">{{ rate }}%</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeKpCreateModal">Отмена</button>
          <button class="btn btn-primary" @click="createKp" :disabled="kpSaving">
            <i v-if="kpSaving" class="fas fa-spinner fa-spin"></i>
            <span v-else>Создать</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="showKpTemplatesModal" class="modal-overlay" v-modal-close="closeKpTemplatesModal">
      <div class="modal-content" @click.stop style="max-width: 960px;">
        <div class="modal-header">
          <h4>Шаблоны КП</h4>
          <button class="btn-close" @click="closeKpTemplatesModal"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="d-grid gap-3" style="grid-template-columns: repeat(2, minmax(0, 1fr));">
            <div class="card p-3 mb-0">
              <h5 class="mb-3">Загрузка шаблона</h5>
              <div class="form-group">
                <label>Название</label>
                <input v-model="kpTemplateForm.name" class="form-control">
              </div>
              <div class="form-group">
                <label>DOCX шаблон</label>
                <input type="file" class="form-control" accept=".docx" @change="onTemplateDocxChange">
              </div>
              <div class="form-group">
                <label>PDF (опционально)</label>
                <input type="file" class="form-control" accept=".pdf" @change="onTemplatePdfChange">
              </div>
              <button class="btn btn-primary" @click="uploadKpTemplate" :disabled="kpTemplateSaving">
                <i v-if="kpTemplateSaving" class="fas fa-spinner fa-spin mr-1"></i>
                Загрузить
              </button>
            </div>

            <div class="card p-3 mb-0">
              <h5 class="mb-3">Привязка шаблона к компании</h5>
              <div class="form-group">
                <label>Шаблон</label>
                <select v-model="kpBindingForm.template_id" class="form-control">
                  <option value="">Не выбран</option>
                  <option v-for="tpl in kpTemplates" :key="tpl.id" :value="tpl.id">
                    {{ tpl.name }}
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label>Компания</label>
                <CompanySmartSelect
                v-model="kpBindingForm.our_company_id"
                :options="internalCompanies"
                placeholder="Найти нашу компанию"
              />
              </div>
              <button class="btn btn-primary" @click="createKpBinding" :disabled="kpBindingSaving">
                <i v-if="kpBindingSaving" class="fas fa-spinner fa-spin mr-1"></i>
                Привязать
              </button>
            </div>
          </div>

          <div class="mt-4">
            <h5>Список шаблонов</h5>
            <table class="table table-sm">
              <thead>
                <tr>
                  <th>Название</th>
                  <th>DOCX</th>
                  <th>PDF</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="tpl in kpTemplates" :key="tpl.id">
                  <td>{{ tpl.name }}</td>
                  <td>
                    <a v-if="tpl.docx_url" :href="tpl.docx_url" target="_blank" rel="noopener noreferrer">Скачать</a>
                    <span v-else class="text-muted">—</span>
                  </td>
                  <td>
                    <a v-if="tpl.pdf_url" :href="tpl.pdf_url" target="_blank" rel="noopener noreferrer">Скачать</a>
                    <span v-else class="text-muted">—</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="mt-3">
            <h5>Привязки</h5>
            <table class="table table-sm">
              <thead>
                <tr>
                  <th>Компания</th>
                  <th>Шаблон</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="binding in kpBindings" :key="binding.id">
                  <td>{{ getCompanyName(binding.our_company_id) }}</td>
                  <td>{{ getTemplateName(binding.template_id) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeKpTemplatesModal">Закрыть</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { api } from '@/services/api'
import PizZip from 'pizzip'
import Docxtemplater from 'docxtemplater'
import { useAuthStore } from '../stores/auth'
import { useUploadQueueStore } from '../stores/uploadQueue'
import { useCompaniesStore } from '../stores/companies'
import { useUsersStore } from '../stores/users'
import { useProductsStore } from '../stores/products'
import CompanySmartSelect from '../components/ui/CompanySmartSelect.vue'
import UiAvatar from '../components/ui/UiAvatar.vue'
import ProductSmartSelect from '../components/ui/ProductSmartSelect.vue'
import LeadFormModal from '../components/leads/LeadFormModal.vue'
import LeadTimeline from '../components/leads/LeadTimeline.vue'
import LeadKpWorkspace from '../components/leads/LeadKpWorkspace.vue'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'
import { getActiveUser } from '../utils/permissions'

const ldClickOutside = {
  beforeMount(el, binding) {
    el._co = (e) => { if (!(el === e.target || el.contains(e.target))) binding.value(e) }
    setTimeout(() => document.addEventListener('click', el._co), 0)
  },
  unmounted(el) { document.removeEventListener('click', el._co) }
}

export default {
  name: 'LeadDetail',
  components: { CompanySmartSelect, ProductSmartSelect, LeadFormModal, LeadTimeline, LeadKpWorkspace, UiAvatar },
  directives: { 'click-outside': ldClickOutside },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const toast = useToast()
    const { confirm } = useConfirm()
    const auth = useAuthStore()
    const uploadQueue = useUploadQueueStore()
    const companiesStore = useCompaniesStore()
    const usersStore = useUsersStore()
    const productsStore = useProductsStore()

    const lead = ref({})
    const companies = ref([])
    const users = ref([])
    const leadProducts = ref([])
    const vatRateOptions = [0, 10, 20, 22]
    const loadingLead = ref(false)
    const vatRate = ref(20)
    const vatSaving = ref(false)
    const productsLoading = ref(false)
    const saving = ref(false)
    const productSaving = ref(false)
    const leadTaxUpdating = ref(false)
    const selectedLeadProductIds = ref([])
    const bulkLeadTaxRate = ref(22)  // дефолт bulk-применения ставки НДС

    const showAddProductModal = ref(false)
    const showEditProductModal = ref(false)
    const showEditLeadModal = ref(false)
    const activeTab = ref(['composition', 'kp'].includes(String(route.query?.tab || '')) ? String(route.query.tab) : 'info')
    const ldStatusMenuOpen = ref(false)
    const ldStatusBusy = ref(false)
    const ldMoreOpen = ref(false)
    const setActiveTab = (t) => {
      activeTab.value = t
      const q = { ...(route.query || {}) }
      q.tab = t
      router.replace({ query: q }).catch(() => {})
    }
    const tabs = [
      { id: 'info',        name: 'Информация', icon: 'fas fa-info-circle' },
      { id: 'composition', name: 'Состав',     icon: 'fas fa-list-ul' },
      { id: 'kp',          name: 'КП',         icon: 'fas fa-file-invoice' },
    ]
    const onTabKeydown = (event) => {
      const ids = tabs.map(t => t.id)
      const idx = ids.indexOf(activeTab.value)
      let next = idx
      if (event.key === 'ArrowRight') next = (idx + 1) % ids.length
      else if (event.key === 'ArrowLeft') next = (idx - 1 + ids.length) % ids.length
      else if (event.key === 'Home') next = 0
      else if (event.key === 'End') next = ids.length - 1
      else return
      event.preventDefault()
      setActiveTab(ids[next])
      document.getElementById(`tab-${ids[next]}`)?.focus()
    }

    // ---- Inline-редактирование «Основной информации» ----
    // Одно поле в режиме редактирования за раз. Enter/blur — сохранить,
    // Esc — отменить. Селекты (компании/ответственный) пока не инлайн —
    // редактируются через «Редактировать» в шапке.
    const editingField = ref(null)
    const editDraft = ref(null)
    const inlineSaving = ref(false)
    const inlineInputRef = ref(null)
    const beginEdit = (field) => {
      if (inlineSaving.value) return
      if (editingField.value === field) return
      editingField.value = field
      const v = lead.value?.[field]
      editDraft.value = v ?? ''
      nextTick(() => {
        const el = inlineInputRef.value
        if (el && typeof el.focus === 'function') {
          el.focus()
          if (typeof el.select === 'function') el.select()
        }
      })
    }
    const cancelEdit = () => {
      editingField.value = null
      editDraft.value = null
    }
    const normInlineValue = (field, raw) => {
      if (raw === null || raw === undefined) return null
      if (field === 'object_area' || field === 'advance_percent') {
        if (raw === '') return null
        const n = Number(raw)
        return Number.isNaN(n) ? null : n
      }
      if (raw === '') return null
      const s = String(raw).trim()
      return s === '' ? null : s
    }
    const saveEdit = async () => {
      if (!editingField.value || inlineSaving.value) return
      const field = editingField.value
      const value = normInlineValue(field, editDraft.value)
      const current = normInlineValue(field, lead.value?.[field])
      if (value === current) { cancelEdit(); return }
      // Бэкенд лидов фильтрует null → бросает "No fields to update".
      // Очистка поля до пустого инлайн не поддерживается — тихо отменяем;
      // снять значение можно через «Редактировать» в шапке.
      if (value === null) { cancelEdit(); return }
      inlineSaving.value = true
      try {
        await api.leads.update(lead.value.id, { [field]: value })
        lead.value = { ...lead.value, [field]: value }
        cancelEdit()
      } catch (e) {
        const detail = e?.response?.data?.detail || ''
        if (typeof detail === 'string' && /no fields|нет полей/i.test(detail)) {
          // подстраховка от той же серверной ошибки.
          cancelEdit()
          return
        }
        toast.error(detail || 'Не удалось сохранить')
      } finally {
        inlineSaving.value = false
      }
    }
    const currentUserId = computed(() => {
      try {
        const u = getActiveUser()
        return u?.id || ''
      } catch (e) { return '' }
    })

    const selectedProductId = ref('')
    const selectedProduct = ref(null)
    const editingLeadProduct = ref(null)

    const leadForm = ref({
      title: '',
      obj_name: '',
      address: '',
      object_type: '',
      object_area: null,
      customer_id: '',
      our_company_id: '',
      responsible_user_id: '',
      advance_percent: 0,
      vat_rate: 20,
      status: 'incoming'
    })

    const objectTypeOptions = [
      'Линейные - метрополитен',
      'Линейные - дороги, эстакады',
      'Линейные - инженерные сети',
      'Образовательные учреждения',
      'Объекты здравоохранения',
      'Спортивные сооружения',
      'Административные здания',
      'Жилые комплексы',
      'Торговые центры',
      'Паркинги',
      'Аэропорты',
      'Промышленные объекты',
      'Складские/архивные здания'
    ]

    const leadProductForm = ref({
      custom_name: '',
      custom_price: null,
      quantity: 1,
      unit: 'шт.',
      discount_percent: 0,
      tax_rate: 22  // дефолтная ставка НДС для новых товаров (была 20)
    })

    const statusOptions = [
      { key: 'incoming', label: 'Входящие' },
      { key: 'no_work', label: 'Лиды не в обработке' },
      { key: 'proposal', label: 'Подготовка КП' },
      { key: 'waiting', label: 'Ожидание заказчика' },
      { key: 'customer_reject_internal', label: 'Отказался заказчик (внутренние причины)' },
      { key: 'customer_reject_our', label: 'Отказался заказчик (наши недочёты)' },
      { key: 'we_reject', label: 'Отказались мы' },
      { key: 'converted', label: 'Конверсия' }
    ]

    const normalizeId = (value) => {
      if (!value) return ''
      return String(value).replace(/-/g, '').toLowerCase()
    }

    const getCompanyIdForSelect = (value) => {
      if (!value) return ''
      const target = normalizeId(value)
      const match = companies.value.find(c => normalizeId(c.id) === target)
      return match ? match.id : ''
    }

    const getUserIdForSelect = (value) => {
      if (!value) return ''
      const target = normalizeId(value)
      const match = users.value.find(u => normalizeId(u.id) === target)
      return match ? match.id : ''
    }

    const companyMap = computed(() => {
      const map = {}
      companies.value.forEach(c => {
        map[normalizeId(c.id)] = c.name
      })
      return map
    })

    const userMap = computed(() => {
      const map = {}
      users.value.forEach(u => {
        map[normalizeId(u.id)] = u.full_name || u.email || u.id
      })
      return map
    })

    const productMap = computed(() => {
      const map = {}
      availableProducts.value.forEach(p => {
        map[normalizeId(p.id)] = p.name
      })
      return map
    })

    const productCategoryMap = ref({})
    const normalizeCategoryId = (value) => (value ? String(value).replace(/-/g, '').toLowerCase() : '')
    const loadProductCategories = async () => {
      try {
        const map = {}
        const limit = 200
        let skip = 0
        while (true) {
          const res = await axios.get('/api/v1/products/categories/', { params: { skip, limit } })
          const chunk = res.data || []
          chunk.forEach(category => {
            const key = normalizeCategoryId(category.id)
            if (key) {
              map[key] = category.name
            }
          })
          if (chunk.length < limit) break
          skip += limit
        }
        productCategoryMap.value = map
      } catch (error) {
        console.error('Error loading product categories:', error)
      }
    }

    const internalCompanies = computed(() => companies.value.filter(c => c.type === 'internal'))
    const customerCompanies = computed(() => companies.value.filter(c => c.type === 'customer'))
    const OBJECT_TYPES = [
      'Линейные - метрополитен',
      'Линейные - дороги, эстакады',
      'Линейные - инженерные сети',
      'Образовательные учреждения',
      'Объекты здравоохранения',
      'Спортивные сооружения',
      'Административные здания',
      'Жилые комплексы',
      'Торговые центры',
      'Паркинги',
      'Аэропорты',
      'Промышленные объекты',
      'Складские/архивные здания',
    ]

    const getCompanyName = (id) => companyMap.value[normalizeId(id)] || '-'
    const getUserName = (id) => userMap.value[normalizeId(id)] || '-'
    const responsibleUser = computed(() => {
      const id = lead.value?.responsible_user_id
      if (!id) return null
      const nid = normalizeId(id)
      return users.value.find(u => normalizeId(u.id) === nid) || null
    })
    const getProductName = (id) => productMap.value[normalizeId(id)] || ''

    const normalizeTaxRate = (value) => {
      const numeric = Number(value ?? 0)
      return Number.isFinite(numeric) ? numeric : 0
    }

    const leadVatSummary = computed(() => {
      const summary = new Map()
      leadProducts.value.forEach((item) => {
        const rate = normalizeTaxRate(item.tax_rate)
        const taxAmount = Number(item.tax_amount || 0)
        const finalAmount = Number(item.final_price || 0)
        const baseAmount = finalAmount - taxAmount
        const current = summary.get(rate) || { rate, baseAmount: 0, taxAmount: 0, totalAmount: 0 }
        current.baseAmount += baseAmount
        current.taxAmount += taxAmount
        current.totalAmount += finalAmount
        summary.set(rate, current)
      })
      return Array.from(summary.values()).sort((a, b) => a.rate - b.rate)
    })

    const leadVatRows = computed(() => leadVatSummary.value.filter((row) => row.rate > 0 && Math.abs(row.taxAmount) > 0.0001))
    const totalVatAmount = computed(() => leadVatSummary.value.reduce((sum, row) => sum + row.taxAmount, 0))
    const totalWithoutVat = computed(() => leadVatSummary.value.reduce((sum, row) => sum + row.baseAmount, 0))
    const totalAmount = computed(() => leadVatSummary.value.reduce((sum, row) => sum + row.totalAmount, 0))
    const allLeadProductsSelected = computed(() => {
      const ids = leadProducts.value.map((item) => item.id)
      return ids.length > 0 && ids.every((id) => selectedLeadProductIds.value.includes(id))
    })

    const vatRateDirty = computed(() => {
      return Number(vatRate.value || 0) !== Number(lead.value.vat_rate || 0)
    })

    const canManageKpTemplates = computed(() => auth.isSuperuser)

    const kpDocuments = ref([])
    const kpTemplates = ref([])
    const kpBindings = ref([])
    const loadingKp = ref(false)
    const kpSaving = ref(false)
    const kpTemplateSaving = ref(false)
    const kpBindingSaving = ref(false)
    const kpActionId = ref(null)

    const showKpCreateModal = ref(false)
    const showKpTemplatesModal = ref(false)

    const kpForm = ref({
      our_company_id: '',
      template_id: '',
      vat_rate: 20
    })

    const kpTemplateForm = ref({
      name: '',
      docxFile: null,
      pdfFile: null
    })

    const kpBindingForm = ref({
      template_id: '',
      our_company_id: ''
    })

    const templateOptions = computed(() => {
      const companyId = kpForm.value.our_company_id
      if (!companyId) return kpTemplates.value
      const boundIds = new Set(
        kpBindings.value
          .filter(b => normalizeId(b.our_company_id) === normalizeId(companyId))
          .map(b => normalizeId(b.template_id))
      )
      if (!boundIds.size) return kpTemplates.value
      return kpTemplates.value.filter(t => boundIds.has(normalizeId(t.id)))
    })

    const getTemplateName = (templateId) => {
      const tpl = kpTemplates.value.find(t => normalizeId(t.id) === normalizeId(templateId))
      return tpl ? tpl.name : '-'
    }

    const resolveTemplateForKp = (kp) => {
      if (kp?.template_id) {
        return kpTemplates.value.find(t => normalizeId(t.id) === normalizeId(kp.template_id)) || null
      }
      if (kp?.our_company_id) {
        const binding = kpBindings.value.find(b => normalizeId(b.our_company_id) === normalizeId(kp.our_company_id))
        if (binding) {
          return kpTemplates.value.find(t => normalizeId(t.id) === normalizeId(binding.template_id)) || null
        }
      }
      return kpTemplates.value[0] || null
    }

    const getKpTemplateDocx = (kp) => {
      const tpl = resolveTemplateForKp(kp)
      return tpl?.docx_url || ''
    }

    const loadLead = async () => {
      loadingLead.value = true
      try {
        const data = await api.leads.getById(route.params.id)
        lead.value = data || {}
        vatRate.value = Number(data?.vat_rate ?? 20)
        bulkLeadTaxRate.value = Number(data?.vat_rate ?? 20)
      } catch (error) {
        console.error('Error loading lead:', error)
        lead.value = {}
      } finally {
        loadingLead.value = false
      }
    }

    const loadLeadProducts = async () => {
      productsLoading.value = true
      try {
        const res = await axios.get(`/api/v1/products/lead/${route.params.id}`)
        leadProducts.value = res.data || []
      } catch (error) {
        console.error('Error loading lead products:', error)
        leadProducts.value = []
      } finally {
        productsLoading.value = false
      }
    }

    const loadAvailableProducts = async () => {
      try {
        if (!Object.keys(productCategoryMap.value).length) {
          await loadProductCategories()
        }
        await productsStore.ensureLoaded()
      } catch (error) {
        console.error('Error loading products:', error)
      }
    }

    const availableProducts = computed(() => {
      const categoryMap = productCategoryMap.value
      return (productsStore.items || []).map(item => {
        const categoryKey = normalizeCategoryId(item.category_id)
        return {
          ...item,
          category_name: categoryMap[categoryKey] || item.category_name || item.category?.name || null
        }
      })
    })

    const loadCompanies = async () => {
      try {
        await companiesStore.ensureLoaded()
        companies.value = companiesStore.items
      } catch (error) {
        console.error('Error loading companies:', error)
      }
    }

    const loadUsers = async () => {
      try {
        await usersStore.ensureLoaded()
        users.value = usersStore.items
      } catch (error) {
        console.error('Error loading users:', error)
      }
    }

    const loadKpDocuments = async () => {
      loadingKp.value = true
      try {
        const res = await axios.get('/api/v1/kp/', { params: { lead_id: route.params.id } })
        kpDocuments.value = res.data || []
      } catch (error) {
        console.error('Error loading KP documents:', error)
        kpDocuments.value = []
      } finally {
        loadingKp.value = false
      }
    }

    const loadKpTemplates = async () => {
      try {
        const res = await axios.get('/api/v1/kp/templates')
        kpTemplates.value = res.data || []
      } catch (error) {
        console.error('Error loading KP templates:', error)
        kpTemplates.value = []
      }
    }

    const loadKpBindings = async () => {
      try {
        const res = await axios.get('/api/v1/kp/template-bindings')
        kpBindings.value = res.data || []
      } catch (error) {
        console.error('Error loading KP bindings:', error)
        kpBindings.value = []
      }
    }
    const openEditModal = () => {
      showEditLeadModal.value = true
    }

    const closeEditLeadModal = () => {
      showEditLeadModal.value = false
    }

    const onLeadFormSubmit = async ({ payload }) => {
      saving.value = true
      try {
        const { id, created_at, updated_at, ...basePayload } = payload
        await api.leads.update(route.params.id, basePayload)
        await loadLead()
        showEditLeadModal.value = false
        toast.success('Лид сохранён')
      } catch (error) {
        console.error('Error saving lead:', error)
        toast.error(error?.response?.data?.detail || 'Не удалось сохранить лид')
      } finally {
        saving.value = false
      }
    }

    const convertLead = async () => {
      if (lead.value.status === 'converted') return
      const ok = await confirm({
        title: 'Конвертировать в сделку?',
        message: `На основе лида «${lead.value.title || ''}» будет создана сделка с теми же данными и продуктами. Это действие необратимо.`,
        confirmText: 'Конвертировать',
        variant: 'primary',
      })
      if (!ok) return
      saving.value = true
      try {
        const data = await api.leads.convert(route.params.id)
        await loadLead()
        toast.success('Сделка создана')
        if (data?.deal_id) router.push(`/deals?deal_id=${data.deal_id}`)
      } catch (error) {
        console.error('Error converting lead:', error)
        toast.error(error?.response?.data?.detail || 'Не удалось конвертировать лид')
      } finally {
        saving.value = false
      }
    }

    const onChangeStatus = async (newStatus) => {
      ldStatusMenuOpen.value = false
      if (!lead.value || newStatus === lead.value.status) return
      if (newStatus === 'converted') { await convertLead(); return }
      const prev = lead.value.status
      lead.value = { ...lead.value, status: newStatus }
      ldStatusBusy.value = true
      try {
        await api.leads.update(route.params.id, { status: newStatus })
        toast.success(`Статус: ${getStatusText(newStatus)}`)
      } catch (e) {
        lead.value = { ...lead.value, status: prev }
        toast.error(e?.response?.data?.detail || 'Не удалось изменить статус')
      } finally {
        ldStatusBusy.value = false
      }
    }

    const deleteLead = async () => {
      const ok = await confirm({
        title: 'Удалить лид?',
        message: `«${lead.value.title || ''}» будет удалён безвозвратно.`,
        confirmText: 'Удалить',
        variant: 'danger',
      })
      if (!ok) return
      try {
        await api.leads.remove(route.params.id)
        toast.success('Лид удалён')
        router.push('/leads')
      } catch (error) {
        console.error('Error deleting lead:', error)
        toast.error(error?.response?.data?.detail || 'Не удалось удалить лид')
      }
    }

    const selectProduct = () => {
      selectedProduct.value = availableProducts.value.find(p => p.id === selectedProductId.value) || null
      if (selectedProduct.value) {
        leadProductForm.value = {
          custom_name: '',
          custom_price: null,
          quantity: 1,
          unit: selectedProduct.value.unit || 'шт.',
          discount_percent: 0,
          // НДС товара по умолчанию 22%. lead.vat_rate больше не используем
          // как референс — лидовая ставка убрана из UI, каждый товар несёт свою.
          tax_rate: 22
        }
      }
    }

    const toggleAllLeadProducts = () => {
      if (allLeadProductsSelected.value) {
        selectedLeadProductIds.value = []
        return
      }
      selectedLeadProductIds.value = leadProducts.value.map((item) => item.id)
    }

    const saveVatRate = async () => {
      if (vatSaving.value || !vatRateDirty.value) return
      vatSaving.value = true
      try {
        await api.leads.update(route.params.id, { vat_rate: Number(vatRate.value) })
        await loadLead()
      } catch (error) {
        console.error('Error saving VAT rate:', error)
        toast.error('Не удалось сохранить ставку НДС')
      } finally {
        vatSaving.value = false
      }
    }

    const closeAddModal = () => {
      showAddProductModal.value = false
      selectedProductId.value = ''
      selectedProduct.value = null
      leadProductForm.value = {
        custom_name: '',
        custom_price: null,
        quantity: 1,
        unit: 'шт.',
        discount_percent: 0,
        tax_rate: Number(lead.value.vat_rate ?? 20)
      }
    }

    const closeEditModal = () => {
      showEditProductModal.value = false
      editingLeadProduct.value = null
    }

    const addProductToLead = async () => {
      if (!selectedProduct.value) return
      productSaving.value = true
      try {
        const payload = {
          lead_id: route.params.id,
          product_id: selectedProduct.value.id,
          custom_name: leadProductForm.value.custom_name || selectedProduct.value.name,
          custom_price: leadProductForm.value.custom_price || null,
          quantity: leadProductForm.value.quantity,
          unit: leadProductForm.value.unit || selectedProduct.value.unit || 'шт.',
          unit_price: leadProductForm.value.custom_price || selectedProduct.value.base_price || 0,
          discount_percent: leadProductForm.value.discount_percent || 0,
          discount_amount: 0,
          tax_rate: normalizeTaxRate(leadProductForm.value.tax_rate)
        }
        await axios.post('/api/v1/products/lead/', payload)
        await Promise.all([loadLead(), loadLeadProducts()])
        closeAddModal()
      } catch (error) {
        console.error('Error adding product:', error)
        toast.error('Не удалось добавить товар')
      } finally {
        productSaving.value = false
      }
    }

    const editLeadProduct = (item) => {
      editingLeadProduct.value = item
      leadProductForm.value = {
        custom_name: item.custom_name || '',
        custom_price: item.custom_price ?? item.unit_price ?? null,
        quantity: item.quantity ?? 1,
        unit: item.unit || 'шт.',
        discount_percent: item.discount_percent ?? 0,
        tax_rate: normalizeTaxRate(item.tax_rate)
      }
      showEditProductModal.value = true
    }

    const updateLeadProduct = async () => {
      if (!editingLeadProduct.value) return
      productSaving.value = true
      try {
        const payload = {
          custom_name: leadProductForm.value.custom_name || null,
          custom_price: leadProductForm.value.custom_price ?? null,
          quantity: leadProductForm.value.quantity,
          unit: leadProductForm.value.unit || 'шт.',
          discount_percent: leadProductForm.value.discount_percent || 0,
          discount_amount: 0,
          tax_rate: normalizeTaxRate(leadProductForm.value.tax_rate)
        }
        await axios.put(`/api/v1/products/lead/${editingLeadProduct.value.id}`, payload)
        await Promise.all([loadLead(), loadLeadProducts()])
        closeEditModal()
      } catch (error) {
        console.error('Error updating lead product:', error)
        toast.error('Не удалось обновить товар')
      } finally {
        productSaving.value = false
      }
    }

    const removeLeadProduct = async (item) => {
      const _ok = await confirm({ title: 'Удалить товар?', confirmText: 'Удалить', variant: 'danger' })
      if (!_ok) return
      try {
        await axios.delete(`/api/v1/products/lead/${item.id}`)
        await Promise.all([loadLead(), loadLeadProducts()])
      } catch (error) {
        console.error('Error deleting lead product:', error)
        toast.error('Не удалось удалить товар')
      }
    }

    const updateLeadProductTaxRate = async (item, nextRate) => {
      if (!item?.id || leadTaxUpdating.value) return
      leadTaxUpdating.value = true
      try {
        await axios.put(`/api/v1/products/lead/${item.id}`, { tax_rate: normalizeTaxRate(nextRate) })
        await Promise.all([loadLead(), loadLeadProducts()])
      } catch (error) {
        console.error('Error updating lead VAT rate:', error)
        toast.error('Не удалось изменить НДС товара')
      } finally {
        leadTaxUpdating.value = false
      }
    }

    const applyBulkLeadTaxRate = async () => {
      if (!selectedLeadProductIds.value.length || leadTaxUpdating.value) return
      leadTaxUpdating.value = true
      try {
        const rate = normalizeTaxRate(bulkLeadTaxRate.value)
        for (const id of selectedLeadProductIds.value) {
          await axios.put(`/api/v1/products/lead/${id}`, { tax_rate: rate })
        }
        await Promise.all([loadLead(), loadLeadProducts()])
        selectedLeadProductIds.value = []
      } catch (error) {
        console.error('Error bulk updating lead VAT rate:', error)
        toast.error('Не удалось массово изменить НДС')
      } finally {
        leadTaxUpdating.value = false
      }
    }

    const openKpCreateModal = () => {
      // our_company_id is no longer selected in UI — backend resolves it
      // from the parent lead → system default.
      kpForm.value = {
        template_id: '',
        vat_rate: lead.value.vat_rate ?? 20
      }
      showKpCreateModal.value = true
    }

    const closeKpCreateModal = () => {
      showKpCreateModal.value = false
    }

    const createKp = async () => {
      kpSaving.value = true
      try {
        const payload = {
          lead_id: route.params.id,
          template_id: kpForm.value.template_id || null,
          vat_rate: kpForm.value.vat_rate ?? 20
        }
        await axios.post('/api/v1/kp/', payload)
        void loadKpDocuments()
        showKpCreateModal.value = false
      } catch (error) {
        console.error('Error creating KP:', error)
        toast.error('Не удалось создать КП')
      } finally {
        kpSaving.value = false
      }
    }

    const uploadKpVersion = async (event, doc) => {
      const file = event.target.files?.[0]
      if (!file || !doc?.id) return
      kpActionId.value = doc.id
      const localId = uploadQueue.addLocalUpload({
        fileName: file.name,
        module: 'kp',
        entityId: doc.id
      })
      try {
        const formData = new FormData()
        formData.append('kp_id', doc.id)
        formData.append('file', file)
        const response = await axios.post('/api/v1/uploads/kp/versions', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (eventProgress) => {
            if (!eventProgress.total) return
            const progress = (eventProgress.loaded / eventProgress.total) * 100
            uploadQueue.updateProgress(localId, progress)
          }
        })
        uploadQueue.markQueued(localId, response.data)
        void loadKpDocuments()
      } catch (e) {
        uploadQueue.markError(localId, e?.response?.data?.detail)
        toast.error('Не удалось сформировать КП')
      } finally {
        kpActionId.value = null
        event.target.value = ''
      }
    }

    const buildKpTemplateData = (kp) => {
      const latestVersion = (kp.versions || [])[0] || {}
      // Эффективная ставка НДС: предпочтительно из последней версии КП
      // (там она была зафиксирована), иначе средняя по товарам, иначе 22.
      const vatFromProducts = (() => {
        const rates = leadProducts.value.map(p => Number(p.tax_rate || 0)).filter(r => r > 0)
        if (!rates.length) return null
        return Math.round(rates.reduce((a, b) => a + b, 0) / rates.length)
      })()
      const vatRate = lead.value.vat_rate ?? vatFromProducts ?? 22

      // Дата КП в формате «25» мая 2026 г.
      const MONTHS = ['января','февраля','марта','апреля','мая','июня',
                      'июля','августа','сентября','октября','ноября','декабря']
      const formatKpDate = (raw) => {
        const d = raw ? new Date(raw) : new Date()
        if (Number.isNaN(d.getTime())) return ''
        const dd = String(d.getDate()).padStart(2, '0')
        return `«${dd}» ${MONTHS[d.getMonth()]} ${d.getFullYear()} г.`
      }

      // Денежное форматирование: «6 996 540,00» (с пробелом-разделителем
      // тысяч и запятой как разделителем дробной части).
      const fmtMoney = (n) => {
        const v = Number(n || 0)
        return v.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      }

      // Сумма и НДС: используем актуальные computed на странице, не
      // снапшот из последней версии — пользователь успел поменять состав
      // и ждёт свежие цифры.
      const totalNumber = Number(totalAmount.value || 0)
      const vatNumber = Number(totalVatAmount.value || 0)

      // {products_table}: docxtemplater не умеет вставить настоящую docx
      // таблицу из строки — для этого нужен серверный python-docx или
      // платный HTML-модуль. Пока подставляем текстовый список (одна
      // строка на товар) — он встанет вместо плейсхолдера и форматирование
      // будет линейное. Настоящая таблица — отдельной задачей через
      // серверный рендер.
      const productsLines = leadProducts.value.map((item, idx) => {
        const name = item.custom_name || getProductName(item.product_id) || '—'
        const qty = item.quantity || 0
        const unit = item.unit || ''
        const total = fmtMoney(item.final_price || 0)
        return `${idx + 1}. ${name} — ${qty} ${unit} = ${total} ₽`
      })
      const productsTable = productsLines.length ? productsLines.join('\n') : '—'

      // ФИО директора нашей компании: пока берём contact_person из
      // companies[our_company_id]. Если пусто — пустая строка.
      const ourCompany = companies.value.find(
        c => normalizeId(c.id) === normalizeId(lead.value.our_company_id)
      )
      const directorName = ourCompany?.contact_person || ''
      const ourCompanyShort = ourCompany?.short_name || ourCompany?.name || ''

      // ВСЕ ключи именованы под плейсхолдеры шаблона КП.
      // НЕ переименовывать без согласования с docx-шаблонами на проде —
      // иначе в выводе появятся `undefined` (как раз эту проблему чиним).
      return {
        // — реквизиты КП —
        kp_number: kp.number_display || '',
        kp_date: formatKpDate(kp.created_at),
        kp_validity_days: 30,
        // — получатель —
        recipient_short_name: getCompanyName(lead.value.customer_id) || '',
        recipient_eio: '',
        recipient_to_name: '',
        // — объект —
        object_name: lead.value.obj_name || '',
        object_address: lead.value.address || '',
        // — финансы —
        total_amount: fmtMoney(totalNumber),
        total_amount_text: latestVersion.total_text || '',
        vat_rate: Math.round(Number(vatRate) || 0),
        vat_amount: fmtMoney(vatNumber),
        vat_amount_text: latestVersion.vat_text || '',
        advance_percent: lead.value.advance_percent ?? 0,
        // — наша компания —
        our_company_short_name: ourCompanyShort,
        our_company_director_position: 'Генеральный директор',
        our_company_director_name: directorName,
        // — состав (текстовая версия, пока не сделан серверный рендер) —
        products_table: productsTable,

        // — legacy-ключи, оставлены чтобы не сломать старые шаблоны —
        number: kp.number_display,
        number_display: kp.number_display,
        date: formatDate(kp.created_at),
        lead_title: lead.value.title || '',
        obj_name: lead.value.obj_name || '',
        address: lead.value.address || '',
        object_type: lead.value.object_type || '',
        object_area: lead.value.object_area || '',
        customer_name: getCompanyName(lead.value.customer_id) || '',
        our_company_name: ourCompanyShort,
        total_text: latestVersion.total_text || '',
        vat_text: latestVersion.vat_text || '',
        items: leadProducts.value.map((item, idx) => ({
          index: idx + 1,
          name: item.custom_name || getProductName(item.product_id) || '',
          quantity: item.quantity || 0,
          unit: item.unit || '',
          unit_price: item.unit_price || 0,
          total: item.final_price || 0
        }))
      }
    }

    const generateKpDocxBlob = async (templateUrl, data) => {
      // KpTemplate.docx_url исторически называется *_url, но содержит
      // storage-path вида "KP/templates/.../600.docx". Прямой axios.get
      // на такой путь даёт 404. Поэтому всегда тащим через единый
      // download-эндпоинт `/api/v1/storage/download?path=...` — он
      // авторизует, локализует путь и отдаёт arraybuffer. Для редкого
      // случая, когда в БД лежит полный URL (миграция со старого
      // публичного хранилища), используем его как есть.
      const isHttpUrl = /^https?:\/\//i.test(templateUrl)
      const resolved = isHttpUrl
        ? templateUrl
        : `/api/v1/storage/download?path=${encodeURIComponent(templateUrl)}`
      const response = await axios.get(resolved, { responseType: 'arraybuffer' })
      const zip = new PizZip(response.data)
      const doc = new Docxtemplater(zip, {
        paragraphLoop: true,
        linebreaks: true
      })
      doc.render(data)
      return doc.getZip().generate({
        type: 'blob',
        mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      })
    }

    const generateKpVersion = async (kp) => {
      // Серверный рендер: бэк сам читает шаблон, подставляет плейсхолдеры
      // и собирает настоящую docx-таблицу товаров. Фронт лишь скачивает
      // готовый blob и заливает его как новую версию КП.
      kpActionId.value = kp.id
      const fileName = `${kp.number_display || 'KP'}.docx`
      const localId = uploadQueue.addLocalUpload({
        fileName,
        module: 'kp',
        entityId: kp.id
      })
      try {
        const renderResponse = await axios.get(`/api/v1/kp/${kp.id}/render-docx`, {
          responseType: 'blob'
        })
        const blob = renderResponse.data
        const formData = new FormData()
        formData.append('kp_id', kp.id)
        formData.append('file', blob, fileName)
        const response = await axios.post('/api/v1/uploads/kp/versions', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (eventProgress) => {
            if (!eventProgress.total) return
            const progress = (eventProgress.loaded / eventProgress.total) * 100
            uploadQueue.updateProgress(localId, progress)
          }
        })
        uploadQueue.markQueued(localId, response.data)
        void loadKpDocuments()
      } catch (e) {
        uploadQueue.markError(localId, e?.response?.data?.detail)
        toast.error('Не удалось обновить КП')
      } finally {
        kpActionId.value = null
      }
    }

    const openKpTemplatesModal = async () => {
      await Promise.all([loadKpTemplates(), loadKpBindings()])
      showKpTemplatesModal.value = true
    }

    const closeKpTemplatesModal = () => {
      showKpTemplatesModal.value = false
    }

    const onTemplateDocxChange = (event) => {
      kpTemplateForm.value.docxFile = event.target.files?.[0] || null
    }

    const onTemplatePdfChange = (event) => {
      kpTemplateForm.value.pdfFile = event.target.files?.[0] || null
    }

    const uploadKpTemplate = async () => {
      if (!kpTemplateForm.value.name || !kpTemplateForm.value.docxFile) {
        toast.warning('Укажите название и DOCX файл')
        return
      }
      kpTemplateSaving.value = true
      try {
        const formData = new FormData()
        formData.append('name', kpTemplateForm.value.name)
        formData.append('docx', kpTemplateForm.value.docxFile)
        if (kpTemplateForm.value.pdfFile) {
          formData.append('pdf', kpTemplateForm.value.pdfFile)
        }
        await axios.post('/api/v1/kp/templates', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        kpTemplateForm.value = { name: '', docxFile: null, pdfFile: null }
        await loadKpTemplates()
      } catch (error) {
        console.error('Error uploading template:', error)
        toast.error('Не удалось загрузить шаблон')
      } finally {
        kpTemplateSaving.value = false
      }
    }

    const createKpBinding = async () => {
      if (!kpBindingForm.value.template_id || !kpBindingForm.value.our_company_id) {
        toast.warning('Выберите шаблон и компанию')
        return
      }
      kpBindingSaving.value = true
      try {
        await axios.post('/api/v1/kp/template-bindings', {
          template_id: kpBindingForm.value.template_id,
          our_company_id: kpBindingForm.value.our_company_id
        })
        kpBindingForm.value = { template_id: '', our_company_id: '' }
        await loadKpBindings()
      } catch (error) {
        console.error('Error binding template:', error)
        toast.error('Не удалось сохранить привязку')
      } finally {
        kpBindingSaving.value = false
      }
    }

    const formatCurrency = (value) => {
      return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', minimumFractionDigits: 0 }).format(value || 0)
    }

    const formatDate = (value) => {
      if (!value) return '-'
      return new Date(value).toLocaleDateString('ru-RU')
    }

    const getStatusText = (status) => {
      const map = {
        incoming: 'Входящие',
        no_work: 'Лиды не в обработке',
        proposal: 'Подготовка КП',
        waiting: 'Ожидание заказчика',
        customer_reject_internal: 'Отказался заказчик (внутренние причины)',
        customer_reject_our: 'Отказался заказчик (наши недочёты)',
        we_reject: 'Отказались мы',
        converted: 'Конверсия'
      }
      return map[status] || status || '-'
    }

    const getStatusClass = (status) => {
      const map = {
        incoming: 'badge-info',
        no_work: 'badge-secondary',
        proposal: 'badge-warning',
        waiting: 'badge-warning',
        customer_reject_internal: 'badge-danger',
        customer_reject_our: 'badge-danger',
        we_reject: 'badge-secondary',
        converted: 'badge-success'
      }
      return map[status] || 'badge-secondary'
    }

    onMounted(async () => {
      await Promise.all([
        loadLead(),
        loadLeadProducts(),
        loadCompanies(),
        loadUsers(),
        loadAvailableProducts(),
        loadKpDocuments(),
        loadKpTemplates(),
        loadKpBindings()
      ])
    })

    watch(selectedProductId, () => {
      if (!selectedProductId.value) {
        selectedProduct.value = null
        return
      }
      selectProduct()
    })

    watch(leadProducts, (items) => {
      const validIds = new Set((items || []).map((item) => item.id))
      selectedLeadProductIds.value = selectedLeadProductIds.value.filter((id) => validIds.has(id))
    }, { deep: true })

    watch(() => route.params.id, async () => {
      await Promise.all([loadLead(), loadLeadProducts(), loadKpDocuments()])
    })

    return {
      route, // exposed for template use (route.params.id in timeline tab)
      activeTab, setActiveTab, tabs, onTabKeydown,
      editingField, editDraft, inlineSaving, inlineInputRef,
      beginEdit, cancelEdit, saveEdit,
      loadLead,
      ldStatusMenuOpen, ldStatusBusy, ldMoreOpen,
      onChangeStatus,
      onLeadFormSubmit,
      currentUserId,
      lead,
      companies,
      users,
      leadProducts,
      availableProducts,
      loadingLead,
      productsLoading,
      saving,
      productSaving,
      vatRate,
      vatRateOptions,
      normalizeTaxRate,
      vatRateDirty,
      vatSaving,
      leadTaxUpdating,
      selectedLeadProductIds,
      bulkLeadTaxRate,
      leadVatRows,
      totalVatAmount,
      totalWithoutVat,
      allLeadProductsSelected,
      showAddProductModal,
      showEditProductModal,
      showEditLeadModal,
      selectedProductId,
      selectedProduct,
      editingLeadProduct,
      leadForm,
      leadProductForm,
      statusOptions,
      totalAmount,
      objectTypeOptions,
      internalCompanies,
      customerCompanies,
      objectTypes: OBJECT_TYPES,
      getCompanyName,
      getUserName,
      responsibleUser,
      getProductName,
      formatCurrency,
      formatDate,
      getStatusText,
      getStatusClass,
      openEditModal,
      closeEditLeadModal,
      saveVatRate,
      toggleAllLeadProducts,
      updateLeadProductTaxRate,
      applyBulkLeadTaxRate,
      convertLead,
      deleteLead,
      selectProduct,
      closeAddModal,
      closeEditModal,
      addProductToLead,
      editLeadProduct,
      updateLeadProduct,
      removeLeadProduct,
      kpDocuments,
      kpTemplates,
      kpBindings,
      loadingKp,
      showKpCreateModal,
      showKpTemplatesModal,
      kpForm,
      kpTemplateForm,
      kpBindingForm,
      kpSaving,
      kpTemplateSaving,
      kpBindingSaving,
      kpActionId,
      templateOptions,
      canManageKpTemplates,
      openKpCreateModal,
      closeKpCreateModal,
      createKp,
      uploadKpVersion,
      generateKpVersion,
      openKpTemplatesModal,
      closeKpTemplatesModal,
      loadKpDocuments,
      onTemplateDocxChange,
      onTemplatePdfChange,
      uploadKpTemplate,
      createKpBinding,
      getTemplateName,
      getKpTemplateDocx
    }
  }
}
</script>
<style scoped>
/* ============================================================
   Compact hero card
   ============================================================ */
.lead-hero-card { padding: 10px 14px !important; overflow: visible !important; }
.lead-breadcrumb {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.78rem;
  color: var(--md-sys-color-on-surface-variant);
  margin-bottom: 6px;
}
.lead-breadcrumb__link {
  color: var(--md-sys-color-primary, #1976d2);
  text-decoration: none;
}
.lead-breadcrumb__link:hover { text-decoration: underline; }
.lead-breadcrumb__sep { color: var(--md-sys-color-outline); }
.lead-breadcrumb__current { font-weight: 600; }

.lead-hero-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.lead-hero-title-block { display: flex; flex-direction: column; min-width: 0; }
.lead-hero-title {
  font-size: 1.1rem;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
.lead-hero-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }

/* Inline status badge */
.ld-status-wrap { position: relative; display: inline-block; }
.ld-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
  border: 1px solid currentColor;
  cursor: pointer;
  background: transparent;
}
.ld-status-badge:hover:not(:disabled) { filter: brightness(0.95); }
.ld-status-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: currentColor; opacity: 0.85; flex-shrink: 0;
}
.ld-status-incoming                 { background: rgba(25,118,210,0.12);  color: #1976d2; }
.ld-status-no_work                  { background: rgba(96,125,139,0.12);  color: #607d8b; }
.ld-status-proposal                 { background: rgba(245,158,11,0.15);  color: #b45309; }
.ld-status-waiting                  { background: rgba(217,119,6,0.15);   color: #92400e; }
.ld-status-customer_reject_internal { background: rgba(239,68,68,0.15);   color: #b91c1c; }
.ld-status-customer_reject_our      { background: rgba(185,28,28,0.15);   color: #991b1b; }
.ld-status-we_reject                { background: rgba(107,114,128,0.15); color: #6b7280; }
.ld-status-converted                { background: rgba(34,197,94,0.15);   color: #166534; }
.ld-status-badge .fa-caret-down { font-size: 0.6rem; opacity: 0.7; }
.ld-status-menu {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  z-index: 200;
  min-width: 240px;
  background: var(--md-sys-color-surface, #fff);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 10px;
  padding: 4px;
  box-shadow: 0 14px 36px rgba(0,0,0,0.14);
}
.ld-status-menu__item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 7px 10px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 6px;
  font-size: 0.85rem;
  text-align: left;
  color: var(--md-sys-color-on-surface);
}
.ld-status-menu__item:hover { background: var(--md-sys-color-surface-variant, rgba(0,0,0,0.05)); }
.ld-status-menu__item.active { font-weight: 700; }
.ld-status-menu__item.ld-status-incoming                 { color: #1976d2; }
.ld-status-menu__item.ld-status-no_work                  { color: #607d8b; }
.ld-status-menu__item.ld-status-proposal                 { color: #b45309; }
.ld-status-menu__item.ld-status-waiting                  { color: #92400e; }
.ld-status-menu__item.ld-status-customer_reject_internal { color: #b91c1c; }
.ld-status-menu__item.ld-status-customer_reject_our      { color: #991b1b; }
.ld-status-menu__item.ld-status-we_reject                { color: #6b7280; }

.ld-more-wrap { position: relative; }
.ld-more-menu {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  z-index: 200;
  min-width: 200px;
  background: var(--md-sys-color-surface, #fff);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 10px;
  padding: 4px;
  box-shadow: 0 14px 36px rgba(0,0,0,0.14);
}
.ld-more-menu__item {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 7px 10px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 6px;
  font-size: 0.85rem;
  text-align: left;
  color: var(--md-sys-color-on-surface);
}
.ld-more-menu__item:hover { background: var(--md-sys-color-surface-variant, rgba(0,0,0,0.05)); }
.ld-more-menu__item.more-menu-item--danger { color: #c62828; }
.ld-more-menu__item.more-menu-item--danger:hover { background: rgba(198,40,40,0.08); }
.ml-auto { margin-left: auto; }
.icon-btn {
  width: 28px; height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
}
.icon-btn:hover { background: rgba(0,0,0,0.06); color: var(--md-sys-color-on-surface); }
.ld-pop-enter-active, .ld-pop-leave-active { transition: opacity 0.12s ease, transform 0.12s ease; }
.ld-pop-enter-from, .ld-pop-leave-to { opacity: 0; transform: translateY(-4px); }

/* Tabs */
.lead-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 8px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  padding: 0 4px;
}
.lead-tab {
  padding: 8px 14px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 0.88rem;
  color: var(--md-sys-color-on-surface-variant);
  font-weight: 500;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: 0.12s ease;
}
.lead-tab:hover { color: var(--md-sys-color-on-surface); }
.lead-tab.active {
  color: var(--md-sys-color-primary, #1976d2);
  border-bottom-color: var(--md-sys-color-primary, #1976d2);
  font-weight: 600;
}

.project-header {
  padding: 16px 20px;
  background: var(--md-sys-color-surface);
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.project-tabs {
  background: var(--md-sys-color-surface);
  border-radius: 12px;
  padding: 8px;
}

.tab-btn {
  padding: 10px 18px;
  border: none;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  font-weight: 500;
  font-size: 0.9rem;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s;
  white-space: nowrap;
}

.tab-btn.active {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  box-shadow: 0 2px 8px rgba(var(--md-sys-color-primary-rgb), 0.3);
}

.card-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}

.bg-surface {
  background-color: var(--md-sys-color-surface);
}

.kp-card {
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 12px;
  padding: 16px;
  background: var(--md-sys-color-surface);
}

.kp-versions {
  margin-top: 12px;
  border-top: 1px dashed var(--md-sys-color-outline-variant);
  padding-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kp-version-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.btn-xs {
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 6px;
}

/* Mobile Responsive */
@media (max-width: 992px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  
  .dashboard-right {
    order: -1;
  }
}

@media (max-width: 768px) {
  .lead-detail-view h1 {
    font-size: 1.25rem !important;
  }
  
  .project-header .d-flex.justify-between {
    flex-direction: column;
    gap: 12px;
  }
  
  .project-header .d-flex.gap-2 {
    flex-wrap: wrap;
  }
  
  .modal-content {
    max-width: 100% !important;
  }
  
  .modal-body .d-flex.gap-2 {
    flex-direction: column;
  }
  
  .modal-body .w-50 {
    width: 100% !important;
  }
  
  .kp-card .d-flex.justify-between {
    flex-direction: column;
    gap: 8px;
  }
}


/* ============================================================
   Unified header (визуально как у ProjectDetail/«Сделок»)
   ============================================================ */
.unified-header {
  padding: 0 20px;
  background: var(--md-sys-color-surface);
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  border: 1px solid var(--glass-border-light, rgba(255, 255, 255, 0.3));
  margin-bottom: 16px;
}
.unified-header-inner {
  display: flex;
  align-items: center;
  gap: 16px;
  height: 56px;
}
.unified-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex-shrink: 1;
}
.unified-back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--md-sys-color-outline-variant);
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.8rem;
  transition: all 0.15s;
  flex-shrink: 0;
}
.unified-back-btn:hover {
  background: var(--md-sys-color-surface-container);
  color: var(--md-sys-color-on-surface);
}
.unified-title-group {
  display: flex;
  align-items: baseline;
  gap: 10px;
  min-width: 0;
}
.unified-project-name {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  line-height: 1.2;
  color: var(--md-sys-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.unified-obj-name {
  font-size: 0.8rem;
  color: var(--md-sys-color-on-surface-variant);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 60ch;
  flex-shrink: 1;
  min-width: 0;
}
.unified-nav {
  display: flex;
  align-items: center;
  gap: 2px;
  margin-left: auto;
  flex-shrink: 0;
  outline: none;
}
.unified-nav-item {
  position: relative;
  padding: 8px 14px;
  border: none;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  font-weight: 500;
  font-size: 0.82rem;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.15s;
  white-space: nowrap;
  letter-spacing: 0.01em;
}
.unified-nav-item:hover {
  color: var(--md-sys-color-on-surface);
  background: var(--md-sys-color-surface-container-low);
}
.unified-nav-item.active {
  color: var(--md-sys-color-primary);
  background: var(--md-sys-color-primary-container);
  font-weight: 600;
}
.unified-nav-item:focus-visible {
  outline: 2px solid var(--md-sys-color-primary);
  outline-offset: 1px;
}
.unified-header-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  margin-left: 8px;
}
.unified-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--md-sys-color-outline-variant);
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.8rem;
  transition: all 0.15s;
}
.unified-action-btn:hover {
  background: var(--md-sys-color-surface-container);
  color: var(--md-sys-color-on-surface);
}
.unified-action-btn--danger:hover {
  background: var(--color-danger-container, #ffebee);
  color: var(--color-danger, #c62828);
  border-color: var(--color-danger, #c62828);
}

/* ============================================================
   Inline-edit стиль для строк «Основной информации»
   ============================================================ */
.info-row--editable {
  cursor: text;
  border-radius: 6px;
  padding: 2px 6px;
  margin: 0 -6px;
  transition: background 0.12s ease;
}
.info-row--editable:hover {
  background: var(--md-sys-color-surface-container-low, rgba(15, 23, 42, 0.04));
}
.info-row--editable:hover .info-row__value::after {
  content: '\f303';
  font-family: 'Font Awesome 6 Free';
  font-weight: 900;
  margin-left: 8px;
  font-size: 0.7rem;
  opacity: 0.45;
}
.info-edit-input {
  flex: 1;
  min-width: 0;
  max-width: 60%;
  margin-left: auto;
  text-align: right;
  padding: 3px 8px;
  border: 1px solid var(--md-sys-color-primary, #1976d2);
  border-radius: 6px;
  font: inherit;
  font-weight: 500;
  background: var(--md-sys-color-surface, #fff);
  color: inherit;
  outline: none;
}
.info-edit-input:focus {
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.15);
}
.info-edit-input:disabled {
  opacity: 0.6;
}
.info-edit-select {
  flex: 1;
  min-width: 0;
  max-width: 70%;
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 4px;
}
.info-edit-select > :first-child {
  flex: 1;
  min-width: 0;
}
.info-edit-cancel {
  width: 26px;
  height: 26px;
  border: 1px solid var(--md-sys-color-outline-variant, rgba(15, 23, 42, 0.15));
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  flex-shrink: 0;
}
.info-edit-cancel:hover {
  background: var(--md-sys-color-surface-container);
  color: var(--color-danger, #c62828);
  border-color: var(--color-danger, #c62828);
}
.info-row__value--with-avatar {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  justify-content: flex-end;
}

/* ============================================================
   Целостный контейнер: шапка + контент = единый rounded box
   (без зазоров и индивидуальных рамок у внутренних карточек)
   ============================================================ */
.unified-header {
  margin-bottom: 0;
  border-radius: 12px 12px 0 0;
  border-bottom: 1px solid var(--md-sys-color-outline-variant, rgba(15, 23, 42, 0.08));
}
.lead-detail-body {
  border: 1px solid var(--md-sys-color-outline-variant, rgba(15, 23, 42, 0.08));
  border-top: none;
  border-radius: 0 0 12px 12px;
  background: var(--md-sys-color-surface, #fff);
  overflow: hidden;
}
/* Контейнеры табов внутри тела — без внешних отступов, чтобы
   внутренние карточки прилегали к рамке тела edge-to-edge. */
.lead-detail-body .scroll-container { padding: 0; }
/* Все внутренние .card снимают индивидуальную рамку/радиус/тень —
   они теперь секции одного большого контейнера, а не отдельные карточки. */
.lead-detail-body .card,
.lead-detail-body .dashboard-left .card,
.lead-detail-body .dashboard-right {
  border: none;
  border-radius: 0;
  box-shadow: none;
}
/* Двухколоночная сетка «Инфо»: без зазора, разделитель между колонками. */
.lead-detail-body .dashboard-grid {
  gap: 0;
  height: 100%;
}
.lead-detail-body .dashboard-grid .dashboard-right {
  border-left: 1px solid var(--md-sys-color-outline-variant, rgba(15, 23, 42, 0.08));
}
/* Левая колонка — это flex-column нескольких карточек; между ними даём
   горизонтальный разделитель, а не gap. */
.lead-detail-body .dashboard-left {
  gap: 0;
}
.lead-detail-body .dashboard-left > .card + .card {
  border-top: 1px solid var(--md-sys-color-outline-variant, rgba(15, 23, 42, 0.08));
}


</style>
