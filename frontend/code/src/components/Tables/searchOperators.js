import {
  mdiCircle,
  mdiCircleOutline,
  mdiEqual,
  mdiGreaterThan,
  mdiGreaterThanOrEqual,
  mdiLessThan,
  mdiLessThanOrEqual,
  mdiMagnifyClose,
  mdiNotEqual,
  mdiTextSearch,
} from '@mdi/js'
import { computed } from 'vue'

import { getI18nT } from '@/i18n'

/**
 * Returns operator definitions with translated labels.
 *
 * @returns {Object} Operator map keyed by operator name.
 */
function getOperators() {
  const t = getI18nT()
  return {
    eq: {
      key: 'eq',
      label: t('components.searchOperators.eq'),
      icon: mdiEqual,
    },
    neq: {
      key: 'neq',
      label: t('components.searchOperators.neq'),
      icon: mdiNotEqual,
    },
    contains: {
      key: 'contains',
      label: t('components.searchOperators.contains'),
      icon: mdiTextSearch,
    },
    ncontains: {
      key: 'ncontains',
      label: t('components.searchOperators.ncontains'),
      icon: mdiMagnifyClose,
    },
    empty: {
      key: 'empty',
      label: t('components.searchOperators.empty'),
      icon: mdiCircleOutline,
    },
    nempty: {
      key: 'nempty',
      label: t('components.searchOperators.nempty'),
      icon: mdiCircle,
    },
    gt: {
      key: 'gt',
      label: t('components.searchOperators.gt'),
      icon: mdiGreaterThan,
    },
    lt: {
      key: 'lt',
      label: t('components.searchOperators.lt'),
      icon: mdiLessThan,
    },
    gte: {
      key: 'gte',
      label: t('components.searchOperators.gte'),
      icon: mdiGreaterThanOrEqual,
    },
    lte: {
      key: 'lte',
      label: t('components.searchOperators.lte'),
      icon: mdiLessThanOrEqual,
    },
    // Date-specific operators with different labels
    after: {
      key: 'gt',
      label: t('components.searchOperators.after'),
      icon: mdiGreaterThan,
    },
    before: {
      key: 'lt',
      label: t('components.searchOperators.before'),
      icon: mdiLessThan,
    },
    after_or_on: {
      key: 'gte',
      label: t('components.searchOperators.afterOrOn'),
      icon: mdiGreaterThanOrEqual,
    },
    before_or_on: {
      key: 'lte',
      label: t('components.searchOperators.beforeOrOn'),
      icon: mdiLessThanOrEqual,
    },
  }
}

// Cached computed — re-evaluates only when locale changes
const operatorsComputed = computed(() => getOperators())

/**
 * Operator presets for TableSearchBar field definitions.
 *
 * @example
 * import { SearchOperators } from '@/components/Tables/searchOperators'
 *
 * const fields = [
 *   { key: 'name', operators: SearchOperators.TEXT },
 *   { key: 'status', operators: SearchOperators.EQUALS_ONLY },
 *   { key: 'count', operators: SearchOperators.NUMBER },
 *   { key: 'createdAt', type: 'datetime', operators: SearchOperators.DATE },
 * ]
 */
export const SearchOperators = {
  /** Text field operators: eq, neq, contains, ncontains, empty, nempty */
  get TEXT() {
    const ops = operatorsComputed.value
    return [ops.eq, ops.neq, ops.contains, ops.ncontains, ops.empty, ops.nempty]
  },

  /** Number field operators: eq, neq, gt, gte, lt, lte, empty, nempty */
  get NUMBER() {
    const ops = operatorsComputed.value
    return [
      ops.eq,
      ops.neq,
      ops.gt,
      ops.gte,
      ops.lt,
      ops.lte,
      ops.empty,
      ops.nempty,
    ]
  },

  /** Simple eq/neq for dropdown/lookup fields */
  get EQUALS_ONLY() {
    const ops = operatorsComputed.value
    return [ops.eq, ops.neq]
  },
  get EQUALS_ONLY_ONLY() {
    const ops = operatorsComputed.value
    return [ops.eq]
  },

  /** Simple contains only for fields */
  get CONTAINS_ONLY() {
    const ops = operatorsComputed.value
    return [ops.contains]
  },

  /** Date/time field operators: eq, neq, after, after_or_on, before, before_or_on, empty, nempty */
  get DATE() {
    const ops = operatorsComputed.value
    return [
      ops.eq,
      ops.neq,
      ops.after,
      ops.after_or_on,
      ops.before,
      ops.before_or_on,
      ops.empty,
      ops.nempty,
    ]
  },

  /** All individual operators for custom combinations */
  get ALL() {
    return operatorsComputed.value
  },
}
