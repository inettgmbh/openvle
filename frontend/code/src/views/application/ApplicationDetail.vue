<script setup>
import {
  mdiApps,
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
import { computed, onMounted, ref } from 'vue'
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
import ObjectMetadataDisplay from '@/components/ObjectMetadataDisplay.vue'
import SearchModal from '@/components/SearchModal.vue'
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
  addTemplates: ref(false),
  addVms: ref(false),
  deleteApplication: ref(false),
  deleteTemplates: ref(false),
  deleteVms: ref(false),
}
const application = ref([])
const dataLoading = ref(true)
const objectModel = 'Application'
const objToAdd = ref('')
const objToRemove = ref({})
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
      fetchData: fetchApplicationTemplates,
    },
    {
      name: 'vms',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'name',
      sortDirection: 'asc',
      searchField: null,
      searchValue: null,
      fetchData: fetchApplicationVMs,
    },
  ],
  fetchArgs: () => [route.params.id],
  modals,
  objToRemove,
  route,
})
/**/

const templateFields = templateSearchBarFields()
const vmFields = vmSearchBarFields()

async function addTemplate(templateId) {
  try {
    const template = ref([])

    /** Fetch Template apps to generate existingAppIds */
    try {
      await backend.templates
        .getApplications(templateId, {
          page: 1,
          limit: 200,
          sort_by: 'createdAt',
          sort_order: 'desc',
        })
        .then((response) => {
          template.value.applications = response.items
        })
    } catch (error) {
      toast.error(
        t('common.loadErrorPlural', {
          entities: t('objectTypes.application.plural'),
        }),
      )
    }

    const apps = [
      ...template.value.applications.map(({ key }) => ({ key })),
      { key: application.value.key },
    ]

    await backend.templates.updateApps(templateId, apps)
    fetchApplicationTemplates()
    toast.success(
      t('common.addSuccess', { entity: t('objectTypes.template.singular') }),
    )
  } catch (error) {
    toast.error(
      t('common.addError', { entity: t('objectTypes.template.singular') }),
    )
  }
  objToAdd.value = ''
}

async function addVM(vmId) {
  try {
    const vm = ref([])

    /** Fetch VM apps to generate existingAppIds */
    try {
      await backend.vms
        .getApps(vmId, {
          page: 1,
          limit: 200,
          sort_by: 'createdAt',
          sort_order: 'desc',
        })
        .then((response) => {
          vm.value.applications = response.items
        })
    } catch (error) {
      toast.error(
        t('common.loadErrorPlural', {
          entities: t('objectTypes.application.plural'),
        }),
      )
    }

    const apps = [
      ...vm.value.applications.map(({ key }) => ({ key })),
      { key: application.value.key },
    ]

    await backend.vms.updateApps(vmId, apps)
    fetchApplicationVMs()
    toast.success(
      t('common.addSuccess', {
        entity: t('objectTypes.virtualMachine.singular'),
      }),
    )
  } catch (error) {
    toast.error(
      t('common.addError', {
        entity: t('objectTypes.virtualMachine.singular'),
      }),
    )
  }
  objToAdd.value = ''
}

async function deleteApplication(appId) {
  try {
    await backend.applications.delete(appId)
    router.push({ path: `/applications` })
    toast.success(
      t('common.deleteSuccess', {
        entity: t('objectTypes.application.singular'),
      }),
    )
  } catch (error) {
    toast.error(
      t('common.deleteError', {
        entity: t('objectTypes.application.singular'),
      }),
    )
  }
}

async function deleteTemplate(appId, templateId) {
  try {
    const template = ref([])

    /** Fetch Template apps to generate existingAppIds */
    try {
      await backend.templates
        .getApplications(templateId, {
          page: 1,
          limit: 200,
          sort_by: 'createdAt',
          sort_order: 'desc',
        })
        .then((response) => {
          template.value.applications = response.items
        })
    } catch (error) {
      toast.error(
        t('common.loadErrorPlural', {
          entities: t('objectTypes.application.plural'),
        }),
      )
    }

    const apps = template.value.applications
      .filter(({ id }) => id !== appId)
      .map(({ key }) => ({ key }))
    await backend.templates.updateApps(templateId, apps)
    fetchApplicationTemplates()
    toast.success(
      t('common.removeSuccess', { entity: t('objectTypes.template.singular') }),
    )
  } catch (error) {
    toast.error(
      t('common.removeError', { entity: t('objectTypes.template.singular') }),
    )
  }
  objToRemove.value = ''
}

async function deleteVM(appId, vmId) {
  try {
    const vm = ref([])

    /** Fetch VM apps to generate existingAppIds */
    try {
      await backend.vms
        .getApps(vmId, {
          page: 1,
          limit: 200,
          sort_by: 'createdAt',
          sort_order: 'desc',
        })
        .then((response) => {
          vm.value.applications = response.items
        })
    } catch (error) {
      toast.error(
        t('common.loadErrorPlural', {
          entities: t('objectTypes.application.plural'),
        }),
      )
    }

    const apps = vm.value.applications
      .filter(({ id }) => id !== appId)
      .map(({ key }) => ({ key }))
    await backend.vms.updateApps(vmId, apps)
    fetchApplicationVMs()
    toast.success(
      t('common.removeSuccess', {
        entity: t('objectTypes.virtualMachine.singular'),
      }),
    )
  } catch (error) {
    toast.error(
      t('common.removeError', {
        entity: t('objectTypes.virtualMachine.singular'),
      }),
    )
  }
  objToRemove.value = ''
}

async function fetchApplication(appId) {
  try {
    dataLoading.value = true

    await backend.applications.get(appId).then(async (response) => {
      application.value = response
      await resolveFieldFromLookup(application.value, [
        { from: 'createdById', to: 'createdBy', keyspace: 'users' },
        { from: 'updatedById', to: 'updatedBy', keyspace: 'users' },
        { from: 'vendor', to: 'vendorName', keyspace: 'vendors' },
      ])
    })
  } catch (error) {
    toast.warning(
      t('common.notFound', { entity: t('objectTypes.application.singular') }),
    )
    router.push({ path: `/applications`, replace: true })
  } finally {
    dataLoading.value = false
  }
}

async function fetchApplicationTemplates() {
  try {
    dataLoading.value = true

    const templatesComponent = childComponents.value.find(
      (component) => component.name === 'templates',
    )
    await backend.applications
      .getTemplates(route.params.id, {
        page: templatesComponent?.currentPage,
        limit: templatesComponent?.perPage,
        sort_by: templatesComponent?.sortColumnKey,
        sort_order: templatesComponent?.sortDirection,
        search_field: templatesComponent?.searchField,
        search_value: templatesComponent?.searchValue,
      })
      .then((response) => {
        application.value.templates = response.items
        application.value.templatesCount = response.pageDetails.totalCount
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

async function fetchApplicationVMs() {
  try {
    dataLoading.value = true

    const vmsComponent = childComponents.value.find(
      (component) => component.name === 'vms',
    )
    await backend.applications
      .getVMs(route.params.id, {
        page: vmsComponent?.currentPage,
        limit: vmsComponent?.perPage,
        sort_by: vmsComponent?.sortColumnKey,
        sort_order: vmsComponent?.sortDirection,
        search_field: vmsComponent?.searchField,
        search_value: vmsComponent?.searchValue,
      })
      .then((response) => {
        application.value.vms = response.items
        application.value.vmsCount = response.pageDetails.totalCount
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

const applicationEdit = (appId) => {
  router.push({ path: `/applications/${appId}/edit` })
}

const buttonsVMs = computed(() => {
  if (permissionRefs.canUpdateVMs) return ['view', 'delete']
  return ['view']
})

const buttonsTemplate = computed(() => {
  if (permissionRefs.canUpdateTemplates) return ['view', 'delete']
  return ['view']
})

onMounted(async () => {
  fetchApplication(route.params.id)
  await checkObjectPermissions(
    'applications',
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
        key: 'canUpdateVMs',
        objectType: 'vms',
        objectPermission: 'update',
        objectPath: '/*',
      },
      {
        key: 'canUpdateTemplates',
        objectType: 'templates',
        objectPermission: 'update',
        objectPath: '/*',
      },
      {
        key: 'canReadChangelogs',
        objectType: 'changelogs',
        objectPermission: 'read',
        objectPath: '/*',
      },
    ],
  )

  permissionsLoaded.value = true
})
</script>

<template>
  <!-- Modal: Add template relation -->
  <SearchModal
    v-model="modals.addTemplates.value"
    :fetch-data="backend.templates.search"
    :icon="mdiVectorArrangeAbove"
    :label="$t('views.applications.detail.searchTemplate')"
    :title="$t('views.applications.detail.assignTemplate')"
    @submitted="addTemplate"
  />

  <!-- Modal: Add VM relation -->
  <SearchModal
    v-model="modals.addVms.value"
    :fetch-data="backend.vms.search"
    :icon="mdiMonitor"
    :label="$t('views.applications.detail.searchVm')"
    :title="$t('views.applications.detail.assignVm')"
    @submitted="addVM"
  />

  <!-- Modal: Delete application -->
  <CardBoxDeleteModal
    v-model="modals.deleteApplication.value"
    :name="application.name"
    :checkvalue="application.name"
    @form-submitted="deleteApplication(application.id)"
  />

  <!-- Modal: Delete template relation -->
  <CardBoxDeleteRelationModal
    v-model="modals.deleteTemplates.value"
    :parent-object="application.name"
    :related-object="objToRemove.name"
    :checkvalue="$t('common.confirmation')"
    @form-submitted="deleteTemplate(application.id, objToRemove.id)"
  />

  <!-- Modal: Delete VM relation -->
  <CardBoxDeleteRelationModal
    v-model="modals.deleteVms.value"
    :parent-object="application.name"
    :related-object="objToRemove.name"
    :checkvalue="$t('common.confirmation')"
    @form-submitted="deleteVM(application.id, objToRemove.id)"
  />

  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiApps"
        :title="application.name ? application.name : 'Loading...'"
        :object-model="$t('objectTypes.application.singular')"
        main
        docs-path="/docs/usage/openvle/infrastructure/applications/"
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
            @click="applicationEdit(application.id)"
          />

          <BaseButton
            v-if="permissionRefs.canDelete"
            target="_blank"
            :icon="mdiDelete"
            :label="$t('common.delete')"
            color="danger"
            rounded-full
            small
            @click="showModal('deleteApplication', application)"
          />
        </BaseButtons>
      </SectionTitleLineWithButton>

      <CardBox>
        <BaseTabs v-if="permissionsLoaded" @tab-changed="handleTabChanged">
          <BaseTab id="apps" :title="$t('objectTypes.application.singular')">
            <FormField
              :label="$t('common.name')"
              :help="$t('views.applications.form.nameHelp')"
            >
              <FormControl
                v-model="application.name"
                :icon="mdiRename"
                disabled
              />
            </FormField>

            <FormField
              label="Key (Slug)"
              :help="$t('views.applications.form.keyHelp')"
            >
              <FormControl v-model="application.key" :icon="mdiKey" disabled />
            </FormField>

            <FormField :label="$t('objectTypes.vendor.singular')">
              <FormControl
                v-model="application.vendorName"
                :icon="mdiDomain"
                :link="`/vendors/${application.vendor}`"
                disabled
              />
            </FormField>

            <FormField
              :label="$t('common.description')"
              :help="$t('views.applications.form.descriptionHelp')"
            >
              <FormControl
                v-model="application.description"
                :icon="mdiTextBox"
                disabled
              />
            </FormField>

            <ObjectMetadataDisplay
              v-if="loadedTabs.has('apps') && application.id"
              :object="application"
              :object-type="objectModel"
              :object-id="route.params.id"
              :can-edit="permissionRefs.canEdit"
              :tags-help="$t('views.applications.detail.tagsHelp')"
            />
          </BaseTab>

          <BaseTab id="vms" :title="$t('objectTypes.virtualMachine.plural')">
            <SectionTitleLineWithButton
              :icon="mdiMonitor"
              title="VMs"
              :reload="fetchApplicationVMs"
            >
              <BaseButton
                v-if="permissionRefs.canUpdateVMs"
                :icon="mdiPlus"
                color="success"
                rounded-full
                small
                @click="showModal('addVms')"
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
              :items-total="application.vmsCount"
              :data="application.vms"
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
              :buttons="buttonsVMs"
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
              :reload="fetchApplicationTemplates"
            >
              <BaseButton
                v-if="permissionRefs.canUpdateTemplates"
                :icon="mdiPlus"
                color="success"
                rounded-full
                small
                @click="showModal('addTemplates')"
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
              :items-total="application.templatesCount"
              :data="application.templates"
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
              :buttons="buttonsTemplate"
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
              v-if="application.id && loadedTabs.has('changelogs')"
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
