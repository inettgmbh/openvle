/**
 * Service for Guacamole connection parameter-related API operations.
 */
export default class ConnectionParamsService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/guacamole-connection-params'
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Retrieves a connection param by ID.
   *
   * @param {string} id - The ID of the connection param.
   * @returns {Promise<Object>} A promise resolving to the connection param.
   */
  async get(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data
  }

  /**
   * Retrieves a paginated list of all connection params with optional search and sorting parameters.
   *
   * @param {Object} params - Query parameters for pagination, filtering, and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=200] - Number of entries per page.
   * @param {string} [params.search_field=""] - Field to search by.
   * @param {string} [params.search_value=""] - Search term.
   * @param {string} [params.sort_by="parameter"] - Field to sort by.
   * @param {string} [params.sort_order="asc"] - Sort order (`asc` or `desc`).
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async list(params = {}) {
    const {
      page = 1,
      limit = 200,
      search_field = '',
      search_value = '',
      sort_by = 'parameter',
      sort_order = 'asc',
    } = params

    const { data } = await this.http.get(`${this.path}/`, {
      params: { page, limit, search_field, search_value, sort_by, sort_order },
    })
    return data
  }

  /**
   * Updates an existing connection param.
   *
   * @param {string} id - The ID of the connection param to update.
   * @param {string} default_own - The updated connection param default own.
   * @returns {Promise<Object>} A promise resolving to the updated connection param.
   */
  async update(id, default_own) {
    const { data } = await this.http.put(`${this.path}/${id}`, { default_own })
    return data
  }
}
