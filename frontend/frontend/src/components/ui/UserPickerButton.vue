<template>
  <div class="user-picker" ref="root">
    <button
      type="button"
      class="user-picker__trigger"
      :aria-expanded="open"
      @click="toggle"
    >
      <i class="fas fa-plus"></i>
      <span v-if="label">{{ label }}</span>
    </button>

    <Teleport to="body">
      <div
        v-if="open"
        ref="popoverEl"
        class="user-picker__pop"
        :style="popoverStyle"
        @click.stop
      >
        <input
          ref="searchInput"
          v-model="query"
          type="text"
          class="user-picker__search"
          placeholder="Поиск по имени или email…"
          @keydown.esc.stop="close"
        />
        <div class="user-picker__list">
          <button
            v-for="user in filtered"
            :key="user.id"
            type="button"
            class="user-picker__option"
            :class="{ 'is-selected': selectedIdSet.has(String(user.id)) }"
            @click="pick(user)"
          >
            <span class="user-picker__avatar">
              {{ initialOf(user) }}
            </span>
            <span class="user-picker__copy">
              <strong>{{ user.full_name || user.email || user.id }}</strong>
              <small v-if="user.email">{{ user.email }}</small>
            </span>
            <i
              v-if="selectedIdSet.has(String(user.id))"
              class="fas fa-check user-picker__tick"
            ></i>
          </button>
          <div v-if="!filtered.length" class="user-picker__empty">
            Никого не нашли
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script>
import { ref, computed, onBeforeUnmount, nextTick, watch } from 'vue'

export default {
  name: 'UserPickerButton',
  props: {
    users: { type: Array, default: () => [] },
    selectedIds: { type: Array, default: () => [] },
    mode: { type: String, default: 'multi' }, // 'single' | 'multi'
    label: { type: String, default: 'Добавить' }
  },
  emits: ['select'],
  setup(props, { emit }) {
    const open = ref(false)
    const query = ref('')
    const root = ref(null)
    const searchInput = ref(null)
    const popoverEl = ref(null)
    const popoverStyle = ref({})

    function recomputePopoverPosition() {
      if (!root.value) return
      const r = root.value.getBoundingClientRect()
      const popWidth = 320
      // Align popover under the trigger, but keep it inside the viewport.
      let left = r.left
      if (left + popWidth + 8 > window.innerWidth) {
        left = Math.max(8, window.innerWidth - popWidth - 8)
      }
      popoverStyle.value = {
        position: 'fixed',
        top: `${r.bottom + 6}px`,
        left: `${left}px`,
        zIndex: 2200
      }
    }

    const selectedIdSet = computed(
      () => new Set((props.selectedIds || []).map(String))
    )

    const filtered = computed(() => {
      const q = query.value.trim().toLowerCase()
      const list = props.users || []
      const base = q
        ? list.filter((u) => {
            const haystack = `${u.full_name || ''} ${u.email || ''}`.toLowerCase()
            return haystack.includes(q)
          })
        : list
      return base.slice(0, 60)
    })

    function initialOf(user) {
      const name = (user?.full_name || user?.email || '?').trim()
      return name.charAt(0).toUpperCase()
    }

    function toggle() {
      if (open.value) close()
      else {
        open.value = true
        query.value = ''
        nextTick(() => {
          recomputePopoverPosition()
          searchInput.value?.focus()
          attachOutside()
        })
      }
    }
    function close() {
      if (!open.value) return
      open.value = false
      detachOutside()
    }
    function pick(user) {
      emit('select', user)
      if (props.mode === 'single') close()
    }

    function onOutside(ev) {
      if (!root.value) return
      if (root.value.contains(ev.target)) return
      if (popoverEl.value && popoverEl.value.contains(ev.target)) return
      close()
    }
    function onReposition() { if (open.value) recomputePopoverPosition() }
    function attachOutside() {
      document.addEventListener('mousedown', onOutside)
      window.addEventListener('resize', onReposition)
      window.addEventListener('scroll', onReposition, true)
    }
    function detachOutside() {
      document.removeEventListener('mousedown', onOutside)
      window.removeEventListener('resize', onReposition)
      window.removeEventListener('scroll', onReposition, true)
    }

    watch(open, (v) => { if (!v) detachOutside() })
    onBeforeUnmount(detachOutside)

    return { open, query, root, searchInput, popoverEl, popoverStyle, selectedIdSet, filtered, initialOf, toggle, close, pick }
  }
}
</script>

<style>
/* not scoped — popover teleports to <body> and needs reachable selectors */
.user-picker {
  position: relative;
  display: inline-flex;
}

.user-picker__trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  padding: 0 10px;
  border-radius: var(--radius-pill);
  background: var(--color-surface);
  border: 1px dashed var(--color-border-strong);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}
.user-picker__trigger:hover {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  border-color: var(--color-primary);
  border-style: solid;
}
.user-picker__trigger:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

.user-picker__pop {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  width: 320px;
  max-width: 90vw;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  padding: var(--space-2);
  z-index: 60;
  animation: user-picker-pop var(--dur-fast) var(--ease-out);
}
@keyframes user-picker-pop {
  from { opacity: 0; transform: translateY(-4px); }
  to   { opacity: 1; transform: translateY(0); }
}

.user-picker__search {
  width: 100%;
  padding: 8px 10px;
  margin-bottom: 6px;
  font-size: var(--text-md);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  outline: none;
}
.user-picker__search:focus {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}

.user-picker__list {
  max-height: 280px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.user-picker__option {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr) 16px;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 10px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  cursor: pointer;
  text-align: left;
  transition: background var(--dur-fast) var(--ease-out);
}
.user-picker__option:hover { background: var(--color-surface-2); }
.user-picker__option.is-selected { background: var(--color-primary-soft); }

.user-picker__avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-surface-3);
  color: var(--color-text);
  font-size: var(--text-sm);
  font-weight: var(--fw-bold);
}

.user-picker__copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.user-picker__copy strong {
  font-size: var(--text-md);
  font-weight: var(--fw-medium);
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.user-picker__copy small {
  font-size: var(--text-sm);
  color: var(--color-text-subtle);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-picker__tick {
  color: var(--color-primary);
  font-size: var(--text-sm);
}

.user-picker__empty {
  padding: var(--space-3);
  text-align: center;
  color: var(--color-text-subtle);
  font-size: var(--text-sm);
}
</style>
