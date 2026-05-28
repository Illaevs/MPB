<template>
  <div class="assignee-stack" :class="{ 'assignee-stack--empty': !visible.length && !overflow }">
    <span
      v-for="user in visible"
      :key="user.id"
      class="assignee-stack__pill"
      :style="user.url ? null : { background: user.bg, color: user.fg }"
      :title="user.tooltip"
    >
      <img v-if="user.url" :src="user.url" :alt="user.name" />
      <span v-else>{{ user.initial }}</span>
    </span>
    <span v-if="overflow" class="assignee-stack__more" :title="overflowTooltip">+{{ overflow }}</span>
    <span v-if="!visible.length && !overflow" class="assignee-stack__none">—</span>
  </div>
</template>

<script>
import { computed } from 'vue'
import { normalizeAvatarUrl } from '../../../utils/avatar'

const AVATAR_THEMES = [
  { bg: 'linear-gradient(135deg, #d7e7ff 0%, #b4d0ff 100%)', fg: '#2563eb' },
  { bg: 'linear-gradient(135deg, #ffe4d3 0%, #ffc79c 100%)', fg: '#b45309' },
  { bg: 'linear-gradient(135deg, #e8ddff 0%, #c8b4ff 100%)', fg: '#7c3aed' },
  { bg: 'linear-gradient(135deg, #d9f7ec 0%, #a9e7cb 100%)', fg: '#0f8f5d' },
  { bg: 'linear-gradient(135deg, #ffe7ef 0%, #ffc3d3 100%)', fg: '#be185d' }
]

function themeFor(seed) {
  const k = String(seed || '?')
  const i = k.split('').reduce((s, c) => s + c.charCodeAt(0), 0) % AVATAR_THEMES.length
  return AVATAR_THEMES[i]
}

export default {
  name: 'AssigneeStack',
  props: {
    userIds: { type: Array, default: () => [] },
    users: { type: Array, default: () => [] },
    max: { type: Number, default: 4 }
  },
  setup(props) {
    const resolved = computed(() => {
      return (props.userIds || []).map((id) => {
        const u = (props.users || []).find((x) => String(x.id) === String(id))
        if (!u) return null
        const name = String(u.full_name || u.email || u.id || '?').trim()
        const raw = String(u.avatar_url || '').trim()
        let url = ''
        if (raw) {
          try { url = normalizeAvatarUrl(raw, u.id) || '' } catch (_) { url = raw }
        }
        const theme = themeFor(`${u.id}${name}`)
        return {
          id: u.id,
          name,
          email: u.email || '',
          tooltip: u.email ? `${name}\n${u.email}` : name,
          initial: (name.charAt(0) || '?').toUpperCase(),
          url,
          bg: theme.bg,
          fg: theme.fg
        }
      }).filter(Boolean)
    })

    const visible = computed(() => resolved.value.slice(0, props.max))
    const overflow = computed(() => Math.max(0, resolved.value.length - props.max))
    const overflowTooltip = computed(() =>
      resolved.value.slice(props.max).map((u) => u.name).join('\n')
    )
    return { visible, overflow, overflowTooltip }
  }
}
</script>

<style scoped>
.assignee-stack {
  display: inline-flex;
  align-items: center;
}

.assignee-stack__pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  /* без flex-shrink:0 узкий контейнер (например карточка матрицы)
     давит ширину пилла → круг превращается в овал/полоску. */
  flex: 0 0 26px;
  border-radius: 50%;
  overflow: hidden;
  font-size: var(--text-xs);
  font-weight: var(--fw-bold);
  border: 2px solid var(--color-surface);
  box-shadow: 0 0 0 1px var(--color-border-subtle);
  margin-left: -8px;
  background: var(--color-surface-3);
  color: var(--color-text);
  cursor: default;
  transition: transform var(--dur-fast) var(--ease-out);
  white-space: pre-line;
}
.assignee-stack__pill:first-child {
  margin-left: 0;
}
.assignee-stack__pill:hover {
  transform: translateY(-1px);
  z-index: 1;
}
.assignee-stack__pill img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.assignee-stack__more {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 26px;
  min-width: 26px;
  flex-shrink: 0;
  padding: 0 6px;
  border-radius: var(--radius-pill);
  background: var(--color-surface-3);
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  margin-left: -8px;
  border: 2px solid var(--color-surface);
  box-shadow: 0 0 0 1px var(--color-border-subtle);
  white-space: pre-line;
  cursor: default;
}

.assignee-stack__none {
  color: var(--color-text-subtle);
  font-size: var(--text-sm);
}
</style>
