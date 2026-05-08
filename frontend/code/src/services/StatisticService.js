/**
 * Service for statistics-related API operations.
 */
export default class StatisticService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/statistics'
  }

  // ============================================================
  // Dashboard Methods
  // ============================================================

  /**
   * Retrieves statistical summary data for the dashboard.
   *
   * @returns {Promise<Object>} A promise resolving to the dashboard statistics.
   */
  async getDashboard() {
    const { data } = await this.http.get(`${this.path}/dashboard`)
    return data
  }
}
