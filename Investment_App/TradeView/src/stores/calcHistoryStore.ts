import { defineStore } from 'pinia'
import { ref } from 'vue'

export type CalcHistoryEntry = {
  id: string
  category: string
  label: string
  inputs: Record<string, string | number>
  results: Record<string, number | string>
  timestamp: number
}

export const useCalcHistoryStore = defineStore(
  'calc-history',
  () => {
    const entries = ref<CalcHistoryEntry[]>([])

    function add(entry: Omit<CalcHistoryEntry, 'id' | 'timestamp'>) {
      entries.value.unshift({
        ...entry,
        id: crypto.randomUUID(),
        timestamp: Date.now(),
      })
      if (entries.value.length > 100) entries.value.pop()
    }

    function clear() {
      entries.value = []
    }

    return { entries, add, clear }
  },
  { persist: true }
)
