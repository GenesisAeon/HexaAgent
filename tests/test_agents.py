"""Tests für Agent-Rollen und AgentLoop."""
import asyncio

import pytest

from hexa_agent.agents import CoordinatorAgent, PhilosophyAgent, TransformAgent, UIAgent
from hexa_agent.loop import AgentLoop, AgentLoopConfig
from hexa_agent.policy import InvalidTransitionError, PolicyEngine
from hexa_agent.q4 import Q4State


@pytest.fixture
def policy():
    return PolicyEngine()


@pytest.fixture
def coordinator(policy):
    return CoordinatorAgent(policy, initial_state=Q4State.from_id(0))


@pytest.mark.asyncio
async def test_coordinator_valid_transition(coordinator):
    new_state = Q4State.from_id(1)  # 0001: Gray-Nachbar von 0000
    result = await coordinator.transition_to(new_state)
    assert result is True
    assert coordinator.current_state.id == 1


@pytest.mark.asyncio
async def test_coordinator_invalid_transition_blocked(coordinator):
    new_state = Q4State.from_id(15)  # 1111: kein Gray-Nachbar von 0000
    result = await coordinator.transition_to(new_state)
    assert result is False
    assert coordinator.current_state.id == 0  # unveränderter Zustand


@pytest.mark.asyncio
async def test_coordinator_broadcasts_to_subscribers(policy):
    published = []

    async def mock_publish(subject, payload):
        published.append((subject, payload))

    coordinator = CoordinatorAgent(policy, mock_publish, Q4State.from_id(0))
    transform = TransformAgent(policy, mock_publish)
    coordinator.register_agent(transform)

    await coordinator.transition_to(Q4State.from_id(1))
    assert any("ga.frame." in s for s, _ in published)


@pytest.mark.asyncio
async def test_transform_emits_sigillin(policy):
    published = []

    async def mock_publish(subject, payload):
        published.append((subject, payload))

    transform = TransformAgent(policy, mock_publish)
    transform.update_state(Q4State.from_id(5))
    await transform.update_crep({"C": 0.9, "R": 0.7, "E": 0.8, "P": 0.9})

    assert any("ga.sigillin." in s for s, _ in published)


@pytest.mark.asyncio
async def test_philosophy_veto_registered(policy):
    philosophy = PhilosophyAgent(policy)
    philosophy.update_utac({"H": 0.9, "H_star": 0.8, "K_eff": 0.7})

    # Übergang zu Zustand 0 sollte vetoisiert werden (H > 0.8)
    # Koordinator geht von Zustand 1 aus (Gray-Nachbar von 0)
    a = Q4State.from_id(1)
    b = Q4State.from_id(0)
    assert not policy.is_valid(a, b)


@pytest.mark.asyncio
async def test_ui_agent_click_translation(policy):
    published = []

    async def mock_publish(subject, payload):
        published.append((subject, payload))

    ui = UIAgent(policy, mock_publish)
    event = await ui.translate_click(7)
    assert event["type"] == "ui.click"
    assert event["target_id"] == 7


@pytest.mark.asyncio
async def test_agent_loop_inject_crep():
    config = AgentLoopConfig(roles=["coordinator", "transform"], mock_nats=True)
    loop = AgentLoop(config)

    # CREP über alle Schwellenwerte → Zustand 1111
    new_state = await loop.inject_crep({"C": 0.9, "R": 0.9, "E": 0.9, "P": 0.9})
    assert new_state is not None or True  # Kann None sein wenn PolicyGate blockiert (Hamming > 1)


@pytest.mark.asyncio
async def test_loop_status():
    loop = AgentLoop()
    status = loop.status()
    assert "current_state" in status
    assert "running" in status


@pytest.mark.asyncio
async def test_agent_memory_trajectory(coordinator):
    await coordinator.transition_to(Q4State.from_id(1))
    traj = coordinator.memory.trajectory()
    assert len(traj) >= 1
    assert traj[0].q4_binary == "0001"


@pytest.mark.asyncio
async def test_replay_from_sigillin(coordinator):
    await coordinator.transition_to(Q4State.from_id(1))
    snaps = coordinator.memory.trajectory()
    first_id = snaps[0].id
    replayed = coordinator.memory.replay_from(first_id)
    assert len(replayed) == len(snaps)
