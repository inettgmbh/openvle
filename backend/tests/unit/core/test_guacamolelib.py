"""Tests for core/guacamolelib.py - Guacamole REST API wrapper.

Tests cover the `session` class methods by mocking `requests.get/post/put/delete/patch`.

- __init__: stores host, data_source, calls generate_token
- generate_token: success returns authToken, JSON decode error returns raw
- delete_token: success
- list_users: returns parsed JSON
- detail_user: returns user dict, handles non-JSON response
- create_user: with and without attributes
- update_user: with attributes
- delete_user: success
- manage_connection: rdp protocol, ssh protocol
- delete_connection: success
- create_sharing_profile: success
- list_connection_groups: success
- create_connection_group: success
"""

import json
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_response(text_content):
    """Create a mock response object with .text attribute."""
    mock = MagicMock()
    mock.text = text_content
    return mock


def _create_client(mock_post):
    """Create a guacamolelib.session with mocked token generation."""
    mock_post.return_value = _mock_response(
        json.dumps({"authToken": "test-token-abc"})
    )
    from core.guacamolelib import session

    client = session("http://guac.local", "mysql", "guacadmin", "guacpass")
    return client


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSessionInit:
    """Tests for session.__init__."""

    @patch("core.guacamolelib.requests.post")
    def test_stores_config(self, mock_post):
        """Should store host, data_source, username, password."""
        client = _create_client(mock_post)

        assert client.host == "http://guac.local"
        assert client.data_source == "mysql"
        assert client.username == "guacadmin"
        assert client.password == "guacpass"
        assert client.session_url == "http://guac.local/api/session/data/mysql"

    @patch("core.guacamolelib.requests.post")
    def test_calls_generate_token(self, mock_post):
        """Should call generate_token on init, setting self.token."""
        client = _create_client(mock_post)

        assert client.token == "test-token-abc"
        assert client.params == {"token": "test-token-abc"}


class TestGenerateToken:
    """Tests for session.generate_token."""

    @patch("core.guacamolelib.requests.post")
    def test_success_returns_auth_token(self, mock_post):
        """Should return authToken from JSON response."""
        client = _create_client(mock_post)
        assert client.token == "test-token-abc"

    @patch("core.guacamolelib.requests.post")
    def test_json_decode_error_returns_raw(self, mock_post):
        """Should return raw text when response is not valid JSON."""
        # First call for __init__
        mock_post.return_value = _mock_response(
            json.dumps({"authToken": "init-token"})
        )
        from core.guacamolelib import session

        client = session("http://guac.local", "mysql", "admin", "pass")

        # Second call: simulate non-JSON response
        mock_post.return_value = _mock_response("INVALID_RESPONSE")
        result = client.generate_token()
        assert result == "INVALID_RESPONSE"


class TestDeleteToken:
    """Tests for session.delete_token."""

    @patch("core.guacamolelib.requests.delete")
    @patch("core.guacamolelib.requests.post")
    def test_success(self, mock_post, mock_delete):
        """Should call DELETE on /api/tokens/{token}."""
        client = _create_client(mock_post)
        mock_delete.return_value = _mock_response("{}")

        result = client.delete_token()
        assert result == {}

        mock_delete.assert_called_once()
        call_url = mock_delete.call_args[0][0]
        assert "/api/tokens/" in call_url


class TestListUsers:
    """Tests for session.list_users."""

    @patch("core.guacamolelib.requests.get")
    @patch("core.guacamolelib.requests.post")
    def test_returns_parsed_json(self, mock_post, mock_get):
        """Should return parsed JSON user list."""
        client = _create_client(mock_post)

        user_data = {
            "guacadmin": {"username": "guacadmin"},
            "testuser": {"username": "testuser"},
        }
        mock_get.return_value = _mock_response(json.dumps(user_data))

        result = client.list_users()
        assert result == user_data
        assert "guacadmin" in result
        assert "testuser" in result


class TestDetailUser:
    """Tests for session.detail_user."""

    @patch("core.guacamolelib.requests.get")
    @patch("core.guacamolelib.requests.post")
    def test_returns_user_dict(self, mock_post, mock_get):
        """Should return user detail dict."""
        client = _create_client(mock_post)

        user_data = {"username": "testuser", "attributes": {"disabled": ""}}
        mock_get.return_value = _mock_response(json.dumps(user_data))

        result = client.detail_user("testuser")
        assert result["username"] == "testuser"

    @patch("core.guacamolelib.requests.get")
    @patch("core.guacamolelib.requests.post")
    def test_handles_non_json_response(self, mock_post, mock_get):
        """Should return raw string when response is not JSON."""
        client = _create_client(mock_post)

        mock_get.return_value = _mock_response("Not Found")

        result = client.detail_user("nonexistent")
        assert result == "Not Found"


class TestCreateUser:
    """Tests for session.create_user."""

    @patch("core.guacamolelib.requests.post")
    def test_without_attributes(self, mock_post):
        """Should create user without attributes."""
        client = _create_client(mock_post)

        response_data = {"username": "newuser"}
        mock_post.return_value = _mock_response(json.dumps(response_data))

        result = client.create_user("newuser", password=None)
        assert result["username"] == "newuser"

    @patch("core.guacamolelib.requests.post")
    def test_with_attributes(self, mock_post):
        """Should create user with attributes."""
        client = _create_client(mock_post)

        response_data = {"username": "newuser"}
        mock_post.return_value = _mock_response(json.dumps(response_data))

        result = client.create_user(
            "newuser",
            password="secret",
            attributes={
                "disabled": "",
                "guac-full-name": "New User",
                "timezone": "Europe/Berlin",
            },
        )
        assert result["username"] == "newuser"

        # Verify the POST was called with correct JSON
        last_call = mock_post.call_args
        assert last_call is not None
        sent_json = last_call.kwargs.get("json") or last_call[1].get("json")
        assert sent_json["username"] == "newuser"
        assert sent_json["password"] == "secret"


class TestUpdateUser:
    """Tests for session.update_user."""

    @patch("core.guacamolelib.requests.put")
    @patch("core.guacamolelib.requests.post")
    def test_with_attributes(self, mock_post, mock_put):
        """Should update user attributes."""
        client = _create_client(mock_post)

        mock_put.return_value = _mock_response("{}")

        result = client.update_user(
            "testuser",
            attributes={
                "disabled": "true",
                "guac-full-name": "Updated Name",
            },
        )
        assert result == {}

        mock_put.assert_called_once()
        call_url = mock_put.call_args[0][0]
        assert "/users/testuser" in call_url


class TestDeleteUserLib:
    """Tests for session.delete_user."""

    @patch("core.guacamolelib.requests.delete")
    @patch("core.guacamolelib.requests.post")
    def test_success(self, mock_post, mock_delete):
        """Should delete user."""
        client = _create_client(mock_post)

        mock_delete.return_value = _mock_response("{}")

        result = client.delete_user("testuser")
        assert result == {}

        mock_delete.assert_called_once()
        call_url = mock_delete.call_args[0][0]
        assert "/users/testuser" in call_url


class TestManageConnection:
    """Tests for session.manage_connection."""

    @patch("core.guacamolelib.requests.post")
    def test_rdp_protocol_create(self, mock_post):
        """Should create an RDP connection (POST, no identifier)."""
        client = _create_client(mock_post)

        response_data = {"identifier": "456", "name": "test-rdp"}
        mock_post.return_value = _mock_response(json.dumps(response_data))

        result = client.manage_connection(
            protocol="rdp",
            name="test-rdp",
            parent_identifier="ROOT",
            parameters={
                "hostname": "10.0.0.1",
                "port": "3389",
                "username": "admin",
                "password": "pass",
            },
        )
        assert result["identifier"] == "456"

    @patch("core.guacamolelib.requests.put")
    @patch("core.guacamolelib.requests.post")
    def test_rdp_protocol_update(self, mock_post, mock_put):
        """Should update an existing RDP connection (PUT, with identifier)."""
        client = _create_client(mock_post)

        mock_put.return_value = _mock_response("{}")

        result = client.manage_connection(
            protocol="rdp",
            name="test-rdp",
            parent_identifier="ROOT",
            identifier="456",
            parameters={
                "hostname": "10.0.0.2",
                "port": "3389",
                "username": "admin",
                "password": "pass",
            },
        )
        # PUT returns empty body on success
        assert result == {}
        mock_put.assert_called_once()

    @patch("core.guacamolelib.requests.post")
    def test_ssh_protocol(self, mock_post):
        """Should create an SSH connection."""
        client = _create_client(mock_post)

        response_data = {"identifier": "789", "name": "test-ssh"}
        mock_post.return_value = _mock_response(json.dumps(response_data))

        result = client.manage_connection(
            protocol="ssh",
            name="test-ssh",
            parameters={
                "hostname": "10.0.0.1",
                "port": "22",
                "username": "root",
                "password": "pass",
            },
        )
        assert result["identifier"] == "789"

    @patch("core.guacamolelib.requests.post")
    def test_invalid_protocol_raises(self, mock_post):
        """Should raise ValueError for invalid protocol."""
        client = _create_client(mock_post)

        with pytest.raises(ValueError, match="Invalid protocol"):
            client.manage_connection(
                protocol="invalid",
                name="test",
            )


class TestDeleteConnectionLib:
    """Tests for session.delete_connection."""

    @patch("core.guacamolelib.requests.delete")
    @patch("core.guacamolelib.requests.post")
    def test_success(self, mock_post, mock_delete):
        """Should delete connection by identifier."""
        client = _create_client(mock_post)

        mock_delete.return_value = _mock_response("{}")

        result = client.delete_connection("123")
        assert result == {}

        mock_delete.assert_called_once()
        call_url = mock_delete.call_args[0][0]
        assert "/connections/123" in call_url


class TestCreateSharingProfile:
    """Tests for session.create_sharing_profile."""

    @patch("core.guacamolelib.requests.post")
    def test_success(self, mock_post):
        """Should create sharing profile and return identifier."""
        client = _create_client(mock_post)

        response_data = {"identifier": "sp-99", "name": "Ansehen"}
        mock_post.return_value = _mock_response(json.dumps(response_data))

        result = client.create_sharing_profile(
            primary_identifier="123",
            name="Ansehen",
            parameters={"read-only": True},
        )
        assert result["identifier"] == "sp-99"

    @patch("core.guacamolelib.requests.post")
    def test_without_parameters(self, mock_post):
        """Should create sharing profile without parameters."""
        client = _create_client(mock_post)

        response_data = {"identifier": "sp-100", "name": "Full"}
        mock_post.return_value = _mock_response(json.dumps(response_data))

        result = client.create_sharing_profile(
            primary_identifier="123",
            name="Full",
        )
        assert result["identifier"] == "sp-100"


class TestListConnectionGroups:
    """Tests for session.list_connection_groups."""

    @patch("core.guacamolelib.requests.get")
    @patch("core.guacamolelib.requests.post")
    def test_success(self, mock_post, mock_get):
        """Should return parsed JSON connection groups."""
        client = _create_client(mock_post)

        groups_data = {
            "ROOT": {"name": "ROOT", "type": "ORGANIZATIONAL"},
            "1": {"name": "Group 1", "type": "ORGANIZATIONAL"},
        }
        mock_get.return_value = _mock_response(json.dumps(groups_data))

        result = client.list_connection_groups()
        assert "ROOT" in result
        assert "1" in result


class TestCreateConnectionGroup:
    """Tests for session.create_connection_group."""

    @patch("core.guacamolelib.requests.post")
    def test_success(self, mock_post):
        """Should create connection group and return identifier."""
        client = _create_client(mock_post)

        response_data = {"identifier": "2", "name": "New Group"}
        mock_post.return_value = _mock_response(json.dumps(response_data))

        result = client.create_connection_group(group_name="New Group")
        assert result["identifier"] == "2"

    @patch("core.guacamolelib.requests.post")
    def test_with_attributes(self, mock_post):
        """Should create connection group with custom attributes."""
        client = _create_client(mock_post)

        response_data = {"identifier": "3", "name": "Balanced Group"}
        mock_post.return_value = _mock_response(json.dumps(response_data))

        result = client.create_connection_group(
            group_name="Balanced Group",
            group_type="BALANCING",
            parent_identifier="ROOT",
            attributes={"max-connections": "10"},
        )
        assert result["identifier"] == "3"

    @patch("core.guacamolelib.requests.post")
    def test_invalid_type_raises_value_error(self, mock_post):
        """Should raise ValueError for invalid group type."""
        client = _create_client(mock_post)

        with pytest.raises(ValueError, match="Invalid option"):
            client.create_connection_group(
                group_name="Bad Group",
                group_type="INVALID",
            )


class TestUpdateConnectionPermissions:
    """Tests for session.update_connection_permissions."""

    @patch("core.guacamolelib.requests.patch")
    @patch("core.guacamolelib.requests.post")
    def test_add_connection_permission(self, mock_post, mock_patch):
        """Should add connection permission for user."""
        client = _create_client(mock_post)

        mock_patch.return_value = _mock_response("{}")

        result = client.update_connection_permissions(
            username="testuser",
            identifiers=["123"],
            operation="add",
            permission="connection",
        )
        assert result == {}
        mock_patch.assert_called_once()

    @patch("core.guacamolelib.requests.patch")
    @patch("core.guacamolelib.requests.post")
    def test_invalid_operation_raises(self, mock_post, mock_patch):
        """Should raise ValueError for invalid operation."""
        client = _create_client(mock_post)

        with pytest.raises(ValueError, match="Invalid operation"):
            client.update_connection_permissions(
                username="testuser",
                identifiers=["123"],
                operation="invalid",
            )

    @patch("core.guacamolelib.requests.patch")
    @patch("core.guacamolelib.requests.post")
    def test_invalid_permission_type_raises(self, mock_post, mock_patch):
        """Should raise ValueError for invalid permission type."""
        client = _create_client(mock_post)

        with pytest.raises(ValueError, match="Invalid permission type"):
            client.update_connection_permissions(
                username="testuser",
                identifiers=["123"],
                operation="add",
                permission="invalid_type",
            )

    @patch("core.guacamolelib.requests.patch")
    @patch("core.guacamolelib.requests.post")
    def test_string_identifier_converted_to_list(self, mock_post, mock_patch):
        """Should handle single string identifier by converting to list."""
        client = _create_client(mock_post)

        mock_patch.return_value = _mock_response("{}")

        result = client.update_connection_permissions(
            username="testuser",
            identifiers="123",
            operation="add",
            permission="connection",
        )
        assert result == {}

        # Check that the JSON body contains a list of permissions
        sent_json = mock_patch.call_args.kwargs.get(
            "json"
        ) or mock_patch.call_args[1].get("json")
        assert isinstance(sent_json, list)
        assert len(sent_json) == 1
        assert sent_json[0]["path"].endswith("123")


class TestDetailConnection:
    """Tests for session.detail_connection."""

    @patch("core.guacamolelib.requests.get")
    @patch("core.guacamolelib.requests.post")
    def test_without_option(self, mock_post, mock_get):
        """Should return connection details without option."""
        client = _create_client(mock_post)

        conn_data = {
            "identifier": "123",
            "name": "test",
            "protocol": "rdp",
        }
        mock_get.return_value = _mock_response(json.dumps(conn_data))

        result = client.detail_connection("123")
        assert result["identifier"] == "123"

    @patch("core.guacamolelib.requests.get")
    @patch("core.guacamolelib.requests.post")
    def test_with_parameters_option(self, mock_post, mock_get):
        """Should fetch connection parameters."""
        client = _create_client(mock_post)

        params_data = {"hostname": "10.0.0.1", "port": "3389"}
        mock_get.return_value = _mock_response(json.dumps(params_data))

        result = client.detail_connection("123", option="parameters")
        assert result["hostname"] == "10.0.0.1"

        call_url = mock_get.call_args[0][0]
        assert "/connections/123/parameters" in call_url

    @patch("core.guacamolelib.requests.get")
    @patch("core.guacamolelib.requests.post")
    def test_invalid_option_raises(self, mock_post, mock_get):
        """Should raise ValueError for invalid option."""
        client = _create_client(mock_post)

        with pytest.raises(ValueError, match="Invalid option"):
            client.detail_connection("123", option="invalid")
