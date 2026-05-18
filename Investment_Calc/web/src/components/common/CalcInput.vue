<script setup lang="ts">
defineProps<{
  label: string
  modelValue: string | number
  placeholder?: string
  type?: string
  hint?: string
}>()

defineEmits<{ 'update:modelValue': [v: string] }>()
</script>

<template>
  <div>
    <label class="calc-label">{{ label }}</label>
    <input
      :type="type ?? 'number'"
      :value="modelValue"
      :placeholder="placeholder ?? '0'"
      step="any"
      class="calc-input"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <p v-if="hint" class="mt-1 text-xs text-[var(--text-muted)]">{{ hint }}</p>
  </div>
</template>
