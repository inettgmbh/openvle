import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const {
  VM_ID,
  PROFILE_RDP_ID,
  PROFILE_SSH_ID,
  rdpProfile,
  sshProfile,
  mockGuacamoleCreate,
  mockListByObject,
  mockConnectionGet,
  mockVmSearch,
  mockVmGetName,
  mockUserSearch,
  mockUserFormatById,
  mockFetchPermissions,
  mockRouterPush,
  mockRouterBack,
  mockToastSuccess,
  mockToastError,
  mockRouteQuery,
} = vi.hoisted(() => {
  const VM_ID = 'vm-abc-123'
  const PROFILE_RDP_ID = 'profile-rdp-001'
  const PROFILE_SSH_ID = 'profile-ssh-002'

  const rdpProfile = {
    id: PROFILE_RDP_ID,
    port: 3389,
    protocol: 'rdp',
    username: 'admin',
    objectId: VM_ID,
    objectType: 'VirtualMachine',
  }

  const sshProfile = {
    id: PROFILE_SSH_ID,
    port: 22,
    protocol: 'ssh',
    username: 'root',
    objectId: VM_ID,
    objectType: 'VirtualMachine',
  }

  return {
    VM_ID,
    PROFILE_RDP_ID,
    PROFILE_SSH_ID,
    rdpProfile,
    sshProfile,
    mockGuacamoleCreate: vi.fn().mockResolvedValue({ id: 'guac-new-123' }),
    mockListByObject: vi.fn().mockResolvedValue({
      pageDetails: {
        page: 1,
        perPage: 100,
        pageCount: 1,
        totalCount: 2,
      },
      items: [rdpProfile, sshProfile],
    }),
    mockConnectionGet: vi.fn().mockResolvedValue({
      id: PROFILE_RDP_ID,
      objectId: VM_ID,
      protocol: 'rdp',
      port: 3389,
      username: 'admin',
    }),
    mockVmSearch: vi.fn().mockResolvedValue({ items: [] }),
    mockVmGetName: vi.fn().mockResolvedValue('Test VM'),
    mockUserSearch: vi.fn().mockResolvedValue({ items: [] }),
    mockUserFormatById: vi.fn().mockResolvedValue('Test User'),
    mockFetchPermissions: vi.fn(),
    mockRouterPush: vi.fn(),
    mockRouterBack: vi.fn(),
    mockToastSuccess: vi.fn(),
    mockToastError: vi.fn(),
    mockRouteQuery: { value: {} },
  }
})

vi.mock('@/services', () => ({
  default: {
    guacamole: { create: mockGuacamoleCreate },
    connections: {
      listByObject: mockListByObject,
      get: mockConnectionGet,
    },
    vms: {
      search: mockVmSearch,
      getName: mockVmGetName,
    },
    users: {
      search: mockUserSearch,
      formatById: mockUserFormatById,
    },
  },
}))

vi.mock('@/stores/main', () => ({
  useMainStore: vi.fn().mockReturnValue({
    fetchPermissions: mockFetchPermissions,
  }),
}))

vi.mock('@/router', () => ({
  default: {
    push: mockRouterPush,
    back: mockRouterBack,
  },
}))

vi.mock('vue-router', () => ({
  useRoute: vi.fn(() => ({ query: mockRouteQuery.value, params: {} })),
  onBeforeRouteLeave: vi.fn(),
}))

vi.mock('vue-toastification', () => ({
  useToast: vi.fn().mockReturnValue({
    success: mockToastSuccess,
    error: mockToastError,
  }),
}))

vi.mock('@/composables/useConnectionForm', () => ({
  protocolConfig: {
    rdp: {
      icon: 'mdi-desktop-classic',
      label: 'RDP',
      description: 'Remote Desktop',
      port: 3389,
    },
    ssh: {
      icon: 'mdi-console',
      label: 'SSH',
      description: 'Secure Shell',
      port: 22,
    },
    vnc: {
      icon: 'mdi-monitor',
      label: 'VNC',
      description: 'Virtual Network',
      port: 5901,
    },
  },
}))

const stubs = {
  LayoutAuthenticated: {
    template: '<div class="layout"><slot /></div>',
  },
  SectionMain: {
    template: '<div class="section-main"><slot /></div>',
  },
  SectionTitleLineWithButton: {
    template: '<div class="section-title" />',
  },
  CardBox: {
    template: '<form class="card-box"><slot /><slot name="footer" /></form>',
    emits: ['submit'],
  },
  FormField: {
    template: '<div class="form-field" :data-label="label"><slot /></div>',
    props: ['label', 'help', 'tooltip'],
  },
  FormControl: {
    template:
      '<input class="form-control" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
    props: [
      'modelValue',
      'icon',
      'placeholder',
      'required',
      'autofocus',
      'options',
      'disabled',
    ],
  },
  SearchControl: {
    template:
      '<div class="search-control" :data-model="modelValue" @click="$emit(\'update:modelValue\', $attrs[\'data-test-value\'])" />',
    props: ['modelValue', 'icon', 'fetchData', 'fetchSelected', 'required'],
    emits: ['update:modelValue'],
  },
  BaseButton: {
    template:
      '<button class="base-button" :type="type" :disabled="disabled">{{ label }}</button>',
    props: ['type', 'color', 'label', 'disabled', 'outline'],
  },
  BaseButtons: {
    template: '<div class="base-buttons"><slot /></div>',
  },
  BaseIcon: {
    template: '<span class="base-icon" />',
    props: ['path', 'size'],
  },
  UnsavedChangesModal: {
    template: '<div class="unsaved-modal" />',
    props: ['modelValue'],
  },
}

import GuacamoleCreate from '@/views/guacamole/GuacamoleCreate.vue'

describe('GuacamoleCreate', () => {
  let wrapper

  const createWrapper = async (routeQuery = {}) => {
    mockRouteQuery.value = routeQuery
    wrapper = mount(GuacamoleCreate, {
      global: {
        stubs,
        directives: { tooltip: () => {} },
      },
    })
    await flushPromises()
    return wrapper
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockRouteQuery.value = {}
  })

  afterEach(() => {
    if (wrapper) wrapper.unmount()
  })

  describe('Initial rendering', () => {
    it('renders name, user, and VM fields', async () => {
      await createWrapper()

      expect(wrapper.findAll('.form-control').length).toBe(1)
      expect(wrapper.findAll('.search-control').length).toBe(2)
    })

    it('does not show connection profile buttons initially', async () => {
      await createWrapper()

      const protocolButtons = wrapper.findAll('.grid button[type="button"]')
      expect(protocolButtons.length).toBe(0)
    })

    it('does not show error message initially', async () => {
      await createWrapper()

      expect(wrapper.find('.text-red-500').exists()).toBe(false)
    })
  })

  describe('VM selection triggers connection loading', () => {
    it('fetches connections when VM is selected', async () => {
      await createWrapper()

      wrapper.vm.selectedVm = VM_ID
      await flushPromises()

      expect(mockListByObject).toHaveBeenCalledWith('VirtualMachine', VM_ID, {
        limit: 100,
      })
    })

    it('clears connections when VM is deselected', async () => {
      await createWrapper()

      wrapper.vm.selectedVm = VM_ID
      await flushPromises()

      expect(wrapper.vm.connections.length).toBe(2)

      wrapper.vm.selectedVm = null
      await flushPromises()

      expect(wrapper.vm.connections.length).toBe(0)
    })

    it('resets connection_profile when VM changes', async () => {
      await createWrapper()

      wrapper.vm.selectedVm = VM_ID
      await flushPromises()

      wrapper.vm.guacamole.connection_profile = PROFILE_RDP_ID

      wrapper.vm.selectedVm = 'other-vm-id'
      await flushPromises()

      expect(wrapper.vm.guacamole.connection_profile).toBeNull()
    })
  })

  describe('Connection profile display', () => {
    it('shows protocol buttons when VM has connections', async () => {
      await createWrapper()

      wrapper.vm.selectedVm = VM_ID
      await flushPromises()

      const protocolButtons = wrapper.findAll('.grid button[type="button"]')
      expect(protocolButtons.length).toBe(2)
    })

    it('displays correct protocol labels', async () => {
      await createWrapper()

      wrapper.vm.selectedVm = VM_ID
      await flushPromises()

      const buttons = wrapper.findAll('.grid button[type="button"]')
      const labels = buttons.map((b) => b.find('.font-semibold').text())
      expect(labels).toEqual(['RDP', 'SSH'])
    })

    it('displays port numbers', async () => {
      await createWrapper()

      wrapper.vm.selectedVm = VM_ID
      await flushPromises()

      const buttons = wrapper.findAll('.grid button[type="button"]')
      const ports = buttons.map((b) => b.find('.text-xs').text())
      expect(ports).toEqual(['Port 3389', 'Port 22'])
    })

    it('selects profile when button is clicked', async () => {
      await createWrapper()

      wrapper.vm.selectedVm = VM_ID
      await flushPromises()

      const buttons = wrapper.findAll('.grid button[type="button"]')
      await buttons[1].trigger('click')

      expect(wrapper.vm.guacamole.connection_profile).toBe(PROFILE_SSH_ID)
    })

    it('highlights the selected button', async () => {
      await createWrapper()

      wrapper.vm.selectedVm = VM_ID
      await flushPromises()

      const buttons = wrapper.findAll('.grid button[type="button"]')
      await buttons[0].trigger('click')
      await flushPromises()

      expect(buttons[0].classes()).toContain('border-blue-500')
    })
  })

  describe('Auto-select with single connection', () => {
    it('auto-selects when only one connection profile exists', async () => {
      mockListByObject.mockResolvedValueOnce({
        pageDetails: {
          page: 1,
          perPage: 100,
          pageCount: 1,
          totalCount: 1,
        },
        items: [rdpProfile],
      })

      await createWrapper()

      wrapper.vm.selectedVm = VM_ID
      await flushPromises()

      expect(wrapper.vm.guacamole.connection_profile).toBe(PROFILE_RDP_ID)
    })
  })

  describe('No connections found', () => {
    it('shows error when VM has no connection profiles', async () => {
      mockListByObject.mockResolvedValueOnce({
        pageDetails: {
          page: 1,
          perPage: 100,
          pageCount: 1,
          totalCount: 0,
        },
        items: [],
      })

      await createWrapper()

      wrapper.vm.selectedVm = VM_ID
      await flushPromises()

      expect(wrapper.find('.text-red-500').exists()).toBe(true)
    })

    it('hides error when a new VM is selected with profiles', async () => {
      mockListByObject
        .mockResolvedValueOnce({
          pageDetails: {
            page: 1,
            perPage: 100,
            pageCount: 1,
            totalCount: 0,
          },
          items: [],
        })
        .mockResolvedValueOnce({
          pageDetails: {
            page: 1,
            perPage: 100,
            pageCount: 1,
            totalCount: 1,
          },
          items: [rdpProfile],
        })

      await createWrapper()

      wrapper.vm.selectedVm = VM_ID
      await flushPromises()
      expect(wrapper.find('.text-red-500').exists()).toBe(true)

      wrapper.vm.selectedVm = 'other-vm-id'
      await flushPromises()
      expect(wrapper.find('.text-red-500').exists()).toBe(false)
    })
  })

  describe('Query parameter support', () => {
    it('pre-selects VM from vmId query parameter', async () => {
      await createWrapper({ vmId: VM_ID })

      expect(wrapper.vm.selectedVm).toBe(VM_ID)
      expect(mockListByObject).toHaveBeenCalledWith('VirtualMachine', VM_ID, {
        limit: 100,
      })
    })

    it('resolves VM from connection_profile query parameter', async () => {
      await createWrapper({ connection_profile: PROFILE_RDP_ID })

      expect(mockConnectionGet).toHaveBeenCalledWith(PROFILE_RDP_ID)
      expect(wrapper.vm.selectedVm).toBe(VM_ID)
    })

    it('pre-fills name from query parameter', async () => {
      await createWrapper({ name: 'My Connection' })

      expect(wrapper.vm.guacamole.name).toBe('My Connection')
    })

    it('pre-fills userId from query parameter', async () => {
      await createWrapper({ userId: 'user-123' })

      expect(wrapper.vm.guacamole.userId).toBe('user-123')
    })

    it('handles missing connection_profile gracefully', async () => {
      mockConnectionGet.mockRejectedValueOnce(new Error('Not found'))

      await createWrapper({ connection_profile: 'invalid-id' })

      expect(wrapper.vm.selectedVm).toBeNull()
    })
  })

  describe('Form submission', () => {
    // Call submit() directly on the VM to avoid jsdom preventDefault issues
    it('submits with correct data', async () => {
      await createWrapper()

      wrapper.vm.guacamole.name = 'Test Connection'
      wrapper.vm.guacamole.userId = 'user-123'
      wrapper.vm.selectedVm = VM_ID
      await flushPromises()

      wrapper.vm.guacamole.connection_profile = PROFILE_RDP_ID

      await wrapper.vm.submit()
      await flushPromises()

      expect(mockGuacamoleCreate).toHaveBeenCalledWith({
        name: 'Test Connection',
        userId: 'user-123',
        connection_profile: PROFILE_RDP_ID,
      })
    })

    it('shows success toast and navigates on success', async () => {
      await createWrapper()

      wrapper.vm.guacamole.name = 'Test'
      wrapper.vm.guacamole.userId = 'user-123'
      wrapper.vm.guacamole.connection_profile = PROFILE_RDP_ID

      await wrapper.vm.submit()
      await flushPromises()

      expect(mockToastSuccess).toHaveBeenCalled()
      expect(mockFetchPermissions).toHaveBeenCalled()
      expect(mockRouterPush).toHaveBeenCalledWith({
        path: '/guacamoles/guac-new-123',
      })
    })

    it('shows error toast on failure', async () => {
      mockGuacamoleCreate.mockRejectedValueOnce({
        response: { data: { detail: 'Duplicate name' } },
      })

      await createWrapper()

      wrapper.vm.guacamole.name = 'Test'
      wrapper.vm.guacamole.userId = 'user-123'
      wrapper.vm.guacamole.connection_profile = PROFILE_RDP_ID

      await wrapper.vm.submit()
      await flushPromises()

      expect(mockToastError).toHaveBeenCalled()
      expect(mockRouterPush).not.toHaveBeenCalled()
    })
  })

  describe('Submit button disabled state', () => {
    it('is disabled when no fields are filled', async () => {
      await createWrapper()

      const submitBtn = wrapper
        .findAll('.base-button')
        .find((b) => b.attributes('type') === 'submit')
      expect(submitBtn.attributes('disabled')).toBeDefined()
    })

    it('is disabled when only name is filled', async () => {
      await createWrapper()
      wrapper.vm.guacamole.name = 'Test'
      await flushPromises()

      const submitBtn = wrapper
        .findAll('.base-button')
        .find((b) => b.attributes('type') === 'submit')
      expect(submitBtn.attributes('disabled')).toBeDefined()
    })

    it('is disabled when connection profile is missing', async () => {
      await createWrapper()
      wrapper.vm.guacamole.name = 'Test'
      wrapper.vm.guacamole.userId = 'user-123'
      wrapper.vm.selectedVm = VM_ID
      await flushPromises()

      // connection_profile not yet selected
      wrapper.vm.guacamole.connection_profile = null
      await flushPromises()

      const submitBtn = wrapper
        .findAll('.base-button')
        .find((b) => b.attributes('type') === 'submit')
      expect(submitBtn.attributes('disabled')).toBeDefined()
    })

    it('is disabled when VM has no connection profiles', async () => {
      mockListByObject.mockResolvedValueOnce({
        pageDetails: {
          page: 1,
          perPage: 100,
          pageCount: 1,
          totalCount: 0,
        },
        items: [],
      })

      await createWrapper()
      wrapper.vm.guacamole.name = 'Test'
      wrapper.vm.guacamole.userId = 'user-123'
      wrapper.vm.selectedVm = VM_ID
      await flushPromises()

      const submitBtn = wrapper
        .findAll('.base-button')
        .find((b) => b.attributes('type') === 'submit')
      expect(submitBtn.attributes('disabled')).toBeDefined()
    })

    it('is enabled when all fields are filled', async () => {
      await createWrapper()
      wrapper.vm.guacamole.name = 'Test'
      wrapper.vm.guacamole.userId = 'user-123'
      wrapper.vm.selectedVm = VM_ID
      await flushPromises()

      wrapper.vm.guacamole.connection_profile = PROFILE_RDP_ID
      await flushPromises()

      const submitBtn = wrapper
        .findAll('.base-button')
        .find((b) => b.attributes('type') === 'submit')
      expect(submitBtn.attributes('disabled')).toBeUndefined()
    })
  })
})
