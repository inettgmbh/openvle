/**
 * Service for system settings API operations.
 */
export default class SystemService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/system/settings'
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Retrieves a paginated list of all system settings.
   *
   * @param {Object} params - Query parameters.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=200] - Number of entries per page.
   * @param {string} [params.search_field=""] - Field to search by.
   * @param {string} [params.search_value=""] - Search term.
   * @param {string} [params.sort_by="key"] - Field to sort by.
   * @param {string} [params.sort_order="asc"] - Sort order.
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async list(params = {}) {
    const {
      page = 1,
      limit = 200,
      search_field = '',
      search_value = '',
      sort_by = 'key',
      sort_order = 'asc',
    } = params

    const { data } = await this.http.get(this.path, {
      params: { page, limit, search_field, search_value, sort_by, sort_order },
      timeout: 10000,
    })
    return data
  }

  /**
   * Updates an existing system setting.
   *
   * @param {string} id - The ID of the system setting.
   * @param {string} value - Updated value.
   * @returns {Promise<Object>} A promise resolving to the updated setting.
   */
  async update(id, value) {
    const { data } = await this.http.put(`${this.path}/${id}`, { value })
    return data
  }
}
