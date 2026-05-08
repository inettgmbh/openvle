import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

const { mockGet, mockTemplateData } = vi.hoisted(() => {
  const mockTemplateData = {
    id: 'tmpl-1234-5678',
    name: 'Ubuntu Base Template',
    status: 'ready',
    cpu: 2,
    ram: 4096,
    disk: 50,
    os: 'dd89af9d-8953-48c5-8083-3e8210219c3e',
    proxmoxNode: 'proxmox01',
    proxmoxId: 900,
    prevent_delete: false,
    guacamoles: [],
    createdById: 'user-1',
    updatedById: 'user-1',
  }
  return {
    mockTemplateData,
    mockGet: vi.fn().mockResolvedValue({ ...mockTemplateData }),
  }
})

vi.mock('@/services', () => ({
  default: {
    templates: {
      get: mockGet,
      getApps: vi.fn().mockResolvedValue({
        items: [],
        pageDetails: { totalCount: 0 },
      }),
      delete: vi.fn().mockResolvedValue({}),
      updateApps: vi.fn().mockResolvedValue({}),
    },
    connections: {
      listByObject: vi.fn().mockResolvedValue({
        items: [],
        pageDetails: { totalCount: 0 },
      }),
    },
    tasks: {
      listSubTasks: vi.fn().mockResolvedValue({
        items: [],
        pageDetails: { totalCount: 0 },
      }),
    },
    applications: { search: vi.fn().mockResolvedValue([]) },
    courses: { search: vi.fn().mockResolvedValue([]) },
    vms: {
      list: vi.fn().mockResolvedValue({
        items: [],
        pageDetails: { totalCount: 0 },
      }),
    },
  },
}))

const { mockResolve, mockCheckPermissions } = vi.hoisted(() => ({
  mockResolve: vi.fn(),
  mockCheckPermissions: vi.fn().mockResolvedValue({}),
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
    canReadConnections: { value: false },
    canCreateConnections: { value: false },
  }),
  connectionProfileLabelFormatter: vi.fn(),
  templateStatusFormatter: vi.fn().mockReturnValue('Bereit'),
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
    userCan: vi.fn().mockResolvedValue(false),
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
  taskStatusIcon: vi.fn(),
  templateStatusIcon: vi.fn(),
  vmStatusIcon: vi.fn(),
}))

vi.mock('@/utils/objectColors.js', () => ({
  protocolColorConnection: vi.fn(),
  statusColorTask: vi.fn(),
  statusColorTemplates: vi.fn(),
  statusColorVM: vi.fn(),
}))

vi.mock('@/utils/tooltips', () => ({
  taskStatusTooltip: vi.fn(),
}))

const stubs = {
  LayoutAuthenticated: { template: '<div><slot /></div>' },
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
  BaseDivider: { template: '<hr />' },
  BaseMarkdown: { template: '<div></div>', props: ['modelValue', 'action'] },
  BaseTable: { template: '<div></div>' },
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
  ObjectMetadataDisplay: { template: '<div></div>' },
  PillTag: {
    template: '<span></span>',
    props: ['label', 'color', 'disabled', 'icon', 'small', 'handleClick'],
  },
  SearchModal: { template: '<div></div>', props: ['modelValue'] },
  TableChangelogs: { template: '<div></div>' },
  TablePermissions: { template: '<div></div>' },
}

import SpecCard from '@/components/SpecCard.vue'
import TemplateDetail from '@/views/template/TemplateDetail.vue'

describe('TemplateDetail - Spec Cards', () => {
  let wrapper

  const createWrapper = async (templateOverrides = {}, resolveCallback) => {
    const tmplData = { ...mockTemplateData, ...templateOverrides }
    mockGet.mockResolvedValue({ ...tmplData })

    mockResolve.mockImplementation(async (obj, mappings) => {
      for (const { from, to } of mappings) {
        if (resolveCallback) {
          const result = resolveCallback(from, to, obj[from])
          if (result !== undefined) {
            obj[to] = result
            continue
          }
        }
        obj[to] = obj[to] || obj[from]
      }
    })

    wrapper = mount(TemplateDetail, {
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
    it('renders 5 spec cards', async () => {
      await createWrapper({}, () => 'Resolved')

      const cards = wrapper.findAllComponents(SpecCard)
      expect(cards.length).toBe(5)
    })

    it('renders correct card labels', async () => {
      await createWrapper({}, () => 'Resolved')

      const cards = wrapper.findAllComponents(SpecCard)
      const labels = cards.map((c) => c.props('label'))
      expect(labels).toEqual([
        'CPU Kerne',
        'Arbeitsspeicher',
        'Festplatte',
        'Betriebssystem',
        'Proxmox VE',
      ])
    })
  })

  describe('card values', () => {
    it('displays CPU value', async () => {
      await createWrapper({}, () => 'Resolved')
      const cards = wrapper.findAllComponents(SpecCard)
      const cpuCard = cards.find((c) => c.props('label') === 'CPU Kerne')
      expect(cpuCard.props('value')).toBe(2)
    })

    it('displays RAM in GB (converted from MB)', async () => {
      await createWrapper({}, () => 'Resolved')
      const cards = wrapper.findAllComponents(SpecCard)
      const ramCard = cards.find((c) => c.props('label') === 'Arbeitsspeicher')
      expect(ramCard.props('value')).toBe('4 GB')
    })

    it('displays disk in GB', async () => {
      await createWrapper({}, () => 'Resolved')
      const cards = wrapper.findAllComponents(SpecCard)
      const diskCard = cards.find((c) => c.props('label') === 'Festplatte')
      expect(diskCard.props('value')).toBe('50 GB')
    })

    it('displays Proxmox VE label', async () => {
      await createWrapper({}, () => 'Resolved')
      const cards = wrapper.findAllComponents(SpecCard)
      const pveCard = cards.find((c) => c.props('label') === 'Proxmox VE')
      expect(pveCard.props('value')).toBe('900 (proxmox01)')
    })
  })

  describe('permission-aware OS display', () => {
    it('shows resolved OS name with link when permission granted', async () => {
      await createWrapper({}, (from, to) => {
        if (to === 'osName') return 'Ubuntu 22.04'
      })

      const cards = wrapper.findAllComponents(SpecCard)
      const osCard = cards.find((c) => c.props('label') === 'Betriebssystem')
      expect(osCard.props('value')).toBe('Ubuntu 22.04')
      expect(osCard.props('link')).toBe(
        '/os/dd89af9d-8953-48c5-8083-3e8210219c3e',
      )
      expect(osCard.props('hint')).toBeNull()
    })

    it('shows truncated UUID with hint when OS permission denied', async () => {
      await createWrapper()

      const cards = wrapper.findAllComponents(SpecCard)
      const osCard = cards.find((c) => c.props('label') === 'Betriebssystem')
      expect(osCard.props('value')).toBe('dd89af9d...')
      expect(osCard.props('link')).toBeNull()
      expect(osCard.props('hint')).toBe('Keine Leseberechtigung')
    })
  })

  describe('card colors', () => {
    it('assigns correct colors to each card', async () => {
      await createWrapper({}, () => 'Resolved')

      const cards = wrapper.findAllComponents(SpecCard)
      const colorMap = {}
      cards.forEach((c) => {
        colorMap[c.props('label')] = c.props('color')
      })

      expect(colorMap).toEqual({
        'CPU Kerne': 'blue',
        Arbeitsspeicher: 'violet',
        Festplatte: 'amber',
        Betriebssystem: 'emerald',
        'Proxmox VE': 'slate',
      })
    })
  })

  describe('does not render VM-specific cards', () => {
    it('has no IPv4, event, or template cards', async () => {
      await createWrapper({}, () => 'Resolved')

      const cards = wrapper.findAllComponents(SpecCard)
      const labels = cards.map((c) => c.props('label'))
      expect(labels).not.toContain('IPv4 Adresse')
      expect(labels).not.toContain('Veranstaltung')
      expect(labels).not.toContain('VM-Vorlage')
    })
  })
})
