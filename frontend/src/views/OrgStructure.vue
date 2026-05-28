<template>
  <div class="org-structure-view">
    <div class="org-head">
      <div>
        <h1 class="org-head__title">Структура организации</h1>
        <p class="org-head__sub">Дерево подразделений, руководители и состав</p>
      </div>
      <div class="org-head__actions" v-if="canEdit">
        <UiButton variant="primary" @click="openCreate(null)">
          <i class="fas fa-plus"></i> Корневой узел
        </UiButton>
      </div>
    </div>

    <div v-if="banner" class="org-banner" :class="'org-banner--' + banner.kind">
      {{ banner.text }}
      <button type="button" @click="banner = null"><i class="fas fa-times"></i></button>
    </div>

    <div class="org-layout">
      <UiCard class="org-tree-card">
        <div class="org-card__title">
          <i class="fas fa-sitemap"></i> Орг-схема
        </div>
        <div v-if="loading" class="org-empty">Загрузка…</div>
        <div v-else-if="!tree.length" class="org-empty">
          Дерево пустое.<span v-if="canEdit"> Создайте корневой узел.</span>
        </div>
        <div v-else class="org-chart-scroll">
          <div class="org-chart">
            <div v-for="root in tree" :key="root.id" class="org-chart__root">
              <OrgChartNode
                :node="root"
                :selected-id="selected && selected.id"
                :can-edit="canEdit"
                :user-map="usersMap"
                @select="selectUnit"
                @add="openCreate"
                @edit="openEdit"
                @remove="confirmRemove"
              />
            </div>
          </div>
        </div>
      </UiCard>

      <UiCard class="org-detail-card">
        <div v-if="!selected" class="org-empty">Выберите подразделение слева</div>
        <template v-else>
          <div class="org-card__title">
            {{ selected.name }}
            <span v-if="selected.kind" class="org-detail__kind">{{ kindLabel(selected.kind) }}</span>
          </div>

          <div class="org-detail__row">
            <span class="org-detail__label">Руководитель</span>
            <span class="org-detail__value">{{ headName || '— не назначен —' }}</span>
          </div>
          <div class="org-detail__row">
            <span class="org-detail__label">Сотрудников</span>
            <span class="org-detail__value">{{ members.length }}</span>
          </div>

          <div class="org-detail__section">
            <div class="org-detail__section-head">
              <span>Состав</span>
              <UiButton v-if="canEdit" size="sm" variant="ghost" @click="showMemberPicker = !showMemberPicker">
                <i class="fas fa-user-plus"></i> Добавить
              </UiButton>
            </div>

            <div v-if="showMemberPicker && canEdit" class="org-picker">
              <UiInput v-model="memberSearch" placeholder="Поиск сотрудника…" />
              <div class="org-picker__list">
                <button
                  v-for="u in pickableUsers"
                  :key="u.id"
                  type="button"
                  class="org-picker__item"
                  @click="assignMember(u.id)"
                >
                  {{ u.full_name }} <span>{{ u.email }}</span>
                </button>
                <div v-if="!pickableUsers.length" class="org-empty">Нет совпадений</div>
              </div>
            </div>

            <div v-if="!members.length" class="org-empty">Нет сотрудников</div>
            <ul v-else class="org-members">
              <li v-for="m in members" :key="m.id">
                <span>{{ m.full_name }} <em>{{ m.email }}</em></span>
                <button v-if="canEdit" type="button" title="Убрать из узла" @click="unassignMember(m.id)">
                  <i class="fas fa-times"></i>
                </button>
              </li>
            </ul>
          </div>
        </template>
      </UiCard>
    </div>

    <UiModal
      :model-value="modal.open"
      :title="modal.editing ? 'Редактирование узла' : 'Новый узел'"
      size="sm"
      @update:model-value="(v) => (modal.open = v)"
      @close="modal.open = false"
    >
      <div class="org-form">
        <label>Название
          <UiInput v-model="modal.name" placeholder="Например: Технический отдел" />
        </label>
        <label>Тип
          <select class="org-native-select" v-model="modal.kind">
            <option value="">—</option>
            <option value="company">Компания</option>
            <option value="department">Отдел</option>
            <option value="team">Команда</option>
            <option value="position">Должность</option>
          </select>
        </label>
        <label>Родитель
          <select class="org-native-select" v-model="modal.parent_id">
            <option value="">— корень —</option>
            <option v-for="u in flatUnits" :key="u.id" :value="u.id" :disabled="modal.editing && u.id === modal.id">
              {{ '— '.repeat(u.depth) }}{{ u.name }}
            </option>
          </select>
        </label>
        <label>Руководитель
          <select class="org-native-select" v-model="modal.head_user_id">
            <option value="">— не назначен —</option>
            <option v-for="u in users" :key="u.id" :value="u.id">{{ u.full_name }}</option>
          </select>
        </label>
        <label>Порядок
          <UiInput v-model.number="modal.sort_order" type="number" />
        </label>
      </div>
      <template #footer>
        <UiButton variant="ghost" @click="modal.open = false">Отмена</UiButton>
        <UiButton variant="primary" :disabled="saving || !modal.name.trim()" @click="saveModal">
          {{ saving ? 'Сохранение…' : 'Сохранить' }}
        </UiButton>
      </template>
    </UiModal>
  </div>
</template>

<script>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../services/api'
import { hasSectionAccess, canEditSection } from '../utils/permissions'
import { useAuthStore } from '../stores/auth'
import { UiButton, UiCard, UiInput, UiModal } from '../components/ui'
import OrgChartNode from '../components/ui/OrgChartNode.vue'

const KIND_LABELS = { company: 'Компания', department: 'Отдел', team: 'Команда', position: 'Должность' }

export default {
  name: 'OrgStructure',
  components: { UiButton, UiCard, UiInput, UiModal, OrgChartNode },
  setup() {
    const auth = useAuthStore()
    const canView = computed(() => hasSectionAccess('org_structure', auth.permissions))
    const canEdit = computed(() => canEditSection('org_structure', auth.permissions))

    const tree = ref([])
    const flatUnits = ref([])
    const users = ref([])
    const loading = ref(true)
    const saving = ref(false)
    const banner = ref(null)

    const selected = ref(null)
    const members = ref([])
    const showMemberPicker = ref(false)
    const memberSearch = ref('')

    const modal = reactive({
      open: false, editing: false, id: null,
      name: '', kind: '', parent_id: '', head_user_id: '', sort_order: 0
    })

    const setBanner = (text, kind = 'error') => { banner.value = { text, kind } }
    const errText = (e) => e?.response?.data?.detail || e?.message || 'Ошибка'

    const loadTree = async () => {
      loading.value = true
      try {
        tree.value = await api.orgStructure.list()
        flatUnits.value = await api.orgStructure.list({ flat: 1 })
      } catch (e) {
        setBanner(errText(e))
      } finally {
        loading.value = false
      }
    }
    const loadUsers = async () => {
      try { users.value = await api.users.list() } catch (e) { /* non-fatal */ }
    }

    const selectUnit = async (node) => {
      try {
        const fresh = await api.orgStructure.getById(node.id)
        selected.value = fresh
        members.value = fresh.members || []
        showMemberPicker.value = false
        memberSearch.value = ''
      } catch (e) {
        setBanner(errText(e))
      }
    }

    const usersMap = computed(() => {
      const m = {}
      for (const u of users.value || []) m[String(u.id)] = u
      return m
    })

    const headName = computed(() => {
      const id = selected.value && selected.value.head_user_id
      const u = id && users.value.find((x) => String(x.id) === String(id))
      return u ? u.full_name : ''
    })
    const kindLabel = (k) => KIND_LABELS[k] || k

    const memberIds = computed(() => new Set(members.value.map((m) => String(m.id))))
    const pickableUsers = computed(() => {
      const q = memberSearch.value.trim().toLowerCase()
      return users.value
        .filter((u) => !memberIds.value.has(String(u.id)))
        .filter((u) => !q || `${u.full_name} ${u.email}`.toLowerCase().includes(q))
        .slice(0, 30)
    })

    const openCreate = (parent) => {
      Object.assign(modal, {
        open: true, editing: false, id: null,
        name: '', kind: '', parent_id: parent ? parent.id : '',
        head_user_id: '', sort_order: 0
      })
    }
    const openEdit = (node) => {
      Object.assign(modal, {
        open: true, editing: true, id: node.id,
        name: node.name || '', kind: node.kind || '',
        parent_id: node.parent_id || '', head_user_id: node.head_user_id || '',
        sort_order: node.sort_order || 0
      })
    }

    const saveModal = async () => {
      saving.value = true
      try {
        const payload = {
          name: modal.name.trim(),
          kind: modal.kind || null,
          parent_id: modal.parent_id || null,
          head_user_id: modal.head_user_id || null,
          sort_order: Number(modal.sort_order) || 0
        }
        if (modal.editing) {
          await api.orgStructure.update(modal.id, payload)
        } else {
          await api.orgStructure.create(payload)
        }
        modal.open = false
        await loadTree()
        if (selected.value) {
          const still = flatUnits.value.find((u) => String(u.id) === String(selected.value.id))
          if (still) await selectUnit(still); else selected.value = null
        }
      } catch (e) {
        setBanner(errText(e))
      } finally {
        saving.value = false
      }
    }

    const confirmRemove = async (node) => {
      if (!window.confirm(`Удалить узел «${node.name}»?`)) return
      try {
        await api.orgStructure.remove(node.id)
        if (selected.value && String(selected.value.id) === String(node.id)) selected.value = null
        await loadTree()
      } catch (e) {
        setBanner(errText(e))
      }
    }

    const assignMember = async (userId) => {
      try {
        await api.orgStructure.assign(userId, selected.value.id)
        await selectUnit(selected.value)
        await loadTree()
      } catch (e) { setBanner(errText(e)) }
    }
    const unassignMember = async (userId) => {
      try {
        await api.orgStructure.assign(userId, null)
        await selectUnit(selected.value)
        await loadTree()
      } catch (e) { setBanner(errText(e)) }
    }

    onMounted(async () => {
      if (!canView.value) return
      await Promise.all([loadTree(), loadUsers()])
    })

    return {
      canView, canEdit, tree, flatUnits, users, loading, saving, banner,
      selected, members, showMemberPicker, memberSearch, modal,
      selectUnit, headName, kindLabel, pickableUsers, usersMap,
      openCreate, openEdit, saveModal, confirmRemove, assignMember, unassignMember
    }
  }
}
</script>

<style scoped>
.org-structure-view {
  --apr-card-bg: rgba(255, 255, 255, 0.97);
  --apr-card-border: rgba(216, 224, 240, 0.92);
  --apr-card-shadow: 0 18px 42px rgba(15, 23, 42, 0.06);
  --apr-radius: 20px;
  --apr-ink: #0a1629;
  --apr-muted: #7d8592;
  --apr-soft: #f6f8fb;
  --oc-line: #cbd5e1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  min-height: calc(100vh - 84px);
}
:root[data-theme="dark"] .org-structure-view { --oc-line: rgba(255, 255, 255, 0.18); }
.org-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}
.org-head__title {
  font-size: 22px;
  font-weight: 700;
  color: var(--apr-ink);
  margin: 0;
}
.org-head__sub {
  margin: 4px 0 0;
  color: var(--apr-muted);
  font-size: 13px;
}
.org-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 13px;
}
.org-banner--error {
  background: rgba(239, 68, 68, 0.1);
  color: #b91c1c;
  border: 1px solid rgba(239, 68, 68, 0.25);
}
.org-banner button {
  border: none;
  background: transparent;
  cursor: pointer;
  color: inherit;
}
.org-layout {
  display: flex;
  gap: 16px;
  flex: 1;
  min-height: 0;
  align-items: stretch;
}
.org-tree-card {
  flex: 1 1 auto;
  min-width: 0;
  min-height: 0;
  max-height: calc(100vh - 170px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.org-detail-card {
  width: 340px;
  flex-shrink: 0;
  min-height: 0;
  max-height: calc(100vh - 170px);
  overflow: auto;
}
.org-chart-scroll {
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
  margin: -4px;
  padding: 4px;
}
.org-chart {
  display: flex;
  flex-wrap: nowrap;
  justify-content: center;
  gap: 40px;
  min-width: max-content;
  padding: 12px 16px 20px;
  margin: 0 auto;
}
.org-chart__root {
  display: flex;
  flex-direction: column;
  align-items: center;
}
@media (max-width: 1024px) {
  .org-layout { flex-direction: column; }
  .org-detail-card { width: auto; }
}
.org-card__title {
  font-size: 15px;
  font-weight: 700;
  color: var(--apr-ink);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.org-detail__kind {
  font-size: 11px;
  font-weight: 500;
  color: var(--apr-muted);
  background: var(--apr-soft);
  border: 1px solid var(--apr-card-border);
  padding: 1px 8px;
  border-radius: 999px;
}
.org-empty {
  color: var(--apr-muted);
  font-size: 13px;
  padding: 16px 8px;
}
.org-detail__row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--apr-card-border);
  font-size: 13px;
}
.org-detail__label { color: var(--apr-muted); }
.org-detail__value { color: var(--apr-ink); font-weight: 600; }
.org-detail__section { margin-top: 16px; }
.org-detail__section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 600;
  color: var(--apr-ink);
  margin-bottom: 8px;
}
.org-picker {
  background: var(--apr-soft);
  border: 1px solid var(--apr-card-border);
  border-radius: 12px;
  padding: 10px;
  margin-bottom: 10px;
}
.org-picker__list {
  max-height: 200px;
  overflow: auto;
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.org-picker__item {
  text-align: left;
  border: none;
  background: transparent;
  padding: 7px 9px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--apr-ink);
}
.org-picker__item span { color: var(--apr-muted); font-size: 11px; }
.org-picker__item:hover { background: var(--apr-card-bg); }
.org-members {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.org-members li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 9px;
  border-radius: 8px;
  font-size: 13px;
  color: var(--apr-ink);
}
.org-members li:hover { background: var(--apr-soft); }
.org-members em { color: var(--apr-muted); font-style: normal; font-size: 11px; margin-left: 6px; }
.org-members button {
  border: none;
  background: transparent;
  color: var(--apr-muted);
  cursor: pointer;
}
.org-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.org-form label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
  color: var(--apr-muted);
}
.org-native-select {
  width: 100%;
  padding: 8px 10px;
  font-size: 13px;
  color: var(--apr-ink);
  background: #fff;
  border: 1px solid var(--apr-card-border);
  border-radius: 10px;
  outline: none;
}
.org-native-select:focus {
  border-color: #6366f1;
}
</style>
