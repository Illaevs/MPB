<template>
  <div class="task-module-main rules-shell card flex-grow-1 overflow-hidden d-flex flex-column">
    <div class="rules-shell__header">
      <div class="rules-shell__headline">
        <h3 class="card-title m-0"><i class="fas fa-balance-scale mr-2"></i> Правила штрафов и бонусов</h3>
        <p>Настройка коэффициентов по оценке и срокам выполнения задач.</p>
      </div>
      <button class="task-toolbar-btn" @click="seedDefaultRules" :disabled="seedingRules">
        <i v-if="seedingRules" class="fas fa-spinner fa-spin mr-1"></i>
        <i v-else class="fas fa-magic mr-1"></i> Создать правила по умолчанию
      </button>
    </div>

    <div v-if="rulesLoading" class="d-flex justify-center align-center flex-grow-1">
      <i class="fas fa-spinner fa-spin fa-2x text-muted"></i>
    </div>

    <div v-else-if="!penaltyRules.length" class="d-flex flex-column align-center justify-center flex-grow-1 text-muted">
      <i class="fas fa-balance-scale fa-3x mb-3 text-light-gray"></i>
      <p>Нет правил штрафов</p>
      <button class="btn btn-primary mt-2" @click="seedDefaultRules">Создать правила по умолчанию</button>
    </div>

    <div v-else class="flex-grow-1 overflow-auto p-3 rules-shell__body">
      <div class="rules-grid">
        <div class="rules-block">
          <div class="rules-block__header">
            <h5 class="mb-0"><i class="fas fa-star text-warning mr-1"></i> Правила по оценке</h5>
            <span>{{ ratingRules.length }} записей</span>
          </div>
          <table class="table table-sm rules-table mb-0">
            <thead>
              <tr>
                <th>Условие</th>
                <th>Коэффициент</th>
                <th>Описание</th>
                <th>Активно</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rule in ratingRules" :key="rule.id">
                <td>Оценка = {{ rule.condition_min }}</td>
                <td><span :class="rule.coefficient >= 1 ? 'text-success' : 'text-danger'">× {{ rule.coefficient }}</span></td>
                <td class="text-muted small">{{ rule.description }}</td>
                <td><span :class="rule.is_active ? 'badge-success' : 'badge-dark'" class="badge">{{ rule.is_active ? 'Да' : 'Нет' }}</span></td>
                <td><button class="btn btn-sm btn-icon" @click="editRule(rule)"><i class="fas fa-edit"></i></button></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="rules-block">
          <div class="rules-block__header">
            <h5 class="mb-0"><i class="fas fa-clock text-info mr-1"></i> Правила по срокам</h5>
            <span>{{ deadlineRules.length }} записей</span>
          </div>
          <table class="table table-sm rules-table mb-0">
            <thead>
              <tr>
                <th>Условие</th>
                <th>Коэффициент</th>
                <th>Описание</th>
                <th>Активно</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rule in deadlineRules" :key="rule.id">
                <td>{{ rule.condition_min }}% - {{ rule.condition_max }}%</td>
                <td><span :class="rule.coefficient >= 1 ? 'text-success' : 'text-danger'">× {{ rule.coefficient }}</span></td>
                <td class="text-muted small">{{ rule.description }}</td>
                <td><span :class="rule.is_active ? 'badge-success' : 'badge-dark'" class="badge">{{ rule.is_active ? 'Да' : 'Нет' }}</span></td>
                <td><button class="btn btn-sm btn-icon" @click="editRule(rule)"><i class="fas fa-edit"></i></button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TaskPenalties',
  props: { state: { type: Object, required: true } },
  setup(props) {
    return { ...props.state }
  }
}
</script>
