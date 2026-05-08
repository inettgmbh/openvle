/**
 * Returns the backend URL.
 *
 * Falls back to current origin if VITE_BACKEND_URL is not set
 * or still contains the Docker placeholder.
 *
 * @returns {string} The backend base URL.
 */
export function getBackendUrl() {
  const envBackendUrl = import.meta.env.VITE_BACKEND_URL
  if (envBackendUrl && !envBackendUrl.endsWith('_PLACEHOLDER')) {
    return envBackendUrl
  }
  return window.location.origin + '/v1/'
}

/**
 * Parses a boolean-ish env variable.
 *
 * Treats only the case-insensitive string 'true' as true. Undefined,
 * empty, unreplaced `*_PLACEHOLDER` values, and any other content map to
 * false. This keeps the dev server runnable without an .env file.
 *
 * @param {unknown} value The raw env value.
 * @returns {boolean}
 */
export function parseBoolEnv(value) {
  return String(value ?? '').toLowerCase() === 'true'
}
