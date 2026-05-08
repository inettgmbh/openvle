---
id: networking
sidebar_label: Réseau & Docker
sidebar_position: 25
status: finished
tags:
  - infrastructure
  - networking
  - docker
---

# Réseau & Docker {#networking}

Tous les services OpenVLE fonctionnent dans des conteneurs Docker et communiquent via un réseau Docker interne. Seuls quelques ports sont publiés vers l'extérieur. Pour la production, un reverse proxy en amont est recommandé, mais pas strictement obligatoire.

## Réseau Docker {#docker-network}

Le stack Docker Compose crée automatiquement un réseau interne (`openvle-internal`). Tous les conteneurs sont connectés entre eux via ce réseau et peuvent se joindre mutuellement par leurs noms de service (par exemple `backend`, `mariadb`, `redis`).

:::note Résolution DNS
Docker Compose fournit une résolution DNS interne : les conteneurs peuvent contacter d'autres conteneurs en utilisant le nom du service comme nom d'hôte. C'est pourquoi les variables d'environnement contiennent par exemple `MARIADB_HOST = "db"` au lieu d'une adresse IP.
:::

## Ports exposés {#exposed-ports}

Dans le fichier `docker-compose.yml` standard, seuls deux ports sont publiés vers l'extérieur :

| Service    | Port conteneur | Port hôte | Fonction                     |
| ---------- | -------------- | --------- | ---------------------------- |
| `frontend` | 80             | 80        | Interface web (Vue.js/Nginx) |
| `backend`  | 80             | 8000      | API REST (FastAPI)           |

Les deux services doivent être accessibles depuis le navigateur de l'utilisateur final : le Frontend sert l'interface web, et le navigateur communique directement avec le Backend à l'exécution (requêtes API).

Tous les autres services (MariaDB, MongoDB, Redis, Worker, Scheduler) ne publient **aucun port** et ne sont accessibles qu'en interne.

:::note Reverse Proxy (recommandé)
Lorsqu'un [Reverse Proxy](../install/reverse-proxy) est utilisé, les publications de ports doivent être restreintes à `127.0.0.1`, car l'accès externe passe alors par le proxy :

```yaml
ports:
  - 127.0.0.1:80:80
  - 127.0.0.1:8000:8000
```

:::

## Chemins de communication {#communication-paths}

### Accès externe {#external-access}

**Avec Reverse Proxy (recommandé) :**

```
Browser → Reverse Proxy → Frontend (Port 80)
Browser → Reverse Proxy → Backend (Port 8000)
```

**Sans Reverse Proxy :**

```
Browser → Frontend (Port 80)
Browser → Backend (Port 8000)
```

Un reverse proxy est optionnel, mais recommandé pour la production — il prend en charge la terminaison SSL, le routage et éventuellement la répartition de charge. Consultez [Reverse Proxy](../install/reverse-proxy) pour la mise en place.

### Communication interne {#internal-communication}

| De          | Vers      | Fonction                                          |
| ----------- | --------- | ------------------------------------------------- |
| `backend`   | `mariadb` | Lecture/écriture des entités principales          |
| `backend`   | `mongodb` | Écriture des activités et des journaux            |
| `backend`   | `redis`   | Mise en file d'attente des tâches en arrière-plan |
| `worker`    | `mariadb` | Lecture/écriture lors de l'exécution des tâches   |
| `worker`    | `redis`   | Récupération des jobs depuis la file d'attente    |
| `scheduler` | `mariadb` | Récupération des jobs depuis la base de données   |
| `scheduler` | `redis`   | Mise en file d'attente des tâches périodiques     |

### Systèmes externes {#external-systems}

OpenVLE communique avec les systèmes externes suivants :

| Système                                        | Direction                  | Protocole         | Fonction                                                            |
| ---------------------------------------------- | -------------------------- | ----------------- | ------------------------------------------------------------------- |
| **Proxmox VE**                                 | Backend/Worker → Proxmox   | HTTPS (8006/tcp)  | Gestion des VMs via l'API Proxmox                                   |
| **Serveur SMTP**                               | Backend/Worker → SMTP      | SSL/TLS (465/tcp) | Envoi d'e-mails                                                     |
| **Apache Guacamole** _(optionnel, recommandé)_ | Backend/Worker → Guacamole | HTTPS (443/tcp)   | Gestion des connexions via l'API Guacamole                          |
| **Moodle** _(optionnel)_                       | Backend/Worker → Moodle    | HTTPS (443/tcp)   | Gestion des cours et des participants via l'API Moodle Web Services |
| **Serveur LDAP** _(optionnel)_                 | Backend/Worker → LDAP      | LDAP(S) (389/636) | Authentification des utilisateurs                                   |
| **Fournisseur OIDC** _(optionnel)_             | Backend → OIDC             | HTTPS (443/tcp)   | Single Sign-On                                                      |

:::info Règles de pare-feu
Le serveur OpenVLE doit pouvoir établir des connexions sortantes vers les systèmes externes mentionnés ci-dessus. Assurez-vous que les ports correspondants sont ouverts dans le pare-feu.
:::
