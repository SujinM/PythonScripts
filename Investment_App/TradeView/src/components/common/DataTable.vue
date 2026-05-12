<script setup lang="ts" generic="T extends Record<string, unknown>">
import { ref, computed } from 'vue'
import LoadingSkeleton from './LoadingSkeleton.vue'
import type { TableColumn, SortOrder } from '@/types/instrument'

interface Props {
  columns: TableColumn<T>[]
  data: T[]
  loading?: boolean
  sortBy?: string
  sortOrder?: SortOrder
  selectable?: boolean
  rowKey?: keyof T
  emptyMessage?: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  selectable: false,
  rowKey: 'id' as keyof T,
  emptyMessage: 'No data available',
})

const emit = defineEmits<{
  sort: [key: string, order: SortOrder]
  'row-click': [row: T]
  'selection-change': [rows: T[]]
}>()

const selected   = ref<Set<unknown>>(new Set())
const allChecked = computed(
  () => props.data.length > 0 && props.data.every((r) => selected.value.has(r[props.rowKey])),
)

function toggleAll() {
  if (allChecked.value) {
    selected.value.clear()
  } else {
    props.data.forEach((r) => selected.value.add(r[props.rowKey]))
  }
  emitSelection()
}

function toggleRow(row: T) {
  const key = row[props.rowKey]
  if (selected.value.has(key)) {
    selected.value.delete(key)
  } else {
    selected.value.add(key)
  }
  emitSelection()
}

function emitSelection() {
  const rows = props.data.filter((r) => selected.value.has(r[props.rowKey]))
  emit('selection-change', rows)
}

function handleSort(key: string) {
  const order: SortOrder =
    props.sortBy === key && props.sortOrder === 'asc' ? 'desc' : 'asc'
  emit('sort', key, order)
}

function getCellValue(row: T, col: TableColumn<T>): string {
  const val = row[col.key as keyof T]
  return col.formatter ? col.formatter(val, row) : String(val ?? '—')
}
</script>

<template>
  <div class="overflow-x-auto rounded-xl border" style="border-color: var(--surface-border);">
    <table class="w-full text-sm border-collapse">
      <!-- Head -->
      <thead>
        <tr class="border-b" style="border-color: var(--surface-border); background-color: var(--surface-secondary);">
          <th v-if="selectable" class="w-10 px-4 py-3">
            <input
              type="checkbox"
              class="rounded border-gray-600 bg-gray-800 text-brand-500 focus:ring-brand-500/40"
              :checked="allChecked"
              @change="toggleAll"
            />
          </th>
          <th
            v-for="col in columns"
            :key="String(col.key)"
            :class="[
              'px-4 py-3 font-medium text-xs uppercase tracking-wide whitespace-nowrap select-none',
              col.sortable ? 'cursor-pointer hover:text-white' : '',
              col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left',
              col.width ?? '',
            ]"
            style="color: var(--text-muted);"
            @click="col.sortable && handleSort(String(col.key))"
          >
            <span class="inline-flex items-center gap-1">
              {{ col.label }}
              <template v-if="col.sortable">
                <svg
                  v-if="sortBy === String(col.key)"
                  :class="['w-3.5 h-3.5 text-brand-400', sortOrder === 'desc' ? 'rotate-180' : '']"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
                </svg>
                <svg v-else class="w-3.5 h-3.5 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                </svg>
              </template>
            </span>
          </th>
        </tr>
      </thead>

      <!-- Body -->
      <tbody>
        <!-- Loading skeleton rows -->
        <template v-if="loading">
          <tr v-for="i in 8" :key="`skel-${i}`" class="border-b animate-pulse" style="border-color: var(--surface-border);">
            <td v-if="selectable" class="px-4 py-3">
              <div class="skeleton h-4 w-4 rounded" />
            </td>
            <td v-for="col in columns" :key="String(col.key)" class="px-4 py-3">
              <div class="skeleton h-4 rounded" :class="col.width ?? 'w-full'" />
            </td>
          </tr>
        </template>

        <!-- Empty state -->
        <tr v-else-if="!loading && data.length === 0">
          <td
            :colspan="columns.length + (selectable ? 1 : 0)"
            class="px-4 py-12 text-center"
            style="color: var(--text-muted);"
          >
            <svg class="mx-auto w-8 h-8 mb-2 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {{ emptyMessage }}
          </td>
        </tr>

        <!-- Data rows -->
        <tr
          v-for="row in data"
          v-else
          :key="String(row[rowKey])"
          class="border-b transition-colors hover:bg-white/3 cursor-pointer"
          style="border-color: var(--surface-border);"
          @click="emit('row-click', row)"
        >
          <td v-if="selectable" class="px-4 py-3" @click.stop>
            <input
              type="checkbox"
              class="rounded border-gray-600 bg-gray-800 text-brand-500 focus:ring-brand-500/40"
              :checked="selected.has(row[rowKey])"
              @change="toggleRow(row)"
            />
          </td>
          <td
            v-for="col in columns"
            :key="String(col.key)"
            :class="[
              'px-4 py-3',
              col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left',
            ]"
            style="color: var(--text-secondary);"
          >
            <slot :name="`cell-${String(col.key)}`" :value="row[col.key as keyof T]" :row="row">
              {{ getCellValue(row, col) }}
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
