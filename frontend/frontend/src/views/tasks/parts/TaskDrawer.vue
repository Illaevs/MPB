<template>
  <transition name="task-drawer-slide">
    <div v-if="showCreateModal" class="task-drawer-overlay" @click.self="closeModal">
      <aside
        class="task-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="task-drawer-title"
        :class="{
          'task-drawer--tabs': layoutMode !== 'split',
          'task-drawer--mobile': layoutMode === 'mobile',
          'task-drawer--tab-chat': layoutMode !== 'split' && activeTab === 'chat'
        }"
        :style="drawerStyle"
        @click.stop
      >
        <!-- HEADER ============================================ -->
        <header class="task-drawer__header">
          <button
            type="button"
            class="task-drawer__icon-btn"
            title="Закрыть (Esc)"
            @click="closeModal"
          >
            <i class="fas fa-arrow-left"></i>
          </button>
          <div class="task-drawer__crumbs">
            <span v-if="currentTaskCode" class="task-drawer__code">{{ currentTaskCode }}</span>
            <span v-if="currentTaskCode" class="task-drawer__crumbs-sep">·</span>
            <PropertyChip
              label="Проект"
              :value="projectChipLabel"
              icon="far fa-folder-open"
              :placeholder="'+ Проект'"
            >
              <template #popover="{ close }">
                <div class="task-drawer__project-popover">
                  <div class="task-drawer__project-popover-title">Проект</div>
                  <input
                    ref="projectSearchInput"
                    v-model="projectSearchQuery"
                    type="text"
                    class="task-drawer__project-search"
                    placeholder="Поиск по проекту…"
                    @keydown.esc.stop="close"
                  />
                  <div class="task-drawer__project-list">
                    <button
                      v-for="project in filteredProjects"
                      :key="project.id"
                      type="button"
                      class="task-drawer__project-option"
                      :class="{ 'is-active': String(taskForm.deal_id) === String(project.id) }"
                      @click="setProject(project.id); close()"
                    >
                      <i class="far fa-folder-open"></i>
                      <span>{{ project.title }}</span>
                      <i
                        v-if="String(taskForm.deal_id) === String(project.id)"
                        class="fas fa-check task-drawer__project-tick"
                      ></i>
                    </button>
                    <div v-if="!filteredProjects.length" class="task-drawer__project-empty">
                      Ничего не нашли
                    </div>
                  </div>
                </div>
              </template>
            </PropertyChip>
          </div>

          <!-- Tabs (only on tablet/mobile) -->
          <nav v-if="layoutMode !== 'split'" class="task-drawer__tabs" role="tablist">
            <button
              type="button"
              role="tab"
              class="task-drawer__tab"
              :class="{ 'is-active': activeTab === 'task' }"
              :aria-selected="activeTab === 'task'"
              @click="activeTab = 'task'"
            >
              <i class="far fa-clipboard"></i>
              <span>Задача</span>
            </button>
            <button
              type="button"
              role="tab"
              class="task-drawer__tab"
              :class="{ 'is-active': activeTab === 'chat' }"
              :aria-selected="activeTab === 'chat'"
              :disabled="!isEditing"
              :title="!isEditing ? 'Чат станет доступен после сохранения' : ''"
              @click="activeTab = 'chat'"
            >
              <i class="far fa-comment-dots"></i>
              <span>Чат</span>
              <span v-if="chatUnreadCount" class="task-drawer__tab-badge">{{ chatUnreadCount }}</span>
            </button>
          </nav>

          <div class="task-drawer__header-actions">
            <span
              v-if="isEditing"
              class="task-drawer__autosave"
              aria-live="polite"
            >
              <span v-if="autoSaving" class="task-drawer__autosave-state">
                <i class="fas fa-spinner fa-spin"></i> Сохранение…
              </span>
              <span
                v-else-if="autoSavedLabel"
                class="task-drawer__autosave-state task-drawer__autosave-state--ok"
              >
                <i class="fas fa-check"></i> {{ autoSavedLabel }}
              </span>
            </span>
            <button
              type="button"
              class="task-drawer__icon-btn"
              title="Закрыть (Esc)"
              aria-label="Закрыть"
              @click="closeModal"
            >
              <i class="fas fa-times"></i>
            </button>
          </div>
        </header>

        <!-- BODY ============================================== -->
        <div class="task-drawer__body">
          <!-- LEFT: TASK -->
          <section
            v-show="layoutMode === 'split' || activeTab === 'task'"
            class="task-drawer__main"
            :style="layoutMode === 'split' ? { flexBasis: taskColumnBasis } : null"
            aria-label="Содержимое задачи"
            @dragenter.prevent="onMainDragEnter"
            @dragover.prevent="onMainDragOver"
            @dragleave.prevent="onMainDragLeave"
            @drop.prevent="onMainDrop"
          >
            <div class="task-drawer__scroll">
              <!-- Title -->
              <input
                id="task-drawer-title"
                ref="titleInput"
                v-model="taskForm.title"
                type="text"
                class="task-drawer__title-input"
                :class="{ 'is-invalid': taskValidation.title }"
                placeholder="Без названия"
                @input="triggerAutoDraftIfNeeded"
                @blur="validateTaskForm"
              />
              <div v-if="taskValidation.title" class="task-drawer__field-error">
                <i class="fas fa-circle-exclamation mr-1"></i>{{ taskValidation.title }}
              </div>

              <!-- Property chips: status / priority / dates -->
              <TaskPropertyChips :state="state" />

              <!-- People: reporter / assignees / watchers -->
              <TaskPeopleRows :state="state" />

              <!-- Description -->
              <div class="task-drawer__field">
                <label class="task-drawer__field-label" for="task-drawer-description">Описание</label>
                <textarea
                  id="task-drawer-description"
                  ref="descriptionInput"
                  v-model="taskForm.description"
                  class="task-drawer__description"
                  placeholder="Опишите этапы и ожидаемый результат. Поддерживаются переносы строк и ссылки."
                  rows="3"
                  @input="onDescriptionInput"
                ></textarea>
              </div>

              <!-- Approval (collapsible) -->
              <CollapsibleSection
                title="Согласование"
                icon="fas fa-route"
                :default-open="hasActiveApproval"
                :badge="hasActiveApproval ? '●' : null"
                badge-class="collapsible-section__badge--warning"
              >
                <ApprovalWidget
                  entity-type="task"
                  :entity-id="taskForm.id"
                  :entity-label="taskForm.title"
                  title="Согласование задачи"
                  empty-text="Сначала сохраните задачу, затем можно будет запустить маршрут согласования."
                  :allow-restart-after-approved="false"
                  @state-changed="handleTaskApprovalState"
                  @updated="refreshTasksAfterApproval"
                />
              </CollapsibleSection>

              <!-- Files (compact) -->
              <div class="task-drawer__field">
                <div class="task-drawer__files-head">
                  <span class="task-drawer__field-label">
                    <i class="fas fa-paperclip"></i>
                    Файлы
                    <span v-if="taskAttachmentsTotalCount" class="task-drawer__files-count">
                      {{ taskAttachmentsTotalCount }}
                    </span>
                  </span>
                  <button
                    type="button"
                    class="task-drawer__files-add"
                    title="Прикрепить файлы"
                    @click="openTaskAttachmentPicker"
                  >
                    <i class="fas fa-plus"></i>
                    <span>Прикрепить</span>
                  </button>
                  <input
                    :ref="setAttachmentInput"
                    type="file"
                    class="d-none"
                    multiple
                    @change="onTaskAttachmentPicked"
                  />
                </div>

                <div v-if="hasAnyFile" class="task-drawer__files-list">
                  <div
                    v-for="attachment in taskAttachmentItems"
                    :key="attachment.path || attachment.name"
                    class="task-drawer__file-item"
                  >
                    <button
                      type="button"
                      class="task-drawer__file-main"
                      :title="attachment.name || 'Файл'"
                      @click="downloadTaskAttachment(attachment)"
                    >
                      <i class="far fa-file task-drawer__file-icon"></i>
                      <span class="task-drawer__file-name">{{ attachment.name || 'Файл' }}</span>
                      <span class="task-drawer__file-size">
                        {{ formatTaskAttachmentSize(attachment.size) || '' }}
                      </span>
                    </button>
                    <button
                      type="button"
                      class="task-drawer__file-remove"
                      title="Удалить файл"
                      @click="removeTaskAttachment(attachment)"
                    >
                      <i class="fas fa-times"></i>
                    </button>
                  </div>
                  <div
                    v-for="(pending, idx) in taskPendingFiles"
                    :key="'pending-' + idx"
                    class="task-drawer__file-item task-drawer__file-item--pending"
                  >
                    <span class="task-drawer__file-main">
                      <i class="fas fa-cloud-arrow-up task-drawer__file-icon"></i>
                      <span class="task-drawer__file-name">{{ pending.name }}</span>
                      <span class="task-drawer__file-size">
                        {{ formatTaskAttachmentSize(pending.size) || '' }} · ожидает загрузки
                      </span>
                    </span>
                    <button
                      type="button"
                      class="task-drawer__file-remove"
                      title="Убрать из очереди"
                      @click="removePendingTaskFile(idx)"
                    >
                      <i class="fas fa-times"></i>
                    </button>
                  </div>
                </div>
                <div v-else class="task-drawer__files-empty">
                  Перетащите файлы сюда или нажмите «Прикрепить».
                </div>
              </div>
            </div>

            <!-- Drag overlay (only when dragging files over the column) -->
            <div
              v-if="taskAttachmentDragActive"
              class="task-drawer__drag-overlay"
              aria-hidden="true"
            >
              <i class="fas fa-cloud-arrow-up"></i>
              <span>Отпустите, чтобы прикрепить файл</span>
            </div>
          </section>

          <!-- RESIZER (split mode only) -->
          <div
            v-if="layoutMode === 'split'"
            class="task-drawer__resizer"
            role="separator"
            aria-orientation="vertical"
            aria-label="Изменить ширину панелей"
            @mousedown="onResizerDown"
            @touchstart.prevent="onResizerDown"
            @dblclick="resetSplit"
          >
            <span class="task-drawer__resizer-handle"></span>
          </div>

          <!-- RIGHT: CHAT -->
          <section
            v-show="layoutMode === 'split' || activeTab === 'chat'"
            class="task-drawer__chat-pane"
            aria-label="Чат задачи"
          >
            <div v-if="taskChatVisible" class="task-drawer__chat-inner">
              <TaskChat
                :task-id="taskForm.id"
                :users="users"
                :can-read="taskChatVisible"
                :can-write="taskChatVisible"
                @message-count="onChatMessageCount"
              />
            </div>
            <div v-else class="task-drawer__placeholder task-drawer__placeholder--chat">
              <i class="far fa-comments fa-2x"></i>
              <p v-if="!isEditing">Сначала сохраните задачу, и здесь появится чат.</p>
              <p v-else>Чат недоступен по текущим правам или задача не назначена текущему пользователю.</p>
            </div>
          </section>
        </div>

        <!-- FOOTER (only for new tasks, before the first save) ===== -->
        <footer v-if="!isEditing" class="task-drawer__footer">
          <div class="task-drawer__footer-left">
            <button type="button" class="btn btn-secondary" @click="closeModal">Отмена</button>
          </div>
          <div class="task-drawer__footer-right">
            <button
              type="button"
              class="btn btn-primary task-drawer__submit"
              :disabled="saving || taskFormHasErrors"
              @click="saveTask"
            >
              <i v-if="saving" class="fas fa-spinner fa-spin mr-1"></i>
              Создать
            </button>
          </div>
        </footer>
      </aside>
    </div>
  </transition>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import TaskPropertyChips from './TaskPropertyChips.vue'
import TaskPeopleRows from './TaskPeopleRows.vue'
import TaskChat from '../../../components/TaskChat.vue'
import CollapsibleSection from '../../../components/ui/CollapsibleSection.vue'
import ApprovalWidget from '../../../components/approvals/ApprovalWidget.vue'
import PropertyChip from '../../../components/ui/PropertyChip.vue'

const SPLIT_KEY = 'taskDrawer.splitBasis'
const SPLIT_DEFAULT = '58%'
const TABLET_BREAKPOINT = 1280
const MOBILE_BREAKPOINT = 900

export default {
  name: 'TaskDrawer',
  components: { TaskPropertyChips, TaskPeopleRows, TaskChat, CollapsibleSection, ApprovalWidget, PropertyChip },
  props: { state: { type: Object, required: true } },
  setup(props) {
    const s = props.state

    const titleInput = ref(null)
    const descriptionInput = ref(null)
    const activeTab = ref('task')
    const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1600)

    // Layout mode driven by viewport width.
    //  - 'split'  : two columns side by side (≥ 1280)
    //  - 'tabs'   : single column, tabs at top (900-1280)
    //  - 'mobile' : full-screen, tabs at top, swipe (< 900)
    const layoutMode = computed(() => {
      if (viewportWidth.value < MOBILE_BREAKPOINT) return 'mobile'
      if (viewportWidth.value < TABLET_BREAKPOINT) return 'tabs'
      return 'split'
    })

    // Resizer state — percentage of task column from total body width.
    const taskColumnBasis = ref(localStorage.getItem(SPLIT_KEY) || SPLIT_DEFAULT)
    let resizerStart = null

    function onResizerDown(ev) {
      const isTouch = ev.type === 'touchstart'
      const startX = isTouch ? ev.touches[0].clientX : ev.clientX
      const bodyEl = ev.currentTarget.parentElement
      const bodyRect = bodyEl.getBoundingClientRect()
      const startBasisPx = bodyEl.querySelector('.task-drawer__main').getBoundingClientRect().width
      resizerStart = { startX, bodyRect, startBasisPx }

      const moveEvt = isTouch ? 'touchmove' : 'mousemove'
      const upEvt = isTouch ? 'touchend' : 'mouseup'
      const onMove = (e) => {
        const x = isTouch ? e.touches[0].clientX : e.clientX
        const dx = x - resizerStart.startX
        const newPx = Math.max(360, Math.min(bodyRect.width - 360, startBasisPx + dx))
        const pct = (newPx / bodyRect.width) * 100
        taskColumnBasis.value = pct.toFixed(2) + '%'
      }
      const onUp = () => {
        window.removeEventListener(moveEvt, onMove)
        window.removeEventListener(upEvt, onUp)
        localStorage.setItem(SPLIT_KEY, taskColumnBasis.value)
        document.body.style.cursor = ''
        document.body.style.userSelect = ''
      }
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
      window.addEventListener(moveEvt, onMove, { passive: !isTouch })
      window.addEventListener(upEvt, onUp)
    }

    function resetSplit() {
      taskColumnBasis.value = SPLIT_DEFAULT
      localStorage.setItem(SPLIT_KEY, SPLIT_DEFAULT)
    }

    // Drawer width (only honored on desktop, full on mobile via CSS).
    const drawerStyle = computed(() => {
      if (layoutMode.value === 'mobile') return null
      return { width: 'min(1440px, calc(100vw - 80px))' }
    })

    // Project chip in the header — bound to the same `deal_id` the form uses.
    const projectChipLabel = computed(() => s.currentTaskProjectLabel?.value || '')
    const projectSearchQuery = ref('')
    const projectSearchInput = ref(null)
    const filteredProjects = computed(() => {
      const q = projectSearchQuery.value.trim().toLowerCase()
      const list = s.projects?.value || []
      if (!q) return list.slice(0, 60)
      return list
        .filter((p) => String(p.title || '').toLowerCase().includes(q))
        .slice(0, 60)
    })
    function setProject(dealId) {
      const tf = s.taskForm.value
      if (!tf) return
      tf.deal_id = dealId || ''
      // Drop the cached display label — it was joined server-side from the
      // previous deal and would otherwise keep showing the old project name
      // in the chip until the next reload. With an empty deal_title the
      // computed label falls back to a fresh lookup in `projects`.
      tf.deal_title = ''
      if (typeof s.triggerAutoDraftIfNeeded === 'function') s.triggerAutoDraftIfNeeded()
      if (typeof s.flushAutoSave === 'function') s.flushAutoSave()
      projectSearchQuery.value = ''
    }

    // Chat unread badge.
    // TaskChat emits 'message-count' on every list update (initial load + polling).
    // We snapshot what the user has "seen" and treat any growth above that as unread.
    // Snapshot resets when the user opens the chat tab, when split mode is active
    // (chat is always visible), or when the drawer closes.
    const chatMessageCount = ref(0)
    const chatSeenCount = ref(0)
    function onChatMessageCount(count) {
      const n = Number(count) || 0
      chatMessageCount.value = n
      // In split mode the chat is fully visible — keep seen in sync.
      if (layoutMode.value === 'split' || activeTab.value === 'chat') {
        chatSeenCount.value = n
      }
    }
    const chatUnreadCount = computed(() =>
      Math.max(0, chatMessageCount.value - chatSeenCount.value)
    )
    watch(activeTab, (tab) => {
      if (tab === 'chat') chatSeenCount.value = chatMessageCount.value
    })
    watch(layoutMode, (mode) => {
      if (mode === 'split') chatSeenCount.value = chatMessageCount.value
    })
    watch(
      () => s.showCreateModal.value,
      (open) => {
        if (!open) {
          chatMessageCount.value = 0
          chatSeenCount.value = 0
        }
      }
    )

    // Bind hidden <input type="file"> back to composable's ref so its
    // openTaskAttachmentPicker() / reset code can click()/clear() the same element.
    const setAttachmentInput = (el) => {
      if (s.taskAttachmentInput) s.taskAttachmentInput.value = el
    }

    const hasAnyFile = computed(() => {
      const items = s.taskAttachmentItems?.value || []
      const pending = s.taskPendingFiles?.value || []
      return items.length > 0 || pending.length > 0
    })

    // Autosave indicator: tick a clock so "5 секунд назад" stays fresh.
    const nowTick = ref(Date.now())
    let nowTickTimer = null
    onMounted(() => {
      nowTickTimer = setInterval(() => { nowTick.value = Date.now() }, 15000)
    })
    onBeforeUnmount(() => {
      if (nowTickTimer) clearInterval(nowTickTimer)
    })
    const autoSavedLabel = computed(() => {
      const ts = s.autoSavedAt?.value
      if (!ts) return ''
      const diff = Math.max(0, Math.floor((nowTick.value - ts) / 1000))
      if (diff < 5) return 'Сохранено'
      if (diff < 60) return `Сохранено ${diff} c назад`
      const m = Math.floor(diff / 60)
      if (m < 60) return `Сохранено ${m} мин назад`
      const h = Math.floor(m / 60)
      return `Сохранено ${h} ч назад`
    })

    // Approval state — used to auto-open the "Согласование" section when active.
    const hasActiveApproval = computed(() => {
      const a = s.taskApprovalState
      const raw = a && 'value' in a ? a.value : a
      return !!(raw && raw.activeInstance)
    })

    // Drag-and-drop: only the task column is a drop target. We forward to
    // composable handlers so the existing upload pipeline runs unchanged.
    function onMainDragEnter(ev) { s.onTaskAttachmentDragOver(ev) }
    function onMainDragOver(ev) { s.onTaskAttachmentDragOver(ev) }
    function onMainDragLeave(ev) { s.onTaskAttachmentDragLeave(ev) }
    function onMainDrop(ev) { s.onTaskAttachmentDrop(ev) }

    // Auto-grow the description textarea up to a comfortable cap.
    function autosizeDescription() {
      const el = descriptionInput.value
      if (!el) return
      el.style.height = 'auto'
      el.style.height = Math.min(el.scrollHeight, 480) + 'px'
    }
    function onDescriptionInput() {
      s.triggerAutoDraftIfNeeded()
      autosizeDescription()
    }

    // Re-autosize after open (existing description may be long).
    watch(
      () => s.showCreateModal.value,
      (open) => {
        if (open) nextTick(autosizeDescription)
      }
    )
    watch(
      () => s.taskForm.value && s.taskForm.value.description,
      () => nextTick(autosizeDescription)
    )

    // When opening the drawer, focus the title input on next tick (for creates).
    watch(
      () => s.showCreateModal.value,
      (open) => {
        if (open && !s.isEditing.value) {
          // Focus title only on creates so existing tasks don't steal focus.
          setTimeout(() => titleInput.value?.focus(), 50)
        }
      },
      { immediate: true }
    )

    // Hotkeys: Esc, Ctrl/Cmd+S, J/K (prev/next task), E (title focus),
    // M (chat composer focus). "/" (chat search) lands in etap 8.
    function isTypingInField() {
      const el = document.activeElement
      if (!el) return false
      const tag = el.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true
      if (el.isContentEditable) return true
      return false
    }
    function navigateTaskBy(delta) {
      const list = s.sortedTasks?.value || []
      if (!list.length) return
      const currentId = s.taskForm.value?.id
      const idx = list.findIndex((t) => String(t.id) === String(currentId))
      if (idx < 0) return
      const nextIdx = Math.max(0, Math.min(list.length - 1, idx + delta))
      if (nextIdx === idx) return
      if (typeof s.editTask === 'function') s.editTask(list[nextIdx])
    }
    function focusChatComposer() {
      const el = document.querySelector('.task-chat__input')
      if (el) {
        if (layoutMode.value !== 'split') activeTab.value = 'chat'
        nextTick(() => el.focus())
      }
    }
    function onKeydown(ev) {
      if (!s.showCreateModal.value) return
      // Always-honored keys (even while typing).
      if (ev.key === 'Escape') {
        ev.preventDefault()
        s.closeModal()
        return
      }
      if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === 's') {
        ev.preventDefault()
        if (!s.saving.value && !s.taskFormHasErrors.value) s.saveTask()
        return
      }
      // Single-letter shortcuts: skip when typing.
      if (ev.ctrlKey || ev.metaKey || ev.altKey) return
      if (isTypingInField()) return
      const k = ev.key.toLowerCase()
      if (k === 'j') {
        ev.preventDefault()
        navigateTaskBy(1)
      } else if (k === 'k') {
        ev.preventDefault()
        navigateTaskBy(-1)
      } else if (k === 'e') {
        ev.preventDefault()
        if (layoutMode.value !== 'split') activeTab.value = 'task'
        nextTick(() => titleInput.value?.focus())
      } else if (k === 'm') {
        ev.preventDefault()
        focusChatComposer()
      } else if (ev.key === '/') {
        ev.preventDefault()
        const btn = document.querySelector('.task-chat__icon-btn[title^="Поиск"]')
        if (btn) btn.click()
        nextTick(() => document.querySelector('.task-chat__search-input')?.focus())
      }
    }

    function onResize() {
      viewportWidth.value = window.innerWidth
    }

    onMounted(() => {
      window.addEventListener('keydown', onKeydown)
      window.addEventListener('resize', onResize)
    })
    onBeforeUnmount(() => {
      window.removeEventListener('keydown', onKeydown)
      window.removeEventListener('resize', onResize)
    })

    return {
      ...s,
      state: s,
      titleInput,
      descriptionInput,
      activeTab,
      layoutMode,
      taskColumnBasis,
      drawerStyle,
      projectChipLabel,
      projectSearchQuery,
      projectSearchInput,
      filteredProjects,
      setProject,
      chatUnreadCount,
      onChatMessageCount,
      onResizerDown,
      resetSplit,
      setAttachmentInput,
      hasAnyFile,
      hasActiveApproval,
      autoSavedLabel,
      onMainDragEnter,
      onMainDragOver,
      onMainDragLeave,
      onMainDrop,
      onDescriptionInput
    }
  }
}
</script>

<style scoped>
/* ============================================================
   TASK DRAWER — wide side panel with two columns (task | chat)
   Uses design tokens from main.css.
   ============================================================ */

.task-drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.18);
  display: flex;
  justify-content: flex-end;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.task-drawer {
  display: flex;
  flex-direction: column;
  height: 100%;
  /* Subtle glassmorphism — sits over the dimmed app background so the
     drawer feels layered, not flat. Falls back to solid surface for
     browsers without backdrop-filter. */
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border-left: 1px solid var(--glass-border-light);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
}
@supports not (backdrop-filter: blur(1px)) {
  .task-drawer { background: var(--color-surface); }
}

/* Slide-in transition (right → 0) */
.task-drawer-slide-enter-active,
.task-drawer-slide-leave-active {
  transition: opacity var(--dur-base) var(--ease-out);
}
.task-drawer-slide-enter-active .task-drawer,
.task-drawer-slide-leave-active .task-drawer {
  transition: transform var(--dur-slow) var(--ease-out);
}
.task-drawer-slide-enter-from .task-drawer,
.task-drawer-slide-leave-to .task-drawer {
  transform: translateX(100%);
}
.task-drawer-slide-enter-from,
.task-drawer-slide-leave-to {
  opacity: 0;
}

/* ----- HEADER ------------------------------------------------ */
.task-drawer__header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--glass-border-light);
  /* Translucent so the glass surface under it remains visible */
  background: rgba(255, 255, 255, 0.55);
  position: sticky;
  top: 0;
  z-index: 2;
  flex-shrink: 0;
}

.task-drawer__icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background: transparent;
  border: 0;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}
.task-drawer__icon-btn:hover {
  background: var(--color-surface-2);
  color: var(--color-text);
}
.task-drawer__icon-btn:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

.task-drawer__crumbs {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  flex: 0 1 auto;
  min-width: 0;
  white-space: nowrap;
}
.task-drawer__code {
  font-family: var(--font-mono);
  font-weight: var(--fw-medium);
  color: var(--color-text);
}
.task-drawer__crumbs-sep { opacity: 0.5; }
.task-drawer__project { display: inline-flex; align-items: center; gap: 4px; }

.task-drawer__tabs {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  margin-left: auto;
}
.task-drawer__tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px var(--space-3);
  border-radius: var(--radius-pill);
  background: transparent;
  border: 0;
  font-size: var(--text-base);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}
.task-drawer__tab:hover { background: var(--color-surface-2); color: var(--color-text); }
.task-drawer__tab.is-active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}
.task-drawer__tab:disabled { opacity: 0.5; cursor: not-allowed; }
.task-drawer__tab-badge {
  display: inline-flex;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  align-items: center;
  justify-content: center;
  background: var(--color-danger);
  color: var(--color-text-inverse);
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  border-radius: var(--radius-pill);
}

.task-drawer__header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  margin-left: auto;
}
/* When tabs are present, push actions to the right edge */
.task-drawer--tabs .task-drawer__header-actions { margin-left: var(--space-2); }

/* ----- BODY -------------------------------------------------- */
.task-drawer__body {
  flex: 1;
  display: flex;
  min-height: 0;
  overflow: hidden;
}

.task-drawer__main {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex-grow: 0;
  flex-shrink: 1;
  flex-basis: 58%;
  /* Transparent so the drawer's glass background shows through.
     Sub-elements (description, files, chips) get their own subtle
     translucent surfaces below. */
  background: transparent;
}
.task-drawer--tabs .task-drawer__main {
  flex-basis: 100% !important;
}

.task-drawer__scroll {
  overflow-y: auto;
  padding: var(--space-5) var(--space-6) var(--space-8);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.task-drawer__title-input {
  width: 100%;
  border: 0;
  background: transparent;
  font-size: var(--text-2xl);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
  padding: 0;
  line-height: var(--leading-tight);
  outline: none;
}
.task-drawer__title-input::placeholder {
  color: var(--color-text-subtle);
  font-weight: var(--fw-regular);
}
.task-drawer__title-input.is-invalid {
  box-shadow: 0 1px 0 0 var(--color-danger);
}

.task-drawer__field-error {
  font-size: var(--text-sm);
  color: var(--color-danger);
}

.task-drawer__placeholder {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-subtle);
  font-size: var(--text-md);
  background: var(--color-surface-2);
}
.task-drawer__placeholder--chat {
  flex-direction: column;
  text-align: center;
  margin: auto;
  padding: var(--space-8);
  max-width: 360px;
}
.task-drawer__placeholder-muted {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text-subtle);
}

/* ----- FIELDS (description / files) ------------------------- */
.task-drawer__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.task-drawer__field-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.task-drawer__description {
  width: 100%;
  min-height: 80px;
  max-height: 480px;
  resize: none;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid var(--glass-border-light);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  font-family: var(--font-main);
  font-size: var(--text-md);
  color: var(--color-text);
  line-height: var(--leading-normal);
  outline: none;
  transition: border-color var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out);
}
.task-drawer__description:hover { background: rgba(255, 255, 255, 0.72); }
.task-drawer__description:focus {
  background: rgba(255, 255, 255, 0.92);
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}
.task-drawer__description::placeholder {
  color: var(--color-text-subtle);
}

/* ----- FILES ------------------------------------------------ */
.task-drawer__files-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}
.task-drawer__files-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  background: var(--color-surface-3);
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  border-radius: var(--radius-pill);
  margin-left: 4px;
}
.task-drawer__files-add {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  background: transparent;
  border: 1px dashed var(--color-border-strong);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}
.task-drawer__files-add:hover {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  border-color: var(--color-primary);
  border-style: solid;
}
.task-drawer__files-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.task-drawer__file-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 6px var(--space-2);
  border-radius: var(--radius-sm);
  transition: background var(--dur-fast) var(--ease-out);
}
.task-drawer__file-item:hover { background: var(--color-surface-2); }
.task-drawer__file-item--pending { opacity: 0.8; }
.task-drawer__file-main {
  flex: 1;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
  background: transparent;
  border: 0;
  padding: 0;
  color: var(--color-text);
  cursor: pointer;
  text-align: left;
}
.task-drawer__file-icon { color: var(--color-text-muted); }
.task-drawer__file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--text-md);
}
.task-drawer__file-size {
  font-size: var(--text-xs);
  color: var(--color-text-subtle);
  white-space: nowrap;
}
.task-drawer__file-remove {
  background: transparent;
  border: 0;
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  color: var(--color-text-subtle);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.task-drawer__file-remove:hover { color: var(--color-danger); background: var(--color-danger-soft); }

.task-drawer__files-empty {
  padding: var(--space-3);
  border: 1px dashed var(--glass-border-light);
  border-radius: var(--radius-md);
  color: var(--color-text-subtle);
  font-size: var(--text-sm);
  text-align: center;
  background: rgba(255, 255, 255, 0.35);
}

/* ----- DRAG OVERLAY ----------------------------------------- */
.task-drawer__main { position: relative; }
.task-drawer__drag-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  background: rgba(37, 99, 235, 0.08);
  border: 2px dashed var(--color-primary);
  border-radius: var(--radius-md);
  margin: var(--space-3);
  color: var(--color-primary);
  font-size: var(--text-lg);
  font-weight: var(--fw-medium);
  pointer-events: none;
  z-index: 1;
}
.task-drawer__drag-overlay i { font-size: 32px; }

/* ----- RESIZER ----------------------------------------------- */
.task-drawer__resizer {
  width: 6px;
  position: relative;
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  flex-shrink: 0;
  border-left: 1px solid var(--color-border-subtle);
  border-right: 1px solid var(--color-border-subtle);
  transition: background var(--dur-fast) var(--ease-out);
}
.task-drawer__resizer:hover { background: var(--color-surface-2); }
.task-drawer__resizer-handle {
  width: 2px;
  height: 32px;
  background: var(--color-border-strong);
  border-radius: var(--radius-pill);
}
.task-drawer__resizer:hover .task-drawer__resizer-handle {
  background: var(--color-primary);
}

/* ----- CHAT PANE --------------------------------------------- */
.task-drawer__chat-pane {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  /* Slight tint so the chat pane reads as a sibling surface but still
     lets the glass background bleed through. */
  background: rgba(248, 250, 252, 0.55);
  border-left: 1px solid var(--glass-border-light);
  overflow: hidden;
}
.task-drawer--tabs .task-drawer__chat-pane {
  border-left: 0;
}
.task-drawer__chat-inner {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}
/* Let TaskChat fill the chat pane. The chat component expects a flex parent
   with min-height: 0. */
.task-drawer__chat-inner > :deep(.task-chat) {
  flex: 1;
  min-height: 0;
}

/* ----- FOOTER ------------------------------------------------ */
.task-drawer__footer {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--glass-border-light);
  background: rgba(255, 255, 255, 0.55);
  flex-shrink: 0;
}
.task-drawer__footer-left,
.task-drawer__footer-right {
  display: flex;
  gap: var(--space-2);
}
.task-drawer__footer-right { margin-left: auto; }

.task-drawer__autosave {
  display: inline-flex;
  align-items: center;
  margin-right: var(--space-2);
  color: var(--color-text-subtle);
  font-size: var(--text-sm);
}
.task-drawer__autosave-state {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.task-drawer__autosave-state--ok {
  color: var(--color-success);
}

.task-drawer__project-popover {
  min-width: 280px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.task-drawer__project-popover-title {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-subtle);
  padding: var(--space-1) var(--space-2);
}
.task-drawer__project-search {
  margin: 4px 8px 6px;
  padding: 6px 10px;
  font-size: var(--text-md);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  outline: none;
}
.task-drawer__project-search:focus {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}
.task-drawer__project-list {
  max-height: 320px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.task-drawer__project-option {
  display: grid;
  grid-template-columns: 18px minmax(0, 1fr) 16px;
  align-items: center;
  gap: var(--space-2);
  padding: 8px 10px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  cursor: pointer;
  text-align: left;
  font-size: var(--text-md);
  color: var(--color-text);
  transition: background var(--dur-fast) var(--ease-out);
}
.task-drawer__project-option > span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.task-drawer__project-option:hover { background: var(--color-surface-2); }
.task-drawer__project-option.is-active { background: var(--color-primary-soft); }
.task-drawer__project-option > i:first-child { color: var(--color-text-muted); }
.task-drawer__project-tick { color: var(--color-primary); font-size: var(--text-sm); }
.task-drawer__project-empty {
  padding: var(--space-3);
  text-align: center;
  color: var(--color-text-subtle);
  font-size: var(--text-sm);
}
.task-drawer__footer-hints {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-subtle);
  font-size: var(--text-sm);
}
.task-drawer__footer-hints kbd {
  display: inline-flex;
  align-items: center;
  padding: 1px 6px;
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xs);
  line-height: var(--leading-tight);
}
.task-drawer__hint-sep { opacity: 0.5; }

.task-drawer__submit {
  min-width: 120px;
}

/* ----- MOBILE ------------------------------------------------ */
.task-drawer--mobile {
  width: 100% !important;
  border-left: 0;
}
.task-drawer--mobile .task-drawer__footer-hints {
  display: none;
}

@media (max-width: 720px) {
  .task-drawer__crumbs { display: none; }
  .task-drawer__scroll { padding: var(--space-4); }
}

/* ----- DARK MODE — mirror the glass surfaces over slate-900 ---- */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) .task-drawer-overlay { background: rgba(2, 6, 23, 0.55); }
  :root:not([data-theme="light"]) .task-drawer {
    background: rgba(15, 23, 42, 0.7);
    border-left-color: var(--glass-border-dark);
  }
  :root:not([data-theme="light"]) .task-drawer__header,
  :root:not([data-theme="light"]) .task-drawer__footer {
    background: rgba(15, 23, 42, 0.55);
    border-color: var(--glass-border-dark);
  }
  :root:not([data-theme="light"]) .task-drawer__chat-pane {
    background: rgba(2, 6, 23, 0.42);
    border-left-color: var(--glass-border-dark);
  }
  :root:not([data-theme="light"]) .task-drawer__description {
    background: rgba(15, 23, 42, 0.45);
    border-color: var(--glass-border-dark);
  }
  :root:not([data-theme="light"]) .task-drawer__description:hover { background: rgba(15, 23, 42, 0.6); }
  :root:not([data-theme="light"]) .task-drawer__description:focus { background: rgba(15, 23, 42, 0.8); }
  :root:not([data-theme="light"]) .task-drawer__files-empty {
    background: rgba(15, 23, 42, 0.32);
    border-color: var(--glass-border-dark);
  }
}
:root[data-theme="dark"] .task-drawer-overlay { background: rgba(2, 6, 23, 0.55); }
:root[data-theme="dark"] .task-drawer {
  background: rgba(15, 23, 42, 0.7);
  border-left-color: var(--glass-border-dark);
}
:root[data-theme="dark"] .task-drawer__header,
:root[data-theme="dark"] .task-drawer__footer {
  background: rgba(15, 23, 42, 0.55);
  border-color: var(--glass-border-dark);
}
:root[data-theme="dark"] .task-drawer__chat-pane {
  background: rgba(2, 6, 23, 0.42);
  border-left-color: var(--glass-border-dark);
}
:root[data-theme="dark"] .task-drawer__description {
  background: rgba(15, 23, 42, 0.45);
  border-color: var(--glass-border-dark);
}
:root[data-theme="dark"] .task-drawer__description:hover { background: rgba(15, 23, 42, 0.6); }
:root[data-theme="dark"] .task-drawer__description:focus { background: rgba(15, 23, 42, 0.8); }
:root[data-theme="dark"] .task-drawer__files-empty {
  background: rgba(15, 23, 42, 0.32);
  border-color: var(--glass-border-dark);
}
</style>
