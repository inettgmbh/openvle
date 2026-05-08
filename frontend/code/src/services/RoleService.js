import { useMainStore } from '@/stores/main.js'

/**
 * Service for role-related API operations.
 */
export default class RoleService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/roles'
    this._mainStore = null
  }

  /**
   * Lazy-load mainStore - only call useMainStore() at runtime when Pinia is initialized.
   */
  get mainStore() {
    if (!this._mainStore) {
      this._mainStore = useMainStore()
    }
    return this._mainStore
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Creates a new role.
   *
   * @param {Object} data - Role details.
   * @param {string} data.name - The name of the role.
   * @param {string} data.key - The key identifier for the role.
   * @param {string} data.description - A description of the role.
   * @param {boolean} data.protected - Whether the role is protected.
   * @returns {Promise<Object>} A promise resolving to the created role.
   */
  async create(data) {
    const { name, key, description, protected: isProtected } = data
    const { data: result } = await this.http.post(`${this.path}/`, {
      name,
      key,
      description,
      protected: isProtected,
    })
    return result
  }

  /**
   * Retrieves a single role by ID.
   *
   * @param {string} id - The ID of the role.
   * @returns {Promise<Object|false>} A promise resolving to the role data, or false if excluded.
   */
  async get(id) {
    try {
      const mainStore = this.mainStore
      if (
        id === mainStore?.settings?.roles?.teachers ||
        id === mainStore?.settings?.roles?.students
      ) {
        return false
      }
      const { data } = await this.http.get(`${this.path}/${id}`)
      return data
    } catch {
      return false
    }
  }

  /**
   * Retrieves a paginated list of all roles with optional search and sorting.
   *
   * @param {Object} params - Query parameters.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.search_field=""] - Field to search by.
   * @param {string} [params.search_value=""] - Search term.
   * @param {string} [params.sort_by="name"] - Field to sort by.
   * @param {string} [params.sort_order="asc"] - Sort order.
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

    // Filter out special roles (teachers/students)
    const mainStore = this.mainStore
    const excludeIds = [
      mainStore?.settings?.roles?.teachers,
      mainStore?.settings?.roles?.students,
    ]
    const filteredItems = data.items.filter(
      (role) => !excludeIds.includes(role.id),
    )

    return {
      ...data,
      items: filteredItems,
    }
  }

  /**
   * Updates an existing role.
   *
   * @param {string} id - The ID of the role.
   * @param {Object} data - The fields to update.
   * @param {string} [data.name] - Updated name.
   * @param {string} [data.description] - Updated description.
   * @returns {Promise<Object>} A promise resolving to the updated role.
   */
  async update(id, data) {
    const { data: result } = await this.http.put(`${this.path}/${id}`, data)
    return result
  }

  /**
   * Deletes a role by ID.
   *
   * @param {string} id - The ID of the role to delete.
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
   * Retrieves the name of a role by ID.
   *
   * @param {string} id - The ID of the role.
   * @returns {Promise<string>} A promise resolving to the role name.
   */
  async getName(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data.name
  }

  /**
   * Fetches all roles and formats them for dropdown usage.
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
   * Fetches static event role options.
   *
   * @returns {Promise<Array<{ label: string, value: string }>>}
   */
  async eventRolesDropdown() {
    const mainStore = this.mainStore
    return [
      {
        label: 'Studierende',
        value: mainStore.settings.roles.students,
      },
      {
        label: 'Lehrende',
        value: mainStore.settings.roles.teachers,
      },
    ]
  }

  /**
   * Searches roles by name.
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
  // Members Management
  // ============================================================

  /**
   * Retrieves a paginated list of users assigned to a role.
   *
   * @param {string} id - The ID of the role.
   * @param {Object} params - Query parameters.
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async getMembers(id, params = {}) {
    const {
      page = 1,
      limit = 10,
      search_field = '',
      search_value = '',
      sort_by = 'name',
      sort_order = 'asc',
    } = params

    const { data } = await this.http.get(`${this.path}/${id}/members`, {
      params: { page, limit, search_field, search_value, sort_by, sort_order },
    })
    return data
  }
}
