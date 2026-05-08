---
id: updates
sidebar_label: Updates
sidebar_position: 30
status: finished
tags:
  - operations
  - updates
---

# Updates {#updates}

Updates werden über neue Docker-Images ausgeliefert. Backend, Frontend und alle Worker teilen sich ein gemeinsames Repository und werden gemeinsam aktualisiert.

:::caution Vor jedem Update
Erstelle ein Backup aller Datenbanken, bevor du ein Update durchführst. Siehe [Backups & Wiederherstellung](backups-restore).
:::

## Ablauf {#procedure}

1. **Backup erstellen** — siehe [Backups & Wiederherstellung](backups-restore)
2. **Neue Images herunterladen:**
   ```bash
   docker compose pull
   ```
3. **Container neu starten:**
   ```bash
   docker compose down && docker compose up -d
   ```
4. **Status prüfen:**
   ```bash
   docker ps -a
   ```
   Alle Container sollten den Status `Running (healthy)` haben.
5. **Logs prüfen** — siehe [Logging](logs)

## Datenbank-Migrationen {#migrations}

Das Backend führt beim Start automatisch ausstehende Datenbank-Migrationen durch. Welcher Container die Migration ausführt (Backend oder Worker), wird über einen Lock-Mechanismus gesteuert — siehe [Datenbanken — Initialisierung](../infrastructure/databases#mariadb-init).

Prüfe nach dem Start die Logs auf erfolgreiche Migrationen:

```bash
docker logs openvle-backend 2>&1 | head -50
```

## Apache Guacamole {#guacamole}

Apache Guacamole wird als separater Docker-Stack betrieben und unabhängig von OpenVLE aktualisiert.

:::caution Datenbank-Schema
Bei Major-Version-Updates von Guacamole kann eine manuelle Aktualisierung des Datenbank-Schemas erforderlich sein. Prüfe die Apache Guacamole Release Notes auf Schema-Änderungen und führe ggf. die bereitgestellten Upgrade-Skripte aus.
:::

## Frontend-Cache {#frontend-cache}

:::note Browser-Cache
Nach einem Update kann es notwendig sein, den Browser-Cache zu leeren, damit die neuen Frontend-Dateien geladen werden.
:::
