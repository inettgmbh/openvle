import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import PillTag from '@/components/PillTag.vue'

// Mock dependencies
vi.mock('@/colors.js', () => ({
  colorsBgLight: {
    green: 'bg-green-100 text-green-800',
    red: 'bg-red-100 text-red-800',
    blue: 'bg-blue-100 text-blue-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    gray: 'bg-gray-100 text-gray-800',
  },
  colorsOutline: {
    green: 'border-green-500 text-green-500',
    red: 'border-red-500 text-red-500',
    blue: 'border-blue-500 text-blue-500',
    yellow: 'border-yellow-500 text-yellow-500',
    gray: 'border-gray-500 text-gray-500',
  },
}))

vi.mock('@/components/PillTagPlain.vue', () => ({
  default: {
    name: 'PillTagPlain',
    template:
      '<span class="pill-tag-plain" @click="$emit(\'click\')"><slot />{{ label }}</span>',
    props: ['icon', 'label', 'small'],
    emits: ['click'],
  },
}))

describe('PillTag', () => {
  const createWrapper = (props = {}) => {
    return mount(PillTag, {
      props: { color: 'green', ...props },
    })
  }

  describe('Rendering', () => {
    it('renders component', () => {
      const wrapper = createWrapper()
      expect(wrapper.find('.pill-tag-plain').exists()).toBe(true)
    })

    it('renders with label', () => {
      const wrapper = createWrapper({ label: 'Test Label' })
      expect(wrapper.text()).toContain('Test Label')
    })

    it('applies border and rounded-full classes', () => {
      const wrapper = createWrapper()
      expect(wrapper.find('.border').exists()).toBe(true)
      expect(wrapper.find('.rounded-full').exists()).toBe(true)
    })
  })

  describe('Sizing', () => {
    it('applies normal padding by default', () => {
      const wrapper = createWrapper()
      expect(wrapper.classes()).toContain('py-1.5')
      expect(wrapper.classes()).toContain('px-4')
    })

    it('applies small padding when small prop is true', () => {
      const wrapper = createWrapper({ small: true })
      expect(wrapper.classes()).toContain('py-1')
      expect(wrapper.classes()).toContain('px-3')
    })
  })

  describe('Colors', () => {
    it('applies background color by default', () => {
      const wrapper = createWrapper({ color: 'green' })
      expect(wrapper.classes().some((c) => c.includes('bg-green'))).toBe(true)
    })

    it('applies outline color when outline prop is true', () => {
      const wrapper = createWrapper({ color: 'green', outline: true })
      expect(wrapper.classes().some((c) => c.includes('border-green'))).toBe(
        true,
      )
    })

    it('supports different colors', () => {
      const colors = ['green', 'red', 'blue', 'yellow', 'gray']
      colors.forEach((color) => {
        const wrapper = createWrapper({ color })
        expect(wrapper.exists()).toBe(true)
      })
    })
  })

  describe('Disabled State', () => {
    it('applies cursor-pointer when not disabled', () => {
      const wrapper = createWrapper({ disabled: false })
      expect(wrapper.classes()).toContain('cursor-pointer')
    })

    it('does not apply cursor-pointer when disabled', () => {
      const wrapper = createWrapper({ disabled: true })
      expect(wrapper.classes()).not.toContain('cursor-pointer')
    })

    it('sets aria-disabled attribute when disabled', () => {
      const wrapper = createWrapper({ disabled: true })
      expect(wrapper.find('.pill-tag-plain').attributes('aria-disabled')).toBe(
        'true',
      )
    })
  })

  describe('Click Handler', () => {
    it('calls handleClick when clicked and not disabled', async () => {
      const handleClick = vi.fn()
      const wrapper = createWrapper({ handleClick, disabled: false })

      await wrapper.find('.pill-tag-plain').trigger('click')
      expect(handleClick).toHaveBeenCalled()
    })

    it('does not call handleClick when clicked and disabled', async () => {
      const handleClick = vi.fn()
      const wrapper = createWrapper({ handleClick, disabled: true })

      await wrapper.find('.pill-tag-plain').trigger('click')
      expect(handleClick).not.toHaveBeenCalled()
    })
  })

  describe('Icon', () => {
    it('passes icon prop to PillTagPlain', () => {
      const wrapper = createWrapper({ icon: 'mdi-check' })
      const pillTagPlain = wrapper.findComponent({ name: 'PillTagPlain' })
      expect(pillTagPlain.props('icon')).toBe('mdi-check')
    })

    it('renders without icon when not provided', () => {
      const wrapper = createWrapper()
      const pillTagPlain = wrapper.findComponent({ name: 'PillTagPlain' })
      expect(pillTagPlain.props('icon')).toBeNull()
    })
  })
})
