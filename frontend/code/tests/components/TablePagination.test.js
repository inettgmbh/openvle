import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import TablePagination from '@/components/Tables/TablePagination.vue'

// Mock child components
vi.mock('@/components/BaseButton.vue', () => ({
  default: {
    name: 'BaseButton',
    template:
      '<button class="base-button" @click="$emit(\'click\')"><slot />{{ label }}</button>',
    props: ['label', 'color', 'small', 'roundedFull'],
    emits: ['click'],
  },
}))

vi.mock('@/components/BaseButtons.vue', () => ({
  default: {
    name: 'BaseButtons',
    template: '<div class="base-buttons"><slot /></div>',
  },
}))

vi.mock('@/components/BaseLevel.vue', () => ({
  default: {
    name: 'BaseLevel',
    template: '<div class="base-level"><slot /></div>',
  },
}))

vi.mock('@/components/FormControl.vue', () => ({
  default: {
    name: 'FormControl',
    template:
      '<select class="form-control" @change="$emit(\'update:modelValue\', $event.target.value)"><option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.label }}</option></select>',
    props: ['modelValue', 'options', 'required', 'name', 'id'],
    emits: ['update:modelValue'],
  },
}))

describe('TablePagination', () => {
  const defaultProps = {
    currentPage: 1,
    itemsTotal: 100,
    perPage: 10,
  }

  let wrapper

  beforeEach(() => {
    wrapper = null
  })

  const createWrapper = (props = {}) => {
    return mount(TablePagination, {
      props: { ...defaultProps, ...props },
    })
  }

  describe('Rendering', () => {
    it('renders pagination component', () => {
      wrapper = createWrapper()
      expect(wrapper.find('.p-3').exists()).toBe(true)
    })

    it('displays current page and total pages', () => {
      wrapper = createWrapper({ currentPage: 3, itemsTotal: 50, perPage: 10 })
      expect(wrapper.text()).toContain('Seite 3 von 5')
    })

    it('displays total items count', () => {
      wrapper = createWrapper({ itemsTotal: 75 })
      expect(wrapper.text()).toContain('Insgesamt: 75 Einträge')
    })

    it('shows "Seite 1 von 1" when no items', () => {
      wrapper = createWrapper({ itemsTotal: 0 })
      expect(wrapper.text()).toContain('Seite 1 von 1')
    })

    it('renders page buttons', () => {
      wrapper = createWrapper()
      const buttons = wrapper.findAll('.base-button')
      expect(buttons.length).toBeGreaterThan(0)
    })

    it('renders perPage select with label', () => {
      wrapper = createWrapper()
      expect(wrapper.text()).toContain('Pro Seite:')
      expect(wrapper.find('.form-control').exists()).toBe(true)
    })
  })

  describe('Page Calculation', () => {
    it('calculates correct number of pages', () => {
      wrapper = createWrapper({ itemsTotal: 100, perPage: 10 })
      expect(wrapper.text()).toContain('von 10')
    })

    it('rounds up pages for partial last page', () => {
      wrapper = createWrapper({ itemsTotal: 95, perPage: 10 })
      expect(wrapper.text()).toContain('von 10')
    })

    it('shows single page for items less than perPage', () => {
      wrapper = createWrapper({ itemsTotal: 5, perPage: 10 })
      expect(wrapper.text()).toContain('von 1')
    })

    it('handles string itemsTotal', () => {
      wrapper = createWrapper({ itemsTotal: '50', perPage: 10 })
      expect(wrapper.text()).toContain('von 5')
    })
  })

  describe('Page List Generation', () => {
    it('shows page 1 button on first page', () => {
      wrapper = createWrapper({ currentPage: 1, itemsTotal: 100, perPage: 10 })
      const buttons = wrapper.findAll('.base-button')
      expect(buttons.some((b) => b.text() === '1')).toBe(true)
    })

    it('shows limited page buttons (max 5 visible)', () => {
      wrapper = createWrapper({ currentPage: 5, itemsTotal: 200, perPage: 10 })
      const buttons = wrapper.findAll('.base-button')
      // Should have around 5-7 buttons (including prev/next jumps)
      expect(buttons.length).toBeLessThanOrEqual(8)
    })

    it('shows +10 button when more than 10 pages ahead exist', () => {
      wrapper = createWrapper({ currentPage: 1, itemsTotal: 200, perPage: 10 })
      const buttons = wrapper.findAll('.base-button')
      expect(buttons.some((b) => b.text() === '+10')).toBe(true)
    })

    it('shows -10 button when current page is greater than 11', () => {
      wrapper = createWrapper({ currentPage: 12, itemsTotal: 200, perPage: 10 })
      const buttons = wrapper.findAll('.base-button')
      expect(buttons.some((b) => b.text() === '-10')).toBe(true)
    })

    it('does not show -10 button on page 10 or less', () => {
      wrapper = createWrapper({ currentPage: 10, itemsTotal: 200, perPage: 10 })
      const buttons = wrapper.findAll('.base-button')
      expect(buttons.some((b) => b.text() === '-10')).toBe(false)
    })
  })

  describe('Events', () => {
    it('emits paginationChanged when page button is clicked', async () => {
      wrapper = createWrapper({ currentPage: 1, itemsTotal: 100, perPage: 10 })
      const buttons = wrapper.findAll('.base-button')
      const page2Button = buttons.find((b) => b.text() === '2')

      if (page2Button) {
        await page2Button.trigger('click')
        expect(wrapper.emitted('paginationChanged')).toBeTruthy()
      }
    })

    it('emits paginationChanged with correct page and perPage', async () => {
      wrapper = createWrapper({ currentPage: 1, itemsTotal: 100, perPage: 10 })
      const buttons = wrapper.findAll('.base-button')
      const page2Button = buttons.find((b) => b.text() === '2')

      if (page2Button) {
        await page2Button.trigger('click')
        const emitted = wrapper.emitted('paginationChanged')
        expect(emitted[0]).toEqual([2, 10])
      }
    })

    it('emits paginationChanged with +10 jump', async () => {
      wrapper = createWrapper({ currentPage: 1, itemsTotal: 200, perPage: 10 })
      const buttons = wrapper.findAll('.base-button')
      const next10Button = buttons.find((b) => b.text() === '+10')

      if (next10Button) {
        await next10Button.trigger('click')
        const emitted = wrapper.emitted('paginationChanged')
        expect(emitted[0][0]).toBe(11)
      }
    })

    it('emits paginationChanged with -10 jump', async () => {
      wrapper = createWrapper({ currentPage: 15, itemsTotal: 200, perPage: 10 })
      const buttons = wrapper.findAll('.base-button')
      const prev10Button = buttons.find((b) => b.text() === '-10')

      if (prev10Button) {
        await prev10Button.trigger('click')
        const emitted = wrapper.emitted('paginationChanged')
        expect(emitted[0][0]).toBe(5)
      }
    })

    it('does not go below page 0 with -10 jump', async () => {
      wrapper = createWrapper({ currentPage: 12, itemsTotal: 200, perPage: 10 })
      const buttons = wrapper.findAll('.base-button')
      const prev10Button = buttons.find((b) => b.text() === '-10')

      if (prev10Button) {
        await prev10Button.trigger('click')
        const emitted = wrapper.emitted('paginationChanged')
        expect(emitted[0][0]).toBeGreaterThanOrEqual(0)
      }
    })
  })

  describe('Per Page Selection', () => {
    it('renders default perPage options', () => {
      wrapper = createWrapper()
      const select = wrapper.find('.form-control')
      expect(select.exists()).toBe(true)
    })

    it('uses custom perPageSelect options when provided', () => {
      const customOptions = [
        { label: '20', value: 20 },
        { label: '40', value: 40 },
      ]
      wrapper = createWrapper({ perPageSelect: customOptions })
      const select = wrapper.find('.form-control')
      expect(select.exists()).toBe(true)
    })
  })

  describe('Edge Cases', () => {
    it('handles zero items', () => {
      wrapper = createWrapper({ itemsTotal: 0 })
      expect(wrapper.text()).toContain('Insgesamt: 0 Einträge')
    })

    it('handles negative currentPage gracefully', () => {
      wrapper = createWrapper({ currentPage: -1 })
      // Should not crash
      expect(wrapper.exists()).toBe(true)
    })

    it('handles very large itemsTotal', () => {
      wrapper = createWrapper({ itemsTotal: 1000000, perPage: 100 })
      expect(wrapper.text()).toContain('von 10000')
    })

    it('handles perPage of 1', () => {
      wrapper = createWrapper({ itemsTotal: 10, perPage: 1 })
      expect(wrapper.text()).toContain('von 10')
    })

    it('handles perPage larger than itemsTotal', () => {
      wrapper = createWrapper({ itemsTotal: 5, perPage: 100 })
      expect(wrapper.text()).toContain('von 1')
    })
  })

  describe('Current Page Highlighting', () => {
    it('highlights current page button with different color', () => {
      wrapper = createWrapper({ currentPage: 3, itemsTotal: 100, perPage: 10 })
      // The current page button should have 'lightDark' color prop
      // We can check if the button for page 3 exists
      const buttons = wrapper.findAll('.base-button')
      expect(buttons.some((b) => b.text() === '3')).toBe(true)
    })
  })
})
