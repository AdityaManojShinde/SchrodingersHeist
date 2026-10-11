# Schrödinger's Heist — Quantum Stealth Puzzle Game

> A turn-based quantum stealth puzzle game built with Qiskit for the Quantum Playground track of the Qollab x IonQ Quantum Hackathon 2026.

---

## 1. Pitch

**Schrödinger's Heist** casts the player as a quantum thief penetrating high-security multi-chamber vaults. Instead of occupying a single room, your position is represented by the basis states of an $n$-qubit quantum register. Guards periodically inspect rooms with projective measurements; getting caught triggers alarms and collapses your wavefunction. To bypass guards and unlock the vault with zero risk, you cannot rely on classical evasion or random guessing—you must orchestrate **superposition**, **relative phase shifts**, **destructive quantum interference**, and **multi-qubit entanglement** so that the probability amplitude in every guarded chamber cancels to exactly zero at the precise moment a guard looks.

---

## 2. Why Quantum Is Essential

In classical stealth games, guards can only be dodged by moving between individual physical rooms. In Schrödinger's Heist, there are levels where **no classical trajectory can achieve zero risk**. Quantum mechanics is not cosmetic flavor or a random number generator; it is the fundamental mechanism required to solve the puzzles:

- **Level 1: The Door (1 qubit, 2 rooms)**
  - *Concept:* Basis state flips and observation timing.
  - *Mechanism:* Introduces the Pauli-X gate ($|0\rangle \to |1\rangle$). Shows how moving away from monitored rooms avoids detection.

- **Level 2: Hallway of Mirrors (1 qubit, 2 rooms)**
  - *Concept:* Destructive quantum interference ($H \to Z \to H$).
  - *Why Quantum is Essential:* The Lobby is guarded on tick 3. A classical thief must remain in either Room 0 or Room 1. By applying Hadamard ($H$) to create $(|0\rangle + |1\rangle)/\sqrt{2}$, Pauli-Z ($Z$) to flip the relative phase to $(|0\rangle - |1\rangle)/\sqrt{2}$, and a second Hadamard ($H$), the amplitudes at $|0\rangle$ interfere destructively ($(1 - 1)/2 = 0$) while constructively interfering at $|1\rangle$, guaranteeing a 100% escape probability with 0% risk.

- **Level 3: Twin Corridors (2 qubits, 4 rooms)**
  - *Concept:* Phase-directed wave steering.
  - *Why Quantum is Essential:* Guard sweeps monitor the Gallery and Lobby across multiple ticks. The player uses relative phase shifts on qubit 1 to steer probability amplitude cleanly into the Archive before executing a conditional dumbwaiter CNOT move into the Vault.

- **Level 4: Bell Alibi (2 qubits, 4 rooms)**
  - *Concept:* Maximal quantum entanglement as an evasion shield.
  - *Why Quantum is Essential:* Overlapping guard patrols inspect individual rooms such that no separable state (e.g. occupying a single room or simple product superposition) can avoid risk. The **only** zero-risk hiding place is the entangled Bell state:
    $$\frac{|00\rangle + |11\rangle}{\sqrt{2}}$$
    Because the amplitudes are strictly concentrated in diagonal chambers ($00$ Lobby and $11$ Vault), guards patrolling rooms $01$ (Gallery) and $10$ (Archive) observe zero probability amplitude! Reversing the entanglement with relative phase $Z_0$ and unrolling via CNOT allows a stealth escape into the Vault.

- **Level 5: The Grand Vault (3 qubits, 8 rooms)**
  - *Concept:* Tripartite Greenberger-Horne-Zeilinger (GHZ) state entanglement.
  - *Why Quantum is Essential:* 8 interconnected chambers are monitored by rotating sensor grids. Only a non-local 3-qubit GHZ state:
    $$\frac{|000\rangle + |111\rangle}{\sqrt{2}}$$
    provides the distributed quantum correlation needed to evade dense perimeter sweeps before focusing all amplitude into the inner vault.

---

## 3. How to Run

### Requirements
- Python 3.10+
- `uv` (recommended) or `pip`
- `qiskit>=1.0`, `qiskit-aer`, `numpy`, `fastapi`, `uvicorn`, `jinja2`, `httpx`

```bash
# Clone or enter project directory
cd Qlab

# Setup virtual environment with uv
uv venv
uv pip install -r requirements.txt

# 1. Run Automated Quantum & Web API Test Suites
uv run python main.py --selftest
uv run python test_app.py

# 2. Launch FastAPI Web Application (Interactive TailwindCSS UI)
uv run python main.py --web
# Alternatively:
uv run uvicorn app.app:app --reload --port 8000
# Open your browser at: http://127.0.0.1:8000

# 3. Run Interactive Terminal Game
uv run python main.py

# 4. Start at a specific level (1-5)
uv run python main.py --level 4

# 5. Watch Autoplay Demo with full narration (no interaction needed)
uv run python main.py --demo

# 6. Fast Demo / CI Mode (no delays)
uv run python main.py --demo --fast

# 7. Specify simulator backend
uv run python main.py --backend aer
```

*Note:* If executed in a non-interactive environment (such as a platform runner without a TTY), `main.py` automatically runs in `--demo` mode so it never blocks waiting for input.

### Cloud Deployment (Render, Heroku, Railway, Fly.io)
A `Procfile` is included for zero-config container and platform deployment:
```bash
web: uvicorn app.app:app --host 0.0.0.0 --port ${PORT:-8000}
```
Simply push to your Git provider and deploy as a Python Web Service.

---

## 4. Level List

| # | Title | Qubits | Rooms | Toolbox | Ticks | Vault | Core Quantum Mechanic |
|---|---|---|---|---|---|---|---|
| **1** | The Door | 1 | 2 | `x0, wait` | 2 | `1` (`|1>`) | Bit flips & timing |
| **2** | Hallway of Mirrors | 1 | 2 | `h0, z0, wait` | 3 | `1` (`|1>`) | $H$-$Z$-$H$ destructive interference |
| **3** | Twin Corridors | 2 | 4 | `h0, h1, z0, z1, cx01, cx10, wait` | 5 | `3` (`|11>`) | Multi-qubit phase steering |
| **4** | Bell Alibi | 2 | 4 | `h0, h1, z0, z1, cx01, cx10, wait` | 6 | `3` (`|11>`) | 2-qubit Bell state entanglement |
| **5** | The Grand Vault | 3 | 8 | `h0..h2, z0..z2, cx01, cx10, cx12, cx21, wait` | 9 | `7` (`|111>`) | 3-qubit GHZ state entanglement |

---

## 5. Technical Architecture

- **Exact Statevector Engine:** The thief's state is evolved as a `qiskit.quantum_info.Statevector`. Non-unitary guard inspections implement true projective measurement:
  - If caught with probability $P_{\text{caught}} = \sum_{r \in G} |\psi_r|^2$, the state collapses onto $G$ and an alarm is triggered.
  - If not caught, the wavefunction is projected onto the complement of $G$ and renormalized, modeling real quantum interaction-free detection.
- **Circuit Tracking & Backend Replay:** Every action is mirrored onto an active `QuantumCircuit`. After each level, **Heist Replay** transpiles the circuit without mid-circuit measurements and executes 2,048 shots on a quantum simulator (`AerSimulator` locally, or Qollab/IonQ simulators in platform mode), printing an ASCII measurement histogram confirming the win.
- **Planning Risk Scan:** Players can execute `scan` at any tick to compile a unitary prefix circuit and sample 1,024 shots against upcoming guard checks.
- **Pruned DFS Solver:** An embedded depth-first solver analyzes levels 1–4, pruning branches whenever $P_{\text{caught}} > 10^{-9}$ to verify zero-risk paths and power real-time in-game hints.
- **Zero-Dependency Terminal Interface:** Uses pure Python ANSI escapes for real-time probability bars and phase markers (`[ + ]`, `[ - ]`, `[+i ]`, `[-i ]`, or radians) without external GUI dependencies.

---

## 6. What Was Built During the Hackathon

- Designed and balanced the entire 5-level quantum stealth game progression from scratch.
- Implemented the full quantum statevector engine with projective measurement and interaction-free collapse rules.
- Built the DFS quantum solver that proves zero-risk solvability for interference and entanglement puzzles.
- Integrated dual-mode simulator backend execution (`AerSimulator` and Qollab/IonQ platform hooks) for Risk Scan and Heist Replay.
- Authored the rich interactive terminal UI, step-by-step narrated demo mode, and 7-part automated test suite.

---

## 7. License

Released under the **MIT License**. Copyright (c) 2026 Aditya.

