<template>
  <div class="task-boards-shell">
    <div
      v-if="loadErrors.tasks || loadErrors.users || loadErrors.companies || loadErrors.projects"
      class="alert alert-warning d-flex justify-between align-center mb-3 flex-wrap gap-2"
    >
      <div class="small">
        <div v-if="loadErrors.tasks">{{ loadErrors.tasks }}</div>
        <div v-if="loadErrors.projects">{{ loadErrors.projects }}</div>
        <div v-if="loadErrors.users">{{ loadErrors.users }}</div>
        <div v-if="loadErrors.companies">{{ loadErrors.companies }}</div>
      </div>
      <button class="btn btn-sm btn-outline-warning" @click="reloadTaskData">
        <i class="fas fa-sync-alt mr-1"></i> Повторить
      </button>
    </div>

    <div class="task-module-main card flex-grow-1 overflow-hidden d-flex flex-column">
      <div v-if="loading" class="d-flex flex-column gap-2 p-3">
        <SkeletonLoader height="44px" v-for="i in 6" :key="i" />
      </div>

      <div v-else-if="!sortedTasks.length" class="d-flex flex-column align-center justify-center flex-grow-1 text-muted py-5">
        <i class="fas fa-tasks fa-3x mb-3 text-light-gray"></i>
        <p>{{ hasActiveTaskFilters ? 'Под фильтр ничего не подошло' : 'Нет задач' }}</p>
        <div class="d-flex gap-2 mt-3">
          <button v-if="hasActiveTaskFilters" class="btn btn-sm btn-outline-secondary" @click="clearTaskFilters">
            <i class="fas fa-rotate-left mr-1"></i> Сбросить фильтры
          </button>
          <button class="btn btn-sm btn-primary" @click="openCreateTaskModal()">
            <i class="fas fa-plus mr-1"></i> Создать задачу
          </button>
        </div>
      </div>

      <div
        v-else
        class="flex-grow-1 overflow-auto p-0 task-list-container"
        :class="{
          'task-list-container--kanban': taskLayout === 'kanban',
          'task-list-container--matrix': taskLayout === 'matrix'
        }"
      >
        <!-- ════════════════ LIST ════════════════ -->
        <template v-if="taskLayout === 'list'">
          <div class="task-grid">
            <header class="task-grid__head">
              <label class="task-grid__select" :title="allOnPageSelected ? 'Снять выбор' : 'Выбрать все на странице'">
                <input
                  type="checkbox"
                  :checked="allOnPageSelected"
                  :indeterminate.prop="someOnPageSelected && !allOnPageSelected"
                  @change="toggleAllOnPage"
                />
              </label>
              <button type="button" class="task-grid__sort task-grid__col--num" @click="onTaskSortByColumn('number')" :class="{ active: taskSort.by === 'number' }">
                №
                <i v-if="taskSort.by === 'number'" class="fas" :class="taskSort.dir === 'asc' ? 'fa-arrow-up-short-wide' : 'fa-arrow-down-wide-short'"></i>
              </button>
              <button type="button" class="task-grid__sort" @click="onTaskSortByColumn('title')" :class="{ active: taskSort.by === 'title' }">
                Задача
                <i v-if="taskSort.by === 'title'" class="fas" :class="taskSort.dir === 'asc' ? 'fa-arrow-up-short-wide' : 'fa-arrow-down-wide-short'"></i>
              </button>
              <button type="button" class="task-grid__sort" @click="onTaskSortByColumn('due_date')" :class="{ active: taskSort.by === 'due_date' }">
                <i class="far fa-calendar-alt task-grid__lead"></i>
                Срок
                <i v-if="taskSort.by === 'due_date'" class="fas" :class="taskSort.dir === 'asc' ? 'fa-arrow-up-short-wide' : 'fa-arrow-down-wide-short'"></i>
              </button>
              <span class="task-grid__col">
                <i class="far fa-folder-open task-grid__lead"></i>
                Проект
              </span>
              <span class="task-grid__col task-grid__col--people">
                <i class="far fa-user task-grid__lead"></i>
                Исполнители
              </span>
            </header>

            <article
              v-for="task in sortedTasks"
              :key="task.id"
              class="task-row"
              :class="[
                `task-row--status-${task.status}`,
                { 'task-row--selected': isTaskSelected(task.id), 'task-row--completed': task.status === 'completed' }
              ]"
              @click="editTask(task)"
            >
              <label class="task-row__select" @click.stop>
                <input
                  type="checkbox"
                  :checked="isTaskSelected(task.id)"
                  @change="toggleTaskSelected(task.id)"
                />
              </label>

              <div class="task-row__num">{{ task.number != null ? task.number : '—' }}</div>

              <div class="task-row__main">
                <span
                  class="task-row__status-dot"
                  :style="{ background: getStatusColor(task.status) }"
                  :title="getStatusText(task.status)"
                ></span>
                <span class="task-row__title">{{ task.title }}</span>
                <i
                  v-if="getPriorityIcon(task.priority)"
                  class="task-row__priority"
                  :class="getPriorityIcon(task.priority)"
                  :style="{ color: getPriorityColor(task.priority) }"
                  :title="'Приоритет: ' + getPriorityText(task.priority)"
                ></i>
                <i
                  v-if="Array.isArray(task.attachments) && task.attachments.length"
                  class="task-row__paperclip fas fa-paperclip"
                  :title="task.attachments.length + ' файл(ов)'"
                ></i>
              </div>

              <div class="task-row__date" :class="getDueDateClass(task.due_date)">
                <span
                  class="task-chat-badge"
                  :class="{ 'task-chat-badge--zero': !getTaskUnreadCount(task.id) }"
                  :title="getTaskUnreadCount(task.id) ? `Непрочитанных сообщений: ${getTaskUnreadCount(task.id)}` : 'Нет новых сообщений в чате'"
                >{{ getTaskUnreadCount(task.id) }}</span>
                <i v-if="task.due_date" class="far fa-calendar-alt"></i>
                <span>{{ task.due_date ? formatDate(task.due_date) : '—' }}</span>
                <span v-if="task.due_date && task.due_time" class="task-row__time">{{ String(task.due_time).slice(0, 5) }}</span>
              </div>

              <div class="task-row__project">
                <template v-if="task.deal_title">
                  <i class="far fa-folder-open"></i>
                  <span>{{ task.deal_title }}</span>
                </template>
                <span v-else class="task-row__muted">—</span>
              </div>

              <div class="task-row__people">
                <AssigneeStack :user-ids="getTaskAssigneeIds(task)" :users="users" />
              </div>

              <button
                type="button"
                class="task-row__action"
                title="Удалить"
                @click.stop="deleteTask(task)"
              >
                <i class="fas fa-trash"></i>
              </button>
            </article>
          </div>
        </template>

        <!-- ════════════════ KANBAN ════════════════ -->
        <div v-else-if="taskLayout === 'kanban'" class="task-kanban-board">
          <section
            v-for="column in kanbanColumns"
            :key="column.key"
            class="task-kanban-column"
            :class="{ 'task-kanban-column--over': kanbanDropKey === column.key }"
            :style="{ '--task-kanban-accent': column.color }"
          >
            <header class="task-kanban-column__header">
              <div class="task-kanban-column__title-wrap">
                <span class="task-kanban-column__dot"></span>
                <div>
                  <h3>{{ column.label }}</h3>
                  <p :title="formatTaskCount(column.tasks.length)">{{ column.tasks.length }}</p>
                </div>
              </div>
              <button
                type="button"
                class="task-kanban-column__create"
                :title="`Создать задачу в колонке «${column.label}»`"
                @click="openCreateTaskModal(column.key)"
              >
                <i class="fas fa-plus"></i>
              </button>
            </header>

            <draggable
              class="task-kanban-column__list"
              :list="column.tasks"
              item-key="id"
              :group="{ name: 'tasks-kanban', pull: true, put: true }"
              :animation="180"
              :delay="isTouchDevice ? 160 : 0"
              :delay-on-touch-only="true"
              :force-fallback="isTouchDevice"
              fallback-on-body
              ghost-class="task-card--ghost"
              chosen-class="task-card--chosen"
              drag-class="task-card--dragging"
              @start="onKanbanSortStart(column.key)"
              @end="onTaskDragEnd"
              @change="onTaskKanbanChange($event, column.key)"
            >
              <template #item="{ element: task }">
                <article
                  class="task-card"
                  :class="{ 'task-card--updating': updatingTaskId === task.id }"
                  @click="editTask(task)"
                >
                  <div class="task-card__title-row">
                    <span
                      class="task-card__priority"
                      v-if="getPriorityIcon(task.priority)"
                      :style="{ color: getPriorityColor(task.priority) }"
                      :title="'Приоритет: ' + getPriorityText(task.priority)"
                    >
                      <i :class="getPriorityIcon(task.priority)"></i>
                    </span>
                    <h4 class="task-card__title">{{ task.title }}</h4>
                  </div>

                  <div v-if="task.deal_title" class="task-card__meta-line">
                    <i class="far fa-folder-open"></i>
                    <span>{{ task.deal_title }}</span>
                  </div>

                  <div class="task-card__bottom">
                    <div
                      class="task-card__date"
                      :class="task.due_date ? getDueDateClass(task.due_date) : ''"
                    >
                      <span
                        class="task-chat-badge"
                        :class="{ 'task-chat-badge--zero': !getTaskUnreadCount(task.id) }"
                        :title="getTaskUnreadCount(task.id) ? `Непрочитанных сообщений: ${getTaskUnreadCount(task.id)}` : 'Нет новых сообщений в чате'"
                      >{{ getTaskUnreadCount(task.id) }}</span>
                      <template v-if="task.due_date">
                        <i class="far fa-calendar-alt"></i>
                        {{ formatDate(task.due_date) }}<span v-if="task.due_time" class="task-card__time"> {{ String(task.due_time).slice(0, 5) }}</span>
                      </template>
                    </div>

                    <AssigneeStack :user-ids="getTaskAssigneeIds(task)" :users="users" :max="3" />
                  </div>
                </article>
              </template>
              <template #footer>
                <div v-if="!column.tasks.length" class="task-kanban-column__empty">
                  Перетащите задачу сюда
                </div>
              </template>
            </draggable>
          </section>
        </div>

        <!-- ════════════════ MATRIX ════════════════ -->
        <div v-else class="task-matrix-board">
          <section
            v-for="column in matrixColumns"
            :key="column.key"
            class="task-matrix-quadrant"
            :class="{ 'task-matrix-quadrant--over': matrixDropKey === column.key }"
            :style="{ '--task-matrix-accent': column.color, '--task-matrix-bg': column.bg }"
          >
            <header class="task-matrix-quadrant__header">
              <div class="task-matrix-quadrant__title">
                <span class="task-matrix-quadrant__dot"></span>
                <div>
                  <h3>{{ column.label }}</h3>
                  <p>{{ column.action }}</p>
                </div>
              </div>
              <span class="task-matrix-quadrant__count">{{ column.tasks.length }}</span>
            </header>

            <draggable
              class="task-matrix-grid"
              :list="column.tasks"
              item-key="id"
              :group="{ name: 'tasks-matrix', pull: true, put: true }"
              :animation="180"
              :delay="isTouchDevice ? 160 : 0"
              :delay-on-touch-only="true"
              :force-fallback="isTouchDevice"
              fallback-on-body
              ghost-class="task-matrix-card--ghost"
              chosen-class="task-matrix-card--chosen"
              drag-class="task-matrix-card--dragging"
              @start="onMatrixDragStart(column.key)"
              @end="onTaskDragEnd"
              @change="onTaskMatrixChange($event, column.key)"
            >
              <template #item="{ element: task }">
                <article
                  class="task-matrix-card"
                  :class="{ 'task-matrix-card--updating': updatingTaskId === task.id }"
                  @click="editTask(task)"
                >
                  <div class="task-matrix-card__main">
                    <h4>{{ task.title }}</h4>
                    <div class="task-matrix-card__meta">
                      <span v-if="task.due_date">
                        <i class="far fa-calendar-alt"></i>
                        <strong :class="getDueDateClass(task.due_date)">{{ formatDate(task.due_date) }}</strong>
                      </span>
                      <span class="task-matrix-status" :class="getTaskMatrixStatusClass(task.status)">
                        {{ getStatusText(task.status) }}
                      </span>
                    </div>
                  </div>
                  <AssigneeStack :user-ids="getTaskAssigneeIds(task)" :users="users" :max="3" class="task-matrix-card__avatar-stack" />
                </article>
              </template>
              <template #footer>
                <div v-if="!column.tasks.length" class="task-matrix-empty">
                  Перетащите задачу сюда.
                </div>
              </template>
            </draggable>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import draggable from 'vuedraggable'
import SkeletonLoader from '../../../components/ui/SkeletonLoader.vue'
import AssigneeStack from './AssigneeStack.vue'

const STATUS_COLOR = {
  new: '#94a3b8',
  in_progress: '#2563eb',
  pending: '#d97706',
  completed: '#16a34a',
  deferred: '#8b5cf6',
  cancelled: '#64748b'
}

const PRIORITY_ICON = {
  low: 'fas fa-arrow-down',
  normal: '',
  high: 'fas fa-arrow-up',
  urgent: 'fas fa-fire'
}

const PRIORITY_COLOR = {
  low: '#16a34a',
  normal: '#64748b',
  high: '#d97706',
  urgent: '#dc2626'
}

export default {
  name: 'TaskBoards',
  components: { draggable, SkeletonLoader, AssigneeStack },
  props: { state: { type: Object, required: true } },
  setup(props) {
    const s = props.state

    const getStatusColor = (status) => STATUS_COLOR[status] || STATUS_COLOR.new
    const getPriorityIcon = (priority) => PRIORITY_ICON[priority] || ''
    const getPriorityColor = (priority) => PRIORITY_COLOR[priority] || PRIORITY_COLOR.normal

    // Returns the list of assignee user ids for a task. Falls back to the
    // legacy single `assigned_to_user_id` for tasks that haven't been
    // migrated to M2M yet.
    const getTaskAssigneeIds = (task) => {
      if (Array.isArray(task?.assignee_ids) && task.assignee_ids.length) {
        return task.assignee_ids.map(String)
      }
      if (task?.assigned_to_user_id) return [String(task.assigned_to_user_id)]
      return []
    }

    return {
      ...s,
      getStatusColor,
      getPriorityIcon,
      getPriorityColor,
      getTaskAssigneeIds
    }
  }
}
</script>

<style>
/* ============================================================
   GLUE THE TOOLBAR AND LIST INTO A SINGLE CARD
   Tasks.vue declares both blocks as separate cards with a 12px
   gap and individual radii. We collapse the gap, kill the
   between-border, and share one rounded shadow so they read as a
   single surface. !important needed because the parent SFC's
   style block is injected after this one.
   ============================================================ */
.tasks-view {
  gap: 0 !important;
}
.tasks-view .task-module-topbar {
  border-radius: var(--radius-lg) var(--radius-lg) 0 0 !important;
  border-bottom: 1px solid var(--color-border-subtle) !important;
  box-shadow: none !important;
  margin-bottom: 0 !important;
}
.tasks-view .task-module-main {
  border-radius: 0 0 var(--radius-lg) var(--radius-lg) !important;
  border-top: 0 !important;
  margin-top: 0 !important;
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08) !important;
}

/* ============================================================
   TASK LIST GRID — flat row layout with icon-chips for metadata
   ============================================================ */
/* Root wrapper — must grow inside .tasks-view flex column so .task-module-main
   can stretch to the bottom of the viewport in every layout (list/kanban/matrix). */
.task-boards-shell {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-height: 0;
}
.task-boards-shell > .task-module-main { flex: 1 1 auto; min-height: 0; }

.task-grid {
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
}

.task-grid__head,
.task-row {
  display: grid;
  /* checkbox | № | title (flex) | срок | проект | исполнители
     Width for № fits up to 5 digits comfortably (~56px monospace). */
  grid-template-columns: 28px 56px minmax(0, 1fr) 160px 260px 220px;
  align-items: center;
  gap: var(--space-3);
  padding: 12px 14px;
}

.task-grid__head {
  padding-top: 10px;
  padding-bottom: 10px;
  /* Tinted panel — matches Leads table header treatment so the column
     strip reads as its own band, not part of the rows */
  background: var(--color-surface-2);
  border-bottom: 1px solid var(--color-border);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.4px;
  color: var(--color-text-muted);
  font-weight: var(--fw-semibold);
  position: sticky;
  top: 0;
  z-index: 1;
}
:root[data-theme="dark"] .task-grid__head {
  background: rgba(15, 23, 42, 0.55);
  border-bottom-color: var(--glass-border-dark);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) .task-grid__head {
    background: rgba(15, 23, 42, 0.55);
    border-bottom-color: var(--glass-border-dark);
  }
}
.task-grid__sort,
.task-grid__col {
  background: transparent;
  border: 0;
  text-align: left;
  cursor: pointer;
  padding: 0;
  display: inline-flex;
  align-items: center;
  gap: 8px; /* match row icon-text gap */
  justify-self: start;
  /* Pin typography so <button> UA styles don't desync from <span> headers */
  font-family: inherit;
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  line-height: 1;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: var(--color-text-muted);
}
.task-grid__col { cursor: default; }
.task-grid__sort.active { color: var(--color-text); }
.task-grid__col--tail { display: none; }
.task-grid__select { display: inline-flex; align-items: center; justify-content: center; }
/* Leading icon in column headers (matches the row's leading icon size
   so header text aligns with row text). */
.task-grid__lead {
  font-size: var(--text-base);
  color: var(--color-text-subtle);
  width: 14px;
  text-align: center;
}

.task-row {
  border-top: 1px solid var(--color-border-subtle);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out);
}
.task-row:hover { background: var(--color-surface-2); }
.task-row--selected { background: var(--color-primary-soft); }
.task-row--selected:hover { background: var(--color-primary-soft); }
.task-row--completed .task-row__title {
  color: var(--color-text-subtle);
  text-decoration: line-through;
}

.task-row__select { display: inline-flex; align-items: center; justify-content: center; }
.task-row__select input { cursor: pointer; }

.task-row__num {
  font-variant-numeric: tabular-nums;
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  color: var(--color-text-muted);
  text-align: left;
}

.task-row__main {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
  justify-self: start;
}
.task-row__status-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* Бейдж непрочитанных сообщений чата задачи.
   - По умолчанию: зелёный кружок с числом непрочитанных от других юзеров.
   - --zero: серый, для нулевых, чтобы UI оставался «единообразным» —
     всегда виден один индикатор слева от названия задачи независимо
     от того, есть ли там новые сообщения. */
.task-chat-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 6px;
  border-radius: 999px;
  background: #16a34a;
  color: #fff;
  font-size: 11px;
  font-weight: var(--fw-bold);
  line-height: 1;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}
.task-chat-badge--zero {
  background: #e2e8f0;
  color: #94a3b8;
  font-weight: var(--fw-medium);
}
.task-row__title {
  /* flex: 1 1 0 — забирает остаток ширины ячейки и сжимается;
     basis 0 (вместо auto) гарантирует, что длинный текст не растянет
     колонку и не пойдёт в соседнюю. */
  flex: 1 1 0;
  min-width: 0;
  font-size: var(--text-md);
  font-weight: var(--fw-medium);
  color: var(--color-text);
  /* Раньше было nowrap+ellipsis. Заменили на перенос (2 строки максимум)
     по запросу: длинные названия не должны наезжать на соседние колонки
     и не должны быть отрезаны до пары слов. word-break — на случай
     URL/одного длинного «слова» без пробелов. */
  white-space: normal;
  overflow: hidden;
  word-break: break-word;
  overflow-wrap: anywhere;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-height: var(--leading-tight, 1.25);
}
.task-row__priority,
.task-row__paperclip {
  flex-shrink: 0;
  font-size: var(--text-base);
}
.task-row__paperclip { color: var(--color-text-subtle); }

.task-row__date {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  white-space: nowrap;
  justify-self: start;
}
.task-row__date i { color: var(--color-text-subtle); }
.task-row__date.text-danger { color: var(--color-danger); font-weight: var(--fw-semibold); }
.task-row__date.text-warning { color: var(--color-warning); }
.task-row__time {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-subtle);
  margin-left: 2px;
}

.task-row__project {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  font-size: var(--text-sm);
  color: var(--color-text);
  justify-self: start;
}
.task-row__project i { color: var(--color-text-subtle); flex-shrink: 0; }
.task-row__project span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.task-row__muted { color: var(--color-text-subtle); }

.task-row__people {
  display: inline-flex;
  align-items: center;
  justify-self: start;
}

.task-row { position: relative; }
.task-row__action {
  position: absolute;
  top: 50%;
  right: 12px;
  transform: translateY(-50%);
  width: 28px;
  height: 28px;
  border: 0;
  background: var(--color-surface);
  border-radius: var(--radius-sm);
  color: var(--color-text-subtle);
  opacity: 0;
  transition: opacity var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
  cursor: pointer;
  box-shadow: var(--shadow-xs);
}
.task-row:hover .task-row__action { opacity: 1; }
.task-row__action:hover {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

/* ============================================================
   KANBAN CARD — slim variant without description / penalty
   ============================================================ */
.task-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  cursor: pointer;
  transition: box-shadow var(--dur-fast) var(--ease-out), transform var(--dur-fast) var(--ease-out);
}
.task-card:hover {
  box-shadow: var(--shadow-sm);
  transform: translateY(-1px);
}
.task-card--updating { opacity: 0.6; pointer-events: none; }

/* DND visual states (vuedraggable / Sortable.js classes).
   - ghost   — placeholder в новой позиции (рамка-пунктир, видно «куда упадёт»).
   - chosen  — карточка в исходной позиции, пока её тащат (приглушённая).
   - dragging — клон, который ездит за курсором (приподнят, чёткая тень). */
.task-card--ghost {
  background: rgba(33, 150, 243, 0.06) !important;
  border: 2px dashed rgba(33, 150, 243, 0.55) !important;
  box-shadow: none !important;
  transform: none !important;
}
.task-card--ghost > * { visibility: hidden; }
.task-card--chosen {
  opacity: 0.45;
  transform: none !important;
}
.task-card--dragging {
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.22) !important;
  transform: rotate(1.5deg) !important;
  cursor: grabbing !important;
  border-color: rgba(33, 150, 243, 0.55) !important;
}

.task-card__title-row {
  display: flex;
  align-items: flex-start;
  gap: 6px;
}
.task-card__priority {
  display: inline-flex;
  align-items: center;
  font-size: var(--text-sm);
  padding-top: 2px;
}
.task-card__title {
  flex: 1;
  font-size: var(--text-md);
  font-weight: var(--fw-medium);
  color: var(--color-text);
  margin: 0;
  line-height: var(--leading-tight);
  word-break: break-word;
}
.task-card__meta-line {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  min-width: 0;
}
.task-card__meta-line i { color: var(--color-text-subtle); flex-shrink: 0; }
.task-card__meta-line span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.task-card__bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  margin-top: 4px;
}
.task-card__date {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}
.task-card__date.text-danger { color: var(--color-danger); font-weight: var(--fw-semibold); }
.task-card__date.text-warning { color: var(--color-warning); }
.task-card__time { font-family: var(--font-mono); font-size: var(--text-xs); margin-left: 2px; }

/* ============================================================
   MATRIX CARD — keep classic layout, just trimmed
   ============================================================ */
.task-matrix-card__avatar-stack {
  margin-left: var(--space-2);
}
.task-matrix-card--ghost {
  background: rgba(33, 150, 243, 0.06) !important;
  border: 2px dashed rgba(33, 150, 243, 0.55) !important;
  box-shadow: none !important;
}
.task-matrix-card--ghost > * { visibility: hidden; }
.task-matrix-card--chosen { opacity: 0.45; }
.task-matrix-card--dragging {
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.22) !important;
  transform: rotate(1.5deg) !important;
  cursor: grabbing !important;
}
</style>
