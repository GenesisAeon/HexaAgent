"""TransformAgent — generiert Sigillin-Snapshots aus CREP + Q4.

Verarbeitet: Feldtheorie, Kosmische Momente, Entropie-Governance.
Publiziert Sigillin-Events auf ga.sigillin.*.
"""
from __future__ import annotations

import logging
from typing import Any

from ..policy import PolicyEngine
from ..q4 import Q4State
from .base import BaseAgent

logger = logging.getLogger(__name__)

SIGILLIN_SUBJECT_PREFIX = "ga.sigillin."
FRAME_SUBJECT_PREFIX = "ga.frame."


class TransformAgent(BaseAgent):
    """Liest Q4-Zustand und generiert Sigillin-Snapshots.

    Publiziert auf ga.sigillin.* wenn signifikante Zustandsänderungen
    erkannt werden (Schwellenwert-Überschreitung in CREP-Metriken).
    """

    def __init__(
        self,
        policy: PolicyEngine,
        nats_publish_fn: Any | None = None,
        crep_thresholds: dict[str, float] | None = None,
    ) -> None:
        super().__init__("transform", policy, nats_publish_fn)
        self.crep_thresholds = crep_thresholds or {
            "C": 0.5,
            "R": 0.6,
            "E": 0.7,
            "P": 0.8,
        }
        self._last_crep: dict[str, float] = {}

    async def handle_event(self, subject: str, payload: dict) -> None:
        if subject.startswith(FRAME_SUBJECT_PREFIX):
            await self._on_frame_event(payload)

    async def update_crep(self, crep_values: dict[str, float]) -> None:
        """Aktualisiert CREP-Werte und erzeugt ggf. Sigillin."""
        self._last_crep = crep_values
        if self._current_state is not None:
            await self._emit_sigillin(crep_values)

    async def _on_frame_event(self, payload: dict) -> None:
        if self._last_crep:
            await self._emit_sigillin(self._last_crep)

    async def _emit_sigillin(self, crep_values: dict[str, float]) -> None:
        if self._current_state is None:
            return

        snap = self.memory.record(
            symbolic_identity=self._derive_identity(crep_values),
            q4_binary=self._current_state.binary,
            q4_id=self._current_state.id,
            crep_values=crep_values,
            narrative_context=f"CREP-Snapshot bei Q4={self._current_state.binary}",
        )

        subject = f"{SIGILLIN_SUBJECT_PREFIX}{snap.id}"
        await self.publish(subject, snap.to_dict())
        logger.info("TransformAgent: Sigillin %s publiziert", snap.id)

    def _derive_identity(self, crep: dict[str, float]) -> str:
        active = [dim for dim, val in crep.items() if val >= self.crep_thresholds.get(dim, 0.5)]
        if not active:
            return "quiescent"
        return "_".join(sorted(active)).lower()
