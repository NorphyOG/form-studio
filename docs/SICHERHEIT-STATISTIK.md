# Sicherheits- und Statistikmodell 0.3

## Bereits im Code

Sitzungen serverseitig, Passwörter mit Argon2-Hashes. HttpOnly-/SameSite-Cookies, bei HTTPS-Konfiguration Secure. Schreibende Adminaufrufe benötigen Sitzung, Rolle, CSRF-Token und passende Origin. Redaktion darf Entwürfe einreichen, aber nicht eigenmächtig veröffentlichen; Moderation darf nur eingereichte Stände freigeben. Globale Einstellungen, Benutzerverwaltung und Statistiklöschung sind Administration vorbehalten.

Pydantic lehnt unbekannte Felder ab, URLs haben ein eingeschränktes Schema, Inhalte sind Text statt frei ausführbarem HTML. Jinja-Ausgaben und Admin-Ausgaben werden escaped. CSP erlaubt keine externen Skripte oder beliebigen Inline-Skripte. Uploads sind auf JPEG/PNG/WebP, Größe und Pixelzahl begrenzt und werden neu kodiert. SQL verwendet Parameter für Nutzereingaben. Revisionen schützen vor stillem Überschreiben, nicht vor vorsätzlich falschen Veröffentlichungen berechtigter Benutzer.

Diese Schutzschichten orientieren sich an dokumentierten Ansätzen, darunter OWASP [2]. Sie sind kein unabhängiges Penetrationstest-Zertifikat und keine Garantie gegen jede Schwachstelle. Ein echter HTTPS-/Browser-/Betriebstest und aktuelle Abhängigkeitsprüfungen bleiben Aufgabe vor dem Livegang.

## Was die optionale Statistik erfasst

Standard: **aus**. Nach Aktivierung im veröffentlichten Einstellungsstand entscheidet jeder Gast über eine gleichwertige Zustimmungsauswahl. Vor Zustimmung verschickt die Website keine Statistikereignisse. DNT/GPC werden berücksichtigt. Mit vorhandener Admin-Sitzung zählt das Backend nicht.

Gespeichert wird ausschließlich eine Tagesaggregation: UTC-Tag, Ereignistyp, öffentlicher Seitenpfad oder Kampagnen-ID, Anzahl. Keine IP-Adressen, User-Agents, Referrer, Querystrings oder individuellen Browserverläufe in `metrics_daily`. Der Server bekommt IP-Adressen technisch bei HTTP-Anfragen; für Ereignisbegrenzung gibt es kurzlebige HMAC-Schlüssel im Arbeitsspeicher. **Webserver-/Proxy-Zugriffslogs sind davon getrennt** und müssen vom Betreiber separat konfiguriert werden.

Der Browser hält einen zufälligen Tab-Token nur im RAM. Keine dauerhafte Besucher-ID. Nur die Zustimmungsauswahl wird, sofern verfügbar, 180 Tage lokal gespeichert. Mehrere Tabs sind keine mehreren Menschen. Gezählt werden sichtbare Seitenfenster mit Zustimmung; Wiederholungen eines Aufrufs in demselben Dokument werden vermieden. Ein vollständiges Neuladen ist ein neuer Aufruf. Aktive Tabs verfallen nach 90 Sekunden ohne Lebenszeichen; ein Serverneustart setzt die RAM-Anzeige zurück.

Anzeigensichtung: Im Browser mindestens 50 % der Fläche eine Sekunde sichtbar. Klick: Aktivierung des Kampagnenlinks. Mehrere identische Plätze derselben Kampagne werden innerhalb eines Dokuments zusammengefasst. Backendwerte sind beobachtende, manipulierbare Telemetrie, keine revisionssichere Abrechnungsgrundlage. Keine Käufer, Conversion, Einnahmen oder eindeutigen Besucher ermittelt. Ohne Zustimmung, mit Skriptblockern oder bei Netzfehlern fehlen Aufrufe.

## Aufbewahrung und Löschung

Berichte bieten 7, 30 oder 90 Tage. Ältere Tagesaggregate werden spätestens beim nächsten gezählten Ereignis mit fälliger stündlicher Bereinigung entfernt. Wenn keine neuen Ereignisse eintreffen oder die Messung abgeschaltet ist, läuft **kein geplanter Löschdienst**: alte Daten bleiben bis zur nächsten Bereinigung oder manuellen Löschung in der Datenbank. Administration kann alle Statistikdaten sofort über den Analysebereich löschen.

Widerruf beendet weitere Messung dieses Browserdokuments und entfernt seinen aktiven Tab. Bereits aggregierte, nicht individuell zugeordnete Tageszähler werden nicht nachträglich einer Person zugeordnet oder selektiv abgezogen. Backups enthalten den jeweiligen Datenbankstand und benötigen ein eigenes Aufbewahrungskonzept.

## Betrieb

Nur eine Serverinstanz für die aktuelle RAM-Metrik. Proxy-Ratenbegrenzung und vertrauenswürdige Proxy-IP-Konfiguration bei einem echten Hosting gesondert planen; der Starter vertraut standardmäßig keinen weitergereichten Proxy-IP-Headern. Admin-Accounts klein halten, lokale Daten schützen, Backups testen und Abhängigkeiten aktualisieren.

Vor einer Veröffentlichung müssen Betreiber die tatsächlichen Datenverarbeitungen, Anbieter, Logs, Kontaktanfragen, Uploads und optionalen Messfunktionen in passenden eigenen Hinweisen berücksichtigen. Die mitgelieferte Datenschutzseite ist ein sichtbarer Platzhalter, kein fertiger Rechtstext.
