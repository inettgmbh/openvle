"""Launch rq worker based on SERVICE_ROLE environment variable."""

import os
import sys

from core.config import Settings
from core.redis import WORKER_PROFILES

role = os.environ.get("SERVICE_ROLE", "worker")
if role not in WORKER_PROFILES:
    print(
        f"Error: No queue profile for SERVICE_ROLE='{role}'",
        file=sys.stderr,
    )
    print(f"Available: {', '.join(WORKER_PROFILES)}", file=sys.stderr)
    sys.exit(1)

settings = Settings()
redis_url = (
    f"redis://:{settings.redis_password}"
    f"@{settings.redis_host}:{settings.redis_port}"
    f"/{settings.redis_database}"
)

queues = WORKER_PROFILES[role]
os.execvp(
    "rq",
    [
        "rq",
        "worker",
        "-c",
        "core.config_worker",
        *queues,
        "--with-scheduler",
        "-u",
        redis_url,
    ],
)
