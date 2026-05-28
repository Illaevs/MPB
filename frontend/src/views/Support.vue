<template>
  <div class="sup-view h-100 d-flex flex-column p-3">
    <section class="sup-tb">
      <div class="sup-tb__row">
        <h1 class="sup-tb__title">Тех. поддержка</h1>

        <label class="sup-tb__search">
          <i class="fas fa-search"></i>
          <input
            v-model.trim="filters.q"
            type="search"
            placeholder="Поиск по теме или номеру…"
            @input="debouncedLoad"
          />
          <button
            v-if="filters.q"
            type="button"
            class="sup-tb__search-clear"
            title="Очистить"
            @click="filters.q = ''; load()"
          >
            <i class="fas fa-times"></i>
          </button>
        </label>

        <div class="sup-tb__field">
          <i class="fas fa-circle-half-stroke"></i>
          <select v-model="filters.status" @change="load">
            <option value="">Все статусы</option>
            <option v-for="s in STATUS_LIST" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
        </div>
        <div class="sup-tb__field">
          <i class="fas fa-tag"></i>
          <select v-model="filters.category" @change="load">
            <option value="">Все категории</option>
            <option v-for="c in CATEGORY_LIST" :key="c.value" :value="c.value">{{ c.label }}</option>
          </select>
        </div>

        <span class="sup-tb__spacer"></span>
        <span class="sup-tb__total">Всего: {{ tickets.length }}</span>

        <button type="button" class="sup-tb__btn sup-tb__btn--primary" @click="openCreate">
          <i class="fas fa-plus"></i><span>Новое обращение</span>
        </button>
      </div>
    </section>

    <div class="sup-main flex-grow-1 d-flex flex-column">
      <div v-if="loading" class="sup-state"><i class="fas fa-spinner fa-spin"></i> Загрузка…</div>
      <div v-else-if="!tickets.length" class="sup-state">
        <i class="far fa-folder-open"></i>
        <span>Обращений нет.<template v-if="!isStaff"> Создайте первое кнопкой «Новое обращение».</template></span>
      </div>
      <div v-else class="sup-grid-wrap">
        <div class="sup-grid">
          <header class="sup-grid__head">
            <span class="sup-grid__col sup-grid__col--num">№</span>
            <span class="sup-grid__col">Тема</span>
            <span class="sup-grid__col">Категория</span>
            <span class="sup-grid__col">Статус</span>
            <span class="sup-grid__col">
              <i class="far fa-user sup-grid__lead"></i>Автор
            </span>
            <span class="sup-grid__col">
              <i class="far fa-comment-dots sup-grid__lead"></i>Последнее сообщение
            </span>
          </header>

          <article
            v-for="t in tickets"
            :key="t.id"
            class="sup-row"
            @click="openTicket(t)"
          >
            <div class="sup-row__num">#{{ t.number }}</div>

            <div class="sup-row__main">
              <span class="sup-row__dot" :style="{ background: statusColor(t.status) }" :title="stLabel(t.status)"></span>
              <span class="sup-row__title">{{ t.subject }}</span>
              <i
                v-if="t.attachments && t.attachments.length"
                class="sup-row__clip fas fa-paperclip"
                :title="t.attachments.length + ' файл(ов)'"
              ></i>
              <i
                v-if="t.linked_task_id"
                class="sup-row__clip fas fa-list-check"
                :title="'Задача #' + t.linked_task_number"
              ></i>
            </div>

            <div class="sup-row__cell">
              <span class="sup-chip" :class="`sup-chip--cat-${t.category}`">{{ catLabel(t.category) }}</span>
            </div>

            <div class="sup-row__cell">
              <span class="sup-chip" :class="`sup-chip--st-${t.status}`">{{ stLabel(t.status) }}</span>
            </div>

            <div class="sup-row__people">
              <span
                class="sup-av"
                :style="authorAvatar(t).url ? null : { background: authorAvatar(t).bg, color: authorAvatar(t).fg }"
                :title="t.created_by_name || ''"
              >
                <img
                  v-if="authorAvatar(t).url && !brokenAv[t.created_by_id]"
                  :src="authorAvatar(t).url"
                  :alt="t.created_by_name || ''"
                  @error="brokenAv[t.created_by_id] = true"
                />
                <span v-else>{{ authorAvatar(t).initial }}</span>
              </span>
              <span class="sup-row__ellipsis">{{ t.created_by_name || '—' }}</span>
            </div>

            <div class="sup-row__last">
              <template v-if="t.last_message_at">
                <span class="sup-row__last-line">
                  <i class="far fa-clock"></i>{{ fmtDateTime(t.last_message_at) }}
                </span>
                <span class="sup-row__last-user">
                  <i class="far fa-comment"></i>{{ t.last_message_by || '—' }}
                </span>
              </template>
              <template v-else>
                <span class="sup-row__last-line sup-row__last-line--muted">
                  <i class="far fa-calendar-alt"></i>{{ fmtDate(t.created_at) }}
                </span>
                <span class="sup-row__last-user sup-row__last-user--muted">нет сообщений</span>
              </template>
            </div>
          </article>
        </div>
      </div>
    </div>

    <TicketDrawer
      v-model="drawerOpen"
      :mode="drawerMode"
      :ticket-id="activeId"
      :is-staff="isStaff"
      :users="users"
      @saved="load"
    />
  </div>
</template>

<script>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../services/api'
import { useToast } from '../composables/useToast'
import { useAuthStore } from '../stores/auth'
import { normalizeAvatarUrl } from '../utils/avatar'
import TicketDrawer from '../components/TicketDrawer.vue'
import { formatDate, formatDateTime } from '../utils/format'

const AVATAR_THEMES = [
  { bg: 'linear-gradient(135deg, #d7e7ff 0%, #b4d0ff 100%)', fg: '#2563eb' },
  { bg: 'linear-gradient(135deg, #ffe4d3 0%, #ffc79c 100%)', fg: '#b45309' },
  { bg: 'linear-gradient(135deg, #e8ddff 0%, #c8b4ff 100%)', fg: '#7c3aed' },
  { bg: 'linear-gradient(135deg, #d9f7ec 0%, #a9e7cb 100%)', fg: '#0f8f5d' },
  { bg: 'linear-gradient(135deg, #ffe7ef 0%, #ffc3d3 100%)', fg: '#be185d' },
]
const themeFor = (seed) => {
  const k = String(seed || '?')
  const i = k.split('').reduce((s, c) => s + c.charCodeAt(0), 0) % AVATAR_THEMES.length
  return AVATAR_THEMES[i]
}

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
const STATUS_COLORS = {
  new: '#2563eb',
  in_progress: '#d97706',
  waiting_user: '#7c3aed',
  resolved: '#16a34a',
  closed: '#16a34a',
  rejected: '#dc2626',
}

export default {
  name: 'Support',
  components: { TicketDrawer },
  setup() {
    const toast = useToast()
    const auth = useAuthStore()
    const route = useRoute()

    const isStaff = computed(() =>
      Boolean(auth.isSuperuser || auth.permissions?.support?.read_all)
    )

    const tickets = ref([])
    const users = ref([])
    const loading = ref(false)
    const filters = reactive({ q: '', status: '', category: '' })

    const drawerOpen = ref(false)
    const drawerMode = ref('view')
    const activeId = ref(null)

    const brokenAv = reactive({})

    const catLabel = (v) => (CATEGORY_LIST.find((c) => c.value === v) || {}).label || v
    const stLabel = (v) => (STATUS_LIST.find((s) => s.value === v) || {}).label || v
    const statusColor = (v) => STATUS_COLORS[v] || '#94a3b8'
    const fmtDate = (v) => {
      if (!v) return ''
      try { return formatDate(v, { day: '2-digit', month: 'short', year: '2-digit' }) }
      catch { return v }
    }
    const fmtDateTime = (v) => {
      if (!v) return ''
      try {
        return formatDateTime(v, {
          day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
        })
      } catch { return v }
    }
    const authorAvatar = (t) => {
      const name = String(t.created_by_name || '?').trim()
      let url = ''
      if (t.created_by_avatar) {
        try { url = normalizeAvatarUrl(t.created_by_avatar, t.created_by_id) || '' }
        catch (_e) { url = t.created_by_avatar }
      }
      const theme = themeFor(`${t.created_by_id}${name}`)
      return { url, initial: (name.charAt(0) || '?').toUpperCase(), bg: theme.bg, fg: theme.fg }
    }

    const load = async () => {
      loading.value = true
      try {
        const params = {}
        if (filters.q) params.q = filters.q
        if (filters.status) params.status = filters.status
        if (filters.category) params.category = filters.category
        tickets.value = await api.support.listTickets(params)
      } catch (e) {
        toast.error('Не удалось загрузить обращения')
      } finally {
        loading.value = false
      }
    }
    let t = null
    const debouncedLoad = () => { clearTimeout(t); t = setTimeout(load, 350) }

    const loadUsers = async () => {
      if (!isStaff.value) return
      try { users.value = await api.users.list() } catch (_e) { /* non-fatal */ }
    }

    const openCreate = () => {
      drawerMode.value = 'create'
      activeId.value = null
      drawerOpen.value = true
    }
    const openTicket = (t0) => {
      drawerMode.value = 'view'
      activeId.value = t0.id
      drawerOpen.value = true
    }

    onMounted(async () => {
      await Promise.all([load(), loadUsers()])
      const qid = route.query.ticket_id
      if (qid) {
        const found = tickets.value.find((x) => String(x.id) === String(qid))
        if (found) openTicket(found)
      }
    })

    return {
      isStaff, tickets, users, loading, filters,
      drawerOpen, drawerMode, activeId,
      CATEGORY_LIST, STATUS_LIST,
      catLabel, stLabel, statusColor, fmtDate, fmtDateTime, authorAvatar, brokenAv,
      load, debouncedLoad,
      openCreate, openTicket,
    }
  },
}
</script>

<style>
/* ============================================================
   Support — визуально/механически 1:1 c модулем «Задачи»:
   единый тулбар-лист (склеенные карточки), плоские строки.
   Метрики скопированы из TasksToolbar.vue / TaskBoards.vue.
   ============================================================ */
.sup-view { gap: 0 !important; }

.sup-tb {
  padding: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-bottom: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  position: relative;
  z-index: 20;
  flex-shrink: 0;
}
.sup-tb__row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  flex-wrap: wrap;
}
.sup-tb__title {
  margin: 0 4px 0 0;
  font-size: var(--text-xl);
  font-weight: var(--fw-bold);
  color: var(--color-text);
}
.sup-tb__spacer { flex: 1; }
.sup-tb__total {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  font-weight: var(--fw-medium);
  white-space: nowrap;
}

.sup-tb__search {
  flex: 1;
  min-width: 220px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 38px;
  padding: 0 14px;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  color: var(--color-text);
  transition: border-color var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out);
}
.sup-tb__search:focus-within {
  border-color: var(--color-primary);
  background: var(--color-surface);
  box-shadow: var(--shadow-focus);
}
.sup-tb__search > i { color: var(--color-text-subtle); }
.sup-tb__search input {
  flex: 1;
  border: 0;
  outline: 0;
  background: transparent;
  font-size: var(--text-md);
  color: var(--color-text);
  padding: 0;
  min-width: 0;
}
.sup-tb__search input::placeholder { color: var(--color-text-subtle); }
.sup-tb__search-clear {
  border: 0;
  background: transparent;
  color: var(--color-text-subtle);
  cursor: pointer;
  padding: 4px;
  border-radius: var(--radius-sm);
}
.sup-tb__search-clear:hover { color: var(--color-text); background: var(--color-surface-3); }

.sup-tb__field {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 34px;
  padding: 0 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text-muted);
}
.sup-tb__field select {
  border: 0;
  outline: 0;
  background: transparent;
  font: inherit;
  font-size: var(--text-md);
  color: var(--color-text);
  cursor: pointer;
  padding-right: 18px;
}

.sup-tb__btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 38px;
  padding: 0 14px;
  border-radius: var(--radius-md);
  font-size: var(--text-md);
  font-weight: var(--fw-medium);
  cursor: pointer;
  white-space: nowrap;
  line-height: 1;
  border: 1px solid var(--color-primary);
  transition: background var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out);
}
.sup-tb__btn i { font-size: var(--text-base); }
.sup-tb__btn--primary { background: var(--color-primary); color: var(--color-on-primary); }
.sup-tb__btn--primary:hover { background: var(--color-primary-hover); border-color: var(--color-primary-hover); }

/* ---- glued list sheet ---- */
.sup-main {
  border: 1px solid var(--color-border-subtle);
  border-top: 0;
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
  background: var(--color-surface);
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
  flex: 1 1 auto;
  min-height: 0;
  padding: 0;
  overflow: hidden; /* клипает скругление + sticky-шапку, рамка цельная */
}
.sup-state {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  flex: 1; color: var(--color-text-muted); padding: 56px 12px; font-size: var(--text-md);
}
.sup-grid-wrap { flex: 1 1 auto; min-height: 0; overflow: auto; }
.sup-grid { display: flex; flex-direction: column; background: var(--color-surface); }

.sup-grid__head,
.sup-row {
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr) 200px 140px 210px 210px;
  align-items: center;
  gap: var(--space-3);
  padding: 12px 16px;
}
.sup-grid__head {
  padding-top: 10px;
  padding-bottom: 10px;
  background: var(--color-surface-2);
  border-bottom: 1px solid var(--color-border);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.4px;
  color: var(--color-text-muted);
  font-weight: var(--fw-semibold);
  position: sticky;
  top: 0;
  z-index: 1;
}
:root[data-theme="dark"] .sup-grid__head {
  background: rgba(15, 23, 42, 0.55);
  border-bottom-color: var(--glass-border-dark);
}
.sup-grid__col { display: inline-flex; align-items: center; gap: 8px; justify-self: start; }
.sup-grid__col--num { justify-self: start; }
.sup-grid__lead {
  font-size: var(--text-base);
  color: var(--color-text-subtle);
  width: 14px;
  text-align: center;
}

.sup-row {
  border-top: 1px solid var(--color-border-subtle);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out);
}
.sup-row:hover { background: var(--color-surface-2); }
.sup-row__num {
  font-variant-numeric: tabular-nums;
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  color: var(--color-text-muted);
}
.sup-row__main {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
  justify-self: start;
}
.sup-row__dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.sup-row__title {
  flex: 0 1 auto;
  min-width: 0;
  font-size: var(--text-md);
  font-weight: var(--fw-medium);
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sup-row__clip { flex-shrink: 0; font-size: var(--text-base); color: var(--color-text-subtle); }
.sup-row__cell { justify-self: start; min-width: 0; }
.sup-row__people {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-sm);
  color: var(--color-text);
  min-width: 0;
  justify-self: start;
}
.sup-row__lead { color: var(--color-text-subtle); flex-shrink: 0; }
.sup-row__ellipsis { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* author avatar pill — как в задачах (AssigneeStack) */
.sup-av {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  font-size: var(--text-xs);
  font-weight: var(--fw-bold);
  border: 2px solid var(--color-surface);
  box-shadow: 0 0 0 1px var(--color-border-subtle);
  background: var(--color-surface-3);
  color: var(--color-text);
}
.sup-av img { width: 100%; height: 100%; object-fit: cover; }

/* индикатор последнего сообщения: дата+время / автор */
.sup-row__last {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
  justify-self: start;
}
.sup-row__last-line {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-sm);
  color: var(--color-text);
  white-space: nowrap;
}
.sup-row__last-line i { color: var(--color-text-subtle); }
.sup-row__last-line--muted { color: var(--color-text-muted); }
.sup-row__last-user {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sup-row__last-user i { color: var(--color-text-subtle); }
.sup-row__last-user--muted { color: var(--color-text-subtle); font-style: italic; }

.sup-chip {
  display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px;
  border-radius: var(--radius-pill); font-size: var(--text-xs); font-weight: var(--fw-bold);
  line-height: 1; background: var(--color-surface-3); color: var(--color-text-muted);
}
.sup-chip--cat-bug { background: var(--color-danger-soft); color: var(--color-danger); }
.sup-chip--cat-improvement { background: var(--color-primary-soft); color: var(--color-primary); }
.sup-chip--cat-access { background: color-mix(in srgb, var(--color-warning) 16%, transparent); color: var(--color-warning); }
.sup-chip--cat-question { background: color-mix(in srgb, #0d9488 16%, transparent); color: #0d9488; }
.sup-chip--st-new { background: var(--color-primary-soft); color: var(--color-primary); }
.sup-chip--st-in_progress { background: color-mix(in srgb, var(--color-warning) 16%, transparent); color: var(--color-warning); }
.sup-chip--st-waiting_user { background: color-mix(in srgb, #7c3aed 16%, transparent); color: #7c3aed; }
.sup-chip--st-resolved,
.sup-chip--st-closed { background: var(--color-success-soft); color: var(--color-success); }
.sup-chip--st-rejected { background: var(--color-danger-soft); color: var(--color-danger); }

@media (max-width: 900px) {
  .sup-grid__head { display: none; }
  .sup-grid__head,
  .sup-row { grid-template-columns: 52px minmax(0, 1fr) auto; }
  .sup-row__cell,
  .sup-row__people { display: none; }
}
</style>
