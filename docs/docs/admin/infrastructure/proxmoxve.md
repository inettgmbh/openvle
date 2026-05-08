---
id: proxmoxve
sidebar_label: Proxmox VE
sidebar_position: 50
status: finished
tags:
  - infrastructure
  - proxmox
---

# Proxmox VE {#proxmox}

Proxmox VE ist der Hypervisor, auf dem OpenVLE virtuelle Maschinen und VM-Vorlagen verwaltet. OpenVLE kommuniziert ausschließlich über die Proxmox REST-API mit dem Cluster — es gibt keinen direkten Zugriff auf die Proxmox-Hosts.

:::caution Erforderliche Komponente
Proxmox VE ist eine Kernabhängigkeit von OpenVLE. Ohne korrekte Proxmox-Konfiguration startet die Anwendung zwar, aber sämtliche Aktionen mit VMs und VM-Vorlagen schlagen fehl.
:::

## Verbindung {#connection}

OpenVLE verbindet sich über die Python-Bibliothek `proxmoxer` mit der Proxmox-API. Die Authentifizierung erfolgt per **API-Token** (nicht per Passwort):

| Parameter         | Beschreibung                  | Beispiel                   |
| ----------------- | ----------------------------- | -------------------------- |
| `PVE_HOSTNAME`    | API-Endpunkt (Host:Port)      | `proxmox.example.com:8006` |
| `PVE_USER`        | Proxmox-Benutzer (User@Realm) | `OpenVLE@pve`              |
| `PVE_TOKEN_NAME`  | Token-ID                      | `prod01`                   |
| `PVE_TOKEN_VALUE` | Token-Secret                  | `xxxxxxxx-xxxx-...`        |
| `PVE_VERIFY_SSL`  | SSL-Zertifikat verifizieren   | `True`                     |

## Pool-Konzept {#pools}

Alle von OpenVLE verwalteten VMs und VM-Vorlagen werden in einem dedizierten Proxmox-Pool organisiert (konfiguriert über `PVE_VMS_POOL`, Standard: `OpenVLE-VMs`). Die Proxmox-Berechtigungen des OpenVLE-API-Tokens sind auf diesen Pool beschränkt — OpenVLE kann daher **keine VMs außerhalb des Pools sehen, steuern oder löschen**. Andere Workloads auf demselben Proxmox-Cluster bleiben vollständig isoliert und unangetastet.

Durch die Kombination von Pool und Privilege Separation können auch mehrere OpenVLE-Instanzen (z. B. Produktion, Staging) auf demselben Proxmox-Cluster betrieben werden: Jede Instanz erhält ein eigenes API-Token mit Zugriff auf einen eigenen Pool, ohne die jeweils andere Instanz sehen oder beeinflussen zu können.

## VM-Lebenszyklus {#vm-lifecycle}

### VM-Vorlagen {#templates}

VM-Vorlagen (Templates) werden direkt in Proxmox als QEMU-Templates gespeichert. OpenVLE synchronisiert deren Status und Metadaten (Name, CPU, RAM, Node) periodisch in die eigene Datenbank. Templates können über OpenVLE erstellt, aktualisiert und gelöscht werden.

### VM-Operationen {#vm-operations}

Beim Deployment einer Veranstaltung oder auf manuelle Anfrage erstellt OpenVLE VMs durch Klonen von Templates:

| Operation                  | Beschreibung                                                                                                                |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **Klonen**                 | Erstellt eine neue VM aus einer VM-Vorlage (Full Clone oder Linked Clone, konfigurierbar über `PVE_VMS_FULL_CLONE_DEFAULT`) |
| **Starten / Stoppen**      | Startet oder stoppt eine VM auf Proxmox                                                                                     |
| **Herunterfahren**         | Fährt eine VM über den QEMU Guest Agent sauber herunter                                                                     |
| **Neustarten**             | Startet eine laufende VM neu                                                                                                |
| **Zurücksetzen**           | Hard-Reset einer VM                                                                                                         |
| **Pausieren / Fortsetzen** | Pausiert eine VM oder setzt sie fort                                                                                        |
| **Migrieren**              | Verschiebt eine VM auf einen anderen Proxmox-Node (online oder offline)                                                     |
| **Löschen**                | Entfernt eine VM von Proxmox und bereinigt die Datenbank                                                                    |

## Node-Management {#node-management}

OpenVLE ist vollständig Multi-Node-fähig und arbeitet mit beliebig vielen Proxmox-Nodes:

- **Node-Erkennung** — Der periodische Sync erfasst alle Nodes im Cluster und speichert deren Status
- **Automatische Node-Auswahl** — Beim Klonen einer VM wählt OpenVLE automatisch den Node mit der meisten verfügbaren CPU-Kapazität
- **Node-Tracking** — Für jede VM und VM-Vorlage wird gespeichert, auf welchem Node sie sich befindet. Bei Migrationen wird dies automatisch aktualisiert

## Netzwerk und IP-Vergabe {#networking}

OpenVLE unterstützt zwei Methoden zur Netzwerkkonfiguration der VMs.

:::note Ohne Apache Guacamole
Wird OpenVLE ohne Apache Guacamole betrieben — z. B. nur zur Verwaltung und zum Ausrollen von VMs ohne webbasierten Remote-Desktop-Zugang — sind die Netzwerkinformationen der VMs für OpenVLE nicht zwingend erforderlich. Die IP-Adressen werden in diesem Fall zwar weiterhin ausgelesen und angezeigt, sind aber für die Kernfunktionalität nicht notwendig.
:::

### DHCP (Standard, empfohlen) {#dhcp}

Im Standardbetrieb (`PVE_CI_ENABLED=False`) erwartet OpenVLE, dass im Subnetz/VLAN der VMs ein externer DHCP-Server aktiv ist, der den VMs dynamisch IP-Adressen zuweist. Die VM-Vorlagen müssen dafür lediglich auf DHCP konfiguriert sein.

Nach dem Start einer VM liest OpenVLE die vom DHCP vergebene IPv4-Adresse über den QEMU Guest Agent aus der VM aus und speichert sie in der Datenbank. Das ist der empfohlene Standardweg.

### Cloud-Init (experimentell) {#cloud-init-networking}

Bei aktiviertem Cloud-Init (`PVE_CI_ENABLED=True`) übernimmt OpenVLE die IP-Vergabe selbst und schreibt eine statische IP-Konfiguration direkt in die VM:

1. Das Subnetz wird aus `PVE_VMS_NETWORK` und `PVE_VMS_SUBNET` gebildet
2. Bereits vergebene IPs (aus der Datenbank) und ausgeschlossene IPs (`PVE_VMS_EXCLUDED_IPS`) werden übersprungen
3. Die erste freie IP wird der neuen VM über Cloud-Init zugewiesen (inkl. Gateway und DNS)

:::caution Experimentell
Cloud-Init-basierte IP-Vergabe ist aktuell ein experimentelles Feature. Weitere Details und alle Cloud-Init-Variablen findest du unter [Cloud-Init](#cloud-init) und in der [Konfigurationsreferenz — Proxmox VE](../install/configuration#proxmox).
:::

### QEMU Guest Agent {#guest-agent}

OpenVLE setzt voraus, dass der QEMU Guest Agent in den VMs installiert ist. Er wird für folgende Funktionen benötigt:

- **IP-Erkennung** — Auslesen der tatsächlichen IPv4-Adresse einer laufenden VM (bei DHCP und Cloud-Init)
- **Sauberes Herunterfahren** — Graceful Shutdown über den Agent

:::note Proxmox-Berechtigung
Ab Proxmox VE 9 wird das Privileg `VM.GuestAudit` auf dem Pool benötigt, damit OpenVLE Guest-Agent-Abfragen und -Befehle ausführen kann. Bei PVE < 9 ist dieses Privileg nicht vorhanden und kann weggelassen werden. Details zur Einrichtung findest du unter [Proxmox VE — Integration](../install/proxmoxve#create-roles).
:::

## Periodischer Sync {#periodic-sync}

Der Worker `worker-periodic` synchronisiert alle `WORKER_PVE_PERIODIC_INTERVAL` Sekunden (Standard: 60) den Status zwischen Proxmox und OpenVLE:

1. **Cluster-Ressourcen abrufen** — Vollständige Liste aller VMs, Templates und Nodes aus Proxmox
2. **MongoDB aktualisieren** — Snapshot der Cluster-Ressourcen für schnellen Zugriff
3. **MariaDB aktualisieren** — Status-Updates für alle bekannten VMs und Templates (z. B. `cloning` → `running`, Node-Wechsel bei Migration)
4. **Changelog erstellen** — Alle Statusänderungen werden protokolliert

VMs in Übergangszuständen (`starting`, `deleting`, `stopping`) werden beim Sync übersprungen, um Konflikte mit laufenden Operationen zu vermeiden.

## Optionale Features {#optional-features}

### Cloud-Init (experimentell) {#cloud-init}

Bei aktiviertem Cloud-Init (`PVE_CI_ENABLED=True`) konfiguriert OpenVLE neue VMs zusätzlich zur [IP-Vergabe](#cloud-init-networking) automatisch mit:

- Benutzername und Passwort (`PVE_VMS_CIUSER`, `PVE_VMS_CIPASSWORD`)
- Optionales Paket-Upgrade beim ersten Start (`PVE_VMS_CIUPGRADE`)

Alle Cloud-Init-Variablen findest du in der [Konfigurationsreferenz — Proxmox VE](../install/configuration#proxmox).

### SMBIOS-Metadaten {#smbios}

Bei aktiviertem `PVE_VMS_SMBIOS_METADATA` (Standard: `True`) schreibt OpenVLE Metadaten aus der Anwendung in die SMBIOS-Informationen (Type 1) der VM:

| SMBIOS-Feld    | Inhalt              |
| -------------- | ------------------- |
| `manufacturer` | Projektname         |
| `product`      | VM-Name             |
| `version`      | Template-ID         |
| `serial`       | OpenVLE VM-UUID     |
| `family`       | Veranstaltungs-Slug |

Diese Metadaten sind innerhalb des Gastbetriebssystems auslesbar (z. B. über `dmidecode` unter Linux oder WMI unter Windows) und ermöglichen es, eigene Automationen innerhalb der VMs zu betreiben. Skripte in der VM können so zur Laufzeit erkennen, zu welcher Veranstaltung und Umgebung sie gehören, und darauf basierend automatisch Konfigurationen anpassen, Dienste starten oder Daten synchronisieren — ohne eine direkte API-Verbindung zu OpenVLE herstellen zu müssen.

### High Availability {#high-availability}

VMs aus Veranstaltungen werden standardmäßig in die Proxmox-HA-Konfiguration aufgenommen und genießen damit automatisch Cluster-Hochverfügbarkeit: Bei einem Node-Ausfall werden die VMs automatisch auf einem anderen Node neu gestartet. OpenVLE verwaltet die HA-Konfiguration vollständig — VMs werden beim Deployment hinzugefügt und bei der Archivierung wieder entfernt.

## Weiterführende Informationen {#further-reading}

- [Proxmox VE Integration konfigurieren](../install/proxmoxve) — Einrichtung von Benutzer, Token, Rollen und Berechtigungen
- [Konfigurationsreferenz — Proxmox VE](../install/configuration#proxmox) — Alle Proxmox-Umgebungsvariablen
- [Task-System](task-system) — Queues und Worker für VM-Operationen
