"""
Moodle Web Services REST API Client
"""

import httpx


class MoodleAPIError(Exception):
    """Error returned by the Moodle Web Services API."""

    def __init__(self, error_code: str, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(f"Moodle API Error [{error_code}]: {message}")


class MoodleClient:
    """Synchronous HTTP client for the Moodle Web Services REST API.

    Args:
        url: Base URL of the Moodle instance (e.g. https://moodle.example.com).
        token: Web Services API token.
        verify_ssl: Whether to verify SSL certificates.
        timeout: Request timeout in seconds.
    """

    def __init__(
        self,
        url: str,
        token: str,
        verify_ssl: bool = True,
        timeout: int = 30,
    ):
        self.url = url.rstrip("/")
        self.token = token
        self.endpoint = f"{self.url}/webservice/rest/server.php"
        self.client = httpx.Client(
            verify=verify_ssl,
            timeout=timeout,
        )

    def _call(self, wsfunction: str, **params) -> dict | list:
        """Execute a Moodle Web Services API call.

        Args:
            wsfunction: The web service function name.
            **params: Additional parameters for the API call.

        Returns:
            Parsed JSON response from Moodle.

        Raises:
            MoodleAPIError: If Moodle returns an error response.
            httpx.HTTPError: If the HTTP request fails.
        """
        data = {
            "wstoken": self.token,
            "wsfunction": wsfunction,
            "moodlewsrestformat": "json",
        }
        data.update(params)

        response = self.client.post(self.endpoint, data=data)
        response.raise_for_status()
        result = response.json()

        if isinstance(result, dict) and "exception" in result:
            raise MoodleAPIError(
                error_code=result.get("errorcode", "unknown"),
                message=result.get("message", "Unknown error"),
            )

        return result

    # ------------------------------------------------------------------
    # Site / Info
    # ------------------------------------------------------------------

    def get_site_info(self) -> dict:
        """Validate connection and token via core_webservice_get_site_info."""
        return self._call("core_webservice_get_site_info")

    # ------------------------------------------------------------------
    # Courses
    # ------------------------------------------------------------------

    def get_courses(self, ids: list[int] | None = None) -> list[dict]:
        """Get courses by ID list.

        Args:
            ids: List of Moodle course IDs. If None, returns all courses.
        """
        params = {}
        if ids:
            for i, cid in enumerate(ids):
                params[f"options[ids][{i}]"] = cid
        return self._call("core_course_get_courses", **params)

    def search_courses(
        self, search: str = "", page: int = 0, per_page: int = 0
    ) -> list[dict]:
        """Search courses using Moodle's built-in search.

        Uses core_course_search_courses which respects permissions
        and supports fulltext search.

        Args:
            search: Search term (matches fullname, shortname, summary).
            page: Page number (0-based).
            per_page: Results per page (0 = all).

        Returns:
            List of matching course dicts.
        """
        result = self._call(
            "core_course_search_courses",
            criterianame="search",
            criteriavalue=search,
            page=page,
            perpage=per_page,
        )
        if isinstance(result, dict) and "courses" in result:
            return result["courses"]
        return result

    def get_courses_by_field(
        self, field: str = "", value: str = ""
    ) -> list[dict]:
        """Search courses by field (e.g. 'shortname', 'idnumber').

        Args:
            field: The field to search by.
            value: The value to search for.

        Returns:
            List of matching courses.
        """
        result = self._call(
            "core_course_get_courses_by_field",
            field=field,
            value=value,
        )
        if isinstance(result, dict) and "courses" in result:
            return result["courses"]
        return result

    def create_courses(self, courses: list[dict]) -> list[dict]:
        """Create one or more courses in Moodle.

        Args:
            courses: List of course dicts with keys like
                     'fullname', 'shortname', 'categoryid', etc.

        Returns:
            List of dicts with 'id' and 'shortname' for each created course.
        """
        params = {}
        for i, course in enumerate(courses):
            for key, value in course.items():
                params[f"courses[{i}][{key}]"] = value
        return self._call("core_course_create_courses", **params)

    def update_courses(self, courses: list[dict]) -> None:
        """Update one or more courses in Moodle.

        Args:
            courses: List of course dicts. Each must include 'id' and
                     the fields to update.
        """
        params = {}
        for i, course in enumerate(courses):
            for key, value in course.items():
                params[f"courses[{i}][{key}]"] = value
        self._call("core_course_update_courses", **params)

    def duplicate_course(
        self,
        course_id: int,
        fullname: str,
        shortname: str,
        categoryid: int,
        visible: bool = True,
    ) -> dict:
        """Duplicate (clone) an existing Moodle course.

        Args:
            course_id: Source course ID to duplicate.
            fullname: Full name for the new course.
            shortname: Short name for the new course.
            categoryid: Category ID for the new course.
            visible: Whether the new course is visible.

        Returns:
            Dict with 'id' and 'shortname' of the new course.
        """
        return self._call(
            "core_course_duplicate_course",
            courseid=course_id,
            fullname=fullname,
            shortname=shortname,
            categoryid=categoryid,
            visible=int(visible),
        )

    def delete_courses(self, ids: list[int]) -> None:
        """Delete courses by ID list.

        Args:
            ids: List of Moodle course IDs to delete.
        """
        params = {}
        for i, cid in enumerate(ids):
            params[f"courseids[{i}]"] = cid
        self._call("core_course_delete_courses", **params)

    # ------------------------------------------------------------------
    # Categories
    # ------------------------------------------------------------------

    def get_categories(self, criteria: list[dict] | None = None) -> list[dict]:
        """Get course categories.

        Args:
            criteria: Optional list of filter criteria dicts with
                      'key' and 'value' (e.g. [{'key': 'id', 'value': '1'}]).

        Returns:
            List of category dicts.
        """
        params = {}
        if criteria:
            for i, criterion in enumerate(criteria):
                params[f"criteria[{i}][key]"] = criterion["key"]
                params[f"criteria[{i}][value]"] = criterion["value"]
        return self._call("core_course_get_categories", **params)

    # ------------------------------------------------------------------
    # Enrolments
    # ------------------------------------------------------------------

    def get_enrolled_users(self, course_id: int) -> list[dict]:
        """Get users enrolled in a course.

        Args:
            course_id: The Moodle course ID.

        Returns:
            List of enrolled user dicts.
        """
        return self._call("core_enrol_get_enrolled_users", courseid=course_id)

    def enrol_users(self, enrolments: list[dict]) -> None:
        """Enrol users into courses.

        Args:
            enrolments: List of dicts with 'roleid', 'userid', 'courseid'.
        """
        params = {}
        for i, enrolment in enumerate(enrolments):
            params[f"enrolments[{i}][roleid]"] = enrolment["roleid"]
            params[f"enrolments[{i}][userid]"] = enrolment["userid"]
            params[f"enrolments[{i}][courseid]"] = enrolment["courseid"]
        self._call("enrol_manual_enrol_users", **params)

    def unenrol_users(self, enrolments: list[dict]) -> None:
        """Unenrol users from courses.

        Args:
            enrolments: List of dicts with 'roleid', 'userid', 'courseid'.
        """
        params = {}
        for i, enrolment in enumerate(enrolments):
            params[f"enrolments[{i}][roleid]"] = enrolment["roleid"]
            params[f"enrolments[{i}][userid]"] = enrolment["userid"]
            params[f"enrolments[{i}][courseid]"] = enrolment["courseid"]
        self._call("enrol_manual_unenrol_users", **params)

    # ------------------------------------------------------------------
    # Roles
    # ------------------------------------------------------------------

    def unassign_roles(self, unassignments: list[dict]) -> None:
        """Remove role assignments from users in a course context.

        Args:
            unassignments: List of dicts with 'roleid', 'userid',
                           'contextlevel' (default 'course'),
                           and 'instanceid' (course id).
        """
        params = {}
        for i, ua in enumerate(unassignments):
            params[f"unassignments[{i}][roleid]"] = ua["roleid"]
            params[f"unassignments[{i}][userid]"] = ua["userid"]
            params[f"unassignments[{i}][contextlevel]"] = ua.get(
                "contextlevel", "course"
            )
            params[f"unassignments[{i}][instanceid]"] = ua["instanceid"]
        self._call("core_role_unassign_roles", **params)

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def create_users(self, users: list[dict]) -> list[dict]:
        """Create one or more users in Moodle.

        Args:
            users: List of user dicts with keys like
                   'username', 'firstname', 'lastname', 'email',
                   'auth', 'password', 'preferences', etc.

        Returns:
            List of dicts with 'id' and 'username' for each created user.
        """
        params = {}
        for i, user in enumerate(users):
            for key, value in user.items():
                params[f"users[{i}][{key}]"] = value
        return self._call("core_user_create_users", **params)

    def get_users_by_field(self, field: str, values: list[str]) -> list[dict]:
        """Find Moodle users by a specific field.

        Args:
            field: Field name (e.g. 'email', 'username', 'id').
            values: List of values to search for.

        Returns:
            List of matching user dicts.
        """
        params = {"field": field}
        for i, value in enumerate(values):
            params[f"values[{i}]"] = value
        return self._call("core_user_get_users_by_field", **params)

    def close(self):
        """Close the underlying HTTP client."""
        self.client.close()
