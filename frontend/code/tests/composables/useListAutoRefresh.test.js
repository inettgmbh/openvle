import { createTestingPinia } from '@pinia/testing'
import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h, nextTick } from 'vue'

import { useListAutoRefresh } from '@/composables/useListAutoRefresh'
import {
  OBJECT_TYPE,
  useUserSettingsStore,
  VIEW_KIND,
} from '@/stores/userSettings'

function withSetup(fn) {
  let result
  const wrapper = mount(
    defineComponent({
      setup() {
        result = fn()
        return () => h('div')
      },
    }),
    {
      global: {
        plugins: [createTestingPinia({ stubActions: false, createSpy: vi.fn })],
      },
    },
  )
  return { result, wrapper }
}

describe('useListAutoRefresh', () => {
  let fetchMock

  beforeEach(() => {
    vi.useFakeTimers()
    fetchMock = vi.fn()
  })

  afterEach(() => {
    vi.clearAllTimers()
    vi.useRealTimers()
  })

  it('starts polling on mount when defaultEnabled is true', () => {
    withSetup(() => useListAutoRefresh({ fetch: fetchMock, intervalMs: 1000 }))

    expect(fetchMock).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1000)
    expect(fetchMock).toHaveBeenCalledTimes(1)
    vi.advanceTimersByTime(1000)
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('does not poll when defaultEnabled is false', () => {
    withSetup(() =>
      useListAutoRefresh({
        fetch: fetchMock,
        intervalMs: 1000,
        defaultEnabled: false,
      }),
    )

    vi.advanceTimersByTime(5000)
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('stops polling when toggled off', async () => {
    const { result } = withSetup(() =>
      useListAutoRefresh({ fetch: fetchMock, intervalMs: 1000 }),
    )

    vi.advanceTimersByTime(1000)
    expect(fetchMock).toHaveBeenCalledTimes(1)

    result.autoRefreshEnabled.value = false
    await nextTick()
    vi.advanceTimersByTime(5000)
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('resumes polling when toggled back on', async () => {
    const { result } = withSetup(() =>
      useListAutoRefresh({
        fetch: fetchMock,
        intervalMs: 1000,
        defaultEnabled: false,
      }),
    )

    result.autoRefreshEnabled.value = true
    await nextTick()
    vi.advanceTimersByTime(1000)
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('manualReload calls fetch immediately and resets the interval', () => {
    const { result } = withSetup(() =>
      useListAutoRefresh({ fetch: fetchMock, intervalMs: 1000 }),
    )

    // Advance halfway through the first interval
    vi.advanceTimersByTime(500)
    expect(fetchMock).toHaveBeenCalledTimes(0)

    // Manual reload: fires fetch + resets timer
    result.manualReload()
    expect(fetchMock).toHaveBeenCalledTimes(1)

    // Old half-elapsed timer should be discarded; need full interval again
    vi.advanceTimersByTime(500)
    expect(fetchMock).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(500)
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('manualReload still fires fetch when auto-refresh is disabled', () => {
    const { result } = withSetup(() =>
      useListAutoRefresh({
        fetch: fetchMock,
        intervalMs: 1000,
        defaultEnabled: false,
      }),
    )

    result.manualReload()
    expect(fetchMock).toHaveBeenCalledTimes(1)

    // No interval should have been started
    vi.advanceTimersByTime(5000)
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('exposes intervalSeconds derived from intervalMs', () => {
    const { result } = withSetup(() =>
      useListAutoRefresh({ fetch: fetchMock, intervalMs: 15000 }),
    )

    expect(result.intervalSeconds.value).toBe(15)
  })

  it('clears the interval on unmount', () => {
    const { wrapper } = withSetup(() =>
      useListAutoRefresh({ fetch: fetchMock, intervalMs: 1000 }),
    )

    wrapper.unmount()
    vi.advanceTimersByTime(5000)
    expect(fetchMock).not.toHaveBeenCalled()
  })

  describe('with objectType (persistence)', () => {
    it('uses defaultEnabled when no setting is stored yet', () => {
      const { result } = withSetup(() =>
        useListAutoRefresh({
          fetch: fetchMock,
          intervalMs: 1000,
          objectType: OBJECT_TYPE.VMS,
          defaultEnabled: true,
        }),
      )
      expect(result.autoRefreshEnabled.value).toBe(true)
      vi.advanceTimersByTime(1000)
      expect(fetchMock).toHaveBeenCalledTimes(1)
    })

    it('reads the persisted value from the userSettings store', () => {
      const { result } = withSetup(() => {
        const userSettings = useUserSettingsStore()
        userSettings.set(
          `objects.${OBJECT_TYPE.VMS}.${VIEW_KIND.LIST}.autoRefresh`,
          false,
        )
        return useListAutoRefresh({
          fetch: fetchMock,
          intervalMs: 1000,
          objectType: OBJECT_TYPE.VMS,
          defaultEnabled: true,
        })
      })
      expect(result.autoRefreshEnabled.value).toBe(false)
      vi.advanceTimersByTime(5000)
      expect(fetchMock).not.toHaveBeenCalled()
    })

    it('writes back to the userSettings store when toggled', async () => {
      let userSettings
      const { result } = withSetup(() => {
        userSettings = useUserSettingsStore()
        return useListAutoRefresh({
          fetch: fetchMock,
          intervalMs: 1000,
          objectType: OBJECT_TYPE.VMS,
          defaultEnabled: true,
        })
      })

      result.autoRefreshEnabled.value = false
      await nextTick()

      expect(
        userSettings.get(
          `objects.${OBJECT_TYPE.VMS}.${VIEW_KIND.LIST}.autoRefresh`,
        ),
      ).toBe(false)
      vi.advanceTimersByTime(5000)
      expect(fetchMock).not.toHaveBeenCalled()
    })

    it('keeps state isolated between object types', async () => {
      let userSettings
      const { result } = withSetup(() => {
        userSettings = useUserSettingsStore()
        return useListAutoRefresh({
          fetch: fetchMock,
          intervalMs: 1000,
          objectType: OBJECT_TYPE.VMS,
          defaultEnabled: true,
        })
      })

      result.autoRefreshEnabled.value = false
      await nextTick()

      expect(
        userSettings.get(
          `objects.${OBJECT_TYPE.VMS}.${VIEW_KIND.LIST}.autoRefresh`,
        ),
      ).toBe(false)
      expect(
        userSettings.get(
          `objects.${OBJECT_TYPE.EVENTS}.${VIEW_KIND.LIST}.autoRefresh`,
          true,
        ),
      ).toBe(true)
    })

    it('persists under the explicit viewKind when not LIST', async () => {
      let userSettings
      const { result } = withSetup(() => {
        userSettings = useUserSettingsStore()
        return useListAutoRefresh({
          fetch: fetchMock,
          intervalMs: 1000,
          objectType: OBJECT_TYPE.VMS,
          viewKind: VIEW_KIND.DETAIL,
          defaultEnabled: true,
        })
      })

      result.autoRefreshEnabled.value = false
      await nextTick()

      expect(
        userSettings.get(
          `objects.${OBJECT_TYPE.VMS}.${VIEW_KIND.DETAIL}.autoRefresh`,
        ),
      ).toBe(false)
      // List bucket stays untouched
      expect(
        userSettings.get(
          `objects.${OBJECT_TYPE.VMS}.${VIEW_KIND.LIST}.autoRefresh`,
          'unset',
        ),
      ).toBe('unset')
    })
  })
})
