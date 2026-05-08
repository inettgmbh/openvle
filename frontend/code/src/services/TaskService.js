/**
 * Service for task-related API operations.
 */
export default class TaskService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/tasks'
    this.subTaskPath = '/sub-tasks'
  }

  // ============================================================
  // Task Methods
  // ============================================================

  /**
   * Retrieves a single task by its ID.
   *
   * @param {string} id - The ID of the task.
   * @returns {Promise<Object>} A promise resolving to the task data.
   */
  async get(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data
  }

  /**
   * Retrieves a paginated list of all tasks with optional search and sorting parameters.
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

  /**
   * Retrieves the name of a task by its ID.
   *
   * @param {string} id - The ID of the task.
   * @returns {Promise<string>} A promise resolving to the task name.
   */
  async getName(id) {
    const task = await this.get(id)
    return task.name
  }

  // ============================================================
  // Sub-Task Methods
  // ============================================================

  /**
   * Retrieves a single sub-task by its ID.
   *
   * @param {string} id - The ID of the sub-task.
   * @returns {Promise<Object>} A promise resolving to the sub-task data.
   */
  async getSubTask(id) {
    const { data } = await this.http.get(`${this.subTaskPath}/${id}`)
    return data
  }

  /**
   * Retrieves a paginated list of all sub-tasks with optional search and sorting parameters.
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
  async listSubTasks(params = {}) {
    const {
      page = 1,
      limit = 10,
      search_field = '',
      search_value = '',
      sort_by = 'createdAt',
      sort_order = 'desc',
    } = params

    const { data } = await this.http.get(`${this.subTaskPath}/`, {
      params: { page, limit, search_field, search_value, sort_by, sort_order },
    })
    return data
  }

  /**
   * Retrieves a paginated list of sub-tasks assigned to the specified task.
   *
   * @param {string} taskId - The ID of the parent task.
   * @param {Object} params - Query parameters for pagination, filtering, and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.search_field=""] - Field to search by.
   * @param {string} [params.search_value=""] - Search term.
   * @param {string} [params.sort_by="createdAt"] - Field to sort by.
   * @param {string} [params.sort_order="desc"] - Sort order (`asc` or `desc`).
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async listSubTasksByTask(taskId, params = {}) {
    const {
      page = 1,
      limit = 10,
      search_field = '',
      search_value = '',
      sort_by = 'createdAt',
      sort_order = 'desc',
    } = params

    const { data } = await this.http.get(`${this.path}/${taskId}/sub-tasks`, {
      params: { page, limit, search_field, search_value, sort_by, sort_order },
    })
    return data
  }

  /**
   * Retry a single failed sub-task by its ID.
   *
   * @param {string} id - The ID of the failed sub-task.
   * @returns {Promise<Object>} A promise resolving to the (current) sub-task data.
   */
  async retrySubTask(id) {
    const { data } = await this.http.get(`${this.subTaskPath}/${id}/retry`)
    return data
  }
}
