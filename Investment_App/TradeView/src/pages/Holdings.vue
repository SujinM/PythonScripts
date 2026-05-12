<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { usePortfolioStore } from '@/stores/portfolioStore'
import { formatCurrency, formatPercent, formatNumber } from '@/utils/formatters'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import SearchBar from '@/components/common/SearchBar.vue'
import Badge from '@/components/common/Badge.vue'

const portfolio = usePortfolioStore()
const currency = computed(() => portfolio.activeBroker === 'etoro' ? 'USD' : 'INR')
const fmt = (v: number) => formatCurrency(v, currency.value)

const searchQuery = ref('')
const activeTab   = ref<'holdings' | 'positions' | 'trades'>('holdings')

onMounted(async () => {
  await Promise.all([
    portfolio.fetchHoldings(),
    portfolio.fetchPositions(),
    portfolio.fetchTrades(),
  ])
})

watch(() => portfolio.activeBroker, async () => {
  await Promise.all([
    portfolio.fetchHoldings(),
    portfolio.fetchPositions(),
    portfolio.fetchTrades(),
  ])
})

// ── Filtered holdings ─────────────────────────────────────────────────────────
const filteredHoldings = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return portfolio.activeHoldings.filter(
    (h) =>
      !q ||
      h.trading_symbol.toLowerCase().includes(q) ||
      h.instrument_key.toLowerCase().includes(q) ||
      h.exchange.toLowerCase().includes(q),
  )
})

const filteredPositions = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return portfolio.activePositions.filter(
    (p) =>
      !q ||
      p.trading_symbol.toLowerCase().includes(q) ||
      p.exchange.toLowerCase().includes(q),
  )
})

const filteredTrades = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return portfolio.activeTrades.filter(
    (t) =>
      !q ||
      t.trading_symbol.toLowerCase().includes(q) ||
      t.transaction_type.toLowerCase().includes(q),
  )
})

// ── PnL colour helper ─────────────────────────────────────────────────────────
function pnlClass(value: number): string {
  if (value > 0) return 'text-emerald-400'
  if (value < 0) return 'text-red-400'
  return ''
}
</script>

<template>
  <div class="space-y-5 animate-fade-in">

    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center gap-3">
      <div>
        <h2 class="text-xl font-bold" style="color: var(--text-primary);">Holdings</h2>
        <p class="text-sm mt-0.5" style="color: var(--text-muted);">
          {{ portfolio.activeBroker.toUpperCase() }} — {{ formatNumber(portfolio.activeHoldings.length) }} holdings
        </p>
      </div>
      <div class="sm:ml-auto flex items-center gap-2">
        <!-- Broker selector -->
        <select
          class="input text-sm"
          :value="portfolio.activeBroker"
          @change="portfolio.selectBroker(($event.target as HTMLSelectElement).value)"
        >
          <option v-for="b in portfolio.brokers" :key="b.id" :value="b.id">
            {{ b.name ?? b.id }}
          </option>
        </select>
        <button class="btn-secondary text-xs" @click="portfolio.fetchHoldings()">
          Refresh
        </button>
      </div>
    </div>

    <!-- Tabs -->
    <div class="flex gap-1 border-b" style="border-color: var(--surface-border);">
      <button
        v-for="tab in (['holdings', 'positions', 'trades'] as const)"
        :key="tab"
        :class="[
          'px-4 py-2 text-sm font-medium capitalize transition-colors',
          activeTab === tab
            ? 'border-b-2 border-brand-500 text-brand-400'
            : 'text-gray-400 hover:text-white',
        ]"
        @click="activeTab = tab"
      >
        {{ tab }}
        <span
          v-if="tab === 'holdings'"
          class="ml-1.5 text-xs px-1.5 py-0.5 rounded-full"
          style="background-color: var(--surface-secondary);"
        >{{ portfolio.activeHoldings.length }}</span>
        <span
          v-if="tab === 'positions'"
          class="ml-1.5 text-xs px-1.5 py-0.5 rounded-full"
          style="background-color: var(--surface-secondary);"
        >{{ portfolio.activePositions.length }}</span>
        <span
          v-if="tab === 'trades'"
          class="ml-1.5 text-xs px-1.5 py-0.5 rounded-full"
          style="background-color: var(--surface-secondary);"
        >{{ portfolio.activeTrades.length }}</span>
      </button>
    </div>

    <!-- Search -->
    <div class="max-w-sm">
      <SearchBar v-model="searchQuery" placeholder="Search symbol, exchange…" />
    </div>

    <!-- Loading -->
    <div v-if="portfolio.loading" class="flex justify-center py-16">
      <LoadingSpinner size="lg" />
    </div>

    <!-- ── Holdings table ───────────────────────────────────────────────── -->
    <div v-else-if="activeTab === 'holdings'" class="card overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b" style="border-color: var(--surface-border); background-color: var(--surface-secondary);">
            <th class="px-4 py-2.5 text-left text-xs uppercase tracking-wide" style="color: var(--text-muted);">Symbol</th>
            <th class="px-4 py-2.5 text-left text-xs uppercase tracking-wide" style="color: var(--text-muted);">Exchange</th>
            <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">Qty</th>
            <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">Avg Price</th>
            <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">LTP</th>
            <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">Invested</th>
            <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">Current</th>
            <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">P&amp;L</th>
            <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">Return%</th>
          </tr>
        </thead>
        <tbody class="divide-y" style="border-color: var(--surface-border);">
          <tr
            v-for="h in filteredHoldings"
            :key="h.instrument_key"
            class="hover:bg-white/5 transition-colors"
          >
            <td class="px-4 py-3">
              <div class="font-mono font-semibold text-xs" style="color: var(--text-primary);">
                {{ h.trading_symbol }}
              </div>
              <div class="text-[10px] mt-0.5" style="color: var(--text-muted);">
                {{ h.broker }}
              </div>
            </td>
            <td class="px-4 py-3">
              <Badge :value="h.exchange" />
            </td>
            <td class="px-4 py-3 text-right font-mono text-xs" style="color: var(--text-secondary);">
              {{ h.quantity }}
            </td>
            <td class="px-4 py-3 text-right font-mono text-xs" style="color: var(--text-secondary);">
              {{ fmt(h.average_price) }}
            </td>
            <td class="px-4 py-3 text-right font-mono text-xs font-semibold" style="color: var(--text-primary);">
              {{ fmt(h.last_price) }}
            </td>
            <td class="px-4 py-3 text-right font-mono text-xs" style="color: var(--text-secondary);">
              {{ fmt(h.invested_value) }}
            </td>
            <td class="px-4 py-3 text-right font-mono text-xs" style="color: var(--text-secondary);">
              {{ fmt(h.current_value) }}
            </td>
            <td class="px-4 py-3 text-right font-mono text-xs font-semibold" :class="pnlClass(h.unrealised_pnl)">
              {{ fmt(h.unrealised_pnl) }}
            </td>
            <td class="px-4 py-3 text-right font-mono text-xs" :class="pnlClass(h.return_pct)">
              {{ formatPercent(h.return_pct) }}
            </td>
          </tr>
          <tr v-if="filteredHoldings.length === 0">
            <td colspan="9" class="px-4 py-10 text-center text-sm" style="color: var(--text-muted);">
              No holdings found
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ── Positions table ──────────────────────────────────────────────── -->
    <div v-else-if="activeTab === 'positions'" class="card overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b" style="border-color: var(--surface-border); background-color: var(--surface-secondary);">
            <th class="px-4 py-2.5 text-left text-xs uppercase tracking-wide" style="color: var(--text-muted);">Symbol</th>
            <th class="px-4 py-2.5 text-left text-xs uppercase tracking-wide" style="color: var(--text-muted);">Product</th>
            <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">Qty</th>
            <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">Buy Price</th>
            <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">LTP</th>
            <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">Realised P&amp;L</th>
            <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">Unrealised P&amp;L</th>
            <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">Total P&amp;L</th>
          </tr>
        </thead>
        <tbody class="divide-y" style="border-color: var(--surface-border);">
          <tr
            v-for="p in filteredPositions"
            :key="p.instrument_key"
            class="hover:bg-white/5 transition-colors"
          >
            <td class="px-4 py-3">
              <div class="font-mono font-semibold text-xs" style="color: var(--text-primary);">
                {{ p.trading_symbol }}
              </div>
              <div class="text-[10px] mt-0.5" style="color: var(--text-muted);">{{ p.exchange }}</div>
            </td>
            <td class="px-4 py-3 text-xs" style="color: var(--text-secondary);">{{ p.product }}</td>
            <td class="px-4 py-3 text-right font-mono text-xs" style="color: var(--text-secondary);">{{ p.quantity }}</td>
            <td class="px-4 py-3 text-right font-mono text-xs" style="color: var(--text-secondary);">{{ fmt(p.buy_price) }}</td>
            <td class="px-4 py-3 text-right font-mono text-xs font-semibold" style="color: var(--text-primary);">{{ fmt(p.last_price) }}</td>
            <td class="px-4 py-3 text-right font-mono text-xs" :class="pnlClass(p.realised_pnl)">{{ fmt(p.realised_pnl) }}</td>
            <td class="px-4 py-3 text-right font-mono text-xs" :class="pnlClass(p.unrealised_pnl)">{{ fmt(p.unrealised_pnl) }}</td>
            <td class="px-4 py-3 text-right font-mono text-xs font-semibold" :class="pnlClass(p.total_pnl)">{{ fmt(p.total_pnl) }}</td>
          </tr>
          <tr v-if="filteredPositions.length === 0">
            <td colspan="8" class="px-4 py-10 text-center text-sm" style="color: var(--text-muted);">
              No open positions
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ── Trades table ─────────────────────────────────────────────────── -->
    <div v-else-if="activeTab === 'trades'" class="card overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b" style="border-color: var(--surface-border); background-color: var(--surface-secondary);">
            <th class="px-4 py-2.5 text-left text-xs uppercase tracking-wide" style="color: var(--text-muted);">Symbol</th>
            <th class="px-4 py-2.5 text-left text-xs uppercase tracking-wide" style="color: var(--text-muted);">Type</th>
            <th class="px-4 py-2.5 text-left text-xs uppercase tracking-wide" style="color: var(--text-muted);">Product</th>
            <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">Qty</th>
            <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">Price</th>
            <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">Trade Value</th>
            <th class="px-4 py-2.5 text-left text-xs uppercase tracking-wide" style="color: var(--text-muted);">Date</th>
          </tr>
        </thead>
        <tbody class="divide-y" style="border-color: var(--surface-border);">
          <tr
            v-for="(t, i) in filteredTrades"
            :key="i"
            class="hover:bg-white/5 transition-colors"
          >
            <td class="px-4 py-3">
              <div class="font-mono font-semibold text-xs" style="color: var(--text-primary);">{{ t.trading_symbol }}</div>
              <div class="text-[10px] mt-0.5" style="color: var(--text-muted);">{{ t.exchange }}</div>
            </td>
            <td class="px-4 py-3">
              <span
                :class="[
                  'text-xs font-semibold px-2 py-0.5 rounded',
                  t.transaction_type === 'BUY'
                    ? 'text-emerald-400 bg-emerald-500/10'
                    : 'text-red-400 bg-red-500/10',
                ]"
              >{{ t.transaction_type }}</span>
            </td>
            <td class="px-4 py-3 text-xs" style="color: var(--text-secondary);">{{ t.product }}</td>
            <td class="px-4 py-3 text-right font-mono text-xs" style="color: var(--text-secondary);">{{ t.quantity }}</td>
            <td class="px-4 py-3 text-right font-mono text-xs" style="color: var(--text-secondary);">{{ fmt(t.price) }}</td>
            <td class="px-4 py-3 text-right font-mono text-xs font-semibold" style="color: var(--text-primary);">{{ fmt(t.trade_value) }}</td>
            <td class="px-4 py-3 text-xs" style="color: var(--text-muted);">
              {{ t.trade_date ? new Date(t.trade_date).toLocaleString() : '—' }}
            </td>
          </tr>
          <tr v-if="filteredTrades.length === 0">
            <td colspan="7" class="px-4 py-10 text-center text-sm" style="color: var(--text-muted);">
              No trades found
            </td>
          </tr>
        </tbody>
      </table>
    </div>

  </div>
</template>
