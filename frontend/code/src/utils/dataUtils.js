import { isRef, reactive, ref } from 'vue'

import { getI18nT } from '@/i18n'
import { SYSTEM_USER_ID } from '@/services/UserService'
import { useLookupStore } from '@/stores/lookup'
import { useMainStore } from '@/stores/main'
import { httpStatusCodes } from '@/utils/httpStatusCodes'
import {
  connectionProtocolFormatterIcon,
  eventStatusIconMap,
  methodHTTPIcon,
  policyStatusIcon,
  protectionObjectIcon,
  responseCodeHTTPIcon,
  roleProtectedIcon,
  scimEnabledIcon,
  systemSettingVisibilityIcon,
  taskStatusIcon,
  templateStatusIcon,
  userAuthBackendIcon,
  userStatusIcon,
  vmStatusIcon,
} from '@/utils/icons'
import { getObjectPermissionsOptions } from '@/utils/objectModelPermissions'

/**
 * Resolves one or more UUID fields into readable names using the LookupStore,
 * with optional formatter functions per field and permission checks.
 *
 * @param {Array|Object|Ref} objectsRef - Object, array of objects, or ref to such.
 * @param {Array<{ from: string, to: string, keyspace: string, formatter?: Function }>} mappings
 * @returns {Promise<void>}
 */
export async function resolveFieldFromLookup(objectsRef, mappings) {
  const lookupStore = useLookupStore()

  let objects = isRef(objectsRef) ? objectsRef.value : objectsRef
  const isSingleObject = !Array.isArray(objects)
  if (isSingleObject) objects = [objects]

  await Promise.all(
    mappings.map(async ({ from, to, keyspace, formatter }) => {
      const ids = objects.map((obj) => obj[from])
      const resolved = await lookupStore.resolveMany(keyspace, ids)

      objects.forEach((obj, i) => {
        obj[to] = resolved[i]

        if (typeof formatter === 'function') {
          try {
            const formatted = formatter({ ...obj })
            Object.assign(obj, formatted)
          } catch (error) {
            console.error(
              `Formatter error for ${keyspace} / ${from} → ${to}:`,
              error,
            )
          }
        }
      })
    }),
  )
}

/**
 * Formats the key of an object permission
 * @param {Object} objectPermission - A single object containing an object permission.
 * @returns {Object<void>} objectPermission
 */
export const formatObjectPermissionsKey = (objectPermission) => {
  const match = getObjectPermissionsOptions(
    objectPermission?.object_type || null,
  ).find((option) => option.value === objectPermission.permission_key)

  if (match) {
    objectPermission.permission = match.label
  } else {
    objectPermission.permission = objectPermission.permission_key
  }

  return objectPermission
}

/**
 * Formats a UTC date string into a localized German datetime string.
 *
 * Converts an ISO-8601 UTC timestamp (e.g., "2025-04-23T19:06:34") to a
 * human-readable date-time format like "2025-04-23 21:06:34 MESZ".
 * Automatically adjusts for the local time zone (e.g., CEST/MESZ).
 *
 * @param {string} dateStr - An ISO date string in UTC without a timezone suffix (e.g., "2025-04-23T19:06:34").
 * @param {object} [options] - Optional Intl.DateTimeFormat options for custom formatting.
 * @returns {string} The formatted date-time string based on options, or default "YYYY-MM-DD HH:mm:ss TZ" if no options are given.
 */
export const formatDate = (dateStr, options = null) => {
  if (!dateStr) return ''

  function parseDate(input) {
    if (/\+\d{2}:\d{2}$/.test(input)) {
      // with timezone
      return new Date(input)
    } else if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/.test(input)) {
      // w/o timezone
      return new Date(input + 'Z')
    } else {
      // unknown
      return new Date(input)
    }
  }

  const date = parseDate(dateStr)

  if (isNaN(date.getTime())) return dateStr

  const useRelative = options?.relative === true

  if (useRelative) {
    const now = new Date()
    const diffMs = date - now
    const diffSec = Math.floor(diffMs / 1000)
    const diffMin = Math.floor(diffSec / 60)
    const diffHrs = Math.floor(diffMin / 60)
    const diffDays = Math.floor(diffHrs / 24)

    const t = getI18nT()

    // future dates
    if (diffSec > 0) {
      if (diffSec < 60) return t('date.inFewSeconds')
      if (diffMin < 60) return t('date.inMinutes', { n: diffMin })
      if (diffHrs < 24) return t('date.inHours', { n: diffHrs })
      if (diffDays === 1) return t('date.tomorrow')
      if (diffDays === 0) return t('date.today')
      if (diffDays > 1) return t('date.inDays', { n: diffDays })
    }

    // past dates
    const pastSec = -diffSec

    if (pastSec < 60) return t('date.fewSecondsAgo')
    const pastMin = Math.floor(pastSec / 60)
    if (pastMin < 60) return t('date.minutesAgo', { n: pastMin })
    const pastHrs = Math.floor(pastMin / 60)
    if (pastHrs < 24) return t('date.hoursAgo', { n: pastHrs })
    const pastDays = Math.floor(pastHrs / 24)
    if (pastDays === 1) return t('date.oneDayAgo')
    if (pastDays < 7) return t('date.daysAgo', { n: pastDays })

    const cleanOptions = { ...options }
    delete cleanOptions.relative
    options = cleanOptions
  }

  const defaultOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    timeZoneName: 'short',
  }

  const opts = options || defaultOptions

  if (options) {
    return new Intl.DateTimeFormat('de-DE', opts).format(date)
  }

  const parts = new Intl.DateTimeFormat('de-DE', defaultOptions).formatToParts(
    date,
  )
  const get = (type) => parts.find((p) => p.type === type)?.value

  return `${get('year')}-${get('month')}-${get('day')} ${get('hour')}:${get('minute')}:${get('second')} ${get('timeZoneName')}`
}

/**
 * Formats a date with weekday and time, using relative phrasing for recent dates.
 * e.g. "Heute, 14:35" / "Gestern, 09:12" / "Mo., 17.02.2026, 14:35"
 *
 * @param {string} dateStr - An ISO date string (e.g., "2025-04-23T19:06:34").
 * @returns {string} The formatted date string with weekday and time.
 */
export const formatDateRelativeWithWeekday = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(
    /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/.test(dateStr)
      ? dateStr + 'Z'
      : dateStr,
  )
  if (isNaN(date.getTime())) return dateStr

  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const dateDay = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  const diffDays = Math.round((today - dateDay) / 86400000)

  const time = date.toLocaleTimeString('de-DE', {
    hour: '2-digit',
    minute: '2-digit',
  })

  const t = getI18nT()
  if (diffDays === 0) return t('date.todayAt', { time })
  if (diffDays === 1) return t('date.yesterdayAt', { time })

  const weekday = date.toLocaleDateString('de-DE', { weekday: 'short' })
  const dateFormatted = date.toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
  return `${weekday}, ${dateFormatted}, ${time}`
}

/**
 * Parses a raw MIME-formatted email string and extracts the HTML or plain text content.
 *
 * The function handles multipart email bodies by identifying the boundary delimiter and scanning
 * for parts with either 'text/html' or 'text/plain' content types. It splits headers and body content
 * even if the usual double line breaks (\r\n\r\n) are missing, providing robustness for improperly formatted emails.
 *
 * - If HTML content is found, it is returned as-is.
 * - If only plain text is found, line breaks are converted to <br> for display purposes.
 * - If no valid content is found, a fallback HTML message is returned.
 *
 * @param {string} rawEmail - The full raw email string, including headers and multipart sections.
 * @returns {string} - Extracted HTML content ready to be rendered (e.g., via v-html or srcdoc).
 */
export const parseEmailContent = (rawEmail) => {
  if (!rawEmail || typeof rawEmail !== 'string')
    return `<p><i>${getI18nT()('common.noContent')}</i></p>`

  const boundaryMatch = rawEmail.match(/boundary="?([^";\s]+)"?/)
  if (!boundaryMatch) return rawEmail

  const boundary = boundaryMatch[1]
  const parts = rawEmail.split('--' + boundary)

  for (const part of parts) {
    const isPlainText = /Content-Type:\s*text\/plain/i.test(part)
    const isHtml = /Content-Type:\s*text\/html/i.test(part)

    if (isHtml || isPlainText) {
      const isBase64 = /Content-Transfer-Encoding:\s*base64/i.test(part)
      const bodyMatch = part.match(/\r?\n\r?\n([\s\S]*)/)
      let body = bodyMatch ? bodyMatch[1].trim() : part.trim()

      if (isBase64) {
        try {
          const bytes = Uint8Array.from(atob(body.replace(/\s/g, '')), (c) =>
            c.charCodeAt(0),
          )
          body = new TextDecoder().decode(bytes)
        } catch {
          // If decoding fails, use body as-is
        }
      }

      if (isHtml) {
        return body
      } else {
        return body.replace(/\n/g, '<br>')
      }
    }
  }

  return `<p><i>${getI18nT()('common.noValidContent')}</i></p>`
}

/**
 * Performs multiple permission checks and stores the results in a reactive ref map.
 *
 * @param {Array<{
 *   key: string,
 *   objectType: string,
 *   objectPermission: string,
 *   objectPath: string
 * }>} checks - List of permission checks to perform.
 * @param {Object} refMap - Reactive object where keys map to `ref<boolean>`.
 * @returns {Promise<void>}
 */
export async function checkPermissionsForObjects(checks, refMap) {
  const mainStore = useMainStore()

  await Promise.all(
    checks.map(async ({ key, objectType, objectPermission, objectPath }) => {
      try {
        const result = await mainStore.userCan(
          objectType,
          objectPermission,
          objectPath,
        )
        // If already exists as a ref, just update its value
        if (refMap[key] && isRef(refMap[key])) {
          refMap[key].value = result
        } else {
          // Otherwise, define it as a new ref
          refMap[key] = ref(result)
        }
      } catch (error) {
        console.error(`[permissions] check failed for key "${key}":`, error)
        // Set fallback if error occurs
        refMap[key] = ref(false)
      }
    }),
  )
}

/**
 * Creates a reactive object for storing permission result refs.
 *
 * This object is used as a target container for functions like `checkPermissionsForObjects`
 * or `checkObjectPermissions`, where permission keys (e.g. `canEdit`, `canDelete`) are stored
 * as `ref<boolean>` values inside this reactive object.
 *
 * @returns {Object} A reactive object that will dynamically hold `ref<boolean>` entries keyed by permission names.
 */
export function usePermissionRefs() {
  return reactive({})
}

/**
 * Performs default permission checks (e.g. edit/delete) + optional extras in one call.
 *
 * @param {string} objectType - The object type (e.g. `applications`)
 * @param {string} objectId - The object's UUID
 * @param {Object} refMap - The reactive permission ref map (e.g. from `usePermissionRefs`)
 * @param {Array<{
 *   key: string,
 *   objectType: string,
 *   objectPermission: string,
 *   objectPath: string
 * }>} [extraChecks] - Optional additional checks (e.g. object_permissions)
 * @param {Array<string>} [defaultKeys] - Which default keys to check (defaults to ['canEdit', 'canDelete'])
 */
export async function checkObjectPermissions(
  objectType,
  objectId,
  refMap,
  extraChecks = [],
  defaultKeys = ['canEdit', 'canDelete'],
) {
  const defaultPermissionMappings = {
    canEdit: 'update',
    canDelete: 'delete',
    canRead: 'read',
    canCreate: 'create',
  }

  const defaultChecks = defaultKeys.map((key) => {
    const objectPermission = defaultPermissionMappings[key]
    if (!objectPermission) {
      throw new Error(`[checkObjectPermissions] Unknown default key: ${key}`)
    }

    return {
      key,
      objectType,
      objectPermission,
      objectPath: `/${objectId}`,
    }
  })

  const allChecks = [...defaultChecks, ...extraChecks]
  await checkPermissionsForObjects(allChecks, refMap)
}

/**
 * Formats a email send status into a human readable string.
 *
 * @param {string} emailStatus - The send status of the email.
 * @returns {string} The formatted send status of the email ([`Gesendet`, `Warteschlange`, `Fehler`]).
 */
export const emailStatusFormatter = (emailStatus) => {
  const t = getI18nT()
  switch (String(emailStatus).toLowerCase()) {
    case 'sent':
      return t('status.sent')
    case 'queued':
      return t('status.queued')
    case 'error':
      return t('status.error')
  }
  return String(emailStatus)
}

/**
 * Returns a formatted connection label with masked password information.
 *
 * The label is constructed using the connection's protocol, username, vm / template name, and port,
 * while the password is masked for security reasons.
 * Example format: `ssh://user:***@hostname:22`
 *
 * @param {Object} connection - The connection details (useful for future syntax changes).
 * @param {string} protocol - The connection protocol (e.g. 'ssh', 'rdp', 'vnc', 'k8s', 'tel').
 * @param {string} username - The username for authentication.
 * @param {string} entity - The target vm / template name.
 * @param {number|string} port - The port number used for the connection.
 * @returns {string} A formatted and masked connection string.
 */
export const connectionProfileLabelFormatter = (
  connection,
  protocol,
  username,
  entity,
  port,
) => {
  return `${protocol}://${username}:***@${entity}:${port}`
}

/**
 * Resolves an object model name to its corresponding URL path segment.
 *
 * This function normalizes various object model identifiers to their pluralized
 * and routable URL counterparts, used for building navigation or API paths.
 *
 * Supported mappings:
 * - 'mail' or 'mails' → 'mails'
 * - 'guacamole' or 'guacamoles' → 'guacamoles'
 * - 'virtualmachine' → 'vms'
 * - 'event' → 'events'
 *
 * @param {string} objectModel - The name of the object model (case-insensitive).
 * @returns {string|null} The corresponding URL path segment, or `null` if unknown.
 */
export const resolveObjectTypeURL = (objectModel) => {
  switch (String(objectModel).toLowerCase()) {
    case 'mail':
      return 'mails'
    case 'mails':
      return 'mails'
    case 'guacamole':
      return 'guacamoles'
    case 'guacamoles':
      return 'guacamoles'
    case 'virtualmachine':
      return 'vms'
    case 'event':
      return 'events'
  }
  return null
}

/**
 * Export any JS object/array as a JSON file and trigger download.
 *
 * @param {any} data - The data to export (must be serializable).
 * @param {string} [filename='data'] - The filename without extension.
 * @returns {Promise<void>}
 */
export async function exportJsonFile(data, filename = 'data') {
  const t = getI18nT()

  if (data === undefined) {
    throw new Error(t('validation.noDataForExport'))
  }

  let jsonStr

  try {
    jsonStr = JSON.stringify(data, null, 2)
  } catch (err) {
    throw new Error(
      t('validation.jsonSerializationFailed', { error: err.message }),
    )
  }

  const blob = new Blob([jsonStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${filename}.json`

  a.click()

  URL.revokeObjectURL(url)
}

/**
 * Attempts to cast a given value to the specified type and validates it.
 *
 * This function normalizes and converts the provided value into the desired type
 * (e.g., converts `"true"`/`"false"` to booleans, parses numbers, or parses JSON strings for objects/arrays)
 * before performing strict validation against the type rules.
 *
 * @param {*} value - The value to cast and validate.
 * @param {string} type - The expected data type (`boolean`, `integer`, `float`, `object`, `array`, or `string`).
 * @param {boolean} [returnCasted=false] - If `true`, returns the casted value on success instead of `true`.
 * @returns {true|*|string} Returns `true` (or the casted value if `returnCasted` is true) if valid,
 *                          otherwise an error message string describing the validation failure.
 */
export function valueValidator(value, type, returnCasted = false) {
  const t = getI18nT()
  let castedValue = value

  switch ((type || '').toLowerCase()) {
    /** Validate booleans */
    case 'boolean':
      if (typeof castedValue === 'string') {
        if (castedValue.toLowerCase() === 'true') {
          castedValue = true
        } else if (castedValue.toLowerCase() === 'false') {
          castedValue = false
        }
      }
      if (typeof castedValue !== 'boolean') {
        return t('validation.booleanRequired')
      }
      return returnCasted ? castedValue : true

    /** Validate integers */
    case 'integer': {
      const parsedValue = parseInt(castedValue, 10)
      if (
        !Number.isInteger(parsedValue) ||
        parsedValue !== Number(castedValue)
      ) {
        return t('validation.integerRequired')
      }
      castedValue = parsedValue
      return returnCasted ? castedValue : true
    }

    /** Validate floats */
    case 'float': {
      const normalizedValue = String(castedValue).replace(',', '.')
      const hasDecimalPoint =
        normalizedValue.includes('.') || normalizedValue.includes(',')
      const parsedValue = parseFloat(normalizedValue)
      if (
        isNaN(parsedValue) ||
        (parsedValue === parseInt(parsedValue, 10) && hasDecimalPoint)
      ) {
        return t('validation.floatRequired')
      }
      castedValue = parsedValue
      return returnCasted ? castedValue : true
    }

    /** Validate objects */
    case 'object': {
      try {
        const trimmedValue = String(castedValue).trim()
        if (trimmedValue === 'null' || trimmedValue === '') {
          return t('validation.nullOrEmpty')
        }
        const parsedValue = JSON.parse(trimmedValue)
        if (typeof parsedValue !== 'object' || Array.isArray(parsedValue)) {
          return t('validation.objectRequired')
        }
        castedValue = parsedValue
      } catch {
        return t('validation.objectRequired')
      }
      return returnCasted ? castedValue : true
    }

    /** Validate arrays */
    case 'array':
      try {
        const parsedValue = JSON.parse(castedValue)
        if (!Array.isArray(parsedValue)) {
          return t('validation.arrayRequired')
        }
        castedValue = parsedValue
      } catch {
        return t('validation.arrayRequired')
      }
      return returnCasted ? castedValue : true

    /** Validate strings (and rest) */
    default:
      if (typeof castedValue !== 'string' || castedValue.trim() === '') {
        return t('validation.stringRequired')
      }
      if (castedValue.length < 1 || castedValue.length > 250) {
        return t('validation.stringLength')
      }
      return returnCasted ? castedValue : true
  }
}

/**
 * Determines the appropriate HTML input type for a given value based on its expected data type.
 *
 * @param {string} type - The expected data type (`boolean`, `integer`, `float`, `array`, `object`, or `string`).
 * @param {*} value - The current value, used to determine if a long string should be rendered as a textarea.
 * @returns {string} Returns the suggested HTML input type (`boolean`, `number`, `textarea`, or `text`).
 */
export function getHTMLInputType(type, value) {
  switch ((type || '').toLowerCase()) {
    case 'boolean':
      return 'boolean'
    case 'integer':
      return 'number'
    case 'float':
      return 'number'
    case 'array':
    case 'object':
      return 'textarea'
    default:
      if (String(value).length >= 35) {
        return 'textarea'
      }
  }
  return 'text'
}

/**
 * Formats a raw setting value for persistence based on its declared type.
 *
 * - float: Ensures at least one decimal place if none is provided.
 * - object: Trims, converts '' or 'null' to `null`; otherwise parses JSON and pretty-prints it.
 * - array:  Trims, converts '' or 'null' to `null`; otherwise parses JSON (must be an array) and pretty-prints it.
 * - string: Trims the value.
 * - null:   Trims the value (keeps original behavior from existing code).
 *
 * For all other types, the value is returned unchanged.
 *
 * @param {string} type - The declared data type (`float`, `object`, `array`, `string`, `null`, etc.).
 * @param {*} value - The raw input value (usually a string).
 * @returns {*} The formatted value ready for persistence.
 * @throws {Error} If the JSON is invalid or the array validation fails.
 */
export function formatSettingValue(type, value) {
  const t = String(type || '').toLowerCase()

  const safeTrim = (v) => (v == null ? '' : String(v).trim())

  switch (t) {
    case 'float': {
      const s = String(value ?? '')
      const hasDotOrComma = s.includes('.') || s.includes(',')
      if (!hasDotOrComma) {
        return parseFloat(s).toFixed(1)
      }
      return value
    }

    case 'object': {
      const trimmed = safeTrim(value)
      if (trimmed === '' || trimmed === 'null') return null
      try {
        const parsed = JSON.parse(trimmed)
        return JSON.stringify(parsed, null, 2)
      } catch {
        throw new Error(getI18nT()('validation.invalidJson'))
      }
    }

    case 'array': {
      const trimmed = safeTrim(value)
      if (trimmed === '' || trimmed === 'null') return null
      try {
        const parsed = JSON.parse(trimmed)
        if (!Array.isArray(parsed)) {
          throw new Error(getI18nT()('validation.arrayRequired'))
        }
        return JSON.stringify(parsed, null, 2)
      } catch (e) {
        if (
          e instanceof Error &&
          e.message !== getI18nT()('validation.arrayRequired')
        ) {
          throw new Error(getI18nT()('validation.invalidJsonArray'))
        }
        throw e
      }
    }

    case 'string':
      return safeTrim(value)

    case 'null':
      return safeTrim(value)

    default:
      return value
  }
}

/**
 * Returns a user profile link if the given `by` ID is valid and different from `byId`.
 * Skips system entries and a predefined special user ID.
 *
 * @param {string} by - The ID or identifier of the actor (could be 'system' or a UUID).
 * @param {string} byId - The UUID of the related user to link to.
 * @returns {string|null} The URL path to the user profile (`/users/{byId}`) or `null` if no link should be shown.
 */
export function getUserLink(by, byId) {
  if (by === 'system') return null
  if (by === SYSTEM_USER_ID) return null
  if (by !== byId) return `/users/${byId}`
  return null
}

/**
 * Formats a visibility of a system setting into a human-readable label.
 *
 * @param {string} visibility - The visibility value to format (e.g., 'public', 'authenticated', 'admins', 'internal').
 * @returns {string} The formatted label, or the original value if no match is found.
 */
export function formatSystemSettingVisibility(visibility) {
  const v = String(visibility || '').toLowerCase()
  const t = getI18nT()

  switch (v) {
    case 'public':
      return t('visibility.public')
    case 'authenticated':
      return t('visibility.authenticated')
    case 'admins':
      return t('visibility.admins')
    case 'internal':
      return t('visibility.internal')
  }

  return visibility
}

/**
 * Validates an event slug to ensure it meets the required format.
 *
 * The slug must:
 * - Not be `null`, `undefined`, or an empty string
 * - Not be the string `"null"` (case-insensitive)
 * - Contain only uppercase letters (A-Z), lowercase letters (a-z), digits (0-9), hyphens (-), or underscores (_)
 * - Be between 4 and 8 characters in length
 *
 * @param {string|number|null|undefined} value - The slug value to validate.
 * @returns {true|string} Returns `true` if the slug is valid, otherwise returns an error message.
 */
export function validateEventSlug(value) {
  const t = getI18nT()

  if (value === null || value === undefined) {
    return t('validation.nullOrEmpty')
  }

  const trimmedValue = String(value).trim()

  if (trimmedValue === '' || trimmedValue.toLowerCase() === 'null') {
    return t('validation.nullOrEmpty')
  }

  const slugPattern = /^[a-z0-9_-]{4,8}$/
  if (!slugPattern.test(trimmedValue)) {
    return t('validation.slugFormat')
  }

  return true
}

/**
 * Maps internal object type identifiers to their corresponding display names.
 *
 * This object is used to provide user-friendly, localized labels for various system entities.
 * It supports both plural and singular forms, as well as variations in casing or naming.
 *
 * Examples:
 * - `'users'` → `'Person'`
 * - `'templates'` → `'VM-Vorlage'`
 * - `'Application'` → `'Anwendung'`
 *
 * @param {string} type
 * @param {{ plural?: boolean }} [options]
 * @returns {string | undefined}
 */
/**
 * Maps normalized type keys to i18n objectType keys.
 * @type {Record<string, string>}
 */
const OBJECT_TYPE_I18N_MAP = {
  activity: 'activity',
  application: 'application',
  changelog: 'changelog',
  course: 'course',
  dashboard: 'dashboard',
  document: 'document',
  event: 'event',
  eventmembership: 'eventMembership',
  guacamole: 'guacamole',
  guacamoleconnectionprofile: 'guacamoleConnectionProfile',
  mail: 'mail',
  mailtemplate: 'mailTemplate',
  os: 'os',
  permission: 'permission',
  policy: 'policy',
  policymembership: 'policyMembership',
  role: 'role',
  subtask: 'subtask',
  tag: 'tag',
  task: 'task',
  template: 'template',
  user: 'user',
  vendor: 'vendor',
  virtualmachine: 'virtualMachine',
}

const TYPE_ALIASES = {
  activities: 'activity',
  app: 'application',
  apps: 'application',
  applications: 'application',
  changelogs: 'changelog',
  connections: 'guacamole',
  courses: 'course',
  dashboards: 'dashboard',
  documents: 'document',
  events: 'event',
  eventmemberships: 'eventmembership',
  guacamoles: 'guacamole',
  guacamoleconnectionprofiles: 'guacamoleconnectionprofile',
  mails: 'mail',
  mailtemplates: 'mailtemplate',
  objectpermission: 'permission',
  objectpermissions: 'permission',
  permissions: 'permission',
  policies: 'policy',
  policymemberships: 'policymembership',
  roles: 'role',
  subtask: 'subtask',
  subtasks: 'subtask',
  tags: 'tag',
  tasks: 'task',
  templates: 'template',
  users: 'user',
  virtualmachines: 'virtualmachine',
}

function normalizeType(type) {
  return String(type).toLowerCase().replace(/[_-]/g, '')
}

export function resolveObjectTypeLabel(type, { plural = false } = {}) {
  if (!type) return undefined

  const normalized = normalizeType(type)
  const resolvedKey = TYPE_ALIASES[normalized] ?? normalized
  const i18nKey = OBJECT_TYPE_I18N_MAP[resolvedKey]

  if (!i18nKey) return undefined

  const t = getI18nT()
  const form = plural ? 'plural' : 'singular'
  return t(`objectTypes.${i18nKey}.${form}`)
}

/**
 * @deprecated Use resolveObjectTypeLabel instead.
 */
export const resolveObjectTypeToGerman = resolveObjectTypeLabel

/**
 * Maps backend object type identifiers to their corresponding frontend URL paths.
 *
 * This object is used to translate internal or API-level type names into routable
 * frontend path segments used for navigation (e.g. in Vue Router or breadcrumb components).
 *
 * It handles singular/plural forms and different casing variants to ensure consistent routing.
 *
 * Examples:
 * - `'Course'` → `'courses'`
 * - `'VirtualMachine'` → `'vms'`
 * - `'MailTemplate'` → `'mail-templates'`
 *
 * @type {Record<string, string>}
 */
export const resolveObjectTypeToFrontendURLs = {
  apps: 'applications',
  applications: 'applications',
  Application: 'applications',
  Course: 'courses',
  courses: 'courses',
  events: 'events',
  Guacamole: 'guacamoles',
  guacamole: 'guacamoles',
  guacamoles: 'guacamoles',
  guacamole_connection_profiles: 'connections',
  GuacamoleConnectionProfile: 'connections',
  mails_templates: 'mail-templates',
  MailTemplate: 'mail-templates',
  os: 'os',
  OS: 'os',
  permissions: 'permissions',
  Policy: 'policies',
  policies: 'policies',
  roles: 'roles',
  templates: 'templates',
  template: 'templates',
  Template: 'templates',
  Templates: 'templates',
  users: 'users',
  vendor: 'vendors',
  virtual_machines: 'vms',
  vm: 'vms',
  vms: 'vms',
  VirtualMachine: 'vms',
  VirtualMachines: 'vms',
}

/**
 * Formats a given value as a German locale number string.
 *
 * - `null` and `undefined` are returned as-is.
 * - `boolean` values are returned unchanged.
 * - `number` values are formatted with `Intl.NumberFormat('de-DE')`,
 *   preserving the number of decimal places.
 * - `string` values are sanitized (trimming, removing spaces, normalizing separators)
 *   and parsed into numbers if possible, then formatted as numbers.
 *   Invalid or unparsable strings are returned unchanged.
 *
 * Supported input examples:
 * - `1234.56` → `"1.234,56"`
 * - `"1,234.56"` → `"1234,56"`
 * - `"1.234,56"` → `"1234,56"`
 * - `"   12 345,67 "` → `"12.345,67"`
 *
 * @param {number|string|boolean|null|undefined} value - The value to format.
 * @returns {string|number|boolean|null|undefined} A formatted string if value is numeric, otherwise the original value.
 */
export const formatGermanNumber = (value) => {
  if (value === null || value === undefined) return value
  if (typeof value === 'boolean') return value

  if (typeof value === 'number') {
    if (!Number.isFinite(value)) return value

    const asStr = String(value)
    const decimals = (asStr.split('.')[1] || '').length
    return new Intl.NumberFormat('de-DE', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value)
  }

  if (typeof value === 'string') {
    const original = value
    let s = value.trim()

    if (s === '') return original

    s = s
      .replace(/\u00A0/g, ' ')
      .replace(/'/g, "'")
      .replace(/ /g, '')

    const hasComma = s.includes(',')
    const hasDot = s.includes('.')

    if (hasComma && hasDot) {
      const lastComma = s.lastIndexOf(',')
      const lastDot = s.lastIndexOf('.')
      if (lastComma > lastDot) {
        s = s.replace(/\./g, '').replace(',', '.')
      } else {
        s = s.replace(/,/g, '')
      }
    } else if (hasComma && !hasDot) {
      s = s.replace(',', '.')
    }

    if (!/^[-+]?\d*(\.\d+)?$/.test(s)) return original

    const num = Number(s)
    if (!Number.isFinite(num)) return original

    const decimals = (s.split('.')[1] || '').length

    return new Intl.NumberFormat('de-DE', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(num)
  }

  return value
}

/**
 * Builds a list of HTTP method filter options including label and icon.
 *
 * Each filter entry contains:
 * - `value`: the HTTP method (e.g. 'GET', 'POST')
 * - `label`: a human-readable label (identical to the value here)
 * - `icon`: the corresponding icon resolved by {@link methodHTTPIcon}
 *
 * Useful for UI components such as dropdowns or filter menus where HTTP methods
 * need to be selectable with visual indicators.
 *
 * @returns {Array<{ value: string, label: string, icon: string }>} An array of filter objects.
 */
export const methodHTTPFilters = () => {
  const methods = ['DELETE', 'GET', 'HEAD', 'OPTIONS', 'PATCH', 'POST', 'PUT']

  const filters = methods.map((m) => ({
    value: m,
    label: m,
    icon: methodHTTPIcon(m),
  }))
  return filters
}

/**
 * Builds a list of HTTP response code filter options including label and icon.
 *
 * Uses `httpStatusCodes` (a mapping of HTTP status codes to human-readable labels)
 * and enriches each entry with the appropriate MDI icon from {@link responseCodeHTTPIcon}.
 *
 * Each filter object contains:
 * - `value`: the HTTP status code as a string (e.g. `'200'`)
 * - `label`: the descriptive label (e.g. `'OK'`)
 * - `icon`: the corresponding icon for the status code class
 *
 * @returns {Array<{ value: string, label: string, icon: string }>} An array of filter objects for all HTTP response codes.
 */
export const responseCodeHTTPFilters = () => {
  return Object.entries(httpStatusCodes).map(([code, label]) => ({
    value: code,
    label,
    icon: responseCodeHTTPIcon(code),
  }))
}

/**
 * Builds a list of system setting visibility filter options with icons.
 *
 * Each option contains:
 * - `value`: the visibility level identifier
 * - `label`: the localized label for display
 * - `icon`: an icon representing the visibility level (via {@link systemSettingVisibilityIcon})
 *
 * Available visibility levels:
 * - `'admins'` → `'Admins'`
 * - `'authenticated'` → `'Angemeldet'`
 * - `'internal'` → `'Intern'`
 * - `'public'` → `'Öffentlich'`
 *
 * @returns {Array<{ value: string, label: string, icon: string }>} An array of filter objects for all visibility options.
 */
export const visibilitySystemSettingFilter = () => {
  const t = getI18nT()
  const visibilityOptions = [
    { value: 'admins', label: t('visibility.admins') },
    { value: 'authenticated', label: t('visibility.authenticated') },
    { value: 'internal', label: t('visibility.internal') },
    { value: 'public', label: t('visibility.public') },
  ]

  return visibilityOptions.map((opt) => ({
    ...opt,
    icon: systemSettingVisibilityIcon(opt.value),
  }))
}

/**
 * Builds a list of event status filter options with icons.
 *
 * Each option contains:
 * - `value`: the UUID of the event status (hardcoded; breaks if backend UUIDs change)
 * - `label`: the localized label for display (e.g. 'Aktiv', 'Geplant')
 * - `icon`: an icon representing the event status (via {@link eventStatusIconMap})
 *
 * Available statuses include:
 * - `'Archiviert'`
 * - `'Fehler'`
 * - `'Archiving'`
 * - `'Deploying'`
 * - `'Aktiv'`
 * - `'Stopped'`
 * - `'Geplant'`
 * - `'Inaktiv'`
 *
 * @returns {Array<{ value: string, label: string, icon: string }>} An array of filter objects for all event statuses.
 */
export const statusEventFilter = () => {
  const t = getI18nT()
  // fixme: this breaks if uuids of event status change
  const visibilityOptions = [
    {
      value: 'bfbee14d-6f04-4ba1-a39c-0f5764f0563d',
      label: t('status.archived'),
      icon: eventStatusIconMap.archived,
    },
    {
      value: 'f63a9362-eb67-4769-ba93-62eb67b76939',
      label: t('status.errorCore'),
      icon: eventStatusIconMap.errorCore,
    },
    {
      value: 'e5c9fafd-c5ec-4aa5-89fa-fdc5ec0aa595',
      label: t('status.errorDeployment'),
      icon: eventStatusIconMap.errorDeployment,
    },
    {
      value: 'af12d859-9aa6-4fae-92d8-599aa6ffae93',
      label: t('status.errorArchiving'),
      icon: eventStatusIconMap.errorArchiving,
    },
    {
      value: '4d99fe64-3c3c-4a2f-99fe-643c3c1a2f23',
      label: t('status.archiving'),
      icon: eventStatusIconMap.archiving,
    },
    {
      value: 'f13303bf-b25f-4869-9717-698a4db13ada',
      label: t('status.deploying'),
      icon: eventStatusIconMap.deploying,
    },
    {
      value: 'f481fb68-4e6b-4027-bf67-ae431bd8b6d1',
      label: t('status.active'),
      icon: eventStatusIconMap.active,
    },
    {
      value: '1fc851bf-5f4e-4937-bae9-c6d3fd0e5846',
      label: t('status.stopped'),
      icon: eventStatusIconMap.stopped,
    },
    {
      value: '53b6993a-57d6-40a6-8d42-e55bf08fac4c',
      label: t('status.planned'),
      icon: eventStatusIconMap.planned,
    },
    {
      value: 'cbc20092-629b-483f-babc-ef26202d685e',
      label: t('status.inactive'),
      icon: eventStatusIconMap.inactive,
    },
  ]

  return visibilityOptions
    .slice()
    .sort((a, b) => a.label.localeCompare(b.label, 'de'))
}

/**
 * Builds a list of VM status filter options with icons.
 *
 * Each option contains:
 * - `value`: the VM status identifier
 * - `label`: the display label for the status
 * - `icon`: the corresponding MDI icon (via {@link vmStatusIcon})
 *
 * Supported statuses:
 * - `'running'` → Running
 * - `'starting'` → Starting
 * - `'stopped'` → Stopped
 * - `'deleting'` → Deleting
 * - `'cloning'` → Cloning
 * - `'paused'` → Paused
 *
 * @returns {Array<{ value: string, label: string, icon: string }>} An array of VM status filter objects.
 */
export const statusVMFilter = () => {
  const t = getI18nT()
  // fixme: this breaks if uuids of vm status change
  const statusOptions = [
    { value: 'running', label: t('status.running') },
    { value: 'starting', label: t('status.starting') },
    { value: 'stopped', label: t('status.stopped') },
    { value: 'deleting', label: t('status.deleting') },
    { value: 'cloning', label: t('status.cloning') },
    { value: 'stopping', label: t('status.stopping') },
    { value: 'paused', label: t('status.paused') },
    { value: 'queued', label: t('status.queued') },
  ]

  return statusOptions.map((opt) => ({
    ...opt,
    icon: vmStatusIcon(opt.value),
  }))
}

/**
 * Returns the display label for a user status value.
 *
 * @param {string} status - The user status identifier (e.g. `'Active'`).
 * @returns {string} The localized label, or the original value if unknown.
 */
export const userStatusLabel = (status) => {
  const t = getI18nT()
  switch (status?.toLowerCase()) {
    case 'active':
      return t('status.active')
    case 'inactive':
      return t('status.inactive')
    case 'banned':
      return t('status.banned')
    case 'e-mail-pending':
      return t('status.emailPending')
  }
  return status ?? ''
}

/**
 * Builds a list of user status filter options with icons.
 *
 * Each option contains:
 * - `value`: the user status identifier (e.g. `'Active'`)
 * - `label`: the display label for the status
 * - `icon`: the corresponding MDI icon (via {@link userStatusIcon})
 *
 * Supported statuses:
 * - `'Active'`
 * - `'Banned'`
 * - `'E-Mail-Pending'`
 * - `'Inactive'`
 *
 * @returns {Array<{ value: string, label: string, icon: string }>} An array of user status filter objects.
 */
export const statusUserFilter = () => {
  const statusOptions = [
    { value: 'Active', label: userStatusLabel('Active') },
    { value: 'Banned', label: userStatusLabel('Banned') },
    { value: 'E-Mail-Pending', label: userStatusLabel('E-Mail-Pending') },
    { value: 'Inactive', label: userStatusLabel('Inactive') },
  ]

  return statusOptions.map((opt) => ({
    ...opt,
    icon: userStatusIcon(opt.value),
  }))
}

/**
 * Builds a list of filter options for the SCIM enabled flag, including icons.
 *
 * @returns {Array<{ value: string, label: string, icon: string }>} An array of filter objects.
 */
export const scimEnabledFilter = () => {
  const t = getI18nT()
  return [
    {
      value: 'True',
      label: t('status.active'),
      icon: scimEnabledIcon(true),
    },
    {
      value: 'False',
      label: t('status.inactive'),
      icon: scimEnabledIcon(false),
    },
  ]
}

/**
 * Returns a localized label for the role protected status.
 *
 * @param {boolean} isProtected - Whether the role is a system role.
 * @returns {string} The localized label.
 */
export const roleProtectedLabel = (isProtected) => {
  const t = getI18nT()
  if (isProtected) return t('status.system')
  return t('status.manual')
}

/**
 * Builds a list of filter options for the role protected status, including icons.
 *
 * @returns {Array<{ value: string, label: string, icon: string }>} An array of filter objects.
 */
export const roleProtectedFilter = () => {
  return [
    {
      value: 'True',
      label: roleProtectedLabel(true),
      icon: roleProtectedIcon(true),
    },
    {
      value: 'False',
      label: roleProtectedLabel(false),
      icon: roleProtectedIcon(false),
    },
  ]
}

/**
 * Builds a list of filter options for the policy "active" status, including icons.
 *
 * Each option contains:
 * - `value`: stringified boolean (`'True'` or `'False'`)
 * - `label`: localized label (`'Aktiv'` or `'Inaktiv'`)
 * - `icon`: an icon representing the status (via {@link policyStatusIcon})
 *
 * @returns {Array<{ value: string, label: string, icon: string }>} An array of filter objects for policy status.
 */
export const statusPolicyFilter = () => {
  const t = getI18nT()
  return [
    {
      value: 'True',
      label: t('common.active'),
      icon: policyStatusIcon(true),
    },
    {
      value: 'False',
      label: t('common.inactive'),
      icon: policyStatusIcon(false),
    },
  ]
}

/**
 * Builds a list of filter options for the "protected" flag of objects, including icons.
 *
 * Each option contains:
 * - `value`: stringified boolean (`'True'` or `'False'`)
 * - `label`: localized label (`'Ja'` or `'Nein'`)
 * - `icon`: an icon representing the protection state (via {@link protectionObjectIcon})
 *
 * @returns {Array<{ value: string, label: string, icon: string }>} An array of filter objects for protected objects.
 */
export const protectedObjectFilter = () => {
  const t = getI18nT()
  const statusOptions = [
    { value: 'True', label: t('common.yes') },
    { value: 'False', label: t('common.no') },
  ]

  return statusOptions.map((opt) => ({
    ...opt,
    icon: protectionObjectIcon(opt.value),
  }))
}

/**
 * Builds a list of authentication backend filter options for users, including icons.
 *
 * Each option contains:
 * - `value`: the backend identifier (`'internal'` or `'external'`)
 * - `label`: the localized display label (`'Intern'` or `'Extern'`)
 * - `icon`: the corresponding icon for the backend (via {@link userAuthBackendIcon})
 *
 * @returns {Array<{ value: string, label: string, icon: string }>} An array of filter objects for user authentication backends.
 */
export const authBackendUserFilter = () => {
  const t = getI18nT()
  const statusOptions = [
    { value: 'internal', label: t('status.internal') },
    { value: 'external', label: t('status.external') },
  ]

  return statusOptions.map((opt) => ({
    ...opt,
    icon: userAuthBackendIcon(opt.value),
  }))
}

/**
 * Validates whether a given avatar style name is supported.
 *
 * The function checks if the provided `input` matches one of the predefined
 * avatar style identifiers. Returns `true` if valid, otherwise `false`.
 *
 * Supported styles include (among others):
 * - `'adventurer'`, `'avataaars'`, `'bottts'`, `'croodles'`, `'funEmoji'`, `'pixelArt'`
 * - Both normal and neutral variants are allowed (e.g. `'adventurerNeutral'`).
 *
 * @param {string} input - The avatar style name to validate.
 * @returns {boolean} `true` if the input is a valid avatar style, otherwise `false`.
 */
export const avatarStyleValidator = (input) => {
  const validStyles = [
    'adventurer',
    'adventurerNeutral',
    'avataaars',
    'avataaarsNeutral',
    'bigEars',
    'bigEarsNeutral',
    'bigSmile',
    'bottts',
    'botttsNeutral',
    'croodles',
    'croodlesNeutral',
    'dylan',
    'funEmoji',
    'glass',
    'icons',
    'identicon',
    'initials',
    'lorelei',
    'loreleiNeutral',
    'micah',
    'miniavs',
    'notionists',
    'notionistsNeutral',
    'openPeeps',
    'personas',
    'pixelArt',
    'pixelArtNeutral',
    'rings',
    'shapes',
    'thumbs',
  ]

  if (validStyles.includes(input)) {
    return true
  } else {
    return false
  }
}

/**
 * Maps event bulk action identifiers to their corresponding object type
 * and backend action name.
 *
 * This mapping is used to translate UI bulk-action keys into the correct
 * backend request parameters for performing actions on virtual machines
 * or Guacamole connections.
 *
 * Structure of each entry:
 * - `type`   → the backend resource type (e.g. `'virtual-machines'`, `'guacamoles'`)
 * - `action` → the backend action to perform (e.g. `'start'`, `'delete'`)
 *
 * @type {Record<string, { type: string, action: string }>}
 */
export const eventActionsMapping = {
  startVMs: { type: 'virtual-machines', action: 'start' },
  shutdownVMs: { type: 'virtual-machines', action: 'shutdown' },
  rebootVMs: { type: 'virtual-machines', action: 'reboot' },
  stopVMs: { type: 'virtual-machines', action: 'stop' },
  resetVMs: { type: 'virtual-machines', action: 'reset' },
  migrateVMs: { type: 'virtual-machines', action: 'migrate' },
  pauseVMs: { type: 'virtual-machines', action: 'pause' },
  resumeVMs: { type: 'virtual-machines', action: 'resume' },
  hibernateVMs: { type: 'virtual-machines', action: 'hibernate' },

  createConnections: { type: 'guacamoles', action: 'create' },
  deleteConnections: { type: 'guacamoles', action: 'delete' },
}

/**
 * Returns a localized label for a given template status.
 *
 * Status-to-label mappings:
 * `'queued'`, `'available'`, `'deleting'`, `'deleted'`, `'error'`
 *
 * Any unknown or missing value returns `'Unknown'`.
 *
 * @param {string} status - The template status (case-insensitive).
 * @returns {string} The label representing the template status.
 */
export const templateStatusFormatter = (status) => {
  const t = getI18nT()
  switch (status?.toLowerCase()) {
    case 'queued':
      return t('status.queued')
    case 'available':
      return t('status.available')
    case 'deleting':
      return t('status.deleting')
    case 'deleted':
      return t('status.deleted')
    case 'error':
      return t('status.error')
  }
  return t('status.unknown')
}

/**
 * Builds a list of template status filter options with icons.
 *
 * Each option contains:
 * - `value`: the template status identifier
 * - `label`: the display label for the status
 * - `icon`: the corresponding MDI icon (via {@link templateStatusIcon})
 *
 * Supported statuses:
 * - `'queued'` → In Warteschlange
 * - `'available'` → Verfügbar
 * - `'deleting'` → Löschen
 * - `'deleted'` → Gelöscht
 * - `'error'` → Fehlerhaft
 *
 * @returns {Array<{ value: string, label: string, icon: string }>} An array of template status filter objects.
 */
export const statusTemplateFilter = () => {
  const t = getI18nT()
  const statusOptions = [
    { value: 'queued', label: t('status.queued') },
    { value: 'available', label: t('status.available') },
    { value: 'deleting', label: t('status.deleting') },
    { value: 'deleted', label: t('status.deleted') },
    { value: 'error', label: t('status.error') },
  ]

  return statusOptions.map((opt) => ({
    ...opt,
    icon: templateStatusIcon(opt.value),
  }))
}

/**
 * Builds a list of task status filter options including corresponding icons.
 *
 * Each option contains:
 * - `value`: the internal task status identifier
 * - `label`: the localized label
 * - `icon`: the corresponding MDI icon (via {@link taskStatusIcon})
 *
 * Supported statuses:
 * - `'success'`     → Erfolgreich
 * - `'failed'`      → Fehlgeschlagen
 * - `'queued'`      → In Warteschlange
 * - `'processing'`  → In Bearbeitung
 *
 * @returns {Array<{ value: string, label: string, icon: string }>}
 *          An array of enriched task status filter options.
 */
export const statusTaskFilter = () => {
  const t = getI18nT()
  const statusOptions = [
    { value: 'queued', label: t('status.queued') },
    { value: 'processing', label: t('status.processing') },
    { value: 'success', label: t('status.success') },
    { value: 'failed', label: t('status.failed') },
  ]

  return statusOptions.map((opt) => ({
    ...opt,
    icon: taskStatusIcon(opt.value),
  }))
}

/**
 * Builds a list of connection profiles protocol filter options including label and icon.
 *
 * Each filter entry contains:
 * - `value`: the protocol (e.g. 'ssh', 'rdp', 'vnc', 'k8s', 'tel')
 * - `label`: a human-readable label (identical to the value here)
 * - `icon`: the corresponding icon resolved by {@link connectionProtocolFormatterIcon}
 *
 * Useful for UI components such as dropdowns or filter menus where HTTP methods
 * need to be selectable with visual indicators.
 *
 * @returns {Array<{ value: string, label: string, icon: string }>} An array of filter objects.
 */
export const protocolConnectionFilter = () => {
  const statusOptions = [
    // { value: 'k8s', label: 'Kubernetes' },
    { value: 'rdp', label: 'RDP' },
    { value: 'ssh', label: 'SSH' },
    // { value: 'tel', label: 'Telnet' },
    { value: 'vnc', label: 'VNC' },
  ]

  return statusOptions.map((opt) => ({
    ...opt,
    icon: connectionProtocolFormatterIcon(opt.value),
  }))
}

/**
 * Builds a Base64-encoded Guacamole client identifier string.
 *
 * The identifier is composed of the connection ID, connection type, and
 * authentication provider, separated by NULL (`\u0000`) characters,
 * as required by Apache Guacamole.
 *
 * Format before encoding:
 * `{connectionId}\0{type}\0{authProvider}`
 *
 * @param {string} connectionId - The Guacamole connection identifier.
 * @param {string} [type='c'] - The connection type (`'c'` for connection, `'g'` for group).
 * @param {string} [authProvider='postgresql'] - The authentication provider name.
 * @returns {string} The Base64-encoded Guacamole client identifier.
 */
export function buildGuacamoleClientIdentifier(
  connectionId,
  type = 'c',
  authProvider = 'postgresql',
) {
  const NULL = '\u0000'

  const raw = `${connectionId}${NULL}${type}${NULL}${authProvider}`

  return btoa(raw)
}

/**
 * Converts a locale key (e.g. 'de_DE', 'en_GB') to a flag emoji
 * using the country part.
 *
 * @param {string} key - Locale code in format 'language_COUNTRY'.
 * @returns {string} Flag emoji.
 */
export function keyToFlag(key) {
  const code = key.split(/[-_]/)[1].toUpperCase().slice(0, 2)
  return String.fromCodePoint(
    ...code.split('').map((c) => c.charCodeAt(0) + 0x1f1a5),
  )
}
