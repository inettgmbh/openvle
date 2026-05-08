---
id: updates
sidebar_label: Mises à jour
sidebar_position: 30
status: finished
tags:
  - operations
  - updates
---

# Mises à jour {#updates}

Les mises à jour sont distribuées via de nouvelles images Docker. Le backend, le frontend et tous les workers partagent un dépôt commun et sont mis à jour simultanément.

:::caution Avant chaque mise à jour
Créez une sauvegarde de toutes les bases de données avant d'effectuer une mise à jour. Voir [Sauvegardes et restauration](backups-restore).
:::

## Procédure {#procedure}

1. **Créer une sauvegarde** — voir [Sauvegardes et restauration](backups-restore)
2. **Télécharger les nouvelles images :**
   ```bash
   docker compose pull
   ```
3. **Redémarrer les conteneurs :**
   ```bash
   docker compose down && docker compose up -d
   ```
4. **Vérifier le statut :**
   ```bash
   docker ps -a
   ```
   Tous les conteneurs doivent afficher le statut `Running (healthy)`.
5. **Vérifier les journaux** — voir [Journalisation](logs)

## Migrations de base de données {#migrations}

Le backend exécute automatiquement les migrations de base de données en attente au démarrage. Le conteneur qui effectue la migration (backend ou worker) est déterminé par un mécanisme de verrouillage — voir [Bases de données — Initialisation](../infrastructure/databases#mariadb-init).

Vérifiez les journaux après le démarrage pour confirmer la réussite des migrations :

```bash
docker logs openvle-backend 2>&1 | head -50
```

## Apache Guacamole {#guacamole}

Apache Guacamole est exploité comme un stack Docker séparé et est mis à jour indépendamment d'OpenVLE.

:::caution Schéma de base de données
Lors des mises à jour de version majeure de Guacamole, une mise à jour manuelle du schéma de base de données peut être nécessaire. Consultez les notes de version d'Apache Guacamole pour les modifications de schéma et exécutez les scripts de mise à niveau fournis si nécessaire.
:::

## Cache du frontend {#frontend-cache}

:::note Cache du navigateur
Après une mise à jour, il peut être nécessaire de vider le cache du navigateur pour que les nouveaux fichiers du frontend soient chargés.
:::
