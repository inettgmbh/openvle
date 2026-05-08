FROM python:3.10
LABEL maintainer="" \
      org.opencontainers.image.authors="inett GmbH <support@inett.de>" \
      org.opencontainers.image.source=https://github.com/inettgmbh/openvle \
      org.opencontainers.image.url=https://github.com/inettgmbh/openvle \
      org.opencontainers.image.documentation=https://docs.openvle.org \
      org.opencontainers.image.licenses=AGPL-3.0 \
      org.opencontainers.image.vendor="inett GmbH" \
      org.opencontainers.image.title="OpenVLE Backend" \
      org.opencontainers.image.description="REST API, background workers, and scheduler for OpenVLE"
ARG SENTRY_RELEASE=""
ENV SENTRY_RELEASE_BACKEND=$SENTRY_RELEASE
WORKDIR /usr/src/app
COPY ./code/requirements.txt ./
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY ./code/ ./
RUN ./scripts/i18n.sh compile
RUN chmod +x ./scripts/entrypoint.sh
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=30s \
  CMD ["python", "-m", "scripts.healthcheck"]
ENTRYPOINT ["./scripts/entrypoint.sh"]
