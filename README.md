# Grundschutz++ Tools

Dieses Repository bündelt eng verzahnte Werkzeuge, Artefakte und Dienste für die Arbeit mit BSI Grundschutz++ und OSCAL. Aufgrund ihrer engen Integration befinden sich alle Projekte in diesem zentralen Multi-Repo.

## Projekte im Überblick

Jedes Projekt verfügt über eine eigene, detaillierte Dokumentation in seinem jeweiligen Verzeichnis.

### Kerndienste & Agenten
- [**Gpp-Agent**](./Gpp-Agent) – Ein KI-gestütztes Multi-Agenten-System, das Nutzer durch den gesamten Compliance-Prozess führt.
- [**GSpp_MCP**](./GSpp_MCP) – Ein Model Context Protocol (MCP) Server, der den BSI Grundschutz++ Katalog für KI-Agenten bereitstellt.
- [**GS_backend_MCP**](./GS_backend_MCP) – Ein MCP Server für das zentrale State-Management, die Persistenz und die Validierung von OSCAL-Modellen.

### Werkzeuge
- [**Gpp-ai-tool**](./Gpp-ai-tool) – Python-Automatisierung zur KI-gestützten Erstellung und Anreicherung von OSCAL-Komponentendefinitionen.
- [**One-Page-Apps**](./One-Page-Apps) – Eine Suite aus browserbasierten HTML/JS-Tools für Modellierung (Blaupausen), SSP-Bearbeitung, Audit-Planung und Maßnahmenverfolgung.

### Inhalte & Kataloge
- [**zielobjektkategorien**](./zielobjektkategorien) – Fachlich strukturierte OSCAL-Profile und Komponentendefinitionen nach Zielobjektkategorien.
- [**ED23-Baustein-komponenten**](./ED23-Baustein-komponenten) – OSCAL-Komponenten auf Basis des IT-Grundschutz Edition 2023.
- [**kataloge**](./kataloge) – Verschiedene produktive Sicherheitsstandards im OSCAL-Format.
- [**hilfsdateien**](./hilfsdateien) – Zentrale Mapping-Dateien, Referenztexte und strukturierte Hilfsdaten zur Unterstützung der Tools.
- [**beispiel-kataloge**](./beispiel-kataloge) – Beispielhafte OSCAL-Kataloge für Tests, Schulungen und Demonstrationen.

---

## Werbeblock
Vertiefende Analysen und ein Ausblick auf die Zukunft finden sich im Buch: [1 Jahr Grundschutz++](https://www.amazon.de/dp/B0GY1HPT89)

## Haftungsausschluss
Die Inhalte dienen der Unterstützung bei der Umsetzung von Sicherheitsstandards. Es wird keine Gewähr für Richtigkeit, Vollständigkeit oder Aktualität übernommen. Die Nutzung erfolgt auf eigene Gefahr.
