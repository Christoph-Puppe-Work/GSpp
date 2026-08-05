# Kapitel 1: Einleitung – Grundschutz++ und die Stand-der-Technik-Bibliothek

**Handbuch zur Grundschutz++ Methodik · Kapitel-Version 0.6 (Entwurf)**
Stand: 2026-08-02 · Gliederungsbezug: Kapitel 1 gemäß `00_gliederung_v0.1.md`

## 1.1 Was Grundschutz++ ist

Der IT-Grundschutz hat fast dreißig Jahre lang als Buch funktioniert: Standards als PDF, Kompendium als Kapitelsammlung, und dazwischen der Anwender, der Prosa in Tabellen übersetzt. Grundschutz++ dreht das Format um. Die Anforderungen liegen als maschinenlesbarer OSCAL-Katalog in einem öffentlichen Git-Repository, der Stand-der-Technik-Bibliothek des BSI (`BSI-Bund/Stand-der-Technik-Bibliothek`). Dort bildet der Control Layer die Katalogebene: neben Grundschutz++ auch Nachbarkataloge (unter anderem ISO 27001 Annex A, Risikomanagement, Lieferkettensicherheit) und die Mapping-Sammlungen, die Grundschutz++ mit der ISO-Welt und der Kompendiums-Edition 2023 verbinden (Kapitel 10.3). Der aufgelöste Anwenderkatalog des Builds 2026-07-29 umfasst 1000 Controls in 20 Gruppen; jedes Control trägt seine Anforderung als strukturierten Datensatz mit Modalverb, Erfüllungsverb, Ergebnis, Parametern und zugeordnetem Nachweisdokument (Kapitel 3).

Für die Praxis ändert das zwei Dinge. Erstens die Arbeitsweise: Modellierung, Vererbung und Registerpflege sind automatisierbar, weil die Quelle es ist; wer den Katalog per Skript verarbeitet, arbeitet mit dem Original statt mit einer Abschrift. Zweitens die Taktung: Kataloge bekommen Builds statt Editionen, und die Methodik verlangt selbst, die Aktualität des eigenen Anforderungspakets regelmäßig gegen den Katalogstand zu prüfen (PERF.1.3).

## 1.2 Gegenstand und Abgrenzung dieses Handbuchs

Gegenstand dieses Handbuchs ist die **Methodik** des Grundschutz++: die fünf Praktiken GC (Governance und Compliance), STM (Strukturmodellierung), UMS (Umsetzung), VRB (Verbesserung) und PERF (Monitoring-Evaluation) mit ihren 95 Controls, also das ISMS-Verfahren selbst, wie es der Katalog als maschinenlesbare Anforderungen formuliert; dazu die vier RISK-Controls (RISK.1.1, RISK.1.3, RISK.1.5, RISK.1.10), die der Anwenderkatalog aus dem Katalog „BSI Anforderungen zum Risikomanagement" importiert. Sie gehören formal nicht zur Methodik, gelten aber im Anwenderkatalog und werden im Exkurs in Kapitel 4.12 behandelt. Die Sicherheitsanforderungen des Kernels, die vierzehn technischen und organisatorischen Praktiken von ASST bis TEST mit über 900 Controls, sind **nicht** Gegenstand; sie erscheinen nur dort, wo die Methodik auf sie verweist, etwa bei der Modellierung des Anforderungspakets (STM.2) oder der Sicherheitsniveau-Steuerung (STM.3). Ebenfalls außerhalb des Gegenstands: die sechs nicht importierten Controls des RISK-Quellkatalogs (Kapitel 10.5, Anhang D, D11) und alle Nachbarkataloge der Bibliothek.

## 1.3 Zielgruppe und Lesarten

Dieses Handbuch richtet sich an ISBs, Auditoren und Berater mit IT-Grundschutz-Vorwissen, aber ohne Grundschutz++-Erfahrung. Es setzt voraus, dass Begriffe wie ISMS, Schutzbedarf oder Grundschutz-Check bekannt sind, und erklärt stattdessen, was aus ihnen geworden ist.

Drei Lesarten haben sich bewährt. Wer die Methodik **einführen** will, liest die Kapitel 2, 4 bis 8 in dieser Reihenfolge und nutzt Kapitel 2.6 als Fahrplan des ersten Zyklus. Wer **auditiert oder sich auditieren lässt**, beginnt mit Kapitel 9, nutzt die Audit-Perspektiven der Praktik-Kapitel als Prüfvorbereitung und Anhang B als Evidenzliste. Wer aus der **200-2-Welt migriert**, beginnt mit Kapitel 10 und liest dann die Abweichungskästen der Praktik-Kapitel. Kapitel 3 ist die Referenz für alle, die den Katalog maschinell verarbeiten; die Anhänge A und B sind generierte Nachschlagewerke, Anhang D sammelt alle offenen Fragen und Katalogfunde.

Jedes Praktik-Kapitel folgt derselben Schablone: Einordnung mit den Kennzahlen der Praktik, dann je Untergruppe der Anforderungsbezug als Tabelle, Umsetzungshinweise, Audit-Perspektive und typische Fehler, am Ende der Dokumenten-Output und die offenen Fragen. Die Umsetzungshinweise tragen erkennbar Handschrift und Erfahrungswerte des Autors; normativ sind allein die zitierten Controls.

## 1.4 Quellen, Rangfolge, Konventionen

Die Quellenlage dieses Handbuchs ist bewusst streng geregelt:

1. **Normative Primärquelle** ist der Katalog `BSI-Methodik-Grundschutz++-catalog.json` (verwendeter Build: 2026-07-29). Jede Aussage über eine Anforderung ist auf eine Control-ID rückführbar, alle Zahlen sind skriptgestützt aus dem JSON erhoben. Bei Widersprüchen zwischen Katalog und jeder anderen Quelle gilt der Katalog.
2. **Auslegungshilfe bei Lücken** ist der BSI-Standard 200-2, ausschließlich dort, wo die Methodik schweigt und ein Begriff oder Verfahren der Erläuterung bedarf. Abweichungen zwischen Katalog und 200-2 werden nie stillschweigend harmonisiert, sondern in gekennzeichneten Kästen benannt und in Kapitel 10.4 konsolidiert.
3. **Auslegungshilfe für Prüffolgen** sind Auditierungsschema (Version 2.5) und Zertifizierungsschema. Da beide noch gegen die 200-2-Welt prüfen, sind alle Audit-Aussagen dieses Handbuchs Übertragungen und als Auslegung gekennzeichnet (Kapitel 9).
4. **Ergänzende Belege** liefern die Namespace-Dateien und Mapping-Sammlungen des Repositories (Snapshot 2026-08-02); sie definieren Feldbedeutungen und Brücken in Alt-Welten, ersetzen aber keine Kataloganforderung.

Was in keiner Quelle steht, wird nicht erfunden, sondern als offene Frage markiert; Anhang D ist die konsolidierte Liste. Die Schreib- und Zitierkonventionen im Einzelnen definiert Kapitel 3.11: exakte Modalverben, Parameter als `{{Label}}`, Blockzitate nur wörtlich und mit ID, versionsfeste Referenzen über `alt-identifier`-UUIDs.

Ein Wort zur Ehrlichkeit dieses Projekts: Grundschutz++ ist jung, sein Katalog in Bewegung (Kapitel 10.3 belegt Strukturänderungen zwischen Builds), sein Prüfschema existiert noch nicht, und dieses Handbuch dokumentiert neben der Methodik auch ihre Baustellen, von Tippfehlern in Statements bis zu Verbindlichkeitslücken. Das ist kein Mangel an Respekt vor der Quelle, sondern die Arbeitsweise, die eine maschinenlesbare, versionierte Anforderungsbibliothek verdient: lesen, nachrechnen, zurückmelden.

---

*Ende Kapitel 1 (v0.1). Review-Anmerkungen bitte gegen die Control-IDs.*
