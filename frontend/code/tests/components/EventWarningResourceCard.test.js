import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import EventWarningResourceCard from '@/components/EventWarningResourceCard.vue'

// Mock BaseIcon
vi.mock('@/components/BaseIcon.vue', () => ({
  default: {
    name: 'BaseIcon',
    template: '<span class="icon" :class="$attrs.class">{{ path }}</span>',
    props: ['path', 'size'],
  },
}))

describe('EventWarningResourceCard', () => {
  const createWrapper = (props = {}) => {
    return mount(EventWarningResourceCard, {
      props: {
        icon: 'mdi-test-icon',
        value: 42,
        label: 'Test Label',
        ...props,
      },
    })
  }

  describe('Rendering', () => {
    it('renders the value', () => {
      const wrapper = createWrapper({ value: 123 })
      expect(wrapper.text()).toContain('123')
    })

    it('renders the label', () => {
      const wrapper = createWrapper({ label: 'Participants' })
      expect(wrapper.text()).toContain('Participants')
    })

    it('renders the icon', () => {
      const wrapper = createWrapper({ icon: 'mdi-account' })
      expect(wrapper.find('.icon').exists()).toBe(true)
    })

    it('renders subtitle when provided', () => {
      const wrapper = createWrapper({ subtitle: '10 Students, 5 Teachers' })
      expect(wrapper.text()).toContain('10 Students, 5 Teachers')
    })

    it('does not render subtitle when not provided', () => {
      const wrapper = createWrapper()
      const subtitleElements = wrapper.findAll('div').filter((el) => {
        return (
          el.classes().includes('text-xs') && !el.text().includes('Test Label')
        )
      })
      // Only label div should exist with text-xs
      expect(subtitleElements.length).toBe(0)
    })

    it('accepts string values', () => {
      const wrapper = createWrapper({ value: 'N/A' })
      expect(wrapper.text()).toContain('N/A')
    })
  })

  describe('Color variants', () => {
    it('applies blue color classes by default', () => {
      const wrapper = createWrapper()
      const container = wrapper.find('div')
      expect(container.classes().some((c) => c.includes('blue'))).toBe(true)
    })

    it('applies emerald color classes', () => {
      const wrapper = createWrapper({ color: 'emerald' })
      const container = wrapper.find('div')
      expect(container.classes().some((c) => c.includes('emerald'))).toBe(true)
    })

    it('applies amber color classes', () => {
      const wrapper = createWrapper({ color: 'amber' })
      const container = wrapper.find('div')
      expect(container.classes().some((c) => c.includes('amber'))).toBe(true)
    })

    it('applies red color classes', () => {
      const wrapper = createWrapper({ color: 'red' })
      const container = wrapper.find('div')
      expect(container.classes().some((c) => c.includes('red'))).toBe(true)
    })

    it('applies orange color classes', () => {
      const wrapper = createWrapper({ color: 'orange' })
      const container = wrapper.find('div')
      expect(container.classes().some((c) => c.includes('orange'))).toBe(true)
    })
  })

  describe('Styling', () => {
    it('has rounded-lg class on container', () => {
      const wrapper = createWrapper()
      const container = wrapper.find('div')
      expect(container.classes()).toContain('rounded-lg')
    })

    it('has p-4 padding class', () => {
      const wrapper = createWrapper()
      const container = wrapper.find('div')
      expect(container.classes()).toContain('p-4')
    })

    it('has border class', () => {
      const wrapper = createWrapper()
      const container = wrapper.find('div')
      expect(container.classes()).toContain('border')
    })

    it('value has text-2xl and font-bold classes', () => {
      const wrapper = createWrapper()
      const valueDiv = wrapper.findAll('div').find((el) => el.text() === '42')
      expect(valueDiv.classes()).toContain('text-2xl')
      expect(valueDiv.classes()).toContain('font-bold')
    })

    it('label has text-xs class', () => {
      const wrapper = createWrapper({ label: 'My Label' })
      const labelDiv = wrapper
        .findAll('div')
        .find((el) => el.text() === 'My Label')
      expect(labelDiv.classes()).toContain('text-xs')
    })
  })

  describe('Props validation', () => {
    it('requires icon prop', () => {
      const iconProp = EventWarningResourceCard.props.icon
      expect(iconProp.required).toBe(true)
      expect(iconProp.type).toBe(String)
    })

    it('requires value prop', () => {
      const valueProp = EventWarningResourceCard.props.value
      expect(valueProp.required).toBe(true)
    })

    it('requires label prop', () => {
      const labelProp = EventWarningResourceCard.props.label
      expect(labelProp.required).toBe(true)
      expect(labelProp.type).toBe(String)
    })

    it('has optional subtitle prop with null default', () => {
      const subtitleProp = EventWarningResourceCard.props.subtitle
      expect(subtitleProp.default).toBe(null)
    })

    it('has color prop with blue default', () => {
      const colorProp = EventWarningResourceCard.props.color
      expect(colorProp.default).toBe('blue')
    })

    it('validates color prop values', () => {
      const colorProp = EventWarningResourceCard.props.color
      expect(colorProp.validator('blue')).toBe(true)
      expect(colorProp.validator('emerald')).toBe(true)
      expect(colorProp.validator('amber')).toBe(true)
      expect(colorProp.validator('red')).toBe(true)
      expect(colorProp.validator('orange')).toBe(true)
      expect(colorProp.validator('invalid')).toBe(false)
    })
  })

  describe('Dark mode', () => {
    it('includes dark mode background classes', () => {
      const wrapper = createWrapper({ color: 'blue' })
      const container = wrapper.find('div')
      const classes = container.classes().join(' ')
      expect(classes).toContain('dark:bg-blue-900/20')
    })

    it('includes dark mode border classes', () => {
      const wrapper = createWrapper({ color: 'blue' })
      const container = wrapper.find('div')
      const classes = container.classes().join(' ')
      expect(classes).toContain('dark:border-blue-800')
    })
  })

  describe('Layout', () => {
    it('has flex container with gap', () => {
      const wrapper = createWrapper()
      const flexContainer = wrapper.find('.flex.items-center.gap-3')
      expect(flexContainer.exists()).toBe(true)
    })

    it('icon container has p-2 and rounded-lg', () => {
      const wrapper = createWrapper()
      const iconContainer = wrapper.find('.p-2.rounded-lg')
      expect(iconContainer.exists()).toBe(true)
    })
  })
})
