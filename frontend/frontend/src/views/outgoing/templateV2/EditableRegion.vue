<template>
  <div
    ref="rootRef"
    class="editable-region"
    :class="{ 'editable-region--focused': focused }"
    :data-region-key="regionKey"
    contenteditable="true"
    spellcheck="true"
    @input="onInput"
    @focus="focused = true; $emit('focus', { regionKey, el: rootRef })"
    @blur="focused = false; $emit('blur', { regionKey, el: rootRef })"
    @paste.prevent="onPaste"
  ></div>
</template>

<script>
import { onMounted, ref, watch } from 'vue'

export default {
  name: 'EditableRegion',
  props: {
    /**
     * Region key from the template (`body` on MVP).
     */
    regionKey: { type: String, required: true },
    /**
     * Initial HTML content for the region. Two-way via `update:modelValue`.
     */
    modelValue: { type: String, default: '' },
  },
  emits: ['update:modelValue', 'focus', 'blur'],
  setup(props, { emit }) {
    const rootRef = ref(null)
    const focused = ref(false)

    const writeHtmlIfChanged = (html) => {
      if (!rootRef.value) return
      if (rootRef.value.innerHTML === html) return
      rootRef.value.innerHTML = html ?? ''
    }

    onMounted(() => { writeHtmlIfChanged(props.modelValue) })

    // Sync external changes (e.g. template reload). Do not write back into the
    // node while it's focused — would break the caret position.
    watch(() => props.modelValue, (next) => {
      if (focused.value) return
      writeHtmlIfChanged(next)
    })

    const onInput = () => {
      if (!rootRef.value) return
      emit('update:modelValue', rootRef.value.innerHTML)
    }

    const onPaste = (e) => {
      // Force plain-text paste for now (MVP). Tiptap integration in step 5
      // will replace this with proper rich-text paste handling.
      const text = (e.clipboardData || window.clipboardData).getData('text/plain')
      document.execCommand('insertText', false, text)
    }

    // Expose the root element so the parent toolbar can refocus + restore
    // selection after interacting with non-button controls (e.g. <select>).
    const getEl = () => rootRef.value

    return { rootRef, focused, onInput, onPaste, getEl }
  }
}
</script>

<style scoped>
.editable-region {
  display: block;
  min-height: 1.4em;
  padding: 6px 8px;
  margin: 0 -8px;
  border-radius: var(--radius-sm);
  background: transparent;
  outline: none;
  transition: background var(--dur-fast) var(--ease-out), box-shadow var(--dur-fast) var(--ease-out);
}
.editable-region:hover { background: var(--color-surface-2); }
.editable-region--focused {
  background: var(--color-surface-2);
  box-shadow: inset 0 0 0 1px var(--color-primary);
}
.editable-region :deep(p) { margin: 0 0 0.5em; }
.editable-region :deep(p:last-child) { margin-bottom: 0; }
</style>
