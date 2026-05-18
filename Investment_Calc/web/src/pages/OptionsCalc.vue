<script setup lang="ts">
import { ref, reactive } from 'vue'
import CalcInput  from '@/components/common/CalcInput.vue'
import ResultCard from '@/components/common/ResultCard.vue'
import ErrorAlert from '@/components/common/ErrorAlert.vue'
import { useHistoryStore } from '@/stores/historyStore'
import * as C from '@/utils/calculations'

const history = useHistoryStore()
const error   = ref('')

// Intrinsic Value
const ivF = reactive({ type: 'call' as 'call'|'put', spot: '', strike: '' })
const ivResult = ref<Record<string, number | string> | null>(null)
function calcIV() {
  try { error.value = ''; ivResult.value = C.intrinsicValue(ivF.type, +ivF.spot, +ivF.strike) }
  catch (e: any) { error.value = e.message }
}

// Black-Scholes
const bsF = reactive({ type: 'call' as 'call'|'put', S: '', K: '', T: '', r: '', sigma: '' })
const bsResult = ref<Record<string, number | string> | null>(null)
function calcBS() {
  try {
    error.value = ''
    bsResult.value = C.blackScholes(bsF.type, +bsF.S, +bsF.K, +bsF.T, +bsF.r / 100, +bsF.sigma / 100)
    history.add({ category: 'Options', label: 'Black-Scholes', inputs: { ...bsF }, results: bsResult.value })
  } catch (e: any) { error.value = e.message }
}
</script>

<template>
  <div class="space-y-8 max-w-5xl">
    <div>
      <h2 class="text-xl font-bold text-[var(--text-primary)]">Options Calculator</h2>
      <p class="text-sm text-[var(--text-secondary)] mt-0.5">Intrinsic value, Black-Scholes pricing, Delta, Gamma, Theta</p>
    </div>

    <ErrorAlert v-if="error" :message="error" />

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Intrinsic Value -->
      <div class="card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">Intrinsic Value</h3>
        <div>
          <label class="calc-label">Option Type</label>
          <div class="flex gap-3">
            <label
              v-for="t in ['call', 'put']" :key="t"
              :class="[
                'flex-1 text-center py-2 rounded-lg border text-sm font-medium cursor-pointer transition-all',
                ivF.type === t
                  ? 'bg-brand-600/20 border-brand-500/50 text-brand-400'
                  : 'border-[var(--surface-border)] text-[var(--text-secondary)] hover:bg-white/5'
              ]"
            >
              <input type="radio" v-model="ivF.type" :value="t" class="sr-only" />
              {{ t.toUpperCase() }}
            </label>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <CalcInput label="Spot Price"   v-model="ivF.spot"   placeholder="105" />
          <CalcInput label="Strike Price" v-model="ivF.strike" placeholder="100" />
        </div>
        <button class="btn-primary w-full" @click="calcIV">Calculate</button>
        <ResultCard v-if="ivResult" title="Result" :results="ivResult" highlightKey="Intrinsic Value" />
      </div>

      <!-- Black-Scholes -->
      <div class="card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)]">Black-Scholes Pricing + Greeks</h3>
        <div>
          <label class="calc-label">Option Type</label>
          <div class="flex gap-3">
            <label
              v-for="t in ['call', 'put']" :key="t"
              :class="[
                'flex-1 text-center py-2 rounded-lg border text-sm font-medium cursor-pointer transition-all',
                bsF.type === t
                  ? 'bg-brand-600/20 border-brand-500/50 text-brand-400'
                  : 'border-[var(--surface-border)] text-[var(--text-secondary)] hover:bg-white/5'
              ]"
            >
              <input type="radio" v-model="bsF.type" :value="t" class="sr-only" />
              {{ t.toUpperCase() }}
            </label>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <CalcInput label="Spot Price (S)"       v-model="bsF.S"     placeholder="100" />
          <CalcInput label="Strike Price (K)"     v-model="bsF.K"     placeholder="100" />
          <CalcInput label="Time to Expiry (yrs)" v-model="bsF.T"     placeholder="0.25" hint="e.g. 0.25 = 3 months" />
          <CalcInput label="Risk-Free Rate %"     v-model="bsF.r"     placeholder="6.5" />
          <CalcInput label="Implied Volatility %" v-model="bsF.sigma" placeholder="20" hint="e.g. 20 = 20% IV" />
        </div>
        <button class="btn-primary w-full" @click="calcBS">Calculate</button>
        <ResultCard v-if="bsResult" title="Price + Greeks" :results="bsResult" highlightKey="Price" />
      </div>
    </div>

    <!-- Info Box -->
    <div class="card p-5 border-brand-500/20">
      <h4 class="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-widest mb-3">Greeks Reference</h4>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
        <div>
          <span class="text-brand-400 font-semibold">Delta</span>
          <p class="text-xs text-[var(--text-muted)] mt-0.5">Rate of change of option price per ₹1 move in spot. Ranges -1 to +1.</p>
        </div>
        <div>
          <span class="text-brand-400 font-semibold">Gamma</span>
          <p class="text-xs text-[var(--text-muted)] mt-0.5">Rate of change of Delta per ₹1 move in spot. Higher near ATM.</p>
        </div>
        <div>
          <span class="text-brand-400 font-semibold">Theta</span>
          <p class="text-xs text-[var(--text-muted)] mt-0.5">Daily time decay of option value. Typically negative for buyers.</p>
        </div>
      </div>
    </div>
  </div>
</template>
