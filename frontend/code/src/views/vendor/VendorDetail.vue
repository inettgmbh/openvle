<script setup>
import {
  mdiApplicationBrackets,
  mdiApps,
  mdiDelete,
  mdiDomain,
  mdiPencil,
  mdiPlus,
  mdiRename,
  mdiTextBox,
} from '@mdi/js'
import { onMounted, ref } from 'vue'
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
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import ObjectMetadataDisplay from '@/components/ObjectMetadataDisplay.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import {
  applicationSearchBarFields,
  osSearchBarFields,
} from '@/components/Tables/searchBarFieldConfigs'
import TableChangelogs from '@/components/Tables/TableChangelogs.vue'
import TablePermissions from '@/components/Tables/TablePermissions.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import {
  checkObjectPermissions,
  resolveFieldFromLookup,
  usePermissionRefs,
} from '@/utils/dataUtils'
import { usePaginationChild } from '@/utils/pagination'

const { t } = useI18n()
const permissionRefs = usePermissionRefs()

const modals = {
  addApplications: ref(false),
  addOS: ref(false),
  deleteApplications: ref(false),
  deleteOs: ref(false),
  deleteVendors: ref(false),
}
const dataLoading = ref(true)
const objectModel = 'Vendor'
const objToRemove = ref({})
const permissionsLoaded = ref(false)
const router = useRouter()
const route = useRoute()
const toast = useToast()
const vendor = ref([])

/* PAGINATION ONLY */
const {
  childComponents,
  loadedTabs,
  handlePaginationChanged,
  handleSortOrderChanged,
  handleDeleteObject,
  handleSearch,
  handleTabChanged,
} = usePaginationChild({
  children: [
    {
      name: 'applications',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'name',
      sortDirection: 'asc',
      searchField: null,
      searchValue: null,
      fetchData: fetchVendorApplications,
    },
    {
      name: 'os',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'name',
      sortDirection: 'asc',
      searchField: null,
      searchValue: null,
      fetchData: fetchVendorOSs,
    },
  ],
  fetchArgs: () => [route.params.id],
  modals,
  objToRemove,
  route,
})
/**/

const applicationFields = applicationSearchBarFields({ exclude: ['vendor'] })
const osFields = osSearchBarFields({ exclude: ['vendor'] })

async function deleteApplication(appId) {
  try {
    await backend.applications.delete(appId)
    fetchVendorApplications()
    toast.success(t('views.vendors.detail.applicationDeleted'))
  } catch (error) {
    toast.error(
      `${t('common.deleteError', { entity: t('objectTypes.application.singular') })}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  }
}

async function deleteOS(osId) {
  try {
    await backend.os.delete(osId)
    fetchVendorOSs()
    toast.success(t('views.vendors.detail.osDeleted'))
  } catch (error) {
    toast.error(
      `${t('common.deleteError', { entity: t('objectTypes.os.singular') })}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  }
}

async function deleteVendor(vendorId) {
  try {
    await backend.vendors.delete(vendorId)
    router.push({ path: `/vendors` })
    toast.success(
      t('common.deleteSuccess', { entity: t('objectTypes.vendor.singular') }),
    )
  } catch (error) {
    toast.error(
      `${t('common.deleteError', { entity: t('objectTypes.vendor.singular') })}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  }
}

async function fetchVendor(vendorId) {
  try {
    dataLoading.value = true

    await backend.vendors.get(vendorId).then(async (response) => {
      vendor.value = response
      await resolveFieldFromLookup(vendor.value, [
        { from: 'createdById', to: 'createdBy', keyspace: 'users' },
        { from: 'updatedById', to: 'updatedBy', keyspace: 'users' },
      ])
    })
  } catch (error) {
    toast.warning(
      t('common.notFound', { entity: t('objectTypes.vendor.singular') }),
    )
    router.push({ path: `/vendors`, replace: true })
  } finally {
    dataLoading.value = false
  }
}

async function fetchVendorApplications() {
  try {
    dataLoading.value = true

    const applicationsComponent = childComponents.value.find(
      (component) => component.name === 'applications',
    )
    await backend.vendors
      .getApplications(route.params.id, {
        page: applicationsComponent?.currentPage,
        limit: applicationsComponent?.perPage,
        sort_by: applicationsComponent?.sortColumnKey,
        sort_order: applicationsComponent?.sortDirection,
        search_field: applicationsComponent?.searchField,
        search_value: applicationsComponent?.searchValue,
      })
      .then((response) => {
        vendor.value.applications = response.items
        vendor.value.applicationsCount = response.pageDetails.totalCount
      })
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', {
        entities: t('objectTypes.application.plural'),
      }),
    )
  } finally {
    dataLoading.value = false
  }
}

async function fetchVendorOSs() {
  try {
    dataLoading.value = true

    const osComponent = childComponents.value.find(
      (component) => component.name === 'os',
    )
    await backend.vendors
      .getOS(route.params.id, {
        page: osComponent?.currentPage,
        limit: osComponent?.perPage,
        sort_by: osComponent?.sortColumnKey,
        sort_order: osComponent?.sortDirection,
        search_field: osComponent?.searchField,
        search_value: osComponent?.searchValue,
      })
      .then((response) => {
        vendor.value.os = response.items
        vendor.value.osCount = response.pageDetails.totalCount
      })
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', { entities: t('objectTypes.os.plural') }),
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

const vendorEdit = (vendorId) => {
  router.push({ path: `${vendorId}/edit` })
}

onMounted(async () => {
  fetchVendor(route.params.id)
  await checkObjectPermissions('vendors', route.params.id, permissionRefs, [
    {
      key: 'canReadPermissions',
      objectType: 'object_permissions',
      objectPermission: 'read',
      objectPath: `/${route.params.id}`,
    },
    {
      key: 'canCreateApps',
      objectType: 'applications',
      objectPermission: 'create',
      objectPath: '/*',
    },
    {
      key: 'canCreateOSs',
      objectType: 'os',
      objectPermission: 'create',
      objectPath: '/*',
    },
    {
      key: 'canReadChangelogs',
      objectType: 'changelogs',
      objectPermission: 'read',
      objectPath: '/*',
    },
  ])

  permissionsLoaded.value = true
})
</script>

<template>
  <!-- Modal: Delete application -->
  <CardBoxDeleteModal
    v-model="modals.deleteApplications.value"
    :name="objToRemove.name"
    :checkvalue="objToRemove.name"
    @form-submitted="deleteApplication(objToRemove.id)"
  />

  <!-- Modal: Delete os -->
  <CardBoxDeleteModal
    v-model="modals.deleteOs.value"
    :name="objToRemove.name"
    :checkvalue="objToRemove.name"
    @form-submitted="deleteOS(objToRemove.id)"
  />

  <!-- Modal: Delete vendor -->
  <CardBoxDeleteModal
    v-model="modals.deleteVendors.value"
    :name="vendor.name"
    :checkvalue="vendor.name"
    @form-submitted="deleteVendor(vendor.id)"
  />

  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiDomain"
        :title="vendor.name ? vendor.name : 'Loading...'"
        :object-model="$t('objectTypes.vendor.singular')"
        main
        docs-path="/docs/usage/openvle/infrastructure/vendors/"
      >
        <BaseButtons type="justify-start lg:justify-end">
          <BaseButton
            v-if="permissionRefs.canEdit"
            target="_blank"
            :icon="mdiPencil"
            :label="$t('common.edit')"
            color="contrast"
            rounded-full
            small
            @click="vendorEdit(vendor.id)"
          />

          <BaseButton
            v-if="permissionRefs.canDelete"
            target="_blank"
            :icon="mdiDelete"
            :label="$t('common.delete')"
            color="danger"
            rounded-full
            small
            @click="showModal('deleteVendors', vendor)"
          />
        </BaseButtons>
      </SectionTitleLineWithButton>

      <CardBox>
        <BaseTabs v-if="permissionsLoaded" @tab-changed="handleTabChanged">
          <BaseTab id="vendor" :title="$t('objectTypes.vendor.singular')">
            <FormField
              :label="$t('common.name')"
              :help="$t('views.vendors.form.nameHelp')"
            >
              <FormControl v-model="vendor.name" :icon="mdiRename" disabled />
            </FormField>

            <FormField
              :label="$t('common.description')"
              :help="$t('views.vendors.form.descriptionHelp')"
            >
              <FormControl
                v-model="vendor.description"
                :icon="mdiTextBox"
                disabled
              />
            </FormField>

            <ObjectMetadataDisplay
              v-if="loadedTabs.has('vendor') && vendor.id"
              :object="vendor"
              :object-type="objectModel"
              :object-id="route.params.id"
              :can-edit="permissionRefs.canEdit"
              :tags-help="$t('views.vendors.detail.tagsHelp')"
            />
          </BaseTab>

          <BaseTab
            id="applications"
            :title="$t('objectTypes.application.plural')"
          >
            <SectionTitleLineWithButton
              :icon="mdiApps"
              :title="$t('objectTypes.application.plural')"
              :reload="fetchVendorApplications"
            >
              <BaseButton
                v-if="permissionRefs.canCreateApps"
                :icon="mdiPlus"
                color="success"
                rounded-full
                small
                @click="
                  router.push({
                    path: `/applications/create`,
                    query: { vendor: vendor.id },
                  })
                "
              />
            </SectionTitleLineWithButton>

            <BaseTable
              v-if="loadedTabs.has('applications')"
              :current-page="
                childComponents.find(
                  (component) => component.name === 'applications',
                )?.currentPage
              "
              :per-page="
                childComponents.find(
                  (component) => component.name === 'applications',
                )?.perPage
              "
              :items-total="vendor.applicationsCount"
              :data="vendor.applications"
              :sort-column-key="
                childComponents.find(
                  (component) => component.name === 'applications',
                )?.sortColumnKey
              "
              :sort-direction="
                childComponents.find(
                  (component) => component.name === 'applications',
                )?.sortDirection
              "
              :loading="dataLoading"
              object-model="applications"
              :buttons="['view']"
              :search-bar-fields="applicationFields"
              :search-bar-max-filters="1"
              search-bar-query-key="filter-applications"
              :columns="[{ label: $t('common.name'), key: 'name' }]"
              @delete-object="handleDeleteObject"
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
              @search-triggered="handleSearch"
            />
          </BaseTab>

          <BaseTab id="os" :title="$t('objectTypes.os.plural')">
            <SectionTitleLineWithButton
              :icon="mdiApplicationBrackets"
              :title="$t('objectTypes.os.plural')"
              :reload="fetchVendorOSs"
            >
              <BaseButton
                v-if="permissionRefs.canCreateOSs"
                :icon="mdiPlus"
                color="success"
                rounded-full
                small
                @click="
                  router.push({
                    path: `/os/create`,
                    query: { vendor: vendor.id },
                  })
                "
              />
            </SectionTitleLineWithButton>

            <BaseTable
              v-if="loadedTabs.has('os')"
              :current-page="
                childComponents.find((component) => component.name === 'os')
                  ?.currentPage
              "
              :per-page="
                childComponents.find((component) => component.name === 'os')
                  ?.perPage
              "
              :items-total="vendor.osCount"
              :data="vendor.os"
              :sort-column-key="
                childComponents.find((component) => component.name === 'os')
                  ?.sortColumnKey
              "
              :sort-direction="
                childComponents.find((component) => component.name === 'os')
                  ?.sortDirection
              "
              :loading="dataLoading"
              object-model="os"
              :buttons="['view']"
              :search-bar-fields="osFields"
              :search-bar-max-filters="1"
              search-bar-query-key="filter-os"
              :columns="[{ label: $t('common.name'), key: 'name' }]"
              @delete-object="handleDeleteObject"
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
              @search-triggered="handleSearch"
            />
          </BaseTab>

          <BaseTab
            v-if="permissionRefs.canReadPermissions"
            id="permissions"
            :title="$t('objectTypes.permission.plural')"
          >
            <TablePermissions
              v-if="loadedTabs.has('permissions')"
              :object-id="route.params.id"
              :object-type="objectModel"
              :per-page="10"
            />
          </BaseTab>

          <BaseTab
            v-if="permissionRefs.canReadChangelogs"
            id="changelogs"
            :title="$t('objectTypes.changelog.plural')"
          >
            <TableChangelogs
              v-if="vendor.id && loadedTabs.has('changelogs')"
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
