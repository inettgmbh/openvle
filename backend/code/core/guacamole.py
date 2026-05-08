import re

from pydantic import UUID4

from controllers.base import CRUDBase
from controllers.sub_tasks import CRUDSubTask
from core.core_utils import db_save, vm_ip_in_subnet
from core.mariadb import SessionLocal
from middlewares.i18n import _
from models import (
    Changelog,
    Event,
    Guacamole as GuacamoleModel,
    GuacamoleConnectionProfile,
    ObjectPermission,
    SubTask,
    VirtualMachine,
)
from pve.cluster import ProxmoxCluster

from . import guacamolelib
from .config import Settings
from .exceptions import GuacamoleConnectionError, GuacamoleRequestError

settings = Settings()


# Connect to Guacamole API
def guacamole_connect():
    try:
        return guacamolelib.session(
            settings.guacamole_url,
            settings.guacamole_db,
            settings.guacamole_user,
            settings.guacamole_password,
        )
    except Exception as e:
        return False  # str(e)


# Check if user already exists in guacamole
def check_user_exists(guacamole: str, username: str):
    try:
        response = guacamole.detail_user(username)
        if "username" in response and response["username"] == username:
            return True
        return "Guacamole Error (4): " + response["message"]
    except Exception as e:
        return "Guacamole Error (4): " + str(e)


# Check if user exists and create if not
def check_create_user(guacamole: str, username: str):
    try:
        response = guacamole.detail_user(username)
        if "username" in response and response["username"] == username:
            return True
        response = None
        response = guacamole.create_user(username, password=None)
        if "username" in response and response["username"] == username:
            return True
        return "Guacamole Error (0): " + response["message"]
    except Exception as e:
        return f"Guacamole Error (0): {e!s}"


# Create user in guacamole
def create_user(guacamole: str, username: str):
    try:
        response = guacamole.create_user(username, password=None)
        if "username" in response and response["username"] == username:
            return True
        return "Guacamole Error (5): " + response["message"]
    except Exception as e:
        return "Guacamole Error (5): " + str(e)


def get_or_create_connection_group(
    guacamole: str, connection_groups: dict, name: str, group_parent: str = None
):
    parent_identifier = next(
        (k for k, v in connection_groups.items() if v.get("name") == name), None
    )
    if not parent_identifier:
        new_connection_group = guacamole.create_connection_group(
            group_name=name, parent_identifier=group_parent
        )
        parent_identifier = new_connection_group["identifier"]
    return parent_identifier


def create_user_connection_group_permission(
    guacamole: str, username: str, group_identifier: int | str
):
    try:
        resp = guacamole.update_connection_permissions(
            username=username,
            identifiers=[group_identifier],
            operation="add",
            permission="group",
        )
        if isinstance(resp, dict) and "message" in resp:
            return "Guacamole Error (11G): " + resp["message"]
        return True
    except Exception as e:
        return "Guacamole Error (11G): " + str(e)


# Create vm connection in guacamole
def create_connection(
    guacamole: str,
    name: str,
    connection_hostname: str,
    connection_username: str,
    connection_password: str,
    guacd_hostname: str = "",
    guacd_port: int = None,
    guacd_encryption: bool = None,
    connection_port: int = 3389,
    connection_protocol: str = "rdp",
    event_slug: str = None,
    username: str | None = None,
):
    try:
        parent_identifier = "ROOT"
        parent_group_ids: list[str] = []
        connection_groups = guacamole.list_connection_groups()
        if not isinstance(connection_groups, dict):
            return (
                "Guacamole Error (10): "
                "unexpected response from list_connection_groups: "
                + str(connection_groups)
            )
        if settings.guacamole_connections_prefix:
            base_gid = get_or_create_connection_group(
                guacamole=guacamole,
                connection_groups=connection_groups,
                name=settings.guacamole_connections_prefix,
                group_parent="ROOT",
            )
            parent_identifier = base_gid
            parent_group_ids.append(base_gid)
        if settings.guacamole_connections_prefix_events and event_slug:
            event_gid = get_or_create_connection_group(
                guacamole=guacamole,
                connection_groups=connection_groups,
                name=event_slug,
                group_parent=parent_identifier,
            )
            parent_identifier = event_gid
            parent_group_ids.append(event_gid)

        if username:
            for gid in parent_group_ids:
                perm_resp = create_user_connection_group_permission(
                    guacamole=guacamole,
                    username=username,
                    group_identifier=gid,
                )
                if isinstance(perm_resp, str) and perm_resp.startswith(
                    "Guacamole Error"
                ):
                    return perm_resp
    except Exception as e:
        return "Guacamole Error (10): " + str(e)
    try:
        # Build protocol-specific parameters from settings
        if connection_protocol == "rdp":
            parameters = {
                "hostname": connection_hostname,
                "port": connection_port,
                "username": connection_username,
                "password": connection_password,
                "timezone": settings.guacamole_conn_timezone,
                "security": settings.guacamole_rdp_security,
                "ignore-cert": settings.guacamole_rdp_ignore_cert,
                "server-layout": settings.guacamole_rdp_server_layout,
                "resize-method": settings.guacamole_rdp_resize_method,
                "enable-audio-input": settings.guacamole_rdp_enable_audio_input,
                "enable-printing": settings.guacamole_rdp_enable_printing,
                "printer-name": settings.guacamole_rdp_printer_name,
                "enable-drive": settings.guacamole_rdp_enable_drive,
                "enable-wallpaper": settings.guacamole_rdp_enable_wallpaper,
                "enable-theming": settings.guacamole_rdp_enable_theming,
                "enable-font-smoothing": settings.guacamole_rdp_enable_font_smoothing,
                "enable-full-window-drag": settings.guacamole_rdp_enable_full_window_drag,
                "enable-desktop-composition": settings.guacamole_rdp_enable_desktop_composition,
                "enable-menu-animations": settings.guacamole_rdp_enable_menu_animations,
                "disable-bitmap-caching": settings.guacamole_rdp_disable_bitmap_caching,
                "disable-offscreen-caching": settings.guacamole_rdp_disable_offscreen_caching,
                "disable-glyph-caching": settings.guacamole_rdp_disable_gfx,
                "disable-download": settings.guacamole_rdp_disable_download,
                "disable-upload": settings.guacamole_rdp_disable_upload,
                "sftp-server-alive-interval": settings.guacamole_sftp_server_alive_interval,
            }
            if settings.guacamole_rdp_color_depth is not None:
                parameters["color-depth"] = settings.guacamole_rdp_color_depth
        elif connection_protocol == "vnc":
            parameters = {
                "hostname": connection_hostname,
                "port": connection_port,
                "username": connection_username,
                "password": connection_password,
                "color-depth": settings.guacamole_vnc_color_depth,
                "sftp-server-alive-interval": settings.guacamole_sftp_server_alive_interval,
            }
        elif connection_protocol == "ssh":
            parameters = {
                "hostname": connection_hostname,
                "port": connection_port,
                "username": connection_username,
                "password": connection_password,
                "server-alive-interval": settings.guacamole_ssh_server_alive_interval,
            }
        else:
            # telnet, kubernetes
            parameters = {
                "hostname": connection_hostname,
                "port": connection_port,
                "username": connection_username,
                "password": connection_password,
            }
        response = guacamole.manage_connection(
            protocol=connection_protocol,
            parent_identifier=parent_identifier,
            name=name,
            attributes={
                "guacd-hostname": guacd_hostname,
                "guacd-port": guacd_port,
                "guacd-encryption": guacd_encryption,
            },
            parameters=parameters,
        )
        # Response Handling
        if "message" not in response:
            return response["identifier"]
        return "Guacamole Error (10): " + response["message"]
    except Exception as e:
        return "Guacamole Error (10): " + str(e)


# Create user connection permission
def create_user_connection(guacamole: str, username: str, identifier: int):
    try:
        # Add user permission on connection
        response = guacamole.update_connection_permissions(
            username=username,
            identifiers=identifier,
            operation="add",
            permission="connection",
        )
        # Response Handling
        if "message" not in response:
            return True
        return "Guacamole Error (11): " + response["message"]
    except Exception as e:
        return "Guacamole Error (11): " + str(e)


# Create default sharing profiles
def create_default_sharing_profiles(guacamole: str, identifier: int):
    try:
        # Add user permission on connection
        response = guacamole.create_sharing_profile(
            primary_identifier=str(identifier),
            name="Ansehen",
            parameters={"read-only": True},
        )
        # Response Handling
        if "message" in response:
            return "Guacamole Error (77): " + response["message"]
        # Save identifier for return
        identifiers = [response["identifier"]]
        response = None
        response = guacamole.create_sharing_profile(
            primary_identifier=str(identifier),
            name="Vollzugriff",
            parameters={"read-only": False},
        )
        # Response Handling
        if "message" in response:
            return "Guacamole Error (77): " + response["message"]
        # Add identifier for return
        identifiers += [response["identifier"]]
        return identifiers
    except Exception as e:
        return "Guacamole Error (77): " + str(e)


# Create user sharing profile permissions
def create_user_sharing_profiles_permissions(
    guacamole: str, username: str, identifier: int | list
):
    try:
        # Add user permission on sharing profile(s)
        response = guacamole.update_connection_permissions(
            username=username,
            identifiers=identifier,
            operation="add",
            permission="sharing profile",
        )
        # Response Handling
        if "message" not in response:
            return True
        return "Guacamole Error (66): " + response["message"]
    except Exception as e:
        return "Guacamole Error (66): " + str(e)


# Delete vm connection from guacamole
def delete_connection(guacamole: str, identifier: int):
    try:
        response = guacamole.delete_connection(identifier)
        # Response Handling
        if "message" not in response:
            return True
        return "Guacamole Error (30): " + response["message"]
    except Exception as e:
        return "Guacamole Error (30); " + str(e)


# Delete user connection permission
def delete_user_connection(guacamole: str, username: str, identifier: int):
    try:
        response = guacamole.update_user_connection(
            username=username,
            connectionid=identifier,
            operation="remove",
            isgroup=False,
        )
        # Response Handling
        if "message" not in response:
            return True
        return "Guacamole Error (40): " + response["message"]
    except Exception as e:
        return "Guacamole Error (40): " + str(e)


# Delete user account from guacamole
def delete_user(guacamole: str, username: str):
    try:
        response = guacamole.delete_user(username=username)
        # Response Handling
        if "message" not in response:
            return True
        return "Guacamole Error (45): " + response["message"]
    except Exception as e:
        return "Guacamole Error (45): " + str(e)


# Update user account status in guacamole
def update_user_status(guacamole: str, username: str, disabled: bool):
    try:
        response = guacamole.update_user(
            username=username, attributes={"disabled": disabled}
        )
        # Response Handling
        if "message" not in response:
            return True
        return "Guacamole Error (47): " + response["message"]
    except Exception as e:
        return "Guacamole Error (47): " + str(e)


# Update user account in guacamole
def update_user(guacamole: str, username: str, attributes):
    attributes = {
        "guac-email-address": attributes.get("guac-email-address", None),
        "guac-full-name": attributes.get("guac-full-name", None),
        "access-window-start": attributes.get("access-window-start", ""),
        "access-window-end": attributes.get("access-window-end", ""),
        "valid-until": attributes.get("valid-until", ""),
        "valid-from": attributes.get("valid-from", ""),
    }
    try:
        response = guacamole.update_user(
            username=username, attributes=attributes
        )
        # Response Handling
        if "message" not in response:
            return True
        return "Guacamole Error (48): " + response["message"]
    except Exception as e:
        return "Guacamole Error (48): " + str(e)


# Update connection in guacamole
def update_connection(
    guacamole: str,
    identifier: int,
    name: str,
    connection_hostname: str,
    connection_username: str,
    connection_password: str,
    guacd_hostname: str = "",
    guacd_port: int = None,
    guacd_encryption: bool = None,
    connection_port: int = 3389,
    connection_protocol: str = "rdp",
):
    try:
        # Fetch existing connection to preserve all params and attributes
        detail = guacamole.detail_connection(identifier)
        if not isinstance(detail, dict):
            return "Guacamole Error (50): Failed to fetch connection detail"

        protocol = detail.get("protocol", connection_protocol)
        parent_identifier = detail.get("parentIdentifier", "ROOT")
        conn_name = detail.get("name", name) or name
        attributes = detail.get("attributes", {}) or {}

        # Overlay guacd attributes only when explicitly provided
        if guacd_hostname:
            attributes["guacd-hostname"] = guacd_hostname
        if guacd_port is not None:
            attributes["guacd-port"] = guacd_port
        if guacd_encryption is not None:
            attributes["guacd-encryption"] = guacd_encryption

        # Fetch full existing parameters to avoid wiping unrelated fields
        params_detail = guacamole.detail_connection(identifier, "parameters")
        parameters = params_detail if isinstance(params_detail, dict) else {}

        # Overlay only the fields being explicitly updated
        parameters["hostname"] = connection_hostname
        parameters["username"] = connection_username
        parameters["password"] = connection_password
        parameters["port"] = connection_port

        response = guacamole.manage_connection(
            identifier=identifier,
            protocol=protocol,
            name=conn_name,
            parent_identifier=parent_identifier,
            attributes=attributes,
            parameters=parameters,
        )
        # Response Handling
        if "message" not in response:
            return True
        return "Guacamole Error (50): " + response["message"]
    except Exception as e:
        return "Guacamole Error (50): " + str(e)


# Handle deletion of connection - Synchronous
def guacamole_delete(identifier):
    """
    This function is used in part of CRUDGuacamole.delete() to handle the deletion of the Guacamole connection.
    The deletion of the Guacamole database object (and associated Changelogs and ObjectPermissions) is handled in the above mention CRUD function.
    """
    # Initiate guacamole session
    guacamole = guacamole_connect()
    if not guacamole:
        return "Guacamole Error (888): Connection failed"
    # Delete connection from guacamole
    return delete_connection(guacamole, identifier)


# Handle deletion of connection - Asynchronous
def guacamole_delete_worker(kvs_guacamole_id: UUID4, kvs_task_object_id: UUID4):
    """
    Handles the deletion of Guacamole connection as well as the Guacamole database object (including associated Changelogs and ObjectPermissions)
    """
    # Step 1: Initiate guacamole and DB sessions
    try:
        db = SessionLocal()
        guacamole = guacamole_connect()
        if not guacamole:
            db.close()
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id,
                502,
                "Failed to initialize Guacamole connection",
            )
    except:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id, 502, "Failed to initialize Guacamole connection"
        )

    # Get and update Task object
    CRUDSubTask(SubTask).worker_process_start(db, kvs_task_object_id)

    # Step 2: Get Guacamole object from DB and delete connection on Guacamole
    try:
        kvs_guacamole = db.get(GuacamoleModel, kvs_guacamole_id)
        if not kvs_guacamole:
            # If Guacamole does not exist in KVS, try delete from Guacamole
            db.close()
            return CRUDSubTask(SubTask).worker_process_success(
                kvs_task_object_id,
                200,
                "Guacamole connection and database object has been successfully deleted!",
            )
        delete_connection(guacamole, kvs_guacamole.identifier)
    except Exception as e:
        db.close()
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            400,
            f"The following error occurred while deleting Guacamole connection: {e} ",
        )

    # Step 3: delete Guacamole object and related objects from DB
    try:
        db.delete(kvs_guacamole)
        # Delete associated Changelogs and ObjectPermissions
        changelogs = db.query(Changelog).filter(
            Changelog.objectId == kvs_guacamole_id,
            Changelog.object == "Guacamole",
        )
        for changelog in changelogs:
            db.delete(changelog)
        object_permissions = db.query(ObjectPermission).filter(
            ObjectPermission.object_id == kvs_guacamole_id,
            ObjectPermission.object_type == "Guacamole",
        )
        for perm in object_permissions:
            db.delete(perm)
        db.commit()
        db.close()
        return CRUDSubTask(SubTask).worker_process_success(
            kvs_task_object_id,
            200,
            "Guacamole connection and database object has been successfully deleted!",
        )
    except Exception as e:
        db.close()
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            400,
            f"The Guacamole connection was successfully deleted but the following error occurred while deleting Guacamole object: {e} ",
        )


# Provision Guacamole - Synchronous
def provision_guacamole(
    username,
    connection_name,
    connection_hostname,
    connection_port,
    connection_username,
    connection_password,
    connection_protocol,
    event_slug: str = None,
):
    """
    Complete provisioning of a new guacamole object - Synchronous
    Handles user check/creation, creation of connection, sharing profiles and permissions
    """
    # Step 1: Initiate guacamole session
    try:
        guacamole = guacamole_connect()
        if not guacamole:
            return "Guacamole Error (999): Connection failed"
    except:
        raise GuacamoleConnectionError()

    # Step 2: Check if user is provided inside of guacamole
    try:
        user_create_response = check_create_user(guacamole, username)
        if not user_create_response:
            return user_create_response
    except:
        raise GuacamoleRequestError(message=_("Error creating Guacamole User"))

    # Step 3: Create new connection in Guacamole
    try:
        connection_create_response = create_connection(
            guacamole=guacamole,
            name=connection_name,
            connection_hostname=connection_hostname,
            connection_port=connection_port,
            connection_username=connection_username,
            connection_password=connection_password,
            connection_protocol=connection_protocol,
            event_slug=event_slug,
            username=username,
        )
        # Check if connection is created successfully
        if connection_create_response.startswith("Guacamole Error"):
            raise GuacamoleRequestError(message=connection_create_response)
        else:
            connection_identifier = connection_create_response

    except:
        raise GuacamoleRequestError(message=connection_create_response)

    # Step 4: Grant user access to connection
    try:
        user_connection_response = create_user_connection(
            guacamole=guacamole,
            username=username,
            identifier=connection_identifier,
        )
        if not user_connection_response:
            return user_connection_response
    except:
        guacamole_delete(connection_identifier)
        raise GuacamoleRequestError(
            message=_("Unable to grant user access to Guacamole connection")
        )

    # Step 5: Create default sharing profiles for connection
    try:
        sharing_profile_response = create_default_sharing_profiles(
            guacamole=guacamole, identifier=connection_identifier
        )
        if type(sharing_profile_response) != list:
            return sharing_profile_response

        sharing_profiles_identifier = sharing_profile_response
    except:
        guacamole_delete(connection_identifier)
        raise GuacamoleRequestError(
            message=_(
                "Error creating default sharing profiles for Guacamole connection"
            )
        )

    # Step 6: Grant user access to sharing profiles
    try:
        sharing_profile_permissions_response = (
            create_user_sharing_profiles_permissions(
                guacamole=guacamole,
                username=username,
                identifier=sharing_profiles_identifier,
            )
        )
        if not sharing_profile_permissions_response:
            return sharing_profile_permissions_response

        return int(connection_identifier)
    except:
        guacamole_delete(connection_identifier)
        raise GuacamoleRequestError(
            message=_(
                "Unable to grant user access to sharing profiles for Guacamole connection"
            )
        )


# Provision Guacamole - Asynchronous
def provision_guacamole_worker(
    username: str,
    connection_name: str,
    kvs_gcp_id: UUID4,
    kvs_task_object_id: UUID4,
    kvs_guacamole_id: UUID4,
    kvs_vm_id: UUID4,
    connection_hostname: str = None,
):
    """
    Complete provisioning of a new guacamole object - Asynchronous
    Handles user check/creation, creation of connection, sharing profiles and permissions
    """
    # Step 1: Initiate guacamole and DB sessions
    try:
        db = SessionLocal()
        # Start worker process before external connection is attempted
        CRUDSubTask(SubTask).worker_process_start(db, kvs_task_object_id)
        guacamole = guacamole_connect()
        # Get GuacamoleConnectionProfile
        connection_profile = CRUDBase(GuacamoleConnectionProfile).get(
            db, kvs_gcp_id
        )
        if not guacamole:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id,
                502,
                "Failed to initialize Guacamole connection",
                db,
            )
    except:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id, 502, "Failed to initialize Guacamole connection"
        )

    # Step 2: Check if user is provided inside of guacamole
    try:
        user_create_response = check_create_user(guacamole, username)
        if not user_create_response:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id, 400, "Error creating Guacamole User", db
            )
    except:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id, 400, "Error creating Guacamole User", db
        )

    # Step 3: Create new connection in Guacamole
    connection_create_response = None
    try:
        kvs_vm = db.get(VirtualMachine, kvs_vm_id)
        if not kvs_vm:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id,
                400,
                "Error retrieving VirtualMachine object from database.",
                db,
            )
        event_slug = None
        if kvs_vm.event:
            event_slug = db.get(Event, kvs_vm.event).slug
        if not connection_hostname or connection_hostname == "0.0.0.0":
            if not kvs_vm.ipv4 or kvs_vm.ipv4 == "0.0.0.0":
                # If the VirtualMachine does not have a valid ipv4, attempt to retrieve it from PVE
                try:
                    proxmox = ProxmoxCluster().proxmox
                    vm_interfaces = proxmox(
                        f"/nodes/{ProxmoxCluster().pve_get_node(kvs_vm.proxmoxId)}/qemu/{kvs_vm.proxmoxId}/agent/network-get-interfaces"
                    ).get()["result"]
                    # Check if an IP from one of the Network Adapters is in the VirtualMachine subnet
                    VIRTUAL_MACHINE_ON_SUBNET = vm_ip_in_subnet(vm_interfaces)
                    if not VIRTUAL_MACHINE_ON_SUBNET:
                        return CRUDSubTask(SubTask).worker_process_fail(
                            kvs_task_object_id,
                            400,
                            "VirtualMachine does not have a valid IPv4 address with which to create a Guacamole connection.",
                            db,
                        )
                    elif kvs_vm.ipv4 != VIRTUAL_MACHINE_ON_SUBNET:
                        kvs_vm.ipv4 = VIRTUAL_MACHINE_ON_SUBNET
                        kvs_vm = db_save(db, kvs_vm)
                except:
                    return CRUDSubTask(SubTask).worker_process_fail(
                        kvs_task_object_id,
                        400,
                        "Unable to retrieve IPv4 address for VirtualMachine",
                        db,
                    )
            connection_hostname = kvs_vm.ipv4

        connection_name_new = re.sub(
            r"(?<=-)(PROV)(?=-)", str(kvs_vm.proxmoxId), connection_name
        )

        try:
            connection_create_response = create_connection(
                guacamole=guacamole,
                name=connection_name_new,
                connection_hostname=connection_hostname,
                connection_port=connection_profile.port,
                connection_username=connection_profile.username,
                connection_password=connection_profile.password,
                connection_protocol=connection_profile.protocol.lower(),
                event_slug=event_slug,
                username=username,
            )
        except Exception as e:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id,
                500,
                f"Exception creating Guacamole Connection: {e}",
                db,
            )

        # Validate connection response
        if not connection_create_response:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id,
                400,
                "Error creating Guacamole Connection",
                db,
            )
        if isinstance(
            connection_create_response, str
        ) and connection_create_response.startswith("Guacamole Error"):
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id, 400, connection_create_response, db
            )

        connection_identifier = connection_create_response

    except Exception as e:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            400,
            f"Unexpected error during connection creation: {e}",
            db,
        )

    # Step 4: Grant user access to connection
    try:
        user_connection_response = create_user_connection(
            guacamole=guacamole,
            username=username,
            identifier=connection_identifier,
        )
        if not user_connection_response:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id,
                400,
                "Unable to grant user access to Guacamole connection",
                db,
            )
    except:
        guacamole_delete(connection_identifier)
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            400,
            "Unable to grant user access to Guacamole connection",
            db,
        )

    # Step 5: Create default sharing profiles for connection
    try:
        sharing_profile_response = create_default_sharing_profiles(
            guacamole=guacamole, identifier=connection_identifier
        )
        if type(sharing_profile_response) != list:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id,
                400,
                "Error creating default sharing profiles for Guacamole connection",
                db,
            )
        sharing_profiles_identifier = sharing_profile_response
    except:
        guacamole_delete(connection_identifier)
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            400,
            "Error creating default sharing profiles for Guacamole connection",
            db,
        )

    # Step 6: Grant user access to sharing profiles
    try:
        sharing_profile_permissions_response = (
            create_user_sharing_profiles_permissions(
                guacamole=guacamole,
                username=username,
                identifier=sharing_profiles_identifier,
            )
        )
        if not sharing_profile_permissions_response:
            guacamole_delete(connection_identifier)
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id,
                400,
                "Unable to grant user access to sharing profiles for Guacamole connection",
                db,
            )
    except:
        guacamole_delete(connection_identifier)
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            400,
            "Unable to grant user access to sharing profiles for Guacamole connection",
            db,
        )

    # Step 7: Update Guacamole object with connection identifier
    try:
        guac_obj = db.get(GuacamoleModel, kvs_guacamole_id)
        if not guac_obj:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id,
                400,
                f"Guacamole object with ID: {kvs_guacamole_id} not found",
                db,
            )
        guac_obj.identifier = int(connection_identifier)
        guac_obj.name = connection_name_new
        db_save(db, guac_obj)
        return CRUDSubTask(SubTask).worker_process_success(
            kvs_task_object_id,
            200,
            "Guacamole connection has been successfully provisioned!",
            db,
        )

    except:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            400,
            f"Unable to update Guacamole object with the following connection identifier: {int(connection_identifier)}",
            db,
        )


def guacamole_hostname_update(
    identifier: str,
    connection_name: str,
    connection_hostname: str,
    connection_protocol: str,
):
    """
    Update only the hostname of an existing Guacamole connection.
    Uses the current connection details to avoid wiping fields.
    Returns the identifier on success, or 'Guacamole Error (11): ...' on failure.
    """
    try:
        guacamole = guacamole_connect()
        if not guacamole:
            return "Guacamole Error (11): Failed to create Guacamole session"
    except Exception as e:
        return "Guacamole Error (11): " + str(e)

    try:
        # Fetch existing connection details
        detail = guacamole.detail_connection(identifier)
        if not isinstance(detail, dict):
            return "Guacamole Error (11): Failed to fetch connection detail"

        protocol = detail.get("protocol", connection_protocol)
        parent_identifier = detail.get("parentIdentifier", "ROOT")
        name = detail.get("name", connection_name) or connection_name
        attributes = detail.get("attributes", {}) or {}

        # Fetch full parameters separately
        params_detail = guacamole.detail_connection(identifier, "parameters")
        parameters = params_detail if isinstance(params_detail, dict) else {}

        # Update ONLY the hostname
        parameters["hostname"] = connection_hostname

        # PUT the updated connection
        response = guacamole.manage_connection(
            protocol=protocol,
            parent_identifier=parent_identifier,
            name=name,
            identifier=identifier,
            parameters=parameters,
            attributes=attributes,
        )

        if isinstance(response, dict) and "message" in response:
            return "Guacamole Error (11): " + response["message"]

        return identifier

    except Exception as e:
        return "Guacamole Error (11): " + str(e)
