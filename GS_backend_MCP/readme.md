# G++ OSCAL Context Management MCP Server

> **Version:** 1.0.0-draft  
> **Spezifikation:** NIST OSCAL 1.1.x / BSI Grundschutz Edition 2023  
> **Architektur-Pattern:** Stateful Context Proxy, Zero-Trust Validation, In-Memory Transactions

## 1. Systemübersicht & Motivation

Das Gpp-Agentensystem orchestriert LLMs, um Nutzer durch den komplexen BSI Grundschutz++ Prozess zu führen. OSCAL-Dateien (System Security Plans, Assessment Results etc.) weisen zwei für LLMs hochproblematische Eigenschaften auf:
1. **Volumen & Rauschen:** Die Dateien sind extrem geschwätzig, tief verschachtelt und wachsen schnell auf mehrere Megabyte an.
2. **Relationale Abhängigkeiten:** Informationen sind über UUIDs in verschiedenen Dateien verknüpft (z.B. referenziert ein Assessment Result nur die UUID eines Controls aus dem SSP).

**Das Problem:** Lädt man diese JSON-Strukturen komplett in den LLM-Kontext, tritt der "Lost-in-the-Middle"-Effekt auf. Das Modell verliert den Fokus, verbraucht massive Token-Quotas und halluziniert bei der Bearbeitung. Gibt man dem Agenten jedoch nur isolierte Fragmente zum Bearbeiten, kann er nicht garantieren, dass sein Output das Gesamt-Schema des OSCAL-Dokuments nicht zerstört.

**Die Lösung:** Dieser MCP-Server agiert als intelligentes, zustandsbehaftetes Gateway zwischen den Agenten und dem GCP-Bucket. Er entkoppelt das *Reasoning* (die Logik der Agenten) von der *Datenhaltung und Validierung*. Er liefert vorgefilterte, relationale Daten-Auszüge (Reads) und integriert Updates in einem sicheren "Maker-Checker"-Loop (Writes), bevor sie persistiert werden.

---

## 2. Zero-Trust Sicherheitsarchitektur & Hard-Limits

Um die Vertraulichkeit von Informationsverbünden (ISMS) zu garantieren und BSI-Konformität zu erzwingen, ist der Server architektonisch stark limitiert:

* **Air-Gapped Validation:** Es gibt **keine externen API-Aufrufe** zur Schema-Prüfung. Die 8 offiziellen NIST/OSCAL-Schemas (`assessment-plan`, `assessment-results`, `catalog`, `component`, `mapping`, `poam`, `profile`, `ssp`) sind physisch in das Docker-Image des Servers einkompiliert.
* **Baked-in Base Catalog:** Der Basis-Katalog (BSI Grundschutz Edition 2023) ist zur performanten Profil-Auflösung ebenfalls fest im Image integriert.
* **Enum-Strictness:** Agenten können keine beliebigen JSON-Pfade ansprechen. Alle Lese- und Schreiboperationen sind durch hart typisierte Schnittstellen und Enums auf die 8 Kernmodelle begrenzt.
* **Isolierter GCP-Zugriff:** Ausschließlich der MCP-Server hält die Credentials für den GCP-Bucket. Agenten können Daten nur über erfolgreiche, validierte Transaktionen speichern.

---

## 3. Der Transaktions-Workflow (Write- & Commit-Loop)

Agenten überschreiben niemals direkt Dateien. Jeder Schreibvorgang ist eine gekapselte Transaktion im Arbeitsspeicher (RAM) des MCP-Servers.

### Phasen der State-Machine:
1. **Read-Phase:** Der Agent fordert über ein Extraktor-Tool einen Ist-Zustand an.
2. **Patch-Phase:** Der Agent sendet ein `partial_json` (das Update) via `update_oscal_model(model_enum, payload)`.
3. **Draft-Phase (In-Memory):** Der MCP-Server zieht das aktuelle Master-Dokument aus der GCP und mergt das `partial_json` in den Baum. Das Resultat existiert nur im RAM.
4. **Validation-Phase:** Der lokale Validator (`jsonschema`) prüft den gesamten RAM-Draft gegen das dem `model_enum` zugeordnete, eingebackene Schema.
5. **Commit / Rollback:**
   * **Success:** Der Draft wird in ein Bytes-Objekt konvertiert und als neuer versionierter Savepoint in die GCP geschrieben. Return an den Agenten: `{"status": "success", "new_version": "v1.2"}`.
   * **Rollback:** Der RAM-Draft wird verworfen. Der Agent erhält den exakten Stacktrace des Schema-Validators (z.B. `Missing property 'state' in $.poam-items[2]`). Der Maker-Checker-Prozess zwingt den Agenten zur Korrektur.

---

## 4. Spezifikation der Extraktor-Tools (Context Retrieval)

Die Lese-Werkzeuge (Reads) reduzieren das Token-Volumen drastisch und lösen komplexe OSCAL-Relationen serverseitig auf.

### 4.1. SSP (System Security Plan)
* `get_ssp_inventory(regex_filter: string)`
  * *Verhalten:* Durchsucht `$.system-security-plan.system-characteristics.system-information` und `$.system-security-plan.system-inventory`.
  * *Nutzen:* Filtert Assets nach Name, Typ oder Status.
* `get_ssp_components(component_type: string)`
  * *Verhalten:* Liefert Objekte aus `$.system-security-plan.system-implementation.components`.
* `get_ssp_implementation(status: string, role_id: string)`
  * *Verhalten:* Extrahiert Controls aus `$.system-security-plan.control-implementation.implemented-requirements`. Reduziert den Payload z.B. auf alle Controls, die noch den Status "planned" haben oder dem CISO (`role_id`) zugewiesen sind.

### 4.2. Assessment (AP & AR)
*Da Assessment-Modelle extrem auf UUIDs aufbauen, führt der MCP hierbei "Joins" mit dem SSP durch.*
* `get_assessment_subjects(regex_filter: string)`
  * *Verhalten:* Liefert die `assessment-subjects` aus dem Assessment Plan.
* `get_assessment_controls(regex_filter: string, selected_only: bool)`
  * *Verhalten:* Löst die referenzierten `control-id`s zum Profil/SSP auf. Ermöglicht dem Agenten, nach tatsächlichen Control-Namen oder Kommentaren zu suchen, anstatt blind UUIDs zu filtern.
* `get_assessment_findings(risk_level: string, state: string)`
  * *Verhalten:* Extrahiert `findings` aus den Assessment Results (z. B. Filter auf alle Befunde, die "not-satisfied" sind).

### 4.3. POA&M (Plan of Action and Milestones)
* `get_poam_items(status: string, due_before: date_string)`
  * *Verhalten:* Liefert priorisierte Listen aus `$.plan-of-action-and-milestones.poam-items`. Kombiniert den Befund mit den definierten Meilensteinen und Deadlines.
* `get_poam_risks(severity: string, treatment_status: string)`
  * *Verhalten:* Extrahiert das Risikoregister.

---

## 5. Profile Resolution Engine (Tailoring & Caching)

OSCAL-Profile enthalten keine Anforderungstexte, sondern nur Modifikationsanweisungen (`alter`, `set-parameter`). Der MCP-Server berechnet daraus einen anwendbaren Katalog ("Resolved Catalog").

### Resolution-Logik
Wird das Tool `get_tailored_control(control_id)` aufgerufen, passiert Folgendes:
1. **Link-Analyse (`href`):** Der Server prüft, worauf das Profil des Informationsverbunds basiert. Ist es der Standard-BSI-Katalog, wird der *eingebackene* Katalog aus dem Container geladen (~0ms Latenz). Ist es ein Custom-Katalog, wird dieser aus der GCP geholt.
2. **Transformation:** Der Server injiziert alle im Profil definierten Parameter (z.B. `<set-parameter param-id="pw-length"><value>12</value>`) in die Platzhalter des Basiskatalogs und fügt Zusatztexte (`alter`) an die Originalanforderungen an.

### Caching-Strategie & Invalidation
Da die Transformation von Megabyte-großen Katalogen extrem CPU-intensiv ist, implementiert der Server einen L2-Cache im RAM.
* **Cache-Key:** SHA-256 Hash des aktuellen `oscal_profile.json` aus dem GCP Bucket.
* **Hit:** Solange sich das Profil im Bucket nicht ändert, liefert der Server die fertig formulierten (getailorten) Controls in Millisekunden aus dem RAM.
* **Invalidation:** Speichert der Nutzer oder ein Agent eine Änderung am Profil ab (neuer Savepoint), ändert sich der Datei-Hash. Der MCP bemerkt dies beim nächsten Aufruf, leert den Cache und baut den Resolved Catalog einmalig neu auf.
