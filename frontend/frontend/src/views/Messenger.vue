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
        </div>

        <div class="messenger-sidebar__content">
          <button
            v-for="conversation in filteredFlatConversations"
            :key="conversation.id"
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
                <span class="conversation-card__time">{{ formatSidebarTime(conversation.last_message?.created_at) }}</span>
              </span>
              <span class="conversation-card__preview">{{ conversationPreview(conversation) }}</span>
            </span>

            <span v-if="isConversationUnread(conversation)" class="conversation-card__badge"></span>
          </button>

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

      <section class="messenger-thread">
        <header v-if="activeConversation" class="messenger-thread__header">
          <div class="thread-title">
            <div class="thread-title__avatar" :class="conversationAvatarClass(activeConversation)" :style="threadAvatarStyle">
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
              <span>{{ activeConversation.description || subtitleText }}</span>
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
            <input v-model="messageSearch" type="text" placeholder="Поиск">
          </label>

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

              <article
                v-else
                :id="`message-${item.message.id}`"
                class="message-row"
                :class="{ 'is-own': isOwn(item.message), 'is-editing': editingId === item.message.id }"
                @mouseenter="hoveredMessageId = item.message.id"
                @mouseleave="hoveredMessageId = null"
              >
                <div
                  v-if="!isOwn(item.message)"
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

                <div class="message-bubble" :class="{ 'is-deleted': item.message.is_deleted }">
                  <div
                    v-if="!isOwn(item.message) && activeConversation && activeConversation.type !== 'direct' && !item.message.is_deleted"
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

                    <p v-if="item.message.body" class="message-bubble__text">{{ item.message.body }}</p>

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
                    <i v-if="isOwn(item.message) && !item.message.is_deleted" class="fas fa-check-double message-bubble__ticks"></i>
                  </span>
                </div>

                <div v-if="messageActionsVisible(item.message)" class="message-row__actions">
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
                  @keydown.enter.exact.prevent="submitComposer"
                ></textarea>
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
            <button type="button" class="detail-section__toggle" @click="toggleSection('files')">
              <span><i class="fas fa-paperclip"></i> Файлы</span>
              <i class="fas" :class="detailSections.files ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
            </button>
            <div v-if="detailSections.files" class="detail-section__body">
              <div v-if="files.length" class="detail-file-list">
                <button
                  v-for="file in files"
                  :key="file.key"
                  type="button"
                  class="detail-file"
                  @click="isInlineImage(file) ? openImageViewer(file, files) : downloadAttachment(file)"
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
      <div v-if="confirmModalOpen" class="messenger-confirm-overlay" @click.self="closeConfirm">
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

      <div v-if="showConversationModal" class="messenger-dialog-overlay" @click.self="closeConversationModal">
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
                  <option value="direct">Личный чат</option>
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

            <template v-if="!renameMode && conversationForm.type === 'direct'">
              <label class="messenger-field">
                <span>Пользователь</span>
                <select v-model="conversationForm.directUserId" class="form-control">
                  <option value="">Выберите пользователя</option>
                  <option v-for="user in availableDirectUsers" :key="user.id" :value="user.id">{{ user.full_name || user.email }}</option>
                </select>
              </label>
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
            <button type="button" class="btn btn-primary btn-sm" :disabled="savingConversation" @click="submitConversationModal">Сохранить</button>
          </div>
        </div>
      </div>

      <div v-if="addMembersModalOpen" class="messenger-dialog-overlay" @click.self="addMembersModalOpen = false">
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

      <div v-if="forwardModalOpen" class="messenger-dialog-overlay" @click.self="closeForwardModal">
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

const URL_RE = /https?:\/\/[^\s<>"']+/gi
const INLINE_IMAGE_TYPES = new Set(['image/png', 'image/jpeg', 'image/webp', 'image/gif'])
const INLINE_IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.webp', '.gif']

export default {
  name: 'Messenger',
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
    const detailSections = ref({ info: true, members: true, files: true, links: false })
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

    const messageImageAttachments = (message) => (message?.attachments || []).filter((file) => isInlineImage(file) && file.download_url)
    const messageFileAttachments = (message) => (message?.attachments || []).filter((file) => !isInlineImage(file) || !file.download_url)

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

    const messageFeed = computed(() => {
      const feed = []
      let lastDay = ''
      visibleMessages.value.forEach((message) => {
        const date = message.created_at ? new Date(message.created_at) : null
        const dayKey = date ? date.toISOString().slice(0, 10) : 'unknown'
        if (dayKey !== lastDay) {
          lastDay = dayKey
          feed.push({ type: 'day', key: `day-${dayKey}`, label: formatDayChip(message.created_at) })
        }
        feed.push({ type: 'message', key: message.id, message })
      })
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
      showConversationModal.value = true
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

    const onComposerInput = () => {
      syncComposerHeight()
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

    const scrollToMessage = (messageId) => {
      const target = document.getElementById(`message-${messageId}`)
      target?.scrollIntoView({ block: 'center', behavior: 'smooth' })
    }

    const scrollToPinned = () => {
      if (pinnedMessage.value?.id) scrollToMessage(pinnedMessage.value.id)
    }

    const messageActionsVisible = (message) => hoveredMessageId.value === message.id && !message.is_deleted

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
    })

    onBeforeUnmount(() => {
      window.removeEventListener('resize', handleViewportResize)
      window.removeEventListener('keydown', handleViewerKeydown)
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
      groupsOpen,
      directOpen,
      messageSearchOpen,
      messageSearch,
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
      submitAddMembers,
      insertLinkToken,
      insertEmoji,
      isInlineImage,
      messageImageAttachments,
      messageFileAttachments,
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
