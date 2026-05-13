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

const form        = reactive({ email: '', password: '', remember: false })
const error       = ref('')
const showPassword = ref(false)

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
    <!-- Logo -->
    <div class="flex items-center justify-center gap-2 mb-8">
      <div class="w-9 h-9 rounded-xl bg-brand-500 flex items-center justify-center text-white font-bold text-sm">IP</div>
      <span class="text-lg font-bold tracking-tight text-white">Investment Portfolio</span>
    </div>

    <div class="rounded-2xl border p-8 backdrop-blur-xl" style="background-color: rgba(17,20,29,0.8); border-color: rgba(255,255,255,0.07);">
      <h2 class="text-xl font-bold text-white mb-1">Sign in</h2>
      <p class="text-sm text-gray-400 mb-6">Access your portfolio dashboard</p>

      <!-- Default credentials hint -->
      <div class="rounded-lg bg-emerald-500/10 border border-emerald-500/20 p-3 mb-5 text-xs text-emerald-300">
        Default admin — <strong>admin@local.com</strong> / <strong>Admin@123</strong>
      </div>

      <form class="space-y-4" @submit.prevent="submit">
        <!-- Email -->
        <div>
          <label class="block text-xs font-medium text-gray-400 mb-1.5">Email address</label>
          <input
            v-model="form.email"
            type="email"
            autocomplete="email"
            placeholder="admin@local.com"
            class="input w-full"
            :disabled="auth.loading"
          />
        </div>

        <!-- Password -->
        <div>
          <label class="block text-xs font-medium text-gray-400 mb-1.5">Password</label>
          <div class="relative">
            <input
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              placeholder="••••••••"
              class="input w-full pr-10"
              :disabled="auth.loading"
            />
            <button
              type="button"
              class="absolute inset-y-0 right-0 flex items-center px-3 text-gray-400 hover:text-gray-200 transition-colors"
              :aria-label="showPassword ? 'Hide password' : 'Show password'"
              @click="showPassword = !showPassword"
            >
              <!-- Eye open -->
              <svg v-if="showPassword" xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.477 0 8.268 2.943 9.542 7-1.274 4.057-5.065 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              <!-- Eye closed -->
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.477 0-8.268-2.943-9.542-7a9.956 9.956 0 012.293-3.95M6.938 6.938A9.956 9.956 0 0112 5c4.477 0 8.268 2.943 9.542 7a9.963 9.963 0 01-4.48 5.562M3 3l18 18" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Remember me -->
        <div class="flex items-center justify-between">
          <label class="flex items-center gap-2 cursor-pointer">
            <input
              v-model="form.remember"
              type="checkbox"
              class="w-4 h-4 rounded accent-brand-500"
            />
            <span class="text-xs text-gray-400">Remember me</span>
          </label>
        </div>

        <!-- Error -->
        <p v-if="error" class="text-xs text-red-400">{{ error }}</p>

        <!-- Submit -->
        <button
          type="submit"
          :disabled="auth.loading"
          class="btn-primary w-full justify-center"
        >
          <LoadingSpinner v-if="auth.loading" size="sm" />
          {{ auth.loading ? 'Signing in…' : 'Sign in' }}
        </button>
      </form>

      <!-- Register link -->
      <p class="text-xs text-gray-500 text-center mt-5">
        Don't have an account?
        <RouterLink to="/register" class="text-brand-400 hover:text-brand-300 font-medium">
          Create one
        </RouterLink>
      </p>
    </div>
  </div>
</template>
