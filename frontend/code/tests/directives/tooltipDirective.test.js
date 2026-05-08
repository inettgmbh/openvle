/* eslint-disable vue/one-component-per-file */
import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, nextTick } from 'vue'

import tooltipDirective, {
  calculatePosition,
  createArrowElement,
  createTooltipElement,
  getPosition,
  parseBindingValue,
} from '@/directives/tooltipDirective'

// Shared test component - defined once to satisfy vue/one-component-per-file
const TestComponent = defineComponent({
  directives: { tooltip: tooltipDirective },
  props: {
    tooltipValue: {
      type: [String, Object],
      default: null,
    },
  },
  template: '<div v-tooltip="tooltipValue">Hover me</div>',
})

const TestComponentBottom = defineComponent({
  directives: { tooltip: tooltipDirective },
  template: '<div v-tooltip.bottom="\'Bottom tooltip\'">Hover</div>',
})

const TestComponentOverride = defineComponent({
  directives: { tooltip: tooltipDirective },
  template:
    "<div v-tooltip.bottom=\"{ text: 'Test', position: 'left' }\">Hover</div>",
})

describe('tooltipDirective', () => {
  describe('getPosition', () => {
    it('returns position from value when valid', () => {
      expect(getPosition({}, 'top')).toBe('top')
      expect(getPosition({}, 'bottom')).toBe('bottom')
      expect(getPosition({}, 'left')).toBe('left')
      expect(getPosition({}, 'right')).toBe('right')
    })

    it('returns position from modifiers when value not provided', () => {
      expect(getPosition({ top: true })).toBe('top')
      expect(getPosition({ bottom: true })).toBe('bottom')
      expect(getPosition({ left: true })).toBe('left')
      expect(getPosition({ right: true })).toBe('right')
    })

    it('returns default position when no valid position provided', () => {
      expect(getPosition({})).toBe('top')
      expect(getPosition({}, undefined)).toBe('top')
      expect(getPosition({}, 'invalid')).toBe('top')
    })

    it('value position takes priority over modifiers', () => {
      expect(getPosition({ bottom: true }, 'left')).toBe('left')
    })

    it('handles empty modifiers object', () => {
      expect(getPosition(undefined, undefined)).toBe('top')
    })
  })

  describe('parseBindingValue', () => {
    it('parses string value', () => {
      const result = parseBindingValue('Hello')
      expect(result).toEqual({ text: 'Hello' })
    })

    it('parses object value with all properties', () => {
      const input = {
        text: 'Tooltip text',
        position: 'bottom',
        arrow: true,
        style: 'custom-class',
      }
      const result = parseBindingValue(input)
      expect(result).toEqual(input)
    })

    it('parses object value with partial properties', () => {
      const result = parseBindingValue({ text: 'Only text' })
      expect(result).toEqual({
        text: 'Only text',
        position: undefined,
        arrow: undefined,
        style: undefined,
      })
    })

    it('handles null value', () => {
      const result = parseBindingValue(null)
      expect(result.text).toBe('')
    })

    it('handles undefined value', () => {
      const result = parseBindingValue(undefined)
      expect(result.text).toBe('')
    })

    it('handles empty object', () => {
      const result = parseBindingValue({})
      expect(result.text).toBe('')
    })
  })

  describe('calculatePosition', () => {
    const elRect = {
      top: 100,
      bottom: 140,
      left: 200,
      right: 300,
      width: 100,
      height: 40,
    }

    const tooltipRect = {
      width: 80,
      height: 30,
    }

    beforeEach(() => {
      Object.defineProperty(window, 'scrollX', { value: 0, writable: true })
      Object.defineProperty(window, 'scrollY', { value: 0, writable: true })
    })

    it('calculates top position correctly', () => {
      const result = calculatePosition(elRect, tooltipRect, 'top', 10)

      expect(result.top).toBe(100 - 30 - 10) // elRect.top - tooltipRect.height - space
      expect(result.left).toBe(200 + (100 - 80) / 2) // centered horizontally
    })

    it('calculates bottom position correctly', () => {
      const result = calculatePosition(elRect, tooltipRect, 'bottom', 10)

      expect(result.top).toBe(140 + 10) // elRect.bottom + space
      expect(result.left).toBe(200 + (100 - 80) / 2) // centered horizontally
    })

    it('calculates left position correctly', () => {
      const result = calculatePosition(elRect, tooltipRect, 'left', 10)

      expect(result.top).toBe(100 + (40 - 30) / 2) // centered vertically
      expect(result.left).toBe(200 - 80 - 10) // elRect.left - tooltipRect.width - space
    })

    it('calculates right position correctly', () => {
      const result = calculatePosition(elRect, tooltipRect, 'right', 10)

      expect(result.top).toBe(100 + (40 - 30) / 2) // centered vertically
      expect(result.left).toBe(300 + 10) // elRect.right + space
    })

    it('returns default position for invalid position', () => {
      const result = calculatePosition(elRect, tooltipRect, 'invalid', 10)
      expect(result).toEqual({ top: 0, left: 0 })
    })

    it('accounts for scroll position', () => {
      Object.defineProperty(window, 'scrollX', { value: 50 })
      Object.defineProperty(window, 'scrollY', { value: 100 })

      const result = calculatePosition(elRect, tooltipRect, 'top', 10)

      expect(result.top).toBe(100 + 100 - 30 - 10) // includes scrollY
      expect(result.left).toBe(200 + 50 + (100 - 80) / 2) // includes scrollX
    })
  })

  describe('createTooltipElement', () => {
    it('creates element with text content', () => {
      const tooltip = createTooltipElement('Hello World')

      expect(tooltip.tagName).toBe('DIV')
      expect(tooltip.textContent).toBe('Hello World')
    })

    it('applies base classes', () => {
      const tooltip = createTooltipElement('Test')

      expect(tooltip.className).toContain('opacity-0')
      expect(tooltip.className).toContain('absolute')
      expect(tooltip.className).toContain('z-50')
    })

    it('applies default style classes when no custom style', () => {
      const tooltip = createTooltipElement('Test')

      expect(tooltip.className).toContain('bg-black')
      expect(tooltip.className).toContain('text-white')
      expect(tooltip.className).toContain('rounded-lg')
    })

    it('applies custom style classes when provided', () => {
      const tooltip = createTooltipElement('Test', 'custom-class bg-red-500')

      expect(tooltip.className).toContain('custom-class')
      expect(tooltip.className).toContain('bg-red-500')
      expect(tooltip.className).not.toContain('bg-black')
    })

    it('sets role attribute to tooltip', () => {
      const tooltip = createTooltipElement('Test')

      expect(tooltip.getAttribute('role')).toBe('tooltip')
    })
  })

  describe('createArrowElement', () => {
    it('creates empty div element for boolean arrow config', () => {
      const arrow = createArrowElement(true)

      expect(arrow.tagName).toBe('DIV')
      expect(arrow.className).toBe('')
    })

    it('applies custom class for string arrow config', () => {
      const arrow = createArrowElement('custom-arrow-class')

      expect(arrow.className).toBe('custom-arrow-class')
    })
  })

  describe('Directive Integration', () => {
    let wrapper

    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
      if (wrapper) {
        wrapper.unmount()
      }
      // Clean up any tooltips left in the document
      document.querySelectorAll('[role="tooltip"]').forEach((el) => el.remove())
    })

    it('does not create tooltip for undefined value', () => {
      wrapper = mount(TestComponent, {
        props: { tooltipValue: undefined },
      })

      expect(document.querySelector('[role="tooltip"]')).toBeNull()
    })

    it('does not create tooltip for null value', () => {
      wrapper = mount(TestComponent, {
        props: { tooltipValue: null },
      })

      expect(document.querySelector('[role="tooltip"]')).toBeNull()
    })

    it('does not create tooltip for empty text', () => {
      wrapper = mount(TestComponent, {
        props: { tooltipValue: { text: '' } },
      })

      expect(document.querySelector('[role="tooltip"]')).toBeNull()
    })

    it('shows tooltip on mouseenter', async () => {
      wrapper = mount(TestComponent, {
        props: { tooltipValue: 'Test tooltip' },
      })

      await wrapper.find('div').trigger('mouseenter')
      vi.advanceTimersByTime(150)

      const tooltip = document.querySelector('[role="tooltip"]')
      expect(tooltip).not.toBeNull()
      expect(tooltip.textContent).toBe('Test tooltip')
    })

    it('hides tooltip on mouseleave', async () => {
      wrapper = mount(TestComponent, {
        props: { tooltipValue: 'Test tooltip' },
      })

      await wrapper.find('div').trigger('mouseenter')
      vi.advanceTimersByTime(150)
      expect(document.querySelector('[role="tooltip"]')).not.toBeNull()

      await wrapper.find('div').trigger('mouseleave')
      vi.advanceTimersByTime(250)

      expect(document.querySelector('[role="tooltip"]')).toBeNull()
    })

    it('creates arrow element when arrow is true', async () => {
      wrapper = mount(TestComponent, {
        props: { tooltipValue: { text: 'With arrow', arrow: true } },
      })

      await wrapper.find('div').trigger('mouseenter')
      vi.advanceTimersByTime(150)

      const tooltip = document.querySelector('[role="tooltip"]')
      expect(tooltip.children.length).toBe(1) // Arrow element
    })

    it('does not create arrow element when arrow is false', async () => {
      wrapper = mount(TestComponent, {
        props: { tooltipValue: { text: 'No arrow', arrow: false } },
      })

      await wrapper.find('div').trigger('mouseenter')
      vi.advanceTimersByTime(150)

      const tooltip = document.querySelector('[role="tooltip"]')
      expect(tooltip.children.length).toBe(0)
    })

    it('applies custom style classes', async () => {
      wrapper = mount(TestComponent, {
        props: { tooltipValue: { text: 'Custom', style: 'bg-blue-500' } },
      })

      await wrapper.find('div').trigger('mouseenter')
      vi.advanceTimersByTime(150)

      const tooltip = document.querySelector('[role="tooltip"]')
      expect(tooltip.className).toContain('bg-blue-500')
    })

    it('cleans up event listeners on unmount', async () => {
      wrapper = mount(TestComponent, {
        props: { tooltipValue: 'Test' },
      })

      const el = wrapper.find('div').element
      const removeEventListenerSpy = vi.spyOn(el, 'removeEventListener')

      wrapper.unmount()

      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'mouseenter',
        expect.any(Function),
      )
      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'mouseleave',
        expect.any(Function),
      )
    })

    it('updates tooltip when value changes', async () => {
      wrapper = mount(TestComponent, {
        props: { tooltipValue: 'Initial' },
      })

      await wrapper.find('div').trigger('mouseenter')
      vi.advanceTimersByTime(150)
      let tooltip = document.querySelector('[role="tooltip"]')
      expect(tooltip.textContent).toBe('Initial')

      await wrapper.find('div').trigger('mouseleave')
      vi.advanceTimersByTime(250)

      await wrapper.setProps({ tooltipValue: 'Updated' })
      await nextTick()

      await wrapper.find('div').trigger('mouseenter')
      vi.advanceTimersByTime(150)

      tooltip = document.querySelector('[role="tooltip"]')
      expect(tooltip.textContent).toBe('Updated')
    })
  })

  describe('Directive with Modifiers', () => {
    let wrapper

    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
      if (wrapper) {
        wrapper.unmount()
      }
      document.querySelectorAll('[role="tooltip"]').forEach((el) => el.remove())
    })

    it('uses position from modifier', async () => {
      wrapper = mount(TestComponentBottom)
      await wrapper.find('div').trigger('mouseenter')
      vi.advanceTimersByTime(150)

      const tooltip = document.querySelector('[role="tooltip"]')
      expect(tooltip).not.toBeNull()
    })

    it('value position overrides modifier', async () => {
      wrapper = mount(TestComponentOverride)
      await wrapper.find('div').trigger('mouseenter')
      vi.advanceTimersByTime(150)

      const tooltip = document.querySelector('[role="tooltip"]')
      expect(tooltip).not.toBeNull()
    })
  })
})
