/**
 * Service for language-related API operations.
 */
export default class LanguageService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/languages'
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Retrieves a single language by ID.
   *
   * @param {string} id - The ID of the language.
   * @returns {Promise<Object>} A promise resolving to the language data.
   */
  async get(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data
  }

  /**
   * Retrieves a list of all available languages (paginated to 100 items).
   *
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async list() {
    const { data } = await this.http.get(`${this.path}/`, {
      params: { page: 1, limit: 100 },
    })
    return data
  }

  // ============================================================
  // Helper Methods for Lookup/Dropdown
  // ============================================================

  /**
   * Searches languages by name (client-side filter on full list).
   *
   * @param {string} query - The search string.
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async search(query) {
    const response = await this.list()
    const lowerQuery = query.toLowerCase()
    return {
      ...response,
      items: response.items.filter(
        (item) =>
          item.nameEnglish?.toLowerCase().includes(lowerQuery) ||
          item.key?.toLowerCase().includes(lowerQuery),
      ),
    }
  }

  /**
   * Returns the name of a language by ID.
   *
   * @param {string} id - The ID of the language.
   * @returns {Promise<string>} The language name.
   */
  async getName(id) {
    const lang = await this.get(id)
    return lang.nameEnglish
  }
}
