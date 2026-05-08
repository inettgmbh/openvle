# Contributing to OpenVLE

Thank you for considering a contribution to OpenVLE. Whether you found a bug,
have an idea for a feature, or want to send code — this document explains how
to do that effectively.

> **Where development happens.** OpenVLE is hosted publicly on
> [github.com/inettgmbh/openvle](https://github.com/inettgmbh/openvle). Day-to-day
> development by the core team currently runs on an internal GitLab mirror,
> which lets us reuse existing CI and deployment infrastructure. The two stay
> in sync, and external contributions are reviewed and merged through GitHub.

## Table of contents

- [Ways to contribute](#ways-to-contribute)
- [Reporting bugs](#reporting-bugs)
- [Suggesting features](#suggesting-features)
- [Contributing code](#contributing-code)
  - [Development setup](#development-setup)
  - [Branches](#branches)
  - [Code style](#code-style)
  - [Tests](#tests)
  - [Translations (backend)](#translations-backend)
  - [Commit messages](#commit-messages)
  - [Opening a pull request](#opening-a-pull-request)
- [Review process](#review-process)
- [License](#license)

## Ways to contribute

There are three useful things you can do, in increasing order of effort:

1. **Report a bug** — open an issue describing what you expected and what
   actually happened.
2. **Suggest a feature** — open an issue describing the use case it would
   solve.
3. **Submit code** — fork the repo, make your change on a branch, open a
   pull request.

You don't need to ask permission before opening an issue or starting work on
a small fix. For larger changes, opening an issue first is a good way to
check that the direction fits the project before you invest time.

## Reporting bugs

Open an issue and include:

- A short, specific title (for example: `frontend crashes when opening
  course with no scheduled events`).
- The OpenVLE version (visible in the footer, or via `git describe --tags`).
- Steps to reproduce, in the smallest form that still triggers the bug.
- What you expected to happen.
- What actually happened, including any error message or relevant log
  output.
- Your environment if it might matter (browser, OS, Proxmox version, etc.).

If you suspect a security issue, please **do not open a public issue**.
Email [support@inett.de](mailto:support@inett.de) instead.

## Suggesting features

Open an issue and describe:

- The problem you're trying to solve (not just the feature you imagine).
- Who benefits and in which situation.
- A rough idea of how it could work, if you have one.

Feature requests are easier to act on when they describe a real use case
rather than a generic "wouldn't it be nice if". Concrete is better than
abstract.

## Contributing code

### Development setup

Each component has its own README with detailed setup steps:

- [`backend/README.md`](backend/README.md) — Python 3.10, FastAPI, MariaDB
- [`frontend/README.md`](frontend/README.md) — Vue 3, Vite, npm
- [`docs/README.md`](docs/README.md) — Docusaurus 3

Runtimes are pinned in `.mise.toml`. If you use [mise](https://mise.jdx.dev),
run `mise install` from the repo root to get matching versions.

For a full local stack, the top-level `docker-compose.yml` runs backend and
frontend together against a fresh database.

### Branches

Branch off `main`. Use a short descriptive name, kebab-case, optionally
prefixed with the change type:

```
feat/course-bulk-import
fix/scheduler-timezone-offset
docs/clarify-proxmox-setup
```

### Code style

Code style is enforced by formatters and linters that also run in CI. Run
them locally before pushing.

**Backend (Python):**
```sh
cd backend/code
ruff format .          # auto-format
ruff check . --fix     # lint with autofix where possible
```
Configuration lives in `backend/code/pyproject.toml`.

**Frontend (Vue / TypeScript):**
```sh
cd frontend/code
npm run format:fix     # prettier
npm run lint:fix       # eslint
```

**Documentation:**
```sh
cd docs
npm run format:fix
npm run lint:fix
```

### Tests

Add tests for new behavior and bug fixes. Existing tests must keep passing.

**Backend:**
```sh
cd backend/code
pytest                                # full suite
pytest path/to/test_module.py         # one file
```

**Frontend:**
```sh
cd frontend/code
npm run test:unit                     # watch mode
npm run test:coverage                 # with coverage
```

If you change database models, add an Alembic migration:
```sh
cd backend/code
alembic revision --autogenerate -m "describe the change"
```
The migration must be reversible — CI runs a full upgrade/downgrade cycle.

### Translations (backend)

Backend strings marked with `_()` (gettext) are tracked under
`backend/code/translations/`. If you add, change, or remove such a string,
regenerate the translation files before committing:

```sh
cd backend/code
./scripts/i18n.sh all
git add translations/
```

This is the single most common reason a backend pull request fails CI —
please run the script after string changes.

### Commit messages

OpenVLE uses
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/). The
release tooling reads commit messages directly to determine version bumps
and generate the `CHANGELOG.md`, so the format matters.

Format:

```
type(scope): short imperative description

Optional body explaining the why, wrapped at ~72 characters.

BREAKING CHANGE: only if applicable, in the body.
```

Common types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `ci`.

Effect on versioning:

- `feat:` → minor version bump
- `fix:` → patch version bump
- `BREAKING CHANGE:` in the body, or `!` after the type (e.g. `feat!:`) →
  major version bump
- `chore:`, `docs:`, `test:`, `refactor:` → no release

Examples from the project:

```
feat(scheduler): support recurring weekly events
fix(auth): reject expired refresh tokens
refactor(backend): rename internal kvs identifiers to openvle
ci(deploy): unify deploy/restart jobs onto compose-ssh template
```

### Opening a pull request

1. Push your branch to your fork.
2. Open a pull request against `main` on
   [github.com/inettgmbh/openvle](https://github.com/inettgmbh/openvle).
3. Mark the PR as a draft until it's ready for review.
4. Reference the issue your PR closes (`Closes #123`) so it's auto-closed
   on merge.
5. Make sure all checks pass before requesting review.

## Review process

A maintainer will review your pull request within a reasonable timeframe.
We may ask for changes; this is normal and not a judgment of your work.
Once feedback is addressed and checks are green, a maintainer merges the
PR.

We squash-merge most contributions to keep `main` history linear and the
auto-generated changelog readable.

## License

OpenVLE is licensed under the
[GNU Affero General Public License v3.0](LICENSE). By contributing code,
documentation, or other material to this repository, you agree that your
contribution is published under the same license.
