"""AgentMemory — persistentes Agent-Gedächtnis via Sigillin-Lineage.

Agenten erinnern nicht nur Fakten, sondern Zustands-Trajektorien.
Memory = Sequenz von Sigillin-Snapshots mit Übergängen.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Sigillin:
    """Semantischer Zustandsanker mit deterministischer ID (SHA256).

    id wird aus dem Inhalt berechnet: gleicher Inhalt → gleiche ID.
    """

    symbolic_identity: str
    q4_binary: str
    q4_id: int
    crep_values: dict[str, float]
    narrative_context: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    semantic_lineage: list[str] = field(default_factory=list)
    id: str = field(init=False)

    def __post_init__(self) -> None:
        self.id = self._compute_id()

    def _compute_id(self) -> str:
        content = {
            "symbolic_identity": self.symbolic_identity,
            "q4_binary": self.q4_binary,
            "q4_id": self.q4_id,
            "crep_values": self.crep_values,
            "narrative_context": self.narrative_context,
            "timestamp": self.timestamp,
            "semantic_lineage": self.semantic_lineage,
        }
        raw = json.dumps(content, sort_keys=True, ensure_ascii=False).encode()
        return "sig_" + hashlib.sha256(raw).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": "1.0.0",
            "timestamp": self.timestamp,
            "symbolic_identity": self.symbolic_identity,
            "q4_state": {"binary": self.q4_binary, "id": self.q4_id},
            "crep_values": self.crep_values,
            "narrative_context": self.narrative_context,
            "semantic_lineage": self.semantic_lineage,
        }


@dataclass
class AgentMemory:
    """Persistentes Gedächtnis: Sequenz von Sigillin-Snapshots.

    Ermöglicht Replay und Lineage-Traversal.
    """

    agent_id: str
    _snapshots: list[Sigillin] = field(default_factory=list)

    def record(
        self,
        symbolic_identity: str,
        q4_binary: str,
        q4_id: int,
        crep_values: dict[str, float],
        narrative_context: str = "",
    ) -> Sigillin:
        """Speichert einen neuen Zustandsanker und verknüpft mit Lineage."""
        lineage = [self._snapshots[-1].id] if self._snapshots else []
        snap = Sigillin(
            symbolic_identity=symbolic_identity,
            q4_binary=q4_binary,
            q4_id=q4_id,
            crep_values=crep_values,
            narrative_context=narrative_context,
            semantic_lineage=lineage,
        )
        self._snapshots.append(snap)
        return snap

    def latest(self) -> Sigillin | None:
        return self._snapshots[-1] if self._snapshots else None

    def trajectory(self) -> list[Sigillin]:
        return list(self._snapshots)

    def get_by_id(self, sigillin_id: str) -> Sigillin | None:
        for snap in self._snapshots:
            if snap.id == sigillin_id:
                return snap
        return None

    def replay_from(self, sigillin_id: str) -> list[Sigillin]:
        """Gibt alle Snapshots ab dem angegebenen Sigillin zurück."""
        for i, snap in enumerate(self._snapshots):
            if snap.id == sigillin_id:
                return list(self._snapshots[i:])
        return []

    def export(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self._snapshots]
