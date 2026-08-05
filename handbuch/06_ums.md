# Kapitel 6: UMS – Umsetzung

**Handbuch zur Grundschutz++ Methodik · Kapitel-Version 0.8 (Entwurf)**
Stand: 2026-08-02 · Normative Basis: `BSI-Methodik-Grundschutz++-catalog.json`, Build 2026-07-29 · Gliederungsbezug: Kapitel 6 gemäß `00_gliederung_v0.1.md`

## 6.0 Einordnung: wo das Anforderungspaket Arbeit wird

Die Umsetzung (UMS) ist die Do-Phase der Methodik und mit elf Controls die kompakteste der fünf Praktiken: 10 MUSS, 1 SOLLTE, und nur die Restrisiko-Bewertung (UMS.1.2) trägt einen `effort_level` über null (Stufe 2). Ihr Leitdokument ist der Umsetzungsplan, an dem sechs der elf Controls hängen; er ist das Grundschutz++-Gegenstück zum Realisierungsplan (Referenzdokument A.6) der alten Welt und zugleich das Bindeglied zu PERF (Evaluation des Umsetzungsplans, PERF.1.2) und VRB (Fortschreibung, VRB-Bezug auf denselben Plan).

Die Praktik folgt einer schlichten Logik: Status feststellen (UMS.1), Maßnahmen planen und priorisieren (UMS.2), Zuständige benennen (UMS.3), Fristen setzen (UMS.4), Ausnahmen regeln (UMS.5), Fortschritt verfolgen und den Plan fortschreiben (UMS.6), Compliance im Prozess halten (UMS.7). Das liest sich wie solides Projektmanagement, und genau das ist der Punkt: Grundschutz++ verlangt hier keine Sicherheitsmagie, sondern nachweisbare Arbeitsorganisation. Die eine wirklich harte methodische Entscheidung steckt im Statusmodell, und sie verdient den ersten Kasten des Kapitels.

## 6.1 UMS.1 Umsetzungsstatus: ja oder nein, nichts dazwischen

**Anforderungsbezug.**

| Control | Verbindlichkeit | Kern | Dokument |
|---|---|---|---|
| UMS.1.1 Ermittlung des Umsetzungsstatus | MUSS | Umsetzungsstatus aller Anforderungen im Paket vollständig `{{regelmäßig}}` überprüfen | keines zugeordnet |
| UMS.1.2 Bewertung des Restrisikos | SOLLTE | Restrisiko durch nicht umgesetzte Anforderungen festlegen | keines zugeordnet |

> „Umsetzung MUSS den Umsetzungsstatus der Anforderungen im Anforderungspaket vollständig `{{regelmäßig}}` überprüfen." (UMS.1.1)

Die Guidance dazu ist die vielleicht folgenreichste Einzelaussage der Praktik: Der Status kann nur „umgesetzt" oder „nicht umgesetzt" sein, und eine Anforderung gilt erst dann als umgesetzt, wenn sie selbst und alle in Abhängigkeit stehenden Anforderungen umgesetzt sind.

> **Abweichung zu 200-2:** Der IT-Grundschutz-Check nach 200-2 kennt vier Umsetzungsstatus: „entbehrlich", „ja", „teilweise", „nein". Grundschutz++ kennt in UMS.1.1 genau zwei: umgesetzt oder nicht umgesetzt. „Teilweise" entfällt ersatzlos, eine teilweise umgesetzte Anforderung ist nicht umgesetzt. „Entbehrlich" entfällt als Status und wandert als Entscheidung nach vorn: Nicht relevante Anforderungen werden bereits in der Modellierung gestrichen (STM.2.1.5, mit dokumentierter Begründung), bewusste Nichtumsetzung läuft über das Ausnahmemanagement (UMS.5). Wer sein altes GS-Check-Tooling weiterbenutzt, importiert ein Statusmodell, das der Katalog nicht mehr kennt.

Die Festlegung reicht bis in die OSCAL-Dokumentation: Von den Statuswerten, die OSCAL für die Umsetzung vorsieht, nutzt das BSI nur „implemented" für umgesetzt; alles andere bleibt leer und bedeutet nicht umgesetzt, denn ein ausdrückliches „nein" kennt OSCAL nicht (Kapitel 3.9; die Festlegung ist in den Repository-Quellen bislang nicht dokumentiert, Anhang D, D32).

Wie die Streichung nicht relevanter Anforderungen technisch zu vollziehen ist, sagt weder die Methodik noch das Begleitmaterial: STM.2.1.5 verlangt nur das Streichen aus dem Anforderungspaket samt dokumentierter Begründung, ohne einen OSCAL-Mechanismus zu benennen. OSCAL kennt dafür zwei denkbare Orte, das Profil (die Anforderung wird gar nicht erst importiert) und den System-Sicherheitsplan (das Control wird als nicht anwendbar gekennzeichnet). Die Repository-Quellen deuten auf den Profilweg: Die OSCAL-FAQ nennt als Zweck von Profilen ausdrücklich, dass nicht anwendbare Anforderungen entfernt werden, und der SSP-Generator der Werkzeugsammlung arbeitet genau so; er erzeugt ein institutionsspezifisches Profil, das nur die ausgewählten Controls importiert (include-controls mit with-ids-Positivliste), und baut den System-Sicherheitsplan darauf auf, gestrichene Anforderungen erscheinen dort also nie. Auch der SSP-Weg ist technisch gangbar: OSCAL kennt den Statuswert „not-applicable", die Werkzeugsammlung bietet ihn als „N/A" an, und er bliebe von der leeren Angabe unterscheidbar; ob die binäre Statusfestlegung diesen Wert unberührt lässt, ist mangels Veröffentlichung offen (D32). Verbindlich geregelt ist keiner der beiden Wege, und auch für die von STM.2.1.5 geforderte Begründung der Streichung ist kein OSCAL-Ablageort benannt (Anhang D, D33).

**Umsetzungshinweise.** Das binäre Modell nimmt dem Schönfärben die Grundlage, denn der vertraute Ausweg „teilweise", mit dem sich halbfertige Maßnahmen jahrelang tragen ließen, fehlt. Das hat allerdings zwei ernste Kosten. Erstens gehen Nuancen verloren: „Teilweise" trug Information, nämlich dass begonnen wurde, wie weit die Umsetzung gediehen ist und was noch fehlt. Im binären Status ist eine zu neunzig Prozent fertige Maßnahme von einer unbegonnenen nicht zu unterscheiden; die Dokumentation wird an dieser Stelle schlechter, nicht besser. Diese Information muss anderswo überleben, realistisch im Umsetzungsplan mit Maßnahmenständen und Restarbeiten (UMS.2, UMS.6), sonst ist sie weg. Zweitens ist die leere Angabe doppeldeutig: Sie steht für „geprüft und nicht umgesetzt" ebenso wie für „noch gar nicht bearbeitet"; die Werkzeuge der Bibliothek zeigen die leere Angabe folgerichtig als „Offen" an. Aus der Statusliste selbst ist damit nicht ablesbar, ob die Erhebung vollständig war; 200-2 konnte genau das mit dem ausdrücklichen „nein" vom fehlenden Eintrag unterscheiden. Wer die Vollständigkeit der Erhebung belegen will, braucht einen Vermerk außerhalb des Status, etwa ein Erhebungsdatum je Anforderung. Nehmen Sie außerdem die Abhängigkeitsregel ernst: Sie brauchen eine gepflegte Sicht darauf, welche Anforderungen voneinander abhängen, sonst ist „umgesetzt" nicht belastbar feststellbar (wo diese Abhängigkeiten herkommen, ist eine offene Frage, siehe Abschnitt 6.9). Setzen Sie den Parameter `{{regelmäßig}}` realistisch; er ist das vereinbarte Prüfintervall, an dem Sie gemessen werden. Die Restrisiko-Bewertung nach UMS.1.2 ist nur SOLLTE, aber die Guidance zeigt den Zweck: konsolidiert aufbereitet macht sie die Lücken für die Institutionsleitung nachvollziehbar, und genau dort gehören sie hin.

**Audit-Perspektive.** Die Statusliste übernimmt die Rolle des Referenzdokuments A.4 (Ergebnis des IT-Grundschutz-Checks). Übertragen aus dem Auditierungsschema kommt eine Verschärfung hinzu: Das Schema behandelt nicht umgesetzte Anforderungen so, dass die entstehenden Risiken bewertet, der Leitungsebene transparent dargestellt und von dieser per Unterschrift oder elektronischer Freigabe getragen werden müssen. Im Katalog ist die Restrisiko-Bewertung dagegen nur SOLLTE; diese Spannung ist real und in Abschnitt 6.9 als offene Frage vermerkt. Praktisch heißt das: Wer UMS.1.2 auslässt, mag katalogkonform argumentieren, wird aber im Zertifizierungsverfahren die Risikoübernahme der Leitung trotzdem nachweisen müssen. Ein Vor-Ort-Klassiker bleibt der Stichprobenabgleich: Status „umgesetzt" auf dem Papier gegen die Realität am System.

**Typische Fehler.** Der Status wird einmal vor dem Audit erhoben statt `{{regelmäßig}}`. Halbfertige Maßnahmen werden als umgesetzt geführt, weil das alte „teilweise" im Kopf weiterlebt. Abhängigkeiten sind nirgends erfasst, sodass Anforderungen als erledigt gelten, deren Voraussetzungen fehlen. Und das Restrisiko existiert als Excel-Liste beim ISB, die die Leitung nie gesehen hat.

## 6.2 UMS.2 Umsetzungsplanung: aus dem Paket wird ein Plan

**Anforderungsbezug.**

| Control | Verbindlichkeit | Kern | Dokument |
|---|---|---|---|
| UMS.2.1 Umsetzungsplanung | MUSS | Maßnahmen für nicht umgesetzte Anforderungen gemäß strukturierter Vorgehensweise festlegen | Umsetzungsplan |
| UMS.2.2 Priorisierung von Maßnahmen | MUSS | Priorisierung auf Basis von Risikobewertung, Abhängigkeiten und Ressourcenverfügbarkeit festlegen | Umsetzungsplan |

Das Ergebnis beschreibt die Guidance zu UMS.2.1 als Überführung „des unstrukturierten Anforderungspakets hin zu einem strukturierten Umsetzungsplans" [sic]. Der Hebel dabei: Maßnahmen und Anforderungen sind nicht eins zu eins; eine gute Maßnahme deckt mehrere Anforderungen zugleich ab, und die Guidance verlangt ausdrücklich, solche Synergien zu suchen.

**Umsetzungshinweise.** Denken Sie in Maßnahmen, nicht in Anforderungszeilen. Ein zentrales Patch- und Härtungsprojekt, eine MFA-Einführung oder ein Berechtigungskonzept erledigen jeweils Dutzende Anforderungszeilen; der Umsetzungsplan sollte diese Bündelung abbilden, mit Rückverweis auf die abgedeckten Control-IDs. Für die Priorisierung nennt das Statement drei Kriterien (Risikobewertung, Abhängigkeiten, Ressourcenverfügbarkeit), die Guidance ergänzt gesetzliche Verpflichtungen und Umsetzungsaufwand. Aus der Beratungspraxis: Priorisieren Sie zuerst nach Risiko und gesetzlicher Pflicht, dann nach Aufwand, und dokumentieren Sie die Reihenfolge-Entscheidung; ein Plan, dessen Reihenfolge niemand begründen kann, ist im Audit nur eine Liste.

**Audit-Perspektive.** Der Umsetzungsplan ist das A.6-Gegenstück und wird auf zwei Dinge geprüft: Vollständigkeit (findet sich jede nicht umgesetzte Anforderung aus UMS.1.1 im Plan wieder?) und Begründbarkeit der Priorisierung gegen die genannten Kriterien. Eine nicht umgesetzte Anforderung, die in keinem Plan auftaucht, ist der direkte Weg zur Abweichung, denn dann fehlt der Nachweis, dass die Institution ihre Lücken überhaupt steuert.

**Typische Fehler.** Der Plan ist eine umbenannte Kopie der Statusliste, ohne Maßnahmenbündelung und ohne Prioritäten. Die Priorisierung folgt der Lautstärke der Fachbereiche statt der Risikobewertung. Quick Wins werden abgearbeitet, während die unbequemen Hochrisiko-Maßnahmen seit drei Planversionen auf „Q4" stehen.

## 6.3 UMS.3 Umsetzungszuständige: eindeutig heißt eine

**Anforderungsbezug.**

| Control | Verbindlichkeit | Kern | Dokument |
|---|---|---|---|
| UMS.3.1 Benennung von Umsetzungszuständigen | MUSS | Zuständige für die Umsetzung nicht erfüllter Anforderungen eindeutig zuweisen | Umsetzungsplan |

Die Guidance verlangt Kompetenzen und Ressourcen bei den Zugewiesenen, Abstimmung mit den betroffenen Bereichen für Akzeptanz, und erlaubt bei komplexeren Maßnahmen die Trennung in fachliche und operative Verantwortung samt Teilaufgaben.

**Umsetzungshinweise.** „Eindeutig" ist das Schlüsselwort: pro Maßnahme genau eine verantwortliche Rolle, keine Gremien, keine Doppelspitzen ohne Klärung, wer entscheidet. Die Trennung fachlich/operativ aus der Guidance ist in der Praxis Gold wert, etwa Fachverantwortung beim Prozesseigner, operative Umsetzung beim Systembetrieb. Und weisen Sie niemandem eine Maßnahme zu, der weder Budget noch Zugriff hat; die Guidance nennt Kompetenzen und Ressourcen nicht zur Zierde.

**Audit-Perspektive.** Schnell geprüft: Spalte „Zuständig" im Umsetzungsplan, Stichprobe im Interview („Wussten Sie, dass Sie diese Maßnahme verantworten?"). Zuständige, die von ihrer Zuständigkeit nichts wissen, sind eine der ergiebigsten Vor-Ort-Feststellungen überhaupt.

**Typische Fehler.** Zuständig ist „die IT". Zuständig ist der ISB, für alles, womit UMS.3.1 formal erfüllt und praktisch beerdigt ist. Personen statt Rollen, und nach dem nächsten Weggang zeigt der halbe Plan auf ein verwaistes Postfach.

## 6.4 UMS.4 Umsetzungsfristen: Termine, die gehalten werden müssen

**Anforderungsbezug.**

| Control | Verbindlichkeit | Kern | Dokument |
|---|---|---|---|
| UMS.4.1 Festlegung von Umsetzungsfristen | MUSS | realistisches Zieldatum für nicht umgesetzte Anforderungen festlegen | Umsetzungsplan |

Die Guidance verlangt dreierlei: Das Zieldatum berücksichtigt Umfang, Ressourcen und Abhängigkeiten; die Einhaltung wird nachgehalten; bei Überschreitung werden geeignete Maßnahmen eingeleitet.

**Umsetzungshinweise.** „Realistisch" schützt vor dem verbreiteten Reflex, alle Fristen auf das Audit-Datum zu legen. Planen Sie gegen Kapazität, nicht gegen Wunsch, und definieren Sie vorab, was bei Fristriss passiert: Eskalation an wen, Neubewertung wann, gegebenenfalls Aussprung in die Risikobetrachtung nach STM.4.1, wenn aus dem Verzug eine dauerhafte Nichtumsetzung wird. Fristen ohne Konsequenzmechanismus sind Dekoration.

**Audit-Perspektive.** Der Auditor liest die Fristenhistorie: Wie oft wurden Termine verschoben, gibt es Nachweise für die eingeleiteten Maßnahmen bei Überschreitung. Ein Plan, in dem dieselbe Maßnahme dreimal kommentarlos verschoben wurde, belegt das Gegenteil von „nachgehalten" und liefert die Abweichung gleich mit Begründung.

**Typische Fehler.** Sammeltermine („alles bis Jahresende"), die niemand ernst nimmt. Verschiebungen ohne Entscheidung und ohne Spur. Fristen, die nur der ISB kennt, während die Zuständigen aus UMS.3.1 nie eingebunden wurden.

## 6.5 UMS.5 Ausnahmemanagement: der geregelte Weg am Soll vorbei

**Anforderungsbezug.**

| Control | Verbindlichkeit | Kern | Dokument |
|---|---|---|---|
| UMS.5.1 Autorisierung von Ausnahmen | MUSS | Ausnahmegenehmigungen durch `{{eine zuständige Person oder Rolle}}` autorisieren | keines zugeordnet |
| UMS.5.2 Dokumentation von Ausnahmen | MUSS | Ausnahmegenehmigungen mit Begründung dokumentieren | Freigegebene Ausnahmegenehmigung |

UMS.5.1 adressiert laut Guidance Zielkonflikte zwischen Verpflichtungen: Wo Anforderungen kollidieren, wird abgewogen und die Ausnahme von der parametrisierten zuständigen Stelle autorisiert, gestützt auf eine Risikobetrachtung, wo nötig. UMS.5.2 verlangt die dokumentierte Begründung, und die Guidance ist erfreulich modern: Die Dokumentation darf in die Geschäftsprozesse integriert werden, ausdrücklich genannt werden CMDBs, Aktenverzeichnisse, Commit-Messages und Ticketsysteme.

**Umsetzungshinweise.** Definieren Sie den Ausnahmeprozess, bevor die erste Ausnahme gebraucht wird: Antrag, Risikobewertung, Autorisierungsinstanz (Parameter setzen, konsistent mit GC.9), Befristung, Wiedervorlage. Befristen Sie jede Ausnahme; unbefristete Ausnahmen sind keine Ausnahmen, sondern stillschweigende Regeländerungen. Die Erlaubnis zur integrierten Dokumentation sollten technische Teams nutzen: Eine begründete Ausnahme in der Commit-Message oder im Ticket ist auffindbarer als ein Formular im Laufwerk, solange die Fundstelle im ISMS referenziert ist. Und denken Sie an den Aussprung: Nicht-Umsetzung ist einer der Risikobetrachtungs-Auslöser aus STM.4.1.

**Audit-Perspektive.** Das Dokument „Freigegebene Ausnahmegenehmigung" ist die Evidenz; geprüft wird die Kette Antrag, Begründung, Autorisierung durch die parametrisierte Stelle, Befristung. Ausnahmen, die faktisch gelebt, aber nie autorisiert wurden, sind keine Ausnahmen, sondern nicht umgesetzte Anforderungen ohne Steuerung, und genau so wird der Auditor sie werten.

**Typische Fehler.** Die Autorisierungsinstanz ist nie parametrisiert worden, also autorisiert de facto der ISB sich selbst. Ausnahmen ohne Enddatum sammeln sich über Jahre. Die Begründung lautet „aus betrieblichen Gründen" und erklärt nichts. Verstreute Dokumentation ohne zentrales Register, sodass niemand sagen kann, wie viele Ausnahmen aktuell gelten.

## 6.6 UMS.6 Umsetzungsfortschrittsverfolgung: der Plan lebt

**Anforderungsbezug.**

| Control | Verbindlichkeit | Kern | Dokument |
|---|---|---|---|
| UMS.6.1 Nachverfolgung des Umsetzungsfortschritts | MUSS | Verfahren für die Nachverfolgung der Maßnahmenumsetzung verankern | Umsetzungsplan |
| UMS.6.2 Fortschreibung des Umsetzungsplans | MUSS | Verfahren zur Fortschreibung des Umsetzungsplans verankern | Umsetzungsplan |

Die Guidance zu UMS.6.1 empfiehlt einen vollständigen Verfolgungszyklus von Planung und KPI-Definition über Status-Reporting und Soll-Ist-Vergleiche bis zu Ursachenanalyse, Korrekturmaßnahmen und Lessons Learned. UMS.6.2 hält den Plan aktuell: Zeitpläne und Ressourcen anpassen, Prioritäten neu bewerten, neue Maßnahmen ergänzen, obsolete streichen und, bemerkenswert, die Erkenntnisse aus der Wirksamkeitsprüfung integrieren, womit der Katalog die Brücke zu VRB.6 schlägt.

**Umsetzungshinweise.** Beide Controls verlangen Verfahren, nicht Heldentaten: ein fester Berichtstakt, ein Soll-Ist-Vergleich gegen die Fristen aus UMS.4.1, eine definierte Eingangstür für Änderungen am Plan. Wer den Umsetzungsplan in einem Ticketsystem oder ISMS-Tool führt, bekommt Nachverfolgung und Fortschreibung fast geschenkt; wer ihn als Dokument führt, braucht Disziplin und Versionierung nach GC.11.1. Entscheidend ist die Rückkopplung: Statusergebnisse aus UMS.1.1 und Wirksamkeitsbefunde aus VRB.6 müssen den Plan tatsächlich verändern, sonst ist die Fortschreibung Fassade.

**Audit-Perspektive.** Die Versionshistorie des Umsetzungsplans erzählt dem Auditor die Wahrheit über die Praktik: Ein Plan mit lebendiger Änderungshistorie, nachvollziehbaren Neubewertungen und integrierten Prüfergebnissen belegt ein funktionierendes Verfahren; ein Plan mit Stand vom letzten Audit belegt das Gegenteil, und zwar für UMS.6.1 und UMS.6.2 gleichzeitig.

**Typische Fehler.** Das Reporting misst Aktivität („80 Prozent der Tickets bearbeitet") statt Wirkung. Der Plan wird nur vor Audits aktualisiert. Erkenntnisse aus Wirksamkeitsprüfungen und Vorfällen landen in Protokollen, aber nie im Plan.

## 6.7 UMS.7 Compliance-Management: die Pflicht bleibt im Prozess

**Anforderungsbezug.**

| Control | Verbindlichkeit | Kern | Dokument |
|---|---|---|---|
| UMS.7.1 Wahrung von Compliance in der Umsetzung | MUSS | Verfahren zur Überprüfung von Compliance im Umsetzungsprozess verankern | Compliance-Verpflichtungen |

Die Guidance verlangt die regelmäßige Überprüfung und Aktualisierung der compliance-bezogenen Prozesse und Anweisungen, damit sie bei sich ändernder Regulierung wirksam bleiben, und nennt Prüflisten oder Auditierung als geeignete Verfahren.

**Umsetzungshinweise.** Das ist das Umsetzungs-Gegenstück zu GC.3: Dort wird erfasst, was gilt; hier wird geprüft, dass die Umsetzung es einhält. Praktisch genügt eine Compliance-Spalte im Umsetzungsplan plus eine Prüfliste je einschlägiger Verpflichtung, angewendet bei Maßnahmenabschluss. Wichtig ist der Aktualisierungspfad: Ändert sich eine Verpflichtung im Kataster (GC.3.1), müssen die betroffenen Maßnahmen und Anweisungen nachgezogen werden; verankern Sie diesen Trigger explizit.

**Audit-Perspektive.** Geprüft wird am Beispiel: Der Auditor nimmt eine Verpflichtung aus dem Kataster und verfolgt sie bis in die umgesetzte Maßnahme. Reißt die Kette (Verpflichtung erfasst, aber in keiner Maßnahme berücksichtigt), steht der Verdacht im Raum, dass das Compliance-Management aus GC.3 ein Papiertiger ist; die Feststellung trifft dann beide Praktiken.

**Typische Fehler.** Compliance wird bei der Planung einmal bedacht und bei Änderungen der Rechtslage nie wieder. Die Prüfliste existiert, wird aber nur bei Neuprojekten angewendet, nicht im Bestand.

## 6.8 Dokumenten-Output der Praktik

| Dokument | Gefordert durch |
|---|---|
| Umsetzungsplan | UMS.2.1, UMS.2.2, UMS.3.1, UMS.4.1, UMS.6.1, UMS.6.2 |
| Freigegebene Ausnahmegenehmigung | UMS.5.2 |
| Compliance-Verpflichtungen | UMS.7.1 |

Drei Controls fordern kein Dokument (UMS.1.1, UMS.1.2, UMS.5.1). Gerade beim Umsetzungsstatus ist das bemerkenswert: Die Statusliste, funktional das A.4-Gegenstück und eine der wichtigsten Auditevidenzen, hat im Katalog kein zugeordnetes Dokument. In der Praxis gehört sie als Bestandteil oder Anlage zum Umsetzungsplan, gelenkt nach GC.11.1; die fehlende Zuordnung steht in Abschnitt 6.9.

## 6.9 Offene Fragen und Katalogfunde

1. **Woher kommen die Abhängigkeiten?** UMS.1.1 macht die Umsetzung einer Anforderung von „allen in Abhängigkeit stehenden Anforderungen" abhängig, aber der Methodik-Teil des Katalogs enthält kein Feld, das solche Abhängigkeiten definiert. Die Control-Verschachtelung scheidet als Quelle aus, denn sie ist rein thematische Gruppierung (Kapitel 3.1); offen bleibt, ob OSCAL-`links` im Kernel oder institutionsindividuelle Festlegungen gemeint sind. Ohne Klärung ist das Statusmodell nicht vollständig operationalisierbar.
2. **Restrisiko nur SOLLTE.** UMS.1.2 stuft die Restrisiko-Bewertung als SOLLTE ein, während das Auditierungsschema (Abschnitt 4.5) für nicht umgesetzte Anforderungen die Risikodarstellung gegenüber der Leitungsebene und deren dokumentierte Risikoübernahme verlangt. Für zertifizierungswillige Institutionen ist das SOLLTE damit faktisch ein MUSS; die Diskrepanz sollte bei einem künftigen GS++-Prüfschema aufgelöst werden.
3. **Kein Dokument für den Umsetzungsstatus.** UMS.1.1 ohne `documentation`-Prop, obwohl die Statusliste zentrale Auditevidenz ist (vgl. Abschnitt 6.8).
4. **Begriffsschärfe „Verpflichtungen" in UMS.5.1.** Das Statement autorisiert Ausnahmen „für Verpflichtungen", die Guidance behandelt Zielkonflikte zwischen Verpflichtungen und die Nicht-Umsetzung von Anforderungen. Ob Ausnahmen nur von Compliance-Verpflichtungen (GC.3) oder von beliebigen Katalog-Anforderungen gemeint sind, sollte geklärt werden; dieses Handbuch liest UMS.5 als Ausnahmemanagement für beides.

---

*Ende Kapitel 6 (v0.8). Review-Anmerkungen bitte gegen die Control-IDs.*
