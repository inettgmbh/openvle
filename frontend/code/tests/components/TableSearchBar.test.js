import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { SearchOperators } from '@/components/Tables/searchOperators'
import TableSearchBar from '@/components/Tables/TableSearchBar.vue'

// Mock vue-router
const mockRoute = {
  query: {},
}
const mockRouter = {
  replace: vi.fn(),
}

vi.mock('vue-router', () => ({
  useRoute: () => mockRoute,
  useRouter: () => mockRouter,
}))

// Mock lodash debounce to execute immediately
vi.mock('lodash/debounce', () => ({
  default: (fn) => fn,
}))

// Mock BaseIcon component
const BaseIconStub = {
  name: 'BaseIcon',
  template: '<span class="icon" data-testid="icon"></span>',
  props: ['path', 'fill', 'class'],
}

/**
 * Helper to get the last filtersChanged event with actual filters.
 * Skips the initial empty event emitted on mount.
 */
function getLastFilterEvent(wrapper) {
  const events = wrapper.emitted('filtersChanged')
  if (!events) return null
  // Find the last event with filters (skip initial empty event)
  for (let i = events.length - 1; i >= 0; i--) {
    if (events[i][0].filters.length > 0) {
      return events[i][0]
    }
  }
  return events[events.length - 1][0] // Fallback to last event
}

describe('TableSearchBar', () => {
  let wrapper

  const defaultFields = [
    { key: 'name', label: 'Name', operators: SearchOperators.TEXT },
    {
      key: 'status',
      label: 'Status',
      operators: SearchOperators.EQUALS_ONLY,
      options: [
        { label: 'Aktiv', value: 'active' },
        { label: 'Inaktiv', value: 'inactive' },
      ],
    },
    { key: 'count', label: 'Anzahl', type: 'number' },
  ]

  function createWrapper(props = {}, options = {}) {
    return mount(TableSearchBar, {
      props: {
        fields: defaultFields,
        ...props,
      },
      global: {
        stubs: {
          BaseIcon: BaseIconStub,
        },
        ...options.global,
      },
      attachTo: document.body,
    })
  }

  beforeEach(() => {
    mockRoute.query = {}
    mockRouter.replace.mockClear()
    document.body.innerHTML = ''
  })

  afterEach(() => {
    wrapper?.unmount()
  })

  // ============================================================
  // Rendering Tests
  // ============================================================

  describe('Rendering', () => {
    it('renders the search bar container', () => {
      wrapper = createWrapper()
      expect(wrapper.find('.relative').exists()).toBe(true)
    })

    it('renders the input field with placeholder', () => {
      wrapper = createWrapper()
      const input = wrapper.find('input[type="text"]')
      expect(input.exists()).toBe(true)
      expect(input.attributes('placeholder')).toBe('Filter hinzufügen...')
    })

    it('renders with custom placeholder', () => {
      wrapper = createWrapper({ placeholder: 'Suchen...' })
      const input = wrapper.find('input[type="text"]')
      expect(input.attributes('placeholder')).toBe('Suchen...')
    })

    it('renders the search icon', () => {
      wrapper = createWrapper()
      const icons = wrapper.findAll('.icon')
      expect(icons.length).toBeGreaterThan(0)
    })

    it('does not render dropdown when idle', () => {
      wrapper = createWrapper()
      expect(wrapper.find('ul[role="listbox"]').exists()).toBe(false)
    })
  })

  // ============================================================
  // Browser Autofill Suppression Tests
  // ============================================================

  describe('Browser autofill suppression', () => {
    it('disables browser autofill on the text input', () => {
      wrapper = createWrapper()
      const input = wrapper.find('input[type="text"]')
      expect(input.attributes('autocomplete')).toBe('off')
      expect(input.attributes('autocorrect')).toBe('off')
      expect(input.attributes('autocapitalize')).toBe('off')
      expect(input.attributes('spellcheck')).toBe('false')
    })

    it('disables browser autofill on the date/time input', async () => {
      wrapper = createWrapper({ fields: [{ preset: 'date' }] })

      await wrapper.find('input').trigger('focus')
      let items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')
      items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')

      const dateInput = wrapper.find('input[type="date"]')
      expect(dateInput.exists()).toBe(true)
      expect(dateInput.attributes('autocomplete')).toBe('off')
      expect(dateInput.attributes('autocorrect')).toBe('off')
      expect(dateInput.attributes('autocapitalize')).toBe('off')
      expect(dateInput.attributes('spellcheck')).toBe('false')
    })
  })

  // ============================================================
  // Field Selection Phase Tests
  // ============================================================

  describe('Field Selection Phase', () => {
    it('shows field dropdown on input focus', async () => {
      wrapper = createWrapper()
      await wrapper.find('input').trigger('focus')
      expect(wrapper.find('ul[role="listbox"]').exists()).toBe(true)
    })

    it('displays all available fields in dropdown (alphabetically sorted)', async () => {
      wrapper = createWrapper()
      await wrapper.find('input').trigger('focus')

      const items = wrapper.findAll('li[role="option"]')
      expect(items.length).toBe(3)
      // Fields are sorted alphabetically by label
      expect(items[0].text()).toBe('Anzahl')
      expect(items[1].text()).toBe('Name')
      expect(items[2].text()).toBe('Status')
    })

    it('filters fields based on input', async () => {
      wrapper = createWrapper()
      const input = wrapper.find('input')
      await input.trigger('focus')
      await input.setValue('stat')

      const items = wrapper.findAll('li[role="option"]')
      expect(items.length).toBe(1)
      expect(items[0].text()).toBe('Status')
    })

    it('selects field on click', async () => {
      wrapper = createWrapper()
      await wrapper.find('input').trigger('focus')

      const items = wrapper.findAll('li[role="option"]')
      await items[1].trigger('click') // Name is at index 1 (alphabetically sorted)

      // Should now show breadcrumb with field name
      expect(wrapper.text()).toContain('Name')
    })

    it('selects field on Enter key', async () => {
      wrapper = createWrapper()
      const input = wrapper.find('input')
      await input.trigger('focus')

      // Highlight first item (Anzahl, alphabetically first)
      await input.trigger('keydown', { key: 'ArrowDown' })
      await input.trigger('keydown', { key: 'Enter' })

      expect(wrapper.text()).toContain('Anzahl')
    })
  })

  // ============================================================
  // Operator Selection Phase Tests
  // ============================================================

  describe('Operator Selection Phase', () => {
    it('shows operators after field selection', async () => {
      wrapper = createWrapper()
      await wrapper.find('input').trigger('focus')

      // Select name field (has TEXT operators) - index 1 after alphabetical sort
      const items = wrapper.findAll('li[role="option"]')
      await items[1].trigger('click')

      // Check operator dropdown
      const operatorItems = wrapper.findAll('li[role="option"]')
      expect(operatorItems.length).toBe(SearchOperators.TEXT.length)
    })

    it('auto-skips operator phase when only one operator', async () => {
      const singleOpFields = [
        {
          key: 'name',
          label: 'Name',
          operators: [SearchOperators.ALL.eq],
        },
      ]
      wrapper = createWrapper({ fields: singleOpFields })

      await wrapper.find('input').trigger('focus')
      const items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')

      // Should skip directly to value phase (no operator dropdown)
      const input = wrapper.find('input')
      expect(input.attributes('placeholder')).toContain('Wert')
    })

    it('selects operator on click', async () => {
      wrapper = createWrapper()
      await wrapper.find('input').trigger('focus')

      // Select name field - index 1 after alphabetical sort
      let items = wrapper.findAll('li[role="option"]')
      await items[1].trigger('click')

      // Select "contains" operator
      items = wrapper.findAll('li[role="option"]')
      await items[2].trigger('click') // contains is 3rd in TEXT

      // Should be in value phase now
      const input = wrapper.find('input')
      expect(input.attributes('placeholder')).toContain('Wert')
    })

    it('adds filter immediately for empty operator', async () => {
      wrapper = createWrapper()
      await wrapper.find('input').trigger('focus')

      // Select name field - index 1 after alphabetical sort
      let items = wrapper.findAll('li[role="option"]')
      await items[1].trigger('click')

      // Select "empty" operator (5th in TEXT operators)
      items = wrapper.findAll('li[role="option"]')
      await items[4].trigger('click') // empty

      // Filter should be added immediately
      expect(wrapper.emitted('filtersChanged')).toBeTruthy()
      const event = getLastFilterEvent(wrapper)
      expect(event.filters[0].operator).toBe('empty')
    })

    it('adds filter immediately for nempty operator', async () => {
      wrapper = createWrapper()
      await wrapper.find('input').trigger('focus')

      // Select name field - index 1 after alphabetical sort
      let items = wrapper.findAll('li[role="option"]')
      await items[1].trigger('click')

      // Select "nempty" operator (6th in TEXT operators)
      items = wrapper.findAll('li[role="option"]')
      await items[5].trigger('click') // nempty

      expect(wrapper.emitted('filtersChanged')).toBeTruthy()
      const event = getLastFilterEvent(wrapper)
      expect(event.filters[0].operator).toBe('nempty')
    })
  })

  // ============================================================
  // Value Input Phase Tests
  // ============================================================

  describe('Value Input Phase - Freetext', () => {
    async function goToValuePhase(w) {
      await w.find('input').trigger('focus')
      let items = w.findAll('li[role="option"]')
      await items[1].trigger('click') // Select name field (index 1 after alphabetical sort)
      items = w.findAll('li[role="option"]')
      await items[0].trigger('click') // Select eq operator
    }

    it('shows value input placeholder', async () => {
      wrapper = createWrapper()
      await goToValuePhase(wrapper)

      const input = wrapper.find('input')
      expect(input.attributes('placeholder')).toContain('Wert eingeben')
    })

    it('adds filter on Enter with freetext value', async () => {
      wrapper = createWrapper()
      await goToValuePhase(wrapper)

      const input = wrapper.find('input')
      await input.setValue('test value')
      await input.trigger('keydown', { key: 'Enter' })

      expect(wrapper.emitted('filtersChanged')).toBeTruthy()
      const event = getLastFilterEvent(wrapper)
      expect(event.filters[0].field).toBe('name')
      expect(event.filters[0].value).toBe('test value')
    })

    it('displays freetext values with quotes in chip', async () => {
      wrapper = createWrapper()
      await goToValuePhase(wrapper)

      const input = wrapper.find('input')
      await input.setValue('test')
      await input.trigger('keydown', { key: 'Enter' })

      // Check that the chip displays the value with quotes
      expect(wrapper.text()).toContain('"test"')
    })
  })

  describe('Value Input Phase - Options', () => {
    async function goToStatusValuePhase(w) {
      await w.find('input').trigger('focus')
      let items = w.findAll('li[role="option"]')
      await items[2].trigger('click') // Select status field (index 2 after alphabetical sort)
      items = w.findAll('li[role="option"]')
      await items[0].trigger('click') // Select eq operator
    }

    it('shows options dropdown for fields with options', async () => {
      wrapper = createWrapper()
      await goToStatusValuePhase(wrapper)

      const items = wrapper.findAll('li[role="option"]')
      expect(items.length).toBe(2)
      expect(items[0].text()).toBe('Aktiv')
      expect(items[1].text()).toBe('Inaktiv')
    })

    it('filters options based on input', async () => {
      wrapper = createWrapper()
      await goToStatusValuePhase(wrapper)

      const input = wrapper.find('input')
      // Use a unique search term that only matches one option
      await input.setValue('Inakt')
      await input.trigger('input')
      await flushPromises()

      const items = wrapper.findAll('li[role="option"]')
      expect(items.length).toBe(1)
      expect(items[0].text()).toBe('Inaktiv')
    })

    it('selects option on click', async () => {
      wrapper = createWrapper()
      await goToStatusValuePhase(wrapper)

      const items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')

      expect(wrapper.emitted('filtersChanged')).toBeTruthy()
      const event = getLastFilterEvent(wrapper)
      expect(event.filters[0].value).toBe('active')
    })

    it('displays option label (not value) in chip', async () => {
      wrapper = createWrapper()
      await goToStatusValuePhase(wrapper)

      const items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')

      // Should show label "Aktiv", not value "active"
      expect(wrapper.text()).toContain('Aktiv')
      expect(wrapper.text()).not.toContain('"Aktiv"') // Options don't have quotes
    })
  })

  describe('Value Input Phase - Lookup', () => {
    const lookupFields = [
      {
        key: 'userId',
        label: 'Benutzer',
        type: 'lookup',
        operators: SearchOperators.EQUALS_ONLY,
        fetchData: vi.fn().mockResolvedValue({
          items: [
            { id: 'uuid-1', name: 'Max Mustermann' },
            { id: 'uuid-2', name: 'Anna Schmidt' },
          ],
        }),
        fetchSelected: vi.fn().mockResolvedValue('Max Mustermann'),
        labelAttribute: 'name',
        returnAttribute: 'id',
        minChars: 3,
      },
    ]

    async function goToLookupValuePhase(w) {
      await w.find('input').trigger('focus')
      let items = w.findAll('li[role="option"]')
      await items[0].trigger('click') // Select userId field
      items = w.findAll('li[role="option"]')
      await items[0].trigger('click') // Select eq operator
    }

    it('shows min chars hint when input is too short', async () => {
      wrapper = createWrapper({ fields: lookupFields })
      await goToLookupValuePhase(wrapper)

      const input = wrapper.find('input')
      await input.setValue('ab')

      expect(wrapper.text()).toContain('Mindestens 3 Zeichen')
    })

    it('triggers lookup search when min chars reached', async () => {
      wrapper = createWrapper({ fields: lookupFields })
      await goToLookupValuePhase(wrapper)

      const input = wrapper.find('input')
      await input.setValue('Max')
      await input.trigger('input')
      await flushPromises()

      expect(lookupFields[0].fetchData).toHaveBeenCalledWith('Max')
    })

    it('displays lookup results in dropdown', async () => {
      wrapper = createWrapper({ fields: lookupFields })
      await goToLookupValuePhase(wrapper)

      const input = wrapper.find('input')
      await input.setValue('Max')
      await input.trigger('input')
      await flushPromises()

      const items = wrapper.findAll('li[role="option"]')
      expect(items.length).toBe(2)
      expect(items[0].text()).toBe('Max Mustermann')
      expect(items[1].text()).toBe('Anna Schmidt')
    })

    it('selects lookup result and stores ID as value', async () => {
      wrapper = createWrapper({ fields: lookupFields })
      await goToLookupValuePhase(wrapper)

      const input = wrapper.find('input')
      await input.setValue('Max')
      await input.trigger('input')
      await flushPromises()

      const items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')

      expect(wrapper.emitted('filtersChanged')).toBeTruthy()
      const event = getLastFilterEvent(wrapper)
      expect(event.filters[0].value).toBe('uuid-1') // ID, not name
    })

    it('shows "no results" message when lookup returns empty', async () => {
      const emptyLookupFields = [
        {
          key: 'userId',
          label: 'Benutzer',
          type: 'lookup',
          operators: SearchOperators.EQUALS_ONLY,
          fetchData: vi.fn().mockResolvedValue({ items: [] }),
          fetchSelected: vi.fn().mockResolvedValue(''),
          labelAttribute: 'name',
          returnAttribute: 'id',
          minChars: 3,
        },
      ]
      wrapper = createWrapper({ fields: emptyLookupFields })

      // Go to lookup value phase
      await wrapper.find('input').trigger('focus')
      let items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click') // Select userId field
      items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click') // Select eq operator

      const input = wrapper.find('input')
      await input.setValue('xyz')
      await input.trigger('input')
      await flushPromises()

      expect(wrapper.text()).toContain('Keine Ergebnisse')
    })
  })

  // ============================================================
  // Date/Time Field Tests
  // ============================================================

  describe('Date/Time Fields', () => {
    const dateFields = [
      { preset: 'date' },
      { preset: 'time' },
      { preset: 'datetime' },
    ]

    it('shows date input for date fields', async () => {
      wrapper = createWrapper({ fields: [{ preset: 'date' }] })

      await wrapper.find('input').trigger('focus')
      let items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')
      items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click') // Select eq operator

      const dateInput = wrapper.find('input[type="date"]')
      expect(dateInput.exists()).toBe(true)
    })

    it('shows time input for time fields', async () => {
      wrapper = createWrapper({ fields: [{ preset: 'time' }] })

      await wrapper.find('input').trigger('focus')
      let items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')
      items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')

      const timeInput = wrapper.find('input[type="time"]')
      expect(timeInput.exists()).toBe(true)
    })

    it('shows datetime-local input for datetime fields', async () => {
      wrapper = createWrapper({ fields: [{ preset: 'datetime' }] })

      await wrapper.find('input').trigger('focus')
      let items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')
      items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')

      const datetimeInput = wrapper.find('input[type="datetime-local"]')
      expect(datetimeInput.exists()).toBe(true)
    })

    it('pre-fills date/time input with current date/time', async () => {
      wrapper = createWrapper({ fields: [{ preset: 'date' }] })

      await wrapper.find('input').trigger('focus')
      let items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')
      items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')

      const dateInput = wrapper.find('input[type="date"]')
      // Should have a value in YYYY-MM-DD format
      expect(dateInput.element.value).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    })

    it('shows confirm button for date/time input', async () => {
      wrapper = createWrapper({ fields: [{ preset: 'date' }] })

      await wrapper.find('input').trigger('focus')
      let items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')
      items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')

      // Confirm button should be visible when there's a value
      const confirmBtn = wrapper.find('button[title="Übernehmen (Enter)"]')
      expect(confirmBtn.exists()).toBe(true)
    })

    it('adds datetime filter with seconds appended', async () => {
      wrapper = createWrapper({ fields: [{ preset: 'datetime' }] })

      await wrapper.find('input').trigger('focus')
      let items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')
      items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')

      const datetimeInput = wrapper.find('input[type="datetime-local"]')
      await datetimeInput.setValue('2025-01-15T10:30')

      const confirmBtn = wrapper.find('button[title="Übernehmen (Enter)"]')
      await confirmBtn.trigger('click')

      expect(wrapper.emitted('filtersChanged')).toBeTruthy()
      const event = getLastFilterEvent(wrapper)
      expect(event.filters[0].value).toBe('2025-01-15T10:30:00')
    })

    it('formats date display value correctly', async () => {
      wrapper = createWrapper({ fields: [{ preset: 'date' }] })

      await wrapper.find('input').trigger('focus')
      let items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')
      items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')

      const dateInput = wrapper.find('input[type="date"]')
      await dateInput.setValue('2025-01-15')

      const confirmBtn = wrapper.find('button[title="Übernehmen (Enter)"]')
      await confirmBtn.trigger('click')

      // Display should be formatted as German date
      expect(wrapper.text()).toContain('15.1.2025')
    })
  })

  // ============================================================
  // Number Field Tests
  // ============================================================

  describe('Number Fields', () => {
    it('auto-applies NUMBER operators for type=number', async () => {
      wrapper = createWrapper()
      await wrapper.find('input').trigger('focus')

      // Select "Anzahl" field (type: number) - index 0 after alphabetical sort
      const items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')

      // Should show NUMBER operators
      const operatorItems = wrapper.findAll('li[role="option"]')
      expect(operatorItems.length).toBe(SearchOperators.NUMBER.length)
    })
  })

  // ============================================================
  // Preset Tests
  // ============================================================

  describe('Preset Resolution', () => {
    it('resolves preset by key automatically', async () => {
      const presetFields = [{ preset: 'name' }]
      wrapper = createWrapper({ fields: presetFields })

      await wrapper.find('input').trigger('focus')
      const items = wrapper.findAll('li[role="option"]')
      expect(items[0].text()).toBe('Name')
    })

    it('resolves preset by explicit preset property', async () => {
      const presetFields = [{ key: 'displayName', preset: 'name' }]
      wrapper = createWrapper({ fields: presetFields })

      await wrapper.find('input').trigger('focus')
      const items = wrapper.findAll('li[role="option"]')
      expect(items[0].text()).toBe('Name')
    })

    it('allows custom properties to override preset', async () => {
      const presetFields = [{ preset: 'name', label: 'Custom Label' }]
      wrapper = createWrapper({ fields: presetFields })

      await wrapper.find('input').trigger('focus')
      const items = wrapper.findAll('li[role="option"]')
      expect(items[0].text()).toBe('Custom Label')
    })
  })

  // ============================================================
  // Filter Management Tests
  // ============================================================

  describe('Filter Management', () => {
    // Default fieldIndex=1 selects "Name" field after alphabetical sort (Anzahl=0, Name=1, Status=2)
    async function addFilter(w, fieldIndex = 1, operatorIndex = 0) {
      await w.find('input').trigger('focus')
      let items = w.findAll('li[role="option"]')
      await items[fieldIndex].trigger('click')
      items = w.findAll('li[role="option"]')
      await items[operatorIndex].trigger('click')
      const input = w.find('input')
      await input.setValue('test')
      await input.trigger('keydown', { key: 'Enter' })
    }

    it('displays active filter as chip', async () => {
      wrapper = createWrapper()
      await addFilter(wrapper)

      const chip = wrapper.find(
        '.bg-blue-100, .dark\\:bg-blue-900\\/40, [class*="bg-blue"]',
      )
      expect(chip.exists()).toBe(true)
    })

    it('removes filter on chip close button click', async () => {
      wrapper = createWrapper()
      await addFilter(wrapper)

      const closeBtn = wrapper.find('button')
      await closeBtn.trigger('click')

      // 2 events: filter added, filter removed (no initial empty emit)
      expect(wrapper.emitted('filtersChanged').length).toBe(2)
      expect(wrapper.emitted('filtersChanged')[1][0].filters).toHaveLength(0)
    })

    it('replaces filter when maxFilters=1', async () => {
      wrapper = createWrapper({ maxFilters: 1 })
      await addFilter(wrapper)

      // In single-filter mode, clicking on the container should allow adding a new filter
      // First, remove the existing filter
      const closeBtn = wrapper.find('button')
      await closeBtn.trigger('click')

      // Now add another filter
      await addFilter(wrapper)

      // Should still have only 1 filter
      const emits = wrapper.emitted('filtersChanged')
      const lastEmit = emits[emits.length - 1][0]
      expect(lastEmit.filters).toHaveLength(1)
    })

    it('allows multiple filters when maxFilters > 1', async () => {
      wrapper = createWrapper({ maxFilters: 3 })
      await addFilter(wrapper, 1) // Name filter (index 1 after alphabetical sort)

      // Add status filter
      await wrapper.find('input').trigger('focus')
      let items = wrapper.findAll('li[role="option"]')
      // After first filter, Name should not be available
      const statusItem = items.find((i) => i.text() === 'Status')
      await statusItem.trigger('click')
      items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')
      items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')

      const emits = wrapper.emitted('filtersChanged')
      const lastEmit = emits[emits.length - 1][0]
      expect(lastEmit.filters).toHaveLength(2)
    })

    it('hides used fields from dropdown in multi-filter mode', async () => {
      wrapper = createWrapper({ maxFilters: 3 })
      await addFilter(wrapper, 1) // Add Name filter (index 1 after alphabetical sort)

      await wrapper.find('input').trigger('focus')
      const items = wrapper.findAll('li[role="option"]')

      // Name should not be in the list anymore
      const names = items.map((i) => i.text())
      expect(names).not.toContain('Name')
    })

    it('shows "all filters used" hint when max reached', async () => {
      wrapper = createWrapper({ maxFilters: 1 })
      await addFilter(wrapper)

      expect(wrapper.text()).toMatch(/Maximale Anzahl|Alle Filter/)
    })

    it('clears all filters via clearAll method', async () => {
      wrapper = createWrapper()
      await addFilter(wrapper)

      wrapper.vm.clearAll()
      await flushPromises()

      const emits = wrapper.emitted('filtersChanged')
      const lastEmit = emits[emits.length - 1][0]
      expect(lastEmit.filters).toHaveLength(0)
    })
  })

  // ============================================================
  // Keyboard Navigation Tests
  // ============================================================

  describe('Keyboard Navigation', () => {
    it('navigates dropdown with ArrowDown', async () => {
      wrapper = createWrapper()
      const input = wrapper.find('input')
      await input.trigger('focus')

      await input.trigger('keydown', { key: 'ArrowDown' })

      const highlighted = wrapper.find('[aria-selected="true"]')
      expect(highlighted.exists()).toBe(true)
    })

    it('navigates dropdown with ArrowUp', async () => {
      wrapper = createWrapper()
      const input = wrapper.find('input')
      await input.trigger('focus')

      await input.trigger('keydown', { key: 'ArrowDown' })
      await input.trigger('keydown', { key: 'ArrowDown' })
      await input.trigger('keydown', { key: 'ArrowUp' })

      const items = wrapper.findAll('li[role="option"]')
      const highlighted = items.find(
        (i) => i.attributes('aria-selected') === 'true',
      )
      // First item after alphabetical sort is "Anzahl"
      expect(highlighted.text()).toBe('Anzahl')
    })

    it('wraps around at end of list', async () => {
      wrapper = createWrapper()
      const input = wrapper.find('input')
      await input.trigger('focus')

      // Go past the end (3 fields: index 0, 1, 2)
      // After 4 ArrowDown presses: 0 -> 1 -> 2 -> 0 (wraps)
      await input.trigger('keydown', { key: 'ArrowDown' }) // index 0
      await input.trigger('keydown', { key: 'ArrowDown' }) // index 1
      await input.trigger('keydown', { key: 'ArrowDown' }) // index 2
      await input.trigger('keydown', { key: 'ArrowDown' }) // wraps to index 0

      const items = wrapper.findAll('li[role="option"]')
      const highlighted = items.find(
        (i) => i.attributes('aria-selected') === 'true',
      )
      // First item after alphabetical sort is "Anzahl"
      expect(highlighted.text()).toBe('Anzahl')
    })

    it('selects highlighted item on Enter', async () => {
      wrapper = createWrapper()
      const input = wrapper.find('input')
      await input.trigger('focus')

      await input.trigger('keydown', { key: 'ArrowDown' })
      await input.trigger('keydown', { key: 'Enter' })

      // First item after alphabetical sort is "Anzahl"
      expect(wrapper.text()).toContain('Anzahl')
    })

    it('resets on Escape', async () => {
      wrapper = createWrapper()
      const input = wrapper.find('input')
      await input.trigger('focus')

      // Select a field
      await input.trigger('keydown', { key: 'ArrowDown' })
      await input.trigger('keydown', { key: 'Enter' })

      // Press Escape
      await input.trigger('keydown', { key: 'Escape' })

      // Should be back to idle
      expect(wrapper.find('ul[role="listbox"]').exists()).toBe(false)
    })

    it('removes last chip on Backspace when input is empty', async () => {
      // Use maxFilters > 1 so input stays visible after adding a filter
      wrapper = createWrapper({ maxFilters: 3 })

      // Add a filter first - use Name field (index 1 after alphabetical sort)
      await wrapper.find('input').trigger('focus')
      let items = wrapper.findAll('li[role="option"]')
      await items[1].trigger('click')
      items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')
      let input = wrapper.find('input')
      await input.setValue('test')
      await input.trigger('keydown', { key: 'Enter' })

      // After adding filter, component should still show input (multi-filter mode)
      // Press backspace with empty input to remove the chip
      input = wrapper.find('input')
      await input.trigger('keydown', { key: 'Backspace' })

      const emits = wrapper.emitted('filtersChanged')
      const lastEmit = emits[emits.length - 1][0]
      expect(lastEmit.filters).toHaveLength(0)
    })

    it('goes back to operator phase on Backspace in value phase', async () => {
      wrapper = createWrapper()
      const input = wrapper.find('input')
      await input.trigger('focus')

      // Select Name field (index 1) and operator
      let items = wrapper.findAll('li[role="option"]')
      await items[1].trigger('click')
      items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')

      // Now in value phase, press Backspace
      await input.trigger('keydown', { key: 'Backspace' })

      // Should show TEXT operators again
      const operatorItems = wrapper.findAll('li[role="option"]')
      expect(operatorItems.length).toBe(SearchOperators.TEXT.length)
    })
  })

  // ============================================================
  // Click Outside Tests
  // ============================================================

  describe('Click Outside', () => {
    it('resets state on click outside', async () => {
      wrapper = createWrapper()
      await wrapper.find('input').trigger('focus')

      // Simulate click outside
      document.body.click()
      await flushPromises()

      expect(wrapper.find('ul[role="listbox"]').exists()).toBe(false)
    })
  })

  // ============================================================
  // Query Sync Tests
  // ============================================================

  describe('Query Synchronization', () => {
    it('syncs filters to URL query params', async () => {
      wrapper = createWrapper({ syncQuery: true })

      // Add a filter - use Name field (index 1 after alphabetical sort)
      await wrapper.find('input').trigger('focus')
      let items = wrapper.findAll('li[role="option"]')
      await items[1].trigger('click')
      items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')
      const input = wrapper.find('input')
      await input.setValue('test')
      await input.trigger('keydown', { key: 'Enter' })

      expect(mockRouter.replace).toHaveBeenCalled()
      const lastCall =
        mockRouter.replace.mock.calls[mockRouter.replace.mock.calls.length - 1]
      expect(lastCall[0].query.filter).toBe('name:eq:test')
    })

    it('uses custom query key', async () => {
      wrapper = createWrapper({ syncQuery: true, queryKey: 'search' })

      // Use Name field (index 1 after alphabetical sort)
      await wrapper.find('input').trigger('focus')
      let items = wrapper.findAll('li[role="option"]')
      await items[1].trigger('click')
      items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')
      const input = wrapper.find('input')
      await input.setValue('test')
      await input.trigger('keydown', { key: 'Enter' })

      const lastCall =
        mockRouter.replace.mock.calls[mockRouter.replace.mock.calls.length - 1]
      expect(lastCall[0].query.search).toBeDefined()
    })

    it('does not sync when syncQuery is false', async () => {
      wrapper = createWrapper({ syncQuery: false })

      // Use Name field (index 1 after alphabetical sort)
      await wrapper.find('input').trigger('focus')
      let items = wrapper.findAll('li[role="option"]')
      await items[1].trigger('click')
      items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')
      const input = wrapper.find('input')
      await input.setValue('test')
      await input.trigger('keydown', { key: 'Enter' })

      expect(mockRouter.replace).not.toHaveBeenCalled()
    })

    it('initializes filters from query params on mount', async () => {
      mockRoute.query = { filter: 'name:eq:initial' }

      wrapper = createWrapper({ syncQuery: true })
      await flushPromises()

      expect(wrapper.text()).toContain('Name')
      expect(wrapper.text()).toContain('"initial"')
    })

    it('handles multiple filters in query params', async () => {
      mockRoute.query = { filter: 'name:eq:test;status:eq:active' }

      const fieldsWithOptions = [...defaultFields]
      wrapper = createWrapper({
        fields: fieldsWithOptions,
        maxFilters: 3,
        syncQuery: true,
      })
      await flushPromises()

      expect(wrapper.emitted('filtersChanged')).toBeTruthy()
      const lastEmit = wrapper.emitted('filtersChanged').pop()[0]
      expect(lastEmit.filters).toHaveLength(2)
    })
  })

  // ============================================================
  // Initial Filters Tests
  // ============================================================

  describe('Initial Filters', () => {
    it('loads initial filters from prop', async () => {
      wrapper = createWrapper({
        initialFilters: [{ field: 'name', operator: 'eq', value: 'initial' }],
        syncQuery: false,
      })
      await flushPromises()

      expect(wrapper.text()).toContain('Name')
      expect(wrapper.text()).toContain('"initial"')
    })

    it('query params take precedence over initialFilters prop', async () => {
      mockRoute.query = { filter: 'name:eq:fromQuery' }

      wrapper = createWrapper({
        initialFilters: [{ field: 'name', operator: 'eq', value: 'fromProp' }],
        syncQuery: true,
      })
      await flushPromises()

      expect(wrapper.text()).toContain('"fromQuery"')
      expect(wrapper.text()).not.toContain('"fromProp"')
    })
  })

  // ============================================================
  // Emit Tests
  // ============================================================

  describe('Event Emissions', () => {
    it('emits filtersChanged with correct structure', async () => {
      wrapper = createWrapper({ objectModel: 'users' })

      // Use Name field (index 1 after alphabetical sort)
      await wrapper.find('input').trigger('focus')
      let items = wrapper.findAll('li[role="option"]')
      await items[1].trigger('click')
      items = wrapper.findAll('li[role="option"]')
      await items[0].trigger('click')
      const input = wrapper.find('input')
      await input.setValue('test')
      await input.trigger('keydown', { key: 'Enter' })

      const emitted = getLastFilterEvent(wrapper)
      expect(emitted).toHaveProperty('filters')
      expect(emitted).toHaveProperty('objectModel', 'users')
      expect(emitted.filters[0]).toMatchObject({
        field: 'name',
        operator: 'eq',
        value: 'test',
      })
    })
  })

  // ============================================================
  // Exposed Methods Tests
  // ============================================================

  describe('Exposed Methods', () => {
    it('exposes clearAll method', () => {
      wrapper = createWrapper()
      expect(typeof wrapper.vm.clearAll).toBe('function')
    })

    it('exposes focus method', () => {
      wrapper = createWrapper()
      expect(typeof wrapper.vm.focus).toBe('function')
    })

    it('focus method focuses the input', async () => {
      wrapper = createWrapper()
      wrapper.vm.focus()
      await flushPromises()

      expect(document.activeElement).toBe(wrapper.find('input').element)
    })
  })

  // ============================================================
  // Default Icon Tests
  // ============================================================

  describe('Default Field Icon', () => {
    it('uses default icon when field has no icon', async () => {
      const noIconFields = [
        {
          key: 'custom',
          label: 'Custom Field',
          operators: SearchOperators.TEXT,
        },
      ]
      wrapper = createWrapper({ fields: noIconFields })

      await wrapper.find('input').trigger('focus')

      // Should render icon component (default icon)
      const icons = wrapper.findAll('.icon')
      expect(icons.length).toBeGreaterThan(0)
    })
  })
})
