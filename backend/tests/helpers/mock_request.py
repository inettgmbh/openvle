"""Mock FastAPI Request and User objects for testing."""

from unittest.mock import MagicMock


class MockUser:
    """Mimics the user object attached to request by AuthenticationMiddleware."""

    def __init__(self, user):
        self.id = user.id
        self.username = user.username
        self.name = user.name
        self.email = user.email
        self.status = user.status
        self.locale = user.locale
        self.is_authenticated = True


def create_mock_request(user):
    """
    Create a mock FastAPI Request that carries an authenticated user.

    The app accesses request.user.id, request.user.username etc.
    throughout controllers and dependencies.
    """
    request = MagicMock()
    request.user = MockUser(user)
    request.state = MagicMock()
    request.headers = {}
    request.query_params = {}
    request.path_params = {}
    request.url = MagicMock()
    request.url.path = "/v1/test"
    request.method = "GET"
    return request
