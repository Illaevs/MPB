<template>
  <div class="lead-timeline">
    <!-- Composer: comment / task / file -->
    <div class="composer card p-2">
      <div class="composer-tabs">
        <button
          v-for="mode in COMPOSER_MODES"
          :key="mode.value"
          type="button"
          class="composer-tab"
          :class="{ active: composer.mode === mode.value }"
          @click="composer.mode = mode.value"
        >
          <i :class="mode.icon"></i>
          <span>{{ mode.label }}</span>
        </button>
      </div>

      <!-- Comment -->
      <div v-if="composer.mode === 'comment'" class="composer-body">
        <textarea
          v-model="composer.commentText"
          class="form-control"
          rows="2"
          placeholder="Напишите комментарий..."
          @keydown.ctrl.enter.prevent="submitComment"
          @keydown.meta.enter.prevent="submitComment"
        ></textarea>
        <div class="composer-actions">
          <small class="text-muted">Ctrl+Enter — отправить</small>
          <button
            type="button"
            class="btn btn-sm btn-primary"
            :disabled="!composer.commentText.trim() || composer.busy"
            @click="submitComment"
          >
            <i v-if="composer.busy" class="fas fa-spinner fa-spin mr-1"></i>
            <i v-else class="fas fa-paper-plane mr-1"></i>
            Отправить
          </button>
        </div>
      </div>

      <!-- Task -->
      <div v-else-if="composer.mode === 'task'" class="composer-body">
        <input
          v-model="composer.taskTitle"
          type="text"
          class="form-control"
          placeholder="Название задачи..."
          @keydown.enter.prevent="submitTask"
        />
        <div class="composer-row">
          <select v-model="composer.taskPriority" class="form-control form-control-sm">
            <option value="low">Низкий</option>
            <option value="normal">Нормальный</option>
            <option value="high">Высокий</option>
            <option value="urgent">Срочный</option>
          </select>
          <input v-model="composer.taskDueDate" type="date" class="form-control form-control-sm" />
          <select v-model="composer.taskAssignee" class="form-control form-control-sm">
            <option value="">Без исполнителя</option>
            <option v-for="u in users" :key="u.id" :value="u.id">{{ u.full_name || u.email }}</option>
          </select>
        </div>
        <div class="composer-actions">
          <small class="text-muted">Задача будет привязана к этому лиду</small>
          <button
            type="button"
            class="btn btn-sm btn-primary"
            :disabled="!composer.taskTitle.trim() || composer.busy"
            @click="submitTask"
          >
            <i v-if="composer.busy" class="fas fa-spinner fa-spin mr-1"></i>
            <i v-else class="fas fa-plus mr-1"></i>
            Создать задачу
          </button>
        </div>
      </div>

      <!-- File -->
      <div v-else-if="composer.mode === 'file'" class="composer-body">
        <div
          class="file-drop"
          :class="{ active: composer.fileDragging }"
          @dragover.prevent="composer.fileDragging = true"
          @dragleave="composer.fileDragging = false"
          @drop.prevent="onFileDrop"
        >
          <input ref="fileInputRef" type="file" multiple class="d-none" @change="onFilePicked" />
          <i class="fas fa-cloud-upload-alt"></i>
          <p>Перетащите файлы сюда или
            <button type="button" class="link-btn" @click="fileInputRef?.click()">выберите вручную</button>
          </p>
          <p v-if="composer.fileQueue.length" class="text-muted small">
            В очереди: {{ composer.fileQueue.length }}
          </p>
        </div>
        <div v-if="composer.fileQueue.length" class="file-queue">
          <div v-for="(f, idx) in composer.fileQueue" :key="idx" class="file-queue__item">
            <i class="fas fa-paperclip"></i>
            <span class="file-queue__name">{{ f.name }}</span>
            <span class="text-muted small">{{ formatBytes(f.size) }}</span>
            <button type="button" class="icon-btn icon-btn--danger" @click="removeQueuedFile(idx)">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
        <div class="composer-actions">
          <input v-model="composer.fileCaption" type="text" class="form-control form-control-sm" placeholder="Описание (необязательно)" />
          <button
            type="button"
            class="btn btn-sm btn-primary"
            :disabled="!composer.fileQueue.length || composer.busy"
            @click="submitFiles"
          >
            <i v-if="composer.busy" class="fas fa-spinner fa-spin mr-1"></i>
            <i v-else class="fas fa-upload mr-1"></i>
            Загрузить ({{ composer.fileQueue.length }})
          </button>
        </div>
      </div>
    </div>

    <!-- Filter chips -->
    <div class="timeline-filters">
      <button
        v-for="f in FILTER_OPTIONS"
        :key="f.value"
        type="button"
        class="timeline-filter"
        :class="{ active: !filterTypes.length && f.value === '' || filterTypes.includes(f.value) }"
        @click="toggleFilter(f.value)"
      >
        <i :class="f.icon"></i>
        <span>{{ f.label }}</span>
      </button>
    </div>

    <!-- Feed -->
    <div v-if="loading" class="p-2 d-flex flex-column gap-2">
      <SkeletonLoader v-for="i in 4" :key="i" height="62px" />
    </div>

    <div v-else-if="!filtered.length" class="empty-state">
      <i class="fas fa-stream"></i>
      <p>Лента пуста</p>
      <small class="text-muted">Напишите первый комментарий или прикрепите файл</small>
    </div>

    <div v-else class="feed">
      <div v-for="(group, gi) in groupedByDay" :key="`g-${gi}`" class="feed-group">
        <div class="feed-day">{{ group.label }}</div>
        <div
          v-for="item in group.items"
          :key="item.id"
          class="feed-item"
          :class="`feed-item--${item.activity_type}`"
        >
          <span class="feed-rail">
            <span class="feed-dot" :class="`dot-${item.activity_type}`">
              <i :class="iconFor(item.activity_type)"></i>
            </span>
          </span>
          <div class="feed-body">
            <div class="feed-head">
              <span class="user-avatar sm" :class="`avatar-${avatarColor(item.actor?.full_name || item.actor?.email)}`">
                <img v-if="item.actor?.avatar_url" :src="resolveAvatar(item.actor.avatar_url, item.actor.id)" alt="" />
                <span v-else>{{ initials(item.actor?.full_name || item.actor?.email) }}</span>
              </span>
              <strong class="feed-author">{{ item.actor?.full_name || item.actor?.email || 'Система' }}</strong>
              <span class="text-muted small">· {{ formatTime(item.created_at) }}</span>
              <button
                v-if="canDelete(item)"
                type="button"
                class="icon-btn icon-btn--danger feed-item__delete"
                @click="onDeleteActivity(item)"
                title="Удалить"
              >
                <i class="fas fa-times"></i>
              </button>
            </div>

            <!-- Type-specific body -->
            <div v-if="item.activity_type === 'comment'" class="feed-content">{{ item.content }}</div>

            <div v-else-if="item.activity_type === 'status_change'" class="feed-content feed-content--status">
              <span class="status-pill" :class="`status-${item.payload?.from || 'default'}`">{{ statusLabel(item.payload?.from) }}</span>
              <i class="fas fa-arrow-right text-muted"></i>
              <span class="status-pill" :class="`status-${item.payload?.to || 'default'}`">{{ statusLabel(item.payload?.to) }}</span>
            </div>

            <div v-else-if="item.activity_type === 'task_link'" class="feed-content">
              <div class="feed-task" v-if="item.payload?.task">
                <i class="fas fa-tasks"></i>
                <router-link :to="`/tasks?task_id=${item.payload.task.id}`" class="feed-task__title">
                  {{ item.payload.task.title }}
                </router-link>
                <span v-if="item.payload.task.status" class="feed-task__status" :class="`task-status-${item.payload.task.status}`">
                  {{ taskStatusLabel(item.payload.task.status) }}
                </span>
                <span v-if="item.payload.task.due_date" class="text-muted small">срок {{ formatDate(item.payload.task.due_date) }}</span>
              </div>
              <div v-else>{{ item.content }}</div>
            </div>

            <div v-else-if="item.activity_type === 'file'" class="feed-content">
              <div class="feed-file">
                <i :class="fileIcon(item.payload?.file_name)"></i>
                <button type="button" class="link-btn feed-file__name" @click="downloadFile(item)">
                  {{ item.payload?.file_name || 'Файл' }}
                </button>
                <span class="text-muted small">{{ formatBytes(item.payload?.file_size || 0) }}</span>
              </div>
              <div v-if="item.content && item.content !== item.payload?.file_name" class="feed-file-caption text-muted small">
                {{ item.content }}
              </div>
            </div>

            <div v-else-if="item.activity_type === 'convert'" class="feed-content">
              <i class="fas fa-arrow-right-arrow-left mr-1"></i>{{ item.content }}
              <router-link v-if="item.payload?.deal_id" :to="`/deals?deal_id=${item.payload.deal_id}`" class="ml-2">
                открыть сделку
              </router-link>
            </div>

            <div v-else class="feed-content text-muted small">{{ item.content }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, reactive } from 'vue'
import { api } from '@/services/api'
import SkeletonLoader from '../ui/SkeletonLoader.vue'
import { useToast } from '../../composables/useToast'
import { useConfirm } from '../../composables/useConfirm'
import { normalizeAvatarUrl } from '../../utils/avatar'
import { downloadFromApi } from '../../utils/download'

const COMPOSER_MODES = [
  { value: 'comment', label: 'Комментарий', icon: 'fas fa-comment' },
  { value: 'task',    label: 'Задача',      icon: 'fas fa-tasks' },
  { value: 'file',    label: 'Файл',        icon: 'fas fa-paperclip' },
]

const FILTER_OPTIONS = [
  { value: '',              label: 'Все',           icon: 'fas fa-stream' },
  { value: 'comment',       label: 'Комментарии',   icon: 'fas fa-comment' },
  { value: 'task_link',     label: 'Задачи',        icon: 'fas fa-tasks' },
  { value: 'file',          label: 'Файлы',         icon: 'fas fa-paperclip' },
  { value: 'status_change', label: 'Статусы',       icon: 'fas fa-flag' },
]

const STATUS_LABELS = {
  incoming: 'Входящие',
  no_work: 'В простое',
  proposal: 'Подготовка КП',
  waiting: 'Ожидание',
  customer_reject_internal: 'Откл. (внутр.)',
  customer_reject_our: 'Откл. (наши)',
  we_reject: 'Откл. нами',
  converted: 'Конверсия',
}

const TASK_STATUS_LABELS = {
  new: 'Новая',
  in_progress: 'В работе',
  pending: 'Ожидает',
  completed: 'Завершена',
  cancelled: 'Отменена',
  deferred: 'Отложена',
}

export default {
  name: 'LeadTimeline',
  components: { SkeletonLoader },
  props: {
    leadId: { type: String, required: true },
    users: { type: Array, default: () => [] },
    currentUserId: { type: String, default: '' },
  },
  emits: ['lead-updated'],
  setup(props, { emit }) {
    const toast = useToast()
    const { confirm } = useConfirm()

    const items = ref([])
    const loading = ref(false)
    const filterTypes = ref([])
    const fileInputRef = ref(null)

    const composer = reactive({
      mode: 'comment',
      busy: false,
      commentText: '',
      taskTitle: '',
      taskPriority: 'normal',
      taskDueDate: '',
      taskAssignee: '',
      fileQueue: [],
      fileCaption: '',
      fileDragging: false,
    })

    const load = async () => {
      loading.value = true
      try {
        const params = {}
        if (filterTypes.value.length) params.types = filterTypes.value.join(',')
        const data = await api.leads.timeline(props.leadId, params)
        items.value = Array.isArray(data) ? data : []
      } catch (e) {
        console.error('Timeline load error:', e)
        toast.error('Не удалось загрузить ленту')
      } finally {
        loading.value = false
      }
    }

    const toggleFilter = (value) => {
      if (value === '') { filterTypes.value = []; load(); return }
      const i = filterTypes.value.indexOf(value)
      if (i >= 0) filterTypes.value.splice(i, 1)
      else filterTypes.value.push(value)
      load()
    }

    const filtered = computed(() => items.value)

    // Group by day
    const groupedByDay = computed(() => {
      const groups = []
      const map = new Map()
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const yesterday = new Date(today.getTime() - 86400000)

      filtered.value.forEach((item) => {
        const d = new Date(item.created_at)
        const day = new Date(d.getFullYear(), d.getMonth(), d.getDate())
        const key = day.getTime()
        if (!map.has(key)) {
          let label
          if (key === today.getTime()) label = 'Сегодня'
          else if (key === yesterday.getTime()) label = 'Вчера'
          else label = d.toLocaleDateString('ru-RU', { day: '2-digit', month: 'long', year: 'numeric' })
          const group = { key, label, items: [] }
          map.set(key, group)
          groups.push(group)
        }
        map.get(key).items.push(item)
      })
      return groups
    })

    const submitComment = async () => {
      const text = composer.commentText.trim()
      if (!text) return
      composer.busy = true
      try {
        const data = await api.leads.addComment(props.leadId, { content: text })
        items.value.unshift(data)
        composer.commentText = ''
        toast.success('Комментарий добавлен')
      } catch (e) {
        toast.error(e?.response?.data?.detail || 'Не удалось отправить комментарий')
      } finally { composer.busy = false }
    }

    const submitTask = async () => {
      const title = composer.taskTitle.trim()
      if (!title) return
      composer.busy = true
      try {
        const body = {
          title,
          priority: composer.taskPriority,
        }
        if (composer.taskDueDate) body.due_date = composer.taskDueDate
        if (composer.taskAssignee) body.assigned_to_user_id = composer.taskAssignee
        const data = await api.leads.addTask(props.leadId, body)
        items.value.unshift(data)
        composer.taskTitle = ''
        composer.taskDueDate = ''
        composer.taskAssignee = ''
        composer.taskPriority = 'normal'
        toast.success('Задача создана')
        emit('lead-updated')
      } catch (e) {
        toast.error(e?.response?.data?.detail || 'Не удалось создать задачу')
      } finally { composer.busy = false }
    }

    const onFilePicked = (event) => {
      const list = Array.from(event.target.files || [])
      composer.fileQueue.push(...list)
      if (event.target) event.target.value = ''
    }
    const onFileDrop = (event) => {
      composer.fileDragging = false
      const list = Array.from(event.dataTransfer?.files || [])
      composer.fileQueue.push(...list)
    }
    const removeQueuedFile = (idx) => composer.fileQueue.splice(idx, 1)

    const submitFiles = async () => {
      if (!composer.fileQueue.length) return
      composer.busy = true
      try {
        for (const file of composer.fileQueue) {
          const formData = new FormData()
          formData.append('file', file)
          if (composer.fileCaption) formData.append('caption', composer.fileCaption)
          const data = await api.leads.uploadFile(props.leadId, formData)
          items.value.unshift(data)
        }
        composer.fileQueue = []
        composer.fileCaption = ''
        toast.success('Файл(ы) загружен(ы)')
      } catch (e) {
        toast.error(e?.response?.data?.detail || 'Не удалось загрузить файл')
      } finally { composer.busy = false }
    }

    const downloadFile = async (item) => {
      const path = item?.payload?.file_path
      if (!path) return
      try {
        await downloadFromApi(`/api/v1/storage/download?path=${encodeURIComponent(path)}`, item.payload.file_name || 'file', {
          module: 'leads', entityId: props.leadId,
        })
      } catch (e) {
        toast.error('Не удалось скачать файл')
      }
    }

    const canDelete = (item) => {
      if (!['comment', 'file'].includes(item.activity_type)) return false
      if (!props.currentUserId) return true
      return item.actor?.id === props.currentUserId
    }

    const onDeleteActivity = async (item) => {
      const ok = await confirm({
        title: item.activity_type === 'file' ? 'Удалить файл?' : 'Удалить комментарий?',
        confirmText: 'Удалить',
        variant: 'danger',
      })
      if (!ok) return
      try {
        await api.leads.removeActivity(item.id)
        items.value = items.value.filter(x => x.id !== item.id)
        toast.success('Удалено')
      } catch (e) {
        toast.error(e?.response?.data?.detail || 'Не удалось удалить')
      }
    }

    // Helpers
    const iconFor = (type) => {
      const map = {
        comment: 'fas fa-comment',
        status_change: 'fas fa-flag',
        field_change: 'fas fa-pen',
        file: 'fas fa-paperclip',
        task_link: 'fas fa-tasks',
        convert: 'fas fa-arrow-right-arrow-left',
        created: 'fas fa-plus',
      }
      return map[type] || 'fas fa-circle-info'
    }
    const fileIcon = (name = '') => {
      const ext = String(name).split('.').pop()?.toLowerCase()
      if (ext === 'pdf') return 'fas fa-file-pdf'
      if (['doc', 'docx'].includes(ext)) return 'fas fa-file-word'
      if (['xls', 'xlsx', 'csv'].includes(ext)) return 'fas fa-file-excel'
      if (['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(ext)) return 'fas fa-file-image'
      if (['zip', 'rar', '7z'].includes(ext)) return 'fas fa-file-archive'
      return 'fas fa-file'
    }
    const statusLabel = (key) => STATUS_LABELS[key] || key || '—'
    const taskStatusLabel = (key) => TASK_STATUS_LABELS[key] || key || ''
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
      let h = 0
      for (let i = 0; i < name.length; i += 1) h = (h * 31 + name.charCodeAt(i)) | 0
      return palette[Math.abs(h) % palette.length]
    }
    const resolveAvatar = (url, userId) => normalizeAvatarUrl(url, userId)
    const formatTime = (v) => v ? new Date(v).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }) : ''
    const formatDate = (v) => v ? new Date(v).toLocaleDateString('ru-RU') : ''
    const formatBytes = (b) => {
      const v = Number(b || 0)
      if (!v) return ''
      if (v < 1024) return `${v} Б`
      if (v < 1024 * 1024) return `${(v / 1024).toFixed(1)} КБ`
      return `${(v / 1024 / 1024).toFixed(1)} МБ`
    }

    onMounted(load)

    return {
      items, loading, filterTypes, fileInputRef, composer,
      filtered, groupedByDay,
      COMPOSER_MODES, FILTER_OPTIONS,
      toggleFilter,
      submitComment, submitTask, submitFiles,
      onFilePicked, onFileDrop, removeQueuedFile, downloadFile,
      canDelete, onDeleteActivity,
      iconFor, fileIcon, statusLabel, taskStatusLabel,
      initials, avatarColor, resolveAvatar,
      formatTime, formatDate, formatBytes,
      load,
    }
  }
}
</script>

<style scoped>
.lead-timeline {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}

/* Composer */
.composer { padding: 8px 10px !important; }
.composer-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 8px;
}
.composer-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.85rem;
  font-weight: 500;
  transition: 0.12s ease;
}
.composer-tab:hover { background: rgba(0,0,0,0.04); color: var(--md-sys-color-on-surface); }
.composer-tab.active {
  background: var(--md-sys-color-primary-container, rgba(25,118,210,0.12));
  color: var(--md-sys-color-primary, #1976d2);
  font-weight: 600;
}
.composer-body { display: flex; flex-direction: column; gap: 8px; }
.composer-body textarea {
  width: 100%;
  resize: vertical;
  min-height: 48px;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 8px;
  padding: 8px 10px;
  font-family: inherit;
  font-size: 0.92rem;
}
.composer-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
}
.composer-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.file-drop {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 16px;
  border: 2px dashed var(--md-sys-color-outline-variant);
  border-radius: 10px;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
  text-align: center;
  transition: 0.12s ease;
}
.file-drop.active {
  background: var(--md-sys-color-primary-container, rgba(25,118,210,0.06));
  border-color: var(--md-sys-color-primary, #1976d2);
  color: var(--md-sys-color-primary, #1976d2);
}
.file-drop i { font-size: 1.5rem; }
.file-drop p { margin: 0; }
.link-btn {
  border: none; background: transparent; cursor: pointer;
  color: var(--md-sys-color-primary, #1976d2); padding: 0;
  text-decoration: underline; font-size: inherit;
}
.file-queue { display: flex; flex-direction: column; gap: 4px; }
.file-queue__item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 6px;
}
.file-queue__name { flex: 1; font-size: 0.88rem; }

/* Filter chips */
.timeline-filters {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  padding: 0 4px;
}
.timeline-filter {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 999px;
  background: var(--md-sys-color-surface, #fff);
  font-size: 0.78rem;
  cursor: pointer;
  color: var(--md-sys-color-on-surface);
}
.timeline-filter:hover { background: var(--md-sys-color-surface-variant, rgba(0,0,0,0.03)); }
.timeline-filter.active {
  background: var(--md-sys-color-primary, #1976d2);
  color: #fff;
  border-color: var(--md-sys-color-primary, #1976d2);
}

/* Feed */
.feed {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.feed-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.feed-day {
  font-size: 0.74rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--md-sys-color-on-surface-variant);
  font-weight: 600;
  padding: 4px 12px;
}
.feed-item {
  display: grid;
  grid-template-columns: 32px 1fr;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--md-sys-color-surface, #fff);
  border: 1px solid var(--md-sys-color-outline-variant);
}
.feed-rail {
  display: flex;
  justify-content: center;
  padding-top: 2px;
}
.feed-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.78rem;
  background: var(--md-sys-color-surface-variant, #e2e8f0);
  color: var(--md-sys-color-on-surface-variant, #475569);
  flex-shrink: 0;
}
.dot-comment       { background: rgba(25,118,210,0.15);   color: #1976d2; }
.dot-status_change { background: rgba(245,158,11,0.15);   color: #b45309; }
.dot-task_link     { background: rgba(106,27,154,0.15);   color: #6a1b9a; }
.dot-file          { background: rgba(0,137,123,0.15);    color: #00695c; }
.dot-convert       { background: rgba(34,197,94,0.15);    color: #166534; }
.dot-created       { background: rgba(96,125,139,0.15);   color: #455a64; }

.feed-body { min-width: 0; }
.feed-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.feed-author { font-size: 0.88rem; color: var(--md-sys-color-on-surface); }
.feed-item__delete {
  margin-left: auto;
  opacity: 0;
  transition: opacity 0.12s ease;
}
.feed-item:hover .feed-item__delete { opacity: 1; }
.feed-content {
  font-size: 0.9rem;
  color: var(--md-sys-color-on-surface);
  line-height: 1.4;
  white-space: pre-wrap;
}
.feed-content--status {
  display: flex;
  align-items: center;
  gap: 6px;
}
.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  background: var(--md-sys-color-surface-container);
  color: var(--md-sys-color-on-surface);
}

.feed-task {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: var(--md-sys-color-surface-container-low, #f7fafc);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 8px;
  flex-wrap: wrap;
}
.feed-task__title {
  color: var(--md-sys-color-primary, #1976d2);
  text-decoration: none;
  font-weight: 500;
}
.feed-task__title:hover { text-decoration: underline; }
.feed-task__status {
  padding: 1px 7px;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
  background: rgba(0,0,0,0.06);
}
.task-status-new         { background: rgba(96,125,139,0.15); color: #455a64; }
.task-status-in_progress { background: rgba(59,130,246,0.15); color: #1d4ed8; }
.task-status-pending     { background: rgba(245,158,11,0.15); color: #b45309; }
.task-status-completed   { background: rgba(34,197,94,0.15);  color: #166534; }
.task-status-cancelled   { background: rgba(239,68,68,0.15);  color: #b91c1c; }
.task-status-deferred    { background: rgba(99,102,241,0.15); color: #4338ca; }

.feed-file {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.feed-file__name {
  color: var(--md-sys-color-primary, #1976d2);
  font-weight: 500;
}
.feed-file-caption { margin-top: 2px; }

/* Avatars */
.user-avatar {
  width: 24px; height: 24px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.66rem;
  font-weight: 700;
  color: #fff;
  background: #607d8b;
  flex-shrink: 0;
  overflow: hidden;
}
.user-avatar.sm { width: 24px; height: 24px; }
.user-avatar img { width: 100%; height: 100%; object-fit: cover; }
.avatar-blue { background: #1976d2; }
.avatar-teal { background: #00897b; }
.avatar-amber { background: #f57c00; }
.avatar-pink { background: #d81b60; }
.avatar-purple { background: #6a1b9a; }
.avatar-green { background: #2e7d32; }
.avatar-red { background: #c62828; }
.avatar-indigo { background: #3949ab; }

.icon-btn {
  width: 24px; height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
}
.icon-btn:hover { background: rgba(0,0,0,0.06); }
.icon-btn--danger:hover { background: rgba(198,40,40,0.1); color: #c62828; }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 2rem 1rem;
  color: var(--md-sys-color-on-surface-variant);
}
.empty-state i {
  font-size: 2rem;
  margin-bottom: 8px;
  color: var(--md-sys-color-outline-variant);
}
.empty-state p { margin: 0 0 4px; font-weight: 500; color: var(--md-sys-color-on-surface); }
.d-none { display: none; }
</style>
