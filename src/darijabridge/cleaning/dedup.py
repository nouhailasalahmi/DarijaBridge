class Deduper:
    """Exact duplicates on (darija, translation), case-insensitive. First occurrence wins,
    so the order of sources in the config is the priority order."""

    def __init__(self) -> None:
        self._seen: dict[tuple[str, str], str] = {}

    def check(self, source: str, darija: str, target: str | None) -> str | None:
        key = (darija.casefold(), (target or "").casefold())
        first = self._seen.get(key)
        if first is None:
            self._seen[key] = source
            return None
        return "duplicate_in_source" if first == source else "duplicate_other_source"
