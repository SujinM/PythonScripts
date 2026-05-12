<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import { useSettingsStore } from '@/stores/settingsStore'
import NotificationToast from '@/components/common/NotificationToast.vue'

const settings = useSettingsStore()

onMounted(() => {
  // Apply persisted theme on first load
  settings.applyTheme()
})
</script>

<template>
  <RouterView />
  <NotificationToast />
</template>
