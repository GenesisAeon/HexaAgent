"""AgentLoop — der AI-UI-AI rekursive Event-Loop.

Dies ist KEIN Request-Response-System.
Dies IST ein kontinuierliches Zustands-Kopplungs-System.

Alle Verhalten sind deterministisch und replaybar (via ReplayEngine).
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from .agents import CoordinatorAgent, PhilosophyAgent, TransformAgent, UIAgent
from .policy import PolicyEngine
from .q4 import Q4State

logger = logging.getLogger(__name__)

AGENT_TARGETS = {
    "loop_latency_ms": (100, 50),
    "state_consistency": (True, None),
    "replay_fidelity": (True, None),
    "gray_policy_enforced": (True, None),
    "deterministic_output": (True, None),
}


@dataclass
class AgentLoopConfig:
    roles: list[str] = field(default_factory=lambda: ["coordinator", "transform", "philosophy", "ui"])
    initial_state_id: int = 0
    nats_url: str = "nats://localhost:4222"
    # Simuliertes NATS wenn kein echter Server verfügbar
    mock_nats: bool = True


class AgentLoop:
    """Der AI-UI-AI rekursive Loop.

    Kontinuierlich laufende Event-Loop:
      1. Subscribe auf NATS-Streams
      2. Q4-Zustandsupdate empfangen
      3. Internes Modell aktualisieren
      4. Response generieren (Sigillin, UI-Update, normative Evaluierung)
      5. Zurück auf NATS publizieren
      6. → WEITER mit 1.

    Alle Verhalten sind deterministisch und replaybar.
    """

    def __init__(self, config: AgentLoopConfig | None = None) -> None:
        self.config = config or AgentLoopConfig()
        self._event_queue: asyncio.Queue[tuple[str, dict]] = asyncio.Queue()
        self._running = False

        self.policy = PolicyEngine()
        publish_fn = self._enqueue_publish if self.config.mock_nats else None

        initial = Q4State.from_id(self.config.initial_state_id)
        self.coordinator = CoordinatorAgent(self.policy, publish_fn, initial)
        self.transform = TransformAgent(self.policy, publish_fn)
        self.philosophy = PhilosophyAgent(self.policy, publish_fn)
        self.ui = UIAgent(self.policy, publish_fn)

        active_agents = {
            "coordinator": self.coordinator,
            "transform": self.transform,
            "philosophy": self.philosophy,
            "ui": self.ui,
        }
        for role in self.config.roles:
            if role != "coordinator" and role in active_agents:
                self.coordinator.register_agent(active_agents[role])

    async def _enqueue_publish(self, subject: str, payload: dict) -> None:
        await self._event_queue.put((subject, payload))

    async def start(self) -> None:
        """Startet den kontinuierlichen Event-Loop."""
        self._running = True
        logger.info("AgentLoop gestartet. Rollen: %s", self.config.roles)
        await self._run_loop()

    async def stop(self) -> None:
        self._running = False
        logger.info("AgentLoop gestoppt.")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                subject, payload = await asyncio.wait_for(
                    self._event_queue.get(), timeout=0.1
                )
                await self._dispatch(subject, payload)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error("Loop-Fehler: %s", e)

    async def _dispatch(self, subject: str, payload: dict) -> None:
        logger.debug("Dispatch: %s", subject)

    async def inject_crep(self, crep_values: dict[str, float]) -> Q4State | None:
        """Injiziert CREP-Werte und löst ggf. Zustandsübergang aus.

        Gibt den neuen Q4-Zustand zurück wenn ein Übergang stattfand.
        """
        await self.transform.update_crep(crep_values)

        thresholds = self.transform.crep_thresholds
        new_state = Q4State(
            C=1 if crep_values.get("C", 0) >= thresholds["C"] else 0,
            R=1 if crep_values.get("R", 0) >= thresholds["R"] else 0,
            E=1 if crep_values.get("E", 0) >= thresholds["E"] else 0,
            P=1 if crep_values.get("P", 0) >= thresholds["P"] else 0,
        )

        current = self.coordinator.current_state
        if current is None or current.id == new_state.id:
            return None

        success = await self.coordinator.transition_to(new_state)
        return new_state if success else None

    async def replay(self, sigillin_id: str) -> list[dict]:
        """Replayed Trajektorie ab einem Sigillin-Snapshot."""
        snaps = self.coordinator.memory.replay_from(sigillin_id)
        result = [s.to_dict() for s in snaps]
        logger.info("Replay ab %s: %d Snapshots", sigillin_id, len(result))
        return result

    def status(self) -> dict:
        return {
            "running": self._running,
            "current_state": (
                self.coordinator.current_state.binary
                if self.coordinator.current_state
                else None
            ),
            "roles": self.config.roles,
            "policy_audit_count": len(self.policy.audit_log()),
            "coordinator_memory": len(self.coordinator.memory.trajectory()),
        }


class ReplayEngine:
    """Replayed gespeicherte Sigillin-Trajektorien deterministisch."""

    def __init__(self, loop: AgentLoop) -> None:
        self.loop = loop

    async def replay_from_sigillin(self, sigillin_id: str) -> list[dict]:
        return await self.loop.replay(sigillin_id)

    def verify_determinism(self, run1: list[dict], run2: list[dict]) -> bool:
        """Prüft ob zwei Replay-Läufe identische Trajektorien ergeben."""
        if len(run1) != len(run2):
            return False
        for a, b in zip(run1, run2):
            if a.get("q4_state") != b.get("q4_state"):
                return False
        return True
