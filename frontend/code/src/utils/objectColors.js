/**
 * Returns the color for the vm status.
 * @param {string} status - The status of the virtual machine.
 * @returns {Promise<void>}
 * @returns {string} One of the following color names: 'success', 'danger', 'warning', 'info', or 'contrast'.
 */
export const statusColorVM = (status) => {
  if (status == null) {
    return 'danger'
  }
  switch (status.toLowerCase()) {
    case 'running':
      return 'success'
    case 'starting':
      return 'success'
    case 'stopping':
      return 'danger'
    case 'stopped':
      return 'danger'
    case 'deleting':
      return 'danger'
    case 'cloning':
      return 'warning'
    case 'paused':
      return 'info'
  }
  return 'contrast'
}

/**
 * Returns the color for the user status.
 * @param {string} status - The status of the user.
 * @returns {string} One of the following color names: 'success', 'danger', 'warning', 'info', or 'contrast'.
 */
export const statusColorUser = (status) => {
  if (status == null) {
    return 'danger'
  }
  switch (status.toLowerCase()) {
    case 'active':
      return 'success'
    case 'inactive':
      return 'warning'
    case 'banned':
      return 'danger'
    case 'e-mail-pending':
      return 'info'
  }
  return 'contrast'
}

/**
 * Returns the color for the event status.
 * @param {string} status - The status of the event.
 * @returns {string} One of the following color names: 'success', 'danger', 'warning', 'info', or 'contrast'.
 */
export const statusColorEvent = (status) => {
  if (status == null) {
    return 'danger'
  }
  switch (status.toLowerCase()) {
    case 'aktiv':
      return 'success'
    case 'archiviert':
      return 'info'
    case 'archiving':
      return 'warning'
    case 'deploying':
      return 'warning'
    case 'fehler':
      return 'danger'
    case 'core fehler':
      return 'danger'
    case 'fehler (core)':
      return 'danger'
    case 'deployment fehler':
      return 'danger'
    case 'fehler (deployment)':
      return 'danger'
    case 'archival fehler':
      return 'danger'
    case 'fehler (archivierung)':
      return 'danger'
    case 'geplant':
      return 'warning'
    case 'inaktiv':
      return 'info'
    case 'stopped':
      return 'info'
  }
  return 'contrast'
}

/**
 * Returns the color for the course status.
 * @param {string} status - The status of the course.
 * @returns {string} One of the following color names: 'success', 'danger', 'warning', 'info', or 'contrast'.
 */
export const statusColorCourse = (status) => {
  if (status == null) {
    return 'danger'
  }
  switch (status.toLowerCase()) {
    case 'aktiv':
      return 'success'
    case 'starting':
      return 'success'
    case 'stopped':
      return 'danger'
    case 'geplant':
      return 'warning'
    case 'inaktiv':
      return 'info'
  }
  return 'contrast'
}

/**
 * Returns the color for the policy status.
 * @param {string} status - The status of the policy.
 * @returns {string} One of the following color names: 'success', or 'danger'.
 */
export const statusColorPolicy = (status) => {
  if (status) {
    return 'success'
  }
  return 'danger'
}

/**
 * Returns the color for the SCIM enabled status.
 * @param {boolean} enabled - Whether the SCIM resource is enabled.
 * @returns {string} One of the following color names: 'success', or 'danger'.
 */
export const statusColorScimEnabled = (enabled) => {
  if (enabled) {
    return 'success'
  }
  return 'danger'
}

/**
 * Returns the color for the mail templates actions.
 * @param {string} status - The status of the mail template.
 * @returns {string} One of the following color names: 'success', or 'info'.
 */
export const statusColorMailTemplate = (status) => {
  if (status) {
    return 'success'
  }
  return 'info'
}

/**
 * Returns the color for the mail send status.
 * @param {string} status - The status of the mail.
 * @returns {string} One of the following color names: 'success', 'danger', 'warning', or 'info'.
 */
export const statusColorMail = (status) => {
  if (status == null) return 'warning'

  switch (status.toLowerCase()) {
    case 'sent':
      return 'success'
    case 'queued':
      return 'info'
    case 'error':
      return 'danger'
  }
  return 'warning'
}

/**
 * Returns the color for the activity response code.
 * @param {string} activityResponse - The response code of the activity.
 * @returns {string} One of the following color names: 'success', 'danger', 'warning', 'info', or 'contrast'.
 */
export const responseCodeColorActivity = (activityResponse) => {
  const string = String(activityResponse)

  if (string.startsWith('2')) {
    return 'success'
  }
  if (string.startsWith('3')) {
    return 'info'
  }
  if (string.startsWith('4')) {
    return 'warning'
  }
  if (string.startsWith('5')) {
    return 'danger'
  }
  return 'contrast'
}

/**
 * Returns the color for the connection protocol.
 * @param {string} connectionProtocol - The protocol of the connection.
 * @returns {string} One of the following color names: 'success', 'info', 'warning', 'danger', or 'contrast'.
 */
export const protocolColorConnection = (connectionProtocol) => {
  const string = String(connectionProtocol).toLowerCase()

  switch (string) {
    case 'ssh':
      return 'success'
    case 'rdp':
      return 'info'
    case 'vnc':
      return 'warning'
    case 'k8s':
      return 'danger'
    case 'tel':
      return 'contrast'
  }
  return 'contrast'
}

/**
 * Returns the color for the connection create type.
 * @param {string} connectionType - The type of the connection.
 * @returns {string} One of the following color names: 'success', or 'info'.
 */
export const createTypeColorConnection = (connectionType) => {
  if (connectionType !== null) return 'success'
  return 'info'
}

/**
 * Returns the color for the mail create type.
 * @param {string} mailType - The type of the mail.
 * @returns {string} One of the following color names: 'success', or 'info'.
 */
export const createTypeColorMail = (mailType) => {
  if (mailType !== null) return 'success'
  return 'info'
}

/**
 * Returns the color for the task status.
 * @param {string} status - The status of the task.
 * @returns {Promise<void>}
 * @returns {string} One of the following color names: 'success', 'danger', 'info', 'warning', or 'contrast'.
 */
export const statusColorTask = (status) => {
  if (status == null) {
    return 'danger'
  }
  switch (status.toLowerCase()) {
    case 'success':
      return 'success'
    case 'failed':
      return 'danger'
    case 'queued':
      return 'info'
    case 'processing':
      return 'warning'
  }
  return 'contrast'
}

/**
 * Returns the color for the system setting visibility.
 * @param {string} visibility - The visibility of the system setting (e.g. public, authenticated, admins, internal).
 * @returns {Promise<void>}
 * @returns {string} One of the following color names: 'success', 'danger', 'warning', 'info', or 'contrast'.
 */
export const visibilityColorSystemSetting = (visibility) => {
  if (visibility == null || visibility === undefined) {
    return 'danger'
  }
  switch (visibility.toLowerCase()) {
    case 'public':
      return 'danger'
    case 'authenticated':
      return 'info'
    case 'admins':
      return 'success'
    case 'internal':
      return 'warning'
  }
  return 'contrast'
}

/**
 * Returns a color identifier for a given HTTP method.
 *
 * The color codes are typically used for styling activity indicators or badges in the UI.
 * Mappings:
 * - `GET` → `'info'`
 * - `POST` → `'success'`
 * - `PUT` / `PATCH` → `'warning'`
 * - `DELETE` → `'danger'`
 * - any other → `'contrast'`
 *
 * @param {string} method - The HTTP method to map (case-insensitive).
 * @returns {'info'|'success'|'warning'|'danger'|'contrast'} The color identifier for the method.
 */
export const responseMethodColorActivity = (method) => {
  const m = String(method).toUpperCase()

  if (m === 'GET') {
    return 'info'
  }
  if (m === 'POST') {
    return 'success'
  }
  if (m === 'PUT' || m === 'PATCH') {
    return 'warning'
  }
  if (m === 'DELETE') {
    return 'danger'
  }
  return 'contrast'
}

/**
 * Returns a color identifier for a given authentication backend.
 *
 * - If no backend is provided (`null` or `undefined`), `'danger'` is returned.
 * - Otherwise, `'info'` is returned.
 *
 *
 * @param {string|null|undefined} authBackend - The authentication backend identifier.
 * @returns {'danger'|'info'} The color identifier for the backend.
 */
export const authBackendColorUser = (authBackend) => {
  if (authBackend == null) {
    return 'danger'
  }
  return 'info'
}

/**
 * Returns the color for the template status.
 * @param {string} status - The status of the template.
 * @returns {Promise<void>}
 * @returns {string} One of the following color names: 'success', 'danger', 'warning', 'info', or 'contrast'.
 */
export const statusColorTemplates = (status) => {
  if (status == null) {
    return 'danger'
  }
  switch (status.toLowerCase()) {
    case 'queued':
      return 'info'
    case 'available':
      return 'success'
    case 'deleting':
      return 'warning'
    case 'deleted':
      return 'warning'
    case 'error':
      return 'danger'
  }
  return 'contrast'
}

/**
 * Returns the color for the role protected status.
 * @param {boolean} isProtected - Whether the role is a system role.
 * @returns {string} One of the following color names: 'info', or 'success'.
 */
export const statusColorRoleProtected = (isProtected) => {
  if (isProtected) {
    return 'info'
  }
  return 'success'
}
