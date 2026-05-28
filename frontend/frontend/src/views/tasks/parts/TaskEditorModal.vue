<template>
  <div v-if="showCreateModal" class="modal-overlay task-modal-overlay" @click.self="closeModal">
    <div class="modal-content task-modal task-sheet" :class="{ 'task-sheet--no-aside': taskSheetAsideCollapsed }" @click.stop :style="taskModalStyle">
      <div class="task-sheet__main">
        <div class="task-sheet__header">
          <div class="task-sheet__header-top">
            <div class="task-sheet__breadcrumbs">
              <span><i class="far fa-folder-open"></i> Проекты</span>
              <span>/</span>
              <span>{{ currentTaskProjectLabel }}</span>
              <span>/</span>
              <span>{{ currentTaskCode }}</span>
            </div>
            <div class="task-sheet__window-actions">
              <button type="button" class="task-sheet__icon-btn" title="Развернуть">
                <i class="fas fa-expand-alt"></i>
              </button>
              <button type="button" class="task-sheet__icon-btn" title="Действия">
                <i class="fas fa-ellipsis-h"></i>
              </button>
              <button type="button" class="task-sheet__icon-btn" title="Закрыть" @click="closeModal">
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>

          <input
            v-model="taskForm.title"
            class="task-sheet__title-input"
            :class="{ 'is-invalid': taskValidation.title }"
            type="text"
            placeholder="Название задачи *"
            required
            @input="triggerAutoDraftIfNeeded"
            @blur="validateTaskForm"
          >
          <div v-if="taskValidation.title" class="task-sheet__field-error">
            <i class="fas fa-circle-exclamation mr-1"></i>{{ taskValidation.title }}
          </div>
        </div>

        <form @submit.prevent="saveTask" class="task-sheet__form">
          <div class="task-sheet__scroll">
            <section class="task-sheet__control-strip">
              <div class="task-sheet__control-card">
                <label>Проект</label>
                <div class="task-sheet__select-wrap">
                  <i class="far fa-folder-open task-sheet__control-icon task-sheet__control-icon--slate"></i>
                  <select v-model="taskForm.deal_id" class="task-sheet__control-select">
                    <option value="">Без проекта</option>
                    <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.title }}</option>
                  </select>
                </div>
              </div>

              <div class="task-sheet__control-card">
                <label>Статус</label>
                <div class="task-sheet__select-wrap">
                  <i class="fas fa-circle task-sheet__control-icon task-sheet__control-icon--blue"></i>
                  <select v-model="taskForm.status" class="task-sheet__control-select">
                    <option value="new">Новая</option>
                    <option value="in_progress">В работе</option>
                    <option value="pending">Ожидает</option>
                    <option value="completed">Завершена</option>
                    <option value="cancelled">Отменена</option>
                    <option value="deferred">Отложена</option>
                  </select>
                </div>
              </div>

              <div class="task-sheet__control-card">
                <label>Приоритет</label>
                <div class="task-sheet__select-wrap">
                  <i class="far fa-dot-circle task-sheet__control-icon task-sheet__control-icon--orange"></i>
                  <select v-model="taskForm.priority" class="task-sheet__control-select">
                    <option value="low">Низкий</option>
                    <option value="normal">Нормальный</option>
                    <option value="high">Высокий</option>
                    <option value="urgent">Срочный</option>
                  </select>
                </div>
              </div>

              <div class="task-sheet__control-card">
                <label>Категория задачи</label>
                <div class="task-sheet__select-wrap">
                  <i class="fas fa-tag task-sheet__control-icon task-sheet__control-icon--violet"></i>
                  <select v-model="taskForm.work_category" class="task-sheet__control-select">
                    <option value="">Не указана</option>
                    <option v-for="cat in workCategories" :key="cat" :value="cat">{{ cat }}</option>
                  </select>
                </div>
              </div>

              <div class="task-sheet__control-card">
                <label>Ответственный</label>
                <div class="task-sheet__select-wrap task-sheet__select-wrap--assignee">
                  <span
                    class="task-sheet__assignee-avatar"
                    :class="{ 'task-sheet__assignee-avatar--image': !!currentTaskAvatarUrl }"
                    :style="currentTaskAvatarUrl ? null : currentTaskAvatarStyle"
                  >
                    <img
                      v-if="currentTaskAvatarUrl && !isAvatarBroken(currentTaskAvatarUrl)"
                      :src="currentTaskAvatarUrl"
                      :alt="currentTaskAssigneeDisplayName"
                      class="task-sheet__assignee-avatar-image"
                      @error="markAvatarBroken(currentTaskAvatarUrl)"
                    >
                    <span v-else>{{ getTaskAssigneeInitial(taskForm) }}</span>
                  </span>
                  <select v-model="taskForm.assigned_to_user_id" class="task-sheet__control-select">
                    <option value="">Не назначен</option>
                    <option v-for="user in users" :key="user.id" :value="user.id">{{ user.full_name }}</option>
                  </select>
                </div>
              </div>
            </section>

            <section class="task-sheet__section">
              <div class="task-sheet__section-head">
                <div class="task-sheet__section-title">
                  <span class="task-sheet__marker is-blue"></span>
                  <h5>Описание задачи</h5>
                </div>
                <div class="task-sheet__section-tools">
                  <button type="button" class="task-sheet__section-tool">B</button>
                  <button type="button" class="task-sheet__section-tool">I</button>
                  <button type="button" class="task-sheet__section-tool">U</button>
                </div>
              </div>

              <textarea
                v-model="taskForm.description"
                class="form-control task-sheet__description"
                rows="4"
                placeholder="Опишите задачу, этапы и ожидаемый результат"
              ></textarea>

              <div class="task-sheet__attachments">
                <div class="task-sheet__attachments-head">
                  <div class="task-sheet__attachments-title">
                    <i class="fas fa-paperclip"></i>
                    <span>Файлы</span>
                    <span v-if="taskAttachmentsTotalCount" class="task-sheet__attachments-count">{{ taskAttachmentsTotalCount }}</span>
                  </div>
                  <span class="task-sheet__attachments-note">Перетащите файлы сюда или выберите их вручную. Загрузка произойдет после сохранения задачи.</span>
                </div>

                <div
                  class="task-sheet__attachments-dropzone"
                  :class="{ 'is-dragover': taskAttachmentDragActive }"
                  @dragenter.prevent="onTaskAttachmentDragOver"
                  @dragover.prevent="onTaskAttachmentDragOver"
                  @dragleave.prevent="onTaskAttachmentDragLeave"
                  @drop.prevent="onTaskAttachmentDrop"
                >
                  <input
                    :ref="setAttachmentInput"
                    type="file"
                    class="d-none"
                    multiple
                    @change="onTaskAttachmentPicked"
                  >
                  <div class="task-sheet__attachments-dropzone-main">
                    <i class="fas fa-cloud-arrow-up"></i>
                    <div class="task-sheet__attachments-copy">
                      <strong>Перетащите файлы сюда</strong>
                      <span>или выберите их вручную</span>
                    </div>
                  </div>
                  <button type="button" class="btn btn-sm btn-outline-primary" @click="openTaskAttachmentPicker">
                    Выбрать файлы
                  </button>
                </div>

                <div v-if="taskAttachmentItems.length || taskPendingFiles.length" class="task-sheet__attachment-list">
                  <div
                    v-for="attachment in taskAttachmentItems"
                    :key="attachment.path || attachment.name"
                    class="task-sheet__attachment-item"
                  >
                    <button
                      type="button"
                      class="task-sheet__attachment-main"
                      @click="downloadTaskAttachment(attachment)"
                      :title="attachment.name || 'Файл'"
                    >
                      <span class="task-sheet__attachment-icon">
                        <i class="fas fa-paperclip"></i>
                      </span>
                      <span class="task-sheet__attachment-copy">
                        <strong>{{ attachment.name || 'Файл' }}</strong>
                        <small>{{ formatTaskAttachmentSize(attachment.size) || 'Прикреплен к задаче' }}</small>
                      </span>
                    </button>
                    <button
                      type="button"
                      class="task-sheet__attachment-action"
                      title="Удалить файл"
                      @click="removeTaskAttachment(attachment)"
                    >
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>

                  <div
                    v-for="(file, index) in taskPendingFiles"
                    :key="`${file.name}-${file.size}-${file.lastModified}-${index}`"
                    class="task-sheet__attachment-item task-sheet__attachment-item--pending"
                  >
                    <div class="task-sheet__attachment-main" :title="file.name">
                      <span class="task-sheet__attachment-icon">
                        <i class="fas fa-file-arrow-up"></i>
                      </span>
                      <span class="task-sheet__attachment-copy">
                        <strong>{{ file.name }}</strong>
                        <small>{{ formatTaskAttachmentSize(file.size) }} · будет загружен после сохранения</small>
                      </span>
                    </div>
                    <button
                      type="button"
                      class="task-sheet__attachment-action"
                      title="Убрать из очереди"
                      @click="removePendingTaskFile(index)"
                    >
                      <i class="fas fa-times"></i>
                    </button>
                  </div>
                </div>
              </div>
            </section>

            <section class="task-sheet__section">
              <div class="task-sheet__section-head">
                <div class="task-sheet__section-title">
                  <span class="task-sheet__marker is-violet"></span>
                  <h5>Детали и финансы</h5>
                </div>
              </div>

              <div class="task-sheet__detail-grid">
                <div class="task-sheet__detail-card">
                  <div class="task-sheet__detail-title">
                    <i class="far fa-calendar-alt"></i>
                    <span>Сроки</span>
                  </div>
                  <div class="task-sheet__detail-field">
                    <label>Дата начала</label>
                    <input type="date" v-model="taskForm.start_date" class="form-control task-sheet__mini-input" @change="validateTaskForm">
                  </div>
                  <div class="task-sheet__detail-field">
                    <label>Дата окончания</label>
                    <input type="date" v-model="taskForm.due_date" class="form-control task-sheet__mini-input" :class="{ 'is-invalid': taskValidation.date }" @change="validateTaskForm">
                  </div>
                  <div v-if="taskValidation.date" class="task-sheet__field-error">
                    <i class="fas fa-circle-exclamation mr-1"></i>{{ taskValidation.date }}
                  </div>
                </div>

                <div class="task-sheet__detail-card">
                  <div class="task-sheet__detail-title">
                    <i class="far fa-credit-card"></i>
                    <span>Бюджет</span>
                  </div>
                  <div class="task-sheet__detail-field">
                    <label>Сумма</label>
                    <div class="task-sheet__money-wrap">
                      <input type="number" v-model.number="taskForm.budget" class="form-control task-sheet__mini-input task-sheet__money-input" min="0">
                      <span class="task-sheet__money-suffix">₽</span>
                    </div>
                  </div>
                  <div class="task-sheet__detail-field">
                    <label>Категория затрат</label>
                    <CategorySmartSelect
                      v-model="taskForm.category_code"
                      :options="expenseCategories"
                      placeholder="Не указана"
                      size="sm"
                      input-class="task-sheet__mini-input"
                    />
                  </div>
                </div>

                <div class="task-sheet__detail-card">
                  <div class="task-sheet__detail-title">
                    <i class="far fa-user"></i>
                    <span>Контрагенты</span>
                  </div>
                  <div class="task-sheet__detail-field">
                    <label>Плательщик</label>
                    <CompanySmartSelect
                      v-model="taskForm.payer_id"
                      :options="companies"
                      placeholder="Найти плательщика"
                    />
                  </div>
                  <div class="task-sheet__detail-field">
                    <label>Получатель</label>
                    <CompanySmartSelect
                      v-model="taskForm.payee_id"
                      :options="companies"
                      placeholder="Найти получателя"
                    />
                  </div>
                </div>
              </div>
            </section>

            <div v-if="isEditing && taskForm.status === 'completed'" class="task-sheet__notice task-sheet__notice--info">
              <i class="fas fa-star"></i>
              <span>Задача завершена. После сохранения можно оценить исполнителя.</span>
            </div>

            <section
              v-if="isEditing && taskForm.final_budget !== null && taskForm.final_budget !== undefined"
              class="task-sheet__summary"
            >
              <div class="task-sheet__summary-item">
                <span>Коэф. оценки</span>
                <strong>{{ formatCoefficient(taskForm.rating_coefficient) }}</strong>
              </div>
              <div class="task-sheet__summary-item">
                <span>Коэф. сроков</span>
                <strong>{{ formatCoefficient(taskForm.deadline_coefficient) }}</strong>
              </div>
              <div class="task-sheet__summary-item">
                <span>Итоговый бюджет</span>
                <strong>{{ formatCurrency(taskForm.final_budget) }}</strong>
              </div>
              <div class="task-sheet__summary-item">
                <span>Штраф/бонус</span>
                <strong :class="getPenaltyClass(taskForm)">{{ getPenaltyText(taskForm) }}</strong>
              </div>
              <div v-if="canRecalculatePenalty" class="task-sheet__summary-action">
                <button
                  class="btn btn-sm btn-outline-secondary"
                  @click="recalculatePenalty"
                  :disabled="recalculatingPenalty"
                  title="Пересчитать штраф/бонус по текущим правилам и оценке. Используйте, если изменились правила или оценка после сохранения."
                >
                  <i v-if="recalculatingPenalty" class="fas fa-spinner fa-spin mr-1"></i>
                  <i v-else class="fas fa-rotate mr-1"></i>
                  Пересчитать штраф/бонус
                </button>
              </div>
            </section>
          </div>

          <div class="task-sheet__footer">
            <button type="button" class="btn btn-secondary" @click="closeModal">Отмена</button>
            <button
              type="button"
              class="btn btn-outline-secondary task-sheet__aside-toggle"
              @click="toggleTaskSheetAside"
              :title="taskSheetAsideCollapsed ? 'Показать чат и согласование' : 'Скрыть чат и согласование'"
            >
              <i class="fas" :class="taskSheetAsideCollapsed ? 'fa-comments' : 'fa-chevron-right'"></i>
              <span class="hide-md">{{ taskSheetAsideCollapsed ? 'Чат' : 'Скрыть' }}</span>
            </button>
            <button type="submit" class="btn btn-primary task-sheet__submit" :disabled="saving || taskFormHasErrors">
              <i v-if="saving" class="fas fa-spinner fa-spin mr-1"></i>
              {{ isEditing ? 'Сохранить' : 'Создать' }}
            </button>
          </div>
        </form>
      </div>

      <aside v-if="!taskSheetAsideCollapsed" class="task-sheet__chat">
        <div class="task-sheet__aside-tabs">
          <button
            type="button"
            class="task-sheet__aside-tab"
            :class="{ active: asideTab === 'approval' }"
            @click="setAsideTab('approval')"
          >
            <i class="fas fa-route mr-1"></i> Согласование
            <span v-if="taskApprovalState.activeInstance" class="task-sheet__aside-tab-dot"></span>
          </button>
          <button
            type="button"
            class="task-sheet__aside-tab"
            :class="{ active: asideTab === 'chat' }"
            @click="setAsideTab('chat')"
            :disabled="!isEditing"
            :title="!isEditing ? 'Чат станет доступен после сохранения задачи' : ''"
          >
            <i class="far fa-comment-dots mr-1"></i> Чат
          </button>
        </div>

        <div v-show="asideTab === 'approval'" class="task-sheet__aside-pane">
          <ApprovalWidget
            class="task-sheet__approval"
            entity-type="task"
            :entity-id="taskForm.id"
            :entity-label="taskForm.title"
            title="Согласование задачи"
            empty-text="Сначала сохраните задачу, затем можно будет запустить маршрут согласования."
            :allow-restart-after-approved="false"
            @state-changed="handleTaskApprovalState"
            @updated="refreshTasksAfterApproval"
          />
        </div>

        <div v-show="asideTab === 'chat'" class="task-sheet__aside-pane task-sheet__aside-pane--chat">
          <div v-if="taskChatVisible" class="task-sheet__chat-inner">
            <TaskChat
              :task-id="taskForm.id"
              :users="users"
              :can-read="taskChatVisible"
              :can-write="taskChatVisible"
            />
          </div>
          <div v-else class="task-sheet__chat-empty">
            <i class="far fa-comment-dots"></i>
            <p v-if="!isEditing">Сначала сохраните задачу, и здесь появится чат.</p>
            <p v-else>Чат недоступен по текущим правам или задача не назначена текущему пользователю.</p>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script>
import CompanySmartSelect from '../../../components/ui/CompanySmartSelect.vue'
import CategorySmartSelect from '../../../components/ui/CategorySmartSelect.vue'
import TaskChat from '../../../components/TaskChat.vue'
import ApprovalWidget from '../../../components/approvals/ApprovalWidget.vue'

export default {
  name: 'TaskEditorModal',
  components: { CompanySmartSelect, CategorySmartSelect, TaskChat, ApprovalWidget },
  props: { state: { type: Object, required: true } },
  setup(props) {
    const s = props.state
    // Bind the DOM input element back to the composable's taskAttachmentInput ref,
    // so openTaskAttachmentPicker() / reset code can click()/clear() the same element.
    const setAttachmentInput = (el) => { s.taskAttachmentInput.value = el }
    const setAsideTab = (tab) => { s.asideTab.value = tab }
    return { ...s, setAttachmentInput, setAsideTab }
  }
}
</script>
