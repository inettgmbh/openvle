import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// Mock BaseButton
vi.mock('@/components/BaseButton.vue', () => ({
  default: {
    name: 'BaseButton',
    template: '<button @click="$emit(\'click\')"><slot />{{ label }}</button>',
    props: ['color', 'label', 'icon', 'disabled'],
  },
}))

// Mock CardBox
vi.mock('@/components/CardBox.vue', () => ({
  default: {
    name: 'CardBox',
    template: '<div class="card-box"><slot /></div>',
    props: ['isModal'],
  },
}))

// Mock OverlayLayer
vi.mock('@/components/OverlayLayer.vue', () => ({
  default: {
    name: 'OverlayLayer',
    template:
      '<div class="overlay" @click="$emit(\'overlay-click\')"><slot /></div>',
  },
}))

// Mock objectModelPermissions
vi.mock('@/utils/objectModelPermissions', () => ({
  getObjectPermissionShortLabel: vi.fn(({ permission }) => {
    const map = {
      object_read: 'Lesen',
      object_update: 'Bearbeiten',
      object_delete: 'Löschen',
      object_full: 'Vollzugriff',
    }
    return map[permission] || permission
  }),
}))

import PermissionChangesConfirmModal from '@/components/permissions/PermissionChangesConfirmModal.vue'

describe('PermissionChangesConfirmModal', () => {
  const defaultChanges = {
    upserts: [],
    deletes: [],
  }

  const getObjectTypeLabel = vi.fn((ot) => `${ot}s`)
  const getObjectLabelSync = vi.fn((ot, id) => `${ot} - ${id}`)

  const createWrapper = (props = {}) => {
    return mount(PermissionChangesConfirmModal, {
      props: {
        modelValue: true,
        changes: defaultChanges,
        getObjectTypeLabel,
        getObjectLabelSync,
        ...props,
      },
    })
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders modal when modelValue is true', () => {
      const wrapper = createWrapper({ modelValue: true })
      expect(wrapper.find('.card-box').isVisible()).toBe(true)
    })

    it('hides modal when modelValue is false', () => {
      const wrapper = createWrapper({ modelValue: false })
      expect(wrapper.find('.card-box').isVisible()).toBe(false)
    })

    it('renders title', () => {
      const wrapper = createWrapper()
      expect(wrapper.text()).toContain('Änderungen bestätigen')
    })

    it('renders description', () => {
      const wrapper = createWrapper()
      expect(wrapper.text()).toContain(
        'Bitte überprüfen Sie die Berechtigungsänderungen',
      )
    })

    it('renders cancel button', () => {
      const wrapper = createWrapper()
      expect(wrapper.text()).toContain('Abbrechen')
    })

    it('renders confirm button', () => {
      const wrapper = createWrapper()
      expect(wrapper.text()).toContain('Änderungen speichern')
    })
  })

  describe('No Changes State', () => {
    it('shows no changes message when empty', () => {
      const wrapper = createWrapper({
        changes: { upserts: [], deletes: [] },
      })

      expect(wrapper.text()).toContain('Keine Änderungen vorhanden')
    })

    it('disables confirm button when no changes', () => {
      const wrapper = createWrapper({
        changes: { upserts: [], deletes: [] },
      })

      const confirmButton = wrapper.findAllComponents({ name: 'BaseButton' })[1]
      expect(confirmButton.props('disabled')).toBe(true)
    })
  })

  describe('With Upserts', () => {
    it('shows upserts grouped by object type', () => {
      const wrapper = createWrapper({
        changes: {
          upserts: [
            {
              object_type: 'User',
              object_id: null,
              permission_key: 'object_read',
            },
            {
              object_type: 'User',
              object_id: 'u-1',
              permission_key: 'object_update',
            },
          ],
          deletes: [],
        },
      })

      expect(wrapper.text()).toContain('Users')
      expect(wrapper.text()).toContain('Hinzugefügt (2)')
    })

    it('shows scope and permission for each upsert', () => {
      const wrapper = createWrapper({
        changes: {
          upserts: [
            {
              object_type: 'User',
              object_id: null,
              permission_key: 'object_read',
            },
          ],
          deletes: [],
        },
      })

      expect(wrapper.text()).toContain('Global')
      expect(wrapper.text()).toContain('Lesen')
    })

    it('shows object label for object-scoped upserts', () => {
      const wrapper = createWrapper({
        changes: {
          upserts: [
            {
              object_type: 'User',
              object_id: 'user-123',
              permission_key: 'object_read',
            },
          ],
          deletes: [],
        },
      })

      expect(getObjectLabelSync).toHaveBeenCalledWith('User', 'user-123')
    })
  })

  describe('With Deletes', () => {
    it('shows deletes grouped by object type', () => {
      const wrapper = createWrapper({
        changes: {
          upserts: [],
          deletes: [
            { object_type: 'Role', object_id: null, previous: 'object_full' },
          ],
        },
      })

      expect(wrapper.text()).toContain('Roles')
      expect(wrapper.text()).toContain('Entfernt (1)')
    })

    it('shows scope and permission for each delete', () => {
      const wrapper = createWrapper({
        changes: {
          upserts: [],
          deletes: [
            { object_type: 'Role', object_id: null, previous: 'object_full' },
          ],
        },
      })

      expect(wrapper.text()).toContain('Global')
      expect(wrapper.text()).toContain('Vollzugriff')
    })

    it('shows "Alle Berechtigungen" when no previous key', () => {
      const wrapper = createWrapper({
        changes: {
          upserts: [],
          deletes: [{ object_type: 'Role', object_id: 'r-1' }],
        },
      })

      expect(wrapper.text()).toContain('Alle Berechtigungen')
    })
  })

  describe('Mixed Changes', () => {
    it('shows both upserts and deletes', () => {
      const wrapper = createWrapper({
        changes: {
          upserts: [
            {
              object_type: 'User',
              object_id: null,
              permission_key: 'object_read',
            },
          ],
          deletes: [
            { object_type: 'User', object_id: null, previous: 'object_delete' },
          ],
        },
      })

      expect(wrapper.text()).toContain('Hinzugefügt')
      expect(wrapper.text()).toContain('Entfernt')
    })

    it('groups by object type correctly', () => {
      const wrapper = createWrapper({
        changes: {
          upserts: [
            {
              object_type: 'User',
              object_id: null,
              permission_key: 'object_read',
            },
            {
              object_type: 'Role',
              object_id: null,
              permission_key: 'object_update',
            },
          ],
          deletes: [
            { object_type: 'User', object_id: null, previous: 'object_delete' },
          ],
        },
      })

      expect(wrapper.text()).toContain('Users')
      expect(wrapper.text()).toContain('Roles')
    })

    it('enables confirm button when has changes', () => {
      const wrapper = createWrapper({
        changes: {
          upserts: [
            {
              object_type: 'User',
              object_id: null,
              permission_key: 'object_read',
            },
          ],
          deletes: [],
        },
      })

      const confirmButton = wrapper.findAllComponents({ name: 'BaseButton' })[1]
      expect(confirmButton.props('disabled')).toBe(false)
    })
  })

  describe('Events', () => {
    it('emits cancel when cancel button clicked', async () => {
      const wrapper = createWrapper()

      const cancelButton = wrapper.findAllComponents({ name: 'BaseButton' })[0]
      await cancelButton.trigger('click')

      expect(wrapper.emitted('cancel')).toBeTruthy()
      // Should emit update:modelValue with false (may emit multiple times due to reactivity)
      const emits = wrapper.emitted('update:modelValue')
      expect(emits).toBeTruthy()
      expect(emits.some((e) => e[0] === false)).toBe(true)
    })

    it('emits confirm when confirm button clicked', async () => {
      const wrapper = createWrapper({
        changes: {
          upserts: [
            {
              object_type: 'User',
              object_id: null,
              permission_key: 'object_read',
            },
          ],
          deletes: [],
        },
      })

      const confirmButton = wrapper.findAllComponents({ name: 'BaseButton' })[1]
      await confirmButton.trigger('click')

      expect(wrapper.emitted('confirm')).toBeTruthy()
      // Should emit update:modelValue with false (may emit multiple times due to reactivity)
      const emits = wrapper.emitted('update:modelValue')
      expect(emits).toBeTruthy()
      expect(emits.some((e) => e[0] === false)).toBe(true)
    })

    it('emits cancel when overlay clicked', async () => {
      const wrapper = createWrapper()

      const overlay = wrapper.findComponent({ name: 'OverlayLayer' })
      await overlay.trigger('overlay-click')

      expect(wrapper.emitted('cancel')).toBeTruthy()
    })
  })

  describe('Sorting', () => {
    it('sorts groups alphabetically by label', () => {
      getObjectTypeLabel.mockImplementation((ot) =>
        ot === 'Zebra' ? 'Zebras' : 'Anwendungen',
      )

      const wrapper = createWrapper({
        changes: {
          upserts: [
            {
              object_type: 'Zebra',
              object_id: null,
              permission_key: 'object_read',
            },
            {
              object_type: 'Application',
              object_id: null,
              permission_key: 'object_read',
            },
          ],
          deletes: [],
        },
      })

      const text = wrapper.text()
      const appIndex = text.indexOf('Anwendungen')
      const zebraIndex = text.indexOf('Zebras')

      expect(appIndex).toBeLessThan(zebraIndex)
    })
  })

  describe('Props Validation', () => {
    it('requires changes prop', () => {
      const { changes } = PermissionChangesConfirmModal.props
      expect(changes.required).toBe(true)
    })

    it('requires getObjectTypeLabel function', () => {
      const { getObjectTypeLabel } = PermissionChangesConfirmModal.props
      expect(getObjectTypeLabel.type).toBe(Function)
      expect(getObjectTypeLabel.required).toBe(true)
    })

    it('requires getObjectLabelSync function', () => {
      const { getObjectLabelSync } = PermissionChangesConfirmModal.props
      expect(getObjectLabelSync.type).toBe(Function)
      expect(getObjectLabelSync.required).toBe(true)
    })
  })

  describe('hasChanges Computed', () => {
    it('returns true when upserts exist', () => {
      const wrapper = createWrapper({
        changes: {
          upserts: [{ object_type: 'User', permission_key: 'object_read' }],
          deletes: [],
        },
      })

      // If hasChanges is true, confirm button should be enabled
      const confirmButton = wrapper.findAllComponents({ name: 'BaseButton' })[1]
      expect(confirmButton.props('disabled')).toBe(false)
    })

    it('returns true when deletes exist', () => {
      const wrapper = createWrapper({
        changes: {
          upserts: [],
          deletes: [{ object_type: 'User', previous: 'object_read' }],
        },
      })

      const confirmButton = wrapper.findAllComponents({ name: 'BaseButton' })[1]
      expect(confirmButton.props('disabled')).toBe(false)
    })

    it('returns false when both empty', () => {
      const wrapper = createWrapper({
        changes: { upserts: [], deletes: [] },
      })

      const confirmButton = wrapper.findAllComponents({ name: 'BaseButton' })[1]
      expect(confirmButton.props('disabled')).toBe(true)
    })
  })

  describe('Icons', () => {
    it('renders warning icon in header', () => {
      const wrapper = createWrapper()
      expect(wrapper.find('svg').exists()).toBe(true)
    })

    it('renders plus icon for upserts section', () => {
      const wrapper = createWrapper({
        changes: {
          upserts: [{ object_type: 'User', permission_key: 'object_read' }],
          deletes: [],
        },
      })

      const svgs = wrapper.findAll('svg')
      expect(svgs.length).toBeGreaterThan(1)
    })

    it('renders delete icon for deletes section', () => {
      const wrapper = createWrapper({
        changes: {
          upserts: [],
          deletes: [{ object_type: 'User', previous: 'object_read' }],
        },
      })

      const svgs = wrapper.findAll('svg')
      expect(svgs.length).toBeGreaterThan(1)
    })
  })
})
