<script setup>
import { mdiClose, mdiPencil } from '@mdi/js'
import { mdiContentCopy } from '@mdi/js'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxComponentTitle from '@/components/CardBoxComponentTitle.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import OverlayLayer from '@/components/OverlayLayer.vue'
import { useStyleStore } from '@/stores/style.js'
import { useAutofocusInput } from '@/utils/useAutofocusInput'

const { t } = useI18n()
const styleStore = useStyleStore()

const props = defineProps({
  modelValue: {
    type: [String, Number, Boolean],
    default: null,
  },
  parentObject: {
    type: String,
    default: null,
  },
  relatedObject: {
    type: String,
    default: null,
  },
  checkvalue: {
    type: String,
    default: null,
  },
})

const emit = defineEmits(['update:modelValue', 'cancel', 'form-submitted'])

const value = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const confirmCancel = (mode) => {
  value.value = false
  confirmationName.value = ''
  emit(mode)
}

const confirm = () => confirmCancel('form-submitted')

const cancel = () => confirmCancel('cancel')

const copied = ref(false)

const confirmationName = ref('')

const { autoFocusInputRef } = useAutofocusInput(value)

const isNameMatch = computed(() => confirmationName.value === props.checkvalue)

const handleEscape = (e) => {
  if (e.key === 'Escape' && value.value) {
    cancel()
  }
}

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    setTimeout(() => (copied.value = false), 1200)
  } catch (err) {
    console.error('Copy to clipboard failed:', err)
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleEscape)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleEscape)
})
</script>

<template>
  <OverlayLayer v-show="value" @overlay-click="cancel">
    <CardBox
      v-show="value"
      class="shadow-lg max-h-modal w-11/12 md:w-3/5 lg:w-2/5 xl:w-4/12 z-50"
      is-modal
      :class="{ dark: styleStore.darkMode }"
    >
      <CardBoxComponentTitle :title="t('components.deleteModal.confirmAction')">
        <BaseButton
          :icon="mdiClose"
          color="whiteDark"
          small
          rounded-full
          @click.prevent="cancel"
        />
      </CardBoxComponentTitle>

      <div class="space-y-3">
        <p>
          {{
            t('components.deleteRelationModal.willBeRemoved', {
              parent: props.parentObject,
              related: props.relatedObject,
            })
          }}
        </p>

        <p>
          {{ t('components.deleteRelationModal.objectsRemain') }}
        </p>

        <hr />

        {{ t('components.deleteModal.confirmPrompt') }}<br />

        <p class="flex items-center gap-2">
          <b>"{{ props.checkvalue }}"</b>

          <BaseButton
            :icon="mdiContentCopy"
            color="light"
            small
            rounded-full
            :class="[
              'transition-colors duration-300',
              copied ? 'bg-green-500 text-white' : '',
            ]"
            @click="copyToClipboard(props.checkvalue)"
          />
        </p>

        <FormField>
          <FormControl
            v-model="confirmationName"
            :icon="mdiPencil"
            :placeholder="props.checkvalue"
            @set-ref="(el) => (autoFocusInputRef = el)"
          />
        </FormField>
      </div>

      <template #footer>
        <BaseButtons>
          <BaseButton
            :label="t('common.remove')"
            color="danger"
            type="submit"
            :disabled="!isNameMatch"
            @click="confirm"
          />

          <BaseButton
            :label="t('common.cancel')"
            color="danger"
            outline
            @click="cancel"
          />
        </BaseButtons>
      </template>
    </CardBox>
  </OverlayLayer>
</template>
