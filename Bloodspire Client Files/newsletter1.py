# =============================================================================
# newsletter.py — BLOODSPIRE Arena Newsletter Generator
# =============================================================================
import random, datetime
from typing import List, Optional

ARENA_NAME  = "Bloodspire Arena"
ARENA_ID    = 1
_NPC_TEAM_NAMES = {"The Monsters", "The Peasants"}
_NPC_RACES      = {"Monster", "Peasant"}

TIER_CHAMPION  = "CHAMPION"
TIER_ELITES    = "ELITES"
TIER_VETERANS  = "VETERANS"
TIER_ADEPTS    = "ADEPTS"
TIER_INITIATES = "INITIATES"
TIER_ROOKIES   = "ROOKIES"
TIER_RECRUITS  = "RECRUITS"


def _warrior_tier(w, is_champion: bool) -> str:
    if is_champion: return TIER_CHAMPION
    fights = getattr(w, "total_fights", 0)
    rec    = getattr(w, "recognition", 0)
    if fights <= 5: return TIER_RECRUITS
    if rec >= 67:   return TIER_ELITES
    if rec >= 57:   return TIER_VETERANS
    if rec >= 34:   return TIER_ADEPTS
    if rec >= 24:   return TIER_INITIATES
    if rec >= 0:    return TIER_ROOKIES
    return TIER_RECRUITS


def _update_champion(teams, champion_state: dict, deaths_this_turn: list,
                     champion_beaten_by: str = None, champion_beaten_team: str = None) -> dict:
    dead_names = {d["name"] for d in deaths_this_turn}
    if champion_beaten_by:
        return {"name": champion_beaten_by, "team_name": champion_beaten_team or "Unknown",
                "source": "beat_champion"}
    current_champ = champion_state.get("name", "")
    if current_champ and current_champ in dead_names:
        current_champ = ""
    if current_champ:
        return champion_state

    all_warriors = []
    for team in teams:
        tname = team.team_name if hasattr(team,"team_name") else team.get("team_name","?")
        if tname in _NPC_TEAM_NAMES: continue
        wlist = team.warriors if hasattr(team,"warriors") else team.get("warriors",[])
        for w in wlist:
            if not w: continue
            if hasattr(w,"name"): wobj=w
            else:
                from warrior import Warrior
                try:    wobj=Warrior.from_dict(w)
                except: continue
            if getattr(wobj,"is_dead",False): continue
            if wobj.name in dead_names: continue
            all_warriors.append((wobj, tname))

    if not all_warriors: return {}
    all_warriors.sort(key=lambda x: (-getattr(x[0],"recognition",0),
                                      -(x[0].wins/max(1,x[0].total_fights)),
                                      x[0].name, x[1]))
    champ_w, champ_t = all_warriors[0]
    return {"name": champ_w.name, "team_name": champ_t, "source": "recognition"}


def _get_warriors(w):
    if hasattr(w,"name"): return w
    from warrior import Warrior
    try:    return Warrior.from_dict(w)
    except: return None


def _is_npc_team(team) -> bool:
    name = team.team_name if hasattr(team,"team_name") else team.get("team_name","")
    return name in _NPC_TEAM_NAMES


def _fmt_date() -> str:
    return datetime.date.today().strftime("%m/%d/%Y")


# --------------------------------------------------------------------------- 
# HEADER
# --------------------------------------------------------------------------- 

def _header(turn_num: int, processed_date: str = None) -> str:
    return (f"Date: {processed_date or _fmt_date()}\n"
            f"{ARENA_NAME} ({ARENA_ID})\n"
            f"Turn - {turn_num}")


# --------------------------------------------------------------------------- 
# TEAM STANDINGS
# --------------------------------------------------------------------------- 

def _team_career_record(team) -> tuple:
    tw = tl = tk = 0
    tname = team.team_name if hasattr(team, "team_name") else team.get("team_name", "?")
    wlist = team.warriors if hasattr(team,"warriors") else team.get("warriors",[])
    for w in wlist:
        if not w: continue
        tw += getattr(w,"wins",0)   if hasattr(w,"wins")   else w.get("wins",0)
        tl += getattr(w,"losses",0) if hasattr(w,"losses") else w.get("losses",0)
        tk += getattr(w,"kills",0)  if hasattr(w,"kills")  else w.get("kills",0)
    active_tw, active_tl, active_tk = tw, tl, tk

    archived = (getattr(team,"archived_warriors",[])
                if hasattr(team,"archived_warriors")
                else team.get("archived_warriors",[]))
    for aw in archived:
        if not aw: continue
        tw += aw.get("wins",0)   if isinstance(aw,dict) else getattr(aw,"wins",0)
        tl += aw.get("losses",0) if isinstance(aw,dict) else getattr(aw,"losses",0)
        tk += aw.get("kills",0)  if isinstance(aw,dict) else getattr(aw,"kills",0)

    return tw, tl, tk


def _team_standings(teams, turn_num: int) -> str:
    rows = []
    for team in teams:
        if _is_npc_team(team): continue
        name = team.team_name if hasattr(team,"team_name") else team.get("team_name","?")
        tid  = team.team_id   if hasattr(team,"team_id")   else team.get("team_id",0)
        hist = getattr(team,"turn_history",[]) if hasattr(team,"turn_history") else team.get("turn_history",[])
        tw, tl, tk = _team_career_record(team)
        tf=tw+tl; pct=(tw/tf*100) if tf else 0.0
        last5=hist[-5:] if hist else []
        l5w=sum(h.get("w",0) for h in last5)
        l5l=sum(h.get("l",0) for h in last5)
        l5k=sum(h.get("k",0) for h in last5)
        rows.append({"name":name,"id":tid,"w":tw,"l":tl,"k":tk,"pct":pct,
                     "l5w":l5w,"l5l":l5l,"l5k":l5k})
    rows.sort(key=lambda r:(-r["pct"],-(r["w"])))
    rows_l5=sorted(rows,key=lambda r:(-(r["l5w"]+r["l5k"]),r["l5l"]))

    SEP = "="*100
    HDR = (f"{'#':<5}{'CAREER STANDINGS':<28}{'W':>4}{'L':>4}{'K':>4}{'%':>7}"
           f"   {'#':<5}{'LAST 5 TURNS':<28}{'W':>4}{'L':>4}{'K':>4}")
    lines=["\nThe Top Teams\n", HDR, SEP]
    for i,(r,r5) in enumerate(zip(rows,rows_l5),1):
        cname  = f" {r['name'][:22]} ({r['id']})"[:28]
        c5name = f" {r5['name'][:22]} ({r5['id']})"[:28]
        career = f"{i:<5}{cname:<28}{r['w']:>4}{r['l']:>4}{r['k']:>4}{r['pct']:>6.1f}%"
        last5s = f"   {i:<5}{c5name:<28}{r5['l5w']:>4}{r5['l5l']:>4}{r5['l5k']:>4}"
        lines.append(career + last5s)
    return "\n".join(lines)


# --------------------------------------------------------------------------- 
# WARRIOR TIERS
# --------------------------------------------------------------------------- 

def _warrior_tiers(teams, champion_state: dict) -> str:
    champ_name=champion_state.get("name","")
    tiers={t:[] for t in [TIER_CHAMPION,TIER_ELITES,TIER_VETERANS,TIER_ADEPTS,
                           TIER_INITIATES,TIER_ROOKIES,TIER_RECRUITS]}
    for team in teams:
        if _is_npc_team(team): continue
        tname=team.team_name if hasattr(team,"team_name") else team.get("team_name","?")
        tid  =team.team_id   if hasattr(team,"team_id")   else team.get("team_id",0)
        wlist=team.warriors  if hasattr(team,"warriors")  else team.get("warriors",[])
        for w in wlist:
            if not w: continue
            wobj=_get_warriors(w)
            if not wobj: continue
            if getattr(wobj,"is_dead",False): continue
            rname=wobj.race.name if hasattr(wobj.race,"name") else "Human"
            if rname in _NPC_RACES: continue
            if getattr(wobj,"total_fights",0) == 0: continue
            tiers[_warrior_tier(wobj,wobj.name==champ_name)].append({
                "name":wobj.name,"team":tname,"tid":tid,
                "w":wobj.wins,"l":wobj.losses,"k":wobj.kills,
                "rec":getattr(wobj,"recognition",0),
            })
    SEP = "="*70
    COL_HDR = f"{'NAME':<22}{'W':>4}{'L':>4}{'K':>4}  {'REC':>3}  TEAM"
    sections=[]
    for tier in [TIER_CHAMPION,TIER_ELITES,TIER_VETERANS,TIER_ADEPTS,TIER_INITIATES,TIER_ROOKIES,TIER_RECRUITS]:
        wlist=tiers[tier]
        if not wlist and tier==TIER_CHAMPION:
            sections.append(f"\n{tier}\n{COL_HDR}\n{SEP}\n  (vacant this turn)"); continue
        if not wlist: continue
        wlist.sort(key=lambda x:(-x["rec"],-(x["w"]/max(1,x["w"]+x["l"]))))
        lines=[f"\n{tier}\n{COL_HDR}",SEP]
        for wd in wlist:
            tm=f"{wd['team'][:22]} ({wd['tid']})"
            lines.append(f"{wd['name'][:22]:<22}{wd['w']:>4}{wd['l']:>4}{wd['k']:>4}"
                         f"  {wd['rec']:>3}  {tm}")
        sections.append("\n".join(lines))
    return "\n".join(sections)+"\n'-' denotes a warrior who did not fight this turn."


# --------------------------------------------------------------------------- 
# DEAD / FIGHTS / RACE REPORT
# --------------------------------------------------------------------------- 

def _dead_section(deaths: list, turn_num: int) -> str:
    if not deaths: return ""
    sep="="*75
    lines=["\nTHE DEAD",
           f"{'NAME':<22}{'W':>4}{'L':>4}{'K':>4}  {'TEAM':<24}{'SLAIN BY':<22}{'TURN':>5}",sep]
    for d in deaths:
        name = d['name'][:22]
        team = d.get('team','?')[:24]
        slain = d.get('killed_by','?')[:22]
        lines.append(f"{name:<22}{d.get('w',0):>4}{d.get('l',0):>4}{d.get('k',0):>4}"
                     f"  {team:<24}{slain:<22}{turn_num:>5}")
    return "\n".join(lines)


def _fights_section(card) -> str:
    sep="="*75
    lines=["\nLAST TURN'S FIGHTS",sep]
    _order = {"monster":0,"champion":1,"blood_challenge":2,"challenge":2,"rivalry":3,"peasant":4}
    sorted_card = sorted(card, key=lambda b: _order.get(getattr(b,"fight_type","rivalry"), 3))

    seen_pairs = set()
    for bout in sorted_card:
        pw=bout.player_warrior; ow=bout.opponent; r=bout.result
        if not r: continue
        pair = frozenset([pw.name, ow.name])
        if pair in seen_pairs: continue
        seen_pairs.add(pair)
        pw_won=r.winner and r.winner.name==pw.name
        winner=pw if pw_won else ow; loser=ow if pw_won else pw
        mins=r.minutes_elapsed
        ftype = "Champions Title" if bout.fight_type == "champion" else bout.fight_type.replace("_"," ")
        style=_fight_style_word(mins)
        if r.loser_died:
            line=(f"{winner.name} slew {loser.name} in a {mins} minute {style} {ftype} fight."
                  if pw_won else
                  f"{loser.name} was slain by {winner.name} in a {mins} minute {style} {ftype} fight.")
        else:
            verb=random.choice(["bested","defeated","outlasted","overcame","vanquished"])
            line=f"{winner.name} {verb} {loser.name} in a {mins} minute {style} {ftype} fight."
        lines.append(line)
    return "\n".join(lines)


def _fight_style_word(mins):
    if mins<=1: return random.choice(["swift","crushing","decisive","one-sided"])
    if mins<=3: return random.choice(["competent","solid","clean"])
    if mins>=8: return random.choice(["grueling","brutal","drawn-out","action-packed"])
    return random.choice(["spirited","hard-fought","contested"])


def _race_report(teams) -> str:
    from collections import defaultdict
    rf=defaultdict(int); rw=defaultdict(int); rl=defaultdict(int); rk=defaultdict(int)
    top={}
    for team in teams:
        if _is_npc_team(team): continue
        tname=team.team_name if hasattr(team,"team_name") else team.get("team_name","?")
        tid  =team.team_id   if hasattr(team,"team_id")   else team.get("team_id",0)
        for w in (team.warriors if hasattr(team,"warriors") else team.get("warriors",[])):
            if not w: continue
            wobj=_get_warriors(w)
            if not wobj: continue
            rname=wobj.race.name if hasattr(wobj.race,"name") else "Human"
            if rname in _NPC_RACES: continue
            rf[rname]+=wobj.total_fights
            rw[rname]+=wobj.wins; rl[rname]+=wobj.losses; rk[rname]+=wobj.kills
            score=wobj.wins*3+wobj.kills*2-wobj.losses
            if rname not in top or score>top[rname]["score"]:
                top[rname]={"warrior":wobj.name,"w":wobj.wins,"l":wobj.losses,
                             "k":wobj.kills,"team":tname,"tid":tid,"score":score}
    races=sorted(rf.keys(),key=lambda r:-rf[r])
    sep="="*75
    lines=["\n                      BATTLE REPORT\n",
           f"    {'MOST POPULAR RACE':<25}  {'RECORD DURING THE LAST 10 TURNS':>38}",sep,
           f"{'|RACE':<16}{'FIGHTS':>8}  {'RACE':<18}{'W':>5} - {'L':>4} - {'K':>4}  {'PERCENT':>7}|",sep]
    for race in races:
        tw=rw[race]; tl=rl[race]; tk=rk[race]; pct=int(tw/max(1,tw+tl)*100)
        lines.append(f"|{race:<16}{rf[race]:>8}  {race:<18}{tw:>5} - {tl:>4} - {tk:>4}  {pct:>6}%|")
    lines.append(sep)
    if top:
        lines.append("\n\n                      TOP WARRIOR by RACE\n")
        lines.append(f"{'RACE':<14}{'WARRIOR':<26}{'W':>4}{'L':>4}{'K':>3}  TEAM NAME"); lines.append(sep)
        for race in races:
            if race in top:
                td=top[race]
                lines.append(f"{race:<14}{td['warrior']:<26}{td['w']:>4}{td['l']:>4}{td['k']:>3}"
                              f"  {td['team']} ({td['tid']})")
    return "\n".join(lines)


# --------------------------------------------------------------------------- 
# UPDATED TEMPLATE POOLS — Better match your desired style
# --------------------------------------------------------------------------- 

_BLK_BYLINES = [
    "Dax Ironquill, Bloodspire Gazette",
    "Mira Coldtongue, The Blood Ledger",
    "Horst Veyne, Pit Press Weekly",
    "Snide Clemens, Arena Correspondent",
    "Alarond the Scribe",
    "The Unknown Spymaster",
    "Olaf Modeen, Retired Correspondent",
    "Bryndis Coldquill, Arena Correspondent",
    "Magistra Pellwood, Official Chronicle",
    "Aldric Fenworth, Bloodspire Gazette",
]

_BLK_INTRO = [
    "Another turn has passed in {arena}, and the dust still hangs heavy where blades met bone. Victories were earned, pride was lost, and more than one plan failed the moment steel left its scabbard. As always, the arena cared little for intent. Only outcomes.",
    "If hope walked into {arena} this turn, it didn't leave intact. Managers talked big, warriors listened poorly, and the standings now tell the truth no one wanted to hear. Let's go over who impressed — and who shouldn't bother pretending.",
    "Hear me now! {arena} thundered beneath the weight of ambition this turn, and the ambitious were sorted from the foolish with ruthless clarity. Songs will exaggerate what happened here — but not by much.",
    "I heard three versions of this turn at {venue}, and every one got louder with each drink. Somewhere between the boasting and the lies is what really happened in {arena}. Lucky for you, I paid attention.",
]

_BLK_TEAM_PERF = [
    "{team} walked into the turn with questions and walked out with answers. Their {record} showing pushed them {rank_change} in the standings, built on decisions that held up under pressure. Others noticed — and adjusted accordingly.",
    "For {team}, the turn was uneven but instructive. A {record} doesn't tell the whole story, but it does explain the current position in the rankings. Progress was made, even if confidence was shaken.",
    "Nothing came easily for {team} this turn, and most things went wrong. Their {record} reflected hesitant choices and punishment delivered on schedule. Lessons were taught — whether anyone learned them remains to be seen.",
    "{team} didn't dominate this turn, but they endured it. Their {record} reflects hard choices made under pressure, and the standings rewarded resolve over spectacle. In {arena}, that distinction matters more often than most admit.",
]

_BLK_CHAMP_HOLDS = [
    "{champion} remains atop {arena}, not through spectacle, but through consistency. Another turn passed without a successful challenge, reinforcing a reign built on reliability rather than luck.",
    "Holding the top spot is harder than taking it, and {champion} demonstrated why. The throne remains occupied, and challengers are running out of excuses.",
    "Every schedule change and whispered plan still points toward {champion}. Until someone succeeds, intention remains irrelevant.",
]

_BLK_CHAMP_NEW = [
    "The crowds were amazed this turn, as {champion} of {champ_team} dethroned the reigning Champion in a fight that will be talked about for turns to come. A new name atop the throne.",
    "{champion} of {champ_team} has done what countless rivals only dreamed — claimed the Championship in direct combat. The arena has a new ruler, and the pretenders must recalculate.",
    "Stop the histories and note the date: {champion} of {champ_team} is the new Champion of {arena}. The old order ends. The new one has precisely one member.",
]

_BLK_CHAMP_VACANT = [
    "The Championship throne remains empty this turn. No warrior has yet met the criteria to claim it. Every manager with ambition should be watching their most recognised fighter closely.",
    "No Champion walks the arena floor this turn. The vacancy is an open invitation, and somewhere in {arena}, someone is already planning to answer it.",
]

_BLK_DEATH = [
    "{warrior} ({record}), a high-level warrior with significant recognition, was slain this turn.",
    "{warrior} ({record}), a promising young warrior with an impressive record, was cut down before reaching full potential.",
    "{warrior} ({record}) fell in the arena this turn.",
]

_BLK_OUTRO = [
    "That's the turn as it happened, not as it was advertised. Anyone unhappy with the outcome is welcome to try again. Results permitting. — {byline}",
    "The turn is done. The consequences remain. — {byline}",
    "The turn closes. The implications remain. Until Turn {next_turn} — {byline}",
    "I'll raise a glass to the survivors. The rest are beyond complaint. Until next time — {byline}",
]


def _pick_block(pool: list, used: set, ctx: dict) -> str:
    available = [b for b in pool if b not in used]
    if not available:
        available = list(pool)
    template = random.choice(available)
    used.add(template)
    return template.format(**ctx)


def _block_commentary(card, teams, deaths, turn_num: int, champion_state: dict) -> str:
    arena = ARENA_NAME.upper()
    venue = "Bloodspire"
    byline = random.choice(_BLK_BYLINES)

    team_records = {}
    for team in teams:
        if _is_npc_team(team): continue
        tname = team.team_name if hasattr(team, "team_name") else team.get("team_name", "?")
        w = l = k = 0
        for bout in card:
            if not bout.result: continue
            pw_won = bout.result.winner and bout.result.winner.name == bout.player_warrior.name
            if bout.player_team.team_name == tname:
                if pw_won: 
                    w += 1
                    if bout.result.loser_died: k += 1
                else: 
                    l += 1
            elif bout.opponent_team.team_name == tname:
                if not pw_won: 
                    w += 1
                    if bout.result.loser_died: k += 1
                else: 
                    l += 1
        team_records[tname] = {"w": w, "l": l, "k": k, "team": team}

    best_team = max(team_records.items(), key=lambda x: (x[1]["w"], -x[1]["l"])) if team_records else None

    champ_name = champion_state.get("name", "")
    champ_team = champion_state.get("team_name", "")
    champ_src  = champion_state.get("source", "")

    # Get champion's current record
    champ_record = ""
    if champ_name:
        for team in teams:
            if _is_npc_team(team): continue
            for w in (team.warriors if hasattr(team, "warriors") else team.get("warriors", [])):
                if not w: continue
                if hasattr(w, "name") and w.name == champ_name:
                    champ_record = f"({w.wins}-{w.losses}-{w.kills})"
                    break
                elif isinstance(w, dict) and w.get("name") == champ_name:
                    champ_record = f"({w.get('wins',0)}-{w.get('losses',0)}-{w.get('kills',0)})"
                    break
            if champ_record:
                break

    paragraphs = []

    # Opening
    intro = _pick_block(_BLK_INTRO, set(), {"arena": arena, "venue": venue, "turn": turn_num})
    paragraphs.append(intro)

    # Champion or top team
    if champ_src == "beat_champion" and champ_name:
        champ_line = _pick_block(_BLK_CHAMP_NEW, set(), {
            "champion": f"{champ_name.upper()} {champ_record}",
            "champ_team": champ_team.upper(), 
            "arena": arena
        })
        paragraphs.append(champ_line)
    elif champ_name:
        hold_line = f"{champ_name.upper()} {champ_record} of {champ_team.upper()} continues to reign as Arena Champion."
        paragraphs.append(hold_line)
    elif best_team:
        tname, rec = best_team
        record_str = f"{rec['w']}-{rec['l']}-{rec['k']}"
        ctx = {"team": tname.upper(), "record": record_str, "arena": arena}
        team_perf = _pick_block(_BLK_TEAM_PERF, set(), ctx)
        paragraphs.append(team_perf)

    # Warrior highlights
    top_warriors = []
    for bout in card:
        if not bout.result: continue
        pw = bout.player_warrior
        ow = bout.opponent
        pw_won = bout.result.winner and bout.result.winner.name == pw.name
        top_warriors.append((pw if pw_won else ow, pw_won))

    top_warriors.sort(key=lambda x: (-x[0].wins if hasattr(x[0],'wins') else 0, 
                                     -getattr(x[0],'recognition',0)))

    if top_warriors:
        hl = []
        for w, won in top_warriors[:3]:
            verb = "dominated" if won else "fought hard"
            line = f"{w.name.upper()} {verb} this turn"
            if hasattr(w, 'wins') and w.wins > 0:
                line += f", collecting {w.wins} win{'s' if w.wins > 1 else ''}"
            hl.append(line)
        if hl:
            paragraphs.append("  ".join(hl))

    # Challenge / avoidance
    challenge_counts = {}
    avoidance_counts = {}
    for bout in card:
        if bout.fight_type not in ["challenge", "blood_challenge"]: continue
        chal_name = bout.player_warrior.name
        challenged = bout.opponent_team.team_name
        challenge_counts[chal_name] = challenge_counts.get(chal_name, 0) + 1
        avoidance_counts[challenged] = avoidance_counts.get(challenged, 0) + 1

    most_challenged = max(challenge_counts, key=challenge_counts.get) if challenge_counts else None
    most_avoided = max(avoidance_counts, key=avoidance_counts.get) if avoidance_counts else None

    if most_challenged or most_avoided:
        parts = []
        if most_challenged:
            parts.append(f"{most_challenged.upper()} was the most challenged warrior this turn")
        if most_avoided and most_avoided not in _NPC_TEAM_NAMES:
            parts.append(f"{most_avoided.upper()} was the team most others chose to avoid")
        if parts:
            paragraphs.append("  ".join(parts))

    # Notable deaths with records
    if deaths:
        death_parts = []
        for d in deaths:
            name = d["name"].upper()
            record = f"{d.get('w',0)}-{d.get('l',0)}-{d.get('k',0)}"
            rec = d.get("rec", 0)
            fights = d.get("total_fights", 0)

            if rec >= 50 or fights >= 35:
                death_parts.append(f"{name} ({record}), a high-level warrior with significant recognition, was slain this turn.")
            elif fights >= 15 and d.get('w', 0) > d.get('l', 0) * 1.5:
                death_parts.append(f"{name} ({record}), a promising young warrior with an impressive record, was cut down before reaching full potential.")
            else:
                death_parts.append(f"{name} ({record}) fell in the arena this turn.")

        if death_parts:
            death_block = "  ".join(death_parts[:2])
            paragraphs.append(death_block)

    # Closing
    outro = _pick_block(_BLK_OUTRO, set(), {
        "arena": arena, "venue": venue, "byline": byline, "next_turn": turn_num + 1
    })
    paragraphs.append(outro)

    article = "\n\n".join(paragraphs)
    return "\n\nArena Happenings\n\n" + article


# --------------------------------------------------------------------------- 
# MAIN ENTRY POINT (unchanged except for calling the new function)
# --------------------------------------------------------------------------- 

def generate_newsletter(turn_num, card, teams, deaths, champion_state,
                        voice="snide", processed_date=None) -> str:
    sections = [_header(turn_num, processed_date)]
    sections.append(_team_standings(teams, turn_num))
    sections.append("\n\n" + _block_commentary(card, teams, deaths, turn_num, champion_state))
    sections.append("\n\n" + _warrior_tiers(teams, champion_state))
    dead = _dead_section(deaths, turn_num)
    if dead: sections.append("\n\n" + dead)
    sections.append("\n\n" + _fights_section(card))
    sections.append("\n\n" + _race_report(teams))
    return "\n".join(sections)