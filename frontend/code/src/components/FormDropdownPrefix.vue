<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import BaseIcon from '@/components/BaseIcon.vue'

const props = defineProps({
  id: {
    type: String,
    default: null,
  },
  required: {
    type: Boolean,
    default: false,
  },
  disabled: Boolean,
  readonly: Boolean,
  modelValue: {
    type: [String, Number, Object, null],
    default: null,
  },
  // dropdown options: [{ label, value, icon? }]
  options: {
    type: Array,
    default: () => [],
  },
  prefixValue: {
    type: [String, Number, null],
    default: null,
  },
  borders: {
    type: String,
    default: 'left',
    validator: (value) =>
      ['all', 'none', 'right', 'left', 'top/bottom'].includes(value),
  },
})

const emit = defineEmits(['update:modelValue', 'update:prefixValue'])

const hasPrefix = computed(
  () => Array.isArray(props.options) && props.options.length > 0,
)

const localPrefixValue = ref(props.prefixValue)

const prefixOpen = ref(false)
const prefixButtonRef = ref(null)
const prefixMenuRef = ref(null)
const activeIndex = ref(-1)

const selectedIndex = computed(() => {
  const opts = props.options || []
  const idx = opts.findIndex(
    (o) => String(o.value) === String(localPrefixValue.value),
  )
  return idx >= 0 ? idx : 0
})

const selectedPrefixOption = computed(() => {
  const opts = props.options || []
  return (
    opts.find((o) => String(o.value) === String(localPrefixValue.value)) ||
    opts[0] ||
    null
  )
})

const truncatedLabel = computed(() => {
  const label = String(selectedPrefixOption.value?.label ?? '')
  if (label.length <= 8) return label
  return `${label.slice(0, 8)}...`
})

const selectPrefix = (opt) => {
  const val = opt?.value ?? ''
  localPrefixValue.value = val
  emit('update:prefixValue', val)
  prefixOpen.value = false
  activeIndex.value = -1
}

const togglePrefix = () => {
  if (props.disabled) return
  prefixOpen.value = !prefixOpen.value

  if (prefixOpen.value) {
    activeIndex.value = selectedIndex.value
  }
}

const closePrefix = () => {
  prefixOpen.value = false
  activeIndex.value = -1
}

const onPrefixKeydown = (e) => {
  if (props.disabled) return

  const opts = props.options || []
  if (!opts.length) return

  if (!prefixOpen.value && ['Enter', ' ', 'ArrowDown'].includes(e.key)) {
    e.preventDefault()
    prefixOpen.value = true
    activeIndex.value = 0
    return
  }

  if (!prefixOpen.value) return

  if (e.key === 'Escape') {
    e.preventDefault()
    closePrefix()
    prefixButtonRef.value?.focus?.()
  }

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    activeIndex.value = (activeIndex.value + 1) % opts.length
  }

  if (e.key === 'ArrowUp') {
    e.preventDefault()
    activeIndex.value = (activeIndex.value - 1 + opts.length) % opts.length
  }

  if (e.key === 'Enter') {
    e.preventDefault()
    selectPrefix(opts[activeIndex.value])
  }
}

const onDocumentPointerDown = (e) => {
  if (!prefixOpen.value) return
  const t = e.target
  if (
    !prefixButtonRef.value?.contains(t) &&
    !prefixMenuRef.value?.contains(t)
  ) {
    closePrefix()
  }
}

const wrapperClass = computed(() =>
  hasPrefix.value ? 'relative inline-flex' : 'relative inline-block',
)

const hasAnyPrefixIcon = computed(() =>
  (props.options || []).some((o) => !!o?.icon),
)

const prefixButtonWidthClass = computed(() =>
  hasAnyPrefixIcon.value ? 'w-32' : 'w-28',
)

const borderClass = computed(() => {
  const borderColorsDefault = 'border-gray-700 focus:border-gray-700'
  let dynamic = ''

  switch (props.borders) {
    case 'all':
      dynamic = 'border rounded focus:ring-4'
      break

    case 'left':
      dynamic =
        'border border-r-0 rounded-l rounded-r-none ' +
        'focus:ring-4 focus:border-r focus:rounded-r-none'
      break

    case 'right':
      dynamic =
        'border border-l-0 rounded-r rounded-l-none ' +
        'focus:ring-4 focus:border-l focus:rounded-l-none'
      break

    case 'top/bottom':
      dynamic = 'border-t border-b focus:ring-4'
      break

    case 'none':
      dynamic = 'border-0 focus:ring-0'
      break
  }

  return `${dynamic} ${borderColorsDefault}`
})

watch(
  () => props.prefixValue,
  (newVal) => {
    localPrefixValue.value = newVal
  },
  { immediate: true },
)

onMounted(() => {
  document.addEventListener('pointerdown', onDocumentPointerDown)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onDocumentPointerDown)
})
</script>

<template>
  <div :class="wrapperClass">
    <div v-if="hasPrefix" class="relative">
      <button
        ref="prefixButtonRef"
        type="button"
        :class="[
          borderClass,
          prefixButtonWidthClass,
          'relative',
          prefixOpen ? 'z-30' : 'z-5',
        ]"
        class="h-12 bg-white dark:bg-slate-800 px-3 text-sm inline-flex items-center gap-2 focus:outline-none focus:ring-blue-500 focus-visible:z-30"
        :disabled="disabled"
        @click="togglePrefix"
        @keydown="onPrefixKeydown"
      >
        <BaseIcon
          v-if="selectedPrefixOption?.icon"
          class="opacity-70 shrink-0"
          w="4"
          h="4"
          :path="selectedPrefixOption.icon"
          aria-hidden="true"
          focusable="false"
        />

        <span class="whitespace-nowrap">
          {{ truncatedLabel }}
        </span>

        <svg
          class="w-4 h-4 opacity-70 ml-auto shrink-0"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fill-rule="evenodd"
            d="M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 111.06 1.06l-4.24 4.24a.75.75 0 01-1.06 0L5.21 8.29a.75.75 0 01.02-1.08z"
          />
        </svg>
      </button>

      <div
        v-show="prefixOpen"
        ref="prefixMenuRef"
        class="absolute mt-2 min-w-44 rounded-md z-50 p-1 border border-slate-200 bg-white shadow-xl dark:bg-slate-800 dark:border-slate-200"
        role="listbox"
        @mouseleave="activeIndex = selectedIndex"
      >
        <button
          v-for="(opt, idx) in options"
          :key="String(opt.value)"
          type="button"
          class="w-full flex items-center gap-3 px-3 py-2 text-sm rounded text-left hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 ring-offset-2 ring-slate-300 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed text-slate-700 dark:text-slate-200"
          :class="idx === activeIndex ? 'bg-blue-200 dark:bg-blue-500' : ''"
          @click="selectPrefix(opt)"
          @mousemove="activeIndex = idx"
        >
          <BaseIcon
            v-if="opt.icon"
            class="shrink-0"
            w="4"
            h="4"
            :path="opt.icon"
            aria-hidden="true"
            focusable="false"
          />

          <span class="truncate flex-1">
            {{ opt.label }}
          </span>
        </button>
      </div>
    </div>
  </div>
</template>
