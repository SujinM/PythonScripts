<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useInstrumentsStore } from '@/stores/instrumentsStore'
import { useMarketStore } from '@/stores/marketStore'
import { useSettingsStore } from '@/stores/settingsStore'
import { usePortfolioStore } from '@/stores/portfolioStore'
import { useRecommendationStore } from '@/stores/recommendationStore'
import { CHART_TIMEFRAMES, ASSET_TYPES } from '@/utils/constants'
import { formatPrice, formatChange, formatVolume, timeAgo } from '@/utils/formatters'
import type { RiskProfile } from '@/types/ai'
import Badge from '@/components/common/Badge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import CandlestickChart from '@/components/charts/CandlestickChart.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import BacktestPanel from '@/components/ai/BacktestPanel.vue'

const route     = useRoute()
const router    = useRouter()
const instStore = useInstrumentsStore()
const market    = useMarketStore()
const settings  = useSettingsStore()
const portfolio = usePortfolioStore()
const recStore  = useRecommendationStore()

const symbol    = computed(() => String(route.params.symbol))
const timeframe = ref<(typeof CHART_TIMEFRAMES)[number]>(CHART_TIMEFRAMES[2]) // 1M default

const instrument  = computed(() => instStore.selectedInstrument)
const marketData  = computed(() => market.marketData[symbol.value])
const candles     = computed(() => market.priceHistory[symbol.value] ?? [])
const inWatchlist = computed(() => settings.isInWatchlist(symbol.value))

// ── AI Recommendation ────────────────────────────────────────────────────────
const riskProfile    = ref<RiskProfile>('moderate')
const broker         = computed(() => portfolio.activeBroker)
const recommendation = computed(() => recStore.getRecommendation(broker.value, symbol.value))
const recLoading     = computed(() => recStore.isLoading(broker.value, symbol.value))
const recError       = computed(() => recStore.getError(broker.value, symbol.value))

// ── Backtest (Phase 3) ───────────────────────────────────────────────────────
const backtest      = computed(() => recStore.getBacktest(broker.value, symbol.value))
const btLoading     = computed(() => recStore.isBacktestLoading(broker.value, symbol.value))
const btError       = computed(() => recStore.getBacktestError(broker.value, symbol.value))

async function fetchBacktest(forceRefresh = false) {
  await recStore.fetchBacktest(broker.value, symbol.value, riskProfile.value, forceRefresh)
}

const actionClass = computed(() => {
  if (!recommendation.value) return ''
  const map: Record<string, string> = {
    BUY:  'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30',
    SELL: 'bg-red-500/15 text-red-400 border border-red-500/30',
    HOLD: 'bg-amber-500/15 text-amber-400 border border-amber-500/30',
  }
  return map[recommendation.value.action] ?? ''
})

const scoreBarClass = computed(() => {
  const s = recommendation.value?.score ?? 50
  if (s >= 65) return 'bg-emerald-500'
  if (s <= 35) return 'bg-red-500'
  return 'bg-amber-400'
})

function featureBarClass(score: number): string {
  if (score >= 65) return 'bg-emerald-500'
  if (score <= 35) return 'bg-red-500'
  return 'bg-amber-400'
}

async function fetchRecommendation(forceRefresh = false) {
  await recStore.fetchRecommendation(broker.value, symbol.value, riskProfile.value, undefined, forceRefresh)
}

watch(riskProfile, () => {
  fetchRecommendation(true)
  fetchBacktest(true)
})

onMounted(async () => {
  await Promise.all([
    instStore.fetchInstrument(symbol.value),
    market.fetchMarketData(symbol.value),
    market.fetchPriceHistory(symbol.value, 90),
    fetchRecommendation(),
    fetchBacktest(),
  ])
})

async function changeTimeframe(tf: typeof timeframe.value) {
  timeframe.value = tf
  await market.fetchPriceHistory(symbol.value, tf.days)
}

function toggleWatchlist() {
  if (inWatchlist.value) {
    settings.removeFromWatchlist(symbol.value)
  } else {
    settings.addToWatchlist(symbol.value)
  }
}

const assetTypeInfo = computed(() =>
  instrument.value
    ? ASSET_TYPES.find((a) => a.value === instrument.value!.assetType)
    : null,
)

const loading = computed(() => instStore.loading || market.loading)
</script>

<template>
  <div class="space-y-5 animate-fade-in">
    <!-- Breadcrumb -->
    <div class="flex items-center gap-2 text-sm" style="color: var(--text-muted);">
      <router-link to="/instruments" class="hover:text-brand-400 transition-colors">Instruments</router-link>
      <span>/</span>
      <span style="color: var(--text-primary);">{{ symbol }}</span>
    </div>

    <!-- Header card -->
    <div class="card p-5">
      <div v-if="loading && !instrument" class="space-y-3">
        <LoadingSkeleton height="h-7" width="w-32" />
        <LoadingSkeleton height="h-4" :lines="2" />
      </div>

      <template v-else-if="instrument">
        <div class="flex flex-col sm:flex-row sm:items-start gap-4">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-1">
              <div class="w-10 h-10 rounded-xl bg-brand-500/10 flex items-center justify-center text-brand-400 font-bold">
                {{ symbol.slice(0, 2) }}
              </div>
              <div>
                <h1 class="text-2xl font-bold" style="color: var(--text-primary);">{{ symbol }}</h1>
                <p class="text-sm" style="color: var(--text-muted);">{{ instrument.displayName }}</p>
              </div>
            </div>
            <div class="flex flex-wrap gap-2 mt-3">
              <Badge :value="instrument.assetType" type="assetType" />
              <span class="badge bg-gray-500/10 text-gray-400">{{ instrument.exchange }}</span>
              <span class="badge" :class="instrument.isTradable ? 'bg-emerald-500/10 text-emerald-400' : 'bg-gray-500/10 text-gray-500'">
                {{ instrument.isTradable ? '● Tradable' : '○ Non-tradable' }}
              </span>
            </div>
          </div>

          <!-- Price panel -->
          <div class="flex flex-col items-start sm:items-end gap-1">
            <p v-if="marketData" class="text-3xl font-bold stat-value" style="color: var(--text-primary);">
              {{ formatPrice(marketData.price, instrument.currency) }}
            </p>
            <div v-if="marketData && marketData.changePercent !== 0" :class="['flex items-center gap-2 text-sm font-semibold', marketData.changePercent >= 0 ? 'text-profit' : 'text-loss']">
              <span>{{ marketData.changePercent >= 0 ? '▲' : '▼' }}</span>
              <span>{{ formatChange(marketData.changePercent) }}</span>
              <span class="text-xs font-normal" style="color: var(--text-muted);">({{ formatPrice(Math.abs(marketData.change)) }})</span>
            </div>
            <div v-else-if="marketData" class="flex items-center gap-1 text-sm" style="color: var(--text-muted);">
              <span>▲</span><span>0.00%</span>
              <span class="text-xs">($0.00)</span>
            </div>

            <!-- Watchlist toggle -->
            <button
              :class="['mt-2 flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-colors', inWatchlist ? 'border-amber-500/40 text-amber-400 bg-amber-500/10' : 'border-[var(--surface-border)] text-gray-400 hover:border-brand-500/40 hover:text-brand-400']"
              @click="toggleWatchlist"
            >
              <svg class="w-3.5 h-3.5" :fill="inWatchlist ? 'currentColor' : 'none'" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
              </svg>
              {{ inWatchlist ? 'In Watchlist' : 'Add to Watchlist' }}
            </button>
          </div>
        </div>

        <!-- Stats row -->
        <div v-if="marketData" class="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-5 pt-5 border-t" style="border-color: var(--surface-border);">
          <div>
            <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">24h High</p>
            <p class="text-sm font-semibold stat-value" style="color: var(--text-primary);">
              {{ marketData.high24h !== marketData.price ? formatPrice(marketData.high24h) : '—' }}
            </p>
          </div>
          <div>
            <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">24h Low</p>
            <p class="text-sm font-semibold stat-value" style="color: var(--text-primary);">
              {{ marketData.low24h !== marketData.price ? formatPrice(marketData.low24h) : '—' }}
            </p>
          </div>
          <div>
            <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Volume</p>
            <p class="text-sm font-semibold stat-value" style="color: var(--text-primary);">{{ formatVolume(marketData.volume) }}</p>
          </div>
          <div>
            <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Currency</p>
            <p class="text-sm font-semibold" style="color: var(--text-primary);">{{ instrument.currency }}</p>
          </div>
        </div>
      </template>

      <div v-else class="text-center py-8" style="color: var(--text-muted);">
        Instrument not found
      </div>
    </div>

    <!-- Chart card -->
    <div class="card p-4">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Price History</h3>
        <!-- Timeframe selector -->
        <div class="flex gap-1">
          <button
            v-for="tf in CHART_TIMEFRAMES"
            :key="tf.value"
            :class="[
              'px-2 py-1 rounded text-xs font-medium transition-colors',
              timeframe.value === tf.value
                ? 'bg-brand-500 text-white'
                : 'text-gray-500 hover:text-white hover:bg-white/5',
            ]"
            @click="changeTimeframe(tf)"
          >
            {{ tf.value }}
          </button>
        </div>
      </div>

      <div v-if="market.loading && candles.length === 0" class="flex items-center justify-center h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
      <CandlestickChart
        v-else-if="candles.length > 0"
        :candles="candles"
        :symbol="symbol"
        height="420px"
        :show-volume="true"
      />
    </div>

    <!-- Instrument metadata -->
    <div v-if="instrument" class="card p-5">
      <h3 class="text-sm font-semibold mb-4" style="color: var(--text-primary);">Instrument Details</h3>
      <div class="grid grid-cols-2 sm:grid-cols-3 gap-y-4 gap-x-6 text-sm">
        <div v-for="[key, val] in [
          ['Instrument ID', instrument.instrumentId],
          ['Exchange', instrument.exchange],
          ['Asset Type', instrument.assetType],
          ['Currency', instrument.currency],
          ['Tradable', instrument.isTradable ? 'Yes' : 'No'],
          ['Leverage', instrument.leverage ?? '—'],
          ['Min Position', instrument.minPositionAmount ?? '—'],
          ['Max Position', instrument.maxPositionAmount ?? '—'],
          ['Spread', instrument.spreadFixed ? `${instrument.spreadFixed} pts` : '—'],
        ]" :key="key">
          <div>
            <p class="text-xs uppercase tracking-wide mb-0.5" style="color: var(--text-muted);">{{ key }}</p>
            <p class="font-medium" style="color: var(--text-primary);">{{ val }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- AI Signal card -->
    <div class="card p-5">
      <!-- Header + risk profile toggle -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div>
          <h3 class="text-sm font-semibold" style="color: var(--text-primary);">AI Signal</h3>
          <p class="text-xs mt-0.5" style="color: var(--text-muted);">
            Deterministic score for <strong>{{ broker }}</strong> portfolio context
          </p>
        </div>
        <!-- Risk profile selector -->
        <div class="flex gap-1 self-start sm:self-auto">
          <button
            v-for="rp in (['conservative', 'moderate', 'aggressive'] as const)"
            :key="rp"
            :class="[
              'px-2.5 py-1 rounded text-xs font-medium capitalize transition-colors',
              riskProfile === rp
                ? 'bg-brand-500 text-white'
                : 'text-gray-400 hover:text-white hover:bg-white/5',
            ]"
            @click="riskProfile = rp"
          >
            {{ rp }}
          </button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="recLoading" class="flex items-center justify-center py-10">
        <LoadingSpinner size="lg" />
      </div>

      <!-- Error -->
      <div v-else-if="recError" class="py-6 text-center">
        <p class="text-sm" style="color: var(--text-muted);">{{ recError }}</p>
        <button class="mt-3 text-xs text-brand-400 hover:underline" @click="fetchRecommendation(true)">Retry</button>
      </div>

      <!-- Result -->
      <template v-else-if="recommendation">

        <!-- Not-in-portfolio notice -->
        <div
          v-if="!recommendation.isPortfolioInstrument"
          class="flex items-start gap-2 p-3 rounded-xl text-xs mb-4"
          style="border: 1px solid rgba(245,158,11,0.3); background: rgba(245,158,11,0.05); color: var(--text-muted);"
        >
          <span class="mt-0.5 shrink-0">⚠</span>
          <span>
            <strong style="color: rgba(245,158,11,0.9);">Not in your portfolio.</strong>
            Score uses the instrument's live market trend as a proxy.
            Add it to your portfolio for full context-aware analysis.
          </span>
        </div>

        <!-- Action + composite score bar -->
        <div class="flex items-center gap-4 mb-5">
          <span :class="['text-xl font-bold px-4 py-2 rounded-xl', actionClass]">
            {{ recommendation.action }}
          </span>
          <div class="flex-1">
            <div class="flex justify-between text-xs mb-1.5">
              <span style="color: var(--text-muted);">Composite score</span>
              <span class="font-semibold" style="color: var(--text-primary);">{{ recommendation.score.toFixed(1) }} / 100</span>
            </div>
            <div class="h-2.5 rounded-full overflow-hidden" style="background: var(--surface-border);">
              <div
                :style="{ width: recommendation.score + '%' }"
                :class="['h-full rounded-full transition-all duration-500', scoreBarClass]"
              />
            </div>
          </div>
          <div class="text-center min-w-[56px]">
            <p class="text-xs mb-0.5" style="color: var(--text-muted);">Confidence</p>
            <p class="text-lg font-bold" style="color: var(--text-primary);">{{ recommendation.confidence }}%</p>
          </div>
        </div>

        <!-- Feature breakdown grid -->
        <div class="grid grid-cols-2 gap-x-6 gap-y-3 mb-5">
          <div
            v-for="(score, feat) in recommendation.features"
            :key="feat"
          >
            <div class="flex justify-between text-xs mb-1">
              <span class="capitalize" style="color: var(--text-muted);">
                {{ feat }}
                <span class="text-gray-600">(×{{ recommendation.featureWeights[feat] }})</span>
              </span>
              <span class="font-medium" style="color: var(--text-primary);">{{ score.toFixed(0) }}</span>
            </div>
            <div class="h-1.5 rounded-full overflow-hidden" style="background: var(--surface-border);">
              <div
                :style="{ width: score + '%' }"
                :class="['h-full rounded-full transition-all duration-500', featureBarClass(score)]"
              />
            </div>
          </div>
        </div>

        <!-- Phase 3: Natural language narrative -->
        <div class="mb-4 p-3 rounded-xl border text-sm leading-relaxed"
             style="border-color: var(--surface-border); background: var(--surface-secondary); color: var(--text-primary);">
          {{ recommendation.narrative }}
        </div>

        <!-- Why this signal? reason bullets -->
        <div class="mb-4">
          <p class="text-xs uppercase tracking-wide mb-2 font-semibold" style="color: var(--text-muted);">Why this signal?</p>
          <ul class="space-y-2">
            <li
              v-for="(bullet, i) in recommendation.reasonBullets"
              :key="i"
              class="flex gap-2 text-sm"
              style="color: var(--text-primary);"
            >
              <span class="text-brand-400 mt-0.5 shrink-0">›</span>
              <span>{{ bullet }}</span>
            </li>
          </ul>
        </div>

        <!-- Risk flags -->
        <div
          v-if="recommendation.riskFlags.length"
          class="mb-4 p-3 rounded-xl border"
          style="background: rgba(245,158,11,0.05); border-color: rgba(245,158,11,0.2);"
        >
          <p class="text-xs uppercase tracking-wide mb-2 font-semibold text-amber-400">Risk Flags</p>
          <ul class="space-y-1.5">
            <li
              v-for="(flag, i) in recommendation.riskFlags"
              :key="i"
              class="flex gap-2 text-sm text-amber-300/80"
            >
              <span class="shrink-0">⚠</span>
              <span>{{ flag }}</span>
            </li>
          </ul>
        </div>

        <!-- Invalidation conditions (collapsible) -->
        <details class="group text-sm">
          <summary
            class="cursor-pointer select-none text-xs uppercase tracking-wide font-semibold list-none flex items-center gap-1.5"
            style="color: var(--text-muted);"
          >
            <span class="transition-transform group-open:rotate-90">›</span>
            Invalidation Conditions
          </summary>
          <ul class="mt-2 space-y-2 pl-4">
            <li
              v-for="(cond, i) in recommendation.invalidationConditions"
              :key="i"
              class="flex gap-2"
              style="color: var(--text-primary);"
            >
              <span style="color: var(--text-muted);">→</span>
              <span>{{ cond }}</span>
            </li>
          </ul>
        </details>

        <!-- Footer: staleness + timestamp -->
        <div class="mt-4 pt-3 flex items-center justify-between text-xs border-t" style="border-color: var(--surface-border); color: var(--text-muted);">
          <span v-if="recommendation.isStale" class="text-amber-400 flex items-center gap-1">
            <span>⚠</span> Stale data — consider refreshing
          </span>
          <span v-else class="flex items-center gap-1">
            <span class="text-emerald-400">●</span> Fresh
          </span>
          <span>Signal generated {{ timeAgo(recommendation.dataTimestamp) }}</span>
        </div>

      </template>

      <!-- No data yet -->
      <div v-else class="py-8 text-center text-sm" style="color: var(--text-muted);">
        No recommendation available
      </div>
    </div>

    <!-- Phase 3: Signal Analysis / Backtest panel -->
    <BacktestPanel
      :backtest="backtest"
      :loading="btLoading"
      :error="btError"
      :symbol="symbol"
      @retry="fetchBacktest(true)"
    />
  </div>
</template>
