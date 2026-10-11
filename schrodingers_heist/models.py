"""Domain models and data structures for Schrödinger's Heist."""

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class ActionDef:
    """Immutable definition of a quantum action in a level toolbox."""
    token: str
    gate: str
    flavour: str
    description: str


ACTIONS: Mapping[str, ActionDef] = {
    "x0": ActionDef("x0", "X", "Elevator", "Bit-flip qubit 0"),
    "x1": ActionDef("x1", "X", "Elevator", "Bit-flip qubit 1"),
    "x2": ActionDef("x2", "X", "Elevator", "Bit-flip qubit 2"),
    "h0": ActionDef("h0", "H", "Split", "Superposition on qubit 0"),
    "h1": ActionDef("h1", "H", "Split", "Superposition on qubit 1"),
    "h2": ActionDef("h2", "H", "Split", "Superposition on qubit 2"),
    "z0": ActionDef("z0", "Z", "Shadow", "Phase-flip on qubit 0"),
    "z1": ActionDef("z1", "Z", "Shadow", "Phase-flip on qubit 1"),
    "z2": ActionDef("z2", "Z", "Shadow", "Phase-flip on qubit 2"),
    "cx01": ActionDef("cx01", "CNOT", "Dumbwaiter", "Conditional move (ctrl 0 -> tgt 1)"),
    "cx10": ActionDef("cx10", "CNOT", "Dumbwaiter", "Conditional move (ctrl 1 -> tgt 0)"),
    "cx12": ActionDef("cx12", "CNOT", "Dumbwaiter", "Conditional move (ctrl 1 -> tgt 2)"),
    "cx21": ActionDef("cx21", "CNOT", "Dumbwaiter", "Conditional move (ctrl 2 -> tgt 1)"),
    "wait": ActionDef("wait", "I", "Hold still", "Identity gate (remain in place)"),
}


@dataclass(frozen=True)
class MissionRating:
    """Evaluation of heist performance based on survival probabilities."""
    stars: int
    title: str
    description: str


@dataclass
class Level:
    """Specification of a heist mission level."""
    num: int
    title: str
    n: int
    toolbox: list[str]
    T: int
    guards: list[list[int]]  # Guarded room indices per tick (1..T)
    vault: int
    intended_solution: list[str]
    concept: str
    story: str
    room_names: dict[int, str]
    narration: list[str] = field(default_factory=list)

