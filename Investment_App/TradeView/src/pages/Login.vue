<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { useNotification } from '@/composables/useNotification'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const auth    = useAuthStore()
const notify  = useNotification()

const form = reactive({ email: '', password: '', remember: false })
const error = ref('')

async function submit() {
  error.value = ''
  if (!form.email || !form.password) {
    error.value = 'Please enter your credentials'
    return
  }
  const ok = await auth.login({ email: form.email, password: form.password })
  if (!ok) {
    error.value = 'Login failed. Please check your credentials.'
    notify.error('Login failed')
  }
}
</script>

<template>
  <div class="w-full max-w-sm mx-auto">
    <!-- Logo -->
    <div class="flex items-center justify-center gap-2 mb-8">
      <div class="w-9 h-9 rounded-xl bg-brand-500 flex items-center justify-center text-white font-bold text-sm">eT</div>
      <span class="text-lg font-bold tracking-tight text-white">eToro Instruments</span>
    </div>

    <div class="rounded-2xl border p-8 backdrop-blur-xl" style="background-color: rgba(17,20,29,0.8); border-color: rgba(255,255,255,0.07);">
      <h2 class="text-xl font-bold text-white mb-1">Sign in</h2>
      <p class="text-sm text-gray-400 mb-6">Access your instruments dashboard</p>

      <!-- Demo hint -->
      <div class="rounded-lg bg-brand-500/10 border border-brand-500/20 p-3 mb-5 text-xs text-brand-300">
        <strong>Demo mode:</strong> Enter any email &amp; password to continue
      </div>

      <form class="space-y-4" @submit.prevent="submit">
        <!-- Email -->
        <div>
          <label class="block text-xs font-medium text-gray-400 mb-1.5">Email address</label>
          <input
            v-model="form.email"
            type="email"
            autocomplete="email"
            placeholder="analyst@etoro.com"
            class="input w-full"
            :disabled="auth.loading"
          />
        </div>

        <!-- Password -->
        <div>
          <label class="block text-xs font-medium text-gray-400 mb-1.5">Password</label>
          <input
            v-model="form.password"
            type="password"
            autocomplete="current-password"
            placeholder="••••••••"
            class="input w-full"
            :disabled="auth.loading"
          />
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
    </div>
  </div>
</template>
