import { getI18nT } from '@/i18n'

/**
 * Returns a localized tooltip message based on the given email send status.
 *
 * @param {string} sendStatus - The current status of the email (e.g. 'sent', 'queued', 'error').
 * @returns {string|undefined} A tooltip message describing the status, or `undefined` if unknown.
 */
export const emailSendStatusTooltip = (sendStatus) => {
  const t = getI18nT()
  const key = `tooltips.emailSendStatus.${sendStatus.toLowerCase()}`
  const result = t(key)
  return result !== key ? result : undefined
}

/**
 * Returns a localized tooltip message based on the given event createType.
 *
 * @param {string} createType - The eventId of the event (e.g. null, uuidv4).
 * @returns {string|undefined} A tooltip message describing the createType.
 */
export const eventCreateTypeTooltip = (createType) => {
  const t = getI18nT()
  return createType
    ? t('tooltips.eventCreateType.event')
    : t('tooltips.eventCreateType.manual')
}

/**
 * Returns a localized tooltip message based on the given mail createType.
 *
 * @param {string} createType - The mailId of the mail (e.g. null, uuidv4).
 * @returns {string|undefined} A tooltip message describing the createType.
 */
export const mailCreateTypeTooltip = (createType) => {
  const t = getI18nT()
  return createType
    ? t('tooltips.mailCreateType.event')
    : t('tooltips.mailCreateType.manual')
}

/**
 * Returns a localized tooltip message based on the given task status.
 *
 * @param {string} status - The status of the task (e.g. success, failed, queued, processing).
 * @returns {string|undefined} A tooltip message describing the status.
 */
export const taskStatusTooltip = (status) => {
  const t = getI18nT()
  const key = `tooltips.taskStatus.${status.toLowerCase()}`
  const result = t(key)
  return result !== key ? result : undefined
}

/**
 * Returns a localized tooltip message based on the given system setting visibility.
 *
 * @param {string} visibility - The visibility of the system setting (e.g. public, authenticated, admins, internal).
 * @returns {string|undefined} A tooltip message describing the visibility.
 */
export const systemSettingVisibilityTooltip = (visibility) => {
  const t = getI18nT()
  const key = `tooltips.systemSettingVisibility.${visibility?.toLowerCase()}`
  const result = t(key)
  return result !== key ? result : undefined
}

/**
 * Returns a localized tooltip text for the given authentication backend.
 *
 * @param {string} authBackend - The authentication backend identifier (case-insensitive).
 * @returns {string|undefined} The tooltip text for the backend, or `undefined` if not recognized.
 */
export const userAuthBackendTooltip = (authBackend) => {
  const t = getI18nT()
  const key = `tooltips.userAuthBackend.${authBackend.toLowerCase()}`
  const result = t(key)
  return result !== key ? result : undefined
}

/**
 * Returns a localized tooltip message based on the given template status.
 *
 * @param {string} status - The status of the template (e.g. queued, available, deleting, deleted, error).
 * @returns {string|undefined} A tooltip message describing the status.
 */
export const templateStatusTooltip = (status) => {
  const t = getI18nT()
  const key = `tooltips.templateStatus.${status.toLowerCase()}`
  const result = t(key)
  return result !== key ? result : undefined
}
