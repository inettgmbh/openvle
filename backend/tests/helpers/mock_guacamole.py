"""Mock for Apache Guacamole API client."""


class MockGuacamoleClient:
    """Mock for Guacamole API client (guacamolelib.session)."""

    def __init__(self):
        self.token = "mock-guac-token"

    def authenticate(self):
        return self.token

    def generate_token(self):
        return self.token

    def delete_token(self):
        return {}

    # User management
    def list_users(self):
        return {}

    def detail_user(self, username):
        return {"username": username}

    def create_user(self, username, **kwargs):
        return {"username": username}

    def update_user(self, username, **kwargs):
        return {}

    def delete_user(self, username):
        return {}

    # Connection management
    def list_connections(self):
        return {}

    def detail_connection(self, identifier, option=None):
        if option == "parameters":
            return {
                "hostname": "10.0.0.1",
                "port": "3389",
                "username": "admin",
                "password": "secret",
            }
        return {
            "identifier": str(identifier),
            "name": "test-connection",
            "protocol": "rdp",
            "parentIdentifier": "ROOT",
            "attributes": {},
        }

    def manage_connection(self, **kwargs):
        return {"identifier": "123"}

    def create_connection(self, *args, **kwargs):
        return {"identifier": "123"}

    def delete_connection(self, identifier):
        return {}

    # Connection permissions
    def update_connection_permissions(self, **kwargs):
        return {}

    def update_user_connection(self, **kwargs):
        return {}

    # Sharing profiles
    def create_sharing_profile(self, **kwargs):
        return {"identifier": "sp-1"}

    def detail_sharing_profile(self, identifier):
        return {"identifier": str(identifier), "name": "test-profile"}

    def list_sharing_profiles(self, identifier):
        return {}

    def update_sharing_profile(self, **kwargs):
        return {}

    def delete_sharing_profile(self, identifier):
        return {}

    # Connection groups
    def list_connection_groups(self):
        return {}

    def create_connection_group(self, **kwargs):
        return {"identifier": "456"}

    def update_connection_group(self, **kwargs):
        return {}

    def delete_connection_group(self, identifier):
        return {}

    # Active connections
    def list_active_connections(self):
        return {}

    def kill_active_connections(self, identifiers):
        return {}
