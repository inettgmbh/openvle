import { beforeEach, describe, expect, it } from 'vitest'
import { nextTick, ref } from 'vue'

import {
  extractPlaceholders,
  extractRawPlaceholders,
  getAllPlaceholders,
  getValidPlaceholders,
  isValidPlaceholderFormat,
  PLACEHOLDER_DEFINITIONS,
  useMailTemplatePlaceholders,
} from '@/composables/useMailTemplatePlaceholders'

describe('useMailTemplatePlaceholders', () => {
  describe('isValidPlaceholderFormat', () => {
    it('returns true for valid placeholder starting with letter', () => {
      expect(isValidPlaceholderFormat('user.name')).toBe(true)
    })

    it('returns true for valid placeholder starting with underscore', () => {
      expect(isValidPlaceholderFormat('_private.field')).toBe(true)
    })

    it('returns true for simple name', () => {
      expect(isValidPlaceholderFormat('name')).toBe(true)
    })

    it('returns false for placeholder starting with number', () => {
      expect(isValidPlaceholderFormat('3232')).toBe(false)
    })

    it('returns false for placeholder with number.number', () => {
      expect(isValidPlaceholderFormat('32.32')).toBe(false)
    })

    it('returns false for placeholder with special characters', () => {
      expect(isValidPlaceholderFormat('/("$/($)")')).toBe(false)
    })

    it('returns false for placeholder with spaces', () => {
      expect(isValidPlaceholderFormat('user name')).toBe(false)
    })

    it('returns false for placeholder with hyphens', () => {
      expect(isValidPlaceholderFormat('user-name')).toBe(false)
    })

    it('returns false for empty string', () => {
      expect(isValidPlaceholderFormat('')).toBe(false)
    })
  })

  describe('extractRawPlaceholders', () => {
    it('returns empty array for null content', () => {
      expect(extractRawPlaceholders(null)).toEqual([])
    })

    it('returns empty array for empty string', () => {
      expect(extractRawPlaceholders('')).toEqual([])
    })

    it('extracts valid placeholder', () => {
      const result = extractRawPlaceholders('Hello {{ user.name }}!')
      expect(result).toContain('user.name')
    })

    it('extracts invalid placeholder starting with number', () => {
      const result = extractRawPlaceholders('Test {{ 3232 }}')
      expect(result).toContain('3232')
    })

    it('extracts placeholder with special characters', () => {
      const result = extractRawPlaceholders('Test {{ /("$/($)")}}')
      expect(result).toContain('/("$/($)")')
    })

    it('extracts mixed valid and invalid placeholders', () => {
      const result = extractRawPlaceholders(
        '{{ user.name }} {{ 3232 }} {{ event.id }}',
      )
      expect(result).toContain('user.name')
      expect(result).toContain('3232')
      expect(result).toContain('event.id')
    })

    it('removes duplicates', () => {
      const result = extractRawPlaceholders('{{ 3232 }} and {{ 3232 }}')
      expect(result).toEqual(['3232'])
    })

    it('trims whitespace', () => {
      const result = extractRawPlaceholders('{{   3232   }}')
      expect(result).toEqual(['3232'])
    })

    it('ignores empty braces', () => {
      const result = extractRawPlaceholders('{{   }}')
      expect(result).toEqual([])
    })
  })

  describe('extractPlaceholders', () => {
    it('returns empty array for null content', () => {
      expect(extractPlaceholders(null)).toEqual([])
    })

    it('returns empty array for empty string', () => {
      expect(extractPlaceholders('')).toEqual([])
    })

    it('extracts single placeholder', () => {
      const result = extractPlaceholders('Hello {{ user.name }}!')
      expect(result).toEqual(['user.name'])
    })

    it('extracts multiple placeholders', () => {
      const result = extractPlaceholders(
        'Hello {{ user.name }}, your email is {{ user.email }}',
      )
      expect(result).toContain('user.name')
      expect(result).toContain('user.email')
    })

    it('removes duplicate placeholders', () => {
      const result = extractPlaceholders(
        '{{ user.name }} and {{ user.name }} again',
      )
      expect(result).toEqual(['user.name'])
    })

    it('handles placeholders without spaces', () => {
      const result = extractPlaceholders('{{user.name}}')
      expect(result).toEqual(['user.name'])
    })

    it('handles placeholders with extra spaces', () => {
      const result = extractPlaceholders('{{   user.name   }}')
      expect(result).toEqual(['user.name'])
    })

    it('handles mixed spacing', () => {
      const result = extractPlaceholders(
        '{{user.name}} {{ user.email }} {{  project.name  }}',
      )
      expect(result).toContain('user.name')
      expect(result).toContain('user.email')
      expect(result).toContain('project.name')
    })

    it('handles nested object placeholders', () => {
      const result = extractPlaceholders('{{ event.name }}')
      expect(result).toEqual(['event.name'])
    })

    it('ignores invalid placeholder syntax', () => {
      const result = extractPlaceholders('{ user.name } and {user.name}')
      expect(result).toEqual([])
    })

    it('ignores placeholders starting with numbers', () => {
      const result = extractPlaceholders('{{ 123.name }}')
      expect(result).toEqual([])
    })
  })

  describe('getAllPlaceholders', () => {
    it('returns all placeholders from all contexts', () => {
      const all = getAllPlaceholders()
      expect(all).toContain('user.name')
      expect(all).toContain('user.email')
      expect(all).toContain('project.name')
      expect(all).toContain('event.name')
      expect(all).toContain('virtualmachine.name')
    })

    it('includes always placeholders', () => {
      const all = getAllPlaceholders()
      PLACEHOLDER_DEFINITIONS.always.forEach((p) => {
        expect(all).toContain(p)
      })
    })

    it('includes events placeholders', () => {
      const all = getAllPlaceholders()
      PLACEHOLDER_DEFINITIONS.events.forEach((p) => {
        expect(all).toContain(p)
      })
    })

    it('includes virtualmachines placeholders', () => {
      const all = getAllPlaceholders()
      PLACEHOLDER_DEFINITIONS.virtualmachines.forEach((p) => {
        expect(all).toContain(p)
      })
    })
  })

  describe('getValidPlaceholders', () => {
    it('returns only always placeholders for null context', () => {
      const valid = getValidPlaceholders(null)
      expect(valid).toEqual(PLACEHOLDER_DEFINITIONS.always)
    })

    it('returns always + events placeholders for events context', () => {
      const valid = getValidPlaceholders('events')
      PLACEHOLDER_DEFINITIONS.always.forEach((p) => {
        expect(valid).toContain(p)
      })
      PLACEHOLDER_DEFINITIONS.events.forEach((p) => {
        expect(valid).toContain(p)
      })
      PLACEHOLDER_DEFINITIONS.virtualmachines.forEach((p) => {
        expect(valid).not.toContain(p)
      })
    })

    it('returns always + vm placeholders for virtualmachines context', () => {
      const valid = getValidPlaceholders('virtualmachines')
      PLACEHOLDER_DEFINITIONS.always.forEach((p) => {
        expect(valid).toContain(p)
      })
      PLACEHOLDER_DEFINITIONS.virtualmachines.forEach((p) => {
        expect(valid).toContain(p)
      })
      PLACEHOLDER_DEFINITIONS.events.forEach((p) => {
        expect(valid).not.toContain(p)
      })
    })

    it('returns only always placeholders for unknown context', () => {
      const valid = getValidPlaceholders('unknown')
      expect(valid).toEqual(PLACEHOLDER_DEFINITIONS.always)
    })
  })

  describe('useMailTemplatePlaceholders composable', () => {
    let content
    let actions
    let selectedActionId

    beforeEach(() => {
      content = ref('')
      actions = ref([])
      selectedActionId = ref('')
    })

    describe('Initialization', () => {
      it('initializes with empty validation error', () => {
        const { validationError } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })
        expect(validationError.value).toBe('')
      })

      it('initializes with canSubmit as true', () => {
        const { canSubmit } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })
        expect(canSubmit.value).toBe(true)
      })

      it('initializes with empty invalidPlaceholders', () => {
        const { invalidPlaceholders } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })
        expect(invalidPlaceholders.value).toEqual([])
      })
    })

    describe('Context Detection', () => {
      it('returns null context when no action selected', () => {
        const { selectedActionContext } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })
        expect(selectedActionContext.value).toBeNull()
      })

      it('returns null context when actions array is empty', () => {
        selectedActionId.value = 'action-123'
        const { selectedActionContext } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })
        expect(selectedActionContext.value).toBeNull()
      })

      it('detects events context from slug prefix', async () => {
        actions.value = [{ value: 'action-123', slug: 'events_notification' }]
        selectedActionId.value = 'action-123'

        const { selectedActionContext } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })

        await nextTick()
        expect(selectedActionContext.value).toBe('events')
      })

      it('detects virtualmachines context from slug prefix', async () => {
        actions.value = [{ value: 'action-456', slug: 'vm_created' }]
        selectedActionId.value = 'action-456'

        const { selectedActionContext } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })

        await nextTick()
        expect(selectedActionContext.value).toBe('virtualmachines')
      })

      it('returns null for generic slug without prefix', async () => {
        actions.value = [{ value: 'action-789', slug: 'generic_action' }]
        selectedActionId.value = 'action-789'

        const { selectedActionContext } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })

        await nextTick()
        expect(selectedActionContext.value).toBeNull()
      })
    })

    describe('Validation without action', () => {
      it('allows valid always placeholders', async () => {
        content.value = 'Hello {{ user.name }}, from {{ project.name }}'

        const { validationError, canSubmit } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })

        await nextTick()
        expect(validationError.value).toBe('')
        expect(canSubmit.value).toBe(true)
      })

      it('detects unknown placeholders', async () => {
        content.value = 'Hello {{ unknown.placeholder }}'

        const { validationError, canSubmit, invalidPlaceholders } =
          useMailTemplatePlaceholders({
            content,
            actions,
            selectedActionId,
          })

        await nextTick()
        expect(invalidPlaceholders.value).toContain('unknown.placeholder')
        expect(validationError.value).toContain('Unbekannte Platzhalter')
        expect(canSubmit.value).toBe(false)
      })

      it('allows event placeholders without action (they exist globally)', async () => {
        content.value = 'Event: {{ event.name }}'

        const { validationError, canSubmit } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })

        await nextTick()
        // Without action selected, all known placeholders are allowed
        expect(validationError.value).toBe('')
        expect(canSubmit.value).toBe(true)
      })
    })

    describe('Validation with events action', () => {
      beforeEach(() => {
        actions.value = [{ value: 'action-123', slug: 'events_notification' }]
        selectedActionId.value = 'action-123'
      })

      it('allows always placeholders', async () => {
        content.value = 'Hello {{ user.name }}'

        const { validationError, canSubmit } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })

        await nextTick()
        expect(validationError.value).toBe('')
        expect(canSubmit.value).toBe(true)
      })

      it('allows event-specific placeholders', async () => {
        content.value = 'Event: {{ event.name }}, Status: {{ subtask.status }}'

        const { validationError, canSubmit } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })

        await nextTick()
        expect(validationError.value).toBe('')
        expect(canSubmit.value).toBe(true)
      })

      it('rejects VM placeholders in events context', async () => {
        content.value = 'VM: {{ virtualmachine.name }}'

        const { validationError, canSubmit, invalidPlaceholders } =
          useMailTemplatePlaceholders({
            content,
            actions,
            selectedActionId,
          })

        await nextTick()
        expect(invalidPlaceholders.value).toContain('virtualmachine.name')
        expect(validationError.value).toContain('Nicht verfügbar')
        expect(canSubmit.value).toBe(false)
      })
    })

    describe('Validation with VM action', () => {
      beforeEach(() => {
        actions.value = [{ value: 'action-456', slug: 'vm_created' }]
        selectedActionId.value = 'action-456'
      })

      it('allows always placeholders', async () => {
        content.value = 'Hello {{ user.name }}'

        const { validationError, canSubmit } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })

        await nextTick()
        expect(validationError.value).toBe('')
        expect(canSubmit.value).toBe(true)
      })

      it('allows VM-specific placeholders', async () => {
        content.value =
          'VM: {{ virtualmachine.name }}, IP: {{ virtualmachine.ipv4 }}'

        const { validationError, canSubmit } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })

        await nextTick()
        expect(validationError.value).toBe('')
        expect(canSubmit.value).toBe(true)
      })

      it('rejects event placeholders in VM context', async () => {
        content.value = 'Event: {{ event.name }}'

        const { validationError, canSubmit, invalidPlaceholders } =
          useMailTemplatePlaceholders({
            content,
            actions,
            selectedActionId,
          })

        await nextTick()
        expect(invalidPlaceholders.value).toContain('event.name')
        expect(validationError.value).toContain('Nicht verfügbar')
        expect(canSubmit.value).toBe(false)
      })
    })

    describe('Malformed placeholder validation', () => {
      it('detects placeholders starting with numbers', async () => {
        content.value = 'Test {{ 3232 }}'

        const { validationError, canSubmit, invalidPlaceholders } =
          useMailTemplatePlaceholders({
            content,
            actions,
            selectedActionId,
          })

        await nextTick()
        expect(invalidPlaceholders.value).toContain('3232')
        expect(validationError.value).toContain('Ungültiges Platzhalter-Format')
        expect(canSubmit.value).toBe(false)
      })

      it('detects placeholders with number.number format', async () => {
        content.value = 'Test {{ 32.32 }}'

        const { validationError, canSubmit } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })

        await nextTick()
        expect(validationError.value).toContain('Ungültiges Platzhalter-Format')
        expect(canSubmit.value).toBe(false)
      })

      it('detects placeholders with special characters', async () => {
        content.value = 'Test {{ /("$/($)")  }}'

        const { validationError, canSubmit } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })

        await nextTick()
        expect(validationError.value).toContain('Ungültiges Platzhalter-Format')
        expect(canSubmit.value).toBe(false)
      })

      it('detects multiple malformed placeholders', async () => {
        content.value = '{{ 3232 }} and {{ 32.32 }} and {{ /$%^ }}'

        const { validationError, invalidPlaceholders } =
          useMailTemplatePlaceholders({
            content,
            actions,
            selectedActionId,
          })

        await nextTick()
        expect(invalidPlaceholders.value.length).toBe(3)
        expect(validationError.value).toContain('Ungültiges Platzhalter-Format')
      })

      it('reports both malformed and unknown placeholders', async () => {
        content.value = '{{ 3232 }} and {{ unknown.var }}'

        const { validationError, invalidPlaceholders } =
          useMailTemplatePlaceholders({
            content,
            actions,
            selectedActionId,
          })

        await nextTick()
        expect(invalidPlaceholders.value).toContain('3232')
        expect(invalidPlaceholders.value).toContain('unknown.var')
        expect(validationError.value).toContain('Ungültiges Platzhalter-Format')
        expect(validationError.value).toContain('Unbekannte Platzhalter')
      })

      it('allows valid placeholders alongside detecting malformed ones', async () => {
        content.value = '{{ user.name }} {{ 3232 }}'

        const { validationError, invalidPlaceholders } =
          useMailTemplatePlaceholders({
            content,
            actions,
            selectedActionId,
          })

        await nextTick()
        expect(invalidPlaceholders.value).toContain('3232')
        expect(invalidPlaceholders.value).not.toContain('user.name')
        expect(validationError.value).toContain('Ungültiges Platzhalter-Format')
      })
    })

    describe('Mixed validation errors', () => {
      beforeEach(() => {
        actions.value = [{ value: 'action-123', slug: 'events_notification' }]
        selectedActionId.value = 'action-123'
      })

      it('reports both wrong context and unknown placeholders', async () => {
        content.value = '{{ virtualmachine.name }} and {{ totally.unknown }}'

        const { validationError, invalidPlaceholders } =
          useMailTemplatePlaceholders({
            content,
            actions,
            selectedActionId,
          })

        await nextTick()
        expect(invalidPlaceholders.value).toContain('virtualmachine.name')
        expect(invalidPlaceholders.value).toContain('totally.unknown')
        expect(validationError.value).toContain('Nicht verfügbar')
        expect(validationError.value).toContain('Unbekannte Platzhalter')
      })
    })

    describe('Reactivity', () => {
      it('updates validation when content changes', async () => {
        const { validationError, canSubmit } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })

        content.value = '{{ unknown.var }}'
        await nextTick()
        expect(canSubmit.value).toBe(false)

        content.value = '{{ user.name }}'
        await nextTick()
        expect(canSubmit.value).toBe(true)
        expect(validationError.value).toBe('')
      })

      it('updates validation when action changes', async () => {
        actions.value = [
          { value: 'action-123', slug: 'events_notification' },
          { value: 'action-456', slug: 'vm_created' },
        ]
        content.value = '{{ virtualmachine.name }}'

        const { validationError, canSubmit } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })

        // No action selected - VM placeholder is valid (exists globally)
        await nextTick()
        expect(canSubmit.value).toBe(true)

        // Select events action - VM placeholder is invalid
        selectedActionId.value = 'action-123'
        await nextTick()
        expect(canSubmit.value).toBe(false)

        // Select VM action - VM placeholder is valid
        selectedActionId.value = 'action-456'
        await nextTick()
        expect(canSubmit.value).toBe(true)
        expect(validationError.value).toBe('')
      })
    })

    describe('availablePlaceholders', () => {
      it('returns always placeholders when no context', () => {
        const { availablePlaceholders } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })

        expect(availablePlaceholders.value).toEqual(
          PLACEHOLDER_DEFINITIONS.always,
        )
      })

      it('returns events placeholders for events context', async () => {
        actions.value = [{ value: 'action-123', slug: 'events_notification' }]
        selectedActionId.value = 'action-123'

        const { availablePlaceholders } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })

        await nextTick()
        PLACEHOLDER_DEFINITIONS.always.forEach((p) => {
          expect(availablePlaceholders.value).toContain(p)
        })
        PLACEHOLDER_DEFINITIONS.events.forEach((p) => {
          expect(availablePlaceholders.value).toContain(p)
        })
      })
    })

    describe('groupedPlaceholders', () => {
      it('returns grouped placeholders for documentation', () => {
        const { groupedPlaceholders } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })

        const groups = groupedPlaceholders.value
        expect(groups.find((g) => g.name === 'Benutzer')).toBeDefined()
        expect(groups.find((g) => g.name === 'Projekt')).toBeDefined()
      })

      it('includes event groups when no context or events context', async () => {
        const { groupedPlaceholders } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })

        await nextTick()
        const groups = groupedPlaceholders.value
        expect(groups.find((g) => g.name === 'Veranstaltung')).toBeDefined()
        expect(groups.find((g) => g.name === 'SubTask')).toBeDefined()
      })

      it('includes VM group when no context or VM context', async () => {
        const { groupedPlaceholders } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })

        await nextTick()
        const groups = groupedPlaceholders.value
        expect(
          groups.find((g) => g.name === 'Virtuelle Maschine'),
        ).toBeDefined()
      })
    })

    describe('validatePlaceholders method', () => {
      it('returns true for valid content', async () => {
        content.value = '{{ user.name }}'

        const { validatePlaceholders } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })

        await nextTick()
        expect(validatePlaceholders()).toBe(true)
      })

      it('returns false for invalid content', async () => {
        content.value = '{{ invalid.placeholder }}'

        const { validatePlaceholders } = useMailTemplatePlaceholders({
          content,
          actions,
          selectedActionId,
        })

        await nextTick()
        expect(validatePlaceholders()).toBe(false)
      })
    })
  })

  describe('PLACEHOLDER_DEFINITIONS', () => {
    it('has always array with user and project placeholders', () => {
      expect(PLACEHOLDER_DEFINITIONS.always).toContain('user.name')
      expect(PLACEHOLDER_DEFINITIONS.always).toContain('user.email')
      expect(PLACEHOLDER_DEFINITIONS.always).toContain('project.name')
    })

    it('has events array with event and subtask placeholders', () => {
      expect(PLACEHOLDER_DEFINITIONS.events).toContain('event.name')
      expect(PLACEHOLDER_DEFINITIONS.events).toContain('event.dateStart')
      expect(PLACEHOLDER_DEFINITIONS.events).toContain('subtask.status')
    })

    it('has virtualmachines array with VM placeholders', () => {
      expect(PLACEHOLDER_DEFINITIONS.virtualmachines).toContain(
        'virtualmachine.name',
      )
      expect(PLACEHOLDER_DEFINITIONS.virtualmachines).toContain(
        'virtualmachine.ipv4',
      )
      expect(PLACEHOLDER_DEFINITIONS.virtualmachines).toContain(
        'virtualmachine.status',
      )
    })
  })
})
