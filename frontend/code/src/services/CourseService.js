/**
 * Service for course-related API operations.
 */
export default class CourseService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/courses'
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Creates a new course with Guacamole support.
   *
   * @param {Object} data - Course details.
   * @param {string} data.name - The name of the course.
   * @param {string} data.description - The course description.
   * @returns {Promise<Object>} A promise resolving to the created course.
   */
  async create(data) {
    const { name, description } = data
    const { data: result } = await this.http.post(`${this.path}/`, {
      name,
      description,
      guacamole: true,
    })
    return result
  }

  /**
   * Retrieves a course by its ID.
   *
   * @param {string} id - The ID of the course.
   * @returns {Promise<Object>} A promise resolving to the course data.
   */
  async get(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data
  }

  /**
   * Retrieves a paginated list of all courses.
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
   * Updates an existing course.
   *
   * @param {string} id - The ID of the course to update.
   * @param {Object} data - Fields to update.
   * @returns {Promise<Object>} A promise resolving to the updated course.
   */
  async update(id, data) {
    const { data: result } = await this.http.put(`${this.path}/${id}`, data)
    return result
  }

  /**
   * Deletes a course by its ID.
   *
   * @param {string} id - The ID of the course.
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
   * Retrieves only the name of a course by ID.
   *
   * @param {string} id - The ID of the course.
   * @returns {Promise<string>} A promise resolving to the course name.
   */
  async getName(id) {
    const course = await this.get(id)
    return course.name
  }

  /**
   * Fetches all courses and formats them for dropdown use.
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
   * Searches courses by name.
   *
   * @param {string} query - The course name or partial name to search.
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
   * Retrieves a paginated list of templates assigned to a course.
   *
   * @param {string} id - The ID of the course.
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

  // ============================================================
  // Template Management
  // ============================================================

  /**
   * Assigns a template to a course.
   *
   * @param {string} id - The ID of the course.
   * @param {string} templateId - The ID of the template to assign.
   * @returns {Promise<Object>}
   */
  async addTemplate(id, templateId) {
    const { data } = await this.http.post(`${this.path}/${id}/template`, {
      templates: [{ id: templateId }],
    })
    return data
  }

  /**
   * Removes a template from a course.
   *
   * @param {string} id - The ID of the course.
   * @param {string} templateId - The ID of the template to remove.
   * @returns {Promise<Object>}
   */
  async deleteTemplate(id, templateId) {
    const { data } = await this.http.delete(`${this.path}/${id}/template`, {
      data: { templates: [{ id: templateId }] },
    })
    return data
  }
}
