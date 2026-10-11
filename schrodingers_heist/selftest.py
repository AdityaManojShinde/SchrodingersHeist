"""Automated verification test suite for Schrödinger's Heist.

Verifies the 7 mandatory game rules, solvers, quantum physics equivalence,
and backend simulators.
"""

import random
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from .backend import get_backend, run_counts
from .engine import GameState
from .game import play_level_demo
from .levels import LEVELS, Level
from .quantum import apply_action_to_circuit, evolve_state
from .solver import find_zero_risk_solutions


def run_selftest(backend_name: str = "aer") -> int:
    """Execute authoritative test suite verifying all 7 requirements."""
    print("================================================================")
    print("           SCHRÖDINGER'S HEIST — AUTOMATED SELFTEST             ")
    print("================================================================")
    all_passed = True

    # Check 1: Zero-risk solver check on levels 1-4
    print("\n[Check 1/7] Testing zero-risk solver on Levels 1-4...")
    try:
        s1, s2 = find_zero_risk_solutions(LEVELS[0]), find_zero_risk_solutions(LEVELS[1])
        s3, s4 = find_zero_risk_solutions(LEVELS[2]), find_zero_risk_solutions(LEVELS[3])
        ok1 = LEVELS[0].intended_solution in s1
        ok2 = LEVELS[1].intended_solution in s2
        ok3 = LEVELS[2].intended_solution in s3 and len(s3) >= 5
        ok4 = LEVELS[3].intended_solution in s4 and len(s4) == 2
        if ok1 and ok2 and ok3 and ok4:
            print(f"  PASS: Intended solutions found (L3 solutions={len(s3)} >= 5, L4 solutions={len(s4)} == 2).")
        else:
            print(f"  FAIL: Solver counts: L1={ok1}, L2={ok2}, L3={len(s3)} (ok={ok3}), L4={len(s4)} (ok={ok4})")
            all_passed = False
    except Exception as err:
        print(f"  FAIL: Exception in Check 1: {err}")
        all_passed = False

    # Check 2: Engine replay of intended solutions
    print("\n[Check 2/7] Testing engine replay of intended solutions (Levels 1-5)...")
    try:
        all_won = True
        for lvl in LEVELS:
            gs = GameState(lvl, random.Random(42))
            for act in lvl.intended_solution:
                gs.apply_action(act)
            vault_p = abs(gs.state.data[lvl.vault]) ** 2
            checks_zero = all(p < 1e-9 for p in gs.history_p_caught)
            if not (gs.won and vault_p >= 1.0 - 1e-9 and checks_zero):
                print(f"  FAIL on Level {lvl.num}: won={gs.won}, vault_p={vault_p}, zero_checks={checks_zero}")
                all_won = False
        if all_won:
            print("  PASS: All 5 levels completed with Vault probability >= 1 - 1e-9 and every p_caught < 1e-9.")
        else:
            all_passed = False
    except Exception as err:
        print(f"  FAIL: Exception in Check 2: {err}")
        all_passed = False

    # Check 3: Engine vs Numpy matrix equivalence
    print("\n[Check 3/7] Testing Statevector engine against manual numpy matrix multiplication...")
    try:
        I_mat = np.eye(2, dtype=complex)
        X_mat = np.array([[0, 1], [1, 0]], dtype=complex)
        Z_mat = np.array([[1, 0], [0, -1]], dtype=complex)
        H_mat = (1.0 / np.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=complex)
        CX10_mat = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=complex)
        CX01_mat = np.array([[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]], dtype=complex)
        gate_map: dict[str, np.ndarray] = {
            "x0": np.kron(I_mat, X_mat),
            "x1": np.kron(X_mat, I_mat),
            "z0": np.kron(I_mat, Z_mat),
            "z1": np.kron(Z_mat, I_mat),
            "h0": np.kron(I_mat, H_mat),
            "h1": np.kron(H_mat, I_mat),
            "cx10": CX10_mat,
            "cx01": CX01_mat,
        }
        test_seq = ["h1", "cx10", "z0", "cx10", "h1", "cx10"]
        np_v = np.zeros(4, dtype=complex)
        np_v[0] = 1.0
        for g in test_seq:
            np_v = gate_map[g] @ np_v

        qc = QuantumCircuit(2)
        for g in test_seq:
            apply_action_to_circuit(qc, g)
        sv = Statevector.from_int(0, 4).evolve(qc)

        diff = float(np.max(np.abs(np_v - sv.data)))
        if diff < 1e-9:
            print(f"  PASS: Statevector matches numpy matrix multiplication (max diff = {diff:.2e} < 1e-9).")
        else:
            print(f"  FAIL: Engine differs from numpy (max diff = {diff})")
            all_passed = False
    except Exception as err:
        print(f"  FAIL: Exception in Check 3: {err}")
        all_passed = False

    # Check 4: Guard-check measurement and collapse statistics
    print("\n[Check 4/7] Testing guard-check math (4,000 trials on |+> with guard [0])...")
    try:
        caught_count = 0
        collapse_ok = True
        dummy_lvl = Level(1, "Test", 1, ["h0"], 1, [[0]], 1, ["h0"], "", "", {0: "0", 1: "1"})
        for trial_seed in range(4000):
            gs = GameState(dummy_lvl, random.Random(trial_seed))
            gs.apply_action("h0")
            if gs.is_caught:
                caught_count += 1
            else:
                probs = gs.state.probabilities()
                if not (abs(probs[1] - 1.0) < 1e-9 and abs(probs[0]) < 1e-9):
                    collapse_ok = False
        freq = caught_count / 4000.0
        in_range = abs(freq - 0.5) <= 0.05
        if in_range and collapse_ok:
            print(f"  PASS: Catch frequency = {freq:.4f} (within 0.50 +/- 0.05); unobserved state strictly |1>.")
        else:
            print(f"  FAIL: Catch frequency = {freq:.4f} (in_range={in_range}), collapse_ok={collapse_ok}")
            all_passed = False
    except Exception as err:
        print(f"  FAIL: Exception in Check 4: {err}")
        all_passed = False

    # Check 5: Backend replay via AerSimulator
    print("\n[Check 5/7] Testing backend replay via get_backend('aer') (>= 99% Vault counts)...")
    try:
        backend = get_backend("aer")
        backend_ok = True
        for lvl in LEVELS:
            qc = QuantumCircuit(lvl.n)
            for act in lvl.intended_solution:
                apply_action_to_circuit(qc, act)
            qc.measure_all()
            counts = run_counts(qc, shots=2048, backend=backend)
            vault_hits = counts.get(format(lvl.vault, f"0{lvl.n}b"), 0)
            fraction = vault_hits / 2048.0
            if fraction < 0.99:
                print(f"  FAIL on Level {lvl.num}: Vault fraction = {fraction*100:.2f}% < 99%")
                backend_ok = False
        if backend_ok:
            print("  PASS: Aer backend replay produced >= 99% Vault outcomes across all 5 levels.")
        else:
            all_passed = False
    except Exception as err:
        print(f"  FAIL: Exception in Check 5: {err}")
        all_passed = False

    # Check 6: Level 5 dynamic guard patrol generation
    print("\n[Check 6/7] Validating Level 5 dynamic guard patrol generation...")
    try:
        lvl5 = LEVELS[4]
        sv5 = Statevector.from_int(0, 8)
        patrol_ok = True
        for t, act in enumerate(lvl5.intended_solution):
            sv5 = evolve_state(sv5, act, 3)
            probs = sv5.probabilities()
            for g_room in lvl5.guards[t]:
                if probs[g_room] >= 1e-9:
                    print(f"  FAIL: Tick {t+1} guard checks room {g_room} with non-zero prob {probs[g_room]}")
                    patrol_ok = False
        if patrol_ok:
            print("  PASS: Level 5 patrols never inspect rooms with non-zero probability on the intended path.")
        else:
            all_passed = False
    except Exception as err:
        print(f"  FAIL: Exception in Check 6: {err}")
        all_passed = False

    # Check 7: Demo mode execution check (--demo --fast)
    print("\n[Check 7/7] Testing full demo execution with --fast flag...")
    try:
        demo_rng = random.Random(1337)
        demo_backend = get_backend(backend_name)
        demo_ok = all(play_level_demo(lvl, backend=demo_backend, rng=demo_rng, fast=True) for lvl in LEVELS)
        if demo_ok:
            print("  PASS: All 5 levels ran through demo mode successfully without exceptions.")
        else:
            print("  FAIL: Demo mode did not win all levels.")
            all_passed = False
    except Exception as err:
        print(f"  FAIL: Exception in Check 7: {err}")
        all_passed = False

    print("\n" + "=" * 64)
    print("                 SELFTEST RESULT: " + ("ALL PASSED (0)" if all_passed else "FAILED (1)"))
    print("================================================================")
    return 0 if all_passed else 1

