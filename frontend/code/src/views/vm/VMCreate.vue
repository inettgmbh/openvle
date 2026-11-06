<script setup>
import {
  mdiAlertCircle,
  mdiInformation,
  mdiMonitor,
  mdiNumeric,
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
import FormCheckRadio from '@/components/FormCheckRadio.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import SearchControl from '@/components/SearchControl.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import UnsavedChangesModal from '@/components/UnsavedChangesModal.vue'
import { useUnsavedChanges } from '@/composables/useUnsavedChanges'
import { FIELD_LIMITS } from '@/config/fieldLimits'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import router from '@/router'
import backend from '@/services'
import { useMainStore } from '@/stores/main'
import { checkObjectPermissions, usePermissionRefs } from '@/utils/dataUtils'

const { t } = useI18n()
const permissionRefs = usePermissionRefs()
const route = useRoute()
const toast = useToast()

const detailsLoaded = ref(false)
const permissionsLoaded = ref(false)
const connectionsFound = ref('init')
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

async function createVM() {
  try {
    const res = await backend.vms.create({
      name: vm.value.name,
      description: vm.value.description,
      cpu: vm.value.cpu,
      ram: vm.value.ram * 1024,
      template: vm.value.template,
      createConnection: vm.value.createConnection,
    })
    toast.success(
      t('common.createSuccess', {
        entity: t('objectTypes.virtualMachine.singular'),
      }),
    )
    useMainStore().fetchPermissions()
    markAsSaved()
    router.push({ path: `/vms/${res.id}` })
  } catch (error) {
    toast.error(
      t('common.createError', {
        entity: t('objectTypes.virtualMachine.singular'),
      }),
    )
  }
}

async function fetchTemplate(templateId) {
  try {
    await backend.templates.get(templateId).then(async (response) => {
      vm.value.description = response.description
      vm.value.templateName = response.name
      vm.value.cpu = response.cpu
      vm.value.ram = response.ram / 1024
      vm.value.templateProxmoxID = response.proxmoxId
      vm.value.createConnection = false
      detailsLoaded.value = true
    })
  } catch (error) {
    toast.warning(t('views.vms.create.templateNotFound'))
  }
}

const showDetail = computed(() => {
  return vm.value.template ? true : false
})

const createDisabled = computed(() => {
  return !vm.value.templateProxmoxID && vm.value.template ? true : false
})

function onTemplateSearchStarted() {
  if (vm.value.template) {
    vm.value.template = null
    vm.value.description = ''
    vm.value.templateName = ''
    vm.value.cpu = undefined
    vm.value.ram = undefined
  }
}

async function fetchTemplateConnections(templateId) {
  try {
    await backend.connections
      .listByObject('Template', templateId, {
        page: 1,
        limit: 100,
        sort_by: 'createdAt',
        sort_order: 'desc',
      })
      .then((response) => {
        if (response.items.length > 0) {
          connectionsFound.value = 'yes'
        } else {
          connectionsFound.value = 'no'
        }
      })
  } catch (error) {
    connectionsFound.value = 'no'
    toast.error(
      t('common.loadErrorPlural', {
        entities: t('objectTypes.guacamoleConnectionProfile.plural'),
      }),
    )
  }
}

async function handleGuacamole(templateID) {
  if (permissionRefs.canReadConnections && vm.value.template) {
    await fetchTemplateConnections(templateID)
  } else {
    connectionsFound.value = 'no-permission'
  }
}

watch(
  () => vm.value.template,
  async (newTemplate) => {
    if (newTemplate) {
      await fetchTemplate(newTemplate)
      await handleGuacamole(newTemplate)
    }
  },
  { immediate: true },
)

function onCancel() {
  if (handleCancel()) router.back()
}

onMounted(async () => {
  vm.value.cpu = route.query.cpu
  vm.value.description = route.query.description
  vm.value.name = route.query.name
  vm.value.ram = route.query.ram / 1024
  vm.value.template = route.query.template
  setOriginal()

  await checkObjectPermissions('vms', route.params.id, permissionRefs, [
    {
      key: 'canReadConnections',
      objectType: 'guacamole_connection_profiles',
      objectPermission: 'read',
      objectPath: '/',
    },
  ])

  permissionsLoaded.value = true
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiMonitor"
        :title="
          $t('common.createTitle', {
            entity: $t('objectTypes.virtualMachine.singular'),
          })
        "
        main
        docs-path="/docs/usage/openvle/vms/"
      />

      <CardBox is-form @submit.prevent="createVM">
        <NotificationBar
          v-if="!showDetail && !createDisabled"
          :dismissable="false"
          color="info"
          :icon="mdiInformation"
        >
          <p>
            <b>{{ $t('views.vms.create.selectTemplateFirst') }}</b>
          </p>
        </NotificationBar>

        <NotificationBar
          v-if="showDetail && !createDisabled && detailsLoaded"
          :dismissable="false"
          color="success"
          :icon="mdiInformation"
        >
          <p>
            <b>{{ $t('views.vms.create.valuesPrefilled') }}</b>
          </p>
        </NotificationBar>

        <NotificationBar
          v-if="createDisabled && detailsLoaded"
          :dismissable="false"
          color="danger"
          :icon="mdiAlertCircle"
        >
          <p>
            <b>{{ $t('views.vms.create.templateNotFoundOnProxmox') }}</b>
          </p>
        </NotificationBar>

        <BaseDivider />

        <FormField
          :label="$t('views.vms.create.templateLabel')"
          :help="$t('views.vms.create.templateHelp')"
        >
          <SearchControl
            v-model="vm.template"
            :icon="mdiVectorArrangeAbove"
            :fetch-data="backend.templates.search"
            :fetch-selected="backend.templates.getName"
            :autofocus="true"
            required
            @input-started="onTemplateSearchStarted"
          />
        </FormField>

        <BaseDivider />

        <div v-if="showDetail">
          <FormField
            :label="$t('common.name')"
            :help="$t('views.vms.nameHelp')"
          >
            <FormControl
              v-model="vm.name"
              :icon="mdiRename"
              :placeholder="$t('views.vms.namePlaceholder')"
              :maxlength="FIELD_LIMITS.vm.name"
              required
            />
          </FormField>

          <BaseDivider />

          <FormField>
            <FormField
              :label="$t('views.vms.cpuCoresLabel')"
              :help="$t('views.vms.cpuCoresHelp')"
            >
              <FormControl
                v-model="vm.cpu"
                type="range"
                placeholder="2"
                :min="1"
                :max="12"
                :step="1"
                required
              />
            </FormField>

            <FormField
              :label="$t('views.vms.ramLabel')"
              :help="$t('views.vms.ramHelp')"
            >
              <FormControl
                v-model="vm.ram"
                :icon="mdiNumeric"
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
            :tooltip="
              $t('common.maxChars', { max: FIELD_LIMITS.vm.description })
            "
          />

          <BaseMarkdown
            v-model="vm.description"
            action="edit"
            :maxlength="FIELD_LIMITS.vm.description"
          />

          <BaseDivider />

          <div v-if="connectionsFound != 'init'">
            <FormField
              :label="$t('views.vms.create.connectionsLabel')"
              :help="$t('views.vms.create.connectionsHelp')"
            />

            <div v-if="connectionsFound == 'no-permission'">
              <NotificationBar
                :dismissable="false"
                color="warning"
                :icon="mdiInformation"
              >
                <p>
                  {{ $t('views.vms.create.noConnectionPermission') }}
                </p>
              </NotificationBar>
            </div>

            <div v-if="connectionsFound == 'no'">
              <NotificationBar
                :dismissable="false"
                color="warning"
                :icon="mdiInformation"
              >
                <p>
                  {{ $t('views.vms.create.noConnectionTemplate') }}
                </p>
              </NotificationBar>
            </div>

            <div v-if="connectionsFound == 'yes'">
              <NotificationBar
                :dismissable="false"
                color="info"
                :icon="mdiInformation"
              >
                <p>
                  {{ $t('views.vms.create.connectionTemplateFound') }}
                </p>
              </NotificationBar>
            </div>

            <div
              v-if="
                connectionsFound == 'yes' || connectionsFound == 'no-permission'
              "
              class="pt-5"
            >
              <FormCheckRadio
                v-model="vm.createConnection"
                name="createConnection"
                :label="$t('views.vms.create.autoCreateConnections')"
                type="checkbox"
              />
            </div>

            <BaseDivider />
          </div>
        </div>

        <template #footer>
          <BaseButtons>
            <BaseButton
              type="submit"
              color="info"
              :label="$t('common.add')"
              :disabled="createDisabled || !detailsLoaded"
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
