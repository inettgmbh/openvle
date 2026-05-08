import { describe, expect, it } from 'vitest'

import { calculateChanges } from '@/utils/objectModelPermissions'

describe('calculateChanges', () => {
  const entityId = 'user-123'
  const entityType = 'User'

  describe('extras object changes', () => {
    it('detects removal of object-scoped extra permission', () => {
      const before = {
        global: {},
        globalCreate: {},
        objects: {},
        extrasGlobal: {},
        extrasObjects: {
          VirtualMachine: {
            'vm-1': ['object_reset'],
          },
        },
      }

      const after = {
        global: {},
        globalCreate: {},
        objects: {
          VirtualMachine: {
            'vm-1': 'none',
          },
        },
        extrasGlobal: {},
        extrasObjects: {},
      }

      const { upserts, deletes } = calculateChanges(
        before,
        after,
        entityId,
        entityType,
      )

      expect(upserts).toEqual([])
      expect(deletes).toHaveLength(1)
      expect(deletes[0]).toEqual({
        object_type: 'VirtualMachine',
        object_id: 'vm-1',
        permission_key: 'object_reset',
      })
    })

    it('detects removal of multiple object-scoped extra permissions', () => {
      const before = {
        global: {},
        globalCreate: {},
        objects: {},
        extrasGlobal: {},
        extrasObjects: {
          VirtualMachine: {
            'vm-1': ['object_reset', 'object_actions_start'],
          },
        },
      }

      const after = {
        global: {},
        globalCreate: {},
        objects: {
          VirtualMachine: {
            'vm-1': 'none',
          },
        },
        extrasGlobal: {},
        extrasObjects: {},
      }

      const { upserts, deletes } = calculateChanges(
        before,
        after,
        entityId,
        entityType,
      )

      expect(upserts).toEqual([])
      expect(deletes).toHaveLength(2)
      expect(deletes).toContainEqual({
        object_type: 'VirtualMachine',
        object_id: 'vm-1',
        permission_key: 'object_reset',
      })
      expect(deletes).toContainEqual({
        object_type: 'VirtualMachine',
        object_id: 'vm-1',
        permission_key: 'object_actions_start',
      })
    })

    it('does not create duplicate deletes when level also changes to none', () => {
      const before = {
        global: {},
        globalCreate: {},
        objects: {
          VirtualMachine: {
            'vm-1': 'object_read',
          },
        },
        extrasGlobal: {},
        extrasObjects: {
          VirtualMachine: {
            'vm-1': ['object_reset'],
          },
        },
      }

      const after = {
        global: {},
        globalCreate: {},
        objects: {
          VirtualMachine: {
            'vm-1': 'none',
          },
        },
        extrasGlobal: {},
        extrasObjects: {},
      }

      const { upserts, deletes } = calculateChanges(
        before,
        after,
        entityId,
        entityType,
      )

      expect(upserts).toEqual([])
      // Should have delete-all for level change, extras should not add individual deletes
      expect(deletes).toHaveLength(1)
      expect(deletes[0]).toEqual({
        object_type: 'VirtualMachine',
        object_id: 'vm-1',
      })
    })
  })
})
