<script setup lang="ts">
import { ref, reactive } from 'vue'
import CalcInput  from '@/components/common/CalcInput.vue'
import ResultCard from '@/components/common/ResultCard.vue'
import ErrorAlert from '@/components/common/ErrorAlert.vue'
import { useHistoryStore } from '@/stores/historyStore'
import * as C from '@/utils/calculations'

const history = useHistoryStore()
const error   = ref('')

// ── Average Buy Price ─────────────────────────────────────────────────────────
const avgEntries = reactive([
  { price: '', qty: '' },
  { price: '', qty: '' },
])
const avgResult = ref<Record<string, number | string> | null>(null)

function addEntry() { avgEntries.push({ price: '', qty: '' }) }
function removeEntry(i: number) { if (avgEntries.length > 2) avgEntries.splice(i, 1) }

function calcAvg() {
  try {
    error.value = ''
    const purchases = avgEntries
      .filter(e => e.price && e.qty)
      .map(e => ({ price: +e.price, qty: +e.qty }))
    avgResult.value = C.averageBuyPrice(purchases)
    history.add({ category: 'Position', label: 'Avg Buy Price', inputs: {}, results: avgResult.value })
  } catch (e: any) { error.value = e.message }
}

// ── Portfolio Allocation ──────────────────────────────────────────────────────
const allocEntries = reactive([
  { symbol: '', value: '' },
  { symbol: '', value: '' },
])
const allocResult = ref<Record<string, number | string> | null>(null)

function addAlloc() { allocEntries.push({ symbol: '', value: '' }) }

function calcAlloc() {
  try {
    error.value = ''
    const holdings = allocEntries
      .filter(e => e.symbol && e.value)
      .map(e => ({ symbol: e.symbol.toUpperCase(), value: +e.value }))
    const result = C.portfolioAllocation(holdings)
    allocResult.value = Object.fromEntries(result.map(r => [r.symbol, r.pct + '%']))
  } catch (e: any) { error.value = e.message }
}

// ── Lot Size ──────────────────────────────────────────────────────────────────
const lotF = reactive({ capital: '', price: '', alloc: '' })
const lotResult = ref<Record<string, number | string> | null>(null)
function calcLot() {
  try { error.value = ''; lotResult.value = C.lotSizeCalculator(+lotF.capital, +lotF.price, +lotF.alloc) }
  catch (e: any) { error.value = e.message }
}

// ── Unrealised P&L ────────────────────────────────────────────────────────────
const upnlF = reactive({ avg: '', current: '', qty: '' })
const upnlResult = ref<Record<string, number | string> | null>(null)
function calcUPnL() {
  try {
    error.value = ''
    upnlResult.value = C.unrealisedPnl(+upnlF.avg, +upnlF.current, +upnlF.qty)
    history.add({ category: 'Position', label: 'Unrealised P&L', inputs: { ...upnlF }, results: upnlResult.value })
  } catch (e: any) { error.value = e.message }
}
</script>

<template>
  <div class="space-y-8 max-w-5xl">
    <div>
      <h2 class="text-xl font-bold text-[var(--text-primary)]">Position & Portfolio</h2>
      <p class="text-sm text-[var(--text-secondary)] mt-0.5">Average buy price, allocation %, lot size, unrealised P&L</p>
    </div>

    <ErrorAlert v-if="error" :message="error" />

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Average Buy Price -->
      <div class="card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">Average Buy Price</h3>
        <div v-for="(e, i) in avgEntries" :key="i" class="grid grid-cols-[1fr_1fr_auto] gap-2 items-end">
          <CalcInput :label="`Entry ${i+1} Price`" v-model="e.price" placeholder="100" />
          <CalcInput :label="`Entry ${i+1} Qty`"   v-model="e.qty"   placeholder="10" />
          <button v-if="avgEntries.length > 2" @click="removeEntry(i)"
            class="mb-0 pb-2 text-red-400 hover:text-red-300 text-lg leading-none">×</button>
        </div>
        <button @click="addEntry" class="text-xs text-brand-400 hover:text-brand-300 transition-colors">+ Add entry</button>
        <button class="btn-primary w-full" @click="calcAvg">Calculate</button>
        <ResultCard v-if="avgResult" title="Result" :results="avgResult" highlightKey="Average Buy Price" />
      </div>

      <!-- Unrealised P&L -->
      <div class="card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">Unrealised P&L</h3>
        <div class="grid grid-cols-3 gap-3">
          <CalcInput label="Avg Buy Price"   v-model="upnlF.avg"     placeholder="100" />
          <CalcInput label="Current Price"   v-model="upnlF.current" placeholder="130" />
          <CalcInput label="Quantity"        v-model="upnlF.qty"     placeholder="50" />
        </div>
        <button class="btn-primary w-full" @click="calcUPnL">Calculate</button>
        <ResultCard v-if="upnlResult" title="Result" :results="upnlResult" highlightKey="Unrealised P&L" />
      </div>

      <!-- Lot Size -->
      <div class="card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">Lot Size Calculator</h3>
        <div class="grid grid-cols-3 gap-3">
          <CalcInput label="Total Capital"  v-model="lotF.capital" placeholder="100000" />
          <CalcInput label="Stock Price"    v-model="lotF.price"   placeholder="500" />
          <CalcInput label="Allocation %"   v-model="lotF.alloc"   placeholder="10" hint="% of capital to allocate" />
        </div>
        <button class="btn-primary w-full" @click="calcLot">Calculate</button>
        <ResultCard v-if="lotResult" title="Result" :results="lotResult" highlightKey="Shares" />
      </div>

      <!-- Portfolio Allocation -->
      <div class="card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">Portfolio Allocation %</h3>
        <div v-for="(e, i) in allocEntries" :key="i" class="grid grid-cols-2 gap-2">
          <CalcInput :label="`Symbol ${i+1}`" v-model="e.symbol" type="text" placeholder="AAPL" />
          <CalcInput :label="`Value ${i+1}`"  v-model="e.value"  placeholder="10000" />
        </div>
        <button @click="addAlloc" class="text-xs text-brand-400 hover:text-brand-300 transition-colors">+ Add holding</button>
        <button class="btn-primary w-full" @click="calcAlloc">Calculate</button>
        <ResultCard v-if="allocResult" title="Allocation" :results="allocResult" />
      </div>
    </div>
  </div>
</template>
