<template>
  <div class="workday-view">
   <div class="workday-shell">
    <!-- Тулбар: переключатель вида + период -->
    <div class="workday-toolbar">
      <div class="wd-switch">
        <button
          type="button"
          class="wd-switch__btn"
          :class="{ 'is-active': viewMode === 'byUser' }"
          @click="viewMode = 'byUser'"
        >
          <i class="fas fa-user-clock"></i> По сотруднику
        </button>
        <button
          type="button"
          class="wd-switch__btn"
          :class="{ 'is-active': viewMode === 'grid' }"
          @click="switchToGrid"
        >
          <i class="fas fa-table-cells"></i> Таблица
        </button>
      </div>
      <div class="workday-toolbar__period">
        <label><span>с</span><input type="date" v-model="dateFrom" @change="reload" /></label>
        <label><span>по</span><input type="date" v-model="dateTo" @change="reload" /></label>
      </div>
    </div>

    <!-- ВИД 1: по сотруднику (sidebar + детали) -->
    <div v-if="viewMode === 'byUser'" class="workday-byuser">
    <!-- Sidebar: пользователи с их сум. временем -->
    <aside class="workday-sidebar">
      <div class="workday-sidebar__head">
        <h3>Сотрудники</h3>
        <span class="workday-sidebar__count">{{ users.length }}</span>
      </div>
      <div class="workday-sidebar__list">
        <div
          v-for="u in users"
          :key="u.user_id"
          class="workday-user-row"
          :class="{ 'is-selected': selectedId === u.user_id }"
          @click="select(u.user_id)"
        >
          <UiAvatar :name="u.full_name || u.email" size="sm" />
          <div class="workday-user-row__meta">
            <div class="workday-user-row__name">
              {{ u.full_name || u.email }}
              <span v-if="u.has_active" class="workday-user-row__dot" title="Сейчас работает"></span>
            </div>
            <div class="workday-user-row__role">{{ u.role_name || '—' }}</div>
          </div>
          <div class="workday-user-row__total">
            <strong>{{ formatHours(u.total_seconds) }}</strong>
            <small>{{ u.sessions_count }} {{ pluralSessions(u.sessions_count) }}</small>
            <span
              v-if="!u.worked_today && !u.has_active"
              class="workday-absent-tag"
              title="Сегодня сессий не было"
            >не было сегодня</span>
          </div>
        </div>
        <div v-if="loadingList" class="workday-sidebar__loading">Загрузка…</div>
        <div v-else-if="!users.length" class="workday-sidebar__empty">
          Нет данных за период
        </div>
      </div>
    </aside>

    <!-- Main: детальная статистика -->
    <main class="workday-main">
      <header class="workday-main__head">
        <div class="workday-main__title">
          <h2>{{ selectedUser?.full_name || selectedUser?.email || 'Выберите сотрудника' }}</h2>
          <small v-if="selectedUser?.role_name">{{ selectedUser.role_name }}</small>
        </div>
        <div class="workday-main__totals">
          <div class="workday-kpi">
            <span class="workday-kpi__label">За период</span>
            <strong class="workday-kpi__value">{{ formatHours(stats?.total_seconds || 0) }}</strong>
          </div>
          <div class="workday-kpi">
            <span class="workday-kpi__label">Сессий</span>
            <strong class="workday-kpi__value">{{ stats?.sessions_count || 0 }}</strong>
          </div>
          <select v-model="groupby" class="workday-groupby" @change="reload">
            <option value="day">По дням</option>
            <option value="week">По неделям</option>
            <option value="month">По месяцам</option>
          </select>
        </div>
      </header>

      <div v-if="loadingStats" class="workday-main__loading">Загрузка статистики…</div>

      <section
        v-for="bucket in stats?.buckets || []"
        :key="bucket.key"
        class="workday-bucket"
      >
        <div class="workday-bucket__head">
          <h4>{{ bucket.label }}</h4>
          <span class="workday-bucket__total">{{ formatHours(bucket.total_seconds) }}</span>
        </div>

        <!-- Тайм-лайн дня: 00–24 ч, зелёные блоки = сессии. Только для groupby=day. -->
        <div v-if="groupby === 'day'" class="workday-timeline" :aria-label="`Тайм-лайн дня ${bucket.label}`">
          <div class="workday-timeline-grid">
            <span v-for="h in [0,3,6,9,12,15,18,21,24]" :key="h" :style="{ left: (h / 24 * 100) + '%' }">
              {{ String(h).padStart(2,'0') }}
            </span>
          </div>
          <div class="workday-timeline-track">
            <div
              v-for="s in bucket.sessions"
              :key="s.id + '-bar'"
              class="workday-timeline-bar"
              :class="{ 'is-active': s.is_active, 'is-idle': s.ended_reason === 'idle' }"
              :style="timelineBarStyle(s, bucket.key)"
              :title="timelineBarTitle(s)"
            ></div>
          </div>
        </div>

        <table class="workday-bucket__table">
          <thead>
            <tr>
              <th>Начало</th>
              <th>Конец</th>
              <th>Длительность</th>
              <th>Закрытие</th>
              <th>План на день</th>
              <th>Итог дня</th>
              <th v-if="canAdminEdit" class="workday-cell-actions"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="s in bucket.sessions"
              :key="s.id"
              :class="{ 'is-anomaly': isAnomaly(s) }"
              :title="anomalyHint(s)"
            >
              <td class="workday-cell-time">{{ formatTime(s.started_at) }}</td>
              <td class="workday-cell-time">
                <span v-if="s.ended_at">{{ formatTime(s.ended_at) }}</span>
                <span v-else class="workday-active-pill">идёт</span>
              </td>
              <td class="workday-cell-dur">{{ formatHours(s.duration_seconds) }}</td>
              <td>
                <span class="workday-reason" :class="reasonClass(s.ended_reason)">
                  {{ reasonLabel(s.ended_reason) }}
                </span>
              </td>
              <td class="workday-cell-note">{{ s.note_start || '—' }}</td>
              <td class="workday-cell-note">{{ s.note_end || '—' }}</td>
              <td v-if="canAdminEdit" class="workday-cell-actions">
                <button
                  type="button"
                  class="workday-edit-btn"
                  title="Исправить сессию"
                  @click="openEdit(s)"
                ><i class="fas fa-pen"></i></button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- Inline-правка сессии (workday_admin). -->
      <Teleport to="body">
        <transition name="wd-edit">
          <div v-if="editOpen" class="wd-edit-overlay" v-modal-close="closeEdit">
            <div class="wd-edit-card" role="dialog" aria-modal="true">
              <h3 class="wd-edit-title">Исправить сессию</h3>
              <p class="wd-edit-hint">
                Изменения попадают в журнал как <strong>«Админ-правка»</strong>.
                Время — в часовом поясе браузера; на сервер уходит UTC.
              </p>
              <div class="wd-edit-grid">
                <label>
                  <span>Начало</span>
                  <input type="datetime-local" v-model="editForm.started_at" />
                </label>
                <label>
                  <span>Конец</span>
                  <input type="datetime-local" v-model="editForm.ended_at" />
                  <small>Пусто = снова активная сессия</small>
                </label>
                <label>
                  <span>Причина закрытия</span>
                  <select v-model="editForm.ended_reason" :disabled="!editForm.ended_at">
                    <option value="manual">Вручную</option>
                    <option value="idle">Авто (бездействие)</option>
                    <option value="admin">Админ-правка</option>
                  </select>
                </label>
                <label class="wd-edit-grid-full">
                  <span>План на день</span>
                  <textarea v-model="editForm.note_start" rows="2" />
                </label>
                <label class="wd-edit-grid-full">
                  <span>Итог дня</span>
                  <textarea v-model="editForm.note_end" rows="2" />
                </label>
              </div>
              <div v-if="editError" class="wd-edit-error">{{ editError }}</div>
              <div class="wd-edit-actions">
                <UiButton variant="ghost" size="sm" :disabled="editSaving" @click="closeEdit">
                  Отмена
                </UiButton>
                <UiButton
                  variant="primary"
                  size="sm"
                  icon-left="fas fa-check"
                  :loading="editSaving"
                  @click="saveEdit"
                >
                  Сохранить
                </UiButton>
              </div>
            </div>
          </div>
        </transition>
      </Teleport>

      <div v-if="!loadingStats && !(stats?.buckets || []).length" class="workday-main__empty">
        Нет сессий за выбранный период
      </div>
    </main>
    </div>

    <!-- ВИД 2: таблица — все сотрудники строками, дни колонками -->
    <div v-else class="workday-grid">
      <div v-if="loadingGrid" class="workday-grid__loading">Загрузка…</div>
      <div v-else-if="!gridRows.length" class="workday-grid__empty">
        Нет сотрудников с учётом рабочего времени за период.
      </div>
      <div
        v-else
        class="wd-table"
        :style="{ '--col-user': '240px', '--col-total': '92px', '--cols-days': gridDays.length, '--col-day-min': gridDayWidth + 'px' }"
      >
        <!-- Шапка -->
        <div class="wd-row wd-row--head">
          <div class="wd-cell wd-cell--user wd-cell--head">Сотрудник</div>
          <div class="wd-axis wd-axis--head">
            <div
              v-for="(d, idx) in gridDays"
              :key="`gh-${idx}`"
              class="wd-day"
              :class="{ 'is-weekend': isWeekend(d), 'is-today': isGridToday(d), 'is-first': d.getDate() === 1 || idx === 0 }"
              :title="formatGridHover(d)"
            >
              <span class="wd-day__num">{{ d.getDate() }}</span>
              <span v-if="d.getDate() === 1 || idx === 0" class="wd-day__month">{{ formatGridMonth(d) }}</span>
            </div>
          </div>
          <div class="wd-cell wd-cell--total wd-cell--head">Итого</div>
        </div>
        <!-- Строки сотрудников -->
        <div
          v-for="row in gridRows"
          :key="row.user_id"
          class="wd-row"
        >
          <div class="wd-cell wd-cell--user">
            <UiAvatar :name="row.full_name || row.email" size="sm" />
            <div class="wd-cell--user__meta">
              <div class="wd-cell--user__name">
                {{ row.full_name || row.email }}
                <span v-if="row.has_active" class="wd-user-dot" title="Сейчас работает"></span>
              </div>
              <div class="wd-cell--user__role">{{ row.role_name || '—' }}</div>
            </div>
          </div>
          <div class="wd-axis wd-axis--track">
            <div
              v-for="(d, idx) in gridDays"
              :key="`gc-${row.user_id}-${idx}`"
              class="wd-day wd-day--cell"
              :class="[
                { 'is-weekend': isWeekend(d), 'is-today': isGridToday(d) },
                gridHeatClass(row.days[isoOf(d)] || 0),
              ]"
              :title="gridCellTitle(row, d)"
            >
              <span v-if="(row.days[isoOf(d)] || 0) > 0" class="wd-day__hours">
                {{ gridShortHours(row.days[isoOf(d)]) }}
              </span>
            </div>
          </div>
          <div class="wd-cell wd-cell--total">
            <strong>{{ formatHours(row.total_seconds) }}</strong>
          </div>
        </div>
      </div>
    </div>
   </div>
  </div>
</template>

<script>
import { computed, onMounted, ref, watch } from 'vue'
import { api } from '../services/api'
import { UiAvatar, UiButton } from '../components/ui'
import { canEditSection } from '../utils/permissions'
import { useToast } from '../composables/useToast'
import { parseServerDate, formatMsk } from '../composables/useServerClock'

const DAY_MS = 24 * 60 * 60 * 1000

function toISO(date) {
  return new Date(date).toISOString().slice(0, 10)
}

// Серверные timestamps приходят naive (без TZ-метки) — сервер МСК пишет
// datetime.now(). parseServerDate трактует это как +03:00. Форматируем
// время сессий принудительно в Europe/Moscow, чтобы все юзеры видели
// одинаковое серверное время независимо от своего браузера.
const parseBackendDate = (value) => parseServerDate(value)

function formatHours(seconds) {
  const s = Math.max(0, Math.floor(Number(seconds) || 0))
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  return `${h} ч ${String(m).padStart(2, '0')} мин`
}

function formatTime(ts) {
  const d = parseBackendDate(ts)
  if (!d) return '—'
  return formatMsk(d)
}

const REASON_LABELS = {
  manual: 'Вручную',
  idle: 'Авто (бездействие)',
  admin: 'Админ-правка',
}

export default {
  name: 'Workday',
  components: { UiAvatar, UiButton },
  setup() {
    const users = ref([])
    const selectedId = ref('')
    const stats = ref(null)
    const loadingList = ref(false)
    const loadingStats = ref(false)
    const groupby = ref('day')
    const toast = useToast()

    // Режим отображения: 'byUser' (sidebar+детали) | 'grid' (таблица).
    const viewMode = ref('byUser')
    const gridRows = ref([])
    const loadingGrid = ref(false)

    const canAdminEdit = computed(() => canEditSection('workday_admin'))

    const today = new Date()
    const weekAgo = new Date(today.getTime() - 6 * DAY_MS)
    const dateFrom = ref(toISO(weekAgo))
    const dateTo = ref(toISO(today))

    const selectedUser = computed(() =>
      users.value.find((u) => u.user_id === selectedId.value) || null
    )

    const loadUsers = async () => {
      loadingList.value = true
      try {
        const data = await api.workday.list({ from: dateFrom.value, to: dateTo.value })
        users.value = Array.isArray(data) ? data : []
        if (!selectedId.value && users.value.length) {
          selectedId.value = users.value[0].user_id
        }
      } catch (e) {
        console.error('Workday list error:', e)
        users.value = []
      } finally {
        loadingList.value = false
      }
    }

    const loadStats = async () => {
      if (!selectedId.value) {
        stats.value = null
        return
      }
      loadingStats.value = true
      try {
        stats.value = await api.workday.stats({
          user_id: selectedId.value,
          from: dateFrom.value,
          to: dateTo.value,
          groupby: groupby.value,
        })
      } catch (e) {
        console.error('Workday stats error:', e)
        stats.value = null
      } finally {
        loadingStats.value = false
      }
    }

    const loadGrid = async () => {
      loadingGrid.value = true
      try {
        const data = await api.workday.grid({ from: dateFrom.value, to: dateTo.value })
        gridRows.value = Array.isArray(data) ? data : []
      } catch (e) {
        console.error('Workday grid error:', e)
        gridRows.value = []
      } finally {
        loadingGrid.value = false
      }
    }

    const reload = async () => {
      if (viewMode.value === 'grid') {
        await Promise.all([loadGrid(), loadUsers()])
      } else {
        await loadUsers()
        await loadStats()
      }
    }

    const switchToGrid = () => {
      viewMode.value = 'grid'
      if (!gridRows.value.length) loadGrid()
    }

    // --- Табличный вид: дни периода + хелперы ---
    const isoOf = (d) => {
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, '0')
      const dd = String(d.getDate()).padStart(2, '0')
      return `${y}-${m}-${dd}`
    }
    const gridDays = computed(() => {
      const from = new Date(dateFrom.value)
      const to = new Date(dateTo.value)
      if (!Number.isFinite(from.getTime()) || !Number.isFinite(to.getTime()) || from > to) return []
      const out = []
      const cur = new Date(from); cur.setHours(0, 0, 0, 0)
      const end = new Date(to); end.setHours(0, 0, 0, 0)
      while (cur <= end) {
        out.push(new Date(cur))
        cur.setDate(cur.getDate() + 1)
      }
      return out
    })
    const gridDayWidth = computed(() => {
      const n = gridDays.value.length
      if (n <= 14) return 46
      if (n <= 31) return 34
      if (n <= 62) return 26
      return 20
    })
    const isWeekend = (d) => [0, 6].includes(d.getDay())
    const isGridToday = (d) => isoOf(d) === isoOf(new Date())
    const formatGridMonth = (d) => d.toLocaleDateString('ru-RU', { month: 'short' })
    const formatGridHover = (d) => d.toLocaleDateString('ru-RU', { weekday: 'short', day: '2-digit', month: 'short' })
    // Часы компактно: «8», «7.5».
    const gridShortHours = (sec) => {
      const h = (Number(sec) || 0) / 3600
      return Number.isInteger(h) ? String(h) : h.toFixed(1)
    }
    // Тепловая градация по отработанному за день.
    const gridHeatClass = (sec) => {
      const h = (Number(sec) || 0) / 3600
      if (h <= 0) return ''
      if (h < 4) return 'is-heat-low'
      if (h < 7) return 'is-heat-mid'
      return 'is-heat-high'
    }
    const gridCellTitle = (row, d) => {
      const sec = row.days[isoOf(d)] || 0
      const base = `${row.full_name || row.email} · ${formatGridHover(d)}`
      return sec > 0 ? `${base}: ${formatHours(sec)}` : `${base}: нет сессий`
    }

    const select = (userId) => {
      selectedId.value = userId
      loadStats()
    }

    const pluralSessions = (n) => {
      const v = Math.abs(n) % 100
      const v10 = v % 10
      if (v > 10 && v < 20) return 'сессий'
      if (v10 > 1 && v10 < 5) return 'сессии'
      if (v10 === 1) return 'сессия'
      return 'сессий'
    }

    const reasonLabel = (r) => REASON_LABELS[r] || (r ? r : '—')
    const reasonClass = (r) => {
      if (r === 'idle') return 'is-idle'
      if (r === 'admin') return 'is-admin'
      if (r === 'manual') return 'is-manual'
      return ''
    }

    // Анормалия: idle-close или очень короткая сессия (<2 мин).
    const isAnomaly = (s) =>
      s.ended_reason === 'idle' || (s.duration_seconds < 120 && !s.is_active)
    const anomalyHint = (s) => {
      if (s.ended_reason === 'idle')
        return 'Закрыто автоматически из-за бездействия (ended_at = время последней активности).'
      if (s.duration_seconds < 120 && !s.is_active)
        return 'Очень короткая сессия (<2 мин).'
      return ''
    }

    // === Timeline (groupby=day) ===
    // Преобразуем started_at / ended_at в проценты от суток в локальной TZ
    // того дня, к которому относится бакет (bucket.key = 'YYYY-MM-DD').
    function dayBounds(bucketKey) {
      // bucketKey приходит из server-side date(started_at) (UTC по факту,
      // но мы трактуем как локальный календарный день — для УЖЕ закрытых
      // сессий разница ≤24ч). Для таймлайна берём «местный» день: 00:00
      // и 24:00 локального времени той даты.
      const [y, m, d] = bucketKey.split('-').map(Number)
      const dayStart = new Date(y, (m || 1) - 1, d || 1, 0, 0, 0, 0)
      const dayEnd = new Date(dayStart.getTime() + 24 * 60 * 60 * 1000)
      return { dayStart, dayEnd }
    }

    function clampPct(value, min = 0, max = 100) {
      return Math.min(max, Math.max(min, value))
    }

    function timelineBarStyle(session, bucketKey) {
      const { dayStart, dayEnd } = dayBounds(bucketKey)
      const startsAt = parseBackendDate(session.started_at)
      const endsAt = session.ended_at
        ? parseBackendDate(session.ended_at)
        : (parseBackendDate(session.last_activity_at) || new Date())
      if (!startsAt || !endsAt) return { display: 'none' }
      const total = dayEnd.getTime() - dayStart.getTime()
      const leftPct = clampPct(((startsAt.getTime() - dayStart.getTime()) / total) * 100)
      const widthPct = clampPct(((endsAt.getTime() - startsAt.getTime()) / total) * 100, 0.5)
      return {
        left: leftPct.toFixed(2) + '%',
        width: widthPct.toFixed(2) + '%',
      }
    }

    function timelineBarTitle(s) {
      const a = formatTime(s.started_at)
      const b = s.ended_at ? formatTime(s.ended_at) : 'сейчас'
      const dur = formatHours(s.duration_seconds)
      const reason = s.ended_reason ? ` · ${REASON_LABELS[s.ended_reason] || s.ended_reason}` : ''
      return `${a}–${b} (${dur})${reason}`
    }

    // === Inline session edit (workday_admin) ===
    const editOpen = ref(false)
    const editSaving = ref(false)
    const editError = ref('')
    const editingId = ref('')
    const editForm = ref({
      started_at: '', ended_at: '',
      ended_reason: 'manual',
      note_start: '', note_end: '',
    })

    // datetime-local input хочет локальное "YYYY-MM-DDTHH:mm".
    function toLocalInput(value) {
      const d = parseBackendDate(value)
      if (!d) return ''
      const pad = (n) => String(n).padStart(2, '0')
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
    }
    function localInputToISO(value) {
      if (!value) return null
      const d = new Date(value)  // браузер парсит как local
      return Number.isFinite(d.getTime()) ? d.toISOString() : null
    }

    const openEdit = (session) => {
      if (!canAdminEdit.value) return
      editingId.value = session.id
      editForm.value = {
        started_at: toLocalInput(session.started_at),
        ended_at: session.ended_at ? toLocalInput(session.ended_at) : '',
        ended_reason: session.ended_reason || 'manual',
        note_start: session.note_start || '',
        note_end: session.note_end || '',
      }
      editError.value = ''
      editOpen.value = true
    }
    const closeEdit = () => {
      if (editSaving.value) return
      editOpen.value = false
      editingId.value = ''
      editError.value = ''
    }
    const saveEdit = async () => {
      if (!editingId.value || editSaving.value) return
      const payload = {}
      const startISO = localInputToISO(editForm.value.started_at)
      if (!startISO) {
        editError.value = 'Начало обязательно'
        return
      }
      payload.started_at = startISO
      payload.ended_at = editForm.value.ended_at
        ? localInputToISO(editForm.value.ended_at)
        : null  // null = снова активная
      payload.ended_reason = payload.ended_at ? editForm.value.ended_reason : null
      payload.note_start = editForm.value.note_start || null
      payload.note_end = editForm.value.note_end || null

      editSaving.value = true
      editError.value = ''
      try {
        await api.workday.patchSession(editingId.value, payload)
        await loadStats()
        await loadUsers()  // тоталы могут поменяться
        if (typeof toast.add === 'function') toast.add('Сессия обновлена', 'success')
        editOpen.value = false
        editingId.value = ''
      } catch (e) {
        editError.value = e?.response?.data?.detail || 'Не удалось сохранить'
      } finally {
        editSaving.value = false
      }
    }

    onMounted(reload)
    watch([dateFrom, dateTo], () => reload())

    return {
      users,
      selectedId,
      selectedUser,
      stats,
      loadingList,
      loadingStats,
      groupby,
      dateFrom,
      dateTo,
      select,
      reload,
      formatHours,
      formatTime,
      pluralSessions,
      // view switch + grid
      viewMode,
      switchToGrid,
      gridRows,
      loadingGrid,
      gridDays,
      gridDayWidth,
      isoOf,
      isWeekend,
      isGridToday,
      formatGridMonth,
      formatGridHover,
      gridShortHours,
      gridHeatClass,
      gridCellTitle,
      reasonLabel,
      reasonClass,
      isAnomaly,
      anomalyHint,
      // timeline
      timelineBarStyle,
      timelineBarTitle,
      // edit
      canAdminEdit,
      editOpen,
      editForm,
      editSaving,
      editError,
      openEdit,
      closeEdit,
      saveEdit,
    }
  },
}
</script>

<style scoped>
/* Внешний контейнер — прозрачный padding (так же, как у Tasks).
   Скруглённое «полотно» лежит внутри (.workday-shell), чтобы sticky-
   шапка и боковая колонка обрезались по углам. */
.workday-view {
  height: 100%;
  padding: 12px;
  box-sizing: border-box;
  overflow: hidden;
}
.workday-shell {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(216, 224, 240, 0.92);
  border-radius: 24px;
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
  overflow: hidden;
}

/* === Тулбар (переключатель вида + период) === */
.workday-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  flex-wrap: wrap;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border, #e2e8f0);
  background: var(--color-surface-2, #f8fafc);
  flex-shrink: 0;
}
.wd-switch {
  display: inline-flex;
  background: var(--color-surface-3, #eef2f7);
  border-radius: 10px;
  padding: 3px;
  gap: 2px;
}
.wd-switch__btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: none;
  background: transparent;
  border-radius: 8px;
  font-size: 0.84rem;
  font-weight: 600;
  font-family: inherit;
  color: var(--color-text-muted, #64748b);
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}
.wd-switch__btn:hover { color: var(--color-text, #0f172a); }
.wd-switch__btn.is-active {
  background: var(--color-surface, #fff);
  color: var(--color-primary, #4338ca);
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.workday-toolbar__period {
  display: inline-flex;
  gap: 8px;
}
.workday-toolbar__period label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.78rem;
  color: var(--color-text-muted, #64748b);
}
.workday-toolbar__period input {
  padding: 5px 8px;
  font-size: 0.82rem;
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 6px;
  background: var(--color-surface, #fff);
  color: var(--color-text, #0f172a);
}

/* Вид «по сотруднику» — grid sidebar + main */
.workday-byuser {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 320px 1fr;
}

/* === Sidebar === */
.workday-sidebar {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-right: 1px solid var(--color-border, #e2e8f0);
  background: var(--color-surface-2, #f8fafc);
}
.workday-sidebar__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 14px 16px 6px;
}
.workday-sidebar__head h3 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
}
.workday-sidebar__count {
  color: var(--color-text-muted, #64748b);
  font-size: 0.85rem;
  font-weight: 600;
}
.workday-sidebar__filters {
  display: flex;
  gap: 6px;
  padding: 0 16px 12px;
  border-bottom: 1px solid var(--color-border, #e2e8f0);
}
.workday-sidebar__filters label {
  flex: 1;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.78rem;
  color: var(--color-text-muted, #64748b);
}
.workday-sidebar__filters input {
  flex: 1;
  padding: 4px 6px;
  font-size: 0.82rem;
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 6px;
  background: var(--color-surface, #fff);
}
.workday-sidebar__list {
  flex: 1;
  overflow-y: auto;
  padding: 6px;
}
.workday-sidebar__loading,
.workday-sidebar__empty {
  padding: 24px 12px;
  text-align: center;
  font-size: 0.85rem;
  color: var(--color-text-muted, #64748b);
}

.workday-user-row {
  display: grid;
  grid-template-columns: 32px 1fr auto;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 10px;
  cursor: pointer;
  margin-bottom: 2px;
  transition: background 0.12s;
}
.workday-user-row:hover {
  background: var(--color-surface-3, rgba(15,23,42,0.04));
}
.workday-user-row.is-selected {
  background: var(--color-primary-soft, rgba(99,102,241,0.12));
}
.workday-user-row__name {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.86rem;
  font-weight: 600;
  color: var(--color-text, #0f172a);
}
.workday-user-row__dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--color-success, #16a34a);
  animation: wd-pulse 1.6s ease-out infinite;
}
@keyframes wd-pulse {
  0%   { box-shadow: 0 0 0 0 rgba(34,197,94,0.55); }
  70%  { box-shadow: 0 0 0 6px rgba(34,197,94,0); }
  100% { box-shadow: 0 0 0 0 rgba(34,197,94,0); }
}
.workday-user-row__role {
  font-size: 0.72rem;
  color: var(--color-text-muted, #64748b);
}
.workday-user-row__total {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.workday-user-row__total strong {
  font-size: 0.84rem;
}
.workday-user-row__total small {
  font-size: 0.68rem;
  color: var(--color-text-muted, #64748b);
}

/* === Main === */
.workday-main {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow-y: auto;
  padding: 18px 24px 28px;
}
.workday-main__head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border, #e2e8f0);
}
.workday-main__title h2 {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 700;
}
.workday-main__title small {
  color: var(--color-text-muted, #64748b);
  font-size: 0.82rem;
}
.workday-main__totals {
  display: flex;
  align-items: center;
  gap: 16px;
}
.workday-kpi {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  font-variant-numeric: tabular-nums;
}
.workday-kpi__label {
  font-size: 0.72rem;
  color: var(--color-text-muted, #64748b);
}
.workday-kpi__value {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--color-text, #0f172a);
}
.workday-groupby {
  padding: 6px 10px;
  font-size: 0.86rem;
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 8px;
  background: var(--color-surface, #fff);
}
.workday-main__loading,
.workday-main__empty {
  padding: 40px;
  text-align: center;
  color: var(--color-text-muted, #64748b);
  font-size: 0.92rem;
}

.workday-bucket {
  margin-bottom: 22px;
}
.workday-bucket__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 6px;
}
.workday-bucket__head h4 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
  text-transform: capitalize;
}
.workday-bucket__total {
  font-size: 0.86rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--color-primary, #6366f1);
}
.workday-bucket__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.86rem;
}
.workday-bucket__table thead th {
  text-align: left;
  padding: 8px 10px;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--color-text-muted, #64748b);
  border-bottom: 1px solid var(--color-border, #e2e8f0);
}
.workday-bucket__table tbody td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--color-border, #f1f5f9);
}
.workday-bucket__table tr.is-anomaly {
  background: rgba(234, 179, 8, 0.08);
}

.workday-cell-time { font-variant-numeric: tabular-nums; white-space: nowrap; }
.workday-cell-dur  { font-variant-numeric: tabular-nums; font-weight: 600; }
.workday-cell-note {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--color-text-muted, #64748b);
}

.workday-active-pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--color-success-soft, rgba(34,197,94,0.14));
  color: var(--color-success, #16a34a);
  font-size: 0.72rem;
  font-weight: 600;
}

.workday-reason {
  display: inline-flex;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  background: var(--color-surface-3, #f1f5f9);
  color: var(--color-text-muted, #64748b);
}
.workday-reason.is-manual { background: rgba(99,102,241,0.12); color: var(--color-primary, #6366f1); }
.workday-reason.is-idle   { background: rgba(234,179,8,0.16); color: #ca8a04; }
.workday-reason.is-admin  { background: rgba(244,63,94,0.14); color: #e11d48; }

/* === Absent-today badge === */
.workday-absent-tag {
  display: inline-block;
  margin-top: 2px;
  padding: 1px 6px;
  border-radius: 999px;
  font-size: 0.62rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  background: rgba(244, 63, 94, 0.12);
  color: #e11d48;
}

/* === Timeline (groupby=day) === */
.workday-timeline {
  position: relative;
  margin: 6px 0 14px;
  padding-top: 18px;
  user-select: none;
}
.workday-timeline-grid {
  position: relative;
  height: 14px;
  margin-bottom: 4px;
}
.workday-timeline-grid span {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  font-size: 0.66rem;
  color: var(--color-text-subtle, #94a3b8);
  font-variant-numeric: tabular-nums;
}
.workday-timeline-track {
  position: relative;
  height: 14px;
  border-radius: 7px;
  background: repeating-linear-gradient(
    to right,
    var(--color-surface-3, #f1f5f9) 0,
    var(--color-surface-3, #f1f5f9) calc(100% / 24 - 1px),
    var(--color-border, #e2e8f0) calc(100% / 24 - 1px),
    var(--color-border, #e2e8f0) calc(100% / 24)
  );
  overflow: hidden;
}
.workday-timeline-bar {
  position: absolute;
  top: 0; bottom: 0;
  background: var(--color-success, #16a34a);
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(22, 163, 74, 0.25);
  cursor: default;
  transition: filter 0.12s;
}
.workday-timeline-bar:hover { filter: brightness(1.08); }
.workday-timeline-bar.is-idle {
  background: linear-gradient(135deg, #16a34a 0%, #16a34a 60%, #ca8a04 60%, #ca8a04 100%);
}
.workday-timeline-bar.is-active {
  background: var(--color-primary, #6366f1);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.35);
}

/* === Edit pencil column === */
.workday-cell-actions {
  width: 38px;
  text-align: right;
  padding-right: 4px;
}
.workday-edit-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--color-text-muted, #64748b);
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}
.workday-edit-btn:hover {
  background: var(--color-surface-3, #f1f5f9);
  color: var(--color-primary, #6366f1);
}
.workday-edit-btn i { font-size: 0.78rem; }

/* === Edit modal === */
.wd-edit-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(4px);
  z-index: 10600;
  display: flex; align-items: center; justify-content: center;
  padding: 16px;
}
.wd-edit-card {
  background: var(--color-surface, #fff);
  color: var(--color-text, #0f172a);
  border-radius: 14px;
  padding: 22px 24px;
  width: 100%;
  max-width: 540px;
  box-shadow: 0 24px 48px rgba(15, 23, 42, 0.24);
  border: 1px solid var(--color-border, rgba(0,0,0,0.06));
}
.wd-edit-title {
  margin: 0 0 6px;
  font-size: 1.1rem;
  font-weight: 700;
}
.wd-edit-hint {
  margin: 0 0 14px;
  font-size: 0.84rem;
  color: var(--color-text-muted, #64748b);
}
.wd-edit-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 14px;
  margin-bottom: 12px;
}
.wd-edit-grid-full { grid-column: 1 / -1; }
.wd-edit-grid label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.82rem;
}
.wd-edit-grid label > span {
  font-weight: 600;
  color: var(--color-text, #0f172a);
}
.wd-edit-grid input,
.wd-edit-grid select,
.wd-edit-grid textarea {
  padding: 7px 9px;
  font-size: 0.9rem;
  font-family: inherit;
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 8px;
  background: var(--color-surface-2, #f8fafc);
  outline: none;
}
.wd-edit-grid textarea { resize: vertical; }
.wd-edit-grid small {
  font-size: 0.72rem;
  color: var(--color-text-muted, #64748b);
}
.wd-edit-error {
  margin-bottom: 10px;
  padding: 6px 8px;
  border-radius: 6px;
  background: rgba(244, 63, 94, 0.1);
  color: #e11d48;
  font-size: 0.82rem;
}
.wd-edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.wd-edit-enter-active, .wd-edit-leave-active { transition: opacity 0.18s ease; }
.wd-edit-enter-from, .wd-edit-leave-to { opacity: 0; }

@media (max-width: 1000px) {
  .workday-view {
    grid-template-columns: 1fr;
  }
  .workday-sidebar {
    border-right: 0;
    border-bottom: 1px solid var(--color-border, #e2e8f0);
    max-height: 280px;
  }
}

/* ===== Табличный вид (grid) ===== */
.workday-grid {
  flex: 1;
  min-height: 0;
  overflow: auto;
}
.workday-grid__loading,
.workday-grid__empty {
  padding: 40px;
  text-align: center;
  color: var(--color-text-muted, #64748b);
}

.wd-table {
  min-width: calc(var(--col-user) + var(--cols-days) * var(--col-day-min) + var(--col-total));
  display: flex;
  flex-direction: column;
}
.wd-row {
  display: grid;
  grid-template-columns: var(--col-user) 1fr var(--col-total);
  align-items: stretch;
  border-bottom: 1px solid var(--color-border-subtle, rgba(0,0,0,0.05));
  min-height: 48px;
}
.wd-row:hover:not(.wd-row--head) { background: rgba(99,102,241,0.04); }
.wd-row--head {
  position: sticky;
  top: 0;
  background: var(--color-surface-2, #f8fafc);
  z-index: 3;
  border-bottom: 1px solid var(--color-border, #e2e8f0);
  min-height: 38px;
}

.wd-cell--user {
  position: sticky;
  left: 0;
  background-color: var(--color-surface, #fff);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  border-right: 1px solid var(--color-border-subtle, rgba(0,0,0,0.05));
  z-index: 2;
}
.wd-row:hover:not(.wd-row--head) .wd-cell--user { background-color: rgba(99,102,241,0.04); }
.wd-row--head .wd-cell--user { background-color: var(--color-surface-2, #f8fafc); z-index: 4; }
.wd-cell--user__meta { min-width: 0; display: flex; flex-direction: column; gap: 1px; line-height: 1.2; }
.wd-cell--user__name {
  display: flex; align-items: center; gap: 6px;
  font-size: 0.86rem; font-weight: 600; color: var(--color-text, #0f172a);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.wd-cell--user__role { font-size: 0.7rem; color: var(--color-text-muted, #64748b); }
.wd-cell--head { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px; color: var(--color-text-muted, #64748b); font-weight: 700; }
.wd-user-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--color-success, #16a34a);
  animation: wd-pulse 1.6s ease-out infinite;
}

.wd-cell--total {
  position: sticky;
  right: 0;
  background-color: var(--color-surface, #fff);
  display: flex;
  align-items: center;
  justify-content: center;
  border-left: 1px solid var(--color-border-subtle, rgba(0,0,0,0.05));
  z-index: 2;
  font-variant-numeric: tabular-nums;
}
.wd-row:hover:not(.wd-row--head) .wd-cell--total { background-color: rgba(99,102,241,0.04); }
.wd-row--head .wd-cell--total { background-color: var(--color-surface-2, #f8fafc); z-index: 4; }
.wd-cell--total strong { font-size: 0.8rem; color: var(--color-text, #0f172a); }

.wd-axis {
  position: relative;
  display: flex;
  width: calc(var(--cols-days) * var(--col-day-min));
}
.wd-day {
  width: var(--col-day-min);
  border-right: 1px solid var(--color-border-subtle, rgba(0,0,0,0.05));
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: 0.66rem;
  color: var(--color-text-muted, #64748b);
  padding: 4px 0;
}
.wd-day.is-weekend { background: rgba(0,0,0,0.025); }
.wd-day.is-today {
  box-shadow: inset 0 0 0 1px rgba(99,102,241,0.35);
}
.wd-day__num { font-weight: 600; }
.wd-day__month {
  font-size: 0.6rem;
  color: var(--color-text-subtle, #94a3b8);
  text-transform: capitalize;
  margin-top: 2px;
}
.wd-day--cell { font-size: 0.72rem; font-weight: 700; }
.wd-day__hours { font-variant-numeric: tabular-nums; }

/* Тепловая заливка ячейки по отработанным часам */
.wd-day--cell.is-heat-low  { background: rgba(34,197,94,0.14); color: #15803d; }
.wd-day--cell.is-heat-mid  { background: rgba(34,197,94,0.34); color: #14532d; }
.wd-day--cell.is-heat-high { background: rgba(22,163,74,0.62); color: #fff; }
.wd-day--cell.is-heat-low.is-weekend  { background: rgba(34,197,94,0.16); }
.wd-day--cell.is-heat-mid.is-weekend  { background: rgba(34,197,94,0.36); }
</style>
