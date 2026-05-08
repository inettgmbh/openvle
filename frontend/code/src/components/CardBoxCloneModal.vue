<script setup>
import { mdiClose, mdiPencil } from '@mdi/js'
import { mdiContentCopy } from '@mdi/js'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useSlots } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxComponentTitle from '@/components/CardBoxComponentTitle.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import OverlayLayer from '@/components/OverlayLayer.vue'
import { useStyleStore } from '@/stores/style.js'

const { t } = useI18n()
const styleStore = useStyleStore()

const props = defineProps({
  modelValue: {
    type: [String, Number, Boolean],
    default: null,
  },
  name: {
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

const checkvalue = computed(() => t('common.clone'))

const confirm = () => confirmCancel('form-submitted')

const cancel = () => confirmCancel('cancel')

const copied = ref(false)

const confirmationName = ref('')

const hasInputSlot = computed(() => !!slots.default)

const isNameMatch = computed(() => confirmationName.value === checkvalue.value)

const slots = useSlots()

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
            t('components.cloneModal.willBeCloned', {
              name: props.name,
            })
          }}
        </p>

        <p>
          {{ t('components.cloneModal.assignmentsCopied') }}
        </p>

        <div v-if="hasInputSlot">
          <hr class="pb-3" />

          <slot />
        </div>

        <hr />

        {{ t('components.deleteModal.confirmPrompt') }}

        <b class="pr-2">"{{ checkvalue }}"</b>

        <BaseButton
          :icon="mdiContentCopy"
          color="light"
          small
          rounded-full
          :class="[
            'transition-colors duration-300',
            copied ? 'bg-green-500 text-white' : '',
          ]"
          @click="copyToClipboard(checkvalue)"
        />

        <FormField>
          <FormControl
            v-model="confirmationName"
            :icon="mdiPencil"
            :placeholder="checkvalue"
          />
        </FormField>
      </div>

      <template #footer>
        <BaseButtons>
          <BaseButton
            :label="t('common.clone')"
            color="info"
            type="submit"
            :disabled="!isNameMatch"
            @click="confirm"
          />

          <BaseButton
            :label="t('common.cancel')"
            color="info"
            outline
            @click="cancel"
          />
        </BaseButtons>
      </template>
    </CardBox>
  </OverlayLayer>
</template>
