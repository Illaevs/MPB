<template>
  <section class="task-module-topbar tb">
    <!-- Row 1: title · search · filters · create -->
    <div class="tb__row tb__row--primary">
      <h1 class="tb__title">Задачи</h1>

      <label class="tb__search">
        <i class="fas fa-search"></i>
        <input
          v-model.trim="filters.search"
          type="search"
          placeholder="Поиск по названию, описанию..."
          @input="onSearchInput"
        />
        <button
          v-if="filters.search"
          type="button"
          class="tb__search-clear"
          @click="clearSearch"
          title="Очистить"
        >
          <i class="fas fa-times"></i>
        </button>
      </label>

      <!-- Sort group -->
      <div class="tb__sort">
        <button
          type="button"
          class="tb__sort-dir"
          :title="taskSort.dir === 'asc' ? 'По возрастанию' : 'По убыванию'"
          @click="toggleTaskSortDir"
        >
          <i class="fas" :class="taskSort.dir === 'asc' ? 'fa-arrow-up-short-wide' : 'fa-arrow-down-wide-short'"></i>
        </button>
        <select v-model="taskSort.by" class="tb__sort-select" @change="onTaskSortChange">
          <option value="created_at">Сначала новые</option>
          <option value="number">По номеру</option>
          <option value="due_date">По сроку</option>
          <option value="priority">По приоритету</option>
          <option value="status">По статусу</option>
          <option value="title">По названию</option>
          <option value="budget">По бюджету</option>
        </select>
      </div>

      <!-- View segmented -->
      <div class="tb__segmented" role="tablist" aria-label="Вид задач">
        <button
          type="button"
          class="tb__seg-btn"
          :class="{ 'tb__seg-btn--active': taskLayout === 'list' }"
          @click="setTaskLayout('list')"
          title="Список"
        >
          <i class="fas fa-list-ul"></i>
        </button>
        <button
          type="button"
          class="tb__seg-btn"
          :class="{ 'tb__seg-btn--active': taskLayout === 'kanban' }"
          @click="setTaskLayout('kanban')"
          title="Канбан"
        >
          <i class="fas fa-table-columns"></i>
        </button>
        <button
          type="button"
          class="tb__seg-btn"
          :class="{ 'tb__seg-btn--active': taskLayout === 'matrix' }"
          @click="setTaskLayout('matrix')"
          title="Матрица"
        >
          <i class="fas fa-border-all"></i>
        </button>
      </div>

      <!-- Pager -->
      <div class="tb__pager">
        <button
          type="button"
          class="tb__pager-arrow"
          :disabled="loading || taskPagination.page <= 1"
          @click="goToPrevTaskPage"
          title="Предыдущая"
        >
          <i class="fas fa-chevron-left"></i>
        </button>
        <span class="tb__pager-label">{{ taskPagination.page }}/{{ totalPages }}</span>
        <button
          type="button"
          class="tb__pager-arrow"
          :disabled="loading || !taskPagination.hasNext"
          @click="goToNextTaskPage"
          title="Следующая"
        >
          <i class="fas fa-chevron-right"></i>
        </button>
        <select v-model.number="taskPagination.pageSize" class="tb__pager-size" @change="onTaskPageSizeChange" title="На странице">
          <option :value="10">10</option>
          <option :value="20">20</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
          <option :value="200">200</option>
        </select>
        <span class="tb__total tb__hide-lg">Всего: <b>{{ taskPagination.total }}</b></span>
      </div>

      <div class="tb__filter-wrap">
        <button
          type="button"
          class="tb__btn tb__btn--ghost"
          :class="{ 'tb__btn--active': hasActiveTaskFilters }"
          @click.stop="filtersOpen = !filtersOpen"
        >
          <i class="fas fa-filter"></i>
          <span>Фильтры</span>
          <span v-if="activeTaskFiltersSummary.length" class="tb__badge">{{ activeTaskFiltersSummary.length }}</span>
        </button>
        <transition name="pop">
          <div
            v-if="filtersOpen"
            class="tb__filter-popover"
            v-click-outside="() => filtersOpen = false"
          >
            <div class="tb__filter-head">
              <span><i class="fas fa-filter"></i> Фильтры</span>
              <button v-if="hasActiveTaskFilters" type="button" class="tb__filter-reset" @click="clearTaskFilters">
                Сброс
              </button>
            </div>

            <div class="tb__filter-row">
              <label class="tb__filter-label">Статус</label>
              <div class="tb__chip-group">
                <button
                  v-for="opt in statusFilterOptions"
                  :key="opt.value"
                  type="button"
                  class="tb__chip"
                  :class="{ 'tb__chip--active': filters.status === opt.value }"
                  @click="setStatusFilter(opt.value)"
                >{{ opt.label }}</button>
              </div>
            </div>

            <div class="tb__filter-row">
              <label class="tb__filter-label">Приоритет</label>
              <div class="tb__chip-group">
                <button
                  v-for="opt in priorityFilterOptions"
                  :key="opt.value"
                  type="button"
                  class="tb__chip"
                  :class="['tb__chip--prio-' + opt.value, { 'tb__chip--active': filters.priority === opt.value }]"
                  @click="setPriorityFilter(opt.value)"
                >{{ opt.label }}</button>
              </div>
            </div>

            <div class="tb__filter-row">
              <label class="tb__filter-label">Проект</label>
              <select v-model="filters.deal_id" class="tb__filter-select" @change="applyTaskFilters">
                <option value="">Все проекты</option>
                <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.title }}</option>
              </select>
            </div>

            <div class="tb__filter-row">
              <label class="tb__filter-label">Ответственный</label>
              <select v-model="filters.assigned_to_user_id" class="tb__filter-select" @change="applyTaskFilters">
                <option value="">Любой</option>
                <option v-for="u in users" :key="u.id" :value="u.id">{{ u.full_name }}</option>
              </select>
            </div>

            <div class="tb__filter-row tb__filter-row--split">
              <div>
                <label class="tb__filter-label">Срок с</label>
                <input type="date" v-model="filters.due_date_from" class="tb__filter-select" @change="applyTaskFilters" />
              </div>
              <div>
                <label class="tb__filter-label">по</label>
                <input type="date" v-model="filters.due_date_to" class="tb__filter-select" @change="applyTaskFilters" />
              </div>
            </div>

            <label class="tb__filter-check">
              <input type="checkbox" v-model="filters.overdue" @change="applyTaskFilters" />
              <span>Только просроченные</span>
            </label>
          </div>
        </transition>
      </div>

      <button type="button" class="tb__btn tb__btn--primary" @click="openCreateTaskModal()">
        <i class="fas fa-plus"></i>
        <span>Новая задача</span>
      </button>
    </div>

    <!-- Row 2: active filter chips (visible only when filters are applied) -->
    <div v-if="hasActiveTaskFilters" class="tb__row tb__row--chips">
      <span v-for="filterItem in activeTaskFiltersSummary" :key="filterItem.key" class="tb__filter-pill">
        {{ filterItem.label }}
      </span>
      <button type="button" class="tb__filter-pill tb__filter-pill--clear" @click="clearTaskFilters">
        <i class="fas fa-rotate-left"></i><span>Сбросить</span>
      </button>
    </div>
  </section>
</template>

<script>
import { ref } from 'vue'

const clickOutside = {
  beforeMount(el, binding) {
    el._co = (e) => { if (!(el === e.target || el.contains(e.target))) binding.value(e) }
    setTimeout(() => document.addEventListener('click', el._co), 0)
  },
  unmounted(el) { document.removeEventListener('click', el._co) }
}

const statusFilterOptions = [
  { value: '', label: 'Все' },
  { value: 'new', label: 'Новая' },
  { value: 'in_progress', label: 'В работе' },
  { value: 'pending', label: 'Ожидает' },
  { value: 'completed', label: 'Завершена' },
  { value: 'cancelled', label: 'Отменена' },
  { value: 'deferred', label: 'Отложена' }
]

const priorityFilterOptions = [
  { value: '', label: 'Любой' },
  { value: 'low', label: 'Низкий' },
  { value: 'normal', label: 'Нормальный' },
  { value: 'high', label: 'Высокий' },
  { value: 'urgent', label: 'Срочный' }
]

export default {
  name: 'TasksToolbar',
  directives: { 'click-outside': clickOutside },
  props: { state: { type: Object, required: true } },
  setup(props) {
    const s = props.state
    const filtersOpen = ref(false)
    const clearSearch = () => { s.filters.value.search = ''; s.onSearchInput() }
    const setStatusFilter = (v) => { s.filters.value.status = v; s.applyTaskFilters() }
    const setPriorityFilter = (v) => { s.filters.value.priority = v; s.applyTaskFilters() }
    return {
      ...s,
      filtersOpen,
      statusFilterOptions,
      priorityFilterOptions,
      clearSearch,
      setStatusFilter,
      setPriorityFilter
    }
  }
}
</script>

<style>
/* ============================================================
   TOOLBAR — clean two-row layout with uniform controls
   `.tb` is namespaced so it overrides Tasks.vue's older
   .task-module-topbar-* rules without colliding.
   !important on layout/dimensions because parent SFC styles
   are injected after this file.
   ============================================================ */
.task-module-topbar.tb {
  padding: 0 !important;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle) !important;
  border-bottom: 0 !important;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0 !important;
  box-shadow: none !important;
  /* Establish a stacking context above .task-module-main so the
     filter popover overlays the list below it. */
  position: relative;
  z-index: 20;
}

.tb__row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
}
.tb__row--primary {
  flex-wrap: wrap;
}
.tb__row--chips {
  border-top: 1px solid var(--color-border-subtle);
  padding: 10px 20px;
  flex-wrap: wrap;
  gap: 6px;
}

.tb__title {
  margin: 0;
  font-size: var(--text-xl);
  font-weight: var(--fw-bold);
  color: var(--color-text);
  margin-right: 4px;
}

.tb__label {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
  font-weight: var(--fw-semibold);
}

.tb__spacer { flex: 1; }

/* ---------- SEARCH ---------- */
.tb__search {
  flex: 1;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 38px;
  padding: 0 14px;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  color: var(--color-text);
  transition: border-color var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out);
}
.tb__search:focus-within {
  border-color: var(--color-primary);
  background: var(--color-surface);
  box-shadow: var(--shadow-focus);
}
.tb__search > i {
  color: var(--color-text-subtle);
}
.tb__search input {
  flex: 1;
  border: 0;
  outline: 0;
  background: transparent;
  font-size: var(--text-md);
  color: var(--color-text);
  padding: 0;
  min-width: 0;
}
.tb__search input::placeholder { color: var(--color-text-subtle); }
.tb__search-clear {
  border: 0;
  background: transparent;
  color: var(--color-text-subtle);
  cursor: pointer;
  padding: 4px;
  border-radius: var(--radius-sm);
}
.tb__search-clear:hover { color: var(--color-text); background: var(--color-surface-3); }

/* ---------- BUTTONS ---------- */
.tb__btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 38px;
  padding: 0 14px;
  border-radius: var(--radius-md);
  font-size: var(--text-md);
  font-weight: var(--fw-medium);
  cursor: pointer;
  white-space: nowrap;
  line-height: 1;
  transition: background var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}
.tb__btn i { font-size: var(--text-base); }

.tb__btn--ghost {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-text);
}
.tb__btn--ghost:hover {
  background: var(--color-surface-2);
  border-color: var(--color-border-strong);
}
.tb__btn--ghost.tb__btn--active {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.tb__btn--primary {
  background: var(--color-primary);
  border: 1px solid var(--color-primary);
  color: var(--color-on-primary);
}
.tb__btn--primary:hover {
  background: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
}

.tb__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 6px;
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-size: var(--text-xs);
  font-weight: var(--fw-bold);
  border-radius: var(--radius-pill);
}
.tb__btn--active .tb__badge {
  background: var(--color-on-primary);
  color: var(--color-primary);
}

/* ---------- SORT ---------- */
.tb__sort {
  display: inline-flex;
  align-items: center;
  height: 34px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  overflow: hidden;
}
.tb__sort-dir,
.tb__sort-select {
  height: 100%;
  border: 0;
  background: transparent;
  font-size: var(--text-md);
  color: var(--color-text);
  padding: 0 10px;
  cursor: pointer;
  outline: 0;
}
.tb__sort-dir {
  color: var(--color-text-muted);
  border-right: 1px solid var(--color-border-subtle);
}
.tb__sort-dir:hover { background: var(--color-surface-2); color: var(--color-text); }
.tb__sort-select {
  padding-right: 28px;
}

/* ---------- SEGMENTED VIEW ---------- */
.tb__segmented {
  display: inline-flex;
  align-items: center;
  height: 34px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  overflow: hidden;
}
.tb__seg-btn {
  height: 100%;
  width: 36px;
  border: 0;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-md);
  transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}
.tb__seg-btn + .tb__seg-btn { border-left: 1px solid var(--color-border-subtle); }
.tb__seg-btn:hover { background: var(--color-surface-2); color: var(--color-text); }
.tb__seg-btn--active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

/* ---------- PAGER — unified pill (mirrors Leads pager frame) ---------- */
.tb__pager {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 34px;
  padding: 0 6px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}
.tb__pager-arrow {
  width: 28px;
  height: 28px;
  border: 0;
  background: transparent;
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
  transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}
.tb__pager-arrow:hover:not(:disabled) {
  background: var(--color-surface-2);
  color: var(--color-text);
}
.tb__pager-arrow:disabled { opacity: 0.4; cursor: default; }
.tb__pager-label {
  min-width: 44px;
  text-align: center;
  font-variant-numeric: tabular-nums;
  font-size: var(--text-sm);
  color: var(--color-text);
  font-weight: var(--fw-medium);
}
.tb__pager-size {
  height: 28px;
  padding: 0 6px;
  border: 0;
  border-left: 1px solid var(--color-border-subtle);
  background: transparent;
  font-size: var(--text-sm);
  color: var(--color-text);
  outline: 0;
  cursor: pointer;
  margin-left: 2px;
}
.tb__total {
  margin-left: 4px;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}
.tb__total b { color: var(--color-text); font-weight: var(--fw-semibold); }

/* ---------- ACTIVE FILTER CHIPS ROW ---------- */
.tb__filter-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
}
.tb__filter-pill--clear {
  background: transparent;
  border: 0;
  color: var(--color-text-muted);
  cursor: pointer;
}
.tb__filter-pill--clear:hover { color: var(--color-text); background: var(--color-surface-2); }

/* ---------- FILTERS POPOVER (mirrors Calendar) ---------- */
.tb__filter-wrap { position: relative; z-index: 30; }
.tb__filter-popover {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 1000;
  width: 340px;
  padding: var(--space-3);
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.tb__filter-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: var(--fw-semibold);
  font-size: var(--text-sm);
  color: var(--color-text);
}
.tb__filter-head i { margin-right: 6px; color: var(--color-text-muted); }
.tb__filter-reset {
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-muted);
  padding: 4px 10px;
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out);
}
.tb__filter-reset:hover { background: var(--color-surface-2); color: var(--color-text); }
.tb__filter-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.tb__filter-row--split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.tb__filter-row--split > div { display: flex; flex-direction: column; gap: 6px; }
.tb__filter-label {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
  font-weight: var(--fw-semibold);
}
.tb__chip-group { display: flex; flex-wrap: wrap; gap: 6px; }
.tb__chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--color-border-subtle);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: var(--text-xs);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}
.tb__chip:hover { background: var(--color-surface-2); }
.tb__chip--active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}
.tb__chip--prio-urgent.tb__chip--active { background: var(--color-danger); border-color: var(--color-danger); }
.tb__chip--prio-high.tb__chip--active { background: var(--color-warning); border-color: var(--color-warning); }
.tb__filter-select {
  height: 34px;
  padding: 0 10px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text);
  font-size: var(--text-sm);
  outline: 0;
  cursor: pointer;
}
.tb__filter-select:focus {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}
.tb__filter-check {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: var(--text-sm);
  color: var(--color-text);
  cursor: pointer;
  padding: 6px 0;
}
.tb__filter-check input { accent-color: var(--color-primary); }

.pop-enter-active, .pop-leave-active { transition: opacity var(--dur-fast) var(--ease-out), transform var(--dur-fast) var(--ease-out); }
.pop-enter-from, .pop-leave-to { opacity: 0; transform: translateY(-4px); }

/* Hide on smaller screens to keep row 1 tidy */
.tb__hide-lg { display: inline-flex; }
@media (max-width: 1280px) {
  .tb__hide-lg { display: none; }
}

/* ---------- RESPONSIVE ---------- */
@media (max-width: 900px) {
  .tb__row { flex-wrap: wrap; }
  .tb__title { width: 100%; }
  .tb__search { flex: 1 1 100%; order: 2; }
  .tb__filter-popover { width: 290px; }
}
</style>
