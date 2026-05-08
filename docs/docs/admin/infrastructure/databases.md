---
id: databases
sidebar_label: Datenbanken
sidebar_position: 30
status: finished
tags:
  - infrastructure
  - databases
---

# Datenbanken {#databases}

OpenVLE nutzt drei verschiedene Datenbanksysteme, die jeweils auf unterschiedliche Aufgaben spezialisiert sind: MariaDB für strukturierte Kerndaten, MongoDB für Aktivitäten und Logs sowie Redis als Task-Queue und Cache.

## Übersicht {#overview}

| Datenbank   | Typ                     | Gespeicherte Daten                                                                             | Persistenz                        |
| ----------- | ----------------------- | ---------------------------------------------------------------------------------------------- | --------------------------------- |
| **MariaDB** | Relational (SQL)        | Kernentitäten: Benutzer, Rollen, Berechtigungen, Umgebungen, Veranstaltungen, VMs, VM-Vorlagen | Volume `./mariadb/data`           |
| **MongoDB** | Dokumentbasiert (NoSQL) | Aktivitäten, System-Events, Audit-Logs, Änderungsverläufe                                      | Volume `./mongodb`                |
| **Redis**   | In-Memory (Key-Value)   | Task-Queue, Cache, Worker/Scheduler-Kommunikation                                              | AOF-Persistenz (`appendonly yes`) |

## MariaDB {#mariadb}

MariaDB ist die primäre Datenbank und speichert alle strukturierten Kernentitäten des Systems:

- **Benutzer und Rollen** — Konten, Rollenzuweisungen, Passwort-Hashes
- **Berechtigungen** — Berechtigungsdefinitionen und Zuordnungen (siehe [Berechtigungssystem](permission-system))
- **Umgebungen und Veranstaltungen** — Kursumgebungen, Veranstaltungstermine, Teilnehmerzuordnungen
- **VMs und VM-Vorlagen** — Virtuelle Maschinen, deren Status und Zuordnung zu Veranstaltungen
- **Systemeinstellungen** — Globale Konfiguration und Einstellungen

### Initialisierung und Migration {#mariadb-init}

Beim ersten Start übernehmen die Backend- und Worker-Container automatisch die Datenbank-Initialisierung und -Migration. Welcher Container die Migration durchführt, wird über einen Lock-Mechanismus gesteuert — der Container, der den Lock zuerst erhält, führt die Migration aus. Dabei werden das Datenbankschema erstellt und initiale Daten angelegt (z. B. der Standard-Administrator-Account und die Standard-Berechtigungen).

## MongoDB {#mongodb}

MongoDB speichert nicht-relationale Daten, die keine feste Tabellenstruktur erfordern:

- **Aktivitäten** — Benutzeraktionen (z. B. "Benutzer X hat VM Y gestartet"), die in der Aktivitätsübersicht der Benutzeroberfläche angezeigt werden

Der Zugriff erfolgt ausschließlich über das Backend. MongoDB ist nicht direkt von außen erreichbar.

## Redis {#redis}

Redis dient nicht als klassische Datenbank, sondern als Kommunikationsschicht zwischen den Anwendungskomponenten:

- **Task-Queue** — Das Backend reiht Aufgaben in Redis-Queues ein, die vom Worker abgearbeitet werden (siehe [Task-System](task-system))
- **Scheduler-Queue** — Der Scheduler legt periodische Aufgaben in Redis ab
- **Cache** — Temporäre Zwischenspeicherung für häufig abgerufene Daten

Redis ist mit AOF (Append Only File) konfiguriert, sodass die Queue-Daten auch nach einem Neustart erhalten bleiben. Der Zugriff ist passwortgeschützt.

## Abgrenzung der Datenbanken {#separation}

Die Aufteilung auf drei Systeme folgt dem Prinzip, jede Datenbank für ihren Stärkenbereich einzusetzen:

| Anforderung                        | Datenbank | Begründung                                            |
| ---------------------------------- | --------- | ----------------------------------------------------- |
| Strukturierte Daten mit Relationen | MariaDB   | Fremdschlüssel, Transaktionen, ACID-Garantien         |
| Flexible, schemalose Dokumente     | MongoDB   | Variierende Dokumentstrukturen, effizientes Logging   |
| Schnelle Queue-Operationen         | Redis     | In-Memory-Geschwindigkeit, native Queue-Unterstützung |

## Weiterführende Informationen {#further-reading}

- [Konfigurationsreferenz — MariaDB](../install/configuration#mariadb) — Alle MariaDB-Umgebungsvariablen
- [Konfigurationsreferenz — MongoDB](../install/configuration#mongodb) — Alle MongoDB-Umgebungsvariablen
- [Konfigurationsreferenz — Redis](../install/configuration#redis) — Alle Redis-Umgebungsvariablen
- [Backups & Restore](../operations/backups-restore) — Sicherung und Wiederherstellung der Datenbanken
