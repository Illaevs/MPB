<template>
  <teleport to="body">
    <transition name="cc-overlay">
      <div v-if="visible" class="cc-overlay" v-modal-close="close">
        <transition name="cc-panel">
          <div v-if="visible" class="cc-panel">
            <div class="cc-header">
              <div class="cc-header__left">
                <div class="cc-header__icon">
                  <i class="fas fa-comments"></i>
                </div>
                <div>
                  <h2 class="cc-header__title">Чаты</h2>
                  <p class="cc-header__subtitle">
                    {{ unreadCount }} непрочитанных, {{ conversations.length }} всего
                  </p>
                </div>
              </div>
              <div class="cc-header__right">
                <button class="cc-btn cc-btn--secondary" @click="openMessenger">
                  <i class="fas fa-up-right-from-square"></i>
                  <span>Мессенджер</span>
                </button>
                <button class="cc-btn cc-btn--icon" :disabled="loading" @click="refresh">
                  <i class="fas fa-sync" :class="{ 'fa-spin': loading }"></i>
                </button>
                <button class="cc-btn cc-btn--icon" @click="close">
                  <i class="fas fa-times"></i>
                </button>
              </div>
            </div>

            <div class="cc-toolbar">
              <div class="cc-tabs">
                <button
                  v-for="tab in tabs"
                  :key="tab.value"
                  class="cc-tab"
                  :class="{ active: activeTab === tab.value }"
                  @click="activeTab = tab.value"
                >
                  {{ tab.label }}
                  <span v-if="tab.count > 0" class="cc-tab__count">{{ tab.count }}</span>
                </button>
              </div>
              <label class="cc-search-wrap">
                <i class="fas fa-search cc-search-icon"></i>
                <input v-model="searchQuery" class="cc-search" type="text" placeholder="Поиск по чатам..." >
              </label>
            </div>

            <div class="cc-feed">
              <div v-if="loading && !conversations.length" class="cc-feed__loading">
                <div v-for="index in 6" :key="index" class="cc-skeleton"></div>
              </div>

              <div v-else-if="!filteredConversations.length" class="cc-empty">
                <div class="cc-empty__icon">
                  <i class="fas fa-comment-slash"></i>
                </div>
                <div class="cc-empty__title">Чаты не найдены</div>
                <div class="cc-empty__hint">Проверьте фильтр или откройте полный мессенджер</div>
              </div>

              <div v-else class="cc-card-list">
                <button
                  v-for="conversation in filteredConversations"
                  :key="conversation.id"
                  type="button"
                  class="cc-card"
                  :class="{ 'cc-card--unread': isConversationUnread(conversation) }"
                  @click="openConversation(conversation)"
                >
                  <span class="cc-card__icon" :class="conversationIconClass(conversation.type)">
                    <i :class="conversationIcon(conversation.type)"></i>
                  </span>

                  <span class="cc-card__body">
                    <span class="cc-card__topline">
                      <strong class="cc-card__title">{{ conversation.title || 'Чат' }}</strong>
                      <span class="cc-card__time">{{ formatConversationTime(conversation.last_message?.created_at || conversation.updated_at || conversation.created_at) }}</span>
                    </span>

                    <span class="cc-card__meta">
                      <span class="cc-card__type">{{ conversationTypeLabel(conversation.type) }}</span>
                      <span v-if="conversation.member_count" class="cc-card__members">{{ formatMembersCount(conversation.member_count) }}</span>
                    </span>

                    <span class="cc-card__preview">{{ conversationPreview(conversation) }}</span>
                  </span>

                  <span v-if="isConversationUnread(conversation)" class="cc-card__badge">новое</span>
                </button>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </transition>
  </teleport>
</template>

<script>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as messengerApi from '../../services/api/messenger'
import { getActiveUser } from '../../utils/permissions'
import { formatDateTime } from '../../utils/format'

const LAST_SEEN_KEY_PREFIX = 'messenger_last_seen_'

export default {
  name: 'ChatCenter',
  props: {
    modelValue: { type: Boolean, default: false }
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const router = useRouter()
    const visible = computed({
      get: () => props.modelValue,
      set: (value) => emit('update:modelValue', value)
    })
    const conversations = ref([])
    const loading = ref(false)
    const activeTab = ref('all')
    const searchQuery = ref('')
    const activeUser = computed(() => getActiveUser())

    const getLastSeenAt = (conversationId) => {
      if (!conversationId) return 0
      try {
        return Number(localStorage.getItem(`${LAST_SEEN_KEY_PREFIX}${conversationId}`) || 0)
      } catch (error) {
        return 0
      }
    }

    const isConversationUnread = (conversation) => {
      if (!conversation?.last_message?.created_at) return false
      if (String(conversation.last_message.user_id || '') === String(activeUser.value?.id || '')) return false
      return new Date(conversation.last_message.created_at).getTime() > getLastSeenAt(conversation.id)
    }

    const sortedConversations = computed(() =>
      [...conversations.value].sort((left, right) => getConversationTimestamp(right) - getConversationTimestamp(left))
    )

    const unreadCount = computed(() => sortedConversations.value.filter((item) => isConversationUnread(item)).length)

    const tabs = computed(() => [
      { label: 'Все', value: 'all', count: conversations.value.length },
      { label: 'Личные', value: 'direct', count: conversations.value.filter((item) => item.type === 'direct').length },
      { label: 'Группы', value: 'group', count: conversations.value.filter((item) => item.type !== 'direct').length }
    ])

    const filteredConversations = computed(() => {
      let list = sortedConversations.value
      if (activeTab.value === 'direct') {
        list = list.filter((item) => item.type === 'direct')
      } else if (activeTab.value === 'group') {
        list = list.filter((item) => item.type !== 'direct')
      }

      const query = searchQuery.value.trim().toLowerCase()
      if (!query) return list

      return list.filter((item) => {
        const haystack = [
          item.title || '',
          item.description || '',
          item.last_message?.body || '',
          conversationTypeLabel(item.type)
        ].join(' ').toLowerCase()
        return haystack.includes(query)
      })
    })

    const loadConversations = async () => {
      loading.value = true
      try {
        const result = await messengerApi.list()
        conversations.value = result || []
      } catch (error) {
        console.error('Error loading chat center conversations:', error)
        conversations.value = []
      } finally {
        loading.value = false
      }
    }

    const close = () => {
      visible.value = false
    }

    const openMessenger = async () => {
      close()
      await router.push({ name: 'Messenger' })
    }

    const openConversation = async (conversation) => {
      if (!conversation?.id) return
      close()
      await router.push({
        name: 'Messenger',
        query: {
          conversation: String(conversation.id)
        }
      })
    }

    const refresh = () => loadConversations()

    watch(visible, (value) => {
      if (value) {
        document.body.style.overflow = 'hidden'
        loadConversations()
      } else {
        document.body.style.overflow = ''
      }
    })

    const handleKeydown = (event) => {
      if (event.key === 'Escape' && visible.value) close()
    }

    if (typeof window !== 'undefined') {
      window.addEventListener('keydown', handleKeydown)
    }

    onBeforeUnmount(() => {
      document.body.style.overflow = ''
      if (typeof window !== 'undefined') {
        window.removeEventListener('keydown', handleKeydown)
      }
    })

    return {
      visible,
      conversations,
      loading,
      activeTab,
      searchQuery,
      unreadCount,
      tabs,
      filteredConversations,
      isConversationUnread,
      conversationIcon,
      conversationIconClass,
      conversationPreview,
      conversationTypeLabel,
      formatConversationTime,
      formatMembersCount,
      close,
      openMessenger,
      openConversation,
      refresh
    }
  }
}

function getConversationTimestamp(conversation) {
  const value = conversation?.last_message?.created_at || conversation?.updated_at || conversation?.created_at || 0
  const timestamp = new Date(value).getTime()
  return Number.isFinite(timestamp) ? timestamp : 0
}

function conversationIcon(type) {
  if (type === 'global') return 'fas fa-globe'
  if (type === 'channel') return 'fas fa-bullhorn'
  if (type === 'direct') return 'fas fa-user'
  return 'fas fa-users'
}

function conversationIconClass(type) {
  if (type === 'global') return 'cc-card__icon--global'
  if (type === 'channel') return 'cc-card__icon--channel'
  if (type === 'direct') return 'cc-card__icon--direct'
  return 'cc-card__icon--group'
}

function conversationTypeLabel(type) {
  if (type === 'global') return 'Глобальный чат'
  if (type === 'direct') return 'Личный чат'
  if (type === 'channel') return 'Канал'
  if (type === 'group') return 'Группа'
  return 'Чат'
}

function conversationPreview(conversation) {
  const body = String(conversation?.last_message?.body || '').trim()
  if (body) return body
  const attachments = Number(conversation?.last_message?.attachments?.length || 0)
  if (attachments > 0) {
    return attachments === 1 ? '1 вложение' : `${attachments} вложения`
  }
  return 'Сообщений пока нет'
}

function formatConversationTime(value) {
  if (!value) return ''
  try {
    return formatDateTime(value, {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (error) {
    return value
  }
}

function formatMembersCount(count) {
  const value = Number(count || 0)
  if (!value) return ''
  const mod10 = value % 10
  const mod100 = value % 100
  if (mod10 === 1 && mod100 !== 11) return `${value} участник`
  if ([2, 3, 4].includes(mod10) && ![12, 13, 14].includes(mod100)) return `${value} участника`
  return `${value} участников`
}
</script>

<style scoped>
.cc-overlay {
  position: fixed;
  inset: 0;
  z-index: 2050;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(11, 18, 32, 0.32);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.cc-overlay-enter-active { animation: cc-fade-in 0.2s ease; }
.cc-overlay-leave-active { animation: cc-fade-in 0.2s ease reverse; }
@keyframes cc-fade-in { from { opacity: 0; } to { opacity: 1; } }

.cc-panel {
  width: min(980px, calc(100vw - 40px));
  height: min(82vh, 760px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.45);
  background: rgba(255, 255, 255, 0.70);
  box-shadow: 0 36px 72px rgba(15, 23, 42, 0.26);
  backdrop-filter: blur(28px) saturate(180%);
  -webkit-backdrop-filter: blur(28px) saturate(180%);
}

:root[data-theme="dark"] .cc-panel {
  background: rgba(18, 21, 29, 0.72);
  border-color: rgba(255, 255, 255, 0.12);
}

.cc-panel-enter-active { animation: cc-pop-in 0.24s cubic-bezier(0.16, 1, 0.3, 1); }
.cc-panel-leave-active { animation: cc-pop-in 0.18s ease reverse; }
@keyframes cc-pop-in {
  from { opacity: 0; transform: translateY(14px) scale(0.97); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.cc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 22px 24px 16px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
}

:root[data-theme="dark"] .cc-header,
:root[data-theme="dark"] .cc-toolbar {
  border-color: rgba(255, 255, 255, 0.08);
}

.cc-header__left,
.cc-header__right,
.cc-tabs,
.cc-card,
.cc-card__topline,
.cc-card__meta,
.cc-search-wrap,
.cc-btn {
  display: flex;
  align-items: center;
}

.cc-header__left {
  gap: 14px;
}

.cc-header__right {
  gap: 8px;
}

.cc-header__icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  color: var(--color-text-inverse);
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-active));
  font-size: 1.1rem;
}

.cc-header__title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--md-sys-color-on-surface);
}

.cc-header__subtitle {
  margin: 3px 0 0;
  font-size: 0.82rem;
  color: var(--md-sys-color-on-surface-variant);
}

.cc-btn {
  gap: 6px;
  border: none;
  cursor: pointer;
  font: inherit;
  transition: background 0.16s ease, transform 0.16s ease, opacity 0.16s ease;
}

.cc-btn:disabled {
  cursor: default;
  opacity: 0.65;
}

.cc-btn--secondary {
  padding: 9px 14px;
  border-radius: 11px;
  background: rgba(15, 23, 42, 0.06);
  color: var(--md-sys-color-on-surface);
}

.cc-btn--secondary:hover:not(:disabled),
.cc-btn--icon:hover:not(:disabled) {
  background: rgba(15, 23, 42, 0.10);
}

:root[data-theme="dark"] .cc-btn--secondary,
:root[data-theme="dark"] .cc-btn--icon {
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-text-inverse);
}

.cc-btn--icon {
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 11px;
  background: rgba(15, 23, 42, 0.05);
  color: var(--md-sys-color-on-surface-variant);
}

.cc-toolbar {
  display: grid;
  grid-template-columns: 1fr minmax(240px, 320px);
  gap: 16px;
  padding: 14px 24px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
}

.cc-tabs {
  gap: 10px;
  flex-wrap: wrap;
}

.cc-tab {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 14px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.56);
  color: var(--md-sys-color-on-surface);
  cursor: pointer;
  font: inherit;
  transition: background 0.16s ease, color 0.16s ease, border-color 0.16s ease;
}

.cc-tab.active {
  color: var(--color-text-inverse);
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-active));
  border-color: transparent;
}

.cc-tab__count {
  min-width: 20px;
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.22);
  font-size: 0.74rem;
  line-height: 1.5;
}

.cc-search-wrap {
  position: relative;
  gap: 8px;
  padding: 0 14px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.56);
}

.cc-search-icon {
  color: var(--md-sys-color-on-surface-variant);
}

.cc-search {
  width: 100%;
  height: 42px;
  border: none;
  background: transparent;
  color: var(--md-sys-color-on-surface);
  font: inherit;
  outline: none;
}

.cc-feed {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 18px 24px 24px;
}

.cc-feed__loading {
  display: grid;
  gap: 12px;
}

.cc-skeleton {
  height: 86px;
  border-radius: 18px;
  background: linear-gradient(90deg, rgba(148, 163, 184, 0.18), rgba(226, 232, 240, 0.46), rgba(148, 163, 184, 0.18));
  background-size: 200% 100%;
  animation: cc-skeleton 1.2s linear infinite;
}

@keyframes cc-skeleton {
  from { background-position: 200% 0; }
  to { background-position: -200% 0; }
}

.cc-empty {
  height: 100%;
  min-height: 280px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: var(--md-sys-color-on-surface-variant);
  text-align: center;
}

.cc-empty__icon {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 1.4rem;
}

.cc-empty__title {
  font-weight: 700;
  color: var(--md-sys-color-on-surface);
}

.cc-card-list {
  display: grid;
  gap: 14px;
}

.cc-card {
  width: 100%;
  gap: 14px;
  padding: 16px 18px;
  text-align: left;
  border: 1px solid rgba(37, 99, 235, 0.08);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.64);
  color: inherit;
  cursor: pointer;
  transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
}

.cc-card:hover {
  transform: translateY(-1px);
  border-color: var(--color-primary-soft-strong);
  box-shadow: var(--shadow-md);
}

.cc-card--unread {
  border-color: var(--color-primary-soft-strong);
  box-shadow: inset 0 0 0 1px var(--color-primary-soft-strong);
}

:root[data-theme="dark"] .cc-card,
:root[data-theme="dark"] .cc-search-wrap,
:root[data-theme="dark"] .cc-tab {
  background: rgba(18, 21, 29, 0.48);
  border-color: rgba(255, 255, 255, 0.10);
}

.cc-card__icon {
  flex: 0 0 48px;
  width: 48px;
  height: 48px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-inverse);
  font-size: 1rem;
}

.cc-card__icon--global { background: linear-gradient(135deg, var(--chat-author-5), var(--chat-author-3)); }
.cc-card__icon--channel { background: linear-gradient(135deg, var(--chat-author-1), var(--chat-author-2)); }
.cc-card__icon--direct { background: linear-gradient(135deg, var(--chat-accent), var(--chat-active-bg)); }
.cc-card__icon--group { background: linear-gradient(135deg, var(--chat-author-7), var(--chat-author-8)); }

.cc-card__body {
  min-width: 0;
  flex: 1;
  display: grid;
  gap: 6px;
}

.cc-card__topline,
.cc-card__meta {
  justify-content: space-between;
  gap: 12px;
}

.cc-card__title,
.cc-card__preview {
  overflow: hidden;
  text-overflow: ellipsis;
}

.cc-card__title {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  white-space: normal;
  line-height: 1.3;
}

.cc-card__time,
.cc-card__meta,
.cc-card__preview {
  font-size: 0.84rem;
  color: var(--md-sys-color-on-surface-variant);
}

.cc-card__type {
  font-weight: 600;
  color: var(--color-primary);
}

.cc-card__preview {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  white-space: normal;
  line-height: 1.35;
}

.cc-card__badge {
  align-self: flex-start;
  padding: 6px 10px;
  border-radius: var(--radius-pill);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 0.74rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

@media (max-width: 900px) {
  .cc-toolbar {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .cc-overlay {
    padding: 0;
  }

  .cc-panel {
    width: 100vw;
    height: 100vh;
    border-radius: 0;
  }

  .cc-header,
  .cc-toolbar,
  .cc-feed {
    padding-left: 16px;
    padding-right: 16px;
  }

  .cc-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .cc-header__right {
    width: 100%;
    justify-content: flex-end;
  }

  .cc-card {
    padding: 14px;
  }

  .cc-card__topline,
  .cc-card__meta {
    align-items: flex-start;
    flex-direction: column;
    gap: 4px;
  }
}
</style>
