<template>
  <div class="reglaments-page">
    <!-- Toolbar card (header + searchbar + filters в одной list-card обёртке) -->
    <div class="reglaments-page__toolbar">
      <div class="reglaments-page__header">
        <div>
          <h2 class="reglaments-page__title">Нормативная база</h2>
          <div class="text-muted small">
            СНиП / ГОСТ / СП / ФЗ / ПП — строительная нормативка для генпроектирования
          </div>
        </div>
        <div class="reglaments-page__actions">
          <span class="text-muted small">
            {{ totalCount }} норм · {{ withContentCount }} с полным текстом
          </span>
          <button
            v-if="auth.isSuperuser"
            class="reglaments-btn reglaments-btn--primary"
            @click="openCreateModal"
            title="Создать новую норму"
          >
            <i class="fa fa-plus"></i> Новая норма
          </button>
        </div>
      </div>

      <div class="reglaments-page__searchbar">
        <div class="reglaments-search-input">
          <i class="fa fa-search reglaments-search-input__icon"></i>
          <input
            ref="searchInputRef"
            v-model="query"
            type="text"
            class="form-control"
            placeholder="Поиск по нормам: «огнестойкость колонн», «защитный слой бетона», «СП 63»…"
            @keydown.esc="onResetSearch"
          />
          <button
            v-if="query"
            class="reglaments-search-input__clear"
            @click="onResetSearch"
            title="Очистить"
          >×</button>
        </div>
        <div v-if="searching" class="text-muted small ml-2">Ищу…</div>
        <div v-else-if="searchMode" class="text-muted small ml-2">
          режим: <strong>{{ searchMode === 'hybrid' ? 'смысловой' : 'полнотекстовый' }}</strong>
        </div>
      </div>

      <div class="reglaments-page__filters">
        <div class="reglaments-chip-group">
          <span class="reglaments-chip-group__label">Тип:</span>
          <button
            v-for="t in DOC_TYPES"
            :key="t.value"
            class="reglaments-chip"
            :class="{ 'reglaments-chip--active': activeDocTypes.includes(t.value) }"
            @click="toggleDocType(t.value)"
          >{{ t.label }}</button>
        </div>
        <div class="reglaments-chip-group">
          <span class="reglaments-chip-group__label">Дисциплина:</span>
          <button
            v-for="d in DISCIPLINES"
            :key="d.value"
            class="reglaments-chip reglaments-chip--discipline"
            :class="{ 'reglaments-chip--active': activeDisciplines.includes(d.value) }"
            @click="toggleDiscipline(d.value)"
            :title="d.title"
          >{{ d.value }}</button>
        </div>
        <div class="reglaments-chip-group">
          <span class="reglaments-chip-group__label">Статус:</span>
          <button
            v-for="s in STATUSES"
            :key="s.value"
            class="reglaments-chip"
            :class="{ 'reglaments-chip--active': activeStatuses.includes(s.value) }"
            @click="toggleStatus(s.value)"
          >{{ s.label }}</button>
        </div>
        <button v-if="hasAnyFilter" class="reglaments-chip reglaments-chip--reset" @click="resetFilters">
          Сбросить
        </button>
      </div>
    </div>

    <!-- 2-column body -->
    <div class="reglaments-page__body">
      <!-- LEFT: list / search results -->
      <aside class="reglaments-page__list">
        <div v-if="loading" class="reglaments-empty">Загрузка…</div>
        <div v-else-if="!visibleItems.length" class="reglaments-empty">
          <i class="fa fa-folder-open"></i>
          <div>Ничего не найдено</div>
          <div class="text-muted small mt-1">
            Попробуй другую формулировку или сбрось фильтры.
          </div>
        </div>
        <div v-else class="reglaments-page__list-inner">
          <button
            v-for="r in visibleItems"
            :key="r.key"
            class="reglament-row"
            :class="{ 'reglament-row--active': r.reglament_id === selectedId }"
            @click="selectReglament(r)"
          >
            <div class="reglament-row__head">
              <span class="reglament-row__doc">{{ r.doc_type }} {{ r.doc_number }}</span>
              <span v-if="r.status && r.status !== 'actual'" class="reglament-row__status-badge" :data-status="r.status">
                {{ statusLabel(r.status) }}
              </span>
            </div>
            <div class="reglament-row__title">{{ r.title || r.reglament_title }}</div>
            <div v-if="r.snippet" class="reglament-row__snippet" v-html="r.snippet"></div>
            <div class="reglament-row__meta">
              <span v-if="r.section_number" class="reglament-row__section">п. {{ r.section_number }}</span>
              <span v-if="r.discipline_tags" class="reglament-row__tags">{{ r.discipline_tags }}</span>
              <span v-else-if="r.section_count" class="text-muted">{{ r.section_count }} разд.</span>
            </div>
          </button>
        </div>
      </aside>

      <!-- RIGHT: detail -->
      <section class="reglaments-page__detail">
        <div v-if="!detail && !detailLoading" class="reglaments-empty">
          <i class="fa fa-book"></i>
          <div>Выбери норму слева</div>
        </div>
        <div v-else-if="detailLoading" class="reglaments-empty">Загрузка нормы…</div>
        <template v-else>
          <div class="reglament-detail__header">
            <div>
              <div class="reglament-detail__doc-line">
                <span class="reglament-detail__doc">{{ detail.doc_type }} {{ detail.doc_number }}</span>
                <span class="reglament-detail__status-badge" :data-status="detail.status">
                  {{ statusLabel(detail.status) }}
                </span>
              </div>
              <h3 class="reglament-detail__title">{{ detail.title }}</h3>
              <div v-if="detail.full_title && detail.full_title !== detail.title" class="text-muted small mt-1">
                {{ detail.full_title }}
              </div>
            </div>
            <div class="reglament-detail__meta">
              <div v-if="detail.discipline_tags" class="reglament-detail__tags">
                <span v-for="t in detail.discipline_tags.split(',')" :key="t" class="reglament-detail__tag">
                  {{ t.trim() }}
                </span>
              </div>
              <div v-if="detail.effective_date" class="text-muted small">
                Введён: {{ formatDate(detail.effective_date) }}
              </div>
              <a v-if="detail.source_url" :href="detail.source_url" target="_blank" rel="noopener" class="reglament-detail__source" title="Прямая ссылка на источник (верифицирован)">
                <i class="fa fa-external-link"></i> Источник
              </a>
              <a v-else :href="findPdfUrl(detail)" target="_blank" rel="noopener" class="reglament-detail__source" title="Поиск PDF в Google по номеру и названию нормы">
                <i class="fa fa-search"></i> Найти PDF
              </a>
              <div v-if="auth.isSuperuser" class="reglament-detail__admin-actions">
                <button
                  class="reglaments-btn reglaments-btn--ghost"
                  @click="openUploadFor(detail)"
                  title="Загрузить PDF/DOCX — заменит текущие секции"
                >
                  <i class="fa fa-upload"></i>
                  {{ realSections.length ? 'Перезалить файл' : 'Загрузить файл' }}
                </button>
                <button
                  class="reglaments-btn reglaments-btn--ghost reglaments-btn--danger"
                  @click="onDeleteReglament"
                  title="Удалить норму"
                >
                  <i class="fa fa-trash"></i>
                </button>
              </div>
            </div>
          </div>

          <!-- Sections / TOC + content -->
          <div class="reglament-detail__body">
            <aside class="reglament-detail__toc">
              <div class="reglament-detail__toc-header">Содержание</div>
              <div v-if="!realSections.length" class="reglaments-empty reglaments-empty--small">
                <i class="fa fa-file-text-o"></i>
                <div class="small">Полный текст не загружен</div>
                <div class="text-muted small mt-1">
                  Загрузка через админ-панель (Phase 3) или скрипт <code>scrape_reglament.py</code>.
                </div>
              </div>
              <ul v-else class="reglament-toc">
                <li
                  v-for="s in realSections"
                  :key="s.id"
                  class="reglament-toc__item"
                  :class="{ 'reglament-toc__item--active': s.id === selectedSectionId }"
                  @click="selectSection(s.id)"
                >
                  <span v-if="s.section_number" class="reglament-toc__num">{{ s.section_number }}</span>
                  <span class="reglament-toc__title">{{ s.section_title || '(без названия)' }}</span>
                </li>
              </ul>
            </aside>
            <article class="reglament-detail__content">
              <div v-if="sectionLoading" class="reglaments-empty">Загрузка раздела…</div>
              <template v-else-if="currentSection">
                <div class="reglament-section__header">
                  <span v-if="currentSection.section_number" class="reglament-section__num">{{ currentSection.section_number }}</span>
                  <h4 class="reglament-section__title">{{ currentSection.section_title || '(без названия)' }}</h4>
                </div>
                <div class="reglament-section__body">{{ currentSection.content }}</div>
              </template>
              <div v-else-if="!realSections.length" class="reglaments-empty">
                <i class="fa fa-info-circle"></i>
                <div>В каталоге есть только метаданные этой нормы.</div>
                <div class="text-muted small mt-1">Поиск по теме работает (используется обложка), но конкретные пункты доступны только после загрузки полного PDF/DOCX.</div>
              </div>
              <div v-else class="reglaments-empty">Выбери раздел в оглавлении.</div>
            </article>
          </div>
        </template>
      </section>
    </div>

    <!-- Admin modal: create / upload (Phase 3) -->
    <Teleport to="body">
      <div v-if="modalOpen" class="reglaments-modal-backdrop" @click.self="closeModal">
        <div class="reglaments-modal">
          <div class="reglaments-modal__header">
            <h3 class="reglaments-modal__title">
              {{ modalMode === 'upload' ? 'Загрузить файл нормы' : 'Новая норма' }}
            </h3>
            <button class="reglaments-modal__close" @click="closeModal">×</button>
          </div>

          <div class="reglaments-modal__body">
            <template v-if="modalMode === 'create'">
              <div class="reglaments-form-row">
                <div class="reglaments-form-group" style="width: 100px;">
                  <label>Тип</label>
                  <select v-model="form.doc_type" class="form-control">
                    <option v-for="t in DOC_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
                  </select>
                </div>
                <div class="reglaments-form-group" style="flex: 1;">
                  <label>Номер</label>
                  <input v-model="form.doc_number" type="text" class="form-control" placeholder="63.13330.2018 или Р 21.101-2020" />
                </div>
              </div>
              <div class="reglaments-form-group">
                <label>Краткое название</label>
                <input v-model="form.title" type="text" class="form-control" placeholder="Бетонные и железобетонные конструкции..." />
              </div>
              <div class="reglaments-form-group">
                <label>Полное название <span class="text-muted small">(опционально)</span></label>
                <input v-model="form.full_title" type="text" class="form-control" placeholder="СП 63.13330.2018 Бетонные..." />
              </div>
              <div class="reglaments-form-row">
                <div class="reglaments-form-group" style="flex: 1;">
                  <label>Статус</label>
                  <select v-model="form.status" class="form-control">
                    <option v-for="s in STATUSES" :key="s.value" :value="s.value">{{ s.label }}</option>
                  </select>
                </div>
                <div class="reglaments-form-group" style="flex: 1;">
                  <label>Действует с</label>
                  <input v-model="form.effective_date" type="date" class="form-control" />
                </div>
              </div>
              <div class="reglaments-form-group">
                <label>Дисциплины <span class="text-muted small">(через запятую: КЖ,КМ)</span></label>
                <input v-model="form.discipline_tags" type="text" class="form-control" placeholder="КЖ,КМ" />
              </div>
              <div class="reglaments-form-group">
                <label>Источник URL <span class="text-muted small">(опционально, верифицированная ссылка)</span></label>
                <input v-model="form.source_url" type="url" class="form-control" placeholder="https://docs.cntd.ru/document/..." />
              </div>
            </template>

            <div class="reglaments-form-group">
              <label>
                Файл нормы <span class="text-muted small">(PDF/DOCX, до 50 MB)</span>
                <span v-if="modalMode === 'create'" class="text-muted small"> · опционально, можно дозагрузить позже</span>
              </label>
              <div
                class="reglaments-drop-zone"
                :class="{ 'reglaments-drop-zone--active': dropActive, 'reglaments-drop-zone--has-file': !!file }"
                @dragover.prevent="dropActive = true"
                @dragleave.prevent="dropActive = false"
                @drop.prevent="onFileDrop"
                @click="$refs.fileInputRef.click()"
              >
                <input ref="fileInputRef" type="file" accept=".pdf,.docx" hidden @change="onFilePick" />
                <template v-if="file">
                  <i class="fa fa-file-text"></i>
                  <div class="fw-500">{{ file.name }}</div>
                  <div class="text-muted small">{{ formatBytes(file.size) }}</div>
                  <button class="reglaments-btn reglaments-btn--ghost reglaments-btn--small" @click.stop="clearFile">Убрать</button>
                </template>
                <template v-else>
                  <i class="fa fa-cloud-upload"></i>
                  <div>Перетащи файл сюда или кликни для выбора</div>
                  <div class="text-muted small">PDF — парсится через pypdf · DOCX — через python-docx</div>
                </template>
              </div>
            </div>

            <div v-if="modalError" class="reglaments-modal__error">
              <i class="fa fa-exclamation-circle"></i> {{ modalError }}
            </div>
          </div>

          <div class="reglaments-modal__footer">
            <button class="reglaments-btn reglaments-btn--ghost" @click="closeModal" :disabled="modalBusy">
              Отмена
            </button>
            <button
              class="reglaments-btn reglaments-btn--primary"
              @click="onSaveModal"
              :disabled="modalBusy || !canSubmit"
            >
              <span v-if="modalBusy"><i class="fa fa-spinner fa-spin"></i> {{ modalMode === 'upload' ? 'Загружаем...' : 'Сохраняем...' }}</span>
              <span v-else>{{ modalMode === 'upload' ? 'Загрузить' : (file ? 'Создать и залить файл' : 'Создать норму') }}</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../services/api'
import { useAuthStore } from '../stores/auth'

const DOC_TYPES = [
  { value: 'СП', label: 'СП' },
  { value: 'ГОСТ', label: 'ГОСТ' },
  { value: 'СНиП', label: 'СНиП' },
  { value: 'ФЗ', label: 'ФЗ' },
  { value: 'ПП', label: 'ПП' },
]

const DISCIPLINES = [
  { value: 'КЖ', title: 'Конструкции железобетонные' },
  { value: 'КМ', title: 'Конструкции металлические' },
  { value: 'КД', title: 'Конструкции деревянные' },
  { value: 'АР', title: 'Архитектура' },
  { value: 'ОВ', title: 'Отопление, вентиляция' },
  { value: 'ВК', title: 'Водоснабжение, канализация' },
  { value: 'ЭО', title: 'Электроснабжение' },
  { value: 'АС', title: 'Автоматизация, связь' },
  { value: 'ПБ', title: 'Пожарная безопасность' },
  { value: 'ИЗЫСК', title: 'Инженерные изыскания' },
  { value: 'ПОС', title: 'Организация строительства' },
  { value: 'ФЗ', title: 'Законы / постановления' },
  { value: 'ОБЩ', title: 'Общие / межотраслевые' },
]

const STATUSES = [
  { value: 'actual', label: 'Действует' },
  { value: 'partially_actual', label: 'Частично' },
  { value: 'replaced', label: 'Заменён' },
  { value: 'cancelled', label: 'Отменён' },
]

const STATUS_LABEL = Object.fromEntries(STATUSES.map(s => [s.value, s.label]))

export default {
  name: 'Reglaments',
  setup() {
    const auth = useAuthStore()
    const query = ref('')
    const activeDocTypes = ref([])
    const activeDisciplines = ref([])
    const activeStatuses = ref([])

    const allItems = ref([])    // GET-каталог (когда поиск пустой)
    const searchItems = ref([]) // POST /search hits
    const searchMode = ref('')  // 'fts' | 'hybrid' | ''
    const loading = ref(false)
    const searching = ref(false)

    const selectedId = ref(null)
    const detail = ref(null)
    const detailLoading = ref(false)
    const selectedSectionId = ref(null)
    const currentSection = ref(null)
    const sectionLoading = ref(false)

    let searchTimer = null

    // Список для отображения. В режиме поиска (query непустой) — searchItems.
    // Иначе — каталог GET (отфильтрован клиентом, потому что GET ходит за всё).
    const visibleItems = computed(() => {
      const isSearch = !!query.value.trim()
      const src = isSearch ? searchItems.value : allItems.value
      // нормализуем ключи + добавляем доп. поля для рендеринга строки.
      return src.map(r => ({
        ...r,
        key: r.section_id || r.id,
        reglament_id: r.reglament_id || r.id,
        title: r.reglament_title || r.title,
      }))
        // клиентский фильтр для list-режима (поиск уже фильтруется на бэке)
        .filter(r => {
          if (isSearch) return true
          if (activeDocTypes.value.length && !activeDocTypes.value.includes(r.doc_type)) return false
          if (activeStatuses.value.length && !activeStatuses.value.includes(r.status || 'actual')) return false
          if (activeDisciplines.value.length) {
            const tags = (r.discipline_tags || '').split(',').map(t => t.trim()).filter(Boolean)
            if (!activeDisciplines.value.some(d => tags.includes(d))) return false
          }
          return true
        })
    })

    const totalCount = computed(() => allItems.value.length)
    const withContentCount = computed(() =>
      allItems.value.filter(r => (r.section_count || 0) > 1).length,
    )
    const hasAnyFilter = computed(() =>
      activeDocTypes.value.length || activeDisciplines.value.length || activeStatuses.value.length || query.value,
    )

    // Реальные секции — без cover-секции (section_number === '0').
    const realSections = computed(() => {
      if (!detail.value || !Array.isArray(detail.value.sections)) return []
      return detail.value.sections.filter(s => s.section_number !== '0')
    })

    async function loadCatalog() {
      loading.value = true
      try {
        const items = await api.reglaments.list({ limit: 500 })
        allItems.value = Array.isArray(items) ? items : []
      } catch (e) {
        console.error('Reglaments list failed:', e)
        allItems.value = []
      } finally {
        loading.value = false
      }
    }

    async function runSearch() {
      const q = query.value.trim()
      if (!q) {
        searchItems.value = []
        searchMode.value = ''
        return
      }
      searching.value = true
      try {
        const resp = await api.reglaments.search({
          query: q,
          limit: 50,
          doc_types: activeDocTypes.value.length ? activeDocTypes.value : null,
          statuses: activeStatuses.value.length ? activeStatuses.value : null,
          disciplines: activeDisciplines.value.length ? activeDisciplines.value : null,
        })
        searchItems.value = Array.isArray(resp?.items) ? resp.items : []
        searchMode.value = resp?.mode || 'fts'
      } catch (e) {
        console.error('Reglaments search failed:', e)
        searchItems.value = []
      } finally {
        searching.value = false
      }
    }

    watch(query, () => {
      if (searchTimer) clearTimeout(searchTimer)
      searchTimer = setTimeout(runSearch, 280)
    })

    watch([activeDocTypes, activeDisciplines, activeStatuses], () => {
      if (query.value.trim()) runSearch()
    }, { deep: true })

    function toggleDocType(v) { toggleIn(activeDocTypes, v) }
    function toggleDiscipline(v) { toggleIn(activeDisciplines, v) }
    function toggleStatus(v) { toggleIn(activeStatuses, v) }
    function toggleIn(refArr, v) {
      const arr = refArr.value
      const i = arr.indexOf(v)
      if (i >= 0) arr.splice(i, 1)
      else arr.push(v)
    }
    function resetFilters() {
      activeDocTypes.value = []
      activeDisciplines.value = []
      activeStatuses.value = []
      query.value = ''
    }
    function onResetSearch() {
      query.value = ''
      searchItems.value = []
      searchMode.value = ''
    }

    async function selectReglament(row) {
      const id = row.reglament_id || row.id
      if (!id) return
      // Если кликаем на тот же — оставляем; иначе грузим деталь.
      if (id !== selectedId.value) {
        selectedId.value = id
        await loadDetail(id)
      }
      // Если был клик из search-результата — пробуем выбрать конкретную секцию.
      if (row.section_id && row.section_id !== row.reglament_id) {
        await selectSection(row.section_id)
      }
    }

    async function loadDetail(id) {
      detailLoading.value = true
      detail.value = null
      currentSection.value = null
      selectedSectionId.value = null
      try {
        const r = await api.reglaments.getById(id)
        detail.value = r
        // Авто-выбираем первый реальный раздел если он есть.
        const real = (r?.sections || []).filter(s => s.section_number !== '0')
        if (real.length) {
          await selectSection(real[0].id)
        }
      } catch (e) {
        console.error('Reglament detail failed:', e)
      } finally {
        detailLoading.value = false
      }
    }

    async function selectSection(id) {
      sectionLoading.value = true
      selectedSectionId.value = id
      try {
        currentSection.value = await api.reglaments.getSection(id)
      } catch (e) {
        console.error('Section load failed:', e)
        currentSection.value = null
      } finally {
        sectionLoading.value = false
      }
    }

    function statusLabel(s) { return STATUS_LABEL[s] || s || '' }

    function formatDate(s) {
      if (!s) return ''
      try {
        const d = new Date(s)
        if (Number.isNaN(d.getTime())) return s
        return d.toLocaleDateString('ru-RU', { year: 'numeric', month: 'long', day: 'numeric' })
      } catch { return s }
    }

    /**
     * Google-поиск по точному номеру и названию нормы. Используется
     * когда source_url не задан (большинство норм в curated-списке).
     * Это надёжнее чем угадывать ID на docs.cntd.ru — каждый documenten ID
     * у Кодекса/Техэксперта непредсказуем, поиск по «СП 63.13330.2018 PDF»
     * почти всегда выводит на Минстрой/Гарант/Консультант+ или открытый PDF.
     */
    function findPdfUrl(r) {
      if (!r) return '#'
      const parts = [r.doc_type, r.doc_number, r.title, 'скачать PDF'].filter(Boolean).join(' ')
      return `https://www.google.com/search?q=${encodeURIComponent(parts)}`
    }

    // ─── Phase 3: admin modal (create / upload) ───────────────────────────
    const modalOpen = ref(false)
    const modalMode = ref('create') // 'create' | 'upload'
    const modalBusy = ref(false)
    const modalError = ref('')
    const dropActive = ref(false)
    const file = ref(null)
    const form = ref({
      doc_type: 'СП',
      doc_number: '',
      title: '',
      full_title: '',
      status: 'actual',
      effective_date: '',
      discipline_tags: '',
      source_url: '',
    })
    const uploadTargetId = ref(null) // для режима upload

    const canSubmit = computed(() => {
      if (modalMode.value === 'upload') return !!file.value
      return form.value.doc_type && form.value.doc_number.trim() && form.value.title.trim()
    })

    function openCreateModal() {
      modalMode.value = 'create'
      modalError.value = ''
      file.value = null
      uploadTargetId.value = null
      form.value = {
        doc_type: 'СП', doc_number: '', title: '', full_title: '',
        status: 'actual', effective_date: '',
        discipline_tags: '', source_url: '',
      }
      modalOpen.value = true
    }

    function openUploadFor(rg) {
      if (!rg) return
      modalMode.value = 'upload'
      uploadTargetId.value = rg.id
      modalError.value = ''
      file.value = null
      modalOpen.value = true
    }

    function closeModal() {
      if (modalBusy.value) return
      modalOpen.value = false
    }

    function onFilePick(e) {
      const f = e.target.files?.[0]
      if (f) file.value = f
    }
    function onFileDrop(e) {
      dropActive.value = false
      const f = e.dataTransfer.files?.[0]
      if (f) file.value = f
    }
    function clearFile() {
      file.value = null
    }

    function formatBytes(n) {
      if (!n) return '0 B'
      if (n < 1024) return `${n} B`
      if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
      return `${(n / 1024 / 1024).toFixed(1)} MB`
    }

    async function onSaveModal() {
      modalError.value = ''
      modalBusy.value = true
      try {
        let targetId = uploadTargetId.value
        // 1) Create-режим — сначала создаём метаданные
        if (modalMode.value === 'create') {
          const payload = {
            doc_type: form.value.doc_type,
            doc_number: form.value.doc_number.trim(),
            title: form.value.title.trim(),
            full_title: (form.value.full_title || form.value.title).trim(),
            status: form.value.status || 'actual',
            effective_date: form.value.effective_date || null,
            discipline_tags: form.value.discipline_tags?.trim() || null,
            source_url: form.value.source_url?.trim() || null,
          }
          const created = await api.reglaments.create(payload)
          targetId = created.id
        }
        // 2) Если файл выбран — заливаем
        if (file.value && targetId) {
          await api.reglaments.uploadFile(targetId, file.value)
        }
        // 3) Обновляем каталог и открываем созданную/обновлённую норму
        await loadCatalog()
        if (targetId) {
          selectedId.value = targetId
          await loadDetail(targetId)
        }
        modalOpen.value = false
      } catch (e) {
        const msg = e?.response?.data?.detail || e?.message || 'Не удалось сохранить'
        modalError.value = String(msg)
      } finally {
        modalBusy.value = false
      }
    }

    async function onDeleteReglament() {
      if (!detail.value) return
      const r = detail.value
      const ok = confirm(`Удалить норму ${r.doc_type} ${r.doc_number}?\n\nВсе разделы и embeddings будут удалены. Действие необратимо.`)
      if (!ok) return
      try {
        await api.reglaments.remove(r.id)
        detail.value = null
        selectedId.value = null
        currentSection.value = null
        await loadCatalog()
      } catch (e) {
        alert(`Ошибка удаления: ${e?.response?.data?.detail || e?.message}`)
      }
    }

    onMounted(loadCatalog)

    return {
      auth,
      DOC_TYPES, DISCIPLINES, STATUSES,
      query, activeDocTypes, activeDisciplines, activeStatuses,
      loading, searching, searchMode,
      visibleItems, totalCount, withContentCount, hasAnyFilter,
      selectedId, detail, detailLoading,
      realSections, selectedSectionId, currentSection, sectionLoading,
      toggleDocType, toggleDiscipline, toggleStatus, resetFilters, onResetSearch,
      selectReglament, selectSection,
      statusLabel, formatDate, findPdfUrl,
      // Phase 3
      modalOpen, modalMode, modalBusy, modalError, dropActive, file, form,
      canSubmit,
      openCreateModal, openUploadFor, closeModal,
      onFilePick, onFileDrop, clearFile, formatBytes,
      onSaveModal, onDeleteReglament,
    }
  },
}
</script>

<style scoped>
/* Подогнано под единый стиль Projects: list-card обёртка с радиусом
   --radius-lg, разделители --color-border-subtle между секциями.
   Тёмная тема — через переменные main.css (data-theme="dark"),
   НЕ через @media (prefers-color-scheme: dark).
   Все цвета берутся из main.css токенов, без хардкода. */

.reglaments-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-4);
  min-height: calc(100vh - 80px);
  color: var(--color-text);
}

/* ─── Toolbar card (header + search + filters) — ОДНА list-card обёртка ── */

.reglaments-page__toolbar {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.reglaments-page__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-border-subtle);
}
.reglaments-page__title {
  font-size: 24px;
  font-weight: 500;
  margin: 0 0 4px;
  color: var(--color-text);
}
.reglaments-page__actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.reglaments-page__searchbar {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border-subtle);
}
.reglaments-search-input {
  position: relative;
  flex: 1;
}
.reglaments-search-input__icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-muted);
  font-size: 14px;
  pointer-events: none;
}
.reglaments-search-input input {
  width: 100%;
  padding: 8px 36px;
  height: 38px;
  font-size: 14px;
  color: var(--color-text);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md, 8px);
  background: var(--color-surface-2);
  transition: border-color 0.15s, background 0.15s;
}
.reglaments-search-input input:focus {
  outline: none;
  border-color: var(--color-primary);
  background: var(--color-surface);
}
.reglaments-search-input input::placeholder {
  color: var(--color-text-muted);
}
.reglaments-search-input__clear {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 22px;
  height: 22px;
  border: none;
  background: transparent;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  color: var(--color-text-muted);
  border-radius: var(--radius-sm, 4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}
.reglaments-search-input__clear:hover {
  background: var(--color-surface-3);
  color: var(--color-text);
}

.reglaments-page__filters {
  display: flex;
  flex-wrap: wrap;
  gap: 12px var(--space-3);
  align-items: center;
  padding: var(--space-3) var(--space-4);
}
.reglaments-chip-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.reglaments-chip-group__label {
  font-size: 12px;
  color: var(--color-text-muted);
  font-weight: 500;
  margin-right: 2px;
}
.reglaments-chip {
  border: 1px solid transparent;
  background: var(--color-surface-2);
  color: var(--color-text);
  border-radius: var(--radius-sm, 4px);
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.4;
  cursor: pointer;
  transition: background 0.12s, color 0.12s, border-color 0.12s;
}
.reglaments-chip:hover {
  background: var(--color-surface-3);
}
.reglaments-chip--active {
  background: var(--color-primary);
  color: var(--color-on-primary, #fff);
}
.reglaments-chip--active:hover {
  background: var(--color-primary-hover, var(--color-primary));
}
.reglaments-chip--discipline { font-size: 11px; padding: 3px 8px; }
.reglaments-chip--reset {
  margin-left: auto;
  background: transparent;
  color: var(--color-text-muted);
}
.reglaments-chip--reset:hover {
  background: var(--color-surface-3);
  color: var(--color-danger);
}

/* ─── Body: 2 колонки список + деталь, каждая своя list-card ───────── */

.reglaments-page__body {
  display: grid;
  grid-template-columns: minmax(380px, 480px) 1fr;
  gap: var(--space-4);
  flex: 1;
  min-height: 0;
}

.reglaments-page__list {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  max-height: calc(100vh - 320px);
}
.reglaments-page__list-inner {
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: var(--space-2);
}

.reglament-row {
  display: block;
  width: 100%;
  text-align: left;
  border: 1px solid transparent;
  border-radius: var(--radius-md, 8px);
  background: transparent;
  padding: 12px 14px;
  cursor: pointer;
  transition: background 0.12s, border-color 0.12s;
}
.reglament-row + .reglament-row {
  margin-top: 2px;
}
.reglament-row:hover {
  background: var(--color-surface-2);
}
.reglament-row--active {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}
.reglament-row__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-2);
}
.reglament-row__doc {
  font-weight: 600;
  font-size: 12px;
  color: var(--color-primary);
  letter-spacing: 0.2px;
}
.reglament-row__status-badge {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: var(--radius-sm, 4px);
  background: var(--color-surface-3);
  color: var(--color-text-muted);
}
.reglament-row__status-badge[data-status="partially_actual"] {
  background: var(--color-warning-soft, var(--color-surface-3));
  color: var(--color-warning, var(--color-text-muted));
}
.reglament-row__status-badge[data-status="replaced"] {
  background: var(--color-info-soft, var(--color-primary-soft));
  color: var(--color-info, var(--color-primary));
}
.reglament-row__status-badge[data-status="cancelled"] {
  background: var(--color-danger-soft, var(--color-surface-3));
  color: var(--color-danger, var(--color-text-muted));
}
.reglament-row__title {
  margin-top: 4px;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.4;
  color: var(--color-text);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.reglament-row__snippet {
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-muted);
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.reglament-row__snippet :deep(mark) {
  background: var(--color-warning-soft, var(--color-primary-soft));
  color: var(--color-text);
  padding: 0 2px;
  border-radius: 2px;
}
.reglament-row__meta {
  display: flex;
  gap: var(--space-2);
  margin-top: 6px;
  font-size: 11px;
  color: var(--color-text-muted);
  align-items: center;
}
.reglament-row__section {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  padding: 1px 6px;
  border-radius: var(--radius-sm, 4px);
  font-weight: 500;
  font-size: 11px;
}
.reglament-row__tags {
  font-weight: 500;
  color: var(--color-text-muted);
}

/* ─── Detail panel — отдельная list-card ───────────────────────────────── */

.reglaments-page__detail {
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  max-height: calc(100vh - 320px);
}

.reglament-detail__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-4);
  padding: 16px 24px;
  border-bottom: 1px solid var(--color-border-subtle);
}
.reglament-detail__doc-line {
  display: flex;
  align-items: center;
  gap: 8px;
}
.reglament-detail__doc {
  font-weight: 600;
  font-size: 13px;
  color: var(--color-primary);
  letter-spacing: 0.3px;
}
.reglament-detail__status-badge {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: var(--radius-sm, 4px);
  background: var(--color-success-soft, var(--color-surface-3));
  color: var(--color-success, var(--color-text-muted));
}
.reglament-detail__status-badge[data-status="partially_actual"] {
  background: var(--color-warning-soft, var(--color-surface-3));
  color: var(--color-warning, var(--color-text-muted));
}
.reglament-detail__status-badge[data-status="replaced"] {
  background: var(--color-info-soft, var(--color-primary-soft));
  color: var(--color-info, var(--color-primary));
}
.reglament-detail__status-badge[data-status="cancelled"] {
  background: var(--color-danger-soft, var(--color-surface-3));
  color: var(--color-danger, var(--color-text-muted));
}
.reglament-detail__title {
  margin: 6px 0 0;
  font-size: 18px;
  font-weight: 500;
  line-height: 1.35;
  color: var(--color-text);
}
.reglament-detail__meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
}
.reglament-detail__tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.reglament-detail__tag {
  font-size: 11px;
  background: var(--color-surface-2);
  color: var(--color-text-muted);
  padding: 2px 8px;
  border-radius: var(--radius-sm, 4px);
  font-weight: 500;
}
.reglament-detail__source {
  font-size: 12px;
  color: var(--color-primary);
  text-decoration: none;
  margin-top: 2px;
}
.reglament-detail__source:hover { text-decoration: underline; }

.reglament-detail__body {
  display: grid;
  grid-template-columns: 280px 1fr;
  flex: 1;
  min-height: 0;
}
.reglament-detail__toc {
  border-right: 1px solid var(--color-border-subtle);
  overflow-y: auto;
  padding: 12px;
  background: var(--color-surface-2);
}
.reglament-detail__toc-header {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin: 4px 8px 8px;
}
.reglament-toc {
  list-style: none;
  padding: 0;
  margin: 0;
}
.reglament-toc__item {
  display: flex;
  gap: 8px;
  padding: 6px 8px;
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
  font-size: 13px;
  line-height: 1.35;
  color: var(--color-text);
  transition: background 0.12s, color 0.12s;
}
.reglament-toc__item:hover { background: var(--color-surface); }
.reglament-toc__item--active {
  background: var(--color-primary);
  color: var(--color-on-primary, #fff);
}
.reglament-toc__item--active .reglament-toc__num {
  color: var(--color-on-primary, #fff);
}
.reglament-toc__num {
  font-weight: 600;
  flex-shrink: 0;
  min-width: 36px;
  color: var(--color-text-muted);
  font-size: 12px;
}

.reglament-detail__content {
  overflow-y: auto;
  padding: 24px;
}
.reglament-section__header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border-subtle);
  margin-bottom: 16px;
}
.reglament-section__num {
  font-weight: 600;
  color: var(--color-primary);
  font-size: 14px;
  letter-spacing: 0.3px;
}
.reglament-section__title {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text);
}
.reglament-section__body {
  white-space: pre-wrap;
  line-height: 1.65;
  color: var(--color-text);
  font-size: 14px;
}

/* ─── Empty states ─────────────────────────────────────────────────────── */

.reglaments-empty {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  padding: 48px 24px;
  color: var(--color-text-muted);
  flex: 1;
}
.reglaments-empty i {
  font-size: 28px;
  margin-bottom: 12px;
  opacity: 0.5;
}
.reglaments-empty--small { padding: 16px; }
.reglaments-empty--small i { font-size: 20px; margin-bottom: 6px; }

.ml-2 { margin-left: 8px; }
.mt-1 { margin-top: 4px; }
.text-muted { color: var(--color-text-muted); }
.small { font-size: 12px; }
.fw-500 { font-weight: 500; }

@media (max-width: 1100px) {
  .reglaments-page__body {
    grid-template-columns: 1fr;
  }
  .reglaments-page__list {
    max-height: 480px;
  }
  .reglament-detail__body {
    grid-template-columns: 1fr;
  }
  .reglament-detail__toc {
    border-right: none;
    border-bottom: 1px solid var(--color-border-subtle);
  }
}

/* ─── Buttons ──────────────────────────────────────────────────────────── */
.reglaments-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.4;
  border: 1px solid transparent;
  border-radius: var(--radius-md, 6px);
  cursor: pointer;
  transition: background 0.12s, color 0.12s, border-color 0.12s;
  white-space: nowrap;
}
.reglaments-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.reglaments-btn--primary {
  background: var(--color-primary);
  color: var(--color-on-primary, #fff);
}
.reglaments-btn--primary:hover:not(:disabled) {
  background: var(--color-primary-hover, var(--color-primary));
}
.reglaments-btn--ghost {
  background: transparent;
  color: var(--color-text);
  border-color: var(--color-border);
}
.reglaments-btn--ghost:hover:not(:disabled) {
  background: var(--color-surface-2);
}
.reglaments-btn--danger {
  color: var(--color-danger);
}
.reglaments-btn--danger:hover:not(:disabled) {
  background: var(--color-danger-soft, var(--color-surface-2));
}
.reglaments-btn--small {
  padding: 3px 8px;
  font-size: 11px;
}

.reglament-detail__admin-actions {
  display: flex;
  gap: 6px;
  margin-top: 6px;
}

/* ─── Modal ────────────────────────────────────────────────────────────── */
.reglaments-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 48px 16px;
  z-index: 1000;
  overflow-y: auto;
}
.reglaments-modal {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.25);
  width: 100%;
  max-width: 560px;
  display: flex;
  flex-direction: column;
}
.reglaments-modal__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border-subtle);
}
.reglaments-modal__title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}
.reglaments-modal__close {
  border: none;
  background: transparent;
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
  color: var(--color-text-muted);
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm, 4px);
}
.reglaments-modal__close:hover {
  background: var(--color-surface-2);
  color: var(--color-text);
}
.reglaments-modal__body {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.reglaments-modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid var(--color-border-subtle);
}
.reglaments-modal__error {
  background: var(--color-danger-soft, #fef2f2);
  color: var(--color-danger, #dc2626);
  padding: 8px 12px;
  border-radius: var(--radius-sm, 4px);
  font-size: 12px;
}

.reglaments-form-row {
  display: flex;
  gap: 8px;
}
.reglaments-form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.reglaments-form-group label {
  font-size: 12px;
  color: var(--color-text-muted);
  font-weight: 500;
}
.reglaments-form-group .form-control {
  padding: 6px 10px;
  height: 34px;
  font-size: 13px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm, 4px);
  background: var(--color-surface);
  color: var(--color-text);
}
.reglaments-form-group .form-control:focus {
  outline: none;
  border-color: var(--color-primary);
}

/* ─── Drop zone ────────────────────────────────────────────────────────── */
.reglaments-drop-zone {
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-md, 8px);
  padding: 24px;
  text-align: center;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  color: var(--color-text-muted);
  background: var(--color-surface-2);
  transition: background 0.12s, border-color 0.12s;
}
.reglaments-drop-zone:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}
.reglaments-drop-zone--active {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}
.reglaments-drop-zone--has-file {
  border-style: solid;
  color: var(--color-text);
}
.reglaments-drop-zone i {
  font-size: 24px;
  opacity: 0.7;
}
</style>
