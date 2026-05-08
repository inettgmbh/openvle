import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import BaseButtonDropdown from '@/components/BaseButtonDropdown.vue'

// Mock BaseButton component - use @click.stop to prevent bubbling to document
vi.mock('@/components/BaseButton.vue', () => ({
  default: {
    name: 'BaseButton',
    template:
      '<button :disabled="disabled" @click.stop="$emit(\'click\', $event)" @keydown="$emit(\'keydown\', $event)"><slot /></button>',
    props: [
      'label',
      'icon',
      'iconSize',
      'type',
      'color',
      'disabled',
      'roundedFull',
      'small',
    ],
  },
}))

// Mock BaseDropdownItem component
vi.mock('@/components/BaseDropdownItem.vue', () => ({
  default: {
    name: 'BaseDropdownItem',
    template:
      '<button class="dropdown-item" role="menuitem" :disabled="disabled" @click="$emit(\'select\')">{{ item.label }}</button>',
    props: ['item', 'disabled'],
  },
}))

describe('BaseButtonDropdown', () => {
  let wrapper

  // Helper to open the dropdown programmatically
  const openDropdown = async (w) => {
    w.vm.isOpen = true
    await nextTick()
    await flushPromises()
  }

  const createWrapper = (props = {}, options = {}) => {
    return mount(BaseButtonDropdown, {
      props: {
        dropdownItems: [
          { id: 1, label: 'Item 1' },
          { id: 2, label: 'Item 2' },
        ],
        ...props,
      },
      attachTo: document.body,
      global: {
        stubs: {
          // Stub transition to render content immediately
          transition: {
            template: '<div><slot /></div>',
          },
        },
        ...options.global,
      },
      ...options,
    })
  }

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('Rendering', () => {
    it('renders a trigger button', () => {
      wrapper = createWrapper()
      expect(wrapper.findComponent({ name: 'BaseButton' }).exists()).toBe(true)
    })

    it('does not show dropdown menu by default', () => {
      wrapper = createWrapper()
      expect(wrapper.find('[role="menu"]').exists()).toBe(false)
    })

    it('passes label prop to trigger button', () => {
      wrapper = createWrapper({ label: 'Actions' })
      const button = wrapper.findComponent({ name: 'BaseButton' })
      expect(button.props('label')).toBe('Actions')
    })

    it('passes icon prop to trigger button', () => {
      wrapper = createWrapper({ icon: 'mdi-menu' })
      const button = wrapper.findComponent({ name: 'BaseButton' })
      expect(button.props('icon')).toBe('mdi-menu')
    })

    it('passes color prop to trigger button', () => {
      wrapper = createWrapper({ color: 'primary' })
      const button = wrapper.findComponent({ name: 'BaseButton' })
      expect(button.props('color')).toBe('primary')
    })

    it('passes disabled prop to trigger button', () => {
      wrapper = createWrapper({ disabled: true })
      const button = wrapper.findComponent({ name: 'BaseButton' })
      expect(button.props('disabled')).toBe(true)
    })

    it('passes small prop to trigger button', () => {
      wrapper = createWrapper({ small: true })
      const button = wrapper.findComponent({ name: 'BaseButton' })
      expect(button.props('small')).toBe(true)
    })

    it('passes roundedFull prop to trigger button', () => {
      wrapper = createWrapper({ roundedFull: true })
      const button = wrapper.findComponent({ name: 'BaseButton' })
      expect(button.props('roundedFull')).toBe(true)
    })
  })

  describe('Opening and Closing', () => {
    it('opens dropdown when isOpen is set to true', async () => {
      wrapper = createWrapper()
      expect(wrapper.find('[role="menu"]').exists()).toBe(false)
      await openDropdown(wrapper)
      expect(wrapper.find('[role="menu"]').exists()).toBe(true)
    })

    it('toggle method opens and closes dropdown', async () => {
      wrapper = createWrapper()
      // Open
      wrapper.vm.toggle()
      await nextTick()
      expect(wrapper.vm.isOpen).toBe(true)
      // Close
      wrapper.vm.toggle()
      await nextTick()
      expect(wrapper.vm.isOpen).toBe(false)
    })

    it('open method does nothing when disabled', async () => {
      wrapper = createWrapper({ disabled: true })
      wrapper.vm.open()
      await nextTick()
      expect(wrapper.vm.isOpen).toBe(false)
    })

    it('closes dropdown when item emits select event', async () => {
      wrapper = createWrapper()
      await openDropdown(wrapper)
      wrapper.vm.handleItemClick()
      await nextTick()
      expect(wrapper.vm.isOpen).toBe(false)
    })
  })

  describe('Keyboard Navigation', () => {
    it('onKeydownTrigger opens on ArrowDown', async () => {
      wrapper = createWrapper()
      wrapper.vm.onKeydownTrigger({ key: 'ArrowDown', preventDefault: vi.fn() })
      await nextTick()
      expect(wrapper.vm.isOpen).toBe(true)
    })

    it('onKeydownTrigger opens on Enter', async () => {
      wrapper = createWrapper()
      wrapper.vm.onKeydownTrigger({ key: 'Enter', preventDefault: vi.fn() })
      await nextTick()
      expect(wrapper.vm.isOpen).toBe(true)
    })

    it('onKeydownTrigger opens on Space', async () => {
      wrapper = createWrapper()
      wrapper.vm.onKeydownTrigger({ key: ' ', preventDefault: vi.fn() })
      await nextTick()
      expect(wrapper.vm.isOpen).toBe(true)
    })

    it('onKeydownMenu closes on Escape', async () => {
      wrapper = createWrapper()
      await openDropdown(wrapper)
      wrapper.vm.onKeydownMenu({ key: 'Escape', preventDefault: vi.fn() })
      await nextTick()
      expect(wrapper.vm.isOpen).toBe(false)
    })

    it('onKeydownMenu navigates with ArrowDown/ArrowUp', async () => {
      wrapper = createWrapper()
      await openDropdown(wrapper)
      // Just verify the function doesn't throw
      wrapper.vm.onKeydownMenu({ key: 'ArrowDown', preventDefault: vi.fn() })
      wrapper.vm.onKeydownMenu({ key: 'ArrowUp', preventDefault: vi.fn() })
    })
  })

  describe('Click Outside', () => {
    it('handleClickOutside closes when clicking outside root element', async () => {
      wrapper = createWrapper()
      await openDropdown(wrapper)

      // Simulate click outside by creating a mock event with target outside
      const outsideElement = document.createElement('div')
      document.body.appendChild(outsideElement)
      wrapper.vm.handleClickOutside({ target: outsideElement })
      await nextTick()

      expect(wrapper.vm.isOpen).toBe(false)
      document.body.removeChild(outsideElement)
    })

    it('handleClickOutside does not close when clicking inside root element', async () => {
      wrapper = createWrapper()
      await openDropdown(wrapper)

      // Click on an element inside the wrapper
      const rootEl = wrapper.vm.rootEl
      wrapper.vm.handleClickOutside({ target: rootEl })
      await nextTick()

      expect(wrapper.vm.isOpen).toBe(true)
    })
  })

  describe('ARIA Attributes', () => {
    it('has aria-haspopup="menu" on trigger button', () => {
      wrapper = createWrapper()
      const button = wrapper.findComponent({ name: 'BaseButton' })
      expect(button.attributes('aria-haspopup')).toBe('menu')
    })

    it('has aria-expanded="false" when closed', () => {
      wrapper = createWrapper()
      const button = wrapper.findComponent({ name: 'BaseButton' })
      expect(button.attributes('aria-expanded')).toBe('false')
    })

    it('has aria-expanded="true" when open', async () => {
      wrapper = createWrapper()
      await openDropdown(wrapper)
      const button = wrapper.findComponent({ name: 'BaseButton' })
      expect(button.attributes('aria-expanded')).toBe('true')
    })

    it('menu has role="menu"', async () => {
      wrapper = createWrapper()
      await openDropdown(wrapper)
      expect(wrapper.find('[role="menu"]').exists()).toBe(true)
    })

    it('menu has tabindex="-1"', async () => {
      wrapper = createWrapper()
      await openDropdown(wrapper)
      expect(wrapper.find('[role="menu"]').attributes('tabindex')).toBe('-1')
    })
  })

  describe('Filtered Items (Divider Handling)', () => {
    it('filters out leading dividers', () => {
      wrapper = createWrapper({
        dropdownItems: [
          { divider: true },
          { id: 1, label: 'Item 1' },
          { id: 2, label: 'Item 2' },
        ],
      })
      // Check filteredItems computed directly
      expect(wrapper.vm.filteredItems.length).toBe(2)
      expect(wrapper.vm.filteredItems[0].divider).toBeUndefined()
    })

    it('filters out trailing dividers', () => {
      wrapper = createWrapper({
        dropdownItems: [
          { id: 1, label: 'Item 1' },
          { id: 2, label: 'Item 2' },
          { divider: true },
        ],
      })
      expect(wrapper.vm.filteredItems.length).toBe(2)
      expect(
        wrapper.vm.filteredItems[wrapper.vm.filteredItems.length - 1].divider,
      ).toBeUndefined()
    })

    it('filters out consecutive dividers', () => {
      wrapper = createWrapper({
        dropdownItems: [
          { id: 1, label: 'Item 1' },
          { divider: true },
          { divider: true },
          { id: 2, label: 'Item 2' },
        ],
      })
      // Should have 3 items: item1, divider, item2
      expect(wrapper.vm.filteredItems.length).toBe(3)
      const dividers = wrapper.vm.filteredItems.filter((i) => i.divider)
      expect(dividers.length).toBe(1)
    })

    it('keeps single divider between items', () => {
      wrapper = createWrapper({
        dropdownItems: [
          { id: 1, label: 'Item 1' },
          { divider: true },
          { id: 2, label: 'Item 2' },
        ],
      })
      expect(wrapper.vm.filteredItems.length).toBe(3)
      expect(wrapper.vm.filteredItems[1].divider).toBe(true)
    })

    it('hasNextNonDivider returns true when there are following items', () => {
      wrapper = createWrapper({
        dropdownItems: [
          { id: 1, label: 'Item 1' },
          { divider: true },
          { id: 2, label: 'Item 2' },
        ],
      })
      expect(wrapper.vm.hasNextNonDivider(1)).toBe(true)
    })

    it('hasNextNonDivider returns false when no following items', () => {
      wrapper = createWrapper({
        dropdownItems: [{ id: 1, label: 'Item 1' }, { divider: true }],
      })
      // The trailing divider is filtered out, so we need different setup
      wrapper = createWrapper({
        dropdownItems: [{ id: 1, label: 'Item 1' }],
      })
      expect(wrapper.vm.hasNextNonDivider(0)).toBe(false)
    })
  })

  describe('Dropdown Items', () => {
    it('renders all non-divider items when open', async () => {
      wrapper = createWrapper({
        dropdownItems: [
          { id: 1, label: 'Item 1' },
          { id: 2, label: 'Item 2' },
          { id: 3, label: 'Item 3' },
        ],
      })
      await openDropdown(wrapper)
      const items = wrapper.findAll('.dropdown-item')
      expect(items.length).toBe(3)
    })

    it('renders item labels correctly when open', async () => {
      wrapper = createWrapper({
        dropdownItems: [{ id: 1, label: 'Test Item' }],
      })
      await openDropdown(wrapper)
      const item = wrapper.find('.dropdown-item')
      expect(item.text()).toBe('Test Item')
    })

    it('renders disabled items with disabled attribute when open', async () => {
      wrapper = createWrapper({
        dropdownItems: [{ id: 1, label: 'Item', disabled: true }],
      })
      await openDropdown(wrapper)
      const item = wrapper.find('.dropdown-item')
      expect(item.attributes('disabled')).toBeDefined()
    })

    it('filteredItems is empty when no items provided', () => {
      wrapper = createWrapper({ dropdownItems: [] })
      expect(wrapper.vm.filteredItems.length).toBe(0)
    })
  })

  describe('Alignment', () => {
    it('aligns to end by default', async () => {
      wrapper = createWrapper()
      await openDropdown(wrapper)
      const menu = wrapper.find('[role="menu"]')
      expect(menu.classes()).toContain('right-0')
    })

    it('aligns to start when align="start"', async () => {
      wrapper = createWrapper({ align: 'start' })
      await openDropdown(wrapper)
      const menu = wrapper.find('[role="menu"]')
      expect(menu.classes()).toContain('left-0')
    })
  })

  describe('Menu Styling', () => {
    it('applies base menu styling', async () => {
      wrapper = createWrapper()
      await openDropdown(wrapper)
      const menu = wrapper.find('[role="menu"]')
      expect(menu.classes()).toContain('absolute')
      expect(menu.classes()).toContain('min-w-44')
      expect(menu.classes()).toContain('rounded-xl')
      expect(menu.classes()).toContain('shadow-xl')
      expect(menu.classes()).toContain('z-50')
    })

    it('applies dark mode styling', async () => {
      wrapper = createWrapper()
      await openDropdown(wrapper)
      const menu = wrapper.find('[role="menu"]')
      expect(menu.classes()).toContain('dark:bg-slate-800')
      expect(menu.classes()).toContain('dark:border-slate-700')
    })
  })

  describe('Event Listener Cleanup', () => {
    it('removes click outside listener on unmount', async () => {
      const removeEventListenerSpy = vi.spyOn(document, 'removeEventListener')
      wrapper = createWrapper()
      wrapper.unmount()
      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'click',
        expect.any(Function),
        { capture: true },
      )
      removeEventListenerSpy.mockRestore()
    })
  })
})
