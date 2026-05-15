<script setup lang="ts">
import { computed } from 'vue'
import type { BacktestResult, RecommendationAction } from '@/types/ai'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

// ── Props ────────────────────────────────────────────────────────────────────
const props = defineProps<{
  backtest:  BacktestResult | null
  loading:   boolean
  error:     string | null
  symbol:    string
}>()

const emit = defineEmits<{
  (e: 'retry'): void
}>()

// ── Helpers ──────────────────────────────────────────────────────────────────
function actionColour(action: RecommendationAction): string {
  return action === 'BUY'  ? 'text-emerald-400'
       : action === 'SELL' ? 'text-red-400'
       :                     'text-amber-400'
}

function actionBg(action: RecommendationAction): string {
  return action === 'BUY'  ? 'bg-emerald-500/15 border-emerald-500/30'
       : action === 'SELL' ? 'bg-red-500/15 border-red-500/30'
       :                     'bg-amber-500/15 border-amber-500/30'
}

function scoreBarColor(action: RecommendationAction): string {
  return action === 'BUY'  ? 'bg-emerald-500'
       : action === 'SELL' ? 'bg-red-500'
       :                     'bg-amber-400'
}

// Zone strip — total sweep is -25 to +30 (55 points wide)
const SWEEP_MIN = -25
const SWEEP_MAX = 30
const SWEEP_WIDTH = SWEEP_MAX - SWEEP_MIN  // 55

function zoneLeft(minReturn: number | null): string {
  const v = minReturn ?? SWEEP_MIN
  return ((v - SWEEP_MIN) / SWEEP_WIDTH * 100).toFixed(1) + '%'
}

function zoneWidth(minReturn: number | null, maxReturn: number | null): string {
  const lo = minReturn ?? SWEEP_MIN
  const hi = maxReturn ?? SWEEP_MAX
  return ((hi - lo) / SWEEP_WIDTH * 100).toFixed(1) + '%'
}

// Current-position marker on zone strip
const currentMarkerLeft = computed(() => {
  if (!props.backtest) return '50%'
  const pct = (props.backtest.currentReturnPct - SWEEP_MIN) / SWEEP_WIDTH * 100
  return Math.max(0, Math.min(100, pct)).toFixed(1) + '%'
})

// Scenarios sorted ascending (for table)
const sortedScenarios = computed(() =>
  props.backtest
    ? [...props.backtest.scenarioAnalysis].sort((a, b) => a.returnPct - b.returnPct)
    : [],
)
</script>

<template>
  <div class="card p-5">
    <!-- Header -->
    <div class="flex items-center justify-between mb-5">
      <div>
        <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Signal Analysis</h3>
        <p class="text-xs mt-0.5" style="color: var(--text-muted);">
          Scenario sweep −25% → +30% return · current portfolio weight held fixed
        </p>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-10">
      <LoadingSpinner size="lg" />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="py-6 text-center">
      <p class="text-sm" style="color: var(--text-muted);">{{ error }}</p>
      <button class="mt-3 text-xs text-brand-400 hover:underline" @click="emit('retry')">Retry</button>
    </div>

    <!-- Content -->
    <template v-else-if="backtest">

      <!-- ── Summary metrics row ── -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <!-- Hit Rate -->
        <div class="flex flex-col items-center justify-center p-4 rounded-xl border"
             style="border-color: var(--surface-border); background: var(--surface-secondary);">
          <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Hit Rate</p>
          <template v-if="backtest.hitRatePct !== null">
            <p
              class="text-2xl font-bold"
              :class="backtest.hitRatePct >= 65 ? 'text-emerald-400' : backtest.hitRatePct >= 40 ? 'text-amber-400' : 'text-red-400'"
            >
              {{ backtest.hitRatePct.toFixed(0) }}%
            </p>
            <p class="text-xs mt-1" style="color: var(--text-muted);">directional accuracy</p>
          </template>
          <p v-else class="text-sm" style="color: var(--text-muted);">—</p>
        </div>

        <!-- Current score -->
        <div class="flex flex-col items-center justify-center p-4 rounded-xl border"
             style="border-color: var(--surface-border); background: var(--surface-secondary);">
          <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Current Score</p>
          <p class="text-2xl font-bold" style="color: var(--text-primary);">
            {{ backtest.currentScore.toFixed(1) }}
          </p>
          <p :class="['text-xs mt-1 font-semibold', actionColour(backtest.currentAction)]">
            {{ backtest.currentAction }}
          </p>
        </div>

        <!-- BUY zone count -->
        <div class="flex flex-col items-center justify-center p-4 rounded-xl border"
             style="border-color: var(--surface-border); background: var(--surface-secondary);">
          <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">BUY Scenarios</p>
          <p class="text-2xl font-bold text-emerald-400">{{ backtest.buySignalCount }}</p>
          <p class="text-xs mt-1" style="color: var(--text-muted);">of {{ backtest.scenarioAnalysis.length }} total</p>
        </div>

        <!-- Flip margin -->
        <div class="flex flex-col items-center justify-center p-4 rounded-xl border"
             style="border-color: var(--surface-border); background: var(--surface-secondary);">
          <p class="text-xs uppercase tracking-wide mb-1" style="color: var(--text-muted);">Nearest Flip</p>
          <template v-if="backtest.flipDownward">
            <p class="text-2xl font-bold text-amber-400">
              −{{ backtest.flipDownward.marginPct }}%
            </p>
            <p class="text-xs mt-1" style="color: var(--text-muted);">to {{ backtest.flipDownward.targetAction }}</p>
          </template>
          <p v-else class="text-sm" style="color: var(--text-muted);">stable</p>
        </div>
      </div>

      <!-- ── Signal zone strip ── -->
      <div class="mb-6">
        <p class="text-xs uppercase tracking-wide mb-2 font-semibold" style="color: var(--text-muted);">
          Signal Zones Across Return Range
        </p>
        <!-- Zone bar -->
        <div class="relative h-7 rounded-lg overflow-hidden" style="background: var(--surface-border);">
          <div
            v-for="zone in backtest.signalZones"
            :key="zone.action + zone.minReturn"
            :style="{ left: zoneLeft(zone.minReturn), width: zoneWidth(zone.minReturn, zone.maxReturn) }"
            :class="[
              'absolute inset-y-0 opacity-80 flex items-center justify-center text-xs font-semibold',
              zone.action === 'BUY'  ? 'bg-emerald-500/40 text-emerald-300' :
              zone.action === 'SELL' ? 'bg-red-500/40 text-red-300' :
                                       'bg-amber-500/30 text-amber-300',
            ]"
          >
            <span v-if="zone.width >= 10">{{ zone.action }}</span>
          </div>
          <!-- Current position marker -->
          <div
            :style="{ left: currentMarkerLeft }"
            class="absolute inset-y-0 w-0.5 bg-white/80 shadow-lg"
          />
        </div>
        <!-- Axis labels -->
        <div class="flex justify-between text-xs mt-1" style="color: var(--text-muted);">
          <span>−25%</span>
          <span>0%</span>
          <span>+30%</span>
        </div>
      </div>

      <!-- ── Flip points ── -->
      <div
        v-if="backtest.flipDownward || backtest.flipUpward"
        class="grid sm:grid-cols-2 gap-3 mb-6"
      >
        <div
          v-if="backtest.flipDownward"
          class="p-3 rounded-xl border flex gap-3 items-start"
          style="border-color: rgba(245,158,11,0.25); background: rgba(245,158,11,0.05);"
        >
          <span class="text-amber-400 mt-0.5 shrink-0">▼</span>
          <div>
            <p class="text-xs font-semibold text-amber-400">Downward flip</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary);">
              Signal changes to
              <strong :class="actionColour(backtest.flipDownward.targetAction)">
                {{ backtest.flipDownward.targetAction }}
              </strong>
              if return drops to {{ backtest.flipDownward.atReturnPct }}%
              <span style="color: var(--text-muted);">
                (−{{ backtest.flipDownward.marginPct }}% margin)
              </span>
            </p>
          </div>
        </div>
        <div
          v-if="backtest.flipUpward"
          class="p-3 rounded-xl border flex gap-3 items-start"
          style="border-color: rgba(16,185,129,0.2); background: rgba(16,185,129,0.05);"
        >
          <span class="text-emerald-400 mt-0.5 shrink-0">▲</span>
          <div>
            <p class="text-xs font-semibold text-emerald-400">Upward flip</p>
            <p class="text-sm mt-0.5" style="color: var(--text-primary);">
              Signal changes to
              <strong :class="actionColour(backtest.flipUpward.targetAction)">
                {{ backtest.flipUpward.targetAction }}
              </strong>
              if return rises to {{ backtest.flipUpward.atReturnPct }}%
              <span style="color: var(--text-muted);">
                (+{{ backtest.flipUpward.marginPct }}% margin)
              </span>
            </p>
          </div>
        </div>
      </div>

      <!-- ── Scenario table ── -->
      <div class="mb-6">
        <p class="text-xs uppercase tracking-wide mb-2 font-semibold" style="color: var(--text-muted);">
          Scenario Detail
        </p>
        <div class="overflow-x-auto rounded-xl border" style="border-color: var(--surface-border);">
          <table class="w-full text-xs">
            <thead>
              <tr style="background: var(--surface-secondary); color: var(--text-muted);">
                <th class="px-3 py-2 text-left font-medium">Return</th>
                <th class="px-3 py-2 text-left font-medium">Label</th>
                <th class="px-3 py-2 text-right font-medium">Score</th>
                <th class="px-3 py-2 text-left font-medium">Signal</th>
                <th class="px-3 py-2 hidden sm:table-cell text-right font-medium">Score bar</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(s, i) in sortedScenarios"
                :key="i"
                :class="[
                  'border-t transition-colors',
                  s.isCurrent
                    ? 'ring-1 ring-inset ring-brand-500/40'
                    : 'hover:bg-white/2',
                ]"
                style="border-color: var(--surface-border);"
              >
                <td
                  class="px-3 py-2 font-mono font-semibold"
                  :class="s.returnPct >= 0 ? 'text-emerald-400' : 'text-red-400'"
                >
                  {{ s.returnPct >= 0 ? '+' : '' }}{{ s.returnPct.toFixed(1) }}%
                  <span v-if="s.isCurrent" class="ml-1 text-brand-400">◀</span>
                </td>
                <td class="px-3 py-2" style="color: var(--text-muted);">{{ s.label }}</td>
                <td class="px-3 py-2 text-right font-mono" style="color: var(--text-primary);">
                  {{ s.score.toFixed(1) }}
                </td>
                <td class="px-3 py-2">
                  <span
                    :class="[
                      'px-1.5 py-0.5 rounded text-xs font-bold border',
                      actionBg(s.action),
                      actionColour(s.action),
                    ]"
                  >
                    {{ s.action }}
                  </span>
                </td>
                <td class="px-3 py-2 hidden sm:table-cell">
                  <div class="flex items-center gap-2">
                    <div class="flex-1 h-1.5 rounded-full overflow-hidden" style="background: var(--surface-border);">
                      <div
                        :style="{ width: s.score + '%' }"
                        :class="['h-full rounded-full', scoreBarColor(s.action)]"
                      />
                    </div>
                    <span class="text-xs w-8 text-right" style="color: var(--text-muted);">
                      {{ s.score.toFixed(0) }}
                    </span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ── Model notes ── -->
      <div v-if="backtest.modelNotes.length" class="mb-4">
        <p class="text-xs uppercase tracking-wide mb-2 font-semibold" style="color: var(--text-muted);">Model Notes</p>
        <ul class="space-y-1.5">
          <li
            v-for="(note, i) in backtest.modelNotes"
            :key="i"
            class="flex gap-2 text-sm"
            style="color: var(--text-primary);"
          >
            <span class="text-brand-400 shrink-0 mt-0.5">›</span>
            <span>{{ note }}</span>
          </li>
        </ul>
      </div>

      <!-- ── Methodology disclosure ── -->
      <details class="group text-xs">
        <summary
          class="cursor-pointer select-none list-none flex items-center gap-1.5 uppercase tracking-wide font-semibold"
          style="color: var(--text-muted);"
        >
          <span class="transition-transform group-open:rotate-90">›</span>
          Methodology
        </summary>
        <p class="mt-2 pl-4 leading-relaxed" style="color: var(--text-muted);">
          {{ backtest.methodology }}
        </p>
      </details>

    </template>

    <!-- No data -->
    <div v-else class="py-8 text-center text-sm" style="color: var(--text-muted);">
      No analysis available for {{ symbol }}
    </div>
  </div>
</template>
