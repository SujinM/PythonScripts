<script setup lang="ts">
import { ref, reactive } from 'vue'
import CalcInput  from '@/components/common/CalcInput.vue'
import ResultCard from '@/components/common/ResultCard.vue'
import ErrorAlert from '@/components/common/ErrorAlert.vue'
import { useHistoryStore } from '@/stores/historyStore'
import * as C from '@/utils/calculations'

const history = useHistoryStore()
const error   = ref('')

// Position size
const psF = reactive({ account: '', risk: '', buy: '', sl: '' })
const psResult = ref<Record<string, number | string> | null>(null)
function calcPS() {
  try {
    error.value = ''
    psResult.value = C.positionSizeByRisk(+psF.account, +psF.risk, +psF.buy, +psF.sl)
    history.add({ category: 'Risk', label: 'Position Size', inputs: { ...psF }, results: psResult.value })
  } catch (e: any) { error.value = e.message }
}

// Risk / Reward
const rrF = reactive({ buy: '', sl: '', target: '' })
const rrResult = ref<Record<string, number | string> | null>(null)
function calcRR() {
  try {
    error.value = ''
    const r = C.riskRewardRatio(+rrF.buy, +rrF.sl, +rrF.target)
    rrResult.value = { [r.label]: r.value }
    history.add({ category: 'Risk', label: 'R/R Ratio', inputs: { ...rrF }, results: rrResult.value })
  } catch (e: any) { error.value = e.message }
}

// Sharpe
const shF = reactive({ avg: '', rf: '', std: '' })
const shResult = ref<Record<string, number | string> | null>(null)
function calcSharpe() {
  try {
    error.value = ''
    const r = C.sharpeRatio(+shF.avg, +shF.rf, +shF.std)
    shResult.value = { [r.label]: r.value }
  } catch (e: any) { error.value = e.message }
}

// Volatility
const volF = reactive({ prices: '' })
const volResult = ref<Record<string, number | string> | null>(null)
function calcVol() {
  try {
    error.value = ''
    const prices = volF.prices.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n))
    const r = C.historicalVolatility(prices)
    volResult.value = { [r.label]: r.value }
  } catch (e: any) { error.value = e.message }
}

// Max Drawdown
const ddF = reactive({ prices: '' })
const ddResult = ref<Record<string, number | string> | null>(null)
function calcDD() {
  try {
    error.value = ''
    const prices = ddF.prices.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n))
    const r = C.maxDrawdown(prices)
    ddResult.value = { [r.label]: r.value }
  } catch (e: any) { error.value = e.message }
}
</script>

<template>
  <div class="space-y-8 max-w-5xl">
    <div>
      <h2 class="text-xl font-bold text-[var(--text-primary)]">Risk Management</h2>
      <p class="text-sm text-[var(--text-secondary)] mt-0.5">Position sizing, risk/reward, Sharpe ratio, volatility, max drawdown</p>
    </div>

    <ErrorAlert v-if="error" :message="error" />

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Position Size -->
      <div class="card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">Position Size by Risk %</h3>
        <div class="grid grid-cols-2 gap-3">
          <CalcInput label="Account Size"    v-model="psF.account" placeholder="100000" />
          <CalcInput label="Risk %"          v-model="psF.risk"    placeholder="1" hint="e.g. 1 = risk 1% of account" />
          <CalcInput label="Buy Price"       v-model="psF.buy"     placeholder="500" />
          <CalcInput label="Stop Loss Price" v-model="psF.sl"      placeholder="480" />
        </div>
        <button class="btn-primary w-full" @click="calcPS">Calculate</button>
        <ResultCard v-if="psResult" title="Result" :results="psResult" highlightKey="Shares to Buy" />
      </div>

      <!-- Risk / Reward -->
      <div class="card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">Risk / Reward Ratio</h3>
        <div class="grid grid-cols-3 gap-3">
          <CalcInput label="Buy Price"    v-model="rrF.buy"    placeholder="100" />
          <CalcInput label="Stop Loss"    v-model="rrF.sl"     placeholder="90" />
          <CalcInput label="Target Price" v-model="rrF.target" placeholder="130" />
        </div>
        <button class="btn-primary w-full" @click="calcRR">Calculate</button>
        <ResultCard v-if="rrResult" title="Result" :results="rrResult" />
      </div>

      <!-- Sharpe Ratio -->
      <div class="card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">Sharpe Ratio</h3>
        <div class="grid grid-cols-3 gap-3">
          <CalcInput label="Avg Return %" v-model="shF.avg" placeholder="12" />
          <CalcInput label="Risk-Free %" v-model="shF.rf"  placeholder="6" />
          <CalcInput label="Std Dev %"   v-model="shF.std" placeholder="15" />
        </div>
        <button class="btn-primary w-full" @click="calcSharpe">Calculate</button>
        <ResultCard v-if="shResult" title="Result" :results="shResult" />
      </div>

      <!-- Volatility -->
      <div class="card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">Historical Volatility</h3>
        <CalcInput label="Prices (comma-separated)" v-model="volF.prices" type="text" placeholder="100, 102, 99, 105, 103, 108" />
        <button class="btn-primary w-full" @click="calcVol">Calculate</button>
        <ResultCard v-if="volResult" title="Daily Std Dev" :results="volResult" />
      </div>

      <!-- Max Drawdown -->
      <div class="card p-5 space-y-4 lg:col-span-2">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">Maximum Drawdown</h3>
        <CalcInput label="Prices (comma-separated)" v-model="ddF.prices" type="text" placeholder="100, 120, 110, 80, 90, 95" />
        <button class="btn-primary" @click="calcDD">Calculate</button>
        <ResultCard v-if="ddResult" title="Max Peak-to-Trough Decline" :results="ddResult" />
      </div>
    </div>
  </div>
</template>
