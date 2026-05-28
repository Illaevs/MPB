<template>
  <div v-if="queue.hasItems" class="upload-queue">
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
        <div v-if="item.status === 'uploading' || item.status === 'queued' || item.status === 'processing'" class="queue-progress">
          <div class="queue-progress-bar" :style="{ width: `${item.progress || 0}%` }"></div>
        </div>
      </div>
    </transition-group>
  </div>
</template>

<script>
import { onMounted, onBeforeUnmount } from 'vue'
import { useUploadQueueStore } from '../../stores/uploadQueue'

export default {
  name: 'UploadQueue',
  setup() {
    const queue = useUploadQueueStore()

    const uiText = {
      title: '\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0438',
      clear: '\u041e\u0447\u0438\u0441\u0442\u0438\u0442\u044c',
      unnamed: '\u0411\u0435\u0437 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u044f'
    }

    onMounted(() => {
      queue.startPolling()
    })

    onBeforeUnmount(() => {
      queue.stopPolling()
    })

    return { queue, uiText }
  }
}
</script>

<style scoped>
.upload-queue {
  position: fixed;
  right: 16px;
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

.queue-status.status-uploading,
.queue-status.status-queued,
.queue-status.status-processing {
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
}

.queue-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #0d6efd, #6ea8fe);
  transition: width 0.2s ease;
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

@media (max-width: 768px) {
  .upload-queue {
    width: calc(100% - 24px);
    left: 12px;
    right: 12px;
  }
}
</style>
