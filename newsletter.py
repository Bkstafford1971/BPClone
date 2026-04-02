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
    """Assign a warrior to a tier based on recognition rating (0-99).

    Champion: determined externally (is_champion flag)
    Elite:    67 - 99
    Veteran:  57 - 66
    Adept:    34 - 56
    Initiate: 24 - 33
    Rookie:   0  - 23
    Recruit:  <= 5 fights
    """
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
    # A warrior who beat the current champion claims the title immediately.
    if champion_beaten_by:
        return {"name": champion_beaten_by, "team_name": champion_beaten_team or "Unknown",
                "source": "beat_champion"}
    current_champ = champion_state.get("name", "")
    if current_champ and current_champ in dead_names:
        current_champ = ""
    if current_champ:
        return champion_state
    # No champion — find the warrior with the highest recognition score.
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
    # Sort by recognition (primary) then win percentage (tiebreak).
    all_warriors.sort(key=lambda x: (-getattr(x[0],"recognition",0),
                                      -(x[0].wins/max(1,x[0].total_fights)),
                                      x[0].name, x[1]))
    best_rec = getattr(all_warriors[0][0], "recognition", 0)
    tied     = [x for x in all_warriors if getattr(x[0],"recognition",0) == best_rec]
    if len(tied) > 1:
        best_pct = tied[0][0].wins / max(1, tied[0][0].total_fights)
        still    = [x for x in tied
                    if abs(x[0].wins/max(1,x[0].total_fights) - best_pct) < 0.001]
        if len(still) > 1:
            # Final tiebreak: alphabetical by name then team — deterministic, never a tie
            still.sort(key=lambda x: (x[0].name, x[1]))
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
    """
    Return cumulative (wins, losses, kills) for ALL warriors who have ever
    fought for this team: active warriors + dead-awaiting-replacement +
    archived (confirmed-replaced) warriors.
    """
    tw = tl = tk = 0
    tname = team.team_name if hasattr(team, "team_name") else team.get("team_name", "?")
    # Active + dead-awaiting-replacement — still in the warriors list
    wlist = team.warriors if hasattr(team,"warriors") else team.get("warriors",[])
    for w in wlist:
        if not w: continue
        tw += getattr(w,"wins",0)   if hasattr(w,"wins")   else w.get("wins",0)
        tl += getattr(w,"losses",0) if hasattr(w,"losses") else w.get("losses",0)
        tk += getattr(w,"kills",0)  if hasattr(w,"kills")  else w.get("kills",0)
    active_tw, active_tl, active_tk = tw, tl, tk
    # Archived warriors (replaced after death / retirement)
    archived = (getattr(team,"archived_warriors",[])
                if hasattr(team,"archived_warriors")
                else team.get("archived_warriors",[]))
    for aw in archived:
        if not aw: continue
        tw += aw.get("wins",0)   if isinstance(aw,dict) else getattr(aw,"wins",0)
        tl += aw.get("losses",0) if isinstance(aw,dict) else getattr(aw,"losses",0)
        tk += aw.get("kills",0)  if isinstance(aw,dict) else getattr(aw,"kills",0)
    print(f"  [career_record] {tname}: active={active_tw}-{active_tl}-{active_tk} "
          f"archived={len(archived)} total={tw}-{tl}-{tk}")
    return tw, tl, tk


def _team_standings(teams, turn_num: int) -> str:
    rows = []
    for team in teams:
        if _is_npc_team(team): continue
        name = team.team_name if hasattr(team,"team_name") else team.get("team_name","?")
        tid  = team.team_id   if hasattr(team,"team_id")   else team.get("team_id",0)
        hist = getattr(team,"turn_history",[]) if hasattr(team,"turn_history") else team.get("turn_history",[])
        # Cumulative career record (all warriors ever on this team)
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

    # Fixed column widths — total line ~100 chars
    # Career side: rank(5) + name(28) + W(4) + L(4) + K(4) + %(7) = 52
    # Last5 side:  rank(5) + name(28) + W(4) + L(4) + K(4) = 45
    SEP = "="*100
    HDR = (f"{'#':<5}{'CAREER STANDINGS':<28}{'W':>4}{'L':>4}{'K':>4}{'%':>7}"
           f"   {'#':<5}{'LAST 5 TURNS':<28}{'W':>4}{'L':>4}{'K':>4}")
    lines=["\nThe Top Teams\n", HDR, SEP]
    for i,(r,r5) in enumerate(zip(rows,rows_l5),1):
        # Truncate name+id to exactly 28 chars
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
            tiers[_warrior_tier(wobj,wobj.name==champ_name)].append({
                "name":wobj.name,"team":tname,"tid":tid,
                "w":wobj.wins,"l":wobj.losses,"k":wobj.kills,
                "rec":getattr(wobj,"recognition",0),
            })
    SEP = "="*70
    # Fixed columns: name(22) + W(4) + L(4) + K(4) + Rec(4) + team
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
    # Monster fights first, then rivalry/challenge, then peasant
    _order = {"monster":0,"blood_challenge":1,"challenge":1,"rivalry":2,"peasant":3}
    sorted_card = sorted(card, key=lambda b: _order.get(getattr(b,"fight_type","rivalry"), 2))

    # Deduplicate: collapse A-vs-B and B-vs-A to one line.
    # Named (non-NPC) warriors may only appear once — peasants/monsters are exempt.
    seen_pairs = set()
    seen_warriors = set()
    for bout in sorted_card:
        pw=bout.player_warrior; ow=bout.opponent; r=bout.result
        if not r: continue
        pair = frozenset([pw.name, ow.name])
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        pt_name = (bout.player_team.team_name
                   if hasattr(bout, "player_team") and bout.player_team
                   else "")
        ot_name = (bout.opponent_team.team_name
                   if hasattr(bout, "opponent_team") and bout.opponent_team
                   else "")
        pw_is_npc = pt_name in _NPC_TEAM_NAMES
        ow_is_npc = ot_name in _NPC_TEAM_NAMES
        if not pw_is_npc and (pt_name, pw.name) in seen_warriors:
            continue
        if not ow_is_npc and (ot_name, ow.name) in seen_warriors:
            continue
        if not pw_is_npc:
            seen_warriors.add((pt_name, pw.name))
        if not ow_is_npc:
            seen_warriors.add((ot_name, ow.name))
        pw_won=r.winner and r.winner.name==pw.name
        winner=pw if pw_won else ow; loser=ow if pw_won else pw
        mins=r.minutes_elapsed; ftype=bout.fight_type.replace("_"," ")
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
# ARENA HAPPENINGS — modular narrative block libraries
# ---------------------------------------------------------------------------
# Each pool holds 10 variant templates.  Variables available in every block:
#   {arena}       Full arena name, uppercase  (BLOODSPIRE ARENA)
#   {venue}       Short venue name            (Bloodspire)
#   {byline}      Reporter name
#   {turn}        Current turn number
#   {next_turn}   Next turn number
#   {team}        Primary team name, uppercase
#   {team2}       Secondary team name, uppercase
#   {record}      W-L-K string for the turn
#   {rank_change} Descriptive movement phrase
#   {warrior}     Warrior name, uppercase
#   {opponent}    Opponent name, uppercase
#   {points}      Warrior's current recognition score
#   {champion}    Champion name, uppercase
#   {champ_team}  Champion's team name, uppercase

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
    "Another turn has passed in {arena}, and the dust still hangs heavy where blades met bone.  Victories were earned, pride was lost, and more than one plan failed the moment steel left its scabbard.  As always, the arena cared little for intent — only outcomes.",
    "If hope walked into {arena} this turn, it didn't leave intact.  Managers talked big, warriors listened poorly, and the standings now tell the truth no one wanted to hear.  Let's go over who impressed — and who shouldn't bother pretending.",
    "Hear me now!  {arena} thundered beneath the weight of ambition this turn, and the ambitious were sorted from the foolish with ruthless clarity.  Songs will exaggerate what happened here — but not by much.",
    "I heard three versions of this turn at {venue}, and every one got louder with each drink.  Somewhere between the boasting and the lies is what really happened in {arena}.  Lucky for you, I paid attention.",
    "The turn began like any other and ended exactly as it had to in {arena}.  Some rose, some fell, and fate collected its due without apology.  Let's read the damage.",
    "{arena} doesn't announce when it's about to teach someone a lesson.  It just waits for confidence to turn into error.  This turn was no exception.",
    "Another turn came and went in {arena}, leaving the standings rearranged and several reputations in urgent need of explanation.  Tradition holds firm.",
    "Managers entered this turn with plans.  Warriors entered with steel.  Only one of those things survived contact with reality in {arena}.",
    "{arena} woke hungry this turn, and it was fed without restraint.  What follows are the names of those who satisfied it — and those who regretted trying.",
    "I have seen many turns in many places, and {arena} remains uniquely honest.  It rewards preparation, punishes pride, and forgets quickly.",
]

_BLK_TEAM_PERF = [
    "{team} walked into the turn with questions and walked out with answers.  Their {record} showing pushed them {rank_change} in the standings, built on decisions that held up under pressure.  Others noticed — and adjusted accordingly.",
    "For {team}, the turn was uneven but instructive.  A {record} doesn't tell the whole story, but it does explain the current position in the rankings.  Progress was made, even if confidence was shaken.",
    "{team} somehow turned a {record} into upward movement, which says more about the competition than the performance.  The standings reward survival as much as excellence, and this turn favored the merely adequate.",
    "Nothing came easily for {team} this turn, and most things went wrong.  Their {record} reflected hesitant choices and punishment delivered on schedule.  Lessons were taught — whether anyone learned them remains to be seen.",
    "{team} didn't dominate this turn, but they endured it.  Their {record} reflects hard choices made under pressure, and the standings rewarded resolve over spectacle.  In {arena}, that distinction matters more often than most admit.",
    "{team} avoided spectacle and focused on execution this turn.  The resulting {record} pushed them {rank_change}, a reminder that consistency still matters here.",
    "The standings record {team}'s {record}, but it's the confidence that followed which concerns rival managers.  Momentum, once earned, is difficult to interrupt.",
    "{team} will likely cite matchups, luck, or scheduling after their {record} this turn.  The rankings, unfortunately, only record outcomes.",
    "It wasn't pretty, but {team} emerged intact with a {record} showing.  In {arena}, survival buys time — and time buys improvement.",
    "Something changed for {team} this turn.  Whether the {record} marks the beginning of a rise or a brief correction remains to be seen.",
]

_BLK_WARRIOR_HI = [
    "{warrior} left little to debate after facing {opponent}.  The fight was decisive, the outcome clearer by the moment, and {points} recognition to their name.  That performance will linger in memory longer than the scars.",
    "Confidence led {warrior} into the arena this turn against {opponent}, and confidence alone proved insufficient.  The loss stung, both in pride and standing, but harsh lessons tend to last longer than easy wins.",
    "Preparation paid off when {warrior} stepped into the arena this turn.  Against {opponent}, patience and timing proved more dangerous than brute force, earning quiet respect from those paying attention.",
    "{warrior} showed courage in facing {opponent}, which would have mattered more if judgment had joined the effort.  The crowd was entertained.  The records were not forgiving.",
    "Victory rarely announces itself loudly in {arena}.  {warrior} overcame {opponent} through patience and timing, not force, earning recognition through discipline rather than drama.  Few noticed at first — but many will remember.",
    "{warrior} entered the arena with a plan and left without an argument.  {opponent} never found footing, and the result was entirely predictable from the opening exchange.",
    "{warrior} underestimated {opponent}, a mistake corrected decisively before the crowd grew bored.  In {arena}, assumptions are expensive.",
    "The fight wasn't clean, fast, or elegant — but {warrior} endured.  Against {opponent}, persistence carried the day and the record followed.",
    "{opponent} learned more than they expected when facing {warrior} this turn.  Some lessons cost pride; others cost position.",
    "Word spreads quickly after performances like {warrior} delivered this turn.  {arena} takes note, and so do managers with memory.  {points} recognition and rising.",
]

_BLK_META_WARRIOR = [
    "{warrior} drew more challenges than anyone else this turn, a mix of opportunity seeking and poor judgment by would-be rivals.  Attention like that rarely ends quietly.",
    "Schedules don't lie, and this turn {warrior} attracted the most challenge traffic in {arena}.  Whether rivals see an opportunity or underestimate the danger remains to be answered.",
    "Several challengers tested {warrior} this turn with varying degrees of confidence.  The results told the story the records already suggested.",
    "As the turn progressed, the challenges aimed at {warrior} felt less strategic and more desperate.  In {arena}, that kind of urgency often exposes more weakness than courage.",
    "{warrior} became a focal point this turn, drawing repeated challenges from hopeful rivals.  Popularity in this arena is rarely comfortable.",
]

_BLK_META_TEAM = [
    "Managers were noticeably reluctant to schedule fights against {team} this turn.  Avoidance like that doesn't come from reputation alone — it comes from recent memory.  Smart managers learn quickly in {arena}.",
    "Whenever {team} appeared on the board, opponents suddenly developed scheduling conflicts.  Fear dresses itself as caution in many ways, and this turn wore it openly.",
    "Schedules don't lie, and this turn revealed growing hesitation around {team}.  Challenges that once came freely are now reconsidered, delayed, or quietly withdrawn.  Reputation is finally catching up.",
    "Once the first manager avoided {team}, others followed.  Fear spreads efficiently under the guise of scheduling logic.",
    "Beneath the noise of the arena, careful managers adjusted pairings with intent.  Not all victories this turn required combat.  {team} benefited from the arithmetic.",
]

_BLK_CHAMP_HOLDS = [
    "{champion} remains atop {arena}, not through spectacle, but through consistency.  Another turn passed without a successful challenge, reinforcing a reign built on reliability rather than luck.",
    "The Champion survived the turn, which technically counts as success in this arena.  Whether {champion} inspired fear or simply benefited from unconvincing challengers is open for debate.",
    "Holding the top spot is harder than taking it, and {champion} demonstrated why.  The throne remains occupied, and challengers are running out of excuses.",
    "Sitting atop the rankings does not grant {champion} comfort, only scrutiny.  Every move is watched, every opponent motivated.  Another turn passes, and still the crown remains where it is.",
    "There was no grand announcement this turn — only confirmation.  {champion} continues to define the top rank through presence alone, forcing challengers to measure themselves before they ever step forward.",
    "Holding the top rank invites constant scrutiny, and {champion} of {champ_team} endured it again.  Another turn passed without displacement, tightening their grip on the title.",
    "Whether through fear or miscalculation, no challenger succeeded against {champion}.  The throne remains occupied, and increasingly familiar.",
    "Every schedule change and whispered plan still points toward {champion}.  Until someone succeeds, intention remains irrelevant.",
    "{champion} didn't dazzle this turn — they didn't need to.  Authority in {arena} is measured by outcomes, not applause.",
    "The arena grows restless under consistency, but {champion} continues to deliver it.  Resentment does little to move standings.",
]

_BLK_CHAMP_NEW = [
    "The crowds were amazed this turn, as {champion} of {champ_team} dethroned the reigning Champion in a fight that will be talked about for turns to come.  A new name atop the throne.",
    "{champion} of {champ_team} has done what countless rivals only dreamed — claimed the Championship in direct combat.  The arena has a new ruler, and the pretenders must recalculate.",
    "Stop the histories and note the date: {champion} of {champ_team} is the new Champion of {arena}.  The old order ends.  The new one has precisely one member.",
]

_BLK_CHAMP_VACANT = [
    "The Championship throne remains empty this turn.  No warrior has yet met the criteria to claim it.  Every manager with ambition should be watching their most recognised fighter closely.",
    "No Champion walks the arena floor this turn.  The vacancy is an open invitation, and somewhere in {arena}, someone is already planning to answer it.",
    "The title sits unclaimed in {arena}, which means every warrior with enough recognition and enough nerve has cause to press forward.  The throne waits.",
]

_BLK_DEATH = [
    "The Dark Arena claimed {warrior} this turn.  The fight ended as so many do — suddenly, decisively, and without ceremony.  In {arena}, remembrance is brief, but final.",
    "{warrior} will not return from the Dark Arena.  The schedule moved on quickly, as it always does.  The arena has no patience for nostalgia.",
    "Records like {record} eventually make demands.  {warrior} answered them in the Dark Arena, where explanations are no longer required.",
    "{warrior} entered the Dark Arena carrying more hope than history justified.  The outcome was swift, and the lesson permanent.  {arena} does not negotiate with potential.",
    "News of {warrior}'s end traveled quickly, then stopped mattering.  In the arena, loss is acknowledged briefly and replaced immediately.  The next fight always comes.",
    "{warrior}'s name was struck from future schedules this turn.  In {arena}, removal is swift and rarely discussed afterward.",
    "The Dark Arena offered no correction, only conclusion, for {warrior}.  The record tells the rest.  Career ended at {record}.",
    "The crowd quieted when {warrior} fell, if only briefly.  Then the next fight was announced, and {arena} moved on.",
    "For every rise in the standings, someone pays elsewhere.  This turn, {warrior} covered that cost.  Career record: {record}.",
    "{arena} has no room for regret.  {warrior} is gone, and the turn proceeds as scheduled.",
]

_BLK_OUTRO = [
    "The ink dries, the crowds thin, and {arena} waits for the next mistake.  Until then, I carry these accounts onward.  — {byline}",
    "That's the turn as it happened, not as it was advertised.  Anyone unhappy with the outcome is welcome to try again — results permitting.  — {byline}",
    "I'll be at {venue} if anyone wants to argue about it.  Bring coin, or don't bother.  — {byline}",
    "The turn is done.  The consequences remain.  — {byline}",
    "The turn is complete, the outcomes recorded, and the excuses already forming.  Whatever comes next, {arena} will be ready.  — {byline}",
    "The turn closes.  The implications remain.  Until Turn {next_turn} — {byline}",
    "{arena} will remember this turn longer than some warriors will.  — {byline}",
    "I've written worse turns, but not many.  See you in Turn {next_turn}.  — {byline}",
    "I'll raise a glass to the survivors.  The rest are beyond complaint.  Until next time — {byline}",
    "Until the brackets change again, this is what happened.  — {byline}",
]


def _pick_block(pool: list, used: set, ctx: dict) -> str:
    """Pick an unused block from pool, format it with ctx, mark raw template as used."""
    available = [b for b in pool if b not in used]
    if not available:
        available = list(pool)
    template = random.choice(available)
    used.add(template)
    return template.format(**ctx)


def _block_commentary(card, teams, deaths, turn_num: int, champion_state: dict) -> str:
    """
    Assemble the Arena Happenings section from modular narrative block libraries.
    Pattern: 1 Intro + up-to-2 Team + up-to-2 Warrior + 1 Meta + 1 Champion + 0-1 Death + 1 Outro
    Each section is conditional on relevant data existing.
    """
    arena  = ARENA_NAME.upper()
    venue  = "Bloodspire"
    byline = random.choice(_BLK_BYLINES)
    used   = set()   # tracks raw templates used this newsletter — prevents repetition

    # ------------------------------------------------------------------
    # Gather turn data
    # ------------------------------------------------------------------
    team_data = {}
    for bout in card:
        if not bout.result: continue
        tn     = bout.player_team.team_name
        pw_won = bout.result.winner and bout.result.winner.name == bout.player_warrior.name
        if tn not in team_data:
            team_data[tn] = {"w": 0, "l": 0, "k": 0}
        td = team_data[tn]
        if pw_won:
            td["w"] += 1
            if bout.result.loser_died:
                td["k"] += 1
        else:
            td["l"] += 1

    player_team_data = {tn: td for tn, td in team_data.items()
                        if tn not in _NPC_TEAM_NAMES}
    best_team  = max(player_team_data.items(),
                     key=lambda x: (x[1]["w"], -x[1]["l"]), default=None) if player_team_data else None
    worst_team = min(player_team_data.items(),
                     key=lambda x: (x[1]["w"], -x[1]["l"]), default=None) if player_team_data else None

    seen_fights   = set()
    kill_fights   = []
    epic_fights   = []
    normal_fights = []
    for bout in card:
        if not bout.result: continue
        pair = frozenset([bout.player_warrior.name, bout.opponent.name])
        if pair in seen_fights: continue
        seen_fights.add(pair)
        pw_won = bout.result.winner and bout.result.winner.name == bout.player_warrior.name
        winner = bout.player_warrior if pw_won else bout.opponent
        loser  = bout.opponent       if pw_won else bout.player_warrior
        m      = bout.result.minutes_elapsed
        if bout.result.loser_died:
            kill_fights.append((winner, loser, m))
        elif m >= 9:
            epic_fights.append((winner, loser, m))
        else:
            normal_fights.append((winner, loser, m))

    challenge_counts = {}
    for bout in card:
        if bout.fight_type in ("challenge", "blood_challenge"):
            oname = bout.opponent.name
            challenge_counts[oname] = challenge_counts.get(oname, 0) + 1

    hot_teams = []
    cold_teams = []
    for team in teams:
        if _is_npc_team(team): continue
        hist   = getattr(team, "turn_history", []) if hasattr(team, "turn_history") else []
        recent = hist[-3:] if len(hist) >= 2 else []
        if not recent: continue
        rw = sum(h.get("w", 0) for h in recent)
        rl = sum(h.get("l", 0) for h in recent)
        tname = team.team_name if hasattr(team, "team_name") else team.get("team_name", "?")
        if rw > 0 and rl == 0:   hot_teams.append(tname)
        elif rl > 0 and rw == 0: cold_teams.append(tname)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _rec(td):
        return f"{td['w']}-{td['l']}-{td['k']}"

    def _rank_change(td):
        if td["w"] > td["l"]:  return "climbing the standings"
        if td["l"] > td["w"]:  return "slipping in the rankings"
        return "holding steady"

    champ     = champion_state.get("name", "")
    champ_t   = champion_state.get("team_name", "")
    champ_src = champion_state.get("source", "")

    # Base context — all variables pre-filled with safe defaults
    ctx = dict(
        arena=arena, venue=venue, byline=byline,
        turn=turn_num, next_turn=turn_num + 1,
        team="", team2="", record="", rank_change="climbing the standings",
        warrior="", opponent="", points="",
        champion=champ.upper() if champ else "",
        champ_team=champ_t.upper() if champ_t else "",
    )

    # Track paragraphs by type (name) for structured formatting
    intro_para = None
    team_paras = []
    warrior_paras = []
    meta_para = None
    champ_para = None
    death_para = None
    outro_para = None

    # ------------------------------------------------------------------
    # 1. INTRO
    # ------------------------------------------------------------------
    intro_para = _pick_block(_BLK_INTRO, used, ctx)

    # ------------------------------------------------------------------
    # 2. TEAM PERFORMANCE  (up to 2 blocks — best team then worst team)
    # ------------------------------------------------------------------
    if best_team:
        tn, td = best_team
        ctx.update(
            team=tn.upper(), record=_rec(td), rank_change=_rank_change(td),
            team2=worst_team[0].upper() if worst_team else tn.upper(),
        )
        team_paras.append(_pick_block(_BLK_TEAM_PERF, used, ctx))

    if worst_team and best_team and worst_team[0] != best_team[0]:
        tn, td = worst_team
        ctx.update(
            team=tn.upper(), record=_rec(td), rank_change=_rank_change(td),
            team2=best_team[0].upper(),
        )
        team_paras.append(_pick_block(_BLK_TEAM_PERF, used, ctx))

    # ------------------------------------------------------------------
    # 3. WARRIOR HIGHLIGHTS  (up to 2 blocks from notable fights)
    # ------------------------------------------------------------------
    highlight_pool = kill_fights + epic_fights + normal_fights
    random.shuffle(highlight_pool)
    for winner, loser, _ in highlight_pool[:2]:
        ctx.update(
            warrior=winner.name.upper(),
            opponent=loser.name.upper(),
            points=str(getattr(winner, "recognition", 0)),
        )
        warrior_paras.append(_pick_block(_BLK_WARRIOR_HI, used, ctx))

    # ------------------------------------------------------------------
    # 4. META / AVOIDANCE  (1 block, conditional)
    # ------------------------------------------------------------------
    if challenge_counts:
        most_chal = max(challenge_counts, key=challenge_counts.get)
        ctx.update(
            warrior=most_chal.upper(),
            team=best_team[0].upper() if best_team else "",
        )
        meta_para = _pick_block(_BLK_META_WARRIOR, used, ctx)
    elif hot_teams or cold_teams:
        featured = (hot_teams or cold_teams)[0]
        ctx.update(team=featured.upper())
        meta_para = _pick_block(_BLK_META_TEAM, used, ctx)

    # ------------------------------------------------------------------
    # 5. CHAMPION  (1 block, conditional on champion_state)
    # ------------------------------------------------------------------
    if champ:
        pool = _BLK_CHAMP_NEW if champ_src == "beat_champion" else _BLK_CHAMP_HOLDS
        champ_para = _pick_block(pool, used, ctx)
    else:
        champ_para = _pick_block(_BLK_CHAMP_VACANT, used, ctx)

    # ------------------------------------------------------------------
    # 6. DEATH  (1 block — only if deaths occurred this turn)
    # ------------------------------------------------------------------
    if deaths:
        d       = deaths[0]
        rec_str = f"{d.get('w', 0)}-{d.get('l', 0)}-{d.get('k', 0)}"
        killer  = d.get("killed_by", "an unknown foe")
        ctx.update(warrior=d["name"].upper(), opponent=killer.upper(), record=rec_str)
        death_para = _pick_block(_BLK_DEATH, used, ctx)

    # ------------------------------------------------------------------
    # 7. OUTRO
    # ------------------------------------------------------------------
    outro_para = _pick_block(_BLK_OUTRO, used, ctx)

    # ====================================================================
    # Build formatted Arena Report with template structure lines
    # ====================================================================
    report_sections = []
    
    # Report header with dividers
    report_sections.append("=" * 75)
    report_sections.append("BLOODSPIRE ARENA REPORT".center(75))
    report_sections.append(f"Turn {turn_num} Official Commentary".center(75))
    report_sections.append("=" * 75)
    report_sections.append("")
    
    # Intro section
    if intro_para:
        report_sections.append(intro_para)
        report_sections.append("")
    
    # Team Performance section
    if team_paras:
        report_sections.append("-" * 75)
        report_sections.append("TEAM PERFORMANCE".center(75))
        report_sections.append("-" * 75)
        report_sections.append("")
        report_sections.append("\n\n".join(team_paras))
        report_sections.append("")
    
    # Warrior Highlights section
    if warrior_paras:
        report_sections.append("-" * 75)
        report_sections.append("NOTABLE CONTESTS".center(75))
        report_sections.append("-" * 75)
        report_sections.append("")
        report_sections.append("\n\n".join(warrior_paras))
        report_sections.append("")
    
    # Arena Dynamics section
    if meta_para:
        report_sections.append("-" * 75)
        report_sections.append("ARENA DYNAMICS".center(75))
        report_sections.append("-" * 75)
        report_sections.append("")
        report_sections.append(meta_para)
        report_sections.append("")
    
    # Championship Status section
    if champ_para:
        report_sections.append("-" * 75)
        report_sections.append("CHAMPIONSHIP STATUS".center(75))
        report_sections.append("-" * 75)
        report_sections.append("")
        report_sections.append(champ_para)
        report_sections.append("")
    
    # The Fallen section (only if deaths occurred)
    if death_para:
        report_sections.append("-" * 75)
        report_sections.append("THE FALLEN".center(75))
        report_sections.append("-" * 75)
        report_sections.append("")
        report_sections.append(death_para)
        report_sections.append("")
    
    # Closing with dividers
    report_sections.append("=" * 75)
    if outro_para:
        report_sections.append(outro_para)
    report_sections.append("=" * 75)
    
    return "\n" + "\n".join(report_sections)


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
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

