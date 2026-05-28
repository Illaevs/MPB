<template>
          <div
             v-if="activeTab === 'dejure'"
             id="panel-dejure"
             class="dejure-layout d-flex flex-column h-100 gap-0"
             role="tabpanel"
             aria-labelledby="tab-dejure"
          >

             <!-- Row 1: Subcontractor Segmented Control -->
             <div class="dejure-topbar flex-shrink-0">
                <div v-if="dejureLoading" class="d-flex align-center justify-center py-3">
                   <div class="spinner" style="width: 24px; height: 24px; border-width: 2px;"></div>
                </div>
                <div v-else class="d-flex align-center gap-3">
                   <div v-if="dejureData.subcontractors.length" class="segmented-control">
                      <button
                         v-for="sub in dejureData.subcontractors"
                         :key="sub.id"
                         class="segment-item"
                         :class="{ active: selectedSubcontractorId === sub.id }"
                         @click="selectedSubcontractorId = sub.id"
                      >
                         <span class="segment-label">{{ sub.title || sub.obj_name || 'Субподрядчик' }}</span>
                         <span class="segment-count">{{ sub.contracts.length }}</span>
                      </button>
                   </div>
                   <span v-else class="text-muted small">Нет субподрядчиков</span>

                   <div class="d-flex align-center gap-2 ml-auto">
                      <div v-if="linkSubcontractorId" class="d-flex align-center gap-2">
                         <span class="dejure-filter-badge">
                            <i class="fas fa-filter" style="font-size: 0.65rem;"></i>
                            {{ linkSubcontractorName }}
                            <button class="dejure-filter-close" @click="clearLinkFilter"><i class="fas fa-times"></i></button>
                         </span>
                      </div>
                      <select ref="linkContractSelect" v-model="linkContractId" class="dejure-select">
                         <option value="">Договор...</option>
                         <option v-for="c in subcontractorLinkableContracts" :key="c.id" :value="c.id">{{ c.contract_number }}</option>
                      </select>
                      <button class="dejure-btn-primary" @click="linkContractToSubcontractor">
                         <i class="fas fa-link" style="font-size: 0.75rem;"></i>
                         Привязать
                      </button>
                   </div>
                </div>
             </div>

             <!-- Row 2: Contract Pills -->
             <div v-if="selectedSubcontractor" class="dejure-contracts-bar flex-shrink-0">
                <div class="d-flex align-center gap-2">
                   <div class="d-flex align-center gap-2 flex-grow-1 overflow-auto custom-scrollbar-x">
                      <button
                         v-for="contract in selectedSubcontractor.contracts"
                         :key="contract.id"
                         class="contract-pill"
                         :class="{ active: activeContractPill && activeContractPill.id === contract.id }"
                         @click="selectedContractPillId = contract.id"
                      >
                         <span class="pill-number">№{{ contract.contract_number }}</span>
                         <span class="pill-amount">{{ formatCurrency(contract.amount) }}</span>
                      </button>
                      <span v-if="!selectedSubcontractor.contracts.length" class="text-muted small">Нет договоров</span>
                   </div>
                   <button class="dejure-btn-ghost" @click="prepareContractLink(selectedSubcontractor)" title="Добавить договор">
                      <i class="fas fa-plus"></i>
                   </button>
                </div>
             </div>
             <div v-else-if="!dejureLoading" class="dejure-empty-state flex-grow-1 d-flex align-center justify-center">
                <div class="text-center">
                   <i class="fas fa-file-contract" style="font-size: 2.5rem; color: var(--md-sys-color-outline-variant);"></i>
                   <p class="text-muted mt-2 mb-0">Выберите субподрядчика</p>
                </div>
             </div>

             <!-- Row 3: Main Content — Товары & Этапы side by side -->
             <div v-if="selectedSubcontractor && activeContractPill" class="dejure-content flex-grow-1 overflow-auto">
                <!-- Contract meta -->
                <div class="dejure-contract-meta">
                   <div class="d-flex align-center gap-3">
                      <span class="text-muted small"><i class="fas fa-calendar-alt mr-1"></i>{{ formatDate(activeContractPill.contract_date) }}</span>
                      <span class="text-muted small"><i class="fas fa-building mr-1"></i>{{ selectedSubcontractor.address || '—' }}</span>
                   </div>
                </div>

                <div class="dejure-two-col">
                   <!-- Products Column -->
                   <div class="dejure-panel">
                      <div class="dejure-panel-header">
                         <div class="d-flex align-center gap-2">
                            <i class="fas fa-box" style="font-size: 0.85rem; color: var(--md-sys-color-primary);"></i>
                            <span class="dejure-panel-title">Тома/работы</span>
                            <span class="dejure-panel-count">{{ activeContractPill.products.length }}</span>
                         </div>
                      </div>
                      <div class="dejure-panel-body">
                         <div v-if="!activeContractPill.products.length" class="dejure-empty-mini">
                            <i class="fas fa-inbox"></i>
                            <span>Нет томов/работ</span>
                         </div>
                         <div v-else class="d-flex flex-column gap-2">
                            <div v-for="p in activeContractPill.products" :key="p.id" class="dejure-item">
                               <div class="dejure-item-main">
                                  <span class="dejure-item-name">{{ p.name }}</span>
                                  <div class="dejure-item-actions">
                                     <button class="dejure-btn-icon" @click="startEditSubProduct(p)" title="Редактировать">
                                        <i class="fas fa-pen"></i>
                                     </button>
                                     <button class="dejure-btn-icon dejure-btn-icon--danger" @click="deleteSubcontractorProduct(activeContractPill, p)" title="Удалить">
                                        <i class="fas fa-trash"></i>
                                     </button>
                                  </div>
                               </div>
                               <div v-if="isEditingSubProduct(p.id)" class="dejure-item-edit">
                                  <input type="number" step="0.01" class="dejure-input" style="width: 120px;" :value="getSubProductEdit(p.id).total" @input="setSubProductEditTotal(p.id, $event.target.value)" placeholder="Сумма">
                                  <button class="dejure-btn-sm dejure-btn-sm--primary" @click="saveSubProductEdit(activeContractPill, p)">OK</button>
                                  <button class="dejure-btn-sm" @click="cancelSubProductEdit(p.id)"><i class="fas fa-times"></i></button>
                               </div>
                               <div v-else class="dejure-item-price-row">
                                  <div class="dejure-item-price">{{ formatCurrency(p.total_price || p.unit_price) }}</div>
                                  <span class="dejure-item-tax">НДС {{ normalizeTaxRate(p.tax_rate) }}%</span>
                               </div>
                            </div>
                         </div>

                         <!-- Add product form -->
                         <div class="dejure-add-form">
                            <select :value="getSubProductDraft(activeContractPill.id).deal_product_id" @change="setSubProductDraftProduct(activeContractPill.id, $event.target.value)" class="dejure-input">
                               <option value="">Том/работа из состава проекта...</option>
                               <option v-for="dp in getAvailableDealProducts(activeContractPill)" :key="dp.id" :value="dp.id">
                                  {{ dp.custom_name || dp.product?.name }}
                               </option>
                            </select>
                            <div class="d-flex gap-2">
                               <input type="number" step="0.01" :value="getSubProductDraft(activeContractPill.id).unit_price" @input="setSubProductDraftPrice(activeContractPill.id, $event.target.value)" placeholder="Цена" class="dejure-input">
                               <select :value="getSubProductDraft(activeContractPill.id).tax_rate" @change="setSubProductDraftTax(activeContractPill.id, $event.target.value)" class="dejure-input" style="width: 80px;">
                                  <option v-for="rate in vatRateOptions" :key="`subcontract-vat-${rate}`" :value="rate">{{ rate }}%</option>
                               </select>
                               <button class="dejure-btn-sm dejure-btn-sm--primary" @click="addSubcontractorProduct(activeContractPill, selectedSubcontractor.id)">
                                  <i class="fas fa-plus" style="font-size: 0.7rem;"></i> Добавить
                               </button>
                            </div>
                         </div>
                      </div>
                   </div>

                   <!-- Stages Column -->
                   <div class="dejure-panel">
                      <div class="dejure-panel-header">
                         <div class="d-flex align-center gap-2">
                            <i class="fas fa-layer-group" style="font-size: 0.85rem; color: var(--md-sys-color-primary);"></i>
                            <span class="dejure-panel-title">Этапы</span>
                            <span class="dejure-panel-count">{{ activeContractPill.stages.length }}</span>
                         </div>
                         <button class="dejure-btn-ghost" @click="openSubStageModal(activeContractPill, selectedSubcontractor)" title="Добавить этап">
                            <i class="fas fa-plus"></i>
                         </button>
                      </div>
                      <div class="dejure-panel-body">
                         <div v-if="!activeContractPill.stages.length" class="dejure-empty-mini">
                            <i class="fas fa-stream"></i>
                            <span>Нет этапов</span>
                         </div>
                         <div v-else class="d-flex flex-column gap-2">
                            <div
                              v-if="isDragScopeActive('sub', activeContractPill.id)"
                              class="stage-root-dropzone"
                              :class="{ 'stage-root-dropzone--active': stageDropState.scope === 'sub' && stageDropState.mode === 'root' && stageDropState.contractId === normalizeUuid(activeContractPill.id) }"
                              @mouseenter="onSubStageRootDragOver"
                              @mouseup.left="applySubStageDrop('root')"
                              @dragover.prevent="onSubStageRootDragOver"
                              @drop.prevent="applySubStageDrop('root')"
                            >
                              <i class="fas fa-arrow-turn-up mr-1"></i>
                              Перетащите сюда, чтобы сделать этап верхнего уровня
                            </div>
                            <div
                              v-for="entry in visibleSubStages"
                              :key="entry.id"
                              class="dejure-item"
                              :style="dejureStageRowStyle(entry.stage)"
                              :class="{
                                'stage-drop-row': stageDropState.scope === 'sub' && stageDropState.mode === 'reorder' && stageDropState.targetId === entry.id && stageDropState.contractId === normalizeUuid(activeContractPill.id),
                                'stage-drag-self': isDragScopeActive('sub', activeContractPill.id) && stageDragState.stageId === entry.id && stageDragState.contractId === normalizeUuid(activeContractPill.id)
                              }"
                              @mouseenter="onSubStageRowDragOver(entry.stage)"
                              @mouseup.left="applySubStageDrop('reorder', entry.stage)"
                              @dragover.prevent="onSubStageRowDragOver(entry.stage)"
                              @drop.prevent="applySubStageDrop('reorder', entry.stage)"
                            >
                               <div class="dejure-item-main dejure-item-main--stage">
                                  <div class="dejure-stage-title d-flex align-center gap-2 flex-grow-1" :style="{ paddingLeft: `${entry.level * 18}px` }">
                                     <span
                                       class="stage-drag-handle"
                                       draggable="true"
                                       title="Перетащить этап"
                                        @mousedown.stop="startStagePointerDrag('sub', entry.stage, activeContractPill.id, $event)"
                                       @dragstart="onStageDragStart('sub', entry.stage, $event, activeContractPill.id)"
                                       @dragend="onStageDragEnd"
                                     >
                                        <i class="fas fa-grip-vertical"></i>
                                     </span>
                                     <button
                                       v-if="entry.hasChildren"
                                       type="button"
                                       class="btn btn-sm btn-icon stage-tree-toggle"
                                       @click.stop="toggleSubStageBranch(entry.id)"
                                     >
                                        <i class="fas" :class="isSubStageBranchCollapsed(entry.id) ? 'fa-chevron-right' : 'fa-chevron-down'"></i>
                                     </button>
                                     <span v-else class="stage-tree-spacer"></span>
                                     <span
                                       class="stage-state-dot"
                                       :class="getDejureStageVisualClass(entry.stage)"
                                       :title="getDejureStageVisualTitle(entry.stage)"
                                     ></span>
                                     <span class="dejure-item-name dejure-stage-name">{{ entry.stage.name }}</span>
                                  </div>
                                  <div class="dejure-item-actions">
                                     <span class="dejure-stage-cost" :title="'Плановая стоимость этапа'">
                                        {{ formatCurrency(entry.stage.planned_cost || 0) }}
                                     </span>
                                     <label class="dejure-stage-close" :title="'Закрыт'">
                                        <input
                                          type="checkbox"
                                          :checked="isDejureStageClosed(entry.stage)"
                                          :disabled="entry.stage.stage_type === 'payment'"
                                          @change="toggleDejureStageClosed(entry.stage, $event)"
                                        />
                                        <span>✓</span>
                                     </label>
                                     <button class="dejure-btn-icon" @click="editSubStage(entry.stage, activeContractPill, selectedSubcontractor)" title="Редактировать">
                                        <i class="fas fa-pen"></i>
                                     </button>
                                     <button class="dejure-btn-icon dejure-btn-icon--danger" @click="deleteSubStage(entry.stage)" title="Удалить">
                                        <i class="fas fa-trash"></i>
                                     </button>
                                  </div>
                               </div>
                               <div class="dejure-stage-meta">
                                  <span v-if="entry.stage.date_start" class="text-muted" style="font-size: 0.75rem;">
                                     <i class="fas fa-calendar-alt mr-1"></i>{{ formatDate(entry.stage.date_start) }}
                                  </span>
                                  <span v-if="entry.stage.date_end" class="text-muted" style="font-size: 0.75rem;">
                                     — {{ formatDate(entry.stage.date_end) }}
                                  </span>
                                  <span v-if="entry.stage.close_date" class="text-success" style="font-size: 0.75rem;">
                                     · Закрыт {{ formatDate(entry.stage.close_date) }}
                                  </span>
                                  <span v-if="entry.stage.stage_type" class="text-muted" style="font-size: 0.75rem;">
                                     · {{ getStageTypeLabel(entry.stage.stage_type) }}
                                  </span>
                                  <span v-if="getSubStageRelationLabel(entry.stage) !== '—'" class="text-muted" style="font-size: 0.75rem;">
                                     · {{ getSubStageRelationLabel(entry.stage) }}
                                  </span>
                               </div>
                               <div
                                 v-if="isDragScopeActive('sub', activeContractPill.id) && stageDragState.stageId !== entry.id"
                                 class="stage-drop-hint stage-drop-hint--inline"
                                 :class="{ 'stage-drop-hint--active': stageDropState.scope === 'sub' && stageDropState.mode === 'child' && stageDropState.targetId === entry.id && stageDropState.contractId === normalizeUuid(activeContractPill.id) }"
                                 @mouseenter="onSubStageChildDragOver(entry.stage)"
                                 @mouseup.left="applySubStageDrop('child', entry.stage)"
                                 @dragover.prevent="onSubStageChildDragOver(entry.stage)"
                                 @drop.prevent="applySubStageDrop('child', entry.stage)"
                               >
                                 <i class="fas fa-level-down-alt mr-1"></i>
                                 Сделать дочерним этапом
                               </div>
                            </div>
                         </div>
                      </div>
                   </div>
                </div>
             </div>
             <div v-else-if="selectedSubcontractor && !activeContractPill && selectedSubcontractor.contracts.length" class="dejure-empty-state flex-grow-1 d-flex align-center justify-center">
                <div class="text-center">
                   <i class="fas fa-hand-pointer" style="font-size: 2rem; color: var(--md-sys-color-outline-variant);"></i>
                   <p class="text-muted mt-2 mb-0">Выберите договор</p>
                </div>
             </div>
          </div>
</template>

<script>

export default {
  name: 'Dejure',
  
  props: { state: { type: Object, required: true } },
  setup(props) {
    return { ...props.state }
  }
}
</script>
