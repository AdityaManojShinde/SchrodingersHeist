# Schrödinger's Heist — 2 to 3 Minute Video Demo Script

This script provides a precise recording plan and voiceover narration matching the automated `--demo` run of `main.py`.

---

## Recording Setup

- **Terminal Window:** 80 columns by 26 rows minimum (or standard 100x30 full-screen terminal).
- **Font:** Monospace (JetBrains Mono, Fira Code, or SF Mono) with ANSI colors enabled.
- **Resolution:** 1080p (1920x1080), 30 or 60 fps.
- **Audio:** Clear voiceover with optional subtle ambient electronic synth background music.
- **Command to Execute:**
  ```bash
  python main.py --demo
  ```
  *(Runs normal speed autoplay with ~3-second pauses between ticks for comfortable viewing and narration).*

---

## Timeline & Narration

### [0:00 – 0:15] The Hook: Classical Evasion is Dead
- **Visual:** Terminal title screen starts:
  ```bash
  python main.py --demo
  ```
  Level 1 ("The Door") begins executing on screen.
- **Spoken Narration (Host):**
  > *"What if sneaking past guards didn't mean hiding behind walls, but existing in two places at once? Welcome to **Schrödinger's Heist**—a quantum stealth puzzle game where you play as an $n$-qubit register breaking into high-security vaults. Classical paths get caught. To survive, you must use the laws of quantum physics: superposition, interference, and entanglement."*

---

### [0:15 – 1:00] Level 2: Canceling Presence with Quantum Interference
- **Visual:** Screen transitions to **Level 2: Hallway of Mirrors** ($n=1$, 2 rooms).
  - Tick 1: Hadamard `H0` creates a 50/50 superposition across Lobby and Vault.
  - Tick 2: Pauli-Z `Z0` applies relative negative phase `[ - ]` to $|1\rangle$.
  - Tick 3: Second Hadamard `H0` cancels the Lobby amplitude to $0.0\%$.
  - Guard inspects Lobby: $P_{\text{caught}} = 0.0\%$.
  - Heist Replay shows 100% measured in Vault $|1\rangle$ across 2,048 simulator shots.
- **Spoken Narration (Host):**
  > *"Here in Level 2, guards patrol the Lobby on Tick 3. If you try to stay put, you're caught immediately. Watch how we solve it:*
  > *First, Hadamard splits our thief into a 50/50 superposition—occupying both the Lobby and Vault simultaneously.*
  > *Next, a Z gate flips our quantum phase. On the outside, probabilities look identical, but notice the negative phase marker in the terminal.*
  > *Finally, our second Hadamard causes quantum interference: amplitudes at the Lobby cancel to exactly zero through destructive interference, while constructively reinforcing the Vault!*
  > *The guard looks directly into the Lobby and sees absolutely nothing. A ghost run!"*

---

### [1:00 – 1:45] Level 4: The Bell Alibi — Entanglement as a Stealth Shield
- **Visual:** Screen reaches **Level 4: Bell Alibi** ($n=2$, 4 rooms).
  - Ticks 1–2: `H1` followed by `CX10` generates the Bell state $(|00\rangle + |11\rangle)/\sqrt{2}$.
  - Terminal shows Lobby ($|00\rangle$) and Vault ($|11\rangle$) at 50% each; Gallery ($|01\rangle$) and Archive ($|10\rangle$) at 0.0%.
  - Guard sweeps Gallery and Archive: both show `[GUARD LOOKING]` but $P_{\text{caught}} = 0.0\%$.
  - Ticks 3–6: Phase flip `Z0`, unrolling via CNOT, and clean extraction into Vault $|11\rangle$.
- **Spoken Narration (Host):**
  > *"In Level 4, security ramps up. Overlapping sensors monitor individual rooms. There is no classical safe room, and no separable single-qubit superposition works.*
  > *The only solution? Quantum entanglement.*
  > *Applying Hadamard and CNOT creates the famous Bell state: $(|00\rangle + |11\rangle)/\sqrt{2}$.*
  > *Notice the room table: our thief is distributed strictly across the Lobby and the Vault. Sensors sweeping the Gallery and Archive detect zero amplitude!*
  > *By entangling two qubits, we've created a non-local alibi that no individual sensor can pierce. We unroll the entanglement and slip into the Vault without ever alerting security."*

---

### [1:45 – 2:30] Level 5: The Grand Vault (GHZ State) & Heist Replay
- **Visual:** Screen showcases **Level 5: The Grand Vault** ($n=3$, 8 chambers).
  - Ticks 1–3: `H2`, `CX21`, `CX10` assemble the 3-qubit GHZ state $(|000\rangle + |111\rangle)/\sqrt{2}$.
  - Ticks 4–9: Coordinated phase manipulation and unraveling into Grand Vault $|111\rangle$.
  - Heist Replay triggers: prints the full ASCII quantum circuit diagram and 2,048-shot AerSimulator histogram with 100% counts on $|111\rangle$ Vault Target.
- **Spoken Narration (Host):**
  > *"Finally, Level 5: The Grand Vault. Eight interconnected chambers monitored by rotating surveillance grids.*
  > *To crack this system, we synthesize a tripartite Greenberger-Horne-Zeilinger (GHZ) state across all three qubits. Non-local three-party correlation lets us glide through rotating perimeter sweeps.*
  > *And here is the payoff: after every run, Schrödinger's Heist triggers **Heist Replay**. It takes our exact quantum circuit, transpiles it onto a quantum simulator backend, and fires thousands of measurement shots.*
  > *Look at that histogram: 2,048 shots, 100.0% Vault detection, 0.0% alarms across all ticks. A flawless 3-star ghost run!"*

---

### [2:30 – 2:45] Wrap-Up & Call to Action
- **Visual:** Terminal displays final victory banner:
  ```
  CONGRATULATIONS, MASTER QUANTUM THIEF!
  You cracked the Grand Vault using pure interference and entanglement.
  Schrödinger's Heist — Built for Qollab x IonQ Quantum Hackathon 2026.
  ```
  Closing slide with repository link and Qollab project URL.
- **Spoken Narration (Host):**
  > *"Schrödinger's Heist is contained entirely within a single Python file, powered by Qiskit and Qiskit Aer, featuring real-time interactive CLI play, an automated DFS quantum solver, and simulator verification.*
  > *Test your own quantum intuition: check out the code on Qollab and GitHub, and see if you can pull off the ultimate heist. Thanks for watching!"*

---

## Backup Commands (Quick Reference)

```bash
# Verify test suite live during demo if desired:
python main.py --selftest

# Fast autoplay for quick rehearsal:
python main.py --demo --fast

# Jump directly to Level 4 during rehearsal:
python main.py --demo 4
```

