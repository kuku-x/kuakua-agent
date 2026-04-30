import { createRouter, createWebHashHistory } from 'vue-router'
import DailySummary from '@/views/DailySummary.vue'
import ChatCompanion from '@/views/ChatCompanion.vue'
import NightlySummary from '@/views/NightlySummary.vue'
import WeeklyReview from '@/views/WeeklyReview.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: DailySummary },
    { path: '/chat', component: ChatCompanion },
    { path: '/nightly-summary', component: NightlySummary },
    { path: '/weekly-review', component: WeeklyReview },
    { path: '/settings', redirect: '/' },
  ],
})

export default router
