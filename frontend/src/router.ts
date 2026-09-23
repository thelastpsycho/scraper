import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from './views/DashboardView.vue'
import InventoryCollectionView from './views/InventoryCollectionView.vue'
import YieldManagementView from './views/YieldManagementView.vue'
import InventoryDataView from './views/InventoryDataView.vue'
import AllotmentManagementView from './views/AllotmentManagementView.vue'
import BarPricingView from './views/BarPricingView.vue'
import AutomationPipelineView from './views/AutomationPipelineView.vue'
import InventoryAssistantView from './views/InventoryAssistantView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: DashboardView
    },
    {
      path: '/scraping',
      name: 'scraping',
      component: InventoryCollectionView
    },
    {
      path: '/yielder',
      name: 'yielder',
      component: YieldManagementView
    },
    {
      path: '/data',
      name: 'data',
      component: InventoryDataView
    },
    {
      path: '/allotment',
      name: 'allotment',
      component: AllotmentManagementView
    },
    {
      path: '/bar-calculator',
      name: 'bar-calculator',
      component: BarPricingView
    },
    {
      path: '/pipeline',
      name: 'pipeline',
      component: AutomationPipelineView
    },
    {
      path: '/chat',
      name: 'chat',
      component: InventoryAssistantView
    }
  ]
})

export default router 