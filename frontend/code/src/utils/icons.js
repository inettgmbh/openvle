import {
  mdiAccountCheck,
  mdiAccountEditOutline,
  mdiAccountNetwork,
  mdiAccountOff,
  mdiAlertCircle,
  mdiAlertCircleOutline,
  mdiArchive,
  mdiArrowRightCircleOutline,
  mdiAutorenew,
  mdiBlockHelper,
  mdiCached,
  mdiCalendarCheck,
  mdiCalendarClock,
  mdiCheckCircle,
  mdiCheckCircleOutline,
  mdiClockOutline,
  mdiCloseCircleOutline,
  mdiCog,
  mdiCogOutline,
  mdiConsole,
  mdiContentCopy,
  mdiContentSaveOutline,
  mdiDelete,
  mdiDeleteRestore,
  mdiDownloadOutline,
  mdiEarth,
  mdiEmailAlert,
  mdiEyeOutline,
  mdiFileDocumentEditOutline,
  mdiHelpCircleOutline,
  mdiInformationOutline,
  mdiLanConnect,
  mdiLock,
  mdiLockAlert,
  mdiLockOpenVariant,
  mdiMonitor,
  mdiNetwork,
  mdiPauseCircle,
  mdiPlayCircle,
  mdiProgressAlert,
  mdiProgressCheck,
  mdiProgressClock,
  mdiProgressHelper,
  mdiRemoteDesktop,
  mdiShieldAccount,
  mdiShieldAlert,
  mdiShieldCheck,
  mdiShieldCrown,
  mdiShieldHalfFull,
  mdiShieldOff,
  mdiShieldOffOutline,
  mdiShieldOutline,
  mdiShieldSync,
  mdiStopCircle,
  mdiSync,
  mdiTrashCanOutline,
  mdiUploadOutline,
  mdiWrench,
} from '@mdi/js'

import { getObjectPermissionByKey } from '@/utils/objectModelPermissions'

/**
 * Returns the corresponding MDI icon based on the event creation type.
 *
 * If the event was created manually (`createType` is falsy), the wrench icon is used.
 * If the event was created automatically or from a template (`createType` is truthy),
 * the calendar check icon is used.
 *
 * @param {boolean} createType - Indicates how the event was created.
 * @returns {string} The MDI icon string: `mdiCalendarCheck` if `true`, otherwise `mdiWrench`.
 */
export const eventCreateTypeIcon = (createType) => {
  return createType ? mdiCalendarCheck : mdiWrench
}

/**
 * Returns the corresponding MDI icon based on the mail creation type.
 *
 * If the mail was created manually (`createType` is falsy), the wrench icon is used.
 * If the mail was created automatically or from a event (`createType` is truthy),
 * the calendar check icon is used.
 *
 * @param {boolean} createType - Indicates how the mail was created.
 * @returns {string} The MDI icon string: `mdiCalendarCheck` if `true`, otherwise `mdiWrench`.
 */
export const mailCreateTypeIcon = (createType) => {
  return createType ? mdiCalendarCheck : mdiWrench
}

/**
 * Returns the corresponding MDI icon for a given connection protocol.
 *
 * This function maps protocol strings to representative Material Design Icons (MDI),
 * used for visual indication of the connection type.
 *
 * Supported protocols:
 * - 'rdp' → Remote Desktop (`mdiRemoteDesktop`)
 * - 'ssh' → Console/Terminal (`mdiConsole`)
 * - 'vnc' → Monitor (`mdiMonitor`)
 * - 'k8s' → Kubernetes (`mdiNetwork`)
 * - 'tel' → Telnet (`mdiLanConnect`)
 *
 * @param {string} value - The connection protocol identifier (e.g. 'ssh', 'rdp').
 * @returns {string|undefined} The MDI icon string corresponding to the protocol, or `undefined` if unknown.
 */
export const connectionProtocolFormatterIcon = (value) => {
  switch (String(value).toLowerCase()) {
    case 'rdp':
      return mdiRemoteDesktop
    case 'ssh':
      return mdiConsole
    case 'vnc':
      return mdiMonitor
    case 'k8s':
      return mdiNetwork
    case 'tel':
      return mdiLanConnect
  }
  return undefined
}

/**
 * Returns the corresponding MDI icon for a given task status.
 *
 * This function maps status strings to representative Material Design Icons (MDI),
 * used for visual indication of the task status.
 *
 * Supported status:
 * - 'success' → `mdiCheckCircleOutline`
 * - 'failed' → `mdiAlertCircleOutline`
 * - 'queued' → `mdiClockOutline`
 * - 'processing' → `mdiSync`
 *
 * @param {string} status - The task status (e.g. 'success', 'failed', 'queued', 'processing').
 * @returns {string} The MDI icon string corresponding to the status, or `undefined` if unknown.
 */
export const taskStatusIcon = (status) => {
  switch (status?.toLowerCase()) {
    case 'success':
      return mdiCheckCircleOutline
    case 'failed':
      return mdiAlertCircleOutline
    case 'queued':
      return mdiClockOutline
    case 'processing':
      return mdiSync
  }
  return mdiHelpCircleOutline
}

/**
 * Stable mapping from event status keys to MDI icons.
 *
 * Keys match the i18n key suffix (e.g. `status.<key>`).
 */
export const eventStatusIconMap = {
  active: mdiCheckCircle,
  archived: mdiArchive,
  archiving: mdiCached,
  deploying: mdiAutorenew,
  errorCore: mdiAlertCircle,
  errorDeployment: mdiAlertCircle,
  errorArchiving: mdiAlertCircle,
  planned: mdiCalendarClock,
  inactive: mdiPauseCircle,
  stopped: mdiStopCircle,
}

/**
 * Returns the corresponding MDI icon based on the event status type.
 *
 * Accepts either the translated display name (from the backend or i18n)
 * or a status key from {@link eventStatusIconMap}.
 *
 * @param {string} status - Status of the event.
 * @returns {string} The MDI icon string.
 */
export const eventStatusIcon = (status) => {
  if (status == null) {
    return ''
  }

  // Direct key match (e.g. 'active', 'archived')
  if (eventStatusIconMap[status]) {
    return eventStatusIconMap[status]
  }

  // Translated / display-name match (legacy, case-insensitive)
  switch (status?.toLowerCase()) {
    case 'aktiv':
      return mdiCheckCircle
    case 'archiviert':
      return mdiArchive
    case 'in archivierung':
      return mdiCached
    case 'deploying':
      return mdiAutorenew
    case 'fehler':
    case 'core fehler':
    case 'fehler (core)':
    case 'deployment fehler':
    case 'fehler (deployment)':
    case 'archival fehler':
    case 'fehler (archivierung)':
      return mdiAlertCircle
    case 'geplant':
      return mdiCalendarClock
    case 'inaktiv':
      return mdiPauseCircle
    case 'stopped':
      return mdiStopCircle
    case 'archiving':
      return mdiAutorenew
  }
  return ''
}

/**
 * Returns the corresponding MDI icon based on the email status type.
 *
 * @param {boolean} status - Status of the email.
 * @returns {string|undefined} The MDI icon string.
 */
export const emailStatusIcon = (status) => {
  switch (String(status).toLowerCase()) {
    case 'sent':
      return mdiProgressCheck
    case 'queued':
      return mdiProgressClock
    case 'error':
      return mdiProgressAlert
  }
  return undefined
}

/**
 * Returns the corresponding MDI icon based on the system setting visibility.
 *
 * @param {string} visibility - The visibility level to determine the icon for.
 * Can be one of: `'public'`, `'authenticated'`, `'admins'`, or `'internal'`.
 * Matching is case-insensitive.
 *
 * @returns {string|undefined} The corresponding MDI path if a match is found, otherwise `undefined`.
 */
export const systemSettingVisibilityIcon = (visibility) => {
  switch (visibility?.toLowerCase()) {
    case 'public':
      return mdiEarth
    case 'authenticated':
      return mdiAccountCheck
    case 'admins':
      return mdiShieldCrown
    case 'internal':
      return mdiLockAlert
  }
  return undefined
}

/**
 * Returns the corresponding MDI icon based on the HTTP method.
 *
 * @param {string} method - The HTTP method to determine the icon for.
 * Can be one of: `'DELETE'`, `'GET'`, `'HEAD'`, `'OPTIONS'`, `'PATCH'`, `'POST'`, or `'PUT'`.
 * Matching is case-insensitive.
 *
 * @returns {string|undefined} The corresponding MDI path if a match is found, otherwise `undefined`.
 */
export const methodHTTPIcon = (method) => {
  switch (method.toUpperCase()) {
    case 'DELETE':
      return mdiTrashCanOutline
    case 'GET':
      return mdiDownloadOutline
    case 'HEAD':
      return mdiEyeOutline
    case 'OPTIONS':
      return mdiCogOutline
    case 'PATCH':
      return mdiFileDocumentEditOutline
    case 'POST':
      return mdiUploadOutline
    case 'PUT':
      return mdiContentSaveOutline
  }
  return undefined
}

/**
 * Returns a Material Design Icon (MDI) representing the given HTTP response code.
 *
 * The icon is chosen based on the response code class:
 * - `1xx` → Information (`mdiInformationOutline`)
 * - `2xx` → Success (`mdiCheckCircleOutline`)
 * - `3xx` → Redirection (`mdiArrowRightCircleOutline`)
 * - `4xx` → Client Error (`mdiCloseCircleOutline`)
 * - `5xx` → Server Error (`mdiAlertCircleOutline`)
 *
 * @param {number|string} responseCode - The HTTP response code to map.
 * @returns {string|undefined} The corresponding MDI icon name, or `undefined` if not recognized.
 */
export const responseCodeHTTPIcon = (responseCode) => {
  const string = String(responseCode)

  if (string.startsWith('1')) {
    return mdiInformationOutline
  }
  if (string.startsWith('2')) {
    return mdiCheckCircleOutline
  }
  if (string.startsWith('3')) {
    return mdiArrowRightCircleOutline
  }
  if (string.startsWith('4')) {
    return mdiCloseCircleOutline
  }
  if (string.startsWith('5')) {
    return mdiAlertCircleOutline
  }
  return undefined
}

/**
 * Returns a Material Design Icon (MDI) representing the given VM status.
 *
 * Status-to-icon mappings:
 * - `'running'` → `mdiPlayCircle`
 * - `'starting'` → `mdiProgressHelper`
 * - `'stopped'` → `mdiStopCircle`
 * - `'deleting'` → `mdiDelete`
 * - `'cloning'` → `mdiContentCopy`
 * - `'paused'` → `mdiPauseCircle`
 *
 * @param {string} status - The virtual machine status (case-insensitive).
 * @returns {string|undefined} The corresponding MDI icon name, or `undefined` if not recognized.
 */
export const vmStatusIcon = (status) => {
  switch (status?.toLowerCase()) {
    case 'running':
      return mdiPlayCircle
    case 'starting':
      return mdiProgressHelper
    case 'stopped':
      return mdiStopCircle
    case 'deleting':
      return mdiDelete
    case 'cloning':
      return mdiContentCopy
    case 'stopping':
      return mdiProgressHelper
    case 'paused':
      return mdiPauseCircle
    case 'queued':
      return mdiProgressClock
  }
  return undefined
}

/**
 * Returns a Material Design Icon (MDI) representing the given Proxmox HA state
 * of a VM.
 *
 * State-to-icon mappings:
 * - `'started'` → `mdiShieldCheck`
 * - `'stopped'` → `mdiShieldOutline`
 * - `'disabled'` → `mdiShieldOff`
 * - `'ignored'` → `mdiShieldOffOutline`
 * - `'error'` / `'fence'` → `mdiShieldAlert`
 * - transient CRM states → `mdiShieldSync`
 *
 * Unlike `vmStatusIcon` this returns a fallback icon (`mdiShieldHalfFull`)
 * for unknown states so the HA badge always renders an icon.
 *
 * @param {string} state - The Proxmox HA state (case-insensitive).
 * @returns {string} The corresponding MDI icon path.
 */
export const haStateIconVM = (state) => {
  switch (String(state ?? '').toLowerCase()) {
    case 'started':
      return mdiShieldCheck
    case 'stopped':
      return mdiShieldOutline
    case 'disabled':
      return mdiShieldOff
    case 'ignored':
      return mdiShieldOffOutline
    case 'error':
    case 'fence':
      return mdiShieldAlert
    case 'migrate':
    case 'relocate':
    case 'recovery':
    case 'request_start':
    case 'request_stop':
    case 'queued':
    case 'freeze':
      return mdiShieldSync
  }
  return mdiShieldHalfFull
}

/**
 * Returns a Material Design Icon (MDI) representing the given user status.
 *
 * Status-to-icon mappings:
 * - `'active'` → `mdiAccountCheck`
 * - `'banned'` → `mdiBlockHelper`
 * - `'e-mail-pending'` → `mdiEmailAlert`
 * - `'inactive'` → `mdiAccountOff`
 *
 * @param {string} status - The user status (case-insensitive).
 * @returns {string|undefined} The corresponding MDI icon name, or `undefined` if not recognized.
 */
export const userStatusIcon = (status) => {
  switch (status?.toLowerCase()) {
    case 'active':
      return mdiAccountCheck
    case 'banned':
      return mdiBlockHelper
    case 'e-mail-pending':
      return mdiEmailAlert
    case 'inactive':
      return mdiAccountOff
  }
  return undefined
}

/**
 * Returns a Material Design Icon (MDI) representing whether an object is protected.
 *
 * Status-to-icon mapping:
 * - `'true'` → `mdiLockOpenVariant`
 * - anything else → `mdiLock`
 *
 * @param {string|boolean} status - The protection status (case-insensitive if string).
 * @returns {string} The corresponding MDI icon name.
 */
export const protectionObjectIcon = (status) => {
  if (status?.toLowerCase() == 'true') {
    return mdiLockOpenVariant
  }
  return mdiLock
}

/**
 * Returns a Material Design Icon (MDI) representing the user's authentication backend.
 *
 * Status-to-icon mappings:
 * - `'internal'` → `mdiShieldAccount`
 * - `'external'` → `mdiAccountNetwork`
 *
 * @param {string} authBackend - The authentication backend identifier (case-insensitive).
 * @returns {string|undefined} The corresponding MDI icon name, or `undefined` if not recognized.
 */
export const userAuthBackendIcon = (authBackend) => {
  switch (authBackend?.toLowerCase()) {
    case 'internal':
      return mdiShieldAccount
    case 'external':
      return mdiAccountNetwork
  }
  return undefined
}

/**
 * Returns a Material Design Icon (MDI) representing the status of a policy.
 *
 * - `true` → `mdiCheckCircleOutline`
 * - `false` → `mdiCloseCircleOutline`
 *
 * @param {boolean} status - The policy status flag.
 * @returns {string} The corresponding MDI icon name.
 */
export const policyStatusIcon = (status) => {
  if (status) return mdiCheckCircleOutline
  return mdiCloseCircleOutline
}

/**
 * Returns a Material Design Icon (MDI) representing whether a SCIM resource is enabled.
 *
 * - `true` → `mdiCheckCircleOutline`
 * - `false` → `mdiCloseCircleOutline`
 *
 * @param {boolean} enabled - The enabled flag.
 * @returns {string} The corresponding MDI icon name.
 */
export const scimEnabledIcon = (enabled) => {
  if (enabled) return mdiCheckCircleOutline
  return mdiCloseCircleOutline
}

/**
 * Returns a Material Design Icon (MDI) representing the given template status.
 *
 * Status-to-icon mappings:
 * - `'queued'` → `mdiProgressClock`
 * - `'available'` → `mdiCheckCircle`
 * - `'deleting'` → `mdiDeleteRestore`
 * - `'deleted'` → `mdiDelete`
 * - `'error'` → `mdiAlertCircle`
 *
 * @param {string} status - The template status (case-insensitive).
 * @returns {string|undefined} The corresponding MDI icon name, or `undefined` if not recognized.
 */
export const templateStatusIcon = (status) => {
  switch (status?.toLowerCase()) {
    case 'queued':
      return mdiProgressClock
    case 'available':
      return mdiCheckCircle
    case 'deleting':
      return mdiDeleteRestore
    case 'deleted':
      return mdiDelete
    case 'error':
      return mdiAlertCircle
  }
  return undefined
}

/**
 * Returns a Material Design Icon (MDI) representing the given permission key.
 *
 * Key-to-icon mappings (examples):
 * - `'object_create'` → `mdiPlusBoxOutline`
 * - `'object_read'` → `mdiEyeOutline`
 * - `'object_update'` → `mdiPencilOutline`
 * - `'object_delete'` → `mdiTrashCanOutline`
 *
 * @param {string} key - The permission key.
 * @param {string|null} [model] - Optional model identifier to disambiguate
 *   keys shared between models (e.g. VM + Event both use `object_actions_stop`).
 * @returns {string|undefined} The corresponding MDI icon name, or `undefined` if not recognized.
 */
export const permissionKeyIcon = (key, model = null) => {
  if (!key) return undefined
  return getObjectPermissionByKey(key, model)?.icon
}

/**
 * Returns a Material Design Icon (MDI) representing whether a role is a system role.
 *
 * - `true` → `mdiCog` (system role)
 * - `false` → `mdiAccountEditOutline` (custom role)
 *
 * @param {boolean} isProtected - Whether the role is a system role.
 * @returns {string} The corresponding MDI icon name.
 */
export const roleProtectedIcon = (isProtected) => {
  if (isProtected) return mdiCog
  return mdiAccountEditOutline
}
