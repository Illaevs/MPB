<template>
  <div class="documents-view h-100 d-flex flex-column p-2">
    <div class="d-flex justify-between align-center mb-2">
      <h2 class="m-0" style="font-weight: 600; font-size: 1.5rem;">Документация</h2>
      <button class="btn btn-sm btn-primary" @click="openCreate">
        <i class="fas fa-plus mr-1"></i> Новый документ
      </button>
    </div>

    <div class="split-view">
      <DocumentList
        :documents="documents"
        :loading="loading"
        :selected-doc="selectedDoc"
        :search="search"
        :selected-status="selectedStatus"
        :selected-type="selectedType"
        :date-from="dateFrom"
        :date-to="dateTo"
        :page="page"
        :has-next="hasNext"
        :trigger-search="triggerSearch"
        :change-filters="changeFilters"
        :clear-filters="clearFilters"
        :on-drag-start="onDragStart"
        :get-type-icon="getTypeIcon"
        :format-date="formatDate"
        @update:search="search = $event"
        @update:selectedStatus="selectedStatus = $event"
        @update:selectedType="selectedType = $event"
        @update:dateFrom="dateFrom = $event"
        @update:dateTo="dateTo = $event"
        @select-document="selectDocument"
        @delete-document="deleteDocument"
        @prev-page="prevPage"
        @next-page="nextPage"
      />

      <DocumentDetail
        :selected-doc="selectedDoc"
        :selected-doc-channels="selectedDocChannels"
        :selected-doc-relations="selectedDocRelations"
        :expanded-channel="expandedChannel"
        :channel-keys="channelKeys"
        :channel-labels="channelLabels"
        :pending-channel-files="pendingChannelFiles"
        :parent-channel-files="parentChannelFiles"
        :drag-over-channel="dragOverChannel"
        :is-drop-target="isDropTarget"
        :format-date="formatDate"
        :get-type-icon="getTypeIcon"
        :get-type-text="getTypeText"
        :get-company-name="getCompanyName"
        :get-status-class="getStatusClass"
        :get-status-text="getStatusText"
        :get-channel-icon="getChannelIcon"
        :get-channel-position="getChannelPosition"
        @edit-document="editDocument"
        @delete-document="deleteDocument"
        @toggle-channel="toggleChannel"
        @download-detail-channel-file="downloadDetailChannelFile"
        @delete-detail-channel-file="deleteDetailChannelFile"
        @handle-channel-file-drop="handleChannelFileDrop"
        @remove-pending-channel-file="removePendingChannelFile"
        @handle-detail-channel-upload="handleDetailChannelUpload"
        @save-channel-changes="saveChannelChanges"
        @drop-related-doc="onDropRelatedDoc"
        @remove-related-doc="removeRelatedDoc"
        @update:dragOverChannel="dragOverChannel = $event"
        @update:isDropTarget="isDropTarget = $event"
      />
    </div>

    <DocumentEditorModal
      :show="showModal"
      :is-editing="isEditing"
      :saving="saving"
      :document-form="documentForm"
      :channels="channels"
      :channel-keys="channelKeys"
      :channel-labels="channelLabels"
      :relations="relations"
      :relation-form="relationForm"
      :document-options="documentOptions"
      :companies="companies"
      :deals="deals"
      :get-document-title="getDocumentTitle"
      @close="closeModal"
      @save="saveDocument"
      @handle-channel-files-change="handleChannelFilesChange"
      @remove-channel-file="removeChannelFile"
      @download-channel-file="downloadChannelFile"
      @delete-uploaded-channel-file="deleteUploadedChannelFile"
      @add-relation="addRelation"
      @remove-relation="removeRelation"
    />

    <PackageEditorModal
      :show="showPackageModal"
      :is-editing="isPackageEditing"
      :saving="savingPackage"
      :package-form="packageForm"
      :package-items="packageItems"
      :selected-package-document-id="selectedPackageDocumentId"
      :document-form="documentForm"
      :relations="relations"
      :relation-form="relationForm"
      :document-options="documentOptions"
      :companies="companies"
      :deals="deals"
      :get-document-title="getDocumentTitle"
      @close="closePackageModal"
      @save="savePackage"
      @update:selectedPackageDocumentId="selectedPackageDocumentId = $event"
      @add-package-item="addPackageItem"
      @remove-package-item="removePackageItem"
      @add-relation="addRelation"
      @remove-relation="removeRelation"
    />
  </div>
</template>

<script>
import DocumentList from './documentRegistry/parts/DocumentList.vue'
import DocumentDetail from './documentRegistry/parts/DocumentDetail.vue'
import DocumentEditorModal from './documentRegistry/parts/DocumentEditorModal.vue'
import PackageEditorModal from './documentRegistry/parts/PackageEditorModal.vue'
import { useDocumentRegistryState } from './documentRegistry/composables/useDocumentRegistryState'

/**
 * DocumentRegistry view (thin shell).
 *
 * All state, fetchers and business helpers live in useDocumentRegistryState.
 * Sections are decomposed into child parts under views/documentRegistry/parts/*.
 * API calls go through api.documentRegistry.* (see services/api/documentRegistry.js).
 *
 * Router import path is unchanged: frontend/src/views/DocumentRegistry.vue.
 */
export default {
  name: 'DocumentRegistry',
  components: {
    DocumentList,
    DocumentDetail,
    DocumentEditorModal,
    PackageEditorModal
  },
  setup() {
    return useDocumentRegistryState()
  }
}
</script>

<style scoped>
/* Shell-only styles: top-level layout + split-view grid.
   Component-specific styles live with their <style scoped> in each part. */

.split-view {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 16px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

@media (max-width: 992px) {
  .split-view {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .documents-view h2 {
    font-size: 1.25rem !important;
  }

  .documents-view > .d-flex:first-child {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
