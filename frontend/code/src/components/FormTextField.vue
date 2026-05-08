<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import FormControlIcon from '@/components/FormControlIcon.vue'
import { useMainStore } from '@/stores/main'

const props = defineProps({
  name: {
    type: String,
    default: null,
  },
  id: {
    type: String,
    default: null,
  },
  autocomplete: {
    type: String,
    default: null,
  },
  maxlength: {
    type: String,
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
  required: Boolean,
  borderless: Boolean,
  transparent: Boolean,
  ctrlKFocus: Boolean,
  disabled: Boolean,
  readonly: Boolean,
})

const emit = defineEmits(['update:modelValue', 'scrolled', 'setRef'])

const computedValue = computed({
  get: () => props.modelValue,
  set: (value) => {
    emit('update:modelValue', value)
  },
})

const textareaElClass = computed(() => [
  'px-3 py-2 max-w-full focus:ring focus:outline-none border-gray-700 rounded w-full',
  'dark:placeholder-gray-400',
  'h-full', // Full height for textarea
  'resize-none', // Disable resizing
  props.borderless ? 'border-0' : 'border',
  props.transparent ? 'bg-transparent' : 'bg-white dark:bg-slate-800',
  props.icon ? 'pl-10' : '',
])

const mainStore = useMainStore()

const textareaEl = ref(null)

onMounted(() => {
  if (textareaEl.value) {
    autoResizeTextarea()
    emit('setRef', textareaEl.value)
  }
})

const autoResizeTextarea = () => {
  const textarea = textareaEl.value
  if (textarea) {
    textarea.style.height = 'auto'
    // textarea.style.height = `${Math.min(textarea.scrollHeight, window.innerHeight * 0.8)}px`
    textarea.style.height = `${window.innerHeight * 0.6}px`
  }
}

if (props.ctrlKFocus) {
  const fieldFocusHook = (e) => {
    if (e.ctrlKey && e.key === 'k') {
      e.preventDefault()
      textareaEl.value.focus()
    } else if (e.key === 'Escape') {
      textareaEl.value.blur()
    }
  }

  onMounted(() => {
    if (!mainStore.isFieldFocusRegistered) {
      window.addEventListener('keydown', fieldFocusHook)
      mainStore.isFieldFocusRegistered = true
    }
  })

  onBeforeUnmount(() => {
    window.removeEventListener('keydown', fieldFocusHook)
    mainStore.isFieldFocusRegistered = false
  })
}

const handleScroll = () => {
  const textarea = textareaEl.value
  const isAtBottom =
    textarea.scrollHeight - textarea.clientHeight <= textarea.scrollTop + 1
  if (isAtBottom) {
    emit('scrolled')
  }
}
</script>

<template>
  <div class="relative">
    <textarea
      :id="props.id"
      ref="textareaEl"
      v-model="computedValue"
      :name="props.name"
      :maxlength="props.maxlength"
      :placeholder="props.placeholder"
      :required="props.required"
      :class="textareaElClass"
      :disabled="props.disabled"
      :readonly="props.readonly"
      @input="autoResizeTextarea"
      @scroll="handleScroll"
    ></textarea>

    <FormControlIcon v-if="props.icon" :icon="props.icon" h="h-full" />
  </div>
</template>
