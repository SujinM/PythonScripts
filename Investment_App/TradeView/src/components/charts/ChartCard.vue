<script setup lang="ts">
import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settingsStore'
import type { EChartsOption } from 'echarts'

interface Props {
  title?: string
  subtitle?: string
  loading?: boolean
  height?: string
  option?: EChartsOption
}

const props = withDefaults(defineProps<Props>(), {
  height: '300px',
  loading: false,
})

const settings = useSettingsStore()

const theme = computed(() => settings.theme)

const chartStyle = computed(() => ({ height: props.height, width: '100%' }))
</script>

<template>
  <div class="card p-4">
    <div v-if="title || subtitle" class="mb-4">
      <h3 v-if="title" class="text-sm font-semibold" style="color: var(--text-primary);">
        {{ title }}
      </h3>
      <p v-if="subtitle" class="text-xs mt-0.5" style="color: var(--text-muted);">{{ subtitle }}</p>
    </div>

    <div v-if="loading" class="animate-pulse" :style="chartStyle">
      <div class="skeleton h-full rounded-lg" />
    </div>

    <template v-else-if="option">
      <VChart
        :option="option"
        :theme="theme"
        :style="chartStyle"
        autoresize
      />
    </template>

    <slot v-else />
  </div>
</template>
