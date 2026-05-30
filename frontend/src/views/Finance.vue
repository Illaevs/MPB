<template>
  <div class="finance-view p-2 h-100 d-flex flex-column">
    <div class="d-flex justify-between align-center mb-3">
      <div>
        <h2 class="m-0" style="font-size: 1.5rem; font-weight: 600;">Финансы — обзор</h2>
        <div class="text-muted small">План, факт, прогноз и контроль распределения</div>
      </div>
      <button class="btn btn-outline-primary" @click="loadOverview" :disabled="loading">
        <i class="fas fa-sync"></i>
      </button>
    </div>

    <div class="card p-2 mb-3 finance-filters-card">
      <div class="d-flex flex-wrap gap-2 align-center">
        <div class="btn-group period-toggle">
          <button class="btn btn-sm" :class="period === 'month' ? 'btn-primary' : 'btn-outline-primary'" @click="setPeriod('month')">Месяц</button>
          <button class="btn btn-sm" :class="period === 'quarter' ? 'btn-primary' : 'btn-outline-primary'" @click="setPeriod('quarter')">Квартал</button>
          <button class="btn btn-sm" :class="period === 'year' ? 'btn-primary' : 'btn-outline-primary'" @click="setPeriod('year')">Год</button>
          <button class="btn btn-sm" :class="period === 'all' ? 'btn-primary' : 'btn-outline-primary'" @click="setPeriod('all')">Всё</button>
        </div>
        <div class="d-flex align-center gap-2">
          <input v-model="startDate" type="date" class="form-control form-control-sm" style="max-width: 160px;">
          <span class="text-muted small">—</span>
          <input v-model="endDate" type="date" class="form-control form-control-sm" style="max-width: 160px;">
          <button class="btn btn-sm btn-outline-primary" @click="applyCustom">Применить</button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="d-flex justify-center align-center py-5">
      <div class="spinner"></div>
    </div>

    <template v-else>
      <div class="d-flex flex-wrap gap-3 mb-4">
        <div class="card p-3 flex-grow-1 stat-card">
          <div class="text-muted small">План (доход/расход)</div>
          <div class="d-flex justify-between align-center mt-2">
            <div class="text-success fw-600">{{ formatCurrency(kpis.plan_income) }}</div>
            <div class="text-danger fw-600">{{ formatCurrency(kpis.plan_expense) }}</div>
          </div>
          <div class="mt-1 text-muted small">Сальдо: <span :class="netClass(kpis.net_plan)">{{ formatCurrency(kpis.net_plan) }}</span></div>
        </div>
        <div class="card p-3 flex-grow-1 stat-card">
          <div class="text-muted small">Факт (доход/расход)</div>
          <div class="d-flex justify-between align-center mt-2">
            <div class="text-success fw-600">{{ formatCurrency(kpis.actual_income) }}</div>
            <div class="text-danger fw-600">{{ formatCurrency(kpis.actual_expense) }}</div>
          </div>
          <div class="mt-1 text-muted small">Сальдо: <span :class="netClass(kpis.net_actual)">{{ formatCurrency(kpis.net_actual) }}</span></div>
        </div>
        <div class="card p-3 flex-grow-1 stat-card">
          <div class="text-muted small">Прогноз (доход/расход)</div>
          <div class="d-flex justify-between align-center mt-2">
            <div class="text-success fw-600">{{ formatCurrency(kpis.forecast_income) }}</div>
            <div class="text-danger fw-600">{{ formatCurrency(kpis.forecast_expense) }}</div>
          </div>
          <div class="mt-1 text-muted small">Сальдо: <span :class="netClass(kpis.net_forecast)">{{ formatCurrency(kpis.net_forecast) }}</span></div>
        </div>
        <div class="card p-3 flex-grow-1 stat-card">
          <div class="text-muted small">Автораспределение</div>
          <div class="fw-600 mt-2">{{ rulesCoverage.percent.toFixed(1) }}%</div>
          <div class="text-muted small">{{ rulesCoverage.auto }} из {{ rulesCoverage.total }}</div>
        </div>
      </div>

      <div class="row mb-4">
        <div class="col-md-8 mb-3">
          <div class="card p-3 h-100">
            <div class="d-flex justify-between align-center mb-2">
              <h4 class="m-0">План / факт / прогноз (накопительно)</h4>
              <div class="btn-group btn-group-sm">
                <button class="btn" :class="cashflowMode === 'combined' ? 'btn-primary' : 'btn-outline-primary'" @click="cashflowMode = 'combined'">Совмещ.</button>
                <button class="btn" :class="cashflowMode === 'income' ? 'btn-primary' : 'btn-outline-primary'" @click="cashflowMode = 'income'">Доход</button>
                <button class="btn" :class="cashflowMode === 'expense' ? 'btn-primary' : 'btn-outline-primary'" @click="cashflowMode = 'expense'">Расход</button>
              </div>
            </div>
            <apexchart type="area" height="320" :options="cashflowOptions" :series="cashflowSeries"></apexchart>
          </div>
        </div>
        <div class="col-md-4 mb-3">
          <div class="card p-3 h-100">
            <h4 class="m-0 mb-3">Статус казначейства</h4>
            <apexchart type="donut" height="280" :options="treasuryOptions" :series="treasurySeries"></apexchart>
            <div class="mt-2 small">
              <div class="d-flex justify-between"><span>Распределено</span><span>{{ treasury.allocated.count }}</span></div>
              <div class="d-flex justify-between"><span>Не распределено</span><span>{{ treasury.unallocated.count }}</span></div>
              <div class="d-flex justify-between"><span>Не учитывать</span><span>{{ treasury.ignored.count }}</span></div>
            </div>
          </div>
        </div>
      </div>

      <div class="row mb-4">
        <div class="col-md-12">
          <div class="card p-3">
            <div class="d-flex justify-between align-center mb-2">
              <h4 class="m-0">Кумуляция доходов и расходов</h4>
              <div class="btn-group btn-group-sm">
                <button class="btn" :class="incomeExpenseMode === 'combined' ? 'btn-primary' : 'btn-outline-primary'" @click="incomeExpenseMode = 'combined'">Совмещ.</button>
                <button class="btn" :class="incomeExpenseMode === 'fact' ? 'btn-primary' : 'btn-outline-primary'" @click="incomeExpenseMode = 'fact'">Факт</button>
                <button class="btn" :class="incomeExpenseMode === 'forecast' ? 'btn-primary' : 'btn-outline-primary'" @click="incomeExpenseMode = 'forecast'">Прогноз</button>
              </div>
            </div>
            <apexchart type="line" height="280" :options="incomeExpenseCumOptions" :series="incomeExpenseCumSeries"></apexchart>
          </div>
        </div>
      </div>

      <div class="row mb-4">
        <div class="col-md-7 mb-3">
          <div class="card p-3 h-100">
            <div class="d-flex justify-between align-center mb-2">
              <h4 class="m-0">Бюджет по категориям</h4>
              <select v-model="budgetDirection" class="form-select form-select-sm" style="max-width: 160px;">
                <option value="expense">Расходы</option>
                <option value="income">Доходы</option>
              </select>
            </div>
            <apexchart type="bar" height="320" :options="budgetOptions" :series="budgetSeries"></apexchart>
          </div>
        </div>
        <div class="col-md-5 mb-3">
          <div class="card p-3 h-100">
            <h4 class="m-0 mb-2">Просрочка распределения</h4>
            <div class="table-container" style="max-height: 320px;">
              <table class="table table-sm">
                <thead>
                  <tr>
                    <th>Интервал</th>
                    <th class="text-right">Кол-во</th>
                    <th class="text-right">Сумма</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="bucket in treasury.aging" :key="bucket.label">
                    <td>{{ bucket.label }} дн.</td>
                    <td class="text-right">{{ bucket.count }}</td>
                    <td class="text-right">{{ formatCurrency(bucket.amount) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <div class="row mb-4">
        <div class="col-md-12">
          <div class="card p-3">
            <div class="d-flex justify-between align-center mb-2">
              <h4 class="m-0">Расшифровка по месяцам</h4>
            </div>
            <div class="table-container cashflow-scroll" style="max-height: 360px;">
              <table class="table table-sm cashflow-table">
                <thead>
                  <tr>
                    <th>Период</th>
                    <th class="text-right">План +</th>
                    <th class="text-right">План -</th>
                    <th class="text-right">Факт +</th>
                    <th class="text-right">Факт -</th>
                    <th class="text-right">Прогноз +</th>
                    <th class="text-right">Прогноз -</th>
                    <th class="text-right">Сальдо</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in cashflowRows" :key="row.label">
                    <td>{{ row.label }}</td>
                    <td class="text-right text-success">{{ formatCurrency(row.plan_income) }}</td>
                    <td class="text-right text-danger">{{ formatCurrency(row.plan_expense) }}</td>
                    <td class="text-right text-success">{{ formatCurrency(row.actual_income) }}</td>
                    <td class="text-right text-danger">{{ formatCurrency(row.actual_expense) }}</td>
                    <td class="text-right text-success">{{ formatCurrency(row.forecast_income) }}</td>
                    <td class="text-right text-danger">{{ formatCurrency(row.forecast_expense) }}</td>
                    <td class="text-right" :class="netClass(row.net)">{{ formatCurrency(row.net) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <div class="row">
        <div class="col-md-12">
          <div class="card p-3">
            <div class="d-flex justify-between align-center mb-2">
              <h4 class="m-0">Прогноз кассового разрыва (по ДДС)</h4>
              <div class="text-muted small">Минимум: {{ formatCurrency(cashGap.min_balance) }} на {{ formatDate(cashGap.min_date) }}</div>
            </div>
            <apexchart type="line" height="280" :options="cashGapOptions" :series="cashGapSeries"></apexchart>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/services/api'
import VueApexCharts from 'vue3-apexcharts'

export default {
  name: 'Finance',
  components: { apexchart: VueApexCharts },
  setup() {
    const period = ref('year')
    const startDate = ref('')
    const endDate = ref('')
    const loading = ref(false)
    const overview = ref(null)
    const budgetDirection = ref('expense')
    const cashflowMode = ref('combined')
    const incomeExpenseMode = ref('combined')

    const setPeriod = (value) => {
      period.value = value
      const range = calcRange(value)
      startDate.value = range.start
      endDate.value = range.end
      loadOverview()
    }

    const applyCustom = () => {
      period.value = 'custom'
      loadOverview()
    }

    const calcRange = (value) => {
      const today = new Date()
      if (value === 'month') {
        const start = new Date(today.getFullYear(), today.getMonth(), 1)
        const end = new Date(today.getFullYear(), today.getMonth() + 1, 0)
        return { start: toIso(start), end: toIso(end) }
      }
      if (value === 'quarter') {
        const quarter = Math.floor(today.getMonth() / 3)
        const start = new Date(today.getFullYear(), quarter * 3, 1)
        const end = new Date(today.getFullYear(), quarter * 3 + 3, 0)
        return { start: toIso(start), end: toIso(end) }
      }
      if (value === 'year') {
        const start = new Date(today.getFullYear(), 0, 1)
        const end = new Date(today.getFullYear(), 11, 31)
        return { start: toIso(start), end: toIso(end) }
      }
      return { start: '', end: '' }
    }

    const toIso = (value) => value.toISOString().slice(0, 10)

    const loadOverview = async () => {
      loading.value = true
      try {
        const response = await api.finance.overview({
          period: period.value === 'custom' ? undefined : period.value,
          start_date: startDate.value || undefined,
          end_date: endDate.value || undefined
        })
        overview.value = response || null
      } catch (error) {
        console.error('Error loading finance overview', error)
      } finally {
        loading.value = false
      }
    }

    const kpis = computed(() => overview.value?.kpis || {
      plan_income: 0,
      plan_expense: 0,
      actual_income: 0,
      actual_expense: 0,
      forecast_income: 0,
      forecast_expense: 0,
      net_plan: 0,
      net_actual: 0,
      net_forecast: 0
    })

    const treasury = computed(() => overview.value?.treasury_status || {
      allocated: { count: 0, amount: 0 },
      unallocated: { count: 0, amount: 0 },
      ignored: { count: 0, amount: 0 },
      aging: []
    })

    const rulesCoverage = computed(() => overview.value?.rules_coverage || { total: 0, auto: 0, percent: 0 })

    const cashflowSeries = computed(() => {
      const data = overview.value?.cashflow
      if (!data) return []
      if (cashflowMode.value === 'income') {
        return [
          { name: 'План доход', data: data.plan_income || [] },
          { name: 'Факт доход', data: data.actual_income || [] },
          { name: 'Прогноз доход', data: data.forecast_income || [] }
        ]
      }
      if (cashflowMode.value === 'expense') {
        return [
          { name: 'План расход', data: data.plan_expense || [] },
          { name: 'Факт расход', data: data.actual_expense || [] },
          { name: 'Прогноз расход', data: data.forecast_expense || [] }
        ]
      }
      const toCumulative = (values) => {
        const result = []
        let running = 0
        for (const value of values) {
          running += Number(value || 0)
          result.push(running)
        }
        return result
      }
      const planNet = (data.plan_income || []).map((val, idx) => Number(val || 0) - Number(data.plan_expense?.[idx] || 0))
      const actualNet = (data.actual_income || []).map((val, idx) => Number(val || 0) - Number(data.actual_expense?.[idx] || 0))
      const forecastNet = (data.forecast_income || []).map((val, idx) => Number(val || 0) - Number(data.forecast_expense?.[idx] || 0))
      return [
        { name: 'Кум. план', data: toCumulative(planNet) },
        { name: 'Кум. факт', data: toCumulative(actualNet) },
        { name: 'Кум. прогноз', data: toCumulative(forecastNet) }
      ]
    })

    const cashflowOptions = computed(() => ({
      chart: { type: 'area', height: 320, toolbar: { show: false } },
      dataLabels: { enabled: false },
      stroke: { curve: 'smooth', width: 2 },
      xaxis: { type: 'datetime', categories: overview.value?.cashflow?.labels || [] },
      tooltip: { x: { format: 'MMM yyyy' }, y: { formatter: (val) => formatCurrency(val) } },
      yaxis: { labels: { formatter: (val) => formatShortNumber(val) } },
      colors: ['#2ecc71', '#3498db', '#f39c12'],
      fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.6, opacityTo: 0.9, stops: [0, 90, 100] } }
    }))

    const budgetSeries = computed(() => {
      const items = overview.value?.budget_by_category?.[budgetDirection.value] || []
      return [
        { name: 'План', data: items.map((item) => item.plan || 0) },
        { name: 'Факт', data: items.map((item) => item.actual || 0) }
      ]
    })

    const budgetOptions = computed(() => {
      const items = overview.value?.budget_by_category?.[budgetDirection.value] || []
      return {
        chart: { type: 'bar', height: 320, toolbar: { show: false } },
        plotOptions: { bar: { horizontal: true, barHeight: '60%' } },
        dataLabels: { enabled: false },
        xaxis: { categories: items.map((item) => item.category), labels: { formatter: (val) => formatShortNumber(val) } },
        tooltip: { y: { formatter: (val) => formatCurrency(val) } },
        colors: ['#6c5ce7', '#00b894'],
        legend: { position: 'top' }
      }
    })

    const treasurySeries = computed(() => [
      treasury.value.allocated.amount || 0,
      treasury.value.unallocated.amount || 0,
      treasury.value.ignored.amount || 0
    ])

    const treasuryOptions = computed(() => ({
      labels: ['Распределено', 'Не распределено', 'Не учитывать'],
      chart: { type: 'donut' },
      legend: { position: 'bottom' },
      colors: ['#2ecc71', '#e67e22', '#95a5a6'],
      dataLabels: { enabled: true }
    }))

    const cashGap = computed(() => overview.value?.cash_gap || { labels: [], balance: [], min_balance: 0, min_date: null })

    const cashGapSeries = computed(() => [{ name: 'Кассовый разрыв', data: cashGap.value.balance || [] }])

    const cashGapOptions = computed(() => ({
      chart: { type: 'line', height: 280, toolbar: { show: false } },
      stroke: { curve: 'smooth', width: 2 },
      xaxis: { type: 'datetime', categories: cashGap.value.labels || [] },
      tooltip: { x: { format: 'MMM yyyy' }, y: { formatter: (val) => formatCurrency(val) } },
      yaxis: { labels: { formatter: (val) => formatShortNumber(val) } },
      colors: ['#9b59b6'],
      dataLabels: { enabled: false }
    }))

    const incomeExpenseCumSeries = computed(() => {
      const data = overview.value?.cashflow
      if (!data) return []
      const toCumulative = (values) => {
        const result = []
        let running = 0
        for (const value of values) {
          running += Number(value || 0)
          result.push(running)
        }
        return result
      }
      if (incomeExpenseMode.value === 'fact') {
        return [
          { name: 'Кум. доход (факт)', data: toCumulative(data.actual_income || []) },
          { name: 'Кум. расход (факт)', data: toCumulative(data.actual_expense || []) }
        ]
      }
      if (incomeExpenseMode.value === 'forecast') {
        return [
          { name: 'Кум. доход (прогноз)', data: toCumulative(data.forecast_income || []) },
          { name: 'Кум. расход (прогноз)', data: toCumulative(data.forecast_expense || []) }
        ]
      }
      return [
        { name: 'Кум. доход (факт)', data: toCumulative(data.actual_income || []) },
        { name: 'Кум. расход (факт)', data: toCumulative(data.actual_expense || []) },
        { name: 'Кум. доход (прогноз)', data: toCumulative(data.forecast_income || []) },
        { name: 'Кум. расход (прогноз)', data: toCumulative(data.forecast_expense || []) }
      ]
    })

    const incomeExpenseCumOptions = computed(() => ({
      chart: { type: 'line', height: 280, toolbar: { show: false } },
      stroke: { curve: 'smooth', width: 2 },
      xaxis: { type: 'datetime', categories: overview.value?.cashflow?.labels || [] },
      tooltip: { x: { format: 'MMM yyyy' }, y: { formatter: (val) => formatCurrency(val) } },
      yaxis: { labels: { formatter: (val) => formatShortNumber(val) } },
      colors: ['#2ecc71', '#e74c3c', '#7bed9f', '#ff9f43'],
      dataLabels: { enabled: false }
    }))

    const cashflowRows = computed(() => {
      const data = overview.value?.cashflow
      if (!data) return []
      const labels = data.labels || []
      return labels.map((label, idx) => {
        const planIncome = data.plan_income?.[idx] || 0
        const planExpense = data.plan_expense?.[idx] || 0
        const actualIncome = data.actual_income?.[idx] || 0
        const actualExpense = data.actual_expense?.[idx] || 0
        const forecastIncome = data.forecast_income?.[idx] || 0
        const forecastExpense = data.forecast_expense?.[idx] || 0
        return {
          label: formatMonthLabel(label),
          plan_income: planIncome,
          plan_expense: planExpense,
          actual_income: actualIncome,
          actual_expense: actualExpense,
          forecast_income: forecastIncome,
          forecast_expense: forecastExpense,
          net: (actualIncome - actualExpense) + (forecastIncome - forecastExpense)
        }
      })
    })

    const formatCurrency = (value) => {
      const amount = Math.round(Number(value || 0))
      return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(amount)
    }

    const formatShortNumber = (value) => {
      const amount = Math.round(Number(value || 0))
      return new Intl.NumberFormat('ru-RU').format(amount)
    }

    const formatMonthLabel = (value) => {
      if (!value) return '-'
      const date = new Date(value)
      return date.toLocaleDateString('ru-RU', { month: 'short', year: 'numeric' })
    }

    const formatDate = (value) => {
      if (!value) return '-'
      return new Date(value).toLocaleDateString('ru-RU')
    }

    const netClass = (value) => (Number(value || 0) >= 0 ? 'text-success' : 'text-danger')

    onMounted(async () => {
      const range = calcRange(period.value)
      startDate.value = range.start
      endDate.value = range.end
      await loadOverview()
    })

    return {
      period,
      startDate,
      endDate,
      loading,
      overview,
      budgetDirection,
      cashflowMode,
      incomeExpenseMode,
      setPeriod,
      applyCustom,
      loadOverview,
      kpis,
      treasury,
      rulesCoverage,
      cashflowSeries,
      cashflowOptions,
      cashflowRows,
      budgetSeries,
      budgetOptions,
      treasurySeries,
      treasuryOptions,
      cashGap,
      cashGapSeries,
      cashGapOptions,
      incomeExpenseCumSeries,
      incomeExpenseCumOptions,
      formatCurrency,
      formatShortNumber,
      formatDate,
      formatMonthLabel,
      netClass
    }
  }
}
</script>

<style scoped>
/* ── Tasks reference standard: white card chrome, soft shadow, light
   border, soft-tint bands, segmented toggles, compact 12px rhythm. ── */
.finance-view {
  --apr-card-bg: rgba(255, 255, 255, 0.97);
  --apr-card-border: rgba(216, 224, 240, 0.92);
  --apr-card-shadow: 0 18px 42px rgba(15, 23, 42, 0.06);
  --apr-radius: 20px;
  --apr-ink: #0a1629;
  --apr-muted: #7d8592;
  --apr-soft: #f6f8fb;
  padding: 12px !important;
}

/* Header row */
.finance-view > .d-flex:first-child { margin-bottom: 12px !important; }
.finance-view h2 {
  font-size: 1.15rem !important;
  font-weight: 800 !important;
  color: var(--apr-ink);
}
.finance-view .text-muted { color: var(--apr-muted) !important; }

/* Panels — unified Tasks card chrome */
.finance-view .card {
  background: var(--apr-card-bg);
  border: 1px solid var(--apr-card-border);
  border-radius: var(--apr-radius);
  box-shadow: var(--apr-card-shadow);
  padding: 14px;
  margin-bottom: 12px;
}
.finance-view .card:hover { box-shadow: var(--apr-card-shadow); }
.finance-view .row { margin-bottom: 0 !important; }
.finance-view .mb-3,
.finance-view .mb-4 { margin-bottom: 12px !important; }

.finance-view h4 {
  font-size: 0.95rem;
  font-weight: 800;
  color: var(--apr-ink);
}

/* KPI stat cards */
.stat-card { min-width: 180px; }
.finance-view .stat-card { padding: 12px 14px; }
.finance-view .stat-card .text-muted.small {
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

/* Filters card → soft-tint band */
.finance-view .finance-filters-card {
  overflow: visible;
  background: var(--apr-soft);
  box-shadow: none;
  padding: 8px 12px;
}
.finance-view .finance-filters-card .btn-group {
  overflow: visible;
}

/* Segmented toggles (period + chart modes) — Tasks segment look */
.finance-view .btn-group {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 3px;
  background: #f3f5f8;
  border: 1px solid rgba(228, 228, 228, 0.95);
  border-radius: 12px;
}
.finance-view .btn-group .btn {
  border: 0 !important;
  border-radius: 9px !important;
  background: transparent !important;
  color: var(--apr-muted) !important;
  font-weight: 700;
  box-shadow: none !important;
}
.finance-view .btn-group .btn:hover { color: var(--apr-ink) !important; }
.finance-view .btn-group .btn.btn-primary {
  background: #fff !important;
  color: var(--apr-ink) !important;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08) !important;
}
.period-toggle {
  flex-wrap: nowrap;
  width: 100%;
  max-width: 520px;
}
.period-toggle .btn {
  flex: 1 1 0;
  min-width: 110px;
  white-space: nowrap;
}

/* Tables — compact, soft-tint header, hairline rows */
.finance-view .table { font-size: 0.82rem; }
.finance-view .table thead th {
  background: var(--apr-soft);
  color: var(--apr-muted);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  border-bottom: 1px solid var(--apr-card-border);
}
.finance-view .table td,
.finance-view .table th { border-color: var(--apr-card-border); }

.text-right { text-align: right; }
.text-success { color: #28cd41; }
.text-danger { color: #ff3b30; }
.fw-600 { font-weight: 600; }

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--md-sys-color-outline-variant);
  border-top-color: var(--md-sys-color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .finance-view h2 {
    font-size: 1.25rem !important;
  }

  .finance-view > .d-flex:first-child {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .stat-card {
    min-width: 100%;
  }
  .period-toggle {
    width: 100%;
    max-width: none;
    flex-wrap: wrap;
  }
  .period-toggle .btn {
    flex: 1 1 45%;
    min-width: 120px;
  }
}

/* Таблица «Расшифровка по месяцам» (8 числовых колонок) на мобиле:
   горизонтальный скролл + залипшая первая колонка (Период), чтобы при
   прокрутке чисел не терять, к какому месяцу они относятся. */
@media (max-width: 768px) {
  .cashflow-scroll { overflow-x: auto; }
  .cashflow-table { min-width: 620px; }
  .cashflow-table thead th:first-child,
  .cashflow-table tbody td:first-child {
    position: sticky;
    left: 0;
    z-index: 1;
    background: var(--color-surface);
  }
}
</style>

