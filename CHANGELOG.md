# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0](https://github.com/inettgmbh/openvle/compare/v1.0.2...v1.1.0) (2026-11-06)

### 🎉 Features

* **backend:** block course deletion while events reference it KVS-837
* **courses:** warn and block course deletion when events are assigned KVS-837
* **frontend:** warn and block template and event deletion when in use KVS-859
* **frontend:** extend central FIELD_LIMITS to all length-bounded models
* **frontend:** add central field-length limits config
* **frontend:** let user CSV import choose full name vs first/last columns
* **object-permissions:** add schema and route to view valid ObjectPermission combinations (KVS-685)
* **vms:** show HA state and manage HA configuration in VM detail view KVS-835

### 🐛 Bug Fixes

* **backend:** correct grammar of generic delete integrity error message
* **frontend:** enforce & surface template/vm markdown description limits
* **frontend:** bind field-length limits on remaining import & inline-add surfaces
* **frontend:** enforce guacamole & connection field-length limits
* **frontend:** enforce mailtemplate & mail field-length limits
* **frontend:** enforce policy name & description limits via FIELD_LIMITS
* **frontend:** enforce os/application/vendor field-length limits across all forms
* **frontend:** enforce user/role/course field-length limits across all forms
* **frontend:** unify event name/description length limits via central config
* **frontend:** guard connection-import modal against undefined target id
* **frontend:** prevent search dropdown from being clipped in modals

### 🧰 Changes

* **backend:** return 409 OBJECT_IN_USE when deleting templates or events in use KVS-859
* **users:** validate password against system Settings validation options (KVS-771)
* **vms:** increase spacing between HA modal title and toggle KVS-835

### 📝 Docs

* **backend:** update schemas / routes with extended responses and descriptions (used by swagger and redoc) (KVS-765)
* **configuration:** document BACKEND_PROXY_IPS env variable KVS-805
* **contributing:** correct the commit-type
* **usage:** document user & participant CSV imports
* **vms:** document VM high availability management KVS-835

### 🔧 Refactor

* **frontend:** share a common.maxChars label and migrate BaseTags to it
* **frontend:** migrate remaining hardcoded maxlength literals to FIELD_LIMITS

### 🧪 Tests

* **backend:** subject tests to the project ruff config
* **frontend:** guard against hardcoded numeric maxlength literals
* **frontend:** avoid duplicate pinia provide in tests
* **users:** add test coverage for User password management (KVS-771)

### 🔧 Miscellaneous Chores

* **backend:** ignore compiled gettext .mo files
* **dev:** add mise tasks for per-component testing, linting and formatting
* **routes:** add build_description function for dynamic route description generation and extend responses (KVS-765)

## [1.0.2](https://github.com/inettgmbh/openvle/compare/v1.0.1...v1.0.2) (2026-06-09)

### 🐛 Bug Fixes

* **docs:** fix wrong tagline wording

### 🔧 Miscellaneous Chores

* **deps:** update dependency @inett/semantic-release-unsquash to v2.0.2

## [1.0.1] (2026-05-08)

### ⚠ BREAKING CHANGES

* **release:** First public release. OpenVLE, developed at inett GmbH, is now publicly available — source at github.com/inettgmbh/openvle, container images on GHCR, end-user documentation at docs.openvle.org. Welcome aboard!

### 🎉 Features

* **release:** OpenVLE goes public

