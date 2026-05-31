"""CoordinatorAgent — verwaltet NATS-Verbindungen und globalen Q4-Zustand.

Einziger Agent der auf ga.frame.* publizieren darf.
Routet alle eingehenden Events zu spezialisierten Agenten.
Erhält Q4-Zustandskonsistenz aufrecht.
"""
from __future__ import annotations

import logging
from typing import Any

from ..policy import InvalidTransitionError, PolicyEngine
from ..q4 import Q4State
from .base import BaseAgent

logger = logging.getLogger(__name__)

FRAME_SUBJECT_PREFIX = "ga.frame."
AGENT_SUBJECT_PREFIX = "ga.agent."
HEALTH_SUBJECT = "ga.system.health"


class CoordinatorAgent(BaseAgent):
    """Verwaltet den globalen Q4-Zustand und routet Events.

    Einzige Instanz die auf ga.frame.* publizieren darf.
    Alle anderen Agenten empfangen ihren Q4-Zustand vom Coordinator.
    """

    def __init__(
        self,
        policy: PolicyEngine,
        nats_publish_fn: Any | None = None,
        initial_state: Q4State | None = None,
    ) -> None:
        super().__init__("coordinator", policy, nats_publish_fn)
        self._current_state = initial_state or Q4State(0, 0, 0, 0)
        self._subscribers: list[BaseAgent] = []

    def register_agent(self, agent: BaseAgent) -> None:
        self._subscribers.append(agent)
        agent.update_state(self._current_state)

    async def transition_to(self, new_state: Q4State) -> bool:
        """Versucht einen Q4-Zustandsübergang. Gibt True bei Erfolg zurück."""
        try:
            self.policy.validate(self._current_state, new_state)
        except InvalidTransitionError as e:
            logger.warning("Coordinator: Übergang blockiert — %s", e)
            return False

        old_state = self._current_state
        self._current_state = new_state

        subject = f"{FRAME_SUBJECT_PREFIX}{new_state.binary}"
        payload = {
            "from": old_state.binary,
            "to": new_state.binary,
            "from_id": old_state.id,
            "to_id": new_state.id,
        }
        await self.publish(subject, payload)

        for agent in self._subscribers:
            agent.update_state(new_state)
            await agent.handle_event(subject, payload)

        self.memory.record(
            symbolic_identity=f"frame_{new_state.binary}",
            q4_binary=new_state.binary,
            q4_id=new_state.id,
            crep_values={},
            narrative_context=f"Übergang von {old_state.binary} zu {new_state.binary}",
        )
        return True

    async def handle_event(self, subject: str, payload: dict) -> None:
        if subject == HEALTH_SUBJECT:
            await self.publish(
                HEALTH_SUBJECT,
                {
                    "status": "ok",
                    "q4_state": self._current_state.binary,
                    "agent": self.role_id,
                },
            )

    async def broadcast_health(self) -> None:
        await self.publish(
            HEALTH_SUBJECT,
            {
                "status": "ok",
                "q4_state": self._current_state.binary,
                "subscribers": len(self._subscribers),
            },
        )
