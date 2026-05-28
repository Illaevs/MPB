import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const devPort = Number(env.VITE_DEV_PORT || 3000)
  const proxyTarget = env.VITE_API_PROXY_TARGET || 'http://localhost:8000'

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
        vuedraggable: fileURLToPath(new URL('./node_modules/vuedraggable/src/vuedraggable.js', import.meta.url))
      }
    },
    server: {
      port: devPort,
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
          secure: false
        },
        '/static': {
          target: proxyTarget,
          changeOrigin: true,
          secure: false
        }
      }
    },
    build: {
      // Чанк-предупреждение поднимаем — у нас крупные views (Tasks/ProjectDetail
      // по 8K+ LOC) и тяжёлые библиотеки (apexcharts, dhtmlx-gantt, tiptap,
      // docxtemplater). После декомпозиции монолитов (см. roadmap Phase 5)
      // лимит можно будет вернуть к дефолту.
      chunkSizeWarningLimit: 1200,
      rollupOptions: {
        output: {
          // Группируем тяжёлые вендоры в отдельные чанки, чтобы они
          // кешировались независимо от пользовательского кода и не раздували
          // главный bundle. Vue/Pinia/router грузятся всегда —
          // их выносим в "vendor-vue". Остальные библиотеки изолированы
          // и подтянутся только на тех страницах, где их реально используют.
          manualChunks(id) {
            if (!id.includes('node_modules')) return undefined
            if (/[\\/]node_modules[\\/](vue|@vue|vue-router|pinia)[\\/]/.test(id)) {
              return 'vendor-vue'
            }
            if (/[\\/]node_modules[\\/]axios[\\/]/.test(id)) {
              return 'vendor-axios'
            }
            if (/[\\/]node_modules[\\/](apexcharts|vue3-apexcharts)[\\/]/.test(id)) {
              return 'vendor-charts'
            }
            if (/[\\/]node_modules[\\/]dhtmlx-gantt[\\/]/.test(id)) {
              return 'vendor-gantt'
            }
            if (/[\\/]node_modules[\\/]@tiptap[\\/]/.test(id)) {
              return 'vendor-tiptap'
            }
            if (/[\\/]node_modules[\\/](docx-preview|docxtemplater|pizzip|file-saver)[\\/]/.test(id)) {
              return 'vendor-docs'
            }
            if (/[\\/]node_modules[\\/](dompurify|qrcode|vuedraggable)[\\/]/.test(id)) {
              return 'vendor-misc'
            }
            return 'vendor'
          }
        }
      }
    }
  }
})
