<template>
  <div class="abs">
   <div class="abs-shell">
    <!-- Шапка: фильтры -->
    <header class="abs-toolbar">
      <div class="abs-toolbar__title">
        <h2>Отсутствия</h2>
        <small>Отпуска, больничные и командировки сотрудников.</small>
      </div>

      <div class="abs-toolbar__filters">
        <div class="abs-switch">
          <button
            type="button"
            class="abs-switch__btn"
            :class="{ 'is-active': viewMode === 'table' }"
            @click="viewMode = 'table'"
          >
            <i class="fas fa-table-cells"></i> Таблица
          </button>
          <button
            type="button"
            class="abs-switch__btn"
            :class="{ 'is-active': viewMode === 'byUser' }"
            @click="viewMode = 'byUser'"
          >
            <i class="fas fa-user"></i> По сотруднику
          </button>
        </div>
        <label class="abs-period">
          <span>период с</span>
          <input type="date" v-model="dateFrom" @change="reload" />
        </label>
        <label class="abs-period">
          <span>по</span>
          <input type="date" v-model="dateTo" @change="reload" />
        </label>
        <div class="abs-period abs-period--shifts">
          <button type="button" class="abs-shift" title="На месяц назад" @click="shiftMonth(-1)">
            <i class="fas fa-chevron-left"></i>
          </button>
          <button type="button" class="abs-shift" @click="setRangeCurrentMonth">Сейчас</button>
          <button type="button" class="abs-shift" title="На месяц вперёд" @click="shiftMonth(1)">
            <i class="fas fa-chevron-right"></i>
          </button>
        </div>

        <select v-model="typeFilter" class="abs-select" @change="">
          <option value="">Все типы</option>
          <option v-for="t in TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>

        <input
          v-model="search"
          type="search"
          class="abs-search"
          placeholder="Поиск по сотруднику…"
        />

        <UiButton
          variant="primary"
          size="sm"
          icon-left="fas fa-plus"
          @click="openCreate()"
        >Добавить</UiButton>
      </div>

      <div class="abs-toolbar__legend">
        <span v-for="t in TYPES" :key="`l-${t.value}`" class="abs-legend-chip" :class="`is-${t.value}`">
          <span class="abs-legend-dot"></span>{{ t.label }}
        </span>
      </div>
    </header>

    <!-- Загрузка -->
    <div v-if="loading" class="abs-loading">Загрузка…</div>

    <!-- ВИД 1: Таблица -->
    <div v-else-if="viewMode === 'table'" class="abs-table-wrap">
      <div
        class="abs-table"
        :style="{ '--col-user': '240px', '--col-total': '70px', '--cols-days': days.length, '--col-day-min': dayCellMinWidth + 'px' }"
      >
        <!-- ШАПКА -->
        <div class="abs-row abs-row--head">
          <div class="abs-cell abs-cell--user abs-cell--head">Сотрудник</div>
          <div class="abs-axis abs-axis--head">
            <div
              v-for="(d, idx) in days"
              :key="`h-${idx}`"
              class="abs-day"
              :class="{
                'is-weekend': isWeekend(d),
                'is-today': isToday(d),
                'is-first': d.getDate() === 1 || idx === 0,
                'is-overlap': (peopleOff[ymd(d)] || 0) >= 2,
              }"
              :title="dayHeaderTitle(d)"
            >
              <span class="abs-day__num">{{ d.getDate() }}</span>
              <span v-if="d.getDate() === 1 || idx === 0" class="abs-day__month">{{ formatMonth(d) }}</span>
              <!-- Бейдж показываем только при пересечении ≥2 человек. -->
              <span v-if="(peopleOff[ymd(d)] || 0) >= 2" class="abs-day__count" :title="`Пересечение: ${peopleOff[ymd(d)]} сотрудников отсутствуют`">{{ peopleOff[ymd(d)] }}</span>
            </div>
          </div>
          <div class="abs-cell abs-cell--total abs-cell--head" title="Сумма дней отсутствий за период">Дн.</div>
        </div>

        <!-- СТРОКИ ПО СОТРУДНИКАМ -->
        <div
          v-for="row in rowsFiltered"
          :key="row.user_id"
          class="abs-row"
          :class="{ 'is-me': row.user_id === auth.user?.id }"
        >
          <div class="abs-cell abs-cell--user">
            <UiAvatar :name="row.full_name || row.email" size="sm" />
            <div class="abs-cell--user__meta">
              <div class="abs-cell--user__name">
                {{ row.full_name || row.email }}
                <span
                  v-if="row.activeAbsence"
                  class="abs-dot"
                  :class="`is-${row.activeAbsence.type}`"
                  :title="`${absenceLabel(row.activeAbsence.type)} до ${formatDate(row.activeAbsence.date_to)}`"
                ></span>
              </div>
              <div class="abs-cell--user__role">{{ row.role_name || '—' }}</div>
            </div>
          </div>

          <div class="abs-axis abs-axis--track">
            <!-- фон по дням -->
            <div
              v-for="(d, idx) in days"
              :key="`bg-${row.user_id}-${idx}`"
              class="abs-day abs-day--bg"
              :class="{ 'is-weekend': isWeekend(d), 'is-today': isToday(d) }"
              @click="onCellClick(row, d, $event)"
            ></div>
            <!-- полоски отсутствий -->
            <div
              v-for="a in row.items"
              :key="a.id"
              class="abs-bar"
              :class="`is-${a.type}`"
              :style="barStyle(a)"
              :title="`${absenceLabel(a.type)} · ${formatDate(a.date_from)} — ${formatDate(a.date_to)}${a.comment ? ' · ' + a.comment : ''}`"
              @click.stop="onBarClick(a)"
            >
              <span class="abs-bar__label">{{ absenceLabel(a.type) }}</span>
            </div>
          </div>

          <div class="abs-cell abs-cell--total">
            <strong>{{ row.totalDays }}</strong>
          </div>
        </div>

        <div v-if="!rowsFiltered.length" class="abs-empty">
          Никто не подходит под фильтр.
        </div>
      </div>
    </div>

    <!-- ВИД 2: По сотруднику (sidebar + детали) -->
    <div v-else class="abs-byuser">
      <aside class="abs-bu-sidebar">
        <div class="abs-bu-sidebar__head">
          <h3>Сотрудники</h3>
          <span class="abs-bu-sidebar__count">{{ rowsFiltered.length }}</span>
        </div>
        <div class="abs-bu-sidebar__list">
          <div
            v-for="row in rowsFiltered"
            :key="row.user_id"
            class="abs-bu-user"
            :class="{ 'is-selected': selectedId === row.user_id }"
            @click="selectedId = row.user_id"
          >
            <UiAvatar :name="row.full_name || row.email" size="sm" />
            <div class="abs-bu-user__meta">
              <div class="abs-bu-user__name">
                {{ row.full_name || row.email }}
                <span
                  v-if="row.activeAbsence"
                  class="abs-dot"
                  :class="`is-${row.activeAbsence.type}`"
                ></span>
              </div>
              <div class="abs-bu-user__role">{{ row.role_name || '—' }}</div>
            </div>
            <div class="abs-bu-user__total">
              <strong>{{ row.totalDays }}</strong>
              <small>{{ pluralDays(row.totalDays) }}</small>
            </div>
          </div>
          <div v-if="!rowsFiltered.length" class="abs-bu-sidebar__empty">
            Никого не видно
          </div>
        </div>
      </aside>

      <main class="abs-bu-main">
        <template v-if="selectedRow">
          <header class="abs-bu-head">
            <div class="abs-bu-head__title">
              <h2>{{ selectedRow.full_name || selectedRow.email }}</h2>
              <small>{{ selectedRow.role_name || '—' }}</small>
            </div>
            <div class="abs-bu-head__kpi">
              <div class="abs-kpi">
                <span class="abs-kpi__label">Дней за период</span>
                <strong class="abs-kpi__value">{{ selectedRow.totalDays }}</strong>
              </div>
              <div class="abs-kpi">
                <span class="abs-kpi__label">Записей</span>
                <strong class="abs-kpi__value">{{ selectedRow.items.length }}</strong>
              </div>
              <UiButton
                v-if="canCreateForUser(selectedRow.user_id)"
                variant="primary"
                size="sm"
                icon-left="fas fa-plus"
                @click="openCreate({ user_id: selectedRow.user_id })"
              >Добавить</UiButton>
            </div>
          </header>

          <!-- Бейдж текущего отсутствия -->
          <div
            v-if="selectedRow.activeAbsence"
            class="abs-bu-now"
            :class="`is-${selectedRow.activeAbsence.type}`"
          >
            <i class="fas" :class="absenceIconClass(selectedRow.activeAbsence.type)"></i>
            <span>
              Сейчас: <strong>{{ absenceLabel(selectedRow.activeAbsence.type) }}</strong>
              до {{ formatDate(selectedRow.activeAbsence.date_to) }}
            </span>
          </div>

          <!-- Персональный таймлайн -->
          <div class="abs-bu-timeline">
            <div class="abs-bu-timeline__axis abs-bu-timeline__axis--head">
              <div
                v-for="(d, idx) in days"
                :key="`buh-${idx}`"
                class="abs-day"
                :class="{ 'is-weekend': isWeekend(d), 'is-today': isToday(d) }"
                :title="formatDate(d)"
              >
                <span class="abs-day__num">{{ d.getDate() }}</span>
                <span v-if="d.getDate() === 1 || idx === 0" class="abs-day__month">{{ formatMonth(d) }}</span>
              </div>
            </div>
            <div class="abs-bu-timeline__axis abs-bu-timeline__axis--track">
              <div
                v-for="(d, idx) in days"
                :key="`bubg-${idx}`"
                class="abs-day abs-day--bg"
                :class="{ 'is-weekend': isWeekend(d), 'is-today': isToday(d) }"
                @click="onCellClick(selectedRow, d, $event)"
              ></div>
              <div
                v-for="a in selectedRow.items"
                :key="a.id"
                class="abs-bar"
                :class="`is-${a.type}`"
                :style="barStyle(a)"
                :title="`${absenceLabel(a.type)} · ${formatDate(a.date_from)} — ${formatDate(a.date_to)}`"
                @click.stop="onBarClick(a)"
              >
                <span class="abs-bar__label">{{ absenceLabel(a.type) }}</span>
              </div>
            </div>
          </div>

          <!-- Карточки отсутствий -->
          <div class="abs-bu-cards">
            <div
              v-for="a in sortedItems(selectedRow.items)"
              :key="a.id"
              class="abs-card"
              :class="`is-${a.type}`"
            >
              <div class="abs-card__icon">
                <i class="fas" :class="absenceIconClass(a.type)"></i>
              </div>
              <div class="abs-card__body">
                <div class="abs-card__head">
                  <strong>{{ absenceLabel(a.type) }}</strong>
                  <span class="abs-card__dates">
                    {{ formatDate(a.date_from) }} — {{ formatDate(a.date_to) }}
                    <span class="abs-card__duration">· {{ daysBetween(a.date_from, a.date_to) }} {{ pluralDays(daysBetween(a.date_from, a.date_to)) }}</span>
                  </span>
                </div>
                <div v-if="a.comment" class="abs-card__comment">{{ a.comment }}</div>
              </div>
              <div v-if="canEditEntry(a)" class="abs-card__actions">
                <button type="button" class="abs-icon-btn" title="Редактировать" @click="openEdit(a)">
                  <i class="fas fa-pen"></i>
                </button>
                <button type="button" class="abs-icon-btn is-danger" title="Удалить" @click="onDeleteEntry(a)">
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            </div>
            <div v-if="!selectedRow.items.length" class="abs-bu-empty">
              За период записей нет.
            </div>
          </div>
        </template>
        <div v-else class="abs-bu-placeholder">
          <i class="fas fa-user-clock"></i>
          <span>Выберите сотрудника слева.</span>
        </div>
      </main>
    </div>

   </div>

    <!-- Модалка create/edit (вне shell, чтобы не подрезалась overflow:hidden) -->
    <UiModal v-model="modalOpen" :title="editingId ? 'Изменить запись' : 'Добавить отсутствие'">
      <div class="abs-form">
        <div v-if="canPickUser" class="abs-form__field">
          <label>Сотрудник</label>
          <select v-model="form.user_id" class="abs-input">
            <option :value="null">— я ({{ auth.user?.full_name || auth.user?.email }}) —</option>
            <option v-for="u in users" :key="u.id" :value="u.id">{{ u.full_name || u.email }}</option>
          </select>
        </div>

        <div class="abs-form__field">
          <label>Тип</label>
          <div class="abs-type-grid">
            <button
              v-for="t in TYPES"
              :key="t.value"
              type="button"
              class="abs-type-btn"
              :class="[`is-${t.value}`, { 'is-active': form.type === t.value }]"
              @click="form.type = t.value"
            >
              <i class="fas" :class="absenceIconClass(t.value)"></i>
              <span>{{ t.label }}</span>
            </button>
          </div>
        </div>

        <div class="abs-form__row">
          <div class="abs-form__field">
            <label>С</label>
            <input type="date" v-model="form.date_from" class="abs-input" />
          </div>
          <div class="abs-form__field">
            <label>По</label>
            <input type="date" v-model="form.date_to" class="abs-input" />
          </div>
        </div>

        <div class="abs-form__field">
          <label>Комментарий <span class="muted">(необязательно)</span></label>
          <textarea
            v-model="form.comment"
            rows="3"
            class="abs-input"
            maxlength="2000"
            placeholder="Например: ежегодный отпуск, командировка в Москву…"
          ></textarea>
        </div>
      </div>
      <template #footer>
        <UiButton v-if="editingId && canDeleteForm" variant="ghost" icon-left="fas fa-trash" @click="onDeleteFromForm">
          Удалить
        </UiButton>
        <span style="flex:1"></span>
        <UiButton variant="ghost" @click="modalOpen = false">Отмена</UiButton>
        <UiButton variant="primary" icon-left="fas fa-check" :loading="saving" @click="save">
          {{ editingId ? 'Сохранить' : 'Добавить' }}
        </UiButton>
      </template>
    </UiModal>
  </div>
</template>

<script>
import { computed, onMounted, ref, watch } from 'vue'
import { api } from '../services/api'
import { useToast } from '../composables/useToast'
import { useAuthStore } from '../stores/auth'
import { UiAvatar, UiButton, UiModal } from '../components/ui'

const TYPES = [
  { value: 'vacation',      label: 'Отпуск' },
  { value: 'sick_leave',    label: 'Больничный' },
  { value: 'business_trip', label: 'Командировка' },
  { value: 'other',         label: 'Другое' },
]
const ABSENCE_LABEL = Object.fromEntries(TYPES.map(t => [t.value, t.label]))
const ABSENCE_ICON = {
  vacation: 'fa-umbrella-beach',
  sick_leave: 'fa-briefcase-medical',
  business_trip: 'fa-plane-departure',
  other: 'fa-clock',
}

function ymd(d) {
  if (!d) return null
  const dd = d instanceof Date ? d : new Date(d)
  if (!Number.isFinite(dd.getTime())) return null
  const y = dd.getFullYear()
  const m = String(dd.getMonth() + 1).padStart(2, '0')
  const day = String(dd.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}
function parseDate(s) {
  if (!s) return null
  const d = new Date(s)
  return Number.isFinite(d.getTime()) ? d : null
}
function startOfDay(d) {
  const r = new Date(d)
  r.setHours(0, 0, 0, 0)
  return r
}
function addDays(d, n) {
  const r = new Date(d)
  r.setDate(r.getDate() + n)
  return r
}

export default {
  name: 'Absences',
  components: { UiAvatar, UiButton, UiModal },
  setup() {
    const auth = useAuthStore()
    const { success, error: toastError } = useToast()

    const loading = ref(false)
    const saving = ref(false)
    const users = ref([])
    const items = ref([])

    // Период по умолчанию — текущий месяц.
    const now = new Date()
    const defaultFrom = new Date(now.getFullYear(), now.getMonth(), 1)
    const defaultTo = new Date(now.getFullYear(), now.getMonth() + 1, 0)
    const dateFrom = ref(ymd(defaultFrom))
    const dateTo = ref(ymd(defaultTo))
    const typeFilter = ref('')
    const search = ref('')

    // Режим: 'table' (единая таблица) | 'byUser' (sidebar + детали).
    const viewMode = ref('table')
    const selectedId = ref(null)

    const canSeeOthers = computed(() => {
      const a = auth.permissions?.absences || {}
      const u = auth.permissions?.users || {}
      return Boolean(auth.isSuperuser || a.read_all || a.edit_all || u.read_all || u.edit_all)
    })
    const canPickUser = computed(() => {
      const a = auth.permissions?.absences || {}
      const u = auth.permissions?.users || {}
      return Boolean(auth.isSuperuser || a.edit_all || u.edit_all)
    })

    const formatDate = (iso) => {
      const d = parseDate(iso)
      if (!d) return ''
      return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
    }
    const formatMonth = (d) => d.toLocaleDateString('ru-RU', { month: 'short' })
    const formatHover = (d) => d.toLocaleDateString('ru-RU', { weekday: 'short', day: '2-digit', month: 'short' })

    // Полный title ячейки шапки: дата + сколько людей отсутствует.
    // Сам бейджик в ячейке показывается ТОЛЬКО при пересечении ≥2 человек,
    // чтобы шапка не пестрила «1»-ами для одиночных отпусков.
    const dayHeaderTitle = (d) => {
      const base = formatHover(d)
      const n = peopleOff.value[ymd(d)] || 0
      if (n <= 0) return base
      const word = n === 1 ? 'сотрудник отсутствует' : (n >= 2 && n <= 4 ? 'сотрудника отсутствуют' : 'сотрудников отсутствуют')
      return `${base} · ${n} ${word}`
    }

    const absenceLabel = (t) => ABSENCE_LABEL[t] || ABSENCE_LABEL.other
    const absenceIconClass = (t) => ABSENCE_ICON[t] || ABSENCE_ICON.other

    const isWeekend = (d) => [0, 6].includes(d.getDay())
    const isToday = (d) => ymd(d) === ymd(new Date())

    // Дни внутри выбранного периода.
    const days = computed(() => {
      const from = parseDate(dateFrom.value)
      const to = parseDate(dateTo.value)
      if (!from || !to || from > to) return []
      const out = []
      let cur = startOfDay(from)
      const end = startOfDay(to)
      while (cur <= end) {
        out.push(new Date(cur))
        cur = addDays(cur, 1)
      }
      return out
    })

    // Минимальная ширина ячейки одного дня — больше периодов влезает.
    const dayCellMinWidth = computed(() => {
      const total = days.value.length
      if (total <= 14) return 36
      if (total <= 31) return 26
      if (total <= 62) return 20
      return 16
    })

    const filteredItems = computed(() => {
      if (!typeFilter.value) return items.value
      return items.value.filter((it) => it.type === typeFilter.value)
    })

    const daysBetween = (a, b) => {
      const da = parseDate(a); const db = parseDate(b)
      if (!da || !db) return 0
      return Math.round((startOfDay(db) - startOfDay(da)) / 86_400_000) + 1
    }

    // Склонение слова «день» по числу.
    const pluralDays = (n) => {
      const lastTwo = Math.abs(n) % 100
      const last = n % 10
      if (lastTwo >= 11 && lastTwo <= 14) return 'дней'
      if (last === 1) return 'день'
      if (last >= 2 && last <= 4) return 'дня'
      return 'дней'
    }

    // Сколько дней попадает В ВЫБРАННЫЙ ПЕРИОД (clamp к границам).
    const daysInRange = (a) => {
      const total = days.value.length
      if (!total) return 0
      const start = startOfDay(days.value[0])
      const end = startOfDay(days.value[total - 1])
      const from = startOfDay(parseDate(a.date_from))
      const to = startOfDay(parseDate(a.date_to))
      if (!from || !to) return 0
      const cf = from < start ? start : from
      const ct = to > end ? end : to
      if (cf > ct) return 0
      return Math.round((ct - cf) / 86_400_000) + 1
    }

    // Группировка по сотруднику.
    const itemsByUser = computed(() => {
      const map = new Map()
      for (const it of filteredItems.value) {
        if (!map.has(it.user_id)) map.set(it.user_id, [])
        map.get(it.user_id).push(it)
      }
      return map
    })

    // Сколько человек отсутствуют в каждый день — для бейджика в шапке.
    const peopleOff = computed(() => {
      const counts = {}
      const todayMap = new Set()
      for (const d of days.value) counts[ymd(d)] = 0
      for (const a of filteredItems.value) {
        const from = startOfDay(parseDate(a.date_from))
        const to = startOfDay(parseDate(a.date_to))
        if (!from || !to) continue
        for (const d of days.value) {
          if (d >= from && d <= to) {
            const key = `${a.user_id}|${ymd(d)}`
            if (todayMap.has(key)) continue
            todayMap.add(key)
            counts[ymd(d)] = (counts[ymd(d)] || 0) + 1
          }
        }
      }
      return counts
    })

    // Строки таблицы.
    const rows = computed(() => {
      const todayStr = ymd(new Date())
      return users.value.map((u) => {
        const list = itemsByUser.value.get(u.id) || []
        const totalDays = list.reduce((s, a) => s + daysInRange(a), 0)
        const activeAbsence = list.find((a) =>
          ymd(a.date_from) <= todayStr && todayStr <= ymd(a.date_to)
        ) || null
        return {
          user_id: u.id,
          full_name: u.full_name,
          email: u.email,
          role_name: u.role_name,
          items: list,
          totalDays,
          activeAbsence,
        }
      })
    })

    const rowsFiltered = computed(() => {
      const q = search.value.trim().toLowerCase()
      let list = rows.value
      if (q) {
        list = list.filter((r) => {
          const a = (r.full_name || '').toLowerCase()
          const b = (r.email || '').toLowerCase()
          const c = (r.role_name || '').toLowerCase()
          return a.includes(q) || b.includes(q) || c.includes(q)
        })
      }
      // Сортировка: сначала «отсутствующие сейчас», потом по сумме дней, потом по имени.
      return [...list].sort((a, b) => {
        const aw = a.activeAbsence ? 1 : 0
        const bw = b.activeAbsence ? 1 : 0
        if (aw !== bw) return bw - aw
        if (b.totalDays !== a.totalDays) return b.totalDays - a.totalDays
        return (a.full_name || '').localeCompare(b.full_name || '')
      })
    })

    // Единичный вид: выбранный сотрудник.
    const selectedRow = computed(() =>
      rowsFiltered.value.find((r) => r.user_id === selectedId.value) || null
    )
    // Карточки сортируем по началу (свежие сверху).
    const sortedItems = (list) =>
      [...(list || [])].sort((a, b) =>
        String(b.date_from || '').localeCompare(String(a.date_from || ''))
      )
    const canCreateForUser = (userId) => {
      if (userId === auth.user?.id) {
        const a = auth.permissions?.absences || {}
        return Boolean(auth.isSuperuser || a.edit_assigned || a.edit_all)
      }
      return canPickUser.value
    }

    // Стиль полоски в таймлайне (clamp к выбранному периоду).
    const barStyle = (a) => {
      const total = days.value.length
      if (!total) return { display: 'none' }
      const start = startOfDay(days.value[0])
      const end = startOfDay(days.value[total - 1])
      const from = startOfDay(parseDate(a.date_from))
      const to = startOfDay(parseDate(a.date_to))
      if (!from || !to) return { display: 'none' }
      const cf = from < start ? start : from
      const ct = to > end ? end : to
      if (cf > ct) return { display: 'none' }
      const offsetDays = Math.round((cf - start) / 86_400_000)
      const widthDays = Math.round((ct - cf) / 86_400_000) + 1
      return {
        left: `calc(${offsetDays} * var(--col-day-min))`,
        width: `calc(${widthDays} * var(--col-day-min) - 2px)`,
      }
    }

    const reload = async () => {
      loading.value = true
      try {
        const params = {}
        if (dateFrom.value) params.from = dateFrom.value
        if (dateTo.value) params.to = dateTo.value
        const [list, allItems] = await Promise.all([
          canSeeOthers.value
            ? api.users.list({ limit: 500 }).then(r => r?.items || r || [])
            : Promise.resolve([{
                id: auth.user.id,
                full_name: auth.user.full_name,
                email: auth.user.email,
                role_name: auth.user.role_name,
              }]),
          api.absences.list(params),
        ])
        users.value = list.filter(Boolean)
        items.value = allItems || []
      } catch (e) {
        items.value = []
        toastError('Не удалось загрузить отсутствия')
      } finally {
        loading.value = false
      }
    }

    // Сдвиг периода на месяц вперёд/назад / возврат к текущему.
    const shiftMonth = (delta) => {
      const f = parseDate(dateFrom.value) || new Date()
      const t = parseDate(dateTo.value) || new Date()
      const nf = new Date(f.getFullYear(), f.getMonth() + delta, 1)
      const nt = new Date(t.getFullYear(), t.getMonth() + delta + 1, 0)
      dateFrom.value = ymd(nf)
      dateTo.value = ymd(nt)
    }
    const setRangeCurrentMonth = () => {
      const n = new Date()
      dateFrom.value = ymd(new Date(n.getFullYear(), n.getMonth(), 1))
      dateTo.value = ymd(new Date(n.getFullYear(), n.getMonth() + 1, 0))
    }

    // ---- Модалка create/edit ----
    const modalOpen = ref(false)
    const editingId = ref(null)
    const form = ref({
      user_id: null,
      type: 'vacation',
      date_from: ymd(new Date()),
      date_to: ymd(new Date()),
      comment: '',
    })

    const canEditEntry = (a) => {
      const isOwn = a.user_id === auth.user?.id
      if (isOwn) {
        const p = auth.permissions?.absences || {}
        return Boolean(auth.isSuperuser || p.edit_assigned || p.edit_all)
      }
      return canPickUser.value
    }

    const canDeleteForm = computed(() => {
      if (!editingId.value) return false
      const a = items.value.find((x) => x.id === editingId.value)
      return a ? canEditEntry(a) : false
    })

    const openCreate = (prefill = null) => {
      editingId.value = null
      // По умолчанию — себя; если у строки уже выбран другой юзер, и есть права — подставляем его.
      const myId = auth.user?.id
      const targetId = prefill?.user_id && canPickUser.value
        ? (prefill.user_id !== myId ? prefill.user_id : null)
        : null
      form.value = {
        user_id: canPickUser.value ? targetId : null,
        type: 'vacation',
        date_from: prefill?.date || ymd(new Date()),
        date_to: prefill?.date || ymd(new Date()),
        comment: '',
      }
      modalOpen.value = true
    }

    const openEdit = (a) => {
      if (!canEditEntry(a)) {
        toastError('У вас нет прав на правку этой записи')
        return
      }
      editingId.value = a.id
      form.value = {
        user_id: a.user_id,
        type: a.type,
        date_from: ymd(parseDate(a.date_from)),
        date_to: ymd(parseDate(a.date_to)),
        comment: a.comment || '',
      }
      modalOpen.value = true
    }

    const onBarClick = (a) => openEdit(a)
    const onCellClick = (row, day) => {
      // Создать запись для этого сотрудника на этот день (если можно).
      const isMe = row.user_id === auth.user?.id
      if (!isMe && !canPickUser.value) return
      openCreate({ user_id: row.user_id, date: ymd(day) })
    }

    const save = async () => {
      if (saving.value) return
      if (!form.value.date_from || !form.value.date_to) {
        toastError('Заполните период')
        return
      }
      if (form.value.date_from > form.value.date_to) {
        toastError('Дата окончания должна быть не раньше начала')
        return
      }
      saving.value = true
      try {
        if (editingId.value) {
          await api.absences.patchOne(editingId.value, {
            type: form.value.type,
            date_from: form.value.date_from,
            date_to: form.value.date_to,
            comment: form.value.comment || null,
          })
          success('Запись обновлена')
        } else {
          const payload = {
            type: form.value.type,
            date_from: form.value.date_from,
            date_to: form.value.date_to,
            comment: form.value.comment || null,
          }
          if (canPickUser.value && form.value.user_id) {
            payload.user_id = form.value.user_id
          }
          await api.absences.create(payload)
          success('Запись добавлена')
        }
        modalOpen.value = false
        await reload()
      } catch (e) {
        toastError(e?.response?.data?.detail || 'Не удалось сохранить')
      } finally {
        saving.value = false
      }
    }

    const onDeleteFromForm = async () => {
      if (!editingId.value) return
      if (!confirm('Удалить запись?')) return
      try {
        await api.absences.remove(editingId.value)
        success('Удалено')
        modalOpen.value = false
        await reload()
      } catch (e) {
        toastError(e?.response?.data?.detail || 'Не удалось удалить')
      }
    }

    // Удаление карточки прямо из единичного вида.
    const onDeleteEntry = async (a) => {
      if (!canEditEntry(a)) {
        toastError('У вас нет прав на удаление')
        return
      }
      if (!confirm('Удалить запись?')) return
      try {
        await api.absences.remove(a.id)
        success('Удалено')
        await reload()
      } catch (e) {
        toastError(e?.response?.data?.detail || 'Не удалось удалить')
      }
    }

    // При переключении на «по сотруднику» — авто-выбор первого в списке.
    watch(viewMode, (mode) => {
      if (mode === 'byUser' && !selectedId.value && rowsFiltered.value.length) {
        const me = rowsFiltered.value.find((r) => r.user_id === auth.user?.id)
        selectedId.value = (me || rowsFiltered.value[0]).user_id
      }
    })

    onMounted(reload)
    watch([dateFrom, dateTo], () => reload())

    return {
      TYPES,
      auth, loading, saving,
      users, items,
      dateFrom, dateTo, typeFilter, search,
      days, dayCellMinWidth, peopleOff,
      rows, rowsFiltered,
      ymd, formatDate, formatMonth, formatHover, dayHeaderTitle,
      absenceLabel, absenceIconClass,
      isWeekend, isToday, barStyle,
      pluralDays, daysBetween,
      canPickUser, canDeleteForm, canEditEntry,
      reload, shiftMonth, setRangeCurrentMonth,
      // view switch + единичный вид
      viewMode, selectedId, selectedRow,
      sortedItems, canCreateForUser, onDeleteEntry,
      // modal
      modalOpen, editingId, form,
      openCreate, openEdit, save,
      onBarClick, onCellClick, onDeleteFromForm,
    }
  },
}
</script>

<style scoped>
/* Внешний контейнер прозрачен, скруглённое полотно — внутренний shell,
   чтобы sticky-шапка и колонка сотрудников чисто обрезались по углам. */
.abs {
  height: 100%;
  padding: 12px;
  box-sizing: border-box;
  overflow: hidden;
}
.abs-shell {
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

/* ===== Toolbar ===== */
.abs-toolbar {
  padding: 16px 22px 12px;
  border-bottom: 1px solid var(--color-border, #e2e8f0);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.abs-toolbar__title h2 { margin: 0; font-size: 1.2rem; font-weight: 700; color: var(--color-text, #0f172a); }
.abs-toolbar__title small { display: block; color: var(--color-text-muted, #64748b); margin-top: 2px; }

.abs-toolbar__filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}
.abs-period {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: var(--color-text-muted, #64748b);
}
.abs-period input {
  padding: 6px 8px;
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 6px;
  font-size: 0.85rem;
  background: var(--color-surface, #fff);
  color: var(--color-text, #0f172a);
}
.abs-period--shifts { display: inline-flex; gap: 4px; }
.abs-shift {
  padding: 6px 10px;
  border: 1px solid var(--color-border, #e2e8f0);
  background: var(--color-surface, #fff);
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
  color: var(--color-text-muted, #64748b);
}
.abs-shift:hover { background: var(--color-surface-3, #f1f5f9); color: var(--color-text, #0f172a); }

.abs-select,
.abs-search {
  padding: 6px 10px;
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 6px;
  font-size: 0.85rem;
  background: var(--color-surface, #fff);
  color: var(--color-text, #0f172a);
}
.abs-search { min-width: 220px; }

.abs-toolbar__legend {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
}
.abs-legend-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
  color: var(--color-text-muted, #64748b);
}
.abs-legend-dot { width: 10px; height: 10px; border-radius: 999px; }
.abs-legend-chip.is-vacation .abs-legend-dot { background: #16a34a; }
.abs-legend-chip.is-sick_leave .abs-legend-dot { background: #dc2626; }
.abs-legend-chip.is-business_trip .abs-legend-dot { background: #6366f1; }
.abs-legend-chip.is-other .abs-legend-dot { background: #94a3b8; }

.abs-loading { padding: 32px; text-align: center; color: var(--color-text-muted, #64748b); }

/* ===== Таблица ===== */
.abs-table-wrap {
  flex: 1;
  min-height: 0;
  overflow: auto;
  background: var(--color-surface, #fff);
}

.abs-table {
  /* Чёткая ширина = первая колонка + (минимальная ширина дня × N дней) + колонка итогов */
  min-width: calc(var(--col-user) + var(--cols-days) * var(--col-day-min) + var(--col-total));
  display: flex;
  flex-direction: column;
}

.abs-row {
  display: grid;
  grid-template-columns: var(--col-user) 1fr var(--col-total);
  align-items: stretch;
  border-bottom: 1px solid var(--color-border-subtle, rgba(0,0,0,0.05));
  min-height: 46px;
}
.abs-row:hover:not(.abs-row--head) { background: rgba(99,102,241,0.04); }
.abs-row.is-me { background: rgba(99,102,241,0.06); }
.abs-row.is-me:hover { background: rgba(99,102,241,0.10); }
.abs-row--head {
  position: sticky;
  top: 0;
  background: var(--color-surface-2, #f8fafc);
  z-index: 3;
  border-bottom: 1px solid var(--color-border, #e2e8f0);
  min-height: 36px;
}

/* === Cell: Сотрудник (sticky left) === */
.abs-cell--user {
  position: sticky;
  left: 0;
  background: inherit;
  background-color: var(--color-surface, #fff);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  border-right: 1px solid var(--color-border-subtle, rgba(0,0,0,0.05));
  z-index: 2;
}
.abs-row.is-me .abs-cell--user { background-color: rgba(99,102,241,0.08); }
.abs-row:hover:not(.abs-row--head) .abs-cell--user { background-color: rgba(99,102,241,0.06); }
.abs-row--head .abs-cell--user { background-color: var(--color-surface-2, #f8fafc); z-index: 4; }

.abs-cell--user__meta { min-width: 0; flex: 1; display: flex; flex-direction: column; gap: 1px; line-height: 1.2; }
.abs-cell--user__name {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.86rem;
  font-weight: 600;
  color: var(--color-text, #0f172a);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.abs-cell--user__role { font-size: 0.7rem; color: var(--color-text-muted, #64748b); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.abs-cell--head { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px; color: var(--color-text-muted, #64748b); font-weight: 700; }

/* === Cell: Итого (sticky right) === */
.abs-cell--total {
  position: sticky;
  right: 0;
  background-color: var(--color-surface, #fff);
  text-align: center;
  font-variant-numeric: tabular-nums;
  display: flex;
  align-items: center;
  justify-content: center;
  border-left: 1px solid var(--color-border-subtle, rgba(0,0,0,0.05));
  z-index: 2;
}
.abs-row.is-me .abs-cell--total { background-color: rgba(99,102,241,0.08); }
.abs-row:hover:not(.abs-row--head) .abs-cell--total { background-color: rgba(99,102,241,0.06); }
.abs-row--head .abs-cell--total { background-color: var(--color-surface-2, #f8fafc); z-index: 4; }
.abs-cell--total strong { font-size: 0.92rem; color: var(--color-text, #0f172a); }

/* === Axis: дни === */
.abs-axis {
  position: relative;
  display: flex;
  height: auto;
  min-height: 100%;
  width: calc(var(--cols-days) * var(--col-day-min));
}
.abs-axis--head {
  align-items: stretch;
}
.abs-axis--track {
  min-height: 46px;
}
.abs-day {
  width: var(--col-day-min);
  border-right: 1px solid var(--color-border-subtle, rgba(0,0,0,0.05));
  text-align: center;
  font-size: 0.66rem;
  color: var(--color-text-muted, #64748b);
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4px 0;
}
.abs-day.is-weekend { background: rgba(0,0,0,0.025); }
.abs-day.is-today {
  background: rgba(99,102,241,0.12);
  box-shadow: inset 0 0 0 1px rgba(99,102,241,0.35);
}
.abs-day--bg { padding: 0; cursor: cell; }
.abs-day--bg:hover { background: rgba(99,102,241,0.08); }
.abs-day__num { font-weight: 600; }
.abs-day__month {
  font-size: 0.62rem;
  color: var(--color-text-subtle, #94a3b8);
  text-transform: capitalize;
  margin-top: 2px;
}
.abs-day__count {
  position: absolute;
  bottom: -2px;
  right: -2px;
  background: var(--color-primary, #4338ca);
  color: #fff;
  font-size: 0.6rem;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 999px;
  min-width: 14px;
  text-align: center;
  line-height: 1.3;
}
/* Подсветка «пересечения» (≥2 одновременно отсутствующих) —
   ненавязчивый жёлтый фон, чтобы глаз цеплялся за такие дни. */
.abs-day.is-overlap { background: rgba(234, 179, 8, 0.12); }

/* === Полоски === */
.abs-bar {
  position: absolute;
  top: 7px;
  bottom: 7px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.72rem;
  color: #fff;
  padding: 0 8px;
  display: flex;
  align-items: center;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.15);
  transition: filter 0.1s, transform 0.1s;
  z-index: 1;
}
.abs-bar:hover { filter: brightness(1.08); transform: translateY(-1px); z-index: 2; }
.abs-bar__label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 600;
  letter-spacing: 0.2px;
}
.abs-bar.is-vacation { background: linear-gradient(180deg, #22c55e 0%, #16a34a 100%); }
.abs-bar.is-sick_leave { background: linear-gradient(180deg, #ef4444 0%, #b91c1c 100%); }
.abs-bar.is-business_trip { background: linear-gradient(180deg, #6366f1 0%, #4338ca 100%); }
.abs-bar.is-other { background: linear-gradient(180deg, #94a3b8 0%, #64748b 100%); }

/* Точка-статус в имени */
.abs-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.abs-dot.is-vacation { background: #16a34a; }
.abs-dot.is-sick_leave { background: #dc2626; }
.abs-dot.is-business_trip { background: #6366f1; }
.abs-dot.is-other { background: #94a3b8; }

.abs-empty { padding: 24px; text-align: center; color: var(--color-text-muted, #64748b); }

/* === Form (модалка) === */
.abs-form { display: flex; flex-direction: column; gap: 14px; }
.abs-form__field { display: flex; flex-direction: column; gap: 4px; }
.abs-form__field > label {
  font-size: 0.74rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 700;
  color: var(--color-text-muted, #64748b);
}
.muted { color: var(--color-text-subtle, #94a3b8); font-weight: 400; text-transform: none; letter-spacing: 0; font-size: 0.7rem; }
.abs-form__row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.abs-input {
  padding: 8px 10px;
  border: 1px solid var(--color-border-strong, rgba(0,0,0,0.12));
  border-radius: 8px;
  font-size: 0.95rem;
  background: var(--color-surface-2, #f8fafc);
  font-family: inherit;
  color: var(--color-text, #0f172a);
}
.abs-input:focus {
  outline: none;
  border-color: var(--color-primary, #6366f1);
  box-shadow: 0 0 0 3px var(--color-primary-soft, rgba(99,102,241,0.18));
}

.abs-type-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.abs-type-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--color-surface-2, #f8fafc);
  border: 1px solid var(--color-border, #e2e8f0);
  cursor: pointer;
  font-size: 0.88rem;
  font-family: inherit;
  font-weight: 600;
  color: var(--color-text-muted, #64748b);
  transition: all 0.12s;
}
.abs-type-btn i { font-size: 1rem; }
.abs-type-btn:hover { background: var(--color-surface-3, #f1f5f9); }
.abs-type-btn.is-active.is-vacation { background: rgba(34,197,94,0.14); color: #15803d; border-color: #16a34a; }
.abs-type-btn.is-active.is-sick_leave { background: rgba(220,38,38,0.12); color: #b91c1c; border-color: #dc2626; }
.abs-type-btn.is-active.is-business_trip { background: rgba(99,102,241,0.12); color: #4338ca; border-color: #6366f1; }
.abs-type-btn.is-active.is-other { background: rgba(148,163,184,0.18); color: #475569; border-color: #94a3b8; }

/* ===== Переключатель вида ===== */
.abs-switch {
  display: inline-flex;
  background: var(--color-surface-3, #eef2f7);
  border-radius: 8px;
  padding: 3px;
  gap: 2px;
}
.abs-switch__btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: none;
  background: transparent;
  border-radius: 6px;
  font-size: 0.82rem;
  font-weight: 600;
  font-family: inherit;
  color: var(--color-text-muted, #64748b);
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}
.abs-switch__btn:hover { color: var(--color-text, #0f172a); }
.abs-switch__btn.is-active {
  background: var(--color-surface, #fff);
  color: var(--color-primary, #4338ca);
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* ===== Единичный вид (sidebar + детали) ===== */
.abs-byuser {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 300px 1fr;
}

.abs-bu-sidebar {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-right: 1px solid var(--color-border, #e2e8f0);
  background: var(--color-surface-2, #f8fafc);
}
.abs-bu-sidebar__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 14px 16px 8px;
}
.abs-bu-sidebar__head h3 { margin: 0; font-size: 1rem; font-weight: 700; }
.abs-bu-sidebar__count { color: var(--color-text-muted, #64748b); font-size: 0.85rem; font-weight: 600; }
.abs-bu-sidebar__list { flex: 1; overflow-y: auto; padding: 6px; }
.abs-bu-sidebar__empty { padding: 24px 12px; text-align: center; font-size: 0.85rem; color: var(--color-text-muted, #64748b); }

.abs-bu-user {
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
.abs-bu-user:hover { background: var(--color-surface-3, rgba(15,23,42,0.04)); }
.abs-bu-user.is-selected { background: var(--color-primary-soft, rgba(99,102,241,0.12)); }
.abs-bu-user__meta { min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.abs-bu-user__name {
  display: flex; align-items: center; gap: 6px;
  font-size: 0.85rem; font-weight: 600; color: var(--color-text, #0f172a);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.abs-bu-user__role { font-size: 0.7rem; color: var(--color-text-muted, #64748b); }
.abs-bu-user__total {
  display: flex; flex-direction: column; align-items: flex-end;
  font-variant-numeric: tabular-nums;
}
.abs-bu-user__total strong { font-size: 0.84rem; }
.abs-bu-user__total small { font-size: 0.66rem; color: var(--color-text-muted, #64748b); }

.abs-bu-main {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow-y: auto;
  padding: 18px 22px 26px;
  gap: 14px;
}
.abs-bu-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 14px;
  flex-wrap: wrap;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border, #e2e8f0);
}
.abs-bu-head__title h2 { margin: 0; font-size: 1.2rem; font-weight: 700; color: var(--color-text, #0f172a); }
.abs-bu-head__title small { color: var(--color-text-muted, #64748b); }
.abs-bu-head__kpi { display: flex; align-items: center; gap: 18px; }

.abs-bu-now {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 0.88rem;
  background: rgba(99,102,241,0.08);
  border: 1px solid rgba(99,102,241,0.35);
  color: #4338ca;
}
.abs-bu-now.is-vacation { background: rgba(34,197,94,0.1); border-color: rgba(34,197,94,0.4); color: #15803d; }
.abs-bu-now.is-sick_leave { background: rgba(220,38,38,0.1); border-color: rgba(220,38,38,0.4); color: #b91c1c; }
.abs-bu-now.is-business_trip { background: rgba(99,102,241,0.1); border-color: rgba(99,102,241,0.4); color: #4338ca; }
.abs-bu-now.is-other { background: rgba(148,163,184,0.14); border-color: rgba(148,163,184,0.45); color: #475569; }

/* Персональный таймлайн */
.abs-bu-timeline {
  border: 1px solid var(--color-border-subtle, rgba(0,0,0,0.06));
  border-radius: 8px;
  overflow: hidden;
}
.abs-bu-timeline__axis {
  position: relative;
  display: flex;
}
.abs-bu-timeline__axis--head {
  background: var(--color-surface-2, #f8fafc);
  border-bottom: 1px solid var(--color-border-subtle, rgba(0,0,0,0.06));
}
.abs-bu-timeline__axis--track {
  height: 40px;
  background: var(--color-surface, #fff);
}
.abs-bu-timeline .abs-day { min-width: 22px; }

/* Карточки */
.abs-bu-cards { display: flex; flex-direction: column; gap: 10px; }
.abs-card {
  display: grid;
  grid-template-columns: 42px 1fr auto;
  gap: 14px;
  align-items: center;
  padding: 12px 14px;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e2e8f0);
  border-left: 4px solid #94a3b8;
  border-radius: 10px;
}
.abs-card.is-vacation { border-left-color: #16a34a; }
.abs-card.is-sick_leave { border-left-color: #dc2626; }
.abs-card.is-business_trip { border-left-color: #6366f1; }
.abs-card.is-other { border-left-color: #94a3b8; }
.abs-card__icon {
  width: 42px; height: 42px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.05rem; color: #fff;
}
.abs-card.is-vacation .abs-card__icon { background: #16a34a; }
.abs-card.is-sick_leave .abs-card__icon { background: #dc2626; }
.abs-card.is-business_trip .abs-card__icon { background: #6366f1; }
.abs-card.is-other .abs-card__icon { background: #94a3b8; }
.abs-card__body { min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.abs-card__head { display: flex; flex-wrap: wrap; gap: 6px 12px; align-items: baseline; }
.abs-card__head strong { font-size: 0.95rem; color: var(--color-text, #0f172a); }
.abs-card__dates { color: var(--color-text-muted, #64748b); font-size: 0.85rem; font-variant-numeric: tabular-nums; }
.abs-card__duration { font-weight: 600; color: var(--color-text, #0f172a); }
.abs-card__comment { font-size: 0.85rem; line-height: 1.4; overflow-wrap: anywhere; }
.abs-card__actions { display: flex; gap: 4px; }
.abs-icon-btn {
  background: transparent; border: none; cursor: pointer;
  color: var(--color-text-muted, #64748b);
  padding: 6px 8px; border-radius: 6px;
  transition: background 0.1s, color 0.1s;
}
.abs-icon-btn:hover { background: rgba(0,0,0,0.05); color: var(--color-text, #0f172a); }
.abs-icon-btn.is-danger:hover { background: rgba(220,38,38,0.08); color: var(--color-danger, #dc2626); }

.abs-bu-empty {
  padding: 22px;
  text-align: center;
  color: var(--color-text-muted, #64748b);
  background: var(--color-surface-2, #f8fafc);
  border-radius: 10px;
  border: 1px dashed var(--color-border-strong, rgba(0,0,0,0.12));
}
.abs-bu-placeholder {
  margin: auto;
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  color: var(--color-text-muted, #64748b);
}
.abs-bu-placeholder i { font-size: 2rem; color: var(--color-text-subtle, #94a3b8); }
</style>
