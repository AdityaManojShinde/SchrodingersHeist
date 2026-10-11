"""Game loops and session runners (interactive and demo).

Coordinates state transitions, user input handling, backend replay triggers,
and gameplay flow.
"""

import random
import sys
import time
from typing import Any, Optional

from .backend import heist_replay, risk_scan
from .engine import GameState
from .models import ACTIONS, Level
from .quantum import calculate_caught_probability, evolve_state
from .solver import find_zero_risk_solutions
from .ui import UI, render_screen


def play_level_interactive(level: Level, backend: Any, rng: Optional[random.Random] = None) -> bool:
    """Run interactive CLI loop for a single level. Returns True on win."""
    state = GameState(level, rng)
    peek_cache = None

    while not (state.won or state.failed):
        render_screen(state, peek_info=peek_cache)
        peek_cache = None

        try:
            raw = input(UI.bold(f"Enter action for Tick {state.tick + 1} (or help): ")).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting game. Goodbye!")
            sys.exit(0)

        if not raw:
            continue
        parts = raw.split()
        cmd = parts[0]

        if cmd in ("quit", "q", "exit"):
            print("Aborting heist. Goodbye!")
            sys.exit(0)
        if cmd in ("help", "h", "?"):
            print(
                f"\nAvailable Commands:\n  <action>        Execute move from toolbox ({', '.join(level.toolbox)})\n"
                "  wait            Remain in current room (apply identity gate)\n"
                "  peek <action>   Preview resulting probabilities without committing\n"
                "  scan            Run Qiskit backend simulation on plan prefix\n"
                "  hint            Suggest next zero-risk action\n"
                "  restart         Restart this level from Tick 1\n"
                "  quit            Exit game\n"
            )
            continue
        if cmd == "restart":
            print(UI.yellow("Restarting level..."))
            state = GameState(level, rng)
            continue
        if cmd == "scan":
            risk_scan(state, backend)
            continue
        if cmd == "hint":
            if level.num in (1, 2, 3, 4):
                sols = find_zero_risk_solutions(level)
                matching = [s for s in sols if s[:state.tick] == state.history_actions]
                print(
                    UI.cyan(f"\n[HINT] A zero-risk action for tick {state.tick + 1} is: '{matching[0][state.tick]}'")
                    if matching
                    else UI.yellow("\n[HINT] Deviated from known zero-risk paths. Consider 'restart'.")
                )
            else:
                sol = level.intended_solution
                print(
                    UI.cyan(f"\n[HINT] Zero-risk GHZ step for tick {state.tick + 1} is: '{sol[state.tick]}'")
                    if sol[:state.tick] == state.history_actions
                    else UI.yellow("\n[HINT] Deviated from GHZ trajectory. Consider 'restart'.")
                )
            continue
        if cmd == "peek":
            if len(parts) < 2 or parts[1] not in level.toolbox:
                print(UI.red(f"Usage: peek <action> (toolbox: {', '.join(level.toolbox)})"))
                continue
            p_action = parts[1]
            nxt_sv = evolve_state(state.state, p_action, level.n)
            nxt_g = level.guards[state.tick] if state.tick < level.T else []
            nxt_p = calculate_caught_probability(nxt_sv, nxt_g)
            peek_cache = (nxt_sv, nxt_p)
            continue

        if cmd not in level.toolbox:
            print(UI.red(f"Invalid action '{cmd}'. Choose from toolbox: {', '.join(level.toolbox)}"))
            continue

        try:
            state.apply_action(cmd)
        except Exception as e:
            print(UI.red(f"Error applying action: {e}"))

    render_screen(state)
    if state.won:
        rating = state.get_rating()
        star_str = "★ " * rating.stars + "☆ " * (3 - rating.stars)
        print(UI.green(UI.bold(f"\nMISSION ACCOMPLISHED! Rating: {star_str} ({rating.stars}/3 Stars)")))
        print(UI.green(f"Rating Details: {rating.title} — {rating.description}"))
        print(UI.cyan(f"Quantum Concept Unlocked: {level.concept}"))
        heist_replay(state, backend)
        return True

    print(UI.red(UI.bold(f"\nMISSION FAILED: {state.fail_reason}")))
    heist_replay(state, backend)
    return False


def play_level_demo(level: Level, backend: Any, rng: Optional[random.Random] = None, fast: bool = False) -> bool:
    """Autoplay the intended solution with step-by-step narration."""
    state = GameState(level, rng)
    print("\n" + "=" * 70 + "\n" + UI.bold(f" DEMO AUTOPLAY — LEVEL {level.num}: {level.title.upper()}") + "\n" + "=" * 70)
    print(f" Story: {level.story}")
    if not fast:
        time.sleep(2.0)

    for step_idx, action in enumerate(level.intended_solution):
        render_screen(state)
        narration = level.narration[step_idx] if step_idx < len(level.narration) else f"Applying {action}."
        print(UI.cyan(UI.bold(f"\n [DEMO MOVE {step_idx + 1}/{level.T}]: {action.upper()} ({ACTIONS[action].flavour})")))
        print(UI.cyan(f" Narration: {narration}"))
        if not fast:
            time.sleep(3.0)
        state.apply_action(action)

    render_screen(state)
    rating = state.get_rating()
    star_str = "★ " * rating.stars + "☆ " * (3 - rating.stars)
    print(UI.green(UI.bold(f"\nDEMO RESULT: {star_str} ({rating.stars}/3 Stars)")))
    print(UI.green(f"{rating.title} — {rating.description}\n") + UI.cyan(f"Quantum Concept: {level.concept}"))
    heist_replay(state, backend)
    if not fast:
        time.sleep(3.0)
    return state.won

