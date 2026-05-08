import { computed, ref, watchEffect } from 'vue'

/**
 * Valid placeholder definitions grouped by context availability.
 * 'always' placeholders are available in all contexts.
 */
const PLACEHOLDER_DEFINITIONS = {
  // Always available (events & VMs)
  always: [
    'user.email',
    'user.name',
    'user.username',
    'project.name',
    'project.title',
  ],

  // Only available for events context
  events: [
    'subtask.action',
    'subtask.attempt',
    'subtask.createdAt',
    'subtask.createdById',
    'subtask.id',
    'subtask.job_id',
    'subtask.name',
    'subtask.object_id',
    'subtask.object_type',
    'subtask.parent_task',
    'subtask.response_code',
    'subtask.response_message',
    'subtask.status',
    'subtask.updatedAt',
    'subtask.updatedById',
    'event.course',
    'event.createdAt',
    'event.createdById',
    'event.dateEnd',
    'event.dateStart',
    'event.deployment_status',
    'event.description',
    'event.guacamole',
    'event.id',
    'event.name',
    'event.slug',
    'event.status',
    'event.timeStart',
    'event.timeEnd',
    'event.updatedAt',
    'event.updatedById',
  ],

  // Only available for VMs context
  virtualmachines: [
    'virtualmachine.cpu',
    'virtualmachine.createdAt',
    'virtualmachine.createdById',
    'virtualmachine.description',
    'virtualmachine.disk',
    'virtualmachine.event',
    'virtualmachine.id',
    'virtualmachine.ipv4',
    'virtualmachine.name',
    'virtualmachine.os',
    'virtualmachine.prevent_delete',
    'virtualmachine.proxmoxId',
    'virtualmachine.proxmoxNode',
    'virtualmachine.ram',
    'virtualmachine.status',
    'virtualmachine.template',
    'virtualmachine.updatedAt',
    'virtualmachine.updatedById',
  ],
}

/**
 * Regex pattern for valid placeholder names.
 * Must start with letter or underscore, followed by letters, numbers, underscores, or dots.
 */
const VALID_PLACEHOLDER_PATTERN = /^[a-zA-Z_][a-zA-Z0-9_.]*$/

/**
 * Checks if a placeholder name has valid format.
 *
 * @param {string} name - The placeholder name to check
 * @returns {boolean} True if the format is valid
 */
function isValidPlaceholderFormat(name) {
  return VALID_PLACEHOLDER_PATTERN.test(name)
}

/**
 * Extracts all raw placeholder-like patterns from content.
 * Matches anything between {{ and }}.
 *
 * @param {string} content - The template content to parse
 * @returns {string[]} Array of raw content between braces (trimmed)
 */
function extractRawPlaceholders(content) {
  if (!content) return []

  const regex = /\{\{\s*([^}]*?)\s*\}\}/g
  const placeholders = []
  let match

  while ((match = regex.exec(content)) !== null) {
    const trimmed = match[1].trim()
    if (trimmed) {
      placeholders.push(trimmed)
    }
  }

  return [...new Set(placeholders)]
}

/**
 * Extracts all valid placeholders from a template string.
 * Matches patterns like {{ placeholder }} with optional whitespace.
 * Only returns placeholders with valid format (letter/underscore start, alphanumeric/dots).
 *
 * @param {string} content - The template content to parse
 * @returns {string[]} Array of placeholder names (without braces)
 */
function extractPlaceholders(content) {
  if (!content) return []

  const regex = /\{\{\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\}\}/g
  const placeholders = []
  let match

  while ((match = regex.exec(content)) !== null) {
    placeholders.push(match[1])
  }

  return [...new Set(placeholders)] // Remove duplicates
}

/**
 * Gets all possible placeholders (for checking if a placeholder exists at all).
 *
 * @returns {string[]} Array of all valid placeholder names across all contexts
 */
function getAllPlaceholders() {
  return [
    ...PLACEHOLDER_DEFINITIONS.always,
    ...PLACEHOLDER_DEFINITIONS.events,
    ...PLACEHOLDER_DEFINITIONS.virtualmachines,
  ]
}

/**
 * Gets the valid placeholders for a given context.
 *
 * @param {string|null} context - The context ('events', 'virtualmachines', or null)
 * @returns {string[]} Array of valid placeholder names
 */
function getValidPlaceholders(context) {
  const valid = [...PLACEHOLDER_DEFINITIONS.always]

  if (context === 'events') {
    valid.push(...PLACEHOLDER_DEFINITIONS.events)
  } else if (context === 'virtualmachines') {
    valid.push(...PLACEHOLDER_DEFINITIONS.virtualmachines)
  }

  return valid
}

/**
 * Composable for validating mail template placeholders.
 *
 * @param {Object} options - Configuration options
 * @param {import('vue').Ref<string>} options.content - Reactive ref to template content
 * @param {import('vue').Ref<Array>} options.actions - Reactive ref to available mail actions
 * @param {import('vue').Ref<string>} options.selectedActionId - Reactive ref to selected mail action ID
 * @returns {Object} Validation state and helpers
 */
export function useMailTemplatePlaceholders({
  content,
  actions,
  selectedActionId,
}) {
  const invalidPlaceholders = ref([])
  const validationError = ref('')

  // Get the context from the selected mail action based on slug prefix
  // - slug starting with "events_" → events context
  // - slug starting with "vm_" → virtualmachines context
  const selectedActionContext = computed(() => {
    if (!selectedActionId.value || !actions.value?.length) return null

    const action = actions.value.find((a) => a.value === selectedActionId.value)
    if (!action?.slug) return null

    if (action.slug.startsWith('events_')) return 'events'
    if (action.slug.startsWith('vm_')) return 'virtualmachines'

    return null
  })

  // Get valid placeholders for the current context
  const availablePlaceholders = computed(() => {
    return getValidPlaceholders(selectedActionContext.value)
  })

  // Validate placeholders - called reactively via watchEffect
  const validatePlaceholders = () => {
    // Access reactive values to ensure watchEffect tracks them
    const contentValue = content.value
    const actionId = selectedActionId.value
    // Access actions.value to track changes (used implicitly via selectedActionContext)
    void actions.value

    // Extract all placeholder-like patterns and valid placeholders
    const rawPlaceholders = extractRawPlaceholders(contentValue)
    const usedPlaceholders = extractPlaceholders(contentValue)

    // Check for malformed placeholders (invalid format)
    const malformed = rawPlaceholders.filter(
      (p) => !isValidPlaceholderFormat(p),
    )

    const messages = []

    if (malformed.length > 0) {
      messages.push(
        `Ungültiges Platzhalter-Format: ${malformed.map((p) => `{{ ${p} }}`).join(', ')}`,
      )
    }

    // If no action is selected, check if placeholders exist at all
    if (!actionId) {
      const allValid = getAllPlaceholders()
      const unknown = usedPlaceholders.filter((p) => !allValid.includes(p))
      invalidPlaceholders.value = [...malformed, ...unknown]

      if (unknown.length > 0) {
        messages.push(
          `Unbekannte Platzhalter: ${unknown.map((p) => `{{ ${p} }}`).join(', ')}`,
        )
      }

      if (messages.length > 0) {
        validationError.value = messages.join(' | ')
        return false
      }

      validationError.value = ''
      return true
    }

    // Action is selected - validate against context-specific placeholders
    const valid = availablePlaceholders.value
    const invalid = usedPlaceholders.filter((p) => !valid.includes(p))
    invalidPlaceholders.value = [...malformed, ...invalid]

    if (invalid.length > 0) {
      // Check if invalid placeholders exist in other contexts
      const allValid = getAllPlaceholders()
      const unknown = invalid.filter((p) => !allValid.includes(p))
      const wrongContext = invalid.filter((p) => allValid.includes(p))

      const contextName =
        selectedActionContext.value === 'events'
          ? 'Veranstaltungen'
          : selectedActionContext.value === 'virtualmachines'
            ? 'Virtuelle Maschinen'
            : 'die zugewiesene E-Mail Aktion'

      if (wrongContext.length > 0) {
        messages.push(
          `Nicht verfügbar für ${contextName}: ${wrongContext.map((p) => `{{ ${p} }}`).join(', ')}`,
        )
      }
      if (unknown.length > 0) {
        messages.push(
          `Unbekannte Platzhalter: ${unknown.map((p) => `{{ ${p} }}`).join(', ')}`,
        )
      }
    }

    if (messages.length > 0) {
      validationError.value = messages.join(' | ')
      return false
    }

    validationError.value = ''
    return true
  }

  // Use watchEffect for automatic dependency tracking - validates live as user types
  watchEffect(() => {
    validatePlaceholders()
  })

  // Check if form can be submitted
  const canSubmit = computed(() => {
    return invalidPlaceholders.value.length === 0
  })

  // Get grouped placeholders for documentation/help
  const groupedPlaceholders = computed(() => {
    const groups = [
      {
        name: 'Benutzer',
        placeholders: PLACEHOLDER_DEFINITIONS.always.filter((p) =>
          p.startsWith('user.'),
        ),
        available: true,
      },
      {
        name: 'Projekt',
        placeholders: PLACEHOLDER_DEFINITIONS.always.filter((p) =>
          p.startsWith('project.'),
        ),
        available: true,
      },
    ]

    if (
      !selectedActionContext.value ||
      selectedActionContext.value === 'events'
    ) {
      groups.push({
        name: 'SubTask',
        placeholders: PLACEHOLDER_DEFINITIONS.events.filter((p) =>
          p.startsWith('subtask.'),
        ),
        available: selectedActionContext.value === 'events',
      })
      groups.push({
        name: 'Veranstaltung',
        placeholders: PLACEHOLDER_DEFINITIONS.events.filter((p) =>
          p.startsWith('event.'),
        ),
        available: selectedActionContext.value === 'events',
      })
    }

    if (
      !selectedActionContext.value ||
      selectedActionContext.value === 'virtualmachines'
    ) {
      groups.push({
        name: 'Virtuelle Maschine',
        placeholders: PLACEHOLDER_DEFINITIONS.virtualmachines,
        available: selectedActionContext.value === 'virtualmachines',
      })
    }

    return groups
  })

  return {
    invalidPlaceholders,
    validationError,
    availablePlaceholders,
    selectedActionContext,
    canSubmit,
    groupedPlaceholders,
    validatePlaceholders,
  }
}

export {
  extractPlaceholders,
  extractRawPlaceholders,
  getAllPlaceholders,
  getValidPlaceholders,
  isValidPlaceholderFormat,
  PLACEHOLDER_DEFINITIONS,
}
