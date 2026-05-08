# G++ OSCAL Context- und State-Manager (MCP Server)

> **Version:** 1.1.0-draft  
> **Spezifikation:** NIST OSCAL 1.2.2 / BSI Grundschutz++  
> **Architektur-Pattern:** Stateful Agent Interface, Zero-Trust Validation, In-Memory Transactions, Snapshot-Versioning

## 1. Systemübersicht & Motivation

Der Gpp-Agent orchestriert LLMs, um Nutzer durch den BSI Grundschutz++ Prozess zu führen. Dieser MCP-Server ist nicht nur ein reiner "Context Manager", der Daten bereitstellt, sondern fungiert als der zentrale **State-Manager und das exklusive Interface** für die Agenten zum Lesen, Manipulieren und Validieren von Compliance-Artefakten.

OSCAL-Dateien weisen zwei für LLMs hochproblematische Eigenschaften auf:
1. **Volumen:** Sie wachsen schnell auf mehrere Megabyte an (Lost-in-the-Middle-Effekt).
2. **Komplexität:** Ein isoliert arbeitender Agent kann bei der Generierung von JSON-Payloads nicht garantieren, dass das globale OSCAL-Schema nicht bricht.

**Die Lösung:** Dieser MCP-Server entkoppelt die *Logik* der Agenten von der *Datenhaltung*. Er liefert den Agenten relationale, vorgefilterte Daten-Auszüge zum Lesen und zwingt sie beim Manipulieren und Anlegen von Artefakten durch einen strikten Validierungs-Loop, bevor Daten als persistente Snapshots in der GCP gespeichert werden.

---

## 2. Zero-Trust Sicherheitsarchitektur & Hard-Limits

Um die Vertraulichkeit von Informationsverbünden (ISMS) zu garantieren und BSI-Konformität zu erzwingen, ist der Server architektonisch limitiert:

* **Air-Gapped Validation:** Es gibt **keine externen API-Aufrufe** zur Schema-Prüfung. Die 8 offiziellen NIST/OSCAL 1.2.2 Schemas (`assessment-plan`, `assessment-results`, `catalog`, `component`, `mapping`, `poam`, `profile`, `ssp`) sind physisch in das Docker-Image des Servers einkompiliert.
* **Enum-Strictness:** Alle Lese- und Schreiboperationen sind durch hart typisierte Schnittstellen auf die 8 Kernmodelle begrenzt.
* **Isolierter GCP-Zugriff:** Ausschließlich der MCP-Server hält die Credentials für den GCP-Bucket.

---

## 3. Der Transaktions-Workflow: Anlegen, Verändern & Snapshots

Dieser MCP-Server ist das alleinige Interface zur Verwaltung des Informationsverbund-Status (State). Alle Schreiboperationen (Writes) sind gekapselte Transaktionen im Arbeitsspeicher (RAM) des MCP-Servers, die bei Erfolg als **versionierte Snapshots / Saves** in der Cloud abgelegt werden. Es werden niemals bestehende Snapshots überschrieben.

Der Workflow unterteilt sich in zwei fundamentale Operationen:

### 3.1. Anlegen von Artefakten (Creation)
Wenn ein Agent den Prozess für einen Informationsverbund startet oder in eine neue Phase eintritt, muss er Basis-Artefakte (z.B. SSP, AP, AR, POA&M) initial erschaffen.
1. **Init:** Der Agent ruft das Tool `create_oscal_model(model_enum, initial_payload)` auf.
2. **Draft (In-Memory):** Der MCP-Server generiert im RAM ein neues JSON-Dokument basierend auf der Payload des Agenten und fügt die nötigen OSCAL 1.2.2 Metadaten (UUIDs, Timestamps) hinzu.
3. **Validation:** Der RAM-Draft wird gegen das eingebackene lokale Schema geprüft.
4. **Initial Snapshot:** Bei fehlerfreier Validierung schreibt der MCP das Dokument als initialen Save/Snapshot (z.B. `save_v1.json`) in das GCP-Verzeichnis des Mandanten.

### 3.2. Veränderungen an Artefakten (Mutation)
Wenn ein Agent ein bestehendes Artefakt bearbeitet (z. B. Controls als "umgesetzt" markiert oder Findings in ein Assessment Result einträgt).
1. **Read-Phase:** Der Agent fordert über ein Extraktor-Tool den aktuellen Ist-Zustand an.
2. **Patch-Phase:** Der Agent sendet ein `partial_json` (das Update) via `update_oscal_model(model_enum, payload)`.
3. **Draft-Phase (In-Memory):** Der MCP-Server zieht den **letzten gültigen Snapshot** aus der GCP und mergt das Update des Agenten in den JSON-Baum. Das Resultat existiert nur im RAM.
4. **Validation-Phase:** Der lokale Validator (`jsonschema`) prüft den gesamten RAM-Draft gegen das Schema.
5. **Snapshot Commit / Rollback:**
   * **Success:** Der Draft wird als **neuer Snapshot** (z.B. `save_v2.json`) persistiert. Das System hat nun einen neuen State. Return an den Agenten: `{"status": "success", "new_snapshot": "save_v2"}`.
   * **Rollback:** Der RAM-Draft wird verworfen. Der Agent erhält den exakten Stacktrace des Schema-Validators. Der "Maker-Checker"-Prozess zwingt den Agenten zur Korrektur seiner Payload.

---

## 4. Spezifikation der Agenten-Interfaces (Reads / Extractors)

Die Lese-Werkzeuge reduzieren das Token-Volumen für die Agenten drastisch und lösen komplexe OSCAL-Relationen serverseitig auf.

### 4.1. SSP (System Security Plan)
* `get_ssp_inventory(regex_filter)`: Filtert Assets nach Name, Typ oder Status aus dem aktuellen Snapshot.
* `get_ssp_implementation(status, role_id)`: Extrahiert Controls aus der `control-implementation` (z.B. Filter auf alle Controls, die dem CISO zugewiesen sind).

### 4.2. Assessment (AP & AR)
* `get_assessment_subjects(regex_filter)`: Liefert die Prüfgegenstände aus dem Assessment Plan.
* `get_assessment_controls(regex_filter, selected_only)`: Löst UUIDs zum SSP auf, damit Agenten nach tatsächlichen Control-Namen suchen können.
* `get_assessment_findings(risk_level, state)`: Extrahiert Befunde (z. B. "not-satisfied") aus den Assessment Results.

### 4.3. POA&M (Plan of Action and Milestones)
* `get_poam_items(status, due_before)`: Liefert den Maßnahmenplan inklusive Meilensteinen aus dem aktuellen Snapshot.

---

## 5. Profile Resolution Engine (Tailoring & Caching)

OSCAL-Profile enthalten keine Anforderungstexte, sondern Modifikationsanweisungen (`alter`, `set-parameter`). Der MCP-Server berechnet daraus einen anwendbaren Katalog.

### Resolution-Logik & Caching
1. **Link-Analyse (`href`):** Ist das Profil auf Basis des Standard-BSI-Katalogs gebaut, wird der *eingebackene* Katalog aus dem Container geladen (~0ms Latenz).
2. **Transformation:** Der Server injiziert alle im Profil definierten Parameter (z.B. Passwortrichtlinien) in den Basiskatalog.
3. **In-Memory Cache:** Das Ergebnis wird im RAM gecacht (Key: SHA-256 Hash des Profil-Snapshots).
4. **Invalidation:** Sobald ein Agent einen neuen Snapshot des Profils in der GCP abspeichert, ändert sich der Datei-Hash. Der Cache wird geleert und der Katalog beim nächsten Aufruf neu getailort.
