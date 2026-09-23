# FORM / STUDIO 0.3 — Experience & Editorial

Modulare Website plus Admin-Studio. FastAPI/Python, TypeScript und SQLite, ohne externe Laufzeitdienste. Entwickelt für eine einzelne Serverinstanz. **FORM / STUDIO, Projekte und Beiträge sind gekennzeichnete Demo-Inhalte.**

Die Website bleibt serverseitig lesbar. JavaScript ergänzt Animationen, interaktive Module, Editor und optionale Statistik. Kein React-/Node-Server und kein separater Datenbankdienst zum lokalen Start nötig.

## Start

1. ZIP vollständig entpacken. Python 3.11 oder neuer installieren, falls noch nicht vorhanden.
2. `START-WINDOWS.cmd` öffnen oder `python start.py` im Projektordner ausführen.
3. Den einmaligen Einrichtungscode aus dem Terminal im Admin-Setup eingeben. Eigenes Passwort mit mindestens zwölf Zeichen setzen.

Beim ersten Start werden die festgelegten Python-Abhängigkeiten in `.venv` installiert; dafür wird Internet benötigt. Anschließend öffnen sich Website/Setup lokal. Das Terminal bleibt während des Betriebs offen. Beenden: Strg+C. Node.js wird nur für TypeScript-Änderungen gebraucht, nicht zum normalen Start.

**Vorhandene v0.1/v0.2-Daten? Zuerst [UPDATE.md](docs/UPDATE.md) lesen.** Nicht den bisherigen Ordner überschreiben.

## Was neu ist

- Wiederkehrende Abschnitts-Choreografien, Hover-Kontrastwechsel mit perspektivischem Versatz, Spotlight-Bühnen und ein Lesefortschritt. Native Seitenwechsel-Animationen sind als progressive Erweiterung eingebaut; Browserunterstützung und tatsächlicher Host entscheiden darüber. Normale Navigation bleibt erhalten.
- **Journal & News** mit Sucharchiv, Kategorien, Autor, Anzeigedatum, RSS und modularen Beitragsdetailseiten. Redaktions- und Freigabeschritte gelten auch für Beiträge.
- **Werbung & Partner**: Kampagnen zentral anlegen, veröffentlichen, zeitlich eingrenzen und über Werbeplätze auf Seiten oder Beiträgen verbinden. Die öffentliche Kennzeichnung ANZEIGE ist nicht wegkonfigurierbar. Keine Werbenetzwerk-Skripte oder beliebigen HTML-Embeds.
- **Lokale Analyse** mit Tagesdiagramm, Tabellen, Seitenaufrufen, aktiven Seitenfenstern und Werbeinteraktionen. Standardmäßig aus, dann zusätzlich zustimmungsbasiert. Keine erfundenen Besucherzahlen, keine eindeutigen Personen oder Umsatzmessung.
- **20 Modultypen**, acht Seitenvorlagen, zwölf lokale geometrische Standardgrafiken. Eigene Bausteine werden als unabhängige Kopien gespeichert.
- Live-Vorschau mit aktualisiertem Seiteninhalt ohne komplettes iframe-Neuladen, Auswahl- und Testmodus, Animationswiederholung, Pause und Großansicht.
- Sichtbare blaue **?**-Hilfen: Kurzinfo bei Hover/Fokus, ausführliche Erklärung per Klick/Tap. Zusätzlich durchsuchbares Handbuch.
- Dezenter öffentlicher **NorphyOG**-Erstellerhinweis außerhalb der CMS-Inhalte.

## Im Admin schnell zum Ziel

| Aufgabe | Weg |
|---|---|
| Beitrag schreiben | Journal & News → Neu → Titel, URL, Text und Autor → optionale Module → Entwurf speichern → Veröffentlichen oder Zur Prüfung |
| News auf Startseite | Seiten → Startseite → Modul/Vorlage → Journal/News → Anzahl/Kategorie → speichern und freigeben |
| Anzeige einbauen | Werbung & Partner → Kampagne erstellen → veröffentlichen → Seite/Beitrag → Werbeplatz → Kampagne auswählen → Seite freigeben |
| Statistik einschalten | Einstellungen → Optionale lokale Statistik anbieten → veröffentlichen. Gäste entscheiden anschließend selbst über Zustimmung. |
| Modul ausprobieren | Vorschau auf Testmodus schalten. Tabs/Regler benutzen; Animation testen. Vorschau-Links und Formulare verlassen die Vorschau nicht. |
| Eigene Vorlage | Modul im Editor öffnen → Als Baustein speichern. Anschließend im Katalog unter Eigene Bausteine einfügen. |
| Hilfe | ? direkt am Feld oder Workspace → Handbuch |
| Branding | Einstellungen → Markenname, Unterzeile, Akzent, Standort und Bewegungsstil. Der Erstellerhinweis bleibt davon getrennt. |

## Modulkatalog

Signature-Raster, Projektgalerie, Feature-Karten, Bild + Text, freie Galerie, Prozess, Kennzahlen, Zitat, Namen/Partner, Angebotspakete, FAQ, Kontakt-Bühne, Text und Trenner. Neu: Journal/News, Werbeplatz, Spotlight, Themen/Tabs, Zeitstrahl, Vorher/Nachher.

Acht Startvorlagen: Studio/Portfolio, Angebot/Landingpage, Über uns/Geschichte, Journal/Magazin, Produkt/Launch, Unternehmen/Lokal, Veranstaltung/Programm und Kampagne/Partner. Eine Produktvorlage ist **kein Shop**, eine Veranstaltungsvorlage **kein Ticket-/Buchungssystem**.

### Bewusste Grenzen

30 Module pro Seite oder Beitrag, üblicherweise 20 Einträge pro Modul. Kontakt und Vergleich höchstens zwei Einträge. 100 eigene Bausteine; 50 lokale Undo-Zustände für Moduländerungen, nicht die gesamte Anwendung. Keine beliebig verschachtelten Freiform-Layouts oder frei ausführbaren Skripte. Neue Modultypen und Geschäftslogik erfordern Entwicklung.

News-Module laden höchstens zwölf Beiträge; das Journal zeigt zwölf pro Seite. Admin-Inhaltslisten, Medienansicht, Postfach und Moderation werden seitenweise angezeigt. Das Signature-Raster zeigt die ersten sieben Leistungen, Projektmodule maximal 24 Arbeiten; vollständige Archive unter `/leistungen` und `/arbeiten` halten weitere Einträge erreichbar. Die Hauptnavigation zeigt maximal 24 zusätzliche veröffentlichte Seiten; weitere Seiten verlinken oder über Einstiegsseiten ordnen.

## Daten, Medien und Backups

Inhalte, Revisionen, Benutzer, Anfragen, Bausteine und Statistik liegen in `data/studio.sqlite3`. Bilder unter `data/media`. `.setup-key` und diese Verzeichnisse sind keine öffentlichen Dateien. Medien selbst sind nach Upload über ihre URL öffentlich: keine vertraulichen Dateien hochladen.

```powershell
python scripts/backup.py
python scripts/restore_backup.py "C:\Pfad\studio-backup-DATUM.zip"
```

Wiederherstellung nur in einen leeren Datenordner. Eigene `DATA_DIR`-Pfade explizit mit `--data-dir` an beide Backup-Werkzeuge übergeben; sie lesen nicht automatisch `.env`.

Anfragen werden gespeichert, aber noch **nicht per E-Mail verschickt**. Keine automatische Abrechnung, kein Checkout, kein Newsletter-Dienst und kein Hosting enthalten.

## Entwicklung

```bash
python -m pip install -r requirements-dev.txt
pytest -q
npm install
npm run typecheck
npm run build
python start.py --no-bootstrap --no-browser
```

`tsc` erzeugt die mitgelieferten Browsermodule unter `app/static/js`. Frontend-Abhängigkeiten sind auf TypeScript begrenzt. Kein CDN, keine Schriftdateien, kein externes Assetkonto erforderlich.

Browserintegration benötigt `requirements-browser.txt` und Chromium. `scripts/browser_v3.py` beschreibt die Testtransport-Grenzen ausdrücklich; es ist kein Deployment-E2E. `scripts/benchmark.py` erzeugt eine isolierte synthetische Datenbank, keine Änderungen an echten Projektdaten.

[Architektur](docs/ARCHITEKTUR.md) · [Sicherheit & Statistik](docs/SICHERHEIT-STATISTIK.md) · [Testbericht](docs/TESTBERICHT.md) · [Erstellerhinweis](docs/ERSTELLERHINWEIS.md) · [Asset-Herkunft](docs/ASSETS.md)

## Vor dem Livegang

Eigene Marke, Bilder, belegbare Referenzen, Betreiberangaben und passende Datenschutzhinweise eintragen. Demo-Beiträge, Spielraum-Seite und Demo-Kampagne ersetzen oder offline nehmen. Kein Rechtstext ist fertig mitgeliefert.

Für einen echten Betrieb: HTTPS-Reverse-Proxy, exakte `SITE_ORIGIN`, `SECURE_COOKIES=1`, geschützte Datenrechte, getestete Backups, Updates und Monitoring. Den lokalen Starter nicht einfach ins Internet freigeben. Die aktive Statistik ist pro Prozess; mehrere Worker sind dafür nicht vorgesehen. PostgreSQL-/Shared-State-Migration ist bei echter Mehrinstanzlast ein eigener Entwicklungsschritt.

Keine Zusicherung völliger Fehlerfreiheit oder eines unabhängigen Sicherheits-Audits. Prüfumfang und bekannte Grenzen stehen im Testbericht.
