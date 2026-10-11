"""Automated test suite for FastAPI application endpoints."""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
from app.app import app

client = TestClient(app)


def test_index_page():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Schrödinger's Heist" in resp.text
    assert "tailwindcss" in resp.text
    print("PASS: GET / serves index.html with TailwindCSS")


def test_get_levels():
    resp = client.get("/api/levels")
    assert resp.status_code == 200
    data = resp.json()
    assert "levels" in data
    assert len(data["levels"]) == 5
    assert data["levels"][0]["title"] == "The Door"
    assert data["levels"][4]["title"] == "The Grand Vault"
    print("PASS: GET /api/levels returns all 5 levels")


def test_level_1_full_playthrough():
    # 1. Start level 1
    resp = client.post("/api/game/start", json={"level_num": 1})
    assert resp.status_code == 200
    data = resp.json()
    session_id = data["session_id"]
    assert data["level"]["num"] == 1
    assert data["tick"] == 0
    assert data["won"] is False
    assert len(data["rooms"]) == 2
    assert data["rooms"][0]["probability"] == 1.0  # Starts in Lobby

    # 2. Peek move 'x0'
    peek_resp = client.post("/api/game/peek", json={"session_id": session_id, "action": "x0"})
    assert peek_resp.status_code == 200
    pdata = peek_resp.json()
    assert pdata["action"] == "x0"
    assert pdata["p_caught"] == 0.0
    assert pdata["risk_status"] == "ZERO RISK (0.0%)"

    # 3. Hint
    hint_resp = client.post("/api/game/hint", json={"session_id": session_id})
    assert hint_resp.status_code == 200
    hdata = hint_resp.json()
    assert hdata["action"] == "x0"

    # 4. Action 'x0'
    act_resp = client.post("/api/game/action", json={"session_id": session_id, "action": "x0"})
    assert act_resp.status_code == 200
    adata = act_resp.json()
    assert adata["tick"] == 1
    assert adata["rooms"][1]["probability"] == 1.0  # Vault has 100%

    # 5. Risk Scan
    scan_resp = client.post("/api/game/scan", json={"session_id": session_id})
    assert scan_resp.status_code == 200
    sdata = scan_resp.json()
    assert len(sdata["steps"]) == 1
    assert sdata["steps"][0]["action"] == "x0"
    assert sdata["steps"][0]["status"] == "ZERO RISK"

    # 6. Action 'wait' (completes Level 1)
    act2_resp = client.post("/api/game/action", json={"session_id": session_id, "action": "wait"})
    assert act2_resp.status_code == 200
    a2data = act2_resp.json()
    assert a2data["tick"] == 2
    assert a2data["won"] is True
    assert a2data["rating"]["stars"] == 3
    assert a2data["rating"]["title"] == "Ghost Run"

    # 7. Replay
    rep_resp = client.post("/api/game/replay", json={"session_id": session_id, "shots": 1024})
    assert rep_resp.status_code == 200
    rdata = rep_resp.json()
    assert "circuit_ascii" in rdata
    assert len(rdata["histogram"]) == 2
    # Vault should have 100% counts
    vault_item = [h for h in rdata["histogram"] if h["is_vault"]][0]
    assert vault_item["count"] == 1024
    print("PASS: Level 1 full playthrough (start, peek, hint, action, scan, win, replay)")


def test_level_5_ghz_playthrough():
    resp = client.post("/api/game/start", json={"level_num": 5})
    assert resp.status_code == 200
    data = resp.json()
    session_id = data["session_id"]
    assert data["level"]["num"] == 5
    assert len(data["rooms"]) == 8

    ghz_moves = ["h2", "cx21", "cx10", "z2", "cx10", "cx21", "h2", "cx21", "cx10"]
    for move in ghz_moves:
        act_resp = client.post("/api/game/action", json={"session_id": session_id, "action": move})
        assert act_resp.status_code == 200
        res = act_resp.json()
        assert res["failed"] is False

    assert res["won"] is True
    assert res["rating"]["stars"] == 3
    print("PASS: Level 5 GHZ 3-qubit playthrough completed with 3 stars")


def test_level_2_playthrough():
    resp = client.post("/api/game/start", json={"level_num": 2})
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]
    # Level 2 intended: h0 -> z0 -> h0
    for move in ["h0", "z0", "h0"]:
        act_resp = client.post("/api/game/action", json={"session_id": session_id, "action": move})
        assert act_resp.status_code == 200
        res = act_resp.json()
        assert res["failed"] is False
    assert res["won"] is True
    assert res["rating"]["stars"] == 3
    print("PASS: Level 2 H-Z-H playthrough completed with 3 stars")


def test_level_3_playthrough():
    resp = client.post("/api/game/start", json={"level_num": 3})
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]
    # Level 3 intended: h1 -> z1 -> h1 -> wait -> cx10
    for move in ["h1", "z1", "h1", "wait", "cx10"]:
        act_resp = client.post("/api/game/action", json={"session_id": session_id, "action": move})
        assert act_resp.status_code == 200
        res = act_resp.json()
        assert res["failed"] is False
    assert res["won"] is True
    assert res["rating"]["stars"] == 3
    print("PASS: Level 3 playthrough completed with 3 stars")


def test_level_4_playthrough():
    resp = client.post("/api/game/start", json={"level_num": 4})
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]
    # Level 4 intended: h1 -> cx10 -> z0 -> cx10 -> h1 -> cx10
    for move in ["h1", "cx10", "z0", "cx10", "h1", "cx10"]:
        act_resp = client.post("/api/game/action", json={"session_id": session_id, "action": move})
        assert act_resp.status_code == 200
        res = act_resp.json()
        assert res["failed"] is False
    assert res["won"] is True
    assert res["rating"]["stars"] == 3
    print("PASS: Level 4 Bell State playthrough completed with 3 stars")


if __name__ == "__main__":
    test_index_page()
    test_get_levels()
    test_level_1_full_playthrough()
    test_level_2_playthrough()
    test_level_3_playthrough()
    test_level_4_playthrough()
    test_level_5_ghz_playthrough()
    print("\nALL 5 LEVELS AND API ENDPOINT TESTS PASSED SUCCESSFULLY!")
