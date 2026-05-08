/**
 * Service for mail-related API operations.
 */
export default class MailService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/mails'
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Creates a new mail entry.
   *
   * @param {Object} data - Mail data.
   * @param {string} data.subject - The subject of the mail.
   * @param {string} data.fromName - The sender display name.
   * @param {string} data.fromMail - The sender email address.
   * @param {string} data.toMail - The recipient email address.
   * @param {string} data.templateId - The ID of the mail template to use.
   * @param {string} [data.replyTo] - Optional reply-to address.
   * @returns {Promise<Object>} A promise resolving to the created mail object.
   */
  async create(data) {
    const { subject, fromName, fromMail, toMail, templateId, replyTo } = data
    const { data: result } = await this.http.post(`${this.path}/`, {
      subject,
      fromName,
      fromMail,
      toMail,
      templateId,
      ...(replyTo && { replyTo }),
    })
    return result
  }

  /**
   * Retrieves a single mail entry by ID.
   *
   * @param {string} id - The ID of the mail entry.
   * @returns {Promise<Object>} A promise resolving to the mail data.
   */
  async get(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data
  }

  /**
   * Retrieves a paginated list of all mails with optional search and sorting parameters.
   *
   * @param {Object} params - Query parameters for pagination, filtering, and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.search_field=""] - Field to search by.
   * @param {string} [params.search_value=""] - Search term.
   * @param {string} [params.sort_by="createdAt"] - Field to sort by.
   * @param {string} [params.sort_order="desc"] - Sort order (`asc` or `desc`).
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
  // Related Resources
  // ============================================================

  /**
   * Retrieves a paginated list of mails for a specific user.
   *
   * @param {string} user - The user email to filter by.
   * @param {Object} params - Query parameters for pagination and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.sort_by="createdAt"] - Field to sort by.
   * @param {string} [params.sort_order="desc"] - Sort order (`asc` or `desc`).
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async listByUser(user, params = {}) {
    const {
      page = 1,
      limit = 10,
      sort_by = 'createdAt',
      sort_order = 'desc',
    } = params

    const { data } = await this.http.get(`${this.path}/`, {
      params: {
        page,
        limit,
        search_field: 'toMail',
        search_value: user,
        sort_by,
        sort_order,
      },
    })
    return data
  }

  /**
   * Retrieves a paginated list of mails for a specific event.
   *
   * @param {string} eventId - The ID of the event.
   * @param {Object} params - Query parameters for pagination and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.search_field=""] - Field to search by.
   * @param {string} [params.search_value=""] - Search term.
   * @param {string} [params.sort_by="createdAt"] - Field to sort by.
   * @param {string} [params.sort_order="desc"] - Sort order (`asc` or `desc`).
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async listByEvent(eventId, params = {}) {
    const {
      page = 1,
      limit = 10,
      search_field = '',
      search_value = '',
      sort_by = 'createdAt',
      sort_order = 'desc',
    } = params

    const { data } = await this.http.get(`events/${eventId}${this.path}`, {
      params: { page, limit, search_field, search_value, sort_by, sort_order },
    })
    return data
  }
}
