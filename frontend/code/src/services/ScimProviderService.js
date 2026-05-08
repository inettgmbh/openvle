/**
 * Service for SCIM Provider (inbound) API operations.
 */
export default class ScimProviderService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/scim-providers'
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Creates a new SCIM provider.
   *
   * @param {Object} data - Provider details.
   * @param {string} data.name - The name of the provider.
   * @param {string} [data.description] - A description of the provider.
   * @param {boolean} [data.enabled] - Whether the provider is enabled.
   * @param {string} [data.default_user_status] - Default status for provisioned users.
   * @returns {Promise<Object>} A promise resolving to the created provider (includes bearer_token).
   */
  async create(data) {
    const { name, description, enabled, default_user_status } = data
    const { data: result } = await this.http.post(`${this.path}/`, {
      name,
      description,
      enabled,
      default_user_status,
    })
    return result
  }

  /**
   * Retrieves a single SCIM provider by ID.
   *
   * @param {string} id - The ID of the provider.
   * @returns {Promise<Object|false>} A promise resolving to the provider data, or false on error.
   */
  async get(id) {
    try {
      const { data } = await this.http.get(`${this.path}/${id}`)
      return data
    } catch {
      return false
    }
  }

  /**
   * Retrieves a paginated list of SCIM providers.
   *
   * @param {Object} params - Query parameters.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.search_field=""] - Field to search by.
   * @param {string} [params.search_value=""] - Search term.
   * @param {string} [params.sort_by="name"] - Field to sort by.
   * @param {string} [params.sort_order="asc"] - Sort order.
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async list(params = {}) {
    const {
      page = 1,
      limit = 10,
      search_field = '',
      search_value = '',
      sort_by = 'name',
      sort_order = 'asc',
    } = params

    const { data } = await this.http.get(`${this.path}/`, {
      params: { page, limit, search_field, search_value, sort_by, sort_order },
    })
    return data
  }

  /**
   * Updates an existing SCIM provider.
   *
   * @param {string} id - The ID of the provider.
   * @param {Object} data - The fields to update.
   * @returns {Promise<Object>} A promise resolving to the updated provider.
   */
  async update(id, data) {
    const { data: result } = await this.http.put(`${this.path}/${id}`, data)
    return result
  }

  /**
   * Deletes a SCIM provider by ID.
   *
   * @param {string} id - The ID of the provider to delete.
   * @returns {Promise<Object>} A promise resolving to the deletion result.
   */
  async delete(id) {
    const { data } = await this.http.delete(`${this.path}/${id}`)
    return data
  }

  // ============================================================
  // Helper Methods for Lookup/Dropdown
  // ============================================================

  /**
   * Retrieves the name of a SCIM provider by ID.
   *
   * @param {string} id - The ID of the provider.
   * @returns {Promise<string>} A promise resolving to the provider name.
   */
  async getName(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data.name
  }

  /**
   * Fetches all SCIM providers and formats them for dropdown usage.
   *
   * @returns {Promise<Array<{ label: string, value: string }>>}
   */
  async dropdown() {
    const { items } = await this.list({
      page: 1,
      limit: 200,
      sort_by: 'name',
      sort_order: 'asc',
    })
    return items.map(({ name, id }) => ({
      label: name,
      value: id,
    }))
  }

  /**
   * Searches SCIM providers by name.
   *
   * @param {string} query - The value to search by.
   * @returns {Promise<{ items: Array<Object>, pageDetails: Object }>}
   */
  async search(query) {
    const response = await this.list({
      page: 1,
      limit: 25,
      sort_by: 'name',
      sort_order: 'asc',
      search_field: 'name',
      search_value: query,
    })
    return {
      items: response.items,
      pageDetails: response.pageDetails,
    }
  }

  // ============================================================
  // Token Management
  // ============================================================

  /**
   * Rotates the bearer token for a SCIM provider.
   *
   * @param {string} id - The ID of the provider.
   * @returns {Promise<Object>} A promise resolving to the provider with new token.
   */
  async rotateToken(id) {
    const { data } = await this.http.post(`${this.path}/${id}/rotate-token`)
    return data
  }

  // ============================================================
  // Role Management
  // ============================================================

  /**
   * Replaces roles assigned to a SCIM provider.
   *
   * @param {string} id - The ID of the provider.
   * @param {Array<Object>} roles - List of role objects to assign.
   * @returns {Promise<Object>} A promise resolving to the updated provider.
   */
  async updateRoles(id, roles) {
    const { data } = await this.http.put(`${this.path}/${id}/roles`, {
      roles,
    })
    return data
  }

  /**
   * Adds roles to a SCIM provider.
   *
   * @param {string} id - The ID of the provider.
   * @param {Array<Object>} roles - List of role objects to add.
   * @returns {Promise<Object>} A promise resolving to the updated provider.
   */
  async addRoles(id, roles) {
    const { data } = await this.http.post(`${this.path}/${id}/roles`, {
      roles,
    })
    return data
  }
}
