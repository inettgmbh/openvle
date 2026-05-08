import { createTestingPinia } from '@pinia/testing'
import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import RateLimitModal from '@/components/RateLimitModal.vue'
import { useRateLimitStore } from '@/stores/rateLimit'

vi.mock('@/stores/style.js', () => ({
  useStyleStore: () => ({ darkMode: false }),
}))

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key, params) => (params ? `${key}:${JSON.stringify(params)}` : key),
  }),
}))

const stubs = {
  CardBoxModal: {
    props: {
      modelValue: { type: Boolean, default: false },
      title: String,
      buttonLabel: String,
      button: String,
      hasButton: { type: Boolean, default: true },
      crossmark: { type: Boolean, default: true },
    },
    emits: ['update:modelValue', 'form-submitted', 'cancel'],
    template: `
      <div v-if="modelValue" class="modal" data-test="modal">
        <h3>{{ title }}</h3>
        <slot />
        <button v-if="hasButton" data-test="confirm" @click="$emit('update:modelValue', false); $emit('form-submitted')">{{ buttonLabel }}</button>
        <button v-if="crossmark" data-test="cancel" @click="$emit('update:modelValue', false); $emit('cancel')">x</button>
      </div>
    `,
  },
}

function mountWithPinia() {
  return mount(RateLimitModal, {
    global: {
      plugins: [createTestingPinia({ createSpy: vi.fn, stubActions: false })],
      stubs,
    },
  })
}

describe('RateLimitModal', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-04-30T12:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('does not render when store is inactive', () => {
    const wrapper = mountWithPinia()
    expect(wrapper.find('[data-test="modal"]').exists()).toBe(false)
  })

  it('renders relative countdown above and absolute time in the message', async () => {
    const wrapper = mountWithPinia()
    const store = useRateLimitStore()

    store.trigger({ retryAfter: 60, endpoint: '/auth/login' })
    await nextTick()

    expect(wrapper.find('[data-test="modal"]').exists()).toBe(true)
    // Top: relative countdown — endpoint message uses .time variant
    expect(wrapper.text()).toContain('views.rateLimit.minutes')
    expect(wrapper.text()).toMatch(/count\\?":1\b/)
    // Bottom: message references the .time variant of the endpoint key
    expect(wrapper.text()).toContain('views.rateLimit.endpoints.auth.time')
    expect(wrapper.text()).toContain('time')
  })

  it('renders relative seconds when remaining time is below a minute', async () => {
    const wrapper = mountWithPinia()
    const store = useRateLimitStore()

    store.trigger({ retryAfter: 30, endpoint: '/users/' })
    await nextTick()

    expect(wrapper.find('[data-test="modal"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('views.rateLimit.seconds')
    expect(wrapper.text()).toMatch(/count\\?":30\b/)
  })

  it('does not render in toast mode', async () => {
    const wrapper = mountWithPinia()
    const store = useRateLimitStore()

    store.trigger({ retryAfter: 5, endpoint: '/users/' })
    await nextTick()

    expect(wrapper.find('[data-test="modal"]').exists()).toBe(false)
  })

  it('renders without confirm or close button when endpoint is non-dismissable', async () => {
    const wrapper = mountWithPinia()
    const store = useRateLimitStore()

    store.trigger({ retryAfter: 60, endpoint: '/auth/login' })
    await nextTick()

    expect(wrapper.find('[data-test="confirm"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="cancel"]').exists()).toBe(false)
  })

  it('renders close button when endpoint is dismissable', async () => {
    const wrapper = mountWithPinia()
    const store = useRateLimitStore()

    store.trigger({ retryAfter: 60, endpoint: '/me/password' })
    await nextTick()

    expect(wrapper.find('[data-test="cancel"]').exists()).toBe(true)
  })

  it('hides on dismiss click but keeps the lockout active in the store', async () => {
    const wrapper = mountWithPinia()
    const store = useRateLimitStore()

    store.trigger({ retryAfter: 60, endpoint: '/me/password' })
    await nextTick()
    expect(wrapper.find('[data-test="modal"]').exists()).toBe(true)

    await wrapper.find('[data-test="cancel"]').trigger('click')

    expect(wrapper.find('[data-test="modal"]').exists()).toBe(false)
    // Store still tracks the lockout so submit-button-disabling keeps working
    expect(store.active).toBe(true)
    expect(store.dismissed).toBe(true)
  })

  it('hides automatically when store clears after timer', async () => {
    const wrapper = mountWithPinia()
    const store = useRateLimitStore()

    store.trigger({ retryAfter: 30, endpoint: '/users/' })
    await nextTick()
    expect(wrapper.find('[data-test="modal"]').exists()).toBe(true)

    vi.advanceTimersByTime(30_000)
    await nextTick()
    expect(wrapper.find('[data-test="modal"]').exists()).toBe(false)
  })
})
