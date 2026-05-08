import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import EventWarningLoadingSpinner from '@/components/EventWarningLoadingSpinner.vue'

describe('EventWarningLoadingSpinner', () => {
  const createWrapper = () => {
    return mount(EventWarningLoadingSpinner)
  }

  describe('Rendering', () => {
    it('renders a container div', () => {
      const wrapper = createWrapper()
      expect(wrapper.find('div').exists()).toBe(true)
    })

    it('renders an SVG spinner', () => {
      const wrapper = createWrapper()
      expect(wrapper.find('svg').exists()).toBe(true)
    })

    it('renders loading text', () => {
      const wrapper = createWrapper()
      expect(wrapper.text()).toContain('Daten werden geladen...')
    })
  })

  describe('Styling', () => {
    it('has flex centering classes', () => {
      const wrapper = createWrapper()
      const container = wrapper.find('div')
      expect(container.classes()).toContain('flex')
      expect(container.classes()).toContain('justify-center')
      expect(container.classes()).toContain('items-center')
    })

    it('has minimum height', () => {
      const wrapper = createWrapper()
      const container = wrapper.find('div')
      expect(container.classes()).toContain('min-h-[300px]')
    })

    it('has animate-spin class on SVG', () => {
      const wrapper = createWrapper()
      const svg = wrapper.find('svg')
      expect(svg.classes()).toContain('animate-spin')
    })

    it('has text-warning color on SVG', () => {
      const wrapper = createWrapper()
      const svg = wrapper.find('svg')
      expect(svg.classes()).toContain('text-warning')
    })

    it('has text-warning color on loading text', () => {
      const wrapper = createWrapper()
      const text = wrapper.find('p')
      expect(text.classes()).toContain('text-warning')
    })
  })

  describe('SVG Structure', () => {
    it('has a circle element', () => {
      const wrapper = createWrapper()
      expect(wrapper.find('circle').exists()).toBe(true)
    })

    it('has a path element', () => {
      const wrapper = createWrapper()
      expect(wrapper.find('path').exists()).toBe(true)
    })

    it('circle has opacity-25 class', () => {
      const wrapper = createWrapper()
      const circle = wrapper.find('circle')
      expect(circle.classes()).toContain('opacity-25')
    })

    it('path has opacity-75 class', () => {
      const wrapper = createWrapper()
      const path = wrapper.find('path')
      expect(path.classes()).toContain('opacity-75')
    })
  })
})
