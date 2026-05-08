#!/bin/sh
set -e

# Backwards compatibility: explicit command takes precedence
if [ $# -gt 0 ]; then
    exec "$@"
fi

# SERVICE_ROLE must be set
if [ -z "$SERVICE_ROLE" ]; then
    echo "[entrypoint] ERROR: SERVICE_ROLE is not set" >&2
    exit 1
fi

# Set SENTRY_RELEASE based on service role
if [ -n "$SENTRY_RELEASE_BACKEND" ]; then
    case "$SERVICE_ROLE" in
        backend)
            export SENTRY_RELEASE="$SENTRY_RELEASE_BACKEND"
            ;;
        worker*|scheduler)
            export SENTRY_RELEASE=$(echo "$SENTRY_RELEASE_BACKEND" | sed 's/backend/worker/')
            ;;
    esac
fi

echo "[entrypoint] Starting service: $SERVICE_ROLE"
case "$SERVICE_ROLE" in
    backend)
        echo "[entrypoint] Running database migrations..."
        python migrate.py
        echo "[entrypoint] Migrations complete."
        if [ -n "$SEED_FIXTURES_PROFILE" ]; then
            echo "[entrypoint] Seeding fixtures (profile: $SEED_FIXTURES_PROFILE)..."
            python -m scripts.seed_fixtures --profile "$SEED_FIXTURES_PROFILE"
        fi
        exec uvicorn main:app \
            --host 0.0.0.0 \
            --port 80 \
            --proxy-headers \
            --forwarded-allow-ips="${BACKEND_PROXY_IPS:-*}"
        ;;
    worker*)
        exec python -m scripts.worker
        ;;
    scheduler)
        exec python -m scripts.scheduler
        ;;
    *)
        echo "[entrypoint] ERROR: Unknown SERVICE_ROLE='$SERVICE_ROLE'" >&2
        echo "[entrypoint] Valid roles: backend, worker, worker-vm-clone, worker-periodic, worker-all, scheduler" >&2
        exit 1
        ;;
esac
