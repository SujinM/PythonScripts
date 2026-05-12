import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

// Lazy-loaded page imports for code splitting
const DefaultLayout = () => import('@/layouts/DefaultLayout.vue')
const AuthLayout    = () => import('@/layouts/AuthLayout.vue')

const routes: RouteRecordRaw[] = [
  // ─── Auth Routes ─────────────────────────────────────────────────────────
  {
    path: '/login',
    component: AuthLayout,
    meta: { requiresGuest: true },
    children: [
      {
        path: '',
        name: 'login',
        component: () => import('@/pages/Login.vue'),
        meta: { title: 'Sign In' },
      },
    ],
  },

  // ─── App Routes (require auth) ────────────────────────────────────────────
  {
    path: '/',
    component: DefaultLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'dashboard',
        component: () => import('@/pages/Dashboard.vue'),
        meta: { title: 'Dashboard' },
      },
      {
        path: 'instruments',
        name: 'instruments',
        component: () => import('@/pages/Instruments.vue'),
        meta: { title: 'Instruments' },
      },
      {
        path: 'instruments/:symbol',
        name: 'instrument-detail',
        component: () => import('@/pages/InstrumentDetail.vue'),
        meta: { title: 'Instrument Detail' },
        props: true,
      },
      {
        path: 'statistics',
        name: 'statistics',
        component: () => import('@/pages/Statistics.vue'),
        meta: { title: 'Statistics' },
      },
      {
        path: 'sync',
        name: 'sync',
        component: () => import('@/pages/SyncManagement.vue'),
        meta: { title: 'Sync Management' },
      },
      {
        path: 'settings',
        name: 'settings',
        component: () => import('@/pages/Settings.vue'),
        meta: { title: 'Settings' },
      },
    ],
  },

  // ─── 404 ─────────────────────────────────────────────────────────────────
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/pages/NotFound.vue'),
    meta: { title: 'Not Found' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

// ─── Navigation Guards ────────────────────────────────────────────────────────

router.beforeEach((to, _from, next) => {
  // Update document title
  const title = to.meta.title as string | undefined
  document.title = title ? `${title} — eToro Dashboard` : 'eToro Dashboard'

  const authStore = useAuthStore()
  const isMock    = import.meta.env.VITE_MOCK_DATA === 'true'

  if (to.meta.requiresAuth) {
    // In mock mode restore the session silently so users aren't blocked
    if (isMock) {
      authStore.restoreSession()
    }
    if (!authStore.isAuthenticated) {
      return next({ name: 'login', query: { redirect: to.fullPath } })
    }
  }

  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    return next({ name: 'dashboard' })
  }

  next()
})

export default router
