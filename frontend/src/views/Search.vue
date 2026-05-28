<template>
  <div class="search-page">
    <div class="search-header">
      <h1>Поиск</h1>
      <div class="search-input-wrap">
        <i class="fas fa-search search-icon" :class="{ 'fa-spin': isSearching }"></i>
        <input
          ref="searchInput"
          v-model="queryInput"
          type="text"
          class="search-input"
          placeholder="КП «бетон М300», договор номер, заказчик по части названия…"
          @input="onInput"
          @keydown.enter="runSearch"
        />
        <span v-if="queryInput" class="search-clear" @click="clearQuery">×</span>
      </div>

      <!-- Фильтры типов -->
      <div class="type-filters">
        <span
          v-for="t in TYPE_OPTIONS"
          :key="t.value"
          class="type-chip"
          :class="{ active: selectedTypes.includes(t.value) }"
          @click="toggleType(t.value)"
        >
          <i :class="t.icon"></i>
          {{ t.label }}
        </span>
        <span v-if="selectedTypes.length" class="type-chip type-chip-reset" @click="selectedTypes = []">
          Сбросить
        </span>
      </div>
    </div>

    <div v-if="!hasResults && !isSearching && queryInput.length >= 2" class="search-empty">
      <i class="fas fa-search-minus"></i>
      <p>Ничего не нашлось по запросу «{{ queryInput }}»</p>
      <small>Попробуйте по части слова, без падежей или с другим термином</small>
    </div>

    <div v-if="!queryInput || queryInput.length < 2" class="search-hint">
      <i class="fas fa-keyboard"></i>
      <p>Введите минимум 2 символа</p>
      <small>Ищем по проектам, договорам, лидам, контрагентам, задачам, документам, КП и сообщениям задач.</small>
    </div>

    <div v-if="hasResults" class="search-results">
      <div v-for="hit in results" :key="`${hit.entity_type}_${hit.entity_id}`" class="result-row" @click="openHit(hit)">
        <div class="result-icon">
          <i :class="iconFor(hit.entity_type)"></i>
        </div>
        <div class="result-body">
          <div class="result-title">{{ stripMarks(hit.title) || '(без названия)' }}</div>
          <!-- snippet содержит <mark>...</mark> — рендерим через v-html. -->
          <div class="result-snippet" v-html="hit.snippet || ''"></div>
        </div>
        <div class="result-type">
          {{ typeLabel(hit.entity_type) }}
        </div>
      </div>

      <div v-if="results.length >= limit" class="search-more">
        <button class="btn-more" :disabled="loadingMore" @click="loadMore">
          {{ loadingMore ? 'Загружаем…' : 'Показать ещё' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../services/api'

const TYPE_OPTIONS = [
  { value: 'deal', label: 'Проекты', icon: 'fas fa-project-diagram' },
  { value: 'contract', label: 'Договоры', icon: 'fas fa-file-contract' },
  { value: 'lead', label: 'Лиды', icon: 'fas fa-bullseye' },
  { value: 'company', label: 'Контрагенты', icon: 'fas fa-building' },
  { value: 'task', label: 'Задачи', icon: 'fas fa-tasks' },
  { value: 'document', label: 'Документы', icon: 'fas fa-folder-open' },
  { value: 'outgoing_document', label: 'Исходящие', icon: 'fas fa-paper-plane' },
  { value: 'kp_document', label: 'КП', icon: 'fas fa-file-invoice-dollar' },
  { value: 'mail_message', label: 'Письма', icon: 'fas fa-envelope' },
  { value: 'legal_case', label: 'Юр.дела', icon: 'fas fa-balance-scale' },
  { value: 'task_message', label: 'Сообщения задач', icon: 'fas fa-comment' },
  { value: 'task_subtask', label: 'Чек-лист', icon: 'fas fa-check-square' },
  { value: 'subcontractor_card', label: 'Субподрядчики', icon: 'fas fa-hammer' },
]

const ENTITY_ROUTES = {
  deal: (id) => `/projects/${id}`,
  contract: () => `/contracts`,
  lead: (id) => `/leads/${id}`,
  company: () => `/companies`,
  task: (id) => `/tasks?task_id=${id}`,
  document: () => `/document-registry`,
  outgoing_document: () => `/outgoing-registry`,
  kp_document: () => `/leads`,
  mail_message: () => `/mail`,
  legal_case: () => `/legal-work`,
  support_ticket: () => `/support`,
  // Дочерние сущности — открываем родительскую задачу через parent_id.
  task_message: (id, parent_id) => parent_id ? `/tasks?task_id=${parent_id}` : `/tasks`,
  task_subtask: (id, parent_id) => parent_id ? `/tasks?task_id=${parent_id}` : `/tasks`,
  subcontractor_card: () => `/subcontractors`,
}

const stripMarksFn = (s) => (s || '').replace(/<\/?mark>/g, '')

export default {
  name: 'Search',
  setup() {
    const route = useRoute()
    const router = useRouter()

    const queryInput = ref(route.query.q || '')
    const selectedTypes = ref([])
    const results = ref([])
    const isSearching = ref(false)
    const loadingMore = ref(false)
    const offset = ref(0)
    const limit = ref(30)
    const searchInput = ref(null)

    let debounceTimer = null

    const hasResults = computed(() => results.value.length > 0)

    const stripMarks = stripMarksFn

    const iconFor = (entity_type) => {
      const t = TYPE_OPTIONS.find((o) => o.value === entity_type)
      return t ? t.icon : 'fas fa-question'
    }
    const typeLabel = (entity_type) => {
      const t = TYPE_OPTIONS.find((o) => o.value === entity_type)
      return t ? t.label.replace(/ы$/, '') : entity_type
    }

    const runSearch = async (reset = true) => {
      if (!queryInput.value || queryInput.value.length < 2) {
        results.value = []
        return
      }
      if (reset) {
        offset.value = 0
        results.value = []
      }
      isSearching.value = true
      try {
        const resp = await api.search.search({
          query: queryInput.value,
          entity_types: selectedTypes.value.length ? selectedTypes.value : null,
          limit: limit.value,
          offset: offset.value,
        })
        const items = (resp && resp.items) || []
        if (reset) {
          results.value = items
        } else {
          results.value = [...results.value, ...items]
        }
        // Обновляем URL ?q=...
        router.replace({ path: '/search', query: { q: queryInput.value } })
      } catch (e) {
        console.error('search error', e)
      } finally {
        isSearching.value = false
        loadingMore.value = false
      }
    }

    const onInput = () => {
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => runSearch(true), 300)
    }

    const clearQuery = () => {
      queryInput.value = ''
      results.value = []
      router.replace({ path: '/search', query: {} })
    }

    const toggleType = (value) => {
      const idx = selectedTypes.value.indexOf(value)
      if (idx >= 0) selectedTypes.value.splice(idx, 1)
      else selectedTypes.value.push(value)
      runSearch(true)
    }

    const openHit = (hit) => {
      const routeFn = ENTITY_ROUTES[hit.entity_type]
      if (routeFn) router.push(routeFn(hit.entity_id, hit.parent_id))
    }

    const loadMore = () => {
      loadingMore.value = true
      offset.value += limit.value
      runSearch(false)
    }

    onMounted(() => {
      if (queryInput.value) runSearch(true)
      // autofocus
      setTimeout(() => searchInput.value?.focus(), 50)
    })

    return {
      queryInput, selectedTypes, results, isSearching, loadingMore,
      limit, hasResults, TYPE_OPTIONS, searchInput,
      runSearch, onInput, clearQuery, toggleType, openHit, loadMore,
      stripMarks, iconFor, typeLabel,
    }
  },
}
</script>

<style scoped>
.search-page {
  padding: 24px 28px;
  max-width: 980px;
  margin: 0 auto;
}
.search-header h1 {
  font-size: 22px;
  font-weight: 600;
  margin: 0 0 16px 0;
  color: var(--color-text);
}
.search-input-wrap {
  position: relative;
  margin-bottom: 16px;
}
.search-input {
  width: 100%;
  padding: 14px 44px 14px 44px;
  border-radius: 12px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: 15px;
  outline: none;
  transition: border-color .15s;
}
.search-input:focus {
  border-color: var(--color-primary);
}
.search-icon {
  position: absolute;
  left: 16px; top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-muted);
}
.search-clear {
  position: absolute;
  right: 16px; top: 50%;
  transform: translateY(-50%);
  font-size: 22px;
  color: var(--color-text-muted);
  cursor: pointer;
}
.type-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 24px;
}
.type-chip {
  padding: 6px 12px;
  border-radius: 20px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  font-size: 13px;
  cursor: pointer;
  user-select: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--color-text);
  transition: background-color .15s, border-color .15s;
}
.type-chip:hover {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
}
.type-chip.active {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}
.type-chip-reset {
  background: transparent;
  color: var(--color-text-muted);
  border-style: dashed;
}
.search-results {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.result-row {
  display: grid;
  grid-template-columns: 40px 1fr auto;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 10px;
  background: var(--color-surface);
  border: 1px solid transparent;
  cursor: pointer;
  transition: background-color .15s, border-color .15s;
}
.result-row:hover {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
}
.result-icon {
  width: 40px; height: 40px;
  border-radius: 8px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}
.result-body {
  min-width: 0;
}
.result-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.result-snippet {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 2px;
  line-height: 1.4;
  max-height: 38px;
  overflow: hidden;
}
.result-snippet :deep(mark) {
  background: var(--color-warning, #fde68a);
  color: inherit;
  padding: 0 2px;
  border-radius: 2px;
}
.result-type {
  font-size: 11px;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
}
.search-empty, .search-hint {
  text-align: center;
  padding: 60px 20px;
  color: var(--color-text-muted);
}
.search-empty i, .search-hint i {
  font-size: 36px;
  display: block;
  margin-bottom: 12px;
}
.search-empty p, .search-hint p {
  font-size: 16px;
  margin: 0 0 6px 0;
}
.search-empty small, .search-hint small {
  font-size: 13px;
}
.search-more {
  text-align: center;
  margin-top: 16px;
}
.btn-more {
  padding: 8px 24px;
  border-radius: 8px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-text);
  cursor: pointer;
}
.btn-more:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
