# Kapitel 5: STM – Strukturmodellierung

**Handbuch zur Grundschutz++ Methodik · Kapitel-Version 0.4 (Entwurf)**
Stand: 2026-08-02 · Normative Basis: `BSI-Methodik-Grundschutz++-catalog.json`, Build 2026-07-29 · Gliederungsbezug: Kapitel 5 gemäß `00_gliederung_v0.1.md`

## 5.0 Einordnung: vom Geltungsbereich zum Anforderungspaket

Wo die 200-2-Welt vier getrennte Arbeitsschritte kannte (Strukturanalyse, Modellierung, teils ergänzt um eigene Anforderungen), bündelt Grundschutz++ die gesamte Übersetzungsarbeit in einer Praktik: Die Strukturmodellierung (STM) macht aus dem formal festgelegten Geltungsbereich (GC.6.1) einen konkreten Informationsverbund und aus dem Katalog ein individuelles Anforderungspaket. 15 Controls, davon 14 MUSS und 1 SOLLTE; beim Aufwand trägt nur STM.3.1 einen Wert über null (`effort_level` 2), alles andere gilt dem Katalog als Pflichtprogramm der Stufe 0.

Die Praktik kennt genau zwei Dokumente: den Informationsverbund (STM.1) und das Anforderungspaket, an dem zehn der 15 Controls arbeiten (STM.2). Das Anforderungspaket ist der zentrale Begriff des gesamten Grundschutz++: Es ist die Menge aller Anforderungen, die für den betrachteten Informationsverbund und den priorisierten Geschäftsprozess gelten, und es ist zugleich das Arbeitsvorrat-Dokument, das UMS abarbeitet, PERF evaluiert und VRB fortschreibt.

Zwei Eigenheiten prägen die Praktik. Erstens die Modellierungslogik: Anforderungen hängen an Zielobjektkategorien, Assets werden diesen Kategorien zugewiesen, und eine deterministische Vererbung entlang der Zielobjekthierarchie sorgt dafür, dass übergeordnete Kategorien mitwirken (STM.2.1.3, STM.2.1.4.1). Das ersetzt die Baustein-Modellierung der Edition-2023-Welt durch einen Mechanismus, der maschinell ausführbar ist; die Guidance empfiehlt die Automatisierung ausdrücklich. Zweitens das iterative Vorgehen: Im ersten Durchlauf genügt es laut Guidance zu STM.2.1.2, die Assets des wichtigsten Geschäftsprozesses zu erfassen; weitere Prozesse folgen in späteren Zyklen. Grundschutz++ verlangt keine Vollabdeckung im ersten Anlauf, sondern einen vollständigen Durchlauf für das Wichtigste zuerst.

## 5.1 STM.1 Informationsverbund: die technische Antwort auf den Geltungsbereich

**Anforderungsbezug.**

| Control | Verbindlichkeit | Kern | Dokument |
|---|---|---|---|
| STM.1.1 Definition und Abgrenzung des Informationsverbunds | MUSS | nachvollziehbar abgegrenzten Informationsverbund auf Basis des Geltungsbereichs festlegen | Informationsverbund |
| STM.1.2 Dokumentation der externen Schnittstellen | MUSS | Schnittstellen des Informationsverbunds zu externen Prozessen festlegen | Informationsverbund |

> „Strukturmodellierung MUSS den nachvollziehbar abgegrenzten Informationsverbund auf Basis des Geltungsbereichs festlegen." (STM.1.1)

Die Arbeitsteilung mit GC ist präzise: GC.6.1 legt den formalen Geltungsbereich fest, nach Freigabe der Leitung; STM.1.1 füllt ihn mit Substanz. Die Guidance verlangt Festlegungen zu internen und ausgelagerten Anteilen, zugehörigen Institutionsbereichen, Anwendungen, Systemen und Netzen, den technischen Grenzen inklusive genutzter Cloud-Dienste sowie Standorten, Gebäuden und Räumlichkeiten. STM.1.2 ergänzt die organisatorischen, technischen und infrastrukturellen Schnittstellen nach außen.

**Umsetzungshinweise.** Der Informationsverbund ist das Gegenstück zur Strukturanalyse der alten Welt, aber schlanker gedacht: ein gelenktes Dokument, das die Grenzen zieht und die Auslagerungen benennt, kein vollständiges Inventar (das kommt asset-weise in STM.2.1.2). Investieren Sie die Sorgfalt in die Schnittstellen: Jeder Dienstleister, jede Cloud, jede Konzernschwester, die in den Verbund hineinarbeitet, gehört mit Art und Richtung der Schnittstelle dokumentiert. Aus der Beratungspraxis: Die Ausschlüsse aus GC.6.1 und die Schnittstellen aus STM.1.2 sind zwei Seiten derselben Entscheidung; wer etwas ausschließt, schuldet die Schnittstellenbetrachtung dazu.

**Audit-Perspektive.** Das Dokument Informationsverbund übernimmt die Rolle des Referenzdokuments A.1 (Strukturanalyse) und wird in der Dokumentenprüfung vollständig gesichtet; das Auditierungsschema verlangt dort ausdrücklich die Konsistenz der in der Strukturanalyse aufgeführten Eigenschaften mit der Realität vor Ort. Übertragen heißt das: Netzplan-Stichproben, Standortabgleich, und die Frage, ob die dokumentierten Cloud-Dienste die tatsächlich genutzten sind. Ein Verbund, der wesentliche Schnittstellen verschweigt, gefährdet die Aussagekraft des gesamten Audits und wiegt entsprechend schwer.

**Typische Fehler.** Der Informationsverbund ist eine Kopie des Netzplans ohne organisatorische und infrastrukturelle Anteile. Schatten-IT und SaaS-Dienste fehlen, weil niemand die Fachbereiche gefragt hat. Die Schnittstellenliste endet an der Firewall, während der Wartungszugang des Herstellers und der Konzern-Fileshare unerwähnt bleiben.

## 5.2 STM.2 Anforderungspaket: die Fließstrecke der Modellierung

**Anforderungsbezug.** Zehn Controls, zehnmal MUSS, alle auf dasselbe Dokument:

| Control | Verbindlichkeit | Kern | Dokument |
|---|---|---|---|
| STM.2.1 Erstellung eines Anforderungspakets | MUSS | Anforderungspaket für den Informationsverbund modellieren | Anforderungspaket |
| STM.2.1.1 ISMS-Anforderungen | MUSS | alle Anforderungen der ISMS-Praktiken auf den Verbund modellieren | Anforderungspaket |
| STM.2.1.2 Erfassung relevanter Assets | MUSS | alle relevanten Assets der betrachteten Geschäftsprozesse festlegen | Anforderungspaket |
| STM.2.1.3 Mapping der Assets auf Zielobjektkategorien | MUSS | jedem Asset eine oder mehrere Zielobjektkategorien zuweisen | Anforderungspaket |
| STM.2.1.4 Modellierung der Anforderungen mit Zielobjektkategorie | MUSS | kategoriezugehörige Anforderungen auf die Assets modellieren | Anforderungspaket |
| STM.2.1.4.1 Vererbung von Zielobjektkategorien | MUSS | übergeordnete Kategorien der Zielobjekthierarchie mit zuweisen | Anforderungspaket |
| STM.2.1.4.2 Konsolidierung und Redundanzprüfung | MUSS | Konsolidierung und Redundanzprüfung des Pakets ausführen | Anforderungspaket |
| STM.2.1.5 Anforderungen ohne Zielobjektkategorie | MUSS | kategorielose Anforderungen modellieren | Anforderungspaket |
| STM.2.1.6 Aufgrund anforderungsloser Assets | MUSS | zusätzliche Anforderungen für Assets ohne passende GS++-Anforderungen zuweisen | Anforderungspaket |
| STM.2.1.7 Aufgrund externer Verpflichtungen | MUSS | zusätzliche Anforderungen aus dem Compliance-Umfeld zuweisen | Anforderungspaket |

Die Controls bilden eine Fließstrecke, und sie funktioniert nur in dieser Reihenfolge: Die ISMS-Anforderungen der fünf Praktiken werden ohne Selektion einmalig als „verbundweite Anforderungen" modelliert (STM.2.1.1). Die Assets des priorisierten Geschäftsprozesses werden erfasst, mit ID, Beschreibung, Prozesszuordnung und Asset-Owner (STM.2.1.2). Jedes Asset erhält funktionsorientiert seine Zielobjektkategorien; entscheidend ist laut Guidance, wie das Asset im Geschäftsprozess wirkt, nicht nur seine technischen Merkmale (STM.2.1.3). Dann werden die kategoriegebundenen Anforderungen auf die Assets modelliert (STM.2.1.4), die Vererbung ergänzt alle Elternknoten bis zur Wurzel der Zielobjekthierarchie (STM.2.1.4.1), und die Konsolidierung wirft Dubletten hinaus, damit das Paket „schlank und umsetzbar" bleibt (STM.2.1.4.2). Drei Ergänzungsschritte schließen ab: die Relevanzentscheidung für jede kategorielose Anforderung, mit dokumentierter Begründung für jede Streichung und Zuweisung der verbleibenden an die betroffenen Geschäftsprozesse und ihre Prozess-Owner (STM.2.1.5); eigene Anforderungen für Assets, die der Katalog noch nicht abdeckt (STM.2.1.6); und die Integration der Compliance-Verpflichtungen aus GC.3 (STM.2.1.7). Der erste dieser Schritte wiegt schwerer, als er klingt: Die kategorielosen Anforderungen sind ganz überwiegend die Prozess-Anforderungen der Kernel-Praktiken (Kapitel 3.5), der Verbund modelliert an dieser Stelle also faktisch seine Prozesse mit.

> **Abweichung zu 200-2:** Die Modellierung nach Bausteinen entfällt. 200-2 ordnet Bausteine des Kompendiums den Zielobjekten zu und erzeugt daraus den Prüfplan; Grundschutz++ modelliert einzelne Anforderungen über Zielobjektkategorien mit deterministischer Vererbung auf Assets. Zugleich ersetzt das iterative Vorgehen (wichtigster Geschäftsprozess zuerst, weitere Prozesse in Folgezyklen) den Anspruch der 200-2-Standard-Absicherung, den gesamten Informationsverbund in einem Zug zu modellieren. Wer migriert, übersetzt also nicht Baustein für Baustein, sondern baut die Modellierung neu auf.

> **Katalogfund:** Das Statement von STM.2.1.4.1 ist grammatisch verunglückt: „Strukturmodellierung MUSS die in der Hierarchie übergeordneten Zielobjektkategorien ebenfalls dem jeweiligen Asset die in der Zielobjekthierarchie übergeordnet sind zuweisen." Der Relativsatz ist doppelt gesetzt. Die Guidance macht die Intention eindeutig (alle Elternknoten bis zur Wurzel werden einbezogen); für die Katalogpflege sollte der Satz repariert werden. Ebenfalls auffällig: Die Titel von STM.2.1.6 und STM.2.1.7 („Aufgrund anforderungsloser Assets", „Aufgrund externer Verpflichtungen") sind Satzfragmente, offenbar als Fortsetzung eines gedachten Obertitels „Zusätzliche Anforderungen …" formuliert.

Bemerkenswert ist ein Nebensatz der Guidance zu STM.2.1.6: Selbst erstellte Anforderungen werden „als fester Bestandteil in das Anforderungspaket integriert und dem BSI zugestellt". Der Katalog etabliert damit beiläufig einen Rückkanal von den Institutionen in die Stand-der-Technik-Bibliothek. Ob diese Zustellung verpflichtend gemeint ist, lässt sich aus einer Guidance nicht ableiten; als Community-Mechanismus ist sie bemerkenswert genug, um sie in Abschnitt 5.7 als offene Frage zu führen.

**Umsetzungshinweise.** Automatisieren Sie, was der Katalog zum Automatisieren gebaut hat. Zielobjekthierarchie, Vererbung und Konsolidierung sind deterministisch definiert, die Guidance zu STM.2.1.4.1 empfiehlt die maschinelle Verarbeitung ausdrücklich; ein Skript über den maschinenlesbaren Katalog erledigt in Minuten, was in Tabellenkalkulation Wochen kostet und fehleranfällig bleibt. Die eigentliche Denkarbeit steckt in zwei Stellen: im Asset-Schnitt (zu grob, und die Anforderungen passen nicht; zu fein, und das Paket explodiert) und in den Relevanzentscheidungen nach STM.2.1.5, deren Begründungen die Guidance ausdrücklich für Audit und Zertifizierung verlangt. Streichen Sie großzügig, aber begründen Sie jede Streichung so, dass sie ein Dritter in zwei Jahren noch nachvollziehen kann. Und prüfen Sie vor jeder Eigenkonstruktion nach STM.2.1.6 die SdT-Bibliothek; die Guidance empfiehlt es zu Recht, denn fremdgepflegte Anforderungen altern besser als selbstgeschriebene.

**Audit-Perspektive.** Das Anforderungspaket übernimmt funktional die Rolle der Modellierung (Referenzdokument A.3) und ist damit Kerngegenstand der Dokumentenprüfung. Übertragen aus der Prüfsystematik ergeben sich als Schwerpunkte: die Vollständigkeit der verbundweiten ISMS-Anforderungen (STM.2.1.1 verlangt „ohne weitere Selektion"), die Nachvollziehbarkeit des Asset-Mappings, die korrekte Vererbung und vor allem die Streichungen nach STM.2.1.5, denn dort steht die Nachvollziehbarkeit wörtlich als Zweck im Katalog. Eine gestrichene Anforderung ohne Begründung ist die am leichtesten zu findende Abweichung dieser Praktik.

**Typische Fehler.** Das Paket wird einmal erzeugt und nie fortgeschrieben, während der Katalog-Build sich weiterentwickelt. Das Asset-Inventar wird aus der CMDB kopiert, inklusive tausender Einträge ohne Prozessbezug, und das Anforderungspaket wächst ins Unbearbeitbare. Die Zielobjektkategorien werden nach Gerätetyp statt nach Funktion im Geschäftsprozess vergeben. Streichungen erfolgen per Filter statt per Einzelentscheidung, und im Audit fehlt jede Begründung.

## 5.3 STM.3 Sicherheitsniveau: die eine SOLLTE-Anforderung

**Anforderungsbezug.**

| Control | Verbindlichkeit | Kern | Dokument |
|---|---|---|---|
| STM.3.1 Überprüfung des gesetzten Sicherheitsniveaus | SOLLTE | initiale Einstufung der Sicherheitsniveaus im Anforderungspaket bei Kontextabweichungen überprüfen | keines zugeordnet |

Jede Katalog-Anforderung trägt ein Sicherheitsniveau (`sec_level`: „normal-SdT" oder „erhöht"). STM.3.1 verlangt, diese initiale Einstufung zu überprüfen, wenn der Kontext der Institution abweicht; die Guidance nennt als Hauptfall Geschäftsprozesse oder Informationen mit hohem Schutzbedarf und erlaubt die Anpassung auch für einzelne Assets. Mit `effort_level` 2 ist das eine der wenigen Anforderungen der Praktik, die der Katalog als echten Zusatzaufwand einstuft.

**Umsetzungshinweise.** Praktisch ist das die Stellschraube, mit der die zweistufige Schutzbedarfslogik aus GC.7 auf das Anforderungspaket wirkt: Hoher Schutzbedarf ist der Anlass, für die betroffenen Assets die „erhöht"-Anforderungen des Kernels in das Paket zu heben. Dokumentieren Sie jede Niveauänderung mit Anlass und Umfang, denn eine Herabstufung (von „erhöht" auf „normal-SdT") löst nach STM.4.1 eine Risikobetrachtung aus. Wer das Niveau nie überprüft, hat bei hohem Schutzbedarf ein Paket, das systematisch zu schwach ist.

**Audit-Perspektive.** Als SOLLTE-Anforderung gilt das übliche Muster: Der Auditor erwartet entweder die dokumentierte Überprüfung oder eine nachvollziehbare Begründung, warum sie unterblieb. Bei Verbünden mit Hoch-Prozessen aus GC.7.2 wird er die Verbindung ziehen: Wer hohen Schutzbedarf feststellt, aber das Sicherheitsniveau im Paket nie angefasst hat, muss erklären können, warum das Paket trotzdem angemessen ist.

**Typische Fehler.** Die Überprüfung findet nicht statt, weil niemand wusste, dass es sie gibt; die Anforderung ist die unauffälligste der Praktik. Oder das Niveau wird pauschal für den ganzen Verbund hochgesetzt, statt gezielt für die Assets der Hoch-Prozesse, und der Umsetzungsaufwand verdoppelt sich ohne Not.

## 5.4 STM.4 Risiko: die definierten Aussprungpunkte

**Anforderungsbezug.**

| Control | Verbindlichkeit | Kern | Dokument |
|---|---|---|---|
| STM.4.1 Durchführung der Risikobetrachtung | MUSS | Risikobetrachtung bei durch die Methodik festgelegter Notwendigkeit ausführen | keines zugeordnet |

Die Guidance zählt die Szenarien auf, in denen die Methodik in eine separate Risikobetrachtung springt: Geschäftsprozesse oder Assets mit hohem Schutzbedarf, Herabstufung des Sicherheitsniveaus von „erhöht" auf „normal-SdT", Nicht-Umsetzung von Anforderungen sowie die Ergänzung des Anforderungspakets bei Assets ohne passende Katalog-Anforderungen.

> **Katalogfund:** Im Statement von STM.4.1 steht „festgeleger" statt „festgelegter". Für die Katalogpflege vermerkt; ebenso das Steuerzeichen in der Guidance zu STM.3.1 („Anforderungsanalyse´wird") und deren Formulierung „initiale Einstellung", wo „initiale Einstufung" gemeint sein dürfte.

**Umsetzungshinweise.** STM.4.1 definiert das Wann, GC.12.1 das Wie: Ausgeführt wird nach der dort verankerten einheitlichen Methodik, und für Hoch-Prozesse überschneidet sich der Auslöser bewusst mit GC.7.2. Bauen Sie die vier Auslöser als Prüfliste in Ihre Modellierungs- und Umsetzungsprozesse ein, dann entsteht die Risikobetrachtung dort, wo sie hingehört, statt als jährliche Sammelveranstaltung. Besonders der dritte Auslöser wird gern übersehen: Jede bewusst nicht umgesetzte Anforderung (UMS.5, VRB-Kontext) ist ein Kandidat für den Aussprung.

**Audit-Perspektive.** Prüfbar ist die Lückenlosigkeit: Der Auditor kann die Auslöserliste gegen den Bestand halten, also Hoch-Prozesse aus der Schutzbedarfsfeststellung, Herabstufungen aus STM.3.1 und Ausnahmen aus UMS.5.2, und für jeden Treffer die zugehörige Risikobetrachtung verlangen. Fehlt sie, ist das wesentliche Ziel der Anforderung verfehlt, mit entsprechendem Gewicht der Feststellung.

**Typische Fehler.** Risikobetrachtungen existieren nur für die Hoch-Prozesse, während Herabstufungen und Ausnahmen nie einen Aussprung ausgelöst haben. Oder die Betrachtungen folgen je nach Bearbeiter unterschiedlichen Methoden, womit der Fehler von GC.12.1 hier sichtbar wird.

## 5.5 STM.5 Parametrisierung: Platzhalter werden Werte

**Anforderungsbezug.**

| Control | Verbindlichkeit | Kern | Dokument |
|---|---|---|---|
| STM.5.1 Setzen von Parametern | MUSS | bei Anforderungen mit Parametern konkrete Werte zuweisen | keines zugeordnet |

Die Guidance beschreibt die beiden Haupttypen: Zuständigkeits-Parameter (jede technische und organisatorische Praktik enthält im Abschnitt „Grundlagen" eine Anforderung zur Zuweisung der führenden Zuständigkeit) und zeitliche Parameter, mit denen etwa „regelmäßig" zu täglich, wöchentlich oder monatlich konkretisiert wird. Belegung per Auswahlfeld oder Freitext.

**Umsetzungshinweise.** Führen Sie ein zentrales Parameterregister statt verstreuter Einzelentscheidungen: Parameter-ID, gewählter Wert, Begründung, Datum. Die Methodik selbst enthält nur wenige Parameter (in GC etwa `{{einem anerkannten Standard}}`, `{{einer unabhängigen Person}}`, in UMS `{{regelmäßig}}`), der Kernel dagegen viele; das Register wird also mit dem Anforderungspaket wachsen. Ein Sonderfall ist der Standard-Parameter aus GC.1.1: Im Anwenderkatalog kommt er bereits mit „BSI Grundschutz++" belegt an, weil das zugrunde liegende Profil ihn setzt (Kapitel 3.8); hier ist der Wert zu prüfen und ins Register zu übernehmen statt neu zu entscheiden. Setzen Sie Zuständigkeits-Parameter konsistent mit der Sicherheitsorganisation aus GC.9, sonst benennt das Paket Rollen, die es im Organigramm nicht gibt. Und behandeln Sie Parameterwerte als gelenkte Inhalte: Wer „regelmäßig" auf „monatlich" setzt, hat damit ein Prüfkriterium für PERF und den Auditor erzeugt.

**Audit-Perspektive.** Parameter sind ein Geschenk an die Prüfbarkeit: Jeder gesetzte Wert ist ein konkretes, vereinbartes Soll. Der Auditor kann unparametrisierte Anforderungen im Paket suchen (dann ist STM.5.1 nicht erfüllt) und gesetzte Werte gegen die gelebte Praxis halten. Ein auf „wöchentlich" gesetzter Überprüfungsparameter mit monatlicher Realität ist eine sauber belegbare Abweichung.

**Typische Fehler.** Parameter bleiben auf dem Katalog-Default oder leer, und niemand merkt es, weil das Paket nie vollständig durchgesehen wurde. Werte werden ambitioniert gesetzt („täglich"), um im Audit gut auszusehen, und reißen dann jede Woche. Zuständigkeits-Parameter zeigen auf Personen statt Rollen und veralten mit dem ersten Personalwechsel.

## 5.6 Dokumenten-Output der Praktik

| Dokument | Gefordert durch |
|---|---|
| Informationsverbund | STM.1.1, STM.1.2 |
| Anforderungspaket | STM.2.1, STM.2.1.1, STM.2.1.2, STM.2.1.3, STM.2.1.4, STM.2.1.4.1, STM.2.1.4.2, STM.2.1.5, STM.2.1.6, STM.2.1.7 |

Drei Controls fordern kein Dokument (STM.3.1, STM.4.1, STM.5.1). Für die Praxis empfiehlt sich trotzdem ein Ablageort: Niveauentscheidungen und Parameterwerte gehören versioniert ins oder ans Anforderungspaket, die Risikobetrachtungen folgen dem Dokument, das GC.7.2 ohnehin fordert (Risikobetrachtung); alles unter der Lenkung von GC.11.1.

## 5.7 Offene Fragen und Katalogfunde

1. **Zielobjekthierarchie als Prüfvoraussetzung.** Vererbung (STM.2.1.4.1) und Mapping (STM.2.1.3) setzen eine fest definierte, maschinenlesbare Zielobjekthierarchie voraus. Sie liegt nicht in den Projektquellen; für Kapitel 3 (OSCAL-Lesart) sollte sie aus dem Repository beschafft werden, sonst bleibt der zentrale Mechanismus der Praktik unbelegt.
2. **Zustellung eigener Anforderungen an das BSI.** Die Guidance zu STM.2.1.6 formuliert die Zustellung selbst erstellter Anforderungen an das BSI als Faktum. Normative Verbindlichkeit, Verfahren und Adresse sind offen; als Community-Rückkanal wäre der Mechanismus ein eigenes Handbuchthema.
3. **Defektes Statement STM.2.1.4.1** (doppelter Relativsatz) sowie Titelfragmente STM.2.1.6/STM.2.1.7 („Aufgrund …"); Details in Abschnitt 5.2.
4. **Tippfehler:** „festgeleger" in STM.4.1; Steuerzeichen und „initiale Einstellung" in der Guidance zu STM.3.1.
5. **Verhältnis STM.4.1 zu GC.7.2.** Beide fordern Risikobetrachtungen für hohen Schutzbedarf, GC.7.2 aus Governance-Sicht, STM.4.1 als Aussprung der Modellierung. Das Handbuch liest sie als dieselbe Betrachtung in zwei Zuständigkeiten; eine normative Klärung, ob zwei getrennte Nachweise erwartet werden, steht aus.
6. **Prozess-Modellierung nur implizit.** STM.2.1.5 weist die kategorielosen Anforderungen allein über die Guidance den Geschäftsprozessen und Prozess-Ownern zu; eine ausdrückliche Anforderung, Prozesse als Modellierungsobjekte zu führen, fehlt ebenso wie eine Prozess-Kategorie im Namespace (Anhang D, D29).

---

*Ende Kapitel 5 (v0.1). Review-Anmerkungen bitte gegen die Control-IDs.*
