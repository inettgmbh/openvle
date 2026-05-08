/**
 * Service for event-related API operations.
 */
export default class EventService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/events'
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Creates a new event.
   *
   * @param {Object} data - Event details.
   * @param {string} data.name - Event name.
   * @param {string} data.description - Event description.
   * @param {string} data.dateStart - ISO start date (YYYY-MM-DD).
   * @param {string} data.dateEnd - ISO end date (YYYY-MM-DD).
   * @param {string} data.course - Associated course ID.
   * @param {string} data.slug - Event slug.
   * @returns {Promise<Object>} Created event object.
   */
  async create(data) {
    const { name, description, dateStart, dateEnd, course, slug } = data
    const { data: result } = await this.http.post(`${this.path}/`, {
      name,
      description,
      dateStart,
      dateEnd,
      guacamole: true,
      status: '53b6993a-57d6-40a6-8d42-e55bf08fac4c',
      course,
      templates: [],
      timeStart: '00:00:00',
      timeEnd: '23:59:59',
      slug,
    })
    return result
  }

  /**
   * Retrieves a single event by ID.
   *
   * @param {string} id - Event ID.
   * @returns {Promise<Object>} Event data.
   */
  async get(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data
  }

  /**
   * Retrieves all events with optional search and sorting parameters.
   *
   * @param {Object} params - Query parameters.
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
   * Updates an existing event.
   *
   * @param {string} id - Event ID.
   * @param {Object} data - Fields to update.
   * @returns {Promise<Object>} Updated event.
   */
  async update(id, data) {
    const { data: result } = await this.http.put(`${this.path}/${id}`, data)
    return result
  }

  /**
   * Deletes an event by ID.
   *
   * @param {string} id - Event ID.
   * @returns {Promise<Object>} Deletion result.
   */
  async delete(id) {
    const { data } = await this.http.delete(`${this.path}/${id}`)
    return data
  }

  // ============================================================
  // Helper Methods for Lookup/Dropdown
  // ============================================================

  /**
   * Retrieves the name of a specific event.
   *
   * @param {string} id - Event ID.
   * @returns {Promise<string>} Event name.
   */
  async getName(id) {
    const event = await this.get(id)
    return event.name
  }

  /**
   * Fetches all events formatted for dropdowns.
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
    return items.map(({ name, id, ...rest }) => ({
      ...rest,
      label: name,
      value: id,
    }))
  }

  /**
   * Searches events by name.
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
  // Related Resources
  // ============================================================

  /**
   * Retrieves Guacamole connections for an event.
   *
   * @param {string} id - Event ID.
   * @param {Object} params - Query parameters.
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async getGuacamoles(id, params = {}) {
    const {
      page = 1,
      limit = 10,
      search_field = '',
      search_value = '',
      sort_by = 'name',
      sort_order = 'asc',
    } = params

    const { data } = await this.http.get(`${this.path}/${id}/guacamole`, {
      params: { page, limit, search_field, search_value, sort_by, sort_order },
    })
    return data
  }

  /**
   * Retrieves templates assigned to an event.
   *
   * @param {string} id - Event ID.
   * @param {Object} params - Query parameters.
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async getTemplates(id, params = {}) {
    const {
      page = 1,
      limit = 10,
      search_field = '',
      search_value = '',
      sort_by = 'name',
      sort_order = 'asc',
    } = params

    const { data } = await this.http.get(`${this.path}/${id}/templates`, {
      params: { page, limit, search_field, search_value, sort_by, sort_order },
    })
    return data
  }

  /**
   * Retrieves users assigned to an event.
   *
   * @param {string} id - Event ID.
   * @param {Object} params - Query parameters.
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async getUsers(id, params = {}) {
    const {
      page = 1,
      limit = 10,
      search_field = '',
      search_value = '',
      sort_by = 'createdAt',
      sort_order = 'desc',
    } = params

    const { data } = await this.http.get(`${this.path}/${id}/users`, {
      params: { page, limit, search_field, search_value, sort_by, sort_order },
    })
    return data
  }

  /**
   * Retrieves virtual machines linked to an event.
   *
   * @param {string} id - Event ID.
   * @param {Object} params - Query parameters.
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async getVMs(id, params = {}) {
    const {
      page = 1,
      limit = 10,
      search_field = '',
      search_value = '',
      sort_by = 'name',
      sort_order = 'asc',
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
   * Retrieves applications linked to an event.
   *
   * @param {string} id - Event ID.
   * @param {Object} params - Query parameters.
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async getApplications(id, params = {}) {
    const {
      page = 1,
      limit = 10,
      search_field = '',
      search_value = '',
      sort_by = 'name',
      sort_order = 'asc',
    } = params

    const { data } = await this.http.get(`${this.path}/${id}/applications`, {
      params: { page, limit, search_field, search_value, sort_by, sort_order },
    })
    return data
  }

  // ============================================================
  // User Management
  // ============================================================

  /**
   * Assigns a user with a role to an event.
   *
   * @param {string} id - Event ID.
   * @param {string} userId - User ID.
   * @param {string} roleId - Role ID.
   * @returns {Promise<Object>} Result of assignment.
   */
  async addUser(id, userId, roleId) {
    const { data } = await this.http.post(`${this.path}/${id}/users`, {
      user_id: userId,
      role_id: roleId,
    })
    return data
  }

  /**
   * Removes a user-role assignment from an event.
   *
   * @param {string} id - Event ID.
   * @param {string} userId - User ID.
   * @param {string} roleId - Role ID.
   * @returns {Promise<Object>} Result of deletion.
   */
  async deleteUser(id, userId, roleId) {
    const { data } = await this.http.delete(
      `${this.path}/${id}/users/${userId}/roles/${roleId}`,
    )
    return data
  }

  // ============================================================
  // Template Management
  // ============================================================

  /**
   * Assigns a template to an event.
   *
   * @param {string} id - Event ID.
   * @param {string} templateId - Template ID.
   * @returns {Promise<Object>} Result of assignment.
   */
  async addTemplate(id, templateId) {
    const { data } = await this.http.post(`${this.path}/${id}/templates`, {
      templates: [{ id: templateId }],
    })
    return data
  }

  // ============================================================
  // Event Actions
  // ============================================================

  /**
   * Triggers the "start" action for an event.
   *
   * @param {string} id - Event ID.
   * @returns {Promise<Object>} Result of the start action.
   */
  async start(id) {
    const { data } = await this.http.post(
      `${this.path}/${id}/actions/start`,
      {},
      { timeout: 30000 },
    )
    return data
  }

  /**
   * Triggers the "stop" action for an event.
   *
   * @param {string} id - Event ID.
   * @returns {Promise<Object>} Result of the stop action.
   */
  async stop(id) {
    const { data } = await this.http.post(
      `${this.path}/${id}/actions/stop`,
      {},
      { timeout: 30000 },
    )
    return data
  }

  /**
   * Extend an event with a new end date.
   *
   * @param {string} id - Event ID.
   * @param {string} newEndDate - New end date.
   * @returns {Promise<Object>} Result of update.
   */
  async extend(id, newEndDate) {
    const { data } = await this.http.post(`${this.path}/${id}/end-date`, {
      dateEnd: newEndDate,
      timeEnd: '23:59:59',
    })
    return data
  }

  /**
   * Resets and restarts the event rollout process.
   *
   * @param {string} id - Event ID.
   * @returns {Promise<Object>} Result of the restart.
   */
  async rerollout(id) {
    await this.http.put(`${this.path}/${id}`, {})
    const { data } = await this.http.post(
      `${this.path}/${id}/actions/start`,
      {},
      { timeout: 30000 },
    )
    return data
  }

  /**
   * Executes a bulk action on a specific event resource.
   *
   * @param {string} id - The UUID of the event.
   * @param {string} type - The resource type (e.g. 'virtual-machines', 'guacamole').
   * @param {string} action - The action to perform (e.g. 'start', 'delete').
   * @returns {Promise<Object>} Result of the bulk action.
   */
  async bulkAction(id, type, action) {
    const { data } = await this.http.post(
      `${this.path}/${id}/${type}/bulk-actions/${action}`,
      {},
      { timeout: 30000 },
    )
    return data
  }

  // ============================================================
  // Status Management
  // ============================================================

  /**
   * Retrieves status entries for all events.
   *
   * @param {Object} params - Query parameters.
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async getStatuses(params = {}) {
    const {
      page = 1,
      limit = 10,
      search_field = '',
      search_value = '',
      sort_by = 'name',
      sort_order = 'asc',
    } = params

    const { data } = await this.http.get('/status/events/', {
      params: { page, limit, search_field, search_value, sort_by, sort_order },
    })
    return data
  }

  /**
   * Gets the status object for a specific event status.
   *
   * @param {string} statusId - Event Status ID.
   * @returns {Promise<Object>} Event Status data.
   */
  async getStatus(statusId) {
    const { data } = await this.http.get(`/status/events/${statusId}`)
    return data
  }

  /**
   * Gets the event status name of a specific event status.
   *
   * @param {string} statusId - Event Status ID.
   * @returns {Promise<string>} Event Status name.
   */
  async getStatusName(statusId) {
    const { data } = await this.http.get(`/status/events/${statusId}`)
    return data.name
  }

  /**
   * Fetches all event status options formatted for dropdowns.
   *
   * @returns {Promise<Array<{ label: string, value: string }>>}
   */
  async statusDropdown() {
    const { items } = await this.getStatuses({
      page: 1,
      limit: 200,
      sort_by: 'name',
      sort_order: 'asc',
    })
    return items.map(({ name, id, ...rest }) => ({
      ...rest,
      label: name,
      value: id,
    }))
  }
}
