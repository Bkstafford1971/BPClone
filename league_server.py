#!/usr/bin/env python3
# =============================================================================
# league_server.py — Blood Pit League Server
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
import sys
import threading
import time
import webbrowser
from typing import Optional

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
LEAGUE_DIR   = os.path.join(BASE_DIR, "saves", "league")
DEFAULT_PORT = 8766
sys.path.insert(0, BASE_DIR)

_lock = threading.Lock()


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
    return _load_json(_config_path(), {
        "current_turn": 1,
        "turn_state": "open",
        "host_password_hash": "",
        "host_password_salt": "",
        "fight_counter": 0,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    })

def _save_config(cfg):   _save_json(_config_path(), cfg)
def _load_managers():    return _load_json(_managers_path(), {})
def _save_managers(m):   _save_json(_managers_path(), m)
def _load_standings():   return _load_json(_standings_path(), {})
def _save_standings(s):  _save_json(_standings_path(), s)

def _load_uploads(turn_num):
    td = _turn_dir(turn_num)
    result = {}
    for fname in os.listdir(td):
        if fname.startswith("upload_") and fname.endswith(".json"):
            mid = fname[len("upload_"):-len(".json")]
            result[mid] = _load_json(os.path.join(td, fname), None)
    return {k: v for k, v in result.items() if v}

def _save_upload(turn_num, manager_id, data):
    _save_json(os.path.join(_turn_dir(turn_num), f"upload_{manager_id}.json"), data)

def _load_result(turn_num, manager_id):
    return _load_json(os.path.join(_turn_dir(turn_num), f"result_{manager_id}.json"), None)

def _save_result(turn_num, manager_id, data):
    _save_json(os.path.join(_turn_dir(turn_num), f"result_{manager_id}.json"), data)


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


# =============================================================================
# FIGHT RUNNER
# =============================================================================

def _run_turn(request_password):
    with _lock:
        cfg = _load_config()
        if not _check_host_pw(cfg, request_password):
            return {"success": False, "error": "Not authorised."}
        if cfg["turn_state"] == "processing":
            return {"success": False, "error": "Turn is already running."}
        turn_num = cfg["current_turn"]
        uploads  = _load_uploads(turn_num)
        if not uploads:
            return {"success": False, "error": "No teams have uploaded."}
        cfg["turn_state"] = "processing"
        _save_config(cfg)

    from team        import Team
    from matchmaking import build_fight_card
    from combat      import run_fight

    # Lightweight duck-type rival wrapper (no need for full RivalManager)
    class _Rival:
        def __init__(self, mid, mname, team):
            self.manager_id   = mid
            self.manager_name = mname
            self.team_name    = team.team_name
            self.team         = team
            self.tier         = 3

    # Pre-deserialise all uploaded teams once
    rival_map = {}
    for mid, upload in uploads.items():
        try:
            team = Team.from_dict(upload["team"])
            team.manager_name = upload["manager_name"]
            rival_map[mid] = _Rival(mid, upload["manager_name"], team)
        except Exception as e:
            print(f"  WARN: could not load team for {upload.get('manager_name','?')}: {e}")

    cfg      = _load_config()
    all_results = {}

    for manager_id, upload in uploads.items():
        mname = upload["manager_name"]
        print(f"\n  [{mname}] processing fights...")
        try:
            player_team = Team.from_dict(upload["team"])
            player_team.manager_name = mname
        except Exception as e:
            print(f"  SKIP {mname}: {e}"); continue

        rivals = [r for mid, r in rival_map.items() if mid != manager_id]
        card   = build_fight_card(player_team, rivals)

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
            fid    = _next_fid(cfg)
            fight_logs[str(fid)] = result.narrative
            pw_won = result.winner is not None and result.winner.name == pw.name
            killed = result.loser_died and pw_won
            slain  = result.loser_died and not pw_won
            pwr    = "win" if pw_won else "loss"

            pw.fight_history.append({
                "turn": turn_num, "opponent_name": ow.name,
                "opponent_race": ow.race.name, "opponent_team": bout.opponent_team.team_name,
                "result": pwr, "minutes": result.minutes_elapsed, "fight_id": fid,
                "warrior_slain": slain, "opponent_slain": killed, "is_kill": killed,
            })
            if slain:
                player_team.kill_warrior(pw, killed_by=ow.name, killer_fights=ow.total_fights)

            bouts.append({
                "warrior_name": pw.name, "opponent_name": ow.name,
                "opponent_race": ow.race.name, "opponent_team": bout.opponent_team.team_name,
                "opponent_manager": bout.opponent_manager, "fight_type": bout.fight_type,
                "result": pwr.upper(), "minutes": result.minutes_elapsed, "fight_id": fid,
                "warrior_slain": slain, "opponent_slain": killed,
                "training": result.training_results.get(pw.name, []),
            })

        mgr_res = {
            "turn": turn_num, "manager_name": mname,
            "bouts": bouts, "team": player_team.to_dict(), "fight_logs": fight_logs,
        }
        _save_result(turn_num, manager_id, mgr_res)
        all_results[manager_id] = mgr_res

    # Update standings
    standings = _load_standings()
    for mid, res in all_results.items():
        if mid not in standings:
            standings[mid] = {"manager_name": res["manager_name"], "turns_played": 0, "warriors": {}}
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

    with _lock:
        cfg["turn_state"]   = "results_ready"
        cfg["current_turn"] = turn_num + 1
        _save_config(cfg)

    total_fights = sum(len(r["bouts"]) for r in all_results.values())
    print(f"\n  Turn {turn_num} complete — {len(all_results)} manager(s), {total_fights} fight(s).")
    return {"success": True, "turn_number": turn_num,
            "managers": len(all_results), "fights": total_fights}


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

    # Upload status rows
    urows = ""
    for mid, mgr in managers.items():
        up = uploads.get(mid)
        badge = (f"<b style='color:#060'>✓ uploaded {up['uploaded_at']}</b>"
                 if up else "<span style='color:#800'>✗ not uploaded</span>")
        urows += f"<tr><td>{mgr['manager_name']}</td><td>{badge}</td></tr>"
    if not urows:
        urows = "<tr><td colspan=2 style='color:#888'>No managers registered yet</td></tr>"

    # Standings rows (sorted by wins)
    warriors_flat = []
    for mid, sd in standings.items():
        for wname, ws in sd.get("warriors", {}).items():
            warriors_flat.append({"mgr": sd["manager_name"], "name": wname, **ws})
    warriors_flat.sort(key=lambda x: (-x["wins"], x["losses"]))
    srows = "".join(
        f"<tr><td>{w['mgr']}</td><td>{w['name']}</td>"
        f"<td style='text-align:center'>{w['wins']}-{w['losses']}-{w['kills']}</td>"
        f"<td style='text-align:center'>{w['fights']}</td></tr>"
        for w in warriors_flat
    ) or "<tr><td colspan=4 style='color:#888'>No completed turns yet</td></tr>"

    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Blood Pit League — Admin</title>
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
 input{{border:2px inset #808080;padding:3px 6px;font-size:12px}}
 button{{background:#d4d0c8;border:2px solid;border-color:#fff #808080 #808080 #fff;
         padding:3px 14px;font-size:12px;cursor:pointer;margin-top:6px}}
 .state{{font-weight:bold;color:{sc.get(state,'#000')}}}
 #msg{{padding:6px 14px;margin:4px 0;display:none;font-size:12px}}
 .ok{{background:#cfc;border-left:4px solid #080}}
 .err{{background:#fcc;border-left:4px solid #800}}
</style></head><body>
<div class="bar">⚔ Blood Pit League — Admin
 <span>Turn {turn}</span>
 <span class="state">{state.replace("_"," ").upper()}</span>
 <span>{len(uploads)}/{len(managers)} uploaded</span>
</div>
<div id="msg"></div>
<div class="wrap">
 <div class="panel" style="min-width:240px;max-width:320px">
  <h3>Run Turn {turn}</h3>
  <p style="font-size:11px;color:#555;margin:0 0 6px">
   {len(uploads)} of {len(managers)} managers have uploaded.<br>
   Managers who haven't uploaded will be skipped.
  </p>
  Host password:<br>
  <input type="password" id="hp" style="width:180px"><br>
  <button onclick="runTurn()">▶ Run Turn {turn}</button>
 </div>
 <div class="panel">
  <h3>Upload Status — Turn {turn}</h3>
  <table><tr><th>Manager</th><th>Status</th></tr>{urows}</table>
 </div>
</div>
<div class="wrap">
 <div class="panel">
  <h3>Standings (Wins - Losses - Kills)</h3>
  <table><tr><th>Manager</th><th>Warrior</th><th>Record</th><th>Fights</th></tr>
  {srows}</table>
 </div>
</div>
<script>
async function runTurn(){{
 const pw=document.getElementById('hp').value;
 if(!pw){{show('Enter the host password first.','err');return;}}
 show('Running turn... this may take a minute.','ok');
 try{{
  const r=await fetch('/api/run_turn',{{method:'POST',
   headers:{{'Content-Type':'application/json'}},
   body:JSON.stringify({{host_password:pw}})}});
  const d=await r.json();
  if(d.success){{show(`Turn ${{d.turn_number}} complete — ${{d.managers}} manager(s), ${{d.fights}} fight(s). Reloading...`,'ok');
   setTimeout(()=>location.reload(),2500);}}
  else show('Error: '+d.error,'err');
 }}catch(e){{show('Connection error: '+e.message,'err');}}
}}
function show(t,c){{const m=document.getElementById('msg');m.textContent=t;m.className=c;m.style.display='block';}}
</script></body></html>"""


# =============================================================================
# HTTP HANDLER
# =============================================================================

class LeagueHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, *a): pass

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

    def send_html(self, html, status=200):
        body = html.encode()
        self.send_response(status)
        self.send_header("Content-Type",   "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

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
            self.send_json({
                "current_turn"    : cfg["current_turn"],
                "turn_state"      : cfg["turn_state"],
                "total_managers"  : len(mgrs),
                "uploaded_count"  : len(ups),
                "uploaded"        : [ups[m]["manager_name"] for m in ups],
                "not_uploaded"    : [mgrs[m]["manager_name"] for m in mgrs if m not in ups],
            }); return

        if path == "/api/standings":
            self.send_json(_load_standings()); return

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
            result = _load_result(res_turn, mid)
            if result is None:
                self.send_json({"success":False,"error":"No results found for your team this turn."}, 404); return
            self.send_json({"success":True,"result":result}); return

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
                    self.send_json({"success":False,"error":"Turn is running. Try again shortly."}); return
                if cfg["turn_state"] == "results_ready":
                    cfg["turn_state"] = "open"; _save_config(cfg)
                turn_num = cfg["current_turn"]
                _save_upload(turn_num, mid, {
                    "manager_id":mid,"manager_name":mgrs[mid]["manager_name"],
                    "team":team,"uploaded_at":time.strftime("%Y-%m-%d %H:%M:%S"),
                })
            self.send_json({"success":True,"turn":turn_num,
                            "message":f"Team uploaded for turn {turn_num}."}); return

        if path == "/api/run_turn":
            self.send_json(_run_turn(b.get("host_password",""))); return

        self.send_json({"error":"Not found."}, 404)


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Blood Pit League Server")
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

    server = http.server.HTTPServer(("0.0.0.0", args.port), LeagueHandler)
    url    = f"http://localhost:{args.port}"

    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║     BLOOD PIT LEAGUE SERVER                  ║")
    print("  ╚══════════════════════════════════════════════╝")
    print(f"\n  Admin panel :  {url}/admin")
    print(f"  Player URL  :  http://YOUR_LAN_IP:{args.port}")
    print(f"  Current turn:  {cfg['current_turn']}")
    print(f"\n  ⚠  Share your LAN/public IP, not 'localhost', with other players.")
    print(f"  ⚠  Forward port {args.port} on your router for internet play.\n")

    threading.Timer(0.8, lambda: webbrowser.open(f"{url}/admin")).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  League server stopped.")

if __name__ == "__main__":
    main()
