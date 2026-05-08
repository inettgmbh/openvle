---
id: requirements
sidebar_label: Anforderungen
sidebar_position: 11
status: finished
tags:
  - installation
  - requirements
---

# Anforderungen {#requirements}

Zum Betrieb von OpenVLE ist ein dedizierter Server notwendig.

Da OpenVLE Proxmox VE als Hypervisor voraussetzt (siehe [Proxmox VE Integration](proxmoxve)), empfehlen wir, OpenVLE als virtuelle Maschine direkt auf dem Proxmox-Host zu betreiben. Dadurch entfällt zusätzliche Hardware, und Backups sowie Snapshots der OpenVLE-VM können über Proxmox selbst erfolgen.

:::tip Trennung von Produktiv-VMs
Lege die OpenVLE-VM außerhalb des in Proxmox angelegten Pools `OpenVLE-VMs` an, damit sie nicht von OpenVLE selbst verwaltet wird.
:::

## Ressourcen {#resources}

Die benötigten Ressourcen hängen von der späteren Last der OpenVLE-Verwaltungsoberfläche ab. Je mehr Nutzer gleichzeitig zugreifen, desto mehr Ressourcen werden benötigt. Für den Start empfehlen wir folgende Ausstattung der VM:

- 4 CPU-Cores
- 8 GB Arbeitsspeicher
- 50 GB Festplattenspeicher

## Betriebssystem {#operating-system}

Offiziell unterstützt werden alle Linux-Distributionen, auf denen Docker offiziell installiert werden kann. Damit sind die gängigsten Distributionen wie Ubuntu, Debian und Red Hat Enterprise Linux abgedeckt.

## Installation von Docker (Compose) {#install-docker}

Zuerst muss auf dem Server die aktuelle offizielle Version von `docker` und `docker compose` installiert werden.

Der schnellste Weg ist das offizielle Convenience Script von Docker, das alle unterstützten Distributionen automatisch erkennt und Docker inklusive Compose V2 installiert:

```bash
curl -fsSL https://get.docker.com | sh
```

:::caution Produktionsumgebung
Das Convenience Script ist für die schnelle Einrichtung gedacht. Für Produktionsumgebungen mit besonderen Anforderungen (z. B. eigene Repositories, Proxy-Konfiguration, spezifische Versionen) empfehlen wir die manuelle Installation gemäß der [offiziellen Docker-Dokumentation](https://docs.docker.com/engine/install/).
:::

### Verifizierung {#verify-docker}

Prüfe nach der Installation, ob Docker und Compose korrekt installiert sind:

```bash
docker --version
docker compose version
```

Beide Befehle sollten eine Versionsnummer ausgeben. Teste zusätzlich, ob Docker funktionsfähig ist:

```bash
docker run --rm hello-world
```

## Fehlerbehebung {#troubleshooting}

| Problem                                 | Lösung                                                                                                           |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `docker compose` nicht gefunden         | Stelle sicher, dass Docker Compose V2 installiert ist (als Docker-Plugin, nicht als separates `docker-compose`). |
| Berechtigungsfehler bei Docker-Befehlen | Füge deinen Benutzer zur Gruppe `docker` hinzu: `sudo usermod -aG docker $USER` und melde dich neu an.           |
