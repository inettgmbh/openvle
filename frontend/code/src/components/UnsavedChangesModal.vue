<script setup>
import { mdiAlertCircleOutline } from '@mdi/js'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxComponentTitle from '@/components/CardBoxComponentTitle.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import OverlayLayer from '@/components/OverlayLayer.vue'
import { useStyleStore } from '@/stores/style.js'

const { t } = useI18n()
const styleStore = useStyleStore()

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'discard', 'continue'])

const value = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

function onDiscard() {
  value.value = false
  emit('discard')
}

function onContinue() {
  value.value = false
  emit('continue')
}

const componentClass = computed(() => {
  const base = [
    'shadow-lg w-11/12 md:w-3/5 lg:w-2/5 xl:w-4/12 z-50 flex flex-col',
    'max-h-screen md:max-h-[90vh]',
  ]

  if (styleStore.darkMode) {
    base.push('dark')
  }

  return base
})
</script>

<template>
  <OverlayLayer v-show="value" @overlay-click="onContinue">
    <CardBox v-show="value" :class="componentClass" is-modal>
      <CardBoxComponentTitle
        :title="t('components.unsavedChangesModal.title')"
      />

      <div class="space-y-3 flex-grow px-4">
        <NotificationBar
          color="warning"
          :icon="mdiAlertCircleOutline"
          :dismissable="false"
        >
          {{ t('components.unsavedChangesModal.warning') }}
        </NotificationBar>
      </div>

      <template #footer>
        <BaseButtons>
          <BaseButton
            :label="t('components.unsavedChangesModal.discard')"
            color="danger"
            @click="onDiscard"
          />

          <BaseButton
            :label="t('components.unsavedChangesModal.continueEditing')"
            color="info"
            outline
            @click="onContinue"
          />
        </BaseButtons>
      </template>
    </CardBox>
  </OverlayLayer>
</template>
