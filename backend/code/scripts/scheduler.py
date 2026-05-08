"""Launch rq cron scheduler with Redis URL from settings."""

import os

from core.config import Settings

settings = Settings()
redis_url = (
    f"redis://:{settings.redis_password}"
    f"@{settings.redis_host}:{settings.redis_port}"
    f"/{settings.redis_database}"
)

os.execvp(
    "rq",
    [
        "rq",
        "cron",
        "scripts/cron_config.py",
        "--url",
        redis_url,
        "--logging-level",
        os.environ.get("SCHEDULER_LOG_LEVEL", "INFO"),
    ],
)
