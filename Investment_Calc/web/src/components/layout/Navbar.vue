<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()

const titles: Record<string, string> = {
  dashboard: 'Dashboard',
  price:     'Price Calculations',
  returns:   'Returns & P&L',
  risk:      'Risk Management',
  position:  'Position & Portfolio',
  options:   'Options',
  history:   'Calculation History',
}
</script>

<template>
  <header class="h-14 flex items-center px-6 border-b border-[var(--surface-border)] bg-[var(--surface-sidebar)] flex-shrink-0">
    <div class="flex items-center gap-2">
      <h1 class="text-sm font-semibold text-[var(--text-primary)]">
        {{ titles[String(route.name)] ?? 'InvestCalc' }}
      </h1>
    </div>
    <div class="ml-auto flex items-center gap-2">
      <span class="badge bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
        <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
        Live
      </span>
    </div>
  </header>
</template>
