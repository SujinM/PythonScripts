<script setup lang="ts">
import { ref, reactive } from 'vue'
import CalcInput  from '@/components/common/CalcInput.vue'
import ResultCard from '@/components/common/ResultCard.vue'
import ErrorAlert from '@/components/common/ErrorAlert.vue'
import { useHistoryStore } from '@/stores/historyStore'
import * as C from '@/utils/calculations'

const history = useHistoryStore()
const error   = ref('')

// Trade P&L
const pl = reactive({ buy: '', sell: '', qty: '' })
const plResult = ref<Record<string, number | string> | null>(null)
function calcPL() {
  try {
    error.value = ''
    plResult.value = C.profitLoss(+pl.buy, +pl.sell, +pl.qty)
    history.add({ category: 'Returns', label: 'Trade P&L', inputs: { buy: pl.buy, sell: pl.sell, qty: pl.qty }, results: plResult.value })
  } catch (e: any) { error.value = e.message }
}

// CAGR
const cagrF = reactive({ initial: '', final: '', years: '' })
const cagrResult = ref<Record<string, number | string> | null>(null)
function calcCAGR() {
  try {
    error.value = ''
    const r = C.cagr(+cagrF.initial, +cagrF.final, +cagrF.years)
    cagrResult.value = { [r.label]: r.value }
  } catch (e: any) { error.value = e.message }
}

// ROI
const roiF = reactive({ cost: '', gain: '' })
const roiResult = ref<Record<string, number | string> | null>(null)
function calcROI() {
  try {
    error.value = ''
    const r = C.roi(+roiF.cost, +roiF.gain)
    roiResult.value = { [r.label]: r.value }
  } catch (e: any) { error.value = e.message }
}

// Breakeven
const beF = reactive({ buy: '', fee: '' })
const beResult = ref<Record<string, number | string> | null>(null)
function calcBE() {
  try { error.value = ''; beResult.value = { 'Breakeven Price': C.breakevenPrice(+beF.buy, +beF.fee).value } }
  catch (e: any) { error.value = e.message }
}

// Dividend Yield
const divF = reactive({ div: '', price: '' })
const divResult = ref<Record<string, number | string> | null>(null)
function calcDiv() {
  try { error.value = ''; divResult.value = { 'Dividend Yield %': C.dividendYield(+divF.div, +divF.price).value } }
  catch (e: any) { error.value = e.message }
}

// Compound Interest
const ciF = reactive({ principal: '', rate: '', years: '', n: '1' })
const ciResult = ref<Record<string, number | string> | null>(null)
function calcCI() {
  try { error.value = ''; ciResult.value = C.compoundInterest(+ciF.principal, +ciF.rate, +ciF.years, +ciF.n) }
  catch (e: any) { error.value = e.message }
}
</script>

<template>
  <div class="space-y-8 max-w-5xl">
    <div>
      <h2 class="text-xl font-bold text-[var(--text-primary)]">Returns & P&L</h2>
      <p class="text-sm text-[var(--text-secondary)] mt-0.5">Trade P&L, CAGR, ROI, breakeven, dividend yield, compound interest</p>
    </div>

    <ErrorAlert v-if="error" :message="error" />

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Trade P&L -->
      <div class="card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">Trade Profit / Loss</h3>
        <div class="grid grid-cols-3 gap-3">
          <CalcInput label="Buy Price"  v-model="pl.buy"  placeholder="100" />
          <CalcInput label="Sell Price" v-model="pl.sell" placeholder="130" />
          <CalcInput label="Quantity"   v-model="pl.qty"  placeholder="50" />
        </div>
        <button class="btn-primary w-full" @click="calcPL">Calculate</button>
        <ResultCard v-if="plResult" title="Result" :results="plResult" highlightKey="P&L" />
      </div>

      <!-- CAGR -->
      <div class="card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">CAGR — Compound Annual Growth Rate</h3>
        <div class="grid grid-cols-3 gap-3">
          <CalcInput label="Initial Value" v-model="cagrF.initial" placeholder="10000" />
          <CalcInput label="Final Value"   v-model="cagrF.final"   placeholder="20000" />
          <CalcInput label="Years"         v-model="cagrF.years"   placeholder="5" />
        </div>
        <button class="btn-primary w-full" @click="calcCAGR">Calculate</button>
        <ResultCard v-if="cagrResult" title="Result" :results="cagrResult" />
      </div>

      <!-- ROI -->
      <div class="card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">Return on Investment (ROI)</h3>
        <div class="grid grid-cols-2 gap-3">
          <CalcInput label="Cost / Invested" v-model="roiF.cost" placeholder="5000" />
          <CalcInput label="Final Value"      v-model="roiF.gain" placeholder="7500" />
        </div>
        <button class="btn-primary w-full" @click="calcROI">Calculate</button>
        <ResultCard v-if="roiResult" title="Result" :results="roiResult" />
      </div>

      <!-- Breakeven -->
      <div class="card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">Breakeven Price</h3>
        <div class="grid grid-cols-2 gap-3">
          <CalcInput label="Buy Price"     v-model="beF.buy" placeholder="100" />
          <CalcInput label="Brokerage Fee %" v-model="beF.fee" placeholder="0.3" hint="e.g. 0.3 = 0.3%" />
        </div>
        <button class="btn-primary w-full" @click="calcBE">Calculate</button>
        <ResultCard v-if="beResult" title="Result" :results="beResult" />
      </div>

      <!-- Dividend Yield -->
      <div class="card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">Dividend Yield</h3>
        <div class="grid grid-cols-2 gap-3">
          <CalcInput label="Annual Dividend / Share" v-model="divF.div"   placeholder="5" />
          <CalcInput label="Stock Price"             v-model="divF.price" placeholder="100" />
        </div>
        <button class="btn-primary w-full" @click="calcDiv">Calculate</button>
        <ResultCard v-if="divResult" title="Result" :results="divResult" />
      </div>

      <!-- Compound Interest -->
      <div class="card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">Compound Interest</h3>
        <div class="grid grid-cols-2 gap-3">
          <CalcInput label="Principal"  v-model="ciF.principal" placeholder="10000" />
          <CalcInput label="Rate %"     v-model="ciF.rate"      placeholder="10" />
          <CalcInput label="Years"      v-model="ciF.years"     placeholder="5" />
          <CalcInput label="n / year"   v-model="ciF.n"         placeholder="1" hint="1=annual 12=monthly 365=daily" />
        </div>
        <button class="btn-primary w-full" @click="calcCI">Calculate</button>
        <ResultCard v-if="ciResult" title="Result" :results="ciResult" highlightKey="Amount" />
      </div>
    </div>
  </div>
</template>
