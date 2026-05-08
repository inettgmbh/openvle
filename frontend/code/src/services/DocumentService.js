/**
 * Service for document-related API operations.
 */
export default class DocumentService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/documents'
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Retrieves a single document by ID.
   *
   * @param {string} id - The ID of the document.
   * @returns {Promise<Object>} A promise resolving to the document data.
   */
  async get(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data
  }

  // ============================================================
  // Helper Methods for Lookup/Dropdown
  // ============================================================

  /**
   * Retrieves only the name of a document by ID.
   *
   * @param {string} id - The ID of the document.
   * @returns {Promise<string>} A promise resolving to the document name.
   */
  async getName(id) {
    const document = await this.get(id)
    return document.name
  }

  /**
   * Searches documents by name.
   *
   * @param {string} query - The value to search by (document name).
   * @returns {Promise<{ items: Array<Object>, pageDetails: Object }>}
   */
  async search(query) {
    const { data } = await this.http.get(`${this.path}/`, {
      params: {
        page: 1,
        limit: 25,
        sort_by: 'name',
        sort_order: 'asc',
        search_field: 'name',
        search_value: query,
      },
    })
    return data
  }
}
