<template>
    <div
      v-if="activeTab === 'letters'"
      id="panel-letters"
      class="card h-100 d-flex flex-column overflow-hidden"
      role="tabpanel"
      aria-labelledby="tab-letters"
    >
      <div class="card-header border-bottom p-3 d-flex justify-between align-center">
        <h3 class="card-title m-0">Письма по сделке</h3>
        <button class="btn btn-sm btn-outline-primary" @click="loadDealLetters">
          <i class="fas fa-sync-alt mr-1" :class="{ 'fa-spin': dealLettersLoading }"></i> Обновить
        </button>
      </div>
      <div class="project-letters-toolbar border-bottom p-3 d-flex justify-between align-center gap-3 flex-wrap">
        <div class="d-flex gap-2 flex-wrap align-center">
          <button
            type="button"
            class="contract-pill"
            :class="{ active: dealLettersRecipientFilter === 'all' }"
            @click="dealLettersRecipientFilter = 'all'"
          >
            <span class="pill-number">Все</span>
          </button>
          <button
            v-for="recipient in dealLetterRecipients"
            :key="recipient.id"
            type="button"
            class="contract-pill"
            :class="{ active: dealLettersRecipientFilter === recipient.id }"
            @click="dealLettersRecipientFilter = recipient.id"
          >
            <span class="pill-number">{{ recipient.name }}</span>
          </button>
        </div>
        <div class="project-letters-sort">
          <label class="text-muted small mb-1 d-block">Сортировка по дате</label>
          <select v-model="dealLettersSortDir" class="form-control form-control-sm">
            <option value="desc">Позже - раньше</option>
            <option value="asc">Раньше - позже</option>
          </select>
        </div>
      </div>
      <div class="flex-grow-1 overflow-auto p-3">
        <div v-if="dealLettersLoading" class="d-flex flex-column gap-2">
          <SkeletonLoader height="58px" v-for="i in 5" :key="i" />
        </div>
        <div v-else-if="!filteredDealLetters.length" class="text-center text-muted small py-5">
          Письма по этой сделке не найдены
        </div>
        <div v-else class="project-letters-list">
          <div
            v-for="letter in filteredDealLetters"
            :key="letter.id"
            class="project-letter-row"
            @click="openOutgoingLetter(letter)"
            @keydown.enter.prevent="openOutgoingLetter(letter)"
            @keydown.space.prevent="openOutgoingLetter(letter)"
            tabindex="0"
            role="button"
          >
            <div class="project-letter-row__cell">
              <div class="project-letter-row__label">Получатель</div>
              <div class="project-letter-row__value">{{ letter.recipient_company_name || 'Без получателя' }}</div>
            </div>
            <div class="project-letter-row__cell">
              <div class="project-letter-row__label">Исх. № и дата</div>
              <div class="project-letter-row__value">{{ formatOutgoingRegistryMeta(letter) }}</div>
            </div>
            <div class="project-letter-row__cell project-letter-row__cell--subject">
              <div class="project-letter-row__label">Тема письма</div>
              <div class="project-letter-row__value">{{ letter.subject || 'Без темы' }}</div>
            </div>
            <div class="project-letter-row__cell project-letter-row__cell--file">
              <div class="project-letter-row__label">Файл письма</div>
              <button
                v-if="getLatestLetterFile(letter)"
                type="button"
                class="project-letter-file"
                @click="downloadLatestLetterFile(letter, $event)"
              >
                <i class="fas fa-file-alt"></i>
                <span>{{ getLatestLetterFile(letter).file_name || 'Файл последней версии' }}</span>
              </button>
              <span v-else class="project-letter-row__empty">Нет файла последней версии</span>
            </div>
          </div>
        </div>
      </div>
    </div>
</template>

<script>
import SkeletonLoader from '../../../components/ui/SkeletonLoader.vue'
export default {
  name: 'Letters',
  components: { SkeletonLoader },
  props: { state: { type: Object, required: true } },
  setup(props) {
    return { ...props.state }
  }
}
</script>
