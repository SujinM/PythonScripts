<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { etoroWatchlistsApi } from '@/api/etoroWatchlists'
import { etoroInstrumentsApi } from '@/api/etoroInstruments'
import type { Watchlist } from '@/types/etoroWatchlist'
import type { EToroTick, LiveTickFrame } from '@/types/portfolio'
import type { InstrumentPriceChange } from '@/api/etoroInstruments'
import { formatPrice } from '@/utils/formatters'

// ── State ──────────────────────────────────────────────────────────────────────

const watchlists    = ref<Watchlist[]>([])
const loading       = ref(false)
const error         = ref<string | null>(null)
const total         = ref(0)
const search        = ref('')
const selectedWl    = ref<Watchlist | null>(null)
const showModal     = ref(false)
const addRelated    = ref(false)

// ── Instrument symbol cache (id → symbol) ────────────────────────────────────

const symbolCache = ref<Record<string, string>>({})

async function fetchSymbols(ids: number[]) {
  const missing = ids.filter(id => !symbolCache.value[String(id)])
  if (!missing.length) return
  try {
    const results = await Promise.allSettled(missing.map(id => etoroInstrumentsApi.getInstrument(id)))
    results.forEach((r, i) => {
      if (r.status === 'fulfilled') {
        symbolCache.value[String(missing[i])] = r.value.symbol
      }
    })
  } catch { /* non-fatal */ }
}

// ── Price-change state (loaded once per modal open) ───────────────────────────

const priceChanges = ref<Record<string, InstrumentPriceChange>>({})

async function fetchPriceChanges(ids: number[]) {
  priceChanges.value = {}
  try {
    const list = await etoroInstrumentsApi.getPriceChanges(ids)
    const map: Record<string, InstrumentPriceChange> = {}
    for (const item of list) map[String(item.instrument_id)] = item
    priceChanges.value = map
  } catch { /* non-fatal — history columns show — */ }
}

// ── Live price state (WebSocket per open modal) ───────────────────────────────

interface LivePrice {
  name:      string
  bid:       number | null
  ask:       number | null
  mid:       number | null
}

// Non-reactive map for prev prices (avoids watcher dependency loop)
const _prevMid = new Map<string, number>()
const tickDir  = ref<Record<string, 'up' | 'down'>>({})
const _flashTimers: Record<string, ReturnType<typeof setTimeout>> = {}

const livePrices   = ref<Record<string, LivePrice>>({})
const wsConnected  = ref(false)
const wsError      = ref<string | null>(null)
let   _ws: WebSocket | null = null
let   _wsReconnect: ReturnType<typeof setTimeout> | null = null
let   _wsStop      = false

function _wsUrl(instrumentIds: string[]): string {
  const base = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/^http/, 'ws')
  return `${base}/api/v1/etoro/ws/live?instruments=${instrumentIds.join(',')}`
}

function _applyTick(id: string, t: EToroTick) {
  const cur = t.mid ?? t.ask ?? t.bid

  // Only store a live-price entry when there is at least one usable price value.
  // This preserves the fallback to priceChanges.current_price for instruments
  // that arrive in the tick frame but carry no price (all null).
  if (t.mid != null || t.ask != null || t.bid != null) {
    livePrices.value[id] = { name: t.name, bid: t.bid, ask: t.ask, mid: t.mid }
  }

  const prev = _prevMid.get(id)

  if (cur == null || prev === undefined || cur === prev) {
    if (cur != null) _prevMid.set(id, cur)
    return
  }
  _prevMid.set(id, cur)

  const dir: 'up' | 'down' = cur > prev ? 'up' : 'down'
  clearTimeout(_flashTimers[id])

  // Remove and re-add so CSS animation always restarts
  if (tickDir.value[id]) {
    delete tickDir.value[id]
    nextTick(() => { tickDir.value[id] = dir })
  } else {
    tickDir.value[id] = dir
  }
  _flashTimers[id] = setTimeout(() => { delete tickDir.value[id] }, 900)
}

function _wsConnect(instrumentIds: string[]) {
  _wsStop = false
  if (!instrumentIds.length) return

  _ws = new WebSocket(_wsUrl(instrumentIds))

  _ws.onopen = () => {
    wsConnected.value = true
    wsError.value     = null
  }

  _ws.onmessage = (event) => {
    try {
      const frame: LiveTickFrame = JSON.parse(event.data as string)
      if (frame.error) { wsError.value = frame.error; return }
      if (!frame.ticks) return
      for (const [id, tick] of Object.entries(frame.ticks)) {
        _applyTick(id, tick as EToroTick)
      }
    } catch { /* ignore malformed frames */ }
  }

  _ws.onclose = () => {
    wsConnected.value = false
    if (_wsStop) return
    _wsReconnect = setTimeout(() => _wsConnect(instrumentIds), 3_000)
  }

  _ws.onerror = () => { _ws?.close() }
}

function _wsDisconnect() {
  _wsStop = true
  _wsReconnect && clearTimeout(_wsReconnect)
  _ws?.close()
  _ws               = null
  wsConnected.value = false
  // Keep livePrices until modal fully closes so no flicker on reconnect
}

onUnmounted(() => { _wsDisconnect(); _prevMid.clear() })

// ── Load ───────────────────────────────────────────────────────────────────────

async function loadWatchlists() {
  loading.value = true
  error.value   = null
  try {
    const result = await etoroWatchlistsApi.getWatchlists({
      items_per_page:     100,
      ensure_builtin:     true,
      add_related_assets: addRelated.value,
    })
    watchlists.value = result.watchlists
    total.value      = result.total
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } }; message?: string }
    error.value = err.response?.data?.detail ?? err.message ?? 'Failed to load watchlists'
  } finally {
    loading.value = false
  }
}

// ── Filtering ──────────────────────────────────────────────────────────────────

const filtered = computed(() => {
  if (!search.value.trim()) return watchlists.value
  const q = search.value.toLowerCase()
  return watchlists.value.filter(w => w.name.toLowerCase().includes(q))
})

// ── Modal ──────────────────────────────────────────────────────────────────────

function openWatchlist(wl: Watchlist) {
  selectedWl.value = wl
  showModal.value  = true
  livePrices.value = {}
  priceChanges.value = {}
  _prevMid.clear()
  tickDir.value = {}
  const ids = wl.items.map(i => i.item_id)
  _wsConnect(ids.map(String))
  fetchSymbols(ids)
  fetchPriceChanges(ids)
}

function closeModal() {
  _wsDisconnect()
  showModal.value    = false
  selectedWl.value   = null
  livePrices.value   = {}
  priceChanges.value = {}
  _prevMid.clear()
  tickDir.value = {}
}

// ── Helpers ────────────────────────────────────────────────────────────────────

function typeChip(type: string): { bg: string; text: string } {
  return type === 'Dynamic'
    ? { bg: 'rgba(99,102,241,0.15)', text: '#818CF8' }
    : { bg: 'rgba(16,185,129,0.15)', text: '#10B981' }
}

function rankLabel(rank: number): string {
  if (rank === 1) return '🥇'
  if (rank === 2) return '🥈'
  if (rank === 3) return '🥉'
  return `#${rank}`
}

/** Best display label: symbol from DB → name from WS tick → ID */
function instrumentLabel(id: number): string {
  return symbolCache.value[String(id)]
    || livePrices.value[String(id)]?.name
    || String(id)
}

/** Current price: prefer live WS mid → ask → bid, then fall back to price-change endpoint */
function currentPrice(id: number): number | null {
  const lp = livePrices.value[String(id)]
  if (lp) return lp.mid ?? lp.ask ?? lp.bid ?? null
  return priceChanges.value[String(id)]?.current_price ?? null
}

function changeColor(val: number | null | undefined): string {
  if (val == null) return 'var(--text-muted)'
  return val >= 0 ? '#4ade80' : '#f87171'
}

function formatChange(val: number | null, pct: number | null): string {
  if (val == null || pct == null) return '—'
  const sign = val >= 0 ? '+' : ''
  return `${sign}${formatPrice(val)} (${sign}${pct.toFixed(2)}%)`
}

onMounted(() => loadWatchlists())
</script>

<template>
  <div class="space-y-5 animate-fade-in">

    <!-- ── Header ──────────────────────────────────────────────── -->
    <div class="flex flex-col sm:flex-row sm:items-center gap-3">
      <div>
        <h2 class="text-xl font-bold" style="color: var(--text-primary);">eToro Watchlists</h2>
        <p class="text-sm mt-0.5" style="color: var(--text-muted);">
          {{ total }} watchlist{{ total !== 1 ? 's' : '' }} for your account
        </p>
      </div>
      <div class="sm:ml-auto flex items-center gap-2">
        <!-- Related assets toggle -->
        <label class="flex items-center gap-1.5 text-xs cursor-pointer select-none" style="color: var(--text-muted);">
          <input
            type="checkbox"
            v-model="addRelated"
            class="w-3.5 h-3.5 accent-brand-500"
            @change="loadWatchlists"
          />
          Related assets
        </label>
        <!-- Refresh -->
        <button
          class="btn-primary text-xs gap-1.5 flex items-center"
          :disabled="loading"
          @click="loadWatchlists"
        >
          <svg
            :class="['w-3.5 h-3.5', loading && 'animate-spin']"
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {{ loading ? 'Loading…' : 'Refresh' }}
        </button>
      </div>
    </div>

    <!-- ── Error ────────────────────────────────────────────────── -->
    <div v-if="error" class="card p-4 text-red-400 text-sm border border-red-500/30">
      {{ error }}
    </div>

    <!-- ── Search bar ───────────────────────────────────────────── -->
    <div class="card p-3">
      <div class="relative max-w-sm">
        <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none"
          fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
        </svg>
        <input
          v-model="search"
          type="text"
          placeholder="Search watchlists…"
          class="input pl-8 text-sm w-full"
        />
      </div>
    </div>

    <!-- ── Skeleton ─────────────────────────────────────────────── -->
    <div v-if="loading && watchlists.length === 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="n in 6" :key="n"
        class="card p-4 space-y-3 animate-pulse"
      >
        <div class="h-4 bg-gray-700/50 rounded w-3/4"></div>
        <div class="h-3 bg-gray-700/30 rounded w-1/2"></div>
        <div class="h-3 bg-gray-700/30 rounded w-1/3"></div>
      </div>
    </div>

    <!-- ── Empty ────────────────────────────────────────────────── -->
    <div
      v-else-if="!loading && filtered.length === 0"
      class="card p-10 text-center"
      style="color: var(--text-muted);"
    >
      <svg class="w-10 h-10 mx-auto mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
          d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
      </svg>
      <p class="text-sm">{{ search ? 'No watchlists match your search.' : 'No watchlists found.' }}</p>
    </div>

    <!-- ── Watchlist cards ──────────────────────────────────────── -->
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="wl in filtered"
        :key="wl.watchlist_id"
        class="card p-4 flex flex-col gap-3 hover:border-brand-500/40 transition-colors cursor-pointer group"
        @click="openWatchlist(wl)"
      >
        <!-- Title row -->
        <div class="flex items-start justify-between gap-2">
          <div class="flex items-center gap-2 min-w-0">
            <!-- Bookmark icon -->
            <svg class="w-4 h-4 flex-shrink-0 text-brand-400" fill="currentColor" viewBox="0 0 20 20">
              <path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z" />
            </svg>
            <span
              class="font-semibold text-sm truncate group-hover:text-brand-400 transition-colors"
              style="color: var(--text-primary);"
            >
              {{ wl.name }}
            </span>
          </div>
          <!-- Default badge -->
          <span
            v-if="wl.is_default"
            class="text-xs px-1.5 py-0.5 rounded flex-shrink-0"
            style="background: rgba(234,179,8,0.15); color: #EAB308;"
          >
            Default
          </span>
        </div>

        <!-- Meta row -->
        <div class="flex items-center gap-3 text-xs" style="color: var(--text-muted);">
          <!-- Type chip -->
          <span
            class="px-2 py-0.5 rounded font-medium"
            :style="typeChip(wl.watchlist_type)"
          >
            {{ wl.watchlist_type }}
          </span>
          <!-- Rank -->
          <span>{{ rankLabel(wl.rank) }}</span>
          <!-- Items count -->
          <span class="ml-auto flex items-center gap-1">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M4 6h16M4 10h16M4 14h10" />
            </svg>
            {{ wl.total_items }} items
          </span>
        </div>

        <!-- Items preview (first 5) -->
        <div v-if="wl.items.length > 0" class="flex flex-wrap gap-1.5 pt-1 border-t border-gray-800/50">
          <span
            v-for="item in wl.items.slice(0, 5)" :key="item.item_id"
            class="text-xs font-mono px-1.5 py-0.5 rounded"
            style="background: rgba(59,130,246,0.1); color: #60A5FA;"
          >
            #{{ item.item_id }}
          </span>
          <span
            v-if="wl.items.length > 5"
            class="text-xs px-1.5 py-0.5 rounded"
            style="color: var(--text-muted);"
          >
            +{{ wl.items.length - 5 }} more
          </span>
        </div>

        <!-- Related assets preview -->
        <div v-if="wl.related_assets.length > 0" class="text-xs" style="color: var(--text-muted);">
          {{ wl.related_assets.length }} related asset{{ wl.related_assets.length !== 1 ? 's' : '' }}
        </div>

        <!-- View link -->
        <div class="mt-auto pt-1 flex justify-end">
          <span class="text-xs text-brand-400 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
            View details
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </span>
        </div>
      </div>
    </div>

    <!-- ── Detail modal ─────────────────────────────────────────── -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showModal && selectedWl"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
          style="background: rgba(0,0,0,0.65);"
          @click.self="closeModal"
        >
          <div
            class="relative w-full max-w-lg rounded-xl border border-gray-700/60 shadow-2xl overflow-hidden"
            style="background: var(--surface-secondary);"
          >
            <!-- Modal header -->
            <div class="flex items-center gap-3 px-5 py-4 border-b border-gray-800/60">
              <svg class="w-5 h-5 text-brand-400" fill="currentColor" viewBox="0 0 20 20">
                <path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z" />
              </svg>
              <div class="flex-1 min-w-0">
                <h3 class="font-semibold text-base truncate" style="color: var(--text-primary);">
                  {{ selectedWl.name }}
                </h3>
                <p class="text-xs mt-0.5" style="color: var(--text-muted);">
                  ID: {{ selectedWl.watchlist_id }}
                  <span v-if="selectedWl.gcid"> · GCID: {{ selectedWl.gcid }}</span>
                </p>
              </div>
              <button
                class="p-1.5 rounded-md text-gray-500 hover:text-gray-300 hover:bg-gray-700/60 transition-colors"
                @click="closeModal"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Modal body -->
            <div class="px-5 py-4 space-y-4 max-h-[70vh] overflow-y-auto">

              <!-- Stats row -->
              <div class="grid grid-cols-3 gap-3">
                <div class="rounded-lg p-3 text-center" style="background: var(--surface-primary);">
                  <p class="text-xs mb-1" style="color: var(--text-muted);">Type</p>
                  <span
                    class="text-xs font-medium px-2 py-0.5 rounded"
                    :style="typeChip(selectedWl.watchlist_type)"
                  >
                    {{ selectedWl.watchlist_type }}
                  </span>
                </div>
                <div class="rounded-lg p-3 text-center" style="background: var(--surface-primary);">
                  <p class="text-xs mb-1" style="color: var(--text-muted);">Total items</p>
                  <p class="text-lg font-bold" style="color: var(--text-primary);">{{ selectedWl.total_items }}</p>
                </div>
                <div class="rounded-lg p-3 text-center" style="background: var(--surface-primary);">
                  <p class="text-xs mb-1" style="color: var(--text-muted);">Rank</p>
                  <p class="text-lg font-bold" style="color: var(--text-primary);">{{ rankLabel(selectedWl.rank) }}</p>
                </div>
              </div>

              <!-- Badges -->
              <div class="flex flex-wrap gap-2">
                <span
                  v-if="selectedWl.is_default"
                  class="text-xs px-2 py-0.5 rounded"
                  style="background: rgba(234,179,8,0.15); color: #EAB308;"
                >
                  ★ Default watchlist
                </span>
                <span
                  v-if="selectedWl.is_user_selected_default"
                  class="text-xs px-2 py-0.5 rounded"
                  style="background: rgba(16,185,129,0.15); color: #10B981;"
                >
                  ✓ User selected default
                </span>
                <span
                  v-if="selectedWl.dynamic_url"
                  class="text-xs px-2 py-0.5 rounded"
                  style="background: rgba(99,102,241,0.15); color: #818CF8;"
                >
                  Dynamic URL
                </span>
              </div>

              <!-- Items list with live prices + period changes -->
              <div v-if="selectedWl.items.length > 0">
                <div class="flex items-center justify-between mb-2">
                  <p class="text-xs font-semibold uppercase tracking-wider" style="color: var(--text-muted);">
                    Instruments ({{ selectedWl.items.length }})
                  </p>
                  <!-- WebSocket status badge -->
                  <span
                    class="flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full"
                    :style="wsConnected
                      ? 'background: rgba(16,185,129,0.15); color: #10B981;'
                      : wsError
                        ? 'background: rgba(239,68,68,0.15); color: #EF4444;'
                        : 'background: rgba(234,179,8,0.15); color: #EAB308;'"
                  >
                    <span
                      class="inline-block w-1.5 h-1.5 rounded-full"
                      :style="wsConnected ? 'background:#10B981;' : wsError ? 'background:#EF4444;' : 'background:#EAB308;'"
                    ></span>
                    {{ wsConnected ? 'Live' : wsError ? 'Error' : 'Connecting…' }}
                  </span>
                </div>

                <div class="rounded-lg overflow-x-auto border border-gray-800/50">
                  <table class="w-full text-xs" style="min-width: 480px;">
                    <thead>
                      <tr style="background: var(--surface-primary);">
                        <th class="text-left px-3 py-2 font-medium" style="color: var(--text-muted);">Symbol</th>
                        <th class="text-right px-3 py-2 font-medium" style="color: var(--text-muted);">Price</th>
                        <th class="text-right px-3 py-2 font-medium" style="color: var(--text-muted);">1-Day</th>
                        <th class="text-right px-3 py-2 font-medium" style="color: var(--text-muted);">1-Month</th>
                        <th class="text-right px-3 py-2 font-medium" style="color: var(--text-muted);">1-Year</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="item in selectedWl.items"
                        :key="item.item_id"
                        class="border-t border-gray-800/40 transition-colors"
                      >
                        <!-- Symbol -->
                        <td class="px-3 py-2 font-semibold" style="color: var(--text-primary);">
                          {{ instrumentLabel(item.item_id) }}
                        </td>

                        <!-- Current price (live WS, flash-colored number only) -->
                        <td class="px-3 py-2 text-right font-mono font-semibold">
                          <span
                            :class="tickDir[String(item.item_id)] === 'up' ? 'tick-up' : tickDir[String(item.item_id)] === 'down' ? 'tick-down' : ''"
                            :style="{ color: tickDir[String(item.item_id)] === 'up' ? '#4ade80' : tickDir[String(item.item_id)] === 'down' ? '#f87171' : 'var(--text-primary)' }"
                          >
                            {{ currentPrice(item.item_id) != null
                                ? '$' + currentPrice(item.item_id)!.toFixed(2)
                                : '—' }}
                          </span>
                        </td>

                        <!-- 1-Day change -->
                        <td class="px-3 py-2 text-right font-mono">
                          <span :style="{ color: changeColor(priceChanges[String(item.item_id)]?.change_1d_value) }">
                            {{ formatChange(
                                priceChanges[String(item.item_id)]?.change_1d_value ?? null,
                                priceChanges[String(item.item_id)]?.change_1d_pct   ?? null,
                              ) }}
                          </span>
                        </td>

                        <!-- 1-Month change -->
                        <td class="px-3 py-2 text-right font-mono">
                          <span :style="{ color: changeColor(priceChanges[String(item.item_id)]?.change_1m_value) }">
                            {{ formatChange(
                                priceChanges[String(item.item_id)]?.change_1m_value ?? null,
                                priceChanges[String(item.item_id)]?.change_1m_pct   ?? null,
                              ) }}
                          </span>
                        </td>

                        <!-- 1-Year change -->
                        <td class="px-3 py-2 text-right font-mono">
                          <span :style="{ color: changeColor(priceChanges[String(item.item_id)]?.change_1y_value) }">
                            {{ formatChange(
                                priceChanges[String(item.item_id)]?.change_1y_value ?? null,
                                priceChanges[String(item.item_id)]?.change_1y_pct   ?? null,
                              ) }}
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <p v-if="wsError" class="mt-2 text-xs" style="color: #EF4444;">
                  WebSocket error: {{ wsError }}
                </p>
              </div>
              <p v-else class="text-xs" style="color: var(--text-muted);">No items in this watchlist.</p>

              <!-- Related assets -->
              <div v-if="selectedWl.related_assets.length > 0">
                <p class="text-xs font-semibold mb-2 uppercase tracking-wider" style="color: var(--text-muted);">
                  Related assets ({{ selectedWl.related_assets.length }})
                </p>
                <div class="flex flex-wrap gap-1.5">
                  <span
                    v-for="assetId in selectedWl.related_assets"
                    :key="assetId"
                    class="text-xs font-mono px-2 py-0.5 rounded"
                    style="background: rgba(107,114,128,0.15); color: #9CA3AF;"
                  >
                    {{ assetId }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Modal footer -->
            <div class="px-5 py-3 border-t border-gray-800/60 flex justify-end">
              <button class="btn-ghost text-xs" @click="closeModal">Close</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-active .relative,
.modal-leave-active .relative {
  transition: transform 0.2s ease;
}
.modal-enter-from .relative {
  transform: scale(0.95);
}

/* Live tick price-number flash — color glow on the span only */
@keyframes flash-up {
  0%   { text-shadow: 0 0 8px rgba(34, 197, 94, 0.9); }
  100% { text-shadow: none; }
}
@keyframes flash-down {
  0%   { text-shadow: 0 0 8px rgba(239, 68, 68, 0.9); }
  100% { text-shadow: none; }
}
.tick-up {
  animation: flash-up 0.9s ease-out;
}
.tick-down {
  animation: flash-down 0.9s ease-out;
}
</style>
