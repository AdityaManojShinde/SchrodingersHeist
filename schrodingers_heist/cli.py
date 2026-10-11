"""Command-line interface and main entrypoint for Schrödinger's Heist."""

import argparse
import random
import sys
import time

from .backend import get_backend
from .game import play_level_demo, play_level_interactive
from .levels import LEVELS
from .selftest import run_selftest
from .ui import UI


def create_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Schrödinger's Heist — A modular Qiskit quantum stealth puzzle game."
    )
    parser.add_argument(
        "--demo", nargs="?", const=-1, type=int, default=None,
        help="Autoplay intended solutions with narration (-1 for all levels, or specify LEVEL)",
    )
    parser.add_argument(
        "--level", type=int, default=1,
        help="Start interactive play at level N (1-5)",
    )
    parser.add_argument(
        "--backend", choices=["auto", "aer", "ionq"], default="auto",
        help="Quantum simulator backend (auto, aer, ionq)",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for game RNG (default: time-based seed)",
    )
    parser.add_argument(
        "--fast", action="store_true",
        help="Disable sleeps and delays for CI and fast automated runs",
    )
    parser.add_argument(
        "--no-color", action="store_true",
        help="Disable ANSI terminal colors",
    )
    parser.add_argument(
        "--selftest", action="store_true",
        help="Run comprehensive test suite and exit 0 on success",
    )
    parser.add_argument(
        "--web", action="store_true",
        help="Start the FastAPI web server with interactive TailwindCSS UI",
    )
    parser.add_argument(
        "--port", type=int, default=8000,
        help="Port for the FastAPI web server (default: 8000)",
    )
    parser.add_argument(
        "--host", type=str, default="127.0.0.1",
        help="Host for the FastAPI web server (default: 127.0.0.1)",
    )
    return parser


def main() -> None:
    """Main CLI execution flow."""
    parser = create_parser()
    args = parser.parse_args()

    if args.web:
        import uvicorn
        print(f"Starting Schrödinger's Heist Web UI at http://{args.host}:{args.port} ...")
        uvicorn.run("app.app:app", host=args.host, port=args.port, reload=False)
        return

    if args.no_color or not sys.stdout.isatty():
        UI.set_color(False)

    used_seed = args.seed if args.seed is not None else int(time.time() * 1000) % (2**31)
    game_rng = random.Random(used_seed)
    print(f"[RNG] Initialized with seed: {used_seed}")

    if args.selftest:
        sys.exit(run_selftest(backend_name=args.backend))

    backend = get_backend(args.backend)

    if args.demo is not None:
        target_levels = LEVELS if args.demo == -1 else [LEVELS[args.demo - 1]]
        for lvl in target_levels:
            play_level_demo(lvl, backend=backend, rng=game_rng, fast=args.fast)
        print("\nDemo completed. All vault securities bypassed!")
        return

    # Non-TTY handling: If not interactive and no specific level requested, auto-demo
    if not sys.stdin.isatty() and "--level" not in sys.argv:
        print("[Notice] Non-interactive environment detected (no TTY). Running automated demo...")
        for lvl in LEVELS:
            play_level_demo(lvl, backend=backend, rng=game_rng, fast=args.fast)
        print("\nDemo completed successfully.")
        return

    # Interactive Play
    current_idx = max(0, min(len(LEVELS) - 1, args.level - 1))
    while current_idx < len(LEVELS):
        lvl = LEVELS[current_idx]
        won = play_level_interactive(lvl, backend=backend, rng=game_rng)
        if won:
            current_idx += 1
            if current_idx < len(LEVELS):
                try:
                    ans = input(UI.bold(f"\nProceed to Level {current_idx + 1}? (Y/n): ")).strip().lower()
                    if ans in ("n", "no", "q", "quit"):
                        break
                except (EOFError, KeyboardInterrupt):
                    break
            else:
                print(
                    "\n" + "=" * 70 + "\n" + UI.bold("  CONGRATULATIONS, MASTER QUANTUM THIEF!") +
                    "\n  You cracked the Grand Vault using pure interference and entanglement."
                    "\n  Schrödinger's Heist — Built for Qollab x IonQ Quantum Hackathon 2026.\n" + "=" * 70 + "\n"
                )
                break
        else:
            try:
                ans = input(UI.bold("\nRetry level? (Y/n): ")).strip().lower()
                if ans in ("n", "no", "q", "quit"):
                    break
            except (EOFError, KeyboardInterrupt):
                break


if __name__ == "__main__":
    main()

