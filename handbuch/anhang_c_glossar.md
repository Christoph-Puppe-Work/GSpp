# Anhang C: Glossar der Methodik-Begriffe

**Handbuch zur Grundschutz++ Methodik · Version 0.3 (Entwurf)** · Stand: 2026-08-02 · Quellen: Katalog-Build 2026-07-29 (Statements und Guidance), Namespace-CSVs (Repo-Snapshot 2026-08-02)

Aufgenommen sind nur katalog- oder namespace-belegte Begriffe; die Fundstelle steht bei jedem Eintrag. Begriffe, deren Definition in den Quellen fehlt oder strittig ist, tragen einen Verweis auf Anhang D. Kursiv gesetzte Alt-Begriffe der 200-2-Welt sind in Kapitel 10.2 übersetzt.

**Action Word** – Das Erfüllungsverb eines Statements mit definierter Erfüllungssemantik im Namespace `action_words.csv` (27 Verben, 13 davon in der Methodik verwendet). Das Action Word liefert das Prüfkriterium einer Anforderung. (Kapitel 3.2)

**alt-identifier** – Stabile UUID jedes Controls; versionsfeste Referenz, im Gegensatz zur sprechenden ID, die sich zwischen Builds ändern kann. (Kapitel 3.1, 10.3)

**Anforderungspaket** – Menge aller Anforderungen, die für den betrachteten Informationsverbund und den priorisierten Geschäftsprozess gelten; zentrales Arbeitsdokument der Methodik, erzeugt durch STM.2, abgearbeitet durch UMS, evaluiert durch PERF.1.2/1.3. (Kapitel 5.2)

**Ausnahmegenehmigung** – Autorisierte, begründete und dokumentierte Abweichung von einer Verpflichtung (UMS.5.1, UMS.5.2); Nachweisdokument „Freigegebene Ausnahmegenehmigung". Begriffsumfang siehe Anhang D. (Kapitel 6.5)

**Control** – Einzelne Anforderung im OSCAL-Katalog, mit Statement, meist Guidance, Properties und gegebenenfalls Kind-Controls bis Ebene 4. (Kapitel 3.1)

**documentation-Prop** – Property am Statement, die das Nachweisdokument der Anforderung benennt; 59 der 95 Methodik-Controls tragen sie, 21 Dokumente insgesamt. (Kapitel 3.2, Anhang B)

**effort_level** – Aufwandsstufe 0 bis 5 je Control; 0 heißt „wird nicht bewertet, da zwingend erforderlich", 5 steht für komplexe Großmaßnahmen. Definitionen im Namespace `effort_level.csv`. (Kapitel 3.4)

**Geltungsbereich** – Formal und organisatorisch abgegrenzter Anwendungsbereich des ISMS, festgelegt nach Freigabe der Institutionsleitung (GC.6.1); Grundlage des Informationsverbunds. (Kapitel 4.6)

**Guidance** – Erläuternder Part eines Controls; nicht normativ, aber auslegungsleitend und teils mit faktisch bindenden Festlegungen. (Kapitel 3.10)

**Informationssicherheitseinstufung** – Verfahren zur Festlegung der Geschäftsprozesse und zur zweistufigen Einstufung ihres Schutzbedarfs in „normal" oder „hoch" (GC.7). (Kapitel 4.7)

**Informationsverbund** – Technisch-organisatorische Ausgestaltung des Geltungsbereichs: Systeme, Prozesse, Personen, Komponenten samt Grenzen und Schnittstellen (STM.1.1, STM.1.2); zugleich Name des Nachweisdokuments. (Kapitel 5.1)

**Institutionsleitung** – Oberste Führungsebene; trägt die Gesamtverantwortung, autorisiert ISMS, Leitlinie und Geltungsbereich, entscheidet über den wichtigsten Geschäftsprozess und empfängt den Managementbericht (GC.1.2, GC.5.1.2, GC.6.1, GC.7.1.2, PERF.4.2). (Kapitel 4, 8.4)

**ISB (Informationssicherheitsbeauftragter)** – Unabhängige, unmittelbar der Institutionsleitung unterstellte Person mit der Zuständigkeit für Informationssicherheit; mit Ressourcen und direktem Vorspracherecht auszustatten (GC.9.1.1.1 mit Sub-Controls). Titelvarianten laut Guidance: CISO, ISM. (Kapitel 4.9)

**ISMS-Regelwerk** – Nachweisdokument der Verfahren und Regelungen zur Errichtung und Aufrechterhaltung des ISMS (GC.1.1); die Klammer über der Dokumentenlandschaft. (Kapitel 4.1)

**Katalog-Build** – Versionsstand des maschinenlesbaren Katalogs (hier durchgängig: 2026-07-29); Grundschutz++ erscheint in Builds statt Editionen. (Kapitel 1.1, 10.3)

**Kernel** – Die technischen und organisatorischen Sicherheitspraktiken ASST bis TEST (14 Praktiken, über 900 Controls im Anwenderkatalog); nicht Gegenstand dieses Handbuchs. (Kapitel 1.2)

**Managementbericht** – Verdichtetes Berichtsdokument der Managementbewertung an die Institutionsleitung; Rahmen und Maßnahmenvorschläge MUSS, acht Inhaltsbausteine SOLLTE (PERF.4.1 mit Sub-Controls, PERF.4.2); zugleich Vehikel der ISMS-Freigabe (GC.1.2). (Kapitel 8.4)

**Modalverb** – Verbindlichkeitsstufe eines Statements nach RFC 2119 / DIN 820-2: MUSS (uneingeschränkt), SOLLTE (Abweichung nur begründet und dokumentiert), KANN (definiert, in der Methodik unbenutzt). Bestand: 76 MUSS, 19 SOLLTE. (Kapitel 3.2)

**Nicht-Konformität** – Abweichung von Anforderungen des ISMS, unabhängig von der Entdeckungsquelle; systematisch zu erfassen, ursachenanalytisch zu bearbeiten (VRB.2). Verhältnis zum Begriff „Fehler" in VRB.4.1: Anhang D. (Kapitel 7.2)

**Parameter** – Belegbare Platzhalter in Statements (`{{…}}`), von der Institution mit konkreten Werten zu füllen (STM.5.1); 14 in der Methodik, davon acht `{{regelmäßig}}`-Varianten. (Kapitel 3.3)

**Praktik** – Oberste Gliederungseinheit des Katalogs und zugleich Adressat der Anforderungen („Governance und Compliance MUSS …"); fünf Methodik-Praktiken, definiert im Namespace `practices.csv`. (Kapitel 2.1, 2.3)

**Profil (OSCAL Profile)** – Dokumenttyp für Auswahl, Parametrisierung und Anpassung über Katalogen; der Anwenderkatalog entsteht durch Auflösung des Grundschutz++-Profils, Blaupausen sind technisch weitere Profile. (Kapitel 3.8)

**Restrisiko** – Risiko aus nicht umgesetzten Anforderungen; Bewertung SOLLTE (UMS.1.2), im Zertifizierungskontext faktisch Pflicht samt Risikoübernahme durch die Leitung. (Kapitel 6.1, 9.3)

**Risikoeigentümer** – Rolle aus der Risikomethodik (GC.12.1, Guidance); zeichnet laut Guidance zu VRB.5.1 die Freigabe im Umsetzungsplan. (Kapitel 4.12, 7.5)

**Schutzbedarf** – Zweistufige Einstufung („normal" / „hoch") von Geschäftsprozessen oder Informationen nach Bedeutung für Geschäftsziele oder gesetzlichen Auftrag (GC.7.1.2); „hoch" löst die dedizierte Risikobetrachtung aus (GC.7.2). (Kapitel 4.7)

**sec_level** – Sicherheitsstufe eines Controls: „normal-SdT" oder „erhöht" (Namespace `security_level.csv`); in der Methodik durchgängig „normal-SdT", gesteuert über STM.3.1. (Kapitel 3.4, 5.3)

**Statement** – Normativer Anforderungssatz eines Controls nach der Satzschablone Praktik + Modalverb + Result + Result-Spezifikation + Action Word. (Kapitel 3.2)

**Umsetzungsplan** – Gemeinsames Steuerungsdokument von UMS und VRB für alle Maßnahmen samt Zuständigen, Fristen, Prioritäten und Risiken; Gegenstück zum alten *Realisierungsplan*. (Kapitel 6.2, 7.5)

**Umsetzungsstatus** – Binäre Feststellung je Anforderung: umgesetzt oder nicht umgesetzt; umgesetzt nur, wenn auch alle abhängigen Anforderungen umgesetzt sind (UMS.1.1, Guidance). (Kapitel 6.1)

**Vererbung** – Deterministische Erweiterung der Zielobjektkategorie-Zuordnung eines Assets um alle Elternknoten der Zielobjekthierarchie (STM.2.1.4.1); automatisierbar und zur Automatisierung empfohlen. (Kapitel 5.2)

**Verbundweite Anforderungen** – Die Anforderungen der ISMS-Praktiken, die ohne Selektion einmalig auf den gesamten Informationsverbund modelliert werden (STM.2.1.1, Guidance). (Kapitel 5.2)

**Wirksamkeitsprüfung** – Test, ob umgesetzte Korrektur- und Verbesserungsmaßnahmen ihre Wirkung erreichen (VRB.6.1 MUSS), samt bewertendem Verfahren darüber (VRB.6.2 SOLLTE). (Kapitel 7.6)

**Zielobjektkategorie** – Standardisierte Klasse, über die Kernel-Anforderungen an Assets modelliert werden; 39 Kategorien mit Hierarchie im Namespace `target_object_categories.csv`; funktionaler Nachfolger der Bausteine; in der Methodik selbst nicht belegt. (Kapitel 3.7, 5.2)

---

*Ende Anhang C (v0.1). Fehlende Begriffe bitte mit Fundstelle nachmelden.*
