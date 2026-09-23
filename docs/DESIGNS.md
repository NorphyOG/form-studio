# Designpakete

FORM / STUDIO enthält zehn globale Oberflächen. Alle nutzen dieselben Inhalte, Module, Berechtigungen und URLs. Die Auswahl ist eine Website-Einstellung: **Einstellungen → Designpaket → Entwurf speichern → Veröffentlichen**. Erst die Freigabe ändert die öffentliche Website.

| Paket | Charakter | Sichtbare Unterschiede |
|---|---|---|
| Studio | klar, modular | Blau, strenges Raster, kantige Karten |
| Noir | dunkel, kontrastreich | dunkle Flächen, hellgrüner Akzent, reduzierte Bilder |
| Editorial | klassisch, typografisch | Serifenschrift, redaktionelle Linien, Bogenform |
| Atelier | warm, weich | Terrakotta, runde Karten und Buttons |
| Aurora | kühl, räumlich | Türkisverlauf, weiche Bühne, Kreismotiv |
| Brutalist | laut, kantig | kräftige Rahmen, Schlagschatten, Versalien |
| Minimal | ruhig, reduziert | viel Weißraum, Schwarzweißbilder, Linien statt Karten |
| Garden | organisch, natürlich | Grün, Blattformen, Serifentitel |
| Sunset | lebendig, farbig | Rosé-Orange-Verlauf, runde Karten |
| Terminal | digital, präzise | dunkles Grün, Monospace, gerahmte Elemente |

Die bisherige Akzentfarbe bleibt für **Studio** verfügbar. Die übrigen Pakete bringen bewusst eine abgestimmte eigene Palette mit. Eigene hochgeladene Bilder bleiben unverändert; Standardgrafiken folgen den CSS-Variablen, soweit sie im HTML eingebettet sind. Die statischen SVG-Dateien behalten ihre Originalfarben.

## Eigene Designs beitragen

1. Einen neuen, kurzen Bezeichner in `app/models.py` (`SiteSettings.design`) und `frontend/admin/editor.ts` (`designOptions`) ergänzen.
2. Design-Regeln in `app/static/css/designs.css` und ein Muster in `app/static/css/admin-designs.css` ergänzen. Existierende Designpakete nicht unbeabsichtigt verändern.
3. Kontrast, Lesbarkeit, Fokusmarkierung, mobile Navigation und reduzierte Bewegung prüfen. Inhalte und Sicherheitslogik bleiben gemeinsam.
4. `npm run typecheck`, `npm run build` und `python -m pytest tests -q` ausführen. Für neue Designpakete die integrierten Veröffentlichungsprüfungen erweitern.

Der Designbezeichner wird serverseitig auf erlaubte Werte begrenzt. Freie CSS-Eingabe durch Admins gibt es nicht.
