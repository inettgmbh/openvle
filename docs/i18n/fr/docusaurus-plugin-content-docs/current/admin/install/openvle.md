---
id: openvle
sidebar_label: OpenVLE
sidebar_position: 40
status: finished
tags:
  - installation
  - docker
  - backend
  - frontend
---

# OpenVLE {#openvle}

OpenVLE fonctionne sous forme de stack Docker Compose et regroupe tous les services nécessaires dans un seul dépôt. Un `docker compose up -d` démarre l'ensemble de l'application.

## Architecture {#architecture}

Le stack Docker Compose se compose des services suivants :

| Service     | Fonction                                                                              |
| ----------- | ------------------------------------------------------------------------------------- |
| `backend`   | Python/FastAPI — serveur API, logique métier                                          |
| `frontend`  | Vue.js/Nginx — interface web                                                          |
| `worker`    | RQ Worker — tâches asynchrones en arrière-plan (opérations VM, envoi d'e-mails, etc.) |
| `scheduler` | RQ Scheduler — tâches périodiques (mises à jour des informations de nœud, etc.)       |
| `mariadb`   | MariaDB — base de données relationnelle pour les entités principales                  |
| `mongodb`   | MongoDB — base de données documentaire pour les activités et les journaux             |
| `redis`     | Redis — file d'attente de tâches et cache pour le Worker/Scheduler                    |

## Prérequis {#prerequisites}

- [Docker et Docker Compose](requirements) installés
- [Proxmox VE](proxmoxve) configuré (nécessaire pour la gestion des VM)
- Un serveur SMTP pour l'envoi d'e-mails (identifiants à disposition)
- Optionnel : [Apache Guacamole](guacamole) pour l'accès bureau à distance

## Installation {#installation}

### Télécharger le dépôt {#download}

Téléchargez les fichiers `docker-compose.yml` et `.env.sample` depuis le dépôt officiel :

```bash
mkdir openvle && cd openvle
curl -fsSLO https://raw.githubusercontent.com/inettgmbh/openvle/main/docker-compose.yml
curl -fsSL -o .env         https://raw.githubusercontent.com/inettgmbh/openvle/main/backend/.env.sample
curl -fsSL -o frontend.env https://raw.githubusercontent.com/inettgmbh/openvle/main/frontend/.env.sample
```

### Télécharger les images Docker {#pull}

```bash
docker compose pull
```

### Configuration {#configuration}

OpenVLE utilise deux fichiers de configuration au niveau racine : `.env` pour le backend, les workers, le scheduler et l'interpolation des variables Compose, et `frontend.env` pour la configuration runtime du frontend.

#### Backend (`.env`) {#configure-backend}

Générez d'abord des mots de passe et des secrets aléatoires et sécurisés pour toutes les variables liées à la sécurité :

```bash
sed -i \
  -e "s|AUTH_SECRET = \"\"|AUTH_SECRET = \"$(openssl rand -hex 32)\"|" \
  -e "s|SESSION_SECRET_TOKEN = \"\"|SESSION_SECRET_TOKEN = \"$(openssl rand -hex 32)\"|" \
  -e "s|MARIADB_PASSWORD = \"project\"|MARIADB_PASSWORD = \"$(openssl rand -hex 16)\"|" \
  -e "s|MARIADB_ROOT_PASSWORD = \"root\"|MARIADB_ROOT_PASSWORD = \"$(openssl rand -hex 16)\"|" \
  -e "s|MONGODB_PASSWORD = \"project\"|MONGODB_PASSWORD = \"$(openssl rand -hex 16)\"|" \
  -e "s|REDIS_PASSWORD = \"password\"|REDIS_PASSWORD = \"$(openssl rand -hex 16)\"|" \
  .env
```

:::caution
Cette commande remplace les mots de passe par défaut par des valeurs aléatoires une seule fois. Exécutez-la **une seule fois** — lors d'une exécution ultérieure, les valeurs déjà définies ne correspondraient plus aux valeurs par défaut et la commande n'aurait aucun effet. Sauvegardez ensuite le fichier `.env` généré, car les mots de passe ne sont pas récupérables.

Si vous ne souhaitez pas utiliser la commande `sed`, vous devez **impérativement définir manuellement** les variables suivantes sur des valeurs sécurisées : `AUTH_SECRET`, `SESSION_SECRET_TOKEN`, `MARIADB_PASSWORD`, `MARIADB_ROOT_PASSWORD`, `MONGODB_PASSWORD`, `REDIS_PASSWORD`. Les valeurs par défaut du fichier `.env.sample` ne sont pas sécurisées et ne doivent pas être utilisées en production.
:::

:::note MARIADB_ROOT_PASSWORD
`MARIADB_ROOT_PASSWORD` n'est nécessaire que lors du **premier démarrage** — MariaDB reprend le mot de passe lors de la première initialisation et le stocke dans la base de données. Après le premier démarrage réussi, vous pouvez supprimer la variable du fichier `.env` et conserver le mot de passe dans un endroit sécurisé (par exemple un gestionnaire de mots de passe), au cas où vous en auriez besoin pour des travaux de maintenance ou en cas d'erreur.
:::

Éditez ensuite le fichier `.env` et définissez les variables spécifiques à votre environnement :

**CORS**

| Variable       | Description                                                  | Exemple                           |
| -------------- | ------------------------------------------------------------ | --------------------------------- |
| `CORS_ORIGINS` | Origines autorisées pour les requêtes CORS (URL du frontend) | `["https://openvle.example.com"]` |

**Proxmox VE** — Identifiants issus de l'[intégration Proxmox VE](proxmoxve)

| Variable          | Description                           | Exemple                                  |
| ----------------- | ------------------------------------- | ---------------------------------------- |
| `PVE_HOSTNAME`    | Nom d'hôte et port du serveur Proxmox | `"proxmox.example.com:8006"`             |
| `PVE_USER`        | Utilisateur Proxmox                   | `"OpenVLE@pve"`                          |
| `PVE_TOKEN_NAME`  | Nom du jeton API                      | `"prod01"`                               |
| `PVE_TOKEN_VALUE` | Valeur secrète du jeton API           | `"xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"` |
| `PVE_FQDN`        | FQDN du serveur Proxmox               | `"proxmox.example.com:8006"`             |
| `PVE_VMS_POOL`    | Pool Proxmox pour les VM gérées       | `"OpenVLE-VMs"`                          |
| `PVE_VM_SUBNET`   | Sous-réseau pour les VM               | `"10.1.1.0/24"`                          |

**E-mail / SMTP**

| Variable         | Description                     | Exemple                 |
| ---------------- | ------------------------------- | ----------------------- |
| `SMTP_HOST`      | Serveur SMTP                    | `"mail.example.com"`    |
| `SMTP_PORT`      | Port SMTP                       | `465`                   |
| `SMTP_METHOD`    | Méthode de connexion            | `"ssl"`                 |
| `SMTP_USERNAME`  | Nom d'utilisateur SMTP          | `"openvle@example.com"` |
| `SMTP_PASSWORD`  | Mot de passe SMTP               | `"smtp-passwort"`       |
| `SMTP_FROM_MAIL` | Adresse de l'expéditeur         | `"openvle@example.com"` |
| `SMTP_FROM_NAME` | Nom d'affichage de l'expéditeur | `"OpenVLE"`             |

:::info
Les variables doivent être définies entre **guillemets (`" "`)**, sans quoi des erreurs d'analyse se produiront au démarrage.
:::

:::note Référence complète
Le tableau ci-dessus ne montre que les variables requises. Pour les paramètres optionnels (Guacamole, LDAP, OIDC, Moodle, Sentry, etc.), consultez la [référence de configuration](configuration).
:::

#### Frontend (`frontend.env`) {#configure-frontend}

Pour le frontend, seule l'URL du backend doit être définie :

```bash
VITE_BACKEND_URL='https://openvle.example.com/v1'
```

Vous trouverez d'autres variables optionnelles pour le frontend (par exemple Sentry) dans la [référence de configuration](configuration?stack=frontend).

### Démarrer les conteneurs {#start}

```bash
docker compose up -d
```

Docker crée automatiquement tous les répertoires nécessaires, initialise les bases de données et démarre tous les services.

:::caution Premier démarrage
Lors du premier démarrage, le backend effectue automatiquement la migration de la base de données. Cela peut prendre quelques minutes. Attendez que tous les conteneurs aient atteint le statut `healthy` avant de poursuivre.
:::

### Réseau et ports {#ports}

Dans le fichier `docker-compose.yml` par défaut, seuls deux ports sont exposés vers l'extérieur :

| Service    | Port | Liaison        |
| ---------- | ---- | -------------- |
| `frontend` | 80   | `0.0.0.0:80`   |
| `backend`  | 8000 | `0.0.0.0:8000` |

Tous les autres conteneurs (MariaDB, MongoDB, Redis, Worker, Scheduler) communiquent exclusivement en interne via le réseau Docker et n'exposent aucun port — et cela doit rester ainsi.

:::note Utiliser un reverse proxy
Lorsqu'un [reverse proxy](reverse-proxy) est utilisé (recommandé), les publications de ports du frontend et du backend peuvent être supprimées ou restreintes à `127.0.0.1` dans le fichier `docker-compose.yml`, car tout l'accès externe passe alors de manière centralisée par le reverse proxy. Exemple :

```yaml
ports:
  - 127.0.0.1:80:80 # accessible uniquement en local
  - 127.0.0.1:8000:8000
```

:::

### Administrateur par défaut {#default-admin}

Après le premier démarrage réussi, un compte administrateur par défaut est automatiquement créé :

|                       |           |
| --------------------- | --------- |
| **Nom d'utilisateur** | `openvle` |
| **Mot de passe**      | `openvle` |

:::caution Changer le mot de passe immédiatement
Changez le mot de passe de l'administrateur par défaut **immédiatement** après la première connexion. Créez ensuite un compte personnel pour chaque administrateur et désactivez ou supprimez le compte par défaut dès que les comptes individuels sont configurés.
:::

## Vérification {#verification}

### Vérifier le statut des conteneurs {#verify-containers}

```bash
docker ps -a
```

Les 7 conteneurs devraient tous avoir le statut `Running (healthy)`.

### Vérifier les journaux {#verify-logs}

```bash
docker logs openvle-backend 2>&1 | head -50
```

Les journaux ne devraient afficher aucun message d'erreur et devraient confirmer la connexion réussie à la base de données.

### Tester l'accès à l'API {#verify-api}

Récupérez les paramètres système via l'API :

```bash
curl -s https://openvle.example.com/v1/system/settings | head -20
```

Une réponse JSON contenant les paramètres actuels confirme que le backend et le reverse proxy sont correctement configurés. Une réponse vide ou erronée indique un problème de configuration.

### Vérifier l'interface web {#verify-frontend}

Ouvrez `https://openvle.example.com` dans votre navigateur. La page de connexion devrait s'afficher.

## Dépannage {#troubleshooting}

| Problème                               | Solution                                                                                                                                               |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Le conteneur ne démarre pas            | Vérifiez les journaux avec `docker logs <container-name>`. Plus d'informations sous [Journaux](../operations/logs).                                    |
| Erreur de base de données au démarrage | Assurez-vous que les variables MariaDB et MongoDB dans le fichier `.env` sont correctement définies. Voir [Référence de configuration](configuration). |
| Le health check échoue                 | Patientez quelques minutes — la migration initiale de la base de données peut prendre plus de temps lors du premier démarrage.                         |
| Interface web inaccessible             | Assurez-vous que le conteneur frontend est en cours d'exécution et que le [reverse proxy](reverse-proxy) est correctement configuré.                   |
| Les appels API échouent                | Vérifiez `CORS_ORIGINS` dans le fichier `.env` — l'URL du frontend doit y figurer.                                                                     |
| L'envoi d'e-mails ne fonctionne pas    | Vérifiez les variables SMTP dans le fichier `.env` et testez la connexion au serveur SMTP.                                                             |
| La connexion Proxmox échoue            | Vérifiez `PVE_HOSTNAME`, `PVE_USER`, `PVE_TOKEN_NAME` et `PVE_TOKEN_VALUE`. Voir [Intégration Proxmox VE](proxmoxve).                                  |
