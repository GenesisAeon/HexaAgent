"""BaseAgent — abstrakte Basisklasse für alle HexaAgent-Rollen."""
from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

from ..memory import AgentMemory
from ..policy import PolicyEngine
from ..q4 import Q4State

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstrakte Basisklasse aller Agent-Rollen.

    Jeder Agent hat:
      - Eine eindeutige role_id
      - Zugang zum PolicyEngine (read-only für nicht-Coordinator)
      - Eigenes AgentMemory
      - NATS-publish-Methode (Mock oder echte Implementierung)
    """

    def __init__(
        self,
        role_id: str,
        policy: PolicyEngine,
        nats_publish_fn: Any | None = None,
    ) -> None:
        self.role_id = role_id
        self.policy = policy
        self.memory = AgentMemory(agent_id=role_id)
        self._publish = nats_publish_fn
        self._current_state: Q4State | None = None
        self._running = False

    @abstractmethod
    async def handle_event(self, subject: str, payload: dict) -> None:
        """Verarbeitet ein eingehendes NATS-Event."""

    async def publish(self, subject: str, payload: dict) -> None:
        if self._publish is not None:
            await self._publish(subject, payload)
        else:
            logger.debug("[%s] PUBLISH %s: %s", self.role_id, subject, payload)

    def update_state(self, new_state: Q4State) -> None:
        self._current_state = new_state

    @property
    def current_state(self) -> Q4State | None:
        return self._current_state
