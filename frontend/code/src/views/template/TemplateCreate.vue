<script setup>
import {
  mdiAlert,
  mdiEye,
  mdiInformation,
  mdiMonitor,
  mdiRename,
  mdiVectorArrangeAbove,
} from '@mdi/js'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseDivider from '@/components/BaseDivider.vue'
import BaseMarkdown from '@/components/BaseMarkdown.vue'
import CardBox from '@/components/CardBox.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import SearchControl from '@/components/SearchControl.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import TemplateCreateWarning from '@/components/TemplateCreateWarning.vue'
import UnsavedChangesModal from '@/components/UnsavedChangesModal.vue'
import { useUnsavedChanges } from '@/composables/useUnsavedChanges'
import { FIELD_LIMITS } from '@/config/fieldLimits'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import router from '@/router'
import backend from '@/services'
import { useMainStore } from '@/stores/main'

const { t } = useI18n()
const route = useRoute()
const showCreateWarning = ref(false)
const template = ref({})
const toast = useToast()

const {
  showDiscardModal,
  setOriginal,
  markAsSaved,
  handleCancel,
  confirmDiscard,
  cancelDiscard,
} = useUnsavedChanges({
  formData: template,
  onNavigateAway: () => router.back(),
})

async function submit() {
  try {
    const res = await backend.templates.create({
      name: template.value.name,
      description: template.value.description,
      cpu: template.value.cpu,
      ram: template.value.ram * 1024,
      source_vm: template.value.source_vm,
    })
    toast.success(
      t('common.createSuccess', { entity: t('objectTypes.template.singular') }),
    )
    useMainStore().fetchPermissions()
    markAsSaved()
    router.push({ path: `/templates/${res.id}` })
  } catch (error) {
    toast.error(
      `${t('common.createError', { entity: t('objectTypes.template.singular') })}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  }
}

async function fetchSourceVM(vmId) {
  try {
    await backend.vms.get(vmId).then(async (response) => {
      template.value.description = response.description
      template.value.cpu = response.cpu
      template.value.ram = response.ram / 1024
      template.value.statusSourceVM = response.status
      template.value.nameSourceVM = response.name
    })
  } catch (error) {
    toast.warning(t('views.templates.create.sourceVmNotFound'))
  }
}

const showDetail = computed(() => {
  return template.value.source_vm ? true : false
})

const vmClonable = computed(() => {
  return template.value.statusSourceVM == 'stopped'
})

function onVMSearchStarted() {
  if (template.value.source_vm) {
    template.value.source_vm = null
    template.value.description = ''
    template.value.cpu = undefined
    template.value.ram = undefined
  }
}

watch(
  () => template.value.source_vm,
  async (newVM) => {
    if (newVM) {
      await fetchSourceVM(newVM)
    }
  },
  { immediate: true },
)

function onCancel() {
  if (handleCancel()) router.back()
}

onMounted(() => {
  template.value.cpu = route.query.cpu
  template.value.description = route.query.description
  template.value.name = route.query.name
  template.value.vm = route.query.vm
  template.value.ram = route.query.ram / 1024
  template.value.source_vm = route.query.template
  setOriginal()
})
</script>

<template>
  <!-- Template Create Warning -->
  <TemplateCreateWarning
    v-model="showCreateWarning"
    :scrollable="true"
    @confirmed="submit"
  />

  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiVectorArrangeAbove"
        :title="
          $t('common.createTitle', {
            entity: $t('objectTypes.template.singular'),
          })
        "
        main
        docs-path="/docs/usage/openvle/vms/templates/"
      />

      <CardBox is-form @submit.prevent="showCreateWarning = true">
        <!-- Notification: Select vm -->
        <NotificationBar
          v-if="!showDetail"
          :dismissable="false"
          color="info"
          :icon="mdiInformation"
        >
          <p>
            <b>{{ $t('views.templates.create.selectSourceVm') }}</b>
          </p>
        </NotificationBar>

        <!-- Notification: VM selected, enter os -->
        <NotificationBar
          v-if="showDetail && vmClonable"
          :dismissable="false"
          color="success"
          :icon="mdiInformation"
        >
          <p>
            <b>
              {{ $t('views.templates.create.valuesPrefilledInfo') }}
            </b>
          </p>
        </NotificationBar>

        <!-- Notification: VM not stopped -->
        <NotificationBar
          v-if="showDetail && !vmClonable && template.statusSourceVM"
          :dismissable="false"
          color="danger"
          :icon="mdiAlert"
        >
          <p>
            <b>
              {{
                $t('views.templates.create.vmNotStopped', {
                  status: template?.statusSourceVM,
                })
              }}
              <br />
              {{ $t('views.templates.create.vmMustBeStopped') }}
            </b>
          </p>

          <br />

          <BaseButton
            :icon="mdiEye"
            color="contrast"
            :label="$t('views.templates.create.showVm')"
            outline
            @click="router.push({ path: `/vms/${template.source_vm}` })"
          />
        </NotificationBar>

        <BaseDivider />

        <FormField
          :label="$t('views.templates.create.sourceVm')"
          :help="$t('views.templates.create.sourceVmHelp')"
        >
          <SearchControl
            v-model="template.source_vm"
            :icon="mdiMonitor"
            :fetch-data="backend.vms.search"
            :fetch-selected="backend.vms.getName"
            required
            :autofocus="true"
            @input-started="onVMSearchStarted"
          />
        </FormField>

        <BaseDivider />

        <div v-if="showDetail && vmClonable">
          <FormField
            :label="$t('common.name')"
            :help="$t('views.templates.form.nameHelp')"
          >
            <FormControl
              v-model="template.name"
              :icon="mdiRename"
              :placeholder="$t('views.templates.form.namePlaceholder')"
              :maxlength="FIELD_LIMITS.template.name"
              required
            />
          </FormField>

          <BaseDivider />

          <FormField>
            <FormField
              :label="$t('views.templates.form.cpuCores')"
              :help="$t('views.templates.form.cpuCoresHelp')"
            >
              <FormControl
                v-model="template.cpu"
                type="range"
                placeholder="2"
                :min="1"
                :max="12"
                :step="1"
                required
              />
            </FormField>

            <FormField
              :label="$t('views.templates.form.ram')"
              :help="$t('views.templates.form.ramHelp')"
            >
              <FormControl
                v-model="template.ram"
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
            :help="$t('views.templates.form.descriptionHelp')"
            :tooltip="
              $t('common.maxChars', { max: FIELD_LIMITS.template.description })
            "
          />

          <BaseMarkdown
            v-model="template.description"
            action="edit"
            :maxlength="FIELD_LIMITS.template.description"
          />

          <BaseDivider />
        </div>

        <template #footer>
          <BaseButtons>
            <BaseButton
              type="submit"
              color="info"
              :label="$t('common.add')"
              :disabled="!vmClonable"
            />

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
