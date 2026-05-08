---
id: permission-system
sidebar_label: Permission System
sidebar_position: 45
status: finished
tags:
  - infrastructure
  - permissions
---

# Permission System {#permission-system}

The OpenVLE permission system controls which actions users are allowed to perform on which resources. It is based on an ObjectPermission model that supports both global and object-level permissions.

:::info Authentication vs. authorization
Authorization (what is a user allowed to do?) is controlled by the permission system described here. Authentication (who is the user?) is handled separately — see [Authentication](authentication).
:::

## Concept {#concept}

Every permission in OpenVLE is a combination of:

- **Object type** — The resource the permission applies to (e.g., `VirtualMachine`, `Event`, `User`, `Role`)
- **Object ID** — A specific instance (or empty for a global permission)
- **Permission key** — The allowed action (e.g., `object_read`, `object_update`, `object_full`)
- **Entity** — The user or role that receives the permission

## Permission keys {#permission-keys}

### Standard CRUD permissions {#crud-permissions}

The CRUD permissions follow a hierarchy — a higher permission automatically includes those below it:

| Key             | Grants                             | Description                      |
| --------------- | ---------------------------------- | -------------------------------- |
| `object_full`   | full, delete, update, read, create | Full access to the resource      |
| `object_delete` | delete, update, read               | Delete, edit, and read           |
| `object_update` | update, read                       | Edit and read                    |
| `object_read`   | read                               | Read only                        |
| `object_create` | create                             | Create new objects (global only) |

:::note Hierarchy example
If a user has `object_delete` on VMs, they can delete, edit, and read VMs — a separate `object_read` permission is not needed.
:::

### Special permissions {#special-permissions}

In addition to the standard CRUD permissions, there are special permissions for certain object types:

| Key                                                | Object type           | Description                            |
| -------------------------------------------------- | --------------------- | -------------------------------------- |
| `object_actions_start`, `object_actions_stop`, ... | VirtualMachine, Event | Individual actions (start, stop, etc.) |
| `object_set_password`                              | User                  | Change a user's password               |
| `object_search`                                    | User                  | Search users                           |
| `object_send`, `object_send_bulk`                  | Mail                  | Send emails                            |
| `object_reset`                                     | VirtualMachine        | Reset a VM                             |
| `object_templates_update`                          | Event                 | Update VM templates in events          |

## Global vs. object-level permissions {#scopes}

The system distinguishes two scopes:

| Scope            | Object ID           | Effect                                          |
| ---------------- | ------------------- | ----------------------------------------------- |
| **Global**       | empty               | Applies to **all** instances of the object type |
| **Object-level** | UUID of an instance | Applies only to the **specific** instance       |

**Example:** A user with global `object_read` on `VirtualMachine` can read all VMs. A user with object-level `object_read` on a specific VM ID can only read that one VM.

During permission checks, the system first looks for an object-level permission. If none is found, it falls back to the global permission.

:::note Global-only object types
Some object types support only global permissions (no object-level): Activity, Changelog, Dashboard, Language, Mail, ObjectPermission, Proxmox, SubTask, System, Tag, Task.
:::

## Roles {#roles}

Roles group permissions together and can be assigned to multiple users. Users inherit all permissions from their assigned roles.

- **Custom roles** — Can be freely created, edited, and deleted
- **System roles** — Predefined, protected roles that cannot be deleted

A user can have multiple roles. The effective permissions are the combination of all direct permissions and all role permissions.

## Permission check {#authorization-flow}

For every protected action, the backend checks the permission via the `PermissionChecker`:

1. **Load effective permissions** — All direct permissions of the user and all permissions from their roles are merged
2. **Resolve permission** — The requested permission key is checked against the effective permissions (including hierarchy)
3. **Result** — If the permission exists, the action is executed; otherwise, `403 Forbidden` is returned

## Frontend visibility {#frontend-visibility}

The frontend retrieves the logged-in user's effective permissions via the API. Based on these, actions and elements in the user interface are shown or hidden — buttons for creating, editing, or deleting are only displayed if the user has the corresponding permission.

## Data model {#data-model}

The permission system is based on the following database tables:

| Table                    | Description                                 |
| ------------------------ | ------------------------------------------- |
| `sys_users`              | User accounts                               |
| `sys_roles`              | Roles with name, key, and protection status |
| `sys_users_roles`        | Assignment of users to roles (n:m)          |
| `sys_object_permissions` | All permissions — for both users and roles  |

The `sys_object_permissions` table combines all permission assignments in a single structure:

| Field            | Description                                     |
| ---------------- | ----------------------------------------------- |
| `object_type`    | Resource type (e.g., `VirtualMachine`, `Event`) |
| `object_id`      | Specific instance (empty = global)              |
| `entity_id`      | User or role ID                                 |
| `entity_type`    | `User` or `Role`                                |
| `permission_key` | Permission key (e.g., `object_read`)            |
