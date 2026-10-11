"""Schrödinger's Heist — A modular Qiskit quantum stealth game.

Cleanly architected according to SOLID principles, OOP, and functional programming.
"""

from .backend import get_backend, heist_replay, risk_scan, run_counts
from .engine import GameState
from .game import play_level_demo, play_level_interactive
from .levels import LEVELS, generate_level_5_guards, get_level
from .models import ACTIONS, ActionDef, Level, MissionRating
from .quantum import (
    apply_action_to_circuit,
    calculate_caught_probability,
    calculate_room_probabilities,
    create_action_circuit,
    evolve_state,
    project_state_complement,
    project_state_onto_rooms,
)
from .selftest import run_selftest
from .solver import find_zero_risk_solutions
from .ui import UI, format_phase, format_prob_bar, render_screen

__all__ = [
    "ACTIONS",
    "ActionDef",
    "GameState",
    "Level",
    "LEVELS",
    "MissionRating",
    "UI",
    "apply_action_to_circuit",
    "calculate_caught_probability",
    "calculate_room_probabilities",
    "create_action_circuit",
    "evolve_state",
    "find_zero_risk_solutions",
    "format_phase",
    "format_prob_bar",
    "generate_level_5_guards",
    "get_backend",
    "get_level",
    "heist_replay",
    "play_level_demo",
    "play_level_interactive",
    "project_state_complement",
    "project_state_onto_rooms",
    "render_screen",
    "risk_scan",
    "run_counts",
    "run_selftest",
]

