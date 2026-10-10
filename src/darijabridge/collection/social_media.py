import re
from typing import Iterator

from darijabridge.collection.base import Record
from darijabridge.collection.tabular import TabularCollector

URL_RE = re.compile(r"https?://\S+|www\.\S+")
USER_RE = re.compile(r"@\w+")


class SocialMediaCollector(TabularCollector):
    """Loads an export you are allowed to use (CSV/JSONL with a text column).
    No scraping here: respect each platform's terms of service and privacy.
    Mentions and URLs are removed at collection time to limit personal data."""

    def iter_records(self) -> Iterator[Record]:
        for rec in super().iter_records():
            text = USER_RE.sub("", URL_RE.sub("", rec.text_darija)).strip()
            if text:
                rec.text_darija = text
                yield rec
