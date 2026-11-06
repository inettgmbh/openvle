<script setup>
import {
  mdiApplicationBrackets,
  mdiApps,
  mdiContentCopy,
  mdiCpu64Bit,
  mdiDelete,
  mdiFileTree,
  mdiHarddisk,
  mdiLock,
  mdiLockOpen,
  mdiMemory,
  mdiMonitor,
  mdiPencil,
  mdiPlus,
  mdiRemoteDesktop,
  mdiSchoolOutline,
  mdiServer,
  mdiVectorArrangeAbove,
} from '@mdi/js'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseDivider from '@/components/BaseDivider.vue'
import BaseMarkdown from '@/components/BaseMarkdown.vue'
import BaseTab from '@/components/BaseTab.vue'
import BaseTable from '@/components/BaseTable.vue'
import BaseTabs from '@/components/BaseTabs.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxDeleteModal from '@/components/CardBoxDeleteModal.vue'
import CardBoxDeleteRelationModal from '@/components/CardBoxDeleteRelationModal.vue'
import CardBoxModal from '@/components/CardBoxModal.vue'
import FormField from '@/components/FormField.vue'
import ImportConnectionProfileModal from '@/components/ImportConnectionProfileModal.vue'
import ObjectMetadataDisplay from '@/components/ObjectMetadataDisplay.vue'
import PillTag from '@/components/PillTag.vue'
import SearchModal from '@/components/SearchModal.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import SpecCard from '@/components/SpecCard.vue'
import {
  applicationSearchBarFields,
  connectionSearchBarFields,
  courseSearchBarFields,
  vmSearchBarFields,
} from '@/components/Tables/searchBarFieldConfigs'
import TableChangelogs from '@/components/Tables/TableChangelogs.vue'
import TablePermissions from '@/components/Tables/TablePermissions.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import {
  checkObjectPermissions,
  connectionProfileLabelFormatter,
  resolveFieldFromLookup,
  templateStatusFormatter,
  usePermissionRefs,
} from '@/utils/dataUtils'
import {
  connectionProtocolFormatterIcon,
  taskStatusIcon,
  templateStatusIcon,
  vmStatusIcon,
} from '@/utils/icons'
import {
  protocolColorConnection,
  statusColorTask,
  statusColorTemplates,
  statusColorVM,
} from '@/utils/objectColors.js'
import { usePaginationChild } from '@/utils/pagination'
import { taskStatusTooltip } from '@/utils/tooltips'

const { t } = useI18n()
const permissionRefs = usePermissionRefs()

const modals = {
  addCourses: ref(false),
  addApplications: ref(false),
  deleteApplications: ref(false),
  deleteConnections: ref(false),
  deleteCourses: ref(false),
  deleteTemplates: ref(false),
  deleteVms: ref(false),
  deleteVmsForReal: ref(false),
  importConnections: ref(false),
}
const dataLoading = ref(true)
const objectModel = 'Template'
const objToAdd = ref('')
const objToRemove = ref({})
const permissionsLoaded = ref(false)
const router = useRouter()
const route = useRoute()
const toast = useToast()
const template = ref([])
const templateTasks = ref([])
const templateConnectionProfiles = ref([])
const relatedGuacamoles = ref([])

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

function resolvedField(id, name) {
  const resolved = id && name && !UUID_RE.test(name)
  return {
    value: resolved ? name : id ? `${id.substring(0, 8)}...` : '–',
    link: resolved ? true : false,
    hint: id && !resolved ? t('views.templates.detail.noReadPermission') : null,
  }
}

const osDisplay = computed(() =>
  resolvedField(template.value.os, template.value.osName),
)

/* PAGINATION ONLY */
const {
  childComponents,
  loadedTabs,
  handlePaginationChanged,
  handleSortOrderChanged,
  handleDeleteObject,
  handleSearch,
  handleTabChanged,
  refreshActiveTab,
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
      fetchData: fetchTemplateApplications,
    },
    {
      name: 'courses',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'name',
      sortDirection: 'asc',
      searchField: null,
      searchValue: null,
      fetchData: fetchTemplateCourses,
    },
    {
      name: 'connections',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'createdAt',
      sortDirection: 'asc',
      searchField: null,
      searchValue: null,
      fetchData: fetchTemplateConnectionProfiles,
    },
    {
      name: 'tasks/subtasks',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'createdAt',
      sortDirection: 'desc',
      fetchData: fetchTemplateTasks,
    },
    {
      name: 'vms',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'name',
      sortDirection: 'asc',
      searchField: null,
      searchValue: null,
      fetchData: fetchTemplateVMs,
    },
  ],
  fetchArgs: () => [route.params.id],
  modals,
  objToRemove,
  route,
})
/**/

const applicationFields = applicationSearchBarFields()
const courseFields = courseSearchBarFields()
const connectionFields = connectionSearchBarFields({ exclude: ['objectId'] })
const vmFields = vmSearchBarFields({ exclude: ['template'] })

async function addApplication(appKey) {
  try {
    const applications = [
      ...template.value.applications.map(({ key }) => ({ key })),
      { key: appKey },
    ]
    await backend.templates.updateApps(route.params.id, applications)
    fetchTemplateApplications()
    toast.success(t('views.templates.detail.applicationAdded'))
  } catch (error) {
    toast.error(
      `${t('common.addError', { entity: t('objectTypes.application.singular') })}\n${error?.response?.data?.detail ?? ''}`,
      { timeout: 8400 },
    )
  }
}

async function addCourse(courseId) {
  try {
    await backend.courses.addTemplate(courseId, route.params.id)
    fetchTemplateCourses()
    toast.success(t('views.templates.detail.courseAdded'))
  } catch (error) {
    toast.error(
      `${t('common.addError', { entity: t('objectTypes.course.singular') })}\n${error?.response?.data?.detail ?? ''}`,
      { timeout: 8400 },
    )
  }
  objToAdd.value = ''
}

async function deleteApplication(appId) {
  try {
    const applications = template.value.applications
      .filter(({ id }) => id !== appId)
      .map(({ key }) => ({ key }))
    await backend.templates.updateApps(route.params.id, applications)
    fetchTemplateApplications()
    toast.success(t('views.templates.detail.applicationRemoved'))
  } catch (error) {
    toast.error(
      `${t('common.removeError', { entity: t('objectTypes.application.singular') })}\n${error?.response?.data?.detail ?? ''}`,
      { timeout: 8400 },
    )
  }
  objToRemove.value = ''
}

async function deleteCourse(templateId, courseId) {
  try {
    await backend.courses.deleteTemplate(courseId, templateId)
    fetchTemplateCourses()
    toast.success(t('views.templates.detail.courseRemoved'))
  } catch (error) {
    toast.error(
      `${t('common.removeError', { entity: t('objectTypes.course.singular') })}\n${error?.response?.data?.detail ?? ''}`,
      { timeout: 8400 },
    )
  }
}

async function openDeleteConnectionProfileModal(profile) {
  objToRemove.value = profile
  relatedGuacamoles.value = []
  backend.beginSilent()
  try {
    const result = await backend.guacamole.listByConnectionProfile(profile.id)
    const items = result?.items ?? []
    if (items.length > 0) {
      await resolveFieldFromLookup(items, [
        { from: 'userId', to: 'user', keyspace: 'users' },
      ])
    }
    relatedGuacamoles.value = items
  } catch {
    relatedGuacamoles.value = []
  } finally {
    backend.endSilent()
  }
  modals.deleteConnections.value = true
}

async function deleteConnectionProfile(id) {
  const cascadeTargets = relatedGuacamoles.value.slice()
  backend.beginSilent()
  try {
    for (const guac of cascadeTargets) {
      try {
        await backend.guacamole.delete(guac.id)
      } catch (error) {
        toast.error(
          `${t('views.connections.delete.cascadeStepError', { name: guac.name ?? guac.id })}\n${error?.response?.data?.detail ?? ''}`,
          { timeout: 8400 },
        )
        return
      }
    }
    await backend.connections.delete(id)
    toast.success(
      t('common.deleteSuccess', {
        entity: t('objectTypes.guacamoleConnectionProfile.singular'),
      }),
    )
  } catch (error) {
    toast.error(
      `${t('common.deleteError', { entity: t('objectTypes.guacamoleConnectionProfile.singular') })}\n${error?.response?.data?.detail ?? ''}`,
      { timeout: 8400 },
    )
  } finally {
    backend.endSilent()
    relatedGuacamoles.value = []
    await fetchTemplateConnectionProfiles()
  }
}

const BLOCKING_ITEMS_LIMIT = 5
const blockingItems = ref([])
const blockingItemsTotal = ref(0)

async function openDeleteTemplateModal(templateObj) {
  objToRemove.value = templateObj
  blockingItems.value = []
  blockingItemsTotal.value = 0
  backend.beginSilent()
  try {
    const [vms, courses] = await Promise.all([
      backend.templates.getVMs(templateObj.id, {
        page: 1,
        limit: BLOCKING_ITEMS_LIMIT,
      }),
      backend.templates.getCourses(templateObj.id, {
        page: 1,
        limit: BLOCKING_ITEMS_LIMIT,
      }),
    ])
    const vmItems = (vms?.items ?? []).map((vm) => ({
      label: vm.name ?? vm.id,
      sublabel: t('objectTypes.virtualMachine.singular'),
    }))
    const courseItems = (courses?.items ?? []).map((course) => ({
      label: course.name ?? course.id,
      sublabel: t('objectTypes.course.singular'),
    }))
    blockingItems.value = [...vmItems, ...courseItems].slice(
      0,
      BLOCKING_ITEMS_LIMIT,
    )
    blockingItemsTotal.value =
      (vms?.pageDetails?.totalCount ?? vmItems.length) +
      (courses?.pageDetails?.totalCount ?? courseItems.length)
  } catch {
    // Fail open: the backend 409 pre-check still blocks the delete.
    // Events referencing the template have no list endpoint and are only
    // caught reactively via OBJECT_IN_USE.
  } finally {
    backend.endSilent()
  }
  modals.deleteTemplates.value = true
}

const blockingItemRows = computed(() => {
  const items = blockingItems.value.slice()
  const more = blockingItemsTotal.value - items.length
  if (more > 0) {
    items.push({
      label: t('views.templates.delete.moreItems', { count: more }, more),
    })
  }
  return items
})

async function deleteTemplate(templateId) {
  backend.beginSilent()
  try {
    await backend.templates.delete(templateId)
    router.push({ path: `/templates` })
    toast.info(t('views.templates.detail.deleteInProgress'))
  } catch (error) {
    const errorCode = error?.response?.data?.error_code
    if (
      errorCode === 'OBJECT_IN_USE' ||
      errorCode === 'OBJECT_DELETE_INTEGRITY_ERROR'
    ) {
      toast.error(t('views.templates.delete.blockedError'), { timeout: 8400 })
    } else {
      toast.error(
        `${t('common.deleteError', { entity: t('objectTypes.template.singular') })}\n${error?.response?.data?.detail ?? ''}`,
        { timeout: 8400 },
      )
    }
  } finally {
    backend.endSilent()
  }
}

async function deleteVM(id) {
  try {
    await backend.vms.delete(id)
    fetchTemplateVMs()
    toast.info(t('views.templates.detail.vmDeleteInProgress'))
  } catch (error) {
    toast.error(
      `${t('common.deleteError', { entity: t('objectTypes.virtualMachine.singular') })}\n${error?.response?.data?.detail ?? ''}`,
      { timeout: 8400 },
    )
  }
}

async function fetchTemplate(templateId) {
  try {
    dataLoading.value = true

    await backend.templates.get(templateId).then(async (response) => {
      template.value = response
      await resolveFieldFromLookup(template.value, [
        { from: 'createdById', to: 'createdBy', keyspace: 'users' },
        { from: 'updatedById', to: 'updatedBy', keyspace: 'users' },
      ])

      if (template.value.os) {
        await resolveFieldFromLookup(template.value, [
          { from: 'os', to: 'osName', keyspace: 'os' },
        ])
      }

      template.value.ram = template.value.ram / 1024
      template.value.proxmoxLabel = `${template?.value?.proxmoxId} (${template?.value?.proxmoxNode})`
    })
  } catch (error) {
    toast.warning(t('views.templates.detail.loadError'))
    router.push({ path: `/templates`, replace: true })
  } finally {
    dataLoading.value = false
  }
}

async function fetchTemplateApplications() {
  try {
    dataLoading.value = true

    const applicationsComponent = childComponents.value.find(
      (component) => component.name === 'applications',
    )
    await backend.templates
      .getApplications(route.params.id, {
        page: applicationsComponent?.currentPage,
        limit: applicationsComponent?.perPage,
        sort_by: applicationsComponent?.sortColumnKey,
        sort_order: applicationsComponent?.sortDirection,
        search_field: applicationsComponent?.searchField,
        search_value: applicationsComponent?.searchValue,
      })
      .then(async (response) => {
        template.value.applications = response.items
        template.value.applicationsCount = response.pageDetails.totalCount
        await resolveFieldFromLookup(template.value.applications, [
          { from: 'vendor', to: 'vendorName', keyspace: 'vendors' },
        ])
      })
  } catch (error) {
    toast.error(
      `${t('common.loadErrorPlural', { entities: t('objectTypes.application.plural') })}\n${error?.response?.data?.detail ?? ''}`,
      { timeout: 8400 },
    )
  } finally {
    dataLoading.value = false
  }
}

async function fetchTemplateConnectionProfiles() {
  try {
    dataLoading.value = true

    const connectionsComponent = childComponents.value.find(
      (component) => component.name === 'connections',
    )
    await backend.connections
      .listByObject(objectModel, route.params.id, {
        page: connectionsComponent?.currentPage,
        limit: connectionsComponent?.perPage,
        sort_by: connectionsComponent?.sortColumnKey,
        sort_order: connectionsComponent?.sortDirection,
        search_field: connectionsComponent?.searchField,
        search_value: connectionsComponent?.searchValue,
      })
      .then((response) => {
        templateConnectionProfiles.value = response.items.map((obj) => ({
          ...obj,
          value: obj.id,
        }))
        templateConnectionProfiles.value.count = response.pageDetails.totalCount
        resolveFieldFromLookup(templateConnectionProfiles.value, [
          {
            from: 'objectId',
            to: 'label',
            keyspace: 'templates',
            formatter: (obj) => ({
              label: connectionProfileLabelFormatter(
                obj,
                obj.protocol,
                obj.username,
                obj.label,
                obj.port,
              ),
            }),
          },
        ])
      })
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', {
        entities: t('objectTypes.guacamoleConnectionProfile.plural'),
      }),
    )
  } finally {
    dataLoading.value = false
  }
}

async function fetchTemplateCourses() {
  try {
    dataLoading.value = true

    const coursesComponent = childComponents.value.find(
      (component) => component.name === 'courses',
    )
    await backend.templates
      .getCourses(route.params.id, {
        page: coursesComponent?.currentPage,
        limit: coursesComponent?.perPage,
        sort_by: coursesComponent?.sortColumnKey,
        sort_order: coursesComponent?.sortDirection,
        search_field: coursesComponent?.searchField,
        search_value: coursesComponent?.searchValue,
      })
      .then((response) => {
        template.value.courses = response.items
        template.value.coursesCount = response.pageDetails.totalCount
      })
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', { entities: t('objectTypes.course.plural') }),
    )
  } finally {
    dataLoading.value = false
  }
}

async function fetchTemplateTasks() {
  try {
    dataLoading.value = true

    const tasksComponent = childComponents.value.find(
      (component) => component.name === 'tasks/subtasks',
    )
    await backend.tasks
      .listSubTasks({
        page: tasksComponent?.currentPage,
        limit: tasksComponent?.perPage,
        sort_by: tasksComponent?.sortColumnKey,
        sort_order: tasksComponent?.sortDirection,
        search_field: 'object_id',
        search_value: route.params.id,
      })
      .then(async (response) => {
        templateTasks.value = response.items
        templateTasks.value.count = response.pageDetails.totalCount
        await resolveFieldFromLookup(templateTasks.value, [
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

async function fetchTemplateVMs() {
  try {
    dataLoading.value = true

    const vmsComponent = childComponents.value.find(
      (component) => component.name === 'vms',
    )
    await backend.templates
      .getVMs(route.params.id, {
        page: vmsComponent?.currentPage,
        limit: vmsComponent?.perPage,
        sort_by: vmsComponent?.sortColumnKey,
        sort_order: vmsComponent?.sortDirection,
        search_field: vmsComponent?.searchField,
        search_value: vmsComponent?.searchValue,
      })
      .then((response) => {
        template.value.vms = response.items
        template.value.vmsCount = response.pageDetails.totalCount
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

async function handleProtectionChange() {
  try {
    await backend.templates
      .setProtection(
        template.value.id,
        template.value.prevent_delete ? false : true,
      )
      .then(() => {
        fetchTemplate(route.params.id)
      })
    toast.success(t('views.templates.detail.protectionChanged'))
  } catch (error) {
    toast.error(
      t('common.protectionChangeError', {
        entity: t('objectTypes.template.singular'),
      }),
    )
  }
}

const actionsDisabled = computed(() => {
  return !template.value.proxmoxId || !template.value.proxmoxNode
})

const actionsTooltip = computed(() => {
  return actionsDisabled.value
    ? t('views.templates.detail.proxmoxNotFound')
    : undefined
})

const buttonsApps = computed(() => {
  if (permissionRefs.canEdit) return ['view', 'delete']
  return ['view']
})

const buttonsConnections = computed(() => {
  if (permissionRefs.canDeleteConnections) return ['view', 'delete']
  return ['view']
})

const createConnectionProfile = (templateId) => {
  router.push({
    path: `/connections/create`,
    query: {
      entityId: templateId,
      entityType: objectModel,
    },
  })
}

const pillType = computed(() => {
  if (template.value.id) {
    if (template.value.prevent_delete) {
      return 'danger'
    }
    return 'success'
  }
  return 'info'
})

const templateEdit = (templateId) => {
  router.push({ path: `/templates/${templateId}/edit` })
}

const isAutoRefreshing = computed(
  () =>
    template.value?.status &&
    template.value.status.toLowerCase() !== 'available',
)

let intervalId = null

function startPolling() {
  stopPolling()
  if (isAutoRefreshing.value) {
    intervalId = setInterval(() => {
      fetchTemplate(route.params.id)
      refreshActiveTab()
    }, 15000)
  }
}

function stopPolling() {
  if (intervalId) {
    clearInterval(intervalId)
    intervalId = null
  }
}

onMounted(async () => {
  await fetchTemplate(route.params.id)
  startPolling()
  await checkObjectPermissions('templates', route.params.id, permissionRefs, [
    {
      key: 'canCreateVMs',
      objectType: 'vms',
      objectPermission: 'read',
      objectPath: '/*',
    },
    {
      key: 'canReadPermissions',
      objectType: 'object_permissions',
      objectPermission: 'read',
      objectPath: `/${route.params.id}`,
    },
    {
      key: 'canCreateCourses',
      objectType: 'courses',
      objectPermission: 'create',
      objectPath: '/*',
    },
    {
      key: 'canCreateConnections',
      objectType: 'guacamole_connection_profiles',
      objectPermission: 'create',
      objectPath: '/*',
    },
    {
      key: 'canDeleteConnections',
      objectType: 'guacamole_connection_profiles',
      objectPermission: 'delete',
      objectPath: '/*',
    },
    {
      key: 'canReadConnections',
      objectType: 'guacamole_connection_profiles',
      objectPermission: 'read',
      objectPath: '/',
    },
    {
      key: 'canReadSubTasks',
      objectType: 'sub_tasks',
      objectPermission: 'read',
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

watch(isAutoRefreshing, (val) => {
  if (val) {
    startPolling()
  } else {
    stopPolling()
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <!-- Modal: Add app to template -->
  <SearchModal
    v-model="modals.addApplications.value"
    :fetch-data="backend.applications.search"
    :icon="mdiApps"
    :label="$t('views.templates.detail.searchApplication')"
    :title="$t('views.templates.detail.assignApplication')"
    return-attribute="key"
    @submitted="addApplication"
  />

  <!-- Modal: Add template to course -->
  <SearchModal
    v-model="modals.addCourses.value"
    :fetch-data="backend.courses.search"
    :icon="mdiSchoolOutline"
    :label="$t('views.templates.detail.searchCourse')"
    :title="$t('views.templates.detail.assignCourse')"
    @submitted="addCourse"
  />

  <!-- Modal: Delete app from template -->
  <CardBoxDeleteRelationModal
    v-model="modals.deleteApplications.value"
    :parent-object="template.name"
    :related-object="objToRemove.name"
    :checkvalue="$t('common.confirmation')"
    @form-submitted="deleteApplication(objToRemove.id)"
  />

  <!-- Modal: Delete template from course -->
  <CardBoxDeleteRelationModal
    v-model="modals.deleteCourses.value"
    :parent-object="template.name"
    :related-object="objToRemove.name"
    :checkvalue="$t('common.confirmation')"
    @form-submitted="deleteCourse(template.id, objToRemove.id)"
  />

  <!-- Modal: Delete template -->
  <CardBoxDeleteModal
    v-model="modals.deleteTemplates.value"
    :name="template.name"
    :checkvalue="template.name"
    :blocked="blockingItemsTotal > 0"
    :warning="
      blockingItemsTotal > 0
        ? $t(
            'views.templates.delete.relatedWarning',
            { count: blockingItemsTotal },
            blockingItemsTotal,
          )
        : null
    "
    :related-items="blockingItemRows"
    :related-label="$t('views.templates.delete.relatedLabel')"
    :related-count="blockingItemsTotal"
    @form-submitted="deleteTemplate(objToRemove.id)"
  />

  <!-- Modal: Import Connection Profile -->
  <ImportConnectionProfileModal
    v-if="template.id"
    v-model="modals.importConnections.value"
    :target-object-type="objectModel"
    :target-object-id="template.id"
    @imported="fetchTemplateConnectionProfiles"
  />

  <!-- Modal: Delete Connection Profile -->
  <CardBoxDeleteModal
    v-model="modals.deleteConnections.value"
    :name="objToRemove.label"
    :checkvalue="$t('common.confirm')"
    :warning="
      relatedGuacamoles.length > 0
        ? $t(
            'views.connections.delete.relatedWarning',
            { count: relatedGuacamoles.length },
            relatedGuacamoles.length,
          )
        : null
    "
    :related-items="
      relatedGuacamoles.map((g) => ({
        label: g.name ?? g.id,
        sublabel: g.user ?? null,
      }))
    "
    :related-label="$t('views.connections.delete.relatedLabel')"
    :require-extra-confirm="relatedGuacamoles.length > 0"
    :extra-confirm-label="$t('views.connections.delete.cascadeConfirmLabel')"
    @form-submitted="deleteConnectionProfile(objToRemove.id)"
  />

  <!-- Modal: Delete vm -->
  <CardBoxModal
    v-model="modals.deleteVms.value"
    :title="$t('views.templates.detail.confirmAction')"
    button="danger"
    has-cancel
    :button-label="$t('common.delete')"
    @form-submitted="modals.deleteVmsForReal.value = true"
  >
    <p>
      {{ $t('views.templates.detail.vmWillBeDeleted', { name: objToRemove }) }}
    </p>

    <p>{{ $t('views.templates.detail.areYouSure') }}</p>
  </CardBoxModal>

  <!-- Delete VM Confirmation Modal -->
  <CardBoxModal
    v-model="modals.deleteVmsForReal.value"
    :title="$t('views.templates.detail.confirmAction')"
    button="danger"
    has-cancel
    :button-label="$t('common.delete')"
    @form-submitted="deleteVM(objToRemove)"
  >
    <p>
      <b>{{ $t('views.templates.detail.cannotBeUndone') }}</b>
    </p>

    <p>
      <b>{{ $t('views.templates.detail.areYouReallySure') }}</b>
    </p>
  </CardBoxModal>

  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiVectorArrangeAbove"
        :title="template.name ? template.name : 'Loading...'"
        :object-model="$t('objectTypes.template.singular')"
        main
        docs-path="/docs/usage/openvle/vms/templates/"
        class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"
      >
        <div class="flex flex-wrap gap-2 justify-start sm:justify-end">
          <!-- PillTag: Template status -->
          <PillTag
            :label="templateStatusFormatter(template.status)"
            :color="statusColorTemplates(template.status)"
            :disabled="true"
            :icon="templateStatusIcon(template.status)"
            small
          />

          <!-- PillTag: Template protection -->
          <PillTag
            :color="pillType"
            :icon="template.prevent_delete ? mdiLock : mdiLockOpen"
            :handle-click="handleProtectionChange"
          />

          <BaseButton
            v-if="permissionRefs.canCreateVMs"
            v-tooltip="actionsTooltip"
            target="_blank"
            :icon="mdiContentCopy"
            :label="$t('views.templates.detail.createVm')"
            color="info"
            rounded-full
            small
            :disabled="actionsDisabled"
            @click="
              router.push({
                path: `/vms/create`,
                query: {
                  template: template.id,
                },
              })
            "
          />

          <BaseButton
            v-if="permissionRefs.canEdit"
            v-tooltip="actionsTooltip"
            target="_blank"
            :icon="mdiPencil"
            :label="$t('common.edit')"
            color="contrast"
            rounded-full
            small
            :disabled="actionsDisabled"
            @click="templateEdit(template.id)"
          />

          <BaseButton
            v-if="permissionRefs.canDelete"
            v-tooltip="
              template.prevent_delete
                ? $t('views.templates.detail.templateProtected')
                : undefined
            "
            target="_blank"
            :icon="mdiDelete"
            :label="$t('common.delete')"
            color="danger"
            rounded-full
            small
            :disabled="template.prevent_delete"
            @click="openDeleteTemplateModal(template)"
          />
        </div>
      </SectionTitleLineWithButton>

      <p
        v-if="isAutoRefreshing"
        class="text-xs text-right text-slate-400 dark:text-slate-500 -mt-4 mb-4"
      >
        {{ $t('common.autoRefresh', { seconds: 15 }) }}
      </p>

      <CardBox>
        <BaseTabs v-if="permissionsLoaded" @tab-changed="handleTabChanged">
          <BaseTab id="infos" :title="$t('common.infos')">
            <!-- Spec cards -->
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
              <SpecCard
                :icon="mdiCpu64Bit"
                :value="template.cpu ?? '–'"
                :label="$t('views.templates.form.cpuCores')"
                color="blue"
              />

              <SpecCard
                :icon="mdiMemory"
                :value="template.ram ? `${template.ram} GB` : '–'"
                :label="$t('common.memory')"
                color="violet"
              />

              <SpecCard
                :icon="mdiHarddisk"
                :value="template.disk ? `${template.disk} GB` : '–'"
                :label="$t('views.templates.detail.disk')"
                color="amber"
              />

              <SpecCard
                :icon="mdiApplicationBrackets"
                :value="osDisplay.value"
                :label="$t('views.templates.form.os')"
                color="emerald"
                :link="osDisplay.link ? `/os/${template.os}` : null"
                :hint="osDisplay.hint"
              />

              <SpecCard
                :icon="mdiServer"
                :value="template.proxmoxLabel ?? '–'"
                :label="$t('common.proxmox')"
                color="slate"
              />
            </div>

            <BaseDivider />

            <FormField
              :label="$t('common.description')"
              :help="$t('views.templates.detail.descriptionHelp')"
            />

            <BaseMarkdown v-model="template.description" action="view" />

            <ObjectMetadataDisplay
              v-if="loadedTabs.has('infos') && template.id"
              :object="template"
              :object-type="objectModel"
              :object-id="route.params.id"
              :can-edit="permissionRefs.canEdit"
              :tags-help="$t('views.templates.detail.tagsHelp')"
            />
          </BaseTab>

          <BaseTab
            id="applications"
            :title="$t('objectTypes.application.plural')"
          >
            <SectionTitleLineWithButton
              :icon="mdiApps"
              :title="$t('objectTypes.application.plural')"
              :reload="fetchTemplateApplications"
            >
              <BaseButton
                v-if="permissionRefs.canEdit"
                :icon="mdiPlus"
                color="success"
                rounded-full
                small
                @click="showModal('addApplications')"
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
              :items-total="template.applicationsCount"
              :data="template.applications"
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
              :buttons="buttonsApps"
              :search-bar-fields="applicationFields"
              :search-bar-max-filters="1"
              search-bar-query-key="filter-applications"
              :columns="[
                { label: $t('common.name'), key: 'name' },
                {
                  label: $t('views.templates.detail.vendor'),
                  key: 'vendorName',
                  sortKey: 'vendor',
                },
              ]"
              @delete-object="handleDeleteObject"
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
              @search-triggered="handleSearch"
            />
          </BaseTab>

          <BaseTab id="vms" :title="$t('objectTypes.virtualMachine.plural')">
            <SectionTitleLineWithButton
              :icon="mdiMonitor"
              :title="$t('views.templates.detail.virtualMachines')"
              :reload="fetchTemplateVMs"
            >
              <BaseButton
                v-if="permissionRefs.canCreateVMs"
                :icon="mdiPlus"
                color="success"
                rounded-full
                small
                @click="
                  router.push({
                    path: `/vms/create`,
                    query: {
                      template: template.id,
                    },
                  })
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
              :items-total="template.vmsCount"
              :data="template.vms"
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

          <BaseTab id="courses" :title="$t('objectTypes.course.plural')">
            <SectionTitleLineWithButton
              :icon="mdiSchoolOutline"
              :title="$t('objectTypes.course.plural')"
              :reload="fetchTemplateCourses"
            >
              <BaseButton
                v-if="permissionRefs.canCreateCourses"
                :icon="mdiPlus"
                color="success"
                rounded-full
                small
                @click="showModal('addCourses')"
              />
            </SectionTitleLineWithButton>

            <BaseTable
              v-if="loadedTabs.has('courses')"
              :current-page="
                childComponents.find(
                  (component) => component.name === 'courses',
                )?.currentPage
              "
              :per-page="
                childComponents.find(
                  (component) => component.name === 'courses',
                )?.perPage
              "
              :items-total="template.coursesCount"
              :data="template.courses"
              :sort-column-key="
                childComponents.find(
                  (component) => component.name === 'courses',
                )?.sortColumnKey
              "
              :sort-direction="
                childComponents.find(
                  (component) => component.name === 'courses',
                )?.sortDirection
              "
              :loading="dataLoading"
              object-model="courses"
              :buttons="['view']"
              :search-bar-fields="courseFields"
              :search-bar-max-filters="1"
              search-bar-query-key="filter-courses"
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
            v-if="permissionRefs.canReadConnections"
            id="connections"
            :title="$t('objectTypes.guacamoleConnectionProfile.plural')"
          >
            <SectionTitleLineWithButton
              :icon="mdiRemoteDesktop"
              :title="$t('objectTypes.guacamoleConnectionProfile.plural')"
              :reload="fetchTemplateConnectionProfiles"
            >
              <BaseButton
                v-if="permissionRefs.canCreateConnections"
                v-tooltip="$t('views.connections.import.tooltip')"
                :icon="mdiContentCopy"
                color="info"
                rounded-full
                small
                @click="modals.importConnections.value = true"
              />

              <BaseButton
                v-if="permissionRefs.canCreateConnections"
                :icon="mdiPlus"
                color="success"
                rounded-full
                small
                @click="createConnectionProfile(template.id)"
              />
            </SectionTitleLineWithButton>

            <BaseTable
              :current-page="
                childComponents.find(
                  (component) => component.name === 'connections',
                )?.currentPage
              "
              :per-page="
                childComponents.find(
                  (component) => component.name === 'connections',
                )?.perPage
              "
              :items-total="templateConnectionProfiles.count"
              :data="templateConnectionProfiles"
              :sort-column-key="
                childComponents.find(
                  (component) => component.name === 'connections',
                )?.sortColumnKey
              "
              :sort-direction="
                childComponents.find(
                  (component) => component.name === 'connections',
                )?.sortDirection
              "
              :loading="dataLoading"
              object-model="connections"
              :buttons="buttonsConnections"
              :search-bar-fields="connectionFields"
              :search-bar-max-filters="1"
              search-bar-query-key="filter-connections"
              :columns="[
                {
                  label: $t('common.label'),
                  key: 'label',
                  sortKey: 'objectId',
                },
                {
                  label: $t('views.templates.detail.username'),
                  key: 'username',
                },
                {
                  label: $t('views.templates.detail.protocol'),
                  key: 'protocol',
                  color: protocolColorConnection,
                  icon: (value) => connectionProtocolFormatterIcon(value),
                  formatter: (value) => String(value).toUpperCase(),
                },
              ]"
              @delete-object="(obj) => openDeleteConnectionProfileModal(obj)"
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
              @search-triggered="handleSearch"
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
              :reload="fetchTemplateTasks"
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
              :items-total="templateTasks.count"
              :data="templateTasks"
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
                { label: $t('common.name'), key: 'name' },
                {
                  label: $t('common.status'),
                  key: 'status',
                  color: statusColorTask,
                  icon: (value) => taskStatusIcon(value),
                  tooltip: (value) => taskStatusTooltip(value),
                  formatter: ['', ''],
                },
                {
                  label: $t('views.templates.detail.triggeredBy'),
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
              v-if="template.id && loadedTabs.has('changelogs')"
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
