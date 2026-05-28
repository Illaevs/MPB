<template>
  <div
    v-if="activeTab === 'contracts'"
    id="panel-contracts"
    class="project-overview-shell h-100 d-flex flex-column"
    role="tabpanel"
    aria-labelledby="tab-contracts"
  >
    <!--
      Используем тот же shell, что и Обзор, чтобы рамка/радиус/фон были
      единообразными.  Внутри одна .card-секция с тулбаром + таблицей —
      растягивается на всю высоту шелла.
    -->
    <div class="card p-4 flex-grow-1 d-flex flex-column overflow-hidden">
      <div class="d-flex justify-between align-center mb-3">
        <h3 class="card-title m-0">Договоры</h3>
        <button
          class="btn btn-sm btn-primary"
          @click="showContractLinker = !showContractLinker"
          :disabled="contractLinking"
          title="Привязать договор"
        >
          <i class="fas fa-plus mr-1"></i>
          <span>Привязать договор</span>
        </button>
      </div>

      <div v-if="showContractLinker" class="contracts-linker-popover mb-3">
        <div class="contracts-link-controls">
          <input
            v-model.trim="contractSearch"
            type="text"
            class="form-control form-control-sm"
            placeholder="Поиск договора"
            :disabled="!canLinkContract || contractLinking"
          >
          <div class="d-flex gap-2 align-center">
            <select
              v-model="selectedContractId"
              class="form-control form-control-sm"
              style="width: 280px;"
              :disabled="!canLinkContract || contractLinking"
            >
              <option value="">{{ contractSelectPlaceholder }}</option>
              <option v-for="c in filteredProjectLinkableContracts" :key="c.id" :value="c.id">
                {{ c.contract_number }} ({{ formatDate(c.contract_date) }})
              </option>
            </select>
            <button
              class="btn btn-sm btn-primary"
              @click="linkContractToProject"
              :disabled="!selectedContractId || !canLinkContract || contractLinking"
              :title="contractLinkDisabledReason || 'Привязать договор'"
            >
              <i v-if="contractLinking" class="fas fa-spinner fa-spin"></i>
              <i v-else class="fas fa-link"></i>
            </button>
          </div>
          <div v-if="contractLinkDisabledReason" class="small text-muted mt-1">
            {{ contractLinkDisabledReason }}
          </div>
        </div>
      </div>

      <!-- Тело: либо скелетон, либо empty, либо таблица — занимает остаток высоты со скроллом. -->
      <div class="flex-grow-1 overflow-auto">
        <div v-if="contractsLoading" class="my-3 d-flex flex-column gap-2">
          <SkeletonLoader height="40px" v-for="i in 3" :key="i" />
        </div>
        <div v-else-if="!contracts.length" class="text-center text-muted small py-5">
          Нет привязанных договоров
        </div>
        <div v-else class="table-container contracts-table-container">
          <table class="table">
            <thead>
              <tr>
                <th>Номер</th>
                <th>Дата</th>
                <th>Статус</th>
                <th class="text-right">Сумма</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="c in contractsDisplay"
                :key="c.id"
                :class="c.contract_type === 'general_contractor' ? 'bg-primary-container' : ''"
              >
                <td>
                  <div class="fw-500">{{ c.contract_number }}</div>
                  <small
                    v-if="c.contract_type === 'general_contractor'"
                    class="badge badge-sm badge-primary"
                  >Генподрядный</small>
                </td>
                <td>{{ formatDate(c.contract_date) }}</td>
                <td>
                  <span class="badge badge-sm" :class="getContractStatusClass(c.status)">
                    {{ getContractStatusText(c.status) }}
                  </span>
                </td>
                <td class="text-right">{{ formatCurrency(c.amount) }}</td>
                <td class="text-right">
                  <button
                    class="btn btn-sm btn-icon text-danger"
                    @click="unlinkContractFromProject(c)"
                    :disabled="contractUnlinkingId === c.id"
                    title="Отвязать"
                  >
                    <i v-if="contractUnlinkingId === c.id" class="fas fa-spinner fa-spin"></i>
                    <i v-else class="fas fa-unlink"></i>
                  </button>
                  <router-link class="btn btn-sm btn-icon" :to="`/contracts/${c.id}`" title="Открыть">
                    <i class="fas fa-eye"></i>
                  </router-link>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * Вкладка "Договоры" в ProjectDetail.
 *
 * Использует тот же shell `.project-overview-shell`, что и Обзор —
 * единая рамка с радиусом 12px вокруг всей вкладки. Внутренняя `.card`
 * без своих рамок (стили снимаются shell-селектором в ProjectDetail.vue).
 * Блок растягивается на всю доступную высоту: shell — `h-100.d-flex.flex-column`,
 * `.card` — `flex-grow-1`, таблица — со своим скроллом.
 */
import SkeletonLoader from '../../../components/ui/SkeletonLoader.vue'
export default {
  name: 'Contracts',
  components: { SkeletonLoader },
  props: { state: { type: Object, required: true } },
  setup(props) {
    return { ...props.state }
  }
}
</script>
