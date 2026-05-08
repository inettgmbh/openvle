/**
 * Service for virtual machine (VM) related API operations.
 */
export default class VMService {
  /**
   * @param {import('axios').AxiosInstance} http
   * @param {Object} [backendClient] - Reference to BackendClient for cross-service calls.
   */
  constructor(http, backendClient = null) {
    this.http = http
    this.path = '/virtual_machines'
    this.backendClient = backendClient
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Creates a new virtual machine.
   *
   * @param {Object} data - VM details.
   * @param {string} data.name - The name of the VM.
   * @param {string} data.description - A description of the VM.
   * @param {number} data.cpu - Number of CPU cores.
   * @param {number} data.ram - Amount of RAM in MB.
   * @param {string} data.template - Template ID to base the VM on.
   * @param {boolean} [data.preventDelete=false] - Prevent deletion of VM.
   * @param {boolean} [data.createConnection=false] - Auto-create a connection.
   * @returns {Promise<Object>} A promise resolving to the created VM.
   */
  async create(data) {
    const {
      name,
      description,
      cpu,
      ram,
      template,
      preventDelete = false,
      createConnection = false,
    } = data
    const { data: result } = await this.http.post(`${this.path}/`, {
      name,
      description,
      cpu,
      ram,
      template,
      prevent_delete: preventDelete,
      create_guacamole: createConnection,
    })
    return result
  }

  /**
   * Retrieves a virtual machine by its ID.
   *
   * @param {string} id - The ID of the VM.
   * @returns {Promise<Object>} A promise resolving to the VM data.
   */
  async get(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data
  }

  /**
   * Retrieves a paginated list of all virtual machines.
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
   * Updates an existing virtual machine.
   *
   * @param {string} id - The ID of the VM.
   * @param {Object} data - Fields to update.
   * @returns {Promise<Object>} A promise resolving to the updated VM.
   */
  async update(id, data) {
    const { data: result } = await this.http.put(`${this.path}/${id}`, data)
    return result
  }

  /**
   * Deletes a VM by ID.
   *
   * @param {string} id - The ID of the VM.
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
   * Retrieves the name of a virtual machine by ID.
   *
   * @param {string} id - The ID of the VM.
   * @returns {Promise<string>} A promise resolving to the VM name.
   */
  async getName(id) {
    const vm = await this.get(id)
    return vm.name
  }

  /**
   * Fetches all virtual machines and formats them for dropdown components.
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
   * Searches virtual machines by name.
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
  // Preload Methods
  // ============================================================

  /**
   * Fetches a preloaded list of virtual machines.
   *
   * @returns {Promise<{ pageDetails: Object, items: Object[] }>}
   */
  async preload() {
    const { data } = await this.http.get(`${this.path}/`, {
      params: { page: 1, limit: 200 },
    })
    return data
  }

  // ============================================================
  // Application Management
  // ============================================================

  /**
   * Retrieves a paginated list of applications assigned to a VM.
   *
   * @param {string} id - The ID of the VM.
   * @param {Object} params - Query parameters.
   * @returns {Promise<Object>}
   */
  async getApps(id, params = {}) {
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
   * Updates applications assigned to a virtual machine.
   *
   * @param {string} id - The ID of the virtual machine.
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
  // VM Actions
  // ============================================================

  /**
   * Triggers a lifecycle action on a VM (start, stop, etc.).
   *
   * @param {string} id - The ID of the VM.
   * @param {string} action - The action to perform.
   * @returns {Promise<Object>}
   */
  async action(id, action) {
    const { data } = await this.http.post(
      `${this.path}/${id}/actions/${action}`,
    )
    return data
  }

  /**
   * Enables or disables deletion protection for a VM.
   *
   * @param {string} id - The ID of the VM.
   * @param {boolean} preventDelete - Whether to prevent deletion.
   * @returns {Promise<Object>}
   */
  async setProtection(id, preventDelete) {
    return this.update(id, { prevent_delete: preventDelete })
  }

  /**
   * Migrates a VM to a different Proxmox node.
   *
   * @param {string} id - The ID of the VM.
   * @param {string} targetNode - The name of the target node.
   * @returns {Promise<Object>}
   */
  async migrate(id, targetNode) {
    const { data } = await this.http.put(`${this.path}/${id}/migrate`, {
      targetNode,
    })
    return data
  }

  // ============================================================
  // Network Information
  // ============================================================

  /**
   * Retrieves the IPv4 address of a VM.
   *
   * @param {string} id - The ID of the VM.
   * @returns {Promise<Object>}
   */
  async getIPv4(id) {
    const response = await this.http.get(`${this.path}/${id}/ipv4`)
    return response
  }

  // ============================================================
  // RRD Data
  // ============================================================

  /**
   * Fetches detailed RRD time-series data for a specific virtual machine.
   *
   * @param {string} id - The UUID of the virtual machine.
   * @param {string} [timeframe='hour'] - The timeframe.
   * @param {string} [cf='AVERAGE'] - The consolidation function.
   * @returns {Promise<Object>}
   */
  async getRRDData(id, timeframe = 'hour', cf = 'AVERAGE') {
    const { data } = await this.http.get(`${this.path}/${id}/rrddata`, {
      params: { timeframe, cf },
    })
    return data
  }

  // ============================================================
  // Cross-Resource Queries
  // ============================================================

  /**
   * Retrieves the name of a virtual machine OR a template by ID.
   *
   * @param {Object} object - The vm or template object.
   * @param {string} object.id - The ID.
   * @param {string} object.type - The type ('VirtualMachine' or 'Template').
   * @returns {Promise<string|undefined>}
   */
  async getVMOrTemplateName(object) {
    try {
      if (!object?.id || !object?.type) return undefined

      let response
      let label

      if (object.type === 'Template') {
        response = await this.http.get(`/templates/${object.id}`)
        label = 'VM-Vorlage'
      } else {
        response = await this.http.get(`${this.path}/${object.id}`)
        label = 'VM'
      }
      return `${response.data.name} (${label})`
    } catch {
      return undefined
    }
  }

  /**
   * Searches virtual machines and templates by name.
   *
   * @param {string} query - The value to search by.
   * @returns {Promise<{ items: Array<Object>, pageDetails: Object }>}
   */
  async searchVMsAndTemplates(query) {
    const markItems = (items, type, label) => {
      return items.map((item) => ({
        ...item,
        _type: type,
        name: `${item.name} (${label})`,
        ident: { id: item.id, type },
      }))
    }

    const [vmsResult, templatesResult] = await Promise.all([
      this.search(query),
      this.backendClient?.templates?.search(query) ?? {
        items: [],
        pageDetails: { totalCount: 0 },
      },
    ])

    return {
      items: [
        ...markItems(vmsResult.items, 'VirtualMachine', 'VM'),
        ...markItems(templatesResult.items, 'Template', 'VM-Vorlage'),
      ],
      pageDetails: {
        totalCount:
          vmsResult.pageDetails.totalCount +
          templatesResult.pageDetails.totalCount,
      },
    }
  }
}
