<template>
    <div
      v-if="activeTab === 'files'"
      id="panel-files"
      class="card h-100 d-flex flex-column overflow-hidden"
      role="tabpanel"
      aria-labelledby="tab-files"
    >
       <div class="deal-files-type-bar border-bottom px-3 py-2">
          <div class="deal-files-type-switcher">
             <button
               v-for="section in dealFileSections"
               :key="section.id"
               type="button"
               class="deal-files-type-chip"
               :class="{ active: activeDealFileSection === section.id }"
               @click="selectDealFileSection(section.id)"
             >
               <i class="fas" :class="[section.icon, section.iconClass]"></i>
               <span>{{ section.label }}</span>
             </button>
          </div>
       </div>
       <div class="flex-grow-1 overflow-hidden p-3">
          <div class="deal-files-explorer">
             <aside class="deal-files-tree-panel">
                <div class="deal-files-panel-head">
                   <div>
                      <div class="text-muted small text-uppercase">Структура папок</div>
                      <div class="deal-files-panel-title">{{ activeDealFileSectionMeta.label }}</div>
                   </div>
                   <div class="d-flex gap-1">
                      <button class="btn btn-xs btn-icon text-primary" @click="openCurrentDealFolderArchive" title="Скачать текущую папку">
                         <i class="fas fa-external-link-alt"></i>
                      </button>
                      <label class="btn btn-xs btn-icon m-0 text-primary cursor-pointer" title="Загрузить файлы">
                         <input type="file" multiple @change="uploadActiveDealFiles" style="display: none;" />
                         <i class="fas fa-plus"></i>
                      </label>
                   </div>
                </div>

                <div class="deal-files-tree-actions">
                   <button class="btn btn-xs btn-icon" :disabled="!activeDealFilePathStack.length" @click="goActiveDealFolderBack">
                      <i class="fas fa-arrow-left"></i>
                   </button>
                   <button class="btn btn-xs btn-outline-secondary" :disabled="!activeDealFilePathStack.length" @click="goActiveDealFolderRoot">
                      Корень
                   </button>
                </div>

                <div class="deal-files-tree-scroll">
                   <button
                     class="deal-tree-node deal-tree-node--root"
                     :class="{ active: !activeDealFilePathStack.length }"
                     @click="goActiveDealFolderRoot"
                   >
                     <i class="fas fa-folder-tree text-primary"></i>
                     <span>{{ activeDealFileSectionMeta.label }}</span>
                   </button>

                   <div v-if="activeDealFolderTreeLoading" class="text-center text-muted small py-3">
                      <i class="fas fa-spinner fa-spin"></i>
                   </div>
                   <template v-else>
                      <div v-if="activeDealFolderTreeRows.length" class="deal-tree-group-label">
                         Все папки
                      </div>
                      <div
                        v-for="node in activeDealFolderTreeRows"
                        :key="node.path"
                        class="deal-tree-row"
                        :style="{ paddingLeft: `${14 + node.depth * 18}px` }"
                      >
                         <button
                           class="deal-tree-toggle-btn"
                           :class="{ 'is-placeholder': !node.hasChildren }"
                           @click="toggleDealTreeNode(activeDealFileSection, node)"
                         >
                           <i v-if="node.hasChildren" class="fas" :class="node.isCollapsed ? 'fa-chevron-right' : 'fa-chevron-down'"></i>
                           <span v-else></span>
                         </button>
                         <button
                           class="deal-tree-node"
                           :class="{ active: getCurrentDealFolderPath(activeDealFileSection) === node.path }"
                           @click="selectDealFolderNode(activeDealFileSection, node)"
                         >
                           <i class="fas" :class="node.isCollapsed ? 'fa-folder text-warning' : 'fa-folder-open text-warning'"></i>
                           <span>{{ node.name }}</span>
                         </button>
                      </div>
                      <div v-if="!activeDealFolderTreeRows.length" class="text-muted small text-center py-3">
                         Нет вложенных папок
                      </div>
                   </template>
                   <div v-if="!activeDealFolderTreeLoading && !activeDealFolderTreeRows.length && !activeDealFolderFiles.length" class="text-muted small text-center py-3">
                      Папка пуста
                   </div>
                </div>
             </aside>

             <section class="deal-files-table-panel">
                <div class="deal-files-panel-head deal-files-panel-head--table">
                   <div>
                      <div class="text-muted small text-uppercase">Файлы</div>
                      <div class="small text-muted">{{ activeDealFileBreadcrumb }}</div>
                   </div>
                </div>

                <div class="deal-files-table-wrap">
                   <div v-if="activeDealFolderLoading" class="text-center text-muted small py-4">
                      <i class="fas fa-spinner fa-spin"></i>
                   </div>
                   <div v-else-if="!activeDealFolderFiles.length" class="text-muted small text-center py-5">
                      Нет файлов в текущей папке
                   </div>
                   <table v-else class="table table-hover m-0 deal-files-table">
                      <thead class="sticky-top bg-surface">
                         <tr>
                            <th>Имя</th>
                            <th class="text-right deal-files-size-col">Размер</th>
                            <th class="deal-files-modified-col">Изменен</th>
                            <th class="text-right deal-files-actions-col">Действия</th>
                         </tr>
                      </thead>
                      <tbody>
                         <tr v-for="item in activeDealFolderFiles" :key="item.path">
                            <td>
                               <button class="deal-file-link deal-file-link--table" @click="openDealItem(item)">
                                  <i class="fas" :class="getDealFileIcon(item)"></i>
                                  <span>{{ item.name }}</span>
                               </button>
                            </td>
                            <td class="text-right text-muted small">{{ formatDealFileSize(getDealItemSize(item)) }}</td>
                            <td class="text-muted small">{{ formatDealFileModified(getDealItemModified(item)) }}</td>
                            <td class="text-right">
                               <div class="d-flex justify-end gap-1">
                                  <button class="btn btn-xs btn-icon text-primary" @click="openDealItem(item)" title="Скачать">
                                     <i class="fas fa-download"></i>
                                  </button>
                                  <button class="btn btn-xs btn-icon text-danger" @click="deleteDealItem(activeDealFileSection, item)" title="Удалить">
                                     <i class="fas fa-trash"></i>
                                  </button>
                               </div>
                            </td>
                         </tr>
                      </tbody>
                   </table>
                </div>
             </section>
          </div>
       </div>
    </div>
</template>

<script>

export default {
  name: 'Files',
  
  props: { state: { type: Object, required: true } },
  setup(props) {
    return { ...props.state }
  }
}
</script>
