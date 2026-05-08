/**
 * Service for operating system-related API operations.
 */
export default class OSService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/os'
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Creates a new operating system entry.
   *
   * @param {Object} data - OS data.
   * @param {string} data.name - The name of the OS.
   * @param {string} data.key - A unique key for the OS.
   * @param {string} data.description - A description of the OS.
   * @param {string} data.vendor - The vendor ID associated with the OS.
   * @returns {Promise<Object>} A promise resolving to the created OS object.
   */
  async create(data) {
    const { name, key, description, vendor } = data
    const { data: result } = await this.http.post(`${this.path}/`, {
      name,
      key,
      description,
      version: '',
      vendor,
    })
    return result
  }

  /**
   * Retrieves a single OS entry by ID.
   *
   * @param {string} id - The ID of the operating system.
   * @returns {Promise<Object>} A promise resolving to the OS data.
   */
  async get(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data
  }

  /**
   * Retrieves a paginated list of all operating systems with optional search and sorting parameters.
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
   * Updates an existing operating system entry.
   *
   * @param {string} id - The ID of the operating system.
   * @param {Object} data - Fields to update.
   * @param {string} [data.name] - The new name of the OS.
   * @param {string} [data.description] - The updated description.
   * @param {string} [data.vendor] - The updated vendor ID.
   * @returns {Promise<Object>} A promise resolving to the updated OS.
   */
  async update(id, data) {
    const { data: result } = await this.http.put(`${this.path}/${id}`, data)
    return result
  }

  /**
   * Deletes an operating system entry by ID.
   *
   * @param {string} id - The ID of the OS to delete.
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
   * Retrieves the name of a specific operating system by ID.
   *
   * @param {string} id - The ID of the operating system.
   * @returns {Promise<string>} A promise resolving to the name of the OS.
   */
  async getName(id) {
    const os = await this.get(id)
    return os.name
  }

  /**
   * Searches operating systems by name.
   *
   * @param {string} query - The value to search by.
   * @returns {Promise<{ items: Array<Object>, pageDetails: Object }>}
   */
  async search(query) {
    return this.list({
      page: 1,
      limit: 25,
      sort_by: 'name',
      sort_order: 'asc',
      search_field: 'name',
      search_value: query,
    })
  }

  // ============================================================
  // Related Resources
  // ============================================================

  /**
   * Retrieves a paginated list of templates assigned to the specified OS.
   *
   * @param {string} id - The ID of the operating system.
   * @param {Object} params - Query parameters for pagination, filtering, and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.search_field=""] - Field to search by.
   * @param {string} [params.search_value=""] - Search term.
   * @param {string} [params.sort_by="name"] - Field to sort by.
   * @param {string} [params.sort_order="asc"] - Sort order (`asc` or `desc`).
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
   * Retrieves a paginated list of virtual machines assigned to the specified OS.
   *
   * @param {string} id - The ID of the operating system.
   * @param {Object} params - Query parameters for pagination, filtering, and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.search_field=""] - Field to search by.
   * @param {string} [params.search_value=""] - Search term.
   * @param {string} [params.sort_by="name"] - Field to sort by.
   * @param {string} [params.sort_order="asc"] - Sort order (`asc` or `desc`).
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
}
