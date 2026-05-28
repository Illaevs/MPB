<template>
  <div class="reviews-view p-3 d-flex flex-column h-100">
    <div class="list-card flex-grow-1 d-flex flex-column overflow-hidden">
    <!-- Single-line toolbar: title + counters + filters + view toggle + refresh -->
    <div class="list-card__toolbar toolbar-card flex-shrink-0">
      <div class="toolbar-row">
        <div class="toolbar-brand">
          <h2 class="m-0 toolbar-title">Согласования РР</h2>
          <Tooltip
            v-if="pendingCount"
            :text="`На рассмотрении: ${pendingCount}${overdueCount ? ` · просрочено: ${overdueCount}` : ''}\nВсего загружено: ${results.length}${totalServerCount !== null ? ` из ${totalServerCount}` : ''}`"
          >
            <span class="counter-pill" :class="{ 'has-overdue': overdueCount > 0 }" @click="overdueCount && setStaleQuickFilter('overdue')" role="button">
              <span class="counter-pending">{{ pendingCount }} ждут</span>
              <span v-if="overdueCount" class="counter-overdue">
                <i class="fas fa-clock"></i>{{ overdueCount }} просрочено
              </span>
            </span>
          </Tooltip>
        </div>

        <div class="toolbar-filters">
          <div class="form-group toolbar-search">
            <input v-model="filters.search" type="text" class="form-control form-control-sm" placeholder="🔍 Поиск по товару / сделке / этапу...">
          </div>
          <div class="form-group toolbar-select">
            <select v-model="filters.deal_id" class="form-control form-control-sm" @change="onDealChange">
              <option value="">Все сделки</option>
              <option v-for="deal in availableDeals" :key="deal.id" :value="deal.id">{{ deal.title }}</option>
            </select>
          </div>
          <div class="form-group toolbar-select">
            <select v-model="filters.product_name" class="form-control form-control-sm" @change="loadResults(true)">
              <option value="">Все товары</option>
              <option v-for="name in availableProducts" :key="name" :value="name">{{ name }}</option>
            </select>
          </div>
          <div class="form-group toolbar-select">
            <UiChipFilter
              v-model="filters.status"
              :options="RR_STATUS_OPTIONS"
              placeholder="Все статусы"
              empty-icon="fas fa-circle-half-stroke"
              @update:model-value="loadResults(true)"
            />
          </div>
          <div class="form-group toolbar-select">
            <UiChipFilter
              v-model="filters.staleness"
              :options="RR_STALENESS_OPTIONS"
              placeholder="Любой возраст"
              empty-icon="fas fa-clock"
            />
          </div>
          <button v-if="hasActiveFilters" class="btn btn-sm btn-icon" @click="resetFilters" title="Сбросить фильтры">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div class="toolbar-actions">
          <div class="view-toggle" role="tablist">
            <button class="view-btn" :class="{ active: viewMode === 'list' }" @click="viewMode = 'list'" title="Список">
              <i class="fas fa-list"></i>
            </button>
            <button class="view-btn" :class="{ active: viewMode === 'grouped' }" @click="viewMode = 'grouped'" title="По сделкам">
              <i class="fas fa-layer-group"></i>
            </button>
          </div>
          <button class="btn btn-sm btn-outline-primary" @click="loadResults(true)" title="Обновить">
            <i class="fas fa-sync"></i>
            <span class="hide-md">Обновить</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Floating bulk action bar (does not push layout) -->
    <transition name="bulk-bar">
      <div v-if="selectedIds.size > 0 && canEdit" class="bulk-bar bulk-bar-floating">
        <div class="bulk-info">
          <i class="fas fa-check-square"></i>
          <span>Выбрано: <b>{{ selectedIds.size }}</b></span>
          <span v-if="selectedReviewable < selectedIds.size" class="text-muted small">
            (на согласовании: {{ selectedReviewable }})
          </span>
        </div>
        <div class="bulk-actions">
          <button class="btn btn-sm btn-success" :disabled="!selectedReviewable || bulkBusy" @click="bulkApprove">
            <i class="fas fa-check mr-1"></i> Согласовать {{ selectedReviewable }}
          </button>
          <button class="btn btn-sm btn-danger" :disabled="!selectedReviewable || bulkBusy" @click="openBulkReject">
            <i class="fas fa-times mr-1"></i> Отклонить {{ selectedReviewable }}
          </button>
          <button class="btn btn-sm btn-outline-secondary" @click="clearSelection">
            Снять выбор
          </button>
        </div>
      </div>
    </transition>

    <!-- Content area -->
    <div class="list-card__body flex-grow-1 overflow-hidden d-flex flex-column">
      <div v-if="loading && !results.length" class="p-3 d-flex flex-column gap-2">
        <SkeletonLoader height="42px" v-for="i in 6" :key="i" />
      </div>
      <div v-else-if="!filteredResults.length" class="empty-state">
        <i class="fas fa-clipboard-check"></i>
        <p>Нет результатов на согласование</p>
        <small class="text-muted">{{ hasActiveFilters ? 'Попробуйте сбросить фильтры' : 'Результаты появятся после загрузки исполнителем в панели исполнителя' }}</small>
        <button v-if="hasActiveFilters" class="btn btn-sm btn-outline-primary mt-2" @click="resetFilters">
          Сбросить фильтры
        </button>
      </div>

      <!-- LIST VIEW -->
      <div v-else-if="viewMode === 'list'" class="flex-grow-1 overflow-auto">
        <table class="table table-hover m-0">
          <thead>
            <tr>
              <th class="check-col" v-if="canEdit">
                <input
                  type="checkbox"
                  :checked="allVisibleSelected"
                  :indeterminate.prop="someVisibleSelected && !allVisibleSelected"
                  @change="toggleAllVisible"
                />
              </th>
              <th>Сделка</th>
              <th>Этап</th>
              <th>Товар</th>
              <th>Версия</th>
              <th>Статус</th>
              <th>Возраст</th>
              <th>Исполнитель</th>
              <th>Комментарий исполнителя</th>
              <th>Комментарий ГИП</th>
              <th class="text-right">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in pagedResults" :key="item.id" :class="{ selected: selectedIds.has(item.id) }">
              <td v-if="canEdit" class="check-col">
                <input type="checkbox" :checked="selectedIds.has(item.id)" @change="toggleSelected(item.id)" />
              </td>
              <td class="fw-500">{{ item.deal_title || '-' }}</td>
              <td>{{ item.stage_name || '-' }}</td>
              <td>{{ item.product_name }}</td>
              <td>
                <button class="version-chip" @click="openVersions(item)" :title="`История версий ${item.product_name}`">
                  {{ versionText(item) }}
                  <i class="fas fa-history"></i>
                </button>
              </td>
              <td>
                <span class="badge" :class="statusClass(item.status)">
                  {{ statusText(item.status) }}
                </span>
              </td>
              <td>
                <Tooltip :text="ageTooltip(item)">
                  <span class="age-cell" :class="`age-${stalenessKind(item)}`">
                    <span class="age-dot"></span>
                    {{ ageText(item) }}
                  </span>
                </Tooltip>
              </td>
              <td class="text-muted small">{{ item.created_by || '-' }}</td>
              <td class="comment-cell">
                <Tooltip v-if="item.executor_comment" :max-width="380">
                  <span class="cmt-inline cmt-inline-exec">
                    <span class="user-avatar" :class="`avatar-${avatarColor(item.created_by)}`">
                      <img v-if="item.executor_avatar_url" :src="resolveAvatar(item.executor_avatar_url, item.executor_user_id)" alt="">
                      <span v-else>{{ initials(item.created_by) }}</span>
                    </span>
                    <span class="cmt-text">{{ truncate(item.executor_comment, 32) }}</span>
                  </span>
                  <template #content>
                    <div class="tt-cmt">
                      <div class="tt-cmt-head">{{ item.created_by || 'Исполнитель' }}</div>
                      <div class="tt-cmt-body">{{ item.executor_comment }}</div>
                    </div>
                  </template>
                </Tooltip>
                <span v-else class="text-muted">—</span>
              </td>
              <td class="comment-cell">
                <Tooltip v-if="item.reviewer_comment" :max-width="380">
                  <span class="cmt-inline cmt-inline-rev">
                    <span class="user-avatar" :class="`avatar-${avatarColor(item.reviewer_name)}`">
                      <img v-if="item.reviewer_avatar_url" :src="resolveAvatar(item.reviewer_avatar_url, item.reviewer_id)" alt="">
                      <span v-else>{{ initials(item.reviewer_name) }}</span>
                    </span>
                    <span class="cmt-text">{{ truncate(item.reviewer_comment, 32) }}</span>
                  </span>
                  <template #content>
                    <div class="tt-cmt">
                      <div class="tt-cmt-head">{{ item.reviewer_name || 'ГИП' }}<span v-if="item.reviewed_at" class="text-muted small ml-2">{{ formatDateTime(item.reviewed_at) }}</span></div>
                      <div class="tt-cmt-body">{{ item.reviewer_comment }}</div>
                    </div>
                  </template>
                </Tooltip>
                <span v-else class="text-muted">—</span>
              </td>
              <td class="text-right">
                <div class="d-flex justify-end gap-1">
                  <button v-if="item.public_url" class="btn btn-sm btn-icon" @click="openResult(item)" title="Открыть файл">
                    <i class="fas fa-external-link-alt"></i>
                  </button>
                  <button v-if="canEdit && item.status === 'review'" class="btn btn-sm btn-icon btn-quick-approve" @click="quickApprove(item)" title="Согласовать">
                    <i class="fas fa-check"></i>
                  </button>
                  <button v-if="canEdit" class="btn btn-sm btn-icon" @click="openReviewModal(item)" title="Редактировать решение">
                    <i class="fas fa-edit"></i>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="canLoadMoreVisible" class="load-more-row">
          <button class="btn btn-sm btn-outline-primary" @click="loadMoreVisible">
            Показать ещё {{ Math.min(VISIBLE_PAGE, filteredResults.length - visibleCount) }}
            <span class="text-muted small ml-1">/ {{ filteredResults.length }}</span>
          </button>
        </div>
        <div v-if="canLoadMoreServer" class="load-more-row">
          <button class="btn btn-sm btn-outline-secondary" :disabled="loading" @click="loadMoreFromServer">
            <i v-if="loading" class="fas fa-spinner fa-spin mr-1"></i>
            Загрузить ещё с сервера ({{ totalServerCount - results.length }} осталось)
          </button>
        </div>
      </div>

      <!-- GROUPED VIEW -->
      <div v-else class="flex-grow-1 overflow-auto p-2">
        <div v-for="group in groupedResults" :key="group.deal_id || 'no-deal'" class="deal-group">
          <div class="deal-group-header" @click="toggleGroup(group.deal_id)">
            <i class="fas fa-chevron-right group-chevron" :class="{ open: !isGroupCollapsed(group.deal_id) }"></i>
            <span class="deal-group-title">{{ group.deal_title || 'Без сделки' }}</span>
            <span class="deal-group-meta text-muted small">{{ group.items.length }} рез.</span>
            <div class="deal-group-stats">
              <span v-if="group.stats.review" class="badge badge-info">{{ group.stats.review }} ждут</span>
              <span v-if="group.stats.approved" class="badge badge-success">{{ group.stats.approved }} ✓</span>
              <span v-if="group.stats.rejected" class="badge badge-danger">{{ group.stats.rejected }} ✗</span>
              <span v-if="group.stats.send_back" class="badge badge-warning">{{ group.stats.send_back }} →</span>
            </div>
            <input
              v-if="canEdit"
              type="checkbox"
              class="group-select"
              :checked="isGroupAllSelected(group)"
              :indeterminate.prop="isGroupSomeSelected(group) && !isGroupAllSelected(group)"
              @click.stop
              @change="toggleGroupSelection(group)"
              :title="'Выбрать все из сделки'"
            />
          </div>
          <transition name="collapse">
            <div v-if="!isGroupCollapsed(group.deal_id)" class="deal-group-body">
              <div v-for="item in group.items" :key="item.id" class="grp-row" :class="{ selected: selectedIds.has(item.id) }">
                <input
                  v-if="canEdit"
                  type="checkbox"
                  :checked="selectedIds.has(item.id)"
                  @change="toggleSelected(item.id)"
                />
                <div class="grp-row-main">
                  <div class="grp-row-title">
                    <span class="fw-500">{{ item.product_name }}</span>
                    <span class="text-muted small">· {{ item.stage_name || '—' }}</span>
                    <button class="version-chip sm" @click="openVersions(item)">
                      {{ versionText(item) }}
                      <i class="fas fa-history"></i>
                    </button>
                  </div>
                  <div class="grp-row-meta">
                    <span class="badge" :class="statusClass(item.status)">{{ statusText(item.status) }}</span>
                    <Tooltip :text="ageTooltip(item)">
                      <span class="age-cell" :class="`age-${stalenessKind(item)}`">
                        <span class="age-dot"></span>{{ ageText(item) }}
                      </span>
                    </Tooltip>
                    <span class="text-muted small" v-if="item.created_by">· {{ item.created_by }}</span>
                  </div>
                  <div v-if="item.executor_comment || item.reviewer_comment" class="grp-row-comments">
                    <div v-if="item.executor_comment" class="cmt cmt-exec">
                      <span class="user-avatar sm" :class="`avatar-${avatarColor(item.created_by)}`">
                        <img v-if="item.executor_avatar_url" :src="resolveAvatar(item.executor_avatar_url, item.executor_user_id)" alt="">
                        <span v-else>{{ initials(item.created_by) }}</span>
                      </span>
                      <div class="cmt-body">
                        <div class="cmt-head"><b>{{ item.created_by || 'Исполнитель' }}</b></div>
                        <div>{{ item.executor_comment }}</div>
                      </div>
                    </div>
                    <div v-if="item.reviewer_comment" class="cmt cmt-rev">
                      <span class="user-avatar sm" :class="`avatar-${avatarColor(item.reviewer_name)}`">
                        <img v-if="item.reviewer_avatar_url" :src="resolveAvatar(item.reviewer_avatar_url, item.reviewer_id)" alt="">
                        <span v-else>{{ initials(item.reviewer_name) }}</span>
                      </span>
                      <div class="cmt-body">
                        <div class="cmt-head">
                          <b>{{ item.reviewer_name || 'ГИП' }}</b>
                          <span v-if="item.reviewed_at" class="text-muted small ml-2">· {{ formatDateTime(item.reviewed_at) }}</span>
                        </div>
                        <div>{{ item.reviewer_comment }}</div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="grp-row-actions">
                  <button v-if="item.public_url" class="btn btn-sm btn-icon" @click="openResult(item)" title="Открыть файл">
                    <i class="fas fa-external-link-alt"></i>
                  </button>
                  <button v-if="canEdit && item.status === 'review'" class="btn btn-sm btn-icon btn-quick-approve" @click="quickApprove(item)" title="Согласовать">
                    <i class="fas fa-check"></i>
                  </button>
                  <button v-if="canEdit" class="btn btn-sm btn-icon" @click="openReviewModal(item)" title="Редактировать решение">
                    <i class="fas fa-edit"></i>
                  </button>
                </div>
              </div>
            </div>
          </transition>
        </div>
        <div v-if="canLoadMoreServer" class="load-more-row">
          <button class="btn btn-sm btn-outline-secondary" :disabled="loading" @click="loadMoreFromServer">
            <i v-if="loading" class="fas fa-spinner fa-spin mr-1"></i>
            Загрузить ещё с сервера ({{ totalServerCount - results.length }} осталось)
          </button>
        </div>
      </div>
    </div>
    </div>

    <!-- Review Modal -->
    <div v-if="showReviewModal" class="modal-overlay" v-modal-close="closeReviewModal">
      <div class="modal-content" @click.stop style="max-width: 520px;">
        <div class="modal-header">
          <h4>Согласование результата</h4>
          <button class="btn-close" @click="closeReviewModal"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="mb-3 d-flex align-center gap-2">
            <span class="badge" :class="statusClass(reviewTarget?.status)">
              {{ statusText(reviewTarget?.status) }}
            </span>
            <span class="text-muted small">{{ reviewTarget?.deal_title || '-' }} · {{ reviewTarget?.stage_name || '-' }}</span>
          </div>
          <div class="mb-2 fw-500">{{ reviewTarget?.product_name }}</div>
          <div class="form-group mb-3">
            <label>Новый статус</label>
            <select v-model="reviewForm.status" class="form-control">
              <option value="review">На рассмотрении</option>
              <option value="approved">Согласовано</option>
              <option value="rejected">Отклонено</option>
              <option value="send_back">На отправку с замечаниями</option>
            </select>
          </div>
          <div class="form-group">
            <label>Комментарий ГИП</label>
            <textarea v-model="reviewForm.reviewer_comment" class="form-control" rows="4" placeholder="Комментарий обязателен при отклонении"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeReviewModal">Отмена</button>
          <button class="btn btn-primary" :disabled="savingReview" @click="saveReview">
            <i v-if="savingReview" class="fas fa-spinner fa-spin mr-1"></i> Сохранить
          </button>
        </div>
      </div>
    </div>

    <!-- Bulk Reject Modal -->
    <div v-if="showBulkRejectModal" class="modal-overlay" v-modal-close="closeBulkReject">
      <div class="modal-content" @click.stop style="max-width: 480px;">
        <div class="modal-header">
          <h4>Отклонить {{ selectedReviewable }} результата</h4>
          <button class="btn-close" @click="closeBulkReject"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="form-group mb-3">
            <label>Тип отказа</label>
            <select v-model="bulkRejectForm.status" class="form-control">
              <option value="rejected">Отклонено</option>
              <option value="send_back">На отправку с замечаниями</option>
            </select>
          </div>
          <div class="form-group">
            <label>Комментарий (применится ко всем) <span class="text-danger">*</span></label>
            <textarea v-model="bulkRejectForm.comment" class="form-control" rows="4" placeholder="Опишите общую причину..."></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeBulkReject">Отмена</button>
          <button class="btn btn-danger" :disabled="bulkBusy || !bulkRejectForm.comment.trim()" @click="bulkReject">
            <i v-if="bulkBusy" class="fas fa-spinner fa-spin mr-1"></i>
            Применить
          </button>
        </div>
      </div>
    </div>

    <!-- Versions Drawer -->
    <transition name="drawer">
      <div v-if="versionsOpen" class="drawer-overlay" v-modal-close="closeVersions">
        <div class="drawer">
          <div class="drawer-header">
            <div>
              <h4 class="m-0">История версий</h4>
              <div class="text-muted small">{{ versionsContext.product_name }} · {{ versionsContext.stage_name || '—' }}</div>
            </div>
            <button class="btn-close" @click="closeVersions"><i class="fas fa-times"></i></button>
          </div>
          <div v-if="versionsLoading" class="p-3 d-flex flex-column gap-2">
            <SkeletonLoader height="64px" v-for="i in 4" :key="i" />
          </div>
          <div v-else-if="!versionsList.length" class="empty-state p-4">
            <i class="fas fa-history"></i>
            <p>Нет данных</p>
          </div>
          <div v-else class="drawer-body">
            <div v-for="(v, idx) in versionsList" :key="v.id" class="ver-card" :class="{ current: idx === 0 }">
              <div class="ver-card-head">
                <span class="version-chip">{{ versionText(v) }}</span>
                <span class="badge" :class="statusClass(v.status)">{{ statusText(v.status) }}</span>
                <span class="text-muted small ml-auto">{{ formatDateTime(v.created_at) }}</span>
              </div>
              <div class="ver-card-row text-muted small">
                <i class="fas fa-user mr-1"></i>{{ v.created_by || '—' }}
                <span v-if="v.reviewed_at" class="ml-3">
                  <i class="fas fa-user-tie mr-1"></i>проверено {{ formatDateTime(v.reviewed_at) }}
                </span>
              </div>
              <div v-if="v.executor_comment" class="ver-cmt"><b>Исполнитель:</b> {{ v.executor_comment }}</div>
              <div v-if="v.reviewer_comment" class="ver-cmt"><b>ГИП:</b> {{ v.reviewer_comment }}</div>
              <div class="ver-card-actions">
                <button v-if="v.public_url" class="btn btn-sm btn-outline-primary" @click="openResult(v)">
                  <i class="fas fa-external-link-alt mr-1"></i> Открыть файл
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '@/services/api'
import { openTrustedExternalUrl } from '../utils/download'
import SkeletonLoader from '../components/ui/SkeletonLoader.vue'
import Tooltip from '../components/ui/Tooltip.vue'
import UiChipFilter from '../components/ui/UiChipFilter.vue'
import { getActiveUser, getStoredPermissions } from '../utils/permissions'
import { normalizeAvatarUrl } from '../utils/avatar'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'

const PAGE_LIMIT = 100
const VISIBLE_PAGE = 50

const RR_STATUS_OPTIONS = [
  { value: 'review',    label: 'На рассмотрении',         color: '#0ea5e9' },
  { value: 'approved',  label: 'Согласовано',             color: '#22c55e' },
  { value: 'rejected',  label: 'Отклонено',               color: '#ef4444' },
  { value: 'send_back', label: 'На отправку с замечаниями', color: '#f59e0b' },
]

const RR_STALENESS_OPTIONS = [
  { value: 'fresh',   label: '< 1 дн.',  color: '#22c55e' },
  { value: 'hanging', label: '1–3 дн.',  color: '#3b82f6' },
  { value: 'warning', label: '3–7 дн.',  color: '#f59e0b' },
  { value: 'overdue', label: '> 7 дн.',  color: '#ef4444' },
]

export default {
  name: 'WorkResultsReviews',
  components: { SkeletonLoader, Tooltip, UiChipFilter },
  setup() {
    const results = ref([])
    const totalServerCount = ref(null)
    const loading = ref(false)
    const filters = ref({ deal_id: '', product_name: '', status: '', search: '', staleness: '' })
    const showReviewModal = ref(false)
    const reviewTarget = ref(null)
    const reviewForm = ref({ status: 'review', reviewer_comment: '' })
    const savingReview = ref(false)
    const viewMode = ref(localStorage.getItem('rr-view') || 'list')
    const collapsedGroups = ref(new Set())
    const visibleCount = ref(VISIBLE_PAGE)

    const selectedIds = ref(new Set())
    const showBulkRejectModal = ref(false)
    const bulkRejectForm = ref({ status: 'rejected', comment: '' })
    const bulkBusy = ref(false)

    const versionsOpen = ref(false)
    const versionsLoading = ref(false)
    const versionsList = ref([])
    const versionsContext = ref({ product_name: '', stage_name: '' })

    const toast = useToast()
    const { confirm } = useConfirm()

    const activeUser = ref(getActiveUser())
    const permissions = getStoredPermissions() || {}
    const sectionPerm = permissions.work_results_reviews || {}
    const isSuper = !!permissions.__superuser__?.read_all
    const canEdit = isSuper || !!(sectionPerm.read_all || sectionPerm.read_assigned)

    watch(viewMode, (v) => localStorage.setItem('rr-view', v))

    const hasActiveFilters = computed(() =>
      !!(filters.value.deal_id || filters.value.product_name || filters.value.status || filters.value.search || filters.value.staleness)
    )

    const filteredResults = computed(() => {
      const q = (filters.value.search || '').toLowerCase().trim()
      const stale = filters.value.staleness
      return results.value.filter(item => {
        if (q) {
          const hay = `${item.product_name || ''} ${item.deal_title || ''} ${item.stage_name || ''} ${item.created_by || ''}`.toLowerCase()
          if (!hay.includes(q)) return false
        }
        if (stale && stalenessKind(item) !== stale) return false
        return true
      })
    })

    const pagedResults = computed(() => filteredResults.value.slice(0, visibleCount.value))

    const canLoadMoreVisible = computed(() => visibleCount.value < filteredResults.value.length)
    const canLoadMoreServer = computed(() =>
      totalServerCount.value !== null && results.value.length < totalServerCount.value
    )

    const loadMoreVisible = () => {
      visibleCount.value = Math.min(visibleCount.value + VISIBLE_PAGE, filteredResults.value.length)
    }

    watch(filteredResults, () => {
      if (visibleCount.value > VISIBLE_PAGE) visibleCount.value = VISIBLE_PAGE
    })

    const pendingCount = computed(() =>
      results.value.filter(i => (i.status || 'review') === 'review').length
    )
    const overdueCount = computed(() =>
      results.value.filter(i => (i.status || 'review') === 'review' && stalenessKind(i) === 'overdue').length
    )

    const availableDeals = computed(() => {
      const map = new Map()
      results.value.forEach((item) => {
        if (item.deal_id && item.deal_title && !map.has(item.deal_id)) {
          map.set(item.deal_id, { id: item.deal_id, title: item.deal_title })
        }
      })
      return Array.from(map.values())
    })

    const availableProducts = computed(() => {
      const items = filters.value.deal_id
        ? results.value.filter((item) => item.deal_id === filters.value.deal_id)
        : results.value
      return Array.from(new Set(items.map((item) => item.product_name))).sort()
    })

    const groupedResults = computed(() => {
      const map = new Map()
      filteredResults.value.forEach((item) => {
        const key = item.deal_id || 'no-deal'
        if (!map.has(key)) {
          map.set(key, {
            deal_id: item.deal_id,
            deal_title: item.deal_title,
            items: [],
            stats: { review: 0, approved: 0, rejected: 0, send_back: 0 }
          })
        }
        const group = map.get(key)
        group.items.push(item)
        const st = item.status || 'review'
        if (group.stats[st] !== undefined) group.stats[st] += 1
      })
      return Array.from(map.values()).sort((a, b) => (b.stats.review - a.stats.review))
    })

    const loadResults = async (reset = true) => {
      loading.value = true
      try {
        const params = { limit: PAGE_LIMIT, offset: reset ? 0 : results.value.length }
        if (filters.value.deal_id) params.deal_id = filters.value.deal_id
        if (filters.value.product_name) params.product_name = filters.value.product_name
        if (filters.value.status) params.status = filters.value.status
        if (!isSuper && !sectionPerm.read_all && sectionPerm.read_assigned && activeUser.value?.id) {
          params.only_assigned = true
          params.gip_user_id = activeUser.value.id
        }
        const response = await api.workResults.list(params)
        const data = response || {}
        const items = Array.isArray(data) ? data : (data.items || [])
        const total = Array.isArray(data) ? items.length : (data.total ?? items.length)
        if (reset) {
          results.value = items
          selectedIds.value = new Set()
          visibleCount.value = VISIBLE_PAGE
        } else {
          results.value = [...results.value, ...items]
        }
        totalServerCount.value = total
      } catch (error) {
        console.error('Error loading reviews:', error)
        toast.error('Не удалось загрузить согласования')
        if (reset) results.value = []
      } finally {
        loading.value = false
      }
    }

    const loadMoreFromServer = () => loadResults(false)

    const onDealChange = () => {
      filters.value.product_name = ''
      loadResults(true)
    }

    const resetFilters = () => {
      filters.value = { deal_id: '', product_name: '', status: '', search: '', staleness: '' }
      loadResults(true)
    }

    const setStaleQuickFilter = (kind) => {
      filters.value.staleness = filters.value.staleness === kind ? '' : kind
    }

    const initials = (name) => {
      if (!name) return '?'
      const parts = String(name).trim().split(/\s+/).filter(Boolean)
      if (!parts.length) return '?'
      if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
      return (parts[0][0] + parts[1][0]).toUpperCase()
    }

    const avatarColor = (name) => {
      const palette = ['blue', 'teal', 'amber', 'pink', 'purple', 'green', 'red', 'indigo']
      if (!name) return palette[0]
      let hash = 0
      const s = String(name)
      for (let i = 0; i < s.length; i += 1) hash = (hash * 31 + s.charCodeAt(i)) | 0
      return palette[Math.abs(hash) % palette.length]
    }

    const resolveAvatar = (url, userId) => normalizeAvatarUrl(url, userId)

    const truncate = (text, length) => {
      if (!text) return '-'
      if (text.length <= length) return text
      return text.substring(0, length) + '...'
    }

    const versionText = (item) => {
      const number = item.version_number || parseInt(String(item.version_label || '').replace(/\D/g, ''), 10)
      return number ? `v.${number}` : (item.version_label || '-')
    }

    const statusText = (status) => {
      const value = status || 'review'
      if (value === 'approved') return 'Согласовано'
      if (value === 'rejected') return 'Отклонено'
      if (value === 'send_back') return 'На отправку'
      return 'На рассмотрении'
    }

    const statusClass = (status) => {
      const value = status || 'review'
      if (value === 'approved') return 'badge-success'
      if (value === 'rejected') return 'badge-danger'
      if (value === 'send_back') return 'badge-warning'
      return 'badge-info'
    }

    const daysSince = (item) => {
      if (!item?.created_at) return null
      const created = new Date(item.created_at)
      if (Number.isNaN(created.getTime())) return null
      return (Date.now() - created.getTime()) / (1000 * 60 * 60 * 24)
    }

    const stalenessKind = (item) => {
      const status = item?.status || 'review'
      const days = daysSince(item)
      if (days === null) return 'none'
      if (status !== 'review') return 'final'
      if (days < 1) return 'fresh'
      if (days < 3) return 'hanging'
      if (days < 7) return 'warning'
      return 'overdue'
    }

    const ageText = (item) => {
      const days = daysSince(item)
      if (days === null) return '—'
      if (days < 1 / 24) return 'только что'
      if (days < 1) return `${Math.max(1, Math.round(days * 24))} ч.`
      if (days < 30) return `${Math.round(days)} дн.`
      if (days < 365) return `${Math.round(days / 30)} мес.`
      return `${Math.round(days / 365)} г.`
    }

    const ageTooltip = (item) => {
      const status = item?.status || 'review'
      const created = item?.created_at ? formatDateTime(item.created_at) : '—'
      const reviewed = item?.reviewed_at ? formatDateTime(item.reviewed_at) : null
      let line2 = ''
      if (status === 'review') {
        const k = stalenessKind(item)
        if (k === 'overdue') line2 = '\nПросрочено (>7 дн.) — требует срочного внимания'
        else if (k === 'warning') line2 = '\nЗалежалось (3–7 дн.)'
        else if (k === 'hanging') line2 = '\nВисит 1–3 дня'
      } else if (reviewed) {
        line2 = `\nРешение: ${formatDateTime(reviewed)}`
      }
      return `Загружено: ${created}${line2}`
    }

    const formatDateTime = (val) => {
      if (!val) return '—'
      const d = new Date(val)
      if (Number.isNaN(d.getTime())) return String(val)
      return d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
    }

    const openReviewModal = (item) => {
      reviewTarget.value = item
      reviewForm.value = {
        status: item.status || 'review',
        reviewer_comment: item.reviewer_comment || ''
      }
      showReviewModal.value = true
    }

    const closeReviewModal = () => {
      showReviewModal.value = false
      reviewTarget.value = null
      reviewForm.value = { status: 'review', reviewer_comment: '' }
    }

    const patchOptimistic = async (item, updates, requestPayload) => {
      const idx = results.value.findIndex(r => r.id === item.id)
      if (idx === -1) return false
      const prev = { ...results.value[idx] }
      results.value[idx] = { ...prev, ...updates }
      try {
        await api.workResults.patchReview(item.id, requestPayload)
        return true
      } catch (error) {
        results.value[idx] = prev
        const msg = error.response?.data?.detail || 'Ошибка сохранения'
        toast.error(msg)
        return false
      }
    }

    const saveReview = async () => {
      if (!reviewTarget.value) return
      if (['rejected', 'send_back'].includes(reviewForm.value.status) && !reviewForm.value.reviewer_comment.trim()) {
        toast.warning('Комментарий обязателен при отклонении')
        return
      }
      savingReview.value = true
      const item = reviewTarget.value
      const updates = {
        status: reviewForm.value.status,
        reviewer_comment: reviewForm.value.reviewer_comment,
        reviewed_at: new Date().toISOString(),
        reviewer_id: activeUser.value?.id || item.reviewer_id
      }
      const ok = await patchOptimistic(item, updates, {
        status: reviewForm.value.status,
        reviewer_comment: reviewForm.value.reviewer_comment,
        reviewer_id: activeUser.value?.id || null
      })
      savingReview.value = false
      if (ok) {
        toast.success('Решение сохранено')
        closeReviewModal()
      }
    }

    const quickApprove = async (item) => {
      const ok = await confirm({
        title: 'Согласовать результат?',
        message: `${item.product_name}\n${item.deal_title || ''}`,
        confirmText: 'Согласовать',
        variant: 'primary'
      })
      if (!ok) return
      const updated = await patchOptimistic(
        item,
        { status: 'approved', reviewed_at: new Date().toISOString(), reviewer_id: activeUser.value?.id || item.reviewer_id },
        { status: 'approved', reviewer_id: activeUser.value?.id || null }
      )
      if (updated) toast.success(`Согласовано: ${item.product_name}`)
    }

    const openResult = (item) => {
      const url = item?.public_url || item?.download_url || item?.url || item?.file_url
      if (url) openTrustedExternalUrl(url)
      else toast.warning('У результата нет доступной ссылки')
    }

    // Selection
    const toggleSelected = (id) => {
      const set = new Set(selectedIds.value)
      if (set.has(id)) set.delete(id)
      else set.add(id)
      selectedIds.value = set
    }

    const clearSelection = () => { selectedIds.value = new Set() }

    const allVisibleSelected = computed(() => {
      if (!pagedResults.value.length) return false
      return pagedResults.value.every(i => selectedIds.value.has(i.id))
    })
    const someVisibleSelected = computed(() => pagedResults.value.some(i => selectedIds.value.has(i.id)))

    const toggleAllVisible = () => {
      const set = new Set(selectedIds.value)
      if (allVisibleSelected.value) {
        pagedResults.value.forEach(i => set.delete(i.id))
      } else {
        pagedResults.value.forEach(i => set.add(i.id))
      }
      selectedIds.value = set
    }

    const isGroupAllSelected = (group) =>
      group.items.length > 0 && group.items.every(i => selectedIds.value.has(i.id))
    const isGroupSomeSelected = (group) =>
      group.items.some(i => selectedIds.value.has(i.id))

    const toggleGroupSelection = (group) => {
      const set = new Set(selectedIds.value)
      if (isGroupAllSelected(group)) group.items.forEach(i => set.delete(i.id))
      else group.items.forEach(i => set.add(i.id))
      selectedIds.value = set
    }

    const selectedReviewable = computed(() =>
      results.value.filter(i => selectedIds.value.has(i.id) && (i.status || 'review') === 'review').length
    )

    // Bulk
    const bulkApprove = async () => {
      const ids = results.value
        .filter(i => selectedIds.value.has(i.id) && (i.status || 'review') === 'review')
        .map(i => i.id)
      if (!ids.length) return
      const ok = await confirm({
        title: `Согласовать ${ids.length} результата(ов)?`,
        message: 'Действие применится ко всем выбранным записям со статусом «На рассмотрении».',
        confirmText: 'Согласовать',
        variant: 'primary'
      })
      if (!ok) return
      bulkBusy.value = true
      const reviewerId = activeUser.value?.id || null
      const reviewedAt = new Date().toISOString()
      const original = new Map()
      ids.forEach(id => {
        const idx = results.value.findIndex(r => r.id === id)
        if (idx !== -1) {
          original.set(id, { ...results.value[idx] })
          results.value[idx] = {
            ...results.value[idx],
            status: 'approved',
            reviewed_at: reviewedAt,
            reviewer_id: reviewerId
          }
        }
      })
      const settle = await Promise.allSettled(ids.map(id =>
        api.workResults.patchReview(id, { status: 'approved', reviewer_id: reviewerId })
      ))
      let failed = 0
      settle.forEach((res, i) => {
        if (res.status === 'rejected') {
          failed += 1
          const id = ids[i]
          const idx = results.value.findIndex(r => r.id === id)
          if (idx !== -1) results.value[idx] = original.get(id)
        }
      })
      bulkBusy.value = false
      clearSelection()
      if (failed === 0) toast.success(`Согласовано: ${ids.length}`)
      else if (failed < ids.length) toast.warning(`Готово: ${ids.length - failed}, ошибок: ${failed}`)
      else toast.error('Не удалось согласовать выбранные')
    }

    const openBulkReject = () => {
      bulkRejectForm.value = { status: 'rejected', comment: '' }
      showBulkRejectModal.value = true
    }
    const closeBulkReject = () => { showBulkRejectModal.value = false }

    const bulkReject = async () => {
      const comment = bulkRejectForm.value.comment.trim()
      if (!comment) { toast.warning('Введите комментарий'); return }
      const ids = results.value
        .filter(i => selectedIds.value.has(i.id) && (i.status || 'review') === 'review')
        .map(i => i.id)
      if (!ids.length) return
      bulkBusy.value = true
      const status = bulkRejectForm.value.status
      const reviewerId = activeUser.value?.id || null
      const reviewedAt = new Date().toISOString()
      const original = new Map()
      ids.forEach(id => {
        const idx = results.value.findIndex(r => r.id === id)
        if (idx !== -1) {
          original.set(id, { ...results.value[idx] })
          results.value[idx] = {
            ...results.value[idx],
            status,
            reviewer_comment: comment,
            reviewed_at: reviewedAt,
            reviewer_id: reviewerId
          }
        }
      })
      const settle = await Promise.allSettled(ids.map(id =>
        api.workResults.patchReview(id, { status, reviewer_comment: comment, reviewer_id: reviewerId })
      ))
      let failed = 0
      settle.forEach((res, i) => {
        if (res.status === 'rejected') {
          failed += 1
          const id = ids[i]
          const idx = results.value.findIndex(r => r.id === id)
          if (idx !== -1) results.value[idx] = original.get(id)
        }
      })
      bulkBusy.value = false
      clearSelection()
      closeBulkReject()
      if (failed === 0) toast.success(`Применено к ${ids.length} результатам`)
      else if (failed < ids.length) toast.warning(`Готово: ${ids.length - failed}, ошибок: ${failed}`)
      else toast.error('Не удалось применить')
    }

    // Groups collapse
    const isGroupCollapsed = (deal_id) => collapsedGroups.value.has(deal_id || 'no-deal')
    const toggleGroup = (deal_id) => {
      const set = new Set(collapsedGroups.value)
      const key = deal_id || 'no-deal'
      if (set.has(key)) set.delete(key)
      else set.add(key)
      collapsedGroups.value = set
    }

    // Versions
    const openVersions = async (item) => {
      versionsContext.value = { product_name: item.product_name, stage_name: item.stage_name, stage_id: item.stage_id }
      versionsOpen.value = true
      versionsLoading.value = true
      versionsList.value = []
      try {
        const response = await api.workResults.listVersions({
          stage_id: item.stage_id,
          product_name: item.product_name
        })
        versionsList.value = response || []
      } catch (error) {
        console.error('Error loading versions:', error)
        toast.error('Не удалось загрузить историю версий')
      } finally {
        versionsLoading.value = false
      }
    }
    const closeVersions = () => { versionsOpen.value = false }

    onMounted(() => loadResults(true))

    return {
      VISIBLE_PAGE,
      RR_STATUS_OPTIONS,
      RR_STALENESS_OPTIONS,
      results,
      totalServerCount,
      loading,
      filters,
      hasActiveFilters,
      filteredResults,
      pagedResults,
      pendingCount,
      overdueCount,
      availableDeals,
      availableProducts,
      groupedResults,
      viewMode,
      visibleCount,
      canLoadMoreVisible,
      canLoadMoreServer,
      loadResults,
      loadMoreVisible,
      loadMoreFromServer,
      onDealChange,
      resetFilters,
      setStaleQuickFilter,
      truncate,
      initials,
      avatarColor,
      resolveAvatar,
      versionText,
      statusText,
      statusClass,
      stalenessKind,
      ageText,
      ageTooltip,
      formatDateTime,
      openReviewModal,
      closeReviewModal,
      saveReview,
      quickApprove,
      showReviewModal,
      reviewTarget,
      reviewForm,
      savingReview,
      openResult,
      canEdit,
      // selection
      selectedIds,
      selectedReviewable,
      toggleSelected,
      clearSelection,
      allVisibleSelected,
      someVisibleSelected,
      toggleAllVisible,
      isGroupAllSelected,
      isGroupSomeSelected,
      toggleGroupSelection,
      // bulk
      bulkApprove,
      openBulkReject,
      closeBulkReject,
      bulkReject,
      showBulkRejectModal,
      bulkRejectForm,
      bulkBusy,
      // groups
      isGroupCollapsed,
      toggleGroup,
      // versions
      versionsOpen,
      versionsLoading,
      versionsList,
      versionsContext,
      openVersions,
      closeVersions
    }
  }
}
</script>

<style scoped>
/* Combined pending+overdue counter pill */
.counter-pill {
  display: inline-flex;
  align-items: stretch;
  border-radius: 999px;
  overflow: hidden;
  font-size: 0.78rem;
  font-weight: 600;
  line-height: 1;
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
  border: 1px solid rgba(0,0,0,0.06);
}
.counter-pill.has-overdue { cursor: pointer; }
.counter-pending {
  background: var(--md-sys-color-primary, #1976d2);
  color: var(--md-sys-color-on-primary, #fff);
  padding: 5px 11px;
}
.counter-overdue {
  background: #c62828;
  color: #fff;
  padding: 5px 11px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  border-left: 1px solid rgba(255,255,255,0.25);
}
.counter-pill.has-overdue:hover .counter-overdue { background: #b71c1c; }

.view-toggle {
  display: inline-flex;
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 10px;
  overflow: hidden;
  background: rgba(255,255,255,0.9);
  backdrop-filter: blur(8px);
}
.view-btn {
  background: transparent;
  border: none;
  padding: 6px 12px;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
  transition: background 0.15s ease;
}
.view-btn:hover { background: rgba(0,0,0,0.04); }
.view-btn.active {
  background: var(--md-sys-color-primary, #1976d2);
  color: #fff;
}

/* Single-line toolbar */
.toolbar-card { padding: 8px 12px !important; }
.toolbar-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.toolbar-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.toolbar-title { font-size: 1rem; font-weight: 700; white-space: nowrap; }
.toolbar-filters {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1 1 auto;
  min-width: 0;
  flex-wrap: wrap;
}
.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  margin-left: auto;
}
.toolbar-search {
  flex: 2 1 200px;
  min-width: 160px;
  margin: 0;
}
.toolbar-select {
  flex: 1 1 130px;
  min-width: 120px;
  margin: 0;
}
.toolbar-card .form-control-sm {
  height: 32px;
  padding: 4px 10px;
  font-size: 0.85rem;
  border-radius: 8px;
}
.hide-md { }
@media (max-width: 1100px) {
  .hide-md { display: none; }
}
@media (max-width: 600px) {
  .toolbar-search, .toolbar-select { flex-basis: 100%; }
}

/* Floating bulk action bar — overlays content, doesn't push layout */
.bulk-bar {
  background: var(--md-sys-color-primary, #1976d2);
  color: #fff;
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 14px;
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  box-shadow: 0 12px 32px rgba(13, 71, 161, 0.35);
}
.bulk-bar-floating {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1500;
  min-width: 360px;
  max-width: calc(100vw - 32px);
}
.bulk-info { display: flex; align-items: center; gap: 8px; }
.bulk-info .text-muted { color: rgba(255,255,255,0.75) !important; }
.bulk-actions { display: flex; gap: 8px; margin-left: auto; }
.bulk-bar .btn-success {
  background: #2e7d32; border-color: #2e7d32; color: #fff;
}
.bulk-bar .btn-success:hover:not(:disabled) { background: #1b5e20; border-color: #1b5e20; }
.bulk-bar .btn-danger { background: #c62828; border-color: #c62828; color: #fff; }
.bulk-bar .btn-danger:hover:not(:disabled) { background: #b71c1c; border-color: #b71c1c; }
.bulk-bar .btn-outline-secondary { background: transparent; border-color: rgba(255,255,255,0.4); color: #fff; }
.bulk-bar .btn-outline-secondary:hover { background: rgba(255,255,255,0.12); }

.bulk-bar-enter-active, .bulk-bar-leave-active {
  transition: opacity 0.22s ease, transform 0.22s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.bulk-bar-enter-from, .bulk-bar-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}

@media (max-width: 600px) {
  .hide-sm { display: none; }
  .toolbar-top { gap: 8px; }
  .bulk-bar-floating { left: 8px; right: 8px; transform: none; min-width: 0; }
  .bulk-bar-enter-from, .bulk-bar-leave-to { transform: translateY(20px); }
}

/* Cards — denser glass for readability over photo backdrop */
.reviews-view :deep(.card) {
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(14px) saturate(140%);
  -webkit-backdrop-filter: blur(14px) saturate(140%);
  border: 1px solid rgba(0, 0, 0, 0.06);
}

/* Header action buttons — solid surface so they don't disappear over photo */
.reviews-view > .d-flex .btn-outline-primary {
  background: rgba(255,255,255,0.9);
  backdrop-filter: blur(8px);
  border-color: var(--md-sys-color-primary, #1976d2);
}
.reviews-view > .d-flex .btn-outline-primary:hover {
  background: var(--md-sys-color-primary, #1976d2);
  color: #fff;
}

/* Table */
.table { width: 100%; }
.table th {
  background: rgba(245, 247, 250, 0.95);
  padding: 10px 12px;
  font-weight: 700;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #455a64;
  position: sticky;
  top: 0;
  z-index: 1;
  border-bottom: 1px solid rgba(0,0,0,0.08);
}
.table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  vertical-align: middle;
}
.table tr:hover { background: var(--md-sys-color-surface-variant); }
.table tr.selected { background: var(--md-sys-color-primary-container, #e3f2fd); }

.check-col { width: 36px; }
.check-col input { cursor: pointer; }

.badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.72rem;
  font-weight: 700;
  white-space: nowrap;
  letter-spacing: 0.2px;
  border: 1px solid transparent;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.badge-success { background: #c8e6c9; color: #1b5e20; border-color: rgba(27, 94, 32, 0.18); }
.badge-danger  { background: #ffcdd2; color: #b71c1c; border-color: rgba(183, 28, 28, 0.18); }
.badge-warning { background: #ffe0b2; color: #bf360c; border-color: rgba(191, 54, 12, 0.18); }
.badge-info    { background: #0277bd; color: #fff;    border-color: rgba(0,0,0,0.06); }

.comment-cell {
  font-size: 0.85rem;
  color: var(--md-sys-color-on-surface-variant);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cmt-inline {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 3px 10px 3px 3px;
  border-radius: 999px;
  font-size: 0.82rem;
  max-width: 100%;
  border: 1px solid transparent;
}
.cmt-inline .cmt-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cmt-inline-exec {
  background: rgba(2, 136, 209, 0.08);
  color: #01579b;
  border-color: rgba(2, 136, 209, 0.18);
}
.cmt-inline-rev {
  background: rgba(46, 125, 50, 0.10);
  color: #1b5e20;
  border-color: rgba(46, 125, 50, 0.18);
}

/* User avatar circle */
.user-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  font-size: 0.66rem;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0;
  background: #607d8b;
}
.user-avatar.sm { width: 20px; height: 20px; font-size: 0.6rem; }
.user-avatar img { width: 100%; height: 100%; object-fit: cover; display: block; }
.avatar-blue   { background: #1976d2; }
.avatar-teal   { background: #00897b; }
.avatar-amber  { background: #f57c00; }
.avatar-pink   { background: #d81b60; }
.avatar-purple { background: #6a1b9a; }
.avatar-green  { background: #2e7d32; }
.avatar-red    { background: #c62828; }
.avatar-indigo { background: #3949ab; }

/* Tooltip body for comments */
.tt-cmt { display: flex; flex-direction: column; gap: 4px; }
.tt-cmt-head { font-weight: 700; font-size: 0.78rem; }
.tt-cmt-body { font-size: 0.82rem; line-height: 1.4; white-space: pre-wrap; opacity: 0.95; }

.btn-quick-approve { color: #2e7d32; }
.btn-quick-approve:hover { background: #e8f5e9; }

/* Version chip — clickable, opens history drawer */
.version-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: rgba(255,255,255,0.85);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 999px;
  padding: 2px 10px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.78rem;
  cursor: pointer;
  color: var(--md-sys-color-primary, #1976d2);
  font-weight: 600;
  transition: background 0.15s ease, border-color 0.15s ease, transform 0.1s ease;
}
.version-chip:hover {
  background: var(--md-sys-color-primary, #1976d2);
  border-color: var(--md-sys-color-primary, #1976d2);
  color: #fff;
}
.version-chip:active { transform: scale(0.97); }
.version-chip.sm { padding: 1px 8px; font-size: 0.72rem; }
.version-chip i { font-size: 0.72rem; opacity: 0.85; }
.version-chip::after {
  content: '';
  width: 0; height: 0;
  border-left: 3px solid currentColor;
  border-top: 3px solid transparent;
  border-bottom: 3px solid transparent;
  margin-left: 1px;
  opacity: 0.7;
}

/* Age */
.age-cell {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.82rem;
  color: var(--md-sys-color-on-surface-variant);
}
.age-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #cfd8dc;
  flex-shrink: 0;
}
.age-fresh .age-dot { background: #66bb6a; }
.age-hanging .age-dot { background: #42a5f5; }
.age-warning .age-dot { background: #ffa726; }
.age-overdue .age-dot { background: #ef5350; box-shadow: 0 0 0 3px rgba(239, 83, 80, 0.18); }
.age-overdue { color: #c62828; font-weight: 600; }
.age-final .age-dot { background: #b0bec5; }

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 1rem;
  text-align: center;
}
.empty-state i {
  font-size: 3rem;
  color: var(--md-sys-color-outline-variant);
  margin-bottom: 1rem;
}
.empty-state p {
  font-size: 1rem;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 0.5rem;
}

/* Load more */
.load-more-row {
  padding: 12px;
  text-align: center;
  border-top: 1px solid var(--md-sys-color-outline-variant);
}

/* Grouped view */
.deal-group {
  margin-bottom: 10px;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 12px;
  overflow: hidden;
  background: var(--md-sys-color-surface);
}
.deal-group-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  cursor: pointer;
  background: var(--md-sys-color-surface-container);
}
.deal-group-header:hover { background: var(--md-sys-color-surface-variant); }
.group-chevron {
  transition: transform 0.18s ease;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.8rem;
}
.group-chevron.open { transform: rotate(90deg); }
.deal-group-title { font-weight: 600; }
.deal-group-meta { margin-left: 4px; }
.deal-group-stats { display: flex; gap: 6px; margin-left: auto; }
.group-select { margin-left: 8px; cursor: pointer; }

.deal-group-body { padding: 4px 0; }

.grp-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 10px 14px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
}
.grp-row:first-child { border-top: none; }
.grp-row.selected { background: var(--md-sys-color-primary-container, #e3f2fd); }
.grp-row-main { flex: 1; min-width: 0; }
.grp-row-title { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.grp-row-meta { display: flex; align-items: center; gap: 10px; margin-top: 4px; flex-wrap: wrap; }
.grp-row-comments { margin-top: 6px; display: flex; flex-direction: column; gap: 4px; }
.cmt {
  font-size: 0.82rem;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(2, 136, 209, 0.06);
  color: #01579b;
  white-space: pre-wrap;
  display: flex;
  gap: 8px;
  align-items: flex-start;
}
.cmt-body { flex: 1; min-width: 0; }
.cmt-head { font-size: 0.78rem; margin-bottom: 2px; }
.cmt-rev { background: rgba(46, 125, 50, 0.08); color: #1b5e20; }
.grp-row-actions { display: flex; gap: 4px; flex-shrink: 0; }

.collapse-enter-active, .collapse-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.collapse-enter-from, .collapse-leave-to {
  opacity: 0;
  max-height: 0;
}
.collapse-enter-to, .collapse-leave-from {
  opacity: 1;
  max-height: 4000px;
}

/* Drawer */
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  z-index: 9500;
  display: flex;
  justify-content: flex-end;
}
.drawer {
  width: min(520px, 100%);
  background: var(--md-sys-color-surface);
  height: 100%;
  display: flex;
  flex-direction: column;
  box-shadow: -10px 0 30px rgba(0,0,0,0.2);
}
.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}
.drawer-body {
  padding: 14px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.ver-card {
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 12px;
  padding: 12px;
  background: var(--md-sys-color-surface-container, #fafafa);
}
.ver-card.current { border-color: var(--md-sys-color-primary, #1976d2); box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.12); }
.ver-card-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.ver-card-row { margin-top: 6px; }
.ver-cmt {
  margin-top: 8px;
  font-size: 0.85rem;
  background: var(--md-sys-color-surface);
  border-radius: 8px;
  padding: 6px 8px;
  white-space: pre-wrap;
}
.ver-card-actions { margin-top: 10px; }

.drawer-enter-active, .drawer-leave-active { transition: opacity 0.2s ease; }
.drawer-enter-active .drawer, .drawer-leave-active .drawer {
  transition: transform 0.22s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
.drawer-enter-from .drawer, .drawer-leave-to .drawer { transform: translateX(100%); }

@media (max-width: 1200px) {
  .table { font-size: 0.85rem; }
  .comment-cell { max-width: 120px; }
}

@media (max-width: 768px) {
  .reviews-view { padding: 8px !important; }
  .reviews-view h2 { font-size: 1.2rem; }
  .card.flex-shrink-0 .form-group { min-width: 100% !important; width: 100%; margin-bottom: 0; }
  .deal-group-stats { display: none; }
  .table thead { display: none; }
  .table tbody tr {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 4px 12px;
    padding: 12px;
    margin-bottom: 8px;
    border: 1px solid var(--md-sys-color-outline-variant);
    border-radius: 12px;
    background: var(--md-sys-color-surface);
  }
  .table tbody td { border: none; padding: 2px 0; }
  .table tbody td.text-right { grid-column: 1 / -1; margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--md-sys-color-outline-variant); }
  .empty-state { padding: 2rem 1rem; }
  .empty-state i { font-size: 2rem; }
}
</style>
