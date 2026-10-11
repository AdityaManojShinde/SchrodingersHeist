"""Game state and rules engine for Schrödinger's Heist.

Encapsulates thief state, guard check measurements, interaction-free collapse,
and victory/failure conditions according to OOP principles.
"""

import math
import random
from typing import Optional
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from .models import Level, MissionRating
from .quantum import (
    apply_action_to_circuit,
    calculate_caught_probability,
    evolve_state,
    project_state_complement,
    project_state_onto_rooms,
)


class GameState:
    """Manages the lifecycle, quantum state, and measurement history of a heist."""

    def __init__(self, level: Level, rng: Optional[random.Random] = None) -> None:
        self.level = level
        self.rng = rng if rng is not None else random.Random()
        self.tick = 0
        self.state = Statevector.from_int(0, 2**level.n)
        self.circuit = QuantumCircuit(level.n)
        self.history_actions: list[str] = []
        self.history_states: list[Statevector] = [self.state.copy()]
        self.history_p_caught: list[float] = []
        self.is_caught = False
        self.caught_room: Optional[int] = None
        self.won = False
        self.failed = False
        self.fail_reason = ""
        self.last_check_msg = ""

    def apply_action(self, action: str) -> None:
        """Apply player action and evolve quantum statevector."""
        if self.failed or self.won:
            return
        if action not in self.level.toolbox:
            raise ValueError(f"Action '{action}' is not in level toolbox: {self.level.toolbox}")

        # State evolution
        self.state = evolve_state(self.state, action, self.level.n)
        apply_action_to_circuit(self.circuit, action)
        self.history_actions.append(action)
        self.tick += 1

        self._run_guard_check()

    def _run_guard_check(self) -> None:
        """Execute the measurement rule for the current tick."""
        guarded_rooms = self.level.guards[self.tick - 1]
        p_caught = calculate_caught_probability(self.state, guarded_rooms)
        self.history_p_caught.append(p_caught)

        if p_caught < 1e-9:
            self.last_check_msg = "Guards detected no presence (p_caught < 1e-9). Wavefunction unaffected."
            self.history_states.append(self.state.copy())
            self._check_final_loot()
            return

        # Sample catch event with probability p_caught
        caught = self.rng.random() < p_caught
        if caught:
            self.is_caught = True
            self.failed = True
            probs = self.state.probabilities()
            g_weights = [probs[r] for r in guarded_rooms]
            sum_w = sum(g_weights)
            self.caught_room = (
                self.rng.choices(guarded_rooms, weights=g_weights)[0]
                if sum_w > 0
                else guarded_rooms[0]
            )

            # Project onto G and renormalize
            self.state = project_state_onto_rooms(self.state, guarded_rooms)
            r_name = self.level.room_names.get(self.caught_room, f"Room {self.caught_room}")
            r_bits = format(self.caught_room, f"0{self.level.n}b")
            self.fail_reason = f"ALARM! Caught by guard in {r_name} [{r_bits}] (P_caught = {p_caught*100:.1f}%)!"
            self.last_check_msg = self.fail_reason
            self.history_states.append(self.state.copy())
            return

        # Not caught: interaction-free measurement projects onto complement of G
        self.state = project_state_complement(self.state, guarded_rooms)
        g_names = ", ".join(self.level.room_names.get(r, f"Room {r}") for r in guarded_rooms)
        self.last_check_msg = (
            f"Guard checked {g_names} (P_caught = {p_caught*100:.1f}%). "
            f"Not there! State collapsed away from guarded rooms."
        )
        self.history_states.append(self.state.copy())
        self._check_final_loot()

    def _check_final_loot(self) -> None:
        """Measure full register after tick T to grab vault loot."""
        if self.tick == self.level.T and not self.failed:
            probs = self.state.probabilities()
            loot_room = self.rng.choices(range(len(probs)), weights=probs)[0]
            if loot_room == self.level.vault:
                self.won = True
            else:
                self.failed = True
                r_name = self.level.room_names.get(loot_room, f"Room {loot_room}")
                r_bits = format(loot_room, f"0{self.level.n}b")
                self.fail_reason = (
                    f"Empty-handed! Final loot measurement collapsed to {r_name} [{r_bits}] instead of Vault."
                )

    def get_rating(self) -> MissionRating:
        """Evaluate star rating based on survival probabilities."""
        if not self.won:
            return MissionRating(0, "Mission Failed", "Thief was caught or missed the vault.")
        if all(p < 1e-6 for p in self.history_p_caught):
            return MissionRating(3, "Ghost Run", "Pure quantum interference/entanglement with 0.0% risk.")
        surv_prob = math.prod(1.0 - p for p in self.history_p_caught)
        if surv_prob >= 0.5:
            return MissionRating(2, "Clean Escape", f"Total survival probability was {surv_prob*100:.1f}% (>= 50%).")
        return MissionRating(1, "Lucky Escape", f"Total survival probability was {surv_prob*100:.1f}% (< 50%).")

