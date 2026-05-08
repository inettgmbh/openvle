import BaseIconMock from '../mocks/components/BaseIconMock'

import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import SpecCard from '@/components/SpecCard.vue'

const stubs = {
  BaseIcon: BaseIconMock,
  'router-link': {
    template: '<a :href="to" class="router-link"><slot /></a>',
    props: ['to'],
  },
}

describe('SpecCard', () => {
  let wrapper

  const createWrapper = (props = {}) => {
    wrapper = mount(SpecCard, {
      props: {
        icon: 'mdi-test-icon',
        value: '4',
        label: 'CPU Kerne',
        ...props,
      },
      global: { stubs },
    })
    return wrapper
  }

  afterEach(() => {
    if (wrapper) wrapper.unmount()
  })

  describe('rendering', () => {
    it('renders value and label', () => {
      createWrapper()
      expect(wrapper.text()).toContain('4')
      expect(wrapper.text()).toContain('CPU Kerne')
    })

    it('renders icon via BaseIcon', () => {
      createWrapper()
      const icon = wrapper.findComponent(BaseIconMock)
      expect(icon.exists()).toBe(true)
      expect(icon.props('path')).toBe('mdi-test-icon')
    })

    it('renders as div when no link', () => {
      createWrapper()
      expect(wrapper.element.tagName).toBe('DIV')
      expect(wrapper.find('.router-link').exists()).toBe(false)
    })

    it('renders as router-link when link is set', () => {
      createWrapper({ link: '/os/123' })
      const link = wrapper.find('.router-link')
      expect(link.exists()).toBe(true)
      expect(link.attributes('href')).toBe('/os/123')
    })
  })

  describe('hint', () => {
    it('does not render hint by default', () => {
      createWrapper()
      expect(wrapper.text()).not.toContain('Keine Leseberechtigung')
    })

    it('renders hint when provided', () => {
      createWrapper({ hint: 'Keine Leseberechtigung' })
      expect(wrapper.text()).toContain('Keine Leseberechtigung')
    })
  })

  describe('color', () => {
    it('applies blue color classes by default', () => {
      createWrapper()
      const badge = wrapper.find('.rounded-lg')
      expect(badge.classes()).toContain('bg-blue-50')
    })

    it('applies specified color classes', () => {
      createWrapper({ color: 'emerald' })
      const badge = wrapper.find('.rounded-lg')
      expect(badge.classes()).toContain('bg-emerald-50')
    })

    it('applies hover classes matching color when link is set', () => {
      createWrapper({ link: '/test', color: 'rose' })
      const link = wrapper.find('.router-link')
      expect(link.classes()).toContain('hover:border-rose-400')
    })
  })

  describe('copyable', () => {
    beforeEach(() => {
      Object.assign(navigator, {
        clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
      })
    })

    it('does not add select-none without copyable', () => {
      createWrapper()
      expect(wrapper.element.classList.contains('select-none')).toBe(false)
    })

    it('adds select-none class when copyable', () => {
      createWrapper({ copyable: true })
      expect(wrapper.element.classList.contains('select-none')).toBe(true)
    })

    it('copies value to clipboard on dblclick', async () => {
      createWrapper({ copyable: true, value: '192.168.1.1' })
      await wrapper.trigger('dblclick')
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('192.168.1.1')
    })

    it('shows copied overlay after dblclick', async () => {
      createWrapper({ copyable: true, value: '10.0.0.1' })
      expect(wrapper.text()).not.toContain('Kopiert!')
      await wrapper.trigger('dblclick')
      await nextTick()
      expect(wrapper.text()).toContain('Kopiert!')
    })

    it('does not copy when not copyable', async () => {
      createWrapper({ value: '10.0.0.1' })
      await wrapper.trigger('dblclick')
      expect(navigator.clipboard.writeText).not.toHaveBeenCalled()
    })

    it('does not copy when value is falsy', async () => {
      createWrapper({ copyable: true, value: '' })
      await wrapper.trigger('dblclick')
      expect(navigator.clipboard.writeText).not.toHaveBeenCalled()
    })
  })
})
