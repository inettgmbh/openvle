/**
 * Service for policy-related API operations.
 */
export default class PolicyService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/policies'
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Creates a new policy.
   *
   * @param {Object} data - Policy data.
   * @param {string} data.name - The name of the policy.
   * @param {string} data.description - The description of the policy.
   * @param {string} data.content - The HTML content of the policy.
   * @returns {Promise<Object>} A promise resolving to the created policy.
   */
  async create(data) {
    const { name, description, content } = data
    const { data: result } = await this.http.post(`${this.path}/`, {
      name,
      description,
      content,
    })
    return result
  }

  /**
   * Retrieves a single policy by ID.
   *
   * @param {string} id - The ID of the policy.
   * @returns {Promise<Object>} A promise resolving to the policy data.
   */
  async get(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data
  }

  /**
   * Retrieves a paginated list of all policies with optional search and sorting parameters.
   *
   * @param {Object} params - Query parameters for pagination, filtering, and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.search_field=""] - Field to search by.
   * @param {string} [params.search_value=""] - Search term.
   * @param {string} [params.sort_by="name"] - Field to sort by.
   * @param {string} [params.sort_order="asc"] - Sort order (`asc` or `desc`).
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
   * Updates an existing policy.
   *
   * @param {string} id - The ID of the policy.
   * @param {Object} data - Fields to update.
   * @param {string} [data.name] - The updated policy name.
   * @param {string} [data.description] - The updated description.
   * @param {string} [data.content] - The updated HTML content.
   * @returns {Promise<Object>} A promise resolving to the updated policy.
   */
  async update(id, data) {
    const { data: result } = await this.http.put(`${this.path}/${id}`, data)
    return result
  }

  /**
   * Deletes a policy by ID.
   *
   * @param {string} id - The ID of the policy to delete.
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
   * Retrieves a single policy name by ID.
   *
   * @param {string} id - The ID of the policy.
   * @returns {Promise<string>} A promise resolving to the policy name.
   */
  async getName(id) {
    const policy = await this.get(id)
    return policy.name
  }

  /**
   * Searches policies by name.
   *
   * @param {string} query - The value to search by.
   * @returns {Promise<{ items: Array<Object>, pageDetails: Object }>}
   */
  async search(query) {
    const { data } = await this.http.get(`${this.path}/`, {
      params: {
        page: 1,
        limit: 25,
        sort_by: 'name',
        sort_order: 'asc',
        search_field: 'name',
        search_value: query,
      },
    })
    return data
  }

  // ============================================================
  // Policy Actions
  // ============================================================

  /**
   * Marks a policy as agreed by the current user.
   *
   * @param {string} id - The ID of the policy.
   * @returns {Promise<Object>} A promise resolving to the agreement result.
   */
  async agree(id) {
    const { data } = await this.http.post(`${this.path}/${id}/actions`, {
      agree: true,
    })
    return data
  }

  /**
   * Enables a policy by ID.
   *
   * @param {string} id - The ID of the policy to enable.
   * @returns {Promise<Object>} A promise resolving to the updated policy.
   */
  async enable(id) {
    const { data } = await this.http.put(`${this.path}/${id}`, { active: true })
    return data
  }

  /**
   * Disables a policy by ID.
   *
   * @param {string} id - The ID of the policy to disable.
   * @returns {Promise<Object>} A promise resolving to the updated policy.
   */
  async disable(id) {
    const { data } = await this.http.put(`${this.path}/${id}`, {
      active: false,
    })
    return data
  }

  // ============================================================
  // Related Resources
  // ============================================================

  /**
   * Retrieves a paginated list of users who agreed to the specified policy.
   *
   * @param {string} id - The ID of the policy.
   * @param {Object} params - Query parameters for pagination and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.sort_by="name"] - Field to sort by.
   * @param {string} [params.sort_order="asc"] - Sort order (`asc` or `desc`).
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async getUsers(id, params = {}) {
    const {
      page = 1,
      limit = 10,
      sort_by = 'name',
      sort_order = 'asc',
    } = params

    const { data } = await this.http.get(`${this.path}/users/`, {
      params: {
        page,
        limit,
        search_field: 'policy_id',
        search_value: id,
        sort_by,
        sort_order,
      },
    })
    return data
  }

  /**
   * Retrieves a paginated list of policies a user has agreed to.
   *
   * @param {string} userId - The user ID.
   * @param {Object} params - Query parameters for pagination and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.sort_by="name"] - Field to sort by.
   * @param {string} [params.sort_order="asc"] - Sort order (`asc` or `desc`).
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async listByUser(userId, params = {}) {
    const {
      page = 1,
      limit = 10,
      sort_by = 'name',
      sort_order = 'asc',
    } = params

    const { data } = await this.http.get(`${this.path}/users`, {
      params: {
        page,
        limit,
        search_field: 'user_id',
        search_value: userId,
        sort_by,
        sort_order,
      },
    })
    return data
  }

  /**
   * Checks whether a user has agreed to a specific policy.
   *
   * @param {string} policyId - The ID of the policy.
   * @param {string} userId - The ID of the user.
   * @returns {Promise<Object>} A promise resolving to the agreement status.
   */
  async checkUserAgreed(policyId, userId) {
    const { data } = await this.http.get(
      `${this.path}/${policyId}/users/${userId}`,
    )
    return data
  }
}
