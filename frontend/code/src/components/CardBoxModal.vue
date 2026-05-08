<script setup>
import { mdiClose } from '@mdi/js'
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxComponentTitle from '@/components/CardBoxComponentTitle.vue'
import OverlayLayer from '@/components/OverlayLayer.vue'
import { useStyleStore } from '@/stores/style.js'

const { t } = useI18n()
const styleStore = useStyleStore()

const props = defineProps({
  customClass: {
    type: [String, Array, Object],
    default: '',
  },
  title: {
    type: String,
    required: true,
  },
  button: {
    type: String,
    default: 'info',
  },
  buttonLabel: {
    type: String,
    default: null,
  },
  hasCancel: {
    type: Boolean,
    default: false,
  },
  modelValue: {
    type: [String, Number, Boolean],
    default: null,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  scrollable: {
    type: Boolean,
    default: false,
  },
  crossmark: {
    type: Boolean,
    default: true,
  },
  hasButton: {
    type: Boolean,
    default: true,
  },
  hasSearch: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'cancel', 'form-submitted'])

const value = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const confirmCancel = (mode) => {
  value.value = false
  emit(mode)
}

const confirm = () => confirmCancel('form-submitted')

const cancel = () => confirmCancel('cancel')

function handleKeydown(e) {
  if (e.key === 'Escape' && value.value) {
    cancel()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
})

const contentClass = computed(() => ({
  'space-y-3 flex-grow px-4': true,
  'overflow-y-auto': props.scrollable,
  dark: styleStore.darkMode,
}))

const componentClass = computed(() => {
  const base = [
    'shadow-lg w-11/12 md:w-3/5 lg:w-2/5 xl:w-4/12 z-50 flex flex-col',
    'max-h-screen md:max-h-[90vh]',
    props.customClass,
  ]

  if (styleStore.darkMode) {
    base.push('dark')
  }

  return base
})
</script>

<template>
  <OverlayLayer v-show="value" @overlay-click="cancel">
    <CardBox
      v-show="value"
      :class="componentClass"
      is-modal
      :has-search="hasSearch"
    >
      <CardBoxComponentTitle :title="title">
        <BaseButton
          v-if="crossmark"
          :icon="mdiClose"
          color="whiteDark"
          small
          rounded-full
          @click.prevent="cancel"
        />
      </CardBoxComponentTitle>

      <div
        :class="[
          contentClass,
          'max-h-[calc(80vh-100px)]',
          !props.hasSearch && 'overflow-y-auto',
        ]"
      >
        <slot />
      </div>

      <template v-if="hasButton || hasCancel" #footer>
        <BaseButtons>
          <BaseButton
            v-if="hasButton"
            :label="buttonLabel || t('common.confirm')"
            :color="button"
            type="submit"
            :disabled="disabled"
            @click="confirm"
          />

          <BaseButton
            v-if="hasCancel"
            :label="t('common.cancel')"
            :color="button"
            outline
            @click="cancel"
          />
        </BaseButtons>
      </template>
    </CardBox>
  </OverlayLayer>
</template>
