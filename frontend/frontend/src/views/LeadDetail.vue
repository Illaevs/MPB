
<template>
  <div class="lead-detail-view h-100 d-flex flex-column">
    <!-- Compact header card -->
    <header class="card lead-hero-card p-2 mb-2 flex-shrink-0">
      <nav class="lead-breadcrumb">
        <router-link to="/leads" class="lead-breadcrumb__link">
          <i class="fas fa-chevron-left mr-1"></i>Лиды
        </router-link>
        <span class="lead-breadcrumb__sep">/</span>
        <span class="lead-breadcrumb__current">{{ lead.title || 'Загрузка...' }}</span>
      </nav>
      <div class="lead-hero-row">
        <div class="lead-hero-title-block">
          <h2 class="lead-hero-title m-0">{{ lead.title || 'Лид без названия' }}</h2>
          <small v-if="lead.obj_name" class="text-muted">{{ lead.obj_name }}</small>
        </div>

        <div class="lead-hero-actions">
          <!-- Inline status badge -->
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
            @click="convertLead"
            :disabled="saving"
          >
            <i v-if="saving" class="fas fa-spinner fa-spin mr-1"></i>
            <i v-else class="fas fa-arrow-right-arrow-left mr-1"></i>Конвертировать
          </button>
          <button class="btn btn-sm btn-outline-secondary" @click="openEditModal">
            <i class="fas fa-edit mr-1"></i>Редактировать
          </button>
          <div class="ld-more-wrap">
            <button class="icon-btn" @click="ldMoreOpen = !ldMoreOpen" title="Действия">
              <i class="fas fa-ellipsis-vertical"></i>
            </button>
            <transition name="ld-pop">
              <div v-if="ldMoreOpen" class="ld-more-menu" v-click-outside="() => ldMoreOpen = false">
                <button class="ld-more-menu__item more-menu-item--danger" @click="deleteLead(); ldMoreOpen = false">
                  <i class="fas fa-trash mr-2"></i>Удалить лид
                </button>
              </div>
            </transition>
          </div>
        </div>
      </div>
    </header>

    <!-- Tabs -->
    <div class="lead-tabs flex-shrink-0">
      <button
        type="button"
        class="lead-tab"
        :class="{ active: activeTab === 'info' }"
        @click="setActiveTab('info')"
      >
        <i class="fas fa-info-circle mr-1"></i>Информация
      </button>
      <button
        type="button"
        class="lead-tab"
        :class="{ active: activeTab === 'timeline' }"
        @click="setActiveTab('timeline')"
      >
        <i class="fas fa-stream mr-1"></i>Таймлайн
      </button>
    </div>

    <div class="flex-grow-1 overflow-hidden position-relative">
      <div v-show="activeTab === 'info'" class="h-100 overflow-auto scroll-container p-1">
        <div v-if="loadingLead" class="spinner mx-auto my-5"></div>
        <div v-else class="dashboard-grid h-100">
          <div class="dashboard-left d-flex flex-column gap-3">
            <div class="card p-4">
              <h3 class="card-title mb-3">Основная информация</h3>
              <div class="info-grid">
                <div class="info-row">
                  <span class="text-muted">Название</span>
                  <span class="fw-500 text-right">{{ lead.title || '-' }}</span>
                </div>
                <div class="info-row">
                  <span class="text-muted">Наименование объекта</span>
                  <span class="fw-500 text-right">{{ lead.obj_name || '-' }}</span>
                </div>
                <div class="info-row">
                  <span class="text-muted">Адрес объекта</span>
                  <span class="fw-500 text-right">{{ lead.address || '-' }}</span>
                </div>
                <div class="info-row">
                  <span class="text-muted">Тип объекта</span>
                  <span class="fw-500 text-right">{{ lead.object_type || '-' }}</span>
                </div>
                <div class="info-row">
                  <span class="text-muted">Площадь</span>
                  <span class="fw-500 text-right">{{ lead.object_area ? `${lead.object_area} м²` : '-' }}</span>
                </div>
                <div class="separator my-2"></div>
                <div class="info-row">
                  <span class="text-muted">Заказчик</span>
                  <span class="fw-500 text-right">{{ getCompanyName(lead.customer_id) }}</span>
                </div>
                <div class="info-row">
                  <span class="text-muted">Наша компания</span>
                  <span class="fw-500 text-right">{{ getCompanyName(lead.our_company_id) }}</span>
                </div>
                <div class="info-row">
                  <span class="text-muted">Ответственный</span>
                  <span class="fw-500 text-right">{{ getUserName(lead.responsible_user_id) }}</span>
                </div>
                <div class="separator my-2"></div>
                <div class="info-row">
                  <span class="text-muted">% аванса</span>
                  <span class="fw-500 text-right">{{ lead.advance_percent ?? 0 }}%</span>
                </div>
                <div class="info-row">
                  <span class="text-muted">Ставка НДС</span>
                  <span class="fw-500 text-right">{{ vatRate }}%</span>
                </div>
                <div class="mt-2">
                  <label class="text-muted small">Изменить ставку НДС</label>
                  <div class="d-flex gap-2 align-center">
                    <select v-model.number="vatRate" class="form-control form-control-sm" style="max-width: 120px;">
                      <option v-for="rate in vatRateOptions" :key="`lead-vat-${rate}`" :value="rate">{{ rate }}%</option>
                    </select>
                    <button class="btn btn-sm btn-outline-primary" :disabled="!vatRateDirty || vatSaving" @click="saveVatRate">
                      <i v-if="vatSaving" class="fas fa-spinner fa-spin"></i>
                      <span v-else>Сохранить</span>
                    </button>
                  </div>
                </div>
                <div class="info-row">
                  <span class="text-muted">Стоимость</span>
                  <span class="fw-600 text-right text-primary">{{ formatCurrency(totalAmount) }}</span>
                </div>
              </div>
            </div>

            <div class="card p-4">
              <div class="d-flex justify-between align-center mb-3 flex-wrap gap-2">
                <h3 class="card-title m-0">Коммерческие предложения (КП)</h3>
                <div class="d-flex gap-2 flex-wrap">
                  <button class="btn btn-sm btn-primary" @click="openKpCreateModal">
                    <i class="fas fa-plus mr-1"></i> Создать КП
                  </button>
                  <button
                    v-if="canManageKpTemplates"
                    class="btn btn-sm btn-outline-secondary"
                    @click="openKpTemplatesModal"
                  >
                    <i class="fas fa-layer-group mr-1"></i> Шаблоны КП
                  </button>
                </div>
              </div>

              <div v-if="loadingKp" class="spinner mx-auto my-4"></div>
              <div v-else-if="!kpDocuments.length" class="text-muted text-center py-4">
                КП пока не созданы
              </div>
              <div v-else class="d-flex flex-column gap-3">
                <div v-for="doc in kpDocuments" :key="doc.id" class="kp-card">
                  <div class="d-flex justify-between align-center flex-wrap gap-2">
                    <div>
                      <div class="fw-600">{{ doc.number_display }}</div>
                      <small class="text-muted">
                        Версия {{ doc.current_version || 1 }} · {{ formatDate(doc.created_at) }}
                      </small>
                    </div>
                    <div class="d-flex align-center gap-2 flex-wrap">
                      <span class="badge badge-secondary">{{ doc.status || 'draft' }}</span>
                      <button
                        v-if="getKpTemplateDocx(doc)"
                        class="btn btn-sm btn-outline-primary"
                        @click="generateKpVersion(doc)"
                        :disabled="kpActionId === doc.id"
                      >
                        <i v-if="kpActionId === doc.id" class="fas fa-spinner fa-spin mr-1"></i>
                        <i v-else class="fas fa-magic mr-1"></i> Сгенерировать DOCX
                      </button>
                      <label class="btn btn-sm btn-outline-primary m-0">
                        <i class="fas fa-upload mr-1"></i> Загрузить версию
                        <input
                          type="file"
                          hidden
                          accept=".docx,.pdf"
                          @change="uploadKpVersion($event, doc)"
                        />
                      </label>
                    </div>
                  </div>

                  <div v-if="doc.versions && doc.versions.length" class="kp-versions">
                    <div
                      v-for="ver in doc.versions"
                      :key="ver.id"
                      class="kp-version-row"
                    >
                      <div class="d-flex flex-column">
                        <strong>v{{ ver.version }}</strong>
                        <small class="text-muted">
                          {{ formatCurrency(ver.total_amount || 0) }} · НДС {{ formatCurrency(ver.vat_amount || 0) }}
                        </small>
                      </div>
                      <div class="d-flex gap-2">
                        <a v-if="ver.docx_url" :href="ver.docx_url" target="_blank" rel="noopener noreferrer" class="btn btn-xs btn-outline-secondary">DOCX</a>
                        <a v-if="ver.pdf_url" :href="ver.pdf_url" target="_blank" rel="noopener noreferrer" class="btn btn-xs btn-outline-secondary">PDF</a>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="dashboard-right card p-0 d-flex flex-column h-100 overflow-hidden">
            <div class="card-header border-bottom p-4 d-flex justify-between align-center">
              <h3 class="card-title m-0">Товары</h3>
              <button class="btn btn-sm btn-primary" @click="showAddProductModal = true">
                <i class="fas fa-plus mr-1"></i> Добавить
              </button>
            </div>
            <div class="flex-grow-1 overflow-auto p-0">
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

      <!-- Timeline tab -->
      <div v-show="activeTab === 'timeline'" class="h-100 overflow-auto scroll-container p-2">
        <LeadTimeline
          :lead-id="route.params.id"
          :users="users"
          :current-user-id="currentUserId"
          @lead-updated="loadLead"
        />
      </div>
    </div>

    <div v-if="showAddProductModal" class="modal-overlay" @click="closeAddModal">
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

    <div v-if="showEditProductModal" class="modal-overlay" @click="closeEditModal">
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
      :internal-companies="internalCompanies"
      :users="users"
      :statuses="statusOptions.filter(s => s.key !== 'converted')"
      :saving="saving"
      @submit="onLeadFormSubmit"
      @cancel="closeEditLeadModal"
    />

    <div v-if="showKpCreateModal" class="modal-overlay" @click="closeKpCreateModal">
      <div class="modal-content" @click.stop style="max-width: 520px;">
        <div class="modal-header">
          <h4>Создать КП</h4>
          <button class="btn-close" @click="closeKpCreateModal"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Наша компания</label>
            <CompanySmartSelect
                v-model="kpForm.our_company_id"
                :options="internalCompanies"
                placeholder="Найти нашу компанию"
              />
          </div>
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

    <div v-if="showKpTemplatesModal" class="modal-overlay" @click="closeKpTemplatesModal">
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
import { ref, computed, onMounted, watch } from 'vue'
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
import ProductSmartSelect from '../components/ui/ProductSmartSelect.vue'
import LeadFormModal from '../components/leads/LeadFormModal.vue'
import LeadTimeline from '../components/leads/LeadTimeline.vue'
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
  components: { CompanySmartSelect, ProductSmartSelect, LeadFormModal, LeadTimeline },
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
    const bulkLeadTaxRate = ref(20)

    const showAddProductModal = ref(false)
    const showEditProductModal = ref(false)
    const showEditLeadModal = ref(false)
    const activeTab = ref(String(route.query?.tab || '') === 'timeline' ? 'timeline' : 'info')
    const ldStatusMenuOpen = ref(false)
    const ldStatusBusy = ref(false)
    const ldMoreOpen = ref(false)
    const setActiveTab = (t) => {
      activeTab.value = t
      const q = { ...(route.query || {}) }
      q.tab = t
      router.replace({ query: q }).catch(() => {})
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
      tax_rate: 20
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

    const getCompanyName = (id) => companyMap.value[normalizeId(id)] || '-'
    const getUserName = (id) => userMap.value[normalizeId(id)] || '-'
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
          tax_rate: Number(lead.value.vat_rate ?? 20)
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
      const defaultCompany = getCompanyIdForSelect(lead.value.our_company_id) || (internalCompanies.value[0]?.id || '')
      kpForm.value = {
        our_company_id: defaultCompany,
        template_id: '',
        vat_rate: lead.value.vat_rate ?? 20
      }
      showKpCreateModal.value = true
    }

    const closeKpCreateModal = () => {
      showKpCreateModal.value = false
    }

    const createKp = async () => {
      if (!kpForm.value.our_company_id) {
        toast.warning('Укажите нашу компанию')
        return
      }
      kpSaving.value = true
      try {
        const payload = {
          lead_id: route.params.id,
          our_company_id: kpForm.value.our_company_id || null,
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
      const vatRate = lead.value.vat_rate ?? 20
      return {
        number: kp.number_display,
        number_display: kp.number_display,
        date: formatDate(kp.created_at),
        lead_title: lead.value.title || '',
        obj_name: lead.value.obj_name || '',
        address: lead.value.address || '',
        object_type: lead.value.object_type || '',
        object_area: lead.value.object_area || '',
        customer_name: getCompanyName(lead.value.customer_id),
        our_company_name: getCompanyName(lead.value.our_company_id),
        advance_percent: lead.value.advance_percent ?? 0,
        vat_rate: vatRate,
        total_amount: latestVersion.total_amount ?? totalAmount.value,
        vat_amount: latestVersion.vat_amount ?? totalVatAmount.value,
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
      const response = await axios.get(templateUrl, { responseType: 'arraybuffer' })
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
      const templateUrl = getKpTemplateDocx(kp)
      if (!templateUrl) return
      kpActionId.value = kp.id
      const fileName = `${kp.number_display || 'KP'}.docx`
      const localId = uploadQueue.addLocalUpload({
        fileName,
        module: 'kp',
        entityId: kp.id
      })
      try {
        const data = buildKpTemplateData(kp)
        const blob = await generateKpDocxBlob(templateUrl, data)
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
      activeTab, setActiveTab,
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
      getCompanyName,
      getUserName,
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
</style>
