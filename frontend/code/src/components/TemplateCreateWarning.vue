<script setup>
import { mdiAlert } from '@mdi/js'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import CardBox from '@/components/CardBox.vue'
import CardBoxModal from '@/components/CardBoxModal.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import { useMainStore } from '@/stores/main'

const { t } = useI18n()
const mainStore = useMainStore()

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true,
  },
})

const emit = defineEmits(['update:modelValue', 'confirmed'])

const modalVisible = ref(props.modelValue)

const onFormSubmit = () => {
  emit('confirmed', true)
  emit('update:modelValue', false)
}

const docsURL = computed(
  () =>
    mainStore.settings?.branding?.docs?.deepurl +
    '/docs/usage/template-requirements',
)

watch(
  () => props.modelValue,
  (newVal) => {
    modalVisible.value = newVal
  },
)

watch(modalVisible, (newVal) => {
  emit('update:modelValue', newVal)
})
</script>

<template>
  <CardBoxModal
    v-model="modalVisible"
    form
    :title="t('components.deleteModal.confirmAction')"
    button="warning"
    has-cancel
    :button-label="t('common.confirm')"
    custom-class=" z-50 w-full md:w-4/5 lg:w-3/5 xl:w-fit"
    @form-submitted="onFormSubmit"
  >
    <CardBox class="grid mb-6">
      <NotificationBar :dismissable="false" color="warning" :icon="mdiAlert">
        <b>{{ t('components.templateWarning.intro') }}</b>

        <br />

        {{ t('components.templateWarning.docsLink') }}
        <u
          ><a :href="docsURL" target="_blank">{{
            t('components.templateWarning.here')
          }}</a></u
        >
      </NotificationBar>

      <b>{{ t('components.templateWarning.generalConfig') }}</b>

      <hr />

      <br />

      <ul>
        <li>{{ t('components.templateWarning.createAccount') }}</li>

        <li>{{ t('components.templateWarning.saveCredentials') }}</li>

        <li>{{ t('components.templateWarning.installGuestAgent') }}</li>

        <li>{{ t('components.templateWarning.enableDhcp') }}</li>
      </ul>

      <br />

      <b>{{ t('components.templateWarning.windowsConfig') }}</b>

      <hr />

      <br />

      <ul>
        <li>{{ t('components.templateWarning.virtioDrivers') }}</li>

        <li>{{ t('components.templateWarning.sysprep') }}</li>
      </ul>

      <br />

      <b>{{ t('components.templateWarning.verifyBeforeConvert') }}</b>

      <hr />

      <br />

      <ul>
        <li>{{ t('components.templateWarning.testNetwork') }}</li>

        <li>{{ t('components.templateWarning.testLogin') }}</li>

        <li>{{ t('components.templateWarning.shutdownVm') }}</li>
      </ul>
    </CardBox>
  </CardBoxModal>
</template>

<style scoped>
ul {
  list-style: inside !important;
}
</style>
