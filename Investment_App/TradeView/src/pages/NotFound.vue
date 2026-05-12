<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="flex flex-col items-center justify-center py-24 text-center animate-fade-in">
    <p class="text-8xl font-black text-brand-500 leading-none mb-4">404</p>
    <h1 class="text-2xl font-bold mb-2" style="color: var(--text-primary);">Page not found</h1>
    <p class="text-sm mb-8" style="color: var(--text-muted);">The page you're looking for doesn't exist or has been moved.</p>
    <button class="btn-primary" @click="router.push('/')">Go to Dashboard</button>
  </div>
</template>
