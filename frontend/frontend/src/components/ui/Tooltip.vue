<template>
  <span
    class="tt-wrap"
    @mouseenter="show"
    @mouseleave="hide"
    @focusin="show"
    @focusout="hide"
  >
    <slot />
    <Teleport to="body">
      <transition name="tt">
        <div
          v-if="visible && hasContent"
          class="tt-bubble"
          :class="`tt-${placement}`"
          :style="bubbleStyle"
          role="tooltip"
        >
          <slot name="content">{{ text }}</slot>
        </div>
      </transition>
    </Teleport>
  </span>
</template>

<script>
import { ref, computed, nextTick, useSlots } from 'vue'

export default {
  name: 'Tooltip',
  props: {
    text: { type: String, default: '' },
    placement: { type: String, default: 'top' },
    maxWidth: { type: Number, default: 320 }
  },
  setup(props) {
    const visible = ref(false)
    const bubbleStyle = ref({})
    const slots = useSlots()

    const hasContent = computed(() => {
      if (props.text) return true
      const fn = slots.content
      if (!fn) return false
      const nodes = fn() || []
      return nodes.length > 0
    })

    const show = (e) => {
      if (!hasContent.value) return
      const target = e.currentTarget
      visible.value = true
      nextTick(() => {
        const rect = target.getBoundingClientRect()
        const padding = 8
        let top = rect.top - padding
        let left = rect.left + rect.width / 2
        let transform = 'translate(-50%, -100%)'
        if (props.placement === 'bottom') {
          top = rect.bottom + padding
          transform = 'translate(-50%, 0)'
        } else if (props.placement === 'left') {
          top = rect.top + rect.height / 2
          left = rect.left - padding
          transform = 'translate(-100%, -50%)'
        } else if (props.placement === 'right') {
          top = rect.top + rect.height / 2
          left = rect.right + padding
          transform = 'translate(0, -50%)'
        }
        bubbleStyle.value = {
          top: `${top}px`,
          left: `${left}px`,
          transform,
          maxWidth: `${props.maxWidth}px`
        }
      })
    }

    const hide = () => { visible.value = false }

    return { visible, bubbleStyle, hasContent, show, hide }
  }
}
</script>

<style scoped>
.tt-wrap {
  display: inline-flex;
  position: relative;
}

.tt-bubble {
  position: fixed;
  z-index: 11000;
  background: rgba(15, 23, 42, 0.95);
  color: var(--color-text-inverse);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-xs);
  font-size: var(--text-xs);
  line-height: var(--leading-normal);
  pointer-events: none;
  white-space: pre-wrap;
  box-shadow: var(--shadow-md);
}

.tt-enter-active,
.tt-leave-active {
  transition: opacity var(--dur-fast) var(--ease-out), transform var(--dur-fast) var(--ease-out);
}
.tt-enter-from,
.tt-leave-to {
  opacity: 0;
}
.tt-top.tt-enter-from,
.tt-top.tt-leave-to {
  transform: translate(-50%, -95%);
}
.tt-bottom.tt-enter-from,
.tt-bottom.tt-leave-to {
  transform: translate(-50%, 5%);
}
</style>
