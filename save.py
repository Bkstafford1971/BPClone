# =============================================================================
# save.py — Blood Pit Save & Load System
# =============================================================================
# All data is stored as JSON files under the saves/ directory.
#
# Directory layout:
#   saves/
#     game_state.json         — global state (next team ID, turn counter)
#     teams/
#       team_0001.json        — one file per team
#       team_0002.json
#       ...
#     fights/
#       fight_0001.txt        — plain-text fight log
#       fight_0002.txt
#       ...
#
# Design choices:
#   - One file per team for easy inspection and debugging.
#   - Fight logs are plain text (human-readable narrative).
#   - game_state.json tracks global counters so IDs never collide.
#   - All operations use try/except with clear error messages.
# =============================================================================

import json
import os
from typing import Optional, List, Dict
from team import Team

# ---------------------------------------------------------------------------
# DIRECTORY PATHS
# ---------------------------------------------------------------------------

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
SAVES_DIR      = os.path.join(BASE_DIR, "saves")
TEAMS_DIR      = os.path.join(SAVES_DIR, "teams")
FIGHTS_DIR     = os.path.join(SAVES_DIR, "fights")
GAME_STATE_FILE= os.path.join(SAVES_DIR, "game_state.json")


def _ensure_dirs():
    """Create save directories if they don't already exist."""
    for path in (SAVES_DIR, TEAMS_DIR, FIGHTS_DIR):
        os.makedirs(path, exist_ok=True)


# ---------------------------------------------------------------------------
# GAME STATE (global counters)
# ---------------------------------------------------------------------------

DEFAULT_GAME_STATE = {
    "next_team_id" : 1,
    "next_fight_id": 1,
    "turn_number"  : 0,
}


def load_game_state() -> dict:
    """Load global game state. Returns defaults if no save exists yet."""
    _ensure_dirs()
    if not os.path.exists(GAME_STATE_FILE):
        return DEFAULT_GAME_STATE.copy()
    try:
        with open(GAME_STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        # Fill in any missing keys with defaults (handles version upgrades)
        for k, v in DEFAULT_GAME_STATE.items():
            state.setdefault(k, v)
        return state
    except (json.JSONDecodeError, IOError) as e:
        print(f"  WARNING: Could not load game_state.json ({e}). Using defaults.")
        return DEFAULT_GAME_STATE.copy()


def save_game_state(state: dict):
    """Persist global game state to disk."""
    _ensure_dirs()
    try:
        with open(GAME_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except IOError as e:
        print(f"  ERROR: Could not save game_state.json: {e}")


def next_team_id() -> int:
    """Consume and return the next available team ID. Increments the counter."""
    state  = load_game_state()
    new_id = state["next_team_id"]
    state["next_team_id"] += 1
    save_game_state(state)
    return new_id


def next_fight_id() -> int:
    """Consume and return the next available fight log ID."""
    state  = load_game_state()
    new_id = state["next_fight_id"]
    state["next_fight_id"] += 1
    save_game_state(state)
    return new_id


def increment_turn():
    """Advance the global turn counter by 1."""
    state = load_game_state()
    state["turn_number"] += 1
    save_game_state(state)
    return state["turn_number"]


def current_turn() -> int:
    return load_game_state()["turn_number"]


# ---------------------------------------------------------------------------
# TEAM SAVE / LOAD
# ---------------------------------------------------------------------------

def _team_filepath(team_id: int) -> str:
    """Return the full path for a team's JSON save file."""
    return os.path.join(TEAMS_DIR, f"team_{team_id:04d}.json")


def save_team(team: Team) -> str:
    """
    Save a team to disk.
    Assigns a new team_id if the team doesn't have one yet (id == 0).
    Returns the file path written.
    """
    _ensure_dirs()

    # Assign ID on first save
    if team.team_id == 0:
        team.team_id = next_team_id()

    filepath = _team_filepath(team.team_id)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(team.to_dict(), f, indent=2)
        return filepath
    except IOError as e:
        raise IOError(f"Could not save team '{team.team_name}': {e}")


def load_team(team_id: int) -> Team:
    """
    Load a team from disk by its ID.
    Raises FileNotFoundError if the save doesn't exist.
    Raises ValueError if the JSON is malformed.
    """
    filepath = _team_filepath(team_id)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No save file found for team ID {team_id} ({filepath}).")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Team.from_dict(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Corrupted save file for team {team_id}: {e}")


def load_all_teams() -> List[Team]:
    """
    Load every team save file found in the teams directory.
    Skips and warns on any corrupted files.
    Returns a list of Team objects, sorted by team_id.
    """
    _ensure_dirs()
    teams = []
    for filename in sorted(os.listdir(TEAMS_DIR)):
        if not filename.startswith("team_") or not filename.endswith(".json"):
            continue
        try:
            id_str  = filename.replace("team_", "").replace(".json", "")
            team_id = int(id_str)
            team    = load_team(team_id)
            teams.append(team)
        except (ValueError, FileNotFoundError) as e:
            print(f"  WARNING: Skipping '{filename}': {e}")
    return teams


def delete_team(team_id: int) -> bool:
    """
    Delete a team's save file.
    Returns True if deleted, False if the file didn't exist.
    """
    filepath = _team_filepath(team_id)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False


def list_saved_teams() -> List[dict]:
    """
    Return a lightweight summary list of all saved teams without loading
    full warrior data. Useful for a quick team-picker menu.

    Returns list of {"team_id", "team_name", "manager_name"} dicts.
    """
    _ensure_dirs()
    summaries = []
    for filename in sorted(os.listdir(TEAMS_DIR)):
        if not filename.startswith("team_") or not filename.endswith(".json"):
            continue
        filepath = os.path.join(TEAMS_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            summaries.append({
                "team_id"     : data.get("team_id",      0),
                "team_name"   : data.get("team_name",    "Unknown"),
                "manager_name": data.get("manager_name", "Unknown"),
            })
        except Exception:
            pass   # Silently skip malformed summaries
    return summaries


# ---------------------------------------------------------------------------
# FIGHT LOG SAVE
# ---------------------------------------------------------------------------

def save_fight_log(narrative_text: str, team_a_name: str, team_b_name: str) -> tuple:
    """
    Save a fight narrative to a timestamped text file.
    Returns (filepath, fight_id).

    Fight logs are plain text — the full blow-by-blow narrative exactly
    as printed to the console.
    """
    _ensure_dirs()
    fight_id = next_fight_id()
    safe_a   = team_a_name.replace(" ", "_")[:20]
    safe_b   = team_b_name.replace(" ", "_")[:20]
    filename = f"fight_{fight_id:04d}_{safe_a}_vs_{safe_b}.txt"
    filepath = os.path.join(FIGHTS_DIR, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Fight #{fight_id}\n")
            f.write(f"{team_a_name}  vs  {team_b_name}\n")
            f.write("=" * 76 + "\n\n")
            f.write(narrative_text)
        return filepath, fight_id
    except IOError as e:
        raise IOError(f"Could not save fight log: {e}")


def load_fight_log(fight_id: int) -> str:
    """
    Load and return the text of a fight log by ID.
    Raises FileNotFoundError if not found.
    """
    _ensure_dirs()
    for filename in os.listdir(FIGHTS_DIR):
        if filename.startswith(f"fight_{fight_id:04d}_"):
            filepath = os.path.join(FIGHTS_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
    raise FileNotFoundError(f"No fight log found with ID {fight_id}.")


def list_fight_logs() -> List[dict]:
    """
    Return a summary list of all saved fight logs.
    Returns list of {"fight_id", "filename"} dicts, sorted by ID.
    """
    _ensure_dirs()
    logs = []
    for filename in sorted(os.listdir(FIGHTS_DIR)):
        if not filename.startswith("fight_") or not filename.endswith(".txt"):
            continue
        try:
            parts    = filename.split("_")
            fight_id = int(parts[1])
            logs.append({"fight_id": fight_id, "filename": filename})
        except (IndexError, ValueError):
            pass
    return sorted(logs, key=lambda x: x["fight_id"])


# ---------------------------------------------------------------------------
# UTILITY: QUICK SAVE & LOAD ALL
# ---------------------------------------------------------------------------

def save_all_teams(teams: List[Team]):
    """Save a list of teams. Prints a status line for each."""
    for team in teams:
        path = save_team(team)
        print(f"  Saved: {team.team_name} → {os.path.basename(path)}")


def backup_all_saves(backup_suffix: str = "bak") -> int:
    """
    Copy every team JSON to a .bak version in the same folder.
    Returns the number of files backed up.

    Useful before running a turn in case something goes wrong.
    """
    import shutil
    count = 0
    for filename in os.listdir(TEAMS_DIR):
        if filename.endswith(".json"):
            src = os.path.join(TEAMS_DIR, filename)
            dst = src.replace(".json", f".{backup_suffix}")
            shutil.copy2(src, dst)
            count += 1
    return count


# ---------------------------------------------------------------------------
# DISPLAY HELPERS
# ---------------------------------------------------------------------------

def print_save_status():
    """Print a summary of what's currently saved to disk."""
    teams    = list_saved_teams()
    fights   = list_fight_logs()
    state    = load_game_state()

    print("\n  === SAVE STATUS ===")
    print(f"  Turn:        {state['turn_number']}")
    print(f"  Teams saved: {len(teams)}")
    for t in teams:
        print(f"    [{t['team_id']:04d}] {t['team_name']}  (Manager: {t['manager_name']})")
    print(f"  Fight logs:  {len(fights)}")
    if fights:
        last = fights[-1]
        print(f"    Latest: {last['filename']}")
    print()
