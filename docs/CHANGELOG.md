# 0.4.0 — Open Source & Design Packages

- Zehn globale Designpakete mit Auswahl und Musterkarten im Admin. Die Freigabe der Website-Einstellungen bestimmt den öffentlichen Look; Inhalte und Module bleiben erhalten.
- AGPL-3.0-only-Lizenz, GitHub-Dokumentation, Handbuch, Beitragsregeln, Sicherheitskontakt und CI.
- Echte Screenshots aus allen zehn CSS-Designs, Vergleichsgalerie, Design-GIF und Screenshot der Admin-Auswahl.
- Windows-Backup und Restore schließen SQLite-Verbindungen explizit, damit temporäre Datenbankdateien wieder freigegeben werden.
- 156 lokale Python-Tests bestanden; TypeScript-Typprüfung und Build bestanden. Visuelle Checks: zehn Designs bei Desktop- und Mobilbreite ohne Überlauf oder Browserfehler; Admin-Auswahl geprüft. Grenzen: [RELEASE-CHECK.md](RELEASE-CHECK.md).

---

# 0.3.0 — Experience & Editorial

Wiederkehrende Animationen, perspektivische Hoverbewegung, native progressive Seitenübergänge, sechs neue Module (20 insgesamt), fünf neue Vorlagen (acht insgesamt), News/Artikel samt Suche/RSS, Kampagnen und Werbeplätze, Opt-in-Analyse, festes NorphyOG-Credit, klare Fragezeichen und Handbuch, inkrementelle interaktive Vorschau, paginierte Inhalts-/Medien-/Moderations-/Postfachansichten, vollständige Service-/Projektarchive, gezielte Medienauflösung, Datenbankschema 3 und kompatibler Restore.

Keine Demodatensätze beim Update eines bestehenden Projekts. Analytics aus, bis explizit aktiviert und vom jeweiligen Gast akzeptiert. Bekannte Betriebs-/Testgrenzen im aktuellen Testbericht.

---

## Bisherige Versionen (historisch)

# v0.2.0 — Motion & Builder

23.09.2026. Aufbauend auf dem tatsächlich gelieferten Projekt v0.1.0.

## Website

- Flächiger blauer Einstieg zieht sich zur mittleren Kachel zusammen; zeitversetzter Aufbau der Umgebung.
- Unterschiedliche SVG-Reaktionen, Scroll-Einblendungen, animierte Projektfilter und Kontakt-Choreografie.
- Ausgeschaltete/reduzierte Bewegung, Abbruch, Wiederholung und mobile Bedienung.
- 14 validierte Modultypen mit endlicher Auswahl für Farbe, Breite, Abstand, Ausrichtung und Einblendung.
- Zwölf lokale geometrische Standardgrafiken ohne externe Bild-/Fontdienste.
- Korrekte Links zum tatsächlich vorhandenen Projektmodul; nur ein Haupttitel bei mehreren Hero-Modulen.
- Korrigierte Text-/Hoverkontraste farbiger Module und sichtbare Kontaktkarten auch auf Tablet-Breite.

## Admin

- Durchsuchbarer Modulkatalog und drei neue Seitenvorlagen.
- Modulgliederung, Umordnen, Duplizieren, Ein-/Ausblenden und lokale Undo-/Redo-Historie.
- Eigene gespeicherte Bausteine als unabhängige Kopien, mit serverseitigen Berechtigungen.
- Echte Vorschau ungespeicherter Formulardaten im Seitenrenderer, inklusive Gerätebreiten und Modulauswahl per Klick.
- Kontextuelle Infozeichen: Kurzinfo bei Fokus/Hover, ausführliche Hilfe per Klick, ohne Verlust des Entwurfs.
- Warndialog bei ungespeicherten Änderungen, Strg/Cmd+S, serverseitige Versionskonflikte bleiben erhalten.
- Alte fünf Startseitenmodule bleiben beim Update editierbar; Freigaben und öffentliche Snapshots bleiben getrennt.

## Daten & Qualität

- Additive Migration von Datenbankschema 1 auf 2; neuer Speicher für Modulvorlagen.
- Aktualisierte Backup-/Restore-Kompatibilität und dokumentierter Updatepfad.
- 98 Python-Tests, TypeScript-Prüfung und reproduzierbare Browser-/API-Integration im Testtransport.
- Keine Einführung beliebiger HTML-/JavaScript-Snippets im Adminbereich.

Details und verbleibende Grenzen: TESTBERICHT.md, UPDATE.md und ARCHITEKTUR.md.
