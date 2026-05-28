<template>
          <div
             v-if="activeTab === 'defacto'"
             id="panel-defacto"
             class="d-grid grid-sidebar-content h-100 gap-3"
             role="tabpanel"
             aria-labelledby="tab-defacto"
          >
             <div class="card d-flex flex-column h-100 overflow-hidden">
                <div class="card-header border-bottom p-3">
                   <h3 class="card-title m-0">Этапы</h3>
                </div>
                <div v-if="defactoLoading" class="p-3 d-flex flex-column gap-2">
                   <SkeletonLoader height="40px" v-for="i in 5" :key="i" />
                </div>
                <div v-else class="flex-grow-1 overflow-auto p-2">
                   <div v-for="stage in defactoData.stages" :key="stage.id" 
                        class="p-2 mb-2 rounded cursor-pointer transition-base"
                        :class="activeDefactoStageId === stage.id ? 'bg-primary-container border-primary border' : 'bg-surface hover-bg-light'"
                        @click="activeDefactoStageId = stage.id">
                      <div class="fw-600">{{ stage.name }}</div>
                   </div>
                </div>
             </div>
             
             <div class="card flex-grow-1 overflow-hidden d-flex flex-column">
                <div v-if="!selectedDefactoStage" class="d-flex justify-center align-center h-100 text-muted">Выберите этап</div>
                <div v-else class="d-flex flex-column h-100 overflow-hidden">
                   <div class="p-3 border-bottom bg-light d-flex justify-between align-center">
                      <h3 class="m-0">{{ selectedDefactoStage.name }}</h3>
                      <span class="text-muted small">{{ formatDate(selectedDefactoStage.date_end || selectedDefactoStage.date_start) }}</span>
                   </div>
                <div class="flex-grow-1 overflow-auto p-3 d-flex flex-column gap-2">
                      <div v-if="!selectedDefactoStage.products.length" class="text-muted text-center py-4">Нет томов/работ в этапе</div>
                      <div v-for="product in selectedDefactoStage.products" :key="product.deal_product_id" class="product-row border rounded bg-surface transition-base">
                         <!-- Header (Always Visible) -->
                         <div class="product-header p-3 d-flex justify-between align-center" :class="{ 'bg-light': expandedProductIds.includes(product.deal_product_id) }">
                            <div class="d-flex align-center gap-3 flex-grow-1 cursor-pointer" @click="toggleProduct(product.deal_product_id)">
                               <div class="icon-box">
                                  <i class="fas" :class="expandedProductIds.includes(product.deal_product_id) ? 'fa-chevron-down' : 'fa-chevron-right'"></i>
                               </div>
                                 <div class="fw-500" style="font-size: 1rem;">{{ product.name }}</div>
                                 <span v-if="product.latest_result" class="badge badge-sm" :class="getReviewStatusClass(product.latest_result.status)">
                                   {{ getReviewStatusText(product.latest_result.status) }}
                                   <span v-if="getReviewVersion(product.latest_result)" class="ml-1">v.{{ getReviewVersion(product.latest_result) }}</span>
                                 </span>
                               <!-- Subcontractor summary bubbles if collapsed -->
                               <div v-if="!expandedProductIds.includes(product.deal_product_id) && product.assignments.length" class="d-flex gap-2">
                                  <span v-for="a in product.assignments" :key="a.id" class="badge badge-sm badge-outline">
                                     {{ a.subcontractor_name || '?' }}
                                  </span>
                               </div>
                            </div>
                            
                            <!-- Right Side Stats -->
                            <div class="d-flex align-center gap-3">
                               <div class="text-muted small">
                                  {{ product.assignments.length }} исп.
                               </div>
                               <!-- Progress Summary -->
                               <div class="d-flex align-center gap-2" style="min-width: 100px;">
                                   <div class="progress-bar flex-grow-1" style="height: 6px; width: 60px; background: var(--md-sys-color-outline-variant);">
                                       <div class="progress-fill bg-success" :style="{ width: (countCompletedSubtasks(product) / countTotalSubtasks(product) * 100 || 0) + '%' }"></div>
                                   </div>
                                   <span class="small text-muted">{{ countCompletedSubtasks(product) }}/{{ countTotalSubtasks(product) }}</span>
                               </div>
                            </div>
                         </div>

                         <!-- Body (Collapsible) -->
                         <div v-if="expandedProductIds.includes(product.deal_product_id)" class="product-body border-top p-3 bg-surface">
                            <div v-if="!product.assignments.length" class="small text-muted">Нет назначений</div>
                            <div v-else class="d-flex flex-column gap-3">
                               <div v-for="assignment in product.assignments" :key="assignment.id" class="d-grid grid-cols-2 gap-3 border-bottom pb-3">
                                  <!-- Left: Assignment -->
                                  <div class="d-flex flex-column gap-2">
                                     <div>
                                        <span class="badge badge-info">{{ assignment.subcontractor_name || '?' }}</span>
                                     </div>
                                     <div class="d-flex align-center gap-2 flex-wrap">
                                        <span class="small text-muted" style="min-width: 110px;">Дата начала</span>
                                        <input type="date" v-model="assignment.start_date" class="form-control form-control-sm" style="width: 170px;" @change="updateAssignment(assignment)">
                                     </div>
                                     <div class="d-flex align-center gap-2 flex-wrap">
                                        <span class="small text-muted" style="min-width: 110px;">Рабочий срок</span>
                                        <input type="date" v-model="assignment.due_date" class="form-control form-control-sm" style="width: 170px;" @change="updateAssignment(assignment)">
                                     </div>
                                     <div class="d-flex align-center gap-2 flex-wrap">
                                        <span class="small text-muted" style="min-width: 110px;">Договорной срок</span>
                                        <input type="date" v-model="assignment.contract_due_date" class="form-control form-control-sm" style="width: 170px;" @change="updateAssignment(assignment)">
                                     </div>
                                     <div class="d-flex align-center gap-2 flex-wrap">
                                        <span class="small text-muted" style="min-width: 110px;">Статус</span>
                                        <select v-model="assignment.status" class="form-control form-control-sm" style="width: 170px;" :class="getDefactoStatusClass(assignment.status)" @change="updateAssignment(assignment)">
                                           <option value="not_started">Не начато</option>
                                           <option value="in_progress">В работе</option>
                                           <option value="completed">Готово</option>
                                           <option value="overdue">Просрочено</option>
                                        </select>
                                     </div>
                                  </div>
                                  <!-- Right: Subtasks -->
                                  <div class="d-flex flex-column gap-2 border-left pl-3">
                                     <div
                                        v-for="st in assignment.subtasks"
                                        :key="st.id"
                                        class="d-grid gap-2 align-center"
                                        style="grid-template-columns: 170px minmax(0, 1fr) 170px auto;"
                                     >
                                        <input type="date" v-model="st.due_date" class="form-control form-control-sm" style="width: 170px;" @change="updateSubtask(st)">
                                        <input v-model="st.title" class="form-control form-control-sm" @change="updateSubtask(st)">
                                        <select v-model="st.status" class="form-control form-control-sm" style="width: 170px;" :class="getDefactoStatusClass(st.status)" @change="updateSubtask(st)">
                                           <option value="not_started">Ждет</option>
                                           <option value="in_progress">В работе</option>
                                           <option value="completed">Готово</option>
                                        </select>
                                        <button class="btn btn-sm btn-icon text-danger" @click="deleteSubtask(st)">&times;</button>
                                     </div>
                                     <div class="d-flex gap-2 mt-1">
                                        <button class="btn btn-xs btn-outline-secondary" @click="autoSubtasks(assignment)">Авто-задачи</button>
                                        <button class="btn btn-xs btn-outline-secondary" @click="addSubtask(assignment)">+ Подзадача</button>
                                     </div>
                                  </div>
                               </div>
                            </div>
                         </div>
                      </div>
                </div>
                </div>
             </div>
          </div>
</template>

<script>
import SkeletonLoader from '../../../components/ui/SkeletonLoader.vue'
export default {
  name: 'Defacto',
  components: { SkeletonLoader },
  props: { state: { type: Object, required: true } },
  setup(props) {
    return { ...props.state }
  }
}
</script>
