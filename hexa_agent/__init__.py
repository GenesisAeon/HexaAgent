"""HexaAgent — Agent-Infrastruktur für den AI-UI-AI Loop.

Phase 6 der GenesisAeon Integrations-Roadmap.
Implementiert: CoordinatorAgent, TransformAgent, PhilosophyAgent, UIAgent,
               AgentLoop, AgentMemory, PolicyEngine.
"""
from .agents import CoordinatorAgent, PhilosophyAgent, TransformAgent, UIAgent
from .loop import AgentLoop, AgentLoopConfig, ReplayEngine
from .memory import AgentMemory, Sigillin
from .policy import InvalidTransitionError, PolicyEngine
from .q4 import GrayCode, Q4State
from .runtime_contract import auto_config, config_from_runtime_contract, load_runtime_contract

__version__ = "0.1.0"

__all__ = [
    "Q4State",
    "GrayCode",
    "PolicyEngine",
    "InvalidTransitionError",
    "AgentMemory",
    "Sigillin",
    "CoordinatorAgent",
    "TransformAgent",
    "PhilosophyAgent",
    "UIAgent",
    "AgentLoop",
    "AgentLoopConfig",
    "ReplayEngine",
    "load_runtime_contract",
    "config_from_runtime_contract",
    "auto_config",
]
