<template>
  <div class="catalog-view h-100 d-flex overflow-hidden">
    <!-- Left Sidebar: Categories & Search -->
    <aside class="catalog-sidebar d-flex flex-column border-right glass-panel">
      <!-- Header: Title & Search -->
      <div class="p-3 border-bottom">
        <h2 class="mb-3" style="font-weight: 600; font-size: 1.25rem;">Каталог</h2>
        
        <!-- Search Input -->
        <div class="search-group w-100">
          <i class="fas fa-search"></i>
          <input
            v-model="searchQuery"
            type="text"
            class="form-control"
            placeholder="Поиск\.\.\."
            @input="debouncedSearch"
          >
          <button v-if="searchQuery" class="btn btn-sm btn-icon-only text-muted" @click="clearFilters">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>

      <!-- Categories List -->
      <div class="flex-grow-1 overflow-auto p-2">
        <div 
          class="nav-item d-flex align-center justify-between p-2 rounded-3 cursor-pointer mb-1"
          :class="{ 'active-category': !selectedCategoryId }"
          @click="selectCategory('')"
        >
          <div class="d-flex align-center gap-2">
            <i class="fas fa-layer-group text-primary"></i>
            <span class="fw-500">Все категории</span>
          </div>
        </div>

        <div v-if="categories.length > 0">
           <div class="text-muted small uppercase px-2 mt-3 mb-2" style="font-size: 0.75rem;">Категории</div>
           <div
             v-for="category in categories"
             :key="category.id"
             class="nav-item d-flex align-center justify-between p-2 rounded-3 cursor-pointer mb-1"
             :class="{ 'active-category': selectedCategoryId === category.id }"
             @click="selectCategory(category)"
           >
             <div class="d-flex align-center gap-2 overflow-hidden">
               <i class="fas fa-folder text-primary opacity-75"></i>
               <span class="text-truncate">{{ category.name }}</span>
             </div>
             <button class="btn btn-sm btn-icon opacity-0 hover-opacity-100" @click.stop="editCategory(category)">
               <i class="fas fa-edit small"></i>
             </button>
           </div>
        </div>
      </div>

      <!-- Bottom Actions -->
      <div class="p-3 border-top mt-auto">
         <button class="btn btn-secondary w-100 mb-2" @click="showCreateCategoryModal = true">
            <i class="fas fa-folder-plus mr-2"></i> Категория
         </button>
      </div>
    </aside>

    <!-- Main Content: Products List -->
    <main class="flex-grow-1 d-flex flex-column h-100 glass-panel-bg">
      <!-- Header -->
      <header class="d-flex justify-between align-center p-3 border-bottom backdrop-blur">
         <div class="d-flex align-center gap-2">
             <h3 class="m-0">{{ selectedCategoryName }}</h3>
             <span class="badge badge-secondary badge-pill">{{ products.length }}</span>
         </div>
         <div class="d-flex gap-2">
            <select v-model="selectedDealId" class="form-select" style="width: 200px;">
               <option value="">Проект для добавления</option>
               <option v-for="deal in deals" :key="deal.id" :value="deal.id">{{ deal.title }}</option>
            </select>
            <button class="btn btn-primary" @click="showCreateProductModal = true">
               <i class="fas fa-plus mr-2"></i> Товар
            </button>
         </div>
      </header>
      
      <!-- Product Table -->
      <div class="flex-grow-1 overflow-auto">
         <div v-if="loading" class="p-4">
            <SkeletonLoader height="50px" v-for="i in 8" :key="i" class="mb-2" />
         </div>

         <div v-else-if="products.length === 0" class="h-100 d-flex flex-column align-center justify-center text-muted">
            <i class="fas fa-box-open fa-3x mb-3 opacity-25"></i>
            <p>Нет товаров в этой категории</p>
         </div>

         <table v-else class="table table-hover m-0 w-100 catalog-table">
            <thead class="sticky-top bg-surface-blur">
               <tr>
                  <th class="pl-4 catalog-name-col">Наименование</th>
                  <th style="min-width: 150px; width: 150px;">Цена</th>
                  <th class="text-right pr-4">Действия</th>
               </tr>
            </thead>
            <tbody>
               <tr v-for="product in products" :key="product.id" class="align-middle">
                  <td class="pl-4 catalog-name-cell">
                     <div class="fw-600 text-dark text-truncate">{{ product.name }}</div>
                  </td>
                  <td>
                     <span class="font-mono fs-1-1">{{ formatCurrency(product.base_price) }}</span>
                  </td>
                  <td class="text-right pr-4">
                     <div class="d-flex justify-end gap-2">
                        <button class="btn btn-icon btn-sm" @click="editProduct(product)" title="Изменить">
                           <i class="fas fa-pen text-muted"></i>
                        </button>
                        <button v-if="selectedDealId" class="btn btn-icon btn-sm text-success" @click="quickAddToDeal(product)" title="Добавить в проект">
                           <i class="fas fa-plus-circle fa-lg"></i>
                        </button>
                        <button class="btn btn-icon btn-sm text-danger" @click="deleteProduct(product)" title="Удалить">
                           <i class="fas fa-trash"></i>
                        </button>
                     </div>
                  </td>
               </tr>
            </tbody>
         </table>
      </div>
    </main>

    <!-- Modals (Keep existing ones) -->
    <!-- Create Category Modal -->
    <div v-if="showCreateCategoryModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="m-0">{{ isEditingCategory ? 'Редактировать категорию' : 'Новая категория' }}</h3>
          <button class="btn btn-sm btn-secondary" @click="closeModal"><i class="fas fa-times"></i></button>
        </div>
        <form @submit.prevent="saveCategory" class="modal-body">
           <div class="form-group mb-3">
             <label class="small text-muted mb-1">Название</label>
             <input v-model="categoryForm.name" type="text" class="form-control" required>
           </div>
           <div class="form-group mb-3">
             <label class="small text-muted mb-1">Описание</label>
             <textarea v-model="categoryForm.description" class="form-control" rows="3"></textarea>
           </div>
           <div class="form-group mb-3">
             <label class="small text-muted mb-1">Родительская категория</label>
             <select v-model="categoryForm.parent_id" class="form-select">
               <option value="">Нет родителя</option>
               <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
             </select>
           </div>
           <div class="modal-footer">
             <button type="button" class="btn btn-secondary" @click="closeModal">Отмена</button>
             <button type="submit" class="btn btn-primary">Сохранить</button>
           </div>
        </form>
      </div>
    </div>

    <!-- Create Product Modal -->
    <div v-if="showCreateProductModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="m-0">{{ isEditingProduct ? 'Редактировать товар' : 'Новый товар' }}</h3>
          <button class="btn btn-sm btn-secondary" @click="closeModal"><i class="fas fa-times"></i></button>
        </div>
        <form @submit.prevent="saveProduct" class="modal-body">
           <div class="form-group mb-3">
             <label class="small text-muted mb-1">Наименование *</label>
             <input v-model="productForm.name" type="text" class="form-control" required>
           </div>
           <div class="form-group mb-3">
             <label class="small text-muted mb-1">Базовая стоимость (₽)</label>
             <input v-model.number="productForm.base_price" type="number" class="form-control" step="0.01">
           </div>
           <div class="form-group mb-3">
             <label class="small text-muted mb-1">Категория</label>
             <select v-model="productForm.category_id" class="form-select">
               <option value="">Без категории</option>
               <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
             </select>
           </div>
           <div class="modal-footer">
             <button type="button" class="btn btn-secondary" @click="closeModal">Отмена</button>
             <button type="submit" class="btn btn-primary">Сохранить</button>
           </div>
        </form>
      </div>
    </div>

    <!-- Quick Add Modal -->
    <div v-if="showQuickAddModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
           <h3 class="m-0">Добавить в проект</h3>
           <button class="btn btn-sm btn-secondary" @click="closeModal"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
           <div class="mb-4">
              <div class="text-muted small mb-1">Товар</div>
              <strong class="d-block text-lg">{{ quickAddProduct?.name }}</strong>
              <div class="text-primary mt-1">{{ formatCurrency(quickAddProduct?.base_price) }}</div>
           </div>
           <div class="d-flex gap-3 mb-3">
              <div class="form-group w-50">
                 <label class="small text-muted mb-1">Количество</label>
                 <input v-model.number="quickAddForm.quantity" type="number" class="form-control" step="0.01">
              </div>
              <div class="form-group w-50">
                 <label class="small text-muted mb-1">Скидка (%)</label>
                 <input v-model.number="quickAddForm.discount_percent" type="number" class="form-control">
              </div>
           </div>
           <div class="d-flex justify-between align-center mt-4 p-3 bg-light rounded-3">
              <span class="text-muted">Итого:</span>
              <strong style="font-size: 1.4rem;" class="text-primary">{{ formatCurrency(calculateTotal()) }}</strong>
           </div>
        </div>
        <div class="modal-footer">
           <button type="button" class="btn btn-secondary" @click="closeModal">Отмена</button>
           <button type="button" class="btn btn-success" @click="confirmQuickAdd">Добавить</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import { api } from '../services/api'
import SkeletonLoader from '../components/ui/SkeletonLoader.vue'
import { useCategoriesStore } from '../stores/categories'
import { useProductsStore } from '../stores/products'

export default {
  name: 'Catalog',
  components: { SkeletonLoader },
  setup() {
    const categoriesStore = useCategoriesStore()
    const productsStore = useProductsStore()
    const deals = ref([])
    const categories = ref([])
    const products = ref([])
    const dealProducts = ref([])
    const loading = ref(false)
    const selectedDealId = ref('')
    const selectedCategoryId = ref('')
    const searchQuery = ref('')

    const searchTimeout = ref(null)

    const selectedCategoryName = computed(() => {
       if (!selectedCategoryId.value) return 'Все категории'
       const cat = categories.value.find(c => c.id === selectedCategoryId.value)
       return cat ? cat.name : 'Категория'
    })

    // Modals
    const showCreateCategoryModal = ref(false)
    const showCreateProductModal = ref(false)
    const showQuickAddModal = ref(false)
    const isEditingCategory = ref(false)
    const isEditingProduct = ref(false)

    // Forms
    const categoryForm = ref({
      name: '',
      description: '',
      parent_id: '',
      sort_order: 0
    })

    const productForm = ref({
      name: '',
      base_price: 0,
      category_id: ''
    })

    const quickAddForm = ref({
      quantity: 1,
      discount_percent: 0
    })

    const quickAddProduct = ref(null)

    const loadDeals = async () => {
      try {
        const data = await api.deals.list()
        deals.value = data
      } catch (error) {
        console.error('Error loading deals:', error)
      }
    }

    const loadCategories = async () => {
      try {
        await categoriesStore.refresh()
        categories.value = categoriesStore.items
      } catch (error) {
        console.error('Error loading categories:', error)
      }
    }

    const loadProducts = async () => {
      loading.value = true
      try {
        const params = {}
        if (selectedCategoryId.value) {
          params.category_id = selectedCategoryId.value
        }
        if (searchQuery.value) {
          params.search = searchQuery.value
        }

        const pageSize = 200
        let skip = 0
        let page = 0
        const allProducts = []

        while (true) {
          const data = await api.products.list({ ...params, skip, limit: pageSize })
          const batch = Array.isArray(data) ? data : []
          allProducts.push(...batch)
          if (batch.length < pageSize) {
            break
          }
          skip += pageSize
          page += 1
          if (page > 50) {
            break
          }
        }

        products.value = allProducts
      } catch (error) {
        console.error('Error loading products:', error)
        products.value = []
      } finally {
        loading.value = false
      }
    }

    const loadDealProducts = async () => {
      if (!selectedDealId.value) {
        dealProducts.value = []
        return
      }

      try {
        const data = await api.products.listDealProducts(selectedDealId.value)
        dealProducts.value = data
      } catch (error) {
        console.error('Error loading deal products:', error)
        dealProducts.value = []
      }
    }

    const debouncedSearch = () => {
      clearTimeout(searchTimeout.value)
      searchTimeout.value = setTimeout(() => {
        loadProducts()
      }, 300)
    }

    const selectCategory = (category) => {
      if (!category) {
        selectedCategoryId.value = ''
        loadProducts()
        return
      }
      selectedCategoryId.value = typeof category === 'string' ? category : category.id
      loadProducts()
    }

    const clearFilters = () => {
      searchQuery.value = ''
      selectedCategoryId.value = ''
      loadProducts()
    }

    const saveCategory = async () => {
      if (!categoryForm.value.name.trim()) {
        alert('Название категории обязательно')
        return
      }

      try {
        if (isEditingCategory.value) {
          await api.categories.update(categoryForm.value.id, categoryForm.value)
        } else {
          await api.categories.create(categoryForm.value)
        }

        await loadCategories()
        closeModal()
        alert(isEditingCategory.value ? 'Категория обновлена!' : 'Категория создана!')
      } catch (error) {
        console.error('Error saving category:', error)
        alert('Ошибка сохранения категории')
      }
    }

    const editCategory = (category) => {
      categoryForm.value = { ...category }
      isEditingCategory.value = true
      showCreateCategoryModal.value = true
    }

    const saveProduct = async () => {
      if (!productForm.value.name.trim()) {
        alert('Название товара обязательно')
        return
      }

      try {
        const payload = {
          name: productForm.value.name,
          base_price: productForm.value.base_price,
          category_id: productForm.value.category_id || null
        }

        if (isEditingProduct.value) {
          await api.products.update(productForm.value.id, payload)
        } else {
          await api.products.create(payload)
        }

        await loadProducts()
        await productsStore.refresh()
        closeModal()
        alert(isEditingProduct.value ? 'Товар обновлен!' : 'Товар создан!')
      } catch (error) {
        console.error('Error saving product:', error)
        alert('Ошибка сохранения товара: ' + (error.response?.data?.detail || error.message))
      }
    }

    const editProduct = (product) => {
      productForm.value = { ...product }
      isEditingProduct.value = true
      showCreateProductModal.value = true
    }

    const deleteProduct = async (product) => {
      if (!confirm(`Удалить товар "${product.name}"?`)) {
        return
      }

      try {
        await api.products.remove(product.id)
        productsStore.removeLocal(product.id)
        await loadProducts()
      } catch (error) {
        console.error('Error deleting product:', error)
        alert('Ошибка удаления товара')
      }
    }

    const quickAddToDeal = (product) => {
      if (!selectedDealId.value) {
        alert('Сначала выберите проект')
        return
      }

      quickAddProduct.value = product
      quickAddForm.value = {
        quantity: 1,
        discount_percent: 0
      }
      showQuickAddModal.value = true
    }

    const calculateTotal = () => {
      if (!quickAddProduct.value) return 0
      const subtotal = quickAddForm.value.quantity * quickAddProduct.value.base_price
      const discount = subtotal * quickAddForm.value.discount_percent / 100
      return subtotal - discount
    }

    const confirmQuickAdd = async () => {
      try {
        await api.products.quickAddToDeal(selectedDealId.value, quickAddProduct.value.id, {
          quantity: quickAddForm.value.quantity,
          discount_percent: quickAddForm.value.discount_percent
        })

        await loadDealProducts()
        closeModal()
        alert('Товар добавлен в проект!')
      } catch (error) {
        console.error('Error adding product to deal:', error)
        alert('Ошибка добавления товара в проект')
      }
    }

    const removeFromDeal = async (dealProduct) => {
      if (!confirm('Удалить товар из проекта?')) {
        return
      }

      try {
        await api.products.removeDealProduct(dealProduct.id)
        await loadDealProducts()
      } catch (error) {
        console.error('Error removing product from deal:', error)
        alert('Ошибка удаления товара из проекта')
      }
    }

    const closeModal = () => {
      showCreateCategoryModal.value = false
      showCreateProductModal.value = false
      showQuickAddModal.value = false
      isEditingCategory.value = false
      isEditingProduct.value = false

      categoryForm.value = {
        name: '',
        description: '',
        parent_id: '',
        sort_order: 0
      }

      productForm.value = {
        name: '',
        base_price: 0,
        category_id: ''
      }
    }

    const formatCurrency = (value) => {
      if (value === null || value === undefined) return '0 ₽'
      return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 0
      }).format(value)
    }

    const getCategoryName = (categoryId) => {
      const category = categories.value.find(c => c.id === categoryId)
      return category ? category.name : 'Неизвестная категория'
    }

    const getProductName = (productId) => {
      const product = products.value.find(p => p.id === productId)
      return product ? product.name : 'Неизвестный товар'
    }

    const getStatusClass = (status) => {
      const classes = {
        planned: 'badge-warning',
        ordered: 'badge-info',
        delivered: 'badge-primary',
        installed: 'badge-success'
      }
      return classes[status] || 'badge-secondary'
    }

    const getStatusText = (status) => {
      const texts = {
        planned: 'Запланирован',
        ordered: 'Заказан',
        delivered: 'Доставлен',
        installed: 'Установлен'
      }
      return texts[status] || status
    }
    
    // Watch for deal selection changes
    watch(selectedDealId, (newVal) => {
       if(newVal) loadDealProducts() // using watch as standard practice or change event
       else dealProducts.value = []
    })

    onMounted(async () => {
      await Promise.all([
        loadDeals(),
        loadCategories(),
        loadProducts()
      ])
    })

    return {
      deals,
      categories,
      products,
      dealProducts,
      loading,
      selectedDealId,
      selectedCategoryId,
      searchQuery,
      showCreateCategoryModal,
      showCreateProductModal,
      showQuickAddModal,
      isEditingCategory,
      isEditingProduct,
      categoryForm,
      productForm,
      quickAddForm,
      quickAddProduct,
      loadProducts,
      loadDealProducts,
      debouncedSearch,
      selectCategory,
      clearFilters,
      saveCategory,
      editCategory,
      saveProduct,
      editProduct,
      deleteProduct,
      quickAddToDeal,
      calculateTotal,
      confirmQuickAdd,
      removeFromDeal,
      closeModal,
      formatCurrency,
      getCategoryName,
      getProductName,
      getStatusClass,
      getStatusClass,
      getStatusText,
      selectedCategoryName
    }
  }
}
</script>


<style scoped>
.catalog-sidebar {
  width: 360px;
  min-width: 360px;
  max-width: 360px;
  flex: 0 0 360px;
  background-color: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(25px);
  z-index: 2;
  transition: width 0.3s ease;
}

[data-theme="dark"] .catalog-sidebar {
  background-color: rgba(30,30,30, 0.85);
  border-right-color: rgba(255,255,255,0.1) !important;
}

.nav-item {
  transition: all 0.2s ease;
}

.nav-item:hover {
  background-color: rgba(0,0,0,0.05);
}

.nav-item.active-category {
  background-color: var(--md-sys-color-primary);
  color: #fff;
}

.nav-item.active-category .text-primary {
  color: #fff !important;
  opacity: 1 !important;
}

.nav-item.active-category .text-muted {
  color: rgba(255,255,255,0.8) !important;
}

.catalog-view {
  background: rgba(255, 255, 255, 0.92);
}

[data-theme="dark"] .catalog-view {
  background: rgba(16, 18, 24, 0.92);
}

.glass-panel-bg {
  background-color: rgba(255, 255, 255, 0.7);
}

[data-theme="dark"] .glass-panel-bg {
  background-color: rgba(16, 18, 24, 0.7);
}

.glass-panel-bg > header {
  background: rgba(255, 255, 255, 0.7);
}

[data-theme="dark"] .glass-panel-bg > header {
  background: rgba(20, 24, 33, 0.72);
}

.btn-icon-only {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sticky-top {
  position: sticky;
  top: 0;
  z-index: 10;
}

.bg-surface-blur {
  background-color: rgba(255,255,255,0.82);
  backdrop-filter: blur(12px);
}

[data-theme="dark"] .bg-surface-blur {
  background-color: rgba(30,30,30,0.8);
}

.hover-opacity-100:hover {
  opacity: 1 !important;
}

.fs-1-1 { font-size: 1.1em; }

/* Mobile Responsive */
@media (max-width: 992px) {
  .catalog-sidebar {
    width: 280px;
    min-width: 280px;
    max-width: 280px;
    flex: 0 0 280px;
  }
}

@media (max-width: 768px) {
  .catalog-view {
    flex-direction: column;
  }
  
  .catalog-sidebar {
    width: 100%;
    min-width: 100%;
    max-width: 100%;
    flex: 0 0 auto;
    max-height: 40vh;
    border-right: none !important;
    border-bottom: 1px solid var(--md-sys-color-outline-variant);
  }
  
  .catalog-sidebar h2 {
    font-size: 1.1rem !important;
  }
  
  main header {
    flex-direction: column;
    gap: 8px;
    padding: 10px !important;
  }
  
  main header .d-flex.gap-2 {
    width: 100%;
  }
  
  main header .form-select,
  main header .btn {
    flex: 1;
  }
}
</style>


