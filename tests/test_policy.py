"""Tests für PolicyEngine — Gray-Code Policy Gate."""
import pytest

from hexa_agent.policy import InvalidTransitionError, PolicyEngine
from hexa_agent.q4 import Q4State


@pytest.fixture
def policy():
    return PolicyEngine()


def test_valid_gray_neighbor(policy):
    # 0000 → 0001: Hamming = 1
    a = Q4State.from_id(0)
    b = Q4State.from_id(1)
    assert policy.is_valid(a, b)


def test_invalid_non_neighbor(policy):
    # 0000 → 1111: Hamming = 4
    a = Q4State.from_id(0)
    b = Q4State.from_id(15)
    assert not policy.is_valid(a, b)


def test_validate_raises_on_invalid(policy):
    a = Q4State.from_id(0)
    b = Q4State.from_id(15)
    with pytest.raises(InvalidTransitionError):
        policy.validate(a, b)


def test_validate_passes_for_neighbor(policy):
    a = Q4State.from_id(0)
    b = Q4State.from_id(1)
    policy.validate(a, b)  # kein Fehler


def test_veto_blocks_transition(policy):
    policy.register_veto(lambda f, t: "test-veto" if t.id == 1 else None)
    a = Q4State.from_id(0)
    b = Q4State.from_id(1)
    assert not policy.is_valid(a, b)


def test_veto_allows_other_transition(policy):
    policy.register_veto(lambda f, t: "veto" if t.id == 1 else None)
    a = Q4State.from_id(0)
    b = Q4State.from_id(8)  # 0000 → 1000: Hamming = 1
    assert policy.is_valid(a, b)


def test_suggest_path_gray_neighbors(policy):
    a = Q4State.from_id(0)
    b = Q4State.from_id(15)
    path = policy.suggest_path(a, b)
    assert path[0].id == 0
    assert path[-1].id == 15
    for i in range(len(path) - 1):
        assert policy.is_valid(path[i], path[i + 1])


def test_audit_log_records(policy):
    a = Q4State.from_id(0)
    b = Q4State.from_id(1)
    policy.validate(a, b)
    log = policy.audit_log()
    assert len(log) == 1
    assert log[0]["result"] == "ALLOWED"
