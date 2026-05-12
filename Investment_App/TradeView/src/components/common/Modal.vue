<script setup lang="ts">

interface Props {
  open: boolean
  title?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
}

withDefaults(defineProps<Props>(), { size: 'md' })
const emit = defineEmits<{ close: [] }>()

const sizeMap = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="open"
        class="fixed inset-0 z-50 overflow-y-auto"
        @click.self="emit('close')"
      >
        <!-- Backdrop -->
        <div class="fixed inset-0 bg-black/60 backdrop-blur-sm" />

        <!-- Panel -->
        <div class="relative flex min-h-full items-center justify-center p-4">
          <Transition
            enter-active-class="transition ease-out duration-200"
            enter-from-class="opacity-0 scale-95"
            enter-to-class="opacity-100 scale-100"
          >
            <div
              v-if="open"
              :class="['relative w-full rounded-2xl border shadow-2xl p-6', sizeMap[size]]"
              style="background-color: var(--surface-card); border-color: var(--surface-border);"
            >
              <!-- Header -->
              <div v-if="title || $slots.header" class="flex items-center justify-between mb-4">
                <slot name="header">
                  <h2 class="text-base font-semibold" style="color: var(--text-primary);">{{ title }}</h2>
                </slot>
                <button
                  class="p-1 rounded-md text-gray-500 hover:text-gray-300 hover:bg-white/5 transition-colors"
                  @click="emit('close')"
                >
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <!-- Body -->
              <slot />

              <!-- Footer -->
              <div v-if="$slots.footer" class="mt-6 flex justify-end gap-3">
                <slot name="footer" />
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
