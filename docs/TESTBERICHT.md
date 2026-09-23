# Prüfbericht 0.3.0 — 23.09.2026

## Ergebnis

**145 Python-Tests, TypeScript-Kompilierung und 23 Browser-/API-Integrationschecks bestanden.** Neun Layoutkombinationen zeigen jeweils alle 20 Module (paper/blue/dark × 1440/768/390 px). Keine JavaScript-Exception oder Transport-Exception im abschließend vollständig durchlaufenen Browserablauf.

Die Suite enthält die bisherigen Backend-/Baukastentests, für die sechs neuen Modultypen erweiterte Parametrisierungen sowie 36 neue v0.3-Prüffälle. Geänderte Erwartungen: 20 statt 14 Module, acht statt drei Vorlagen, Schema 3 statt 2. Nicht zugeordnete Werbeplätze müssen öffentlich verschwinden und privat erklärbar bleiben.

## Python-Abdeckung

Bestehende Authentifizierung, Setup, Rollen, CSRF/Origin, Revisionen, Entwurf/Freigabe, Medien, Anfragen, Vorlagen, Restore und Sicherheitsheader. Neu geprüft: Artikelablauf einschließlich Moderation, Anzeigedaten, Such-/Kategoriearchive, RSS, kompakte Listenprojektionen und Pagination, Werbezeiten inklusive Grenzen, zentrale Kampagnenupdates, unzulässige URLs, zweistufige Anzeigenfreigabe, Datenschutzsignale, ausgeschaltete Messung, erforderliche Zustimmung, Adminausschluss, Deduplication, Rollen der Analyse, Löschung, RAM-Verfall und -Obergrenzen, Ereignisbegrenzung, Bereinigung alter Tageswerte, Migration von Schema 2, öffentliche Attribution, Anzeigen-Gesamtsummen über die Top-20-Liste hinaus und eine einzelne H1 auf Artikeln mit Bento-Modul.

## Browserprüfung: Methode und Grenzen

Chromium mit Playwright, tatsächlichem App-HTML, CSS, erzeugtem JavaScript und FastAPI-TestClient. Weil direkte Host-Navigation mit `ERR_BLOCKED_BY_ADMINISTRATOR` blockiert ist, wird HTML über `set_content` geladen. Ein ausschließlich im Testtransport angewandter Adapter ersetzt bei den beiden Preview-Skripten das `postMessage`-Ziel durch `*`, damit der opaque `about:blank`-Ursprung funktioniert. Source-/Origin-Prüfungen bleiben im Code erhalten; im Liefercode werden Nachrichten weiterhin an die exakte Origin gesendet.

**Das ist kein Test gegen einen bereitgestellten Server und kein vollständiger SameSite-/CSP-/HTTPS-Browsernachweis.** Insbesondere native dokumentübergreifende View Transitions konnten in dieser Umgebung nicht auf echten Navigationen geprüft werden. HTTP-Sicherheitsregeln sind separat über API-Tests geprüft. Windows-Doppelklick, Safari, Firefox, reale Mobilgeräte, langdauernder Betrieb und ein unabhängiges Security-Audit sind nicht abgedeckt.

## Die 23 Browserprüfungen

1. Startseite: sieben Kacheln, drei echte Demo-Beiträge, kein Überlauf.
2. Vier Hover-Kontrastwechsel mit perspektivischer Bewegung.
3. Signature-Intro bleibt abspielbar und überspringbar.
4. Themen-Tabs per Maus und Pfeiltaste, ARIA-Zustand aktualisiert.
5. Bildvergleich aktualisiert sichtbare Teilung und zugänglichen Wert.
6. Partnerfläche und fixer Erstellerhinweis sind öffentlich sichtbar.
7. Wiederkehrende Bühne animiert beim erneuten Betreten des Sichtbereichs.
8. Mobile Navigation und reduzierte Bewegung bei 390 px.
9. Journal und modulare Beitragsdetailseite werden gerendert.
10. Echtes Setup, Hilfedialog ohne Eingabeverlust, authentifizierter Admin.
11. Live-Vorschau patcht ungespeicherte Eingaben ohne iframe-Neuladen oder Datenbankrevision.
12. Ausführliche Fragezeichen-Hilfe erhält Eingaben; echte Mobilvorschau.
13. Live-Vorschau pausiert und übernimmt beim Fortsetzen die Änderungen.
14. 20 Module durchsuchen, Themen einfügen, Undo und Redo.
15. Vorschau-Auswahl, Testmodus mit echten Tabs und Animation erneut abspielen.
16. Speichern erzeugt Entwurfsrevision und verändert nicht die öffentliche Startseite.
17. Beitrag über UI anlegen, Mediathek öffnen, sicher als Entwurf speichern.
18. Acht Vorlagen, fünf eindeutige Produktmodule und mobiler Editor ohne Überlauf.
19. Durchsuchbares Handbuch mit ausführlicher Werbeplatz-Hilfe.
20. Analyse zeigt deaktivierten Zustand und echte Nullwerte statt Beispieldaten.
21. 20 Module × drei Farbschemata × drei Bildschirmbreiten ohne horizontalen Seitenüberlauf.
22. Gastbrowser: keine Zählung vor Zustimmung, ein Aufruf und eine Sichtung danach, Widerruf beendet aktive Messung.
23. Keine JavaScript-Exceptions oder Testtransportfehler im gesamten geprüften Ablauf.

## Reproduzierbare Leseprüfung

Zusätzlich 2.000 synthetische veröffentlichte Beiträge in einer isolierten Datenbank. Je Route 30 warme lokale TestClient-Leseaufrufe, ohne Netzwerk/TLS:

| Route | Median | 95. Perzentil | HTML-Größe |
|---|---:|---:|---:|
| `/` | 17.66 ms | 20.87 ms | 20591 Bytes |
| `/news` | 15.71 ms | 18.34 ms | 15974 Bytes |
| `/news/benchmark-100` | 3.63 ms | 4.58 ms | 8449 Bytes |
| `/news?q=Synthetic` | 25.9 ms | 34.94 ms | 15568 Bytes |

Vier parallele Lese-Worker, 40 Journal-Aufrufe, **0 Fehler**; Median 27.31 ms. Das ist ein lokaler Funktions-/Größencheck, **keine** Kapazitätsgarantie, Last-/Dauertest oder Vorhersage für den Nutzer-PC. Gleichzeitige Schreiblast, Internetlatenz, Rendering-Zeit und produktive Logs sind nicht in diesen Zahlen enthalten.

Rohdaten: [Browser](qa-v3/browser-results.json), [Benchmark](benchmark.json). Alle Auslieferungsscreenshots stammen aus dieser Implementierung; Messdiagramme enthalten keine künstlich angelegten Marketing-Zahlen.

## Nachvollziehen

```bash
python -m pip install -r requirements-dev.txt
pytest -q
npm install
npm run typecheck
npm run build
python -m pip install -r requirements-browser.txt
python scripts/browser_v3.py --output docs/qa-v3
python scripts/benchmark.py
```

Chromium zusätzlich installieren oder `CHROMIUM_EXECUTABLE` setzen. Der Browserrunner erzeugt ausschließlich temporäre Testdatenbanken; niemals echte Produktionsdaten daran anschließen.

## Weiterhin offen

Eigene Marke und Rechtstexte, HTTPS-Hosting, E-Mail-Versand, Mehrinstanz-Datenbank/Shared-State, echtes Werbenetzwerk, Checkout oder Buchungssystem. Beiträge haben ein Anzeigedatum, keine zeitgesteuerte Freischaltung. Die aktive Statistik ist eine RAM-Tabzählung, keine Personenzählung. Alte Statistikdaten werden bei fälliger Bereinigung mit einem neuen Ereignis entfernt, nicht durch einen laufenden Scheduler.

Der konkrete Lieferarchiv-Startcheck wird zusätzlich in `LIEFERPRUEFUNG.json` protokolliert. ZIP und Quellcode sind keine Zusicherung völliger Fehlerfreiheit.
