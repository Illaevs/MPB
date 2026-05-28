<template>
  <div class="calendar-view d-flex flex-column h-100" @keydown="handleKeydown" tabindex="0" ref="calendarRoot">
    <!-- Single-line toolbar -->
    <div class="card toolbar-card flex-shrink-0">
      <div class="toolbar-row">
        <h2 class="m-0 toolbar-title">Календарь</h2>

        <!-- Today summary chip -->
        <Tooltip :text="todaySummaryTooltip">
          <button type="button" class="today-chip" :class="{ urgent: todayStats.urgent > 0 }" @click="goTodayDay">
            <i class="fas fa-calendar-day"></i>
            <span><b>Сегодня:</b> {{ todayStats.total }}</span>
            <span v-if="todayStats.urgent > 0" class="today-chip-urgent">+{{ todayStats.urgent }} срочн.</span>
          </button>
        </Tooltip>

        <div class="view-switcher">
          <button
            v-for="mode in viewModes"
            :key="mode.value"
            class="view-btn"
            :class="{ active: viewMode === mode.value }"
            @click="setViewMode(mode.value)"
            :title="mode.label"
          >
            <i :class="mode.icon"></i>
            <span class="hide-md">{{ mode.label }}</span>
          </button>
        </div>

        <div class="calendar-nav">
          <button class="btn btn-sm btn-icon" @click="prevPeriod" title="Назад">
            <i class="fas fa-chevron-left"></i>
          </button>
          <span class="period-label">{{ periodLabel }}</span>
          <button class="btn btn-sm btn-icon" @click="nextPeriod" title="Вперёд">
            <i class="fas fa-chevron-right"></i>
          </button>
        </div>

        <button class="btn btn-sm btn-outline-primary today-btn" @click="goToday" title="К сегодняшней дате">
          <i class="fas fa-bullseye"></i>
          <span class="hide-md">Сегодня <span class="today-num">{{ todayDayNumber }}</span></span>
        </button>

        <!-- Filters popover trigger -->
        <div class="filter-wrap">
          <button
            class="btn btn-sm"
            :class="hasActiveFilters ? 'btn-primary' : 'btn-icon'"
            @click="filtersOpen = !filtersOpen"
            title="Фильтры"
          >
            <i class="fas fa-filter"></i>
            <span v-if="hasActiveFilters" class="filter-active-dot">{{ activeFiltersCount }}</span>
          </button>
          <transition name="pop">
            <div v-if="filtersOpen" class="filter-popover" v-click-outside="() => filtersOpen = false">
              <div class="filter-popover-head">
                <span><i class="fas fa-filter mr-1"></i>Фильтры</span>
                <button v-if="hasActiveFilters" class="btn btn-sm btn-outline-secondary" @click="resetFilters">Сброс</button>
              </div>
              <div class="filter-row">
                <label class="filter-label">Тип</label>
                <div class="chip-group">
                  <button class="chip" :class="{ active: filters.types.tasks }" @click="filters.types.tasks = !filters.types.tasks">
                    <i class="fas fa-check-square mr-1"></i>Задачи
                  </button>
                  <button v-if="canSeeHearings" class="chip" :class="{ active: filters.types.hearings }" @click="filters.types.hearings = !filters.types.hearings">
                    <i class="fas fa-gavel mr-1"></i>Заседания
                  </button>
                </div>
              </div>
              <div class="filter-row">
                <label class="filter-label">Статус</label>
                <div class="chip-group">
                  <button v-for="opt in statusFilterOptions" :key="opt.value" class="chip" :class="{ active: filters.statuses.includes(opt.value) }" @click="toggleArrayFilter('statuses', opt.value)">
                    {{ opt.label }}
                  </button>
                </div>
              </div>
              <div class="filter-row">
                <label class="filter-label">Приоритет</label>
                <div class="chip-group">
                  <button v-for="opt in priorityFilterOptions" :key="opt.value" class="chip" :class="['priority-' + opt.value, { active: filters.priorities.includes(opt.value) }]" @click="toggleArrayFilter('priorities', opt.value)">
                    {{ opt.label }}
                  </button>
                </div>
              </div>
              <div class="filter-row">
                <label class="filter-label">Исполнитель</label>
                <select v-model="filters.assignee" class="form-control form-control-sm">
                  <option value="">Любой</option>
                  <option v-if="activeUserId" value="__me__">Только мои</option>
                  <option v-for="u in users" :key="u.id" :value="u.id">{{ u.full_name }}</option>
                </select>
              </div>
              <div class="filter-row">
                <label class="filter-label">Боковая панель</label>
                <label class="check-label">
                  <input type="checkbox" v-model="showUnscheduled"> Нераспределённые
                </label>
              </div>
            </div>
          </transition>
        </div>

        <!-- Color legend trigger -->
        <div class="filter-wrap">
          <button class="btn btn-sm btn-icon" @click="legendOpen = !legendOpen" title="Условные обозначения">
            <i class="fas fa-circle-question"></i>
          </button>
          <transition name="pop">
            <div v-if="legendOpen" class="legend-popover" v-click-outside="() => legendOpen = false">
              <div class="legend-head"><i class="fas fa-palette mr-1"></i>Условные обозначения</div>
              <div v-for="item in colorLegend" :key="item.key" class="legend-row">
                <span class="legend-swatch" :class="item.cssClass"></span>
                <span>{{ item.label }}</span>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </div>

    <!-- Workspace -->
    <div class="workspace flex-grow-1 overflow-hidden" :class="{ 'with-sidebar': showUnscheduled }">
      <div class="card calendar-area">
        <div v-if="loading" class="loading-state">
          <i class="fas fa-spinner fa-spin fa-2x"></i>
          <span>Загрузка...</span>
        </div>

        <template v-else>
          <!-- ========== MONTH ========== -->
          <template v-if="viewMode === 'month'">
            <div class="cal-desktop">
              <div class="weekdays">
                <div v-for="(day, idx) in weekDays" :key="day" class="weekday" :class="{ weekend: idx >= 5, today: weekTodayIdx === idx }">
                  {{ day }}
                </div>
              </div>
              <div class="month-grid">
                <div
                  v-for="(cell, cellIdx) in calendarDays"
                  :key="cell.key"
                  class="day-cell"
                  :class="{ muted: !cell.inCurrentMonth, today: cell.isToday, weekend: cell.isWeekend, focused: focusedCellIndex === cellIdx, dropping: dragOverKey === cell.key }"
                  :tabindex="cell.inCurrentMonth ? 0 : -1"
                  @focus="focusedCellIndex = cellIdx"
                  @keydown.enter.prevent="expandDay(cell)"
                  @dragover.prevent="onDragOver(cell)"
                  @dragleave="dragOverKey = null"
                  @drop.prevent="onDrop(cell)"
                  role="gridcell"
                  :aria-label="cellAriaLabel(cell)"
                >
                  <div class="day-head">
                    <span class="day-num" :class="{ 'today-num': cell.isToday }">{{ cell.dayNumber }}</span>
                    <div class="day-actions">
                      <span v-if="cell.tasks.length" class="day-count">{{ cell.tasks.length }}</span>
                      <button v-if="cell.inCurrentMonth" class="add-btn" @click.stop="openQuickCreate(cell)" title="Создать задачу">
                        <i class="fas fa-plus"></i>
                      </button>
                    </div>
                  </div>
                  <div class="day-tasks">
                    <button
                      v-for="item in cell.visibleTasks"
                      :key="item.id"
                      class="cal-task"
                      :class="getTaskClass(item)"
                      :draggable="canDrag(item)"
                      @dragstart="onDragStart($event, item)"
                      @dragend="onDragEnd"
                      @click.stop="openTask(item)"
                    >
                      <i class="task-icon" :class="getTaskIcon(item)"></i>
                      <span class="task-title">{{ truncateTitle(item.title) }}</span>
                      <span v-if="getTimeLabel(item)" class="task-time">{{ getTimeLabel(item) }}</span>
                    </button>
                    <button v-if="cell.overflowCount > 0" class="cal-overflow" @click.stop="expandDay(cell)">
                      +{{ cell.overflowCount }} ещё
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div class="cal-mobile-agenda">
              <div v-if="agendaDays.length === 0" class="empty-state">
                <i class="fas fa-calendar-xmark"></i>
                <p>Задач с дедлайнами пока нет</p>
              </div>
              <div v-for="aDay in agendaDays" :key="aDay.key" class="agenda-day">
                <div class="agenda-day-head" :class="{ today: aDay.isToday }">
                  <span class="agenda-day-num" :class="{ 'today-num': aDay.isToday }">{{ aDay.dayNumber }}</span>
                  <span class="agenda-day-label">{{ aDay.weekdayName }}, {{ aDay.monthDay }}</span>
                  <button class="add-btn" @click="openQuickCreate(aDay)"><i class="fas fa-plus"></i></button>
                </div>
                <div class="agenda-day-tasks">
                  <button v-for="item in aDay.tasks" :key="item.id" class="cal-task agenda" :class="getTaskClass(item)" @click="openTask(item)">
                    <i class="task-icon" :class="getTaskIcon(item)"></i>
                    <div class="task-content">
                      <span class="task-title">{{ item.title }}</span>
                      <span class="task-meta">{{ getTaskMeta(item) }}</span>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          </template>

          <!-- ========== WEEK ========== -->
          <template v-if="viewMode === 'week'">
            <div class="weekdays">
              <div v-for="(day, idx) in weekDays" :key="day" class="weekday" :class="{ weekend: idx >= 5, today: weekDaysCells[idx]?.isToday }">
                {{ day }}<span v-if="weekDaysCells[idx]?.isToday" class="today-mark">·</span>
              </div>
            </div>
            <div class="week-grid">
              <div
                v-for="(cell, cellIdx) in weekDaysCells"
                :key="cell.key"
                class="day-cell week-cell"
                :class="{ today: cell.isToday, weekend: cell.isWeekend, focused: focusedCellIndex === cellIdx, dropping: dragOverKey === cell.key }"
                tabindex="0"
                @focus="focusedCellIndex = cellIdx"
                @keydown.enter.prevent="expandDay(cell)"
                @dragover.prevent="onDragOver(cell)"
                @dragleave="dragOverKey = null"
                @drop.prevent="onDrop(cell)"
              >
                <div class="day-head">
                  <span class="day-num" :class="{ 'today-num': cell.isToday }">{{ cell.dayNumber }}</span>
                  <div class="day-actions">
                    <span v-if="cell.tasks.length" class="day-count">{{ cell.tasks.length }}</span>
                    <button class="add-btn" @click.stop="openQuickCreate(cell)"><i class="fas fa-plus"></i></button>
                  </div>
                </div>
                <div class="day-tasks">
                  <button
                    v-for="item in cell.tasks"
                    :key="item.id"
                    class="cal-task"
                    :class="getTaskClass(item)"
                    :draggable="canDrag(item)"
                    @dragstart="onDragStart($event, item)"
                    @dragend="onDragEnd"
                    @click.stop="openTask(item)"
                  >
                    <i class="task-icon" :class="getTaskIcon(item)"></i>
                    <span class="task-title">{{ truncateTitle(item.title, 28) }}</span>
                    <span v-if="getTimeLabel(item)" class="task-time">{{ getTimeLabel(item) }}</span>
                  </button>
                </div>
              </div>
            </div>
          </template>

          <!-- ========== DAY (timeline) ========== -->
          <template v-if="viewMode === 'day'">
            <div class="day-view">
              <div class="day-view-head" :class="{ today: dayViewCell.isToday }">
                <span class="day-view-num" :class="{ 'today-num': dayViewCell.isToday }">{{ dayViewCell.dayNumber }}</span>
                <span class="day-view-label">{{ dayViewFullLabel }}</span>
                <button class="btn btn-sm btn-primary" @click="openQuickCreate(dayViewCell)">
                  <i class="fas fa-plus mr-1"></i> Новая задача
                </button>
              </div>

              <div v-if="!dayViewCell.tasks.length" class="empty-state">
                <i class="fas fa-calendar-check"></i>
                <p>На этот день задач нет</p>
              </div>

              <div v-else class="day-timeline">
                <div v-if="dayViewAllDay.length" class="all-day-section">
                  <div class="all-day-label">Весь день</div>
                  <div class="all-day-tasks">
                    <button
                      v-for="item in dayViewAllDay"
                      :key="item.id"
                      class="cal-task agenda"
                      :class="getTaskClass(item)"
                      :draggable="canDrag(item)"
                      @dragstart="onDragStart($event, item)"
                      @dragend="onDragEnd"
                      @click.stop="openTask(item)"
                    >
                      <i class="task-icon" :class="getTaskIcon(item)"></i>
                      <div class="task-content">
                        <span class="task-title">{{ item.title }}</span>
                        <span class="task-meta">{{ getTaskMeta(item) }}</span>
                      </div>
                    </button>
                  </div>
                </div>
                <div class="hours-grid">
                  <div v-for="hour in hours" :key="hour" class="hour-row">
                    <span class="hour-label">{{ String(hour).padStart(2, '0') }}:00</span>
                    <div class="hour-track">
                      <button
                        v-for="item in tasksByHour[hour] || []"
                        :key="item.id"
                        class="cal-task timed"
                        :class="getTaskClass(item)"
                        :style="hourPositionStyle(item)"
                        :draggable="canDrag(item)"
                        @dragstart="onDragStart($event, item)"
                        @dragend="onDragEnd"
                        @click.stop="openTask(item)"
                      >
                        <i class="task-icon" :class="getTaskIcon(item)"></i>
                        <span class="task-title">{{ truncateTitle(item.title, 36) }}</span>
                        <span class="task-time">{{ getTimeLabel(item) }}</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </template>
      </div>

      <!-- Unscheduled sidebar -->
      <aside v-if="showUnscheduled" class="card unscheduled-panel p-2">
        <div class="unscheduled-head">
          <span><i class="fas fa-inbox mr-1"></i>Нераспределённые</span>
          <button class="btn btn-sm btn-icon" @click="showUnscheduled = false" title="Скрыть"><i class="fas fa-times"></i></button>
        </div>
        <div v-if="loadingUnscheduled" class="p-2 d-flex flex-column gap-2">
          <SkeletonLoader v-for="i in 4" :key="i" height="48px" />
        </div>
        <div v-else-if="!unscheduledTasks.length" class="empty-state small">
          <i class="fas fa-check"></i>
          <p>Все задачи распределены</p>
          <small class="text-muted">Можно перетянуть сюда задачу из календаря, чтобы снять с неё дату</small>
        </div>
        <div v-else class="unscheduled-list" @dragover.prevent="dragOverKey = '__unscheduled__'" @drop.prevent="onDropUnscheduled">
          <button
            v-for="item in unscheduledTasks"
            :key="item.id"
            class="cal-task agenda"
            :class="getTaskClass(item)"
            :draggable="true"
            @dragstart="onDragStart($event, item)"
            @dragend="onDragEnd"
            @click.stop="openTask(item)"
          >
            <i class="task-icon" :class="getTaskIcon(item)"></i>
            <div class="task-content">
              <span class="task-title">{{ item.title }}</span>
              <span class="task-meta">{{ getTaskMeta(item) }}</span>
            </div>
          </button>
        </div>
      </aside>
    </div>

    <!-- Day detail modal -->
    <div v-if="expandedDay" class="modal-overlay" @click="expandedDay = null" @keydown.escape="expandedDay = null">
      <div class="modal-content modal-sm" @click.stop>
        <div class="modal-header">
          <h3>{{ expandedDayLabel }}</h3>
          <button class="btn btn-sm btn-icon" @click="expandedDay = null"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="expanded-task-list">
            <button v-for="item in expandedDay.tasks" :key="item.id" class="cal-task agenda" :class="getTaskClass(item)" @click="openTask(item)">
              <i class="task-icon" :class="getTaskIcon(item)"></i>
              <div class="task-content">
                <span class="task-title">{{ item.title }}</span>
                <span class="task-meta">{{ getTaskMeta(item) }}</span>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick create modal -->
    <div v-if="showQuickCreate" class="modal-overlay" @click="showQuickCreate = false" @keydown.escape="showQuickCreate = false">
      <div class="modal-content modal-sm" @click.stop>
        <div class="modal-header">
          <h3>Новая задача</h3>
          <button class="btn btn-sm btn-icon" @click="showQuickCreate = false"><i class="fas fa-times"></i></button>
        </div>
        <form @submit.prevent="saveQuickTask" class="modal-body">
          <div class="form-group mb-3">
            <label>Название *</label>
            <input v-model="quickForm.title" class="form-control" required autofocus />
          </div>
          <div class="row mb-3">
            <div class="col-md-4 form-group">
              <label>Дата</label>
              <input type="date" v-model="quickForm.due_date" class="form-control" />
            </div>
            <div class="col-md-4 form-group">
              <label>Время</label>
              <input type="time" v-model="quickForm.due_time" class="form-control" placeholder="—" />
            </div>
            <div class="col-md-4 form-group">
              <label>Приоритет</label>
              <select v-model="quickForm.priority" class="form-control">
                <option value="low">Низкий</option>
                <option value="normal">Нормальный</option>
                <option value="high">Высокий</option>
                <option value="urgent">Срочный</option>
              </select>
            </div>
          </div>
          <div class="form-group mb-3">
            <label>Исполнитель</label>
            <select v-model="quickForm.assigned_to_user_id" class="form-control">
              <option :value="null">Не назначен</option>
              <option v-for="u in users" :key="u.id" :value="u.id">{{ u.full_name }}</option>
            </select>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-sm btn-secondary" @click="showQuickCreate = false">Отмена</button>
            <button type="submit" class="btn btn-sm btn-primary" :disabled="quickSaving">
              <i v-if="quickSaving" class="fas fa-spinner fa-spin mr-1"></i>
              Создать
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Edit drawer -->
    <transition name="drawer">
      <div v-if="editingTask" class="drawer-overlay" @click.self="closeEditDrawer">
        <div class="drawer">
          <div class="drawer-head">
            <div>
              <div class="text-muted small">{{ editingTask.item_type === 'hearing' ? 'Заседание' : 'Задача' }}</div>
              <h4 class="m-0">{{ editingTask.title }}</h4>
            </div>
            <button class="btn btn-sm btn-icon" @click="closeEditDrawer"><i class="fas fa-times"></i></button>
          </div>
          <div class="drawer-body">
            <template v-if="editingTask.item_type === 'hearing'">
              <div class="drawer-meta">
                <p><b>Дата:</b> {{ formatDateRu(editingTask.due_date) }}</p>
                <p v-if="editingTask.event_time"><b>Время:</b> {{ editingTask.event_time.slice(0,5) }}</p>
                <p v-if="editingTask.courtroom"><b>Зал:</b> {{ editingTask.courtroom }}</p>
              </div>
              <button class="btn btn-sm btn-outline-primary mt-3" @click="goToHearing(editingTask)">
                <i class="fas fa-arrow-up-right-from-square mr-1"></i> Перейти в дело
              </button>
            </template>
            <template v-else>
              <div class="form-group mb-2">
                <label>Название</label>
                <input v-model="editForm.title" class="form-control" />
              </div>
              <div class="row mb-2">
                <div class="col-md-6 form-group">
                  <label>Статус</label>
                  <select v-model="editForm.status" class="form-control">
                    <option value="new">Новая</option>
                    <option value="in_progress">В работе</option>
                    <option value="pending">Ожидает</option>
                    <option value="completed">Завершена</option>
                    <option value="cancelled">Отменена</option>
                    <option value="deferred">Отложена</option>
                  </select>
                </div>
                <div class="col-md-6 form-group">
                  <label>Приоритет</label>
                  <select v-model="editForm.priority" class="form-control">
                    <option value="low">Низкий</option>
                    <option value="normal">Нормальный</option>
                    <option value="high">Высокий</option>
                    <option value="urgent">Срочный</option>
                  </select>
                </div>
              </div>
              <div class="row mb-2">
                <div class="col-md-6 form-group">
                  <label>Дата</label>
                  <input type="date" v-model="editForm.due_date" class="form-control" />
                </div>
                <div class="col-md-6 form-group">
                  <label>Время</label>
                  <input type="time" v-model="editForm.due_time" class="form-control" />
                </div>
              </div>
              <div class="form-group mb-2">
                <label>Исполнитель</label>
                <select v-model="editForm.assigned_to_user_id" class="form-control">
                  <option :value="null">Не назначен</option>
                  <option v-for="u in users" :key="u.id" :value="u.id">{{ u.full_name }}</option>
                </select>
              </div>
              <div class="form-group mb-2">
                <label>Описание</label>
                <textarea v-model="editForm.description" rows="3" class="form-control"></textarea>
              </div>
            </template>
          </div>
          <div v-if="editingTask.item_type !== 'hearing'" class="drawer-footer">
            <button class="btn btn-sm btn-outline-secondary" @click="goToFullTask(editingTask)">
              <i class="fas fa-arrow-up-right-from-square mr-1"></i> Открыть полностью
            </button>
            <div class="d-flex gap-2 ml-auto">
              <button class="btn btn-sm btn-secondary" @click="closeEditDrawer">Отмена</button>
              <button class="btn btn-sm btn-primary" :disabled="savingEdit" @click="saveEdit">
                <i v-if="savingEdit" class="fas fa-spinner fa-spin mr-1"></i>
                Сохранить
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api'
import { getActiveUser, hasSectionAccess } from '../utils/permissions'
import { useToast } from '../composables/useToast'
import { useUsersStore } from '../stores/users'
import SkeletonLoader from '../components/ui/SkeletonLoader.vue'
import Tooltip from '../components/ui/Tooltip.vue'

const STORAGE_KEY = 'crm-calendar-prefs-v2'

const clickOutside = {
  beforeMount(el, binding) {
    el._co = (e) => { if (!(el === e.target || el.contains(e.target))) binding.value(e) }
    setTimeout(() => document.addEventListener('click', el._co), 0)
  },
  unmounted(el) { document.removeEventListener('click', el._co) }
}

export default {
  name: 'Calendar',
  components: { SkeletonLoader, Tooltip },
  directives: { 'click-outside': clickOutside },
  setup() {
    const router = useRouter()
    const { error: toastError, success: toastSuccess } = useToast()
    const usersStore = useUsersStore()
    const calendarRoot = ref(null)

    // Reactive today
    const today = ref(new Date())
    let midnightTimer = null
    const scheduleMidnightUpdate = () => {
      const now = new Date()
      const tomorrow = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1)
      const ms = tomorrow.getTime() - now.getTime() + 100
      midnightTimer = setTimeout(() => { today.value = new Date(); scheduleMidnightUpdate() }, ms)
    }

    const activeUser = ref(getActiveUser())
    const activeUserId = computed(() => activeUser.value?.id || '')
    const canSeeHearings = computed(() => hasSectionAccess('legal_work'))

    // Persisted prefs
    const loadPrefs = () => {
      try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') } catch (e) { return {} }
    }
    const prefs = loadPrefs()

    const viewMode = ref(prefs.viewMode || 'month')
    const showUnscheduled = ref(!!prefs.showUnscheduled)
    const filters = reactive({
      types: { tasks: prefs.types?.tasks ?? true, hearings: prefs.types?.hearings ?? true },
      statuses: prefs.statuses ?? [],   // empty = all
      priorities: prefs.priorities ?? [], // empty = all
      assignee: prefs.assignee ?? '',     // '', '__me__', or user_id
    })

    const persist = () => {
      const data = {
        viewMode: viewMode.value,
        showUnscheduled: showUnscheduled.value,
        types: filters.types,
        statuses: filters.statuses,
        priorities: filters.priorities,
        assignee: filters.assignee,
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
    }
    watch([viewMode, showUnscheduled, filters], persist, { deep: true })

    // Period state
    const currentMonth = ref(new Date(today.value.getFullYear(), today.value.getMonth(), 1))
    const currentWeekStart = ref(getMonday(today.value))
    const currentDay = ref(new Date(today.value.getFullYear(), today.value.getMonth(), today.value.getDate()))

    const tasks = ref([])
    const hearings = ref([])
    const unscheduledTasks = ref([])
    const loading = ref(false)
    const loadingUnscheduled = ref(false)
    const expandedDay = ref(null)
    const focusedCellIndex = ref(-1)
    const filtersOpen = ref(false)
    const legendOpen = ref(false)
    const dragOverKey = ref(null)
    let draggedTask = null
    const maxVisibleTasks = 3

    // Quick create + edit drawer
    const showQuickCreate = ref(false)
    const quickSaving = ref(false)
    const users = ref([])
    const quickForm = ref({ title: '', due_date: '', due_time: '', priority: 'normal', assigned_to_user_id: null })

    const editingTask = ref(null)
    const editForm = ref({ title: '', status: 'new', priority: 'normal', due_date: '', due_time: '', assigned_to_user_id: null, description: '' })
    const savingEdit = ref(false)

    const viewModes = [
      { value: 'month', label: 'Месяц', icon: 'fas fa-calendar' },
      { value: 'week', label: 'Неделя', icon: 'fas fa-calendar-week' },
      { value: 'day', label: 'День', icon: 'fas fa-calendar-day' },
    ]

    const weekDays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    const hours = Array.from({ length: 13 }, (_, i) => 8 + i) // 08..20

    const statusFilterOptions = [
      { value: 'new', label: 'Новые' },
      { value: 'in_progress', label: 'В работе' },
      { value: 'pending', label: 'Ожидают' },
      { value: 'completed', label: 'Завершённые' },
      { value: 'cancelled', label: 'Отменённые' },
      { value: 'deferred', label: 'Отложенные' },
    ]
    const priorityFilterOptions = [
      { value: 'low', label: 'Низкий' },
      { value: 'normal', label: 'Нормальный' },
      { value: 'high', label: 'Высокий' },
      { value: 'urgent', label: 'Срочный' },
    ]

    const colorLegend = [
      { key: 'new',         label: 'Новая',           cssClass: 'task--new' },
      { key: 'in_progress', label: 'В работе',        cssClass: 'task--in_progress' },
      { key: 'pending',     label: 'Ожидает',         cssClass: 'task--pending' },
      { key: 'completed',   label: 'Завершена',       cssClass: 'task--completed' },
      { key: 'cancelled',   label: 'Отменена',        cssClass: 'task--cancelled' },
      { key: 'deferred',    label: 'Отложена',        cssClass: 'task--deferred' },
      { key: 'hearing',     label: 'Судебное заседание', cssClass: 'task--hearing' },
    ]

    // Helpers
    function getMonday(d) {
      const date = new Date(d)
      const day = date.getDay()
      const diff = date.getDate() - day + (day === 0 ? -6 : 1)
      return new Date(date.getFullYear(), date.getMonth(), diff)
    }
    const formatDateKey = (date) => {
      const y = date.getFullYear(), m = String(date.getMonth() + 1).padStart(2, '0'), d = String(date.getDate()).padStart(2, '0')
      return `${y}-${m}-${d}`
    }
    const formatDateISO = formatDateKey
    const formatDateRu = (d) => d ? new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: 'long', year: 'numeric' }) : '—'
    const normalizeId = (v) => v ? String(v).replace(/-/g, '').toLowerCase() : ''

    // Date range
    const dateRange = computed(() => {
      if (viewMode.value === 'month') {
        const start = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth(), 1)
        const startDay = (start.getDay() + 6) % 7
        const gridStart = new Date(start); gridStart.setDate(start.getDate() - startDay)
        const gridEnd = new Date(gridStart); gridEnd.setDate(gridStart.getDate() + 41)
        return { from: formatDateISO(gridStart), to: formatDateISO(gridEnd) }
      }
      if (viewMode.value === 'week') {
        const end = new Date(currentWeekStart.value); end.setDate(end.getDate() + 6)
        return { from: formatDateISO(currentWeekStart.value), to: formatDateISO(end) }
      }
      return { from: formatDateISO(currentDay.value), to: formatDateISO(currentDay.value) }
    })

    // Period labels
    const periodLabel = computed(() => {
      if (viewMode.value === 'month') {
        const m = currentMonth.value.toLocaleDateString('ru-RU', { month: 'long' })
        return `${m.charAt(0).toUpperCase() + m.slice(1)} ${currentMonth.value.getFullYear()}`
      }
      if (viewMode.value === 'week') {
        const end = new Date(currentWeekStart.value); end.setDate(end.getDate() + 6)
        const sameYear = currentWeekStart.value.getFullYear() === end.getFullYear()
        const s = currentWeekStart.value.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
        const e = end.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
        return sameYear ? `${s} — ${e} ${end.getFullYear()}` : `${s} ${currentWeekStart.value.getFullYear()} — ${e} ${end.getFullYear()}`
      }
      return currentDay.value.toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
    })

    const todayDayNumber = computed(() => today.value.getDate())
    const weekTodayIdx = computed(() => {
      const d = today.value.getDay()
      return (d === 0 ? 6 : d - 1)
    })

    // Visibility filtering
    const visibleItems = computed(() => {
      const list = []
      if (filters.types.tasks) {
        let pool = tasks.value
        if (filters.statuses.length) pool = pool.filter(t => filters.statuses.includes(t.status))
        if (filters.priorities.length) pool = pool.filter(t => filters.priorities.includes(t.priority))
        if (filters.assignee === '__me__' && activeUserId.value) {
          pool = pool.filter(t => normalizeId(t.assigned_to_user_id) === normalizeId(activeUserId.value))
        } else if (filters.assignee && filters.assignee !== '__me__') {
          pool = pool.filter(t => normalizeId(t.assigned_to_user_id) === normalizeId(filters.assignee))
        }
        list.push(...pool)
      }
      if (filters.types.hearings && canSeeHearings.value) list.push(...hearings.value)
      return list
    })

    const tasksByDate = computed(() => {
      const map = {}
      visibleItems.value.forEach(item => {
        if (!item.due_date) return
        const key = formatDateKey(new Date(item.due_date))
        if (!map[key]) map[key] = []
        map[key].push(item)
      })
      // Sort by time within each day
      Object.keys(map).forEach(k => {
        map[k].sort((a, b) => {
          const ta = a.due_time || a.event_time || '99:99'
          const tb = b.due_time || b.event_time || '99:99'
          return ta.localeCompare(tb)
        })
      })
      return map
    })

    // Today summary
    const todayStats = computed(() => {
      const key = formatDateKey(today.value)
      const items = tasksByDate.value[key] || []
      const tasksOnly = items.filter(i => i.item_type !== 'hearing')
      const urgent = tasksOnly.filter(i => i.priority === 'urgent' || i.priority === 'high').length
      return { total: items.length, urgent }
    })
    const todaySummaryTooltip = computed(() => {
      const s = todayStats.value
      let txt = `Сегодня: ${s.total}`
      if (s.urgent) txt += `\nВажных/срочных: ${s.urgent}`
      txt += '\nКлик — открыть день в режиме «День»'
      return txt
    })

    // Active filters count
    const hasActiveFilters = computed(() => {
      return !filters.types.tasks || (canSeeHearings.value && !filters.types.hearings)
        || filters.statuses.length > 0 || filters.priorities.length > 0
        || (filters.assignee && filters.assignee !== '')
    })
    const activeFiltersCount = computed(() => {
      let n = 0
      if (!filters.types.tasks) n += 1
      if (canSeeHearings.value && !filters.types.hearings) n += 1
      n += filters.statuses.length
      n += filters.priorities.length
      if (filters.assignee) n += 1
      return n
    })
    const resetFilters = () => {
      filters.types.tasks = true
      filters.types.hearings = true
      filters.statuses = []
      filters.priorities = []
      filters.assignee = ''
    }
    const toggleArrayFilter = (key, value) => {
      const arr = filters[key]
      const idx = arr.indexOf(value)
      if (idx >= 0) arr.splice(idx, 1)
      else arr.push(value)
    }

    // Calendar cells
    const calendarDays = computed(() => {
      const start = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth(), 1)
      const startDay = (start.getDay() + 6) % 7
      const gridStart = new Date(start); gridStart.setDate(start.getDate() - startDay)
      const days = []
      for (let i = 0; i < 42; i += 1) {
        const date = new Date(gridStart); date.setDate(gridStart.getDate() + i)
        const key = formatDateKey(date)
        const inCurrentMonth = date.getMonth() === currentMonth.value.getMonth()
        const dow = date.getDay()
        const allTasks = tasksByDate.value[key] || []
        days.push({
          key, date, dayNumber: date.getDate(), inCurrentMonth,
          isToday: key === formatDateKey(today.value),
          isWeekend: dow === 0 || dow === 6,
          tasks: allTasks,
          visibleTasks: allTasks.slice(0, maxVisibleTasks),
          overflowCount: Math.max(0, allTasks.length - maxVisibleTasks),
        })
      }
      return days
    })

    const agendaDays = computed(() =>
      calendarDays.value
        .filter(c => c.inCurrentMonth && c.tasks.length > 0)
        .map(c => ({
          ...c,
          weekdayName: c.date.toLocaleDateString('ru-RU', { weekday: 'short' }),
          monthDay: c.date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' }),
        }))
    )

    const weekDaysCells = computed(() => {
      const days = []
      for (let i = 0; i < 7; i += 1) {
        const date = new Date(currentWeekStart.value); date.setDate(currentWeekStart.value.getDate() + i)
        const key = formatDateKey(date)
        const dow = date.getDay()
        const allTasks = tasksByDate.value[key] || []
        days.push({
          key, date, dayNumber: date.getDate(),
          inCurrentMonth: true,
          isToday: key === formatDateKey(today.value),
          isWeekend: dow === 0 || dow === 6,
          tasks: allTasks,
        })
      }
      return days
    })

    const dayViewCell = computed(() => {
      const key = formatDateKey(currentDay.value)
      const dow = currentDay.value.getDay()
      const allTasks = tasksByDate.value[key] || []
      return {
        key, date: currentDay.value, dayNumber: currentDay.value.getDate(),
        inCurrentMonth: true, isToday: key === formatDateKey(today.value),
        isWeekend: dow === 0 || dow === 6, tasks: allTasks,
      }
    })

    const dayViewAllDay = computed(() => dayViewCell.value.tasks.filter(t => !(t.due_time || t.event_time)))
    const tasksByHour = computed(() => {
      const map = {}
      dayViewCell.value.tasks.forEach(t => {
        const time = t.due_time || t.event_time
        if (!time) return
        const hour = parseInt(String(time).split(':')[0], 10)
        if (Number.isNaN(hour)) return
        const bucket = Math.max(8, Math.min(20, hour))
        if (!map[bucket]) map[bucket] = []
        map[bucket].push(t)
      })
      return map
    })

    const hourPositionStyle = (item) => {
      const time = item.due_time || item.event_time || '00:00'
      const minutes = parseInt(String(time).split(':')[1] || '0', 10)
      const top = (minutes / 60) * 100
      return { top: `${top}%` }
    }

    const dayViewFullLabel = computed(() =>
      currentDay.value.toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }))

    const expandedDayLabel = computed(() => expandedDay.value
      ? expandedDay.value.date.toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' })
      : '')

    // API
    const loadTasks = async () => {
      try {
        const range = dateRange.value
        const res = await api.calendar.listTasks({ limit: 500, due_date_from: range.from, due_date_to: range.to })
        tasks.value = res.data || []
      } catch (err) {
        console.error('Tasks load error:', err)
        tasks.value = []
        toastError('Не удалось загрузить задачи')
      }
    }

    const loadHearings = async () => {
      if (!canSeeHearings.value || !filters.types.hearings) {
        hearings.value = []
        return
      }
      try {
        const data = await api.calendar.listLegalCases()
        hearings.value = (data || []).flatMap((c) => (c.events || [])
          .filter(e => e.event_type === 'Заседание' && e.event_date)
          .map(e => ({
            id: `hearing-${e.id}`, item_type: 'hearing',
            title: `${c.case_number || 'Дело'} — Заседание`,
            due_date: e.event_date, status: 'hearing', priority: 'normal',
            case_id: c.id, event_id: e.id, event_time: e.event_time, courtroom: e.courtroom,
          })))
      } catch (err) {
        console.error('Hearings load error:', err)
        hearings.value = []
      }
    }

    const loadUnscheduled = async () => {
      if (!showUnscheduled.value) return
      loadingUnscheduled.value = true
      try {
        const params = { limit: 200 }
        if (filters.assignee === '__me__' && activeUserId.value) params.assigned_to_user_id = activeUserId.value
        else if (filters.assignee) params.assigned_to_user_id = filters.assignee
        const res = await api.calendar.listTasks(params)
        unscheduledTasks.value = (res.data || []).filter(t => !t.due_date && t.status !== 'completed' && t.status !== 'cancelled')
      } catch (err) {
        console.error('Unscheduled load error:', err)
        unscheduledTasks.value = []
      } finally { loadingUnscheduled.value = false }
    }

    const loadAll = async () => {
      loading.value = true
      await Promise.all([loadTasks(), loadHearings(), loadUnscheduled()])
      loading.value = false
    }

    const loadUsers = async () => {
      try {
        await usersStore.ensureLoaded()
        users.value = usersStore.items
      } catch (err) { users.value = [] }
    }

    // Navigation
    const setViewMode = (mode) => { viewMode.value = mode; focusedCellIndex.value = -1 }
    const prevPeriod = () => {
      focusedCellIndex.value = -1
      if (viewMode.value === 'month') {
        const d = new Date(currentMonth.value); d.setMonth(d.getMonth() - 1)
        currentMonth.value = new Date(d.getFullYear(), d.getMonth(), 1)
      } else if (viewMode.value === 'week') {
        const d = new Date(currentWeekStart.value); d.setDate(d.getDate() - 7); currentWeekStart.value = d
      } else { const d = new Date(currentDay.value); d.setDate(d.getDate() - 1); currentDay.value = d }
    }
    const nextPeriod = () => {
      focusedCellIndex.value = -1
      if (viewMode.value === 'month') {
        const d = new Date(currentMonth.value); d.setMonth(d.getMonth() + 1)
        currentMonth.value = new Date(d.getFullYear(), d.getMonth(), 1)
      } else if (viewMode.value === 'week') {
        const d = new Date(currentWeekStart.value); d.setDate(d.getDate() + 7); currentWeekStart.value = d
      } else { const d = new Date(currentDay.value); d.setDate(d.getDate() + 1); currentDay.value = d }
    }
    const goToday = () => {
      focusedCellIndex.value = -1
      const t = today.value
      currentMonth.value = new Date(t.getFullYear(), t.getMonth(), 1)
      currentWeekStart.value = getMonday(t)
      currentDay.value = new Date(t.getFullYear(), t.getMonth(), t.getDate())
    }
    const goTodayDay = () => { setViewMode('day'); goToday() }

    watch(dateRange, () => loadTasks())
    watch(showUnscheduled, () => { if (showUnscheduled.value) loadUnscheduled() })
    watch(() => filters.assignee, () => loadUnscheduled())
    watch(() => filters.types.hearings, () => loadHearings())

    // Task helpers
    const truncateTitle = (value, max = 20) => {
      const text = value || ''
      return text.length <= max ? text : `${text.slice(0, max - 2)}…`
    }
    const getTaskClass = (item) => {
      if (item.item_type === 'hearing') return 'task--hearing'
      const cls = [`task--${item.status || 'new'}`]
      if (item.priority === 'urgent') cls.push('task--urgent')
      return cls
    }
    const getTaskIcon = (item) => {
      if (item.item_type === 'hearing') return 'fas fa-gavel'
      const icons = {
        new: 'fas fa-circle', in_progress: 'fas fa-play-circle',
        pending: 'fas fa-pause-circle', completed: 'fas fa-check-circle',
        cancelled: 'fas fa-times-circle', deferred: 'fas fa-clock'
      }
      return icons[item.status] || 'fas fa-circle'
    }
    const getTimeLabel = (item) => {
      const t = item.due_time || item.event_time
      return t ? String(t).slice(0, 5) : ''
    }
    const getTaskMeta = (item) => {
      if (item.item_type === 'hearing') {
        const parts = []
        if (item.event_time) parts.push(item.event_time.slice(0, 5))
        if (item.courtroom) parts.push(`зал ${item.courtroom}`)
        return parts.join(', ') || 'Заседание'
      }
      const map = {
        new: 'Новая', in_progress: 'В работе', pending: 'Ожидает',
        completed: 'Завершена', cancelled: 'Отменена', deferred: 'Отложена'
      }
      const parts = [map[item.status] || 'Задача']
      if (item.due_time) parts.push(item.due_time.slice(0, 5))
      if (item.priority === 'urgent') parts.push('Срочно')
      else if (item.priority === 'high') parts.push('Высокий')
      return parts.join(' · ')
    }

    const expandDay = (cell) => { expandedDay.value = cell }
    const openTask = (task) => {
      expandedDay.value = null
      if (task.item_type === 'hearing') {
        editingTask.value = task
        return
      }
      editForm.value = {
        title: task.title || '',
        status: task.status || 'new',
        priority: task.priority || 'normal',
        due_date: task.due_date || '',
        due_time: task.due_time || '',
        assigned_to_user_id: task.assigned_to_user_id || null,
        description: task.description || '',
      }
      editingTask.value = task
    }
    const closeEditDrawer = () => { editingTask.value = null }
    const goToFullTask = (task) => router.push({ path: '/tasks', query: { task_id: task.id } })
    const goToHearing = (task) => router.push({ path: `/legal-work/${task.case_id}` })

    const saveEdit = async () => {
      if (!editingTask.value) return
      savingEdit.value = true
      try {
        const payload = { ...editForm.value }
        if (!payload.due_date) payload.due_date = null
        if (!payload.due_time) payload.due_time = null
        await api.calendar.updateTask(editingTask.value.id, payload)
        toastSuccess('Сохранено')
        closeEditDrawer()
        await loadTasks()
        if (showUnscheduled.value) await loadUnscheduled()
      } catch (err) {
        console.error('Save edit error:', err)
        toastError(err.response?.data?.detail || 'Ошибка сохранения')
      } finally { savingEdit.value = false }
    }

    // Quick create
    const openQuickCreate = (cell) => {
      quickForm.value = {
        title: '', due_date: formatDateISO(cell.date), due_time: '',
        priority: 'normal', assigned_to_user_id: null,
      }
      showQuickCreate.value = true
    }
    const saveQuickTask = async () => {
      if (!quickForm.value.title.trim()) { toastError('Введите название задачи'); return }
      quickSaving.value = true
      try {
        await api.calendar.createTask({
          title: quickForm.value.title,
          due_date: quickForm.value.due_date || null,
          due_time: quickForm.value.due_time || null,
          priority: quickForm.value.priority,
          assigned_to_user_id: quickForm.value.assigned_to_user_id,
          status: 'new',
          notify_assigned: true,
          notify_overdue: true,
        })
        showQuickCreate.value = false
        toastSuccess('Задача создана')
        await loadTasks()
        if (!quickForm.value.due_date && showUnscheduled.value) await loadUnscheduled()
      } catch (err) {
        console.error('Create error:', err)
        toastError('Ошибка создания задачи')
      } finally { quickSaving.value = false }
    }

    // Drag-drop
    const canDrag = (item) => item.item_type !== 'hearing'
    const onDragStart = (e, item) => {
      if (!canDrag(item)) { e.preventDefault(); return }
      draggedTask = item
      e.dataTransfer.effectAllowed = 'move'
      try { e.dataTransfer.setData('text/plain', item.id) } catch (_) { /* noop */ }
    }
    const onDragOver = (cell) => {
      if (!draggedTask) return
      dragOverKey.value = cell.key
    }
    const onDragEnd = () => { draggedTask = null; dragOverKey.value = null }

    const updateTaskDueDate = async (taskId, newDateOrNull) => {
      try {
        await api.calendar.updateTask(taskId, { due_date: newDateOrNull })
        toastSuccess(newDateOrNull ? 'Дата обновлена' : 'Дата снята')
        await loadTasks()
        if (showUnscheduled.value) await loadUnscheduled()
      } catch (err) {
        console.error('Move error:', err)
        toastError(err.response?.data?.detail || 'Не удалось перенести')
      }
    }

    const onDrop = async (cell) => {
      if (!draggedTask) return
      const id = draggedTask.id
      const newDate = formatDateISO(cell.date)
      onDragEnd()
      // optimistic: update local
      const idx = tasks.value.findIndex(t => t.id === id)
      const prev = idx >= 0 ? { ...tasks.value[idx] } : null
      if (idx >= 0) tasks.value[idx] = { ...tasks.value[idx], due_date: newDate }
      else {
        // could be from unscheduled
        unscheduledTasks.value = unscheduledTasks.value.filter(t => t.id !== id)
        tasks.value.push({ ...draggedTask, due_date: newDate })
      }
      try {
        await api.calendar.updateTask(id, { due_date: newDate })
        toastSuccess('Перенесено')
      } catch (err) {
        console.error('Drop error:', err)
        toastError('Не удалось перенести')
        if (prev && idx >= 0) tasks.value[idx] = prev
      }
    }

    const onDropUnscheduled = async () => {
      if (!draggedTask) return
      const id = draggedTask.id
      onDragEnd()
      const idx = tasks.value.findIndex(t => t.id === id)
      const prev = idx >= 0 ? { ...tasks.value[idx] } : null
      if (idx >= 0) tasks.value[idx] = { ...tasks.value[idx], due_date: null }
      try {
        await api.calendar.updateTask(id, { due_date: null })
        toastSuccess('Дата снята')
        await loadUnscheduled()
      } catch (err) {
        console.error('Unschedule error:', err)
        toastError('Не удалось снять дату')
        if (prev && idx >= 0) tasks.value[idx] = prev
      }
    }

    // Keyboard
    const handleKeydown = (e) => {
      if (e.key === 'Escape') {
        if (showQuickCreate.value) { showQuickCreate.value = false; return }
        if (editingTask.value) { closeEditDrawer(); return }
        if (expandedDay.value) { expandedDay.value = null; return }
        if (filtersOpen.value) { filtersOpen.value = false; return }
        if (legendOpen.value) { legendOpen.value = false; return }
      }
      if (showQuickCreate.value || editingTask.value || expandedDay.value) return
      if (viewMode.value === 'month') {
        const total = calendarDays.value.length
        let idx = focusedCellIndex.value < 0 ? 0 : focusedCellIndex.value
        if (e.key === 'ArrowRight') { e.preventDefault(); idx = Math.min(idx + 1, total - 1) }
        else if (e.key === 'ArrowLeft') { e.preventDefault(); idx = Math.max(idx - 1, 0) }
        else if (e.key === 'ArrowDown') { e.preventDefault(); idx = Math.min(idx + 7, total - 1) }
        else if (e.key === 'ArrowUp') { e.preventDefault(); idx = Math.max(idx - 7, 0) }
        else return
        focusedCellIndex.value = idx
        nextTick(() => { const cells = calendarRoot.value?.querySelectorAll('.day-cell[tabindex="0"]'); if (cells && cells[idx]) cells[idx].focus() })
      } else if (viewMode.value === 'week') {
        let idx = focusedCellIndex.value < 0 ? 0 : focusedCellIndex.value
        if (e.key === 'ArrowRight') { e.preventDefault(); idx = Math.min(idx + 1, 6) }
        else if (e.key === 'ArrowLeft') { e.preventDefault(); idx = Math.max(idx - 1, 0) }
        else return
        focusedCellIndex.value = idx
        nextTick(() => { const cells = calendarRoot.value?.querySelectorAll('.week-cell[tabindex="0"]'); if (cells && cells[idx]) cells[idx].focus() })
      }
    }

    const cellAriaLabel = (cell) => {
      const dateStr = cell.date.toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' })
      return `${dateStr}, задач: ${cell.tasks.length}`
    }

    const syncActiveUser = () => { activeUser.value = getActiveUser() }

    onMounted(() => {
      loadAll()
      loadUsers()
      scheduleMidnightUpdate()
      window.addEventListener('permissions-updated', syncActiveUser)
    })
    onBeforeUnmount(() => {
      if (midnightTimer) clearTimeout(midnightTimer)
      window.removeEventListener('permissions-updated', syncActiveUser)
    })

    return {
      calendarRoot, weekDays, hours,
      loading, viewMode, viewModes,
      periodLabel, todayDayNumber, weekTodayIdx,
      activeUserId, canSeeHearings, users,
      todayStats, todaySummaryTooltip,
      filters, filtersOpen, hasActiveFilters, activeFiltersCount, statusFilterOptions, priorityFilterOptions,
      legendOpen, colorLegend,
      showUnscheduled, unscheduledTasks, loadingUnscheduled,
      calendarDays, agendaDays, weekDaysCells, dayViewCell, dayViewAllDay, tasksByHour, dayViewFullLabel,
      focusedCellIndex, dragOverKey,
      expandedDay, expandedDayLabel,
      showQuickCreate, quickForm, quickSaving,
      editingTask, editForm, savingEdit,
      setViewMode, prevPeriod, nextPeriod, goToday, goTodayDay,
      truncateTitle, getTaskClass, getTaskIcon, getTimeLabel, getTaskMeta,
      expandDay, openTask, closeEditDrawer, goToFullTask, goToHearing, saveEdit, formatDateRu,
      openQuickCreate, saveQuickTask,
      canDrag, onDragStart, onDragOver, onDragEnd, onDrop, onDropUnscheduled,
      handleKeydown, cellAriaLabel,
      hourPositionStyle,
      toggleArrayFilter, resetFilters,
    }
  },
}
</script>

<style scoped>
/* ============================================================
   Status colour tokens (light + dark theme)
   ============================================================ */
.calendar-view {
  --cal-status-new-bg: rgba(100, 116, 139, 0.18);
  --cal-status-new-fg: #475569;
  --cal-status-new-icon: #64748b;
  --cal-status-progress-bg: rgba(59, 130, 246, 0.18);
  --cal-status-progress-fg: #1d4ed8;
  --cal-status-progress-icon: #3b82f6;
  --cal-status-pending-bg: rgba(245, 158, 11, 0.20);
  --cal-status-pending-fg: #b45309;
  --cal-status-pending-icon: #f59e0b;
  --cal-status-completed-bg: rgba(34, 197, 94, 0.20);
  --cal-status-completed-fg: #15803d;
  --cal-status-completed-icon: #22c55e;
  --cal-status-cancelled-bg: rgba(239, 68, 68, 0.18);
  --cal-status-cancelled-fg: #b91c1c;
  --cal-status-cancelled-icon: #ef4444;
  --cal-status-deferred-bg: rgba(99, 102, 241, 0.18);
  --cal-status-deferred-fg: #4338ca;
  --cal-status-deferred-icon: #6366f1;
  --cal-status-hearing-bg: rgba(6, 182, 212, 0.20);
  --cal-status-hearing-fg: #0e7490;
  --cal-status-hearing-icon: #06b6d4;

  --cal-weekend-color: #dc2626;
  --cal-weekend-bg: rgba(220, 38, 38, 0.04);
  --cal-today-bg: rgba(0, 122, 255, 0.10);
  --cal-today-border: var(--md-sys-color-primary, #1976d2);
  --cal-drop-bg: rgba(25, 118, 210, 0.10);
  --cal-drop-border: var(--md-sys-color-primary, #1976d2);
}
:root[data-theme="dark"] .calendar-view,
@media (prefers-color-scheme: dark) {
  .calendar-view {
    --cal-status-new-bg: rgba(148, 163, 184, 0.20);
    --cal-status-new-fg: #cbd5e1;
    --cal-status-progress-bg: rgba(59, 130, 246, 0.25);
    --cal-status-progress-fg: #93c5fd;
    --cal-status-pending-bg: rgba(245, 158, 11, 0.25);
    --cal-status-pending-fg: #fcd34d;
    --cal-status-completed-bg: rgba(34, 197, 94, 0.25);
    --cal-status-completed-fg: #86efac;
    --cal-status-cancelled-bg: rgba(239, 68, 68, 0.25);
    --cal-status-cancelled-fg: #fca5a5;
    --cal-status-deferred-bg: rgba(99, 102, 241, 0.25);
    --cal-status-deferred-fg: #c7d2fe;
    --cal-status-hearing-bg: rgba(6, 182, 212, 0.25);
    --cal-status-hearing-fg: #67e8f9;
  }
}

.calendar-view {
  padding: 0;
  gap: 0;
  outline: none;
}

/* ============================================================
   Toolbar — mirrors Tasks reference (.task-module-topbar.tb):
   rounded top, butted against the panel below, tokenised surface.
   ============================================================ */
.toolbar-card {
  padding: 10px 16px !important;
  margin: 0 !important;
  background: var(--color-surface) !important;
  border: 1px solid var(--color-border-subtle) !important;
  border-bottom: 0 !important;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0 !important;
  box-shadow: none !important;
  /* Override global .card { overflow: hidden } so popovers can escape */
  overflow: visible !important;
  z-index: 50;
}
.toolbar-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}
.toolbar-title {
  margin: 0;
  font-size: var(--text-xl);
  font-weight: var(--fw-bold);
  white-space: nowrap;
  color: var(--color-text);
}

.today-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 38px;
  padding: 0 var(--space-3);
  border-radius: var(--radius-pill);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border-subtle);
  font-size: var(--text-sm);
  cursor: pointer;
  color: var(--color-text);
  transition: background var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out);
}
.today-chip:hover { background: var(--color-surface-3); }
.today-chip.urgent { border-color: var(--color-danger); }
.today-chip-urgent {
  background: var(--color-danger);
  color: #fff;
  padding: 1px 8px;
  border-radius: var(--radius-pill);
  font-weight: var(--fw-bold);
  font-size: var(--text-xs);
}

.view-switcher {
  display: inline-flex;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  padding: 3px;
  gap: 2px;
  height: 38px;
  align-items: center;
}
.view-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 30px;
  padding: 0 var(--space-3);
  border: 0;
  background: transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}
.view-btn:hover { background: var(--color-surface-3); color: var(--color-text); }
.view-btn.active {
  background: var(--color-surface);
  color: var(--color-text);
  font-weight: var(--fw-semibold);
  box-shadow: var(--shadow-xs, 0 1px 2px rgba(15, 23, 42, 0.06));
}

.calendar-nav {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}
.calendar-nav .btn-icon {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border-subtle);
  color: var(--color-text);
}
.calendar-nav .btn-icon:hover { background: var(--color-surface-3); }
.period-label {
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  text-transform: capitalize;
  width: 220px;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--color-text);
}

.today-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 38px;
  padding: 0 var(--space-3);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-primary);
  background: transparent;
  color: var(--color-primary);
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out);
}
.today-btn:hover { background: var(--color-primary-soft, rgba(63, 140, 255, 0.10)); }
.today-btn .today-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: #fff;
  border-radius: var(--radius-xs, 4px);
  padding: 0 6px;
  margin-left: 4px;
  font-size: var(--text-xs);
  font-weight: var(--fw-bold);
}
.hide-md { }
@media (max-width: 1100px) { .hide-md { display: none; } }

/* Filters / Legend popover */
.filter-wrap { position: relative; }
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
.filter-popover, .legend-popover {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 600;
  width: 320px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  padding: var(--space-3);
}
.legend-popover { width: 240px; }
.filter-popover-head, .legend-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-weight: 700;
  font-size: 0.88rem;
}
.filter-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 10px;
}
.filter-label {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--md-sys-color-on-surface-variant);
  font-weight: 600;
}
.chip-group { display: flex; flex-wrap: wrap; gap: 6px; }
.chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--color-border-subtle);
  background: var(--color-surface);
  cursor: pointer;
  font-size: var(--text-xs);
  color: var(--color-text);
  transition: background var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out);
}
.chip:hover { background: var(--color-surface-2); }
.chip.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}
.chip.priority-urgent.active { background: #c62828; border-color: #c62828; }
.chip.priority-high.active { background: #f57c00; border-color: #f57c00; }
.check-label { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; cursor: pointer; }

.legend-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 0.82rem;
}
.legend-swatch {
  display: inline-block;
  width: 20px;
  height: 20px;
  border-radius: 4px;
}
.legend-swatch.task--new { background: var(--cal-status-new-bg); }
.legend-swatch.task--in_progress { background: var(--cal-status-progress-bg); }
.legend-swatch.task--pending { background: var(--cal-status-pending-bg); }
.legend-swatch.task--completed { background: var(--cal-status-completed-bg); }
.legend-swatch.task--cancelled { background: var(--cal-status-cancelled-bg); }
.legend-swatch.task--deferred { background: var(--cal-status-deferred-bg); }
.legend-swatch.task--hearing { background: var(--cal-status-hearing-bg); }

.pop-enter-active, .pop-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.pop-enter-from, .pop-leave-to { opacity: 0; transform: translateY(-4px); }

/* ============================================================
   Workspace layout (with optional sidebar)
   ============================================================ */
.workspace { display: grid; grid-template-columns: 1fr; gap: var(--space-3); min-height: 0; }
.workspace.with-sidebar { grid-template-columns: 1fr 320px; }
.calendar-area {
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
  /* Mirror .task-module-main: butted to toolbar, rounded only at bottom,
     no internal padding (the global .card padding is overridden here). */
  padding: var(--space-3) !important;
  margin: 0 !important;
  background: var(--color-surface) !important;
  border: 1px solid var(--color-border-subtle) !important;
  border-top: 0 !important;
  border-radius: 0 0 var(--radius-lg) var(--radius-lg) !important;
  box-shadow: none !important;
}
.unscheduled-panel {
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--md-sys-color-surface-container-low, #f8fafc);
}
.unscheduled-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 4px 8px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  margin-bottom: 8px;
  font-weight: 700;
  font-size: 0.88rem;
}
.unscheduled-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow-y: auto;
  flex: 1;
  min-height: 80px;
}
.unscheduled-list:empty::after {
  content: 'Перетяните сюда задачу';
  display: block;
  text-align: center;
  color: var(--md-sys-color-on-surface-variant);
  padding: 24px 12px;
  border: 2px dashed var(--md-sys-color-outline-variant);
  border-radius: 8px;
  font-size: 0.85rem;
}

/* ============================================================
   Loading / empty
   ============================================================ */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 4rem 1rem;
  color: var(--md-sys-color-on-surface-variant);
}
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 3rem 1rem;
}
.empty-state.small { padding: 1.5rem 0.5rem; }
.empty-state i {
  font-size: 2.4rem;
  color: var(--md-sys-color-outline-variant);
  margin-bottom: 12px;
}
.empty-state p { margin: 0 0 4px; font-weight: 500; color: var(--md-sys-color-on-surface); }

/* ============================================================
   Weekday headers + grids
   ============================================================ */
.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
  margin-bottom: 6px;
}
.weekday {
  text-align: center;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--md-sys-color-on-surface-variant);
  padding: 6px 0;
  border-radius: 6px;
}
.weekday.weekend { color: var(--cal-weekend-color); }
.weekday.today {
  background: var(--cal-today-bg);
  color: var(--cal-today-border);
}
.today-mark { color: var(--cal-today-border); margin-left: 2px; font-weight: 800; }

.month-grid, .week-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
  flex: 1;
  min-height: 0;
}
.week-grid { grid-auto-rows: minmax(280px, 1fr); }

.day-cell {
  min-height: 100px;
  background: var(--md-sys-color-surface, #fff);
  border: 1px solid var(--md-sys-color-outline-variant, rgba(0,0,0,0.06));
  border-radius: 10px;
  padding: 6px;
  display: flex;
  flex-direction: column;
  cursor: default;
  transition: border-color 0.12s ease, background 0.12s ease;
}
.day-cell.muted { opacity: 0.45; background: transparent; }
.day-cell.weekend { background: var(--cal-weekend-bg); }
.day-cell.today {
  border-color: var(--cal-today-border);
  background: var(--cal-today-bg);
}
.day-cell.focused { outline: 2px solid var(--cal-today-border); outline-offset: -2px; }
.day-cell.dropping {
  background: var(--cal-drop-bg);
  border: 2px dashed var(--cal-drop-border);
}
.day-cell:focus { outline: 2px solid var(--cal-today-border); outline-offset: -2px; }

.day-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  min-height: 22px;
}
.day-num {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}
.day-num.today-num,
.today-num {
  background: var(--cal-today-border);
  color: #fff;
  border-radius: 50%;
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.day-actions { display: flex; align-items: center; gap: 4px; }
.day-count {
  font-size: 0.7rem;
  background: rgba(0,0,0,0.08);
  padding: 1px 6px;
  border-radius: 999px;
  font-weight: 700;
}
.add-btn {
  width: 22px; height: 22px;
  display: inline-flex; align-items: center; justify-content: center;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.12s ease, background 0.12s ease;
}
.day-cell:hover .add-btn,
.agenda-day-head .add-btn { opacity: 1; }
.add-btn:hover { background: var(--md-sys-color-primary, #1976d2); color: #fff; }

.day-tasks {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
  min-height: 0;
}

/* ============================================================
   Task chip
   ============================================================ */
.cal-task {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 8px;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 0.78rem;
  cursor: pointer;
  text-align: left;
  background: var(--cal-status-new-bg);
  color: var(--cal-status-new-fg);
  border-color: rgba(0,0,0,0.05);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  position: relative;
}
.cal-task:hover { filter: brightness(0.96); }
.cal-task[draggable="true"] { cursor: grab; }
.cal-task[draggable="true"]:active { cursor: grabbing; }
.task-icon { font-size: 0.62rem; opacity: 0.85; flex-shrink: 0; }
.task-title { overflow: hidden; text-overflow: ellipsis; flex: 1; }
.task-time {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.7rem;
  font-weight: 700;
  margin-left: auto;
  flex-shrink: 0;
  opacity: 0.85;
}

.task--new { background: var(--cal-status-new-bg); color: var(--cal-status-new-fg); }
.task--new .task-icon { color: var(--cal-status-new-icon); }
.task--in_progress { background: var(--cal-status-progress-bg); color: var(--cal-status-progress-fg); }
.task--in_progress .task-icon { color: var(--cal-status-progress-icon); }
.task--pending { background: var(--cal-status-pending-bg); color: var(--cal-status-pending-fg); }
.task--pending .task-icon { color: var(--cal-status-pending-icon); }
.task--completed { background: var(--cal-status-completed-bg); color: var(--cal-status-completed-fg); }
.task--completed .task-icon { color: var(--cal-status-completed-icon); }
.task--completed .task-title { text-decoration: line-through; opacity: 0.7; }
.task--cancelled { background: var(--cal-status-cancelled-bg); color: var(--cal-status-cancelled-fg); }
.task--cancelled .task-icon { color: var(--cal-status-cancelled-icon); }
.task--cancelled .task-title { text-decoration: line-through; opacity: 0.65; }
.task--deferred { background: var(--cal-status-deferred-bg); color: var(--cal-status-deferred-fg); }
.task--deferred .task-icon { color: var(--cal-status-deferred-icon); }
.task--hearing { background: var(--cal-status-hearing-bg); color: var(--cal-status-hearing-fg); border-color: var(--cal-status-hearing-icon); }
.task--hearing .task-icon { color: var(--cal-status-hearing-icon); }

.task--urgent { box-shadow: inset 3px 0 0 #c62828; padding-left: 10px; }

.cal-task.agenda {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 10px;
  white-space: normal;
}
.cal-task.agenda .task-content { display: flex; flex-direction: column; gap: 2px; flex: 1; min-width: 0; overflow: hidden; }
.cal-task.agenda .task-meta {
  font-size: 0.7rem;
  opacity: 0.8;
  text-overflow: ellipsis;
  overflow: hidden;
}

.cal-overflow {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.72rem;
  padding: 2px 6px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
}
.cal-overflow:hover { background: rgba(0,0,0,0.05); color: var(--md-sys-color-on-surface); }

/* ============================================================
   Agenda (mobile fallback for month)
   ============================================================ */
.cal-desktop { display: flex; flex-direction: column; flex: 1; min-height: 0; }
.cal-mobile-agenda { display: none; }
@media (max-width: 768px) {
  .cal-desktop { display: none; }
  .cal-mobile-agenda { display: flex; flex-direction: column; gap: 12px; }
}
.agenda-day {
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 12px;
  padding: 10px;
}
.agenda-day-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.agenda-day-head.today { color: var(--cal-today-border); }
.agenda-day-num { font-size: 1rem; font-weight: 700; }
.agenda-day-label { flex: 1; font-size: 0.85rem; color: var(--md-sys-color-on-surface-variant); }
.agenda-day-tasks { display: flex; flex-direction: column; gap: 6px; }

/* ============================================================
   Day view (timeline)
   ============================================================ */
.day-view { display: flex; flex-direction: column; flex: 1; min-height: 0; }
.day-view-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  margin-bottom: 8px;
}
.day-view-num {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--md-sys-color-surface-container);
  border-radius: 10px;
  font-weight: 700;
  font-size: 1.1rem;
}
.day-view-num.today-num { background: var(--cal-today-border); color: #fff; }
.day-view-label { flex: 1; font-size: 1rem; font-weight: 600; text-transform: capitalize; }

.day-timeline { flex: 1; min-height: 0; overflow-y: auto; padding: 4px; }
.all-day-section {
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 10px;
  padding: 8px 10px;
  margin-bottom: 12px;
  background: var(--md-sys-color-surface-container-low, #fafbfc);
}
.all-day-label {
  font-size: 0.72rem;
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: var(--md-sys-color-on-surface-variant);
  margin-bottom: 6px;
}
.all-day-tasks { display: flex; flex-direction: column; gap: 6px; }

.hours-grid { display: flex; flex-direction: column; }
.hour-row {
  display: grid;
  grid-template-columns: 60px 1fr;
  min-height: 52px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
  position: relative;
}
.hour-row:last-child { border-bottom: 1px solid var(--md-sys-color-outline-variant); }
.hour-label {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.72rem;
  color: var(--md-sys-color-on-surface-variant);
  padding: 4px 8px;
  border-right: 1px solid var(--md-sys-color-outline-variant);
}
.hour-track { position: relative; padding: 2px 4px; }
.cal-task.timed {
  position: absolute;
  left: 4px;
  right: 4px;
  white-space: normal;
  padding: 4px 8px;
  z-index: 2;
}

/* ============================================================
   Edit drawer
   ============================================================ */
.drawer-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.4);
  z-index: 9500;
  display: flex;
  justify-content: flex-end;
}
.drawer {
  width: min(560px, 100%);
  background: var(--md-sys-color-surface);
  height: 100%;
  display: flex;
  flex-direction: column;
  box-shadow: -10px 0 30px rgba(0,0,0,0.18);
}
.drawer-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 14px 16px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}
.drawer-body { padding: 14px 16px; overflow-y: auto; flex: 1; }
.drawer-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
}
.drawer-meta p { margin: 4px 0; }
.drawer-enter-active, .drawer-leave-active { transition: opacity 0.18s ease; }
.drawer-enter-active .drawer, .drawer-leave-active .drawer { transition: transform 0.22s cubic-bezier(0.2, 0.8, 0.2, 1); }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
.drawer-enter-from .drawer, .drawer-leave-to .drawer { transform: translateX(100%); }

/* ============================================================
   Responsive
   ============================================================ */
@media (max-width: 1100px) {
  .workspace.with-sidebar { grid-template-columns: 1fr; }
  .unscheduled-panel { max-height: 280px; }
}
@media (max-width: 600px) {
  .toolbar-title { display: none; }
  .period-label { min-width: 0; }
}
</style>
