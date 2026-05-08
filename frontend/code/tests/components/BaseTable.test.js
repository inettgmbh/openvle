import '../setupComponentMocks'

import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import BaseTable from '@/components/BaseTable.vue'
import { SearchOperators } from '@/components/Tables/searchOperators'

describe('BaseTable', () => {
  const defaultColumns = [
    { key: 'name', label: 'Name' },
    { key: 'status', label: 'Status' },
  ]

  const defaultData = [
    { id: 1, name: 'Item 1', status: 'active', createdAt: '2024-01-01' },
    { id: 2, name: 'Item 2', status: 'inactive', createdAt: '2024-01-02' },
  ]

  const defaultProps = {
    columns: defaultColumns,
    data: defaultData,
    objectModel: 'test',
    itemsTotal: 2,
    loading: false,
  }

  let wrapper

  beforeEach(() => {
    wrapper = null
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
      wrapper = null
    }
  })

  const createWrapper = (props = {}, options = {}) => {
    return mount(BaseTable, {
      props: { ...defaultProps, ...props },
      global: {
        stubs: {
          transition: false,
        },
        directives: {
          tooltip: () => {},
        },
        ...options.global,
      },
      ...options,
    })
  }

  describe('Rendering', () => {
    it('renders a table element', () => {
      wrapper = createWrapper()
      expect(wrapper.find('table').exists()).toBe(true)
    })

    it('renders column headers based on columns prop', () => {
      wrapper = createWrapper()
      const headers = wrapper.findAll('th')
      expect(headers.length).toBeGreaterThanOrEqual(2)
      expect(wrapper.text()).toContain('Name')
      expect(wrapper.text()).toContain('Status')
    })

    it('renders the correct number of data rows', () => {
      wrapper = createWrapper()
      const rows = wrapper.findAll('tbody tr')
      expect(rows.length).toBe(2)
    })

    it('displays empty state message when itemsTotal is 0', () => {
      wrapper = createWrapper({ itemsTotal: 0, data: [] })
      expect(wrapper.text()).toContain('Keine Daten vorhanden')
    })

    it('renders createdAt column by default', () => {
      wrapper = createWrapper()
      expect(wrapper.text()).toContain('Erstellt am')
    })

    it('hides createdAt column when createdColumnEnabled is false', () => {
      wrapper = createWrapper({ createdColumnEnabled: false })
      expect(wrapper.text()).not.toContain('Erstellt am')
    })

    it('uses custom createdColumnLabel when provided', () => {
      wrapper = createWrapper({ createdColumnLabel: 'Created Date' })
      expect(wrapper.text()).toContain('Created Date')
    })
  })

  describe('Column Width', () => {
    it('applies w-full class to table', () => {
      wrapper = createWrapper()
      const table = wrapper.find('table')
      expect(table.classes()).toContain('w-full')
    })

    it('applies width style when column has width property', () => {
      const columnsWithWidth = [
        { key: 'name', label: 'Name', width: '200px' },
        { key: 'status', label: 'Status', width: '150px' },
      ]
      wrapper = createWrapper({ columns: columnsWithWidth })

      const headers = wrapper.findAll('th')
      const nameHeader = headers.find((h) => h.text().includes('Name'))
      const statusHeader = headers.find((h) => h.text().includes('Status'))

      expect(nameHeader.attributes('style')).toContain('width: 200px')
      expect(statusHeader.attributes('style')).toContain('width: 150px')
    })

    it('does not apply width style when column has no width property', () => {
      wrapper = createWrapper()
      const headers = wrapper.findAll('th')
      const nameHeader = headers.find((h) => h.text().includes('Name'))

      expect(nameHeader.attributes('style')).toBeFalsy()
    })

    it('supports percentage width values', () => {
      const columnsWithPercentage = [
        { key: 'name', label: 'Name', width: '50%' },
      ]
      wrapper = createWrapper({ columns: columnsWithPercentage })

      const headers = wrapper.findAll('th')
      const nameHeader = headers.find((h) => h.text().includes('Name'))

      expect(nameHeader.attributes('style')).toContain('width: 50%')
    })

    it('applies w-10 class to checkable column header', () => {
      wrapper = createWrapper({ checkable: true })
      const headers = wrapper.findAll('th')
      expect(headers[0].classes()).toContain('w-10')
    })

    it('applies w-16 class to symbol column header', () => {
      wrapper = createWrapper({ symbol: true })
      const headers = wrapper.findAll('th')
      const symbolHeader = headers.find((h) => h.classes().includes('w-16'))
      expect(symbolHeader).toBeTruthy()
    })
  })

  describe('Sorting', () => {
    it('emits sortOrderChanged when clicking sort icon', async () => {
      wrapper = createWrapper()
      const sortIcons = wrapper.findAll('.icon')

      await sortIcons[0].trigger('click')

      expect(wrapper.emitted('sortOrderChanged')).toBeTruthy()
    })

    it('emits ascending direction when clicking on unsorted column', async () => {
      wrapper = createWrapper({
        sortColumnKey: 'status',
        sortDirection: 'asc',
      })

      const sortIcons = wrapper.findAll('.icon')
      await sortIcons[0].trigger('click')

      const emitted = wrapper.emitted('sortOrderChanged')
      expect(emitted).toBeTruthy()
      expect(emitted[0]).toContain('asc')
    })

    it('toggles to descending when clicking sorted ascending column', async () => {
      wrapper = createWrapper({
        sortColumnKey: 'name',
        sortDirection: 'asc',
      })

      const sortIcons = wrapper.findAll('.icon')
      await sortIcons[0].trigger('click')

      const emitted = wrapper.emitted('sortOrderChanged')
      expect(emitted).toBeTruthy()
      expect(emitted[0]).toContain('desc')
    })

    it('emits sort event with column key and objectModel', async () => {
      wrapper = createWrapper()
      const sortIcons = wrapper.findAll('.icon')

      await sortIcons[0].trigger('click')

      const emitted = wrapper.emitted('sortOrderChanged')
      expect(emitted[0]).toContain('test')
    })
  })

  describe('Loading State', () => {
    it('shows skeleton rows when loading', async () => {
      wrapper = createWrapper({ loading: true })

      await new Promise((resolve) => setTimeout(resolve, 50))

      const skeletonElements = wrapper.findAll('.animate-pulse')
      expect(skeletonElements.length).toBeGreaterThan(0)
    })

    it('shows correct number of skeleton rows based on perPage', async () => {
      wrapper = createWrapper({ loading: true, perPage: 3 })

      await new Promise((resolve) => setTimeout(resolve, 50))

      const skeletonRows = wrapper.findAll('tbody tr')
      expect(skeletonRows.length).toBe(3)
    })

    it('shows max 5 skeleton rows when perPage is large', async () => {
      wrapper = createWrapper({ loading: true, perPage: 20 })

      await new Promise((resolve) => setTimeout(resolve, 50))

      const skeletonRows = wrapper.findAll('tbody tr')
      expect(skeletonRows.length).toBe(5)
    })
  })

  describe('Action Buttons', () => {
    it('renders view button when buttons include "view"', () => {
      wrapper = createWrapper({ buttons: ['view'] })
      const buttons = wrapper.findAll('button')
      expect(buttons.length).toBeGreaterThan(0)
    })

    it('renders edit button when buttons include "edit"', () => {
      wrapper = createWrapper({ buttons: ['edit'] })
      const buttons = wrapper.findAll('button')
      expect(buttons.length).toBeGreaterThan(0)
    })

    it('renders delete button when buttons include "delete"', () => {
      wrapper = createWrapper({ buttons: ['delete'] })
      const buttons = wrapper.findAll('button')
      expect(buttons.length).toBeGreaterThan(0)
    })

    it('renders multiple buttons when multiple are specified', () => {
      wrapper = createWrapper({ buttons: ['view', 'edit', 'delete'] })
      const rows = wrapper.findAll('tbody tr')
      const buttonsInFirstRow = rows[0].findAll('button')
      expect(buttonsInFirstRow.length).toBe(3)
    })

    it('emits deleteObject with item data when delete button is clicked', async () => {
      wrapper = createWrapper({ buttons: ['delete'] })
      const deleteButtons = wrapper.findAll('button')

      await deleteButtons[0].trigger('click')

      const emitted = wrapper.emitted('deleteObject')
      expect(emitted).toBeTruthy()
      expect(emitted[0][0]).toEqual(defaultData[0])
      expect(emitted[0][1]).toBe('test')
    })

    it('emits viewObject when view button clicked and emitViewObject is true', async () => {
      wrapper = createWrapper({ buttons: ['view'], emitViewObject: true })
      const viewButtons = wrapper.findAll('button')

      await viewButtons[0].trigger('click')

      expect(wrapper.emitted('viewObject')).toBeTruthy()
    })

    describe('view button: open in new tab', () => {
      let openSpy
      let pushSpy

      beforeEach(async () => {
        const router = (await import('@/router')).default
        openSpy = vi.spyOn(window, 'open').mockImplementation(() => null)
        pushSpy = vi.spyOn(router, 'push').mockResolvedValue()
      })

      afterEach(() => {
        openSpy.mockRestore()
        pushSpy.mockRestore()
      })

      it('navigates via router.push on plain left-click', async () => {
        wrapper = createWrapper({ buttons: ['view'] })
        const viewButton = wrapper.findAll('button')[0]

        await viewButton.trigger('click')

        expect(pushSpy).toHaveBeenCalledWith({ path: '/test/1' })
        expect(openSpy).not.toHaveBeenCalled()
      })

      it('opens in new tab on Cmd+click (metaKey)', async () => {
        wrapper = createWrapper({ buttons: ['view'] })
        const viewButton = wrapper.findAll('button')[0]

        await viewButton.trigger('click', { metaKey: true })

        expect(openSpy).toHaveBeenCalledWith('#/test/1', '_blank')
        expect(pushSpy).not.toHaveBeenCalled()
      })

      it('opens in new tab on Ctrl+click (ctrlKey)', async () => {
        wrapper = createWrapper({ buttons: ['view'] })
        const viewButton = wrapper.findAll('button')[0]

        await viewButton.trigger('click', { ctrlKey: true })

        expect(openSpy).toHaveBeenCalledWith('#/test/1', '_blank')
        expect(pushSpy).not.toHaveBeenCalled()
      })

      it('opens in new tab on middle-click (auxclick, button === 1)', async () => {
        wrapper = createWrapper({ buttons: ['view'] })
        const viewButton = wrapper.findAll('button')[0]

        await viewButton.trigger('auxclick', { button: 1 })

        expect(openSpy).toHaveBeenCalledWith('#/test/1', '_blank')
        expect(pushSpy).not.toHaveBeenCalled()
      })

      it('does not trigger view on right-click (auxclick, button === 2)', async () => {
        wrapper = createWrapper({ buttons: ['view'] })
        const viewButton = wrapper.findAll('button')[0]

        await viewButton.trigger('auxclick', { button: 2 })

        expect(openSpy).not.toHaveBeenCalled()
        expect(pushSpy).not.toHaveBeenCalled()
      })

      it('emits viewObject on middle-click when emitViewObject is true', async () => {
        wrapper = createWrapper({ buttons: ['view'], emitViewObject: true })
        const viewButton = wrapper.findAll('button')[0]

        await viewButton.trigger('auxclick', { button: 1 })

        expect(wrapper.emitted('viewObject')).toBeTruthy()
        expect(openSpy).not.toHaveBeenCalled()
      })
    })

    it('emits editObject when edit button clicked and emitEditObject is true', async () => {
      wrapper = createWrapper({ buttons: ['edit'], emitEditObject: true })
      const editButtons = wrapper.findAll('button')

      await editButtons[0].trigger('click')

      expect(wrapper.emitted('editObject')).toBeTruthy()
    })

    describe('Dynamic Button Configuration', () => {
      it('supports object button config with type property', () => {
        wrapper = createWrapper({
          buttons: [{ type: 'view' }, { type: 'edit' }],
        })
        const rows = wrapper.findAll('tbody tr')
        const buttonsInFirstRow = rows[0].findAll('button')
        expect(buttonsInFirstRow.length).toBe(2)
      })

      it('supports mixed string and object button configs', () => {
        wrapper = createWrapper({
          buttons: ['view', { type: 'edit' }, { type: 'delete' }],
        })
        const rows = wrapper.findAll('tbody tr')
        const buttonsInFirstRow = rows[0].findAll('button')
        expect(buttonsInFirstRow.length).toBe(3)
      })

      it('hides button when visible function returns false', () => {
        wrapper = createWrapper({
          buttons: [
            'view',
            { type: 'edit', visible: (item) => item.status === 'active' },
          ],
        })
        const rows = wrapper.findAll('tbody tr')
        // Item 1 has status 'active', Item 2 has status 'inactive'
        const buttonsInRow1 = rows[0].findAll('button')
        const buttonsInRow2 = rows[1].findAll('button')
        expect(buttonsInRow1.length).toBe(2) // view + edit
        expect(buttonsInRow2.length).toBe(1) // only view
      })

      it('shows button when visible function returns true', () => {
        wrapper = createWrapper({
          buttons: [{ type: 'delete', visible: () => true }],
        })
        const rows = wrapper.findAll('tbody tr')
        expect(rows[0].findAll('button').length).toBe(1)
        expect(rows[1].findAll('button').length).toBe(1)
      })

      it('disables button when disabled function returns true', () => {
        wrapper = createWrapper({
          buttons: [{ type: 'edit', disabled: (item) => item.id === 1 }],
        })
        const rows = wrapper.findAll('tbody tr')
        const buttonInRow1 = rows[0].find('button')
        const buttonInRow2 = rows[1].find('button')
        expect(buttonInRow1.element.disabled).toBe(true)
        expect(buttonInRow2.element.disabled).toBe(false)
      })

      it('button is not disabled when disabled function returns false', () => {
        wrapper = createWrapper({
          buttons: [{ type: 'view', disabled: () => false }],
        })
        const rows = wrapper.findAll('tbody tr')
        const button = rows[0].find('button')
        expect(button.attributes('disabled')).toBeUndefined()
      })

      it('supports static boolean for visible property', () => {
        wrapper = createWrapper({
          buttons: [
            { type: 'view', visible: true },
            { type: 'edit', visible: false },
          ],
        })
        const rows = wrapper.findAll('tbody tr')
        const buttonsInFirstRow = rows[0].findAll('button')
        expect(buttonsInFirstRow.length).toBe(1) // only view
      })

      it('supports static boolean for disabled property', () => {
        wrapper = createWrapper({
          buttons: [{ type: 'edit', disabled: true }],
        })
        const rows = wrapper.findAll('tbody tr')
        const button = rows[0].find('button')
        expect(button.element.disabled).toBe(true)
      })

      it('renders button column when at least one button type is valid', () => {
        wrapper = createWrapper({
          buttons: [{ type: 'view', visible: () => false }],
        })
        // Header should still have the button column
        const headers = wrapper.findAll('th')
        // Count should include button column even if buttons are conditionally hidden
        expect(headers.length).toBeGreaterThan(2)
      })

      it('does not render disabled button click handler', async () => {
        wrapper = createWrapper({
          buttons: [{ type: 'delete', disabled: () => true }],
        })
        const deleteButton = wrapper.find('button')
        expect(deleteButton.element.disabled).toBe(true)
      })

      it('combines visible and disabled correctly', () => {
        const data = [
          { id: 1, name: 'Item 1', status: 'draft', createdAt: '2024-01-01' },
          {
            id: 2,
            name: 'Item 2',
            status: 'published',
            createdAt: '2024-01-02',
          },
          {
            id: 3,
            name: 'Item 3',
            status: 'archived',
            createdAt: '2024-01-03',
          },
        ]
        wrapper = createWrapper({
          data,
          itemsTotal: 3,
          buttons: [
            {
              type: 'edit',
              visible: (item) => item.status !== 'archived',
              disabled: (item) => item.status === 'published',
            },
          ],
        })
        const rows = wrapper.findAll('tbody tr')

        // Row 1: draft - visible, not disabled
        const row1Buttons = rows[0].findAll('button')
        expect(row1Buttons.length).toBe(1)
        expect(row1Buttons[0].element.disabled).toBe(false)

        // Row 2: published - visible, disabled
        const row2Buttons = rows[1].findAll('button')
        expect(row2Buttons.length).toBe(1)
        expect(row2Buttons[0].element.disabled).toBe(true)

        // Row 3: archived - not visible
        const row3Buttons = rows[2].findAll('button')
        expect(row3Buttons.length).toBe(0)
      })

      it('defaults to visible true when not specified', () => {
        wrapper = createWrapper({
          buttons: [{ type: 'view' }],
        })
        const rows = wrapper.findAll('tbody tr')
        expect(rows[0].findAll('button').length).toBe(1)
        expect(rows[1].findAll('button').length).toBe(1)
      })

      it('defaults to disabled false when not specified', () => {
        wrapper = createWrapper({
          buttons: [{ type: 'edit' }],
        })
        const rows = wrapper.findAll('tbody tr')
        const button = rows[0].find('button')
        expect(button.attributes('disabled')).toBeUndefined()
      })

      it('supports disabledTooltip as string', () => {
        wrapper = createWrapper({
          buttons: [
            {
              type: 'delete',
              disabled: () => true,
              disabledTooltip: 'Cannot delete protected item',
            },
          ],
        })
        // The tooltip directive is mocked, so we just verify the button is disabled
        const button = wrapper.find('button')
        expect(button.element.disabled).toBe(true)
      })

      it('supports disabledTooltip as function', () => {
        wrapper = createWrapper({
          buttons: [
            {
              type: 'delete',
              disabled: (item) => item.id === 1,
              disabledTooltip: (item) => `Cannot delete item ${item.id}`,
            },
          ],
        })
        const rows = wrapper.findAll('tbody tr')
        expect(rows[0].find('button').element.disabled).toBe(true)
        expect(rows[1].find('button').element.disabled).toBe(false)
      })
    })
  })

  describe('Search Functionality', () => {
    it('does not render inline search icons for columns', () => {
      const columns = [
        { key: 'name', label: 'Name', sortable: false },
        { key: 'status', label: 'Status', sortable: false },
      ]
      wrapper = createWrapper({
        columns,
        createdColumnEnabled: false,
      })

      const headers = wrapper.findAll('th')
      expect(headers[0].find('.icon').exists()).toBe(false)
      expect(headers[1].find('.icon').exists()).toBe(false)
    })
  })

  describe('Pagination', () => {
    it('renders pagination component by default', () => {
      wrapper = createWrapper()
      expect(wrapper.find('.pagination').exists()).toBe(true)
    })

    it('hides pagination when pagination prop is false', () => {
      wrapper = createWrapper({ pagination: false })
      expect(wrapper.find('.pagination').exists()).toBe(false)
    })

    it('passes correct props to pagination component', () => {
      wrapper = createWrapper({
        currentPage: 2,
        itemsTotal: 50,
        perPage: 25,
      })
      expect(wrapper.find('.pagination').exists()).toBe(true)
    })
  })

  describe('Checkable Rows', () => {
    it('renders checkbox cells when checkable is true', () => {
      wrapper = createWrapper({ checkable: true })
      const checkboxes = wrapper.findAll('input[type="checkbox"]')
      expect(checkboxes.length).toBe(2)
    })

    it('displays checked items above table', async () => {
      wrapper = createWrapper({ checkable: true })
      const checkbox = wrapper.find('input[type="checkbox"]')

      await checkbox.setValue(true)

      expect(wrapper.text()).toContain('Item 1')
    })

    it('emits checkedRowsChange when a row is checked', async () => {
      wrapper = createWrapper({ checkable: true })
      const checkbox = wrapper.find('input[type="checkbox"]')

      await checkbox.setValue(true)

      expect(wrapper.emitted('checkedRowsChange')).toBeTruthy()
      const emitted = wrapper.emitted('checkedRowsChange')
      expect(emitted[emitted.length - 1][0]).toEqual([
        expect.objectContaining({ id: 1, name: 'Item 1' }),
      ])
    })

    it('emits checkedRowsChange with empty array when row is unchecked', async () => {
      wrapper = createWrapper({ checkable: true })
      const checkbox = wrapper.find('input[type="checkbox"]')

      await checkbox.setValue(true)
      await checkbox.setValue(false)

      const emitted = wrapper.emitted('checkedRowsChange')
      expect(emitted[emitted.length - 1][0]).toEqual([])
    })

    it('emits checkedRowsChange with multiple rows', async () => {
      wrapper = createWrapper({ checkable: true })
      const checkboxes = wrapper.findAll('input[type="checkbox"]')

      await checkboxes[0].setValue(true)
      await checkboxes[1].setValue(true)

      const emitted = wrapper.emitted('checkedRowsChange')
      expect(emitted[emitted.length - 1][0]).toHaveLength(2)
    })

    it('clears checked rows and emits empty array when uncheckAll button is clicked', async () => {
      wrapper = createWrapper({ checkable: true })
      const checkbox = wrapper.find('input[type="checkbox"]')

      await checkbox.setValue(true)
      expect(wrapper.text()).toContain('Item 1')

      // Find the uncheckAll button (the X button in the checked rows bar)
      const uncheckBtn = wrapper.find(
        '.bg-gray-100\\/50 button, .dark\\:bg-slate-800 button',
      )
      await uncheckBtn.trigger('click')

      const emitted = wrapper.emitted('checkedRowsChange')
      expect(emitted[emitted.length - 1][0]).toEqual([])
    })

    it('preserves checked rows by ID when data changes', async () => {
      wrapper = createWrapper({ checkable: true })
      const checkbox = wrapper.find('input[type="checkbox"]')

      await checkbox.setValue(true)
      expect(wrapper.emitted('checkedRowsChange')).toBeTruthy()

      // Simulate data reload with same IDs but new object references
      const newData = [
        {
          id: 1,
          name: 'Item 1 Updated',
          status: 'active',
          createdAt: '2024-01-01',
        },
        {
          id: 2,
          name: 'Item 2 Updated',
          status: 'inactive',
          createdAt: '2024-01-02',
        },
      ]
      await wrapper.setProps({ data: newData })

      const emitted = wrapper.emitted('checkedRowsChange')
      // Previously checked item (id: 1) should still be selected with updated data
      expect(emitted[emitted.length - 1][0]).toEqual([newData[0]])
    })

    it('removes checked rows when their IDs disappear from new data', async () => {
      wrapper = createWrapper({ checkable: true })
      const checkbox = wrapper.find('input[type="checkbox"]')

      await checkbox.setValue(true)

      // Simulate data reload where checked item (id: 1) no longer exists
      await wrapper.setProps({
        data: [
          {
            id: 3,
            name: 'Item 3',
            status: 'active',
            createdAt: '2024-01-03',
          },
        ],
      })

      const emitted = wrapper.emitted('checkedRowsChange')
      expect(emitted[emitted.length - 1][0]).toEqual([])
    })

    it('uses first column key for display in checked rows strip', async () => {
      const columns = [
        { key: 'username', label: 'Person' },
        { key: 'role', label: 'Rolle' },
      ]
      const data = [
        { id: 1, username: 'alice', role: 'Student', createdAt: '2024-01-01' },
        { id: 2, username: 'bob', role: 'Dozent', createdAt: '2024-01-02' },
      ]
      wrapper = createWrapper({ columns, data, checkable: true, itemsTotal: 2 })
      const checkbox = wrapper.find('input[type="checkbox"]')

      await checkbox.setValue(true)

      expect(wrapper.text()).toContain('alice')
    })

    it('exposes clearCheckedRows method', async () => {
      wrapper = createWrapper({ checkable: true })
      const checkbox = wrapper.find('input[type="checkbox"]')

      await checkbox.setValue(true)
      expect(wrapper.vm.checkedRows.size).toBe(1)

      wrapper.vm.clearCheckedRows()

      expect(wrapper.vm.checkedRows.size).toBe(0)
    })
  })

  describe('Column Formatters', () => {
    it('applies custom formatter function to column values', () => {
      const formattedColumns = [
        {
          key: 'status',
          label: 'Status',
          formatter: (val) => `Status: ${val}`,
        },
      ]
      wrapper = createWrapper({ columns: formattedColumns })

      expect(wrapper.text()).toContain('Status: active')
      expect(wrapper.text()).toContain('Status: inactive')
    })

    it('applies array formatter based on boolean value', () => {
      const data = [
        { id: 1, name: 'Item 1', active: true, createdAt: '2024-01-01' },
        { id: 2, name: 'Item 2', active: false, createdAt: '2024-01-02' },
      ]
      const formattedColumns = [
        {
          key: 'active',
          label: 'Active',
          formatter: ['Yes', 'No'],
        },
      ]
      wrapper = createWrapper({ columns: formattedColumns, data })

      expect(wrapper.text()).toContain('Yes')
      expect(wrapper.text()).toContain('No')
    })

    it('renders PillTag for columns with color property', () => {
      const colorColumns = [
        {
          key: 'status',
          label: 'Status',
          color: () => 'green',
        },
      ]
      wrapper = createWrapper({ columns: colorColumns })

      expect(wrapper.find('.pill-tag').exists()).toBe(true)
    })

    it('renders PillTag with icon when column has both color and icon', () => {
      const colorIconColumns = [
        {
          key: 'status',
          label: 'Status',
          color: () => 'green',
          icon: () => 'mdi-check',
        },
      ]
      wrapper = createWrapper({ columns: colorIconColumns })

      expect(wrapper.findAll('.pill-tag').length).toBe(2)
    })
  })

  describe('Normalized Columns', () => {
    it('sets sortable to true by default', () => {
      wrapper = createWrapper()
      const sortIcons = wrapper.findAll('.icon')
      expect(sortIcons.length).toBeGreaterThan(0)
    })

    it('respects sortable: false on columns', () => {
      const nonSortableColumns = [
        { key: 'custom1', label: 'Custom 1', sortable: false },
        { key: 'custom2', label: 'Custom 2', sortable: false },
      ]
      wrapper = createWrapper({
        columns: nonSortableColumns,
        createdColumnEnabled: false,
      })

      const headers = wrapper.findAll('th')
      const icons = headers[0].findAll('.icon')
      expect(icons.length).toBe(0)
    })
  })

  describe('Symbol Column', () => {
    it('renders UserAvatar for symbol columns', () => {
      const symbolColumns = [
        { key: 'avatar', label: 'Avatar', symbol: true },
        { key: 'name', label: 'Name' },
      ]
      const dataWithAvatar = [
        { id: 1, avatar: 'user-1', name: 'Item 1', createdAt: '2024-01-01' },
      ]
      wrapper = createWrapper({
        columns: symbolColumns,
        data: dataWithAvatar,
        itemsTotal: 1,
        symbol: true,
      })

      expect(wrapper.find('.user-avatar').exists()).toBe(true)
    })
  })

  describe('Markdown Column', () => {
    it('renders MarkdownRenderer for markdown columns', () => {
      const markdownColumns = [
        { key: 'description', label: 'Description', markdown: true },
      ]
      const dataWithMarkdown = [
        {
          id: 1,
          description: '**Bold text**',
          createdAt: '2024-01-01',
        },
      ]
      wrapper = createWrapper({
        columns: markdownColumns,
        data: dataWithMarkdown,
        itemsTotal: 1,
      })

      expect(wrapper.find('.markdown').exists()).toBe(true)
    })
  })

  describe('Tooltip', () => {
    it('applies tooltip from column config', () => {
      const tooltipColumns = [
        {
          key: 'status',
          label: 'Status',
          color: () => 'green',
          tooltip: () => 'Status tooltip',
        },
      ]
      wrapper = createWrapper({ columns: tooltipColumns })

      expect(wrapper.find('.pill-tag').exists()).toBe(true)
    })
  })

  describe('Custom sortKey', () => {
    it('uses sortKey instead of key when provided', async () => {
      const columnsWithSortKey = [
        { key: 'displayName', label: 'Name', sortKey: 'name' },
      ]
      wrapper = createWrapper({
        columns: columnsWithSortKey,
        sortColumnKey: 'name',
      })

      const sortIcons = wrapper.findAll('.icon')
      await sortIcons[0].trigger('click')

      const emitted = wrapper.emitted('sortOrderChanged')
      expect(emitted[0]).toContain('name')
    })
  })

  describe('Formatter Output Sanitization', () => {
    it('escapes HTML tags in formatter output', () => {
      const columns = [
        {
          key: 'content',
          label: 'Content',
          formatter: () => '<script>alert("xss")</script>',
        },
      ]
      const data = [{ id: 1, content: 'test', createdAt: '2024-01-01' }]
      wrapper = createWrapper({ columns, data, itemsTotal: 1 })

      // HTML should be escaped, not rendered
      expect(wrapper.text()).toContain('<script>')
      expect(wrapper.html()).not.toContain('<script>alert')
    })

    it('escapes HTML tags with attributes in formatter output', () => {
      const columns = [
        {
          key: 'content',
          label: 'Content',
          formatter: () => '<img src="x" onerror="alert(1)">',
        },
      ]
      const data = [{ id: 1, content: 'test', createdAt: '2024-01-01' }]
      wrapper = createWrapper({ columns, data, itemsTotal: 1 })

      // HTML should be escaped - check that it's rendered as text, not as an actual img element
      expect(wrapper.text()).toContain('<img')
      expect(wrapper.text()).toContain('onerror=')
      // The img tag should NOT be rendered as an actual HTML element
      expect(wrapper.find('img').exists()).toBe(false)
    })

    it('escapes nested HTML tags in formatter output', () => {
      const columns = [
        {
          key: 'content',
          label: 'Content',
          formatter: () => '<div><span onclick="evil()">Click</span></div>',
        },
      ]
      const data = [{ id: 1, content: 'test', createdAt: '2024-01-01' }]
      wrapper = createWrapper({ columns, data, itemsTotal: 1 })

      expect(wrapper.text()).toContain('<div>')
      expect(wrapper.text()).toContain('<span')
    })

    it('displays plain text from formatter correctly', () => {
      const columns = [
        {
          key: 'content',
          label: 'Content',
          formatter: () => 'Plain text content',
        },
      ]
      const data = [{ id: 1, content: 'test', createdAt: '2024-01-01' }]
      wrapper = createWrapper({ columns, data, itemsTotal: 1 })

      expect(wrapper.text()).toContain('Plain text content')
    })

    it('handles special characters in formatter output', () => {
      const columns = [
        {
          key: 'content',
          label: 'Content',
          formatter: () => '< > & " \' © ® ™',
        },
      ]
      const data = [{ id: 1, content: 'test', createdAt: '2024-01-01' }]
      wrapper = createWrapper({ columns, data, itemsTotal: 1 })

      expect(wrapper.text()).toContain('< > & " \' © ® ™')
    })

    it('handles emoji in formatter output', () => {
      const columns = [
        {
          key: 'content',
          label: 'Content',
          formatter: () => '✅ ❌ 🚀 ⚠️',
        },
      ]
      const data = [{ id: 1, content: 'test', createdAt: '2024-01-01' }]
      wrapper = createWrapper({ columns, data, itemsTotal: 1 })

      expect(wrapper.text()).toContain('✅')
      expect(wrapper.text()).toContain('❌')
      expect(wrapper.text()).toContain('🚀')
    })

    it('handles null value in formatter', () => {
      const columns = [
        {
          key: 'content',
          label: 'Content',
          formatter: (val) => val ?? 'N/A',
        },
      ]
      const data = [{ id: 1, content: null, createdAt: '2024-01-01' }]
      wrapper = createWrapper({ columns, data, itemsTotal: 1 })

      expect(wrapper.text()).toContain('N/A')
    })

    it('handles undefined value in formatter', () => {
      const columns = [
        {
          key: 'content',
          label: 'Content',
          formatter: (val) => val ?? 'Undefined',
        },
      ]
      const data = [{ id: 1, createdAt: '2024-01-01' }] // content is undefined
      wrapper = createWrapper({ columns, data, itemsTotal: 1 })

      expect(wrapper.text()).toContain('Undefined')
    })

    it('handles empty string in formatter', () => {
      const columns = [
        {
          key: 'content',
          label: 'Content',
          formatter: (val) => val || 'Empty',
        },
      ]
      const data = [{ id: 1, content: '', createdAt: '2024-01-01' }]
      wrapper = createWrapper({ columns, data, itemsTotal: 1 })

      expect(wrapper.text()).toContain('Empty')
    })

    it('handles number values in formatter', () => {
      const columns = [
        {
          key: 'amount',
          label: 'Amount',
          formatter: (val) => `€ ${val.toFixed(2)}`,
        },
      ]
      const data = [{ id: 1, amount: 1234.5, createdAt: '2024-01-01' }]
      wrapper = createWrapper({ columns, data, itemsTotal: 1 })

      expect(wrapper.text()).toContain('€ 1234.50')
    })

    it('handles array formatter with truthy value', () => {
      const columns = [
        {
          key: 'active',
          label: 'Active',
          formatter: ['Aktiv', 'Inaktiv'],
        },
      ]
      const data = [{ id: 1, active: true, createdAt: '2024-01-01' }]
      wrapper = createWrapper({ columns, data, itemsTotal: 1 })

      expect(wrapper.text()).toContain('Aktiv')
    })

    it('handles array formatter with falsy value', () => {
      const columns = [
        {
          key: 'active',
          label: 'Active',
          formatter: ['Aktiv', 'Inaktiv'],
        },
      ]
      const data = [{ id: 1, active: false, createdAt: '2024-01-01' }]
      wrapper = createWrapper({ columns, data, itemsTotal: 1 })

      expect(wrapper.text()).toContain('Inaktiv')
    })

    it('handles array formatter with zero value (falsy)', () => {
      const columns = [
        {
          key: 'count',
          label: 'Count',
          formatter: ['Has items', 'No items'],
        },
      ]
      const data = [{ id: 1, count: 0, createdAt: '2024-01-01' }]
      wrapper = createWrapper({ columns, data, itemsTotal: 1 })

      expect(wrapper.text()).toContain('No items')
    })

    it('handles formatter returning object by converting to string', () => {
      const columns = [
        {
          key: 'data',
          label: 'Data',
          formatter: () => ({ key: 'value' }),
        },
      ]
      const data = [{ id: 1, data: 'test', createdAt: '2024-01-01' }]
      wrapper = createWrapper({ columns, data, itemsTotal: 1 })

      // Vue renders objects as JSON
      expect(wrapper.text()).toContain('"key"')
      expect(wrapper.text()).toContain('"value"')
    })

    it('handles formatter returning array by converting to string', () => {
      const columns = [
        {
          key: 'tags',
          label: 'Tags',
          formatter: () => ['tag1', 'tag2', 'tag3'],
        },
      ]
      const data = [{ id: 1, tags: [], createdAt: '2024-01-01' }]
      wrapper = createWrapper({ columns, data, itemsTotal: 1 })

      // Vue renders arrays as JSON
      expect(wrapper.text()).toContain('tag1')
      expect(wrapper.text()).toContain('tag2')
      expect(wrapper.text()).toContain('tag3')
    })

    it('handles long text in formatter output', () => {
      const longText = 'A'.repeat(500)
      const columns = [
        {
          key: 'content',
          label: 'Content',
          formatter: () => longText,
        },
      ]
      const data = [{ id: 1, content: 'test', createdAt: '2024-01-01' }]
      wrapper = createWrapper({ columns, data, itemsTotal: 1 })

      expect(wrapper.text()).toContain(longText)
    })

    it('handles unicode characters in formatter output', () => {
      const columns = [
        {
          key: 'content',
          label: 'Content',
          formatter: () => '日本語 中文 한국어 العربية',
        },
      ]
      const data = [{ id: 1, content: 'test', createdAt: '2024-01-01' }]
      wrapper = createWrapper({ columns, data, itemsTotal: 1 })

      expect(wrapper.text()).toContain('日本語')
      expect(wrapper.text()).toContain('中文')
      expect(wrapper.text()).toContain('한국어')
      expect(wrapper.text()).toContain('العربية')
    })

    it('handles newlines in formatter output', () => {
      const columns = [
        {
          key: 'content',
          label: 'Content',
          formatter: () => 'Line 1\nLine 2\nLine 3',
        },
      ]
      const data = [{ id: 1, content: 'test', createdAt: '2024-01-01' }]
      wrapper = createWrapper({ columns, data, itemsTotal: 1 })

      expect(wrapper.text()).toContain('Line 1')
      expect(wrapper.text()).toContain('Line 2')
      expect(wrapper.text()).toContain('Line 3')
    })

    it('handles tabs in formatter output', () => {
      const columns = [
        {
          key: 'content',
          label: 'Content',
          formatter: () => 'Col1\tCol2\tCol3',
        },
      ]
      const data = [{ id: 1, content: 'test', createdAt: '2024-01-01' }]
      wrapper = createWrapper({ columns, data, itemsTotal: 1 })

      expect(wrapper.text()).toContain('Col1')
      expect(wrapper.text()).toContain('Col2')
      expect(wrapper.text()).toContain('Col3')
    })
  })

  describe('Custom Cell Slots', () => {
    it('renders custom slot content when provided', () => {
      const columns = [{ key: 'custom', label: 'Custom' }]
      const data = [{ id: 1, custom: 'original', createdAt: '2024-01-01' }]

      wrapper = mount(BaseTable, {
        props: { ...defaultProps, columns, data, itemsTotal: 1 },
        slots: {
          'cell-custom': '<span class="custom-slot">Custom Content</span>',
        },
        global: {
          stubs: { transition: false },
          directives: { tooltip: () => {} },
        },
      })

      expect(wrapper.find('.custom-slot').exists()).toBe(true)
      expect(wrapper.text()).toContain('Custom Content')
    })

    it('passes item, column, and value as slot props', () => {
      const columns = [{ key: 'status', label: 'Status' }]
      const data = [
        { id: 1, status: 'active', createdAt: '2024-01-01' },
        { id: 2, status: 'inactive', createdAt: '2024-01-02' },
      ]

      wrapper = mount(BaseTable, {
        props: { ...defaultProps, columns, data, itemsTotal: 2 },
        slots: {
          'cell-status': `
            <template #cell-status="{ item, value }">
              <span class="status-slot" :data-id="item.id">{{ value }}</span>
            </template>
          `,
        },
        global: {
          stubs: { transition: false },
          directives: { tooltip: () => {} },
        },
      })

      const slots = wrapper.findAll('.status-slot')
      expect(slots.length).toBe(2)
      expect(slots[0].text()).toBe('active')
      expect(slots[1].text()).toBe('inactive')
    })

    it('custom slot takes priority over other column types', () => {
      const columns = [
        {
          key: 'status',
          label: 'Status',
          color: () => 'green',
          formatter: () => 'Formatted',
        },
      ]
      const data = [{ id: 1, status: 'active', createdAt: '2024-01-01' }]

      wrapper = mount(BaseTable, {
        props: { ...defaultProps, columns, data, itemsTotal: 1 },
        slots: {
          'cell-status': '<span class="override-slot">Overridden</span>',
        },
        global: {
          stubs: { transition: false },
          directives: { tooltip: () => {} },
        },
      })

      expect(wrapper.find('.override-slot').exists()).toBe(true)
      expect(wrapper.text()).toContain('Overridden')
      expect(wrapper.find('.pill-tag').exists()).toBe(false)
    })

    it('renders default content when no slot is provided', () => {
      const columns = [{ key: 'name', label: 'Name' }]
      const data = [{ id: 1, name: 'Test Item', createdAt: '2024-01-01' }]

      wrapper = createWrapper({ columns, data, itemsTotal: 1 })

      expect(wrapper.text()).toContain('Test Item')
    })

    it('supports multiple custom slots for different columns', () => {
      const columns = [
        { key: 'col1', label: 'Column 1' },
        { key: 'col2', label: 'Column 2' },
      ]
      const data = [
        { id: 1, col1: 'val1', col2: 'val2', createdAt: '2024-01-01' },
      ]

      wrapper = mount(BaseTable, {
        props: { ...defaultProps, columns, data, itemsTotal: 1 },
        slots: {
          'cell-col1': '<span class="slot-1">Slot 1</span>',
          'cell-col2': '<span class="slot-2">Slot 2</span>',
        },
        global: {
          stubs: { transition: false },
          directives: { tooltip: () => {} },
        },
      })

      expect(wrapper.find('.slot-1').exists()).toBe(true)
      expect(wrapper.find('.slot-2').exists()).toBe(true)
    })

    it('renders complex HTML in custom slot', () => {
      const columns = [{ key: 'changes', label: 'Changes' }]
      const data = [
        {
          id: 1,
          changes: [{ field: 'name', old: 'A', new: 'B' }],
          createdAt: '2024-01-01',
        },
      ]

      wrapper = mount(BaseTable, {
        props: { ...defaultProps, columns, data, itemsTotal: 1 },
        slots: {
          'cell-changes': `
            <template #cell-changes="{ value }">
              <ul class="changes-list">
                <li v-for="(change, i) in value" :key="i">
                  <s>{{ change.old }}</s> → {{ change.new }}
                </li>
              </ul>
            </template>
          `,
        },
        global: {
          stubs: { transition: false },
          directives: { tooltip: () => {} },
        },
      })

      expect(wrapper.find('.changes-list').exists()).toBe(true)
      expect(wrapper.find('s').text()).toBe('A')
      expect(wrapper.text()).toContain('→')
      expect(wrapper.text()).toContain('B')
    })
  })

  describe('Integrated Search Bar', () => {
    const searchBarFields = [
      { key: 'name', label: 'Name', operators: SearchOperators.TEXT },
      {
        key: 'status',
        label: 'Status',
        operators: SearchOperators.EQUALS_ONLY,
      },
    ]

    it('renders TableSearchBar when searchBar prop is true', async () => {
      wrapper = createWrapper({
        searchBar: true,
        searchBarFields,
      })
      await flushPromises()
      expect(wrapper.findComponent({ name: 'TableSearchBar' }).exists()).toBe(
        true,
      )
    })

    it('does not render TableSearchBar when searchBarFields is empty', () => {
      wrapper = createWrapper({
        searchBarFields: [],
      })
      expect(wrapper.findComponent({ name: 'TableSearchBar' }).exists()).toBe(
        false,
      )
    })

    it('hides column filter icons when searchBar is enabled', () => {
      const filterColumns = [
        {
          key: 'status',
          label: 'Status',
          sortable: false,
          filters: [
            { value: 'active', label: 'Aktiv' },
            { value: 'inactive', label: 'Inaktiv' },
          ],
        },
      ]
      wrapper = createWrapper({
        columns: filterColumns,
        searchBar: true,
        searchBarFields,
        createdColumnEnabled: false,
      })

      const header = wrapper.find('th')
      const icons = header.findAll('.icon')
      expect(icons.length).toBe(0)
    })

    it('emits searchTriggered when filter changes', async () => {
      wrapper = createWrapper({
        searchBar: true,
        searchBarFields,
      })
      await flushPromises()

      const searchBar = wrapper.findComponent({ name: 'TableSearchBar' })
      await searchBar.vm.$emit('filtersChanged', {
        filters: [{ field: 'name', operator: 'eq', value: 'test' }],
        objectModel: 'test',
      })

      const emitted = wrapper.emitted('searchTriggered')
      expect(emitted).toBeTruthy()
      expect(emitted[0][0]).toEqual({
        field: 'name',
        value: 'test',
        operator: 'eq',
        filters: [{ field: 'name', operator: 'eq', value: 'test' }],
        objectModel: 'test',
      })
    })

    it('emits empty search when filters cleared', async () => {
      wrapper = createWrapper({
        searchBar: true,
        searchBarFields,
      })
      await flushPromises()

      const searchBar = wrapper.findComponent({ name: 'TableSearchBar' })
      await searchBar.vm.$emit('filtersChanged', {
        filters: [],
        objectModel: 'test',
      })

      const emitted = wrapper.emitted('searchTriggered')
      expect(emitted).toBeTruthy()
      expect(emitted[0][0]).toEqual({
        field: '',
        value: '',
        objectModel: 'test',
      })
    })

    it('passes correct props to TableSearchBar', async () => {
      wrapper = createWrapper({
        searchBar: true,
        searchBarFields,
        searchBarMaxFilters: 5,
        searchBarPlaceholder: 'Custom placeholder...',
        searchBarQueryKey: 'customKey',
        searchBarSyncQuery: false,
        searchBarInitialFilters: [
          { field: 'name', operator: 'eq', value: 'initial' },
        ],
      })
      await flushPromises()

      const searchBar = wrapper.findComponent({ name: 'TableSearchBar' })
      expect(searchBar.props('fields')).toEqual(searchBarFields)
      expect(searchBar.props('maxFilters')).toBe(5)
      expect(searchBar.props('placeholder')).toBe('Custom placeholder...')
      expect(searchBar.props('queryKey')).toBe('customKey')
      expect(searchBar.props('syncQuery')).toBe(false)
      expect(searchBar.props('initialFilters')).toEqual([
        { field: 'name', operator: 'eq', value: 'initial' },
      ])
    })

    it('exposes clearSearchBar method', () => {
      wrapper = createWrapper({
        searchBar: true,
        searchBarFields,
      })

      expect(typeof wrapper.vm.clearSearchBar).toBe('function')
    })

    it('exposes focusSearchBar method', () => {
      wrapper = createWrapper({
        searchBar: true,
        searchBarFields,
      })

      expect(typeof wrapper.vm.focusSearchBar).toBe('function')
    })

    it('renders TableSearchBar when only searchBarFields is provided', async () => {
      wrapper = createWrapper({
        searchBarFields,
      })
      await flushPromises()
      expect(wrapper.findComponent({ name: 'TableSearchBar' }).exists()).toBe(
        true,
      )
    })

    it('does not render TableSearchBar when searchBarFields is empty and searchBar is not set', () => {
      wrapper = createWrapper({
        searchBarFields: [],
      })
      expect(wrapper.findComponent({ name: 'TableSearchBar' }).exists()).toBe(
        false,
      )
    })

    it('uses default queryKey "filter" when no searchBarQueryKey is provided', async () => {
      wrapper = createWrapper({
        searchBarFields,
      })
      await flushPromises()

      const searchBar = wrapper.findComponent({ name: 'TableSearchBar' })
      expect(searchBar.props('queryKey')).toBe('filter')
    })

    it('uses explicit searchBarQueryKey when provided', async () => {
      wrapper = createWrapper({
        searchBarFields,
        searchBarQueryKey: 'filter-users',
      })
      await flushPromises()

      const searchBar = wrapper.findComponent({ name: 'TableSearchBar' })
      expect(searchBar.props('queryKey')).toBe('filter-users')
    })
  })
})
