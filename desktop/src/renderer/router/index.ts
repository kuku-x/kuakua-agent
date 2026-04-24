import { createRouter, createWebHashHistory } from 'vue-router'
import DailySummary from '@/views/DailySummary.vue'
import ChatCompanion from '@/views/ChatCompanion.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: DailySummary },
    { path: '/chat', component: ChatCompanion },
    { path: '/settings', redirect: '/' },
  ],
})

export default router
