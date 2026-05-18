<script setup lang="ts">
defineProps<{
  title: string
  results: Record<string, number | string | boolean>
  highlightKey?: string
}>()

function isPositive(v: number | string | boolean): boolean {
  if (typeof v === 'number') return v >= 0
  if (typeof v === 'string') {
    const n = parseFloat(v)
    return !isNaN(n) && n >= 0
  }
  return !!v
}

function fmt(v: number | string | boolean): string {
  if (typeof v === 'number') {
    return Math.abs(v) >= 1000
      ? v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })
      : v.toFixed(4)
  }
  return String(v)
}
</script>

<template>
  <div class="card p-5 animate-slide-up">
    <h3 class="text-xs font-semibold uppercase tracking-widest text-[var(--text-muted)] mb-4">
      {{ title }}
    </h3>
    <div class="space-y-0">
      <div
        v-for="(val, key) in results" :key="key"
        class="result-row"
        :class="key === highlightKey ? 'font-semibold' : ''"
      >
        <span class="text-xs text-[var(--text-secondary)]">{{ key }}</span>
        <span
          class="stat-value text-sm"
          :class="
            key.includes('%') || key.includes('P&L') || key === highlightKey
              ? (typeof val === 'number' && val < 0 ? 'text-loss' : 'text-profit')
              : 'text-[var(--text-primary)]'
          "
        >
          {{ fmt(val) }}
        </span>
      </div>
    </div>
  </div>
</template>
