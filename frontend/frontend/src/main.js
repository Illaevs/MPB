import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import { setupHttpInterceptors } from './services/http'

import './assets/styles/main.css'
import '@fortawesome/fontawesome-free/css/all.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

setupHttpInterceptors(pinia)

app.mount('#app')
