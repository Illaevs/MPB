<template>
  <div class="dash">
    <header class="dash-topbar">
      <div class="dash-topbar__meta">
        <span class="dash-topbar__eyebrow">Главная</span>
        <h1 class="dash-topbar__title">{{ headerTitle }}</h1>
      </div>
      <div class="dash-topbar__tools">
        <div v-if="canUseManagerMode" class="dash-seg">
          <button
            type="button"
            class="dash-seg__btn"
            :class="{ 'dash-seg__btn--active': dashboardMode === 'manager' }"
            @click="dashboardMode = 'manager'"
          >
            <i class="fas fa-binoculars"></i><span>Руководитель</span>
          </button>
          <button
            type="button"
            class="dash-seg__btn"
            :class="{ 'dash-seg__btn--active': dashboardMode === 'default' }"
            @click="dashboardMode = 'default'"
          >
            <i class="fas fa-chart-line"></i><span>Операционный</span>
          </button>
        </div>
        <div class="dash-cfg">
          <button
            type="button"
            class="dash-refresh"
            :class="{ 'dash-refresh--active': dashSettingsOpen }"
            title="Настроить дашборд"
            @click="dashSettingsOpen = !dashSettingsOpen"
          >
            <i class="fas fa-sliders"></i>
          </button>
          <transition name="dash-pop">
            <div
              v-if="dashSettingsOpen"
              class="dash-cfg__pop"
              v-click-outside="() => dashSettingsOpen = false"
            >
              <div class="dash-cfg__head">Блоки дашборда</div>
              <label
                v-for="block in dashboardBlocks"
                :key="block.id"
                class="dash-cfg__item"
              >
                <input
                  type="checkbox"
                  :checked="isDashboardBlockVisible(block.id)"
                  @change="toggleDashboardBlock(block.id)"
                />
                <span>{{ block.label }}</span>
              </label>
              <div class="dash-cfg__hint">
                <i class="fas fa-up-down-left-right"></i>
                Боковые виджеты можно перетаскивать за заголовок
              </div>
            </div>
          </transition>
        </div>
        <button type="button" class="dash-refresh" :disabled="loading" title="Обновить данные" @click="reload">
          <i class="fas fa-rotate" :class="{ 'dash-refresh--spin': loading }"></i>
        </button>
      </div>
    </header>

    <section v-show="isDashboardBlockVisible('hero')" class="dash-hero">
      <div class="dash-hero__primary">
        <span class="dash-hero__label">Стоимость портфеля</span>
        <span class="dash-hero__value">
          <SkeletonLoader v-if="loading" style="width: 170px; height: 30px;" />
          <template v-else>{{ formatMoneyCompact(dealStats.portfolio) }}</template>
        </span>
        <div class="dash-hero__sub">
          <div class="dash-hero__stat">
            <span class="dash-hero__stat-value">{{ loading ? '—' : dealStats.active }}</span>
            <span class="dash-hero__stat-label">Активные сделки</span>
          </div>
          <div class="dash-hero__stat">
            <span class="dash-hero__stat-value">{{ loading ? '—' : formatMoneyCompact(dealStats.avg) }}</span>
            <span class="dash-hero__stat-label">Средний чек</span>
          </div>
          <div class="dash-hero__stat">
            <span class="dash-hero__stat-value">{{ loading ? '—' : taskStats.rate + '%' }}</span>
            <span class="dash-hero__stat-label">Выполнение задач</span>
          </div>
        </div>
      </div>
      <div class="dash-hero__chart">
        <div class="dash-hero__chart-head">
          <span class="dash-hero__label">Активность · 14 дней</span>
          <span class="dash-hero__chart-total">{{ activitySeries.total }}</span>
        </div>
        <div class="dash-hero__spark">
          <SkeletonLoader v-if="activityLoading" height="64px" />
          <apexchart v-else type="area" height="64" :options="areaChartOptions" :series="areaChartSeries" />
        </div>
      </div>
    </section>

    <section v-show="isDashboardBlockVisible('kpis')" class="dash-kpis">
      <article
        v-for="stat in currentStatCards"
        :key="stat.key"
        class="dash-kpi"
        :class="{ 'dash-kpi--alert': stat.alert }"
      >
        <span class="dash-kpi__icon" :style="{ color: stat.color, background: stat.iconBg }">
          <i :class="stat.icon"></i>
        </span>
        <span class="dash-kpi__body">
          <span class="dash-kpi__value">
            <SkeletonLoader v-if="loading" style="width: 36px; height: 18px;" />
            <template v-else>{{ stat.value }}</template>
          </span>
          <span class="dash-kpi__label">{{ stat.label }}</span>
        </span>
        <span v-if="stat.badge && !loading" class="dash-kpi__badge">{{ stat.badge }}</span>
      </article>
    </section>

    <section class="dash-grid">
      <div v-show="isDashboardBlockVisible('lists')" class="dash-col dash-col--main">
        <article v-for="panel in listPanels" :key="panel.key" class="dash-panel">
          <div class="dash-panel__head">
            <h3 class="dash-panel__title">{{ panel.title }}</h3>
            <router-link :to="panel.link" class="dash-panel__link">{{ panel.linkLabel }}</router-link>
          </div>

          <div v-if="loading" class="dash-panel__body dash-skel">
            <SkeletonLoader v-for="i in 4" :key="`${panel.key}-s-${i}`" height="40px" />
          </div>

          <div v-else-if="!panel.items.length" class="dash-empty">
            <span class="dash-empty__icon" :class="{ 'dash-empty__icon--ok': panel.emptyOk }">
              <i :class="panel.emptyIcon"></i>
            </span>
            <span class="dash-empty__text">
              <span class="dash-empty__title">{{ panel.emptyTitle }}</span>
              <span class="dash-empty__hint">{{ panel.emptyHint }}</span>
            </span>
          </div>

          <div v-else class="dash-list">
            <button
              v-for="row in panel.items"
              :key="panel.key + '-' + row.id"
              type="button"
              class="dash-row"
              @click="panel.onClick(row)"
            >
              <span v-if="panel.marker" class="dash-row__dot" :class="panel.marker(row)"></span>
              <span class="dash-row__main">
                <span class="dash-row__title">{{ panel.titleOf(row) }}</span>
                <span class="dash-row__meta">
                  <span v-for="(m, mi) in panel.metaOf(row)" :key="mi"><i :class="m.icon"></i>{{ m.text }}</span>
                </span>
              </span>
              <span class="dash-row__aside">
                <span class="dash-chip" :class="panel.chipClass(row)">{{ panel.chipText(row) }}</span>
                <span v-if="panel.valueOf(row)" class="dash-row__value">{{ panel.valueOf(row) }}</span>
              </span>
            </button>
          </div>
        </article>
      </div>

      <draggable
        tag="aside"
        class="dash-col dash-col--side"
        v-model="sideModel"
        :item-key="(el) => el"
        handle=".dash-drag"
        :animation="150"
      >
        <template #item="{ element }">
          <div class="dash-side-slot">
            <article v-if="element === 'portfolio'" class="dash-panel">
              <div class="dash-panel__head">
                <h3 class="dash-panel__title">
                  <i class="fas fa-grip-vertical dash-drag" title="Перетащить"></i>
                  Портфель проектов
                </h3>
                <router-link to="/projects" class="dash-panel__link">Проекты</router-link>
              </div>
              <div v-if="loading" class="dash-panel__body dash-skel">
                <SkeletonLoader height="150px" />
              </div>
              <div v-else-if="!dealStats.total" class="dash-empty">
                <span class="dash-empty__icon"><i class="fas fa-folder-open"></i></span>
                <span class="dash-empty__text">
                  <span class="dash-empty__title">Нет проектов</span>
                  <span class="dash-empty__hint">Распределение появится после первой сделки</span>
                </span>
              </div>
              <div v-else class="dash-portfolio">
                <div class="dash-portfolio__chart">
                  <apexchart type="donut" height="150" :options="donutChartOptions" :series="donutChartSeries" />
                </div>
                <ul class="dash-legend">
                  <li v-for="seg in statusDistribution" :key="seg.key">
                    <span class="dash-legend__dot" :style="{ background: seg.color }"></span>
                    <span class="dash-legend__label">{{ seg.label }}</span>
                    <span class="dash-legend__value">{{ seg.value }}</span>
                    <span class="dash-legend__pct">{{ seg.pct }}%</span>
                  </li>
                </ul>
              </div>
            </article>

            <article v-else-if="element === 'tasks'" class="dash-panel">
              <div class="dash-panel__head">
                <h3 class="dash-panel__title">
                  <i class="fas fa-grip-vertical dash-drag" title="Перетащить"></i>
                  Задачи
                </h3>
                <router-link to="/tasks" class="dash-panel__link">Все задачи</router-link>
              </div>
              <div class="dash-bars">
                <div v-for="bar in taskBars" :key="bar.key" class="dash-bar">
                  <div class="dash-bar__top">
                    <span class="dash-bar__label">{{ bar.label }}</span>
                    <span class="dash-bar__value">{{ loading ? '—' : bar.value }}</span>
                  </div>
                  <div class="dash-bar__track">
                    <span class="dash-bar__fill" :class="bar.cls" :style="{ width: (loading ? 0 : bar.pct) + '%' }"></span>
                  </div>
                </div>
              </div>
            </article>

            <article v-else-if="element === 'actions'" class="dash-panel dash-panel--actions">
              <div class="dash-panel__head">
                <h3 class="dash-panel__title dash-panel__title--accent">
                  <i class="fas fa-grip-vertical dash-drag" title="Перетащить"></i>
                  <i class="fas fa-bolt"></i> Быстрые действия
                </h3>
              </div>
              <div class="dash-actions">
                <button
                  v-for="action in quickActions"
                  :key="action.key"
                  type="button"
                  class="dash-action"
                  :class="{ 'dash-action--primary': action.primary }"
                  @click="action.onClick"
                >
                  <i :class="action.icon"></i><span>{{ action.label }}</span>
                </button>
              </div>
            </article>
          </div>
        </template>
      </draggable>
    </section>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRouter } from 'vue-router'
import draggable from 'vuedraggable'
import { api } from '../services/api'
import SkeletonLoader from '../components/ui/SkeletonLoader.vue'
import VueApexCharts from 'vue3-apexcharts'
import { useAuthStore } from '../stores/auth'
import { useUiPreferences } from '../composables/useUiPreferences'

const clickOutside = {
  beforeMount(el, binding) {
    el._co = (e) => { if (!(el === e.target || el.contains(e.target))) binding.value(e) }
    setTimeout(() => document.addEventListener('click', el._co), 0)
  },
  unmounted(el) { document.removeEventListener('click', el._co) },
}

const DASHBOARD_BLOCKS = [
  { id: 'hero', label: 'Портфель и активность' },
  { id: 'kpis', label: 'KPI-карточки' },
  { id: 'lists', label: 'Списки (проекты/задачи)' },
  { id: 'portfolio', label: 'Портфель проектов' },
  { id: 'tasks', label: 'Задачи (диаграмма)' },
  { id: 'actions', label: 'Быстрые действия' },
]

export default {
  name: 'Home',
  components: { SkeletonLoader, apexchart: VueApexCharts, draggable },
  directives: { 'click-outside': clickOutside },
  setup() {
    const authStore = useAuthStore()
    const {
      isDashboardBlockVisible,
      toggleDashboardBlock,
      getDashboardSideOrder,
      setDashboardSideOrder,
    } = useUiPreferences()
    const dashSettingsOpen = ref(false)
    const dashboardBlocks = DASHBOARD_BLOCKS
    const SIDE_IDS = ['portfolio', 'tasks', 'actions']
    // Полный упорядоченный список боковых виджетов (все id гарантированно есть).
    const sideOrderFull = computed(() => {
      const saved = getDashboardSideOrder().filter((id) => SIDE_IDS.includes(id))
      return [...saved, ...SIDE_IDS.filter((id) => !saved.includes(id))]
    })
    // Для draggable показываем только видимые; скрытые сохраняем в хвосте порядка.
    const sideModel = computed({
      get: () => sideOrderFull.value.filter((id) => isDashboardBlockVisible(id)),
      set: (list) => {
        const hidden = sideOrderFull.value.filter((id) => !list.includes(id))
        setDashboardSideOrder([...list, ...hidden])
      },
    })
    const loading = ref(true)
    const activityLoading = ref(true)
    const projects = ref([])
    const tasks = ref([])
    const activityData = ref([])
    const dashboardMode = ref('default')
    const themeTick = ref(0)
    const managerSummary = ref({
      enabled: false,
      active_deals: 0,
      risky_deals_count: 0,
      overdue_tasks: 0,
      unsigned_contracts_count: 0,
      stalled_contracts_count: 0,
      overloaded_users_count: 0,
      risky_deals: [],
      overloaded_users: [],
      contracts_on_approval: []
    })
    const summary = ref({
      active_deals: 0,
      overdue_tasks: 0,
      new_documents_7d: 0,
      upload_errors_7d: 0,
      unread_notifications: 0
    })
    const router = useRouter()
    const canUseManagerMode = computed(() =>
      Boolean(
        authStore.isSuperuser ||
        authStore.permissions?.projects?.read_all ||
        authStore.permissions?.tasks?.read_all ||
        authStore.permissions?.contracts?.read_all ||
        authStore.permissions?.users?.read_all
      )
    )

    const headerTitle = computed(() =>
      dashboardMode.value === 'manager' ? 'Режим руководителя' : 'Операционный обзор'
    )

    /* ---- Theme-aware chart tokens ---- */
    const readToken = (name, fallback) => {
      if (typeof window === 'undefined') return fallback
      const v = getComputedStyle(document.documentElement).getPropertyValue(name)
      return (v && v.trim()) || fallback
    }
    const chartTokens = computed(() => {
      void themeTick.value
      return {
        primary: readToken('--color-primary', '#2563eb'),
        success: readToken('--color-success', '#16a34a'),
        warning: readToken('--color-warning', '#d97706'),
        danger: readToken('--color-danger', '#dc2626'),
        subtle: readToken('--color-text-subtle', '#94a3b8'),
        muted: readToken('--color-text-muted', '#64748b'),
        strong: readToken('--color-text-strong', '#0f172a'),
        border: readToken('--color-border', '#e2e8f0')
      }
    })
    const isDark = computed(() => {
      void themeTick.value
      if (typeof document === 'undefined') return false
      const attr = document.documentElement.getAttribute('data-theme')
      if (attr === 'dark') return true
      if (attr === 'light') return false
      return typeof window !== 'undefined' &&
        window.matchMedia('(prefers-color-scheme: dark)').matches
    })

    /* ---- Derived statistics ---- */
    const getProjectAmount = (project) =>
      project?.total_contract_value ?? project?.budget ?? 0

    const dealStats = computed(() => {
      const list = projects.value || []
      const counts = { active: 0, completed: 0, on_hold: 0, cancelled: 0 }
      let portfolio = 0
      list.forEach((p) => {
        if (counts[p.status] !== undefined) counts[p.status] += 1
        portfolio += Number(getProjectAmount(p)) || 0
      })
      const total = list.length
      return { ...counts, total, portfolio, avg: total ? portfolio / total : 0 }
    })

    const isOverdue = (value) => {
      if (!value) return false
      const date = new Date(value)
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      date.setHours(0, 0, 0, 0)
      return date < today
    }

    const taskStats = computed(() => {
      const list = tasks.value || []
      let done = 0
      let active = 0
      let overdue = 0
      list.forEach((t) => {
        if (t.status === 'completed') done += 1
        else if (t.status !== 'cancelled') {
          active += 1
          if (isOverdue(t.due_date)) overdue += 1
        }
      })
      const total = list.length
      return { total, done, active, overdue, rate: total ? Math.round((done / total) * 100) : 0 }
    })

    const taskBars = computed(() => {
      const s = taskStats.value
      const base = Math.max(s.total, 1)
      return [
        { key: 'done', label: 'Выполнено', value: s.done, pct: Math.round((s.done / base) * 100), cls: 'dash-bar__fill--ok' },
        { key: 'active', label: 'В работе', value: s.active, pct: Math.round((s.active / base) * 100), cls: 'dash-bar__fill--primary' },
        { key: 'overdue', label: 'Просрочено', value: s.overdue, pct: Math.round((s.overdue / base) * 100), cls: 'dash-bar__fill--danger' }
      ]
    })

    const activeProjects = computed(() =>
      projects.value.filter((project) => project.status === 'active').slice(0, 5)
    )

    const urgentTasks = computed(() =>
      tasks.value
        .filter((task) => task.status !== 'completed' && task.status !== 'cancelled')
        .sort((a, b) => new Date(a.due_date || 0) - new Date(b.due_date || 0))
        .slice(0, 5)
    )

    const riskyDeals = computed(() => managerSummary.value.risky_deals || [])
    const overloadedUsers = computed(() => managerSummary.value.overloaded_users || [])
    const contractsOnApproval = computed(() => managerSummary.value.contracts_on_approval || [])

    const statCards = computed(() => [
      { key: 'deals', icon: 'fas fa-share-alt', label: 'Активные сделки', value: summary.value.active_deals, color: '#2563eb', iconBg: 'rgba(37, 99, 235, 0.12)' },
      { key: 'overdue', icon: 'fas fa-exclamation-triangle', label: 'Просрочено', value: summary.value.overdue_tasks, color: '#dc2626', iconBg: 'rgba(220, 38, 38, 0.12)', alert: summary.value.overdue_tasks > 0, badge: summary.value.overdue_tasks > 0 ? 'Внимание' : null },
      { key: 'docs', icon: 'far fa-file-alt', label: 'Документы · 7д', value: summary.value.new_documents_7d, color: '#d97706', iconBg: 'rgba(217, 119, 6, 0.14)' },
      { key: 'errors', icon: 'fas fa-cloud-upload-alt', label: 'Ошибки загрузок', value: summary.value.upload_errors_7d, color: summary.value.upload_errors_7d > 0 ? '#dc2626' : '#16a34a', iconBg: summary.value.upload_errors_7d > 0 ? 'rgba(220, 38, 38, 0.12)' : 'rgba(22, 163, 74, 0.14)' },
      { key: 'unread', icon: 'far fa-bell', label: 'Непрочитано', value: summary.value.unread_notifications, color: '#64748b', iconBg: 'rgba(100, 116, 139, 0.12)' }
    ])

    const managerStatCards = computed(() => [
      { key: 'active', icon: 'fas fa-folder-open', label: 'Активные сделки', value: managerSummary.value.active_deals, color: '#2563eb', iconBg: 'rgba(37, 99, 235, 0.12)' },
      { key: 'risky', icon: 'fas fa-triangle-exclamation', label: 'Сделки с риском', value: managerSummary.value.risky_deals_count, color: '#dc2626', iconBg: 'rgba(220, 38, 38, 0.12)', alert: managerSummary.value.risky_deals_count > 0, badge: managerSummary.value.risky_deals_count > 0 ? 'Контроль' : null },
      { key: 'overdue', icon: 'fas fa-list-check', label: 'Просроченные задачи', value: managerSummary.value.overdue_tasks, color: '#dc2626', iconBg: 'rgba(220, 38, 38, 0.12)', alert: managerSummary.value.overdue_tasks > 0 },
      { key: 'unsigned', icon: 'fas fa-file-signature', label: 'Без подписи', value: managerSummary.value.unsigned_contracts_count, color: '#d97706', iconBg: 'rgba(217, 119, 6, 0.14)' },
      { key: 'stalled', icon: 'fas fa-hourglass-half', label: 'Зависли', value: managerSummary.value.stalled_contracts_count, color: '#7c3aed', iconBg: 'rgba(124, 58, 237, 0.14)', alert: managerSummary.value.stalled_contracts_count > 0 }
    ])

    const currentStatCards = computed(() =>
      dashboardMode.value === 'manager' ? managerStatCards.value : statCards.value
    )

    const formatCurrency = (value) =>
      value !== null && value !== undefined && value !== '' && !Number.isNaN(Number(value))
        ? new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(Number(value))
        : '—'

    const formatMoneyCompact = (value) => {
      const n = Number(value)
      if (!Number.isFinite(n)) return '0 ₽'
      return new Intl.NumberFormat('ru-RU', { notation: 'compact', maximumFractionDigits: 1 }).format(n) + ' ₽'
    }

    const formatDate = (value) => {
      if (!value) return '—'
      return new Date(value).toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' })
    }

    const getStatusText = (status) =>
      ({ active: 'Активен', completed: 'Завершён', on_hold: 'Пауза', cancelled: 'Отменён' })[status] || status

    const getStatusClass = (status) =>
      ({ active: 'dash-chip--ok', completed: 'dash-chip--info', on_hold: 'dash-chip--warn', cancelled: 'dash-chip--danger' })[status] || 'dash-chip--muted'

    const getUrgencyDotClass = (task) => {
      if (isOverdue(task.due_date)) return 'dash-row__dot--danger'
      if (task.priority === 'urgent' || task.priority === 'high') return 'dash-row__dot--warn'
      return 'dash-row__dot--muted'
    }

    const getProjectAddress = (project) =>
      project?.address_short || project?.address || 'Нет адреса'

    const getRiskText = (level) => {
      if (level === 'high') return 'Критично'
      if (level === 'medium') return 'Нагрузка'
      return 'Норма'
    }

    const getRiskChipClass = (level) => {
      if (level === 'high') return 'dash-chip--danger'
      if (level === 'medium') return 'dash-chip--warn'
      return 'dash-chip--info'
    }

    const goToProjects = () => router.push('/projects')
    const goToTasks = () => router.push('/tasks')
    const goToContracts = () => router.push('/contracts')
    const goToCompanies = () => router.push('/companies')

    /* ---- List panels (mode-aware) ---- */
    const listPanels = computed(() => {
      if (dashboardMode.value === 'manager') {
        return [
          {
            key: 'risky',
            title: 'Сделки с риском',
            link: '/projects',
            linkLabel: 'Все сделки',
            items: riskyDeals.value,
            emptyOk: true,
            emptyIcon: 'fas fa-shield-halved',
            emptyTitle: 'Критичных рисков нет',
            emptyHint: 'Просроченные и срочные сделки появятся здесь',
            onClick: (d) => router.push(`/projects/${d.id}`),
            titleOf: (d) => d.title,
            metaOf: (d) => [
              { icon: 'fas fa-map-marker-alt', text: ' ' + (d.address || 'Без адреса') },
              { icon: 'fas fa-list-check', text: ' ' + d.open_tasks + ' задач' },
              { icon: 'fas fa-calendar-day', text: ' ' + formatDate(d.nearest_due_date) }
            ],
            chipClass: (d) => (d.risk_level === 'high' ? 'dash-chip--danger' : 'dash-chip--warn'),
            chipText: (d) => (d.risk_level === 'high' ? 'Просрочка' : 'Скоро срок'),
            valueOf: (d) => d.overdue_tasks + ' проср.'
          },
          {
            key: 'overloaded',
            title: 'Перегруженные исполнители',
            link: '/tasks',
            linkLabel: 'Все задачи',
            items: overloadedUsers.value,
            emptyOk: true,
            emptyIcon: 'fas fa-user-check',
            emptyTitle: 'Перегрузки не обнаружены',
            emptyHint: 'Сюда попадут пользователи с очередью задач',
            onClick: () => router.push('/tasks'),
            titleOf: (u) => u.full_name,
            metaOf: (u) => [
              { icon: 'fas fa-briefcase', text: ' ' + u.open_tasks + ' активных' },
              { icon: 'fas fa-triangle-exclamation', text: ' ' + u.overdue_tasks + ' просрочено' }
            ],
            chipClass: (u) => getRiskChipClass(u.risk_level),
            chipText: (u) => getRiskText(u.risk_level),
            valueOf: () => ''
          },
          {
            key: 'contracts',
            title: 'Договоры без подписи',
            link: '/contracts',
            linkLabel: 'Все договоры',
            items: contractsOnApproval.value,
            emptyOk: true,
            emptyIcon: 'fas fa-file-signature',
            emptyTitle: 'Подвисших договоров нет',
            emptyHint: 'Договоры на согласовании появятся здесь',
            onClick: (c) => router.push(`/contracts/${c.id}`),
            titleOf: (c) => c.contract_number,
            metaOf: (c) => [
              { icon: 'far fa-calendar', text: ' ' + formatDate(c.contract_date) },
              { icon: 'fas fa-folder-open', text: ' ' + (c.deal_title || 'Без сделки') }
            ],
            chipClass: (c) => (c.is_stalled ? 'dash-chip--danger' : 'dash-chip--warn'),
            chipText: (c) => c.wait_days + ' дн.',
            valueOf: (c) => formatCurrency(c.amount)
          }
        ]
      }
      return [
        {
          key: 'projects',
          title: 'Активные проекты',
          link: '/projects',
          linkLabel: 'Все',
          items: activeProjects.value,
          emptyOk: false,
          emptyIcon: 'fas fa-folder-open',
          emptyTitle: 'Нет активных проектов',
          emptyHint: 'Новые сделки появятся здесь автоматически',
          onClick: (p) => router.push(`/projects/${p.id}`),
          titleOf: (p) => p.title,
          metaOf: (p) => [{ icon: 'fas fa-map-marker-alt', text: ' ' + getProjectAddress(p) }],
          chipClass: (p) => getStatusClass(p.status),
          chipText: (p) => getStatusText(p.status),
          valueOf: (p) => formatCurrency(getProjectAmount(p))
        },
        {
          key: 'tasks',
          title: 'Срочные задачи',
          link: '/tasks',
          linkLabel: 'Все',
          items: urgentTasks.value,
          emptyOk: true,
          emptyIcon: 'fas fa-check-circle',
          emptyTitle: 'Нет срочных задач',
          emptyHint: 'Срочные и просроченные задачи появятся здесь',
          onClick: () => router.push('/tasks'),
          marker: (t) => getUrgencyDotClass(t),
          titleOf: (t) => t.title,
          metaOf: (t) => [{ icon: 'fas fa-folder', text: ' ' + (t.project_name || 'Без проекта') }],
          chipClass: (t) => (isOverdue(t.due_date) ? 'dash-chip--danger' : 'dash-chip--muted'),
          chipText: (t) => formatDate(t.due_date),
          valueOf: () => ''
        }
      ]
    })

    const quickActions = computed(() => {
      if (dashboardMode.value === 'manager') {
        return [
          { key: 'd', icon: 'fas fa-folder-open', label: 'Сделки', primary: true, onClick: goToProjects },
          { key: 't', icon: 'fas fa-check-square', label: 'Задачи', onClick: goToTasks },
          { key: 'c', icon: 'fas fa-file-signature', label: 'Договоры', onClick: goToContracts },
          { key: 'co', icon: 'fas fa-user-plus', label: 'Контрагенты', onClick: goToCompanies }
        ]
      }
      return [
        { key: 'np', icon: 'fas fa-plus', label: 'Новый проект', primary: true, onClick: goToProjects },
        { key: 'nt', icon: 'fas fa-check-square', label: 'Задача', onClick: goToTasks },
        { key: 'nc', icon: 'fas fa-user-plus', label: 'Контрагент', onClick: goToCompanies },
        { key: 'dc', icon: 'fas fa-file-signature', label: 'Договоры', onClick: goToContracts }
      ]
    })

    /* ---- Charts ---- */
    const activitySeries = computed(() => {
      const today = new Date()
      const labels = []
      const values = []
      for (let i = 13; i >= 0; i--) {
        const date = new Date(today)
        date.setDate(today.getDate() - i)
        const key = date.toISOString().slice(0, 10)
        const total = (activityData.value || [])
          .filter((item) => (item.date || '').slice(0, 10) === key)
          .reduce((sum, item) => sum + Number(item.count || 0), 0)
        labels.push(String(date.getDate()))
        values.push(total)
      }
      return { labels, values, total: values.reduce((a, b) => a + b, 0) }
    })

    const areaChartSeries = computed(() => [{ name: 'Активность', data: activitySeries.value.values }])

    const areaChartOptions = computed(() => ({
      chart: { type: 'area', toolbar: { show: false }, sparkline: { enabled: true }, fontFamily: 'inherit' },
      colors: [chartTokens.value.primary],
      stroke: { curve: 'smooth', width: 2 },
      fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.35, opacityTo: 0.02, stops: [0, 100] } },
      dataLabels: { enabled: false },
      tooltip: {
        theme: isDark.value ? 'dark' : 'light',
        x: { show: false },
        y: { formatter: (v) => `${v} событий` }
      },
      xaxis: { categories: activitySeries.value.labels }
    }))

    const donutChartSeries = computed(() => {
      const s = dealStats.value
      return [s.active, s.completed, s.on_hold, s.cancelled]
    })

    const statusDistribution = computed(() => {
      const s = dealStats.value
      const t = chartTokens.value
      const items = [
        { key: 'active', label: 'Активные', value: s.active, color: t.primary },
        { key: 'completed', label: 'Завершённые', value: s.completed, color: t.success },
        { key: 'on_hold', label: 'На паузе', value: s.on_hold, color: t.warning },
        { key: 'cancelled', label: 'Отменённые', value: s.cancelled, color: t.subtle }
      ]
      const total = s.total || 0
      return items.map((it) => ({ ...it, pct: total ? Math.round((it.value / total) * 100) : 0 }))
    })

    const donutChartOptions = computed(() => ({
      chart: { type: 'donut', toolbar: { show: false }, fontFamily: 'inherit', background: 'transparent' },
      labels: ['Активные', 'Завершённые', 'На паузе', 'Отменённые'],
      colors: [chartTokens.value.primary, chartTokens.value.success, chartTokens.value.warning, chartTokens.value.subtle],
      legend: { show: false },
      dataLabels: { enabled: false },
      stroke: { width: 0 },
      tooltip: { theme: isDark.value ? 'dark' : 'light' },
      plotOptions: {
        pie: {
          donut: {
            size: '70%',
            labels: {
              show: true,
              name: { show: true, offsetY: -8, color: chartTokens.value.muted, fontSize: '12px' },
              value: { show: true, offsetY: 12, fontSize: '22px', fontWeight: 700, color: chartTokens.value.strong },
              total: {
                show: true,
                showAlways: true,
                label: 'Всего',
                color: chartTokens.value.muted,
                fontSize: '12px',
                formatter: () => String(dealStats.value.total || 0)
              }
            }
          }
        }
      }
    }))

    const loadData = async () => {
      loading.value = true
      activityLoading.value = true
      try {
        const requests = [
          api.deals.list(),
          api.tasks.list(),
          api.home.summary(),
          api.home.activity({ days: 30 })
        ]
        if (canUseManagerMode.value) {
          requests.push(api.home.managerSummary())
        }

        const responses = await Promise.all(requests)
        const [projectData, taskResponse, summaryData, activityData_, managerData] = responses

        projects.value = projectData || []
        tasks.value = taskResponse?.data || []
        summary.value = summaryData || summary.value
        activityData.value = activityData_ || []
        managerSummary.value = canUseManagerMode.value
          ? (managerData || managerSummary.value)
          : managerSummary.value
      } catch (error) {
        console.error('Error loading dashboard data:', error)
        projects.value = []
        tasks.value = []
        activityData.value = []
        managerSummary.value = {
          enabled: false,
          active_deals: 0,
          risky_deals_count: 0,
          overdue_tasks: 0,
          unsigned_contracts_count: 0,
          stalled_contracts_count: 0,
          overloaded_users_count: 0,
          risky_deals: [],
          overloaded_users: [],
          contracts_on_approval: []
        }
      } finally {
        loading.value = false
        activityLoading.value = false
      }
    }

    let themeObserver = null
    let media = null
    const bumpTheme = () => { themeTick.value += 1 }

    onMounted(() => {
      if (canUseManagerMode.value) {
        dashboardMode.value = 'manager'
      }
      loadData()
      if (typeof window !== 'undefined') {
        themeObserver = new MutationObserver(bumpTheme)
        themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
        media = window.matchMedia('(prefers-color-scheme: dark)')
        media.addEventListener?.('change', bumpTheme)
      }
    })

    onBeforeUnmount(() => {
      themeObserver?.disconnect()
      media?.removeEventListener?.('change', bumpTheme)
    })

    return {
      loading,
      activityLoading,
      dashboardMode,
      canUseManagerMode,
      headerTitle,
      currentStatCards,
      dealStats,
      taskStats,
      taskBars,
      statusDistribution,
      activitySeries,
      areaChartSeries,
      areaChartOptions,
      donutChartSeries,
      donutChartOptions,
      listPanels,
      quickActions,
      formatCurrency,
      formatMoneyCompact,
      formatDate,
      reload: loadData,
      // dashboard customization
      dashSettingsOpen,
      dashboardBlocks,
      isDashboardBlockVisible,
      toggleDashboardBlock,
      sideModel,
    }
  }
}
</script>

<style scoped>
/* ============================================================
   Dashboard — tuned to the Tasks module visual language:
   flat surface sheets, hairline borders, tinted header bands,
   compact controls. Direction: max info density, min chrome.
   ============================================================ */
.dash {
  --apr-card-bg: rgba(255, 255, 255, 0.97);
  --apr-card-border: rgba(216, 224, 240, 0.92);
  --apr-card-shadow: 0 18px 42px rgba(15, 23, 42, 0.06);
  --apr-radius: 20px;
  --apr-ink: #0a1629;
  --apr-muted: #7d8592;
  --apr-soft: #f6f8fb;
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  padding: 12px;
}

/* ---- Topbar ---- */
.dash-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.dash-topbar__meta {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.dash-topbar__eyebrow {
  font-size: 0.68rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--apr-muted);
}

.dash-topbar__title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--apr-ink);
}

.dash-topbar__tools {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.dash-seg {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  height: 34px;
  padding: 3px;
  border: 1px solid rgba(228, 228, 228, 0.95);
  border-radius: 12px;
  background: #f3f5f8;
}

.dash-seg__btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 100%;
  padding: 0 14px;
  border: 0;
  border-radius: 9px;
  background: transparent;
  color: var(--apr-muted);
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 700;
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out), box-shadow var(--dur-fast) var(--ease-out);
}

.dash-seg__btn:hover {
  color: var(--apr-ink);
}

.dash-seg__btn--active {
  background: #fff;
  color: var(--apr-ink);
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
}

.dash-seg__btn:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

.dash-refresh {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 12px;
  border: 1px solid var(--apr-card-border);
  background: var(--apr-card-bg);
  color: var(--apr-muted);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}

.dash-refresh:hover {
  background: var(--apr-soft);
  color: var(--apr-ink);
}

.dash-refresh:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

.dash-refresh--spin {
  animation: dash-spin 0.9s linear infinite;
}

@keyframes dash-spin {
  to { transform: rotate(360deg); }
}

/* ---- Dashboard customization ---- */
.dash-cfg {
  position: relative;
  display: inline-flex;
}

.dash-refresh--active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  border-color: color-mix(in srgb, var(--color-primary) 32%, transparent);
}

.dash-cfg__pop {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 60;
  width: 240px;
  padding: 8px;
  border-radius: 12px;
  background: var(--apr-card-bg);
  border: 1px solid var(--apr-card-border);
  box-shadow: var(--shadow-lg);
}

.dash-cfg__head {
  padding: 4px 8px 6px;
  font-size: 0.72rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--apr-muted);
}

.dash-cfg__item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 8px;
  font-size: 0.82rem;
  color: var(--apr-ink);
  cursor: pointer;
}

.dash-cfg__item:hover {
  background: var(--apr-soft);
}

.dash-cfg__item input {
  cursor: pointer;
}

.dash-cfg__hint {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: 4px;
  padding: 8px;
  border-top: 1px solid var(--apr-card-border);
  font-size: 0.72rem;
  color: var(--apr-muted);
}

.dash-side-slot {
  display: flex;
  flex-direction: column;
}

.dash-drag {
  cursor: grab;
  color: var(--apr-muted);
  margin-right: 2px;
}

.dash-drag:active {
  cursor: grabbing;
}

.dash-pop-enter-active,
.dash-pop-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.dash-pop-enter-from,
.dash-pop-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.sortable-ghost {
  opacity: 0.4;
}

/* ---- Flat panel ---- */
.dash-panel {
  display: flex;
  flex-direction: column;
  background: var(--apr-card-bg);
  border: 1px solid var(--apr-card-border);
  border-radius: var(--apr-radius);
  box-shadow: var(--apr-card-shadow);
  overflow: hidden;
}

.dash-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: 9px 14px;
  background: var(--apr-soft);
  border-bottom: 1px solid var(--apr-card-border);
}

.dash-panel__title {
  margin: 0;
  font-size: 0.82rem;
  font-weight: 800;
  color: var(--apr-ink);
}

.dash-panel__title--accent {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.dash-panel__title--accent i {
  color: var(--color-warning);
  font-size: var(--text-base);
}

.dash-panel__link {
  font-size: 0.68rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--apr-muted);
  text-decoration: none;
  border-radius: var(--radius-sm);
  transition: color var(--dur-fast) var(--ease-out);
}

.dash-panel__link:hover {
  color: var(--color-primary);
}

.dash-panel__link:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

.dash-skel {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-3) 14px;
}

/* ---- Hero ---- */
.dash-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--space-4);
  padding: 16px;
  background: var(--apr-card-bg);
  border: 1px solid var(--apr-card-border);
  border-radius: var(--apr-radius);
  box-shadow: var(--apr-card-shadow);
}

.dash-hero__primary {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.dash-hero__label {
  font-size: 0.68rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--apr-muted);
}

.dash-hero__value {
  font-size: clamp(1.5rem, 2.4vw, 1.95rem);
  font-weight: 800;
  line-height: 1.15;
  color: var(--apr-ink);
}

.dash-hero__sub {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-5);
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--apr-card-border);
}

.dash-hero__stat {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.dash-hero__stat-value {
  font-size: var(--text-md);
  font-weight: 800;
  color: var(--apr-ink);
}

.dash-hero__stat-label {
  font-size: var(--text-xs);
  color: var(--apr-muted);
}

.dash-hero__chart {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: 12px;
  background: var(--apr-soft);
  border: 1px solid var(--apr-card-border);
}

.dash-hero__chart-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.dash-hero__chart-total {
  font-size: var(--text-lg);
  font-weight: var(--fw-bold);
  color: var(--color-primary);
}

.dash-hero__spark {
  min-height: 64px;
}

/* ---- KPI strip ---- */
.dash-kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: var(--space-2);
}

.dash-kpi {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 10px 12px;
  background: var(--apr-card-bg);
  border: 1px solid var(--apr-card-border);
  border-radius: 14px;
  box-shadow: var(--apr-card-shadow);
  transition: border-color var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out);
}

.dash-kpi:hover {
  background: var(--apr-soft);
}

.dash-kpi--alert {
  border-color: color-mix(in srgb, var(--color-danger) 38%, var(--color-border));
}

.dash-kpi__icon {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  font-size: var(--text-base);
  flex-shrink: 0;
}

.dash-kpi__body {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.dash-kpi__value {
  font-size: var(--text-xl);
  font-weight: 800;
  line-height: 1.1;
  color: var(--apr-ink);
}

.dash-kpi__label {
  font-size: var(--text-xs);
  color: var(--apr-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dash-kpi__badge {
  position: absolute;
  top: 7px;
  right: 8px;
  padding: 1px 7px;
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  font-weight: var(--fw-bold);
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--color-danger);
  background: var(--color-danger-soft);
}

/* ---- Main grid ---- */
.dash-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(300px, 1fr);
  gap: 12px;
  align-items: start;
}

.dash-col {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

/* ---- List rows ---- */
.dash-list {
  display: flex;
  flex-direction: column;
}

.dash-row {
  width: 100%;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-3);
  padding: 8px 14px;
  background: transparent;
  border: 0;
  border-top: 1px solid var(--apr-card-border);
  text-align: left;
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out);
}

.dash-row:first-child {
  border-top: 0;
}

.dash-row:has(.dash-row__dot) {
  grid-template-columns: 8px minmax(0, 1fr) auto;
}

.dash-row:hover {
  background: var(--apr-soft);
}

.dash-row:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

.dash-row__dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-pill);
}

.dash-row__dot--danger { background: var(--color-danger); }
.dash-row__dot--warn { background: var(--color-warning); }
.dash-row__dot--muted { background: var(--color-border-strong); }

.dash-row__main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.dash-row__title {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--apr-ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dash-row__meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  font-size: var(--text-xs);
  color: var(--color-text-subtle);
}

.dash-row__meta i {
  margin-right: 4px;
}

.dash-row__aside {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  white-space: nowrap;
}

.dash-row__value {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--apr-muted);
}

/* ---- Chips ---- */
.dash-chip {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.dash-chip--ok { color: var(--color-success); background: color-mix(in srgb, var(--color-success) 15%, transparent); }
.dash-chip--info { color: var(--color-primary); background: var(--color-primary-soft); }
.dash-chip--warn { color: var(--color-warning); background: color-mix(in srgb, var(--color-warning) 16%, transparent); }
.dash-chip--danger { color: var(--color-danger); background: var(--color-danger-soft); }
.dash-chip--muted { color: #5f6b7c; background: var(--apr-soft); }

/* ---- Empty (compact) ---- */
.dash-empty {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4) 14px;
}

.dash-empty__icon {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: var(--text-base);
  flex-shrink: 0;
}

.dash-empty__icon--ok {
  background: color-mix(in srgb, var(--color-success) 14%, transparent);
  color: var(--color-success);
}

.dash-empty__text {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.dash-empty__title {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--apr-ink);
}

.dash-empty__hint {
  font-size: var(--text-xs);
  color: var(--apr-muted);
}

/* ---- Portfolio donut ---- */
.dash-portfolio {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-3) 14px;
}

.dash-portfolio__chart {
  display: flex;
  justify-content: center;
}

.dash-legend {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.dash-legend li {
  display: grid;
  grid-template-columns: 9px 1fr auto auto;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--text-sm);
}

.dash-legend__dot {
  width: 9px;
  height: 9px;
  border-radius: var(--radius-pill);
}

.dash-legend__label { color: var(--apr-muted); font-weight: 600; }

.dash-legend__value {
  font-weight: 800;
  color: var(--apr-ink);
}

.dash-legend__pct {
  min-width: 36px;
  text-align: right;
  color: var(--apr-muted);
}

/* ---- Task bars ---- */
.dash-bars {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4) 14px;
}

.dash-bar__top {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
  font-size: var(--text-xs);
}

.dash-bar__label { color: var(--apr-muted); font-weight: 600; }

.dash-bar__value {
  font-weight: 800;
  color: var(--apr-ink);
}

.dash-bar__track {
  height: 6px;
  border-radius: var(--radius-pill);
  background: var(--apr-soft);
  overflow: hidden;
}

.dash-bar__fill {
  display: block;
  height: 100%;
  border-radius: var(--radius-pill);
  transition: width var(--dur-slow) var(--ease-out);
}

.dash-bar__fill--ok { background: var(--color-success); }
.dash-bar__fill--primary { background: var(--color-primary); }
.dash-bar__fill--danger { background: var(--color-danger); }

/* ---- Quick actions ---- */
.dash-panel--actions { flex: 1; }

.dash-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-2);
  padding: var(--space-3) 14px;
}

.dash-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  height: 36px;
  border-radius: 12px;
  border: 1px solid var(--apr-card-border);
  background: var(--apr-card-bg);
  color: var(--apr-ink);
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 700;
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}

.dash-action:hover {
  background: var(--apr-soft);
}

.dash-action:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

.dash-action--primary {
  color: var(--color-primary);
  background: var(--color-primary-soft);
  border-color: color-mix(in srgb, var(--color-primary) 32%, transparent);
}

.dash-action--primary:hover {
  background: color-mix(in srgb, var(--color-primary) 16%, transparent);
  border-color: var(--color-primary);
}

/* ---- Responsive ---- */
@media (max-width: 1180px) {
  .dash-grid {
    grid-template-columns: 1fr;
  }

  .dash-hero {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .dash-topbar__tools {
    width: 100%;
    justify-content: space-between;
  }

  .dash-seg {
    flex: 1;
  }

  .dash-seg__btn {
    flex: 1;
    justify-content: center;
  }

  .dash-row {
    grid-template-columns: 1fr;
    gap: 4px;
  }

  .dash-row:has(.dash-row__dot) {
    grid-template-columns: 1fr;
  }

  .dash-row__aside {
    gap: var(--space-3);
  }
}

@media (prefers-reduced-motion: reduce) {
  .dash-kpi,
  .dash-action,
  .dash-row,
  .dash-seg__btn,
  .dash-bar__fill,
  .dash-refresh {
    transition: none;
  }

  .dash-refresh--spin {
    animation: none;
  }
}
</style>
