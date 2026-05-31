"""Q4State — lokale Implementierung bis genesis-q4-core auf PyPI verfügbar.

Mathematische Grundlage:
  16 Zustände = 4 Bit  (H = log₂(16) = 4 Bit)
  Gray-Code: g(n) = n XOR (n >> 1)
  Hamming-Distanz aufeinanderfolgender Gray-Codes: immer = 1
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class Q4State:
    """4-Bit Zustand im GenesisAeon Q4-Zustandsraum.

    Felder:
      C: Kohärenz-Flag  (0 oder 1)
      R: Resonanz-Flag  (0 oder 1)
      E: Emergenz-Flag  (0 oder 1)
      P: Poetik-Flag    (0 oder 1)

    INVARIANTE: 16 Zustände = 4 Bit. Nicht 16 Bit.
    """

    C: int
    R: int
    E: int
    P: int

    # Alle 16 gültigen Zustände (für Validierung)
    _VALID_BITS: ClassVar[frozenset[int]] = frozenset({0, 1})

    def __post_init__(self) -> None:
        for name, val in (("C", self.C), ("R", self.R), ("E", self.E), ("P", self.P)):
            if val not in self._VALID_BITS:
                raise ValueError(f"Q4State.{name} muss 0 oder 1 sein, nicht {val!r}")

    @property
    def id(self) -> int:
        return 8 * self.C + 4 * self.R + 2 * self.E + self.P

    @property
    def binary(self) -> str:
        return f"{self.id:04b}"

    @property
    def gray_id(self) -> int:
        n = self.id
        return n ^ (n >> 1)

    @property
    def entropy_bits(self) -> float:
        return 4.0  # log₂(16) = 4 Bit bei Gleichverteilung

    @classmethod
    def from_id(cls, state_id: int) -> "Q4State":
        if not 0 <= state_id <= 15:
            raise ValueError(f"Q4State-ID muss 0..15 sein, nicht {state_id}")
        return cls(
            C=(state_id >> 3) & 1,
            R=(state_id >> 2) & 1,
            E=(state_id >> 1) & 1,
            P=state_id & 1,
        )

    def __repr__(self) -> str:
        return (
            f"Q4State(C={self.C}, R={self.R}, E={self.E}, P={self.P} "
            f"| id={self.id}, binary={self.binary})"
        )


# Alle 16 kanonischen Zustände
ALL_Q4_STATES: list[Q4State] = [Q4State.from_id(i) for i in range(16)]

# Gray-Code-Traversal-Reihenfolge (Hamming-Distanz zwischen Nachbarn = 1)
GRAY_ORDER: list[int] = [0, 1, 3, 2, 6, 7, 5, 4, 12, 13, 15, 14, 10, 11, 9, 8]
