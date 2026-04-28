from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def write_text_atomic(path: Path, text: str, encoding: str = "utf-8") -> None:
    """
    Atomically write a text file:
    - write to tmp file in same directory
    - flush + fsync
    - os.replace to target path
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            # Best-effort cleanup; atomicity already achieved or failed.
            pass


def write_json_atomic(path: Path, data: Any, *, ensure_ascii: bool = False, indent: int = 2) -> None:
    text = json.dumps(data, ensure_ascii=ensure_ascii, indent=indent, default=str)
    write_text_atomic(path, text + "\n")

