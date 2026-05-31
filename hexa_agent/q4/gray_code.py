"""Gray-Code Utilities für Q4-Zustandsübergänge.

KERN-INVARIANTE:
  hamming_distance(gray(n), gray(n+1)) == 1  für alle n in 0..14
  → Sichert Einzelbit-Übergänge zwischen benachbarten Q4-Zuständen.
"""
from __future__ import annotations


class GrayCode:
    """Gray-Code Encoding/Decoding und Hamming-Distanz-Berechnung."""

    @staticmethod
    def encode(n: int) -> int:
        return n ^ (n >> 1)

    @staticmethod
    def decode(g: int) -> int:
        mask = g >> 1
        while mask:
            g ^= mask
            mask >>= 1
        return g

    @staticmethod
    def hamming_distance(a: int, b: int) -> int:
        return bin(a ^ b).count("1")

    @staticmethod
    def are_gray_neighbors(state_id_a: int, state_id_b: int) -> bool:
        """Prüft ob zwei Q4-Zustand-IDs direkte Tesserakt-Nachbarn sind.

        Nachbarschaft = direkter Hamming-Abstand = 1 (genau 1 Bit-Flip).
        Dies ist die Kanten-Relation des 4D-Hyperwürfels.
        """
        return GrayCode.hamming_distance(state_id_a, state_id_b) == 1

    @staticmethod
    def validate_sequence(states: list[int]) -> bool:
        """Alle aufeinanderfolgenden Zustände haben direkten Hamming-Abstand = 1."""
        return all(
            GrayCode.hamming_distance(states[i], states[i + 1]) == 1
            for i in range(len(states) - 1)
        )

    @staticmethod
    def shortest_path(from_id: int, to_id: int) -> list[int]:
        """Kürzester Pfad zwischen zwei Q4-Zuständen via BFS (1-Bit-Schritte)."""
        if from_id == to_id:
            return [from_id]
        from collections import deque

        visited: dict[int, list[int]] = {from_id: [from_id]}
        queue: deque[int] = deque([from_id])
        while queue:
            current = queue.popleft()
            for bit in range(4):
                neighbor = current ^ (1 << bit)
                if neighbor not in visited:
                    visited[neighbor] = visited[current] + [neighbor]
                    if neighbor == to_id:
                        return visited[neighbor]
                    queue.append(neighbor)
        return []
