<template>
  <div class="oc-node">
    <div
      class="oc-card"
      :class="{ 'is-selected': selectedId === node.id }"
      @click="$emit('select', node)"
    >
      <div class="oc-card__top">
        <span class="oc-card__icon" :class="`oc-kind-${node.kind || 'default'}`">
          <i :class="kindIcon"></i>
        </span>
        <div class="oc-card__titles">
          <span class="oc-card__name" :title="node.name">{{ node.name }}</span>
          <span v-if="node.kind" class="oc-card__kind">{{ kindLabel }}</span>
        </div>
        <span v-if="canEdit" class="oc-card__actions" @click.stop>
          <button type="button" title="Добавить подразделение" @click="$emit('add', node)">
            <i class="fas fa-plus"></i>
          </button>
          <button type="button" title="Настроить" @click="$emit('edit', node)">
            <i class="fas fa-pen"></i>
          </button>
          <button type="button" title="Удалить" @click="$emit('remove', node)">
            <i class="fas fa-trash"></i>
          </button>
        </span>
      </div>

      <!-- Начальник: визуально выделенная полоса -->
      <div class="oc-head" :class="{ 'oc-head--empty': !headName }">
        <span class="oc-avatar" :class="headName ? 'oc-avatar--head' : 'oc-avatar--empty'">
          <template v-if="headName">{{ initials(headName) }}</template>
          <i v-else class="fas fa-user-slash"></i>
        </span>
        <span class="oc-head__meta">
          <span class="oc-head__role"><i class="fas fa-user-tie"></i> Руководитель</span>
          <span class="oc-head__name">{{ headName || 'не назначен' }}</span>
        </span>
      </div>

      <!-- Подчинённые: отдельная секция -->
      <div class="oc-foot">
        <span class="oc-foot__count">
          <i class="fas fa-users"></i> {{ node.member_count || 0 }} сотр.
        </span>
        <span class="oc-foot__avatars" v-if="previewMembers.length">
          <span
            v-for="m in previewMembers"
            :key="m.id"
            class="oc-mini-av"
            :title="m.full_name || m.email"
          >{{ initials(m.full_name || m.email) }}</span>
          <span v-if="extraMembers > 0" class="oc-mini-av oc-mini-av--more">+{{ extraMembers }}</span>
        </span>
        <button
          v-if="hasChildren"
          type="button"
          class="oc-toggle"
          :title="open ? 'Свернуть подразделения' : 'Развернуть подразделения'"
          @click.stop="open = !open"
        >
          <i :class="open ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"></i>
          {{ sortedChildren.length }}
        </button>
      </div>
    </div>

    <div v-if="hasChildren && open" class="oc-children">
      <div
        v-for="child in sortedChildren"
        :key="child.id"
        class="oc-branch"
      >
        <org-chart-node
          :node="child"
          :selected-id="selectedId"
          :can-edit="canEdit"
          :user-map="userMap"
          @select="$emit('select', $event)"
          @add="$emit('add', $event)"
          @edit="$emit('edit', $event)"
          @remove="$emit('remove', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { computed, ref } from 'vue'

const KIND_LABELS = {
  company: 'Компания',
  department: 'Отдел',
  team: 'Команда',
  position: 'Должность',
}
const KIND_ICONS = {
  company: 'fas fa-building',
  department: 'fas fa-sitemap',
  team: 'fas fa-people-group',
  position: 'fas fa-id-badge',
  default: 'fas fa-diagram-project',
}

export default {
  name: 'OrgChartNode',
  props: {
    node: { type: Object, required: true },
    selectedId: { type: [String, Number, null], default: null },
    canEdit: { type: Boolean, default: false },
    userMap: { type: Object, default: () => ({}) },
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
    const kindIcon = computed(() => KIND_ICONS[props.node.kind] || KIND_ICONS.default)

    const headName = computed(() => {
      const id = props.node.head_user_id
      if (!id) return ''
      const u = props.userMap[String(id)]
      return u ? (u.full_name || u.email || '') : ''
    })

    const previewMembers = computed(() =>
      Array.isArray(props.node.members) ? props.node.members.slice(0, 4) : []
    )
    const extraMembers = computed(() => {
      const total = props.node.member_count || (props.node.members || []).length || 0
      return Math.max(0, total - previewMembers.value.length)
    })

    const initials = (name) => {
      const s = String(name || '').trim()
      if (!s) return '?'
      const parts = s.split(/\s+/)
      return ((parts[0]?.[0] || '') + (parts[1]?.[0] || '')).toUpperCase() || s[0].toUpperCase()
    }

    return {
      open, hasChildren, sortedChildren, kindLabel, kindIcon,
      headName, previewMembers, extraMembers, initials,
    }
  },
}
</script>

<style scoped>
.oc-node {
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* ---- Карточка подразделения ---- */
.oc-card {
  width: 236px;
  background: var(--apr-card-bg, #fff);
  border: 1px solid var(--apr-card-border, rgba(216, 224, 240, 0.92));
  border-radius: 14px;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.07);
  overflow: hidden;
  cursor: pointer;
  transition: box-shadow 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
}

.oc-card:hover {
  box-shadow: 0 12px 26px rgba(15, 23, 42, 0.13);
  transform: translateY(-1px);
}

.oc-card.is-selected {
  border-color: var(--color-primary, #2563eb);
  box-shadow: 0 0 0 3px var(--color-primary-ring, rgba(37, 99, 235, 0.25));
}

.oc-card__top {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 10px 8px;
}

.oc-card__icon {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  background: var(--color-primary-soft, #eff6ff);
  color: var(--color-primary, #2563eb);
}

.oc-kind-company { background: rgba(124, 58, 237, 0.14); color: #7c3aed; }
.oc-kind-department { background: rgba(37, 99, 235, 0.12); color: #2563eb; }
.oc-kind-team { background: rgba(13, 148, 136, 0.14); color: #0d9488; }
.oc-kind-position { background: rgba(217, 119, 6, 0.14); color: #d97706; }

.oc-card__titles {
  min-width: 0;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.oc-card__name {
  font-size: 13px;
  font-weight: 700;
  color: var(--apr-ink, #0a1629);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.oc-card__kind {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--apr-muted, #7d8592);
}

.oc-card__actions {
  display: flex;
  gap: 1px;
  opacity: 0;
  transition: opacity 0.12s ease;
}

.oc-card:hover .oc-card__actions {
  opacity: 1;
}

.oc-card__actions button {
  width: 22px;
  height: 22px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--apr-muted, #7d8592);
  cursor: pointer;
  font-size: 10px;
}

.oc-card__actions button:hover {
  background: var(--apr-soft, #f6f8fb);
  color: var(--apr-ink, #0a1629);
}

/* ---- Начальник ---- */
.oc-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--color-primary, #2563eb) 12%, transparent),
    color-mix(in srgb, var(--color-primary, #2563eb) 6%, transparent)
  );
  border-top: 1px solid var(--apr-card-border, rgba(216, 224, 240, 0.92));
  border-bottom: 1px solid var(--apr-card-border, rgba(216, 224, 240, 0.92));
}

.oc-head--empty {
  background: var(--apr-soft, #f6f8fb);
}

.oc-avatar {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
}

.oc-avatar--head {
  background: var(--color-primary, #2563eb);
}

.oc-avatar--empty {
  background: var(--color-border-strong, #cbd5e1);
  color: #fff;
  font-size: 11px;
}

.oc-head__meta {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.oc-head__role {
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-primary, #2563eb);
}

.oc-head--empty .oc-head__role {
  color: var(--apr-muted, #7d8592);
}

.oc-head__name {
  font-size: 12px;
  font-weight: 600;
  color: var(--apr-ink, #0a1629);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ---- Подчинённые ---- */
.oc-foot {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
}

.oc-foot__count {
  font-size: 11px;
  font-weight: 600;
  color: var(--apr-muted, #7d8592);
  white-space: nowrap;
}

.oc-foot__avatars {
  display: flex;
  flex: 1 1 auto;
  min-width: 0;
}

.oc-mini-av {
  width: 20px;
  height: 20px;
  margin-left: -5px;
  border-radius: 50%;
  border: 2px solid var(--apr-card-bg, #fff);
  background: var(--color-surface-3, #e2e8f0);
  color: var(--apr-ink, #0a1629);
  font-size: 8px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.oc-mini-av:first-child { margin-left: 0; }
.oc-mini-av--more { background: var(--apr-muted, #7d8592); color: #fff; }

.oc-toggle {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border: 1px solid var(--apr-card-border, rgba(216, 224, 240, 0.92));
  border-radius: 999px;
  background: var(--apr-soft, #f6f8fb);
  color: var(--apr-muted, #7d8592);
  font-size: 10px;
  font-weight: 700;
  cursor: pointer;
}

.oc-toggle:hover {
  color: var(--color-primary, #2563eb);
  border-color: var(--color-primary, #2563eb);
}

/* ---- Соединительные линии (нативное дерево) ---- */
.oc-children {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 22px;
}

/* ствол от родителя вниз к шине */
.oc-children::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  width: 2px;
  height: 22px;
  background: var(--oc-line, #cbd5e1);
}

.oc-branch {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 22px 14px 0;
}

/* вертикаль от шины к карточке ребёнка */
.oc-branch::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  width: 2px;
  height: 22px;
  background: var(--oc-line, #cbd5e1);
}

/* горизонтальная шина */
.oc-branch::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--oc-line, #cbd5e1);
}

.oc-branch:first-child::after { left: 50%; }
.oc-branch:last-child::after { right: 50%; }
.oc-branch:only-child::after { display: none; }
</style>
