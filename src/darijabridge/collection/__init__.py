from darijabridge.collection.plaintext import PlainTextCollector
from darijabridge.collection.social_media import SocialMediaCollector
from darijabridge.collection.subtitles import SubtitlesCollector
from darijabridge.collection.tabular import DodaCollector, MadarCollector, TabularCollector

COLLECTORS = {
    "tabular": TabularCollector,
    "doda": DodaCollector,
    "madar": MadarCollector,
    "plaintext": PlainTextCollector,
    "social_media": SocialMediaCollector,
    "subtitles": SubtitlesCollector,
}