# Architektur 0.3 — ein modularer Monolith

## Grenzen und Verantwortlichkeiten

`app/models.py` enthält validierte Inhaltsverträge. `app/content.py` verwaltet Entwurf, öffentlichen Snapshot, Revisionen und Aktionen atomar. `app/catalog.py` beschreibt Module, Formfelder und Vorlagen. `app/collections.py` liefert öffentliche News-Projektionen, zeitlich gültige Kampagnen und ausschließlich benötigte Medien.

Router trennen Authentifizierung, Redaktion, Baukasten, Medien, Kontakt, öffentliche Seiten und Analyse. HTML entsteht in Jinja-Templates. `frontend/admin` enthält Auth/API, Ansichten, Editor, Baukasten, Bibliothek, Suchauswahl und Hilfesystem. `frontend/motion.ts`, `experience.ts`, `preview-bridge.ts` und `analytics.ts` ergänzen die öffentliche Darstellung.

## Inhaltsfluss

Eingabe → Pydantic-Vertrag → gespeicherter Entwurf → Prüfung → öffentlicher JSON-Snapshot. Öffentliche URLs lesen den Snapshot, nie den aktuellen Entwurf. Optimistische Revisionen verhindern stilles Überschreiben paralleler Änderungen. Wiederherstellen einer Revision erzeugt wiederum einen Entwurf.

Artikel erben textuelle Medienfelder und können zusätzlich Module enthalten. Ein Werbeplatz referenziert eine Kampagnen-ID; in der Öffentlichkeit müssen sowohl Seitenstand als auch Kampagne freigegeben sein. Kampagnenzeitraum gilt pro UTC-Kalendertag. Das Beitragsdatum ist dagegen nur Darstellung/Sortierung, keine geplante Freischaltung.

## Live-Vorschau

Die API rendert validierte ungespeicherte Eingaben ohne neue Datenbankrevision. Beim ersten Aufruf wird ein same-origin `srcdoc`-iframe befüllt. Spätere Updates senden ausschließlich servergerendertes HTML an diesen Frame. Der Frame akzeptiert nur Nachrichten vom exakten Parent und derselben Origin, der Editor nur vom exakten Frame.

Direkte Seitenmodule werden anhand ihrer IDs und HTML-Fingerprints aktualisiert. Unveränderte Module bleiben nach dem ersten Patch erhalten; Artikelrahmen werden bei Änderungen als Einheit ersetzt. Scrollposition wird soweit möglich wiederhergestellt, bei verkürzten Dokumenten vom Browser begrenzt. Interaktive Module werden idempotent initialisiert. Hilfe-Overlays ersetzen den Editor nicht.

Kein Preview-POST erzeugt Revisionen. Die Vorschau darf keine Kontaktformulare senden oder zu anderen Seiten navigieren. Das ist kein Sandbox-Modus für beliebigen Fremdcode; beliebiger HTML-/JavaScript-Inhalt ist im Datenvertrag absichtlich ausgeschlossen.

## Gebundene Lesewege

Einzelinhalte werden per Typ/Live-Slug und Index gelesen. Admin-Listen enthalten kompakte Projektionen statt vollständiger Texte und Blöcke; der Editor lädt den vollen Datensatz erst beim Öffnen. Medienzugriff per referenzierten IDs, keine vollständige Medienbibliothek pro Seitenaufruf. Inhaltslisten, Archive, Mediensuche, Moderation und Postfach sind begrenzt/paginiert. Zusätzliche Ausdrucksindizes unterstützen öffentliche Reihenfolge, Artikeldatum, Navigation und aktuelle Einträge.

Die Suchfunktion arbeitet weiterhin mit SQLite-Substring-Suche, nicht mit einem dedizierten Volltextserver. Die Gesamtzahl zu zählen und komplexe Suchen bleiben datenabhängig. Offset-Pagination ist für überschaubare bis mittlere Bestände gedacht; bei sehr tiefen Seiten und großen Datenbeständen Cursor-Pagination/FTS gezielt nach Messungen ergänzen.

## Bewegung mit Grenzen

Ein IntersectionObserver steuert Eintritte. Auto wiederholt Signature-Raster und Kontakt; „repeat“ wiederholt andere Abschnitte. Layout-/SVG-Animationen laufen nicht dauerhaft für beliebig viele unsichtbare Elemente. Die dekorative Spotlight-Bewegung läuft nur im Sichtbereich. Pointerbewegung nutzt höchstens einen angeforderten Animationsframe statt einer permanenten Schleife. Reduzierte Bewegung und die globale Abschaltung haben Vorrang.

Native View Transitions sind progressive Erweiterung auf derselben Origin. Nicht unterstützte Browser navigieren normal. Der Host-übergreifende bzw. echte Seitenwechsel war in der Testumgebung nicht ausführbar; keine browserübergreifende Garantie dafür.

## Skalierung und Erweiterung

Aktuell SQLite/WAL, eine Anwendung, ein Serverprozess. WAL erlaubt parallel laufende Leser, aber weiterhin nur einen Schreiber gleichzeitig [3]. Keine Behauptung unbegrenzter Lastfestigkeit. Der beigefügte synthetische Benchmark prüft begrenzte Lesewege, nicht produktive Spitzenlast oder gleichzeitige Schreiblast.

Für einen neuen Modultyp: Literal/Vertrag → Katalogbeschreibung mit Hilfen → Template → optional gekapselte CSS/TS-Interaktion → Vorschau-/Public-/Rechte-/Layouttests. Für neue Geschäftsfunktionen zusätzliche Dienste/Router, ohne unvertrauenswürdigen Code aus CMS-Feldern auszuführen.

Mehrere Serverinstanzen brauchen PostgreSQL oder eine andere zentral geeignete Datenbank, gemeinsamen Medienspeicher und gemeinsamen Zustand für Rate-Limits/aktive Tabs. Diese Migration ist nicht implementiert. Analytics-RAM hält höchstens 5.000 aktive Tabs, 10.000 kurzlebige Ratenzähler und 100 Ereignisidentitäten je Tab. Die Tagesaggregate sind nach Zeit und Ressource gruppiert.

## Quellen

Siehe [QUELLEN.md](QUELLEN.md), insbesondere MDN zu View Transitions [1], OWASP zu Ausgabe-Encoding [2] und SQLite/WAL [3].
