<template>
  <div v-if="show" class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" style="max-width: 520px;" @click.stop>
      <div class="modal-header">
        <h3 class="m-0">{{ editingExpense ? 'Редактировать расход' : 'Новый расход' }}</h3>
        <button class="btn btn-sm btn-secondary" @click="$emit('close')">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <form class="modal-body" @submit.prevent="$emit('save')">
        <div class="form-group">
          <label>Категория затрат</label>
          <CategorySmartSelect
            :model-value="form.category_code"
            :options="expenseCategories"
            placeholder="Категория затрат"
            @update:model-value="updateField('category_code', $event)"
          />
        </div>
        <div class="form-group">
          <label>Сумма</label>
          <input
            :value="form.amount"
            type="number"
            min="0"
            step="0.01"
            class="form-control"
            required
            @input="updateField('amount', $event.target.value)"
          />
        </div>
        <div class="form-group">
          <label>Плановая дата</label>
          <input
            :value="form.plan_date"
            type="date"
            class="form-control"
            required
            @input="updateField('plan_date', $event.target.value)"
          />
        </div>
        <div class="form-group">
          <label>Фактическая дата</label>
          <input
            :value="form.actual_date"
            type="date"
            class="form-control"
            @input="updateField('actual_date', $event.target.value)"
          />
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="$emit('close')">Отмена</button>
          <button type="submit" class="btn btn-primary">Сохранить</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import CategorySmartSelect from '@/components/ui/CategorySmartSelect.vue'

export default {
  name: 'ExpenseModal',
  components: { CategorySmartSelect },
  props: {
    show: Boolean,
    form: { type: Object, required: true },
    editingExpense: { type: Object, default: null },
    expenseCategories: { type: Array, required: true },
  },
  emits: ['close', 'save', 'update-field'],
  methods: {
    updateField(key, value) {
      this.$emit('update-field', { key, value })
    }
  }
}
</script>

<style scoped>
:deep(.modal-content) {
  border-radius: 18px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 28px 50px rgba(15, 23, 42, 0.16);
}
:deep(.modal-header),
:deep(.modal-footer) {
  border-color: rgba(15, 23, 42, 0.08);
}
:deep(.form-control) {
  min-height: 36px;
  border-radius: 10px;
  border-color: rgba(15, 23, 42, 0.12);
  background: #fff;
  box-shadow: none;
}
</style>
