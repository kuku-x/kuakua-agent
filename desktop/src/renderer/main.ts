import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAppStore } from '@/store/app'
import '@/styles/vars.css'
import '@/styles/base.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

app.config.errorHandler = (error) => {
  const appStore = useAppStore(pinia)
  appStore.setGlobalError(error instanceof Error ? error.message : '发生未知错误')
}

window.addEventListener('unhandledrejection', (event) => {
  const appStore = useAppStore(pinia)
  const reason = event.reason
  appStore.setGlobalError(reason instanceof Error ? reason.message : '异步操作失败')
})

app.mount('#app')
