<script setup>
import {
  mdiAccountBox,
  mdiCached,
  mdiCalendarOutline,
  mdiCogRefresh,
  mdiDelete,
  mdiFileTree,
  mdiInformation,
  mdiMonitor,
  mdiOpenInNew,
  mdiRemoteDesktop,
  mdiRename,
} from '@mdi/js'
import { onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseTab from '@/components/BaseTab.vue'
import BaseTable from '@/components/BaseTable.vue'
import BaseTabs from '@/components/BaseTabs.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxDeleteModal from '@/components/CardBoxDeleteModal.vue'
import CardBoxModal from '@/components/CardBoxModal.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import ObjectMetadataDisplay from '@/components/ObjectMetadataDisplay.vue'
import PillTag from '@/components/PillTag.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import TablePermissions from '@/components/Tables/TablePermissions.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { useMainStore } from '@/stores/main'
import {
  buildGuacamoleClientIdentifier,
  checkObjectPermissions,
  resolveFieldFromLookup,
  usePermissionRefs,
} from '@/utils/dataUtils'
import { eventCreateTypeIcon, taskStatusIcon } from '@/utils/icons'
import { statusColorTask } from '@/utils/objectColors'
import { usePaginationChild } from '@/utils/pagination'
import { eventCreateTypeTooltip, taskStatusTooltip } from '@/utils/tooltips'

const permissionRefs = usePermissionRefs()

const modals = {
  deleteGuacamole: ref(false),
  reprovisionGuacamole: ref(false),
  updateGuacamole: ref(false),
}
const dataLoading = ref(true)
const mainStore = useMainStore()
const objectModel = 'Guacamole'
const objToRemove = ref({})
const permissionsLoaded = ref(false)
const router = useRouter()
const route = useRoute()
const toast = useToast()
const { t } = useI18n()
const guacamole = ref({})
const guacamoleTasks = ref([])

/* PAGINATION ONLY */
const {
  childComponents,
  loadedTabs,
  handlePaginationChanged,
  handleSortOrderChanged,
  handleDeleteObject,
  handleTabChanged,
} = usePaginationChild({
  children: [
    {
      name: 'tasks/subtasks',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'createdAt',
      sortDirection: 'desc',
      fetchData: fetchGuacamoleTasks,
    },
  ],
  fetchArgs: () => [route.params.id],
  modals,
  objToRemove,
})
/**/

async function deleteGuacamole(guacamoleId) {
  try {
    await backend.guacamole.delete(guacamoleId)
    router.push({ path: `/guacamoles` })
    toast.success(
      t('common.deleteSuccess', {
        entity: t('objectTypes.guacamole.singular'),
      }),
    )
  } catch (error) {
    toast.error(
      `${t('common.deleteError', { entity: t('objectTypes.guacamole.singular') })}\n${error?.response?.data?.detail}`,
    )
  }
}

async function fetchGuacamole(id) {
  try {
    await backend.guacamole.get(id).then(async (response) => {
      guacamole.value = response
      guacamole.value.vmId = guacamole?.value?.vms[0]?.id
      guacamole.value.vm = guacamole?.value?.vms[0]?.name

      const guacClientId = buildGuacamoleClientIdentifier(
        guacamole.value.identifier,
      )
      guacamole.value.url = `${mainStore.settings?.guacamole?.url?.base}/#/client/${guacClientId}`

      const mappings = [
        { from: 'createdById', to: 'createdBy', keyspace: 'users' },
        guacamole.value.eventId && {
          from: 'eventId',
          to: 'event',
          keyspace: 'events',
        },
        { from: 'updatedById', to: 'updatedBy', keyspace: 'users' },
        { from: 'userId', to: 'user', keyspace: 'users' },
        {
          from: 'connection_profile',
          to: 'connection',
          keyspace: 'connectionProfiles',
        },
      ].filter(Boolean)

      await resolveFieldFromLookup(guacamole.value, mappings)
    })
  } catch (error) {
    toast.warning(
      t('common.notFound', { entity: t('objectTypes.guacamole.singular') }),
    )
    router.push({ path: `/guacamoles`, replace: true })
  } finally {
    dataLoading.value = false
  }
}

async function fetchGuacamoleTasks() {
  try {
    dataLoading.value = true

    await backend.tasks
      .listSubTasks({
        page: childComponents.value.find(
          (component) => component.name === 'tasks/subtasks',
        )?.currentPage,
        limit: childComponents.value.find(
          (component) => component.name === 'tasks/subtasks',
        )?.perPage,
        sort_by: childComponents.value.find(
          (component) => component.name === 'tasks/subtasks',
        )?.sortColumnKey,
        sort_order: childComponents.value.find(
          (component) => component.name === 'tasks/subtasks',
        )?.sortDirection,
        search_field: 'object_id',
        search_value: route.params.id,
      })
      .then(async (response) => {
        guacamoleTasks.value = response.items
        guacamoleTasks.value.count = response.pageDetails.totalCount
        await resolveFieldFromLookup(guacamoleTasks.value, [
          { from: 'createdById', to: 'createdBy', keyspace: 'users' },
        ])
      })
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', { entities: t('objectTypes.task.plural') }),
    )
  } finally {
    dataLoading.value = false
  }
}

const openGuacamole = () => {
  window.open(guacamole.value.url, '_blank', 'noopener')
}

function showModal(modal, item) {
  if (Object.prototype.hasOwnProperty.call(modals, modal)) {
    modals[modal].value = true
  }
  if (item) {
    objToRemove.value = item
  }
}

async function reprovisionGuacamole(guacamole) {
  try {
    await backend.vms.getIPv4(guacamole.vmId)
  } catch {
    // do nothing
  }

  try {
    await backend.guacamole.provision(guacamole.id)
    toast.success(t('views.guacamole.detail.connectionRedeployed'))
  } catch (error) {
    toast.error(
      `${t('views.guacamole.detail.reprovisionError')}\n${error?.response?.data?.detail || t('common.unknownError')}`,
    )
  } finally {
    fetchGuacamole(route.params.id)
    fetchGuacamoleTasks()
  }
}

async function updateGuacamole(vmId) {
  try {
    await backend.vms.getIPv4(vmId)
    toast.success(t('views.guacamole.detail.connectionUpdated'))
  } catch (error) {
    toast.error(
      `${t('common.editError', { entity: t('objectTypes.guacamole.singular') })}\n${error?.response?.data?.detail || t('common.unknownError')}`,
    )
  } finally {
    fetchGuacamole(route.params.id)
    fetchGuacamoleTasks()
  }
}

async function pillClicked() {
  router.push({ path: `/events/${guacamole.value.eventId}` })
}

async function startAutoReload() {
  clearInterval(intervalId)

  const g = guacamole.value
  const shouldReload =
    g?.id && (g.identifier == null || String(g.name).includes('PROV'))

  if (!shouldReload) return

  intervalId = setInterval(async () => {
    await fetchGuacamole(route.params.id)

    const updated = guacamole.value
    const stillValid =
      updated?.id &&
      (updated.identifier == null || String(updated.name).includes('PROV'))

    if (!stillValid) clearInterval(intervalId)
  }, 5000)
}

// TODO KVS-435
let intervalId

onMounted(async () => {
  await fetchGuacamole(route.params.id)
  startAutoReload()

  await checkObjectPermissions(
    'guacamoles',
    route.params.id,
    permissionRefs,
    [
      {
        key: 'canReadSubTasks',
        objectType: 'sub_tasks',
        objectPermission: 'read',
        objectPath: '/*',
      },
      {
        key: 'canReadVM',
        objectType: 'vms',
        objectPermission: 'read',
        objectPath: `/${guacamole?.value?.vmId || '*'}`,
      },
      {
        key: 'canReadPermissions',
        objectType: 'object_permissions',
        objectPermission: 'read',
        objectPath: `/${route.params.id}`,
      },
    ],
    ['canCreate', 'canDelete'],
  )

  permissionsLoaded.value = true
})

onUnmounted(() => {
  clearInterval(intervalId)
})
</script>

<template>
  <!-- Modal: Update Guacamole-->
  <CardBoxModal
    v-model="modals.updateGuacamole.value"
    form
    :title="$t('views.guacamole.detail.updateConnection')"
    button="success"
    has-cancel
    button-:label="$t('common.refresh')"
    @form-submitted="updateGuacamole(guacamole.vmId)"
  >
    <NotificationBar :dismissable="false" color="info" :icon="mdiInformation">
      <p>
        {{ $t('views.guacamole.detail.updateModalText') }}
      </p>
    </NotificationBar>
  </CardBoxModal>

  <!-- Modal: Reprovision Guacamole-->
  <CardBoxModal
    v-model="modals.reprovisionGuacamole.value"
    form
    :title="$t('views.guacamole.detail.redeployConnection')"
    button="success"
    has-cancel
    button-:label="$t('views.guacamole.detail.reprovision')"
    @form-submitted="reprovisionGuacamole(guacamole)"
  >
    <NotificationBar :dismissable="false" color="info" :icon="mdiInformation">
      <p>
        {{ $t('views.guacamole.detail.reprovisionModalText') }}
      </p>
    </NotificationBar>
  </CardBoxModal>

  <!-- Modal: Delete Guacamole -->
  <CardBoxDeleteModal
    v-model="modals.deleteGuacamole.value"
    :name="guacamole.name"
    :checkvalue="guacamole.name"
    @form-submitted="deleteGuacamole(guacamole.id)"
  />

  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiRemoteDesktop"
        :title="guacamole.name ? guacamole.name : 'Loading...'"
        :object-model="$t('objectTypes.guacamole.singular')"
        main
        docs-path="/docs/usage/openvle/connections/"
      >
        <PillTag
          v-tooltip="eventCreateTypeTooltip(guacamole.eventId)"
          :color="guacamole.eventId ? 'success' : 'info'"
          :disabled="guacamole.eventId ? false : true"
          :label="guacamole.eventId ? $t('common.event') : $t('common.manual')"
          :icon="eventCreateTypeIcon(guacamole.eventId)"
          :handle-click="pillClicked"
        />

        <BaseButtons type="justify-start lg:justify-end">
          <BaseButton
            v-if="
              guacamole.name &&
              permissionRefs.canReadVM &&
              guacamole.identifier != null &&
              !String(guacamole.name).includes('PROV') &&
              guacamole.userId == mainStore.user?.id
            "
            v-tooltip="$t('views.guacamole.detail.openTooltip')"
            target="_blank"
            :icon="mdiOpenInNew"
            :label="$t('views.guacamole.detail.open')"
            color="info"
            rounded-full
            small
            @click="openGuacamole"
          />

          <BaseButton
            v-if="
              guacamole.name &&
              permissionRefs.canReadVM &&
              guacamole.identifier != null &&
              !String(guacamole.name).includes('PROV')
            "
            target="_blank"
            :icon="mdiCogRefresh"
            :label="$t('common.refresh')"
            color="warning"
            rounded-full
            small
            @click="showModal('updateGuacamole', guacamole.id)"
          />

          <BaseButton
            v-if="
              guacamole.name &&
              permissionRefs.canCreate &&
              guacamole.identifier == null &&
              !String(guacamole.name).includes('PROV')
            "
            target="_blank"
            :icon="mdiCogRefresh"
            :label="$t('views.guacamole.detail.reprovision')"
            color="warning"
            rounded-full
            small
            @click="showModal('reprovisionGuacamole', guacamole.id)"
          />

          <BaseButton
            v-if="permissionRefs.canDelete"
            target="_blank"
            :icon="mdiDelete"
            :label="$t('common.delete')"
            color="danger"
            rounded-full
            small
            @click="showModal('deleteGuacamole', guacamole.id)"
          />
        </BaseButtons>
      </SectionTitleLineWithButton>

      <CardBox>
        <BaseTabs v-if="permissionsLoaded" @tab-changed="handleTabChanged">
          <BaseTab id="infos" :title="$t('views.guacamole.detail.info')">
            <FormField
              :label="$t('common.name')"
              :help="$t('views.guacamole.detail.nameHelp')"
            >
              <FormControl
                v-model="guacamole.name"
                :icon="mdiRename"
                disabled
              />
            </FormField>

            <FormField>
              <FormField
                :label="$t('views.guacamole.detail.user')"
                :help="$t('views.guacamole.detail.userHelp')"
              >
                <FormControl
                  v-model="guacamole.user"
                  :icon="mdiAccountBox"
                  :link="`/users/${guacamole.userId}`"
                  disabled
                />
              </FormField>

              <FormField
                :label="$t('views.guacamole.detail.vm')"
                :help="$t('views.guacamole.detail.vmHelp')"
              >
                <FormControl
                  v-model="guacamole.vm"
                  :icon="mdiMonitor"
                  :link="`/vms/${guacamole.vmId}`"
                  disabled
                />
              </FormField>
            </FormField>

            <FormField
              :label="$t('views.guacamole.detail.connectionTemplate')"
              :help="$t('views.guacamole.detail.connectionTemplateHelp')"
            >
              <FormControl
                v-model="guacamole.connection"
                :icon="mdiCached"
                :link="`/connections/${guacamole.connection_profile}`"
                disabled
              />
            </FormField>

            <FormField
              v-if="guacamole.eventId"
              :label="$t('views.guacamole.detail.event')"
              :help="$t('views.guacamole.detail.eventHelp')"
            >
              <FormControl
                v-model="guacamole.event"
                :icon="mdiCalendarOutline"
                :link="`/events/${guacamole.eventId}`"
                disabled
              />
            </FormField>

            <ObjectMetadataDisplay
              v-if="guacamole.id"
              :object="guacamole"
              :object-type="objectModel"
              :object-id="route.params.id"
              :can-edit="permissionRefs.canEdit"
              tags-:help="$t('views.guacamole.detail.tagsHelp')"
            />
          </BaseTab>

          <BaseTab
            v-if="permissionRefs.canReadSubTasks"
            id="tasks/subtasks"
            :title="$t('objectTypes.task.plural')"
          >
            <SectionTitleLineWithButton
              :icon="mdiFileTree"
              :title="$t('objectTypes.task.plural')"
              :reload="fetchGuacamoleTasks"
            >
            </SectionTitleLineWithButton>

            <BaseTable
              :current-page="
                childComponents.find(
                  (component) => component.name === 'tasks/subtasks',
                )?.currentPage
              "
              :per-page="
                childComponents.find(
                  (component) => component.name === 'tasks/subtasks',
                )?.perPage
              "
              :items-total="guacamoleTasks.count"
              :data="guacamoleTasks"
              :sort-column-key="
                childComponents.find(
                  (component) => component.name === 'tasks/subtasks',
                )?.sortColumnKey
              "
              :sort-direction="
                childComponents.find(
                  (component) => component.name === 'tasks/subtasks',
                )?.sortDirection
              "
              :loading="dataLoading"
              object-model="tasks/subtasks"
              :buttons="['view']"
              :columns="[
                { key: 'name' },
                {
                  key: 'status',
                  color: statusColorTask,
                  icon: (value) => taskStatusIcon(value),
                  tooltip: (value) => taskStatusTooltip(value),
                  formatter: ['', ''],
                },
                {
                  label: $t('common.triggeredBy'),
                  key: 'createdBy',
                  sortKey: 'createdById',
                },
              ]"
              @delete-object="handleDeleteObject"
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
            />
          </BaseTab>

          <BaseTab
            v-if="permissionRefs.canReadPermissions"
            id="permissions"
            :title="$t('views.guacamole.detail.permissions')"
          >
            <TablePermissions
              v-if="loadedTabs.has('permissions')"
              :object-id="route.params.id"
              :object-type="objectModel"
              :per-page="10"
            />
          </BaseTab>
        </BaseTabs>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
