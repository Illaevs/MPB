<template>
  <div class="task-chat">
    <div class="task-chat__header">
      <div class="task-chat__title">
        <i class="far fa-comment"></i>
        <span>Чат задачи</span>
      </div>
      <div class="task-chat__header-actions">
        <button
          type="button"
          class="task-chat__icon-btn"
          :class="{ 'is-active': searchOpen }"
          :title="searchOpen ? 'Скрыть поиск' : 'Поиск по чату (/)'"
          @click="toggleSearch"
        >
          <i class="fas fa-magnifying-glass"></i>
        </button>
        <button
          type="button"
          class="task-chat__refresh"
          :disabled="loading"
          @click="refreshMessages"
        >
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
          <span>Обновить</span>
        </button>
      </div>
    </div>

    <div v-if="searchOpen" class="task-chat__search-bar">
      <i class="fas fa-magnifying-glass"></i>
      <input
        ref="searchInput"
        v-model="searchQuery"
        type="text"
        class="task-chat__search-input"
        placeholder="Найти в чате…"
        @keydown.esc.prevent="closeSearch"
      />
      <span v-if="searchQuery" class="task-chat__search-count">
        {{ filteredMessageCount }} {{ pluralMatch(filteredMessageCount) }}
      </span>
      <button
        v-if="searchQuery"
        type="button"
        class="task-chat__icon-btn"
        title="Очистить"
        @click="searchQuery = ''"
      >
        <i class="fas fa-times"></i>
      </button>
    </div>

    <div class="task-chat__body">
      <div class="task-chat__list" ref="listRef">
        <div v-if="loading" class="task-chat__placeholder">
          <i class="fas fa-spinner fa-spin mr-1"></i> Загружаем сообщения...
        </div>
        <div v-else-if="!chatItems.length" class="task-chat__placeholder">
          Сообщений пока нет. Начните обсуждение задачи.
        </div>
        <div v-else-if="!chatItems.length && searchQuery" class="task-chat__placeholder">
          <i class="fas fa-magnifying-glass mr-1"></i>
          По запросу «{{ searchQuery }}» ничего не найдено
        </div>
        <div v-else class="task-chat__messages">
          <template v-for="item in chatItems" :key="item.key">
            <div v-if="item.type === 'day'" class="task-chat__day-chip">
              {{ item.label }}
            </div>
            <div
              v-else
              class="task-chat__message-row"
              :class="{ 'is-own': isOwn(item.message), 'is-deleted': item.message.is_deleted }"
            >
              <div
                class="task-chat__avatar"
                :class="{ 'task-chat__avatar--image': !!getMessageAvatarUrl(item.message) }"
                :style="getMessageAvatarUrl(item.message) ? null : getMessageAvatarStyle(item.message)"
              >
                <img
                  v-if="getMessageAvatarUrl(item.message) && !isAvatarBroken(getMessageAvatarUrl(item.message))"
                  :src="getMessageAvatarUrl(item.message)"
                  :alt="item.message.user_name || 'Пользователь'"
                  class="task-chat__avatar-image"
                  @error="markAvatarBroken(getMessageAvatarUrl(item.message))"
                >
                <span v-else>{{ getMessageInitial(item.message) }}</span>
              </div>

              <div class="task-chat__message-main">
                <div class="task-chat__meta">
                  <span class="task-chat__author">{{ item.message.user_name || 'Пользователь' }}</span>
                  <span class="task-chat__time">{{ formatTime(item.message.created_at) }}</span>
                  <span v-if="item.message.edited_at" class="task-chat__edited">изменено</span>
                </div>

                <div class="task-chat__bubble" :class="{ 'is-own': isOwn(item.message) }">
                  <template v-if="item.message.is_deleted">
                    <span class="task-chat__deleted">Сообщение удалено</span>
                  </template>
                  <template v-else>
                    <div v-if="editingId === item.message.id" class="task-chat__edit">
                      <textarea v-model="editingBody" class="form-control" rows="4"></textarea>
                      <div class="task-chat__edit-actions">
                        <button type="button" class="btn btn-sm btn-primary" @click="saveEdit(item.message)">
                          Сохранить
                        </button>
                        <button type="button" class="btn btn-sm btn-outline-secondary" @click="cancelEdit">
                          Отмена
                        </button>
                      </div>
                    </div>
                    <template v-else>
                      <div
                        v-if="item.message.body"
                        class="task-chat__text"
                        v-html="renderBodyHtml(item.message)"
                      ></div>
                      <div v-if="item.message.attachments?.length" class="task-chat__attachments">
                        <template v-for="file in item.message.attachments" :key="file.path || file.name">
                          <button
                            v-if="isImageAttachment(file)"
                            type="button"
                            class="task-chat__image-attachment"
                            :title="file.name || 'Изображение'"
                            @click="openImageLightbox(file)"
                          >
                            <img
                              :src="file.download_url || file.url || ''"
                              :alt="file.name || 'Изображение'"
                              loading="lazy"
                            />
                          </button>
                          <button
                            v-else
                            type="button"
                            class="task-chat__attachment"
                            @click="downloadAttachment(file)"
                          >
                            <span class="task-chat__attachment-icon">
                              <i :class="fileIconClass(file)"></i>
                            </span>
                            <span class="task-chat__attachment-content">
                              <span class="task-chat__attachment-name">{{ file.name || 'Файл' }}</span>
                              <span v-if="file.size" class="task-chat__attachment-size">{{ formatSize(file.size) }}</span>
                            </span>
                          </button>
                        </template>
                      </div>
                    </template>
                  </template>
                </div>

                <div v-if="canEdit(item.message) && editingId !== item.message.id" class="task-chat__message-actions">
                  <button type="button" class="task-chat__link-btn" @click="startEdit(item.message)">Редактировать</button>
                  <button type="button" class="task-chat__link-btn is-danger" @click="deleteMessage(item.message)">Удалить</button>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>

      <div v-if="canWrite" class="task-chat__composer">
        <div v-if="selectedMentions.length" class="task-chat__mentions">
          <span v-for="mention in selectedMentions" :key="mention.id" class="task-chat__mention-chip">
            @{{ mention.name }}
            <button type="button" @click="removeMention(mention.id)">
              <i class="fas fa-times"></i>
            </button>
          </span>
        </div>

        <div v-if="pendingFiles.length" class="task-chat__file-list">
          <div
            v-for="(file, idx) in pendingFiles"
            :key="file.name + idx"
            class="task-chat__pending-file"
            :class="{ 'is-uploading': sending }"
          >
            <span class="task-chat__pending-file-main">
              <i v-if="sending" class="fas fa-spinner fa-spin"></i>
              <i v-else class="fas fa-paperclip"></i>
              <span>{{ file.name }}</span>
            </span>
            <span class="task-chat__pending-file-meta">
              {{ sending ? 'Загрузка…' : formatSize(file.size) }}
            </span>
            <button
              type="button"
              class="task-chat__pending-remove"
              :disabled="sending"
              :title="sending ? 'Идёт загрузка…' : 'Убрать файл'"
              @click="removeFile(idx)"
            >
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>

        <div class="task-chat__composer-bar">
          <div class="task-chat__input-wrap">
            <textarea
              ref="inputRef"
              v-model="draft"
              class="task-chat__input"
              rows="1"
              placeholder="Напишите сообщение… (Enter — отправить, Shift/Ctrl+Enter — перенос строки)"
              :style="{ maxHeight: inputMaxHeight + 'px' }"
              @input="onComposerInput"
              @keydown="onComposerKeydownMention"
              @keydown.enter.exact.prevent.stop="sendMessage"
            ></textarea>
            <!-- Phase D.3 — inline @-mention autocomplete (user/deal/task). -->
            <div
              v-if="mentionAutoOpen && mentionAutoResults.length"
              class="task-chat__mention-auto"
              @mousedown.prevent
            >
              <button
                v-for="(item, idx) in mentionAutoResults"
                :key="`${item.kind}:${item.id}`"
                type="button"
                class="task-chat__mention-auto-item"
                :class="{ 'is-active': idx === mentionAutoActiveIdx }"
                @click="pickMentionAutoItem(item)"
                @mouseenter="mentionAutoActiveIdx = idx"
              >
                <span class="task-chat__mention-auto-kind" :data-kind="item.kind">
                  <i
                    :class="
                      item.kind === 'user'
                        ? 'fas fa-user'
                        : item.kind === 'deal'
                          ? 'fas fa-briefcase'
                          : 'fas fa-tasks'
                    "
                  ></i>
                </span>
                <span class="task-chat__mention-auto-copy">
                  <strong>{{ item.label }}</strong>
                  <small v-if="item.sublabel">{{ item.sublabel }}</small>
                </span>
              </button>
            </div>
          </div>

          <div class="task-chat__composer-actions">
            <button type="button" class="task-chat__tool-btn" title="Прикрепить файл" @click="openFilePicker">
              <i class="fas fa-paperclip"></i>
            </button>
            <button type="button" class="task-chat__tool-btn" title="Упомянуть" @click="toggleMentions">
              <i class="fas fa-at"></i>
            </button>
            <button type="button" class="task-chat__send-btn" :disabled="sending" @click="sendMessage">
              <i v-if="sending" class="fas fa-spinner fa-spin"></i>
              <i v-else class="fas fa-paper-plane"></i>
            </button>
          </div>
        </div>

        <input ref="fileInput" type="file" class="d-none" multiple @change="onFilesPicked" />

        <div v-if="mentionPickerOpen" class="task-chat__mention-picker">
          <div class="task-chat__mention-header">
            <input
              v-model="mentionQuery"
              class="form-control form-control-sm"
              placeholder="Поиск пользователя"
            >
            <button type="button" class="task-chat__link-btn" @click="mentionPickerOpen = false">Закрыть</button>
          </div>
          <div class="task-chat__mention-list">
            <button
              v-for="user in mentionOptions"
              :key="user.id"
              type="button"
              class="task-chat__mention-option"
              @click="addMention(user)"
            >
              <span
                class="task-chat__mention-avatar"
                :class="{ 'task-chat__mention-avatar--image': !!String(user.avatar_url || '').trim() }"
                :style="String(user.avatar_url || '').trim() ? null : getAvatarTheme(`${user.id}${user.full_name || ''}`)"
              >
                <img
                  v-if="String(user.avatar_url || '').trim() && !isAvatarBroken(user.avatar_url)"
                  :src="user.avatar_url"
                  :alt="user.full_name || user.email || user.id"
                  class="task-chat__mention-avatar-image"
                  @error="markAvatarBroken(user.avatar_url)"
                >
                <span v-else>{{ getMessageInitial({ user_name: user.full_name || user.email || user.id }) }}</span>
              </span>
              <span class="task-chat__mention-copy">
                <strong>{{ user.full_name || user.email || user.id }}</strong>
                <small>{{ user.email || 'Пользователь ERP' }}</small>
              </span>
            </button>
            <div v-if="!mentionOptions.length" class="task-chat__mention-empty">Никого не нашли</div>
          </div>
        </div>
      </div>

      <div v-else class="task-chat__readonly">Нет доступа к чату задачи</div>
    </div>

    <Teleport to="body">
      <div
        v-if="lightboxFile"
        class="task-chat-lightbox"
        @click.self="closeImageLightbox"
      >
        <button type="button" class="task-chat-lightbox__close" @click="closeImageLightbox">
          <i class="fas fa-times"></i>
        </button>
        <img
          :src="lightboxFile.download_url || lightboxFile.url || ''"
          :alt="lightboxFile.name || 'Изображение'"
          class="task-chat-lightbox__image"
        />
        <div class="task-chat-lightbox__caption">
          <span>{{ lightboxFile.name || 'Изображение' }}</span>
          <button
            type="button"
            class="btn btn-sm btn-outline-secondary task-chat-lightbox__download"
            @click="downloadAttachment(lightboxFile)"
          >
            <i class="fas fa-download mr-1"></i> Скачать
          </button>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="confirmModalOpen" class="task-chat-confirm-overlay" v-modal-close="() => confirmModalOpen = false">
        <div class="task-chat-confirm-glass">
          <div class="task-chat-confirm-header">
            <h5 class="m-0">{{ confirmModalTitle }}</h5>
            <button class="btn btn-sm btn-icon task-chat-confirm-close" @click="confirmModalOpen = false">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="task-chat-confirm-body">
            <p class="m-0">{{ confirmModalText }}</p>
          </div>
          <div class="task-chat-confirm-footer">
            <button class="btn btn-outline-secondary btn-sm" @click="confirmModalOpen = false">Отмена</button>
            <button class="btn btn-danger btn-sm" @click="executeConfirm">
              <i class="fas fa-check mr-1"></i> Подтвердить
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { api } from '@/services/api'
import { getActiveUser } from '../utils/permissions'
import { useToast } from '../composables/useToast'
import { downloadFromApi } from '../utils/download'
import { normalizeAvatarUrl } from '../utils/avatar'
import { parseServerDate } from '../composables/useServerClock'
import { formatTime as fmtServerTime, formatDate as fmtServerDate } from '../utils/format'

const AVATAR_THEMES = [
  { background: 'linear-gradient(135deg, #d7e7ff 0%, #b4d0ff 100%)', color: '#2563eb' },
  { background: 'linear-gradient(135deg, #ffe4d3 0%, #ffc79c 100%)', color: '#b45309' },
  { background: 'linear-gradient(135deg, #e8ddff 0%, #c8b4ff 100%)', color: '#7c3aed' },
  { background: 'linear-gradient(135deg, #d9f7ec 0%, #a9e7cb 100%)', color: '#0f8f5d' },
  { background: 'linear-gradient(135deg, #ffe7ef 0%, #ffc3d3 100%)', color: '#be185d' }
]

export default {
  name: 'TaskChat',
  props: {
    taskId: { type: [String, Number], required: false, default: '' },
    users: { type: Array, default: () => [] },
    canRead: { type: Boolean, default: false },
    canWrite: { type: Boolean, default: false }
  },
  emits: ['message-count'],
  setup(props, { emit }) {
    const { error: toastError } = useToast()

    const confirmModalOpen = ref(false)
    const brokenAvatarUrls = ref(new Set())
    const confirmModalTitle = ref('')
    const confirmModalText = ref('')
    const confirmModalAction = ref(null)
    const showConfirm = (title, text, action) => {
      confirmModalTitle.value = title
      confirmModalText.value = text
      confirmModalAction.value = action
      confirmModalOpen.value = true
    }
    const executeConfirm = () => {
      confirmModalOpen.value = false
      if (confirmModalAction.value) confirmModalAction.value()
    }

    const messages = ref([])
    watch(
      messages,
      (list) => emit('message-count', Array.isArray(list) ? list.length : 0),
      { deep: false }
    )
    const loading = ref(false)

    // Search ---------------------------------------------------
    const searchOpen = ref(false)
    const searchQuery = ref('')
    const searchInput = ref(null)
    const toggleSearch = () => {
      searchOpen.value = !searchOpen.value
      if (searchOpen.value) {
        nextTick(() => searchInput.value?.focus())
      } else {
        searchQuery.value = ''
      }
    }
    const closeSearch = () => {
      searchOpen.value = false
      searchQuery.value = ''
    }
    const pluralMatch = (n) => {
      const mod10 = n % 10
      const mod100 = n % 100
      if (mod10 === 1 && mod100 !== 11) return 'совпадение'
      if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return 'совпадения'
      return 'совпадений'
    }

    // Lightbox (image preview) ---------------------------------
    const lightboxFile = ref(null)
    const openImageLightbox = (file) => { lightboxFile.value = file }
    const closeImageLightbox = () => { lightboxFile.value = null }

    const IMAGE_EXT_RE = /\.(png|jpe?g|gif|webp|bmp|svg|avif|heic)$/i
    const isImageAttachment = (file) => {
      if (!file) return false
      if (file.mime && String(file.mime).startsWith('image/')) return true
      if (file.content_type && String(file.content_type).startsWith('image/')) return true
      return IMAGE_EXT_RE.test(String(file.name || ''))
    }
    const fileIconClass = (file) => {
      const name = String(file?.name || '').toLowerCase()
      if (/\.(pdf)$/.test(name)) return 'far fa-file-pdf'
      if (/\.(xlsx?|csv)$/.test(name)) return 'far fa-file-excel'
      if (/\.(docx?)$/.test(name)) return 'far fa-file-word'
      if (/\.(pptx?)$/.test(name)) return 'far fa-file-powerpoint'
      if (/\.(zip|rar|7z|tar|gz)$/.test(name)) return 'far fa-file-zipper'
      if (/\.(mp4|mov|avi|mkv|webm)$/.test(name)) return 'far fa-file-video'
      if (/\.(mp3|wav|ogg|flac)$/.test(name)) return 'far fa-file-audio'
      if (/\.(txt|md|log)$/.test(name)) return 'far fa-file-lines'
      return 'far fa-file'
    }

    // Mention chips in rendered body ---------------------------
    const escapeHtml = (str) => String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
    const linkifyUrl = (text) => {
      return text.replace(
        /(https?:\/\/[^\s<]+)/g,
        (m) => `<a href="${m}" target="_blank" rel="noopener noreferrer" class="task-chat__link">${m}</a>`
      )
    }
    // Phase D.3 — рендер @-mentions с поддержкой нового формата
    // (mentions = массив объектов {kind, id, label, href}).
    // Алгоритм: сначала пробуем новый формат (структурированные mentions
    // из message.mentions); fallback — старый по списку юзеров props.users.
    const renderBodyHtml = (message) => {
      const raw = String(message?.body || '')
      if (!raw) return ''
      let html = escapeHtml(raw)

      // 1) Новый формат: extended mentions с label/href/kind.
      const ext = (message?.mentions || []).filter(
        (m) => m && typeof m === 'object' && m.label
      )
      const usedRanges = []
      ext.forEach((m) => {
        const name = String(m.label || '').trim()
        if (!name) return
        const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
        const re = new RegExp('@' + escaped, 'g')
        // Defensive: старые href /deals/<id> → /projects/<id>
        let href = String(m.href || '')
        if (href.startsWith('/deals/')) href = '/projects/' + href.slice('/deals/'.length)
        const kind = String(m.kind || '')
        const escapedLabel = escapeHtml(name)
        const chip = href
          ? `<a href="${href}" class="task-chat__mention-inline" data-kind="${kind}" data-id="${m.id}">@${escapedLabel}</a>`
          : `<span class="task-chat__mention-inline task-chat__mention-inline--inert" data-kind="${kind}" data-id="${m.id}">@${escapedLabel}</span>`
        html = html.replace(re, chip)
      })

      // 2) Старый формат fallback: подменяем по списку известных юзеров.
      // Не трогаем фрагменты, уже превращённые в chip-теги (наивная проверка
      // на '<a' / '<span' слева от позиции — но т.к. мы уже заменили выше,
      // повторно делаем replace только по чистому остатку: ОК для большинства
      // случаев. Если новый формат покрыл всех — здесь почти пусто.
      const usersList = props.users || []
      const sorted = usersList.slice().sort((a, b) => {
        return String(b.full_name || '').length - String(a.full_name || '').length
      })
      sorted.forEach((u) => {
        const name = String(u.full_name || u.email || '').trim()
        if (!name) return
        // Проверяем что мы уже не сделали chip для этого имени.
        if (html.includes(`>@${escapeHtml(name)}</a>`) || html.includes(`>@${escapeHtml(name)}</span>`)) return
        const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
        const re = new RegExp('@' + escaped, 'gi')
        html = html.replace(re, `<span class="task-chat__mention-inline" data-user-id="${u.id}">@${escapeHtml(name)}</span>`)
      })

      html = linkifyUrl(html)
      return html
    }

    // Computed: chatItems filters by search.
    const matchesSearch = (text) => {
      const q = (searchQuery.value || '').trim().toLowerCase()
      if (!q) return true
      return String(text || '').toLowerCase().includes(q)
    }
    const visibleMessages = computed(() => {
      const q = (searchQuery.value || '').trim()
      if (!q) return messages.value
      return messages.value.filter((m) =>
        matchesSearch(m.body) ||
        (Array.isArray(m.attachments) && m.attachments.some((f) => matchesSearch(f.name)))
      )
    })
    const filteredMessageCount = computed(() => visibleMessages.value.length)
    const sending = ref(false)
    const draft = ref('')
    const pendingFiles = ref([])
    const selectedMentions = ref([])
    const mentionPickerOpen = ref(false)
    const mentionQuery = ref('')
    const editingId = ref(null)
    const editingBody = ref('')
    const pollingTimer = ref(null)
    const listRef = ref(null)
    const fileInput = ref(null)
    const inputRef = ref(null)
    // Динамический cap высоты поля ввода: «не более X высоты чата».
    // Дефолт — 200px, пересчёт при mount/resize. См. recomputeInputMax().
    const inputMaxHeight = ref(200)

    const activeUser = computed(() => getActiveUser())
    const pollingActive = computed(() => !!pollingTimer.value)

    const mentionOptions = computed(() => {
      const query = (mentionQuery.value || '').trim().toLowerCase()
      const base = props.users || []
      const filtered = query
        ? base.filter((u) => (u.full_name || u.email || '').toLowerCase().includes(query))
        : base
      const selectedIds = new Set(selectedMentions.value.map((item) => item.id))
      return filtered.filter((u) => u && !selectedIds.has(u.id))
    })

    const getAvatarTheme = (seed) => {
      const key = String(seed || '?')
      const index = key.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0) % AVATAR_THEMES.length
      return AVATAR_THEMES[index]
    }

    const getUserRecord = (userId) => {
      if (!userId) return null
      return (props.users || []).find((item) => String(item.id) === String(userId)) || null
    }

    const getMessageAvatarUrl = (message) => {
      const user = getUserRecord(message?.user_id)
      return normalizeAvatarUrl(user?.avatar_url || '', user?.id || message?.user_id || '')
    }
    const isAvatarBroken = (url) => {
      const normalized = String(url || '').trim()
      return normalized ? brokenAvatarUrls.value.has(normalized) : false
    }
    const markAvatarBroken = (url) => {
      const normalized = String(url || '').trim()
      if (!normalized || brokenAvatarUrls.value.has(normalized)) return
      brokenAvatarUrls.value = new Set([...brokenAvatarUrls.value, normalized])
    }

    const getMessageAvatarStyle = (message) => getAvatarTheme(`${message?.user_id || ''}${message?.user_name || ''}`)

    const getMessageInitial = (message) => {
      const value = String(message?.user_name || 'П').trim()
      return value.charAt(0).toUpperCase() || 'П'
    }

    const isOwn = (message) => {
      const userId = activeUser.value?.id
      return !!(userId && String(message?.user_id) === String(userId))
    }

    const canEdit = (message) => {
      if (!message || message.is_deleted) return false
      const userId = activeUser.value?.id
      if (activeUser.value?.is_superuser) return true
      return !!(userId && String(message.user_id) === String(userId))
    }

    // Время сообщения в чате — серверное (МСК). Раньше использовался
    // локальный `new Date(value).toLocaleString()`, который трактовал
    // naive ISO с бэка как локальное время браузера — у юзеров вне МСК
    // время показывалось «−3 часа».
    const formatTime = (value) => {
      if (!value) return ''
      return fmtServerTime(value) || ''
    }

    // День сравниваем тоже в МСК: иначе сообщение, отправленное в МСК
    // 00:30, для UTC-юзера попадёт во «вчера». Через parseServerDate
    // получаем правильный Date, дальше сравниваем по YYYY-MM-DD в МСК.
    const mskDayKey = (value) => {
      if (!value) return ''
      const d = value instanceof Date ? value : parseServerDate(value)
      if (!d) return ''
      // Intl с timeZone:'Europe/Moscow' → стабильный ключ дня независимо
      // от TZ браузера.
      return new Intl.DateTimeFormat('en-CA', {
        timeZone: 'Europe/Moscow', year: 'numeric', month: '2-digit', day: '2-digit',
      }).format(d)
    }

    const isSameDay = (left, right) => {
      const a = mskDayKey(left)
      const b = mskDayKey(right)
      return Boolean(a) && a === b
    }

    const formatDayLabel = (value) => {
      if (!value) return ''
      const today = new Date()
      const yesterday = new Date()
      yesterday.setDate(today.getDate() - 1)
      const short = fmtServerDate(value, { day: 'numeric', month: 'short', year: undefined })
      if (isSameDay(value, today)) return `Сегодня, ${short}`
      if (isSameDay(value, yesterday)) return `Вчера, ${short}`
      return fmtServerDate(value, { weekday: 'long', day: 'numeric', month: 'short', year: undefined })
    }

    const chatItems = computed(() => {
      const result = []
      let previousDate = null
      visibleMessages.value.forEach((message) => {
        if (!isSameDay(message.created_at, previousDate)) {
          result.push({
            type: 'day',
            key: `day-${message.id}`,
            label: formatDayLabel(message.created_at)
          })
        }
        result.push({
          type: 'message',
          key: message.id,
          message
        })
        previousDate = message.created_at
      })
      return result
    })

    const formatSize = (bytes) => {
      if (!bytes && bytes !== 0) return ''
      const sizes = ['Б', 'КБ', 'МБ', 'ГБ']
      let index = 0
      let value = Number(bytes)
      while (value >= 1024 && index < sizes.length - 1) {
        value /= 1024
        index += 1
      }
      return `${value.toFixed(value >= 10 || index === 0 ? 0 : 1)} ${sizes[index]}`
    }

    const scrollToBottom = async () => {
      await nextTick()
      const el = listRef.value
      if (!el) return
      el.scrollTop = el.scrollHeight
    }

    const shouldUpdateMessages = (nextItems, currentItems) => {
      if (nextItems.length !== currentItems.length) return true
      for (let i = 0; i < nextItems.length; i += 1) {
        const next = nextItems[i]
        const current = currentItems[i]
        if (!current) return true
        if (next.id !== current.id) return true
        if (next.updated_at !== current.updated_at) return true
        if (next.is_deleted !== current.is_deleted) return true
        const nextFiles = Array.isArray(next.attachments) ? next.attachments.length : 0
        const currFiles = Array.isArray(current.attachments) ? current.attachments.length : 0
        if (nextFiles !== currFiles) return true
      }
      return false
    }

    const loadMessages = async ({ silent = false } = {}) => {
      if (!props.taskId || !props.canRead) return
      if (!silent) loading.value = true
      try {
        const res = await api.tasks.listMessages(props.taskId)
        const nextItems = res || []
        if (shouldUpdateMessages(nextItems, messages.value)) {
          const hadNew = nextItems.length > messages.value.length
          messages.value = nextItems
          if (hadNew) {
            await scrollToBottom()
          }
        }
      } catch (e) {
        toastError('Ошибка загрузки сообщений')
      } finally {
        if (!silent) loading.value = false
      }
    }

    const refreshMessages = () => {
      if (loading.value) return
      return loadMessages()
    }

    const startPolling = () => {
      if (pollingTimer.value || !props.taskId || !props.canRead) return
      pollingTimer.value = setInterval(() => loadMessages({ silent: true }), 10000)
    }

    const stopPolling = () => {
      if (pollingTimer.value) {
        clearInterval(pollingTimer.value)
        pollingTimer.value = null
      }
    }

    const openFilePicker = () => {
      if (fileInput.value) fileInput.value.click()
    }

    const onFilesPicked = (event) => {
      const files = Array.from(event.target.files || [])
      if (!files.length) return
      pendingFiles.value = [...pendingFiles.value, ...files]
      event.target.value = ''
    }

    const removeFile = (idx) => {
      pendingFiles.value.splice(idx, 1)
    }

    const toggleMentions = () => {
      mentionPickerOpen.value = !mentionPickerOpen.value
      mentionQuery.value = ''
    }

    const addMention = (user) => {
      if (!user) return
      // Через старую модалку (только users). Сохраняем kind=user
      // чтобы и старый, и новый формат вели себя одинаково в renderBodyHtml.
      selectedMentions.value.push({
        id: user.id,
        name: user.full_name || user.email || user.id,
        label: user.full_name || user.email || user.id,
        kind: 'user',
        href: '',
      })
      draft.value = `${draft.value.trim()} @${user.full_name || user.email || ''} `.trim() + ' '
    }

    const removeMention = (userId) => {
      selectedMentions.value = selectedMentions.value.filter((item) => item.id !== userId)
    }

    // Phase D.3 — inline @-mention autocomplete для TaskChat
    // (как в Messenger). Триггер по `@<query>` в textarea, popup
    // показывает users + deals + tasks через /chat/mention-search.
    // Если юзер выбрал — вставляем `@label ` в draft и сохраняем
    // структуру в selectedMentions.
    const mentionAutoOpen = ref(false)
    const mentionAutoResults = ref([])
    const mentionAutoActiveIdx = ref(0)
    const mentionAutoStart = ref(-1)  // позиция «@» в тексте
    const mentionAutoQuery = ref('')
    let _mentionFetchTimer = null

    const _detectMentionTrigger = () => {
      const el = inputRef.value
      if (!el) return null
      const caret = el.selectionStart ?? draft.value.length
      const text = draft.value || ''
      // Откатываемся назад от каретки, ищем последний `@` НЕ внутри
      // другого слова. Если по дороге встретили пробел/перенос —
      // триггер не работает.
      let i = caret - 1
      while (i >= 0) {
        const ch = text[i]
        if (ch === '@') {
          if (i === 0 || /\s/.test(text[i - 1])) {
            const query = text.slice(i + 1, caret)
            if (/^[\wа-яёА-ЯЁ\- .]*$/.test(query)) {
              return { at: i, query }
            }
          }
          return null
        }
        if (/\s/.test(ch)) return null
        i -= 1
      }
      return null
    }

    const _fetchMentionResults = (q) => {
      if (_mentionFetchTimer) clearTimeout(_mentionFetchTimer)
      _mentionFetchTimer = setTimeout(async () => {
        try {
          const data = await api.messenger.mentionSearch(q)
          mentionAutoResults.value = Array.isArray(data) ? data : []
          mentionAutoActiveIdx.value = 0
        } catch (e) {
          mentionAutoResults.value = []
        }
      }, 180)
    }

    const closeMentionAutocomplete = () => {
      mentionAutoOpen.value = false
      mentionAutoResults.value = []
      mentionAutoStart.value = -1
      mentionAutoQuery.value = ''
    }

    const pickMentionAutoItem = (item) => {
      if (!item || mentionAutoStart.value < 0) {
        closeMentionAutocomplete()
        return
      }
      const text = draft.value || ''
      const start = mentionAutoStart.value
      const el = inputRef.value
      const caret = el?.selectionStart ?? text.length
      const before = text.slice(0, start)
      const after = text.slice(caret)
      const insert = `@${item.label} `
      draft.value = `${before}${insert}${after}`
      // Сохраняем структуру в selectedMentions, дабы при отправке
      // backend получил kind/id/label/href — renderBodyHtml у получателя
      // тоже использует mentions из ответа.
      selectedMentions.value = [
        ...selectedMentions.value,
        {
          id: item.id,
          name: item.label,
          label: item.label,
          kind: item.kind,
          href: item.href || '',
        },
      ]
      closeMentionAutocomplete()
      nextTick(() => {
        const e = inputRef.value
        if (e?.focus) {
          e.focus()
          const newCaret = before.length + insert.length
          try { e.setSelectionRange(newCaret, newCaret) } catch (err) { /* ignore */ }
        }
        autoResizeInput()
      })
    }

    // Обработчик ввода: проверяем триггер `@<query>` после каждого
    // изменения. Если есть — открываем popup и подтягиваем результаты.
    const onComposerInput = () => {
      autoResizeInput()
      const trig = _detectMentionTrigger()
      if (trig) {
        mentionAutoOpen.value = true
        mentionAutoStart.value = trig.at
        mentionAutoQuery.value = trig.query
        if (trig.query.length >= 1) _fetchMentionResults(trig.query)
        else mentionAutoResults.value = []
      } else {
        mentionAutoOpen.value = false
        mentionAutoResults.value = []
        mentionAutoStart.value = -1
      }
    }

    const onComposerKeydownMention = (event) => {
      if (!mentionAutoOpen.value || !mentionAutoResults.value.length) return false
      if (event.key === 'ArrowDown') {
        event.preventDefault()
        mentionAutoActiveIdx.value =
          (mentionAutoActiveIdx.value + 1) % mentionAutoResults.value.length
        return true
      }
      if (event.key === 'ArrowUp') {
        event.preventDefault()
        mentionAutoActiveIdx.value =
          (mentionAutoActiveIdx.value - 1 + mentionAutoResults.value.length) %
          mentionAutoResults.value.length
        return true
      }
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault()
        pickMentionAutoItem(mentionAutoResults.value[mentionAutoActiveIdx.value])
        return true
      }
      if (event.key === 'Escape') {
        event.preventDefault()
        closeMentionAutocomplete()
        return true
      }
      return false
    }

    const sendMessage = async () => {
      if (!props.taskId || sending.value) return
      const text = (draft.value || '').trim()
      if (!text && !pendingFiles.value.length) return
      sending.value = true
      try {
        const form = new FormData()
        if (text) form.append('body', text)
        if (selectedMentions.value.length) {
          // Phase D.3 — отправляем расширенный формат если есть kind,
          // иначе остаётся backward-compat (просто user_id строки).
          const payload = selectedMentions.value.map((item) => {
            if (item.kind) {
              return {
                kind: item.kind,
                id: item.id,
                label: item.label || item.name || '',
                href: item.href || '',
              }
            }
            return String(item.id)
          })
          form.append('mentions', JSON.stringify(payload))
        }
        pendingFiles.value.forEach((file) => form.append('files', file, file.name))
        const res = await api.tasks.sendMessage(props.taskId, form)
        if (res) {
          messages.value = [...messages.value, res]
        }
        draft.value = ''
        saveDraft(props.taskId, '')
        pendingFiles.value = []
        selectedMentions.value = []
        mentionPickerOpen.value = false
        // Сброс высоты textarea после отправки — иначе пустой инпут
        // остаётся «вытянутым» под прошлое сообщение.
        await nextTick()
        autoResizeInput()
        await scrollToBottom()
      } catch (e) {
        toastError('Ошибка отправки сообщения')
      } finally {
        sending.value = false
      }
    }

    // Auto-resize textarea как в Telegram: высота подгоняется под
    // содержимое, но не больше `inputMaxHeight` (динамический cap,
    // зависит от размера .task-chat). При cap включается внутренний
    // скролл textarea.
    const autoResizeInput = () => {
      const el = inputRef.value
      if (!el) return
      // Сброс на 'auto' нужен, чтобы scrollHeight не залипал на старом
      // (наибольшем за сессию) значении — иначе при удалении строк
      // textarea не сжимается.
      el.style.height = 'auto'
      const max = inputMaxHeight.value || 200
      const next = Math.min(el.scrollHeight, max)
      el.style.height = next + 'px'
    }

    // Пересчёт cap-а: 40% высоты `.task-chat`, но не меньше 80px и не
    // больше 320px. Это даёт «дифференциальность по масштабу»: при
    // высоком чате textarea может расти до 320px, при сжатом — резко
    // отрезается, чтобы оставить место под историей сообщений.
    const recomputeInputMax = () => {
      const host = document.querySelector('.task-chat')
      const h = host?.clientHeight || 0
      if (!h) return
      const next = Math.round(Math.min(320, Math.max(80, h * 0.4)))
      if (next !== inputMaxHeight.value) {
        inputMaxHeight.value = next
        autoResizeInput()
      }
    }

    const downloadAttachment = async (file) => {
      try {
        const url = file?.download_url
        if (!url) return
        await downloadFromApi(url, {}, file?.name || 'file', { module: 'task_chat', entityId: props.taskId })
      } catch (e) {
        toastError('Ошибка загрузки файла')
      }
    }

    const startEdit = (message) => {
      if (!message || !message.body) return
      editingId.value = message.id
      editingBody.value = message.body
    }

    const cancelEdit = () => {
      editingId.value = null
      editingBody.value = ''
    }

    const saveEdit = async (message) => {
      if (!editingId.value || !editingBody.value.trim()) return
      try {
        const res = await api.tasks.updateMessage(message.id, {
          body: editingBody.value.trim()
        })
        messages.value = messages.value.map((item) => (item.id === message.id ? res : item))
        cancelEdit()
      } catch (e) {
        toastError('Ошибка редактирования')
      }
    }

    const deleteMessage = (message) => {
      if (!message) return
      showConfirm('Удалить сообщение?', 'Сообщение будет удалено.', async () => {
        try {
          await api.tasks.deleteMessage(message.id)
          messages.value = messages.value.map((item) =>
            item.id === message.id ? { ...item, is_deleted: true, body: null } : item
          )
        } catch (e) {
          toastError('Ошибка удаления сообщения')
        }
      })
    }

    // Draft persistence per task_id ----------------------------
    const draftKey = (taskId) => `taskChat.draft.${taskId}`
    const loadDraft = (taskId) => {
      if (!taskId) return ''
      try { return localStorage.getItem(draftKey(taskId)) || '' }
      catch (_e) { return '' }
    }
    const saveDraft = (taskId, value) => {
      if (!taskId) return
      try {
        if (value && value.trim()) localStorage.setItem(draftKey(taskId), value)
        else localStorage.removeItem(draftKey(taskId))
      } catch (_e) { /* quota or disabled */ }
    }
    watch(draft, (value) => saveDraft(props.taskId, value))

    watch(
      () => props.taskId,
      async (newId) => {
        messages.value = []
        cancelEdit()
        draft.value = loadDraft(newId)
        if (!newId) return
        await loadMessages()
        startPolling()
      }
    )

    watch(
      () => props.canRead,
      (value) => {
        if (!value) {
          stopPolling()
          return
        }
        if (props.taskId) startPolling()
      }
    )

    let inputResizeObserver = null
    const onWindowResize = () => recomputeInputMax()

    onMounted(async () => {
      draft.value = loadDraft(props.taskId)
      if (props.taskId && props.canRead) {
        await loadMessages()
        startPolling()
      }
      // После маунта меряем контейнер чата и подстраиваем textarea.
      // ResizeObserver на `.task-chat` ловит изменения высоты модалки
      // (resizable drawer, кнопка свернуть/развернуть, поворот экрана).
      await nextTick()
      recomputeInputMax()
      autoResizeInput()
      const host = document.querySelector('.task-chat')
      if (host && typeof ResizeObserver !== 'undefined') {
        inputResizeObserver = new ResizeObserver(() => recomputeInputMax())
        inputResizeObserver.observe(host)
      }
      window.addEventListener('resize', onWindowResize)
    })

    onBeforeUnmount(() => {
      stopPolling()
      if (inputResizeObserver) { inputResizeObserver.disconnect(); inputResizeObserver = null }
      window.removeEventListener('resize', onWindowResize)
    })

    // При смене черновика по taskId — также подгонимая высоту (например,
    // загрузили сохранённый длинный черновик из localStorage).
    watch(() => draft.value, () => { nextTick(() => autoResizeInput()) })

    return {
      loading,
      sending,
      draft,
      pendingFiles,
      selectedMentions,
      mentionPickerOpen,
      mentionQuery,
      mentionOptions,
      editingId,
      editingBody,
      listRef,
      fileInput,
      inputRef,
      inputMaxHeight,
      autoResizeInput,
      pollingActive,
      chatItems,
      isOwn,
      canEdit,
      formatTime,
      formatSize,
      refreshMessages,
      openFilePicker,
      onFilesPicked,
      removeFile,
      toggleMentions,
      addMention,
      removeMention,
      // Phase D.3 — inline @-autocomplete
      mentionAutoOpen,
      mentionAutoResults,
      mentionAutoActiveIdx,
      onComposerInput,
      onComposerKeydownMention,
      pickMentionAutoItem,
      sendMessage,
      downloadAttachment,
      startEdit,
      cancelEdit,
      saveEdit,
      deleteMessage,
      getAvatarTheme,
      getMessageAvatarUrl,
      isAvatarBroken,
      markAvatarBroken,
      getMessageAvatarStyle,
      getMessageInitial,
      confirmModalOpen,
      confirmModalTitle,
      confirmModalText,
      executeConfirm,
      // search
      searchOpen,
      searchQuery,
      searchInput,
      toggleSearch,
      closeSearch,
      filteredMessageCount,
      pluralMatch,
      // attachments
      isImageAttachment,
      fileIconClass,
      lightboxFile,
      openImageLightbox,
      closeImageLightbox,
      // body rendering
      renderBodyHtml
    }
  }
}
</script>

<style scoped>
/* ============================================================
   TASK CHAT — token-based, dark mode via tokens (no !important).
   All colors come from main.css (--color-*, --chat-*, --space-*).
   ============================================================ */
.task-chat {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  background: var(--color-surface);
  color: var(--color-text);
}

.task-chat__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5) var(--space-3);
  border-bottom: 1px solid var(--color-border-subtle);
}

.task-chat__title {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
  color: var(--color-text);
  font-size: var(--text-md);
  font-weight: var(--fw-semibold);
}
.task-chat__title i {
  color: var(--color-text-muted);
  font-size: var(--text-lg);
}

.task-chat__status {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: var(--radius-pill);
  background: var(--color-success-soft);
  color: var(--color-success);
  font-size: var(--text-xs);
  font-weight: var(--fw-bold);
  line-height: 1;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.task-chat__header-actions {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.task-chat__icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 0;
  background: transparent;
  color: var(--color-text-muted);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}
.task-chat__icon-btn:hover { background: var(--color-surface-2); color: var(--color-text); }
.task-chat__icon-btn.is-active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}
.task-chat__icon-btn:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

.task-chat__search-bar {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border-subtle);
}
.task-chat__search-bar > i:first-child {
  color: var(--color-text-subtle);
}
.task-chat__search-input {
  flex: 1;
  border: 0;
  outline: none;
  background: transparent;
  color: var(--color-text);
  font-size: var(--text-md);
}
.task-chat__search-input::placeholder { color: var(--color-text-subtle); }
.task-chat__search-count {
  font-size: var(--text-sm);
  color: var(--color-text-subtle);
  white-space: nowrap;
}

.task-chat__refresh {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  border: 0;
  background: transparent;
  color: var(--color-text-muted);
  font-size: var(--text-base);
  font-weight: var(--fw-medium);
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}
.task-chat__refresh:hover {
  background: var(--color-surface-2);
  color: var(--color-text);
}
.task-chat__refresh:disabled { opacity: 0.6; cursor: default; }
.task-chat__refresh:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

.task-chat__body {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  /* Wallpaper from /public/wallpapers/task-chat.jpg, with a soft tint
     so chat bubbles remain readable on any part of the image. */
  background-image:
    linear-gradient(rgba(248, 250, 252, 0.55), rgba(248, 250, 252, 0.55)),
    url('/wallpapers/task-chat.jpg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  background-attachment: local;
}
:root[data-theme="dark"] .task-chat__body {
  background-image:
    linear-gradient(rgba(15, 23, 42, 0.78), rgba(15, 23, 42, 0.78)),
    url('/wallpapers/task-chat.jpg');
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) .task-chat__body {
    background-image:
      linear-gradient(rgba(15, 23, 42, 0.78), rgba(15, 23, 42, 0.78)),
      url('/wallpapers/task-chat.jpg');
  }
}

.task-chat__list {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: var(--space-5) var(--space-4) var(--space-4);
}

.task-chat__placeholder {
  color: var(--color-text-subtle);
  font-size: var(--text-md);
  text-align: center;
  padding: var(--space-12) var(--space-4);
}

.task-chat__messages {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.task-chat__day-chip {
  align-self: center;
  padding: 6px 14px;
  border-radius: var(--radius-pill);
  background: var(--color-surface-3);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  line-height: 1;
  position: sticky;
  top: 0;
  z-index: 1;
}

.task-chat__message-row {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  gap: var(--space-3);
  align-items: start;
}
.task-chat__message-row.is-own {
  grid-template-columns: minmax(0, 1fr) 36px;
}
.task-chat__message-row.is-own .task-chat__avatar { order: 2; }
.task-chat__message-row.is-own .task-chat__message-main {
  order: 1;
  align-items: flex-end;
}

.task-chat__message-main {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.task-chat__avatar,
.task-chat__mention-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-md);
  font-weight: var(--fw-bold);
  line-height: 1;
}
.task-chat__mention-avatar {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  font-size: var(--text-base);
}
.task-chat__avatar-image,
.task-chat__mention-avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.task-chat__meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
  color: var(--color-text-subtle);
  font-size: var(--text-sm);
  line-height: 1.2;
}
.task-chat__message-row.is-own .task-chat__meta { justify-content: flex-end; }
.task-chat__author {
  color: var(--color-text);
  font-weight: var(--fw-semibold);
}
:root[data-theme="dark"] .task-chat__author { color: var(--color-text-strong); }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) .task-chat__author { color: var(--color-text-strong); }
}
/* Time / "edited" tag — keep muted but light-friendly on dark wallpaper. */
.task-chat__time,
.task-chat__edited {
  color: var(--color-text-subtle);
}
:root[data-theme="dark"] .task-chat__time,
:root[data-theme="dark"] .task-chat__edited {
  color: var(--color-text-muted);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) .task-chat__time,
  :root:not([data-theme="light"]) .task-chat__edited {
    color: var(--color-text-muted);
  }
}
.task-chat__edited { font-style: italic; }

.task-chat__bubble {
  max-width: min(560px, 78%);
  padding: 10px 14px;
  border-radius: 14px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-xs);
}
.task-chat__bubble.is-own {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-on-primary);
  box-shadow: var(--shadow-sm);
}
.task-chat__message-row.is-deleted .task-chat__bubble { opacity: 0.65; }

.task-chat__text,
.task-chat__deleted {
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: anywhere;
  font-size: var(--text-md);
  line-height: var(--leading-normal);
}

.task-chat__attachments {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-top: var(--space-2);
}

.task-chat__image-attachment {
  display: block;
  width: fit-content;
  max-width: 100%;
  padding: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
  cursor: zoom-in;
  overflow: hidden;
  transition: transform var(--dur-fast) var(--ease-out), box-shadow var(--dur-fast) var(--ease-out);
}
.task-chat__image-attachment:hover {
  transform: scale(1.01);
  box-shadow: var(--shadow-md);
}
.task-chat__image-attachment img {
  display: block;
  max-width: 240px;
  max-height: 180px;
  width: auto;
  height: auto;
}

/* Phase D.3 — .task-chat__mention-inline стили вынесены в
   non-scoped блок в конце файла (см. ниже, после конца этого
   scoped блока), потому что v-html вставляет элементы без
   data-v scoped атрибута. */

/* Phase D.3 — inline @-mention autocomplete popup (TaskChat). */
.task-chat__input-wrap {
  position: relative;
  min-width: 0;
}
.task-chat__mention-auto {
  position: absolute;
  bottom: 100%;
  left: 0;
  right: 0;
  margin-bottom: 6px;
  max-height: 240px;
  overflow-y: auto;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  z-index: 30;
  padding: 4px;
}
.task-chat__mention-auto-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  text-align: left;
  border: 0;
  background: transparent;
  color: var(--color-text);
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
}
.task-chat__mention-auto-item:hover,
.task-chat__mention-auto-item.is-active {
  background: var(--color-surface-2);
}
.task-chat__mention-auto-kind {
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--color-surface-2);
  color: var(--color-text-muted);
  font-size: 0.8em;
  flex-shrink: 0;
}
.task-chat__mention-auto-kind[data-kind="deal"] { background: rgba(22, 163, 74, 0.16); color: #16a34a; }
.task-chat__mention-auto-kind[data-kind="task"] { background: rgba(217, 119, 6, 0.16); color: #d97706; }
.task-chat__mention-auto-kind[data-kind="user"] { background: rgba(99, 102, 241, 0.16); color: var(--color-primary); }
.task-chat__mention-auto-copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}
.task-chat__mention-auto-copy strong {
  font-size: var(--text-sm);
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.task-chat__mention-auto-copy small {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-chat__link {
  color: var(--color-primary);
  text-decoration: underline;
  text-underline-offset: 2px;
}
.task-chat__bubble.is-own .task-chat__link {
  color: var(--color-on-primary);
}

.task-chat__attachment {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  gap: var(--space-2);
  align-items: center;
  width: 100%;
  padding: 8px 10px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface-2);
  text-align: left;
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out);
}
.task-chat__attachment:hover { background: var(--color-surface-3); }
.task-chat__bubble.is-own .task-chat__attachment {
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 255, 255, 0.22);
}
.task-chat__bubble.is-own .task-chat__attachment:hover {
  background: rgba(255, 255, 255, 0.20);
}

.task-chat__attachment-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-md);
}
.task-chat__bubble.is-own .task-chat__attachment-icon {
  background: rgba(255, 255, 255, 0.22);
  color: var(--color-on-primary);
}

.task-chat__attachment-content {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.task-chat__attachment-name,
.task-chat__attachment-size {
  min-width: 0;
  overflow-wrap: anywhere;
}
.task-chat__attachment-name {
  color: var(--color-text);
  font-size: var(--text-md);
  font-weight: var(--fw-semibold);
}
.task-chat__attachment-size {
  color: var(--color-text-subtle);
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
}
.task-chat__bubble.is-own .task-chat__attachment-name,
.task-chat__bubble.is-own .task-chat__attachment-size {
  color: var(--color-on-primary);
}

.task-chat__message-actions {
  display: inline-flex;
  gap: var(--space-3);
  padding: 0 4px;
}
.task-chat__message-row.is-own .task-chat__message-actions {
  justify-content: flex-end;
}

.task-chat__link-btn,
.task-chat__pending-remove {
  border: 0;
  background: transparent;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  cursor: pointer;
  padding: 0;
}
.task-chat__link-btn:hover { color: var(--color-primary); }
.task-chat__link-btn.is-danger,
.task-chat__pending-remove { color: var(--color-danger); }
.task-chat__link-btn.is-danger:hover { color: var(--color-danger-hover); }

.task-chat__composer {
  border-top: 1px solid var(--color-border-subtle);
  padding: var(--space-3) var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  background: var(--color-surface);
}

.task-chat__mentions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.task-chat__mention-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
}
.task-chat__mention-chip button {
  border: 0;
  background: transparent;
  color: inherit;
  padding: 0;
  cursor: pointer;
}

.task-chat__file-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.task-chat__pending-file {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: var(--space-2);
  align-items: center;
  padding: 8px 12px;
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
}
.task-chat__pending-file-main {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text);
  font-size: var(--text-base);
  font-weight: var(--fw-medium);
}
.task-chat__pending-file-main span {
  min-width: 0;
  overflow-wrap: anywhere;
}
.task-chat__pending-file-meta {
  color: var(--color-text-subtle);
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
}
.task-chat__pending-file.is-uploading {
  background: var(--color-primary-soft, rgba(99, 102, 241, 0.08));
  border-color: var(--color-primary, #6366f1);
}
.task-chat__pending-file.is-uploading .task-chat__pending-file-main,
.task-chat__pending-file.is-uploading .task-chat__pending-file-meta {
  color: var(--color-primary, #6366f1);
}
.task-chat__pending-file.is-uploading .task-chat__pending-remove {
  opacity: 0.4;
  cursor: default;
}

.task-chat__composer-bar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--space-2);
  /* `end` ровняет actions по нижней грани textarea. При росте textarea
     кнопки остаются у дна — как в Telegram. */
  align-items: end;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  transition: border-color var(--dur-fast) var(--ease-out), box-shadow var(--dur-fast) var(--ease-out);
}
.task-chat__composer-bar:focus-within {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}

.task-chat__input {
  /* min-height = высота одной строки + вертикальные паддинги.
     Раньше было 24px при line-height ~1.5 — верх текста подрезался
     при descenders (буквы «р», «у»). Поднимаем до 36px, чтобы строка
     помещалась с воздухом сверху и снизу. */
  min-height: 36px;
  /* max-height устанавливается inline (`inputMaxHeight`), привязан
     к высоте `.task-chat`. CSS-дефолт оставляем как fallback. */
  max-height: 200px;
  resize: none;
  border: 0;
  outline: none;
  background: transparent;
  color: var(--color-text);
  font-family: var(--font-main);
  font-size: var(--text-md);
  line-height: var(--leading-normal);
  /* Симметричный padding — верх не клиппится. Раньше `padding: 4px 0`
     визуально съедало 2-3px сверху. */
  padding: 7px 0;
  /* Auto-grow: высота ставится JS-ом по scrollHeight. overflow-y: auto —
     включает скролл, когда уперлись в max. До этого скролла нет. */
  overflow-y: auto;
  /* Длинные одно-словные строки не должны выпинать инпут шире контейнера. */
  word-break: break-word;
  overflow-wrap: anywhere;
  /* В Chrome/Edge современных версий native-метрика делает то же
     самое без JS; держим для будущей замены autoResizeInput(). */
  field-sizing: content;
}
.task-chat__input::placeholder { color: var(--color-text-subtle); }

.task-chat__composer-actions {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.task-chat__tool-btn,
.task-chat__send-btn {
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: var(--radius-md);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}
.task-chat__tool-btn {
  background: var(--color-surface-2);
  color: var(--color-text-muted);
}
.task-chat__tool-btn:hover { background: var(--color-surface-3); color: var(--color-text); }
.task-chat__send-btn {
  background: var(--color-primary);
  color: var(--color-on-primary);
  box-shadow: var(--shadow-sm);
}
.task-chat__send-btn:hover { background: var(--color-primary-hover); }
.task-chat__send-btn:disabled { opacity: 0.55; cursor: default; }

.task-chat__mention-picker {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-md);
  padding: var(--space-2);
}

.task-chat__mention-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}

.task-chat__mention-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 220px;
  overflow-y: auto;
}

.task-chat__mention-option {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr);
  gap: var(--space-2);
  align-items: center;
  width: 100%;
  padding: 8px 10px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  cursor: pointer;
  text-align: left;
}
.task-chat__mention-option:hover { background: var(--color-surface-2); }

.task-chat__mention-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.task-chat__mention-copy strong,
.task-chat__mention-copy small {
  min-width: 0;
  overflow-wrap: anywhere;
}
.task-chat__mention-copy strong {
  color: var(--color-text);
  font-size: var(--text-base);
  font-weight: var(--fw-semibold);
}
.task-chat__mention-copy small {
  color: var(--color-text-subtle);
  font-size: var(--text-sm);
}

.task-chat__mention-empty,
.task-chat__readonly {
  color: var(--color-text-subtle);
  font-size: var(--text-base);
  text-align: center;
  padding: var(--space-3);
}

.task-chat__edit {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.task-chat__edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
}

.task-chat-confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.38);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2100;
  backdrop-filter: blur(4px);
}

.task-chat-confirm-glass {
  width: 400px;
  max-width: calc(100vw - 24px);
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-xl);
  display: flex;
  flex-direction: column;
  color: var(--color-text);
}

.task-chat-confirm-header,
.task-chat-confirm-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-4);
}
.task-chat-confirm-header { border-bottom: 1px solid var(--color-border-subtle); }
.task-chat-confirm-footer {
  justify-content: flex-end;
  border-top: 1px solid var(--color-border-subtle);
}
.task-chat-confirm-close {
  background: transparent;
  border: 0;
  color: var(--color-text-muted);
  cursor: pointer;
}
.task-chat-confirm-body { padding: var(--space-4); }

/* ----- LIGHTBOX --------------------------------------------- */
.task-chat-lightbox {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.84);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 2200;
  padding: var(--space-6);
  gap: var(--space-3);
  cursor: zoom-out;
}
.task-chat-lightbox__image {
  max-width: min(92vw, 1400px);
  max-height: 80vh;
  width: auto;
  height: auto;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-xl);
  cursor: default;
}
.task-chat-lightbox__close {
  position: absolute;
  top: var(--space-4);
  right: var(--space-4);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 0;
  background: rgba(255, 255, 255, 0.12);
  color: var(--color-text-inverse);
  cursor: pointer;
  font-size: var(--text-lg);
}
.task-chat-lightbox__close:hover { background: rgba(255, 255, 255, 0.22); }
.task-chat-lightbox__caption {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  color: var(--color-text-inverse);
  font-size: var(--text-md);
  cursor: default;
}
.task-chat-lightbox__download {
  background: rgba(255, 255, 255, 0.14);
  color: var(--color-text-inverse);
  border-color: rgba(255, 255, 255, 0.18);
}
.task-chat-lightbox__download:hover {
  background: rgba(255, 255, 255, 0.22);
}

@media (max-width: 860px) {
  .task-chat__message-row,
  .task-chat__message-row.is-own {
    grid-template-columns: 32px minmax(0, 1fr);
  }
  .task-chat__message-row.is-own .task-chat__avatar,
  .task-chat__message-row.is-own .task-chat__message-main {
    order: initial;
  }
  .task-chat__message-row.is-own .task-chat__meta,
  .task-chat__message-row.is-own .task-chat__message-actions {
    justify-content: flex-start;
  }
  .task-chat__bubble {
    max-width: 100%;
  }
  .task-chat__composer-bar {
    grid-template-columns: 1fr;
  }
  .task-chat__composer-actions {
    justify-content: flex-end;
  }
}
</style>

<!-- Phase D.3: @-mention chip — non-scoped, т.к. renderBodyHtml
     вставляет <a> через v-html и scoped CSS не матчит их (нет
     data-v атрибута на HTML, вставленном через v-html). -->
<style>
.task-chat__mention-inline {
  display: inline-block;
  padding: 0 4px;
  border-radius: 4px;
  background: rgba(99, 102, 241, 0.14);
  color: #4f46e5;
  text-decoration: none !important;
  font-weight: 600;
  white-space: nowrap;
  transition: background-color 0.15s ease;
}
.task-chat__mention-inline:hover,
.task-chat__mention-inline:focus {
  background: rgba(99, 102, 241, 0.24);
  text-decoration: none !important;
}
.task-chat__mention-inline--inert { cursor: default; opacity: 0.85; }
.task-chat__mention-inline[data-kind="deal"] { color: #16a34a; background: rgba(22, 163, 74, 0.12); }
.task-chat__mention-inline[data-kind="task"] { color: #d97706; background: rgba(217, 119, 6, 0.12); }
.task-chat__mention-inline[data-kind="user"] { color: #4f46e5; background: rgba(99, 102, 241, 0.14); }
.task-chat__mention-inline[data-kind="deal"]:hover { background: rgba(22, 163, 74, 0.20); }
.task-chat__mention-inline[data-kind="task"]:hover { background: rgba(217, 119, 6, 0.20); }
/* В own-баббле — белый текст на полупрозрачной белой подложке. */
.task-chat__bubble.is-own .task-chat__mention-inline {
  background: rgba(255, 255, 255, 0.22) !important;
  color: #ffffff !important;
}
.task-chat__bubble.is-own .task-chat__mention-inline:hover {
  background: rgba(255, 255, 255, 0.32) !important;
}
</style>
