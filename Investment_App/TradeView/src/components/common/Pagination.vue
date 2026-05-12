<script setup lang="ts">
import { computed } from 'vue'
import { usePagination } from '@/composables/usePagination'
import { toRef } from 'vue'

interface Props {
  total: number
  page: number
  pageSize: number
}

const props = defineProps<Props>()
const emit  = defineEmits<{ 'update:page': [page: number] }>()

const { totalPages, hasPrev, hasNext, startItem, endItem, pages } = usePagination({
  total:    toRef(props, 'total'),
  page:     toRef(props, 'page'),
  pageSize: toRef(props, 'pageSize'),
})

function go(p: number) {
  if (p < 1 || p > totalPages.value) return
  emit('update:page', p)
}
</script>

<template>
  <div class="flex flex-col sm:flex-row items-center justify-between gap-3 text-sm">
    <!-- Item count -->
    <p style="color: var(--text-muted);">
      Showing <strong style="color: var(--text-secondary);">{{ startItem }}–{{ endItem }}</strong>
      of <strong style="color: var(--text-secondary);">{{ total }}</strong> results
    </p>

    <!-- Page buttons -->
    <div class="flex items-center gap-1">
      <!-- Previous -->
      <button
        :disabled="!hasPrev"
        class="px-2 py-1.5 rounded-md border transition-colors disabled:opacity-40 disabled:cursor-not-allowed hover:bg-white/5"
        style="border-color: var(--surface-border); color: var(--text-secondary);"
        aria-label="Previous page"
        @click="go(page - 1)"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      <!-- Page numbers -->
      <template v-for="p in pages" :key="p">
        <span v-if="p === 0" class="px-2 py-1.5" style="color: var(--text-muted);">…</span>
        <button
          v-else
          :class="[
            'min-w-[32px] px-2 py-1.5 rounded-md border text-center transition-colors text-xs font-medium',
            p === page
              ? 'bg-brand-500 border-brand-500 text-white'
              : 'hover:bg-white/5 border-transparent',
          ]"
          :style="p !== page ? 'color: var(--text-secondary);' : ''"
          @click="go(p)"
        >
          {{ p }}
        </button>
      </template>

      <!-- Next -->
      <button
        :disabled="!hasNext"
        class="px-2 py-1.5 rounded-md border transition-colors disabled:opacity-40 disabled:cursor-not-allowed hover:bg-white/5"
        style="border-color: var(--surface-border); color: var(--text-secondary);"
        aria-label="Next page"
        @click="go(page + 1)"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </div>
  </div>
</template>
