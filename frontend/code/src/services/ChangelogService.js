/**
 * Service for changelog-related API operations.
 */
export default class ChangelogService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/changelogs'
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Retrieves a single changelog entry by ID.
   *
   * @param {string} id - The ID of the changelog entry.
   * @returns {Promise<Object>} A promise resolving to the changelog data.
   */
  async get(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data
  }

  /**
   * Retrieves all changelogs with optional search and sorting parameters.
   *
   * @param {Object} params - Query parameters for pagination, filtering and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.search_field=""] - Field to search by.
   * @param {string} [params.search_value=""] - Search term.
   * @param {string} [params.sort_by="timestamp"] - Field to sort by.
   * @param {string} [params.sort_order="desc"] - Sort order (`asc` or `desc`).
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async list(params = {}) {
    const {
      page = 1,
      limit = 10,
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

  // ============================================================
  // Related Resources
  // ============================================================

  /**
   * Retrieves paginated changelogs for a specific object type and ID.
   *
   * @param {string} objectType - The type of the object (e.g. `user`, `course`).
   * @param {string} objectId - The ID of the object to fetch changelogs for.
   * @param {Object} params - Query parameters for pagination and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.sort_by="timestamp"] - Field to sort by.
   * @param {string} [params.sort_order="desc"] - Sort order (`asc` or `desc`).
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async listByObject(objectType, objectId, params = {}) {
    const {
      page = 1,
      limit = 10,
      search_field = '',
      search_value = '',
      sort_by = 'timestamp',
      sort_order = 'desc',
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
   * Retrieves paginated changelogs filtered by user ID.
   *
   * @param {string} userId - The user ID to filter changelogs by.
   * @param {Object} params - Query parameters for pagination and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.sort_by="timestamp"] - Field to sort by.
   * @param {string} [params.sort_order="desc"] - Sort order (`asc` or `desc`).
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async listByUser(userId, params = {}) {
    const {
      page = 1,
      limit = 10,
      sort_by = 'timestamp',
      sort_order = 'desc',
    } = params

    const { data } = await this.http.get(`${this.path}/`, {
      params: {
        page,
        limit,
        sort_by,
        sort_order,
        search_field: 'userId',
        search_value: userId,
      },
    })
    return data
  }
}
