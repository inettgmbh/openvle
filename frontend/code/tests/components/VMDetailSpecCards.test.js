import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

const { mockGet, mockVMData } = vi.hoisted(() => {
  const mockVMData = {
    id: 'a1b2c3d4-5678-4e9f-9bcb-2f3a4d5e6f7g',
    name: 'Test VM',
    status: 'running',
    cpu: 4,
    ram: 2048,
    disk: 120,
    os: '85ed6d38-881c-454f-8950-307f64044d16',
    template: 'ebcf3979-40be-46c4-a9ca-e335d106a7ef',
    event: '17cc28e6-19c0-46b9-9082-feb09ad0bfcd',
    ipv4: '192.168.3.13',
    proxmoxNode: 'proxmox01',
    proxmoxId: 421,
    prevent_delete: false,
    guacamoles: [],
    createdById: 'user-1',
    updatedById: 'user-1',
  }
  return {
    mockVMData,
    mockGet: vi.fn().mockResolvedValue({ ...mockVMData }),
  }
})

vi.mock('@/services', () => ({
  default: {
    vms: {
      get: mockGet,
      getApps: vi.fn().mockResolvedValue({
        items: [],
        pageDetails: { totalCount: 0 },
      }),
      action: vi.fn().mockResolvedValue({}),
      getIPv4: vi.fn().mockResolvedValue({}),
      setProtection: vi.fn().mockResolvedValue({}),
      delete: vi.fn().mockResolvedValue({}),
      updateApps: vi.fn().mockResolvedValue({}),
      getHa: vi.fn().mockResolvedValue({
        type: 'vm',
        state: 'ignored',
        max_restart: 0,
        max_relocate: 0,
        digest: null,
      }),
      setHa: vi.fn().mockResolvedValue({}),
      removeHa: vi.fn().mockResolvedValue({}),
    },
    beginSilent: vi.fn(),
    endSilent: vi.fn(),
    connections: {
      listByObject: vi.fn().mockResolvedValue({
        items: [],
        pageDetails: { totalCount: 0 },
      }),
    },
    guacamole: {
      create: vi.fn().mockResolvedValue({}),
      delete: vi.fn().mockResolvedValue({}),
    },
    tasks: {
      listSubTasks: vi.fn().mockResolvedValue({
        items: [],
        pageDetails: { totalCount: 0 },
      }),
    },
    applications: { search: vi.fn().mockResolvedValue([]) },
    users: {
      search: vi.fn().mockResolvedValue([]),
      formatById: vi.fn().mockResolvedValue(''),
    },
  },
}))

// Track what resolveFieldFromLookup does to test permission-aware display
const { mockResolve, mockCheckPermissions, mockUserCan } = vi.hoisted(() => ({
  mockResolve: vi.fn(),
  mockCheckPermissions: vi.fn().mockResolvedValue({}),
  mockUserCan: vi.fn().mockResolvedValue(false),
}))

vi.mock('@/utils/dataUtils', () => ({
  resolveFieldFromLookup: mockResolve,
  checkObjectPermissions: mockCheckPermissions,
  usePermissionRefs: () => ({
    canEdit: { value: false },
    canDelete: { value: false },
    canReadPermissions: { value: false },
    canReadTasks: { value: false },
    canReadChangelogs: { value: false },
    canReadGuacamoles: { value: false },
    canReadConnections: { value: false },
    canCreateGuacamoles: { value: false },
    canCreateConnections: { value: false },
  }),
  connectionProfileLabelFormatter: vi.fn(),
  protocolConnectionFilter: vi.fn().mockReturnValue([]),
  protectedObjectFilter: vi.fn().mockReturnValue([]),
  roleProtectedFilter: vi.fn().mockReturnValue([]),
  statusEventFilter: vi.fn().mockReturnValue([]),
  statusTemplateFilter: vi.fn().mockReturnValue([]),
  statusUserFilter: vi.fn().mockReturnValue([]),
  statusVMFilter: vi.fn().mockReturnValue([]),
}))

vi.mock('@/stores/main', () => ({
  useMainStore: vi.fn().mockReturnValue({
    fetchPermissions: vi.fn(),
    userCan: mockUserCan,
    settings: {},
  }),
}))

vi.mock('vue-toastification', () => ({
  useToast: vi.fn().mockReturnValue({
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  }),
}))

vi.mock('@/utils/icons', () => ({
  connectionProtocolFormatterIcon: vi.fn(),
  eventCreateTypeIcon: vi.fn(),
  haStateIconVM: vi.fn().mockReturnValue('M0 0h24v24H0z'),
  taskStatusIcon: vi.fn(),
  vmStatusIcon: vi.fn(),
}))

vi.mock('@/utils/objectColors.js', () => ({
  createTypeColorConnection: vi.fn(),
  protocolColorConnection: vi.fn(),
  statusColorTask: vi.fn(),
  statusColorVM: vi.fn(),
}))

vi.mock('@/utils/tooltips', () => ({
  eventCreateTypeTooltip: vi.fn(),
  taskStatusTooltip: vi.fn(),
}))

vi.mock('@/utils/useAutofocusInput', () => ({
  useAutofocusInput: () => ({ autoFocusInputRef: { value: null } }),
}))

// Stub all heavy child components
const stubComponent = (name) => ({
  template: `<div class="${name}"><slot /></div>`,
  props: Object.keys(
    Object.getOwnPropertyDescriptors(Object.getPrototypeOf({})),
  ),
})

const stubs = {
  LayoutAuthenticated: {
    template: '<div><slot /></div>',
  },
  SectionMain: { template: '<div><slot /></div>' },
  SectionTitleLineWithButton: {
    template: '<div class="section-title"><slot /></div>',
    props: ['icon', 'title', 'objectModel', 'main', 'docsPath', 'reload'],
  },
  CardBox: { template: '<div class="card-box"><slot /></div>' },
  BaseTabs: {
    template: '<div class="tabs"><slot /></div>',
    emits: ['tab-changed'],
  },
  BaseTab: {
    template: '<div class="tab"><slot /></div>',
    props: ['id', 'title'],
  },
  BaseButton: {
    template: '<button></button>',
    props: ['icon', 'label', 'color', 'roundedFull', 'small', 'disabled'],
  },
  BaseButtons: { template: '<div><slot /></div>', props: ['type'] },
  BaseButtonDropdown: {
    template: '<div></div>',
    props: [
      'label',
      'icon',
      'dropdownItems',
      'disabled',
      'roundedFull',
      'color',
      'small',
    ],
  },
  BaseDivider: { template: '<hr />' },
  BaseMarkdown: { template: '<div></div>', props: ['modelValue', 'action'] },
  BaseTable: {
    template: '<div></div>',
    props: [
      'currentPage',
      'perPage',
      'itemsTotal',
      'data',
      'sortColumnKey',
      'sortDirection',
      'loading',
      'objectModel',
      'buttons',
      'columns',
    ],
  },
  CardBoxDeleteModal: { template: '<div></div>', props: ['modelValue'] },
  CardBoxDeleteRelationModal: {
    template: '<div></div>',
    props: ['modelValue'],
  },
  CardBoxModal: { template: '<div></div>', props: ['modelValue'] },
  FormControl: {
    template: '<input />',
    props: ['modelValue', 'icon', 'link', 'disabled'],
  },
  FormField: {
    template: '<div class="form-field"><slot /></div>',
    props: ['label', 'help'],
  },
  MetricsSelectionPanel: { template: '<div></div>' },
  NotificationBar: { template: '<div></div>' },
  ObjectMetadataDisplay: { template: '<div></div>' },
  PillTag: {
    template: '<span></span>',
    props: ['label', 'color', 'disabled', 'icon', 'small', 'handleClick'],
  },
  ProxmoxRrdChart: { template: '<div></div>' },
  SearchControl: { template: '<div></div>' },
  SearchModal: { template: '<div></div>', props: ['modelValue'] },
  TableChangelogs: { template: '<div></div>' },
  TablePermissions: { template: '<div></div>' },
}

import SpecCard from '@/components/SpecCard.vue'
import VMDetail from '@/views/vm/VMDetail.vue'

describe('VMDetail - Spec Cards', () => {
  let wrapper

  const createWrapper = async (vmOverrides = {}, resolveCallback) => {
    const vmData = { ...mockVMData, ...vmOverrides }
    mockGet.mockResolvedValue({ ...vmData })

    // Simulate resolveFieldFromLookup applying resolved names
    mockResolve.mockImplementation(async (obj, mappings) => {
      for (const { from, to } of mappings) {
        if (resolveCallback) {
          const result = resolveCallback(from, to, obj[from])
          if (result !== undefined) {
            obj[to] = result
            continue
          }
        }
        // Default: return the UUID (simulating no read permission)
        obj[to] = obj[to] || obj[from]
      }
    })

    wrapper = mount(VMDetail, {
      global: {
        stubs: {
          ...stubs,
          SpecCard,
        },
      },
    })

    await flushPromises()
    return wrapper
  }

  afterEach(() => {
    if (wrapper) wrapper.unmount()
    vi.clearAllMocks()
  })

  describe('card rendering', () => {
    it('renders 9 spec cards when all fields are present', async () => {
      await createWrapper({}, (from, to) => {
        const names = {
          osName: 'Ubuntu 22.04',
          eventName: 'Sommersemester 2025',
          templateName: 'Ubuntu Base',
          createdBy: 'Admin',
          updatedBy: 'Admin',
        }
        return names[to]
      })

      const cards = wrapper.findAllComponents(SpecCard)
      expect(cards.length).toBe(9)
    })

    it('renders 7 spec cards when event and template are missing', async () => {
      await createWrapper({ event: null, template: null })

      const cards = wrapper.findAllComponents(SpecCard)
      expect(cards.length).toBe(7)
    })

    it('renders 8 spec cards when only event is missing', async () => {
      await createWrapper({ event: null })

      const cards = wrapper.findAllComponents(SpecCard)
      expect(cards.length).toBe(8)
    })

    it('omits the HA card when the VM has no Proxmox ID', async () => {
      await createWrapper({ proxmoxId: null })

      const cards = wrapper.findAllComponents(SpecCard)
      expect(cards.find((c) => c.props('label') === 'HA-Status')).toBe(
        undefined,
      )
    })
  })

  describe('card values', () => {
    it('displays CPU value', async () => {
      await createWrapper({}, () => 'Resolved')
      const cards = wrapper.findAllComponents(SpecCard)
      const cpuCard = cards.find((c) => c.props('label') === 'CPU Kerne')
      expect(cpuCard.props('value')).toBe(4)
    })

    it('displays RAM in GB (converted from MB)', async () => {
      await createWrapper({}, () => 'Resolved')
      const cards = wrapper.findAllComponents(SpecCard)
      const ramCard = cards.find((c) => c.props('label') === 'Arbeitsspeicher')
      expect(ramCard.props('value')).toBe('2 GB')
    })

    it('displays disk in GB', async () => {
      await createWrapper({}, () => 'Resolved')
      const cards = wrapper.findAllComponents(SpecCard)
      const diskCard = cards.find((c) => c.props('label') === 'Festplatte')
      expect(diskCard.props('value')).toBe('120 GB')
    })

    it('displays IPv4 address', async () => {
      await createWrapper({}, () => 'Resolved')
      const cards = wrapper.findAllComponents(SpecCard)
      const ipCard = cards.find((c) => c.props('label') === 'IPv4 Adresse')
      expect(ipCard.props('value')).toBe('192.168.3.13')
      expect(ipCard.props('copyable')).toBe(true)
    })

    it('displays Proxmox VE label', async () => {
      await createWrapper({}, () => 'Resolved')
      const cards = wrapper.findAllComponents(SpecCard)
      const pveCard = cards.find((c) => c.props('label') === 'Proxmox VE')
      expect(pveCard.props('value')).toBe('421 (proxmox01)')
    })

    it('displays the HA state fetched on mount', async () => {
      await createWrapper({}, () => 'Resolved')
      const cards = wrapper.findAllComponents(SpecCard)
      const haCard = cards.find((c) => c.props('label') === 'HA-Status')
      expect(haCard.props('value')).toBe('Nicht aktiviert')
    })
  })

  describe('permission-aware display', () => {
    it('shows resolved OS name with link when permission granted', async () => {
      await createWrapper({}, (from, to) => {
        if (to === 'osName') return 'Ubuntu 22.04'
      })

      const cards = wrapper.findAllComponents(SpecCard)
      const osCard = cards.find((c) => c.props('label') === 'Betriebssystem')
      expect(osCard.props('value')).toBe('Ubuntu 22.04')
      expect(osCard.props('link')).toBe(
        '/os/85ed6d38-881c-454f-8950-307f64044d16',
      )
      expect(osCard.props('hint')).toBeNull()
    })

    it('shows truncated UUID with hint when OS permission denied', async () => {
      await createWrapper()

      const cards = wrapper.findAllComponents(SpecCard)
      const osCard = cards.find((c) => c.props('label') === 'Betriebssystem')
      expect(osCard.props('value')).toBe('85ed6d38...')
      expect(osCard.props('link')).toBeNull()
      expect(osCard.props('hint')).toBe('Keine Leseberechtigung')
    })

    it('shows resolved event name with link when permission granted', async () => {
      await createWrapper({}, (from, to) => {
        if (to === 'eventName') return 'Sommersemester 2025'
      })

      const cards = wrapper.findAllComponents(SpecCard)
      const eventCard = cards.find((c) => c.props('label') === 'Veranstaltung')
      expect(eventCard.props('value')).toBe('Sommersemester 2025')
      expect(eventCard.props('link')).toBe(
        '/events/17cc28e6-19c0-46b9-9082-feb09ad0bfcd',
      )
      expect(eventCard.props('hint')).toBeNull()
    })

    it('shows truncated UUID with hint when event permission denied', async () => {
      await createWrapper()

      const cards = wrapper.findAllComponents(SpecCard)
      const eventCard = cards.find((c) => c.props('label') === 'Veranstaltung')
      expect(eventCard.props('value')).toBe('17cc28e6...')
      expect(eventCard.props('link')).toBeNull()
      expect(eventCard.props('hint')).toBe('Keine Leseberechtigung')
    })

    it('shows resolved template name with link when permission granted', async () => {
      await createWrapper({}, (from, to) => {
        if (to === 'templateName') return 'Ubuntu Base'
      })

      const cards = wrapper.findAllComponents(SpecCard)
      const tmplCard = cards.find((c) => c.props('label') === 'VM-Vorlage')
      expect(tmplCard.props('value')).toBe('Ubuntu Base')
      expect(tmplCard.props('link')).toBe(
        '/templates/ebcf3979-40be-46c4-a9ca-e335d106a7ef',
      )
    })

    it('shows truncated UUID with hint when template permission denied', async () => {
      await createWrapper()

      const cards = wrapper.findAllComponents(SpecCard)
      const tmplCard = cards.find((c) => c.props('label') === 'VM-Vorlage')
      expect(tmplCard.props('value')).toBe('ebcf3979...')
      expect(tmplCard.props('link')).toBeNull()
      expect(tmplCard.props('hint')).toBe('Keine Leseberechtigung')
    })
  })

  describe('card colors', () => {
    it('assigns correct colors to each card', async () => {
      await createWrapper({}, (from, to) => {
        const names = {
          osName: 'Ubuntu',
          eventName: 'Event',
          templateName: 'Template',
        }
        return names[to]
      })

      const cards = wrapper.findAllComponents(SpecCard)
      const colorMap = {}
      cards.forEach((c) => {
        colorMap[c.props('label')] = c.props('color')
      })

      expect(colorMap).toEqual(
        expect.objectContaining({
          'CPU Kerne': 'blue',
          Arbeitsspeicher: 'violet',
          Festplatte: 'amber',
          Betriebssystem: 'emerald',
          'IPv4 Adresse': 'sky',
          'Proxmox VE': 'slate',
          'VM-Vorlage': 'cyan',
          Veranstaltung: 'rose',
        }),
      )
    })
  })
})
