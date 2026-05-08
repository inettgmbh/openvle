import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import CardBoxComponentBody from '@/components/CardBoxComponentBody.vue'

describe('CardBoxComponentBody', () => {
  const createWrapper = (props = {}, options = {}) =>
    mount(CardBoxComponentBody, {
      props,
      slots: options.slots,
    })

  describe('Rendering', () => {
    it('renders slot content', () => {
      const wrapper = createWrapper(
        {},
        { slots: { default: '<p class="probe">hello</p>' } },
      )
      expect(wrapper.find('.probe').exists()).toBe(true)
    })

    it('always applies flex-1 so it grows inside flex containers', () => {
      const wrapper = createWrapper()
      expect(wrapper.classes()).toContain('flex-1')
    })
  })

  describe('Padding', () => {
    it('applies p-6 by default', () => {
      const wrapper = createWrapper()
      expect(wrapper.classes()).toContain('p-6')
    })

    it('omits p-6 when noPadding is true', () => {
      const wrapper = createWrapper({ noPadding: true })
      expect(wrapper.classes()).not.toContain('p-6')
    })
  })

  describe('Modal scrolling', () => {
    // Regression guard: in flex-col modals with max-height, the body must
    // be allowed to shrink below content size (min-h-0) and scroll
    // (overflow-y-auto), otherwise the content overflows the modal and
    // pushes the footer buttons out of view.
    it('applies min-h-0 and overflow-y-auto when isModal is true', () => {
      const wrapper = createWrapper({ isModal: true })
      expect(wrapper.classes()).toContain('min-h-0')
      expect(wrapper.classes()).toContain('overflow-y-auto')
    })

    // Regression guard: page-level cards must NOT be scroll containers,
    // because that would clip absolute-positioned children (search dropdowns,
    // etc.) and break sticky positioning relative to the page.
    it('omits min-h-0 and overflow-y-auto by default (non-modal)', () => {
      const wrapper = createWrapper()
      expect(wrapper.classes()).not.toContain('min-h-0')
      expect(wrapper.classes()).not.toContain('overflow-y-auto')
    })

    it('omits scrolling classes when isModal is explicitly false', () => {
      const wrapper = createWrapper({ isModal: false })
      expect(wrapper.classes()).not.toContain('min-h-0')
      expect(wrapper.classes()).not.toContain('overflow-y-auto')
    })

    // Regression guard: search modals must not create a clipping context,
    // otherwise absolute-positioned dropdowns from SearchField are trapped
    // inside the modal instead of flowing out beneath it.
    it('omits scrolling classes when isModal and hasSearch are true', () => {
      const wrapper = createWrapper({ isModal: true, hasSearch: true })
      expect(wrapper.classes()).not.toContain('min-h-0')
      expect(wrapper.classes()).not.toContain('overflow-y-auto')
    })
  })

  describe('Combined behavior', () => {
    it('works as table body in modal: no padding, but scrollable', () => {
      const wrapper = createWrapper({ noPadding: true, isModal: true })
      expect(wrapper.classes()).not.toContain('p-6')
      expect(wrapper.classes()).toContain('flex-1')
      expect(wrapper.classes()).toContain('min-h-0')
      expect(wrapper.classes()).toContain('overflow-y-auto')
    })

    it('works as standard form card: padded, not scrollable', () => {
      const wrapper = createWrapper()
      expect(wrapper.classes()).toContain('p-6')
      expect(wrapper.classes()).toContain('flex-1')
      expect(wrapper.classes()).not.toContain('min-h-0')
      expect(wrapper.classes()).not.toContain('overflow-y-auto')
    })
  })
})
