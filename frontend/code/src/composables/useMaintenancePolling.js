import { computed, onUnmounted, ref, watch } from 'vue'

import backend from '@/services'
import { useMainStore } from '@/stores/main'

// Shared state for banner height across components
const bannerHeight = ref(0)

// Shared polling state to prevent duplicate intervals across component instances
let intervalId = null
let activeConsumers = 0

/** @internal Reset shared state between test runs. */
export function _resetPollingState() {
  if (intervalId) clearInterval(intervalId)
  intervalId = null
  activeConsumers = 0
}

/**
 * Composable for maintenance mode polling.
 * Polls settings every 2 minutes for near-real-time updates.
 *
 * @returns {Object} Maintenance state and polling status.
 */
export function useMaintenancePolling() {
  const mainStore = useMainStore()
  const POLL_INTERVAL_MS = 2 * 60 * 1000 // 2 minutes

  const isMaintenanceEnabled = computed(
    () => mainStore.settings?.maintenance?.enabled ?? false,
  )

  const maintenanceLabel = computed(
    () => mainStore.settings?.maintenance?.label ?? '',
  )

  async function silentLoadSettings() {
    backend.beginSilent()
    try {
      await mainStore.loadSettings()
    } catch {
      // Silently ignore errors during background polling
    } finally {
      backend.endSilent()
    }
  }

  function startPolling() {
    activeConsumers++
    if (intervalId) return
    intervalId = setInterval(silentLoadSettings, POLL_INTERVAL_MS)
  }

  function stopPolling() {
    activeConsumers--
    if (activeConsumers <= 0 && intervalId) {
      clearInterval(intervalId)
      intervalId = null
      activeConsumers = 0
    }
  }

  function setBannerHeight(height) {
    bannerHeight.value = height
  }

  // Reset banner height when maintenance is disabled
  watch(isMaintenanceEnabled, (enabled) => {
    if (!enabled) {
      bannerHeight.value = 0
    }
  })

  // Always poll settings for near-real-time updates
  startPolling()

  onUnmounted(() => stopPolling())

  return {
    isMaintenanceEnabled,
    maintenanceLabel,
    bannerHeight,
    setBannerHeight,
  }
}
