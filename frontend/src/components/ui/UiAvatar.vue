<template>
  <Tooltip v-if="tooltip && name" :text="name">
    <span class="ui-avatar" :class="classes" aria-hidden="true">
      <img
        v-if="showImage"
        :src="src"
        :alt="name || 'Avatar'"
        class="ui-avatar__image"
        @error="onImageError"
      />
      <span v-else class="ui-avatar__initials">{{ initials }}</span>
    </span>
  </Tooltip>

  <span v-else class="ui-avatar" :class="classes" :title="tooltip ? name : undefined" aria-hidden="true">
    <img
      v-if="showImage"
      :src="src"
      :alt="name || 'Avatar'"
      class="ui-avatar__image"
      @error="onImageError"
    />
    <span v-else class="ui-avatar__initials">{{ initials }}</span>
  </span>
</template>

<script>
import { computed, ref, watch } from 'vue'
import Tooltip from './Tooltip.vue'

const SIZES = ['xs', 'sm', 'md', 'lg', 'xl', '2xl']
const PALETTE = ['blue', 'teal', 'amber', 'pink', 'purple', 'green', 'red', 'indigo']

export default {
  name: 'UiAvatar',
  components: { Tooltip },
  props: {
    name: { type: String, default: '' },
    src: { type: String, default: null },
    size: { type: String, default: 'md', validator: v => SIZES.includes(v) },
    tooltip: { type: Boolean, default: false }
  },
  setup(props) {
    const imageFailed = ref(false)

    watch(() => props.src, () => { imageFailed.value = false })

    const initials = computed(() => {
      const value = String(props.name || '').trim()
      if (!value) return '?'
      const parts = value.split(/\s+/).filter(Boolean)
      if (!parts.length) return '?'
      if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
      return `${parts[0][0] || ''}${parts[1][0] || ''}`.toUpperCase()
    })

    const paletteKey = computed(() => {
      const value = String(props.name || '')
      if (!value) return PALETTE[0]
      let hash = 0
      for (let i = 0; i < value.length; i += 1) hash = (hash * 31 + value.charCodeAt(i)) | 0
      return PALETTE[Math.abs(hash) % PALETTE.length]
    })

    const showImage = computed(() => !!props.src && !imageFailed.value)

    const classes = computed(() => [
      `ui-avatar--${props.size}`,
      `ui-avatar--${paletteKey.value}`
    ])

    const onImageError = () => { imageFailed.value = true }

    return { initials, showImage, classes, onImageError }
  }
}
</script>

<style scoped>
.ui-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  overflow: hidden;
  color: #fff;
  font-weight: var(--fw-semibold);
  line-height: 1;
  flex-shrink: 0;
  user-select: none;
}

.ui-avatar--xs { width: 22px; height: 22px; font-size: var(--text-xs); }
.ui-avatar--sm { width: 26px; height: 26px; font-size: var(--text-xs); }
.ui-avatar--md { width: 32px; height: 32px; font-size: var(--text-sm); }
.ui-avatar--lg { width: 40px; height: 40px; font-size: var(--text-base); }
.ui-avatar--xl { width: 64px; height: 64px; font-size: var(--text-xl, 1.25rem); }
.ui-avatar--2xl { width: 96px; height: 96px; font-size: 2rem; }

.ui-avatar__image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.ui-avatar__initials {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.ui-avatar--blue { background: #1976d2; }
.ui-avatar--teal { background: #00897b; }
.ui-avatar--amber { background: #f57c00; }
.ui-avatar--pink { background: #d81b60; }
.ui-avatar--purple { background: #6a1b9a; }
.ui-avatar--green { background: #2e7d32; }
.ui-avatar--red { background: #c62828; }
.ui-avatar--indigo { background: #3949ab; }
</style>
