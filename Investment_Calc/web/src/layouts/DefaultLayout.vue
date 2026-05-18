<script setup lang="ts">
import Sidebar from '@/components/layout/Sidebar.vue'
import Navbar  from '@/components/layout/Navbar.vue'
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-[var(--surface-primary)]">
    <Sidebar />
    <div class="flex flex-col flex-1 min-w-0 overflow-hidden">
      <Navbar />
      <main class="flex-1 overflow-y-auto p-6 animate-fade-in">
        <RouterView />
      </main>
    </div>
  </div>
</template>
