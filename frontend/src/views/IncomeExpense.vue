<template>
  <div class="income-expense-view p-2 h-100 d-flex flex-column">
    <div class="list-card flex-grow-1 d-flex flex-column overflow-hidden">
    <div class="ie-head d-flex justify-between align-center">
      <h2 class="m-0">Доходы и расходы</h2>
      <div class="d-flex align-center gap-3">
        <span v-if="totalCount > 0" class="ie-count">{{ totalCount }}</span>
        <button class="btn btn-sm btn-primary" @click="openCreate">
          <i class="fas fa-plus"></i> Создать
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="list-card__toolbar filters-card flex-shrink-0">
       <div class="filters-row">
          <div class="filter-search">
             <i class="fas fa-search filter-search-icon"></i>
             <input v-model="search" @input="triggerSearch" type="text"
                    class="form-control form-control-sm"
                    style="padding-left: 32px;"
                    placeholder="Поиск по сумме, компании, сделке, договору...">
          </div>
          <UiChipFilter
            v-model="filters.direction"
            :options="DIRECTION_OPTIONS"
            placeholder="Все"
            empty-icon="fas fa-exchange-alt"
            @update:model-value="onFilterChange"
          />
          <UiChipFilter
            v-model="filters.status"
            :options="PAYMENT_STATUS_OPTIONS"
            placeholder="Статус"
            empty-icon="fas fa-circle-half-stroke"
            @update:model-value="onFilterChange"
          />
          <UiChipFilter
            v-model="filters.dealId"
            :options="dealFilterOptions"
            placeholder="Сделка"
            empty-icon="fas fa-project-diagram"
            @update:model-value="onFilterChange"
          />
          <UiChipFilter
            v-model="filters.contractId"
            :options="contractFilterOptions"
            placeholder="Договор"
            empty-icon="fas fa-file-contract"
            @update:model-value="onFilterChange"
          />
          <UiChipFilter
            v-model="filters.payerId"
            :options="companyFilterOptions"
            placeholder="Плательщик"
            empty-icon="fas fa-user"
            @update:model-value="onFilterChange"
          />
          <UiChipFilter
            v-model="filters.payeeId"
            :options="companyFilterOptions"
            placeholder="Получатель"
            empty-icon="fas fa-user"
            @update:model-value="onFilterChange"
          />
          <button
            v-if="selectedEntryIds.length"
            type="button"
            class="btn btn-sm btn-primary bulk-edit-btn"
            @click="openBulkModal"
          >
            <i class="fas fa-pen-to-square"></i>
            Изменить {{ selectedEntryIds.length }}
          </button>
          <button v-if="hasActiveFilters" class="btn btn-sm btn-ghost filter-reset" @click="resetFilters" title="Сбросить фильтры">
            <i class="fas fa-times"></i>
          </button>
       </div>
    </div>

    <!-- Table -->
    <div class="list-card__body flex-grow-1 overflow-hidden d-flex flex-column">
      <!-- Loading -->
      <div v-if="loading" class="d-flex justify-center align-center py-5">
        <div class="spinner"></div>
      </div>

      <!-- Empty State -->
      <div v-else-if="!entries.length" class="empty-state">
        <i class="fas fa-receipt fa-3x mb-3"></i>
        <h4>Нет записей</h4>
        <p class="text-muted">Создайте первую запись о доходе или расходе</p>
        <button class="btn btn-primary mt-2" @click="openCreate">
          <i class="fas fa-plus mr-1"></i> Создать запись
        </button>
      </div>

      <div v-else class="flex-grow-1 overflow-auto p-0">
        <table class="table table-hover m-0 sticky-header">
          <thead>
            <tr>
              <th style="width: 42px;">
                <input
                  type="checkbox"
                  class="bulk-checkbox"
                  :checked="allVisibleSelected"
                  :indeterminate.prop="someVisibleSelected && !allVisibleSelected"
                  @change="toggleVisibleSelection"
                  @click.stop
                >
              </th>
              <th style="width: 90px;">Тип</th>
              <th class="text-right" style="width: 110px;">Сумма</th>
              <th style="width: 100px;">Дата</th>
              <th>Контрагенты</th>
              <th>Сделка</th>
              <th>Договор</th>
              <th>Категория</th>
              <th>Оплаты</th>
              <th style="width: 90px;">Статус</th>
              <th style="width: 60px;"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="entry in entries"
              :key="entry.id"
              class="entry-row"
              :class="{ 'is-expense': entry.direction === 'expense', 'is-selected': selectedEntryIdSet.has(entry.id) }"
              @click="openEdit(entry)"
              style="cursor: pointer;"
            >
              <td @click.stop>
                <input
                  type="checkbox"
                  class="bulk-checkbox"
                  :checked="selectedEntryIdSet.has(entry.id)"
                  @change="toggleEntrySelection(entry.id)"
                >
              </td>
              <td>
                <span class="direction-badge" :class="entry.direction">
                  <i :class="entry.direction === 'income' ? 'fas fa-arrow-up' : 'fas fa-arrow-down'"></i>
                  {{ entry.direction === 'income' ? 'Доход' : 'Расход' }}
                </span>
              </td>
              <td class="text-right fw-600 font-mono" :class="amountClass(entry)">
                {{ formatAmount(entry.amount, entry.direction) }}
              </td>
              <td class="small line-height-1">
                <div>{{ formatDate(entry.plan_date) }}</div>
                <div class="text-muted" v-if="entry.actual_date">{{ formatDate(entry.actual_date) }}</div>
              </td>
              <td>
                <div class="d-flex flex-column small">
                  <div v-if="entry.payer_name" class="counterparty-name fw-500">{{ entry.payer_name }}</div>
                  <div v-if="entry.payee_name" class="counterparty-name text-muted"><span class="counterparty-arrow">→</span> {{ entry.payee_name }}</div>
                  <div v-if="!entry.payer_name && !entry.payee_name" class="text-muted">-</div>
                </div>
              </td>
              <td><span class="text-truncate d-block" style="max-width: 120px;">{{ entry.deal_title || '-' }}</span></td>
              <td>{{ entry.contract_number || '-' }}</td>
              <td>{{ entry.category_code || '-' }}</td>
              <td>
                <div class="payment-chips">
                  <div v-for="item in entry.payments_history" :key="item.transaction_id + '-' + (item.allocation_id || '')"
                       class="payment-chip" :title="chipTooltip(item, entry)">
                    <span class="payment-chip__text">{{ formatDate(item.transaction_date) }} {{ formatAmountShort(item.amount) }}</span>
                    <button class="payment-chip__remove" @click.stop="unlinkPayment(item)" :disabled="saving">&times;</button>
                  </div>
                  <button class="payment-chip payment-chip--add" @click.stop="openLinkModal(entry)">
                    <i class="fas fa-plus"></i>
                  </button>
                </div>
              </td>
              <td>
                <span class="badge badge-sm" :class="statusClass(entry.payment_status)">
                  {{ statusLabel(entry.payment_status) }}
                </span>
              </td>
              <td class="text-right">
                <button class="btn btn-sm btn-icon" @click.stop="openEdit(entry)">
                  <i class="fas fa-pen"></i>
                </button>
                <button class="btn btn-sm btn-icon text-danger" @click.stop="deleteEntry(entry)" :title="'Удалить'" :disabled="saving">
                  <i class="fas fa-trash"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="income-expense-pagination border-top p-2 d-flex justify-between align-center">
        <div class="small text-muted">
          <template v-if="totalCount > 0">
            Показано {{ pageFrom }}-{{ pageTo }} из {{ totalCount }}
          </template>
          <template v-else>
            Нет записей
          </template>
        </div>
        <div class="d-flex align-center gap-2">
          <span class="text-muted small">Стр. {{ page }} из {{ totalPages }}</span>
          <button class="btn btn-sm btn-outline-secondary" :disabled="page <= 1" @click="prevPage">
            <i class="fas fa-chevron-left"></i>
          </button>
          <button class="btn btn-sm btn-outline-secondary" :disabled="!hasNext" @click="nextPage">
            <i class="fas fa-chevron-right"></i>
          </button>
        </div>
      </div>
    </div>
    </div>

    <!-- Bulk Edit Modal -->
    <div v-if="showBulkModal" class="modal-overlay" @click="closeBulkModal">
      <div class="modal-glass" @click.stop style="max-width: 620px;">
        <div class="modal-glass-header">
          <h3 class="m-0">
            <i class="fas fa-pen-to-square mr-2"></i>
            Массовое редактирование
          </h3>
          <button class="btn btn-sm btn-ghost" @click="closeBulkModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-glass-body">
          <div class="bulk-edit-summary">
            Выбрано записей: <strong>{{ selectedEntryIds.length }}</strong>
          </div>

          <div class="form-section">
            <div class="section-title"><i class="fas fa-link"></i> Связи и категория</div>
            <div class="form-group mb-3">
              <label class="small text-muted mb-1">Сделка</label>
              <select v-model="bulkForm.deal_id" class="form-select">
                <option :value="BULK_KEEP">Не менять</option>
                <option :value="BULK_CLEAR">Очистить</option>
                <option v-for="deal in deals" :key="deal.id" :value="deal.id">
                  {{ deal.title }}
                </option>
              </select>
            </div>
            <div class="form-group mb-3">
              <label class="small text-muted mb-1">Договор</label>
              <select v-model="bulkForm.contract_id" class="form-select">
                <option :value="BULK_KEEP">Не менять</option>
                <option :value="BULK_CLEAR">Очистить</option>
                <option v-for="contract in filteredContractsForBulk" :key="contract.id" :value="contract.id">
                  {{ contract.contract_number }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label class="small text-muted mb-1">Категория</label>
              <CategorySmartSelect
                v-model="bulkForm.category_code"
                :options="bulkCategorySelectOptions"
                placeholder="Категория"
                :allow-clear="false"
              />
            </div>
          </div>
        </div>
        <div class="modal-glass-footer">
          <button class="btn btn-secondary" @click="closeBulkModal">Отмена</button>
          <button class="btn btn-primary" @click="saveBulkEdit" :disabled="saving">
            <span v-if="saving" class="spinner-sm mr-1"></span>
            Применить
          </button>
        </div>
      </div>
    </div>

    <!-- Confirm Modal -->
    <Teleport to="body">
      <div v-if="confirmModalOpen" class="confirm-overlay" @click="confirmModalOpen = false">
        <div class="modal-glass" @click.stop style="max-width: 420px;">
          <div class="modal-glass-header">
            <h3 class="m-0"><i class="fas fa-exclamation-triangle mr-2"></i>{{ confirmModalTitle }}</h3>
          </div>
          <div class="modal-glass-body">
            <p class="m-0">{{ confirmModalText }}</p>
          </div>
          <div class="modal-glass-footer">
            <button class="btn btn-secondary" @click="confirmModalOpen = false">Отмена</button>
            <button class="btn btn-primary" @click="executeConfirm" :disabled="saving">
              <span v-if="saving" class="spinner-sm mr-1"></span>
              Подтвердить
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Create/Edit Modal -->
    <div v-if="showFormModal" class="modal-overlay" @click="closeFormModal">
      <div class="modal-glass" @click.stop style="max-width: 600px;">
        <div class="modal-glass-header">
          <h3 class="m-0">
            <i :class="editingEntry ? 'fas fa-edit' : 'fas fa-plus-circle'" class="mr-2"></i>
            {{ editingEntry ? 'Редактирование записи' : 'Новая запись' }}
          </h3>
          <button class="btn btn-sm btn-ghost" @click="closeFormModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-glass-body">
           <!-- Section: Basic -->
           <div class="form-section">
              <div class="section-title"><i class="fas fa-info-circle"></i> Основное</div>
              <div class="d-flex gap-4 mb-3">
                 <div class="form-group w-50">
                    <label class="small text-muted mb-1"><i class="fas fa-exchange-alt mr-1"></i> Тип</label>
                    <select v-model="form.direction" class="form-select">
                      <option value="income">Доход</option>
                      <option value="expense">Расход</option>
                    </select>
                 </div>
                 <div class="form-group w-50">
                    <label class="small text-muted mb-1"><i class="fas fa-ruble-sign mr-1"></i> Сумма</label>
                    <input v-model.number="form.amount" type="number" class="form-control">
                 </div>
              </div>

           <div class="d-flex gap-4 mb-3">
              <div class="form-group w-50">
                 <label class="small text-muted mb-1"><i class="fas fa-calendar mr-1"></i> Плановая дата</label>
                 <input v-model="form.plan_date" type="date" class="form-control">
              </div>
              <div class="form-group w-50">
                 <label class="small text-muted mb-1"><i class="fas fa-calendar-check mr-1"></i> Фактическая дата</label>
                 <input v-model="form.actual_date" type="date" class="form-control">
              </div>
           </div>
           </div>

           <!-- Section: Counterparties -->
           <div class="form-section">
              <div class="section-title"><i class="fas fa-users"></i> Контрагенты</div>
              <div class="d-flex gap-4 mb-3">
                 <div class="form-group w-50">
                    <label class="small text-muted mb-1"><i class="fas fa-user-minus mr-1"></i> Плательщик</label>
                    <CompanySmartSelect
                    v-model="form.payer_id"
                    :options="companies"
                    placeholder="Выберите плательщика"
                  />
                 </div>
                 <div class="form-group w-50">
                    <label class="small text-muted mb-1"><i class="fas fa-user-plus mr-1"></i> Получатель</label>
                    <CompanySmartSelect
                    v-model="form.payee_id"
                    :options="companies"
                    placeholder="Выберите получателя"
                  />
                 </div>
              </div>
           </div>

           <!-- Section: Bindings -->
           <div class="form-section">
              <div class="section-title"><i class="fas fa-link"></i> Связи</div>
              <div class="d-flex gap-4 mb-3">
                 <div class="form-group w-50">
                    <label class="small text-muted mb-1"><i class="fas fa-handshake mr-1"></i> Сделка</label>
                    <select v-model="form.deal_id" class="form-select">
                      <option value="">-</option>
                      <option v-for="deal in deals" :key="deal.id" :value="deal.id">
                        {{ deal.title }}
                      </option>
                    </select>
                 </div>
                 <div class="form-group w-50">
                    <label class="small text-muted mb-1"><i class="fas fa-file-contract mr-1"></i> Договор</label>
                    <select v-model="form.contract_id" class="form-select">
                      <option value="">-</option>
                      <option v-for="contract in filteredContractsForForm" :key="contract.id" :value="contract.id">
                        {{ contract.contract_number }}
                      </option>
                    </select>
                 </div>
              </div>
              <div class="form-group">
                 <label class="small text-muted mb-1"><i class="fas fa-tag mr-1"></i> Категория</label>
                 <CategorySmartSelect
                   v-model="form.category_code"
                   :options="entryCategories"
                   placeholder="Категория"
                 />
              </div>
           </div>

        </div>
        <div class="modal-glass-footer">
          <button class="btn btn-secondary" @click="closeFormModal">
            <i class="fas fa-times mr-1"></i> Отмена
          </button>
          <button class="btn btn-primary" @click="saveEntry" :disabled="saving">
            <span v-if="saving" class="spinner-sm mr-1"></span>
            <i v-else class="fas fa-save mr-1"></i> Сохранить
          </button>
        </div>
      </div>
    </div>

    <!-- Link Modal -->
    <div v-if="showLinkModal" class="modal-overlay" @click="closeLinkModal">
      <div class="modal-glass link-modal" @click.stop>
        <div class="modal-glass-header">
          <div>
            <h3 class="m-0"><i class="fas fa-link mr-2"></i> Привязка платежа</h3>
            <div v-if="selectedEntry" class="d-flex align-center gap-2 mt-1 small">
              <span :class="selectedEntry.direction === 'income' ? 'text-success' : 'text-danger'">
                {{ selectedEntry.direction === 'income' ? 'Доход' : 'Расход' }}
              </span>
              <span class="text-muted">{{ formatAmount(selectedEntry.amount, selectedEntry.direction) }}</span>
              <span class="remaining-indicator">
                <i class="fas fa-wallet mr-1"></i>
                Остаток: {{ formatAmountShort(remainingAmount) }}
              </span>
            </div>
          </div>
          <button class="btn btn-sm btn-ghost" @click="closeLinkModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-glass-body p-0">
           <div class="d-flex gap-2 p-3 pb-0">
              <div class="position-relative flex-grow-1">
                <i class="fas fa-search position-absolute text-muted" style="left: 12px; top: 10px;"></i>
                <input v-model="treasurySearch" @input="triggerTreasurySearch" type="text"
                       class="form-control form-control-sm" style="padding-left: 32px;"
                       placeholder="Поиск по номеру, контрагенту...">
              </div>
              <button class="btn btn-sm btn-outline-secondary" @click="loadTreasuryOptions({ append: false })" title="Обновить">
                <i class="fas fa-sync"></i>
              </button>
           </div>
           <div v-if="treasuryLoading && !treasuryOptions.length" class="d-flex justify-center py-4">
             <div class="spinner"></div>
           </div>
           <div v-else-if="!treasuryOptions.length" class="d-flex flex-column align-center py-4 text-muted">
             <i class="fas fa-inbox fa-2x mb-2"></i>
             <span>Нет подходящих платежей</span>
           </div>
           <div v-else class="link-table-wrap">
              <table class="table table-hover m-0 link-table">
                <thead>
                  <tr>
                    <th class="link-th">Документ</th>
                    <th class="link-th">Дата</th>
                    <th class="link-th text-right">Сумма</th>
                    <th class="link-th text-right">Остаток</th>
                    <th class="link-th text-right">К распредел.</th>
                    <th class="link-th">Плательщик</th>
                    <th class="link-th">Получатель</th>
                    <th class="link-th">Категория</th>
                    <th class="link-th"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="tx in treasuryOptions" :key="tx.id">
                    <td class="small text-nowrap">{{ tx.doc_num || '-' }}</td>
                    <td class="small text-nowrap">{{ formatDate(tx.transaction_date) }}</td>
                    <td class="text-right small text-nowrap" :class="tx.amount < 0 ? 'text-danger' : 'text-success'">
                      {{ formatAmountShort(Math.abs(tx.amount)) }}
                    </td>
                    <td class="text-right small text-nowrap fw-600">
                      {{ formatAmountShort(tx.remainder || Math.abs(tx.amount)) }}
                    </td>
                    <td class="text-right" style="min-width: 100px;">
                      <input
                        v-model.number="getAllocationDraft(tx).amount"
                        type="number"
                        class="form-control form-control-sm"
                        min="0"
                        :max="tx.remainder || Math.abs(tx.amount)"
                      >
                    </td>
                    <td class="small"><span class="text-truncate d-block" style="max-width: 110px;">{{ tx.payer_name || '-' }}</span></td>
                    <td class="small"><span class="text-truncate d-block" style="max-width: 110px;">{{ tx.payee_name || '-' }}</span></td>
                    <td style="min-width: 160px;">
                      <CategorySmartSelect
                        v-model="getAllocationDraft(tx).category_code"
                        :options="allocationCategories"
                        placeholder="Категория"
                        size="sm"
                        input-class="form-select-sm"
                      />
                    </td>
                    <td class="text-right">
                      <button class="btn btn-sm btn-primary" @click="linkAllocation(tx)" :disabled="saving">
                        <span v-if="saving" class="spinner-sm mr-1"></span>
                        <i v-else class="fas fa-link"></i>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
           </div>
           <div v-if="treasuryOptions.length" class="link-pagination">
             <span>
               Показано {{ treasuryOptions.length }} из {{ treasuryTotal || treasuryOptions.length }}
             </span>
             <button
               v-if="treasuryHasMore"
               class="btn btn-sm btn-outline-secondary"
               @click="loadMoreTreasuryOptions"
               :disabled="treasuryLoadingMore"
             >
               <span v-if="treasuryLoadingMore" class="spinner-sm mr-1"></span>
               Показать еще
             </button>
           </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'

import axios from 'axios'
import { api } from '@/services/api'
import CompanySmartSelect from '../components/ui/CompanySmartSelect.vue'
import CategorySmartSelect from '../components/ui/CategorySmartSelect.vue'
import UiChipFilter from '../components/ui/UiChipFilter.vue'
import { useToast } from '../composables/useToast'
import { expenseCategories, incomeCategories } from '../utils/categories'
import { useCompaniesStore } from '../stores/companies'

const DIRECTION_OPTIONS = [
  { value: 'income',  label: 'Доход',  color: '#22c55e' },
  { value: 'expense', label: 'Расход', color: '#ef4444' },
]

const PAYMENT_STATUS_OPTIONS = [
  { value: 'unpaid',  label: 'Не оплачено', color: '#ef4444' },
  { value: 'partial', label: 'Частично',    color: '#f59e0b' },
  { value: 'paid',    label: 'Оплачено',    color: '#22c55e' },
]

export default {
  name: 'IncomeExpense',
  components: { CompanySmartSelect, CategorySmartSelect, UiChipFilter },
  setup() {
    const companiesStore = useCompaniesStore()
    const entries = ref([])
    const companies = ref([])
    const deals = ref([])
    const contracts = ref([])
    const filters = ref({
      direction: '',
      status: '',
      payerId: '',
      payeeId: '',
      dealId: '',
      contractId: ''
    })

    const loading = ref(false)

    // Pagination & search
    const page = ref(1)
    const pageSize = 25
    const totalCount = ref(0)
    const hasNext = ref(false)
    const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize)))
    const pageFrom = computed(() => (totalCount.value > 0 ? (page.value - 1) * pageSize + 1 : 0))
    const pageTo = computed(() => Math.min(page.value * pageSize, totalCount.value))
    const search = ref('')
    let searchTimeout

    // Toast (useToast composable)
    const { success: toastSuccess, error: toastError } = useToast()

    // Confirm modal
    const confirmModalOpen = ref(false)
    const confirmModalTitle = ref('')
    const confirmModalText = ref('')
    const confirmModalAction = ref(null)
    const showConfirm = (title, text, action) => {
      confirmModalTitle.value = title
      confirmModalText.value = text
      confirmModalAction.value = action
      confirmModalOpen.value = true
    }
    const executeConfirm = async () => {
      confirmModalOpen.value = false
      if (confirmModalAction.value) await confirmModalAction.value()
    }

    // Loading states
    const saving = ref(false)
    const selectedEntryIds = ref([])
    const BULK_KEEP = '__keep__'
    const BULK_CLEAR = '__clear__'

    const showFormModal = ref(false)
    const editingEntry = ref(null)
    const form = ref({
      direction: 'income',
      amount: 0,
      plan_date: '',
      actual_date: '',
      payer_id: '',
      payee_id: '',
      deal_id: '',
      contract_id: '',
      category_code: ''
    })
    const showBulkModal = ref(false)
    const bulkForm = ref({
      deal_id: BULK_KEEP,
      contract_id: BULK_KEEP,
      category_code: BULK_KEEP
    })

    const showLinkModal = ref(false)
    const selectedEntry = ref(null)
    const treasuryOptions = ref([])
    const treasurySearch = ref('')
    const treasuryLoading = ref(false)
    const treasuryLoadingMore = ref(false)
    const treasuryTotal = ref(0)
    const treasuryHasMore = ref(false)
    const treasuryLimit = 50
    let treasurySearchTimeout
    const allocationDrafts = ref({})

    const hasActiveFilters = computed(() => {
      return search.value.trim() || filters.value.direction || filters.value.status ||
        filters.value.payerId || filters.value.payeeId || filters.value.dealId || filters.value.contractId
    })

    const resetFilters = () => {
      search.value = ''
      filters.value = { direction: '', status: '', payerId: '', payeeId: '', dealId: '', contractId: '' }
      page.value = 1
      loadEntries()
    }

    const filteredContractsForFilter = computed(() => {
      if (!filters.value.dealId) return contracts.value
      return contracts.value.filter((contract) => contract.deal_id === filters.value.dealId)
    })

    // Опции для UiChipFilter
    const dealFilterOptions = computed(() =>
      (deals.value || []).map((deal) => ({ value: deal.id, label: deal.title }))
    )
    const contractFilterOptions = computed(() =>
      (filteredContractsForFilter.value || []).map((c) => ({ value: c.id, label: c.contract_number }))
    )
    const companyFilterOptions = computed(() =>
      (companies.value || []).map((c) => ({ value: c.id, label: c.name }))
    )

    const onFilterChange = () => {
      page.value = 1
      loadEntries()
    }

    const normalizeId = (value) => String(value || '').trim().toLowerCase()

    const filteredContractsForForm = computed(() => {
      const selectedDealId = normalizeId(form.value.deal_id)
      const selectedPayeeId = normalizeId(form.value.payee_id)
      const allContracts = Array.isArray(contracts.value) ? contracts.value : []

      // Priority rules:
      // 1) if deal selected -> first filter by deal, then by payee(executor) inside that deal
      // 2) if no deal -> filter by payee(executor)
      // 3) if nothing selected -> all contracts
      let byDeal = allContracts
      if (selectedDealId) {
        byDeal = byDeal.filter((contract) => normalizeId(contract.deal_id) === selectedDealId)
      }

      if (selectedPayeeId) {
        byDeal = byDeal.filter((contract) => normalizeId(contract.executor_id) === selectedPayeeId)
      }

      return byDeal
    })

    const selectedEntryIdSet = computed(() => new Set(selectedEntryIds.value))
    const visibleEntryIds = computed(() => entries.value.map((entry) => entry.id).filter(Boolean))
    const selectedEntries = computed(() => entries.value.filter((entry) => selectedEntryIdSet.value.has(entry.id)))
    const allVisibleSelected = computed(() => (
      visibleEntryIds.value.length > 0 &&
      visibleEntryIds.value.every((id) => selectedEntryIdSet.value.has(id))
    ))
    const someVisibleSelected = computed(() => (
      visibleEntryIds.value.some((id) => selectedEntryIdSet.value.has(id))
    ))

    const filteredContractsForBulk = computed(() => {
      const selectedDealId = bulkForm.value.deal_id
      if (!selectedDealId || selectedDealId === BULK_KEEP || selectedDealId === BULK_CLEAR) {
        return contracts.value
      }
      return contracts.value.filter((contract) => normalizeId(contract.deal_id) === normalizeId(selectedDealId))
    })

    const selectedDirections = computed(() => {
      return [...new Set(selectedEntries.value.map((entry) => entry.direction).filter(Boolean))]
    })

    const mergeCategoryOptions = (baseCategories, extraCategories = []) => {
      const result = []
      const seen = new Set()
      ;[...(baseCategories || []), ...(extraCategories || [])].forEach((category) => {
        if (!category || !String(category).trim()) return
        const key = String(category).trim().toLowerCase()
        if (seen.has(key)) return
        seen.add(key)
        result.push(category)
      })
      return result
    }

    const entryCategories = computed(() => {
      const base = form.value.direction === 'expense' ? expenseCategories : incomeCategories
      return mergeCategoryOptions(base, [form.value.category_code, editingEntry.value?.category_code])
    })

    const bulkCategoryOptions = computed(() => {
      let base = []
      if (selectedDirections.value.length === 1) {
        base = selectedDirections.value[0] === 'expense' ? expenseCategories : incomeCategories
      } else {
        base = [...incomeCategories, ...expenseCategories]
      }
      return mergeCategoryOptions(base, selectedEntries.value.map((entry) => entry.category_code))
    })
    const bulkCategorySelectOptions = computed(() => [
      { value: BULK_KEEP, label: 'Не менять' },
      { value: BULK_CLEAR, label: 'Очистить' },
      ...bulkCategoryOptions.value
    ])

    watch(
      () => [form.value.deal_id, form.value.payee_id, contracts.value.length],
      () => {
        const currentContractId = normalizeId(form.value.contract_id)
        if (!currentContractId) return
        const stillAvailable = filteredContractsForForm.value.some(
          (contract) => normalizeId(contract.id) === currentContractId
        )
        if (!stillAvailable) {
          form.value.contract_id = ''
        }
      }
    )

    watch(
      () => [bulkForm.value.deal_id, contracts.value.length],
      () => {
        const currentContractId = normalizeId(bulkForm.value.contract_id)
        if (!currentContractId || bulkForm.value.contract_id === BULK_KEEP || bulkForm.value.contract_id === BULK_CLEAR) return
        const stillAvailable = filteredContractsForBulk.value.some(
          (contract) => normalizeId(contract.id) === currentContractId
        )
        if (!stillAvailable) {
          bulkForm.value.contract_id = BULK_KEEP
        }
      }
    )

    const allocationCategories = computed(() => {
      if (!selectedEntry.value) return []
      const base = selectedEntry.value.direction === 'expense' ? expenseCategories : incomeCategories
      const historyCategories = (selectedEntry.value.payments_history || []).map((item) => item.category_code)
      return mergeCategoryOptions(base, [selectedEntry.value.category_code, ...historyCategories])
    })

    const remainingAmount = computed(() => {
      if (!selectedEntry.value) return 0
      const paid = (selectedEntry.value.payments_history || [])
        .reduce((sum, p) => sum + Math.abs(p.amount || 0), 0)
      return Math.max(0, Math.abs(selectedEntry.value.amount || 0) - paid)
    })

    const getAllocationDraft = (tx) => {
      if (!tx || !tx.id) return { amount: 0, category_code: '' }
      if (!allocationDrafts.value[tx.id]) {
        const defaultAmount = typeof tx.remainder === 'number'
          ? tx.remainder
          : Math.abs(tx.amount || 0)
        allocationDrafts.value[tx.id] = {
          amount: defaultAmount,
          category_code: ''
        }
      }
      return allocationDrafts.value[tx.id]
    }

    const _buildFilterParams = () => {
      const params = {}
      if (filters.value.direction) params.direction = filters.value.direction
      if (filters.value.status) params.status = filters.value.status
      if (filters.value.payerId) params.payer_id = filters.value.payerId
      if (filters.value.payeeId) params.payee_id = filters.value.payeeId
      if (filters.value.dealId) params.deal_id = filters.value.dealId
      if (filters.value.contractId) params.contract_id = filters.value.contractId
      if (search.value.trim()) params.search = search.value.trim()
      return params
    }

    const loadEntries = async () => {
      loading.value = true
      try {
        const params = {
          ..._buildFilterParams(),
          skip: (page.value - 1) * pageSize,
          limit: pageSize
        }
        const response = await api.incomeExpense.list(params)
        entries.value = response || []
        const visibleIds = new Set(entries.value.map((entry) => entry.id))
        selectedEntryIds.value = selectedEntryIds.value.filter((id) => visibleIds.has(id))
        await loadCount()
        hasNext.value = page.value * pageSize < totalCount.value
      } catch (error) {
        toastError('Ошибка загрузки записей')
      } finally {
        loading.value = false
      }
    }

    const toggleEntrySelection = (entryId) => {
      if (!entryId) return
      if (selectedEntryIdSet.value.has(entryId)) {
        selectedEntryIds.value = selectedEntryIds.value.filter((id) => id !== entryId)
      } else {
        selectedEntryIds.value = [...selectedEntryIds.value, entryId]
      }
    }

    const toggleVisibleSelection = () => {
      if (allVisibleSelected.value) {
        const visible = new Set(visibleEntryIds.value)
        selectedEntryIds.value = selectedEntryIds.value.filter((id) => !visible.has(id))
        return
      }
      const merged = new Set([...selectedEntryIds.value, ...visibleEntryIds.value])
      selectedEntryIds.value = [...merged]
    }

    const resetBulkForm = () => {
      bulkForm.value = {
        deal_id: BULK_KEEP,
        contract_id: BULK_KEEP,
        category_code: BULK_KEEP
      }
    }

    const openBulkModal = () => {
      if (!selectedEntryIds.value.length) {
        toastError('Выберите записи')
        return
      }
      resetBulkForm()
      showBulkModal.value = true
    }

    const closeBulkModal = () => {
      showBulkModal.value = false
    }

    const buildBulkPayload = () => {
      const payload = { entry_ids: [...selectedEntryIds.value] }
      ;['deal_id', 'contract_id', 'category_code'].forEach((key) => {
        const value = bulkForm.value[key]
        if (value === BULK_KEEP) return
        payload[key] = value === BULK_CLEAR ? null : value
      })
      return payload
    }

    const saveBulkEdit = async () => {
      const payload = buildBulkPayload()
      if (!payload.entry_ids.length) {
        toastError('Выберите записи')
        return
      }
      const changedFields = ['deal_id', 'contract_id', 'category_code'].filter((key) => Object.prototype.hasOwnProperty.call(payload, key))
      if (!changedFields.length) {
        toastError('Выберите, что изменить')
        return
      }
      saving.value = true
      try {
        const response = await api.incomeExpense.bulkUpdate(payload)
        toastSuccess(`Обновлено записей: ${response?.updated || payload.entry_ids.length}`)
        showBulkModal.value = false
        selectedEntryIds.value = []
        await loadEntries()
      } catch (error) {
        toastError(error.response?.data?.detail || 'Ошибка массового редактирования')
      } finally {
        saving.value = false
      }
    }

    const loadCount = async () => {
      try {
        const params = _buildFilterParams()
        const response = await api.incomeExpense.count(params)
        totalCount.value = response?.count || 0
      } catch (error) {
        toastError('Ошибка загрузки счетчика')
      }
    }

    const nextPage = () => {
      if (hasNext.value) { page.value++; loadEntries() }
    }
    const prevPage = () => {
      if (page.value > 1) { page.value--; loadEntries() }
    }
    const triggerSearch = () => {
      clearTimeout(searchTimeout)
      searchTimeout = setTimeout(() => {
        page.value = 1
        loadEntries()
      }, 300)
    }

    const loadCompanies = async () => {
      try {
        await companiesStore.ensureLoaded()
        companies.value = companiesStore.items
      } catch (error) {
        toastError('Ошибка загрузки компаний')
      }
    }

    const loadDeals = async () => {
      try {
        const response = await axios.get('/api/v1/deals/')
        deals.value = response.data || []
      } catch (error) {
        toastError('Ошибка загрузки сделок')
      }
    }

    const loadContracts = async () => {
      try {
        const response = await axios.get('/api/v1/contracts/')
        contracts.value = response.data?.items || response.data || []
      } catch (error) {
        toastError('Ошибка загрузки договоров')
      }
    }

    const openCreate = () => {
      editingEntry.value = null
      form.value = {
        direction: 'income',
        amount: 0,
        plan_date: '',
        actual_date: '',
        payer_id: '',
        payee_id: '',
        deal_id: '',
        contract_id: '',
        category_code: ''
      }
      showFormModal.value = true
    }

    const openEdit = (entry) => {
      editingEntry.value = entry
      form.value = {
        direction: entry.direction,
        amount: entry.amount,
        plan_date: entry.plan_date || '',
        actual_date: entry.actual_date || '',
        payer_id: entry.payer_id || '',
        payee_id: entry.payee_id || '',
        deal_id: entry.deal_id || '',
        contract_id: entry.contract_id || '',
        category_code: entry.category_code || ''
      }
      showFormModal.value = true
    }

    const closeFormModal = () => {
      showFormModal.value = false
    }

    const buildPayload = () => {
      return {
        direction: form.value.direction,
        amount: form.value.amount,
        plan_date: form.value.plan_date || null,
        actual_date: form.value.actual_date || null,
        payer_id: form.value.payer_id || null,
        payee_id: form.value.payee_id || null,
        deal_id: form.value.deal_id || null,
        contract_id: form.value.contract_id || null,
        category_code: form.value.category_code || null
      }
    }

    const _doSave = async () => {
      const payload = buildPayload()
      saving.value = true
      try {
        if (editingEntry.value) {
          await api.incomeExpense.update(editingEntry.value.id, payload)
        } else {
          await api.incomeExpense.create(payload)
        }
        showFormModal.value = false
        toastSuccess(editingEntry.value ? 'Запись сохранена' : 'Запись создана')
        await loadEntries()
      } catch (error) {
        toastError('Ошибка при сохранении')
      } finally {
        saving.value = false
      }
    }

    const saveEntry = async () => {
      if (!form.value.plan_date) {
        toastError('Заполните плановую дату')
        return
      }
      const payload = buildPayload()
      const selectedContract = contracts.value.find((c) => c.id === payload.contract_id)
      const isServiceContract = selectedContract?.contract_type === 'services'
      if (selectedContract && !isServiceContract && selectedContract.amount && payload.amount > selectedContract.amount) {
        showConfirm('Превышение суммы', 'Сумма превышает лимит договора. Продолжить?', _doSave)
        return
      }
      await _doSave()
    }

    const deleteEntry = (entry) => {
      if (!entry || !entry.id) return
      const amount = formatAmount(entry.amount, entry.direction)
      showConfirm('Удалить запись', `Удалить запись на сумму ${amount}?`, async () => {
        saving.value = true
        try {
          await api.incomeExpense.remove(entry.id)
          toastSuccess('Запись удалена')
          await loadEntries()
        } catch (error) {
          toastError('Ошибка удаления')
        } finally {
          saving.value = false
        }
      })
    }

    const openLinkModal = async (entry) => {
      selectedEntry.value = entry
      treasurySearch.value = ''
      allocationDrafts.value = {}
      treasuryOptions.value = []
      treasuryTotal.value = 0
      treasuryHasMore.value = false
      await loadTreasuryOptions({ append: false })
      showLinkModal.value = true
    }

    const closeLinkModal = () => {
      showLinkModal.value = false
      selectedEntry.value = null
      treasuryOptions.value = []
      treasuryTotal.value = 0
      treasuryHasMore.value = false
      treasuryLoadingMore.value = false
    }

    const loadTreasuryOptions = async ({ append = false } = {}) => {
      if (!selectedEntry.value) return
      const direction = selectedEntry.value.direction
      const skip = append ? treasuryOptions.value.length : 0
      if (append) {
        treasuryLoadingMore.value = true
      } else {
        treasuryLoading.value = true
        treasuryOptions.value = []
        treasuryTotal.value = 0
        treasuryHasMore.value = false
      }
      try {
        const response = await api.treasury.list({
          tx_type: direction === 'expense' ? 'expense' : 'income',
          search: treasurySearch.value || undefined,
          status: 'not_allocated',
          skip,
          limit: treasuryLimit
        })
        const items = response.items || []
        const filteredItems = items.filter((item) => {
          const remainder = item.remainder ?? Math.abs(item.amount || 0)
          if (remainder <= 0) return false
          const flag = String(item.ignore_flag || '').trim().toLowerCase()
          if (['да', 'yes', 'true', '1'].includes(flag)) return false
          return true
        })
        if (append) {
          const existingIds = new Set(treasuryOptions.value.map((item) => item.id))
          treasuryOptions.value = [
            ...treasuryOptions.value,
            ...filteredItems.filter((item) => !existingIds.has(item.id))
          ]
        } else {
          treasuryOptions.value = filteredItems
        }
        treasuryTotal.value = Number(response.total || treasuryOptions.value.length)
        treasuryHasMore.value = Boolean(response.has_more ?? (skip + items.length < treasuryTotal.value))
      } catch (error) {
        toastError('Ошибка загрузки платежей')
      } finally {
        treasuryLoading.value = false
        treasuryLoadingMore.value = false
      }
    }

    const loadMoreTreasuryOptions = () => {
      if (!treasuryHasMore.value || treasuryLoadingMore.value) return
      loadTreasuryOptions({ append: true })
    }

    const triggerTreasurySearch = () => {
      clearTimeout(treasurySearchTimeout)
      treasurySearchTimeout = setTimeout(() => {
        loadTreasuryOptions({ append: false })
      }, 300)
    }

    const linkAllocation = async (tx) => {
      if (!selectedEntry.value) return
      const draft = getAllocationDraft(tx)
      const amount = Number(draft.amount || 0)
      const remainder = Number(tx.remainder || Math.abs(tx.amount || 0))
      const ignoreFlag = String(tx.ignore_flag || '').trim().toLowerCase()
      const ignoreCategory = ['yes', 'true', '1', '\u0434\u0430'].includes(ignoreFlag) || (
        ignoreFlag && !['no', 'false', '0', '\u043d\u0435\u0442'].includes(ignoreFlag)
      )
      if (!amount || amount <= 0) {
        toastError('Укажите сумму распределения')
        return
      }
      if (amount > remainder) {
        toastError('Сумма превышает остаток')
        return
      }
      if (!ignoreCategory && !draft.category_code) {
        toastError('Выберите категорию')
        return
      }
      saving.value = true
      try {
        await api.treasury.createAllocation(tx.id, {
          income_expense_id: selectedEntry.value.id,
          amount,
          category_code: draft.category_code || null
        })
        toastSuccess('Платеж привязан')
        await loadEntries()
        await loadTreasuryOptions({ append: false })
      } catch (error) {
        toastError('Ошибка привязки платежа')
      } finally {
        saving.value = false
      }
    }

    const unlinkPayment = async (item) => {
      if (!item) return
      saving.value = true
      try {
        if (item.allocation_id) {
          await api.treasury.removeAllocation(item.allocation_id)
        } else if (item.transaction_id) {
          await api.treasury.update(item.transaction_id, { income_expense_id: null })
        }
        toastSuccess('Привязка удалена')
        await loadEntries()
      } catch (error) {
        toastError('Ошибка удаления привязки')
      } finally {
        saving.value = false
      }
    }

    const statusLabel = (status) => {
      if (status === 'paid') return 'Оплачено'
      if (status === 'partial') return 'Частично'
      return 'Не оплачено'
    }

    const statusClass = (status) => {
      if (status === 'paid') return 'badge-success'
      if (status === 'partial') return 'badge-warning'
      return 'badge-danger'
    }

    const formatDate = (value) => {
      if (!value) return '-'
      return new Date(value).toLocaleDateString('ru-RU')
    }

    const formatAmount = (value, direction) => {
      const num = Math.abs(value || 0)
      const formatted = new Intl.NumberFormat('ru-RU').format(num)
      if (direction === 'expense') return `- ${formatted}`
      return formatted
    }

    const amountClass = (entry) => (entry.direction === 'expense' ? 'text-danger' : 'text-success')

    const formatAmountShort = (value) => {
      const num = Math.abs(value || 0)
      return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 }).format(num)
    }

    const chipTooltip = (item, entry) => {
      const date = formatDate(item.transaction_date)
      const amount = formatAmount(item.amount, entry.direction)
      const docNum = item.doc_num || '-'
      return `${date} — ${amount}\n№ документа: ${docNum}`
    }

    onMounted(async () => {
      await Promise.all([
        loadCompanies(),
        loadDeals(),
        loadContracts(),
        loadEntries()
      ])
    })

    return {
      entries, companies, deals, contracts,
      filteredContractsForFilter, filteredContractsForForm, filters,
      DIRECTION_OPTIONS, PAYMENT_STATUS_OPTIONS,
      dealFilterOptions, contractFilterOptions, companyFilterOptions,
      onFilterChange,
      hasActiveFilters, resetFilters,
      selectedEntryIds, selectedEntryIdSet, allVisibleSelected, someVisibleSelected,
      toggleEntrySelection, toggleVisibleSelection,
      showBulkModal, bulkForm, filteredContractsForBulk, bulkCategoryOptions, bulkCategorySelectOptions,
      BULK_KEEP, BULK_CLEAR, openBulkModal, closeBulkModal, saveBulkEdit,
      showFormModal, editingEntry, form, entryCategories,
      showLinkModal, selectedEntry, treasuryOptions, treasurySearch, treasuryLoading,
      treasuryLoadingMore, treasuryTotal, treasuryHasMore, allocationCategories,
      remainingAmount,
      loadEntries, openCreate, openEdit, closeFormModal, saveEntry, deleteEntry,
      openLinkModal, closeLinkModal, loadTreasuryOptions, loadMoreTreasuryOptions, triggerTreasurySearch,
      getAllocationDraft, linkAllocation, unlinkPayment,
      statusLabel, statusClass, formatDate, formatAmount, formatAmountShort, amountClass, chipTooltip,
      loading, saving,
      // Confirm modal
      confirmModalOpen, confirmModalTitle, confirmModalText, executeConfirm,
      // Pagination & search
      page, totalPages, totalCount, hasNext, nextPage, prevPage, pageFrom, pageTo, search, triggerSearch
    }
  }
}
</script>


<style scoped>
.fw-600 { font-weight: 600; }
.font-mono { font-family: monospace; }
.text-right { text-align: right; }
.text-success { color: var(--md-sys-color-primary, #28cd41); }
.text-danger { color: var(--md-sys-color-error, #ff3b30); }
.text-nowrap { white-space: nowrap; }
/* ── Tasks reference standard: one unified card (header band → filters
   band → table body), white chrome, soft shadow, full-height. ── */
.income-expense-view {
  --apr-card-bg: rgba(255, 255, 255, 0.97);
  --apr-card-border: rgba(216, 224, 240, 0.92);
  --apr-card-shadow: 0 18px 42px rgba(15, 23, 42, 0.06);
  --apr-radius: 20px;
  --apr-ink: #0a1629;
  --apr-muted: #7d8592;
  --apr-soft: #f6f8fb;
  padding: 12px !important;
  min-height: 0;
}

.income-expense-view .list-card {
  flex: 1;
  min-height: 0;
  margin-bottom: 0;
  background: var(--apr-card-bg);
  border: 1px solid var(--apr-card-border);
  border-radius: var(--apr-radius);
  box-shadow: var(--apr-card-shadow);
  overflow: hidden;
}

/* Header band */
.income-expense-view .ie-head {
  padding: 10px 16px;
  border-bottom: 1px solid var(--apr-card-border);
  flex-shrink: 0;
}
.income-expense-view .ie-head h2 {
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--apr-ink);
}
.income-expense-view .ie-count {
  display: inline-flex;
  align-items: center;
  min-height: 20px;
  padding: 2px 9px;
  border-radius: var(--radius-pill, 999px);
  background: var(--apr-soft);
  color: #5f6b7c;
  font-size: 0.72rem;
  font-weight: 700;
}

/* Filters band */
.income-expense-view .list-card__toolbar,
.income-expense-view .filters-card {
  background: var(--apr-soft);
  border-bottom: 1px solid var(--apr-card-border);
  padding: 8px 16px !important;
}

/* Table — compact, soft-tint sticky head, hairline rows */
.income-expense-view .table { font-size: 0.82rem; }
.sticky-header th {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--apr-soft) !important;
  color: var(--apr-muted);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  border-bottom: 1px solid var(--apr-card-border);
}
.income-expense-view .table td,
.income-expense-view .table th { border-color: var(--apr-card-border); }
.income-expense-view .entry-row:hover { background-color: var(--apr-soft); }
.bulk-checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--md-sys-color-primary, #0d6efd);
}
.bulk-edit-btn {
  white-space: nowrap;
}
.entry-row.is-selected {
  background: rgba(63, 140, 255, 0.08);
}
.entry-row.is-selected:hover {
  background: rgba(63, 140, 255, 0.12);
}
.bulk-edit-summary {
  padding: 10px 12px;
  margin-bottom: 12px;
  border: 1px solid rgba(63, 140, 255, 0.16);
  border-radius: 12px;
  background: rgba(63, 140, 255, 0.08);
  color: var(--md-sys-color-on-surface);
  font-size: 0.9rem;
}
.income-expense-pagination {
  position: sticky;
  bottom: 0;
  background: var(--apr-soft, #f6f8fb);
  border-top: 1px solid var(--apr-card-border, rgba(216, 224, 240, 0.92));
  z-index: 4;
  padding: 8px 16px;
}
.text-truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: var(--md-sys-color-on-surface-variant);
}

.empty-state h4 {
  margin: 0 0 8px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}

.empty-state p {
  margin: 0;
  max-width: 280px;
}

/* Spinner */
.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--md-sys-color-outline-variant);
  border-top-color: var(--md-sys-color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.spinner-sm {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid var(--md-sys-color-outline-variant);
  border-top-color: var(--md-sys-color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  vertical-align: middle;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Direction Badge */
.direction-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.direction-badge.income {
  background: var(--md-sys-color-primary-container, #e8f5e9);
  color: var(--md-sys-color-on-primary-container, #2e7d32);
}

.direction-badge.expense {
  background: var(--md-sys-color-error-container, #ffebee);
  color: var(--md-sys-color-on-error-container, #c62828);
}

/* Entry Row */
.entry-row {
  transition: background-color 0.15s ease;
}

.entry-row:hover {
  background-color: rgba(120, 120, 128, 0.12);
}

.entry-row.is-expense {
  background: var(--md-sys-color-error-container, rgba(255, 59, 48, 0.08));
}

.entry-row.is-expense:hover {
  background: rgba(255, 59, 48, 0.13);
}

/* Dates column */
.line-height-1 { line-height: 1.3; }

/* Counterparties */
.counterparty-name {
  white-space: normal;
  word-break: break-word;
  line-height: 1.3;
  max-width: 180px;
}

.counterparty-arrow {
  color: var(--md-sys-color-outline, #999);
  margin-right: 2px;
}

/* Remaining amount indicator */
.remaining-indicator {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 8px;
  background: var(--md-sys-color-tertiary-container, #fff3e0);
  color: var(--md-sys-color-on-tertiary-container, #e65100);
  font-weight: 600;
}

/* Glass Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-glass {
  width: 100%;
  background: var(--md-sys-color-surface-thick);
  backdrop-filter: var(--glass-blur, blur(20px));
  border: 1px solid var(--glass-border-light, rgba(255,255,255,0.3));
  border-radius: 16px;
  box-shadow: var(--shadow-lg, 0 8px 32px rgba(0,0,0,0.12));
  animation: modalSlideIn 0.25s ease;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.modal-glass-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant, #e0e0e0);
}

.modal-glass-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.modal-glass-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid var(--md-sys-color-outline-variant, #e0e0e0);
}

@keyframes modalSlideIn {
  from { transform: translateY(-12px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* Confirm overlay */
.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 20px;
}

/* Ghost button */
.btn-ghost {
  background: transparent;
  border: none;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background-color 0.15s ease;
}
.btn-ghost:hover {
  background: rgba(120, 120, 128, 0.18);
}

/* Form sections */
.form-section {
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 12px;
  background: rgba(120, 120, 128, 0.08);
}

.section-title {
  font-weight: 600;
  font-size: 0.85rem;
  color: var(--md-sys-color-on-surface-variant);
  margin-bottom: 12px;
}

/* Filters */
.filters-card {
  padding: 8px 12px !important;
}

.filters-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

/* Базово все фильтры в одну строку (десктоп). На узких экранах
   медиазапрос ниже разрешает перенос. Без overflow на ряду —
   иначе клиппятся выпадашки чип-фильтров. */
.income-expense-view .filters-row {
  flex-wrap: nowrap;
  gap: 6px;
}
.income-expense-view .filters-row > * {
  flex-shrink: 0;
}
.income-expense-view .filter-search {
  flex: 1 1 180px;
  min-width: 140px;
  max-width: 320px;
}

.filter-search {
  position: relative;
  flex: 1 1 220px;
  max-width: 320px;
}

.filter-search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.75rem;
  pointer-events: none;
}

.filter-select {
  flex: 0 0 auto;
  width: 120px;
}

.filter-select--wide {
  width: 160px;
}

.filter-reset {
  flex: 0 0 auto;
  color: var(--md-sys-color-error, #ff3b30);
  padding: 4px 6px;
}

/* Payment Chips */
.payment-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.payment-chip {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 500;
  background: rgba(120, 120, 128, 0.2);
  color: var(--md-sys-color-on-surface, #333);
  border: none;
  white-space: nowrap;
  cursor: default;
  transition: background-color 0.15s ease;
  line-height: 1.4;
}

.payment-chip:hover {
  background: rgba(120, 120, 128, 0.28);
}

.payment-chip__text {
  pointer-events: none;
}

.payment-chip__remove {
  display: none;
  background: none;
  border: none;
  color: var(--md-sys-color-error, #ff3b30);
  cursor: pointer;
  font-size: 0.85rem;
  line-height: 1;
  padding: 0 2px;
  margin-left: 2px;
  font-weight: 700;
}

.payment-chip:hover .payment-chip__remove {
  display: inline;
}

.payment-chip--add {
  background: transparent;
  border: 1px dashed var(--md-sys-color-outline, #999);
  color: var(--md-sys-color-primary, #007aff);
  cursor: pointer;
  padding: 2px 6px;
  font-size: 0.65rem;
}

.payment-chip--add:hover {
  background: var(--md-sys-color-primary-container, #e3f2fd);
  border-color: var(--md-sys-color-primary, #007aff);
}

/* Link Modal */
.link-modal {
  max-width: 1100px;
  width: 95vw;
}

.link-table-wrap {
  max-height: 420px;
  overflow-y: auto;
  padding: 8px 0 0;
}

.link-table {
  font-size: 0.82rem;
}

.link-table th {
  position: sticky;
  top: 0;
  background: var(--md-sys-color-surface-thick);
  z-index: 2;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--md-sys-color-on-surface-variant);
  padding: 6px 8px;
  white-space: nowrap;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.link-table td {
  padding: 6px 8px;
  vertical-align: middle;
}

.link-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.78rem;
}

/* Dark theme contrast fixes */
:global(:root[data-theme="dark"]) .income-expense-view .modal-glass {
  background: rgba(24, 28, 34, 0.98);
  border-color: rgba(255, 255, 255, 0.16);
  color: #eef3fb;
}

:global(:root[data-theme="dark"]) .income-expense-view .modal-glass-header,
:global(:root[data-theme="dark"]) .income-expense-view .modal-glass-footer {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.12);
}

:global(:root[data-theme="dark"]) .income-expense-view .modal-glass .text-muted {
  color: #b8c1cf !important;
}

:global(:root[data-theme="dark"]) .income-expense-view .form-section {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

:global(:root[data-theme="dark"]) .income-expense-view .section-title {
  color: #d7deea;
}

:global(:root[data-theme="dark"]) .income-expense-view .modal-glass .form-control,
:global(:root[data-theme="dark"]) .income-expense-view .modal-glass .form-select {
  background: rgba(255, 255, 255, 0.09);
  border-color: rgba(255, 255, 255, 0.16);
  color: #eef3fb;
}

:global(:root[data-theme="dark"]) .income-expense-view .modal-glass .form-control:focus,
:global(:root[data-theme="dark"]) .income-expense-view .modal-glass .form-select:focus {
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(64, 145, 255, 0.7);
  box-shadow: 0 0 0 3px rgba(64, 145, 255, 0.22);
}

:global(:root[data-theme="dark"]) .income-expense-view .payment-chip {
  background: rgba(255, 255, 255, 0.14);
  color: #eef3fb;
}

:global(:root[data-theme="dark"]) .income-expense-view .payment-chip:hover {
  background: rgba(255, 255, 255, 0.2);
}

:global(:root[data-theme="dark"]) .income-expense-view .payment-chip--add {
  background: rgba(64, 145, 255, 0.08);
  border-color: rgba(143, 195, 255, 0.65);
  color: #8fc3ff;
}

:global(:root[data-theme="dark"]) .income-expense-view .payment-chip--add:hover {
  background: rgba(64, 145, 255, 0.2);
  border-color: #8fc3ff;
}

:global(:root[data-theme="dark"]) .income-expense-view .link-table th {
  background: rgba(24, 28, 34, 0.98);
  color: #cfd7e4;
  border-bottom-color: rgba(255, 255, 255, 0.12);
}

:global(:root[data-theme="dark"]) .income-expense-view .link-table td {
  color: #eef3fb;
  border-bottom-color: rgba(255, 255, 255, 0.08);
}

:global(:root[data-theme="dark"]) .income-expense-view .link-table tbody tr:hover td {
  background: rgba(255, 255, 255, 0.05);
}

/* Mobile Responsive */
@media (max-width: 768px) {
  .income-expense-view {
    padding: 0 !important;
  }

  .income-expense-view h2 {
    font-size: 1.25rem !important;
  }

  .income-expense-view > .d-flex:first-child {
    flex-direction: column;
    gap: 12px;
  }

  .income-expense-view .filters-row {
    flex-direction: column;
    flex-wrap: wrap;
  }
  .income-expense-view .filters-row > * {
    flex-shrink: 1;
  }

  .filter-search,
  .filter-select,
  .filter-select--wide {
    width: 100% !important;
    max-width: 100% !important;
    flex: 1 1 100%;
  }

  .link-modal {
    width: 100vw;
    max-width: 100vw;
  }

  .table-container {
    overflow-x: auto;
  }

  .income-expense-pagination {
    padding-right: 16px;
  }
}
</style>



