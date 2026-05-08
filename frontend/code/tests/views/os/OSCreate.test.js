import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

const {
  mockCreate,
  mockVendorSearch,
  mockVendorGetName,
  mockCheckObjectPermissions,
  mockPermissionRefs,
} = vi.hoisted(() => {
  const refs = {
    canCreate: false,
  }
  return {
    mockCreate: vi.fn().mockResolvedValue({ id: 'os-123' }),
    mockVendorSearch: vi.fn().mockResolvedValue({ items: [] }),
    mockVendorGetName: vi.fn().mockResolvedValue('Mock Vendor'),
    mockCheckObjectPermissions: vi.fn().mockResolvedValue(undefined),
    mockPermissionRefs: refs,
  }
})

vi.mock('@/services', () => ({
  default: {
    os: { create: mockCreate },
    vendors: {
      search: mockVendorSearch,
      getName: mockVendorGetName,
    },
  },
}))

vi.mock('@/stores/main', () => ({
  useMainStore: vi.fn().mockReturnValue({
    fetchPermissions: vi.fn(),
  }),
}))

vi.mock('@/router', () => ({
  default: {
    push: vi.fn(),
    back: vi.fn(),
  },
}))

vi.mock('vue-router', () => ({
  useRoute: vi.fn().mockReturnValue({ query: {}, params: {} }),
  onBeforeRouteLeave: vi.fn(),
}))

vi.mock('vue-toastification', () => ({
  useToast: vi.fn().mockReturnValue({
    success: vi.fn(),
    error: vi.fn(),
  }),
}))

vi.mock('@/utils/dataUtils', () => ({
  checkObjectPermissions: mockCheckObjectPermissions,
  usePermissionRefs: vi.fn().mockReturnValue(mockPermissionRefs),
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
    template:
      '<form class="card-box" @submit.prevent="$emit(\'submit\')"><slot /><slot name="footer" /></form>',
  },
  FormField: {
    template: '<div class="form-field"><slot /></div>',
  },
  FormControl: {
    template:
      '<input class="form-control" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
    props: ['modelValue', 'icon', 'placeholder', 'required', 'autofocus'],
  },
  SearchControl: {
    template: '<div class="search-control" />',
    props: ['modelValue', 'icon', 'fetchData', 'fetchSelected', 'required'],
    emits: ['update:modelValue', 'setRef'],
  },
  BaseButton: {
    template:
      '<button class="base-button" :type="type" :disabled="disabled" :data-icon="icon">{{ label }}</button>',
    props: [
      'type',
      'color',
      'label',
      'disabled',
      'outline',
      'icon',
      'small',
      'roundedFull',
    ],
  },
  BaseButtons: {
    template: '<div class="base-buttons"><slot /></div>',
  },
  UnsavedChangesModal: {
    template: '<div class="unsaved-modal" />',
    props: ['modelValue'],
  },
  VendorCreateModal: {
    template: '<div class="vendor-create-modal" v-if="modelValue" />',
    props: ['modelValue'],
    emits: ['update:modelValue', 'created'],
  },
}

import OSCreate from '@/views/os/OSCreate.vue'

describe('OSCreate - Inline Vendor Creation', () => {
  let wrapper

  const createWrapper = async (permCanCreate = false) => {
    mockPermissionRefs.canCreate = permCanCreate
    wrapper = mount(OSCreate, {
      global: {
        stubs,
        directives: {
          tooltip: () => {},
        },
      },
    })
    await flushPromises()
    return wrapper
  }

  afterEach(() => {
    if (wrapper) wrapper.unmount()
    vi.clearAllMocks()
    mockPermissionRefs.canCreate = false
  })

  describe('Permission check on mount', () => {
    it('calls checkObjectPermissions for vendors create', async () => {
      await createWrapper()

      expect(mockCheckObjectPermissions).toHaveBeenCalledWith(
        'vendors',
        '*',
        mockPermissionRefs,
        [],
        ['canCreate'],
      )
    })
  })

  describe('Add vendor button visibility', () => {
    it('does not show add vendor button without canCreate permission', async () => {
      await createWrapper(false)

      const buttons = wrapper.findAll('.base-button')
      const addBtn = buttons.find((b) =>
        b
          .attributes('data-icon')
          ?.includes('M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z'),
      )
      expect(addBtn).toBeUndefined()
    })

    it('shows add vendor button with canCreate permission', async () => {
      await createWrapper(true)

      const buttons = wrapper.findAll('.base-button')
      const addBtn = buttons.find((b) =>
        b
          .attributes('data-icon')
          ?.includes('M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z'),
      )
      expect(addBtn).toBeDefined()
    })
  })

  describe('Vendor create modal', () => {
    it('does not show modal initially', async () => {
      await createWrapper(true)
      expect(wrapper.find('.vendor-create-modal').exists()).toBe(false)
    })

    it('opens modal when add button is clicked', async () => {
      await createWrapper(true)

      const buttons = wrapper.findAll('.base-button')
      const addBtn = buttons.find((b) =>
        b
          .attributes('data-icon')
          ?.includes('M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z'),
      )
      await addBtn.trigger('click')

      expect(wrapper.find('.vendor-create-modal').exists()).toBe(true)
    })

    it('sets vendor id on entity after vendor creation', async () => {
      await createWrapper(true)
      wrapper.vm.onVendorCreated({
        id: 'created-vendor-id',
        name: 'Created Vendor',
      })

      expect(wrapper.vm.os.vendor).toBe('created-vendor-id')
    })
  })
})
