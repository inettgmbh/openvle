<script setup>
import {
  mdiAccountMultipleOutline,
  mdiAccountQuestion,
  mdiCloudLockOutline,
  mdiDelete,
  mdiInformation,
  mdiPencil,
  mdiPlus,
  mdiRefresh,
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
import CardBoxModal from '@/components/CardBoxModal.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import ObjectMetadataDisplay from '@/components/ObjectMetadataDisplay.vue'
import PillTag from '@/components/PillTag.vue'
import ScimTokenModal from '@/components/ScimTokenModal.vue'
import SearchModal from '@/components/SearchModal.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import TableChangelogs from '@/components/Tables/TableChangelogs.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import {
  checkObjectPermissions,
  resolveFieldFromLookup,
  usePermissionRefs,
  userStatusLabel,
} from '@/utils/dataUtils'
import { scimEnabledIcon } from '@/utils/icons'
import { statusColorScimEnabled } from '@/utils/objectColors'
import { usePaginationChild } from '@/utils/pagination'

const permissionRefs = usePermissionRefs()

const modals = {
  addRole: ref(false),
  deleteProvider: ref(false),
  deleteRoles: ref(false),
  rotateToken: ref(false),
}
const dataLoading = ref(true)
const objectModel = 'ScimProvider'
const objToRemove = ref({})
const provider = ref({})
const providerRoles = ref([])
const router = useRouter()
const route = useRoute()
const toast = useToast()
const { t } = useI18n()
const permissionsLoaded = ref(false)
const showTokenModal = ref(false)
const rotatedToken = ref('')

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
      fetchData: fetchProviderRoles,
    },
  ],
  fetchArgs: () => [route.params.id],
  modals,
  objToRemove,
})
/**/

async function addRole(roleKey) {
  try {
    await backend.scimProviders.addRoles(route.params.id, [{ key: roleKey }])
    fetchProvider(route.params.id)
    toast.success(t('views.scimProviders.detail.roleAdded'))
  } catch (error) {
    toast.error(
      t('common.addError', { entity: t('objectTypes.role.singular') }),
    )
  }
}

async function deleteProvider(id) {
  try {
    await backend.scimProviders.delete(id)
    router.push({ path: `/scim/providers` })
    toast.success(t('views.scimProviders.detail.scimProviderDeleted'))
  } catch (error) {
    toast.error(
      t('common.deleteError', {
        entity: t('objectTypes.scimProvider.singular'),
      }),
    )
  }
}

async function deleteRole(roleKey) {
  try {
    const newRoles = provider.value.roles.filter((role) => role.key !== roleKey)
    await backend.scimProviders.updateRoles(route.params.id, newRoles)
    fetchProvider(route.params.id)
    toast.success(t('views.scimProviders.detail.roleRemoved'))
  } catch (error) {
    toast.error(
      t('common.removeError', { entity: t('objectTypes.role.singular') }),
    )
  }
}

async function fetchProvider(id) {
  try {
    dataLoading.value = true

    const response = await backend.scimProviders.get(id)
    provider.value = response
    providerRoles.value = response.roles || []

    await resolveFieldFromLookup(provider.value, [
      { from: 'createdById', to: 'createdBy', keyspace: 'users' },
      { from: 'updatedById', to: 'updatedBy', keyspace: 'users' },
    ])
  } catch (error) {
    toast.warning(
      t('common.notFound', { entity: t('objectTypes.scimProvider.singular') }),
    )
    router.push({ path: `/scim/providers`, replace: true })
  } finally {
    dataLoading.value = false
  }
}

async function fetchProviderRoles() {
  // Roles are embedded in the provider object
  providerRoles.value = provider.value.roles || []
}

async function rotateToken() {
  try {
    const response = await backend.scimProviders.rotateToken(route.params.id)
    if (response.bearer_token) {
      rotatedToken.value = response.bearer_token
      showTokenModal.value = true
    }
    toast.success(t('views.scimProviders.detail.tokenRotated'))
  } catch (error) {
    toast.error(t('views.scimProviders.detail.tokenCouldNotRotated'))
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

const providerEdit = (id) => {
  router.push({ path: `${id}/edit` })
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

async function loadProviderAndPermissions(id) {
  await fetchProvider(id)

  await checkObjectPermissions(
    'scim_providers',
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
  await loadProviderAndPermissions(route.params.id)
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
      await loadProviderAndPermissions(newId)
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
    :label="$t('views.scimProviders.detail.searchExistingRole')"
    :title="$t('views.scimProviders.detail.roleAssign')"
    return-attribute="key"
    @submitted="addRole"
  />

  <!-- Modal: Delete provider -->
  <CardBoxDeleteModal
    v-model="modals.deleteProvider.value"
    :name="provider.name"
    :checkvalue="provider.name"
    @form-submitted="deleteProvider(provider.id)"
  />

  <!-- Modal: Delete role from provider -->
  <CardBoxDeleteRelationModal
    v-model="modals.deleteRoles.value"
    :parent-object="provider.name"
    :related-object="objToRemove.name"
    checkvalue="Bestätigung"
    @form-submitted="deleteRole(objToRemove.key)"
  />

  <!-- Modal: Confirm token rotation -->
  <CardBoxModal
    v-model="modals.rotateToken.value"
    :title="$t('views.scimProviders.detail.tokenRotate')"
    button-:label="$t('views.scimProviders.detail.tokenRotate')"
    button="warning"
    has-cancel
    @form-submitted="rotateToken"
  >
    <p>
      Das bestehende Token wird ungültig und durch ein neues ersetzt. Alle
      Systeme, die das aktuelle Token verwenden, müssen aktualisiert werden.
    </p>
  </CardBoxModal>

  <!-- Modal: Token display -->
  <ScimTokenModal
    :model-value="showTokenModal"
    :token="rotatedToken"
    @update:model-value="showTokenModal = $event"
  />

  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiCloudLockOutline"
        :title="provider.name ? provider.name : 'Loading...'"
        object-model="SCIM Provider"
        main
      >
        <BaseButtons type="justify-start lg:justify-end">
          <PillTag
            v-if="provider.id"
            disabled
            :label="provider.enabled ? 'Aktiv' : 'Inaktiv'"
            :color="statusColorScimEnabled(provider.enabled)"
            :icon="scimEnabledIcon(provider.enabled)"
          />

          <BaseButton
            v-if="permissionRefs.canEdit"
            target="_blank"
            :icon="mdiRefresh"
            :label="$t('views.scimProviders.detail.tokenRotate')"
            color="warning"
            rounded-full
            small
            @click="showModal('rotateToken')"
          />

          <BaseButton
            v-if="permissionRefs.canEdit"
            target="_blank"
            :icon="mdiPencil"
            :label="$t('common.edit')"
            color="contrast"
            rounded-full
            small
            @click="providerEdit(provider.id)"
          />

          <BaseButton
            v-if="permissionRefs.canDelete"
            target="_blank"
            :icon="mdiDelete"
            :label="$t('common.delete')"
            color="danger"
            rounded-full
            small
            @click="showModal('deleteProvider', provider.id)"
          />
        </BaseButtons>
      </SectionTitleLineWithButton>

      <CardBox>
        <BaseTabs v-if="permissionsLoaded" @tab-changed="handleTabChanged">
          <BaseTab
            id="provider"
            :title="$t('views.scimProviders.detail.provider')"
          >
            <FormField
              :label="$t('common.name')"
              :help="$t('views.scimProviders.detail.nameHelp')"
            >
              <FormControl v-model="provider.name" :icon="mdiRename" disabled />
            </FormField>

            <FormField
              :label="$t('common.description')"
              :help="$t('views.scimProviders.detail.descriptionHelp')"
            >
              <FormControl
                v-model="provider.description"
                :icon="mdiTextBox"
                disabled
              />
            </FormField>

            <FormField
              :label="$t('views.scimProviders.detail.defaultUserStatus')"
              :help="$t('views.scimProviders.detail.defaultUserStatusHelp')"
            >
              <FormControl
                :model-value="userStatusLabel(provider.default_user_status)"
                :icon="mdiAccountQuestion"
                disabled
              />
            </FormField>

            <ObjectMetadataDisplay
              v-if="loadedTabs.has('provider') && provider.id"
              :object="provider"
              :object-type="objectModel"
              :object-id="route.params.id"
              :show-tags="false"
            />
          </BaseTab>

          <BaseTab id="roles" :title="$t('views.scimProviders.detail.roles')">
            <SectionTitleLineWithButton
              :icon="mdiAccountMultipleOutline"
              :title="$t('views.scimProviders.detail.assignedRoles')"
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
              Zugewiesene Rollen werden automatisch an Benutzer vergeben, die
              über diesen SCIM Provider provisioniert werden.
            </NotificationBar>

            <BaseTable
              v-if="providerRoles"
              :current-page="
                childComponents.find((component) => component.name === 'roles')
                  ?.currentPage
              "
              :per-page="
                childComponents.find((component) => component.name === 'roles')
                  ?.perPage
              "
              :items-total="providerRoles.length"
              :data="providerRoles"
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
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
              @view-object="viewRole"
            />
          </BaseTab>

          <BaseTab
            v-if="permissionRefs.canReadChangelogs"
            id="changelogs"
            :title="$t('views.scimProviders.detail.changelogs')"
          >
            <TableChangelogs
              v-if="provider.id && loadedTabs.has('changelogs')"
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
