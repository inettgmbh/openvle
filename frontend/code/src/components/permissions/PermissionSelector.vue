<script setup>
import { mdiCloseCircleOutline, mdiShieldCrownOutline } from '@mdi/js'
import { computed } from 'vue'

import { permissionKeyIcon } from '@/utils/icons'
import {
  getObjectPermissionLabel,
  getObjectPermissionShortLabel,
} from '@/utils/objectModelPermissions'

const props = defineProps({
  modelValue: { type: String, required: true }, // none | object_read | object_update | object_delete | object_full | ...
  createValue: { type: Boolean, default: false }, // legacy split for object_create in global scope
  disabled: { type: Boolean, default: false },
  mode: { type: String, default: 'global' }, // 'global' | 'object'
  // Backend object model (e.g. 'VirtualMachine', 'Event'). Disambiguates
  // permission keys that are shared between models so labels, icons and
  // tooltips resolve to the correct entry.
  model: { type: String, default: null },
  allowedKeys: { type: Array, default: null },
  extraValues: { type: Array, default: () => [] },
  defaultCollapsedCategories: {
    type: Array,
    default: () => ['actions'],
  },
})

const emit = defineEmits([
  'update:modelValue',
  'update:createValue',
  'update:extraValues',
])

const CHAIN_KEYS = ['object_read', 'object_update', 'object_delete']

// object_reset (Steuerung) implicitly includes these permissions
const STEUERUNG_KEY = 'object_reset'
const STEUERUNG_CONTAINS = [
  'object_actions_start',
  'object_actions_stop',
  'object_actions_reboot',
  'object_actions_reset',
  'object_actions_shutdown',
  'object_actions_resume',
]

// object_reset (Steuerung) also implies these chain permissions
const STEUERUNG_IMPLIES_CHAIN = ['object_read']

// Custom sort order for VM action permissions (lower index = higher priority)
const ACTION_SORT_ORDER = [
  'object_reset', // Steuerung first
  'object_actions_start',
  'object_actions_shutdown',
  'object_actions_stop',
  'object_actions_reboot',
  'object_actions_reset',
  // Rest will be sorted alphabetically
]

// Mutually exclusive permission groups (selecting one deselects others in the group)
const MUTUALLY_EXCLUSIVE_GROUPS = [
  ['object_admins', 'object_verwaltende'], // Dashboard permissions
]

// Chain-Extra exclusions: selecting a chain key deselects the extra and vice versa
// Format: { chainKey: extraKey } - these are mutually exclusive across chain/extras
const CHAIN_EXTRA_EXCLUSIONS = {
  // dummy: 'object_dummy', //
}

function getMutuallyExclusiveGroup(key) {
  return MUTUALLY_EXCLUSIVE_GROUPS.find((group) => group.includes(key)) ?? null
}

function getChainExcludedExtra(chainKey) {
  return CHAIN_EXTRA_EXCLUSIONS[chainKey] ?? null
}

function getExtraExcludedChain(extraKey) {
  for (const [chain, extra] of Object.entries(CHAIN_EXTRA_EXCLUSIONS)) {
    if (extra === extraKey) return chain
  }
  return null
}

function expandToActive(level) {
  if (level === 'none') return new Set()
  // object_full implies all chain keys
  if (level === 'object_full') return new Set(CHAIN_KEYS)
  const idx = CHAIN_KEYS.indexOf(level)
  if (idx < 0) return new Set()
  const s = new Set()
  for (let i = 0; i <= idx; i++) s.add(CHAIN_KEYS[i])
  return s
}

function collapseFromActive(activeSet) {
  if (activeSet.size === 0) return 'none'
  // Return the highest chain key
  let best = null
  for (const k of CHAIN_KEYS) {
    if (activeSet.has(k)) best = k
  }
  return best ?? 'none'
}

const allowedSet = computed(() => {
  if (!props.allowedKeys) return null
  return new Set(props.allowedKeys.map((k) => String(k)))
})

const canShowCreate = computed(() => {
  if (props.mode === 'object') return false
  if (!allowedSet.value) return true
  return allowedSet.value.has('object_create')
})

const chainAllowed = computed(() => {
  if (!allowedSet.value) return new Set(CHAIN_KEYS)
  return new Set(CHAIN_KEYS.filter((k) => allowedSet.value.has(k)))
})

const extrasAllowed = computed(() => {
  if (!allowedSet.value) return []
  const excluded = new Set(['object_create', 'object_full', ...CHAIN_KEYS])
  return [...allowedSet.value].filter((k) => !excluded.has(k))
})

const activeChain = computed(() => expandToActive(props.modelValue))
const extraSet = computed(
  () => new Set((props.extraValues ?? []).map((k) => String(k))),
)

// Check if object_full is active
const isFullActive = computed(() => props.modelValue === 'object_full')

// Check if Steuerung (object_reset) is active
const isSteuerungActive = computed(() => extraSet.value.has(STEUERUNG_KEY))

// Extras that are implicitly active because object_full or Steuerung is selected
const implicitExtras = computed(() => {
  const set = new Set()
  // object_full implies all extras
  if (isFullActive.value) {
    for (const extra of extrasAllowed.value) {
      set.add(extra)
    }
  }
  // Steuerung implies its contained actions
  if (isSteuerungActive.value) {
    for (const contained of STEUERUNG_CONTAINS) {
      set.add(contained)
    }
  }
  return set
})

// Chain permissions that are implicitly active because object_full or Steuerung is selected
const implicitChain = computed(() => {
  const set = new Set()
  // object_full implies all chain keys
  if (isFullActive.value) {
    for (const k of CHAIN_KEYS) {
      set.add(k)
    }
  }
  // Steuerung implies object_read
  if (isSteuerungActive.value) {
    for (const k of STEUERUNG_IMPLIES_CHAIN) {
      set.add(k)
    }
  }
  return set
})

// Create is implicitly active because object_full is selected (global mode only)
const isCreateImplicit = computed(() => {
  if (props.mode === 'object') return false
  return isFullActive.value
})

const noneActive = computed(() => {
  const noExtras = extraSet.value.size === 0
  const noCreate = props.mode === 'object' ? true : !props.createValue
  return props.modelValue === 'none' && noCreate && noExtras
})

// Check if object_full is allowed
const canShowFull = computed(() => {
  if (!allowedSet.value) return true
  return allowedSet.value.has('object_full')
})

/**
 * Checks if all available permissions would be selected with the given state.
 * If so, we should upgrade to object_full automatically.
 */
function shouldUpgradeToFull(nextChainLevel, nextCreateValue, nextExtras) {
  // object_full must be allowed
  if (!canShowFull.value) return false

  // Count total available permissions to ensure upgrade is meaningful
  // Don't upgrade if there's only a single permission (e.g., only object_read)
  const totalAvailable =
    chainAllowed.value.size +
    (props.mode !== 'object' && canShowCreate.value ? 1 : 0) +
    extrasAllowed.value.length

  if (totalAvailable <= 1) return false

  // Check chain: all allowed chain keys must be active
  const nextChainSet = expandToActive(nextChainLevel)
  for (const k of chainAllowed.value) {
    if (!nextChainSet.has(k)) return false
  }

  // Check create: in global mode, create must be active (if allowed)
  if (props.mode !== 'object' && canShowCreate.value) {
    if (!nextCreateValue) return false
  }

  // Check extras: all allowed extras must be active
  const nextExtrasSet = new Set(nextExtras.map((k) => String(k)))
  for (const k of extrasAllowed.value) {
    if (!nextExtrasSet.has(k)) return false
  }

  return true
}

function setNone() {
  if (props.disabled) return
  emit('update:modelValue', 'none')
  if (props.mode !== 'object') emit('update:createValue', false)
  emit('update:extraValues', [])
}

function toggleFull() {
  if (props.disabled) return

  if (isFullActive.value) {
    // Deactivate object_full: reset everything to none
    emit('update:modelValue', 'none')
    if (props.mode !== 'object') emit('update:createValue', false)
    emit('update:extraValues', [])
  } else {
    // Activate object_full: set level, clear explicit extras (they become implicit)
    // Note: Don't change createValue - object_full implies create, so we don't need
    // to explicitly set it. Keeping it as-is avoids issues with the save logic.
    emit('update:modelValue', 'object_full')
    emit('update:extraValues', [])
  }
}

function toggleCreate() {
  if (props.disabled) return
  if (props.mode === 'object') return

  // If object_full is active, clicking create deactivates object_full
  // and activates ONLY create (consistent with Steuerung pattern)
  if (isFullActive.value) {
    emit('update:modelValue', 'none')
    emit('update:createValue', true)
    emit('update:extraValues', [])
    return
  }

  const nextCreateValue = !props.createValue

  // Check if this would complete all permissions -> upgrade to object_full
  if (
    nextCreateValue &&
    shouldUpgradeToFull(props.modelValue, nextCreateValue, props.extraValues)
  ) {
    emit('update:modelValue', 'object_full')
    emit('update:createValue', false)
    emit('update:extraValues', [])
    return
  }

  emit('update:createValue', nextCreateValue)
}

function toggleChain(key) {
  if (props.disabled) return
  if (!chainAllowed.value.has(key)) return

  const clickedIdx = CHAIN_KEYS.indexOf(key)
  if (clickedIdx === -1) return

  // If object_full is active, clicking a chain key deactivates object_full
  // and activates ONLY up to the clicked key (consistent with Steuerung pattern)
  if (isFullActive.value) {
    const nextActive = new Set()
    for (let i = 0; i <= clickedIdx; i++) nextActive.add(CHAIN_KEYS[i])
    emit('update:modelValue', collapseFromActive(nextActive))
    // Clear create and extras (user explicitly chose only chain permissions)
    if (props.mode !== 'object') emit('update:createValue', false)
    emit('update:extraValues', [])
    return
  }

  const nextActive = new Set(activeChain.value)

  const hasHigher = CHAIN_KEYS.slice(clickedIdx + 1).some((k) =>
    nextActive.has(k),
  )

  let nextExtras = null

  // Check if this chain key is implied by Steuerung and Steuerung is active
  const isImpliedBySteuerung = STEUERUNG_IMPLIES_CHAIN.includes(key)
  if (isImpliedBySteuerung && isSteuerungActive.value) {
    // Clicking an implied chain key while Steuerung is active:
    // Deselect Steuerung and activate this chain key explicitly
    nextExtras = [...extraSet.value].filter((k) => k !== STEUERUNG_KEY)
    for (let i = 0; i <= clickedIdx; i++) nextActive.add(CHAIN_KEYS[i])
  } else if (nextActive.has(key)) {
    const start = hasHigher ? clickedIdx + 1 : clickedIdx
    for (let i = start; i < CHAIN_KEYS.length; i++)
      nextActive.delete(CHAIN_KEYS[i])
  } else {
    for (let i = 0; i <= clickedIdx; i++) nextActive.add(CHAIN_KEYS[i])

    // Check for chain-extra exclusion: remove excluded extra when chain is activated
    const excludedExtra = getChainExcludedExtra(key)
    if (excludedExtra && extraSet.value.has(excludedExtra)) {
      nextExtras = [...extraSet.value].filter((k) => k !== excludedExtra)
    }
  }

  const nextChainLevel = collapseFromActive(nextActive)
  const finalExtras = nextExtras ?? props.extraValues

  // Check if this would complete all permissions -> upgrade to object_full
  if (shouldUpgradeToFull(nextChainLevel, props.createValue, finalExtras)) {
    emit('update:modelValue', 'object_full')
    if (props.mode !== 'object') emit('update:createValue', false)
    emit('update:extraValues', [])
    return
  }

  emit('update:modelValue', nextChainLevel)
  if (nextExtras !== null) {
    emit('update:extraValues', nextExtras)
  }
}

function toggleExtra(key) {
  if (props.disabled) return
  if (allowedSet.value && !allowedSet.value.has(key)) return

  // If object_full is active, clicking an extra deactivates object_full
  // and activates only this extra
  if (isFullActive.value) {
    emit('update:modelValue', 'none')
    if (props.mode !== 'object') emit('update:createValue', false)
    emit('update:extraValues', [key])
    return
  }

  const next = new Set(extraSet.value)
  const isContainedInSteuerung = STEUERUNG_CONTAINS.includes(key)
  let newChainLevel = null

  if (key === STEUERUNG_KEY) {
    // Toggling Steuerung
    if (next.has(key)) {
      // Deselecting Steuerung: remove it and all contained actions
      next.delete(key)
      for (const contained of STEUERUNG_CONTAINS) {
        next.delete(contained)
      }
    } else {
      // Selecting Steuerung: add it, remove individual contained actions
      // (they are now implicit)
      next.add(key)
      for (const contained of STEUERUNG_CONTAINS) {
        next.delete(contained)
      }

      // Also remove implied chain permissions (they are now implicit via Steuerung)
      // Only remove if the chain level is exactly that key (not higher)
      for (const impliedChainKey of STEUERUNG_IMPLIES_CHAIN) {
        if (props.modelValue === impliedChainKey) {
          newChainLevel = 'none'
        }
      }
    }
  } else if (isContainedInSteuerung) {
    // Toggling an action that is contained in Steuerung
    if (isSteuerungActive.value) {
      // Steuerung is active: selecting individual action removes Steuerung
      // and adds only this action
      next.delete(STEUERUNG_KEY)
      next.add(key)
    } else if (next.has(key)) {
      // Action is explicitly selected: deselect it
      next.delete(key)
    } else {
      // Action is not selected: select it
      next.add(key)
    }
  } else {
    // Check for chain-extra exclusion
    const excludedChainKey = getExtraExcludedChain(key)

    if (excludedChainKey) {
      // This extra has a chain-extra exclusion relationship
      if (next.has(key)) {
        // Deselecting the extra
        next.delete(key)
      } else {
        // Selecting an extra that excludes a chain key
        next.add(key)

        // Remove the excluded chain key (and all higher keys in the chain)
        if (activeChain.value.has(excludedChainKey)) {
          const excludedIdx = CHAIN_KEYS.indexOf(excludedChainKey)
          const nextActive = new Set(activeChain.value)

          // Remove this key and all keys from this point
          for (let i = excludedIdx; i < CHAIN_KEYS.length; i++) {
            nextActive.delete(CHAIN_KEYS[i])
          }

          newChainLevel = collapseFromActive(nextActive)
        }
      }
    } else {
      // Check for mutually exclusive group
      const exclusiveGroup = getMutuallyExclusiveGroup(key)

      if (exclusiveGroup) {
        // Mutually exclusive: selecting one deselects others in the group
        if (next.has(key)) {
          next.delete(key)
        } else {
          // Remove all others in the group first
          for (const other of exclusiveGroup) {
            next.delete(other)
          }
          next.add(key)
        }
      } else {
        // Normal extra toggle
        if (next.has(key)) next.delete(key)
        else next.add(key)
      }
    }
  }

  const nextExtras = [...next]
  const nextChainLevel = newChainLevel ?? props.modelValue

  // Check if this would complete all permissions -> upgrade to object_full
  if (shouldUpgradeToFull(nextChainLevel, props.createValue, nextExtras)) {
    emit('update:modelValue', 'object_full')
    if (props.mode !== 'object') emit('update:createValue', false)
    emit('update:extraValues', [])
    return
  }

  emit('update:extraValues', nextExtras)
  if (newChainLevel !== null) {
    emit('update:modelValue', newChainLevel)
  }
}

function isChainActive(key) {
  // If object_full is active, chain keys are shown as implicit, not active
  if (isFullActive.value) return false
  return activeChain.value.has(key)
}

function isChainImplicit(key) {
  return implicitChain.value.has(key)
}

function isChainActiveOrImplicit(key) {
  return isChainActive(key) || implicitChain.value.has(key)
}

function isExtraActive(key) {
  // If object_full is active, extras are shown as implicit, not active
  if (isFullActive.value) return false
  return extraSet.value.has(key)
}

function isExtraImplicit(key) {
  return implicitExtras.value.has(key)
}

function isExtraActiveOrImplicit(key) {
  return isExtraActive(key) || isExtraImplicit(key)
}

function isCreateActive() {
  if (isFullActive.value) return false
  return props.createValue
}

function isCreateActiveOrImplicit() {
  return isCreateActive() || isCreateImplicit.value
}

function describePermission(key) {
  // Model-aware description lookup: shared keys (e.g. `object_actions_stop`
  // exists on both VM and Event) resolve to the correct copy via `props.model`.
  return getObjectPermissionLabel({
    permission: key,
    model: props.model,
    selector: (p) => p.description,
  })
}

const chainButtons = computed(() => {
  return CHAIN_KEYS.filter((k) => chainAllowed.value.has(k)).map((k) => ({
    key: k,
    label: getObjectPermissionShortLabel({ permission: k, model: props.model }),
    icon: permissionKeyIcon(k, props.model) ?? null,
  }))
})

const createButton = computed(() => {
  if (props.mode === 'object') return null
  if (!canShowCreate.value) return null

  return {
    key: 'object_create',
    label: getObjectPermissionShortLabel({
      permission: 'object_create',
      model: props.model,
    }),
    icon: permissionKeyIcon('object_create', props.model) ?? null,
  }
})

const fullButton = computed(() => {
  if (!canShowFull.value) return null

  return {
    key: 'object_full',
    label: getObjectPermissionShortLabel({
      permission: 'object_full',
      model: props.model,
    }),
    icon: mdiShieldCrownOutline,
  }
})

const specialPermissions = computed(() => {
  const keys = extrasAllowed.value.slice().sort((a, b) => {
    const indexA = ACTION_SORT_ORDER.indexOf(a)
    const indexB = ACTION_SORT_ORDER.indexOf(b)

    // Both have custom order: sort by index
    if (indexA !== -1 && indexB !== -1) return indexA - indexB

    // Only a has custom order: a comes first
    if (indexA !== -1) return -1

    // Only b has custom order: b comes first
    if (indexB !== -1) return 1

    // Neither has custom order: sort alphabetically by label
    return getObjectPermissionShortLabel({
      permission: a,
      model: props.model,
    }).localeCompare(
      getObjectPermissionShortLabel({ permission: b, model: props.model }),
      'de',
    )
  })

  const groups = []

  for (const k of keys) {
    groups.push({
      key: k,
      label: getObjectPermissionShortLabel({
        permission: k,
        model: props.model,
      }),
      description: describePermission(k),
      icon: permissionKeyIcon(k, props.model) ?? null,
    })
  }

  return groups
})
</script>

<template>
  <div class="inline-flex flex-col gap-2">
    <!-- Top row: None + Create + Chain + Special Permissions (if space) -->
    <div class="inline-flex flex-wrap gap-2">
      <!-- None -->
      <button
        type="button"
        :disabled="disabled"
        :aria-pressed="noneActive"
        class="px-3 py-2 rounded-lg border text-sm font-medium transition-all inline-flex items-center gap-2 shadow-sm"
        :class="[
          disabled
            ? 'opacity-50 cursor-not-allowed'
            : 'hover:shadow-md active:scale-95',
          !noneActive && [
            'bg-white text-gray-700 border-gray-300',
            'hover:bg-gray-50 hover:border-gray-400',
            'dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600',
            'dark:hover:bg-gray-750 dark:hover:border-gray-500',
          ],
          noneActive && [
            'bg-gradient-to-b from-gray-800 to-gray-900 text-white border-gray-900',
            'hover:from-gray-700 hover:to-gray-800',
            'dark:from-gray-100 dark:to-gray-200 dark:text-gray-900 dark:border-gray-300',
            'dark:hover:from-gray-50 dark:hover:to-gray-100',
          ],
        ]"
        @click="setNone"
      >
        <svg
          viewBox="0 0 24 24"
          class="w-4 h-4 fill-current"
          aria-hidden="true"
        >
          <path :d="mdiCloseCircleOutline" />
        </svg>

        <span>{{ $t('components.permissionSelector.none') }}</span>
      </button>

      <!-- Vollzugriff (object_full) -->
      <button
        v-if="fullButton"
        type="button"
        :disabled="disabled"
        :aria-pressed="isFullActive"
        class="px-3 py-2 rounded-lg border text-sm font-medium transition-all inline-flex items-center gap-2 shadow-sm"
        :class="[
          disabled
            ? 'opacity-50 cursor-not-allowed'
            : 'hover:shadow-md active:scale-95',
          !isFullActive && [
            'bg-white text-gray-700 border-gray-300',
            'hover:bg-gray-50 hover:border-gray-400',
            'dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600',
            'dark:hover:bg-gray-750 dark:hover:border-gray-500',
          ],
          isFullActive && [
            'bg-gradient-to-b from-amber-500 to-amber-600 text-white border-amber-600',
            'hover:from-amber-400 hover:to-amber-500',
            'dark:from-amber-500 dark:to-amber-600 dark:border-amber-600',
            'dark:hover:from-amber-400 dark:hover:to-amber-500',
          ],
        ]"
        @click="toggleFull"
      >
        <svg
          v-if="fullButton.icon"
          viewBox="0 0 24 24"
          class="w-4 h-4 fill-current"
          aria-hidden="true"
        >
          <path :d="fullButton.icon" />
        </svg>

        <span>{{ fullButton.label }}</span>
      </button>

      <!-- Create -->
      <button
        v-if="createButton"
        type="button"
        :disabled="disabled"
        :aria-pressed="isCreateActiveOrImplicit()"
        class="px-3 py-2 rounded-lg border text-sm font-medium transition-all inline-flex items-center gap-2 shadow-sm"
        :class="[
          disabled
            ? 'opacity-50 cursor-not-allowed'
            : 'hover:shadow-md active:scale-95',
          !isCreateActiveOrImplicit() && [
            'bg-white text-gray-700 border-gray-300',
            'hover:bg-gray-50 hover:border-gray-400',
            'dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600',
            'dark:hover:bg-gray-750 dark:hover:border-gray-500',
          ],
          isCreateImplicit && [
            'bg-gradient-to-b from-blue-400 to-blue-500 text-white border-blue-500',
            'hover:from-blue-300 hover:to-blue-400',
            'dark:from-blue-400 dark:to-blue-500 dark:border-blue-500',
            'dark:hover:from-blue-300 dark:hover:to-blue-400',
          ],
          isCreateActive() && [
            'bg-gradient-to-b from-blue-600 to-blue-700 text-white border-blue-700',
            'hover:from-blue-500 hover:to-blue-600',
            'dark:from-blue-500 dark:to-blue-600 dark:border-blue-600',
            'dark:hover:from-blue-400 dark:hover:to-blue-500',
          ],
        ]"
        @click="toggleCreate"
      >
        <svg
          v-if="createButton.icon"
          viewBox="0 0 24 24"
          class="w-4 h-4 fill-current"
          aria-hidden="true"
        >
          <path :d="createButton.icon" />
        </svg>

        <span>{{ createButton.label }}</span>
      </button>

      <!-- RWUD chain -->
      <button
        v-for="b in chainButtons"
        :key="b.key"
        type="button"
        :disabled="disabled"
        :aria-pressed="isChainActiveOrImplicit(b.key)"
        class="px-3 py-2 rounded-lg border text-sm font-medium transition-all inline-flex items-center gap-2 shadow-sm"
        :class="[
          disabled
            ? 'opacity-50 cursor-not-allowed'
            : 'hover:shadow-md active:scale-95',
          !isChainActiveOrImplicit(b.key) && [
            'bg-white text-gray-700 border-gray-300',
            'hover:bg-gray-50 hover:border-gray-400',
            'dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600',
            'dark:hover:bg-gray-750 dark:hover:border-gray-500',
          ],
          isChainImplicit(b.key) && [
            'bg-gradient-to-b from-emerald-400 to-emerald-500 text-white border-emerald-500',
            'hover:from-emerald-300 hover:to-emerald-400',
            'dark:from-emerald-400 dark:to-emerald-500 dark:border-emerald-500',
            'dark:hover:from-emerald-300 dark:hover:to-emerald-400',
          ],
          isChainActive(b.key) && [
            'bg-gradient-to-b from-emerald-600 to-emerald-700 text-white border-emerald-700',
            'hover:from-emerald-500 hover:to-emerald-600',
            'dark:from-emerald-500 dark:to-emerald-600 dark:border-emerald-600',
            'dark:hover:from-emerald-400 dark:hover:to-emerald-500',
          ],
        ]"
        @click="toggleChain(b.key)"
      >
        <svg
          v-if="b.icon"
          viewBox="0 0 24 24"
          class="w-4 h-4 fill-current"
          aria-hidden="true"
        >
          <path :d="b.icon" />
        </svg>

        <span>{{ b.label }}</span>
      </button>

      <!-- Special Permissions in first row if there's space (only for global mode) -->
      <button
        v-for="specialPermission in mode === 'global' &&
        chainButtons.length + (createButton ? 1 : 0) < 4
          ? specialPermissions
          : []"
        :key="specialPermission.key"
        v-tooltip="specialPermission.description"
        type="button"
        :disabled="disabled"
        :aria-pressed="isExtraActiveOrImplicit(specialPermission.key)"
        class="px-3 py-2 rounded-lg border text-sm font-medium transition-all inline-flex items-center gap-2 shadow-sm"
        :class="[
          disabled
            ? 'opacity-50 cursor-not-allowed'
            : 'hover:shadow-md active:scale-95',
          !isExtraActiveOrImplicit(specialPermission.key) && [
            'bg-white text-gray-700 border-gray-300',
            'hover:bg-gray-50 hover:border-gray-400',
            'dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600',
            'dark:hover:bg-gray-750 dark:hover:border-gray-500',
          ],
          isExtraImplicit(specialPermission.key) && [
            'bg-gradient-to-b from-violet-400 to-violet-500 text-white border-violet-500',
            'hover:from-violet-300 hover:to-violet-400',
            'dark:from-violet-400 dark:to-violet-500 dark:border-violet-500',
            'dark:hover:from-violet-300 dark:hover:to-violet-400',
          ],
          isExtraActive(specialPermission.key) && [
            'bg-gradient-to-b from-violet-600 to-violet-700 text-white border-violet-700',
            'hover:from-violet-500 hover:to-violet-600',
            'dark:from-violet-500 dark:to-violet-600 dark:border-violet-600',
            'dark:hover:from-violet-400 dark:hover:to-violet-500',
          ],
        ]"
        @click="toggleExtra(specialPermission.key)"
      >
        <svg
          v-if="specialPermission.icon"
          viewBox="0 0 24 24"
          class="w-4 h-4 fill-current"
          aria-hidden="true"
        >
          <path :d="specialPermission.icon" />
        </svg>

        <span>{{ specialPermission.label }}</span>
      </button>
    </div>

    <!-- Extras in second row for object mode or if first row is full -->
    <div
      v-if="
        specialPermissions.length &&
        (mode === 'object' || chainButtons.length + (createButton ? 1 : 0) >= 4)
      "
      class="flex flex-col gap-2"
    >
      <!-- Divider between CRUD and special permissions -->
      <div class="flex items-center gap-2 pt-1">
        <div class="flex-1 h-px bg-gray-200 dark:bg-gray-700" />

        <span
          class="text-[10px] uppercase tracking-wider text-gray-400 dark:text-gray-500 font-medium"
        >
          {{ $t('components.permissionSelector.special') }}
        </span>

        <div class="flex-1 h-px bg-gray-200 dark:bg-gray-700" />
      </div>

      <!-- Category content -->
      <div class="inline-flex flex-wrap gap-2">
        <button
          v-for="specialPermission in specialPermissions"
          :key="specialPermission.key"
          v-tooltip="specialPermission.description"
          type="button"
          :disabled="disabled"
          :aria-pressed="isExtraActiveOrImplicit(specialPermission.key)"
          class="px-3 py-2 rounded-lg border text-sm font-medium transition-all inline-flex items-center gap-2 shadow-sm"
          :class="[
            disabled
              ? 'opacity-50 cursor-not-allowed'
              : 'hover:shadow-md active:scale-95',
            !isExtraActiveOrImplicit(specialPermission.key) && [
              'bg-white text-gray-700 border-gray-300',
              'hover:bg-gray-50 hover:border-gray-400',
              'dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600',
              'dark:hover:bg-gray-750 dark:hover:border-gray-500',
            ],
            isExtraImplicit(specialPermission.key) && [
              'bg-gradient-to-b from-violet-400 to-violet-500 text-white border-violet-500',
              'hover:from-violet-300 hover:to-violet-400',
              'dark:from-violet-400 dark:to-violet-500 dark:border-violet-500',
              'dark:hover:from-violet-300 dark:hover:to-violet-400',
            ],
            isExtraActive(specialPermission.key) && [
              'bg-gradient-to-b from-violet-600 to-violet-700 text-white border-violet-700',
              'hover:from-violet-500 hover:to-violet-600',
              'dark:from-violet-500 dark:to-violet-600 dark:border-violet-600',
              'dark:hover:from-violet-400 dark:hover:to-violet-500',
            ],
          ]"
          @click="toggleExtra(specialPermission.key)"
        >
          <svg
            v-if="specialPermission.icon"
            viewBox="0 0 24 24"
            class="w-4 h-4 fill-current"
            aria-hidden="true"
          >
            <path :d="specialPermission.icon" />
          </svg>

          <span>{{ specialPermission.label }}</span>
        </button>
      </div>
    </div>
  </div>
</template>
