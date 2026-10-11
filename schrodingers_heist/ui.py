"""Terminal user interface rendering, ANSI color management, and visual markers.

Adheres to Single Responsibility: strictly formats and renders visual output
without containing any quantum evolution or gameplay mutation logic.
"""

import math
from typing import Optional, Tuple
from qiskit.quantum_info import Statevector

from .engine import GameState
from .models import ACTIONS


class UI:
    """Terminal rendering helper supporting configurable ANSI color escapes."""
    COLOR: bool = True

    @classmethod
    def set_color(cls, enabled: bool) -> None:
        """Enable or disable ANSI escape sequences globally."""
        cls.COLOR = enabled

    @classmethod
    def c(cls, code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if cls.COLOR else text

    @classmethod
    def bold(cls, text: str) -> str: return cls.c("1", text)
    @classmethod
    def cyan(cls, text: str) -> str: return cls.c("36", text)
    @classmethod
    def green(cls, text: str) -> str: return cls.c("32", text)
    @classmethod
    def red(cls, text: str) -> str: return cls.c("31", text)
    @classmethod
    def yellow(cls, text: str) -> str: return cls.c("33", text)
    @classmethod
    def magenta(cls, text: str) -> str: return cls.c("35", text)
    @classmethod
    def dim(cls, text: str) -> str: return cls.c("2", text)


def format_phase(amp: complex) -> str:
    """Format the quantum phase of an amplitude as a readable visual marker."""
    if abs(amp) ** 2 < 1e-6:
        return "      "
    angle = math.atan2(amp.imag, amp.real)
    if abs(angle) < 0.05:
        return UI.green(" [ + ]")
    if abs(abs(angle) - math.pi) < 0.05:
        return UI.yellow(" [ - ]")
    if abs(angle - math.pi / 2) < 0.05:
        return UI.cyan("[+i  ]")
    if abs(angle + math.pi / 2) < 0.05:
        return UI.cyan("[-i  ]")
    val = angle / math.pi
    return UI.magenta(f"[{val:+.2f}π]")


def format_prob_bar(prob: float, width: int = 10) -> str:
    """Format a probability value into an ASCII bar graph."""
    filled = max(0, min(width, int(round(prob * width))))
    bar = "█" * filled + "░" * (width - filled)
    return f"{bar} {prob*100:5.1f}%"


def render_screen(game_state: GameState, peek_info: Optional[Tuple[Statevector, float]] = None) -> None:
    """Render the compact terminal UI for the current game tick."""
    lvl, t = game_state.level, game_state.tick
    print("\n" + "=" * 70)
    print(UI.bold(f" LEVEL {lvl.num}: {lvl.title.upper()} (Tick {t}/{lvl.T}) — {lvl.n} Qubits"))
    print("=" * 70 + f"\n Story: {lvl.story}\n" + "-" * 70)

    tb_parts = [f"{UI.cyan(tok)}: {ACTIONS[tok].flavour} ({ACTIONS[tok].gate})" for tok in lvl.toolbox]
    print(" Toolbox: " + " | ".join(tb_parts))

    sched_parts = []
    for step in range(1, lvl.T + 1):
        g_rooms = lvl.guards[step - 1]
        g_names = ", ".join(lvl.room_names.get(r, str(r)) for r in g_rooms) if g_rooms else "None"
        part = f"T{step}:[{g_names}]"
        if step == t + 1 and not (game_state.won or game_state.failed):
            sched_parts.append(UI.yellow(UI.bold(f">{part}<")))
        elif step <= t:
            sched_parts.append(UI.dim(part))
        else:
            sched_parts.append(part)
    print(" Patrols: " + "  ".join(sched_parts) + "\n" + "-" * 70)

    target_sv = peek_info[0] if peek_info else game_state.state
    probs = target_sv.probabilities()
    print(UI.bold(f" {'Room':<18} {'State':<7} {'Probability Bar':<18} {'Phase':<8} {'Status'}") + "\n" + "-" * 70)

    next_guards = lvl.guards[t] if t < lvl.T else []
    for r in range(2**lvl.n):
        bitstr = format(r, f"0{lvl.n}b")
        name = lvl.room_names.get(r, f"Room {r}")
        prob = probs[r]
        bar_str = format_prob_bar(prob)
        phase_str = format_phase(target_sv.data[r])

        tags = []
        if r == lvl.vault:
            tags.append(UI.magenta("[VAULT]"))
        if r in next_guards:
            tags.append(UI.red("[GUARD LOOKING]"))
        print(f" {name:<18} |{bitstr}>  {bar_str:<18} {phase_str:<8} {' '.join(tags)}")

    print("-" * 70)
    if peek_info:
        peek_p = peek_info[1]
        risk_color = UI.green if peek_p < 1e-6 else UI.red
        print(risk_color(f" [PEEK PREVIEW] Next tick guard catch probability: {peek_p*100:.1f}%\n" + "-" * 70))
    if game_state.last_check_msg:
        print(f" Last Patrol Report: {game_state.last_check_msg}\n" + "-" * 70)

