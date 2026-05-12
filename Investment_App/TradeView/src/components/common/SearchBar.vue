<script setup lang="ts">
import { ref, watch } from 'vue'
import { useDebounce } from '@/composables/useDebounce'

interface Props {
  modelValue?: string
  placeholder?: string
  debounce?: number
  autofocus?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  placeholder: 'Search…',
  debounce: 300,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  search: [value: string]
}>()

const inputValue = ref(props.modelValue)
const debounced  = useDebounce(inputValue, props.debounce)

watch(() => props.modelValue, (v) => { inputValue.value = v })
watch(debounced, (v) => {
  emit('update:modelValue', v)
  emit('search', v)
})

function clearInput() {
  inputValue.value = ''
  emit('update:modelValue', '')
  emit('search', '')
}
</script>

<template>
  <div class="relative">
    <!-- Search icon -->
    <svg
      class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
      style="color: var(--text-muted);"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>

    <input
      v-model="inputValue"
      type="search"
      class="input pl-9 pr-8 text-sm"
      :placeholder="placeholder"
      :autofocus="autofocus"
    />

    <!-- Clear button -->
    <button
      v-if="inputValue"
      class="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 rounded text-gray-500 hover:text-gray-300 transition-colors"
      aria-label="Clear search"
      @click="clearInput"
    >
      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </div>
</template>
