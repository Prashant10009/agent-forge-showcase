"""Atomic JSON checkpoints for public examples and local experimentation."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import RLock
from typing import Any


class JsonCheckpointStore:
    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self._lock = RLock()

    def save(self, checkpoint_id: str, payload: dict[str, Any]) -> Path:
        target = self._target(checkpoint_id)
        with self._lock:
            self.directory.mkdir(parents=True, exist_ok=True)
            with NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.directory,
                prefix=f".{checkpoint_id}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
                handle.write("\n")
                temporary = Path(handle.name)
            os.replace(temporary, target)
        return target

    def load(self, checkpoint_id: str) -> dict[str, Any] | None:
        target = self._target(checkpoint_id)
        with self._lock:
            if not target.exists():
                return None
            return json.loads(target.read_text(encoding="utf-8"))

    def _target(self, checkpoint_id: str) -> Path:
        if not checkpoint_id or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for character in checkpoint_id):
            raise ValueError("checkpoint_id may contain only letters, digits, hyphen, and underscore")
        return self.directory / f"{checkpoint_id}.json"
