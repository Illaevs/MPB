<template>
  <div class="task-chip-row">
    <!-- STATUS ============================================ -->
    <PropertyChip
      label="Статус"
      :value="statusLabel"
      :dot-color="statusColor"
    >
      <template #popover="{ close }">
        <div class="task-chip-popover">
          <div class="task-chip-popover__title">Статус</div>
          <button
            v-for="opt in STATUS_OPTIONS"
            :key="opt.value"
            type="button"
            class="task-chip-popover__option"
            :class="{ 'is-active': taskForm.status === opt.value }"
            @click="setField('status', opt.value); close()"
          >
            <span class="task-chip-popover__dot" :style="{ background: opt.color }"></span>
            <span class="task-chip-popover__label">{{ opt.label }}</span>
            <i v-if="taskForm.status === opt.value" class="fas fa-check task-chip-popover__tick"></i>
          </button>
        </div>
      </template>
    </PropertyChip>

    <!-- PRIORITY ========================================== -->
    <PropertyChip
      label="Приоритет"
      :value="priorityLabel"
      :icon="priorityIcon"
      :icon-color="priorityColor"
    >
      <template #popover="{ close }">
        <div class="task-chip-popover">
          <div class="task-chip-popover__title">Приоритет</div>
          <button
            v-for="opt in PRIORITY_OPTIONS"
            :key="opt.value"
            type="button"
            class="task-chip-popover__option"
            :class="{ 'is-active': taskForm.priority === opt.value }"
            @click="setField('priority', opt.value); close()"
          >
            <i class="task-chip-popover__icon" :class="opt.icon" :style="{ color: opt.color }"></i>
            <span class="task-chip-popover__label">{{ opt.label }}</span>
            <i v-if="taskForm.priority === opt.value" class="fas fa-check task-chip-popover__tick"></i>
          </button>
        </div>
      </template>
    </PropertyChip>

    <!-- DUE / START DATE ================================== -->
    <PropertyChip
      label="Сроки"
      :value="dateLabel"
      icon="far fa-calendar-alt"
      :placeholder="'+ Срок'"
    >
      <template #popover="{ close }">
        <div class="task-chip-popover task-chip-popover--wide">
          <div class="task-chip-popover__title">Сроки</div>
          <div class="task-chip-popover__date-row">
            <label>
              <span>Начало</span>
              <input
                type="date"
                :value="taskForm.start_date || ''"
                class="task-chip-popover__date-input"
                @change="setField('start_date', $event.target.value); validateTaskForm()"
              />
            </label>
            <label>
              <span>Окончание</span>
              <input
                type="date"
                :value="taskForm.due_date || ''"
                class="task-chip-popover__date-input"
                :class="{ 'is-invalid': taskValidation.date }"
                @change="setField('due_date', $event.target.value); validateTaskForm()"
              />
            </label>
          </div>
          <div class="task-chip-popover__date-row task-chip-popover__date-row--time">
            <label>
              <span>Время дедлайна</span>
              <input
                type="time"
                :value="taskForm.due_time || ''"
                class="task-chip-popover__date-input"
                step="60"
                :disabled="!taskForm.due_date"
                @change="setField('due_time', $event.target.value || null)"
              />
            </label>
            <span v-if="!taskForm.due_date" class="task-chip-popover__time-hint">
              сначала укажите дату окончания
            </span>
          </div>
          <div v-if="taskValidation.date" class="task-chip-popover__error">
            <i class="fas fa-circle-exclamation mr-1"></i>{{ taskValidation.date }}
          </div>
          <div class="task-chip-popover__actions">
            <button
              v-if="taskForm.start_date || taskForm.due_date || taskForm.due_time"
              type="button"
              class="task-chip-popover__clear"
              @click="setField('start_date', ''); setField('due_date', ''); setField('due_time', null); validateTaskForm()"
            >
              <i class="fas fa-rotate-left mr-1"></i> Сбросить
            </button>
            <button type="button" class="btn btn-sm btn-primary" @click="close">Готово</button>
          </div>
        </div>
      </template>
    </PropertyChip>
  </div>
</template>

<script>
import { computed } from 'vue'
import PropertyChip from '../../../components/ui/PropertyChip.vue'

const STATUS_OPTIONS = [
  { value: 'new', label: 'Новая', color: '#94a3b8' },
  { value: 'in_progress', label: 'В работе', color: '#2563eb' },
  { value: 'pending', label: 'Ожидает', color: '#d97706' },
  { value: 'completed', label: 'Завершена', color: '#16a34a' },
  { value: 'deferred', label: 'Отложена', color: '#8b5cf6' },
  { value: 'cancelled', label: 'Отменена', color: '#64748b' }
]

const PRIORITY_OPTIONS = [
  { value: 'low', label: 'Низкий', icon: 'fas fa-arrow-down', color: '#16a34a' },
  { value: 'normal', label: 'Нормальный', icon: 'fas fa-equals', color: '#64748b' },
  { value: 'high', label: 'Высокий', icon: 'fas fa-arrow-up', color: '#d97706' },
  { value: 'urgent', label: 'Срочный', icon: 'fas fa-fire', color: '#dc2626' }
]

function formatShortDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.valueOf())) return iso
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })
}

export default {
  name: 'TaskPropertyChips',
  components: { PropertyChip },
  props: { state: { type: Object, required: true } },
  setup(props) {
    const s = props.state
    // taskForm is a ref — must access .value in script code.
    const taskFormRef = s.taskForm

    function setField(field, value) {
      taskFormRef.value[field] = value
      if (typeof s.triggerAutoDraftIfNeeded === 'function') s.triggerAutoDraftIfNeeded()
      // Status / priority / срок (start_date, due_date, due_time) are discrete
      // choices — persist immediately (like people rows), not via the
      // 700ms debounce used for title/description. flushAutoSave + the
      // request-counter in the composable serialize rapid clicks safely
      // and no-op for not-yet-created tasks (guarded by isEditing).
      if (typeof s.flushAutoSave === 'function') s.flushAutoSave()
    }

    const statusLabel = computed(() => {
      const found = STATUS_OPTIONS.find(o => o.value === taskFormRef.value.status)
      return found ? found.label : 'Новая'
    })
    const statusColor = computed(() => {
      const found = STATUS_OPTIONS.find(o => o.value === taskFormRef.value.status)
      return found ? found.color : '#94a3b8'
    })

    const priorityLabel = computed(() => {
      const found = PRIORITY_OPTIONS.find(o => o.value === taskFormRef.value.priority)
      return found ? found.label : 'Нормальный'
    })
    const priorityIcon = computed(() => {
      const found = PRIORITY_OPTIONS.find(o => o.value === taskFormRef.value.priority)
      return found ? found.icon : 'fas fa-equals'
    })
    const priorityColor = computed(() => {
      const found = PRIORITY_OPTIONS.find(o => o.value === taskFormRef.value.priority)
      return found ? found.color : '#64748b'
    })

    const dateLabel = computed(() => {
      const from = formatShortDate(taskFormRef.value.start_date)
      const to = formatShortDate(taskFormRef.value.due_date)
      const time = (taskFormRef.value.due_time || '').slice(0, 5)
      const toWithTime = to ? (time ? `${to} ${time}` : to) : ''
      if (from && toWithTime) return `${from} — ${toWithTime}`
      if (toWithTime) return `до ${toWithTime}`
      if (from) return `с ${from}`
      return ''
    })

    return {
      // taskForm exposed for template — Vue auto-unwraps refs in templates.
      taskForm: taskFormRef,
      validateTaskForm: s.validateTaskForm,
      taskValidation: s.taskValidation,
      STATUS_OPTIONS,
      PRIORITY_OPTIONS,
      setField,
      statusLabel, statusColor,
      priorityLabel, priorityIcon, priorityColor,
      dateLabel
    }
  }
}
</script>

<style scoped>
.task-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  align-items: center;
}

/* ---------- Popover internals ---------- */
.task-chip-popover {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 220px;
}
.task-chip-popover--wide { min-width: 280px; }

.task-chip-popover__title {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-subtle);
  padding: var(--space-1) var(--space-2) var(--space-2);
}

.task-chip-popover__option {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-2);
  border-radius: var(--radius-sm);
  background: transparent;
  border: 0;
  text-align: left;
  font-size: var(--text-md);
  color: var(--color-text);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out);
}
.task-chip-popover__option:hover { background: var(--color-surface-2); }
.task-chip-popover__option.is-active { background: var(--color-primary-soft); }

.task-chip-popover__dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.task-chip-popover__icon { width: 16px; text-align: center; color: var(--color-text-muted); }
.task-chip-popover__label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.task-chip-popover__tick { color: var(--color-primary); font-size: var(--text-sm); }

.task-chip-popover__date-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-2);
  padding: 0 var(--space-2);
}
.task-chip-popover__date-row label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}
.task-chip-popover__date-input {
  padding: 6px 8px;
  font-size: var(--text-md);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
}
.task-chip-popover__date-input.is-invalid { border-color: var(--color-danger); }
.task-chip-popover__date-input:disabled { opacity: 0.55; cursor: not-allowed; }

.task-chip-popover__date-row--time {
  grid-template-columns: 160px 1fr;
  align-items: end;
}
.task-chip-popover__time-hint {
  font-size: var(--text-xs);
  color: var(--color-text-subtle);
  padding-bottom: 8px;
}
.task-chip-popover__error {
  padding: 4px 12px;
  color: var(--color-danger);
  font-size: var(--text-sm);
}
.task-chip-popover__actions {
  display: flex;
  gap: var(--space-2);
  padding: var(--space-2);
  justify-content: flex-end;
}
.task-chip-popover__clear {
  margin-right: auto;
  background: transparent;
  border: 0;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: var(--text-sm);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
}
.task-chip-popover__clear:hover { background: var(--color-surface-2); color: var(--color-text); }
</style>
