"""PhilosophyAgent — bewertet CREP-Zustände gegen ethische/governance Metriken.

Greift auf Worldview + Gemeinwohl-Repos zu.
Kann Zustandsübergänge via PolicyEngine vetoisieren.
Publiziert auf ga.agent.philosophy.*.
"""
from __future__ import annotations

import logging
from typing import Any

from ..policy import PolicyEngine
from ..q4 import Q4State
from .base import BaseAgent

logger = logging.getLogger(__name__)

PHILOSOPHY_SUBJECT = "ga.agent.philosophy"
FRAME_SUBJECT_PREFIX = "ga.frame."


# Governance-Regel: Callback-Typ
GovernanzeRule = Any  # Callable[[Q4State, Q4State], str | None]


class PhilosophyAgent(BaseAgent):
    """Bewertet Übergänge gegen ethische Governance-Metriken.

    Registriert Veto-Funktionen beim PolicyEngine. Wenn ein Übergang
    Gemeinwohl-Kriterien verletzt, wird er via PolicyEngine blockiert.

    Verarbeitet utac_state (H, H_star, K_eff) zur normativen Bewertung.
    """

    # PHI_APPROX = 1.6  # Engineering-Näherung, NICHT exakt Φ = 1.6180339...
    PHI_APPROX: float = 1.6

    def __init__(
        self,
        policy: PolicyEngine,
        nats_publish_fn: Any | None = None,
        min_coherence_for_transition: float = 0.3,
    ) -> None:
        super().__init__("philosophy", policy, nats_publish_fn)
        self.min_coherence = min_coherence_for_transition
        self._utac: dict[str, float] = {}
        # Registriert Gemeinwohl-Veto beim PolicyEngine
        policy.register_veto(self._gemeinwohl_veto)

    def _gemeinwohl_veto(self, from_state: Q4State, to_state: Q4State) -> str | None:
        """Vetoisiert Übergänge die Gemeinwohl verletzen.

        Aktuell: Blokkiert jeden Übergang in Zustand 0 (quiescent)
        wenn aktuelle Kohärenz (H) zu hoch ist (System verliert Kohärenz).
        """
        if to_state.id == 0 and self._utac.get("H", 1.0) > 0.8:
            return (
                f"Gemeinwohl-Veto: Übergang zu quiescentem Zustand bei H={self._utac.get('H')} > 0.8"
            )
        return None

    def update_utac(self, utac_state: dict[str, float]) -> None:
        """Aktualisiert UTAC-Metriken (H, H_star, K_eff)."""
        self._utac = utac_state

    async def handle_event(self, subject: str, payload: dict) -> None:
        if subject.startswith(FRAME_SUBJECT_PREFIX):
            await self._evaluate_transition(payload)

    async def _evaluate_transition(self, payload: dict) -> None:
        evaluation = {
            "from": payload.get("from"),
            "to": payload.get("to"),
            "utac": self._utac,
            "phi_approx": self.PHI_APPROX,
            "approved": True,
        }
        await self.publish(PHILOSOPHY_SUBJECT, evaluation)
        logger.info("PhilosophyAgent: Übergang %s → %s evaluiert", payload.get("from"), payload.get("to"))
