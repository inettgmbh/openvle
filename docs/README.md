# OpenVLE Docs

User and administrator documentation for OpenVLE — built with [Docusaurus 3](https://docusaurus.io/), MDX, and i18n (DE / EN / FR). Source language is German; English and French are translations under `i18n/`.

The published site lives at [docs.openvle.org](https://docs.openvle.org).

For an overview of the whole project, see the [root README](../README.md).

## Layout

```
docs/
├── docs/                # Docusaurus content (German source)
│   ├── admin/           # Administrator guide
│   ├── usage/           # End-user guide
│   └── changelogs/
├── i18n/
│   ├── de/              # German UI/theme strings
│   ├── en/              # English translation
│   └── fr/              # French translation
├── src/                 # Custom React components / theme overrides
├── static/              # Static assets served as-is
├── docusaurus.config.js
├── sidebars.js
├── babel.config.js
├── eslint.config.mjs
├── package.json
├── Dockerfile           # Production image (build → nginx)
├── docker-compose.yml   # Standalone docs service
├── nginx.conf
└── .env.sample          # DOCS_IMAGE_TAG
```

## Development

```bash
cd docs
npm install
npm run dev             # German (default)
npm run dev:en          # English
npm run dev:fr          # French
```

Each `dev` variant launches a Docusaurus dev server at `http://localhost:3000` for that locale only — switching locales requires restarting with the matching script.

### Quality checks

```bash
npm run format            # prettier --check (use format:fix to write)
npm run lint              # eslint (use lint:fix to auto-fix)
npm run build             # build all locales into build/
npm run serve             # serve the production build locally
```

## Translations

German is the source. To add or update strings in English or French, edit the matching files under `i18n/<locale>/`. To regenerate the translation key files from the source content:

```bash
npm run write-translations:en
npm run write-translations:fr
```

Use `npm run write-translations:locale:override -- <locale>` to overwrite existing translations from source (destructive).

## Production image

Two-stage build: Docusaurus produces the static site, nginx serves it. Published per release at `${IMAGE_REGISTRY:-ghcr.io/inettgmbh}/openvle/docs:v${VERSION}`.

To run the standalone docs service:

```bash
cd docs
cp .env.sample .env       # DOCS_IMAGE_TAG (defaults to latest)
docker compose up
```

## Versioning, contributing, license

See the [root README](../README.md) for versioning, [`CONTRIBUTING.md`](../CONTRIBUTING.md) for contribution guidelines, and [`LICENSE`](../LICENSE) for the AGPL v3.0 license.
