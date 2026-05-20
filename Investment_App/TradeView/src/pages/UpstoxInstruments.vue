<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import DataTable from '@/components/common/DataTable.vue'
import SearchBar from '@/components/common/SearchBar.vue'
import Pagination from '@/components/common/Pagination.vue'
import { upstoxInstrumentsApi } from '@/api/upstoxInstruments'
import type { UpstoxInstrument } from '@/types/upstoxInstrument'
import { UPSTOX_SEGMENTS, UPSTOX_EXCHANGES } from '@/types/upstoxInstrument'
import type { TableColumn, SortOrder } from '@/types/instrument'

const router = useRouter()

function viewChart(instrument: UpstoxInstrument) {
  router.push({
    name: 'upstox-historical',
    params: { instrumentKey: encodeURIComponent(instrument.instrument_key) },
    query:  { name: instrument.name || instrument.trading_symbol },
  })
}

// ── State ─────────────────────────────────────────────────────────────────────

const data        = ref<UpstoxInstrument[]>([])
const loading     = ref(false)
const syncing     = ref(false)
const error       = ref<string | null>(null)
const syncMessage = ref<string | null>(null)
const syncError   = ref<string | null>(null)

const total      = ref(0)
const page       = ref(1)
const pageSize   = ref(50)
const totalPages = ref(1)

const search          = ref('')
const filterSegment   = ref<string>('')
const filterExchange  = ref<string>('')
const sortBy          = ref('trading_symbol')
const sortOrder       = ref<SortOrder>('asc')

const PAGE_SIZE_OPTIONS = [25, 50, 100, 200]

const segmentOptions = Object.entries(UPSTOX_SEGMENTS).map(([key, label]) => ({ value: key, label }))
const exchangeOptions = UPSTOX_EXCHANGES.map(ex => ({ value: ex, label: ex }))

// ── Table columns ─────────────────────────────────────────────────────────────

const columns = computed<TableColumn<Record<string, unknown>>[]>(() => [
  { key: 'trading_symbol', label: 'Symbol',       sortable: true },
  { key: 'name',           label: 'Name',          sortable: true },
  { key: 'segment_label',  label: 'Segment',       sortable: false },
  { key: 'exchange',       label: 'Exchange',      sortable: true,  width: '90px' },
  { key: 'instrument_type', label: 'Type',         sortable: false, width: '70px' },
  { key: 'isin',           label: 'ISIN',          sortable: false },
  { key: 'lot_size',       label: 'Lot',           sortable: true,  width: '70px' },
  { key: 'tick_size',      label: 'Tick',          sortable: true,  width: '70px' },
  { key: '_chart',         label: '',              sortable: false, width: '50px' },
])

// ── Data loading ──────────────────────────────────────────────────────────────

async function loadData() {
  loading.value = true
  error.value   = null
  try {
    const result = await upstoxInstrumentsApi.getInstruments({
      page:       page.value,
      page_size:  pageSize.value,
      search:     search.value || undefined,
      segment:    filterSegment.value  || undefined,
      exchange:   filterExchange.value || undefined,
      sort_by:    sortBy.value,
      sort_order: sortOrder.value,
    })
    data.value       = result.data
    total.value      = result.total
    totalPages.value = result.total_pages
    page.value       = result.page
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } }; message?: string }
    error.value = err.response?.data?.detail ?? err.message ?? 'Failed to load instruments'
  } finally {
    loading.value = false
  }
}

async function syncFromFile() {
  syncing.value    = true
  syncMessage.value = null
  syncError.value  = null
  try {
    const result = await upstoxInstrumentsApi.syncInstruments()
    syncMessage.value = result.message
    await loadData()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } }; message?: string }
    syncError.value = err.response?.data?.detail ?? err.message ?? 'Sync failed'
  } finally {
    syncing.value = false
  }
}

function handleSort(key: string, order: SortOrder) {
  sortBy.value    = key
  sortOrder.value = order
  page.value      = 1
  loadData()
}

function resetFilters() {
  search.value         = ''
  filterSegment.value  = ''
  filterExchange.value = ''
  page.value           = 1
  loadData()
}

watch([search, filterSegment, filterExchange], () => {
  page.value = 1
  loadData()
})

watch([page, pageSize], () => loadData())

onMounted(() => loadData())

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatNumber(n: number) {
  return new Intl.NumberFormat().format(n)
}

function segmentChipStyle(segment: string): Record<string, string> {
  const map: Record<string, [string, string]> = {
    BSE_EQ:           ['rgba(59,130,246,0.15)',   '#60A5FA'],
    BSE_FO:           ['rgba(99,102,241,0.15)',   '#818CF8'],
    BSE_INDEX:        ['rgba(168,85,247,0.15)',   '#C084FC'],
    NSE_EQ:           ['rgba(16,185,129,0.15)',   '#10B981'],
    NSE_FO:           ['rgba(245,158,11,0.15)',   '#F59E0B'],
    NSE_INDEX:        ['rgba(234,179,8,0.15)',    '#EAB308'],
    NSE_COM:          ['rgba(239,68,68,0.15)',    '#F87171'],
    MCX_FO:           ['rgba(249,115,22,0.15)',   '#FB923C'],
    NCD_FO:           ['rgba(20,184,166,0.15)',   '#2DD4BF'],
    BCD_FO:           ['rgba(236,72,153,0.15)',   '#F472B6'],
    GLOBAL_INDEX:     ['rgba(107,114,128,0.15)', '#9CA3AF'],
    GLOBAL_INDICATOR: ['rgba(75,85,99,0.15)',    '#6B7280'],
  }
  const [bg, color] = map[segment] ?? ['rgba(107,114,128,0.15)', '#9CA3AF']
  return { background: bg, color }
}

function exchangeChipStyle(exchange: string): Record<string, string> {
  const map: Record<string, [string, string]> = {
    BSE:    ['rgba(59,130,246,0.15)',  '#60A5FA'],
    NSE:    ['rgba(16,185,129,0.15)',  '#10B981'],
    MCX:    ['rgba(245,158,11,0.15)',  '#F59E0B'],
    GLOBAL: ['rgba(107,114,128,0.15)', '#9CA3AF'],
  }
  const [bg, color] = map[exchange] ?? ['rgba(107,114,128,0.15)', '#9CA3AF']
  return { background: bg, color }
}
</script>

<template>
  <div class="space-y-5 animate-fade-in">

    <!-- Page header -->
    <div class="flex flex-col sm:flex-row sm:items-center gap-3">
      <div>
        <h2 class="text-xl font-bold" style="color: var(--text-primary);">Upstox Instruments</h2>
        <p class="text-sm mt-0.5" style="color: var(--text-muted);">
          {{ formatNumber(total) }} instruments in database
        </p>
      </div>
      <div class="sm:ml-auto flex items-center gap-2">
        <button
          class="btn-primary text-xs gap-1.5 flex items-center"
          :disabled="syncing"
          @click="syncFromFile"
        >
          <svg
            :class="['w-3.5 h-3.5', syncing && 'animate-spin']"
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path
              stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003
                 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          {{ syncing ? 'Syncing…' : 'Sync from File' }}
        </button>
      </div>
    </div>

    <!-- Sync feedback -->
    <div v-if="syncMessage" class="card p-3 text-sm text-emerald-400 border border-emerald-500/30">
      ✓ {{ syncMessage }}
    </div>
    <div v-if="syncError" class="card p-3 text-sm text-red-400 border border-red-500/30">
      ✗ {{ syncError }}
    </div>

    <!-- Filters bar -->
    <div class="card p-3 flex flex-wrap gap-3 items-center">
      <div class="flex-1 min-w-[200px] max-w-sm">
        <SearchBar v-model="search" placeholder="Search symbol, name or ISIN…" />
      </div>

      <!-- Segment filter -->
      <select
        class="input text-sm w-auto min-w-[160px]"
        :value="filterSegment"
        @change="filterSegment = ($event.target as HTMLSelectElement).value"
      >
        <option value="">All Segments</option>
        <option v-for="s in segmentOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
      </select>

      <!-- Exchange filter -->
      <select
        class="input text-sm w-auto min-w-[120px]"
        :value="filterExchange"
        @change="filterExchange = ($event.target as HTMLSelectElement).value"
      >
        <option value="">All Exchanges</option>
        <option v-for="ex in exchangeOptions" :key="ex.value" :value="ex.value">{{ ex.label }}</option>
      </select>

      <!-- Page size -->
      <select
        class="input text-sm w-auto"
        :value="pageSize"
        @change="pageSize = Number(($event.target as HTMLSelectElement).value); page = 1"
      >
        <option v-for="ps in PAGE_SIZE_OPTIONS" :key="ps" :value="ps">{{ ps }} / page</option>
      </select>

      <!-- Reset -->
      <button
        v-if="search || filterSegment || filterExchange"
        class="btn-ghost text-xs"
        @click="resetFilters"
      >
        Reset
      </button>
    </div>

    <!-- Error -->
    <div v-if="error" class="card p-4 text-red-400 text-sm border border-red-500/30">
      {{ error }}
    </div>

    <!-- Table -->
    <DataTable
      :columns="columns"
      :data="data as unknown as Record<string, unknown>[]"
      :loading="loading"
      :sort-by="sortBy"
      :sort-order="sortOrder"
      row-key="instrument_key"
      empty-message="No instruments found — try syncing from file first"
      @sort="handleSort"
    >
      <!-- Symbol -->
      <template #cell-trading_symbol="{ value }">
        <span class="font-semibold text-brand-400 font-mono text-xs">{{ value }}</span>
      </template>

      <!-- Name -->
      <template #cell-name="{ value }">
        <span class="truncate max-w-[220px] block">{{ value }}</span>
      </template>

      <!-- Segment badge -->
      <template #cell-segment_label="{ row }">
        <span
          class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
          :style="segmentChipStyle((row as unknown as UpstoxInstrument).segment)"
        >
          {{ (row as unknown as UpstoxInstrument).segment_label ?? (row as unknown as UpstoxInstrument).segment }}
        </span>
      </template>

      <!-- Exchange badge -->
      <template #cell-exchange="{ value }">
        <span
          class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
          :style="exchangeChipStyle(value as string)"
        >
          {{ value }}
        </span>
      </template>

      <!-- Instrument type -->
      <template #cell-instrument_type="{ value }">
        <span v-if="value" class="text-xs text-gray-400 font-mono">{{ value }}</span>
        <span v-else class="text-xs text-gray-600">—</span>
      </template>

      <!-- ISIN -->
      <template #cell-isin="{ value }">
        <span v-if="value" class="font-mono text-xs text-gray-300">{{ value }}</span>
        <span v-else class="text-xs text-gray-600">—</span>
      </template>

      <!-- Lot size -->
      <template #cell-lot_size="{ value }">
        <span class="text-xs tabular-nums">{{ value ?? '—' }}</span>
      </template>

      <!-- Tick size -->
      <template #cell-tick_size="{ value }">
        <span class="text-xs tabular-nums">{{ value ?? '—' }}</span>
      </template>

      <!-- Chart link -->
      <template #cell-_chart="{ row }">
        <button
          class="p-1.5 rounded hover:bg-brand-500/15 text-gray-500 hover:text-brand-400 transition-colors"
          title="View historical chart"
          @click.stop="viewChart(row as unknown as UpstoxInstrument)"
        >
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
          </svg>
        </button>
      </template>
    </DataTable>

    <!-- Pagination -->
    <Pagination
      :total="total"
      :page="page"
      :page-size="pageSize"
      @update:page="page = $event"
    />
  </div>
</template>
