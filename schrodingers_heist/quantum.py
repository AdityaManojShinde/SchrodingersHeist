"""Pure quantum functional operations for Schrödinger's Heist.

Adheres to functional programming principles: pure functions for circuit
synthesis, state evolution, projective measurement collapse, and probability math.
"""

from collections.abc import Sequence
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector


def apply_action_to_circuit(qc: QuantumCircuit, action: str) -> None:
    """Mutate a QuantumCircuit by appending the gate corresponding to action token."""
    if action == "wait":
        return
    if action.startswith("x"):
        qc.x(int(action[1]))
    elif action.startswith("h"):
        qc.h(int(action[1]))
    elif action.startswith("z"):
        qc.z(int(action[1]))
    elif action.startswith("cx"):
        qc.cx(int(action[2]), int(action[3]))
    else:
        raise ValueError(f"Unknown action token: '{action}'")


def create_action_circuit(n: int, action: str) -> QuantumCircuit:
    """Pure factory function returning a new QuantumCircuit for a single action."""
    qc = QuantumCircuit(n)
    apply_action_to_circuit(qc, action)
    return qc


def evolve_state(state: Statevector, action: str, n: int) -> Statevector:
    """Pure functional state evolution under a quantum gate action."""
    qc = create_action_circuit(n, action)
    return state.evolve(qc)


def calculate_room_probabilities(state: Statevector) -> list[float]:
    """Compute exact measurement probabilities across all basis rooms."""
    return [float(p) for p in state.probabilities()]


def calculate_caught_probability(state: Statevector, guarded_rooms: Sequence[int]) -> float:
    """Compute total detection probability over a set of guarded rooms."""
    probs = state.probabilities()
    return float(sum(probs[r] for r in guarded_rooms))


def project_state_onto_rooms(state: Statevector, rooms: Sequence[int]) -> Statevector:
    """Project wavefunction onto a target room subspace and renormalize."""
    data = np.zeros_like(state.data)
    for r in rooms:
        data[r] = state.data[r]
    norm = np.linalg.norm(data)
    if norm > 0:
        data = data / norm
    return Statevector(data)


def project_state_complement(state: Statevector, rooms: Sequence[int]) -> Statevector:
    """Interaction-free measurement: project onto complement of rooms and renormalize."""
    data = np.copy(state.data)
    for r in rooms:
        data[r] = 0.0 + 0.0j
    norm = np.linalg.norm(data)
    if norm > 0:
        data = data / norm
    return Statevector(data)

