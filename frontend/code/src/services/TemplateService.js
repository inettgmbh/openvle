/**
 * Service for VM template related API operations.
 */
export default class TemplateService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/templates'
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Creates a new VM template.
   *
   * @param {Object} data - Template details.
   * @param {string} data.name - The name of the template.
   * @param {string} data.description - A description of the template.
   * @param {number} data.cpu - The number of CPUs assigned.
   * @param {number} data.ram - The amount of RAM in MB.
   * @param {string} data.source_vm - The source VM ID to clone from.
   * @returns {Promise<Object>} A promise resolving to the created template.
   */
  async create(data) {
    const { name, description, cpu, ram, source_vm } = data
    const { data: result } = await this.http.post(`${this.path}/`, {
      name,
      description,
      cpu,
      ram,
      source_vm,
      disk: '20', // TODO: Remove when fixed in backend
    })
    return result
  }

  /**
   * Retrieves a single template by ID.
   *
   * @param {string} id - The ID of the template.
   * @returns {Promise<Object>} A promise resolving to the template data.
   */
  async get(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data
  }

  /**
   * Retrieves a paginated list of all templates.
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
   * Updates an existing template.
   *
   * @param {string} id - The ID of the template.
   * @param {Object} data - Fields to update.
   * @returns {Promise<Object>} A promise resolving to the updated template.
   */
  async update(id, data) {
    const { data: result } = await this.http.put(`${this.path}/${id}`, data)
    return result
  }

  /**
   * Deletes a template by ID.
   *
   * @param {string} id - The ID of the template to delete.
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
   * Retrieves the name of a template by ID.
   *
   * @param {string} id - The ID of the template.
   * @returns {Promise<string>} A promise resolving to the template name.
   */
  async getName(id) {
    const template = await this.get(id)
    return template.name
  }

  /**
   * Fetches all templates and formats them for dropdown components.
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
   * Searches templates by name.
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
   * Retrieves a paginated list of applications assigned to a template.
   *
   * @param {string} id - The ID of the template.
   * @param {Object} params - Query parameters.
   * @returns {Promise<Object>}
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

  /**
   * Retrieves a paginated list of courses assigned to a template.
   *
   * @param {string} id - The ID of the template.
   * @param {Object} params - Query parameters.
   * @returns {Promise<Object>}
   */
  async getCourses(id, params = {}) {
    const {
      page = 1,
      limit = 10,
      search_field = '',
      search_value = '',
      sort_by = 'name',
      sort_order = 'asc',
    } = params

    const { data } = await this.http.get(`${this.path}/${id}/courses`, {
      params: { page, limit, search_field, search_value, sort_by, sort_order },
    })
    return data
  }

  /**
   * Retrieves a paginated list of VMs created from a template.
   *
   * @param {string} id - The ID of the template.
   * @param {Object} params - Query parameters.
   * @returns {Promise<Object>}
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

  // ============================================================
  // Application Management
  // ============================================================

  /**
   * Updates the applications assigned to a template.
   *
   * @param {string} id - The ID of the template.
   * @param {Array<string>} apps - List of application IDs.
   * @returns {Promise<Object>}
   */
  async updateApps(id, apps) {
    const { data } = await this.http.put(`${this.path}/${id}/applications`, {
      apps,
    })
    return data
  }

  // ============================================================
  // Protection Management
  // ============================================================

  /**
   * Toggles deletion protection on a template.
   *
   * @param {string} id - The ID of the template.
   * @param {boolean} preventDelete - Whether deletion should be prevented.
   * @returns {Promise<Object>}
   */
  async setProtection(id, preventDelete) {
    return this.update(id, { prevent_delete: preventDelete })
  }

  // ============================================================
  // Proxmox Integration
  // ============================================================

  /**
   * Loads additional details from Proxmox for the given template.
   *
   * @param {string} pveID - The Proxmox ID of the template.
   * @returns {Promise<Object>}
   */
  async loadPVEDetails(pveID) {
    const { data } = await this.http.get('/proxmox/templates/load', {
      params: { proxmox_id: pveID },
    })
    return data
  }

  /**
   * Imports a template from Proxmox into the system.
   *
   * @param {string} pveID - The Proxmox template ID.
   * @returns {Promise<Object>}
   */
  async importFromPVE(pveID) {
    const { data } = await this.http.post(
      '/proxmox/templates/load',
      null, // TODO: fix to body parameter when fixed in backend
      { params: { proxmox_id: pveID } },
    )
    return data
  }
}
