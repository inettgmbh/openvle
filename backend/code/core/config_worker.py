from core.config import Settings

settings = Settings()

# Add Sentry (worker) if it is enabled
if settings.sentry_worker_enabled:
    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.sentry_worker_dsn,
        traces_sample_rate=settings.sentry_worker_traces_sample_rate,
        profiles_sample_rate=settings.sentry_worker_profiles_sample_rate,
        enable_tracing=settings.sentry_worker_enable_tracing,
        environment=settings.sentry_env,
        release=settings.sentry_release or None,
    )
