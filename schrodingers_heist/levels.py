"""Level design, guard generation, and mission definitions."""

import random
from qiskit.quantum_info import Statevector
from .models import Level
from .quantum import evolve_state


def generate_level_5_guards() -> list[list[int]]:
    """Generate rotating guard patrols for Level 5 using fixed seed 2026.

    Simulates the intended GHZ sequence and selects guarded rooms strictly from
    zero-amplitude basis states at each tick to guarantee zero-risk solvability.
    """
    rng = random.Random(2026)
    sol = ["h2", "cx21", "cx10", "z2", "cx10", "cx21", "h2", "cx21", "cx10"]
    sv = Statevector.from_int(0, 8)
    guards: list[list[int]] = []
    for t, action in enumerate(sol):
        sv = evolve_state(sv, action, 3)
        probs = sv.probabilities()
        zero_rooms = [r for r, p in enumerate(probs) if p < 1e-9]
        if t == len(sol) - 1:
            g = [r for r in range(8) if r != 7]
        else:
            k = min(4, len(zero_rooms))
            g = sorted(rng.sample(zero_rooms, k))
        guards.append(g)
    return guards


LEVELS: list[Level] = [
    Level(
        num=1,
        title="The Door",
        n=1,
        toolbox=["x0", "wait"],
        T=2,
        guards=[[], [0]],
        vault=1,
        intended_solution=["x0", "wait"],
        concept="Moving, guards, and basic classical bit-flips (|0> -> |1>).",
        story="A heavy blast door separates the lobby from the vault. Time your movement past the patrol.",
        room_names={0: "Lobby", 1: "Vault"},
        narration=[
            "Elevator (X0) flips the bit |0> -> |1>. The thief advances directly to the Vault.",
            "Hold still (wait). Guards inspect Room 0, but the thief is already safely in Room 1.",
        ],
    ),
    Level(
        num=2,
        title="Hallway of Mirrors",
        n=1,
        toolbox=["h0", "z0", "wait"],
        T=3,
        guards=[[], [], [0]],
        vault=1,
        intended_solution=["h0", "z0", "h0"],
        concept="Quantum interference: H-Z-H cancels the Lobby amplitude to exactly zero.",
        story="A mirrored corridor of beam-splitters. Moving forward triggers alarms, but quantum paths can cancel.",
        room_names={0: "Lobby", 1: "Vault"},
        narration=[
            "Split (H0) creates an equal superposition (|0> + |1>)/√2. The thief occupies both rooms at once!",
            "Shadow (Z0) applies a relative phase flip to |1>, producing (|0> - |1>)/√2. Magnitudes stay equal.",
            "Split (H0) causes destructive interference at |0> and constructive interference at |1>. The Lobby cancels to 0!",
        ],
    ),
    Level(
        num=3,
        title="Twin Corridors",
        n=2,
        toolbox=["h0", "h1", "z0", "z1", "cx01", "cx10", "wait"],
        T=5,
        guards=[[1], [1], [0, 1], [0, 1], [0, 1, 2]],
        vault=3,
        intended_solution=["h1", "z1", "h1", "wait", "cx10"],
        concept="Phase decides where the wave goes: relative phase steers multi-qubit branching.",
        story="Two security corridors flank the building. Guards sweep both sides; relative phase steers survival.",
        room_names={0: "Lobby", 1: "Gallery", 2: "Archive", 3: "Vault"},
        narration=[
            "Split (H1) creates superposition (|00> + |10>)/√2 between Lobby and Archive. Gallery |01| is empty.",
            "Shadow (Z1) flips the phase of Archive |10> -> (|00> - |10>)/√2, arming destructive interference.",
            "Split (H1) concentrates amplitude purely into Archive |10>. Guards patrol Lobby and Gallery: zero risk!",
            "Hold still (wait) in Archive |10> while guards sweep Lobby and Gallery once more.",
            "Dumbwaiter (CNOT 1->0) steps from Archive |10> into Vault |11> as guards sweep rooms 00, 01, and 10!",
        ],
    ),
    Level(
        num=4,
        title="Bell Alibi",
        n=2,
        toolbox=["h0", "h1", "z0", "z1", "cx01", "cx10", "wait"],
        T=6,
        guards=[[1], [1, 2], [1, 2], [1], [0, 1], [0, 1, 2]],
        vault=3,
        intended_solution=["h1", "cx10", "z0", "cx10", "h1", "cx10"],
        concept="Quantum entanglement: the Bell state (|00> + |11>)/√2 is the only safe hiding place.",
        story="Strict alternating patrols watch individual rooms. Entangling two qubits creates a non-local alibi.",
        room_names={0: "Lobby", 1: "Gallery", 2: "Archive", 3: "Vault"},
        narration=[
            "Split (H1) creates superposition (|00> + |10>)/√2. Guard checks Gallery |01|: safe.",
            "Dumbwaiter (CNOT 1->0) creates Bell state (|00> + |11>)/√2! Gallery |01| and Archive |10| have zero amplitude.",
            "Shadow (Z0) flips the relative phase to (|00> - |11>)/√2 while maintaining safe room distribution.",
            "CNOT 1->0 unrolls the entanglement into (|00> - |10>)/√2, keeping Gallery |01| unobserved.",
            "Split (H1) interferes destructively on Lobby |00>, landing safely in Archive |10>.",
            "Final CNOT 1->0 moves into Vault |11> as guards check rooms 00, 01, and 10! Clean getaway.",
        ],
    ),
    Level(
        num=5,
        title="The Grand Vault",
        n=3,
        toolbox=["h0", "h1", "h2", "z0", "z1", "z2", "cx01", "cx10", "cx12", "cx21", "wait"],
        T=9,
        guards=generate_level_5_guards(),
        vault=7,
        intended_solution=["h2", "cx21", "cx10", "z2", "cx10", "cx21", "h2", "cx21", "cx10"],
        concept="3-qubit GHZ state entanglement: non-local multi-particle correlation across 8 chambers.",
        story="The central repository: eight chambers monitored by rotating grids. Only a tripartite GHZ state can slip past.",
        room_names={
            0: "Lobby",
            1: "Laser Grid",
            2: "Ventilation Shaft",
            3: "Security Terminal",
            4: "Server Core",
            5: "Motion Hall",
            6: "Pressure Chamber",
            7: "Grand Vault",
        },
        narration=[
            "Split (H2) launches superposition across Lobby |000> and Server Core |100>: (|000> + |100>)/√2.",
            "CNOT 2->1 extends the superposition to Pressure Chamber |110>: (|000> + |110>)/√2.",
            "CNOT 1->0 forms the 3-qubit GHZ state (|000> + |111>)/√2! Maximum non-local correlation across all 3 qubits.",
            "Shadow (Z2) flips the GHZ relative phase to (|000> - |111>)/√2 without altering room occupancies.",
            "CNOT 1->0 begins GHZ unrolling into (|000> - |110>)/√2.",
            "CNOT 2->1 collapses correlation back to (|000> - |100>)/√2.",
            "Split (H2) performs destructive interference on |000>, concentrating amplitude purely into |100>.",
            "CNOT 2->1 shifts amplitude from |100> to |110>.",
            "CNOT 1->0 moves into Grand Vault |111>! Final perimeter guards check rooms 0-6: Vault is 100% occupied!",
        ],
    ),
]


def get_level(level_num: int) -> Level:
    """Retrieve Level instance by 1-based index."""
    if not 1 <= level_num <= len(LEVELS):
        raise ValueError(f"Level index {level_num} out of bounds (1..{len(LEVELS)})")
    return LEVELS[level_num - 1]

