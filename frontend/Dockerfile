FROM node:lts AS build-stage
WORKDIR /app
COPY ./code/package*.json ./
RUN npm install --no-fund
RUN npm install -g @sentry/cli --no-fund --no-audit
COPY ./code/ .
COPY ./.env.build ./.env
ARG SENTRY_RELEASE VERSION
RUN npm run build
RUN sentry-cli sourcemaps inject /app/dist

FROM nginx:stable-alpine AS production-stage
LABEL maintainer="" \
      org.opencontainers.image.authors="inett GmbH <support@inett.de>" \
      org.opencontainers.image.source=https://github.com/inettgmbh/openvle \
      org.opencontainers.image.url=https://github.com/inettgmbh/openvle \
      org.opencontainers.image.documentation=https://docs.openvle.org \
      org.opencontainers.image.licenses=AGPL-3.0 \
      org.opencontainers.image.vendor="inett GmbH" \
      org.opencontainers.image.title="OpenVLE Frontend" \
      org.opencontainers.image.description="Web interface for OpenVLE"
COPY --from=build-stage /app/dist /usr/share/nginx/html
RUN rm -rf /usr/share/nginx/html/50x.html
COPY nginx.conf /etc/nginx/nginx.conf
COPY ./env_injection.sh /docker-entrypoint.d/env_injection.sh
EXPOSE 80
