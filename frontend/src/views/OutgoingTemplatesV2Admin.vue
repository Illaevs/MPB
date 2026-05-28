<template>
  <div class="tpl-admin">
    <!-- LEFT: template list -->
    <aside class="tpl-admin__list">
      <header class="tpl-admin__list-head">
        <span>Шаблоны v2</span>
        <button class="tpl-btn tpl-btn--primary" title="Новый шаблон" @click="newTemplate">
          <i class="fas fa-plus"></i>
        </button>
      </header>
      <div class="tpl-admin__list-body">
        <div v-if="listLoading" class="tpl-admin__muted">Загрузка…</div>
        <template v-else>
          <div v-for="kind in kinds" :key="kind.value" class="tpl-admin__group">
            <div class="tpl-admin__group-label">{{ kind.label }}</div>
            <button
              v-for="t in templatesByKind(kind.value)"
              :key="t.id"
              class="tpl-item"
              :class="{ 'tpl-item--active': form.id === t.id }"
              @click="openTemplate(t.id)"
            >
              {{ t.name }}
            </button>
            <div v-if="!templatesByKind(kind.value).length" class="tpl-admin__muted tpl-admin__muted--sm">—</div>
          </div>
        </template>
      </div>
    </aside>

    <!-- CENTER: editor -->
    <main class="tpl-admin__editor">
      <header class="tpl-admin__editor-head">
        <h2>{{ form.id ? 'Редактирование шаблона' : 'Новый шаблон' }}</h2>
        <div class="tpl-admin__actions">
          <button
            v-if="form.id"
            class="tpl-btn tpl-btn--danger"
            @click="removeTemplate"
          ><i class="fas fa-trash mr-1"></i>Удалить</button>
          <button class="tpl-btn tpl-btn--primary" :disabled="saving" @click="save">
            <i class="fas mr-1" :class="saving ? 'fa-spinner fa-spin' : 'fa-check'"></i>
            {{ saving ? 'Сохранение…' : 'Сохранить' }}
          </button>
        </div>
      </header>

      <div v-if="msg" class="tpl-admin__msg" :class="{ 'tpl-admin__msg--err': msgErr }">{{ msg }}</div>

      <div class="tpl-admin__scroll">
        <!-- Meta -->
        <div class="tpl-row">
          <label class="tpl-field tpl-field--grow">
            <span>Название</span>
            <input v-model="form.name" type="text" class="tpl-input" placeholder="Напр. Письмо-уведомление (v2)" />
          </label>
          <label class="tpl-field">
            <span>Тип документа</span>
            <select v-model="form.document_kind" class="tpl-input">
              <option v-for="k in kinds" :key="k.value" :value="k.value">{{ k.label }}</option>
            </select>
          </label>
        </div>

        <!-- Layout HTML -->
        <label class="tpl-field">
          <span>
            HTML-вёрстка
            <small>data-locked — статичный текст · data-placeholder="key" — чип · data-editable="body" — редактируемая зона · data-table="stages|payments" — таблица</small>
          </span>
          <textarea
            v-model="form.layout_html"
            class="tpl-textarea tpl-textarea--code"
            rows="14"
            spellcheck="false"
          ></textarea>
        </label>

        <!-- Placeholder fields -->
        <div class="tpl-field">
          <span>
            Поля параметров
            <button class="tpl-btn tpl-btn--ghost tpl-btn--xs" @click="addField">
              <i class="fas fa-plus"></i> поле
            </button>
          </span>
          <div class="tpl-fields">
            <div class="tpl-fields__head">
              <span>key</span><span>Подпись</span><span>Тип</span><span>Роль</span><span>Группа</span><span></span>
            </div>
            <div v-for="(f, i) in form.placeholder_fields" :key="i" class="tpl-fields__row">
              <input v-model="f.key" class="tpl-input tpl-input--sm" placeholder="recipient.name" />
              <input v-model="f.label" class="tpl-input tpl-input--sm" placeholder="Контрагент" />
              <select v-model="f.type" class="tpl-input tpl-input--sm">
                <option v-for="t in FIELD_TYPES" :key="t" :value="t">{{ t }}</option>
              </select>
              <select v-model="f.role" class="tpl-input tpl-input--sm">
                <option value="anchor">anchor</option>
                <option value="resolved">resolved</option>
              </select>
              <input v-model="f.group" class="tpl-input tpl-input--sm" placeholder="parties" />
              <button class="tpl-btn tpl-btn--ghost tpl-btn--xs" title="Удалить" @click="form.placeholder_fields.splice(i, 1)">
                <i class="fas fa-times"></i>
              </button>
            </div>
            <div v-if="!form.placeholder_fields.length" class="tpl-admin__muted tpl-admin__muted--sm">Полей нет</div>
          </div>
        </div>
      </div>
    </main>

    <!-- RIGHT: live preview -->
    <section class="tpl-admin__preview">
      <header class="tpl-admin__preview-head">Предпросмотр</header>
      <div class="tpl-admin__preview-body">
        <OutgoingTemplateRenderer
          v-if="form.layout_html"
          :key="previewKey"
          :layout-html="form.layout_html"
          :placeholder-fields="form.placeholder_fields"
          :field-values="{}"
          :resolved-context="{}"
          :editable-content="{}"
        />
        <div v-else class="tpl-admin__muted">Добавьте HTML-вёрстку</div>
      </div>
    </section>
  </div>
</template>

<script>
import { computed, onMounted, ref } from 'vue'
import OutgoingTemplateRenderer from './outgoing/templateV2/OutgoingTemplateRenderer.vue'
import {
  listTemplatesV2,
  getTemplateV2,
  createTemplateV2,
  updateTemplateV2,
  deleteTemplateV2,
} from '../services/api/outgoing'

const KINDS = [
  { value: 'letter', label: 'Письмо' },
  { value: 'invoice', label: 'Счёт' },
  { value: 'upd', label: 'УПД' },
  { value: 'act', label: 'Акт' },
  { value: 'vat_invoice', label: 'Счёт-фактура' },
]
const FIELD_TYPES = [
  'text', 'date', 'money',
  'company-select', 'our-company-select', 'deal-select', 'contract-select',
  'bank-account-select', 'stage-multiselect', 'payment-rows',
]
const blankForm = () => ({
  id: null,
  name: '',
  document_kind: 'letter',
  layout_html: '<header><h1 data-locked="true">ЗАГОЛОВОК</h1></header>\n<section data-editable="body"><p></p></section>',
  placeholder_fields: [],
  editable_regions: [{ key: 'body', label: 'Текст документа',
    allowed_marks: ['bold', 'italic', 'underline', 'list', 'alignment', 'link'], default_html: '<p></p>' }],
})

export default {
  name: 'OutgoingTemplatesV2Admin',
  components: { OutgoingTemplateRenderer },
  setup() {
    const templates = ref([])
    const listLoading = ref(false)
    const saving = ref(false)
    const form = ref(blankForm())
    const msg = ref('')
    const msgErr = ref(false)
    const previewKey = ref(0)

    const flash = (text, err = false) => {
      msg.value = text; msgErr.value = err
      if (text) setTimeout(() => { if (msg.value === text) msg.value = '' }, 3500)
    }

    const loadList = async () => {
      listLoading.value = true
      try {
        templates.value = (await listTemplatesV2({})) || []
      } catch (e) {
        flash(e?.response?.data?.detail || 'Не удалось загрузить список', true)
      } finally {
        listLoading.value = false
      }
    }
    const templatesByKind = (kind) => templates.value.filter((t) => t.document_kind === kind)

    const openTemplate = async (id) => {
      try {
        const t = await getTemplateV2(id)
        form.value = {
          id: t.id,
          name: t.name,
          document_kind: t.document_kind,
          layout_html: t.layout_html || '',
          placeholder_fields: (t.placeholder_fields || []).map((f) => ({
            key: f.key || '', label: f.label || '', type: f.type || 'text',
            role: f.role || 'resolved', group: f.group || '',
          })),
          editable_regions: t.editable_regions && t.editable_regions.length
            ? t.editable_regions : blankForm().editable_regions,
        }
        previewKey.value++
      } catch (e) {
        flash(e?.response?.data?.detail || 'Не удалось открыть шаблон', true)
      }
    }
    const newTemplate = () => { form.value = blankForm(); previewKey.value++ }
    const addField = () => {
      form.value.placeholder_fields.push({ key: '', label: '', type: 'text', role: 'resolved', group: '' })
    }

    const save = async () => {
      if (!form.value.name.trim()) { flash('Укажите название', true); return }
      saving.value = true
      try {
        const payload = {
          name: form.value.name.trim(),
          document_kind: form.value.document_kind,
          layout_html: form.value.layout_html,
          placeholder_fields: form.value.placeholder_fields.filter((f) => f.key.trim()),
          editable_regions: form.value.editable_regions,
        }
        const saved = form.value.id
          ? await updateTemplateV2(form.value.id, payload)
          : await createTemplateV2(payload)
        form.value.id = saved.id
        await loadList()
        flash('Сохранено')
      } catch (e) {
        flash(e?.response?.data?.detail || e.message || 'Ошибка сохранения', true)
      } finally {
        saving.value = false
      }
    }

    const removeTemplate = async () => {
      if (!form.value.id) return
      if (!window.confirm('Удалить шаблон безвозвратно?')) return
      try {
        await deleteTemplateV2(form.value.id)
        await loadList()
        newTemplate()
        flash('Удалено')
      } catch (e) {
        flash(e?.response?.data?.detail || 'Не удалось удалить', true)
      }
    }

    onMounted(loadList)

    return {
      kinds: KINDS, FIELD_TYPES,
      templates, listLoading, saving, form, msg, msgErr, previewKey,
      templatesByKind, openTemplate, newTemplate, addField, save, removeTemplate,
    }
  }
}
</script>

<style scoped>
.tpl-admin {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr) 420px;
  height: 100%;
  background: var(--color-surface-2);
}
.tpl-admin__list, .tpl-admin__editor, .tpl-admin__preview {
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--color-surface);
}
.tpl-admin__list { border-right: 1px solid var(--color-border-subtle); }
.tpl-admin__preview { border-left: 1px solid var(--color-border-subtle); }

.tpl-admin__list-head,
.tpl-admin__editor-head,
.tpl-admin__preview-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--color-border-subtle);
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
}
.tpl-admin__editor-head h2 { margin: 0; font-size: var(--text-base); font-weight: var(--fw-bold); color: var(--color-text); text-transform: none; letter-spacing: 0; }
.tpl-admin__actions { display: inline-flex; gap: 8px; }

.tpl-admin__list-body { flex: 1; overflow-y: auto; padding: 8px; }
.tpl-admin__group { margin-bottom: 12px; }
.tpl-admin__group-label { font-size: var(--text-xs); color: var(--color-text-subtle); text-transform: uppercase; padding: 4px 8px; }
.tpl-item {
  display: block;
  width: 100%;
  text-align: left;
  padding: 8px 10px;
  border: 0;
  background: transparent;
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  color: var(--color-text);
  cursor: pointer;
}
.tpl-item:hover { background: var(--color-surface-2); }
.tpl-item--active { background: var(--color-primary-soft); color: var(--color-primary); font-weight: var(--fw-semibold); }
.tpl-admin__muted { color: var(--color-text-subtle); font-size: var(--text-sm); padding: 12px; text-align: center; }
.tpl-admin__muted--sm { padding: 4px 10px; text-align: left; }

.tpl-admin__scroll { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 16px; }
.tpl-row { display: flex; gap: 12px; }
.tpl-field { display: flex; flex-direction: column; gap: 6px; }
.tpl-field--grow { flex: 1; }
.tpl-field > span {
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  gap: 8px;
}
.tpl-field > span small { font-weight: var(--fw-regular); text-transform: none; letter-spacing: 0; color: var(--color-text-subtle); }

.tpl-input {
  height: 36px;
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: var(--text-sm);
}
.tpl-input--sm { height: 30px; font-size: var(--text-xs); }
.tpl-input:focus { outline: none; border-color: var(--color-primary); box-shadow: var(--shadow-focus); }

.tpl-textarea {
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: var(--text-sm);
  resize: vertical;
}
.tpl-textarea--code { font-family: var(--font-mono, ui-monospace, monospace); font-size: 12px; line-height: 1.5; }
.tpl-textarea:focus { outline: none; border-color: var(--color-primary); box-shadow: var(--shadow-focus); }

.tpl-fields { display: flex; flex-direction: column; gap: 6px; }
.tpl-fields__head,
.tpl-fields__row {
  display: grid;
  grid-template-columns: 1.4fr 1.4fr 1.3fr 0.9fr 1fr 28px;
  gap: 6px;
  align-items: center;
}
.tpl-fields__head { font-size: var(--text-xs); color: var(--color-text-subtle); padding: 0 2px; }

.tpl-btn {
  display: inline-flex;
  align-items: center;
  height: 32px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: var(--text-sm);
  cursor: pointer;
}
.tpl-btn:hover { background: var(--color-surface-2); }
.tpl-btn--primary { background: var(--color-primary); border-color: var(--color-primary); color: #fff; }
.tpl-btn--primary:hover:not(:disabled) { background: var(--color-primary-hover, #2f6fe0); }
.tpl-btn--primary:disabled { opacity: 0.6; cursor: not-allowed; }
.tpl-btn--danger { color: var(--color-danger); border-color: var(--color-danger); background: transparent; }
.tpl-btn--danger:hover { background: var(--color-danger-soft); }
.tpl-btn--ghost { border: 0; background: transparent; height: auto; padding: 2px 6px; }
.tpl-btn--xs { height: 22px; padding: 0 6px; font-size: var(--text-xs); }

.tpl-admin__msg {
  margin: 0 16px;
  margin-top: 12px;
  padding: 8px 12px;
  border-radius: var(--radius-md);
  background: var(--color-success-soft);
  color: var(--color-success);
  font-size: var(--text-sm);
}
.tpl-admin__msg--err { background: var(--color-danger-soft); color: var(--color-danger); }

.tpl-admin__preview-body { flex: 1; overflow: auto; padding: 16px; background: var(--color-surface-2); }
</style>
