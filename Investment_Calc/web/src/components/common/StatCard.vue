<script setup lang="ts">
defineProps<{ label: string; value: string | number; unit?: string; color?: string }>()
</script>

<template>
  <div class="card p-4">
    <p class="text-xs text-[var(--text-muted)] uppercase tracking-widest mb-1">{{ label }}</p>
    <p class="stat-value text-2xl" :class="color ?? 'text-[var(--text-primary)]'">
      {{ value }}<span v-if="unit" class="text-sm text-[var(--text-muted)] ml-1">{{ unit }}</span>
    </p>
  </div>
</template>
