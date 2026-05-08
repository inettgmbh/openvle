/**
 * Service for application-related API operations.
 */
export default class ApplicationService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/applications'
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Creates a new application.
   *
   * @param {Object} data - Application details.
   * @param {string} data.name - The name of the application.
   * @param {string} data.key - The unique key of the application.
   * @param {string} data.description - A description of the application.
   * @param {string} data.vendor - The vendor associated with the application.
   * @returns {Promise<Object>} A promise resolving to the created application.
   */
  async create(data) {
    const { name, key, description, vendor } = data
    const { data: result } = await this.http.post(`${this.path}/`, {
      name,
      key,
      description,
      vendor,
    })
    return result
  }

  /**
   * Retrieves a single application by its ID.
   *
   * @param {string} id - The ID of the application.
   * @returns {Promise<Object>} A promise resolving to the application data.
   */
  async get(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data
  }

  /**
   * Retrieves a paginated list of all applications.
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
   * Updates an existing application.
   *
   * @param {string} id - The ID of the application to update.
   * @param {Object} data - Fields to update.
   * @returns {Promise<Object>} A promise resolving to the updated application.
   */
  async update(id, data) {
    const { data: result } = await this.http.put(`${this.path}/${id}`, data)
    return result
  }

  /**
   * Deletes an application by its ID.
   *
   * @param {string} id - The ID of the application to delete.
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
   * Retrieves only the name of an application by ID.
   *
   * @param {string} id - The ID of the application.
   * @returns {Promise<string>} A promise resolving to the application name.
   */
  async getName(id) {
    const app = await this.get(id)
    return app.name
  }

  /**
   * Fetches all applications and formats them for dropdown display.
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
    return items.map(({ name, key, ...rest }) => ({
      ...rest,
      label: name,
      value: key,
    }))
  }

  /**
   * Searches applications by name.
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
  // Related Resources
  // ============================================================

  /**
   * Retrieves a paginated list of templates for a specific application.
   *
   * @param {string} id - The ID of the application.
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
   * Retrieves a paginated list of virtual machines for a specific application.
   *
   * @param {string} id - The ID of the application.
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
}
