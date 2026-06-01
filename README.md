# Grundschutz++ Tools

Dieses Repository bündelt eng verzahnte Werkzeuge, Artefakte und Dienste für die Arbeit mit BSI Grundschutz++ und OSCAL. Aufgrund ihrer engen Integration befinden sich alle Projekte in diesem zentralen Multi-Repo.

## Projekte im Überblick

Jedes Projekt verfügt über eine eigene, detaillierte Dokumentation in seinem jeweiligen Verzeichnis.

### Kerndienste & Agenten
- [**Gpp-Agent**](./agentic/gpp-agent) – Ein KI-gestütztes Multi-Agenten-System, das Nutzer durch den gesamten Compliance-Prozess führt.
- [**GSpp_MCP**](./GSpp_MCP) – Ein Model Context Protocol (MCP) Server, der den BSI Grundschutz++ Katalog für KI-Agenten bereitstellt.
- [**GS_backend_MCP**](./GS_backend_MCP) – Ein MCP Server für das zentrale State-Management, die Persistenz und die Validierung von OSCAL-Modellen.

### Werkzeuge
- [**Gpp-ai-tool**](./Gpp-ai-tool) – Python-Automatisierung zur KI-gestützten Erstellung und Anreicherung von OSCAL-Komponentendefinitionen.
- [**One-Page-Apps**](./One-Page-Apps) – Eine Suite aus browserbasierten HTML/JS-Tools für Modellierung (Blaupausen), SSP-Bearbeitung, Audit-Planung und Maßnahmenverfolgung.

Die Komponenten in diesem Verzeichnis dienen als produktive Grundlage für:

- Die automatisierte Erstellung und Anreicherung von System Security Plans (SSP).
- Die detaillierte Dokumentation von Umsetzungsmaßnahmen.
- Die Durchführung von Audits auf Basis von Reifegraden (Maturity Levels).

#### Inhalt

Die Dateien sind nach den Bausteinen der Edition 2023 benannt und enthalten "enhanced" Beschreibungen, die über die reinen Anforderungen hinausgehen und konkrete Implementierungsvorschläge sowie Prüfhinweise liefern.

---

### `zielobjektkategorien`

Dieses Verzeichnis enthält die fachlich strukturierte Sammlung von OSCAL-Dateien auf Basis von GS++ Zielobjektkategorien wie sie in der offiziellen Methodik definiert sind.

Es ist der inhaltliche Kernbestand für wiederverwendbare Grundschutz++-Artefakte. Die Dateien sind so benannt, dass sie die jeweilige Zielobjektkategorie klar erkennen lassen und direkt in Werkzeugen, Referenzen oder eigenen Arbeitsabläufen verwendet werden können.

#### Zweck

`zielobjektkategorien` dient dazu,

- Zielobjektkategorien in strukturierter Form bereitzustellen,
- OSCAL-Profile pro Kategorie verfügbar zu machen,
- OSCAL-Komponentendefinitionen pro Kategorie verfügbar zu machen,
- eine nachvollziehbare Zuordnung zwischen fachlicher Kategorie und technischem Artefakt zu schaffen.

#### Inhalt von `zielobjektkategorien`

##### `profile/`
Hier liegen OSCAL-Profile pro Zielobjektkategorie.

Die Benennung folgt einem klaren Muster wie zum Beispiel:

- `administrierende_profile.json`
- `cloud-dienste_profile.json`
- `daten_profile.json`
- `it-systeme_profile.json`
- `webserver_profile.json`
- `wlans_profile.json`

Diese Profile eignen sich als Ausgangspunkt für Modellierung, Tailoring, SSP-Erstellung und Prüfvorbereitung.

##### `komponenten/`
Hier liegen OSCAL-Komponentendefinitionen pro Zielobjektkategorie.

Die Benennung folgt einem parallelen Schema, zum Beispiel:

- `administrierende-component.json`
- `cloud-dienste-component.json`
- `daten-component.json`
- `it-systeme-component.json`
- `office-anwendungen-component.json`
- `serverraeume-component.json`

Diese Dateien sind vor allem dann relevant, wenn mit konkreten Komponenten, wiederverwendbaren Implementierungsbausteinen oder standardisierten Umsetzungsbeschreibungen gearbeitet wird.

#### Einordnung

Während `profile/` stärker den anwendbaren Kontrollrahmen einer Zielobjektkategorie abbildet, liefern `komponenten/` eher umsetzungsnahe und wiederverwendbare Beschreibungen für die praktische Anwendung in Sicherheitskonzepten, Prüfungen oder Automatisierung.

---

### `hilfsdateien`

Dieses Verzeichnis enthält unterstützende Dateien, die in den Werkzeugen, bei der Vorbereitung von OSCAL-Artefakten oder für Mapping- und Referenzzwecke verwendet werden können.

Es ist die technische und fachliche Materialsammlung für wiederkehrende Hintergrunddaten.

#### Zweck

`hilfsdateien` bündelt insbesondere:

- Referenz- und Arbeitsfassungen von Textbeständen,
- Mapping-Dateien,
- strukturierte JSON-Hilfsdaten,
- vorbereitete Kataloge,
- Zuordnungen zwischen Zielobjekten, Controls und Anforderungen.

#### Inhalt von `hilfsdateien`

Die vorhandenen Dateien lassen sich in mehrere Gruppen einordnen:

##### Mapping- und Strukturdateien

- `baustein_zielobjekt.json`
- `prozessbausteine_mapping.json`
- `zielobjekt_controls.json`

Diese Dateien unterstützen die Zuordnung zwischen Bausteinen, Zielobjekten, Controls und Anforderungen. Sie sind besonders wichtig für Automatisierung, Ableitungen und konsistente Referenzierung.

##### Katalog- und Arbeitsdateien im OSCAL-Umfeld

- `c5-2026-oscal-catalog.json`
- `dsgvo_oscal_catalog.json`
- `kritis_oscal_catalog.json`

Diese Dateien liefern zusätzliche, strukturierte Kataloginhalte im OSCAL-Format und können als Grundlage für Beispiele, Tests oder weiterführende Verarbeitung dienen.

#### Einordnung

`hilfsdateien` ist kein Randbereich, sondern das unterstützende Fundament des Repositories. Viele der anderen Inhalte werden erst durch diese Mapping-, Referenz- und Arbeitsdateien effizient nutzbar.

---

### `beispiel-kataloge`

Dieses Verzeichnis enthält beispielhafte OSCAL-Kataloge, die direkt für Demonstrationen, Tests, Vorlagen oder prototypische Ableitungen genutzt werden können.

#### Inhalt von `beispiel-kataloge`

##### `dsgvo_oscal_catalog.json`
Beispielkatalog für die Verarbeitung eines DSGVO-bezogenen Katalogs im OSCAL-Format.

##### `kritis_oscal_catalog.json`
Beispielkatalog für die Verarbeitung eines KRITIS-bezogenen Katalogs im OSCAL-Format.

#### Zweck

Die Beispielkataloge sind besonders nützlich für:

- Demonstrationen,
- Tool-Tests,
- Schulungen,
- Prototyping,
- Validierung von Import- und Exportpfaden,
- Vergleich unterschiedlicher Katalogquellen.

---

## Werbeblock
Vertiefende Analysen und ein Ausblick auf die Zukunft finden sich im Buch: [1 Jahr Grundschutz++](https://www.amazon.de/dp/B0GY1HPT89)

## Haftungsausschluss
Die Inhalte dienen der Unterstützung bei der Umsetzung von Sicherheitsstandards. Es wird keine Gewähr für Richtigkeit, Vollständigkeit oder Aktualität übernommen. Die Nutzung erfolgt auf eigene Gefahr.
