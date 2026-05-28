<template>
  <div class="approvals-page d-flex flex-column h-100">
    <div class="approvals-workspace flex-grow-1">
      <UiCard class="approvals-sidebar" padding="sm">
        <div class="sidebar-search-block">
          <UiInput
            v-model="filters.search"
            type="search"
            size="sm"
            icon-left="fas fa-search"
            clearable
            placeholder="Поиск шаблона..."
          />

          <UiSelect
            v-model="filters.entityType"
            size="sm"
            :options="meta.entity_types"
            label-key="label"
            value-key="value"
            placeholder="Все типы объектов"
          />

          <div v-if="allTags.length" class="tag-filter">
            <button
              v-for="tag in allTags"
              :key="tag"
              type="button"
              class="tag-chip"
              :class="{ active: filters.tag === tag }"
              @click="filters.tag = filters.tag === tag ? '' : tag"
            >
              <i class="fas fa-tag"></i>
              <span>{{ tag }}</span>
            </button>
          </div>
        </div>

        <div v-if="loadingTemplates" class="p-2 d-flex flex-column gap-2">
          <SkeletonLoader v-for="i in 5" :key="i" height="64px" />
        </div>

        <UiEmptyState
          v-else-if="!filteredTemplates.length"
          icon="fas fa-diagram-project"
          :title="hasActiveFilters ? 'Ничего не найдено' : 'Шаблонов пока нет'"
          :description="hasActiveFilters ? 'Попробуйте изменить или сбросить фильтры.' : 'Создайте первый шаблон, чтобы настроить маршрут согласования.'"
          size="sm"
          class="sidebar-empty"
        >
          <template #actions>
            <UiButton
              v-if="hasActiveFilters"
              variant="secondary"
              size="sm"
              icon-left="fas fa-rotate-left"
              @click="resetFilters"
            >
              Сбросить фильтры
            </UiButton>
          </template>
        </UiEmptyState>

        <div v-else class="template-list">
          <button
            v-for="template in filteredTemplates"
            :key="template.id"
            type="button"
            class="template-item"
            :class="{ active: selectedTemplateId === template.id }"
            :title="template.name"
            @click="trySelectTemplate(template.id)"
          >
            <div class="template-item-top">
              <span class="template-item-title">{{ template.name }}</span>
              <UiBadge
                v-if="template.active_instances_count > 0"
                variant="primary"
                size="sm"
                pill
              >
                {{ template.active_instances_count }}
              </UiBadge>
            </div>

            <div class="template-item-meta">
              <span>{{ entityLabel(template.entity_type) }}</span>
              <span class="dot">·</span>
              <span>{{ template.steps.length }} {{ stepWord(template.steps.length) }}</span>
            </div>

            <div class="template-item-foot">
              <UiBadge :variant="template.is_active ? 'success' : 'neutral'" size="sm" pill>
                {{ template.is_active ? 'Активен' : 'Черновик' }}
              </UiBadge>

              <span v-if="template.tags && template.tags.length" class="template-item-tags">
                <UiBadge v-for="t in template.tags.slice(0, 2)" :key="t" variant="neutral" size="sm" pill>{{ t }}</UiBadge>
                <UiBadge v-if="template.tags.length > 2" variant="neutral" size="sm" pill>+{{ template.tags.length - 2 }}</UiBadge>
              </span>
            </div>
          </button>
        </div>

        <div class="sidebar-footer">
          <UiButton variant="primary" size="sm" icon-left="fas fa-plus" block @click="createTemplate">
            Создать новый
          </UiButton>
        </div>
      </UiCard>

      <section class="approvals-stage">
        <UiCard class="stage-header-card" padding="sm">
          <div class="stage-header-row">
            <div class="stage-title-block">
              <h2 class="m-0 stage-title">Конструктор цепочек</h2>
              <UiBadge v-if="editor && isDirty" variant="warning" size="sm" pill icon="fas fa-circle">
                Не сохранено
              </UiBadge>
              <UiBadge v-else-if="editor && editor.id" variant="success" size="sm" pill icon="fas fa-check">
                Сохранено
              </UiBadge>
            </div>

            <div v-if="editor" class="stage-actions">
              <label class="active-toggle" :class="{ on: editor.is_active }">
                <input v-model="editor.is_active" type="checkbox" />
                <span class="toggle-slider"></span>
                <span class="toggle-label">{{ editor.is_active ? 'Активен' : 'Черновик' }}</span>
              </label>

              <UiButton
                v-if="editor.id"
                variant="secondary"
                size="sm"
                icon-left="fas fa-copy"
                :loading="duplicating"
                :disabled="duplicating"
                @click="onDuplicate"
              >
                Дублировать
              </UiButton>

              <UiButton
                v-if="isDirty"
                variant="secondary"
                size="sm"
                @click="resetEditor"
              >
                Отменить
              </UiButton>

              <UiButton
                variant="primary"
                size="sm"
                icon-left="fas fa-check"
                :loading="saving"
                :disabled="!editor || saving || !isDirty"
                @click="saveTemplate"
              >
                Сохранить
              </UiButton>
            </div>
          </div>
        </UiCard>

        <UiEmptyState
          v-if="!editor"
          icon="fas fa-arrow-pointer"
          title="Выберите шаблон слева"
          description="Или создайте новый, чтобы настроить маршрут согласования."
          class="stage-empty-card"
        >
          <template #actions>
            <UiButton variant="primary" size="sm" icon-left="fas fa-plus" @click="createTemplate">
              Создать шаблон
            </UiButton>
          </template>
        </UiEmptyState>

        <template v-else>
          <div class="stage-body">
            <UiCard class="process-card" padding="md">
              <div class="process-grid">
                <UiInput
                  v-model="editor.name"
                  label="Название процесса"
                  placeholder="Например, Договор аренды (ОФИС)"
                  :error="validation.name"
                  required
                />

                <UiSelect
                  v-model="editor.entity_type"
                  label="Тип объекта"
                  :options="meta.entity_types"
                  label-key="label"
                  value-key="value"
                />
              </div>

              <div class="process-grid process-grid--single">
                <UiChipInput
                  v-model="editor.tags"
                  label="Метки"
                  placeholder="Добавить метку и Enter..."
                />
              </div>

              <details class="advanced">
                <summary><i class="fas fa-cog mr-1"></i>Технические настройки</summary>
                <div class="advanced-body">
                  <UiInput
                    v-model="editor.code"
                    label="Код шаблона"
                    placeholder="template_lease_v2"
                    hint="Необязательное поле для API-привязок и автоматизаций."
                  />

                  <UiTextarea
                    v-model="editor.description"
                    label="Описание"
                    rows="3"
                    placeholder="Когда использовать эту цепочку и что она проверяет."
                  />

                  <UiButton
                    v-if="editor.id"
                    variant="danger"
                    size="sm"
                    icon-left="fas fa-trash"
                    @click="onDelete"
                  >
                    Удалить шаблон
                  </UiButton>
                </div>
              </details>
            </UiCard>

            <UiCard class="route-section" padding="md">
              <header class="route-header">
                <div>
                  <h3 class="m-0 route-title"><i class="fas fa-route mr-1"></i>Маршрут согласования</h3>
                  <small class="text-muted">Перетаскивайте шаги или используйте стрелки для изменения порядка.</small>
                </div>
                <UiButton variant="primary" size="sm" icon-left="fas fa-plus" @click="addRootStep">
                  Добавить шаг
                </UiButton>
              </header>

              <UiEmptyState
                v-if="!orderedSteps.length"
                icon="fas fa-plus-circle"
                title="Пока нет ни одного шага"
                description="Добавьте первый шаг, чтобы собрать маршрут согласования."
                size="sm"
                class="route-empty"
              >
                <template #actions>
                  <UiButton variant="primary" size="sm" icon-left="fas fa-plus" @click="addRootStep">
                    Добавить первый шаг
                  </UiButton>
                </template>
              </UiEmptyState>

              <div v-else class="route-list">
                <div
                  v-for="step in visibleOrderedSteps"
                  :key="step.client_id"
                  class="route-row"
                  :class="{ dragging: dragOver === step.client_id }"
                  :style="{ '--depth': step.depth }"
                  :draggable="dragEnabledFor === step.client_id"
                  @dragstart="onDragStart($event, step)"
                  @dragover.prevent="onDragOver($event, step)"
                  @dragleave="dragOver = null"
                  @drop.prevent="onDrop($event, step)"
                  @dragend="onDragEnd"
                >
                  <div class="route-row-rail">
                    <span v-if="step.depth > 0" class="branch-line"></span>
                    <span class="route-marker" :class="{ child: step.depth > 0 }">{{ step.dotted_order }}</span>
                  </div>

                  <article class="step-card">
                    <div class="step-card-head">
                      <UiIconButton
                        v-if="step.has_children"
                        :icon="isCollapsed(step.client_id) ? 'fas fa-chevron-right' : 'fas fa-chevron-down'"
                        :label="isCollapsed(step.client_id) ? 'Развернуть' : 'Свернуть'"
                        size="xs"
                        variant="ghost"
                        @click="toggleStep(step.client_id)"
                      />
                      <span v-else class="step-head-spacer"></span>

                      <i
                        class="drag-handle fas fa-grip-vertical"
                        title="Перетащите для перемещения"
                        @mousedown.stop="enableDrag(step.client_id)"
                        @mouseup.stop="disableDrag"
                        @mouseleave="disableDrag"
                      ></i>

                      <input
                        v-model.trim="step.title"
                        type="text"
                        class="step-title-input"
                        :class="{ 'is-invalid': stepValidation(step).title }"
                        placeholder="Название шага, например: Юридический аудит"
                      />

                      <UiBadge v-if="!step.is_required" variant="neutral" size="sm" pill>
                        Необязательно
                      </UiBadge>

                      <div class="step-tools">
                        <UiIconButton
                          icon="fas fa-code-branch"
                          label="Добавить дочерний шаг"
                          size="xs"
                          variant="ghost"
                          @click="addChildStep(step.client_id)"
                        />
                        <UiIconButton
                          icon="fas fa-arrow-up"
                          label="Вверх"
                          size="xs"
                          variant="ghost"
                          :disabled="!canMoveUp(step)"
                          @click="moveStep(step.client_id, -1)"
                        />
                        <UiIconButton
                          icon="fas fa-arrow-down"
                          label="Вниз"
                          size="xs"
                          variant="ghost"
                          :disabled="!canMoveDown(step)"
                          @click="moveStep(step.client_id, 1)"
                        />
                        <UiIconButton
                          icon="fas fa-times"
                          label="Удалить шаг"
                          size="xs"
                          variant="danger"
                          @click="onRemoveStep(step.client_id)"
                        />
                      </div>
                    </div>

                    <div class="step-card-body">
                      <div class="form-group">
                        <label class="field-label">Кто согласует</label>
                        <UiTabs
                          :model-value="step.assignee_type"
                          :tabs="assigneeTabs"
                          variant="segment"
                          size="sm"
                          @update:modelValue="setAssigneeType(step, $event)"
                        />
                        <UiSelect
                          v-if="step.assignee_type === 'user'"
                          v-model="step.assignee_user_id"
                          size="sm"
                          :options="meta.users"
                          label-key="label"
                          value-key="id"
                          placeholder="Выберите пользователя"
                          :error="stepValidation(step).assignee"
                        />
                        <UiSelect
                          v-else
                          v-model="step.assignee_role_id"
                          size="sm"
                          :options="meta.roles"
                          label-key="label"
                          value-key="id"
                          placeholder="Выберите роль"
                          :error="stepValidation(step).assignee"
                        />
                      </div>

                      <div class="form-group">
                        <UiTextarea
                          v-model="step.description"
                          label="Что проверить"
                          rows="3"
                          placeholder="Например: проверить сумму, реквизиты, комплект приложений..."
                        />
                      </div>
                    </div>

                    <div class="step-card-foot">
                      <label class="check-label">
                        <input v-model="step.is_required" type="checkbox" />
                        <span>Шаг обязателен</span>
                      </label>
                    </div>
                  </article>
                </div>

                <UiButton
                  variant="secondary"
                  size="sm"
                  icon-left="fas fa-plus"
                  @click="addRootStep"
                >
                  Добавить следующий шаг
                </UiButton>
              </div>
            </UiCard>

            <footer class="stage-footer text-muted small">
              <span>Всего шаблонов: {{ templates.length }}</span>
              <span>·</span>
              <span>Активных: {{ activeTemplateCount }}</span>
              <span v-if="lastUpdatedLabel">· Последнее изменение: {{ lastUpdatedLabel }}</span>
            </footer>
          </div>
        </template>
      </section>
    </div>
  </div>
</template>

<script>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../services/api'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'
import SkeletonLoader from '../components/ui/SkeletonLoader.vue'
import {
  UiBadge,
  UiButton,
  UiCard,
  UiChipInput,
  UiEmptyState,
  UiIconButton,
  UiInput,
  UiSelect,
  UiTabs,
  UiTextarea,
} from '../components/ui'

const createClientId = () => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  return `step-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

const createStep = (overrides = {}) => ({
  client_id: createClientId(),
  parent_client_id: null,
  title: '',
  description: '',
  assignee_type: 'user',
  assignee_user_id: '',
  assignee_role_id: '',
  is_required: true,
  sort_index: 1,
  ...overrides,
})

const blankTemplate = () => ({
  id: null,
  name: '',
  code: '',
  description: '',
  entity_type: 'outgoing_document',
  is_active: false,
  tags: [],
  steps: [],
})

const formatDateTime = (value) => {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export default {
  name: 'Approvals',
  components: {
    SkeletonLoader,
    UiBadge,
    UiButton,
    UiCard,
    UiChipInput,
    UiEmptyState,
    UiIconButton,
    UiInput,
    UiSelect,
    UiTabs,
    UiTextarea,
  },
  setup() {
    const toast = useToast()
    const { confirm } = useConfirm()

    const meta = ref({ entity_types: [], assignee_types: [], users: [], roles: [] })
    const templates = ref([])
    const loadingTemplates = ref(false)
    const saving = ref(false)
    const duplicating = ref(false)
    const selectedTemplateId = ref(null)
    const collapsedByTemplate = ref({})
    const filters = reactive({ search: '', entityType: '', tag: '' })
    const editor = ref(null)
    const editorBaseline = ref('')
    const dragOver = ref(null)
    const dragEnabledFor = ref(null)
    let draggedStep = null

    const assigneeTabs = [
      { value: 'user', label: 'Пользователь' },
      { value: 'role', label: 'Роль' },
    ]

    const entityLabel = (value) => meta.value.entity_types.find((item) => item.value === value)?.label || value || '—'

    const stepWord = (count) => {
      const mod10 = count % 10
      const mod100 = count % 100
      if (mod10 === 1 && mod100 !== 11) return 'шаг'
      if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return 'шага'
      return 'шагов'
    }

    const allTags = computed(() => {
      const set = new Set()
      templates.value.forEach((template) => (template.tags || []).forEach((tag) => set.add(tag)))
      return Array.from(set).sort()
    })

    const hasActiveFilters = computed(() => !!(filters.search || filters.entityType || filters.tag))
    const resetFilters = () => {
      filters.search = ''
      filters.entityType = ''
      filters.tag = ''
    }

    const filteredTemplates = computed(() => {
      const query = filters.search.trim().toLowerCase()
      return templates.value.filter((template) => {
        if (filters.entityType && template.entity_type !== filters.entityType) return false
        if (filters.tag && !(template.tags || []).includes(filters.tag)) return false
        if (!query) return true
        return [template.name, template.code, template.description, entityLabel(template.entity_type)]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase().includes(query))
      })
    })

    const activeTemplateCount = computed(() => templates.value.filter((template) => template.is_active).length)

    const lastUpdatedLabel = computed(() => {
      const dates = templates.value.map((template) => template.updated_at || template.created_at).filter(Boolean).sort()
      return formatDateTime(dates.at(-1) || null)
    })

    const normalizeEditor = (template) => {
      const normalized = { ...blankTemplate(), ...template, tags: [...(template?.tags || [])], steps: [] }
      normalized.steps = (template?.steps || []).map((step, index) => createStep({
        client_id: step.id || createClientId(),
        parent_client_id: step.parent_step_id || null,
        title: step.title || '',
        description: step.description || '',
        assignee_type: step.assignee_type || 'user',
        assignee_user_id: step.assignee_user_id || '',
        assignee_role_id: step.assignee_role_id || '',
        is_required: step.is_required !== false,
        sort_index: Number.isFinite(step.step_order) ? step.step_order : index + 1,
      }))
      return normalized
    }

    const computeBaseline = (value) => JSON.stringify(value)
    const isDirty = computed(() => editor.value && computeBaseline(editor.value) !== editorBaseline.value)

    const orderedSteps = computed(() => {
      const steps = editor.value?.steps || []
      const byParent = new Map()

      for (const step of steps) {
        const key = step.parent_client_id || '__root__'
        const bucket = byParent.get(key) || []
        bucket.push(step)
        byParent.set(key, bucket)
      }

      for (const arr of byParent.values()) {
        arr.sort((a, b) => a.sort_index - b.sort_index || (a.title || '').localeCompare(b.title || '', 'ru'))
      }

      const depthFirst = []
      const visit = (parent, depth, prefix) => {
        const items = byParent.get(parent || '__root__') || []
        items.forEach((step, index) => {
          const dotted = prefix ? `${prefix}.${index + 1}` : `${index + 1}`
          Object.assign(step, {
            depth,
            step_order: depthFirst.length + 1,
            dotted_order: dotted,
            has_children: (byParent.get(step.client_id) || []).length > 0,
            sibling_count: items.length,
            sibling_index: index,
          })
          depthFirst.push(step)
          visit(step.client_id, depth + 1, dotted)
        })
      }

      visit(null, 0, '')
      return depthFirst
    })

    const currentCollapseKey = () => editor.value?.id || '__new__'
    const isCollapsed = (clientId) => Boolean((collapsedByTemplate.value[currentCollapseKey()] || {})[clientId])

    const visibleOrderedSteps = computed(() => {
      const ordered = orderedSteps.value
      const byId = new Map(ordered.map((step) => [step.client_id, step]))
      const collapsed = collapsedByTemplate.value[currentCollapseKey()] || {}
      return ordered.filter((step) => {
        let parent = step.parent_client_id
        while (parent) {
          if (collapsed[parent]) return false
          parent = byId.get(parent)?.parent_client_id || null
        }
        return true
      })
    })

    const toggleStep = (clientId) => {
      const key = currentCollapseKey()
      const map = collapsedByTemplate.value[key] || {}
      collapsedByTemplate.value = {
        ...collapsedByTemplate.value,
        [key]: { ...map, [clientId]: !map[clientId] },
      }
    }

    const canMoveUp = (step) => step.sibling_index > 0
    const canMoveDown = (step) => step.sibling_index < step.sibling_count - 1

    const validation = computed(() => {
      const result = {}
      if (editor.value && !editor.value.name?.trim()) result.name = 'Введите название шаблона'
      return result
    })

    const stepValidation = (step) => {
      const result = {}
      if (!step.title?.trim()) result.title = 'Введите название шага'
      if (step.assignee_type === 'user' && !step.assignee_user_id) result.assignee = 'Выберите пользователя'
      if (step.assignee_type === 'role' && !step.assignee_role_id) result.assignee = 'Выберите роль'
      return result
    }

    const isValid = computed(() => {
      if (Object.keys(validation.value).length) return false
      const steps = editor.value?.steps || []
      return steps.every((step) => Object.keys(stepValidation(step)).length === 0)
    })

    const loadMeta = async () => {
      try {
        const data = await api.approvals.meta()
        meta.value = data || meta.value
      } catch (error) {
        console.error(error)
      }
    }

    const loadTemplates = async () => {
      loadingTemplates.value = true
      try {
        const data = await api.approvals.listTemplates()
        templates.value = Array.isArray(data) ? data : []
        if (selectedTemplateId.value) {
          const fresh = templates.value.find((template) => template.id === selectedTemplateId.value)
          if (fresh) {
            editor.value = normalizeEditor(fresh)
            editorBaseline.value = computeBaseline(editor.value)
          }
        }
      } catch (error) {
        toast.error(error?.response?.data?.detail || 'Не удалось загрузить шаблоны.')
      } finally {
        loadingTemplates.value = false
      }
    }

    const reloadAll = async () => {
      try {
        await Promise.all([loadMeta(), loadTemplates()])
      } catch (error) {
        toast.error('Не удалось обновить данные блока согласований.')
      }
    }

    const selectTemplate = (id) => {
      selectedTemplateId.value = id
      const template = templates.value.find((item) => item.id === id)
      editor.value = template ? normalizeEditor(template) : null
      editorBaseline.value = editor.value ? computeBaseline(editor.value) : ''
    }

    const trySelectTemplate = async (id) => {
      if (id === selectedTemplateId.value) return
      if (isDirty.value) {
        const ok = await confirm({
          title: 'Несохранённые изменения',
          message: 'У вас есть несохранённые изменения. Перейти к другому шаблону, потеряв их?',
          confirmText: 'Да, перейти',
          variant: 'warning',
        })
        if (!ok) return
      }
      selectTemplate(id)
    }

    const createTemplate = async () => {
      if (isDirty.value) {
        const ok = await confirm({
          title: 'Несохранённые изменения',
          message: 'Создать новый шаблон, потеряв текущие изменения?',
          confirmText: 'Да, создать',
          variant: 'warning',
        })
        if (!ok) return
      }
      selectedTemplateId.value = null
      editor.value = blankTemplate()
      editorBaseline.value = computeBaseline(editor.value)
    }

    const resetEditor = async () => {
      const ok = await confirm({
        title: 'Отменить изменения?',
        message: 'Все несохранённые правки будут утеряны.',
        confirmText: 'Да, отменить',
        variant: 'warning',
      })
      if (!ok) return
      if (selectedTemplateId.value) {
        selectTemplate(selectedTemplateId.value)
      } else {
        editor.value = blankTemplate()
        editorBaseline.value = computeBaseline(editor.value)
      }
    }

    const siblingSteps = (parentId) =>
      (editor.value?.steps || [])
        .filter((step) => (step.parent_client_id || null) === (parentId || null))
        .sort((a, b) => a.sort_index - b.sort_index)

    const reindexSiblings = (parentId) => {
      siblingSteps(parentId).forEach((step, index) => {
        step.sort_index = index + 1
      })
    }

    const setAssigneeType = (step, type) => {
      step.assignee_type = type
      if (type === 'user') {
        step.assignee_role_id = ''
        if (!step.assignee_user_id) step.assignee_user_id = meta.value.users[0]?.id || ''
      } else {
        step.assignee_user_id = ''
        if (!step.assignee_role_id) step.assignee_role_id = meta.value.roles[0]?.id || ''
      }
    }

    const addRootStep = () => {
      if (!editor.value) editor.value = blankTemplate()
      const siblings = siblingSteps(null)
      editor.value.steps.push(createStep({
        parent_client_id: null,
        sort_index: siblings.length + 1,
        assignee_user_id: meta.value.users[0]?.id || '',
      }))
    }

    const addChildStep = (parentClientId) => {
      const siblings = siblingSteps(parentClientId)
      editor.value.steps.push(createStep({
        parent_client_id: parentClientId,
        sort_index: siblings.length + 1,
        assignee_user_id: meta.value.users[0]?.id || '',
      }))
      const key = currentCollapseKey()
      const map = collapsedByTemplate.value[key] || {}
      if (map[parentClientId]) {
        collapsedByTemplate.value = {
          ...collapsedByTemplate.value,
          [key]: { ...map, [parentClientId]: false },
        }
      }
    }

    const collectDescendants = (clientId) => {
      const ids = new Set([clientId])
      let changed = true
      while (changed) {
        changed = false
        for (const step of editor.value.steps) {
          if (step.parent_client_id && ids.has(step.parent_client_id) && !ids.has(step.client_id)) {
            ids.add(step.client_id)
            changed = true
          }
        }
      }
      return ids
    }

    const onRemoveStep = async (clientId) => {
      const step = editor.value.steps.find((item) => item.client_id === clientId)
      if (!step) return
      const descendants = collectDescendants(clientId)
      const childCount = descendants.size - 1
      const ok = await confirm({
        title: childCount ? `Удалить шаг и ${childCount} дочерних?` : 'Удалить шаг?',
        message: childCount
          ? 'Шаг и все вложенные шаги будут удалены безвозвратно.'
          : `Шаг «${step.title || 'Без названия'}» будет удалён.`,
        confirmText: 'Удалить',
        variant: 'danger',
      })
      if (!ok) return
      editor.value.steps = editor.value.steps.filter((item) => !descendants.has(item.client_id))
      reindexSiblings(step.parent_client_id)
    }

    const moveStep = (clientId, direction) => {
      const step = editor.value.steps.find((item) => item.client_id === clientId)
      if (!step) return
      const siblings = siblingSteps(step.parent_client_id)
      const index = siblings.findIndex((item) => item.client_id === clientId)
      const next = index + direction
      if (next < 0 || next >= siblings.length) return
      const a = siblings[index]
      const b = siblings[next]
      const tmp = a.sort_index
      a.sort_index = b.sort_index
      b.sort_index = tmp
    }

    const onDragStart = (event, step) => {
      if (dragEnabledFor.value !== step.client_id) {
        event.preventDefault()
        return
      }
      draggedStep = step
      event.dataTransfer.effectAllowed = 'move'
      try {
        event.dataTransfer.setData('text/plain', step.client_id)
      } catch (_) {
        // noop
      }
    }

    const isDescendant = (potentialDescId, ancestorId) => {
      let current = editor.value.steps.find((step) => step.client_id === potentialDescId)
      while (current?.parent_client_id) {
        if (current.parent_client_id === ancestorId) return true
        current = editor.value.steps.find((step) => step.client_id === current.parent_client_id)
      }
      return false
    }

    const onDragOver = (event, step) => {
      if (!draggedStep || draggedStep.client_id === step.client_id) return
      if (isDescendant(step.client_id, draggedStep.client_id)) return
      dragOver.value = step.client_id
    }

    const onDragEnd = () => {
      draggedStep = null
      dragOver.value = null
      dragEnabledFor.value = null
    }

    const enableDrag = (clientId) => {
      dragEnabledFor.value = clientId
    }

    const disableDrag = () => {
      if (!draggedStep) dragEnabledFor.value = null
    }

    const onDrop = (event, target) => {
      if (!draggedStep) return
      if (draggedStep.client_id === target.client_id) {
        onDragEnd()
        return
      }
      if (isDescendant(target.client_id, draggedStep.client_id)) {
        toast.warning('Нельзя перетащить шаг внутрь его собственного потомка')
        onDragEnd()
        return
      }

      const targetStep = editor.value.steps.find((step) => step.client_id === target.client_id)
      if (!targetStep) {
        onDragEnd()
        return
      }

      const oldParent = draggedStep.parent_client_id
      const newParent = targetStep.parent_client_id
      const dragged = editor.value.steps.find((step) => step.client_id === draggedStep.client_id)
      if (!dragged) {
        onDragEnd()
        return
      }

      dragged.parent_client_id = newParent
      const siblings = siblingSteps(newParent).filter((step) => step.client_id !== dragged.client_id)
      const targetIdx = siblings.findIndex((step) => step.client_id === target.client_id)
      siblings.splice(targetIdx >= 0 ? targetIdx : siblings.length, 0, dragged)
      siblings.forEach((step, index) => {
        step.sort_index = index + 1
      })

      if (oldParent !== newParent) reindexSiblings(oldParent)
      onDragEnd()
    }

    const buildPayload = () => ({
      name: editor.value.name.trim(),
      code: editor.value.code?.trim() || null,
      description: editor.value.description?.trim() || null,
      entity_type: editor.value.entity_type,
      is_active: !!editor.value.is_active,
      tags: editor.value.tags || [],
      steps: editor.value.steps.map((step) => ({
        client_id: step.client_id,
        parent_client_id: step.parent_client_id,
        title: step.title.trim(),
        description: step.description?.trim() || null,
        assignee_type: step.assignee_type,
        assignee_user_id: step.assignee_user_id || null,
        assignee_role_id: step.assignee_role_id || null,
        is_required: !!step.is_required,
        step_order: step.sort_index,
      })),
    })

    const saveTemplate = async () => {
      if (!editor.value) return
      if (!isValid.value) {
        toast.warning('Заполните обязательные поля')
        return
      }
      saving.value = true
      try {
        const payload = buildPayload()
        let saved
        if (editor.value.id) {
          saved = await api.approvals.updateTemplate(editor.value.id, payload)
        } else {
          saved = await api.approvals.createTemplate(payload)
        }

        const index = templates.value.findIndex((template) => template.id === saved.id)
        if (index >= 0) templates.value[index] = saved
        else templates.value.unshift(saved)

        selectedTemplateId.value = saved.id
        editor.value = normalizeEditor(saved)
        editorBaseline.value = computeBaseline(editor.value)
        toast.success('Сохранено')
      } catch (error) {
        toast.error(error?.response?.data?.detail || 'Не удалось сохранить шаблон.')
      } finally {
        saving.value = false
      }
    }

    const onDuplicate = async () => {
      if (!editor.value?.id) return
      if (isDirty.value) {
        const ok = await confirm({
          title: 'Дублировать шаблон',
          message: 'Текущие несохранённые изменения не попадут в копию. Продолжить?',
          confirmText: 'Дублировать',
        })
        if (!ok) return
      }
      duplicating.value = true
      try {
        const data = await api.approvals.duplicateTemplate(editor.value.id)
        templates.value.unshift(data)
        selectedTemplateId.value = data.id
        editor.value = normalizeEditor(data)
        editorBaseline.value = computeBaseline(editor.value)
        toast.success('Создана копия')
      } catch (error) {
        toast.error(error?.response?.data?.detail || 'Не удалось дублировать шаблон.')
      } finally {
        duplicating.value = false
      }
    }

    const onDelete = async () => {
      if (!editor.value?.id) return
      let usage = { active_instances_count: 0, total_instances_count: 0 }
      try {
        const data = await api.approvals.templateUsage(editor.value.id)
        usage = data || usage
      } catch (error) {
        // ignore
      }

      const lines = [`Шаблон «${editor.value.name}» будет удалён.`]
      if (usage.active_instances_count) {
        lines.push(`⚠ Сейчас по этому шаблону идёт ${usage.active_instances_count} активных согласований — они будут отвязаны.`)
      }
      if (usage.total_instances_count) {
        lines.push(`Всего по шаблону было запущено ${usage.total_instances_count} согласований.`)
      }

      const ok = await confirm({
        title: 'Удалить шаблон?',
        message: lines.join('\n'),
        confirmText: 'Удалить',
        variant: 'danger',
      })
      if (!ok) return

      try {
        await api.approvals.removeTemplate(editor.value.id)
        templates.value = templates.value.filter((template) => template.id !== editor.value.id)
        editor.value = null
        editorBaseline.value = ''
        selectedTemplateId.value = null
        toast.success('Шаблон удалён')
      } catch (error) {
        toast.error(error?.response?.data?.detail || 'Не удалось удалить шаблон.')
      }
    }

    onMounted(reloadAll)

    return {
      meta,
      templates,
      loadingTemplates,
      saving,
      duplicating,
      selectedTemplateId,
      editor,
      filters,
      hasActiveFilters,
      dragOver,
      dragEnabledFor,
      allTags,
      assigneeTabs,
      isDirty,
      validation,
      stepValidation,
      orderedSteps,
      visibleOrderedSteps,
      isCollapsed,
      toggleStep,
      filteredTemplates,
      activeTemplateCount,
      lastUpdatedLabel,
      entityLabel,
      stepWord,
      resetFilters,
      trySelectTemplate,
      createTemplate,
      resetEditor,
      addRootStep,
      addChildStep,
      onRemoveStep,
      moveStep,
      canMoveUp,
      canMoveDown,
      setAssigneeType,
      onDragStart,
      onDragOver,
      onDragEnd,
      onDrop,
      enableDrag,
      disableDrag,
      saveTemplate,
      onDuplicate,
      onDelete,
    }
  },
}
</script>

<style scoped>
.approvals-page {
  padding: var(--space-3);
  gap: var(--space-3);
}

.approvals-workspace {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: var(--space-3);
  min-height: 0;
}

.approvals-sidebar {
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.sidebar-search-block {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.tag-filter {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  background: var(--color-surface);
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  cursor: pointer;
  transition:
    background-color var(--dur-fast) ease,
    border-color var(--dur-fast) ease,
    color var(--dur-fast) ease;
}

.tag-chip:hover {
  background: var(--color-surface-2);
  border-color: var(--color-border-strong);
  color: var(--color-text);
}

.tag-chip.active {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.sidebar-empty {
  min-height: 220px;
}

.template-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  overflow-y: auto;
  min-height: 0;
}

.template-item {
  width: 100%;
  text-align: left;
  padding: var(--space-3);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  cursor: pointer;
  transition:
    border-color var(--dur-fast) ease,
    background-color var(--dur-fast) ease,
    box-shadow var(--dur-fast) ease;
}

.template-item:hover {
  border-color: var(--color-primary);
  background: var(--color-surface-2);
}

.template-item.active {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
  box-shadow: inset 3px 0 0 var(--color-primary);
}

.template-item-top,
.template-item-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.template-item-top {
  margin-bottom: var(--space-1);
}

.template-item-title {
  font-size: var(--text-base);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.template-item-meta {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin-bottom: var(--space-2);
}

.template-item-tags {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  flex-wrap: wrap;
}

.sidebar-footer {
  margin-top: auto;
  padding-top: var(--space-2);
  border-top: 1px solid var(--color-border-subtle);
}

.approvals-stage {
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.stage-header-card {
  flex-shrink: 0;
}

.stage-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.stage-title-block {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.stage-title {
  font-size: var(--text-xl);
  font-weight: var(--fw-bold);
  color: var(--color-text);
}

.stage-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.active-toggle {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  cursor: pointer;
}

.active-toggle input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.toggle-slider {
  position: relative;
  width: 38px;
  height: 22px;
  border-radius: var(--radius-pill);
  background: var(--color-border-strong);
  transition: background-color var(--dur-fast) ease;
}

.toggle-slider::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fff;
  transition: transform var(--dur-fast) ease;
  box-shadow: var(--shadow-xs);
}

.active-toggle input:checked + .toggle-slider {
  background: var(--color-success);
}

.active-toggle input:checked + .toggle-slider::after {
  transform: translateX(16px);
}

.active-toggle.on {
  color: var(--color-success);
  font-weight: var(--fw-semibold);
}

.stage-empty-card {
  flex: 1;
  min-height: 280px;
}

.stage-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  min-height: 0;
}

.process-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-3);
}

.process-grid--single {
  grid-template-columns: 1fr;
  margin-top: var(--space-3);
}

.advanced {
  margin-top: var(--space-3);
  border-top: 1px solid var(--color-border-subtle);
  padding-top: var(--space-3);
}

.advanced summary {
  cursor: pointer;
  color: var(--color-text);
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
}

.advanced-body {
  margin-top: var(--space-3);
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-3);
  align-items: start;
}

.advanced-body > :last-child:nth-child(odd) {
  grid-column: 1 / -1;
}

.route-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.route-title {
  font-size: var(--text-lg);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.route-empty {
  min-height: 220px;
}

.route-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.route-row {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr);
  gap: var(--space-2);
  align-items: start;
}

.route-row.dragging .step-card {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}

.route-row-rail {
  position: relative;
  padding-top: var(--space-3);
  padding-left: calc(var(--depth) * 12px);
}

.branch-line {
  position: absolute;
  left: calc(var(--depth) * 12px - 6px);
  top: 0;
  bottom: 0;
  width: 1px;
  background: var(--color-border-subtle);
}

.route-marker {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 30px;
  min-height: 30px;
  padding: 0 var(--space-2);
  border-radius: var(--radius-pill);
  background: var(--color-surface-3);
  color: var(--color-text);
  font-size: var(--text-sm);
  font-weight: var(--fw-bold);
}

.route-marker.child {
  background: var(--color-surface-2);
}

.step-card {
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  overflow: hidden;
}

.step-card-head {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  border-bottom: 1px solid var(--color-border-subtle);
}

.step-head-spacer {
  width: 22px;
  flex-shrink: 0;
}

.drag-handle {
  color: var(--color-text-subtle);
  cursor: grab;
  padding: 0 var(--space-1);
}

.drag-handle:active {
  cursor: grabbing;
}

.step-title-input {
  flex: 1;
  min-width: 0;
  border: none;
  border-bottom: 1px solid transparent;
  background: transparent;
  padding: var(--space-1) 0;
  font-size: var(--text-base);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
  outline: none;
}

.step-title-input::placeholder {
  color: var(--color-text-subtle);
}

.step-title-input:focus {
  border-bottom-color: var(--color-primary);
}

.step-title-input.is-invalid {
  border-bottom-color: var(--color-danger);
}

.step-tools {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  margin-left: auto;
}

.step-card-body {
  padding: var(--space-3);
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-3);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.field-label {
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.step-card-foot {
  padding: var(--space-3);
  border-top: 1px dashed var(--color-border-subtle);
  background: var(--color-surface-2);
}

.check-label {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-text);
  cursor: pointer;
}

.stage-footer {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
  padding: 0 var(--space-1);
}

@media (max-width: 1180px) {
  .approvals-workspace {
    grid-template-columns: 280px minmax(0, 1fr);
  }

  .step-card-body,
  .process-grid,
  .advanced-body {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .approvals-workspace {
    grid-template-columns: 1fr;
  }

  .approvals-sidebar {
    max-height: 40vh;
  }

  .stage-actions,
  .route-header {
    width: 100%;
  }
}

@media (max-width: 640px) {
  .stage-actions,
  .stage-header-row,
  .route-header {
    flex-direction: column;
    align-items: stretch;
  }

  .step-card-head {
    flex-wrap: wrap;
  }

  .step-tools {
    margin-left: 0;
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
