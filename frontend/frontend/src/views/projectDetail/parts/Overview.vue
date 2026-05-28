<template>
          <div
             v-if="activeTab === 'overview'"
             id="panel-overview"
             class="overview-layout h-100"
             role="tabpanel"
             aria-labelledby="tab-overview"
          >
             <div class="overview-kpis d-grid grid-cols-3 gap-3">
                <div class="glass-card kpi-card">
                   <div class="kpi-card-head">
                      <span class="kpi-card-label">Контракт</span>
                      <i class="fas fa-file-signature text-primary"></i>
                   </div>
                   <div class="kpi-card-value text-primary">{{ formatCurrency(contractAmount) }}</div>
                   <div class="kpi-progress">
                      <div class="kpi-progress-fill kpi-progress-fill--primary" :style="{ width: `${paymentProgressPercent}%` }"></div>
                   </div>
                   <div class="small text-muted mt-1">Оплачено {{ paymentProgressPercent.toFixed(1) }}%</div>
                </div>

                <div class="glass-card kpi-card">
                   <div class="kpi-card-head">
                      <span class="kpi-card-label">Оплачено</span>
                      <i class="fas fa-check-circle text-success"></i>
                   </div>
                   <div class="kpi-card-value text-success">{{ formatCurrency(paidAmount) }}</div>
                   <div class="small text-muted mt-1">Факт платежей</div>
                </div>

                <div class="glass-card kpi-card">
                   <div class="kpi-card-head">
                      <span class="kpi-card-label">Остаток</span>
                      <i class="fas fa-hourglass-half" :class="remainingTextClass"></i>
                   </div>
                   <div class="kpi-card-value" :class="remainingTextClass">{{ formatCurrency(remainingAmount) }}</div>
                   <div class="small text-muted mt-1">Неоплачено {{ remainingPercent.toFixed(1) }}%</div>
                </div>
             </div>

             <div class="overview-main d-grid gap-3">
                <div class="glass-card p-4">
                   <h3 class="card-title mb-3">Основная информация</h3>
                   <div class="info-grid">
                      <div class="info-row">
                         <span class="text-muted">Объект</span>
                         <span class="fw-500 text-right">{{ project.obj_name || '-' }}</span>
                      </div>
                      <div class="info-row">
                         <span class="text-muted">Адрес</span>
                         <span class="fw-500 text-right">{{ project.address || '-' }}</span>
                      </div>
                      <div class="info-row">
                         <span class="text-muted">Тип объекта</span>
                         <span class="fw-500 text-right">{{ project.object_type || '-' }}</span>
                      </div>
                      <div class="info-row">
                         <span class="text-muted">Площадь</span>
                         <span class="fw-500 text-right">{{ project.object_area ? project.object_area + ' м²' : '-' }}</span>
                      </div>
                      <div class="info-row">
                         <span class="text-muted">Заказчик</span>
                         <span class="fw-500 text-right">{{ getCompanyName(project.customer?.name, project.customer_id) }}</span>
                      </div>
                      <div class="info-row">
                         <span class="text-muted">Наша компания</span>
                         <span class="fw-500 text-right">{{ getCompanyName(project.our_company?.name, project.our_company_id) }}</span>
                      </div>
                      <div class="separator my-2"></div>
                      <div class="info-row">
                         <span class="text-muted">ГИП</span>
                         <span class="fw-500 text-right">{{ gipNames || '-' }}</span>
                      </div>
                      <div class="mt-2">
                         <div class="d-flex justify-between align-center mb-2">
                            <label class="text-muted small m-0">Привязанные ГИПы</label>
                            <button class="btn btn-sm btn-outline-primary" @click="openGipDialog" :disabled="gipSaving">
                               Добавить
                            </button>
                         </div>
                         <div v-if="!gipUsers.length" class="text-muted small">Нет привязанных ГИПов</div>
                         <div v-else class="d-flex flex-column gap-1">
                            <div v-for="user in gipUsers" :key="user.id" class="d-flex justify-between align-center bg-light rounded px-2 py-1">
                               <span class="small">{{ user.full_name || user.email }}</span>
                               <button class="btn btn-sm btn-icon text-danger" @click="removeGip(user.id)">
                                  <i class="fas fa-times"></i>
                               </button>
                            </div>
                         </div>
                         <div v-if="gipDirty" class="small text-warning mb-2">
                            Есть несохраненные изменения
                         </div>
                         <div class="mt-2 d-flex gap-2">
                            <button class="btn btn-sm btn-outline-primary" :disabled="gipSaving || !gipDirty" @click="saveDealGips">
                               <i v-if="gipSaving" class="fas fa-spinner fa-spin"></i>
                               <span v-else>Сохранить</span>
                            </button>
                            <button class="btn btn-sm btn-secondary" :disabled="gipSaving || !gipDirty" @click="resetDealGips">
                               Отменить
                            </button>
                         </div>
                      </div>
                      <div class="separator my-2"></div>
                      <div class="info-row">
                         <span class="text-muted">Ставка НДС</span>
                         <span class="fw-500 text-right">{{ project.vat_rate ?? 0 }}%</span>
                      </div>
                      <div class="mt-2">
                         <label class="text-muted small">Изменить ставку НДС</label>
                         <div class="d-flex gap-2 align-center">
                            <select v-model.number="vatRate" class="form-control form-control-sm" style="max-width: 120px;">
                               <option v-for="rate in vatRateOptions" :key="`project-vat-${rate}`" :value="rate">{{ rate }}%</option>
                            </select>
                            <button class="btn btn-sm btn-outline-primary" :disabled="!vatRateDirty || vatSaving" @click="saveVatRate">
                               <i v-if="vatSaving" class="fas fa-spinner fa-spin"></i>
                               <span v-else>Сохранить</span>
                            </button>
                         </div>
                         <div v-if="vatRateDirty" class="small text-warning mt-1">
                            Предпросмотр сметы с НДС {{ previewVatRate }}%
                         </div>
                      </div>
                   </div>
                </div>

                <div class="glass-card p-4">
                   <div class="d-flex justify-between align-center mb-3">
                      <h3 class="card-title m-0">Договоры</h3>
                      <button
                         class="btn btn-sm btn-primary"
                         @click="showContractLinker = !showContractLinker"
                         :disabled="contractLinking"
                         title="Привязать договор"
                      >
                         <i class="fas fa-plus"></i>
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
                               style="width: 220px;"
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
                   

                   <div v-if="contractsLoading" class="my-3 d-flex flex-column gap-2">
                      <SkeletonLoader height="40px" v-for="i in 3" :key="i" />
                   </div>
                   <div v-else-if="!contracts.length" class="text-center text-muted small py-4">Нет привязанных договоров</div>
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
                            <tr v-for="c in contractsDisplay" :key="c.id" :class="c.contract_type === 'general_contractor' ? 'bg-primary-container' : ''">
                               <td>
                                  <div class="fw-500">{{ c.contract_number }}</div>
                                  <small v-if="c.contract_type === 'general_contractor'" class="badge badge-sm badge-primary">Генподрядный</small>
                               </td>
                               <td>{{ formatDate(c.contract_date) }}</td>
                               <td><span class="badge badge-sm" :class="getContractStatusClass(c.status)">{{ getContractStatusText(c.status) }}</span></td>
                               <td class="text-right">{{ formatCurrency(c.amount) }}</td>
                               <td class="text-right">
                                  <button
                                     class="btn btn-sm btn-icon text-danger"
                                     @click="unlinkContractFromProject(c)"
                                     :disabled="contractUnlinkingId === c.id"
                                  >
                                     <i v-if="contractUnlinkingId === c.id" class="fas fa-spinner fa-spin"></i>
                                     <i v-else class="fas fa-unlink"></i>
                                  </button>
                                  <router-link class="btn btn-sm btn-icon" :to="`/contracts/${c.id}`">
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
import SkeletonLoader from '../../../components/ui/SkeletonLoader.vue'
export default {
  name: 'Overview',
  components: { SkeletonLoader },
  props: { state: { type: Object, required: true } },
  setup(props) {
    return { ...props.state }
  }
}
</script>
