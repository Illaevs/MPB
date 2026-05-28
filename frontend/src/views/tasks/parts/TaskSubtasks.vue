<template>
  <div class="task-subtasks">
    <div class="task-subtasks__head">
      <span class="task-subtasks__title">
        <i class="fas fa-list-check"></i>
        Чек-лист
        <span v-if="total" class="task-subtasks__counter">{{ doneCount }} / {{ total }}</span>
      </span>
      <div v-if="total" class="task-subtasks__progress" :title="`${doneCount} из ${total} выполнено`">
        <div class="task-subtasks__progress-bar" :style="{ width: progressPercent + '%' }"></div>
      </div>
    </div>

    <draggable
      v-if="subtasks.length"
      :list="subtasks"
      item-key="id"
      handle=".task-subtask__drag"
      :animation="180"
      ghost-class="task-subtask--ghost"
      chosen-class="task-subtask--chosen"
      class="task-subtasks__list"
      @end="onDragEnd"
    >
      <template #item="{ element: item }">
        <div class="task-subtask" :class="{ 'task-subtask--done': item.is_done }">
          <button
            type="button"
            class="task-subtask__drag"
            tabindex="-1"
            title="Перетащить"
            @click.stop
          >
            <i class="fas fa-grip-vertical"></i>
          </button>
          <label class="task-subtask__check">
            <input
              type="checkbox"
              :checked="item.is_done"
              :disabled="!canEdit || busyIds.has(item.id)"
              @change="toggleDone(item)"
            />
            <span class="task-subtask__check-box"></span>
          </label>
          <div class="task-subtask__body">
            <input
              v-if="editingId === item.id"
              ref="editInput"
              v-model="editingTitle"
              class="task-subtask__title-input"
              type="text"
              :disabled="!canEdit"
              @keydown.enter.prevent="commitEdit(item)"
              @keydown.esc.prevent="cancelEdit"
              @blur="commitEdit(item)"
            />
            <span
              v-else
              class="task-subtask__title"
              :title="canEdit ? 'Кликните, чтобы редактировать' : item.title"
              @click="canEdit && startEdit(item)"
            >{{ item.title }}</span>

            <div class="task-subtask__meta">
              <UiAvatar
                v-if="item.assigned_to_user_id"
                :name="item.assignee_name || getUserName(item.assigned_to_user_id)"
                :src="getUserAvatarUrl(item.assigned_to_user_id)"
                size="xs"
                tooltip
                class="task-subtask__avatar"
                @click.stop="canEdit && openAssigneePicker(item, $event)"
              />
              <button
                v-else-if="canEdit"
                type="button"
                class="task-subtask__chip task-subtask__chip--add"
                title="Назначить ответственного"
                @click.stop="openAssigneePicker(item, $event)"
              >
                <i class="fas fa-user-plus"></i>
              </button>

              <span
                v-if="item.due_date || canEdit"
                class="task-subtask__chip task-subtask__date-chip"
                :class="{ 'task-subtask__chip--overdue': isOverdue(item) }"
                :title="item.due_date ? `Дедлайн: ${formatDate(item.due_date)}${item.due_time ? ' ' + item.due_time : ''}` : 'Установить дедлайн'"
              >
                <i class="far fa-calendar-alt"></i>
                <span v-if="item.due_date">{{ formatDateShort(item.due_date) }}</span>
                <input
                  type="date"
                  class="task-subtask__overlay-input"
                  :value="item.due_date || ''"
                  :disabled="!canEdit"
                  @click.stop="closeAssigneePicker"
                  @change="onDateChange(item, $event)"
                />
              </span>

              <!-- Время — отдельный chip с иконкой часов. Активен,
                   только если дата задана (без даты время теряет смысл),
                   либо если нечего показывать, скрыт. -->
              <span
                v-if="item.due_date && (item.due_time || canEdit)"
                class="task-subtask__chip task-subtask__time-chip"
                :title="item.due_time ? `Время: ${item.due_time}` : 'Установить время'"
              >
                <i class="far fa-clock"></i>
                <span v-if="item.due_time">{{ item.due_time }}</span>
                <input
                  type="time"
                  class="task-subtask__overlay-input"
                  :value="item.due_time || ''"
                  :disabled="!canEdit"
                  @click.stop="closeAssigneePicker"
                  @change="onTimeChange(item, $event)"
                />
              </span>

              <!-- Огонёк: тумблер «важно». Та же иконка/цвет, что и у
                   urgent-приоритета задачи (fas fa-fire, #dc2626) —
                   юзер сразу опознаёт значок. -->
              <button
                v-if="canEdit || item.is_urgent"
                type="button"
                class="task-subtask__chip task-subtask__fire-chip"
                :class="{ 'task-subtask__fire-chip--active': item.is_urgent }"
                :title="item.is_urgent ? 'Снять отметку «срочно»' : 'Отметить как срочное'"
                :disabled="!canEdit"
                @click.stop="toggleUrgent(item)"
              >
                <i class="fas fa-fire"></i>
              </button>
            </div>
          </div>
          <button
            v-if="canEdit"
            type="button"
            class="task-subtask__delete"
            title="Удалить"
            @click.stop="removeItem(item)"
          >
            <i class="fas fa-times"></i>
          </button>
        </div>
      </template>
    </draggable>

    <div v-else class="task-subtasks__empty">
      Пока пусто. Добавьте первый пункт ниже.
    </div>

    <div v-if="canEdit" class="task-subtasks__add">
      <input
        v-model="newTitle"
        type="text"
        class="task-subtasks__add-input"
        placeholder="Добавить пункт и нажать Enter…"
        :disabled="creating"
        @keydown.enter.prevent="createItem"
      />
      <button
        type="button"
        class="task-subtasks__add-btn"
        :disabled="creating || !newTitle.trim()"
        @click="createItem"
      >
        <i class="fas fa-plus"></i>
        Добавить
      </button>
    </div>

    <!-- Assignee picker — рендерим через teleport в body, чтобы position:fixed
         не клиппился родительскими overflow:hidden / transform / filter
         (а у task-drawer есть и transform, и overflow). Раньше из-за
         этого поповер «улетал» в правую часть экрана. -->
    <teleport to="body">
      <div
        v-if="assigneePopover.open"
        class="task-subtasks__popover"
        :style="popoverStyle(assigneePopover)"
        v-modal-close="closeAssigneePicker"
        @click.stop
      >
        <div class="task-subtasks__popover-head">Ответственный</div>
        <input
          v-model="assigneeQuery"
          type="text"
          class="task-subtasks__popover-search"
          placeholder="Поиск…"
          autofocus
        />
        <div class="task-subtasks__popover-list">
          <button
            v-if="assigneePopover.item?.assigned_to_user_id"
            type="button"
            class="task-subtasks__popover-item task-subtasks__popover-item--clear"
            @click="setAssignee(assigneePopover.item, null)"
          >
            <i class="fas fa-times"></i>
            Снять ответственного
          </button>
          <button
            v-for="u in filteredUsers"
            :key="u.id"
            type="button"
            class="task-subtasks__popover-item"
            :class="{ 'task-subtasks__popover-item--active': assigneePopover.item?.assigned_to_user_id === u.id }"
            @click="setAssignee(assigneePopover.item, u.id)"
          >
            <UiAvatar :name="u.full_name" :src="getUserAvatarUrl(u.id)" size="xs" />
            <span>{{ u.full_name }}</span>
          </button>
        </div>
      </div>
    </teleport>

  </div>
</template>

<script>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import draggable from 'vuedraggable'
import * as apiTasks from '../../../services/api/tasks'
import UiAvatar from '../../../components/ui/UiAvatar.vue'
import { useToast } from '../../../composables/useToast'
import { normalizeAvatarUrl } from '../../../utils/avatar'

/**
 * Чек-лист подзадач для модалки задачи. Зависит только от `task-id` и
 * списка пользователей (нужны для аватаров/выбора ответственного).
 * Все CRUD — оптимистичные с откатом при ошибке: пользователь видит
 * мгновенный отклик, как и в чате.
 */
export default {
  name: 'TaskSubtasks',
  components: { draggable, UiAvatar },
  emits: ['update:modelValue'],
  props: {
    taskId: { type: String, default: null },
    users: { type: Array, default: () => [] },
    canEdit: { type: Boolean, default: true },
    // Local-only режим: всё, что обычно идёт PUT/POST/DELETE в API,
    // мутирует переданный массив и эмитит обратно через v-model.
    // Используется в форме создания НОВОЙ задачи (taskId ещё нет),
    // чтобы юзер мог собрать чек-лист до сохранения.
    localOnly: { type: Boolean, default: false },
    modelValue: { type: Array, default: () => [] },
  },
  setup(props, { emit }) {
    const { error: toastError } = useToast()

    const subtasks = ref([])
    const newTitle = ref('')
    const creating = ref(false)
    const editingId = ref(null)
    const editingTitle = ref('')
    const editInput = ref(null)
    const busyIds = ref(new Set())
    const hiddenDateInput = ref(null)

    const assigneePopover = ref({ open: false, item: null, x: 0, y: 0 })
    const assigneeQuery = ref('')

    const total = computed(() => subtasks.value.length)
    const doneCount = computed(() => subtasks.value.filter(s => s.is_done).length)
    const progressPercent = computed(() => {
      if (!total.value) return 0
      return Math.round((doneCount.value / total.value) * 100)
    })

    const usersById = computed(() => {
      const map = new Map()
      for (const u of (props.users || [])) map.set(String(u.id), u)
      return map
    })

    const getUserName = (id) => {
      if (!id) return ''
      const u = usersById.value.get(String(id))
      return u?.full_name || ''
    }
    const getUserAvatarUrl = (id) => {
      if (!id) return null
      const u = usersById.value.get(String(id))
      return normalizeAvatarUrl(u?.avatar_url)
    }

    const formatDate = (s) => {
      if (!s) return ''
      try {
        const d = new Date(s)
        if (Number.isNaN(d.getTime())) return s
        return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
      } catch {
        return s
      }
    }
    // Компактный формат для chip — день и месяц.
    const formatDateShort = (s) => {
      if (!s) return ''
      try {
        const d = new Date(s)
        if (Number.isNaN(d.getTime())) return s
        return d.toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' })
      } catch {
        return s
      }
    }

    const isOverdue = (item) => {
      if (!item?.due_date || item.is_done) return false
      try {
        const d = new Date(item.due_date)
        const today = new Date()
        today.setHours(0, 0, 0, 0)
        d.setHours(0, 0, 0, 0)
        return d < today
      } catch {
        return false
      }
    }

    // ── Helpers для local-only режима ──────────────────────────────────
    const genLocalId = () => `_tmp_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
    const emitChange = () => {
      if (!props.localOnly) return
      // Передаём чистый массив наружу (без Vue-прокси).
      emit('update:modelValue', subtasks.value.map(s => ({ ...s })))
    }

    const load = async () => {
      // Local-only: берём из modelValue (если что-то есть) и не лезем в API.
      if (props.localOnly) {
        subtasks.value = Array.isArray(props.modelValue)
          ? props.modelValue.map(s => ({ ...s }))
          : []
        return
      }
      if (!props.taskId) {
        subtasks.value = []
        return
      }
      try {
        const data = await apiTasks.listSubtasks(props.taskId)
        subtasks.value = Array.isArray(data) ? data : []
      } catch (e) {
        // 404/permission — тихо пустой список. Сетевые — показать.
        if (e?.response?.status !== 404) {
          console.warn('[subtasks] load failed', e)
        }
        subtasks.value = []
      }
    }

    const createItem = async () => {
      const title = (newTitle.value || '').trim()
      if (!title) return
      // Local-only: пушим в массив с temp id, эмитим, готово.
      if (props.localOnly) {
        subtasks.value.push({
          id: genLocalId(),
          title,
          is_done: false,
          is_urgent: false,
          assigned_to_user_id: null,
          assignee_name: null,
          due_date: null,
          due_time: null,
        })
        emitChange()
        newTitle.value = ''
        return
      }
      if (!props.taskId) return
      creating.value = true
      try {
        const created = await apiTasks.createSubtask(props.taskId, { title })
        if (created?.id) subtasks.value.push(created)
        newTitle.value = ''
      } catch (e) {
        console.error(e)
        toastError('Не удалось добавить пункт')
      } finally {
        creating.value = false
      }
    }

    const toggleDone = async (item) => {
      if (props.localOnly) {
        item.is_done = !item.is_done
        emitChange()
        return
      }
      const prev = item.is_done
      item.is_done = !item.is_done
      busyIds.value.add(item.id)
      try {
        const updated = await apiTasks.updateSubtask(item.id, { is_done: item.is_done })
        Object.assign(item, updated)
      } catch (e) {
        item.is_done = prev
        toastError('Не удалось обновить пункт')
      } finally {
        busyIds.value.delete(item.id)
      }
    }

    const startEdit = (item) => {
      editingId.value = item.id
      editingTitle.value = item.title
      nextTick(() => editInput.value?.focus?.())
    }
    const cancelEdit = () => {
      editingId.value = null
      editingTitle.value = ''
    }
    const commitEdit = async (item) => {
      if (editingId.value !== item.id) return
      const next = (editingTitle.value || '').trim()
      editingId.value = null
      if (!next || next === item.title) return
      if (props.localOnly) {
        item.title = next
        emitChange()
        return
      }
      const prev = item.title
      item.title = next
      try {
        const updated = await apiTasks.updateSubtask(item.id, { title: next })
        Object.assign(item, updated)
      } catch (e) {
        item.title = prev
        toastError('Не удалось переименовать пункт')
      }
    }

    const removeItem = async (item) => {
      const idx = subtasks.value.findIndex(s => s.id === item.id)
      if (idx < 0) return
      if (props.localOnly) {
        subtasks.value.splice(idx, 1)
        emitChange()
        return
      }
      const snapshot = subtasks.value[idx]
      subtasks.value.splice(idx, 1)
      try {
        await apiTasks.deleteSubtask(item.id)
      } catch (e) {
        // Откатываем в исходную позицию.
        subtasks.value.splice(idx, 0, snapshot)
        toastError('Не удалось удалить пункт')
      }
    }

    const onDragEnd = async () => {
      if (props.localOnly) {
        emitChange()
        return
      }
      if (!props.taskId) return
      const ids = subtasks.value.map(s => s.id)
      try {
        const updated = await apiTasks.reorderSubtasks(props.taskId, ids)
        if (Array.isArray(updated) && updated.length) {
          subtasks.value = updated
        }
      } catch (e) {
        toastError('Не удалось сохранить порядок')
        load()
      }
    }

    const POPOVER_W = 260
    const POPOVER_H = 320
    const openAssigneePicker = (item, ev) => {
      assigneeQuery.value = ''
      // Якорим к элементу, на который кликнули. Используем
      // currentTarget (chip-button или UiAvatar), но падаем на target
      // если UiAvatar внутренне переадресует event.
      const anchor = ev?.currentTarget || ev?.target
      const rect = anchor?.getBoundingClientRect?.()
      let x = rect ? rect.left : 8
      let y = rect ? rect.bottom + 4 : 8
      // Clamp в viewport — иначе поповер «улетал» за правый край при
      // открытии у chip, расположенного близко к правой границе модалки.
      if (typeof window !== 'undefined') {
        const vw = window.innerWidth
        const vh = window.innerHeight
        if (x + POPOVER_W > vw - 8) x = Math.max(8, vw - POPOVER_W - 8)
        if (x < 8) x = 8
        // Если внизу не помещается — показываем выше якоря.
        if (y + POPOVER_H > vh - 8 && rect) y = Math.max(8, rect.top - POPOVER_H - 4)
        if (y < 8) y = 8
      }
      assigneePopover.value = { open: true, item, x, y }
    }
    const closeAssigneePicker = () => {
      assigneePopover.value = { open: false, item: null, x: 0, y: 0 }
    }
    const filteredUsers = computed(() => {
      const q = (assigneeQuery.value || '').trim().toLowerCase()
      const list = props.users || []
      if (!q) return list.slice(0, 30)
      return list.filter(u => (u.full_name || '').toLowerCase().includes(q)).slice(0, 30)
    })
    const setAssignee = async (item, userId) => {
      const prev = item.assigned_to_user_id
      const prevName = item.assignee_name
      item.assigned_to_user_id = userId || null
      item.assignee_name = userId ? (usersById.value.get(String(userId))?.full_name || null) : null
      closeAssigneePicker()
      if (props.localOnly) {
        emitChange()
        return
      }
      try {
        const updated = await apiTasks.updateSubtask(item.id, {
          assigned_to_user_id: userId || '',
        })
        Object.assign(item, updated)
      } catch (e) {
        item.assigned_to_user_id = prev
        item.assignee_name = prevName
        toastError('Не удалось обновить ответственного')
      }
    }

    // Дату меняем прямо из inline-input на chip-е. `value` пуст → snap to null,
    // что в бэке трактуется как «снять дедлайн».
    const onDateChange = async (item, ev) => {
      if (!item) return
      const next = ev?.target?.value || null
      const prev = item.due_date
      const prevTime = item.due_time
      item.due_date = next
      if (!next) item.due_time = null
      if (props.localOnly) {
        emitChange()
        return
      }
      try {
        const payload = { due_date: next }
        if (!next) payload.due_time = ''
        const updated = await apiTasks.updateSubtask(item.id, payload)
        Object.assign(item, updated)
      } catch (e) {
        item.due_date = prev
        item.due_time = prevTime
        toastError('Не удалось установить дедлайн')
      }
    }

    const onTimeChange = async (item, ev) => {
      if (!item) return
      const next = ev?.target?.value || null
      const prev = item.due_time
      item.due_time = next
      if (props.localOnly) {
        emitChange()
        return
      }
      try {
        const updated = await apiTasks.updateSubtask(item.id, {
          due_time: next || '',
        })
        Object.assign(item, updated)
      } catch (e) {
        item.due_time = prev
        toastError('Не удалось установить время')
      }
    }

    const toggleUrgent = async (item) => {
      if (!item) return
      const next = !item.is_urgent
      const prev = item.is_urgent
      item.is_urgent = next
      if (props.localOnly) {
        emitChange()
        return
      }
      try {
        const updated = await apiTasks.updateSubtask(item.id, { is_urgent: next })
        Object.assign(item, updated)
      } catch (e) {
        item.is_urgent = prev
        toastError('Не удалось изменить флаг')
      }
    }

    const popoverStyle = (popover) => ({
      position: 'fixed',
      left: `${popover.x}px`,
      top: `${popover.y}px`,
      zIndex: 9999,
    })

    watch(() => props.taskId, load, { immediate: true })
    // Local-only: переинициализация при смене localOnly или сброса
    // массива снаружи (например, после успешного save новой задачи
    // parent сбрасывает pending до пустого массива).
    watch(() => [props.localOnly, props.modelValue], () => {
      if (props.localOnly) load()
    }, { deep: false })

    onBeforeUnmount(() => {
      closeAssigneePicker()
    })

    return {
      subtasks, total, doneCount, progressPercent,
      newTitle, creating, editingId, editingTitle, editInput, busyIds,
      assigneePopover, assigneeQuery, filteredUsers,
      getUserName, getUserAvatarUrl,
      formatDate, formatDateShort, isOverdue,
      createItem, toggleDone, startEdit, cancelEdit, commitEdit, removeItem,
      onDragEnd, openAssigneePicker, closeAssigneePicker, setAssignee,
      onDateChange, onTimeChange, toggleUrgent, popoverStyle, load,
    }
  },
}
</script>

<style scoped>
.task-subtasks {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: var(--color-surface-2, #f8fafc);
  border: 1px solid var(--color-border-subtle, #e2e8f0);
  border-radius: var(--radius-md, 8px);
}

.task-subtasks__head {
  display: flex;
  align-items: center;
  gap: 12px;
}
.task-subtasks__title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: var(--text-sm, 0.875rem);
  font-weight: var(--fw-semibold, 600);
  color: var(--color-text, #0f172a);
}
/* Иконка списка — slate-900 (как заголовки/иконки в Tasks-drawer),
   а не --color-primary, чтобы шапка чек-листа не контрастировала
   с остальным стилем drawer'а. */
.task-subtasks__title i { color: var(--color-text, #0f172a); }
.task-subtasks__counter {
  padding: 1px 8px;
  border-radius: 999px;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e2e8f0);
  font-size: 11px;
  font-weight: var(--fw-bold, 700);
  color: var(--color-text-muted, #64748b);
}
.task-subtasks__progress {
  flex: 1 1 auto;
  height: 4px;
  background: var(--color-surface, #fff);
  border-radius: 999px;
  overflow: hidden;
  border: 1px solid var(--color-border-subtle, #e2e8f0);
}
.task-subtasks__progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #16a34a, #22c55e);
  transition: width 0.2s ease;
}

.task-subtasks__list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.task-subtasks__empty {
  padding: 16px;
  text-align: center;
  color: var(--color-text-muted, #64748b);
  font-size: var(--text-sm, 0.875rem);
  background: var(--color-surface, #fff);
  border: 1px dashed var(--color-border, #cbd5e1);
  border-radius: var(--radius-sm, 6px);
}

.task-subtask {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border-subtle, #e2e8f0);
  border-radius: var(--radius-sm, 6px);
  transition: background 0.15s ease, border-color 0.15s ease;
}
.task-subtask:hover {
  border-color: var(--color-border, #cbd5e1);
}
.task-subtask--done .task-subtask__title {
  color: var(--color-text-subtle, #94a3b8);
  text-decoration: line-through;
}

.task-subtask--ghost {
  background: rgba(33, 150, 243, 0.06) !important;
  border: 2px dashed rgba(33, 150, 243, 0.45) !important;
}
.task-subtask--chosen { opacity: 0.5; }

.task-subtask__drag {
  border: none;
  background: transparent;
  color: var(--color-text-subtle, #94a3b8);
  cursor: grab;
  padding: 2px 4px;
  font-size: 12px;
}
.task-subtask__drag:active { cursor: grabbing; }

.task-subtask__check {
  position: relative;
  display: inline-flex;
  align-items: center;
  cursor: pointer;
}
.task-subtask__check input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}
.task-subtask__check-box {
  width: 18px;
  height: 18px;
  border-radius: 4px;
  border: 1.5px solid var(--color-border, #cbd5e1);
  background: var(--color-surface, #fff);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s ease, border-color 0.15s ease;
}
.task-subtask__check-box::after {
  content: '\f00c';
  font-family: 'Font Awesome 6 Free';
  font-weight: 900;
  font-size: 11px;
  color: #fff;
  opacity: 0;
  transform: scale(0.6);
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.task-subtask__check input:checked + .task-subtask__check-box {
  background: #16a34a;
  border-color: #16a34a;
}
.task-subtask__check input:checked + .task-subtask__check-box::after {
  opacity: 1;
  transform: scale(1);
}
.task-subtask__check input:disabled + .task-subtask__check-box {
  opacity: 0.6;
  cursor: not-allowed;
}

.task-subtask__body {
  flex: 1 1 auto;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.task-subtask__title {
  flex: 1 1 auto;
  min-width: 0;
  font-size: var(--text-sm, 0.875rem);
  color: var(--color-text, #0f172a);
  cursor: text;
  word-break: break-word;
}
.task-subtask__title-input {
  flex: 1 1 auto;
  min-width: 0;
  height: 24px;
  border: 1px solid var(--color-primary, #2563eb);
  border-radius: 4px;
  padding: 0 6px;
  font-size: var(--text-sm, 0.875rem);
  background: var(--color-surface, #fff);
  outline: none;
}

.task-subtask__meta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}
.task-subtask__avatar {
  cursor: pointer;
}
.task-subtask__chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  height: 22px;
  border-radius: 4px;
  border: 1px solid var(--color-border-subtle, #e2e8f0);
  background: var(--color-surface, #fff);
  color: var(--color-text-muted, #64748b);
  font-size: 11px;
  cursor: pointer;
  white-space: nowrap;
}
.task-subtask__chip:hover {
  border-color: var(--color-primary, #2563eb);
  color: var(--color-primary, #2563eb);
}
.task-subtask__chip--add {
  width: 22px;
  justify-content: center;
  padding: 0;
}
.task-subtask__chip--overdue {
  color: var(--color-danger, #dc2626);
  border-color: rgba(220, 38, 38, 0.3);
  background: rgba(220, 38, 38, 0.06);
}

.task-subtask__delete {
  border: none;
  background: transparent;
  color: var(--color-text-subtle, #94a3b8);
  cursor: pointer;
  padding: 2px 6px;
  opacity: 0;
  transition: opacity 0.15s ease, color 0.15s ease;
}
.task-subtask:hover .task-subtask__delete { opacity: 1; }
.task-subtask__delete:hover { color: var(--color-danger, #dc2626); }

.task-subtasks__add {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-top: 4px;
}
.task-subtasks__add-input {
  flex: 1 1 auto;
  height: 32px;
  padding: 0 10px;
  border: 1px solid var(--color-border, #cbd5e1);
  border-radius: var(--radius-sm, 6px);
  background: var(--color-surface, #fff);
  font-size: var(--text-sm, 0.875rem);
  outline: none;
}
.task-subtasks__add-input:focus {
  border-color: var(--color-primary, #2563eb);
}
/* Кнопка «Добавить пункт» — slate-900 фон вместо синего. Совпадает
   с цветовым языком Tasks-drawer (primary-action buttons там тоже
   slate-900, не blue-600). */
.task-subtasks__add-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 12px;
  border-radius: var(--radius-sm, 6px);
  border: 1px solid var(--color-text, #0f172a);
  background: var(--color-text, #0f172a);
  color: var(--color-on-text, #fff);
  font-size: var(--text-sm, 0.875rem);
  cursor: pointer;
  transition: background 0.12s, border-color 0.12s, opacity 0.12s;
}
.task-subtasks__add-btn:hover:not(:disabled) {
  background: var(--color-text-strong, #020617);
  border-color: var(--color-text-strong, #020617);
}
.task-subtasks__add-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

/* Popover для выбора ответственного. fixed-позиционирование, чтобы
   не зависело от overflow родительской модалки. */
.task-subtasks__popover {
  width: 260px;
  max-height: 320px;
  display: flex;
  flex-direction: column;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #cbd5e1);
  border-radius: var(--radius-md, 8px);
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.16);
  overflow: hidden;
}
.task-subtasks__popover-head {
  padding: 8px 12px;
  font-size: 11px;
  font-weight: var(--fw-bold, 700);
  text-transform: uppercase;
  letter-spacing: 0.4px;
  color: var(--color-text-muted, #64748b);
  background: var(--color-surface-2, #f8fafc);
  border-bottom: 1px solid var(--color-border-subtle, #e2e8f0);
}
.task-subtasks__popover-search {
  width: 100%;
  height: 30px;
  border: 0;
  border-bottom: 1px solid var(--color-border-subtle, #e2e8f0);
  padding: 0 10px;
  font-size: var(--text-sm, 0.875rem);
  outline: none;
}
.task-subtasks__popover-list {
  overflow-y: auto;
  padding: 4px 0;
}
.task-subtasks__popover-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 6px 10px;
  border: 0;
  background: transparent;
  cursor: pointer;
  text-align: left;
  font-size: var(--text-sm, 0.875rem);
  color: var(--color-text, #0f172a);
}
.task-subtasks__popover-item:hover {
  background: var(--color-surface-2, #f8fafc);
}
.task-subtasks__popover-item--active {
  background: var(--color-primary-soft, rgba(37, 99, 235, 0.08));
  color: var(--color-primary, #2563eb);
}
.task-subtasks__popover-item--clear {
  color: var(--color-text-muted, #64748b);
  border-bottom: 1px solid var(--color-border-subtle, #e2e8f0);
}

/* Дата/время как chip: visible chip-content (иконка + текст) под
   прозрачным native input. Клик по chip-зоне сразу открывает нативный
   календарь/тайм-пикер ровно под кнопкой — без showPicker()-хака. */
.task-subtask__date-chip,
.task-subtask__time-chip {
  position: relative;
  cursor: pointer;
}
.task-subtask__overlay-input {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: transparent;
  cursor: pointer;
  /* Скрываем встроенный текст value и иконку у нативного input —
     нам нужны только клик-зона и picker. */
  font-size: 0;
  opacity: 0;
}
.task-subtask__overlay-input::-webkit-calendar-picker-indicator {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
  cursor: pointer;
  opacity: 0;
}
.task-subtask__overlay-input:disabled {
  cursor: not-allowed;
}

/* Огонёк: chip-кнопка, активный — красный fire (тот же цвет, что у
   urgent-приоритета задачи: #dc2626). Неактивный — приглушённый серый,
   чтобы зона клика была видна, но не отвлекала. */
.task-subtask__fire-chip {
  cursor: pointer;
  color: var(--color-text-subtle, #94a3b8);
  border-color: var(--color-border-subtle, #e2e8f0);
}
.task-subtask__fire-chip:hover {
  color: #dc2626;
  border-color: rgba(220, 38, 38, 0.4);
  background: rgba(220, 38, 38, 0.04);
}
.task-subtask__fire-chip--active {
  color: #dc2626;
  border-color: rgba(220, 38, 38, 0.5);
  background: rgba(220, 38, 38, 0.10);
}
.task-subtask__fire-chip--active:hover {
  background: rgba(220, 38, 38, 0.16);
}
.task-subtask__fire-chip:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}
</style>
