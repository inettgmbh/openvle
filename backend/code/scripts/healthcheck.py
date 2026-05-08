"""Universal healthcheck script dispatching by SERVICE_ROLE."""

import os
import subprocess
import sys


def check_backend():
    import httpx

    r = httpx.get("http://localhost:80/system/healthz", timeout=5)
    r.raise_for_status()


def check_worker():
    from redis import Redis
    from rq import Worker

    from core.config import Settings

    settings = Settings()
    conn = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_database,
        password=settings.redis_password,
    )
    conn.ping()
    hostname = os.environ.get("HOSTNAME", "")
    workers = Worker.all(connection=conn)
    if not any(w.hostname == hostname for w in workers):
        print(f"No RQ worker registered for hostname {hostname}")
        sys.exit(1)


def check_scheduler():
    from redis import Redis

    from core.config import Settings

    settings = Settings()
    conn = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_database,
        password=settings.redis_password,
    )
    conn.ping()
    result = subprocess.run(
        ["pgrep", "-f", "rq cron"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        print("rq cron process not running")
        sys.exit(1)


def main():
    role = os.environ.get("SERVICE_ROLE", "")
    try:
        if role.startswith("backend"):
            check_backend()
        elif role.startswith("worker"):
            check_worker()
        elif role == "scheduler":
            check_scheduler()
        else:
            print(f"Unknown SERVICE_ROLE: {role}")
            sys.exit(1)
    except SystemExit:
        raise
    except Exception as e:
        print(f"Healthcheck failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
