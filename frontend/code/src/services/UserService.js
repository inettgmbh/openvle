export const SYSTEM_USER_ID = '1db3d8ac-22d9-4116-976a-93ad6e4fb234'
const SYSTEM_USER_NAME = 'System'
const SYSTEM_USER_LABEL = `${SYSTEM_USER_NAME} <system>`

/**
 * Service for user-related API operations.
 */
export default class UserService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/users'
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Creates a new user.
   *
   * @param {Object} data - User details.
   * @param {string} data.username - The login name of the user.
   * @param {string} data.email - The email address of the user.
   * @param {string} data.name - The display name of the user.
   * @param {string} data.status - The status assigned to the user.
   * @param {string} [data.locale=''] - The locale setting for the user.
   * @param {string} [data.password=''] - Optional initial password.
   * @param {string} [data.password_repeat=''] - Repeat of the initial password.
   * @returns {Promise<Object>} A promise resolving to the created user.
   */
  async create(data) {
    const {
      username,
      email,
      name,
      status,
      locale,
      password = '',
      password_repeat = '',
    } = data
    const { data: result } = await this.http.post(`${this.path}/`, {
      username,
      email,
      name,
      status,
      locale,
      password,
      password_repeat,
    })
    return result
  }

  /**
   * Retrieves a user by ID.
   *
   * @param {string} id - The ID of the user.
   * @returns {Promise<Object>} A promise resolving to the user object.
   */
  async get(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data
  }

  /**
   * Retrieves a paginated list of users with optional search and sorting parameters.
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
   * Updates basic user information.
   *
   * @param {string} id - The ID of the user.
   * @param {Object} data - The fields to update.
   * @param {string} [data.name] - New display name.
   * @param {string} [data.email] - New email address.
   * @param {string} [data.status] - New status.
   * @param {string} [data.locale] - New locale.
   * @returns {Promise<Object>} A promise resolving to the updated user.
   */
  async update(id, data) {
    const { data: result } = await this.http.put(`${this.path}/${id}`, data)
    return result
  }

  /**
   * Deletes a user by ID.
   *
   * @param {string} id - The ID of the user.
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
   * Retrieves the username of a user by ID (for lookup).
   *
   * @param {string} id - The ID of the user.
   * @returns {Promise<string>} A promise resolving to the username.
   */
  async getName(id) {
    const user = await this.get(id)
    return user?.username ?? ''
  }
  async getNameNew(id) {
    const { data } = await this.http.get(`${this.path}/`, {
      params: {
        page: 1,
        limit: 1,
        search_field: 'id',
        search_value: id,
        sort_by: 'username',
      },
    })
    return data.items[0]?.username ?? id
  }

  /**
   * Fetches users and maps them to label/value pairs for dropdowns.
   *
   * @returns {Promise<Array<{ label: string, value: string }>>} Dropdown options.
   */
  async dropdown() {
    const { items } = await this.list({
      page: 1,
      limit: 200,
      sort_by: 'name',
      sort_order: 'asc',
    })
    return items.map(({ name, username, id }) => ({
      label: `${name} (${username})`,
      value: id,
    }))
  }

  /**
   * Searches users by name.
   *
   * @param {string} query - The value to search by (user name).
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
    const formattedItems = response.items.map(
      ({ name, email, id, ...rest }) => ({
        ...rest,
        name: `${name} <${email}>`,
        id,
      }),
    )

    // Include system user if query matches
    if (SYSTEM_USER_NAME.toLowerCase().includes(query.toLowerCase())) {
      formattedItems.unshift({ id: SYSTEM_USER_ID, name: SYSTEM_USER_LABEL })
    }

    return {
      items: formattedItems,
      pageDetails: response.pageDetails,
    }
  }

  /**
   * Retrieves and formats a user by ID.
   *
   * @param {string} id - The ID of the user.
   * @returns {Promise<string>} A promise resolving to the formatted name and email string.
   */
  async formatById(id) {
    if (id === SYSTEM_USER_ID) return SYSTEM_USER_LABEL
    const user = await this.get(id)
    return `${user.name} <${user.email}>`
  }

  // ============================================================
  // Preload Methods
  // ============================================================

  /**
   * Fetches a preloaded list of users with a fixed pagination limit.
   *
   * @returns {Promise<{ pageDetails: Object, items: Object[] }>}
   */
  async preload() {
    const { data } = await this.http.get(`${this.path}/`, {
      params: { page: 1, limit: 200 },
    })

    const cleanedUsers = data.items.map((obj) => ({
      id: obj.id,
      name: obj.username ?? obj.id,
    }))

    return {
      pageDetails: data.pageDetails,
      items: cleanedUsers,
    }
  }

  /**
   * Sets a new password for another user.
   *
   * @param {string} id - The ID of the user.
   * @param {string} passwordNew - New password to set.
   * @param {string} passwordNewRepeat - Repeated new password.
   * @returns {Promise<Object>} A promise resolving to the update result.
   */
  async setPassword(id, passwordNew, passwordNewRepeat) {
    const { data } = await this.http.post(`${this.path}/${id}/password`, {
      password_new: passwordNew,
      password_new_repeat: passwordNewRepeat,
    })
    return data
  }

  // ============================================================
  // Role Management
  // ============================================================

  /**
   * Retrieves all roles assigned to a user.
   *
   * @param {string} id - The ID of the user.
   * @returns {Promise<Array<Object>>} A promise resolving to the list of roles.
   */
  async getRoles(id) {
    const { data } = await this.http.get(`${this.path}/${id}/roles`)
    return data
  }

  /**
   * Assigns a role to a user.
   *
   * @param {string} id - The ID of the user.
   * @param {string} roleKey - The key of the role to assign.
   * @returns {Promise<Object>} A promise resolving to the updated user.
   */
  async addRole(id, roleKey) {
    const { data } = await this.http.post(`${this.path}/${id}/roles`, {
      roles: [{ key: roleKey }],
    })
    return data
  }

  /**
   * Updates all roles of a user.
   *
   * @param {string} id - The ID of the user.
   * @param {Array<Object>} roles - Array of role objects to assign.
   * @returns {Promise<Object>} A promise resolving to the updated user.
   */
  async updateRoles(id, roles) {
    const { data } = await this.http.put(`${this.path}/${id}/roles`, { roles })
    return data
  }

  /**
   * Removes a specific role from a user.
   *
   * @param {string} id - The ID of the user.
   * @param {string} roleKey - The key of the role to remove.
   * @returns {Promise<Object>} A promise resolving to the updated user.
   */
  async deleteRole(id, roleKey) {
    const user = await this.get(id)
    const newRoles = user.roles.filter((role) => role.key !== roleKey)
    return this.updateRoles(id, newRoles)
  }

  // ============================================================
  // Related Resources
  // ============================================================

  /**
   * Fetches a paginated list of events associated with a user.
   *
   * @param {string} id - The UUID of the user.
   * @param {Object} params - Query parameters.
   * @returns {Promise<{ pageDetails: Object, items: Object[] }>}
   */
  async getEvents(id, params = {}) {
    const {
      page = 1,
      limit = 10,
      search_field = '',
      search_value = '',
      sort_by = 'createdAt',
      sort_order = 'desc',
    } = params

    const { data } = await this.http.get(`${this.path}/${id}/events`, {
      params: { page, limit, search_field, search_value, sort_by, sort_order },
    })
    return data
  }

  /**
   * Fetches a paginated list of virtual machines associated with a user.
   *
   * @param {string} id - The UUID of the user.
   * @param {Object} params - Query parameters.
   * @returns {Promise<{ pageDetails: Object, items: Object[] }>}
   */
  async getVMs(id, params = {}) {
    const {
      page = 1,
      limit = 10,
      search_field = '',
      search_value = '',
      sort_by = 'createdAt',
      sort_order = 'desc',
    } = params

    const { data } = await this.http.get(
      `${this.path}/${id}/virtual-machines`,
      {
        params: {
          page,
          limit,
          search_field,
          search_value,
          sort_by,
          sort_order,
        },
      },
    )
    return data
  }

  /**
   * Retrieves a paginated list of Guacamole connections assigned to a user.
   *
   * @param {string} id - The ID of the user.
   * @param {Object} params - Pagination and filtering parameters.
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async getGuacamoles(id, params = {}) {
    const {
      page = 1,
      limit = 10,
      search_field = '',
      search_value = '',
      sort_by = 'createdAt',
      sort_order = 'desc',
    } = params

    const { data } = await this.http.get(`${this.path}/${id}/guacamole`, {
      params: { page, limit, search_field, search_value, sort_by, sort_order },
    })
    return data
  }

  // ============================================================
  // Status Management
  // ============================================================

  /**
   * Retrieves all defined user statuses.
   *
   * @returns {Promise<Array<string>>} A promise resolving to the user status list.
   */
  async getStatuses() {
    const { data } = await this.http.get('/status/user')
    return data
  }

  /**
   * Adds a new custom user status.
   *
   * @param {string} status - Status string to add.
   * @returns {Promise<Object>} A promise resolving to the creation result.
   */
  async addStatus(status) {
    const { data } = await this.http.post('/status/user', { status })
    return data
  }

  /**
   * Deletes a custom user status.
   *
   * @param {string} status - Status string to delete.
   * @returns {Promise<Object>} A promise resolving to the deletion result.
   */
  async deleteStatus(status) {
    const { data } = await this.http.delete(`/status/user/${status}`)
    return data
  }

  // ============================================================
  // Delete Preview
  // ============================================================

  /**
   * Get a delete preview of a user by ID.
   *
   * @param {string} id - The ID of the user.
   * @returns {Promise<Object>} A promise resolving to the delete preview result.
   */
  async getDeletePreview(id) {
    const { data } = await this.http.get(`${this.path}/${id}/delete-preview`)
    return data
  }
}
