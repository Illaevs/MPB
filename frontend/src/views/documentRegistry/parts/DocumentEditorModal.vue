<template>
  <div v-if="show" class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop style="max-width: 900px;">
      <div class="modal-header">
        <h3 class="m-0">{{ isEditing ? 'Редактирование документа' : 'Новый документ' }}</h3>
        <button class="btn btn-sm btn-secondary" @click="$emit('close')">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <form @submit.prevent="$emit('save')" class="modal-body">
        <div class="form-grid">
          <div class="form-group">
            <label class="small text-muted mb-1">Тип документа *</label>
            <select v-model="documentForm.doc_type" class="form-control" required>
              <option value="outgoing_letter">Исходящее письмо</option>
              <option value="contract">Договор</option>
              <option value="addendum">Доп. соглашение</option>
              <option value="act">Акт</option>
              <option value="waybill">Накладная</option>
              <option value="result">Результат работ</option>
              <option value="other">Прочее</option>
            </select>
          </div>
          <div class="form-group">
            <label class="small text-muted mb-1">Статус</label>
            <select v-model="documentForm.status" class="form-control">
              <option value="draft">Проект</option>
              <option value="sent">Направлен</option>
              <option value="received">Получен</option>
              <option value="archived">Архив</option>
            </select>
          </div>
          <div class="form-group span-2">
            <label class="small text-muted mb-1">Название *</label>
            <input v-model="documentForm.title" type="text" class="form-control" required>
          </div>
          <div class="form-group">
            <label class="small text-muted mb-1">Номер</label>
            <input v-model="documentForm.number" type="text" class="form-control">
          </div>
          <div class="form-group">
            <label class="small text-muted mb-1">Дата</label>
            <input v-model="documentForm.document_date" type="date" class="form-control" :required="!isEditing">
          </div>
          <div class="form-group">
            <label class="small text-muted mb-1">Проект</label>
            <select v-model="documentForm.project_id" class="form-control">
              <option value="">Не выбран</option>
              <option v-for="deal in deals" :key="deal.id" :value="deal.id">
                {{ deal.title }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label class="small text-muted mb-1">Контрагент</label>
            <CompanySmartSelect
              v-model="documentForm.counterparty_id"
              :options="companies"
              placeholder="Найти контрагента"
            />
          </div>
          <div class="form-group">
            <label class="small text-muted mb-1">Наша компания</label>
            <select v-model="documentForm.our_company_id" class="form-control">
              <option value="">Не выбрано</option>
              <option v-for="company in ourCompanies" :key="company.id" :value="company.id">
                {{ company.name }}
              </option>
            </select>
          </div>
        </div>

        <div class="dispatch-block">
          <div class="dispatch-title">Отправка</div>
          <div class="dispatch-row" v-for="channel in channelKeys" :key="channel">
            <label class="dispatch-label">
              <input type="checkbox" v-model="channels[channel].enabled">
              {{ channelLabels[channel] }}
            </label>
            <input v-model="channels[channel].date" type="date" class="form-control form-control-sm" :disabled="!channels[channel].enabled">
            <input v-if="channel === 'post'" v-model="channels[channel].track" type="text" class="form-control form-control-sm" placeholder="Трек" :disabled="!channels[channel].enabled">
            <input
              type="file"
              multiple
              class="form-control form-control-sm"
              :disabled="!channels[channel].enabled"
              @change="$emit('handle-channel-files-change', channel, $event)"
            >
            <div v-if="channels[channel]?.files?.length" class="dispatch-pending">
              <div v-for="(file, idx) in channels[channel].files" :key="file.name + idx" class="dispatch-pending-file">
                <span>{{ file.name }}</span>
                <button type="button" class="btn btn-sm btn-icon" @click="$emit('remove-channel-file', channel, idx)">
                  <i class="fas fa-times"></i>
                </button>
              </div>
            </div>
          </div>
          <template v-for="channel in channelKeys" :key="`${channel}-files`">
            <div v-if="channels[channel]?.uploaded?.length" class="dispatch-files">
              <div class="dispatch-files-title">{{ channelLabels[channel] }}: подтверждения</div>
              <div class="dispatch-files-list">
                <div v-for="file in channels[channel].uploaded" :key="file.path" class="dispatch-file">
                  <span class="dispatch-file-name">{{ file.name }}</span>
                  <div class="dispatch-file-actions">
                    <button type="button" class="btn btn-sm btn-icon" @click="$emit('download-channel-file', channel, file)">
                      <i class="fas fa-download"></i>
                    </button>
                    <button type="button" class="btn btn-sm btn-icon text-danger" @click="$emit('delete-uploaded-channel-file', channel, file)">
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </template>
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
import CompanySmartSelect from '../../../components/ui/CompanySmartSelect.vue'

export default {
  name: 'DocumentEditorModal',
  components: { CompanySmartSelect },
  props: {
    show: { type: Boolean, default: false },
    isEditing: { type: Boolean, default: false },
    saving: { type: Boolean, default: false },
    documentForm: { type: Object, required: true },
    channels: { type: Object, required: true },
    channelKeys: { type: Array, required: true },
    channelLabels: { type: Object, required: true },
    relations: { type: Array, required: true },
    relationForm: { type: Object, required: true },
    documentOptions: { type: Array, required: true },
    companies: { type: Array, required: true },
    ourCompanies: { type: Array, required: true },
    deals: { type: Array, required: true },
    getDocumentTitle: { type: Function, required: true }
  },
  emits: [
    'close',
    'save',
    'handle-channel-files-change',
    'remove-channel-file',
    'download-channel-file',
    'delete-uploaded-channel-file',
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

.dispatch-block {
  padding: 12px;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 12px;
  margin-bottom: 16px;
}

.dispatch-title {
  font-weight: 600;
  margin-bottom: 8px;
}

.dispatch-row {
  display: grid;
  grid-template-columns: 160px 160px 140px 1fr;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.dispatch-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
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

.dispatch-files {
  margin-bottom: 8px;
  padding-left: 12px;
}

.dispatch-files-title {
  font-size: 0.85rem;
  color: var(--md-sys-color-on-surface-variant);
  margin-bottom: 4px;
}

.dispatch-files-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dispatch-file {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--md-sys-color-surface-variant);
  border-radius: 8px;
  padding: 4px 8px;
}

.dispatch-file-actions {
  display: inline-flex;
  gap: 6px;
}

.dispatch-file-name {
  font-size: 0.85rem;
}

.dispatch-pending {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-left: 2px;
}

.dispatch-pending-file {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--md-sys-color-surface-variant);
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 0.85rem;
}

@media (max-width: 768px) {
  .modal-content {
    max-width: 100% !important;
  }
}
</style>
