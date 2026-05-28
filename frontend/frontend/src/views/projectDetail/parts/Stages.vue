<template>
          <div
             v-if="activeTab === 'stages'"
             id="panel-stages"
             class="card h-100 d-flex flex-column overflow-hidden"
             role="tabpanel"
             aria-labelledby="tab-stages"
          >
             <div class="card-header border-bottom p-3 d-flex justify-between align-center">
                <h3 class="card-title m-0">Этапы выполнения</h3>
                <div class="d-flex gap-2">
                   <button class="btn btn-sm btn-primary" @click="createStage">
                      <i class="fas fa-plus mr-1"></i> Новый этап
                   </button>
                   <button class="btn btn-sm btn-outline-primary" @click="selectTab('gantt')">
                      <i class="fas fa-chart-gantt mr-1"></i> Диаграмма Ганта
                   </button>
                </div>
             </div>
             <div ref="stagesScrollRef" class="flex-grow-1 overflow-auto p-0">
                <div v-if="stagesLoading" class="spinner mx-auto my-5"></div>
                <div v-else-if="!stages.length" class="text-center text-muted py-5">Нет этапов</div>
                <table v-else class="table table-hover m-0">
                   <thead class="sticky-top bg-surface">
                      <tr>
                         <th style="width: 50px;">#</th>
                         <th>Название</th>
                         <th>Связь</th>
                         <th>Тип</th>
                         <th>Срок</th>
                         <th>Даты</th>
                         <th>Индикатор</th>
                         <th>Тома/работы</th>
                         <th>Бюджет (план)</th>
                         <th>Закрывашки</th>
                         <th>Closed</th>
                         <th></th>
                      </tr>
                   </thead>
                   <tbody>
                      <tr v-if="isDragScopeActive('deal')">
                         <td colspan="12" class="stage-dropzone-cell">
                            <div
                              class="stage-root-dropzone"
                              :class="{ 'stage-root-dropzone--active': stageDropState.scope === 'deal' && stageDropState.mode === 'root' }"
                              @mouseenter="onDealStageRootDragOver"
                              @mouseup.left="applyDealStageDrop('root')"
                              @dragover.prevent="onDealStageRootDragOver"
                              @drop.prevent="applyDealStageDrop('root')"
                            >
                              <i class="fas fa-arrow-turn-up mr-1"></i>
                              Перетащите сюда, чтобы сделать этап верхнего уровня
                            </div>
                         </td>
                      </tr>
                      <tr
                        v-for="(stageEntry, idx) in visibleStages"
                        :key="stageEntry.id"
                        :style="stageRowStyle(stageEntry.stage)"
                        :class="{
                          'stage-drop-row': stageDropState.scope === 'deal' && stageDropState.mode === 'reorder' && stageDropState.targetId === stageEntry.id,
                          'stage-drag-self': isDragScopeActive('deal') && stageDragState.stageId === stageEntry.id
                        }"
                        @mouseenter="onDealStageRowDragOver(stageEntry.stage)"
                        @mouseup.left="applyDealStageDrop('reorder', stageEntry.stage)"
                        @dragover.prevent="onDealStageRowDragOver(stageEntry.stage)"
                        @drop.prevent="applyDealStageDrop('reorder', stageEntry.stage)"
                      >
                         <td>
                            <div class="stage-order-cell">
                               <span
                                 class="stage-drag-handle"
                                 draggable="true"
                                 title="Перетащить этап"
                                 @mousedown.stop="startStagePointerDrag('deal', stageEntry.stage, '', $event)"
                                 @dragstart="onStageDragStart('deal', stageEntry.stage, $event)"
                                 @dragend="onStageDragEnd"
                               >
                                  <i class="fas fa-grip-vertical"></i>
                               </span>
                               <span>{{ idx + 1 }}</span>
                            </div>
                         </td>
                         <td class="fw-500">
                            <div class="d-flex align-center gap-2" :style="{ paddingLeft: `${stageEntry.level * 18}px` }">
                               <button
                                 v-if="stageEntry.hasChildren"
                                 type="button"
                                 class="btn btn-sm btn-icon stage-tree-toggle"
                                 @click.stop="toggleStageBranch(stageEntry.id)"
                               >
                                  <i class="fas" :class="isStageBranchCollapsed(stageEntry.id) ? 'fa-chevron-right' : 'fa-chevron-down'"></i>
                               </button>
                               <span v-else class="stage-tree-spacer"></span>
                               <span>{{ stageEntry.stage.name }}</span>
                            </div>
                         </td>
                         <td class="stage-relation-cell">
                            <div class="stage-relation-list">
                               <span
                                 v-for="(relationItem, relationIndex) in getStageRelationItems(stageEntry.stage)"
                                 :key="`stage-relation-${stageEntry.id}-${relationIndex}`"
                                 class="small text-muted stage-relation-line"
                               >
                                  {{ relationItem }}
                               </span>
                            </div>
                            <div
                              v-if="isDragScopeActive('deal') && stageDragState.stageId !== stageEntry.id"
                              class="stage-drop-hint"
                              :class="{ 'stage-drop-hint--active': stageDropState.scope === 'deal' && stageDropState.mode === 'child' && stageDropState.targetId === stageEntry.id }"
                              @mouseenter="onDealStageChildDragOver(stageEntry.stage)"
                              @mouseup.left="applyDealStageDrop('child', stageEntry.stage)"
                              @dragover.prevent="onDealStageChildDragOver(stageEntry.stage)"
                              @drop.prevent="applyDealStageDrop('child', stageEntry.stage)"
                            >
                              <i class="fas fa-level-down-alt mr-1"></i>
                              Сделать дочерним этапом
                            </div>
                         </td>
                         <td><span :class="getStageTypeClass(stageEntry.stage.stage_type)">{{ getStageTypeLabel(stageEntry.stage.stage_type) }}</span></td>
                         <td>{{ stageEntry.stage.duration }} {{ getTermTypeLabel(stageEntry.stage.term_type) }}</td>
                         <td>
                            <div class="small">{{ formatDate(stageEntry.stage.date_start) }} - {{ formatDate(stageEntry.stage.date_end) }}</div>
                            <div v-if="stageEntry.stage.close_date" class="small text-success mt-1">
                               Закрыт: {{ formatDate(stageEntry.stage.close_date) }}
                            </div>
                         </td>
                         <td>
                            <span
                              class="stage-state-dot"
                              :class="getStageVisualClass(stageEntry.stage)"
                              :title="getStageVisualTitle(stageEntry.stage)"
                            ></span>
                         </td>
                         <td>
                            <button class="btn btn-sm btn-outline-secondary" @click="openStageProductsModal(stageEntry.stage)">
                               {{ getStageProductCount(stageEntry.id) }} томов/работ
                            </button>
                         </td>
                         <td>{{ formatCurrency(stageEntry.stage.planned_cost) }}</td>
                         <td class="stage-closing-docs-cell">
                            <div v-if="getStageClosingDocuments(stageEntry.stage).length" class="stage-closing-docs">
                              <button
                                v-for="doc in getStageClosingDocuments(stageEntry.stage)"
                                :key="doc.id"
                                type="button"
                                class="stage-closing-doc-chip"
                                @click.stop="openOutgoingClosingDocument(doc)"
                              >
                                <span>{{ doc.label }}</span>
                                <strong v-if="doc.amount">{{ formatCurrency(doc.amount) }}</strong>
                              </button>
                            </div>
                            <span v-else class="text-muted small">-</span>
                         </td>
                         <td class="text-center">
                            <input
                              type="checkbox"
                              :checked="isStageClosed(stageEntry.stage)"
                              :disabled="stageEntry.stage.stage_type === 'payment'"
                              @change="toggleStageClosed(stageEntry.stage, $event)"
                            />
                         </td>
                         <td class="text-right">
                            <div class="d-flex justify-end gap-1">
                               <button class="btn btn-sm btn-icon" title="Копировать этап" @click="copyStage(stageEntry.stage)"><i class="fas fa-copy"></i></button>
                               <button class="btn btn-sm btn-icon" @click="editStage(stageEntry.stage)"><i class="fas fa-pen"></i></button>
                               <button class="btn btn-sm btn-icon text-danger" @click="deleteStage(stageEntry.stage)"><i class="fas fa-trash"></i></button>
                            </div>
                         </td>
                      </tr>
                   </tbody>
                </table>
             </div>
          </div>
</template>

<script>

export default {
  name: 'Stages',
  
  props: { state: { type: Object, required: true } },
  setup(props) {
    return { ...props.state }
  }
}
</script>
