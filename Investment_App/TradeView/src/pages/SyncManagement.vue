<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useSyncStore } from '@/stores/syncStore'
import { formatDate, timeAgo } from '@/utils/formatters'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const syncStore = useSyncStore()

onMounted(async () => {
  await syncStore.fetchLogs()
})

const logLevelColor: Record<string, string> = {
  info:    'text-blue-400 bg-blue-500/10',
  warning: 'text-amber-400 bg-amber-500/10',
  error:   'text-red-400 bg-red-500/10',
}

const progressColor = computed(() => {
  const p = syncStore.status.progress
  if (p === 100) return 'bg-emerald-500'
  if (syncStore.status.errors?.length) return 'bg-red-500'
  return 'bg-brand-500'
})
</script>

<template>
  <div class="space-y-5 animate-fade-in">
    <div>
      <h2 class="text-xl font-bold" style="color: var(--text-primary);">Sync Management</h2>
      <p class="text-sm mt-0.5" style="color: var(--text-muted);">
        Synchronise financial instruments from the eToro API
      </p>
    </div>

    <!-- Control card -->
    <div class="card p-5 space-y-5">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Instrument Sync</h3>
          <p class="text-xs mt-0.5" style="color: var(--text-muted);">
            Last sync: {{ syncStore.status.lastSyncAt ? timeAgo(syncStore.status.lastSyncAt) : 'Never' }}
          </p>
        </div>
        <button
          :disabled="syncStore.status.isRunning || syncStore.loading"
          class="btn-primary"
          @click="syncStore.triggerSync"
        >
          <LoadingSpinner v-if="syncStore.status.isRunning || syncStore.loading" size="sm" />
          <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {{ syncStore.status.isRunning ? 'Syncing…' : 'Start Sync' }}
        </button>
      </div>

      <!-- Progress bar -->
      <div v-if="syncStore.status.isRunning || syncStore.status.progress > 0">
        <div class="flex justify-between text-xs mb-1.5" style="color: var(--text-muted);">
          <span>
            {{
              syncStore.status.isRunning
                ? `Processing ${syncStore.status.itemsProcessed ?? 0} / ${syncStore.status.totalItems ?? '?'} instruments`
                : syncStore.status.progress === 100
                ? 'Sync completed successfully'
                : 'Ready'
            }}
          </span>
          <span class="font-mono font-semibold" style="color: var(--text-primary);">{{ syncStore.status.progress }}%</span>
        </div>
        <div class="h-2 rounded-full overflow-hidden" style="background-color: var(--surface-border);">
          <div
            :class="['h-full rounded-full transition-all duration-500', progressColor]"
            :style="{ width: syncStore.status.progress + '%' }"
          />
        </div>
        <div class="flex gap-6 mt-2 text-xs" style="color: var(--text-muted);">
          <span v-if="syncStore.status.startedAt">
            Started: {{ formatDate(syncStore.status.startedAt) }}
          </span>
          <span v-if="syncStore.status.completedAt">
            Completed: {{ formatDate(syncStore.status.completedAt) }}
          </span>
        </div>
      </div>

      <!-- Errors -->
      <div v-if="syncStore.status.errors?.length" class="rounded-lg bg-red-500/10 border border-red-500/20 p-3">
        <p class="text-xs font-semibold text-red-400 mb-1">Errors during sync:</p>
        <ul class="list-disc list-inside space-y-0.5">
          <li v-for="err in syncStore.status.errors" :key="err" class="text-xs text-red-300">{{ err }}</li>
        </ul>
      </div>
    </div>

    <!-- Sync info cards -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div class="card p-4 text-center">
        <p class="text-2xl font-bold stat-value" style="color: var(--text-primary);">
          {{ syncStore.status.totalItems ?? 791 }}
        </p>
        <p class="text-xs mt-1" style="color: var(--text-muted);">Total Instruments</p>
      </div>
      <div class="card p-4 text-center">
        <p class="text-2xl font-bold stat-value text-profit">
          {{ syncStore.status.itemsProcessed ?? (syncStore.status.progress === 100 ? 791 : 0) }}
        </p>
        <p class="text-xs mt-1" style="color: var(--text-muted);">Processed</p>
      </div>
      <div class="card p-4 text-center">
        <p class="text-2xl font-bold stat-value" :class="syncStore.status.errors?.length ? 'text-loss' : 'text-profit'">
          {{ syncStore.status.errors?.length ?? 0 }}
        </p>
        <p class="text-xs mt-1" style="color: var(--text-muted);">Errors</p>
      </div>
    </div>

    <!-- Sync log -->
    <div class="card overflow-hidden">
      <div class="px-4 py-3 border-b flex items-center justify-between" style="border-color: var(--surface-border);">
        <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Sync Log</h3>
        <button class="text-xs text-brand-400 hover:text-brand-300 transition-colors" @click="syncStore.fetchLogs">
          Refresh
        </button>
      </div>
      <div class="divide-y font-mono text-xs overflow-y-auto max-h-[340px]" style="border-color: var(--surface-border);">
        <div
          v-for="log in syncStore.logs"
          :key="log.id"
          class="px-4 py-2.5 flex items-start gap-3 hover:bg-white/3"
        >
          <span class="text-gray-600 flex-shrink-0 tabular-nums" style="min-width: 160px;">
            {{ formatDate(log.timestamp) }}
          </span>
          <span :class="['badge flex-shrink-0', logLevelColor[log.level] ?? 'text-gray-400']">
            {{ log.level.toUpperCase() }}
          </span>
          <span class="flex-1" style="color: var(--text-secondary);">{{ log.message }}</span>
          <span v-if="log.symbol" class="text-brand-400 flex-shrink-0">{{ log.symbol }}</span>
        </div>
        <div v-if="syncStore.logs.length === 0" class="px-4 py-8 text-center" style="color: var(--text-muted);">
          No log entries yet — trigger a sync to see activity
        </div>
      </div>
    </div>
  </div>
</template>
