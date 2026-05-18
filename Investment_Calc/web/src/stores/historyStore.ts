import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { HistoryEntry } from '@/types'

export const useHistoryStore = defineStore(
  'history',
  () => {
    const entries = ref<HistoryEntry[]>([])

    function add(entry: Omit<HistoryEntry, 'id' | 'timestamp'>) {
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
