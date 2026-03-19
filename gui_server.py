#!/usr/bin/env python3
# =============================================================================
# gui_server.py — Blood Pit Client HTTP Server
# =============================================================================
# Run: python gui_server.py
# Opens http://localhost:8765 in your default browser automatically.
#
# Serves bloodpit_client.html and provides a REST JSON API for all game data.
# =============================================================================

import http.server
import json
import os
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from accounts  import create_account, login, add_team, get_account, MAX_TEAMS
from warrior   import (
    Warrior, Strategy, generate_base_stats,
    ATTRIBUTES, FIGHTING_STYLES, TRIGGERS, AIM_DEFENSE_POINTS,
    NON_WEAPON_SKILLS, WEAPON_SKILLS, SKILL_LEVEL_NAMES,
)
from team      import Team, TEAM_SIZE
from save      import save_team, load_team, next_team_id, increment_turn, current_turn, load_fight_log
from weapons   import WEAPONS
from armor     import armor_selection_menu, helm_selection_menu

PORT     = 8765
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE= os.path.join(BASE_DIR, "bloodpit_client.html")
LEAGUE_SETTINGS_FILE = os.path.join(BASE_DIR, "saves", "league_client.json")


# ---------------------------------------------------------------------------
# JSON CONVERSION HELPERS
# ---------------------------------------------------------------------------

def warrior_to_json(w: Warrior) -> dict:
    """Serialize a warrior to a JSON-compatible dict for the client."""
    d = w.to_dict()
    d["max_hp"]      = w.max_hp
    d["height_in"]   = w.height_in
    d["weight_lbs"]  = w.weight_lbs
    d["kills"]       = w.kills
    d["luck"]        = w.luck
    d["streak"]      = getattr(w, "streak", 0)
    d["turns_active"]= getattr(w, "turns_active", 0)
    d["popularity"]  = getattr(w, "popularity", 50)
    d["want_monster_fight"] = getattr(w, "want_monster_fight", False)
    d["want_retire"]        = getattr(w, "want_retire", False)

    # Format height as ft'in"
    ft  = w.height_in // 12
    ins = w.height_in % 12
    d["height_str"]  = f"{ft}' {ins}\""

    # Build skills list (only trained skills)
    skill_lines = []
    for skill, level in sorted(w.skills.items(), key=lambda x: -x[1]):
        if level > 0:
            desc = SKILL_LEVEL_NAMES.get(level, "Unknown")
            name = skill.replace("_", " ").title()
            skill_lines.append(f"Has {desc.lower()} ({level}) in {name}")
    d["skills_text"] = skill_lines

    # Build injury list
    injury_lines = []
    from warrior import INJURY_DESCRIPTIONS, INJURY_LOCATIONS
    for loc in INJURY_LOCATIONS:
        lvl = w.injuries.get(loc)
        if lvl > 0:
            desc     = INJURY_DESCRIPTIONS.get(lvl, "Unknown")
            loc_name = loc.replace("_", " ").title()
            injury_lines.append(f"Has a {desc.lower()} ({lvl}) injury to the {loc_name}")
    d["injuries_text"] = injury_lines

    # Include injury raw levels too
    d["injury_levels"] = w.injuries.to_dict()

    # Stat display with initial values
    d["stat_display"] = {}
    for attr in ATTRIBUTES:
        current = getattr(w, attr)
        if w.initial_stats and attr in w.initial_stats:
            initial = w.initial_stats[attr]
            d["stat_display"][attr] = f"{current} ({initial})" if current != initial else str(current)
        else:
            d["stat_display"][attr] = str(current)

    return d


def team_to_json(team: Team) -> dict:
    """Serialize a team to JSON for the client."""
    total_w = total_l = total_k = 0
    warriors = []
    for w in team.warriors:
        if w is None:
            warriors.append(None)
        else:
            warriors.append(warrior_to_json(w))
            total_w += w.wins
            total_l += w.losses
            total_k += w.kills

    return {
        "team_id"     : team.team_id,
        "team_name"   : team.team_name,
        "manager_name": team.manager_name,
        "record"      : f"{total_w}-{total_l}-{total_k}",  # W-L-K
        "warriors"    : warriors,
    }


# ---------------------------------------------------------------------------
# REQUEST HANDLER
# ---------------------------------------------------------------------------

class BloodPitHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass  # Suppress console noise

    # --- Helpers ---

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, filepath: str, content_type: str = "text/html; charset=utf-8"):
        if not os.path.exists(filepath):
            self.send_response(404)
            self.end_headers()
            return
        with open(filepath, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def qs(self) -> dict:
        if "?" in self.path:
            return dict(urllib.parse.parse_qsl(self.path.split("?", 1)[1]))
        return {}

    def path_only(self) -> str:
        return self.path.split("?")[0]

    # --- CORS preflight ---

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # --- GET ---

    def do_GET(self):
        p = self.path_only()

        # Serve the HTML client
        if p in ("/", "/index.html"):
            self.send_file(HTML_FILE)
            return

        # --- API routes ---

        if p == "/api/game_data":
            # All static dropdown data the client needs
            self.send_json({
                "weapons"         : sorted([w.display for w in WEAPONS.values()]),
                "armor"           : armor_selection_menu() + ["None"],
                "helms"           : helm_selection_menu() + ["None"],
                "triggers"        : TRIGGERS,
                "styles"          : FIGHTING_STYLES,
                "aim_points"      : AIM_DEFENSE_POINTS,
                "races"           : ["Human","Half-Orc","Halfling","Dwarf","Half-Elf","Elf"],
                "genders"         : ["Male","Female"],
                "attributes"      : ATTRIBUTES,
                "non_weapon_skills": NON_WEAPON_SKILLS,
                "weapon_skills"   : sorted(WEAPON_SKILLS),
                "train_skills"    : sorted(
                ["Strength","Dexterity","Constitution","Intelligence","Presence"] +
                [s.replace("_"," ").title() for s in NON_WEAPON_SKILLS] +
                [w.display for w in WEAPONS.values()]
            ),
            })

        elif p == "/api/rollup":
            # Generate 5 fresh base stat sets
            rolls = [generate_base_stats() for _ in range(TEAM_SIZE)]
            self.send_json({"rolls": rolls})

        elif p == "/api/account":
            q   = self.qs()
            acc = get_account(int(q.get("id", 0)))
            if acc:
                self.send_json({"success": True, "account": acc})
            else:
                self.send_json({"success": False, "error": "Account not found."}, 404)

        elif p == "/api/team":
            q = self.qs()
            try:
                team = load_team(int(q.get("id", 0)))
                self.send_json({"success": True, "team": team_to_json(team)})
            except FileNotFoundError:
                self.send_json({"success": False, "error": "Team not found."}, 404)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 500)

        elif p == "/api/fight/narrative":
            q = self.qs()
            try:
                text = load_fight_log(int(q.get("id", 0)))
                self.send_json({"success": True, "narrative": text})
            except FileNotFoundError:
                self.send_json({"success": False, "error": "Fight log not found."}, 404)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 500)

        elif p == "/api/league/settings":
            self.send_json(_get_league_settings())

        elif p == "/api/league/status":
            self.send_json(_league_proxy_get("/league/status", self.qs()))

        elif p == "/api/league/standings":
            self.send_json(_league_proxy_get("/league/standings", self.qs()))

        elif p == "/api/league/results":
            self.send_json(_league_proxy_get("/league/results", self.qs()))

        elif p == "/api/league/narrative":
            self.send_json(_league_proxy_get("/league/narrative", self.qs()))

        elif p == "/api/league/admin":
            self.send_json(_league_proxy_get("/league/admin", self.qs()))

        elif p == "/api/league_settings":
            # Return saved league server URL and manager credentials
            try:
                with open(LEAGUE_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                self.send_json({"success": True, "settings": settings})
            except FileNotFoundError:
                self.send_json({"success": True, "settings": {
                    "url": "", "manager_id": "", "manager_name": ""
                }})

        else:
            self.send_json({"error": "Not found."}, 404)

    # --- POST ---

    def do_POST(self):
        p    = self.path_only()
        body = self.read_body()

        if p == "/api/account/create":
            result = create_account(
                body.get("manager_name", ""),
                body.get("email", ""),
                body.get("password", ""),
            )
            self.send_json(result)

        elif p == "/api/account/login":
            result = login(
                body.get("manager_name", ""),
                body.get("password", ""),
            )
            self.send_json(result)

        elif p == "/api/team/create":
            self.send_json(_create_team(body))

        elif p == "/api/turn/run":
            self.send_json(_run_turn_for_team(body))

        elif p == "/api/league/settings":
            self.send_json(_save_league_settings(body))

        elif p == "/api/league/register":
            self.send_json(_league_proxy_post("/league/register", body))

        elif p == "/api/league/upload":
            self.send_json(_do_league_upload(body))

        elif p == "/api/league/run_turn":
            self.send_json(_league_proxy_post("/league/run_turn", body))

        elif p == "/api/league/get_results":
            self.send_json(_do_league_get_results(body))

        elif p == "/api/league_settings":
            # Save league server URL and manager credentials locally
            os.makedirs(os.path.dirname(LEAGUE_SETTINGS_FILE), exist_ok=True)
            with open(LEAGUE_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(body, f, indent=2)
            self.send_json({"success": True})

        elif p == "/api/apply_league_results":
            # Apply results downloaded from the league server to the local team
            self.send_json(_apply_league_results(body))

        else:
            self.send_json({"error": "Not found."}, 404)

    # --- PUT ---

    def do_PUT(self):
        p    = self.path_only()
        body = self.read_body()

        if p == "/api/warrior":
            self.send_json(_update_warrior(body))
        else:
            self.send_json({"error": "Not found."}, 404)


# ---------------------------------------------------------------------------
# BUSINESS LOGIC
# ---------------------------------------------------------------------------

def _create_team(body: dict) -> dict:
    """Create a new team from the GUI team-creation form data."""
    manager_id   = body.get("manager_id")
    manager_name = body.get("manager_name", "")
    team_name    = body.get("team_name", "").strip()
    warriors_data= body.get("warriors", [])

    if not team_name:
        return {"success": False, "error": "Team name cannot be blank."}
    if len(warriors_data) < TEAM_SIZE:
        return {"success": False, "error": f"Need exactly {TEAM_SIZE} warriors."}

    team = Team(
        team_name    = team_name.upper(),
        manager_name = manager_name,
        team_id      = next_team_id(),
    )

    for wd in warriors_data:
        name = wd.get("name", "").strip()
        if not name:
            return {"success": False, "error": "All warriors must have a name."}
        try:
            w = Warrior(
                name         = name.upper(),
                race_name    = wd["race"],
                gender       = wd["gender"],
                strength     = int(wd["strength"]),
                dexterity    = int(wd["dexterity"]),
                constitution = int(wd["constitution"]),
                intelligence = int(wd["intelligence"]),
                presence     = int(wd["presence"]),
                size         = int(wd["size"]),
            )
            # Store creation stats for the "current (initial)" display
            w.initial_stats = {
                attr: int(wd[attr])
                for attr in ATTRIBUTES
            }
        except Exception as e:
            return {"success": False, "error": f"Warrior '{name}': {e}"}

        team.add_warrior(w)

    save_team(team)

    ok, err = add_team(manager_id, team.team_id)
    if not ok:
        return {"success": False, "error": err}

    return {"success": True, "team_id": team.team_id, "team": team_to_json(team)}


def _update_warrior(body: dict) -> dict:
    """Update a warrior's gear, strategies, or training from the client."""
    try:
        team = load_team(int(body["team_id"]))
        idx  = int(body["warrior_idx"])
        w    = team.warriors[idx]
        if w is None:
            return {"success": False, "error": "Warrior slot is empty."}

        # Fight-option flags (cleared by matchmaking after use)
        if "want_monster_fight" in body:
            w.want_monster_fight = bool(body["want_monster_fight"])
        if "want_retire" in body:
            w.want_retire = bool(body["want_retire"])

        # Equipment
        for field in ["armor","helm","primary_weapon","secondary_weapon","backup_weapon","blood_cry"]:
            if field in body:
                val = body[field]
                if val == "None":
                    val = None
                setattr(w, field, val)

        # Training queue
        if "trains" in body:
            raw = body["trains"]
            w.trains = [t.lower().replace(" ","_") for t in raw if t and t != "—"][:3]

        # Strategies
        if "strategies" in body:
            w.strategies = []
            for sd in body["strategies"]:
                if sd.get("trigger"):
                    w.strategies.append(Strategy(
                        trigger       = sd["trigger"],
                        style         = sd.get("style", "Strike"),
                        activity      = int(sd.get("activity", 5)),
                        aim_point     = sd.get("aim_point", "None"),
                        defense_point = sd.get("defense_point", "None"),
                    ))
            if not w.strategies:
                w.strategies = [Strategy()]

        save_team(team)

        # Return updated warrior data
        return {"success": True, "warrior": warrior_to_json(w)}

    except Exception as e:
        import traceback; traceback.print_exc()
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# TURN RUNNER
# ---------------------------------------------------------------------------

def _run_turn_for_team(body: dict) -> dict:
    """
    Run one full turn for a player team.
    Returns a JSON summary with per-fight results and the refreshed team data.
    """
    try:
        from ai          import get_or_create_rivals, save_rivals
        from matchmaking import run_turn as _do_run_turn

        team_id = int(body.get("team_id", 0))
        team    = load_team(team_id)
        rivals  = get_or_create_rivals()

        turn_num = increment_turn()

        card = _do_run_turn(team, rivals, verbose=False)

        bouts = []
        for bout in card:
            pw = bout.player_warrior
            r  = bout.result
            if not r:
                continue

            # Determine outcome from the player's perspective
            if r.winner and r.winner.name == pw.name:
                result_str = "WIN"
            elif r.winner is None:
                result_str = "DRAW"
            else:
                result_str = "LOSS"

            bouts.append({
                "warrior_name"   : pw.name,
                "opponent_name"  : bout.opponent.name,
                "opponent_race"  : bout.opponent.race.name,
                "opponent_team"  : bout.opponent_team.team_name,
                "opponent_manager": bout.opponent_manager,
                "fight_type"     : bout.fight_type,
                "result"         : result_str,
                "minutes"        : r.minutes_elapsed,
                "warrior_slain"  : r.loser_died and r.loser is bout.player_warrior,
                "opponent_slain" : r.loser_died and r.winner is not None
                                   and r.winner.name == pw.name,
                "fight_id"       : bout.fight_id,
                "training"       : r.training_results.get(pw.name, []),
            })

        # Reload fresh team (may contain replacement warriors)
        fresh_team = load_team(team_id)

        return {
            "success"     : True,
            "turn_number" : turn_num,
            "bouts"       : bouts,
            "team"        : team_to_json(fresh_team),
        }

    except Exception as e:
        import traceback; traceback.print_exc()
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# LEAGUE SETTINGS (local file per player)
# ---------------------------------------------------------------------------

LEAGUE_SETTINGS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "saves", "league_settings.json"
)


def _get_league_settings() -> dict:
    if not os.path.exists(LEAGUE_SETTINGS_FILE):
        return {"success": True, "settings": {}}
    with open(LEAGUE_SETTINGS_FILE, "r", encoding="utf-8") as f:
        return {"success": True, "settings": json.load(f)}


def _save_league_settings(body: dict) -> dict:
    os.makedirs(os.path.dirname(LEAGUE_SETTINGS_FILE), exist_ok=True)
    settings = body.get("settings", {})
    with open(LEAGUE_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
    return {"success": True}


# ---------------------------------------------------------------------------
# LEAGUE PROXY HELPERS
# ---------------------------------------------------------------------------

def _league_url(path: str) -> str:
    """Build full league server URL from stored settings."""
    try:
        s = _get_league_settings().get("settings", {})
        base = s.get("server_url", "").rstrip("/")
        if not base:
            return None
        return base + path
    except Exception:
        return None


def _league_proxy_get(path: str, params: dict = None) -> dict:
    url = _league_url(path)
    if not url:
        return {"success": False, "error": "No league server URL configured."}
    if params:
        qs = urllib.parse.urlencode(params)
        url = f"{url}?{qs}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"success": False, "error": f"Could not reach league server: {e}"}


def _league_proxy_post(path: str, body: dict) -> dict:
    url = _league_url(path)
    if not url:
        return {"success": False, "error": "No league server URL configured."}
    try:
        data = json.dumps(body).encode("utf-8")
        req  = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"success": False, "error": f"Could not reach league server: {e}"}


def _do_league_upload(body: dict) -> dict:
    """Load the player's team from local disk, attach credentials, upload."""
    try:
        settings = _get_league_settings().get("settings", {})
        team_id  = int(body.get("team_id", 0))
        mgr_id   = settings.get("manager_id")
        password = settings.get("password", "")

        if not mgr_id:
            return {"success": False, "error": "Not registered with league server."}

        team = load_team(team_id)
        return _league_proxy_post("/league/upload", {
            "manager_id": mgr_id,
            "password"  : password,
            "team"      : team.to_dict(),
        })
    except Exception as e:
        return {"success": False, "error": str(e)}


def _do_league_get_results(body: dict) -> dict:
    """Fetch results from league server and apply to the local team."""
    try:
        settings = _get_league_settings().get("settings", {})
        mgr_id   = settings.get("manager_id")
        password = settings.get("password", "")
        team_id  = int(body.get("team_id", 0))

        if not mgr_id:
            return {"success": False, "error": "Not registered with league server."}

        url = _league_url(
            f"/league/results?manager_id={mgr_id}&password="
            + urllib.parse.quote(password)
        )
        if not url:
            return {"success": False, "error": "No league server URL configured."}

        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.loads(r.read())

        if not data.get("success"):
            return data

        # Apply the updated team from the server to local storage
        updated = data.get("updated_team")
        if updated:
            from team import Team
            new_team = Team.from_dict(updated)
            save_team(new_team)

        return {
            "success"     : True,
            "turn"        : data.get("turn"),
            "bouts"       : data.get("bouts", []),
            "team"        : team_to_json(load_team(team_id)) if updated else None,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# LEAGUE RESULT APPLICATOR
# ---------------------------------------------------------------------------

def _apply_league_results(body: dict) -> dict:
    """
    Apply results received from the league server to a local team save.
    The league result contains:
      - team:       updated warrior data (records, injuries, fight_history, etc.)
      - bouts:      fight summaries for the turn results view
      - fight_logs: {fight_id: narrative_text} for the Fights tab
      - turn:       turn number

    We merge the updated warrior state into the local team file and write
    fight logs to the local saves/fights/ directory with new local IDs so
    the narrative viewer can find them.
    """
    try:
        result = body.get("result", {})
        if not result:
            return {"success": False, "error": "No result data provided."}

        team_id = int(body.get("team_id", 0))
        if not team_id:
            return {"success": False, "error": "team_id required."}

        from save import load_team, save_team, save_fight_log

        team = load_team(team_id)

        # Remap league fight_ids to local fight_ids so narratives load correctly
        fight_id_map = {}   # league_fid -> local_fid
        for league_fid_str, narrative in result.get("fight_logs", {}).items():
            local_path, local_fid = save_fight_log(
                narrative,
                result.get("manager_name", "League"),
                "League Turn " + str(result.get("turn", "?")),
            )
            fight_id_map[int(league_fid_str)] = local_fid

        # Apply updated warrior data from the league result
        updated_warriors = result.get("team", {}).get("warriors", [])
        for idx, wd in enumerate(updated_warriors):
            if wd is None or idx >= len(team.warriors):
                continue
            from warrior import Warrior
            updated_w = Warrior.from_dict(wd)
            # Remap fight_ids in fight_history entries
            for entry in updated_w.fight_history:
                old_fid = entry.get("fight_id")
                if old_fid and old_fid in fight_id_map:
                    entry["fight_id"] = fight_id_map[old_fid]
            team.warriors[idx] = updated_w

        save_team(team)

        # Build bout list with remapped fight_ids for the turn results view
        bouts = []
        for b in result.get("bouts", []):
            b2 = dict(b)
            old_fid = b2.get("fight_id")
            if old_fid and old_fid in fight_id_map:
                b2["fight_id"] = fight_id_map[old_fid]
            bouts.append(b2)

        return {
            "success"     : True,
            "turn_number" : result.get("turn"),
            "bouts"       : bouts,
            "team"        : team_to_json(team),
        }

    except Exception as e:
        import traceback; traceback.print_exc()
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

def main():
    server = http.server.HTTPServer(("127.0.0.1", PORT), BloodPitHandler)
    url    = f"http://localhost:{PORT}"

    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║     BLOOD PIT CLIENT - v1.2          ║")
    print("  ╚══════════════════════════════════════╝")
    print(f"\n  Server running at: {url}")
    print("  Opening browser... (Ctrl+C to stop)\n")

    if not os.path.exists(HTML_FILE):
        print(f"  ERROR: bloodpit_client.html not found at {HTML_FILE}")
        print("  Make sure all game files are in the same directory.")
        return

    threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped. Farewell from the Blood Pit.")


if __name__ == "__main__":
    main()
