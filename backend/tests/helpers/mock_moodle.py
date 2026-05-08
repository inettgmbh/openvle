"""Mock for Moodle Web Services API client."""


class MockMoodleClient:
    """Mock for MoodleClient with call tracking and error injection.

    Usage:
        mock = MockMoodleClient()
        mock._errors["get_courses"] = MoodleAPIError("err", "msg")
        mock.returns["get_users_by_field"] = [{"id": 42, "username": "test"}]
    """

    def __init__(self):
        self.calls = []
        self.returns = {}
        self._errors = {}
        self._closed = False
        self.url = "https://moodle.test"
        self.token = "test-token"
        self.endpoint = f"{self.url}/webservice/rest/server.php"

    def _record(self, method, **kwargs):
        self.calls.append({"method": method, **kwargs})
        if method in self._errors:
            raise self._errors[method]
        return self.returns.get(method, {})

    # Low-level call (used directly by ensure_moodle_user)
    def _call(self, wsfunction, **params):
        return self._record("_call", wsfunction=wsfunction, params=params)

    # Site
    def get_site_info(self):
        return self._record("get_site_info")

    # Courses
    def get_courses(self, ids=None):
        return self._record("get_courses", ids=ids)

    def search_courses(self, search="", page=0, per_page=0):
        return self._record(
            "search_courses", search=search, page=page, per_page=per_page
        )

    def get_courses_by_field(self, field="", value=""):
        return self._record("get_courses_by_field", field=field, value=value)

    def create_courses(self, courses):
        return self._record("create_courses", courses=courses)

    def update_courses(self, courses):
        return self._record("update_courses", courses=courses)

    def duplicate_course(
        self, course_id, fullname, shortname, categoryid, visible=True
    ):
        return self._record(
            "duplicate_course",
            course_id=course_id,
            fullname=fullname,
            shortname=shortname,
            categoryid=categoryid,
            visible=visible,
        )

    def delete_courses(self, ids):
        return self._record("delete_courses", ids=ids)

    # Categories
    def get_categories(self, criteria=None):
        return self._record("get_categories", criteria=criteria)

    # Enrolments
    def get_enrolled_users(self, course_id):
        return self._record("get_enrolled_users", course_id=course_id)

    def enrol_users(self, enrolments):
        return self._record("enrol_users", enrolments=enrolments)

    def unenrol_users(self, enrolments):
        return self._record("unenrol_users", enrolments=enrolments)

    # Roles
    def unassign_roles(self, unassignments):
        return self._record("unassign_roles", unassignments=unassignments)

    # Users
    def create_users(self, users):
        return self._record("create_users", users=users)

    def get_users_by_field(self, field, values):
        return self._record("get_users_by_field", field=field, values=values)

    def close(self):
        self._closed = True
        self.calls.append({"method": "close"})
