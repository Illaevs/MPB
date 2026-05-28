<template>
  <section class="mail-list-pane">
    <div class="mail-list-toolbar">
      <div class="search-wrap" :class="{ focused: searchFocused }">
        <i class="fas fa-search"></i>
        <input
          :value="searchInput"
          @input="$emit('update:searchInput', $event.target.value)"
          placeholder="Поиск по почте..."
          @focus="$emit('update:searchFocused', true)"
          @blur="$emit('update:searchFocused', false)"
        >
        <button v-if="searchInput" class="search-clear" @click="$emit('update:searchInput', '')">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <button class="icon-action" title="Фильтр">
        <i class="fas fa-filter"></i>
      </button>
    </div>

    <div class="mail-list-scroll">
      <div v-if="!selectedMailbox" class="empty-state">
        <i class="fas fa-inbox empty-icon"></i>
        <div>Выберите почтовый ящик</div>
      </div>
      <div v-else-if="loadingMessages" class="empty-state">
        <i class="fas fa-circle-notch fa-spin"></i>
        <div>Загрузка...</div>
      </div>
      <div v-else-if="!filteredMessages.length" class="empty-state">
        <i class="fas fa-envelope-open empty-icon"></i>
        <div v-if="searchQuery">Ничего не найдено</div>
        <div v-else>Писем пока нет</div>
      </div>
      <div v-else class="mail-list">
        <button
          v-for="(msg, index) in filteredMessages"
          :key="msg.id"
          class="mail-item"
          :class="{
            active: selectedMessageId === msg.id,
            unread: !msg.is_read,
            focused: focusedMessageIndex === index
          }"
          @click="onSelect(msg.id)"
          :ref="el => bindRef(el, index)"
        >
          <div class="item-avatar" :style="{ '--avatar-bg': avatarColor(getSenderEmail(msg) || getSenderName(msg)) }">
            {{ getInitials(getSenderName(msg)) }}
          </div>
          <div class="item-content">
            <div class="item-row-top">
              <div class="item-from">
                <span v-if="!msg.is_read" class="unread-dot"></span>
                <span class="from-text" :class="{ 'fw-600': !msg.is_read }">{{ getSenderName(msg) }}</span>
              </div>
              <span class="item-date">{{ formatDate(msg.date) }}</span>
            </div>
            <div class="item-subject" :class="{ 'fw-600': !msg.is_read }">{{ msg.subject || '(без темы)' }}</div>
            <div v-if="msg.has_attachments || msg.attachments_count" class="item-attach">
              <i class="fas fa-paperclip"></i>
              <span>{{ msg.attachments_count || 1 }}</span>
            </div>
          </div>
        </button>
      </div>
      <div v-if="selectedMailbox && filteredMessages.length && hasMoreMessages && !searchQuery" class="mail-load-more">
        <button class="btn btn-sm btn-outline-primary" :disabled="loadingMoreMessages" @click="$emit('load-more')">
          <i v-if="loadingMoreMessages" class="fas fa-spinner fa-spin"></i>
          <i v-else class="fas fa-chevron-down"></i>
          Загрузить еще
        </button>
        <span>{{ filteredMessages.length }} из {{ messageTotal }}</span>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: 'MailList',
  props: {
    selectedMailbox: { type: Object, default: null },
    filteredMessages: { type: Array, required: true },
    selectedMessageId: { type: [String, Number, null], default: null },
    focusedMessageIndex: { type: Number, default: -1 },
    loadingMessages: Boolean,
    loadingMoreMessages: Boolean,
    hasMoreMessages: Boolean,
    messageTotal: Number,
    searchInput: { type: String, default: '' },
    searchQuery: { type: String, default: '' },
    searchFocused: Boolean,
    // Helpers from composable
    avatarColor: { type: Function, required: true },
    getSenderEmail: { type: Function, required: true },
    getSenderName: { type: Function, required: true },
    getInitials: { type: Function, required: true },
    formatDate: { type: Function, required: true },
    // Shared array of element refs (so parent can scroll via keyboard nav)
    messageRefsList: { type: Array, default: () => [] }
  },
  emits: [
    'update:searchInput', 'update:searchFocused',
    'select-message', 'update:mobileView', 'load-more'
  ],
  setup(props, { emit }) {
    const bindRef = (el, index) => {
      if (el) props.messageRefsList[index] = el
    }
    const onSelect = (id) => {
      emit('select-message', id)
      emit('update:mobileView', 'preview')
    }
    return { bindRef, onSelect }
  }
}
</script>

<style scoped>
.mail-list-pane {
  width: 384px;
  flex: 0 0 384px;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-right: 1px solid var(--mail-slate-200, #e2e8f0);
  background: rgba(255, 255, 255, 0.34);
}

.mail-list-toolbar {
  height: 64px;
  flex: 0 0 64px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid var(--mail-slate-200, #e2e8f0);
}

.search-wrap {
  height: 40px;
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 0 12px;
  border: 1px solid var(--mail-slate-200, #e2e8f0);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.82);
  transition: border-color 0.14s ease, box-shadow 0.14s ease, background 0.14s ease;
}
.search-wrap.focused {
  border-color: rgba(37, 99, 235, 0.45);
  background: #fff;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.09);
}
.search-wrap i {
  color: var(--mail-slate-400, #94a3b8);
  font-size: 13px;
}
.search-wrap input {
  width: 100%;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  color: var(--mail-slate-900, #0f172a);
  font-size: 13px;
}
.search-wrap input::placeholder { color: var(--mail-slate-400, #94a3b8); }

.search-clear,
.icon-action {
  width: 38px;
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--mail-slate-400, #94a3b8);
  cursor: pointer;
  transition: background 0.14s ease, color 0.14s ease;
}
.search-clear { width: 24px; height: 24px; }
.icon-action:hover,
.search-clear:hover {
  background: var(--mail-slate-100, #f1f5f9);
  color: var(--mail-slate-700, #334155);
}

.mail-list-scroll {
  min-height: 0;
  flex: 1;
  overflow: auto;
}

.mail-list {
  display: flex;
  flex-direction: column;
}

.mail-item {
  width: 100%;
  min-height: 88px;
  padding: 13px 16px 12px;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 11px;
  border: none;
  border-left: 4px solid transparent;
  border-radius: 0;
  border-bottom: 1px solid var(--mail-slate-100, #f1f5f9);
  background: transparent;
  color: var(--mail-slate-700, #334155);
  text-align: left;
  cursor: pointer;
  box-shadow: none;
  transition: background 0.14s ease, border-color 0.14s ease;
}
.mail-item:hover { background: rgba(248, 250, 252, 0.88); }
.mail-item.active {
  background: rgba(239, 246, 255, 0.7);
  border-left-color: var(--mail-blue, #2563eb);
}
.mail-item.focused { box-shadow: inset 0 0 0 2px rgba(37, 99, 235, 0.16); }

.mail-item.unread .from-text,
.mail-item.unread .item-subject {
  color: var(--mail-slate-900, #0f172a);
}

.item-avatar {
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: var(--avatar-bg, var(--mail-blue, #2563eb));
  color: #fff;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.02em;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.35);
}

.item-content {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.item-row-top,
.item-from {
  min-width: 0;
  display: flex;
  align-items: center;
}
.item-row-top {
  justify-content: space-between;
  gap: 10px;
}
.item-from { gap: 7px; }

.from-text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  font-weight: 600;
  color: var(--mail-slate-500, #64748b);
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--mail-blue, #2563eb);
  flex: 0 0 auto;
}

.item-date {
  flex: 0 0 auto;
  color: var(--mail-slate-400, #94a3b8);
  font-size: 10px;
  font-weight: 600;
}

.item-subject {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--mail-slate-700, #334155);
  font-size: 14px;
  font-weight: 700;
  line-height: 1.35;
}

.item-attach {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 2px;
  color: var(--mail-slate-400, #94a3b8);
  font-size: 10px;
  font-weight: 800;
}

.mail-load-more {
  padding: 12px 16px 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-top: 1px solid var(--mail-slate-100, #f1f5f9);
  background: rgba(255, 255, 255, 0.5);
}
.mail-load-more span {
  color: var(--mail-slate-400, #94a3b8);
  font-size: 11px;
  font-weight: 700;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
  text-align: center;
  color: var(--mail-slate-500, #64748b);
  gap: 6px;
  flex: 1;
}
.empty-icon { font-size: 28px; opacity: .35; }

.fw-600 { font-weight: 600; }

@media (max-width: 980px) {
  .mail-list-pane {
    width: 100%;
    flex: 0 0 300px;
    border-right: none;
    border-bottom: 1px solid var(--mail-slate-200, #e2e8f0);
  }
}

@media (max-width: 640px) {
  .mail-list-toolbar { padding-inline: 12px; }
}
</style>
