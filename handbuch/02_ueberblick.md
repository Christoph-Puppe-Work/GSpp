# Kapitel 2: Die Methodik im Überblick

**Handbuch zur Grundschutz++ Methodik · Kapitel-Version 0.5 (Entwurf)**
Stand: 2026-08-02 · Normative Basis: `BSI-Methodik-Grundschutz++-catalog.json`, Build 2026-07-29; Praktik-Definitionen aus `documentation/namespaces/practices.csv` (Repo-Snapshot 2026-08-02) · Gliederungsbezug: Kapitel 2 gemäß `00_gliederung_v0.1.md`

## 2.1 Fünf Praktiken, ein Verfahren

Die Grundschutz++-Methodik besteht aus fünf Praktiken mit zusammen 95 Controls; hinzu kommen die vier RISK-Controls (RISK.1.1, RISK.1.3, RISK.1.5, RISK.1.10), die der Anwenderkatalog aus dem Katalog „BSI Anforderungen zum Risikomanagement" importiert und die neben der Methodik gelten (Exkurs in Kapitel 4.12). Der Namespace `practices.csv` definiert jede Praktik und ordnet ihr eine Nummer und einen Alternativnamen zu; die Kurzfassung:

| Praktik | Controls | Aufgabe (nach Namespace-Definition) | Handbuch |
|---|---|---|---|
| GC – Governance und Compliance | 35 (31 MUSS / 4 SOLLTE) | strategischer Rahmen: das „Was" und „Warum", Einbindung der Führungsebene, Integration externer und interner Anforderungen | Kapitel 4 |
| STM – Strukturmodellierung | 15 (14 / 1) | aus dem Katalog ein individuelles Anforderungspaket für die Institution generieren; auch bekannt als „Modellierung" | Kapitel 5 |
| UMS – Umsetzung | 11 (10 / 1) | systematische Planung, Implementierung und Dokumentation der Maßnahmen; „Realisierung von Sicherheitsmaßnahmen" | Kapitel 6 |
| VRB – Verbesserung | 10 (8 / 2) | kontinuierliche Weiterentwicklung; schließt den PDCA-Zyklus ab und stößt den neuen an | Kapitel 7 |
| PERF – Monitoring-Evaluation | 24 (13 / 11) | Überwachung und Bewertung; laut Namespace ausdrücklich die „Check-Phase" im PDCA-Zyklus | Kapitel 8 |

Die Arbeitsteilung in einem Satz: GC entscheidet, was gelten soll; STM übersetzt es in ein konkretes Anforderungspaket; UMS arbeitet das Paket ab; PERF misst, ob es wirkt; VRB macht aus den Messergebnissen Veränderung, und der Zyklus beginnt von vorn.

## 2.2 Der Wirkzyklus: PDCA mit einer Eigenheit in der Reihenfolge

Auf das klassische PDCA-Modell abgebildet: Plan sind GC und STM, Do ist UMS, Check ist PERF, Act ist VRB. Der Katalog selbst benennt die Zuordnung in den Namespace-Definitionen (PERF als Check-Phase, VRB als Abschluss und Neustart des Zyklus) und in der Guidance zu VRB.1.1. Die Eigenheit: Die Katalogreihenfolge stellt VRB vor PERF, der Wirkfluss läuft umgekehrt. Dieses Handbuch folgt der Katalogreihenfolge in der Kapitelfolge und beschreibt den Wirkfluss in Kapitel 8.6 im Detail; die Übergabepunkte sind konkret benannt: Auditfeststellungen und Monitoring-Befunde aus PERF landen als Nicht-Konformitäten und Verbesserungspotenziale in VRB (VRB.2, VRB.3), dessen Maßnahmen fließen in den Umsetzungsplan (VRB.5.1) und damit zurück in die Maschinerie von UMS, und der Managementbericht (PERF.4) verkettet die Zyklen, weil er den Status der Folgemaßnahmen der jeweils letzten Bewertung dokumentiert (PERF.4.1.1).

Zwei Takte halten den Zyklus zusammen. Der große: GC.1.1 gilt laut Guidance erst als erfüllt, wenn die komplette Vorgehensweise mindestens einmal vollständig durchlaufen wurde; der erste Zyklus ist also das Abnahmekriterium des ganzen ISMS. Der kleine: Acht der 14 Parameter der Methodik sind `{{regelmäßig}}`-Varianten (Kapitel 3.3), und jede Institution bestimmt mit ihrer Belegung selbst, wie schnell ihr Zyklus schlägt.

## 2.3 Die Praktik als Adressat

Jedes Statement der Methodik adressiert die Praktik selbst: „Governance und Compliance MUSS …", „Strukturmodellierung MUSS …". Das ist die auffälligste sprachliche Neuerung gegenüber der 200-2-Welt, und sie hat einen praktischen Sinn: Der Katalog schreibt nicht vor, welche Person oder Organisationseinheit die Leistung erbringt, sondern dass die Institution die Praktik so organisieren muss, dass das Ergebnis entsteht. Die Zuordnung zu Rollen geschieht an zwei definierten Stellen: strukturell über die Sicherheitsorganisation (GC.9: Rollen, Zuständigkeiten, Befugnisse, Stellvertretung, Interessenkonflikte) und fein über Zuständigkeits-Parameter (STM.5.1). Für ISBs heißt das umgekehrt: Wer im Audit gefragt wird, „wer ist bei Ihnen Strukturmodellierung?", muss auf Organigramm, Rollenbeschreibungen und Parameterwerte zeigen können, nicht auf sich selbst.

## 2.4 Das Dokumentenmodell: 21 Dokumente statt eines Sicherheitskonzepts

59 der 95 Controls fordern über die `documentation`-Prop ein konkretes ISMS-Dokument, insgesamt 21 verschiedene. An die Stelle des monolithischen Sicherheitskonzepts der alten Welt tritt eine Landschaft gelenkter Einzeldokumente, deren Lenkung selbst eine MUSS-Anforderung ist (GC.11.1). Die tragenden Stücke: das ISMS-Regelwerk als Klammer (GC.1.1), die Informationssicherheitsleitlinie samt Strategie und Zielen (GC.5), der Informationsverbund (STM.1), das Anforderungspaket als Arbeitsvorrat des gesamten Systems (STM.2), der Umsetzungsplan als gemeinsames Steuerungsdokument von UMS und VRB, sowie Auditbericht und Managementbericht als Produkte von PERF, mit denen sich der Zyklus gegenüber Leitung und Prüfern belegt. Die vollständige Landkarte mit fordernden Controls, Namespace-Kategorie und Zielgruppe ist Anhang B; die Übersetzung in die Referenzdokumente A.0 bis A.6 der Zertifizierungswelt steht in Kapitel 9.2.

## 2.5 Das Maschinenzimmer: Anwenderkatalog, Kategorien, OSCAL

Unter der Methodik liegt eine Katalogmaschine, und wer sie einmal im Überblick gesehen hat, liest die Praktik-Kapitel mit anderen Augen; die Details trägt Kapitel 3 in den Abschnitten 3.5 bis 3.9.

Der Anwenderkatalog mit seinen 1000 Controls ist ein gebautes Produkt: Ein OSCAL-Profil importiert den Methodik-Katalog und den Kernel vollständig sowie vier RISK-Controls gezielt, setzt erste Parameter und wird zum Gesamtkatalog aufgelöst (3.8). Die 901 Kernel-Anforderungen tragen dabei drei Property-Familien, die die Methodik selbst nicht braucht: ein vierwertiges Schutzziel-Wirkprofil, die elementaren Gefährdungen G 0.1 bis G 0.47 und Zielobjektkategorien (3.5). Diese Kategorien sind die Erben der Bausteine, mit umgekehrter Blickrichtung: Nicht mehr der Baustein bündelt Anforderungen für einen Zielobjekttyp, sondern jede Anforderung trägt ihre Kategorie selbst, und eine Hierarchie mit 39 Kategorien unter sieben Wurzeln vererbt deterministisch von der Wurzel bis zum Blatt (3.7). Die Selektion fürs Anforderungspaket läuft dann über vier Zahnräder: verbundweite Methodik-Grundlast, Kategorien-Auswahl mit Vererbung, die Niveau-Weiche über `sec_level` und die Analyse-Metadaten für Risiko und Priorisierung (3.6). Und über allem steht eine OSCAL-Dokumentfamilie, die vom Katalog über Profil und System-Sicherheitsplan bis zu Prüfplan, Prüfergebnissen und Maßnahmenplan reicht; für die komplette Staffel existieren browserbasierte Werkzeuge; die Umsetzungsebene der Bibliothek ist mit ersten Komponenten-Vorlagen gefüllt, die Prüfebene noch leer (3.9).

## 2.6 Wie ein Grundschutz++-ISMS anläuft

Die Reihenfolge des ersten Zyklus ergibt sich aus den Abhängigkeiten der Controls; als Wegweiser für die ersten Monate, mit den Kapiteln, die die Details tragen:

Zuerst der Rahmen: ISMS-Verfahren verankern und den Standard-Parameter setzen (GC.1.1), Kontext und Stakeholder analysieren (GC.2, GC.4), Compliance-Kataster aufbauen (GC.3), messbare Ziele, Strategie und Leitlinie festlegen und von der Leitung autorisieren lassen (GC.5), Geltungsbereich nach Leitungsfreigabe abgrenzen (GC.6.1), Sicherheitsorganisation mit unabhängigem ISB aufstellen (GC.9), Dokumentenlenkung und Risikomethodik verankern (GC.11, GC.12), Ressourcen und Kommunikationswege regeln (GC.8, GC.10). Dann die Einstufung: Geschäftsprozesse festlegen, Schutzbedarf zweistufig einstufen, den wichtigsten Prozess durch die Leitung bestimmen lassen (GC.7). Dann die Modellierung: Informationsverbund abgrenzen (STM.1), für den wichtigsten Prozess Assets erfassen, Zielobjektkategorien zuweisen und das Anforderungspaket erzeugen (STM.2), Sicherheitsniveau prüfen (STM.3), nötige Risikobetrachtungen ausführen (STM.4, GC.7.2), Parameter setzen (STM.5). Dann die Umsetzung: Status binär erheben, Maßnahmen planen, priorisieren, Zuständige und Fristen festlegen, Ausnahmen regeln, Fortschritt verfolgen (UMS.1 bis UMS.7). Schließlich Messung und Verbesserung: Monitoring und Auditprogramm aufsetzen, erstes internes Audit, Managementbericht an die Leitung (PERF), Feststellungen in Korrekturen und Verbesserungen übersetzen und deren Wirksamkeit testen (VRB). Mit dem Managementbericht und der Leitungsentscheidung darüber ist der erste Zyklus belegt, GC.1.1 erfüllt und GC.1.2 bedient.

Der wichtigste Unterschied zum alten Vorgehen steckt im dritten Schritt: Es ist kein Vollausbau. Der erste Zyklus gilt dem wichtigsten Geschäftsprozess (STM.2.1.2, Guidance), die weiteren Prozesse folgen in den nächsten Zyklen. Klein anfangen ist hier nicht Pragmatismus gegen die Methode, sondern die Methode.

---

*Ende Kapitel 2 (v0.5). Review-Anmerkungen bitte gegen die Control-IDs.*
