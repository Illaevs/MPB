<template>
  <div v-if="enabled" class="global-chat">
    <!-- FAB Button -->
    <button type="button" class="global-chat__fab" @click="toggleOpen">
      <span class="global-chat__fab-icon">
        <i class="fas fa-comments"></i>
      </span>
      <transition name="badge-pop">
        <span v-if="unreadCount" class="global-chat__badge">
          {{ unreadCount > 99 ? '99+' : unreadCount }}
        </span>
      </transition>
    </button>

    <!-- Chat Panel -->
    <transition name="global-chat-pop">
      <div v-if="open" class="global-chat__panel">
        <!-- Header -->
        <div class="global-chat__header">
          <div class="global-chat__title">
            <div class="global-chat__avatar">
              <i class="fas fa-users"></i>
            </div>
            <div class="global-chat__title-text">
              <div class="global-chat__name">Общий чат</div>
              <div class="global-chat__subtitle">
                <span class="global-chat__online-dot"></span>
                {{ onlineStatus }}
              </div>
            </div>
          </div>
          <div class="global-chat__header-actions">
            <button type="button" class="global-chat__header-btn" @click="refreshMessages" :disabled="loading" title="Обновить">
              <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
            </button>
            <button type="button" class="global-chat__header-btn" @click="toggleOpen" title="Закрыть">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>

        <!-- Messages Body -->
        <div class="global-chat__body" ref="listRef">
          <div v-if="loading && !messages.length" class="global-chat__placeholder">
            <div class="global-chat__loader">
              <div class="global-chat__loader-dot"></div>
              <div class="global-chat__loader-dot"></div>
              <div class="global-chat__loader-dot"></div>
            </div>
            <span>Загрузка сообщений</span>
          </div>
          <div v-else-if="!messages.length" class="global-chat__placeholder">
            <i class="fas fa-comment-dots global-chat__placeholder-icon"></i>
            <span>Сообщений пока нет</span>
            <small>Начните общение первыми</small>
          </div>
          <div v-else class="global-chat__messages">
            <div
              v-for="message in messages"
              :key="message.id"
              class="global-chat__msg-row"
              :class="{ 'is-own': isOwn(message) }"
            >
              <div
                class="global-chat__bubble"
                :class="{
                  'is-own': isOwn(message),
                  'is-deleted': message.is_deleted
                }"
              >
                <div v-if="!isOwn(message)" class="global-chat__author">{{ message.user_name || '?' }}</div>
                <div class="global-chat__content">
                  <template v-if="message.is_deleted">
                    <span class="global-chat__deleted"><i class="fas fa-ban"></i> Сообщение удалено</span>
                  </template>
                  <template v-else>
                    <div class="global-chat__text" v-text="message.body"></div>
                    <div v-if="message.attachments?.length" class="global-chat__attachments">
                      <a
                        v-for="file in message.attachments"
                        :key="file.path || file.name"
                        href="#"
                        class="global-chat__attachment"
                        @click.prevent="downloadAttachment(file)"
                      >
                        <i class="fas fa-file-alt"></i>
                        <div class="global-chat__attachment-info">
                          <span class="global-chat__attachment-name">{{ file.name || 'файл' }}</span>
                          <span v-if="file.size" class="global-chat__attachment-size">{{ formatSize(file.size) }}</span>
                        </div>
                      </a>
                    </div>
                  </template>
                </div>
                <div class="global-chat__msg-footer">
                  <span v-if="message.edited_at" class="global-chat__edited">ред.</span>
                  <span class="global-chat__time">{{ formatDateTime(message.created_at) }}</span>
                  <i v-if="isOwn(message) && !message.is_deleted" class="fas fa-check-double global-chat__read-icon"></i>
                </div>
                <!-- Actions on hover -->
                <div v-if="canEdit(message) && !message.is_deleted" class="global-chat__msg-actions">
                  <button type="button" @click="startEdit(message)" title="Редактировать">
                    <i class="fas fa-pen"></i>
                  </button>
                  <button type="button" @click="deleteMessage(message)" title="Удалить">
                    <i class="fas fa-trash"></i>
                  </button>
                </div>
              </div>
              <!-- Inline Edit -->
              <div v-if="editingId === message.id" class="global-chat__edit" :class="{ 'is-own': isOwn(message) }">
                <textarea v-model="editingBody" class="global-chat__edit-input" rows="2" @keydown.enter.exact.prevent="saveEdit(message)"></textarea>
                <div class="global-chat__edit-actions">
                  <button type="button" class="global-chat__edit-btn save" @click="saveEdit(message)">
                    <i class="fas fa-check"></i>
                  </button>
                  <button type="button" class="global-chat__edit-btn cancel" @click="cancelEdit">
                    <i class="fas fa-times"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Composer -->
        <div class="global-chat__composer">
          <!-- Mentions chips -->
          <div v-if="selectedMentions.length" class="global-chat__mentions">
            <span v-for="mention in selectedMentions" :key="mention.id" class="global-chat__mention-chip">
              @{{ mention.name }}
              <button type="button" @click="removeMention(mention.id)">?</button>
            </span>
          </div>

          <!-- Pending files -->
          <div v-if="pendingFiles.length" class="global-chat__file-list">
            <div v-for="(file, idx) in pendingFiles" :key="file.name + idx" class="global-chat__file">
              <i class="fas fa-file"></i>
              <div class="global-chat__file-info">
                <span class="global-chat__file-name">{{ file.name }}</span>
                <span class="global-chat__file-size">{{ formatSize(file.size) }}</span>
              </div>
              <button type="button" class="global-chat__file-remove" @click="removeFile(idx)">
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>

          <!-- Mention Picker -->
          <div v-if="mentionPickerOpen" class="global-chat__mention-picker">
            <div class="global-chat__mention-search">
              <i class="fas fa-search"></i>
              <input v-model="mentionQuery" placeholder="Поиск пользователя..." />
            </div>
            <div class="global-chat__mention-list">
              <button
                v-for="user in mentionOptions"
                :key="user.id"
                type="button"
                class="global-chat__mention-option"
                @click="addMention(user)"
              >
                <div class="global-chat__mention-avatar">{{ (user.full_name || user.email || '?')[0].toUpperCase() }}</div>
                <span>{{ user.full_name || user.email || user.id }}</span>
              </button>
              <div v-if="!mentionOptions.length" class="global-chat__mention-empty">
                <i class="fas fa-user-slash"></i> Никого не нашли
              </div>
            </div>
          </div>

          <!-- Input row -->
          <div class="global-chat__input-row">
            <div class="global-chat__input-actions">
              <button type="button" class="global-chat__action-btn" @click="openFilePicker" title="Прикрепить файл">
                <i class="fas fa-paperclip"></i>
              </button>
              <button type="button" class="global-chat__action-btn" @click="toggleMentions" title="Упомянуть" :class="{ active: mentionPickerOpen }">
                <i class="fas fa-at"></i>
              </button>
            </div>
            <textarea
              v-model="draft"
              class="global-chat__input"
              rows="1"
              placeholder="Сообщение..."
              @keydown.enter.exact.prevent="sendMessage"
            ></textarea>
            <button
              type="button"
              class="global-chat__send-btn"
              :disabled="sending || (!draft.trim() && !pendingFiles.length)"
              @click="sendMessage"
            >
              <i v-if="sending" class="fas fa-spinner fa-spin"></i>
              <i v-else class="fas fa-paper-plane"></i>
            </button>
          </div>

          <input ref="fileInput" type="file" class="d-none" multiple @change="onFilesPicked" />
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import * as messengerApi from '../services/api/messenger'
import { getActiveUser, hasSectionAccess } from '../utils/permissions'
import { useToast } from '../composables/useToast'
import { downloadFromApi } from '../utils/download'
import { useUsersStore } from '../stores/users'

const LAST_SEEN_KEY = 'global_chat_last_seen'
const MAX_FILE_BYTES = 1024 * 1024 * 1024

export default {
  name: 'GlobalChatWidget',
  setup() {
    const { error: toastError } = useToast()
    const usersStore = useUsersStore()
    const activeUser = computed(() => getActiveUser())
    const enabled = computed(() => !!activeUser.value && hasSectionAccess('global_chat'))
    const open = ref(false)
    const loading = ref(false)
    const sending = ref(false)
    const messages = ref([])
    const draft = ref('')
    const pendingFiles = ref([])
    const listRef = ref(null)
    const fileInput = ref(null)
    const pollingTimer = ref(null)
    const unreadCount = ref(0)
    const lastSeenAt = ref(0)

    const mentionPickerOpen = ref(false)
    const mentionQuery = ref('')
    const selectedMentions = ref([])
    const users = ref([])
    const editingId = ref(null)
    const editingBody = ref('')

    const onlineStatus = computed(() => (pollingTimer.value ? 'онлайн' : 'оффлайн'))

    const mentionOptions = computed(() => {
      const query = (mentionQuery.value || '').trim().toLowerCase()
      const filtered = query
        ? users.value.filter((u) => (u.full_name || u.email || '').toLowerCase().includes(query))
        : users.value
      const selectedIds = new Set(selectedMentions.value.map((item) => item.id))
      return filtered.filter((u) => u && !selectedIds.has(u.id))
    })

    const isOwn = (message) => {
      const userId = activeUser.value?.id
      return userId && message.user_id === userId
    }

    const canEdit = (message) => {
      if (!message || message.is_deleted) return false
      const userId = activeUser.value?.id
      if (activeUser.value?.is_superuser) return true
      return userId && message.user_id === userId
    }

    const formatDateTime = (value) => {
      if (!value) return ''
      try {
        return new Date(value).toLocaleString('ru-RU', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: 'short' })
      } catch (e) {
        return value
      }
    }

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

    const loadLastSeen = () => {
      try {
        const stored = localStorage.getItem(LAST_SEEN_KEY)
        lastSeenAt.value = stored ? Number(stored) : 0
      } catch {
        lastSeenAt.value = 0
      }
    }

    const saveLastSeen = (timestamp) => {
      lastSeenAt.value = timestamp
      try {
        localStorage.setItem(LAST_SEEN_KEY, String(timestamp))
      } catch {
        // ignore
      }
    }

    const updateUnreadCount = (items) => {
      const last = lastSeenAt.value || 0
      const userId = activeUser.value?.id
      const unread = items.filter((msg) => {
        const ts = msg?.created_at ? new Date(msg.created_at).getTime() : 0
        if (!ts || ts <= last) return false
        if (userId && msg.user_id === userId) return false
        return true
      })
      unreadCount.value = unread.length
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

    const loadUsers = async () => {
      try {
        await usersStore.ensureLoaded()
        users.value = usersStore.items
      } catch (e) {
        users.value = []
      }
    }

    const loadMessages = async ({ silent = false } = {}) => {
      if (!enabled.value) return
      if (!silent) loading.value = true
      try {
        const result = await messengerApi.listGlobalMessages()
        const nextItems = result || []
        if (shouldUpdateMessages(nextItems, messages.value)) {
          const hadNew = nextItems.length > messages.value.length
          messages.value = nextItems
          if (open.value && hadNew) {
            await scrollToBottom()
          }
        }
        updateUnreadCount(nextItems)
        if (open.value && nextItems.length) {
          const last = new Date(nextItems[nextItems.length - 1].created_at || Date.now()).getTime()
          saveLastSeen(last)
          unreadCount.value = 0
        }
      } catch (e) {
        if (!silent) {
          toastError('Ошибка загрузки сообщений')
        }
      } finally {
        if (!silent) loading.value = false
      }
    }

    const refreshMessages = () => {
      if (loading.value) return
      return loadMessages()
    }

    const startPolling = () => {
      if (pollingTimer.value || !enabled.value) return
      pollingTimer.value = setInterval(() => loadMessages({ silent: true }), 8000)
    }

    const stopPolling = () => {
      if (pollingTimer.value) {
        clearInterval(pollingTimer.value)
        pollingTimer.value = null
      }
    }

    const toggleOpen = () => {
      open.value = !open.value
      if (open.value) {
        loadMessages()
        if (messages.value.length) {
          const last = new Date(messages.value[messages.value.length - 1].created_at || Date.now()).getTime()
          saveLastSeen(last)
          unreadCount.value = 0
        }
        scrollToBottom()
      }
    }

    const openFilePicker = () => {
      if (!fileInput.value) return
      fileInput.value.click()
    }

    const onFilesPicked = (event) => {
      const files = Array.from(event.target.files || [])
      if (!files.length) return
      const oversized = files.find((file) => file.size > MAX_FILE_BYTES)
      if (oversized) {
        toastError('Файл превышает лимит 1 ГБ')
        event.target.value = ''
        return
      }
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
      selectedMentions.value.push({
        id: user.id,
        name: user.full_name || user.email || user.id
      })
      draft.value = `${draft.value.trim()} @${user.full_name || user.email || ''} `.trim() + ' '
    }

    const removeMention = (userId) => {
      selectedMentions.value = selectedMentions.value.filter((item) => item.id !== userId)
    }

    const sendMessage = async () => {
      if (sending.value) return
      const text = (draft.value || '').trim()
      if (!text && !pendingFiles.value.length) return
      sending.value = true
      try {
        const form = new FormData()
        if (text) form.append('body', text)
        if (selectedMentions.value.length) {
          form.append('mentions', JSON.stringify(selectedMentions.value.map((item) => item.id)))
        }
        pendingFiles.value.forEach((file) => form.append('files', file, file.name))
        const result = await messengerApi.sendGlobalMessage(form)
        if (result) {
          messages.value = [...messages.value, result]
        }
        draft.value = ''
        pendingFiles.value = []
        selectedMentions.value = []
        await scrollToBottom()
        if (messages.value.length) {
          const last = new Date(messages.value[messages.value.length - 1].created_at || Date.now()).getTime()
          saveLastSeen(last)
          unreadCount.value = 0
        }
      } catch (e) {
        toastError('Ошибка загрузки сообщений')
      } finally {
        sending.value = false
      }
    }

    const downloadAttachment = async (file) => {
      try {
        const url = file?.download_url
        if (!url) return
        await downloadFromApi(url, {}, file?.name || 'file', { module: 'global_chat' })
      } catch (e) {
        toastError('Ошибка отправки сообщения')
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
        const result = await messengerApi.updateMessage(message.id, {
          body: editingBody.value.trim()
        })
        messages.value = messages.value.map((item) => (item.id === message.id ? result : item))
        cancelEdit()
      } catch (e) {
        toastError('Ошибка при обновлении')
      }
    }

    const deleteMessage = async (message) => {
      if (!message) return
      try {
        await messengerApi.deleteMessage(message.id)
        messages.value = messages.value.map((item) =>
          item.id === message.id ? { ...item, is_deleted: true, body: null } : item
        )
      } catch (e) {
        toastError('Ошибка загрузки сообщений')
      }
    }

    watch(open, (value) => {
      if (value) {
        loadMessages()
      }
    })

    onMounted(async () => {
      loadLastSeen()
      if (enabled.value) {
        await loadUsers()
        await loadMessages({ silent: true })
        startPolling()
      }
    })

    onBeforeUnmount(() => {
      stopPolling()
    })

    return {
      enabled,
      open,
      loading,
      sending,
      messages,
      draft,
      pendingFiles,
      listRef,
      fileInput,
      unreadCount,
      mentionPickerOpen,
      mentionQuery,
      mentionOptions,
      selectedMentions,
      editingId,
      editingBody,
      onlineStatus,
      toggleOpen,
      refreshMessages,
      isOwn,
      canEdit,
      formatDateTime,
      formatSize,
      openFilePicker,
      onFilesPicked,
      removeFile,
      toggleMentions,
      addMention,
      removeMention,
      sendMessage,
      downloadAttachment,
      startEdit,
      cancelEdit,
      saveEdit,
      deleteMessage
    }
  }
}
</script>

<style scoped>
/* ===================================================
   GLOBAL CHAT � Telegram Liquid Glass Edition
   =================================================== */

.global-chat {
  position: fixed;
  right: 22px;
  bottom: 140px;
  z-index: 2100;
  font-family: var(--font-main, 'Inter', -apple-system, BlinkMacSystemFont, sans-serif);
}

/* --- FAB Button --- */
.global-chat__fab {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(145deg, var(--chat-accent), var(--chat-active-bg));
  color: var(--chat-unread-fg);
  box-shadow:
    0 4px 16px rgba(64, 167, 227, 0.35),
    0 8px 32px rgba(64, 167, 227, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.global-chat__fab:hover {
  transform: scale(1.08);
  box-shadow:
    0 6px 24px rgba(64, 167, 227, 0.45),
    0 12px 40px rgba(64, 167, 227, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.25);
}

.global-chat__fab:active {
  transform: scale(0.95);
}

.global-chat__fab-icon {
  font-size: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.global-chat__badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: var(--color-danger, #ff3b30);
  color: var(--chat-unread-fg);
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  min-width: 20px;
  text-align: center;
  border-radius: 999px;
  border: 2.5px solid var(--color-bg);
  line-height: 1.4;
  box-shadow: 0 2px 8px rgba(255, 59, 48, 0.4);
}

.badge-pop-enter-active { transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
.badge-pop-leave-active { transition: all 0.2s ease; }
.badge-pop-enter-from { transform: scale(0); opacity: 0; }
.badge-pop-leave-to { transform: scale(0); opacity: 0; }

/* --- Panel --- */
.global-chat__panel {
  width: 400px;
  max-width: calc(100vw - 40px);
  height: 560px;
  position: absolute;
  right: 0;
  bottom: 72px;
  background: rgba(255, 255, 255, 0.65);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  box-shadow:
    0 24px 80px -12px rgba(0, 0, 0, 0.18),
    0 8px 24px -4px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.6),
    inset 0 -1px 0 rgba(255, 255, 255, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

:root[data-theme="dark"] .global-chat__panel {
  background: rgba(30, 30, 32, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow:
    0 24px 80px -12px rgba(0, 0, 0, 0.5),
    0 8px 24px -4px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

/* --- Header --- */
.global-chat__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
}

:root[data-theme="dark"] .global-chat__header {
  background: rgba(40, 40, 42, 0.4);
  border-bottom-color: rgba(255, 255, 255, 0.06);
}

.global-chat__title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.global-chat__avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(145deg, var(--chat-accent), var(--chat-active-bg));
  color: var(--chat-unread-fg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  box-shadow: 0 2px 8px rgba(64, 167, 227, 0.25);
}

.global-chat__title-text {
  display: flex;
  flex-direction: column;
}

.global-chat__name {
  font-weight: 700;
  font-size: 15px;
  color: var(--md-sys-color-on-surface);
  line-height: 1.2;
}

.global-chat__subtitle {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  display: flex;
  align-items: center;
  gap: 5px;
}

.global-chat__online-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #34c759;
  box-shadow: 0 0 6px rgba(52, 199, 89, 0.5);
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.global-chat__header-actions {
  display: flex;
  gap: 4px;
}

.global-chat__header-btn {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.04);
  color: var(--md-sys-color-on-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s;
  font-size: 14px;
}

.global-chat__header-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  color: var(--md-sys-color-on-surface);
}

:root[data-theme="dark"] .global-chat__header-btn {
  background: rgba(255, 255, 255, 0.06);
}

:root[data-theme="dark"] .global-chat__header-btn:hover {
  background: rgba(255, 255, 255, 0.12);
}

/* --- Body --- */
.global-chat__body {
  flex: 1;
  overflow-y: auto;
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  background: transparent;
  min-height: 0;
}

.global-chat__body::-webkit-scrollbar { width: 4px; }
.global-chat__body::-webkit-scrollbar-thumb { background: rgba(0, 0, 0, 0.12); border-radius: 4px; }
.global-chat__body::-webkit-scrollbar-track { background: transparent; }

/* --- Placeholder --- */
.global-chat__placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex: 1;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 14px;
}

.global-chat__placeholder small {
  font-size: 12px;
  opacity: 0.6;
}

.global-chat__placeholder-icon {
  font-size: 36px;
  opacity: 0.25;
  margin-bottom: 4px;
}

/* --- Loader --- */
.global-chat__loader {
  display: flex;
  gap: 6px;
  margin-bottom: 6px;
}

.global-chat__loader-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--chat-accent);
  animation: loader-bounce 1.4s ease-in-out infinite both;
}

.global-chat__loader-dot:nth-child(1) { animation-delay: -0.32s; }
.global-chat__loader-dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes loader-bounce {
  0%, 80%, 100% { transform: scale(0.5); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* --- Messages --- */
.global-chat__messages {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 4px 0;
}

/* --- Message Row --- */
.global-chat__msg-row {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  max-width: 85%;
  position: relative;
}

.global-chat__msg-row.is-own {
  align-items: flex-end;
  align-self: flex-end;
}

/* --- Bubble --- */
.global-chat__bubble {
  position: relative;
  padding: 8px 12px 4px;
  border-radius: 16px 16px 16px 4px;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  transition: box-shadow 0.15s ease;
  max-width: 100%;
}

.global-chat__bubble:hover {
  box-shadow:
    0 2px 8px rgba(0, 0, 0, 0.07),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
}

:root[data-theme="dark"] .global-chat__bubble {
  background: rgba(44, 44, 46, 0.7);
  border-color: rgba(255, 255, 255, 0.06);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}

/* Own bubble — TG mint on light, blue on dark (via token) */
.global-chat__bubble.is-own {
  background: var(--chat-bubble-out);
  border: none;
  border-radius: var(--chat-radius-large) var(--chat-radius-large) var(--chat-radius-small) var(--chat-radius-large);
  color: var(--chat-bubble-out-fg);
  box-shadow: var(--chat-bubble-shadow-out);
}

.global-chat__bubble.is-own:hover {
  box-shadow: var(--chat-bubble-shadow-out);
}

.global-chat__bubble.is-deleted {
  opacity: 0.5;
}

/* --- Author --- */
.global-chat__author {
  font-size: 12px;
  font-weight: 700;
  color: var(--chat-accent);
  margin-bottom: 2px;
  line-height: 1.2;
}

/* --- Text --- */
.global-chat__text {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 14px;
  line-height: 1.45;
}

/* --- Deleted --- */
.global-chat__deleted {
  font-style: italic;
  font-size: 13px;
  opacity: 0.7;
}

.global-chat__deleted i {
  margin-right: 4px;
  font-size: 11px;
}

/* --- Message Footer --- */
.global-chat__msg-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  margin-top: 2px;
}

.global-chat__time {
  font-size: 11px;
  opacity: 0.55;
  line-height: 1;
}

.global-chat__bubble.is-own .global-chat__time {
  opacity: 0.7;
  color: rgba(255, 255, 255, 0.85);
}

.global-chat__edited {
  font-size: 10px;
  opacity: 0.45;
  font-style: italic;
}

.global-chat__read-icon {
  font-size: 12px;
  opacity: 0.7;
  color: rgba(255, 255, 255, 0.85);
}

/* --- Hover Actions --- */
.global-chat__msg-actions {
  position: absolute;
  top: 4px;
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.15s;
  z-index: 2;
}

.global-chat__bubble:not(.is-own) .global-chat__msg-actions {
  right: -60px;
}

.global-chat__bubble.is-own .global-chat__msg-actions {
  left: -60px;
}

.global-chat__msg-row:hover .global-chat__msg-actions {
  opacity: 1;
}

.global-chat__msg-actions button {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.05);
  backdrop-filter: blur(10px);
  color: var(--md-sys-color-on-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 11px;
  transition: all 0.15s;
}

.global-chat__msg-actions button:hover {
  background: rgba(0, 0, 0, 0.1);
  color: var(--md-sys-color-on-surface);
}

:root[data-theme="dark"] .global-chat__msg-actions button {
  background: rgba(255, 255, 255, 0.08);
}

:root[data-theme="dark"] .global-chat__msg-actions button:hover {
  background: rgba(255, 255, 255, 0.15);
}

/* --- Attachments --- */
.global-chat__attachments {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 6px;
}

.global-chat__attachment {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.04);
  text-decoration: none;
  color: inherit;
  transition: background 0.15s;
}

.global-chat__bubble.is-own .global-chat__attachment {
  background: rgba(255, 255, 255, 0.15);
}

.global-chat__attachment:hover {
  background: rgba(0, 0, 0, 0.08);
}

.global-chat__bubble.is-own .global-chat__attachment:hover {
  background: rgba(255, 255, 255, 0.25);
}

.global-chat__attachment i {
  font-size: 18px;
  opacity: 0.7;
  flex-shrink: 0;
}

.global-chat__attachment-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.global-chat__attachment-name {
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.global-chat__attachment-size {
  font-size: 11px;
  opacity: 0.55;
}

/* --- Edit Inline --- */
.global-chat__edit {
  margin-top: 6px;
  display: flex;
  gap: 6px;
  align-items: flex-end;
  max-width: 100%;
}

.global-chat__edit.is-own {
  justify-content: flex-end;
}

.global-chat__edit-input {
  flex: 1;
  resize: none;
  padding: 8px 12px;
  border-radius: 14px;
  border: 1px solid rgba(64, 167, 227, 0.25);
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  font-size: 14px;
  font-family: inherit;
  color: var(--md-sys-color-on-surface);
  outline: none;
  transition: border-color 0.15s;
}

.global-chat__edit-input:focus {
  border-color: var(--chat-accent);
  box-shadow: 0 0 0 3px rgba(64, 167, 227, 0.12);
}

:root[data-theme="dark"] .global-chat__edit-input {
  background: rgba(44, 44, 46, 0.7);
  border-color: rgba(255, 255, 255, 0.1);
}

.global-chat__edit-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.global-chat__edit-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.15s;
}

.global-chat__edit-btn.save {
  background: var(--chat-accent);
  color: var(--chat-unread-fg);
}

.global-chat__edit-btn.save:hover {
  background: var(--chat-active-bg);
}

.global-chat__edit-btn.cancel {
  background: rgba(0, 0, 0, 0.06);
  color: var(--md-sys-color-on-surface-variant);
}

.global-chat__edit-btn.cancel:hover {
  background: rgba(0, 0, 0, 0.1);
}

/* --- Composer --- */
.global-chat__composer {
  padding: 8px 12px 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.04);
  background: rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(20px);
  flex-shrink: 0;
}

:root[data-theme="dark"] .global-chat__composer {
  background: rgba(30, 30, 32, 0.35);
  border-top-color: rgba(255, 255, 255, 0.04);
}

/* --- Mentions Chips --- */
.global-chat__mentions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 6px;
}

.global-chat__mention-chip {
  background: rgba(64, 167, 227, 0.12);
  color: var(--chat-accent);
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 12px;
  font-weight: 500;
  display: inline-flex;
  gap: 4px;
  align-items: center;
}

:root[data-theme="dark"] .global-chat__mention-chip {
  background: rgba(46, 166, 255, 0.2);
}

.global-chat__mention-chip button {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  color: inherit;
  opacity: 0.6;
}

.global-chat__mention-chip button:hover {
  opacity: 1;
}

/* --- File list --- */
.global-chat__file-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}

.global-chat__file {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 10px;
  background: rgba(64, 167, 227, 0.06);
  border: 1px solid rgba(64, 167, 227, 0.1);
}

.global-chat__file i {
  color: var(--chat-accent);
  font-size: 14px;
  flex-shrink: 0;
}

.global-chat__file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.global-chat__file-name {
  font-size: 12px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.global-chat__file-size {
  font-size: 10px;
  color: var(--md-sys-color-on-surface-variant);
}

.global-chat__file-remove {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 59, 48, 0.08);
  color: var(--color-danger, #ff3b30);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 10px;
  flex-shrink: 0;
  transition: background 0.15s;
}

.global-chat__file-remove:hover {
  background: rgba(255, 59, 48, 0.15);
}

/* --- Mention Picker --- */
.global-chat__mention-picker {
  margin-bottom: 8px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 14px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}

:root[data-theme="dark"] .global-chat__mention-picker {
  background: rgba(44, 44, 46, 0.7);
  border-color: rgba(255, 255, 255, 0.06);
}

.global-chat__mention-search {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 10px;
  margin-bottom: 6px;
}

.global-chat__mention-search i {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  flex-shrink: 0;
}

.global-chat__mention-search input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 13px;
  font-family: inherit;
  color: var(--md-sys-color-on-surface);
  outline: none;
}

.global-chat__mention-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: 140px;
  overflow-y: auto;
}

.global-chat__mention-option {
  display: flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  border: none;
  text-align: left;
  padding: 6px 8px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  color: var(--md-sys-color-on-surface);
  transition: background 0.12s;
}

.global-chat__mention-option:hover {
  background: rgba(64, 167, 227, 0.08);
}

.global-chat__mention-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(145deg, var(--chat-accent), var(--chat-active-bg));
  color: var(--chat-unread-fg);
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.global-chat__mention-empty {
  text-align: center;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  padding: 8px;
}

.global-chat__mention-empty i {
  margin-right: 4px;
}

/* --- Input Row --- */
.global-chat__input-row {
  display: flex;
  align-items: flex-end;
  gap: 6px;
}

.global-chat__input-actions {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
  padding-bottom: 4px;
}

.global-chat__action-btn {
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.15s;
}

.global-chat__action-btn:hover,
.global-chat__action-btn.active {
  color: var(--chat-accent);
  background: rgba(64, 167, 227, 0.08);
}

.global-chat__input {
  flex: 1;
  resize: none;
  padding: 9px 14px;
  border-radius: 20px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(8px);
  font-size: 14px;
  font-family: inherit;
  color: var(--md-sys-color-on-surface);
  outline: none;
  line-height: 1.4;
  max-height: 100px;
  overflow-y: auto;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.global-chat__input:focus {
  border-color: rgba(64, 167, 227, 0.3);
  box-shadow: 0 0 0 3px rgba(64, 167, 227, 0.08);
}

:root[data-theme="dark"] .global-chat__input {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.08);
}

:root[data-theme="dark"] .global-chat__input:focus {
  border-color: rgba(46, 166, 255, 0.4);
}

.global-chat__input::placeholder {
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.6;
}

/* --- Send Button --- */
.global-chat__send-btn {
  width: 38px;
  height: 38px;
  border: none;
  border-radius: 50%;
  background: linear-gradient(145deg, var(--chat-accent), var(--chat-active-bg));
  color: var(--chat-unread-fg);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
  flex-shrink: 0;
  transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
  box-shadow: 0 2px 8px rgba(64, 167, 227, 0.25);
}

.global-chat__send-btn:hover:not(:disabled) {
  transform: scale(1.08);
  box-shadow: 0 4px 12px rgba(64, 167, 227, 0.35);
}

.global-chat__send-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.global-chat__send-btn:disabled {
  background: rgba(0, 0, 0, 0.06);
  color: var(--md-sys-color-on-surface-variant);
  box-shadow: none;
  cursor: default;
}

:root[data-theme="dark"] .global-chat__send-btn:disabled {
  background: rgba(255, 255, 255, 0.06);
}

/* --- Transitions --- */
.global-chat-pop-enter-active {
  transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1);
}

.global-chat-pop-leave-active {
  transition: all 0.18s ease-in;
}

.global-chat-pop-enter-from {
  opacity: 0;
  transform: translateY(12px) scale(0.96);
}

.global-chat-pop-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.98);
}

/* --- Mobile --- */
@media (max-width: 768px) {
  .global-chat {
    right: 14px;
    bottom: 24px;
  }

  .global-chat__panel {
    width: calc(100vw - 24px);
    height: 75vh;
    right: -10px;
    bottom: 70px;
    border-radius: 18px;
  }

  .global-chat__msg-actions {
    position: static;
    opacity: 1;
    margin-top: 4px;
  }

  .global-chat__bubble:not(.is-own) .global-chat__msg-actions,
  .global-chat__bubble.is-own .global-chat__msg-actions {
    left: auto;
    right: auto;
  }
}
</style>
