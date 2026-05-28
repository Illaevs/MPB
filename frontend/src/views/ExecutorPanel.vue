<template>
  <div class="executor-panel h-100 p-2">
    <div class="panel-layout d-flex gap-2 h-100">
      <!-- Sidebar -->
      <aside class="card sidebar-panel d-flex flex-column mb-0 flex-shrink-0">
        <div class="sidebar-header border-bottom border-light p-3 bg-transparent">
          <div class="d-flex justify-between align-center mb-3">
            <h4 class="m-0" style="font-size: 1rem;">Объекты</h4>
            <button class="btn btn-sm btn-icon" @click="refreshData" title="Обновить данные">
              <i class="fas fa-sync-alt" :class="{ 'fa-spin': refreshing }"></i>
            </button>
          </div>
          
          <!-- Status & Search Row -->
          <div class="d-flex gap-2">
            <select v-model="statusFilter" class="form-select form-select-sm" style="flex: 1;">
              <option value="">Статус</option>
              <option value="in_progress">В работе</option>
              <option value="delayed">Просрочен</option>
              <option value="planned">План</option>
              <option value="completed">Готово</option>
            </select>
            <div class="position-relative" style="flex: 1;">
              <i class="fas fa-search position-absolute text-muted" style="left: 8px; top: 7px; font-size: 0.75rem;"></i>
              <input
                v-model="search"
                type="text"
                class="form-control form-control-sm"
                placeholder="Поиск"
                style="padding-left: 26px;"
              />
            </div>
          </div>
        </div>

        <div class="sidebar-list flex-grow-1 overflow-auto p-2 custom-scrollbar">
          <div v-if="!filteredCards.length" class="text-center text-muted py-4 small">
             Объектов не найдено
          </div>
          <div
            v-for="card in filteredCards"
            :key="card.id"
            class="card mb-2 border-0 shadow-none bg-transparent"
          >
            <!-- Card Item -->
            <div
              class="card-body p-2 rounded-3 cursor-pointer sidebar-item"
              :class="{ 'active-item': expandedCards[card.id], 'hover-bg': !expandedCards[card.id] }"
              @click="toggleCard(card.id)"
            >
              <div class="d-flex justify-between align-center">
                <div class="overflow-hidden">
                  <h4 class="m-0 text-truncate" style="font-size: 0.9rem; font-weight: 600;" :title="card.obj_name || card.title">{{ card.obj_name || card.title }}</h4>
                  <div class="text-muted small mt-1 text-truncate" style="font-size: 0.75rem;" :title="card.address">
                    <i class="fas fa-map-marker-alt mr-1 opacity-50"></i>
                    <span>{{ card.address || '-' }}</span>
                  </div>
                </div>
                <div class="d-flex align-center gap-2">
                  <span v-if="card.stages?.length" class="badge badge-counter-sm">{{ card.stages.length }}</span>
                  <button class="btn btn-sm btn-icon ml-1 flex-shrink-0 text-muted">
                    <i class="fas transition-transform" :class="expandedCards[card.id] ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
                  </button>
                </div>
              </div>
            </div>
            
            <!-- Stages List -->
            <div v-if="expandedCards[card.id]" class="pl-2 pr-1 pb-1 pt-1">
               <div v-if="!getFilteredStages(card).length" class="text-muted small text-center py-1">Этапов нет</div>
               <div
                 v-for="stage in getFilteredStages(card)"
                 :key="stage.id"
                 class="p-2 rounded-3 mb-1 stage-item cursor-pointer"
                 :class="{ 'active-stage': stage.id === activeStageId }"
                 @click.stop="selectStage(card, stage)"
               >
                 <div class="d-flex justify-between align-center mb-1">
                    <span class="fw-500 text-truncate" style="font-size: 0.85rem;" :title="stage.name">{{ stage.name }}</span>
                 </div>
                 <div class="d-flex justify-between align-center small">
                    <span class="text-muted" style="font-size: 0.75rem;">
                      {{ formatDate(stage.date_end || stage.date_start) }}
                    </span>
                    <span class="badge badge-sm" :class="statusClass(stage.status)">
                      {{ statusLabel(stage.status) }}
                    </span>
                 </div>
               </div>
            </div>
          </div>
        </div>

        <!-- Sidebar Footer -->
        <div v-if="filteredCards.length" class="sidebar-footer p-2 border-top border-light">
          <div class="text-muted small text-center">
            {{ filteredCards.length }} объект{{ pluralSuffix(filteredCards.length) }}
          </div>
        </div>
      </aside>

      <!-- Main Content -->
      <main class="flex-grow-1 card mb-0 d-flex flex-column overflow-hidden bg-glass">
        <div v-if="!activeStage" class="d-flex flex-column align-center justify-center h-100 text-muted p-5 text-center">
          <div class="mb-3 opacity-50">
             <i class="fas fa-cubes fa-3x"></i>
          </div>
          <h3 class="mb-2">Выберите этап</h3>
          <p class="m-0 small" style="max-width: 300px;">Выберите объект и этап в левой панели, чтобы увидеть задачи, файлы и прогресс.</p>
        </div>

        <div v-else class="d-flex flex-column h-100 overflow-hidden">
          <!-- Stage Header -->
          <div class="stage-header border-bottom border-light px-3 py-2 bg-transparent flex-shrink-0">
             <!-- Row 1: Title + Status + Deadline -->
             <div class="d-flex justify-between align-center mb-2">
                <div class="d-flex align-center gap-2 overflow-hidden" style="min-width: 0;">
                   <h2 class="m-0 text-truncate" style="font-size: 1.1rem;" :title="activeStage.stage.name">{{ activeStage.stage.name }}</h2>
                   <span class="badge badge-sm" :class="statusClass(activeStage.stage.status)">
                     {{ statusLabel(activeStage.stage.status) }}
                   </span>
                </div>
                 <div class="text-right flex-shrink-0 executor-stage-actions">
                   <span class="text-muted small mr-2">Срок:</span>
                    <button class="executor-gantt-toggle" :class="{ active: stageViewMode === 'gantt' }" @click="stageViewMode = stageViewMode === 'gantt' ? 'list' : 'gantt'">
                      <i class="fas fa-chart-bar"></i>
                      <span>Гант</span>
                    </button>
                    <span class="fw-600 font-mono">{{ formatDate(activeStage.stage.date_end || activeStage.stage.date_start) }}</span>
                </div>
             </div>
             <!-- Row 2: Object + TZ Files -->
             <div class="d-flex justify-between align-center">
                <div class="text-muted small text-truncate" :title="activeStage.card.obj_name + ' • ' + activeStage.card.address">
                   {{ activeStage.card.obj_name || activeStage.card.title }} &bull; {{ activeStage.card.address || '-' }}
                </div>
                <!-- TZ Files Inline -->
                <div class="d-flex align-center gap-2 flex-shrink-0"
                     :class="{ 'tz-drag-over': dragOver === 'tz' }"
                     @dragover.prevent="dragOver = 'tz'"
                     @dragleave.prevent="dragOver = null"
                     @drop.prevent="handleDrop($event, currentFolderPath('tz'), 'tz')">
                   <span class="small text-muted"><i class="fas fa-file-alt mr-1"></i>ТЗ:</span>
                   <div v-if="folderItems.tz.loading"><i class="fas fa-spinner fa-spin text-muted small"></i></div>
                   <span v-else-if="!folderItems.tz.items.length" class="text-muted small">—</span>
                   <div v-for="item in folderItems.tz.items" :key="item.path" class="tz-link" @click="openFolderItem('tz', item)" :title="item.name">
                     <i class="fas fa-file-pdf text-danger" v-if="item.name.endsWith('.pdf')"></i>
                     <i class="fas fa-file-word text-primary" v-else-if="item.name.endsWith('.docx') || item.name.endsWith('.doc')"></i>
                     <i class="fas fa-folder text-warning" v-else-if="item.type === 'folder'"></i>
                     <i class="fas fa-file text-muted" v-else></i>
                     <span>{{ truncateFileName(item.name) }}</span>
                   </div>
                   <button v-if="folderPathStacks.tz.length" class="btn btn-xs btn-icon text-primary" @click="goFolderBack('tz')" title="Назад">
                     <i class="fas fa-arrow-left"></i>
                   </button>
                   <button v-if="folderPathStacks.tz.length" class="btn btn-xs btn-icon text-primary" @click="goFolderRoot('tz')" title="Корень">
                     <i class="fas fa-home"></i>
                   </button>
                   <button class="btn btn-xs btn-icon text-primary" @click="openFolder(currentFolderPath('tz'))" title="Открыть папку ТЗ">
                     <i class="fas fa-external-link-alt"></i>
                   </button>
                   <label class="btn btn-xs btn-icon m-0 text-primary cursor-pointer" title="Загрузить ТЗ">
                     <input type="file" multiple @change="uploadToFolder($event, currentFolderPath('tz'))" style="display: none;" />
                     <i class="fas fa-plus"></i>
                   </label>
                </div>
             </div>
          </div>

          <div
            v-if="stageViewMode === 'gantt'"
            class="executor-gantt-workspace flex-grow-1 overflow-hidden p-3"
          >
            <ExecutionGantt
              v-if="activeStage.products?.length"
              :groups="executorGanttGroups"
              search-placeholder="Поиск по товарам и подзадачам..."
              empty-title="Нет товаров и подзадач"
              empty-hint="Добавьте товары и подзадачи, чтобы построить график."
              group-count-label="поз\."
              name-column-label="НАИМЕНОВАНИЕ"
              status-column-label="СТАТУС"
              export-filename="gant-ispolnitelya.csv"
            />
            <div v-else class="card h-100 d-flex align-center justify-center text-muted">
              Нет товаров и задач
            </div>
          </div>

          <!-- Content Scrollable Area -->
          <div v-else class="flex-grow-1 overflow-auto p-3 custom-scrollbar">
             <!-- Files Section: 2 columns side by side -->
             <div class="files-grid mb-4">
                <!-- Other Files (Left Column) -->
                <div class="file-column">
                   <div class="file-section">
                      <div class="file-section-header">
                         <span class="fw-600"><i class="fas fa-folder-open mr-2 text-warning"></i> Документы</span>
                         <div class="d-flex gap-1">
                            <button v-if="folderPathStacks.other.length" class="btn btn-xs btn-icon text-primary" @click="goFolderBack('other')" title="Назад">
                              <i class="fas fa-arrow-left"></i>
                            </button>
                            <button v-if="folderPathStacks.other.length" class="btn btn-xs btn-icon text-primary" @click="goFolderRoot('other')" title="Корень">
                              <i class="fas fa-home"></i>
                            </button>
                            <button class="btn btn-xs btn-icon text-primary" @click="openFolder(currentFolderPath('other'))" title="Скачать">
                              <i class="fas fa-download"></i>
                            </button>
                         </div>
                      </div>
                      <div class="small text-muted mb-2">{{ folderBreadcrumb('other', 'Документы') }}</div>
                      <div 
                        class="file-list"
                      >
                         <div v-if="folderItems.other.loading" class="text-center py-2"><i class="fas fa-spinner fa-spin text-muted"></i></div>
                         <div v-else-if="!folderItems.other.items.length" class="empty-list">
                           <i class="fas fa-inbox text-muted"></i>
                           <span class="text-muted small">Нет файлов</span>
                         </div>
                         <div v-for="item in folderItems.other.items" :key="item.path" class="file-item" @click="openFolderItem('other', item)">
                            <i class="fas" :class="getFileIcon(item)"></i>
                            <span class="file-name" :title="item.name">{{ item.name }}</span>
                         </div>
                      </div>
                   </div>
                </div>

                <!-- Results Files (Right Column) -->
                <div class="file-column">
                   <div class="file-section">
                      <div class="file-section-header">
                         <span class="fw-600"><i class="fas fa-check-circle mr-2 text-success"></i> Результаты</span>
                         <div class="d-flex gap-1">
                            <button class="btn btn-sm btn-primary px-2" @click="openUploadModal">
                               <i class="fas fa-upload mr-1"></i> Загрузить
                            </button>
                            <button v-if="folderPathStacks.results.length" class="btn btn-xs btn-icon text-primary" @click="goFolderBack('results')" title="Назад">
                              <i class="fas fa-arrow-left"></i>
                            </button>
                            <button v-if="folderPathStacks.results.length" class="btn btn-xs btn-icon text-primary" @click="goFolderRoot('results')" title="Корень">
                              <i class="fas fa-home"></i>
                            </button>
                            <button class="btn btn-xs btn-icon text-primary" @click="openFolder(currentFolderPath('results'))" title="Открыть папку">
                              <i class="fas fa-external-link-alt"></i>
                            </button>
                         </div>
                      </div>
                      <div class="small text-muted mb-2">{{ folderBreadcrumb('results', 'Результаты') }}</div>
                      <div 
                        class="file-list drop-zone"
                        :class="{ 'drag-over': dragOver === 'results' }"
                        @dragover.prevent="dragOver = 'results'"
                        @dragleave.prevent="dragOver = null"
                        @drop.prevent="handleDrop($event, currentFolderPath('results'), 'results')"
                      >
                         <div v-if="folderItems.results.loading" class="text-center py-2"><i class="fas fa-spinner fa-spin text-muted"></i></div>
                         <div v-else-if="!folderItems.results.items.length" class="empty-list">
                           <i class="fas fa-inbox text-muted"></i>
                           <span class="text-muted small">Нет файлов</span>
                         </div>
                         <div v-for="item in folderItems.results.items" :key="item.path" class="file-item" @click="openFolderItem('results', item)">
                            <i class="fas" :class="getFileIcon(item)"></i>
                            <span class="file-name" :title="item.name">{{ item.name }}</span>
                         </div>
                      </div>
                   </div>
                </div>
             </div>

             <!-- History Section (Compact) -->
             <div v-if="stageResults.length" class="history-section mb-4">
                <div class="d-flex justify-between align-center mb-2">
                   <span class="small fw-600 text-muted"><i class="fas fa-history mr-2"></i> История согласований</span>
                   <span class="badge badge-counter-sm">{{ stageResults.length }}</span>
                </div>
                <div class="history-list">
                   <div v-for="item in stageResults" :key="item.id" class="history-item">
                      <div class="d-flex justify-between align-center">
                         <div class="d-flex align-center gap-2">
                           <span class="fw-500">{{ item.product_name }}</span>
                           <span class="badge badge-xs" :class="resultStatusClass(item.status)">{{ resultStatusLabel(item.status) }}</span>
                           <span class="text-muted small">{{ item.version_label }}</span>
                         </div>
                         <div class="d-flex align-center gap-2">
                           <small class="text-muted font-mono">{{ formatDate(item.created_at) }}</small>
                           <button class="btn btn-xs btn-text text-primary" @click="openResult(item)" title="Открыть">
                              <i class="fas fa-external-link-alt"></i>
                           </button>
                           <button v-if="(item.status || 'review') === 'review'" class="btn btn-xs btn-text text-danger" @click="withdrawResult(item)" title="Отозвать">
                              <i class="fas fa-undo"></i>
                           </button>
                         </div>
                      </div>
                   </div>
                </div>
             </div>

             <!-- Products & Subtasks -->
             <div class="card mb-3 border-light bg-surface-subtle shadow-sm executor-products-card">
                <div class="card-header bg-transparent border-bottom border-light py-2 px-3 d-flex justify-between align-center">
                   <div class="d-flex align-center gap-2">
                     <h3 class="m-0" style="font-size: 1.1rem;">Товары и подзадачи</h3>
                     <span v-if="activeStage.products?.length" class="badge badge-counter-sm">{{ activeStage.products.length }}</span>
                   </div>
                </div>
                <div class="card-body p-2">
                   <div v-if="!activeStage.products.length" class="p-4 text-muted text-center opacity-75">Нет товаров и задач</div>
                   <div v-else class="executor-products-grid">
                      <div
                        v-for="product in activeStage.products"
                        :key="product.id"
                        class="card border-light overflow-hidden executor-product-card"
                        :class="{ 'border-primary ring-2': expandedProducts[product.id] }"
                      >
                         <!-- Product Header -->
                         <div
                           class="card-body p-2 cursor-pointer transition-colors hover-bg-light executor-product-header"
                           @click="toggleProduct(product.id)"
                         >
                            <div class="d-flex justify-between align-center">
                               <div class="flex-grow-1 pr-3">
                                  <div class="d-flex align-center gap-2 mb-1">
                                     <i class="fas transition-transform text-muted" :class="expandedProducts[product.id] ? 'fa-chevron-down' : 'fa-chevron-right'"></i>
                                      <strong style="font-size: 1.05rem;" class="text-dark" :title="product.name">{{ product.name }}</strong>
                                      <span v-if="latestResultByProduct[normalizeName(product.name)]" class="badge badge-sm" :class="resultStatusClass(latestResultByProduct[normalizeName(product.name)].status)">
                                        {{ resultStatusLabel(latestResultByProduct[normalizeName(product.name)].status) }}
                                        <span v-if="getResultVersion(latestResultByProduct[normalizeName(product.name)])" class="ml-1">v.{{ getResultVersion(latestResultByProduct[normalizeName(product.name)]) }}</span>
                                      </span>
                                     <span class="product-status-pill" :class="assignmentIndicatorClass(product.status)">
                                        <span class="product-status-dot" :class="assignmentIndicatorClass(product.status)"></span>
                                        {{ assignmentStatusLabel(product.status) }}
                                     </span>
                                  </div>
                                  <div class="text-muted small ml-4 product-summary">
                                     {{ product.quantity }} {{ product.unit || 'шт' }} × <span class="font-mono">{{ formatMoney(product.unit_price) }}</span> = <strong class="text-dark font-mono">{{ formatMoney(product.total_price) }}</strong>
                                  </div>
                               </div>
                               <div class="text-right flex-shrink-0">
                                  <div class="text-muted small mb-1">Срок</div>
                                  <div class="fw-600 font-mono">{{ formatDate(product.due_date) }}</div>
                               </div>
                            </div>
                         </div>

                         <!-- Subtasks (Collapsible) -->
                         <div v-if="expandedProducts[product.id] && product.subtasks" class="border-top border-light executor-subtasks p-2">
                            <h5 class="mb-3 text-muted small text-uppercase">Подзадачи</h5>
                            <div v-if="!product.subtasks.length" class="text-muted small pl-2">Нет подзадач</div>
                            <div v-else class="d-flex flex-column gap-2">
                               <div
                                 v-for="subtask in product.subtasks"
                                 :key="subtask.id"
                                 class="subtask-row p-2 border border-light rounded shadow-sm"
                               >
                                  <div class="subtask-main d-flex align-center gap-3">
                                     <div class="bg-primary-subtle rounded-circle p-2 d-flex align-center justify-center subtask-icon">
                                        <i class="fas fa-tasks text-primary small"></i>
                                     </div>
                                     <span class="fw-500 subtask-title" :title="subtask.title">{{ subtask.title }}</span>
                                  </div>
                                  <div class="subtask-meta">
                                     <span class="subtask-status-pill" :class="assignmentIndicatorClass(subtask.status)">
                                        <span class="subtask-status-dot" :class="assignmentIndicatorClass(subtask.status)"></span>
                                        {{ assignmentStatusLabel(subtask.status) }}
                                     </span>
                                     <small class="text-muted subtask-deadline">Срок: {{ formatDate(subtask.due_date) }}</small>
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
      </main>
    </div>

    <!-- Upload Modal -->
    <div v-if="uploadModalOpen" class="modal-overlay" v-modal-close="closeUploadModal">
      <div class="modal-content glass-modal" style="max-width: 500px;">
        <div class="modal-header border-bottom border-light">
          <h3 class="m-0">Загрузка результата</h3>
          <button class="btn btn-sm btn-secondary" @click="closeUploadModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body p-4">
          <div class="form-group mb-3">
             <label class="small text-muted mb-1">Товар *</label>
             <select v-model="uploadForm.productName" class="form-select">
               <option value="">Выберите товар</option>
               <option v-for="product in activeStage.products" :key="product.id" :value="product.name">
                 {{ product.name }}
               </option>
             </select>
          </div>
          <div class="form-group mb-3">
             <label class="small text-muted mb-1">Комментарий</label>
             <textarea v-model="uploadForm.comment" rows="3" class="form-control" placeholder="Опишите что загружаете..."></textarea>
          </div>
          <div class="form-group mb-3">
             <label class="small text-muted mb-1">Файлы *</label>
             <input type="file" multiple @change="onResultFilesChange" class="form-control" />
          </div>
          <!-- File Preview -->
          <div v-if="uploadForm.files.length" class="file-preview p-3 rounded mb-3">
            <div class="small text-muted mb-2">Выбранные файлы:</div>
            <div class="d-flex flex-wrap gap-2">
              <div v-for="(file, idx) in uploadForm.files" :key="file.name + idx" class="file-preview-item">
                <i class="fas fa-file mr-1"></i>
                <span class="text-truncate" style="max-width: 120px;">{{ file.name }}</span>
                <button type="button" class="btn btn-sm btn-icon text-danger p-0 ml-1" @click="removeUploadFile(idx)">
                  <i class="fas fa-times"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer border-top border-light">
          <button class="btn btn-secondary" @click="closeUploadModal">Отмена</button>
          <button class="btn btn-primary" :disabled="uploadingResult || !uploadForm.productName || !uploadForm.files.length" @click="uploadResults">
            <i v-if="uploadingResult" class="fas fa-spinner fa-spin mr-2"></i>
            {{ uploadingResult ? 'Загрузка...' : 'Загрузить' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Success Modal -->
    <div v-if="successModalOpen" class="modal-overlay" v-modal-close="closeSuccessModal">
      <div class="modal-content glass-modal" style="max-width: 400px;">
        <div class="modal-body text-center p-5">
           <div class="mb-3 text-success">
              <i class="fas fa-check-circle fa-4x scale-in-center"></i>
           </div>
           <h3 class="mb-2">Готово!</h3>
           <p class="text-muted">{{ successMessage }}</p>
           <button class="btn btn-primary mt-3 px-4" @click="closeSuccessModal">OK</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { api } from '../services/api'
import { downloadFromPath, downloadFromHref } from '../utils/download'
import { useUploadQueueStore } from '../stores/uploadQueue'
import ExecutionGantt from '../components/ExecutionGantt.vue'

const cards = ref([])
const search = ref('')
const statusFilter = ref('')
const expandedCards = ref({})
const expandedProducts = ref({})
const stageViewMode = ref('list')
const activeStageId = ref(null)
const activeStage = ref(null)
const stageResults = ref([])
const historyLoading = ref(false)
const refreshing = ref(false)
const dragOver = ref(null)
const uploadQueue = useUploadQueueStore()

const folderItems = ref({
  tz: { items: [], loading: false },
  other: { items: [], loading: false },
  results: { items: [], loading: false }
})
const currentFolderPaths = ref({
  tz: '',
  other: '',
  results: ''
})
const folderPathStacks = ref({
  tz: [],
  other: [],
  results: []
})

const uploadModalOpen = ref(false)
const successModalOpen = ref(false)
const successMessage = ref('')
const uploadingResult = ref(false)
const uploadForm = ref({
  productName: '',
  comment: '',
  files: []
})

const normalizeName = (value) => (value || '').trim().toLowerCase().replace(/\s+/g, ' ')

const parseVersion = (label) => {
  if (!label) return null
  const match = label.match(/(\d+)/)
  return match ? Number(match[1]) : null
}

const getResultVersion = (item) => item?.version_number || parseVersion(item?.version_label)

const latestResultByProduct = computed(() => {
  const map = {}
  stageResults.value.forEach((item) => {
    const key = normalizeName(item.product_name)
    if (!key) return
    const current = map[key]
    const currentVersion = current ? getResultVersion(current) : null
    const nextVersion = getResultVersion(item)
    if (!current) {
      map[key] = item
      return
    }
    if (nextVersion && (!currentVersion || nextVersion > currentVersion)) {
      map[key] = item
      return
    }
    if (item.created_at && current.created_at && new Date(item.created_at) > new Date(current.created_at)) {
      map[key] = item
    }
  })
  return map
})

const normalizeExecutionStatus = (value) => {
  if (value === 'overdue' || value === 'delayed') return 'overdue'
  if (value === 'completed') return 'completed'
  if (value === 'in_progress') return 'in_progress'
  return 'not_started'
}

const aggregateExecutionProgress = (subtasks = [], status = 'not_started', startDateValue = '', dueDateValue = '') => {
  const normalized = normalizeExecutionStatus(status)
  if (normalized === 'completed') return 100
  const start = startDateValue ? new Date(`${String(startDateValue).slice(0, 10)}T00:00:00`) : null
  const due = dueDateValue ? new Date(`${String(dueDateValue).slice(0, 10)}T00:00:00`) : null
  if (!start || !due || Number.isNaN(start.getTime()) || Number.isNaN(due.getTime())) {
    if (subtasks.length) {
      const completed = subtasks.filter((task) => task.status === 'completed').length
      return Math.round((completed / subtasks.length) * 100)
    }
    if (normalized === 'in_progress') return 45
    if (normalized === 'overdue') return 35
    return 0
  }
  const totalDays = Math.round((due.getTime() - start.getTime()) / 86400000)
  if (totalDays <= 0) {
    return new Date() >= due ? 100 : 0
  }
  const today = new Date()
  const elapsedDays = Math.round((today.getTime() - start.getTime()) / 86400000)
  const ratio = (elapsedDays / totalDays) * 100
  return Math.max(0, Math.min(100, Math.round(ratio)))
}

const shiftIsoDate = (value, days = 0) => {
  if (!value) return ''
  const date = new Date(`${String(value).slice(0, 10)}T00:00:00`)
  if (Number.isNaN(date.getTime())) return ''
  date.setDate(date.getDate() + days)
  return date.toISOString().slice(0, 10)
}

const executorGanttGroups = computed(() => {
  if (!activeStage.value?.stage) return []
  const stage = activeStage.value.stage
  const stageStart = stage.date_start || stage.date_end || ''
  const productRows = (activeStage.value.products || []).map((product) => {
    const subtasks = (product.subtasks || []).map((subtask, index) => ({
      id: subtask.id || `${product.id}-${index}`,
      name: subtask.title || `Подзадача ${index + 1}`,
      status: normalizeExecutionStatus(subtask.status),
      progress: subtask.status === 'completed' ? 100 : (subtask.status === 'in_progress' ? 45 : 0),
      startDate: shiftIsoDate(subtask.due_date || product.due_date || stageStart, -7),
      endDate: subtask.due_date || product.due_date || stageStart,
      children: []
    }))
    return {
      id: `executor-product-${product.id}`,
      name: product.name,
      status: normalizeExecutionStatus(product.status),
      progress: aggregateExecutionProgress(product.subtasks || [], product.status, product.start_date || stageStart, product.due_date || stage.date_end || stageStart),
      startDate: product.start_date || stageStart,
      endDate: product.due_date || stage.date_end || stageStart,
      children: subtasks
    }
  })
  return [{
    id: `executor-stage-${stage.id}`,
    name: stage.name,
    status: normalizeExecutionStatus(stage.status),
    progress: Math.round(productRows.reduce((sum, row) => sum + Number(row.progress || 0), 0) / Math.max(productRows.length, 1)),
    startDate: stage.date_start || stageStart,
    endDate: stage.date_end || stageStart,
    items: productRows
  }]
})

const filteredCards = computed(() => {
  let result = cards.value
  const query = search.value.trim().toLowerCase()
  if (query) {
    result = result.filter((card) => {
      const name = (card.obj_name || card.title || '').toLowerCase()
      const address = (card.address || '').toLowerCase()
      return name.includes(query) || address.includes(query)
    })
  }
  return result
})

const getFilteredStages = (card) => {
  if (!statusFilter.value) return card.stages || []
  return (card.stages || []).filter(s => s.status === statusFilter.value)
}

const pluralSuffix = (count) => {
  if (count % 10 === 1 && count % 100 !== 11) return ''
  if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return 'а'
  return 'ов'
}

const loadCards = async () => {
  try {
    const data = await api.executor.listCards()
    cards.value = data || []
    if (activeStageId.value) {
      const hasActiveStage = cards.value.some((card) =>
        (card.stages || []).some((stage) => String(stage.id) === String(activeStageId.value))
      )
      if (!hasActiveStage) {
        activeStageId.value = null
        activeStage.value = null
        stageResults.value = []
        currentFolderPaths.value = { tz: '', other: '', results: '' }
        folderPathStacks.value = { tz: [], other: [], results: [] }
      }
    }
  } catch (error) {
    console.error('Error loading executor cards:', error)
    cards.value = []
  }
}

const refreshData = async () => {
  refreshing.value = true
  try {
    await loadCards()
    if (activeStageId.value && activeStage.value) {
      void loadFolderGroup()
      void loadStageHistory()
    }
  } finally {
    refreshing.value = false
  }
}

const setFolderRoots = () => {
  if (!activeStage.value?.folders) return
  currentFolderPaths.value = {
    tz: activeStage.value.folders.tz || '',
    other: activeStage.value.folders.other || '',
    results: activeStage.value.folders.results || ''
  }
  folderPathStacks.value = {
    tz: [],
    other: [],
    results: []
  }
}

const selectStage = async (card, stage) => {
  activeStageId.value = stage.id
  try {
    const data = await api.executor.getStage(stage.id, { subcontractor_card_id: card.id })
    activeStage.value = data
    setFolderRoots()
    void loadFolderGroup()
    void loadStageHistory()
  } catch (error) {
    console.error('Error loading stage:', error)
  }
}

const currentFolderPath = (key) => currentFolderPaths.value[key] || activeStage.value?.folders?.[key] || ''

const folderBreadcrumb = (key, label) => {
  const stack = folderPathStacks.value[key] || []
  if (!stack.length) return label
  return `${label} / ${stack.map(item => item.name).join(' / ')}`
}

const sortFolderItems = (items = []) => {
  return [...items].sort((a, b) => {
    if (a.type === 'folder' && b.type !== 'folder') return -1
    if (a.type !== 'folder' && b.type === 'folder') return 1
    return String(a.name || '').localeCompare(String(b.name || ''), 'ru')
  })
}

const loadFolderGroup = async () => {
  if (!activeStage.value) return
  await Promise.all([
    loadFolder('tz', currentFolderPath('tz')),
    loadFolder('other', currentFolderPath('other')),
    loadFolder('results', currentFolderPath('results'))
  ])
}

const loadFolder = async (key, path) => {
  folderItems.value[key].loading = true
  try {
    const data = await api.executor.storageList({ path })
    folderItems.value[key].items = sortFolderItems(data || [])
  } catch (error) {
    folderItems.value[key].items = []
    console.error('Error loading folder:', error)
  } finally {
    folderItems.value[key].loading = false
  }
}

const loadStageHistory = async () => {
  if (!activeStageId.value) return
  historyLoading.value = true
  try {
    const data = await api.executor.listResults({ stage_id: activeStageId.value })
    stageResults.value = data
  } catch (error) {
    stageResults.value = []
    console.error('Error loading results:', error)
  } finally {
    historyLoading.value = false
  }
}

const toggleCard = (cardId) => {
  expandedCards.value[cardId] = !expandedCards.value[cardId]
}

const toggleProduct = (productId) => {
  expandedProducts.value[productId] = !expandedProducts.value[productId]
}

const openFolder = async (path) => {
  try {
    if (!path) return
    const folderName = path.split('/').filter(Boolean).pop() || 'folder'
    await downloadFromPath(path, `${folderName}.zip`)
  } catch (error) {
    console.error('Error opening folder:', error)
  }
}

const openItem = async (item) => {
  if (item?.type !== 'file' || !item?.path) return
  try {
    const data = await api.executor.storageDownload({ path: item.path })
    if (data?.href) {
      await downloadFromHref(data.href, item.name || 'file')
    }
  } catch (error) {
    console.error('Error opening file:', error)
  }
}

const openFolderItem = async (key, item) => {
  if (!item?.path) return
  if (item.type === 'folder') {
    currentFolderPaths.value[key] = item.path
    folderPathStacks.value[key] = [...(folderPathStacks.value[key] || []), { name: item.name, path: item.path }]
    await loadFolder(key, item.path)
    return
  }
  await openItem(item)
}

const goFolderBack = async (key) => {
  const stack = [...(folderPathStacks.value[key] || [])]
  if (!stack.length) return
  stack.pop()
  folderPathStacks.value[key] = stack
  currentFolderPaths.value[key] = stack.length ? stack[stack.length - 1].path : (activeStage.value?.folders?.[key] || '')
  await loadFolder(key, currentFolderPaths.value[key])
}

const goFolderRoot = async (key) => {
  folderPathStacks.value[key] = []
  currentFolderPaths.value[key] = activeStage.value?.folders?.[key] || ''
  await loadFolder(key, currentFolderPaths.value[key])
}

const getFileIcon = (item) => {
  if (item.type === 'folder') return 'fa-folder text-warning'
  const ext = (item.name || '').split('.').pop().toLowerCase()
  if (['pdf'].includes(ext)) return 'fa-file-pdf text-danger'
  if (['doc', 'docx'].includes(ext)) return 'fa-file-word text-primary'
  if (['xls', 'xlsx'].includes(ext)) return 'fa-file-excel text-success'
  if (['jpg', 'jpeg', 'png', 'gif', 'jfif', 'webp'].includes(ext)) return 'fa-file-image text-info'
  if (['zip', 'rar', '7z'].includes(ext)) return 'fa-file-archive text-warning'
  return 'fa-file text-muted'
}

const truncateFileName = (name, maxLen = 20) => {
  if (!name || name.length <= maxLen) return name
  const ext = name.split('.').pop()
  const base = name.slice(0, name.length - ext.length - 1)
  const truncated = base.slice(0, maxLen - ext.length - 4) + '...'
  return truncated + '.' + ext
}

const openResult = async (item) => {
  if (!item) return
  const fallbackName = item.file_name || item.name || 'file'
  if (item.yandex_path) {
    try {
      await downloadFromPath(item.yandex_path, fallbackName)
      return
    } catch (e) {
      console.error(e)
    }
  }
  if (item.public_url) {
    await downloadFromHref(item.public_url, fallbackName)
  }
}

const uploadToFolder = async (event, path) => {
  const files = Array.from(event.target.files || [])
  if (!files.length) return
  void doUploadFiles(files, path)
  event.target.value = ''
}

const handleDrop = async (event, path, key) => {
  dragOver.value = null
  const files = Array.from(event.dataTransfer.files || [])
  if (!files.length) return
  void doUploadFiles(files, path)
}

const doUploadFiles = async (files, path) => {
  let hasSuccess = false
  for (const file of files) {
    const localId = uploadQueue.addLocalUpload({
      fileName: file.name,
      module: 'executor_storage',
      entityId: path
    })
    try {
      const form = new FormData()
      form.append('path', path)
      form.append('files', file)
      const response = await axios.post('/api/v1/executor/storage/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (event) => {
          if (!event.total) return
          const progress = (event.loaded / event.total) * 100
          uploadQueue.updateProgress(localId, progress)
        }
      })
      uploadQueue.markQueued(localId, response.data)
      hasSuccess = true
    } catch (error) {
      console.error('Error uploading files:', error)
      uploadQueue.markError(localId, error?.response?.data?.detail)
    }
  }
  if (hasSuccess) {
    void loadFolderGroup()
    successMessage.value = 'Загрузка отправлена в очередь'
    successModalOpen.value = true
  }
}

const openUploadModal = () => {
  if (!activeStage.value) return
  uploadForm.value = { productName: '', comment: '', files: [] }
  uploadModalOpen.value = true
}

const closeUploadModal = () => {
  uploadModalOpen.value = false
}

const closeSuccessModal = () => {
  successModalOpen.value = false
}

const onResultFilesChange = (event) => {
  uploadForm.value.files = Array.from(event.target.files || [])
}

const removeUploadFile = (index) => {
  uploadForm.value.files = uploadForm.value.files.filter((_, idx) => idx !== index)
}

const uploadResults = async () => {
  if (!uploadForm.value.productName || !uploadForm.value.files.length) {
    return
  }
  uploadingResult.value = true
  try {
    const localUploads = uploadForm.value.files.map((file) => ({
      file,
      localId: uploadQueue.addLocalUpload({
        fileName: file.name,
        module: 'executor_results',
        entityId: activeStage.value.stage.id
      })
    }))
    const form = new FormData()
    form.append('stage_id', activeStage.value.stage.id)
    form.append('product_name', uploadForm.value.productName)
    form.append('comment', uploadForm.value.comment || '')
    form.append('subcontractor_card_id', activeStage.value.card.id)
    if (activeStage.value.deal?.id) {
      form.append('deal_id', activeStage.value.deal.id)
    }
    localUploads.forEach(({ file }) => form.append('files', file))

    const response = await axios.post('/api/v1/uploads/executor/results', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (event) => {
        if (!event.total) return
        const progress = (event.loaded / event.total) * 100
        localUploads.forEach(({ localId }) => uploadQueue.updateProgress(localId, progress))
      }
    })
    const jobs = Array.isArray(response.data) ? response.data : []
    const byName = new Map(jobs.map((job) => [job.file_name, job]))
    localUploads.forEach(({ file, localId }) => {
      const job = byName.get(file.name) || jobs[0]
      if (job) {
        uploadQueue.markQueued(localId, job)
      } else {
        uploadQueue.markError(localId, 'Upload failed')
      }
    })
    uploadModalOpen.value = false
    void loadFolderGroup()
    void loadStageHistory()
    successMessage.value = 'Результаты отправлены в очередь'
    successModalOpen.value = true
  } catch (error) {
    console.error('Error uploading results:', error)
  } finally {
    uploadingResult.value = false
  }
}

const formatDate = (value) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

const formatMoney = (value) => {
  const amount = Number(value || 0)
  return amount.toLocaleString('ru-RU')
}

const resultStatusLabel = (status) => {
  const value = status || 'review'
  if (value === 'approved') return 'Согласовано'
  if (value === 'rejected') return 'Отклонено'
  if (value === 'send_back') return 'Отклонено'
  return 'На рассмотрении'
}

const resultStatusClass = (status) => {
  const value = status || 'review'
  if (value === 'approved') return 'badge-success'
  if (value === 'rejected') return 'badge-danger'
  if (value === 'send_back') return 'badge-warning'
  return 'badge-info'
}

const statusLabel = (status) => {
  if (status === 'completed') return 'Завершен'
  if (status === 'in_progress') return 'В работе'
  if (status === 'delayed') return 'Просрочен'
  return 'План'
}

const assignmentStatusLabel = (status) => {
  if (status === 'not_started') return 'Не начато'
  if (status === 'in_progress') return 'В работе'
  if (status === 'completed') return 'Завершено'
  if (status === 'overdue') return 'Просрочено'
  return status || '-'
}

const assignmentStatusClass = (status) => {
  if (status === 'not_started') return 'badge-secondary'
  if (status === 'in_progress') return 'badge-primary'
  if (status === 'completed') return 'badge-success'
  if (status === 'overdue') return 'badge-danger'
  return 'badge-info'
}

const assignmentIndicatorClass = (status) => {
  if (status === 'not_started') return 'status-not-started'
  if (status === 'in_progress') return 'status-in-progress'
  if (status === 'completed') return 'status-completed'
  if (status === 'overdue') return 'status-overdue'
  return 'status-default'
}

const statusClass = (status) => {
  if (status === 'completed') return 'badge-secondary'
  if (status === 'in_progress') return 'badge-success'
  if (status === 'delayed') return 'badge-danger'
  return 'badge-info'
}

const withdrawResult = async (item) => {
  if (!confirm('Отозвать результат? Запись будет удалена полностью.')) return
  try {
    await api.executor.removeResult(item.id)
    void loadStageHistory()
  } catch (error) {
    console.error('Error withdrawing result:', error)
    alert(error.response?.data?.detail || 'Ошибка удаления')
  }
}

onMounted(async () => {
  await loadCards()
})
</script>


<style scoped>
.fw-600 { font-weight: 600; }
.fw-500 { font-weight: 500; }
.font-mono { font-family: monospace; }
.cursor-pointer { cursor: pointer; }
.text-truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.sidebar-panel {
  width: 320px;
  min-width: 300px;
  max-width: 360px;
}

.sidebar-header {
  padding: 12px !important;
}

.sidebar-footer {
  background: var(--md-sys-color-surface-variant);
  padding: 8px 12px;
}

.badge-counter-sm {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 600;
}

.bg-glass {
   background-color: var(--md-sys-color-surface);
   backdrop-filter: var(--glass-blur);
   -webkit-backdrop-filter: var(--glass-blur);
}
.bg-surface-subtle {
   background-color: var(--md-sys-color-surface);
   backdrop-filter: var(--glass-blur);
   -webkit-backdrop-filter: var(--glass-blur);
   opacity: 1;
}

.executor-panel :deep(.card) {
  background: var(--md-sys-color-surface);
}

.executor-products-card {
  background: var(--md-sys-color-surface) !important;
}

.executor-gantt-workspace {
  min-height: 0;
}

.executor-gantt-workspace :deep(.execution-gantt) {
  height: 100%;
}

.executor-products-grid {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.executor-product-card {
  background: var(--md-sys-color-surface) !important;
  border-radius: 0;
  border-color: var(--md-sys-color-outline-variant) !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin-bottom: 0 !important;
  min-height: auto !important;
}

.executor-product-header {
  background: transparent !important;
  padding: 8px 10px !important;
}

.executor-product-header > .d-flex {
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 6px 10px;
  align-items: center;
}

.executor-product-header .flex-grow-1 {
  min-width: 0;
  padding-right: 0 !important;
}

.executor-product-header .flex-grow-1 > .d-flex {
  display: grid !important;
  grid-template-columns: 14px minmax(0, 1fr) auto;
  column-gap: 6px;
  row-gap: 3px;
  align-items: center;
  margin-bottom: 0 !important;
}

.executor-product-header .flex-grow-1 > .d-flex > i {
  grid-column: 1;
  grid-row: 1;
}

.executor-product-header .flex-grow-1 > .d-flex > strong {
  grid-column: 2;
  grid-row: 1;
  min-width: 0;
  font-size: 0.92rem !important;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.executor-product-header .flex-grow-1 > .d-flex > .badge {
  grid-column: 2;
  grid-row: 2;
  justify-self: start;
  max-width: 100%;
}

.executor-product-header .flex-grow-1 > .d-flex > .product-status-pill {
  grid-column: 3;
  grid-row: 1 / span 2;
  justify-self: end;
  align-self: center;
}

.executor-product-header .text-right.flex-shrink-0 {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.executor-product-header .text-right.flex-shrink-0 .text-muted.small.mb-1 {
  margin-bottom: 0 !important;
}

.executor-product-header .text-right.flex-shrink-0 .fw-600.font-mono {
  font-size: 0.78rem;
}

.executor-products-card > .card-body {
  padding: 0 !important;
}

.executor-products-card {
  padding: 0 !important;
}

.executor-products-card > .card-header {
  margin-bottom: 0 !important;
}

.executor-products-grid > .executor-product-card + .executor-product-card {
  border-top: none;
}

.executor-subtasks {
  background: rgba(127, 127, 127, 0.04);
  padding: 6px 8px !important;
}

.executor-subtasks h5 {
  margin-bottom: 6px !important;
}

.sidebar-item {
   transition: all 0.2s;
   border: 1px solid transparent;
   padding: 8px !important;
}
.sidebar-item:hover, .hover-bg:hover {
   background-color: rgba(var(--md-sys-color-on-surface-rgb), 0.04);
}
.active-item {
   background-color: var(--md-sys-color-primary-container);
   color: var(--md-sys-color-on-primary-container);
}

.stage-item {
   transition: all 0.2s;
   border: 1px solid transparent;
   padding: 6px 8px !important;
}
.stage-item:hover {
   background-color: rgba(var(--md-sys-color-on-surface-rgb), 0.04);
}
.active-stage {
   background-color: var(--md-sys-color-secondary-container);
   color: var(--md-sys-color-on-secondary-container);
   border-left: 3px solid var(--md-sys-color-secondary);
}

.executor-stage-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.executor-gantt-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 30px;
  padding: 0 10px;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.84);
  color: var(--md-sys-color-on-surface);
  font-size: 0.72rem;
  font-weight: 700;
}

.executor-gantt-toggle.active {
  background: rgba(var(--md-sys-color-primary-rgb), 0.12);
  border-color: rgba(var(--md-sys-color-primary-rgb), 0.28);
  color: var(--md-sys-color-primary);
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 20px;
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline-variant);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.15s;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.chip:hover {
  background: var(--md-sys-color-surface-variant);
  box-shadow: 0 2px 4px rgba(0,0,0,0.08);
}

.result-item {
   transition: transform 0.2s;
}
.result-item:hover {
   transform: translateY(-1px);
   box-shadow: 0 4px 6px rgba(0,0,0,0.05);
}

.ring-2 {
   box-shadow: 0 0 0 2px var(--md-sys-color-primary);
}
.hover-bg-light:hover {
   background-color: var(--md-sys-color-surface-variant);
}

.transition-transform { transition: transform 0.3s; }
.transition-colors { transition: background-color 0.2s; }

.product-summary {
  display: none;
}

.product-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
  border: 1px solid transparent;
}

.product-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex: 0 0 8px;
  background: currentColor;
}

.subtask-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 6px 8px !important;
  border-radius: 8px;
  box-shadow: none !important;
}

.subtask-main {
  min-width: 0;
  flex: 1 1 auto;
  gap: 8px !important;
}

.subtask-icon {
  width: 26px;
  height: 26px;
  flex: 0 0 26px;
}

.subtask-title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.subtask-meta {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex: 0 0 auto;
  margin-left: auto;
}

.subtask-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
  border: 1px solid transparent;
}

.subtask-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex: 0 0 8px;
  background: currentColor;
}

.subtask-deadline {
  white-space: nowrap;
}

.status-not-started {
  color: #6b7280;
  background: rgba(107, 114, 128, 0.12);
  border-color: rgba(107, 114, 128, 0.18);
}

.status-in-progress {
  color: #2563eb;
  background: rgba(37, 99, 235, 0.12);
  border-color: rgba(37, 99, 235, 0.18);
}

.status-completed {
  color: #16a34a;
  background: rgba(22, 163, 74, 0.12);
  border-color: rgba(22, 163, 74, 0.18);
}

.status-overdue {
  color: #dc2626;
  background: rgba(220, 38, 38, 0.12);
  border-color: rgba(220, 38, 38, 0.18);
}

.status-default {
  color: #7c3aed;
  background: rgba(124, 58, 237, 0.12);
  border-color: rgba(124, 58, 237, 0.18);
}

:root[data-theme="dark"] .executor-subtasks,
:root[data-theme="dark"] .subtask-row,
:root[data-theme="dark"] .executor-product-card {
  background: rgba(255, 255, 255, 0.03);
}

/* Drop Zone */
.drop-zone {
  min-height: 48px;
  border: 1px dashed transparent;
  transition: all 0.15s;
  border-radius: 8px;
}

.drop-zone.drag-over {
  border-color: var(--md-sys-color-primary);
  background: rgba(var(--md-sys-color-primary-rgb), 0.06);
}

.drop-placeholder {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 8px;
  opacity: 0.5;
  padding: 8px;
}

.drop-placeholder i {
  font-size: 1rem;
}

.drop-placeholder .text-muted {
  font-size: 0.75rem;
}

/* File Preview */
.file-preview {
  background: var(--md-sys-color-surface-variant);
}

.file-preview-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: var(--md-sys-color-surface);
  border-radius: 20px;
  font-size: 0.8rem;
  border: 1px solid var(--md-sys-color-outline-variant);
}

/* Custom Scrollbar for inner areas */
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background-color: rgba(0,0,0,0.1); border-radius: 3px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background-color: rgba(0,0,0,0.2); }

.glass-modal {
   backdrop-filter: blur(10px);
   background-color: rgba(255, 255, 255, 0.9);
}

.scale-in-center {
	animation: scale-in-center 0.5s cubic-bezier(0.250, 0.460, 0.450, 0.940) both;
}
@keyframes scale-in-center {
  0% { transform: scale(0); opacity: 1; }
  100% { transform: scale(1); opacity: 1; }
}

/* Files Grid - 2 columns */
.files-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

@media (max-width: 768px) {
  .executor-product-header > .d-flex {
    grid-template-columns: 1fr;
  }

  .executor-product-header .text-right.flex-shrink-0 {
    justify-content: flex-start;
  }

  .executor-product-header .flex-grow-1 > .d-flex {
    grid-template-columns: 14px minmax(0, 1fr);
  }

  .executor-product-header .flex-grow-1 > .d-flex > .product-status-pill {
    grid-column: 2;
    grid-row: 3;
    justify-self: start;
  }

  .files-grid {
    grid-template-columns: 1fr;
  }

  .subtask-row {
    align-items: flex-start;
    flex-direction: column;
  }

  .subtask-meta {
    width: 100%;
    justify-content: space-between;
  }
}

.file-column {
  min-width: 0;
}

/* TZ Link in Header */
.tz-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: var(--md-sys-color-surface-variant);
  border-radius: 12px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s;
  color: var(--md-sys-color-on-surface);
}

.tz-link:hover {
  background: var(--md-sys-color-primary-container);
}

.tz-link span {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tz-drag-over {
  background: rgba(var(--md-sys-color-primary-rgb), 0.1);
  border-radius: 8px;
}

/* File Section */
.file-section {
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 12px;
  overflow: hidden;
}

.file-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: var(--md-sys-color-surface-variant);
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.file-list {
  max-height: 300px;
  overflow-y: auto;
  padding: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}

.file-item:hover {
  background: var(--md-sys-color-surface-variant);
}

.file-item i {
  font-size: 0.9rem;
  width: 18px;
  text-align: center;
}

.file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.85rem;
}

.empty-list {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  opacity: 0.6;
}

/* History Section */
.history-section {
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 12px;
  padding: 12px;
}

.history-list {
  max-height: 200px;
  overflow-y: auto;
}

.history-item {
  padding: 8px 10px;
  border-radius: 6px;
  margin-bottom: 4px;
  background: var(--md-sys-color-surface-variant);
}

.history-item:hover {
  background: var(--md-sys-color-primary-container);
}

.badge-xs {
  font-size: 0.65rem;
  padding: 2px 6px;
}

.btn-xs {
  padding: 2px 6px;
  font-size: 0.7rem;
}

/* Mobile Responsive */
@media (max-width: 992px) {
  .panel-layout {
    flex-direction: column;
  }
  
  .sidebar-panel {
    width: 100% !important;
    max-width: none !important;
    min-width: auto !important;
    max-height: 40vh;
  }
}

@media (max-width: 768px) {
  .executor-panel {
    padding: 0 !important;
  }
  
  .panel-layout {
    gap: 0;
  }
  
  .sidebar-panel {
    max-height: 35vh;
    border-radius: 0 0 16px 16px !important;
  }
  
  .sidebar-header {
    padding: 10px !important;
  }
  
  .stage-header {
    padding: 8px 10px !important;
  }
  
  .stage-header h2 {
    font-size: 1rem !important;
  }
  
  .files-grid {
    grid-template-columns: 1fr !important;
    gap: 12px;
  }
  
  .file-section {
    border-radius: 10px;
  }
  
  .file-list {
    max-height: 150px;
  }
  
  .history-section {
    padding: 10px;
    border-radius: 10px;
  }
  
  .history-list {
    max-height: 150px;
  }
}

</style>

