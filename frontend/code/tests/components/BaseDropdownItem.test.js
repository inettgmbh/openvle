import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import BaseDropdownItem from '@/components/BaseDropdownItem.vue'

// Mock BaseIcon component
vi.mock('@/components/BaseIcon.vue', () => ({
  default: {
    name: 'BaseIcon',
    template: '<span class="icon" data-testid="icon">{{ path }}</span>',
    props: ['path', 'w', 'h'],
  },
}))

describe('BaseDropdownItem', () => {
  const createWrapper = (props = {}, options = {}) => {
    return mount(BaseDropdownItem, {
      props: {
        item: { id: 1, label: 'Test Item' },
        ...props,
      },
      global: {
        directives: {
          tooltip: vi.fn(),
        },
        ...options.global,
      },
      ...options,
    })
  }

  describe('Rendering', () => {
    it('renders a button element', () => {
      const wrapper = createWrapper()
      expect(wrapper.find('button').exists()).toBe(true)
    })

    it('renders the item label', () => {
      const wrapper = createWrapper({
        item: { id: 1, label: 'Click Me' },
      })
      expect(wrapper.text()).toContain('Click Me')
    })

    it('renders icon when item has icon property', () => {
      const wrapper = createWrapper({
        item: { id: 1, label: 'With Icon', icon: 'mdi-test' },
      })
      expect(wrapper.find('[data-testid="icon"]').exists()).toBe(true)
    })

    it('does not render icon when item has no icon', () => {
      const wrapper = createWrapper({
        item: { id: 1, label: 'No Icon' },
      })
      expect(wrapper.find('[data-testid="icon"]').exists()).toBe(false)
    })

    it('has role="menuitem" attribute', () => {
      const wrapper = createWrapper()
      expect(wrapper.find('button').attributes('role')).toBe('menuitem')
    })

    it('has type="button" attribute', () => {
      const wrapper = createWrapper()
      expect(wrapper.find('button').attributes('type')).toBe('button')
    })
  })

  describe('Disabled State', () => {
    it('sets disabled attribute when disabled prop is true', () => {
      const wrapper = createWrapper({ disabled: true })
      expect(wrapper.find('button').attributes('disabled')).toBeDefined()
    })

    it('does not set disabled attribute when disabled prop is false', () => {
      const wrapper = createWrapper({ disabled: false })
      expect(wrapper.find('button').attributes('disabled')).toBeUndefined()
    })

    it('sets aria-disabled="true" when disabled', () => {
      const wrapper = createWrapper({ disabled: true })
      expect(wrapper.find('button').attributes('aria-disabled')).toBe('true')
    })

    it('sets aria-disabled="false" when not disabled', () => {
      const wrapper = createWrapper({ disabled: false })
      expect(wrapper.find('button').attributes('aria-disabled')).toBe('false')
    })
  })

  describe('Click Handling', () => {
    it('emits select event with item on click', async () => {
      const item = { id: 1, label: 'Test', action: 'test' }
      const wrapper = createWrapper({ item })
      await wrapper.find('button').trigger('click')
      expect(wrapper.emitted('select')).toBeTruthy()
      expect(wrapper.emitted('select')[0]).toEqual([item])
    })

    it('calls item onClick callback when clicked', async () => {
      const onClick = vi.fn()
      const wrapper = createWrapper({
        item: { id: 1, label: 'Test', onClick },
      })
      await wrapper.find('button').trigger('click')
      expect(onClick).toHaveBeenCalled()
    })

    it('does not emit select event when disabled', async () => {
      const wrapper = createWrapper({
        item: { id: 1, label: 'Test' },
        disabled: true,
      })
      await wrapper.find('button').trigger('click')
      expect(wrapper.emitted('select')).toBeFalsy()
    })

    it('does not call item onClick when disabled', async () => {
      const onClick = vi.fn()
      const wrapper = createWrapper({
        item: { id: 1, label: 'Test', onClick },
        disabled: true,
      })
      await wrapper.find('button').trigger('click')
      expect(onClick).not.toHaveBeenCalled()
    })

    it('prevents default when disabled', async () => {
      const wrapper = createWrapper({
        item: { id: 1, label: 'Test' },
        disabled: true,
      })
      const event = { preventDefault: vi.fn() }
      await wrapper.vm.onClick(event)
      expect(event.preventDefault).toHaveBeenCalled()
    })
  })

  describe('Tooltip Directive', () => {
    it('receives tooltip directive with item tooltip', () => {
      const tooltipDirective = vi.fn()
      mount(BaseDropdownItem, {
        props: {
          item: { id: 1, label: 'Test', tooltip: 'Helper text' },
        },
        global: {
          directives: {
            tooltip: tooltipDirective,
          },
        },
      })
      expect(tooltipDirective).toHaveBeenCalled()
      // The directive receives the tooltip value
      const call = tooltipDirective.mock.calls[0]
      expect(call[1].value).toBe('Helper text')
    })

    it('uses disabledTooltip when disabled', () => {
      const tooltipDirective = vi.fn()
      mount(BaseDropdownItem, {
        props: {
          item: {
            id: 1,
            label: 'Test',
            tooltip: 'Normal tooltip',
            disabledTooltip: 'Disabled tooltip',
          },
          disabled: true,
        },
        global: {
          directives: {
            tooltip: tooltipDirective,
          },
        },
      })
      expect(tooltipDirective).toHaveBeenCalled()
      const call = tooltipDirective.mock.calls[0]
      expect(call[1].value).toBe('Disabled tooltip')
    })

    it('uses normal tooltip when enabled even if disabledTooltip exists', () => {
      const tooltipDirective = vi.fn()
      mount(BaseDropdownItem, {
        props: {
          item: {
            id: 1,
            label: 'Test',
            tooltip: 'Normal tooltip',
            disabledTooltip: 'Disabled tooltip',
          },
          disabled: false,
        },
        global: {
          directives: {
            tooltip: tooltipDirective,
          },
        },
      })
      const call = tooltipDirective.mock.calls[0]
      expect(call[1].value).toBe('Normal tooltip')
    })

    it('uses normal tooltip when disabled but no disabledTooltip provided', () => {
      const tooltipDirective = vi.fn()
      mount(BaseDropdownItem, {
        props: {
          item: {
            id: 1,
            label: 'Test',
            tooltip: 'Normal tooltip',
          },
          disabled: true,
        },
        global: {
          directives: {
            tooltip: tooltipDirective,
          },
        },
      })
      const call = tooltipDirective.mock.calls[0]
      expect(call[1].value).toBe('Normal tooltip')
    })
  })

  describe('Styling', () => {
    it('applies base styling classes', () => {
      const wrapper = createWrapper()
      const button = wrapper.find('button')
      expect(button.classes()).toContain('w-full')
      expect(button.classes()).toContain('flex')
      expect(button.classes()).toContain('items-center')
    })

    it('applies hover styling classes', () => {
      const wrapper = createWrapper()
      const button = wrapper.find('button')
      expect(button.classes()).toContain('hover:bg-slate-100')
    })

    it('applies dark mode classes', () => {
      const wrapper = createWrapper()
      const button = wrapper.find('button')
      expect(button.classes()).toContain('dark:hover:bg-slate-700')
      expect(button.classes()).toContain('dark:text-slate-200')
    })

    it('applies disabled styling classes', () => {
      const wrapper = createWrapper()
      const button = wrapper.find('button')
      expect(button.classes()).toContain('disabled:opacity-50')
      expect(button.classes()).toContain('disabled:cursor-not-allowed')
    })

    it('applies truncate class to label span', () => {
      const wrapper = createWrapper({
        item: { id: 1, label: 'Very long label text' },
      })
      const span = wrapper.find('span.truncate')
      expect(span.exists()).toBe(true)
    })
  })

  describe('Icon Attributes', () => {
    it('passes correct size props to BaseIcon', () => {
      const wrapper = createWrapper({
        item: { id: 1, label: 'With Icon', icon: 'mdi-test' },
      })
      const icon = wrapper.findComponent({ name: 'BaseIcon' })
      expect(icon.props('w')).toBe('18')
      expect(icon.props('h')).toBe('18')
    })

    it('applies shrink-0 class to icon', () => {
      const wrapper = createWrapper({
        item: { id: 1, label: 'With Icon', icon: 'mdi-test' },
      })
      const icon = wrapper.findComponent({ name: 'BaseIcon' })
      expect(icon.classes()).toContain('shrink-0')
    })

    it('sets aria-hidden on icon', () => {
      const wrapper = createWrapper({
        item: { id: 1, label: 'With Icon', icon: 'mdi-test' },
      })
      const icon = wrapper.findComponent({ name: 'BaseIcon' })
      expect(icon.attributes('aria-hidden')).toBe('true')
    })

    it('sets focusable="false" on icon', () => {
      const wrapper = createWrapper({
        item: { id: 1, label: 'With Icon', icon: 'mdi-test' },
      })
      const icon = wrapper.findComponent({ name: 'BaseIcon' })
      expect(icon.attributes('focusable')).toBe('false')
    })
  })
})
