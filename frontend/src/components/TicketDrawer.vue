<template>
  <transition name="tk-dr-slide">
    <div v-if="modelValue" class="tk-dr-overlay" @click.self="close">
      <aside
        class="tk-dr"
        role="dialog"
        aria-modal="true"
        :class="{ 'tk-dr--tabs': layoutMode !== 'split', 'tk-dr--mobile': layoutMode === 'mobile', 'tk-dr--chat': layoutMode !== 'split' && tab === 'chat' }"
        @click.stop
      >
        <header class="tk-dr__header">
          <button type="button" class="tk-dr__icon-btn" title="Закрыть (Esc)" @click="close">
            <i class="fas fa-arrow-left"></i>
          </button>
          <div class="tk-dr__crumbs">
            <span v-if="mode === 'view' && ticket" class="tk-dr__code">#{{ ticket.number }}</span>
            <span v-if="mode === 'view' && ticket" class="tk-dr__sep">·</span>
            <span class="tk-dr__crumb-label">{{ mode === 'create' ? 'Новое обращение' : 'Тех. поддержка' }}</span>
          </div>

          <nav v-if="layoutMode !== 'split' && mode === 'view'" class="tk-dr__tabs">
            <button type="button" class="tk-dr__tab" :class="{ 'is-active': tab === 'main' }" @click="tab = 'main'">
              <i class="far fa-clipboard"></i><span>Тикет</span>
            </button>
            <button type="button" class="tk-dr__tab" :class="{ 'is-active': tab === 'chat' }" @click="tab = 'chat'">
              <i class="far fa-comment-dots"></i><span>Чат</span>
            </button>
          </nav>

          <div class="tk-dr__header-actions">
            <button type="button" class="tk-dr__icon-btn" title="Закрыть" @click="close">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </header>

        <div v-if="loading" class="tk-dr__loading"><i class="fas fa-spinner fa-spin"></i> Загрузка…</div>

        <div v-else class="tk-dr__body">
          <!-- LEFT: ticket / form -->
          <section
            v-show="layoutMode === 'split' || tab === 'main'"
            class="tk-dr__main"
            :style="layoutMode === 'split' && mode === 'view' ? { flexBasis: '54%' } : null"
          >
            <div class="tk-dr__scroll">
              <!-- CREATE -->
              <template v-if="mode === 'create'">
                <input
                  v-model="form.subject"
                  type="text"
                  class="tk-dr__title-input"
                  placeholder="Тема обращения"
                />
                <div class="tk-dr__field">
                  <label class="tk-dr__label">Категория</label>
                  <div class="tk-dr__cat-row">
                    <button
                      v-for="c in CATEGORY_LIST"
                      :key="c.value"
                      type="button"
                      class="tk-dr__cat"
                      :class="{ 'is-active': form.category === c.value }"
                      @click="form.category = c.value"
                    >{{ c.label }}</button>
                  </div>
                </div>
                <div class="tk-dr__field">
                  <label class="tk-dr__label">Описание</label>
                  <textarea
                    v-model="form.description"
                    class="tk-dr__textarea"
                    rows="6"
                    placeholder="Подробно опишите проблему или запрос. Можно вставить скрин из буфера (Ctrl+V)."
                    @paste="onPaste"
                  ></textarea>
                </div>
                <div class="tk-dr__field">
                  <label class="tk-dr__label">Файлы (Word, PDF, JPG, PNG)</label>
                  <button type="button" class="tk-dr__files-add" @click="$refs.fileInput.click()">
                    <i class="fas fa-paperclip"></i> Прикрепить
                  </button>
                  <input ref="fileInput" type="file" multiple class="tk-dr__file-hidden"
                         accept=".doc,.docx,.pdf,image/png,image/jpeg,image/gif" @change="onPick" />
                  <div v-if="form.files.length" class="tk-dr__files">
                    <div v-for="(f, i) in form.files" :key="i" class="tk-dr__file">
                      <i class="fas fa-paperclip"></i><span>{{ f.name }}</span>
                      <button type="button" @click="form.files.splice(i, 1)"><i class="fas fa-times"></i></button>
                    </div>
                  </div>
                </div>
              </template>

              <!-- VIEW -->
              <template v-else-if="ticket">
                <div class="tk-dr__title">{{ ticket.subject }}</div>
                <div class="tk-dr__chips">
                  <span class="tk-chip" :class="`tk-chip--cat-${ticket.category}`">{{ catLabel(ticket.category) }}</span>
                  <span v-if="!isStaff" class="tk-chip" :class="`tk-chip--st-${ticket.status}`">{{ stLabel(ticket.status) }}</span>
                  <router-link
                    v-if="ticket.linked_task_id"
                    :to="`/tasks?task_id=${ticket.linked_task_id}`"
                    class="tk-dr__tasklink"
                  >
                    <i class="fas fa-up-right-from-square"></i> Задача #{{ ticket.linked_task_number }}
                  </router-link>
                </div>

                <div v-if="isStaff" class="tk-dr__controls">
                  <label class="tk-dr__ctl">
                    <span>Статус</span>
                    <select v-model="ticket.status" @change="changeStatus">
                      <option v-for="s in STATUS_LIST" :key="s.value" :value="s.value">{{ s.label }}</option>
                    </select>
                  </label>
                  <label class="tk-dr__ctl">
                    <span>Исполнитель</span>
                    <select v-model="assigneeModel" @change="changeAssignee">
                      <option value="">— не назначен —</option>
                      <option v-for="u in users" :key="u.id" :value="u.id">{{ u.full_name }}</option>
                    </select>
                  </label>
                  <label class="tk-dr__ctl">
                    <span>Категория</span>
                    <select v-model="ticket.category" @change="changeCategory">
                      <option v-for="c in CATEGORY_LIST" :key="c.value" :value="c.value">{{ c.label }}</option>
                    </select>
                  </label>
                  <button type="button" class="tk-dr__mkbtn" @click="openTaskModal">
                    <i class="fas fa-list-check"></i> Создать задачу
                  </button>
                </div>

                <div class="tk-dr__field">
                  <label class="tk-dr__label">Описание</label>
                  <div class="tk-dr__desc">{{ ticket.description || '—' }}</div>
                </div>

                <div v-if="ticket.attachments && ticket.attachments.length" class="tk-dr__field">
                  <label class="tk-dr__label">Вложения</label>
                  <div class="tk-dr__files">
                    <button
                      v-for="(f, i) in ticket.attachments"
                      :key="i"
                      type="button"
                      class="tk-dr__file"
                      @click="download(f)"
                    >
                      <i class="fas fa-paperclip"></i><span>{{ f.name }}</span>
                    </button>
                  </div>
                </div>
              </template>
            </div>

            <footer v-if="mode === 'create'" class="tk-dr__footer">
              <button type="button" class="tk-dr__btn" @click="close">Отмена</button>
              <button
                type="button"
                class="tk-dr__btn tk-dr__btn--primary"
                :disabled="saving || !form.subject.trim()"
                @click="submitCreate"
              >
                <i v-if="saving" class="fas fa-spinner fa-spin"></i>
                Отправить
              </button>
            </footer>
          </section>

          <!-- RIGHT: chat -->
          <section
            v-if="mode === 'view' && ticket"
            v-show="layoutMode === 'split' || tab === 'chat'"
            class="tk-dr__chat"
          >
            <TicketChat :ticket-id="ticket.id" :is-staff="isStaff" :can-write="true" @updated="onChatUpdated" />
          </section>
        </div>
      </aside>
    </div>
  </transition>

  <!-- Создать задачу из тикета -->
  <transition name="tk-dr-fade">
    <div v-if="taskModal.open" class="tk-dr-overlay tk-dr-overlay--center" @click.self="taskModal.open = false">
      <div class="tk-dr-modal">
        <header class="tk-dr-modal__head">
          <h3>Задача из тикета #{{ ticket && ticket.number }}</h3>
          <button type="button" @click="taskModal.open = false"><i class="fas fa-times"></i></button>
        </header>
        <div class="tk-dr-modal__body">
          <label class="tk-dr__field"><span class="tk-dr__label">Название</span>
            <input v-model="taskModal.title" class="tk-dr__inp" type="text" /></label>
          <label class="tk-dr__field"><span class="tk-dr__label">Описание</span>
            <textarea v-model="taskModal.description" class="tk-dr__textarea" rows="4"></textarea></label>
          <div class="tk-dr__grid2">
            <label class="tk-dr__field"><span class="tk-dr__label">Исполнитель</span>
              <select v-model="taskModal.assigned_to_user_id" class="tk-dr__inp">
                <option value="">— не назначен —</option>
                <option v-for="u in users" :key="u.id" :value="u.id">{{ u.full_name }}</option>
              </select></label>
            <label class="tk-dr__field"><span class="tk-dr__label">Приоритет</span>
              <select v-model="taskModal.priority" class="tk-dr__inp">
                <option value="low">Низкий</option>
                <option value="normal">Обычный</option>
                <option value="high">Высокий</option>
                <option value="urgent">Срочный</option>
              </select></label>
            <label class="tk-dr__field"><span class="tk-dr__label">Начало</span>
              <input v-model="taskModal.start_date" type="date" class="tk-dr__inp" /></label>
            <label class="tk-dr__field"><span class="tk-dr__label">Срок</span>
              <input v-model="taskModal.due_date" type="date" class="tk-dr__inp" /></label>
          </div>
        </div>
        <footer class="tk-dr-modal__foot">
          <button type="button" class="tk-dr__btn" @click="taskModal.open = false">Отмена</button>
          <button type="button" class="tk-dr__btn tk-dr__btn--primary" :disabled="taskModal.saving || !taskModal.title.trim()" @click="submitCreateTask">
            Создать задачу
          </button>
        </footer>
      </div>
    </div>
  </transition>
</template>

<script>
import { reactive, ref, watch, computed, onMounted, onBeforeUnmount } from 'vue'
import { api } from '@/services/api'
import { useToast } from '../composables/useToast'
import { downloadFromApi } from '../utils/download'
import TicketChat from './TicketChat.vue'

const CATEGORY_LIST = [
  { value: 'bug', label: 'Ошибка / баг' },
  { value: 'improvement', label: 'Доработка / улучшение' },
  { value: 'access', label: 'Доступ и администрирование' },
  { value: 'question', label: 'Вопрос / консультация' },
  { value: 'other', label: 'Прочее' },
]
const STATUS_LIST = [
  { value: 'new', label: 'Новый' },
  { value: 'in_progress', label: 'В работе' },
  { value: 'waiting_user', label: 'Ожидает ответа' },
  { value: 'resolved', label: 'Решён' },
  { value: 'closed', label: 'Закрыт' },
  { value: 'rejected', label: 'Отклонён' },
]

export default {
  name: 'TicketDrawer',
  components: { TicketChat },
  props: {
    modelValue: { type: Boolean, default: false },
    mode: { type: String, default: 'view' }, // 'create' | 'view'
    ticketId: { type: [String, Number, null], default: null },
    isStaff: { type: Boolean, default: false },
    users: { type: Array, default: () => [] },
  },
  emits: ['update:modelValue', 'saved'],
  setup(props, { emit }) {
    const toast = useToast()
    const ticket = ref(null)
    const loading = ref(false)
    const saving = ref(false)
    const tab = ref('main')
    const assigneeModel = ref('')
    const fileInput = ref(null)
    const form = reactive({ subject: '', category: 'other', description: '', files: [] })
    const taskModal = reactive({
      open: false, saving: false, title: '', description: '',
      assigned_to_user_id: '', priority: 'normal', start_date: '', due_date: '',
    })

    const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1440)
    const onResize = () => { viewportWidth.value = window.innerWidth }
    const layoutMode = computed(() => {
      if (viewportWidth.value < 680) return 'mobile'
      if (viewportWidth.value < 1100) return 'tabs'
      return 'split'
    })

    const catLabel = (v) => (CATEGORY_LIST.find((c) => c.value === v) || {}).label || v
    const stLabel = (v) => (STATUS_LIST.find((s) => s.value === v) || {}).label || v

    const close = () => emit('update:modelValue', false)

    const loadTicket = async () => {
      if (props.mode !== 'view' || !props.ticketId) return
      loading.value = true
      try {
        ticket.value = await api.support.getTicket(props.ticketId)
        assigneeModel.value = ticket.value.assignee_id || ''
      } catch (e) {
        toast.error('Не удалось открыть тикет')
        close()
      } finally {
        loading.value = false
      }
    }

    const resetForm = () => {
      form.subject = ''
      form.category = 'other'
      form.description = ''
      form.files = []
    }

    watch(() => props.modelValue, (open) => {
      if (!open) return
      tab.value = 'main'
      if (props.mode === 'create') { resetForm(); ticket.value = null }
      else loadTicket()
    })

    const onPick = (e) => {
      const fs = Array.from(e.target.files || [])
      if (fs.length) form.files.push(...fs)
      e.target.value = ''
    }
    const onPaste = (e) => {
      const items = e.clipboardData && e.clipboardData.items
      if (!items) return
      for (const it of items) {
        if (it.kind === 'file' && it.type.startsWith('image/')) {
          const blob = it.getAsFile()
          if (blob) {
            const ext = (it.type.split('/')[1] || 'png').split('+')[0]
            form.files.push(new File([blob], `screenshot-${Date.now()}.${ext}`, { type: it.type }))
          }
        }
      }
    }
    const submitCreate = async () => {
      if (!form.subject.trim()) return
      saving.value = true
      try {
        const fd = new FormData()
        fd.append('subject', form.subject.trim())
        fd.append('category', form.category)
        if (form.description.trim()) fd.append('description', form.description.trim())
        form.files.forEach((f) => fd.append('files', f, f.name))
        const created = await api.support.createTicket(fd)
        toast.success(`Обращение #${created.number} создано`)
        emit('saved')
        close() // НЕ открываем чат после создания
      } catch (e) {
        toast.error(e?.response?.data?.detail || 'Не удалось создать обращение')
      } finally {
        saving.value = false
      }
    }

    const changeStatus = async () => {
      try {
        await api.support.updateTicket(ticket.value.id, { status: ticket.value.status })
        toast.success('Статус обновлён')
        emit('saved')
      } catch (e) { toast.error('Не удалось изменить статус') }
    }
    const changeAssignee = async () => {
      try {
        const upd = await api.support.updateTicket(ticket.value.id, { assignee_id: assigneeModel.value || null })
        ticket.value.assignee_id = upd.assignee_id
        ticket.value.assignee_name = upd.assignee_name
        emit('saved')
      } catch (e) { toast.error('Не удалось назначить исполнителя') }
    }
    const changeCategory = async () => {
      try {
        await api.support.updateTicket(ticket.value.id, { category: ticket.value.category })
        emit('saved')
      } catch (e) { toast.error('Не удалось изменить категорию') }
    }

    const openTaskModal = () => {
      taskModal.title = ticket.value.subject || ''
      taskModal.description = ticket.value.description || ''
      taskModal.assigned_to_user_id = ticket.value.assignee_id || ''
      taskModal.priority = 'normal'
      taskModal.start_date = ''
      taskModal.due_date = ''
      taskModal.open = true
    }
    const submitCreateTask = async () => {
      if (!taskModal.title.trim()) return
      taskModal.saving = true
      try {
        const res = await api.support.createTaskFromTicket(ticket.value.id, {
          title: taskModal.title.trim(),
          description: taskModal.description || null,
          assigned_to_user_id: taskModal.assigned_to_user_id || null,
          priority: taskModal.priority,
          start_date: taskModal.start_date || null,
          due_date: taskModal.due_date || null,
        })
        taskModal.open = false
        toast.success(`Создана задача #${res.task_number}`)
        await loadTicket()
        emit('saved')
      } catch (e) {
        toast.error(e?.response?.data?.detail || 'Не удалось создать задачу')
      } finally {
        taskModal.saving = false
      }
    }

    const onChatUpdated = (data) => {
      if (data && data.id) {
        ticket.value = { ...ticket.value, ...data }
        assigneeModel.value = ticket.value.assignee_id || ''
      }
      emit('saved')
    }
    const download = async (f) => {
      try {
        if (f?.download_url) await downloadFromApi(f.download_url, {}, f.name || 'file', { module: 'support' })
      } catch (e) { toast.error('Не удалось скачать файл') }
    }

    const onKey = (e) => { if (e.key === 'Escape' && props.modelValue) close() }
    onMounted(() => {
      window.addEventListener('resize', onResize, { passive: true })
      window.addEventListener('keydown', onKey)
    })
    onBeforeUnmount(() => {
      window.removeEventListener('resize', onResize)
      window.removeEventListener('keydown', onKey)
    })

    return {
      ticket, loading, saving, tab, layoutMode, assigneeModel, fileInput,
      form, taskModal, CATEGORY_LIST, STATUS_LIST,
      catLabel, stLabel, close, onPick, onPaste, submitCreate,
      changeStatus, changeAssignee, changeCategory,
      openTaskModal, submitCreateTask, onChatUpdated, download,
    }
  },
}
</script>

<style scoped>
.tk-dr-overlay {
  position: fixed; inset: 0; z-index: 1600;
  background: rgba(15, 23, 42, 0.2);
  display: flex; justify-content: flex-end;
  backdrop-filter: blur(4px);
}
.tk-dr-overlay--center { justify-content: center; align-items: center; padding: 24px; z-index: 1700; }
.tk-dr {
  display: flex; flex-direction: column; height: 100%;
  width: min(1080px, 94vw);
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border-left: 1px solid var(--glass-border-light);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
}
.tk-dr--tabs { width: min(720px, 96vw); }
.tk-dr--mobile { width: 100vw; }
@supports not (backdrop-filter: blur(1px)) { .tk-dr { background: var(--color-surface); } }
:root[data-theme="dark"] .tk-dr { background: rgba(20, 28, 44, 0.92); }

.tk-dr-slide-enter-active, .tk-dr-slide-leave-active { transition: opacity var(--dur-base) var(--ease-out); }
.tk-dr-slide-enter-active .tk-dr, .tk-dr-slide-leave-active .tk-dr { transition: transform var(--dur-slow) var(--ease-out); }
.tk-dr-slide-enter-from .tk-dr, .tk-dr-slide-leave-to .tk-dr { transform: translateX(100%); }
.tk-dr-slide-enter-from, .tk-dr-slide-leave-to { opacity: 0; }
.tk-dr-fade-enter-active, .tk-dr-fade-leave-active { transition: opacity 0.15s ease; }
.tk-dr-fade-enter-from, .tk-dr-fade-leave-to { opacity: 0; }

.tk-dr__header {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--glass-border-light);
  background: rgba(255, 255, 255, 0.55);
  flex-shrink: 0;
}
:root[data-theme="dark"] .tk-dr__header { background: rgba(15, 23, 42, 0.5); }
.tk-dr__icon-btn {
  width: 32px; height: 32px; border: 0; border-radius: var(--radius-sm);
  background: transparent; color: var(--color-text-muted); cursor: pointer;
  display: inline-flex; align-items: center; justify-content: center;
}
.tk-dr__icon-btn:hover { background: var(--color-surface-2); color: var(--color-text); }
.tk-dr__crumbs { display: flex; align-items: center; gap: var(--space-2); font-size: var(--text-sm); color: var(--color-text-muted); min-width: 0; }
.tk-dr__code { font-family: var(--font-mono); font-weight: var(--fw-semibold); color: var(--color-text); }
.tk-dr__sep { opacity: 0.5; }
.tk-dr__tabs { display: flex; gap: var(--space-1); margin-left: auto; }
.tk-dr__tab {
  display: inline-flex; align-items: center; gap: 6px; padding: 6px var(--space-3);
  border: 0; border-radius: var(--radius-pill); background: transparent;
  font-size: var(--text-base); color: var(--color-text-muted); cursor: pointer;
}
.tk-dr__tab:hover { background: var(--color-surface-2); color: var(--color-text); }
.tk-dr__tab.is-active { background: var(--color-primary-soft); color: var(--color-primary); }
.tk-dr__header-actions { display: flex; align-items: center; gap: var(--space-1); margin-left: auto; }
.tk-dr--tabs .tk-dr__tabs + .tk-dr__header-actions,
.tk-dr__tabs ~ .tk-dr__header-actions { margin-left: var(--space-2); }

.tk-dr__loading { padding: var(--space-10); text-align: center; color: var(--color-text-muted); }
.tk-dr__body { flex: 1 1 auto; min-height: 0; display: flex; }
.tk-dr__main { display: flex; flex-direction: column; min-width: 0; flex: 1 1 auto; background: transparent; }
.tk-dr--tabs .tk-dr__main { flex-basis: 100% !important; }
.tk-dr__scroll {
  overflow-y: auto; flex: 1 1 auto; min-height: 0;
  padding: var(--space-5) var(--space-6) var(--space-8);
  display: flex; flex-direction: column; gap: var(--space-4);
}
.tk-dr__title-input {
  width: 100%; border: 0; background: transparent; padding: 0;
  font-size: var(--text-2xl); font-weight: var(--fw-semibold);
  color: var(--color-text); outline: none; line-height: var(--leading-tight);
}
.tk-dr__title-input::placeholder { color: var(--color-text-subtle); font-weight: var(--fw-regular); }
.tk-dr__title { font-size: var(--text-2xl); font-weight: var(--fw-semibold); color: var(--color-text); line-height: var(--leading-tight); }
.tk-dr__chips { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.tk-dr__tasklink { margin-left: auto; font-size: var(--text-sm); color: var(--color-primary); text-decoration: none; font-weight: var(--fw-semibold); }
.tk-chip { display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px; border-radius: var(--radius-pill); font-size: var(--text-xs); font-weight: var(--fw-bold); background: var(--color-surface-3); color: var(--color-text-muted); }
.tk-chip--cat-bug { background: var(--color-danger-soft); color: var(--color-danger); }
.tk-chip--cat-improvement { background: var(--color-primary-soft); color: var(--color-primary); }
.tk-chip--cat-access { background: color-mix(in srgb, var(--color-warning) 16%, transparent); color: var(--color-warning); }
.tk-chip--cat-question { background: color-mix(in srgb, #0d9488 16%, transparent); color: #0d9488; }
.tk-chip--st-new { background: var(--color-primary-soft); color: var(--color-primary); }
.tk-chip--st-in_progress { background: color-mix(in srgb, var(--color-warning) 16%, transparent); color: var(--color-warning); }
.tk-chip--st-waiting_user { background: color-mix(in srgb, #7c3aed 16%, transparent); color: #7c3aed; }
.tk-chip--st-resolved, .tk-chip--st-closed { background: var(--color-success-soft); color: var(--color-success); }
.tk-chip--st-rejected { background: var(--color-danger-soft); color: var(--color-danger); }
.tk-dr__controls { display: flex; flex-wrap: wrap; gap: 10px; align-items: flex-end; padding: var(--space-3); background: rgba(255,255,255,0.5); border: 1px solid var(--glass-border-light); border-radius: var(--radius-md); }
:root[data-theme="dark"] .tk-dr__controls { background: rgba(255,255,255,0.04); }
.tk-dr__ctl { display: flex; flex-direction: column; gap: 4px; font-size: var(--text-xs); font-weight: var(--fw-semibold); color: var(--color-text-muted); }
.tk-dr__ctl select { min-height: 34px; padding: 0 8px; border: 1px solid var(--color-border); border-radius: var(--radius-sm); background: var(--color-surface); color: var(--color-text); font-size: var(--text-sm); cursor: pointer; }
.tk-dr__mkbtn { min-height: 34px; padding: 0 12px; border: 1px solid var(--color-primary); border-radius: var(--radius-sm); background: var(--color-primary-soft); color: var(--color-primary); font-weight: var(--fw-semibold); font-size: var(--text-sm); cursor: pointer; }
.tk-dr__field { display: flex; flex-direction: column; gap: var(--space-2); }
.tk-dr__label { font-size: var(--text-sm); font-weight: var(--fw-medium); color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.04em; }
.tk-dr__desc { white-space: pre-wrap; font-size: var(--text-md); color: var(--color-text); line-height: var(--leading-normal); }
.tk-dr__textarea, .tk-dr__inp {
  width: 100%; background: rgba(255,255,255,0.6); border: 1px solid var(--glass-border-light);
  border-radius: var(--radius-md); padding: var(--space-3); font: inherit; font-size: var(--text-md);
  color: var(--color-text); outline: none; resize: vertical;
}
:root[data-theme="dark"] .tk-dr__textarea, :root[data-theme="dark"] .tk-dr__inp { background: rgba(255,255,255,0.05); }
.tk-dr__textarea:focus, .tk-dr__inp:focus { border-color: var(--color-primary); box-shadow: var(--shadow-focus); }
.tk-dr__cat-row { display: flex; flex-wrap: wrap; gap: 6px; }
.tk-dr__cat { padding: 6px 12px; border: 1px solid var(--color-border); border-radius: var(--radius-pill); background: var(--color-surface); color: var(--color-text-muted); font-size: var(--text-sm); font-weight: var(--fw-semibold); cursor: pointer; }
.tk-dr__cat.is-active { background: var(--color-primary-soft); border-color: var(--color-primary); color: var(--color-primary); }
.tk-dr__files-add { align-self: flex-start; display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px; border: 1px dashed var(--color-border-strong); border-radius: var(--radius-pill); background: transparent; color: var(--color-text-muted); font-size: var(--text-sm); cursor: pointer; }
.tk-dr__file-hidden { display: none; }
.tk-dr__files { display: flex; flex-direction: column; gap: 4px; }
.tk-dr__file { display: inline-flex; align-items: center; gap: 8px; padding: 6px 10px; border: 1px solid var(--color-border); border-radius: var(--radius-sm); background: var(--color-surface-2); font-size: var(--text-sm); color: var(--color-text); cursor: pointer; text-align: left; }
.tk-dr__file button { border: 0; background: transparent; color: var(--color-danger); cursor: pointer; margin-left: auto; }
.tk-dr__footer { display: flex; justify-content: flex-end; gap: 8px; padding: var(--space-3) var(--space-5); border-top: 1px solid var(--glass-border-light); background: rgba(255,255,255,0.5); }
:root[data-theme="dark"] .tk-dr__footer { background: rgba(15,23,42,0.4); }
.tk-dr__btn { min-height: 38px; padding: 0 16px; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface); color: var(--color-text); font-weight: var(--fw-semibold); font-size: var(--text-sm); cursor: pointer; }
.tk-dr__btn--primary { background: var(--color-primary); border-color: var(--color-primary); color: var(--color-on-primary, #fff); }
.tk-dr__btn:disabled { opacity: 0.55; cursor: default; }
.tk-dr__chat { flex: 1 1 46%; min-width: 0; border-left: 1px solid var(--glass-border-light); display: flex; flex-direction: column; min-height: 0; }
.tk-dr--tabs .tk-dr__chat { flex-basis: 100%; border-left: 0; }

.tk-dr-modal { width: min(560px, 94vw); max-height: calc(100vh - 48px); display: flex; flex-direction: column; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); box-shadow: var(--shadow-xl); }
.tk-dr-modal__head { display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; border-bottom: 1px solid var(--color-border-subtle); }
.tk-dr-modal__head h3 { margin: 0; font-size: 16px; font-weight: 800; }
.tk-dr-modal__head button { border: 0; background: transparent; color: var(--color-text-muted); cursor: pointer; font-size: 15px; }
.tk-dr-modal__body { padding: 16px 18px; overflow: auto; display: flex; flex-direction: column; gap: 12px; }
.tk-dr-modal__foot { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 18px; border-top: 1px solid var(--color-border-subtle); }
.tk-dr__grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media (max-width: 640px) { .tk-dr__grid2 { grid-template-columns: 1fr; } }
</style>
