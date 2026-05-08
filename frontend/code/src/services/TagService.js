import { resolveObjectTypeToGerman } from '@/utils/dataUtils'

/**
 * Service for tag-related API operations.
 */
export default class TagService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/tags'
  }

  // ============================================================
  // Standard CRUD Methods
  // ============================================================

  /**
   * Creates a new tag for a specific object.
   *
   * @param {Object} data - Tag data.
   * @param {string} data.key - The tag key.
   * @param {string} data.value - The tag value.
   * @param {string} data.objectId - The ID of the object to tag.
   * @param {string} data.objectType - The type of the object.
   * @returns {Promise<Object>} A promise resolving to the created tag.
   */
  async create(data) {
    const { key, value, objectId, objectType } = data
    const { data: result } = await this.http.post(`${this.path}/`, {
      key: String(key).toLowerCase(),
      value: String(value).toLowerCase(),
      objectId,
      objectType,
    })
    return result
  }

  /**
   * Retrieves a single tag by its ID.
   *
   * @param {string} id - The ID of the tag.
   * @returns {Promise<Object>} A promise resolving to the tag data.
   */
  async get(id) {
    const { data } = await this.http.get(`${this.path}/${id}`)
    return data
  }

  /**
   * Retrieves a paginated list of all tags with optional search and sorting parameters.
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
   * Deletes a tag by ID.
   *
   * @param {string} id - The ID of the tag to delete.
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
   * Retrieves a single tag label (key: value (objectType)) by its ID.
   *
   * @param {string} id - The ID of the tag.
   * @returns {Promise<string>} A promise resolving to the tag label.
   */
  async getLabel(id) {
    const tag = await this.get(id)
    return `"${tag?.key}: ${tag?.value}" (${resolveObjectTypeToGerman(tag?.objectType)})`
  }

  /**
   * Searches tags by key.
   *
   * @param {string} query - The value to search by.
   * @returns {Promise<{ items: Array<Object>, pageDetails: Object }>}
   */
  async search(query) {
    const response = await this.list({
      page: 1,
      limit: 25,
      sort_by: 'key',
      sort_order: 'asc',
      search_field: 'key',
      search_value: query,
    })

    const seen = new Set()
    const uniqueItems = response.items.filter((item) => {
      const key = item.key.toLowerCase()
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })

    return {
      items: uniqueItems,
      pageDetails: response.pageDetails,
    }
  }

  // ============================================================
  // Related Resources
  // ============================================================

  /**
   * Retrieves a paginated list of tags for a specific object.
   *
   * @param {string} objectType - The type of the object.
   * @param {string} objectId - The ID of the object.
   * @param {Object} params - Query parameters for pagination and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.sort_by="createdAt"] - Field to sort by.
   * @param {string} [params.sort_order="desc"] - Sort order (`asc` or `desc`).
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async listByObject(objectType, objectId, params = {}) {
    const {
      page = 1,
      limit = 10,
      sort_by = 'createdAt',
      sort_order = 'desc',
    } = params

    const { data } = await this.http.get(
      `${this.path}/${objectType}/${objectId}`,
      {
        params: { page, limit, sort_by, sort_order },
      },
    )
    return data
  }

  /**
   * Retrieves a paginated list of tags by key.
   *
   * @param {string} key - The tag key to filter by.
   * @param {Object} params - Query parameters for pagination and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.sort_by="createdAt"] - Field to sort by.
   * @param {string} [params.sort_order="desc"] - Sort order (`asc` or `desc`).
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async listByKey(key, params = {}) {
    const {
      page = 1,
      limit = 10,
      sort_by = 'createdAt',
      sort_order = 'desc',
    } = params

    const { data } = await this.http.get(`${this.path}/${key}/`, {
      params: { page, limit, sort_by, sort_order },
    })
    return data
  }

  /**
   * Retrieves a paginated list of tags by key-value pair.
   *
   * @param {string} key - The tag key.
   * @param {string} value - The tag value.
   * @param {Object} params - Query parameters for pagination and sorting.
   * @param {number} [params.page=1] - The page number to fetch.
   * @param {number} [params.limit=10] - Number of entries per page.
   * @param {string} [params.sort_by="createdAt"] - Field to sort by.
   * @param {string} [params.sort_order="desc"] - Sort order (`asc` or `desc`).
   * @returns {Promise<{ pageDetails: Object, items: Array<Object> }>}
   */
  async listByKeyValue(key, value, params = {}) {
    const {
      page = 1,
      limit = 10,
      sort_by = 'createdAt',
      sort_order = 'desc',
    } = params

    const { data } = await this.http.get(`${this.path}/${key}/${value}/`, {
      params: { page, limit, sort_by, sort_order },
    })
    return data
  }
}
