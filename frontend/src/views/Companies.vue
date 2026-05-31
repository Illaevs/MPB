<template>
  <div class="companies-view d-flex flex-column h-100">
    <div class="list-card flex-grow-1 d-flex flex-column overflow-hidden">
      <!-- Compact single-line toolbar -->
      <div class="list-card__toolbar toolbar-card">
      <div class="toolbar-row">
        <h2 class="m-0 toolbar-title">Контрагенты</h2>

        <!-- Type filter -->
        <UiChipFilter
          :model-value="selectedType === 'all' ? '' : selectedType"
          :options="typeFilterOptions"
          placeholder="Все типы"
          empty-icon="fas fa-tag"
          :counts="typeFilterCounts"
          @update:model-value="(value) => selectType(value || 'all')"
        />

        <div class="companies-search-wrap">
          <UiInput
            v-model="search"
            size="sm"
            icon-left="fas fa-search"
            clearable
            placeholder="Поиск по ИНН, названию, контакту..."
            @update:modelValue="triggerSearch"
            @clear="search = ''; triggerSearch()"
          />
        </div>

        <UiPager
          v-model="page"
          v-model:pageSize="limit"
          class="companies-pager"
          :total="totalCount"
          :loading="loading"
          size="sm"
          @change="onPagerChange"
        />

        <div class="more-wrap">
          <UiIconButton
            icon="fas fa-ellipsis-vertical"
            label="Действия"
            size="sm"
            @click="moreMenuOpen = !moreMenuOpen"
          />
          <transition name="pop">
            <div v-if="moreMenuOpen" class="more-menu" v-click-outside="() => moreMenuOpen = false">
              <button type="button" class="more-menu-item" @click="onRefreshClick">
                <i class="fas fa-sync mr-2"></i> Обновить все по ИНН
              </button>
            </div>
          </transition>
        </div>

        <div v-if="canEditCompanies" class="quick-add" title="Быстрое создание контрагента: введите ИНН и нажмите Enter — данные подтянутся из ЕГРЮЛ">
          <i class="fas fa-bolt"></i>
          <span class="quick-add__label">Создать по ИНН</span>
          <input
            v-model="quickInn"
            type="text"
            placeholder="10 или 12 цифр + Enter"
            maxlength="12"
            :disabled="quickAdding"
            @keydown.enter.prevent="quickAddByInn"
          />
          <i v-if="quickAdding" class="fas fa-spinner fa-spin"></i>
        </div>
        <UiButton v-if="canEditCompanies" size="sm" icon-left="fas fa-plus" @click="openCreate">Создать</UiButton>
      </div>

      <div v-if="hasActiveFilters" class="filter-pills">
        <span v-if="search" class="filter-pill">
          Поиск: «{{ search }}»
          <button type="button" @click="search = ''; triggerSearch()"><i class="fas fa-times"></i></button>
        </span>
        <span v-if="selectedType !== 'all'" class="filter-pill" :class="`type-${selectedType}`">
          Тип: {{ getTypeText(selectedType) }}
          <button type="button" @click="selectType('all')"><i class="fas fa-times"></i></button>
        </span>
        <button type="button" class="filter-pill filter-pill--clear" @click="clearAllFilters">
          <i class="fas fa-rotate-left mr-1"></i> Сбросить
        </button>
      </div>
      </div>

    <!-- Table -->
    <div class="list-card__body companies-table-card flex-grow-1 overflow-hidden d-flex flex-column">
      <div v-if="loading" class="p-3 d-flex flex-column gap-2">
        <SkeletonLoader v-for="i in 8" :key="i" height="46px" />
      </div>

      <UiEmptyState
        v-else-if="!companies.length"
        icon="fas fa-building"
        :title="hasActiveFilters ? 'Ничего не найдено по фильтру' : 'Нет контрагентов'"
        :description="hasActiveFilters ? 'Сбросьте фильтры или измените поисковый запрос.' : 'Создайте первого контрагента вручную или по ИНН.'"
      >
        <template #actions>
          <div class="d-flex gap-2 mt-2">
            <UiButton v-if="hasActiveFilters" variant="secondary" size="sm" icon-left="fas fa-rotate-left" @click="clearAllFilters">
              Сбросить фильтры
            </UiButton>
            <UiButton v-if="canEditCompanies" size="sm" icon-left="fas fa-plus" @click="openCreate">
              Создать контрагента
            </UiButton>
          </div>
        </template>
      </UiEmptyState>

      <div v-else class="companies-table-scroll">
        <table class="companies-table">
          <thead>
            <tr>
              <th class="sortable-header" @click="toggleSort('inn')">
                <span>ИНН</span>
                <i v-if="sortBy === 'inn'" class="fas" :class="sortDir === 'asc' ? 'fa-arrow-up-short-wide' : 'fa-arrow-down-wide-short'"></i>
              </th>
              <th class="sortable-header" @click="toggleSort('name')">
                <span>Название</span>
                <i v-if="sortBy === 'name'" class="fas" :class="sortDir === 'asc' ? 'fa-arrow-up-short-wide' : 'fa-arrow-down-wide-short'"></i>
              </th>
              <th class="sortable-header" @click="toggleSort('type')">
                <span>Тип</span>
                <i v-if="sortBy === 'type'" class="fas" :class="sortDir === 'asc' ? 'fa-arrow-up-short-wide' : 'fa-arrow-down-wide-short'"></i>
              </th>
              <th>Контактное лицо</th>
              <th>Телефоны</th>
              <th>Email</th>
              <th>Направление работ</th>
              <th>Рейтинг</th>
              <th>Примечание</th>
              <th class="actions-th"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="company in companies"
              :key="company.id"
              class="companies-row"
              @click="editCompany(company)"
            >
              <td class="companies-inn">{{ company.inn || '—' }}</td>
              <td class="companies-name">
                <div class="companies-name__primary">
                  <i
                    v-if="company.is_default"
                    class="fas fa-star companies-name__default-star"
                    title="Основная «наша компания» — используется по умолчанию"
                  ></i>
                  {{ company.name || '—' }}
                </div>
                <span class="companies-name__secondary">{{ company.full_name || company.short_name || '' }}</span>
              </td>
              <td @click.stop>
                <div class="inline-type-wrap">
                  <button
                    type="button"
                    class="type-badge type-badge--editable"
                    :class="`type-${company.type || 'other'}`"
                    :disabled="inlineTypeBusyId === company.id"
                    @click.stop="inlineTypeOpenId = inlineTypeOpenId === company.id ? null : company.id"
                    title="Сменить тип"
                  >
                    <span class="type-badge-dot"></span>{{ getTypeText(company.type) }}
                    <i v-if="inlineTypeBusyId === company.id" class="fas fa-spinner fa-spin ml-1"></i>
                    <i v-else class="fas fa-caret-down ml-1"></i>
                  </button>
                  <transition name="pop">
                    <div
                      v-if="inlineTypeOpenId === company.id"
                      class="inline-type-menu"
                      v-click-outside="() => inlineTypeOpenId = null"
                    >
                      <button
                        v-for="opt in typeOptions"
                        :key="opt.value"
                        type="button"
                        class="inline-type-menu__item"
                        :class="[`type-${opt.value}`, { active: company.type === opt.value }]"
                        @click.stop="changeCompanyType(company, opt.value)"
                      >
                        <span class="type-badge-dot"></span>{{ opt.label }}
                        <i v-if="company.type === opt.value" class="fas fa-check ml-auto"></i>
                      </button>
                    </div>
                  </transition>
                </div>
              </td>
              <td>
                <div v-if="company.contact_person || (company.contacts && company.contacts.length)" class="contact-cell">
                  <span class="user-avatar sm" :class="`avatar-${avatarColor(primaryContactName(company))}`">
                    {{ initials(primaryContactName(company)) }}
                  </span>
                  <span class="contact-cell__name">{{ primaryContactName(company) || '—' }}</span>
                </div>
                <span v-else class="text-muted">—</span>
              </td>
              <td class="cell-list">
                <template v-if="getPhoneList(company).length">
                  <a :href="'tel:' + getPhoneList(company)[0]" class="cell-list__primary" @click.stop>
                    {{ getPhoneList(company)[0] }}
                  </a>
                  <Tooltip v-if="getPhoneList(company).length > 1" :text="getPhoneList(company).slice(1).join('\n')">
                    <span class="cell-list__more">+{{ getPhoneList(company).length - 1 }}</span>
                  </Tooltip>
                </template>
                <span v-else class="text-muted">—</span>
              </td>
              <td class="cell-list">
                <template v-if="getEmailList(company).length">
                  <a :href="'mailto:' + getEmailList(company)[0]" class="cell-list__primary" @click.stop>
                    {{ getEmailList(company)[0] }}
                  </a>
                  <Tooltip v-if="getEmailList(company).length > 1" :text="getEmailList(company).slice(1).join('\n')">
                    <span class="cell-list__more">+{{ getEmailList(company).length - 1 }}</span>
                  </Tooltip>
                </template>
                <span v-else class="text-muted">—</span>
              </td>
              <td class="cell-directions" @click.stop>
                <button type="button" class="directions-btn" @click="openDirections(company)">
                  <template v-if="directionNames(company).length">
                    <span class="directions-chip" v-for="(nm, i) in directionNames(company).slice(0, 2)" :key="i">{{ nm }}</span>
                    <span v-if="directionNames(company).length > 2" class="directions-chip directions-chip--more">
                      +{{ directionNames(company).length - 2 }}
                    </span>
                  </template>
                  <span v-else class="directions-btn__empty"><i class="fas fa-sitemap"></i> Указать</span>
                </button>
              </td>
              <td class="cell-rating" @click.stop>
                <StarRating
                  :model-value="company.rating || 0"
                  @update:model-value="setCompanyRating(company, $event)"
                />
              </td>
              <td class="cell-note" @click.stop>
                <div v-if="noteEditId === company.id" class="note-edit">
                  <textarea
                    v-model="noteDraft"
                    class="note-edit__area"
                    rows="2"
                    placeholder="Примечание..."
                    @keydown.enter.exact.prevent="saveNote(company)"
                    @keydown.esc.prevent="cancelNoteEdit"
                  ></textarea>
                  <div class="note-edit__actions">
                    <button type="button" class="note-edit__btn note-edit__btn--ok" :disabled="noteSaving" @click="saveNote(company)">
                      <i class="fas fa-check"></i>
                    </button>
                    <button type="button" class="note-edit__btn" :disabled="noteSaving" @click="cancelNoteEdit">
                      <i class="fas fa-xmark"></i>
                    </button>
                  </div>
                </div>
                <button v-else type="button" class="note-cell" :title="company.note || 'Добавить примечание'" @click="startNoteEdit(company)">
                  <span v-if="company.note" class="note-cell__text">{{ company.note }}</span>
                  <span v-else class="note-cell__empty"><i class="fas fa-pen"></i></span>
                </button>
              </td>
              <td class="row-actions text-right" @click.stop>
                <div class="row-action-menu-wrap">
                  <UiIconButton
                    icon="fas fa-ellipsis-vertical"
                    label="Действия"
                    size="sm"
                    @click.stop="toggleRowMenu(company.id)"
                  />
                  <transition name="pop">
                    <div v-if="openRowMenuId === company.id" class="more-menu" v-click-outside="() => openRowMenuId = null">
                      <button v-if="canEditCompanies" type="button" class="more-menu-item" @click="editCompany(company)">
                        <i class="fas fa-pen mr-2"></i> Редактировать
                      </button>
                      <button v-if="canEditCompanies" type="button" class="more-menu-item" @click="duplicateCompany(company)">
                        <i class="fas fa-copy mr-2"></i> Дублировать
                      </button>
                      <button type="button" class="more-menu-item" @click="openRelatedDeals(company)">
                        <i class="fas fa-link mr-2"></i> Связанные сделки
                      </button>
                      <button
                        v-if="canEditCompanies && company.type === 'internal' && !company.is_default"
                        type="button"
                        class="more-menu-item"
                        @click="promoteAsDefaultOurCompany(company)"
                      >
                        <i class="fas fa-star mr-2"></i> Сделать основной «нашей»
                      </button>
                      <div v-if="canEditCompanies" class="more-menu-divider"></div>
                      <button v-if="canEditCompanies" type="button" class="more-menu-item more-menu-item--danger" @click="deleteCompany(company)">
                        <i class="fas fa-trash mr-2"></i> Удалить
                      </button>
                    </div>
                  </transition>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    </div>
    <!-- Drawer -->
    <UiDrawer
      :model-value="showCreateModal"
      size="xl"
      :closable="false"
      :close-on-overlay="true"
      :close-on-esc="false"
      @update:modelValue="(value) => { if (!value) onDrawerBackdropClick() }"
    >
      <template #header>
        <div class="company-drawer__title">
          <div>
            <h3>{{ isEditing ? 'Редактирование контрагента' : 'Новый контрагент' }}</h3>
            <p v-if="isEditing && companyForm.id" class="text-muted small">ID: {{ companyForm.id }}</p>
          </div>
          <UiIconButton icon="fas fa-times" label="Закрыть" @click="onDrawerBackdropClick" />
        </div>
      </template>

      <form class="company-drawer" @submit.prevent="saveCompany">
        <div class="company-drawer__body">
          <section class="company-section">
            <header class="company-section__header">
              <i class="fas fa-building"></i>
              <h4>Основная информация</h4>
            </header>
            <div class="company-form-grid">
              <div class="company-field">
                <div class="input-with-suffix">
                  <UiInput
                    v-model="companyForm.inn"
                    type="text"
                    label="ИНН"
                    required
                    maxlength="12"
                    :error="innValidation.error || null"
                    hint="10 или 12 цифр"
                    @blur="lookupCompanyByInn"
                    @update:modelValue="validateInn"
                  />
                  <span v-if="innLookupBusy" class="input-suffix"><i class="fas fa-spinner fa-spin"></i></span>
                  <span v-else-if="innValidation.valid" class="input-suffix text-success"><i class="fas fa-check"></i></span>
                </div>
              </div>
              <div class="company-field company-field--wide"><UiInput v-model="companyForm.name" label="Название" required /></div>
              <div class="company-field"><UiInput v-model="companyForm.kpp" label="КПП" maxlength="20" /></div>
              <div class="company-field"><UiInput v-model="companyForm.short_name" label="Сокращённое наименование" /></div>
              <div class="company-field"><UiSelect v-model="companyForm.type" label="Тип" :options="typeOptions" /></div>
              <div class="company-field company-field--full"><UiInput v-model="companyForm.full_name" label="Полное наименование" /></div>
            </div>
          </section>

          <section class="company-section">
            <header class="company-section__header">
              <i class="fas fa-user-tie"></i>
              <h4>Руководитель (ЕИО)</h4>
              <span v-if="innLookupBusy" class="company-section__hint"><i class="fas fa-spinner fa-spin"></i> загрузка из ЕГРЮЛ…</span>
            </header>
            <div class="company-form-grid">
              <div class="company-field company-field--full"><UiInput v-model="companyForm.director_position" label="Должность" placeholder="Генеральный директор / ИП" /></div>
              <div class="company-field"><UiInput v-model="companyForm.director_last_name" label="Фамилия" /></div>
              <div class="company-field"><UiInput v-model="companyForm.director_first_name" label="Имя" /></div>
              <div class="company-field"><UiInput v-model="companyForm.director_middle_name" label="Отчество" /></div>
            </div>
          </section>

          <section class="company-section">
            <header class="company-section__header">
              <i class="fas fa-phone"></i>
              <h4>Связь и адрес</h4>
            </header>
            <div class="company-form-grid">
              <div class="company-field"><UiChipInput v-model="companyForm.phones" label="Телефоны" placeholder="+7..., Enter" link-prefix="tel:" /></div>
              <div class="company-field"><UiChipInput v-model="companyForm.emails" label="Email" placeholder="email@..., Enter" link-prefix="mailto:" /></div>
              <div class="company-field company-field--full"><UiInput v-model="companyForm.address" label="Адрес" /></div>
            </div>
          </section>

          <section class="company-section">
            <header class="company-section__header">
              <i class="fas fa-sitemap"></i>
              <h4>Направление работ, рейтинг, примечание</h4>
            </header>
            <div class="company-form-grid">
              <div class="company-field company-field--full">
                <label class="company-mini-label">Направление работ</label>
                <div class="form-directions">
                  <span
                    v-for="(nm, i) in formDirectionNames"
                    :key="i"
                    class="directions-chip"
                  >{{ nm }}</span>
                  <span v-if="!formDirectionNames.length" class="text-muted small">Не выбрано</span>
                  <UiButton
                    type="button"
                    variant="outline"
                    size="sm"
                    icon-left="fas fa-sitemap"
                    @click="openDirectionsForm"
                  >Выбрать</UiButton>
                </div>
              </div>
              <div class="company-field">
                <label class="company-mini-label">Рейтинг</label>
                <StarRating v-model="companyForm.rating" show-value />
              </div>
              <div class="company-field company-field--full">
                <label class="company-mini-label">Примечание</label>
                <textarea
                  v-model="companyForm.note"
                  class="company-note-area"
                  rows="3"
                  placeholder="Примечание о контрагенте..."
                ></textarea>
              </div>
            </div>
          </section>

          <section class="company-section">
            <header class="company-section__header company-section__header--action">
              <i class="fas fa-user-group"></i>
              <h4>Контактные лица</h4>
              <UiButton type="button" variant="outline" size="sm" icon-left="fas fa-plus" @click="addContact">Добавить</UiButton>
            </header>
            <div v-if="!companyForm.contacts.length" class="company-empty-box">
              <span class="text-muted">Не указано. Поле «контактное лицо» в карточке заполняется первым добавленным контактом.</span>
            </div>
            <div v-for="(c, idx) in companyForm.contacts" :key="`c-${idx}`" class="contact-row">
              <div class="contact-row__grid">
                <div class="company-field"><UiInput v-model="c.name" label="ФИО" /></div>
                <div class="company-field"><UiInput v-model="c.position" label="Должность" /></div>
                <div class="company-field"><UiInput v-model="c.phone" type="tel" label="Телефон" /></div>
                <div class="company-field"><UiInput v-model="c.email" type="email" label="Email" /></div>
              </div>
              <UiIconButton icon="fas fa-trash" label="Убрать" variant="danger" class="contact-row__remove" @click="removeContact(idx)" />
            </div>
          </section>

          <section class="company-section">
            <header class="company-section__header company-section__header--action">
              <i class="fas fa-credit-card"></i>
              <h4>Банковские реквизиты</h4>
              <UiButton type="button" variant="outline" size="sm" icon-left="fas fa-plus" @click="addBankAccount">Добавить</UiButton>
            </header>
            <div v-if="!companyForm.bank_accounts.length" class="company-empty-box"><span class="text-muted">Реквизиты не добавлены</span></div>
            <div v-for="(acc, idx) in companyForm.bank_accounts" :key="`b-${idx}`" class="company-bank-card">
              <div class="company-form-grid company-form-grid--bank">
                <div class="company-field">
                  <div class="input-with-suffix">
                    <UiInput v-model="acc.bik" label="БИК" @blur="lookupBankByBik(acc)" />
                    <span v-if="acc.__lookupBusy" class="input-suffix"><i class="fas fa-spinner fa-spin"></i></span>
                  </div>
                </div>
                <div class="company-field"><UiInput v-model="acc.bank_name" label="Банк" /></div>
                <div class="company-field">
                  <UiInput v-model="acc.account_rs" type="text" label="Р/с" maxlength="20" :error="rsCheck(acc).error || null" />
                  <small v-if="rsCheck(acc).valid" class="text-success"><i class="fas fa-check mr-1"></i>контрольный ключ ОК</small>
                </div>
                <div class="company-field"><UiInput v-model="acc.account_ks" type="text" label="К/с" maxlength="20" /></div>
              </div>
              <UiIconButton icon="fas fa-trash" label="Убрать" variant="danger" class="contact-row__remove" @click="removeBankAccount(idx)" />
            </div>
          </section>

          <section v-if="companyForm.type === 'subcontractor'" class="company-section">
            <header class="company-section__header">
              <i class="fas fa-star"></i>
              <h4>Рейтинг подрядчика</h4>
            </header>
            <div class="company-form-grid">
              <div class="company-field"><UiInput v-model="companyForm.rating_speed" type="number" label="Скорость (0–5)" step="0.1" min="0" max="5" /></div>
              <div class="company-field"><UiInput v-model="companyForm.rating_quality" type="number" label="Качество (0–5)" step="0.1" min="0" max="5" /></div>
            </div>
          </section>

          <section v-if="isEditing" class="company-section">
            <header class="company-section__header company-section__header--action">
              <i class="fas fa-file-alt"></i>
              <h4>Документы</h4>
              <div class="doc-upload">
                <input ref="companyDocumentFileInput" type="file" class="d-none" multiple @change="uploadCompanyDocuments" />
                <UiButton
                  type="button"
                  variant="outline"
                  size="sm"
                  icon-left="fas fa-plus"
                  :loading="companyDocumentUploading"
                  :disabled="companyDocumentUploading"
                  @click="triggerCompanyDocumentUpload"
                >
                  Файл
                </UiButton>
              </div>
            </header>

            <div v-if="companyDocumentsLoading" class="company-empty-box"><span class="text-muted">Загрузка...</span></div>
            <div v-else-if="!companyDocuments.length" class="company-empty-box"><span class="text-muted">Документов нет</span></div>
            <div v-else class="doc-list">
              <div v-for="doc in companyDocuments" :key="doc.id" class="doc-row">
                <button type="button" class="doc-row__main" @click="downloadCompanyDocument(doc)">
                  <span class="doc-icon" :class="getCompanyDocumentIconClass(doc.file_name)">
                    <i class="fas" :class="getCompanyDocumentIcon(doc.file_name)"></i>
                  </span>
                  <span class="doc-row__copy">
                    <strong>{{ doc.file_name || 'Файл' }}</strong>
                    <small class="text-muted">{{ formatFileSize(doc.file_size) }} · {{ formatDocumentDate(doc.created_at) }}</small>
                  </span>
                </button>
                <UiIconButton icon="fas fa-trash" label="Удалить" variant="danger" @click="deleteCompanyDocument(doc)" />
              </div>
            </div>
          </section>

          <div class="company-team-grid">
            <section class="company-section">
              <header class="company-section__header company-section__header--action">
                <i class="fas fa-check-circle"></i>
                <h4>Руководители</h4>
                <UiButton type="button" variant="outline" size="sm" icon-left="fas fa-user-plus" @click="openLeaderDialog">Добавить</UiButton>
              </header>
              <div v-if="!leaderUsers.length" class="company-empty-box"><span class="text-muted">Не привязаны</span></div>
              <div v-else class="company-contact-list">
                <div v-for="user in leaderUsers" :key="user.id" class="company-contact-card">
                  <span class="user-avatar sm" :class="`avatar-${avatarColor(user.full_name || user.email)}`">
                    {{ initials(user.full_name || user.email) }}
                  </span>
                  <div class="company-contact-card__body">
                    <strong>{{ user.full_name || user.email }}</strong>
                    <span class="text-muted small">{{ user.email || '—' }}</span>
                  </div>
                  <UiIconButton icon="fas fa-times" label="Убрать" variant="danger" @click="removeLeader(user.id)" />
                </div>
              </div>
            </section>

            <section class="company-section">
              <header class="company-section__header company-section__header--action">
                <i class="fas fa-users"></i>
                <h4>Сотрудники</h4>
                <UiButton type="button" variant="outline" size="sm" icon-left="fas fa-user-plus" @click="openEmployeeDialog">Добавить</UiButton>
              </header>
              <div v-if="!employeeUsers.length" class="company-empty-box"><span class="text-muted">Не привязаны</span></div>
              <div v-else class="company-contact-list">
                <div v-for="user in employeeUsers" :key="user.id" class="company-contact-card">
                  <span class="user-avatar sm" :class="`avatar-${avatarColor(user.full_name || user.email)}`">
                    {{ initials(user.full_name || user.email) }}
                  </span>
                  <div class="company-contact-card__body">
                    <strong>{{ user.full_name || user.email }}</strong>
                    <span class="text-muted small">{{ user.email || '—' }}</span>
                  </div>
                  <UiIconButton icon="fas fa-times" label="Убрать" variant="danger" @click="removeEmployee(user.id)" />
                </div>
              </div>
            </section>
          </div>
        </div>
      </form>

      <template #footer>
        <UiButton type="button" variant="secondary" size="sm" @click="onDrawerBackdropClick">Отмена</UiButton>
        <UiButton v-if="canEditCompanies" type="button" size="sm" icon-left="fas fa-check" :loading="saving" @click="saveCompany">
          {{ isEditing ? 'Сохранить' : 'Создать' }}
        </UiButton>
      </template>
    </UiDrawer>

    <Teleport to="body">
    <!-- Leader/Employee pickers (teleported so they sit above the
         body-level teleported UiDrawer instead of behind it) -->
    <div v-if="showLeaderDialog" class="picker-overlay" v-modal-close="closeLeaderDialog">
      <div class="picker" @click.stop>
        <header class="picker__head">
          <h4>Выбор руководителя</h4>
          <UiIconButton icon="fas fa-times" label="Закрыть" @click="closeLeaderDialog" />
        </header>
        <UiInput v-model="leaderSearch" class="picker__search-field" type="text" placeholder="Имя или email" />
        <div class="picker__list">
          <button v-for="user in filteredLeaderUsers" :key="user.id" type="button" class="picker__item" @click="addLeader(user)">
            <span class="user-avatar sm" :class="`avatar-${avatarColor(user.full_name || user.email)}`">
              {{ initials(user.full_name || user.email) }}
            </span>
            <div>
              <strong>{{ user.full_name || user.email }}</strong>
              <span class="text-muted small">{{ user.email || '—' }}</span>
            </div>
          </button>
          <div v-if="!filteredLeaderUsers.length" class="company-empty-box"><span class="text-muted">Ничего не найдено</span></div>
        </div>
      </div>
    </div>

    <div v-if="showEmployeeDialog" class="picker-overlay" v-modal-close="closeEmployeeDialog">
      <div class="picker" @click.stop>
        <header class="picker__head">
          <h4>Выбор сотрудника</h4>
          <UiIconButton icon="fas fa-times" label="Закрыть" @click="closeEmployeeDialog" />
        </header>
        <UiInput v-model="employeeSearch" class="picker__search-field" type="text" placeholder="Имя или email" />
        <div class="picker__list">
          <button v-for="user in filteredEmployeeUsers" :key="user.id" type="button" class="picker__item" @click="addEmployee(user)">
            <span class="user-avatar sm" :class="`avatar-${avatarColor(user.full_name || user.email)}`">
              {{ initials(user.full_name || user.email) }}
            </span>
            <div>
              <strong>{{ user.full_name || user.email }}</strong>
              <span class="text-muted small">{{ user.email || '—' }}</span>
            </div>
          </button>
          <div v-if="!filteredEmployeeUsers.length" class="company-empty-box"><span class="text-muted">Ничего не найдено</span></div>
        </div>
      </div>
    </div>

    <!-- Related deals modal -->
    <div v-if="relatedDealsOpen" class="picker-overlay" v-modal-close="closeRelatedDeals">
      <div class="picker" @click.stop style="max-width: 560px;">
        <header class="picker__head">
          <h4>Сделки контрагента <span class="text-muted small">— {{ relatedDealsCompany?.name }}</span></h4>
          <UiIconButton icon="fas fa-times" label="Закрыть" @click="closeRelatedDeals" />
        </header>
        <div v-if="relatedDealsLoading" class="p-3 d-flex flex-column gap-2">
          <SkeletonLoader v-for="i in 4" :key="i" height="42px" />
        </div>
        <div v-else-if="!relatedDeals.length" class="company-empty-box"><span class="text-muted">Сделок не найдено</span></div>
        <div v-else class="picker__list">
          <a
            v-for="deal in relatedDeals"
            :key="deal.id"
            :href="`/deals/${deal.id}`"
            class="picker__item"
            @click.prevent="goToDeal(deal)"
          >
            <span class="user-avatar sm avatar-blue"><i class="fas fa-folder-open"></i></span>
            <div>
              <strong>{{ deal.title }}</strong>
              <span class="text-muted small">{{ dealRoleLabel(deal.role) }} · {{ dealStatusText(deal.status) }}</span>
            </div>
          </a>
        </div>
      </div>
    </div>

    <div v-if="directionsCompany" class="picker-overlay" v-modal-close="closeDirections">
      <div class="picker" @click.stop style="max-width: 520px;">
        <header class="picker__head">
          <h4>Направление работ <span class="text-muted small">— {{ directionsCompany?.name }}</span></h4>
          <UiIconButton icon="fas fa-times" label="Закрыть" @click="closeDirections" />
        </header>
        <div class="directions-modal__search">
          <UiInput v-model="directionsSearch" size="sm" icon-left="fas fa-search" placeholder="Поиск раздела каталога..." />
        </div>
        <div class="directions-modal__list">
          <div v-if="!filteredCategories.length" class="company-empty-box">
            <span class="text-muted">Разделы каталога не найдены</span>
          </div>
          <label
            v-for="cat in filteredCategories"
            :key="cat.id"
            class="directions-modal__item"
            :class="{ 'is-selected': isDirectionSelected(cat.id) }"
          >
            <input
              type="checkbox"
              :checked="isDirectionSelected(cat.id)"
              @change="toggleDirection(cat.id)"
            />
            <span>{{ cat.name }}</span>
          </label>
        </div>
        <footer class="directions-modal__foot">
          <span class="text-muted small">Выбрано: {{ directionsDraft.length }}</span>
          <div class="d-flex gap-2">
            <UiButton variant="ghost" size="sm" @click="closeDirections">Отмена</UiButton>
            <UiButton variant="primary" size="sm" :loading="directionsSaving" @click="saveDirections">
              Сохранить
            </UiButton>
          </div>
        </footer>
      </div>
    </div>
    </Teleport>
  </div>
</template>

<script>
import { computed, onMounted, ref, reactive, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import {
  UiButton,
  UiChipInput,
  UiDrawer,
  UiEmptyState,
  UiIconButton,
  UiInput,
  UiPager,
  UiSelect
} from '../components/ui'
import SkeletonLoader from '../components/ui/SkeletonLoader.vue'
import Tooltip from '../components/ui/Tooltip.vue'
import UiChipFilter from '../components/ui/UiChipFilter.vue'
import StarRating from '../components/ui/StarRating.vue'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'
import { downloadFromHref } from '../utils/download'
import { canEditSection } from '../utils/permissions'
import { api } from '../services/api'
import { useCompaniesStore } from '../stores/companies'
import { useCategoriesStore } from '../stores/categories'
import { useUsersStore } from '../stores/users'

const blankCompanyForm = () => ({
  id: null,
  inn: '',
  name: '',
  short_name: '',
  full_name: '',
  kpp: '',
  type: 'customer',
  contact_person: '',
  // ЕИО / руководитель — структурно (заполняется из DaData по ИНН)
  director_position: '',
  director_last_name: '',
  director_first_name: '',
  director_middle_name: '',
  phones: [],
  emails: [],
  contacts: [],
  bank_accounts: [],
  address: '',
  rating_speed: 0,
  rating_quality: 0,
  work_directions: [],
  rating: 0,
  note: '',
  leader_user_ids: [],
  employee_user_ids: []
})

const normalizeBankAccounts = (accounts) => {
  if (!Array.isArray(accounts)) return []
  return accounts.map((account) => ({
    bank_name: account?.bank_name || '',
    account_rs: account?.account_rs || '',
    account_ks: account?.account_ks || '',
    bik: account?.bik || ''
  }))
}

const normalizeContacts = (contacts, fallbackName = '') => {
  const list = Array.isArray(contacts)
    ? contacts.map((c) => ({
        name: c?.name || '',
        position: c?.position || '',
        phone: c?.phone || '',
        email: c?.email || ''
      }))
    : []
  // Legacy single `contact_person` (shown in the list column) but no
  // structured contacts → seed one so the drawer matches the list.
  if (!list.length && fallbackName) {
    list.push({ name: fallbackName, position: '', phone: '', email: '' })
  }
  return list
}

/**
 * Контрольный ключ расчётного счёта по БИК.
 * Алгоритм ЦБ РФ: к 3 последним цифрам БИК конкатенируется 20-значный р/с,
 * каждой цифре сопоставляется вес [7,1,3]*, сумма (digit*weight) % 10 == 0.
 */
const validateAccountRs = (bik, rs) => {
  const b = String(bik || '').replace(/\D/g, '')
  const a = String(rs || '').replace(/\D/g, '')
  if (!a) return { valid: false, error: '' }
  if (a.length !== 20) return { valid: false, error: `Р/с должен содержать 20 цифр (сейчас ${a.length})` }
  if (b.length !== 9) return { valid: false, error: 'Введите БИК для проверки р/с' }
  const combined = b.slice(-3) + a  // 23 цифры
  const weights = [7, 1, 3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7, 1]
  let sum = 0
  for (let i = 0; i < 23; i += 1) sum += (Number(combined[i]) * weights[i]) % 10
  if (sum % 10 !== 0) return { valid: false, error: 'Не сходится контрольный ключ — проверьте номер' }
  return { valid: true, error: '' }
}

const clickOutside = {
  beforeMount(el, binding) {
    el._co = (e) => { if (!(el === e.target || el.contains(e.target))) binding.value(e) }
    setTimeout(() => document.addEventListener('click', el._co), 0)
  },
  unmounted(el) { document.removeEventListener('click', el._co) }
}

const TYPE_OPTIONS = [
  { value: 'customer',      short: 'Заказчики',  label: 'Заказчик' },
  { value: 'subcontractor', short: 'Субподрядчики', label: 'Субподрядчик' },
  { value: 'contractor',    short: 'Подрядчики', label: 'Подрядчик' },
  { value: 'internal',      short: 'Внутренние', label: 'Внутренний' },
  { value: 'service',       short: 'Услуги',     label: 'Оказание услуг' },
  { value: 'other',         short: 'Иные',       label: 'Иной' }
]

// Цвета для chip-фильтра по типу контрагента (семантические)
const TYPE_FILTER_COLORS = {
  customer:      '#2563eb', // синий — заказчик
  subcontractor: '#a855f7', // фиолет — субподрядчик
  contractor:    '#0ea5e9', // голубой — подрядчик
  internal:      '#22c55e', // зелёный — наши
  service:       '#f59e0b', // янтарь — услуги
  other:         '#6b7280', // серый — иные
}

export default {
  name: 'Companies',
  components: {
    SkeletonLoader,
    Tooltip,
    UiButton,
    UiChipFilter,
    UiChipInput,
    UiDrawer,
    UiEmptyState,
    UiIconButton,
    UiInput,
    UiPager,
    UiSelect,
    StarRating
  },
  directives: { 'click-outside': clickOutside },
  setup() {
    const toast = useToast()
    const { confirm } = useConfirm()
    // Write actions (create/edit/duplicate/delete) are hidden for users
    // without `companies` edit rights — they'd only get a backend 403.
    const canEditCompanies = computed(() => canEditSection('companies'))
    const router = useRouter()
    const companiesStore = useCompaniesStore()
    const usersStore = useUsersStore()

    const companies = ref([])
    const totalCount = ref(0)
    const typesSummary = ref({ total: 0, counts: {} })
    const totalAcrossTypes = computed(() => typesSummary.value.total || 0)
    const loading = ref(false)
    const saving = ref(false)
    const refreshing = ref(false)
    const search = ref('')
    const selectedType = ref('all')
    const sortBy = ref('name')
    const sortDir = ref('asc')
    const page = ref(1)
    const limit = ref(parseInt(localStorage.getItem('companies-page-size') || '20', 10) || 20)
    let searchTimer = null

    const showCreateModal = ref(false)
    const isEditing = ref(false)
    const companyForm = ref(blankCompanyForm())
    const initialFormSnapshot = ref('')

    const allUsers = ref([])
    const leaderUsers = ref([])
    const employeeUsers = ref([])
    const showLeaderDialog = ref(false)
    const showEmployeeDialog = ref(false)
    const leaderSearch = ref('')
    const employeeSearch = ref('')

    const ourCompanyOptions = ref([])
    const companyDocuments = ref([])
    const companyDocumentsLoading = ref(false)
    const companyDocumentUploading = ref(false)
    const companyDocumentFileInput = ref(null)
    // companyDocumentForm previously held our_company_id picked by the user;
    // backend now resolves it from the system default, so no input is needed.

    const innLookupBusy = ref(false)
    const innValidation = reactive({ valid: false, error: '' })
    const phoneDraft = ref('')
    const emailDraft = ref('')

    const moreMenuOpen = ref(false)
    const openRowMenuId = ref(null)
    const typeFilterOpen = ref(false)

    // Quick Add via INN
    const quickInn = ref('')
    const quickAdding = ref(false)
    const inlineTypeOpenId = ref(null)
    const inlineTypeBusyId = ref(null)

    const relatedDealsOpen = ref(false)
    const relatedDealsLoading = ref(false)
    const relatedDealsCompany = ref(null)
    const relatedDeals = ref([])

    const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / limit.value)))
    const hasNext = computed(() => page.value < totalPages.value)
    const typeOptions = TYPE_OPTIONS

    const typeFilterOptions = computed(() =>
      TYPE_OPTIONS.map((opt) => ({
        value: opt.value,
        label: opt.label,
        color: TYPE_FILTER_COLORS[opt.value] || '#6b7280',
      }))
    )

    const typeFilterCounts = computed(() => {
      const result = { total: typesSummary.value.total || 0 }
      const counts = typesSummary.value.counts || {}
      TYPE_OPTIONS.forEach((opt) => {
        result[opt.value] = counts[opt.value] || 0
      })
      return result
    })

    const hasActiveFilters = computed(() => !!(search.value || selectedType.value !== 'all'))

    const currentTypeCount = computed(() => {
      if (selectedType.value === 'all') return totalAcrossTypes.value
      return typesSummary.value.counts[selectedType.value] || 0
    })

    const selectedLeaderIds = computed(() => new Set(companyForm.value.leader_user_ids || []))
    const selectedEmployeeIds = computed(() => new Set(companyForm.value.employee_user_ids || []))

    const filterUsers = (users, value) => {
      const query = (value || '').trim().toLowerCase()
      if (!query) return users
      return users.filter((u) => `${u.full_name || ''} ${u.email || ''}`.toLowerCase().includes(query))
    }
    const filteredLeaderUsers = computed(() => filterUsers(allUsers.value.filter(u => !selectedLeaderIds.value.has(u.id)), leaderSearch.value))
    const filteredEmployeeUsers = computed(() => filterUsers(allUsers.value.filter(u => !selectedEmployeeIds.value.has(u.id)), employeeSearch.value))

    const initials = (name) => {
      if (!name) return '?'
      const parts = String(name).trim().split(/\s+/).filter(Boolean)
      if (!parts.length) return '?'
      if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
      return (parts[0][0] + parts[1][0]).toUpperCase()
    }
    const avatarColor = (name) => {
      const palette = ['blue', 'teal', 'amber', 'pink', 'purple', 'green', 'red', 'indigo']
      if (!name) return palette[0]
      let hash = 0
      const s = String(name)
      for (let i = 0; i < s.length; i += 1) hash = (hash * 31 + s.charCodeAt(i)) | 0
      return palette[Math.abs(hash) % palette.length]
    }

    const getPhoneList = (company) => {
      const list = []
      if (Array.isArray(company.phones)) list.push(...company.phones.filter(Boolean))
      if (!list.length && company.phone) list.push(company.phone)
      return list
    }
    const getEmailList = (company) => {
      const list = []
      if (Array.isArray(company.emails)) list.push(...company.emails.filter(Boolean))
      if (!list.length && company.email) list.push(company.email)
      return list
    }
    const primaryContactName = (company) => {
      if (Array.isArray(company.contacts) && company.contacts.length && company.contacts[0]?.name) return company.contacts[0].name
      return company.contact_person || ''
    }

    const getTypeText = (type) => TYPE_OPTIONS.find(o => o.value === type)?.label || 'Иной'

    // API
    const loadCompanies = async () => {
      loading.value = true
      try {
        const params = {
          skip: (page.value - 1) * limit.value,
          limit: limit.value,
          search: search.value || undefined,
          company_type: selectedType.value !== 'all' ? selectedType.value : undefined,
          sort_by: sortBy.value,
          sort_dir: sortDir.value
        }
        const [listData, countData] = await Promise.all([
          api.companies.list(params),
          api.companies.count({ search: params.search, company_type: params.company_type })
        ])
        companies.value = Array.isArray(listData) ? listData : []
        totalCount.value = countData?.count || 0
      } catch (error) {
        console.error('Companies load error:', error)
        toast.error('Не удалось загрузить контрагентов')
      } finally {
        loading.value = false
      }
    }

    const loadTypesSummary = async () => {
      try {
        const data = await api.companies.typesSummary({ search: search.value || undefined })
        typesSummary.value = data || { total: 0, counts: {} }
      } catch (e) {
        console.warn('Types summary load failed', e)
      }
    }

    const reloadAll = async () => { await Promise.all([loadCompanies(), loadTypesSummary()]) }

    const triggerSearch = () => {
      clearTimeout(searchTimer)
      searchTimer = setTimeout(() => { page.value = 1; reloadAll() }, 300)
    }

    const selectType = (value) => {
      selectedType.value = value
      page.value = 1
      loadCompanies()
    }

    const clearAllFilters = () => {
      search.value = ''
      selectedType.value = 'all'
      page.value = 1
      reloadAll()
    }

    const onLimitChange = () => {
      page.value = 1
      localStorage.setItem('companies-page-size', String(limit.value))
      loadCompanies()
    }

    const onPagerChange = () => {
      localStorage.setItem('companies-page-size', String(limit.value))
      loadCompanies()
    }

    const nextPage = () => { if (hasNext.value) { page.value += 1; loadCompanies() } }
    const prevPage = () => { if (page.value > 1) { page.value -= 1; loadCompanies() } }

    const toggleSort = (field) => {
      if (sortBy.value === field) sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
      else { sortBy.value = field; sortDir.value = 'asc' }
      page.value = 1
      loadCompanies()
    }

    // Validation
    const validateInn = () => {
      const inn = (companyForm.value.inn || '').trim()
      if (!inn) { innValidation.valid = false; innValidation.error = ''; return }
      if (!/^\d+$/.test(inn)) { innValidation.valid = false; innValidation.error = 'Только цифры'; return }
      if (inn.length !== 10 && inn.length !== 12) { innValidation.valid = false; innValidation.error = `Ожидается 10 или 12 цифр (сейчас ${inn.length})`; return }
      innValidation.valid = true
      innValidation.error = ''
    }

    // CRUD
    const openCreate = async () => {
      isEditing.value = false
      companyForm.value = blankCompanyForm()
      innValidation.valid = false
      innValidation.error = ''
      phoneDraft.value = ''
      emailDraft.value = ''
      leaderUsers.value = []
      employeeUsers.value = []
      companyDocuments.value = []
      showCreateModal.value = true
      await Promise.all([loadUsers(), loadOurCompanyOptions()])
      initialFormSnapshot.value = JSON.stringify(companyForm.value)
    }

    const editCompany = async (company) => {
      openRowMenuId.value = null
      isEditing.value = true
      companyForm.value = {
        ...blankCompanyForm(),
        ...company,
        phones: Array.isArray(company.phones) ? [...company.phones] : (company.phone ? [company.phone] : []),
        emails: Array.isArray(company.emails) ? [...company.emails] : (company.email ? [company.email] : []),
        contacts: normalizeContacts(company.contacts, company.contact_person),
        bank_accounts: normalizeBankAccounts(company.bank_accounts),
        leader_user_ids: [],
        employee_user_ids: []
      }
      validateInn()
      phoneDraft.value = ''
      emailDraft.value = ''
      leaderUsers.value = []
      employeeUsers.value = []
      companyDocuments.value = []
      showCreateModal.value = true
      await Promise.all([
        loadUsers(),
        loadOurCompanyOptions(),
        loadCompanyUsers(company.id),
        loadCompanyDocuments(company.id)
      ])
      initialFormSnapshot.value = JSON.stringify(companyForm.value)
    }

    const duplicateCompany = async (company) => {
      openRowMenuId.value = null
      isEditing.value = false
      companyForm.value = {
        ...blankCompanyForm(),
        ...company,
        id: null,
        inn: '',
        name: company.name ? `${company.name} (копия)` : '',
        phones: Array.isArray(company.phones) ? [...company.phones] : [],
        emails: Array.isArray(company.emails) ? [...company.emails] : [],
        contacts: normalizeContacts(company.contacts, company.contact_person),
        bank_accounts: normalizeBankAccounts(company.bank_accounts),
        leader_user_ids: [],
        employee_user_ids: []
      }
      validateInn()
      leaderUsers.value = []
      employeeUsers.value = []
      companyDocuments.value = []
      showCreateModal.value = true
      await Promise.all([loadUsers(), loadOurCompanyOptions()])
      initialFormSnapshot.value = JSON.stringify(companyForm.value)
    }

    const onDrawerBackdropClick = async () => {
      if (JSON.stringify(companyForm.value) === initialFormSnapshot.value) { closeModal(); return }
      const ok = await confirm({
        title: 'Закрыть без сохранения?',
        message: 'Несохранённые правки будут утеряны.',
        confirmText: 'Закрыть',
        variant: 'warning'
      })
      if (ok) closeModal()
    }

    const closeModal = () => {
      showCreateModal.value = false
      showLeaderDialog.value = false
      showEmployeeDialog.value = false
      companyForm.value = blankCompanyForm()
      companyDocuments.value = []
      leaderUsers.value = []
      employeeUsers.value = []
    }

    const makePayload = () => ({
      inn: (companyForm.value.inn || '').trim(),
      name: (companyForm.value.name || '').trim(),
      short_name: companyForm.value.short_name || null,
      full_name: companyForm.value.full_name || null,
      kpp: companyForm.value.kpp || null,
      type: companyForm.value.type || 'customer',
      contact_person: primaryContactName(companyForm.value) || null,
      phone: companyForm.value.phones[0] || null,
      email: companyForm.value.emails[0] || null,
      phones: [...companyForm.value.phones],
      emails: [...companyForm.value.emails],
      contacts: normalizeContacts(companyForm.value.contacts),
      bank_accounts: normalizeBankAccounts(companyForm.value.bank_accounts),
      address: companyForm.value.address || null,
      rating_speed: Number(companyForm.value.rating_speed || 0),
      rating_quality: Number(companyForm.value.rating_quality || 0),
      work_directions: Array.isArray(companyForm.value.work_directions) ? [...companyForm.value.work_directions] : [],
      rating: Number(companyForm.value.rating || 0),
      note: companyForm.value.note || null
    })

    const saveCompany = async () => {
      validateInn()
      if (innValidation.error) { toast.warning(innValidation.error); return }
      if (!companyForm.value.name?.trim()) { toast.warning('Введите название'); return }
      const badRs = (companyForm.value.bank_accounts || []).filter(a => a.account_rs && validateAccountRs(a.bik, a.account_rs).error)
      if (badRs.length) {
        const ok = await confirm({
          title: 'Контрольный ключ р/с не сходится',
          message: `${badRs.length} счёт(а) не проходят проверку контрольного ключа. Сохранить как есть?`,
          confirmText: 'Сохранить',
          variant: 'warning'
        })
        if (!ok) return
      }
      if (!isEditing.value) {
        const innTrim = (companyForm.value.inn || '').trim()
        if (innTrim) {
          try {
            const dup = await api.companies.findByInn(innTrim)
            const existing = (dup || []).find(c => String(c.inn || '').trim() === innTrim)
            if (existing) {
              toast.error(`Контрагент с ИНН ${innTrim} уже создан: «${existing.name}».`)
              return
            }
          } catch (e) { /* сеть подвисла — отдаём бэкенду, который тоже проверяет */ }
        }
      }
      saving.value = true
      try {
        const payload = makePayload()
        let companyId = companyForm.value.id
        if (isEditing.value && companyId) {
          await api.companies.update(companyId, payload)
        } else {
          const created = await api.companies.create(payload)
          companyId = created?.id
        }
        if (companyId) await updateCompanyUsers(companyId)
        toast.success(isEditing.value ? 'Контрагент сохранён' : 'Контрагент создан')
        closeModal()
        companiesStore.invalidate()
        await reloadAll()
      } catch (error) {
        console.error('Company save error:', error)
        toast.error(error?.response?.data?.detail || 'Не удалось сохранить контрагента')
      } finally {
        saving.value = false
      }
    }

    const deleteCompany = async (company) => {
      openRowMenuId.value = null
      const ok = await confirm({
        title: 'Удалить контрагента?',
        message: `«${company.name}» будет удалён. Действие необратимо.`,
        confirmText: 'Удалить',
        variant: 'danger'
      })
      if (!ok) return
      try {
        await api.companies.remove(company.id)
        toast.success('Контрагент удалён')
        companiesStore.removeLocal(company.id)
        companiesStore.invalidate()
        if (companies.value.length === 1 && page.value > 1) page.value -= 1
        await reloadAll()
      } catch (error) {
        console.error('Company delete error:', error)
        toast.error(error?.response?.data?.detail || 'Не удалось удалить контрагента')
      }
    }

    const quickAddByInn = async () => {
      const inn = (quickInn.value || '').trim()
      if (!inn) return
      if (!/^\d{10,12}$/.test(inn)) { toast.warning('ИНН должен содержать 10 или 12 цифр'); return }

      // Check duplicate first
      try {
        const dup = await api.companies.findByInn(inn)
        const existing = (dup || []).find(c => String(c.inn || '').trim() === inn)
        if (existing) {
          const ok = await confirm({
            title: 'Контрагент уже есть',
            message: `Найден «${existing.name}» с тем же ИНН. Открыть карточку?`,
            confirmText: 'Открыть',
            variant: 'primary'
          })
          if (ok) {
            quickInn.value = ''
            await editCompany(existing)
          }
          return
        }
      } catch (e) { /* noop — продолжаем */ }

      quickAdding.value = true
      try {
        let dadataResp = null
        try {
          dadataResp = await axios.post('/api/v1/dadata/party', { query: inn })
        } catch (e) {
          toast.error(e?.response?.data?.detail || 'DaData недоступна — заполните данные вручную.')
        }
        const data = dadataResp?.data || {}

        if (!data.short_name && !data.full_name) {
          toast.warning('ЕГРЮЛ не нашёл такой ИНН — откройте форму и заполните вручную')
          openCreate()
          await nextTick()
          companyForm.value.inn = inn
          validateInn()
          quickInn.value = ''
          return
        }

        const payload = {
          inn,
          name: data.short_name || data.full_name,
          short_name: data.short_name || null,
          full_name: data.full_name || null,
          kpp: data.kpp || null,
          type: 'customer',
          contact_person: data.ceo_name || null,
          director_position: data.director_position || null,
          director_last_name: data.director_last_name || null,
          director_first_name: data.director_first_name || null,
          director_middle_name: data.director_middle_name || null,
          address: data.address || null,
          phones: [],
          emails: [],
          contacts: [],
          bank_accounts: []
        }
        const created = await api.companies.create(payload)
        toast.success(`Создан: ${payload.name}`)
        quickInn.value = ''
        companiesStore.invalidate()
        await reloadAll()
        if (created?.id) await editCompany(created)
      } catch (error) {
        console.error('Quick add error:', error)
        toast.error(error?.response?.data?.detail || 'Не удалось создать контрагента')
      } finally {
        quickAdding.value = false
      }
    }

    const onRefreshClick = async () => {
      moreMenuOpen.value = false
      const total = typesSummary.value.total || 0
      const ok = await confirm({
        title: 'Обновить все по ИНН?',
        message: `Будут запрошены данные DaData для всех ${total} контрагентов. Это может занять несколько минут.`,
        confirmText: 'Обновить',
        variant: 'primary'
      })
      if (!ok) return
      refreshing.value = true
      try {
        const data = (await api.companies.refreshAll()) || {}
        toast.success(`Обновлено: ${data.updated || 0} · пропущено: ${data.skipped || 0} · ошибок: ${data.errors || 0}`, 6000)
        companiesStore.invalidate()
        await reloadAll()
      } catch (error) {
        console.error('Companies refresh error:', error)
        toast.error(error?.response?.data?.detail || 'Не удалось обновить контрагентов')
      } finally {
        refreshing.value = false
      }
    }

    const loadUsers = async () => {
      try {
        await usersStore.ensureLoaded()
        allUsers.value = usersStore.items
      } catch (e) { allUsers.value = [] }
    }

    const loadCompanyUsers = async (companyId) => {
      if (!companyId) return
      try {
        const data = await api.companies.getUsers(companyId)
        leaderUsers.value = data?.leaders || []
        employeeUsers.value = data?.employees || []
        companyForm.value.leader_user_ids = leaderUsers.value.map(u => u.id)
        companyForm.value.employee_user_ids = employeeUsers.value.map(u => u.id)
      } catch (e) {
        leaderUsers.value = []
        employeeUsers.value = []
      }
    }

    const updateCompanyUsers = async (companyId) => {
      await api.companies.updateUsers(companyId, {
        leader_user_ids: companyForm.value.leader_user_ids || [],
        employee_user_ids: companyForm.value.employee_user_ids || []
      })
    }

    const loadOurCompanyOptions = async () => {
      try {
        const internal = await api.companies.list({
          limit: 1000, company_type: 'internal', sort_by: 'name', sort_dir: 'asc'
        })
        ourCompanyOptions.value = Array.isArray(internal) ? internal : []
      } catch (e) { ourCompanyOptions.value = [] }
    }

    const loadCompanyDocuments = async (companyId = companyForm.value.id) => {
      if (!companyId) return
      companyDocumentsLoading.value = true
      try {
        const data = await api.companies.listDocuments(companyId)
        companyDocuments.value = Array.isArray(data) ? data : []
      } catch (e) {
        toast.error('Не удалось загрузить документы')
      } finally { companyDocumentsLoading.value = false }
    }

    const triggerCompanyDocumentUpload = () => {
      // our_company_id is resolved server-side from the default — no need to pick.
      companyDocumentFileInput.value?.click()
    }

    const uploadCompanyDocuments = async (event) => {
      const files = Array.from(event.target.files || [])
      if (!files.length || !companyForm.value.id) return
      companyDocumentUploading.value = true
      try {
        for (const file of files) {
          const formData = new FormData()
          formData.append('file', file)
          await api.companies.uploadDocument(companyForm.value.id, formData)
        }
        toast.success(files.length > 1 ? 'Документы добавлены' : 'Документ добавлен')
        await loadCompanyDocuments(companyForm.value.id)
      } catch (error) {
        toast.error(error?.response?.data?.detail || 'Не удалось загрузить документ')
      } finally {
        companyDocumentUploading.value = false
        if (event.target) event.target.value = ''
      }
    }

    const downloadCompanyDocument = async (doc) => {
      try {
        const data = await api.companies.downloadDocumentMeta(doc.id)
        await downloadFromHref(data?.href, doc.file_name || 'file', { module: 'companies', entityId: doc.id })
      } catch (e) {
        toast.error('Не удалось скачать документ')
      }
    }

    const deleteCompanyDocument = async (doc) => {
      const ok = await confirm({ title: 'Удалить файл?', message: doc.file_name, confirmText: 'Удалить', variant: 'danger' })
      if (!ok) return
      try {
        await api.companies.removeDocument(doc.id)
        toast.success('Документ удалён')
        await loadCompanyDocuments(companyForm.value.id)
      } catch (e) {
        toast.error(e?.response?.data?.detail || 'Не удалось удалить документ')
      }
    }

    // DaData
    const lookupCompanyByInn = async () => {
      validateInn()
      if (!innValidation.valid) return
      innLookupBusy.value = true
      try {
        const response = await axios.post('/api/v1/dadata/party', { query: companyForm.value.inn.trim() })
        const data = response.data || {}
        if (!data.short_name && !data.full_name) return
        companyForm.value.short_name = companyForm.value.short_name || data.short_name || ''
        companyForm.value.full_name = companyForm.value.full_name || data.full_name || ''
        companyForm.value.kpp = companyForm.value.kpp || data.kpp || ''
        companyForm.value.name = companyForm.value.name || data.short_name || data.full_name || ''
        companyForm.value.contact_person = companyForm.value.contact_person || data.ceo_name || ''
        // ЕИО структурно (#2/#3) — не затираем уже введённое вручную.
        companyForm.value.director_position = companyForm.value.director_position || data.director_position || ''
        companyForm.value.director_last_name = companyForm.value.director_last_name || data.director_last_name || ''
        companyForm.value.director_first_name = companyForm.value.director_first_name || data.director_first_name || ''
        companyForm.value.director_middle_name = companyForm.value.director_middle_name || data.director_middle_name || ''
        companyForm.value.address = companyForm.value.address || data.address || ''
        toast.success('Данные загружены из ЕГРЮЛ')
      } catch (e) {
        console.warn('Dadata party lookup failed:', e)
        toast.error(e?.response?.data?.detail || 'Не удалось получить данные из ЕГРЮЛ (DaData).')
      } finally {
        innLookupBusy.value = false
      }
    }

    const lookupBankByBik = async (account) => {
      const bik = (account?.bik || '').trim()
      if (!bik) return
      account.__lookupBusy = true
      try {
        const response = await axios.post('/api/v1/banks/lookup', { query: bik })
        const data = response.data || {}
        account.bank_name = account.bank_name || data.bank_name || ''
        account.account_ks = account.account_ks || data.correspondent_account || ''
        account.bik = data.bik || bik
      } catch (e) { /* noop */ } finally {
        account.__lookupBusy = false
      }
    }

    // Phones / Emails chip input
    const addPhone = () => {
      const v = (phoneDraft.value || '').trim()
      if (!v) { phoneDraft.value = ''; return }
      if (!companyForm.value.phones.includes(v)) companyForm.value.phones.push(v)
      phoneDraft.value = ''
    }
    const removePhone = (idx) => { companyForm.value.phones.splice(idx, 1) }
    const addEmail = () => {
      const v = (emailDraft.value || '').trim()
      if (!v) { emailDraft.value = ''; return }
      if (!companyForm.value.emails.includes(v)) companyForm.value.emails.push(v)
      emailDraft.value = ''
    }
    const removeEmail = (idx) => { companyForm.value.emails.splice(idx, 1) }

    // Contacts
    const addContact = () => { companyForm.value.contacts.push({ name: '', position: '', phone: '', email: '' }) }
    const removeContact = (idx) => { companyForm.value.contacts.splice(idx, 1) }

    // Banks
    const addBankAccount = () => { companyForm.value.bank_accounts.push({ bank_name: '', account_rs: '', account_ks: '', bik: '' }) }
    const removeBankAccount = (idx) => { companyForm.value.bank_accounts.splice(idx, 1) }
    const rsCheck = (acc) => validateAccountRs(acc?.bik, acc?.account_rs)

    // Leaders/Employees
    const openLeaderDialog = async () => { await loadUsers(); leaderSearch.value = ''; showLeaderDialog.value = true }
    const closeLeaderDialog = () => { showLeaderDialog.value = false; leaderSearch.value = '' }
    const addLeader = (user) => {
      if (!selectedLeaderIds.value.has(user.id)) {
        companyForm.value.leader_user_ids.push(user.id)
        leaderUsers.value.push(user)
      }
      closeLeaderDialog()
    }
    const removeLeader = (userId) => {
      companyForm.value.leader_user_ids = companyForm.value.leader_user_ids.filter(id => id !== userId)
      leaderUsers.value = leaderUsers.value.filter(u => u.id !== userId)
    }
    const openEmployeeDialog = async () => { await loadUsers(); employeeSearch.value = ''; showEmployeeDialog.value = true }
    const closeEmployeeDialog = () => { showEmployeeDialog.value = false; employeeSearch.value = '' }
    const addEmployee = (user) => {
      if (!selectedEmployeeIds.value.has(user.id)) {
        companyForm.value.employee_user_ids.push(user.id)
        employeeUsers.value.push(user)
      }
      closeEmployeeDialog()
    }
    const removeEmployee = (userId) => {
      companyForm.value.employee_user_ids = companyForm.value.employee_user_ids.filter(id => id !== userId)
      employeeUsers.value = employeeUsers.value.filter(u => u.id !== userId)
    }

    // Row action menu
    const toggleRowMenu = (id) => { openRowMenuId.value = openRowMenuId.value === id ? null : id }

    // Inline type change
    const changeCompanyType = async (company, newType) => {
      inlineTypeOpenId.value = null
      if (!company || !newType || company.type === newType) return
      const idx = companies.value.findIndex(c => c.id === company.id)
      if (idx < 0) return
      const previousType = companies.value[idx].type
      // optimistic
      companies.value[idx] = { ...companies.value[idx], type: newType }
      inlineTypeBusyId.value = company.id
      try {
        await api.companies.update(company.id, { ...company, type: newType })
        companiesStore.invalidate()
        toast.success(`Тип изменён: ${getTypeText(newType)}`)
        // Refresh chip counters
        await loadTypesSummary()
      } catch (error) {
        console.error('Type change error:', error)
        companies.value[idx] = { ...companies.value[idx], type: previousType }
        toast.error(error?.response?.data?.detail || 'Не удалось изменить тип')
      } finally {
        inlineTypeBusyId.value = null
      }
    }

    // Related deals
    const openRelatedDeals = async (company) => {
      openRowMenuId.value = null
      relatedDealsCompany.value = company
      relatedDeals.value = []
      relatedDealsOpen.value = true
      relatedDealsLoading.value = true
      try {
        const data = await api.companies.relatedDeals(company.id)
        relatedDeals.value = Array.isArray(data) ? data : []
      } catch (e) {
        toast.error('Не удалось загрузить связанные сделки')
      } finally { relatedDealsLoading.value = false }
    }
    const closeRelatedDeals = () => { relatedDealsOpen.value = false; relatedDealsCompany.value = null }
    const goToDeal = (deal) => {
      closeRelatedDeals()
      router.push({ path: '/deals', query: { deal_id: deal.id } })
    }

    // Promote an internal company to the system-wide default "наша компания".
    // After this, all create-endpoints (leads/deals/documents/etc.) will
    // auto-fill our_company_id with this id when the frontend doesn't send one.
    const promoteAsDefaultOurCompany = async (company) => {
      openRowMenuId.value = null
      if (!company?.id) return
      try {
        await api.companies.setDefaultOurCompany(company.id)
        toast.success(`«${company.short_name || company.name}» — теперь основная «наша»`)
        // Refresh both the row list and the cached options
        await Promise.all([loadCompanies(), loadOurCompanyOptions()])
      } catch (e) {
        toast.error(e?.response?.data?.detail || 'Не удалось назначить основной')
      }
    }
    const dealRoleLabel = (role) => ({ customer: 'Заказчик', our: 'Наша компания', contractor: 'Генподрядчик', other: '—' }[role] || '—')
    const dealStatusText = (status) => status || '—'

    // Docs
    const getCompanyDocumentIcon = (fileName = '') => {
      const ext = fileName.split('.').pop()?.toLowerCase()
      if (ext === 'pdf') return 'fa-file-pdf'
      if (['doc', 'docx'].includes(ext)) return 'fa-file-word'
      if (['xls', 'xlsx', 'csv'].includes(ext)) return 'fa-file-excel'
      if (['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(ext)) return 'fa-file-image'
      if (['zip', 'rar', '7z'].includes(ext)) return 'fa-file-archive'
      return 'fa-file'
    }
    const getCompanyDocumentIconClass = (fileName = '') => {
      const ext = fileName.split('.').pop()?.toLowerCase()
      if (ext === 'pdf') return 'doc-icon--pdf'
      if (['doc', 'docx'].includes(ext)) return 'doc-icon--word'
      if (['xls', 'xlsx', 'csv'].includes(ext)) return 'doc-icon--excel'
      if (['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(ext)) return 'doc-icon--image'
      if (['zip', 'rar', '7z'].includes(ext)) return 'doc-icon--archive'
      return 'doc-icon--file'
    }
    const formatFileSize = (size) => {
      const b = Number(size || 0)
      if (!b) return ''
      if (b < 1024) return `${b} Б`
      if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} КБ`
      return `${(b / 1024 / 1024).toFixed(1)} МБ`
    }
    const formatDocumentDate = (v) => v ? new Date(v).toLocaleDateString('ru-RU') : '—'

    /* ===== Направление работ / рейтинг / примечание ===== */
    const categoriesStore = useCategoriesStore()
    const categoryItems = computed(() => categoriesStore.items || [])

    const directionNames = (company) => {
      const ids = Array.isArray(company?.work_directions) ? company.work_directions : []
      return ids
        .map((id) => categoriesStore.getById(id)?.name)
        .filter(Boolean)
    }

    // Общий оптимистичный патч строки + PUT (inn/name обязательны в схеме —
    // поэтому шлём merged-объект, как в changeCompanyType).
    const patchCompany = async (company, patch) => {
      const idx = companies.value.findIndex((c) => c.id === company.id)
      if (idx < 0) return
      const prev = companies.value[idx]
      const next = { ...prev, ...patch }
      companies.value[idx] = next
      try {
        await api.companies.update(company.id, next)
        companiesStore.invalidate()
      } catch (e) {
        companies.value[idx] = prev
        toast.error(e?.response?.data?.detail || 'Не удалось сохранить изменение')
        throw e
      }
    }

    const setCompanyRating = (company, value) => {
      if (Number(company.rating || 0) === Number(value)) return
      patchCompany(company, { rating: Number(value) || 0 }).catch(() => {})
    }

    // --- Модалка выбора направлений (две роли: строка таблицы / форма) ---
    const directionsCompany = ref(null)
    const directionsDraft = ref([])
    const directionsSearch = ref('')
    const directionsSaving = ref(false)
    const directionsMode = ref('row') // 'row' | 'form'

    const openDirections = (company) => {
      openRowMenuId.value = null
      directionsMode.value = 'row'
      directionsCompany.value = company
      directionsDraft.value = Array.isArray(company.work_directions) ? [...company.work_directions] : []
      directionsSearch.value = ''
      categoriesStore.ensureLoaded()
    }
    const openDirectionsForm = () => {
      directionsMode.value = 'form'
      directionsCompany.value = { name: companyForm.value.name || 'Контрагент' }
      directionsDraft.value = Array.isArray(companyForm.value.work_directions)
        ? [...companyForm.value.work_directions]
        : []
      directionsSearch.value = ''
      categoriesStore.ensureLoaded()
    }
    const closeDirections = () => {
      directionsCompany.value = null
      directionsDraft.value = []
      directionsMode.value = 'row'
    }
    const formDirectionNames = computed(() =>
      (Array.isArray(companyForm.value.work_directions) ? companyForm.value.work_directions : [])
        .map((id) => categoriesStore.getById(id)?.name)
        .filter(Boolean)
    )
    const isDirectionSelected = (id) => directionsDraft.value.some((x) => String(x) === String(id))
    const toggleDirection = (id) => {
      directionsDraft.value = isDirectionSelected(id)
        ? directionsDraft.value.filter((x) => String(x) !== String(id))
        : [...directionsDraft.value, id]
    }
    const filteredCategories = computed(() => {
      const q = directionsSearch.value.trim().toLowerCase()
      const items = categoryItems.value
      if (!q) return items
      return items.filter((c) => String(c.name || '').toLowerCase().includes(q))
    })
    const saveDirections = async () => {
      if (!directionsCompany.value) return
      // Режим формы — просто кладём в companyForm, сохранится с формой.
      if (directionsMode.value === 'form') {
        companyForm.value.work_directions = [...directionsDraft.value]
        closeDirections()
        return
      }
      directionsSaving.value = true
      try {
        await patchCompany(directionsCompany.value, { work_directions: [...directionsDraft.value] })
        toast.success('Направления работ сохранены')
        closeDirections()
      } catch (e) {
        /* ошибка уже показана patchCompany */
      } finally {
        directionsSaving.value = false
      }
    }

    // --- Инлайн-примечание ---
    const noteEditId = ref(null)
    const noteDraft = ref('')
    const noteSaving = ref(false)
    const startNoteEdit = (company) => {
      noteEditId.value = company.id
      noteDraft.value = company.note || ''
    }
    const cancelNoteEdit = () => {
      noteEditId.value = null
      noteDraft.value = ''
    }
    const saveNote = async (company) => {
      const value = noteDraft.value.trim()
      if (value === (company.note || '')) { cancelNoteEdit(); return }
      noteSaving.value = true
      try {
        await patchCompany(company, { note: value || null })
        cancelNoteEdit()
      } catch (e) {
        /* ошибка уже показана */
      } finally {
        noteSaving.value = false
      }
    }

    onMounted(() => { reloadAll(); loadOurCompanyOptions(); categoriesStore.ensureLoaded() })

    return {
      companies, totalCount, typesSummary, totalAcrossTypes,
      loading, saving, refreshing,
      search, selectedType, sortBy, sortDir, page, limit, totalPages, hasNext,
      typeOptions, typeFilterOptions, typeFilterCounts, hasActiveFilters,
      moreMenuOpen, openRowMenuId, typeFilterOpen, currentTypeCount,
      // Quick add + inline type
      quickInn, quickAdding, quickAddByInn,
      inlineTypeOpenId, inlineTypeBusyId, changeCompanyType,
      // Направление работ / рейтинг / примечание
      directionNames, setCompanyRating,
      directionsCompany, directionsDraft, directionsSearch, directionsSaving,
      openDirections, openDirectionsForm, closeDirections, isDirectionSelected, toggleDirection,
      filteredCategories, saveDirections, formDirectionNames,
      noteEditId, noteDraft, noteSaving, startNoteEdit, cancelNoteEdit, saveNote,
      showCreateModal, isEditing, companyForm, innLookupBusy, innValidation,
      phoneDraft, emailDraft,
      leaderUsers, employeeUsers, showLeaderDialog, showEmployeeDialog,
      leaderSearch, employeeSearch, filteredLeaderUsers, filteredEmployeeUsers,
      ourCompanyOptions, companyDocuments, companyDocumentsLoading, companyDocumentUploading,
      companyDocumentFileInput,
      relatedDealsOpen, relatedDealsLoading, relatedDealsCompany, relatedDeals,
      // helpers
      initials, avatarColor, getPhoneList, getEmailList, primaryContactName, getTypeText,
      // actions
      loadCompanies, triggerSearch, selectType, clearAllFilters, onLimitChange, onPagerChange,
      nextPage, prevPage, toggleSort,
      canEditCompanies,
      openCreate, editCompany, duplicateCompany, onDrawerBackdropClick, closeModal, saveCompany, deleteCompany,
      onRefreshClick, toggleRowMenu,
      addContact, removeContact, addBankAccount, removeBankAccount, rsCheck,
      lookupCompanyByInn, lookupBankByBik, validateInn,
      addPhone, removePhone, addEmail, removeEmail,
      openLeaderDialog, closeLeaderDialog, addLeader, removeLeader,
      openEmployeeDialog, closeEmployeeDialog, addEmployee, removeEmployee,
      triggerCompanyDocumentUpload, uploadCompanyDocuments, downloadCompanyDocument, deleteCompanyDocument,
      openRelatedDeals, closeRelatedDeals, goToDeal, dealRoleLabel, dealStatusText,
      promoteAsDefaultOurCompany,
      getCompanyDocumentIcon, getCompanyDocumentIconClass, formatFileSize, formatDocumentDate
    }
  }
}
</script>

<style scoped>
.companies-view { padding: 12px; gap: 8px; }

/* ============================================================
   Toolbar (single-line, glass card)
   ============================================================ */
.toolbar-card {
  overflow: visible;
  position: relative;
  z-index: 50;
}
.toolbar-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: nowrap;
}

@media (max-width: 1280px) {
  .toolbar-row {
    flex-wrap: wrap;
  }
}
.toolbar-title { font-size: 1rem; font-weight: 700; white-space: nowrap; }
.counter-pill {
  background: var(--color-surface-2, #f1f5f9);
  border: 1px solid var(--color-border-subtle, rgba(0,0,0,0.06));
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  color: var(--color-text);
}

/* Search */
.companies-search-wrap {
  flex: 0 1 320px;
  min-width: 200px;
  margin-left: auto;
}

/* Pager */
.companies-pager {
  flex-shrink: 0;
}

/* More menu (dropdown) */
.more-wrap { position: relative; }
.more-menu {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  z-index: 200;
  min-width: 220px;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border-subtle);
  border-radius: 10px;
  padding: 4px;
  box-shadow: 0 12px 32px rgba(0,0,0,0.12);
}
.more-menu-item {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 7px 10px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 6px;
  font-size: 0.85rem;
  color: var(--color-text);
  text-align: left;
}
.more-menu-item:hover { background: var(--color-surface-3, rgba(0,0,0,0.05)); }
.more-menu-item--danger { color: var(--color-danger); }
.more-menu-item--danger:hover { background: var(--color-danger-soft); }
.more-menu-divider { height: 1px; background: var(--color-border-subtle); margin: 4px 0; }
.pop-enter-active, .pop-leave-active { transition: opacity 0.12s ease, transform 0.12s ease; }
.pop-enter-from, .pop-leave-to { opacity: 0; transform: translateY(-4px); }

/* Quick Add by INN */
.quick-add {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 10px;
  border: 1px solid var(--color-border-subtle);
  border-radius: 8px;
  background: var(--color-warning-soft);
  transition: border-color var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out);
}
.quick-add:focus-within {
  border-color: var(--color-warning);
  background: var(--color-warning-soft);
}
.quick-add > i:first-child { color: var(--color-warning); font-size: 0.8rem; }
.quick-add__label {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--color-warning-hover);
  padding-right: 4px;
  border-right: 1px solid var(--color-warning);
  white-space: nowrap;
}
.quick-add input {
  border: none;
  outline: none;
  background: transparent;
  font-size: 0.85rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  letter-spacing: 0.5px;
  width: 170px;
  color: inherit;
}
@media (max-width: 1280px) {
  .quick-add__label { display: none; }
  .quick-add input { width: 130px; }
}
.quick-add input::placeholder { color: var(--color-text-muted); font-family: inherit; letter-spacing: 0; }
.quick-add input:disabled { opacity: 0.5; }

/* Inline type-badge editor */
.inline-type-wrap { position: relative; display: inline-block; }
.type-badge--editable {
  border: 1px solid currentColor;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
}
.type-badge--editable:hover:not(:disabled) {
  filter: brightness(0.95);
}
.type-badge--editable .fa-caret-down { font-size: 0.6rem; opacity: 0.7; }
.inline-type-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  z-index: 100;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border-subtle);
  border-radius: 10px;
  padding: 4px;
  min-width: 200px;
  box-shadow: 0 12px 28px rgba(0,0,0,0.14);
}
.inline-type-menu__item {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 6px 10px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.82rem;
  text-align: left;
}
.inline-type-menu__item:hover { background: var(--color-surface-3, rgba(0,0,0,0.05)); }
.inline-type-menu__item.active { font-weight: 600; }
.inline-type-menu__item.type-customer      { color: var(--tag-customer-fg); }
.inline-type-menu__item.type-subcontractor { color: var(--tag-subcontractor-fg); }
.inline-type-menu__item.type-contractor    { color: var(--tag-contractor-fg); }
.inline-type-menu__item.type-internal      { color: var(--tag-internal-fg); }
.inline-type-menu__item.type-service       { color: var(--tag-service-fg); }
.inline-type-menu__item.type-other         { color: var(--tag-other-fg); }
.ml-auto { margin-left: auto; }

/* Filter pills row */
.filter-pills {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  padding-top: 6px;
  border-top: 1px solid var(--color-border-subtle, rgba(0,0,0,0.06));
  margin-top: 6px;
}
.filter-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 4px 3px 10px;
  border-radius: 999px;
  background: var(--color-surface-3, rgba(0,0,0,0.05));
  font-size: 0.78rem;
  color: var(--color-text);
}
.filter-pill button {
  border: none; background: transparent; cursor: pointer;
  color: inherit; padding: 0 6px; border-radius: 999px;
}
.filter-pill button:hover { background: rgba(0,0,0,0.08); }
.filter-pill--clear { background: transparent; color: var(--color-text-muted); padding: 3px 10px; cursor: pointer; border: none; }
.filter-pill--clear:hover { background: var(--color-surface-3, rgba(0,0,0,0.05)); }
.filter-pill.type-customer      { background: var(--tag-customer-bg);      color: var(--tag-customer-fg); }
.filter-pill.type-subcontractor { background: var(--tag-subcontractor-bg);  color: var(--tag-subcontractor-fg); }
.filter-pill.type-contractor    { background: var(--tag-contractor-bg);     color: var(--tag-contractor-fg); }
.filter-pill.type-internal      { background: var(--tag-internal-bg);       color: var(--tag-internal-fg); }
.filter-pill.type-service       { background: var(--tag-service-bg);        color: var(--tag-service-fg); }
.filter-pill.type-other         { background: var(--tag-other-bg);          color: var(--tag-other-fg); }

/* ============================================================
   Table
   ============================================================ */
.companies-table-card {
  padding: 0 !important;
}
.companies-table-scroll {
  flex: 1;
  min-height: 0;
  overflow: auto;
}
.companies-table {
  width: 100%;
  border-collapse: collapse;
}
.companies-table thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  text-align: left;
  background: var(--color-surface-2, #f1f5f9);
  color: var(--color-text-muted);
  font-weight: 700;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--color-border-subtle);
}
.sortable-header { cursor: pointer; user-select: none; }
.sortable-header:hover { color: var(--color-text); }
.sortable-header span { margin-right: 4px; }
.sortable-header i { font-size: 0.8rem; color: var(--color-primary); }

.companies-row {
  border-bottom: 1px solid var(--color-border-subtle);
  cursor: pointer;
  transition: background 0.12s ease;
}
.companies-row:hover { background: var(--color-surface-3, rgba(0,0,0,0.03)); }
.companies-row td { padding: 10px 14px; font-size: 0.85rem; vertical-align: middle; }
.companies-inn {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.82rem;
  color: var(--color-text-muted);
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0;
}

.actions-th { width: 56px; padding: 10px 8px !important; }
.row-actions { width: 56px; padding-left: 4px !important; padding-right: 8px !important; }
.companies-name__primary { font-weight: 600; color: var(--color-text); }
.companies-name__default-star {
  color: #f59e0b; /* amber-500 — выделяет основную «нашу» в общем списке */
  margin-right: 4px;
  font-size: 0.78rem;
}
.companies-name__secondary {
  display: block;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}

.contact-cell { display: inline-flex; align-items: center; gap: 8px; }
.contact-cell__name { font-size: 0.85rem; }

.cell-list { white-space: nowrap; }
.cell-list__primary {
  color: var(--color-primary);
  text-decoration: none;
}
.cell-list__primary:hover { text-decoration: underline; }
.cell-list__more {
  margin-left: 6px;
  font-size: 0.72rem;
  background: var(--color-surface-3, rgba(0,0,0,0.06));
  padding: 1px 6px;
  border-radius: 999px;
  cursor: help;
  color: var(--color-text-muted);
}

.row-actions { position: relative; white-space: nowrap; }
.row-action-menu-wrap { position: relative; display: inline-block; }
.row-action-menu-wrap .more-menu { right: 0; top: calc(100% + 2px); }

/* Type badge */
.type-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  white-space: nowrap;
  border: 1px solid transparent;
}
.type-badge-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; opacity: 0.85; }
.type-badge.type-customer      { background: var(--tag-customer-bg);      color: var(--tag-customer-fg);      border-color: var(--tag-customer-border); }
.type-badge.type-subcontractor { background: var(--tag-subcontractor-bg);  color: var(--tag-subcontractor-fg);  border-color: var(--tag-subcontractor-border); }
.type-badge.type-contractor    { background: var(--tag-contractor-bg);     color: var(--tag-contractor-fg);     border-color: var(--tag-contractor-border); }
.type-badge.type-internal      { background: var(--tag-internal-bg);       color: var(--tag-internal-fg);       border-color: var(--tag-internal-border); }
.type-badge.type-service       { background: var(--tag-service-bg);        color: var(--tag-service-fg);        border-color: var(--tag-service-border); }
.type-badge.type-other         { background: var(--tag-other-bg);          color: var(--tag-other-fg);          border-color: var(--tag-other-border); }

/* Empty state */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
  color: var(--color-text-muted);
}
.empty-state i { font-size: 2.4rem; color: var(--color-border-subtle); margin-bottom: 12px; }
.empty-state p { margin: 0 0 6px; color: var(--color-text); font-weight: 500; }

/* ============================================================
   Avatars
   ============================================================ */
.user-avatar {
  width: 28px; height: 28px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--color-text-inverse);
  flex-shrink: 0;
  background: var(--color-text-muted);
}
.user-avatar.sm { width: 24px; height: 24px; font-size: 0.62rem; }
/* Декоративные оттенки для аватаров пользователей — детерминированно
   распределяются по хэшу имени, цвета намеренно различны для узнаваемости. */
.avatar-blue   { background: #1976d2; }
.avatar-teal   { background: #00897b; }
.avatar-amber  { background: #f57c00; }
.avatar-pink   { background: #d81b60; }
.avatar-purple { background: #6a1b9a; }
.avatar-green  { background: #2e7d32; }
.avatar-red    { background: #c62828; }
.avatar-indigo { background: #3949ab; }

/* ============================================================
   Drawer
   ============================================================ */
.company-drawer-backdrop {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.4);
  z-index: 9000;
}
.company-drawer-panel {
  position: fixed;
  top: 0; right: 0; bottom: 0;
  width: min(820px, 100%);
  background: var(--color-surface, #fff);
  z-index: 9100;
  display: flex;
  flex-direction: column;
  box-shadow: -10px 0 30px rgba(0,0,0,0.2);
}
.company-drawer { display: flex; flex-direction: column; height: 100%; min-height: 0; }
.company-drawer__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border-subtle);
  background: var(--color-surface, #fafbfc);
}
.company-drawer__title { display: flex; align-items: center; gap: 12px; }
.company-drawer__title h3 { margin: 0; font-size: 1.05rem; }
.company-drawer__title p { margin: 0; }
.company-drawer__actions { display: flex; gap: 8px; }
.company-drawer__body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.company-section {
  border: 1px solid var(--color-border-subtle);
  border-radius: 12px;
  padding: 12px 14px;
  background: var(--color-surface, #fff);
}
.company-section__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.company-section__header h4 {
  margin: 0;
  font-size: 0.92rem;
  font-weight: 700;
}
.company-section__header > i { color: var(--color-primary); }
.company-section__header--action h4 { margin-right: auto; }

.company-form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 10px;
}
.company-form-grid--bank {
  display: grid;
  grid-template-columns: minmax(140px, 0.8fr) minmax(200px, 1.4fr) minmax(180px, 1.2fr) minmax(180px, 1.2fr);
  gap: 10px;
}
.company-field { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.company-field span {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  font-weight: 600;
  color: var(--color-text-muted);
}
.company-field input,
.company-field select,
.company-field textarea {
  width: 100%;
  border: 1px solid var(--color-border-subtle);
  border-radius: 8px;
  padding: 7px 10px;
  font-size: 0.88rem;
  background: var(--color-surface, #fff);
  color: var(--color-text);
}
.company-field input:focus, .company-field select:focus, .company-field textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}
.company-field--wide { grid-column: span 2; }
.company-field--full { grid-column: 1 / -1; }
.company-field .is-invalid { border-color: var(--color-danger); }
.req { color: var(--color-danger); }

.input-with-suffix {
  position: relative;
  display: flex;
  align-items: center;
}
.input-with-suffix input { padding-right: 30px; }
.input-suffix {
  position: absolute;
  right: 8px;
  pointer-events: none;
  color: var(--color-text-muted);
}
.input-suffix.text-success { color: #2e7d32; }
.text-success { color: #2e7d32; }

/* Contact rows / bank rows */
.contact-row, .company-bank-card {
  position: relative;
  padding: 10px;
  border: 1px solid var(--color-border-subtle);
  border-radius: 10px;
  margin-top: 6px;
  background: var(--color-surface, #fafbfc);
}
.contact-row__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 8px;
}
.contact-row__remove {
  position: absolute;
  top: 6px;
  right: 6px;
}

.company-empty-box {
  padding: 10px 12px;
  border: 1px dashed var(--color-border-subtle);
  border-radius: 8px;
  text-align: center;
}

/* Documents */
.doc-upload { display: flex; gap: 6px; align-items: center; }
.doc-upload__select {
  height: 32px;
  padding: 4px 8px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  font-size: var(--text-sm);
  min-width: 160px;
}
.doc-list { display: flex; flex-direction: column; gap: 6px; }
.doc-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid var(--color-border-subtle);
  border-radius: 8px;
  background: var(--color-surface, #fff);
}
.doc-row__main {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 0;
  text-align: left;
}
.doc-row__copy strong { display: block; font-size: 0.88rem; }
.doc-row__copy small { display: block; font-size: 0.72rem; }
.doc-icon {
  width: 30px; height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  background: var(--color-surface-3);
  color: var(--color-text-muted);
}
/* Иконки документов: цвета намеренно соответствуют корпоративным
   цветам форматов (Word — синий, Excel — зелёный и т. д.). */
.doc-icon--pdf { background: var(--color-danger-soft); color: var(--color-danger); }
.doc-icon--word { background: var(--color-primary-soft); color: var(--color-primary); }
.doc-icon--excel { background: var(--color-success-soft); color: var(--color-success); }
.doc-icon--image { background: var(--color-warning-soft); color: var(--color-warning); }
.doc-icon--archive { background: var(--tag-contractor-bg); color: var(--tag-contractor-fg); }

/* Team */
.company-team-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.company-contact-list { display: flex; flex-direction: column; gap: 6px; }
.company-contact-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border: 1px solid var(--color-border-subtle);
  border-radius: 8px;
  background: var(--color-surface, #fff);
}
.company-contact-card__body { flex: 1; min-width: 0; }
.company-contact-card__body strong { display: block; font-size: 0.88rem; }

/* Pickers */
.picker-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.4);
  z-index: 9300;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}
.picker {
  width: min(460px, 100%);
  background: var(--color-surface, #fff);
  border-radius: 14px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.25);
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}
.picker__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border-bottom: 1px solid var(--color-border-subtle);
}
.picker__head h4 { margin: 0; font-size: 1rem; }
.picker__search-field {
  margin: 10px 14px 0;
}
.picker__list {
  padding: 10px 14px 14px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.picker__item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border: 1px solid var(--color-border-subtle);
  border-radius: 8px;
  background: var(--color-surface, #fff);
  text-align: left;
  cursor: pointer;
  text-decoration: none;
  color: inherit;
}
.picker__item:hover {
  background: var(--color-surface-3, rgba(0,0,0,0.04));
  border-color: var(--color-primary, #1976d2);
}

/* Transitions */
.companies-backdrop-enter-active, .companies-backdrop-leave-active { transition: opacity 0.2s ease; }
.companies-backdrop-enter-from, .companies-backdrop-leave-to { opacity: 0; }
.company-drawer-enter-active, .company-drawer-leave-active { transition: transform 0.22s cubic-bezier(0.2,0.8,0.2,1); }
.company-drawer-enter-from, .company-drawer-leave-to { transform: translateX(100%); }

@media (max-width: 1100px) {
  .company-team-grid { grid-template-columns: 1fr; }
  .company-form-grid--bank { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 600px) {
  .company-form-grid--bank { grid-template-columns: 1fr; }
  .toolbar-row { gap: 6px; }
  .companies-search-wrap { flex-basis: 100%; }
}

/* ===== Направление работ / рейтинг / примечание ===== */
.cell-directions { max-width: 220px; }

.directions-btn {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  max-width: 100%;
  padding: 3px 4px;
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.directions-chip {
  display: inline-block;
  max-width: 110px;
  padding: 2px 7px;
  border-radius: var(--radius-pill, 999px);
  background: var(--color-primary-soft, #eff6ff);
  color: var(--color-primary, #2563eb);
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.directions-chip--more {
  background: var(--color-surface-3, #f1f5f9);
  color: var(--color-text-muted, #64748b);
}

.directions-btn__empty {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--color-text-subtle, #94a3b8);
}

.directions-btn:hover .directions-btn__empty {
  color: var(--color-primary, #2563eb);
}

.cell-rating { white-space: nowrap; }

.cell-note { max-width: 220px; }

.note-cell {
  width: 100%;
  max-width: 210px;
  padding: 3px 4px;
  border: none;
  background: transparent;
  cursor: text;
  text-align: left;
}

.note-cell__text {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-size: 12px;
  color: var(--color-text, #0f172a);
  line-height: 1.35;
}

.note-cell__empty {
  color: var(--color-text-subtle, #94a3b8);
  font-size: 11px;
}

.note-cell:hover .note-cell__empty {
  color: var(--color-primary, #2563eb);
}

.note-edit {
  display: flex;
  align-items: flex-start;
  gap: 4px;
}

.note-edit__area {
  flex: 1 1 auto;
  width: 100%;
  min-width: 150px;
  padding: 5px 7px;
  border: 1px solid var(--color-border-strong, #cbd5e1);
  border-radius: 6px;
  font: inherit;
  font-size: 12px;
  resize: vertical;
}

.note-edit__actions {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.note-edit__btn {
  width: 22px;
  height: 22px;
  padding: 0;
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 6px;
  background: var(--color-surface, #fff);
  color: var(--color-text-muted, #64748b);
  cursor: pointer;
  font-size: 11px;
}

.note-edit__btn--ok {
  border-color: color-mix(in srgb, var(--color-primary) 40%, transparent);
  color: var(--color-primary, #2563eb);
}

.note-edit__btn:hover { background: var(--color-surface-3, #f1f5f9); }

.directions-modal__search { padding: 10px 14px 6px; }

.directions-modal__list {
  max-height: 360px;
  overflow-y: auto;
  padding: 0 10px 6px;
}

.directions-modal__item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 8px;
  border-radius: 8px;
  font-size: 0.85rem;
  color: var(--color-text, #0f172a);
  cursor: pointer;
}

.directions-modal__item:hover { background: var(--color-surface-3, #f1f5f9); }

.directions-modal__item.is-selected {
  background: var(--color-primary-soft, #eff6ff);
  color: var(--color-primary, #2563eb);
  font-weight: 600;
}

.directions-modal__item input { cursor: pointer; }

.directions-modal__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  border-top: 1px solid var(--color-border, #e2e8f0);
}

.company-mini-label {
  display: block;
  margin-bottom: 5px;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--color-text-muted, #64748b);
}

.form-directions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.company-note-area {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--color-border-strong, #cbd5e1);
  border-radius: 8px;
  font: inherit;
  font-size: 0.85rem;
  color: var(--color-text, #0f172a);
  background: var(--color-surface, #fff);
  resize: vertical;
}

.company-note-area:focus {
  outline: none;
  border-color: var(--color-primary, #2563eb);
  box-shadow: 0 0 0 3px var(--color-primary-ring, rgba(37, 99, 235, 0.18));
}
</style>


