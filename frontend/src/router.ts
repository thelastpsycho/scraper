import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import Scraping from './views/Scraping.vue'
import Yielder from './views/Yielder.vue'
import Data from './views/Data.vue'
import Allotment from './views/Allotment.vue'
import Chat from './views/Chat.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home
    },
    {
      path: '/scraping',
      name: 'scraping',
      component: Scraping
    },
    {
      path: '/yielder',
      name: 'yielder',
      component: Yielder
    },
    {
      path: '/data',
      name: 'data',
      component: Data
    },
    {
      path: '/allotment',
      name: 'allotment',
      component: Allotment
    },
    {
      path: '/chat',
      name: 'chat',
      component: Chat
    }
  ]
})

export default router 