import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { computed, ref } from 'vue'

import CSVUpload from '@/components/CSVUpload.vue'
import { CSV_ROW_STATUS } from '@/utils/csvImportStatus'

// ── Mock child components ────────────────────────────────
vi.mock('@/components/BaseButton.vue', () => ({
  default: {
    name: 'BaseButton',
    template:
      '<button :disabled="disabled" :data-label="label" @click="$emit(\'click\')"><slot />{{ label }}</button>',
    props: [
      'color',
      'icon',
      'small',
      'disabled',
      'label',
      'roundedFull',
      'type',
    ],
    emits: ['click'],
  },
}))

vi.mock('@/components/BaseButtons.vue', () => ({
  default: {
    name: 'BaseButtons',
    template: '<div class="base-buttons"><slot /></div>',
  },
}))

vi.mock('@/components/BaseIcon.vue', () => ({
  default: {
    name: 'BaseIcon',
    template: '<span class="icon"></span>',
    props: ['path', 'size', 'w', 'h'],
  },
}))

vi.mock('@/components/FormControl.vue', () => ({
  default: {
    name: 'FormControl',
    template: '<select><slot /></select>',
    props: ['id', 'modelValue', 'required', 'disabled', 'type', 'options'],
    emits: ['update:modelValue'],
  },
}))

vi.mock('@/components/NotificationBar.vue', () => ({
  default: {
    name: 'NotificationBar',
    template: '<div class="notification-bar"><slot /></div>',
    props: ['dismissable', 'color', 'icon'],
  },
}))

vi.mock('@/components/PillTag.vue', () => ({
  default: {
    name: 'PillTag',
    template: '<span class="pill-tag">{{ label }}</span>',
    props: ['label', 'color', 'icon', 'disabled', 'small'],
  },
}))

vi.mock('@/colors.js', () => ({
  colorsBgLight: {},
  colorsOutline: {},
  getButtonColor: vi.fn(() => ''),
}))

// ── Mock useCSVImport composable ─────────────────────────
const mockState = {}

function createMockState(overrides = {}) {
  return {
    allowRetry: ref(false),
    csvHeaders: ref([]),
    fileName: ref(''),
    fileSize: ref(0),
    hasImportStarted: ref(false),
    headerMapping: ref({}),
    isImporting: ref(false),
    limitExceeded: ref(false),
    noFile: ref(true),
    parseError: ref(''),
    parsedRowCount: ref(0),
    rawRows: ref([]),
    rowError: ref([]),
    rowStatus: ref([]),
    canConfirm: computed(() => false),
    currentStep: computed(() => 1),
    failedCount: computed(() => 0),
    hasDuplicateMappings: computed(() => false),
    importingCount: computed(() => 0),
    isImportFinished: computed(() => false),
    progressPercent: computed(() => 0),
    remainingCount: computed(() => 0),
    successCount: computed(() => 0),
    totalCount: computed(() => 0),
    confirmImport: vi.fn(),
    parseFile: vi.fn(),
    reset: vi.fn(),
    ...overrides,
  }
}

vi.mock('@/composables/useCSVImport', () => ({
  useCSVImport: vi.fn(() => mockState.current),
}))

const DEFAULT_PROPS = {
  requiredMappings: [
    { key: 'email', label: 'E-Mail' },
    { key: 'name', label: 'Name' },
  ],
  onImportConfirm: vi.fn(),
}

function createWrapper(props = {}, stateOverrides = {}) {
  mockState.current = createMockState(stateOverrides)
  return mount(CSVUpload, {
    props: { ...DEFAULT_PROPS, ...props },
    attachTo: document.body,
  })
}

describe('CSVUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Initial rendering (Step 1)', () => {
    it('renders the stepper with 4 steps', () => {
      const wrapper = createWrapper()
      const stepper = wrapper.find('[data-testid="stepper"]')
      expect(stepper.exists()).toBe(true)
      expect(stepper.text()).toContain('Hochladen')
      expect(stepper.text()).toContain('Zuordnen')
      expect(stepper.text()).toContain('Import')
      expect(stepper.text()).toContain('Ergebnis')
    })

    it('shows step 1 content and hides others via v-show', () => {
      const wrapper = createWrapper()
      const step1 = wrapper.find('[data-testid="step-1"]')
      const step2 = wrapper.find('[data-testid="step-2"]')
      const step3 = wrapper.find('[data-testid="step-3"]')
      const step4 = wrapper.find('[data-testid="step-4"]')

      expect(step1.isVisible()).toBe(true)
      expect(step2.isVisible()).toBe(false)
      expect(step3.isVisible()).toBe(false)
      expect(step4.isVisible()).toBe(false)
    })

    it('renders drag-and-drop zone', () => {
      const wrapper = createWrapper()
      const dropZone = wrapper.find('[data-testid="drop-zone"]')
      expect(dropZone.exists()).toBe(true)
      expect(dropZone.text()).toContain('Datei auswählen')
    })

    it('renders hidden file input', () => {
      const wrapper = createWrapper()
      const input = wrapper.find('[data-testid="file-input"]')
      expect(input.exists()).toBe(true)
      expect(input.attributes('type')).toBe('file')
      expect(input.attributes('accept')).toBe('.csv')
      expect(input.classes()).toContain('hidden')
    })

    it('shows upload instructions when no file', () => {
      const wrapper = createWrapper()
      expect(wrapper.text()).toContain('Datei auswählen:')
    })

    it('shows required columns', () => {
      const wrapper = createWrapper()
      const info = wrapper.find('[data-testid="required-columns"]')
      expect(info.exists()).toBe(true)
      expect(info.text()).toContain('Erforderliche Spalten')
      expect(info.text()).toContain('E-Mail')
      expect(info.text()).toContain('Name')
    })

    it('shows template download button', () => {
      const wrapper = createWrapper()
      const info = wrapper.find('[data-testid="required-columns"]')
      expect(info.text()).toContain('Vorlage')
    })
  })

  describe('Step 1 error states', () => {
    it('shows limit exceeded error', () => {
      const wrapper = createWrapper(
        { limit: 100 },
        {
          limitExceeded: ref(true),
          parsedRowCount: ref(250),
          currentStep: computed(() => 1),
        },
      )
      expect(wrapper.text()).toContain('250 Zeilen')
    })

    it('shows parse error', () => {
      const wrapper = createWrapper(
        {},
        {
          parseError: ref('Ungültiges Dateiformat'),
          currentStep: computed(() => 1),
        },
      )
      expect(wrapper.text()).toContain('Ungültiges Dateiformat')
    })
  })

  describe('Step 1: File info display', () => {
    it('shows file info after successful parse', () => {
      const wrapper = createWrapper(
        {},
        {
          noFile: ref(false),
          fileName: ref('users.csv'),
          fileSize: ref(4200),
          rawRows: ref([{ email: 'a@b.com' }]),
          currentStep: computed(() => 1),
        },
      )
      const fileInfo = wrapper.find('[data-testid="file-info"]')
      expect(fileInfo.exists()).toBe(true)
      expect(fileInfo.text()).toContain('users.csv')
    })
  })

  describe('Step 2: Column mapping', () => {
    it('shows step 2 when currentStep is 2', () => {
      const wrapper = createWrapper(
        {},
        {
          noFile: ref(false),
          rawRows: ref([{ email: 'a@b.com', name: 'Alice' }]),
          csvHeaders: ref(['email', 'name']),
          headerMapping: ref({ email: '', name: '' }),
          currentStep: computed(() => 2),
        },
      )
      const step2 = wrapper.find('[data-testid="step-2"]')
      expect(step2.isVisible()).toBe(true)
      expect(step2.text()).toContain('Spalten zuordnen')
    })

    it('renders a mapping control for each required mapping', () => {
      const wrapper = createWrapper(
        {},
        {
          noFile: ref(false),
          rawRows: ref([{ email: 'a@b.com', name: 'Alice' }]),
          csvHeaders: ref(['email', 'name']),
          headerMapping: ref({ email: '', name: '' }),
          currentStep: computed(() => 2),
        },
      )
      const labels = wrapper.findAll('[data-testid="step-2"] label')
      expect(labels.length).toBe(2)
      expect(labels[0].text()).toBe('E-Mail')
      expect(labels[1].text()).toBe('Name')
    })

    it('shows duplicate mapping warning', () => {
      const wrapper = createWrapper(
        {},
        {
          noFile: ref(false),
          rawRows: ref([{ email: 'a@b.com', name: 'Alice' }]),
          csvHeaders: ref(['email', 'name']),
          headerMapping: ref({ email: 'email', name: 'email' }),
          hasDuplicateMappings: computed(() => true),
          currentStep: computed(() => 2),
        },
      )
      expect(wrapper.text()).toContain('mehrfach zugeordnet')
    })

    it('disables "Vorschau" button when canConfirm is false', () => {
      const wrapper = createWrapper(
        {},
        {
          rawRows: ref([{ email: 'a@b.com' }]),
          csvHeaders: ref(['email']),
          headerMapping: ref({ email: '' }),
          canConfirm: computed(() => false),
          currentStep: computed(() => 2),
        },
      )
      const buttons = wrapper.findAll('[data-testid="step-2"] button')
      const previewBtn = buttons.find((b) =>
        b.attributes('data-label')?.includes('Vorschau'),
      )
      expect(previewBtn?.attributes('disabled')).toBeDefined()
    })

    it('does NOT disable "Vorschau" button on duplicate mappings', () => {
      const wrapper = createWrapper(
        {},
        {
          rawRows: ref([{ email: 'a@b.com', name: 'A' }]),
          csvHeaders: ref(['email', 'name']),
          headerMapping: ref({ email: 'email', name: 'email' }),
          canConfirm: computed(() => true),
          hasDuplicateMappings: computed(() => true),
          currentStep: computed(() => 2),
        },
      )
      const buttons = wrapper.findAll('[data-testid="step-2"] button')
      const previewBtn = buttons.find((b) =>
        b.attributes('data-label')?.includes('Vorschau'),
      )
      expect(previewBtn?.attributes('disabled')).toBeUndefined()
    })
  })

  describe('Step 3: Preview & Import', () => {
    it('shows step 3 content', () => {
      const wrapper = createWrapper(
        {},
        {
          hasImportStarted: ref(true),
          rawRows: ref([
            { email: 'a@b.com', name: 'Alice' },
            { email: 'c@d.com', name: 'Bob' },
          ]),
          csvHeaders: ref(['email', 'name']),
          rowStatus: ref([CSV_ROW_STATUS.PENDING, CSV_ROW_STATUS.PENDING]),
          rowError: ref(['', '']),
          currentStep: computed(() => 3),
        },
      )
      const step3 = wrapper.find('[data-testid="step-3"]')
      expect(step3.isVisible()).toBe(true)
    })

    it('renders scrollable preview table', () => {
      const wrapper = createWrapper(
        {},
        {
          hasImportStarted: ref(true),
          rawRows: ref([{ email: 'a@b.com', name: 'Alice' }]),
          csvHeaders: ref(['email', 'name']),
          rowStatus: ref([CSV_ROW_STATUS.PENDING]),
          rowError: ref(['']),
          currentStep: computed(() => 3),
        },
      )
      const table = wrapper.find('[data-testid="preview-table"]')
      expect(table.exists()).toBe(true)
      expect(table.classes()).toContain('overflow-y-auto')
    })

    it('shows "Import starten" button when not importing', () => {
      const wrapper = createWrapper(
        {},
        {
          hasImportStarted: ref(true),
          rawRows: ref([{ email: 'a@b.com' }]),
          csvHeaders: ref(['email']),
          rowStatus: ref([CSV_ROW_STATUS.PENDING]),
          rowError: ref(['']),
          isImporting: ref(false),
          isImportFinished: computed(() => false),
          currentStep: computed(() => 3),
        },
      )
      expect(wrapper.text()).toContain('Import starten')
    })

    it('renders PillTag for row status', () => {
      const wrapper = createWrapper(
        {},
        {
          hasImportStarted: ref(true),
          rawRows: ref([{ email: 'a@b.com' }]),
          csvHeaders: ref(['email']),
          rowStatus: ref([CSV_ROW_STATUS.PENDING]),
          rowError: ref(['']),
          currentStep: computed(() => 3),
        },
      )
      const pillTags = wrapper.findAll('.pill-tag')
      expect(pillTags.length).toBeGreaterThanOrEqual(1)
      expect(pillTags[0].text()).toBe('Ausstehend')
    })
  })

  describe('Step 4: Result', () => {
    it('shows step 4 with summary cards', () => {
      const wrapper = createWrapper(
        {},
        {
          hasImportStarted: ref(true),
          rawRows: ref([{ email: 'a@b.com' }, { email: 'c@d.com' }]),
          csvHeaders: ref(['email']),
          rowStatus: ref([CSV_ROW_STATUS.SUCCESS, CSV_ROW_STATUS.FAILED]),
          rowError: ref(['', 'Duplicate']),
          totalCount: computed(() => 2),
          successCount: computed(() => 1),
          failedCount: computed(() => 1),
          isImportFinished: computed(() => true),
          currentStep: computed(() => 4),
        },
      )
      const step4 = wrapper.find('[data-testid="step-4"]')
      expect(step4.isVisible()).toBe(true)
      expect(step4.text()).toContain('Gesamt')
      expect(step4.text()).toContain('Erfolgreich')
      expect(step4.text()).toContain('Fehlgeschlagen')
    })

    it('shows close button when no failures', () => {
      const wrapper = createWrapper(
        {},
        {
          hasImportStarted: ref(true),
          rawRows: ref([{ email: 'a@b.com' }]),
          csvHeaders: ref(['email']),
          rowStatus: ref([CSV_ROW_STATUS.SUCCESS]),
          rowError: ref(['']),
          totalCount: computed(() => 1),
          successCount: computed(() => 1),
          failedCount: computed(() => 0),
          isImportFinished: computed(() => true),
          currentStep: computed(() => 4),
        },
      )
      expect(wrapper.text()).toContain('Schließen')
    })

    it('shows retry button when there are failures', () => {
      const wrapper = createWrapper(
        {},
        {
          hasImportStarted: ref(true),
          allowRetry: ref(true),
          rawRows: ref([{ email: 'a@b.com' }]),
          csvHeaders: ref(['email']),
          rowStatus: ref([CSV_ROW_STATUS.FAILED]),
          rowError: ref(['Error']),
          totalCount: computed(() => 1),
          successCount: computed(() => 0),
          failedCount: computed(() => 1),
          isImportFinished: computed(() => true),
          currentStep: computed(() => 4),
        },
      )
      expect(wrapper.text()).toContain('Fehlerhafte erneut importieren')
    })

    it('shows failed rows table', () => {
      const wrapper = createWrapper(
        {},
        {
          hasImportStarted: ref(true),
          rawRows: ref([{ email: 'a@b.com' }]),
          csvHeaders: ref(['email']),
          rowStatus: ref([CSV_ROW_STATUS.FAILED]),
          rowError: ref(['Duplicate']),
          totalCount: computed(() => 1),
          successCount: computed(() => 0),
          failedCount: computed(() => 1),
          isImportFinished: computed(() => true),
          currentStep: computed(() => 4),
        },
      )
      const failedTable = wrapper.find('[data-testid="failed-table"]')
      expect(failedTable.exists()).toBe(true)
      expect(wrapper.text()).toContain('Fehlgeschlagene Zeilen')
    })

    it('shows neustart button', () => {
      const wrapper = createWrapper(
        {},
        {
          isImportFinished: computed(() => true),
          currentStep: computed(() => 4),
          totalCount: computed(() => 1),
          successCount: computed(() => 1),
          failedCount: computed(() => 0),
          rawRows: ref([{ email: 'a@b.com' }]),
          csvHeaders: ref(['email']),
          rowStatus: ref([CSV_ROW_STATUS.SUCCESS]),
          rowError: ref(['']),
        },
      )
      expect(wrapper.text()).toContain('Neustart')
    })
  })

  describe('Events', () => {
    it('emits "closed" when emitOnClose is true and close is triggered', async () => {
      const wrapper = createWrapper(
        { emitOnClose: true },
        {
          isImportFinished: computed(() => true),
          currentStep: computed(() => 4),
          totalCount: computed(() => 1),
          successCount: computed(() => 1),
          failedCount: computed(() => 0),
          rawRows: ref([{ email: 'a@b.com' }]),
          csvHeaders: ref(['email']),
          rowStatus: ref([CSV_ROW_STATUS.SUCCESS]),
          rowError: ref(['']),
        },
      )
      const closeBtn = wrapper
        .findAll('button')
        .find((b) => b.attributes('data-label') === 'Schließen')
      await closeBtn.trigger('click')
      expect(wrapper.emitted('closed')).toBeTruthy()
      expect(wrapper.emitted('closed')[0]).toEqual([true])
    })
  })

  describe('Drag and drop', () => {
    it('applies drag-over styling on dragover', async () => {
      const wrapper = createWrapper()
      const dropZone = wrapper.find('[data-testid="drop-zone"]')
      await dropZone.trigger('dragover')
      expect(dropZone.classes()).toContain('border-blue-500')
    })

    it('removes drag-over styling on dragleave', async () => {
      const wrapper = createWrapper()
      const dropZone = wrapper.find('[data-testid="drop-zone"]')
      await dropZone.trigger('dragover')
      await dropZone.trigger('dragleave')
      expect(dropZone.classes()).not.toContain('border-blue-500')
    })
  })
})
