<template>
  <div class="structured-rich-text" :class="{ 'is-disabled': disabled }">
    <div class="structured-rich-text__toolbar">
      <button type="button" :disabled="disabled" :class="{ active: editor?.isActive('bold') }" @click="toggleBold" title="Жирный">
        <i class="fas fa-bold"></i>
      </button>
      <button type="button" :disabled="disabled" :class="{ active: editor?.isActive('italic') }" @click="toggleItalic" title="Курсив">
        <i class="fas fa-italic"></i>
      </button>
      <button type="button" :disabled="disabled" :class="{ active: editor?.isActive('underline') }" @click="toggleUnderline" title="Подчеркивание">
        <i class="fas fa-underline"></i>
      </button>
      <button type="button" :disabled="disabled" :class="{ active: editor?.isActive('bulletList') }" @click="toggleBulletList" title="Список">
        <i class="fas fa-list-ul"></i>
      </button>
      <button type="button" :disabled="disabled" :class="{ active: editor?.isActive('orderedList') }" @click="toggleOrderedList" title="Нумерация">
        <i class="fas fa-list-ol"></i>
      </button>
      <button type="button" :disabled="disabled" :class="{ active: editor?.isActive('blockquote') }" @click="toggleBlockquote" title="Цитата">
        <i class="fas fa-quote-right"></i>
      </button>
      <button type="button" :disabled="disabled" @click="clearFormatting" title="Очистить форматирование">
        <i class="fas fa-eraser"></i>
      </button>
      <div class="structured-rich-text__toolbar-spacer"></div>
      <div class="structured-rich-text__toolbar-group">
        <select v-model="selectedFieldKey" :disabled="disabled || !fields.length" class="structured-rich-text__toolbar-select">
          <option value="">Поле...</option>
          <option v-for="field in fields" :key="field.key" :value="field.key">
            {{ field.label }}
          </option>
        </select>
        <button type="button" :disabled="disabled || !selectedFieldKey" @click="insertSelectedField" title="Вставить поле">
          <i class="fas fa-tags"></i>
        </button>
      </div>
      <div class="structured-rich-text__toolbar-group">
        <select v-model="selectedTemplateBlockKey" :disabled="disabled || !templateBlocks.length" class="structured-rich-text__toolbar-select">
          <option value="">Шаблонный блок...</option>
          <option v-for="block in templateBlocks" :key="block.key" :value="block.key">
            {{ block.label }}
          </option>
        </select>
        <button type="button" :disabled="disabled || !selectedTemplateBlockKey" @click="insertSelectedTemplateBlock" title="Вставить шаблонный блок">
          <i class="fas fa-puzzle-piece"></i>
        </button>
      </div>
      <button
        v-if="aiEnabled"
        type="button"
        class="structured-rich-text__ai-toggle"
        :class="{ active: showAiPanel }"
        :disabled="disabled"
        @click="showAiPanel = !showAiPanel"
        title="AI-ассистент"
      >
        <i class="fas fa-wand-magic-sparkles"></i>
        <span>AI</span>
      </button>
    </div>

    <div v-if="aiEnabled && showAiPanel" class="structured-rich-text__ai-panel">
      <div class="structured-rich-text__ai-head">
        <div>
          <div class="structured-rich-text__ai-title">AI-ассистент текста</div>
          <div class="structured-rich-text__ai-subtitle">
            {{ aiModel ? `Модель: ${aiModel}` : 'Модель доступна через backend-прокси' }}
          </div>
        </div>
        <div class="structured-rich-text__ai-scope">
          {{ hasSelection ? 'Работаем с выделением' : 'Работаем со всем блоком' }}
        </div>
      </div>

      <textarea
        v-model.trim="aiPrompt"
        class="structured-rich-text__ai-prompt"
        :disabled="disabled || aiBusy"
        placeholder="Что сделать с текстом: подготовить черновик, улучшить формулировки, сократить, сделать официальнее..."
        rows="3"
      ></textarea>

      <div class="structured-rich-text__ai-actions">
        <button type="button" class="btn btn-sm btn-primary" :disabled="disabled || aiBusy || !aiHandler" @click="runAiAction('draft')">
          <i v-if="aiBusy && aiAction === 'draft'" class="fas fa-spinner fa-spin mr-1"></i>
          <i v-else class="fas fa-feather-pointed mr-1"></i>
          Черновик
        </button>
        <button type="button" class="btn btn-sm btn-outline-primary" :disabled="disabled || aiBusy || !aiHandler" @click="runAiAction('improve')">
          <i v-if="aiBusy && aiAction === 'improve'" class="fas fa-spinner fa-spin mr-1"></i>
          <i v-else class="fas fa-wand-magic-sparkles mr-1"></i>
          Улучшить
        </button>
        <button type="button" class="btn btn-sm btn-outline-primary" :disabled="disabled || aiBusy || !aiHandler" @click="runAiAction('formalize')">
          <i v-if="aiBusy && aiAction === 'formalize'" class="fas fa-spinner fa-spin mr-1"></i>
          <i v-else class="fas fa-scale-balanced mr-1"></i>
          Официальнее
        </button>
        <button type="button" class="btn btn-sm btn-outline-secondary" :disabled="disabled || aiBusy || !aiHandler" @click="runAiAction('shorten')">
          <i v-if="aiBusy && aiAction === 'shorten'" class="fas fa-spinner fa-spin mr-1"></i>
          <i v-else class="fas fa-compress-alt mr-1"></i>
          Сократить
        </button>
      </div>

      <div v-if="aiError" class="structured-rich-text__ai-error">
        <i class="fas fa-exclamation-triangle"></i>
        <span>{{ aiError }}</span>
      </div>
      <div v-else-if="aiLastNote" class="structured-rich-text__ai-note">
        <i class="fas fa-info-circle"></i>
        <span>{{ aiLastNote }}</span>
      </div>
    </div>

    <EditorContent :editor="editor" class="structured-rich-text__content" />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { EditorContent, useEditor } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import Placeholder from '@tiptap/extension-placeholder'
import DOMPurify from 'dompurify'

import FieldChip from './tiptap/FieldChip'
import TemplateBlock from './tiptap/TemplateBlock'

const props = defineProps({
  modelValue: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  placeholder: { type: String, default: 'Введите текст блока' },
  fields: { type: Array, default: () => [] },
  resolvedFields: { type: Object, default: () => ({}) },
  templateBlocks: { type: Array, default: () => [] },
  aiEnabled: { type: Boolean, default: false },
  aiModel: { type: String, default: '' },
  aiHandler: { type: Function, default: null },
})

const emit = defineEmits(['update:modelValue'])
const selectedFieldKey = ref('')
const selectedTemplateBlockKey = ref('')
const showAiPanel = ref(false)
const aiPrompt = ref('')
const aiBusy = ref(false)
const aiError = ref('')
const aiAction = ref('')
const aiLastNote = ref('')

const normalizeHtml = (value) => {
  const html = String(value || '').trim()
  if (!html || html === '<p></p>') return ''
  return html
}

const sanitizeStructuredHtml = (value) => DOMPurify.sanitize(value || '', {
  ALLOWED_TAGS: ['p', 'br', 'ul', 'ol', 'li', 'strong', 'em', 'span', 'div', 'blockquote'],
  ALLOWED_ATTR: ['class', 'data-field-chip', 'data-field-key', 'data-template-block', 'data-template-key', 'contenteditable'],
})

const fieldKeyMap = computed(() => Object.fromEntries(
  (props.fields || [])
    .filter((item) => item?.key)
    .map((item) => [String(item.key), item])
))

const templateBlockMap = computed(() => Object.fromEntries(
  (props.templateBlocks || [])
    .filter((item) => item?.key)
    .map((item) => [String(item.key), item])
))

const escapeHtml = (value) => String(value || '')
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;')

const decorateStructuredTokens = (value) => {
  let html = String(value || '').trim()
  if (!html) return ''

  html = html.replace(/\[\[(?:template|block):([^\]]+)\]\]/gi, (match, rawKey) => {
    const key = String(rawKey || '').trim()
    const template = templateBlockMap.value[key]
    if (!template) return escapeHtml(match)
    return `<div data-template-block="true" data-template-key="${escapeHtml(key)}" class="structured-template-block" contenteditable="false">Шаблон: ${escapeHtml(template.label || key)}</div>`
  })

  html = html.replace(/{{\s*([^}]+?)\s*}}/g, (match, rawKey) => {
    const key = String(rawKey || '').trim()
    const field = fieldKeyMap.value[key]
    if (!field) return escapeHtml(match)
    return `<span data-field-chip="true" data-field-key="${escapeHtml(key)}" class="structured-field-chip" contenteditable="false">{{ ${escapeHtml(field.label || key)} }}</span>`
  })

  return sanitizeStructuredHtml(html)
}

const editor = useEditor({
  extensions: [
    StarterKit.configure({
      heading: false,
      codeBlock: false,
      horizontalRule: false,
    }),
    Underline,
    Placeholder.configure({
      placeholder: props.placeholder,
    }),
    FieldChip,
    TemplateBlock,
  ],
  content: normalizeHtml(props.modelValue),
  editable: !props.disabled,
  editorProps: {
    attributes: {
      class: 'structured-rich-text__prosemirror',
    },
  },
  onUpdate: ({ editor: instance }) => {
    emit('update:modelValue', instance.isEmpty ? '' : normalizeHtml(instance.getHTML()))
  },
})

watch(() => props.modelValue, (value) => {
  if (!editor.value) return
  const nextHtml = normalizeHtml(value)
  const currentHtml = normalizeHtml(editor.value.isEmpty ? '' : editor.value.getHTML())
  if (nextHtml === currentHtml) return
  editor.value.commands.setContent(nextHtml || '<p></p>', false)
})

watch(() => props.disabled, (disabled) => {
  if (!editor.value) return
  editor.value.setEditable(!disabled)
})

onBeforeUnmount(() => {
  editor.value?.destroy()
})

const getSelectionText = () => {
  if (!editor.value) return ''
  const { from, to } = editor.value.state.selection
  if (from === to) return ''
  return editor.value.state.doc.textBetween(from, to, '\n').trim()
}

const hasSelection = computed(() => !!getSelectionText())

const toggleBold = () => editor.value?.chain().focus().toggleBold().run()
const toggleItalic = () => editor.value?.chain().focus().toggleItalic().run()
const toggleUnderline = () => editor.value?.chain().focus().toggleUnderline().run()
const toggleBulletList = () => editor.value?.chain().focus().toggleBulletList().run()
const toggleOrderedList = () => editor.value?.chain().focus().toggleOrderedList().run()
const toggleBlockquote = () => editor.value?.chain().focus().toggleBlockquote().run()
const clearFormatting = () => {
  editor.value?.chain().focus().clearNodes().unsetAllMarks().run()
}

const insertSelectedField = () => {
  const field = props.fields.find((item) => String(item?.key || '') === selectedFieldKey.value)
  if (!field || !editor.value) return
  editor.value.chain().focus().insertFieldChip({
    key: field.key,
    label: field.label || field.key,
  }).run()
  selectedFieldKey.value = ''
}

const insertSelectedTemplateBlock = () => {
  const block = props.templateBlocks.find((item) => String(item?.key || '') === selectedTemplateBlockKey.value)
  if (!block || !editor.value) return
  editor.value.chain().focus().insertTemplateBlock({
    key: block.key,
    label: block.label || block.key,
  }).run()
  selectedTemplateBlockKey.value = ''
}

const applyAiHtml = (html, action, selectionPresent) => {
  if (!editor.value) return
  const preparedHtml = decorateStructuredTokens(html)
  if (!preparedHtml) return

  const currentHtml = normalizeHtml(editor.value.isEmpty ? '' : editor.value.getHTML())
  if (selectionPresent) {
    editor.value.chain().focus().insertContent(preparedHtml).run()
    return
  }
  if (action === 'draft' && currentHtml) {
    editor.value.chain().focus('end').insertContent(preparedHtml).run()
    return
  }
  editor.value.commands.setContent(preparedHtml, true)
}

const runAiAction = async (action) => {
  if (!props.aiHandler || !editor.value) return
  aiBusy.value = true
  aiError.value = ''
  aiAction.value = action
  aiLastNote.value = ''
  try {
    const selectionText = getSelectionText()
    const selectionPresent = !!selectionText
    const response = await props.aiHandler({
      action,
      prompt: aiPrompt.value || '',
      currentHtml: normalizeHtml(editor.value.isEmpty ? '' : editor.value.getHTML()),
      selectionText,
      selectionPresent,
    })
    const html = String(response?.html || '').trim()
    if (!html) {
      aiError.value = 'AI вернул пустой результат.'
      return
    }
    applyAiHtml(html, action, selectionPresent)
    aiLastNote.value = selectionPresent
      ? 'Результат применен к выделенному фрагменту.'
      : (action === 'draft' && normalizeHtml(props.modelValue) ? 'Результат добавлен в конец блока.' : 'Результат заменил текущий блок.')
    if (Array.isArray(response?.warnings) && response.warnings.length) {
      aiLastNote.value = response.warnings.join(' ')
    }
  } catch (error) {
    aiError.value = error?.response?.data?.detail || error?.message || 'Не удалось получить ответ от AI.'
  } finally {
    aiBusy.value = false
  }
}
</script>

<style scoped>
.structured-rich-text {
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 14px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.96);
}

.structured-rich-text.is-disabled {
  opacity: 0.75;
}

.structured-rich-text__toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 10px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  background: rgba(248, 250, 252, 0.92);
}

.structured-rich-text__toolbar button {
  width: 32px;
  height: 32px;
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 10px;
  background: #ffffff;
  color: #64748b;
}

.structured-rich-text__toolbar button.active {
  border-color: rgba(59, 130, 246, 0.24);
  background: rgba(59, 130, 246, 0.08);
  color: #4f46e5;
}

.structured-rich-text__toolbar-spacer {
  flex: 1 1 auto;
}

.structured-rich-text__toolbar-group {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.structured-rich-text__toolbar-select {
  min-width: 180px;
  max-width: 240px;
  height: 32px;
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 10px;
  background: #ffffff;
  color: #475569;
  padding: 0 10px;
  font-size: 12px;
}

.structured-rich-text__ai-toggle {
  width: auto !important;
  min-width: 66px;
  padding: 0 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.structured-rich-text__ai-panel {
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.95), rgba(239, 246, 255, 0.92));
  padding: 12px 14px;
}

.structured-rich-text__ai-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.structured-rich-text__ai-title {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}

.structured-rich-text__ai-subtitle,
.structured-rich-text__ai-scope {
  font-size: 12px;
  color: #64748b;
}

.structured-rich-text__ai-prompt {
  width: 100%;
  margin-top: 10px;
  resize: vertical;
  min-height: 74px;
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 12px;
  padding: 10px 12px;
  background: #ffffff;
  color: #14233f;
  font-size: 13px;
  line-height: 1.5;
}

.structured-rich-text__ai-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.structured-rich-text__ai-actions .btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.structured-rich-text__ai-error,
.structured-rich-text__ai-note {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  font-size: 12px;
}

.structured-rich-text__ai-error {
  color: #b42318;
}

.structured-rich-text__ai-note {
  color: #475569;
}

.structured-rich-text__content :deep(.structured-rich-text__prosemirror) {
  min-height: 180px;
  padding: 14px;
  font-size: 14px;
  line-height: 1.6;
  color: #14233f;
  outline: none;
  background: #ffffff;
}

.structured-rich-text__content :deep(.structured-rich-text__prosemirror p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  color: #94a3b8;
  float: left;
  height: 0;
  pointer-events: none;
}

.structured-rich-text__content :deep(.structured-rich-text__prosemirror ul),
.structured-rich-text__content :deep(.structured-rich-text__prosemirror ol) {
  padding-left: 22px;
}

.structured-rich-text__content :deep(.structured-rich-text__prosemirror blockquote) {
  border-left: 3px solid rgba(37, 99, 235, 0.25);
  padding-left: 12px;
  color: #475569;
}

.structured-rich-text__content :deep(.structured-field-chip) {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 3px 9px;
  margin: 0 2px;
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(59, 130, 246, 0.16);
  color: #4f46e5;
  font-size: 12px;
  font-weight: 600;
}

.structured-rich-text__content :deep(.structured-template-block) {
  display: block;
  margin: 10px 0;
  padding: 10px 12px;
  border: 1px dashed rgba(148, 163, 184, 0.4);
  border-radius: 12px;
  background: rgba(248, 250, 252, 0.95);
  color: #475569;
  font-size: 13px;
  font-weight: 600;
}
</style>
