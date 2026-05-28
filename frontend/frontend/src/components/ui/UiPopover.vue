<template>
  <div ref="rootEl" class="ui-popover" :class="{ 'ui-popover--block': block }">
    <div ref="triggerEl" class="ui-popover__trigger">
      <slot name="trigger" :toggle="toggle" :isOpen="isOpen"></slot>
    </div>

    <Teleport v-if="teleport" to="body">
      <transition name="ui-popover">
        <div
          v-if="isOpen"
          ref="contentEl"
          class="ui-popover__content"
          :class="contentClasses"
          :style="teleportStyle"
          @click="onInsideClick"
        >
          <slot />
        </div>
      </transition>
    </Teleport>

    <transition v-else name="ui-popover">
      <div
        v-if="isOpen"
        ref="contentEl"
        class="ui-popover__content"
        :class="contentClasses"
        :style="inlineStyle"
        @click="onInsideClick"
      >
        <slot />
      </div>
    </transition>
  </div>
</template>

<script>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'

const PLACEMENTS = ['bottom-start', 'bottom-end', 'top-start', 'top-end']

export default {
  name: 'UiPopover',
  props: {
    modelValue: { type: Boolean, default: false },
    placement: { type: String, default: 'bottom-start', validator: v => PLACEMENTS.includes(v) },
    offset: { type: Number, default: 4 },
    closeOnInside: { type: Boolean, default: false },
    width: { type: [String, Number], default: null },
    teleport: { type: Boolean, default: false },
    block: { type: Boolean, default: false }
  },
  emits: ['update:modelValue', 'open', 'close'],
  setup(props, { emit }) {
    const rootEl = ref(null)
    const triggerEl = ref(null)
    const contentEl = ref(null)
    const teleportStyle = ref({})

    const isOpen = computed(() => props.modelValue)
    const widthValue = computed(() => {
      if (props.width == null || props.width === '') return null
      return typeof props.width === 'number' ? `${props.width}px` : props.width
    })

    const contentClasses = computed(() => [
      `ui-popover__content--${props.placement}`,
      { 'ui-popover__content--teleport': props.teleport }
    ])

    const inlineStyle = computed(() => ({
      width: widthValue.value || undefined
    }))

    const updateTeleportPosition = () => {
      if (!props.teleport || !triggerEl.value) return
      const rect = triggerEl.value.getBoundingClientRect()
      const spacing = Number(props.offset) || 4
      const style = {
        top: `${rect.bottom + spacing}px`,
        left: `${rect.left}px`,
        width: widthValue.value || undefined
      }
      if (props.placement === 'bottom-end') {
        style.left = `${rect.right}px`
        style.transform = 'translateX(-100%)'
      } else if (props.placement === 'top-start') {
        style.top = `${rect.top - spacing}px`
        style.transform = 'translateY(-100%)'
      } else if (props.placement === 'top-end') {
        style.top = `${rect.top - spacing}px`
        style.left = `${rect.right}px`
        style.transform = 'translate(-100%, -100%)'
      }
      teleportStyle.value = style
    }

    const close = () => {
      if (!props.modelValue) return
      emit('update:modelValue', false)
      emit('close')
    }

    const open = () => {
      if (props.modelValue) return
      emit('update:modelValue', true)
      emit('open')
    }

    const toggle = (event) => {
      if (event?.preventDefault) event.preventDefault()
      if (props.modelValue) close()
      else open()
    }

    const onInsideClick = () => {
      if (props.closeOnInside) close()
    }

    const onDocumentMouseDown = (event) => {
      const target = event.target
      if (rootEl.value?.contains(target)) return
      if (contentEl.value?.contains(target)) return
      close()
    }

    const onDocumentKeyDown = (event) => {
      if (event.key === 'Escape') close()
    }

    const bindGlobalListeners = (bind) => {
      if (typeof window === 'undefined') return
      const method = bind ? 'addEventListener' : 'removeEventListener'
      window[method]('mousedown', onDocumentMouseDown, true)
      window[method]('keydown', onDocumentKeyDown)
      if (props.teleport) {
        window[method]('resize', updateTeleportPosition)
        window[method]('scroll', updateTeleportPosition, true)
      }
    }

    watch(() => props.modelValue, async (value) => {
      bindGlobalListeners(value)
      if (value && props.teleport) {
        await nextTick()
        updateTeleportPosition()
      }
    }, { immediate: true })

    onBeforeUnmount(() => bindGlobalListeners(false))

    return {
      rootEl,
      triggerEl,
      contentEl,
      isOpen,
      contentClasses,
      inlineStyle,
      teleportStyle,
      toggle,
      onInsideClick
    }
  }
}
</script>

<style scoped>
.ui-popover {
  position: relative;
  display: inline-flex;
  min-width: 0;
}

.ui-popover--block {
  display: flex;
  width: 100%;
}

.ui-popover__trigger {
  display: inline-flex;
  min-width: 0;
}

.ui-popover--block .ui-popover__trigger {
  width: 100%;
}

.ui-popover__content {
  position: absolute;
  z-index: 200;
  min-width: 180px;
  padding: var(--space-1);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
}

.ui-popover__content--teleport {
  position: fixed;
}

.ui-popover__content--bottom-start {
  top: calc(100% + var(--space-1));
  left: 0;
}

.ui-popover__content--bottom-end {
  top: calc(100% + var(--space-1));
  right: 0;
}

.ui-popover__content--top-start {
  bottom: calc(100% + var(--space-1));
  left: 0;
}

.ui-popover__content--top-end {
  bottom: calc(100% + var(--space-1));
  right: 0;
}

.ui-popover-enter-active,
.ui-popover-leave-active {
  transition:
    opacity var(--dur-fast) ease,
    transform var(--dur-fast) var(--ease-out);
}

.ui-popover-enter-from,
.ui-popover-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
