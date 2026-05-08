import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import ScimTokenModal from '@/components/ScimTokenModal.vue'

// Stub child components
const stubs = {
  CardBoxModal: {
    template:
      '<div class="modal" v-if="modelValue"><slot /><button class="close-btn" @click="$emit(\'form-submitted\')">Close</button></div>',
    props: ['modelValue', 'title', 'buttonLabel'],
  },
  BaseButton: {
    template:
      '<button class="base-button" @click="$emit(\'click\')">{{ label }}</button>',
    props: ['icon', 'label', 'color', 'small'],
  },
}

describe('ScimTokenModal', () => {
  const createWrapper = (props = {}) => {
    return mount(ScimTokenModal, {
      props: {
        modelValue: true,
        token: 'test-token-abc123',
        ...props,
      },
      global: {
        stubs,
      },
    })
  }

  describe('Rendering', () => {
    it('renders the token text', () => {
      const wrapper = createWrapper()
      expect(wrapper.text()).toContain('test-token-abc123')
    })

    it('renders the warning message', () => {
      const wrapper = createWrapper()
      expect(wrapper.text()).toContain('Dieser Token wird nur einmal angezeigt')
    })

    it('renders the copy button', () => {
      const wrapper = createWrapper()
      const copyButton = wrapper.find('.base-button')
      expect(copyButton.exists()).toBe(true)
      expect(copyButton.text()).toContain('Kopieren')
    })

    it('does not render when modelValue is false', () => {
      const wrapper = createWrapper({ modelValue: false })
      expect(wrapper.find('.modal').exists()).toBe(false)
    })
  })

  describe('Interactions', () => {
    it('copies token to clipboard on button click', async () => {
      const writeText = vi.fn().mockResolvedValue(undefined)
      Object.assign(navigator, {
        clipboard: { writeText },
      })

      const wrapper = createWrapper()
      await wrapper.find('.base-button').trigger('click')

      expect(writeText).toHaveBeenCalledWith('test-token-abc123')
    })

    it('emits update:modelValue on close', async () => {
      const wrapper = createWrapper()
      await wrapper.find('.close-btn').trigger('click')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    })
  })
})
