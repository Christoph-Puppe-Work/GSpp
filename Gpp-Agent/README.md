# G++ Compliance Management Agent (Gpp-Agent)

Der Gpp-Agent ist ein multimodales, KI-gestütztes Multi-Agenten-System, dessen Hauptzweck es ist, den Nutzer durch den gesamten OSCAL-Prozess (Open Security Controls Assessment Language) nach BSI Grundschutz++ zu führen.

## Kernfunktionen

* **Mandantenfähigkeit (Multi-Informationsverbund):** Der Agent ist in der Lage, mehrere "Informationsverbünde" parallel zu verwalten und deren Daten strikt voneinander zu trennen.
* **GCP Cloud-Speicherung & Versionierung:** Wenn ein Nutzer speichert, legt der Agent die Daten direkt in einem GCP Bucket ab. Dabei wird für jeden Informationsverbund ein eigenes Unterverzeichnis erstellt, in welchem wiederum Unterverzeichnisse für jeden einzelnen Speicherpunkt (Save) angelegt werden. Nutzer können jederzeit vorherige Speicherstände auswählen, um diese weiterzubearbeiten, oder das JSON des aktuellen sowie vergangener Speicherpunkte herunterladen.
* **Multimodalität:** Nutzer können verschiedene Medien und Dokumente hochladen, damit der Agent diese nutzen kann (z.B. eine Liste von Assets für den SSP oder Beweisdokumente/Evidence zur Einbindung in die Assessment Results).
* **Sub-Agenten & Modellspezialisierung:** Das System besteht aus einem Hauptagenten und mehreren spezialisierten Sub-Agenten. Für unterschiedliche Aufgaben kommen jeweils optimal geeignete KI-Modelle zum Einsatz.
* **Strikte JSON-Validierung:** Der Agent verwendet für alle erzeugten Artefakte ausschließlich das JSON-Format. Jedes gespeicherte JSON-Dokument wird vor dem Speichern zwingend über das MCP-Tool `verify_oscal_json` gegen die offiziellen Schema-Dateien (aus `GSpp_MCP/OSCAL_schemas`) validiert, um absolute OSCAL-Konformität sicherzustellen.
* **MCP-Integration (Anwenderkatalog):** Der Agent nutzt einen speziellen MCP-Server (`GSpp_MCP`), um den jeweils aktuell verfügbaren "Anwenderkatalog" abzurufen und in die Workflows zu integrieren.

## Qualitätssicherung: Peer-Review & Human-in-the-Loop (HITL)

Um höchste Qualitätsstandards und BSI-Konformität sicherzustellen, setzt der Gpp-Agent auf ein zweistufiges Kontrollsystem:

### 1. KI-gestütztes Peer-Review (Agent-to-Agent)
Innerhalb des Multi-Agenten-Systems wird konsequent das "Maker-Checker"-Prinzip angewandt:
* **Producer-Agent**: Erstellt den initialen Entwurf (z. B. eine Risikobewertung, ein Tailoring-Profil oder SSP-Einträge).
* **Reviewer-Agent**: Ein separater, analytisch spezialisierter Sub-Agent prüft das erzeugte Artefakt auf Konsistenz, Vollständigkeit und formale Richtigkeit (Gegenabgleich mit dem `GSpp_MCP` Katalog und den strikten OSCAL-Schemas).
* Werden Mängel oder Inkonsistenzen festgestellt, geht das Artefakt mit spezifischem Feedback in eine interne Korrekturschleife zurück an den Producer.

### 2. Human-in-the-Loop (HITL)
Trotz hochgradiger Automatisierung behalten Sie als Nutzer stets die volle Kontrolle und Entscheidungsgewalt. Das System ist so designt, dass **HITL-Interventionen an allen Stellen des Workflows möglich** sind:
* **Entscheidungspunkte**: Vor jedem kritischen Statusübergang (z. B. Abschluss der Modellierung, Finalisierung des SSP, Generierung des Assessment Plans) pausiert der Agent und fordert Ihre Freigabe an.
* **Manuelle Übersteuerung**: Sie können die generierten Vorschläge der Agenten jederzeit verwerfen, manuell überschreiben oder durch direkte Prompts anpassen lassen.
* **Nahtlose Integration mit Savepoints**: Da jeder Schritt als versionierter Speicherstand im GCP Bucket abgelegt wird, können Sie jederzeit in den Prozess eingreifen, alte Stände laden und die KI von diesem exakten Punkt aus neu instruieren.

---

# Workflow-Übersicht: G++ Compliance Management

Der Prozess folgt einer klaren Kette von der Modellierung über die Umsetzung bis hin zur finalen Prüfung.

### 1. Modellierung mit dem SSP-Generator
In dieser Phase legen Sie das Fundament für Ihren Informationsverbund.
* **Profil-Erstellung**: Das Tool generiert ein OSCAL-Profil auf Basis des gewählten ISMS-Typs.
* **Asset-Management**: Sie integrieren Muster-Assets oder laden eigene Zielobjekte direkt aus der GitHub-Bibliothek.
* **Risikoanalyse**: Die Anwendung enthält ein integriertes Risikomanagement inklusive der Erstellung von Custom Controls.
* **Tailoring**: Sie passen Anforderungstexte und Parameter (z. B. Fristen oder Rollen) bereits hier an die lokale Situation an.
* **Export**: Sie erhalten den System Security Plan (SSP).

### 2. Grundschutzcheck mit SSP-Ausfüllen
Hier dokumentieren Sie die tatsächliche Umsetzung der Maßnahmen im Betrieb.
* **Umsetzungsstatus**: Sie erfassen den Status (z. B. "umgesetzt", "geplant") sowie Verantwortliche und Termine für jedes Control.
* **Workspace-Konzept**: Anstatt Dateien manuell zu verwalten, speichert der Agent Ihre Arbeit direkt im GCP Bucket. Sie können jederzeit vorherige Speicherstände (Saves) auswählen und den Bearbeitungsstand nahtlos fortsetzen.
* **AI-Assistent**: Die Anwendung nutzt KI-Unterstützung für tiefere Einblicke:
    * **Verständnis**: Erklärungen helfen, komplexe Control-Texte zu interpretieren.
    * **Risikofokus**: Die KI zeigt Gefahren bei Nicht-Umsetzung auf.
    * **Referenzierung**: Das Tool mappt Anforderungen auf die BSI Grundschutz Edition 2023.

### 3. Audit & Reporting mit Assessment Plan & Results
Die letzte Phase dient der formalen Prüfung und dem Nachweis der Compliance.
* **Prüfplanung (AP)**: Sie erstellen einen Assessment Plan, der Zeitpläne, Assessoren und die gewählten Prüfmethoden (Dokumentenprüfung, Interview, Test) festlegt.
* **Durchführung**: Sie bewerten die im SSP dokumentierte Umsetzung und halten Befunde (satisfied/not-satisfied) fest.
* **KI-Audit-Support**: 
    * **Befundvorschlag**: Die KI analysiert den SSP-Eintrag und schlägt eine Bewertung vor.
    * **Reifegrade**: Der Assistent generiert Prüfungshandlungen für verschiedene Reifegrade.
* **Ergebnis-Export (AR)**: Sie generieren die formalen Assessment Results (AR) als Beleg für die Wirksamkeit Ihres ISMS.

### 4. Feststellungen Abarbeiten: POA&M-Generator
Das Tool überführt ungelöste Mängel in einen verbindlichen Maßnahmenplan, damit keine Sicherheitslücke unbehandelt bleibt.
* **Mängel-Import**: Sobald du die Assessment Results lädst, übernimmt die Anwendung automatisch alle nicht erfüllten Controls.
* **Meilenstein-Planung**: Du legst detaillierte Phasenpläne fest, damit die Sanierung der Schwachstellen termingerecht erfolgt.
* **Dashboard**: Du behältst überfällige Deadlines und den allgemeinen Fortschritt der Mängelbeseitigung permanent im Blick.

---

# Kurzanleitung: Informationsverbund erstellen (Modellieren, Strukturanalyse, Risiko Analyse - OSCAL SSP-Generator)

### 1. Metadaten festlegen
* Trage Titel, Version und Zweck deines SSPs ein.
* Das Tool übernimmt diese Angaben direkt in die Metadaten des späteren OSCAL-Profils.

### 2. ISMS & Assets wählen
* Wähle ein Basis-ISMS (Standard oder Enhanced), um die Pflicht-Controls zu laden.
* Importiere Muster-Assets aus der GitHub-Bibliothek, wodurch die App deren Anforderungen automatisch extrahiert.

### 3. Tailoring (Anpassung)
* Nutze den Button "⚙️ Modify", um Parameter-Werte innerhalb der Controls zu definieren.
* Ergänze eigene Texte am Anfang oder Ende der Original-Anforderungen, um lokale Besonderheiten abzubilden.
* Füge zusätzliche Control-IDs bei Bedarf manuell hinzu.

### 4. Risikoanalyse durchführen
* Erstelle Risiko-Einträge und ordne diese entweder dem gesamten System oder spezifischen Assets zu.
* Verknüpfe mitigierende Maßnahmen aus dem Katalog oder erstelle eigene "Custom Controls".

### 5. OSCAL-Paket exportieren
* Lade deinen finalen SSP als JSON-Datei herunter oder verwalte ihn direkt als Savepoint im GCP Bucket.
