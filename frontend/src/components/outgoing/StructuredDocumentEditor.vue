<template>
  <div class="structured-editor">
    <div class="structured-editor__header">
      <div>
        <div class="structured-editor__title">Конструктор документа</div>
        <div class="structured-editor__subtitle">Структурированный draft для шаблонов, печатных форм и будущего AI-ассистента.</div>
      </div>
      <div class="structured-editor__actions">
        <button
          v-for="block in quickAddBlocks"
          :key="block.type"
          class="structured-editor__quick-add"
          type="button"
          :disabled="disabled"
          @click="addBlock(block.type)"
        >
          <i class="fas fa-plus"></i>
          {{ block.label }}
        </button>
      </div>
    </div>

    <div v-if="validationErrors.length || validationWarnings.length" class="structured-editor__alerts">
      <div v-for="(item, index) in validationErrors" :key="`error-${index}`" class="structured-editor__alert structured-editor__alert--error">
        <i class="fas fa-exclamation-circle"></i>
        <span>{{ item }}</span>
      </div>
      <div v-for="(item, index) in validationWarnings" :key="`warning-${index}`" class="structured-editor__alert structured-editor__alert--warning">
        <i class="fas fa-exclamation-triangle"></i>
        <span>{{ item }}</span>
      </div>
    </div>

    <div class="structured-editor__layout">
      <div class="structured-editor__canvas">
        <div v-if="!blocks.length" class="structured-editor__empty">
          <i class="fas fa-layer-group"></i>
          <span>Структура документа пока пустая</span>
        </div>

        <div
          v-for="(block, index) in blocks"
          :key="block.id || `${block.type}-${index}`"
          class="structured-editor__block"
        >
          <div class="structured-editor__block-header">
            <div class="structured-editor__block-meta">
              <span class="structured-editor__block-index">{{ index + 1 }}</span>
              <div>
                <div class="structured-editor__block-title">{{ blockTitle(block.type) }}</div>
                <div class="structured-editor__block-description">{{ blockDescription(block.type) }}</div>
              </div>
            </div>
            <div class="structured-editor__block-actions">
              <button type="button" :disabled="disabled || index === 0" @click="moveBlock(index, -1)" title="Выше">
                <i class="fas fa-arrow-up"></i>
              </button>
              <button type="button" :disabled="disabled || index === blocks.length - 1" @click="moveBlock(index, 1)" title="Ниже">
                <i class="fas fa-arrow-down"></i>
              </button>
              <button type="button" :disabled="disabled" @click="removeBlock(index)" title="Удалить">
                <i class="fas fa-trash"></i>
              </button>
            </div>
          </div>

          <div class="structured-editor__block-body">
            <template v-if="block.type === 'document_meta'">
              <div class="structured-editor__grid">
                <label>
                  <span>Нумерация</span>
                  <select :value="block.attrs?.number_mode || 'auto'" :disabled="disabled" @change="updateAttr(index, 'number_mode', $event.target.value)">
                    <option value="auto">Автоматическая</option>
                    <option value="daily_sequence">Дневная последовательность</option>
                    <option value="contract_next_act_number">Следующий акт по договору</option>
                  </select>
                </label>
                <label>
                  <span>Срок оплаты</span>
                  <select :value="block.attrs?.payment_due_date_mode || 'workdays_plus'" :disabled="disabled" @change="updateAttr(index, 'payment_due_date_mode', $event.target.value)">
                    <option value="workdays_plus">Дата + рабочие дни</option>
                    <option value="document_date">Равен дате документа</option>
                    <option value="manual">Будет задан в шаблоне</option>
                  </select>
                </label>
                <label>
                  <span>Рабочих дней</span>
                  <input
                    type="number"
                    min="0"
                    :value="block.attrs?.payment_due_days ?? 5"
                    :disabled="disabled"
                    @input="updateAttr(index, 'payment_due_days', Number($event.target.value || 0))"
                  />
                </label>
              </div>
            </template>

            <template v-else-if="block.type === 'party_details'">
              <div class="structured-editor__grid">
                <label>
                  <span>Источник данных</span>
                  <select :value="block.attrs?.role || 'recipient'" :disabled="disabled" @change="updateAttr(index, 'role', $event.target.value)">
                    <option value="our_company">Наша компания</option>
                    <option value="recipient">Получатель</option>
                  </select>
                </label>
                <label class="structured-editor__checkbox">
                  <input
                    type="checkbox"
                    :checked="!!block.attrs?.show_bank_details"
                    :disabled="disabled"
                    @change="updateAttr(index, 'show_bank_details', $event.target.checked)"
                  />
                  <span>Показывать банковские реквизиты</span>
                </label>
              </div>
            </template>

            <template v-else-if="block.type === 'intro_paragraph'">
              <div class="structured-editor__grid">
                <label>
                  <span>Режим</span>
                  <select :value="block.attrs?.mode || 'contract_intro'" :disabled="disabled" @change="updateAttr(index, 'mode', $event.target.value)">
                    <option value="contract_intro">Вводный абзац по договору</option>
                    <option value="manual">Ручной текст</option>
                  </select>
                </label>
              </div>
              <label class="structured-editor__full">
                <span>Текст абзаца</span>
                <textarea
                  rows="3"
                  :value="block.attrs?.text || ''"
                  :disabled="disabled"
                  @input="updateAttr(index, 'text', $event.target.value)"
                ></textarea>
              </label>
            </template>

            <template v-else-if="block.type === 'basis_block'">
              <div class="structured-editor__grid">
                <label>
                  <span>Источник основания</span>
                  <select :value="block.attrs?.mode || 'contract_auto'" :disabled="disabled" @change="updateAttr(index, 'mode', $event.target.value)">
                    <option value="contract_auto">Авто из договора</option>
                    <option value="template">Шаблон строки</option>
                    <option value="manual">Ручная строка</option>
                  </select>
                </label>
              </div>
              <label class="structured-editor__full">
                <span>Шаблон / текст</span>
                <textarea
                  rows="3"
                  :value="block.attrs?.text_pattern || ''"
                  :disabled="disabled"
                  @input="updateAttr(index, 'text_pattern', $event.target.value)"
                ></textarea>
              </label>
            </template>

            <template v-else-if="block.type === 'rich_text_block'">
              <label class="structured-editor__full">
                <span>Текст блока</span>
                <StructuredRichTextBlock
                  :model-value="block.attrs?.html || ''"
                  :disabled="disabled"
                  placeholder="Введите содержимое документа"
                  :fields="fields"
                  :resolved-fields="resolvedFields"
                  :template-blocks="templateBlocks"
                  :ai-enabled="aiEnabled"
                  :ai-model="aiModel"
                  :ai-handler="aiHandler"
                  @update:model-value="updateAttr(index, 'html', $event)"
                />
              </label>
            </template>

            <template v-else-if="block.type === 'invoice_items_table'">
              <div class="structured-editor__hint">
                Таблица счета будет собираться из платежей, договора и шаблона. Сейчас этот блок фиксирует наличие табличной части в структуре.
              </div>
              <label class="structured-editor__checkbox">
                <input
                  type="checkbox"
                  :checked="block.attrs?.show_vat_rate !== false"
                  :disabled="disabled"
                  @change="updateAttr(index, 'show_vat_rate', $event.target.checked)"
                />
                <span>Показывать ставку НДС в строках</span>
              </label>
            </template>

            <template v-else-if="block.type === 'stage_lines_block'">
              <div class="structured-editor__hint">
                Блок использует связанные этапы из формы документа. Их состав и суммы продолжают контролироваться в основной форме исходящего документа.
              </div>
            </template>

            <template v-else-if="block.type === 'payment_allocation_block'">
              <div class="structured-editor__hint">
                Блок использует привязанные платежи и частичные зачеты из формы документа.
              </div>
              <label class="structured-editor__checkbox">
                <input
                  type="checkbox"
                  :checked="block.attrs?.show_remaining_after_offset !== false"
                  :disabled="disabled"
                  @change="updateAttr(index, 'show_remaining_after_offset', $event.target.checked)"
                />
                <span>Показывать остаток после зачета</span>
              </label>
            </template>

            <template v-else-if="block.type === 'totals_block'">
              <div class="structured-editor__grid">
                <label class="structured-editor__checkbox">
                  <input
                    type="checkbox"
                    :checked="block.attrs?.show_vat_amount !== false"
                    :disabled="disabled"
                    @change="updateAttr(index, 'show_vat_amount', $event.target.checked)"
                  />
                  <span>Сумма НДС</span>
                </label>
                <label class="structured-editor__checkbox">
                  <input
                    type="checkbox"
                    :checked="block.attrs?.show_total_words !== false"
                    :disabled="disabled"
                    @change="updateAttr(index, 'show_total_words', $event.target.checked)"
                  />
                  <span>Сумма прописью</span>
                </label>
                <label class="structured-editor__checkbox">
                  <input
                    type="checkbox"
                    :checked="block.attrs?.show_vat_rate !== false"
                    :disabled="disabled"
                    @change="updateAttr(index, 'show_vat_rate', $event.target.checked)"
                  />
                  <span>Ставка НДС</span>
                </label>
              </div>
            </template>

            <template v-else-if="block.type === 'signature_stamp'">
              <div class="structured-editor__grid">
                <label class="structured-editor__checkbox">
                  <input
                    type="checkbox"
                    :checked="block.attrs?.show_director !== false"
                    :disabled="disabled"
                    @change="updateAttr(index, 'show_director', $event.target.checked)"
                  />
                  <span>Руководитель</span>
                </label>
                <label class="structured-editor__checkbox">
                  <input
                    type="checkbox"
                    :checked="!!block.attrs?.show_accountant"
                    :disabled="disabled"
                    @change="updateAttr(index, 'show_accountant', $event.target.checked)"
                  />
                  <span>Бухгалтер</span>
                </label>
                <label class="structured-editor__checkbox">
                  <input
                    type="checkbox"
                    :checked="block.attrs?.show_stamp !== false"
                    :disabled="disabled"
                    @change="updateAttr(index, 'show_stamp', $event.target.checked)"
                  />
                  <span>Печать</span>
                </label>
              </div>
            </template>
          </div>
        </div>
      </div>

      <aside class="structured-editor__sidebar">
        <div class="structured-editor__sidebar-card">
          <div class="structured-editor__sidebar-title">Справочник полей</div>
          <input v-model.trim="fieldSearch" type="text" class="structured-editor__search" placeholder="Поиск по полям" />
          <div class="structured-editor__field-list">
            <div v-for="field in filteredFields" :key="field.key" class="structured-editor__field-item">
              <div class="structured-editor__field-top">
                <code>{{ field.key }}</code>
                <span class="structured-editor__field-type">{{ field.type }}</span>
              </div>
              <div class="structured-editor__field-label">{{ field.label }}</div>
              <div class="structured-editor__field-value">
                {{ renderResolvedValue(field.key) }}
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import StructuredRichTextBlock from './StructuredRichTextBlock.vue'

const props = defineProps({
  modelValue: { type: Object, default: () => ({ schema_version: 1, document_kind: 'letter', content: [] }) },
  documentKind: { type: String, default: 'letter' },
  blockCatalog: { type: Array, default: () => [] },
  fields: { type: Array, default: () => [] },
  templateBlocks: { type: Array, default: () => [] },
  resolvedFields: { type: Object, default: () => ({}) },
  validation: { type: Object, default: () => ({ errors: [], warnings: [] }) },
  disabled: { type: Boolean, default: false },
  aiEnabled: { type: Boolean, default: false },
  aiModel: { type: String, default: '' },
  aiHandler: { type: Function, default: null }
})

const emit = defineEmits(['update:modelValue'])

const fieldSearch = ref('')

const blocks = computed(() => Array.isArray(props.modelValue?.content) ? props.modelValue.content : [])
const validationErrors = computed(() => Array.isArray(props.validation?.errors) ? props.validation.errors : [])
const validationWarnings = computed(() => Array.isArray(props.validation?.warnings) ? props.validation.warnings : [])
const quickAddBlocks = computed(() => props.blockCatalog)
const filteredFields = computed(() => {
  const needle = fieldSearch.value.toLowerCase()
  if (!needle) return props.fields
  return props.fields.filter((field) => (
    `${field.key} ${field.label} ${field.group || ''} ${field.description || ''}`.toLowerCase().includes(needle)
  ))
})

const cloneDraft = () => JSON.parse(JSON.stringify(props.modelValue || { schema_version: 1, document_kind: props.documentKind, content: [] }))

const emitDraft = (draft) => {
  emit('update:modelValue', draft)
}

const defaultAttrsByType = computed(() => Object.fromEntries(
  props.blockCatalog.map((item) => [item.type, JSON.parse(JSON.stringify(item.default_attrs || {}))])
))

const addBlock = (type) => {
  const draft = cloneDraft()
  draft.document_kind = props.documentKind
  if (!Array.isArray(draft.content)) draft.content = []
  draft.content.push({
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    type,
    attrs: JSON.parse(JSON.stringify(defaultAttrsByType.value[type] || {}))
  })
  emitDraft(draft)
}

const removeBlock = (index) => {
  const draft = cloneDraft()
  draft.content.splice(index, 1)
  emitDraft(draft)
}

const moveBlock = (index, step) => {
  const nextIndex = index + step
  if (nextIndex < 0 || nextIndex >= blocks.value.length) return
  const draft = cloneDraft()
  const [item] = draft.content.splice(index, 1)
  draft.content.splice(nextIndex, 0, item)
  emitDraft(draft)
}

const updateAttr = (index, key, value) => {
  const draft = cloneDraft()
  if (!draft.content[index]) return
  if (!draft.content[index].attrs || typeof draft.content[index].attrs !== 'object') {
    draft.content[index].attrs = {}
  }
  draft.content[index].attrs[key] = value
  emitDraft(draft)
}

const blockByType = computed(() => Object.fromEntries(props.blockCatalog.map((item) => [item.type, item])))

const blockTitle = (type) => blockByType.value[type]?.label || type
const blockDescription = (type) => blockByType.value[type]?.description || ''

const renderResolvedValue = (key) => {
  const value = props.resolvedFields?.[key]
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}
</script>

<style scoped>
.structured-editor {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  border: 1px solid rgba(59, 130, 246, 0.14);
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(247, 250, 255, 0.96));
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.06);
}

.structured-editor__header,
.structured-editor__layout,
.structured-editor__alerts,
.structured-editor__grid {
  display: flex;
  gap: 12px;
}

.structured-editor__header {
  justify-content: space-between;
  align-items: flex-start;
}

.structured-editor__title {
  font-size: 16px;
  font-weight: 700;
  color: #102249;
}

.structured-editor__subtitle {
  font-size: 12px;
  color: #6c7a96;
  margin-top: 4px;
}

.structured-editor__actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.structured-editor__quick-add {
  border: 1px solid rgba(59, 130, 246, 0.18);
  background: rgba(59, 130, 246, 0.08);
  color: #1846b8;
  border-radius: 999px;
  padding: 7px 12px;
  font-size: 12px;
  font-weight: 600;
}

.structured-editor__layout {
  align-items: stretch;
}

.structured-editor__canvas {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.structured-editor__sidebar {
  flex: 0 0 320px;
}

.structured-editor__sidebar-card,
.structured-editor__block {
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255, 255, 255, 0.92);
  border-radius: 18px;
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.06);
}

.structured-editor__sidebar-card {
  padding: 16px;
  position: sticky;
  top: 0;
}

.structured-editor__sidebar-title {
  font-size: 13px;
  font-weight: 700;
  color: #12264e;
  margin-bottom: 10px;
}

.structured-editor__search,
.structured-editor__grid select,
.structured-editor__grid input,
.structured-editor__full textarea {
  width: 100%;
  border: 1px solid rgba(148, 163, 184, 0.4);
  border-radius: 12px;
  background: rgba(247, 250, 255, 0.94);
  padding: 9px 12px;
  font-size: 13px;
  color: #334155;
  outline: none;
}

.structured-editor__field-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 620px;
  overflow: auto;
  margin-top: 10px;
}

.structured-editor__field-item {
  padding: 11px 12px;
  border-radius: 14px;
  background: rgba(244, 247, 252, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.18);
}

.structured-editor__field-top {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.structured-editor__field-top code {
  color: #4f46e5;
  font-size: 12px;
}

.structured-editor__field-type {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: #94a3b8;
  font-weight: 700;
}

.structured-editor__field-label {
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
  margin-top: 4px;
}

.structured-editor__field-value {
  font-size: 12px;
  color: #64748b;
  margin-top: 4px;
  word-break: break-word;
}

.structured-editor__block {
  padding: 16px;
}

.structured-editor__block-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.structured-editor__block-meta {
  display: flex;
  gap: 10px;
}

.structured-editor__block-index {
  width: 28px;
  height: 28px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(59, 130, 246, 0.12);
  color: #4f46e5;
  font-size: 12px;
  font-weight: 700;
}

.structured-editor__block-title {
  font-size: 14px;
  font-weight: 700;
  color: #132853;
}

.structured-editor__block-description {
  font-size: 12px;
  color: #64748b;
  margin-top: 4px;
}

.structured-editor__block-actions {
  display: flex;
  gap: 6px;
}

.structured-editor__block-actions button {
  width: 28px;
  height: 28px;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.24);
  background: #ffffff;
  color: #64748b;
}

.structured-editor__block-body {
  margin-top: 12px;
}

.structured-editor__grid {
  flex-wrap: wrap;
}

.structured-editor__grid label,
.structured-editor__full {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1 1 220px;
}

.structured-editor__grid label span,
.structured-editor__full span {
  font-size: 12px;
  font-weight: 600;
  color: #334155;
}

.structured-editor__checkbox {
  justify-content: center;
}

.structured-editor__checkbox input {
  width: auto;
  margin-right: 8px;
}

.structured-editor__hint {
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(59, 130, 246, 0.08);
  color: #64748b;
  font-size: 12px;
  line-height: 1.45;
  border: 1px solid rgba(59, 130, 246, 0.14);
}

.structured-editor__alerts {
  flex-direction: column;
}

.structured-editor__alert {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 12px;
  font-size: 13px;
}

.structured-editor__alert--error {
  background: rgba(239, 68, 68, 0.08);
  color: #b42318;
}

.structured-editor__alert--warning {
  background: rgba(245, 158, 11, 0.11);
  color: #9a5b00;
}

.structured-editor__empty {
  display: flex;
  gap: 10px;
  align-items: center;
  justify-content: center;
  min-height: 180px;
  border: 1px dashed rgba(148, 163, 184, 0.36);
  border-radius: 16px;
  color: #64748b;
  background: rgba(248, 250, 252, 0.9);
}

@media (max-width: 1280px) {
  .structured-editor__layout {
    flex-direction: column;
  }

  .structured-editor__sidebar {
    flex-basis: auto;
  }

  .structured-editor__sidebar-card {
    position: static;
  }
}
</style>
