"""Quantum backend adapters, simulator runners, and replay analytics.

Encapsulates simulation backend discovery, circuit transpilation, shot execution,
plan prefix risk scanning, and end-of-level heist replay.
"""

import builtins
from typing import Any

from qiskit import QuantumCircuit, transpile
from qiskit.providers.basic_provider import BasicSimulator

from .engine import GameState
from .quantum import apply_action_to_circuit

# Backend injected by the hosting platform (e.g. Qollab). Set it from the entrypoint
# with set_platform_backend(backend) if the platform exposes a `backend` variable.
_PLATFORM_BACKEND: Any = None


def set_platform_backend(b: Any) -> None:
    """Register the platform-provided backend so get_backend() can find it."""
    global _PLATFORM_BACKEND
    _PLATFORM_BACKEND = b


def _find_platform_backend() -> Any:
    """Return the platform backend if one was registered or injected as a builtin."""
    if _PLATFORM_BACKEND is not None:
        return _PLATFORM_BACKEND
    return getattr(builtins, "backend", None)


def _local_simulator() -> BasicSimulator:
    """Pure-Python simulator that works in the browser runtime (no qiskit-aer needed)."""
    return BasicSimulator()


def get_backend(name: str) -> Any:
    """Retrieve a backend simulator per Qollab documentation or the local fallback.

    name in {'auto', 'aer', 'ionq'}.
    'auto'  -> use the Qollab platform backend if present, else BasicSimulator
    'aer'   -> local simulator (BasicSimulator; qiskit-aer is not available in the browser)
    'ionq'  -> IonQ simulator via Qollab if present; on failure fall back with a notice
    """
    # TODO(qollab): adapt per docs (https://qollab.xyz/learn/docs/compute-backends)
    if name == "aer":
        return _local_simulator()

    platform_backend = _find_platform_backend()

    if name == "ionq":
        if platform_backend is not None and "ionq" in str(platform_backend).lower():
            return platform_backend
        try:
            from qiskit_ionq import IonQProvider  # type: ignore

            provider = IonQProvider()
            return provider.get_backend("ionq_simulator")
        except Exception as e:
            print(
                f"[Backend Notice] IonQ simulator adapter unavailable ({e}). "
                "Falling back to the local BasicSimulator (ideal simulation)."
            )
            return _local_simulator()

    # 'auto' mode
    if platform_backend is not None:
        b_name = getattr(platform_backend, "name", str(platform_backend))
        print(f"[Backend] Connected to Qollab runtime backend: {b_name}")
        return platform_backend

    return _local_simulator()


def run_counts(qc: QuantumCircuit, shots: int = 1024, backend: Any = None) -> dict[str, int]:
    """Transpile for backend, run, and return counts.

    Catches backend exceptions and retries transparently on the local simulator without crashing.
    """
    if backend is None:
        backend = get_backend("aer")
    try:
        tqc = transpile(qc, backend)
        job = backend.run(tqc, shots=shots)
        return dict(job.result().get_counts())
    except Exception as e:
        print(f"[Backend Warning] Execution on {backend} encountered error ({e}); retrying on BasicSimulator...")
        fallback = _local_simulator()
        tqc = transpile(qc, fallback)
        job = fallback.run(tqc, shots=shots)
        return dict(job.result().get_counts())


def risk_scan(game_state: GameState, backend: Any) -> None:
    """Analyze plan prefix with 1024 shots and compare to exact Statevector."""
    k = game_state.tick
    if k == 0:
        print("No actions taken yet in current plan. Use 'peek <action>' to test moves.")
        return

    b_name = getattr(backend, "name", type(backend).__name__)
    print(f"\n--- RISK SCAN (Ticks 1..{k} | Backend: {b_name} | Shots: 1024) ---")
    print(f"{'Tick':<6} {'Action':<8} {'Guarded Rooms':<24} {'Backend Est':<14} {'Exact SV':<12} {'Risk Status'}")
    print("-" * 76)

    had_prior_risk = False
    for step in range(1, k + 1):
        action = game_state.history_actions[step - 1]
        g_rooms = game_state.level.guards[step - 1]
        g_str = ", ".join(game_state.level.room_names.get(r, str(r)) for r in g_rooms) if g_rooms else "None"

        prefix_qc = QuantumCircuit(game_state.level.n)
        for act in game_state.history_actions[:step]:
            apply_action_to_circuit(prefix_qc, act)
        prefix_qc.measure_all()

        counts = run_counts(prefix_qc, shots=1024, backend=backend)
        shot_caught = sum(counts.get(format(r, f"0{game_state.level.n}b"), 0) for r in g_rooms)
        p_est = shot_caught / 1024.0
        p_exact = game_state.history_p_caught[step - 1]

        status = "ZERO RISK" if p_exact < 1e-6 else f"DANGER ({p_exact*100:.1f}%)"
        print(f"{step:<6} {action:<8} {g_str:<24} {p_est*100:>5.1f}% ({shot_caught:>4d}) {p_exact*100:>8.1f}%   {status}")
        if p_exact >= 1e-6:
            had_prior_risk = True

    if had_prior_risk:
        print("\nNote: Earlier ticks had non-zero risk. In actual play, guards perform non-unitary projection.")
        print("Unitary prefix circuits evaluate uncollapsed dynamics and are approximate for risky paths.")


def heist_replay(game_state: GameState, backend: Any, shots: int = 2048) -> None:
    """Print full circuit and measured histogram after level completion."""
    b_name = getattr(backend, "name", type(backend).__name__)
    print("\n====================== HEIST REPLAY ======================")
    print(f"Backend: {b_name} | Total Shots: {shots}\n" + "-" * 58)
    print("Executed Quantum Circuit:")
    try:
        print(game_state.circuit.draw(output="text"))
    except Exception:
        print(game_state.circuit)
    print("-" * 58)

    meas_qc = game_state.circuit.copy()
    meas_qc.measure_all()
    counts = run_counts(meas_qc, shots=shots, backend=backend)

    print("Final State Measurement Histogram:")
    n = game_state.level.n
    for r in range(2**n):
        bitstr = format(r, f"0{n}b")
        r_name = game_state.level.room_names.get(r, f"Room {r}")
        count = counts.get(bitstr, 0)
        pct = count / shots * 100.0
        bar = "█" * int(round(pct / 4))
        tag = " <== [VAULT TARGET]" if r == game_state.level.vault else ""
        print(f"  |{bitstr}> {r_name:<18s} {bar:<25s} {pct:5.1f}% ({count:4d}){tag}")
    print("==========================================================\n")