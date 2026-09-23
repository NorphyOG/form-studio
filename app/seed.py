"""Transparent, fictional demo content. Seeding never overwrites existing records."""
from .content import create_content
from .catalog import make_block
from datetime import date

SERVICES = [
 ('Brand Design','brand','Marken, die nicht nur gut aussehen. Sondern wiedererkannt werden.','Positionierung, Identität und ein System, das mit deiner Marke wächst. Gemeinsam übersetzen wir deinen Kern in ein eigenständiges visuelles Erscheinungsbild.',['Strategie','Identität','Designsystem']),
 ('Visual Design','visual','Ein visueller Gedanke. Überall konsequent weitergedacht.','Art Direction, digitale Kampagnen und klare visuelle Geschichten. Von der ersten Skizze bis zum wiederverwendbaren Asset.',['Art Direction','Kampagnen','Assets']),
 ('Motion & Film','motion','Ideen bewegen. Aufmerksamkeit behalten.','Bewegung als Teil deiner Identität: präzise Animationen, erklärende Sequenzen und bewegte Markenwelten. Bewusst eingesetzt statt als Selbstzweck.',['Motion','Animation','Film']),
 ('Web & Digital','web','Digitale Erlebnisse, die sich richtig anfühlen.','Websites und digitale Produkte mit einem klaren System dahinter. Wir verbinden Gestaltung mit modularer Entwicklung, guter Bedienbarkeit und einfacher Inhaltspflege.',['Websites','UX / UI','Entwicklung']),
 ('Print & Editorial','print','Digitale Gedanken. Zum Anfassen gemacht.','Editorial, Print und Kommunikationsmittel, die Gestaltung auch jenseits des Bildschirms erlebbar machen. Konsistent von der Typografie bis zum Material.',['Editorial','Packaging','Print']),
 ('AI & Automation','automation','Weniger Wiederholung. Mehr Raum für das Wesentliche.','Wir prüfen, wo Automatisierung tatsächlich hilft, und bauen nachvollziehbare Abläufe mit klaren Grenzen, menschlicher Kontrolle und wartbaren Schnittstellen.',['Workflows','Prototypen','Integration']),
 ('3D & Raum','space','Neue Perspektiven für Produkte und Ideen.','Räumliche Visualisierungen, die eine Idee verständlich machen. Von reduzierten Produktstudien bis zu eigenständigen digitalen Szenen.',['3D','Visualisierung','Raum'])
]

def seed(db):
    if db.one('SELECT id FROM content LIMIT 1'):
        return
    for i,(title,art,desc,body,tags) in enumerate(SERVICES):
        create_content(db,'service',dict(title=title,slug=art,art=art,description=desc,body=body,tags=tags,order=i),publish=True)
    projects = [
        ('MONO — Less, but better.','mono','brand','Branding','Ein reduziertes Identitätssystem für eine fiktive Designmarke.'),
        ('Orbit — A different perspective.','orbit','space','Digital','Eine digitale Produktwelt zwischen Klarheit und räumlicher Tiefe.'),
        ('Paper / Matter','paper-matter','print','Editorial','Ein experimentelles Editorial-System mit kontrastreicher Typografie.')
    ]
    for i,(title,slug,art,category,desc) in enumerate(projects):
        create_content(db,'project',dict(title=title,slug=slug,art=art,category=category,description=desc,
            body='Dieses Projekt ist ein fiktives Gestaltungsbeispiel für die Website-Vorschau, keine echte Kundenreferenz.\n\n'+desc+'\n\nIm Adminbereich kannst du dieses Beispiel durch deine eigenen Arbeiten ersetzen: mit Beschreibung, Vorschaubild und Kategorien.',
            tags=[category,'Konzept'],order=i,demo=True),publish=True)
    create_content(db,'settings',dict(title='Website-Einstellungen',slug='site',brand='FORM / STUDIO',description='Unabhängiges Studio für Design und digitale Erlebnisse.'),publish=True)
    for i, (title, slug, art, category, text) in enumerate([
        ('Warum ein System besser ist als zwanzig Einzelteile.', 'design-als-system', 'stack', 'Design', 'Wiederverwendbare Bausteine schaffen einen gemeinsamen Rahmen. Texte, Bilder und Inhalte können wechseln, ohne dass die gesamte Gestaltung neu beginnt.'),
        ('Bewegung, die Orientierung gibt.', 'bewegung-mit-richtung', 'rings', 'Einblicke', 'Animationen können Zusammenhänge sichtbar machen. Entscheidend ist, dass die Oberfläche auch ohne Bewegung vollständig verständlich und benutzbar bleibt.'),
        ('Ein neues Kapitel beginnt im Editor.', 'ein-neues-kapitel', 'print', 'Studio', 'Ein Beitrag beginnt als Entwurf. Vorschau, Prüfung und Veröffentlichung bleiben getrennt, damit Ideen erst dann öffentlich werden, wenn sie bereit sind.')
    ]):
        create_content(db, 'article', dict(title=title, slug=slug, art=art, category=category, author='Demo-Redaktion', published_on=date.today().isoformat(), description=text,
            body='BEISPIELBEITRAG — Dieser Text demonstriert den Baukasten und ist keine echte Unternehmensmeldung.\n\n'+text+'\n\nErsetze diesen Beispieltext durch eigene Informationen, Quellen und Einblicke. Module ergänzen Bilder, Erklärungen und Verweise.',
            blocks=[make_block('quote', id='gedanke', title='Ein klarer Rahmen lässt Raum für gute Ideen.', text='Beispielaussage der Demo-Redaktion, keine Kundenreferenz.')]), publish=True)
    campaign = create_content(db, 'campaign', dict(title='Raum für deine nächste Idee.', slug='demopartner', sponsor='DEMO / BEISPIELPARTNER', description='So kann ein zentral gepflegter Partnerplatz aussehen.', body='Diese Anzeige ist ein sichtbares Gestaltungsbeispiel. Es besteht keine bezahlte Partnerschaft.', art='mesh', link_label='Beispielanfrage öffnen', link_url='/kontakt'), publish=True)
    create_content(db, 'page', dict(title='Spielraum', slug='spielraum', description='Interaktive Bausteine ausprobieren. Alle Inhalte sind Gestaltungsbeispiele.', in_navigation=True, navigation_label='Spielraum',
        blocks=[make_block('spotlight', id='buehne', title='Nicht nur ansehen.\nAusprobieren.', theme='dark', art='space', text='Eine Bühne für neue Ideen. Themen wechseln, Perspektiven verschieben und Bausteine neu zusammendenken.', animation='repeat'),
                make_block('tabs', id='perspektiven'), make_block('comparison', id='vergleich'), make_block('timeline', id='entwicklung'), make_block('advert', id='partner', campaign=campaign['id']), make_block('contact', id='weiterdenken')]), publish=True)
    blocks = [
        dict(id='leistungen',type='bento',eyebrow='INDEPENDENT DIGITAL STUDIO',title='IDEEN.\nMIT WIRKUNG.',text='Wir verbinden Design und Technologie. Für Marken, die etwas bewegen.'),
        dict(id='arbeiten',type='projects',eyebrow='AUSGEWÄHLTE KONZEPTE',title='Nicht nur schön.\nDurchdacht.',text='Ein erster Einblick in mögliche Markenwelten. Diese Arbeiten sind als Konzeptbeispiele angelegt.'),
        dict(id='studio',type='process',eyebrow='WENIGER UMWEGE. MEHR KLARHEIT.',title='Gute Arbeit beginnt\nmit guten Fragen.',text='Vom ersten Gedanken bis zur fertigen Umsetzung. Transparent, gemeinsam und mit einem klaren nächsten Schritt.',items=[
            dict(title='Verstehen',text='Wir klären Ziele, Zielgruppe und die eigentliche Aufgabe.'),
            dict(title='Gestalten',text='Wir machen aus einer Richtung ein greifbares Konzept.'),
            dict(title='Umsetzen',text='Wir bauen, testen und verfeinern bis ins Detail.'),
            dict(title='Weiterdenken',text='Wir übergeben ein System, das du selbst weiterpflegen kannst.')]),
        dict(id='fragen',type='faq',eyebrow='GUT ZU WISSEN',title='Noch eine Frage?',items=[
            dict(title='Kann ich Inhalte später selbst ändern?',text='Ja. Texte, Leistungskarten, Projekte und Seitenmodule werden im Adminbereich verwaltet. Neue Modultypen oder neue Geschäftslogik ergänzt ein Entwickler.'),
            dict(title='Muss meine Idee schon fertig sein?',text='Nein. Ein Ziel, eine Frage oder eine grobe Richtung reicht für ein erstes Gespräch.'),
            dict(title='Wie läuft eine Projektanfrage ab?',text='Du beschreibst kurz dein Vorhaben. Die Anfrage landet im Adminbereich und kann dort bearbeitet werden. In dieser lokalen Version wird noch keine E-Mail automatisch versendet.')]),
        make_block('news', id='journal', title='Neue Gedanken.\nNeue Perspektiven.', limit=3),
        dict(id='kontakt',type='contact',eyebrow='DEIN NÄCHSTER SCHRITT',title='Eine gute Idee\nbeginnt mit einem Hallo.',text='Erzähl uns, was du vorhast. Den Rest finden wir gemeinsam heraus.')
    ]
    create_content(db,'page',dict(title='Startseite',slug='home',description='Design und Technologie, modular zusammengedacht. Entdecke Leistungen, Konzepte und den Weg zu deinem nächsten Projekt.',blocks=blocks),publish=True)
    for slug,title in [('impressum','Impressum'),('datenschutz','Datenschutz')]:
        create_content(db,'page',dict(title=title,slug=slug,blocks=[dict(id='hinweis',type='text',eyebrow='DEMO / VOR VERÖFFENTLICHUNG ERSETZEN',title=title,text='Hier fehlen die individuellen Angaben des Betreibers. Diese Seite ist ein sichtbarer Platzhalter und kein fertiger Rechtstext. Vor einer öffentlichen Nutzung müssen Betreiberangaben, tatsächliche Datenverarbeitung und passende Hinweise ergänzt und geprüft werden.')]),publish=True)
