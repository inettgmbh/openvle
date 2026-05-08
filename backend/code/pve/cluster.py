import requests
import urllib3
from proxmoxer import ProxmoxAPI
from sqlalchemy import select, union_all
from sqlalchemy.orm import Session

from core.config import Settings
from core.exceptions import ProxmoxConnectionError
from models import Template, VirtualMachine

settings = Settings()


# PVE cluster class
class ProxmoxCluster:
    """
    Calling the ProxmoxCluster() class initializes the ProxmoxAPI connection to the PVE cluster.
    """

    def __init__(
        self,
    ):
        try:
            if settings.pve_verify_ssl:
                self.proxmox = ProxmoxAPI(
                    settings.pve_hostname,
                    user=settings.pve_user,
                    token_name=settings.pve_token_name,
                    token_value=settings.pve_token_value,
                    verify_ssl=True,
                )
            else:
                urllib3.disable_warnings()
                self.proxmox = ProxmoxAPI(
                    settings.pve_hostname,
                    user=settings.pve_user,
                    token_name=settings.pve_token_name,
                    token_value=settings.pve_token_value,
                    verify_ssl=False,
                )
        except requests.exceptions.ConnectionError:
            raise ProxmoxConnectionError()

    # Returns the name of the node on which a VirtualMachine in running based on the provided vm_id
    def pve_get_node(self, vm_id: int):
        resource_list = self.proxmox.cluster.resources.get()
        for item in resource_list:
            try:
                if "vmid" not in item:
                    continue
                elif item["vmid"] == vm_id:
                    return item["node"]
            except:
                return False

    # Request next available vm_id from PVE
    def next_vm_id(self, db: Session) -> int | bool:
        try:
            # Fetch all reserved proxmoxIds from our DB (ignore NULLs)
            vm_q = select(VirtualMachine.proxmoxId).where(
                VirtualMachine.proxmoxId.isnot(None)
            )
            tpl_q = select(Template.proxmoxId).where(
                Template.proxmoxId.isnot(None)
            )
            rows = db.execute(union_all(vm_q, tpl_q)).all()
            reserved = {int(r[0]) for r in rows if r[0] is not None}

            # Start with Proxmox suggestion
            candidate = int(self.proxmox.cluster.nextid.get())

            MAX_STEPS = 10000
            steps = 0

            while steps < MAX_STEPS:
                steps += 1

                # Skip anything in use
                while candidate in reserved:
                    candidate += 1

                # Validate candidate is available
                try:
                    _ = self.proxmox.cluster.nextid.get(vmid=candidate)
                    # If no exception, VMID is available
                    return candidate
                except Exception:
                    # VMID already in use
                    candidate += 1
                    try:
                        px_next = int(self.proxmox.cluster.nextid.get())
                        candidate = max(candidate, px_next)
                    except requests.exceptions.ConnectionError:
                        raise ProxmoxConnectionError()
                    except Exception:
                        pass

            return False  # Timeout failure

        except Exception:
            return False

    # Returns the node with the most available CPU
    def get_free_node(self):
        resource_list = self.proxmox.cluster.resources.get()
        nodes_list = []
        for item in resource_list:
            try:
                if "cgroup-mode" in item and item["cgroup-mode"] == 2:
                    free_cpu = item["maxcpu"] - item["cpu"]
                    nodes_list.append(
                        {"node": item["node"], "free_cpu": free_cpu}
                    )
            except KeyError:
                continue
        best_node = max(nodes_list, key=lambda x: x["free_cpu"])
        return best_node["node"]
