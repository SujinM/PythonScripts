<script setup lang="ts">
import { computed } from 'vue'
import { useNotificationStore } from '@/stores/notificationStore'
import type { Notification } from '@/types/api'

const store = useNotificationStore()

const iconMap: Record<Notification['type'], string> = {
  success: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
  error:   'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z',
  warning: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
  info:    'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
}

const colorMap: Record<Notification['type'], string> = {
  success: 'border-l-emerald-500 bg-emerald-500/5',
  error:   'border-l-red-500 bg-red-500/5',
  warning: 'border-l-amber-500 bg-amber-500/5',
  info:    'border-l-blue-500 bg-blue-500/5',
}

const iconColorMap: Record<Notification['type'], string> = {
  success: 'text-emerald-500',
  error:   'text-red-500',
  warning: 'text-amber-500',
  info:    'text-blue-500',
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed top-4 right-4 z-[100] flex flex-col gap-2 w-80 pointer-events-none">
      <TransitionGroup
        tag="div"
        enter-active-class="transition ease-out duration-200"
        enter-from-class="opacity-0 translate-x-8"
        enter-to-class="opacity-100 translate-x-0"
        leave-active-class="transition ease-in duration-150 absolute"
        leave-from-class="opacity-100 translate-x-0"
        leave-to-class="opacity-0 translate-x-8"
        class="flex flex-col gap-2"
      >
        <div
          v-for="notif in store.notifications"
          :key="notif.id"
          :class="[
            'pointer-events-auto flex items-start gap-3 rounded-xl border border-l-4 px-4 py-3 shadow-xl',
            'backdrop-blur-sm',
            colorMap[notif.type],
          ]"
          style="background-color: var(--surface-card);"
        >
          <!-- Icon -->
          <svg
            :class="['mt-0.5 w-5 h-5 flex-shrink-0', iconColorMap[notif.type]]"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="iconMap[notif.type]" />
          </svg>

          <!-- Content -->
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium" style="color: var(--text-primary);">{{ notif.title }}</p>
            <p v-if="notif.message" class="text-xs mt-0.5" style="color: var(--text-muted);">{{ notif.message }}</p>
          </div>

          <!-- Close button -->
          <button
            class="flex-shrink-0 text-gray-500 hover:text-gray-300 transition-colors"
            @click="store.remove(notif.id)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>
