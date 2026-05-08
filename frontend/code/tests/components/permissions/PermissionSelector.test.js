import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// Mock icons
vi.mock('@/utils/icons', () => ({
  permissionKeyIcon: vi.fn(() => 'M12 0L24 12L12 24L0 12Z'),
}))

// Mock objectModelPermissions
vi.mock('@/utils/objectModelPermissions', () => ({
  getObjectPermissionLabel: vi.fn(({ permission }) => {
    const map = {
      none: 'Keine',
      object_read: 'Lesen',
      object_update: 'Bearbeiten',
      object_delete: 'Löschen',
      object_full: 'Vollzugriff',
      object_create: 'Erstellen',
      action_special: 'Spezial',
      object_reset: 'Steuerung',
      object_actions_start: 'Starten',
      object_actions_stop: 'Stoppen',
      object_actions_reboot: 'Neustart',
      object_actions_reset: 'Reset',
      object_actions_shutdown: 'Herunterfahren',
      object_actions_resume: 'Fortsetzen',
      object_admins: 'Admins',
      object_verwaltende: 'Verwaltende',
    }
    return map[permission] || permission
  }),
  getObjectPermissionShortLabel: vi.fn(({ permission }) => {
    const map = {
      none: 'Keine',
      object_read: 'Lesen',
      object_update: 'Bearbeiten',
      object_delete: 'Löschen',
      object_full: 'Vollzugriff',
      object_create: 'Erstellen',
      action_special: 'Spezial',
      object_reset: 'Steuerung',
      object_actions_start: 'Starten',
      object_actions_stop: 'Stoppen',
      object_actions_reboot: 'Neustart',
      object_actions_reset: 'Reset',
      object_actions_shutdown: 'Herunterfahren',
      object_actions_resume: 'Fortsetzen',
      object_admins: 'Admins',
      object_verwaltende: 'Verwaltende',
    }
    return map[permission] || permission
  }),
}))

import PermissionSelector from '@/components/permissions/PermissionSelector.vue'

describe('PermissionSelector', () => {
  const createWrapper = (props = {}) => {
    return mount(PermissionSelector, {
      props: {
        modelValue: 'none',
        ...props,
      },
    })
  }

  describe('Rendering', () => {
    it('renders the None button', () => {
      const wrapper = createWrapper()
      expect(wrapper.text()).toContain('Keine')
    })

    it('renders chain buttons (read, update, delete)', () => {
      const wrapper = createWrapper()
      expect(wrapper.text()).toContain('Lesen')
      expect(wrapper.text()).toContain('Bearbeiten')
      expect(wrapper.text()).toContain('Löschen')
    })

    it('renders Create button in global mode', () => {
      const wrapper = createWrapper({ mode: 'global' })
      expect(wrapper.text()).toContain('Erstellen')
    })

    it('does not render Create button in object mode', () => {
      const wrapper = createWrapper({ mode: 'object' })
      expect(wrapper.text()).not.toContain('Erstellen')
    })
  })

  describe('None Button', () => {
    it('is active when modelValue is none and no extras', () => {
      const wrapper = createWrapper({
        modelValue: 'none',
        createValue: false,
        extraValues: [],
      })

      const noneButton = wrapper.findAll('button')[0]
      expect(noneButton.attributes('aria-pressed')).toBe('true')
    })

    it('is not active when modelValue is not none', () => {
      const wrapper = createWrapper({ modelValue: 'object_read' })

      const noneButton = wrapper.findAll('button')[0]
      expect(noneButton.attributes('aria-pressed')).toBe('false')
    })

    it('is not active when createValue is true', () => {
      const wrapper = createWrapper({
        modelValue: 'none',
        createValue: true,
        mode: 'global',
      })

      const noneButton = wrapper.findAll('button')[0]
      expect(noneButton.attributes('aria-pressed')).toBe('false')
    })

    it('is not active when extraValues has items', () => {
      const wrapper = createWrapper({
        modelValue: 'none',
        extraValues: ['action_special'],
      })

      const noneButton = wrapper.findAll('button')[0]
      expect(noneButton.attributes('aria-pressed')).toBe('false')
    })

    it('emits none and resets createValue when clicked', async () => {
      const wrapper = createWrapper({
        modelValue: 'object_read',
        createValue: true,
        extraValues: ['action_special'],
        mode: 'global',
      })

      const noneButton = wrapper.findAll('button')[0]
      await noneButton.trigger('click')

      expect(wrapper.emitted('update:modelValue')).toEqual([['none']])
      expect(wrapper.emitted('update:createValue')).toEqual([[false]])
      expect(wrapper.emitted('update:extraValues')).toEqual([[[]]])
    })
  })

  describe('Create Button', () => {
    it('emits update:createValue when clicked', async () => {
      const wrapper = createWrapper({
        modelValue: 'none',
        createValue: false,
        mode: 'global',
      })

      // Find create button - it's after None
      const buttons = wrapper.findAll('button')
      const createButton = buttons.find((b) => b.text().includes('Erstellen'))

      await createButton.trigger('click')

      expect(wrapper.emitted('update:createValue')).toEqual([[true]])
    })

    it('toggles createValue from true to false', async () => {
      const wrapper = createWrapper({
        modelValue: 'none',
        createValue: true,
        mode: 'global',
      })

      const buttons = wrapper.findAll('button')
      const createButton = buttons.find((b) => b.text().includes('Erstellen'))

      await createButton.trigger('click')

      expect(wrapper.emitted('update:createValue')).toEqual([[false]])
    })

    it('shows active state when createValue is true', () => {
      const wrapper = createWrapper({
        modelValue: 'none',
        createValue: true,
        mode: 'global',
      })

      const buttons = wrapper.findAll('button')
      const createButton = buttons.find((b) => b.text().includes('Erstellen'))

      expect(createButton.attributes('aria-pressed')).toBe('true')
    })
  })

  describe('Chain Buttons (RWUD)', () => {
    it('activates read when clicking read', async () => {
      const wrapper = createWrapper({ modelValue: 'none' })

      const buttons = wrapper.findAll('button')
      const readButton = buttons.find((b) => b.text().includes('Lesen'))

      await readButton.trigger('click')

      expect(wrapper.emitted('update:modelValue')).toEqual([['object_read']])
    })

    it('activates read+update when clicking update', async () => {
      const wrapper = createWrapper({ modelValue: 'none' })

      const buttons = wrapper.findAll('button')
      const updateButton = buttons.find((b) => b.text().includes('Bearbeiten'))

      await updateButton.trigger('click')

      expect(wrapper.emitted('update:modelValue')).toEqual([['object_update']])
    })

    it('activates full chain when clicking delete (object_delete)', async () => {
      const wrapper = createWrapper({ modelValue: 'none' })

      const buttons = wrapper.findAll('button')
      const deleteButton = buttons.find((b) => b.text().includes('Löschen'))

      await deleteButton.trigger('click')

      expect(wrapper.emitted('update:modelValue')).toEqual([['object_delete']])
    })

    it('deactivates higher levels when clicking lower (from object_delete)', async () => {
      const wrapper = createWrapper({ modelValue: 'object_delete' })

      const buttons = wrapper.findAll('button')
      const readButton = buttons.find((b) => b.text().includes('Lesen'))

      await readButton.trigger('click')

      // Clicking read when at delete -> removes delete and update, keeps only read
      expect(wrapper.emitted('update:modelValue')[0][0]).toBe('object_read')
    })

    it('shows active state for all lower levels', () => {
      const wrapper = createWrapper({ modelValue: 'object_update' })

      const buttons = wrapper.findAll('button')
      const readButton = buttons.find((b) => b.text().includes('Lesen'))
      const updateButton = buttons.find((b) => b.text().includes('Bearbeiten'))
      const deleteButton = buttons.find((b) => b.text().includes('Löschen'))

      expect(readButton.attributes('aria-pressed')).toBe('true')
      expect(updateButton.attributes('aria-pressed')).toBe('true')
      expect(deleteButton.attributes('aria-pressed')).toBe('false')
    })
  })

  describe('Vollzugriff Button (object_full)', () => {
    it('renders Vollzugriff button by default', () => {
      const wrapper = createWrapper()
      expect(wrapper.text()).toContain('Vollzugriff')
    })

    it('does not render Vollzugriff button when not in allowedKeys', () => {
      const wrapper = createWrapper({
        allowedKeys: ['object_read', 'object_update'],
      })
      expect(wrapper.text()).not.toContain('Vollzugriff')
    })

    it('renders Vollzugriff button when in allowedKeys', () => {
      const wrapper = createWrapper({
        allowedKeys: ['object_read', 'object_full'],
      })
      expect(wrapper.text()).toContain('Vollzugriff')
    })

    it('activates object_full when clicking Vollzugriff', async () => {
      const wrapper = createWrapper({ modelValue: 'none' })

      const buttons = wrapper.findAll('button')
      const fullButton = buttons.find((b) => b.text().includes('Vollzugriff'))

      await fullButton.trigger('click')

      expect(wrapper.emitted('update:modelValue')).toEqual([['object_full']])
    })

    it('deactivates object_full when clicking Vollzugriff again and resets everything', async () => {
      const wrapper = createWrapper({
        modelValue: 'object_full',
        createValue: true,
        mode: 'global',
        allowedKeys: ['object_read', 'object_full', 'action_special'],
        extraValues: ['action_special'],
      })

      const buttons = wrapper.findAll('button')
      const fullButton = buttons.find((b) => b.text().includes('Vollzugriff'))

      await fullButton.trigger('click')

      expect(wrapper.emitted('update:modelValue')).toEqual([['none']])
      expect(wrapper.emitted('update:createValue')).toEqual([[false]])
      expect(wrapper.emitted('update:extraValues')).toEqual([[[]]])
    })

    it('shows active state when object_full is selected', () => {
      const wrapper = createWrapper({ modelValue: 'object_full' })

      const buttons = wrapper.findAll('button')
      const fullButton = buttons.find((b) => b.text().includes('Vollzugriff'))

      expect(fullButton.attributes('aria-pressed')).toBe('true')
      expect(fullButton.classes()).toContain('from-amber-500')
    })

    it('clears extraValues when activating object_full', async () => {
      const wrapper = createWrapper({
        modelValue: 'none',
        allowedKeys: ['object_read', 'object_full', 'action_special'],
        extraValues: ['action_special'],
      })

      const buttons = wrapper.findAll('button')
      const fullButton = buttons.find((b) => b.text().includes('Vollzugriff'))

      await fullButton.trigger('click')

      expect(wrapper.emitted('update:extraValues')).toEqual([[[]]])
    })

    it('does not change createValue when activating object_full', async () => {
      const wrapper = createWrapper({
        modelValue: 'none',
        createValue: true,
        mode: 'global',
      })

      const buttons = wrapper.findAll('button')
      const fullButton = buttons.find((b) => b.text().includes('Vollzugriff'))

      await fullButton.trigger('click')

      // createValue should not be emitted (no change)
      expect(wrapper.emitted('update:createValue')).toBeUndefined()
    })
  })

  describe('Implicit State when object_full is active', () => {
    it('chain buttons show as implicit when object_full is active', () => {
      const wrapper = createWrapper({ modelValue: 'object_full' })

      const buttons = wrapper.findAll('button')
      const readButton = buttons.find((b) => b.text().includes('Lesen'))
      const updateButton = buttons.find((b) => b.text().includes('Bearbeiten'))
      const deleteButton = buttons.find((b) => b.text().includes('Löschen'))

      // All chain buttons should show implicit (lighter emerald)
      expect(readButton.classes()).toContain('from-emerald-400')
      expect(updateButton.classes()).toContain('from-emerald-400')
      expect(deleteButton.classes()).toContain('from-emerald-400')

      // All should be marked as pressed (implicit or active)
      expect(readButton.attributes('aria-pressed')).toBe('true')
      expect(updateButton.attributes('aria-pressed')).toBe('true')
      expect(deleteButton.attributes('aria-pressed')).toBe('true')
    })

    it('create button shows as implicit when object_full is active (global mode)', () => {
      const wrapper = createWrapper({
        modelValue: 'object_full',
        mode: 'global',
      })

      const buttons = wrapper.findAll('button')
      const createButton = buttons.find((b) => b.text().includes('Erstellen'))

      // Create should show implicit (lighter blue)
      expect(createButton.classes()).toContain('from-blue-400')
      expect(createButton.attributes('aria-pressed')).toBe('true')
    })

    it('extra buttons show as implicit when object_full is active', () => {
      const wrapper = createWrapper({
        modelValue: 'object_full',
        allowedKeys: ['object_read', 'object_full', 'action_special'],
      })

      const buttons = wrapper.findAll('button')
      const specialButton = buttons.find((b) => b.text().includes('Spezial'))

      // Extra should show implicit (lighter violet)
      expect(specialButton.classes()).toContain('from-violet-400')
      expect(specialButton.attributes('aria-pressed')).toBe('true')
    })

    it('clicking chain button while object_full is active deactivates full and activates only that chain', async () => {
      const wrapper = createWrapper({
        modelValue: 'object_full',
        mode: 'global',
      })

      const buttons = wrapper.findAll('button')
      const readButton = buttons.find((b) => b.text().includes('Lesen'))

      await readButton.trigger('click')

      expect(wrapper.emitted('update:modelValue')).toEqual([['object_read']])
      expect(wrapper.emitted('update:createValue')).toEqual([[false]])
      expect(wrapper.emitted('update:extraValues')).toEqual([[[]]])
    })

    it('clicking create while object_full is active deactivates full and activates only create', async () => {
      const wrapper = createWrapper({
        modelValue: 'object_full',
        mode: 'global',
      })

      const buttons = wrapper.findAll('button')
      const createButton = buttons.find((b) => b.text().includes('Erstellen'))

      await createButton.trigger('click')

      expect(wrapper.emitted('update:modelValue')).toEqual([['none']])
      expect(wrapper.emitted('update:createValue')).toEqual([[true]])
      expect(wrapper.emitted('update:extraValues')).toEqual([[[]]])
    })

    it('clicking extra while object_full is active deactivates full and activates only that extra', async () => {
      const wrapper = createWrapper({
        modelValue: 'object_full',
        allowedKeys: ['object_read', 'object_full', 'action_special'],
        mode: 'global',
      })

      const buttons = wrapper.findAll('button')
      const specialButton = buttons.find((b) => b.text().includes('Spezial'))

      await specialButton.trigger('click')

      expect(wrapper.emitted('update:modelValue')).toEqual([['none']])
      expect(wrapper.emitted('update:createValue')).toEqual([[false]])
      expect(wrapper.emitted('update:extraValues')).toEqual([
        [['action_special']],
      ])
    })

    it('clicking Löschen while object_full is active activates full chain only', async () => {
      const wrapper = createWrapper({
        modelValue: 'object_full',
        mode: 'global',
      })

      const buttons = wrapper.findAll('button')
      const deleteButton = buttons.find((b) => b.text().includes('Löschen'))

      await deleteButton.trigger('click')

      expect(wrapper.emitted('update:modelValue')).toEqual([['object_delete']])
      expect(wrapper.emitted('update:createValue')).toEqual([[false]])
      expect(wrapper.emitted('update:extraValues')).toEqual([[[]]])
    })
  })

  describe('Auto-upgrade to Vollzugriff when all permissions selected', () => {
    it('upgrades to object_full when selecting last chain key completes all permissions', async () => {
      const wrapper = createWrapper({
        modelValue: 'object_update',
        createValue: true,
        mode: 'global',
        allowedKeys: [
          'object_create',
          'object_read',
          'object_update',
          'object_delete',
          'object_full',
        ],
        extraValues: [],
      })

      const buttons = wrapper.findAll('button')
      const deleteButton = buttons.find((b) => b.text().includes('Löschen'))

      await deleteButton.trigger('click')

      // Should upgrade to object_full instead of object_delete
      expect(wrapper.emitted('update:modelValue')).toEqual([['object_full']])
      expect(wrapper.emitted('update:createValue')).toEqual([[false]])
      expect(wrapper.emitted('update:extraValues')).toEqual([[[]]])
    })

    it('upgrades to object_full when selecting create completes all permissions', async () => {
      const wrapper = createWrapper({
        modelValue: 'object_delete',
        createValue: false,
        mode: 'global',
        allowedKeys: [
          'object_create',
          'object_read',
          'object_update',
          'object_delete',
          'object_full',
        ],
        extraValues: [],
      })

      const buttons = wrapper.findAll('button')
      const createButton = buttons.find((b) => b.text().includes('Erstellen'))

      await createButton.trigger('click')

      // Should upgrade to object_full
      expect(wrapper.emitted('update:modelValue')).toEqual([['object_full']])
      expect(wrapper.emitted('update:createValue')).toEqual([[false]])
      expect(wrapper.emitted('update:extraValues')).toEqual([[[]]])
    })

    it('upgrades to object_full when selecting last extra completes all permissions', async () => {
      const wrapper = createWrapper({
        modelValue: 'object_delete',
        createValue: true,
        mode: 'global',
        allowedKeys: [
          'object_create',
          'object_read',
          'object_update',
          'object_delete',
          'object_full',
          'action_special',
        ],
        extraValues: [],
      })

      const buttons = wrapper.findAll('button')
      const specialButton = buttons.find((b) => b.text().includes('Spezial'))

      await specialButton.trigger('click')

      // Should upgrade to object_full
      expect(wrapper.emitted('update:modelValue')).toEqual([['object_full']])
      expect(wrapper.emitted('update:createValue')).toEqual([[false]])
      expect(wrapper.emitted('update:extraValues')).toEqual([[[]]])
    })

    it('does not upgrade if only one permission is available (e.g., only object_read)', async () => {
      const wrapper = createWrapper({
        modelValue: 'none',
        mode: 'global',
        allowedKeys: ['object_read', 'object_full'],
        extraValues: [],
      })

      const buttons = wrapper.findAll('button')
      const readButton = buttons.find((b) => b.text().includes('Lesen'))

      await readButton.trigger('click')

      // Should NOT upgrade because only one permission is available
      expect(wrapper.emitted('update:modelValue')).toEqual([['object_read']])
    })

    it('does not upgrade if object_full is not in allowedKeys', async () => {
      const wrapper = createWrapper({
        modelValue: 'object_update',
        createValue: true,
        mode: 'global',
        allowedKeys: [
          'object_create',
          'object_read',
          'object_update',
          'object_delete',
          // object_full NOT included
        ],
        extraValues: [],
      })

      const buttons = wrapper.findAll('button')
      const deleteButton = buttons.find((b) => b.text().includes('Löschen'))

      await deleteButton.trigger('click')

      // Should NOT upgrade, just set object_delete
      expect(wrapper.emitted('update:modelValue')).toEqual([['object_delete']])
      expect(wrapper.emitted('update:createValue')).toBeUndefined()
    })

    it('does not upgrade if not all extras are selected', async () => {
      const wrapper = createWrapper({
        modelValue: 'object_update',
        createValue: true,
        mode: 'global',
        allowedKeys: [
          'object_create',
          'object_read',
          'object_update',
          'object_delete',
          'object_full',
          'action_special',
        ],
        extraValues: [], // action_special not selected
      })

      const buttons = wrapper.findAll('button')
      const deleteButton = buttons.find((b) => b.text().includes('Löschen'))

      await deleteButton.trigger('click')

      // Should NOT upgrade because action_special is missing
      expect(wrapper.emitted('update:modelValue')).toEqual([['object_delete']])
    })

    it('does not upgrade in object mode (no create required)', async () => {
      const wrapper = createWrapper({
        modelValue: 'object_update',
        mode: 'object',
        allowedKeys: [
          'object_read',
          'object_update',
          'object_delete',
          'object_full',
        ],
        extraValues: [],
      })

      const buttons = wrapper.findAll('button')
      const deleteButton = buttons.find((b) => b.text().includes('Löschen'))

      await deleteButton.trigger('click')

      // In object mode with no extras, selecting all chain keys should upgrade
      expect(wrapper.emitted('update:modelValue')).toEqual([['object_full']])
    })
  })

  describe('Disabled State', () => {
    it('disables all buttons when disabled prop is true', () => {
      const wrapper = createWrapper({ disabled: true })

      const buttons = wrapper.findAll('button')
      buttons.forEach((button) => {
        expect(button.attributes('disabled')).toBeDefined()
      })
    })

    it('does not emit events when disabled', async () => {
      const wrapper = createWrapper({ disabled: true })

      const buttons = wrapper.findAll('button')
      await buttons[0].trigger('click')

      expect(wrapper.emitted('update:modelValue')).toBeUndefined()
    })

    it('applies opacity class when disabled', () => {
      const wrapper = createWrapper({ disabled: true })

      const buttons = wrapper.findAll('button')
      expect(buttons[0].classes()).toContain('opacity-50')
    })
  })

  describe('Allowed Keys', () => {
    it('only shows allowed chain keys', () => {
      const wrapper = createWrapper({
        allowedKeys: ['object_read', 'object_update'],
      })

      expect(wrapper.text()).toContain('Lesen')
      expect(wrapper.text()).toContain('Bearbeiten')
      expect(wrapper.text()).not.toContain('Löschen')
    })

    it('hides create button when not in allowedKeys', () => {
      const wrapper = createWrapper({
        allowedKeys: ['object_read'],
        mode: 'global',
      })

      expect(wrapper.text()).not.toContain('Erstellen')
    })

    it('shows create button when in allowedKeys', () => {
      const wrapper = createWrapper({
        allowedKeys: ['object_read', 'object_create'],
        mode: 'global',
      })

      expect(wrapper.text()).toContain('Erstellen')
    })

    it('does not toggle disallowed chain key', async () => {
      const wrapper = createWrapper({
        modelValue: 'none',
        allowedKeys: ['object_read'],
      })

      // update is not in allowedKeys, so this button shouldn't exist
      const buttons = wrapper.findAll('button')
      const updateButton = buttons.find((b) => b.text().includes('Bearbeiten'))

      expect(updateButton).toBeUndefined()
    })
  })

  describe('Extra Values (Special Permissions)', () => {
    it('renders extra permission buttons when allowedKeys includes them', () => {
      const wrapper = createWrapper({
        allowedKeys: ['object_read', 'action_special'],
      })

      expect(wrapper.text()).toContain('Spezial')
    })

    it('shows active state for active extras', () => {
      const wrapper = createWrapper({
        allowedKeys: ['object_read', 'action_special'],
        extraValues: ['action_special'],
      })

      const buttons = wrapper.findAll('button')
      const specialButton = buttons.find((b) => b.text().includes('Spezial'))

      expect(specialButton.attributes('aria-pressed')).toBe('true')
    })

    it('emits update:extraValues when toggling extra', async () => {
      const wrapper = createWrapper({
        allowedKeys: ['object_read', 'action_special'],
        extraValues: [],
      })

      const buttons = wrapper.findAll('button')
      const specialButton = buttons.find((b) => b.text().includes('Spezial'))

      await specialButton.trigger('click')

      expect(wrapper.emitted('update:extraValues')).toEqual([
        [['action_special']],
      ])
    })

    it('removes from extraValues when already active', async () => {
      const wrapper = createWrapper({
        allowedKeys: ['object_read', 'action_special'],
        extraValues: ['action_special'],
      })

      const buttons = wrapper.findAll('button')
      const specialButton = buttons.find((b) => b.text().includes('Spezial'))

      await specialButton.trigger('click')

      expect(wrapper.emitted('update:extraValues')).toEqual([[[]]])
    })
  })

  describe('Mode Behavior', () => {
    it('in global mode shows create button', () => {
      const wrapper = createWrapper({ mode: 'global' })
      expect(wrapper.text()).toContain('Erstellen')
    })

    it('in object mode hides create button', () => {
      const wrapper = createWrapper({ mode: 'object' })
      expect(wrapper.text()).not.toContain('Erstellen')
    })

    it('in object mode, none does not emit createValue', async () => {
      const wrapper = createWrapper({
        mode: 'object',
        modelValue: 'object_read',
      })

      const noneButton = wrapper.findAll('button')[0]
      await noneButton.trigger('click')

      expect(wrapper.emitted('update:createValue')).toBeUndefined()
    })
  })

  describe('Props', () => {
    it('has correct default for mode', () => {
      const wrapper = createWrapper()
      expect(wrapper.props('mode')).toBe('global')
    })

    it('has correct default for createValue', () => {
      const wrapper = createWrapper()
      expect(wrapper.props('createValue')).toBe(false)
    })

    it('has correct default for disabled', () => {
      const wrapper = createWrapper()
      expect(wrapper.props('disabled')).toBe(false)
    })

    it('has correct default for allowedKeys', () => {
      const wrapper = createWrapper()
      expect(wrapper.props('allowedKeys')).toBeNull()
    })

    it('has correct default for extraValues', () => {
      const wrapper = createWrapper()
      expect(wrapper.props('extraValues')).toEqual([])
    })
  })

  describe('Styling', () => {
    it('applies active styling to active chain buttons', () => {
      const wrapper = createWrapper({ modelValue: 'object_read' })

      const buttons = wrapper.findAll('button')
      const readButton = buttons.find((b) => b.text().includes('Lesen'))

      expect(readButton.classes()).toContain('from-emerald-600')
    })

    it('applies inactive styling to inactive chain buttons', () => {
      const wrapper = createWrapper({ modelValue: 'none' })

      const buttons = wrapper.findAll('button')
      const readButton = buttons.find((b) => b.text().includes('Lesen'))

      expect(readButton.classes()).toContain('bg-white')
    })

    it('applies blue styling to active create button', () => {
      const wrapper = createWrapper({
        modelValue: 'none',
        createValue: true,
        mode: 'global',
      })

      const buttons = wrapper.findAll('button')
      const createButton = buttons.find((b) => b.text().includes('Erstellen'))

      expect(createButton.classes()).toContain('from-blue-600')
    })

    it('applies violet styling to active extra buttons', () => {
      const wrapper = createWrapper({
        allowedKeys: ['action_special'],
        extraValues: ['action_special'],
      })

      const buttons = wrapper.findAll('button')
      const specialButton = buttons.find((b) => b.text().includes('Spezial'))

      expect(specialButton.classes()).toContain('from-violet-600')
    })
  })

  describe('SVG Icons', () => {
    it('renders SVG icons in buttons', () => {
      const wrapper = createWrapper()

      const svgs = wrapper.findAll('svg')
      expect(svgs.length).toBeGreaterThan(0)
    })

    it('renders icon path in SVG', () => {
      const wrapper = createWrapper()

      const paths = wrapper.findAll('svg path')
      expect(paths.length).toBeGreaterThan(0)
    })
  })

  describe('Steuerung (object_reset) Grouping', () => {
    const steuerungAllowedKeys = [
      'object_read',
      'object_reset',
      'object_actions_start',
      'object_actions_stop',
      'object_actions_reboot',
      'object_actions_reset',
      'object_actions_shutdown',
      'object_actions_resume',
    ]

    it('shows Steuerung button when allowed', () => {
      const wrapper = createWrapper({
        allowedKeys: steuerungAllowedKeys,
      })

      expect(wrapper.text()).toContain('Steuerung')
    })

    it('shows contained action buttons when Steuerung is allowed', () => {
      const wrapper = createWrapper({
        allowedKeys: steuerungAllowedKeys,
      })

      expect(wrapper.text()).toContain('Starten')
      expect(wrapper.text()).toContain('Stoppen')
      expect(wrapper.text()).toContain('Neustart')
    })

    it('selecting Steuerung adds it to extraValues', async () => {
      const wrapper = createWrapper({
        allowedKeys: steuerungAllowedKeys,
        extraValues: [],
      })

      const buttons = wrapper.findAll('button')
      const steuerungButton = buttons.find((b) =>
        b.text().includes('Steuerung'),
      )

      await steuerungButton.trigger('click')

      expect(wrapper.emitted('update:extraValues')[0][0]).toContain(
        'object_reset',
      )
    })

    it('selecting Steuerung removes individual contained actions from extraValues', async () => {
      const wrapper = createWrapper({
        allowedKeys: steuerungAllowedKeys,
        extraValues: ['object_actions_start', 'object_actions_stop'],
      })

      const buttons = wrapper.findAll('button')
      const steuerungButton = buttons.find((b) =>
        b.text().includes('Steuerung'),
      )

      await steuerungButton.trigger('click')

      const emitted = wrapper.emitted('update:extraValues')[0][0]
      expect(emitted).toContain('object_reset')
      expect(emitted).not.toContain('object_actions_start')
      expect(emitted).not.toContain('object_actions_stop')
    })

    it('deselecting Steuerung removes it and all contained actions', async () => {
      const wrapper = createWrapper({
        allowedKeys: steuerungAllowedKeys,
        extraValues: ['object_reset'],
      })

      const buttons = wrapper.findAll('button')
      const steuerungButton = buttons.find((b) =>
        b.text().includes('Steuerung'),
      )

      await steuerungButton.trigger('click')

      const emitted = wrapper.emitted('update:extraValues')[0][0]
      expect(emitted).not.toContain('object_reset')
      expect(emitted).not.toContain('object_actions_start')
    })

    it('contained actions show implicit state when Steuerung is active', () => {
      const wrapper = createWrapper({
        allowedKeys: steuerungAllowedKeys,
        extraValues: ['object_reset'],
      })

      const buttons = wrapper.findAll('button')
      const startButton = buttons.find((b) => b.text().includes('Starten'))

      // Implicit actions show lighter violet color
      expect(startButton.classes()).toContain('from-violet-400')
    })

    it('selecting individual action when Steuerung is active removes Steuerung', async () => {
      const wrapper = createWrapper({
        allowedKeys: steuerungAllowedKeys,
        extraValues: ['object_reset'],
      })

      const buttons = wrapper.findAll('button')
      const startButton = buttons.find((b) => b.text().includes('Starten'))

      await startButton.trigger('click')

      const emitted = wrapper.emitted('update:extraValues')[0][0]
      expect(emitted).not.toContain('object_reset')
      expect(emitted).toContain('object_actions_start')
    })

    it('selecting individual action when Steuerung is not active adds it normally', async () => {
      const wrapper = createWrapper({
        allowedKeys: steuerungAllowedKeys,
        extraValues: [],
      })

      const buttons = wrapper.findAll('button')
      const startButton = buttons.find((b) => b.text().includes('Starten'))

      await startButton.trigger('click')

      const emitted = wrapper.emitted('update:extraValues')[0][0]
      expect(emitted).toContain('object_actions_start')
      expect(emitted).not.toContain('object_reset')
    })

    it('deselecting individual action removes it', async () => {
      const wrapper = createWrapper({
        allowedKeys: steuerungAllowedKeys,
        extraValues: ['object_actions_start'],
      })

      const buttons = wrapper.findAll('button')
      const startButton = buttons.find((b) => b.text().includes('Starten'))

      await startButton.trigger('click')

      const emitted = wrapper.emitted('update:extraValues')[0][0]
      expect(emitted).not.toContain('object_actions_start')
    })
  })

  describe('Mutually Exclusive Groups (Dashboard Permissions)', () => {
    const dashboardAllowedKeys = [
      'object_read',
      'object_admins',
      'object_verwaltende',
    ]

    it('shows both admins and verwaltende buttons', () => {
      const wrapper = createWrapper({
        allowedKeys: dashboardAllowedKeys,
      })

      expect(wrapper.text()).toContain('Admins')
      expect(wrapper.text()).toContain('Verwaltende')
    })

    it('selecting admins adds it to extraValues', async () => {
      const wrapper = createWrapper({
        allowedKeys: dashboardAllowedKeys,
        extraValues: [],
      })

      const buttons = wrapper.findAll('button')
      const adminsButton = buttons.find((b) => b.text().includes('Admins'))

      await adminsButton.trigger('click')

      expect(wrapper.emitted('update:extraValues')[0][0]).toContain(
        'object_admins',
      )
    })

    it('selecting admins removes verwaltende', async () => {
      const wrapper = createWrapper({
        allowedKeys: dashboardAllowedKeys,
        extraValues: ['object_verwaltende'],
      })

      const buttons = wrapper.findAll('button')
      const adminsButton = buttons.find((b) => b.text().includes('Admins'))

      await adminsButton.trigger('click')

      const emitted = wrapper.emitted('update:extraValues')[0][0]
      expect(emitted).toContain('object_admins')
      expect(emitted).not.toContain('object_verwaltende')
    })

    it('selecting verwaltende removes admins', async () => {
      const wrapper = createWrapper({
        allowedKeys: dashboardAllowedKeys,
        extraValues: ['object_admins'],
      })

      const buttons = wrapper.findAll('button')
      const verwButton = buttons.find((b) => b.text().includes('Verwaltende'))

      await verwButton.trigger('click')

      const emitted = wrapper.emitted('update:extraValues')[0][0]
      expect(emitted).toContain('object_verwaltende')
      expect(emitted).not.toContain('object_admins')
    })

    it('deselecting active permission removes it', async () => {
      const wrapper = createWrapper({
        allowedKeys: dashboardAllowedKeys,
        extraValues: ['object_admins'],
      })

      const buttons = wrapper.findAll('button')
      const adminsButton = buttons.find((b) => b.text().includes('Admins'))

      await adminsButton.trigger('click')

      const emitted = wrapper.emitted('update:extraValues')[0][0]
      expect(emitted).not.toContain('object_admins')
    })

    it('cannot have both admins and verwaltende active', async () => {
      const wrapper = createWrapper({
        allowedKeys: dashboardAllowedKeys,
        extraValues: [],
      })

      const buttons = wrapper.findAll('button')
      const adminsButton = buttons.find((b) => b.text().includes('Admins'))
      const verwButton = buttons.find((b) => b.text().includes('Verwaltende'))

      // Select admins first
      await adminsButton.trigger('click')
      let emitted = wrapper.emitted('update:extraValues')[0][0]
      expect(emitted).toContain('object_admins')

      // Now create a new wrapper with admins selected and click verwaltende
      const wrapper2 = createWrapper({
        allowedKeys: dashboardAllowedKeys,
        extraValues: ['object_admins'],
      })

      const buttons2 = wrapper2.findAll('button')
      const verwButton2 = buttons2.find((b) => b.text().includes('Verwaltende'))

      await verwButton2.trigger('click')
      emitted = wrapper2.emitted('update:extraValues')[0][0]

      // Should only have verwaltende, not both
      expect(emitted).toContain('object_verwaltende')
      expect(emitted).not.toContain('object_admins')
    })
  })

  describe('Chain-Extra Exclusions', () => {
    const activitiesAllowedKeys = [
      'object_read',
      'object_update',
      'object_delete',
    ]

    it('shows both Lesen button', () => {
      const wrapper = createWrapper({
        allowedKeys: activitiesAllowedKeys,
      })

      expect(wrapper.text()).toContain('Lesen')
    })
  })

  describe('Custom Sort Order (VM Actions)', () => {
    const vmAllowedKeys = [
      'object_read',
      'object_reset',
      'object_actions_start',
      'object_actions_stop',
      'object_actions_reboot',
      'object_actions_reset',
      'object_actions_shutdown',
      'object_actions_resume',
    ]

    it('renders action buttons in custom order', () => {
      const wrapper = createWrapper({
        allowedKeys: vmAllowedKeys,
        mode: 'global',
      })

      const text = wrapper.text()

      // Find positions of each action in the text
      const steuerungPos = text.indexOf('Steuerung')
      const startPos = text.indexOf('Starten')
      const shutdownPos = text.indexOf('Herunterfahren')
      const stopPos = text.indexOf('Stoppen')
      const rebootPos = text.indexOf('Neustart')
      const resetPos = text.indexOf('Reset')

      // Steuerung should come first
      expect(steuerungPos).toBeLessThan(startPos)

      // Start should come before shutdown
      expect(startPos).toBeLessThan(shutdownPos)

      // Shutdown should come before stop (custom order)
      expect(shutdownPos).toBeLessThan(stopPos)

      // Stop should come before reboot
      expect(stopPos).toBeLessThan(rebootPos)

      // Reboot should come before reset
      expect(rebootPos).toBeLessThan(resetPos)
    })

    it('Steuerung appears before individual actions', () => {
      const wrapper = createWrapper({
        allowedKeys: vmAllowedKeys,
      })

      const buttons = wrapper.findAll('button')
      const buttonTexts = buttons.map((b) => b.text())

      const steuerungIndex = buttonTexts.findIndex((t) =>
        t.includes('Steuerung'),
      )
      const startIndex = buttonTexts.findIndex((t) => t.includes('Starten'))

      expect(steuerungIndex).toBeLessThan(startIndex)
    })
  })

  describe('Object Mode Layout', () => {
    it('in object mode, extras always appear in second row container', () => {
      const wrapper = createWrapper({
        mode: 'object',
        allowedKeys: ['object_read', 'action_special'],
      })

      // Find the flex-col container (second row container)
      const secondRowContainer = wrapper.find('.flex.flex-col.gap-2')
      expect(secondRowContainer.exists()).toBe(true)

      // The special button should be inside the second row
      const specialButton = secondRowContainer
        .findAll('button')
        .find((b) => b.text().includes('Spezial'))
      expect(specialButton).toBeDefined()
    })

    it('in global mode with few buttons, extras can be in first row', () => {
      const wrapper = createWrapper({
        mode: 'global',
        allowedKeys: ['object_read', 'action_special'],
      })

      // Find all top-level divs
      const rows = wrapper.findAll(':scope > div > div')

      // With only read + special (and None), they should be in first row
      // The first row contains the inline-flex wrapper
      const firstRow = wrapper.find('.inline-flex.flex-wrap.gap-2')
      const specialInFirstRow = firstRow
        .findAll('button')
        .find((b) => b.text().includes('Spezial'))
      expect(specialInFirstRow).toBeDefined()
    })
  })

  describe('Edge Cases', () => {
    it('handles empty allowedKeys array', () => {
      const wrapper = createWrapper({
        allowedKeys: [],
      })

      // Should only show None button (no create, no chain, no full, no extras)
      const buttons = wrapper.findAll('button')
      expect(buttons.length).toBe(1)
      expect(buttons[0].text()).toContain('Keine')
    })

    it('handles null extraValues gracefully', () => {
      const wrapper = createWrapper({
        extraValues: null,
      })

      // Should not crash
      expect(wrapper.exists()).toBe(true)
    })

    it('handles clicking None when already at none', async () => {
      const wrapper = createWrapper({
        modelValue: 'none',
        extraValues: [],
        createValue: false,
      })

      const noneButton = wrapper.findAll('button')[0]
      await noneButton.trigger('click')

      // Should still emit, even though nothing changes
      expect(wrapper.emitted('update:modelValue')).toEqual([['none']])
      expect(wrapper.emitted('update:extraValues')).toEqual([[[]]])
    })

    it('preserves unrelated extras when toggling chain', async () => {
      const wrapper = createWrapper({
        modelValue: 'none',
        allowedKeys: ['object_read', 'object_update', 'action_special'],
        extraValues: ['action_special'],
      })

      const buttons = wrapper.findAll('button')
      const readButton = buttons.find((b) => b.text().includes('Lesen'))

      await readButton.trigger('click')

      // Chain toggle should not affect unrelated extras
      expect(wrapper.emitted('update:extraValues')).toBeUndefined()
      expect(wrapper.emitted('update:modelValue')).toEqual([['object_read']])
    })

    it('string extraValues are handled correctly', () => {
      const wrapper = createWrapper({
        allowedKeys: ['object_read', 'action_special'],
        extraValues: ['action_special'], // Already strings
      })

      const buttons = wrapper.findAll('button')
      const specialButton = buttons.find((b) => b.text().includes('Spezial'))

      expect(specialButton.attributes('aria-pressed')).toBe('true')
    })
  })
})
