/**
 * Formats a retry duration in seconds to a localized string,
 * switching to minutes (rounded up) once a full minute is reached.
 *
 * Lives in its own file (not in dataUtils.js) to avoid a circular
 * import: BackendClient.js consumes this helper, and dataUtils.js
 * already imports stores/services that lead back to BackendClient.
 *
 * @param {number} seconds - Remaining seconds until retry is allowed.
 * @param {Function} t - vue-i18n translate function.
 * @returns {string} Localized duration string (e.g. "30 Sekunden", "11 Minuten").
 */
export function formatRetryDuration(seconds, t) {
  if (seconds >= 60) {
    const minutes = Math.ceil(seconds / 60)
    return t('views.rateLimit.minutes', { count: minutes }, minutes)
  }
  return t('views.rateLimit.seconds', { count: seconds }, seconds)
}
