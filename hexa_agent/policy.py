"""PolicyEngine — steuert welche Q4-Zustandsübergänge Agenten initiieren dürfen.

Umhüllt Gray-Code-Validierung + domänenspezifische Regeln.
PhilosophyAgent kann Übergänge vetoisieren.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable

from .q4 import GrayCode, Q4State

logger = logging.getLogger(__name__)


class InvalidTransitionError(Exception):
    """Wird ausgelöst wenn ein ungültiger Q4-Zustandsübergang versucht wird."""

    def __init__(self, from_state: Q4State, to_state: Q4State, reason: str = "") -> None:
        self.from_state = from_state
        self.to_state = to_state
        self.reason = reason
        super().__init__(
            f"Ungültiger Übergang {from_state.binary} → {to_state.binary}"
            + (f": {reason}" if reason else "")
        )


# Veto-Funktion: nimmt (from_state, to_state) und gibt optionalen Veto-Grund zurück
VetoFn = Callable[[Q4State, Q4State], str | None]


@dataclass
class PolicyEngine:
    """Erzwingt Gray-Code Policy Gate und optionale domänenspezifische Regeln.

    Kern-Invariante: Nur Übergänge mit Hamming-Distanz = 1 (Gray-Code-Nachbarn)
    sind erlaubt. Alle anderen lösen InvalidTransitionError aus.
    """

    _veto_fns: list[VetoFn] = field(default_factory=list)
    _audit_log: list[dict] = field(default_factory=list)

    def register_veto(self, fn: VetoFn) -> None:
        """Registriert eine Veto-Funktion (z.B. vom PhilosophyAgent)."""
        self._veto_fns.append(fn)

    def is_valid(self, from_state: Q4State, to_state: Q4State) -> bool:
        """Gibt True zurück wenn der Übergang erlaubt ist."""
        if not GrayCode.are_gray_neighbors(from_state.id, to_state.id):
            return False
        for veto_fn in self._veto_fns:
            if veto_fn(from_state, to_state) is not None:
                return False
        return True

    def validate(self, from_state: Q4State, to_state: Q4State) -> None:
        """Wirft InvalidTransitionError wenn der Übergang nicht erlaubt ist."""
        if not GrayCode.are_gray_neighbors(from_state.id, to_state.id):
            reason = (
                f"Hamming-Distanz = "
                f"{GrayCode.hamming_distance(GrayCode.encode(from_state.id), GrayCode.encode(to_state.id))} "
                f"(muss = 1 sein)"
            )
            self._audit(from_state, to_state, "BLOCKED_GRAY", reason)
            raise InvalidTransitionError(from_state, to_state, reason)
        for veto_fn in self._veto_fns:
            reason = veto_fn(from_state, to_state)
            if reason is not None:
                self._audit(from_state, to_state, "BLOCKED_VETO", reason)
                raise InvalidTransitionError(from_state, to_state, reason)
        self._audit(from_state, to_state, "ALLOWED", "")
        logger.debug("Übergang erlaubt: %s → %s", from_state.binary, to_state.binary)

    def suggest_path(self, from_state: Q4State, to_state: Q4State) -> list[Q4State]:
        """Schlägt einen gültigen Gray-Code-Pfad vor."""
        ids = GrayCode.shortest_path(from_state.id, to_state.id)
        return [Q4State.from_id(i) for i in ids]

    def audit_log(self) -> list[dict]:
        return list(self._audit_log)

    def _audit(self, from_state: Q4State, to_state: Q4State, result: str, reason: str) -> None:
        entry = {
            "from": from_state.binary,
            "to": to_state.binary,
            "result": result,
            "reason": reason,
        }
        self._audit_log.append(entry)
        logger.info("PolicyGate %s: %s → %s %s", result, from_state.binary, to_state.binary, reason)
