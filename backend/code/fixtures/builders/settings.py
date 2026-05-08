import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from fixtures.constants import Profile
from fixtures.profiles import ProfileConfig
from models.system import SystemSetting

log = logging.getLogger("fixtures")

# Settings to update per profile
_PROFILE_SETTINGS: dict[Profile, dict[str, str]] = {
    Profile.DEMO: {
        "branding.app.name": "OpenVLE Demo",
        "branding.app.title": "OpenVLE Demo-Umgebung",
        "branding.customer.name": "Hochschule Musterstadt",
        "branding.customer.url01": ("https://www.hs-musterstadt.de/informatik"),
        "branding.customer.url02": "https://www.hs-musterstadt.de",
        "branding.support.email": "support@hs-musterstadt.de",
        "branding.support.name": ("Rechenzentrum Hochschule Musterstadt"),
        "branding.support.url": "https://rz.hs-musterstadt.de",
        "version.backend.label": "demo",
    },
    Profile.STAGING: {
        "branding.app.name": "OpenVLE Staging",
        "branding.app.title": "OpenVLE Staging-Umgebung",
        "branding.customer.name": "Hochschule Musterstadt",
        "branding.customer.url01": (
            "https://staging.hs-musterstadt.de/informatik"
        ),
        "branding.customer.url02": ("https://staging.hs-musterstadt.de"),
        "branding.support.email": ("staging-support@hs-musterstadt.de"),
        "branding.support.name": ("Rechenzentrum Hochschule Musterstadt"),
        "branding.support.url": "https://rz.hs-musterstadt.de",
        "version.backend.label": "staging",
    },
    Profile.TESTING: {
        "branding.app.name": "OpenVLE Testing",
        "branding.app.title": "OpenVLE Test-Umgebung",
        "branding.customer.name": "Test-Organisation",
        "branding.customer.url01": "https://test.example.com",
        "branding.customer.url02": "https://example.com",
        "branding.support.email": "test@example.com",
        "branding.support.name": "Test-Support",
        "branding.support.url": "https://example.com/support",
        "version.backend.label": "testing",
    },
}

# Original seed values for restore on purge
_SEED_DEFAULTS: dict[str, str] = {
    "branding.app.name": "OpenVLE",
    "branding.app.title": "OpenVLE",
    "branding.customer.name": "Example Customer",
    "branding.customer.url01": (
        "https://www.example.com/my-example-project-page"
    ),
    "branding.customer.url02": "https://www.example.com/",
    "branding.support.email": "support@example.com",
    "branding.support.name": "Example GmbH",
    "branding.support.url": "https://www.example.com",
    "version.backend.label": "prod",
}


def _get_setting(session: Session, key: str):
    return session.execute(
        select(SystemSetting).where(SystemSetting.key == key)
    ).scalar_one_or_none()


def update_settings(
    session: Session,
    config: ProfileConfig,
    context: dict,
) -> None:
    overrides = _PROFILE_SETTINGS.get(config.name, {})
    count = 0

    for key, value in overrides.items():
        setting = _get_setting(session, key)
        if setting and setting.value != value:
            setting.value = value
            count += 1

    session.flush()
    log.info("  %d settings updated", count)


def restore_settings(session: Session) -> None:
    """Restore seed defaults for branding settings."""
    count = 0
    for key, default_value in _SEED_DEFAULTS.items():
        setting = _get_setting(session, key)
        if setting and setting.value != default_value:
            setting.value = default_value
            count += 1
    session.flush()
    log.info("  %d settings restored", count)
