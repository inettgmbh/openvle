---
id: networking
sidebar_label: Netzwerk & Docker
sidebar_position: 25
status: finished
tags:
  - infrastructure
  - networking
  - docker
---

# Netzwerk & Docker {#networking}

Alle OpenVLE-Services laufen in Docker-Containern und kommunizieren über ein internes Docker-Netzwerk. Nur wenige Ports werden nach außen veröffentlicht. Für den Produktivbetrieb wird ein vorgelagerter Reverse Proxy empfohlen, ist aber nicht zwingend erforderlich.

## Docker-Netzwerk {#docker-network}

Der Docker-Compose-Stack erstellt automatisch ein internes Netzwerk (`openvle-internal`). Alle Container sind über dieses Netzwerk miteinander verbunden und können sich gegenseitig über ihre Service-Namen erreichen (z. B. `backend`, `mariadb`, `redis`).

:::note DNS-Auflösung
Docker Compose stellt eine interne DNS-Auflösung bereit: Container können andere Container über den Service-Namen als Hostnamen ansprechen. Deshalb steht in den Umgebungsvariablen beispielsweise `MARIADB_HOST = "db"` statt einer IP-Adresse.
:::

## Exponierte Ports {#exposed-ports}

In der Standard-`docker-compose.yml` werden nur zwei Ports nach außen veröffentlicht:

| Service    | Container-Port | Host-Port | Zweck                        |
| ---------- | -------------- | --------- | ---------------------------- |
| `frontend` | 80             | 80        | Weboberfläche (Vue.js/Nginx) |
| `backend`  | 80             | 8000      | REST-API (FastAPI)           |

Beide Services müssen vom Browser des Endbenutzers erreichbar sein: Das Frontend liefert die Weboberfläche aus, und der Browser kommuniziert zur Laufzeit direkt mit dem Backend (API-Anfragen).

Alle anderen Services (MariaDB, MongoDB, Redis, Worker, Scheduler) veröffentlichen **keine Ports** und sind ausschließlich intern erreichbar.

:::note Reverse Proxy (empfohlen)
Wird ein [Reverse Proxy](../install/reverse-proxy) eingesetzt, sollten die Port-Veröffentlichungen auf `127.0.0.1` eingeschränkt werden, da der externe Zugriff dann über den Proxy erfolgt:

```yaml
ports:
  - 127.0.0.1:80:80
  - 127.0.0.1:8000:8000
```

:::

## Kommunikationspfade {#communication-paths}

### Externer Zugriff {#external-access}

**Mit Reverse Proxy (empfohlen):**

```
Browser → Reverse Proxy → Frontend (Port 80)
Browser → Reverse Proxy → Backend (Port 8000)
```

**Ohne Reverse Proxy:**

```
Browser → Frontend (Port 80)
Browser → Backend (Port 8000)
```

Ein Reverse Proxy ist optional, wird aber für den Produktivbetrieb empfohlen — er übernimmt SSL-Terminierung, Routing und ggf. Lastverteilung. Siehe [Reverse Proxy](../install/reverse-proxy) für die Einrichtung.

### Interne Kommunikation {#internal-communication}

| Von         | Nach      | Zweck                               |
| ----------- | --------- | ----------------------------------- |
| `backend`   | `mariadb` | Lesen/Schreiben von Kernentitäten   |
| `backend`   | `mongodb` | Schreiben von Aktivitäten und Logs  |
| `backend`   | `redis`   | Enqueue von Hintergrundaufgaben     |
| `worker`    | `mariadb` | Lesen/Schreiben bei Task-Ausführung |
| `worker`    | `redis`   | Abrufen von Jobs aus der Queue      |
| `scheduler` | `mariadb` | Abrufen von Jobs aus der Datenbank  |
| `scheduler` | `redis`   | Enqueue periodischer Tasks          |

### Externe Systeme {#external-systems}

OpenVLE kommuniziert mit folgenden externen Systemen:

| System                                       | Richtung                   | Protokoll         | Zweck                                                       |
| -------------------------------------------- | -------------------------- | ----------------- | ----------------------------------------------------------- |
| **Proxmox VE**                               | Backend/Worker → Proxmox   | HTTPS (8006/tcp)  | VM-Verwaltung über Proxmox-API                              |
| **SMTP-Server**                              | Backend/Worker → SMTP      | SSL/TLS (465/tcp) | E-Mail-Versand                                              |
| **Apache Guacamole** _(optional, empfohlen)_ | Backend/Worker → Guacamole | HTTPS (443/tcp)   | Verbindungsverwaltung über Guacamole-API                    |
| **Moodle** _(optional)_                      | Backend/Worker → Moodle    | HTTPS (443/tcp)   | Kurs- und Teilnehmerverwaltung über Moodle Web Services API |
| **LDAP-Server** _(optional)_                 | Backend/Worker → LDAP      | LDAP(S) (389/636) | Benutzer-Authentifizierung                                  |
| **OIDC-Provider** _(optional)_               | Backend → OIDC             | HTTPS (443/tcp)   | Single Sign-On                                              |

:::info Firewall-Regeln
Der OpenVLE-Server muss ausgehende Verbindungen zu den oben genannten externen Systemen herstellen können. Stelle sicher, dass die entsprechenden Ports in der Firewall freigegeben sind.
:::
