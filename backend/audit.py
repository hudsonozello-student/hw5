"""Append-only audit trail: every agent-loop step becomes one event in output/audit_trail.json."""

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.config import AUDIT_TEXT_LIMIT
from backend.models import AuditEvent, AuditEventType, TeamDeps


def _clip(value: Any) -> Any:
    """Keep long strings readable in the trail without dropping structure."""
    if isinstance(value, str) and len(value) > AUDIT_TEXT_LIMIT:
        return value[:AUDIT_TEXT_LIMIT] + f"... [clipped {len(value) - AUDIT_TEXT_LIMIT} chars]"
    if isinstance(value, dict):
        return {k: _clip(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clip(v) for v in value]
    return value


class AuditTrail:
    """A JSON array on disk that only ever grows. Existing events are never rewritten or removed."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    def _load(self) -> list:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return []
        events = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(events, list):
            raise ValueError(f"{self.path} is not a JSON array; refusing to overwrite it.")
        return events

    def write(self, event: AuditEvent) -> None:
        with self._lock:
            events = self._load()
            events.append(_clip(event.model_dump(mode="json")))
            tmp = self.path.with_suffix(".json.tmp")
            tmp.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_text(json.dumps(events, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
            os.replace(tmp, self.path)

    def log(self, deps: TeamDeps, event: AuditEventType, data: dict[str, Any] | None = None,
            *, step: int = 0, model: str | None = None) -> None:
        self.write(AuditEvent(
            ts=_now(), run_id=deps.run_id, ticket_id=deps.ticket_id, agent=deps.agent, chain=list(deps.chain),
            depth=deps.depth, step=step, event=event, model=model, data=data or {},
        ))

    def log_human(self, who: str, event: AuditEventType, data: dict[str, Any], ticket_id: int | None = None) -> None:
        """Events a person caused (approvals, rejections, resets), outside any agent run."""
        self.write(AuditEvent(
            ts=_now(), run_id=f"desk-{uuid.uuid4().hex[:8]}", ticket_id=ticket_id, agent=f"human:{who}",
            chain=[], depth=0, step=0, event=event, data=data,
        ))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")
