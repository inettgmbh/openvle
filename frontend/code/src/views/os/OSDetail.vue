<script setup>
import {
  mdiApplicationBrackets,
  mdiDelete,
  mdiDomain,
  mdiKey,
  mdiMonitor,
  mdiPencil,
  mdiPlus,
  mdiRename,
  mdiTextBox,
  mdiVectorArrangeAbove,
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
  templateSearchBarFields,
  vmSearchBarFields,
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
import { vmStatusIcon } from '@/utils/icons'
import { statusColorVM } from '@/utils/objectColors.js'
import { usePaginationChild } from '@/utils/pagination'

const { t } = useI18n()
const permissionRefs = usePermissionRefs()

const modals = {
  deleteOS: ref(false),
  deleteTemplates: ref(false),
  deleteVms: ref(false),
}
const objectModel = 'OS'
const objToRemove = ref({})
const dataLoading = ref(true)
const os = ref([])
const permissionsLoaded = ref(false)
const router = useRouter()
const route = useRoute()
const toast = useToast()

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
      name: 'templates',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'name',
      sortDirection: 'asc',
      searchField: null,
      searchValue: null,
      fetchData: fetchOSTemplates,
    },
    {
      name: 'vms',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'name',
      sortDirection: 'asc',
      searchField: null,
      searchValue: null,
      fetchData: fetchOSVMs,
    },
  ],
  fetchArgs: () => [route.params.id],
  modals,
  objToRemove,
  route,
})
/**/

const templateFields = templateSearchBarFields({ exclude: ['os'] })
const vmFields = vmSearchBarFields({ exclude: ['os'] })

async function deleteOS(osId) {
  try {
    await backend.os.delete(osId)
    router.push({ path: `/os` })
    toast.success(
      t('common.deleteSuccess', { entity: t('objectTypes.os.singular') }),
    )
  } catch (error) {
    toast.error(
      t('common.deleteError', { entity: t('objectTypes.os.singular') }),
    )
  }
}

async function deleteTemplate(templateId) {
  try {
    await backend.templates.delete(templateId)
    fetchOSTemplates()
    toast.success(t('views.os.detail.templateDeleted'))
  } catch (error) {
    toast.error(
      t('common.deleteError', { entity: t('objectTypes.template.singular') }),
    )
  }
}

async function deleteVM(id) {
  try {
    await backend.vms.delete(id)
    fetchOSVMs()
    toast.success(t('views.os.detail.vmDeleted'))
  } catch (error) {
    toast.error(
      t('common.deleteError', {
        entity: t('objectTypes.virtualMachine.singular'),
      }),
    )
  }
}

async function fetchOS(osId) {
  try {
    dataLoading.value = true

    await backend.os.get(osId).then(async (response) => {
      os.value = response
      await resolveFieldFromLookup(os.value, [
        { from: 'createdById', to: 'createdBy', keyspace: 'users' },
        { from: 'updatedById', to: 'updatedBy', keyspace: 'users' },
        { from: 'vendor', to: 'vendorName', keyspace: 'vendors' },
      ])
    })
  } catch (error) {
    toast.warning(
      t('common.notFound', { entity: t('objectTypes.os.singular') }),
    )
    router.push({ path: `/os`, replace: true })
  } finally {
    dataLoading.value = false
  }
}

async function fetchOSTemplates() {
  try {
    dataLoading.value = true

    const templatesComponent = childComponents.value.find(
      (component) => component.name === 'templates',
    )
    await backend.os
      .getTemplates(route.params.id, {
        page: templatesComponent?.currentPage,
        limit: templatesComponent?.perPage,
        sort_by: templatesComponent?.sortColumnKey,
        sort_order: templatesComponent?.sortDirection,
        search_field: templatesComponent?.searchField,
        search_value: templatesComponent?.searchValue,
      })
      .then((response) => {
        os.value.templates = response.items
        os.value.templatesCount = response.pageDetails.totalCount
      })
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', {
        entities: t('objectTypes.template.plural'),
      }),
    )
  } finally {
    dataLoading.value = false
  }
}

async function fetchOSVMs() {
  try {
    dataLoading.value = true

    const vmsComponent = childComponents.value.find(
      (component) => component.name === 'vms',
    )
    await backend.os
      .getVMs(route.params.id, {
        page: vmsComponent?.currentPage,
        limit: vmsComponent?.perPage,
        sort_by: vmsComponent?.sortColumnKey,
        sort_order: vmsComponent?.sortDirection,
        search_field: vmsComponent?.searchField,
        search_value: vmsComponent?.searchValue,
      })
      .then((response) => {
        os.value.vms = response.items
        os.value.vmsCount = response.pageDetails.totalCount
      })
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', {
        entities: t('objectTypes.virtualMachine.plural'),
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

const osEdit = (osId) => {
  router.push({ path: `/os/${osId}/edit` })
}

onMounted(async () => {
  fetchOS(route.params.id)
  await checkObjectPermissions('os', route.params.id, permissionRefs, [
    {
      key: 'canReadPermissions',
      objectType: 'object_permissions',
      objectPermission: 'read',
      objectPath: `/${route.params.id}`,
    },
    {
      key: 'canCreateVMs',
      objectType: 'vms',
      objectPermission: 'create',
      objectPath: '/*',
    },
    {
      key: 'canCreateTemplates',
      objectType: 'templates',
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
  <!-- Modal: Delete os -->
  <CardBoxDeleteModal
    v-model="modals.deleteOS.value"
    :name="os.name"
    :checkvalue="os.name"
    @form-submitted="deleteOS(objToRemove.id)"
  />

  <!-- Modal: Delete template -->
  <CardBoxDeleteModal
    v-model="modals.deleteTemplates.value"
    :name="objToRemove.name"
    :checkvalue="$t('common.confirmation')"
    @form-submitted="deleteTemplate(objToRemove.id)"
  />

  <!-- Modal: Delete vm -->
  <CardBoxDeleteModal
    v-model="modals.deleteVms.value"
    :name="objToRemove.name"
    :checkvalue="$t('common.confirmation')"
    @form-submitted="deleteVM(objToRemove.id)"
  />

  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiApplicationBrackets"
        :title="os.name ? os.name : 'Loading...'"
        :object-model="$t('objectTypes.os.singular')"
        main
        docs-path="/docs/usage/openvle/infrastructure/os/"
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
            @click="osEdit(os.id)"
          />

          <BaseButton
            v-if="permissionRefs.canDelete"
            target="_blank"
            :icon="mdiDelete"
            :label="$t('common.delete')"
            color="danger"
            rounded-full
            small
            @click="showModal('deleteOS', os)"
          />
        </BaseButtons>
      </SectionTitleLineWithButton>

      <CardBox>
        <BaseTabs v-if="permissionsLoaded" @tab-changed="handleTabChanged">
          <BaseTab id="os" :title="$t('objectTypes.os.singular')">
            <FormField
              :label="$t('common.name')"
              :help="$t('views.os.form.nameHelp')"
            >
              <FormControl v-model="os.name" :icon="mdiRename" disabled />
            </FormField>

            <FormField label="Key (Slug)" :help="$t('views.os.form.keyHelp')">
              <FormControl v-model="os.key" :icon="mdiKey" disabled />
            </FormField>

            <FormField :label="$t('objectTypes.vendor.singular')">
              <FormControl
                v-model="os.vendorName"
                :icon="mdiDomain"
                :link="`/vendors/${os.vendor}`"
                disabled
              />
            </FormField>

            <FormField
              :label="$t('common.description')"
              :help="$t('views.os.form.descriptionHelp')"
            >
              <FormControl
                v-model="os.description"
                :icon="mdiTextBox"
                disabled
              />
            </FormField>

            <ObjectMetadataDisplay
              v-if="loadedTabs.has('os') && os.id"
              :object="os"
              :object-type="objectModel"
              :object-id="route.params.id"
              :can-edit="permissionRefs.canEdit"
              :tags-help="$t('views.os.detail.tagsHelp')"
            />
          </BaseTab>

          <BaseTab id="vms" :title="$t('objectTypes.virtualMachine.plural')">
            <SectionTitleLineWithButton
              :icon="mdiMonitor"
              title="VMs"
              :reload="fetchOSVMs"
            >
              <BaseButton
                v-if="permissionRefs.canCreateVMs"
                :icon="mdiPlus"
                color="success"
                rounded-full
                small
                @click="
                  router.push({ path: `/vms/create`, query: { os: os.id } })
                "
              />
            </SectionTitleLineWithButton>

            <BaseTable
              v-if="loadedTabs.has('vms')"
              :current-page="
                childComponents.find((component) => component.name === 'vms')
                  ?.currentPage
              "
              :per-page="
                childComponents.find((component) => component.name === 'vms')
                  ?.perPage
              "
              :items-total="os.vmsCount"
              :data="os.vms"
              :sort-column-key="
                childComponents.find((component) => component.name === 'vms')
                  ?.sortColumnKey
              "
              :sort-direction="
                childComponents.find((component) => component.name === 'vms')
                  ?.sortDirection
              "
              :loading="dataLoading"
              object-model="vms"
              :buttons="['view']"
              :search-bar-fields="vmFields"
              :search-bar-max-filters="1"
              search-bar-query-key="filter-vms"
              :columns="[
                { label: $t('common.name'), key: 'name' },
                {
                  label: $t('common.description'),
                  key: 'description',
                  markdown: true,
                },
                {
                  label: $t('common.status'),
                  key: 'status',
                  color: statusColorVM,
                  icon: (value) => vmStatusIcon(value),
                },
              ]"
              @delete-object="handleDeleteObject"
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
              @search-triggered="handleSearch"
            />
          </BaseTab>

          <BaseTab id="templates" :title="$t('objectTypes.template.plural')">
            <SectionTitleLineWithButton
              :icon="mdiVectorArrangeAbove"
              :title="$t('objectTypes.template.plural')"
              :reload="fetchOSTemplates"
            >
              <BaseButton
                v-if="permissionRefs.canCreateTemplates"
                :icon="mdiPlus"
                color="success"
                rounded-full
                small
                @click="
                  router.push({
                    path: `/templates/create`,
                    query: { os: os.id },
                  })
                "
              />
            </SectionTitleLineWithButton>

            <BaseTable
              v-if="loadedTabs.has('templates')"
              :current-page="
                childComponents.find(
                  (component) => component.name === 'templates',
                )?.currentPage
              "
              :per-page="
                childComponents.find(
                  (component) => component.name === 'templates',
                )?.perPage
              "
              :items-total="os.templatesCount"
              :data="os.templates"
              :sort-column-key="
                childComponents.find(
                  (component) => component.name === 'templates',
                )?.sortColumnKey
              "
              :sort-direction="
                childComponents.find(
                  (component) => component.name === 'templates',
                )?.sortDirection
              "
              :loading="dataLoading"
              object-model="templates"
              :buttons="['view']"
              :search-bar-fields="templateFields"
              :search-bar-max-filters="1"
              search-bar-query-key="filter-templates"
              :columns="[
                { label: $t('common.name'), key: 'name' },
                {
                  label: $t('common.description'),
                  key: 'description',
                  markdown: true,
                },
              ]"
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
              v-if="os.id && loadedTabs.has('changelogs')"
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
