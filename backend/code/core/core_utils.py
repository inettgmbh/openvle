import difflib
import ipaddress
import json
import re

from fastapi import Request
from sqlalchemy.orm import Session

from core.config import Settings
from models import User

settings = Settings()
from core.mariadb import SessionLocal


# Generic save operation used to commit changes/additions to the MariaDB
def db_save(db: Session, db_object):
    try:
        db_object = db.merge(db_object)
        db.commit()
        db.refresh(db_object)
        return db_object
    except Exception as e:
        db.rollback()
        raise RuntimeError(
            f"The following error occurred while trying to save the object to the database:\n{e}"
        ) from e


# Determines if the provided list of Network Interfaces (provided by PVE API call) contains an interface within the configured subnet
def vm_ip_in_subnet(vm_network_interfaces: list):
    vm_subnet = ipaddress.ip_network(settings.pve_vm_subnet)

    for interface in vm_network_interfaces:
        if "ip-addresses" not in interface:
            continue
        for ip_address in interface["ip-addresses"]:
            if "ip-address" not in ip_address:
                continue
            if ipaddress.ip_address(ip_address["ip-address"]) in vm_subnet:
                return str(ip_address["ip-address"])

    return False


# Generate slug based on name
def convert_to_slug(
    name: str, split_char: str = "-", max_length: int = 100
) -> str:
    # Convert name into lower case before replacements
    slug = name.lower()
    # Replace invalid characters
    replacements = {"ä": "ae", "ü": "ue", "ö": "oe", "ß": "ss"}
    for char, replacement in replacements.items():
        slug = slug.replace(char, replacement)
    # Replace any remaining special characters with the split_char
    slug = re.sub(r"[^a-z0-9]+", split_char, slug)
    slug = slug.strip("-")
    # Check that slug is unique
    return slug[:max_length]


# Checks if a valid Request object was provided and returns the Request user ID. If not, return ID of System user
def request_user_validation(db: Session, request: Request = None):
    # If request is None, set request.user.id to system user
    if request and request.user.id:
        request_user_id = request.user.id
    else:
        system_user = db.query(User).filter(User.username == "system").first()
        request_user_id = system_user.id
    return request_user_id


# Converts given string into a valid dns-name (format required for name fields on Proxmox)
def sanitize_dns_name(name: str) -> str:
    # Replace invalid characters with a dash
    sanitized_name = re.sub(r"[^A-Za-z0-9.-]", "-", name)
    # Split the name into labels and process each label
    labels = sanitized_name.split(".")
    processed_labels = []
    for label in labels:
        label = label.strip("-")
        # Ensure the label is not empty and not longer than 63 characters
        if label:
            processed_labels.append(label[:63])
    sanitized_name = ".".join(processed_labels)
    # Ensure the total length of the DNS name does not exceed 253 characters
    return sanitized_name[:253]


_MAX_COLUMN_LEN = 1950  # safe margin below String(2000)
_DIFF_THRESHOLD = 300  # per-field value length that triggers diff mode
_DIFF_CONTEXT = 60  # surrounding chars kept on either side of a change


def _field_diff(old: str, new: str) -> tuple[str, str]:
    """Return compact (old_repr, new_repr) showing only what changed.

    For multi-line values uses a line-level unified diff; for single-line
    values uses a character-range approach centred on the changed region.
    """
    old_lines = old.splitlines()
    new_lines = new.splitlines()

    if len(old_lines) > 1 or len(new_lines) > 1:
        diff = list(difflib.unified_diff(old_lines, new_lines, n=1))
        removed = "\n".join(
            line[1:]
            for line in diff
            if line.startswith("-") and not line.startswith("---")
        )
        added = "\n".join(
            line[1:]
            for line in diff
            if line.startswith("+") and not line.startswith("+++")
        )
        return removed or old[:_DIFF_CONTEXT], added or new[:_DIFF_CONTEXT]

    # Single-line: find the changed character range
    sm = difflib.SequenceMatcher(None, old, new, autojunk=False)
    changes = [op for op in sm.get_opcodes() if op[0] != "equal"]
    if not changes:
        return old[:_DIFF_CONTEXT], new[:_DIFF_CONTEXT]

    o_lo = max(0, changes[0][1] - _DIFF_CONTEXT)
    o_hi = min(len(old), changes[-1][2] + _DIFF_CONTEXT)
    n_lo = max(0, changes[0][3] - _DIFF_CONTEXT)
    n_hi = min(len(new), changes[-1][4] + _DIFF_CONTEXT)

    old_repr = (
        ("…" if o_lo > 0 else "")
        + old[o_lo:o_hi]
        + ("…" if o_hi < len(old) else "")
    )
    new_repr = (
        ("…" if n_lo > 0 else "")
        + new[n_lo:n_hi]
        + ("…" if n_hi < len(new) else "")
    )
    return old_repr, new_repr


def prepare_changelog_values(
    values_old: dict, values_new: dict
) -> tuple[str, str]:
    """Build the (old_json, new_json) strings to store in the changelog.

    Fields whose value exceeds _DIFF_THRESHOLD chars are replaced with a
    compact diff showing only the changed portion, so both strings stay
    within the String(2000) column limit.
    """
    out_old: dict = {}
    out_new: dict = {}

    for field, new_val in values_new.items():
        old_v = "" if values_old.get(field) is None else str(values_old[field])
        new_v = "" if new_val is None else str(new_val)

        if len(old_v) <= _DIFF_THRESHOLD and len(new_v) <= _DIFF_THRESHOLD:
            out_old[field] = old_v
            out_new[field] = new_v
        else:
            old_repr, new_repr = _field_diff(old_v, new_v)
            out_old[field] = old_repr
            out_new[field] = new_repr

    def _to_json(data: dict) -> str:
        try:
            s = json.dumps(data, ensure_ascii=False)
        except Exception:
            s = str(data)
        if len(s) > _MAX_COLUMN_LEN:
            s = s[:_MAX_COLUMN_LEN] + "…[TRUNCATED]"
        return s

    return _to_json(out_old), _to_json(out_new)


def get_system_user(db: Session = None) -> User:
    if db:
        return db.query(User).filter(User.username == "system").first()
    else:
        db = SessionLocal()
        try:
            return db.query(User).filter(User.username == "system").first()
        finally:
            db.close()
