import time

from proxmoxer.core import ResourceException

from core.config import Settings

from .cluster import ProxmoxCluster
from .pve_node_info import proxmox_node_info_periodic

settings = Settings()


class TaskException(Exception):
    pass


def pve_task_get(pve_task_upid: str):
    # Extract node name from pve_task_upid
    task_upid_parts = pve_task_upid.split(":")
    task_node_name = task_upid_parts[1] if len(task_upid_parts) > 2 else None
    PVE_TASK = None
    pve_task_response = None
    while PVE_TASK is None:
        try:
            pve_task_response = (
                ProxmoxCluster()
                .proxmox.nodes(task_node_name)
                .tasks(pve_task_upid)
                .status.get()
            )
        except:
            time.sleep(5)  # Restart loop after sleeping for 5s
        # Check that response contains valid dictionary object
        if pve_task_response and type(pve_task_response) == dict:
            PVE_TASK = pve_task_response
        else:
            time.sleep(5)  # Restart loop after sleeping for 5s

    return PVE_TASK


async def kvs_await_pve_task_exit(pve_task_upid: str) -> bool:
    """
    :param pve_vm_id: proxmoxId of VirtualMachine on Proxmox
    :param pve_task_upid: String containing the UPID of the task on Proxmox
    This function is used by the RQ Worker to await the exit status of a Proxmox task. On success, the function returns True.
    """
    time.sleep(
        1
    )  # Waits 1 second before executing to allow PVE time to start the task (Helps prevent 501 ResourceException)
    TASK_SUCCESS = False
    while not TASK_SUCCESS:
        # Get status of task from PVE
        task = pve_task_get(pve_task_upid)
        # Check if task is still running
        if "status" in task and task["status"] != "stopped":
            time.sleep(
                settings.pve_api_poll_rate
            )  # Restart loop after sleeping for duration set in .env (in seconds)
        elif "exitstatus" in task and task["exitstatus"] == "OK":
            TASK_SUCCESS = True
        elif "exitstatus" in task and task["exitstatus"] != "OK":
            return False
        elif "exitstatus" not in task:
            time.sleep(
                settings.pve_api_poll_rate
            )  # Restart loop after sleeping for duration set in .env (in seconds)

    # Run proxmox_node_info_periodic function to insure VirtualMachine DB values are up-to-date with PVE
    try:
        await proxmox_node_info_periodic()
        return True
    except:
        return True


# Convert Proxmox exception into user-friendly response
def format_pve_exception_for_user(
    exc: Exception, prefix: str = "PVE operation failed"
) -> tuple[int, str]:
    # Real PVE ResourceException
    if isinstance(exc, ResourceException):
        status = getattr(exc, "status_code", 503)
        msg = str(getattr(exc, "message", str(exc)))

        # Translate well-known PVE errors into clearer messages
        if "QEMU guest agent is not running" in msg:
            return 503, (
                f"{prefix}: QEMU guest agent is not (yet) available."
                " The job will be retried automatically."
            )

        user_msg = f"{prefix}. Status: {status}. Message: {msg}"

        pve_detail = getattr(exc, "response", None)
        if pve_detail:
            user_msg += f". PVE Details: {pve_detail}"

        return status, user_msg

    # Generic non-PVE errors
    return 500, f"{prefix}: {exc!s}"
