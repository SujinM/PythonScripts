<script setup lang="ts">
import { ref, reactive } from 'vue'
import CalcInput  from '@/components/common/CalcInput.vue'
import ResultCard from '@/components/common/ResultCard.vue'
import ErrorAlert from '@/components/common/ErrorAlert.vue'
import { useHistoryStore } from '@/stores/historyStore'
import * as C from '@/utils/calculations'

const history = useHistoryStore()
const error   = ref('')

// ── 1. Price Difference ──────────────────────────────────────────────────────
const diff = reactive({ old: '', new: '' })
const diffResult = ref<Record<string, number | string> | null>(null)
function calcDiff() {
  try { error.value = ''; diffResult.value = { [C.priceDifference(+diff.old, +diff.new).label]: C.priceDifference(+diff.old, +diff.new).value } }
  catch (e: any) { error.value = e.message }
}

// ── 2. Percentage Change ─────────────────────────────────────────────────────
const pct = reactive({ old: '', new: '' })
const pctResult = ref<Record<string, number | string> | null>(null)
function calcPct() {
  try {
    error.value = ''
    const r = C.percentageChange(+pct.old, +pct.new)
    pctResult.value = { [r.label]: r.value }
    history.add({ category: 'Price', label: r.label, inputs: { old: pct.old, new: pct.new }, results: pctResult.value })
  } catch (e: any) { error.value = e.message }
}

// ── 3. Stop Loss & Take Profit ───────────────────────────────────────────────
const sltp = reactive({ buy: '', sl: '', tp: '' })
const sltpResult = ref<Record<string, number | string> | null>(null)
function calcSLTP() {
  try {
    error.value = ''
    const sl = C.stopLossPrice(+sltp.buy, +sltp.sl)
    const tp = C.takeProfitPrice(+sltp.buy, +sltp.tp)
    sltpResult.value = { 'Stop Loss': sl.value, 'Take Profit': tp.value, 'Risk Amount': +(+sltp.buy - sl.value).toFixed(4), 'Reward Amount': +(tp.value - +sltp.buy).toFixed(4) }
    history.add({ category: 'Price', label: 'SL / TP', inputs: { buy: sltp.buy, sl: sltp.sl, tp: sltp.tp }, results: sltpResult.value })
  } catch (e: any) { error.value = e.message }
}

// ── 4. Pivot Points ──────────────────────────────────────────────────────────
const pivot = reactive({ h: '', l: '', c: '' })
const pivotResult = ref<Record<string, number | string> | null>(null)
function calcPivot() {
  try { error.value = ''; pivotResult.value = C.pivotPoints(+pivot.h, +pivot.l, +pivot.c) }
  catch (e: any) { error.value = e.message }
}

// ── 5. Moving Average ────────────────────────────────────────────────────────
const ma = reactive({ prices: '', period: '' })
const maResult = ref<Record<string, number | string> | null>(null)
function calcMA() {
  try {
    error.value = ''
    const prices = ma.prices.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n))
    const period = ma.period ? parseInt(ma.period) : undefined
    maResult.value = { 'Moving Average': C.movingAverage(prices, period) }
  } catch (e: any) { error.value = e.message }
}
</script>

<template>
  <div class="space-y-8 max-w-5xl">
    <div>
      <h2 class="text-xl font-bold text-[var(--text-primary)]">Price Calculations</h2>
      <p class="text-sm text-[var(--text-secondary)] mt-0.5">Difference, % change, stop-loss, take-profit, pivot points, moving average</p>
    </div>

    <ErrorAlert v-if="error" :message="error" />

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Price Difference -->
      <div class="card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">Price Difference</h3>
        <div class="grid grid-cols-2 gap-3">
          <CalcInput label="Old Price" v-model="diff.old" placeholder="100" />
          <CalcInput label="New Price" v-model="diff.new" placeholder="115" />
        </div>
        <button class="btn-primary w-full" @click="calcDiff">Calculate</button>
        <ResultCard v-if="diffResult" title="Result" :results="diffResult" />
      </div>

      <!-- Percentage Change -->
      <div class="card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">Percentage Change</h3>
        <div class="grid grid-cols-2 gap-3">
          <CalcInput label="Old Price" v-model="pct.old" placeholder="100" />
          <CalcInput label="New Price" v-model="pct.new" placeholder="120" />
        </div>
        <button class="btn-primary w-full" @click="calcPct">Calculate</button>
        <ResultCard v-if="pctResult" title="Result" :results="pctResult" />
      </div>

      <!-- Stop Loss / Take Profit -->
      <div class="card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">Stop Loss & Take Profit</h3>
        <CalcInput label="Buy Price" v-model="sltp.buy" placeholder="100" />
        <div class="grid grid-cols-2 gap-3">
          <CalcInput label="Stop Loss %" v-model="sltp.sl" placeholder="5" hint="-5% from buy" />
          <CalcInput label="Take Profit %" v-model="sltp.tp" placeholder="10" hint="+10% from buy" />
        </div>
        <button class="btn-primary w-full" @click="calcSLTP">Calculate</button>
        <ResultCard v-if="sltpResult" title="Result" :results="sltpResult" />
      </div>

      <!-- Pivot Points -->
      <div class="card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">Pivot Points</h3>
        <div class="grid grid-cols-3 gap-3">
          <CalcInput label="High"  v-model="pivot.h" placeholder="110" />
          <CalcInput label="Low"   v-model="pivot.l" placeholder="90" />
          <CalcInput label="Close" v-model="pivot.c" placeholder="100" />
        </div>
        <button class="btn-primary w-full" @click="calcPivot">Calculate</button>
        <ResultCard v-if="pivotResult" title="PP / R1–R3 / S1–S3" :results="pivotResult" highlightKey="PP" />
      </div>

      <!-- Moving Average -->
      <div class="card p-5 space-y-4 lg:col-span-2">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">Simple Moving Average</h3>
        <CalcInput label="Prices (comma-separated)" v-model="ma.prices" type="text" placeholder="100, 102, 105, 103, 108" />
        <CalcInput label="Period (blank = all)" v-model="ma.period" placeholder="5" hint="Last N prices to average" />
        <button class="btn-primary" @click="calcMA">Calculate</button>
        <ResultCard v-if="maResult" title="Result" :results="maResult" />
      </div>
    </div>
  </div>
</template>
