# Mitgelieferte Standard-Assets

Die zwölf SVG-Dateien unter `app/static/assets/` sind direkt im Projekt erzeugte geometrische Gestaltungselemente. Die gleichen Motive werden für interaktive Leistungskacheln über `app/templates/art.html` ausgegeben. Es wurden keine fremden Stockgrafiken, Personenbilder, Markenlogos oder kostenpflichtigen Iconpakete eingebunden. Die Schriften verwenden System-Fallbacks; Schriftdateien werden nicht mitgeliefert.

| Datei | Bezeichnung |
|---|---|
| brand.svg | Farbsystem |
| visual.svg | Geometrie |
| motion.svg | Orbit |
| web.svg | Wireframe |
| print.svg | Editorial |
| automation.svg | Netzwerk |
| space.svg | Raumstudie |
| stack.svg | Ebenen |
| mesh.svg | Wellenfeld |
| spark.svg | Strahlen |
| rings.svg | Ringe |
| landscape.svg | Horizont |

Die Grafiken sind für die Verwendung und Anpassung in diesem Projekt vorgesehen. Diese Herkunftsbeschreibung ist keine Prüfung von Markenrechten des Platzhalternamens oder der gezeigten Beispielfirmen. Namen und echte Referenzen vor öffentlicher Nutzung gesondert klären.

Die vollständige Website orientiert sich an der vom Nutzer bereitgestellten Videoreferenz; deren Originalvideo wird nicht mit dem Projekt ausgeliefert. Die neuen Screenshots und die Animationsvorschau zeigen die tatsächlich implementierte Oberfläche.

Eigene Bilder haben Vorrang vor dem jeweiligen Standardmotiv. Hochgeladene PNG/JPEG/WebP-Dateien werden serverseitig neu kodiert. SVG-Uploads sind nicht freigeschaltet.

## Designpakete in Version 0.4

`docs/designs/*.png`, `docs/design-gallery.png`, `docs/design-switcher.gif` und `docs/admin-designs.png` wurden mit `scripts/capture_designs.py` aus der lokalen Demo-Anwendung und den zehn tatsächlich implementierten CSS-Designs erzeugt. Das Skript nutzt FastAPI TestClient und installiertes Chromium; es zeigt keine bereitgestellte Website. Der Bildzuschnitt und die GIF-Reihenfolge wurden programmatisch erstellt. Die früheren 0.3-Screenshots und `motion-preview.gif` bleiben unverändert erhalten.
