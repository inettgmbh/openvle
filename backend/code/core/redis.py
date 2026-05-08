from redis import Redis
from redis.exceptions import AuthenticationError, ConnectionError, TimeoutError
from rq import Queue, Retry

from .config import Settings
from .exceptions import RedisConnectionError

settings = Settings()

try:
    # Connect to the Redis server
    redis_connection = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_database,
        password=settings.redis_password,
        socket_connect_timeout=5,
    )
    # Test connection is reachable
    redis_connection.ping()
except AuthenticationError as e:
    # Add local logger call with exception msg
    raise RedisConnectionError()
except TimeoutError as e:
    # Add local logger call with exception msg
    raise RedisConnectionError()
except ConnectionError as e:
    # Add local logger call with exception msg
    raise RedisConnectionError()

# PVE queues
queue_pve_periodic = Queue(
    name="pve_periodic",
    connection=redis_connection,
    retry=Retry(max=3, interval=[5, 10, 15]),
)  # Used for periodic operations (pve_node_info, ...)
queue_pve_vm_clone = Queue(
    name="pve_vm_clone",
    connection=redis_connection,
    retry=Retry(max=settings.worker_max_retry, interval=[10, 30, 60]),
)  # Used for cloning VMs
queue_pve_vm_actions = Queue(
    name="pve_vm_actions",
    connection=redis_connection,
    retry=Retry(max=settings.worker_max_retry, interval=[5, 10, 15]),
)  # Used for VM actions(update, start, etc)

# Mails queue
queue_mails = Queue(
    name="mails",
    connection=redis_connection,
    retry=Retry(max=settings.worker_max_retry, interval=[30, 60, 120]),
)

# Guacamole queue
queue_guacamole = Queue(
    name="guacamole",
    connection=redis_connection,
    retry=Retry(max=settings.worker_max_retry, interval=[10, 30, 60]),
)

# Moodle queue
queue_moodle = Queue(
    name="moodle",
    connection=redis_connection,
    retry=Retry(max=settings.worker_max_retry, interval=[10, 30, 60]),
)

# Core queues
queue_core_periodic = Queue(
    name="core_periodic",
    connection=redis_connection,
    retry=Retry(max=3, interval=[5, 10, 15]),
)  # Used for periodic operations

# Worker queue profiles — keys match SERVICE_ROLE values
WORKER_PROFILES: dict[str, list[str]] = {
    "worker": [
        "core_periodic",
        "guacamole",
        "mails",
        "moodle",
        "pve_vm_actions",
    ],
    "worker-vm-clone": ["pve_vm_clone"],
    "worker-periodic": ["pve_periodic"],
}
WORKER_PROFILES["worker-all"] = sorted(
    {q for queues in WORKER_PROFILES.values() for q in queues}
)
