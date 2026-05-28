<template>



  <div v-if="isOpen" class="palette-overlay" @click="close">



    <div class="palette-container" @click.stop>



      <div class="palette-search">



        <i class="fas fa-search search-icon" :class="{'fa-spin': isSearching}"></i>



        <input 



          ref="searchInput"



          v-model="query"



          type="text" 



          placeholder="Поиск сделок, контрагентов или команд..."



          @keydown.down.prevent="navigateDown"



          @keydown.up.prevent="navigateUp"



          @keydown.enter.prevent="execute"



          @keydown.esc="close"



          @input="onInput"



        >



        <div class="palette-shortcut">ESC</div>



      </div>



      



      <div class="palette-results" v-if="allItems.length">



        <div 



          v-for="(item, index) in allItems" 



          :key="item.uniqueId"



          class="palette-item"



          :class="{ 'is-selected': index === selectedIndex }"



          @click="selectItem(item)"



          @mouseover="selectedIndex = index"



        >



          <div class="item-icon">



            <i :class="item.icon"></i>



          </div>



          <div class="item-content">



            <div class="item-label">



                {{ item.label }}



                <!-- Tag for search matches -->



                <span v-if="item.isRemote" class="remote-tag">{{ item.type }}</span>



            </div>



            <div class="item-desc" v-if="item.desc">{{ item.desc }}</div>



          </div>



          <div class="item-type" v-if="!item.isRemote">{{ item.type }}</div>



        </div>



      </div>



      



      <div v-else class="palette-empty">



        <span v-if="isSearching">Searching...</span>



        <span v-else>No results found</span>



      </div>



      



      <div class="palette-footer">



        <div class="key-hint"><span>Enter</span> select</div>



        <div class="key-hint"><span>Up/Down</span> navigate</div>



      </div>



    </div>



  </div>



</template>







<script>



import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'



import { useRouter } from 'vue-router'



import { api } from '../../services/api'



import { hasSectionAccess } from '../../utils/permissions'







export default {



  name: 'CommandPalette',



  setup() {



    const router = useRouter()



    const isOpen = ref(false)



    const query = ref('')



    const selectedIndex = ref(0)



    const searchInput = ref(null)



    const isSearching = ref(false)



    const fetchedItems = ref([])



    let searchTimeout = null







        const staticItems = [
      // Navigation
      { id: 'home', label: 'Главная', desc: 'Переход на главную страницу', icon: 'fas fa-home', type: 'Перейти', action: () => router.push('/') },
      { id: 'projects', label: 'Сделки', desc: 'Список всех сделок', icon: 'fas fa-project-diagram', type: 'Перейти', section: 'projects', action: () => router.push('/projects') },
      { id: 'tasks', label: 'Задачи', desc: 'Управление задачами', icon: 'fas fa-tasks', type: 'Перейти', section: 'tasks', action: () => router.push('/tasks') },
      { id: 'users', label: 'Пользователи', desc: 'Управление пользователями', icon: 'fas fa-user-cog', type: 'Перейти', section: 'users', action: () => router.push('/users') },
      { id: 'roles', label: 'Роли и права', desc: 'Настройка ролей и прав', icon: 'fas fa-shield-alt', type: 'Перейти', section: 'roles', action: () => router.push('/roles') },
      { id: 'gantt', label: 'План-график', desc: 'Диаграмма Ганта по сделкам', icon: 'fas fa-chart-gantt', type: 'Перейти', section: 'projects', action: () => router.push('/gantt') },
      { id: 'finance', label: 'Финансы', desc: 'Финансовые показатели', icon: 'fas fa-money-bill-wave', type: 'Перейти', section: 'finance', action: () => router.push('/finance') },
      { id: 'treasury', label: 'Казначейство', desc: 'Управление платежами', icon: 'fas fa-landmark', type: 'Перейти', section: 'treasury', action: () => router.push('/treasury') },
      { id: 'catalog', label: 'Каталог', desc: 'Каталог товаров и услуг', icon: 'fas fa-boxes', type: 'Перейти', section: 'catalog', action: () => router.push('/catalog') },
      { id: 'files_catalog', label: 'Файлы', desc: 'Каталог файлов на Яндекс.Диске', icon: 'fas fa-hdd', type: 'Перейти', section: 'files_catalog', action: () => router.push('/files-catalog') },
      { id: 'mail', label: 'Почта', desc: 'Входящие и исходящие письма', icon: 'fas fa-at', type: 'Перейти', section: 'mail', action: () => router.push('/mail') },
      
      // Actions
      { id: 'theme', label: 'Переключить тему', desc: 'Светлая / тёмная', icon: 'fas fa-adjust', type: 'Действие', action: () => document.querySelector('.sidebar button.w-100')?.click() },
      { id: 'create_project', label: 'Новая сделка', desc: 'Создать новую сделку', icon: 'fas fa-plus', type: 'Действие', action: () => { router.push('/projects'); setTimeout(() => document.querySelector('.btn-primary')?.click(), 500) } },
    ]

    const allItems = computed(() => {



       // Filter static items



       const q = query.value.toLowerCase()



       const filteredStatic = staticItems.filter(item =>



         (!item.section || hasSectionAccess(item.section)) &&



         (!q ||



           item.label.toLowerCase().includes(q) ||



           (item.desc && item.desc.toLowerCase().includes(q)))



       ).map(i => ({ ...i, uniqueId: `static_${i.id}`, isRemote: false }))







       // Combine with fetched items



       return [...filteredStatic, ...fetchedItems.value]



    })







    const onInput = () => {



       isSearching.value = true



       clearTimeout(searchTimeout)



       searchTimeout = setTimeout(searchApi, 300)



    }







    const searchApi = async () => {



       if (!query.value || query.value.length < 2) {



          fetchedItems.value = []



          isSearching.value = false



          return



       }







       try {



          const canSearchProjects = hasSectionAccess('projects')



          const canSearchCompanies = hasSectionAccess('companies')



          if (!canSearchProjects && !canSearchCompanies) {



             fetchedItems.value = []



             isSearching.value = false



             return



          }







          let projectsRes = { data: [] }



          let companiesRes = { data: [] }



          const tasks = []



          if (canSearchProjects) {



            tasks.push(



              api.deals.list({ search: query.value }).then((data) => {



                projectsRes = { data }



              })



            )



          }



          if (canSearchCompanies) {



            tasks.push(



              api.companies.list({ search: query.value }).then((data) => {



                companiesRes = { data }



              })



            )



          }



          await Promise.all(tasks)







          const projects = projectsRes.data.map(p => ({



             uniqueId: `project_${p.id}`,



             label: p.title,



             desc: p.obj_name || 'Объект',



             icon: 'fas fa-project-diagram',



             type: 'Сделка',



             isRemote: true,



             action: () => router.push(`/projects/${p.id}`)



          }))







          const companies = companiesRes.data.map(c => ({



            uniqueId: `company_${c.id}`,



            label: c.name,



            desc: c.inn ? `ИНН: ${c.inn}` : 'Контрагент',



            icon: 'fas fa-building',



            type: 'Контрагент',



            isRemote: true,



            action: () => router.push(`/companies`) // Ideally navigate to detail if exists



          }))







          fetchedItems.value = [...projects, ...companies]



       } catch (error) {



          console.error('Search error:', error)



          // Don't clear fetchedItems on error to avoid flickering, just stop spinner



       } finally {



          isSearching.value = false



          selectedIndex.value = 0 // Reset selection to top



       }



    }







    const open = () => {



      isOpen.value = true



      query.value = ''



      fetchedItems.value = []



      selectedIndex.value = 0



      nextTick(() => searchInput.value?.focus())



    }







    const close = () => {



      isOpen.value = false



    }







    const toggle = () => isOpen.value ? close() : open()







    const navigateDown = () => {



      if (selectedIndex.value < allItems.value.length - 1) selectedIndex.value++



    }







    const navigateUp = () => {



      if (selectedIndex.value > 0) selectedIndex.value--



    }







    const execute = () => {



      const item = allItems.value[selectedIndex.value]



      if (item) {



        selectItem(item)



      }



    }







    const selectItem = (item) => {



      item.action()



      close()



    }







    const handleKeydown = (e) => {



      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {



        e.preventDefault()



        toggle()



      }



    }







    onMounted(() => {



      window.addEventListener('keydown', handleKeydown)



    })







    onUnmounted(() => {



      window.removeEventListener('keydown', handleKeydown)



    })



    



    // Reset selection when query changes



    watch(query, () => selectedIndex.value = 0)







    return {



      isOpen,



      query,



      allItems,



      selectedIndex,



      searchInput,



      isSearching,



      open,



      close,



      navigateDown,



      navigateUp,



      execute,



      selectItem,



      onInput



    }



  }



}



</script>







<style scoped>



.palette-overlay {



  position: fixed;



  inset: 0;



  background: rgba(0, 0, 0, 0.5);



  backdrop-filter: blur(2px);



  z-index: 99999;



  display: flex;



  justify-content: center;



  padding-top: 100px;



  animation: fadeIn 0.1s ease-out;



}







.palette-container {



  width: 100%;



  max-width: 600px;



  background: var(--md-sys-color-surface);



  border-radius: 16px;



  box-shadow: 0 20px 40px rgba(0,0,0,0.3);



  overflow: hidden;



  border: 1px solid var(--md-sys-color-outline-variant);



  display: flex;



  flex-direction: column;



  max-height: 500px;



  animation: slideDown 0.2s cubic-bezier(0.16, 1, 0.3, 1);



}







.palette-search {



  display: flex;



  align-items: center;



  padding: 16px;



  border-bottom: 1px solid var(--md-sys-color-outline-variant);



  gap: 12px;



}







.search-icon {



  color: var(--md-sys-color-on-surface-variant);



  font-size: 1.2rem;



}







.palette-search input {



  border: none;



  background: none;



  font-size: 1.1rem;



  width: 100%;



  color: var(--md-sys-color-on-surface);



  outline: none;



}







.palette-shortcut {



  font-size: 0.75rem;



  background: var(--md-sys-color-surface-variant);



  padding: 2px 6px;



  border-radius: 4px;



  color: var(--md-sys-color-on-surface-variant);



  border: 1px solid var(--md-sys-color-outline-variant);



}







.palette-results {



  overflow-y: auto;



  padding: 8px;



  max-height: 400px;



}







.palette-empty {



  padding: 32px;



  text-align: center;



  color: var(--md-sys-color-on-surface-variant);



}







.palette-item {



  display: flex;



  align-items: center;



  gap: 12px;



  padding: 12px;



  border-radius: 8px;



  cursor: pointer;



  transition: all 0.1s;



  color: var(--md-sys-color-on-surface);



}







.palette-item.is-selected {



  background: var(--md-sys-color-primary-container);



  color: var(--md-sys-color-on-primary-container);



}







.item-icon {



  width: 24px;



  text-align: center;



  font-size: 1rem;



  color: var(--md-sys-color-on-surface-variant);



}







.is-selected .item-icon {



  color: var(--md-sys-color-primary);



}







.item-content {



  flex-grow: 1;



}







.item-label {



  font-weight: 500;



  display: flex;



  align-items: center;



  gap: 8px;



}







.remote-tag {



    font-size: 0.7rem;



    padding: 2px 6px;



    background: var(--md-sys-color-surface-variant);



    border-radius: 4px;



    color: var(--md-sys-color-primary);



}



.is-selected .remote-tag {



    background: rgba(255,255,255,0.2);



    color: var(--md-sys-color-on-primary-container);



}







.item-desc {



  font-size: 0.85rem;



  color: var(--md-sys-color-on-surface-variant);



  opacity: 0.8;



}







.is-selected .item-desc {



  color: var(--md-sys-color-on-primary-container);



}







.item-type {



  font-size: 0.75rem;



  opacity: 0.6;



}







.palette-footer {



  padding: 8px 16px;



  background: var(--md-sys-color-surface-variant);



  display: flex;



  gap: 16px;



  font-size: 0.75rem;



  color: var(--md-sys-color-on-surface-variant);



  border-top: 1px solid var(--md-sys-color-outline-variant);



}







.key-hint span {



  background: rgba(0,0,0,0.1);



  padding: 2px 4px;



  border-radius: 4px;



  margin-right: 4px;



}







@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }



@keyframes slideDown { from { transform: translateY(-20px) scale(0.98); } to { transform: translateY(0) scale(1); } }



</style>















