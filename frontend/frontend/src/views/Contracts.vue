<template>
  <div class="contracts-view d-flex flex-column h-100">
    <div class="list-card flex-grow-1 d-flex flex-column overflow-hidden">
    <!-- Single-line toolbar -->
    <div class="list-card__toolbar toolbar-card flex-shrink-0">
      <div class="toolbar-row">
        <h2 class="m-0 toolbar-title">Договоры</h2>

        <!-- Status pills as a compact dropdown -->
        <div class="status-filter-wrap">
          <button
            type="button"
            class="status-filter-btn"
            :class="filters.status ? `status-${filters.status}` : 'status-all'"
            @click="statusFilterOpen = !statusFilterOpen"
          >
            <i v-if="!filters.status" class="fas fa-circle-half-stroke status-filter-btn__icon"></i>
            <span v-else class="status-dot"></span>
            <span class="status-filter-btn__label">{{ filters.status ? getStatusText(filters.status) : 'Все статусы' }}</span>
            <span class="status-filter-btn__count">{{ currentStatusCount }}</span>
            <i class="fas fa-caret-down ml-1"></i>
          </button>
          <transition name="pop">
            <div v-if="statusFilterOpen" class="status-filter-menu" v-click-outside="() => statusFilterOpen = false">
              <button
                type="button"
                class="status-filter-menu__item"
                :class="{ active: !filters.status }"
                @click="setQuickStatus(''); statusFilterOpen = false"
              >
                <span class="status-filter-menu__label">Все статусы</span>
                <span class="status-filter-menu__count">{{ stats.total }}</span>
                <i v-if="!filters.status" class="fas fa-check ml-1"></i>
              </button>
              <div class="status-filter-menu__divider"></div>
              <button
                v-for="opt in STATUS_OPTIONS"
                :key="opt.value"
                type="button"
                class="status-filter-menu__item"
                :class="[`status-${opt.value}`, { active: filters.status === opt.value }]"
                @click="setQuickStatus(opt.value); statusFilterOpen = false"
              >
                <span class="status-dot"></span>
                <span class="status-filter-menu__label">{{ opt.label }}</span>
                <span class="status-filter-menu__count">{{ stats[opt.value] || 0 }}</span>
                <i v-if="filters.status === opt.value" class="fas fa-check ml-1"></i>
              </button>
            </div>
          </transition>
        </div>

        <!-- Type filter dropdown -->
        <div class="type-filter-wrap">
          <button
            type="button"
            class="type-filter-btn"
            :class="filters.contract_type ? `type-${filters.contract_type}` : ''"
            @click="typeFilterOpen = !typeFilterOpen"
          >
            <span v-if="filters.contract_type" class="type-dot"></span>
            <i v-else class="fas fa-file-contract"></i>
            <span class="type-filter-btn__label">{{ filters.contract_type ? getTypeText(filters.contract_type) : 'Все типы' }}</span>
            <i class="fas fa-caret-down ml-1"></i>
          </button>
          <transition name="pop">
            <div v-if="typeFilterOpen" class="type-filter-menu" v-click-outside="() => typeFilterOpen = false">
              <button
                type="button"
                class="type-filter-menu__item"
                :class="{ active: !filters.contract_type }"
                @click="setContractType(''); typeFilterOpen = false"
              >
                <span class="type-filter-menu__label">Все типы</span>
                <i v-if="!filters.contract_type" class="fas fa-check ml-1"></i>
              </button>
              <div class="type-filter-menu__divider"></div>
              <button
                v-for="opt in CONTRACT_TYPES"
                :key="opt.value"
                type="button"
                class="type-filter-menu__item"
                :class="[`type-${opt.value}`, { active: filters.contract_type === opt.value }]"
                @click="setContractType(opt.value); typeFilterOpen = false"
              >
                <span class="type-dot"></span>
                <span class="type-filter-menu__label">{{ opt.label }}</span>
                <i v-if="filters.contract_type === opt.value" class="fas fa-check ml-1"></i>
              </button>
            </div>
          </transition>
        </div>

        <div class="contracts-search-wrap">
          <UiInput
            v-model="filters.search"
            class="contracts-search"
            size="sm"
            icon-left="fas fa-search"
            clearable
            placeholder="Поиск (номер, заказчик, исполнитель, сделка)..."
            @update:modelValue="debouncedSearch"
            @clear="resetAndLoad"
          />
        </div>

        <div class="more-filter-wrap">
          <UiIconButton
            icon="fas fa-sliders-h"
            label="Дополнительные фильтры"
            size="sm"
            :variant="hasMoreFilters ? 'primary' : 'default'"
            @click="showFilterPanel = !showFilterPanel"
          >
            <span v-if="hasMoreFilters" class="filter-active-dot">{{ activeMoreFiltersCount }}</span>
          </UiIconButton>
          <transition name="pop">
            <div v-if="showFilterPanel" class="advanced-filters-pop" v-click-outside="() => showFilterPanel = false">
              <div class="advanced-filters-pop__head">
                <span><i class="fas fa-sliders-h mr-1"></i>Доп. фильтры</span>
                <button v-if="hasMoreFilters" class="filter-pill filter-pill--clear" @click="clearAdvancedFilters">
                  <i class="fas fa-rotate-left mr-1"></i>Сбросить
                </button>
              </div>
              <div class="advanced-filters">
                <div class="form-group">
                  <label>Дата от</label>
                  <UiInput v-model="filters.date_from" type="date" size="sm" @change="resetAndLoad" />
                </div>
                <div class="form-group">
                  <label>Дата до</label>
                  <UiInput v-model="filters.date_to" type="date" size="sm" @change="resetAndLoad" />
                </div>
                <div class="form-group">
                  <label>Сумма от</label>
                  <UiInput v-model="filters.amount_from" type="number" size="sm" min="0" @change="debouncedSearch" />
                </div>
                <div class="form-group">
                  <label>Сумма до</label>
                  <UiInput v-model="filters.amount_to" type="number" size="sm" min="0" @change="debouncedSearch" />
                </div>
                <div class="form-group form-group--full">
                  <label>Заказчик</label>
                  <CompanySmartSelect v-model="filters.customer_id" :options="companies" placeholder="Любой" @update:modelValue="resetAndLoad" />
                </div>
                <div class="form-group form-group--full">
                  <label>Исполнитель</label>
                  <CompanySmartSelect v-model="filters.executor_id" :options="companies" placeholder="Любой" @update:modelValue="resetAndLoad" />
                </div>
              </div>
            </div>
          </transition>
        </div>

        <UiPager
          v-model="currentPage"
          class="contracts-pager"
          :total="totalCount"
          :page-size="pageSize"
          :loading="loading"
          @update:pageSize="onPagerPageSizeChange"
          @change="goToPage"
        />

        <div class="more-wrap">
          <UiIconButton
            icon="fas fa-ellipsis-vertical"
            label="Действия"
            size="sm"
            @click="moreMenuOpen = !moreMenuOpen"
          />
          <transition name="pop">
            <div v-if="moreMenuOpen" class="more-menu" v-click-outside="() => moreMenuOpen = false">
              <button type="button" class="more-menu-item" @click="exportContractsCsv('page')">
                <i class="fas fa-download mr-2"></i> Экспорт текущей страницы
              </button>
              <button type="button" class="more-menu-item" @click="exportContractsCsv('all')" :disabled="exportingAll">
                <i v-if="exportingAll" class="fas fa-spinner fa-spin mr-2"></i>
                <i v-else class="fas fa-file-csv mr-2"></i>
                Экспорт всех (с фильтрами)
              </button>
            </div>
          </transition>
        </div>

        <UiButton variant="primary" size="sm" icon-left="fas fa-plus" @click="openCreateModal">
          Добавить
        </UiButton>

      <!-- Active filter pills -->
      <div v-if="hasActiveFilters" class="filter-pills">
        <span v-if="filters.search" class="filter-pill">
          Поиск: «{{ filters.search }}»
          <button type="button" @click="filters.search = ''; resetAndLoad()"><i class="fas fa-times"></i></button>
        </span>
        <span v-if="filters.status" class="filter-pill" :class="`status-${filters.status}`">
          {{ getStatusText(filters.status) }}
          <button type="button" @click="setQuickStatus('')"><i class="fas fa-times"></i></button>
        </span>
        <span v-if="filters.contract_type" class="filter-pill" :class="`type-${filters.contract_type}`">
          {{ getTypeText(filters.contract_type) }}
          <button type="button" @click="setContractType('')"><i class="fas fa-times"></i></button>
        </span>
        <span v-if="filters.date_from || filters.date_to" class="filter-pill">
          Дата: {{ filters.date_from || '—' }} → {{ filters.date_to || '—' }}
          <button type="button" @click="filters.date_from = ''; filters.date_to = ''; resetAndLoad()"><i class="fas fa-times"></i></button>
        </span>
        <span v-if="filters.amount_from || filters.amount_to" class="filter-pill">
          Сумма: {{ filters.amount_from || '0' }} → {{ filters.amount_to || '∞' }}
          <button type="button" @click="filters.amount_from = null; filters.amount_to = null; resetAndLoad()"><i class="fas fa-times"></i></button>
        </span>
        <span v-if="filters.customer_id" class="filter-pill">
          Заказчик: {{ getCompanyName(filters.customer_id) }}
          <button type="button" @click="filters.customer_id = ''; resetAndLoad()"><i class="fas fa-times"></i></button>
        </span>
        <span v-if="filters.executor_id" class="filter-pill">
          Исполнитель: {{ getCompanyName(filters.executor_id) }}
          <button type="button" @click="filters.executor_id = ''; resetAndLoad()"><i class="fas fa-times"></i></button>
        </span>
        <button type="button" class="filter-pill filter-pill--clear" @click="clearAllFilters">
          <i class="fas fa-rotate-left mr-1"></i>Сбросить все
        </button>
      </div>
    </div>

    <!-- Floating bulk action bar -->
    <transition name="bulk-bar">
      <div v-if="selectedIds.size > 0" class="bulk-bar">
        <div class="bulk-bar__info">
          <i class="fas fa-check-square"></i>
          <span>Выбрано: <b>{{ selectedIds.size }}</b></span>
        </div>
        <div class="bulk-bar__actions">
          <UiSelect
            :model-value="bulkStatusAction"
            class="bulk-bar__select"
            :options="STATUS_OPTIONS"
            :disabled="bulkBusy"
            placeholder="Изменить статус..."
            size="sm"
            :block="false"
            @update:modelValue="onBulkStatusChange"
          />
          <UiButton variant="danger" size="sm" icon-left="fas fa-trash" :disabled="bulkBusy" @click="bulkDelete">
            Удалить
          </UiButton>
          <UiButton variant="secondary" size="sm" @click="clearSelection">Снять выбор</UiButton>
        </div>
      </div>
    </transition>

    <!-- Table -->
    <div class="list-card__body contracts-table-card flex-grow-1 overflow-hidden d-flex flex-column">
      <div v-if="loading" class="p-3 d-flex flex-column gap-2">
        <SkeletonLoader v-for="i in 8" :key="i" height="44px" />
      </div>

      <UiEmptyState
        v-else-if="!contracts.length"
        icon="fas fa-file-contract"
        :title="hasActiveFilters ? 'Договоры по фильтру не найдены' : 'Договоров пока нет'"
        :description="hasActiveFilters ? 'Попробуйте изменить или сбросить фильтры.' : 'Создайте первый договор, чтобы начать работу.'"
      >
        <template #actions>
          <UiButton v-if="hasActiveFilters" variant="secondary" size="sm" icon-left="fas fa-rotate-left" @click="clearAllFilters">
            Сбросить фильтры
          </UiButton>
          <UiButton variant="primary" size="sm" icon-left="fas fa-plus" @click="openCreateModal">
            Создать договор
          </UiButton>
        </template>
      </UiEmptyState>

      <div v-else class="contracts-table-scroll">
        <table class="contracts-table">
          <thead>
            <tr>
              <th class="check-col">
                <input
                  type="checkbox"
                  :checked="allOnPageSelected"
                  :indeterminate.prop="someOnPageSelected && !allOnPageSelected"
                  @change="toggleAllOnPage"
                />
              </th>
              <th class="sortable" @click="toggleSort('contract_number')">
                <span>Номер</span>
                <i v-if="sortBy === 'contract_number'" class="fas" :class="sortDir === 'asc' ? 'fa-arrow-up-short-wide' : 'fa-arrow-down-wide-short'"></i>
              </th>
              <th class="sortable" @click="toggleSort('contract_date')">
                <span>Дата</span>
                <i v-if="sortBy === 'contract_date'" class="fas" :class="sortDir === 'asc' ? 'fa-arrow-up-short-wide' : 'fa-arrow-down-wide-short'"></i>
              </th>
              <th class="sortable" @click="toggleSort('status')">
                <span>Статус</span>
                <i v-if="sortBy === 'status'" class="fas" :class="sortDir === 'asc' ? 'fa-arrow-up-short-wide' : 'fa-arrow-down-wide-short'"></i>
              </th>
              <th class="text-right sortable" @click="toggleSort('amount')">
                <span>Сумма</span>
                <i v-if="sortBy === 'amount'" class="fas" :class="sortDir === 'asc' ? 'fa-arrow-up-short-wide' : 'fa-arrow-down-wide-short'"></i>
              </th>
              <th>Тип</th>
              <th>Заказчик</th>
              <th>Исполнитель</th>
              <th>Сделка</th>
              <th class="actions-th"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="contract in contracts"
              :key="contract.id"
              class="contracts-row"
              :class="{ selected: selectedIds.has(contract.id) }"
              @click="openContract(contract)"
            >
              <td class="check-col" @click.stop>
                <input type="checkbox" :checked="selectedIds.has(contract.id)" @change="toggleSelected(contract.id)" />
              </td>
              <td class="contracts-num">
                <span class="contracts-num__primary">{{ contract.contract_number }}</span>
              </td>
              <td class="contracts-date">{{ formatDate(contract.contract_date) }}</td>
              <td @click.stop>
                <div class="inline-status-wrap">
                  <button
                    type="button"
                    class="status-badge status-badge--editable"
                    :class="`status-${contract.status || 'default'}`"
                    :disabled="inlineStatusBusyId === contract.id"
                    @click.stop="inlineStatusOpenId = inlineStatusOpenId === contract.id ? null : contract.id"
                  >
                    <span class="status-dot"></span>{{ getStatusText(contract.status) }}
                    <i v-if="inlineStatusBusyId === contract.id" class="fas fa-spinner fa-spin ml-1"></i>
                    <i v-else class="fas fa-caret-down ml-1"></i>
                  </button>
                  <transition name="pop">
                    <div
                      v-if="inlineStatusOpenId === contract.id"
                      class="inline-status-menu"
                      v-click-outside="() => inlineStatusOpenId = null"
                    >
                      <button
                        v-for="opt in STATUS_OPTIONS"
                        :key="opt.value"
                        type="button"
                        class="inline-status-menu__item"
                        :class="[`status-${opt.value}`, { active: contract.status === opt.value }]"
                        @click.stop="changeContractStatus(contract, opt.value)"
                      >
                        <span class="status-dot"></span>{{ opt.label }}
                        <i v-if="contract.status === opt.value" class="fas fa-check ml-auto"></i>
                      </button>
                    </div>
                  </transition>
                </div>
              </td>
              <td class="text-right contracts-amount">{{ formatAmount(contract.amount) }}</td>
              <td>
                <span class="type-badge" :class="`type-${contract.contract_type || 'other'}`">
                  <span class="type-dot"></span>{{ getTypeText(contract.contract_type) }}
                </span>
              </td>
              <td :title="getCompanyName(contract.customer_id)">
                <router-link
                  v-if="contract.customer_id"
                  :to="`/companies?company_id=${contract.customer_id}`"
                  class="contracts-company-cell"
                  @click.stop
                >
                  <span class="user-avatar xs" :class="`avatar-${avatarColor(getCompanyName(contract.customer_id))}`">
                    {{ initials(getCompanyName(contract.customer_id)) }}
                  </span>
                  <span class="contracts-company-cell__name">{{ getCompanyName(contract.customer_id) }}</span>
                </router-link>
                <span v-else class="text-muted">—</span>
              </td>
              <td :title="getCompanyName(contract.executor_id)">
                <router-link
                  v-if="contract.executor_id"
                  :to="`/companies?company_id=${contract.executor_id}`"
                  class="contracts-company-cell"
                  @click.stop
                >
                  <span class="user-avatar xs" :class="`avatar-${avatarColor(getCompanyName(contract.executor_id))}`">
                    {{ initials(getCompanyName(contract.executor_id)) }}
                  </span>
                  <span class="contracts-company-cell__name">{{ getCompanyName(contract.executor_id) }}</span>
                </router-link>
                <span v-else class="text-muted">—</span>
              </td>
              <td @click.stop>
                <router-link v-if="contract.deal_id" :to="`/projects/${contract.deal_id}`" class="contracts-deal__link" :title="getDealTitle(contract.deal_id)">
                  {{ getDealTitle(contract.deal_id) }}
                </router-link>
                <span v-else class="text-muted">—</span>
              </td>
              <td class="actions-cell" @click.stop>
                <UiIconButton
                  class="row-actions-btn"
                  icon="fas fa-ellipsis-vertical"
                  label="Действия"
                  size="sm"
                  @click.stop="onRowMenuToggle($event, contract.id)"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="!loading && contracts.length" class="contracts-footer">
        <span class="text-muted small">
          Показано {{ Math.min((currentPage - 1) * pageSize + 1, totalCount) }}–{{ Math.min(currentPage * pageSize, totalCount) }} из {{ totalCount }}
        </span>
      </div>
    </div>
    </div>

    <!-- Floating row-actions menu (teleported to body so scroll-overflow doesn't clip it) -->
    <Teleport to="body">
      <transition name="pop">
        <div
          v-if="openRowMenuId && rowMenuTarget"
          class="more-menu more-menu--floating"
          :style="{ top: rowMenuCoords.top + 'px', left: rowMenuCoords.left + 'px' }"
          v-click-outside="() => openRowMenuId = null"
          @click.stop
        >
          <button type="button" class="more-menu-item" @click="editContract(rowMenuTarget); openRowMenuId = null">
            <i class="fas fa-edit mr-2"></i> Редактировать
          </button>
          <button type="button" class="more-menu-item" @click="openContract(rowMenuTarget); openRowMenuId = null">
            <i class="fas fa-up-right-from-square mr-2"></i> Открыть карточку
          </button>
          <div class="more-menu-divider"></div>
          <button type="button" class="more-menu-item more-menu-item--danger" @click="deleteContract(rowMenuTarget); openRowMenuId = null">
            <i class="fas fa-trash mr-2"></i> Удалить
          </button>
        </div>
      </transition>
    </Teleport>

    <!-- Create/Edit Modal -->
    <UiModal
      v-model="showModal"
      :title="isEditing ? 'Редактировать договор' : 'Новый договор'"
      size="md"
      class="contract-form-modal"
      @close="closeModal"
    >
      <form id="contract-form" @submit.prevent="saveContract" class="contract-form">
        <div class="form-row">
          <div class="form-group">
            <UiInput
              v-model="contractForm.contract_number"
              type="text"
              label="Номер договора"
              required
              :error="formValidation.contract_number"
              @blur="validateForm"
            />
          </div>
          <div class="form-group">
            <UiInput
              v-model="contractForm.contract_date"
              type="date"
              label="Дата договора"
              required
              :error="formValidation.contract_date"
              @change="validateForm"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <UiSelect v-model="contractForm.status" label="Статус" :options="STATUS_OPTIONS" />
          </div>
          <div class="form-group">
            <label>Сумма</label>
            <div class="input-with-suffix">
              <UiInput
                v-model.number="contractForm.amount"
                type="number"
                min="0"
                step="0.01"
                :disabled="isServiceType"
                class="contract-amount-field"
              />
              <span class="input-suffix">₽</span>
            </div>
            <small v-if="isServiceType" class="text-muted">
              Для «Оказание услуг» сумма рассчитывается автоматически по оплаченным платежам.
            </small>
          </div>
        </div>

        <div class="form-group">
          <UiSelect v-model="contractForm.contract_type" label="Тип договора" required :options="CONTRACT_TYPES" />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Заказчик (плательщик)</label>
            <CompanySmartSelect v-model="contractForm.customer_id" :options="companies" placeholder="Найти заказчика" />
          </div>
          <div class="form-group">
            <label>Исполнитель</label>
            <CompanySmartSelect v-model="contractForm.executor_id" :options="companies" placeholder="Найти исполнителя" />
          </div>
        </div>

        <div class="form-group">
          <label>Сделка</label>
          <CompanySmartSelect v-model="contractForm.deal_id" :options="dealOptions" placeholder="Не привязано" />
        </div>

        <div class="form-group">
          <UiTextarea
            v-model="contractForm.notes"
            label="Примечания"
            rows="3"
            placeholder="Комментарии, особые условия..."
          />
        </div>
      </form>
      <template #footer>
        <UiButton variant="secondary" @click="closeModal">Отмена</UiButton>
        <UiButton
          type="submit"
          form="contract-form"
          variant="primary"
          :loading="saving"
          :disabled="saving || hasFormErrors"
          icon-left="fas fa-check"
        >
          {{ isEditing ? 'Сохранить' : 'Создать' }}
        </UiButton>
      </template>
    </UiModal>
  </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { api } from '@/services/api'
import { UiButton, UiEmptyState, UiIconButton, UiInput, UiModal, UiPager, UiSelect, UiTextarea } from '../components/ui'
import SkeletonLoader from '../components/ui/SkeletonLoader.vue'
import CompanySmartSelect from '../components/ui/CompanySmartSelect.vue'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'
import { useCompaniesStore } from '../stores/companies'

// Single source of truth — types & statuses with labels/colors
const CONTRACT_TYPES = [
  { value: 'general_contractor', label: 'Генподрядный',   color: '#1976d2' },
  { value: 'subcontractor',      label: 'Субподрядный',   color: '#f57c00' },
  { value: 'services',           label: 'Оказание услуг', color: '#00897b' },
  { value: 'labor',              label: 'Трудовой',       color: '#6a1b9a' },
]

const STATUS_OPTIONS = [
  { value: 'approval',     label: 'На согласовании', color: '#f59e0b' },
  { value: 'in_progress',  label: 'В работе',        color: '#3b82f6' },
  { value: 'completed',    label: 'Подписан',        color: '#22c55e' },
]

const clickOutside = {
  beforeMount(el, binding) {
    el._co = (e) => { if (!(el === e.target || el.contains(e.target))) binding.value(e) }
    setTimeout(() => document.addEventListener('click', el._co), 0)
  },
  unmounted(el) { document.removeEventListener('click', el._co) }
}

const normalizeId = (v) => v ? String(v).replace(/-/g, '').toLowerCase() : ''

const blankForm = () => ({
  contract_number: '',
  contract_date: '',
  status: 'approval',
  amount: 0,
  contract_type: 'general_contractor',
  customer_id: '',
  executor_id: '',
  deal_id: '',
  notes: '',
})

export default {
  name: 'Contracts',
  components: {
    CompanySmartSelect,
    SkeletonLoader,
    UiButton,
    UiEmptyState,
    UiIconButton,
    UiInput,
    UiModal,
    UiPager,
    UiSelect,
    UiTextarea
  },
  directives: { 'click-outside': clickOutside },
  setup() {
    const toast = useToast()
    const { confirm } = useConfirm()
    const route = useRoute()
    const router = useRouter()
    const companiesStore = useCompaniesStore()

    const contracts = ref([])
    const companies = ref([])
    const deals = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const showModal = ref(false)
    const isEditing = ref(false)
    const showFilterPanel = ref(false)

    // Pagination + sort
    const currentPage = ref(1)
    const pageSize = ref(parseInt(localStorage.getItem('contracts-page-size') || '25', 10) || 25)
    const totalCount = ref(0)
    const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize.value)))
    const sortBy = ref('contract_date')
    const sortDir = ref('desc')

    const stats = ref({ total: 0, approval: 0, in_progress: 0, completed: 0 })

    const filters = ref({
      search: '',
      contract_type: '',
      status: '',
      date_from: '',
      date_to: '',
      amount_from: null,
      amount_to: null,
      customer_id: '',
      executor_id: '',
    })

    // UI state
    const statusFilterOpen = ref(false)
    const typeFilterOpen = ref(false)
    const moreMenuOpen = ref(false)
    const openRowMenuId = ref(null)
    const inlineStatusOpenId = ref(null)
    const inlineStatusBusyId = ref(null)

    // Selection (bulk)
    const selectedIds = ref(new Set())
    const bulkBusy = ref(false)
    const exportingAll = ref(false)
    const bulkStatusAction = ref('')

    // Form
    const contractForm = ref(blankForm())
    const formValidation = ref({ contract_number: '', contract_date: '' })
    const isServiceType = computed(() => contractForm.value.contract_type === 'services')
    const hasFormErrors = computed(() => !!(formValidation.value.contract_number || formValidation.value.contract_date))
    const dealOptions = computed(() => deals.value.map(d => ({ id: d.id, name: d.title || `Сделка ${d.id}` })))

    const STATUS_TEXT = Object.fromEntries(STATUS_OPTIONS.map(o => [o.value, o.label]))
    const TYPE_TEXT = Object.fromEntries(CONTRACT_TYPES.map(o => [o.value, o.label]))
    const getStatusText = (s) => STATUS_TEXT[s] || s || '—'
    const getTypeText = (t) => TYPE_TEXT[t] || t || '—'

    const hasMoreFilters = computed(() => !!(
      filters.value.date_from || filters.value.date_to ||
      filters.value.amount_from || filters.value.amount_to ||
      filters.value.customer_id || filters.value.executor_id
    ))
    const activeMoreFiltersCount = computed(() => {
      let n = 0
      if (filters.value.date_from || filters.value.date_to) n += 1
      if (filters.value.amount_from || filters.value.amount_to) n += 1
      if (filters.value.customer_id) n += 1
      if (filters.value.executor_id) n += 1
      return n
    })
    const hasActiveFilters = computed(() => !!(
      filters.value.search || filters.value.status || filters.value.contract_type ||
      hasMoreFilters.value
    ))
    const currentStatusCount = computed(() => {
      if (!filters.value.status) return stats.value.total
      return stats.value[filters.value.status] || 0
    })

    const initials = (name) => {
      if (!name || name === '—') return '?'
      const parts = String(name).replace(/^ООО\s*«?/, '').replace(/»$/, '').trim().split(/\s+/).filter(Boolean)
      if (!parts.length) return '?'
      if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
      return (parts[0][0] + parts[1][0]).toUpperCase()
    }
    const avatarColor = (name) => {
      const palette = ['blue', 'teal', 'amber', 'pink', 'purple', 'green', 'red', 'indigo']
      if (!name) return palette[0]
      let h = 0
      for (let i = 0; i < name.length; i += 1) h = (h * 31 + name.charCodeAt(i)) | 0
      return palette[Math.abs(h) % palette.length]
    }

    // Debounced search
    let searchTimeout = null
    const debouncedSearch = () => {
      clearTimeout(searchTimeout)
      searchTimeout = setTimeout(() => { currentPage.value = 1; loadContracts() }, 300)
    }

    const resetAndLoad = () => { currentPage.value = 1; loadContracts() }

    const setQuickStatus = (status) => { filters.value.status = status; resetAndLoad() }
    const setContractType = (type) => { filters.value.contract_type = type; resetAndLoad() }

    const clearAdvancedFilters = () => {
      filters.value.date_from = ''
      filters.value.date_to = ''
      filters.value.amount_from = null
      filters.value.amount_to = null
      filters.value.customer_id = ''
      filters.value.executor_id = ''
      resetAndLoad()
    }
    const clearAllFilters = () => {
      filters.value = {
        search: '', contract_type: '', status: '',
        date_from: '', date_to: '', amount_from: null, amount_to: null,
        customer_id: '', executor_id: '',
      }
      resetAndLoad()
    }

    // URL state
    const syncToUrl = () => {
      const q = {}
      if (filters.value.search) q.q = filters.value.search
      if (filters.value.status) q.status = filters.value.status
      if (filters.value.contract_type) q.type = filters.value.contract_type
      if (currentPage.value > 1) q.page = String(currentPage.value)
      if (pageSize.value !== 25) q.size = String(pageSize.value)
      if (sortBy.value !== 'contract_date' || sortDir.value !== 'desc') q.sort = `${sortBy.value}:${sortDir.value}`
      router.replace({ query: q }).catch(() => {})
    }
    const restoreFromUrl = () => {
      const q = route.query || {}
      if (q.q) filters.value.search = String(q.q)
      if (q.status) filters.value.status = String(q.status)
      if (q.type) filters.value.contract_type = String(q.type)
      if (q.page) currentPage.value = parseInt(q.page, 10) || 1
      if (q.size) pageSize.value = parseInt(q.size, 10) || pageSize.value
      if (q.sort) {
        const [by, dir] = String(q.sort).split(':')
        if (by) sortBy.value = by
        if (dir) sortDir.value = dir
      }
    }

    const loadContracts = async () => {
      loading.value = true
      try {
        const params = {
          skip: (currentPage.value - 1) * pageSize.value,
          limit: pageSize.value,
          sort_by: sortBy.value,
          sort_dir: sortDir.value,
        }
        const f = filters.value
        if (f.search) params.search = f.search
        if (f.contract_type) params.contract_type = f.contract_type
        if (f.status) params.status = f.status
        if (f.customer_id) params.customer_id = f.customer_id
        if (f.executor_id) params.executor_id = f.executor_id

        const data = await api.contracts.list(params)
        let items = []
        if (Array.isArray(data)) {
          items = data
          totalCount.value = data.length
        } else {
          items = data.items || []
          totalCount.value = data.total || 0
          stats.value = data.stats || { total: 0, approval: 0, in_progress: 0, completed: 0 }
        }

        // Client-side filters for date_range / amount_range (backend doesn't support these yet)
        if (f.date_from) items = items.filter(c => c.contract_date && c.contract_date >= f.date_from)
        if (f.date_to) items = items.filter(c => c.contract_date && c.contract_date <= f.date_to)
        if (f.amount_from != null && f.amount_from !== '') items = items.filter(c => Number(c.amount || 0) >= Number(f.amount_from))
        if (f.amount_to != null && f.amount_to !== '') items = items.filter(c => Number(c.amount || 0) <= Number(f.amount_to))

        contracts.value = items
        syncToUrl()

        // Drop selection of items not on this page
        if (selectedIds.value.size) {
          const onPage = new Set(items.map(c => c.id))
          const next = new Set()
          selectedIds.value.forEach(id => { if (onPage.has(id)) next.add(id) })
          selectedIds.value = next
        }
      } catch (error) {
        console.error('Contracts load error:', error)
        toast.error('Не удалось загрузить договоры')
        contracts.value = []
      } finally {
        loading.value = false
      }
    }

    const onPageSizeChange = () => {
      currentPage.value = 1
      localStorage.setItem('contracts-page-size', String(pageSize.value))
      loadContracts()
    }

    const onPagerPageSizeChange = (value) => {
      pageSize.value = Number(value) || pageSize.value
      onPageSizeChange()
    }

    const goToPage = (page) => {
      currentPage.value = Math.max(1, Math.min(page, totalPages.value))
      loadContracts()
    }

    const toggleSort = (field) => {
      if (sortBy.value === field) sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
      else { sortBy.value = field; sortDir.value = field === 'contract_number' ? 'asc' : 'desc' }
      currentPage.value = 1
      loadContracts()
    }

    // CSV export
    const buildCsv = (rows) => {
      const header = ['Номер', 'Дата', 'Статус', 'Сумма', 'Тип', 'Заказчик', 'Исполнитель', 'Сделка']
      const lines = [header.join(';')]
      for (const c of rows) {
        const row = [
          c.contract_number || '',
          formatDate(c.contract_date),
          getStatusText(c.status),
          formatAmount(c.amount),
          getTypeText(c.contract_type),
          getCompanyName(c.customer_id),
          getCompanyName(c.executor_id),
          getDealTitle(c.deal_id),
        ].map(v => `"${String(v).replace(/"/g, '""')}"`).join(';')
        lines.push(row)
      }
      return '﻿' + lines.join('\n')
    }

    const downloadCsv = (csv, filename) => {
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    }

    const exportContractsCsv = async (scope) => {
      moreMenuOpen.value = false
      if (scope === 'page') {
        downloadCsv(buildCsv(contracts.value), `contracts-p${currentPage.value}.csv`)
        toast.success(`Скачано ${contracts.value.length} записей`)
        return
      }
      exportingAll.value = true
      try {
        const params = { skip: 0, limit: 5000, sort_by: sortBy.value, sort_dir: sortDir.value }
        const f = filters.value
        if (f.search) params.search = f.search
        if (f.contract_type) params.contract_type = f.contract_type
        if (f.status) params.status = f.status
        if (f.customer_id) params.customer_id = f.customer_id
        if (f.executor_id) params.executor_id = f.executor_id
        const data = await api.contracts.list(params)
        const items = Array.isArray(data) ? data : (data.items || [])
        downloadCsv(buildCsv(items), `contracts-all-${new Date().toISOString().slice(0,10)}.csv`)
        toast.success(`Скачано ${items.length} записей`)
      } catch (e) {
        toast.error('Не удалось выгрузить полный список')
      } finally {
        exportingAll.value = false
      }
    }

    const loadCompanies = async () => {
      try {
        await companiesStore.ensureLoaded()
        companies.value = companiesStore.items
      } catch (e) { companies.value = [] }
    }
    const loadDeals = async () => {
      try {
        const r = await axios.get('/api/v1/deals/')
        deals.value = r.data || []
      } catch (e) { deals.value = [] }
    }

    // CRUD
    const openCreateModal = () => {
      isEditing.value = false
      contractForm.value = blankForm()
      contractForm.value.contract_date = new Date().toISOString().slice(0, 10)
      formValidation.value = { contract_number: '', contract_date: '' }
      showModal.value = true
    }
    const openContract = (contract) => {
      if (contract?.id) router.push(`/contracts/${contract.id}`)
    }
    const editContract = (contract) => {
      openRowMenuId.value = null
      isEditing.value = true
      const matchedDeal = deals.value.find(d => normalizeId(d.id) === normalizeId(contract.deal_id))
      contractForm.value = {
        id: contract.id,
        contract_number: contract.contract_number || '',
        contract_date: contract.contract_date || '',
        status: contract.status || 'approval',
        amount: contract.amount || 0,
        contract_type: contract.contract_type || 'general_contractor',
        customer_id: normalizeId(contract.customer_id),
        executor_id: normalizeId(contract.executor_id),
        deal_id: matchedDeal ? matchedDeal.id : (contract.deal_id || ''),
        notes: contract.notes || '',
      }
      formValidation.value = { contract_number: '', contract_date: '' }
      showModal.value = true
    }
    const validateForm = () => {
      const v = { contract_number: '', contract_date: '' }
      if (!contractForm.value.contract_number?.trim()) v.contract_number = 'Введите номер'
      if (!contractForm.value.contract_date) v.contract_date = 'Укажите дату'
      formValidation.value = v
      return !v.contract_number && !v.contract_date
    }
    const saveContract = async () => {
      if (!validateForm()) { toast.warning('Заполните обязательные поля'); return }
      saving.value = true
      try {
        const payload = {
          ...contractForm.value,
          amount: contractForm.value.contract_type === 'services' ? 0 : Number(contractForm.value.amount || 0),
          deal_id: contractForm.value.deal_id || null,
        }
        if (isEditing.value) {
          await api.contracts.update(contractForm.value.id, payload)
        } else {
          await api.contracts.create(payload)
        }
        toast.success(isEditing.value ? 'Договор сохранён' : 'Договор создан')
        await loadContracts()
        closeModal()
      } catch (error) {
        console.error('Save error:', error)
        toast.error(error?.response?.data?.detail || 'Ошибка сохранения договора')
      } finally {
        saving.value = false
      }
    }
    const deleteContract = async (contract) => {
      openRowMenuId.value = null
      const ok = await confirm({
        title: 'Удалить договор?',
        message: `«${contract.contract_number}» будет удалён. Действие необратимо.`,
        confirmText: 'Удалить',
        variant: 'danger',
      })
      if (!ok) return
      try {
        await api.contracts.remove(contract.id)
        toast.success('Договор удалён')
        if (contracts.value.length === 1 && currentPage.value > 1) currentPage.value -= 1
        await loadContracts()
      } catch (error) {
        toast.error(error?.response?.data?.detail || 'Ошибка удаления договора')
      }
    }
    const closeModal = () => { showModal.value = false; isEditing.value = false }

    watch(() => contractForm.value.contract_type, (next) => {
      if (next === 'services') contractForm.value.amount = 0
    })

    // Inline status change
    const changeContractStatus = async (contract, newStatus) => {
      inlineStatusOpenId.value = null
      if (!contract || !newStatus || contract.status === newStatus) return
      const idx = contracts.value.findIndex(c => c.id === contract.id)
      if (idx < 0) return
      const prev = contracts.value[idx].status
      contracts.value[idx] = { ...contracts.value[idx], status: newStatus }
      inlineStatusBusyId.value = contract.id
      try {
        await api.contracts.update(contract.id, {
          ...contract,
          status: newStatus,
          customer_id: normalizeId(contract.customer_id),
          executor_id: normalizeId(contract.executor_id),
          deal_id: contract.deal_id || null,
        })
        toast.success(`Статус: ${getStatusText(newStatus)}`)
        // Refresh stats counters in background
        loadContracts()
      } catch (error) {
        contracts.value[idx] = { ...contracts.value[idx], status: prev }
        toast.error(error?.response?.data?.detail || 'Не удалось изменить статус')
      } finally {
        inlineStatusBusyId.value = null
      }
    }

    // Bulk selection
    const toggleSelected = (id) => {
      const next = new Set(selectedIds.value)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      selectedIds.value = next
    }
    const allOnPageSelected = computed(() => {
      if (!contracts.value.length) return false
      return contracts.value.every(c => selectedIds.value.has(c.id))
    })
    const someOnPageSelected = computed(() => contracts.value.some(c => selectedIds.value.has(c.id)))
    const toggleAllOnPage = () => {
      const next = new Set(selectedIds.value)
      if (allOnPageSelected.value) contracts.value.forEach(c => next.delete(c.id))
      else contracts.value.forEach(c => next.add(c.id))
      selectedIds.value = next
    }
    const clearSelection = () => { selectedIds.value = new Set() }
    const toggleRowMenu = (id) => { openRowMenuId.value = openRowMenuId.value === id ? null : id }

    // Teleported row menu — compute coordinates from button rect
    const rowMenuCoords = ref({ top: 0, left: 0 })
    const rowMenuTarget = computed(() => {
      if (!openRowMenuId.value) return null
      return contracts.value.find(c => c.id === openRowMenuId.value) || null
    })
    const onRowMenuToggle = (event, id) => {
      if (openRowMenuId.value === id) {
        openRowMenuId.value = null
        return
      }
      const rect = event.currentTarget.getBoundingClientRect()
      // Default: open below button, right-aligned (menu ~240px wide)
      const menuWidth = 240
      let left = rect.right - menuWidth
      let top = rect.bottom + 6
      // Fit within viewport
      if (left < 8) left = 8
      if (left + menuWidth > window.innerWidth - 8) left = window.innerWidth - menuWidth - 8
      const menuHeightEstimate = 160
      if (top + menuHeightEstimate > window.innerHeight - 8) top = rect.top - menuHeightEstimate - 6
      rowMenuCoords.value = { top, left }
      openRowMenuId.value = id
    }

    const bulkSetStatus = async (status) => {
      const ids = Array.from(selectedIds.value)
      if (!ids.length || !status) return
      const ok = await confirm({
        title: `Перевести ${ids.length} договор(ов) в «${getStatusText(status)}»?`,
        confirmText: 'Применить',
      })
      if (!ok) return
      bulkBusy.value = true
      let failed = 0
      const settle = await Promise.allSettled(ids.map(id => {
        const c = contracts.value.find(x => x.id === id)
        if (!c) return Promise.resolve()
        return api.contracts.update(id, {
          ...c,
          status,
          customer_id: normalizeId(c.customer_id),
          executor_id: normalizeId(c.executor_id),
          deal_id: c.deal_id || null,
        })
      }))
      settle.forEach(r => { if (r.status === 'rejected') failed += 1 })
      bulkBusy.value = false
      clearSelection()
      await loadContracts()
      if (!failed) toast.success(`Готово: ${ids.length}`)
      else if (failed < ids.length) toast.warning(`Готово: ${ids.length - failed}, ошибок: ${failed}`)
      else toast.error('Не удалось применить')
    }

    const onBulkStatusChange = (value) => {
      if (!value) return
      bulkStatusAction.value = ''
      bulkSetStatus(value)
    }

    const bulkDelete = async () => {
      const ids = Array.from(selectedIds.value)
      if (!ids.length) return
      const ok = await confirm({
        title: `Удалить ${ids.length} договор(ов)?`,
        message: 'Действие необратимо.',
        confirmText: 'Удалить',
        variant: 'danger',
      })
      if (!ok) return
      bulkBusy.value = true
      let failed = 0
      const settle = await Promise.allSettled(ids.map(id => api.contracts.remove(id)))
      settle.forEach(r => { if (r.status === 'rejected') failed += 1 })
      bulkBusy.value = false
      clearSelection()
      await loadContracts()
      if (!failed) toast.success(`Удалено: ${ids.length}`)
      else toast.warning(`Удалено: ${ids.length - failed}, ошибок: ${failed}`)
    }

    // Helpers
    const formatAmount = (value) => {
      const a = Number(value || 0)
      return a.toLocaleString('ru-RU', { minimumFractionDigits: 0, maximumFractionDigits: 0, style: 'currency', currency: 'RUB' })
    }
    const formatDate = (value) => value ? new Date(value).toLocaleDateString('ru-RU') : '—'
    const getCompanyName = (id) => {
      if (!id) return ''
      const c = companies.value.find(item => normalizeId(item.id) === normalizeId(id))
      return c ? (c.name || c.short_name || '—') : '—'
    }
    const getDealTitle = (id) => {
      if (!id) return ''
      const d = deals.value.find(item => normalizeId(item.id) === normalizeId(id))
      return d ? (d.title || '—') : '—'
    }

    onMounted(async () => {
      restoreFromUrl()
      await Promise.all([loadCompanies(), loadDeals()])
      await loadContracts()
    })

    return {
      // refs
      contracts, companies, deals, dealOptions,
      loading, saving, showModal, isEditing, showFilterPanel,
      currentPage, pageSize, totalCount, totalPages, sortBy, sortDir,
      stats, filters, contractForm, formValidation, isServiceType, hasFormErrors,
      statusFilterOpen, typeFilterOpen, moreMenuOpen, openRowMenuId,
      inlineStatusOpenId, inlineStatusBusyId,
      selectedIds, bulkBusy, exportingAll, bulkStatusAction,
      // computed
      hasMoreFilters, activeMoreFiltersCount, hasActiveFilters, currentStatusCount,
      allOnPageSelected, someOnPageSelected,
      // constants
      CONTRACT_TYPES, STATUS_OPTIONS,
      // helpers
      getStatusText, getTypeText, getCompanyName, getDealTitle, formatAmount, formatDate,
      initials, avatarColor,
      // actions
      debouncedSearch, resetAndLoad,
      setQuickStatus, setContractType, clearAdvancedFilters, clearAllFilters,
      onPageSizeChange, onPagerPageSizeChange, goToPage, toggleSort,
      exportContractsCsv,
      openCreateModal, openContract, editContract, saveContract, deleteContract, closeModal, validateForm,
      changeContractStatus,
      toggleSelected, toggleAllOnPage, clearSelection, toggleRowMenu,
      rowMenuCoords, rowMenuTarget, onRowMenuToggle,
      bulkSetStatus, onBulkStatusChange, bulkDelete,
    }
  }
}
</script>

<style scoped>
.contracts-view { padding: 12px; gap: 8px; }

/* ============================================================
   Toolbar
   ============================================================ */
.toolbar-card {
  padding: 8px 12px !important;
  overflow: visible !important;
  z-index: 50;
}
.toolbar-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.toolbar-title { font-size: 1rem; font-weight: 700; white-space: nowrap; }

/* Status / type filter dropdowns */
.status-filter-wrap, .type-filter-wrap { position: relative; }
.status-filter-btn, .type-filter-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 10px;
  border: 1px solid var(--color-border-subtle);
  border-radius: 8px;
  background: var(--color-surface);
  font-size: 0.82rem;
  color: var(--color-text);
  cursor: pointer;
  white-space: nowrap;
  transition: 0.12s ease;
}
.status-filter-btn:hover, .type-filter-btn:hover { background: var(--color-surface-3); }
.status-filter-btn__label, .type-filter-btn__label { font-weight: 600; }
.status-filter-btn__icon { color: var(--color-text-muted); font-size: 0.85rem; }
.type-filter-btn .fa-file-contract { color: var(--color-text-muted); font-size: 0.85rem; }
.status-filter-btn__count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 18px;
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(0,0,0,0.06);
  font-size: 0.7rem;
  font-weight: 700;
}
.status-filter-btn .fa-caret-down, .type-filter-btn .fa-caret-down { font-size: 0.7rem; opacity: 0.65; }

.status-filter-btn.status-approval    { color: #b45309; border-color: rgba(245,158,11,0.45); background: rgba(245,158,11,0.06); }
.status-filter-btn.status-in_progress { color: #1d4ed8; border-color: rgba(59,130,246,0.45); background: rgba(59,130,246,0.06); }
.status-filter-btn.status-completed   { color: #166534; border-color: rgba(34,197,94,0.45); background: rgba(34,197,94,0.06); }

.type-filter-btn.type-general_contractor { color: #0277bd; border-color: rgba(2,119,189,0.45); background: rgba(2,119,189,0.06); }
.type-filter-btn.type-subcontractor      { color: #bf360c; border-color: rgba(245,124,0,0.45); background: rgba(245,124,0,0.06); }
.type-filter-btn.type-services           { color: #00695c; border-color: rgba(0,137,123,0.45); background: rgba(0,137,123,0.06); }
.type-filter-btn.type-labor              { color: #4a148c; border-color: rgba(106,27,154,0.45); background: rgba(106,27,154,0.06); }

.status-filter-menu, .type-filter-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  z-index: 200;
  min-width: 220px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: 10px;
  padding: 4px;
  box-shadow: 0 14px 36px rgba(0,0,0,0.14);
}
.status-filter-menu__item, .type-filter-menu__item {
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
  color: var(--color-text);
  text-align: left;
}
.status-filter-menu__item:hover, .type-filter-menu__item:hover {
  background: var(--color-surface-3);
}
.status-filter-menu__item.active, .type-filter-menu__item.active { font-weight: 700; }
.status-filter-menu__label, .type-filter-menu__label { flex: 1; }
.status-filter-menu__item .status-dot,
.type-filter-menu__item .type-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  opacity: 1;
  box-shadow: 0 0 0 2px rgba(255,255,255,0.85);
}
.status-filter-menu__item.status-approval    .status-dot { background: #f59e0b; }
.status-filter-menu__item.status-in_progress .status-dot { background: #3b82f6; }
.status-filter-menu__item.status-completed   .status-dot { background: #22c55e; }
.status-filter-menu__item.status-approval    { color: #b45309; }
.status-filter-menu__item.status-in_progress { color: #1d4ed8; }
.status-filter-menu__item.status-completed   { color: #166534; }
.status-filter-menu__item.status-approval:hover    { background: rgba(245,158,11,0.10); }
.status-filter-menu__item.status-in_progress:hover { background: rgba(59,130,246,0.10); }
.status-filter-menu__item.status-completed:hover   { background: rgba(34,197,94,0.10); }

.type-filter-menu__item.type-general_contractor .type-dot { background: #1976d2; }
.type-filter-menu__item.type-subcontractor      .type-dot { background: #f57c00; }
.type-filter-menu__item.type-services           .type-dot { background: #00897b; }
.type-filter-menu__item.type-labor              .type-dot { background: #6a1b9a; }
.type-filter-menu__item.type-general_contractor { color: #0277bd; }
.type-filter-menu__item.type-subcontractor      { color: #bf360c; }
.type-filter-menu__item.type-services           { color: #00695c; }
.type-filter-menu__item.type-labor              { color: #4a148c; }
.type-filter-menu__item.type-general_contractor:hover { background: rgba(25,118,210,0.10); }
.type-filter-menu__item.type-subcontractor:hover      { background: rgba(245,124,0,0.10); }
.type-filter-menu__item.type-services:hover           { background: rgba(0,137,123,0.10); }
.type-filter-menu__item.type-labor:hover              { background: rgba(106,27,154,0.10); }
.status-filter-menu__count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  padding: 1px 6px;
  border-radius: 999px;
  background: var(--color-surface-3);
  font-size: 0.72rem;
  font-weight: 700;
}
.status-filter-menu__divider, .type-filter-menu__divider {
  height: 1px;
  background: var(--color-border-subtle);
  margin: 4px 0;
}

/* Search */
.contracts-search {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 0 1 320px;
  min-width: 180px;
  height: 32px;
  padding: 0 10px;
  margin-left: auto;
  border: 1px solid var(--color-border-subtle);
  border-radius: 8px;
  background: var(--color-surface);
}
.contracts-search i { color: var(--color-text-muted); font-size: 0.78rem; }
.contracts-search input { flex: 1; border: none; outline: none; background: transparent; font-size: 0.85rem; color: inherit; }
.contracts-search__clear { border: none; background: transparent; cursor: pointer; color: var(--color-text-muted); padding: 2px 4px; }

.filter-active-dot {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: 4px;
  background: rgba(255,255,255,0.25);
  border-radius: 999px;
  padding: 1px 6px;
  font-size: 0.7rem;
  font-weight: 700;
}

/* Pager */
.contracts-pager {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0 6px;
  height: 32px;
  border: 1px solid var(--color-border-subtle);
  border-radius: 8px;
  background: var(--color-surface);
  font-size: 0.82rem;
}
.pager-label {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-weight: 600;
  min-width: 38px;
  text-align: center;
}
.pager-size {
  border: none;
  background: transparent;
  font-size: 0.82rem;
  color: inherit;
  outline: none;
  cursor: pointer;
  padding: 0 4px;
  border-left: 1px solid var(--color-border-subtle);
  margin-left: 4px;
}

/* More menu */
.more-wrap { position: relative; }
.more-menu {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  z-index: 200;
  min-width: 240px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: 10px;
  padding: 4px;
  box-shadow: 0 12px 32px rgba(0,0,0,0.12);
}
.more-menu-item {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 7px 10px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 6px;
  font-size: 0.85rem;
  color: var(--color-text);
  text-align: left;
}
.more-menu-item:hover { background: var(--color-surface-3); }
.more-menu-item--danger { color: #c62828; }
.more-menu-item--danger:hover { background: rgba(198,40,40,0.08); }
.more-menu-divider { height: 1px; background: var(--color-border-subtle); margin: 4px 0; }
/* Teleported row menu: position: fixed so it escapes table scroll container */
.more-menu--floating {
  position: fixed;
  z-index: 9500;
  min-width: 240px;
}

.pop-enter-active, .pop-leave-active { transition: opacity 0.12s ease, transform 0.12s ease; }
.pop-enter-from, .pop-leave-to { opacity: 0; transform: translateY(-4px); }

/* Advanced filters popover */
.more-filter-wrap { position: relative; }
.advanced-filters-pop {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 220;
  width: 380px;
  max-width: calc(100vw - 24px);
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: 12px;
  box-shadow: 0 18px 44px rgba(0,0,0,0.16);
  padding: 12px;
}
.advanced-filters-pop__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 0.86rem;
  font-weight: 600;
  color: var(--color-text);
}
.advanced-filters {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.advanced-filters .form-group { margin: 0; }
.advanced-filters label {
  display: block;
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  font-weight: 600;
  color: var(--color-text-muted);
  margin-bottom: 3px;
}
.advanced-filters .form-group--full { grid-column: 1 / -1; }

/* Filter pills */
.filter-pills {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  padding-top: 6px;
  border-top: 1px solid var(--color-border-subtle);
  margin-top: 6px;
}
.filter-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 4px 3px 10px;
  border-radius: 999px;
  background: var(--color-surface-3);
  font-size: 0.78rem;
  color: var(--color-text);
}
.filter-pill button {
  border: none; background: transparent; cursor: pointer;
  color: inherit; padding: 0 6px; border-radius: 999px;
}
.filter-pill button:hover { background: rgba(0,0,0,0.08); }
.filter-pill--clear { background: transparent; color: var(--color-text-muted); padding: 3px 10px; cursor: pointer; border: none; }
.filter-pill--clear:hover { background: var(--color-surface-3); }
.filter-pill.status-approval    { background: rgba(245,158,11,0.15); color: #b45309; }
.filter-pill.status-in_progress { background: rgba(59,130,246,0.15); color: #1d4ed8; }
.filter-pill.status-completed   { background: rgba(34,197,94,0.15); color: #166534; }

/* Bulk bar */
.bulk-bar {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1500;
  background: var(--color-primary);
  color: #fff;
  border-radius: 14px;
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 12px 32px rgba(13,71,161,0.35);
  flex-wrap: wrap;
}
.bulk-bar__info { display: flex; align-items: center; gap: 8px; }
.bulk-bar__actions { display: flex; gap: 6px; flex-wrap: wrap; }
.bulk-bar__select {
  height: 30px;
  padding: 4px 8px;
  font-size: 0.82rem;
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.4);
  background: rgba(255,255,255,0.12);
  color: #fff;
}
.bulk-bar__select option { color: #000; }
.bulk-bar .btn-outline-secondary { background: transparent; border-color: rgba(255,255,255,0.4); color: #fff; }
.bulk-bar .btn-outline-secondary:hover { background: rgba(255,255,255,0.12); }
.bulk-bar .btn-outline-danger { background: rgba(255,255,255,0.12); border-color: rgba(255,255,255,0.4); color: #fff; }
.bulk-bar .btn-outline-danger:hover { background: #c62828; }
.bulk-bar-enter-active, .bulk-bar-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.bulk-bar-enter-from, .bulk-bar-leave-to { opacity: 0; transform: translateX(-50%) translateY(20px); }

/* ============================================================
   Table
   ============================================================ */
.contracts-table-card { padding: 0 !important; }
.contracts-table-scroll { flex: 1; min-height: 0; overflow: auto; }
.contracts-table { width: 100%; border-collapse: collapse; }
.contracts-table thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  text-align: left;
  background: var(--color-surface-3);
  color: var(--color-text-muted);
  font-weight: 700;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border-subtle);
}
.contracts-table thead th.sortable { cursor: pointer; user-select: none; }
.contracts-table thead th.sortable:hover { color: var(--color-text); }
.contracts-table thead th.sortable i { font-size: 0.78rem; margin-left: 4px; color: var(--color-primary); }
.contracts-table .check-col { width: 36px; padding-left: 14px !important; padding-right: 0 !important; }
.contracts-table .actions-th, .contracts-table .actions-cell { width: 56px; padding-right: 8px; }
.contracts-table .text-right { text-align: right; }

.contracts-row {
  border-bottom: 1px solid var(--color-border-subtle);
  cursor: pointer;
  transition: background 0.12s ease;
}
.contracts-row:hover { background: var(--color-surface-2); }
.contracts-row.selected { background: var(--color-primary-soft); }
.contracts-row td { padding: 10px 12px; font-size: 0.85rem; vertical-align: middle; }

.contracts-num__primary {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-weight: 600;
  color: var(--color-primary);
}
.contracts-date {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.82rem;
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.contracts-amount {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  white-space: nowrap;
}
.contracts-company-cell {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 240px;
  text-decoration: none;
  color: var(--color-text);
}
.contracts-company-cell:hover .contracts-company-cell__name { text-decoration: underline; }
.contracts-company-cell__name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.contracts-deal__link {
  color: var(--color-primary);
  text-decoration: none;
}
.contracts-deal__link:hover { text-decoration: underline; }

/* Status badge — inline editable */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  white-space: nowrap;
  border: 1px solid currentColor;
}
.status-badge--editable {
  cursor: pointer;
  background: transparent;
}
.status-badge--editable:hover:not(:disabled) { filter: brightness(0.95); }
.status-badge--editable .fa-caret-down { font-size: 0.6rem; opacity: 0.7; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; opacity: 0.85; flex-shrink: 0; }
.status-badge.status-approval    { background: rgba(245,158,11,0.15); color: #b45309; }
.status-badge.status-in_progress { background: rgba(59,130,246,0.15); color: #1d4ed8; }
.status-badge.status-completed   { background: rgba(34,197,94,0.15); color: #166534; }
.status-badge.status-default     { background: rgba(96,125,139,0.15); color: #455a64; }

.inline-status-wrap { position: relative; display: inline-block; }
.inline-status-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  z-index: 100;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: 10px;
  padding: 4px;
  min-width: 200px;
  box-shadow: 0 12px 28px rgba(0,0,0,0.14);
}
.inline-status-menu__item {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 6px 10px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.82rem;
  text-align: left;
}
.inline-status-menu__item:hover { background: var(--color-surface-3); }
.inline-status-menu__item.active { font-weight: 600; }
.inline-status-menu__item.status-approval    { color: #b45309; }
.inline-status-menu__item.status-in_progress { color: #1d4ed8; }
.inline-status-menu__item.status-completed   { color: #166534; }

/* Type badge */
.type-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  white-space: nowrap;
}
.type-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; opacity: 0.85; flex-shrink: 0; }
.type-badge.type-general_contractor { background: rgba(2,119,189,0.12); color: #01579b; }
.type-badge.type-subcontractor      { background: rgba(245,124,0,0.15); color: #bf360c; }
.type-badge.type-services           { background: rgba(0,137,123,0.15); color: #00695c; }
.type-badge.type-labor              { background: rgba(106,27,154,0.15); color: #4a148c; }
/* Fallback for any legacy/unknown type code from DB */
.type-badge.type-other,
.type-badge[class*="type-"]:not(.type-general_contractor):not(.type-subcontractor):not(.type-services):not(.type-labor) {
  background: rgba(96,125,139,0.15);
  color: #37474f;
}
.filter-pill.type-general_contractor { background: rgba(2,119,189,0.15); color: #01579b; }
.filter-pill.type-subcontractor      { background: rgba(245,124,0,0.18); color: #bf360c; }
.filter-pill.type-services           { background: rgba(0,137,123,0.18); color: #00695c; }
.filter-pill.type-labor              { background: rgba(106,27,154,0.18); color: #4a148c; }

/* Avatars (compact) */
.user-avatar {
  width: 24px; height: 24px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.62rem;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
  background: #607d8b;
}
.user-avatar.xs { width: 22px; height: 22px; font-size: 0.58rem; }
.avatar-blue   { background: #1976d2; }
.avatar-teal   { background: #00897b; }
.avatar-amber  { background: #f57c00; }
.avatar-pink   { background: #d81b60; }
.avatar-purple { background: #6a1b9a; }
.avatar-green  { background: #2e7d32; }
.avatar-red    { background: #c62828; }
.avatar-indigo { background: #3949ab; }

.contracts-footer {
  padding: 8px 14px;
  border-top: 1px solid var(--color-border-subtle);
  text-align: right;
}

/* ============================================================
   Modal form
   ============================================================ */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.4);
  z-index: 9100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}
.contract-form-modal {
  width: min(640px, 100%);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-radius: 14px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid var(--color-border-subtle);
}
.modal-header h3 { margin: 0; font-size: 1.05rem; }
.modal-body {
  padding: 16px 18px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 18px;
  border-top: 1px solid var(--color-border-subtle);
  margin: 12px -18px -16px;
}
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.form-group label {
  display: block;
  font-size: 0.74rem;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  font-weight: 600;
  color: var(--color-text-muted);
  margin-bottom: 4px;
}
.req { color: #c62828; }
.is-invalid { border-color: #c62828 !important; }
.input-with-suffix {
  position: relative;
  display: flex;
  align-items: center;
}
.input-with-suffix input { padding-right: 28px; }
.input-suffix {
  position: absolute;
  right: 10px;
  color: var(--color-text-muted);
  font-weight: 600;
  pointer-events: none;
}

@media (max-width: 800px) {
  .form-row { grid-template-columns: 1fr; }
}
@media (max-width: 600px) {
  .contracts-search { flex-basis: 100%; margin-left: 0; }
}
</style>


