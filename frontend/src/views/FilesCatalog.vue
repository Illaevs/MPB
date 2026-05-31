<template>
  <div class="files-catalog-view">
    <!-- Header -->
    <div class="files-header">
      <div class="files-header-left">
        <div class="files-icon-wrapper">
          <i class="fas fa-hdd"></i>
        </div>
        <div>
          <div class="files-title-row">
            <h1 class="files-title">Файловый каталог</h1>
            <div v-if="storageUsage.available" class="storage-usage">
              <div class="storage-usage-bar">
                <div
                  class="storage-usage-fill"
                  :class="{ loading: storageUsage.loading }"
                  :style="{ width: storageUsage.loading ? '25%' : storageUsage.percent + '%' }"
                ></div>
              </div>
              <div class="storage-usage-text">
                <span v-if="storageUsage.loading">Загрузка...</span>
                <span v-else>{{ storageUsage.percent }}% · {{ formatBytes(storageUsage.usedBytes) }} / {{ formatBytes(storageUsage.totalBytes) }}</span>
              </div>
            </div>
          </div>
          <div class="files-breadcrumbs">
            <button 
              v-for="(crumb, idx) in breadcrumbs" 
              :key="crumb.path"
              class="breadcrumb-chip"
              :class="{ 'breadcrumb-chip--active': idx === breadcrumbs.length - 1 }"
              @click="openPath(crumb.path)"
            >
              <i v-if="idx === 0" class="fas fa-home"></i>
              <span>{{ crumb.label }}</span>
            </button>
          </div>
        </div>
      </div>
      <div class="files-header-actions">
        <button class="btn btn-outline-secondary btn-sm" @click="goBack" :disabled="!canGoBack">
          <i class="fas fa-arrow-left"></i>
          <span class="btn-text">Назад</span>
        </button>
        <button class="btn btn-outline-primary btn-sm" @click="openCreateFolder">
          <i class="fas fa-folder-plus"></i>
          <span class="btn-text">Новая папка</span>
        </button>
        <button class="btn btn-primary btn-sm" @click="triggerUpload">
          <i class="fas fa-upload"></i>
          <span class="btn-text">Загрузить</span>
        </button>
        <button class="btn btn-outline-primary btn-sm" @click="triggerFolderUpload">
          <i class="fas fa-folder-open"></i>
          <span class="btn-text">Папку</span>
        </button>
        <input ref="uploadInput" type="file" multiple class="d-none" @change="handleUpload">
        <input ref="folderInput" type="file" webkitdirectory directory mozdirectory multiple class="d-none" @change="handleFolderUpload">
      </div>
    </div>

    <!-- Toolbar -->
    <div class="files-toolbar">
      <div class="toolbar-search">
        <i class="fas fa-search"></i>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Поиск по имени..."
          @keyup.enter="applySearch"
        >
        <button v-if="searchQuery" class="search-clear" @click="clearSearch">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <div class="toolbar-filters">
        <select v-model="filterType" class="filter-select">
          <option value="all">Все файлы</option>
          <option value="folder">Папки</option>
          <option value="file">Файлы</option>
          <option value="image">Изображения</option>
          <option value="document">Документы</option>
        </select>
        <select v-model="sortBy" class="filter-select">
          <option value="name">По имени</option>
          <option value="date">По дате</option>
          <option value="size">По размеру</option>
        </select>
        <button 
          class="view-toggle" 
          :class="{ active: viewMode === 'grid' }"
          @click="viewMode = 'grid'"
          title="Сетка"
        >
          <i class="fas fa-th-large"></i>
        </button>
        <button
          class="view-toggle"
          :class="{ active: viewMode === 'list' }"
          @click="viewMode = 'list'"
          title="Список"
        >
          <i class="fas fa-list"></i>
        </button>
        <button
          class="view-toggle"
          :class="{ active: viewMode === 'tree' }"
          @click="setViewMode('tree')"
          title="Дерево"
        >
          <i class="fas fa-folder-tree"></i>
        </button>
      </div>
      <button class="btn btn-icon" @click="refresh" title="Обновить">
        <i class="fas fa-sync-alt"></i>
      </button>
    </div>

    <!-- Transfer indicator -->
    <div v-if="uploadStatus.active || downloadStatus.active" class="transfer-indicator">
      <div v-if="uploadStatus.active" class="transfer-item">
        <div class="transfer-item-header">
          <i class="fas fa-cloud-upload-alt"></i>
          <span>Загрузка</span>
          <span class="transfer-item-name">{{ uploadStatus.filename }}</span>
        </div>
        <div class="transfer-bar">
          <div class="transfer-bar-fill" :style="{ width: uploadStatus.progress + '%' }"></div>
        </div>
        <div class="transfer-meta">
          <span v-if="uploadStatus.totalFiles > 1">{{ uploadStatus.completed }}/{{ uploadStatus.totalFiles }}</span>
          <span>{{ uploadStatus.progress }}%</span>
        </div>
      </div>
      <div v-if="downloadStatus.active" class="transfer-item">
        <div class="transfer-item-header">
          <i class="fas fa-cloud-download-alt"></i>
          <span>Скачивание</span>
          <span class="transfer-item-name">{{ downloadStatus.filename }}</span>
        </div>
        <div class="transfer-bar" :class="{ indeterminate: downloadStatus.indeterminate }">
          <div class="transfer-bar-fill" :style="{ width: downloadStatus.indeterminate ? '40%' : downloadStatus.progress + '%' }"></div>
        </div>
        <div class="transfer-meta">
          <span v-if="!downloadStatus.indeterminate">{{ downloadStatus.progress }}%</span>
          <span v-else>...</span>
        </div>
      </div>
    </div>

    <!-- Search indicator -->
    <div v-if="isSearchMode" class="search-indicator">
      <i class="fas fa-filter"></i>
      Результаты поиска: "{{ searchQuery }}"
      <button @click="clearSearch"><i class="fas fa-times"></i></button>
    </div>

    <!-- Drop zone -->
    <div 
      class="files-content"
      :class="{ 'drop-active': isDragOver }"
      @dragenter.prevent="handleDragEnter"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
    >
      <!-- Loading -->
      <div v-if="loading" class="files-loading">
        <div class="spinner-large"></div>
        <span>Загрузка файлов...</span>
      </div>

      <!-- Tree View (как в документации сделки) -->
      <div v-else-if="viewMode === 'tree'" class="files-tree-explorer">
        <aside class="ftree-panel">
          <div class="ftree-panel-head">
            <i class="fas fa-folder-tree"></i>
            <span>Структура папок</span>
          </div>
          <div class="ftree-scroll">
            <button
              class="ftree-node ftree-node--root"
              :class="{ active: treeSelectedPath === treeRootPath }"
              @click="selectTreeNode({ path: treeRootPath, name: 'Каталог' })"
            >
              <i class="fas fa-hdd text-primary"></i>
              <span>Каталог</span>
            </button>
            <div v-if="treeRootLoading" class="ftree-hint"><i class="fas fa-spinner fa-spin"></i></div>
            <template v-else>
              <div
                v-for="node in treeRows"
                :key="node.path"
                class="ftree-row"
                :style="{ paddingLeft: (8 + node.depth * 16) + 'px' }"
              >
                <button class="ftree-toggle" @click="toggleTreeNode(node)">
                  <i v-if="node.loading" class="fas fa-spinner fa-spin"></i>
                  <i v-else class="fas" :class="node.expanded ? 'fa-chevron-down' : 'fa-chevron-right'"></i>
                </button>
                <button
                  class="ftree-node"
                  :class="{ active: treeSelectedPath === node.path }"
                  @click="selectTreeNode(node)"
                >
                  <i class="fas" :class="node.expanded ? 'fa-folder-open text-warning' : 'fa-folder text-warning'"></i>
                  <span :title="node.name">{{ node.name }}</span>
                </button>
              </div>
              <div v-if="!treeRows.length" class="ftree-hint">Нет папок</div>
            </template>
          </div>
        </aside>

        <section class="ftree-content">
          <div class="ftree-content-head">
            <div class="ftree-content-path" :title="displayCurrentPath">
              <i class="fas fa-folder-open text-warning"></i>
              <span>{{ treeSelectedLabel }}</span>
            </div>
            <div class="ftree-content-actions">
              <label class="btn btn-icon" title="Загрузить в эту папку">
                <input type="file" multiple @change="handleUpload" style="display: none;" />
                <i class="fas fa-upload"></i>
              </label>
              <button class="btn btn-icon" @click="openCreateFolder" title="Новая папка">
                <i class="fas fa-folder-plus"></i>
              </button>
            </div>
          </div>
          <div class="ftree-content-body">
            <div v-if="treeContentLoading" class="ftree-hint"><i class="fas fa-spinner fa-spin"></i></div>
            <div v-else-if="!treeContentSorted.length" class="ftree-hint">Папка пуста</div>
            <table v-else class="ftree-table">
              <thead>
                <tr>
                  <th>Название</th>
                  <th class="ftree-col-size">Размер</th>
                  <th class="ftree-col-date">Изменён</th>
                  <th class="ftree-col-actions"></th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="item in treeContentSorted"
                  :key="item.path"
                  :class="{ 'is-folder': item.type === 'folder' }"
                  @click="item.type === 'folder' ? selectTreeNode(item) : null"
                  @dblclick="openItem(item)"
                >
                  <td class="ftree-td-name">
                    <span class="ftree-name-inner">
                      <i class="fas" :class="[getItemIcon(item), item.type === 'folder' ? 'text-warning' : 'text-muted']"></i>
                      <span :title="item.name">{{ item.name }}</span>
                    </span>
                  </td>
                  <td class="ftree-col-size">{{ item.type === 'file' ? formatBytes(item.size) : '—' }}</td>
                  <td class="ftree-col-date">{{ formatDateTime(item.modified) }}</td>
                  <td class="ftree-col-actions">
                    <button @click.stop="downloadItem(item)" :title="item.type === 'folder' ? 'Скачать архив' : 'Скачать'">
                      <i class="fas" :class="item.type === 'folder' ? 'fa-file-archive' : 'fa-download'"></i>
                    </button>
                    <button v-if="item.type === 'folder'" @click.stop="openPermissions(item)" title="Права доступа">
                      <i class="fas fa-lock"></i>
                    </button>
                    <button @click.stop="openRename(item)" title="Переименовать">
                      <i class="fas fa-pen"></i>
                    </button>
                    <button @click.stop="openMove(item)" title="Переместить">
                      <i class="fas fa-arrows-alt"></i>
                    </button>
                    <button class="danger" @click.stop="deleteItem(item)" title="Удалить">
                      <i class="fas fa-trash"></i>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <!-- Empty state -->
      <div v-else-if="!sortedItems.length" class="files-empty">
        <div class="empty-icon">
          <i class="fas fa-folder-open"></i>
        </div>
        <h3>Папка пуста</h3>
        <p>Перетащите файлы сюда или нажмите "Загрузить"</p>
        <button class="btn btn-primary" @click="triggerUpload">
          <i class="fas fa-upload mr-2"></i>
          Загрузить файлы
        </button>
      </div>

      <!-- Grid View -->
      <div v-else-if="viewMode === 'grid'" class="files-grid">
        <div 
          v-for="item in sortedItems" 
          :key="item.path"
          class="file-card"
          @click="openFolder(item)"
          @dblclick="openItem(item)"
        >
          <div class="file-card-icon" :class="getIconClass(item)">
            <i class="fas" :class="getItemIcon(item)"></i>
          </div>
          <div class="file-card-info">
            <div class="file-card-name" :title="item.name">{{ item.name }}</div>
            <div class="file-card-meta">
              {{ item.type === 'file' ? formatBytes(item.size) : 'Папка' }}
            </div>
          </div>
          <div class="file-card-actions">
            <button v-if="item.type === 'file'" @click.stop="downloadItem(item)" title="Скачать">
              <i class="fas fa-download"></i>
            </button>
            <button v-if="item.type === 'folder'" @click.stop="downloadItem(item)" title="Скачать архив">
              <i class="fas fa-file-archive"></i>
            </button>
            <button v-if="item.type === 'folder'" @click.stop="openPermissions(item)" title="Права доступа">
              <i class="fas fa-lock"></i>
            </button>
            <button @click.stop="toggleMenu(item)" title="Меню">
              <i class="fas fa-ellipsis-v"></i>
            </button>
          </div>
          <!-- Context menu -->
          <div v-if="activeMenu === item.path" class="file-context-menu">
            <button @click="openItem(item)">
              <i class="fas fa-folder-open"></i> Открыть
            </button>
            <button v-if="item.type === 'file'" @click="downloadItem(item)">
              <i class="fas fa-download"></i> Скачать
            </button>
            <button v-if="item.type === 'folder'" @click="downloadItem(item)">
              <i class="fas fa-file-archive"></i> Скачать архив
            </button>
            <button @click="openRename(item)">
              <i class="fas fa-pen"></i> Переименовать
            </button>
            <button @click="openMove(item)">
              <i class="fas fa-arrows-alt"></i> Переместить
            </button>
            <button v-if="item.type === 'folder'" @click="openPermissions(item)">
              <i class="fas fa-lock"></i> Права доступа
            </button>
            <div class="menu-divider"></div>
            <button class="danger" @click="deleteItem(item)">
              <i class="fas fa-trash"></i> Удалить
            </button>
          </div>
        </div>
      </div>

      <!-- List View -->
      <div v-else class="files-list">
        <div class="list-header">
          <div class="col-name">Название</div>
          <div class="col-type">Тип</div>
          <div class="col-size">Размер</div>
          <div class="col-date">Изменён</div>
          <div class="col-actions"></div>
        </div>
        <div 
          v-for="item in sortedItems" 
          :key="item.path"
          class="list-row"
          @click="openFolder(item)"
          @dblclick="openItem(item)"
        >
          <div class="col-name">
            <div class="file-icon" :class="getIconClass(item)">
              <i class="fas" :class="getItemIcon(item)"></i>
            </div>
            <span class="file-name">{{ item.name }}</span>
          </div>
          <div class="col-type">{{ item.type === 'folder' ? 'Папка' : getFileExt(item) }}</div>
          <div class="col-size">{{ item.type === 'file' ? formatBytes(item.size) : '—' }}</div>
          <div class="col-date">{{ formatDateTime(item.modified) }}</div>
          <div class="col-actions">
            <button v-if="item.type === 'file'" @click.stop="downloadItem(item)" title="Скачать">
              <i class="fas fa-download"></i>
            </button>
            <button v-if="item.type === 'folder'" @click.stop="downloadItem(item)" title="Скачать архив">
              <i class="fas fa-file-archive"></i>
            </button>
            <button v-if="item.type === 'folder'" @click.stop="openPermissions(item)" title="Права доступа">
              <i class="fas fa-lock"></i>
            </button>
            <button @click.stop="openRename(item)" title="Переименовать">
              <i class="fas fa-pen"></i>
            </button>
            <button @click.stop="openMove(item)" title="Переместить">
              <i class="fas fa-arrows-alt"></i>
            </button>
            <button class="danger" @click.stop="deleteItem(item)" title="Удалить">
              <i class="fas fa-trash"></i>
            </button>
          </div>
        </div>
      </div>

      <!-- Drop overlay -->
      <div v-if="isDragOver" class="drop-overlay">
        <div class="drop-overlay-content">
          <i class="fas fa-cloud-upload-alt"></i>
          <span>Отпустите для загрузки</span>
        </div>
      </div>
    </div>

    <!-- Create folder modal -->
    <div v-if="showCreateModal" class="modal-overlay" v-modal-close="closeCreateFolder">
      <div class="modal-dialog" @click.stop>
        <div class="modal-header">
          <div class="modal-icon folder">
            <i class="fas fa-folder-plus"></i>
          </div>
          <h3>Новая папка</h3>
          <button class="modal-close" @click="closeCreateFolder">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <label>Название папки</label>
          <input 
            v-model="createFolderName" 
            type="text" 
            class="form-input"
            placeholder="Введите название"
            @keyup.enter="createFolder"
          >
          <div class="input-hint">Папка будет создана в: {{ displayCurrentPath }}</div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeCreateFolder">Отмена</button>
          <button class="btn btn-primary" @click="createFolder">
            <i class="fas fa-plus mr-1"></i> Создать
          </button>
        </div>
      </div>
    </div>

    <!-- Rename modal -->
    <div v-if="showRenameModal" class="modal-overlay" v-modal-close="closeRename">
      <div class="modal-dialog" @click.stop>
        <div class="modal-header">
          <div class="modal-icon edit">
            <i class="fas fa-pen"></i>
          </div>
          <h3>Переименовать</h3>
          <button class="modal-close" @click="closeRename">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <label>Новое имя</label>
          <input 
            v-model="renameValue" 
            type="text" 
            class="form-input"
            @keyup.enter="renameItem"
          >
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeRename">Отмена</button>
          <button class="btn btn-primary" @click="renameItem">
            <i class="fas fa-check mr-1"></i> Сохранить
          </button>
        </div>
      </div>
    </div>

    <!-- Folder permissions modal -->
    <FolderPermissionsModal
      :open="showPermissionsModal"
      :path="permissionsPath"
      @close="closePermissions"
    />

    <!-- Move modal -->
    <div v-if="showMoveModal" class="modal-overlay" v-modal-close="closeMove">
      <div class="modal-dialog" @click.stop>
        <div class="modal-header">
          <div class="modal-icon move">
            <i class="fas fa-arrows-alt"></i>
          </div>
          <h3>Переместить</h3>
          <button class="modal-close" @click="closeMove">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <label>Целевая папка</label>
          <input 
            v-model="moveTargetPath" 
            type="text" 
            class="form-input"
            placeholder="/CRM/Документы"
            @keyup.enter="moveItem"
          >
          <div class="input-hint">Текущая папка: {{ displayCurrentPath }}</div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeMove">Отмена</button>
          <button class="btn btn-primary" @click="moveItem">
            <i class="fas fa-arrow-right mr-1"></i> Переместить
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount, reactive } from 'vue'
import * as filesApi from '../services/api/files'
import { rawRequest } from '../services/api/_client'
import { useToast } from '../composables/useToast'
import { openTrustedExternalUrl } from '../utils/download'
import FolderPermissionsModal from '../components/files/FolderPermissionsModal.vue'

export default {
  name: 'FilesCatalog',
  components: { FolderPermissionsModal },
  setup() {
    const toast = useToast()
    const showToast = (message, type = 'success') => {
      if (type === 'error') {
        toast.error(message)
      } else {
        toast.success(message)
      }
    }
    
    const rootPath = ref('')
    const currentPath = ref('')
    const items = ref([])
    const loading = ref(false)
    const searchQuery = ref('')
    const isSearchMode = ref(false)
    const filterType = ref('all')
    const sortBy = ref('name')
    const viewMode = ref('list')
    const isDragOver = ref(false)
    const dragDepth = ref(0)
    const activeMenu = ref(null)

    const uploadStatus = reactive({
      active: false,
      progress: 0,
      filename: '',
      totalFiles: 0,
      completed: 0,
    })

    const downloadStatus = reactive({
      active: false,
      progress: 0,
      filename: '',
      indeterminate: false,
    })

    const storageUsage = reactive({
      loading: false,
      available: false,
      usedBytes: 0,
      totalBytes: 0,
      percent: 0,
    })

    const resetUploadStatus = (delay = 0) => {
      const clear = () => {
        uploadStatus.active = false
        uploadStatus.progress = 0
        uploadStatus.filename = ''
        uploadStatus.totalFiles = 0
        uploadStatus.completed = 0
      }
      if (delay) {
        setTimeout(clear, delay)
      } else {
        clear()
      }
    }

    const resetDownloadStatus = (delay = 0) => {
      const clear = () => {
        downloadStatus.active = false
        downloadStatus.progress = 0
        downloadStatus.filename = ''
        downloadStatus.indeterminate = false
      }
      if (delay) {
        setTimeout(clear, delay)
      } else {
        clear()
      }
    }

    const loadStorageUsage = async () => {
      storageUsage.loading = true
      try {
        const data = (await filesApi.getStorageUsage()) || {}
        storageUsage.usedBytes = Number(data.used_bytes || 0)
        storageUsage.totalBytes = Number(data.total_bytes || 0)
        storageUsage.percent = Number.isFinite(data.percent) ? data.percent : (storageUsage.totalBytes ? Math.round((storageUsage.usedBytes / storageUsage.totalBytes) * 1000) / 10 : 0)
        storageUsage.available = true
      } catch (error) {
        const status = error?.response?.status
        if (status !== 403) {
          console.error('Error loading storage usage:', error)
        }
        storageUsage.available = false
      } finally {
        storageUsage.loading = false
      }
    }


    const uploadInput = ref(null)
    const folderInput = ref(null)
    const showCreateModal = ref(false)
    const createFolderName = ref('')
    const showRenameModal = ref(false)
    const renameTarget = ref(null)
    const renameValue = ref('')
    const showMoveModal = ref(false)
    const moveTarget = ref(null)
    const moveTargetPath = ref('')
    const showPermissionsModal = ref(false)
    const permissionsPath = ref('')

    const stripDiskPrefix = (path) => {
      if (!path) return ''
      return path.startsWith('disk:') ? path.slice(5) : path
    }

    const normalizePath = (path) => {
      if (!path) return '/'
      const prefix = path.startsWith('disk:') ? 'disk:' : ''
      const rest = stripDiskPrefix(path)
      const normalized = rest.startsWith('/') ? rest : `/${rest}`
      return `${prefix}${normalized}`
    }

    const joinPath = (base, name) => {
      if (!base) return name
      const prefix = base.startsWith('disk:') ? 'disk:' : ''
      const rest = stripDiskPrefix(base).replace(/\/+$/, '')
      return `${prefix}${rest}/${name}`
    }

    const formatBytes = (bytes) => {
      if (!bytes && bytes !== 0) return '—'
      const units = ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ']
      let size = Number(bytes)
      let index = 0
      while (size >= 1024 && index < units.length - 1) {
        size /= 1024
        index += 1
      }
      return `${size.toFixed(size >= 10 ? 0 : 1)} ${units[index]}`
    }

    const formatDateTime = (value) => {
      if (!value) return '—'
      const date = new Date(value)
      if (Number.isNaN(date.getTime())) return '—'
      return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })
    }

    const getFileExt = (item) => {
      const name = (item.name || '').trim()
      const lastDot = name.lastIndexOf('.')
      if (lastDot <= 0 || lastDot === name.length - 1) {
        const hint = (item.ext_hint || '').toString().trim()
        return hint ? hint.toUpperCase() : '—'
      }
      const ext = name.slice(lastDot + 1).trim()
      if (!ext) return '—'
      if (ext.length > 8) return '—'
      if (!/^[A-Za-z0-9]+$/.test(ext)) return '—'
      return ext.toUpperCase()
    }

    const getItemIcon = (item) => {
      if (item.type === 'folder') return 'fa-folder'
      const ext = (item.name || '').split('.').pop().toLowerCase()
      if (['pdf'].includes(ext)) return 'fa-file-pdf'
      if (['doc', 'docx'].includes(ext)) return 'fa-file-word'
      if (['xls', 'xlsx'].includes(ext)) return 'fa-file-excel'
      if (['ppt', 'pptx'].includes(ext)) return 'fa-file-powerpoint'
      if (['jpg', 'jpeg', 'png', 'gif', 'jfif', 'webp', 'svg'].includes(ext)) return 'fa-file-image'
      if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return 'fa-file-archive'
      if (['mp4', 'avi', 'mov', 'mkv'].includes(ext)) return 'fa-file-video'
      if (['mp3', 'wav', 'flac', 'ogg'].includes(ext)) return 'fa-file-audio'
      if (['txt', 'md', 'log'].includes(ext)) return 'fa-file-alt'
      if (['js', 'ts', 'py', 'html', 'css', 'json', 'xml'].includes(ext)) return 'fa-file-code'
      return 'fa-file'
    }

    const getIconClass = (item) => {
      if (item.type === 'folder') return 'icon-folder'
      const ext = (item.name || '').split('.').pop().toLowerCase()
      if (['pdf'].includes(ext)) return 'icon-pdf'
      if (['doc', 'docx'].includes(ext)) return 'icon-word'
      if (['xls', 'xlsx'].includes(ext)) return 'icon-excel'
      if (['jpg', 'jpeg', 'png', 'gif', 'jfif', 'webp', 'svg'].includes(ext)) return 'icon-image'
      if (['zip', 'rar', '7z'].includes(ext)) return 'icon-archive'
      return 'icon-default'
    }

    const filteredItems = computed(() => {
      let result = items.value || []
      result = result.filter((item) => {
        const name = (item.name || '').toLowerCase()
        return !['thumbs.db', 'desktop.ini', '.ds_store'].includes(name)
      })
      if (filterType.value === 'folder') {
        result = result.filter(i => i.type === 'folder')
      } else if (filterType.value === 'file') {
        result = result.filter(i => i.type === 'file')
      } else if (filterType.value === 'image') {
        result = result.filter(i => {
          const ext = (i.name || '').split('.').pop().toLowerCase()
          return ['jpg', 'jpeg', 'png', 'gif', 'jfif', 'webp', 'svg'].includes(ext)
        })
      } else if (filterType.value === 'document') {
        result = result.filter(i => {
          const ext = (i.name || '').split('.').pop().toLowerCase()
          return ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt'].includes(ext)
        })
      }
      return result
    })

    const sortedItems = computed(() => {
      const arr = [...filteredItems.value]
      // Folders first
      arr.sort((a, b) => {
        if (a.type === 'folder' && b.type !== 'folder') return -1
        if (a.type !== 'folder' && b.type === 'folder') return 1
        if (sortBy.value === 'name') {
          return (a.name || '').localeCompare(b.name || '', 'ru')
        } else if (sortBy.value === 'date') {
          return new Date(b.modified || 0) - new Date(a.modified || 0)
        } else if (sortBy.value === 'size') {
          return (b.size || 0) - (a.size || 0)
        }
        return 0
      })
      return arr
    })

    const loadItems = async (path = currentPath.value, query = '') => {
      loading.value = true
      try {
        const result = await filesApi.list({ path, search: query || undefined })
        items.value = result.items || []
        rootPath.value = result.root || rootPath.value
        currentPath.value = result.path || path
      } catch (error) {
        console.error('Error loading files:', error)
        items.value = []
        showToast('Ошибка загрузки каталога', 'error')
      } finally {
        loading.value = false
      }
    }

    const refresh = () => {
      if (viewMode.value === 'tree') {
        return refreshTree()
      }
      if (isSearchMode.value && searchQuery.value) {
        loadItems(currentPath.value, searchQuery.value)
      } else {
        loadItems(currentPath.value)
      }
    }

    const applySearch = () => {
      const query = searchQuery.value.trim()
      if (!query) {
        clearSearch()
        return
      }
      isSearchMode.value = true
      loadItems(currentPath.value, query)
    }

    const clearSearch = () => {
      isSearchMode.value = false
      searchQuery.value = ''
      loadItems(currentPath.value)
    }

    const openPath = (path) => {
      isSearchMode.value = false
      searchQuery.value = ''
      loadItems(path)
    }

    // ───────────────────────────────────────────────────────────────
    // Tree view (третий вид) — двухпанельный explorer как в документации
    // сделки: слева ленивое дерево папок, справа содержимое выбранной.
    // ───────────────────────────────────────────────────────────────
    const treeRootPath = ref('')
    const treeRootLoading = ref(false)
    const treeInitialized = ref(false)
    const treeChildren = reactive({})           // path -> [folder nodes]
    const treeExpanded = reactive(new Set())     // развёрнутые пути папок
    const treeLoadingPaths = reactive(new Set()) // пути, у которых грузятся дети
    const treeSelectedPath = ref('')
    const treeSelectedName = ref('Каталог')
    const treeContent = ref([])                 // items (папки+файлы) выбранной
    const treeContentLoading = ref(false)

    const treeSelectedLabel = computed(() => {
      if (!treeSelectedPath.value || treeSelectedPath.value === treeRootPath.value) return 'Каталог'
      return treeSelectedName.value
        || (stripDiskPrefix(treeSelectedPath.value).split('/').filter(Boolean).pop() || 'Каталог')
    })

    const treeContentSorted = computed(() => {
      const arr = (treeContent.value || []).filter((item) => {
        const name = (item.name || '').toLowerCase()
        return !['thumbs.db', 'desktop.ini', '.ds_store'].includes(name)
      })
      arr.sort((a, b) => {
        if (a.type === 'folder' && b.type !== 'folder') return -1
        if (a.type !== 'folder' && b.type === 'folder') return 1
        return (a.name || '').localeCompare(b.name || '', 'ru')
      })
      return arr
    })

    // Плоский список строк из вложенного дерева — depth + collapse-состояние.
    const treeRows = computed(() => {
      const rows = []
      const walk = (parentPath, depth) => {
        const kids = treeChildren[parentPath] || []
        for (const node of kids) {
          const expanded = treeExpanded.has(node.path)
          rows.push({ ...node, depth, expanded, loading: treeLoadingPaths.has(node.path) })
          if (expanded) walk(node.path, depth + 1)
        }
      }
      walk(treeRootPath.value, 0)
      return rows
    })

    const loadTreeChildren = async (path) => {
      treeLoadingPaths.add(path)
      try {
        const result = await filesApi.list({ path })
        treeChildren[path] = (result.items || []).filter((i) => i.type === 'folder')
      } catch (error) {
        console.error('Error loading tree children:', error)
        treeChildren[path] = []
      } finally {
        treeLoadingPaths.delete(path)
      }
    }

    const loadTreeContent = async (path) => {
      treeContentLoading.value = true
      try {
        const result = await filesApi.list({ path })
        treeContent.value = result.items || []
      } catch (error) {
        console.error('Error loading tree content:', error)
        treeContent.value = []
      } finally {
        treeContentLoading.value = false
      }
    }

    const toggleTreeNode = async (node) => {
      if (!node?.path) return
      if (treeExpanded.has(node.path)) {
        treeExpanded.delete(node.path)
      } else {
        treeExpanded.add(node.path)
        if (!treeChildren[node.path]) await loadTreeChildren(node.path)
      }
    }

    const selectTreeNode = async (node) => {
      if (node?.path === undefined || node?.path === null) return
      treeSelectedPath.value = node.path
      treeSelectedName.value = node.name || 'Каталог'
      // Действия тулбара (создать папку / загрузить) нацеливаем на выбранную.
      currentPath.value = node.path
      if (node.path !== treeRootPath.value && !treeExpanded.has(node.path)) {
        treeExpanded.add(node.path)
      }
      await Promise.all([
        treeChildren[node.path] ? Promise.resolve() : loadTreeChildren(node.path),
        loadTreeContent(node.path),
      ])
    }

    const initTree = async () => {
      treeRootLoading.value = true
      try {
        const result = await filesApi.list({ path: '' })
        const root = result.path || ''
        treeRootPath.value = root
        treeChildren[root] = (result.items || []).filter((i) => i.type === 'folder')
        treeSelectedPath.value = root
        treeSelectedName.value = 'Каталог'
        currentPath.value = root
        rootPath.value = result.root || rootPath.value
        treeContent.value = result.items || []
        treeInitialized.value = true
      } catch (error) {
        console.error('Error init tree:', error)
        showToast('Ошибка загрузки дерева', 'error')
      } finally {
        treeRootLoading.value = false
      }
    }

    const refreshTree = async () => {
      if (!treeInitialized.value) return initTree()
      const sel = treeSelectedPath.value || treeRootPath.value
      await Promise.all([loadTreeChildren(sel), loadTreeContent(sel)])
    }

    const setViewMode = (mode) => {
      viewMode.value = mode
      if (mode === 'tree' && !treeInitialized.value) initTree()
    }

    const openItem = (item) => {
      activeMenu.value = null
      if (item.type === 'folder') {
        openPath(item.path)
      } else {
        downloadItem(item)
      }
    }

    const openFolder = (item) => {
      if (item?.type !== 'folder') return
      openItem(item)
    }

    const downloadItem = async (item) => {
      activeMenu.value = null
      if (!item?.path) return
      downloadStatus.active = true
      downloadStatus.indeterminate = true
      downloadStatus.progress = 0
      const fallbackName = item?.type === 'folder' ? `${item?.name || 'folder'}.zip` : (item?.name || 'file')
      downloadStatus.filename = fallbackName
      try {
        const result = await filesApi.getDownloadLink({ path: item.path })
        if (result?.href) {
          const href = result.href
          if (href.startsWith('/api/')) {
            const fileResp = await rawRequest({
              method: 'get',
              url: href,
              responseType: 'blob',
              onDownloadProgress: (event) => {
                if (event.total) {
                  downloadStatus.indeterminate = false
                  downloadStatus.progress = Math.round((event.loaded / event.total) * 100)
                }
              }
            })
            const blobUrl = window.URL.createObjectURL(fileResp.data)
            const link = document.createElement('a')
            const disposition = fileResp.headers?.['content-disposition'] || ''
            const match = disposition.match(/filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i)
            let filename = fallbackName
            if (match?.[1]) {
              filename = decodeURIComponent(match[1])
            } else if (match?.[2]) {
              filename = match[2]
            }
            link.href = blobUrl
            link.download = filename
            document.body.appendChild(link)
            link.click()
            link.remove()
            window.URL.revokeObjectURL(blobUrl)
            downloadStatus.indeterminate = false
            downloadStatus.progress = 100
            resetDownloadStatus(800)
            return
          }
          if (openTrustedExternalUrl(href, ['disk.yandex.ru', 'yadi.sk', 'yandex.ru'])) {
            resetDownloadStatus(800)
            return
          }
          resetDownloadStatus()
          showToast('Недопустимая ссылка', 'error')
        } else {
          resetDownloadStatus()
          showToast('Ссылка недоступна', 'error')
        }
      } catch (error) {
        resetDownloadStatus()
        console.error('Error downloading file:', error)
        showToast('Ссылка недоступна', 'error')
      }
    }

    const triggerUpload = () => {
      uploadInput.value?.click()
    }

    const handleUpload = async (event) => {
      const files = Array.from(event.target.files || [])
      await uploadFiles(files)
      event.target.value = ''
    }

    const triggerFolderUpload = () => {
      folderInput.value?.click()
    }

    const handleFolderUpload = async (event) => {
      const files = Array.from(event.target.files || [])
      await uploadFiles(files)
      event.target.value = ''
    }

    const handleDragEnter = () => {
      dragDepth.value += 1
      isDragOver.value = true
    }

    const handleDragOver = () => {
      isDragOver.value = true
    }

    const handleDragLeave = () => {
      dragDepth.value = Math.max(0, dragDepth.value - 1)
      if (dragDepth.value === 0) {
        isDragOver.value = false
      }
    }

    const handleDrop = async (event) => {
      isDragOver.value = false
      dragDepth.value = 0
      const items = Array.from(event.dataTransfer?.items || []).filter((item) => item.kind === 'file')
      const files = Array.from(event.dataTransfer?.files || [])
      let entries = []
      if (items.length) {
        if (items.length > 1) {
          const perRoot = []
          for (const item of items) {
            const chunk = await extractEntries([item])
            const sample = chunk[0]?.relPath || chunk[0]?.file?.name || ''
            const rootName = sample.split('/')[0] || sample || '[unknown]'
            perRoot.push({ root: rootName, count: chunk.length })
            if (chunk.length) {
              entries = entries.concat(chunk)
            }
          }
          console.log('[files-dnd] roots summary:', perRoot)
        } else {
          entries = await extractEntries(items)
          const sample = entries[0]?.relPath || entries[0]?.file?.name || ''
          const rootName = sample.split('/')[0] || sample || '[unknown]'
          console.log('[files-dnd] single root:', rootName, 'files:', entries.length)
        }
      }
      if (!entries.length) {
        if (files.length) {
          await uploadFiles(files)
        }
        return
      }
      const merged = []
      const seen = new Set()
      const addItem = (file, relPath = '') => {
        if (!file) return
        const key = `${relPath}|${file.name}|${file.size}`
        if (seen.has(key)) return
        seen.add(key)
        merged.push({ file, relPath })
      }
      entries.forEach((item) => addItem(item.file, item.relPath || ''))
      const relFiles = files.filter((file) => file.webkitRelativePath && (file.size > 0 || file.type))
      const hasNested = entries.some((item) => (item.relPath || '').includes('/'))
      relFiles.forEach((file) => addItem(file, file.webkitRelativePath || ''))
      if (!hasNested) {
        files.forEach((file) => {
          if (!file) return
          if (file.webkitRelativePath) return
          if (file.size === 0 && !file.type) return
          addItem(file, '')
        })
      }
      await uploadFiles(merged)
    }

    const extractEntries = async (items) => {
      const results = []

      const readAllEntries = async (reader) => {
        const entries = []
        while (true) {
          const batch = await new Promise((resolve, reject) => {
            reader.readEntries(resolve, reject)
          })
          if (!batch || !batch.length) break
          entries.push(...batch)
        }
        return entries
      }

      const traverseHandle = async (handle, prefix = '') => {
        if (!handle) return
        if (handle.kind === 'file') {
          try {
            const file = await handle.getFile()
            if (file) {
              results.push({ file, relPath: `${prefix}${file.name}` })
            }
          } catch (error) {
            console.warn('Не удалось прочитать файл из handle:', error)
          }
          return
        }
        if (handle.kind === 'directory') {
          const dirPrefix = `${prefix}${handle.name}/`
          for await (const child of handle.values()) {
            await traverseHandle(child, dirPrefix)
          }
        }
      }

      const traverseEntry = async (entry, prefix = '') => {
        if (!entry) return
        if (entry.isFile) {
          await new Promise((resolve) => {
            entry.file((file) => {
              if (file) {
                results.push({ file, relPath: `${prefix}${file.name}` })
              }
              resolve()
            })
          })
          return
        }
        if (entry.isDirectory) {
          const reader = entry.createReader()
          let children = []
          try {
            children = await readAllEntries(reader)
          } catch (error) {
            console.warn('Не удалось прочитать каталог:', error)
            return
          }
          for (const child of children) {
            await traverseEntry(child, `${prefix}${entry.name}/`)
          }
        }
      }

      for (const item of items) {
        const getHandle = item?.getAsFileSystemHandle
        if (getHandle) {
          try {
            const handle = await getHandle.call(item)
            if (handle) {
              await traverseHandle(handle, '')
              continue
            }
          } catch (error) {
            console.warn('FileSystemHandle not доступен:', error)
          }
        }
        const entry = item.webkitGetAsEntry ? item.webkitGetAsEntry() : null
        if (entry) {
          await traverseEntry(entry)
        }
      }
      return results.filter((item) => item?.file instanceof File)
    }

    const uploadFormData = (formData, onProgress) => {
      const url = filesApi.uploadUrl(currentPath.value)
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest()
        xhr.open('POST', url, true)
        xhr.withCredentials = true
        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve()
            return
          }
          let detail = null
          try {
            const parsed = JSON.parse(xhr.responseText || '{}')
            detail = parsed?.detail || parsed?.message || null
          } catch (error) {
            detail = null
          }
          const err = new Error(detail || `HTTP ${xhr.status}`)
          err.response = { status: xhr.status, data: { detail } }
          reject(err)
        }
        xhr.onerror = () => {
          reject(new Error('Network Error'))
        }
        if (xhr.upload && onProgress) {
          xhr.upload.onprogress = onProgress
        }
        xhr.send(formData)
      })
    }

    const uploadFiles = async (files) => {
      if (!files.length) return
      const skipNames = new Set(['thumbs.db', 'desktop.ini', '.ds_store'])
      const normalized = files.map((item) => {
        if (item instanceof File) {
          return { file: item, relPath: item.webkitRelativePath || '' }
        }
        return item
      }).filter((item) => item?.file instanceof File)
        .filter((item) => {
          const rel = (item.relPath || item.file?.webkitRelativePath || '').replace(/\\/g, '/')
          const name = (rel.split('/').pop() || item.file?.name || '').toLowerCase()
          return !skipNames.has(name)
        })
      if (!normalized.length) {
        showToast('Нет файлов для загрузки', 'error')
        return
      }
      uploadStatus.active = true
      uploadStatus.progress = 0
      uploadStatus.totalFiles = normalized.length
      uploadStatus.completed = 0
      uploadStatus.filename = normalized.length === 1 ? (normalized[0]?.file?.name || 'file') : `${normalized.length} файлов`

      const totalBytes = normalized.reduce((sum, item) => sum + (item.file?.size || 0), 0)
      const hasRelPaths = normalized.some((item) => item.relPath)
      const MAX_BATCH_FILES = hasRelPaths ? 1 : 50
      const MAX_BATCH_BYTES = hasRelPaths ? (10 * 1024 * 1024) : (50 * 1024 * 1024)
      const batches = []
      let currentBatch = []
      let currentBytes = 0
      normalized.forEach((item) => {
        const size = item.file?.size || 0
        const wouldExceed = currentBatch.length >= MAX_BATCH_FILES || (currentBytes + size) > MAX_BATCH_BYTES
        if (currentBatch.length && wouldExceed) {
          batches.push(currentBatch)
          currentBatch = []
          currentBytes = 0
        }
        currentBatch.push(item)
        currentBytes += size
      })
      if (currentBatch.length) {
        batches.push(currentBatch)
      }

      let uploadedBytes = 0
      let successFiles = 0
      let failedFiles = 0
      let skippedFiles = 0
      const errors = []
      for (const batch of batches) {
        const formData = new FormData()
        let batchBytes = 0
        batch.forEach((item) => {
          formData.append('files', item.file)
          formData.append('paths', item.relPath || '')
          batchBytes += item.file?.size || 0
        })
        try {
          await uploadFormData(formData, (event) => {
            if (event.total && totalBytes) {
              const overall = Math.min(totalBytes, uploadedBytes + event.loaded)
              uploadStatus.progress = Math.round((overall / totalBytes) * 100)
            }
          })
          uploadedBytes += batchBytes
          successFiles += batch.length
          uploadStatus.completed += batch.length
          if (totalBytes) {
            uploadStatus.progress = Math.round((uploadedBytes / totalBytes) * 100)
          }
        } catch (error) {
          const message = error?.message || ''
          const isAccessDenied = message.toLowerCase().includes('network error') || message.toLowerCase().includes('access denied')
          if (isAccessDenied && batch.length === 1) {
            skippedFiles += 1
            continue
          }
          failedFiles += batch.length
          errors.push(error)
          console.error('Upload batch failed:', error)
        }
      }

      if (successFiles > 0) {
        uploadStatus.progress = 100
        if (failedFiles > 0) {
          showToast(`Загружено ${successFiles} файл(ов). Не удалось: ${failedFiles}`, 'error')
        } else {
          showToast(`Загружено ${successFiles} файл(ов)`, 'success')
        }
        await refresh()
        resetUploadStatus(800)
        return
      }

      resetUploadStatus()
      const lastError = errors[errors.length - 1]
      const detail = lastError?.response?.data?.detail
      showToast(detail || 'Ошибка загрузки', 'error')

    }

    const toggleMenu = (item) => {
      activeMenu.value = activeMenu.value === item.path ? null : item.path
    }

    const closeMenuOnClick = (e) => {
      if (!e.target.closest('.file-context-menu') && !e.target.closest('.file-card-actions')) {
        activeMenu.value = null
      }
    }

    const openCreateFolder = () => {
      createFolderName.value = ''
      showCreateModal.value = true
    }

    const closeCreateFolder = () => {
      showCreateModal.value = false
    }

    const createFolder = async () => {
      const name = createFolderName.value.trim()
      if (!name) {
        showToast('Введите название папки', 'error')
        return
      }
      try {
        await filesApi.createFolder({ path: currentPath.value, name })
        closeCreateFolder()
        showToast('Папка создана', 'success')
        await refresh()
      } catch (error) {
        console.error('Error creating folder:', error)
        showToast('Ошибка создания папки', 'error')
      }
    }

    const openRename = (item) => {
      activeMenu.value = null
      renameTarget.value = item
      renameValue.value = item?.name || ''
      showRenameModal.value = true
    }

    const closeRename = () => {
      showRenameModal.value = false
      renameTarget.value = null
      renameValue.value = ''
    }

    const renameItem = async () => {
      if (!renameTarget.value) return
      const name = renameValue.value.trim()
      if (!name) {
        showToast('Введите новое имя', 'error')
        return
      }
      try {
        await filesApi.rename({
          path: renameTarget.value.path,
          name
        })
        closeRename()
        showToast('Переименовано', 'success')
        await refresh()
      } catch (error) {
        console.error('Error renaming:', error)
        showToast('Ошибка переименования', 'error')
      }
    }

    const openMove = (item) => {
      activeMenu.value = null
      moveTarget.value = item
      moveTargetPath.value = currentPath.value
      showMoveModal.value = true
    }

    const closeMove = () => {
      showMoveModal.value = false
      moveTarget.value = null
      moveTargetPath.value = ''
    }

    const moveItem = async () => {
      if (!moveTarget.value) return
      const targetDir = moveTargetPath.value.trim()
      if (!targetDir) {
        showToast('Введите путь к папке', 'error')
        return
      }
      const destination = joinPath(targetDir, moveTarget.value.name)
      try {
        await filesApi.move({
          from_path: moveTarget.value.path,
          to_path: destination
        })
        closeMove()
        showToast('Перемещено', 'success')
        await refresh()
      } catch (error) {
        console.error('Error moving:', error)
        showToast('Ошибка перемещения', 'error')
      }
    }

    const openPermissions = (item) => {
      activeMenu.value = null
      if (!item || item.type !== 'folder' || !item.path) return
      permissionsPath.value = item.path
      showPermissionsModal.value = true
    }

    const closePermissions = () => {
      showPermissionsModal.value = false
      permissionsPath.value = ''
    }

    const deleteItem = async (item) => {
      activeMenu.value = null
      if (!item?.path) return
      if (!confirm('Удалить в корзину?')) return
      try {
        await filesApi.remove({ path: item.path, permanent: false })
        showToast('Перемещено в корзину', 'success')
        await refresh()
      } catch (error) {
        console.error('Error deleting:', error)
        showToast('Ошибка удаления', 'error')
      }
    }

    const normalizeForBreadcrumbs = (path) => {
      const base = normalizePath(path)
      return stripDiskPrefix(base).replace(/\/+$/, '') || '/'
    }

    const displayCurrentPath = computed(() => {
      return stripDiskPrefix(currentPath.value || '') || '/'
    })

    const breadcrumbs = computed(() => {
      if (!currentPath.value) return []
      const rootNormalized = normalizeForBreadcrumbs(rootPath.value || currentPath.value)
      const currentNormalized = normalizeForBreadcrumbs(currentPath.value)
      const rootLabel = rootNormalized.split('/').filter(Boolean).pop() || 'Корень'
      const prefix = currentPath.value.startsWith('disk:') ? 'disk:' : ''
      const crumbs = [{ label: rootLabel, path: `${prefix}${rootNormalized}` }]
      if (currentNormalized === rootNormalized) return crumbs
      const relative = currentNormalized.startsWith(rootNormalized)
        ? currentNormalized.slice(rootNormalized.length)
        : currentNormalized
      const parts = relative.split('/').filter(Boolean)
      let current = rootNormalized
      parts.forEach((part) => {
        current = `${current}/${part}`
        crumbs.push({ label: part, path: `${prefix}${current}` })
      })
      return crumbs
    })

    const canGoBack = computed(() => {
      if (!currentPath.value || !rootPath.value) return false
      const currentNorm = normalizeForBreadcrumbs(currentPath.value)
      const rootNorm = normalizeForBreadcrumbs(rootPath.value)
      return currentNorm !== rootNorm
    })

    const goBack = () => {
      if (!canGoBack.value) return
      const prefix = currentPath.value.startsWith('disk:') ? 'disk:' : ''
      const currentNorm = normalizeForBreadcrumbs(currentPath.value)
      const rootNorm = normalizeForBreadcrumbs(rootPath.value)
      const lastSlash = currentNorm.lastIndexOf('/')
      let parent = lastSlash > 0 ? currentNorm.slice(0, lastSlash) : '/'
      if (parent.length < rootNorm.length) parent = rootNorm
      openPath(`${prefix}${parent}`)
    }

    let usageTimer = null

    onMounted(() => {
      loadItems()
      loadStorageUsage()
      usageTimer = setInterval(loadStorageUsage, 5 * 60 * 1000)
      document.addEventListener('click', closeMenuOnClick)
    })

    onBeforeUnmount(() => {
      if (usageTimer) {
        clearInterval(usageTimer)
      }
      document.removeEventListener('click', closeMenuOnClick)
    })

    return {
      rootPath, currentPath, items, loading, searchQuery, isSearchMode,
      filterType, sortBy, viewMode, isDragOver, activeMenu, uploadStatus, downloadStatus,
      uploadInput, folderInput, showCreateModal, createFolderName,
      showRenameModal, renameValue, showMoveModal, moveTargetPath,
      showPermissionsModal, permissionsPath,
      storageUsage,
      sortedItems, breadcrumbs, canGoBack, displayCurrentPath,
      refresh, applySearch, clearSearch, openPath, openItem,
      openFolder,
      downloadItem, triggerUpload, handleUpload, triggerFolderUpload, handleFolderUpload, handleDrop,
      handleDragEnter, handleDragOver, handleDragLeave,
      toggleMenu, openCreateFolder, closeCreateFolder, createFolder,
      openPermissions, closePermissions,
      openRename, closeRename, renameItem,
      openMove, closeMove, moveItem, deleteItem, goBack,
      getItemIcon, getIconClass, getFileExt, formatBytes, formatDateTime,
      // tree view
      setViewMode, treeRows, treeRootPath, treeRootLoading,
      treeSelectedPath, treeSelectedLabel, treeContentLoading, treeContentSorted,
      toggleTreeNode, selectTreeNode
    }
  }
}
</script>

<style scoped>
.files-catalog-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 16px;
}

/* Header */
.files-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}

.files-header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.files-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.3rem;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.files-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
  color: var(--md-sys-color-on-background);
}

.files-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.storage-usage {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: 999px;
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline-variant);
  font-size: 0.75rem;
  color: var(--md-sys-color-on-surface-variant);
}

.storage-usage-bar {
  width: 120px;
  height: 6px;
  border-radius: 999px;
  background: var(--md-sys-color-surface-variant);
  overflow: hidden;
}

.storage-usage-fill {
  height: 100%;
  background: linear-gradient(90deg, #22c55e, #16a34a);
  transition: width 0.2s ease;
}

.storage-usage-fill.loading {
  width: 40%;
  animation: usage-pulse 1.2s infinite ease-in-out;
}

.storage-usage-text {
  white-space: nowrap;
}

@keyframes usage-pulse {
  0% { transform: translateX(-30%); }
  50% { transform: translateX(40%); }
  100% { transform: translateX(120%); }
}

.files-breadcrumbs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}

.breadcrumb-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 16px;
  font-size: 0.8rem;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  transition: all 0.2s;
}

.breadcrumb-chip:hover {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-primary);
  border-color: var(--md-sys-color-primary);
}

.breadcrumb-chip--active {
  background: var(--md-sys-color-primary);
  color: white;
  border-color: var(--md-sys-color-primary);
}

.files-header-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.files-header-actions .btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

/* Toolbar */
.files-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--md-sys-color-surface);
  border-radius: 12px;
  border: 1px solid var(--md-sys-color-outline);
  flex-wrap: wrap;
}

.toolbar-search {
  position: relative;
  flex: 1;
  min-width: 200px;
  max-width: 400px;
}

.toolbar-search i {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.85rem;
}

.toolbar-search input {
  width: 100%;
  padding: 8px 32px 8px 36px;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 8px;
  background: var(--md-sys-color-surface-thick);
  font-size: 0.9rem;
}

.toolbar-search input:focus {
  outline: none;
  border-color: var(--md-sys-color-primary);
}

.search-clear {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  padding: 4px;
}

.toolbar-filters {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 8px;
  background: var(--md-sys-color-surface-thick);
  font-size: 0.85rem;
  color: var(--md-sys-color-on-surface);
  cursor: pointer;
}

.view-toggle {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 8px;
  background: var(--md-sys-color-surface-thick);
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  transition: all 0.2s;
}

.view-toggle:hover {
  background: var(--md-sys-color-primary-container);
}

.view-toggle.active {
  background: var(--md-sys-color-primary);
  color: white;
  border-color: var(--md-sys-color-primary);
}

.btn-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 8px;
  background: var(--md-sys-color-surface-thick);
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
}

.btn-icon:hover {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-primary);
}

/* Search indicator */
.search-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--md-sys-color-primary-container);
  border-radius: 8px;
  font-size: 0.85rem;
  color: var(--md-sys-color-primary);
}

.search-indicator button {
  background: none;
  border: none;
  color: var(--md-sys-color-primary);
  cursor: pointer;
  padding: 2px 6px;
}

/* Content */
.files-content {
  flex: 1;
  position: relative;
  overflow: auto;
  background: var(--md-sys-color-surface);
  border-radius: 16px;
  border: 1px solid var(--md-sys-color-outline);
  min-height: 300px;
}

.files-content.drop-active {
  border-color: var(--md-sys-color-primary);
  border-style: dashed;
}

/* Loading */
.files-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  height: 100%;
  min-height: 300px;
  color: var(--md-sys-color-on-surface-variant);
}

.spinner-large {
  width: 48px;
  height: 48px;
  border: 4px solid var(--md-sys-color-outline);
  border-top-color: var(--md-sys-color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Empty state */
.files-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 48px 24px;
  text-align: center;
}

.empty-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--md-sys-color-primary-container);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  color: var(--md-sys-color-primary);
}

.files-empty h3 {
  margin: 8px 0 4px;
  color: var(--md-sys-color-on-surface);
}

.files-empty p {
  color: var(--md-sys-color-on-surface-variant);
  margin: 0 0 16px;
}

/* Grid View */
.files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
  padding: 16px;
}

.file-card {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 16px;
  background: var(--md-sys-color-surface-thick);
  border-radius: 12px;
  border: 1px solid var(--md-sys-color-outline-variant);
  cursor: pointer;
  transition: all 0.2s;
}

.file-card:hover {
  border-color: var(--md-sys-color-primary);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  transform: translateY(-2px);
}

.file-card-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  margin-bottom: 12px;
}

.file-card-icon.icon-folder { background: #FEF3C7; color: #D97706; }
.file-card-icon.icon-pdf { background: #FEE2E2; color: #DC2626; }
.file-card-icon.icon-word { background: #DBEAFE; color: #2563EB; }
.file-card-icon.icon-excel { background: #D1FAE5; color: #059669; }
.file-card-icon.icon-image { background: #E0E7FF; color: #4F46E5; }
.file-card-icon.icon-archive { background: #FEF3C7; color: #B45309; }
.file-card-icon.icon-default { background: #F3F4F6; color: #6B7280; }

.file-card-name {
  font-weight: 500;
  font-size: 0.9rem;
  color: var(--md-sys-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-card-meta {
  font-size: 0.75rem;
  color: var(--md-sys-color-on-surface-variant);
  margin-top: 4px;
}

.file-card-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.file-card:hover .file-card-actions {
  opacity: 1;
}

.file-card-actions button {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: none;
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-card-actions button:hover {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-primary);
}

/* Context menu */
.file-context-menu {
  position: absolute;
  top: 40px;
  right: 8px;
  z-index: 100;
  background: var(--md-sys-color-surface-thick);
  border-radius: 10px;
  border: 1px solid var(--md-sys-color-outline);
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
  min-width: 160px;
  overflow: hidden;
}

.file-context-menu button {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 14px;
  border: none;
  background: none;
  font-size: 0.85rem;
  color: var(--md-sys-color-on-surface);
  cursor: pointer;
  text-align: left;
}

.file-context-menu button:hover {
  background: var(--md-sys-color-primary-container);
}

.file-context-menu button.danger {
  color: var(--color-danger);
}

.file-context-menu button.danger:hover {
  background: rgba(255, 59, 48, 0.1);
}

.menu-divider {
  height: 1px;
  background: var(--md-sys-color-outline-variant);
  margin: 4px 0;
}

/* List View */
.files-list {
  display: flex;
  flex-direction: column;
}

.list-header {
  display: grid;
  grid-template-columns: 1fr 100px 100px 120px 140px;
  gap: 12px;
  padding: 12px 16px;
  background: var(--md-sys-color-surface);
  border-bottom: 1px solid var(--md-sys-color-outline);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--md-sys-color-on-surface-variant);
  position: sticky;
  top: 0;
  z-index: 10;
}

.list-row {
  display: grid;
  grid-template-columns: 1fr 100px 100px 120px 140px;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  align-items: center;
  cursor: pointer;
  transition: background 0.15s;
}

.list-row:hover {
  background: var(--md-sys-color-primary-container);
}

.col-name {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.file-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
}

.file-icon.icon-folder { background: #FEF3C7; color: #D97706; }
.file-icon.icon-pdf { background: #FEE2E2; color: #DC2626; }
.file-icon.icon-word { background: #DBEAFE; color: #2563EB; }
.file-icon.icon-excel { background: #D1FAE5; color: #059669; }
.file-icon.icon-image { background: #E0E7FF; color: #4F46E5; }
.file-icon.icon-archive { background: #FEF3C7; color: #B45309; }
.file-icon.icon-default { background: #F3F4F6; color: #6B7280; }

.file-name {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.col-type, .col-size, .col-date {
  font-size: 0.85rem;
  color: var(--md-sys-color-on-surface-variant);
}

.col-size {
  text-align: right;
}

.col-actions {
  display: flex;
  gap: 4px;
  justify-content: flex-end;
  opacity: 0;
  transition: opacity 0.15s;
}

.list-row:hover .col-actions {
  opacity: 1;
}

.col-actions button {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: none;
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.col-actions button:hover {
  background: var(--md-sys-color-primary);
  color: white;
}

.col-actions button.danger:hover {
  background: var(--color-danger);
}

/* Drop overlay */
.drop-overlay {
  position: absolute;
  inset: 0;
  background: rgba(99, 102, 241, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.drop-overlay-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px 48px;
  background: var(--md-sys-color-surface-thick);
  border-radius: 16px;
  border: 2px dashed var(--md-sys-color-primary);
}

.drop-overlay-content i {
  font-size: 2.5rem;
  color: var(--md-sys-color-primary);
}

.drop-overlay-content span {
  font-weight: 500;
  color: var(--md-sys-color-primary);
}

/* Modals */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-dialog {
  background: var(--md-sys-color-surface-thick);
  border-radius: 16px;
  width: 100%;
  max-width: 420px;
  margin: 16px;
  box-shadow: 0 16px 48px rgba(0,0,0,0.2);
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.modal-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
}

.modal-icon.folder { background: #FEF3C7; color: #D97706; }
.modal-icon.edit { background: #DBEAFE; color: #2563EB; }
.modal-icon.move { background: #E0E7FF; color: #4F46E5; }

.modal-header h3 {
  flex: 1;
  margin: 0;
  font-size: 1.1rem;
}

.modal-close {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  background: var(--md-sys-color-outline-variant);
}

.modal-body {
  padding: 20px;
}

.modal-body label {
  display: block;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 10px;
  background: var(--md-sys-color-surface);
  font-size: 0.95rem;
}

.form-input:focus {
  outline: none;
  border-color: var(--md-sys-color-primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

.input-hint {
  font-size: 0.8rem;
  color: var(--md-sys-color-on-surface-variant);
  margin-top: 8px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
}

/* Mobile */
@media (max-width: 768px) {
  .files-header {
    flex-direction: column;
  }
  
  .files-header-actions {
    width: 100%;
    justify-content: flex-start;
  }
  
  .btn-text {
    display: none;
  }
  
  .files-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .toolbar-search {
    max-width: none;
  }
  
  .toolbar-filters {
    flex-wrap: wrap;
  }
  
  .list-header, .list-row {
    grid-template-columns: 1fr 80px;
  }
  
  .col-type, .col-date {
    display: none;
  }
  
  .files-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 12px;
    padding: 12px;
  }
}

.transfer-indicator {
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 12px;
  padding: 10px 12px;
  display: grid;
  gap: 12px;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
}

.transfer-item {
  display: grid;
  gap: 6px;
}

.transfer-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: var(--md-sys-color-on-surface);
}

.transfer-item-name {
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.85rem;
  margin-left: 6px;
  word-break: break-all;
}

.transfer-bar {
  position: relative;
  height: 6px;
  border-radius: 999px;
  background: var(--md-sys-color-surface-variant);
  overflow: hidden;
}

.transfer-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #4f8bff, #56ccf2);
  transition: width 0.2s ease;
}

.transfer-bar.indeterminate .transfer-bar-fill {
  width: 40%;
  position: relative;
  animation: transfer-indeterminate 1.2s infinite ease-in-out;
}

.transfer-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: var(--md-sys-color-on-surface-variant);
}

@keyframes transfer-indeterminate {
  0% {
    transform: translateX(-30%);
  }
  50% {
    transform: translateX(60%);
  }
  100% {
    transform: translateX(130%);
  }
}

/* ───────────── Tree View (третий вид) ───────────── */
.files-tree-explorer {
  display: flex;
  height: 100%;
  min-height: 360px;
}

.ftree-panel {
  width: 300px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--md-sys-color-outline-variant);
  min-height: 0;
}

.ftree-panel-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  font-weight: 600;
  font-size: 0.85rem;
  color: var(--md-sys-color-on-surface-variant);
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.ftree-scroll {
  flex: 1;
  overflow: auto;
  padding: 6px;
  min-height: 0;
}

.ftree-row {
  display: flex;
  align-items: center;
}

.ftree-toggle {
  width: 22px;
  height: 28px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.7rem;
  padding: 0;
}

.ftree-toggle:hover {
  color: var(--md-sys-color-primary);
}

.ftree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
  padding: 5px 8px;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  text-align: left;
  color: var(--md-sys-color-on-surface);
  font-size: 0.88rem;
}

.ftree-node span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ftree-node:hover {
  background: var(--md-sys-color-surface-variant);
}

.ftree-node.active {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-primary);
  font-weight: 600;
}

.ftree-node--root {
  width: 100%;
  margin-bottom: 4px;
}

.ftree-hint {
  padding: 14px;
  text-align: center;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.85rem;
}

.ftree-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}

.ftree-content-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.ftree-content-path {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 0.92rem;
  color: var(--md-sys-color-on-surface);
  min-width: 0;
}

.ftree-content-path span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ftree-content-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.ftree-content-body {
  flex: 1;
  overflow: auto;
  min-height: 0;
}

.ftree-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}

.ftree-table th {
  position: sticky;
  top: 0;
  background: var(--md-sys-color-surface);
  text-align: left;
  font-weight: 600;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.02em;
  color: var(--md-sys-color-on-surface-variant);
  padding: 8px 12px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  z-index: 1;
}

.ftree-table td {
  padding: 7px 12px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  color: var(--md-sys-color-on-surface);
  vertical-align: middle;
}

.ftree-table tr.is-folder {
  cursor: pointer;
}

.ftree-table tbody tr:hover {
  background: var(--md-sys-color-surface-variant);
}

/* НЕ делаем сам <td> флексом — это ломает table-cell модель и
   border-collapse: горизонтальная линия-разделитель «переламывается»
   на границе колонок. Флекс держим во внутреннем span. */
.ftree-name-inner {
  display: flex;
  align-items: center;
  gap: 9px;
  min-width: 0;
}

.ftree-name-inner > span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 420px;
}

.ftree-col-size {
  width: 110px;
  white-space: nowrap;
  color: var(--md-sys-color-on-surface-variant);
}

.ftree-col-date {
  width: 160px;
  white-space: nowrap;
  color: var(--md-sys-color-on-surface-variant);
}

.ftree-col-actions {
  width: 1%;
  white-space: nowrap;
  text-align: right;
}

.ftree-col-actions button {
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
  width: 28px;
  height: 28px;
  border-radius: 6px;
  font-size: 0.82rem;
}

.ftree-col-actions button:hover {
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-primary);
}

.ftree-col-actions button.danger:hover {
  color: var(--md-sys-color-danger, #DC2626);
}

@media (max-width: 720px) {
  .ftree-panel {
    width: 220px;
  }
  .ftree-col-date {
    display: none;
  }
}

</style>
