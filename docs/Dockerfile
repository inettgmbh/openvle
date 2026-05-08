FROM node:lts AS build-stage
ENV FORCE_COLOR=0
WORKDIR /app
COPY ./package*.json ./
RUN npm install --unsafe-perm --no-fund --no-audit
COPY ./ .
ARG VERSION
ENV APP_VERSION=$VERSION
RUN npm run build -- --out-dir ./dist/


FROM nginx:stable-alpine AS production-stage
LABEL maintainer="" \
      org.opencontainers.image.authors="inett GmbH <support@inett.de>" \
      org.opencontainers.image.source=https://github.com/inettgmbh/openvle \
      org.opencontainers.image.url=https://github.com/inettgmbh/openvle \
      org.opencontainers.image.documentation=https://docs.openvle.org \
      org.opencontainers.image.licenses=AGPL-3.0 \
      org.opencontainers.image.vendor="inett GmbH" \
      org.opencontainers.image.title="OpenVLE Docs" \
      org.opencontainers.image.description="User and administrator documentation for OpenVLE"
COPY --from=build-stage /app/dist /usr/share/nginx/html
RUN rm -rf /usr/share/nginx/html/50x.html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
