import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'

vi.mock('@/components/BaseButton.vue', () => ({
  default: {
    name: 'BaseButton',
    template:
      '<button :disabled="disabled" :href="href" :target="target"><slot /></button>',
    props: ['color', 'icon', 'disabled', 'href', 'target'],
  },
}))

vi.mock('@/components/BaseButtons.vue', () => ({
  default: {
    name: 'BaseButtons',
    template: '<div class="base-buttons"><slot /></div>',
    props: ['type', 'noWrap'],
  },
}))

vi.mock('@/components/BaseIcon.vue', () => ({
  default: {
    name: 'BaseIcon',
    template: '<span class="base-icon"></span>',
    props: ['path', 'size'],
  },
}))

vi.mock('@/components/IconRounded.vue', () => ({
  default: {
    name: 'IconRounded',
    template: '<span class="icon-rounded"></span>',
    props: ['icon', 'color', 'bg'],
  },
}))

vi.mock('@/stores/main', () => ({
  useMainStore: () => ({
    settings: {
      branding: {
        docs: {
          deepurl: 'https://docs.example.com',
        },
      },
    },
  }),
}))

describe('SectionTitleLineWithButton', () => {
  const createWrapper = (props = {}, options = {}) => {
    return mount(SectionTitleLineWithButton, {
      props: { title: 'Test Title', ...props },
      global: {
        directives: {
          tooltip: () => {},
        },
        ...options.global,
      },
      ...options,
    })
  }

  describe('Responsive Layout', () => {
    it('uses flex-col by default and flex-row on lg', () => {
      const wrapper = createWrapper()
      const section = wrapper.find('section')
      expect(section.classes()).toContain('flex')
      expect(section.classes()).toContain('flex-col')
      expect(section.classes()).toContain('lg:flex-row')
    })

    it('aligns items center on lg', () => {
      const wrapper = createWrapper()
      const section = wrapper.find('section')
      expect(section.classes()).toContain('lg:items-center')
      expect(section.classes()).toContain('lg:justify-between')
    })

    it('has gap between title and buttons', () => {
      const wrapper = createWrapper()
      const section = wrapper.find('section')
      expect(section.classes()).toContain('gap-4')
    })

    it('title row uses flex-1 only on lg', () => {
      const wrapper = createWrapper()
      const titleRow = wrapper.find('section > div')
      expect(titleRow.classes()).toContain('lg:flex-1')
      expect(titleRow.classes()).not.toContain('flex-1')
    })
  })

  describe('Slot Button Alignment', () => {
    it('aligns slot buttons to the end (right) on small screens', () => {
      const wrapper = createWrapper(
        {},
        {
          slots: { default: '<span>Action</span>' },
        },
      )
      const baseButtons = wrapper.findComponent({ name: 'BaseButtons' })
      expect(baseButtons.classes()).toContain('self-end')
    })

    it('resets alignment on lg screens', () => {
      const wrapper = createWrapper(
        {},
        {
          slots: { default: '<span>Action</span>' },
        },
      )
      const baseButtons = wrapper.findComponent({ name: 'BaseButtons' })
      expect(baseButtons.classes()).toContain('lg:self-auto')
    })

    it('prevents slot buttons from shrinking on lg', () => {
      const wrapper = createWrapper(
        {},
        {
          slots: { default: '<span>Action</span>' },
        },
      )
      const baseButtons = wrapper.findComponent({ name: 'BaseButtons' })
      expect(baseButtons.classes()).toContain('lg:flex-shrink-0')
    })
  })

  describe('Title Rendering', () => {
    it('renders the title text', () => {
      const wrapper = createWrapper({ title: 'My Page Title' })
      expect(wrapper.find('h1').text()).toBe('My Page Title')
    })

    it('uses text-3xl for main variant', () => {
      const wrapper = createWrapper({ main: true })
      expect(wrapper.find('h1').classes()).toContain('text-3xl')
    })

    it('uses text-2xl for non-main variant', () => {
      const wrapper = createWrapper({ main: false })
      expect(wrapper.find('h1').classes()).toContain('text-2xl')
    })

    it('renders objectModel subtitle when provided', () => {
      const wrapper = createWrapper({ objectModel: 'Veranstaltung' })
      expect(wrapper.find('p').text()).toBe('Veranstaltung')
    })

    it('does not render objectModel when not provided', () => {
      const wrapper = createWrapper()
      expect(wrapper.find('p').exists()).toBe(false)
    })
  })

  describe('Main Variant', () => {
    it('does not add pt-6 when main is true', () => {
      const wrapper = createWrapper({ main: true })
      expect(wrapper.find('section').classes()).not.toContain('pt-6')
    })

    it('adds pt-6 when main is false', () => {
      const wrapper = createWrapper({ main: false })
      expect(wrapper.find('section').classes()).toContain('pt-6')
    })
  })

  describe('Icon', () => {
    it('renders IconRounded when icon and main are provided', () => {
      const wrapper = createWrapper({ icon: 'mdi-home', main: true })
      expect(wrapper.findComponent({ name: 'IconRounded' }).exists()).toBe(true)
      expect(wrapper.findComponent({ name: 'BaseIcon' }).exists()).toBe(false)
    })

    it('renders BaseIcon when icon is provided but not main', () => {
      const wrapper = createWrapper({ icon: 'mdi-home', main: false })
      expect(wrapper.findComponent({ name: 'BaseIcon' }).exists()).toBe(true)
      expect(wrapper.findComponent({ name: 'IconRounded' }).exists()).toBe(
        false,
      )
    })

    it('renders no icon when icon is not provided', () => {
      const wrapper = createWrapper()
      expect(wrapper.findComponent({ name: 'BaseIcon' }).exists()).toBe(false)
      expect(wrapper.findComponent({ name: 'IconRounded' }).exists()).toBe(
        false,
      )
    })
  })

  describe('Docs Button', () => {
    it('renders docs button in title row when docsPath is provided', () => {
      const wrapper = createWrapper({ docsPath: '/docs/test/' })
      const titleRow = wrapper.find('section > div')
      const buttons = titleRow.findAllComponents({ name: 'BaseButton' })
      expect(buttons.length).toBeGreaterThanOrEqual(1)
      expect(buttons[0].attributes('href')).toBe(
        'https://docs.example.com/docs/test/',
      )
    })

    it('opens docs link in new tab', () => {
      const wrapper = createWrapper({ docsPath: '/docs/test/' })
      const titleRow = wrapper.find('section > div')
      const docsButton = titleRow.findComponent({ name: 'BaseButton' })
      expect(docsButton.attributes('target')).toBe('_blank')
    })

    it('does not render docs button when docsPath is not provided', () => {
      const wrapper = createWrapper()
      const titleRow = wrapper.find('section > div')
      expect(titleRow.findComponent({ name: 'BaseButton' }).exists()).toBe(
        false,
      )
    })

    it('places docs button inside title row, not in slot area', () => {
      const wrapper = createWrapper(
        { docsPath: '/docs/test/' },
        { slots: { default: '<span>Action</span>' } },
      )
      const titleRow = wrapper.find('section > div')
      expect(titleRow.findComponent({ name: 'BaseButton' }).exists()).toBe(true)
    })
  })

  describe('Reload Button', () => {
    it('renders reload button when reload function is provided', () => {
      const reload = vi.fn()
      const wrapper = createWrapper({ reload })
      const titleRow = wrapper.find('section > div')
      const buttons = titleRow.findAllComponents({ name: 'BaseButton' })
      expect(buttons.length).toBe(1)
    })

    it('calls reload function on click', async () => {
      const reload = vi.fn()
      const wrapper = createWrapper({ reload })
      const titleRow = wrapper.find('section > div')
      const reloadBtn = titleRow.findComponent({ name: 'BaseButton' })
      await reloadBtn.trigger('click')
      expect(reload).toHaveBeenCalled()
    })

    it('disables reload button when reloadDisabled is true', () => {
      const reload = vi.fn()
      const wrapper = createWrapper({ reload, reloadDisabled: true })
      const titleRow = wrapper.find('section > div')
      const reloadBtn = titleRow.findComponent({ name: 'BaseButton' })
      expect(reloadBtn.attributes('disabled')).toBeDefined()
    })

    it('does not render reload button when no reload function', () => {
      const wrapper = createWrapper()
      const titleRow = wrapper.find('section > div')
      expect(titleRow.findComponent({ name: 'BaseButton' }).exists()).toBe(
        false,
      )
    })
  })

  describe('Slot Content', () => {
    it('renders BaseButtons wrapper when slot content exists', () => {
      const wrapper = createWrapper(
        {},
        {
          slots: { default: '<span>Action Button</span>' },
        },
      )
      expect(wrapper.findComponent({ name: 'BaseButtons' }).exists()).toBe(true)
    })

    it('does not render BaseButtons when no slot content', () => {
      const wrapper = createWrapper()
      expect(wrapper.findComponent({ name: 'BaseButtons' }).exists()).toBe(
        false,
      )
    })

    it('renders slot content inside BaseButtons', () => {
      const wrapper = createWrapper(
        {},
        {
          slots: { default: '<span class="action">Delete</span>' },
        },
      )
      const baseButtons = wrapper.findComponent({ name: 'BaseButtons' })
      expect(baseButtons.find('.action').exists()).toBe(true)
    })
  })

  describe('Combined Props', () => {
    it('renders all elements together', () => {
      const wrapper = createWrapper(
        {
          title: 'Event Detail',
          icon: 'mdi-calendar',
          main: true,
          objectModel: 'Veranstaltung',
          docsPath: '/docs/events/',
          reload: vi.fn(),
        },
        { slots: { default: '<span>Actions</span>' } },
      )

      expect(wrapper.find('h1').text()).toBe('Event Detail')
      expect(wrapper.find('p').text()).toBe('Veranstaltung')
      expect(wrapper.findComponent({ name: 'IconRounded' }).exists()).toBe(true)
      expect(wrapper.findComponent({ name: 'BaseButtons' }).exists()).toBe(true)

      const titleRow = wrapper.find('section > div')
      const buttons = titleRow.findAllComponents({ name: 'BaseButton' })
      expect(buttons).toHaveLength(2)
    })
  })
})
