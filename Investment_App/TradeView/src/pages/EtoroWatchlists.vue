<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { etoroWatchlistsApi } from '@/api/etoroWatchlists'
import type { Watchlist } from '@/types/etoroWatchlist'
import type { EToroTick, LiveTickFrame } from '@/types/portfolio'
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

// ── Live price state (per open modal) ─────────────────────────────────────────

interface LivePrice {
  name:      string
  bid:       number | null
  ask:       number | null
  mid:       number | null
  updatedAt: number
}

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
      if (frame.error) {
        wsError.value = frame.error
        return
      }
      if (!frame.ticks) return
      for (const [id, tick] of Object.entries(frame.ticks)) {
        const t = tick as EToroTick
        livePrices.value[id] = {
          name:      t.name,
          bid:       t.bid,
          ask:       t.ask,
          mid:       t.mid,
          updatedAt: Date.now(),
        }
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
  _ws             = null
  wsConnected.value = false
  livePrices.value  = {}
  wsError.value     = null
}

onUnmounted(_wsDisconnect)

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
  selectedWl.value  = wl
  showModal.value   = true
  livePrices.value  = {}
  const ids = wl.items.map(i => String(i.item_id))
  _wsConnect(ids)
}

function closeModal() {
  _wsDisconnect()
  showModal.value  = false
  selectedWl.value = null
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

function priceColor(mid: number | null | undefined, bid: number | null | undefined, ask: number | null | undefined): string {
  if (mid == null && bid == null) return 'var(--text-muted)'
  return 'var(--text-primary)'
}

function instrumentName(id: number): string {
  return livePrices.value[String(id)]?.name ?? ''
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

              <!-- Items list with live prices -->
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
                      :style="wsConnected
                        ? 'background:#10B981;'
                        : wsError
                          ? 'background:#EF4444;'
                          : 'background:#EAB308;'"
                    ></span>
                    {{ wsConnected ? 'Live' : wsError ? 'Error' : 'Connecting…' }}
                  </span>
                </div>

                <div class="rounded-lg overflow-hidden border border-gray-800/50">
                  <table class="w-full text-xs">
                    <thead>
                      <tr style="background: var(--surface-primary);">
                        <th class="text-left px-3 py-2 font-medium" style="color: var(--text-muted);">Instrument</th>
                        <th class="text-right px-3 py-2 font-medium" style="color: var(--text-muted);">Bid</th>
                        <th class="text-right px-3 py-2 font-medium" style="color: var(--text-muted);">Ask</th>
                        <th class="text-right px-3 py-2 font-medium" style="color: var(--text-muted);">Mid</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="item in selectedWl.items"
                        :key="item.item_id"
                        class="border-t border-gray-800/40 hover:bg-white/2 transition-colors"
                      >
                        <!-- Name / ID -->
                        <td class="px-3 py-2">
                          <span
                            v-if="livePrices[String(item.item_id)]?.name"
                            class="font-semibold"
                            style="color: var(--text-primary);"
                          >
                            {{ livePrices[String(item.item_id)].name }}
                          </span>
                          <span
                            v-else
                            class="font-mono animate-pulse"
                            style="color: var(--text-muted);"
                          >
                            {{ item.item_id }}
                          </span>
                        </td>
                        <!-- Bid -->
                        <td class="px-3 py-2 text-right font-mono">
                          <span
                            v-if="livePrices[String(item.item_id)]?.bid != null"
                            style="color: #F87171;"
                          >
                            {{ formatPrice(livePrices[String(item.item_id)].bid!) }}
                          </span>
                          <span v-else style="color: var(--text-muted);">—</span>
                        </td>
                        <!-- Ask -->
                        <td class="px-3 py-2 text-right font-mono">
                          <span
                            v-if="livePrices[String(item.item_id)]?.ask != null"
                            style="color: #34D399;"
                          >
                            {{ formatPrice(livePrices[String(item.item_id)].ask!) }}
                          </span>
                          <span v-else style="color: var(--text-muted);">—</span>
                        </td>
                        <!-- Mid -->
                        <td class="px-3 py-2 text-right font-mono">
                          <span
                            v-if="livePrices[String(item.item_id)]?.mid != null"
                            class="font-semibold"
                            style="color: var(--text-primary);"
                          >
                            {{ formatPrice(livePrices[String(item.item_id)].mid!) }}
                          </span>
                          <span v-else style="color: var(--text-muted);">—</span>
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
</style>
