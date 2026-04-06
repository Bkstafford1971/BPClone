#!/usr/bin/env python3
# =============================================================================
# league_server.py — BLOODSPIRE League Server
# =============================================================================
# The host runs this alongside their normal client.
# All other players connect to http://HOST_IP:8766 to upload teams and
# download results.
#
# Usage:
#   python league_server.py --host-password SECRET [--port 8766]
#
# Admin panel: http://localhost:8766/admin
# =============================================================================

import argparse
import hashlib
import http.server
import json
import os
import secrets
import socketserver
import sys
import threading
import time
import webbrowser
from typing import Optional

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
LEAGUE_DIR   = os.path.join(BASE_DIR, "saves", "league")
DEFAULT_PORT = 8766
sys.path.insert(0, BASE_DIR)

_lock          = threading.Lock()
_turn_progress = {"running": False, "done": 0, "total": 0, "message": ""}
_global_server = None  # Reference for graceful shutdown from request handlers


# =============================================================================
# STORAGE HELPERS
# =============================================================================

def _ensure_dirs():
    os.makedirs(LEAGUE_DIR, exist_ok=True)

def _load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def _save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

def _config_path():   return os.path.join(LEAGUE_DIR, "config.json")
def _managers_path(): return os.path.join(LEAGUE_DIR, "managers.json")
def _standings_path():return os.path.join(LEAGUE_DIR, "standings.json")

def _turn_dir(turn_num):
    d = os.path.join(LEAGUE_DIR, f"turn_{turn_num:04d}")
    os.makedirs(d, exist_ok=True)
    return d

def _load_config():
    cfg = _load_json(_config_path(), {
        "current_turn": 1,
        "turn_state": "open",
        "host_password_hash": "",
        "host_password_salt": "",
        "fight_counter": 0,
        "reset_count": 0,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "show_favorite_weapon": False,  # Feature flag for testing favorite weapon mechanic
        "show_luck_factor": False,      # Feature flag for testing luck factor visibility
        "show_max_hp": False,           # Feature flag for testing max HP visibility
        "ai_teams_enabled": True,       # Whether AI filler teams participate each turn
        "schedule_enabled": False,      # Whether to auto-run turns on a schedule
        "schedule_day": "Friday",       # Day of week to auto-run
        "schedule_time": "20:00",       # HH:MM (24-hour) to auto-run
    })
    # Ensure new flags exist in old configs
    for key, default in [
        ("show_favorite_weapon", False),
        ("show_luck_factor",     False),
        ("show_max_hp",          False),
        ("ai_teams_enabled",     True),
        ("schedule_enabled",     False),
        ("schedule_day",         "Friday"),
        ("schedule_time",        "20:00"),
    ]:
        if key not in cfg:
            cfg[key] = default
    return cfg

def _save_config(cfg):   _save_json(_config_path(), cfg)
def _load_managers():    return _load_json(_managers_path(), {})
def _save_managers(m):   _save_json(_managers_path(), m)
def _load_standings():   return _load_json(_standings_path(), {})
def _save_standings(s):  _save_json(_standings_path(), s)

def _load_uploads(turn_num):
    td = _turn_dir(turn_num)
    if not os.path.exists(td): return {}
    uploads = {}
    for fname in sorted(os.listdir(td)):
        if not (fname.startswith("upload_") and fname.endswith(".json")):
            continue
        data = _load_json(os.path.join(td, fname), None)
        if not data:
            continue
        mid     = data.get("manager_id") or ""
        team_id = data.get("team_id") or (data.get("team") or {}).get("team_id", "")
        # Key by manager_id+team_id so multiple teams from same manager coexist
        key = f"{mid}_team{team_id}" if team_id else mid
        uploads[key] = data
    return uploads

def _save_upload(turn_num, manager_id, data):
    team_id = data.get("team_id") or (data.get("team") or {}).get("team_id", "")
    if team_id:
        fname = f"upload_{manager_id}_team{team_id}.json"
    else:
        fname = f"upload_{manager_id}.json"
    _save_json(os.path.join(_turn_dir(turn_num), fname), data)

def _load_result(turn_num, manager_id):
    return _load_json(os.path.join(_turn_dir(turn_num), f"result_{manager_id}.json"), None)

def _save_result(turn_num, manager_id, data):
    # Include team_id in filename so a manager with multiple teams has separate files
    team_id = data.get("team_id", "")
    if team_id:
        fname = f"result_{manager_id}_team{team_id}.json"
    else:
        fname = f"result_{manager_id}.json"
    _save_json(os.path.join(_turn_dir(turn_num), fname), data)


# =============================================================================
# AUTH HELPERS
# =============================================================================

def _hash_pw(password, salt):
    return hashlib.sha256((salt + password).encode()).hexdigest()

def _check_host_pw(cfg, password):
    return _hash_pw(password, cfg["host_password_salt"]) == cfg["host_password_hash"]

def _check_mgr_pw(mgr, password):
    return _hash_pw(password, mgr["salt"]) == mgr["password_hash"]

def _next_fid(cfg):
    cfg["fight_counter"] = cfg.get("fight_counter", 0) + 1
    return cfg["fight_counter"]


def _store_scout_narrative(warrior_name: str, narrative: str, turn_num: int) -> None:
    """
    Persist the fight narrative for a scouted warrior so the client can
    retrieve it via the scout report without needing to chase fight_ids.
    Stored at saves/league/scout_narratives.json keyed by warrior name.
    """
    path = os.path.join(LEAGUE_DIR, "scout_narratives.json")
    try:
        data = _load_json(path, {})
        data[warrior_name] = {"narrative": narrative, "turn": turn_num}
        _save_json(path, data)
    except Exception:
        pass


# =============================================================================
# FIGHT RUNNER
# =============================================================================

def _run_turn(request_password, rerun_turn=None):
    """Run all fights for the current (or re-run) turn, including 12 AI teams."""
    global _turn_progress
    with _lock:
        cfg = _load_config()
        if not _check_host_pw(cfg, request_password):
            return {"success": False, "error": "Not authorised."}
        if cfg["turn_state"] == "processing":
            return {"success": False, "error": "Turn is already running."}
        turn_num = rerun_turn if rerun_turn else cfg["current_turn"]
        uploads  = _load_uploads(turn_num)

        # Inject AI teams as pseudo-uploads (only when the flag is enabled)
        ai_teams = []
        if cfg.get("ai_teams_enabled", True):
            try:
                from ai_league_teams import get_or_create_ai_teams
                ai_teams = get_or_create_ai_teams()
                for ai_team in ai_teams:
                    mid = ai_team["manager_id"]
                    if mid not in uploads:
                        uploads[mid] = {
                            "manager_id"  : mid,
                            "manager_name": ai_team["manager_name"],
                            "team"        : ai_team,
                            "uploaded_at" : "AI (auto)",
                            "is_ai"       : True,
                        }
            except Exception as e:
                print(f"  WARNING: Could not load AI teams: {e}")
        else:
            print("  AI teams disabled — skipping AI team injection.")

        if not uploads:
            return {"success": False, "error": "No teams (player or AI) available."}
        cfg["turn_state"] = "processing"
        import datetime as _dt2
        cfg["processing_started_at"] = _dt2.datetime.now().isoformat()
        _save_config(cfg)
        _turn_progress = {"running": True, "done": 0, "total": len(uploads),
                          "message": "Starting..."}

    from team        import Team
    from matchmaking import build_fight_card
    from combat      import run_fight, set_show_favorite_weapon, set_show_luck_factor, set_show_max_hp

    # Apply feature flags from config
    cfg = _load_config()
    set_show_favorite_weapon(cfg.get("show_favorite_weapon", False))
    set_show_luck_factor(cfg.get("show_luck_factor", False))
    set_show_max_hp(cfg.get("show_max_hp", False))

    class _Rival:
        def __init__(self, mid, mname, team):
            self.manager_id   = mid
            self.manager_name = mname
            self.team_name    = team.team_name
            self.team         = team
            self.tier         = 3

    rival_map = {}
    for mid, upload in uploads.items():
        try:
            team = Team.from_dict(upload["team"])
            team.manager_name = upload["manager_name"]
            rival_map[mid] = _Rival(mid, upload["manager_name"], team)
            # Store real manager_id on the rival object for cross-team exclusion
            rival_map[mid].real_manager_id = upload.get("manager_id", mid)
        except Exception as e:
            print(f"  WARN: could not load team for {upload.get('manager_name','?')}: {e}")

    cfg         = _load_config()
    all_results = {}
    done_count  = 0

    for manager_id, upload in uploads.items():
        mname = upload["manager_name"]
        done_count += 1
        _turn_progress["done"]    = done_count
        _turn_progress["message"] = f"Fighting: {mname} ({done_count}/{len(uploads)})"
        print(f"\n  [{mname}] processing fights...")
        try:
            player_team = Team.from_dict(upload["team"])
            player_team.manager_name = mname
        except Exception as e:
            print(f"  SKIP {mname}: {e}"); continue

        # Exclude all teams owned by the same manager (real manager_id match)
        this_real_mid = upload.get("manager_id", manager_id)
        is_ai_manager = manager_id.startswith("ai_")
        if is_ai_manager:
            # AI teams only fight other AI teams — player warriors must not
            # appear as opponents here because they already fight once in their
            # OWN team's fight card.  Allowing AI cards to use player warriors
            # as rivals causes each player warrior to fight twice per turn.
            rivals = [
                r for mid, r in rival_map.items()
                if mid != manager_id and mid.startswith("ai_")
            ]
        else:
            rivals = [
                r for mid, r in rival_map.items()
                if mid != manager_id
                and getattr(r, "real_manager_id", mid) != this_real_mid
            ]
        
        # Load champion state for challenge matching
        try:
            from save import load_champion_state
            champ_state = load_champion_state()
        except Exception:
            champ_state = {}
        
        card   = build_fight_card(player_team, rivals, champion_state=champ_state)

        fight_logs, bouts = {}, []
        for bout in card:
            pw  = bout.player_warrior
            ow  = bout.opponent
            result = run_fight(
                pw, ow,
                team_a_name    = player_team.team_name,
                team_b_name    = bout.opponent_team.team_name,
                manager_a_name = mname,
                manager_b_name = bout.opponent_manager,
                is_monster_fight=(bout.opponent_team.team_name == "The Monsters"),
            )
            # Inject scout-attendance flavor text if any manager is watching either warrior
            try:
                from save import get_all_scouted_warriors
                scouted  = get_all_scouted_warriors(turn_num)
                attending= set()
                for warrior in (pw, ow):
                    for mgr in scouted.get(warrior.name, []):
                        attending.add(mgr)
                if attending:
                    mgr_list   = ", ".join(sorted(attending))
                    scout_line = (
                        f"\n[A scout from {mgr_list}'s stable is in attendance, "
                        f"watching the proceedings with a keen eye.]\n"
                    )
                    from combat import FightResult
                    result = FightResult(
                        winner           = result.winner,
                        loser            = result.loser,
                        loser_died       = result.loser_died,
                        minutes_elapsed  = result.minutes_elapsed,
                        narrative        = scout_line + result.narrative,
                        training_results = result.training_results,
                    )
            except Exception:
                pass

            # Persist fight narrative for any scouted warrior in this bout
            try:
                for _w in (pw, ow):
                    if _w.name in scouted:
                        _store_scout_narrative(_w.name, result.narrative, turn_num)
            except Exception:
                pass

            fid    = _next_fid(cfg)
            fight_logs[str(fid)] = result.narrative
            pw_won = result.winner is not None and result.winner.name == pw.name
            killed = result.loser_died and pw_won
            slain  = result.loser_died and not pw_won
            pwr    = "win" if pw_won else "loss"

            # If either warrior is the reigning champion, record as a champion title fight
            _champ_name = champ_state.get("name", "") if isinstance(champ_state, dict) else ""
            fight_type_to_record = (
                "champion" if (_champ_name and (
                    ow.name == _champ_name or pw.name == _champ_name
                )) else bout.fight_type
            )

            # NOTE: record_result() is already called inside run_fight() (combat.py).
            # Do NOT call it again here — wins/losses/kills would be double-counted.

            # Update popularity and recognition (NOT called inside run_fight)
            pw.update_popularity(won=pw_won)
            pw.update_recognition(
                won=pw_won,
                killed_opponent=killed,
                self_hp_pct=result.winner_hp_pct if pw_won else result.loser_hp_pct,
                opp_hp_pct=result.loser_hp_pct if pw_won else result.winner_hp_pct,
                self_knockdowns=result.winner_knockdowns if pw_won else result.loser_knockdowns,
                opp_knockdowns=result.loser_knockdowns if pw_won else result.winner_knockdowns,
                self_near_kills=result.winner_near_kills if pw_won else result.loser_near_kills,
                opp_near_kills=result.loser_near_kills if pw_won else result.winner_near_kills,
                minutes_elapsed=result.minutes_elapsed,
                opponent_total_fights=ow.total_fights,
            )

            pw.fight_history.append({
                "turn": turn_num, "opponent_name": ow.name,
                "opponent_race": ow.race.name, "opponent_team": bout.opponent_team.team_name,
                "result": pwr, "minutes": result.minutes_elapsed, "fight_id": fid,
                "warrior_slain": slain, "opponent_slain": killed, "is_kill": killed,
                "fight_type": fight_type_to_record,
            })
            if slain:
                player_team.kill_warrior(pw, killed_by=ow.name, killer_fights=ow.total_fights)

            bouts.append({
                "warrior_name": pw.name, "opponent_name": ow.name,
                "opponent_race": ow.race.name, "opponent_team": bout.opponent_team.team_name,
                "opponent_manager": bout.opponent_manager, "fight_type": fight_type_to_record,
                "result": pwr.upper(), "minutes": result.minutes_elapsed, "fight_id": fid,
                "warrior_slain": slain, "opponent_slain": killed,
                "training": result.training_results.get(pw.name, []),
            })

        # Create two versions:
        # 1. team_slim: for server-side storage (strip fight_history to save space)
        # 2. team_full: for client download (keep fight_history so client has complete picture)
        team_full = player_team.to_dict()
        
        # Server storage version: stripped fight_history
        team_slim = dict(team_full)
        team_slim["warriors"] = []
        for wd in team_full.get("warriors", []):
            if not wd:
                team_slim["warriors"].append(None)
                continue
            ws = dict(wd)
            ws.pop("fight_history", None)   # strip — large and not needed server-side
            team_slim["warriors"].append(ws)
        
        # Client version: KEEP fight_history for complete record display
        team_for_client = dict(team_full)
        # Don't strip fight_history — clients need it to verify record accuracy
        
        # Preserve archived warriors (they have stats but no fight_history)
        team_slim["archived_warriors"] = team_full.get("archived_warriors", [])
        team_for_client["archived_warriors"] = team_full.get("archived_warriors", [])
        
        # Update turn_history with this turn's results.
        # The upload now includes the client's existing turn_history so we can
        # build an accurate last-5-turns record.  Remove any stale entry for
        # this turn first (handles reruns), then append the fresh one.
        if "turn_history" not in team_for_client:
            team_for_client["turn_history"] = []
        team_for_client["turn_history"] = [
            e for e in team_for_client["turn_history"]
            if e.get("turn") != turn_num
        ]
        team_for_client["turn_history"].append({
            "turn": turn_num,
            "w": sum(1 for b in bouts if b.get("result") == "WIN"),
            "l": sum(1 for b in bouts if b.get("result") == "LOSS"),
            "k": sum(1 for b in bouts if b.get("opponent_slain")),
        })

        mgr_res = {
            "turn"        : turn_num,
            "manager_name": mname,
            "team_id"     : player_team.team_id,
            "team_name"   : player_team.team_name,
            "bouts"       : bouts,
            "team"        : team_for_client,  # Use FULL version with fight_history for client
            "fight_logs"  : fight_logs,
        }
        _save_result(turn_num, manager_id, mgr_res)
        all_results[manager_id] = mgr_res

    # Update standings (skip AI-only results from standings if desired, but include them)
    standings = _load_standings()
    for mid, res in all_results.items():
        if mid not in standings:
            standings[mid] = {"manager_name": res["manager_name"], "turns_played": 0,
                              "warriors": {}, "is_ai": mid.startswith("ai_")}
        e = standings[mid]; e["turns_played"] += 1
        for wd in res["team"].get("warriors", []):
            if not wd: continue
            wn = wd["name"]
            if wn not in e["warriors"]:
                e["warriors"][wn] = {"wins":0,"losses":0,"kills":0,"fights":0}
            ws = e["warriors"][wn]
            ws.update(wins=wd.get("wins",0), losses=wd.get("losses",0),
                      kills=wd.get("kills",0), fights=wd.get("total_fights",0))
    _save_standings(standings)

    # Evolve AI teams — apply fight results, handle deaths, train survivors
    try:
        from ai_league_teams import evolve_ai_teams
        ai_results = {mid: r for mid,r in all_results.items() if mid.startswith("ai_")}
        if ai_teams:
            evolve_ai_teams(ai_teams, ai_results)
            print(f"  AI teams evolved and saved ({len(ai_results)} teams processed).")
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"  WARNING: AI team evolution failed: {e}")

    with _lock:
        if not rerun_turn:
            cfg["turn_state"]   = "results_ready"
            cfg["current_turn"] = turn_num + 1
        else:
            cfg["turn_state"] = "results_ready"
        _save_config(cfg)
        _turn_progress = {"running": False, "done": len(uploads), "total": len(uploads),
                          "message": f"Turn {turn_num} complete — {len(all_results)} managers."}

    # Generate arena newsletter for this turn
    newsletter_text = ""
    try:
        import sys as _sys; _sys.path.insert(0, BASE_DIR)
        from newsletter import generate_newsletter, _update_champion
        from save import load_champion_state, save_champion_state, load_newsletter_voice
        import datetime as _dt

        # Build team objects from result data (non-AI only for newsletter)
        nl_teams = []
        for mid2, res in all_results.items():
            if mid2.startswith("ai_"): continue
            try:
                from team import Team
                t = Team.from_dict(res["team"])
                # turn_history already has this turn appended in team_for_client above
                nl_teams.append(t)
            except Exception:
                pass

        # Include AI teams in newsletter standings
        try:
            from ai_league_teams import load_ai_teams
            from warrior import Warrior
            for at in (load_ai_teams() or []):
                try:
                    t = Team.from_dict(at)
                    nl_teams.append(t)
                except Exception:
                    pass
        except Exception:
            pass

        # Deaths this turn — pull real W/L/K from the team result data
        deaths_nl = []
        _seen_deaths = set()
        for mid2, res in all_results.items():
            team_dict = res.get("team", {})
            warriors_by_name = {
                wd["name"]: wd
                for wd in team_dict.get("warriors", []) if wd
            }
            for b in res.get("bouts", []):
                if b.get("warrior_slain"):
                    wname = b.get("warrior_name", "?")
                    if wname in _seen_deaths:
                        continue
                    _seen_deaths.add(wname)
                    wd    = warriors_by_name.get(wname, {})
                    deaths_nl.append({
                        "name"     : wname,
                        "team"     : res.get("team_name","?"),
                        "w"        : wd.get("wins",  b.get("wins",  0)),
                        "l"        : wd.get("losses", b.get("losses", 0)),
                        "k"        : wd.get("kills",  b.get("kills",  0)),
                        "killed_by": b.get("opponent_name","?"),
                    })
                elif b.get("opponent_slain"):
                    # Opponent (rival/AI) was killed by the player's warrior —
                    # AI teams don't fight player teams from their own perspective,
                    # so this death would otherwise be invisible to the deaths list.
                    oname = b.get("opponent_name", "?")
                    if oname in _seen_deaths:
                        continue
                    _seen_deaths.add(oname)
                    deaths_nl.append({
                        "name"     : oname,
                        "team"     : b.get("opponent_team", "?"),
                        "w"        : 0,
                        "l"        : 0,
                        "k"        : 0,
                        "killed_by": b.get("warrior_name", "?"),
                    })

        # Build a minimal card-like list for the newsletter — all managers including AI
        class _Bout:
            pass
        fake_card = []
        for mid2, res in all_results.items():
            try:
                t = Team.from_dict(res["team"])
                for b in res.get("bouts",[]):
                    bout = _Bout()
                    bout.player_warrior = next(
                        (w for w in t.warriors if w and w.name==b.get("warrior_name")),
                        type("W",(),{"name":b.get("warrior_name","?"),"race":type("R",(),{"name":"Human"})()})()
                    )
                    bout.opponent       = type("W",(),{"name":b.get("opponent_name","?"),"race":type("R",(),{"name":"Human"})()})()
                    bout.player_team    = t
                    bout.opponent_team  = type("T",(),{"team_name":b.get("opponent_team","?"),"team_id":0})()
                    bout.opponent_manager = b.get("opponent_manager","?")
                    bout.fight_type     = b.get("fight_type","rivalry")
                    pw_won = b.get("result","LOSS")=="WIN"
                    bout.result         = type("R",(),{
                        "winner"       : bout.player_warrior if pw_won else bout.opponent,
                        "loser"        : bout.opponent if pw_won else bout.player_warrior,
                        "loser_died"   : b.get("warrior_slain",False) or b.get("opponent_slain",False),
                        "minutes_elapsed": b.get("minutes",3),
                    })()
                    fake_card.append(bout)
            except Exception:
                pass

        champ_state = load_champion_state()

        # Detect if the reigning champion was beaten or didn't fight this turn
        _champ_beaten_by   = None
        _champ_beaten_team = None
        _cur_champ = champ_state.get("name", "")
        _champ_fought = False
        if _cur_champ:
            for _bout in fake_card:
                _pw_won  = _bout.result.winner.name == _bout.player_warrior.name
                _winner  = _bout.player_warrior if _pw_won else _bout.opponent
                _loser   = _bout.opponent       if _pw_won else _bout.player_warrior
                _w_team  = (_bout.player_team.team_name if _pw_won
                            else _bout.opponent_team.team_name)
                # Track whether the champion fought at all
                if _bout.player_warrior.name == _cur_champ or _bout.opponent.name == _cur_champ:
                    _champ_fought = True
                # Detect defeat
                if _loser.name == _cur_champ:
                    _champ_beaten_by   = _winner.name
                    _champ_beaten_team = _w_team
                    break
            # Champion forfeits title if they didn't fight this turn
            if _cur_champ and not _champ_fought and not _champ_beaten_by:
                print(f"  [champion] {_cur_champ} did not fight this turn — title vacated.")
                champ_state = {}

        champ_state = _update_champion(nl_teams, champ_state, deaths_nl,
                                       champion_beaten_by=_champ_beaten_by,
                                       champion_beaten_team=_champ_beaten_team)
        save_champion_state(champ_state)

        voice = load_newsletter_voice()
        date_str = _dt.date.today().strftime("%m/%d/%Y")
        newsletter_text = generate_newsletter(
            turn_num       = turn_num,
            card           = fake_card,
            teams          = nl_teams,
            deaths         = deaths_nl,
            champion_state = champ_state,
            voice          = voice,
            processed_date = date_str,
        )
        # Save newsletter to league turn directory
        nl_path = os.path.join(_turn_dir(turn_num), "newsletter.txt")
        with open(nl_path, "w", encoding="utf-8") as _f:
            _f.write(newsletter_text)
        print(f"  Newsletter written: {nl_path}")
    except Exception as _e:
        import traceback; traceback.print_exc()
        print(f"  WARNING: newsletter generation failed: {_e}")

    total_fights = sum(len(r["bouts"]) for r in all_results.values())
    print(f"\n  Turn {turn_num} complete — {len(all_results)} manager(s), {total_fights} fight(s).")
    return {"success": True, "turn_number": turn_num,
            "managers": len(all_results), "fights": total_fights,
            "newsletter": newsletter_text}


def _filter_warrior_for_client(warrior_dict: dict, cfg: dict) -> dict:
    """
    Filter warrior data for client download based on feature flags.
    Removes sensitive fields if flags are disabled.
    """
    w = warrior_dict.copy()
    # Remove luck factor if flag is off
    if not cfg.get("show_luck_factor", False):
        w.pop("luck", None)
    # Remove favorite weapon if flag is off  
    if not cfg.get("show_favorite_weapon", False):
        w.pop("favorite_weapon", None)
    return w


def _filter_results_for_client(results: list, cfg: dict) -> list:
    """
    Filter all team results for client download based on feature flags.
    """
    filtered = []
    for team_result in results:
        tr = team_result.copy()
        # Filter warriors in the team
        if "team" in tr and "warriors" in tr["team"]:
            tr["team"] = tr["team"].copy()
            tr["team"]["warriors"] = [
                _filter_warrior_for_client(w, cfg)
                for w in tr["team"]["warriors"]
            ]
        filtered.append(tr)
    return filtered


# =============================================================================
# ADMIN PAGE (HTML)
# =============================================================================

def _admin_page():
    cfg      = _load_config()
    managers = _load_managers()
    uploads  = _load_uploads(cfg["current_turn"])
    standings= _load_standings()
    turn     = cfg["current_turn"]
    state    = cfg["turn_state"]
    sc = {"open":"#080","processing":"#840","results_ready":"#00a"}

    # Upload status rows — show AI teams separately
    # Count uploads per manager (keys are now "mid_teamXXX" or "mid")
    mgr_upload_counts = {}
    mgr_upload_times  = {}
    for key, udata in uploads.items():
        uid = udata.get("manager_id", key.split("_team")[0])
        mgr_upload_counts[uid] = mgr_upload_counts.get(uid, 0) + 1
        mgr_upload_times[uid]  = udata.get("uploaded_at","?")

    urows = ""
    for mid, mgr in managers.items():
        count = mgr_upload_counts.get(mid, 0)
        if count:
            badge = f"<b style='color:#060'>✓ {count} team(s) uploaded — {mgr_upload_times.get(mid,'')}</b>"
        else:
            badge = "<span style='color:#800'>✗ not uploaded</span>"
        urows += f"<tr><td>{mgr['manager_name']}</td><td>{badge}</td></tr>"
    if not urows:
        urows = "<tr><td colspan=2 style='color:#888'>No managers registered yet</td></tr>"
    # Add AI teams indicator
    try:
        ai_path = os.path.join(LEAGUE_DIR, "ai_teams.json")
        ai_count = len(json.loads(open(ai_path).read())) if os.path.exists(ai_path) else 0
    except Exception:
        ai_count = 0
    if ai_count:
        urows += f"<tr><td colspan=2 style='color:#555;font-style:italic'>+ {ai_count} AI teams (auto-included)</td></tr>"

    # Standings rows (sorted by wins, AI teams marked)
    warriors_flat = []
    for mid, sd in standings.items():
        is_ai = sd.get("is_ai", mid.startswith("ai_"))
        for wname, ws in sd.get("warriors", {}).items():
            warriors_flat.append({"mgr": sd["manager_name"], "name": wname,
                                   "is_ai": is_ai, **ws})
    warriors_flat.sort(key=lambda x: (-x["wins"], x["losses"]))
    srows = "".join(
        f"<tr><td>{'🤖 ' if w['is_ai'] else ''}{w['mgr']}</td><td>{w['name']}</td>"
        f"<td style='text-align:center'>{w['wins']}-{w['losses']}-{w['kills']}</td>"
        f"<td style='text-align:center'>{w['fights']}</td></tr>"
        for w in warriors_flat
    ) or "<tr><td colspan=4 style='color:#888'>No completed turns yet</td></tr>"

    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BLOODSPIRE League — Admin</title>
<style>
 body{{font:13px Tahoma,Arial,sans-serif;background:#d4d0c8;margin:0}}
 .bar{{background:#000080;color:#fff;padding:6px 14px;font-weight:bold;font-size:15px;
       display:flex;align-items:center;gap:16px}}
 .bar span{{font-size:11px;font-weight:normal;opacity:.9}}
 .wrap{{padding:10px;display:flex;gap:10px;flex-wrap:wrap}}
 .panel{{border:2px solid #808080;background:#fff;padding:10px;flex:1;min-width:260px}}
 h3{{margin:0 0 8px;font-size:12px;font-weight:bold;border-bottom:1px solid #ccc;padding-bottom:4px}}
 table{{border-collapse:collapse;width:100%;font-size:12px}}
 th{{background:#d4d0c8;border:1px solid #808080;padding:3px 8px;text-align:left}}
 td{{border:1px solid #ddd;padding:2px 8px}}
 tr:nth-child(even){{background:#f5f4f0}}
 input[type=password],input[type=number]{{border:2px inset #808080;padding:3px 6px;font-size:12px}}
 button{{background:#d4d0c8;border:2px solid;border-color:#fff #808080 #808080 #fff;
         padding:3px 14px;font-size:12px;cursor:pointer;margin-top:4px}}
 button:active{{border-color:#808080 #fff #fff #808080}}
 button.danger{{border-color:#f88 #800 #800 #f88;color:#800}}
 .state{{font-weight:bold;color:{sc.get(state,'#000')}}}
 #msg{{padding:6px 14px;margin:4px 0;display:none;font-size:12px}}
 .ok{{background:#cfc;border-left:4px solid #080}}
 .err{{background:#fcc;border-left:4px solid #800}}
 .prog-wrap{{background:#e0e0e0;border:1px inset #808080;height:18px;margin:6px 0;position:relative}}
 .prog-bar{{background:#000080;height:100%;transition:width .4s}}
 .prog-lbl{{position:absolute;top:0;left:0;right:0;text-align:center;font-size:11px;
            line-height:18px;color:#fff;mix-blend-mode:difference}}
</style></head><body>
<div class="bar">⚔ BLOODSPIRE League — Admin
 <span>Turn {turn}</span>
 <span class="state">{state.replace("_"," ").upper()}</span>
 <span>{len(mgr_upload_counts)}/{len(managers)} players + {ai_count} AI uploaded</span>
</div>
<div id="msg"></div>
<div class="wrap">

 <div class="panel" style="min-width:260px;max-width:340px">
  <h3>Run Turn {turn}</h3>
  <p style="font-size:11px;color:#555;margin:0 0 6px">
   {len(uploads)} of {len(managers)} players uploaded.<br>
   {ai_count} AI teams auto-included. Players who haven't uploaded are skipped.
  </p>
  Host password:<br>
  <input type="password" id="hp" style="width:200px"><br>
  <button onclick="runTurn()">▶ Run Turn {turn}</button>
  <div id="prog-wrap" class="prog-wrap" style="display:none">
   <div id="prog-bar" class="prog-bar" style="width:0%"></div>
   <div id="prog-lbl" class="prog-lbl">Starting...</div>
  </div>
  <div style="margin-top:10px;border-top:1px solid #ddd;padding-top:8px">
   <b style="font-size:11px">Re-run a past turn:</b><br>
   <input type="number" id="rerun-turn" min="1" max="{turn}" placeholder="Turn #"
          style="width:80px"> &nbsp;
   <button onclick="rerunTurn()">↺ Re-run</button>
  </div>
 </div>

 <div class="panel">
  <h3>Upload Status — Turn {turn}</h3>
  <table><tr><th>Manager</th><th>Status</th></tr>{urows}</table>
 </div>

 <div class="panel" style="min-width:220px;max-width:280px">
  <h3>Arena Reset</h3>
  <p style="font-size:11px;color:#800;margin:0 0 8px">
   ⚠ Wipes all turn history, fight records, and standings.<br>
   Keeps manager registrations. AI teams are regenerated.
  </p>
  <button class="danger" onclick="resetArena()">🗑 Reset Arena to Turn 1</button>
 </div>

 <div class="panel" style="min-width:220px;max-width:320px">
  <h3>Feature Flags (Testing)</h3>
  <p style="font-size:11px;margin:0 0 10px;color:#555">Enable debug visibility for testing mechanics (hidden by default).</p>
  <label style="display:block;margin:6px 0"><input type="checkbox" id="fav-wpn" onchange="toggleFlag('show_favorite_weapon')" style="cursor:pointer">
   <span style="cursor:pointer;user-select:none">Show favorite weapon flavor</span></label>
  <label style="display:block;margin:6px 0"><input type="checkbox" id="luck-fct" onchange="toggleFlag('show_luck_factor')" style="cursor:pointer">
   <span style="cursor:pointer;user-select:none">Show luck factor (1-30)</span></label>
  <label style="display:block;margin:6px 0"><input type="checkbox" id="max-hp" onchange="toggleFlag('show_max_hp')" style="cursor:pointer">
   <span style="cursor:pointer;user-select:none">Show warrior max HP</span></label>
  <div style="margin-top:8px;border-top:1px solid #ddd;padding-top:8px">
   <label style="display:block;margin:6px 0"><input type="checkbox" id="ai-enabled" onchange="toggleFlag('ai_teams_enabled')" style="cursor:pointer">
    <span style="cursor:pointer;user-select:none">AI teams participate each turn</span></label>
   <div style="font-size:10px;color:#666;margin-left:20px">
    Uncheck when running live playtester sessions.
   </div>
  </div>
  <div style="margin-top:8px;font-size:10px;color:#888">
   Changes apply on next turn run.
  </div>
 </div>

 <div class="panel" style="min-width:240px;max-width:340px">
  <h3>Turn Schedule</h3>
  <p style="font-size:11px;margin:0 0 8px;color:#555">
   Automatically run a turn once a week at a set day and time.<br>
   You can still run turns manually at any time regardless of this setting.
  </p>
  <label style="display:block;margin:6px 0">
   <input type="checkbox" id="sched-enabled" onchange="toggleSchedule()" style="cursor:pointer">
   <span style="cursor:pointer;user-select:none">Enable auto-schedule</span>
  </label>
  <div id="sched-details" style="margin-top:8px;padding-left:4px">
   Day:
   <select id="sched-day" onchange="saveSchedule()" style="font-size:12px;border:2px inset #808080;margin-left:4px">
    <option>Sunday</option><option>Monday</option><option>Tuesday</option>
    <option>Wednesday</option><option>Thursday</option><option selected>Friday</option>
    <option>Saturday</option>
   </select>
   <br><br>
   Time (24h):
   <input type="time" id="sched-time" onchange="saveSchedule()"
          style="font-size:12px;border:2px inset #808080;margin-left:4px;width:90px"
          value="20:00">
   <div style="margin-top:8px;font-size:10px;color:#888" id="sched-next"></div>
  </div>
 </div>

</div>
<div class="wrap">
 <div class="panel">
  <h3>Standings (W-L-K) &nbsp; <span style="font-weight:normal;color:#888;font-size:11px">🤖 = AI team</span></h3>
  <table><tr><th>Manager</th><th>Warrior</th><th>Record</th><th>Fights</th></tr>
  {srows}</table>
 </div>
</div>
<script>
let _pollTimer=null;

async function runTurn(){{
 const pw=pw_val();
 if(!pw){{show('Enter the host password first.','err');return;}}
 show('Submitting turn...','ok');
 startPoll();
 try{{
  const r=await fetch('/api/run_turn',{{method:'POST',
   headers:{{'Content-Type':'application/json'}},
   body:JSON.stringify({{host_password:pw}})}});
  const d=await r.json();
  if(!d.success){{show('Error: '+d.error,'err');stopPoll();}}
 }}catch(e){{show('Connection error: '+e.message,'err');stopPoll();}}
}}

async function rerunTurn(){{
 const pw=pw_val();
 const t=document.getElementById('rerun-turn')?.value;
 if(!pw){{show('Enter the host password first.','err');return;}}
 if(!t){{show('Enter a turn number to re-run.','err');return;}}
 show(`Re-running turn ${{t}}...`,'ok');
 startPoll();
 try{{
  const r=await fetch('/api/run_turn',{{method:'POST',
   headers:{{'Content-Type':'application/json'}},
   body:JSON.stringify({{host_password:pw,rerun_turn:parseInt(t)}})}});
  const d=await r.json();
  if(!d.success){{show('Error: '+d.error,'err');stopPoll();}}
 }}catch(e){{show('Connection error: '+e.message,'err');stopPoll();}}
}}

async function resetArena(){{
 const pw=pw_val();
 if(!pw){{show('Enter the host password first.','err');return;}}
 if(!confirm('Reset the arena to Turn 1? This wipes all fight records and standings.'))return;
 try{{
  const r=await fetch('/api/arena/reset',{{method:'POST',
   headers:{{'Content-Type':'application/json'}},
   body:JSON.stringify({{host_password:pw}})}});
  const d=await r.json();
  if(d.success){{show('Arena reset. Reloading...','ok');setTimeout(()=>location.reload(),1500);}}
  else show('Error: '+d.error,'err');
 }}catch(e){{show('Connection error: '+e.message,'err');}}
}}

function pw_val(){{return document.getElementById('hp')?.value||'';}}

function startPoll(){{
 document.getElementById('prog-wrap').style.display='block';
 _pollTimer=setInterval(pollProgress,800);
}}
function stopPoll(){{clearInterval(_pollTimer);_pollTimer=null;}}

async function pollProgress(){{
 try{{
  const d=await(await fetch('/api/progress')).json();
  const pct=d.total>0?Math.round(d.done/d.total*100):0;
  document.getElementById('prog-bar').style.width=pct+'%';
  document.getElementById('prog-lbl').textContent=d.message||'Running...';
  if(!d.running && d.done>0){{
   stopPoll();
   show(`Done — ${{d.message}}`,'ok');
   setTimeout(()=>location.reload(),2000);
  }}
 }}catch(e){{}}
}}

function show(t,c){{const m=document.getElementById('msg');m.textContent=t;m.className=c;m.style.display='block';}}

function _cbId(flag){{
 const m={{'show_favorite_weapon':'fav-wpn','show_luck_factor':'luck-fct',
           'show_max_hp':'max-hp','ai_teams_enabled':'ai-enabled'}};
 return m[flag]||flag;
}}

async function toggleFlag(flag){{
 const pw=pw_val();
 const cb=document.getElementById(_cbId(flag));
 if(!pw){{show('Enter the host password first.','err');cb.checked=!cb.checked;return;}}
 const newVal=cb.checked;
 const body={{}};
 body[flag]=newVal;
 try{{
  const r=await fetch('/api/admin/update',{{method:'POST',
   headers:{{'Content-Type':'application/json'}},
   body:JSON.stringify({{host_password:pw,...body}})}});
  const d=await r.json();
  if(d.success){{
   const label=flag.replace(/^show_/,'').replace(/_/g,' ');
   show(`✓ ${{label}} ${{newVal?'enabled':'disabled'}}`,'ok');
   loadFlags();
  }}else{{
   show('Error: '+d.error,'err');
   cb.checked=!newVal;
  }}
 }}catch(e){{show('Connection error: '+e.message,'err');cb.checked=!newVal;}}
}}

function _applyFlags(flags){{
 const f=flags||{{}};
 document.getElementById('fav-wpn').checked   = f.show_favorite_weapon||false;
 document.getElementById('luck-fct').checked  = f.show_luck_factor||false;
 document.getElementById('max-hp').checked    = f.show_max_hp||false;
 document.getElementById('ai-enabled').checked= f.ai_teams_enabled!==false;
 localStorage.setItem('bp_flags',JSON.stringify(f));
}}

async function loadFlags(){{
 try{{
  const r=await fetch('/api/flags');
  const d=await r.json();
  if(d.success){{_applyFlags(d);return;}}
 }}catch(e){{}}
 try{{
  _applyFlags(JSON.parse(localStorage.getItem('bp_flags')||'{{}}'));
 }}catch(e){{}}
}}

async function loadSchedule(){{
 try{{
  const r=await fetch('/api/schedule');
  const d=await r.json();
  if(!d.success)return;
  document.getElementById('sched-enabled').checked=d.schedule_enabled||false;
  const sel=document.getElementById('sched-day');
  for(let o of sel.options){{if(o.value===d.schedule_day){{o.selected=true;break;}}}}
  document.getElementById('sched-time').value=d.schedule_time||'20:00';
  _updateSchedNote(d.schedule_enabled,d.schedule_day,d.schedule_time);
 }}catch(e){{}}
}}

function _updateSchedNote(enabled,day,t){{
 const el=document.getElementById('sched-next');
 if(!el)return;
 if(!enabled){{el.textContent='Schedule is disabled.';return;}}
 el.textContent=`Next auto-run: ${{day}} at ${{t}}`;
}}

async function toggleSchedule(){{
 const pw=pw_val();
 if(!pw){{show('Enter the host password first.','err');
          document.getElementById('sched-enabled').checked=!document.getElementById('sched-enabled').checked;return;}}
 await saveSchedule();
}}

async function saveSchedule(){{
 const pw=pw_val();
 if(!pw)return;  // silent if no pw — only fires on explicit toggle or time change
 const enabled=document.getElementById('sched-enabled').checked;
 const day=document.getElementById('sched-day').value;
 const t=document.getElementById('sched-time').value;
 try{{
  const r=await fetch('/api/admin/update',{{method:'POST',
   headers:{{'Content-Type':'application/json'}},
   body:JSON.stringify({{host_password:pw,schedule_enabled:enabled,
                         schedule_day:day,schedule_time:t}})}});
  const d=await r.json();
  if(d.success){{
   _updateSchedNote(enabled,day,t);
   show(`✓ Schedule ${{enabled?'set to '+day+' '+t:'disabled'}}`,'ok');
  }}else show('Error: '+d.error,'err');
 }}catch(e){{show('Connection error: '+e.message,'err');}}
}}

document.addEventListener('DOMContentLoaded',()=>{{loadFlags();loadSchedule();}});

// Browser close detection — gracefully shutdown server when page unloads
window.addEventListener('beforeunload', () => {{
  navigator.sendBeacon('/api/shutdown', '');
}});
</script></body></html>"""


# =============================================================================
# HTTP HANDLER
# =============================================================================

class LeagueHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, *a): pass

    def _shutdown_server(self):
        """Gracefully shutdown the server."""
        import time
        time.sleep(0.2)  # Brief wait to ensure response is fully sent
        global _global_server
        if _global_server:
            try:
                _global_server.shutdown()
                _global_server.server_close()
            except Exception:
                pass
        import sys
        sys.exit(0)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def send_json(self, data, status=200):
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type",   "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()

    def send_html(self, html, status=200):
        body = html.encode()
        self.send_response(status)
        self.send_header("Content-Type",   "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()

    def body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n)) if n else {}

    def qs(self):
        from urllib.parse import parse_qsl
        return dict(parse_qsl(self.path.split("?",1)[1])) if "?" in self.path else {}

    def p(self):
        return self.path.split("?")[0].rstrip("/") or "/"

    def do_OPTIONS(self):
        self.send_response(200); self._cors(); self.end_headers()

    # ── GET ───────────────────────────────────────────────────────────────

    def do_GET(self):
        path = self.p()

        if path in ("/", "/admin"):
            self.send_html(_admin_page()); return

        if path == "/api/status":
            cfg = _load_config()
            mgrs= _load_managers()
            ups = _load_uploads(cfg["current_turn"])
            # Build manager list with last upload timestamps
            managers_info = []
            for mid, mgr in mgrs.items():
                managers_info.append({
                    "manager_id": mid,
                    "manager_name": mgr["manager_name"],
                    "last_upload_timestamp": mgr.get("last_upload_timestamp", "—")
                })
            self.send_json({
                "current_turn"    : cfg["current_turn"],
                "turn_state"      : cfg["turn_state"],
                "total_managers"  : len(mgrs),
                "uploaded_count"  : len(ups),
                "managers"        : managers_info,
                "uploaded"        : [ups[m]["manager_name"] for m in ups],
                "not_uploaded"    : [mgrs[m]["manager_name"] for m in mgrs if m not in ups],
                "reset_count"     : cfg.get("reset_count", 0),
            }); return

        if path == "/api/newsletter":
            q        = self.qs()
            turn_num = int(q.get("turn", 0))
            if not turn_num:
                self.send_json({"success":False,"error":"turn required"}); return
            nl_path = os.path.join(_turn_dir(turn_num), "newsletter.txt")
            if not os.path.exists(nl_path):
                self.send_json({"success":False,"error":f"No newsletter for turn {turn_num}"}); return
            with open(nl_path,"r",encoding="utf-8") as _f:
                nl_text = _f.read()
            self.send_json({"success":True,"turn":turn_num,"newsletter":nl_text}); return

        if path == "/api/fight_log":
            q       = self.qs()
            turn_n  = int(q.get("turn",  0))
            fid     = int(q.get("fight_id", 0))
            mid     = q.get("manager_id", "")
            pw      = q.get("password", "")
            if not turn_n or not fid:
                self.send_json({"success":False,"error":"turn and fight_id required"}); return
            # Auth check — require valid manager credentials
            mgrs = _load_managers()
            if mid and pw:
                if mid not in mgrs or not _check_mgr_pw(mgrs[mid], pw):
                    self.send_json({"success":False,"error":"Not authorised."},401); return
            # Search all result files for this turn for the given fight_id
            td = _turn_dir(turn_n)
            narrative = None
            if os.path.exists(td):
                for fname in os.listdir(td):
                    if not fname.startswith("result_") or not fname.endswith(".json"):
                        continue
                    r = _load_json(os.path.join(td, fname), None)
                    if not r: continue
                    logs = r.get("fight_logs", {})
                    if str(fid) in logs:
                        narrative = logs[str(fid)]
                        break
            if narrative is None:
                self.send_json({"success":False,"error":f"Fight log {fid} not found for turn {turn_n}."},404); return
            self.send_json({"success":True,"narrative":narrative,"fight_id":fid,"turn":turn_n}); return

        if path == "/api/standings":
            cfg = _load_config()
            standings = _load_standings()
            # Filter warrior data based on feature flags
            filtered_standings = {}
            for mid, sd in standings.items():
                fsd = sd.copy()
                if "warriors" in fsd:
                    fsd["warriors"] = {
                        wname: _filter_warrior_for_client(ws, cfg)
                        for wname, ws in fsd["warriors"].items()
                    }
                filtered_standings[mid] = fsd
            self.send_json(filtered_standings); return

        if path == "/api/progress":
            self.send_json(_turn_progress); return

        if path == "/api/flags":
            cfg = _load_config()
            self.send_json({
                "success"              : True,
                "show_favorite_weapon" : cfg.get("show_favorite_weapon", False),
                "show_luck_factor"     : cfg.get("show_luck_factor",     False),
                "show_max_hp"          : cfg.get("show_max_hp",          False),
                "ai_teams_enabled"     : cfg.get("ai_teams_enabled",     True),
            }); return

        if path == "/api/schedule":
            cfg = _load_config()
            self.send_json({
                "success"          : True,
                "schedule_enabled" : cfg.get("schedule_enabled", False),
                "schedule_day"     : cfg.get("schedule_day",     "Friday"),
                "schedule_time"    : cfg.get("schedule_time",    "20:00"),
            }); return

        if path == "/api/results":
            q  = self.qs()
            mid= q.get("manager_id","")
            pw = q.get("password","")
            mgrs = _load_managers()
            if mid not in mgrs:
                self.send_json({"success":False,"error":"Manager not found. Register first."}, 404); return
            if not _check_mgr_pw(mgrs[mid], pw):
                self.send_json({"success":False,"error":"Wrong password."}, 401); return
            cfg = _load_config()
            res_turn = cfg["current_turn"] - 1
            if res_turn < 1:
                self.send_json({"success":False,"error":"No completed turns yet."}, 404); return
            # Collect ALL result files for this manager (one per uploaded team)
            td = _turn_dir(res_turn)
            team_results = []
            if os.path.exists(td):
                for fname in sorted(os.listdir(td)):
                    if fname.startswith(f"result_{mid}") and fname.endswith(".json"):
                        r = _load_json(os.path.join(td, fname), None)
                        if r:
                            # Strip only fight_logs (large narratives ~7KB each).
                            # Keep fight_history on warriors (~230 bytes/entry) --
                            # the client needs it for the Fights tab and View Fight.
                            r_slim = {k: v for k, v in r.items() if k != "fight_logs"}
                            team_results.append(r_slim)
            if not team_results:
                self.send_json({"success":False,"error":"No results found for your manager this turn."}); return
            # Include newsletter for this turn if available
            nl_text = ""
            nl_path = os.path.join(_turn_dir(res_turn), "newsletter.txt")
            if os.path.exists(nl_path):
                with open(nl_path, "r", encoding="utf-8") as _nf:
                    nl_text = _nf.read()
            # Filter results based on feature flags
            team_results = _filter_results_for_client(team_results, cfg)
            # Newsletter is served separately via /api/newsletter?turn=N
            # to keep /api/results payload small and avoid Windows socket aborts
            self.send_json({"success":True,"results":team_results,
                            "turn":res_turn,"has_newsletter":bool(nl_text)}); return

        if path == "/api/admin":
            q  = self.qs()
            cfg= _load_config()
            if not _check_host_pw(cfg, q.get("host_password","")):
                self.send_json({"success":False,"error":"Not authorised."}, 401); return
            mgrs = _load_managers()
            ups  = _load_uploads(cfg["current_turn"])
            self.send_json({
                "success":True, "config":cfg, "managers":mgrs,
                "uploads":{m:{"manager_name":u["manager_name"],"uploaded_at":u.get("uploaded_at")} for m,u in ups.items()},
                "standings":_load_standings(),
            }); return

        self.send_json({"error":"Not found."}, 404)

    # ── POST ──────────────────────────────────────────────────────────────

    def do_POST(self):
        path = self.p()
        b    = self.body()

        if path == "/api/register":
            mname = (b.get("manager_name") or "").strip()
            pw    = (b.get("password")     or "").strip()
            if not mname or not pw:
                self.send_json({"success":False,"error":"manager_name and password required."}); return
            if len(pw) < 4:
                self.send_json({"success":False,"error":"Password must be at least 4 characters."}); return
            with _lock:
                mgrs = _load_managers()
                if any(m["manager_name"].lower()==mname.lower() for m in mgrs.values()):
                    self.send_json({"success":False,"error":"Manager name already taken."}); return
                import uuid
                mid  = str(uuid.uuid4())[:8]
                salt = secrets.token_hex(16)
                mgrs[mid] = {"manager_name":mname,"salt":salt,
                             "password_hash":_hash_pw(pw,salt),
                             "registered_at":time.strftime("%Y-%m-%d %H:%M:%S")}
                _save_managers(mgrs)
            self.send_json({"success":True,"manager_id":mid,"manager_name":mname}); return

        if path == "/api/upload":
            mid   = (b.get("manager_id") or "").strip()
            pw    = (b.get("password")   or "").strip()
            team  = b.get("team")
            if not all([mid, pw, team]):
                self.send_json({"success":False,"error":"manager_id, password and team required."}); return
            with _lock:
                mgrs = _load_managers()
                if mid not in mgrs:
                    self.send_json({"success":False,"error":"Manager not found. Register first."}); return
                if not _check_mgr_pw(mgrs[mid], pw):
                    self.send_json({"success":False,"error":"Wrong password."}); return
                cfg = _load_config()
                if cfg["turn_state"] == "processing":
                    # Safety: if stuck in processing for more than 10 minutes, auto-recover
                    import datetime as _dt
                    started = cfg.get("processing_started_at","")
                    stuck = False
                    if started:
                        try:
                            elapsed = (_dt.datetime.now() - _dt.datetime.fromisoformat(started)).seconds
                            stuck = elapsed > 600  # 10 minutes
                        except Exception:
                            stuck = True
                    if not stuck:
                        self.send_json({"success":False,"error":"Turn is running. Try again shortly."}); return
                    # Auto-recover from stuck state
                    print("  WARNING: turn_state was stuck as 'processing' — auto-recovering.")
                    cfg["turn_state"] = "open"; _save_config(cfg)
                if cfg["turn_state"] == "results_ready":
                    cfg["turn_state"] = "open"; _save_config(cfg)
                turn_num = cfg["current_turn"]
                team_id  = team.get("team_id", "") if isinstance(team, dict) else ""
                upload_time = time.strftime("%Y-%m-%d %H:%M:%S")
                _save_upload(turn_num, mid, {
                    "manager_id"  : mid,
                    "manager_name": mgrs[mid]["manager_name"],
                    "team_id"     : team_id,
                    "team"        : team,
                    "uploaded_at" : upload_time,
                })
                # Update manager's last_upload_timestamp for tracking
                mgrs[mid]["last_upload_timestamp"] = upload_time
                _save_managers(mgrs)
            self.send_json({"success":True,"turn":turn_num,
                            "message":f"Team uploaded for turn {turn_num}."}); return

        if path == "/api/run_turn":
            rerun = b.get("rerun_turn")
            self.send_json(_run_turn(b.get("host_password",""),
                                     rerun_turn=int(rerun) if rerun else None)); return

        if path == "/api/arena/reset":
            cfg = _load_config()
            if not _check_host_pw(cfg, b.get("host_password","")):
                self.send_json({"success":False,"error":"Not authorised."}); return
            import shutil
            for entry in os.listdir(LEAGUE_DIR):
                full = os.path.join(LEAGUE_DIR, entry)
                if entry.startswith("turn_") and os.path.isdir(full):
                    shutil.rmtree(full)
            ai_file = os.path.join(LEAGUE_DIR, "ai_teams.json")
            if os.path.exists(ai_file): os.remove(ai_file)
            cfg["current_turn"] = 1; cfg["turn_state"] = "open"; cfg["fight_counter"] = 0
            cfg["reset_count"] = cfg.get("reset_count", 0) + 1
            _save_config(cfg)
            self.send_json({"success":True,"message":"League reset to turn 1."}); return

        if path == "/api/admin/update":
            cfg = _load_config()
            if not _check_host_pw(cfg, b.get("host_password","")):
                self.send_json({"success":False,"error":"Not authorised."}, 401); return
            # Update feature flags
            for bool_key in ("show_favorite_weapon", "show_luck_factor",
                             "show_max_hp", "ai_teams_enabled", "schedule_enabled"):
                if bool_key in b:
                    cfg[bool_key] = bool(b[bool_key])
            # Update schedule settings
            if "schedule_day" in b:
                valid_days = ("Sunday","Monday","Tuesday","Wednesday",
                              "Thursday","Friday","Saturday")
                day = b["schedule_day"]
                if day in valid_days:
                    cfg["schedule_day"] = day
            if "schedule_time" in b:
                # Validate HH:MM format
                import re as _re
                if _re.match(r"^\d{2}:\d{2}$", str(b["schedule_time"])):
                    cfg["schedule_time"] = b["schedule_time"]
            _save_config(cfg)
            self.send_json({"success":True,"message":"Config updated.","config":cfg}); return

        if path == "/api/shutdown":
            # Browser closed or admin requested shutdown
            self.send_json({"success": True, "message": "Shutting down..."})
            # Schedule shutdown for after response is sent
            threading.Timer(0.5, self._shutdown_server).start()
            return

        self.send_json({"error":"Not found."}, 404)


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="BLOODSPIRE League Server")
    parser.add_argument("--host-password", required=True,
                        help="Password for host admin access and running turns")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    _ensure_dirs()
    cfg  = _load_config()
    salt = cfg.get("host_password_salt") or secrets.token_hex(16)
    cfg["host_password_salt"] = salt
    cfg["host_password_hash"] = _hash_pw(args.host_password, salt)
    _save_config(cfg)

    # Use a threading server so GET requests (results, status, etc.) are handled
    # concurrently while a turn is running — prevents 10053 socket abort on Windows
    class ThreadedLeagueServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True   # threads die with the server process

    server = ThreadedLeagueServer(("0.0.0.0", args.port), LeagueHandler)
    _global_server = server
    url    = f"http://localhost:{args.port}"

    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║     BLOODSPIRE LEAGUE SERVER                 ║")
    print("  ╚══════════════════════════════════════════════╝")
    print(f"\n  Admin panel :  {url}/admin")
    print(f"  Player URL  :  http://YOUR_LAN_IP:{args.port}")
    print(f"  Current turn:  {cfg['current_turn']}")
    print(f"\n  ⚠  Share your LAN/public IP, not 'localhost', with other players.")
    print(f"  ⚠  Forward port {args.port} on your router for internet play.\n")

    threading.Timer(0.8, lambda: webbrowser.open(f"{url}/admin")).start()

    # ── Auto-scheduler thread ──────────────────────────────────────────────
    # Checks every minute whether a scheduled turn should fire.
    _DAYS = ("Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday")

    def _scheduler():
        import datetime as _dt
        _last_fired_turn = None  # prevent double-fire within the same minute
        while True:
            time.sleep(30)
            try:
                cfg = _load_config()
                if not cfg.get("schedule_enabled", False):
                    continue
                if cfg.get("turn_state") in ("processing",):
                    continue  # already running
                day_target  = cfg.get("schedule_day",  "Friday")
                time_target = cfg.get("schedule_time", "20:00")
                now = _dt.datetime.now()
                cur_day  = now.strftime("%A")          # e.g. "Friday"
                cur_time = now.strftime("%H:%M")       # e.g. "20:00"
                cur_turn = cfg.get("current_turn", 1)
                if (cur_day == day_target
                        and cur_time == time_target
                        and _last_fired_turn != cur_turn):
                    print(f"\n  [scheduler] Auto-running turn {cur_turn} "
                          f"({day_target} {time_target})")
                    _last_fired_turn = cur_turn
                    # Run in a separate thread so the scheduler loop continues
                    threading.Thread(
                        target=_run_turn,
                        args=(args.host_password,),
                        daemon=True,
                    ).start()
            except Exception as _se:
                print(f"  [scheduler] Error: {_se}")

    threading.Thread(target=_scheduler, daemon=True, name="bp-scheduler").start()
    # ──────────────────────────────────────────────────────────────────────

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  League server stopped.")

if __name__ == "__main__":
    main()
