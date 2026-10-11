"""FastAPI Web Application for Schrödinger's Heist.

Exposes RESTful endpoints for quantum state progression, guard inspection,
peek risk preview, zero-risk hints, prefix risk scans, and heist replay analytics.
"""

import math
import os
from pathlib import Path
import random
import sys
from typing import Any, Dict, List, Optional
import uuid

# Ensure repository root is on sys.path for schrodingers_heist imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from schrodingers_heist.backend import get_backend, run_counts
from schrodingers_heist.engine import GameState
from schrodingers_heist.levels import LEVELS, get_level
from schrodingers_heist.models import ACTIONS
from schrodingers_heist.quantum import (
    apply_action_to_circuit,
    calculate_caught_probability,
    evolve_state,
)
from schrodingers_heist.solver import find_zero_risk_solutions

# Initialize FastAPI application
app = FastAPI(
    title="Schrödinger's Heist — Quantum Simulator API",
    description="Interactive quantum puzzle heist game powered by Qiskit and FastAPI",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# In-memory session store
GAME_SESSIONS: Dict[str, GameState] = {}


# --- Pydantic Request Models ---

class StartGameRequest(BaseModel):
    level_num: int = 1
    session_id: Optional[str] = None


class ActionRequest(BaseModel):
    session_id: str
    action: str


class PeekRequest(BaseModel):
    session_id: str
    action: str


class ScanRequest(BaseModel):
    session_id: str


class ReplayRequest(BaseModel):
    session_id: str
    shots: int = 2048


class HintRequest(BaseModel):
    session_id: str


# --- Helper Serialization Functions ---

def parse_phase_info(amp: complex) -> Dict[str, Any]:
    """Parse quantum amplitude into phase label, category, and angle."""
    mag_sq = abs(amp) ** 2
    if mag_sq < 1e-6:
        return {
            "label": "—",
            "type": "zero",
            "angle": 0.0,
            "real": float(amp.real),
            "imag": float(amp.imag),
        }

    angle = math.atan2(amp.imag, amp.real)
    if abs(angle) < 0.05:
        return {
            "label": "[ + ]",
            "type": "plus",
            "angle": float(angle),
            "real": float(amp.real),
            "imag": float(amp.imag),
        }
    if abs(abs(angle) - math.pi) < 0.05:
        return {
            "label": "[ - ]",
            "type": "minus",
            "angle": float(angle),
            "real": float(amp.real),
            "imag": float(amp.imag),
        }
    if abs(angle - math.pi / 2) < 0.05:
        return {
            "label": "[ +i ]",
            "type": "plus_i",
            "angle": float(angle),
            "real": float(amp.real),
            "imag": float(amp.imag),
        }
    if abs(angle + math.pi / 2) < 0.05:
        return {
            "label": "[ -i ]",
            "type": "minus_i",
            "angle": float(angle),
            "real": float(amp.real),
            "imag": float(amp.imag),
        }

    val = angle / math.pi
    return {
        "label": f"[{val:+.2f}π]",
        "type": "angle",
        "angle": float(angle),
        "real": float(amp.real),
        "imag": float(amp.imag),
    }


def serialize_game_state(game: GameState, session_id: str) -> Dict[str, Any]:
    """Serialize full GameState into a frontend-ready JSON structure."""
    lvl = game.level
    t = game.tick
    probs = game.state.probabilities()
    next_guards = lvl.guards[t] if t < lvl.T else []

    # Room representations
    rooms = []
    for r in range(2**lvl.n):
        bitstr = format(r, f"0{lvl.n}b")
        name = lvl.room_names.get(r, f"Room {r}")
        prob = float(probs[r])
        amp = game.state.data[r]
        phase_info = parse_phase_info(amp)

        rooms.append({
            "index": r,
            "bitstring": bitstr,
            "name": name,
            "probability": prob,
            "probability_pct": round(prob * 100.0, 1),
            "phase": phase_info,
            "is_vault": (r == lvl.vault),
            "is_guarded_next": (r in next_guards),
        })

    # Patrol schedule
    schedule = []
    for step in range(1, lvl.T + 1):
        g_rooms = lvl.guards[step - 1]
        g_names = [lvl.room_names.get(room, f"Room {room}") for room in g_rooms]
        schedule.append({
            "tick": step,
            "guarded_rooms": g_rooms,
            "guarded_names": g_names,
            "is_past": step <= t,
            "is_current": (step == t + 1 and not (game.won or game.failed)),
            "is_future": step > t + 1,
        })

    # Toolbox items with metadata
    toolbox = []
    for token in lvl.toolbox:
        action_def = ACTIONS.get(token)
        toolbox.append({
            "token": token,
            "flavour": action_def.flavour if action_def else token,
            "gate": action_def.gate if action_def else token.upper(),
            "desc": action_def.description if action_def else "",
        })

    # Rating if finished
    rating_data = None
    if game.won or game.failed:
        rating = game.get_rating()
        rating_data = {
            "stars": rating.stars,
            "title": rating.title,
            "summary": rating.description,
        }

    return {
        "session_id": session_id,
        "level": {
            "num": lvl.num,
            "title": lvl.title,
            "n": lvl.n,
            "T": lvl.T,
            "vault": lvl.vault,
            "vault_name": lvl.room_names.get(lvl.vault, f"Room {lvl.vault}"),
            "concept": lvl.concept,
            "story": lvl.story,
            "toolbox": toolbox,
            "schedule": schedule,
        },
        "tick": t,
        "max_ticks": lvl.T,
        "rooms": rooms,
        "history_actions": list(game.history_actions),
        "history_p_caught": [round(p * 100.0, 1) for p in game.history_p_caught],
        "is_caught": game.is_caught,
        "caught_room": game.caught_room,
        "caught_room_name": lvl.room_names.get(game.caught_room, "") if game.caught_room is not None else "",
        "won": game.won,
        "failed": game.failed,
        "fail_reason": game.fail_reason,
        "last_check_msg": game.last_check_msg,
        "rating": rating_data,
    }


def find_hint_move(game: GameState) -> Dict[str, Any]:
    """Calculate the best zero-risk next move or tactical recommendation."""
    lvl = game.level
    t = game.tick

    if game.won or game.failed or t >= lvl.T:
        return {"action": None, "explanation": "Mission already finished."}

    # For Level 5 (GHZ Patrol)
    if lvl.num == 5:
        sol = lvl.intended_solution
        if t < len(sol):
            rec_action = sol[t]
            narration = lvl.narration[t] if t < len(lvl.narration) else ""
            return {
                "action": rec_action,
                "explanation": f"Recommended Move: '{rec_action}'. {narration}",
            }

    # For Levels 1-4: DFS solver from current state
    guarded_rooms = lvl.guards[t]
    valid_candidates = []
    for act in lvl.toolbox:
        nxt_state = evolve_state(game.state, act, lvl.n)
        p_caught = calculate_caught_probability(nxt_state, guarded_rooms)
        if p_caught < 1e-9:
            # Check if this leads to a valid path to vault
            remaining_paths = find_zero_risk_solutions(lvl)
            valid_candidates.append(act)

    if valid_candidates:
        # Check if intended solution matches
        if t < len(lvl.intended_solution) and lvl.intended_solution[t] in valid_candidates:
            rec = lvl.intended_solution[t]
            narr = lvl.narration[t] if t < len(lvl.narration) else ""
            return {
                "action": rec,
                "explanation": f"Recommended Move: '{rec}' (Zero-Risk). {narr}",
            }
        return {
            "action": valid_candidates[0],
            "explanation": f"Recommended Move: '{valid_candidates[0]}' maintains 0.0% guard detection risk.",
        }

    return {
        "action": None,
        "explanation": "No strictly zero-risk moves detected from the current superposition. Consider 'peek' to check risks or restart level.",
    }


# --- API Routes ---

@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    """Serve the interactive TailwindCSS frontend."""
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.get("/api/levels")
async def get_levels_metadata():
    """Retrieve metadata of all available heist levels."""
    levels_data = []
    for l in LEVELS:
        levels_data.append({
            "num": l.num,
            "title": l.title,
            "n": l.n,
            "T": l.T,
            "vault": l.vault,
            "vault_name": l.room_names.get(l.vault, f"Room {l.vault}"),
            "concept": l.concept,
            "story": l.story,
            "toolbox": l.toolbox,
        })
    return {"levels": levels_data}


@app.post("/api/game/start")
async def start_game(req: StartGameRequest):
    """Start or reset a game session for a specific level."""
    session_id = req.session_id or str(uuid.uuid4())
    try:
        level = get_level(req.level_num)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    game = GameState(level=level)
    GAME_SESSIONS[session_id] = game
    return serialize_game_state(game, session_id)


@app.get("/api/game/state")
async def get_game_state(session_id: str):
    """Fetch current state of an existing session."""
    game = GAME_SESSIONS.get(session_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game session not found.")
    return serialize_game_state(game, session_id)


@app.post("/api/game/action")
async def apply_game_action(req: ActionRequest):
    """Apply a quantum move, evaluate guards, and return the new state."""
    game = GAME_SESSIONS.get(req.session_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game session not found.")

    if game.failed or game.won:
        raise HTTPException(status_code=400, detail="Game is already completed.")

    try:
        game.apply_action(req.action)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return serialize_game_state(game, req.session_id)


@app.post("/api/game/peek")
async def peek_action(req: PeekRequest):
    """Preview wavefunction evolution and guard detection probability without mutating state."""
    game = GAME_SESSIONS.get(req.session_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game session not found.")

    if game.failed or game.won or game.tick >= game.level.T:
        raise HTTPException(status_code=400, detail="Cannot peek on a completed game.")

    if req.action not in game.level.toolbox:
        raise HTTPException(status_code=400, detail=f"Action '{req.action}' not in toolbox.")

    # Pure simulation
    preview_sv = evolve_state(game.state, req.action, game.level.n)
    guarded_rooms = game.level.guards[game.tick]
    p_caught = calculate_caught_probability(preview_sv, guarded_rooms)

    probs = preview_sv.probabilities()
    preview_rooms = []
    for r in range(2**game.level.n):
        amp = preview_sv.data[r]
        phase_info = parse_phase_info(amp)
        preview_rooms.append({
            "index": r,
            "bitstring": format(r, f"0{game.level.n}b"),
            "name": game.level.room_names.get(r, f"Room {r}"),
            "probability": float(probs[r]),
            "probability_pct": round(float(probs[r]) * 100.0, 1),
            "phase": phase_info,
            "is_guarded": (r in guarded_rooms),
        })

    return {
        "action": req.action,
        "p_caught": float(p_caught),
        "p_caught_pct": round(float(p_caught) * 100.0, 1),
        "risk_status": "ZERO RISK (0.0%)" if p_caught < 1e-6 else f"DANGER ({p_caught*100:.1f}%)",
        "guarded_rooms": guarded_rooms,
        "rooms": preview_rooms,
    }


@app.post("/api/game/hint")
async def get_hint(req: HintRequest):
    """Return zero-risk path hint or tactical guidance."""
    game = GAME_SESSIONS.get(req.session_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game session not found.")

    hint_info = find_hint_move(game)
    return hint_info


@app.post("/api/game/scan")
async def run_risk_scan(req: ScanRequest):
    """Run quantum prefix risk scan with 1,024 shots comparing backend estimate to exact SV."""
    game = GAME_SESSIONS.get(req.session_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game session not found.")

    k = game.tick
    if k == 0:
        return {
            "steps": [],
            "backend_name": "BasicSimulator",
            "message": "No actions taken yet in current plan. Use 'Peek' or execute moves first.",
        }

    backend = get_backend("aer")
    backend_name = getattr(backend, "name", type(backend).__name__)

    scan_steps = []
    for step in range(1, k + 1):
        action = game.history_actions[step - 1]
        g_rooms = game.level.guards[step - 1]
        g_str = ", ".join(game.level.room_names.get(r, str(r)) for r in g_rooms) if g_rooms else "None"

        # Build prefix circuit
        prefix_qc = QuantumCircuit(game.level.n)
        for act in game.history_actions[:step]:
            apply_action_to_circuit(prefix_qc, act)
        prefix_qc.measure_all()

        counts = run_counts(prefix_qc, shots=1024, backend=backend)
        shot_caught = sum(counts.get(format(r, f"0{game.level.n}b"), 0) for r in g_rooms)
        p_est = shot_caught / 1024.0
        p_exact = game.history_p_caught[step - 1]

        scan_steps.append({
            "step": step,
            "action": action,
            "guarded_rooms_str": g_str,
            "backend_est_pct": round(p_est * 100.0, 1),
            "shots_caught": shot_caught,
            "total_shots": 1024,
            "exact_sv_pct": round(p_exact * 100.0, 1),
            "status": "ZERO RISK" if p_exact < 1e-6 else f"DANGER ({p_exact*100:.1f}%)",
        })

    return {
        "backend_name": backend_name,
        "steps": scan_steps,
        "message": "Scan complete.",
    }


@app.post("/api/game/replay")
async def run_heist_replay(req: ReplayRequest):
    """Run full circuit simulation with 2,048 shots and return ASCII circuit and measurement histogram."""
    game = GAME_SESSIONS.get(req.session_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game session not found.")

    shots = req.shots or 2048
    backend = get_backend("aer")
    backend_name = getattr(backend, "name", type(backend).__name__)

    # Circuit ASCII drawing
    try:
        circuit_diagram = str(game.circuit.draw(output="text"))
    except Exception:
        circuit_diagram = str(game.circuit)

    # Final measurement
    meas_qc = game.circuit.copy()
    meas_qc.measure_all()
    counts = run_counts(meas_qc, shots=shots, backend=backend)

    n = game.level.n
    histogram = []
    for r in range(2**n):
        bitstr = format(r, f"0{n}b")
        name = game.level.room_names.get(r, f"Room {r}")
        cnt = counts.get(bitstr, 0)
        pct = round(cnt / shots * 100.0, 1)
        histogram.append({
            "room_index": r,
            "bitstring": bitstr,
            "name": name,
            "count": cnt,
            "percentage": pct,
            "is_vault": (r == game.level.vault),
        })

    return {
        "backend_name": backend_name,
        "shots": shots,
        "circuit_ascii": circuit_diagram,
        "histogram": histogram,
    }
