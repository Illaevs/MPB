<template>
  <div v-if="queue.hasItems" class="download-queue">
    <div class="queue-header">
      <span>{{ uiText.title }}</span>
      <button class="btn btn-sm btn-outline-secondary" @click="queue.clearFinished">{{ uiText.clear }}</button>
    </div>
    <transition-group name="queue-fade" tag="div" class="queue-list">
      <div v-for="item in queue.items" :key="item.id" class="queue-item">
        <div class="queue-main">
          <div class="queue-name" :title="item.file_name">{{ item.file_name || uiText.unnamed }}</div>
          <div class="queue-status" :class="`status-${item.status}`">
            {{ queue.statusLabel(item.status) }}
          </div>
        </div>
        <div v-if="item.error_message" class="queue-error">
          {{ item.error_message }}
        </div>
        <div
          v-if="item.status === 'preparing' || item.status === 'downloading'"
          class="queue-progress"
          :class="{ indeterminate: item.indeterminate }"
        >
          <div class="queue-progress-bar" :style="item.indeterminate ? null : { width: `${item.progress || 0}%` }"></div>
        </div>
      </div>
    </transition-group>
  </div>
</template>

<script>
import { useDownloadQueueStore } from '../../stores/downloadQueue'

export default {
  name: 'DownloadQueue',
  setup() {
    const queue = useDownloadQueueStore()

    const uiText = {
      title: 'Скачивания',
      clear: 'Очистить',
      unnamed: 'Без названия'
    }

    return { queue, uiText }
  }
}
</script>

<style scoped>
.download-queue {
  position: fixed;
  right: 352px;
  bottom: 16px;
  width: 320px;
  max-height: 60vh;
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 16px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.12);
  z-index: 1200;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.queue-header {
  padding: 10px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  background: var(--md-sys-color-surface-variant);
}

.queue-list {
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
}

.queue-item {
  background: var(--md-sys-color-surface);
  border-radius: 12px;
  padding: 8px 10px;
  border: 1px solid var(--md-sys-color-outline-variant);
}

.queue-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.queue-name {
  font-size: 0.85rem;
  font-weight: 600;
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.queue-status {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 999px;
  text-transform: uppercase;
}

.queue-status.status-preparing,
.queue-status.status-downloading {
  background: rgba(13, 110, 253, 0.12);
  color: #0d6efd;
}

.queue-status.status-done {
  background: rgba(25, 135, 84, 0.12);
  color: #198754;
}

.queue-status.status-error {
  background: rgba(220, 53, 69, 0.12);
  color: #dc3545;
}

.queue-progress {
  margin-top: 6px;
  height: 6px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.08);
  overflow: hidden;
  position: relative;
}

.queue-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #0d6efd, #6ea8fe);
  transition: width 0.2s ease;
}

.queue-progress.indeterminate .queue-progress-bar {
  width: 45%;
  animation: queue-slide 1.1s ease-in-out infinite;
}

.queue-error {
  margin-top: 4px;
  font-size: 0.75rem;
  color: #dc3545;
}

.queue-fade-enter-active,
.queue-fade-leave-active {
  transition: opacity 0.28s ease, transform 0.28s ease;
}

.queue-fade-enter-from,
.queue-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

.queue-fade-move {
  transition: transform 0.28s ease;
}

@keyframes queue-slide {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(260%); }
}

@media (max-width: 1200px) {
  .download-queue {
    right: 16px;
    bottom: 148px;
  }
}

@media (max-width: 768px) {
  .download-queue {
    width: calc(100% - 24px);
    left: 12px;
    right: 12px;
    bottom: 148px;
  }
}
</style>
