---
id: permission-system
sidebar_label: Berechtigungssystem
sidebar_position: 45
status: finished
tags:
  - infrastructure
  - permissions
---

# Berechtigungssystem {#permission-system}

Das Berechtigungssystem von OpenVLE steuert, welche Aktionen Benutzer auf welchen Ressourcen ausführen dürfen. Es basiert auf einem ObjectPermission-Modell, das sowohl globale als auch objektbezogene Berechtigungen unterstützt.

:::info Authentifizierung vs. Autorisierung
Die Autorisierung (was darf ein Benutzer tun?) wird durch das hier beschriebene Berechtigungssystem gesteuert. Die Authentifizierung (wer ist der Benutzer?) wird separat behandelt — siehe [Authentifizierung](authentication).
:::

## Konzept {#concept}

Jede Berechtigung in OpenVLE ist eine Kombination aus:

- **Objekttyp** — Die Ressource, auf die sich die Berechtigung bezieht (z. B. `VirtualMachine`, `Event`, `User`, `Role`)
- **Objekt-ID** — Eine spezifische Instanz (oder leer für globale Berechtigung)
- **Berechtigungsschlüssel** — Die erlaubte Aktion (z. B. `object_read`, `object_update`, `object_full`)
- **Entität** — Der Benutzer oder die Rolle, der/die die Berechtigung erhält

## Berechtigungsschlüssel {#permission-keys}

### Standard-CRUD-Berechtigungen {#crud-permissions}

Die CRUD-Berechtigungen folgen einer Hierarchie — eine höhere Berechtigung schließt die darunterliegenden automatisch mit ein:

| Schlüssel       | Gewährt                            | Beschreibung                        |
| --------------- | ---------------------------------- | ----------------------------------- |
| `object_full`   | full, delete, update, read, create | Vollzugriff auf die Ressource       |
| `object_delete` | delete, update, read               | Löschen, Bearbeiten und Lesen       |
| `object_update` | update, read                       | Bearbeiten und Lesen                |
| `object_read`   | read                               | Nur Lesen                           |
| `object_create` | create                             | Neue Objekte erstellen (nur global) |

:::note Hierarchie-Beispiel
Hat ein Benutzer `object_delete` auf VMs, darf er VMs löschen, bearbeiten und lesen — eine separate `object_read`-Berechtigung ist nicht nötig.
:::

### Spezielle Berechtigungen {#special-permissions}

Neben den Standard-CRUD-Berechtigungen gibt es spezielle Berechtigungen für bestimmte Objekttypen:

| Schlüssel                                          | Objekttyp             | Beschreibung                                 |
| -------------------------------------------------- | --------------------- | -------------------------------------------- |
| `object_actions_start`, `object_actions_stop`, ... | VirtualMachine, Event | Einzelne Aktionen (Starten, Stoppen, etc.)   |
| `object_set_password`                              | User                  | Passwort eines Benutzers ändern              |
| `object_search`                                    | User                  | Benutzer durchsuchen                         |
| `object_send`, `object_send_bulk`                  | Mail                  | E-Mails versenden                            |
| `object_reset`                                     | VirtualMachine        | VM zurücksetzen                              |
| `object_templates_update`                          | Event                 | VM-Vorlagen in Veranstaltungen aktualisieren |

## Globale vs. objektbezogene Berechtigungen {#scopes}

Das System unterscheidet zwei Geltungsbereiche:

| Geltungsbereich   | Objekt-ID          | Wirkung                                    |
| ----------------- | ------------------ | ------------------------------------------ |
| **Global**        | leer               | Gilt für **alle** Instanzen des Objekttyps |
| **Objektbezogen** | UUID einer Instanz | Gilt nur für die **spezifische** Instanz   |

**Beispiel:** Ein Benutzer mit globalem `object_read` auf `VirtualMachine` kann alle VMs lesen. Ein Benutzer mit objektbezogenem `object_read` auf eine bestimmte VM-ID kann nur diese eine VM lesen.

Bei der Berechtigungsprüfung wird zuerst nach einer objektbezogenen Berechtigung gesucht. Ist keine vorhanden, wird auf die globale Berechtigung zurückgefallen.

:::note Nur-globale Objekttypen
Einige Objekttypen unterstützen ausschließlich globale Berechtigungen (keine objektbezogenen): Activity, Changelog, Dashboard, Language, Mail, ObjectPermission, Proxmox, SubTask, System, Tag, Task.
:::

## Rollen {#roles}

Rollen fassen Berechtigungen zusammen und können mehreren Benutzern zugewiesen werden. Benutzer erben alle Berechtigungen ihrer zugewiesenen Rollen.

- **Benutzerdefinierte Rollen** — Können frei erstellt, bearbeitet und gelöscht werden
- **Systemrollen** — Vordefinierte, geschützte Rollen, die nicht gelöscht werden können

Ein Benutzer kann mehrere Rollen haben. Die effektiven Berechtigungen ergeben sich aus der Kombination aller direkten Berechtigungen und aller Rollen-Berechtigungen.

## Berechtigungsprüfung {#authorization-flow}

Bei jeder geschützten Aktion prüft das Backend die Berechtigung über den `PermissionChecker`:

1. **Effektive Berechtigungen laden** — Alle direkten Berechtigungen des Benutzers und alle Berechtigungen seiner Rollen werden zusammengeführt
2. **Berechtigung auflösen** — Der angeforderte Berechtigungsschlüssel wird gegen die effektiven Berechtigungen geprüft (inkl. Hierarchie)
3. **Ergebnis** — Bei vorhandener Berechtigung wird die Aktion ausgeführt, andernfalls wird `403 Forbidden` zurückgegeben

## Frontend-Sichtbarkeit {#frontend-visibility}

Das Frontend ruft die effektiven Berechtigungen des angemeldeten Benutzers über die API ab. Basierend darauf werden Aktionen und Elemente in der Benutzeroberfläche ein- oder ausgeblendet — Buttons zum Erstellen, Bearbeiten oder Löschen werden nur angezeigt, wenn der Benutzer die entsprechende Berechtigung besitzt.

## Datenmodell {#data-model}

Das Berechtigungssystem basiert auf folgenden Datenbanktabellen:

| Tabelle                  | Beschreibung                                                  |
| ------------------------ | ------------------------------------------------------------- |
| `sys_users`              | Benutzerkonten                                                |
| `sys_roles`              | Rollen mit Name, Schlüssel und Schutzstatus                   |
| `sys_users_roles`        | Zuordnung von Benutzern zu Rollen (n:m)                       |
| `sys_object_permissions` | Alle Berechtigungen — sowohl für Benutzer als auch für Rollen |

Die Tabelle `sys_object_permissions` vereint alle Berechtigungszuweisungen in einer einzigen Struktur:

| Feld             | Beschreibung                                    |
| ---------------- | ----------------------------------------------- |
| `object_type`    | Ressourcentyp (z. B. `VirtualMachine`, `Event`) |
| `object_id`      | Spezifische Instanz (leer = global)             |
| `entity_id`      | Benutzer- oder Rollen-ID                        |
| `entity_type`    | `User` oder `Role`                              |
| `permission_key` | Berechtigungsschlüssel (z. B. `object_read`)    |
