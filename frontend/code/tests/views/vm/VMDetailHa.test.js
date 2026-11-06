import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { computed, h, ref } from 'vue'

import { FIELD_LIMITS, FIELD_VALUE_LIMITS } from '@/config/fieldLimits'

/**
 * Focused contract tests for the HA (High Availability) logic in VMDetail.vue,
 * mirrored here without mounting the full view:
 *
 * - haConfigured is digest-based ('ignored' alone is ambiguous: the backend
 *   synthesizes digest=null only when the VM is not under HA management)
 * - the config modal uses a toggle model: HA enabled (started/stopped +
 *   limits) or not managed at all; confirming with the toggle off removes
 *   the HA configuration
 * - prefill reflects the live HA info; live states that cannot be selected
 *   (disabled, transient CRM states) fall back to 'started'
 * - the confirm button stays disabled while nothing changed or while the
 *   limits are invalid
 * - after a modal change the tile re-fetches until the async job is visible
 *   (digest differs), bounded by a max number of tries
 */

const HA_SELECTABLE_STATES = ['started', 'stopped']

/**
 * Mounts a minimal component that runs the given setup callback inside
 * a real Vue component context. Returns whatever the callback returns.
 */
function mountSetup(setupCb) {
  let result
  const wrapper = mount({
    setup() {
      result = setupCb()
      return () => h('div')
    },
  })
  return { ...result, wrapper }
}

function withHaSetup() {
  return mountSetup(() => {
    const haInfo = ref(null)
    const haForm = ref({
      enabled: false,
      state: 'started',
      maxRestart: 5,
      maxRelocate: 5,
    })
    const haFormInitial = ref(null)

    const haConfigured = computed(() => Boolean(haInfo.value?.digest))

    const haFormValid = computed(() =>
      [
        [
          haForm.value.maxRestart,
          FIELD_LIMITS.vm.haMaxRestart,
          FIELD_VALUE_LIMITS.vm.haMaxRestart,
        ],
        [
          haForm.value.maxRelocate,
          FIELD_LIMITS.vm.haMaxRelocate,
          FIELD_VALUE_LIMITS.vm.haMaxRelocate,
        ],
      ].every(([value, maxChars, maxValue]) => {
        const n = Number(value)
        return (
          Number.isInteger(n) &&
          n >= 0 &&
          n <= maxValue &&
          String(value).trim().length <= maxChars
        )
      }),
    )

    function haFormNormalized(form) {
      return {
        enabled: Boolean(form.enabled),
        state: form.state,
        maxRestart: Number(form.maxRestart),
        maxRelocate: Number(form.maxRelocate),
      }
    }

    const haFormDirty = computed(
      () =>
        haFormInitial.value === null ||
        JSON.stringify(haFormNormalized(haForm.value)) !== haFormInitial.value,
    )

    const haConfirmDisabled = computed(() => {
      if (!haFormDirty.value) return true
      if (haForm.value.enabled) return !haFormValid.value
      return false
    })

    function prefillHaForm() {
      haForm.value = haConfigured.value
        ? {
            enabled: true,
            state: HA_SELECTABLE_STATES.includes(haInfo.value.state)
              ? haInfo.value.state
              : 'started',
            maxRestart: haInfo.value.max_restart ?? 5,
            maxRelocate: haInfo.value.max_relocate ?? 5,
          }
        : { enabled: false, state: 'started', maxRestart: 5, maxRelocate: 5 }
      haFormInitial.value = JSON.stringify(haFormNormalized(haForm.value))
    }

    return {
      haInfo,
      haForm,
      haConfigured,
      haFormValid,
      haFormDirty,
      haConfirmDisabled,
      prefillHaForm,
    }
  })
}

describe('VMDetail – HA configured check', () => {
  it('is false for the synthesized not-configured response', () => {
    const { haInfo, haConfigured } = withHaSetup()

    haInfo.value = {
      state: 'ignored',
      max_restart: 0,
      max_relocate: 0,
      digest: null,
    }

    expect(haConfigured.value).toBe(false)
  })

  it('is true for a configured resource even in state ignored', () => {
    const { haInfo, haConfigured } = withHaSetup()

    haInfo.value = {
      state: 'ignored',
      max_restart: 5,
      max_relocate: 5,
      digest: 'abc123',
    }

    expect(haConfigured.value).toBe(true)
  })

  it('is false while nothing has been fetched yet', () => {
    const { haConfigured } = withHaSetup()

    expect(haConfigured.value).toBe(false)
  })
})

describe('VMDetail – HA modal prefill', () => {
  it('starts with the toggle off when HA is not configured', () => {
    const { haInfo, haForm, prefillHaForm } = withHaSetup()

    haInfo.value = { state: 'ignored', digest: null }
    prefillHaForm()

    expect(haForm.value).toEqual({
      enabled: false,
      state: 'started',
      maxRestart: 5,
      maxRelocate: 5,
    })
  })

  it('prefills from the live HA configuration with the toggle on', () => {
    const { haInfo, haForm, prefillHaForm } = withHaSetup()

    haInfo.value = {
      state: 'stopped',
      max_restart: 3,
      max_relocate: 1,
      digest: 'abc123',
    }
    prefillHaForm()

    expect(haForm.value).toEqual({
      enabled: true,
      state: 'stopped',
      maxRestart: 3,
      maxRelocate: 1,
    })
  })

  it.each(['disabled', 'migrate', 'error'])(
    'falls back to started for the non-selectable live state %s',
    (state) => {
      const { haInfo, haForm, prefillHaForm } = withHaSetup()

      haInfo.value = {
        state,
        max_restart: 2,
        max_relocate: 2,
        digest: 'abc123',
      }
      prefillHaForm()

      expect(haForm.value.state).toBe('started')
      expect(haForm.value.enabled).toBe(true)
    },
  )
})

describe('VMDetail – HA confirm button gating', () => {
  it('is disabled while nothing changed', () => {
    const { haInfo, prefillHaForm, haConfirmDisabled } = withHaSetup()

    haInfo.value = {
      state: 'started',
      max_restart: 5,
      max_relocate: 5,
      digest: 'abc123',
    }
    prefillHaForm()

    expect(haConfirmDisabled.value).toBe(true)
  })

  it('is disabled for an unconfigured VM until the toggle is switched on', () => {
    const { haInfo, haForm, prefillHaForm, haConfirmDisabled } = withHaSetup()

    haInfo.value = { state: 'ignored', digest: null }
    prefillHaForm()
    expect(haConfirmDisabled.value).toBe(true)

    haForm.value.enabled = true
    expect(haConfirmDisabled.value).toBe(false)
  })

  it('enables when a configured VM is toggled off (removal)', () => {
    const { haInfo, haForm, prefillHaForm, haConfirmDisabled } = withHaSetup()

    haInfo.value = {
      state: 'started',
      max_restart: 5,
      max_relocate: 5,
      digest: 'abc123',
    }
    prefillHaForm()

    haForm.value.enabled = false
    expect(haConfirmDisabled.value).toBe(false)
  })

  it('treats numeric strings from number inputs as unchanged', () => {
    const { haInfo, haForm, prefillHaForm, haConfirmDisabled } = withHaSetup()

    haInfo.value = {
      state: 'started',
      max_restart: 5,
      max_relocate: 5,
      digest: 'abc123',
    }
    prefillHaForm()

    haForm.value.maxRestart = '5'
    expect(haConfirmDisabled.value).toBe(true)

    haForm.value.maxRestart = '6'
    expect(haConfirmDisabled.value).toBe(false)
  })

  it('is disabled while the limits are invalid', () => {
    const { haInfo, haForm, prefillHaForm, haConfirmDisabled } = withHaSetup()

    haInfo.value = { state: 'ignored', digest: null }
    prefillHaForm()
    haForm.value.enabled = true

    haForm.value.maxRestart = -1
    expect(haConfirmDisabled.value).toBe(true)

    haForm.value.maxRestart = 1.5
    expect(haConfirmDisabled.value).toBe(true)

    haForm.value.maxRestart = 'abc'
    expect(haConfirmDisabled.value).toBe(true)

    haForm.value.maxRestart = 0
    expect(haConfirmDisabled.value).toBe(false)
  })
})

describe('VMDetail – HA form validation', () => {
  it('accepts non-negative integers', () => {
    const { haForm, haFormValid } = withHaSetup()

    haForm.value = {
      enabled: true,
      state: 'started',
      maxRestart: 0,
      maxRelocate: 10,
    }
    expect(haFormValid.value).toBe(true)
  })

  it('accepts numeric strings from number inputs', () => {
    const { haForm, haFormValid } = withHaSetup()

    haForm.value = {
      enabled: true,
      state: 'started',
      maxRestart: '3',
      maxRelocate: '0',
    }
    expect(haFormValid.value).toBe(true)
  })

  it('rejects negative, non-integer and non-numeric values', () => {
    const { haForm, haFormValid } = withHaSetup()

    haForm.value.maxRestart = -1
    expect(haFormValid.value).toBe(false)

    haForm.value.maxRestart = 1.5
    expect(haFormValid.value).toBe(false)

    haForm.value.maxRestart = 'abc'
    expect(haFormValid.value).toBe(false)
  })

  it('enforces the FIELD_VALUE_LIMITS max value on both counts', () => {
    const { haForm, haFormValid } = withHaSetup()

    haForm.value.maxRestart = FIELD_VALUE_LIMITS.vm.haMaxRestart
    expect(haFormValid.value).toBe(true)

    haForm.value.maxRestart = FIELD_VALUE_LIMITS.vm.haMaxRestart + 1
    expect(haFormValid.value).toBe(false)

    haForm.value.maxRestart = 5
    haForm.value.maxRelocate = FIELD_VALUE_LIMITS.vm.haMaxRelocate + 1
    expect(haFormValid.value).toBe(false)
  })

  it('enforces the FIELD_LIMITS char limit even for small values', () => {
    const { haForm, haFormValid } = withHaSetup()

    // value 15 is within the max, but '015' exceeds the 2-char limit
    haForm.value.maxRestart = '015'
    expect(haFormValid.value).toBe(false)
  })
})

function withStopWarningSetup() {
  return mountSetup(() => {
    const vm = ref({ status: 'running' })
    const haForm = ref({
      enabled: true,
      state: 'started',
      maxRestart: 5,
      maxRelocate: 5,
    })

    const haStopWarning = computed(
      () =>
        haForm.value.enabled &&
        haForm.value.state === 'stopped' &&
        vm.value?.status === 'running',
    )

    return { vm, haForm, haStopWarning }
  })
}

describe('VMDetail – HA stop warning', () => {
  it('warns when a running VM is set to stopped', () => {
    const { haForm, haStopWarning } = withStopWarningSetup()

    haForm.value.state = 'stopped'
    expect(haStopWarning.value).toBe(true)
  })

  it('does not warn for a VM that is not running', () => {
    const { vm, haForm, haStopWarning } = withStopWarningSetup()

    vm.value.status = 'stopped'
    haForm.value.state = 'stopped'
    expect(haStopWarning.value).toBe(false)
  })

  it('does not warn while started is selected or HA is disabled', () => {
    const { haForm, haStopWarning } = withStopWarningSetup()

    expect(haStopWarning.value).toBe(false)

    haForm.value = { ...haForm.value, state: 'stopped', enabled: false }
    expect(haStopWarning.value).toBe(false)
  })
})

const HA_REFETCH_INTERVAL_MS = 3000
const HA_REFETCH_MAX_TRIES = 10

function withRefetchSetup() {
  return mountSetup(() => {
    const haInfo = ref({ state: 'ignored', digest: null })
    const fetchHaState = vi.fn(() => Promise.resolve(true))
    let haRefetchTimeoutId = null

    function scheduleHaRefetch() {
      const previousDigest = haInfo.value?.digest ?? null
      let tries = 0

      const poll = async () => {
        tries += 1
        await fetchHaState()
        const digest = haInfo.value?.digest ?? null
        if (digest !== previousDigest || tries >= HA_REFETCH_MAX_TRIES) return
        haRefetchTimeoutId = setTimeout(poll, HA_REFETCH_INTERVAL_MS)
      }

      clearTimeout(haRefetchTimeoutId)
      haRefetchTimeoutId = setTimeout(poll, HA_REFETCH_INTERVAL_MS)
    }

    return { haInfo, fetchHaState, scheduleHaRefetch }
  })
}

describe('VMDetail – HA refetch after modal changes', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('re-fetches until the async change is visible, then stops', async () => {
    vi.useFakeTimers()
    const { haInfo, fetchHaState, scheduleHaRefetch } = withRefetchSetup()

    scheduleHaRefetch()

    // first poll: job not visible yet, digest unchanged
    await vi.advanceTimersByTimeAsync(HA_REFETCH_INTERVAL_MS)
    expect(fetchHaState).toHaveBeenCalledTimes(1)

    // second poll: the fetch now sees the applied configuration
    fetchHaState.mockImplementation(async () => {
      haInfo.value = { state: 'started', digest: 'abc123' }
      return true
    })
    await vi.advanceTimersByTimeAsync(HA_REFETCH_INTERVAL_MS)
    expect(fetchHaState).toHaveBeenCalledTimes(2)

    // digest changed → no further polls
    await vi.advanceTimersByTimeAsync(HA_REFETCH_INTERVAL_MS * 5)
    expect(fetchHaState).toHaveBeenCalledTimes(2)
  })

  it('gives up after the max number of tries', async () => {
    vi.useFakeTimers()
    const { fetchHaState, scheduleHaRefetch } = withRefetchSetup()

    scheduleHaRefetch()

    await vi.advanceTimersByTimeAsync(
      HA_REFETCH_INTERVAL_MS * (HA_REFETCH_MAX_TRIES + 5),
    )
    expect(fetchHaState).toHaveBeenCalledTimes(HA_REFETCH_MAX_TRIES)
  })
})
