import { ref } from 'vue'

/**
 * Service for Guacamole instance-related API operations.
 */
export default class GuacamoleService {
  /**
   * @param {import('axios').AxiosInstance} http
   * @param {Object} connectionService - ConnectionService instance for VM lookups.
   */
  constructor(http, connectionService = null) {
    this.http = http
    this.path = '/guacamole'
    this.connectionService = connectionService
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Creates a new Guacamole instance for a user with a specific connection profile.
   *
   * @param {Object} data - Guacamole instance data.
   * @param {string} data.name - The name of the Guacamole instance.
   * @param {string} data.userId - The ID of the assigned user.
   * @param {string} data.connection_profile - The ID of the connection profile.
   * @returns {Promise<Object>} The created Guacamole instance.
   */
  async create(data) {
    const { name, userId, connection_profile } = data
    const { data: result } = await this.http.post(`${this.path}/`, {
      name,
      userId,
      connection_profile,
    })
    return result
  }

  /**
   * Retrieves a single Guacamole instance by ID.
   *
   * @param {string} id - The ID of the Guacamole instance.
   * @returns {Promise<Object>} The Guacamole instance data.
   */
  async get(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data
  }

  /**
   * Retrieves a paginated list of all Guacamole instances with optional search and sorting parameters.
   *
   * @param {Object} params - Query parameters for pagination, filtering, and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.search_field=""] - Field to search by.
   * @param {string} [params.search_value=""] - Search term.
   * @param {string} [params.sort_by="createdAt"] - Field to sort by.
   * @param {string} [params.sort_order="desc"] - Sort order (`asc` or `desc`).
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async list(params = {}) {
    const {
      page = 1,
      limit = 10,
      search_field = '',
      search_value = '',
      sort_by = 'createdAt',
      sort_order = 'desc',
    } = params

    const { data } = await this.http.get(`${this.path}/`, {
      params: { page, limit, search_field, search_value, sort_by, sort_order },
    })
    return data
  }

  /**
   * Deletes a Guacamole instance by ID.
   *
   * @param {string} id - The ID of the Guacamole instance.
   * @returns {Promise<Object>} Result of the deletion.
   */
  async delete(id) {
    const { data } = await this.http.delete(`${this.path}/${id}`)
    return data
  }

  // ============================================================
  // Helper Methods for Lookup/Dropdown
  // ============================================================

  /**
   * Retrieves a single Guacamole instance name by ID.
   *
   * @param {string} id - The ID of the Guacamole instance.
   * @returns {Promise<string>} The Guacamole instance name.
   */
  async getName(id) {
    const instance = await this.get(id)
    return instance.name
  }

  /**
   * Searches Guacamole instances by name.
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
   * Retrieves all Guacamole instances associated with a specific event.
   *
   * @param {string} eventId - The ID of the event.
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async listByEvent(eventId) {
    const { data } = await this.http.get(`${this.path}/`, {
      params: {
        page: 1,
        limit: 200,
        search_field: 'eventId',
        search_value: eventId,
        sort_by: 'createdAt',
        sort_order: 'desc',
      },
    })
    return data
  }

  /**
   * Retrieves all Guacamole instances assigned to a specific user.
   *
   * @param {string} userId - The ID of the user.
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async listByUser(userId) {
    const { data } = await this.http.get(`${this.path}/`, {
      params: {
        page: 1,
        limit: 200,
        search_field: 'userId',
        search_value: userId,
        sort_by: 'createdAt',
        sort_order: 'desc',
      },
    })
    return data
  }

  /**
   * Retrieves all Guacamole instances that use a specific connection profile.
   *
   * @param {string} connectionProfileId - The ID of the connection profile.
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async listByConnectionProfile(connectionProfileId) {
    const { data } = await this.http.get(`${this.path}/`, {
      params: {
        page: 1,
        limit: 200,
        search_field: 'connection_profile',
        search_value: connectionProfileId,
        sort_by: 'createdAt',
        sort_order: 'desc',
      },
    })
    return data
  }

  /**
   * Retrieves all Guacamole instances that use a specific VM.
   *
   * @param {string} vmId - The ID of the VM.
   * @param {Object} params - Query parameters (unused, for compatibility).
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async listByVM(vmId, params = {}) {
    // This is a workaround as long as we do not have a separate backend API for this
    if (!this.connectionService) {
      console.warn(
        'ConnectionService not provided to GuacamoleService. Cannot fetch by VM.',
      )
      return { items: [], pageDetails: { totalCount: 0 } }
    }

    const vmConnectionProfiles = ref([])

    const response = await this.connectionService.listByObject(
      'VirtualMachine',
      vmId,
      { page: 1, limit: 200 },
    )
    vmConnectionProfiles.value = response.items
    vmConnectionProfiles.value.count = response.pageDetails.totalCount

    const tempArray = []

    for (const connectionProfile of vmConnectionProfiles.value) {
      const result = await this.listByConnectionProfile(connectionProfile.id)

      if (Array.isArray(result)) {
        tempArray.push(...result)
      } else if (result?.items && Array.isArray(result.items)) {
        tempArray.push(...result.items)
      } else {
        console.warn('Unexpected result format:', result)
      }
    }

    return {
      items: tempArray,
      pageDetails: {
        page: 1,
        perPage: 200,
        pageCount: 1,
        totalCount: tempArray.length,
      },
    }
  }

  // ============================================================
  // Actions
  // ============================================================

  /**
   * Triggers provisioning of a Guacamole instance.
   *
   * @param {string} id - The ID of the Guacamole instance to provision.
   * @returns {Promise<Object>} Result of the provisioning action.
   */
  async provision(id) {
    const { data } = await this.http.post(
      `${this.path}/${id}/actions/provision`,
    )
    return data
  }
}
