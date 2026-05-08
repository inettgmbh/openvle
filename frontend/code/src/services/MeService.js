/**
 * Service for endpoints scoped to the currently authenticated user (`/me/*`).
 *
 * These were previously merged into `UserService`; they're split out here
 * because they don't operate on a user resource by id but on the implicit
 * "self" identity, and they have a distinct backend route prefix.
 */
export default class MeService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this.path = '/me'
  }

  /**
   * Retrieves the currently authenticated user.
   *
   * @returns {Promise<Object>} The current user object.
   */
  async get() {
    const { data } = await this.http.get(this.path)
    return data
  }

  /**
   * Retrieves the permissions of the currently authenticated user.
   *
   * @returns {Promise<Array<Object>>} The list of permission entries.
   */
  async getPermissions() {
    const { data } = await this.http.get(`${this.path}/permissions`)
    return data
  }

  /**
   * Updates the password of the currently authenticated user.
   *
   * @param {string} passwordOld - The current password.
   * @param {string} passwordNew - The new password.
   * @param {string} passwordNewRepeat - The new password again, for confirmation.
   * @returns {Promise<Object>} The update response payload.
   */
  async updatePassword(passwordOld, passwordNew, passwordNewRepeat) {
    const { data } = await this.http.put(`${this.path}/password`, {
      password_old: passwordOld,
      password_new: passwordNew,
      password_new_repeat: passwordNewRepeat,
    })
    return data
  }
}
