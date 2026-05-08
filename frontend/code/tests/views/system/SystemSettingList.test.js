import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, ref } from 'vue'

const { mockList, mockUpdate, mockLoadSettings, mockToast } = vi.hoisted(
  () => ({
    mockList: vi.fn().mockResolvedValue({
      pageDetails: { page: 1, perPage: 100, pageCount: 1, totalCount: 3 },
      items: [
        {
          id: 'setting-1',
          key: 'app.maintenance_mode',
          value: 'false',
          type: 'bool',
          visibility: 'admins',
          description: 'Maintenance mode toggle',
          updatedAt: '2025-01-15T10:30:00',
          updatedById: 'user-1',
          updatedBy: 'Admin User',
        },
        {
          id: 'setting-2',
          key: 'app.max_upload_size',
          value: '1048576',
          type: 'int',
          visibility: 'admins',
          description: 'Max upload size in bytes',
          updatedAt: '2025-01-10T08:00:00',
          updatedById: 'user-1',
          updatedBy: 'Admin User',
        },
        {
          id: 'setting-3',
          key: 'app.internal_version',
          value: '4.2.0',
          type: 'str',
          visibility: 'internal',
          description: 'Internal version string',
          updatedAt: '2025-01-01T00:00:00',
          updatedById: 'user-1',
          updatedBy: 'System',
        },
      ],
    }),
    mockUpdate: vi.fn().mockResolvedValue({ success: true }),
    mockLoadSettings: vi.fn(),
    mockToast: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
    },
  }),
)

vi.mock('@/services', () => ({
  default: {
    system: {
      list: mockList,
      update: mockUpdate,
    },
  },
}))

vi.mock('@/stores/main', () => ({
  useMainStore: vi.fn(() => ({
    loadSettings: mockLoadSettings,
  })),
}))

vi.mock('@/utils/dataUtils', () => ({
  checkObjectPermissions: vi.fn().mockResolvedValue({}),
  usePermissionRefs: vi.fn().mockReturnValue({
    canEdit: true,
  }),
  exportJsonFile: vi.fn().mockResolvedValue(undefined),
  formatDate: vi.fn((val) => val || ''),
  formatSettingValue: vi.fn((type, val) => val),
  formatSystemSettingVisibility: vi.fn((v) => {
    const map = {
      public: 'Öffentlich',
      authenticated: 'Angemeldet',
      admins: 'Admins',
      internal: 'Intern',
    }
    return map[v] || v
  }),
  getHTMLInputType: vi.fn((type) => {
    if (type === 'bool') return 'boolean'
    if (type === 'int' || type === 'float') return 'number'
    return 'text'
  }),
  getUserLink: vi.fn(() => null),
  resolveFieldFromLookup: vi.fn().mockResolvedValue(undefined),
  valueValidator: vi.fn(() => true),
  visibilitySystemSettingFilter: vi.fn(() => []),
}))

vi.mock('@/utils/icons', () => ({
  systemSettingVisibilityIcon: vi.fn(() => 'mocked-icon-path'),
}))

vi.mock('@/utils/objectColors', () => ({
  visibilityColorSystemSetting: vi.fn(() => 'info'),
}))

vi.mock('@/utils/tooltips', () => ({
  systemSettingVisibilityTooltip: vi.fn(() => 'tooltip'),
}))

vi.mock('@/utils/pagination', () => ({
  usePaginationList: vi.fn(({ fetch }) => {
    // Call fetch on setup to simulate onMounted behavior
    Promise.resolve().then(() => fetch())
    return {
      currentPage: ref(1),
      perPage: ref(100),
      sortColumnKey: ref('key'),
      sortDirection: ref('asc'),
      searchField: ref(null),
      searchValue: ref(null),
      handlePaginationChanged: vi.fn(),
      handleSortOrderChanged: vi.fn(),
      handleSearch: vi.fn(),
      initialFetch: vi.fn(),
    }
  }),
}))

vi.mock('vue-toastification', () => ({
  useToast: vi.fn(() => mockToast),
}))

const stubs = {
  LayoutAuthenticated: {
    template: '<div class="layout"><slot /></div>',
  },
  SectionMain: {
    template: '<div class="section-main"><slot /></div>',
  },
  SectionTitleLineWithButton: {
    template: '<div class="section-title"><slot /></div>',
  },
  CardBox: {
    template: '<div class="card-box"><slot /></div>',
  },
  CardBoxModal: {
    template: `
      <div v-if="modelValue" class="modal" :data-title="title">
        <slot />
        <button
          v-if="hasCancel || hasButton !== false"
          class="submit-btn"
          :disabled="disabled"
          @click="$emit('form-submitted')"
        >{{ buttonLabel }}</button>
        <button class="cancel-btn" @click="$emit('cancel')">Cancel</button>
      </div>
    `,
    props: [
      'modelValue',
      'title',
      'button',
      'buttonLabel',
      'hasCancel',
      'hasButton',
      'disabled',
      'customClass',
    ],
    emits: ['update:modelValue', 'form-submitted', 'cancel'],
  },
  BaseTable: {
    name: 'BaseTable',
    template: '<table class="base-table" />',
    props: [
      'currentPage',
      'perPage',
      'itemsTotal',
      'data',
      'sortColumnKey',
      'sortDirection',
      'loading',
      'createdColumnEnabled',
      'objectModel',
      'buttons',
      'emitEditObject',
      'emitViewObject',
      'columns',
    ],
    emits: [
      'view-object',
      'edit-object',
      'search-triggered',
      'sort-order-changed',
      'pagination-changed',
    ],
  },
  FormField: {
    template: '<div class="form-field"><slot /></div>',
    props: ['label', 'help'],
  },
  FormControl: {
    template:
      '<input class="form-control" :value="modelValue" :disabled="disabled" @input="$emit(\'update:modelValue\', $event.target.value)" />',
    props: [
      'modelValue',
      'icon',
      'disabled',
      'type',
      'maxlength',
      'validate',
      'step',
      'required',
    ],
    emits: ['update:modelValue'],
  },
  BaseButton: {
    template:
      '<button class="base-button" :data-label="label" @click="$emit(\'click\')">{{ label }}</button>',
    props: ['icon', 'label', 'color', 'roundedFull', 'small', 'outline'],
    emits: ['click'],
  },
  BaseIcon: {
    template: '<span class="icon" />',
    props: ['path', 'size', 'w', 'h'],
  },
  BaseMarkdown: {
    template: '<div class="markdown">{{ modelValue }}</div>',
    props: ['modelValue', 'action'],
  },
  NotificationBar: {
    template: '<div class="notification-bar"><slot /></div>',
    props: ['color', 'icon', 'dismissable'],
  },
  PillTag: {
    template:
      '<span class="pill-tag" :data-label="label" :data-color="color">{{ label }}</span>',
    props: ['label', 'color', 'icon', 'disabled', 'small'],
  },
}

const tooltipDirectiveStub = {
  mounted() {},
  updated() {},
  beforeUnmount() {},
}

import SystemSettingList from '@/views/system/SystemSettingList.vue'

describe('SystemSettingList', () => {
  let wrapper

  const createWrapper = async () => {
    wrapper = mount(SystemSettingList, {
      global: {
        stubs,
        directives: {
          tooltip: tooltipDirectiveStub,
        },
      },
    })
    await flushPromises()
    return wrapper
  }

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders the component', async () => {
      await createWrapper()
      expect(wrapper.exists()).toBe(true)
    })

    it('renders the page title section', async () => {
      await createWrapper()
      expect(wrapper.find('.section-title').exists()).toBe(true)
    })

    it('renders the info notification bar', async () => {
      await createWrapper()
      const bar = wrapper.find('.notification-bar')
      expect(bar.exists()).toBe(true)
      expect(bar.text()).toContain('globale Einstellungen')
    })

    it('renders the base table', async () => {
      await createWrapper()
      expect(wrapper.find('.base-table').exists()).toBe(true)
    })

    it('fetches settings on mount', async () => {
      await createWrapper()
      expect(mockList).toHaveBeenCalled()
    })
  })

  describe('View Modal', () => {
    it('opens view modal via openViewModal', async () => {
      await createWrapper()

      wrapper.vm.openViewModal({ id: 'setting-1' })
      await nextTick()

      const modals = wrapper.findAll('.modal')
      const viewModal = modals.find(
        (m) => m.attributes('data-title') === 'Einstellung ansehen',
      )
      expect(viewModal).toBeDefined()
    })

    it('displays the setting key in the view modal', async () => {
      await createWrapper()

      wrapper.vm.openViewModal({ id: 'setting-1' })
      await nextTick()

      expect(wrapper.text()).toContain('app.maintenance_mode')
    })

    it('displays the description in the view modal', async () => {
      await createWrapper()

      wrapper.vm.openViewModal({ id: 'setting-1' })
      await nextTick()

      const markdown = wrapper.find('.markdown')
      expect(markdown.exists()).toBe(true)
      expect(markdown.text()).toContain('Maintenance mode toggle')
    })

    it('displays the data type in the view modal', async () => {
      await createWrapper()

      wrapper.vm.openViewModal({ id: 'setting-1' })
      await nextTick()

      expect(wrapper.text()).toContain('bool')
    })

    it('displays the visibility as PillTag', async () => {
      await createWrapper()

      wrapper.vm.openViewModal({ id: 'setting-1' })
      await nextTick()

      const pillTag = wrapper.find(
        '.modal[data-title="Einstellung ansehen"] .pill-tag',
      )
      expect(pillTag.exists()).toBe(true)
      expect(pillTag.attributes('data-label')).toBe('Admins')
    })

    it('displays boolean value as Aktiv/Inaktiv', async () => {
      await createWrapper()

      wrapper.vm.openViewModal({ id: 'setting-1' })
      await nextTick()

      // setting-1 has value 'false' -> Inaktiv (false)
      expect(wrapper.text()).toContain('Inaktiv (false)')
    })

    it('displays non-boolean value as text', async () => {
      await createWrapper()

      wrapper.vm.openViewModal({ id: 'setting-2' })
      await nextTick()

      expect(wrapper.text()).toContain('1048576')
    })

    it('displays audit trail information', async () => {
      await createWrapper()

      wrapper.vm.openViewModal({ id: 'setting-1' })
      await nextTick()

      expect(wrapper.text()).toContain('Letzte Änderung')
      expect(wrapper.text()).toContain('Geändert von')
      expect(wrapper.text()).toContain('Admin User')
    })

    it('shows edit button for non-internal settings when user has permission', async () => {
      await createWrapper()

      wrapper.vm.openViewModal({ id: 'setting-1' })
      await nextTick()

      const editBtn = wrapper.find(
        '.modal[data-title="Einstellung ansehen"] .base-button[data-label="Bearbeiten"]',
      )
      expect(editBtn.exists()).toBe(true)
    })

    it('hides edit button for internal settings', async () => {
      await createWrapper()

      wrapper.vm.openViewModal({ id: 'setting-3' })
      await nextTick()

      const viewModal = wrapper.find('.modal[data-title="Einstellung ansehen"]')
      const editBtn = viewModal.find('.base-button[data-label="Bearbeiten"]')
      expect(editBtn.exists()).toBe(false)
    })

    it('does not show footer buttons (no hasButton/hasCancel)', async () => {
      await createWrapper()

      wrapper.vm.openViewModal({ id: 'setting-1' })
      await nextTick()

      const viewModal = wrapper.find('.modal[data-title="Einstellung ansehen"]')
      // The CardBoxModal stub only renders submit-btn when hasCancel or hasButton !== false
      // View modal has hasButton=false and hasCancel=false
      // Our stub condition: v-if="hasCancel || hasButton !== false"
      // hasCancel=false, hasButton=false -> false || (false !== false) -> false || false -> false
      const submitBtn = viewModal.find('.submit-btn')
      expect(submitBtn.exists()).toBe(false)
    })
  })

  describe('Edit Modal', () => {
    it('opens edit modal via openEditModal for non-internal settings', async () => {
      await createWrapper()

      wrapper.vm.openEditModal({ id: 'setting-1' })
      await nextTick()

      const editModal = wrapper.find('.modal[data-title="Einstellung ändern"]')
      expect(editModal.exists()).toBe(true)
    })

    it('redirects to view modal for internal settings', async () => {
      await createWrapper()

      wrapper.vm.openEditModal({ id: 'setting-3' })
      await nextTick()

      // Should open view modal instead
      const viewModal = wrapper.find('.modal[data-title="Einstellung ansehen"]')
      expect(viewModal.exists()).toBe(true)

      // Edit modal should NOT be open
      const editModal = wrapper.find('.modal[data-title="Einstellung ändern"]')
      expect(editModal.exists()).toBe(false)
    })

    it('displays the setting key in the edit modal header', async () => {
      await createWrapper()

      wrapper.vm.openEditModal({ id: 'setting-2' })
      await nextTick()

      const editModal = wrapper.find('.modal[data-title="Einstellung ändern"]')
      expect(editModal.text()).toContain('app.max_upload_size')
    })

    it('displays visibility PillTag in the edit modal', async () => {
      await createWrapper()

      wrapper.vm.openEditModal({ id: 'setting-2' })
      await nextTick()

      const pillTag = wrapper.find(
        '.modal[data-title="Einstellung ändern"] .pill-tag',
      )
      expect(pillTag.exists()).toBe(true)
    })

    it('displays the description in the edit modal', async () => {
      await createWrapper()

      wrapper.vm.openEditModal({ id: 'setting-2' })
      await nextTick()

      const editModal = wrapper.find('.modal[data-title="Einstellung ändern"]')
      const markdown = editModal.find('.markdown')
      expect(markdown.exists()).toBe(true)
      expect(markdown.text()).toContain('Max upload size in bytes')
    })

    it('displays the compact warning banner', async () => {
      await createWrapper()

      wrapper.vm.openEditModal({ id: 'setting-2' })
      await nextTick()

      const editModal = wrapper.find('.modal[data-title="Einstellung ändern"]')
      expect(editModal.text()).toContain('sofort aktiv')
    })

    it('shows FormControl input for non-boolean settings', async () => {
      await createWrapper()

      wrapper.vm.openEditModal({ id: 'setting-2' })
      await nextTick()

      const editModal = wrapper.find('.modal[data-title="Einstellung ändern"]')
      expect(editModal.find('.form-control').exists()).toBe(true)
    })

    it('shows toggle buttons for boolean settings', async () => {
      await createWrapper()

      wrapper.vm.openEditModal({ id: 'setting-1' })
      await nextTick()

      const editModal = wrapper.find('.modal[data-title="Einstellung ändern"]')
      const buttons = editModal.findAll('button[type="button"]')
      const toggleBtns = buttons.filter(
        (b) => b.text() === 'Aktiv' || b.text() === 'Inaktiv',
      )
      expect(toggleBtns.length).toBe(2)
    })

    it('toggles boolean value to true when Aktiv button is clicked', async () => {
      await createWrapper()

      wrapper.vm.openEditModal({ id: 'setting-1' })
      await nextTick()

      const editModal = wrapper.find('.modal[data-title="Einstellung ändern"]')
      const buttons = editModal.findAll('button[type="button"]')
      const aktivBtn = buttons.find((b) => b.text().includes('Aktiv'))

      await aktivBtn.trigger('click')
      expect(wrapper.vm.objSingle.value).toBe('true')
    })

    it('toggles boolean value to false when Inaktiv button is clicked', async () => {
      await createWrapper()

      wrapper.vm.openEditModal({ id: 'setting-1' })
      await nextTick()

      // First set to true
      wrapper.vm.objSingle.value = 'true'
      await nextTick()

      const editModal = wrapper.find('.modal[data-title="Einstellung ändern"]')
      const buttons = editModal.findAll('button[type="button"]')
      const inaktivBtn = buttons.find((b) => b.text().includes('Inaktiv'))

      await inaktivBtn.trigger('click')
      expect(wrapper.vm.objSingle.value).toBe('false')
    })

    it('calls editSetting on form submission', async () => {
      await createWrapper()

      wrapper.vm.openEditModal({ id: 'setting-2' })
      await nextTick()

      const submitBtn = wrapper.find(
        '.modal[data-title="Einstellung ändern"] .submit-btn',
      )
      await submitBtn.trigger('click')
      await flushPromises()

      expect(mockUpdate).toHaveBeenCalledWith('setting-2', '1048576')
    })

    it('shows success toast after saving', async () => {
      await createWrapper()

      wrapper.vm.openEditModal({ id: 'setting-2' })
      await nextTick()

      const submitBtn = wrapper.find(
        '.modal[data-title="Einstellung ändern"] .submit-btn',
      )
      await submitBtn.trigger('click')
      await flushPromises()

      expect(mockToast.success).toHaveBeenCalledWith(
        'System Einstellung erfolgreich bearbeitet',
      )
    })

    it('reloads settings in store after saving', async () => {
      await createWrapper()

      wrapper.vm.openEditModal({ id: 'setting-2' })
      await nextTick()

      const submitBtn = wrapper.find(
        '.modal[data-title="Einstellung ändern"] .submit-btn',
      )
      await submitBtn.trigger('click')
      await flushPromises()

      expect(mockLoadSettings).toHaveBeenCalled()
    })

    it('shows error toast on save failure', async () => {
      mockUpdate.mockRejectedValueOnce(new Error('Network error'))

      await createWrapper()

      wrapper.vm.openEditModal({ id: 'setting-2' })
      await nextTick()

      const submitBtn = wrapper.find(
        '.modal[data-title="Einstellung ändern"] .submit-btn',
      )
      await submitBtn.trigger('click')
      await flushPromises()

      expect(mockToast.error).toHaveBeenCalled()
    })

    it('resets form on cancel', async () => {
      await createWrapper()

      wrapper.vm.openEditModal({ id: 'setting-2' })
      await nextTick()

      const cancelBtn = wrapper.find(
        '.modal[data-title="Einstellung ändern"] .cancel-btn',
      )
      await cancelBtn.trigger('click')

      expect(wrapper.vm.objSingle).toBe('')
    })
  })

  describe('View to Edit Transition', () => {
    it('closes view modal and opens edit modal via switchToEdit', async () => {
      vi.useFakeTimers()
      await createWrapper()

      wrapper.vm.openViewModal({ id: 'setting-1' })
      await nextTick()

      // Click the edit button inside view modal
      const editBtn = wrapper.find(
        '.modal[data-title="Einstellung ansehen"] .base-button[data-label="Bearbeiten"]',
      )
      await editBtn.trigger('click')

      // View modal should close immediately
      expect(wrapper.vm.modals.viewSetting.value).toBe(false)

      // Edit modal opens after delay
      vi.advanceTimersByTime(160)
      await nextTick()

      expect(wrapper.vm.modals.editSetting.value).toBe(true)

      vi.useRealTimers()
    })
  })

  describe('Computed Properties', () => {
    it('isInternalSetting returns true for internal visibility', async () => {
      await createWrapper()

      wrapper.vm.openViewModal({ id: 'setting-3' })
      await nextTick()

      expect(wrapper.vm.isInternalSetting).toBe(true)
    })

    it('isInternalSetting returns false for non-internal visibility', async () => {
      await createWrapper()

      wrapper.vm.openViewModal({ id: 'setting-1' })
      await nextTick()

      expect(wrapper.vm.isInternalSetting).toBe(false)
    })

    it('booleanDisplayValue returns true for value "true"', async () => {
      await createWrapper()

      wrapper.vm.openViewModal({ id: 'setting-1' })
      wrapper.vm.objSingle.value = 'true'
      await nextTick()

      expect(wrapper.vm.booleanDisplayValue).toBe(true)
    })

    it('booleanDisplayValue returns false for value "false"', async () => {
      await createWrapper()

      wrapper.vm.openViewModal({ id: 'setting-1' })
      wrapper.vm.objSingle.value = 'false'
      await nextTick()

      expect(wrapper.vm.booleanDisplayValue).toBe(false)
    })

    it('canEditSetting returns true when user has edit permission and setting is not internal', async () => {
      await createWrapper()

      wrapper.vm.openViewModal({ id: 'setting-1' })
      await nextTick()

      expect(wrapper.vm.canEditSetting).toBe(true)
    })

    it('canEditSetting returns false for internal settings', async () => {
      await createWrapper()

      wrapper.vm.openViewModal({ id: 'setting-3' })
      await nextTick()

      expect(wrapper.vm.canEditSetting).toBe(false)
    })

    it('settingUpdatable returns true when setting has valid data', async () => {
      await createWrapper()

      wrapper.vm.openEditModal({ id: 'setting-2' })
      await nextTick()

      expect(wrapper.vm.settingUpdatable).toBe(true)
    })

    it('settingUpdatable returns false when key is missing', async () => {
      await createWrapper()

      wrapper.vm.objSingle = { id: 'x', key: '', value: 'abc' }
      await nextTick()

      expect(wrapper.vm.settingUpdatable).toBe(false)
    })
  })

  describe('Table Boolean Formatter', () => {
    it('passes formatter that converts true to Aktiv', async () => {
      await createWrapper()

      const table = wrapper.findComponent({ name: 'BaseTable' })
      const columns = table.props('columns')
      const valueColumn = columns.find((c) => c.key === 'value')

      expect(valueColumn.formatter('true')).toBe('Aktiv')
    })

    it('passes formatter that converts false to Inaktiv', async () => {
      await createWrapper()

      const table = wrapper.findComponent({ name: 'BaseTable' })
      const columns = table.props('columns')
      const valueColumn = columns.find((c) => c.key === 'value')

      expect(valueColumn.formatter('false')).toBe('Inaktiv')
    })

    it('passes formatter that returns other values as string', async () => {
      await createWrapper()

      const table = wrapper.findComponent({ name: 'BaseTable' })
      const columns = table.props('columns')
      const valueColumn = columns.find((c) => c.key === 'value')

      expect(valueColumn.formatter('1048576')).toBe('1048576')
    })
  })
})
