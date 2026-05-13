<script setup lang="ts">
import { RouterView } from 'vue-router'
import Sidebar from '@/components/layout/Sidebar.vue'
import Navbar from '@/components/layout/Navbar.vue'
</script>

<template>
  <div class="flex h-screen overflow-hidden" style="background-color: var(--surface-primary);">
    <!-- Sidebar -->
    <Sidebar />

    <!-- Main content area -->
    <div class="flex flex-col flex-1 min-w-0 overflow-hidden">
      <Navbar />

      <!-- Page content -->
      <main class="flex-1 overflow-y-auto p-4 sm:p-6">
        <RouterView v-slot="{ Component }">
          <Transition name="fade" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
