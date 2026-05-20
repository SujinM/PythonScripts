<script setup lang="ts">
import { ref, reactive } from 'vue'
import CalcInput  from '@/components/calc/CalcInput.vue'
import ResultCard from '@/components/calc/ResultCard.vue'
import ErrorAlert from '@/components/calc/ErrorAlert.vue'
import { useCalcHistoryStore } from '@/stores/calcHistoryStore'
import * as C from '@/utils/calcFunctions'

const history = useCalcHistoryStore()
const error   = ref('')

const form   = reactive({ value: '', pct: '' })
const result = ref<Record<string, number | string> | null>(null)

function calc() {
  try {
    error.value = ''
    result.value = C.percentageUpDown(+form.value, +form.pct)
    history.add({
      category: 'Percentage',
      label: 'Value % Up/Down',
      inputs: { value: form.value, percentage: form.pct },
      results: result.value,
    })
  } catch (e: any) { error.value = e.message }
}
</script>

<template>
  <div class="space-y-8 max-w-3xl">
    <div>
      <h2 class="text-xl font-bold text-[var(--text-primary)]">Percentage Calculator</h2>
      <p class="text-sm text-[var(--text-secondary)] mt-0.5">
        Enter a value and a percentage — see the result both up and down.
      </p>
    </div>
    <ErrorAlert v-if="error" :message="error" />
    <div class="card p-6 space-y-5">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <CalcInput label="Value" v-model="form.value" placeholder="e.g. 1000" />
        <CalcInput label="Percentage (%)" v-model="form.pct" placeholder="e.g. 5" />
      </div>
      <button class="btn-primary w-full" @click="calc">Calculate</button>
    </div>
    <ResultCard v-if="result" title="Result" :results="result" highlightKey="Value UP" />
  </div>
</template>
