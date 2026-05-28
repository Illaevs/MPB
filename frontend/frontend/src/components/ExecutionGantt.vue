<template>
  <div ref="rootRef" class="execution-gantt">
    <div class="execution-gantt-toolbar">
      <div class="execution-gantt-toolbar-left">
        <label class="execution-gantt-search">
          <i class="fas fa-search"></i>
          <input
            v-model.trim="searchQuery"
            type="text"
            :placeholder="searchPlaceholder"
          />
        </label>

        <div class="execution-gantt-filter-wrap">
          <button
            class="execution-gantt-icon-btn"
            title="Фильтр статусов"
            @click="showFilters = !showFilters"
          >
            <i class="fas fa-filter"></i>
          </button>

          <div v-if="showFilters" class="execution-gantt-filter-panel">
            <label
              v-for="item in statusFilterItems"
              :key="item.value"
              class="execution-gantt-filter-item"
            >
              <input
                type="checkbox"
                :checked="activeStatuses.has(item.value)"
                @change="toggleStatus(item.value)"
              />
              <span>{{ item.label }}</span>
            </label>
          </div>
        </div>
      </div>

      <div class="execution-gantt-toolbar-right">
        <div class="execution-gantt-scale-switch">
          <button
            v-for="item in scaleOptions"
            :key="item.value"
            class="execution-gantt-scale-btn"
            :class="{ active: scale === item.value }"
            @click="scale = item.value"
          >
            {{ item.label }}
          </button>
        </div>

        <button class="execution-gantt-secondary-btn" @click="toggleFullscreen">
          <i class="fas" :class="isFullscreen ? 'fa-compress' : 'fa-expand'"></i>
          <span>{{ isFullscreen ? collapseLabel : fullScreenLabel }}</span>
        </button>

        <button class="execution-gantt-secondary-btn" @click="exportRows">
          <i class="fas fa-download"></i>
          <span>{{ exportLabel }}</span>
        </button>
      </div>
    </div>

    <div v-if="!visibleGroups.length" class="execution-gantt-empty">
      <i class="fas fa-chart-gantt"></i>
      <h3>{{ emptyTitle }}</h3>
      <p>{{ emptyHint }}</p>
    </div>

    <div v-else class="execution-gantt-board">
      <div class="execution-gantt-scroll">
        <div class="execution-gantt-row execution-gantt-row--head" :style="gridTemplateStyle">
          <div class="execution-gantt-head execution-gantt-head--name">{{ nameColumnLabel }}</div>
          <div class="execution-gantt-head execution-gantt-head--status">{{ statusColumnLabel }}</div>
          <div class="execution-gantt-head execution-gantt-head--timeline">
            <div class="execution-gantt-track" :style="{ width: `${timelineWidth}px` }">
              <div
                v-for="segment in timelineSegments"
                :key="segment.key"
                class="execution-gantt-head-segment"
                :style="{ width: `${segment.width}px` }"
              >
                {{ segment.label }}
              </div>
              <div
                v-if="todayOffset !== null"
                class="execution-gantt-today-line"
                :style="{ left: `${todayOffset}px` }"
              ></div>
            </div>
          </div>
        </div>

        <template v-for="group in visibleGroups" :key="group.id">
          <div class="execution-gantt-row execution-gantt-row--group" :style="gridTemplateStyle">
            <div class="execution-gantt-group execution-gantt-group--name">
              <button class="execution-gantt-chevron" @click="toggleGroup(group.id)">
                <i class="fas" :class="isGroupCollapsed(group.id) ? 'fa-chevron-right' : 'fa-chevron-down'"></i>
              </button>
              <span class="execution-gantt-group-title">{{ group.name }}</span>
              <span class="execution-gantt-group-count">{{ countRows(group.items) }} {{ groupCountLabel }}</span>
            </div>

            <div class="execution-gantt-group execution-gantt-group--status">
              <span class="execution-gantt-status-pill" :class="statusClass(group.status)">
                <i class="fas fa-circle"></i>
                {{ statusLabel(group.status) }}
              </span>
            </div>

            <div class="execution-gantt-group execution-gantt-group--timeline">
              <div class="execution-gantt-track" :style="{ width: `${timelineWidth}px` }">
                <div
                  v-for="segment in timelineSegments"
                  :key="`${group.id}-${segment.key}`"
                  class="execution-gantt-grid-segment"
                  :style="{ width: `${segment.width}px` }"
                ></div>
                <div
                  v-if="todayOffset !== null"
                  class="execution-gantt-today-line"
                  :style="{ left: `${todayOffset}px` }"
                ></div>
                <div
                  v-if="hasDateRange(group)"
                  class="execution-gantt-bar execution-gantt-bar--group"
                  :class="barClass(group.status)"
                  :style="barStyle(group)"
                >
                  <span class="execution-gantt-bar-label">{{ displayProgress(group) }}</span>
                </div>
              </div>
            </div>
          </div>

          <template v-if="!isGroupCollapsed(group.id)">
            <template v-for="row in getVisibleRows(group.items)" :key="row.id">
              <div class="execution-gantt-row execution-gantt-row--item" :style="gridTemplateStyle">
                <div class="execution-gantt-cell execution-gantt-cell--name" :style="{ '--level': row.level }">
                  <button
                    v-if="row.children?.length"
                    class="execution-gantt-chevron execution-gantt-chevron--child"
                    @click="toggleRow(row.id)"
                  >
                    <i class="fas" :class="isRowCollapsed(row.id) ? 'fa-chevron-right' : 'fa-chevron-down'"></i>
                  </button>
                  <span v-else class="execution-gantt-row-spacer"></span>
                  <span class="execution-gantt-row-title" :title="row.name">{{ row.name }}</span>
                </div>

                <div class="execution-gantt-cell execution-gantt-cell--status">
                  <span class="execution-gantt-status-pill" :class="statusClass(row.status)">
                    <i class="fas fa-circle"></i>
                    {{ statusLabel(row.status) }}
                  </span>
                </div>

                <div class="execution-gantt-cell execution-gantt-cell--timeline">
                  <div class="execution-gantt-track" :style="{ width: `${timelineWidth}px` }">
                    <div
                      v-for="segment in timelineSegments"
                      :key="`${row.id}-${segment.key}`"
                      class="execution-gantt-grid-segment"
                      :style="{ width: `${segment.width}px` }"
                    ></div>

                    <div
                      v-if="todayOffset !== null"
                      class="execution-gantt-today-line"
                      :style="{ left: `${todayOffset}px` }"
                    ></div>

                    <div
                      v-if="hasDateRange(row)"
                      class="execution-gantt-bar"
                      :class="barClass(row.status)"
                      :style="barStyle(row)"
                    >
                      <span class="execution-gantt-bar-label">{{ displayProgress(row) }}</span>
                    </div>

                    <div
                      v-if="row.contractDueDate && contractSpanStyle(row)"
                      class="execution-gantt-contract-span"
                      :style="contractSpanStyle(row)"
                    ></div>

                    <div
                      v-if="row.contractDueDate"
                      class="execution-gantt-contract-marker"
                      :style="contractMarkerStyle(row)"
                      :title="contractDeadlineTitle"
                    ></div>
                  </div>
                </div>
              </div>
            </template>
          </template>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  groups: { type: Array, default: () => [] },
  searchPlaceholder: { type: String, default: 'Поиск по графику...' },
  emptyTitle: { type: String, default: 'Нет данных' },
  emptyHint: { type: String, default: 'Добавьте элементы для отображения графика.' },
  groupCountLabel: { type: String, default: 'элем.' },
  nameColumnLabel: { type: String, default: 'НАИМЕНОВАНИЕ' },
  statusColumnLabel: { type: String, default: 'СТАТУС' },
  contractDeadlineTitle: { type: String, default: 'Договорной срок' },
  fullScreenLabel: { type: String, default: 'На весь экран' },
  collapseLabel: { type: String, default: 'Свернуть' },
  exportLabel: { type: String, default: 'Экспорт' },
  exportFilename: { type: String, default: 'grafik-gantta.csv' }
})

const searchQuery = ref('')
const scale = ref('months')
const showFilters = ref(false)
const isFullscreen = ref(false)
const rootRef = ref(null)
const collapsedGroups = ref(new Set())
const collapsedRows = ref(new Set())
const activeStatuses = ref(new Set(['planned', 'not_started', 'in_progress', 'completed', 'overdue', 'delayed']))

const scaleOptions = [
  { value: 'days', label: 'Дни' },
  { value: 'months', label: 'Месяцы' },
  { value: 'quarters', label: 'Кварталы' }
]

const statusFilterItems = [
  { value: 'planned', label: 'План' },
  { value: 'not_started', label: 'Не начато' },
  { value: 'in_progress', label: 'В работе' },
  { value: 'completed', label: 'Готово' },
  { value: 'overdue', label: 'Просрочено' },
  { value: 'delayed', label: 'Задержано' }
]

const dayWidth = computed(() => {
  if (scale.value === 'days') return 24
  if (scale.value === 'quarters') return 1.8
  return 4.2
})

const toDate = (value) => {
  if (!value) return null
  const normalized = String(value).slice(0, 10)
  const parsed = new Date(`${normalized}T00:00:00`)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

const addDays = (value, count) => new Date(value.getTime() + count * 86400000)
const dayDiff = (start, end) => Math.round((end.getTime() - start.getTime()) / 86400000)
const startOfMonth = (value) => new Date(value.getFullYear(), value.getMonth(), 1)
const endOfMonth = (value) => new Date(value.getFullYear(), value.getMonth() + 1, 0)
const startOfQuarter = (value) => new Date(value.getFullYear(), Math.floor(value.getMonth() / 3) * 3, 1)

const decorateRow = (row, level = 0) => ({
  ...row,
  level,
  startDate: toDate(row.startDate),
  endDate: toDate(row.endDate),
  contractDueDate: toDate(row.contractDueDate),
  children: (row.children || []).map((child) => decorateRow(child, level + 1))
})

const decorateGroup = (group) => ({
  ...group,
  startDate: toDate(group.startDate),
  endDate: toDate(group.endDate),
  items: (group.items || []).map((row) => decorateRow(row))
})

const allGroups = computed(() => (props.groups || []).map((group) => decorateGroup(group)))

const matchesQuery = (row, query) => {
  const selfMatch = String(row.name || '').toLowerCase().includes(query)
  if (selfMatch) return true
  return (row.children || []).some((child) => matchesQuery(child, query))
}

const filterRow = (row, query) => {
  const nextChildren = (row.children || []).map((child) => filterRow(child, query)).filter(Boolean)
  const matches = !query || String(row.name || '').toLowerCase().includes(query)
  const statusMatches = activeStatuses.value.has(row.status || 'planned')
  if (!matches && !nextChildren.length) return null
  if (!statusMatches && !nextChildren.length) return null
  return { ...row, children: nextChildren }
}

const visibleGroups = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return allGroups.value
    .map((group) => {
      const nextItems = group.items.map((row) => filterRow(row, query)).filter(Boolean)
      const groupMatches = !query || String(group.name || '').toLowerCase().includes(query) || group.items.some((row) => matchesQuery(row, query))
      if (!groupMatches && !nextItems.length) return null
      if (!nextItems.length) return null
      return { ...group, items: nextItems }
    })
    .filter(Boolean)
})

const timelineBounds = computed(() => {
  const dates = []
  const pushDates = (row) => {
    if (row.startDate) dates.push(row.startDate)
    if (row.endDate) dates.push(row.endDate)
    if (row.contractDueDate) dates.push(row.contractDueDate)
    ;(row.children || []).forEach(pushDates)
  }

  visibleGroups.value.forEach((group) => {
    if (group.startDate) dates.push(group.startDate)
    if (group.endDate) dates.push(group.endDate)
    group.items.forEach(pushDates)
  })

  const today = new Date()
  if (!dates.length) {
    return {
      start: startOfMonth(addDays(today, -30)),
      end: endOfMonth(addDays(today, 120))
    }
  }

  dates.sort((a, b) => a - b)
  return {
    start: startOfMonth(addDays(dates[0], -14)),
    end: endOfMonth(addDays(dates[dates.length - 1], 14))
  }
})

const timelineSegments = computed(() => {
  const segments = []
  const { start, end } = timelineBounds.value
  const cursor = new Date(start)

  while (cursor <= end) {
    if (scale.value === 'days') {
      segments.push({
        key: cursor.toISOString(),
        label: cursor.toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' }),
        width: dayWidth.value
      })
      cursor.setDate(cursor.getDate() + 1)
      continue
    }

    if (scale.value === 'quarters') {
      const quarterStart = startOfQuarter(cursor)
      const quarterEnd = new Date(quarterStart.getFullYear(), quarterStart.getMonth() + 3, 0)
      const effectiveStart = cursor > quarterStart ? cursor : quarterStart
      const effectiveEnd = quarterEnd > end ? end : quarterEnd
      segments.push({
        key: `${quarterStart.getFullYear()}-${quarterStart.getMonth()}`,
        label: `${Math.floor(quarterStart.getMonth() / 3) + 1} кв. ${quarterStart.getFullYear()}`,
        width: (dayDiff(effectiveStart, effectiveEnd) + 1) * dayWidth.value
      })
      cursor.setMonth(cursor.getMonth() + 3, 1)
      continue
    }

    const monthStart = startOfMonth(cursor)
    const monthEnd = endOfMonth(cursor)
    const effectiveEnd = monthEnd > end ? end : monthEnd
    segments.push({
      key: `${monthStart.getFullYear()}-${monthStart.getMonth()}`,
      label: monthStart.toLocaleDateString('ru-RU', { month: 'short', year: 'numeric' }),
      width: (dayDiff(cursor, effectiveEnd) + 1) * dayWidth.value
    })
    cursor.setMonth(cursor.getMonth() + 1, 1)
  }

  return segments
})

const timelineWidth = computed(() => timelineSegments.value.reduce((sum, segment) => sum + segment.width, 0))
const gridTemplateStyle = computed(() => ({ gridTemplateColumns: `260px 120px ${timelineWidth.value}px` }))

const todayOffset = computed(() => {
  const today = new Date()
  const { start, end } = timelineBounds.value
  if (today < start || today > end) return null
  return dayDiff(start, today) * dayWidth.value
})

const countRows = (rows = []) => rows.reduce((sum, row) => sum + 1 + countRows(row.children || []), 0)
const hasDateRange = (row) => !!(row.startDate && row.endDate)
const isGroupCollapsed = (id) => collapsedGroups.value.has(id)
const isRowCollapsed = (id) => collapsedRows.value.has(id)

const flattenRows = (rows = []) => rows.flatMap((row) => {
  if (isRowCollapsed(row.id) || !row.children?.length) return [row]
  return [row, ...flattenRows(row.children)]
})

const getVisibleRows = (rows = []) => flattenRows(rows)

const toggleGroup = (id) => {
  const next = new Set(collapsedGroups.value)
  next.has(id) ? next.delete(id) : next.add(id)
  collapsedGroups.value = next
}

const toggleRow = (id) => {
  const next = new Set(collapsedRows.value)
  next.has(id) ? next.delete(id) : next.add(id)
  collapsedRows.value = next
}

const statusLabel = (value) => {
  if (value === 'completed') return 'Готово'
  if (value === 'in_progress') return 'В работе'
  if (value === 'overdue' || value === 'delayed') return 'Просрочено'
  if (value === 'not_started') return 'Не начато'
  return 'План'
}

const statusClass = (value) => `is-${value || 'planned'}`
const barClass = (value) => `is-${value || 'planned'}`
const displayProgress = (row) => `${Math.max(0, Math.min(100, Number(row.progress || 0))).toFixed(0)}%`

const barStyle = (row) => {
  const left = dayDiff(timelineBounds.value.start, row.startDate) * dayWidth.value
  const width = Math.max((dayDiff(row.startDate, row.endDate) + 1) * dayWidth.value, 18)
  return { left: `${left}px`, width: `${width}px` }
}

const contractMarkerStyle = (row) => ({
  left: `${dayDiff(timelineBounds.value.start, row.contractDueDate) * dayWidth.value}px`
})

const contractSpanStyle = (row) => {
  if (!row.endDate || !row.contractDueDate) return null
  const startLeft = dayDiff(timelineBounds.value.start, row.endDate) * dayWidth.value
  const endLeft = dayDiff(timelineBounds.value.start, row.contractDueDate) * dayWidth.value
  if (startLeft === endLeft) return null
  return {
    left: `${Math.min(startLeft, endLeft)}px`,
    width: `${Math.max(Math.abs(endLeft - startLeft), 2)}px`
  }
}

const toggleStatus = (value) => {
  const next = new Set(activeStatuses.value)
  next.has(value) ? next.delete(value) : next.add(value)
  activeStatuses.value = next
}

const syncFullscreenState = () => {
  isFullscreen.value = document.fullscreenElement === rootRef.value
}

const toggleFullscreen = async () => {
  const target = rootRef.value
  if (!target) return
  if (document.fullscreenElement !== target) {
    await target.requestFullscreen?.()
    syncFullscreenState()
    return
  }
  await document.exitFullscreen?.()
  syncFullscreenState()
}

const exportRows = () => {
  const lines = ['Группа;Наименование;Статус;Начало;Рабочий срок;Договорной срок']
  visibleGroups.value.forEach((group) => {
    getVisibleRows(group.items).forEach((row) => {
      lines.push([
        group.name,
        row.name,
        statusLabel(row.status),
        row.startDate ? row.startDate.toISOString().slice(0, 10) : '',
        row.endDate ? row.endDate.toISOString().slice(0, 10) : '',
        row.contractDueDate ? row.contractDueDate.toISOString().slice(0, 10) : ''
      ].join(';'))
    })
  })

  const blob = new Blob([`\uFEFF${lines.join('\n')}`], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = props.exportFilename
  link.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  document.addEventListener('fullscreenchange', syncFullscreenState)
})

onBeforeUnmount(() => {
  document.removeEventListener('fullscreenchange', syncFullscreenState)
})
</script>

<style scoped>
.execution-gantt {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
  min-height: 0;
  color: #1e293b;
}

.execution-gantt-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 14px;
  border: 1px solid #dbe4f0;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
}

.execution-gantt-toolbar-left,
.execution-gantt-toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.execution-gantt-search {
  position: relative;
  display: flex;
  align-items: center;
  min-width: 240px;
}

.execution-gantt-search i {
  position: absolute;
  left: 12px;
  color: #94a3b8;
  font-size: 13px;
}

.execution-gantt-search input {
  width: 100%;
  height: 40px;
  padding: 0 14px 0 34px;
  border: 1px solid #d9e2ef;
  border-radius: 10px;
  background: #fff;
}

.execution-gantt-search input:focus {
  outline: none;
  border-color: #5b86ff;
  box-shadow: 0 0 0 3px rgba(91, 134, 255, 0.14);
}

.execution-gantt-icon-btn,
.execution-gantt-secondary-btn,
.execution-gantt-scale-btn {
  border: 1px solid #d9e2ef;
  background: #fff;
  color: #334155;
  border-radius: 10px;
  height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.execution-gantt-icon-btn {
  width: 40px;
}

.execution-gantt-secondary-btn {
  padding: 0 14px;
  font-size: 0.9rem;
  font-weight: 600;
}

.execution-gantt-scale-switch {
  display: inline-flex;
  padding: 3px;
  border: 1px solid #d9e2ef;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.05);
}

.execution-gantt-scale-btn {
  border: none;
  height: 34px;
  padding: 0 14px;
  font-size: 0.8rem;
  font-weight: 700;
  background: transparent;
}

.execution-gantt-scale-btn.active {
  background: #f3f6fb;
  color: #0f172a;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}

.execution-gantt-filter-wrap {
  position: relative;
}

.execution-gantt-filter-panel {
  position: absolute;
  top: 46px;
  left: 0;
  z-index: 20;
  min-width: 180px;
  padding: 10px;
  border: 1px solid #dbe4f0;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.12);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.execution-gantt-filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: #475569;
}

.execution-gantt-board {
  flex: 1 1 auto;
  min-height: 0;
  height: 100%;
  border: 1px solid #dbe4f0;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.08);
  overflow: hidden;
}

.execution-gantt-scroll {
  height: 100%;
  overflow: auto;
}

.execution-gantt-row {
  display: grid;
  min-width: max-content;
}

.execution-gantt-row--head {
  position: sticky;
  top: 0;
  z-index: 12;
  background: #f8fafc;
  border-bottom: 1px solid #dbe4f0;
}

.execution-gantt-row--group {
  background: #f8fafc;
  border-bottom: 1px solid #dbe4f0;
}

.execution-gantt-row--item {
  border-bottom: 1px solid #edf2f8;
}

.execution-gantt-head,
.execution-gantt-group,
.execution-gantt-cell {
  min-height: 44px;
  display: flex;
  align-items: center;
  padding: 0 14px;
}

.execution-gantt-head--name,
.execution-gantt-group--name,
.execution-gantt-cell--name {
  position: sticky;
  left: 0;
  z-index: 6;
  background: inherit;
  border-right: 1px solid #e6edf5;
}

.execution-gantt-head--status,
.execution-gantt-group--status,
.execution-gantt-cell--status {
  position: sticky;
  left: 260px;
  z-index: 6;
  background: inherit;
  border-right: 1px solid #e6edf5;
}

.execution-gantt-head {
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: #64748b;
}

.execution-gantt-group--name,
.execution-gantt-cell--name {
  align-items: flex-start;
  padding-top: 10px;
  padding-bottom: 10px;
}

.execution-gantt-group-title,
.execution-gantt-row-title {
  display: block;
  overflow: visible;
  text-overflow: clip;
  white-space: normal;
  word-break: break-word;
  line-height: 1.3;
}

.execution-gantt-group-title {
  font-weight: 700;
}

.execution-gantt-group-count {
  margin-left: 10px;
  padding: 3px 8px;
  border-radius: 999px;
  background: #edf2ff;
  color: #5b6f95;
  font-size: 0.7rem;
}

.execution-gantt-chevron {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: #64748b;
  flex: 0 0 24px;
}

.execution-gantt-chevron--child {
  margin-left: calc(var(--level) * 18px);
}

.execution-gantt-row-spacer {
  width: 24px;
  flex: 0 0 24px;
  margin-left: calc(var(--level) * 18px);
}

.execution-gantt-track {
  position: relative;
  display: flex;
  min-height: 44px;
}

.execution-gantt-head-segment,
.execution-gantt-grid-segment {
  flex: 0 0 auto;
  border-right: 1px solid #edf2f8;
}

.execution-gantt-head-segment {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.78rem;
  font-weight: 700;
  color: #4b5563;
}

.execution-gantt-grid-segment {
  min-height: 44px;
}

.execution-gantt-today-line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #ff3b30;
  z-index: 3;
}

.execution-gantt-bar {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  height: 26px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  overflow: hidden;
  padding: 0 10px;
  font-size: 0.72rem;
  font-weight: 800;
  color: #fff;
  z-index: 2;
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.08);
}

.execution-gantt-bar--group {
  opacity: 0.9;
}

.execution-gantt-bar-label {
  position: relative;
  z-index: 2;
  white-space: nowrap;
}

.execution-gantt-contract-span {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  height: 0;
  border-top: 2px dashed #8b5cf6;
  z-index: 2;
}

.execution-gantt-contract-marker {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%) rotate(45deg);
  width: 12px;
  height: 12px;
  border: 2px solid #8b5cf6;
  background: #fff;
  z-index: 4;
}

.execution-gantt-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  border: 1px solid transparent;
  white-space: nowrap;
}

.execution-gantt-status-pill i {
  font-size: 8px;
}

.execution-gantt-bar.is-completed,
.execution-gantt-status-pill.is-completed {
  background: #11a36c;
  color: #fff;
  border-color: #11a36c;
}

.execution-gantt-bar.is-in_progress,
.execution-gantt-status-pill.is-in_progress {
  background: #3b82f6;
  color: #fff;
  border-color: #3b82f6;
}

.execution-gantt-bar.is-overdue,
.execution-gantt-status-pill.is-overdue,
.execution-gantt-bar.is-delayed,
.execution-gantt-status-pill.is-delayed {
  background: #ef4444;
  color: #fff;
  border-color: #ef4444;
}

.execution-gantt-bar.is-not_started,
.execution-gantt-status-pill.is-not_started,
.execution-gantt-bar.is-planned,
.execution-gantt-status-pill.is-planned {
  background: #eef2f7;
  color: #475569;
  border-color: #d8e1ec;
}

.execution-gantt-empty {
  flex: 1 1 auto;
  border: 1px dashed #d9e2ef;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #64748b;
  min-height: 320px;
}

.execution-gantt-empty i {
  font-size: 2rem;
  color: #94a3b8;
}

:root[data-theme="dark"] .execution-gantt,
:root[data-theme="dark"] .execution-gantt-toolbar,
:root[data-theme="dark"] .execution-gantt-board,
:root[data-theme="dark"] .execution-gantt-filter-panel,
:root[data-theme="dark"] .execution-gantt-search input,
:root[data-theme="dark"] .execution-gantt-icon-btn,
:root[data-theme="dark"] .execution-gantt-secondary-btn,
:root[data-theme="dark"] .execution-gantt-scale-switch {
  background: rgba(15, 23, 42, 0.9);
  color: #e2e8f0;
  border-color: rgba(148, 163, 184, 0.24);
}

:root[data-theme="dark"] .execution-gantt-row--head,
:root[data-theme="dark"] .execution-gantt-row--group,
:root[data-theme="dark"] .execution-gantt-head--name,
:root[data-theme="dark"] .execution-gantt-group--name,
:root[data-theme="dark"] .execution-gantt-cell--name,
:root[data-theme="dark"] .execution-gantt-head--status,
:root[data-theme="dark"] .execution-gantt-group--status,
:root[data-theme="dark"] .execution-gantt-cell--status {
  background: rgba(15, 23, 42, 0.94);
}

:root[data-theme="dark"] .execution-gantt-grid-segment,
:root[data-theme="dark"] .execution-gantt-head-segment {
  border-color: rgba(148, 163, 184, 0.12);
  color: #cbd5e1;
}

:root[data-theme="dark"] .execution-gantt-row--item {
  border-color: rgba(148, 163, 184, 0.12);
}

@media (max-width: 1024px) {
  .execution-gantt-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .execution-gantt-toolbar-left,
  .execution-gantt-toolbar-right {
    justify-content: space-between;
    flex-wrap: wrap;
  }
}

@media (max-width: 768px) {
  .execution-gantt-search {
    min-width: 0;
    width: 100%;
  }

  .execution-gantt-toolbar-right {
    justify-content: flex-start;
  }

  .execution-gantt-row {
    grid-template-columns: 220px 112px auto !important;
  }
}
</style>
