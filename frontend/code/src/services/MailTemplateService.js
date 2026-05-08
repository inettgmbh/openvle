/**
 * Service for mail template-related API operations.
 */
export default class MailTemplateService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/mailtemplates'
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Creates a new mail template.
   *
   * @param {Object} data - Mail template data.
   * @param {string} data.name - Name of the mail template.
   * @param {string} data.subject - Subject line of the mail template.
   * @param {string} data.description - Description for internal reference.
   * @param {string} data.contentHTML - HTML content of the mail template.
   * @param {string} data.contentPlain - Plain text fallback content.
   * @param {string} data.replyTo - Reply-to address.
   * @param {string} [data.language='08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0'] - Language ID.
   * @returns {Promise<Object>} A promise resolving to the created mail template.
   */
  async create(data) {
    const {
      name,
      subject,
      description,
      contentHTML,
      contentPlain,
      replyTo,
      language = '08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0',
    } = data
    const { data: result } = await this.http.post(`${this.path}/`, {
      name,
      subject,
      description,
      contentHTML,
      contentPlain,
      language,
      replyTo,
      protected: false,
    })
    return result
  }

  /**
   * Retrieves a single mail template by ID.
   *
   * @param {string} id - The ID of the mail template.
   * @returns {Promise<Object>} A promise resolving to the mail template data.
   */
  async get(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data
  }

  /**
   * Retrieves a paginated list of all mail templates with optional search and sorting parameters.
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
   * Updates a mail template.
   *
   * @param {string} id - The ID of the mail template.
   * @param {Object} data - Fields to update.
   * @param {string} [data.name] - New mail template name.
   * @param {string} [data.subject] - Updated subject line.
   * @param {string} [data.description] - Updated description.
   * @param {string} [data.contentHTML] - Updated HTML content.
   * @param {string} [data.replyTo] - Updated reply-to address.
   * @param {string} [data.language] - Language ID.
   * @param {string} [data.mail_action] - The associated mail action ID.
   * @returns {Promise<Object>} A promise resolving to the updated mail template.
   */
  async update(id, data) {
    const { data: result } = await this.http.put(`${this.path}/${id}`, data)
    return result
  }

  /**
   * Deletes a mail template by ID.
   *
   * @param {string} id - The ID of the mail template.
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
   * Retrieves the name of a mail template.
   *
   * @param {string} id - The ID of the mail template.
   * @returns {Promise<string>} A promise resolving to the template name.
   */
  async getName(id) {
    const template = await this.get(id)
    return template.name
  }

  /**
   * Fetches all mail templates and formats them for use in dropdown components.
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
   * Searches mail templates by name.
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
   * Retrieves a paginated list of mails using a specific mail template.
   *
   * @param {string} id - The ID of the mail template.
   * @param {Object} params - Query parameters for pagination, filtering, and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.sort_by="name"] - Field to sort by.
   * @param {string} [params.sort_order="asc"] - Sort order (`asc` or `desc`).
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async getMails(id, params = {}) {
    const {
      page = 1,
      limit = 10,
      sort_by = 'name',
      sort_order = 'asc',
    } = params

    const { data } = await this.http.get(`mails`, {
      params: {
        page,
        limit,
        search_field: 'templateId',
        search_value: id,
        sort_by,
        sort_order,
      },
    })
    return data
  }

  // ============================================================
  // Protection Management
  // ============================================================

  /**
   * Changes the protection flag of a mail template.
   *
   * @param {string} id - The ID of the mail template.
   * @param {boolean} isProtected - True to protect, false to unprotect.
   * @returns {Promise<Object>} A promise resolving to the updated mail template.
   */
  async setProtection(id, isProtected) {
    const { data } = await this.http.put(`${this.path}/${id}`, {
      protected: isProtected,
    })
    return data
  }

  // ============================================================
  // Mail Action Assignment
  // ============================================================

  /**
   * Assigns a mail_action to a specific mail template.
   *
   * @param {string} id - The UUID of the mail template to update.
   * @param {string} mail_action - The mail action to assign.
   * @returns {Promise<Object>} A promise resolving with the response data.
   */
  async assignMailAction(id, mail_action) {
    const { data } = await this.http.put(`${this.path}/${id}`, { mail_action })
    return data
  }

  /**
   * Unassigns the mail_action from a specific mail template.
   *
   * @param {string} id - The UUID of the mail template to update.
   * @returns {Promise<Object>} A promise resolving with the response data.
   */
  async unassignMailAction(id) {
    const { data } = await this.http.put(`${this.path}/${id}`, {
      mail_action: null,
    })
    return data
  }
}
