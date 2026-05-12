<script setup lang="ts">
interface Props {
  lines?: number
  height?: string
  width?: string
  rounded?: boolean
}
withDefaults(defineProps<Props>(), {
  lines: 1,
  height: 'h-4',
  width: 'w-full',
  rounded: true,
})
</script>

<template>
  <div :class="['space-y-2']">
    <div
      v-for="i in lines"
      :key="i"
      :class="[
        'skeleton',
        height,
        i === lines && lines > 1 ? 'w-3/4' : width,
        rounded ? 'rounded-md' : '',
      ]"
    />
  </div>
</template>
