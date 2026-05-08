import { computed, onUnmounted, ref, watch } from 'vue'

import { useUserSettingsStore, VIEW_KIND } from '@/stores/userSettings'

/**
 * Composable for list-view auto-refresh with toggle and timer-aware
 * manual reload. Centralizes the setInterval lifecycle so all list views
 * behave consistently.
 *
 * When `objectType` is provided, the toggle state is persisted via the
 * userSettings store at `objects.<objectType>.<viewKind>.autoRefresh`
 * and survives page reloads. On logout the store is reset.
 *
 * @param {Object} options
 * @param {Function} options.fetch - Async fetch function called on each tick.
 * @param {number} [options.intervalMs=15000] - Refresh interval in ms.
 * @param {boolean} [options.defaultEnabled=true] - Initial toggle state when no persisted value exists.
 * @param {string} [options.objectType] - OBJECT_TYPE constant; enables persistence when set.
 * @param {string} [options.viewKind=VIEW_KIND.LIST] - VIEW_KIND constant; defaults to list.
 * @returns {{
 *   autoRefreshEnabled: import('vue').WritableComputedRef<boolean> | import('vue').Ref<boolean>,
 *   intervalSeconds: import('vue').ComputedRef<number>,
 *   manualReload: () => void,
 * }}
 */
export function useListAutoRefresh({
  fetch,
  intervalMs = 15000,
  defaultEnabled = true,
  objectType = null,
  viewKind = VIEW_KIND.LIST,
}) {
  const intervalSeconds = computed(() => Math.round(intervalMs / 1000))

  let autoRefreshEnabled
  if (objectType) {
    const userSettings = useUserSettingsStore()
    const path = `objects.${objectType}.${viewKind}.autoRefresh`
    autoRefreshEnabled = computed({
      get: () => userSettings.get(path, defaultEnabled),
      set: (value) => userSettings.set(path, value),
    })
  } else {
    autoRefreshEnabled = ref(defaultEnabled)
  }

  let intervalId = null

  function start() {
    stop()
    intervalId = setInterval(fetch, intervalMs)
  }

  function stop() {
    if (intervalId) {
      clearInterval(intervalId)
      intervalId = null
    }
  }

  /**
   * Calls fetch and, if auto-refresh is enabled, resets the interval timer
   * so the next automatic tick happens a full intervalMs from now.
   */
  function manualReload() {
    fetch()
    if (autoRefreshEnabled.value) start()
  }

  watch(
    autoRefreshEnabled,
    (enabled) => {
      if (enabled) start()
      else stop()
    },
    { immediate: true },
  )

  onUnmounted(stop)

  return {
    autoRefreshEnabled,
    intervalSeconds,
    manualReload,
  }
}
