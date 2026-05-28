<template>
  <div class="org-node">
    <div
      class="org-node__row"
      :class="{ 'is-selected': selectedId === node.id }"
      :style="{ paddingLeft: (depth * 16 + 8) + 'px' }"
      @click="$emit('select', node)"
    >
      <button
        type="button"
        class="org-node__toggle"
        :class="{ 'is-leaf': !hasChildren }"
        @click.stop="hasChildren && (open = !open)"
      >
        <i v-if="hasChildren" :class="open ? 'fas fa-chevron-down' : 'fas fa-chevron-right'"></i>
        <i v-else class="fas fa-circle org-node__dot"></i>
      </button>

      <span class="org-node__name">{{ node.name }}</span>
      <span v-if="node.kind" class="org-node__kind">{{ kindLabel }}</span>
      <span v-if="node.member_count" class="org-node__count" :title="'Сотрудников: ' + node.member_count">
        <i class="fas fa-user"></i> {{ node.member_count }}
      </span>

      <span class="org-node__spacer"></span>

      <span v-if="canEdit" class="org-node__actions" @click.stop>
        <button type="button" title="Добавить дочерний" @click="$emit('add', node)">
          <i class="fas fa-plus"></i>
        </button>
        <button type="button" title="Переименовать / настроить" @click="$emit('edit', node)">
          <i class="fas fa-pen"></i>
        </button>
        <button type="button" title="Удалить" @click="$emit('remove', node)">
          <i class="fas fa-trash"></i>
        </button>
      </span>
    </div>

    <div v-if="hasChildren && open" class="org-node__children">
      <org-tree-node
        v-for="child in sortedChildren"
        :key="child.id"
        :node="child"
        :selected-id="selectedId"
        :can-edit="canEdit"
        :depth="depth + 1"
        @select="$emit('select', $event)"
        @add="$emit('add', $event)"
        @edit="$emit('edit', $event)"
        @remove="$emit('remove', $event)"
      />
    </div>
  </div>
</template>

<script>
import { computed, ref } from 'vue'

const KIND_LABELS = {
  company: 'Компания',
  department: 'Отдел',
  team: 'Команда',
  position: 'Должность'
}

export default {
  name: 'OrgTreeNode',
  props: {
    node: { type: Object, required: true },
    selectedId: { type: [String, Number, null], default: null },
    canEdit: { type: Boolean, default: false },
    depth: { type: Number, default: 0 }
  },
  emits: ['select', 'add', 'edit', 'remove'],
  setup(props) {
    const open = ref(true)
    const hasChildren = computed(
      () => Array.isArray(props.node.children) && props.node.children.length > 0
    )
    const sortedChildren = computed(() =>
      [...(props.node.children || [])].sort(
        (a, b) =>
          (a.sort_order || 0) - (b.sort_order || 0) ||
          String(a.name).localeCompare(String(b.name))
      )
    )
    const kindLabel = computed(() => KIND_LABELS[props.node.kind] || props.node.kind)
    return { open, hasChildren, sortedChildren, kindLabel }
  }
}
</script>

<style scoped>
.org-node__row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px 7px 8px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  color: var(--apr-ink, #0a1629);
  transition: background 0.12s ease;
}
.org-node__row:hover {
  background: var(--apr-soft, #f6f8fb);
}
.org-node__row.is-selected {
  background: rgba(99, 102, 241, 0.12);
  font-weight: 600;
}
.org-node__toggle {
  border: none;
  background: transparent;
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--apr-muted, #7d8592);
  cursor: pointer;
  font-size: 11px;
  flex-shrink: 0;
}
.org-node__toggle.is-leaf {
  cursor: default;
}
.org-node__dot {
  font-size: 5px;
}
.org-node__name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.org-node__kind {
  font-size: 11px;
  color: var(--apr-muted, #7d8592);
  background: var(--apr-soft, #f6f8fb);
  border: 1px solid var(--apr-card-border, rgba(216, 224, 240, 0.92));
  padding: 1px 7px;
  border-radius: 999px;
}
.org-node__count {
  font-size: 11px;
  color: var(--apr-muted, #7d8592);
}
.org-node__spacer {
  flex: 1 1 auto;
}
.org-node__actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.12s ease;
}
.org-node__row:hover .org-node__actions {
  opacity: 1;
}
.org-node__actions button {
  border: none;
  background: transparent;
  color: var(--apr-muted, #7d8592);
  width: 24px;
  height: 24px;
  border-radius: 7px;
  cursor: pointer;
  font-size: 11px;
}
.org-node__actions button:hover {
  background: var(--apr-card-bg, #fff);
  color: var(--apr-ink, #0a1629);
}
</style>
