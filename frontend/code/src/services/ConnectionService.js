import {
  connectionProfileLabelFormatter,
  resolveFieldFromLookup,
} from '@/utils/dataUtils'

/**
 * Service for Guacamole connection profile-related API operations.
 */
export default class ConnectionService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/guacamole-connection-profiles'
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Creates a new Guacamole connection profile.
   *
   * @param {Object} data - Connection profile data.
   * @param {number} data.port - The port used by the connection.
   * @param {string} data.protocol - The protocol (e.g. `ssh` or `rdp`).
   * @param {string} data.username - The username for the connection.
   * @param {string} data.password - The password for the connection.
   * @param {string} data.objectId - The ID of the related object.
   * @param {string} data.objectType - The type of the related object.
   * @returns {Promise<Object>} A promise resolving to the created connection profile.
   */
  async create(data) {
    const { port, protocol, username, password, objectId, objectType } = data
    const { data: result } = await this.http.post(`${this.path}/`, {
      port,
      protocol,
      username,
      password,
      objectId,
      objectType,
    })
    return result
  }

  /**
   * Creates a new Guacamole connection profile (V2 with params).
   *
   * @param {Object} data - Connection profile data.
   * @param {Object} data.params - The params used by the connection.
   * @param {string} data.protocol - The protocol (e.g. `ssh` or `rdp`).
   * @param {string} data.objectId - The ID of the related object.
   * @param {string} data.objectType - The type of the related object.
   * @returns {Promise<Object>} A promise resolving to the created connection profile.
   */
  async createV2(data) {
    const { params, protocol, objectId, objectType } = data
    const { data: result } = await this.http.post(`${this.path}/`, {
      params,
      protocol,
      objectId,
      objectType,
    })
    return result
  }

  /**
   * Retrieves a Guacamole connection profile by ID.
   *
   * @param {string} id - The ID of the connection profile.
   * @returns {Promise<Object>} A promise resolving to the connection profile.
   */
  async get(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data
  }

  /**
   * Retrieves a paginated list of all connection profiles with optional search and sorting parameters.
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
   * Deletes a connection profile by ID.
   *
   * @param {string} id - The ID of the connection profile.
   * @returns {Promise<Object>} A promise resolving to the deletion result.
   */
  async delete(id) {
    const { data } = await this.http.delete(`${this.path}/${id}`)
    return data
  }

  // ============================================================
  // Clone Methods
  // ============================================================

  /**
   * Clone an existing Guacamole connection profile.
   *
   * @param {string} id - The ID of the existing Guacamole connection profile.
   * @param {Object} data - Clone data.
   * @param {string} data.objectId - The ID of the related object.
   * @param {string} data.objectType - The type of the related object.
   * @param {number} data.port - The port used by the connection.
   * @param {string} data.protocol - The protocol.
   * @param {string} data.username - The username for the connection.
   * @param {string} data.password - The password for the connection.
   * @returns {Promise<Object>} A promise resolving to the created connection profile.
   */
  async clone(id, data) {
    const { objectId, objectType, port, protocol, username, password } = data
    const { data: result } = await this.http.post(`${this.path}/${id}/clone`, {
      objectId,
      objectType,
      port,
      protocol,
      username,
      password,
    })
    return result
  }

  // ============================================================
  // Helper Methods for Lookup/Dropdown
  // ============================================================

  /**
   * Fetches a preloaded list of connection profiles with a fixed pagination limit.
   *
   * @returns {Promise<{ pageDetails: Object, items: Object[] }>}
   */
  async preload() {
    const { data } = await this.http.get(`${this.path}/`, {
      params: { page: 1, limit: 200 },
    })
    return data
  }

  /**
   * Resolves and returns a human-readable label for a connection profile.
   *
   * @param {string} id - The ID of the connection profile.
   * @returns {Promise<string|undefined>} A promise resolving to the label.
   */
  async getLabel(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)

    await resolveFieldFromLookup(data, [
      {
        from: 'objectId',
        to: 'label',
        keyspace: 'vms',
        formatter: (obj) => ({
          label: connectionProfileLabelFormatter(
            obj,
            obj.protocol,
            obj.username,
            obj.label,
            obj.port,
          ),
        }),
      },
    ])

    return data?.label
  }

  /**
   * Retrieves only the `objectId` of a connection profile by ID.
   *
   * @param {string} id - The ID of the connection profile.
   * @returns {Promise<string>} A promise resolving to the object ID.
   */
  async getObjectId(id) {
    const profile = await this.get(id)
    return profile.objectId
  }

  /**
   * Fetches all connection profiles and formats them for dropdown use.
   *
   * @returns {Promise<Array<{ label: string, value: string }>>}
   */
  async dropdown() {
    const { items } = await this.list({
      page: 1,
      limit: 200,
      sort_by: 'createdAt',
      sort_order: 'desc',
    })
    return items.map(
      ({ protocol, objectId, objectType, username, id, ...rest }) => ({
        ...rest,
        label:
          objectType +
          ': [' +
          protocol +
          '] + ' +
          objectId +
          ' - Benutzer: ' +
          username,
        value: id,
      }),
    )
  }

  /**
   * Fetches all template-type connection profiles and formats them for dropdown use.
   *
   * @returns {Promise<Array<{ label: string, value: string }>>}
   */
  async dropdownTemplates() {
    const { items } = await this.list({
      page: 1,
      limit: 200,
      sort_by: 'createdAt',
      sort_order: 'desc',
      search_field: 'objectType',
      search_value: 'Template',
    })
    return items.map(({ protocol, objectId, username, id, ...rest }) => ({
      ...rest,
      label:
        'Vorlage: [' +
        protocol +
        '] + ' +
        objectId +
        ' - Benutzer: ' +
        username,
      value: id,
    }))
  }

  /**
   * Fetches all VM-type connection profiles and formats them for dropdown use.
   *
   * @returns {Promise<Array<Object>>}
   */
  async dropdownVMs() {
    const { items } = await this.list({
      page: 1,
      limit: 200,
      sort_by: 'createdAt',
      sort_order: 'desc',
      search_field: 'objectType',
      search_value: 'VirtualMachine',
    })
    return items.map(({ protocol, objectId, username, id, port }) => ({
      label: '[' + protocol + '] + ' + objectId + ' - Benutzer: ' + username,
      protocol,
      username,
      objectId,
      value: id,
      port,
    }))
  }

  /**
   * Searches connection profiles by name.
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
   * Retrieves all connection profiles associated with a specific object.
   *
   * @param {string} objectType - The type of the object.
   * @param {string} objectId - The ID of the object.
   * @param {Object} params - Query parameters for pagination and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.sort_by="createdAt"] - Field to sort by.
   * @param {string} [params.sort_order="desc"] - Sort order (`asc` or `desc`).
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async listByObject(objectType, objectId, params = {}) {
    const {
      page = 1,
      limit = 10,
      sort_by = 'createdAt',
      sort_order = 'desc',
    } = params

    const { data } = await this.http.get(
      `${this.path}/${objectType}/${objectId}`,
      {
        params: { page, limit, sort_by, sort_order },
      },
    )
    return data
  }
}
