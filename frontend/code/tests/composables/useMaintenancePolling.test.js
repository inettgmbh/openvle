import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h, nextTick } from 'vue'

import {
  _resetPollingState,
  useMaintenancePolling,
} from '@/composables/useMaintenancePolling'
import { useMainStore } from '@/stores/main'

// Mock backend singleton (beginSilent/endSilent)
const backendMock = vi.hoisted(() => ({
  beginSilent: vi.fn(),
  endSilent: vi.fn(),
}))
vi.mock('@/services', () => ({
  default: backendMock,
}))

/**
 * Calls a composable inside a mounted component so that
 * lifecycle hooks (onUnmounted, etc.) have a valid instance.
 */
function withSetup(fn) {
  let result
  const wrapper = mount(
    defineComponent({
      setup() {
        result = fn()
        return () => h('div')
      },
    }),
  )
  return { result, wrapper }
}

describe('useMaintenancePolling', () => {
  let mainStore

  beforeEach(() => {
    vi.useFakeTimers()
    mainStore = useMainStore()
    mainStore.settings = {}
    backendMock.beginSilent.mockClear()
    backendMock.endSilent.mockClear()
  })

  afterEach(() => {
    _resetPollingState()
    vi.clearAllTimers()
    vi.useRealTimers()
  })

  describe('computed properties', () => {
    it('returns isMaintenanceEnabled as false when maintenance is not set', () => {
      const { result } = withSetup(() => useMaintenancePolling())
      expect(result.isMaintenanceEnabled.value).toBe(false)
    })

    it('returns isMaintenanceEnabled as true when maintenance is enabled', () => {
      mainStore.settings = { maintenance: { enabled: true } }
      const { result } = withSetup(() => useMaintenancePolling())
      expect(result.isMaintenanceEnabled.value).toBe(true)
    })

    it('returns maintenanceLabel from settings', () => {
      mainStore.settings = {
        maintenance: { enabled: true, label: 'Wartung aktiv' },
      }
      const { result } = withSetup(() => useMaintenancePolling())
      expect(result.maintenanceLabel.value).toBe('Wartung aktiv')
    })

    it('returns empty string when maintenanceLabel is not set', () => {
      const { result } = withSetup(() => useMaintenancePolling())
      expect(result.maintenanceLabel.value).toBe('')
    })
  })

  describe('polling', () => {
    it('calls loadSettings after 2 minutes', () => {
      withSetup(() => useMaintenancePolling())
      mainStore.loadSettings.mockClear()

      vi.advanceTimersByTime(2 * 60 * 1000)
      expect(mainStore.loadSettings).toHaveBeenCalledTimes(1)
    })

    it('calls loadSettings repeatedly every 2 minutes', () => {
      withSetup(() => useMaintenancePolling())
      mainStore.loadSettings.mockClear()

      vi.advanceTimersByTime(6 * 60 * 1000)
      expect(mainStore.loadSettings).toHaveBeenCalledTimes(3)
    })

    it('does not call loadSettings before the interval elapses', () => {
      withSetup(() => useMaintenancePolling())
      mainStore.loadSettings.mockClear()

      vi.advanceTimersByTime(60 * 1000)
      expect(mainStore.loadSettings).not.toHaveBeenCalled()
    })

    it('polls regardless of maintenance mode being disabled', () => {
      mainStore.settings = { maintenance: { enabled: false } }
      withSetup(() => useMaintenancePolling())
      mainStore.loadSettings.mockClear()

      vi.advanceTimersByTime(2 * 60 * 1000)
      expect(mainStore.loadSettings).toHaveBeenCalledTimes(1)
    })
  })

  describe('silent error handling', () => {
    it('suppresses toasts during polling via beginSilent/endSilent', async () => {
      mainStore.loadSettings.mockResolvedValue(undefined)
      withSetup(() => useMaintenancePolling())

      vi.advanceTimersByTime(2 * 60 * 1000)
      await vi.waitFor(() => {
        expect(backendMock.endSilent).toHaveBeenCalled()
      })

      expect(backendMock.beginSilent).toHaveBeenCalled()
      expect(backendMock.endSilent).toHaveBeenCalled()
    })

    it('calls endSilent even when loadSettings rejects', async () => {
      mainStore.loadSettings.mockRejectedValue(new Error('Network error'))
      withSetup(() => useMaintenancePolling())

      vi.advanceTimersByTime(2 * 60 * 1000)
      await vi.waitFor(() => {
        expect(backendMock.endSilent).toHaveBeenCalled()
      })

      expect(backendMock.beginSilent).toHaveBeenCalled()
      expect(backendMock.endSilent).toHaveBeenCalled()
    })

    it('does not throw when loadSettings fails', async () => {
      mainStore.loadSettings.mockRejectedValue(new Error('Server error'))
      withSetup(() => useMaintenancePolling())

      vi.advanceTimersByTime(2 * 60 * 1000)
      // Should not throw
      await vi.waitFor(() => {
        expect(backendMock.endSilent).toHaveBeenCalled()
      })
    })
  })

  describe('bannerHeight', () => {
    it('sets banner height via setBannerHeight', () => {
      const { result } = withSetup(() => useMaintenancePolling())

      result.setBannerHeight(48)
      expect(result.bannerHeight.value).toBe(48)
    })

    it('resets banner height when maintenance is disabled', async () => {
      mainStore.settings = {
        maintenance: { enabled: true, label: 'Wartung' },
      }
      const { result } = withSetup(() => useMaintenancePolling())

      result.setBannerHeight(48)
      expect(result.bannerHeight.value).toBe(48)

      mainStore.settings = { maintenance: { enabled: false } }
      await nextTick()

      expect(result.bannerHeight.value).toBe(0)
    })

    it('keeps banner height when maintenance stays enabled', async () => {
      mainStore.settings = {
        maintenance: { enabled: true, label: 'Wartung' },
      }
      const { result } = withSetup(() => useMaintenancePolling())

      result.setBannerHeight(48)

      mainStore.settings = {
        maintenance: { enabled: true, label: 'Updated' },
      }
      await nextTick()

      expect(result.bannerHeight.value).toBe(48)
    })

    it('shares banner height across multiple instances', () => {
      const { result: instance1 } = withSetup(() => useMaintenancePolling())
      const { result: instance2 } = withSetup(() => useMaintenancePolling())

      instance1.setBannerHeight(64)
      expect(instance2.bannerHeight.value).toBe(64)
    })
  })
})
