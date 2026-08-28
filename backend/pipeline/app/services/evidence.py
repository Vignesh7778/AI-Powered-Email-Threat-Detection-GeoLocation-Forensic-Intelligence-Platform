from collections import defaultdict
from datetime import datetime, timezone
from app.schemas import EvidenceEntry


class EvidenceLedger:
    """In-memory append-only ledger; replace with immutable persistent storage in production."""

    def __init__(self) -> None:
        self._entries: dict[str, list[EvidenceEntry]] = defaultdict(list)

    def record(self, submission_id: str, action: str, **metadata: str) -> EvidenceEntry:
        entry = EvidenceEntry(
            submission_id=submission_id,
            action=action,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata,
        )
        self._entries[submission_id].append(entry)
        return entry

    def chain(self, submission_id: str) -> list[EvidenceEntry]:
        return list(self._entries.get(submission_id, []))


evidence_ledger = EvidenceLedger()
