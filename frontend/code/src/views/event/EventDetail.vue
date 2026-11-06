<script setup>
import {
  mdiAccount,
  mdiAlert,
  mdiCalendarEndOutline,
  mdiCalendarOutline,
  mdiClockPlusOutline,
  mdiCloudRefreshVariant,
  mdiContentCopy,
  mdiDelete,
  mdiDotsVertical,
  mdiFileTree,
  mdiFlash,
  mdiImport,
  mdiInformation,
  mdiLabel,
  mdiMailboxOutline,
  mdiMonitor,
  mdiPauseCircle,
  mdiPencil,
  mdiPlay,
  mdiPlaySpeed,
  mdiPlus,
  mdiPower,
  mdiRemoteDesktop,
  mdiRename,
  mdiRestart,
  mdiSchoolOutline,
  mdiServerNetwork,
  mdiShieldAccount,
  mdiSleep,
  mdiStop,
  mdiStopCircle,
  mdiTabPlus,
  mdiTabRemove,
  mdiTextBox,
  mdiVectorArrangeAbove,
} from '@mdi/js'
import VueDatePicker from '@vuepic/vue-datepicker'
import '@vuepic/vue-datepicker/dist/main.css'
import { computed, onMounted, onUnmounted, ref, toRaw, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtonDropdown from '@/components/BaseButtonDropdown.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseTab from '@/components/BaseTab.vue'
import BaseTable from '@/components/BaseTable.vue'
import BaseTabs from '@/components/BaseTabs.vue'
import BatchAddModal from '@/components/BatchAddModal.vue'
import BulkDeleteModal from '@/components/BulkDeleteModal.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxCloneModal from '@/components/CardBoxCloneModal.vue'
import CardBoxDeleteModal from '@/components/CardBoxDeleteModal.vue'
import CardBoxModal from '@/components/CardBoxModal.vue'
import CSVUpload from '@/components/CSVUpload.vue'
import EventStatus from '@/components/EventStatus.vue'
import EventWarningRollout from '@/components/EventWarningRollout.vue'
import EventWarningStop from '@/components/EventWarningStop.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import ObjectMetadataDisplay from '@/components/ObjectMetadataDisplay.vue'
import PillTag from '@/components/PillTag.vue'
import SearchControl from '@/components/SearchControl.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import {
  guacamoleSearchBarFields,
  mailSearchBarFields,
  templateSearchBarFields,
  vmSearchBarFields,
} from '@/components/Tables/searchBarFieldConfigs'
import { SearchOperators } from '@/components/Tables/searchOperators'
import TableChangelogs from '@/components/Tables/TableChangelogs.vue'
import TablePermissions from '@/components/Tables/TablePermissions.vue'
import { FIELD_LIMITS } from '@/config/fieldLimits'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { useMainStore } from '@/stores/main'
import { useStyleStore } from '@/stores/style.js'
import {
  checkObjectPermissions,
  emailStatusFormatter,
  eventActionsMapping,
  formatDate,
  resolveFieldFromLookup,
  usePermissionRefs,
  validateEventSlug,
} from '@/utils/dataUtils'
import {
  emailStatusIcon,
  eventStatusIcon,
  taskStatusIcon,
  vmStatusIcon,
} from '@/utils/icons'
import { statusColorEvent, statusColorMail } from '@/utils/objectColors'
import { statusColorTask, statusColorVM } from '@/utils/objectColors.js'
import { usePaginationChild } from '@/utils/pagination'
import { taskStatusTooltip } from '@/utils/tooltips'
import { useAutofocusInput } from '@/utils/useAutofocusInput'

const { t } = useI18n()
const permissionRefs = usePermissionRefs()

const modals = {
  addUsers: ref(false),
  addTemplate: ref(false),
  bulkAction: ref(false),
  bulkDeleteUsers: ref(false),
  cloneEvent: ref(false),
  deleteEvents: ref(false),
  deleteGuacamoles: ref(false),
  deleteUsers: ref(false),
  extendEvent: ref(false),
  importUsers: ref(false),
  rollout: ref(false),
  stopEvent: ref(false),
}
const allUsers = ref([])
const { autoFocusInputRef } = useAutofocusInput(modals.addUsers)
const checkedUsers = ref([])
const clonedEvent = ref({})
const dataLoading = ref(false)
const dataLoadingEvent = ref(true)
const mainStore = useMainStore()
const objectModel = 'Event'
const objToAdd = ref({
  roleId: mainStore?.settings?.roles?.students,
})
const objToRemove = ref({})
const permissionsLoaded = ref(false)
const router = useRouter()
const route = useRoute()
const searchControlVMRef = ref(null)
const toast = useToast()
const usersTableRef = ref(null)
const event = ref({})
const eventApps = ref([])
const moodleEnabled = computed(() => !!mainStore.settings?.moodle?.enabled)
const moodleBaseUrl = computed(() => mainStore.settings?.moodle?.url?.base)
const eventGuacamoles = ref([])
const eventMails = ref([])
const eventStatusChildKey = ref(0)
const eventTasks = ref([])
const eventTemplates = ref([])
const eventUsers = ref([])
const eventVMs = ref([])
const roles = ref([])

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
      fetchData: fetchEventApplications,
    },
    {
      name: 'guacamoles',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'name',
      sortDirection: 'asc',
      searchField: null,
      searchValue: null,
      fetchData: fetchEventGuacamoles,
    },
    {
      name: 'mails',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'createdAt',
      sortDirection: 'desc',
      searchField: null,
      searchValue: null,
      fetchData: fetchEventMails,
    },
    {
      name: 'tasks',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'createdAt',
      sortDirection: 'desc',
      fetchData: fetchEventTasks,
    },
    {
      name: 'templates',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'name',
      sortDirection: 'asc',
      searchField: null,
      searchValue: null,
      fetchData: fetchEventTemplates,
    },
    {
      name: 'users',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'user_id',
      sortDirection: 'asc',
      searchField: null,
      searchValue: null,
      fetchData: fetchEventUsers,
    },
    {
      name: 'vms',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'name',
      sortDirection: 'asc',
      searchField: null,
      searchValue: null,
      fetchData: fetchEventVMs,
    },
  ],
  fetchArgs: () => [route.params.id],
  modals,
  objToRemove,
  route,
})
/**/

const participantFields = [
  {
    preset: 'createdById',
    key: 'user_id',
    label: t('views.events.detail.columns.person'),
    operators: SearchOperators.EQUALS_ONLY_ONLY,
  },
  {
    key: 'role_id',
    label: t('views.events.detail.columns.role'),
    icon: mdiShieldAccount,
    operators: SearchOperators.EQUALS_ONLY_ONLY,
    options: [
      {
        value: mainStore.settings?.roles?.students,
        label: t('common.students'),
      },
      {
        value: mainStore.settings?.roles?.teachers,
        label: t('common.teachers'),
      },
    ],
  },
  { preset: 'createdById', operators: SearchOperators.EQUALS_ONLY_ONLY },
]
const guacamoleFields = guacamoleSearchBarFields({ exclude: ['eventId'] })
const vmFields = vmSearchBarFields({ exclude: ['event'] })
const templateFields = templateSearchBarFields()
const mailFields = mailSearchBarFields({ exclude: ['event'] })

const ACTION_DROPDOWN_DEFINITIONS = computed(() => [
  {
    id: 'eventRollout',
    label: t('views.events.detail.actions.rollout'),
    icon: mdiCloudRefreshVariant,
    action: 'rolloutEvent',
    permissionRef: 'canStart',
    shownOwn: ['geplant', 'core fehler', 'deployment fehler'],
    onClick: () => showModal('rollout', event.value.id),
  },
  {
    id: 'eventEdit',
    label: t('common.edit'),
    icon: mdiPencil,
    action: 'editEvent',
    permissionRef: 'canEdit',
    shownOwn: ['geplant', 'core fehler'],
    onClick: () => eventEdit(event.value.id),
  },
  {
    id: 'eventExtend',
    label: t('views.events.detail.actions.extendShorten'),
    icon: mdiCalendarEndOutline,
    action: 'extendEvent',
    permissionRef: 'canEdit',
    shownOwn: ['aktiv'],
    onClick: () => showModal('extendEvent', event.value.id),
  },
  {
    id: 'eventStop',
    label: t('views.events.detail.actions.stop'),
    icon: mdiStopCircle,
    action: 'stopEvent',
    permissionRef: 'canStop',
    shownOwn: ['aktiv', 'archival fehler'],
    onClick: () => showModal('stopEvent', event.value.id),
  },
  'divider',
  {
    id: 'vmsStart',
    label: t('views.events.detail.actions.vmsStart'),
    icon: mdiPlay,
    action: 'startVMs',
    permissionRef: 'canEdit',
    shownOwn: ['aktiv'],
  },
  {
    id: 'vmsPause',
    label: t('views.events.detail.actions.vmsPause'),
    icon: mdiPauseCircle,
    action: 'pauseVMs',
    permissionRef: 'canPause', // fixme: implement me
    shownOwn: ['aktiv'],
  },
  {
    id: 'vmsResume',
    label: t('views.events.detail.actions.vmsResume'),
    icon: mdiPlaySpeed,
    action: 'resumeVMs',
    permissionRef: 'canResume', // fixme: implement me
    shownOwn: ['aktiv'],
  },
  {
    id: 'vmsHibernate',
    label: t('views.events.detail.actions.vmsHibernate'),
    icon: mdiSleep,
    action: 'hibernateVMs',
    permissionRef: 'canHibernate', // fixme: implement me
    shownOwn: ['aktiv'],
  },
  {
    id: 'vmsShutdown',
    label: t('views.events.detail.actions.vmsShutdown'),
    icon: mdiPower,
    action: 'shutdownVMs',
    permissionRef: 'canEdit',
    shownOwn: ['aktiv'],
  },
  {
    id: 'vmsReboot',
    label: t('views.events.detail.actions.vmsReboot'),
    icon: mdiRestart,
    action: 'rebootVMs',
    permissionRef: 'canEdit',
    shownOwn: ['aktiv'],
  },
  {
    id: 'vmsStop',
    label: t('views.events.detail.actions.vmsStop'),
    icon: mdiStop,
    action: 'stopVMs',
    permissionRef: 'canEdit',
    shownOwn: ['aktiv'],
  },
  {
    id: 'vmsReset',
    label: t('views.events.detail.actions.vmsReset'),
    icon: mdiFlash,
    action: 'resetVMs',
    permissionRef: 'canEdit',
    shownOwn: ['aktiv'],
  },
  {
    id: 'vmsMigrate',
    label: t('views.events.detail.actions.vmsMigrate'),
    icon: mdiServerNetwork,
    action: 'migrateVMs',
    permissionRef: 'canMigrate', // fixme: implement me
    shownOwn: ['aktiv'],
  },
  'divider',
  {
    id: 'connectionsCreate',
    label: t('views.events.detail.actions.connectionsCreate'),
    icon: mdiTabPlus,
    action: 'createConnections',
    permissionRef: 'canEdit',
    shownOwn: ['aktiv'],
  },
  {
    id: 'connectionsDelete',
    label: t('views.events.detail.actions.connectionsDelete'),
    icon: mdiTabRemove,
    action: 'deleteConnections',
    permissionRef: 'canEdit',
    shownOwn: ['aktiv'],
  },
  'divider',
  {
    id: 'eventClone',
    label: t('common.clone'),
    icon: mdiContentCopy,
    action: 'cloneEvent',
    permissionRef: 'canCreate',
    onClick: () => showModal('cloneEvent', event.value.id),
  },
])

function onBatchAddUsers({ succeeded, failed, skipped }) {
  fetchEventUsers()
  if (failed === 0 && skipped === 0) {
    toast.success(
      t('views.events.detail.participants.addedCount', { n: succeeded }),
    )
  } else if (failed === 0) {
    toast.success(
      t('views.events.detail.participants.addedSkipped', {
        added: succeeded,
        skipped,
      }),
    )
  } else {
    toast.warning(
      t('views.events.detail.participants.addedPartial', {
        added: succeeded,
        total: succeeded + failed,
      }),
    )
  }
}

function onBulkDeleteUsers({ succeeded, failed }) {
  fetchEventUsers()
  usersTableRef.value?.clearCheckedRows()
  checkedUsers.value = []
  if (failed === 0) {
    toast.success(
      t('views.events.detail.participants.removedCount', { n: succeeded }),
    )
  } else {
    toast.warning(
      t('views.events.detail.participants.removedPartial', {
        removed: succeeded,
        total: succeeded + failed,
      }),
    )
  }
}

async function addTemplate(eventId, templateId) {
  try {
    await backend.events.addTemplate(eventId, templateId)
    fetchEventTemplates()
    toast.success(
      t('common.addSuccess', { entity: t('objectTypes.template.singular') }),
    )
  } catch (error) {
    toast.error(
      `${t('common.addError', { entity: t('objectTypes.template.singular') })}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  } finally {
    resetForm()
  }
}

async function bulkActionEvent(eventId, bulkAction) {
  try {
    const entry = eventActionsMapping[bulkAction]
    if (!entry) throw new Error(`Unknown action: ${bulkAction}`)

    const response = await backend.events.bulkAction(
      eventId,
      entry.type,
      entry.action,
    )

    toast.success(
      t('views.events.detail.bulkAction.started', {
        enqueued: response.enqueued,
        skipped: response.skipped?.length ?? 0,
      }),
      { timeout: 4200 },
    )

    fetchEvent()
  } catch (error) {
    const errorCode = error?.response?.data?.error_code
    const detail = String(error?.response?.data?.detail || '')

    if (errorCode === 'BULK_ACTION_REQUIREMENT_MISSING') {
      toast.info(t('views.events.detail.bulkAction.skipped'), {
        timeout: 4200,
      })
    } else {
      toast.error(
        `${t('views.events.detail.bulkAction.error')}\n${detail || error.message}`,
        { timeout: 8400 },
      )
    }
  } finally {
    resetForm()
  }
}

async function cloneEvent(event) {
  try {
    toast.info(t('views.events.detail.clone.inProgress'), { timeout: 4200 })
    const newEvent = await backend.events.create({
      name: event.name,
      description: event.description,
      dateStart: event.dateStart,
      dateEnd: event.dateEnd,
      course: event.course,
      slug: event.slug,
    })

    const tempUsersAll = ref([])
    await backend.events
      .getUsers(route.params.id, {
        page: 1,
        limit: 200,
      })
      .then(async (response) => {
        tempUsersAll.value = response.items
        tempUsersAll.value.count = response.pageDetails.totalCount

        if (tempUsersAll.value.count > 200) {
          toast.warning(t('views.events.detail.clone.tooManyUsers'), {
            timeout: 4200,
          })
        }
      })

    for (const t of tempUsersAll.value) {
      await backend.events.addUser(newEvent.id, t.user_id, t.role_id)
    }

    toast.success(t('views.events.detail.clone.success'))
    mainStore.fetchPermissions()
    router.push({ path: `/events/${newEvent.id}` })
  } catch (error) {
    toast.error(
      t('views.events.detail.clone.error') +
        '\n' +
        error?.response?.data?.detail,
    )
  }
}

const BLOCKING_VMS_LIMIT = 5
const blockingVms = ref([])
const blockingVmsTotal = ref(0)

async function openDeleteEventModal(eventObj) {
  blockingVms.value = []
  blockingVmsTotal.value = 0
  backend.beginSilent()
  try {
    const result = await backend.events.getVMs(eventObj.id, {
      page: 1,
      limit: BLOCKING_VMS_LIMIT,
    })
    blockingVms.value = result?.items ?? []
    blockingVmsTotal.value =
      result?.pageDetails?.totalCount ?? blockingVms.value.length
  } catch {
    // Fail open: the backend 409 pre-check still blocks the delete
  } finally {
    backend.endSilent()
  }
  modals.deleteEvents.value = true
}

const blockingVmRows = computed(() => {
  const items = blockingVms.value.map((vm) => ({
    label: vm.name ?? vm.id,
  }))
  const more = blockingVmsTotal.value - blockingVms.value.length
  if (more > 0) {
    items.push({
      label: t('views.events.delete.moreVms', { count: more }, more),
    })
  }
  return items
})

async function deleteEvent(eventId) {
  backend.beginSilent()
  try {
    await backend.events.delete(eventId)
    router.push({ path: `/events` })
    toast.success(
      t('common.deleteSuccess', { entity: t('objectTypes.event.singular') }),
    )
  } catch (error) {
    const errorCode = error?.response?.data?.error_code
    if (
      errorCode === 'OBJECT_IN_USE' ||
      errorCode === 'OBJECT_DELETE_INTEGRITY_ERROR'
    ) {
      toast.error(t('views.events.delete.blockedError'), { timeout: 8400 })
    } else {
      const detail = String(error?.response?.data?.detail || '')
      toast.error(
        `${t('common.deleteError', { entity: t('objectTypes.event.singular') })}${detail ? '\n' + detail : ''}`,
        { timeout: 8400 },
      )
    }
  } finally {
    backend.endSilent()
  }
}

async function deleteGuacamole(guacamoleToRemove) {
  try {
    await backend.guacamole.delete(guacamoleToRemove.id)
    fetchEventGuacamoles()
    toast.success(
      t('common.deleteSuccess', {
        entity: t('objectTypes.guacamole.singular'),
      }),
    )
  } catch (error) {
    toast.error(
      t('common.deleteError', { entity: t('objectTypes.guacamole.singular') }),
    )
  }
}

async function deleteUser(participantToRemove) {
  try {
    await backend.events.deleteUser(
      participantToRemove.event_id,
      participantToRemove.user_id,
      participantToRemove.role_id,
    )
    fetchEventUsers()
    toast.success(
      t('common.removeSuccess', { entity: t('objectTypes.user.singular') }),
    )
  } catch (error) {
    toast.error(
      `${t('common.removeError', { entity: t('objectTypes.participant.singular') })}\n${error?.response?.data?.detail}`,
    )
  }
}

backend.roles.eventRolesDropdown().then((response) => {
  roles.value = response
})

async function fetchEvent(isInitial = false) {
  try {
    if (isInitial) dataLoadingEvent.value = true

    const response = await backend.events.get(route.params.id)

    event.value = response

    if (event.value.dateEnd === '2099-12-31') {
      event.value.dateEnd = t('views.events.form.noEndDate')
    }

    event.value.courseId = event.value.course
    event.value.statusId = event.value.status
    if (isInitial) {
      objToAdd.value.newEndDate = event.value.dateEnd

      // fixme: this _could_ make the user clone an outdated object
      clonedEvent.value = structuredClone(toRaw(response))
      clonedEvent.value.name = ''
      clonedEvent.value.slug = ''
      clonedEvent.value.dateStart = '2099-01-01'
      clonedEvent.value.dateEnd = '2099-12-31'
    }

    await resolveFieldFromLookup(event.value, [
      { from: 'courseId', to: 'course', keyspace: 'courses' },
      { from: 'createdById', to: 'createdBy', keyspace: 'users' },
      {
        from: 'moodleCourseId',
        to: 'moodleCourse',
        keyspace: 'moodleCourses',
      },
      { from: 'statusId', to: 'status', keyspace: 'eventStatus' },
      { from: 'updatedById', to: 'updatedBy', keyspace: 'users' },
    ])

    event.value.statusName = event.value.status
    eventStatusChildKey.value = Math.random().toString(36).substring(2)
  } catch (error) {
    if (isInitial) {
      toast.warning(
        t('common.notFound', { entity: t('objectTypes.event.singular') }),
      )
      router.push({ path: `/events`, replace: true })
    }
  } finally {
    if (isInitial) dataLoadingEvent.value = false
  }
}

async function fetchEventApplications() {
  try {
    dataLoading.value = true

    const applicationsComponent = childComponents.value.find(
      (component) => component.name === 'applications',
    )
    await backend.events
      .getApplications(route.params.id, {
        page: applicationsComponent?.currentPage,
        limit: applicationsComponent?.perPage,
        sort_by: applicationsComponent?.sortColumnKey,
        sort_order: applicationsComponent?.sortDirection,
      })
      .then((response) => {
        eventApps.value = response.items
        eventApps.value.count = response.pageDetails.totalCount
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

async function fetchEventGuacamoles() {
  try {
    dataLoading.value = true

    const guacamolesComponent = childComponents.value.find(
      (component) => component.name === 'guacamoles',
    )
    await backend.events
      .getGuacamoles(route.params.id, {
        page: guacamolesComponent?.currentPage,
        limit: guacamolesComponent?.perPage,
        sort_by: guacamolesComponent?.sortColumnKey,
        sort_order: guacamolesComponent?.sortDirection,
        search_field: guacamolesComponent?.searchField,
        search_value: guacamolesComponent?.searchValue,
      })
      .then(async (response) => {
        eventGuacamoles.value = response.items
        eventGuacamoles.value.count = response.pageDetails.totalCount
        await resolveFieldFromLookup(eventGuacamoles.value, [
          { from: 'createdById', to: 'createdBy', keyspace: 'users' },
          { from: 'userId', to: 'user', keyspace: 'users' },
        ])
      })
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', {
        entities: t('objectTypes.guacamole.plural'),
      }),
    )
  } finally {
    dataLoading.value = false
  }
}

async function fetchEventMails() {
  try {
    dataLoading.value = true

    const mailsComponent = childComponents.value.find(
      (component) => component.name === 'mails',
    )
    await backend.mails
      .listByEvent(event.value.id ?? 'XXXXXXXXX-fixme', {
        page: mailsComponent?.currentPage,
        limit: mailsComponent?.perPage,
        sort_by: mailsComponent?.sortColumnKey,
        sort_order: mailsComponent?.sortDirection,
        search_field: mailsComponent?.searchField,
        search_value: mailsComponent?.searchValue,
      })
      .then(async (response) => {
        eventMails.value = response.items
        eventMails.value.count = response.pageDetails.totalCount
      })
  } catch (error) {
    toast.error(
      `${t('common.loadErrorPlural', { entities: t('objectTypes.mail.plural') })}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  } finally {
    dataLoading.value = false
  }
}

async function fetchEventUsers() {
  try {
    dataLoading.value = true

    const usersComponent = childComponents.value.find(
      (component) => component.name === 'users',
    )
    await backend.events
      .getUsers(route.params.id, {
        page: usersComponent?.currentPage,
        limit: usersComponent?.perPage,
        sort_by: usersComponent?.sortColumnKey,
        sort_order: usersComponent?.sortDirection,
        search_field: usersComponent?.searchField,
        search_value: usersComponent?.searchValue,
      })
      .then(async (response) => {
        eventUsers.value = response.items
        eventUsers.value.count = response.pageDetails.totalCount
        await resolveFieldFromLookup(eventUsers.value, [
          { from: 'createdById', to: 'createdBy', keyspace: 'users' },
          { from: 'role_id', to: 'role', keyspace: 'roles' },
          { from: 'user_id', to: 'username', keyspace: 'users' },
        ])
      })
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', { entities: t('objectTypes.user.plural') }) +
        '\n' +
        error?.response?.data?.detail,
    )
  } finally {
    dataLoading.value = false
  }
}

async function fetchEventTasks() {
  try {
    dataLoading.value = true

    const tasksComponent = childComponents.value.find(
      (component) => component.name === 'tasks',
    )
    await backend.tasks
      .list({
        page: tasksComponent?.currentPage,
        limit: tasksComponent?.perPage,
        sort_by: tasksComponent?.sortColumnKey,
        sort_order: tasksComponent?.sortDirection,
        search_field: 'event_id',
        search_value: route.params.id,
      })
      .then(async (response) => {
        eventTasks.value = response.items
        eventTasks.value.count = response.pageDetails.totalCount
        await resolveFieldFromLookup(eventTasks.value, [
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

async function fetchEventTemplates() {
  try {
    dataLoading.value = true

    const templatesComponent = childComponents.value.find(
      (component) => component.name === 'templates',
    )
    await backend.events
      .getTemplates(route.params.id, {
        page: templatesComponent?.currentPage,
        limit: templatesComponent?.perPage,
        sort_by: templatesComponent?.sortColumnKey,
        sort_order: templatesComponent?.sortDirection,
        search_field: templatesComponent?.searchField,
        search_value: templatesComponent?.searchValue,
      })
      .then(async (response) => {
        eventTemplates.value = response.items
        eventTemplates.value.count = response.pageDetails.totalCount
        await resolveFieldFromLookup(eventTemplates.value, [
          { from: 'os', to: 'osName', keyspace: 'os' },
        ])
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

async function fetchEventVMs() {
  try {
    dataLoading.value = true

    const vmsComponent = childComponents.value.find(
      (component) => component.name === 'vms',
    )
    await backend.events
      .getVMs(route.params.id, {
        page: vmsComponent?.currentPage,
        limit: vmsComponent?.perPage,
        sort_by: vmsComponent?.sortColumnKey,
        sort_order: vmsComponent?.sortDirection,
        search_field: vmsComponent?.searchField,
        search_value: vmsComponent?.searchValue,
      })
      .then((response) => {
        eventVMs.value = response.items
        eventVMs.value.count = response.pageDetails.totalCount
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

  if (modal == 'rollout') {
    handleTabChanged('users') // fixme: add all users, not only the paginated ones
  }

  if (modal == 'stopEvent') {
    handleTabChanged('guacamoles') // fixme: add all guacamoles, not only the paginated ones
    handleTabChanged('users') // fixme: add all users, not only the paginated ones
    handleTabChanged('vms') // fixme: add all vms, not only the paginated ones
  }
}

const eventEdit = (eventId) => {
  router.push({ path: `/events/${eventId}/edit` })
}

async function eventRollout(id) {
  try {
    if (String(event.value.status).toLowerCase().includes('fehler')) {
      // fixme
      await backend.events.rerollout(id)
    } else {
      await backend.events.start(id)
    }
    toast.success(t('views.events.detail.rollout.success'))
  } catch (error) {
    toast.error(
      `${t('views.events.detail.rollout.error')}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  } finally {
    await fetchEvent()
    // event users does not need any further permissions
    await fetchEventUsers()

    if (permissionRefs.canReadTasks) {
      await fetchEventTasks()
    }
  }
}

async function eventStop(id) {
  try {
    await backend.events.stop(id)
    fetchEvent()
    toast.success(t('views.events.detail.stopEvent.success'))
  } catch (error) {
    toast.error(
      `${t('views.events.detail.stopEvent.error')}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  }
}

async function eventExtend(id, newEndDate) {
  try {
    let dateEnd
    const parsedEndDate = new Date(newEndDate)
    if (newEndDate && !isNaN(parsedEndDate)) {
      dateEnd = parsedEndDate.toISOString().split('T')[0]
    } else {
      dateEnd = '2099-12-31'
    }
    await backend.events.extend(id, dateEnd)
    fetchEvent()
    toast.success(t('views.events.detail.extend.success'))
  } catch (error) {
    toast.error(
      `${t('views.events.detail.extend.error')}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  }
}

const actionColor = computed(
  () => bulkActionColors[objToRemove.value] || 'info',
)

const actionLabel = computed(
  () => bulkActionTexts.value[objToRemove.value] || '',
)

const bulkActionColors = {
  startVMs: 'success',
  shutdownVMs: 'danger',
  rebootVMs: 'danger',
  stopVMs: 'danger',
  resetVMs: 'danger',
  createConnections: 'success',
  deleteConnections: 'danger',
}

const bulkActionTexts = computed(() => ({
  startVMs: t('views.events.detail.bulkAction.texts.startVMs'),
  pauseVMs: t('views.events.detail.bulkAction.texts.pauseVMs'),
  resumeVMs: t('views.events.detail.bulkAction.texts.resumeVMs'),
  hibernateVMs: t('views.events.detail.bulkAction.texts.hibernateVMs'),
  shutdownVMs: t('views.events.detail.bulkAction.texts.shutdownVMs'),
  rebootVMs: t('views.events.detail.bulkAction.texts.rebootVMs'),
  stopVMs: t('views.events.detail.bulkAction.texts.stopVMs'),
  resetVMs: t('views.events.detail.bulkAction.texts.resetVMs'),
  migrateVMs: t('views.events.detail.bulkAction.texts.migrateVMs'),
  createConnections: t(
    'views.events.detail.bulkAction.texts.createConnections',
  ),
  deleteConnections: t(
    'views.events.detail.bulkAction.texts.deleteConnections',
  ),
}))

const bulkActionTitles = computed(() => ({
  startVMs: t('views.events.detail.bulkAction.titles.startVMs'),
  shutdownVMs: t('views.events.detail.bulkAction.titles.shutdownVMs'),
  rebootVMs: t('views.events.detail.bulkAction.titles.rebootVMs'),
  stopVMs: t('views.events.detail.bulkAction.titles.stopVMs'),
  resetVMs: t('views.events.detail.bulkAction.titles.resetVMs'),
  createConnections: t(
    'views.events.detail.bulkAction.titles.createConnections',
  ),
  deleteConnections: t(
    'views.events.detail.bulkAction.titles.deleteConnections',
  ),
}))

const getDisabledActions = (action) => {
  const s = event.value.statusName?.toLowerCase()

  const activeOnly = [
    'startVMs',
    'shutdownVMs',
    'rebootVMs',
    'stopVMs',
    'resetVMs',
    'createConnections',
    'deleteConnections',
    'extendEvent',
  ]

  if (activeOnly.includes(action)) return s !== 'aktiv'

  if (action === 'rolloutEvent')
    return (
      s !== 'geplant' &&
      !s?.includes('core fehler') &&
      !s?.includes('deployment fehler')
    )

  if (action === 'stopEvent')
    return s !== 'aktiv' && !s?.includes('archival fehler')

  return false
}

const dropdownItems = computed(() => {
  const items = ACTION_DROPDOWN_DEFINITIONS.value
    .map((item) => {
      if (item === 'divider') return { divider: true }

      if (item.permissionRef && !permissionRefs[item.permissionRef]) return null

      if (
        item.shownOwn &&
        !item.shownOwn.includes(event.value.statusName?.toLowerCase())
      )
        return null

      return {
        ...item,
        disabled: getDisabledActions(item.action),
        onClick: (...args) => {
          if (typeof item.onClick === 'function') {
            return item.onClick(...args)
          }
          showModal('bulkAction', item.action)
        },
      }
    })
    .filter(Boolean)

  const hasNonDivider = items.some((i) => !i.divider)
  return hasNonDivider ? items : []
})

const userHasAction = computed(() => dropdownItems.value.length !== 0)

const eventStatusTooltip = computed(() => {
  if (event.value?.deployment_status === null) {
    return t('views.events.detail.noDeploymentStatus')
  }
  return event.value?.deployment_status
})

const eventDeleteDisabled = computed(() => {
  return (
    event.value.status != 'Geplant' &&
    event.value.status != 'Archiviert' &&
    event.value.status != 'Core Fehler' &&
    event.value.status != 'Inaktiv'
  )
})

const eventDeleteTooltip = computed(() => {
  switch (event.value?.statusId?.toLowerCase()) {
    case 'f481fb68-4e6b-4027-bf67-ae431bd8b6d1': // aktiv
      return t('views.events.detail.deleteTooltip.mustEndFirst')
    case '53b6993a-57d6-40a6-8d42-e55bf08fac4c': // geplant
      return undefined
    case 'cbc20092-629b-483f-babc-ef26202d685e': // inaktiv
      return undefined
    case 'bfbee14d-6f04-4ba1-a39c-0f5764f0563d': // archiviert
      return undefined
    case '4d99fe64-3c3c-4a2f-99fe-643c3c1a2f23': // archiving
      return t('views.events.detail.deleteTooltip.mustArchiveFirst')
    case 'f13303bf-b25f-4869-9717-698a4db13ada': // deploying
      return t('views.events.detail.deleteTooltip.cannotDeleteDeploying')
    case '1fc851bf-5f4e-4937-bae9-c6d3fd0e5846': // stopped
      return t('views.events.detail.deleteTooltip.mustArchiveFirst')
    case 'f63a9362-eb67-4769-ba93-62eb67b76939': // core fehler
      return undefined
    case 'e5c9fafd-c5ec-4aa5-89fa-fdc5ec0aa595': // deployment fehler
      return t('views.events.detail.deleteTooltip.cannotDeleteStatus')
    case 'af12d859-9aa6-4fae-92d8-599aa6ffae93': // archival fehler
      return t('views.events.detail.deleteTooltip.cannotDeleteStatus')
  }
  return undefined
})

const buttonsParticipants = computed(() => {
  let perms = []
  if (permissionRefs.canReadUsers) {
    perms.push('view')
  }
  if (
    permissionRefs.canEdit &&
    ['Geplant', 'Aktiv', 'Inaktiv', 'Fehler'].includes(event.value.status)
  ) {
    perms.push('delete')
  }
  return perms
})

const buttonsConnections = computed(() => {
  if (permissionRefs.canDeleteConnections) return ['view', 'delete']
  return ['view']
})

const modalTitle = computed(
  () =>
    bulkActionTitles.value[objToRemove.value] ||
    t('views.events.detail.bulkAction.defaultTitle'),
)

const resetImportUserForm = () => {
  modals['importUsers'].value = false
  resetForm()
}

const resetForm = () => {
  objToAdd.value.templateId = ''
  objToAdd.value.roleId = mainStore?.settings?.roles?.students
  searchControlVMRef.value?.setInitialDisplay('')
  searchControlVMRef.value?.setSelectedId('')
}

const resetExtendEventForm = () => {
  objToAdd.value.newEndDate = event.value.dateEnd
}

async function loadAllUsers() {
  const limit = 200
  let page = 1
  let totalCount = 0
  const all = []

  while (true) {
    const response = await backend.users.list({ page, limit })
    all.push(...response.items)

    totalCount = response.pageDetails.totalCount
    if (all.length >= totalCount) break

    page++
  }

  allUsers.value = all
  allUsers.value.count = totalCount
}

async function importUser(row) {
  if (!row.email?.includes('@')) {
    throw new Error(t('views.events.detail.import.invalidEmail'))
  }

  // import users with role `students`
  const userRoleId = mainStore?.settings?.roles?.students

  // load all users if not already loaded
  if (!Array.isArray(allUsers.value) || allUsers.value.length === 0) {
    await loadAllUsers()
  }

  const foundUser = allUsers.value.find(
    (user) => user.email?.toLowerCase() === row.email?.toLowerCase(),
  )

  if (!foundUser) {
    throw new Error(t('views.events.detail.import.userNotFound'))
  }

  try {
    await backend.events.addUser(route.params.id, foundUser.id, userRoleId)
    return true
  } catch (error) {
    if (error?.response?.data?.detail) {
      throw new Error(error.response.data.detail)
    } else {
      throw new Error(t('views.events.detail.import.unknownError'))
    }
  }
}

async function importUserFinished() {
  fetchEventUsers()
}

const userImportHeadersCSV = [
  { key: 'email', label: t('views.users.form.emailShort') },
]

const viewUser = (obj, model) => {
  return router.push({ path: `/users/${obj.user_id}` })
}

const eventStatusAction = (action) => {
  switch (action) {
    case 'delete':
      return showModal('deleteEvents', event.value.id)
    case 'edit':
      return eventEdit(event.value.id)
    case 'extend':
      return showModal('extendEvent', event.value.id)
    case 'rollout':
      return showModal('rollout', event.value.id)
    case 'stop':
      return showModal('stopEvent', event.value.id)
    default:
      toast.warning(t('views.events.detail.unknownAction', { action }))
  }
}

async function loadEventAndPermissions(id) {
  await fetchEvent(true)

  await checkObjectPermissions(
    'events',
    id,
    permissionRefs,
    [
      {
        key: 'canStart',
        objectType: 'events',
        objectPermission: 'actions_start',
        objectPath: `/${id}`,
      },
      {
        key: 'canStop',
        objectType: 'events',
        objectPermission: 'actions_stop',
        objectPath: `/${id}`,
      },
      {
        key: 'canReadPermissions',
        objectType: 'object_permissions',
        objectPermission: 'read',
        objectPath: `/${id}`,
      },
      {
        key: 'canDeleteConnections',
        objectType: 'guacamoles',
        objectPermission: 'delete',
        objectPath: '/*',
      },
      {
        key: 'canUpdateTemplates',
        objectType: 'templates',
        objectPermission: 'update',
        objectPath: '/*',
      },
      {
        key: 'canReadCourse',
        objectType: 'courses',
        objectPermission: 'read',
        objectPath: `/${event.value.course}`,
      },
      {
        key: 'canReadConnectionProfiles',
        objectType: 'guacamole_connection_profiles',
        objectPermission: 'read',
        objectPath: '/*',
      },
      {
        key: 'canReadTasks',
        objectType: 'tasks',
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
        key: 'canReadUpdateTemplates',
        objectType: 'events',
        objectPermission: 'templates_update',
        objectPath: '/*',
      },
      {
        key: 'canReadMails',
        objectType: 'mails',
        objectPermission: 'read',
        objectPath: '/*',
      },
      {
        key: 'canReadChangelogs',
        objectType: 'changelogs',
        objectPermission: 'read',
        objectPath: '/*',
      },
    ],
    ['canCreate', 'canEdit', 'canDelete'],
  )
}

// TODO KVS-435
let intervalId
onMounted(async () => {
  await loadEventAndPermissions(route.params.id)

  intervalId = setInterval(() => {
    fetchEvent(false)
    refreshActiveTab()
  }, 15000)

  permissionsLoaded.value = true
})

onUnmounted(() => {
  clearInterval(intervalId)
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
      await loadEventAndPermissions(newId)
    } finally {
      permissionsLoaded.value = true
      dataLoading.value = false
    }
  },
)

// Reset role selection when the add-users modal closes
watch(
  () => modals.addUsers.value,
  (isOpen) => {
    if (!isOpen) resetForm()
  },
)
</script>

<template>
  <!-- Add users to event (batch) -->
  <BatchAddModal
    v-model="modals.addUsers.value"
    :title="$t('views.events.detail.participants.addTitle')"
    :fetch-data="backend.users.search"
    :execute="
      (item) => backend.events.addUser(event.id, item.id, objToAdd.roleId)
    "
    :search-icon="mdiAccount"
    :search-label="$t('views.events.detail.participants.searchLabel')"
    :batch-size="3"
    :is-skippable="
      (err) => err?.response?.data?.error_code === 'DUPLICATE_EVENT_USER_ROLE'
    "
    :begin-silent="() => backend.beginSilent()"
    :end-silent="() => backend.endSilent()"
    @saved="onBatchAddUsers"
  >
    <template #warning>
      <NotificationBar
        v-if="event.status == 'Aktiv'"
        :dismissable="false"
        color="warning"
        :icon="mdiInformation"
      >
        <p>
          <b>{{ $t('views.events.detail.warnings.eventAlreadyActive') }}</b>

          <br />
          {{ $t('views.events.detail.warnings.addUserTriggersCreation') }}
          <template v-if="moodleEnabled && event.moodleCourseId != null">
            <br />{{
              $t('views.events.detail.warnings.addUserMoodleEnrollment')
            }}
          </template>
        </p>
      </NotificationBar>
    </template>

    <template #options>
      <FormField :label="$t('views.events.detail.participants.selectRole')">
        <div class="flex gap-x-4 flex-wrap">
          <label
            v-for="role in roles"
            :key="role.value"
            class="flex items-center space-x-2 cursor-pointer"
          >
            <input
              v-model="objToAdd.roleId"
              type="radio"
              class="form-radio"
              :value="role.value"
            />

            <span>{{ role.label }}</span>
          </label>
        </div>
      </FormField>
    </template>
  </BatchAddModal>

  <!-- Add template to event-->
  <CardBoxModal
    v-model="modals.addTemplate.value"
    form
    has-search
    :title="$t('views.events.detail.templates.addTitle')"
    button="success"
    has-cancel
    :button-label="$t('common.add')"
    @cancel="resetForm()"
    @form-submitted="addTemplate(event.id, objToAdd.templateId)"
  >
    <NotificationBar :dismissable="false" color="info" :icon="mdiInformation">
      <p>
        <b>
          {{ $t('views.events.detail.templates.cannotRemoveWarning') }}
        </b>
      </p>
    </NotificationBar>

    <NotificationBar
      v-if="event.status == 'Aktiv'"
      :dismissable="false"
      color="warning"
      :icon="mdiInformation"
    >
      <p>
        <b>
          {{ $t('views.events.detail.warnings.eventAlreadyActive') }}

          <br />{{
            $t('views.events.detail.warnings.addTemplateTriggersCreation')
          }}</b
        >
      </p>
    </NotificationBar>

    <FormField :label="$t('views.events.detail.templates.selectTemplate')">
      <SearchControl
        v-model="objToAdd.templateId"
        :fetch-data="backend.templates.search"
        :icon="mdiVectorArrangeAbove"
        required
        @set-ref="
          (ref) => {
            searchControlVMRef = ref
            autoFocusInputRef = ref
          }
        "
      />
    </FormField>
  </CardBoxModal>

  <!-- Bulk action -->
  <CardBoxModal
    v-model="modals.bulkAction.value"
    form
    has-search
    :title="modalTitle"
    :button="actionColor"
    has-cancel
    :button-label="$t('common.confirm')"
    @cancel="resetForm()"
    @form-submitted="bulkActionEvent(event.id, objToRemove)"
  >
    <NotificationBar :dismissable="false" color="info" :icon="mdiInformation">
      <p class="text-sm leading-relaxed">
        <b>{{ actionLabel }}</b>
      </p>
    </NotificationBar>
  </CardBoxModal>

  <!-- Modal: Clone event -->
  <CardBoxCloneModal
    v-model="modals.cloneEvent.value"
    :name="event.name"
    :checkvalue="event.name"
    @form-submitted="cloneEvent(clonedEvent)"
  >
    <NotificationBar :dismissable="false" color="info" :icon="mdiInformation">
      {{ $t('views.events.detail.clone.participantsIncluded') }}
    </NotificationBar>

    <FormField
      :label="$t('views.events.detail.clone.newName')"
      :help="$t('views.events.form.nameHelp')"
    >
      <FormControl
        v-model="clonedEvent.name"
        :icon="mdiRename"
        :maxlength="FIELD_LIMITS.event.name"
        :placeholder="$t('views.events.form.namePlaceholder')"
        required
      />
    </FormField>

    <FormField
      :label="$t('views.events.detail.clone.newSlug')"
      :help="$t('views.events.form.slugHelp')"
      :tooltip="$t('views.events.form.slugTooltip')"
    >
      <FormControl
        v-model="clonedEvent.slug"
        :icon="mdiLabel"
        :validate="(val) => validateEventSlug(val)"
        :maxlength="FIELD_LIMITS.event.slug"
        :placeholder="$t('views.events.form.slugPlaceholder')"
        required
      />
    </FormField>
  </CardBoxCloneModal>

  <!-- Import users to event -->
  <CardBoxModal
    v-model="modals.importUsers.value"
    :title="$t('views.events.detail.import.title')"
    :has-button="false"
    has-search
    :scrollable="true"
    custom-class="!w-[70vw] !h-[80vh]"
    @cancel="resetImportUserForm()"
  >
    <CSVUpload
      :required-mappings="userImportHeadersCSV"
      :on-import-confirm="importUser"
      :on-finish="importUserFinished"
      :emit-on-close="true"
      :limit="200"
      @closed="resetImportUserForm()"
    />
  </CardBoxModal>

  <!-- Delete event-->
  <CardBoxDeleteModal
    v-model="modals.deleteEvents.value"
    :name="event.name"
    :checkvalue="event.name"
    :blocked="blockingVmsTotal > 0"
    :warning="
      blockingVmsTotal > 0
        ? $t(
            'views.events.delete.relatedWarning',
            { count: blockingVmsTotal },
            blockingVmsTotal,
          )
        : null
    "
    :related-items="blockingVmRows"
    :related-label="$t('views.events.delete.relatedLabel')"
    :related-count="blockingVmsTotal"
    @form-submitted="deleteEvent(event.id)"
  />

  <!-- Delete user from event-->
  <CardBoxModal
    v-model="modals.deleteUsers.value"
    :title="$t('views.events.detail.participants.confirmAction')"
    button="danger"
    :button-label="$t('common.remove')"
    :has-cancel="true"
    :has-button="true"
    :disabled="false"
    @form-submitted="deleteUser(objToRemove)"
  >
    <!-- Warning if event is active -->
    <NotificationBar
      v-if="event?.status?.toLowerCase() == 'aktiv'"
      :dismissable="false"
      color="danger"
      :icon="mdiAlert"
    >
      <b>{{ $t('views.events.detail.warnings.removeUserDeletesVMs') }}</b>

      <template v-if="moodleEnabled && event.moodleCourseId != null">
        <br />

        <b>{{
          $t('views.events.detail.warnings.removeUserMoodleUnenrollment')
        }}</b>
      </template>
    </NotificationBar>

    <div>
      <p>
        {{
          $t('views.events.detail.participants.removeConfirm', {
            username: objToRemove.username,
            eventName: event.name,
          })
        }}
      </p>

      <br />

      <p>{{ $t('views.events.detail.participants.areYouSure') }}</p>
    </div>
  </CardBoxModal>

  <!-- Bulk delete users from event -->
  <BulkDeleteModal
    v-model="modals.bulkDeleteUsers.value"
    :items="checkedUsers"
    :execute="
      (item) =>
        backend.events.deleteUser(item.event_id, item.user_id, item.role_id)
    "
    label-key="username"
    :begin-silent="() => backend.beginSilent()"
    :end-silent="() => backend.endSilent()"
    @completed="onBulkDeleteUsers"
  >
    <template #warning>
      <NotificationBar
        v-if="event?.status?.toLowerCase() === 'aktiv'"
        :dismissable="false"
        color="danger"
        :icon="mdiAlert"
      >
        <b>
          {{ $t('views.events.detail.warnings.removeUsersDeletesVMs') }}
        </b>

        <template v-if="moodleEnabled && event.moodleCourseId != null">
          <br />

          <b>{{
            $t('views.events.detail.warnings.removeUserMoodleUnenrollment')
          }}</b>
        </template>
      </NotificationBar>
    </template>

    <template #description>
      <p class="text-sm text-gray-700 dark:text-gray-300">
        {{
          $t('views.events.detail.participants.bulkRemoveDescription', {
            eventName: event.name,
          })
        }}
      </p>
    </template>
  </BulkDeleteModal>

  <!-- Delete guacamole from event-->
  <CardBoxDeleteModal
    v-model="modals.deleteGuacamoles.value"
    :name="objToRemove.name"
    :checkvalue="objToRemove.name"
    @form-submitted="deleteGuacamole(objToRemove)"
  />

  <!-- Extend event-->
  <CardBoxModal
    v-model="modals.extendEvent.value"
    form
    :title="$t('views.events.detail.extend.title')"
    button="success"
    has-cancel
    has-search
    :disabled="objToAdd.newEndDate == event.dateEnd"
    :button-label="$t('views.events.detail.extend.adjust')"
    @cancel="resetExtendEventForm()"
    @form-submitted="eventExtend(event.id, objToAdd.newEndDate)"
  >
    <NotificationBar
      :dismissable="false"
      color="warning"
      :icon="mdiInformation"
    >
      <p>
        <b>
          {{ $t('views.events.detail.extend.warning') }}
        </b>
      </p>
    </NotificationBar>

    <FormField
      :label="$t('views.events.detail.extend.newEndDate')"
      :help="$t('views.events.detail.extend.newEndDateHelp')"
    >
      <VueDatePicker
        v-model="objToAdd.newEndDate"
        utc="preserve"
        :enable-time-picker="false"
        text-input
        :month-change-on-scroll="false"
        :clearable="true"
        :placeholder="$t('views.events.form.datePickerPlaceholder')"
        :min-date="new Date()"
        format="EEE, dd.MM.yyyy"
        locale="de"
        week-numbers="iso"
        auto-apply
        :dark="useStyleStore().darkMode"
        :required="true"
      />
    </FormField>
  </CardBoxModal>

  <!-- (Re-)Rollout event -->
  <EventWarningRollout
    v-model="modals.rollout.value"
    :scrollable="true"
    :object="event"
    :permissions="permissionRefs"
    :total-participants="eventUsers.count"
    @confirmed="eventRollout(event.id)"
  />

  <!-- Stop event-->
  <EventWarningStop
    v-model="modals.stopEvent.value"
    :scrollable="true"
    :object="event"
    @confirmed="eventStop(event.id)"
  />

  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiCalendarOutline"
        :title="event.name ? event.name : 'Loading...'"
        :object-model="$t('objectTypes.event.singular')"
        main
        docs-path="/docs/usage/openvle/events/"
      >
        <BaseButtons type="justify-start lg:justify-end">
          <!-- Event status -->
          <PillTag
            v-if="event.status"
            v-tooltip="eventStatusTooltip"
            disabled
            :label="event.status"
            :color="statusColorEvent(event.status)"
            :icon="eventStatusIcon(event.status)"
          />

          <!-- Event actions dropdown-->
          <BaseButtonDropdown
            v-if="userHasAction"
            :label="$t('common.actions')"
            :icon="mdiDotsVertical"
            :dropdown-items="dropdownItems"
            :disabled="false"
            :rounded-full="true"
            color="info"
            small
          />

          <!-- Event delete button -->
          <BaseButton
            v-if="event.id && permissionRefs.canDelete"
            v-tooltip="eventDeleteTooltip"
            target="_blank"
            :icon="mdiDelete"
            :label="$t('common.delete')"
            color="danger"
            rounded-full
            small
            :disabled="eventDeleteDisabled"
            @click="openDeleteEventModal(event)"
          />
        </BaseButtons>
      </SectionTitleLineWithButton>

      <p
        class="text-xs text-right text-slate-400 dark:text-slate-500 -mt-4 mb-4"
      >
        {{ $t('common.autoRefresh', { seconds: 15 }) }}
      </p>

      <CardBox>
        <BaseTabs v-if="permissionsLoaded" @tab-changed="handleTabChanged">
          <BaseTab id="event" :title="$t('objectTypes.event.singular')">
            <div class="flex gap-4">
              <FormField
                :label="$t('common.name')"
                :help="$t('views.events.form.nameHelp')"
                class="w-[65%]"
              >
                <FormControl
                  v-model="event.name"
                  :icon="mdiRename"
                  :maxlength="FIELD_LIMITS.event.name"
                  disabled
                />
              </FormField>

              <FormField
                :label="$t('views.events.form.slug')"
                :help="$t('views.events.form.slugHelp')"
                class="w-[35%]"
              >
                <FormControl
                  v-model="event.slug"
                  :icon="mdiLabel"
                  :maxlength="FIELD_LIMITS.event.slug"
                  disabled
                />
              </FormField>
            </div>

            <FormField
              :label="$t('common.description')"
              :help="$t('views.events.form.descriptionHelp')"
            >
              <FormControl
                v-model="event.description"
                :icon="mdiTextBox"
                disabled
              />
            </FormField>

            <FormField :label="$t('views.events.form.course')">
              <FormControl
                v-model="event.course"
                :icon="mdiSchoolOutline"
                :link="`/courses/${event.courseId}`"
                disabled
              />
            </FormField>

            <!-- Moodle course (feature-gated, read-only) -->
            <FormField
              v-if="moodleEnabled && event.moodleCourseId != null"
              :label="$t('views.events.detail.moodleCourse')"
            >
              <FormControl
                :model-value="event.moodleCourse"
                :icon="mdiSchoolOutline"
                :link="
                  moodleBaseUrl
                    ? `${moodleBaseUrl}/course/view.php?id=${event.moodleCourseId}`
                    : undefined
                "
                disabled
              />
            </FormField>

            <FormField>
              <FormField
                :label="$t('views.events.form.dateStart')"
                :help="$t('views.events.form.dateStartHelp')"
              >
                <FormControl
                  v-if="event.status === 'Geplant'"
                  :model-value="
                    formatDate(event?.dateStart, {
                      weekday: 'long',
                      day: '2-digit',
                      month: '2-digit',
                      year: 'numeric',
                      hour12: false,
                    }) +
                    ' (- ' +
                    mainStore?.settings?.events?.start?.prep_time?.days +
                    ' ' +
                    $t('views.events.form.preparationDays') +
                    ')'
                  "
                  :icon="mdiClockPlusOutline"
                  disabled
                />

                <FormControl
                  v-else
                  :model-value="
                    formatDate(event?.dateStart, {
                      weekday: 'long',
                      day: '2-digit',
                      month: '2-digit',
                      year: 'numeric',
                      hour12: false,
                    })
                  "
                  :icon="mdiClockPlusOutline"
                  disabled
                />
              </FormField>

              <FormField
                :label="$t('views.events.form.dateEnd')"
                :help="$t('views.events.form.dateEndHelp')"
                :tooltip="$t('views.events.form.dateEndArchiveTooltip')"
              >
                <FormControl
                  v-if="event.dateEnd === $t('views.events.form.noEndDate')"
                  :model-value="event.dateEnd"
                  :icon="mdiClockPlusOutline"
                  disabled
                />

                <FormControl
                  v-else-if="
                    event.status != 'Archiving' &&
                    event.status != 'Archiviert' &&
                    event.status != 'Archival Fehler'
                  "
                  :model-value="
                    formatDate(event?.dateEnd, {
                      weekday: 'long',
                      day: '2-digit',
                      month: '2-digit',
                      year: 'numeric',
                      hour12: false,
                    }) +
                    ' (+ ' +
                    mainStore?.settings?.events?.end?.prep_time?.days +
                    ' ' +
                    $t('views.events.form.transitionDays') +
                    ')'
                  "
                  :icon="mdiClockPlusOutline"
                  disabled
                />

                <FormControl
                  v-else
                  :model-value="
                    formatDate(event?.dateEnd, {
                      weekday: 'long',
                      day: '2-digit',
                      month: '2-digit',
                      year: 'numeric',
                      hour12: false,
                    })
                  "
                  :icon="mdiClockPlusOutline"
                  disabled
                />
              </FormField>
            </FormField>

            <ObjectMetadataDisplay
              v-if="loadedTabs.has('event') && event.id"
              :object="event"
              :object-type="objectModel"
              :object-id="route.params.id"
              :can-edit="permissionRefs.canEdit"
              :tags-help="$t('views.events.detail.tagsHelp')"
            />
          </BaseTab>

          <BaseTab id="status" :title="$t('common.status')">
            <EventStatus
              v-if="event"
              :key="eventStatusChildKey"
              :event="event"
              :user-permissions="{
                edit: permissionRefs.canEdit,
                delete: permissionRefs.canDelete,
                rollout: permissionRefs.canStart,
                stop: permissionRefs.canStop,
              }"
              @action="eventStatusAction"
              @reload="fetchEvent"
            />
          </BaseTab>

          <BaseTab id="users" :title="$t('common.participants')">
            <SectionTitleLineWithButton
              :icon="mdiAccount"
              :title="$t('common.participants')"
              :reload="() => fetchEventUsers()"
            >
              <BaseButton
                v-if="
                  checkedUsers.length > 0 &&
                  permissionRefs.canEdit &&
                  ['Geplant', 'Aktiv', 'Inaktiv', 'Fehler'].includes(
                    event.status,
                  )
                "
                :icon="mdiDelete"
                :label="
                  $t('views.events.detail.participants.removeCount', {
                    n: checkedUsers.length,
                  })
                "
                color="danger"
                rounded-full
                small
                @click="modals.bulkDeleteUsers.value = true"
              />

              <BaseButton
                v-if="permissionRefs.canEdit && permissionRefs.canReadUsers"
                :icon="mdiImport"
                :label="$t('common.import')"
                color="info"
                rounded-full
                small
                :disabled="
                  !['Geplant', 'Aktiv', 'Inaktiv', 'Fehler'].includes(
                    event.status,
                  )
                "
                @click="showModal('importUsers')"
              />

              <BaseButton
                v-if="permissionRefs.canEdit && permissionRefs.canReadUsers"
                :icon="mdiPlus"
                color="success"
                rounded-full
                small
                :disabled="
                  !['Geplant', 'Aktiv', 'Inaktiv', 'Fehler'].includes(
                    event.status,
                  )
                "
                @click="showModal('addUsers')"
              />
            </SectionTitleLineWithButton>

            <BaseTable
              v-if="loadedTabs.has('users')"
              ref="usersTableRef"
              :current-page="
                childComponents.find((component) => component.name === 'users')
                  ?.currentPage
              "
              :per-page="
                childComponents.find((component) => component.name === 'users')
                  ?.perPage
              "
              :items-total="eventUsers.count"
              :data="eventUsers"
              :sort-column-key="
                childComponents.find((component) => component.name === 'users')
                  ?.sortColumnKey
              "
              :sort-direction="
                childComponents.find((component) => component.name === 'users')
                  ?.sortDirection
              "
              :loading="dataLoading"
              object-model="users"
              :buttons="buttonsParticipants"
              :emit-view-object="true"
              :search-bar-fields="participantFields"
              :search-bar-max-filters="1"
              search-bar-query-key="filter-users"
              :checkable="
                permissionRefs.canEdit &&
                ['Geplant', 'Aktiv', 'Inaktiv', 'Fehler'].includes(event.status)
              "
              :columns="[
                {
                  label: $t('views.events.detail.columns.person'),
                  key: 'username',
                  sortKey: 'user_id',
                },
                {
                  label: $t('views.events.detail.columns.role'),
                  key: 'role',
                  sortKey: 'role_id',
                },
                {
                  label: $t('views.events.detail.columns.createdBy'),
                  key: 'createdBy',
                  sortKey: 'createdById',
                  class:
                    'sm:flex-row gap-0.5 sm:gap-1 flex flex-col sm:flex-row sm:gap-0.5',
                },
              ]"
              @view-object="viewUser"
              @delete-object="handleDeleteObject"
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
              @search-triggered="handleSearch"
              @checked-rows-change="checkedUsers = $event"
            />
          </BaseTab>

          <BaseTab id="guacamoles" :title="$t('objectTypes.guacamole.plural')">
            <SectionTitleLineWithButton
              :icon="mdiRemoteDesktop"
              :title="$t('objectTypes.guacamole.plural')"
              :reload="fetchEventGuacamoles"
            >
            </SectionTitleLineWithButton>

            <BaseTable
              v-if="loadedTabs.has('guacamoles')"
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
              :items-total="eventGuacamoles.count"
              :data="eventGuacamoles"
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
              :buttons="buttonsConnections"
              :search-bar-fields="guacamoleFields"
              :search-bar-max-filters="1"
              search-bar-query-key="filter-guacamoles"
              :columns="[
                { label: $t('common.name'), key: 'name' },
                {
                  label: $t('views.events.detail.columns.person'),
                  key: 'user',
                  sortKey: 'userId',
                },
                {
                  label: $t('views.events.detail.columns.createdBy'),
                  key: 'createdBy',
                  sortKey: 'createdById',
                  class:
                    'sm:flex-row gap-0.5 sm:gap-1 flex flex-col sm:flex-row sm:gap-0.5',
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
              :title="$t('objectTypes.virtualMachine.plural')"
              :reload="fetchEventVMs"
            >
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
              :items-total="eventVMs.count"
              :data="eventVMs"
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

          <BaseTab
            v-if="permissionRefs.canReadUpdateTemplates"
            id="templates"
            :title="$t('objectTypes.template.plural')"
          >
            <SectionTitleLineWithButton
              :icon="mdiVectorArrangeAbove"
              :title="$t('objectTypes.template.plural')"
              :reload="fetchEventTemplates"
            >
              <BaseButton
                :icon="mdiPlus"
                color="success"
                rounded-full
                small
                :disabled="
                  !['Geplant', 'Aktiv', 'Inaktiv'].includes(event.status)
                "
                @click="showModal('addTemplate')"
              />
            </SectionTitleLineWithButton>

            <NotificationBar
              :dismissable="false"
              color="info"
              :icon="mdiInformation"
            >
              {{ $t('views.events.detail.templates.infoNotice') }}
            </NotificationBar>

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
              :items-total="eventTemplates.count"
              :data="eventTemplates"
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
                  label: $t('views.templates.form.cpuCores'),
                  key: 'cpu',
                  formatter: (value) => value + ' Cores',
                },
                {
                  label: $t('common.ram'),
                  key: 'ram',
                  formatter: (value) => Number(value) / 1024 + ' GB',
                },
                {
                  label: $t('views.events.detail.columns.os'),
                  key: 'osName',
                  sortKey: 'os',
                },
              ]"
              @delete-object="handleDeleteObject"
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
              @search-triggered="handleSearch"
            />
          </BaseTab>

          <BaseTab
            v-if="permissionRefs.canReadTasks"
            id="tasks"
            :title="$t('objectTypes.task.plural')"
          >
            <SectionTitleLineWithButton
              :icon="mdiFileTree"
              :title="$t('objectTypes.task.plural')"
              :reload="fetchEventTasks"
            >
            </SectionTitleLineWithButton>

            <NotificationBar
              :dismissable="false"
              color="info"
              :icon="mdiInformation"
            >
              <b>{{ $t('views.events.detail.tasks.infoNotice') }}</b>
            </NotificationBar>

            <BaseTable
              v-if="eventTasks"
              :current-page="
                childComponents.find((component) => component.name === 'tasks')
                  ?.currentPage
              "
              :per-page="
                childComponents.find((component) => component.name === 'tasks')
                  ?.perPage
              "
              :items-total="eventTasks.count"
              :data="eventTasks"
              :sort-column-key="
                childComponents.find((component) => component.name === 'tasks')
                  ?.sortColumnKey
              "
              :sort-direction="
                childComponents.find((component) => component.name === 'tasks')
                  ?.sortDirection
              "
              :loading="dataLoading"
              object-model="tasks"
              :buttons="['view']"
              :columns="[
                {
                  label: $t('common.name'),
                  key: 'name',
                  width: '450px',
                },
                {
                  label: $t('common.status'),
                  key: 'status',
                  color: statusColorTask,
                  icon: (value) => taskStatusIcon(value),
                  tooltip: (value) => taskStatusTooltip(value),
                  formatter: ['', ''],
                },
                {
                  label: $t('views.events.detail.columns.triggeredBy'),
                  key: 'createdBy',
                  sortKey: 'createdById',
                },
              ]"
              @delete-object="handleDeleteObject"
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
            />
          </BaseTab>

          <BaseTab id="mails" :title="$t('objectTypes.mail.plural')">
            <SectionTitleLineWithButton
              :icon="mdiMailboxOutline"
              :title="$t('objectTypes.mail.plural')"
              :reload="fetchEventMails"
            />

            <BaseTable
              v-if="loadedTabs.has('mails')"
              :current-page="
                childComponents.find((component) => component.name === 'mails')
                  ?.currentPage
              "
              :per-page="
                childComponents.find((component) => component.name === 'mails')
                  ?.perPage
              "
              :items-total="eventMails.count"
              :data="eventMails"
              :sort-column-key="
                childComponents.find((component) => component.name === 'mails')
                  ?.sortColumnKey
              "
              :sort-direction="
                childComponents.find((component) => component.name === 'mails')
                  ?.sortDirection
              "
              :loading="dataLoading"
              object-model="mails"
              :buttons="[permissionRefs.canReadMails ? 'view' : '']"
              :search-bar-fields="mailFields"
              :search-bar-max-filters="1"
              search-bar-query-key="filter-mails"
              :columns="[
                {
                  label: $t('views.events.detail.columns.subject'),
                  key: 'subject',
                },
                {
                  label: $t('views.events.detail.columns.recipient'),
                  key: 'toMail',
                  width: '320px',
                },
                {
                  label: $t('common.status'),
                  key: 'sendStatus',
                  color: statusColorMail,
                  icon: (value) => emailStatusIcon(value),
                  formatter: (value) => emailStatusFormatter(value),
                  width: '170px',
                },
              ]"
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
              v-if="event.id && loadedTabs.has('changelogs')"
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

<style>
.dp__theme_dark {
  --dp-background-color: rgb(30 41 59);
}
</style>
