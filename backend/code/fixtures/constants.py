import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum

# -- Deterministic seed for fixture UUIDs --
FIXTURE_SEED = "openvle-fixture-seed-2026"

# Marker tag key (stored in kvs_tags to track seeded profiles)
FIXTURE_MARKER_KEY = "_fixture_marker"

# -- Seeded system data UUIDs (from seed_data.sql) --

# Users
SYSTEM_USER_ID = uuid.UUID("1db3d8ac-22d9-4116-976a-93ad6e4fb234")
OPENVLE_USER_ID = uuid.UUID("71803f9c-b97b-4dd4-999f-f55084666d12")

# Roles
ROLE_ADMIN_FULL_ID = uuid.UUID("d8d8de51-0242-4453-bda4-cb53cc832dd3")
ROLE_ADMIN_READ_ONLY_ID = uuid.UUID("374568c9-feb7-4741-a74e-07ef8fe80050")
ROLE_LEHRENDE_ID = uuid.UUID("acec4438-2dec-41fb-9e5e-f0284845753e")
ROLE_STUDIERENDE_ID = uuid.UUID("cec850b3-608b-4cc3-aac2-4adc85df38e3")

# Event statuses
STATUS_GEPLANT_ID = uuid.UUID("53b6993a-57d6-40a6-8d42-e55bf08fac4c")
STATUS_AKTIV_ID = uuid.UUID("f481fb68-4e6b-4027-bf67-ae431bd8b6d1")
STATUS_ARCHIVIERT_ID = uuid.UUID("bfbee14d-6f04-4ba1-a39c-0f5764f0563d")
STATUS_INAKTIV_ID = uuid.UUID("cbc20092-629b-483f-babc-ef26202d685e")
STATUS_STOPPED_ID = uuid.UUID("1fc851bf-5f4e-4937-bae9-c6d3fd0e5846")

# Operating systems (subset used by fixture templates)
OS_DEBIAN_12_ID = uuid.UUID("bdda06a1-486c-491e-9d44-5d23189b08c3")
OS_UBUNTU_2204_ID = uuid.UUID("27d5e8ba-8205-4d6d-9934-d16c63265d75")
OS_WINDOWS_11_ID = uuid.UUID("f6843793-240e-42b0-ae45-8162952d4e5d")
OS_UBUNTU_2004_ID = uuid.UUID("8fae042b-81a9-44a3-9572-4b7a8c06ba89")

# Applications (subset used by fixture templates)
APP_VSCODE_ID = uuid.UUID("2aab6a3e-a322-4f98-8095-0f6e6de4fc44")
APP_CHROME_ID = uuid.UUID("2359089d-61bc-4296-901e-5ca17b3f6135")
APP_FIREFOX_ID = uuid.UUID("f7fc2362-9717-4127-80bc-bfa0b5b216b6")
APP_WORD_2022_ID = uuid.UUID("51c1cbe3-53fa-4db2-8446-7c91a9de37a0")
APP_EXCEL_2022_ID = uuid.UUID("6c6b9845-a462-42c9-8e30-9ddedaae839f")
APP_POWERPOINT_2022_ID = uuid.UUID("98bfd7be-d83a-42dc-b16b-076dc96f2e96")

# Language (German, for fixture mail templates etc.)
LANG_DE_DE_ID = uuid.UUID("08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0")

# -- Infrastructure defaults --
PROXMOX_NODE = "pve-node-01"
PROXMOX_TEMPLATE_BASE_ID = 5000
PROXMOX_VM_BASE_ID = 8000
PROXMOX_MANUAL_VM_BASE_ID = 9000
GUACD_HOSTNAME = "guacd.local"
GUACD_PORT = 4822
GUAC_IDENTIFIER_BASE = 900000


class Profile(str, Enum):
    TESTING = "testing"
    STAGING = "staging"
    DEMO = "demo"


_SIX_MONTHS_SECONDS = 180 * 24 * 3600


def next_audit_user(context: dict) -> uuid.UUID:
    """Return the next audit user ID from the rotating pool."""
    pool = context.get("_audit_pool", [SYSTEM_USER_ID])
    idx = context.get("_audit_idx", 0)
    uid = pool[idx % len(pool)]
    context["_audit_idx"] = idx + 1
    return uid


def fixture_timestamp(
    entity_type: str,
    profile: str,
    index: int,
    not_before: datetime | None = None,
) -> datetime:
    """Deterministic random timestamp in [not_before, now].

    Uses the same hashing approach as ``fixture_uuid`` to produce
    a stable timestamp that is reproducible across runs.  The
    ``not_before`` parameter ensures child objects are never older
    than their parents.
    """
    now = datetime.now(timezone.utc)
    earliest = now - timedelta(seconds=_SIX_MONTHS_SECONDS)
    if not_before:
        # Ensure timezone-aware for comparison
        if not_before.tzinfo is None:
            not_before = not_before.replace(tzinfo=timezone.utc)
        earliest = max(earliest, not_before)

    raw = f"{FIXTURE_SEED}:ts:{entity_type}:{profile}:{index}"
    h = hashlib.sha256(raw.encode()).digest()
    # Use first 8 bytes as a deterministic fraction 0..1
    n = int.from_bytes(h[:8], "big")
    fraction = n / (2**64)

    span = (now - earliest).total_seconds()
    offset = fraction * span
    return earliest + timedelta(seconds=offset)


def ensure_association(session, table, **values) -> None:
    """Insert into an association table if the row doesn't exist yet."""
    conditions = [table.c[k] == v for k, v in values.items()]
    if not session.execute(table.select().where(*conditions)).first():
        session.execute(table.insert().values(**values))


def fixture_uuid(entity_type: str, profile: str, index: int) -> uuid.UUID:
    """Generate a deterministic UUID v4 for a fixture entity.

    Uses SHA-256 of a stable input string, then forces the version
    and variant bits to comply with UUID v4 so that Pydantic's
    ``UUID4`` validator accepts the result.
    """
    raw = f"{FIXTURE_SEED}:{entity_type}:{profile}:{index}"
    h = hashlib.sha256(raw.encode()).digest()[:16]
    # Set version to 4 (bits 48-51)
    h = bytearray(h)
    h[6] = (h[6] & 0x0F) | 0x40
    # Set variant to RFC 4122 (bits 64-65)
    h[8] = (h[8] & 0x3F) | 0x80
    return uuid.UUID(bytes=bytes(h))
