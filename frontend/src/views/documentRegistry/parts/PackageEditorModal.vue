<template>
  <div v-if="show" class="modal-overlay" v-modal-close="() => $emit('close')">
    <div class="modal-content" @click.stop style="max-width: 900px;">
      <div class="modal-header">
        <h3 class="m-0">{{ isEditing ? 'Редактирование пачки' : 'Новая пачка' }}</h3>
        <button class="btn btn-sm btn-secondary" @click="$emit('close')">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <form @submit.prevent="$emit('save')" class="modal-body">
        <div class="form-grid">
          <div class="form-group span-2">
            <label class="small text-muted mb-1">Название *</label>
            <input v-model="packageForm.title" type="text" class="form-control" required>
          </div>
          <div class="form-group">
            <label class="small text-muted mb-1">Статус</label>
            <select v-model="packageForm.status" class="form-control">
              <option value="draft">Проект</option>
              <option value="sent">Направлен</option>
              <option value="received">Получен</option>
              <option value="archived">Архив</option>
            </select>
          </div>
          <div class="form-group">
            <label class="small text-muted mb-1">Дата</label>
            <input v-model="packageForm.package_date" type="date" class="form-control">
          </div>
          <div class="form-group">
            <label class="small text-muted mb-1">Проект</label>
            <select v-model="packageForm.project_id" class="form-control">
              <option value="">Не выбран</option>
              <option v-for="deal in deals" :key="deal.id" :value="deal.id">
                {{ deal.title }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label class="small text-muted mb-1">Контрагент</label>
            <select v-model="packageForm.counterparty_id" class="form-control">
              <option value="">Не выбран</option>
              <option v-for="company in companies" :key="company.id" :value="company.id">
                {{ company.name }}
              </option>
            </select>
          </div>
        </div>

        <div class="relations-block">
          <div class="relations-header">
            <div class="fw-600">Состав пачки</div>
            <div class="d-flex gap-2">
              <select
                :value="selectedPackageDocumentId"
                @change="$emit('update:selectedPackageDocumentId', $event.target.value)"
                class="form-control form-control-sm"
                style="min-width: 260px;"
              >
                <option value="">Выберите документ</option>
                <option v-for="doc in documentOptions" :key="doc.id" :value="doc.id">
                  {{ doc.title }}
                </option>
              </select>
              <button type="button" class="btn btn-sm btn-outline-primary" @click="$emit('add-package-item')">
                Добавить
              </button>
            </div>
          </div>
          <div v-if="packageItems.length === 0" class="text-muted small">
            Документы в пачке пока не добавлены.
          </div>
          <div v-else class="relations-list">
            <div v-for="item in packageItems" :key="item.id" class="relations-item">
              <div class="relations-name">{{ getDocumentTitle(item.document_id) }}</div>
              <button type="button" class="btn btn-sm btn-icon text-danger" @click="$emit('remove-package-item', item)">
                <i class="fas fa-trash"></i>
              </button>
            </div>
          </div>
        </div>

        <div class="relations-block">
          <div class="relations-header">
            <div class="fw-600">Связи документов</div>
            <div class="d-flex gap-2">
              <select v-model="relationForm.related_document_id" class="form-control form-control-sm" style="min-width: 260px;" :disabled="!documentForm.id">
                <option value="">Выберите документ</option>
                <option v-for="doc in documentOptions" :key="doc.id" :value="doc.id" :disabled="doc.id === documentForm.id">
                  {{ doc.title }}
                </option>
              </select>
              <button type="button" class="btn btn-sm btn-outline-primary" @click="$emit('add-relation')" :disabled="!documentForm.id">
                Добавить
              </button>
            </div>
          </div>
          <div v-if="!documentForm.id" class="text-muted small">
            Сначала сохраните документ, чтобы добавлять связи.
          </div>
          <div v-else-if="relations.length === 0" class="text-muted small">
            Связей пока нет.
          </div>
          <div v-else class="relations-list">
            <div v-for="relation in relations" :key="relation.id" class="relations-item">
              <div class="relations-name">{{ getDocumentTitle(relation.related_document_id) }}</div>
              <button type="button" class="btn btn-sm btn-icon text-danger" @click="$emit('remove-relation', relation)">
                <i class="fas fa-trash"></i>
              </button>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="$emit('close')">
            Отмена
          </button>
          <button type="submit" class="btn btn-primary" :disabled="saving">
            <i v-if="saving" class="fas fa-spinner fa-spin"></i>
            {{ isEditing ? 'Сохранить' : 'Создать' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PackageEditorModal',
  props: {
    show: { type: Boolean, default: false },
    isEditing: { type: Boolean, default: false },
    saving: { type: Boolean, default: false },
    packageForm: { type: Object, required: true },
    packageItems: { type: Array, required: true },
    selectedPackageDocumentId: { type: [String, Number], default: '' },
    documentForm: { type: Object, required: true },
    relations: { type: Array, required: true },
    relationForm: { type: Object, required: true },
    documentOptions: { type: Array, required: true },
    companies: { type: Array, required: true },
    deals: { type: Array, required: true },
    getDocumentTitle: { type: Function, required: true }
  },
  emits: [
    'close',
    'save',
    'update:selectedPackageDocumentId',
    'add-package-item',
    'remove-package-item',
    'add-relation',
    'remove-relation'
  ]
}
</script>

<style scoped>
.fw-600 { font-weight: 600; }

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.form-grid .span-2 {
  grid-column: span 2;
}

.relations-block {
  padding: 12px;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 12px;
  margin-bottom: 16px;
}

.relations-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.relations-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.relations-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  border-radius: 8px;
  background: var(--md-sys-color-surface-variant);
}

.relations-name {
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .modal-content {
    max-width: 100% !important;
  }
}
</style>
