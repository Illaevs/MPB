import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import { setupHttpInterceptors } from './services/http'
import modalCloseDirective from './directives/modalClose'

import './assets/styles/main.css'
import '@fortawesome/fontawesome-free/css/all.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// v-modal-close="closeFn" — безопасная замена @click.self на overlay
// модалок. Не закрывает при drag-selection текста за пределы модалки.
app.directive('modal-close', modalCloseDirective)

setupHttpInterceptors(pinia)

app.mount('#app')
