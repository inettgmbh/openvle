"""Mock for LDAP (ldap3.Connection)."""


class MockLDAPConnection:
    """Mock for ldap3.Connection."""

    def __init__(self, *args, **kwargs):
        self.bound = True
        self.entries = []

    def bind(self):
        return True

    def search(self, *args, **kwargs):
        return True

    def unbind(self):
        pass
