<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useInstrumentsStore } from '@/stores/instrumentsStore'
import type { Instrument, TableColumn } from '@/types/instrument'
import { ASSET_TYPES, EXCHANGES, PAGE_SIZE_OPTIONS } from '@/utils/constants'
import DataTable from '@/components/common/DataTable.vue'
import SearchBar from '@/components/common/SearchBar.vue'
import Pagination from '@/components/common/Pagination.vue'
import Badge from '@/components/common/Badge.vue'
import { formatNumber } from '@/utils/formatters'
import { useRouter } from 'vue-router'

const store  = useInstrumentsStore()
const router = useRouter()
const route  = useRoute()

const searchQuery = ref(String(route.query.search ?? ''))

onMounted(async () => {
  if (searchQuery.value) store.setFilters({ search: searchQuery.value })
  await store.fetchInstruments()
})

watch(searchQuery, (val) => {
  store.setFilters({ search: val })
})

// Sync URL query param with search
watch(searchQuery, (val) => {
  router.replace({ query: val ? { search: val } : {} })
})

const columns: TableColumn<Instrument>[] = [
  { key: 'instrumentId', label: 'ID',           sortable: true, width: 'w-16', align: 'right' },
  { key: 'symbol',       label: 'Symbol',        sortable: true },
  { key: 'displayName',  label: 'Name',          sortable: true },
  { key: 'exchange',     label: 'Exchange',      sortable: true },
  { key: 'assetType',    label: 'Type',          sortable: true },
  { key: 'currency',     label: 'Currency',      sortable: true, align: 'center' },
  { key: 'isTradable',   label: 'Tradable',      sortable: true, align: 'center' },
]

const selectedRows = ref<Instrument[]>([])

function handleSort(key: string, order: 'asc' | 'desc') {
  store.setPagination({ sortBy: key as keyof Instrument, sortOrder: order, page: 1 })
}

function handleRowClick(row: Instrument) {
  router.push({ name: 'instrument-detail', params: { symbol: row.symbol } })
}

function handleSelectionChange(rows: Instrument[]) {
  selectedRows.value = rows
}

function resetFilters() {
  searchQuery.value = ''
  store.clearFilters()
}
</script>

<template>
  <div class="space-y-5 animate-fade-in">
    <!-- Page header -->
    <div class="flex flex-col sm:flex-row sm:items-center gap-3">
      <div>
        <h2 class="text-xl font-bold" style="color: var(--text-primary);">Instruments</h2>
        <p class="text-sm mt-0.5" style="color: var(--text-muted);">
          {{ formatNumber(store.totalCount) }} instruments total
        </p>
      </div>
      <div class="sm:ml-auto flex items-center gap-2">
        <button
          v-if="selectedRows.length > 0"
          class="btn-secondary text-xs"
          @click="selectedRows = []"
        >
          {{ selectedRows.length }} selected
        </button>
        <button class="btn-primary text-xs gap-1.5" @click="store.exportToCsv">
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Export CSV
        </button>
      </div>
    </div>

    <!-- Filters bar -->
    <div class="card p-3 flex flex-wrap gap-3 items-center">
      <!-- Search -->
      <div class="flex-1 min-w-[200px] max-w-sm">
        <SearchBar v-model="searchQuery" placeholder="Search symbol or name…" />
      </div>

      <!-- Asset type filter -->
      <select
        class="input text-sm w-auto min-w-[130px]"
        :value="store.filters.assetType ?? ''"
        @change="store.setFilters({ assetType: ($event.target as HTMLSelectElement).value as any || undefined })"
      >
        <option value="">All Types</option>
        <option v-for="at in ASSET_TYPES" :key="at.value" :value="at.value">{{ at.label }}</option>
      </select>

      <!-- Exchange filter -->
      <select
        class="input text-sm w-auto min-w-[130px]"
        :value="store.filters.exchange ?? ''"
        @change="store.setFilters({ exchange: ($event.target as HTMLSelectElement).value || undefined })"
      >
        <option value="">All Exchanges</option>
        <option v-for="ex in EXCHANGES" :key="ex" :value="ex">{{ ex }}</option>
      </select>

      <!-- Tradable filter -->
      <select
        class="input text-sm w-auto min-w-[120px]"
        @change="(e) => {
          const v = (e.target as HTMLSelectElement).value
          store.setFilters({ isTradable: v === '' ? undefined : v === 'true' })
        }"
      >
        <option value="">All</option>
        <option value="true">Tradable</option>
        <option value="false">Non-tradable</option>
      </select>

      <!-- Page size -->
      <select
        class="input text-sm w-auto"
        :value="store.pagination.pageSize"
        @change="store.setPagination({ pageSize: Number(($event.target as HTMLSelectElement).value), page: 1 })"
      >
        <option v-for="ps in PAGE_SIZE_OPTIONS" :key="ps" :value="ps">{{ ps }} / page</option>
      </select>

      <!-- Reset -->
      <button
        v-if="store.filters.search || store.filters.assetType || store.filters.exchange || store.filters.isTradable !== undefined"
        class="btn-ghost text-xs"
        @click="resetFilters"
      >
        Reset
      </button>
    </div>

    <!-- Table -->
    <DataTable
      :columns="columns"
      :data="store.filteredInstruments"
      :loading="store.loading"
      :sort-by="String(store.pagination.sortBy ?? '')"
      :sort-order="store.pagination.sortOrder"
      :selectable="true"
      row-key="instrumentId"
      empty-message="No instruments match your filters"
      @sort="handleSort"
      @row-click="handleRowClick"
      @selection-change="handleSelectionChange"
    >
      <!-- Symbol cell -->
      <template #cell-symbol="{ value }">
        <span class="font-semibold text-brand-400 font-mono text-xs">{{ value }}</span>
      </template>

      <!-- Asset type cell -->
      <template #cell-assetType="{ value }">
        <Badge :value="String(value)" type="assetType" />
      </template>

      <!-- Tradable cell -->
      <template #cell-isTradable="{ value }">
        <span
          :class="[
            'inline-flex items-center justify-center w-5 h-5 rounded-full text-xs',
            value ? 'bg-emerald-500/10 text-emerald-400' : 'bg-gray-500/10 text-gray-500',
          ]"
        >
          {{ value ? '✓' : '✗' }}
        </span>
      </template>

      <!-- Currency cell -->
      <template #cell-currency="{ value }">
        <span class="text-xs font-mono" style="color: var(--text-muted);">{{ value }}</span>
      </template>
    </DataTable>

    <!-- Pagination -->
    <Pagination
      :total="store.totalCount"
      :page="store.pagination.page"
      :page-size="store.pagination.pageSize"
      @update:page="store.setPagination({ page: $event })"
    />
  </div>
</template>
