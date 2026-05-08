<script setup>
import { mdiApplicationBrackets, mdiMonitor, mdiRename } from '@mdi/js'
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseDivider from '@/components/BaseDivider.vue'
import BaseMarkdown from '@/components/BaseMarkdown.vue'
import CardBox from '@/components/CardBox.vue'
import FormCheckRadio from '@/components/FormCheckRadio.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import PillTag from '@/components/PillTag.vue'
import SearchControl from '@/components/SearchControl.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import UnsavedChangesModal from '@/components/UnsavedChangesModal.vue'
import { useUnsavedChanges } from '@/composables/useUnsavedChanges'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import router from '@/router'
import backend from '@/services'
import { useLookupStore } from '@/stores/lookup'
import { statusColorVM } from '@/utils/objectColors'

const { t } = useI18n()
const originalVM = ref({})
const restartRequired = ref(false)
const route = useRoute()
const toast = useToast()
const vm = ref({})

const {
  showDiscardModal,
  setOriginal,
  markAsSaved,
  handleCancel,
  confirmDiscard,
  cancelDiscard,
} = useUnsavedChanges({
  formData: vm,
  onNavigateAway: () => router.back(),
})

async function fetchVM(vmId) {
  try {
    const data = await backend.vms.get(vmId)
    data.ram = data.ram / 1024

    vm.value = JSON.parse(JSON.stringify(data))
    originalVM.value = JSON.parse(JSON.stringify(data))
    setOriginal()
  } catch (error) {
    toast.error(
      t('common.loadError', {
        entity: t('objectTypes.virtualMachine.singular'),
      }),
    )
  }
}

async function submit() {
  try {
    const res = await backend.vms.update(vm.value.id, {
      name: vm.value.name,
      description: vm.value.description,
      cpu: vm.value.cpu,
      ram: vm.value.ram * 1024,
      os: vm.value.os,
      restart_vm: vm.value.restart_vm,
    })
    toast.success(
      t('common.editSuccess', {
        entity: t('objectTypes.virtualMachine.singular'),
      }),
    )
    useLookupStore().updateFromObject('vms', res)
    markAsSaved()
    router.push({ path: `/vms/${vm.value.id}` })
  } catch (error) {
    toast.error(
      t('common.editError', {
        entity: t('objectTypes.virtualMachine.singular'),
      }),
    )
  }
}

function onCancel() {
  if (handleCancel()) router.back()
}

onMounted(() => {
  fetchVM(route.params.id)
})

/**
 * this seems ugly and easy to improve - but if it's not handled
 * exactly like this, it does not work.
 * try your luck and let me know ~ phauch
 */
watch(
  () => [vm.value.cpu, vm.value.ram],
  ([newCpu, newRam]) => {
    if (vm.value.status.toLowerCase() !== 'running') {
      restartRequired.value = false
    } else if (
      newCpu != originalVM.value.cpu ||
      newRam != originalVM.value.ram
    ) {
      restartRequired.value = true
    } else {
      restartRequired.value = false
    }
  },
)
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiMonitor"
        :title="
          $t('common.editTitle', {
            entity: $t('objectTypes.virtualMachine.singular'),
          })
        "
        main
        docs-path="/docs/usage/openvle/vms/"
      >
        <PillTag
          v-if="vm.status"
          :label="vm.status ? vm.status : 'unkwn'"
          :color="statusColorVM(vm.status)"
          :disabled="true"
        />
      </SectionTitleLineWithButton>

      <CardBox is-form @submit.prevent="submit">
        <FormField>
          <FormField
            :label="$t('common.name')"
            :help="$t('views.vms.nameHelp')"
          >
            <FormControl
              v-model="vm.name"
              :icon="mdiRename"
              :placeholder="$t('views.vms.namePlaceholder')"
              maxlength="50"
              required
            />
          </FormField>

          <FormField
            :label="$t('views.vms.osLabel')"
            :help="$t('views.vms.osHelp')"
          >
            <SearchControl
              v-model="vm.os"
              :icon="mdiApplicationBrackets"
              :fetch-data="backend.os.search"
              :fetch-selected="backend.os.getName"
              required
            />
          </FormField>
        </FormField>

        <BaseDivider />

        <FormField>
          <FormField
            :label="$t('views.vms.cpuCoresLabel')"
            :help="$t('views.vms.cpuCoresHelp')"
            :tooltip="$t('views.vms.edit.cpuTooltip')"
          >
            <FormControl
              v-model="vm.cpu"
              type="range"
              placeholder="2"
              :min="1"
              :max="12"
              required
            />
          </FormField>

          <FormField
            :label="$t('views.vms.ramLabel')"
            :help="$t('views.vms.ramHelp')"
            :tooltip="$t('views.vms.edit.ramTooltip')"
          >
            <FormControl
              v-model="vm.ram"
              type="range"
              placeholder="4"
              :min="1"
              :max="20"
              :step="1"
              required
            />
          </FormField>
        </FormField>

        <BaseDivider />

        <FormField
          :label="$t('common.description')"
          :help="$t('views.vms.descriptionHelpMarkdown')"
        >
          <BaseMarkdown v-model="vm.description" action="edit" />
        </FormField>

        <BaseDivider />

        <FormCheckRadio
          v-if="restartRequired"
          v-model="vm.restart_vm"
          name="restart_vm"
          :help="$t('views.vms.edit.autoRestartHelp')"
          :label="$t('views.vms.edit.autoRestartLabel')"
          type="checkbox"
        />

        <template #footer>
          <BaseButtons>
            <BaseButton type="submit" color="info" :label="$t('common.save')" />

            <BaseButton
              type="button"
              color="info"
              :label="$t('common.cancel')"
              outline
              @click="onCancel"
            />
          </BaseButtons>
        </template>
      </CardBox>

      <UnsavedChangesModal
        v-model="showDiscardModal"
        @discard="confirmDiscard"
        @continue="cancelDiscard"
      />
    </SectionMain>
  </LayoutAuthenticated>
</template>
