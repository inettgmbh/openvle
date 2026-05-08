/**
 * Service for activity-related API operations.
 */
export default class ActivityService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/activities'
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Retrieves a single activity by ID.
   *
   * @param {string} id - The UUID of the activity.
   * @returns {Promise<Object>} A promise resolving to the activity data.
   */
  async get(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data
  }

  /**
   * Retrieves a paginated list of activities with optional search and sorting parameters.
   *
   * @param {Object} params - Query parameters for pagination, filtering, and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=25] - Number of entries per page.
   * @param {string} [params.search_field=""] - Field to search by.
   * @param {string} [params.search_value=""] - Search term.
   * @param {string} [params.sort_by="timestamp"] - Field to sort by.
   * @param {string} [params.sort_order="desc"] - Sort order (`asc` or `desc`).
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async list(params = {}) {
    const {
      page = 1,
      limit = 25,
      search_field = '',
      search_value = '',
      sort_by = 'timestamp',
      sort_order = 'desc',
    } = params

    const { data } = await this.http.get(`${this.path}/`, {
      params: { page, limit, search_field, search_value, sort_by, sort_order },
    })
    return data
  }

  /**
   * Retrieves a paginated list of own activities with optional search and sorting parameters.
   *
   * @param {Object} params - Query parameters for pagination, filtering, and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=25] - Number of entries per page.
   * @param {string} [params.search_field=""] - Field to search by.
   * @param {string} [params.search_value=""] - Search term.
   * @param {string} [params.sort_by="timestamp"] - Field to sort by.
   * @param {string} [params.sort_order="desc"] - Sort order (`asc` or `desc`).
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async listOwn(params = {}) {
    const {
      page = 1,
      limit = 25,
      search_field = '',
      search_value = '',
      sort_by = 'timestamp',
      sort_order = 'desc',
    } = params

    const { data } = await this.http.get(`${this.path}/own`, {
      params: { page, limit, search_field, search_value, sort_by, sort_order },
    })
    return data
  }
}
