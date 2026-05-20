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
  {
    path: '/register',
    component: AuthLayout,
    meta: { requiresGuest: true },
    children: [
      {
        path: '',
        name: 'register',
        component: () => import('@/pages/Register.vue'),
        meta: { title: 'Create Account' },
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
        path: 'holdings',
        name: 'holdings',
        component: () => import('@/pages/Holdings.vue'),
        meta: { title: 'Holdings' },
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
      // Redirect old /sync route to settings (broker management moved there)
      {
        path: 'sync',
        redirect: '/settings',
      },
      {
        path: 'etoro-instruments',
        name: 'etoro-instruments',
        component: () => import('@/pages/EtoroInstruments.vue'),
        meta: { title: 'eToro Markets' },
      },
      {
        path: 'upstox-instruments',
        name: 'upstox-instruments',
        component: () => import('@/pages/UpstoxInstruments.vue'),
        meta: { title: 'Upstox Instruments' },
      },
      {
        path: 'upstox-historical/:instrumentKey',
        name: 'upstox-historical',
        component: () => import('@/pages/UpstoxHistorical.vue'),
        meta: { title: 'Historical Chart' },
        props: true,
      },

      // ─── Calculations ───────────────────────────────────────────────────
      {
        path: 'calc',
        name: 'calc',
        component: () => import('@/pages/calc/CalcDashboard.vue'),
        meta: { title: 'Calculations' },
      },
      {
        path: 'calc/price',
        name: 'calc-price',
        component: () => import('@/pages/calc/PriceCalc.vue'),
        meta: { title: 'Price Calc' },
      },
      {
        path: 'calc/returns',
        name: 'calc-returns',
        component: () => import('@/pages/calc/ReturnsCalc.vue'),
        meta: { title: 'Returns & P&L' },
      },
      {
        path: 'calc/risk',
        name: 'calc-risk',
        component: () => import('@/pages/calc/RiskCalc.vue'),
        meta: { title: 'Risk Management' },
      },
      {
        path: 'calc/position',
        name: 'calc-position',
        component: () => import('@/pages/calc/PositionCalc.vue'),
        meta: { title: 'Position & Portfolio' },
      },
      {
        path: 'calc/options',
        name: 'calc-options',
        component: () => import('@/pages/calc/OptionsCalc.vue'),
        meta: { title: 'Options Calculator' },
      },
      {
        path: 'calc/percent',
        name: 'calc-percent',
        component: () => import('@/pages/calc/PercentCalc.vue'),
        meta: { title: 'Percentage Calculator' },
      },
      {
        path: 'calc/history',
        name: 'calc-history',
        component: () => import('@/pages/calc/CalcHistory.vue'),
        meta: { title: 'Calc History' },
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

let _authInitialised = false

router.beforeEach(async (to, _from, next) => {
  // Update document title
  const title = to.meta.title as string | undefined
  document.title = title ? `${title} — Investment Portfolio` : 'Investment Portfolio'

  const authStore = useAuthStore()

  // On the very first navigation, attempt to restore a persisted session.
  if (!_authInitialised) {
    _authInitialised = true
    await authStore.checkAuth()
  }

  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated) {
      // Only carry a redirect param for meaningful deep-link paths (not just '/')
      const redirectTo = to.fullPath !== '/' ? { redirect: to.fullPath } : undefined
      return next({ name: 'login', query: redirectTo })
    }
  }

  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    return next({ name: 'dashboard' })
  }

  next()
})

export default router
