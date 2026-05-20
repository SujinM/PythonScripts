import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('@/layouts/DefaultLayout.vue'),
      children: [
        { path: '',           name: 'dashboard',  component: () => import('@/pages/Dashboard.vue') },
        { path: 'price',      name: 'price',      component: () => import('@/pages/PriceCalc.vue') },
        { path: 'returns',    name: 'returns',    component: () => import('@/pages/ReturnsCalc.vue') },
        { path: 'risk',       name: 'risk',       component: () => import('@/pages/RiskCalc.vue') },
        { path: 'position',   name: 'position',   component: () => import('@/pages/PositionCalc.vue') },
        { path: 'options',    name: 'options',    component: () => import('@/pages/OptionsCalc.vue') },
        { path: 'percent',    name: 'percent',    component: () => import('@/pages/PercentCalc.vue') },
        { path: 'history',    name: 'history',    component: () => import('@/pages/History.vue') },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

export default router
