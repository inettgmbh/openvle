import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import {
  OBJECT_TYPE,
  useUserSettingsStore,
  VIEW_KIND,
} from '@/stores/userSettings'

describe('userSettings store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('constants', () => {
    it('exposes frozen VIEW_KIND with the expected kinds', () => {
      expect(VIEW_KIND.LIST).toBe('list')
      expect(VIEW_KIND.DETAIL).toBe('detail')
      expect(VIEW_KIND.CREATE).toBe('create')
      expect(VIEW_KIND.EDIT).toBe('edit')
      expect(VIEW_KIND.BULK_ACTION).toBe('bulkAction')
      expect(VIEW_KIND.IMPORT).toBe('import')
      expect(Object.isFrozen(VIEW_KIND)).toBe(true)
    })

    it('exposes frozen OBJECT_TYPE constants', () => {
      expect(OBJECT_TYPE.VMS).toBe('vms')
      expect(OBJECT_TYPE.EVENTS).toBe('events')
      expect(OBJECT_TYPE.TEMPLATES).toBe('templates')
      expect(OBJECT_TYPE.RATE_LIMITS).toBe('rateLimits')
      expect(Object.isFrozen(OBJECT_TYPE)).toBe(true)
    })
  })

  describe('get', () => {
    it('returns the fallback when the path does not exist', () => {
      const store = useUserSettingsStore()
      expect(store.get('objects.vms.list.autoRefresh', true)).toBe(true)
      expect(store.get('app.dashboard.widgets', [])).toEqual([])
      expect(store.get('global.tablePerPageDefault', 25)).toBe(25)
    })

    it('returns the stored value when present', () => {
      const store = useUserSettingsStore()
      store.set('objects.vms.list.autoRefresh', false)
      expect(store.get('objects.vms.list.autoRefresh')).toBe(false)
    })

    it('treats explicitly stored falsy values as values, not as missing', () => {
      const store = useUserSettingsStore()
      store.set('objects.vms.list.autoRefresh', false)
      expect(store.get('objects.vms.list.autoRefresh', true)).toBe(false)

      store.set('global.theme', null)
      expect(store.get('global.theme', 'auto')).toBe(null)
    })
  })

  describe('set', () => {
    it('writes a leaf value at a deep path, creating intermediates', () => {
      const store = useUserSettingsStore()
      store.set('objects.vms.detail.activeTab', 'permissions')
      expect(store.objects).toEqual({
        vms: { detail: { activeTab: 'permissions' } },
      })
    })

    it('keeps unrelated buckets untouched', () => {
      const store = useUserSettingsStore()
      store.set('objects.vms.list.autoRefresh', false)
      store.set('app.dashboard.widgets', ['a', 'b'])
      store.set('global.locale', 'de')

      expect(store.objects.vms.list.autoRefresh).toBe(false)
      expect(store.app.dashboard.widgets).toEqual(['a', 'b'])
      expect(store.global.locale).toBe('de')
    })

    it('overwrites existing values without dropping siblings', () => {
      const store = useUserSettingsStore()
      store.set('objects.vms.list.autoRefresh', true)
      store.set('objects.vms.list.perPage', 50)
      store.set('objects.vms.list.autoRefresh', false)

      expect(store.objects.vms.list).toEqual({
        autoRefresh: false,
        perPage: 50,
      })
    })

    it('keeps state isolated between object types and view kinds', () => {
      const store = useUserSettingsStore()
      store.set(
        `objects.${OBJECT_TYPE.VMS}.${VIEW_KIND.LIST}.autoRefresh`,
        false,
      )
      store.set(
        `objects.${OBJECT_TYPE.EVENTS}.${VIEW_KIND.LIST}.autoRefresh`,
        true,
      )
      store.set(
        `objects.${OBJECT_TYPE.VMS}.${VIEW_KIND.DETAIL}.activeTab`,
        'meta',
      )

      expect(
        store.get(`objects.${OBJECT_TYPE.VMS}.${VIEW_KIND.LIST}.autoRefresh`),
      ).toBe(false)
      expect(
        store.get(
          `objects.${OBJECT_TYPE.EVENTS}.${VIEW_KIND.LIST}.autoRefresh`,
        ),
      ).toBe(true)
      expect(
        store.get(`objects.${OBJECT_TYPE.VMS}.${VIEW_KIND.DETAIL}.activeTab`),
      ).toBe('meta')
    })
  })

  describe('reset', () => {
    it('clears every bucket', () => {
      const store = useUserSettingsStore()
      store.set('objects.vms.list.autoRefresh', false)
      store.set('app.dashboard.widgets', ['a'])
      store.set('global.locale', 'de')

      store.reset()

      expect(store.objects).toEqual({})
      expect(store.app).toEqual({})
      expect(store.global).toEqual({})
      expect(store.get('objects.vms.list.autoRefresh', true)).toBe(true)
    })
  })
})
