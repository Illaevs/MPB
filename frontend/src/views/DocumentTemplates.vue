<template>
  <div class="document-templates-view">
    <header class="dt-header">
      <div>
        <div class="dt-kicker">Администрирование</div>
        <h1>Шаблоны документов</h1>
        <p>DOCX-шаблоны, версии файлов и справочник идентификаторов для плейсхолдеров.</p>
      </div>
      <button class="dt-btn dt-btn--primary" @click="openCreate">
        <i class="fas fa-plus"></i>
        Новый шаблон
      </button>
    </header>

    <div class="dt-tabs">
      <button :class="{ active: activeTab === 'templates' }" @click="activeTab = 'templates'">
        <i class="fas fa-file-word"></i>
        Шаблоны
      </button>
      <button :class="{ active: activeTab === 'fields' }" @click="activeTab = 'fields'">
        <i class="fas fa-list-check"></i>
        Справочник полей
      </button>
    </div>

    <section v-if="activeTab === 'templates'" class="dt-grid">
      <div class="dt-card">
        <div class="dt-toolbar">
          <label class="dt-search">
            <i class="fas fa-search"></i>
            <input v-model.trim="templateFilters.search" placeholder="Поиск по шаблонам..." @input="debouncedLoadTemplates">
          </label>
          <select v-model="templateFilters.module" @change="loadTemplates">
            <option value="">Все модули</option>
            <option v-for="item in meta.modules" :key="item.value" :value="item.value">{{ item.label }}</option>
          </select>
          <select v-model="templateFilters.document_kind" @change="loadTemplates">
            <option value="">Все типы</option>
            <option v-for="item in filteredDocumentKinds" :key="item.value" :value="item.value">{{ item.label }}</option>
          </select>
          <select v-model="templateFilters.status" @change="loadTemplates">
            <option value="">Все статусы</option>
            <option v-for="item in meta.statuses" :key="item.value" :value="item.value">{{ item.label }}</option>
          </select>
          <select v-model="templateFilters.active" @change="loadTemplates">
            <option value="">Активность</option>
            <option value="true">Активные</option>
            <option value="false">Неактивные</option>
          </select>
        </div>

        <div v-if="loadingTemplates" class="dt-state">
          <i class="fas fa-spinner fa-spin"></i>
          Загрузка шаблонов...
        </div>
        <div v-else-if="!templates.length" class="dt-state">
          <i class="fas fa-file-circle-plus"></i>
          <strong>Шаблонов пока нет</strong>
          <span>Загрузите DOCX-файл, чтобы система извлекла плейсхолдеры.</span>
        </div>
        <div v-else class="dt-table-wrap">
          <table class="dt-table">
            <thead>
              <tr>
                <th>Шаблон</th>
                <th>Модуль</th>
                <th>Тип</th>
                <th>Область</th>
                <th>Поля</th>
                <th>Статус</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="template in templates"
                :key="template.id"
                :class="{ selected: selectedTemplate?.id === template.id }"
                @click="selectTemplate(template)"
              >
                <td>
                  <strong>{{ template.name }}</strong>
                  <small><i class="fas fa-paperclip"></i> {{ template.file_name || 'без файла' }}<span v-if="template.current_version_number"> · v{{ template.current_version_number }}</span></small>
                </td>
                <td>{{ optionLabel(meta.modules, template.module) }}</td>
                <td>{{ optionLabel(meta.document_kinds, template.document_kind) }}</td>
                <td><span class="dt-chip">{{ bindingLabel(template) }}</span></td>
                <td>
                  <b>{{ (template.fields || []).length }}</b>
                  <span v-if="(template.unknown_fields || []).length" class="dt-warn">+{{ template.unknown_fields.length }}</span>
                </td>
                <td>
                  <span class="dt-status" :class="`dt-status--${template.status || 'draft'}`">{{ optionLabel(meta.statuses, template.status) }}</span>
                  <span v-if="template.is_active" class="dt-active">Активен</span>
                </td>
                <td>
                  <div class="dt-actions">
                    <button title="Скачать" @click.stop="downloadTemplate(template)"><i class="fas fa-download"></i></button>
                    <button title="Редактировать" @click.stop="openEdit(template)"><i class="fas fa-pen"></i></button>
                    <button class="danger" title="Удалить" @click.stop="deleteTemplate(template)"><i class="fas fa-trash"></i></button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <aside class="dt-card dt-detail">
        <template v-if="selectedTemplate">
          <div class="dt-detail-head">
            <div>
              <div class="dt-kicker">Карточка шаблона</div>
              <h2>{{ selectedTemplate.name }}</h2>
            </div>
            <button class="dt-icon" @click="reloadSelectedTemplate"><i class="fas fa-sync"></i></button>
          </div>
          <p>{{ selectedTemplate.description || 'Описание не заполнено.' }}</p>
          <div class="dt-info">
            <div><span>Модуль</span><b>{{ optionLabel(meta.modules, selectedTemplate.module) }}</b></div>
            <div><span>Тип</span><b>{{ optionLabel(meta.document_kinds, selectedTemplate.document_kind) }}</b></div>
            <div><span>Наша компания</span><b>{{ ourCompanyLabel(selectedTemplate.our_company_key) }}</b></div>
            <div><span>Область</span><b>{{ bindingLabel(selectedTemplate) }}</b></div>
          </div>
          <div class="dt-section">
            <h3>Поля в шаблоне <span>{{ (selectedTemplate.fields || []).length }}</span></h3>
            <div v-if="!(selectedTemplate.fields || []).length" class="dt-muted">Плейсхолдеры не найдены.</div>
            <div v-else class="dt-pills">
              <button
                v-for="field in selectedTemplate.fields"
                :key="placeholderKey(field)"
                @click="copyKey(placeholderKey(field))"
              >
                {{ placeholderKey(field) }}
              </button>
            </div>
          </div>
          <div v-if="(selectedTemplate.unknown_fields || []).length" class="dt-section">
            <h3 class="warning">Неизвестные поля <span>{{ selectedTemplate.unknown_fields.length }}</span></h3>
            <div class="dt-pills">
              <button
                v-for="field in selectedTemplate.unknown_fields"
                :key="placeholderKey(field)"
                class="warning"
                @click="copyKey(placeholderKey(field))"
              >
                {{ placeholderKey(field) }}
              </button>
            </div>
          </div>
          <div class="dt-section">
            <h3>Версии <span>{{ (selectedTemplate.versions || []).length }}</span></h3>
            <div v-for="version in selectedTemplate.versions || []" :key="version.id" class="dt-version">
              <div><b>v{{ version.version_number }}</b> {{ version.file_name }}</div>
              <button class="dt-icon" @click="downloadTemplate(selectedTemplate, version)"><i class="fas fa-download"></i></button>
            </div>
          </div>
        </template>
        <div v-else class="dt-state">
          <i class="fas fa-arrow-pointer"></i>
          <strong>Выберите шаблон</strong>
          <span>Здесь появятся поля, неизвестные плейсхолдеры и версии.</span>
        </div>
      </aside>
    </section>

    <section v-else class="dt-card">
      <div class="dt-toolbar dt-toolbar--fields">
        <label class="dt-search">
          <i class="fas fa-search"></i>
          <input v-model.trim="fieldFilters.search" placeholder="Поиск по идентификатору, названию, описанию..." @input="debouncedLoadFields">
        </label>
        <select v-model="fieldFilters.module" @change="loadFields">
          <option value="">Все модули</option>
          <option v-for="item in meta.modules" :key="item.value" :value="item.value">{{ item.label }}</option>
        </select>
        <select v-model="fieldFilters.document_kind" @change="loadFields">
          <option value="">Все типы</option>
          <option v-for="item in filteredFieldDocumentKinds" :key="item.value" :value="item.value">{{ item.label }}</option>
        </select>
        <select v-model="fieldFilters.group" @change="loadFields">
          <option value="">Все группы</option>
          <option v-for="group in fieldGroups" :key="group" :value="group">{{ group }}</option>
        </select>
      </div>
      <div v-if="loadingFields" class="dt-state"><i class="fas fa-spinner fa-spin"></i> Загрузка справочника...</div>
      <div v-else class="dt-fields">
        <article v-for="field in fields" :key="field.key" class="dt-field">
          <div class="dt-field-head">
            <div>
              <span>{{ field.group }}</span>
              <h3>{{ field.label }}</h3>
            </div>
            <button class="dt-icon" @click="copyKey(field.key)"><i class="fas fa-copy"></i></button>
          </div>
          <code>{{ placeholderLabel(field.key) }}</code>
          <p>{{ field.description }}</p>
          <div class="dt-field-meta">
            <span>{{ typeLabel(field.type) }}</span>
            <span v-if="field.example">Пример: {{ field.example }}</span>
          </div>
          <div v-if="(field.requires || []).length" class="dt-requires">
            <span v-for="req in field.requires" :key="req">{{ req }}</span>
          </div>
        </article>
      </div>
    </section>

    <div v-if="showModal" class="dt-modal-overlay" v-modal-close="closeModal">
      <form class="dt-modal" @submit.prevent="saveTemplate" @click.stop>
        <div class="dt-modal-head">
          <div>
            <div class="dt-kicker">{{ editingTemplate ? 'Редактирование' : 'Новый шаблон' }}</div>
            <h2>{{ editingTemplate ? form.name : 'Загрузка DOCX-шаблона' }}</h2>
          </div>
          <button type="button" class="dt-icon" @click="closeModal"><i class="fas fa-times"></i></button>
        </div>
        <div class="dt-form">
          <label class="wide"><span>Название *</span><input v-model.trim="form.name" required></label>
          <label><span>Модуль</span><select v-model="form.module"><option v-for="item in meta.modules" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
          <label><span>Тип документа</span><select v-model="form.document_kind"><option v-for="item in modalDocumentKinds" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
          <label><span>Статус</span><select v-model="form.status"><option v-for="item in meta.statuses" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
          <label><span>Наша компания</span><select v-model="form.our_company_key"><option value="">Любая</option><option v-for="company in ourCompanies" :key="company.key" :value="company.key">{{ company.label }}</option></select></label>
          <label><span>Привязка</span><select v-model="form.binding_type"><option v-for="item in meta.bindings" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
          <label><span>ID привязки</span><input v-model.trim="form.binding_id" placeholder="UUID сделки/договора/контрагента"></label>
          <label class="wide"><span>Описание</span><textarea v-model.trim="form.description" rows="3"></textarea></label>
          <label class="dt-file wide">
            <input type="file" accept=".docx" :required="!editingTemplate" @change="onFileChange">
            <i class="fas fa-file-arrow-up"></i>
            <b>{{ selectedFile ? selectedFile.name : 'Выберите DOCX-файл' }}</b>
            <small>{{ editingTemplate ? 'Новый файл создаст новую версию.' : 'Система извлечет плейсхолдеры при загрузке.' }}</small>
          </label>
          <label class="dt-check wide">
            <input v-model="form.is_active" type="checkbox">
            <span>Сделать активным для выбранной области. Старый активный шаблон в этой области будет отключен.</span>
          </label>
        </div>
        <div class="dt-modal-actions">
          <button type="button" class="dt-btn" @click="closeModal">Отмена</button>
          <button type="submit" class="dt-btn dt-btn--primary" :disabled="saving">
            <i v-if="saving" class="fas fa-spinner fa-spin"></i>
            Сохранить
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { computed, onMounted, ref, watch } from 'vue'
import * as documentTemplatesApi from '../services/api/documentTemplates'
import { useToast } from '../composables/useToast'
import { staticOurCompanies } from '../config/appVariant'

const createEmptyMeta = () => ({ modules: [], document_kinds: [], statuses: [], bindings: [] })

export default {
  name: 'DocumentTemplates',
  setup() {
    const toast = useToast()
    const activeTab = ref('templates')
    const meta = ref(createEmptyMeta())
    const templates = ref([])
    const selectedTemplate = ref(null)
    const fields = ref([])
    const fieldGroups = ref([])
    const loadingTemplates = ref(false)
    const loadingFields = ref(false)
    const saving = ref(false)
    const showModal = ref(false)
    const editingTemplate = ref(null)
    const selectedFile = ref(null)
    const templateTimer = ref(null)
    const fieldTimer = ref(null)

    const templateFilters = ref({ search: '', module: '', document_kind: '', status: '', active: '' })
    const fieldFilters = ref({ search: '', module: '', document_kind: '', group: '' })
    const form = ref({
      name: '',
      description: '',
      module: 'outgoing_registry',
      document_kind: 'letter',
      status: 'draft',
      is_active: false,
      our_company_key: '',
      binding_type: 'global',
      binding_id: ''
    })

    const ourCompanies = computed(() => staticOurCompanies)
    const filteredDocumentKinds = computed(() => {
      if (!templateFilters.value.module) return meta.value.document_kinds
      return meta.value.document_kinds.filter(item => item.module === templateFilters.value.module)
    })
    const filteredFieldDocumentKinds = computed(() => {
      if (!fieldFilters.value.module) return meta.value.document_kinds
      return meta.value.document_kinds.filter(item => item.module === fieldFilters.value.module)
    })
    const modalDocumentKinds = computed(() => meta.value.document_kinds.filter(item => item.module === form.value.module))

    watch(() => templateFilters.value.module, () => {
      if (!filteredDocumentKinds.value.some(item => item.value === templateFilters.value.document_kind)) {
        templateFilters.value.document_kind = ''
      }
    })
    watch(() => fieldFilters.value.module, () => {
      if (!filteredFieldDocumentKinds.value.some(item => item.value === fieldFilters.value.document_kind)) {
        fieldFilters.value.document_kind = ''
      }
    })
    watch(() => form.value.module, () => {
      if (!modalDocumentKinds.value.some(item => item.value === form.value.document_kind)) {
        form.value.document_kind = modalDocumentKinds.value[0]?.value || 'letter'
      }
    })

    const optionLabel = (options, value) => options.find(item => item.value === value)?.label || value || '—'
    const ourCompanyLabel = (key) => {
      if (!key) return 'Любая'
      return ourCompanies.value.find(item => item.key === key)?.label || key
    }
    const bindingLabel = (template) => {
      const label = optionLabel(meta.value.bindings, template.binding_type)
      return template.binding_id ? `${label}: ${template.binding_id}` : label
    }
    const placeholderKey = (item) => (typeof item === 'string' ? item : item?.key || '')
    const placeholderLabel = (key) => `{{ ${key} }}`
    const typeLabel = (type) => ({
      string: 'Текст',
      date: 'Дата',
      money: 'Сумма',
      block: 'Повторяемый блок'
    }[type] || type || 'Поле')

    const loadMeta = async () => {
      const result = await documentTemplatesApi.getMeta()
      meta.value = result || createEmptyMeta()
    }

    const loadTemplates = async () => {
      loadingTemplates.value = true
      try {
        const result = await documentTemplatesApi.list({
          search: templateFilters.value.search || undefined,
          module: templateFilters.value.module || undefined,
          document_kind: templateFilters.value.document_kind || undefined,
          status: templateFilters.value.status || undefined,
          active: templateFilters.value.active || undefined,
          limit: 100
        })
        templates.value = result || []
        if (selectedTemplate.value && !templates.value.some(item => item.id === selectedTemplate.value.id)) {
          selectedTemplate.value = null
        }
      } catch (error) {
        console.error('Document templates load error:', error)
        toast.error('Не удалось загрузить шаблоны')
      } finally {
        loadingTemplates.value = false
      }
    }

    const loadFields = async () => {
      loadingFields.value = true
      try {
        const result = await documentTemplatesApi.listFields({
          search: fieldFilters.value.search || undefined,
          module: fieldFilters.value.module || undefined,
          document_kind: fieldFilters.value.document_kind || undefined,
          group: fieldFilters.value.group || undefined
        })
        fields.value = result || []
      } catch (error) {
        console.error('Template fields load error:', error)
        toast.error('Не удалось загрузить справочник полей')
      } finally {
        loadingFields.value = false
      }
    }

    const loadFieldGroups = async () => {
      const result = await documentTemplatesApi.listFieldGroups()
      fieldGroups.value = result || []
    }

    const debouncedLoadTemplates = () => {
      clearTimeout(templateTimer.value)
      templateTimer.value = setTimeout(loadTemplates, 250)
    }
    const debouncedLoadFields = () => {
      clearTimeout(fieldTimer.value)
      fieldTimer.value = setTimeout(loadFields, 250)
    }

    const selectTemplate = async (template) => {
      try {
        const result = await documentTemplatesApi.getById(template.id)
        selectedTemplate.value = result
      } catch (error) {
        console.error('Template detail error:', error)
        toast.error('Не удалось открыть шаблон')
      }
    }
    const reloadSelectedTemplate = async () => {
      if (selectedTemplate.value) await selectTemplate(selectedTemplate.value)
    }

    const resetForm = () => {
      form.value = {
        name: '',
        description: '',
        module: 'outgoing_registry',
        document_kind: 'letter',
        status: 'draft',
        is_active: false,
        our_company_key: '',
        binding_type: 'global',
        binding_id: ''
      }
      selectedFile.value = null
    }
    const openCreate = () => {
      editingTemplate.value = null
      resetForm()
      showModal.value = true
    }
    const openEdit = (template) => {
      const source = selectedTemplate.value?.id === template.id ? selectedTemplate.value : template
      editingTemplate.value = source
      form.value = {
        name: source.name || '',
        description: source.description || '',
        module: source.module || 'outgoing_registry',
        document_kind: source.document_kind || 'letter',
        status: source.status || 'draft',
        is_active: Boolean(source.is_active),
        our_company_key: source.our_company_key || '',
        binding_type: source.binding_type || 'global',
        binding_id: source.binding_id || ''
      }
      selectedFile.value = null
      showModal.value = true
    }
    const closeModal = () => {
      if (saving.value) return
      showModal.value = false
      editingTemplate.value = null
      resetForm()
    }
    const onFileChange = (event) => {
      selectedFile.value = event.target.files?.[0] || null
    }

    const buildFormData = () => {
      const data = new FormData()
      data.append('name', form.value.name)
      data.append('description', form.value.description || '')
      data.append('module', form.value.module)
      data.append('document_kind', form.value.document_kind)
      data.append('status', form.value.status)
      data.append('is_active', String(Boolean(form.value.is_active)))
      data.append('our_company_key', form.value.our_company_key || '')
      data.append('binding_type', form.value.binding_type)
      data.append('binding_id', form.value.binding_id || '')
      if (selectedFile.value) data.append('file', selectedFile.value)
      return data
    }

    const saveTemplate = async () => {
      if (!editingTemplate.value && !selectedFile.value) {
        toast.warning('Выберите DOCX-файл')
        return
      }
      saving.value = true
      try {
        let saved = null
        if (editingTemplate.value) {
          const payload = {
            name: form.value.name,
            description: form.value.description || null,
            module: form.value.module,
            document_kind: form.value.document_kind,
            status: form.value.status,
            is_active: Boolean(form.value.is_active),
            our_company_key: form.value.our_company_key || null,
            binding_type: form.value.binding_type,
            binding_id: form.value.binding_id || null
          }
          saved = await documentTemplatesApi.update(editingTemplate.value.id, payload)
          if (selectedFile.value) {
            const fileData = new FormData()
            fileData.append('file', selectedFile.value)
            saved = await documentTemplatesApi.uploadVersion(editingTemplate.value.id, fileData)
          }
        } else {
          saved = await documentTemplatesApi.create(buildFormData())
        }
        toast.success('Шаблон сохранен')
        closeModal()
        await loadTemplates()
        if (saved?.id) await selectTemplate(saved)
      } catch (error) {
        console.error('Template save error:', error)
        toast.error(error.response?.data?.detail || 'Не удалось сохранить шаблон')
      } finally {
        saving.value = false
      }
    }

    const deleteTemplate = async (template) => {
      if (!confirm(`Удалить шаблон "${template.name}"?`)) return
      try {
        await documentTemplatesApi.remove(template.id)
        if (selectedTemplate.value?.id === template.id) selectedTemplate.value = null
        await loadTemplates()
        toast.success('Шаблон удален')
      } catch (error) {
        console.error('Template delete error:', error)
        toast.error('Не удалось удалить шаблон')
      }
    }

    const parseFilename = (headers, fallback) => {
      const disposition = headers?.['content-disposition'] || ''
      const utf = disposition.match(/filename\*=UTF-8''([^;]+)/i)
      if (utf) return decodeURIComponent(utf[1])
      const ascii = disposition.match(/filename="?([^"]+)"?/i)
      return ascii?.[1] || fallback || 'template.docx'
    }
    const downloadTemplate = async (template, version = null) => {
      try {
        const response = await documentTemplatesApi.download(
          template.id,
          version?.id ? { version_id: version.id } : {}
        )
        const link = document.createElement('a')
        const url = URL.createObjectURL(response.data)
        link.href = url
        link.download = parseFilename(response.headers, version?.file_name || template.file_name)
        document.body.appendChild(link)
        link.click()
        link.remove()
        URL.revokeObjectURL(url)
      } catch (error) {
        console.error('Template download error:', error)
        toast.error('Не удалось скачать шаблон')
      }
    }

    const copyKey = async (key) => {
      try {
        await navigator.clipboard.writeText(key)
        toast.success('Идентификатор скопирован')
      } catch (error) {
        console.error('Clipboard error:', error)
        toast.warning(key)
      }
    }

    onMounted(async () => {
      await Promise.all([loadMeta(), loadFieldGroups()])
      await Promise.all([loadTemplates(), loadFields()])
    })

    return {
      activeTab,
      meta,
      templates,
      selectedTemplate,
      fields,
      fieldGroups,
      loadingTemplates,
      loadingFields,
      saving,
      showModal,
      editingTemplate,
      selectedFile,
      templateFilters,
      fieldFilters,
      form,
      ourCompanies,
      filteredDocumentKinds,
      filteredFieldDocumentKinds,
      modalDocumentKinds,
      optionLabel,
      ourCompanyLabel,
      bindingLabel,
      placeholderKey,
      placeholderLabel,
      typeLabel,
      loadTemplates,
      loadFields,
      debouncedLoadTemplates,
      debouncedLoadFields,
      selectTemplate,
      reloadSelectedTemplate,
      openCreate,
      openEdit,
      closeModal,
      onFileChange,
      saveTemplate,
      deleteTemplate,
      downloadTemplate,
      copyKey
    }
  }
}
</script>

<style scoped>
.document-templates-view {
  padding: 18px;
  min-height: calc(100vh - 80px);
  color: #172033;
}

.dt-header,
.dt-card,
.dt-tabs {
  border: 1px solid rgba(148, 163, 184, 0.28);
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(14px);
}

.dt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  border-radius: 22px;
  padding: 20px 22px;
}

.dt-header h1,
.dt-detail h2,
.dt-modal h2 {
  margin: 0;
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.dt-header p,
.dt-detail p,
.dt-muted {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 14px;
}

.dt-kicker {
  color: #2563eb;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.dt-tabs {
  display: inline-flex;
  margin: 14px 0;
  border-radius: 16px;
  padding: 5px;
}

.dt-tabs button {
  border: 0;
  background: transparent;
  border-radius: 12px;
  padding: 10px 16px;
  color: #64748b;
  font-weight: 800;
  cursor: pointer;
}

.dt-tabs button.active {
  background: #0f172a;
  color: #fff;
}

.dt-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(360px, 0.7fr);
  gap: 14px;
}

.dt-card {
  border-radius: 22px;
  overflow: hidden;
}

.dt-detail {
  padding: 18px;
}

.dt-toolbar {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) 170px 170px 150px 130px;
  gap: 10px;
  padding: 14px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.22);
}

.dt-toolbar--fields {
  grid-template-columns: minmax(280px, 1fr) 180px 200px 190px;
}

.dt-search {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 38px;
  border: 1px solid #dbe3ef;
  border-radius: 12px;
  padding: 0 12px;
  background: #fff;
  color: #94a3b8;
}

.dt-search input,
.dt-toolbar select,
.dt-form input,
.dt-form select,
.dt-form textarea {
  width: 100%;
  border: 1px solid #dbe3ef;
  border-radius: 12px;
  background: #fff;
  color: #172033;
  outline: none;
}

.dt-search input {
  min-height: 36px;
  border: 0;
}

.dt-toolbar select,
.dt-form input,
.dt-form select {
  min-height: 38px;
  padding: 0 10px;
}

.dt-form textarea {
  min-height: 78px;
  padding: 10px;
  resize: vertical;
}

.dt-table-wrap {
  overflow: auto;
}

.dt-table {
  width: 100%;
  border-collapse: collapse;
}

.dt-table th {
  padding: 12px 14px;
  background: #f8fafc;
  color: #64748b;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-align: left;
  text-transform: uppercase;
}

.dt-table td {
  padding: 13px 14px;
  border-top: 1px solid rgba(148, 163, 184, 0.2);
  vertical-align: middle;
}

.dt-table tr {
  cursor: pointer;
}

.dt-table tr:hover,
.dt-table tr.selected {
  background: #f1f7ff;
}

.dt-table small {
  display: block;
  margin-top: 4px;
  color: #64748b;
}

.dt-chip,
.dt-status,
.dt-active,
.dt-field-meta span,
.dt-requires span {
  display: inline-flex;
  width: fit-content;
  border-radius: 999px;
  padding: 4px 9px;
  font-size: 11px;
  font-weight: 800;
}

.dt-chip,
.dt-field-meta span {
  background: #f1f5f9;
  color: #475569;
}

.dt-active {
  margin-top: 5px;
  background: #dcfce7;
  color: #15803d;
}

.dt-status--draft {
  background: #fef3c7;
  color: #a16207;
}

.dt-status--approved {
  background: #dcfce7;
  color: #15803d;
}

.dt-status--archived {
  background: #e2e8f0;
  color: #475569;
}

.dt-warn,
.warning {
  color: #d97706;
}

.dt-actions {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
}

.dt-actions button,
.dt-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid #dbe3ef;
  border-radius: 10px;
  background: #fff;
  color: #475569;
  cursor: pointer;
}

.dt-actions button:hover,
.dt-icon:hover {
  color: #2563eb;
  border-color: #bfdbfe;
  background: #eff6ff;
}

.dt-actions .danger:hover {
  color: #dc2626;
  border-color: #fecaca;
  background: #fff1f2;
}

.dt-state {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 10px;
  min-height: 360px;
  color: #64748b;
  text-align: center;
}

.dt-state i {
  color: #94a3b8;
  font-size: 40px;
}

.dt-detail-head,
.dt-section h3,
.dt-version,
.dt-field-head,
.dt-modal-head,
.dt-modal-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.dt-info {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}

.dt-info > div {
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 12px;
  background: #f8fafc;
}

.dt-info span {
  display: block;
  margin-bottom: 4px;
  color: #64748b;
  font-size: 11px;
}

.dt-section {
  margin-top: 18px;
}

.dt-section h3 {
  margin: 0 0 10px;
  font-size: 15px;
}

.dt-section h3 span {
  color: #64748b;
  font-size: 12px;
}

.dt-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.dt-pills button {
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  padding: 6px 10px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
  cursor: pointer;
}

.dt-pills button.warning {
  border-color: #fed7aa;
  background: #fff7ed;
  color: #c2410c;
}

.dt-version {
  margin-top: 8px;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 10px;
  background: #fff;
}

.dt-fields {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  padding: 14px;
}

.dt-field {
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  padding: 14px;
  background: #fff;
}

.dt-field-head span {
  color: #2563eb;
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
}

.dt-field h3 {
  margin: 4px 0 0;
  font-size: 15px;
}

.dt-field code {
  display: block;
  margin-top: 12px;
  border-radius: 10px;
  background: #0f172a;
  color: #dbeafe;
  padding: 9px 10px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dt-field p {
  min-height: 44px;
  color: #64748b;
  font-size: 13px;
  line-height: 1.45;
}

.dt-field-meta,
.dt-requires {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.dt-requires {
  margin-top: 8px;
}

.dt-requires span {
  background: #fff7ed;
  color: #c2410c;
}

.dt-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 40px;
  border: 0;
  border-radius: 12px;
  padding: 0 16px;
  background: #f1f5f9;
  color: #334155;
  font-weight: 800;
  cursor: pointer;
}

.dt-btn--primary {
  background: #2563eb;
  color: #fff;
}

.dt-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 2200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28px;
  background: rgba(15, 23, 42, 0.46);
  backdrop-filter: blur(8px);
}

.dt-modal {
  width: min(820px, 100%);
  max-height: calc(100vh - 56px);
  overflow: auto;
  border-radius: 24px;
  background: #fff;
  box-shadow: 0 28px 80px rgba(15, 23, 42, 0.24);
}

.dt-modal-head,
.dt-modal-actions {
  padding: 18px 20px;
  border-bottom: 1px solid #e2e8f0;
}

.dt-modal-actions {
  justify-content: flex-end;
  border-top: 1px solid #e2e8f0;
  border-bottom: 0;
}

.dt-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  padding: 18px 20px;
}

.dt-form label {
  display: grid;
  gap: 6px;
}

.dt-form label.wide {
  grid-column: 1 / -1;
}

.dt-form label > span {
  color: #64748b;
  font-size: 12px;
  font-weight: 800;
}

.dt-file {
  border: 1px dashed #93c5fd;
  border-radius: 16px;
  padding: 14px;
  background: #eff6ff;
  color: #1d4ed8;
  cursor: pointer;
}

.dt-file input {
  display: none;
}

.dt-file small {
  display: block;
  margin-top: 4px;
  color: #64748b;
}

.dt-check {
  display: flex !important;
  align-items: flex-start;
  flex-direction: row;
  color: #475569;
  font-size: 13px;
}

:global(:root[data-theme="dark"] .document-templates-view) {
  color: #f5f7fb;
}

:global(:root[data-theme="dark"] .document-templates-view .dt-header),
:global(:root[data-theme="dark"] .document-templates-view .dt-card),
:global(:root[data-theme="dark"] .document-templates-view .dt-tabs),
:global(:root[data-theme="dark"] .document-templates-view .dt-modal) {
  background: rgba(20, 24, 33, 0.92);
  border-color: rgba(255, 255, 255, 0.12);
  color: #f5f7fb;
  box-shadow: 0 20px 64px rgba(0, 0, 0, 0.2);
}

:global(:root[data-theme="dark"] .document-templates-view .dt-tabs button) {
  color: #a8b3c5;
}

:global(:root[data-theme="dark"] .document-templates-view .dt-tabs button.active) {
  background: #f5f7fb;
  color: #111827;
}

:global(:root[data-theme="dark"] .document-templates-view .dt-search),
:global(:root[data-theme="dark"] .document-templates-view .dt-search input),
:global(:root[data-theme="dark"] .document-templates-view .dt-toolbar select),
:global(:root[data-theme="dark"] .document-templates-view .dt-form input),
:global(:root[data-theme="dark"] .document-templates-view .dt-form select),
:global(:root[data-theme="dark"] .document-templates-view .dt-form textarea),
:global(:root[data-theme="dark"] .document-templates-view .dt-field),
:global(:root[data-theme="dark"] .document-templates-view .dt-version),
:global(:root[data-theme="dark"] .document-templates-view .dt-info > div),
:global(:root[data-theme="dark"] .document-templates-view .dt-icon),
:global(:root[data-theme="dark"] .document-templates-view .dt-actions button) {
  background: rgba(12, 16, 24, 0.82);
  border-color: rgba(255, 255, 255, 0.1);
  color: #f5f7fb;
}

:global(:root[data-theme="dark"] .document-templates-view .dt-search input::placeholder),
:global(:root[data-theme="dark"] .document-templates-view .dt-form input::placeholder),
:global(:root[data-theme="dark"] .document-templates-view .dt-form textarea::placeholder) {
  color: #7d8a9f;
}

:global(:root[data-theme="dark"] .document-templates-view .dt-table th) {
  background: rgba(12, 16, 24, 0.9);
  color: #a8b3c5;
}

:global(:root[data-theme="dark"] .document-templates-view .dt-table td),
:global(:root[data-theme="dark"] .document-templates-view .dt-toolbar),
:global(:root[data-theme="dark"] .document-templates-view .dt-modal-head),
:global(:root[data-theme="dark"] .document-templates-view .dt-modal-actions) {
  border-color: rgba(255, 255, 255, 0.1);
}

:global(:root[data-theme="dark"] .document-templates-view .dt-table tr:hover),
:global(:root[data-theme="dark"] .document-templates-view .dt-table tr.selected) {
  background: rgba(37, 99, 235, 0.18);
}

:global(:root[data-theme="dark"] .document-templates-view .dt-table small),
:global(:root[data-theme="dark"] .document-templates-view .dt-header p),
:global(:root[data-theme="dark"] .document-templates-view .dt-detail p),
:global(:root[data-theme="dark"] .document-templates-view .dt-field p),
:global(:root[data-theme="dark"] .document-templates-view .dt-muted),
:global(:root[data-theme="dark"] .document-templates-view .dt-info span),
:global(:root[data-theme="dark"] .document-templates-view .dt-section h3 span),
:global(:root[data-theme="dark"] .document-templates-view .dt-form label > span),
:global(:root[data-theme="dark"] .document-templates-view .dt-file small),
:global(:root[data-theme="dark"] .document-templates-view .dt-check) {
  color: #a8b3c5;
}

:global(:root[data-theme="dark"] .document-templates-view .dt-chip),
:global(:root[data-theme="dark"] .document-templates-view .dt-field-meta span) {
  background: rgba(148, 163, 184, 0.16);
  color: #d6deea;
}

:global(:root[data-theme="dark"] .document-templates-view .dt-status--draft) {
  background: rgba(245, 158, 11, 0.18);
  color: #fbbf24;
}

:global(:root[data-theme="dark"] .document-templates-view .dt-status--approved),
:global(:root[data-theme="dark"] .document-templates-view .dt-active) {
  background: rgba(34, 197, 94, 0.16);
  color: #86efac;
}

:global(:root[data-theme="dark"] .document-templates-view .dt-status--archived) {
  background: rgba(148, 163, 184, 0.16);
  color: #cbd5e1;
}

:global(:root[data-theme="dark"] .document-templates-view .dt-pills button) {
  border-color: rgba(96, 165, 250, 0.35);
  background: rgba(37, 99, 235, 0.16);
  color: #bfdbfe;
}

:global(:root[data-theme="dark"] .document-templates-view .dt-pills button.warning),
:global(:root[data-theme="dark"] .document-templates-view .dt-requires span) {
  border-color: rgba(251, 146, 60, 0.34);
  background: rgba(194, 65, 12, 0.16);
  color: #fdba74;
}

:global(:root[data-theme="dark"] .document-templates-view .dt-field code) {
  background: rgba(2, 6, 23, 0.86);
  color: #bfdbfe;
}

:global(:root[data-theme="dark"] .document-templates-view .dt-file) {
  border-color: rgba(96, 165, 250, 0.42);
  background: rgba(37, 99, 235, 0.14);
  color: #bfdbfe;
}

:global(:root[data-theme="dark"] .document-templates-view .dt-btn) {
  background: rgba(255, 255, 255, 0.08);
  color: #f5f7fb;
}

:global(:root[data-theme="dark"] .document-templates-view .dt-btn--primary) {
  background: #2563eb;
  color: #fff;
}

:global(:root[data-theme="dark"] .document-templates-view .dt-actions button:hover),
:global(:root[data-theme="dark"] .document-templates-view .dt-icon:hover) {
  color: #93c5fd;
  border-color: rgba(96, 165, 250, 0.38);
  background: rgba(37, 99, 235, 0.16);
}

:global(:root[data-theme="dark"] .document-templates-view .dt-actions .danger:hover) {
  color: #fca5a5;
  border-color: rgba(248, 113, 113, 0.34);
  background: rgba(220, 38, 38, 0.14);
}

@media (max-width: 1180px) {
  .dt-grid,
  .dt-toolbar,
  .dt-toolbar--fields,
  .dt-fields {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 720px) {
  .dt-header,
  .dt-grid,
  .dt-toolbar,
  .dt-toolbar--fields,
  .dt-fields,
  .dt-info,
  .dt-form {
    grid-template-columns: 1fr;
  }

  .dt-header {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
