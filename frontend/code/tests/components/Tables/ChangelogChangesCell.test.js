import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import ChangelogChangesCell from '@/components/Tables/ChangelogChangesCell.vue'

describe('ChangelogChangesCell', () => {
  // Helper functions to pass as props
  const formatFieldKey = (key) => {
    const labels = {
      name: 'Name',
      status: 'Status',
      description: 'Beschreibung',
    }
    return labels[key] || key
  }

  const formatDisplayValue = (value) => {
    if (value === null || value === undefined || value === '') {
      return { isEmpty: true, value: '(kein Wert)' }
    }
    if (Array.isArray(value)) {
      return { isList: true, items: value }
    }
    return { isSimple: true, value }
  }

  const shortenMiddle = (str, maxLength = 80) => {
    if (str === null || str === undefined) return ''
    if (typeof str !== 'string') str = String(str)
    if (str.length <= maxLength) return str
    return `${str.slice(0, 30)}[...]${str.slice(-30)}`
  }

  const defaultProps = {
    formatFieldKey,
    formatDisplayValue,
    shortenMiddle,
  }

  const createWrapper = (props = {}) => {
    return mount(ChangelogChangesCell, {
      props: { ...defaultProps, ...props },
    })
  }

  describe('Rendering', () => {
    it('renders component', () => {
      const wrapper = createWrapper({ changes: [] })
      expect(wrapper.exists()).toBe(true)
    })

    it('shows no changes message when changes is empty', () => {
      const wrapper = createWrapper({ changes: [] })
      expect(wrapper.text()).toContain('(keine Änderungen)')
    })

    it('shows no changes message when changes is null', () => {
      const wrapper = createWrapper({ changes: null })
      expect(wrapper.text()).toContain('(keine Änderungen)')
    })

    it('shows no changes message when changes is undefined', () => {
      const wrapper = createWrapper({ changes: undefined })
      expect(wrapper.text()).toContain('(keine Änderungen)')
    })
  })

  describe('Structured Changes', () => {
    it('renders a single change correctly', () => {
      const changes = [
        {
          key: 'name',
          oldValue: 'Old Name',
          newValue: 'New Name',
          isRaw: false,
        },
      ]
      const wrapper = createWrapper({ changes })

      expect(wrapper.text()).toContain('Name')
      expect(wrapper.text()).toContain('Old Name')
      expect(wrapper.text()).toContain('New Name')
      expect(wrapper.text()).toContain('→')
    })

    it('renders multiple changes as list', () => {
      const changes = [
        { key: 'name', oldValue: 'A', newValue: 'B', isRaw: false },
        {
          key: 'status',
          oldValue: 'active',
          newValue: 'inactive',
          isRaw: false,
        },
      ]
      const wrapper = createWrapper({ changes })

      const listItems = wrapper.findAll('li')
      expect(listItems.length).toBe(2)
    })

    it('applies strikethrough to old value', () => {
      const changes = [
        { key: 'name', oldValue: 'Old', newValue: 'New', isRaw: false },
      ]
      const wrapper = createWrapper({ changes })

      const strikethrough = wrapper.find('s')
      expect(strikethrough.exists()).toBe(true)
      expect(strikethrough.text()).toContain('Old')
    })

    it('formats field key using provided function', () => {
      const changes = [
        { key: 'description', oldValue: 'A', newValue: 'B', isRaw: false },
      ]
      const wrapper = createWrapper({ changes })

      expect(wrapper.text()).toContain('Beschreibung')
    })

    it('renders empty value indicator for null oldValue', () => {
      const changes = [
        { key: 'name', oldValue: null, newValue: 'New Value', isRaw: false },
      ]
      const wrapper = createWrapper({ changes })

      expect(wrapper.text()).toContain('(kein Wert)')
      expect(wrapper.text()).toContain('New Value')
    })

    it('renders empty value indicator for empty string newValue', () => {
      const changes = [
        { key: 'name', oldValue: 'Old Value', newValue: '', isRaw: false },
      ]
      const wrapper = createWrapper({ changes })

      expect(wrapper.text()).toContain('Old Value')
      expect(wrapper.text()).toContain('(kein Wert)')
    })
  })

  describe('List Values', () => {
    it('renders array values as list items', () => {
      const formatDisplayValueWithList = (value) => {
        if (Array.isArray(value)) {
          return { isList: true, items: value }
        }
        return { isSimple: true, value }
      }

      const changes = [
        {
          key: 'roles',
          oldValue: ['Admin', 'User'],
          newValue: ['Admin', 'User', 'Manager'],
          isRaw: false,
        },
      ]
      const wrapper = createWrapper({
        changes,
        formatDisplayValue: formatDisplayValueWithList,
      })

      expect(wrapper.text()).toContain('Admin')
      expect(wrapper.text()).toContain('User')
      expect(wrapper.text()).toContain('Manager')
    })

    it('renders nested lists correctly', () => {
      const changes = [
        {
          key: 'tags',
          oldValue: ['tag1'],
          newValue: ['tag1', 'tag2', 'tag3'],
          isRaw: false,
        },
      ]
      const wrapper = createWrapper({ changes })

      const listItems = wrapper.findAll('ul li')
      expect(listItems.length).toBeGreaterThan(0)
    })
  })

  describe('Raw Diff', () => {
    it('renders raw diff format for isRaw: true', () => {
      const changes = [
        { key: 'Raw-Diff', oldValue: 'UNKWN', newValue: 'UNKWN', isRaw: true },
      ]
      const wrapper = createWrapper({ changes })

      expect(wrapper.text()).toContain('Raw-Diff')
      const preElements = wrapper.findAll('pre')
      expect(preElements.length).toBe(2)
    })

    it('shows minus prefix for old value in raw diff', () => {
      const changes = [
        {
          key: 'Raw-Diff',
          oldValue: 'old data',
          newValue: 'new data',
          isRaw: true,
        },
      ]
      const wrapper = createWrapper({ changes })

      const preElements = wrapper.findAll('pre')
      expect(preElements[0].text()).toContain('-')
      expect(preElements[0].text()).toContain('old data')
    })

    it('shows plus prefix for new value in raw diff', () => {
      const changes = [
        {
          key: 'Raw-Diff',
          oldValue: 'old data',
          newValue: 'new data',
          isRaw: true,
        },
      ]
      const wrapper = createWrapper({ changes })

      const preElements = wrapper.findAll('pre')
      expect(preElements[1].text()).toContain('+')
      expect(preElements[1].text()).toContain('new data')
    })

    it('applies correct color classes to raw diff', () => {
      const changes = [
        { key: 'Raw-Diff', oldValue: 'old', newValue: 'new', isRaw: true },
      ]
      const wrapper = createWrapper({ changes })

      const preElements = wrapper.findAll('pre')
      expect(preElements[0].classes()).toContain('text-red-500')
      expect(preElements[1].classes()).toContain('text-green-600')
    })
  })

  describe('Value Shortening', () => {
    it('shortens long values using shortenMiddle', () => {
      const longValue = 'A'.repeat(100)
      const changes = [
        {
          key: 'content',
          oldValue: longValue,
          newValue: 'short',
          isRaw: false,
        },
      ]
      const wrapper = createWrapper({ changes })

      expect(wrapper.text()).toContain('[...]')
      expect(wrapper.text()).not.toContain(longValue)
    })

    it('does not shorten short values', () => {
      const shortValue = 'Short text'
      const changes = [
        { key: 'name', oldValue: shortValue, newValue: 'New', isRaw: false },
      ]
      const wrapper = createWrapper({ changes })

      expect(wrapper.text()).toContain(shortValue)
      expect(wrapper.text()).not.toContain('[...]')
    })
  })

  describe('Boolean Values', () => {
    it('renders boolean true correctly', () => {
      const formatDisplayValueWithBoolean = (value) => {
        if (typeof value === 'boolean') {
          return { isSimple: true, value: value ? 'Ja' : 'Nein' }
        }
        return { isSimple: true, value }
      }

      const changes = [
        { key: 'active', oldValue: false, newValue: true, isRaw: false },
      ]
      const wrapper = createWrapper({
        changes,
        formatDisplayValue: formatDisplayValueWithBoolean,
      })

      expect(wrapper.text()).toContain('Ja')
      expect(wrapper.text()).toContain('Nein')
    })
  })

  describe('Styling', () => {
    it('applies changelog-item class to list items', () => {
      const changes = [
        { key: 'name', oldValue: 'A', newValue: 'B', isRaw: false },
      ]
      const wrapper = createWrapper({ changes })

      expect(wrapper.find('.changelog-item').exists()).toBe(true)
    })

    it('applies changelog-value class to value spans', () => {
      const changes = [
        { key: 'name', oldValue: 'A', newValue: 'B', isRaw: false },
      ]
      const wrapper = createWrapper({ changes })

      const valueSpans = wrapper.findAll('.changelog-value')
      expect(valueSpans.length).toBe(2)
    })

    it('applies italic style to empty values', () => {
      const changes = [
        { key: 'name', oldValue: null, newValue: 'New', isRaw: false },
      ]
      const wrapper = createWrapper({ changes })

      const italicSpan = wrapper.find('.italic')
      expect(italicSpan.exists()).toBe(true)
      expect(italicSpan.text()).toContain('(kein Wert)')
    })
  })
})
