from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterator

from darijabridge.utils.io import make_id, write_jsonl
from darijabridge.utils.logging import get_logger


@dataclass
class Record:
    """Common schema shared by every source."""
    source: str
    text_darija: str
    text_target: str | None = None      # translation (FR/EN/MSA...) if available
    target_lang: str | None = None
    license: str | None = None
    meta: dict = field(default_factory=dict)
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = make_id(self.source, self.text_darija, self.text_target or "")


class BaseCollector(ABC):
    """One collector per source. Subclasses only implement iter_records()."""

    def __init__(self, name: str, cfg: dict, raw_root: str | Path = "data/raw"):
        self.name = name
        self.cfg = cfg
        self.out_dir = Path(raw_root) / name
        self.log = get_logger(f"collect.{name}")

    @abstractmethod
    def iter_records(self) -> Iterator[Record]:
        ...

    def run(self) -> int:
        out = self.out_dir / f"{self.name}.jsonl"
        n = write_jsonl((asdict(r) for r in self.iter_records()), out)
        self.log.info("%d records written to %s", n, out)
        return n
