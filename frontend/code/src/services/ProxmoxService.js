/**
 * Service for Proxmox cluster-related API operations.
 */
export default class ProxmoxService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/proxmox'
  }

  // ============================================================
  // Cluster Methods
  // ============================================================

  /**
   * Retrieves the cluster log from the Proxmox cluster.
   *
   * @returns {Promise<Object>} A promise resolving to the cluster log data.
   */
  async getClusterLog() {
    const { data } = await this.http.get(`${this.path}/cluster/logs`)
    return data
  }

  /**
   * Retrieves information about resources in the Proxmox cluster.
   *
   * @returns {Promise<Object>} A promise resolving to the cluster resources data.
   */
  async getClusterResources() {
    const { data } = await this.http.get(`${this.path}/cluster/resources`)
    return data
  }

  /**
   * Retrieves the current status of the Proxmox cluster.
   *
   * @returns {Promise<Object>} A promise resolving to the cluster status.
   */
  async getClusterStatus() {
    const { data } = await this.http.get(`${this.path}/cluster/status`)
    return data
  }

  /**
   * Retrieves the task list of the Proxmox cluster.
   *
   * @returns {Promise<Object>} A promise resolving to the cluster tasks.
   */
  async getClusterTasks() {
    const { data } = await this.http.get(`${this.path}/cluster/tasks`)
    return data
  }

  /**
   * Fetches all cluster tasks for a specific Proxmox node.
   *
   * @param {string} nodeName - The name or identifier of the Proxmox node.
   * @returns {Promise<Object[]>} A promise resolving with an array of cluster task objects for the node.
   */
  async getClusterTasksByNode(nodeName) {
    const { data } = await this.http.get(`${this.path}/cluster/tasks`)
    return data.filter((task) => task.node === nodeName)
  }

  /**
   * Retrieves the count of active elements in the cluster.
   *
   * @returns {Promise<Object>} A promise resolving to object counts in the cluster.
   */
  async getClusterCounts() {
    const { data } = await this.http.get(`${this.path}/cluster/counts`)
    return data
  }

  // ============================================================
  // Node Methods
  // ============================================================

  /**
   * Retrieves a list of all Proxmox nodes.
   *
   * @returns {Promise<Object>} A promise resolving to the list of nodes.
   */
  async getNodes() {
    const { data } = await this.http.get(`${this.path}/nodes`)
    return data
  }

  /**
   * Fetches details of a specific Proxmox node.
   *
   * @param {string} nodeName - The name or identifier of the Proxmox node to retrieve.
   * @returns {Promise<Object|undefined>} A promise resolving with the node object if found.
   */
  async getNode(nodeName) {
    const { data } = await this.http.get(`${this.path}/nodes`)
    return data.find((node) => node.name === nodeName)
  }

  /**
   * Fetches an RRD graph for a given Proxmox node.
   *
   * @param {string} nodeName - The name or identifier of the Proxmox node.
   * @param {string} [timeframe='hour'] - The timeframe of the graph.
   * @param {string} [cf='AVERAGE'] - The RRD consolidation function.
   * @param {string} [ds='cpu'] - The dataset to display.
   * @returns {Promise<Object>} A promise resolving with the graph data of the node.
   */
  async getNodeRRDPicture(
    nodeName,
    timeframe = 'hour',
    cf = 'AVERAGE',
    ds = 'cpu',
  ) {
    const { data } = await this.http.get(`${this.path}/nodes/${nodeName}/rrd`, {
      params: { timeframe, cf, ds },
    })
    return data
  }

  /**
   * Fetches detailed RRD time-series data for a given Proxmox node.
   *
   * @param {string} nodeName - The name or identifier of the Proxmox node.
   * @param {string} [timeframe='hour'] - The timeframe of the metrics.
   * @param {string} [cf='AVERAGE'] - The RRD consolidation function.
   * @returns {Promise<Object>} A promise resolving with the raw RRD data of the node.
   */
  async getNodeRRDData(nodeName, timeframe = 'hour', cf = 'AVERAGE') {
    const { data } = await this.http.get(
      `${this.path}/nodes/${nodeName}/rrddata`,
      {
        params: { timeframe, cf },
      },
    )
    return data
  }
}
