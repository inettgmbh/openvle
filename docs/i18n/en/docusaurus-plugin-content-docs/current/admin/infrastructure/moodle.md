---
id: moodle
sidebar_label: Moodle
sidebar_position: 60
status: finished
tags:
  - infrastructure
  - moodle
---

# Moodle {#moodle}

OpenVLE can be connected to an existing Moodle instance to automatically provision learning environments. Moodle courses are duplicated, participants are synchronized, and enrollments are managed — all controlled by the lifecycle of events in OpenVLE.

:::info Optional
The Moodle integration is fully optional. When not in use, all Moodle-related elements are hidden in the user interface. The integration is disabled by default.
:::

## Architecture {#architecture}

OpenVLE communicates with Moodle exclusively via the **Moodle Web Services REST API**. There is no direct database connection — all operations are performed through HTTP API calls.

| Component               | Role                                                                       |
| ----------------------- | -------------------------------------------------------------------------- |
| **OpenVLE Backend**     | Retrieves Moodle courses and checks users                                  |
| **OpenVLE Worker**      | Performs course duplication, user creation, and enrollments asynchronously |
| **Moodle Web Services** | Receives API requests and executes the operations in Moodle                |

:::note Network access
The OpenVLE backend must be able to establish outgoing HTTPS connections to the Moodle instance. Authentication is done via a Moodle API token.
:::

## Concept: Course mapping {#course-mapping}

The integration is based on mapping Moodle courses to OpenVLE environments:

1. **Environment** — An OpenVLE environment can be linked to a Moodle course. This Moodle course serves as a **template**.
2. **Event** — When an event is started from this environment, OpenVLE automatically duplicates the Moodle template course. Each event receives its own Moodle course.

## Event lifecycle {#event-lifecycle}

The Moodle actions are tied to the lifecycle of an event:

| Phase                  | Moodle action                                                        |
| ---------------------- | -------------------------------------------------------------------- |
| **Deployment**         | Template course is duplicated, participants are created and enrolled |
| **Add participant**    | User is created in Moodle if needed and enrolled in the course       |
| **Remove participant** | User is unenrolled from the Moodle course                            |
| **Event end**          | Students are unenrolled, instructors remain, course becomes hidden   |
| **Delete event**       | Moodle course is optionally deleted (configurable)                   |

### User synchronization {#user-sync}

During deployment, OpenVLE checks for each participant whether a corresponding user exists in Moodle. The matching is done via the configured field (`MOODLE_USER_MATCH_FIELD` — either `email` or `username`). If no Moodle user is found, OpenVLE automatically creates a new one.

### Role mapping {#role-mapping}

OpenVLE maps participant roles to Moodle course roles:

| OpenVLE role | Moodle role                 |
| ------------ | --------------------------- |
| Instructor   | Editing Teacher (Role ID 3) |
| Student      | Student (Role ID 5)         |

:::caution Data loss on unenrollment
When unenrolling a participant, submissions, grades, and learning progress in the Moodle course are lost. This is a limitation of the Moodle REST API (see [MDL-70582](https://tracker.moodle.org/browse/MDL-70582)).
:::

## Further reading {#further-reading}

- [Configure Moodle](../install/moodle) — Setup, configuration, and troubleshooting
- [Configuration reference](../install/configuration) — All Moodle environment variables
