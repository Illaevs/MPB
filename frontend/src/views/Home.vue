<template>
  <div class="feed-page">
    <!-- ЛЕНТА -->
    <div class="feed-main">
      <!-- Composer (только для тех, кто может публиковать) -->
      <div v-if="canPost" class="composer">
        <div class="composer__modes">
          <button
            type="button"
            class="composer__mode"
            :class="{ 'is-active': draft.mode === 'post' }"
            @click="draft.mode = 'post'"
          ><i class="fas fa-pen"></i> Запись</button>
          <button
            type="button"
            class="composer__mode"
            :class="{ 'is-active': draft.mode === 'poll' }"
            @click="draft.mode = 'poll'"
          ><i class="fas fa-square-poll-vertical"></i> Опрос</button>
        </div>

        <div class="composer__top">
          <UiAvatar :src="me?.avatar_url" :name="me?.full_name" size="md" />
          <MentionInput
            v-model="draft.body"
            :users="allUsers"
            multiline
            :rows="1"
            auto-grow
            :min-height="44"
            :max-height="320"
            class="composer__input"
            :placeholder="draft.mode === 'poll'
              ? 'Вопрос опроса…'
              : `О чём вы хотите рассказать, ${firstName}?`"
            @mention="onComposerMention"
            @paste="onPaste"
          />
        </div>

        <!-- Варианты опроса -->
        <div v-if="draft.mode === 'poll'" class="composer__poll">
          <div
            v-for="(opt, i) in draft.pollOptions"
            :key="i"
            class="composer__poll-opt"
          >
            <i class="far fa-circle"></i>
            <input
              type="text"
              v-model="draft.pollOptions[i]"
              class="composer__poll-input"
              :placeholder="`Вариант ${i + 1}`"
              maxlength="300"
            />
            <button
              v-if="draft.pollOptions.length > 2"
              type="button"
              class="composer__poll-x"
              @click="draft.pollOptions.splice(i, 1)"
            ><i class="fas fa-times"></i></button>
          </div>
          <button
            v-if="draft.pollOptions.length < 10"
            type="button"
            class="composer__poll-add"
            @click="draft.pollOptions.push('')"
          ><i class="fas fa-plus"></i> Добавить вариант</button>
          <div class="composer__poll-opts">
            <label class="composer__opt">
              <input type="checkbox" v-model="draft.pollMulti" />
              <span>Несколько ответов</span>
            </label>
            <label class="composer__opt">
              <input type="checkbox" v-model="draft.pollAnon" />
              <span>Анонимно</span>
            </label>
          </div>
        </div>

        <div v-if="draft.images.length" class="composer__images">
          <div v-for="(img, i) in draft.images" :key="img.url" class="composer__image">
            <img :src="img.url" :alt="img.name" />
            <button type="button" class="composer__image-x" @click="removeDraftImage(i)">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>

        <div v-if="draft.files.length" class="composer__files">
          <div v-for="(f, i) in draft.files" :key="f.url" class="composer__file-chip">
            <i :class="fileIcon(f.name)"></i>
            <span class="composer__file-name" :title="f.name">{{ f.name }}</span>
            <span v-if="f.size" class="composer__file-size">{{ formatBytes(f.size) }}</span>
            <button type="button" class="composer__file-x" @click="removeDraftFile(i)">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>

        <div v-if="composerExpanded || draft.body || draft.images.length || draft.files.length || draft.mode === 'poll'" class="composer__bar">
          <div class="composer__actions">
            <input
              ref="imageInput"
              type="file"
              accept="image/png,image/jpeg,image/webp,image/gif"
              multiple
              class="composer__file"
              @change="onImagesPicked"
            />
            <input
              ref="fileInput"
              type="file"
              multiple
              class="composer__file"
              @change="onFilesPicked"
            />
            <button type="button" class="composer__act" :disabled="uploading" @click="imageInput?.click()">
              <i class="fas" :class="uploading ? 'fa-spinner fa-spin' : 'fa-image'"></i>
              Картинка
            </button>
            <button type="button" class="composer__act" :disabled="uploadingFile" @click="fileInput?.click()">
              <i class="fas" :class="uploadingFile ? 'fa-spinner fa-spin' : 'fa-paperclip'"></i>
              Файл
            </button>
            <label class="composer__opt">
              <input type="checkbox" v-model="draft.is_news" />
              <span>Официальная новость</span>
            </label>
            <label class="composer__opt">
              <input type="checkbox" v-model="draft.is_pinned" />
              <span>Закрепить</span>
            </label>
          </div>
          <div class="composer__submit">
            <UiButton variant="ghost" size="sm" :disabled="publishing" @click="resetComposer">
              Отмена
            </UiButton>
            <UiButton
              variant="primary"
              size="sm"
              icon-left="fas fa-paper-plane"
              :loading="publishing"
              :disabled="!canSubmit"
              @click="publish"
            >Опубликовать</UiButton>
          </div>
        </div>
      </div>

      <!-- Скрытые file input'ы для edit-режима. Вынесены ИЗ v-for ленты:
           внутри v-for Vue делает ref массивом (по элементу на итерацию),
           и `editImageInput.click()` ломается. Тут они одиночные. -->
      <input
        ref="editImageInput"
        type="file"
        accept="image/png,image/jpeg,image/webp,image/gif"
        multiple
        class="composer__file"
        @change="onEditImagesPicked"
      />
      <input
        ref="editFileInput"
        type="file"
        multiple
        class="composer__file"
        @change="onEditFilesPicked"
      />

      <!-- Лента постов -->
      <div v-if="loadingFeed" class="feed-state">Загрузка ленты…</div>
      <div v-else-if="!posts.length" class="feed-state feed-state--empty">
        <i class="fas fa-newspaper"></i>
        <span>Пока новостей нет.</span>
      </div>

      <article
        v-for="post in posts"
        :key="post.id"
        class="post"
        :class="{ 'is-pinned': post.is_pinned }"
      >
        <header class="post__head">
          <UiAvatar :src="post.author?.avatar_url" :name="post.author?.full_name" size="md" />
          <div class="post__meta">
            <div class="post__author">{{ post.author?.full_name || 'Сотрудник' }}</div>
            <div class="post__sub">
              <span v-if="post.author?.job_title">{{ post.author.job_title }}</span>
              <span v-else-if="post.author?.department">{{ post.author.department }}</span>
              <span v-else-if="post.author?.role_name">{{ post.author.role_name }}</span>
              <span class="post__dot">·</span>
              <span>{{ formatWhen(post.created_at) }}</span>
              <span v-if="isEdited(post)" class="post__edited" :title="`Изменено ${formatWhen(post.updated_at)}`">
                · изменено
              </span>
            </div>
          </div>
          <div class="post__badges">
            <span v-if="post.is_pinned" class="post__badge is-pin" title="Закреплено">
              <i class="fas fa-thumbtack"></i>
            </span>
            <span v-if="post.poll" class="post__badge is-poll">Опрос</span>
            <span v-if="post.post_type === 'news'" class="post__badge is-news">Новость</span>
          </div>
          <div v-if="post.can_edit" class="post__menu">
            <button type="button" class="post__menu-btn" @click="toggleMenu(post.id)">
              <i class="fas fa-ellipsis-h"></i>
            </button>
            <div v-if="menuOpenId === post.id" class="post__menu-pop">
              <button type="button" @click="startEditPost(post)">
                <i class="fas fa-pen"></i> Изменить
              </button>
              <button type="button" @click="togglePin(post)">
                <i class="fas fa-thumbtack"></i>
                {{ post.is_pinned ? 'Открепить' : 'Закрепить' }}
              </button>
              <button type="button" class="is-danger" @click="onDeletePost(post)">
                <i class="fas fa-trash"></i> Удалить
              </button>
            </div>
          </div>
        </header>

        <!-- Inline-редактор поста: открывается из меню "Изменить".
             Опрос правкой не меняем (бэкенд это запрещает, чтобы не сбить голоса). -->
        <div v-if="editingPostId === post.id" class="post__edit">
          <MentionInput
            v-model="editDraft.body"
            :users="allUsers"
            multiline
            :rows="1"
            auto-grow
            :min-height="44"
            :max-height="320"
            class="composer__input"
            placeholder="Текст новости…"
            @mention="onEditMention"
          />

          <!-- Текущие вложения: картинки thumbnail-сеткой, файлы — чипами,
               у каждого крестик для удаления. -->
          <div v-if="editDraft.attachments.filter((a) => (a.kind || 'image') !== 'file').length"
               class="composer__images">
            <template v-for="(att, i) in editDraft.attachments" :key="att.url">
              <div v-if="(att.kind || 'image') !== 'file'" class="composer__image">
                <img :src="att.url" :alt="att.name" />
                <button type="button" class="composer__image-x" @click="removeEditAttachment(i)">
                  <i class="fas fa-times"></i>
                </button>
              </div>
            </template>
          </div>
          <div v-if="editDraft.attachments.filter((a) => a.kind === 'file').length"
               class="composer__files">
            <template v-for="(att, i) in editDraft.attachments" :key="att.url + '-f'">
              <div v-if="att.kind === 'file'" class="composer__file-chip">
                <i :class="fileIcon(att.name)"></i>
                <span class="composer__file-name" :title="att.name">{{ att.name }}</span>
                <span v-if="att.size" class="composer__file-size">{{ formatBytes(att.size) }}</span>
                <button type="button" class="composer__file-x" @click="removeEditAttachment(i)">
                  <i class="fas fa-times"></i>
                </button>
              </div>
            </template>
          </div>

          <div class="post__edit-actions">
            <div class="post__edit-add">
              <!-- file input'ы у edit-формы вынесены наверх страницы
                   (см. секцию feed-page), потому что внутри v-for
                   Vue превращает ref в массив, у которого нет .click(). -->
              <button type="button" class="composer__act" :disabled="uploading" @click="editImageInput?.click()">
                <i class="fas" :class="uploading ? 'fa-spinner fa-spin' : 'fa-image'"></i>
                Картинка
              </button>
              <button type="button" class="composer__act" :disabled="uploadingFile" @click="editFileInput?.click()">
                <i class="fas" :class="uploadingFile ? 'fa-spinner fa-spin' : 'fa-paperclip'"></i>
                Файл
              </button>
              <span v-if="post.poll" class="post__edit-hint">
                <i class="fas fa-info-circle"></i> Опрос не меняется
              </span>
            </div>
            <div class="post__edit-buttons">
              <UiButton variant="ghost" size="sm" :disabled="savingEdit" @click="cancelEditPost">
                Отмена
              </UiButton>
              <UiButton
                variant="primary"
                size="sm"
                icon-left="fas fa-check"
                :loading="savingEdit"
                :disabled="!editDraft.body.trim() && !editDraft.attachments.length"
                @click="saveEditPost(post)"
              >Сохранить</UiButton>
            </div>
          </div>
        </div>
        <div v-else-if="post.body" class="post__body">
          <template v-for="(seg, i) in parseSegments(post.body)" :key="i">
            <span v-if="seg.type === 'mention'" class="post__mention">@{{ seg.name }}</span>
            <template v-else>{{ seg.text }}</template>
          </template>
        </div>

        <!-- Опрос -->
        <div v-if="post.poll" class="poll">
          <div
            v-for="opt in post.poll.options"
            :key="opt.id"
            class="poll__opt"
            :class="{ 'is-voted': opt.voted }"
            @click="onVote(post, opt)"
          >
            <div class="poll__bar" :style="{ width: pollPct(opt, post.poll) + '%' }"></div>
            <div class="poll__opt-row">
              <span class="poll__check">
                <i :class="opt.voted
                  ? 'fas fa-check-circle'
                  : (post.poll.multi ? 'far fa-square' : 'far fa-circle')"></i>
              </span>
              <span class="poll__text">{{ opt.text }}</span>
              <span v-if="!post.poll.anonymous && opt.voters.length" class="poll__voters">
                <UiAvatar
                  v-for="v in opt.voters.slice(0, 3)"
                  :key="v.id"
                  :src="v.avatar_url"
                  :name="v.full_name"
                  size="xs"
                />
                <span v-if="opt.voters.length > 3" class="poll__voters-more">
                  +{{ opt.voters.length - 3 }}
                </span>
              </span>
              <span class="poll__pct">{{ pollPct(opt, post.poll) }}%</span>
            </div>
          </div>
          <div class="poll__foot">
            {{ post.poll.total_votes }} {{ pluralVotes(post.poll.total_votes) }}
            <span v-if="post.poll.multi">· неск. ответов</span>
            <span v-if="post.poll.anonymous">· анонимно</span>
          </div>
        </div>

        <!-- Картинки поста (inline-галерея). У старых постов kind отсутствует
             — считаем картинкой по дефолту (см. postImages в setup). -->
        <div v-if="postImages(post).length" class="post__images" :class="`count-${Math.min(postImages(post).length, 4)}`">
          <a
            v-for="(img, i) in postImages(post)"
            :key="img.url + i"
            :href="img.url"
            target="_blank"
            rel="noopener"
            class="post__image"
          >
            <img :src="img.url" :alt="img.name || 'Изображение'" loading="lazy" />
          </a>
        </div>

        <!-- Файлы поста (документы, архивы и т.п.) — кликабельные чипы. -->
        <div v-if="postFiles(post).length" class="post__files">
          <a
            v-for="(f, i) in postFiles(post)"
            :key="f.url + i"
            :href="f.url + (f.url.includes('?') ? '&' : '?') + 'name=' + encodeURIComponent(f.name || '')"
            target="_blank"
            rel="noopener"
            class="post__file"
            :title="`Скачать ${f.name}`"
          >
            <i :class="fileIcon(f.name)"></i>
            <span class="post__file-name">{{ f.name }}</span>
            <span v-if="f.size" class="post__file-size">{{ formatBytes(f.size) }}</span>
            <i class="fas fa-arrow-down post__file-dl"></i>
          </a>
        </div>

        <footer class="post__footer">
          <!-- Реакции -->
          <div class="post__reactions">
            <button
              v-for="r in post.reactions"
              :key="r.emoji"
              type="button"
              class="post__reaction"
              :class="{ 'is-mine': r.mine }"
              @click="toggleReaction(post, r.emoji)"
            >
              <span class="post__reaction-emoji">{{ r.emoji }}</span>
              <span>{{ r.count }}</span>
            </button>
            <div class="post__react-add-wrap">
              <button
                type="button"
                class="post__react-add"
                title="Добавить реакцию"
                @click="toggleReactionPicker(post.id)"
              ><i class="far fa-face-smile"></i></button>
              <div v-if="reactionPickerId === post.id" class="post__react-picker">
                <button
                  v-for="e in EMOJI_SET"
                  :key="e"
                  type="button"
                  @click="toggleReaction(post, e)"
                >{{ e }}</button>
              </div>
            </div>
          </div>
          <button type="button" class="post__react" @click="toggleComments(post)">
            <i class="far fa-comment"></i>
            <span>{{ post.comments_count || 0 }}</span>
          </button>
          <span class="post__views" :title="`${post.views_count || 0} просмотров`">
            <i class="far fa-eye"></i>
            <span>{{ post.views_count || 0 }}</span>
          </span>
        </footer>

        <!-- Комментарии -->
        <div v-if="commentState[post.id]?.open" class="post__comments">
          <div v-if="commentState[post.id].loading" class="post__comments-loading">Загрузка…</div>
          <div
            v-for="c in commentState[post.id].list"
            :key="c.id"
            class="comment"
          >
            <UiAvatar :src="c.author?.avatar_url" :name="c.author?.full_name" size="sm" />
            <div class="comment__bubble">
              <div class="comment__head">
                <strong>{{ c.author?.full_name || 'Сотрудник' }}</strong>
                <span class="comment__when">{{ formatWhen(c.created_at) }}</span>
                <button
                  v-if="c.can_delete"
                  type="button"
                  class="comment__del"
                  title="Удалить"
                  @click="onDeleteComment(post, c)"
                ><i class="fas fa-times"></i></button>
              </div>
              <div class="comment__text">
                <template v-for="(seg, i) in parseSegments(c.body)" :key="i">
                  <span v-if="seg.type === 'mention'" class="post__mention">@{{ seg.name }}</span>
                  <template v-else>{{ seg.text }}</template>
                </template>
              </div>
            </div>
          </div>
          <div class="comment-form">
            <UiAvatar :src="me?.avatar_url" :name="me?.full_name" size="sm" />
            <MentionInput
              v-model="commentState[post.id].draft"
              :users="allUsers"
              class="comment-form__input"
              placeholder="Написать комментарий…  @ — упомянуть"
              @mention="(m) => onCommentMention(post.id, m)"
              @submit="submitComment(post)"
            />
            <button
              type="button"
              class="comment-form__send"
              :disabled="!commentState[post.id].draft.trim()"
              @click="submitComment(post)"
            ><i class="fas fa-paper-plane"></i></button>
          </div>
        </div>
      </article>
    </div>

    <!-- ПРАВЫЙ САЙДБАР -->
    <aside class="feed-side">
      <section class="widget">
        <h3 class="widget__title">Мои задачи</h3>
        <div class="widget__tasks">
          <router-link to="/tasks" class="wtask">
            <span class="wtask__label">Делаю</span>
            <span class="wtask__count">{{ taskCounts.doing }}</span>
          </router-link>
          <router-link to="/tasks" class="wtask">
            <span class="wtask__label">Помогаю</span>
            <span class="wtask__count">{{ taskCounts.helping }}</span>
          </router-link>
          <router-link to="/tasks" class="wtask">
            <span class="wtask__label">Поручил</span>
            <span class="wtask__count">{{ taskCounts.assigned }}</span>
          </router-link>
          <router-link to="/tasks" class="wtask">
            <span class="wtask__label">Наблюдаю</span>
            <span class="wtask__count">{{ taskCounts.watching }}</span>
          </router-link>
        </div>
      </section>

      <section v-if="kpiVisible" class="widget">
        <h3 class="widget__title">Сводка</h3>
        <div class="widget__kpi">
          <router-link to="/projects" class="wkpi">
            <span class="wkpi__value">{{ summary.active_deals }}</span>
            <span class="wkpi__label">Активных проектов</span>
          </router-link>
          <router-link to="/tasks" class="wkpi" :class="{ 'is-warn': summary.overdue_tasks > 0 }">
            <span class="wkpi__value">{{ summary.overdue_tasks }}</span>
            <span class="wkpi__label">Просроченных задач</span>
          </router-link>
          <div class="wkpi">
            <span class="wkpi__value">{{ summary.new_documents_7d }}</span>
            <span class="wkpi__label">Документов за неделю</span>
          </div>
        </div>
      </section>

      <section v-if="popular.length" class="widget">
        <h3 class="widget__title">Популярное в ленте</h3>
        <ul class="widget__popular">
          <li v-for="p in popular" :key="p.id" @click="scrollToPost(p.id)">
            <div class="wpop__text">{{ shortText(p.body) }}</div>
            <div class="wpop__meta">
              <span><i class="far fa-face-smile"></i> {{ reactionsTotal(p) }}</span>
              <span><i class="far fa-comment"></i> {{ p.comments_count }}</span>
            </div>
          </li>
        </ul>
      </section>

      <section v-if="birthdays.length" class="widget">
        <h3 class="widget__title">Дни рождения</h3>
        <ul class="widget__people">
          <li v-for="b in birthdays" :key="b.user_id">
            <UiAvatar :src="b.avatar_url" :name="b.full_name" size="sm" />
            <div class="wperson__meta">
              <div class="wperson__name">{{ b.full_name }}</div>
              <div class="wperson__sub">
                <template v-if="b.is_today">
                  <span class="wperson__today">Сегодня празднует!</span>
                </template>
                <template v-else>
                  {{ b.date_label }} · через {{ b.days_until }} {{ pluralDays(b.days_until) }}
                </template>
              </div>
            </div>
            <span v-if="b.is_today" class="wperson__gift"><i class="fas fa-gift"></i></span>
          </li>
        </ul>
      </section>

      <section v-if="absentToday.length" class="widget">
        <h3 class="widget__title">Сегодня отсутствуют</h3>
        <ul class="widget__people">
          <li v-for="a in absentToday" :key="a.id">
            <UiAvatar :name="a.user_full_name" size="sm" />
            <div class="wperson__meta">
              <div class="wperson__name">{{ a.user_full_name || '—' }}</div>
              <div class="wperson__sub">
                {{ absenceLabel(a.type) }} · до {{ formatShortDate(a.date_to) }}
              </div>
            </div>
            <span class="wperson__abs" :class="`is-${a.type}`"></span>
          </li>
        </ul>
        <router-link to="/absences" class="widget__more">Все отсутствия →</router-link>
      </section>

      <div class="feed-side__foot">
        Корпоративный портал · {{ currentYear }}
      </div>
    </aside>
  </div>
</template>

<script>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { api } from '../services/api'
import { useToast } from '../composables/useToast'
import { useAuthStore } from '../stores/auth'
import { UiAvatar, UiButton } from '../components/ui'
import MentionInput from '../components/ui/MentionInput.vue'
import { formatDate as fmtDate, formatTime as fmtTime } from '../utils/format'
import { parseServerDate } from '../composables/useServerClock'

const ABSENCE_LABEL = {
  vacation: 'Отпуск',
  sick_leave: 'Больничный',
  business_trip: 'Командировка',
  other: 'Отсутствует',
}
const EMOJI_SET = ['👍', '❤️', '🔥', '👏', '😄', '🎉', '😮']
// Маркер упоминания в тексте: @[Имя](user_id).
const MENTION_RE = /@\[([^\]]+)\]\(([0-9a-fA-F][0-9a-fA-F-]{7,})\)/g

export default {
  name: 'Home',
  components: { UiAvatar, UiButton, MentionInput },
  setup() {
    const auth = useAuthStore()
    const { success, error: toastError } = useToast()

    const me = computed(() => auth.user || null)
    const currentYear = new Date().getFullYear()
    const firstName = computed(() => {
      const n = (auth.user?.full_name || '').trim().split(/\s+/)
      return n[1] || n[0] || 'коллега'
    })
    const canPost = computed(() => {
      const f = auth.permissions?.feed || {}
      return Boolean(auth.isSuperuser || f.edit_all)
    })

    // ---- Composer ----
    const composerExpanded = ref(false)
    const publishing = ref(false)
    const uploading = ref(false)
    const uploadingFile = ref(false)
    const imageInput = ref(null)
    const fileInput = ref(null)
    const composerMentions = ref([])  // [{name, id}]
    const draft = reactive({
      mode: 'post',          // 'post' | 'poll'
      body: '',
      // Картинки идут в inline-галерею; файлы — в отдельный список
      // «скрепок» под телом поста. На сервер уходят склеенными
      // в attachments с полем kind ("image" / "file").
      images: [],
      files: [],
      is_news: true,
      is_pinned: false,
      pollOptions: ['', ''],
      pollMulti: false,
      pollAnon: false,
    })

    const canSubmit = computed(() => {
      if (publishing.value) return false
      if (draft.mode === 'poll') {
        const filled = draft.pollOptions.filter((o) => o.trim()).length
        return draft.body.trim().length > 0 && filled >= 2
      }
      return Boolean(draft.body.trim() || draft.images.length || draft.files.length)
    })

    const resetComposer = () => {
      draft.mode = 'post'
      draft.body = ''
      draft.images = []
      draft.files = []
      draft.is_news = true
      draft.is_pinned = false
      draft.pollOptions = ['', '']
      draft.pollMulti = false
      draft.pollAnon = false
      composerMentions.value = []
      composerExpanded.value = false
    }

    const onComposerMention = (m) => {
      if (m && m.id) composerMentions.value.push(m)
    }

    // @Имя Фамилия  →  @[Имя Фамилия](id). Длинные имена — первыми,
    // чтобы «@Иван» не перехватил «@Иван Петров».
    const applyMentions = (text, mentions) => {
      let out = text || ''
      const sorted = [...(mentions || [])].sort((a, b) => b.name.length - a.name.length)
      const seen = new Set()
      for (const m of sorted) {
        if (seen.has(m.name)) continue
        seen.add(m.name)
        const safe = m.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
        out = out.replace(new RegExp(`@${safe}`, 'g'), `@[${m.name}](${m.id})`)
      }
      return out
    }

    // Текст с маркерами  →  сегменты для рендера.
    const parseSegments = (text) => {
      const segs = []
      let last = 0
      const re = new RegExp(MENTION_RE)
      let m
      while ((m = re.exec(text || '')) !== null) {
        if (m.index > last) segs.push({ type: 'text', text: text.slice(last, m.index) })
        segs.push({ type: 'mention', name: m[1], id: m[2] })
        last = m.index + m[0].length
      }
      if (last < (text || '').length) segs.push({ type: 'text', text: text.slice(last) })
      return segs
    }

    const onImagesPicked = async (e) => {
      const files = [...(e.target?.files || [])]
      if (e.target) e.target.value = ''
      await uploadFiles(files, draft.images)
    }
    // Универсальный uploader. Если в target передан массив draft'а
    // (`draft.images` или `editDraft.attachments`), результат пушится туда.
    const uploadFiles = async (files, target) => {
      const list = [...(files || [])].filter((f) => f && f.type && f.type.startsWith('image/'))
      if (!list.length) return
      uploading.value = true
      try {
        for (const file of list) {
          const fd = new FormData()
          fd.append('file', file)
          const res = await api.feed.uploadImage(fd)
          if (res?.url) (target || draft.images).push({
            url: res.url, name: res.name, kind: 'image',
          })
        }
      } catch (err) {
        toastError(err?.response?.data?.detail || 'Не удалось загрузить картинку')
      } finally {
        uploading.value = false
      }
    }

    // Произвольные файлы (документы/архивы/CAD/медиа). target — тот же
    // приёмник, что и у uploadFiles, чтобы переиспользовать из edit-формы.
    const onFilesPicked = async (e) => {
      const files = [...(e.target?.files || [])]
      if (e.target) e.target.value = ''
      await uploadAnyFiles(files, draft.files)
    }
    const uploadAnyFiles = async (files, target) => {
      const list = [...(files || [])].filter(Boolean)
      if (!list.length) return
      uploadingFile.value = true
      try {
        for (const file of list) {
          const fd = new FormData()
          fd.append('file', file)
          try {
            const res = await api.feed.uploadFile(fd)
            if (res?.url) (target || draft.files).push({
              url: res.url, name: res.name, kind: 'file', size: res.size,
            })
          } catch (err) {
            toastError(err?.response?.data?.detail || `Не удалось загрузить ${file.name}`)
          }
        }
      } finally {
        uploadingFile.value = false
      }
    }
    const onPaste = async (e) => {
      const items = e.clipboardData?.items
      if (!items) return
      const images = []
      for (const it of items) {
        if (it.kind === 'file' && it.type && it.type.startsWith('image/')) {
          const f = it.getAsFile()
          if (f) images.push(f)
        }
      }
      if (!images.length) return
      e.preventDefault()
      composerExpanded.value = true
      await uploadFiles(images, draft.images)
    }
    const removeDraftImage = (i) => draft.images.splice(i, 1)
    const removeDraftFile = (i) => draft.files.splice(i, 1)

    // ---- Лента ----
    const posts = ref([])
    const loadingFeed = ref(false)
    const menuOpenId = ref(null)
    const reactionPickerId = ref(null)
    const commentState = reactive({})

    const resortPosts = () => {
      posts.value.sort((a, b) => {
        if (!!b.is_pinned !== !!a.is_pinned) return (b.is_pinned ? 1 : 0) - (a.is_pinned ? 1 : 0)
        return String(b.created_at || '').localeCompare(String(a.created_at || ''))
      })
    }

    const publish = async () => {
      if (!canSubmit.value) return
      publishing.value = true
      try {
        const body = applyMentions(draft.body.trim(), composerMentions.value)
        // Картинки и файлы хранятся раздельно в драфте, но на бэк
        // уходят склеенным массивом attachments; рендер на стороне
        // фронта решает по att.kind, что показывать (галерея / чип).
        const payload = {
          body,
          post_type: draft.is_news ? 'news' : 'post',
          is_pinned: draft.is_pinned,
          attachments: [...draft.images, ...draft.files],
        }
        if (draft.mode === 'poll') {
          payload.poll = {
            multi: draft.pollMulti,
            anonymous: draft.pollAnon,
            options: draft.pollOptions.map((o) => o.trim()).filter(Boolean),
          }
        }
        const created = await api.feed.create(payload)
        posts.value.unshift(created)
        resortPosts()
        resetComposer()
        success('Опубликовано')
      } catch (err) {
        toastError(err?.response?.data?.detail || 'Не удалось опубликовать')
      } finally {
        publishing.value = false
      }
    }

    const loadFeed = async () => {
      loadingFeed.value = true
      try {
        const data = await api.feed.list({ limit: 30 })
        posts.value = Array.isArray(data) ? data : []
        for (const p of posts.value) api.feed.markView(p.id).catch(() => {})
      } catch (e) {
        posts.value = []
        toastError('Не удалось загрузить ленту')
      } finally {
        loadingFeed.value = false
      }
    }

    const toggleMenu = (id) => {
      menuOpenId.value = menuOpenId.value === id ? null : id
    }
    const closeMenu = () => { menuOpenId.value = null }

    const toggleReactionPicker = (id) => {
      reactionPickerId.value = reactionPickerId.value === id ? null : id
    }

    const toggleReaction = async (post, emoji) => {
      reactionPickerId.value = null
      try {
        const res = await api.feed.react(post.id, emoji)
        if (res?.reactions) post.reactions = res.reactions
      } catch (e) {
        toastError('Не удалось поставить реакцию')
      }
    }
    const reactionsTotal = (post) =>
      (post.reactions || []).reduce((s, r) => s + (r.count || 0), 0)

    // ---- Опрос ----
    const pollPct = (opt, poll) => {
      const total = poll?.total_votes || 0
      if (!total) return 0
      return Math.round(((opt.votes || 0) / total) * 100)
    }
    const onVote = async (post, opt) => {
      if (!post.poll) return
      let selected
      if (post.poll.multi) {
        const cur = post.poll.options.filter((o) => o.voted).map((o) => o.id)
        selected = cur.includes(opt.id)
          ? cur.filter((x) => x !== opt.id)
          : [...cur, opt.id]
      } else {
        selected = [opt.id]
      }
      try {
        const res = await api.feed.vote(post.id, selected)
        if (res) post.poll = res
      } catch (e) {
        toastError('Не удалось проголосовать')
      }
    }

    // ---- Комментарии ----
    const toggleComments = async (post) => {
      const st = commentState[post.id]
      if (st?.open) { st.open = false; return }
      commentState[post.id] = { open: true, list: [], loading: true, draft: '', mentions: [] }
      try {
        const list = await api.feed.comments(post.id)
        commentState[post.id].list = Array.isArray(list) ? list : []
      } catch (e) {
        commentState[post.id].list = []
      } finally {
        commentState[post.id].loading = false
      }
    }
    const onCommentMention = (postId, m) => {
      const st = commentState[postId]
      if (st && m && m.id) (st.mentions = st.mentions || []).push(m)
    }
    const submitComment = async (post) => {
      const st = commentState[post.id]
      if (!st || !st.draft.trim()) return
      const body = applyMentions(st.draft.trim(), st.mentions || [])
      const rawDraft = st.draft
      st.draft = ''
      st.mentions = []
      try {
        const c = await api.feed.addComment(post.id, { body })
        st.list.push(c)
        post.comments_count = (post.comments_count || 0) + 1
      } catch (e) {
        toastError('Не удалось отправить комментарий')
        st.draft = rawDraft
      }
    }
    const onDeleteComment = async (post, comment) => {
      if (!confirm('Удалить комментарий?')) return
      try {
        await api.feed.removeComment(comment.id)
        const st = commentState[post.id]
        if (st) st.list = st.list.filter((x) => x.id !== comment.id)
        post.comments_count = Math.max(0, (post.comments_count || 0) - 1)
      } catch (e) {
        toastError('Не удалось удалить комментарий')
      }
    }

    const togglePin = async (post) => {
      closeMenu()
      try {
        const updated = await api.feed.patchPost(post.id, { is_pinned: !post.is_pinned })
        Object.assign(post, updated)
        resortPosts()
      } catch (e) {
        toastError('Не удалось изменить закрепление')
      }
    }

    // ---- Inline edit поста ----------------------------------------
    // Правится текст, упоминания и attachments (картинки + файлы).
    // Опрос правкой по-прежнему не трогаем — бэкенд это явно
    // запрещает (см. patch_post), чтобы не сбить уже отданные голоса.
    const editingPostId = ref(null)
    const savingEdit = ref(false)
    const editImageInput = ref(null)
    const editFileInput = ref(null)
    const editDraft = reactive({ body: '', attachments: [] })
    const editMentions = ref([])  // [{name, id}]

    // Текст с маркерами `@[Имя](id)`  →  плоский текст с `@Имя`
    // плюс список мемнтионов (для дальнейшего applyMentions при save).
    const bodyToPlain = (text) => {
      const mentions = []
      const plain = String(text || '').replace(MENTION_RE, (_m, name, id) => {
        mentions.push({ name, id })
        return `@${name}`
      })
      return { plain, mentions }
    }

    const startEditPost = (post) => {
      closeMenu()
      const { plain, mentions } = bodyToPlain(post.body || '')
      editDraft.body = plain
      editMentions.value = mentions
      // Копия attachments — чтобы можно было удалить/добавить, не
      // ломая исходный пост до явного «Сохранить». У старых постов
      // (до появления kind) считаем элемент картинкой.
      editDraft.attachments = (post.attachments || []).map((a) => ({
        url: a.url,
        name: a.name,
        kind: a.kind || 'image',
        size: a.size,
      }))
      editingPostId.value = post.id
    }

    const cancelEditPost = () => {
      editingPostId.value = null
      editDraft.body = ''
      editDraft.attachments = []
      editMentions.value = []
      savingEdit.value = false
    }

    const onEditMention = (m) => {
      if (m && m.id) editMentions.value.push(m)
    }

    // Хендлеры для добавления вложений в режиме правки.
    const onEditImagesPicked = async (e) => {
      const files = [...(e.target?.files || [])]
      if (e.target) e.target.value = ''
      await uploadFiles(files, editDraft.attachments)
    }
    const onEditFilesPicked = async (e) => {
      const files = [...(e.target?.files || [])]
      if (e.target) e.target.value = ''
      await uploadAnyFiles(files, editDraft.attachments)
    }
    const removeEditAttachment = (i) => editDraft.attachments.splice(i, 1)

    const saveEditPost = async (post) => {
      const trimmed = (editDraft.body || '').trim()
      // Разрешаем пустой текст только если есть хотя бы одно вложение —
      // как и при публикации.
      if (!trimmed && !editDraft.attachments.length) {
        toastError('Текст или вложения должны быть')
        return
      }
      savingEdit.value = true
      try {
        const body = applyMentions(trimmed, editMentions.value)
        const updated = await api.feed.patchPost(post.id, {
          body,
          attachments: editDraft.attachments,
        })
        Object.assign(post, updated)
        cancelEditPost()
        success('Изменения сохранены')
      } catch (err) {
        toastError(err?.response?.data?.detail || 'Не удалось сохранить')
      } finally {
        savingEdit.value = false
      }
    }

    // Был ли пост отредактирован: бэк отдаёт updated_at только после
    // PATCH (server_onupdate). created_at заполнен всегда → updated_at,
    // отличный от созданного, означает правку.
    const isEdited = (post) => {
      if (!post?.updated_at) return false
      const a = String(post.created_at || '')
      const b = String(post.updated_at || '')
      return Boolean(a && b && a !== b)
    }

    const onDeletePost = async (post) => {
      closeMenu()
      if (!confirm('Удалить пост?')) return
      try {
        await api.feed.remove(post.id)
        posts.value = posts.value.filter((p) => p.id !== post.id)
        success('Пост удалён')
      } catch (e) {
        toastError('Не удалось удалить пост')
      }
    }
    const scrollToPost = (id) => {
      const el = document.querySelectorAll('.post')
      const idx = posts.value.findIndex((p) => p.id === id)
      if (idx >= 0 && el[idx]) el[idx].scrollIntoView({ behavior: 'smooth', block: 'center' })
    }

    // ---- Виджеты ----
    const taskCounts = reactive({ doing: 0, helping: 0, assigned: 0, watching: 0 })
    const summary = reactive({ active_deals: 0, overdue_tasks: 0, new_documents_7d: 0 })
    const kpiVisible = ref(false)
    const popular = ref([])
    const birthdays = ref([])
    const absentToday = ref([])
    const allUsers = ref([])

    const loadWidgets = () => {
      api.home.myTaskCounts().then((d) => { if (d) Object.assign(taskCounts, d) }).catch(() => {})
      api.home.summary().then((d) => {
        if (d) { Object.assign(summary, d); kpiVisible.value = true }
      }).catch(() => {})
      api.feed.popular({ days: 30, limit: 5 }).then((d) => {
        popular.value = Array.isArray(d) ? d : []
      }).catch(() => {})
      api.profiles.birthdays(365).then((d) => {
        birthdays.value = (Array.isArray(d) ? d : []).slice(0, 4)
      }).catch(() => {})
      api.absences.list({}).then((d) => {
        const today = new Date(); today.setHours(0, 0, 0, 0)
        const ms = today.getTime()
        absentToday.value = (Array.isArray(d) ? d : []).filter((a) => {
          const from = new Date(a.date_from); from.setHours(0, 0, 0, 0)
          const to = new Date(a.date_to); to.setHours(23, 59, 59, 999)
          return from.getTime() <= ms && ms <= to.getTime()
        })
      }).catch(() => {})
      // Список сотрудников для @-упоминаний.
      api.users.list({ limit: 500 }).then((d) => {
        const list = d?.items || d || []
        allUsers.value = list.filter(Boolean).map((u) => ({
          id: u.id, full_name: u.full_name, email: u.email, avatar_url: u.avatar_url,
        }))
      }).catch(() => {})
    }

    // ---- Хелперы ----
    // Бэкенд отдаёт created_at как naive ISO без таймзоны (сервер в МСК и
    // пишет `datetime.now()`). parseServerDate из useServerClock трактует
    // naive-строку как +03:00 — это синхронизирует отображение для всех
    // браузеров вне МСК. Форматирование тоже принудительно через
    // Europe/Moscow в utils/format.js.
    const parseBackendDate = (value) => parseServerDate(value)
    const formatWhen = (iso) => {
      if (!iso) return ''
      const d = parseBackendDate(iso)
      if (!d || !Number.isFinite(d.getTime())) return ''
      const now = new Date()
      const sameDay = d.toDateString() === now.toDateString()
      const yest = new Date(now); yest.setDate(yest.getDate() - 1)
      const isYest = d.toDateString() === yest.toDateString()
      const time = fmtTime(d)
      if (sameDay) return `сегодня в ${time}`
      if (isYest) return `вчера в ${time}`
      return fmtDate(d, { day: '2-digit', month: 'long' }) + ` в ${time}`
    }
    const formatShortDate = (iso) => {
      if (!iso) return ''
      const d = parseBackendDate(iso)
      return d && Number.isFinite(d.getTime())
        ? fmtDate(d, { day: '2-digit', month: '2-digit' })
        : ''
    }
    const shortText = (t) => {
      const s = String(t || '').trim().replace(MENTION_RE, '@$1').replace(/\s+/g, ' ')
      return s.length > 80 ? s.slice(0, 80) + '…' : (s || '(опрос)')
    }
    const pluralDays = (n) => {
      const lastTwo = n % 100, last = n % 10
      if (lastTwo >= 11 && lastTwo <= 14) return 'дней'
      if (last === 1) return 'день'
      if (last >= 2 && last <= 4) return 'дня'
      return 'дней'
    }
    const pluralVotes = (n) => {
      const lastTwo = n % 100, last = n % 10
      if (lastTwo >= 11 && lastTwo <= 14) return 'голосов'
      if (last === 1) return 'голос'
      if (last >= 2 && last <= 4) return 'голоса'
      return 'голосов'
    }
    const absenceLabel = (t) => ABSENCE_LABEL[t] || ABSENCE_LABEL.other

    // Иконка по расширению файла — для рендера чипов-вложений в посте.
    const fileIcon = (name) => {
      const ext = String(name || '').toLowerCase().split('.').pop()
      if (['pdf'].includes(ext)) return 'fas fa-file-pdf'
      if (['doc', 'docx', 'rtf', 'odt'].includes(ext)) return 'fas fa-file-word'
      if (['xls', 'xlsx', 'csv', 'ods', 'tsv'].includes(ext)) return 'fas fa-file-excel'
      if (['ppt', 'pptx', 'odp', 'key'].includes(ext)) return 'fas fa-file-powerpoint'
      if (['zip', 'rar', '7z', 'tar', 'gz', 'tgz'].includes(ext)) return 'fas fa-file-archive'
      if (['mp3', 'wav', 'ogg', 'm4a'].includes(ext)) return 'fas fa-file-audio'
      if (['mp4', 'webm', 'mov', 'avi', 'mkv'].includes(ext)) return 'fas fa-file-video'
      if (['dwg', 'dxf', 'step', 'stp', 'iges', 'igs'].includes(ext)) return 'fas fa-drafting-compass'
      if (['txt', 'md'].includes(ext)) return 'fas fa-file-alt'
      return 'fas fa-file'
    }
    const formatBytes = (n) => {
      const x = Number(n) || 0
      if (x < 1024) return x + ' Б'
      if (x < 1024 * 1024) return (x / 1024).toFixed(1) + ' КБ'
      return (x / (1024 * 1024)).toFixed(1) + ' МБ'
    }
    // Хелперы для рендера сегрегации картинок и файлов внутри одного поста.
    const postImages = (post) =>
      (post.attachments || []).filter((a) => (a.kind || 'image') !== 'file')
    const postFiles = (post) =>
      (post.attachments || []).filter((a) => a.kind === 'file')

    const onDocClick = (e) => {
      if (!e.target.closest('.post__menu')) closeMenu()
      if (!e.target.closest('.post__react-add-wrap')) reactionPickerId.value = null
    }

    onMounted(() => {
      loadFeed()
      loadWidgets()
      document.addEventListener('click', onDocClick)
    })
    onBeforeUnmount(() => {
      document.removeEventListener('click', onDocClick)
    })

    return {
      me, firstName, currentYear, canPost, EMOJI_SET,
      composerExpanded, publishing, uploading, uploadingFile, imageInput, fileInput,
      draft, canSubmit,
      resetComposer, onImagesPicked, onFilesPicked, onPaste,
      removeDraftImage, removeDraftFile, publish,
      onComposerMention, parseSegments,
      posts, loadingFeed, menuOpenId, reactionPickerId, commentState,
      toggleMenu, toggleReactionPicker, toggleReaction, reactionsTotal,
      pollPct, onVote,
      toggleComments, onCommentMention, submitComment, onDeleteComment,
      togglePin, onDeletePost, scrollToPost,
      editingPostId, savingEdit, editImageInput, editFileInput, editDraft, editMentions,
      startEditPost, cancelEditPost, saveEditPost, onEditMention, isEdited,
      onEditImagesPicked, onEditFilesPicked, removeEditAttachment,
      fileIcon, formatBytes, postImages, postFiles,
      taskCounts, summary, kpiVisible, popular, birthdays, absentToday, allUsers,
      formatWhen, formatShortDate, shortText, pluralDays, pluralVotes, absenceLabel,
    }
  },
}
</script>

<style scoped>
.feed-page {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 24px;
  max-width: 1480px;
  margin: 0 auto;
  padding: 24px;
  align-items: start;
}
@media (min-width: 2000px) {
  .feed-page { max-width: 1680px; }
}
@media (max-width: 1024px) {
  .feed-page { grid-template-columns: 1fr; gap: 16px; padding: 16px; }
  /* На мобиле лента (главный контент) — выше виджетов сайдбара, чтобы
     новости/композер не уезжали под «Мои задачи»/«Сводку».
     Сайдбар не должен «прилипать» в одноколоночной раскладке. */
  .feed-side { order: 2; position: static; }
}

/* ===== Лента ===== */
.feed-main { display: flex; flex-direction: column; gap: 16px; min-width: 0; }

.feed-state {
  padding: 40px;
  text-align: center;
  color: var(--color-text-muted, #64748b);
  background: var(--color-surface, #fff);
  border-radius: 14px;
  border: 1px solid var(--color-border, #e2e8f0);
}
.feed-state--empty { display: flex; flex-direction: column; align-items: center; gap: 10px; }
.feed-state--empty i { font-size: 2rem; color: var(--color-text-subtle, #94a3b8); }

/* ===== Composer ===== */
.composer {
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 14px;
  padding: 14px 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.composer__modes { display: flex; gap: 6px; margin-bottom: 12px; }
.composer__mode {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 12px; border-radius: 8px;
  border: 1px solid var(--color-border, #e2e8f0);
  background: var(--color-surface-2, #f8fafc);
  font-size: 0.84rem; font-weight: 600; font-family: inherit;
  color: var(--color-text-muted, #64748b); cursor: pointer;
}
.composer__mode.is-active {
  background: var(--color-primary-soft, rgba(99,102,241,0.12));
  color: var(--color-primary, #4338ca);
  border-color: var(--color-primary, #6366f1);
}
.composer__top { display: flex; gap: 12px; align-items: flex-start; }
/* Рамка вокруг ввода — по аналогии с .task-chat__composer-bar:
   мягкий бордер, при фокусе подсвечивается primary-цветом и тенью.
   Textarea внутри растёт по содержимому до :max-height="320" (см.
   проп auto-grow у MentionInput), после чего включается внутренний
   скролл — текст больше не «обрезается полем». */
.composer__input {
  flex: 1;
  min-width: 0; /* чтобы flex-child не выпинал контейнер шире родителя */
  background: var(--color-surface-2, #f8fafc);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 10px;
  padding: 8px 12px;
  transition: border-color var(--dur-fast, 0.15s) ease,
              box-shadow var(--dur-fast, 0.15s) ease;
}
.composer__input:focus-within {
  border-color: var(--color-primary, #6366f1);
  box-shadow: var(--shadow-focus, 0 0 0 3px rgba(99, 102, 241, 0.18));
}
.composer__input :deep(.mention-input__field) {
  font-size: 0.96rem;
  /* min-height и max-height приходят inline-стилем из MentionInput
     при auto-grow=true; здесь оставляем только базовый padding-фолбэк. */
  padding: 2px 0;
}

.composer__poll { margin-top: 10px; display: flex; flex-direction: column; gap: 8px; }
.composer__poll-opt { display: flex; align-items: center; gap: 8px; }
.composer__poll-opt > i { color: var(--color-text-subtle, #94a3b8); }
.composer__poll-input {
  flex: 1;
  padding: 7px 10px;
  border: 1px solid var(--color-border-strong, rgba(0,0,0,0.12));
  border-radius: 8px;
  font-size: 0.9rem; font-family: inherit;
  background: var(--color-surface-2, #f8fafc);
  color: var(--color-text, #0f172a);
}
.composer__poll-x {
  background: transparent; border: none; cursor: pointer;
  color: var(--color-text-subtle, #94a3b8); padding: 4px;
}
.composer__poll-x:hover { color: var(--color-danger, #dc2626); }
.composer__poll-add {
  align-self: flex-start;
  display: inline-flex; align-items: center; gap: 6px;
  background: transparent; border: none; cursor: pointer;
  color: var(--color-primary, #4338ca);
  font-size: 0.84rem; font-weight: 600; font-family: inherit;
  padding: 2px 0;
}
.composer__poll-opts { display: flex; gap: 16px; margin-top: 2px; }

/* Список «скрепок»-файлов в композере (и в edit-форме). */
.composer__files { display: flex; flex-direction: column; gap: 6px; margin-top: 10px; }
.composer__file-chip {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 10px; border-radius: 8px;
  background: var(--color-surface-2, #f8fafc);
  border: 1px solid var(--color-border, #e2e8f0);
  font-size: 0.85rem; color: var(--color-text, #0f172a);
  max-width: 100%;
}
.composer__file-chip > i:first-child {
  color: var(--color-primary, #4338ca); font-size: 0.95rem; flex-shrink: 0;
}
.composer__file-name {
  flex: 1; min-width: 0;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.composer__file-size {
  color: var(--color-text-subtle, #94a3b8); font-size: 0.78rem; flex-shrink: 0;
}
.composer__file-x {
  background: transparent; border: 0; cursor: pointer;
  color: var(--color-text-subtle, #94a3b8); padding: 0 4px;
  flex-shrink: 0;
}
.composer__file-x:hover { color: var(--color-danger, #dc2626); }

.composer__images { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.composer__image {
  position: relative; width: 96px; height: 96px;
  border-radius: 8px; overflow: hidden;
  border: 1px solid var(--color-border, #e2e8f0);
}
.composer__image img { width: 100%; height: 100%; object-fit: cover; }
.composer__image-x {
  position: absolute; top: 3px; right: 3px;
  width: 20px; height: 20px; border: none; border-radius: 50%;
  background: rgba(15,23,42,0.7); color: #fff;
  cursor: pointer; font-size: 0.65rem;
  display: flex; align-items: center; justify-content: center;
}
.composer__bar {
  display: flex; justify-content: space-between; align-items: center;
  gap: 10px; flex-wrap: wrap;
  margin-top: 12px; padding-top: 12px;
  border-top: 1px solid var(--color-border-subtle, rgba(0,0,0,0.06));
}
.composer__actions { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.composer__file { display: none; }
.composer__act {
  display: inline-flex; align-items: center; gap: 6px;
  background: transparent; border: none; cursor: pointer;
  color: var(--color-text-muted, #64748b);
  font-size: 0.86rem; font-weight: 600; font-family: inherit;
}
.composer__act:hover { color: var(--color-primary, #4338ca); }
.composer__opt {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 0.82rem; color: var(--color-text-muted, #64748b); cursor: pointer;
}
.composer__submit { display: flex; gap: 8px; }

/* ===== Пост ===== */
.post {
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.post.is-pinned { border-color: rgba(99,102,241,0.4); }

.post__head { display: flex; align-items: flex-start; gap: 12px; }
.post__meta { flex: 1; min-width: 0; }
.post__author { font-weight: 700; font-size: 0.95rem; color: var(--color-text, #0f172a); }
.post__sub { font-size: 0.78rem; color: var(--color-text-muted, #64748b); display: flex; gap: 5px; flex-wrap: wrap; }
.post__dot { opacity: 0.5; }
.post__badges { display: flex; gap: 6px; align-items: center; }
.post__badge {
  font-size: 0.66rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.4px; padding: 3px 8px; border-radius: 999px;
}
.post__badge.is-news { background: var(--color-primary-soft, rgba(99,102,241,0.12)); color: var(--color-primary, #4338ca); }
.post__badge.is-pin { background: rgba(234,179,8,0.18); color: #b45309; }
.post__badge.is-poll { background: rgba(20,184,166,0.16); color: #0f766e; }

.post__menu { position: relative; }
.post__menu-btn {
  background: transparent; border: none; cursor: pointer;
  color: var(--color-text-muted, #64748b);
  width: 28px; height: 28px; border-radius: 6px;
}
.post__menu-btn:hover { background: var(--color-surface-3, #f1f5f9); }
.post__menu-pop {
  position: absolute; right: 0; top: 32px;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(15,23,42,0.16);
  z-index: 10; min-width: 160px; padding: 4px;
}
.post__menu-pop button {
  display: flex; align-items: center; gap: 8px; width: 100%;
  padding: 8px 10px; background: transparent; border: none;
  cursor: pointer; font-size: 0.86rem; font-family: inherit;
  color: var(--color-text, #0f172a); border-radius: 6px; text-align: left;
}
.post__menu-pop button:hover { background: var(--color-surface-2, #f8fafc); }
.post__menu-pop button.is-danger { color: var(--color-danger, #dc2626); }

.post__body {
  margin: 12px 0;
  font-size: 0.95rem; line-height: 1.55;
  color: var(--color-text, #0f172a);
  white-space: pre-wrap; overflow-wrap: anywhere;
  max-width: 880px;
}

/* «изменено» — мягкая метка рядом с датой, как «edited» в чате задачи. */
.post__edited {
  color: var(--color-text-subtle, #94a3b8);
  font-style: italic;
}

/* Inline-редактор поста — стиль повторяет композер ленты. */
.post__edit { margin: 12px 0; display: flex; flex-direction: column; gap: 10px; }
.post__edit-actions {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; flex-wrap: wrap;
}
.post__edit-add {
  display: inline-flex; align-items: center; gap: 14px; flex-wrap: wrap;
}
.post__edit-hint {
  font-size: 0.8rem;
  color: var(--color-text-muted, #64748b);
  display: inline-flex; align-items: center; gap: 6px;
}
.post__edit-buttons { display: flex; gap: 8px; margin-left: auto; }

/* Файлы поста (read-mode) — кликабельные строки-«скрепки». */
.post__files {
  display: flex; flex-direction: column; gap: 6px; margin-top: 10px;
}
.post__file {
  display: inline-flex; align-items: center; gap: 10px;
  padding: 8px 12px; border-radius: 8px;
  background: var(--color-surface-2, #f8fafc);
  border: 1px solid var(--color-border, #e2e8f0);
  text-decoration: none; color: var(--color-text, #0f172a);
  font-size: 0.88rem;
  transition: border-color var(--dur-fast, 0.15s) ease, background var(--dur-fast, 0.15s) ease;
}
.post__file:hover {
  border-color: var(--color-primary, #6366f1);
  background: var(--color-primary-soft, rgba(99,102,241,0.08));
}
.post__file > i:first-child {
  color: var(--color-primary, #4338ca); font-size: 1.1rem; flex-shrink: 0;
}
.post__file-name {
  flex: 1; min-width: 0;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.post__file-size {
  color: var(--color-text-subtle, #94a3b8); font-size: 0.78rem; flex-shrink: 0;
}
.post__file-dl {
  color: var(--color-text-subtle, #94a3b8); font-size: 0.82rem; flex-shrink: 0;
}
.post__mention {
  color: var(--color-primary, #4338ca);
  font-weight: 600;
  background: var(--color-primary-soft, rgba(99,102,241,0.1));
  border-radius: 4px;
  padding: 0 3px;
}

/* ===== Опрос в посте ===== */
.poll { margin: 12px 0; display: flex; flex-direction: column; gap: 6px; max-width: 560px; }
.poll__opt {
  position: relative;
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  background: var(--color-surface-2, #f8fafc);
  transition: border-color 0.1s;
}
.poll__opt:hover { border-color: var(--color-primary, #6366f1); }
.poll__opt.is-voted { border-color: var(--color-primary, #6366f1); }
.poll__bar {
  position: absolute; inset: 0 auto 0 0;
  background: var(--color-primary-soft, rgba(99,102,241,0.18));
  transition: width 0.3s ease;
}
.poll__opt.is-voted .poll__bar { background: rgba(99,102,241,0.3); }
.poll__opt-row {
  position: relative;
  display: flex; align-items: center; gap: 8px;
  padding: 9px 12px;
}
.poll__check { color: var(--color-primary, #6366f1); }
.poll__text { flex: 1; font-size: 0.9rem; color: var(--color-text, #0f172a); }
.poll__voters { display: inline-flex; align-items: center; gap: 2px; }
.poll__voters-more { font-size: 0.7rem; color: var(--color-text-muted, #64748b); margin-left: 2px; }
.poll__pct {
  font-size: 0.84rem; font-weight: 700;
  color: var(--color-text, #0f172a);
  font-variant-numeric: tabular-nums;
  min-width: 38px; text-align: right;
}
.poll__foot { font-size: 0.76rem; color: var(--color-text-muted, #64748b); margin-top: 2px; }

.post__images {
  display: grid; gap: 6px; margin-bottom: 12px;
  border-radius: 10px; overflow: hidden;
}
.post__images.count-1 { grid-template-columns: 1fr; }
.post__images.count-2 { grid-template-columns: 1fr 1fr; }
.post__images.count-3, .post__images.count-4 { grid-template-columns: 1fr 1fr; }
.post__image { display: block; }
.post__image img {
  width: 100%; height: 100%; max-height: 420px;
  object-fit: cover; display: block;
}
.post__images.count-1 .post__image img {
  max-height: 520px; object-fit: contain;
  background: var(--color-surface-2, #f8fafc);
}

.post__footer {
  display: flex; align-items: center; gap: 8px;
  padding-top: 10px; flex-wrap: wrap;
  border-top: 1px solid var(--color-border-subtle, rgba(0,0,0,0.06));
}
.post__reactions { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.post__reaction {
  display: inline-flex; align-items: center; gap: 5px;
  background: var(--color-surface-2, #f8fafc);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 999px;
  padding: 3px 9px;
  font-size: 0.8rem; font-weight: 600; font-family: inherit;
  color: var(--color-text, #0f172a); cursor: pointer;
}
.post__reaction.is-mine {
  background: var(--color-primary-soft, rgba(99,102,241,0.14));
  border-color: var(--color-primary, #6366f1);
}
.post__reaction-emoji { font-size: 0.95rem; }
.post__react-add-wrap { position: relative; }
.post__react-add {
  display: inline-flex; align-items: center; justify-content: center;
  width: 30px; height: 26px;
  background: transparent;
  border: 1px dashed var(--color-border-strong, rgba(0,0,0,0.18));
  border-radius: 999px;
  color: var(--color-text-muted, #64748b); cursor: pointer;
}
.post__react-add:hover { color: var(--color-primary, #4338ca); border-color: var(--color-primary, #6366f1); }
.post__react-picker {
  position: absolute; left: 0; bottom: calc(100% + 6px);
  display: flex; gap: 2px;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 999px;
  padding: 4px 6px;
  box-shadow: 0 8px 24px rgba(15,23,42,0.16);
  z-index: 12;
}
.post__react-picker button {
  background: transparent; border: none; cursor: pointer;
  font-size: 1.2rem; padding: 2px 4px; border-radius: 6px;
}
.post__react-picker button:hover { background: var(--color-surface-2, #f8fafc); transform: scale(1.15); }

.post__react {
  display: inline-flex; align-items: center; gap: 6px;
  background: transparent; border: none; cursor: pointer;
  padding: 6px 10px; border-radius: 8px;
  color: var(--color-text-muted, #64748b);
  font-size: 0.84rem; font-weight: 600; font-family: inherit;
}
.post__react:hover { background: var(--color-surface-2, #f8fafc); }
.post__views {
  margin-left: auto;
  display: inline-flex; align-items: center; gap: 6px;
  color: var(--color-text-subtle, #94a3b8); font-size: 0.82rem;
}

/* ===== Комментарии ===== */
.post__comments {
  margin-top: 12px; padding-top: 12px;
  border-top: 1px solid var(--color-border-subtle, rgba(0,0,0,0.06));
  display: flex; flex-direction: column; gap: 10px;
}
.post__comments-loading { font-size: 0.84rem; color: var(--color-text-muted, #64748b); }
.comment { display: flex; gap: 8px; }
.comment__bubble {
  flex: 1; min-width: 0;
  background: var(--color-surface-2, #f8fafc);
  border-radius: 10px; padding: 8px 12px;
}
.comment__head { display: flex; align-items: baseline; gap: 8px; }
.comment__head strong { font-size: 0.84rem; color: var(--color-text, #0f172a); }
.comment__when { font-size: 0.72rem; color: var(--color-text-subtle, #94a3b8); }
.comment__del {
  margin-left: auto; background: transparent; border: none; cursor: pointer;
  color: var(--color-text-subtle, #94a3b8); font-size: 0.72rem;
}
.comment__del:hover { color: var(--color-danger, #dc2626); }
.comment__text {
  font-size: 0.88rem; color: var(--color-text, #0f172a);
  line-height: 1.45; white-space: pre-wrap; overflow-wrap: anywhere;
}

.comment-form { display: flex; gap: 8px; align-items: center; }
.comment-form__input {
  flex: 1;
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 999px;
  padding: 8px 14px;
  background: var(--color-surface-2, #f8fafc);
}
.comment-form__input :deep(.mention-input__field) { font-size: 0.88rem; }
.comment-form__send {
  width: 34px; height: 34px;
  border: none; border-radius: 50%;
  background: var(--color-primary, #6366f1); color: #fff;
  cursor: pointer; flex-shrink: 0;
}
.comment-form__send:disabled { opacity: 0.4; cursor: not-allowed; }

/* ===== Сайдбар ===== */
.feed-side { display: flex; flex-direction: column; gap: 14px; position: sticky; top: 12px; }
.widget {
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 14px;
  padding: 14px 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.widget__title { margin: 0 0 12px; font-size: 0.95rem; font-weight: 700; color: var(--color-text, #0f172a); }
.widget__tasks { display: flex; flex-direction: column; gap: 4px; }
.wtask {
  display: flex; justify-content: space-between; align-items: center;
  padding: 7px 10px; border-radius: 8px;
  text-decoration: none; color: var(--color-text, #0f172a); font-size: 0.88rem;
}
.wtask:hover { background: var(--color-surface-2, #f8fafc); }
.wtask__count {
  background: var(--color-primary-soft, rgba(99,102,241,0.12));
  color: var(--color-primary, #4338ca);
  font-weight: 700; font-size: 0.8rem;
  padding: 1px 9px; border-radius: 999px;
  min-width: 26px; text-align: center;
}
.widget__kpi { display: flex; flex-direction: column; gap: 6px; }
.wkpi {
  display: flex; align-items: baseline; gap: 8px;
  padding: 6px 10px; border-radius: 8px;
  text-decoration: none; color: var(--color-text, #0f172a);
}
.wkpi:hover { background: var(--color-surface-2, #f8fafc); }
.wkpi__value { font-size: 1.2rem; font-weight: 700; font-variant-numeric: tabular-nums; }
.wkpi__label { font-size: 0.8rem; color: var(--color-text-muted, #64748b); }
.wkpi.is-warn .wkpi__value { color: var(--color-danger, #dc2626); }
.widget__popular { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.widget__popular li { cursor: pointer; }
.widget__popular li:hover .wpop__text { color: var(--color-primary, #4338ca); }
.wpop__text { font-size: 0.84rem; color: var(--color-text, #0f172a); line-height: 1.4; }
.wpop__meta { font-size: 0.74rem; color: var(--color-text-subtle, #94a3b8); display: flex; gap: 10px; margin-top: 2px; }
.wpop__meta i { margin-right: 3px; }
.widget__people { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.widget__people li { display: flex; align-items: center; gap: 10px; }
.wperson__meta { flex: 1; min-width: 0; }
.wperson__name {
  font-size: 0.86rem; font-weight: 600; color: var(--color-text, #0f172a);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.wperson__sub { font-size: 0.74rem; color: var(--color-text-muted, #64748b); }
.wperson__today { color: var(--color-success, #16a34a); font-weight: 600; }
.wperson__gift { color: #e11d48; }
.wperson__abs { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.wperson__abs.is-vacation { background: #16a34a; }
.wperson__abs.is-sick_leave { background: #dc2626; }
.wperson__abs.is-business_trip { background: #6366f1; }
.wperson__abs.is-other { background: #94a3b8; }
.widget__more {
  display: block; margin-top: 10px;
  font-size: 0.8rem; color: var(--color-primary, #4338ca); text-decoration: none;
}
.widget__more:hover { text-decoration: underline; }
.feed-side__foot {
  font-size: 0.74rem; color: var(--color-text-subtle, #94a3b8);
  text-align: center; padding: 4px;
}
</style>
