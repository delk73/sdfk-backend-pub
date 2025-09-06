from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import PatchStorageBackend


class JsonLinesPatchStorage(PatchStorageBackend):
    """Append patches to JSONL files under a date-based directory."""

    def __init__(self, base_dir: str | Path = "bronze/patches") -> None:
        self.base_dir = Path(base_dir)

    def put(self, patch_id: str, component_type: str, patch: dict[str, Any]) -> str:
        date_dir = self.base_dir / f"dt={datetime.utcnow().date()}"
        date_dir.mkdir(parents=True, exist_ok=True)
        file_path = date_dir / f"component={component_type}.jsonl"
        record = {
            "patch_id": patch_id,
            "component_type": component_type,
            "patch": patch,
        }
        with file_path.open("a", encoding="utf-8") as f:
            json.dump(record, f)
            f.write("\n")
        return file_path.resolve().as_uri()

    def get(self, patch_id: str) -> dict[str, Any]:
        if not self.base_dir.exists():
            raise KeyError(patch_id)
        for file in self.base_dir.rglob("component=*.jsonl"):
            with file.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if record.get("patch_id") == patch_id:
                        return record["patch"]
        raise KeyError(patch_id)
