import { ref, watch, type Ref } from 'vue'

/**
 * Returns a debounced ref that updates only after the given delay.
 * Useful for search inputs to avoid firing API calls on every keystroke.
 */
export function useDebounce<T>(source: Ref<T>, delayMs = 300): Ref<T> {
  const debounced = ref<T>(source.value) as Ref<T>
  let timer: ReturnType<typeof setTimeout>

  watch(source, (val) => {
    clearTimeout(timer)
    timer = setTimeout(() => { debounced.value = val }, delayMs)
  })

  return debounced
}
