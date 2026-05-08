<script setup>
import {
  mdiAccountMultipleOutline,
  mdiAccountOutline,
  mdiCloudSyncOutline,
  mdiDelete,
  mdiInformation,
  mdiLink,
  mdiPencil,
  mdiPlus,
  mdiRename,
  mdiTextBox,
} from '@mdi/js'
import { computed, onMounted, ref, watch } from 'vue'
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
import CardBoxDeleteRelationModal from '@/components/CardBoxDeleteRelationModal.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import ObjectMetadataDisplay from '@/components/ObjectMetadataDisplay.vue'
import PillTag from '@/components/PillTag.vue'
import SearchModal from '@/components/SearchModal.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import TableChangelogs from '@/components/Tables/TableChangelogs.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { formatDate } from '@/utils/dataUtils'
import {
  checkObjectPermissions,
  resolveFieldFromLookup,
  usePermissionRefs,
} from '@/utils/dataUtils'
import { scimEnabledIcon } from '@/utils/icons'
import { statusColorScimEnabled } from '@/utils/objectColors'
import { usePaginationChild } from '@/utils/pagination'

const permissionRefs = usePermissionRefs()

const modals = {
  addRole: ref(false),
  deleteClient: ref(false),
  deleteRoles: ref(false),
}
const dataLoading = ref(true)
const objectModel = 'ScimClient'
const objToRemove = ref({})
const client = ref({})
const clientRoles = ref([])
const roleMappings = ref([])
const userMappings = ref([])
const router = useRouter()
const route = useRoute()
const toast = useToast()
const { t } = useI18n()
const permissionsLoaded = ref(false)

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
      name: 'roles',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'name',
      sortDirection: 'asc',
      fetchData: fetchClientRoles,
    },
    {
      name: 'roleMappings',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'last_synced_at',
      sortDirection: 'desc',
      fetchData: fetchRoleMappings,
    },
    {
      name: 'userMappings',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'last_synced_at',
      sortDirection: 'desc',
      fetchData: fetchUserMappings,
    },
  ],
  fetchArgs: () => [route.params.id],
  modals,
  objToRemove,
})
/**/

async function addRole(roleKey) {
  try {
    await backend.scimClients.addRoles(route.params.id, [{ key: roleKey }])
    fetchClient(route.params.id)
    toast.success(t('views.scimClients.detail.roleAdded'))
  } catch (error) {
    toast.error(
      t('common.addError', { entity: t('objectTypes.role.singular') }),
    )
  }
}

async function deleteClient(id) {
  try {
    await backend.scimClients.delete(id)
    router.push({ path: `/scim/clients` })
    toast.success(t('views.scimClients.detail.scimClientDeleted'))
  } catch (error) {
    toast.error(
      t('common.deleteError', { entity: t('objectTypes.scimClient.singular') }),
    )
  }
}

async function deleteRole(roleKey) {
  try {
    const newRoles = client.value.roles.filter((role) => role.key !== roleKey)
    await backend.scimClients.updateRoles(route.params.id, newRoles)
    fetchClient(route.params.id)
    toast.success(t('views.scimClients.detail.roleRemoved'))
  } catch (error) {
    toast.error(
      t('common.removeError', { entity: t('objectTypes.role.singular') }),
    )
  }
}

async function fetchClient(id) {
  try {
    dataLoading.value = true

    const response = await backend.scimClients.get(id)
    client.value = response
    clientRoles.value = response.roles || []

    await resolveFieldFromLookup(client.value, [
      { from: 'createdById', to: 'createdBy', keyspace: 'users' },
      { from: 'updatedById', to: 'updatedBy', keyspace: 'users' },
    ])
  } catch (error) {
    toast.warning(
      t('common.notFound', { entity: t('objectTypes.scimClient.singular') }),
    )
    router.push({ path: `/scim/clients`, replace: true })
  } finally {
    dataLoading.value = false
  }
}

async function fetchClientRoles() {
  // Roles are embedded in the client object
  clientRoles.value = client.value.roles || []
}

async function fetchRoleMappings() {
  try {
    dataLoading.value = true

    const mappingsChild = childComponents.value.find(
      (component) => component.name === 'roleMappings',
    )

    const response = await backend.scimClients.getRoleMappings(
      route.params.id,
      {
        page: mappingsChild?.currentPage,
        limit: mappingsChild?.perPage,
        sort_by: mappingsChild?.sortColumnKey,
        sort_order: mappingsChild?.sortDirection,
      },
    )
    roleMappings.value = response.items
    roleMappings.value.count = response.pageDetails.totalCount
  } catch (error) {
    toast.warning(t('common.loadErrorPlural', { entities: 'Role-Mappings' }))
  } finally {
    dataLoading.value = false
  }
}

async function fetchUserMappings() {
  try {
    dataLoading.value = true

    const mappingsChild = childComponents.value.find(
      (component) => component.name === 'userMappings',
    )

    const response = await backend.scimClients.getUserMappings(
      route.params.id,
      {
        page: mappingsChild?.currentPage,
        limit: mappingsChild?.perPage,
        sort_by: mappingsChild?.sortColumnKey,
        sort_order: mappingsChild?.sortDirection,
      },
    )
    userMappings.value = response.items
    userMappings.value.count = response.pageDetails.totalCount
  } catch (error) {
    toast.warning(t('common.loadErrorPlural', { entities: 'User-Mappings' }))
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

const clientEdit = (id) => {
  router.push({ path: `${id}/edit` })
}

const viewUser = (obj, model) => {
  return router.push({ path: `/users/${obj.user_id}` })
}

const viewRole = async (obj, model) => {
  const test = await backend.roles.list({
    search_field: 'key',
    search_value: obj.key,
  })
  if (test?.items[0]?.id)
    return router.push({ path: `/roles/${test.items[0].id}` })
  return null
}

const syncGroupsText = computed(() => {
  return client.value.sync_groups ? 'Ja' : 'Nein'
})

async function loadClientAndPermissions(id) {
  await fetchClient(id)

  await checkObjectPermissions(
    'scim_clients',
    id,
    permissionRefs,
    [
      {
        key: 'canReadChangelogs',
        objectType: 'changelogs',
        objectPermission: 'read',
        objectPath: '/*',
      },
      {
        key: 'canReadUsers',
        objectType: 'users',
        objectPermission: 'read',
        objectPath: '/*',
      },
      {
        key: 'canReadRoles',
        objectType: 'roles',
        objectPermission: 'read',
        objectPath: '/*',
      },
    ],
    ['canCreate', 'canEdit', 'canDelete'],
  )
}

onMounted(async () => {
  await loadClientAndPermissions(route.params.id)
  permissionsLoaded.value = true
})

watch(
  () => route.params.id,
  async (newId, oldId) => {
    if (!newId || newId === oldId) return

    dataLoading.value = true
    permissionsLoaded.value = false

    loadedTabs.clear()
    childComponents.value.forEach((component) => {
      component.currentPage = 1
    })

    try {
      await loadClientAndPermissions(newId)
    } finally {
      permissionsLoaded.value = true
      dataLoading.value = false
    }
  },
)
</script>

<template>
  <!-- Modal: Add role -->
  <SearchModal
    v-model="modals.addRole.value"
    :fetch-data="backend.roles.search"
    :icon="mdiAccountMultipleOutline"
    :label="$t('views.scimClients.detail.searchExistingRole')"
    :title="$t('views.scimClients.detail.roleAssign')"
    return-attribute="key"
    @submitted="addRole"
  />

  <!-- Modal: Delete client -->
  <CardBoxDeleteModal
    v-model="modals.deleteClient.value"
    :name="client.name"
    :checkvalue="client.name"
    @form-submitted="deleteClient(client.id)"
  />

  <!-- Modal: Delete role from client -->
  <CardBoxDeleteRelationModal
    v-model="modals.deleteRoles.value"
    :parent-object="client.name"
    :related-object="objToRemove.name"
    checkvalue="Bestätigung"
    @form-submitted="deleteRole(objToRemove.key)"
  />

  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiCloudSyncOutline"
        :title="client.name ? client.name : 'Loading...'"
        object-model="SCIM Client"
        main
      >
        <BaseButtons type="justify-start lg:justify-end">
          <PillTag
            v-if="client.id"
            disabled
            :label="client.enabled ? 'Aktiv' : 'Inaktiv'"
            :color="statusColorScimEnabled(client.enabled)"
            :icon="scimEnabledIcon(client.enabled)"
          />

          <BaseButton
            v-if="permissionRefs.canEdit"
            target="_blank"
            :icon="mdiPencil"
            :label="$t('common.edit')"
            color="contrast"
            rounded-full
            small
            @click="clientEdit(client.id)"
          />

          <BaseButton
            v-if="permissionRefs.canDelete"
            target="_blank"
            :icon="mdiDelete"
            :label="$t('common.delete')"
            color="danger"
            rounded-full
            small
            @click="showModal('deleteClient', client.id)"
          />
        </BaseButtons>
      </SectionTitleLineWithButton>

      <CardBox>
        <BaseTabs v-if="permissionsLoaded" @tab-changed="handleTabChanged">
          <BaseTab id="client" :title="$t('views.scimClients.detail.client')">
            <FormField
              :label="$t('common.name')"
              :help="$t('views.scimClients.detail.nameHelp')"
            >
              <FormControl v-model="client.name" :icon="mdiRename" disabled />
            </FormField>

            <FormField
              :label="$t('common.description')"
              :help="$t('views.scimClients.detail.descriptionHelp')"
            >
              <FormControl
                v-model="client.description"
                :icon="mdiTextBox"
                disabled
              />
            </FormField>

            <FormField
              :label="$t('views.scimClients.detail.endpointUrl')"
              :help="$t('views.scimClients.detail.endpointUrlHelp')"
            >
              <FormControl
                v-model="client.endpoint_url"
                :icon="mdiLink"
                disabled
              />
            </FormField>

            <FormField
              :label="$t('views.scimClients.detail.roleGroupSync')"
              :help="$t('views.scimClients.detail.syncRolesAsGroupsHelp')"
            >
              <FormControl
                :model-value="syncGroupsText"
                :icon="mdiAccountMultipleOutline"
                disabled
              />
            </FormField>

            <ObjectMetadataDisplay
              v-if="loadedTabs.has('client') && client.id"
              :object="client"
              :object-type="objectModel"
              :object-id="route.params.id"
              :show-tags="false"
            />
          </BaseTab>

          <BaseTab id="roles" :title="$t('views.scimClients.detail.roles')">
            <SectionTitleLineWithButton
              :icon="mdiAccountMultipleOutline"
              :title="$t('views.scimClients.detail.assignedRoles')"
            >
              <BaseButton
                v-if="permissionRefs.canEdit"
                :icon="mdiPlus"
                color="success"
                rounded-full
                small
                @click="showModal('addRole')"
              />
            </SectionTitleLineWithButton>

            <NotificationBar
              :dismissable="false"
              color="info"
              :icon="mdiInformation"
            >
              Nur Benutzer mit mindestens einer der zugewiesenen Rollen werden
              zu diesem SCIM Client synchronisiert. Ohne Rollenzuordnung werden
              keine Benutzer synchronisiert.
            </NotificationBar>

            <BaseTable
              v-if="clientRoles"
              :current-page="
                childComponents.find((component) => component.name === 'roles')
                  ?.currentPage
              "
              :per-page="
                childComponents.find((component) => component.name === 'roles')
                  ?.perPage
              "
              :items-total="clientRoles.length"
              :data="clientRoles"
              :sort-column-key="
                childComponents.find((component) => component.name === 'roles')
                  ?.sortColumnKey
              "
              :sort-direction="
                childComponents.find((component) => component.name === 'roles')
                  ?.sortDirection
              "
              :loading="dataLoading"
              object-model="roles"
              :emit-view-object="true"
              :buttons="
                permissionRefs.canReadRoles && permissionRefs.canEdit
                  ? ['view', 'delete']
                  : permissionRefs.canReadRoles
                    ? ['view']
                    : permissionRefs.canEdit
                      ? ['delete']
                      : []
              "
              :pagination="false"
              :created-column-enabled="false"
              :columns="[
                { label: 'Name', key: 'name', width: '300px', sortable: false },
                { label: 'Key', key: 'key', width: '200px', sortable: false },
              ]"
              @delete-object="handleDeleteObject"
              @view-object="viewRole"
            />
          </BaseTab>

          <BaseTab
            id="userMappings"
            :title="$t('views.scimClients.detail.usermappings')"
          >
            <SectionTitleLineWithButton
              :icon="mdiAccountOutline"
              :title="$t('views.scimClients.detail.usermappings')"
              :reload="fetchUserMappings"
            />

            <NotificationBar
              :dismissable="false"
              color="info"
              :icon="mdiInformation"
            >
              User-Mappings zeigen die Zuordnung zwischen lokalen Benutzern und
              deren externen SCIM-IDs im Zielsystem. Sie werden bei der
              Synchronisation automatisch erstellt und verwaltet.
            </NotificationBar>

            <BaseTable
              v-if="userMappings"
              :current-page="
                childComponents.find(
                  (component) => component.name === 'userMappings',
                )?.currentPage
              "
              :per-page="
                childComponents.find(
                  (component) => component.name === 'userMappings',
                )?.perPage
              "
              :items-total="userMappings.count"
              :data="userMappings"
              :sort-column-key="
                childComponents.find(
                  (component) => component.name === 'userMappings',
                )?.sortColumnKey
              "
              :sort-direction="
                childComponents.find(
                  (component) => component.name === 'userMappings',
                )?.sortDirection
              "
              :loading="dataLoading"
              object-model="userMappings"
              :emit-view-object="true"
              :buttons="permissionRefs.canReadUsers ? ['view'] : ['']"
              :columns="[
                {
                  label: 'User ID',
                  key: 'user_id',
                  width: '250px',
                },
                {
                  label: 'Externe SCIM ID',
                  key: 'external_scim_id',
                  width: '290px',
                },
                {
                  label: 'Letzte Synchronisation',
                  key: 'last_synced_at',
                  formatter: (value) => formatDate(value),
                },
              ]"
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
              @view-object="viewUser"
            />
          </BaseTab>

          <BaseTab
            id="roleMappings"
            :title="$t('views.scimClients.detail.rolemappings')"
          >
            <SectionTitleLineWithButton
              :icon="mdiAccountMultipleOutline"
              :title="$t('views.scimClients.detail.rolemappings')"
              :reload="fetchRoleMappings"
            />

            <NotificationBar
              :dismissable="false"
              color="info"
              :icon="mdiInformation"
            >
              Role-Mappings zeigen die Zuordnung zwischen lokalen Rollen und
              deren externen SCIM-IDs im Zielsystem. Sie werden bei der
              Synchronisation automatisch erstellt und verwaltet.
            </NotificationBar>

            <BaseTable
              v-if="roleMappings"
              :current-page="
                childComponents.find(
                  (component) => component.name === 'roleMappings',
                )?.currentPage
              "
              :per-page="
                childComponents.find(
                  (component) => component.name === 'roleMappings',
                )?.perPage
              "
              :items-total="roleMappings.count"
              :data="roleMappings"
              :sort-column-key="
                childComponents.find(
                  (component) => component.name === 'roleMappings',
                )?.sortColumnKey
              "
              :sort-direction="
                childComponents.find(
                  (component) => component.name === 'roleMappings',
                )?.sortDirection
              "
              :loading="dataLoading"
              object-model="roleMappings"
              :emit-view-object="true"
              :buttons="permissionRefs.canReadRoles ? ['view'] : ['']"
              :columns="[
                {
                  label: 'Role ID',
                  key: 'role_id',
                  width: '250px',
                },
                {
                  label: 'Externe SCIM ID',
                  key: 'external_scim_id',
                  width: '290px',
                },
                {
                  label: 'Letzte Synchronisation',
                  key: 'last_synced_at',
                  formatter: (value) => formatDate(value),
                },
              ]"
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
              @view-object="(e) => router.push({ path: `/roles/${e.role_id}` })"
            />
          </BaseTab>

          <BaseTab
            v-if="permissionRefs.canReadChangelogs"
            id="changelogs"
            :title="$t('views.scimClients.detail.changelogs')"
          >
            <TableChangelogs
              v-if="client.id && loadedTabs.has('changelogs')"
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
