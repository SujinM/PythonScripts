<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <div
    class="min-h-screen flex items-center justify-center p-4"
    style="background: linear-gradient(135deg, #0b0e1a 0%, #0f1629 50%, #0b1020 100%);"
  >
    <!-- Background grid pattern -->
    <div
      class="absolute inset-0 opacity-20"
      style="background-image: url(\"data:image/svg+xml,%3Csvg width='40' height='40' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 40L40 0H20L0 20M40 40V20L20 40' fill='none' stroke='%233b82f6' stroke-opacity='0.3' stroke-width='1'/%3E%3C/svg%3E\");"
    />

    <!-- Logo / branding above form -->
    <div class="relative z-10 w-full max-w-md">
      <div class="text-center mb-8">
        <div class="inline-flex items-center gap-2 mb-3">
          <div class="w-10 h-10 rounded-xl bg-brand-500 flex items-center justify-center shadow-lg shadow-brand-500/40">
            <span class="text-white font-bold text-sm">eT</span>
          </div>
          <span class="text-white font-bold text-2xl tracking-tight">
            eToro <span class="text-brand-400">Pro</span>
          </span>
        </div>
        <p class="text-gray-500 text-sm">Financial Instruments Dashboard</p>
      </div>

      <!-- Auth form slot -->
      <RouterView />
    </div>
  </div>
</template>
