<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { useNotification } from '@/composables/useNotification'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const auth   = useAuthStore()
const notify = useNotification()
const router = useRouter()
const route  = useRoute()

const form         = reactive({ email: '', password: '', remember: false })
const error        = ref('')
const showPassword = ref(false)
const eyeMove      = reactive({ x: 0, y: 0 })

function handleMouseMove(e: MouseEvent) {
  if (!showPassword.value) return
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  const x = (e.clientX - rect.left) / rect.width - 0.5
  const y = (e.clientY - rect.top) / rect.height - 0.5
  eyeMove.x = x * 10
  eyeMove.y = y * 6
}

function resetEye() {
  eyeMove.x = 0
  eyeMove.y = 0
}

async function submit() {
  error.value = ''
  if (!form.email || !form.password) {
    error.value = 'Please enter your credentials'
    return
  }
  const ok = await auth.login({ email: form.email, password: form.password })
  if (ok) {
    const redirect = route.query.redirect as string | undefined
    router.push(redirect || '/')
  } else {
    error.value = 'Login failed. Please check your credentials.'
    notify.error('Login failed')
  }
}
</script>

<template>
  <div class="w-full max-w-sm mx-auto">

    <!-- Card -->
    <div class="login-card rounded-2xl p-8">

      <div class="mb-7">
        <h2 class="text-2xl font-bold text-white tracking-tight">Welcome back</h2>
        <p class="text-sm text-gray-500 mt-1">Sign in to your portfolio dashboard</p>
      </div>

      <form class="space-y-5" @submit.prevent="submit">

        <!-- Email -->
        <div class="space-y-1.5">
          <label class="block text-xs font-semibold text-gray-400 uppercase tracking-wider">Email</label>
          <div class="input-wrapper">
            <svg class="input-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
            </svg>
            <input
              v-model="form.email"
              type="email"
              autocomplete="email"
              placeholder="you@example.com"
              class="input-field"
              :disabled="auth.loading"
            />
          </div>
        </div>

        <!-- Password -->
        <div class="space-y-1.5">
          <label class="block text-xs font-semibold text-gray-400 uppercase tracking-wider">Password</label>
          <div
            class="input-wrapper"
            @mousemove="handleMouseMove"
            @mouseleave="resetEye"
          >
            <svg class="input-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
            </svg>
            <input
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              placeholder="••••••••"
              class="input-field password-dots pr-14"
              :disabled="auth.loading"
            />

            <!-- Animated eye button -->
            <button
              type="button"
              tabindex="-1"
              class="eye-toggle"
              :aria-label="showPassword ? 'Hide password' : 'Show password'"
              @click="showPassword = !showPassword"
            >
              <svg viewBox="0 0 100 100" class="eye-svg" overflow="visible">
                <defs>
                  <radialGradient id="irisGrad" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stop-color="#818cf8" />
                    <stop offset="100%" stop-color="#3730a3" />
                  </radialGradient>
                  <filter id="eyeShine" x="-50%" y="-50%" width="200%" height="200%">
                    <feGaussianBlur stdDeviation="0.8" result="blur" />
                  </filter>
                </defs>

                <!-- Open eye — squeezes shut on close -->
                <g
                  class="eye-open-group"
                  :class="showPassword ? 'eye-is-open' : 'eye-is-closing'"
                >
                  <path d="M10 50 Q50 15 90 50 Q50 85 10 50" fill="white" stroke="#000000" stroke-width="2.5" stroke-linejoin="round" />
                  <g
                    :style="{ transform: `translate(${eyeMove.x * 0.55}px, ${eyeMove.y * 0.55}px)` }"
                    class="iris-group"
                  >
                    <circle cx="50" cy="50" r="16" fill="url(#irisGrad)" />
                    <circle cx="50" cy="50" r="7" fill="#060609" />
                    <circle cx="44" cy="44" r="3" fill="white" fill-opacity="0.9" filter="url(#eyeShine)" />
                  </g>
                </g>

                <!-- Closed lid + lashes — fades in when shut -->
                <g
                  class="eye-closed-group"
                  :class="showPassword ? 'lashes-hidden' : 'lashes-visible'"
                >
                  <!-- Lid curve -->
                  <path d="M10 50 Q50 72 90 50" fill="none" stroke="#000000" stroke-width="6" stroke-linecap="round" />
                  <!-- 5 lashes — thick, long, black -->
                  <line x1="22" y1="60" x2="17" y2="72" stroke="#000000" stroke-width="4" stroke-linecap="round" />
                  <line x1="36" y1="66" x2="33" y2="79" stroke="#000000" stroke-width="4" stroke-linecap="round" />
                  <line x1="50" y1="68" x2="50" y2="82" stroke="#000000" stroke-width="4" stroke-linecap="round" />
                  <line x1="64" y1="66" x2="67" y2="79" stroke="#000000" stroke-width="4" stroke-linecap="round" />
                  <line x1="78" y1="60" x2="83" y2="72" stroke="#000000" stroke-width="4" stroke-linecap="round" />
                </g>
              </svg>
            </button>
          </div>
        </div>

        <!-- Remember me -->
        <div class="flex items-center justify-between pt-1">
          <label class="flex items-center gap-2 cursor-pointer select-none">
            <input v-model="form.remember" type="checkbox" class="w-4 h-4 rounded accent-brand-500" />
            <span class="text-xs text-gray-400">Remember me</span>
          </label>
        </div>

        <!-- Error -->
        <Transition
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="opacity-0 -translate-y-1"
          enter-to-class="opacity-100 translate-y-0"
        >
          <div v-if="error" class="flex items-center gap-2 rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2.5">
            <svg class="w-4 h-4 text-red-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <p class="text-xs text-red-400">{{ error }}</p>
          </div>
        </Transition>

        <!-- Submit -->
        <button
          type="submit"
          :disabled="auth.loading"
          class="submit-btn w-full"
        >
          <LoadingSpinner v-if="auth.loading" size="sm" />
          <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"/>
          </svg>
          {{ auth.loading ? 'Signing in…' : 'Sign in' }}
        </button>
      </form>

      <!-- Divider -->
      <div class="flex items-center gap-3 my-6">
        <div class="flex-1 h-px bg-white/5" />
        <span class="text-xs text-gray-600">New here?</span>
        <div class="flex-1 h-px bg-white/5" />
      </div>

      <!-- Register link -->
      <RouterLink
        to="/register"
        class="register-btn w-full flex items-center justify-center gap-2"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"/>
        </svg>
        Create an account
      </RouterLink>
    </div>

  </div>
</template>

<style scoped>
.login-card {
  background: linear-gradient(145deg, rgba(20, 24, 38, 0.95) 0%, rgba(14, 17, 28, 0.98) 100%);
  border: 1px solid rgba(255, 255, 255, 0.07);
  box-shadow:
    0 0 0 1px rgba(99, 102, 241, 0.06),
    0 20px 60px -10px rgba(0, 0, 0, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(20px);
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 0.75rem;
  width: 1rem;
  height: 1rem;
  color: #4b5563;
  pointer-events: none;
  flex-shrink: 0;
}

.input-field {
  width: 100%;
  height: 2.625rem;
  padding: 0 0.75rem 0 2.25rem;
  border-radius: 0.625rem;
  border: 1px solid rgba(255, 255, 255, 0.07);
  background: rgba(255, 255, 255, 0.03);
  color: #f9fafb;
  font-size: 0.875rem;
  line-height: 1;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
}
.input-field::placeholder { color: #4b5563; }
.input-field:focus {
  border-color: rgba(99, 102, 241, 0.5);
  background: rgba(99, 102, 241, 0.04);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
}
.input-field:disabled { opacity: 0.5; cursor: not-allowed; }

/* Premium password dot spacing — no font-size change to keep height stable */
.password-dots[type="password"] {
  letter-spacing: 0.3em;
}
.password-dots::placeholder {
  letter-spacing: normal;
}

/* ── Animated Eye Toggle ─────────────────────────────────────── */
.eye-toggle {
  position: absolute;
  right: 0.35rem;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 50%;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
  color: #6b7280;
  transition: color 0.2s, background 0.2s, transform 0.1s;
}
.eye-toggle:hover {
  color: #a5b4fc;
  background: rgba(99, 102, 241, 0.1);
}
.eye-toggle:active { transform: translateY(-50%) scale(0.88); }

.eye-svg {
  width: 1.875rem;
  height: 1.875rem;
  overflow: visible;
}

/* Open eye: full scale when open, squeezes to line when closing */
.eye-open-group {
  transform-origin: 50px 50px;
  transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.25s ease;
}
.eye-is-open    { transform: scaleY(1);    opacity: 1; }
.eye-is-closing { transform: scaleY(0.06); opacity: 0; }

.iris-group {
  transition: transform 0.12s ease-out;
  transform-origin: 50px 50px;
}

/* Closed lid + lashes: crossfades in/out */
.eye-closed-group {
  transition: opacity 0.25s ease 0.05s;
}
.lashes-hidden  { opacity: 0; pointer-events: none; }
.lashes-visible { opacity: 1; }

.submit-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  border-radius: 0.625rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  border: none;
  cursor: pointer;
  transition: opacity 0.15s, transform 0.1s, box-shadow 0.15s;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}
.submit-btn:hover:not(:disabled) {
  opacity: 0.92;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45);
}
.submit-btn:active:not(:disabled) { transform: translateY(0); }
.submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.register-btn {
  padding: 0.6rem 1rem;
  border-radius: 0.625rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
  color: #9ca3af;
  font-size: 0.875rem;
  font-weight: 500;
  text-decoration: none;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.register-btn:hover {
  background: rgba(99, 102, 241, 0.08);
  border-color: rgba(99, 102, 241, 0.25);
  color: #a5b4fc;
}
</style>
