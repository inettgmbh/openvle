/**
 * Service for SCIM Client (outbound) API operations.
 */
export default class ScimClientService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/scim-clients'
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Creates a new SCIM client.
   *
   * @param {Object} data - Client details.
   * @param {string} data.name - The name of the client.
   * @param {string} [data.description] - A description of the client.
   * @param {boolean} [data.enabled] - Whether the client is enabled.
   * @param {string} data.endpoint_url - The target SCIM endpoint URL.
   * @param {boolean} [data.sync_groups] - Whether to sync groups.
   * @returns {Promise<Object>} A promise resolving to the created client (includes bearer_token).
   */
  async create(data) {
    const {
      name,
      description,
      enabled,
      endpoint_url,
      bearer_token,
      sync_groups,
    } = data
    const { data: result } = await this.http.post(`${this.path}/`, {
      name,
      description,
      enabled,
      endpoint_url,
      bearer_token,
      sync_groups,
    })
    return result
  }

  /**
   * Retrieves a single SCIM client by ID.
   *
   * @param {string} id - The ID of the client.
   * @returns {Promise<Object|false>} A promise resolving to the client data, or false on error.
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
   * Retrieves a paginated list of SCIM clients.
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
   * Updates an existing SCIM client.
   *
   * @param {string} id - The ID of the client.
   * @param {Object} data - The fields to update.
   * @returns {Promise<Object>} A promise resolving to the updated client.
   */
  async update(id, data) {
    const { data: result } = await this.http.put(`${this.path}/${id}`, data)
    return result
  }

  /**
   * Deletes a SCIM client by ID.
   *
   * @param {string} id - The ID of the client to delete.
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
   * Retrieves the name of a SCIM client by ID.
   *
   * @param {string} id - The ID of the client.
   * @returns {Promise<string>} A promise resolving to the client name.
   */
  async getName(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data.name
  }

  /**
   * Fetches all SCIM clients and formats them for dropdown usage.
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
   * Searches SCIM clients by name.
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
  // Role Management
  // ============================================================

  /**
   * Replaces roles assigned to a SCIM client.
   *
   * @param {string} id - The ID of the client.
   * @param {Array<Object>} roles - List of role objects to assign.
   * @returns {Promise<Object>} A promise resolving to the updated client.
   */
  async updateRoles(id, roles) {
    const { data } = await this.http.put(`${this.path}/${id}/roles`, {
      roles,
    })
    return data
  }

  /**
   * Adds roles to a SCIM client.
   *
   * @param {string} id - The ID of the client.
   * @param {Array<Object>} roles - List of role objects to add.
   * @returns {Promise<Object>} A promise resolving to the updated client.
   */
  async addRoles(id, roles) {
    const { data } = await this.http.post(`${this.path}/${id}/roles`, {
      roles,
    })
    return data
  }

  // ============================================================
  // Role Mappings
  // ============================================================

  /**
   * Retrieves role mappings for a SCIM client.
   *
   * @param {string} id - The ID of the client.
   * @param {Object} params - Query parameters.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.sort_by="last_synced_at"] - Field to sort by.
   * @param {string} [params.sort_order="desc"] - Sort order.
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async getRoleMappings(id, params = {}) {
    const {
      page = 1,
      limit = 10,
      sort_by = 'last_synced_at',
      sort_order = 'desc',
    } = params

    const { data } = await this.http.get(`${this.path}/${id}/group-mappings`, {
      params: { page, limit, sort_by, sort_order },
    })
    return data
  }

  // ============================================================
  // User Mappings
  // ============================================================

  /**
   * Retrieves user mappings for a SCIM client.
   *
   * @param {string} id - The ID of the client.
   * @param {Object} params - Query parameters.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.sort_by="last_synced_at"] - Field to sort by.
   * @param {string} [params.sort_order="desc"] - Sort order.
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async getUserMappings(id, params = {}) {
    const {
      page = 1,
      limit = 10,
      sort_by = 'last_synced_at',
      sort_order = 'desc',
    } = params

    const { data } = await this.http.get(`${this.path}/${id}/user-mappings`, {
      params: { page, limit, sort_by, sort_order },
    })
    return data
  }
}
