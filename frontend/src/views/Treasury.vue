<template>
  <div class="treasury-view h-100 d-flex flex-column p-2">
    <div class="trz-card">
    <!-- Header (title + stats chips inline + actions) -->
    <div class="d-flex justify-between align-center mb-2">
       <div class="trz-head-left">
          <h2 class="m-0" style="font-weight: 600; font-size: 1.5rem;">Казначейство</h2>
          <div class="d-flex gap-2 trz-stats">
             <div class="badge badge-lg badge-outline-primary">Всего: {{ stats.total }}</div>
             <div class="badge badge-lg badge-success-subtle">Распределено: {{ stats.ok }}</div>
             <div class="badge badge-lg badge-danger-subtle">Не распределено: {{ stats.alert }}</div>
             <div class="badge badge-lg badge-warning-subtle">Не учитывать: {{ stats.ignored }}</div>
          </div>
       </div>
       <div class="d-flex gap-2">
         <button class="btn btn-sm btn-outline-secondary" @click="openRulesModal">
            <i class="fas fa-magic mr-2"></i> Правила
         </button>
         <button class="btn btn-sm btn-success" @click="openFilePicker">
            <i class="fas fa-file-csv mr-2"></i> Импорт
         </button>
         <button class="btn btn-sm btn-primary" @click="openCreateModal">
            <i class="fas fa-plus mr-2"></i> Создать
         </button>
       </div>
       <input ref="fileInput" type="file" accept=".csv" @change="handleFileSelect" style="display: none">
    </div>

    <!-- Loading Skeleton for Table -->
    <div v-if="loading" class="card p-3 d-flex flex-column gap-2 mb-3">
       <SkeletonLoader height="40px" v-for="i in 5" :key="i" />
    </div>

    <!-- Filters -->
    <div class="card p-2 mb-3 flex-shrink-0">
       <div class="d-grid gap-2 trz-filters-grid" style="grid-template-columns: minmax(220px, 2fr) minmax(150px, 1.1fr) minmax(150px, 1.1fr) auto auto auto 90px;">
          <div class="form-group mb-0">
             <input v-model="filters.search" class="form-control form-control-sm" placeholder="Поиск (№, назначение, ИНН)..." @input="debouncedSearch">
          </div>
          <div class="form-group mb-0">
             <input v-model="filters.payer" class="form-control form-control-sm" placeholder="Плательщик">
          </div>
          <div class="form-group mb-0">
             <input v-model="filters.payee" class="form-control form-control-sm" placeholder="Получатель">
          </div>
          <div class="form-group mb-0">
             <UiChipFilter
                v-model="filters.type"
                :options="TREASURY_TYPE_OPTIONS"
                placeholder="Все типы"
                empty-icon="fas fa-exchange-alt"
                @update:model-value="onTypeChange"
             />
          </div>
          <div class="form-group mb-0">
             <UiChipFilter
                v-model="filters.status"
                :options="TREASURY_STATUS_OPTIONS"
                placeholder="Все статусы"
                empty-icon="fas fa-circle-half-stroke"
                @update:model-value="loadTransactions"
             />
          </div>
          <div class="form-group mb-0">
             <UiChipFilter
                v-model="filters.calcType"
                :options="TREASURY_CALC_TYPE_OPTIONS"
                placeholder="Расчёт"
                empty-icon="fas fa-calculator"
                @update:model-value="loadTransactions"
             />
          </div>
          <div class="d-flex align-end">
             <button class="btn btn-sm btn-outline-secondary w-100" @click="loadTransactions">Найти</button>
          </div>
       </div>
    </div>

    <!-- Bulk actions → floating bottom mini-modal (see after .trz-card) -->

    <!-- Import Preview -->
    <div v-if="selectedFile" class="card mb-4 p-4 bg-light border-primary">
       <div class="d-flex justify-between align-center mb-2">
          <h4 class="m-0 text-primary">Импорт: {{ selectedFile.name }} ({{ formatFileSize(selectedFile.size) }})</h4>
          <button class="btn btn-sm btn-text text-muted" @click="openFilePicker">Изменить</button>
       </div>
       <div class="d-flex gap-3 align-end">
          <div class="form-group flex-grow-1" style="max-width: 200px;">
             <label class="small text-muted">Тип расчета по умолчанию</label>
             <select v-model="defaultCalcType" class="form-select form-select-sm">
                <option value="vtb">ВТБ</option>
                <option value="material">Матер.</option>
                <option value="other">Иной</option>
             </select>
          </div>
          <button class="btn btn-primary btn-sm" @click="previewImport" :disabled="importing">
             <i v-if="importing" class="fas fa-spinner fa-spin mr-1"></i> Проверить
          </button>
       </div>
    </div>

    <!-- Import Result -->
    <div v-if="importResult" class="card mb-4 p-4">
        <h4 class="mb-2">Результат импорта</h4>
        <div class="d-flex gap-4 mb-2">
           <div>Импортировано: <strong class="text-success">{{ importResult.imported_count }}</strong></div>
           <div>Пропущено: <strong class="text-warning">{{ importResult.skipped_count }}</strong></div>
           <div>Ошибки: <strong class="text-danger">{{ importResult.errors?.length || 0 }}</strong></div>
        </div>
        <div v-if="importResult.parse_errors?.length" class="alert alert-danger p-2 small m-0">
           <ul class="m-0 pl-3">
              <li v-for="error in importResult.parse_errors" :key="error">{{ error }}</li>
           </ul>
        </div>
    </div>

    <!-- Table -->
    <div class="card flex-grow-1 overflow-hidden d-flex flex-column">
       <div class="flex-grow-1 overflow-auto p-0">
          <table class="table table-hover m-0 sticky-header treasury-table">
             <thead>
                <tr>
                   <th style="width: 30px;"><input type="checkbox" :checked="allSelected" @change="toggleSelectAll" title="Выбрать все"></th>
                   <th style="width: 50px;">ID</th>
                   <th style="width: 90px;">Дата</th>
                   <th>Плательщик / Получатель</th>
                   <th style="width: 25%;">Назначение</th>
                   <th class="text-right" style="width: 120px;">Сумма</th>
                   <th style="width: 160px;">Распределение</th>
                   <th style="width: 100px;">Расчет</th>
                   <th style="width: 200px;">Категория</th>
                   <th style="width: 120px;">Статус</th>
                   <th style="width: 80px;"></th>
                </tr>
             </thead>
             <tbody>
                <tr v-for="tx in transactions" :key="tx.id" :class="rowClass(tx)">
                   <td><input type="checkbox" :checked="selectedIds.includes(tx.id)" @change="toggleSelect(tx.id)"></td>
                   <td class="text-center small text-muted">
                     {{ shortId(tx.id) }}
                     <i v-if="tx.auto_filled || tx.auto_rule_id" class="fas fa-bolt text-warning ml-1" title="Заполнено автоматически"></i>
                   </td>
                   <td class="small line-height-1">
                      <div>{{ formatDate(tx.transaction_date) }}</div>
                      <div class="text-muted">№ {{ tx.doc_num || '-' }}</div>
                   </td>
                   <td>
                      <div class="d-flex flex-column small">
                         <div v-if="tx.payer_name" class="fw-500">{{ tx.payer_name }} <span class="text-muted text-xs">{{ tx.payer_inn }}</span></div>
                         <div v-if="tx.payee_name" class="fw-500">-> {{ tx.payee_name }} <span class="text-muted text-xs">{{ tx.payee_inn }}</span></div>
                      </div>
                   </td>
                   <td>
                      <div class="text-truncate-2 small" :title="tx.purpose">{{ tx.purpose }}</div>
                   </td>
                   <td class="text-right fw-600 font-mono" :class="amountClass(tx)">{{ signedAmount(tx.amount) }}</td>
                   <td class="small">
                      <div>Расп: {{ formatCurrency(tx.allocated_amount || 0) }}</div>
                      <div class="text-muted">Ост: {{ formatCurrency(tx.remainder != null ? tx.remainder : Math.abs(tx.amount)) }}</div>
                      <div v-if="tx.linked_transaction_id" class="linked-indicator" title="Привязан как возврат/зачёт">
                        <i class="fas fa-link"></i> Привязан
                      </div>
                      <div v-if="tx.linked_payments && tx.linked_payments.length" class="linked-badge" :title="tx.linked_payments.length + ' возврат(ов) привязано'">
                        <i class="fas fa-link"></i> {{ tx.linked_payments.length }} возвр.
                      </div>
                   </td>
                   <td>
                      <select class="form-select form-select-xs bg-transparent border-0" :value="tx.calc_type" @change="updateField(tx.id, { calc_type: $event.target.value })">
                         <option value="vtb">ВТБ</option>
                         <option value="material">Матер.</option>
                         <option value="other">Иной</option>
                      </select>
                   </td>
                   <td>
                      <CategorySmartSelect
                         :model-value="tx.category_code || ''"
                         :options="rowCategories(tx)"
                         placeholder="-"
                         size="xs"
                         input-class="form-select-xs bg-transparent border-0"
                         @change="value => updateField(tx.id, { category_code: value || null })"
                      />
                   </td>
                   <td>
                      <div class="d-flex align-center justify-between">
                         <div class="form-check form-switch m-0" title="Не учитывать">
                            <input class="form-check-input" type="checkbox" :checked="isIgnored(tx)" @change="updateField(tx.id, { ignore_flag: $event.target.checked ? 'Да' : 'Нет' })">
                         </div>
                         <span v-if="isIgnored(tx)" class="badge badge-sm badge-warning-subtle">Не учит.</span>
                         <span v-else-if="isFullyAllocated(tx)" class="badge badge-sm badge-success-subtle">Распред.</span>
                         <span v-else class="badge badge-sm badge-danger-subtle">Ждёт</span>
                      </div>
                   </td>
                   <td class="text-right">
                      <button class="btn btn-sm btn-icon" title="Распределить" @click="openAllocate(tx)">
                         <i class="fas fa-sliders-h"></i>
                      </button>
                      <button class="btn btn-sm btn-icon text-danger ml-1" title="Удалить" @click="deleteTransaction(tx)">
                         <i class="fas fa-trash"></i>
                      </button>
                   </td>
                </tr>
             </tbody>
          </table>
       </div>
       <!-- Pagination -->
       <div class="d-flex justify-between align-center p-2 border-top">
          <div class="small text-muted">
             Показано {{ Math.min((currentPage - 1) * pageSize + 1, totalCount) }}-{{ Math.min(currentPage * pageSize, totalCount) }} из {{ totalCount }}
          </div>
          <div class="d-flex gap-1 align-center">
             <button class="btn btn-sm btn-outline-secondary" :disabled="currentPage <= 1" @click="goToPage(1)">
                <i class="fas fa-angle-double-left"></i>
             </button>
             <button class="btn btn-sm btn-outline-secondary" :disabled="currentPage <= 1" @click="goToPage(currentPage - 1)">
                <i class="fas fa-angle-left"></i>
             </button>
             <span class="px-2">Стр. {{ currentPage }} из {{ totalPages }}</span>
             <button class="btn btn-sm btn-outline-secondary" :disabled="currentPage >= totalPages" @click="goToPage(currentPage + 1)">
                <i class="fas fa-angle-right"></i>
             </button>
             <button class="btn btn-sm btn-outline-secondary" :disabled="currentPage >= totalPages" @click="goToPage(totalPages)">
                <i class="fas fa-angle-double-right"></i>
             </button>
          </div>
       </div>
    </div>
    </div>

    <!-- Floating bulk-action bar (bottom mini-modal, like Tasks) -->
    <transition name="bulk-bar">
      <div v-if="selectedIds.length" class="bulk-bar">
        <div class="bulk-bar__info">
          <i class="fas fa-check-square"></i>
          <span>Выбрано: <b>{{ selectedIds.length }}</b></span>
        </div>
        <div class="bulk-bar__actions">
          <select v-model="bulkAction" class="form-control form-control-sm">
            <option value="">Действие...</option>
            <option value="category">Установить категорию</option>
            <option value="calc_type">Установить расчёт</option>
            <option value="create_dds">Создать ДДС</option>
            <option value="ignore">Пометить "не учитывать"</option>
          </select>
          <CategorySmartSelect
            v-if="bulkAction === 'category'"
            v-model="bulkCategory"
            :options="allCategoryOptions"
            placeholder="Выберите категорию..."
            size="sm"
            input-class="form-select-sm"
            style="width: 260px;"
          />
          <select v-if="bulkAction === 'calc_type'" v-model="bulkCalcType" class="form-control form-control-sm" style="min-width: 140px;">
            <option value="">Расчёт...</option>
            <option value="vtb">ВТБ</option>
            <option value="material">Матер.</option>
            <option value="other">Иной</option>
          </select>
          <button class="btn btn-sm bulk-bar__apply" @click="applyBulkAction" :disabled="!bulkAction || bulkLoading">
            <i v-if="bulkLoading" class="fas fa-spinner fa-spin mr-1"></i> Применить
          </button>
          <button class="btn btn-sm btn-outline-secondary" @click="clearSelection">Снять выбор</button>
        </div>
      </div>
    </transition>

    <!-- Confirm Import Modal -->
    <div v-if="showImportConfirmModal" class="modal-overlay" v-modal-close="closeImportModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
           <h4>Подтверждение импорта</h4>
           <button class="btn-close" @click="closeImportModal"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
           <div class="row mb-3">
              <div class="col-4"><strong>Строк:</strong> {{ importPreview?.total_rows || 0 }}</div>
              <div class="col-4"><strong>Дубликаты:</strong> {{ importPreview?.duplicate_count || 0 }}</div>
              <div class="col-4"><strong>Новые:</strong> {{ importPreview?.missing_companies?.length || 0 }}</div>
           </div>
           
           <div v-if="importPreview?.parse_errors?.length" class="alert alert-danger p-2 small">
              <strong>Ошибки:</strong>
              <ul class="m-0 pl-3">
                 <li v-for="err in importPreview.parse_errors" :key="err">{{ err }}</li>
              </ul>
           </div>
           
           <div class="form-check mb-3">
               <input class="form-check-input" type="checkbox" id="createMissing" v-model="createMissingCompanies">
               <label class="form-check-label" for="createMissing">Создавать недостающих контрагентов</label>
           </div>
           
           <div v-if="importPreview?.rows?.length" class="overflow-auto border rounded" style="max-height: 300px;">
              <table class="table table-sm table-stripe m-0">
                 <thead><tr><th>#</th><th>Док</th><th>Дата</th><th>Сумма</th><th>Статус</th></tr></thead>
                 <tbody>
                    <tr v-for="row in importPreview.rows.slice(0, 50)" :key="row.index">
                       <td>{{ row.index }}</td><td>{{ row.doc_num }}</td><td>{{ formatDate(row.transaction_date) }}</td>
                       <td>{{ formatCurrency(row.amount) }}</td>
                       <td>
                          <span v-if="row.is_duplicate" class="badge badge-sm badge-warning">Дубль</span>
                          <span v-else class="badge badge-sm badge-success">Новый</span>
                       </td>
                    </tr>
                 </tbody>
              </table>
           </div>
        </div>
        <div class="modal-footer">
           <button class="btn btn-secondary" @click="closeImportModal">Отмена</button>
           <button class="btn btn-primary" @click="confirmImport" :disabled="importing">
              <i v-if="importing" class="fas fa-spinner fa-spin mr-1"></i> Импортировать
           </button>
        </div>
      </div>
    </div>

    <!-- Create Transaction Modal -->
    <div v-if="showCreateModal" class="modal-overlay" v-modal-close="closeCreateModal">
      <div class="modal-content" @click.stop style="max-width: 600px;">
        <div class="modal-header">
          <h4>Создать транзакцию</h4>
          <button class="btn-close" @click="closeCreateModal"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="row">
            <div class="col-6">
              <div class="form-group">
                <label class="form-label">Номер документа *</label>
                <input v-model="createForm.doc_num" class="form-control form-control-sm" placeholder="№ документа">
              </div>
            </div>
            <div class="col-6">
              <div class="form-group">
                <label class="form-label">Дата *</label>
                <input v-model="createForm.transaction_date" type="date" class="form-control form-control-sm">
              </div>
            </div>
          </div>
          <div class="row">
            <div class="col-6">
              <div class="form-group">
                <label class="form-label">Сумма *</label>
                <input v-model.number="createForm.amount" type="number" step="0.01" class="form-control form-control-sm" placeholder="Расход: отрицательное, Приход: положительное">
              </div>
            </div>
            <div class="col-6">
              <div class="form-group">
                <label class="form-label">Тип расчета</label>
                <select v-model="createForm.calc_type" class="form-select form-select-sm">
                  <option value="vtb">ВТБ</option>
                  <option value="material">Матер.</option>
                  <option value="other">Иной</option>
                </select>
              </div>
            </div>
          </div>
          <div class="row">
            <div class="col-6">
              <div class="form-group">
                <label class="form-label">Плательщик</label>
                <input v-model="createForm.payer_name" class="form-control form-control-sm" placeholder="Название">
              </div>
            </div>
            <div class="col-6">
              <div class="form-group">
                <label class="form-label">ИНН плательщика</label>
                <input v-model="createForm.payer_inn" class="form-control form-control-sm" placeholder="ИНН">
              </div>
            </div>
          </div>
          <div class="row">
            <div class="col-6">
              <div class="form-group">
                <label class="form-label">Получатель</label>
                <input v-model="createForm.payee_name" class="form-control form-control-sm" placeholder="Название">
              </div>
            </div>
            <div class="col-6">
              <div class="form-group">
                <label class="form-label">ИНН получателя</label>
                <input v-model="createForm.payee_inn" class="form-control form-control-sm" placeholder="ИНН">
              </div>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Назначение платежа</label>
            <textarea v-model="createForm.purpose" class="form-control form-control-sm" rows="2" placeholder="Назначение"></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">Категория</label>
            <CategorySmartSelect
              v-model="createForm.category_code"
              :options="createFormCategories"
              placeholder="Категория"
              size="sm"
              input-class="form-select-sm"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeCreateModal">Отмена</button>
          <button class="btn btn-primary" @click="submitCreateForm" :disabled="creatingTx">
            <i v-if="creatingTx" class="fas fa-spinner fa-spin mr-1"></i> Создать
          </button>
        </div>
      </div>
    </div>

    <!-- Rules Management Modal -->
    <div v-if="showRulesModal" class="modal-overlay" v-modal-close="closeRulesModal">
      <div class="modal-content" @click.stop style="max-width: 900px;">
        <div class="modal-header">
          <h4>Правила автораспределения</h4>
          <button class="btn-close" @click="closeRulesModal"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <!-- Rules List -->
          <div v-if="!editingRule" class="mb-3">
            <div class="d-flex justify-between align-center mb-2">
              <span class="text-muted small">Правила применяются в порядке приоритета. Первое совпавшее выполняется.</span>
              <button class="btn btn-sm btn-primary" @click="startCreateRule">
                <i class="fas fa-plus mr-1"></i> Добавить
              </button>
            </div>
            <table v-if="rules.length" class="table table-sm table-hover">
              <thead>
                <tr>
                  <th style="width: 50px;">Прио.</th>
                  <th>Название</th>
                  <th>Паттерн</th>
                  <th>Тип</th>
                  <th>Действие</th>
                  <th style="width: 100px;">Активно</th>
                  <th style="width: 150px;"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="rule in rules" :key="rule.id">
                  <td class="text-center">{{ rule.priority }}</td>
                  <td>{{ rule.name }}</td>
                  <td class="small text-muted">{{ rule.match_type }}: "{{ rule.match_text }}"</td>
                  <td>
                    <span v-if="rule.action_type === 'category'" class="badge badge-sm badge-primary">Категория</span>
                    <span v-else-if="rule.action_type === 'ignore'" class="badge badge-sm badge-warning">Не учитывать</span>
                    <span v-else-if="rule.action_type === 'create_dds'" class="badge badge-sm badge-success">Создать ДДС</span>
                  </td>
                  <td class="small">{{ rule.category_code || '-' }}</td>
                  <td class="text-center">
                    <div class="form-check form-switch m-0 d-inline-block">
                      <input class="form-check-input" type="checkbox" :checked="rule.is_active" @change="toggleRuleActive(rule)">
                    </div>
                  </td>
                  <td class="text-right">
                    <button class="btn btn-xs btn-outline-primary mr-1" title="Обработать все" @click="applyRuleToAll(rule)" :disabled="applyingRule === rule.id">
                      <i :class="applyingRule === rule.id ? 'fas fa-spinner fa-spin' : 'fas fa-play'"></i>
                    </button>
                    <button class="btn btn-xs btn-outline-secondary mr-1" title="Редактировать" @click="startEditRule(rule)">
                      <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-xs btn-outline-danger" title="Удалить" @click="deleteRule(rule)">
                      <i class="fas fa-trash"></i>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-else class="text-center text-muted p-4">
              Нет правил. Нажмите "Добавить" чтобы создать первое правило.
            </div>
          </div>

          <!-- Rule Edit Form -->
          <div v-else>
            <div class="d-flex align-center mb-3">
              <button class="btn btn-sm btn-text" @click="cancelEditRule"><i class="fas fa-arrow-left mr-1"></i> Назад</button>
              <h5 class="m-0 ml-2">{{ ruleForm.id ? 'Редактирование' : 'Новое правило' }}</h5>
            </div>
            <div class="row">
              <div class="col-6">
                <div class="form-group">
                  <label class="form-label">Название *</label>
                  <input v-model="ruleForm.name" class="form-control form-control-sm" placeholder="Название правила">
                </div>
              </div>
              <div class="col-6">
                <div class="form-group">
                  <label class="form-label">Приоритет</label>
                  <input v-model.number="ruleForm.priority" type="number" class="form-control form-control-sm" placeholder="100">
                </div>
              </div>
            </div>
            <div class="row">
              <div class="col-8">
                <div class="form-group">
                  <label class="form-label">Текст для поиска *</label>
                  <input v-model="ruleForm.match_text" class="form-control form-control-sm" placeholder="Текст в назначении платежа">
                </div>
              </div>
              <div class="col-4">
                <div class="form-group">
                  <label class="form-label">Тип совпадения</label>
                  <select v-model="ruleForm.match_type" class="form-select form-select-sm">
                    <option value="contains">Содержит</option>
                    <option value="starts_with">Начинается с</option>
                    <option value="ends_with">Заканчивается на</option>
                    <option value="regex">Regex</option>
                  </select>
                </div>
              </div>
            </div>
            <div class="row">
              <div class="col-6">
                <div class="form-group">
                  <label class="form-label">Действие *</label>
                  <select v-model="ruleForm.action_type" class="form-select form-select-sm">
                    <option value="category">Установить категорию</option>
                    <option value="ignore">Пометить "не учитывать"</option>
                    <option value="create_dds">Создать запись ДДС</option>
                  </select>
                </div>
              </div>
              <div class="col-6">
                <div class="form-group">
                  <label class="form-label">Категория</label>
                  <CategorySmartSelect
                    v-model="ruleForm.category_code"
                    :options="allCategoryOptions"
                    placeholder="Категория"
                    size="sm"
                    input-class="form-select-sm"
                    :disabled="ruleForm.action_type === 'ignore'"
                  />
                </div>
              </div>
            </div>
            <div class="d-flex justify-end gap-2 mt-3">
              <button class="btn btn-secondary" @click="cancelEditRule">Отмена</button>
              <button class="btn btn-primary" @click="saveRule" :disabled="savingRule">
                <i v-if="savingRule" class="fas fa-spinner fa-spin mr-1"></i> Сохранить
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Allocate Modal -->
    <div v-if="showAllocateModal" class="modal-overlay" v-modal-close="closeAllocateModal">
      <div class="modal-content allocation-modal" @click.stop>
        <div class="modal-header d-flex justify-between align-center">
          <h4 class="m-0">Распределение платежа</h4>
          <button class="btn btn-sm btn-secondary" @click="closeAllocateModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body allocation-modal__body">
          <div class="allocation-modal__summary">
            <div class="small text-muted">
              Док: {{ allocationTx?.doc_num || '-' }} · {{ formatDate(allocationTx?.transaction_date) }} · {{ signedAmount(allocationTx?.amount || 0) }}
            </div>
            <div class="allocation-modal__totals">
              <div>Распределено: <strong>{{ formatCurrency(allocatedDraftTotal) }}</strong></div>
              <div>Остаток: <strong :class="draftRemainder < 0 ? 'text-danger' : ''">{{ formatCurrency(draftRemainder) }}</strong></div>
            </div>
          </div>

          <div class="allocation-modal__grid">
            <section class="allocation-panel allocation-panel--main">
              <div class="allocation-panel__header">
                <div>
                  <h5 class="m-0">Записи ДДС</h5>
                  <small class="text-muted">Создание новой записи или привязка к существующей</small>
                </div>
                <div class="small text-muted text-right">
                  Остаток к распределению<br>
                  <strong>{{ formatCurrency(draftRemainder) }}</strong>
                </div>
              </div>

              <div class="allocation-panel__search">
                <input v-model="incomeExpenseSearch" class="form-control form-control-sm" placeholder="Поиск ДДС: сумма, дата, сделка, договор">
              </div>

              <div class="allocation-table-wrap">
                <table class="table table-sm allocation-table">
                  <thead>
                    <tr>
                      <th style="width: 44%;">Запись ДДС</th>
                      <th style="width: 34%;">Категория</th>
                      <th style="width: 17%;">Сумма</th>
                      <th style="width: 5%;"></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, idx) in allocationRows" :key="row.local_id">
                      <td>
                        <select v-model="row.income_expense_id" class="form-select form-select-sm">
                          <option value="">+ Создать новую запись ДДС</option>
                          <option v-for="opt in filteredIncomeExpenseOptions" :key="opt.id" :value="opt.id">
                            {{ formatIncomeExpenseOption(opt) }}
                          </option>
                        </select>
                        <small v-if="!row.income_expense_id" class="text-muted">Будет создана автоматически</small>
                      </td>
                      <td>
                        <CategorySmartSelect
                          v-model="row.category_code"
                          :options="allocationCategoryOptions"
                          placeholder="Категория"
                          size="sm"
                          input-class="form-select-sm"
                        />
                      </td>
                      <td>
                        <input v-model.number="row.amount" type="number" min="0" class="form-control form-control-sm text-right">
                      </td>
                      <td class="text-right">
                        <button class="btn btn-sm btn-text text-danger" @click="removeAllocationRow(idx)">
                          &times;
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="allocation-panel__footer">
                <button class="btn btn-sm btn-outline-secondary" @click="addAllocationRow">
                  + Добавить строку
                </button>
              </div>
            </section>

            <section class="allocation-panel allocation-panel--linked">
              <div class="allocation-panel__header">
                <div>
                  <h5 class="m-0"><i class="fas fa-link mr-1"></i> Привязанные платежи</h5>
                  <small class="text-muted">Возвраты и зачёты</small>
                </div>
                <div v-if="linkedPayments.length" class="small fw-600 text-right">
                  Сумма<br>{{ formatCurrency(linkedPaymentsTotal) }}
                </div>
              </div>

              <div v-if="linkedPayments.length" class="allocation-linked-list">
                <div v-for="lp in linkedPayments" :key="lp.id" class="allocation-linked-item">
                  <div class="allocation-linked-item__main">
                    <div class="small fw-600">№ {{ lp.doc_num || '-' }}</div>
                    <div class="small text-muted">{{ formatDate(lp.transaction_date) }}</div>
                  </div>
                  <div class="allocation-linked-item__amount" :class="lp.amount < 0 ? 'text-danger' : 'text-success'">
                    {{ signedAmount(lp.amount) }}
                  </div>
                  <button class="btn btn-sm btn-text text-danger" @click="unlinkPayment(lp.id)" title="Отвязать">
                    <i class="fas fa-unlink"></i>
                  </button>
                </div>
              </div>
              <div v-else class="allocation-linked-empty">
                Нет привязанных платежей.
              </div>

              <div class="allocation-panel__search allocation-panel__search--link">
                <input
                  v-model="linkSearch"
                  class="form-control form-control-sm"
                  placeholder="Найти платёж для привязки (номер, ИНН, назначение)..."
                  @input="debouncedLinkSearch"
                >
                <div v-if="linkSearchResults.length" class="link-search-dropdown">
                  <div
                    v-for="result in linkSearchResults"
                    :key="result.id"
                    class="link-search-item"
                    @click="linkPayment(result.id)"
                  >
                    <div class="d-flex justify-between align-center">
                      <span class="small fw-500">
                        № {{ result.doc_num || '-' }} · {{ formatDate(result.transaction_date) }}
                      </span>
                      <span class="small fw-600" :class="result.amount < 0 ? 'text-danger' : 'text-success'">
                        {{ signedAmount(result.amount) }}
                      </span>
                    </div>
                    <div class="text-muted small text-truncate" style="font-size: 11px;">
                      {{ result.payer_name || '' }} → {{ result.payee_name || '' }}
                    </div>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeAllocateModal">Отмена</button>
          <button class="btn btn-primary" @click="saveAllocations">Сохранить</button>
        </div>
      </div>
    </div>

    <!-- UI Feedback Modal -->
    <div v-if="uiModal.open" class="modal-overlay" v-modal-close="cancelUiModal">
      <div class="modal-content" @click.stop style="max-width: 480px;">
        <div class="modal-header">
          <h4>{{ uiModal.title }}</h4>
          <button class="btn-close" @click="cancelUiModal"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="small" style="line-height: 1.5;">{{ uiModal.message }}</div>
        </div>
        <div class="modal-footer">
          <button v-if="uiModal.showCancel" class="btn btn-secondary" @click="cancelUiModal">
            {{ uiModal.cancelText }}
          </button>
          <button class="btn btn-primary" @click="confirmUiModal">
            {{ uiModal.confirmText }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import { api } from '@/services/api'
import SkeletonLoader from '../components/ui/SkeletonLoader.vue'
import CategorySmartSelect from '../components/ui/CategorySmartSelect.vue'
import UiChipFilter from '../components/ui/UiChipFilter.vue'
import { useToast } from '../composables/useToast'

const TREASURY_TYPE_OPTIONS = [
  { value: 'expense', label: 'Расход', color: '#ef4444' },
  { value: 'income',  label: 'Приход', color: '#22c55e' },
]

const TREASURY_STATUS_OPTIONS = [
  { value: 'allocated',     label: 'Распределено',    color: '#22c55e' },
  { value: 'not_allocated', label: 'Не распределено', color: '#ef4444' },
  { value: 'ignored',       label: 'Не учитывать',    color: '#6b7280' },
]

const TREASURY_CALC_TYPE_OPTIONS = [
  { value: 'vtb',      label: 'ВТБ',    color: '#2563eb' },
  { value: 'material', label: 'Матер.', color: '#a855f7' },
  { value: 'other',    label: 'Иной',   color: '#6b7280' },
]

export default {
  name: 'Treasury',
  components: { SkeletonLoader, CategorySmartSelect, UiChipFilter },
  setup() {
    const toast = useToast()
    const importing = ref(false)
    const fileInput = ref(null)
    const selectedFile = ref(null)
    const importResult = ref(null)
    const importPreview = ref(null)
    const showImportConfirmModal = ref(false)
    const createMissingCompanies = ref(false)
    const defaultCalcType = ref('vtb')

    // Create transaction modal
    const showCreateModal = ref(false)
    const creatingTx = ref(false)
    const createForm = ref({
      doc_num: '',
      transaction_date: '',
      amount: 0,
      calc_type: 'vtb',
      payer_name: '',
      payer_inn: '',
      payee_name: '',
      payee_inn: '',
      purpose: '',
      category_code: ''
    })

    // Rules management
    const showRulesModal = ref(false)
    const rules = ref([])
    const editingRule = ref(false)
    const savingRule = ref(false)
    const applyingRule = ref(null)
    const ruleForm = ref({
      id: null,
      name: '',
      match_text: '',
      match_type: 'contains',
      action_type: 'category',
      category_code: '',
      is_active: true,
      priority: 100
    })

    const transactions = ref([])
    const loading = ref(false)
    const stats = ref({ total: 0, ok: 0, alert: 0, ignored: 0 })
    const filters = ref({
      search: '', payer: '', payee: '', type: '', status: '', category: '', calcType: ''
    })
    
    // Pagination
    const currentPage = ref(1)
    const pageSize = ref(25)
    const totalCount = ref(0)
    const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize.value)))
    
    // Selection & Bulk actions
    const selectedIds = ref([])
    const bulkAction = ref('')
    const bulkCategory = ref('')
    const bulkCalcType = ref('')
    const bulkLoading = ref(false)
    const allSelected = computed(() => transactions.value.length > 0 && selectedIds.value.length === transactions.value.length)
    
    // Debounced search
    let searchTimeout = null
    const debouncedSearch = () => {
      clearTimeout(searchTimeout)
      searchTimeout = setTimeout(() => loadTransactions(), 300)
    }

    // Unified UI modal for alerts/confirmations
    const uiModal = ref({
      open: false,
      title: 'Сообщение',
      message: '',
      showCancel: false,
      confirmText: 'ОК',
      cancelText: 'Отмена',
      resolve: null
    })

    const openConfirm = (message, title = 'Подтверждение') => new Promise((resolve) => {
      uiModal.value = {
        open: true,
        title,
        message,
        showCancel: true,
        confirmText: 'Да',
        cancelText: 'Отмена',
        resolve
      }
    })

    const closeUiModal = (result = false) => {
      const resolver = uiModal.value.resolve
      const shouldResolve = uiModal.value.showCancel && typeof resolver === 'function'
      uiModal.value.open = false
      uiModal.value.resolve = null
      if (shouldResolve) resolver(Boolean(result))
    }

    const confirmUiModal = () => closeUiModal(true)
    const cancelUiModal = () => closeUiModal(false)


    const expenseCategories = [
      '1.1.1. Материальные затраты. Оборудование и материалы. Для прямой реализации',
      '1.1.2. Материальные затраты. Оборудование и материалы. Тара и упаковка',
      '1.2.1. Материальные затраты. Прочие ТМЦ. Канцелярия',
      '1.2.2. Материальные затраты. Прочие ТМЦ. Компьютерное оборудование',
      '2.1.1.1.1. Фонд оплаты труда. Заработная плата. Штатных сотрудников. По ставкам и тарифам. Административный персонал',
      '2.1.1.1.2. Фонд оплаты труда. Заработная плата. Штатных сотрудников. По ставкам и тарифам. Производственный персонал',
      '2.1.1.2.1. Фонд оплаты труда. Заработная плата. Штатных сотрудников. Премии и доплаты. Административный персонал',
      '2.1.1.2.2. Фонд оплаты труда. Заработная плата. Штатных сотрудников. Премии и доплаты. Производственный персонал',
      '2.1.1.3.1. Фонд оплаты труда. Заработная плата. Штатных сотрудников. Отпускные/компенсация. Административный персонал',
      '2.1.1.3.2. Фонд оплаты труда. Заработная плата. Штатных сотрудников. Отпускные/компенсация. Производственный персонал',
      '2.1.2.1.1. Фонд оплаты труда. Заработная плата. По договорам. Административные. С НДС',
      '2.1.2.1.2. Фонд оплаты труда. Заработная плата. По договорам. Административные. Без НДС',
      '2.1.2.1.3. Фонд оплаты труда. Заработная плата. По договорам. Административные. ГПХ',
      '2.1.2.2.1. Фонд оплаты труда. Заработная плата. По договорам. Производственные. С НДС',
      '2.1.2.2.2. Фонд оплаты труда. Заработная плата. По договорам. Производственные. Без НДС',
      '2.1.2.2.3. Фонд оплаты труда. Заработная плата. По договорам. Производственные. ГПХ',
      '2.2.1. Фонд оплаты труда. Отчисления от заработной платы. Страховые взносы',
      '2.2.2. Фонд оплаты труда. Отчисления от заработной платы. НДФЛ',
      '2.3.1. Субподряд. С НДС',
      '2.3.2. Субподряд. Без НДС',
      '3.1.1. Аренда объектов основных средств. Аренда недвижимости. Офис',
      '3.1.2. Аренда объектов основных средств. Аренда недвижимости. Склад',
      '4.1.1.1.1. Ремонт и содержание основных средств. Содержание основных средств. Содержание недвижимости. Коммунальные услуги. Офис',
      '4.1.1.1.2. Ремонт и содержание основных средств. Содержание основных средств. Содержание недвижимости. Коммунальные услуги. Склад',
      '4.1.1.2. Ремонт и содержание основных средств. Содержание основных средств. Содержание недвижимости. Уборка',
      '4.1.2.1. Ремонт и содержание основных средств. Содержание основных средств. Содержание оборудования. Техническое обслуживание',
      '4.2.1. Ремонт и содержание основных средств. Ремонт основных средств. Ремонт недвижимости',
      '4.2.2. Ремонт и содержание основных средств. Ремонт оборудования',
      '5.1.1.1. Услуги сторонних организаций. Транспортные услуги. Доставка ТМЦ. Доставка от поставщиков',
      '5.1.1.2. Услуги сторонних организаций. Транспортные услуги. Доставка ТМЦ. Доставка покупателям',
      '5.1.2. Услуги сторонних организаций. Транспортные услуги. Доставка корреспонденции',
      '5.2.1. Услуги сторонних организаций. Юридические услуги. Консультации',
      '5.2.2. Услуги сторонних организаций. Юридические услуги. Арбитраж',
      '5.2.3. Услуги сторонних организаций. Юридические услуги. Разработка документации',
      '5.2.4. Услуги сторонних организаций. Юридические услуги. Нотариус',
      '5.3. Услуги сторонних организаций. Бухгалтерские услуги',
      '5.4.1. Услуги сторонних организаций. Коммерческие услуги. Реклама',
      '5.4.2. Услуги сторонних организаций. Коммерческие услуги. Агентское вознаграждение',
      '5.5.1. Услуги сторонних организаций. Услуги по подбору персонала. Вакансии хедхантер',
      '5.6.1. Услуги сторонних организаций. Программное обеспечение. Административное',
      '5.6.2. Услуги сторонних организаций. Программное обеспечение. Производственное',
      '5.7.1. Услуги сторонних организаций. Лицензирование деятельности. СРО',
      '5.7.2. Услуги сторонних организаций. Лицензирование деятельности. Лицензии',
      '5.7.3. Услуги сторонних организаций. Лицензирование деятельности. Федресурс',
      '5.8.1.1. Услуги сторонних организаций. Прочие услуги. Услуги связи. нтернет',
      '5.8.1.2. Услуги сторонних организаций. Прочие услуги. Услуги связи. Телефон',
      '5.8.2. Услуги сторонних организаций. Прочие услуги. Юр. Адрес',
      '6.1. Налоги. Налог на имущество',
      '6.2. Налоги. Налог на добавленную стоимость',
      '6.3. Налоги. Налог на прибыль',
      '6.4. Налоги. Прочие налоги',
      '7.1. Финансовые затраты. Проценты по кредитам',
      '7.2.1. Финансовые затраты. Прочие финансовые затраты. Банковские услуги',
      '7.2.2. Финансовые затраты. Прочие финансовые затраты. Комиссии и сборы',
      '7.2.3. Финансовые затраты. Прочие финансовые затраты. Штрафы',
      '8.1. Прочие затраты. Командировочные расходы',
      '8.2. Прочие затраты. Представительские расходы',
      '8.3.1. Прочие затраты. Хозяйственные расходы. Перевозка сотрудников',
      '8.3.2. Прочие затраты. Хозяйственные расходы. Внутренние доставки ТМЦ',
      '8.3.3. Прочие затраты. Хозяйственные расходы. Офисные инструменты',
      '8.3.4. Прочие затраты. Хозяйственные расходы. Продукты',
      '8.3.5. Прочие затраты. Хозяйственные расходы. Прочие офисные затраты'
    ]

    const incomeCategories = [
      '01.01. ПР с НДС', '01.02. ПР без НДС', '02.01. Поставки с НДС', '02.02. Поставки без НДС',
      '03.01. СМР с НДС', '03.02. СМР без НДС', '04.01. Проценты', '04.02. Неустойки',
      '05.01. Иные с НДС', '05.02. Иные без НДС'
    ]

    const categoryOptions = computed(() => {
      if (filters.value.type === 'expense') return expenseCategories
      if (filters.value.type === 'income') return incomeCategories
      return []
    })

    const allCategoryOptions = computed(() => [
      ...expenseCategories.map((value) => ({ value, label: value, hint: 'Расходы' })),
      ...incomeCategories.map((value) => ({ value, label: value, hint: 'Доходы' }))
    ])

    const createFormCategories = computed(() => {
      return createForm.value.amount < 0 ? expenseCategories : incomeCategories
    })

    const showAllocateModal = ref(false)
    const allocationTx = ref(null)
    const allocationRows = ref([])
    const deletedAllocationIds = ref([])
    const incomeExpenseOptions = ref([])
    const incomeExpenseSearch = ref('')
    const allocationCategoryOptions = computed(() => {
      if (!allocationTx.value) return []
      return allocationTx.value.amount < 0 ? expenseCategories : incomeCategories
    })

    const filteredIncomeExpenseOptions = computed(() => {
      const query = (incomeExpenseSearch.value || '').trim().toLowerCase()
      if (!query) return incomeExpenseOptions.value
      const tokens = query.split(/\s+/)
      return incomeExpenseOptions.value.filter((entry) => {
        const haystack = [
          formatDate(entry.plan_date),
          String(entry.amount || ''),
          entry.deal_title,
          entry.contract_number
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase()
        return tokens.every((token) => haystack.includes(token))
      })
    })

    // Привязанные платежи (возвраты/зачёты)
    const linkedPayments = ref([])
    const linkSearch = ref('')
    const linkSearchResults = ref([])
    const linkSearchLoading = ref(false)
    let linkSearchTimer = null

    const linkedPaymentsTotal = computed(() => {
      return linkedPayments.value.reduce((sum, lp) => sum + Math.abs(lp.amount), 0)
    })

    const allocatedDraftTotal = computed(() => {
      return allocationRows.value.reduce((sum, row) => sum + (Number(row.amount) || 0), 0)
    })
    const draftRemainder = computed(() => {
      const total = Math.abs(allocationTx.value?.amount || 0)
      return Math.max(total - allocatedDraftTotal.value - linkedPaymentsTotal.value, 0)
    })

    const handleFileSelect = (ev) => { if(ev.target.files[0]) selectedFile.value = ev.target.files[0] }
    const openFilePicker = () => fileInput.value && fileInput.value.click()

    // Create transaction modal functions
    const resetCreateForm = () => {
      createForm.value = {
        doc_num: '',
        transaction_date: new Date().toISOString().split('T')[0],
        amount: 0,
        calc_type: 'vtb',
        payer_name: '',
        payer_inn: '',
        payee_name: '',
        payee_inn: '',
        purpose: '',
        category_code: ''
      }
    }

    const openCreateModal = () => {
      resetCreateForm()
      showCreateModal.value = true
    }

    const closeCreateModal = () => {
      showCreateModal.value = false
    }

    const submitCreateForm = async () => {
      const form = createForm.value
      if (!form.doc_num.trim()) {
        toast.warning('Номер документа обязателен')
        return
      }
      if (!form.transaction_date) {
        toast.warning('Дата обязательна')
        return
      }
      if (!form.amount || form.amount === 0) {
        toast.warning('Сумма обязательна (отрицательная для расходов, положительная для доходов)')
        return
      }

      creatingTx.value = true
      try {
        await api.treasury.create({
          doc_num: form.doc_num.trim(),
          transaction_date: form.transaction_date,
          amount: form.amount,
          calc_type: form.calc_type || 'vtb',
          payer_name: form.payer_name || null,
          payer_inn: form.payer_inn || null,
          payee_name: form.payee_name || null,
          payee_inn: form.payee_inn || null,
          purpose: form.purpose || null,
          category_code: form.category_code || null
        })
        closeCreateModal()
        await loadTransactions()
      } catch (e) {
        console.error(e)
        const msg = e.response?.data?.detail || 'Ошибка создания транзакции'
        toast.error(msg)
      } finally {
        creatingTx.value = false
      }
    }

    // Rules management functions
    const loadRules = async () => {
      try {
        const res = await api.treasury.listRules()
        rules.value = res || []
      } catch (e) {
        console.error(e)
        rules.value = []
      }
    }

    const openRulesModal = async () => {
      await loadRules()
      editingRule.value = false
      showRulesModal.value = true
    }

    const closeRulesModal = () => {
      showRulesModal.value = false
      editingRule.value = false
    }

    const resetRuleForm = () => {
      ruleForm.value = {
        id: null,
        name: '',
        match_text: '',
        match_type: 'contains',
        action_type: 'category',
        category_code: '',
        is_active: true,
        priority: 100
      }
    }

    const startCreateRule = () => {
      resetRuleForm()
      editingRule.value = true
    }

    const startEditRule = (rule) => {
      ruleForm.value = {
        id: rule.id,
        name: rule.name,
        match_text: rule.match_text,
        match_type: rule.match_type,
        action_type: rule.action_type,
        category_code: rule.category_code || '',
        is_active: rule.is_active,
        priority: rule.priority
      }
      editingRule.value = true
    }

    const cancelEditRule = () => {
      editingRule.value = false
      resetRuleForm()
    }

    const saveRule = async () => {
      const form = ruleForm.value
      if (!form.name.trim()) {
        toast.warning('Название обязательно')
        return
      }
      if (!form.match_text.trim()) {
        toast.warning('Текст для поиска обязателен')
        return
      }

      savingRule.value = true
      try {
        if (form.id) {
          await api.treasury.updateRule(form.id, {
            name: form.name,
            match_text: form.match_text,
            match_type: form.match_type,
            action_type: form.action_type,
            category_code: form.category_code || null,
            is_active: form.is_active,
            priority: form.priority
          })
        } else {
          await api.treasury.createRule({
            name: form.name,
            match_text: form.match_text,
            match_type: form.match_type,
            action_type: form.action_type,
            category_code: form.category_code || null,
            is_active: form.is_active,
            priority: form.priority
          })
        }
        await loadRules()
        editingRule.value = false
        resetRuleForm()
      } catch (e) {
        console.error(e)
        toast.error(e.response?.data?.detail || 'Ошибка сохранения правила')
      } finally {
        savingRule.value = false
      }
    }

    const deleteRule = async (rule) => {
      if (!(await openConfirm(`Удалить правило "${rule.name}"?`))) return
      try {
        await api.treasury.removeRule(rule.id)
        await loadRules()
      } catch (e) {
        console.error(e)
        toast.error('Ошибка удаления')
      }
    }

    const toggleRuleActive = async (rule) => {
      try {
        await api.treasury.updateRule(rule.id, {
          is_active: !rule.is_active
        })
        await loadRules()
      } catch (e) {
        console.error(e)
      }
    }

    const applyRuleToAll = async (rule) => {
      if (!(await openConfirm(`Применить правило "${rule.name}" ко всем существующим транзакциям?`))) return
      applyingRule.value = rule.id
      try {
        const res = await api.treasury.applyRuleToAll(rule.id)
        toast.success(`Обработано транзакций: ${res.applied_count} из ${res.total_checked}`)
        await loadTransactions()
      } catch (e) {
        console.error(e)
        toast.error('Ошибка применения правила')
      } finally {
        applyingRule.value = null
      }
    }

    const previewImport = async () => {
       if (!selectedFile.value) return
       importing.value = true
       const fd = new FormData(); fd.append('file', selectedFile.value)
       try {
          const res = await api.treasury.importPreview(fd, { default_calc_type: defaultCalcType.value })
          importPreview.value = res
          showImportConfirmModal.value = true
       } catch (e) { toast.error('Ошибка предпросмотра'); console.error(e) }
       finally { importing.value = false }
    }

    const confirmImport = async () => {
       importing.value = true
       const fd = new FormData(); fd.append('file', selectedFile.value)
       try {
          const res = await api.treasury.importConfirm(fd, {
             create_missing_companies: createMissingCompanies.value,
             default_calc_type: defaultCalcType.value
          })
          importResult.value = res; selectedFile.value = null; importPreview.value = null; showImportConfirmModal.value = false
          await loadTransactions(); toast.success('Импорт завершен')
       } catch (e) { toast.error('Ошибка импорта'); console.error(e) }
       finally { importing.value = false }
    }

    const loadTransactions = async () => {
       loading.value = true
       selectedIds.value = [] // Clear selection on reload
       try {
          const params = {
            skip: (currentPage.value - 1) * pageSize.value,
            limit: pageSize.value
          }
          // Add filters
          if (filters.value.search) params.search = filters.value.search
          if (filters.value.payer) params.payer_name = filters.value.payer
          if (filters.value.payee) params.payee_name = filters.value.payee
          if (filters.value.type) params.tx_type = filters.value.type
          if (filters.value.status) params.status = filters.value.status
          if (filters.value.calcType) params.calc_type = filters.value.calcType
          
          const res = await api.treasury.list(params)
          transactions.value = res.items || []
          stats.value = res.stats || { total: 0, ok: 0, alert: 0, ignored: 0 }
          totalCount.value = res.stats?.total || transactions.value.length
       } catch(e) { console.error(e) }
       finally { loading.value = false }
    }
    
    // Pagination functions
    const goToPage = (page) => {
      currentPage.value = Math.max(1, Math.min(page, totalPages.value))
      loadTransactions()
    }
    
    // Selection functions
    const toggleSelect = (id) => {
      const idx = selectedIds.value.indexOf(id)
      if (idx === -1) {
        selectedIds.value.push(id)
      } else {
        selectedIds.value.splice(idx, 1)
      }
    }
    
    const toggleSelectAll = () => {
      if (allSelected.value) {
        selectedIds.value = []
      } else {
        selectedIds.value = transactions.value.map(tx => tx.id)
      }
    }
    
    const clearSelection = () => {
      selectedIds.value = []
      bulkAction.value = ''
      bulkCategory.value = ''
      bulkCalcType.value = ''
    }
    
    // Bulk action
    const applyBulkAction = async () => {
      if (!selectedIds.value.length || !bulkAction.value) return
      
      bulkLoading.value = true
      try {
        const payload = {
          transaction_ids: selectedIds.value,
          action: bulkAction.value
        }
        if (bulkAction.value === 'category') {
          if (!bulkCategory.value) { toast.warning('Выберите категорию'); return }
          payload.category_code = bulkCategory.value
        }
        if (bulkAction.value === 'calc_type') {
          if (!bulkCalcType.value) { toast.warning('Выберите расчёт'); return }
          payload.calc_type = bulkCalcType.value
        }
        
        await api.treasury.bulkAction(payload)
        clearSelection()
        await loadTransactions()
        toast.success('Операция выполнена')
      } catch(e) {
        console.error(e)
        toast.error(e.response?.data?.detail || 'Ошибка выполнения')
      } finally {
        bulkLoading.value = false
      }
    }

    const deleteTransaction = async (tx) => {
       if (!(await openConfirm(`Удалить транзакцию №${tx.doc_num} от ${formatDate(tx.transaction_date)} на сумму ${signedAmount(tx.amount)}?`))) return
       try {
          await api.treasury.remove(tx.id)
          await loadTransactions()
       } catch(e) {
          console.error(e)
          toast.error('Ошибка удаления транзакции')
       }
    }


    const formatIncomeExpenseOption = (entry) => {
      if (!entry) return '-'
      const date = entry.plan_date ? formatDate(entry.plan_date) : '-'
      const amount = formatCurrency(entry.amount)
      const deal = entry.deal_title || entry.contract_number || ''
      return `${date} · ${amount}${deal ? ' · ' + deal : ''}`
    }

    const mergeIncomeExpenseOptions = (baseItems, extraItems = []) => {
      const seen = new Set()
      return [...(baseItems || []), ...(extraItems || [])]
        .filter(Boolean)
        .filter((entry) => {
          if (!entry.id) return false
          const key = String(entry.id)
          if (seen.has(key)) return false
          seen.add(key)
          return true
        })
    }

    const loadIncomeExpenseEntryById = async (entryId) => {
      try {
        const res = await api.incomeExpense.getById(entryId)
        return res || null
      } catch (e) {
        return null
      }
    }

    const loadIncomeExpenseOptions = async () => {
      if (!allocationTx.value) return
      try {
        const direction = allocationTx.value.amount < 0 ? 'expense' : 'income'
        const res = await api.incomeExpense.list({
          direction,
          exclude_paid: true,
          limit: 500
        })
        const items = res || []
        const visibleItems = items.filter((entry) => entry.payment_status !== 'paid')
        const visibleIds = new Set(visibleItems.map((entry) => String(entry.id)))
        const selectedIds = allocationRows.value
          .map((row) => row.income_expense_id)
          .filter(Boolean)
          .map((id) => String(id))
        const missingIds = [...new Set(selectedIds)].filter((id) => !visibleIds.has(id))
        const missingItems = missingIds.length
          ? (await Promise.all(missingIds.map(loadIncomeExpenseEntryById))).filter(Boolean)
          : []
        incomeExpenseOptions.value = mergeIncomeExpenseOptions(visibleItems, missingItems)
      } catch (e) {
        console.error(e)
        incomeExpenseOptions.value = []
      }
    }

    const openAllocate = async (tx) => {
      allocationTx.value = tx
      incomeExpenseSearch.value = ''
      deletedAllocationIds.value = []
      linkSearch.value = ''
      linkSearchResults.value = []
      allocationRows.value = (tx.allocations || []).map((a) => ({
        id: a.id,
        local_id: a.id,
        income_expense_id: a.income_expense_id,
        category_code: a.category_code || '',
        amount: a.amount
      }))
      if (!allocationRows.value.length) {
        allocationRows.value = [{
          id: null,
          local_id: `new-${Date.now()}`,
          income_expense_id: '',
          category_code: '',
          amount: 0
        }]
      }
      // Загружаем привязанные платежи
      linkedPayments.value = tx.linked_payments || []
      try {
        const lpRes = await api.treasury.listLinked(tx.id)
        linkedPayments.value = lpRes || []
      } catch (e) {
        linkedPayments.value = tx.linked_payments || []
      }
      await loadIncomeExpenseOptions()
      showAllocateModal.value = true
    }

    const closeAllocateModal = () => {
      showAllocateModal.value = false
      allocationTx.value = null
      allocationRows.value = []
      deletedAllocationIds.value = []
      linkedPayments.value = []
      linkSearch.value = ''
      linkSearchResults.value = []
    }

    const addAllocationRow = () => {
      allocationRows.value.push({
        id: null,
        local_id: `new-${Date.now()}-${allocationRows.value.length}`,
        income_expense_id: '',
        category_code: '',
        amount: 0
      })
    }

    const removeAllocationRow = (idx) => {
      const row = allocationRows.value[idx]
      if (row?.id) deletedAllocationIds.value.push(row.id)
      allocationRows.value.splice(idx, 1)
      if (!allocationRows.value.length) addAllocationRow()
    }

    const saveAllocations = async () => {
      if (!allocationTx.value) return
      const tx = allocationTx.value
      const total = Math.abs(tx.amount || 0)
      const ignore = String(tx.ignore_flag || '').trim().toLowerCase() === 'да'

      const rows = allocationRows.value
      for (const row of rows) {
        if (!row.amount || row.amount <= 0) {
          toast.warning('Сумма должна быть больше 0.')
          return
        }
        if (!row.income_expense_id) {
          // Автосоздание ДДС — обязательна категория
          if (!row.category_code) {
            toast.warning('Для автосоздания записи ДДС укажите категорию.')
            return
          }
        }
        if (!ignore && !row.category_code) {
          toast.warning('Категория обязательна (если платеж не помечен как "Не учитывать").')
          return
        }
      }

      const totalWithLinked = rows.reduce((sum, r) => sum + (Number(r.amount) || 0), 0) + linkedPaymentsTotal.value
      if (totalWithLinked > total + 0.01) {
        toast.warning('Сумма распределений и привязанных платежей превышает сумму платежа.')
        return
      }

      try {
        const createPayloads = rows.filter((r) => !r.id).map((r) => ({
          income_expense_id: r.income_expense_id || null,
          amount: r.amount,
          category_code: r.category_code || null
        }))
        const updatePayloads = rows.filter((r) => r.id).map((r) => ({
          id: r.id,
          income_expense_id: r.income_expense_id || null,
          amount: r.amount,
          category_code: r.category_code || null
        }))

        await Promise.all(deletedAllocationIds.value.map((id) =>
          api.treasury.removeAllocation(id)
        ))
        await Promise.all(updatePayloads.map((r) =>
          api.treasury.updateAllocation(r.id, {
            income_expense_id: r.income_expense_id || null,
            amount: r.amount,
            category_code: r.category_code
          })
        ))
        await Promise.all(createPayloads.map((r) =>
          api.treasury.createAllocation(tx.id, r)
        ))

        await loadTransactions()
        closeAllocateModal()
      } catch (e) {
        console.error(e)
        toast.error('Ошибка сохранения распределений.')
      }
    }
    
    // Привязка платежей: поиск
    const debouncedLinkSearch = () => {
      if (linkSearchTimer) clearTimeout(linkSearchTimer)
      linkSearchTimer = setTimeout(async () => {
        const q = (linkSearch.value || '').trim()
        if (!q || q.length < 2) { linkSearchResults.value = []; return }
        linkSearchLoading.value = true
        try {
          const res = await api.treasury.list({
            search: q,
            status: 'not_allocated',
            limit: 50,
            skip: 0
          })
          const items = res?.items || []
          const txId = allocationTx.value?.id
          // Исключаем текущий платёж, уже привязанные и платежи без остатка.
          linkSearchResults.value = items.filter((item) =>
            item.id !== txId &&
            !item.linked_transaction_id &&
            (item.remainder ?? Math.abs(item.amount || 0)) > 0
          )
        } catch (e) {
          linkSearchResults.value = []
        } finally {
          linkSearchLoading.value = false
        }
      }, 400)
    }

    const linkPayment = async (linkedId) => {
      if (!allocationTx.value) return
      try {
        await api.treasury.linkTransaction(allocationTx.value.id, {
          linked_transaction_id: linkedId
        })
        // Перезагружаем привязанные
        const lpRes = await api.treasury.listLinked(allocationTx.value.id)
        linkedPayments.value = lpRes || []
        linkSearch.value = ''
        linkSearchResults.value = []
      } catch (e) {
        console.error(e)
        toast.error(e?.response?.data?.detail || 'Ошибка привязки платежа.')
      }
    }

    const unlinkPayment = async (linkedId) => {
      if (!allocationTx.value) return
      try {
        await api.treasury.unlinkTransaction(allocationTx.value.id, linkedId)
        linkedPayments.value = linkedPayments.value.filter((lp) => lp.id !== linkedId)
      } catch (e) {
        console.error(e)
        toast.error('Ошибка отвязки платежа.')
      }
    }

    const onTypeChange = () => { filters.value.category = ''; loadTransactions() }
    const updateField = async (id, payload) => {
       try { await api.treasury.update(id, payload); await loadTransactions() }
       catch(e) { console.error(e) }
    }
    
    const isIgnored = (tx) => {
      const raw = String(tx.ignore_flag || '').trim().toLowerCase()
      if (!raw) return false
      if (['да', 'yes', 'true', '1', 'y', 'on', 'истина'].includes(raw)) return true
      if (['нет', 'no', 'false', '0', 'n', 'off'].includes(raw)) return false
      return false
    }
    const isFullyAllocated = (tx) => {
      if (isIgnored(tx)) return false
      const totalAmount = Math.abs(tx.amount)
      const allocatedAmount = tx.allocated_amount || 0
      // Fully allocated if remainder is 0 or negligible
      return allocatedAmount >= totalAmount * 0.99
    }
    const isOk = (tx) => isIgnored(tx) || isFullyAllocated(tx)
    const rowCategories = (tx) => tx.amount < 0 ? expenseCategories : incomeCategories
    const rowClass = (tx) => {
      if (isIgnored(tx)) return 'row-ignored'
      if (isFullyAllocated(tx)) return 'row-success'
      return 'row-danger'
    }
    const amountClass = (tx) => tx.amount < 0 ? 'text-danger' : 'text-success'
    const signedAmount = (a) => { const v = Math.abs(a); const f = new Intl.NumberFormat('ru-RU').format(v); return a < 0 ? `- ${f}` : f }
    const shortId = (id) => id ? String(id).slice(0, 8) : ''
    const formatCurrency = (v) => v!=null ? new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', minimumFractionDigits: 0 }).format(v) : '0 ₽'
    const formatDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU') : '-'
    const formatFileSize = (b) => { if(!b) return '0 B'; const k=1024; const s=['B','KB','MB']; const i=Math.floor(Math.log(b)/Math.log(k)); return parseFloat((b/Math.pow(k,i)).toFixed(2))+' '+s[i] }
    const closeImportModal = () => showImportConfirmModal.value = false

    onMounted(() => loadTransactions())

    return {
       TREASURY_TYPE_OPTIONS, TREASURY_STATUS_OPTIONS, TREASURY_CALC_TYPE_OPTIONS,
       importing, fileInput, selectedFile, importResult, importPreview, showImportConfirmModal,
       createMissingCompanies, defaultCalcType, transactions, loading, stats, filters, categoryOptions, allCategoryOptions,
       showAllocateModal, allocationTx, allocationRows, incomeExpenseOptions, incomeExpenseSearch, allocationCategoryOptions,
       filteredIncomeExpenseOptions,
       allocatedDraftTotal, draftRemainder,
       // Pagination
       currentPage, pageSize, totalCount, totalPages, goToPage,
       // Selection & Bulk
       selectedIds, bulkAction, bulkCategory, bulkCalcType, bulkLoading, allSelected,
       toggleSelect, toggleSelectAll, clearSelection, applyBulkAction,
       debouncedSearch,
       // Create modal
       showCreateModal, creatingTx, createForm, createFormCategories,
       openCreateModal, closeCreateModal, submitCreateForm,
       // Rules modal
       showRulesModal, rules, editingRule, savingRule, applyingRule, ruleForm,
       openRulesModal, closeRulesModal, startCreateRule, startEditRule, cancelEditRule,
       saveRule, deleteRule, toggleRuleActive, applyRuleToAll,
       expenseCategories, incomeCategories,
       // Other
       handleFileSelect, openFilePicker, previewImport, confirmImport, closeImportModal,
       loadTransactions, deleteTransaction, onTypeChange, updateField, 
       isOk, isIgnored, isFullyAllocated, rowCategories, rowClass, amountClass,
       signedAmount, shortId, formatDate, formatCurrency, formatFileSize,
       openAllocate, closeAllocateModal, addAllocationRow, removeAllocationRow, saveAllocations,
       formatIncomeExpenseOption,
       // Linked payments
       linkedPayments, linkedPaymentsTotal, linkSearch, linkSearchResults, linkSearchLoading,
       debouncedLinkSearch, linkPayment, unlinkPayment,
       uiModal, confirmUiModal, cancelUiModal
    }
  }
}
</script>


<style scoped>
/* ── Tasks reference standard: ONE unified card (header → stats →
   filters → table body), white chrome, soft shadow, flush bands.
   Scoped to the main page; allocation-modal styles below untouched. ── */
.treasury-view {
  --apr-card-bg: rgba(255, 255, 255, 0.97);
  --apr-card-border: rgba(216, 224, 240, 0.92);
  --apr-card-shadow: 0 18px 42px rgba(15, 23, 42, 0.06);
  --apr-radius: 20px;
  --apr-ink: #0a1629;
  --apr-muted: #7d8592;
  --apr-soft: #f6f8fb;
  padding: 12px !important;
}

/* The single card — fills the viewport to the bottom (Tasks behaviour);
   table body scrolls internally. */
.treasury-view {
  min-height: 0;
}
.trz-card {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  background: var(--apr-card-bg);
  border: 1px solid var(--apr-card-border);
  border-radius: var(--apr-radius);
  box-shadow: var(--apr-card-shadow);
  overflow: hidden;
}

/* Header band: title + stats chips inline (left), actions (right) */
.trz-card > .d-flex:first-child {
  margin: 0 !important;
  padding: 10px 16px;
  border-bottom: 1px solid var(--apr-card-border);
}
.trz-head-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  min-width: 0;
}
.trz-stats {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.treasury-view h2 {
  font-size: 1.15rem !important;
  font-weight: 800 !important;
  color: var(--apr-ink);
  white-space: nowrap;
}
.treasury-view .badge.badge-lg {
  border-radius: var(--radius-pill, 999px);
  font-size: 0.72rem;
  font-weight: 700;
  padding: 4px 10px;
}

/* Inner sections → flush bands (strip card chrome) */
.treasury-view .trz-card .card {
  background: transparent;
  border: 0;
  border-radius: 0;
  box-shadow: none;
  margin: 0;
}

/* Filters + bulk bar → soft-tint band with divider */
.treasury-view .trz-card .card.flex-shrink-0,
.treasury-view .trz-card .card.bg-primary-subtle {
  background: var(--apr-soft);
  border-bottom: 1px solid var(--apr-card-border);
  padding: 8px 16px;
}

/* Filters band must NOT clip the chip-filter dropdowns and must stack
   ABOVE the table (otherwise statuses/calc menus open under the rows). */
.treasury-view .trz-card .card.flex-shrink-0 {
  overflow: visible;
  position: relative;
  z-index: 30;
}
.treasury-view .trz-card .card.flex-shrink-0 .trz-filters-grid,
.treasury-view .trz-card .card.flex-shrink-0 .form-group {
  overflow: visible;
}
/* Table card stays below the filters dropdowns */
.treasury-view .trz-card .card.flex-grow-1 {
  position: relative;
  z-index: 1;
}
/* Chip-filter menu above the sticky table header (z-index:10) too */
.treasury-view :deep(.ui-chip-filter__menu) {
  z-index: 60;
}

/* Filters row: chip filters size to content (no stretched gaps) */
.treasury-view .trz-filters-grid { align-items: center; }
.treasury-view .trz-filters-grid > .form-group { min-width: 0; }
.treasury-view .trz-filters-grid > .form-group:nth-child(n+4):nth-child(-n+6) {
  min-width: 140px;
  max-width: 220px;
}

/* Floating bulk-action bar — bottom mini-modal (Tasks pattern) */
.bulk-bar {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1500;
  background: var(--md-sys-color-primary, #1976d2);
  color: #fff;
  border-radius: 14px;
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 12px 32px rgba(13, 71, 161, 0.35);
  flex-wrap: wrap;
  max-width: calc(100vw - 32px);
}
.bulk-bar__info { display: flex; align-items: center; gap: 8px; white-space: nowrap; }
.bulk-bar__actions { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.bulk-bar .form-control-sm {
  height: 30px;
  padding: 4px 8px;
  font-size: 0.82rem;
  min-width: 150px;
}
.bulk-bar .btn-outline-secondary {
  background: transparent;
  border-color: rgba(255, 255, 255, 0.4);
  color: #fff;
}
.bulk-bar .btn-outline-secondary:hover { background: rgba(255, 255, 255, 0.12); }
.bulk-bar .bulk-bar__apply {
  background: #fff;
  color: var(--md-sys-color-primary, #1976d2);
  border: 1px solid #fff;
  font-weight: 700;
}
.bulk-bar .bulk-bar__apply:hover:not(:disabled) { background: rgba(255, 255, 255, 0.88); }
.bulk-bar .bulk-bar__apply:disabled { opacity: 0.6; cursor: not-allowed; }
.bulk-bar-enter-active, .bulk-bar-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.bulk-bar-enter-from, .bulk-bar-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}
@media (max-width: 600px) {
  .bulk-bar { left: 8px; right: 8px; transform: none; }
  .bulk-bar-enter-from, .bulk-bar-leave-to { transform: translateY(20px); }
}

/* Loading skeleton band */
.treasury-view .trz-card .card.p-3 {
  border-bottom: 1px solid var(--apr-card-border);
}

/* Table card = body: fills remaining height to the bottom of the screen
   (like Tasks); the table area scrolls internally. */
.treasury-view .trz-card .card.flex-grow-1 {
  flex: 1;
  min-height: 0;
  padding: 0;
}
.treasury-view .trz-card .card.flex-grow-1 > .overflow-auto {
  flex: 1;
  min-height: 0;
}

/* Transactions table — compact, soft-tint sticky head, hairline rows */
.treasury-view .treasury-table { font-size: 0.82rem; }
.treasury-view .treasury-table thead th,
.treasury-view .sticky-header th {
  background: var(--apr-soft) !important;
  color: var(--apr-muted);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  border-bottom: 1px solid var(--apr-card-border);
}
.treasury-view .treasury-table td,
.treasury-view .treasury-table th {
  border-color: var(--apr-card-border);
}
.treasury-view .treasury-table tbody tr:hover { background: var(--apr-soft); }

/* Pagination footer band */
.treasury-view .trz-card .border-top {
  border-top: 1px solid var(--apr-card-border) !important;
  background: var(--apr-soft);
}

.fw-500 { font-weight: 500; }
.fw-600 { font-weight: 600; }
.text-xs { font-size: 0.75em; }
.font-mono { font-family: monospace; }
.sticky-header th { position: sticky; top: 0; background-color: var(--md-sys-color-surface); z-index: 10; }
.row-warning { background-color: rgba(255, 193, 7, 0.05); }
.text-truncate-2 {
   display: -webkit-box;
   -webkit-line-clamp: 2;
   -webkit-box-orient: vertical;
   overflow: hidden;
}
.line-height-1 { line-height: 1.2; }
/* Custom scrollbar for table if needed */
.overflow-auto::-webkit-scrollbar { width: 6px; height: 6px; }
.overflow-auto::-webkit-scrollbar-thumb { background: #ccc; border-radius: 3px; }
/* Row status colors */
.row-success { background-color: rgba(40, 167, 69, 0.15) !important; }
.row-danger { background-color: rgba(220, 53, 69, 0.15) !important; }
.row-ignored { background-color: rgba(255, 193, 7, 0.15) !important; }

.allocation-modal {
  width: min(1180px, calc(100vw - 32px));
  max-width: min(1180px, calc(100vw - 32px)) !important;
}

.allocation-modal__body {
  overflow: visible;
}

.allocation-modal__summary {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 12px;
}

.allocation-modal__totals {
  display: flex;
  gap: 16px;
  font-size: 13px;
  white-space: nowrap;
}

.allocation-modal__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.8fr);
  gap: 14px;
  align-items: start;
}

.allocation-panel {
  position: relative;
  min-width: 0;
  border: 1px solid var(--md-sys-color-outline-variant, #dfe5ee);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.62);
  padding: 12px;
}

.allocation-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.allocation-panel__header h5 {
  font-size: 14px;
  font-weight: 700;
}

.allocation-panel__search {
  position: relative;
  margin-bottom: 10px;
}

.allocation-panel__search--link {
  margin-top: 12px;
  margin-bottom: 0;
}

.allocation-table-wrap {
  overflow: visible;
}

.allocation-table {
  margin-bottom: 0;
}

.allocation-table th {
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--md-sys-color-on-surface-variant, #6b7280);
}

.allocation-table td {
  vertical-align: top;
  padding-top: 8px;
  padding-bottom: 8px;
}

.allocation-panel__footer {
  display: flex;
  justify-content: flex-start;
  margin-top: 10px;
}

.allocation-linked-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 242px;
  overflow-y: auto;
  padding-right: 2px;
}

.allocation-linked-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto 30px;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.04);
}

.allocation-linked-item__main {
  min-width: 0;
}

.allocation-linked-item__amount {
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.allocation-linked-empty {
  display: flex;
  align-items: center;
  min-height: 52px;
  padding: 10px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.035);
  color: var(--md-sys-color-on-surface-variant, #6b7280);
  font-size: 12px;
}

/* Link search dropdown */
.link-search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 100;
  background: var(--md-sys-color-surface, #fff);
  border: 1px solid var(--md-sys-color-outline-variant, #ddd);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  max-height: 220px;
  overflow-y: auto;
  margin-top: 2px;
}

.link-search-item {
  padding: 8px 12px;
  cursor: pointer;
  border-bottom: 1px solid var(--md-sys-color-outline-variant, #f0f0f0);
  transition: background-color 0.15s ease;
}

.link-search-item:last-child {
  border-bottom: none;
}

.link-search-item:hover {
  background-color: var(--md-sys-color-secondary-container, rgba(0, 102, 204, 0.08));
}

/* Linked payment indicator in main table */
.linked-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--md-sys-color-primary, #0066cc);
  margin-top: 2px;
}

.linked-indicator i {
  font-size: 10px;
}

.linked-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 10px;
  background-color: rgba(0, 102, 204, 0.1);
  color: var(--md-sys-color-primary, #0066cc);
  white-space: nowrap;
}

/* Dark theme contrast tuning for treasury */
:global(:root[data-theme="dark"]) .treasury-view .modal-content {
  background: rgba(24, 28, 34, 0.98);
  border-color: rgba(255, 255, 255, 0.16);
  color: var(--md-sys-color-on-surface);
}

:global(:root[data-theme="dark"]) .treasury-view .modal-header,
:global(:root[data-theme="dark"]) .treasury-view .modal-footer {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.12);
}

:global(:root[data-theme="dark"]) .treasury-view .modal-body {
  color: #f2f5fb;
}

:global(:root[data-theme="dark"]) .treasury-view .text-muted {
  color: #b8c1cf !important;
}

:global(:root[data-theme="dark"]) .treasury-view .treasury-table td,
:global(:root[data-theme="dark"]) .treasury-view .treasury-table th {
  color: #eef3fb;
}

:global(:root[data-theme="dark"]) .treasury-view .treasury-table .form-select,
:global(:root[data-theme="dark"]) .treasury-view .treasury-table .form-control {
  color: #eef3fb;
}

:global(:root[data-theme="dark"]) .treasury-view .row-success {
  background-color: rgba(28, 118, 62, 0.28) !important;
}

:global(:root[data-theme="dark"]) .treasury-view .row-danger {
  background-color: rgba(138, 36, 48, 0.28) !important;
}

:global(:root[data-theme="dark"]) .treasury-view .row-ignored {
  background-color: rgba(128, 94, 24, 0.26) !important;
}

:global(:root[data-theme="dark"]) .treasury-view .linked-indicator,
:global(:root[data-theme="dark"]) .treasury-view .linked-badge {
  color: #8fc3ff;
}

:global(:root[data-theme="dark"]) .treasury-view .linked-badge {
  background-color: rgba(64, 145, 255, 0.22);
}

:global(:root[data-theme="dark"]) .treasury-view .allocation-panel {
  background: rgba(255, 255, 255, 0.045);
  border-color: rgba(255, 255, 255, 0.12);
}

:global(:root[data-theme="dark"]) .treasury-view .allocation-table th {
  color: #b8c1cf;
}

:global(:root[data-theme="dark"]) .treasury-view .allocation-linked-item,
:global(:root[data-theme="dark"]) .treasury-view .allocation-linked-empty {
  background: rgba(255, 255, 255, 0.055);
}

:global(:root[data-theme="dark"]) .treasury-view .link-search-dropdown {
  background: rgba(22, 26, 32, 0.98);
  border-color: rgba(255, 255, 255, 0.16);
}

:global(:root[data-theme="dark"]) .treasury-view .link-search-item {
  color: #eef3fb;
  border-bottom-color: rgba(255, 255, 255, 0.09);
}

:global(:root[data-theme="dark"]) .treasury-view .link-search-item:hover {
  background-color: rgba(64, 145, 255, 0.18);
}

/* Mobile Responsive */
@media (max-width: 992px) {
  .d-grid[style*="grid-template-columns"] {
    grid-template-columns: 1fr 1fr !important;
  }

  .allocation-modal__grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .treasury-view {
    padding: 0 !important;
  }
  
  .treasury-view h2 {
    font-size: 1.25rem !important;
  }
  
  .treasury-view > .d-flex:first-child {
    flex-direction: column;
    gap: 8px;
  }
  
  .d-grid[style*="grid-template-columns"] {
    grid-template-columns: 1fr !important;
    gap: 8px !important;
  }
  
  .badge-lg {
    font-size: 0.75rem;
    padding: 4px 8px;
  }
  
  .treasury-table {
    min-width: 900px;
  }
  
  .modal-content {
    max-width: 100% !important;
    margin: 8px !important;
  }

  .allocation-modal {
    width: calc(100vw - 16px);
  }

  .allocation-modal__summary,
  .allocation-modal__totals {
    flex-direction: column;
    gap: 6px;
  }
  
  .modal-body .row {
    flex-direction: column;
  }
  
  .modal-body .col-6,
  .modal-body .col-4,
  .modal-body .col-8 {
    width: 100%;
  }
}
</style>


