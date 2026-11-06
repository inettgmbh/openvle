<script setup>
import { mdiEye } from '@mdi/js'
import { computed, inject, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseIcon from '@/components/BaseIcon.vue'
import FormControlIcon from '@/components/FormControlIcon.vue'
import { useMainStore } from '@/stores/main'

const { t } = useI18n()

const props = defineProps({
  name: {
    type: String,
    default: null,
  },
  id: {
    type: String,
    default: null,
  },
  ariaDescribedby: {
    type: String,
    default: null,
  },
  autocomplete: {
    type: String,
    default: null,
  },
  maxlength: {
    type: [String, Number],
    default: null,
  },
  placeholder: {
    type: String,
    default: null,
  },
  inputmode: {
    type: String,
    default: null,
  },
  icon: {
    type: String,
    default: null,
  },
  options: {
    type: Array,
    default: null,
  },
  type: {
    type: String,
    default: 'text',
  },
  modelValue: {
    type: [String, Number, Boolean, Array, Object],
    default: '',
  },
  min: {
    type: [String, Number],
    default: null,
  },
  max: {
    type: [String, Number],
    default: null,
  },
  step: {
    type: [String, Number],
    default: null,
  },
  link: {
    type: String,
    default: null,
  },
  validate: {
    type: [Boolean, Function],
    default: false,
    required: false,
  },
  autofocus: Boolean,
  required: Boolean,
  borderless: Boolean,
  transparent: Boolean,
  ctrlKFocus: Boolean,
  disabled: Boolean,
  readonly: Boolean,
  resize: Boolean,
  rows: {
    type: [String, Number],
    default: null,
  },
})

const router = useRouter()

const emit = defineEmits([
  'update:modelValue',
  'setRef',
  'update:validationError',
])

const computedValue = computed({
  get: () => props.modelValue,
  set: (value) => {
    emit('update:modelValue', value)
    inputValidator(value)
  },
})

const validationError = ref('')

/** Input validation logic */
const inputValidator = (value) => {
  if (props.validate === false) return
  if (props.validate && typeof props.validate === 'function') {
    const result = props.validate(value)
    if (result === true) {
      validationError.value = ''
    } else {
      validationError.value = result
    }
  } else if (props.validate === false) {
    validationError.value = ''
  } else {
    /** Fallback to default validation */
    if (props.required && !value) {
      validationError.value = t('components.formControl.fieldRequired')
    } else if (props.maxlength && value.length > props.maxlength) {
      validationError.value = t('components.formControl.maxLengthExceeded', {
        max: props.maxlength,
      })
    } else {
      validationError.value = ''
    }
  }

  emit('update:validationError', validationError.value)
}

const inputElClass = computed(() => {
  const isRange = computedType.value === 'range'
  const base = [
    isRange ? 'w-full' : 'px-3 py-2 max-w-full',
    'px-3 py-2 max-w-full w-full',
    'focus:ring focus:outline-none border-gray-700 rounded',
    'dark:placeholder-gray-400',
    computedType.value === 'textarea' ? (props.rows ? '' : 'h-24') : 'h-12',
    props.borderless ? 'border-0' : 'border',
    props.transparent ? 'bg-transparent' : 'bg-white dark:bg-slate-800',
    validationError.value ? 'border-red-500 border-2' : '',
    props.resize ? '' : 'resize-none',
  ]

  if (props.icon && !isRange) {
    base.push('pl-10')
  }
  if (props.link && !isRange && computedType.value !== 'select') {
    base.push('pr-10')
  }

  return base
})

const computedType = computed(() => (props.options ? 'select' : props.type))

const controlIconH = computed(() =>
  props.type === 'textarea' ? 'h-full' : 'h-12',
)

const handleClick = (event) => {
  if (props.link == null) return

  const isExternal = /^https?:\/\//.test(props.link)
  const openInNewTab = event.metaKey || event.ctrlKey
  if (computedValue.value) {
    if (isExternal) {
      window.open(props.link, '_blank')
    } else if (openInNewTab) {
      window.open(`/#${props.link}`, '_blank')
    } else {
      router.push({ path: props.link })
    }
  }
}

const mainStore = useMainStore()

const selectEl = ref(null)

const textareaEl = ref(null)

const inputEl = ref(null)

onMounted(() => {
  if (
    computedType.value === 'select' &&
    props.options &&
    props.options.length > 0
  ) {
    // Find the option with selected: true and set its value as the computedValue
    const selectedOption = props.options.find((option) => option.selected)
    computedValue.value = selectedOption ? selectedOption.value : null
  }

  if (selectEl.value) {
    emit('setRef', selectEl.value)
  } else if (textareaEl.value) {
    emit('setRef', textareaEl.value)
  } else {
    emit('setRef', inputEl.value)
  }
})

if (props.ctrlKFocus) {
  const fieldFocusHook = (e) => {
    if (e.ctrlKey && e.key === 'k') {
      e.preventDefault()
      inputEl.value.focus()
    } else if (e.key === 'Escape') {
      inputEl.value.blur()
    }
  }

  onMounted(() => {
    if (!mainStore.isFieldFocusRegistered) {
      window.addEventListener('keydown', fieldFocusHook)
      mainStore.isFieldFocusRegistered = true
    } else {
      // console.error('Duplicate field focus event')
    }
  })

  onBeforeUnmount(() => {
    window.removeEventListener('keydown', fieldFocusHook)
    mainStore.isFieldFocusRegistered = false
  })
}

const formFieldContext = inject('formFieldControlContext', null)

const effectiveId = computed(
  () => props.id || formFieldContext?.inputId?.value || null,
)
const effectiveDescribedby = computed(
  () =>
    props.ariaDescribedby || formFieldContext?.ariaDescribedby?.value || null,
)
</script>

<template>
  <div>
    <div class="relative">
      <select
        v-if="computedType === 'select'"
        :id="effectiveId"
        v-model="computedValue"
        :aria-describedby="effectiveDescribedby"
        :name="name"
        :class="inputElClass"
        :required="required"
        :disabled="disabled"
      >
        <option v-if="!required" :value="null" />

        <option
          v-for="option in options"
          :key="option.id ?? option"
          :value="option.value"
          :disabled="option.disabled || disabled"
          :readonly="option.readonly || readonly"
        >
          {{ option.label ?? option }}
        </option>
      </select>

      <textarea
        v-else-if="computedType === 'textarea'"
        :id="effectiveId"
        v-model="computedValue"
        :aria-describedby="effectiveDescribedby"
        :class="inputElClass"
        :name="name"
        :maxlength="maxlength"
        :placeholder="placeholder"
        :required="required"
        :disabled="disabled"
        :rows="rows"
      />

      <div v-else-if="computedType === 'range'" class="w-full">
        <div
          class="flex justify-between items-center mb-1 text-sm text-gray-600 dark:text-gray-300"
        >
          <span>{{ min }}</span>

          <span class="font-bold">{{ computedValue }}</span>

          <span>{{ max }}</span>
        </div>

        <input
          :id="effectiveId"
          ref="inputEl"
          v-model="computedValue"
          :aria-describedby="effectiveDescribedby"
          type="range"
          :min="min"
          :max="max"
          :step="step"
          :disabled="disabled"
          :readonly="readonly"
          :autofocus="autofocus"
          class="w-full appearance-none h-2 bg-gray-200 rounded-full outline-none transition-all dark:bg-slate-600 focus:ring-2 focus:ring-blue-400 dark:focus:ring-blue-500 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:bg-blue-600 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:cursor-pointer [&::-moz-range-thumb]:w-4 [&::-moz-range-thumb]:h-4 [&::-moz-range-thumb]:bg-blue-600 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:cursor-pointer"
        />
      </div>

      <input
        v-else
        :id="effectiveId"
        ref="inputEl"
        v-model="computedValue"
        :aria-describedby="effectiveDescribedby"
        :name="name"
        :maxlength="maxlength"
        :inputmode="inputmode"
        :autocomplete="autocomplete"
        :required="required"
        :placeholder="placeholder"
        :type="computedType"
        :class="inputElClass"
        :disabled="disabled"
        :readonly="readonly"
        :autofocus="autofocus"
        :min="min"
        :max="max"
        :step="step"
      />

      <FormControlIcon v-if="icon" :icon="icon" :h="controlIconH" />

      <div
        v-if="link && computedType !== 'select' && computedType !== 'range'"
        class="absolute right-2 top-1/2 -translate-y-1/2 cursor-pointer text-gray-500 hover:text-blue-600"
        @click="handleClick"
      >
        <BaseIcon
          v-tooltip="t('components.formControl.open')"
          :path="mdiEye"
          :size="20"
        />
      </div>
    </div>

    <!-- Validation error, if ValidationError -->
    <transition name="fade">
      <div
        v-if="validationError"
        class="text-red-500 text-sm mt-1 text-right font-medium"
      >
        {{ validationError }}
      </div>
    </transition>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter,
.fade-leave-to {
  opacity: 0;
}
</style>
