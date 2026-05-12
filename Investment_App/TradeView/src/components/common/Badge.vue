<script setup lang="ts">
import type { AssetType } from '@/types/instrument'
import { ASSET_TYPES } from '@/utils/constants'

interface Props {
  value: string
  type?: 'assetType' | 'exchange' | 'tradable' | 'custom'
  label?: string
}

const props = defineProps<Props>()

function getStyle(): string {
  if (props.type === 'assetType') {
    const found = ASSET_TYPES.find((a) => a.value === props.value)
    return found?.bgColor ?? 'bg-gray-500/10 text-gray-400'
  }
  if (props.type === 'tradable') {
    return props.value === 'true' || props.value === true
      ? 'bg-emerald-500/10 text-emerald-400'
      : 'bg-gray-500/10 text-gray-500'
  }
  return 'bg-blue-500/10 text-blue-400'
}
</script>

<template>
  <span :class="['badge', getStyle()]">
    {{ label ?? value }}
  </span>
</template>
