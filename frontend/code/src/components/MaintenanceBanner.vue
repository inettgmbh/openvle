<script setup>
import { mdiAlert } from '@mdi/js'
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

import BaseIcon from '@/components/BaseIcon.vue'
import { useMaintenancePolling } from '@/composables/useMaintenancePolling'

const { isMaintenanceEnabled, maintenanceLabel, setBannerHeight } =
  useMaintenancePolling()

const bannerRef = ref(null)
let resizeObserver = null

function updateHeight() {
  if (bannerRef.value) {
    setBannerHeight(bannerRef.value.offsetHeight)
  }
}

onMounted(() => {
  if (bannerRef.value) {
    resizeObserver = new ResizeObserver(updateHeight)
    resizeObserver.observe(bannerRef.value)
    updateHeight()
  }
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  setBannerHeight(0)
})

watch(isMaintenanceEnabled, async (enabled) => {
  if (enabled) {
    await nextTick()
    updateHeight()
  } else {
    setBannerHeight(0)
  }
})
</script>

<template>
  <div
    v-if="isMaintenanceEnabled"
    ref="bannerRef"
    class="fixed top-0 inset-x-0 z-50 bg-yellow-500 text-yellow-900 py-2 px-4 flex items-center justify-center gap-2 font-medium shadow-md"
  >
    <BaseIcon :path="mdiAlert" size="20" class="flex-shrink-0" />

    <span class="text-center">{{ maintenanceLabel }}</span>
  </div>
</template>
