<template>
  <div class="kp-workspace">
    <!-- Topbar: заголовок + действия на уровне КП-вкладки. -->
    <header class="kp-topbar">
      <div class="kp-topbar__title">
        <h3 class="m-0">Коммерческие предложения</h3>
        <span v-if="kpDocuments.length" class="kp-topbar__count">
          {{ kpDocuments.length }}
        </span>
      </div>
      <div class="kp-topbar__actions">
        <button class="btn btn-sm btn-primary" type="button" @click="$emit('create-kp')">
          <i class="fas fa-plus mr-1"></i> Создать КП
        </button>
        <button
          v-if="canManageTemplates"
          class="btn btn-sm btn-outline-secondary"
          type="button"
          @click="$emit('open-templates')"
        >
          <i class="fas fa-layer-group mr-1"></i> Шаблоны
        </button>
      </div>
    </header>

    <div class="kp-split">
      <!-- Колонка 1: список КП лида. -->
      <aside class="kp-list custom-scrollbar">
        <div v-if="loading" class="kp-empty">
          <div class="spinner mx-auto"></div>
        </div>
        <div v-else-if="!kpDocuments.length" class="kp-empty">
          <i class="far fa-file-alt fa-2x text-muted mb-2"></i>
          <div class="text-muted small">КП пока не созданы</div>
        </div>
        <button
          v-for="doc in kpDocuments"
          v-else
          :key="doc.id"
          type="button"
          class="kp-list__item"
          :class="{ active: selectedKpId === doc.id }"
          @click="selectKp(doc.id)"
        >
          <div class="kp-list__head">
            <strong class="kp-list__num">{{ doc.number_display }}</strong>
            <span class="badge badge-secondary kp-list__badge">{{ doc.status || 'draft' }}</span>
          </div>
          <div class="kp-list__meta">
            <span>v{{ doc.current_version || 1 }}</span>
            <span class="dot">·</span>
            <span>{{ formatDate(doc.created_at) }}</span>
          </div>
          <div class="kp-list__sum">
            {{ formatMoney(latestSum(doc)) }}
          </div>
        </button>
      </aside>

      <!-- Колонка 2: предпросмотр текущей версии. -->
      <section class="kp-preview">
        <template v-if="!selectedDoc">
          <div class="kp-preview__placeholder">
            <i class="far fa-file-alt fa-3x text-muted mb-3"></i>
            <p class="text-muted m-0">Выберите КП слева или создайте новое</p>
          </div>
        </template>
        <template v-else>
          <div class="kp-preview__toolbar">
            <div class="kp-preview__title">
              <strong>{{ selectedDoc.number_display }}</strong>
              <span v-if="selectedVersion" class="kp-preview__vbadge">
                v{{ selectedVersion.version }}
              </span>
              <span v-if="selectedVersion" class="text-muted small ml-2">
                {{ formatDate(selectedVersion.created_at) }}
              </span>
            </div>
            <div class="kp-preview__actions">
              <button
                class="btn btn-sm btn-primary"
                type="button"
                :disabled="!!actionBusy"
                @click="generateNewVersion"
                title="Сгенерировать новую версию из шаблона"
              >
                <i
                  :class="actionBusy === 'generate' ? 'fas fa-spinner fa-spin' : 'fas fa-plus'"
                  class="mr-1"
                ></i>
                Создать версию
              </button>
              <label class="btn btn-sm btn-outline-secondary m-0" :class="{ disabled: actionBusy }">
                <i class="fas fa-upload mr-1"></i> Загрузить
                <input
                  type="file"
                  hidden
                  accept=".docx,.pdf"
                  :disabled="actionBusy"
                  @change="onUploadChange"
                />
              </label>
              <div class="kp-preview__divider"></div>
              <button
                v-if="selectedVersion?.docx_url"
                class="btn btn-sm btn-outline-primary"
                type="button"
                :disabled="downloadBusy === 'docx'"
                @click="downloadVersion(selectedVersion, 'docx')"
                title="Скачать DOCX"
              >
                <i
                  :class="downloadBusy === 'docx' ? 'fas fa-spinner fa-spin' : 'fas fa-file-word'"
                  class="mr-1"
                ></i> DOCX
              </button>
              <button
                v-if="selectedVersion?.pdf_url"
                class="btn btn-sm btn-outline-primary"
                type="button"
                :disabled="downloadBusy === 'pdf'"
                @click="downloadVersion(selectedVersion, 'pdf')"
                title="Скачать PDF"
              >
                <i
                  :class="downloadBusy === 'pdf' ? 'fas fa-spinner fa-spin' : 'fas fa-file-pdf'"
                  class="mr-1"
                ></i> PDF
              </button>
              <button
                v-if="selectedVersion?.docx_url"
                class="btn btn-sm btn-outline-secondary"
                type="button"
                :disabled="previewLoading"
                title="Обновить предпросмотр"
                @click="renderPreview(selectedVersion)"
              >
                <i :class="previewLoading ? 'fas fa-spinner fa-spin' : 'fas fa-sync-alt'"></i>
              </button>
            </div>
          </div>

          <div class="kp-preview__body">
            <div v-if="previewLoading" class="kp-preview__overlay">
              <div class="spinner"></div>
              <div class="small text-muted mt-2">Рендер документа…</div>
            </div>
            <div v-else-if="previewError" class="kp-preview__overlay">
              <i class="fas fa-exclamation-triangle fa-2x text-warning mb-2"></i>
              <div class="text-muted">{{ previewError }}</div>
              <button
                v-if="selectedVersion?.docx_url"
                class="btn btn-sm btn-outline-primary mt-3"
                type="button"
                @click="renderPreview(selectedVersion)"
              >
                <i class="fas fa-redo mr-1"></i> Повторить
              </button>
            </div>
            <div v-else-if="!selectedVersion?.docx_url" class="kp-preview__overlay">
              <i class="fas fa-file-import fa-2x text-muted mb-2"></i>
              <div class="text-muted text-center">
                У версии нет DOCX-файла.<br />
                <span v-if="selectedVersion?.pdf_url">Доступен только PDF — нажмите «PDF» сверху.</span>
                <span v-else>Создайте новую версию или загрузите файл.</span>
              </div>
            </div>
            <div
              v-show="!previewLoading && !previewError && selectedVersion?.docx_url"
              ref="previewContainer"
              class="kp-preview__doc custom-scrollbar"
            ></div>
          </div>
        </template>
      </section>

      <!-- Колонка 3: история версий. -->
      <aside v-if="selectedDoc" class="kp-versions custom-scrollbar">
        <div class="kp-versions__title">История версий</div>
        <div v-if="!sortedVersions.length" class="text-muted small">Версий нет</div>
        <button
          v-for="ver in sortedVersions"
          v-else
          :key="ver.id"
          type="button"
          class="kp-version"
          :class="{ active: selectedVersionId === ver.id }"
          @click="selectVersion(ver.id)"
        >
          <div class="kp-version__head">
            <strong>v{{ ver.version }}</strong>
            <span class="small text-muted">{{ formatDate(ver.created_at) }}</span>
          </div>
          <div class="kp-version__sum">
            {{ formatMoney(ver.total_amount) }}
            <span v-if="ver.vat_amount" class="text-muted small ml-1">
              · НДС {{ formatMoney(ver.vat_amount) }}
            </span>
          </div>
          <div class="kp-version__files">
            <span
              v-if="ver.docx_url"
              class="kp-version__pill"
              title="Скачать DOCX"
              @click.stop="downloadVersion(ver, 'docx')"
            >
              <i class="fas fa-file-word mr-1"></i> DOCX
            </span>
            <span
              v-if="ver.pdf_url"
              class="kp-version__pill"
              title="Скачать PDF"
              @click.stop="downloadVersion(ver, 'pdf')"
            >
              <i class="fas fa-file-pdf mr-1"></i> PDF
            </span>
            <span v-if="!ver.docx_url && !ver.pdf_url" class="small text-muted">— нет файлов</span>
          </div>
        </button>
      </aside>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import axios from 'axios'
import { renderAsync as renderDocxAsync } from 'docx-preview'
import { useToast } from '@/composables/useToast'
import { downloadFromPath, downloadFromHref } from '@/utils/download'

/**
 * Версии КП хранятся в БД в двух форматах:
 *   • старые (созданы через legacy `POST /uploads/kp/versions`):
 *     `docx_url = "KP/600-КП/file.docx"` — это «голый» storage-path.
 *   • новые (через `POST /kp/{id}/generate-version` + `upload-worker`):
 *     `docx_url = "/api/v1/storage/download?path=KP/..."` — это уже
 *     готовая API-ссылка из `storage.publish()`.
 * Чтобы и preview, и download корректно работали в обоих случаях,
 * нормализуем к API-href: если значение уже начинается с `/api/`
 * или `http`, отдаём как есть, иначе оборачиваем в storage/download.
 */
const toApiHref = (value) => {
  if (!value) return ''
  const s = String(value)
  if (s.startsWith('/api/') || s.startsWith('http://') || s.startsWith('https://')) return s
  return `/api/v1/storage/download?path=${encodeURIComponent(s)}`
}

/**
 * Рабочее пространство КП внутри LeadDetail (вкладка «КП»).
 *
 * Цель — UX, аналогичный реестру исходящих:
 *   • слева — компактный список КП лида;
 *   • по центру — настоящий предпросмотр документа (docx-preview);
 *   • справа — версии с быстрыми ссылками DOCX/PDF.
 *
 * В отличие от исходящих, у нас нет soffice/LibreOffice на бэке,
 * поэтому PDF серверно не рендерим — превью делается клиентским
 * docx-preview (он умеет таблицы/секции/стили). PDF показывается
 * только если был загружен пользователем как файл версии.
 */
export default {
  name: 'LeadKpWorkspace',
  props: {
    leadId: { type: String, required: true },
    kpDocuments: { type: Array, default: () => [] },
    kpTemplates: { type: Array, default: () => [] },
    kpBindings: { type: Array, default: () => [] },
    canManageTemplates: { type: Boolean, default: false },
    loading: { type: Boolean, default: false }
  },
  emits: ['create-kp', 'open-templates', 'reload'],
  setup(props, { emit }) {
    const toast = useToast()

    const selectedKpId = ref(null)
    const selectedVersionId = ref(null)
    const previewContainer = ref(null)
    const previewLoading = ref(false)
    const previewError = ref('')
    const actionBusy = ref('')        // '' | 'generate' | 'upload'
    const downloadBusy = ref('')      // '' | 'docx' | 'pdf'
    // Чтобы устаревший fetch не перезаписал актуальный предпросмотр.
    let previewToken = 0

    const normalizeId = (v) => (v == null ? '' : String(v))

    const selectedDoc = computed(() =>
      props.kpDocuments.find((d) => normalizeId(d.id) === normalizeId(selectedKpId.value)) || null
    )

    const sortedVersions = computed(() => {
      const list = selectedDoc.value?.versions || []
      // По убыванию номера версии — последняя сверху.
      return [...list].sort((a, b) => (b.version || 0) - (a.version || 0))
    })

    const selectedVersion = computed(() => {
      if (!selectedVersionId.value) {
        return sortedVersions.value[0] || null
      }
      return (
        sortedVersions.value.find((v) => normalizeId(v.id) === normalizeId(selectedVersionId.value))
        || sortedVersions.value[0]
        || null
      )
    })

    const latestSum = (doc) => {
      const versions = doc?.versions || []
      if (!versions.length) return 0
      const latest = [...versions].sort((a, b) => (b.version || 0) - (a.version || 0))[0]
      return Number(latest?.total_amount || 0)
    }

    const formatMoney = (value) => {
      const n = Number(value || 0)
      // Тысячные разряды — узким неразрывным пробелом, как в нашем docx.
      const formatted = n.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
      return `${formatted} ₽`
    }

    const formatDate = (value) => {
      if (!value) return '—'
      try {
        return new Date(value).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
      } catch {
        return String(value)
      }
    }

    const resolveTemplateForKp = (kp) => {
      if (!kp) return null
      if (kp.template_id) {
        return props.kpTemplates.find((t) => normalizeId(t.id) === normalizeId(kp.template_id)) || null
      }
      if (kp.our_company_id) {
        const binding = props.kpBindings.find(
          (b) => normalizeId(b.our_company_id) === normalizeId(kp.our_company_id)
        )
        if (binding) {
          return props.kpTemplates.find((t) => normalizeId(t.id) === normalizeId(binding.template_id)) || null
        }
      }
      return props.kpTemplates[0] || null
    }

    const resolveTemplateDocx = (kp) => resolveTemplateForKp(kp)?.docx_url || ''

    // ─── selection helpers ───────────────────────────────────────────────
    const selectKp = (id) => {
      selectedKpId.value = id
      selectedVersionId.value = null   // → подхватится последняя версия
    }

    const selectVersion = (id) => {
      selectedVersionId.value = id
    }

    // Автовыбор первого КП при наличии и при изменении набора КП.
    watch(
      () => props.kpDocuments,
      (list) => {
        if (!list?.length) {
          selectedKpId.value = null
          selectedVersionId.value = null
          return
        }
        if (!selectedKpId.value || !list.some((d) => normalizeId(d.id) === normalizeId(selectedKpId.value))) {
          selectedKpId.value = list[0].id
          selectedVersionId.value = null
        }
      },
      { immediate: true }
    )

    // При смене выбранной версии (или выбранного КП) — перерендерить превью.
    watch(
      () => selectedVersion.value?.id,
      async () => {
        const v = selectedVersion.value
        if (!v) {
          clearPreview()
          return
        }
        await nextTick()
        renderPreview(v)
      }
    )

    // ─── docx-preview render ─────────────────────────────────────────────
    const clearPreview = () => {
      if (previewContainer.value) previewContainer.value.innerHTML = ''
      previewError.value = ''
    }

    const renderPreview = async (version) => {
      if (!version?.docx_url) {
        clearPreview()
        return
      }
      const token = ++previewToken
      previewLoading.value = true
      previewError.value = ''
      try {
        const url = toApiHref(version.docx_url)
        const response = await axios.get(url, { responseType: 'blob' })
        if (token !== previewToken) return  // выбор изменился — выбрасываем
        await nextTick()
        if (!previewContainer.value) return
        previewContainer.value.innerHTML = ''
        await renderDocxAsync(response.data, previewContainer.value, null, {
          className: 'docx',
          inWrapper: true,
          ignoreWidth: false,
          ignoreHeight: false,
          ignoreFonts: false,
          breakPages: true,
          experimental: true,
          useBase64URL: false
        })
      } catch (err) {
        if (token !== previewToken) return
        console.error('KP preview error', err)
        previewError.value = err?.response?.data?.detail || 'Не удалось загрузить предпросмотр документа'
      } finally {
        if (token === previewToken) previewLoading.value = false
      }
    }

    // ─── actions: generate / upload / download ───────────────────────────
    const generateNewVersion = async () => {
      const kp = selectedDoc.value
      if (!kp?.id) return
      actionBusy.value = 'generate'
      try {
        // Атомарный синхронный endpoint: бэк рендерит DOCX + (если есть
        // soffice) PDF, кладёт оба файла в storage и СРАЗУ возвращает
        // готовый KpVersion с заполненными docx_url/pdf_url. Никакого
        // upload-worker'а — нет race condition «версия в БД появилась,
        // но docx_url ещё пустой».
        await axios.post(`/api/v1/kp/${kp.id}/generate-version`)
        toast.success('Создана новая версия КП')
        // Снимаем закреп — пусть selectedVersion подхватит самую свежую.
        selectedVersionId.value = null
        emit('reload')
      } catch (e) {
        const msg = e?.response?.data?.detail || 'Не удалось создать версию КП'
        toast.error(msg)
      } finally {
        actionBusy.value = ''
      }
    }

    const onUploadChange = async (event) => {
      const kp = selectedDoc.value
      const file = event.target.files?.[0]
      if (!kp?.id || !file) return
      actionBusy.value = 'upload'
      const isPdf = (file.name || '').toLowerCase().endsWith('.pdf')
      try {
        const formData = new FormData()
        formData.append('kp_id', kp.id)
        formData.append('file', file)
        await axios.post('/api/v1/uploads/kp/versions', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        toast.success(`«${file.name}» загружен — обрабатываем...`)
        selectedVersionId.value = null
        emit('reload')
        // Ручной upload идёт через `upload-worker` (asyncpolling каждые 3с),
        // поэтому сразу после `emit('reload')` в kpDocuments прилетит
        // версия С пустым docx_url/pdf_url. Поллим до тех пор, пока
        // воркер не проставит нужное поле (или таймаут 30с).
        await waitForUrlField(kp.id, isPdf ? 'pdf_url' : 'docx_url', 30_000)
      } catch (e) {
        const msg = e?.response?.data?.detail || 'Не удалось загрузить файл'
        toast.error(msg)
      } finally {
        actionBusy.value = ''
        event.target.value = ''
      }
    }

    /**
     * Опросить `GET /kp/?lead_id=...` пока у самой свежей версии указанного
     * КП не появится непустое поле `field` (docx_url или pdf_url).
     * Используется после ручной загрузки через upload-worker, где новая
     * версия в БД появляется мгновенно, но `docx_url` — асинхронно.
     * Если получилось — эмитит reload, чтобы родитель подсунул свежие
     * данные с заполненным URL. Если таймаут — молча останавливаемся
     * (пользователь увидит файл после следующего обновления страницы).
     */
    const waitForUrlField = async (kpId, field, timeoutMs = 15_000) => {
      const startedAt = Date.now()
      let attempts = 0
      // Чтобы не блокировать UI и не нагружать API: каждые 1.5 с до
      // первого успеха.
      while (Date.now() - startedAt < timeoutMs) {
        await new Promise((r) => setTimeout(r, 1500))
        attempts += 1
        try {
          const res = await axios.get('/api/v1/kp/', { params: { lead_id: props.leadId } })
          const list = res.data || []
          const doc = list.find((d) => normalizeId(d.id) === normalizeId(kpId))
          if (!doc) continue
          const sorted = [...(doc.versions || [])].sort((a, b) => (b.version || 0) - (a.version || 0))
          if (sorted[0] && sorted[0][field]) {
            // Эмитим reload, чтобы родитель тоже подтянул свежие данные.
            emit('reload')
            return true
          }
        } catch (e) {
          // не критично — просто пробуем следующую итерацию
          if (attempts > 5) return false
        }
      }
      return false
    }

    const downloadVersion = async (version, type) => {
      const value = type === 'pdf' ? version?.pdf_url : version?.docx_url
      if (!value) return
      const docNumber = selectedDoc.value?.number_display || 'KP'
      const ext = type === 'pdf' ? 'pdf' : 'docx'
      const fileName = `${docNumber}-v${version.version || 1}.${ext}`
      downloadBusy.value = type
      try {
        const s = String(value)
        // Старые версии хранят raw path, новые — готовый API-href.
        if (s.startsWith('/api/') || s.startsWith('http://') || s.startsWith('https://')) {
          await downloadFromHref(s, fileName, { module: 'kp', entityId: version.id })
        } else {
          await downloadFromPath(s, fileName, { module: 'kp', entityId: version.id })
        }
      } catch (e) {
        toast.error('Не удалось скачать файл')
      } finally {
        downloadBusy.value = ''
      }
    }

    onBeforeUnmount(() => {
      // На всякий случай — обрываем активный fetch, чтобы он не дёрнул
      // уже размонтированный previewContainer через ref.
      previewToken++
    })

    return {
      // state
      selectedKpId,
      selectedVersionId,
      previewContainer,
      previewLoading,
      previewError,
      actionBusy,
      downloadBusy,
      // computed
      selectedDoc,
      selectedVersion,
      sortedVersions,
      // helpers
      latestSum,
      formatMoney,
      formatDate,
      resolveTemplateDocx,
      // methods
      selectKp,
      selectVersion,
      renderPreview,
      generateNewVersion,
      onUploadChange,
      downloadVersion
    }
  }
}
</script>

<style scoped>
.kp-workspace {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  gap: 10px;
}

/* ─── Topbar ───────────────────────────────────────────────────────────── */
.kp-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  background: var(--md-sys-color-surface, #fff);
  border: 1px solid var(--md-sys-color-outline-variant, rgba(0, 0, 0, 0.08));
  border-radius: 12px;
  flex-shrink: 0;
}
.kp-topbar__title { display: flex; align-items: center; gap: 10px; }
.kp-topbar__title h3 { font-size: 1rem; font-weight: 600; }
.kp-topbar__count {
  background: var(--md-sys-color-surface-container, rgba(0, 0, 0, 0.05));
  color: var(--md-sys-color-on-surface-variant, #5f6368);
  font-size: 0.78rem;
  font-weight: 600;
  border-radius: 999px;
  padding: 2px 10px;
}
.kp-topbar__actions { display: flex; gap: 8px; flex-wrap: wrap; }

/* ─── Split layout ─────────────────────────────────────────────────────── */
.kp-split {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr) 280px;
  gap: 10px;
  flex-grow: 1;
  min-height: 0;
}

/* ─── Колонка 1: список КП ────────────────────────────────────────────── */
.kp-list {
  background: var(--md-sys-color-surface, #fff);
  border: 1px solid var(--md-sys-color-outline-variant, rgba(0, 0, 0, 0.08));
  border-radius: 12px;
  padding: 8px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.kp-list__item {
  text-align: left;
  background: transparent;
  border: 1px solid transparent;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.kp-list__item:hover {
  background: var(--md-sys-color-surface-container-low, rgba(0, 0, 0, 0.03));
}
.kp-list__item.active {
  background: var(--md-sys-color-primary-container, rgba(33, 150, 243, 0.12));
  border-color: var(--md-sys-color-primary, #2196f3);
}
.kp-list__head { display: flex; align-items: center; justify-content: space-between; gap: 6px; }
.kp-list__num { font-size: 0.95rem; }
.kp-list__badge { font-size: 0.7rem; padding: 2px 8px; }
.kp-list__meta { font-size: 0.78rem; color: var(--md-sys-color-on-surface-variant, #5f6368); display: flex; gap: 4px; align-items: center; }
.kp-list__meta .dot { opacity: 0.5; }
.kp-list__sum { font-size: 0.82rem; font-weight: 600; color: var(--md-sys-color-on-surface, #1f1f1f); }

.kp-empty {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  text-align: center;
}

/* ─── Колонка 2: preview ──────────────────────────────────────────────── */
.kp-preview {
  background: var(--md-sys-color-surface, #fff);
  border: 1px solid var(--md-sys-color-outline-variant, rgba(0, 0, 0, 0.08));
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}
.kp-preview__placeholder {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  text-align: center;
}
.kp-preview__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant, rgba(0, 0, 0, 0.08));
  background: var(--md-sys-color-surface, #fff);
  flex-shrink: 0;
}
.kp-preview__title { display: flex; align-items: center; gap: 8px; min-width: 0; }
.kp-preview__title strong { font-size: 1rem; }
.kp-preview__vbadge {
  background: var(--md-sys-color-primary-container, rgba(33, 150, 243, 0.12));
  color: var(--md-sys-color-on-primary-container, #0b3d91);
  font-size: 0.72rem;
  font-weight: 600;
  border-radius: 999px;
  padding: 2px 8px;
}
.kp-preview__actions { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.kp-preview__divider {
  width: 1px;
  height: 22px;
  background: var(--md-sys-color-outline-variant, rgba(0, 0, 0, 0.12));
  margin: 0 2px;
}

.kp-preview__body {
  position: relative;
  flex-grow: 1;
  min-height: 0;
  background: #e8eaed;
  overflow: hidden;
}
.kp-preview__overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  text-align: center;
  background: #e8eaed;
  z-index: 1;
}
.kp-preview__doc {
  position: absolute;
  inset: 0;
  overflow: auto;
  padding: 18px 14px 28px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* docx-preview сам внутри рендерит обёртки `.docx-wrapper > .docx`.
   Подгоняем фон и тень страницы под образ «листа A4».               */
.kp-preview__doc :deep(.docx-wrapper) {
  background: transparent;
  padding: 0;
}
.kp-preview__doc :deep(.docx-wrapper > section.docx) {
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08), 0 6px 24px rgba(0, 0, 0, 0.12);
  margin-bottom: 18px;
  border-radius: 4px;
}

/* ─── Колонка 3: версии ────────────────────────────────────────────────── */
.kp-versions {
  background: var(--md-sys-color-surface, #fff);
  border: 1px solid var(--md-sys-color-outline-variant, rgba(0, 0, 0, 0.08));
  border-radius: 12px;
  padding: 12px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.kp-versions__title {
  font-weight: 600;
  font-size: 0.86rem;
  color: var(--md-sys-color-on-surface, #1f1f1f);
  margin-bottom: 4px;
}
.kp-version {
  text-align: left;
  background: var(--md-sys-color-surface-container-low, rgba(0, 0, 0, 0.02));
  border: 1px solid var(--md-sys-color-outline-variant, rgba(0, 0, 0, 0.08));
  border-radius: 10px;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.kp-version:hover {
  background: var(--md-sys-color-surface-container, rgba(0, 0, 0, 0.05));
}
.kp-version.active {
  background: var(--md-sys-color-primary-container, rgba(33, 150, 243, 0.12));
  border-color: var(--md-sys-color-primary, #2196f3);
}
.kp-version__head { display: flex; justify-content: space-between; align-items: center; gap: 6px; }
.kp-version__sum { font-size: 0.86rem; }
.kp-version__files { display: flex; flex-wrap: wrap; gap: 6px; }
.kp-version__pill {
  display: inline-flex;
  align-items: center;
  font-size: 0.74rem;
  font-weight: 600;
  background: var(--md-sys-color-surface, #fff);
  border: 1px solid var(--md-sys-color-outline-variant, rgba(0, 0, 0, 0.12));
  border-radius: 999px;
  padding: 3px 10px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.kp-version__pill:hover {
  background: var(--md-sys-color-primary, #2196f3);
  color: var(--md-sys-color-on-primary, #fff);
  border-color: var(--md-sys-color-primary, #2196f3);
}

/* ─── Адаптив ─────────────────────────────────────────────────────────── */
@media (max-width: 1280px) {
  .kp-split { grid-template-columns: 220px minmax(0, 1fr) 260px; }
}
@media (max-width: 1100px) {
  .kp-split { grid-template-columns: 200px minmax(0, 1fr); }
  .kp-versions { display: none; }
}
@media (max-width: 820px) {
  .kp-split { grid-template-columns: 1fr; }
  .kp-list { max-height: 200px; }
}

.custom-scrollbar::-webkit-scrollbar { width: 6px; height: 6px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(128, 128, 128, 0.3); border-radius: 3px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
</style>
