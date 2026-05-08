---
id: authentication
sidebar_label: Authentifizierung
sidebar_position: 40
status: finished
tags:
  - infrastructure
  - authentication
---

# Authentifizierung {#authentication}

OpenVLE unterstützt drei Authentifizierungsmethoden: lokale Anmeldung, LDAP und OpenID Connect (OIDC). Alle Methoden können gleichzeitig aktiv sein — Benutzer wählen beim Login die gewünschte Methode.

:::info Authentifizierung vs. Autorisierung
Die Authentifizierung bestimmt, **wer** ein Benutzer ist (Identitätsprüfung). Die Autorisierung bestimmt, **was** ein Benutzer tun darf (Zugriffskontrolle). Für die Autorisierung ist das [Berechtigungssystem](permission-system) zuständig — es arbeitet unabhängig von der gewählten Authentifizierungsmethode.
:::

## Übersicht {#overview}

| Methode   | Aktivierung           | Voraussetzungen                                | Beschreibung                                                          |
| --------- | --------------------- | ---------------------------------------------- | --------------------------------------------------------------------- |
| **Lokal** | Immer aktiv           | Keine                                          | Benutzername und Passwort werden in der OpenVLE-Datenbank gespeichert |
| **LDAP**  | `LDAP_ENABLED = True` | LDAP-Server (z. B. Active Directory, OpenLDAP) | Anmeldung mit bestehenden Verzeichnisdienst-Zugangsdaten              |
| **OIDC**  | `OIDC_ENABLED = True` | OIDC-Provider (z. B. Keycloak, Azure AD)       | Single Sign-On über einen externen Identity Provider                  |

## Token-basierte Sitzungen {#token-sessions}

Unabhängig von der gewählten Authentifizierungsmethode erhält jeder Benutzer nach erfolgreicher Anmeldung ein JWT (JSON Web Token) vom Backend. Dieses Token wird für alle nachfolgenden API-Anfragen verwendet:

- **Access Token** — Kurzlebiger Token für API-Zugriff (Ablaufzeit: `AUTH_ACCESS_TOKE_EXPIRE_MINUTES`, Standard: 480 Minuten)

Die Tokens werden mit dem `AUTH_SECRET` signiert (Algorithmus: HS256). Ein Wechsel des `AUTH_SECRET` meldet alle aktiven Benutzer sofort ab.

## Lokale Authentifizierung {#local-auth}

Die lokale Authentifizierung ist die Standardmethode und immer verfügbar. Benutzer melden sich mit einem Benutzernamen und Passwort an, das in der MariaDB-Datenbank gespeichert ist. Lokale Benutzerkonten werden manuell in der Benutzeroberfläche oder über die API angelegt.

## LDAP {#ldap}

Bei aktiviertem LDAP können sich Benutzer mit ihren bestehenden Verzeichnisdienst-Zugangsdaten anmelden (z. B. Active Directory, OpenLDAP). OpenVLE prüft die Zugangsdaten gegen den konfigurierten LDAP-Server, ohne ein lokales Passwort zu speichern.

### Ablauf {#ldap-flow}

1. Benutzer gibt LDAP-Zugangsdaten auf der Anmeldeseite ein
2. Das Backend sucht den Benutzer im LDAP-Verzeichnis (basierend auf `LDAP_DN_PEOPLE` und `LDAP_ATTR_USER`)
3. Das Backend führt einen LDAP-Bind mit den eingegebenen Zugangsdaten durch
4. Bei Erfolg wird eine lokale Sitzung erstellt (JWT-Token)

### Auto-Enrollment {#ldap-enrollment}

LDAP-Benutzer werden beim ersten erfolgreichen Login automatisch in der OpenVLE-Datenbank angelegt. Benutzername und E-Mail-Adresse werden aus den LDAP-Attributen übernommen (`LDAP_ATTR_USER`, `LDAP_ATTR_MAIL`).

### Voraussetzungen {#ldap-requirements}

- Ein LDAP-Server muss vom OpenVLE-Backend aus erreichbar sein (Standard-Ports: 389 für LDAP, 636 für LDAPS)
- Das LDAP-Verzeichnis muss die Benutzer unter dem konfigurierten DN (`LDAP_DN_PEOPLE`) enthalten

## OIDC (OpenID Connect) {#oidc}

OIDC ermöglicht Single Sign-On (SSO) über einen externen Identity Provider. Benutzer werden auf die Anmeldeseite des Providers weitergeleitet und nach erfolgreicher Anmeldung zurück zu OpenVLE.

### Ablauf {#oidc-flow}

1. Benutzer klickt auf "Anmelden mit SSO" auf der Anmeldeseite
2. OpenVLE leitet den Benutzer zum OIDC-Provider weiter
3. Der Benutzer meldet sich beim Provider an (z. B. Keycloak, Azure AD)
4. Der Provider leitet den Benutzer mit einem Authorization Code zurück zu OpenVLE
5. Das Backend tauscht den Code gegen Benutzerinformationen und erstellt eine lokale Sitzung

### Auto-Enrollment {#oidc-enrollment}

Wenn `OIDC_ENROLL_USERS = True` (Standard), werden Benutzer beim ersten SSO-Login automatisch in OpenVLE registriert. Benutzername, Name und E-Mail werden aus den OIDC-Attributen übernommen (`OIDC_ATTR_USERNAME`, `OIDC_ATTR_NAME`, `OIDC_ATTR_EMAIL`).

Bei deaktiviertem Auto-Enrollment (`OIDC_ENROLL_USERS = False`) muss der Benutzer zuvor manuell in OpenVLE angelegt worden sein.

### Daten-Synchronisation {#oidc-sync}

Bei jedem OIDC-Login werden Name und E-Mail-Adresse des Benutzers mit den aktuellen Werten des Identity Providers aktualisiert. So bleiben die Benutzerdaten in OpenVLE automatisch synchron mit dem IdP — unabhängig davon, ob der Benutzer per Auto-Enrollment oder manuell angelegt wurde.

### Voraussetzungen {#oidc-requirements}

- Ein OIDC-Provider muss konfiguriert und vom Backend aus erreichbar sein
- Ein Client mit `OIDC_CLIENT_ID` und `OIDC_CLIENT_SECRET` muss beim Provider registriert sein
- Die Redirect-URL zu OpenVLE muss beim Provider als erlaubte Redirect-URL eingetragen sein

## Benutzerverwaltung und Provisionierung {#user-provisioning}

LDAP und OIDC dienen ausschließlich der **Authentifizierung** und der **On-the-fly-Provisionierung** beim Login. Es findet keine automatische Hintergrundsynchronisation von Benutzern statt — OpenVLE ruft keine Benutzerlisten aus LDAP oder dem OIDC-Provider ab.

Um einen Benutzer in OpenVLE Objekten zuzuweisen (z. B. als Teilnehmer einer Veranstaltung), muss dieser für OpenVLE bekannt sein. Das bedeutet:

- Der Benutzer hat sich **mindestens einmal angemeldet** (dabei wird er automatisch angelegt), oder
- Der Benutzer wurde **manuell angelegt** — über den CSV-Import im Frontend oder über die API

:::note Geplante Erweiterungen

- **SCIM-Integration** (Provider und Client) — Eine vollständige SCIM-Integration ist in naher Zukunft geplant und ermöglicht die automatische Provisionierung und Synchronisation von Benutzern mit externen Identity-Management-Systemen.
- **Periodischer LDAP-Sync** — Auf Kundenanfrage kann ein periodischer LDAP-Sync bereitgestellt werden, der Benutzer automatisch im Hintergrund synchronisiert.
  :::

## Hinweis zu Apache Guacamole {#guacamole-auth}

Wird [Apache Guacamole](guacamole) für den Remote-Desktop-Zugang eingesetzt, sollte Guacamole idealerweise an denselben Identity Provider (LDAP oder OIDC) angebunden werden wie OpenVLE. OpenVLE provisioniert Guacamole-Verbindungen auf die gleichen Benutzernamen wie in OpenVLE — eine Benutzerverwaltung in Guacamole ist nicht notwendig, da OpenVLE fehlende Benutzer dort automatisch anlegt. In Guacamole muss daher nur die Authentifizierung konfiguriert werden. Weitere Details findest du unter [Apache Guacamole — Benutzer-Authentifizierung](guacamole#guacamole-auth).

## Hinweis zu Moodle {#moodle-auth}

Wird [Moodle](moodle) angebunden, sollte Moodle idealerweise an denselben Identity Provider (LDAP oder OIDC) angebunden werden wie OpenVLE. OpenVLE provisioniert Moodle-Benutzer auf die gleichen Benutzernamen wie in OpenVLE — eine Benutzerverwaltung in Moodle ist nicht notwendig, da OpenVLE fehlende Benutzer dort automatisch anlegt. In Moodle muss daher nur die Authentifizierung konfiguriert werden. Weitere Details findest du unter [Moodle — Benutzer-Synchronisation](moodle#user-sync).

## Weiterführende Informationen {#further-reading}

- [Konfigurationsreferenz — Authentifizierung](../install/configuration#auth) — Allgemeine Auth-Variablen
- [Konfigurationsreferenz — LDAP](../install/configuration#ldap) — LDAP-Umgebungsvariablen
- [Konfigurationsreferenz — OIDC](../install/configuration#oidc) — OIDC-Umgebungsvariablen
- [Berechtigungssystem](permission-system) — Autorisierung und Zugriffskontrolle
