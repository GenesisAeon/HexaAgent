"""UIAgent — Brücke zwischen Human und Q4-System.

Liest ga.frame.* und ga.sigillin.* Streams.
Übersetzt User-Input (Text, Klicks) in Q4-Events.
"""
from __future__ import annotations

import logging
from typing import Any

from ..policy import PolicyEngine
from ..q4 import Q4State
from .base import BaseAgent

logger = logging.getLogger(__name__)

FRAME_SUBJECT_PREFIX = "ga.frame."
SIGILLIN_SUBJECT_PREFIX = "ga.sigillin."
UI_INPUT_SUBJECT = "ga.agent.ui.input"


class UIAgent(BaseAgent):
    """Liest Frame- und Sigillin-Streams, übersetzt Human-Input.

    Hält einen lokalen UI-State der die Mandala-Visualisierung treibt.
    """

    def __init__(
        self,
        policy: PolicyEngine,
        nats_publish_fn: Any | None = None,
    ) -> None:
        super().__init__("ui", policy, nats_publish_fn)
        self._frame_history: list[dict] = []
        self._sigillin_history: list[dict] = []
        self._on_state_change_cb: Any | None = None

    def on_state_change(self, callback: Any) -> None:
        """Registriert Callback für UI-Updates bei Zustandsänderung."""
        self._on_state_change_cb = callback

    async def handle_event(self, subject: str, payload: dict) -> None:
        if subject.startswith(FRAME_SUBJECT_PREFIX):
            self._frame_history.append(payload)
            if len(self._frame_history) > 64:
                self._frame_history.pop(0)
            if self._on_state_change_cb is not None:
                await self._on_state_change_cb(self._current_state, payload)
            logger.debug("UIAgent: Frame %s empfangen", subject)

        elif subject.startswith(SIGILLIN_SUBJECT_PREFIX):
            self._sigillin_history.append(payload)
            if len(self._sigillin_history) > 32:
                self._sigillin_history.pop(0)

    async def translate_click(self, target_state_id: int) -> dict:
        """Übersetzt einen UI-Klick auf eine Gray-Grid-Zelle in ein Q4-Event.

        Gibt ein Event-Dict zurück das der CoordinatorAgent verarbeiten kann.
        """
        target = Q4State.from_id(target_state_id)
        event = {
            "type": "ui.click",
            "target_state": target.binary,
            "target_id": target.id,
            "source": "graygrid",
        }
        await self.publish(UI_INPUT_SUBJECT, event)
        return event

    async def translate_text_input(self, text: str, crep_hint: dict[str, float] | None = None) -> dict:
        """Übersetzt Text-Input in ein semantisches Event."""
        event = {
            "type": "ui.text",
            "text": text,
            "crep_hint": crep_hint or {},
            "current_state": self._current_state.binary if self._current_state else "0000",
        }
        await self.publish(UI_INPUT_SUBJECT, event)
        return event

    def frame_history(self, n: int = 16) -> list[dict]:
        return self._frame_history[-n:]

    def sigillin_history(self, n: int = 8) -> list[dict]:
        return self._sigillin_history[-n:]
