"""Functional zero-risk quantum solver for Schrödinger's Heist.

Uses pruned depth-first search (DFS) over unitary state evolutions to discover
all zero-risk solutions for levels 1 to 4.
"""

from qiskit.quantum_info import Statevector
from .models import Level
from .quantum import calculate_caught_probability, evolve_state


def find_zero_risk_solutions(level: Level) -> list[list[str]]:
    """Pure functional DFS solver returning all zero-risk solutions for a level.

    Abandons a search branch as soon as a guard check encounters p_caught > 1e-9.
    """
    solutions: list[list[str]] = []

    def dfs(step: int, current_state: Statevector, path: list[str]) -> None:
        if step == level.T:
            if abs(current_state.data[level.vault]) ** 2 >= 1.0 - 1e-9:
                solutions.append(list(path))
            return

        guarded_rooms = level.guards[step]
        for action in level.toolbox:
            nxt_state = evolve_state(current_state, action, level.n)
            p_caught = calculate_caught_probability(nxt_state, guarded_rooms)
            if p_caught > 1e-9:
                continue
            dfs(step + 1, nxt_state, path + [action])

    initial_state = Statevector.from_int(0, 2**level.n)
    dfs(0, initial_state, [])
    return solutions

