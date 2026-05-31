"""Tests für Q4State und GrayCode — Kern-Invarianten."""
import pytest

from hexa_agent.q4 import GrayCode, Q4State
from hexa_agent.q4.state import ALL_Q4_STATES, GRAY_ORDER


def test_state_count():
    assert len(ALL_Q4_STATES) == 16


def test_entropy_bits():
    for s in ALL_Q4_STATES:
        assert s.entropy_bits == 4.0


def test_id_range():
    ids = {s.id for s in ALL_Q4_STATES}
    assert ids == set(range(16))


def test_from_id_roundtrip():
    for i in range(16):
        s = Q4State.from_id(i)
        assert s.id == i


def test_binary_format():
    for s in ALL_Q4_STATES:
        assert len(s.binary) == 4
        assert all(c in "01" for c in s.binary)


def test_gray_hamming_invariant():
    """KERN-INVARIANTE: Hamming-Distanz aufeinanderfolgender Gray-Codes = 1."""
    for n in range(15):
        ga = GrayCode.encode(n)
        gb = GrayCode.encode(n + 1)
        dist = GrayCode.hamming_distance(ga, gb)
        assert dist == 1, f"Hamming-Distanz gray({n})={ga} → gray({n+1})={gb} ist {dist}, nicht 1"


def test_gray_encode_decode_roundtrip():
    for n in range(16):
        assert GrayCode.decode(GrayCode.encode(n)) == n


def test_gray_order_adjacency():
    """Alle benachbarten Zustände in GRAY_ORDER unterscheiden sich um genau 1 Bit."""
    assert GrayCode.validate_sequence(GRAY_ORDER)


def test_gray_order_length():
    assert len(GRAY_ORDER) == 16
    assert set(GRAY_ORDER) == set(range(16))


def test_shortest_path_same():
    path = GrayCode.shortest_path(0, 0)
    assert path == [0]


def test_shortest_path_neighbors():
    path = GrayCode.shortest_path(0, 1)
    assert len(path) == 2
    assert path[0] == 0
    assert path[-1] == 1


def test_shortest_path_validity():
    path = GrayCode.shortest_path(0, 15)
    assert path[0] == 0
    assert path[-1] == 15
    assert GrayCode.validate_sequence(path)


def test_invalid_state_raises():
    with pytest.raises(ValueError):
        Q4State(C=2, R=0, E=0, P=0)
