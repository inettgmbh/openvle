<script setup>
import {
  mdiAccountBox,
  mdiAlert,
  mdiApplicationBrackets,
  mdiApps,
  mdiCalendarOutline,
  mdiChartBar,
  mdiContentCopy,
  mdiCpu64Bit,
  mdiDelete,
  mdiDotsVertical,
  mdiFileTree,
  mdiFlash,
  mdiHarddisk,
  mdiInformation,
  mdiIp,
  mdiLock,
  mdiLockOpen,
  mdiMemory,
  mdiMonitor,
  mdiPencil,
  mdiPlay,
  mdiPlus,
  mdiPower,
  mdiReload,
  mdiRemoteDesktop,
  mdiRename,
  mdiRestart,
  mdiServer,
  mdiShieldHalfFull,
  mdiShieldRemove,
  mdiStop,
  mdiVectorArrangeAbove,
} from '@mdi/js'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtonDropdown from '@/components/BaseButtonDropdown.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseDivider from '@/components/BaseDivider.vue'
import BaseMarkdown from '@/components/BaseMarkdown.vue'
import BaseTab from '@/components/BaseTab.vue'
import BaseTable from '@/components/BaseTable.vue'
import BaseTabs from '@/components/BaseTabs.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxComponentHeader from '@/components/CardBoxComponentHeader.vue'
import CardBoxDeleteModal from '@/components/CardBoxDeleteModal.vue'
import CardBoxDeleteRelationModal from '@/components/CardBoxDeleteRelationModal.vue'
import CardBoxModal from '@/components/CardBoxModal.vue'
import FormCheckRadio from '@/components/FormCheckRadio.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import ImportConnectionProfileModal from '@/components/ImportConnectionProfileModal.vue'
import MetricsSelectionPanel from '@/components/MetricsSelectionPanel.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import ObjectMetadataDisplay from '@/components/ObjectMetadataDisplay.vue'
import PillTag from '@/components/PillTag.vue'
import ProxmoxRrdChart from '@/components/ProxmoxRrdChart.vue'
import SearchControl from '@/components/SearchControl.vue'
import SearchModal from '@/components/SearchModal.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import SpecCard from '@/components/SpecCard.vue'
import {
  applicationSearchBarFields,
  connectionSearchBarFields,
} from '@/components/Tables/searchBarFieldConfigs'
import TableChangelogs from '@/components/Tables/TableChangelogs.vue'
import TablePermissions from '@/components/Tables/TablePermissions.vue'
import { FIELD_LIMITS, FIELD_VALUE_LIMITS } from '@/config/fieldLimits'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { useMainStore } from '@/stores/main'
import {
  checkObjectPermissions,
  connectionProfileLabelFormatter,
  resolveFieldFromLookup,
  usePermissionRefs,
} from '@/utils/dataUtils'
import {
  connectionProtocolFormatterIcon,
  eventCreateTypeIcon,
  haStateIconVM,
  taskStatusIcon,
  vmStatusIcon,
} from '@/utils/icons'
import {
  createTypeColorConnection,
  protocolColorConnection,
  statusColorTask,
  statusColorVM,
} from '@/utils/objectColors.js'
import { usePaginationChild } from '@/utils/pagination'
import { eventCreateTypeTooltip, taskStatusTooltip } from '@/utils/tooltips'
import { useAutofocusInput } from '@/utils/useAutofocusInput'

const { t } = useI18n()
const mainStore = useMainStore()
const permissionRefs = usePermissionRefs()

const modals = {
  addApplications: ref(false),
  addGuacamoles: ref(false),
  confirmAction: ref(false),
  deleteApplications: ref(false),
  deleteConnections: ref(false),
  deleteGuacamoles: ref(false),
  deleteVms: ref(false),
  haConfig: ref(false),
  importConnections: ref(false),
}
const pendingAction = ref(null)
const { autoFocusInputRef } = useAutofocusInput(modals.addGuacamoles)
const customChartLoaded = ref(false)
const dataLoading = ref(false)
const dataLoadingGuac = ref(false)
const dataLoadingVM = ref(true)
const objectModel = 'VirtualMachine'
const objToAdd = ref('')
const objToAdd2 = ref('')
const objToAdd3 = ref('')
const objToRemove = ref({})
const permissionsLoaded = ref(false)
const router = useRouter()
const route = useRoute()
const searchControlUserRef = ref(null)
const selectedCf = ref({})
const selectedMetrics = ref([])
const selectedTimeframe = ref('hour')
const toast = useToast()
const vm = ref([])
const vmApps = ref([])
const vmStatistics = ref([])
const vmTasks = ref([])
const vmConnectionProfiles = ref([])
const vmGuacamoles = ref([])
const relatedGuacamoles = ref([])
const actionPermissions = ref({})

/* HA (High Availability) */
const haInfo = ref(null)
const haUnavailable = ref(false)
const haForm = ref({
  enabled: false,
  state: 'started',
  maxRestart: 5,
  maxRelocate: 5,
})
const haFormInitial = ref(null)
let haFetchPromise = null
let haRefetchTimeoutId = null
let haRefetchStopped = false

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

function resolvedField(id, name) {
  const resolved = id && name && !UUID_RE.test(name)
  return {
    value: resolved ? name : id ? `${id.substring(0, 8)}...` : '–',
    link: resolved ? true : false,
    hint: id && !resolved ? t('views.vms.detail.noReadPermission') : null,
  }
}

const osDisplay = computed(() => resolvedField(vm.value.os, vm.value.osName))

const eventDisplay = computed(() =>
  resolvedField(vm.value.event, vm.value.eventName),
)

const templateDisplay = computed(() =>
  resolvedField(vm.value.template, vm.value.templateName),
)

const actionConfirmConfig = computed(() => {
  const a = pendingAction.value
  if (!a) return {}
  const name = vm.value?.name || ''
  return (
    {
      start: {
        title: t('views.vms.detail.actions.start'),
        text: t('views.vms.detail.confirm.start', { name }),
        color: 'success',
      },
      shutdown: {
        title: t('views.vms.detail.actions.shutdown'),
        text: t('views.vms.detail.confirm.shutdown', { name }),
        color: 'warning',
      },
      reboot: {
        title: t('views.vms.detail.actions.reboot'),
        text: t('views.vms.detail.confirm.reboot', { name }),
        color: 'warning',
      },
      stop: {
        title: t('views.vms.detail.actions.stop'),
        text: t('views.vms.detail.confirm.stop', { name }),
        color: 'danger',
      },
      reset: {
        title: t('views.vms.detail.actions.reset'),
        text: t('views.vms.detail.confirm.reset', { name }),
        color: 'danger',
      },
    }[a] || {}
  )
})

function requestAction(action) {
  if (action === 'createTemplate') {
    vmAction(vm.value.id, action)
    return
  }
  if (action === 'updateip') {
    fetchIPv4(vm.value.id)
    return
  }
  if (action === 'haConfigure') {
    openHaConfigModal()
    return
  }
  pendingAction.value = action
  modals.confirmAction.value = true
}

function confirmAction() {
  modals.confirmAction.value = false
  vmAction(vm.value.id, pendingAction.value)
  pendingAction.value = null
}

const getDisabledState = (action) => {
  const { status } = vm.value
  return (
    {
      start: status !== 'stopped',
      shutdown: status === 'stopped',
      reboot: status !== 'running',
      stop: status !== 'running',
      reset: status === 'stopped',
      updateip: status !== 'running',
      createTemplate: status !== 'stopped',
      haConfigure: !vm.value?.proxmoxId,
      haRemove: !vm.value?.proxmoxId,
    }[action] ?? false
  )
}

const dropdownItems = computed(() => {
  const perms = actionPermissions.value
  if (!perms || Object.keys(perms).length === 0) return []

  return [
    {
      id: 1,
      label: t('views.vms.detail.actions.start'),
      icon: mdiPlay,
      action: 'start',
      permission: 'actions_start',
      disabledTooltip: t('views.vms.detail.actions.mustBeStopped'),
    },
    {
      id: 2,
      label: t('views.vms.detail.actions.shutdown'),
      icon: mdiPower,
      action: 'shutdown',
      permission: 'actions_shutdown',
      tooltip: t('views.vms.detail.actions.shutdownTooltip'),
      disabledTooltip: t('views.vms.detail.actions.alreadyStopped'),
    },
    {
      id: 3,
      label: t('views.vms.detail.actions.reboot'),
      icon: mdiRestart,
      action: 'reboot',
      permission: 'actions_reboot',
      disabledTooltip: t('views.vms.detail.actions.mustBeRunning'),
    },
    {
      id: 6,
      label: t('views.vms.detail.actions.stop'),
      icon: mdiStop,
      action: 'stop',
      permission: 'actions_stop',
      tooltip: t('views.vms.detail.actions.stopTooltip'),
      disabledTooltip: t('views.vms.detail.actions.mustBeRunning'),
    },
    {
      id: 7,
      label: t('views.vms.detail.actions.reset'),
      icon: mdiFlash,
      action: 'reset',
      permission: 'actions_reset',
      tooltip: t('views.vms.detail.actions.resetTooltip'),
      disabledTooltip: t('views.vms.detail.actions.alreadyStopped'),
    },
    {
      id: 8,
      label: t('views.vms.detail.actions.updateIp'),
      icon: mdiReload,
      action: 'updateip',
      permission: 'actions_ipv4',
      tooltip: t('views.vms.detail.actions.updateIpTooltip'),
      disabledTooltip: t('views.vms.detail.actions.mustBeRunning'),
    },
    { divider: true },
    {
      id: 9,
      label: t('views.vms.detail.actions.createTemplate'),
      icon: mdiVectorArrangeAbove,
      action: 'createTemplate',
      permission: 'createTemplate',
      tooltip: t('views.vms.detail.actions.createTemplateTooltip'),
      disabledTooltip: t('views.vms.detail.actions.mustBeStopped'),
    },
    { divider: true },
    {
      id: 10,
      label: t('views.vms.detail.ha.actions.configure'),
      icon: mdiShieldHalfFull,
      action: 'haConfigure',
      permission: 'update',
      tooltip: t('views.vms.detail.ha.actions.configureTooltip'),
      disabledTooltip: t('views.vms.detail.ha.actions.noProxmoxTooltip'),
    },
  ]
    .filter((item) => !item.permission || perms[item.permission])
    .map((item) => ({
      ...item,
      disabled: getDisabledState(item.action),
      onClick: () => requestAction(item.action),
    }))
})

const userHasAction = computed(() => dropdownItems.value.length !== 0)

/* HA (High Availability) — state is fetched on demand only, no auto-refresh */
const KNOWN_HA_STATES = [
  'disabled',
  'error',
  'fence',
  'freeze',
  'ignored',
  'migrate',
  'queued',
  'recovery',
  'relocate',
  'request_start',
  'request_stop',
  'started',
  'stopped',
  'unknown',
]
// deliberately without 'disabled': the simplified toggle model only knows
// managed (started/stopped) or not managed at all (HA removed)
const HA_SELECTABLE_STATES = ['started', 'stopped']

// digest-based: the backend synthesizes digest=null only when the VM is not
// under HA management ('ignored' alone is ambiguous, it is also a valid state)
const haConfigured = computed(() => Boolean(haInfo.value?.digest))

const haState = computed(() => {
  if (haUnavailable.value) return 'unknown'
  return haInfo.value?.state ?? null
})

const haStateLabel = computed(() => {
  const state = haState.value
  if (state == null) return null
  const key = String(state).toLowerCase()
  return KNOWN_HA_STATES.includes(key)
    ? t(`views.vms.detail.ha.states.${key}`)
    : String(state)
})

const haStateOptions = computed(() =>
  HA_SELECTABLE_STATES.map((state) => ({
    value: state,
    label: t(`views.vms.detail.ha.states.${state}`),
  })),
)

const haFormValid = computed(() =>
  [
    [
      haForm.value.maxRestart,
      FIELD_LIMITS.vm.haMaxRestart,
      FIELD_VALUE_LIMITS.vm.haMaxRestart,
    ],
    [
      haForm.value.maxRelocate,
      FIELD_LIMITS.vm.haMaxRelocate,
      FIELD_VALUE_LIMITS.vm.haMaxRelocate,
    ],
  ].every(([value, maxChars, maxValue]) => {
    const n = Number(value)
    return (
      Number.isInteger(n) &&
      n >= 0 &&
      n <= maxValue &&
      String(value).trim().length <= maxChars
    )
  }),
)

// numbers arrive as strings from number inputs, compare a canonical form
function haFormNormalized(form) {
  return {
    enabled: Boolean(form.enabled),
    state: form.state,
    maxRestart: Number(form.maxRestart),
    maxRelocate: Number(form.maxRelocate),
  }
}

const haFormDirty = computed(
  () =>
    haFormInitial.value === null ||
    JSON.stringify(haFormNormalized(haForm.value)) !== haFormInitial.value,
)

// confirming while unchanged would be a no-op (or a stray remove on an
// unconfigured VM), confirming while enabled needs valid limits
const haConfirmDisabled = computed(() => {
  if (!haFormDirty.value) return true
  if (haForm.value.enabled) return !haFormValid.value
  return false
})

// requesting 'stopped' for a running VM makes the HA manager shut it down
// right after confirming — warn so nobody stops a VM by accident
const haStopWarning = computed(
  () =>
    haForm.value.enabled &&
    haForm.value.state === 'stopped' &&
    vm.value?.status === 'running',
)

async function fetchHaState() {
  if (!vm.value?.id || !vm.value?.proxmoxId) return false
  if (haFetchPromise) return haFetchPromise

  haFetchPromise = (async () => {
    backend.beginSilent()
    try {
      haInfo.value = await backend.vms.getHa(route.params.id)
      haUnavailable.value = false
      return true
    } catch {
      haUnavailable.value = true
      return false
    } finally {
      backend.endSilent()
      haFetchPromise = null
    }
  })()

  return haFetchPromise
}

// HA add/remove only enqueue an async job; re-fetch until the change is
// visible on Proxmox (digest differs), bounded so this never polls permanently
const HA_REFETCH_INTERVAL_MS = 3000
const HA_REFETCH_MAX_TRIES = 10

function scheduleHaRefetch() {
  const previousDigest = haInfo.value?.digest ?? null
  let tries = 0

  const poll = async () => {
    tries += 1
    await fetchHaState()
    if (haRefetchStopped) return
    const digest = haInfo.value?.digest ?? null
    if (digest !== previousDigest || tries >= HA_REFETCH_MAX_TRIES) return
    haRefetchTimeoutId = setTimeout(poll, HA_REFETCH_INTERVAL_MS)
  }

  clearTimeout(haRefetchTimeoutId)
  haRefetchTimeoutId = setTimeout(poll, HA_REFETCH_INTERVAL_MS)
}

async function openHaConfigModal() {
  if (!(await fetchHaState())) {
    toast.error(t('views.vms.detail.ha.fetchError'))
    return
  }
  haForm.value = haConfigured.value
    ? {
        enabled: true,
        state: HA_SELECTABLE_STATES.includes(haInfo.value.state)
          ? haInfo.value.state
          : 'started',
        maxRestart: haInfo.value.max_restart ?? 5,
        maxRelocate: haInfo.value.max_relocate ?? 5,
      }
    : { enabled: false, state: 'started', maxRestart: 5, maxRelocate: 5 }
  haFormInitial.value = JSON.stringify(haFormNormalized(haForm.value))
  modals.haConfig.value = true
}

// vault: vue-controlled-radio-desync — segmented control uses button-radios,
// arrow keys move the selection like a native radio group
function onHaStateKeydown(event) {
  const navKeys = ['ArrowRight', 'ArrowDown', 'ArrowLeft', 'ArrowUp']
  if (!navKeys.includes(event.key)) return

  event.preventDefault()
  const forward = event.key === 'ArrowRight' || event.key === 'ArrowDown'
  const nextIndex =
    (HA_SELECTABLE_STATES.indexOf(haForm.value.state) +
      (forward ? 1 : -1) +
      HA_SELECTABLE_STATES.length) %
    HA_SELECTABLE_STATES.length
  haForm.value.state = HA_SELECTABLE_STATES[nextIndex]
}

async function applyHaConfig() {
  // toggle switched off on a configured VM: confirming removes HA management
  if (!haForm.value.enabled) {
    await removeHaConfig()
    return
  }
  try {
    await backend.vms.setHa(vm.value.id, {
      haState: haForm.value.state,
      haMaxRestart: Number(haForm.value.maxRestart),
      haMaxRelocate: Number(haForm.value.maxRelocate),
    })
    toast.success(
      t('views.vms.detail.ha.applySuccess', { name: vm.value.name }),
    )
    scheduleHaRefetch()
  } catch (error) {
    toast.error(t('views.vms.detail.ha.applyError', { name: vm.value.name }))
  }
}

async function removeHaConfig() {
  try {
    await backend.vms.removeHa(vm.value.id)
    toast.success(
      t('views.vms.detail.ha.removeSuccess', { name: vm.value.name }),
    )
    scheduleHaRefetch()
  } catch (error) {
    toast.error(t('views.vms.detail.ha.removeError', { name: vm.value.name }))
  }
}

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
      fetchData: fetchVMApplications,
    },
    {
      name: 'connections',
      perPage: 5,
      currentPage: 1,
      sortColumnKey: 'createdAt',
      sortDirection: 'asc',
      searchField: null,
      searchValue: null,
      fetchData: fetchVMConnections,
    },
    {
      name: 'guac',
      perPage: 5,
      currentPage: 1,
      sortColumnKey: 'createdAt',
      sortDirection: 'asc',
      fetchData: fetchVMGuacs,
    },
    {
      name: 'guacamoles',
      perPage: 100,
      currentPage: 1,
      sortColumnKey: 'createdAt',
      sortDirection: 'asc',
      fetchData: fetchVM,
    },
    {
      name: 'tasks/subtasks',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'createdAt',
      sortDirection: 'desc',
      fetchData: fetchVMTasks,
    },
    {
      name: 'statistics',
      fetchData: fetchVMStatistics,
    },
    {
      name: 'users',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'name',
      sortDirection: 'asc',
    },
  ],
  fetchArgs: () => [route.params.id],
  modals,
  objToRemove,
  route,
})
/**/

const applicationFields = applicationSearchBarFields()
const connectionFields = connectionSearchBarFields({ exclude: ['objectId'] })

async function fetchVMGuacs(id) {
  await fetchVMConnections(id)
}

async function addApplication(appKey) {
  try {
    const applications = [
      ...vmApps.value.map(({ key }) => ({ key })),
      { key: appKey },
    ]
    await backend.vms.updateApps(route.params.id, applications)
    fetchVMApplications(route.params.id)
    toast.success(
      t('common.addSuccess', { entity: t('objectTypes.application.singular') }),
    )
  } catch (error) {
    toast.error(
      t('common.addError', { entity: t('objectTypes.application.singular') }),
    )
  } finally {
    resetSearchComponent()
  }
}

async function addConnection(name, userId, connectionProfile) {
  try {
    await backend.guacamole.create({
      name,
      userId,
      connection_profile: connectionProfile,
    })
    useMainStore().fetchPermissions()
    toast.success(
      t('common.createSuccess', {
        entity: t('objectTypes.guacamole.singular'),
      }),
    )
  } catch (error) {
    toast.error(
      `${t('common.createError', { entity: t('objectTypes.guacamole.singular') })}\n${error?.response?.data?.detail}`,
    )
  } finally {
    resetSearchComponent()
    await fetchVM()
  }
}

async function deleteApplication(appId) {
  try {
    const applications = vmApps.value
      .filter(({ id }) => id !== appId)
      .map(({ key }) => ({ key }))
    await backend.vms.updateApps(route.params.id, applications)
    fetchVMApplications(route.params.id)
    toast.success(
      t('common.removeSuccess', {
        entity: t('objectTypes.application.singular'),
      }),
    )
  } catch (error) {
    toast.error(
      t('common.removeError', {
        entity: t('objectTypes.application.singular'),
      }),
    )
  }
  objToRemove.value = ''
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
      `${t('common.deleteError', { entity: t('objectTypes.guacamole.singular') })}\n${error?.response?.data?.detail}`,
    )
  } finally {
    resetSearchComponent()
    await fetchVM()
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
    )
  } finally {
    backend.endSilent()
    relatedGuacamoles.value = []
    resetSearchComponent()
    await fetchVMConnections(route.params.id)
    if (cascadeTargets.length > 0) {
      await fetchVM()
    }
  }
}

async function deleteVM(vmId) {
  try {
    await backend.vms.delete(vmId)
    router.push({ path: `/vms` })
    toast.success(
      t('common.deleteSuccess', {
        entity: t('objectTypes.virtualMachine.singular'),
      }),
    )
  } catch (error) {
    const errorCode = error?.response?.data?.error_code

    if (errorCode === 'PROTECTED_OBJECT') {
      toast.error(t('views.vms.detail.deleteProtectedError'), {
        timeout: 8400,
      })
      await fetchVM()
    } else {
      toast.error(
        t('common.deleteError', {
          entity: t('objectTypes.virtualMachine.singular'),
        }),
      )
    }
  }
}

async function fetchIPv4(vmId) {
  try {
    await backend.vms.getIPv4(vmId)
    toast.success(t('views.vms.detail.ipv4UpdateSuccess'))
  } catch (error) {
    toast.error(t('views.vms.detail.ipv4UpdateError'))
  }
}

async function fetchVM(isInitial = false) {
  try {
    if (isInitial) dataLoadingVM.value = true

    const response = await backend.vms.get(route.params.id)

    vm.value = response
    await resolveFieldFromLookup(vm.value, [
      { from: 'createdById', to: 'createdBy', keyspace: 'users' },
      { from: 'updatedById', to: 'updatedBy', keyspace: 'users' },
      { from: 'event', to: 'eventName', keyspace: 'events' },
    ])

    if (vm.value.os) {
      await resolveFieldFromLookup(vm.value, [
        { from: 'os', to: 'osName', keyspace: 'os' },
      ])
    }

    if (vm.value.template) {
      await resolveFieldFromLookup(vm.value, [
        { from: 'template', to: 'templateName', keyspace: 'templates' },
      ])
    }

    vm.value.ram = vm.value.ram / 1024
    vm.value.proxmoxLabel = `${vm?.value?.proxmoxId} (${vm?.value?.proxmoxNode})`

    vmGuacamoles.value = vm.value.guacamoles
    vmGuacamoles.value.count = vmGuacamoles.value?.length ?? 0

    await resolveFieldFromLookup(vmGuacamoles.value, [
      { from: 'userId', to: 'user', keyspace: 'users' },
      {
        from: 'connection_profile',
        to: 'connectionProfile',
        keyspace: 'connectionProfiles',
      },
    ])
  } catch (error) {
    if (isInitial) {
      toast.warning(
        t('common.notFound', {
          entity: t('objectTypes.virtualMachine.singular'),
        }),
      )
      router.push({ path: `/vms`, replace: true })
    }
  } finally {
    if (isInitial) dataLoadingVM.value = false
  }
}

async function fetchVMApplications() {
  try {
    dataLoading.value = true

    const applicationsComponent = childComponents.value.find(
      (component) => component.name === 'applications',
    )
    await backend.vms
      .getApps(route.params.id, {
        page: applicationsComponent?.currentPage,
        limit: applicationsComponent?.perPage,
        sort_by: applicationsComponent?.sortColumnKey,
        sort_order: applicationsComponent?.sortDirection,
        search_field: applicationsComponent?.searchField,
        search_value: applicationsComponent?.searchValue,
      })
      .then(async (response) => {
        vmApps.value = response.items
        vmApps.value.count = response.pageDetails.totalCount
        await resolveFieldFromLookup(vmApps.value, [
          { from: 'vendor', to: 'vendorName', keyspace: 'vendors' },
        ])
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

async function fetchVMConnections() {
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
        vmConnectionProfiles.value = response.items.map((obj) => ({
          ...obj,
          value: obj.id,
        }))
        vmConnectionProfiles.value.count = response.pageDetails.totalCount
        resolveFieldFromLookup(vmConnectionProfiles.value, [
          {
            from: 'objectId',
            to: 'label',
            keyspace: 'vms',
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

async function fetchVMStatistics() {
  try {
    dataLoading.value = true

    await backend.vms
      .getRRDData(route.params.id, selectedTimeframe.value, selectedCf.value)
      .then(async (response) => {
        vmStatistics.value = response
      })
  } catch (error) {
    toast.error(t('views.vms.detail.statisticsLoadError') + `\n${error}`)
  } finally {
    dataLoading.value = false
  }
}

async function updateStatisticsFilter({
  hosts = [],
  metrics = [],
  timeframe = 'hour',
  cf = 'AVERAGE',
}) {
  selectedMetrics.value = metrics.map((item) => item.value)
  selectedTimeframe.value = timeframe
  selectedCf.value = cf

  fetchVMStatistics()

  customChartLoaded.value = true
}

async function fetchVMTasks() {
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
        vmTasks.value = response.items
        vmTasks.value.count = response.pageDetails.totalCount
        await resolveFieldFromLookup(vmTasks.value, [
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

function showModal(modal, item) {
  if (Object.prototype.hasOwnProperty.call(modals, modal)) {
    modals[modal].value = true
  }
  if (item) {
    objToRemove.value = item
  }
}

const vmEdit = (vmId) => {
  router.push({ path: `/vms/${vmId}/edit` })
}

const createConnectionProfile = (vmId) => {
  router.push({
    path: `/connections/create`,
    query: {
      entityId: vmId,
      entityType: objectModel,
    },
  })
}

async function vmAction(vmId, action) {
  try {
    if (action === 'createTemplate') {
      return router.push({
        path: `/templates/create`,
        query: {
          template: vmId,
        },
      })
    }

    await backend.vms.action(vmId, action)
    fetchVM()
    toast.success(
      t('views.vms.detail.actionSuccess', {
        action: t(`views.vms.detail.actions.${action}`),
        name: vm.value.name,
      }),
    )
  } catch (error) {
    toast.error(
      t('views.vms.detail.actionError', {
        action: t(`views.vms.detail.actions.${action}`),
        name: vm.value.name,
      }),
    )
  }
}

async function handleProtectionChange() {
  try {
    await backend.vms
      .setProtection(vm.value.id, vm.value.prevent_delete ? false : true)
      .then(() => {
        fetchVM()
      })
    toast.success(t('views.vms.detail.protectionChanged'))
  } catch (error) {
    toast.error(
      t('common.protectionChangeError', {
        entity: t('objectTypes.virtualMachine.singular'),
      }),
    )
  }
}

const fetchPermissions = async () => {
  const actions = [
    'actions_start',
    'actions_shutdown',
    'actions_reboot',
    'actions_stop',
    'actions_reset',
    'update',
    'reset',
  ]

  const results = await Promise.all(
    actions.map((action) => mainStore.userCan('vms', action, '/')),
  )

  let userPermissions = Object.fromEntries(
    actions.map((action, index) => [action, results[index]]),
  )

  if (userPermissions.reset) {
    userPermissions = {
      ...userPermissions,
      ...Object.fromEntries(
        actions
          .filter((action) => action.startsWith('actions_'))
          .map((action) => [action, true]),
      ),
    }
  }

  if (await mainStore.userCan('templates', 'create', '/*')) {
    userPermissions.createTemplate = true
  }

  if (Object.values(userPermissions).some((val) => val === true)) {
    userPermissions.actions_ipv4 = true
  } else {
    userPermissions.actions_ipv4 = false
  }
  actionPermissions.value = userPermissions
}

const resetSearchComponent = () => {
  objToAdd.value = null
  objToAdd2.value = null
  objToAdd3.value = null
  searchControlUserRef.value?.setInitialDisplay('')
  searchControlUserRef.value?.setSelectedId('')
}

const buttonsApps = computed(() => {
  if (permissionRefs.canEdit) return ['view', 'delete']
  return ['view']
})

const buttonsConnections = computed(() => {
  if (permissionRefs.canDeleteConnections) return ['view', 'delete']
  return ['view']
})

const buttonsGuacamoles = computed(() => {
  if (permissionRefs.canDeleteGuacamoles) return ['view', 'delete']
  return ['view']
})

const pillType = computed(() => {
  if (vm.value.id) {
    if (vm.value.prevent_delete) {
      return 'danger'
    }
    return 'success'
  }
  return 'info'
})

const showActionButtons = computed(() => {
  if (!vm?.value?.id) {
    return false
  }
  return vm?.value?.status?.toLowerCase() != 'deleting'
})

const graphLabel = computed(() => {
  return `VM: ${vm.value.name} (${vm.value.proxmoxId}) (${vm.value.proxmoxNode})`
})

// TODO KVS-435
let intervalId
onMounted(async () => {
  await fetchVM(true)
  fetchHaState()
  await fetchPermissions()

  intervalId = setInterval(() => {
    fetchVM(false)
    refreshActiveTab()
  }, 15000)

  await checkObjectPermissions(
    'vms',
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
        key: 'canCreateGuacamoles',
        objectType: 'guacamoles',
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
        key: 'canReadGuacamoles',
        objectType: 'guacamoles',
        objectPermission: 'read',
        objectPath: '/*',
      },
      {
        key: 'canDeleteGuacamoles',
        objectType: 'guacamoles',
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
    ],
    ['canEdit', 'canDelete'],
  )

  permissionsLoaded.value = true
})

onUnmounted(() => {
  clearInterval(intervalId)
  haRefetchStopped = true
  clearTimeout(haRefetchTimeoutId)
})
</script>

<template>
  <!-- Modal: Add vm application association -->
  <SearchModal
    v-model="modals.addApplications.value"
    :fetch-data="backend.applications.search"
    :icon="mdiApps"
    :label="$t('views.vms.detail.searchAppLabel')"
    :title="$t('views.vms.detail.assignApp')"
    return-attribute="key"
    @submitted="addApplication"
  />

  <!-- Modal: Confirm VM action -->
  <CardBoxModal
    v-model="modals.confirmAction.value"
    :title="actionConfirmConfig.title"
    :button="actionConfirmConfig.color"
    :button-label="$t('common.confirm')"
    has-cancel
    @form-submitted="confirmAction"
  >
    <p>{{ actionConfirmConfig.text }}</p>
  </CardBoxModal>

  <!-- Modal: HA configuration (enable, adjust or remove) -->
  <CardBoxModal
    v-model="modals.haConfig.value"
    form
    :title="$t('views.vms.detail.ha.actions.configure')"
    :button="!haForm.enabled && haConfigured ? 'danger' : 'success'"
    :button-label="$t('common.confirm')"
    :disabled="haConfirmDisabled"
    has-cancel
    @form-submitted="applyHaConfig"
  >
    <div class="mt-4">
      <FormCheckRadio
        v-model="haForm.enabled"
        name="ha_enabled"
        type="switch"
        :label="$t('views.vms.detail.ha.modal.enabledLabel')"
        :help="$t('views.vms.detail.ha.modal.enabledHelp')"
      />
    </div>

    <template v-if="haForm.enabled">
      <FormField
        :label="$t('views.vms.detail.ha.modal.stateLabel')"
        :help="$t('views.vms.detail.ha.modal.stateHelp')"
        :tooltip="$t('views.vms.detail.ha.modal.stateTooltip')"
      >
        <div
          role="radiogroup"
          :aria-label="$t('views.vms.detail.ha.modal.stateLabel')"
          class="inline-flex gap-1 rounded-lg border border-gray-300 bg-gray-100 p-1 dark:border-slate-600 dark:bg-slate-800/60"
        >
          <button
            v-for="opt in haStateOptions"
            :key="opt.value"
            type="button"
            role="radio"
            :aria-checked="haForm.state === opt.value"
            :tabindex="haForm.state === opt.value ? 0 : -1"
            class="cursor-pointer rounded-md px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            :class="
              haForm.state === opt.value
                ? 'bg-blue-500 text-white shadow-sm'
                : 'text-gray-600 hover:bg-white/70 hover:text-gray-900 dark:text-slate-300 dark:hover:bg-slate-700/60 dark:hover:text-white'
            "
            @click="haForm.state = opt.value"
            @keydown="onHaStateKeydown"
          >
            {{ opt.label }}
          </button>
        </div>
      </FormField>

      <NotificationBar
        v-if="haStopWarning"
        color="warning"
        :icon="mdiAlert"
        :dismissable="false"
      >
        {{ $t('views.vms.detail.ha.modal.stopWarning') }}
      </NotificationBar>

      <div class="grid grid-cols-1 gap-x-4 sm:grid-cols-2">
        <FormField
          :label="$t('views.vms.detail.ha.modal.maxRestartLabel')"
          :help="$t('views.vms.detail.ha.modal.maxRestartHelp')"
          :tooltip="
            $t('views.vms.detail.ha.modal.limitTooltip', {
              min: 0,
              max: FIELD_VALUE_LIMITS.vm.haMaxRestart,
            })
          "
        >
          <FormControl
            v-model="haForm.maxRestart"
            type="number"
            min="0"
            :max="FIELD_VALUE_LIMITS.vm.haMaxRestart"
            step="1"
            :maxlength="FIELD_LIMITS.vm.haMaxRestart"
            required
          />
        </FormField>

        <FormField
          :label="$t('views.vms.detail.ha.modal.maxRelocateLabel')"
          :help="$t('views.vms.detail.ha.modal.maxRelocateHelp')"
          :tooltip="
            $t('views.vms.detail.ha.modal.limitTooltip', {
              min: 0,
              max: FIELD_VALUE_LIMITS.vm.haMaxRelocate,
            })
          "
        >
          <FormControl
            v-model="haForm.maxRelocate"
            type="number"
            min="0"
            :max="FIELD_VALUE_LIMITS.vm.haMaxRelocate"
            step="1"
            :maxlength="FIELD_LIMITS.vm.haMaxRelocate"
            required
          />
        </FormField>
      </div>
    </template>

    <NotificationBar
      v-else-if="haConfigured"
      color="danger"
      :icon="mdiShieldRemove"
      :dismissable="false"
    >
      {{ $t('views.vms.detail.ha.modal.removeWarning') }}
    </NotificationBar>
  </CardBoxModal>

  <!-- Modal: Add vm guacamole connection profile association -->
  <CardBoxModal
    v-model="modals.addGuacamoles.value"
    form
    :title="$t('views.vms.detail.addConnection')"
    button="success"
    has-cancel
    has-search
    :button-label="$t('common.add')"
    @cancel="resetSearchComponent"
    @form-submitted="addConnection(objToAdd, objToAdd2, objToAdd3)"
  >
    <FormField
      :label="$t('common.name')"
      :tooltip="$t('views.vms.detail.connectionNameTooltip')"
      :help="$t('views.vms.detail.connectionNameHelp')"
    >
      <FormControl
        v-model="objToAdd"
        :icon="mdiRename"
        :maxlength="FIELD_LIMITS.guacamole.name"
        :placeholder="$t('views.vms.detail.connectionNamePlaceholder')"
        required
        @set-ref="
          (ref) => {
            autoFocusInputRef = ref
          }
        "
      />
    </FormField>

    <FormField
      :label="$t('views.vms.detail.userLabel')"
      :help="$t('views.vms.detail.userHelp')"
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

    <FormField
      :label="$t('views.vms.detail.connectionTemplateLabel')"
      :help="$t('views.vms.detail.connectionTemplateHelp')"
    >
      <FormControl
        v-model="objToAdd3"
        :icon="mdiMonitor"
        :options="vmConnectionProfiles"
        required
      />
    </FormField>
  </CardBoxModal>

  <!-- Modal: Delete Connection -->
  <CardBoxDeleteModal
    v-model="modals.deleteGuacamoles.value"
    :name="
      $t('views.vms.detail.connectionForUser', {
        connection: objToRemove.connectionProfile,
        user: objToRemove.user,
      })
    "
    :checkvalue="$t('common.confirm')"
    @form-submitted="deleteConnection(objToRemove.id)"
  />

  <!-- Modal: Import Connection Profile -->
  <ImportConnectionProfileModal
    v-if="vm.id"
    v-model="modals.importConnections.value"
    :target-object-type="objectModel"
    :target-object-id="vm.id"
    @imported="fetchVMConnections(route.params.id)"
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

  <!-- Modal: Delete vm application association -->
  <CardBoxDeleteRelationModal
    v-model="modals.deleteApplications.value"
    :parent-object="vm.name"
    :related-object="objToRemove.name"
    :checkvalue="objToRemove.name"
    @form-submitted="deleteApplication(objToRemove.id)"
  />

  <!-- Modal: Delete vm -->
  <CardBoxDeleteModal
    v-model="modals.deleteVms.value"
    :name="vm.name"
    :checkvalue="vm.name"
    @form-submitted="deleteVM(vm.id)"
  />

  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiMonitor"
        :title="vm.name ? vm.name : $t('common.loading')"
        :object-model="$t('views.vms.detail.objectModel')"
        main
        docs-path="/docs/usage/openvle/vms/"
      >
        <!-- PillTag: VM status -->
        <PillTag
          :label="vm.status ? vm.status : 'unkwn'"
          :color="statusColorVM(vm.status)"
          :disabled="true"
          :icon="vmStatusIcon(vm.status)"
          small
        />

        <!-- PillTag: VM protection -->
        <PillTag
          v-if="showActionButtons"
          label=""
          :disabled="!permissionRefs.canEdit"
          :color="pillType"
          :icon="vm.prevent_delete ? mdiLock : mdiLockOpen"
          :handle-click="handleProtectionChange"
          small
        />

        <!-- Button: Actions -->
        <BaseButtons
          v-if="showActionButtons"
          type="justify-start lg:justify-end"
        >
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

          <!-- Button: Edit VM -->
          <BaseButton
            v-if="permissionRefs.canEdit"
            target="_blank"
            :icon="mdiPencil"
            :label="$t('common.edit')"
            color="contrast"
            rounded-full
            small
            @click="vmEdit(vm.id)"
          />

          <!-- Button: Delete VM -->
          <BaseButton
            v-if="permissionRefs.canDelete"
            target="_blank"
            :icon="mdiDelete"
            :label="$t('common.delete')"
            color="danger"
            rounded-full
            small
            :disabled="vm.prevent_delete"
            @click="showModal('deleteVms', vm)"
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
          <BaseTab id="vm" :title="$t('objectTypes.virtualMachine.singular')">
            <!-- Spec cards -->
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
              <SpecCard
                :icon="mdiCpu64Bit"
                :value="vm.cpu ?? '–'"
                :label="$t('views.vms.cpuCoresLabel')"
                color="blue"
              />

              <SpecCard
                :icon="mdiMemory"
                :value="vm.ram ? `${vm.ram} GB` : '–'"
                :label="$t('common.memory')"
                color="violet"
              />

              <SpecCard
                :icon="mdiHarddisk"
                :value="vm.disk ? `${vm.disk} GB` : '–'"
                :label="$t('views.vms.detail.disk')"
                color="amber"
              />

              <SpecCard
                :icon="mdiApplicationBrackets"
                :value="osDisplay.value"
                :label="$t('views.vms.osLabel')"
                color="emerald"
                :link="osDisplay.link ? `/os/${vm.os}` : null"
                :hint="osDisplay.hint"
              />

              <SpecCard
                :icon="mdiIp"
                :value="vm.ipv4 ?? '–'"
                :label="$t('views.vms.detail.ipv4Address')"
                color="sky"
                copyable
              />

              <SpecCard
                :icon="mdiServer"
                :value="vm.proxmoxLabel ?? '–'"
                :label="$t('common.proxmox')"
                color="slate"
              />

              <SpecCard
                v-if="vm.proxmoxId"
                :icon="haStateIconVM(haState)"
                :value="haStateLabel ?? '–'"
                :label="$t('views.vms.detail.ha.specLabel')"
                color="slate"
              />

              <SpecCard
                v-if="vm.template"
                :icon="mdiVectorArrangeAbove"
                :value="templateDisplay.value"
                :label="$t('views.vms.detail.vmTemplate')"
                color="cyan"
                :link="
                  templateDisplay.link ? `/templates/${vm.template}` : null
                "
                :hint="templateDisplay.hint"
              />

              <SpecCard
                v-if="vm.event"
                :icon="mdiCalendarOutline"
                :value="eventDisplay.value"
                :label="$t('views.vms.detail.event')"
                color="rose"
                :link="eventDisplay.link ? `/events/${vm.event}` : null"
                :hint="eventDisplay.hint"
              />
            </div>

            <BaseDivider />

            <FormField
              :label="$t('common.description')"
              :help="$t('views.vms.descriptionHelp')"
            />

            <BaseMarkdown v-model="vm.description" action="view" />

            <ObjectMetadataDisplay
              v-if="loadedTabs.has('vm') && vm.id"
              :object="vm"
              :object-type="objectModel"
              :object-id="route.params.id"
              :can-edit="permissionRefs.canEdit"
              :tags-help="$t('views.vms.detail.tagsHelp')"
            />
          </BaseTab>

          <BaseTab
            id="applications"
            :title="$t('objectTypes.application.plural')"
          >
            <SectionTitleLineWithButton
              :icon="mdiApps"
              :title="$t('views.vms.detail.applications')"
              :reload="fetchVMApplications"
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
              :items-total="vmApps.count"
              :data="vmApps"
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
                  label: $t('views.vms.detail.vendor'),
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

          <BaseTab
            v-if="
              permissionRefs.canReadConnections ||
              permissionRefs.canReadGuacamoles
            "
            id="guac"
            :title="$t('objectTypes.guacamole.plural')"
          >
            <SectionTitleLineWithButton
              v-if="permissionRefs.canReadConnections"
              :icon="mdiRemoteDesktop"
              :title="$t('views.vms.detail.connectionTemplates')"
              :reload="fetchVMConnections"
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
                @click="createConnectionProfile(vm.id)"
              />
            </SectionTitleLineWithButton>

            <BaseTable
              v-if="loadedTabs.has('guac') && permissionRefs.canReadConnections"
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
              :items-total="vmConnectionProfiles.count"
              :data="vmConnectionProfiles"
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
                { label: $t('views.vms.detail.username'), key: 'username' },
                {
                  label: $t('views.vms.detail.protocol'),
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

            <BaseDivider />

            <SectionTitleLineWithButton
              v-if="permissionRefs.canReadGuacamoles"
              :icon="mdiRemoteDesktop"
              :title="$t('views.vms.detail.connections')"
              :reload="fetchVM"
            >
              <BaseButton
                v-if="permissionRefs.canCreateGuacamoles"
                :icon="mdiPlus"
                color="success"
                rounded-full
                small
                @click="showModal('addGuacamoles')"
              />
            </SectionTitleLineWithButton>

            <BaseTable
              v-if="vmGuacamoles && permissionRefs.canReadGuacamoles"
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
              :items-total="vmGuacamoles.count"
              :data="vmGuacamoles"
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
              :loading="dataLoadingGuac"
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
                { label: $t('common.name'), key: 'name', sortable: false },
                {
                  label: $t('views.vms.detail.user'),
                  key: 'user',
                  sortable: false,
                },
                {
                  label: $t('views.vms.detail.connectionTemplateColumn'),
                  key: 'connectionProfile',
                  sortable: false,
                },
              ]"
              @delete-object="handleDeleteObject"
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
            />
          </BaseTab>

          <BaseTab id="statistics" :title="$t('common.statistics')">
            <SectionTitleLineWithButton
              :icon="mdiChartBar"
              :title="$t('common.statistics')"
              :reload="fetchVMStatistics"
            />

            <!-- Charts: note -->
            <NotificationBar
              :dismissable="false"
              color="info"
              :icon="mdiInformation"
            >
              <b>{{ $t('views.vms.detail.statisticsNote') }}</b>
            </NotificationBar>

            <!-- Charts: metrics filter -->
            <MetricsSelectionPanel
              :hosts="[
                {
                  ...vm,
                  value: vm.name,
                },
              ]"
              :type="'vm'"
              @submit="updateStatisticsFilter"
            />

            <!-- Charts: CPU and memory chart -->
            <CardBox class="mb-6">
              <ProxmoxRrdChart
                v-if="vmStatistics"
                :rrd-data="vmStatistics"
                :title="graphLabel"
                :metrics="['cpu', 'memhost']"
                :timeframe="selectedTimeframe"
              />
            </CardBox>

            <!-- Charts: netin and netout chart -->
            <CardBox class="mb-6">
              <ProxmoxRrdChart
                v-if="vmStatistics"
                :rrd-data="vmStatistics"
                :title="graphLabel"
                :metrics="['netin', 'netout']"
                :timeframe="selectedTimeframe"
              />
            </CardBox>

            <!-- Charts: custom chart -->
            <CardBox v-if="vmStatistics && customChartLoaded" class="mb-6">
              <CardBoxComponentHeader
                :title="$t('views.vms.detail.customChart')"
              />

              <ProxmoxRrdChart
                :rrd-data="vmStatistics"
                :title="graphLabel"
                :metrics="selectedMetrics"
                :timeframe="selectedTimeframe"
              />
            </CardBox>
          </BaseTab>

          <BaseTab
            v-if="permissionRefs.canReadSubTasks"
            id="tasks/subtasks"
            :title="$t('objectTypes.task.plural')"
          >
            <SectionTitleLineWithButton
              :icon="mdiFileTree"
              :title="$t('objectTypes.task.plural')"
              :reload="fetchVMTasks"
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
              :items-total="vmTasks.count"
              :data="vmTasks"
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
                  label: $t('views.vms.detail.triggeredBy'),
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
              v-if="vm.id && loadedTabs.has('changelogs')"
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
