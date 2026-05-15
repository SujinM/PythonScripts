<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import DataTable from '@/components/common/DataTable.vue'
import SearchBar from '@/components/common/SearchBar.vue'
import Pagination from '@/components/common/Pagination.vue'
import { etoroInstrumentsApi } from '@/api/etoroInstruments'
import type { EtoroInstrument } from '@/types/etoroInstrument'
import { ETORO_INSTRUMENT_TYPES } from '@/types/etoroInstrument'
import type { TableColumn, SortOrder } from '@/types/instrument'

// ── State ─────────────────────────────────────────────────────────────────────

const data        = ref<EtoroInstrument[]>([])
const loading     = ref(false)
const syncing     = ref(false)
const error       = ref<string | null>(null)
const syncMessage = ref<string | null>(null)
const syncError   = ref<string | null>(null)

const total      = ref(0)
const page       = ref(1)
const pageSize   = ref(50)
const totalPages = ref(1)

const search             = ref('')
const filterTypeId       = ref<number | ''>('')
const sortBy             = ref('instrument_id')
const sortOrder          = ref<SortOrder>('asc')

const PAGE_SIZE_OPTIONS = [25, 50, 100, 200]

const typeOptions = Object.entries(ETORO_INSTRUMENT_TYPES).map(([id, label]) => ({
  value: Number(id),
  label,
}))

// ── Table columns ─────────────────────────────────────────────────────────────

const columns = computed<TableColumn<Record<string, unknown>>[]>(() => [
  { key: 'instrument_id',  label: 'ID',          sortable: true,  width: '70px' },
  { key: 'symbol',         label: 'Symbol',       sortable: true },
  { key: 'display_name',   label: 'Name',         sortable: true },
  { key: 'instrument_type', label: 'Type',        sortable: false },
  { key: 'exchange_id',    label: 'Exchange',     sortable: true,  width: '90px' },
  { key: 'price_source',   label: 'Price Source', sortable: false },
  { key: 'has_expiration_date', label: 'Expires', sortable: false, width: '80px' },
])

// ── Data loading ──────────────────────────────────────────────────────────────

async function loadData() {
  loading.value = true
  error.value   = null
  try {
    const result = await etoroInstrumentsApi.getInstruments({
      page:                page.value,
      page_size:           pageSize.value,
      search:              search.value || undefined,
      instrument_type_id:  filterTypeId.value !== '' ? filterTypeId.value : undefined,
      sort_by:             sortBy.value,
      sort_order:          sortOrder.value,
    })
    data.value        = result.data
    total.value       = result.total
    totalPages.value  = result.total_pages
    page.value        = result.page
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } }; message?: string }
    error.value = err.response?.data?.detail ?? err.message ?? 'Failed to load instruments'
  } finally {
    loading.value = false
  }
}

async function syncFromEtoro() {
  syncing.value    = true
  syncMessage.value = null
  syncError.value  = null
  try {
    const result = await etoroInstrumentsApi.syncInstruments()
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
  search.value       = ''
  filterTypeId.value = ''
  page.value         = 1
  loadData()
}

// Re-fetch on filter/page changes
watch([search, filterTypeId], () => {
  page.value = 1
  loadData()
})

watch([page, pageSize], () => loadData())

onMounted(() => loadData())

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatNumber(n: number) {
  return new Intl.NumberFormat().format(n)
}

function typeChipStyle(typeId: number | null | undefined): Record<string, string> {
  const map: Record<number, [string, string]> = {
    1: ['rgba(16,185,129,0.15)',  '#10B981'],  // Forex     — emerald
    2: ['rgba(245,158,11,0.15)',  '#F59E0B'],  // Commod    — amber
    3: ['rgba(99,102,241,0.15)',  '#818CF8'],  // Indices   — indigo
    4: ['rgba(59,130,246,0.15)',  '#60A5FA'],  // Stocks    — blue
    5: ['rgba(168,85,247,0.15)',  '#C084FC'],  // ETFs      — purple
    6: ['rgba(234,179,8,0.15)',   '#EAB308'],  // Crypto    — yellow
  }
  const [bg, color] = map[typeId ?? 0] ?? ['rgba(107,114,128,0.15)', '#9CA3AF']
  return { background: bg, color }
}
</script>

<template>
  <div class="space-y-5 animate-fade-in">

    <!-- Page header -->
    <div class="flex flex-col sm:flex-row sm:items-center gap-3">
      <div>
        <h2 class="text-xl font-bold" style="color: var(--text-primary);">eToro Markets</h2>
        <p class="text-sm mt-0.5" style="color: var(--text-muted);">
          {{ formatNumber(total) }} instruments in database
        </p>
      </div>
      <div class="sm:ml-auto flex items-center gap-2">
        <button
          class="btn-primary text-xs gap-1.5 flex items-center"
          :disabled="syncing"
          @click="syncFromEtoro"
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
          {{ syncing ? 'Syncing…' : 'Sync from eToro' }}
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
        <SearchBar v-model="search" placeholder="Search symbol or name…" />
      </div>

      <!-- Type filter -->
      <select
        class="input text-sm w-auto min-w-[140px]"
        :value="filterTypeId"
        @change="filterTypeId = ($event.target as HTMLSelectElement).value === ''
          ? ''
          : Number(($event.target as HTMLSelectElement).value)"
      >
        <option value="">All Types</option>
        <option v-for="t in typeOptions" :key="t.value" :value="t.value">{{ t.label }}</option>
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
        v-if="search || filterTypeId !== ''"
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
      row-key="instrument_id"
      empty-message="No instruments found — try syncing from eToro first"
      @sort="handleSort"
    >
      <!-- Symbol -->
      <template #cell-symbol="{ value }">
        <span class="font-semibold text-brand-400 font-mono text-xs">{{ value }}</span>
      </template>

      <!-- Name with avatar -->
      <template #cell-display_name="{ row }">
        <div class="flex items-center gap-2">
          <img
            v-if="(row as unknown as EtoroInstrument).image_url"
            :src="(row as unknown as EtoroInstrument).image_url ?? undefined"
            :alt="(row as unknown as EtoroInstrument).symbol"
            class="w-5 h-5 rounded-full object-cover flex-shrink-0"
            loading="lazy"
            @error="($event.target as HTMLImageElement).style.display = 'none'"
          />
          <span class="truncate max-w-[220px]">{{ (row as unknown as EtoroInstrument).display_name }}</span>
        </div>
      </template>

      <!-- Type badge -->
      <template #cell-instrument_type="{ row }">
        <span
          v-if="(row as unknown as EtoroInstrument).instrument_type"
          class="inline-block px-2 py-0.5 rounded text-xs font-medium"
          :style="typeChipStyle((row as unknown as EtoroInstrument).instrument_type_id)"
        >
          {{ (row as unknown as EtoroInstrument).instrument_type }}
        </span>
        <span v-else class="text-xs" style="color: var(--text-muted);">—</span>
      </template>

      <!-- Exchange ID -->
      <template #cell-exchange_id="{ value }">
        <span class="text-xs font-mono" style="color: var(--text-muted);">
          {{ value ?? '—' }}
        </span>
      </template>

      <!-- Price source -->
      <template #cell-price_source="{ value }">
        <span class="text-xs" style="color: var(--text-muted);">{{ value ?? '—' }}</span>
      </template>

      <!-- Has expiry -->
      <template #cell-has_expiration_date="{ value }">
        <span
          :class="[
            'inline-flex items-center justify-center w-5 h-5 rounded-full text-xs',
            value ? 'bg-amber-500/10 text-amber-400' : 'bg-gray-500/10 text-gray-500',
          ]"
        >
          {{ value ? '✓' : '—' }}
        </span>
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
