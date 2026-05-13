<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const auth   = useAuthStore()
const router = useRouter()

const form = reactive({
  username:        '',
  email:           '',
  password:        '',
  confirmPassword: '',
})
const error = ref('')

const passwordsMatch = computed(() => form.password === form.confirmPassword)

async function submit() {
  error.value = ''

  if (!form.username || !form.email || !form.password || !form.confirmPassword) {
    error.value = 'Please fill in all fields.'
    return
  }
  if (!passwordsMatch.value) {
    error.value = 'Passwords do not match.'
    return
  }
  if (form.password.length < 6) {
    error.value = 'Password must be at least 6 characters.'
    return
  }

  const ok = await auth.register({
    username:        form.username,
    email:           form.email,
    password:        form.password,
    confirmPassword: form.confirmPassword,
  })

  if (ok) {
    router.push({ name: 'login' })
  } else {
    error.value = 'Registration failed. Please try again.'
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
      <h2 class="text-xl font-bold text-white mb-1">Create account</h2>
      <p class="text-sm text-gray-400 mb-6">Set up your portfolio dashboard</p>

      <form class="space-y-4" @submit.prevent="submit">
        <!-- Username -->
        <div>
          <label class="block text-xs font-medium text-gray-400 mb-1.5">Username</label>
          <input
            v-model="form.username"
            type="text"
            autocomplete="username"
            placeholder="johndoe"
            class="input w-full"
            :disabled="auth.loading"
          />
        </div>

        <!-- Email -->
        <div>
          <label class="block text-xs font-medium text-gray-400 mb-1.5">Email address</label>
          <input
            v-model="form.email"
            type="email"
            autocomplete="email"
            placeholder="you@example.com"
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
            autocomplete="new-password"
            placeholder="Min. 6 characters"
            class="input w-full"
            :disabled="auth.loading"
          />
        </div>

        <!-- Confirm Password -->
        <div>
          <label class="block text-xs font-medium text-gray-400 mb-1.5">Confirm password</label>
          <input
            v-model="form.confirmPassword"
            type="password"
            autocomplete="new-password"
            placeholder="Repeat your password"
            class="input w-full"
            :class="{ 'border-red-500/60': form.confirmPassword && !passwordsMatch }"
            :disabled="auth.loading"
          />
          <p v-if="form.confirmPassword && !passwordsMatch" class="text-xs text-red-400 mt-1">
            Passwords do not match
          </p>
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
          {{ auth.loading ? 'Creating account…' : 'Create account' }}
        </button>
      </form>

      <!-- Link to login -->
      <p class="text-xs text-gray-500 text-center mt-5">
        Already have an account?
        <RouterLink to="/login" class="text-brand-400 hover:text-brand-300 font-medium">
          Sign in
        </RouterLink>
      </p>
    </div>
  </div>
</template>
