"""Cron job definitions for ``rq cron``.

This module is loaded by the scheduler container via::

    rq cron scripts/cron_config.py --url <redis_url>

Each ``register()`` call declares a periodic task.  The CronScheduler
process enqueues them independently of the workers, so a crashing job
can never break the schedule.
"""

from rq.cron import register

from core.config import Settings
from core.periodic_tasks import events_periodic, mail_periodic_delete
from pve.pve_node_info import proxmox_node_info_periodic

settings = Settings()

# -- PVE Node-Info: poll Proxmox cluster every N seconds (default 60) --------
register(
    proxmox_node_info_periodic,
    queue_name="pve_periodic",
    interval=settings.worker_pve_periodic_interval,
)

# -- Events: check for due start/end daily at 01:00 UTC ---------------------
register(
    events_periodic,
    queue_name="core_periodic",
    cron="0 1 * * *",
)

# -- Mail cleanup: delete expired mails daily at 02:00 UTC ------------------
register(
    mail_periodic_delete,
    queue_name="core_periodic",
    cron="0 2 * * *",
)
