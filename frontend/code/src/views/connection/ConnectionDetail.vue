<script setup>
import {
  mdiAccountBox,
  mdiContentCopy,
  mdiDelete,
  mdiInformation,
  mdiKey,
  mdiLabel,
  mdiMonitor,
  mdiNetwork,
  mdiPlus,
  mdiProtocol,
  mdiRemoteDesktop,
  mdiRename,
} from '@mdi/js'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseDivider from '@/components/BaseDivider.vue'
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
import SearchControl from '@/components/SearchControl.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import TablePermissions from '@/components/Tables/TablePermissions.vue'
import { FIELD_LIMITS } from '@/config/fieldLimits'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { useMainStore } from '@/stores/main'
import {
  checkObjectPermissions,
  connectionProfileLabelFormatter,
  resolveFieldFromLookup,
  usePermissionRefs,
} from '@/utils/dataUtils'
import { eventCreateTypeIcon } from '@/utils/icons'
import { createTypeColorConnection } from '@/utils/objectColors'
import { usePaginationChild } from '@/utils/pagination'
import { eventCreateTypeTooltip } from '@/utils/tooltips'
import { useAutofocusInput } from '@/utils/useAutofocusInput'

const permissionRefs = usePermissionRefs()

const modals = {
  addGuacamoles: ref(false),
  deleteConnectionProfile: ref(false),
  deleteGuacamoles: ref(false),
}
const { autoFocusInputRef } = useAutofocusInput(modals.addGuacamoles)
const dataLoading = ref(true)
const objectModel = 'GuacamoleConnectionProfile'
const objToAdd = ref('')
const objToAdd2 = ref('')
const objToRemove = ref({})
const permissionsLoaded = ref(false)
const router = useRouter()
const route = useRoute()
const searchControlUserRef = ref(null)
const toast = useToast()
const { t } = useI18n()
const connection = ref([])

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
      name: 'guacamoles',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'createdAt',
      sortDirection: 'desc',
      fetchData: fetchConnectionGuacamoles,
    },
  ],
  fetchArgs: () => [route.params.id],
  modals,
  objToRemove,
})
/**/

async function addConnection(name, userId) {
  try {
    await backend.guacamole.create({
      name,
      userId,
      connection_profile: connection.value.id,
    })
    toast.success(
      t('common.createSuccess', {
        entity: t('objectTypes.guacamole.singular'),
      }),
    )
    useMainStore().fetchPermissions()
  } catch (error) {
    toast.error(
      `${t('common.createError', { entity: t('objectTypes.guacamole.singular') })}\n${error?.response?.data?.detail}`,
    )
  } finally {
    resetSearchComponent()
    await fetchConnectionGuacamoles()
  }
}

async function deleteConnection(id) {
  try {
    await backend.guacamole.delete(id)
    toast.success(
      t('common.deleteSuccess', {
        entity: t('objectTypes.guacamole.singular'),
      }),
    )
  } catch (error) {
    toast.error(
      `${t('common.deleteError', { entity: t('objectTypes.guacamoleConnectionProfile.singular') })}\n${error?.response?.data?.detail}`,
    )
  } finally {
    resetSearchComponent()
    await fetchConnectionGuacamoles()
  }
}

async function deleteConnectionProfile(id) {
  try {
    await backend.connections.delete(id)
    router.push({ path: `/connections` })
    toast.success(
      t('common.deleteSuccess', {
        entity: t('objectTypes.guacamoleConnectionProfile.singular'),
      }),
    )
  } catch (error) {
    toast.error(
      t('common.deleteError', { entity: t('objectTypes.guacamole.singular') }),
    )
  }
}

async function fetchConnection(id) {
  try {
    dataLoading.value = true

    await backend.connections.get(id).then(async (response) => {
      connection.value = response
      const keyspace =
        connection.value.objectType === 'VirtualMachine' ? 'vms' : 'templates'
      connection.value.objectLink = `/${keyspace}/${connection.value.objectId}`

      await resolveFieldFromLookup(connection.value, [
        { from: 'createdById', to: 'createdBy', keyspace: 'users' },
        { from: 'objectId', to: 'vm', keyspace },
        { from: 'updatedById', to: 'updatedBy', keyspace: 'users' },
      ])

      const objectType =
        connection.value.objectType === 'VirtualMachine'
          ? 'VM'
          : t('views.connections.detail.vmTemplate')

      connection.value.entity = `${connection.value.vm} (${objectType})`
      connection.value.label = connectionProfileLabelFormatter(
        connection.value,
        connection.value.protocol,
        connection.value.username,
        connection.value.vm,
        connection.value.port,
      )
    })
  } catch (error) {
    toast.warning(
      t('common.notFound', { entity: t('objectTypes.guacamole.singular') }),
    )
    router.push({ path: `/connections`, replace: true })
  } finally {
    dataLoading.value = false
  }
}

async function fetchConnectionGuacamoles() {
  try {
    dataLoading.value = true

    await backend.guacamole
      .list({
        page: childComponents.value.find(
          (component) => component.name === 'guacamoles',
        )?.currentPage,
        limit: childComponents.value.find(
          (component) => component.name === 'guacamoles',
        )?.perPage,
        sort_by: childComponents.value.find(
          (component) => component.name === 'guacamoles',
        )?.sortColumnKey,
        sort_order: childComponents.value.find(
          (component) => component.name === 'guacamoles',
        )?.sortDirection,
        search_field: 'connection_profile',
        search_value: route.params.id,
      })
      .then(async (response) => {
        connection.value.guacamoles = response.items
        connection.value.guacamolesCount = response.pageDetails.totalCount

        await resolveFieldFromLookup(connection.value.guacamoles, [
          { from: 'createdById', to: 'createdBy', keyspace: 'users' },
          { from: 'userId', to: 'user', keyspace: 'users' },
          {
            from: 'eventId',
            to: 'event',
            keyspace: 'events',
            formatter: (obj) => ({
              event: obj.event ? obj.event : t('common.manual'),
            }),
          },
        ])
      })
  } catch (error) {
    toast.warning(
      t('common.loadErrorPlural', {
        entities: t('objectTypes.guacamole.plural'),
      }),
    )
  } finally {
    dataLoading.value = false
  }
}

function showModal(modal, item) {
  if (Object.prototype.hasOwnProperty.call(modals, modal)) {
    modals[modal].value = true
  }
  if (item) {
    objToRemove.value = item
  }
}

const cloneConnectionProfile = (connection) => {
  router.push({
    path: `/connections/clone`,
    query: {
      port: connection.port,
      protocol: connection.protocol,
      username: connection.username,
      entityId: connection.objectId,
      entityType: connection.objectType,
      source: connection.id,
    },
  })
}

const resetSearchComponent = () => {
  objToAdd.value = null
  objToAdd2.value = null
  searchControlUserRef.value?.setInitialDisplay('')
  searchControlUserRef.value?.setSelectedId('')
}

const deleteActionDisabled = computed(() => {
  if (connection.value.guacamolesCount === 0) {
    return false
  }
  return true
})

const deleteActionTooltip = computed(() => {
  if (deleteActionDisabled.value == true) {
    return t('views.connections.detail.deleteDisabledTooltip')
  }
  return undefined
})

const buttonsGuacamoles = computed(() => {
  if (permissionRefs.canDeleteGuacamoles) return ['view', 'delete']
  return ['view']
})

onMounted(async () => {
  fetchConnection(route.params.id)
  fetchConnectionGuacamoles()
  await checkObjectPermissions(
    'guacamole_connection_profiles',
    route.params.id,
    permissionRefs,
    [
      {
        key: 'canReadPermissions',
        objectType: 'object_permissions',
        objectPermission: 'read',
        objectPath: `/${route.params.id}`,
      },
      {
        key: 'canReadGuacamoles',
        objectType: 'guacamoles',
        objectPermission: 'read',
        objectPath: '/*',
      },
      {
        key: 'canCreateGuacamoles',
        objectType: 'guacamoles',
        objectPermission: 'create',
        objectPath: '/*',
      },
      {
        key: 'canDeleteGuacamoles',
        objectType: 'guacamoles',
        objectPermission: 'delete',
        objectPath: '/*',
      },
    ],
    ['canCreate', 'canEdit', 'canDelete'],
  )

  permissionsLoaded.value = true
})
</script>

<template>
  <!-- Modal: Add vm guacamole connection profile association -->
  <CardBoxModal
    v-model="modals.addGuacamoles.value"
    form
    :title="$t('views.connections.detail.connectionAdd')"
    button="success"
    has-cancel
    has-search
    button-:label="$t('common.add')"
    @cancel="resetSearchComponent"
    @form-submitted="addConnection(objToAdd, objToAdd2)"
  >
    <FormField
      :label="$t('common.name')"
      :tooltip="t('views.connections.detail.nameTooltip')"
      :help="$t('views.connections.detail.nameHelp')"
    >
      <FormControl
        v-model="objToAdd"
        :icon="mdiRename"
        :maxlength="FIELD_LIMITS.guacamole.name"
        :placeholder="$t('views.connections.detail.namePlaceholder')"
        required
        @set-ref="
          (ref) => {
            autoFocusInputRef = ref
          }
        "
      />
    </FormField>

    <FormField
      :label="$t('views.connections.detail.user')"
      :help="$t('views.connections.detail.selectUserHelp')"
    >
      <SearchControl
        v-model="objToAdd2"
        :icon="mdiAccountBox"
        :fetch-data="backend.users.search"
        :fetch-selected="backend.users.formatById"
        required
        @set-ref="
          (ref) => {
            searchControlUserRef = ref
          }
        "
      />
    </FormField>
  </CardBoxModal>

  <!-- Modal: Delete Connection Profile -->
  <CardBoxDeleteModal
    v-model="modals.deleteConnectionProfile.value"
    :name="connection.label"
    :checkvalue="$t('common.confirm')"
    @form-submitted="deleteConnectionProfile(objToRemove.id)"
  />

  <!-- Modal: Delete Connection -->
  <CardBoxDeleteModal
    v-model="modals.deleteGuacamoles.value"
    :name="objToRemove.name"
    :checkvalue="$t('common.confirm')"
    @form-submitted="deleteConnection(objToRemove.id)"
  />

  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiRemoteDesktop"
        :title="$t('views.connections.detail.connectionTemplate')"
        main
        docs-path="/docs/usage/openvle/connections/"
      >
        <BaseButtons type="justify-start lg:justify-end">
          <BaseButton
            v-if="permissionRefs.canCreate"
            target="_blank"
            :icon="mdiContentCopy"
            :label="$t('views.connections.detail.copy')"
            color="info"
            rounded-full
            small
            @click="cloneConnectionProfile(connection)"
          />

          <BaseButton
            v-if="permissionRefs.canDelete"
            v-tooltip="deleteActionTooltip"
            target="_blank"
            :disabled="deleteActionDisabled"
            :icon="mdiDelete"
            :label="$t('common.delete')"
            color="danger"
            rounded-full
            small
            @click="showModal('deleteConnectionProfile', connection)"
          />
        </BaseButtons>
      </SectionTitleLineWithButton>

      <CardBox>
        <BaseTabs v-if="permissionsLoaded" @tab-changed="handleTabChanged">
          <BaseTab id="infos" :title="$t('views.connections.detail.info')">
            <FormField
              :label="$t('common.label')"
              :tooltip="t('views.connections.detail.labelTooltip')"
              :help="$t('views.connections.detail.uniqueIdentification')"
            >
              <FormControl
                v-model="connection.label"
                :icon="mdiLabel"
                disabled
              />
            </FormField>

            <BaseDivider />

            <FormField
              :label="$t('views.connections.detail.vmOrTemplate')"
              :help="$t('views.connections.detail.assignedVmOrTemplate')"
            >
              <FormControl
                v-model="connection.entity"
                :icon="mdiMonitor"
                :link="connection.objectLink"
                disabled
              />
            </FormField>

            <FormField>
              <FormField
                :label="$t('common.protocol')"
                :help="$t('views.connections.detail.protocolHelp')"
              >
                <FormControl
                  v-model="connection.protocol"
                  :icon="mdiProtocol"
                  disabled
                />
              </FormField>

              <FormField
                :label="$t('common.port')"
                :help="$t('views.connections.detail.portHelp')"
              >
                <FormControl
                  v-model="connection.port"
                  :icon="mdiNetwork"
                  disabled
                />
              </FormField>
            </FormField>

            <FormField>
              <FormField
                :label="$t('common.username')"
                :help="$t('views.connections.detail.usernameHelp')"
              >
                <FormControl
                  v-model="connection.username"
                  :icon="mdiAccountBox"
                  disabled
                />
              </FormField>

              <FormField
                :label="$t('common.password')"
                :help="$t('views.connections.detail.passwordHelp')"
              >
                <FormControl
                  placeholder="***************"
                  :icon="mdiKey"
                  type="password"
                  disabled
                />
              </FormField>
            </FormField>

            <ObjectMetadataDisplay
              v-if="loadedTabs.has('infos') && connection.id"
              :object="connection"
              :object-type="objectModel"
              :object-id="route.params.id"
              :can-edit="permissionRefs.canEdit"
              tags-:help="$t('views.connections.detail.tagsHelp')"
            />
          </BaseTab>

          <BaseTab
            v-if="permissionRefs.canReadGuacamoles"
            id="guacamoles"
            :title="$t('views.connections.detail.connections')"
          >
            <SectionTitleLineWithButton
              :icon="mdiRemoteDesktop"
              :title="$t('views.connections.detail.connections')"
              :reload="fetchConnectionGuacamoles"
            >
              <BaseButton
                v-if="
                  permissionRefs.canCreateGuacamoles &&
                  connection.objectType == 'VirtualMachine'
                "
                :icon="mdiPlus"
                color="success"
                rounded-full
                small
                @click="showModal('addGuacamoles')"
              />
            </SectionTitleLineWithButton>

            <NotificationBar
              v-if="connection.objectType !== 'VirtualMachine'"
              :dismissable="false"
              :icon="mdiInformation"
              color="info"
            >
              <p>
                <b>
                  {{ $t('views.connections.detail.templateNotification') }}
                </b>
              </p>
            </NotificationBar>

            <BaseTable
              v-if="connection.guacamoles"
              :current-page="
                childComponents.find(
                  (component) => component.name === 'guacamoles',
                )?.currentPage
              "
              :per-page="
                childComponents.find(
                  (component) => component.name === 'guacamoles',
                )?.perPage
              "
              :items-total="connection.guacamolesCount"
              :data="connection.guacamoles"
              :sort-column-key="
                childComponents.find(
                  (component) => component.name === 'guacamoles',
                )?.sortColumnKey
              "
              :sort-direction="
                childComponents.find(
                  (component) => component.name === 'guacamoles',
                )?.sortDirection
              "
              :loading="dataLoading"
              object-model="guacamoles"
              :buttons="buttonsGuacamoles"
              :columns="[
                {
                  label: null,
                  key: 'eventId',
                  sortable: false,
                  tooltip: (value) => eventCreateTypeTooltip(value),
                  color: createTypeColorConnection,
                  icon: (value) => eventCreateTypeIcon(value),
                  formatter: ['', ''],
                },
                { key: 'name' },
                {
                  label: $t('common.user'),
                  key: 'user',
                  sortKey: 'userId',
                },
                {
                  label: $t('common.createdBy'),
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
            :title="$t('views.connections.detail.permissions')"
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
