<script setup>
import { computed, onMounted, onUnmounted } from 'vue'

import MaintenanceBanner from '@/components/MaintenanceBanner.vue'
import { useMaintenancePolling } from '@/composables/useMaintenancePolling'
import { useStyleStore } from '@/stores/style.js'

const styleStore = useStyleStore()
const { bannerHeight } = useMaintenancePolling()

const contentPaddingTop = computed(() =>
  bannerHeight.value > 0 ? `${bannerHeight.value}px` : '0',
)

onMounted(async () => {
  styleStore.initializeThemeWatcher()
})

onUnmounted(() => {
  styleStore.destroyThemeWatcher()
})
</script>

<template>
  <div :class="{ dark: styleStore.darkMode }">
    <MaintenanceBanner />

    <div
      :style="{ paddingTop: contentPaddingTop }"
      class="bg-gray-50 dark:bg-slate-800 dark:text-slate-100"
    >
      <slot />
    </div>
  </div>
</template>
