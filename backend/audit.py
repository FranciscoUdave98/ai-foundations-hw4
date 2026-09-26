"""Append-only audit trail of agent-loop activity: output/audit_trail.json.

The file is always a valid JSON array. New entries are appended (only the closing "]" is
rewritten), existing entries are never changed or deleted, and each entry carries the SHA-256
of the previous one ("prev_hash" -> "hash"), so any edit to history breaks the chain and shows
up in verify(). Entries hold short summaries only: no message text, names, emails, or tokens.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_PATH = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"
MAX_TEXT = 160

_lock = threading.Lock()
_state: dict[str, Any] = {"seq": None, "hash": None}


def _short(value: Any) -> Any:
    """Keep entries small: truncate long strings and lists, recurse into dicts."""
    if isinstance(value, str):
        return value if len(value) <= MAX_TEXT else value[: MAX_TEXT - 1] + "…"
    if isinstance(value, dict):
        return {k: _short(v) for k, v in value.items() if v not in (None, "", [], {})}
    if isinstance(value, (list, tuple)):
        items = [_short(v) for v in value[:8]]
        return items + [f"… +{len(value) - 8} more"] if len(value) > 8 else items
    return value


def _load_tail(path: Path) -> None:
    if _state["seq"] is not None:
        return
    if path.exists() and path.stat().st_size > 2:
        entries = json.loads(path.read_text(encoding="utf-8"))
        last = entries[-1] if entries else {}
        _state.update(seq=last.get("seq", 0), hash=last.get("hash", "GENESIS"))
    else:
        _state.update(seq=0, hash="GENESIS")


def append(event: str, *, run_id: str, tool: str | None = None, args: Any = None, result: Any = None,
           reason: str | None = None, path: Path = AUDIT_PATH, **extra: Any) -> dict:
    """Append one entry (thread-safe). Returns the entry as written."""
    with _lock:
        _load_tail(path)
        entry = {
            "seq": _state["seq"] + 1,
            "time": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "run_id": run_id,
            "event": event,
            "tool": tool,
            "args": _short(args),
            "result": _short(result),
            "reason": _short(reason),
            **{k: _short(v) for k, v in extra.items()},
            "prev_hash": _state["hash"],
        }
        entry = {k: v for k, v in entry.items() if v not in (None, "", [], {})}
        entry["hash"] = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()
        line = json.dumps(entry, ensure_ascii=False)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.stat().st_size <= 2:
            path.write_text("[\n" + line + "\n]\n", encoding="utf-8")
        else:
            with open(path, "rb+") as f:  # rewrite only the final "]"
                f.seek(0, 2)
                end = f.tell()
                back = min(end, 16)
                f.seek(end - back)
                tail = f.read(back)
                cut = end - back + tail.rindex(b"]")
                f.seek(cut)
                f.truncate()
                f.write((",\n" + line + "\n]\n").encode("utf-8"))
        _state.update(seq=entry["seq"], hash=entry["hash"])
        return entry


def verify(path: Path = AUDIT_PATH) -> tuple[bool, int]:
    """Re-check the hash chain. Returns (ok, number of entries)."""
    entries = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    prev = "GENESIS"
    for e in entries:
        body = {k: v for k, v in e.items() if k != "hash"}
        if e.get("prev_hash") != prev or hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest() != e.get("hash"):
            return False, len(entries)
        prev = e["hash"]
    return True, len(entries)


class AuditRun:
    """Audit helper for one chat turn: every entry shares the same run_id."""

    def __init__(self, path: Path = AUDIT_PATH):
        self.run_id = "run_" + secrets.token_hex(4)
        self.path = path

    def __call__(self, event: str, **fields: Any) -> None:
        try:
            append(event, run_id=self.run_id, path=self.path, **fields)
        except Exception:  # auditing must never break a shopper's chat
            pass
