import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import CardBoxDeleteUserModal from '@/components/CardBoxDeleteUserModal.vue'
import backend from '@/services'

// resolveFieldFromLookup is a no-op so eventName lookups don't try to
// hit any backend; tests inject eventName directly on items when needed.
vi.mock('@/utils/dataUtils', async () => {
  const actual = await vi.importActual('@/utils/dataUtils')
  return {
    ...actual,
    resolveFieldFromLookup: vi.fn().mockResolvedValue(undefined),
  }
})

// vi.mock factories run before module-level consts initialize, so the
// fns are hoisted via vi.hoisted to keep the same identity across tests.
const { toastError, toastSuccess } = vi.hoisted(() => ({
  toastError: vi.fn(),
  toastSuccess: vi.fn(),
}))

vi.mock('vue-toastification', () => ({
  useToast: vi.fn(() => ({
    error: toastError,
    success: toastSuccess,
  })),
}))

const stubs = {
  CardBoxModal: {
    template: '<div class="card-modal"><slot /></div>',
    props: ['modelValue', 'hasButton', 'title', 'customClass'],
  },
  CardBox: {
    template: '<div class="card-box"><slot /><slot name="footer" /></div>',
  },
  BaseDivider: { template: '<hr />' },
  BaseButton: {
    template:
      '<button class="base-button" :disabled="disabled" @click="$emit(\'click\', $event)">{{ label }}</button>',
    emits: ['click'],
    props: [
      'label',
      'icon',
      'color',
      'small',
      'roundedFull',
      'class',
      'disabled',
      'outline',
      'type',
    ],
  },
  BaseButtons: { template: '<div><slot /></div>' },
  FormControl: {
    template: '<input class="form-control" />',
    props: ['modelValue', 'icon', 'placeholder'],
  },
  FormField: {
    template: '<div class="form-field"><slot /></div>',
    props: ['class'],
  },
  NotificationBar: {
    template:
      '<div :class="[\'notification\', `notification-${color}`]"><slot /></div>',
    props: ['dismissable', 'color', 'icon', 'class'],
  },
}

const baseStats = {
  virtual_machines: 0,
  connections: 0,
  mails: 0,
  changelogs: 0,
  object_permissions: 0,
  event_memberships: 0,
  policy_memberships: 0,
  tags: 0,
}

const emptyList = { items: [], truncated: false }

const buildResponse = (overrides = {}) => ({
  stats: { ...baseStats, ...(overrides.stats ?? {}) },
  virtual_machines: overrides.virtual_machines ?? emptyList,
  connections: overrides.connections ?? emptyList,
  mails: overrides.mails ?? emptyList,
  changelogs: overrides.changelogs ?? emptyList,
  object_permissions: overrides.object_permissions ?? emptyList,
  tags: overrides.tags ?? emptyList,
  event_memberships: overrides.event_memberships ?? emptyList,
})

const defaultProps = {
  modelValue: false,
  checkvalue: 'Mock User',
  object: { id: 'user-1', name: 'Mock User', email: 'mock@example.com' },
}

const mountModal = async (props = {}) => {
  const w = mount(CardBoxDeleteUserModal, {
    props: { ...defaultProps, ...props },
    global: { stubs },
    attachTo: document.body,
  })
  // Trigger the watch on modelValue → fetch fires when modal becomes visible
  await w.setProps({ modelValue: true })
  await flushPromises()
  return w
}

describe('CardBoxDeleteUserModal', () => {
  let wrapper
  let openSpy

  beforeEach(() => {
    backend.users.getDeletePreview.mockReset()
    backend.users.getDeletePreview.mockResolvedValue(buildResponse())
    toastError.mockReset()
    toastSuccess.mockReset()
    openSpy = vi.spyOn(window, 'open').mockImplementation(() => null)
  })

  afterEach(() => {
    wrapper?.unmount()
    document.body.innerHTML = ''
    openSpy.mockRestore()
  })

  describe('loading & empty state', () => {
    it('shows a loading spinner before fetch resolves', async () => {
      let resolveFetch
      backend.users.getDeletePreview.mockImplementation(
        () => new Promise((res) => (resolveFetch = res)),
      )

      // Mount closed first, then open so the watch fires and triggers fetch
      wrapper = mount(CardBoxDeleteUserModal, {
        props: { ...defaultProps, modelValue: false },
        global: { stubs },
        attachTo: document.body,
      })
      await wrapper.setProps({ modelValue: true })
      // Intentionally do not flushPromises — the fetch must remain pending

      expect(wrapper.text()).toContain('Laden')
      expect(wrapper.findAll('details').length).toBe(0)

      // Resolve so afterEach can unmount cleanly
      resolveFetch(buildResponse())
      await flushPromises()
    })

    it('shows empty state when nothing is linked to the user', async () => {
      wrapper = await mountModal()

      expect(wrapper.text()).toContain(
        'Mit diesem Benutzer sind keine weiteren Objekte verknüpft.',
      )
      expect(wrapper.findAll('details').length).toBe(0)
      expect(wrapper.text()).not.toContain('Die folgenden Objekte')
    })

    it('does not show empty state when only counter-only data exists', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({ stats: { policy_memberships: 2 } }),
      )

      wrapper = await mountModal()

      expect(wrapper.text()).not.toContain('keine weiteren Objekte')
      expect(wrapper.text()).toContain('Richtlinien-Zustimmungen')
    })

    it('does not fetch while the modal is closed', () => {
      wrapper = mount(CardBoxDeleteUserModal, {
        props: { ...defaultProps, modelValue: false },
        global: { stubs },
        attachTo: document.body,
      })

      expect(backend.users.getDeletePreview).not.toHaveBeenCalled()
    })
  })

  describe('section composition', () => {
    it('renders only non-counter-only lists as <details>', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({
          stats: { virtual_machines: 2, mails: 1 },
          virtual_machines: {
            items: [
              { id: 'vm-1', name: 'pyws-alice-t101' },
              { id: 'vm-2', name: 'pyws-alice-t102' },
            ],
            truncated: false,
          },
          mails: {
            items: [{ id: 'm-1', subject: 'Welcome', to_mail: 'a@b.de' }],
            truncated: false,
          },
        }),
      )

      wrapper = await mountModal()

      const details = wrapper.findAll('details')
      expect(details.length).toBe(1)
      expect(details[0].find('summary').text()).toContain('VMs')
      expect(details[0].find('summary').text()).toContain('2')
      // Mails counter still appears, just not as <details>
      expect(wrapper.text()).toContain('E-Mails')
      expect(wrapper.text()).toContain('1')
    })

    it('hides sections whose counter is zero', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({
          stats: { tags: 3 },
          tags: {
            items: [
              { key: 'a', value: '1' },
              { key: 'b', value: '2' },
              { key: 'c', value: '3' },
            ],
            truncated: false,
          },
        }),
      )

      wrapper = await mountModal()

      // VMs/Mails/etc. with count=0 must not be rendered
      expect(wrapper.text()).not.toContain('VMs')
      expect(wrapper.text()).not.toContain('E-Mails')
      expect(wrapper.text()).not.toContain('Berechtigungen')
      expect(wrapper.text()).not.toContain('Changelog')
      expect(wrapper.text()).not.toContain('Verbindungen')
      expect(wrapper.text()).not.toContain('Veranstaltungsteilnahmen')
      expect(wrapper.text()).not.toContain('Richtlinien-Zustimmungen')
      expect(wrapper.text()).toContain('Tags')
    })

    it('sorts sections alphabetically by translated label', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({
          stats: {
            virtual_machines: 1,
            tags: 1,
            event_memberships: 1,
            mails: 1,
            object_permissions: 1,
            changelogs: 1,
            policy_memberships: 1,
          },
          virtual_machines: {
            items: [{ id: 'vm-1', name: 'vm' }],
            truncated: false,
          },
          tags: { items: [{ key: 't', value: 'v' }], truncated: false },
          event_memberships: {
            items: [{ id: 'em-1', name: 'EM', role: { name: 'Tutor' } }],
            truncated: false,
          },
        }),
      )

      wrapper = await mountModal()

      const labels = wrapper
        .findAll(
          '.notification-danger ~ * span.font-medium > span.truncate, ' +
            // Headers live in summary or sibling div; pick text from each row
            'details > summary span.font-medium > span.truncate, ' +
            'div.flex.items-center.gap-2 > span.font-medium > span.truncate',
        )
        .map((w) => w.text())

      // Filter out potential noise: keep only known section labels
      const known = [
        'Berechtigungen',
        'Changelogs',
        'E-Mails',
        'Richtlinien-Zustimmungen',
        'Tags',
        'Veranstaltungsteilnahmen',
        'Verbindungen',
        'VMs',
      ]
      const ordered = labels.filter((l) => known.includes(l))

      expect(ordered).toEqual([
        'Berechtigungen',
        'Changelogs',
        'E-Mails',
        'Richtlinien-Zustimmungen',
        'Tags',
        'Veranstaltungsteilnahmen',
        'VMs',
      ])
    })
  })

  describe('counter-only sections', () => {
    it('renders policy memberships as a non-collapsible counter section', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({ stats: { policy_memberships: 5 } }),
      )

      wrapper = await mountModal()

      expect(wrapper.findAll('details').length).toBe(0)
      expect(wrapper.text()).toContain('Richtlinien-Zustimmungen')
      expect(wrapper.text()).toContain('5')
    })

    it('renders changelogs and object_permissions as counter-only sections', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({
          stats: { changelogs: 42, object_permissions: 7 },
          // Backend may still send items; UI must ignore them.
          changelogs: {
            items: [{ id: 'c-1', object_id: 'uuid-...' }],
            truncated: false,
          },
          object_permissions: {
            items: [{ id: 'p-1', name: '' }],
            truncated: false,
          },
        }),
      )

      wrapper = await mountModal()

      expect(wrapper.findAll('details').length).toBe(0)
      expect(wrapper.text()).toContain('Changelog')
      expect(wrapper.text()).toContain('42')
      expect(wrapper.text()).toContain('Berechtigungen')
      expect(wrapper.text()).toContain('7')
    })

    it('renders mails as a counter-only section even when items are sent', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({
          stats: { mails: 3 },
          mails: {
            items: [
              { id: 'm-1', subject: 'A', to_mail: 'a@b.de' },
              { id: 'm-2', subject: 'B', to_mail: 'b@b.de' },
              { id: 'm-3', subject: 'C', to_mail: 'c@b.de' },
            ],
            truncated: false,
          },
        }),
      )

      wrapper = await mountModal()

      expect(wrapper.findAll('details').length).toBe(0)
      expect(wrapper.text()).toContain('E-Mails')
      expect(wrapper.text()).toContain('3')
      // Item subjects must NOT bleed into the counter-only section
      expect(wrapper.text()).not.toContain('a@b.de')
    })

    it('shows only the total in counter-only sections, even when truncated', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({
          stats: { mails: 250 },
          mails: { items: [], truncated: true },
        }),
      )

      wrapper = await mountModal()

      expect(wrapper.text()).toContain('E-Mails')
      expect(wrapper.text()).toContain('250')
      // No "X von Y" hint on counter-only sections
      expect(wrapper.text()).not.toContain('insgesamt')
      expect(wrapper.text()).not.toContain('angezeigt')
    })
  })

  describe('truncated counter', () => {
    it('renders "<total> insgesamt – <shown> angezeigt" on expandable sections', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({
          stats: { virtual_machines: 250 },
          virtual_machines: {
            items: Array.from({ length: 100 }, (_, i) => ({
              id: `vm-${i}`,
              name: `vm-${i}`,
            })),
            truncated: true,
          },
        }),
      )

      wrapper = await mountModal()

      const summary = wrapper.find('details summary')
      expect(summary.text()).toContain('VMs')
      expect(summary.text()).toContain('250 insgesamt')
      expect(summary.text()).toContain('100 angezeigt')
    })

    it('flags truncated badges with the warning color class', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({
          stats: { virtual_machines: 200 },
          virtual_machines: {
            items: Array.from({ length: 100 }, (_, i) => ({
              id: `vm-${i}`,
              name: `vm-${i}`,
            })),
            truncated: true,
          },
        }),
      )

      wrapper = await mountModal()

      // The badge inside the summary uses amber-* classes when truncated
      const html = wrapper.find('details summary').html()
      expect(html).toContain('bg-amber-100')
    })
  })

  describe('item display labels', () => {
    it('uses item.name for vms by default', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({
          stats: { virtual_machines: 1 },
          virtual_machines: {
            items: [{ id: 'vm-1', name: 'pyws-alice-t101' }],
            truncated: false,
          },
        }),
      )

      wrapper = await mountModal()
      expect(wrapper.find('details li').text()).toContain('pyws-alice-t101')
    })

    it('uses item.name for connections by default', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({
          stats: { connections: 1 },
          connections: {
            items: [{ id: 'conn-1', name: 'rdp-server-01' }],
            truncated: false,
          },
        }),
      )

      wrapper = await mountModal()
      expect(wrapper.find('details li').text()).toContain('rdp-server-01')
    })

    it('uses key: value for tags', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({
          stats: { tags: 1 },
          tags: {
            items: [{ key: 'room', value: 'A101' }],
            truncated: false,
          },
        }),
      )

      wrapper = await mountModal()
      expect(wrapper.find('details li').text()).toContain('room: A101')
    })

    it('uses name + role.name for event_memberships', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({
          stats: { event_memberships: 1 },
          event_memberships: {
            items: [
              {
                id: 'em-1',
                name: 'WS25 Networking',
                role: { id: 'r-1', name: 'Tutor' },
                event: 'evt-1',
              },
            ],
            truncated: false,
          },
        }),
      )

      wrapper = await mountModal()
      const text = wrapper.find('details li').text()
      expect(text).toContain('WS25 Networking')
      expect(text).toContain('Tutor')
    })

    it('falls back to eventName when event_membership has no own name', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({
          stats: { event_memberships: 1 },
          event_memberships: {
            items: [
              {
                id: 'em-1',
                eventName: 'WS25 Resolved Event',
                role: { name: 'Tutor' },
                event: 'evt-1',
              },
            ],
            truncated: false,
          },
        }),
      )

      wrapper = await mountModal()
      expect(wrapper.find('details li').text()).toContain('WS25 Resolved Event')
    })

    it('renders an em-dash placeholder when label resolves to empty', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({
          stats: { virtual_machines: 1 },
          virtual_machines: {
            // Neither name nor id present → placeholder fallback
            items: [{}],
            truncated: false,
          },
        }),
      )

      wrapper = await mountModal()
      expect(wrapper.find('details li').text()).toContain('—')
    })
  })

  describe('open-in-new button', () => {
    const findItemButton = (w) =>
      w.findAll('details li button.base-button').at(0)

    it('renders the button when item has the configured idField', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({
          stats: { virtual_machines: 1 },
          virtual_machines: {
            items: [{ id: 'vm-1', name: 'foo' }],
            truncated: false,
          },
        }),
      )

      wrapper = await mountModal()
      expect(wrapper.findAll('details li button.base-button').length).toBe(1)
    })

    it('hides the button when item is missing the configured idField', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({
          stats: { tags: 1 },
          tags: {
            // tag without `key` → no link, button must be hidden
            items: [{ value: 'A101' }],
            truncated: false,
          },
        }),
      )

      wrapper = await mountModal()
      expect(wrapper.findAll('details li button.base-button').length).toBe(0)
    })

    it('opens /vms/:id for vm items', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({
          stats: { virtual_machines: 1 },
          virtual_machines: {
            items: [{ id: 'vm-42', name: 'foo' }],
            truncated: false,
          },
        }),
      )

      wrapper = await mountModal()
      await findItemButton(wrapper).trigger('click')

      expect(openSpy).toHaveBeenCalledTimes(1)
      expect(openSpy.mock.calls[0][0]).toContain('/vms/vm-42')
      expect(openSpy.mock.calls[0][1]).toBe('_blank')
    })

    it('opens /guacamoles/:id for connection items', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({
          stats: { connections: 1 },
          connections: {
            items: [{ id: 'conn-9', name: 'foo' }],
            truncated: false,
          },
        }),
      )

      wrapper = await mountModal()
      await findItemButton(wrapper).trigger('click')

      expect(openSpy.mock.calls[0][0]).toContain('/guacamoles/conn-9')
    })

    it('opens /tags/:key for tag items (key, not id)', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({
          stats: { tags: 1 },
          tags: {
            items: [{ key: 'room', value: 'A101' }],
            truncated: false,
          },
        }),
      )

      wrapper = await mountModal()
      await findItemButton(wrapper).trigger('click')

      expect(openSpy.mock.calls[0][0]).toContain('/tags/room')
    })

    it('opens /events/:event for event_membership items', async () => {
      backend.users.getDeletePreview.mockResolvedValue(
        buildResponse({
          stats: { event_memberships: 1 },
          event_memberships: {
            items: [
              {
                id: 'em-1',
                name: 'WS25',
                role: { name: 'Tutor' },
                event: 'evt-uuid-77',
              },
            ],
            truncated: false,
          },
        }),
      )

      wrapper = await mountModal()
      await findItemButton(wrapper).trigger('click')

      expect(openSpy.mock.calls[0][0]).toContain('/events/evt-uuid-77')
    })
  })

  describe('error handling', () => {
    it('shows a toast when the preview fetch fails', async () => {
      backend.users.getDeletePreview.mockRejectedValue({
        response: { data: { detail: 'boom' } },
      })

      wrapper = await mountModal()

      expect(toastError).toHaveBeenCalledTimes(1)
      const message = toastError.mock.calls[0][0]
      expect(message).toContain('Fehler beim Laden der Löschvorschau')
      expect(message).toContain('boom')
    })
  })
})
