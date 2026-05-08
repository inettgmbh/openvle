---
id: proxmoxve
sidebar_label: Proxmox VE Integration
sidebar_position: 20
status: finished
tags:
  - installation
  - proxmox
format: md
---

# Proxmox VE — Integration {#proxmox-ve-integration}

Diese Anleitung beschreibt die Schritte zur Integration von OpenVLE mit Proxmox VE (PVE), einschließlich der Einrichtung von Benutzern, Berechtigungen und API-Zugang.

:::caution Erforderliche Komponente
Proxmox VE ist eine Kernabhängigkeit von OpenVLE. Ohne korrekte Proxmox-Konfiguration startet die Anwendung zwar, aber sämtliche Aktionen mit VMs und VM-Vorlagen (Erstellen, Klonen, Starten, Stoppen, Löschen) schlagen fehl.
:::

## Proxmox-Benutzer und Token einrichten {#setup-user-and-token}

Für die Nutzung der Proxmox API müssen ein Pool, ein Benutzer, ein API-Token, Rollen und die entsprechenden Berechtigungen angelegt werden.

### Pool erstellen {#create-pool}

Erstelle einen Pool wie `OpenVLE-VMs`.  
Dieser Pool wird für alle von OpenVLE verwalteten Templates und VMs verwendet. Nur VMs und Templates in diesem Pool sind für OpenVLE sichtbar.

<details>
<summary>CLI-Befehl</summary>

```bash
pvesh create /pools --poolid 'OpenVLE-VMs'
```

</details>

<details>
<summary>WebGUI</summary>

```bash
Datacenter -> Permissions -> Pools -> Add
```

</details>

### Benutzerkonto erstellen {#create-user}

Erstelle einen Benutzer wie `OpenVLE@pve` — du kannst einen beliebigen Benutzernamen verwenden
(wir nutzen diesen als Referenz im Rest der Anleitung).  
Dieser Benutzer wird für alle Interaktionen von OpenVLE mit Proxmox verwendet. Es kann ein `@pve`-, `@pam`-, `@ldap`- oder ein beliebiges anderes Konto sein.  
Da OpenVLE sich über ein API-Token verbindet, spielt das Backend-Realm keine Rolle.  
Das Konto benötigt kein Passwort (Hinweis: Konten ohne Passwort können nur über die PVE-CLI erstellt werden, nicht über die WebGUI).  
Benutzerattribute wie `Vorname / Nachname`, `E-Mail` und `Kommentar` können beliebig gesetzt werden — sie sind für die Funktion von OpenVLE nicht relevant. Der Benutzer muss lediglich das Flag `Enabled` auf true gesetzt haben.

<details>
<summary>CLI-Befehl</summary>

```bash
pvesh create /access/users --userid 'OpenVLE@pve'
```

</details>

<details>
<summary>WebGUI</summary>

```bash
Datacenter -> Permissions -> Users -> Add
```

</details>

### API-Token generieren {#generate-api-token}

Generiere ein API-Token für den soeben erstellten Benutzer.  
Als `Token ID` kannst du eine beliebige ID wählen — wir verwenden hier `prod01`.  
Setze `Privilege Separation` auf **true**.  
Notiere dir die Token-Details, da sie nur einmal angezeigt werden.

:::note Warum Privilege Separation?
Ohne Privilege Separation erbt ein API-Token automatisch alle Berechtigungen seines Benutzers. Mit aktivierter Privilege Separation hingegen hat ein Token nur die Berechtigungen, die ihm **explizit** zugewiesen wurden.

Das ermöglicht es, mit einem einzigen Proxmox-Benutzer mehrere OpenVLE-Instanzen isoliert zu betreiben: Erstelle für jede Instanz (z. B. Produktion, Staging, Testing) ein eigenes API-Token und weise jedem Token nur den jeweiligen VM-Pool zu. So kann eine Staging-Instanz ausschließlich auf ihre eigenen VMs zugreifen, ohne die Produktions-VMs zu sehen oder zu beeinflussen.

**Beispiel:** Ein Benutzer `OpenVLE@pve` mit zwei Tokens:

- `OpenVLE@pve!prod01` → Pool `OpenVLE-Prod` (Produktionsumgebung)
- `OpenVLE@pve!staging01` → Pool `OpenVLE-Staging` (Testumgebung)
  :::

<details>
<summary>CLI-Befehl</summary>

```bash
pvesh create /access/users/OpenVLE@pve/token/prod01
```

</details>

<details>
<summary>WebGUI</summary>

```bash
Datacenter -> Permissions -> API Tokens -> Add
```

</details>

### Zwei Rollen auf dem PVE erstellen {#create-roles}

Da der Benutzer und das API-Token unterschiedliche Berechtigungen auf verschiedenen Pfaden innerhalb von PVE benötigen, müssen zwei Rollen erstellt werden.

1. `OpenVLE-Infra-General` mit folgenden Privilegien:
   1. `Sys.Audit`
   2. `Sys.Console`
2. `OpenVLE-Infra-VMs` mit folgenden Privilegien:
   1. `VM.Allocate`
   2. `VM.Audit`
   3. `VM.Clone`
   4. `VM.Config.Disk`
   5. `VM.Config.CDROM`
   6. `VM.Config.CPU`
   7. `VM.Config.Memory`
   8. `VM.Config.Network`
   9. `VM.Config.HWType`
   10. `VM.Config.Options`
   11. `VM.Config.Cloudinit`
   12. `VM.GuestAudit`
   13. `VM.Migrate`
   14. `VM.Monitor`
   15. `VM.PowerMgmt`

:::note Proxmox VE < 9
Das Privileg `VM.GuestAudit` existiert erst ab Proxmox VE 9. Wenn du eine ältere Version einsetzt, lasse dieses Privileg weg.
:::

<details>
<summary>Wozu werden diese Privilegien benötigt?</summary>

**`OpenVLE-Infra-General`** — Wird auf Pfad `/` zugewiesen und ermöglicht systemweite Abfragen:

| Privileg                                                                                        | Verwendung in OpenVLE                                                                                         |
| ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Audit</code></a>   | Cluster-Status und -Ressourcen abfragen, Node-Statistiken abrufen, Task-Status prüfen, HA-Konfiguration lesen |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Console</code></a> | HA-Konfiguration für VMs erstellen, ändern und löschen                                                        |

**`OpenVLE-Infra-VMs`** — Wird auf den VM-Pool zugewiesen und ermöglicht die Verwaltung von VMs und Templates:

| Privileg                                                                                          | Verwendung in OpenVLE                                                                   |
| ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Allocate</code></a>   | VMs und Templates erstellen und löschen                                                 |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Audit</code></a>      | VM-Status und -Konfiguration abfragen, CloudInit-Konfiguration regenerieren             |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Clone</code></a>      | VMs und Templates klonen                                                                |
| `VM.Config.*`                                                                                     | VM-Konfiguration ändern (Disk, CDROM, CPU, Memory, Network, HWType, Options, Cloudinit) |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.GuestAudit</code></a> | Guest-Agent-Abfragen und -Befehle ausführen (ab PVE 9, bei PVE < 9 weglassen)           |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Migrate</code></a>    | VMs zwischen Nodes migrieren                                                            |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Monitor</code></a>    | Netzwerk-Interfaces auslesen (z. B. IPv4-Adresse einer VM ermitteln)                    |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.PowerMgmt</code></a>  | VMs starten, stoppen, neu starten, herunterfahren, pausieren und fortsetzen             |

</details>

<details>
<summary>CLI-Befehl</summary>

```bash
pvesh create /access/roles --roleid 'OpenVLE-Infra-General' --privs 'Sys.Audit,Sys.Console'
pvesh create /access/roles --roleid 'OpenVLE-Infra-VMs' --privs 'VM.Allocate, VM.Audit, VM.Clone, VM.Config.Disk, VM.Config.CDROM, VM.Config.CPU, VM.Config.Memory, VM.Config.Network, VM.Config.HWType, VM.Config.Options, VM.Config.Cloudinit, VM.GuestAudit, VM.Migrate, VM.Monitor, VM.PowerMgmt'
```

</details>

<details>
<summary>WebGUI</summary>

```bash
Datacenter -> Permissions -> Roles -> Create
```

</details>

### Berechtigungen zuweisen {#assign-permissions}

Alle folgenden Berechtigungen müssen **sowohl** dem Benutzer (`OpenVLE@pve`) **als auch** dem API-Token (`OpenVLE@pve!prod01`) zugewiesen werden. Durch `Privilege Separation` validiert Proxmox die Berechtigungen beider Identitäten unabhängig voneinander — fehlt eine Zuweisung, schlagen die API-Aufrufe fehl.

#### Zugehörige Rollen zuweisen {#assign-roles}

Die zuvor erstellten Rollen müssen auf den jeweiligen Pfaden zugewiesen werden.

**1. Allgemeine Systemberechtigungen (`OpenVLE-Infra-General`)**

- Pfad: `/`
- Rolle: `OpenVLE-Infra-General`
- Propagate: True

Diese Zuweisung ermöglicht systemweite Operationen: Cluster-Status und -Ressourcen abfragen, Node-Statistiken abrufen, Task-Status prüfen sowie HA-Konfigurationen verwalten.

**2. VM-Berechtigungen im Pool (`OpenVLE-Infra-VMs`)**

- Pfad: `/pool/OpenVLE-VMs`
- Rolle: `OpenVLE-Infra-VMs`
- Propagate: True

Diese Zuweisung beschränkt die VM-Verwaltung auf den zuvor erstellten Pool. OpenVLE kann damit VMs und Templates innerhalb dieses Pools erstellen, klonen, konfigurieren, steuern und löschen — jedoch keine VMs außerhalb des Pools beeinflussen.

#### Storage- und Netzwerk-Berechtigungen zuweisen {#assign-storage-network}

Beim Klonen von VMs benötigt Proxmox zusätzliche Berechtigungen auf den verwendeten Storage und das Netzwerk. Ohne diese Berechtigungen schlägt das Klonen mit einem Berechtigungsfehler fehl, obwohl die VM-Rechte korrekt gesetzt sind.

:::caution Umgebungsabhängig
Die folgenden Pfade sind Beispiele. Du musst sie an den Storage und das Netzwerk deiner Umgebung anpassen.

Falls deine VMs und Templates unterschiedliche Storages oder Netzwerke verwenden (z. B. VMs auf `local-lvm` und Templates auf `ceph`, oder VMs in verschiedenen VLANs), musst du die jeweilige Berechtigung **pro Storage bzw. Netzwerk** separat vergeben. Erstelle dafür einfach weitere Zuweisungen mit der gleichen Rolle auf den zusätzlichen Pfaden.
:::

**3. Storage-Berechtigungen**

Pro verwendetem Storage eine Zuweisung erstellen:

- Pfad: `/storage/ceph` (ersetze `ceph` mit deinem Storage-Namen)
- Rolle: `PVEDatastoreUser`
- Propagate: True

Ermöglicht das Allozieren von Festplatten-Images beim Klonen und Erstellen von VMs auf dem angegebenen Storage. Nutzen deine VMs und Templates mehrere Storages, wiederhole diesen Schritt für jeden Storage (z. B. `/storage/local-lvm`, `/storage/nfs-share`).

**4. SDN-/Netzwerk-Berechtigungen**

Pro verwendetem Netzwerksegment eine Zuweisung erstellen:

- Pfad: `/sdn/zones/localnetwork/vmbr1/10` (ersetze mit deiner Zone, Bridge und VLAN)
- Rolle: `PVESDNUser`
- Propagate: True

Ermöglicht das Zuweisen von Netzwerk-Interfaces beim Klonen und Konfigurieren von VMs. Werden VMs in verschiedenen VLANs oder Bridges betrieben, wiederhole diesen Schritt für jedes Netzwerksegment (z. B. `/sdn/zones/localnetwork/vmbr1/20`).

#### CLI-Befehle und WebGUI {#cli-and-webgui}

<details>
<summary>CLI-Befehle (alle 4 Zuweisungen)</summary>

**Ersetze die Werte für Benutzer, API-Token, Pool, Storage und Netzwerk mit deinen eigenen.**

```bash
# 1. Allgemeine Systemberechtigungen
pvesh set /access/acl --path '/' \
--roles 'OpenVLE-Infra-General' \
--users 'OpenVLE@pve' --tokens 'OpenVLE@pve!prod01'

# 2. VM-Berechtigungen im Pool
pvesh set /access/acl --path '/pool/OpenVLE-VMs' \
--roles 'OpenVLE-Infra-VMs' \
--users 'OpenVLE@pve' --tokens 'OpenVLE@pve!prod01'

# 3. Storage-Berechtigungen
pvesh set /access/acl --path '/storage/ceph' \
--roles 'PVEDatastoreUser' \
--users 'OpenVLE@pve' --tokens 'OpenVLE@pve!prod01'

# 4. SDN-/Netzwerk-Berechtigungen
pvesh set /access/acl --path '/sdn/zones/localnetwork/vmbr1/10' \
--roles 'PVESDNUser' \
--users 'OpenVLE@pve' --tokens 'OpenVLE@pve!prod01'
```

</details>

<details>
<summary>WebGUI</summary>

Für jede der 4 Zuweisungen:

```
Datacenter -> Permissions -> Add -> User Permission
Datacenter -> Permissions -> Add -> API Token Permission
```

Wähle jeweils den Pfad, die Rolle und setze Propagate auf True.

</details>

## API-Referenz {#api-reference}

OpenVLE nutzt die folgenden Proxmox VE API-Endpoints. Diese Übersicht dient als Referenz zur Fehleranalyse bei Berechtigungsproblemen. Die vollständige API-Dokumentation von Proxmox findest du im <a href="https://pve.proxmox.com/pve-docs/api-viewer/"><code>PVE API Viewer</code></a>.

<details>
<summary>Vollständige API-Endpoint-Übersicht</summary>

### Cluster-Operationen {#cluster-operations}

Endpoints mit Privileg „Keine\*" erfordern kein explizites Privileg, liefern aber nur Objekte zurück, auf die der Benutzer bzw. das Token über andere Berechtigungen (z. B. `Sys.Audit`, `VM.Audit`) Zugriff hat. Die Ergebnismenge wird von Proxmox dynamisch anhand der vorhandenen Berechtigungen gefiltert.

| Endpoint                                                                                                      | Methode | Benötigtes Privileg                                                                           | Funktion                                       |
| ------------------------------------------------------------------------------------------------------------- | ------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/resources"><code>/cluster/resources</code></a> | GET     | Keine\*                                                                                       | Cluster-Ressourcen und Node-Zuordnung abfragen |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/status"><code>/cluster/status</code></a>       | GET     | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Audit</code></a> | Cluster-Status abfragen                        |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/nextid"><code>/cluster/nextid</code></a>       | GET     | Keine\*                                                                                       | Nächste verfügbare VM-ID ermitteln             |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/log"><code>/cluster/log</code></a>             | GET     | Keine\*                                                                                       | PVE-Logs abrufen                               |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/tasks"><code>/cluster/tasks</code></a>         | GET     | Keine\*                                                                                       | Aktuelle Cluster-Tasks auflisten               |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes"><code>/nodes</code></a>                         | GET     | Keine                                                                                         | Alle PVE-Nodes auflisten                       |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/rrd"><code>/nodes/{node}/rrd</code></a>   | GET     | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Audit</code></a> | Node-Statistiken abrufen                       |

### High Availability (HA) {#high-availability}

| Endpoint                                                                                                                        | Methode | Benötigtes Privileg                                                                             | Funktion                         |
| ------------------------------------------------------------------------------------------------------------------------------- | ------- | ----------------------------------------------------------------------------------------------- | -------------------------------- |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/ha/resources"><code>/cluster/ha/resources</code></a>             | GET     | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Audit</code></a>   | Alle HA-Ressourcen auflisten     |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/ha/resources"><code>/cluster/ha/resources</code></a>             | POST    | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Console</code></a> | HA für eine VM aktivieren        |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/ha/resources/{sid}"><code>/cluster/ha/resources/{sid}</code></a> | GET     | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Audit</code></a>   | HA-Status einer VM abfragen      |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/ha/resources/{sid}"><code>/cluster/ha/resources/{sid}</code></a> | PUT     | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Console</code></a> | HA-Konfiguration einer VM ändern |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/ha/resources/{sid}"><code>/cluster/ha/resources/{sid}</code></a> | DELETE  | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Console</code></a> | HA für eine VM deaktivieren      |

### VM-Verwaltung {#vm-management}

| Endpoint                                                                                                                                                                              | Methode | Benötigtes Privileg                                                                                                                                                                           | Funktion                             |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/config"><code>/nodes/{node}/qemu/{vmid}/config</code></a>                                             | GET     | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Audit</code></a>                                                                                                  | VM-Konfiguration abfragen            |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/config"><code>/nodes/{node}/qemu/{vmid}/config</code></a>                                             | PUT     | `VM.Config.*`                                                                                                                                                                                 | VM-Konfiguration ändern              |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/status/current"><code>/nodes/{node}/qemu/{vmid}/status/current</code></a>                             | GET     | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Audit</code></a>                                                                                                  | Aktuellen VM-Status abfragen         |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/clone"><code>/nodes/{node}/qemu/{vmid}/clone</code></a>                                               | POST    | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Clone</code></a>, <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Allocate</code></a> | VM oder Template klonen              |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}"><code>/nodes/{node}/qemu/{vmid}</code></a>                                                           | DELETE  | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Allocate</code></a>                                                                                               | VM löschen                           |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/migrate"><code>/nodes/{node}/qemu/{vmid}/migrate</code></a>                                           | POST    | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Migrate</code></a>                                                                                                | VM auf anderen Node migrieren        |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/cloudinit"><code>/nodes/{node}/qemu/{vmid}/cloudinit</code></a>                                       | PUT     | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Audit</code></a>                                                                                                  | CloudInit-Konfiguration regenerieren |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces"><code>/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces</code></a> | GET     | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Monitor</code></a>                                                                                                | Netzwerk-Interfaces (IPv4) auslesen  |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/tasks/{upid}/status"><code>/nodes/{node}/tasks/{upid}/status</code></a>                                           | GET     | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Audit</code></a>                                                                                                 | Task-Status abfragen                 |

### VM-Steuerung (Power Management) {#power-management}

| Endpoint                                                                                                                                           | Methode | Benötigtes Privileg                                                                              | Funktion                                                                        |
| -------------------------------------------------------------------------------------------------------------------------------------------------- | ------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------- |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/status"><code>/nodes/{node}/qemu/{vmid}/status/{action}</code></a> | POST    | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.PowerMgmt</code></a> | VM steuern: `start`, `stop`, `shutdown`, `reboot`, `reset`, `resume`, `suspend` |

</details>
