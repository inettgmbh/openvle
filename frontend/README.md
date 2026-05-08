# OpenVLE Frontend

Web interface for OpenVLE — Vue 3, Vite, Pinia, Tailwind. The frontend talks to the backend API and is served as a static bundle from an nginx container in production.

For an overview of the whole project, see the [root README](../README.md). For installation guides, configuration references, and admin/usage how-tos, see [docs.openvle.org](https://docs.openvle.org).

## Layout

```
frontend/
├── code/                # Vue source (npm project root)
│   ├── src/
│   ├── tests/
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   ├── vitest.config.js
│   ├── tailwind.config.js
│   └── eslint.config.js
├── Dockerfile           # Production image (build → nginx)
├── docker-compose.yml   # Standalone frontend service
├── nginx.conf           # nginx config served inside the container
├── env_injection.sh     # Injects runtime env vars into the static bundle on container start
└── .env.sample          # Sample env (FRONTEND_IMAGE_TAG, VITE_*)
```

## Development

```bash
cd frontend/code
cp .env.sample .env             # see code/.env or, for runtime injection, ../.env.sample
npm install
npm run dev                     # vite dev server with HMR (default: http://localhost:5173)
```

Point `VITE_BACKEND_URL` at a running backend (local stack or testing host). If left unset, the frontend falls back to the same origin it was loaded from and calls `/v1/` there — convenient when frontend and backend are served behind one host/reverse proxy in production, but unusable for `npm run dev`, where the backend isn't on the Vite dev server.

### Quality checks

```bash
npm run lint                    # eslint (use lint:fix to auto-fix)
npm run format                  # prettier --check (use format:fix to write)
npm run test:unit               # vitest, watch mode
npm run test:coverage           # vitest with coverage
npm run build                   # production build into code/dist/
```

## Production image

The production image is a two-stage build: Vue bundle → nginx. At container start, `env_injection.sh` reads runtime config from `/docker-entrypoint.d/.env` and patches the built JS, so `VITE_*` values can be set without rebuilding.

The image is published per release:

```
${IMAGE_REGISTRY:-ghcr.io/inettgmbh}/openvle/frontend:v${VERSION}
```

To run the standalone frontend service:

```bash
cd frontend
cp .env.sample .env             # FRONTEND_IMAGE_TAG, VITE_BACKEND_URL, optional Sentry
docker compose up
```

Or pull an arbitrary tag directly:

```bash
docker run --rm -p 8080:8080 \
  -v "$PWD/.env:/docker-entrypoint.d/.env:ro" \
  ghcr.io/inettgmbh/openvle/frontend:v1.0.0
```

## Versioning, contributing, license

See the [root README](../README.md) for versioning, [`CONTRIBUTING.md`](../CONTRIBUTING.md) for contribution guidelines, and [`LICENSE`](../LICENSE) for the AGPL v3.0 license.
