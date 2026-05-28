<template>
  <div class="mention-input">
    <textarea
      v-if="multiline"
      ref="fieldRef"
      :value="modelValue"
      class="mention-input__field mention-input__field--area"
      :class="{ 'mention-input__field--grow': autoGrow }"
      :placeholder="placeholder"
      :rows="rows"
      :style="autoGrow ? { minHeight: minHeight + 'px', maxHeight: maxHeight + 'px' } : null"
      @input="onInput"
      @keydown="onKeydown"
      @paste="$emit('paste', $event)"
      @blur="onBlur"
    ></textarea>
    <input
      v-else
      ref="fieldRef"
      type="text"
      :value="modelValue"
      class="mention-input__field"
      :placeholder="placeholder"
      @input="onInput"
      @keydown="onKeydown"
      @blur="onBlur"
    />

    <ul v-if="dropdownOpen && matches.length" class="mention-input__dropdown">
      <li
        v-for="(u, i) in matches"
        :key="u.id"
        class="mention-input__item"
        :class="{ 'is-active': i === activeIndex }"
        @mousedown.prevent="pick(u)"
      >
        <UiAvatar :src="u.avatar_url" :name="u.full_name || u.email" size="sm" />
        <span class="mention-input__item-name">{{ u.full_name || u.email }}</span>
      </li>
    </ul>
  </div>
</template>

<script>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import UiAvatar from './UiAvatar.vue'

/**
 * Поле ввода с @-упоминаниями.
 *
 * В сам текст (`modelValue`) вставляется человекочитаемое `@Имя
 * Фамилия`. Параллельно при каждом выборе эмитится `mention` с
 * `{ name, id }` — родитель копит список и при отправке заменяет
 * `@Имя Фамилия` на маркер `@[Имя Фамилия](user_id)`.
 */
export default {
  name: 'MentionInput',
  components: { UiAvatar },
  props: {
    modelValue: { type: String, default: '' },
    users: { type: Array, default: () => [] },
    placeholder: { type: String, default: '' },
    multiline: { type: Boolean, default: false },
    rows: { type: Number, default: 3 },
    // Auto-resize textarea по содержимому (как в TaskChat).
    // Активно только при multiline=true; высота растёт от minHeight до
    // maxHeight, после чего включается внутренний скролл.
    autoGrow: { type: Boolean, default: false },
    minHeight: { type: Number, default: 40 },
    maxHeight: { type: Number, default: 240 },
  },
  emits: ['update:modelValue', 'mention', 'paste', 'submit'],
  setup(props, { emit }) {
    const fieldRef = ref(null)
    const dropdownOpen = ref(false)
    const query = ref('')
    const activeIndex = ref(0)
    // [start, end) — позиции фрагмента «@query» в тексте.
    let triggerStart = -1

    const matches = computed(() => {
      const q = query.value.trim().toLowerCase()
      const list = props.users || []
      const filtered = q
        ? list.filter((u) => (u.full_name || u.email || '').toLowerCase().includes(q))
        : list
      return filtered.slice(0, 6)
    })

    // Ищем «@…» прямо перед курсором.
    const detectTrigger = (value, caret) => {
      const before = value.slice(0, caret)
      const m = before.match(/@([^\s@]*)$/)
      if (m) {
        triggerStart = caret - m[0].length
        query.value = m[1]
        activeIndex.value = 0
        dropdownOpen.value = true
      } else {
        dropdownOpen.value = false
        triggerStart = -1
      }
    }

    // Auto-resize как в TaskChat: высота = scrollHeight, ограниченная
    // сверху maxHeight. После порога включается внутренний скролл.
    // Сброс на 'auto' нужен, чтобы scrollHeight не залипал на
    // максимальном за сессию значении (иначе textarea не сжимается
    // при удалении строк).
    const autoResize = () => {
      const el = fieldRef.value
      if (!el || !props.autoGrow || !props.multiline) return
      el.style.height = 'auto'
      const next = Math.min(el.scrollHeight, props.maxHeight)
      el.style.height = Math.max(next, props.minHeight) + 'px'
    }

    const onInput = (e) => {
      const value = e.target.value
      emit('update:modelValue', value)
      detectTrigger(value, e.target.selectionStart || value.length)
      if (props.autoGrow && props.multiline) nextTick(autoResize)
    }

    const pick = (user) => {
      const name = user.full_name || user.email || 'Сотрудник'
      const field = fieldRef.value
      const value = props.modelValue || ''
      if (triggerStart < 0) return
      const caret = field ? (field.selectionStart || value.length) : value.length
      const next = value.slice(0, triggerStart) + `@${name} ` + value.slice(caret)
      emit('update:modelValue', next)
      emit('mention', { name, id: user.id })
      dropdownOpen.value = false
      triggerStart = -1
      query.value = ''
      nextTick(() => {
        if (field) {
          const pos = triggerStart < 0 ? next.length : (value.slice(0, triggerStart) + `@${name} `).length
          field.focus()
          try { field.setSelectionRange(pos, pos) } catch { /* noop */ }
        }
      })
    }

    const onKeydown = (e) => {
      if (dropdownOpen.value && matches.value.length) {
        if (e.key === 'ArrowDown') {
          e.preventDefault()
          activeIndex.value = (activeIndex.value + 1) % matches.value.length
          return
        }
        if (e.key === 'ArrowUp') {
          e.preventDefault()
          activeIndex.value = (activeIndex.value - 1 + matches.value.length) % matches.value.length
          return
        }
        if (e.key === 'Enter' || e.key === 'Tab') {
          e.preventDefault()
          pick(matches.value[activeIndex.value])
          return
        }
        if (e.key === 'Escape') {
          dropdownOpen.value = false
          return
        }
      }
      // Enter без Shift в однострочном режиме — submit.
      if (!props.multiline && e.key === 'Enter' && !e.shiftKey && !dropdownOpen.value) {
        emit('submit')
      }
    }

    const onBlur = () => {
      // Небольшая задержка — чтобы успел сработать mousedown по пункту.
      setTimeout(() => { dropdownOpen.value = false }, 150)
    }

    // Подстраиваем высоту:
    //  • после маунта (загружен черновик из props.modelValue),
    //  • при внешнем изменении modelValue (reset композера, drag-сценарии).
    onMounted(() => { nextTick(autoResize) })
    watch(() => props.modelValue, () => {
      if (props.autoGrow && props.multiline) nextTick(autoResize)
    })

    return { fieldRef, dropdownOpen, matches, activeIndex, onInput, onKeydown, onBlur, pick }
  },
}
</script>

<style scoped>
.mention-input { position: relative; }

.mention-input__field {
  width: 100%;
  border: none;
  outline: none;
  font-family: inherit;
  color: var(--color-text, #0f172a);
  background: transparent;
}
.mention-input__field--area {
  resize: none;
  line-height: 1.5;
}
.mention-input__field--grow {
  /* Высота ставится JS-ом по scrollHeight (см. autoResize).
     overflow-y:auto включает внутренний скролл, когда уперлись в maxHeight.
     field-sizing — нативный эквивалент в современных Chrome/Edge;
     держим как fallback и для случаев, когда JS не успел отработать. */
  overflow-y: auto;
  field-sizing: content;
}

.mention-input__dropdown {
  position: absolute;
  left: 0;
  bottom: calc(100% + 4px);
  z-index: 30;
  margin: 0;
  padding: 4px;
  list-style: none;
  min-width: 220px;
  max-width: 320px;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 10px;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.18);
}
.mention-input__item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 7px;
  cursor: pointer;
}
.mention-input__item:hover,
.mention-input__item.is-active {
  background: var(--color-primary-soft, rgba(99, 102, 241, 0.1));
}
.mention-input__item-name {
  font-size: 0.86rem;
  color: var(--color-text, #0f172a);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
