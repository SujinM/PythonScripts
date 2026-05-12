import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Instrument, InstrumentFilter, PaginationParams } from '@/types/instrument'
import { instrumentsApi } from '@/api/instruments'
import { MOCK_INSTRUMENTS } from '@/utils/mockData'
import { DEFAULT_PAGE_SIZE } from '@/utils/constants'
import { useNotificationStore } from './notificationStore'

const useMock = import.meta.env.VITE_MOCK_DATA === 'true'

// ─── Instruments Store ────────────────────────────────────────────────────────

export const useInstrumentsStore = defineStore('instruments', () => {
  const notifications = useNotificationStore()

  // State
  const allInstruments      = ref<Instrument[]>(useMock ? MOCK_INSTRUMENTS : [])
  const selectedInstrument  = ref<Instrument | null>(null)
  const loading             = ref(false)
  const error               = ref<string | null>(null)
  const totalCount          = ref(useMock ? MOCK_INSTRUMENTS.length : 0)
  const filters             = ref<InstrumentFilter>({})
  const pagination          = ref<PaginationParams>({ page: 1, pageSize: DEFAULT_PAGE_SIZE })

  // ─── Computed ─────────────────────────────────────────────────────────────

  /** Client-side filtered & paginated slice (mock mode only) */
  const filteredInstruments = computed<Instrument[]>(() => {
    if (!useMock) return allInstruments.value

    let result = [...MOCK_INSTRUMENTS]

    if (filters.value.search) {
      const q = filters.value.search.toLowerCase()
      result = result.filter(
        (i) =>
          i.symbol.toLowerCase().includes(q) || i.displayName.toLowerCase().includes(q),
      )
    }
    if (filters.value.assetType) {
      result = result.filter((i) => i.assetType === filters.value.assetType)
    }
    if (filters.value.exchange) {
      result = result.filter((i) => i.exchange === filters.value.exchange)
    }
    if (filters.value.isTradable !== undefined) {
      result = result.filter((i) => i.isTradable === filters.value.isTradable)
    }

    // Sort
    if (pagination.value.sortBy) {
      const key = pagination.value.sortBy
      const asc = pagination.value.sortOrder !== 'desc'
      result.sort((a, b) => {
        const av = a[key as keyof Instrument]
        const bv = b[key as keyof Instrument]
        if (av === undefined || bv === undefined) return 0
        const cmp = String(av).localeCompare(String(bv), undefined, { numeric: true })
        return asc ? cmp : -cmp
      })
    }

    totalCount.value = result.length
    const start = (pagination.value.page - 1) * pagination.value.pageSize
    return result.slice(start, start + pagination.value.pageSize)
  })

  const totalPages = computed(() =>
    Math.ceil(totalCount.value / pagination.value.pageSize),
  )

  // ─── Actions ──────────────────────────────────────────────────────────────

  async function fetchInstruments() {
    if (useMock) {
      totalCount.value = filteredInstruments.value.length
      return
    }

    loading.value = true
    error.value = null
    try {
      const response = await instrumentsApi.getInstruments({
        ...filters.value,
        ...pagination.value,
      })
      allInstruments.value = response.data
      totalCount.value = response.total
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch instruments'
      notifications.error('Fetch failed', error.value)
    } finally {
      loading.value = false
    }
  }

  async function fetchInstrument(symbol: string): Promise<Instrument | null> {
    if (useMock) {
      selectedInstrument.value = MOCK_INSTRUMENTS.find((i) => i.symbol === symbol) ?? null
      return selectedInstrument.value
    }

    loading.value = true
    error.value = null
    try {
      selectedInstrument.value = await instrumentsApi.getInstrument(symbol)
      return selectedInstrument.value
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch instrument'
      notifications.error('Fetch failed', error.value)
      return null
    } finally {
      loading.value = false
    }
  }

  function setFilters(newFilters: Partial<InstrumentFilter>) {
    filters.value = { ...filters.value, ...newFilters }
    pagination.value.page = 1 // reset to first page on filter change
    if (!useMock) fetchInstruments()
  }

  function setPagination(params: Partial<PaginationParams>) {
    pagination.value = { ...pagination.value, ...params }
    if (!useMock) fetchInstruments()
  }

  function clearFilters() {
    filters.value = {}
    pagination.value = { page: 1, pageSize: DEFAULT_PAGE_SIZE }
    if (!useMock) fetchInstruments()
  }

  /** Export currently filtered instruments to CSV */
  function exportToCsv() {
    const items = useMock ? filteredInstruments.value : allInstruments.value
    const headers = ['ID', 'Symbol', 'Display Name', 'Exchange', 'Asset Type', 'Currency', 'Tradable']
    const rows = items.map((i) => [
      i.instrumentId, i.symbol, `"${i.displayName}"`, i.exchange,
      i.assetType, i.currency, i.isTradable,
    ])
    const csv = [headers, ...rows].map((r) => r.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `instruments-${new Date().toISOString().slice(0, 10)}.csv`
    link.click()
    URL.revokeObjectURL(url)
    notifications.success('Export complete', `${items.length} instruments exported`)
  }

  return {
    allInstruments,
    selectedInstrument,
    loading,
    error,
    totalCount,
    totalPages,
    filters,
    pagination,
    filteredInstruments,
    fetchInstruments,
    fetchInstrument,
    setFilters,
    setPagination,
    clearFilters,
    exportToCsv,
  }
})
