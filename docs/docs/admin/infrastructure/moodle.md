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

OpenVLE kann mit einer bestehenden Moodle-Instanz verbunden werden, um Lernumgebungen automatisch bereitzustellen. Dabei werden Moodle-Kurse dupliziert, Teilnehmer synchronisiert und Einschreibungen verwaltet — alles gesteuert durch den Lebenszyklus von Veranstaltungen in OpenVLE.

:::info Optional
Die Moodle-Integration ist vollständig optional. Bei Nichtverwendung werden sämtliche Moodle-bezogenen Elemente in der Benutzeroberfläche nicht angezeigt. Die Integration ist standardmäßig deaktiviert.
:::

## Architektur {#architecture}

OpenVLE kommuniziert mit Moodle ausschließlich über die **Moodle Web Services REST-API**. Es gibt keine direkte Datenbankverbindung — alle Operationen erfolgen über HTTP-API-Aufrufe.

| Komponente              | Rolle                                                                         |
| ----------------------- | ----------------------------------------------------------------------------- |
| **OpenVLE Backend**     | Ruft Moodle-Kurse ab und prüft Benutzer                                       |
| **OpenVLE Worker**      | Führt Kurs-Duplikation, Benutzer-Erstellung und Einschreibungen asynchron aus |
| **Moodle Web Services** | Empfängt API-Anfragen und führt die Operationen in Moodle aus                 |

:::note Netzwerkzugriff
Das OpenVLE-Backend muss ausgehende HTTPS-Verbindungen zur Moodle-Instanz herstellen können. Die Authentifizierung erfolgt über ein Moodle-API-Token.
:::

## Konzept: Kurs-Zuordnung {#course-mapping}

Die Integration basiert auf der Zuordnung von Moodle-Kursen zu OpenVLE-Umgebungen:

1. **Umgebung** — Eine OpenVLE-Umgebung kann mit einem Moodle-Kurs verknüpft werden. Dieser Moodle-Kurs dient als **Vorlage**.
2. **Veranstaltung** — Wird eine Veranstaltung aus dieser Umgebung gestartet, dupliziert OpenVLE den Moodle-Vorlagenkurs automatisch. Jede Veranstaltung erhält ihren eigenen Moodle-Kurs.

## Lebenszyklus einer Veranstaltung {#event-lifecycle}

Die Moodle-Aktionen sind an den Lebenszyklus einer Veranstaltung gebunden:

| Phase                     | Moodle-Aktion                                                               |
| ------------------------- | --------------------------------------------------------------------------- |
| **Deployment**            | Vorlagenkurs wird dupliziert, Teilnehmer werden erstellt und eingeschrieben |
| **Teilnehmer hinzufügen** | Benutzer wird bei Bedarf in Moodle erstellt und in den Kurs eingeschrieben  |
| **Teilnehmer entfernen**  | Benutzer wird aus dem Moodle-Kurs ausgeschrieben                            |
| **Veranstaltungsende**    | Studierende werden ausgeschrieben, Lehrende bleiben, Kurs wird unsichtbar   |
| **Veranstaltung löschen** | Moodle-Kurs wird optional gelöscht (konfigurierbar)                         |

### Benutzer-Synchronisation {#user-sync}

Beim Deployment prüft OpenVLE für jeden Teilnehmer, ob ein entsprechender Benutzer in Moodle existiert. Der Abgleich erfolgt über das konfigurierte Feld (`MOODLE_USER_MATCH_FIELD` — entweder `email` oder `username`). Wird kein Moodle-Benutzer gefunden, erstellt OpenVLE automatisch einen neuen.

### Rollen-Zuordnung {#role-mapping}

OpenVLE bildet die Teilnehmer-Rollen auf Moodle-Kursrollen ab:

| OpenVLE-Rolle | Moodle-Rolle                |
| ------------- | --------------------------- |
| Lehrende      | Editing Teacher (Role ID 3) |
| Studierende   | Student (Role ID 5)         |

:::caution Datenverlust bei Ausschreibung
Beim Ausschreiben eines Teilnehmers gehen Abgaben, Noten und Lernfortschritt im Moodle-Kurs verloren. Dies ist eine Einschränkung der Moodle-REST-API (siehe [MDL-70582](https://tracker.moodle.org/browse/MDL-70582)).
:::

## Weiterführende Informationen {#further-reading}

- [Moodle konfigurieren](../install/moodle) — Einrichtung, Konfiguration und Fehlerbehebung
- [Konfigurationsreferenz](../install/configuration) — Alle Moodle-Umgebungsvariablen
