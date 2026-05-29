<template>
  <div
    v-if="activeTab === 'overview'"
    id="panel-overview"
    class="project-overview-shell h-100"
    role="tabpanel"
    aria-labelledby="tab-overview"
  >
    <!--
      1-в-1 с .lead-detail-body на вкладке Info лидов:
        * внешний `.project-overview-shell` = единая «коробка» с одной
          рамкой 12px вокруг обеих колонок;
        * `.dashboard-grid` — 2 колонки без зазора, с вертикальным
          разделителем между ними;
        * каждая «секция» = обычный `.card` без своей рамки/тени
          (стили снимаются `.project-overview-shell .card` ниже).
    -->
    <div class="dashboard-grid h-100">
      <!-- LEFT: «Основная информация» -->
      <div class="dashboard-left d-flex flex-column gap-3">
        <div class="card p-4">
          <h3 class="card-title mb-3">Основная информация</h3>
          <div class="info-grid">
            <div class="info-row info-row--editable" @click="beginInlineEdit('title')">
              <span class="text-muted">Название</span>
              <input
                v-if="editingField === 'title'"
                ref="inlineInputRef"
                v-model="editDraft"
                type="text"
                class="info-edit-input"
                :disabled="inlineSaving"
                @click.stop
                @keydown.enter.prevent="saveInlineEdit"
                @keydown.esc.prevent="cancelInlineEdit"
                @blur="saveInlineEdit"
              />
              <span v-else class="fw-500 text-right info-row__value">{{ project.title || '—' }}</span>
            </div>

            <div class="info-row info-row--editable" @click="beginInlineEdit('obj_name')">
              <span class="text-muted">Объект</span>
              <input
                v-if="editingField === 'obj_name'"
                ref="inlineInputRef"
                v-model="editDraft"
                type="text"
                class="info-edit-input"
                :disabled="inlineSaving"
                @click.stop
                @keydown.enter.prevent="saveInlineEdit"
                @keydown.esc.prevent="cancelInlineEdit"
                @blur="saveInlineEdit"
              />
              <span v-else class="fw-500 text-right info-row__value">{{ project.obj_name || '—' }}</span>
            </div>

            <div class="info-row info-row--editable" @click="beginInlineEdit('address')">
              <span class="text-muted">Адрес</span>
              <input
                v-if="editingField === 'address'"
                ref="inlineInputRef"
                v-model="editDraft"
                type="text"
                class="info-edit-input"
                :disabled="inlineSaving"
                @click.stop
                @keydown.enter.prevent="saveInlineEdit"
                @keydown.esc.prevent="cancelInlineEdit"
                @blur="saveInlineEdit"
              />
              <span v-else class="fw-500 text-right info-row__value">{{ project.address || '—' }}</span>
            </div>

            <div class="info-row info-row--editable" @click="beginInlineEdit('object_type')">
              <span class="text-muted">Тип объекта</span>
              <select
                v-if="editingField === 'object_type'"
                ref="inlineInputRef"
                v-model="editDraft"
                class="info-edit-input"
                :disabled="inlineSaving"
                @click.stop
                @change="saveInlineEdit"
                @keydown.esc.prevent="cancelInlineEdit"
                @blur="saveInlineEdit"
              >
                <option value="">— не указан —</option>
                <option v-for="t in PROJECT_OBJECT_TYPES" :key="t" :value="t">{{ t }}</option>
              </select>
              <span v-else class="fw-500 text-right info-row__value">{{ project.object_type || '—' }}</span>
            </div>

            <div class="info-row info-row--editable" @click="beginInlineEdit('object_area')">
              <span class="text-muted">Площадь</span>
              <input
                v-if="editingField === 'object_area'"
                ref="inlineInputRef"
                v-model="editDraft"
                type="number"
                min="0"
                step="0.1"
                class="info-edit-input"
                :disabled="inlineSaving"
                @click.stop
                @keydown.enter.prevent="saveInlineEdit"
                @keydown.esc.prevent="cancelInlineEdit"
                @blur="saveInlineEdit"
              />
              <span v-else class="fw-500 text-right info-row__value">{{ project.object_area ? `${project.object_area} м²` : '—' }}</span>
            </div>

            <div class="separator my-2"></div>

            <div class="info-row info-row--editable" @click="beginInlineEdit('customer_id')">
              <span class="text-muted">Заказчик</span>
              <!-- CompanySmartSelect — поиск по ИНН/названию, тот же UX, что у лидов. -->
              <div
                v-if="editingField === 'customer_id'"
                class="info-edit-select"
                @click.stop
                @keydown.esc.prevent="cancelInlineEdit"
              >
                <CompanySmartSelect
                  v-model="editDraft"
                  :options="customerCompanies"
                  placeholder="Не выбран"
                  @update:modelValue="saveInlineEdit"
                />
                <button type="button" class="info-edit-cancel" title="Отмена" @click.stop="cancelInlineEdit">
                  <i class="fas fa-times"></i>
                </button>
              </div>
              <span v-else class="fw-500 text-right info-row__value">{{ getCompanyName(project.customer?.name, project.customer_id) }}</span>
            </div>

            <!--
              Статус из «Основной информации» убран — он отображается и
              переключается на верхней панели проекта (unified-header badge).
            -->

            <div class="info-row info-row--editable" @click="beginInlineEdit('total_contract_value')">
              <span class="text-muted">Договорная стоимость</span>
              <input
                v-if="editingField === 'total_contract_value'"
                ref="inlineInputRef"
                v-model="editDraft"
                type="number"
                min="0"
                step="0.01"
                class="info-edit-input"
                :disabled="inlineSaving"
                @click.stop
                @keydown.enter.prevent="saveInlineEdit"
                @keydown.esc.prevent="cancelInlineEdit"
                @blur="saveInlineEdit"
              />
              <span v-else class="fw-500 text-right info-row__value text-primary">{{ formatCurrency(contractAmount) }}</span>
            </div>

            <div class="separator my-2"></div>

            <!--
              ГИП — как «Ответственный» у лидов: одна info-row, при клике
              открывается inline-select со списком юзеров (кандидаты ≠ уже
              привязанные ГИПы), выбор моментально сохраняется на сервер
              без отдельной кнопки «Добавить». Под строкой — список уже
              привязанных ГИПов как чипы с аватарками; крестик на каждом
              удаляет ГИПа (тоже сразу с сохранением).
            -->
            <div class="info-row info-row--editable" @click="beginGipInlineEdit">
              <span class="text-muted">ГИП</span>
              <select
                v-if="editingField === '__gip_picker__'"
                ref="inlineInputRef"
                v-model="editDraft"
                class="info-edit-input"
                :disabled="gipSaving"
                @click.stop
                @change="onGipSelected"
                @keydown.esc.prevent="cancelInlineEdit"
                @blur="cancelInlineEdit"
              >
                <option value="">— добавить ГИПа —</option>
                <option v-for="u in availableGipCandidates" :key="u.id" :value="u.id">
                  {{ u.full_name || u.email || u.id }}
                </option>
              </select>
              <span v-else class="fw-500 text-right info-row__value">
                <span v-if="!gipUsers.length" class="text-muted">—</span>
                <span v-else>{{ gipUsers.length }}</span>
              </span>
            </div>
            <!-- Чипы привязанных ГИПов с аватарками + крестиком удаления. -->
            <div v-if="gipUsers.length" class="project-gip-chips">
              <span
                v-for="user in gipUsers"
                :key="user.id"
                class="project-gip-chip"
              >
                <UiAvatar
                  :src="gipAvatarSrc(user)"
                  :name="user.full_name || user.email || '?'"
                  size="xs"
                />
                <span class="project-gip-chip__name">{{ user.full_name || user.email || '—' }}</span>
                <button
                  type="button"
                  class="project-gip-chip__remove"
                  title="Убрать"
                  :disabled="gipSaving"
                  @click.stop="removeGipInline(user.id)"
                >
                  <i class="fas fa-times"></i>
                </button>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT: Финансовый виджет + История событий (timeline) -->
      <div class="dashboard-right card p-0 d-flex flex-column h-100 overflow-hidden">
        <div v-if="hasSectionAccess('contracts')" class="project-money-bar px-4 pt-4 pb-3">
          <div class="project-money-grid">
            <div class="project-money-cell">
              <div class="project-money-label">Всего</div>
              <div class="project-money-value">{{ formatCurrency(contractAmount) }}</div>
            </div>
            <div class="project-money-cell">
              <div class="project-money-label">Оплачено</div>
              <div class="project-money-value text-success">{{ formatCurrency(paidAmount) }}</div>
            </div>
            <div class="project-money-cell">
              <div class="project-money-label">Не оплачено</div>
              <div class="project-money-value" :class="remainingTextClass">{{ formatCurrency(remainingAmount) }}</div>
            </div>
          </div>
          <div class="project-money-progress" :title="`Оплачено ${paymentProgressPercent.toFixed(1)}%`">
            <div
              class="project-money-progress__fill"
              :style="{ width: `${paymentProgressPercent}%` }"
            ></div>
          </div>
        </div>

        <div class="px-4 pt-2 pb-2">
          <h3 class="card-title m-0">История событий</h3>
        </div>
        <div class="flex-grow-1 overflow-auto p-2">
          <DealTimeline
            v-if="project && project.id"
            :deal-id="String(project.id)"
            :users="allUsers"
            :current-user-id="String(currentUserId || '')"
            @deal-updated="onDealTimelineUpdated"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * Обзор сделки/проекта — 1-в-1 шаблон левой+правой колонки LeadDetail
 * (вкладка «Информация»). Ключевая идея — единая «коробка»
 * `.project-overview-shell` с одной общей рамкой 12px; обе колонки внутри
 * используют общий класс `.card` без своих рамок/теней (стили снимаются
 * в ProjectDetail.vue через `.project-overview-shell .card`).
 *
 * Слева: карточка «Основная информация» с inline-редактируемыми полями
 * (title/obj_name/address/object_type/object_area/customer_id/status/
 *  total_contract_value) + блок «Привязанные ГИПы» (встроен в info-grid
 * без своих рамок).
 *
 * Справа: финансовый мини-виджет (3 цифры + плашка-прогресс) → заголовок
 * «История событий» → DealTimeline (composer Комментарий/Задача/Файл +
 * чип-фильтры + лента). Договоры вынесены в отдельную вкладку.
 */
import DealTimeline from '../../../components/projects/DealTimeline.vue'
import CompanySmartSelect from '../../../components/ui/CompanySmartSelect.vue'
import UiAvatar from '../../../components/ui/UiAvatar.vue'
import { hasSectionAccess, getActiveUser } from '../../../utils/permissions'
import { normalizeAvatarUrl } from '../../../utils/avatar'
import { computed } from 'vue'
export default {
  name: 'Overview',
  components: { DealTimeline, CompanySmartSelect, UiAvatar },
  props: { state: { type: Object, required: true } },
  setup(props) {
    const state = props.state
    const currentUserId = computed(() => {
      try { return getActiveUser()?.id || '' } catch (e) { return '' }
    })
    const onDealTimelineUpdated = () => {
      // Когда из таймлайна создаётся задача — Tasks.vue подгрузит её
      // при следующем заходе на свою вкладку.
    }
    // Sentinel field-id для inline-select "добавить ГИПа": переиспользуем
    // ту же editingField/editDraft машину, что и для прочих info-row, но
    // под уникальным маркером (чтоб не путаться с реальными полями Deal).
    const beginGipInlineEdit = () => {
      if (state.inlineSaving?.value || state.gipSaving?.value) return
      state.editingField.value = '__gip_picker__'
      state.editDraft.value = ''
    }
    const onGipSelected = async () => {
      const userId = state.editDraft.value
      // Закрываем picker сразу — async-сохранение само разрулит ошибку.
      state.editingField.value = null
      state.editDraft.value = null
      if (userId) await state.addGipInline(userId)
    }
    // ГИП-аватар: avatar_url от usersStore/сервера бывает в форме
    // /api/v1/users/avatar/... или /static/avatars/..., которую сырой
    // <img> не тянет. Приводим к каноничному /avatar-user/<id> как в
    // мессенджере/таймлайне. Иначе UiAvatar валится в инициалы.
    const gipAvatarSrc = (user) => normalizeAvatarUrl(user?.avatar_url, user?.id)
    return {
      ...state,
      hasSectionAccess,
      currentUserId,
      onDealTimelineUpdated,
      beginGipInlineEdit,
      onGipSelected,
      gipAvatarSrc,
    }
  }
}
</script>

<style scoped>
/* Чипы привязанных ГИПов: компактный пилюлевидный ряд с аватаром,
   именем и крестиком удаления. Сидит сразу под info-row "ГИП". */
.project-gip-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}
.project-gip-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 8px 3px 4px;
  border: 1px solid var(--md-sys-color-outline-variant, rgba(15, 23, 42, 0.15));
  border-radius: 999px;
  background: var(--md-sys-color-surface, #fff);
  font-size: 0.82rem;
  line-height: 1.2;
}
.project-gip-chip__name {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.project-gip-chip__remove {
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.68rem;
  padding: 0;
}
.project-gip-chip__remove:hover {
  background: rgba(198, 40, 40, 0.12);
  color: #c62828;
}
.project-gip-chip__remove:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
