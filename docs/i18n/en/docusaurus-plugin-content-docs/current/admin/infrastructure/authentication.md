---
id: authentication
sidebar_label: Authentication
sidebar_position: 40
status: finished
tags:
  - infrastructure
  - authentication
---

# Authentication {#authentication}

OpenVLE supports three authentication methods: local login, LDAP, and OpenID Connect (OIDC). All methods can be active simultaneously — users choose the desired method at login.

:::info Authentication vs. authorization
Authentication determines **who** a user is (identity verification). Authorization determines **what** a user is allowed to do (access control). Authorization is handled by the [permission system](permission-system) — it operates independently of the chosen authentication method.
:::

## Overview {#overview}

| Method    | Activation            | Requirements                                   | Description                                              |
| --------- | --------------------- | ---------------------------------------------- | -------------------------------------------------------- |
| **Local** | Always active         | None                                           | Username and password are stored in the OpenVLE database |
| **LDAP**  | `LDAP_ENABLED = True` | LDAP server (e.g., Active Directory, OpenLDAP) | Login with existing directory service credentials        |
| **OIDC**  | `OIDC_ENABLED = True` | OIDC provider (e.g., Keycloak, Azure AD)       | Single sign-on via an external identity provider         |

## Token-based sessions {#token-sessions}

Regardless of the chosen authentication method, every user receives a JWT (JSON Web Token) from the backend after successful login. This token is used for all subsequent API requests:

- **Access Token** — Short-lived token for API access (expiration: `AUTH_ACCESS_TOKE_EXPIRE_MINUTES`, default: 480 minutes)

The tokens are signed with the `AUTH_SECRET` (algorithm: HS256). Changing the `AUTH_SECRET` immediately logs out all active users.

## Local authentication {#local-auth}

Local authentication is the default method and always available. Users log in with a username and password stored in the MariaDB database. Local user accounts are created manually in the user interface or via the API.

## LDAP {#ldap}

When LDAP is enabled, users can log in with their existing directory service credentials (e.g., Active Directory, OpenLDAP). OpenVLE verifies the credentials against the configured LDAP server without storing a local password.

### Flow {#ldap-flow}

1. User enters LDAP credentials on the login page
2. The backend searches for the user in the LDAP directory (based on `LDAP_DN_PEOPLE` and `LDAP_ATTR_USER`)
3. The backend performs an LDAP bind with the entered credentials
4. On success, a local session is created (JWT token)

### Auto-enrollment {#ldap-enrollment}

LDAP users are automatically created in the OpenVLE database on their first successful login. Username and email address are taken from the LDAP attributes (`LDAP_ATTR_USER`, `LDAP_ATTR_MAIL`).

### Requirements {#ldap-requirements}

- An LDAP server must be reachable from the OpenVLE backend (default ports: 389 for LDAP, 636 for LDAPS)
- The LDAP directory must contain the users under the configured DN (`LDAP_DN_PEOPLE`)

## OIDC (OpenID Connect) {#oidc}

OIDC enables single sign-on (SSO) via an external identity provider. Users are redirected to the provider's login page and returned to OpenVLE after successful authentication.

### Flow {#oidc-flow}

1. User clicks "Sign in with SSO" on the login page
2. OpenVLE redirects the user to the OIDC provider
3. The user authenticates with the provider (e.g., Keycloak, Azure AD)
4. The provider redirects the user back to OpenVLE with an authorization code
5. The backend exchanges the code for user information and creates a local session

### Auto-enrollment {#oidc-enrollment}

If `OIDC_ENROLL_USERS = True` (default), users are automatically registered in OpenVLE on their first SSO login. Username, name, and email are taken from the OIDC attributes (`OIDC_ATTR_USERNAME`, `OIDC_ATTR_NAME`, `OIDC_ATTR_EMAIL`).

When auto-enrollment is disabled (`OIDC_ENROLL_USERS = False`), the user must have been previously created manually in OpenVLE.

### Data synchronization {#oidc-sync}

On every OIDC login, the user's name and email address are updated with the current values from the identity provider. This keeps user data in OpenVLE automatically in sync with the IdP — regardless of whether the user was created via auto-enrollment or manually.

### Requirements {#oidc-requirements}

- An OIDC provider must be configured and reachable from the backend
- A client with `OIDC_CLIENT_ID` and `OIDC_CLIENT_SECRET` must be registered with the provider
- The redirect URL to OpenVLE must be registered as an allowed redirect URL with the provider

## User management and provisioning {#user-provisioning}

LDAP and OIDC serve exclusively for **authentication** and **on-the-fly provisioning** at login. There is no automatic background synchronization of users — OpenVLE does not fetch user lists from LDAP or the OIDC provider.

To assign a user to OpenVLE objects (e.g., as a participant in an event), the user must be known to OpenVLE. This means:

- The user has **logged in at least once** (at which point they are automatically created), or
- The user was **created manually** — via CSV import in the frontend or via the API

:::note Planned enhancements

- **SCIM integration** (provider and client) — A full SCIM integration is planned for the near future, enabling automatic provisioning and synchronization of users with external identity management systems.
- **Periodic LDAP sync** — On customer request, a periodic LDAP sync can be provided that automatically synchronizes users in the background.
  :::

## Note on Apache Guacamole {#guacamole-auth}

If [Apache Guacamole](guacamole) is used for remote desktop access, Guacamole should ideally be connected to the same identity provider (LDAP or OIDC) as OpenVLE. OpenVLE provisions Guacamole connections for the same usernames as in OpenVLE — user management in Guacamole is not necessary, as OpenVLE automatically creates missing users there. Therefore, only authentication needs to be configured in Guacamole. For more details, see [Apache Guacamole — User authentication](guacamole#guacamole-auth).

## Note on Moodle {#moodle-auth}

If [Moodle](moodle) is connected, Moodle should ideally be connected to the same identity provider (LDAP or OIDC) as OpenVLE. OpenVLE provisions Moodle users for the same usernames as in OpenVLE — user management in Moodle is not necessary, as OpenVLE automatically creates missing users there. Therefore, only authentication needs to be configured in Moodle. For more details, see [Moodle — User synchronization](moodle#user-sync).

## Further reading {#further-reading}

- [Configuration reference — Authentication](../install/configuration#auth) — General auth variables
- [Configuration reference — LDAP](../install/configuration#ldap) — LDAP environment variables
- [Configuration reference — OIDC](../install/configuration#oidc) — OIDC environment variables
- [Permission system](permission-system) — Authorization and access control
