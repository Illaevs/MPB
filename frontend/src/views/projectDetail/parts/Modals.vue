<template>
  <div>
    <!-- Modals -->
    <!-- Add Product Modal -->
    <div v-if="showAddProductModal" class="modal-overlay" v-modal-close="closeModal">
      <div class="modal-content modal-product" @click.stop style="max-width: 860px;">
        <div class="modal-header">
           <h4>Добавить товар в смету</h4>
           <button class="btn-close" @click="closeModal"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body modal-body--visible">
           <div class="form-group mb-3">
              <label>Товар из каталога</label>
              <ProductSmartSelect
                v-model="selectedProductId"
                :options="availableProducts"
                placeholder="Найти товар"
              />
           </div>
           
           <div v-if="selectedProduct" class="p-3 bg-light rounded">
              <div class="form-group mb-2">
                 <label>Название (для сделки)</label>
                 <input v-model="dealProductForm.custom_name" class="form-control" :placeholder="selectedProduct.name">
              </div>
              <div class="d-flex gap-2 mb-2">
                 <div class="form-group w-50">
                    <label>{{ dealProductForm.tax_included ? 'Цена с НДС' : 'Цена без НДС' }}</label>
                    <input type="number" step="0.01" v-model.number="dealProductForm.custom_price" class="form-control" :placeholder="selectedProduct.base_price">
                 </div>
                 <div class="form-group w-50">
                    <label>Ед. изм.</label>
                    <input v-model="dealProductForm.unit" class="form-control">
                 </div>
              </div>
                  <div class="d-flex gap-2">
                     <div class="form-group w-50">
                        <label>Количество</label>
                        <input type="number" step="0.01" v-model.number="dealProductForm.quantity" class="form-control">
                     </div>
                     <div class="form-group w-50">
                        <label>Скидка (%)</label>
                        <input type="number" step="0.01" v-model.number="dealProductForm.discount_percent" class="form-control">
                     </div>
                  </div>
                  <div class="form-group mt-2 mb-0">
                     <label>Ставка НДС</label>
                     <select v-model.number="dealProductForm.tax_rate" class="form-control">
                        <option v-for="rate in vatRateOptions" :key="`deal-form-vat-${rate}`" :value="rate">{{ rate }}%</option>
                     </select>
                  </div>
                  <label class="form-check mt-2 mb-0 d-flex align-center gap-2">
                     <input v-model="dealProductForm.tax_included" type="checkbox" class="form-check-input">
                     <span>Указанная цена уже включает НДС</span>
                  </label>
                  <small class="text-muted d-block mt-1">
                     Если выключено, НДС начисляется сверху. Если включено, НДС выделяется из указанной цены.
                  </small>
               </div>
            </div>
            <div class="modal-footer">
           <button class="btn btn-secondary" @click="closeModal">Отмена</button>
           <button class="btn btn-primary" @click="addProductToDeal" :disabled="!selectedProduct">Добавить</button>
        </div>
      </div>
    </div>

    <!-- Create Stage Modal -->
    <div v-if="showCreateStageModal" class="modal-overlay" v-modal-close="closeCreateStageModal">
      <div class="modal-content" @click.stop style="max-width: 640px;">
        <div class="modal-header">
           <h4>{{ stageEditingId ? 'Редактировать этап' : 'Новый этап' }}</h4>
           <button class="btn-close" @click="closeCreateStageModal"><i class="fas fa-times"></i></button>
        </div>
        <form class="modal-body" @submit.prevent="saveStage()">
           <div class="form-group mb-2">
              <label>Название этапа *</label>
              <input v-model="stageForm.name" type="text" class="form-control" required>
           </div>
            <div class="d-flex gap-2 mb-2">
               <div class="form-group w-50">
                  <label>Родительский этап</label>
                  <select v-model="stageForm.parent_id" class="form-control">
                     <option value="">Без родителя</option>
                     <option v-for="option in stageLinkOptions" :key="`stage-parent-${option.id}`" :value="option.id">{{ option.name }}</option>
                  </select>
               </div>
               <div class="form-group w-50">
                  <label>Зависимости по этапам</label>
                  <div class="stage-dependency-picker">
                     <div v-if="!stageLinkOptions.length" class="text-muted small">Нет доступных этапов</div>
                     <label
                       v-for="option in stageLinkOptions"
                       :key="`stage-predecessor-${option.id}`"
                       class="stage-dependency-picker__item"
                     >
                        <input
                          v-model="stageForm.predecessor_ids"
                          type="checkbox"
                          :value="option.id"
                          @change="onStageDependencySelectionChange"
                        >
                        <span>{{ option.name }}</span>
                     </label>
                  </div>
               </div>
            </div>
            <div class="form-group mb-2" v-if="stageSelectedDependencies.length">
               <label>Лаг по связям, дней</label>
               <div class="stage-dependency-config-list">
                  <div
                    v-for="dependencyOption in stageSelectedDependencies"
                    :key="`stage-dependency-lag-${dependencyOption.id}`"
                    class="stage-dependency-config-item"
                  >
                     <span class="stage-dependency-config-item__name">{{ dependencyOption.name }}</span>
                     <input
                       type="number"
                       class="form-control"
                       :value="stageForm.dependency_settings?.[dependencyOption.id]?.lag ?? 0"
                       @input="setStageDependencyLag(dependencyOption.id, $event.target.value)"
                     >
                  </div>
               </div>
            </div>
           <div class="d-flex gap-2 mb-2">
              <div class="form-group w-50">
                 <label>Дата начала</label>
                 <input v-model="stageForm.date_start" type="date" class="form-control" @change="onStageStartOrDurationChange">
              </div>
              <div class="form-group w-50">
                 <label>Длительность *</label>
                 <input v-model.number="stageForm.duration" type="number" class="form-control" min="1" required @change="onStageStartOrDurationChange">
              </div>
           </div>
           <div class="form-group mb-2">
              <label>Дата окончания</label>
              <input :value="stageForm.date_end ? formatDate(stageForm.date_end) : '—'" type="text" class="form-control" disabled>
           </div>
           <div class="d-flex gap-2 mb-2">
              <div class="form-group w-50">
                 <label>Тип этапа</label>
                 <select v-model="stageForm.stage_type" class="form-control" :disabled="!!stageEditingId">
                    <option value="stage">Этап</option>
                    <option value="payment">Платеж</option>
                    <option value="other">Другое</option>
                 </select>
                 <small v-if="stageEditingId" class="text-muted">Тип этапа нельзя менять после создания</small>
              </div>
              <div class="form-group w-50">
                 <label>Тип сроков</label>
                 <select v-model="stageForm.term_type" class="form-control" @change="onStageTermTypeChange">
                    <option value="work_days">Рабочие дни</option>
                    <option value="calendar_days">Календарные дни</option>
                    <option value="week">Недели</option>
                    <option value="month">Месяцы</option>
                 </select>
              </div>
           </div>
           <div class="form-group mb-2">
              <label>Стоимость (план)</label>
              <input v-model.number="stageForm.planned_cost" type="number" step="0.01" class="form-control" min="0">
           </div>
           <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="closeCreateStageModal">Отмена</button>
              <button type="submit" class="btn btn-primary" :disabled="stageSaving">
                 <i v-if="stageSaving" class="fas fa-spinner fa-spin"></i>
                 <span v-else>{{ stageEditingId ? 'Сохранить' : 'Создать' }}</span>
              </button>
           </div>
        </form>
      </div>
    </div>

    <!-- GIP Selection Modal -->
    <div v-if="showGipDialog" class="modal-overlay" v-modal-close="closeGipDialog">
      <div class="modal-content" @click.stop style="max-width: 520px;">
        <div class="modal-header">
           <h4>Выбор ГИПа</h4>
           <button class="btn-close" @click="closeGipDialog"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
           <div class="form-group mb-3">
              <label>Поиск пользователя</label>
              <input
                ref="gipSearchInput"
                v-model="gipSearch"
                type="text"
                class="form-control"
                placeholder="Имя или email"
              >
           </div>
           <div class="border rounded p-2" style="max-height: 320px; overflow-y: auto;">
              <div v-if="!filteredGipUsers.length" class="text-muted small">Ничего не найдено</div>
              <button
                v-for="user in filteredGipUsers"
                :key="user.id"
                type="button"
                class="w-100 text-left p-2 border-0 bg-transparent hover-bg-light rounded"
                @click="addGip(user)"
              >
                <div class="fw-500">{{ user.full_name || user.email }}</div>
                <div class="text-muted small">{{ user.email || '-' }}</div>
              </button>
           </div>
        </div>
        <div class="modal-footer">
           <div class="small text-muted" style="margin-right: auto;">Выбрано: {{ gipUsers.length }}</div>
           <button class="btn btn-secondary" @click="closeGipDialog">Готово</button>
        </div>
      </div>
    </div>

    <!-- Edit Product Modal -->
    <div v-if="showEditProductModal" class="modal-overlay" v-modal-close="closeEditModal">
       <div class="modal-content" @click.stop style="max-width: 600px;">
          <div class="modal-header">
             <h4>Редактировать товар</h4>
             <button class="btn-close" @click="closeEditModal"><i class="fas fa-times"></i></button>
          </div>
          <div class="modal-body">
             <div class="p-3 bg-light rounded">
                <div class="form-group mb-2">
                   <label>Название</label>
                   <input v-model="dealProductForm.custom_name" class="form-control">
                </div>
                <div class="d-flex gap-2 mb-2">
                   <div class="form-group w-50">
                      <label>{{ dealProductForm.tax_included ? 'Цена с НДС' : 'Цена без НДС' }}</label>
                      <input type="number" step="0.01" v-model.number="dealProductForm.custom_price" class="form-control">
                   </div>
                   <div class="form-group w-50">
                      <label>Ед. изм.</label>
                      <input v-model="dealProductForm.unit" class="form-control">
                   </div>
                </div>
                    <div class="d-flex gap-2">
                       <div class="form-group w-50">
                          <label>Количество</label>
                          <input type="number" step="0.01" v-model.number="dealProductForm.quantity" class="form-control">
                       </div>
                       <div class="form-group w-50">
                          <label>Скидка (%)</label>
                          <input type="number" step="0.01" v-model.number="dealProductForm.discount_percent" class="form-control">
                       </div>
                    </div>
                    <div class="form-group mt-2 mb-0">
                       <label>Ставка НДС</label>
                       <select v-model.number="dealProductForm.tax_rate" class="form-control">
                          <option v-for="rate in vatRateOptions" :key="`deal-edit-vat-${rate}`" :value="rate">{{ rate }}%</option>
                       </select>
                    </div>
                    <label class="form-check mt-2 mb-0 d-flex align-center gap-2">
                       <input v-model="dealProductForm.tax_included" type="checkbox" class="form-check-input">
                       <span>Указанная цена уже включает НДС</span>
                    </label>
                    <small class="text-muted d-block mt-1">
                       Если выключено, НДС начисляется сверху. Если включено, НДС выделяется из указанной цены.
                    </small>
                 </div>
               </div>
               <div class="modal-footer">
             <button class="btn btn-secondary" @click="closeEditModal">Отмена</button>
             <button class="btn btn-primary" @click="updateDealProduct">Сохранить</button>
          </div>
       </div>
    </div>

    <!-- Stage Products Modal -->
    <div v-if="showStageProductsModal" class="modal-overlay" v-modal-close="closeStageProductsModal">
       <div class="modal-content" @click.stop style="max-width: 500px;">
          <div class="modal-header">
             <h4>Тома/работы для этапа</h4>
             <button class="btn-close" @click="closeStageProductsModal"><i class="fas fa-times"></i></button>
          </div>
          <div class="modal-body">
             <div class="mb-2 fw-600">{{ stageProductsModalStage?.name }}</div>
             <div class="border rounded p-2" style="max-height: 400px; overflow-y: auto;">
                 <div v-if="!stageProductsModalItems.length" class="text-muted small">Нет томов/работ в составе проекта</div>
                 <div v-else class="d-flex flex-column gap-2">
                    <label v-for="p in stageProductsModalItems" :key="p.id" class="d-flex align-center gap-2 cursor-pointer hover-bg-light p-1 rounded">
                       <input type="checkbox" :value="p.id" v-model="stageProductsModalSelection">
                       <span class="small">{{ p.custom_name || p.product?.name }}</span>
                    </label>
                 </div>
             </div>
          </div>
          <div class="modal-footer">
             <button class="btn btn-secondary" @click="closeStageProductsModal">Отмена</button>
             <button class="btn btn-primary" @click="saveStageProductsModal">Сохранить</button>
          </div>
       </div>
    </div>

    <!-- Subcontractor Stage Modal -->
    <div v-if="showSubStageModal" class="modal-overlay" v-modal-close="closeSubStageModal">
       <div class="modal-content" @click.stop style="max-width: 600px;">
          <div class="modal-header">
             <h4>{{ subStageEditingId ? 'Редактировать этап субподрядчика' : 'Новый этап субподрядчика' }}</h4>
             <button class="btn-close" @click="closeSubStageModal"><i class="fas fa-times"></i></button>
          </div>
          <form @submit.prevent="saveSubcontractorStage()" class="modal-body">
             <div class="form-group mb-2">
                <label>Субподрядчик</label>
                <input type="text" class="form-control" :value="subStageContext.subcontractor_name" disabled>
             </div>
             <div class="form-group mb-2">
                <label>Договор</label>
                <input type="text" class="form-control" :value="subStageContext.contract_label" disabled>
             </div>
             <div class="form-group mb-2">
                <label>Название этапа *</label>
                <input v-model="subStageForm.name" type="text" class="form-control" required>
             </div>
             <div class="form-group mb-2">
                <label>Описание</label>
                <textarea v-model="subStageForm.description" class="form-control" rows="2"></textarea>
             </div>
             <div class="d-flex gap-2 mb-2">
                <div class="form-group w-50">
                   <label>Дата начала</label>
                   <input v-model="subStageForm.date_start" type="date" class="form-control" @change="onSubStageStartOrDurationChange">
                </div>
                <div class="form-group w-50">
                   <label>Длительность *</label>
                   <input v-model.number="subStageForm.duration" type="number" class="form-control" min="1" required @change="onSubStageStartOrDurationChange">
                </div>
             </div>
             <div class="form-group mb-2">
                <label>Дата окончания</label>
                <input :value="subStageForm.date_end ? formatDate(subStageForm.date_end) : '—'" type="text" class="form-control" disabled>
             </div>
             <div class="d-flex gap-2 mb-2">
                <div class="form-group w-50">
                   <label>Тип этапа</label>
                   <select v-model="subStageForm.stage_type" class="form-control" :disabled="!!subStageEditingId">
                      <option value="stage">Этап</option>
                      <option value="payment">Платеж</option>
                      <option value="other">Другое</option>
                   </select>
                   <small v-if="subStageEditingId" class="text-muted">Тип этапа нельзя менять после создания</small>
                </div>
                <div class="form-group w-50">
                   <label>Тип сроков</label>
                   <select v-model="subStageForm.term_type" class="form-control" @change="onSubStageTermTypeChange">
                      <option value="work_days">Рабочие дни</option>
                      <option value="calendar_days">Календарные дни</option>
                      <option value="week">Недели</option>
                      <option value="month">Месяцы</option>
                   </select>
                 </div>
              </div>
             <div class="d-flex gap-2 mb-2">
                <div class="form-group w-50">
                   <label>Родительский этап</label>
                   <select v-model="subStageForm.parent_id" class="form-control">
                      <option value="">Без родителя</option>
                      <option v-for="option in subStageLinkOptions" :key="`substage-parent-${option.id}`" :value="option.id">{{ option.name }}</option>
                   </select>
                </div>
                <div class="form-group w-50">
                   <label>Зависит от этапа</label>
                   <select v-model="subStageForm.predecessor_id" class="form-control">
                      <option value="">Нет зависимости</option>
                      <option v-for="option in subStageLinkOptions" :key="`substage-predecessor-${option.id}`" :value="option.id">{{ option.name }}</option>
                   </select>
                </div>
             </div>
             <div class="form-group mb-2">
                <label>Лаг, дней</label>
                <input v-model.number="subStageForm.dependency_lag" type="number" class="form-control" step="1">
                <small class="text-muted">Сдвиг относительно зависимого этапа. Можно указать отрицательное значение.</small>
             </div>
             <div class="d-flex gap-2 mb-2">
                <div class="form-group w-50">
                   <label>Статус</label>
                   <select v-model="subStageForm.status" class="form-control">
                      <option value="planned">Планируется</option>
                      <option value="in_progress">В работе</option>
                      <option value="completed">Завершен</option>
                      <option value="delayed">Просрочен</option>
                   </select>
                </div>
                <div class="form-group w-50">
                   <label>Плановая стоимость</label>
                   <input v-model.number="subStageForm.planned_cost" type="number" class="form-control" step="0.01">
                </div>
             </div>
             <div v-if="subStageEditingId" class="form-group mb-2">
                <label>Фактическая стоимость</label>
                <input v-model.number="subStageForm.actual_cost" type="number" class="form-control" step="0.01">
             </div>
             <div class="form-group mb-2">
                <label>Тома/работы (по договору)</label>
                <div class="border rounded p-2" style="max-height: 220px; overflow-y: auto;">
                   <div v-if="!subStageProducts.length" class="text-muted small">Нет томов/работ по договору</div>
                   <label v-else v-for="p in subStageProducts" :key="p.id" class="d-flex align-center gap-2 cursor-pointer hover-bg-light p-1 rounded">
                      <input type="checkbox" :value="p.id" v-model="subStageProductIds">
                      <span class="small">{{ p.name }}</span>
                   </label>
                </div>
             </div>
             <div class="modal-footer">
                <button type="button" class="btn btn-secondary" @click="closeSubStageModal">Отмена</button>
                <button type="submit" class="btn btn-primary" :disabled="subStageSaving">
                   <i v-if="subStageSaving" class="fas fa-spinner fa-spin"></i>
                   <span v-else>Создать</span>
                </button>
             </div>
          </form>
       </div>
    </div>

    <!-- Confirm Modal -->
    <Teleport to="body">
      <div v-if="confirmModalOpen" class="modal-overlay confirm-overlay" v-modal-close="() => confirmModalOpen = false">
        <div class="modal-glass">
          <div class="modal-glass-header">
            <h5 class="m-0">{{ confirmModalTitle }}</h5>
            <button class="btn btn-sm btn-icon btn-ghost" @click="confirmModalOpen = false">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="modal-glass-body">
            <p class="m-0">{{ confirmModalText }}</p>
          </div>
          <div class="modal-glass-footer">
            <button class="btn btn-outline-secondary btn-sm" @click="confirmModalOpen = false">Отмена</button>
            <button class="btn btn-danger btn-sm" @click="executeConfirm">
              <i class="fas fa-check mr-1"></i> Подтвердить
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="stageCloseModalOpen" class="modal-overlay" v-modal-close="closeStageCloseModal">
        <div class="modal-glass stage-close-modal" @click.stop>
          <div class="modal-glass-header">
            <div>
              <h5 class="m-0">Дата закрытия этапа</h5>
              <div class="small text-muted mt-1">{{ stageCloseForm.stageName }}</div>
            </div>
            <button class="btn btn-sm btn-icon btn-ghost" @click="closeStageCloseModal">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="modal-glass-body d-flex flex-column gap-3">
            <div class="small text-muted">
              Плановый диапазон:
              <strong>{{ formatDate(stageCloseForm.rangeStart) }}</strong>
              —
              <strong>{{ formatDate(stageCloseForm.rangeEnd) }}</strong>
            </div>
            <div class="form-group m-0">
              <label>Дата закрытия</label>
              <input
                v-model="stageCloseForm.date"
                type="date"
                class="form-control"
                :class="{ 'stage-close-input--warning': isStageCloseOutOfRange }"
              >
            </div>
            <div v-if="isStageCloseOutOfRange" class="stage-close-warning">
              <i class="fas fa-exclamation-triangle"></i>
              <span>{{ stageCloseWarningText }}</span>
            </div>
          </div>
          <div class="modal-glass-footer">
            <button class="btn btn-outline-secondary btn-sm" @click="closeStageCloseModal">Отмена</button>
            <button class="btn btn-primary btn-sm" :disabled="stageCloseModalSaving" @click="submitStageCloseModal">
              <i v-if="stageCloseModalSaving" class="fas fa-spinner fa-spin mr-1"></i>
              <i v-else class="fas fa-check mr-1"></i>
              Сохранить
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div
        v-if="stageDragActive && stageDragState.stageId"
        class="stage-drag-cursor"
        :class="{
          'stage-drag-cursor--reorder': stageDropState.mode === 'reorder',
          'stage-drag-cursor--child': stageDropState.mode === 'child',
          'stage-drag-cursor--root': stageDropState.mode === 'root'
        }"
        :style="{
          left: `${stagePointerState.x + 16}px`,
          top: `${stagePointerState.y + 16}px`
        }"
      >
        <i
          class="fas"
          :class="stageDropState.mode === 'child'
            ? 'fa-level-down-alt'
            : stageDropState.mode === 'root'
              ? 'fa-arrow-turn-up'
              : 'fa-arrow-down'"
        ></i>
        <span>{{ stageDropHintText }}</span>
      </div>
    </Teleport>
    <!-- Edit Project Modal -->
    <Teleport to="body">
      <div v-if="showEditProjectModal" class="modal-overlay" v-modal-close="() => showEditProjectModal = false">
        <div class="modal-content modal-glass" @click.stop style="max-width: 640px;">
          <div class="modal-glass-header">
            <h4 class="m-0">Редактировать сделку</h4>
            <button class="btn btn-sm btn-icon btn-ghost" @click="showEditProjectModal = false">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <form class="modal-body" @submit.prevent="saveProjectEdit">
            <div class="form-group mb-2">
              <label>Название *</label>
              <input v-model="editProjectForm.title" type="text" class="form-control" required>
            </div>
            <div class="form-group mb-2">
              <label>Наименование объекта</label>
              <textarea v-model="editProjectForm.obj_name" class="form-control" rows="3"></textarea>
            </div>
            <div class="form-group mb-2">
              <label>Адрес</label>
              <textarea v-model="editProjectForm.address" class="form-control" rows="3"></textarea>
            </div>
            <div class="d-flex gap-2 mb-2">
              <div class="form-group w-50">
                <label>Тип объекта</label>
                <select v-model="editProjectForm.object_type" class="form-control">
                  <option value="">Не указан</option>
                  <option v-for="t in PROJECT_OBJECT_TYPES" :key="t" :value="t">{{ t }}</option>
                </select>
              </div>
              <div class="form-group w-50">
                <label>Площадь (м²)</label>
                <input v-model.number="editProjectForm.object_area" type="number" class="form-control" step="0.01">
              </div>
            </div>
            <div class="form-group mb-2">
              <label>Заказчик</label>
              <select v-model="editProjectForm.customer_id" class="form-control">
                <option value="">Не выбран</option>
                <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div class="form-group mb-2">
              <label>Статус</label>
              <select v-model="editProjectForm.status" class="form-control">
                <option value="active">Активен</option>
                <option value="completed">Завершен</option>
                <option value="on_hold">Пауза</option>
                <option value="cancelled">Отмена</option>
              </select>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="showEditProjectModal = false">Отмена</button>
              <button type="submit" class="btn btn-primary" :disabled="editProjectSaving">
                <i v-if="editProjectSaving" class="fas fa-spinner fa-spin mr-1"></i>
                <i v-else class="fas fa-save mr-1"></i> Сохранить
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script>
import ProductSmartSelect from '../../../components/ui/ProductSmartSelect.vue'
export default {
  name: 'ProjectDetailModals',
  components: { ProductSmartSelect },
  props: { state: { type: Object, required: true } },
  setup(props) {
    return { ...props.state }
  }
}
</script>
