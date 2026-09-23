"""Trusted, versioned module registry consumed by the admin UI.

Content is plain text. Adding a module requires an explicit schema, renderer,
registry entry and tests; administrators can freely compose existing modules.
"""
from .models import Block

ARTS = [
    ('brand','Farbsystem','Marke'), ('visual','Geometrie','Form'),
    ('motion','Orbit','Bewegung'), ('web','Wireframe','Digital'),
    ('print','Editorial','Print'), ('automation','Netzwerk','Digital'),
    ('space','Raumstudie','Form'), ('stack','Ebenen','Form'),
    ('mesh','Wellenfeld','Textur'), ('spark','Strahlen','Form'),
    ('rings','Ringe','Bewegung'), ('landscape','Horizont','Textur'),
]
# supports drives which inspector fields appear; no arbitrary HTML/CSS is stored.
_DEFS = [
 ('bento','Signature-Raster','Einstieg','Eine große Mitte, interaktive Leistungskacheln und die Öffnungsanimation aus der Videoreferenz.', ['text'], 'IDEEN.\nMIT WIRKUNG.'),
 ('projects','Projektgalerie','Inhalte','Zeigt veröffentlichte Projekte automatisch. Kategorien werden aus den Projekten abgeleitet.', ['text'], 'Aus Ideen\nwird Wirkung.'),
 ('features','Feature-Karten','Inhalte','Eigene Vorteile, Leistungen oder Funktionen als Karten mit Grafik und optionalem Link.', ['text','items','art_items','links_items','columns'], 'Mehr als eine gute Idee.'),
 ('media','Bild + Text','Inhalte','Ein eigenes Bild oder eine Standardgrafik mit erklärendem Text und optionalem Link.', ['text','image','art','link'], 'Ein Gedanke.\nEine neue Perspektive.'),
 ('gallery','Freie Galerie','Inhalte','Eigene Bilder und Standardgrafiken frei zusammenstellen – unabhängig von Projekten.', ['text','items','art_items','image_items','columns'], 'Einblicke ins Detail.'),
 ('process','Prozess / Schritte','Vertrauen','Erklärt einen Ablauf in nachvollziehbaren, nummerierten Schritten.', ['text','items'], 'Ein klarer Weg.'),
 ('stats','Kennzahlen','Vertrauen','Zahlen, Einheiten und Erläuterungen. Werte werden wörtlich angezeigt, nicht künstlich hochgezählt.', ['text','items','values','columns'], 'Auf einen Blick.'),
 ('quote','Zitat / Stimme','Vertrauen','Ein bewusst gesetztes Zitat mit Quellenangabe. Verwende nur belegbare, freigegebene Aussagen.', ['text'], 'Was andere sagen.'),
 ('logos','Namen / Partner','Vertrauen','Eine ruhige Leiste mit Namen oder Begriffen. Keine ungeprüften Kundenlogos oder erfundenen Referenzen.', ['items','columns'], 'Ein gutes Netzwerk.'),
 ('pricing','Angebotspakete','Aktion','Pakete mit Preistext, Leistungsbeschreibung und individuellem Anfrage-Link. Kein Shop oder Checkout.', ['text','items','values','links_items','columns'], 'Der passende Rahmen.'),
 ('faq','Fragen & Antworten','Vertrauen','Aufklappbare Fragen. Texte bleiben auch ohne JavaScript zugänglich.', ['items'], 'Gut zu wissen.'),
 ('contact','Kontakt-Bühne','Aktion','Ein großer Aufruf mit versetzt einfahrenden Randkarten und frei wählbarem Ziel.', ['text','link','items'], 'Erzähl uns,\nwas du vorhast.'),
 ('text','Freier Text','Grundlagen','Überschrift und längerer Text, etwa für Hintergründe oder Informationsseiten. HTML wird nicht ausgeführt.', ['text'], 'Raum für deine Gedanken.'),
 ('divider','Trenner / Zwischenraum','Grundlagen','Eine grafische Zäsur mit optionaler Bezeichnung. Der Abstand ist über die Darstellung einstellbar.', [], ''),
]

_DEFS.extend([
 ('news','Journal / News','Dynamische Inhalte','Automatisch veröffentlichte Beiträge anzeigen, nach Kategorie filtern und auf das durchsuchbare Journal verlinken.', ['text','news','columns'], 'Was uns gerade bewegt.'),
 ('advert','Werbeplatz','Dynamische Inhalte','Eine zentral gepflegte Kampagne einblenden. Veröffentlichung und Zeitraum steuern die Sichtbarkeit. Immer als Anzeige gekennzeichnet.', ['campaign'], 'Raum für Partner.'),
 ('spotlight','Spotlight / Bühne','Einstieg','Große Typografie, eine räumliche Grafik und ein klarer Aufruf – auch ohne Leistungskatalog.', ['text','image','art','link'], 'Die nächste Idee.\nSchon einen Schritt weiter.'),
 ('tabs','Themen / Tabs','Inhalte','Mehrere Perspektiven in einer kompakten, per Tastatur bedienbaren Themenansicht. Ohne JavaScript bleiben alle Texte lesbar.', ['text','items','art_items','image_items','links_items'], 'Ein Thema. Viele Perspektiven.'),
 ('timeline','Zeitstrahl','Vertrauen','Meilensteine, Projektphasen oder einen Veranstaltungsablauf als visuelle Geschichte zeigen.', ['text','items','values'], 'Von der Idee zum nächsten Kapitel.'),
 ('comparison','Vorher / Nachher','Inhalte','Zwei Bilder oder Grafiken mit einem zugänglichen Schieberegler vergleichen. Mehr als zwei Einträge sind hier nicht sinnvoll.', ['text','items','image_items','art_items'], 'Ein neuer Blick auf das Gleiche.'),
])

def make_block(kind, **overrides):
    spec=next(item for item in _DEFS if item[0]==kind)
    data=dict(id='module',type=kind,title=spec[5],eyebrow=spec[1].upper(),text='')
    if 'items' in spec[4]:
        data['items']=[dict(title='Beispiel '+str(i+1),text='Diesen Beispieltext durch deinen eigenen Inhalt ersetzen.',
                            value='Beispiel',art=ARTS[i][0]) for i in range(3)]
    if kind=='faq':
        data['items']=[dict(title='Kann ich den Inhalt selbst anpassen?',text='Ja. Alle Texte dieses Moduls lassen sich im Seiteneditor bearbeiten.')]
    if kind=='quote':
        data.update(title='Gute Gestaltung macht komplexe Dinge verständlich.',text='Beispielzitat · Eigene Aussage und belegbare Quelle eintragen.')
    if kind=='contact':
        data.update(link_label='Projekt anfragen',link_url='/kontakt',text='Eine Richtung reicht. Den nächsten Schritt finden wir gemeinsam.',items=[dict(title='Wir denken zuerst.',text='Ein Ziel, eine Frage oder eine erste Richtung reicht.'),dict(title='Deine Idee wächst.',text='Aus einer Richtung wird ein klarer nächster Schritt.')])
    if kind=='media':
        data.update(text='Ein visuelles Thema, ergänzt um eine klare Erklärung. Nutze eine Standardgrafik oder ein eigenes Bild.',link_label='Mehr erfahren',link_url='/kontakt')
    if kind=='spotlight':
        data.update(art='rings',text='Klar im Ausdruck. Flexibel im Aufbau. Bereit für das, was als Nächstes kommt.',link_label='Idee besprechen',link_url='/kontakt',animation='unfold')
    if kind=='news':
        data.update(text='Gedanken, Einblicke und Neuigkeiten aus dem Studio.',limit=3)
    if kind=='comparison':
        data.update(items=[dict(title='Vorher',text='Die Ausgangslage.',art='web'),dict(title='Nachher',text='Die neue Perspektive.',art='space')])
    if kind=='tabs':
        data['items']=[dict(title=t,text=d,art=a) for t,d,a in [('Verstehen','Ziele klären und die richtige Frage finden.','brand'),('Gestalten','Eine klare Idee in eine visuelle Richtung übersetzen.','visual'),('Entwickeln','Ein wartbares System bauen und zusammen testen.','automation')]]
    if kind=='timeline':
        data['items']=[dict(title=t,text=d,value=v) for v,t,d in [('01','Start','Die Idee bekommt einen klaren Rahmen.'),('02','Prototyp','Aus der Richtung wird etwas Greifbares.'),('03','Weiterentwicklung','Prüfen, lernen und gezielt verbessern.')]]
        data['animation']='stack'
    data.update(overrides)
    return Block.model_validate(data).model_dump()


def catalog():
    modules=[dict(type=k,name=n,category=c,description=d,keywords={'pricing':'Preise Preis Preisgestaltung Angebote Pakete','faq':'FAQ Fragen Antworten Hilfe','features':'Vorteile Features Karten Funktionen','logos':'Logos Partner Namen Kunden','bento':'Hero Kacheln Raster Animation Einstieg'}.get(k,k),supports=f,defaults=make_block(k)) for k,n,c,d,f,t in _DEFS]
    templates=[
        dict(id='studio',name='Studio / Portfolio',description='Signature-Einstieg, Arbeiten, Prozess, FAQ und Kontakt.',
             blocks=[make_block(k) for k in ['bento','projects','process','faq','contact']]),
        dict(id='landing',name='Angebot / Landingpage',description='Bild-Text-Einstieg, Vorteile, Pakete, FAQ und Anfrage.',
             blocks=[make_block(k) for k in ['media','features','pricing','faq','contact']]),
        dict(id='story',name='Über uns / Geschichte',description='Bild, Hintergrund, Arbeitsweise und ein klarer Abschluss.',
             blocks=[make_block(k) for k in ['media','text','process','quote','contact']]),
    ]
    templates.extend([
      dict(id='journal',name='Journal / Magazin',description='Editorial-Bühne, automatische Beiträge, Partnerplatz und Themenbereiche.',blocks=[make_block('spotlight',title='Perspektiven.\nNicht nur Schlagzeilen.',art='print'),make_block('news'),make_block('advert'),make_block('tabs')]),
      dict(id='product',name='Produkt / Launch',description='Ein Produkt erklären: Bühne, Vergleich, Funktionen, Pakete und FAQ.',blocks=[make_block('spotlight',title='Eine neue Perspektive.',theme='dark',art='space'),make_block('comparison'),make_block('tabs'),make_block('pricing'),make_block('faq')]),
      dict(id='local',name='Unternehmen / Lokal',description='Leistungen, Arbeitsweise, aktuelle Meldungen und Kontakt.',blocks=[make_block('spotlight',title='Hier beginnt gute Zusammenarbeit.',art='landscape'),make_block('features'),make_block('timeline'),make_block('news'),make_block('contact')]),
      dict(id='event',name='Veranstaltung / Programm',description='Programm und Informationen darstellen. Keine Ticketbuchung oder Bezahlung.',blocks=[make_block('spotlight',title='Zusammen kommt\nmehr in Bewegung.',theme='blue',art='spark'),make_block('timeline',title='Das Programm.'),make_block('media'),make_block('faq'),make_block('contact',title='Dabei sein.',link_label='Informationen anfragen')]),
      dict(id='campaign',name='Kampagne / Partner',description='Eine fokussierte Landingpage mit klar gekennzeichneter Partnerfläche.',blocks=[make_block('spotlight',title='Eine Idee.\nEine klare Richtung.',art='mesh'),make_block('features'),make_block('advert'),make_block('news'),make_block('contact')]),
    ])
    return dict(version=3,modules=modules,templates=templates,assets=[dict(id=k,name=n,category=c,url=f'/static/assets/{k}.svg') for k,n,c in ARTS],limits=dict(blocks=30,items=20,presets=100))
