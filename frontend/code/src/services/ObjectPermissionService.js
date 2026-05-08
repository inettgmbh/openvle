/**
 * Service for object permission-related API operations.
 */
export default class ObjectPermissionService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/object-permissions'
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Creates a new object permission for a user or role on a specific object.
   *
   * @param {Object} data - Permission data.
   * @param {string} data.objectType - The type of the object (e.g. `template`, `event`).
   * @param {string} data.objectId - The ID of the object.
   * @param {string} data.entityId - The ID of the entity (user or role).
   * @param {string} data.entityType - The type of the entity (user or role).
   * @param {string} data.permissionKey - The key identifying the permission.
   * @returns {Promise<Object>} A promise resolving to the created permission object.
   */
  async create(data) {
    const { objectType, objectId, entityId, entityType, permissionKey } = data

    if (permissionKey === 'object_reset' && objectType !== 'VirtualMachine') {
      console.error(
        `The "${permissionKey}" permission cannot be assigned to a ${objectType} object.`,
      )
      throw new Error()
    }

    const { data: result } = await this.http.post(`${this.path}/`, {
      object_type: objectType,
      object_id: objectId,
      entity_id: entityId,
      entity_type: entityType,
      permission_key: permissionKey,
    })
    return result
  }

  /**
   * Retrieves a single object permission by ID.
   *
   * @param {string} id - The ID of the object permission.
   * @returns {Promise<Object>} A promise resolving to the permission data.
   */
  async get(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data
  }

  /**
   * Retrieves a paginated list of all object permissions with optional search and sorting parameters.
   *
   * @param {Object} params - Query parameters for pagination, filtering, and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.search_field=""] - Field to search by.
   * @param {string} [params.search_value=""] - Search term.
   * @param {string} [params.sort_by="createdAt"] - Field to sort by.
   * @param {string} [params.sort_order="asc"] - Sort order (`asc` or `desc`).
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async list(params = {}) {
    const {
      page = 1,
      limit = 10,
      search_field = '',
      search_value = '',
      sort_by = 'createdAt',
      sort_order = 'asc',
    } = params

    const { data } = await this.http.get(`${this.path}/`, {
      params: { page, limit, search_field, search_value, sort_by, sort_order },
    })
    return data
  }

  /**
   * Retrieves a paginated list of all object permissions with optional search and sorting parameters.
   *
   * @param {Object} params - Query parameters for pagination, filtering, and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.search_field=""] - Field to search by.
   * @param {string} [params.search_value=""] - Search term.
   * @param {string} [params.sort_by="createdAt"] - Field to sort by.
   * @param {string} [params.sort_order="asc"] - Sort order (`asc` or `desc`).
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async listByObject(objectType, objectId, params = {}) {
    const {
      page = 1,
      limit = 10,
      search_field = '',
      search_value = '',
      sort_by = 'createdAt',
      sort_order = 'asc',
    } = params

    const { data } = await this.http.get(
      `${this.path}/${objectType}/${objectId}`,
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
   * Deletes an object permission by ID.
   *
   * @param {string} id - The ID of the object permission.
   * @returns {Promise<Object>} A promise resolving to the deletion result.
   */
  async delete(id) {
    const { data } = await this.http.delete(`${this.path}/${id}`)
    return data
  }
}
