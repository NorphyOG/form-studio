"""Strict shared content contracts. User input is text, never executable HTML."""
from typing import Literal, Annotated
from urllib.parse import urlsplit
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
import re

Kind = Literal['service', 'project', 'page', 'settings', 'article', 'campaign']
Art = Literal['brand', 'web', 'visual', 'motion', 'print', 'automation', 'space', 'stack', 'mesh', 'spark', 'rings', 'landscape']

class Model(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class Credentials(Model):
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=1, max_length=256)

class UserInput(Credentials):
    name: str = Field(min_length=2, max_length=80)
    role: Literal['admin', 'editor', 'moderator'] = 'editor'

    @field_validator('password')
    @classmethod
    def password_length(cls, value):
        if len(value) < 12:
            raise ValueError('Das Passwort muss mindestens 12 Zeichen lang sein.')
        return value

    @field_validator('email')
    @classmethod
    def valid_email(cls, value):
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
            raise ValueError('Bitte eine gültige E-Mail-Adresse eingeben.')
        return value.lower()

class SetupInput(UserInput):
    setup_key: str = Field(min_length=16, max_length=200)

class BaseContent(Model):
    title: str = Field(min_length=2, max_length=120)
    slug: str = Field(pattern=r'^[a-z0-9][a-z0-9-]{0,63}$')
    description: str = Field(default='', max_length=500)
    order: int = Field(default=0, ge=0, le=10000)

class Service(BaseContent):
    art: Art = 'web'
    body: str = Field(default='', max_length=15000)
    tags: list[str] = Field(default_factory=list, max_length=8)
    image: str = Field(default='', pattern=r'^(|[a-f0-9]{32})$')

    @field_validator('tags')
    @classmethod
    def tag_length(cls, tags):
        if any(not t.strip() or len(t) > 40 for t in tags):
            raise ValueError('Tags müssen 1–40 Zeichen lang sein.')
        return tags

class Project(Service):
    category: str = Field(default='Digital', min_length=1, max_length=50)
    client: str = Field(default='Konzeptprojekt', max_length=80)
    year: str = Field(default='2026', pattern=r'^20[0-9]{2}$')
    demo: bool = True

def safe_link(value: str) -> str:
    """Allow local absolute paths, anchors and HTTPS; never active URL schemes."""
    if not value:
        return value
    if re.search(r'[\x00-\x20\x7f\\]', value) or '%' in value[:10]:
        raise ValueError('Keine Leerzeichen, Steuerzeichen oder maskierte URL-Präfixe.')
    if value.startswith('#') and re.fullmatch(r'#[a-zA-Z0-9_-]+', value):
        return value
    if value.startswith('/') and not value.startswith('//'):
        return value
    parsed = urlsplit(value)
    if parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.password:
        return value
    raise ValueError('Erlaubt: /kontakt, #abschnitt oder eine vollständige HTTPS-Adresse.')

class BlockItem(Model):
    title: str = Field(min_length=1, max_length=150)
    text: str = Field(default='', max_length=3000)
    value: str = Field(default='', max_length=60)
    link_label: str = Field(default='', max_length=60)
    link_url: str = Field(default='', max_length=1000)
    image: str = Field(default='', pattern=r'^(|[a-f0-9]{32})$')
    art: Art = 'brand'

    _safe_link = field_validator('link_url')(safe_link)

BlockType = Literal['bento', 'projects', 'process', 'text', 'faq', 'contact',
                    'features', 'media', 'stats', 'quote', 'logos', 'pricing', 'gallery', 'divider', 'news', 'advert', 'spotlight', 'tabs', 'timeline', 'comparison']

class Block(Model):
    id: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,50}$')
    type: BlockType
    enabled: bool = True
    eyebrow: str = Field(default='', max_length=80)
    title: str = Field(default='', max_length=150)
    text: str = Field(default='', max_length=10000)
    items: list[BlockItem] = Field(default_factory=list, max_length=20)
    theme: Literal['paper', 'blue', 'dark'] = 'paper'
    spacing: Literal['compact', 'normal', 'spacious'] = 'normal'
    width: Literal['wide', 'narrow'] = 'wide'
    animation: Literal['auto', 'reveal', 'slide', 'none', 'unfold', 'stack', 'repeat'] = 'auto'
    columns: Literal[2, 3, 4] = 3
    category: str = Field(default='', max_length=50)
    limit: int = Field(default=6, ge=1, le=12)
    campaign: str = Field(default='', pattern=r'^(|[a-f0-9]{32})$')
    align: Literal['left', 'center'] = 'left'
    image: str = Field(default='', pattern=r'^(|[a-f0-9]{32})$')
    art: Art = 'space'
    link_label: str = Field(default='', max_length=60)
    link_url: str = Field(default='', max_length=1000)

    _safe_link = field_validator('link_url')(safe_link)

    @model_validator(mode='after')
    def contact_has_two_notes(self):
        if self.type == 'comparison' and len(self.items) > 2:
            raise ValueError('Ein Vorher-/Nachher-Vergleich verwendet höchstens zwei Einträge.')
        if self.type == 'contact' and len(self.items) > 2:
            raise ValueError('Die Kontakt-Bühne hat zwei Randkarten. Weitere Karten als eigenes Modul ergänzen.')
        return self

class ReusableInput(Model):
    name: str = Field(min_length=2, max_length=80)
    block: Block

class Page(BaseContent):
    in_navigation: bool = False
    navigation_label: str = Field(default='', max_length=30)
    blocks: list[Block] = Field(default_factory=list, max_length=30)

    @field_validator('blocks')
    @classmethod
    def unique_ids(cls, value):
        if len({b.id for b in value}) != len(value):
            raise ValueError('Modul-IDs müssen eindeutig sein.')
        return value

class SiteSettings(BaseContent):
    brand: str = Field(default='FORM / STUDIO', min_length=2, max_length=40)
    tagline: str = Field(default='Independent digital studio', max_length=80)
    email: str = Field(default='', max_length=200)
    accent: str = Field(default='blue', pattern=r'^(blue|purple|green|orange)$')
    design: Literal['studio', 'noir', 'editorial', 'atelier', 'aurora', 'brutalist', 'minimal', 'garden', 'sunset', 'terminal'] = 'studio'
    location: str = Field(default='Design. Technologie. Wirkung.', max_length=100)
    motion: Literal['signature', 'subtle', 'off'] = 'signature'
    intro: Literal['session', 'always', 'off'] = 'session'
    analytics_enabled: bool = False
    news_in_navigation: bool = True

    @model_validator(mode='after')
    def fixed_slug(self):
        if self.slug != 'site':
            raise ValueError('Die Einstellungs-ID muss site bleiben.')
        return self

class ContentInput(Model):
    kind: Kind
    data: dict

class ContentUpdate(Model):
    data: dict
    expected_revision: int = Field(ge=1)

class Action(Model):
    expected_revision: int = Field(ge=1)
    note: str = Field(default='', max_length=2000)

class Inquiry(Model):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=200)
    service: str = Field(default='Noch offen', max_length=120)
    message: str = Field(min_length=10, max_length=6000)
    website: str = Field(default='', max_length=500)  # Honeypot, not a real website field.
    privacy: bool

    @field_validator('email')
    @classmethod
    def email_valid(cls, value):
        return UserInput.valid_email(value)

    @field_validator('privacy')
    @classmethod
    def privacy_acknowledged(cls, value):
        if not value:
            raise ValueError('Bitte den Datenschutzhinweis bestätigen.')
        return value

class InquiryStatus(Model):
    status: Literal['new', 'in_progress', 'done', 'spam']

class UserState(Model):
    active: bool

def valid_date(value: str) -> str:
    from datetime import date
    if value:
        try:
            if date.fromisoformat(value).isoformat() != value:
                raise ValueError()
        except ValueError as exc:
            raise ValueError('Bitte ein gültiges Datum im Format JJJJ-MM-TT angeben.') from exc
    return value


class Article(Service):
    category: str = Field(default='Studio', min_length=1, max_length=50)
    author: str = Field(default='Redaktion', min_length=1, max_length=80)
    published_on: str = Field(default_factory=lambda: __import__('datetime').date.today().isoformat(), min_length=10, max_length=10)
    featured: bool = False
    blocks: list[Block] = Field(default_factory=list, max_length=30)

    _valid_date = field_validator('published_on')(valid_date)
    _unique_blocks = field_validator('blocks')(Page.unique_ids.__func__)


class Campaign(BaseContent):
    sponsor: str = Field(default='', max_length=80)
    body: str = Field(default='', max_length=1500)
    link_label: str = Field(default='Mehr erfahren', min_length=1, max_length=60)
    link_url: str = Field(min_length=1, max_length=1000)
    image: str = Field(default='', pattern=r'^(|[a-f0-9]{32})$')
    art: Art = 'rings'
    starts_on: str = Field(default='', max_length=10)
    ends_on: str = Field(default='', max_length=10)

    _link = field_validator('link_url')(safe_link)
    _dates = field_validator('starts_on', 'ends_on')(valid_date)

    @model_validator(mode='after')
    def date_order(self):
        if self.starts_on and self.ends_on and self.ends_on < self.starts_on:
            raise ValueError('Das Enddatum darf nicht vor dem Startdatum liegen.')
        return self


CONTENT_MODELS = {'service': Service, 'project': Project, 'page': Page,
                  'settings': SiteSettings, 'article': Article, 'campaign': Campaign}

def validate_content(kind, data):
    return CONTENT_MODELS[kind].model_validate(data).model_dump()
