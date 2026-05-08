/**
 * Service for mail action-related API operations.
 */
export default class MailActionService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/mailactions'
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Retrieves a single mail action by ID.
   *
   * @param {string} id - The ID of the mail action.
   * @returns {Promise<Object>} A promise resolving to the mail action data.
   */
  async get(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data
  }

  /**
   * Retrieves a paginated list of all mail actions with optional search and sorting parameters.
   *
   * @param {Object} params - Query parameters for pagination, filtering, and sorting.
   * @param {number} [params.page=1] - Page number.
   * @param {number} [params.limit=10] - Number of results per page.
   * @param {string} [params.search_field=""] - Field to search by.
   * @param {string} [params.search_value=""] - Search value.
   * @param {string} [params.sort_by="createdAt"] - Field to sort by.
   * @param {string} [params.sort_order="desc"] - Sort direction.
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

  // ============================================================
  // Helper Methods for Lookup/Dropdown
  // ============================================================

  /**
   * Searches mail actions by name for use in lookup fields.
   *
   * @param {string} query - The search string.
   * @returns {Promise<Array<Object>>} Matching mail actions.
   */
  async search(query) {
    return await this.list({
      page: 1,
      limit: 25,
      sort_by: 'name',
      sort_order: 'asc',
      search_field: 'name',
      search_value: query,
    })
  }

  /**
   * Returns the formatted name of a mail action by ID.
   *
   * @param {string} id - The ID of the mail action.
   * @returns {Promise<string>} The mail action name.
   */
  async formatById(id) {
    const action = await this.get(id)
    return action.name
  }

  /**
   * Retrieves only the name of a mail action by ID.
   *
   * @param {string} id - The ID of the mail action.
   * @returns {Promise<string>} A promise resolving to the name.
   */
  async getName(id) {
    const action = await this.get(id)
    return action.name
  }

  /**
   * Fetches all mail actions and formats them for use in dropdown components.
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
}
