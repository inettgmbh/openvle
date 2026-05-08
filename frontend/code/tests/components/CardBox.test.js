import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import CardBox from '@/components/CardBox.vue'

// Mock dependencies
vi.mock('@/stores/style.js', () => ({
  useStyleStore: () => ({
    darkMode: false,
    darkText: 'text-white',
    darkBg: 'bg-slate-900',
    darkBgModal: 'bg-slate-800',
    whiteBg: 'bg-white',
  }),
}))

vi.mock('@/components/CardBoxComponentBody.vue', () => ({
  default: {
    name: 'CardBoxComponentBody',
    template: '<div class="card-body"><slot /></div>',
    props: ['noPadding', 'isModal', 'hasSearch'],
  },
}))

vi.mock('@/components/CardBoxComponentFooter.vue', () => ({
  default: {
    name: 'CardBoxComponentFooter',
    template: '<div class="card-footer"><slot /></div>',
  },
}))

describe('CardBox', () => {
  const createWrapper = (props = {}, options = {}) => {
    return mount(CardBox, {
      props,
      global: {
        ...options.global,
      },
      slots: options.slots,
      ...options,
    })
  }

  describe('Rendering', () => {
    it('renders as div by default', () => {
      const wrapper = createWrapper()
      expect(wrapper.find('div').exists()).toBe(true)
    })

    it('renders as form when isForm is true', () => {
      const wrapper = createWrapper({ isForm: true })
      expect(wrapper.find('form').exists()).toBe(true)
    })

    it('renders slot content', () => {
      const wrapper = createWrapper(
        {},
        {
          slots: {
            default: '<p class="test-content">Test Content</p>',
          },
        },
      )
      expect(wrapper.find('.test-content').exists()).toBe(true)
    })

    it('renders CardBoxComponentBody by default', () => {
      const wrapper = createWrapper()
      expect(wrapper.find('.card-body').exists()).toBe(true)
    })

    it('renders footer slot when provided', () => {
      const wrapper = createWrapper(
        {},
        {
          slots: {
            footer: '<button>Submit</button>',
          },
        },
      )
      expect(wrapper.find('.card-footer').exists()).toBe(true)
    })

    it('does not render footer when no footer slot', () => {
      const wrapper = createWrapper()
      expect(wrapper.find('.card-footer').exists()).toBe(false)
    })
  })

  describe('Component Layout', () => {
    it('renders slot directly when hasComponentLayout is true', () => {
      const wrapper = createWrapper(
        { hasComponentLayout: true },
        {
          slots: {
            default: '<div class="custom-layout">Custom</div>',
          },
        },
      )
      expect(wrapper.find('.custom-layout').exists()).toBe(true)
      // Should not render CardBoxComponentBody when hasComponentLayout
    })
  })

  describe('Styling', () => {
    it('applies flex class', () => {
      const wrapper = createWrapper()
      expect(wrapper.find('.flex').exists()).toBe(true)
    })

    it('applies default rounded class', () => {
      const wrapper = createWrapper()
      expect(wrapper.classes()).toContain('rounded-2xl')
    })

    it('applies custom rounded class', () => {
      const wrapper = createWrapper({ rounded: 'rounded-lg' })
      expect(wrapper.classes()).toContain('rounded-lg')
    })

    it('applies default flex-col class', () => {
      const wrapper = createWrapper()
      expect(wrapper.classes()).toContain('flex-col')
    })

    it('applies custom flex class', () => {
      const wrapper = createWrapper({ flex: 'flex-row' })
      expect(wrapper.classes()).toContain('flex-row')
    })

    it('applies hover shadow when isHoverable is true', () => {
      const wrapper = createWrapper({ isHoverable: true })
      expect(wrapper.classes()).toContain('hover:shadow-lg')
      expect(wrapper.classes()).toContain('transition-shadow')
    })

    it('does not apply hover shadow by default', () => {
      const wrapper = createWrapper()
      expect(wrapper.classes()).not.toContain('hover:shadow-lg')
    })

    it('applies white background in light mode', () => {
      const wrapper = createWrapper()
      expect(wrapper.classes()).toContain('bg-white')
    })
  })

  describe('Table Mode', () => {
    it('passes noPadding to CardBoxComponentBody when hasTable is true', () => {
      const wrapper = createWrapper({ hasTable: true })
      const body = wrapper.findComponent({ name: 'CardBoxComponentBody' })
      expect(body.props('noPadding')).toBe(true)
    })

    it('passes noPadding false when hasTable is false', () => {
      const wrapper = createWrapper({ hasTable: false })
      const body = wrapper.findComponent({ name: 'CardBoxComponentBody' })
      expect(body.props('noPadding')).toBe(false)
    })
  })

  describe('Modal Mode', () => {
    it('passes isModal=true to CardBoxComponentBody when is-modal is set', () => {
      const wrapper = createWrapper({ isModal: true })
      const body = wrapper.findComponent({ name: 'CardBoxComponentBody' })
      expect(body.props('isModal')).toBe(true)
    })

    it('passes isModal=false by default', () => {
      const wrapper = createWrapper()
      const body = wrapper.findComponent({ name: 'CardBoxComponentBody' })
      expect(body.props('isModal')).toBe(false)
    })

    it('passes hasSearch=true to CardBoxComponentBody when has-search is set', () => {
      const wrapper = createWrapper({ isModal: true, hasSearch: true })
      const body = wrapper.findComponent({ name: 'CardBoxComponentBody' })
      expect(body.props('hasSearch')).toBe(true)
    })

    it('passes hasSearch=false by default', () => {
      const wrapper = createWrapper({ isModal: true })
      const body = wrapper.findComponent({ name: 'CardBoxComponentBody' })
      expect(body.props('hasSearch')).toBe(false)
    })
  })

  describe('Form Mode', () => {
    it('emits submit event when form is submitted', async () => {
      const wrapper = createWrapper({ isForm: true })
      await wrapper.find('form').trigger('submit')
      expect(wrapper.emitted('submit')).toBeTruthy()
    })

    it('passes submit event data', async () => {
      const wrapper = createWrapper({ isForm: true })
      await wrapper.find('form').trigger('submit')
      expect(wrapper.emitted('submit')[0]).toBeTruthy()
    })
  })

  describe('Props', () => {
    it('has correct default for rounded', () => {
      const { rounded } = CardBox.props
      expect(rounded.default).toBe('rounded-2xl')
    })

    it('has correct default for flex', () => {
      const { flex } = CardBox.props
      expect(flex.default).toBe('flex-col')
    })

    it('has boolean props with correct types', () => {
      const props = CardBox.props
      expect(props.hasComponentLayout).toBe(Boolean)
      expect(props.hasTable).toBe(Boolean)
      expect(props.hasSearch).toBe(Boolean)
      expect(props.isForm).toBe(Boolean)
      expect(props.isHoverable).toBe(Boolean)
      expect(props.isModal).toBe(Boolean)
    })
  })
})
