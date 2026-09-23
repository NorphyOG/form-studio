# Von v0.1 / v0.2 auf v0.3 — vorhandene Daten behalten

## Sicherer Wechsel unter Windows

1. Im alten Projekt ein Backup erzeugen: `python scripts/backup.py`. Bei einem eigenen Datenpfad: `python scripts/backup.py --data-dir "C:\Pfad\Daten"`. Das Backup enthält private Inhalte und Zugangsdaten-Hashes; geschützt aufbewahren.
2. Alten Server mit Strg+C beenden. Das alte Projekt und das Backup behalten.
3. v0.3 vollständig in einen **neuen Ordner** entpacken. Nicht über den alten Ordner kopieren. Keine alte `.venv` übernehmen.
4. Im neuen Projekt das vertrauenswürdige Backup wiederherstellen:

   ```powershell
   python scripts/restore_backup.py "C:\Pfad\studio-backup-DATUM.zip"
   ```

   Das Ziel `data` muss leer oder nicht vorhanden sein. Bereits erzeugte Testdaten vorher sichern und den Ordner umbenennen, nicht ungeprüft löschen. Für andere Pfade `--data-dir` angeben.
5. `START-WINDOWS.cmd` starten. Unter bisherigen Zugangsdaten neu anmelden. Restore beendet alte Sitzungen; Benutzer und Passwörter bleiben erhalten.
6. Startseite, Bilder, Freigabestatus, einen Entwurf und zwei wichtige Detailseiten prüfen. Browser bei alten JavaScript-Dateien einmal mit Strg+F5 vollständig neu laden.

## Automatische Migration, keine automatische Umgestaltung

Schema 1 oder 2 wird auf **Schema 3** erweitert. Neue Leseindizes und die Tabelle `metrics_daily` kommen hinzu; bei Schema 1 außerdem die bereits in v0.2 eingeführte Bausteintabelle. Bestehende Inhalte werden nicht überschrieben. Wiederholte Initialisierung ist getestet.

Ein bestehendes Projekt bekommt **keine** Demo-Beiträge oder neue Spielraum-Seite aufgezwungen. Die neuen Module stehen im Katalog bereit. Ein News-Modul selbst einsetzen; Beiträge unter „Journal & News“ anlegen. Das Journal ist unter `/news` erreichbar. Seine Navigation lässt sich in den Einstellungen ausschalten.

Die Statistik ist bei alten Daten ohne das neue Feld **ausgeschaltet**. Aktivierung braucht einen gespeicherten und veröffentlichten Einstellungsstand. Anschließend braucht die Messung zusätzlich die Zustimmung der jeweiligen Besucher.

## Alternative und Rückwechsel

Bei vollständig gestopptem alten Server kann auch der gesamte Datenordner kopiert werden. Nicht nur `studio.sqlite3` aus einem laufenden WAL-Betrieb kopieren. Die eigene `.env` prüfen: Ein absoluter `DATA_DIR` darf nicht versehentlich auf den alten produktiven Datenordner zeigen.

**v0.1/v0.2 dürfen Schema 3 nicht öffnen.** Nicht die Versionsnummer der Datenbank von Hand zurücksetzen. Zum Rückwechsel das vor dem Update erstellte Backup mit der passenden alten Version in einen leeren Datenordner zurückspielen. Änderungen nach diesem Backup sind darin nicht enthalten.

Der Windows-Doppelklickstarter wurde in dieser Umgebung nicht ausgeführt. Schema-Migration und Backup/Restore wurden unter Linux automatisiert geprüft.
