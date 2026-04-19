# =============================================================================
# accounts.py — BLOODSPIRE Account Management
# =============================================================================
# Stores manager accounts in saves/accounts.json.
# Each account tracks: id, manager_name, email, password (hashed), team_ids
# Maximum 5 teams per manager (25 warriors total).
# =============================================================================

import json
import os
import hashlib
import secrets
from typing import Optional

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "saves", "accounts.json")
MAX_TEAMS     = 5


# ---------------------------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------------------------

def _load() -> dict:
    os.makedirs(os.path.dirname(ACCOUNTS_FILE), exist_ok=True)
    if not os.path.exists(ACCOUNTS_FILE):
        return {"accounts": [], "next_id": 1}
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"accounts": [], "next_id": 1}


def _save(data: dict):
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _hash_password(password: str, salt: str = None):
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return h, salt


def _public(acc: dict) -> dict:
    """Return account without sensitive fields."""
    return {
        "id"          : acc["id"],
        "manager_name": acc["manager_name"],
        "email"       : acc["email"],
        "team_ids"    : acc["team_ids"],
    }


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def create_account(manager_name: str, email: str, password: str) -> dict:
    """
    Register a new manager account.
    Returns {success, id, manager_name, team_ids} or {success, error}.
    """
    if not manager_name.strip():
        return {"success": False, "error": "Manager name cannot be blank."}
    if len(password) < 4:
        return {"success": False, "error": "Password must be at least 4 characters."}

    data = _load()
    for acc in data["accounts"]:
        if acc["manager_name"].lower() == manager_name.strip().lower():
            return {"success": False, "error": "That manager name is already taken."}

    pw_hash, salt = _hash_password(password)
    new_acc = {
        "id"          : data["next_id"],
        "manager_name": manager_name.strip().upper(),
        "email"       : email.strip(),
        "pw_hash"     : pw_hash,
        "salt"        : salt,
        "team_ids"    : [],
    }
    data["accounts"].append(new_acc)
    data["next_id"] += 1
    _save(data)

    return {
        "success"      : True,
        "id"           : new_acc["id"],
        "manager_name" : new_acc["manager_name"],
        "team_ids"     : [],
    }


def login(manager_name: str, password: str) -> dict:
    """
    Authenticate a manager.
    Returns {success, id, manager_name, team_ids} or {success, error}.
    """
    data = _load()
    for acc in data["accounts"]:
        if acc["manager_name"].lower() == manager_name.strip().lower():
            h, _ = _hash_password(password, acc["salt"])
            if h == acc["pw_hash"]:
                return {
                    "success"      : True,
                    "id"           : acc["id"],
                    "manager_name" : acc["manager_name"],
                    "email"        : acc.get("email", ""),
                    "team_ids"     : acc["team_ids"],
                    "run_next_turn": acc.get("run_next_turn", {}),
                }
    return {"success": False, "error": "Invalid manager name or password."}


def get_account(manager_id: int) -> Optional[dict]:
    """Return public account data by ID, or None."""
    data = _load()
    for acc in data["accounts"]:
        if acc["id"] == manager_id:
            return _public(acc)
    return None


def get_manager_for_team(team_id: int) -> Optional[int]:
    """Return the manager_id that owns team_id, or None."""
    data = _load()
    for acc in data["accounts"]:
        if team_id in acc.get("team_ids", []):
            return acc["id"]
    return None


def add_team(manager_id: int, team_id: int) -> tuple:
    """
    Associate a team_id with a manager account.
    Returns (success: bool, error_message: str).
    """
    data = _load()
    for acc in data["accounts"]:
        if acc["id"] == manager_id:
            if len(acc["team_ids"]) >= MAX_TEAMS:
                return False, f"Maximum {MAX_TEAMS} teams per manager."
            if team_id not in acc["team_ids"]:
                acc["team_ids"].append(team_id)
                _save(data)
            return True, ""
    return False, "Account not found."


def replace_team(manager_id: int, old_team_id: int, new_team_id: int) -> tuple:
    """
    Swap old_team_id for new_team_id in a manager's team list.
    Preserves slot order. Returns (success, error).
    """
    data = _load()
    for acc in data["accounts"]:
        if acc["id"] == manager_id:
            if old_team_id not in acc["team_ids"]:
                return False, "Team not found in this account."
            idx = acc["team_ids"].index(old_team_id)
            acc["team_ids"][idx] = new_team_id
            # Copy run_next_turn state if present
            rnt = acc.get("run_next_turn", {})
            rnt.pop(str(old_team_id), None)
            acc["run_next_turn"] = rnt
            _save(data)
            return True, ""
    return False, "Account not found."


def remove_team(manager_id: int, team_id: int) -> tuple:
    """
    Remove a team_id from a manager's account (does NOT delete the team file).
    Returns (success, error).
    """
    data = _load()
    for acc in data["accounts"]:
        if acc["id"] == manager_id:
            if team_id not in acc["team_ids"]:
                return False, "Team not found in this account."
            acc["team_ids"].remove(team_id)
            acc.get("run_next_turn", {}).pop(str(team_id), None)
            _save(data)
            return True, ""
    return False, "Account not found."


def set_run_next_turn(manager_id: int, team_id: int, value: bool) -> tuple:
    """
    Set the run_next_turn flag for a specific team. Returns (success, error).
    """
    data = _load()
    for acc in data["accounts"]:
        if acc["id"] == manager_id:
            if "run_next_turn" not in acc:
                acc["run_next_turn"] = {}
            acc["run_next_turn"][str(team_id)] = value
            _save(data)
            return True, ""
    return False, "Account not found."


def get_run_next_turn(manager_id: int, team_id: int) -> bool:
    """Return the run_next_turn flag for a team (default True)."""
    data = _load()
    for acc in data["accounts"]:
        if acc["id"] == manager_id:
            return acc.get("run_next_turn", {}).get(str(team_id), True)
    return True


def get_teams_to_run(manager_id: int, team_ids: list) -> list:
    """Return the subset of team_ids whose run_next_turn flag is True."""
    data = _load()
    for acc in data["accounts"]:
        if acc["id"] == manager_id:
            rnt = acc.get("run_next_turn", {})
            return [tid for tid in team_ids if rnt.get(str(tid), True)]
    return list(team_ids)
