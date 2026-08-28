"""Local filesystem storage for raw .eml email files."""
from __future__ import annotations

from pathlib import Path

from app.core.config import settings


def save_eml(content: bytes, submission_id: str) -> str:
    """Write raw .eml bytes to disk. Returns the absolute file path (storage_ref)."""
    storage_dir = Path(settings.storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    file_path = storage_dir / f"{submission_id}.eml"
    file_path.write_bytes(content)
    return str(file_path)


def read_eml(storage_ref: str) -> bytes:
    """Read raw .eml bytes from disk."""
    return Path(storage_ref).read_bytes()


def delete_eml(storage_ref: str) -> None:
    """Delete a stored .eml file (e.g., after retention period expires)."""
    path = Path(storage_ref)
    if path.exists():
        path.unlink()
