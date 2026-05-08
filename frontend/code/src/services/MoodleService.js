/**
 * Service for Moodle course-related API operations.
 */
export default class MoodleService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/moodle/courses'
  }

  /**
   * Searches Moodle courses by name.
   * Compatible with SearchControl's fetchData prop.
   *
   * @param {string} query - The search term.
   * @returns {Promise<{ items: Array<Object>, pageDetails: Object }>}
   */
  async search(query) {
    const { data } = await this.http.get(this.path, {
      params: { search: query },
    })
    return data
  }

  /**
   * Retrieves the display name for a Moodle course by ID.
   * Compatible with SearchControl's fetchSelected prop.
   *
   * @param {number} id - The Moodle course ID.
   * @returns {Promise<string>} The course fullname.
   */
  async getName(id) {
    const { data } = await this.http.get(this.path, {
      params: { id },
    })
    const course = data.items?.[0]
    return course ? course.fullname : `Moodle #${id}`
  }
}
