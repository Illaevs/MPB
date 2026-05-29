<template>
  <div class="messenger-page">
    <div v-if="isCompactMessenger" class="messenger-mobile-tabs" role="tablist" aria-label="Мобильная навигация мессенджера">
      <button
        type="button"
        class="messenger-mobile-tabs__tab"
        :class="{ 'is-active': activeMobilePane === 'contacts' }"
        @click="setMobilePane('contacts')"
      >
        Контакты
      </button>
      <button
        type="button"
        class="messenger-mobile-tabs__tab"
        :class="{ 'is-active': activeMobilePane === 'chat' }"
        :disabled="!activeConversation"
        @click="setMobilePane('chat')"
      >
        Чат
      </button>
      <button
        type="button"
        class="messenger-mobile-tabs__tab"
        :class="{ 'is-active': activeMobilePane === 'info' }"
        :disabled="!activeConversation"
        @click="setMobilePane('info')"
      >
        Инфо
      </button>
    </div>

    <div
      class="messenger-shell"
      :class="{
        'has-details': detailsOpen && activeConversation,
        'is-compact': isCompactMessenger,
        'mobile-pane-contacts': isCompactMessenger && activeMobilePane === 'contacts',
        'mobile-pane-chat': isCompactMessenger && activeMobilePane === 'chat',
        'mobile-pane-info': isCompactMessenger && activeMobilePane === 'info'
      }"
    >
      <aside class="messenger-sidebar">
        <div class="messenger-sidebar__topbar">
          <button
            type="button"
            class="messenger-icon-btn"
            :disabled="loading"
            title="Обновить"
            @click="refreshAll"
          >
            <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
          </button>
          <label class="messenger-sidebar__search">
            <i class="fas fa-search"></i>
            <input
              v-model="sidebarSearch"
              type="text"
              placeholder="Поиск"
            >
            <button
              v-if="sidebarSearch"
              type="button"
              class="messenger-sidebar__search-clear"
              @click="sidebarSearch = ''"
              title="Очистить"
            >
              <i class="fas fa-times"></i>
            </button>
          </label>
          <!-- Phase D.1 — глобальный поиск по сообщениям всех моих чатов. -->
          <button
            type="button"
            class="messenger-icon-btn"
            :class="{ 'is-active': messageSearchPanelOpen }"
            :title="messageSearchPanelOpen ? 'Закрыть поиск по сообщениям' : 'Поиск по сообщениям'"
            @click="toggleGlobalMessageSearch"
          >
            <i class="fas" :class="messageSearchPanelOpen ? 'fa-times' : 'fa-comment-dots'"></i>
          </button>
        </div>

        <!-- Phase D.1 — панель глобального поиска по сообщениям.
             Перекрывает список чатов когда открыта; результаты сгруппированы
             по чатам. Клик по результату — открывает чат и прыгает на
             сообщение с highlight (механика A.4). -->
        <div v-if="messageSearchPanelOpen" class="messenger-sidebar__search-panel">
          <label class="messenger-sidebar__search messenger-sidebar__search--global">
            <i class="fas fa-search"></i>
            <input
              :value="messageSearchQuery"
              type="text"
              placeholder="Поиск по сообщениям (мин. 2 символа)"
              autofocus
              @input="onGlobalSearchInput($event.target.value)"
            >
            <button
              v-if="messageSearchQuery"
              type="button"
              class="messenger-sidebar__search-clear"
              @click="onGlobalSearchInput('')"
              title="Очистить"
            >
              <i class="fas fa-times"></i>
            </button>
          </label>

          <div class="messenger-sidebar__search-meta">
            <span v-if="messageSearchLoading">
              <i class="fas fa-spinner fa-spin"></i> Ищем…
            </span>
            <span v-else-if="messageSearchQuery.trim().length < 2">
              Введите минимум 2 символа
            </span>
            <span v-else-if="!messageSearchResults.length">
              Ничего не найдено
            </span>
            <span v-else>
              Найдено: {{ messageSearchResults.length }}
            </span>
          </div>

          <div class="messenger-sidebar__search-results">
            <div
              v-for="group in messageSearchResultsByChat"
              :key="group.conversation_id"
              class="search-result-group"
            >
              <div class="search-result-group__header">
                <i class="fas" :class="searchResultGroupIcon(group)"></i>
                <strong>{{ group.conversation_title }}</strong>
                <span class="search-result-group__count">{{ group.items.length }}</span>
              </div>
              <button
                v-for="item in group.items"
                :key="item.message_id"
                type="button"
                class="search-result-item"
                @click="openSearchResult(item)"
              >
                <span class="search-result-item__topline">
                  <strong>{{ item.user_name || 'Пользователь' }}</strong>
                  <span class="search-result-item__time">{{ formatSidebarTime(item.created_at) }}</span>
                </span>
                <!-- v-html: backend возвращает уже HTML-экранированный snippet
                     с <mark> вокруг найденного. XSS-безопасно — escape сделан
                     на сервере перед вставкой <mark>. -->
                <span class="search-result-item__snippet" v-html="item.snippet"></span>
              </button>
            </div>
          </div>
        </div>

        <div v-else class="messenger-sidebar__content">
          <div
            v-for="conversation in filteredFlatConversations"
            :key="conversation.id"
            class="conversation-card-wrap"
            :class="{ 'is-muted': isConversationMuted(conversation) }"
          >
            <button
              type="button"
              class="conversation-card"
              :class="{ 'is-active': conversation.type === 'direct' ? isDirectEntryActive(conversation) : String(conversation.id) === String(activeConversationId) }"
              @click="conversation.type === 'direct' ? openDirectConversation(conversation) : openConversation(conversation.id)"
            >
              <span
                class="conversation-card__avatar"
                :class="conversation.type === 'direct' ? '' : conversationAvatarClass(conversation)"
                :style="conversation.type === 'direct' && !getConversationUserAvatarUrl(conversation) ? getAvatarStyle(conversation.title) : null"
              >
                <span
                  v-if="conversation.type === 'direct' && conversationPresenceStatus(conversation) !== 'offline'"
                  class="presence-dot"
                  :class="'presence-dot--' + conversationPresenceStatus(conversation)"
                  :title="conversationPresenceStatus(conversation) === 'online' ? 'Сейчас в сети' : 'Был(а) недавно'"
                ></span>
                <template v-if="conversation.type === 'direct'">
                  <img
                    v-if="getConversationUserAvatarUrl(conversation) && !isAvatarBroken(getConversationUserAvatarUrl(conversation))"
                    :src="getConversationUserAvatarUrl(conversation)"
                    :alt="conversation.title"
                    class="messenger-avatar-image"
                    @error="markAvatarBroken(getConversationUserAvatarUrl(conversation))"
                  >
                  <template v-else>{{ getInitial(conversation.title) }}</template>
                </template>
                <template v-else>
                  <i v-if="conversation.type === 'global'" class="fas fa-shopping-bag"></i>
                  <i v-else-if="conversation.type === 'channel'" class="fas fa-bullhorn"></i>
                  <i v-else class="fas fa-users"></i>
                </template>
              </span>

              <span class="conversation-card__content">
                <span class="conversation-card__topline">
                  <strong>{{ conversation.title }}</strong>
                  <span class="conversation-card__time">
                    <i v-if="isConversationPinned(conversation)" class="fas fa-thumbtack" title="Закреплён"></i>
                    <i v-if="isConversationMuted(conversation)" class="fas fa-bell-slash" title="Беззвучный"></i>
                    {{ formatSidebarTime(conversation.last_message?.created_at) }}
                  </span>
                </span>
                <span class="conversation-card__preview">{{ conversationPreview(conversation) }}</span>
              </span>

              <span
                v-if="conversationUnreadCount(conversation) > 0"
                class="conversation-card__badge"
                :title="`${conversationUnreadCount(conversation)} непрочитанных`"
              >{{ conversationUnreadCount(conversation) > 99 ? '99+' : conversationUnreadCount(conversation) }}</span>
            </button>

            <button
              v-if="conversation.type !== 'global'"
              type="button"
              class="conversation-card__menu-btn"
              :class="{ 'is-open': openCardMenuId === String(conversation.id) }"
              :aria-label="`Действия с чатом ${conversation.title}`"
              @click.stop="toggleCardMenu(conversation)"
            >
              <i class="fas fa-ellipsis-v"></i>
            </button>

            <div
              v-if="openCardMenuId === String(conversation.id)"
              class="conversation-card__menu"
              @click.stop
            >
              <button
                v-if="!isConversationPinned(conversation)"
                type="button"
                class="conversation-card__menu-item"
                @click="pinCard(conversation)"
              >
                <i class="fas fa-thumbtack"></i> Закрепить вверху
              </button>
              <button
                v-else
                type="button"
                class="conversation-card__menu-item"
                @click="unpinCard(conversation)"
              >
                <i class="fas fa-thumbtack" style="transform:rotate(45deg)"></i> Открепить
              </button>
              <button
                v-if="!isConversationMuted(conversation)"
                type="button"
                class="conversation-card__menu-item"
                @click="muteCardForever(conversation)"
              >
                <i class="fas fa-bell-slash"></i> Беззвучный
              </button>
              <button
                v-else
                type="button"
                class="conversation-card__menu-item"
                @click="unmuteCard(conversation)"
              >
                <i class="fas fa-bell"></i> Включить звук
              </button>
              <button
                type="button"
                class="conversation-card__menu-item"
                @click="archiveCard(conversation)"
              >
                <i class="fas fa-archive"></i> Скрыть из списка
              </button>
            </div>
          </div>

          <div v-if="!filteredFlatConversations.length && !loading" class="messenger-sidebar__empty">
            <i class="fas" :class="sidebarSearch ? 'fa-search' : 'fa-inbox'"></i>
            <span>{{ sidebarSearch ? 'Ничего не найдено' : 'Пока нет чатов' }}</span>
          </div>
        </div>

        <button
          type="button"
          class="messenger-fab"
          title="Новый чат"
          @click="openConversationModal"
        >
          <i class="fas fa-pen"></i>
        </button>
      </aside>

      <section
        class="messenger-thread"
        :class="{ 'is-drop-target': composerDragOver }"
        @dragenter.prevent="onComposerDragEnter"
        @dragover.prevent="onComposerDragOver"
        @dragleave.prevent="onComposerDragLeave"
        @drop.prevent="onComposerDrop"
      >
        <div v-if="composerDragOver" class="messenger-thread__drop-overlay">
          <div class="messenger-thread__drop-card">
            <i class="fas fa-cloud-upload-alt"></i>
            <span>Бросьте файлы — добавим к сообщению</span>
          </div>
        </div>
        <header v-if="activeConversation" class="messenger-thread__header">
          <div class="thread-title">
            <div class="thread-title__avatar" :class="conversationAvatarClass(activeConversation)" :style="threadAvatarStyle">
              <span
                v-if="activeConversation.type === 'direct' && conversationPresenceStatus(activeConversation) !== 'offline'"
                class="presence-dot presence-dot--lg"
                :class="'presence-dot--' + conversationPresenceStatus(activeConversation)"
                :title="conversationPresenceStatus(activeConversation) === 'online' ? 'Сейчас в сети' : 'Был(а) недавно'"
              ></span>
              <template v-if="activeConversation.type === 'direct'">
                <img
                  v-if="getConversationUserAvatarUrl(activeConversation) && !isAvatarBroken(getConversationUserAvatarUrl(activeConversation))"
                  :src="getConversationUserAvatarUrl(activeConversation)"
                  :alt="activeConversation.title"
                  class="messenger-avatar-image"
                  @error="markAvatarBroken(getConversationUserAvatarUrl(activeConversation))"
                >
                <template v-else>{{ getInitial(activeConversation.title) }}</template>
              </template>
              <template v-else>
                <i :class="conversationHeaderIcon(activeConversation)"></i>
              </template>
            </div>
            <div class="thread-title__content">
              <strong>{{ activeConversation.title }}</strong>
              <!-- Phase C.1: typing indicator выводится поверх subtitle.
                   typingUsers — массив {user_id, user_name, at} от бэкенда. -->
              <span v-if="typingUsers.length" class="thread-title__typing">
                {{ typingHumanText }}
                <span class="thread-title__typing-dots"><span></span><span></span><span></span></span>
              </span>
              <span v-else>{{ activeConversation.description || subtitleText }}</span>
            </div>
          </div>

          <div class="messenger-thread__actions">
            <button type="button" class="messenger-icon-btn" :class="{ 'is-active': messageSearchOpen }" title="Поиск по чату" @click="toggleMessageSearch">
              <i class="fas fa-search"></i>
            </button>
            <button type="button" class="messenger-icon-btn" :disabled="!pinnedMessage" title="Закрепленное сообщение" @click="scrollToPinned">
              <i class="fas fa-thumbtack"></i>
            </button>
            <button type="button" class="messenger-icon-btn" :title="detailsOpen ? 'Скрыть детали' : 'Показать детали'" @click="toggleDetails">
              <i class="fas" :class="detailsOpen ? 'fa-times' : 'fa-ellipsis-v'"></i>
            </button>
          </div>
        </header>

        <div v-if="pinnedMessage" class="messenger-thread__pinned" @click="scrollToPinned">
          <i class="fas fa-thumbtack"></i>
          <div class="messenger-thread__pinned-body">
            <strong>{{ pinnedMessage.user_name || 'Пользователь' }}</strong>
            <span>{{ messageExcerpt(pinnedMessage) }}</span>
          </div>
        </div>

        <div v-if="messageSearchOpen" class="messenger-thread__searchbar">
          <label class="messenger-thread__searchbox">
            <i class="fas fa-search"></i>
            <input v-model="messageSearch" type="text" placeholder="Поиск" autofocus>
          </label>

          <span
            v-if="messageSearch.trim()"
            class="messenger-thread__search-meta"
            :class="{ 'is-empty': !visibleMessages.length }"
          >
            <template v-if="visibleMessages.length">Найдено: {{ visibleMessages.length }}</template>
            <template v-else>Ничего не найдено</template>
          </span>

          <div class="messenger-thread__search-actions">
            <button type="button" class="messenger-icon-btn" title="Очистить" :disabled="!messageSearch" @click="messageSearch = ''">
              <i class="fas fa-times-circle"></i>
            </button>
            <button type="button" class="messenger-icon-btn" title="Закрыть поиск" @click="toggleMessageSearch">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>

        <div ref="listRef" class="messenger-thread__body" @scroll="onThreadScroll">
          <div v-if="loadingMessages && !messages.length" class="messenger-thread__placeholder">
            <i class="fas fa-spinner fa-spin"></i>
            <span>Загрузка сообщений...</span>
          </div>

          <div v-else-if="!messageFeed.length" class="messenger-thread__placeholder">
            <i class="fas fa-comment-dots"></i>
            <span>{{ activeConversation ? 'Пока нет сообщений' : 'Выберите диалог' }}</span>
          </div>

          <template v-else>
            <template v-for="item in messageFeed" :key="item.key">
              <div v-if="item.type === 'day'" class="messenger-thread__day">
                <span>{{ item.label }}</span>
              </div>

              <div
                v-else-if="item.type === 'unread'"
                class="messenger-thread__unread-divider"
              >
                <span>Новые сообщения</span>
              </div>

              <article
                v-else
                :id="`message-${item.message.id}`"
                class="message-row"
                :class="{
                  'is-own': isOwn(item.message),
                  'is-editing': editingId === item.message.id,
                  'is-group-first': item.isFirstFromAuthor,
                  'is-group-last': item.isLastFromAuthor,
                  'is-group-mid': !item.isFirstFromAuthor && !item.isLastFromAuthor,
                  'is-highlighted': highlightedMessageId === String(item.message.id),
                }"
                @mouseenter="hoveredMessageId = item.message.id"
                @mouseleave="hoveredMessageId = null"
              >
                <!-- Аватар: только на ПЕРВОМ сообщении в группе у не-меня.
                     В середине группы вместо аватара — пустой слот для
                     сохранения отступа (см. CSS .message-row__avatar-placeholder). -->
                <div
                  v-if="!isOwn(item.message) && item.isFirstFromAuthor"
                  class="message-row__avatar"
                  :style="getMessageAvatarUrl(item.message) ? null : getAvatarStyle(getMessageAuthor(item.message), 'user')"
                >
                  <img
                    v-if="getMessageAvatarUrl(item.message) && !isAvatarBroken(getMessageAvatarUrl(item.message))"
                    :src="getMessageAvatarUrl(item.message)"
                    :alt="getMessageAuthor(item.message)"
                    class="messenger-avatar-image"
                    @error="markAvatarBroken(getMessageAvatarUrl(item.message))"
                  >
                  <template v-else>{{ getMessageInitial(item.message) }}</template>
                </div>
                <div
                  v-else-if="!isOwn(item.message)"
                  class="message-row__avatar-placeholder"
                  aria-hidden="true"
                ></div>

                <div class="message-bubble" :class="{ 'is-deleted': item.message.is_deleted }">
                  <div
                    v-if="!isOwn(item.message) && item.isFirstFromAuthor && activeConversation && activeConversation.type !== 'direct' && !item.message.is_deleted"
                    class="message-bubble__author"
                    :style="{ color: getAuthorColor(getMessageAuthor(item.message)) }"
                  >
                    {{ getMessageAuthor(item.message) }}
                  </div>

                  <template v-if="item.message.reply_to_message && !item.message.is_deleted">
                    <button type="button" class="message-bubble__reference" @click="scrollToMessage(item.message.reply_to_message.id)">
                      <i class="fas fa-reply"></i>
                      <div>
                        <strong>{{ item.message.reply_to_message.user_name || 'Пользователь' }}</strong>
                        <span>{{ messageExcerpt(item.message.reply_to_message) }}</span>
                      </div>
                    </button>
                  </template>

                  <template v-if="item.message.forwarded_from_message && !item.message.is_deleted">
                    <button type="button" class="message-bubble__reference message-bubble__reference--forwarded" @click="scrollToMessage(item.message.forwarded_from_message.id)">
                      <i class="fas fa-share"></i>
                      <div>
                        <strong>Переслано от {{ item.message.forwarded_from_message.user_name || 'Пользователь' }}</strong>
                        <span>{{ messageExcerpt(item.message.forwarded_from_message) }}</span>
                      </div>
                    </button>
                  </template>

                  <template v-if="item.message.is_deleted">
                    <div class="message-bubble__deleted">
                      <i class="fas fa-ban"></i>
                      <span>Сообщение удалено</span>
                    </div>
                  </template>

                  <template v-else>
                    <div v-if="messageImageAttachments(item.message).length" class="message-bubble__media-grid">
                      <button
                        v-for="file in messageImageAttachments(item.message)"
                        :key="`image:${file.path || file.name}`"
                        type="button"
                        class="message-image"
                        :title="file.name || 'Изображение'"
                        @click="openImageViewer(file, item.message.attachments)"
                      >
                        <img :src="file.download_url" :alt="file.name || 'Изображение'">
                      </button>
                    </div>

                    <div v-if="messageVideoAttachments(item.message).length" class="message-bubble__video-grid">
                      <video
                        v-for="file in messageVideoAttachments(item.message)"
                        :key="`video:${file.path || file.name}`"
                        :src="file.download_url"
                        controls
                        preload="metadata"
                        playsinline
                        class="message-video"
                      ></video>
                    </div>

                    <!-- Phase D.2 — голосовые сообщения / любое audio/* -->
                    <div v-if="messageAudioAttachments(item.message).length" class="message-bubble__audio-list">
                      <div
                        v-for="file in messageAudioAttachments(item.message)"
                        :key="`audio:${file.path || file.name}`"
                        class="message-audio"
                      >
                        <i class="fas fa-microphone"></i>
                        <audio
                          :src="file.download_url"
                          controls
                          preload="metadata"
                          class="message-audio__player"
                        ></audio>
                      </div>
                    </div>

                    <div v-if="messageFileAttachments(item.message).length" class="message-bubble__attachments">
                      <div v-for="file in messageFileAttachments(item.message)" :key="file.path || file.name" class="message-file">
                        <button type="button" class="message-file__icon" :title="file.name || 'Файл'" @click="downloadAttachment(file)">
                          <i class="fas" :class="(file.content_type || '').startsWith('image/') ? 'fa-image' : (file.content_type === 'application/pdf' ? 'fa-file-pdf' : 'fa-file')"></i>
                        </button>
                        <span class="message-file__body">
                          <strong>{{ file.name || 'Файл' }}</strong>
                          <span>{{ formatSize(file.size) }}</span>
                        </span>
                      </div>
                    </div>

                    <p v-if="item.message.body" class="message-bubble__text">
                      <!-- Phase D.3: @-меншены рендерятся как ссылки/чипы.
                           renderMessageBody возвращает массив сегментов:
                           text → обычный текст, mention → router-link
                           если есть href, иначе span. -->
                      <template v-for="(seg, sidx) in renderMessageBody(item.message.body, item.message.mentions)" :key="`seg-${item.message.id}-${sidx}`">
                        <router-link
                          v-if="seg.type === 'mention' && seg.href"
                          :to="seg.href"
                          class="message-mention"
                          :data-kind="seg.kind"
                        >@{{ seg.label }}</router-link>
                        <span
                          v-else-if="seg.type === 'mention'"
                          class="message-mention message-mention--inert"
                          :data-kind="seg.kind"
                        >@{{ seg.label }}</span>
                        <template v-else>{{ seg.value }}</template>
                      </template>
                    </p>

                    <div v-if="extractMessageLinks(item.message).length" class="message-bubble__links">
                      <a
                        v-for="link in extractMessageLinks(item.message)"
                        :key="`${item.message.id}:${link.url}`"
                        :href="link.url"
                        class="message-link-pill"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <i class="fas fa-link"></i>
                        <span>{{ link.label }}</span>
                      </a>
                    </div>
                  </template>

                  <span class="message-bubble__meta">
                    <span v-if="item.message.edited_at" class="message-bubble__edited">ред.</span>
                    <span class="message-bubble__time">{{ formatMessageTime(item.message.created_at) }}</span>
                    <!-- Phase B.2: ✓ delivered / ✓✓ read.
                         Логика: ticks показываются на моих сообщениях.
                         Для DM сравниваем created_at сообщения с
                         peer_last_read_at собеседника:
                           created_at <= peer_last_read_at → ✓✓ (read)
                           иначе → ✓ (delivered)
                         Для group/global Stage 2 ticks → всегда ✓ (read
                         receipts per N участников — отдельная задача). -->
                    <template v-if="isOwn(item.message) && !item.message.is_deleted">
                      <i
                        v-if="isMessageRead(item.message)"
                        class="fas fa-check-double message-bubble__ticks message-bubble__ticks--read"
                        title="Прочитано"
                      ></i>
                      <i
                        v-else
                        class="fas fa-check message-bubble__ticks"
                        title="Доставлено"
                      ></i>
                    </template>
                  </span>

                  <!-- Phase B.3: уже поставленные реакции, click → toggle. -->
                  <div
                    v-if="(item.message.reactions || []).length && !item.message.is_deleted"
                    class="message-bubble__reactions"
                  >
                    <button
                      v-for="r in item.message.reactions"
                      :key="r.emoji"
                      type="button"
                      class="message-bubble__reaction"
                      :class="{ 'is-mine': r.reacted_by_me }"
                      :title="`${r.count} ${r.reacted_by_me ? '(включая вас)' : ''}`"
                      @click="toggleMessageReaction(item.message.id, r.emoji)"
                    >
                      <span class="message-bubble__reaction-emoji">{{ r.emoji }}</span>
                      <span class="message-bubble__reaction-count">{{ r.count }}</span>
                    </button>
                  </div>

                  <!-- Phase B.3: мини-пикер эмодзи поверх баббла. -->
                  <div
                    v-if="reactionPickerOpenFor === String(item.message.id)"
                    class="message-bubble__reaction-picker"
                    @click.stop
                  >
                    <button
                      v-for="emoji in REACTION_PRESETS"
                      :key="emoji"
                      type="button"
                      class="message-bubble__reaction-picker-item"
                      :title="`Реагировать ${emoji}`"
                      @click="applyReaction(item.message.id, emoji)"
                    >{{ emoji }}</button>
                  </div>
                </div>

                <div v-if="messageActionsVisible(item.message)" class="message-row__actions">
                  <button type="button" title="Реакция" @click="openReactionPicker(item.message)">
                    <i class="far fa-smile"></i>
                  </button>
                  <button type="button" title="Ответить" @click="replyToMessage(item.message)">
                    <i class="fas fa-reply"></i>
                  </button>
                  <button type="button" title="Переслать" @click="openForwardModal(item.message)">
                    <i class="fas fa-share-alt"></i>
                  </button>
                  <button type="button" :title="item.message.is_pinned ? 'Открепить' : 'Закрепить'" @click="togglePin(item.message)">
                    <i class="fas fa-thumbtack"></i>
                  </button>
                  <button type="button" title="Копировать" @click="copyMessage(item.message)">
                    <i class="far fa-copy"></i>
                  </button>
                  <button v-if="canEdit(item.message)" type="button" title="Изменить" @click="startEditing(item.message)">
                    <i class="fas fa-pen"></i>
                  </button>
                  <button v-if="canEdit(item.message)" type="button" title="Удалить" class="is-danger" @click="askDelete(item.message)">
                    <i class="fas fa-trash"></i>
                  </button>
                </div>
              </article>
            </template>
          </template>
        </div>

        <div v-if="activeConversation" class="messenger-composer">
          <div v-if="replyTarget" class="messenger-composer__context">
            <div>
              <strong>Ответ для {{ replyTarget.user_name || getMessageAuthor(replyTarget) }}</strong>
              <span>{{ messageExcerpt(replyTarget) }}</span>
            </div>
            <button type="button" @click="cancelReply">
              <i class="fas fa-times"></i>
            </button>
          </div>

          <div v-if="pendingFiles.length" class="messenger-composer__files">
            <div
              v-for="(file, index) in pendingFiles"
              :key="file.id || `${file.name}-${index}`"
              class="messenger-composer__file"
              :class="{ 'messenger-composer__file--image': file.isImagePreview }"
            >
              <div v-if="file.previewUrl" class="messenger-composer__file-preview">
                <img :src="file.previewUrl" :alt="file.name">
              </div>
              <span class="messenger-composer__file-icon"><i class="fas" :class="file.isImagePreview ? 'fa-image' : 'fa-paperclip'"></i></span>
              <span class="messenger-composer__file-body">
                <strong>{{ file.name }}</strong>
                <span>{{ formatSize(file.size) }}</span>
              </span>
              <button type="button" @click="removeFile(index)">
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>

          <div v-if="mentionPickerOpen" class="messenger-composer__mention-picker">
            <div class="messenger-composer__mention-search">
              <i class="fas fa-search"></i>
              <input v-model="mentionQuery" type="text" placeholder="Найти участника">
            </div>
            <div v-if="mentionOptions.length" class="messenger-composer__mention-list">
              <button v-for="user in mentionOptions" :key="user.id" type="button" class="messenger-composer__mention-option" @click="addMention(user)">
                <span class="messenger-composer__mention-avatar" :style="getUserAvatarUrl(user) ? null : getAvatarStyle(user.full_name || user.email || user.id)">
                  <img
                    v-if="getUserAvatarUrl(user) && !isAvatarBroken(getUserAvatarUrl(user))"
                    :src="getUserAvatarUrl(user)"
                    :alt="user.full_name || user.email || user.id"
                    class="messenger-avatar-image"
                    @error="markAvatarBroken(getUserAvatarUrl(user))"
                  >
                  <template v-else>{{ getInitial(user.full_name || user.email || user.id) }}</template>
                </span>
                <span>{{ user.full_name || user.email || user.id }}</span>
              </button>
            </div>
            <div v-else class="messenger-composer__mention-empty">Пользователи не найдены</div>
          </div>

          <div class="messenger-composer__input-row" :class="{ 'is-edit': isEditMode }">
            <div class="messenger-composer__pill">
              <button
                type="button"
                class="messenger-composer__icon"
                title="Прикрепить файл"
                @click="triggerFilePicker"
              >
                <i class="fas fa-paperclip"></i>
              </button>

              <div class="messenger-composer__field">
                <div v-if="selectedMentions.length" class="messenger-composer__mentions messenger-composer__mentions--inline">
                  <span v-for="mention in selectedMentions" :key="mention.id" class="messenger-composer__mention-chip">
                    @{{ mention.name }}
                    <button type="button" @click="removeMention(mention.id)">
                      <i class="fas fa-times"></i>
                    </button>
                  </span>
                </div>

                <textarea
                  ref="composerInputRef"
                  v-model="composerText"
                  class="messenger-composer__input"
                  rows="1"
                  :placeholder="isEditMode ? 'Измените сообщение...' : 'Сообщение'"
                  @input="onComposerInput"
                  @paste="onComposerPaste"
                  @keydown="onComposerKeydownMention"
                  @keydown.enter.exact.prevent="submitComposer"
                ></textarea>

                <!-- Phase B.4: @-mention autocomplete dropdown. -->
                <div
                  v-if="mentionAutoOpen && mentionAutoResults.length"
                  class="messenger-composer__mention-auto"
                  @mousedown.prevent
                >
                  <button
                    v-for="(item, idx) in mentionAutoResults"
                    :key="`${item.kind}:${item.id}`"
                    type="button"
                    class="messenger-composer__mention-auto-item"
                    :class="{ 'is-active': idx === mentionAutoActiveIdx }"
                    @click="pickMentionAutoItem(item)"
                    @mouseenter="mentionAutoActiveIdx = idx"
                  >
                    <span class="mention-auto__kind" :data-kind="item.kind">
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
                    <span class="mention-auto__copy">
                      <strong>{{ item.label }}</strong>
                      <small v-if="item.sublabel">{{ item.sublabel }}</small>
                    </span>
                  </button>
                </div>
              </div>

              <button
                type="button"
                class="messenger-composer__icon"
                :class="{ 'is-active': mentionPickerOpen }"
                title="Упомянуть"
                @click="toggleMentions"
              >
                <i class="fas fa-at"></i>
              </button>
              <button
                type="button"
                class="messenger-composer__icon"
                title="Вставить ссылку"
                @click="insertLinkToken"
              >
                <i class="fas fa-link"></i>
              </button>
              <button
                type="button"
                class="messenger-composer__icon"
                title="Эмодзи"
                @click="insertEmoji"
              >
                <i class="far fa-smile"></i>
              </button>
              <!-- Phase D.2 — кнопка записи голосового сообщения. -->
              <button
                type="button"
                class="messenger-composer__icon"
                :class="{ 'is-recording': isRecording }"
                :title="isRecording ? 'Остановить запись' : 'Голосовое сообщение'"
                @click="isRecording ? stopRecording() : startRecording()"
              >
                <i class="fas" :class="isRecording ? 'fa-stop' : 'fa-microphone'"></i>
              </button>
            </div>

            <!-- Phase D.2 — индикатор активной записи (внутри composer). -->
            <div v-if="isRecording" class="messenger-composer__recording">
              <span class="messenger-composer__recording-dot"></span>
              <span class="messenger-composer__recording-time">{{ recordingDurationLabel }}</span>
              <span class="messenger-composer__recording-hint">Запись… отпустите Stop, чтобы прикрепить</span>
              <button
                type="button"
                class="messenger-composer__recording-cancel"
                title="Отменить запись"
                @click="cancelRecording"
              >
                <i class="fas fa-times"></i>
              </button>
            </div>

            <button
              v-if="isEditMode"
              type="button"
              class="messenger-composer__send messenger-composer__send--muted"
              title="Отменить редактирование"
              @click="cancelEdit"
            >
              <i class="fas fa-times"></i>
            </button>
            <button
              type="button"
              class="messenger-composer__send"
              :class="{ 'is-disabled': submitDisabled }"
              :title="isEditMode ? 'Сохранить сообщение' : 'Отправить сообщение'"
              :disabled="submitDisabled"
              @click="submitComposer"
            >
              <i v-if="sending" class="fas fa-spinner fa-spin"></i>
              <i v-else class="fas" :class="isEditMode ? 'fa-check' : 'fa-paper-plane'"></i>
            </button>
          </div>

          <input ref="fileInput" type="file" class="d-none" multiple @change="onFilesPicked">
        </div>
      </section>

      <aside v-if="detailsOpen && activeConversation" class="messenger-details">
        <div class="messenger-details__header">
          <h2>Детали</h2>
          <button type="button" class="messenger-icon-btn" @click="closeDetails">
            <i class="fas fa-times"></i>
          </button>
        </div>

          <div class="messenger-details__hero">
            <div class="messenger-details__hero-icon" :class="conversationAvatarClass(activeConversation)" :style="threadAvatarStyle">
              <template v-if="activeConversation.type === 'direct'">
                <img
                  v-if="getConversationUserAvatarUrl(activeConversation) && !isAvatarBroken(getConversationUserAvatarUrl(activeConversation))"
                  :src="getConversationUserAvatarUrl(activeConversation)"
                  :alt="activeConversation.title"
                  class="messenger-avatar-image"
                  @error="markAvatarBroken(getConversationUserAvatarUrl(activeConversation))"
                >
                <template v-else>{{ getInitial(activeConversation.title) }}</template>
              </template>
              <template v-else>
                <i :class="conversationHeaderIcon(activeConversation)"></i>
            </template>
          </div>
          <strong>{{ activeConversation.title }}</strong>
          <span>{{ activeConversation.description || subtitleText }}</span>
          <div class="messenger-details__hero-actions">
            <button type="button" class="messenger-icon-btn" @click="toggleMessageSearch">
              <i class="fas fa-search"></i>
            </button>
            <button type="button" class="messenger-icon-btn" :disabled="!canManageMembers" @click="addMembersModalOpen = true">
              <i class="fas fa-user-plus"></i>
            </button>
            <button type="button" class="messenger-icon-btn" :disabled="!canManageMembers" @click="openRenameModal">
              <i class="fas fa-pen"></i>
            </button>
          </div>
        </div>

        <div class="messenger-details__sections">
          <section class="detail-section">
            <button type="button" class="detail-section__toggle" @click="toggleSection('info')">
              <span><i class="fas fa-info-circle"></i> Информация</span>
              <i class="fas" :class="detailSections.info ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
            </button>
            <div v-if="detailSections.info" class="detail-section__body">
              <div class="detail-stat">
                <span>Тип</span>
                <strong>{{ conversationTypeLabel(activeConversation.type) }}</strong>
              </div>
              <div class="detail-stat">
                <span>Сообщений</span>
                <strong>{{ messages.length }}</strong>
              </div>
              <div class="detail-stat">
                <span>Закреплено</span>
                <strong>{{ pinnedMessage ? '1' : '0' }}</strong>
              </div>
            </div>
          </section>

          <section class="detail-section">
            <button type="button" class="detail-section__toggle" @click="toggleSection('members')">
              <span><i class="fas fa-users"></i> Участники</span>
              <i class="fas" :class="detailSections.members ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
            </button>
            <div v-if="detailSections.members" class="detail-section__body">
              <div v-if="members.length" class="member-list">
                <div v-for="member in members" :key="member.user_id" class="member-list__item">
                  <span class="member-list__avatar" :style="getMemberAvatarUrl(member) ? null : getAvatarStyle(member.user_name)">
                    <img
                      v-if="getMemberAvatarUrl(member) && !isAvatarBroken(getMemberAvatarUrl(member))"
                      :src="getMemberAvatarUrl(member)"
                      :alt="member.user_name"
                      class="messenger-avatar-image"
                      @error="markAvatarBroken(getMemberAvatarUrl(member))"
                    >
                    <template v-else>{{ getInitial(member.user_name) }}</template>
                  </span>
                  <span class="member-list__body">
                    <strong>{{ member.user_name }}</strong>
                    <span>{{ member.user_email || memberRoleLabel(member.role) }}</span>
                  </span>
                  <button v-if="canManageMembers && activeConversation.type !== 'direct' && activeConversation.type !== 'global'" type="button" class="messenger-inline-btn" @click="askRemoveMember(member)">
                    <i class="fas fa-times"></i>
                  </button>
                </div>
              </div>
              <div v-else class="detail-section__empty">Участников пока нет</div>
            </div>
          </section>

          <section class="detail-section">
            <button type="button" class="detail-section__toggle" @click="toggleSection('media')">
              <span><i class="fas fa-photo-film"></i> Медиа<small v-if="mediaItems.length"> · {{ mediaItems.length }}</small></span>
              <i class="fas" :class="detailSections.media ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
            </button>
            <div v-if="detailSections.media" class="detail-section__body">
              <div v-if="mediaItems.length" class="detail-media-grid">
                <button
                  v-for="item in mediaItems"
                  :key="item.key"
                  type="button"
                  class="detail-media"
                  :title="item.name || 'Медиа'"
                  @click="isInlineVideo(item) ? downloadAttachment(item) : openImageViewer(item, mediaItems)"
                >
                  <img
                    v-if="isInlineImage(item) && item.download_url"
                    :src="item.download_url"
                    :alt="item.name || 'Изображение'"
                    loading="lazy"
                    class="detail-media__img"
                  >
                  <span v-else-if="isInlineVideo(item)" class="detail-media__video">
                    <i class="fas fa-play"></i>
                  </span>
                </button>
              </div>
              <div v-else class="detail-section__empty">Медиа пока нет</div>
            </div>
          </section>

          <section class="detail-section">
            <button type="button" class="detail-section__toggle" @click="toggleSection('files')">
              <span><i class="fas fa-paperclip"></i> Файлы<small v-if="documentItems.length"> · {{ documentItems.length }}</small></span>
              <i class="fas" :class="detailSections.files ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
            </button>
            <div v-if="detailSections.files" class="detail-section__body">
              <div v-if="documentItems.length" class="detail-file-list">
                <button
                  v-for="file in documentItems"
                  :key="file.key"
                  type="button"
                  class="detail-file"
                  @click="downloadAttachment(file)"
                >
                  <span class="detail-file__icon"><i class="fas fa-paperclip"></i></span>
                  <span class="detail-file__body">
                    <strong>{{ file.name }}</strong>
                    <span>{{ formatSize(file.size) }} · {{ formatDateTime(file.created_at) }}</span>
                  </span>
                </button>
              </div>
              <div v-else class="detail-section__empty">Файлов пока нет</div>
            </div>
          </section>

          <section class="detail-section">
            <button type="button" class="detail-section__toggle" @click="toggleSection('links')">
              <span><i class="fas fa-link"></i> Ссылки</span>
              <i class="fas" :class="detailSections.links ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
            </button>
            <div v-if="detailSections.links" class="detail-section__body">
              <div v-if="links.length" class="detail-link-list">
                <a v-for="link in links" :key="`${link.message_id}:${link.url}`" :href="link.url" class="detail-link" target="_blank" rel="noopener noreferrer">
                  <span>{{ trimText(link.text, 36) }}</span>
                  <i class="fas fa-external-link-alt"></i>
                </a>
              </div>
              <div v-else class="detail-section__empty">Ссылок пока нет</div>
            </div>
          </section>
        </div>
      </aside>
    </div>

    <Teleport to="body">
      <div v-if="confirmModalOpen" class="messenger-confirm-overlay" v-modal-close="closeConfirm">
        <div class="messenger-confirm">
          <div class="messenger-confirm__header">
            <h3>{{ confirmTitle }}</h3>
            <button type="button" class="messenger-icon-btn" @click="closeConfirm"><i class="fas fa-times"></i></button>
          </div>
          <p>{{ confirmText }}</p>
          <div class="messenger-confirm__actions">
            <button type="button" class="btn btn-outline-secondary btn-sm" @click="closeConfirm">Отмена</button>
            <button type="button" class="btn btn-danger btn-sm" @click="executeConfirm">Подтвердить</button>
          </div>
        </div>
      </div>

      <div v-if="showConversationModal" class="messenger-dialog-overlay" v-modal-close="closeConversationModal">
        <div class="messenger-dialog">
          <div class="messenger-dialog__header">
            <h3>{{ renameMode ? 'Переименовать чат' : 'Новый чат' }}</h3>
            <button type="button" class="messenger-icon-btn" @click="closeConversationModal"><i class="fas fa-times"></i></button>
          </div>
          <div class="messenger-dialog__body">
            <template v-if="!renameMode">
              <label class="messenger-field">
                <span>Тип</span>
                <select v-model="conversationForm.type" class="form-control">
                  <option value="direct">Написать коллеге</option>
                  <option value="group">Группа</option>
                  <option value="channel">Канал</option>
                </select>
              </label>
            </template>

            <template v-if="renameMode || conversationForm.type !== 'direct'">
              <label class="messenger-field">
                <span>Название</span>
                <input v-model="conversationForm.title" class="form-control" type="text">
              </label>
              <label class="messenger-field">
                <span>Описание</span>
                <input v-model="conversationForm.description" class="form-control" type="text">
              </label>
            </template>

            <!-- Stage 1 implicit DM: searchable users (любой активный
                 юзер, не только «без чата»). Помечаем «уже есть чат» —
                 клик переключает на существующий, а не плодит дубль. -->
            <template v-if="!renameMode && conversationForm.type === 'direct'">
              <label class="messenger-field">
                <span>Кому написать</span>
                <input
                  v-model="writeColleagueSearch"
                  class="form-control"
                  type="text"
                  placeholder="Поиск по имени или email…"
                  @keydown.esc.stop="writeColleagueSearch = ''"
                >
              </label>
              <div class="messenger-write-list">
                <button
                  v-for="user in filteredSearchableUsers"
                  :key="user.id"
                  type="button"
                  class="messenger-write-row"
                  @click="pickColleagueAndOpen(user)"
                >
                  <UiAvatar
                    :name="user.full_name || user.email || ''"
                    :src="user.avatar_url || null"
                    size="sm"
                  />
                  <span class="messenger-write-row__copy">
                    <strong>{{ user.full_name || user.email || user.id }}</strong>
                    <small>
                      <template v-if="user.has_dm"><i class="fas fa-comment-dots"></i> Уже есть чат</template>
                      <template v-else-if="user.email">{{ user.email }}</template>
                    </small>
                  </span>
                </button>
                <div v-if="loadingSearchableUsers && !filteredSearchableUsers.length" class="messenger-write-empty">
                  Загрузка…
                </div>
                <div v-else-if="!filteredSearchableUsers.length" class="messenger-write-empty">
                  {{ writeColleagueSearch ? 'Никого не нашли' : 'Нет доступных коллег' }}
                </div>
              </div>
            </template>

            <template v-if="!renameMode && conversationForm.type !== 'direct'">
              <label class="messenger-field">
                <span>Участники</span>
                <div class="messenger-checkbox-list">
                  <label v-for="user in availableDirectUsers" :key="user.id" class="messenger-checkbox">
                    <input v-model="conversationForm.memberIds" :value="user.id" type="checkbox">
                    <span>{{ user.full_name || user.email }}</span>
                  </label>
                </div>
              </label>
            </template>
          </div>
          <div class="messenger-dialog__actions">
            <button type="button" class="btn btn-outline-secondary btn-sm" @click="closeConversationModal">Отмена</button>
            <button
              v-if="renameMode || conversationForm.type !== 'direct'"
              type="button"
              class="btn btn-primary btn-sm"
              :disabled="savingConversation"
              @click="submitConversationModal"
            >Сохранить</button>
          </div>
        </div>
      </div>

      <div v-if="addMembersModalOpen" class="messenger-dialog-overlay" v-modal-close="() => addMembersModalOpen = false">
        <div class="messenger-dialog">
          <div class="messenger-dialog__header">
            <h3>Добавить участников</h3>
            <button type="button" class="messenger-icon-btn" @click="addMembersModalOpen = false"><i class="fas fa-times"></i></button>
          </div>
          <div class="messenger-dialog__body">
            <div class="messenger-checkbox-list">
              <label v-for="user in availableUsersToAdd" :key="user.id" class="messenger-checkbox">
                <input v-model="addMembersSelection" :value="user.id" type="checkbox">
                <span>{{ user.full_name || user.email }}</span>
              </label>
            </div>
          </div>
          <div class="messenger-dialog__actions">
            <button type="button" class="btn btn-outline-secondary btn-sm" @click="addMembersModalOpen = false">Отмена</button>
            <button type="button" class="btn btn-primary btn-sm" :disabled="savingConversation" @click="submitAddMembers">Добавить</button>
          </div>
        </div>
      </div>

      <div v-if="forwardModalOpen" class="messenger-dialog-overlay" v-modal-close="closeForwardModal">
        <div class="messenger-dialog">
          <div class="messenger-dialog__header">
            <h3>Переслать сообщение</h3>
            <button type="button" class="messenger-icon-btn" @click="closeForwardModal"><i class="fas fa-times"></i></button>
          </div>
          <div class="messenger-dialog__body messenger-dialog__body--scroll">
            <button v-for="conversation in forwardTargets" :key="conversation.id" type="button" class="messenger-forward-target" @click="submitForward(conversation.id)">
              <strong>{{ conversation.title }}</strong>
              <span>{{ conversation.description || conversationTypeLabel(conversation.type) }}</span>
            </button>
          </div>
        </div>
      </div>

      <div v-if="imageViewerOpen && activeImageItem" class="messenger-media-viewer" @click="closeImageViewer">
        <div class="messenger-media-viewer__toolbar" @click.stop>
          <div class="messenger-media-viewer__meta">
            <strong>{{ activeImageItem.name || 'Изображение' }}</strong>
            <span>{{ formatSize(activeImageItem.size) }}</span>
          </div>
          <div class="messenger-media-viewer__actions">
            <button
              v-if="imageViewerItems.length > 1"
              type="button"
              class="messenger-icon-btn"
              title="Предыдущее изображение"
              @click="showPreviousImage"
            >
              <i class="fas fa-chevron-left"></i>
            </button>
            <button
              v-if="imageViewerItems.length > 1"
              type="button"
              class="messenger-icon-btn"
              title="Следующее изображение"
              @click="showNextImage"
            >
              <i class="fas fa-chevron-right"></i>
            </button>
            <button type="button" class="messenger-icon-btn" title="Скачать" @click="downloadAttachment(activeImageItem)">
              <i class="fas fa-download"></i>
            </button>
            <button type="button" class="messenger-icon-btn" title="Закрыть" @click="closeImageViewer">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
        <div class="messenger-media-viewer__stage">
          <img :src="activeImageItem.download_url" :alt="activeImageItem.name || 'Изображение'" @click.stop>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessenger } from '../composables/useMessenger'
import { useToast } from '../composables/useToast'
import { normalizeAvatarUrl } from '../utils/avatar'
import UiAvatar from '../components/ui/UiAvatar.vue'

const URL_RE = /https?:\/\/[^\s<>"']+/gi
const INLINE_IMAGE_TYPES = new Set(['image/png', 'image/jpeg', 'image/webp', 'image/gif'])
const INLINE_IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.webp', '.gif']

export default {
  name: 'Messenger',
  components: { UiAvatar },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const { success: toastSuccess, info: toastInfo } = useToast()
    const listRef = ref(null)
    const fileInput = ref(null)
    const composerInputRef = ref(null)
    const brokenAvatarUrls = ref(new Set())
    const messageSearchOpen = ref(false)
    const messageSearch = ref('')
    const detailsOpen = ref(false)
    const mobilePane = ref('contacts')
    const hoveredMessageId = ref(null)
    const groupsOpen = ref(true)
    const directOpen = ref(true)
    const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 0)
    const autoScrollPending = ref(true)
    const userNearBottom = ref(true)
    const detailSections = ref({ info: true, members: true, media: true, files: true, links: false })
    const confirmModalOpen = ref(false)
    const confirmTitle = ref('')
    const confirmText = ref('')
    const confirmAction = ref(null)
    const showConversationModal = ref(false)
    const renameMode = ref(false)
    const addMembersModalOpen = ref(false)
    const addMembersSelection = ref([])
    const forwardModalOpen = ref(false)
    const forwardingMessage = ref(null)
    const imageViewerOpen = ref(false)
    const imageViewerItems = ref([])
    const activeImageIndex = ref(0)
    const conversationForm = ref({
      type: 'direct',
      title: '',
      description: '',
      directUserId: '',
      memberIds: []
    })
    const routeConversationResolved = ref(false)

    const {
      activeUser,
      loading,
      loadingMessages,
      savingConversation,
      sending,
      conversations,
      activeConversationId,
      activeConversation,
      users,
      messages,
      members,
      files,
      links,
      draft,
      pendingFiles,
      mentionPickerOpen,
      mentionQuery,
      mentionOptions,
      selectedMentions,
      editingId,
      editingBody,
      replyTarget,
      isEditMode,
      canManageMembers,
      isConversationUnread,
      conversationUnreadCount,
      isConversationMuted,
      isConversationArchived,
      isConversationPinned,
      searchableUsers,
      loadingSearchableUsers,
      loadSearchableUsers,
      archiveConversationForMe,
      muteConversationForever,
      unmuteConversation,
      pinConversation,
      unpinConversation,
      toggleMessageReaction,
      messageSearchQuery,
      messageSearchResults,
      messageSearchResultsByChat,
      messageSearchLoading,
      messageSearchPanelOpen,
      runMessageSearch,
      openMessageSearchPanel,
      closeMessageSearchPanel,
      typingUsers,
      noteUserTyping,
      isOwn,
      canEdit,
      formatDateTime,
      formatMessageTime,
      formatSize,
      markConversationSeen,
      loadConversations,
      loadMessages,
      selectConversation,
      openFilePicker,
      appendPendingFiles,
      onFilesPicked,
      removeFile,
      toggleMentions,
      addMention,
      removeMention,
      createDirectConversation,
      createConversation,
      updateConversation,
      addConversationMembers,
      removeConversationMember,
      sendMessage,
      forwardMessage,
      startReply,
      cancelReply,
      startEdit,
      cancelEdit,
      saveEdit,
      deleteMessage,
      pinMessage,
      unpinMessage,
      downloadAttachment
    } = useMessenger()

    // Stage 1 implicit DM: state для «написать коллеге» + per-card menu.
    const writeColleagueSearch = ref('')
    const openCardMenuId = ref(null)

    // Phase A.2: drag-and-drop файлов в чат. dragDepth — стандартный
    // патт для устранения мерцания overlay (dragenter/dragleave
    // у дочерних элементов триггерит лишние события).
    const composerDragOver = ref(false)
    let _composerDragDepth = 0

    const onComposerDragEnter = (event) => {
      // На простой text-drag не реагируем.
      if (!event?.dataTransfer?.types || !Array.from(event.dataTransfer.types).includes('Files')) {
        return
      }
      _composerDragDepth += 1
      composerDragOver.value = true
    }

    const onComposerDragOver = (event) => {
      // dropEffect=copy визуально показывает «добавим к сообщению».
      if (event?.dataTransfer && Array.from(event.dataTransfer.types || []).includes('Files')) {
        event.dataTransfer.dropEffect = 'copy'
        composerDragOver.value = true
      }
    }

    const onComposerDragLeave = () => {
      _composerDragDepth = Math.max(0, _composerDragDepth - 1)
      if (_composerDragDepth === 0) {
        composerDragOver.value = false
      }
    }

    const onComposerDrop = (event) => {
      _composerDragDepth = 0
      composerDragOver.value = false
      const files = Array.from(event?.dataTransfer?.files || [])
      if (!files.length) return
      // Используем тот же канал, что и file-picker / paste — это
      // делает проверки размера/типа единообразными.
      appendPendingFiles(files)
    }

    // Phase A.3: разделяем files на «Медиа» (картинки + видео,
    // отображаются grid'ом превью) и «Файлы» (остальное, list-карточки).
    // files уже flattened из useMessenger — здесь только split.
    const mediaItems = computed(() =>
      (files.value || []).filter((file) => isInlineImage(file) || isInlineVideo(file))
    )
    const documentItems = computed(() =>
      (files.value || []).filter((file) => !isInlineImage(file) && !isInlineVideo(file))
    )

    const filteredSearchableUsers = computed(() => {
      const q = String(writeColleagueSearch.value || '').trim().toLowerCase()
      const list = searchableUsers.value || []
      if (!q) return list.slice(0, 60)
      return list
        .filter((u) => {
          const hay = `${u.full_name || ''} ${u.email || ''}`.toLowerCase()
          return hay.includes(q)
        })
        .slice(0, 60)
    })

    const isCompactMessenger = computed(() => viewportWidth.value <= 1180)
    const activeMobilePane = computed(() => {
      if (!isCompactMessenger.value) return 'desktop'
      if (!activeConversation.value) return 'contacts'
      if (detailsOpen.value) return 'info'
      return mobilePane.value === 'contacts' ? 'contacts' : 'chat'
    })
    const activeImageItem = computed(() => imageViewerItems.value[activeImageIndex.value] || null)

    const groupConversations = computed(() => conversations.value.filter((item) => item.type !== 'direct'))
    const directConversations = computed(() => conversations.value.filter((item) => item.type === 'direct'))
    const pinnedMessage = computed(() => activeConversation.value?.pinned_message || messages.value.find((item) => item.is_pinned) || null)
    const subtitleText = computed(() => {
      if (!activeConversation.value) return ''
      const count = activeConversation.value.member_count || members.value.length || 0
      return formatMembersCount(count)
    })
    const availableDirectUsers = computed(() =>
      users.value.filter((user) => String(user.id) !== String(activeUser.value?.id || ''))
    )
    const availableUsersToAdd = computed(() => {
      const memberIds = new Set(members.value.map((item) => String(item.user_id)))
      return availableDirectUsers.value.filter((user) => !memberIds.has(String(user.id)))
    })
    const userDirectory = computed(() => {
      const map = {}
      users.value.forEach((user) => {
        if (!user?.id) return
        map[String(user.id)] = user
      })
      if (activeUser.value?.id) {
        map[String(activeUser.value.id)] = {
          ...(map[String(activeUser.value.id)] || {}),
          ...activeUser.value
        }
      }
      return map
    })
    const getDirectPeerId = (conversation) => {
      if (!conversation?.members?.length) return ''
      const activeId = String(activeUser.value?.id || '')
      const peer = conversation.members.find((item) => String(item.user_id) !== activeId)
      return String(peer?.user_id || '')
    }
    const directConversationMap = computed(() => {
      const map = new Map()
      directConversations.value.forEach((conversation) => {
        const peerId = getDirectPeerId(conversation)
        if (peerId) map.set(peerId, conversation)
      })
      return map
    })
    const directEntries = computed(() => {
      const existingByPeer = new Map()
      directConversations.value.forEach((conversation) => {
        const directUserId = getDirectPeerId(conversation)
        if (!directUserId) return
        const current = existingByPeer.get(String(directUserId))
        const currentTimestamp = current?.last_message?.created_at
          ? new Date(current.last_message.created_at).getTime()
          : new Date(current?.updated_at || current?.created_at || 0).getTime()
        const nextTimestamp = conversation?.last_message?.created_at
          ? new Date(conversation.last_message.created_at).getTime()
          : new Date(conversation?.updated_at || conversation?.created_at || 0).getTime()
        if (!current || nextTimestamp >= currentTimestamp) {
          existingByPeer.set(String(directUserId), {
            ...conversation,
            direct_user_id: directUserId,
            isPlaceholder: false
          })
        }
      })

      const existing = [...existingByPeer.values()]
      const usedPeerIds = new Set(existing.map((conversation) => String(conversation.direct_user_id || '')).filter(Boolean))
      const placeholders = availableDirectUsers.value
        .filter((user) => !usedPeerIds.has(String(user.id)))
        .sort((left, right) => String(left.full_name || '').localeCompare(String(right.full_name || ''), 'ru'))
        .map((user) => ({
          id: `placeholder:${user.id}`,
          type: 'direct',
          title: user.full_name || user.email || 'Пользователь',
          description: user.email || '',
          member_count: 2,
          members: [
            {
              user_id: user.id,
              user_name: user.full_name || user.email || 'Пользователь',
              user_email: user.email || ''
            }
          ],
          last_message: null,
          direct_user_id: String(user.id),
          isPlaceholder: true
        }))
      return [...existing, ...placeholders]
    })
    const forwardTargets = computed(() => conversations.value.filter((item) => String(item.id) !== ''))

    // Flat sidebar list: groups + real direct chats, sorted by last activity
    const sidebarSearch = ref('')
    const conversationTimestamp = (conversation) => {
      const last = conversation?.last_message?.created_at
      if (last) return new Date(last).getTime()
      return new Date(conversation?.updated_at || conversation?.created_at || 0).getTime()
    }
    const flatConversations = computed(() => {
      const realDirect = directEntries.value.filter((c) => !c.isPlaceholder)
      const all = [...groupConversations.value, ...realDirect]
      return all.sort((a, b) => conversationTimestamp(b) - conversationTimestamp(a))
    })
    const filteredFlatConversations = computed(() => {
      const q = sidebarSearch.value.trim().toLowerCase()
      if (!q) return flatConversations.value
      return flatConversations.value.filter((c) => {
        const haystack = [
          c.title || '',
          c.description || '',
          c.last_message?.body || ''
        ].join(' ').toLowerCase()
        return haystack.includes(q)
      })
    })
    const threadAvatarStyle = computed(() => (
      activeConversation.value?.type === 'direct'
        ? (getConversationUserAvatarUrl(activeConversation.value) ? null : getAvatarStyle(activeConversation.value.title))
        : null
    ))

    const isInlineImage = (file = {}) => {
      const contentType = String(file.content_type || file.type || '').toLowerCase()
      if (INLINE_IMAGE_TYPES.has(contentType)) return true
      const name = String(file.name || '').toLowerCase()
      return INLINE_IMAGE_EXTENSIONS.some((ext) => name.endsWith(ext))
    }

    // Phase A.1 — inline-видео. mp4/webm играем прямо в бабблe, не
    // выкидываем как download-карточку. preload="metadata" грузит
    // только заголовки до play — никакого автотрафика.
    //
    // MIME имеет приоритет над расширением. Phase D.2 voice messages
    // используют контейнер `.webm`/`.ogg` — но с MIME audio/webm, и
    // НЕ должны попадать сюда. Поэтому если content_type явно audio/* —
    // возвращаем false до проверки расширения.
    const isInlineVideo = (file = {}) => {
      const contentType = String(file.content_type || file.type || '').toLowerCase()
      if (contentType.startsWith('video/')) return true
      if (contentType.startsWith('audio/')) return false
      const name = String(file.name || '').toLowerCase()
      return ['.mp4', '.webm', '.ogg', '.mov', '.m4v'].some((ext) => name.endsWith(ext))
    }

    // Phase D.2 — inline-аудио. Голосовые сообщения от MediaRecorder
    // приходят как audio/webm или audio/mp4. Рендерим встроенный
    // <audio controls preload="metadata"> вместо download-карточки.
    // Распознавание по MIME (надёжно) + расширению (страховка для
    // случаев когда MIME отсутствует; .webm/.ogg ambiguous, но если
    // браузер не выставил MIME — не угадаешь).
    const isInlineAudio = (file = {}) => {
      const contentType = String(file.content_type || file.type || '').toLowerCase()
      if (contentType.startsWith('audio/')) return true
      if (contentType.startsWith('video/')) return false
      const name = String(file.name || '').toLowerCase()
      return ['.mp3', '.wav', '.oga', '.m4a', '.weba', '.opus', '.aac'].some((ext) => name.endsWith(ext))
    }

    // Phase D.3 — рендер @-mentions в теле сообщения.
    // На вход: body + mentions (расширенный формат: массив объектов
    // {kind, id, label, href} ИЛИ массив строк-user_id для legacy).
    // На выход: массив сегментов [{type:'text',value} | {type:'mention',label,href}],
    // которые шаблон отрендерит через v-for + <router-link>.
    //
    // Алгоритм: для каждого расширенного mention'а ищем в body первое
    // вхождение `@label` (как substring) — если нашли, разрезаем body
    // на куски и помечаем mention. Жадно слева-направо. Если label
    // не найден (например, юзер вручную поправил текст) — пропускаем.
    // Legacy string-mentions (только user_id) не рендерим ссылкой —
    // у нас нет label, оставляем body как plain text.
    const renderMessageBody = (body, mentions) => {
      const text = String(body || '')
      if (!text) return []
      const extMentions = (mentions || [])
        .filter((m) => m && typeof m === 'object' && m.label)
        .map((m) => ({ ...m, label: String(m.label) }))
      if (!extMentions.length) return [{ type: 'text', value: text }]

      const segments = []
      let rest = text
      let consumed = 0
      // Делаем копию списка, чтобы каждый mention был использован
      // максимум один раз (защита от дублей одного и того же тега).
      const pool = extMentions.slice()

      while (pool.length) {
        // Ищем самое раннее вхождение любого `@label` из пула.
        let bestIdx = -1
        let bestPick = -1
        for (let i = 0; i < pool.length; i += 1) {
          const needle = `@${pool[i].label}`
          const at = rest.indexOf(needle)
          if (at >= 0 && (bestIdx < 0 || at < bestIdx)) {
            bestIdx = at
            bestPick = i
          }
        }
        if (bestPick < 0) break
        const m = pool[bestPick]
        const needle = `@${m.label}`
        // Текст до меншена
        if (bestIdx > 0) {
          segments.push({ type: 'text', value: rest.slice(0, bestIdx) })
        }
        // Defensive: старые сообщения (отправленные до фикса) могут иметь
        // href = /deals/<id>, а такого роутера в этом CRM нет — сделки
        // живут как ProjectDetail по /projects/<id>. Переписываем на лету.
        let href = m.href || ''
        if (href.startsWith('/deals/')) href = '/projects/' + href.slice('/deals/'.length)
        segments.push({
          type: 'mention',
          label: m.label,
          href,
          kind: m.kind || '',
          id: m.id || '',
        })
        rest = rest.slice(bestIdx + needle.length)
        consumed += bestIdx + needle.length
        pool.splice(bestPick, 1)
      }
      if (rest) segments.push({ type: 'text', value: rest })
      return segments
    }

    const messageImageAttachments = (message) => (message?.attachments || []).filter((file) => isInlineImage(file) && file.download_url)
    const messageVideoAttachments = (message) => (message?.attachments || []).filter((file) => isInlineVideo(file) && file.download_url)
    const messageAudioAttachments = (message) => (message?.attachments || []).filter((file) => isInlineAudio(file) && file.download_url)
    // Файлы — то, что НЕ inline-картинка, НЕ видео, НЕ аудио.
    const messageFileAttachments = (message) => (message?.attachments || []).filter(
      (file) => (!isInlineImage(file) && !isInlineVideo(file) && !isInlineAudio(file)) || !file.download_url
    )

    const openImageViewer = (file, sourceFiles = []) => {
      const mediaItems = (sourceFiles || []).filter((item) => isInlineImage(item) && item.download_url)
      if (!mediaItems.length) return

      imageViewerItems.value = mediaItems
      const nextIndex = mediaItems.findIndex((item) => item.download_url === file.download_url && item.name === file.name)
      activeImageIndex.value = nextIndex >= 0 ? nextIndex : 0
      imageViewerOpen.value = true
    }

    const closeImageViewer = () => {
      imageViewerOpen.value = false
      imageViewerItems.value = []
      activeImageIndex.value = 0
    }

    const showPreviousImage = () => {
      if (!imageViewerItems.value.length) return
      activeImageIndex.value = (activeImageIndex.value - 1 + imageViewerItems.value.length) % imageViewerItems.value.length
    }

    const showNextImage = () => {
      if (!imageViewerItems.value.length) return
      activeImageIndex.value = (activeImageIndex.value + 1) % imageViewerItems.value.length
    }

    const visibleMessages = computed(() => {
      const query = messageSearch.value.trim().toLowerCase()
      if (!query) return messages.value
      return messages.value.filter((message) => {
        const haystack = [
          message.body || '',
          message.user_name || '',
          message.reply_to_message?.body || '',
          message.forwarded_from_message?.body || '',
          (message.attachments || []).map((file) => file.name || '').join(' ')
        ].join(' ').toLowerCase()
        return haystack.includes(query)
      })
    })

    const GROUP_GAP_MS = 5 * 60 * 1000 // 5 минут — порог группировки соседних сообщений одного автора

    const messageFeed = computed(() => {
      const feed = []
      let lastDay = ''
      let lastAuthor = null
      let lastTime = 0
      const visible = visibleMessages.value

      // Stage 1: last_read_at приходит на activeConversation (per-user
      // state). Ищем первое сообщение от ДРУГОГО юзера, пришедшее
      // после моего last_read_at — туда поставим разделитель
      // «Новые сообщения». Если у меня нет last_read_at (первое
      // открытие) — анкор на первом не-моём сообщении (всё новое).
      const myId = String(activeUser.value?.id || '')
      const lastReadAt = activeConversation.value?.last_read_at
      let unreadAnchorIdx = -1
      const lastReadMs = lastReadAt ? new Date(lastReadAt).getTime() : 0
      for (let i = 0; i < visible.length; i += 1) {
        const m = visible[i]
        if (!m || !m.created_at) continue
        if (String(m.user_id || '') === myId) continue
        const ts = new Date(m.created_at).getTime()
        if (!lastReadMs || ts > lastReadMs) {
          unreadAnchorIdx = i
          break
        }
      }

      for (let i = 0; i < visible.length; i += 1) {
        const message = visible[i]
        const date = message.created_at ? new Date(message.created_at) : null
        const dayKey = date ? date.toISOString().slice(0, 10) : 'unknown'
        if (dayKey !== lastDay) {
          lastDay = dayKey
          lastAuthor = null
          lastTime = 0
          feed.push({ type: 'day', key: `day-${dayKey}`, label: formatDayChip(message.created_at) })
        }

        if (i === unreadAnchorIdx) {
          feed.push({ type: 'unread', key: `unread-${message.id}` })
        }

        const author = String(message.user_id || '')
        const time = date ? date.getTime() : 0

        // Группировка: сообщение «первое в группе», если автор сменился
        // или прошло >5 мин с предыдущего. «Последнее в группе» —
        // если у следующего другой автор / >5мин позже / смена дня.
        const isFirstFromAuthor = author !== lastAuthor || (time - lastTime) > GROUP_GAP_MS
        const next = visible[i + 1]
        const nextDate = next?.created_at ? new Date(next.created_at) : null
        const nextDayKey = nextDate ? nextDate.toISOString().slice(0, 10) : ''
        const nextSameAuthor = next
          && String(next.user_id || '') === author
          && nextDate && date
          && (nextDate.getTime() - time) <= GROUP_GAP_MS
          && nextDayKey === dayKey
        const isLastFromAuthor = !nextSameAuthor

        feed.push({
          type: 'message',
          key: message.id,
          message,
          isFirstFromAuthor,
          isLastFromAuthor,
        })

        lastAuthor = author
        lastTime = time
      }
      return feed
    })

    const composerText = computed({
      get: () => (isEditMode.value ? editingBody.value : draft.value),
      set: (value) => {
        if (isEditMode.value) editingBody.value = value
        else draft.value = value
      }
    })

    const submitDisabled = computed(() => {
      if (sending.value || !activeConversation.value) return true
      if (isEditMode.value) return !editingBody.value.trim()
      return !draft.value.trim() && !pendingFiles.value.length
    })

    const syncMobilePane = () => {
      if (!isCompactMessenger.value) return
      if (!activeConversation.value) {
        mobilePane.value = 'contacts'
        detailsOpen.value = false
        return
      }
      mobilePane.value = detailsOpen.value ? 'info' : 'chat'
    }

    const closeConfirm = () => {
      confirmModalOpen.value = false
      confirmTitle.value = ''
      confirmText.value = ''
      confirmAction.value = null
    }

    const showConfirm = (title, text, action) => {
      confirmTitle.value = title
      confirmText.value = text
      confirmAction.value = action
      confirmModalOpen.value = true
    }

    const executeConfirm = async () => {
      const action = confirmAction.value
      closeConfirm()
      if (action) await action()
    }

    const focusComposer = () => {
      nextTick(() => composerInputRef.value?.focus())
    }

    const syncComposerHeight = () => {
      const textarea = composerInputRef.value
      if (!textarea) return
      textarea.style.height = '0px'
      textarea.style.height = `${Math.min(Math.max(textarea.scrollHeight, 28), 132)}px`
    }

    const requestAutoScroll = () => {
      autoScrollPending.value = true
    }

    const scrollThreadToBottom = async (force = false) => {
      await nextTick()
      const element = listRef.value
      if (!element) return
      if (!force && !autoScrollPending.value && !userNearBottom.value) return
      element.scrollTop = element.scrollHeight
      autoScrollPending.value = false
      userNearBottom.value = true
      markConversationSeen(activeConversationId.value, messages.value)
    }

    const onThreadScroll = () => {
      const element = listRef.value
      if (!element) return
      const offset = element.scrollHeight - (element.scrollTop + element.clientHeight)
      userNearBottom.value = offset <= 96
      if (userNearBottom.value) {
        markConversationSeen(activeConversationId.value, messages.value)
      }
    }

    const refreshAll = async () => {
      requestAutoScroll()
      await loadConversations({ preferredId: activeConversationId.value })
      if (activeConversationId.value) {
        await loadMessages(activeConversationId.value)
      }
      await scrollThreadToBottom(true)
    }

    const openConversation = async (conversationId) => {
      requestAutoScroll()
      await selectConversation(conversationId)
      if (isCompactMessenger.value) mobilePane.value = 'chat'
      await scrollThreadToBottom(true)
    }

    const isDirectEntryActive = (entry) => {
      if (!entry) return false
      if (!entry.isPlaceholder) return String(entry.id) === String(activeConversationId.value)
      if (!activeConversation.value || activeConversation.value.type !== 'direct') return false
      return String(entry.direct_user_id || '') === String(getDirectPeerId(activeConversation.value))
    }

    const openDirectConversation = async (entry) => {
      if (!entry) return
      requestAutoScroll()
      if (entry.isPlaceholder && entry.direct_user_id) {
        await createDirectConversation(entry.direct_user_id)
      } else {
        await selectConversation(entry.id)
      }
      if (isCompactMessenger.value) mobilePane.value = 'chat'
      await scrollThreadToBottom(true)
    }

    const syncConversationFromRoute = async () => {
      const targetId = String(route.query.conversation || '').trim()
      if (!targetId || !conversations.value.length) return
      const exists = conversations.value.some((item) => String(item.id) === targetId)
      if (!exists) {
        routeConversationResolved.value = true
        return
      }
      if (String(activeConversationId.value) !== targetId) {
        requestAutoScroll()
        await selectConversation(targetId, { silent: true })
        if (isCompactMessenger.value) mobilePane.value = 'chat'
        await scrollThreadToBottom(true)
      }
      routeConversationResolved.value = true
    }

    const getUserAvatarUrl = (user) => {
      return normalizeAvatarUrl(user?.avatar_url || '', user?.id || '')
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

    const getUserRecord = (userId) => userDirectory.value[String(userId || '')] || null

    const getConversationUserAvatarUrl = (conversation) => {
      const userId = conversation?.direct_user_id || getDirectPeerId(conversation)
      return getUserAvatarUrl(getUserRecord(userId))
    }

    const getMessageAvatarUrl = (message) => getUserAvatarUrl(getUserRecord(message?.user_id))

    const getMemberAvatarUrl = (member) => getUserAvatarUrl(getUserRecord(member?.user_id))

    const toggleMessageSearch = async () => {
      messageSearchOpen.value = !messageSearchOpen.value
      if (!messageSearchOpen.value) messageSearch.value = ''
      await nextTick()
      if (userNearBottom.value) await scrollThreadToBottom(true)
    }

    // Phase D.1 — глобальный поиск по сообщениям (sidebar panel).
    // Debounce 300мс: пока юзер печатает — таймер сбрасывается, запрос
    // уходит только после паузы. Меньше нагрузки на бэк и меньше
    // мерцания в UI.
    let _globalSearchDebounce = null
    const toggleGlobalMessageSearch = () => {
      if (messageSearchPanelOpen.value) {
        closeMessageSearchPanel()
      } else {
        openMessageSearchPanel()
      }
    }

    const onGlobalSearchInput = (value) => {
      const next = String(value || '')
      messageSearchQuery.value = next
      if (_globalSearchDebounce) clearTimeout(_globalSearchDebounce)
      // Если пусто — не зовём backend; синхронно очищаем.
      if (!next.trim()) {
        runMessageSearch('')
        return
      }
      _globalSearchDebounce = setTimeout(() => {
        runMessageSearch(next)
        _globalSearchDebounce = null
      }, 300)
    }

    // Иконка для группы результатов по chat-типу.
    const searchResultGroupIcon = (group) => {
      const t = String(group?.conversation_type || '')
      if (t === 'direct') return 'fa-user'
      if (t === 'channel') return 'fa-bullhorn'
      if (t === 'global') return 'fa-shopping-bag'
      return 'fa-users'
    }

    // Клик по результату: открываем chat, ждём загрузки сообщений,
    // прыгаем на сообщение с highlight. Если найдено в другом чате —
    // подгружаем; если в текущем — просто скроллим.
    const openSearchResult = async (item) => {
      if (!item?.conversation_id || !item?.message_id) return
      const targetCid = String(item.conversation_id)
      const targetMid = String(item.message_id)
      // Закрываем панель — UX: result выбран, юзер хочет читать чат.
      closeMessageSearchPanel()
      if (String(activeConversationId.value) !== targetCid) {
        await openConversation(targetCid)
      }
      // Сообщение могло уйти за пределы первой страницы listMessages
      // (load 500). Сейчас — best-effort scroll. Если позже на больших
      // чатах появятся «пропуски» — добавим явный fetch around messageId.
      await nextTick()
      // Дать DOM время отрисоваться: scrollToMessage сам делает
      // getElementById, если узла нет — тихо вернётся; в этом случае
      // пробуем ещё раз через 300мс.
      let attempts = 0
      const tryScroll = () => {
        const el = document.getElementById(`message-${targetMid}`)
        if (el) {
          scrollToMessage(targetMid)
          return
        }
        attempts += 1
        if (attempts < 4) setTimeout(tryScroll, 250)
      }
      tryScroll()
    }

    const toggleDetails = async () => {
      detailsOpen.value = !detailsOpen.value
      if (isCompactMessenger.value && activeConversation.value) {
        mobilePane.value = detailsOpen.value ? 'info' : 'chat'
      }
      await nextTick()
      if (userNearBottom.value) await scrollThreadToBottom(true)
    }

    const closeDetails = async () => {
      detailsOpen.value = false
      if (isCompactMessenger.value) {
        mobilePane.value = activeConversation.value ? 'chat' : 'contacts'
      }
      await nextTick()
      if (userNearBottom.value) await scrollThreadToBottom(true)
    }

    const setMobilePane = (pane) => {
      if (!isCompactMessenger.value) return
      mobilePane.value = pane
      detailsOpen.value = pane === 'info'
      if (pane === 'contacts') {
        messageSearchOpen.value = false
      }
    }

    const toggleSection = (key) => {
      detailSections.value[key] = !detailSections.value[key]
    }

    const triggerFilePicker = () => {
      openFilePicker(fileInput.value)
    }

    // Phase D.2 — голосовые сообщения (MediaRecorder).
    // Воркфлоу:
    //   click microphone → запрашиваем getUserMedia({audio})
    //     ↳ если отказ — toastError, состояние не меняется
    //     ↳ если ok — стартуем MediaRecorder, тикаем duration
    //   click stop → останавливаем recorder, audio blob → File →
    //     appendPendingFiles → юзер видит в pendingFiles + может
    //     отправить кнопкой send (как обычный аттач)
    //   click cancel → останавливаем, отбрасываем blob
    //
    // Формат: MediaRecorder сам выбирает поддерживаемый container
    // (Chrome/FF — audio/webm с opus; Safari — audio/mp4 с aac).
    // Backend принимает любой content_type (existing _store_attachments).
    const isRecording = ref(false)
    const recordingDuration = ref(0)  // в секундах, для UI таймера
    let _mediaRecorder = null
    let _mediaStream = null
    let _recordedChunks = []
    let _durationTimer = null
    let _recordingCancelled = false

    const _pickAudioMime = () => {
      // Предпочтительный порядок: opus в webm (лучшее качество/размер),
      // затем mp4/aac (Safari), затем дефолт MediaRecorder'а.
      if (typeof MediaRecorder === 'undefined' || !MediaRecorder.isTypeSupported) return ''
      const candidates = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
        'audio/mp4',
      ]
      for (const mime of candidates) {
        try {
          if (MediaRecorder.isTypeSupported(mime)) return mime
        } catch (e) {
          // ignore
        }
      }
      return ''
    }

    const _resetRecorderState = () => {
      isRecording.value = false
      recordingDuration.value = 0
      _recordedChunks = []
      _recordingCancelled = false
      if (_durationTimer) {
        clearInterval(_durationTimer)
        _durationTimer = null
      }
      if (_mediaStream) {
        try {
          _mediaStream.getTracks().forEach((t) => t.stop())
        } catch (e) {
          // ignore
        }
        _mediaStream = null
      }
      _mediaRecorder = null
    }

    const startRecording = async () => {
      if (isRecording.value) return
      if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
        toastError('Браузер не поддерживает запись с микрофона')
        return
      }
      if (typeof MediaRecorder === 'undefined') {
        toastError('Браузер не поддерживает MediaRecorder')
        return
      }
      let stream
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      } catch (err) {
        // NotAllowedError / NotFoundError — отказ или нет микрофона.
        toastError('Не удалось получить доступ к микрофону')
        return
      }
      _mediaStream = stream
      _recordedChunks = []
      _recordingCancelled = false
      const mimeType = _pickAudioMime()
      try {
        _mediaRecorder = mimeType
          ? new MediaRecorder(stream, { mimeType })
          : new MediaRecorder(stream)
      } catch (err) {
        toastError('Не удалось запустить запись')
        _resetRecorderState()
        return
      }
      _mediaRecorder.addEventListener('dataavailable', (event) => {
        if (event.data && event.data.size > 0) _recordedChunks.push(event.data)
      })
      _mediaRecorder.addEventListener('stop', () => {
        const wasCancelled = _recordingCancelled
        const chunks = _recordedChunks.slice()
        const recorderMime = _mediaRecorder?.mimeType || mimeType || 'audio/webm'
        _resetRecorderState()
        if (wasCancelled || !chunks.length) return
        const blob = new Blob(chunks, { type: recorderMime })
        // Имя: voice_YYYYMMDD_HHMMSS.<ext>
        const ext = recorderMime.includes('mp4')
          ? 'm4a'
          : recorderMime.includes('ogg')
            ? 'ogg'
            : 'webm'
        const ts = new Date()
        const pad = (n) => String(n).padStart(2, '0')
        const stamp =
          `${ts.getFullYear()}${pad(ts.getMonth() + 1)}${pad(ts.getDate())}` +
          `_${pad(ts.getHours())}${pad(ts.getMinutes())}${pad(ts.getSeconds())}`
        const file = new File([blob], `voice_${stamp}.${ext}`, { type: recorderMime })
        appendPendingFiles([file])
      })
      _mediaRecorder.start()
      isRecording.value = true
      recordingDuration.value = 0
      // Таймер длительности — на UI отображаем «0:03».
      _durationTimer = setInterval(() => {
        recordingDuration.value += 1
      }, 1000)
    }

    const stopRecording = () => {
      if (!isRecording.value || !_mediaRecorder) return
      try {
        _mediaRecorder.stop()
      } catch (e) {
        _resetRecorderState()
      }
    }

    const cancelRecording = () => {
      if (!isRecording.value || !_mediaRecorder) {
        _resetRecorderState()
        return
      }
      _recordingCancelled = true
      try {
        _mediaRecorder.stop()
      } catch (e) {
        _resetRecorderState()
      }
    }

    const recordingDurationLabel = computed(() => {
      const total = recordingDuration.value
      const m = Math.floor(total / 60)
      const s = total % 60
      return `${m}:${String(s).padStart(2, '0')}`
    })

    // Безопасность: если юзер закрыл вкладку или сменил чат во время
    // записи — гасим recorder, чтобы микрофон не остался активным.
    onBeforeUnmount(() => {
      if (isRecording.value) cancelRecording()
    })
    watch(activeConversationId, () => {
      if (isRecording.value) cancelRecording()
    })

    const submitComposer = async () => {
      if (isEditMode.value) {
        const updated = await saveEdit(messages.value.find((item) => item.id === editingId.value))
        if (updated) toastSuccess('Сообщение обновлено')
      } else {
        await sendMessage()
      }
      requestAutoScroll()
      await scrollThreadToBottom(true)
      syncComposerHeight()
      focusComposer()
    }

    const replyToMessage = (message) => {
      startReply(message)
      focusComposer()
    }

    const startEditing = (message) => {
      startEdit(message)
      nextTick(() => {
        syncComposerHeight()
        focusComposer()
      })
    }

    const askDelete = (message) => {
      showConfirm('Удалить сообщение?', 'Сообщение будет помечено как удаленное в истории чата.', async () => {
        await deleteMessage(message)
      })
    }

    const askRemoveMember = (member) => {
      showConfirm('Удалить участника?', `${member.user_name} будет удален из этого чата.`, async () => {
        await removeConversationMember(member.user_id)
      })
    }

    const togglePin = async (message) => {
      if (message.is_pinned) await unpinMessage(message)
      else await pinMessage(message)
    }

    const copyMessage = async (message) => {
      const payload = message.body || messageExcerpt(message)
      if (!payload) return
      try {
        await navigator.clipboard.writeText(payload)
        toastSuccess('Скопировано в буфер обмена')
      } catch (error) {
        toastInfo('Скопируйте сообщение вручную')
      }
    }

    const openForwardModal = (message) => {
      forwardingMessage.value = message
      forwardModalOpen.value = true
    }

    const closeForwardModal = () => {
      forwardModalOpen.value = false
      forwardingMessage.value = null
    }

    const submitForward = async (conversationId) => {
      if (!forwardingMessage.value) return
      await forwardMessage(forwardingMessage.value, conversationId)
      closeForwardModal()
    }

    const openConversationModal = () => {
      renameMode.value = false
      conversationForm.value = { type: 'direct', title: '', description: '', directUserId: '', memberIds: [] }
      writeColleagueSearch.value = ''
      showConversationModal.value = true
      // Stage 1: подтягиваем список юзеров для inline-поиска. Ленивая
      // загрузка — не пытаемся обновить, если список уже есть.
      if (!searchableUsers.value?.length) {
        loadSearchableUsers()
      }
    }

    // Stage 1: клик по карточке юзера в «написать коллеге» — открываем
    // существующий DM (если has_dm=true) или создаём новый. Закрываем
    // модал сразу.
    const pickColleagueAndOpen = async (user) => {
      if (!user || !user.id) return
      try {
        if (user.has_dm && user.dm_conversation_id) {
          await selectConversation(user.dm_conversation_id, { silent: true })
        } else {
          await createDirectConversation(user.id)
        }
      } finally {
        showConversationModal.value = false
      }
    }

    // Per-card actions ----------------------------------------------------

    const toggleCardMenu = (conversation) => {
      const id = String(conversation?.id || '')
      if (openCardMenuId.value === id) {
        openCardMenuId.value = null
      } else {
        openCardMenuId.value = id
      }
    }

    const closeCardMenuOnDocumentClick = (event) => {
      const t = event.target
      if (openCardMenuId.value) {
        if (!t || !t.closest || (!t.closest('.conversation-card__menu') && !t.closest('.conversation-card__menu-btn'))) {
          openCardMenuId.value = null
        }
      }
      // Phase B.3: то же самое для reaction-picker.
      if (reactionPickerOpenFor.value) {
        if (!t || !t.closest || (!t.closest('.message-bubble__reaction-picker') && !t.closest('.message-row__actions'))) {
          reactionPickerOpenFor.value = null
        }
      }
    }

    const archiveCard = async (conversation) => {
      const id = String(conversation?.id || '')
      if (!id) return
      openCardMenuId.value = null
      await archiveConversationForMe(id)
      toastSuccess('Чат скрыт из списка')
    }

    const muteCardForever = async (conversation) => {
      const id = String(conversation?.id || '')
      if (!id) return
      openCardMenuId.value = null
      await muteConversationForever(id)
    }

    const unmuteCard = async (conversation) => {
      const id = String(conversation?.id || '')
      if (!id) return
      openCardMenuId.value = null
      await unmuteConversation(id)
    }

    // Phase C.2: online-status helper.
    // online: last_seen <  2 минут назад → зелёная точка
    // recent: 2–10 минут        → жёлтая точка
    // offline: >10 минут / null → точку не рисуем
    const presenceStatus = (lastSeenAt) => {
      if (!lastSeenAt) return 'offline'
      try {
        const ageMs = Date.now() - new Date(lastSeenAt).getTime()
        if (ageMs < 0) return 'online'
        if (ageMs < 2 * 60 * 1000) return 'online'
        if (ageMs < 10 * 60 * 1000) return 'recent'
        return 'offline'
      } catch (e) {
        return 'offline'
      }
    }

    // Для DM-конвера: статус собеседника. Глобал/группа — null
    // (групповой presence — отдельная задача Stage E).
    const conversationPresenceStatus = (conversation) => {
      if (!conversation || conversation.type !== 'direct') return 'offline'
      return presenceStatus(conversation.peer_last_seen_at)
    }

    // Phase C.1: humanized "X печатает..." / "X и Y печатают..." /
    // "X, Y и ещё 2 печатают...".
    const typingHumanText = computed(() => {
      const list = typingUsers.value || []
      if (!list.length) return ''
      const names = list.map((u) => u.user_name || 'Кто-то').filter(Boolean)
      if (!names.length) return 'Печатает…'
      if (names.length === 1) return `${names[0]} печатает…`
      if (names.length === 2) return `${names[0]} и ${names[1]} печатают…`
      return `${names[0]}, ${names[1]} и ещё ${names.length - 2} печатают…`
    })

    // Phase B.3: emoji reactions presets + picker state.
    const REACTION_PRESETS = ['👍', '❤️', '😂', '🎉', '🔥', '👏', '😮', '😢']
    const reactionPickerOpenFor = ref(null)

    const openReactionPicker = (message) => {
      reactionPickerOpenFor.value = String(message?.id || '')
    }
    const closeReactionPicker = () => {
      reactionPickerOpenFor.value = null
    }
    const applyReaction = async (messageId, emoji) => {
      closeReactionPicker()
      await toggleMessageReaction(messageId, emoji)
    }

    // Phase B.1: pin / unpin
    const pinCard = async (conversation) => {
      const id = String(conversation?.id || '')
      if (!id) return
      openCardMenuId.value = null
      await pinConversation(id)
    }

    const unpinCard = async (conversation) => {
      const id = String(conversation?.id || '')
      if (!id) return
      openCardMenuId.value = null
      await unpinConversation(id)
    }

    const openRenameModal = () => {
      if (!activeConversation.value) return
      renameMode.value = true
      conversationForm.value = {
        type: activeConversation.value.type,
        title: activeConversation.value.title || '',
        description: activeConversation.value.description || '',
        directUserId: '',
        memberIds: []
      }
      showConversationModal.value = true
    }

    const closeConversationModal = () => {
      showConversationModal.value = false
      renameMode.value = false
    }

    const submitConversationModal = async () => {
      if (renameMode.value) {
        const updated = await updateConversation({
          title: conversationForm.value.title,
          description: conversationForm.value.description
        })
        if (updated) closeConversationModal()
        return
      }

      if (conversationForm.value.type === 'direct') {
        const created = await createDirectConversation(conversationForm.value.directUserId)
        if (created) closeConversationModal()
      } else {
        const created = await createConversation({
          type: conversationForm.value.type,
          title: conversationForm.value.title,
          description: conversationForm.value.description,
          member_ids: conversationForm.value.memberIds
        })
        if (created) closeConversationModal()
      }
    }

    const submitAddMembers = async () => {
      const updated = await addConversationMembers(addMembersSelection.value)
      if (updated) {
        addMembersSelection.value = []
        addMembersModalOpen.value = false
      }
    }

    const insertLinkToken = () => {
      composerText.value = `${composerText.value || ''}${composerText.value ? ' ' : ''}https://`
      focusComposer()
      nextTick(syncComposerHeight)
    }

    const insertEmoji = () => {
      composerText.value = `${composerText.value || ''} :)`
      focusComposer()
      nextTick(syncComposerHeight)
    }

    // Phase B.4 — @-mention autocomplete в composer'е.
    // При вводе текста проверяем, есть ли активный «@» (символ перед
    // курсором, за которым идут не-пробельные символы). Если есть —
    // фетчим /mention-search и показываем dropdown.
    const mentionAutoOpen = ref(false)
    const mentionAutoQuery = ref('')
    const mentionAutoResults = ref([])
    const mentionAutoStart = ref(-1)   // позиция «@» в тексте
    const mentionAutoActiveIdx = ref(0) // курсор в результатах (для ↑↓ Enter)
    let _mentionFetchTimer = null

    const _detectMentionTrigger = () => {
      const inputEl = composerInputRef.value
      if (!inputEl) return null
      const text = composerText.value || ''
      const caret = inputEl.selectionStart ?? text.length
      // Найти последний '@' до курсора, у которого слева пробел/начало.
      let i = caret - 1
      while (i >= 0) {
        const ch = text[i]
        if (ch === '@') {
          const prev = i > 0 ? text[i - 1] : ''
          if (i === 0 || /\s/.test(prev)) {
            return { at: i, query: text.slice(i + 1, caret) }
          }
          return null
        }
        if (/\s/.test(ch)) return null
        i -= 1
      }
      return null
    }

    const _fetchMentionResults = async (q) => {
      if (_mentionFetchTimer) clearTimeout(_mentionFetchTimer)
      _mentionFetchTimer = setTimeout(async () => {
        try {
          const data = await import('../services/api/messenger').then((m) => m.mentionSearch(q))
          mentionAutoResults.value = Array.isArray(data) ? data : []
          mentionAutoActiveIdx.value = 0
        } catch (e) {
          mentionAutoResults.value = []
        }
      }, 180)
    }

    const onComposerInput = () => {
      syncComposerHeight()
      // Phase C.1: typing signal (debounced 1с в composable).
      noteUserTyping()
      const trig = _detectMentionTrigger()
      if (trig && trig.query.length >= 0) {
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

    const closeMentionAutocomplete = () => {
      mentionAutoOpen.value = false
      mentionAutoResults.value = []
      mentionAutoStart.value = -1
    }

    const pickMentionAutoItem = (item) => {
      if (!item || mentionAutoStart.value < 0) {
        closeMentionAutocomplete()
        return
      }
      const text = composerText.value || ''
      const start = mentionAutoStart.value
      // заменяем «@query» на «@label »
      const inputEl = composerInputRef.value
      const caret = inputEl?.selectionStart ?? text.length
      const before = text.slice(0, start)
      const after = text.slice(caret)
      const insert = `@${item.label} `
      composerText.value = `${before}${insert}${after}`
      // Phase D.3: запоминаем структурированный mention (kind/id/label/href)
      // в selectedMentions — пойдёт на бэк как объект, renderer сделает
      // из @label кликабельную ссылку.
      selectedMentions.value = [
        ...selectedMentions.value,
        {
          kind: item.kind,
          id: item.id,
          label: item.label,
          href: item.href || '',
          name: item.label, // backward compat: старый renderer ждал .name
        },
      ]
      closeMentionAutocomplete()
      nextTick(() => {
        const el = composerInputRef.value
        if (el && el.focus) {
          el.focus()
          const newCaret = before.length + insert.length
          try { el.setSelectionRange(newCaret, newCaret) } catch (e) { /* ignore */ }
        }
      })
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

    const onComposerPaste = (event) => {
      if (isEditMode.value) return

      const clipboardItems = Array.from(event?.clipboardData?.items || [])
      if (!clipboardItems.length) return

      const imageFiles = clipboardItems
        .filter((item) => item.kind === 'file' && String(item.type || '').toLowerCase().startsWith('image/'))
        .map((item) => item.getAsFile())
        .filter(Boolean)

      if (!imageFiles.length) return

      event.preventDefault()

      const { added, skipped } = appendPendingFiles(imageFiles, { clipboardOnlyImages: true }) || { added: 0, skipped: 0 }
      if (added > 0) {
        toastInfo(added > 1 ? 'Скриншоты добавлены в сообщение' : 'Скриншот добавлен в сообщение')
      }
      if (skipped > 0) {
        toastInfo('Из буфера обмена добавляются только безопасные изображения PNG, JPG, WEBP или GIF')
      }
    }

    // Phase A.4 — jump-to-message: после scrollIntoView ставим
    // highlighted-класс на 2 секунды, чтобы юзер визуально нашёл
    // прыжок (особенно если контент похожий и target слегка вне поля).
    let _highlightTimer = null
    const highlightedMessageId = ref(null)
    const scrollToMessage = (messageId) => {
      const target = document.getElementById(`message-${messageId}`)
      if (!target) return
      target.scrollIntoView({ block: 'center', behavior: 'smooth' })
      highlightedMessageId.value = String(messageId)
      if (_highlightTimer) clearTimeout(_highlightTimer)
      _highlightTimer = setTimeout(() => {
        highlightedMessageId.value = null
        _highlightTimer = null
      }, 2000)
    }

    const scrollToPinned = () => {
      if (pinnedMessage.value?.id) scrollToMessage(pinnedMessage.value.id)
    }

    const messageActionsVisible = (message) => hoveredMessageId.value === message.id && !message.is_deleted

    // Phase B.2: read-receipt logic.
    // Возвращает true, если моё сообщение было прочитано собеседником
    // (в DM-чате). Для group/global сейчас всегда false — нет
    // peer_last_read_at, ticks деградируют до «доставлено» (✓).
    const isMessageRead = (message) => {
      if (!message?.created_at) return false
      if (activeConversation.value?.type !== 'direct') return false
      const peerReadAt = activeConversation.value?.peer_last_read_at
      if (!peerReadAt) return false
      try {
        return new Date(peerReadAt).getTime() >= new Date(message.created_at).getTime()
      } catch (e) {
        return false
      }
    }

    const messageSignature = computed(() =>
      messages.value
        .map((message) => `${message.id}:${message.updated_at || message.edited_at || message.created_at}:${message.is_deleted ? 1 : 0}:${message.is_pinned ? 1 : 0}`)
        .join('|')
    )

    watch(messageSignature, async (nextValue, previousValue) => {
      if (!nextValue) return
      const shouldStick = autoScrollPending.value || userNearBottom.value || !previousValue
      await nextTick()
      if (shouldStick) await scrollThreadToBottom(true)
    })

    watch(() => composerText.value, async () => {
      await nextTick()
      syncComposerHeight()
    })

    watch(activeConversationId, async (value) => {
      if (!value) {
        syncMobilePane()
        return
      }
      const routeConversationId = String(route.query.conversation || '').trim()
      if (!routeConversationId || routeConversationResolved.value || routeConversationId === String(value)) {
        if (routeConversationId !== String(value)) {
          router.replace({
            query: {
              ...route.query,
              conversation: String(value)
            }
          })
        }
      }
      requestAutoScroll()
      syncMobilePane()
      await nextTick()
      await scrollThreadToBottom(true)
    })

    watch(
      () => route.query.conversation,
      async () => {
        routeConversationResolved.value = false
        await syncConversationFromRoute()
      },
      { immediate: true }
    )

    watch(
      () => conversations.value.map((item) => item.id).join('|'),
      async () => {
        await syncConversationFromRoute()
      }
    )

    watch(activeConversation, async (value) => {
      if (!isCompactMessenger.value) return
      if (!value) {
        mobilePane.value = 'contacts'
        detailsOpen.value = false
        return
      }
      if (detailsOpen.value) {
        mobilePane.value = 'info'
        return
      }
      if (mobilePane.value === 'contacts') {
        mobilePane.value = 'chat'
      }
    })

    const handleViewportResize = () => {
      viewportWidth.value = window.innerWidth
      syncMobilePane()
    }

    const handleViewerKeydown = (event) => {
      if (!imageViewerOpen.value) return
      if (event.key === 'Escape') {
        closeImageViewer()
      } else if (event.key === 'ArrowLeft') {
        showPreviousImage()
      } else if (event.key === 'ArrowRight') {
        showNextImage()
      }
    }

    onMounted(() => {
      handleViewportResize()
      window.addEventListener('resize', handleViewportResize, { passive: true })
      window.addEventListener('keydown', handleViewerKeydown)
      document.addEventListener('click', closeCardMenuOnDocumentClick)
    })

    onBeforeUnmount(() => {
      window.removeEventListener('resize', handleViewportResize)
      window.removeEventListener('keydown', handleViewerKeydown)
      document.removeEventListener('click', closeCardMenuOnDocumentClick)
    })

    return {
      loading,
      loadingMessages,
      savingConversation,
      sending,
      conversations,
      activeConversationId,
      activeConversation,
      users,
      messages,
      members,
      files,
      links,
      pendingFiles,
      mentionPickerOpen,
      mentionQuery,
      mentionOptions,
      selectedMentions,
      editingId,
      replyTarget,
      isEditMode,
      canManageMembers,
      isConversationUnread,
      conversationUnreadCount,
      isConversationMuted,
      isConversationArchived,
      isConversationPinned,
      typingUsers,
      writeColleagueSearch,
      loadingSearchableUsers,
      filteredSearchableUsers,
      openCardMenuId,
      composerDragOver,
      onComposerDragEnter,
      onComposerDragOver,
      onComposerDragLeave,
      onComposerDrop,
      highlightedMessageId,
      visibleMessages,
      groupsOpen,
      directOpen,
      messageSearchOpen,
      messageSearch,
      messageSearchPanelOpen,
      messageSearchQuery,
      messageSearchResults,
      messageSearchResultsByChat,
      messageSearchLoading,
      toggleGlobalMessageSearch,
      onGlobalSearchInput,
      openSearchResult,
      searchResultGroupIcon,
      detailsOpen,
      mobilePane,
      activeMobilePane,
      isCompactMessenger,
      hoveredMessageId,
      detailSections,
      imageViewerOpen,
      imageViewerItems,
      activeImageItem,
      confirmModalOpen,
      confirmTitle,
      confirmText,
      showConversationModal,
      renameMode,
      addMembersModalOpen,
      addMembersSelection,
      forwardModalOpen,
      conversationForm,
      groupConversations,
      directConversations,
      directEntries,
      sidebarSearch,
      flatConversations,
      filteredFlatConversations,
      pinnedMessage,
      subtitleText,
      availableDirectUsers,
      availableUsersToAdd,
      forwardTargets,
      composerText,
      submitDisabled,
      listRef,
      fileInput,
      composerInputRef,
      isOwn,
      canEdit,
      formatDateTime,
      formatMessageTime,
      formatSize,
      isMessageRead,
      toggleMessageReaction,
      refreshAll,
      openConversation,
      openDirectConversation,
      isDirectEntryActive,
      toggleMessageSearch,
      toggleDetails,
      closeDetails,
      setMobilePane,
      toggleSection,
      triggerFilePicker,
      isRecording,
      recordingDurationLabel,
      startRecording,
      stopRecording,
      cancelRecording,
      onFilesPicked,
      removeFile,
      toggleMentions,
      addMention,
      removeMention,
      submitComposer,
      replyToMessage,
      cancelReply,
      startEditing,
      cancelEdit,
      askDelete,
      askRemoveMember,
      togglePin,
      copyMessage,
      openForwardModal,
      closeForwardModal,
      submitForward,
      openConversationModal,
      openRenameModal,
      closeConversationModal,
      submitConversationModal,
      pickColleagueAndOpen,
      toggleCardMenu,
      archiveCard,
      muteCardForever,
      unmuteCard,
      pinCard,
      unpinCard,
      REACTION_PRESETS,
      reactionPickerOpenFor,
      openReactionPicker,
      closeReactionPicker,
      applyReaction,
      mentionAutoOpen,
      mentionAutoResults,
      mentionAutoActiveIdx,
      pickMentionAutoItem,
      onComposerKeydownMention,
      typingHumanText,
      conversationPresenceStatus,
      submitAddMembers,
      insertLinkToken,
      insertEmoji,
      isInlineImage,
      isInlineVideo,
      isInlineAudio,
      renderMessageBody,
      messageImageAttachments,
      messageVideoAttachments,
      messageAudioAttachments,
      messageFileAttachments,
      mediaItems,
      documentItems,
      openImageViewer,
      closeImageViewer,
      showPreviousImage,
      showNextImage,
      onComposerInput,
      onComposerPaste,
      closeConfirm,
      executeConfirm,
      onThreadScroll,
      scrollToPinned,
      scrollToMessage,
      messageActionsVisible,
      messageFeed,
      messageExcerpt,
      extractMessageLinks,
      trimText,
      getMessageAuthor,
      getMessageInitial,
      getAvatarStyle,
      getAuthorColor,
      getInitial,
      conversationTypeLabel,
      memberRoleLabel,
      formatSidebarTime,
      conversationPreview,
      conversationAvatarClass,
      conversationHeaderIcon,
      threadAvatarStyle,
      getUserAvatarUrl,
      isAvatarBroken,
      markAvatarBroken,
      getConversationUserAvatarUrl,
      getMessageAvatarUrl,
      getMemberAvatarUrl,
      downloadAttachment
    }
  }
}

function trimText(text, maxLength = 48) {
  const value = String(text || '').trim()
  if (!value) return ''
  return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value
}

function messageExcerpt(message) {
  if (!message) return ''
  if (message.is_deleted) return 'Сообщение удалено'
  if (message.body) return trimText(message.body, 84)
  if (message.attachments?.length) return `Файлы: ${message.attachments.map((file) => file.name || 'файл').join(', ')}`
  if (message.forwarded_from_message?.body) return trimText(message.forwarded_from_message.body, 84)
  return 'Сообщение'
}

function extractMessageLinks(message) {
  const body = String(message?.body || '')
  const matches = body.match(URL_RE) || []
  return matches.map((url) => ({
    url,
    label: trimText(url.replace(/^https?:\/\//, ''), 30)
  }))
}

function formatDayChip(value) {
  if (!value) return 'Сегодня'
  try {
    return new Date(value).toLocaleDateString('ru-RU', { weekday: 'long', month: 'long', day: 'numeric' })
  } catch (error) {
    return value
  }
}

function getMessageAuthor(message) {
  return message?.user_name || 'Пользователь'
}

function getInitial(value) {
  return (String(value || '?').trim().charAt(0).toUpperCase() || '?')
}

function getMessageInitial(message) {
  return getInitial(getMessageAuthor(message))
}

function formatSidebarTime(value) {
  if (!value) return ''
  try {
    return new Date(value).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
  } catch (error) {
    return value
  }
}

function conversationPreview(conversation) {
  if (conversation?.isPlaceholder) return trimText(conversation?.description || '', 40) || 'Пока нет сообщений'
  return messageExcerpt(conversation?.last_message) || 'Пока нет сообщений'
}

function formatMembersCount(count) {
  const value = Number(count || 0)
  const mod10 = value % 10
  const mod100 = value % 100
  if (mod10 === 1 && mod100 !== 11) return `${value} участник`
  if ([2, 3, 4].includes(mod10) && ![12, 13, 14].includes(mod100)) return `${value} участника`
  return `${value} участников`
}

function conversationTypeLabel(type) {
  if (type === 'global') return 'Глобальный чат'
  if (type === 'direct') return 'Личный чат'
  if (type === 'group') return 'Группа'
  if (type === 'channel') return 'Канал'
  return 'Чат'
}

function memberRoleLabel(role) {
  if (role === 'owner') return 'Владелец'
  if (role === 'admin') return 'Администратор'
  if (role === 'member') return 'Участник'
  return role || 'Участник'
}

function conversationAvatarClass(conversation) {
  if (conversation?.type === 'direct') return 'conversation-card__avatar--user'
  return 'conversation-card__avatar--group'
}

function conversationHeaderIcon(conversation) {
  if (conversation?.type === 'channel') return 'fas fa-bullhorn'
  if (conversation?.type === 'global') return 'fas fa-shopping-bag'
  return 'fas fa-users'
}

function getAuthorColor(seed) {
  const palette = ['#2563eb', '#16a34a', '#d97706', '#dc2626', '#7c3aed', '#0891b2', '#db2777', '#65a30d']
  let hash = 0
  const source = String(seed || 'user')
  for (let i = 0; i < source.length; i += 1) hash = (hash * 31 + source.charCodeAt(i)) | 0
  return palette[Math.abs(hash) % palette.length]
}

function getAvatarStyle(seed, kind = 'user') {
  if (kind === 'self') {
    return {
      background: 'linear-gradient(135deg, #ffe9c2 0%, #f7d58e 100%)',
      color: '#7a4d08',
      boxShadow: '0 10px 20px rgba(247, 213, 142, 0.28)'
    }
  }

  const palette = [
    { background: 'linear-gradient(135deg, #d6ebff 0%, #bddcff 100%)', color: '#2176d7', boxShadow: '0 10px 20px rgba(63, 140, 255, 0.20)' },
    { background: 'linear-gradient(135deg, #ffe1e7 0%, #ffc1cd 100%)', color: '#c2415d', boxShadow: '0 10px 20px rgba(255, 95, 115, 0.18)' },
    { background: 'linear-gradient(135deg, #e6f7dd 0%, #c9ecb7 100%)', color: '#4f8a29', boxShadow: '0 10px 20px rgba(91, 179, 60, 0.18)' },
    { background: 'linear-gradient(135deg, #ede5ff 0%, #ddd0ff 100%)', color: '#6c4bd2', boxShadow: '0 10px 20px rgba(134, 108, 255, 0.18)' },
    { background: 'linear-gradient(135deg, #ffe7d1 0%, #ffd3a8 100%)', color: '#bb6a1c', boxShadow: '0 10px 20px rgba(255, 163, 87, 0.18)' }
  ]

  let hash = 0
  const source = String(seed || 'user')
  for (let index = 0; index < source.length; index += 1) {
    hash = (hash * 31 + source.charCodeAt(index)) | 0
  }
  return palette[Math.abs(hash) % palette.length]
}
</script>

<style scoped src="../styles/messenger-view.css"></style>
