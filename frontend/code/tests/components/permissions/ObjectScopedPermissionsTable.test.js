import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// Mock PermissionSelector
vi.mock('@/components/permissions/PermissionSelector.vue', () => ({
  default: {
    name: 'PermissionSelector',
    template: `
      <div class="permission-selector" data-testid="permission-selector">
        <button
          @click="$emit('update:modelValue', 'object_read')"
          data-testid="set-read"
        >Set Read</button>
        <button
          @click="$emit('update:extraValues', ['action_1'])"
          data-testid="set-extras"
        >Set Extras</button>
      </div>
    `,
    props: ['modelValue', 'disabled', 'mode', 'allowedKeys', 'extraValues'],
  },
}))

import ObjectScopedPermissionsTable from '@/components/permissions/ObjectScopedPermissionsTable.vue'

describe('ObjectScopedPermissionsTable', () => {
  const defaultProps = {
    objectType: 'User',
    objectEntries: [],
    isEditing: false,
    getObjectLabelSync: vi.fn((ot, id) => `Label for ${id}`),
    getObjectTypeLabel: vi.fn((ot) => `${ot}s`),
    getLevel: vi.fn(() => 'none'),
    getExtras: vi.fn(() => []),
    allowedKeys: null,
  }

  const createWrapper = (props = {}) => {
    return mount(ObjectScopedPermissionsTable, {
      props: {
        ...defaultProps,
        ...props,
      },
    })
  }

  beforeEach(() => {
    vi.clearAllMocks()
    defaultProps.getObjectLabelSync.mockImplementation(
      (ot, id) => `Label for ${id}`,
    )
    defaultProps.getObjectTypeLabel.mockImplementation((ot) => `${ot}s`)
    defaultProps.getLevel.mockReturnValue('none')
    defaultProps.getExtras.mockReturnValue([])
  })

  describe('Rendering', () => {
    it('renders header', () => {
      const wrapper = createWrapper()
      expect(wrapper.text()).toContain('Objektbezogene Berechtigungen')
    })

    it('renders description', () => {
      const wrapper = createWrapper()
      expect(wrapper.text()).toContain(
        'Overrides gelten nur für einzelne Objekte',
      )
    })

    it('renders table with headers', () => {
      const wrapper = createWrapper()
      expect(wrapper.text()).toContain('Objekt')
      expect(wrapper.text()).toContain('Berechtigung')
      expect(wrapper.text()).toContain('Aktion')
    })

    it('renders empty state when no entries', () => {
      const wrapper = createWrapper({ objectEntries: [] })
      expect(wrapper.text()).toContain(
        'Keine objektbezogenen Berechtigungen vorhanden',
      )
    })
  })

  describe('With Object Entries', () => {
    it('renders a row for each entry', () => {
      const wrapper = createWrapper({
        objectEntries: [
          { objectId: 'obj-1' },
          { objectId: 'obj-2' },
          { objectId: 'obj-3' },
        ],
      })

      const rows = wrapper.findAll('tbody tr')
      expect(rows).toHaveLength(3)
    })

    it('displays object label', () => {
      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-123' }],
      })

      expect(wrapper.text()).toContain('Label for obj-123')
      expect(defaultProps.getObjectLabelSync).toHaveBeenCalledWith(
        'User',
        'obj-123',
      )
    })

    it('displays object ID in monospace', () => {
      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-123' }],
      })

      expect(wrapper.text()).toContain('obj-123')
      expect(wrapper.find('.font-mono').exists()).toBe(true)
    })

    it('renders PermissionSelector for each entry', () => {
      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-1' }],
      })

      expect(
        wrapper.findComponent({ name: 'PermissionSelector' }).exists(),
      ).toBe(true)
    })

    it('renders remove button for each entry', () => {
      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-1' }],
      })

      const buttons = wrapper.findAll('button')
      const removeButton = buttons.find((b) => b.text().includes('Entfernen'))
      expect(removeButton).toBeTruthy()
      expect(removeButton.text()).toContain('Entfernen')
    })
  })

  describe('PermissionSelector Props', () => {
    it('passes mode="object" to PermissionSelector', () => {
      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-1' }],
      })

      const selector = wrapper.findComponent({ name: 'PermissionSelector' })
      expect(selector.props('mode')).toBe('object')
    })

    it('passes current level to PermissionSelector', () => {
      defaultProps.getLevel.mockReturnValue('object_read')

      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-1' }],
      })

      const selector = wrapper.findComponent({ name: 'PermissionSelector' })
      expect(selector.props('modelValue')).toBe('object_read')
      expect(defaultProps.getLevel).toHaveBeenCalledWith('User', 'obj-1')
    })

    it('passes disabled based on isEditing', () => {
      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-1' }],
        isEditing: false,
      })

      const selector = wrapper.findComponent({ name: 'PermissionSelector' })
      expect(selector.props('disabled')).toBe(true)
    })

    it('passes enabled when isEditing', () => {
      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-1' }],
        isEditing: true,
      })

      const selector = wrapper.findComponent({ name: 'PermissionSelector' })
      expect(selector.props('disabled')).toBe(false)
    })

    it('passes allowedKeys to PermissionSelector', () => {
      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-1' }],
        allowedKeys: ['object_read', 'object_update'],
      })

      const selector = wrapper.findComponent({ name: 'PermissionSelector' })
      expect(selector.props('allowedKeys')).toEqual([
        'object_read',
        'object_update',
      ])
    })

    it('passes extras to PermissionSelector', () => {
      defaultProps.getExtras.mockReturnValue(['action_1', 'action_2'])

      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-1' }],
      })

      const selector = wrapper.findComponent({ name: 'PermissionSelector' })
      expect(selector.props('extraValues')).toEqual(['action_1', 'action_2'])
      expect(defaultProps.getExtras).toHaveBeenCalledWith('User', 'obj-1')
    })
  })

  describe('Events - Set Level', () => {
    it('emits set-level when PermissionSelector changes', async () => {
      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-1' }],
        isEditing: true,
      })

      const selector = wrapper.findComponent({ name: 'PermissionSelector' })
      await selector.vm.$emit('update:modelValue', 'object_read')

      expect(wrapper.emitted('set-level')).toBeTruthy()
      expect(wrapper.emitted('set-level')[0][0]).toEqual({
        objectType: 'User',
        objectId: 'obj-1',
        level: 'object_read',
      })
    })
  })

  describe('Events - Set Extras', () => {
    it('emits set-extras when PermissionSelector changes', async () => {
      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-1' }],
        isEditing: true,
      })

      const selector = wrapper.findComponent({ name: 'PermissionSelector' })
      await selector.vm.$emit('update:extraValues', ['action_1'])

      expect(wrapper.emitted('set-extras')).toBeTruthy()
      expect(wrapper.emitted('set-extras')[0][0]).toEqual({
        objectType: 'User',
        objectId: 'obj-1',
        extras: ['action_1'],
      })
    })
  })

  describe('Remove Button', () => {
    function findRemoveButton(wrapper) {
      // Find the button containing "Entfernen" text (the actual remove button in the template)
      const buttons = wrapper.findAll('button')
      return buttons.find((b) => b.text().includes('Entfernen'))
    }

    it('is disabled when not editing', () => {
      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-1' }],
        isEditing: false,
      })

      const removeButton = findRemoveButton(wrapper)
      expect(removeButton).toBeTruthy()
      expect(removeButton.attributes('disabled')).toBeDefined()
    })

    it('is disabled when already "none" with no extras', () => {
      defaultProps.getLevel.mockReturnValue('none')
      defaultProps.getExtras.mockReturnValue([])

      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-1' }],
        isEditing: true,
      })

      const removeButton = findRemoveButton(wrapper)
      expect(removeButton).toBeTruthy()
      expect(removeButton.attributes('disabled')).toBeDefined()
    })

    it('is enabled when has permission', () => {
      defaultProps.getLevel.mockReturnValue('object_read')

      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-1' }],
        isEditing: true,
      })

      const removeButton = findRemoveButton(wrapper)
      expect(removeButton).toBeTruthy()
      expect(removeButton.attributes('disabled')).toBeUndefined()
    })

    it('is enabled when has extras even if level is none', () => {
      defaultProps.getLevel.mockReturnValue('none')
      defaultProps.getExtras.mockReturnValue(['action_1'])

      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-1' }],
        isEditing: true,
      })

      const removeButton = findRemoveButton(wrapper)
      expect(removeButton).toBeTruthy()
      expect(removeButton.attributes('disabled')).toBeUndefined()
    })

    it('emits set-level when clicked', async () => {
      defaultProps.getLevel.mockReturnValue('object_read')
      defaultProps.getExtras.mockReturnValue(['action_1'])

      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-1' }],
        isEditing: true,
      })

      const removeButton = findRemoveButton(wrapper)
      await removeButton.trigger('click')

      // Should emit set-level with 'none'
      expect(wrapper.emitted('set-level')).toBeTruthy()
      // Find the event with level 'none' (the remove button emits this)
      const setLevelEvents = wrapper.emitted('set-level')
      const noneEvent = setLevelEvents.find((e) => e[0].level === 'none')
      expect(noneEvent).toBeTruthy()
      expect(noneEvent[0]).toEqual({
        objectType: 'User',
        objectId: 'obj-1',
        level: 'none',
      })
    })

    it('emits set-extras when clicked', async () => {
      defaultProps.getLevel.mockReturnValue('object_read')
      defaultProps.getExtras.mockReturnValue(['action_1'])

      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-1' }],
        isEditing: true,
      })

      const removeButton = findRemoveButton(wrapper)
      await removeButton.trigger('click')

      // Should emit set-extras with []
      expect(wrapper.emitted('set-extras')).toBeTruthy()
      const setExtrasEvents = wrapper.emitted('set-extras')
      const emptyEvent = setExtrasEvents.find(
        (e) => Array.isArray(e[0].extras) && e[0].extras.length === 0,
      )
      expect(emptyEvent).toBeTruthy()
      expect(emptyEvent[0]).toEqual({
        objectType: 'User',
        objectId: 'obj-1',
        extras: [],
      })
    })
  })

  describe('Multiple Entries', () => {
    it('handles multiple entries independently', () => {
      defaultProps.getLevel.mockImplementation((ot, id) =>
        id === 'obj-1' ? 'object_read' : 'object_full',
      )

      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-1' }, { objectId: 'obj-2' }],
      })

      expect(defaultProps.getLevel).toHaveBeenCalledWith('User', 'obj-1')
      expect(defaultProps.getLevel).toHaveBeenCalledWith('User', 'obj-2')
    })

    it('emits correct objectId for each row', async () => {
      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-1' }, { objectId: 'obj-2' }],
        isEditing: true,
      })

      const selectors = wrapper.findAllComponents({
        name: 'PermissionSelector',
      })

      await selectors[0].vm.$emit('update:modelValue', 'object_read')
      await selectors[1].vm.$emit('update:modelValue', 'object_read')

      expect(wrapper.emitted('set-level')[0][0].objectId).toBe('obj-1')
      expect(wrapper.emitted('set-level')[1][0].objectId).toBe('obj-2')
    })
  })

  describe('Props Validation', () => {
    it('requires objectType', () => {
      const { objectType } = ObjectScopedPermissionsTable.props
      expect(objectType.required).toBe(true)
      expect(objectType.type).toBe(String)
    })

    it('requires getObjectLabelSync function', () => {
      const { getObjectLabelSync } = ObjectScopedPermissionsTable.props
      expect(getObjectLabelSync.required).toBe(true)
      expect(getObjectLabelSync.type).toBe(Function)
    })

    it('requires getObjectTypeLabel function', () => {
      const { getObjectTypeLabel } = ObjectScopedPermissionsTable.props
      expect(getObjectTypeLabel.required).toBe(true)
      expect(getObjectTypeLabel.type).toBe(Function)
    })

    it('requires getLevel function', () => {
      const { getLevel } = ObjectScopedPermissionsTable.props
      expect(getLevel.required).toBe(true)
      expect(getLevel.type).toBe(Function)
    })

    it('requires getExtras function', () => {
      const { getExtras } = ObjectScopedPermissionsTable.props
      expect(getExtras.required).toBe(true)
      expect(getExtras.type).toBe(Function)
    })

    it('has default for objectEntries', () => {
      const { objectEntries } = ObjectScopedPermissionsTable.props
      expect(objectEntries.default()).toEqual([])
    })

    it('has default for isEditing', () => {
      const { isEditing } = ObjectScopedPermissionsTable.props
      expect(isEditing.default).toBe(false)
    })

    it('has default for allowedKeys', () => {
      const { allowedKeys } = ObjectScopedPermissionsTable.props
      expect(allowedKeys.default).toBeNull()
    })
  })

  describe('Styling', () => {
    it('applies dark mode classes', () => {
      const wrapper = createWrapper()

      expect(wrapper.html()).toContain('dark:')
    })

    it('applies border styling to table', () => {
      const wrapper = createWrapper()

      expect(wrapper.find('.border').exists()).toBe(true)
    })

    it('applies font-bold to title', () => {
      const wrapper = createWrapper()

      expect(wrapper.find('.font-bold').exists()).toBe(true)
    })

    it('applies font-mono to object ID', () => {
      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-1' }],
      })

      expect(wrapper.find('.font-mono').exists()).toBe(true)
    })
  })

  describe('Table Structure', () => {
    it('renders proper table elements', () => {
      const wrapper = createWrapper({
        objectEntries: [{ objectId: 'obj-1' }],
      })

      expect(wrapper.find('table').exists()).toBe(true)
      expect(wrapper.find('thead').exists()).toBe(true)
      expect(wrapper.find('tbody').exists()).toBe(true)
      expect(wrapper.find('th').exists()).toBe(true)
      expect(wrapper.find('td').exists()).toBe(true)
    })

    it('has 3 columns', () => {
      const wrapper = createWrapper()

      const headers = wrapper.findAll('th')
      expect(headers).toHaveLength(3)
    })
  })
})
