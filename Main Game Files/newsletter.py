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
            # Don't show replacement warriors until they've competed at least once
            if getattr(wobj,"total_fights",0) == 0: continue
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
    # Monster fights first, then champion title fights, then rivalry/challenge, then peasant
    _order = {"monster":0,"champion":1,"blood_challenge":2,"challenge":2,"rivalry":3,"peasant":4}
    sorted_card = sorted(card, key=lambda b: _order.get(getattr(b,"fight_type","rivalry"), 3))

    # Deduplicate: collapse A-vs-B and B-vs-A to one line.
    # The fake_card in league mode contains every fight from every team's
    # perspective, so the same matchup can appear twice (once with A as
    # player_warrior, once with B as player_warrior).  seen_pairs handles
    # that.  We deliberately do NOT filter by individual warrior because
    # that caused legitimate fights to be dropped when a warrior appeared
    # as pw in their own team's card AND as ow in an AI team's card.
    seen_pairs = set()
    for bout in sorted_card:
        pw=bout.player_warrior; ow=bout.opponent; r=bout.result
        if not r: continue
        pair = frozenset([pw.name, ow.name])
        if pair in seen_pairs:
            continue
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
    Generate a 4-6 paragraph newspaper article from fight data.
    Comprehensive narrative with team performance, warrior highlights, 
    ranking shifts, and meta-game analysis.
    """
    arena  = ARENA_NAME.upper()
    venue  = "Bloodspire"
    byline = random.choice(_BLK_BYLINES)
    random.seed()
    
    # ==================================================================
    # DATA EXTRACTION & ANALYSIS
    # ==================================================================
    
    # 1. Team standings analysis
    team_records = {}
    team_changes = {}  # Track which teams moved
    for team in teams:
        if _is_npc_team(team): continue
        tname = team.team_name if hasattr(team, "team_name") else team.get("team_name", "?")
        w, l, k = 0, 0, 0
        for bout in card:
            if not bout.result: continue
            pteam = bout.player_team
            pteam_name = pteam.team_name if hasattr(pteam, "team_name") else pteam.get("team_name", "?")
            oteam = bout.opponent_team
            oteam_name = oteam.team_name if hasattr(oteam, "team_name") else oteam.get("team_name", "?")
            
            pw_won = bout.result.winner and bout.result.winner.name == bout.player_warrior.name
            
            if pteam_name == tname:
                if pw_won:
                    w += 1
                    if bout.result.loser_died: k += 1
                else:
                    l += 1
            elif oteam_name == tname:
                if not pw_won:
                    w += 1
                    if bout.result.loser_died: k += 1
                else:
                    l += 1
        
        team_records[tname] = {"w": w, "l": l, "k": k, "team": team}
    
    # 2. Warrior performance tracking (recognition changes, fight counts)
    warrior_stats = {}  # {name: {team, wins, losses, kills, recs_pt, tier}}
    for bout in card:
        if not bout.result: continue
        pw = bout.player_warrior
        op = bout.opponent
        pw_won = bout.result.winner and bout.result.winner.name == pw.name
        
        for warrior, won, team in [(pw, pw_won, bout.player_team), 
                                   (op, not pw_won, bout.opponent_team)]:
            if not warrior or not hasattr(warrior, "name"): continue
            name = warrior.name
            tname = team.team_name if hasattr(team, "team_name") else team.get("team_name", "?")
            if tname in _NPC_TEAM_NAMES: continue
            
            if name not in warrior_stats:
                rec = getattr(warrior, "recognition", 0)
                warrior_stats[name] = {
                    "team": tname, "wins": 0, "losses": 0, "kills": 0,
                    "recs": rec, "fights": [], "warrior_obj": warrior
                }
            
            ws = warrior_stats[name]
            if won:
                ws["wins"] += 1
                if bout.result.loser_died: ws["kills"] += 1
            else:
                ws["losses"] += 1
            
            ws["fights"].append({
                "opponent": op.name if hasattr(op, "name") else "?",
                "won": won, "died": won and bout.result.loser_died,
                "minutes": bout.result.minutes_elapsed
            })
    
    # 3. Challenge tracking (who was challenged most, who avoided most)
    challenge_counts = {}  # {warrior: count}
    avoidance_counts = {}  # {team: count}
    for bout in card:
        if not bout.result or bout.fight_type not in ["challenge", "blood_challenge"]:
            continue
        challenger = bout.player_warrior
        chal_name = challenger.name if hasattr(challenger, "name") else "?"
        challenged_team = bout.opponent_team
        cteam_name = challenged_team.team_name if hasattr(challenged_team, "team_name") else "?"
        
        challenge_counts[chal_name] = challenge_counts.get(chal_name, 0) + 1
        avoidance_counts[cteam_name] = avoidance_counts.get(cteam_name, 0) + 1
    
    most_challenged = max(challenge_counts.items(), key=lambda x: x[1])[0] if challenge_counts else None
    most_avoided = max(avoidance_counts.items(), key=lambda x: x[1])[0] if avoidance_counts else None
    
    # 4. Top performers this turn
    top_warriors = sorted(
        [(name, ws) for name, ws in warrior_stats.items() if ws["wins"] + ws["losses"] > 0],
        key=lambda x: (-x[1]["wins"], x[1]["losses"], -x[1]["recs"])
    )[:3]
    
    # 5. Champion tracking
    champ = champion_state.get("name", "")
    champ_t = champion_state.get("team_name", "")
    champ_src = champion_state.get("source", "")
    
    # Base context
    ctx = dict(
        arena=arena, venue=venue, byline=byline,
        turn=turn_num, next_turn=turn_num + 1,
        team="", team2="", record="",
        rank_change="", warrior="", opponent="",
        points="", champion=champ.upper() if champ else "",
        champ_team=champ_t.upper() if champ_t else "",
    )
    
    paragraphs = []
    
    # ==================================================================
    # PARAGRAPH 1: OPENING + TEAM STANDINGS
    # ==================================================================
    intro = _pick_block(_BLK_INTRO, set(), ctx)
    
    # Find top/bottom team for opening
    if team_records:
        best_team = max(team_records.items(), key=lambda x: (x[1]["w"], -x[1]["l"]))
        worst_team = min(team_records.items(), key=lambda x: (x[1]["w"], -x[1]["l"]))
        
        best_name, best_rec = best_team
        worst_name, worst_rec = worst_team
        
        record_str = f"{best_rec['w']}-{best_rec['l']}-{best_rec['k']}"
        ctx["team"] = best_name.upper()
        ctx["record"] = record_str
        
        if best_rec["w"] > best_rec["l"]:
            ctx["rank_change"] = "climbing the standings"
        elif best_rec["l"] > best_rec["w"]:
            ctx["rank_change"] = "slipping lower"
        else:
            ctx["rank_change"] = "holding steady"
        
        team_perf = _pick_block(_BLK_TEAM_PERF, set(), ctx)
        para1 = f"{intro}  {team_perf}"
    else:
        para1 = f"{intro}"
    
    paragraphs.append(para1)
    
    # ==================================================================
    # PARAGRAPH 2: WARRIOR HIGHLIGHTS & INDIVIDUAL PERFORMANCES
    # ==================================================================
    para2_parts = []
    
    if top_warriors:
        for name, ws in top_warriors[:2]:
            if ws["wins"] > 0:
                ctx["warrior"] = name.upper()
                ctx["points"] = str(ws["recs"])
                rec_gain = ws["recs"] - (ws["recs"] - ws["wins"] * 5)  # rough estimate
                
                if ws["wins"] == len(ws["fights"]) and len(ws["fights"]) > 0:
                    # Perfect record this turn
                    line = f"{name.upper()} dominated this turn with a perfect {ws['wins']}-{ws['losses']} record, gaining recognition and notoriety in equal measure.  Managers are taking notice."
                else:
                    line = f"{name.upper()} emerged from the turn {ws['wins']}-{ws['losses']}, further establishing their presence in {arena}.  The crowd remembers winners."
                
                para2_parts.append(line)
    
    # Add meta about challenges or avoidance
    if most_challenged and most_challenged not in [w[0] for w in top_warriors]:
        ctx["warrior"] = most_challenged.upper()
        meta_warrior = _pick_block(_BLK_META_WARRIOR, set(), ctx)
        para2_parts.append(meta_warrior)
    
    if para2_parts:
        para2 = "  ".join(para2_parts)
        paragraphs.append(para2)
    
    # ==================================================================
    # PARAGRAPH 3: TEAM META & AVOIDANCE / STRATEGY
    # ==================================================================
    para3_parts = []
    
    if most_avoided and most_avoided not in _NPC_TEAM_NAMES:
        ctx["team"] = most_avoided.upper()
        meta_team = _pick_block(_BLK_META_TEAM, set(), ctx)
        para3_parts.append(meta_team)
    
    if worst_team and worst_rec["w"] < worst_rec["l"]:
        wname, wrec = worst_team
        ctx["team"] = wname.upper()
        ctx["record"] = f"{wrec['w']}-{wrec['l']}-{wrec['k']}"
        para3_parts.append(f"{wname} walked into trouble and couldn't escape it.  A {wrec['w']}-{wrec['l']}-{wrec['k']} turn like that carries consequences.  The standings don't forget.")
    
    if para3_parts:
        para3 = "  ".join(para3_parts)
        paragraphs.append(para3)
    
    # ==================================================================
    # PARAGRAPH 4: CHAMPION STATUS
    # ==================================================================
    para4_parts = []
    
    if champ:
        if champ_src == "beat_champion":
            ctx["champion"] = champ.upper()
            ctx["champ_team"] = champ_t.upper()
            champ_line = _pick_block(_BLK_CHAMP_NEW, set(), ctx)
        else:
            ctx["champion"] = champ.upper()
            ctx["champ_team"] = champ_t.upper() if champ_t else "?"
            champ_line = _pick_block(_BLK_CHAMP_HOLDS, set(), ctx)
    else:
        champ_line = _pick_block(_BLK_CHAMP_VACANT, set(), ctx)
    
    para4_parts.append(champ_line)
    
    if para4_parts:
        para4 = "  ".join(para4_parts)
        paragraphs.append(para4)
    
    # ==================================================================
    # PARAGRAPH 4b: ADDITIONAL WARRIOR SPOTLIGHT (3rd place and beyond)
    # ==================================================================
    if len(top_warriors) >= 3:
        para4b_parts = []
        for name, ws in top_warriors[2:4]:
            if ws["wins"] + ws["losses"] > 0:
                ratio = ws["wins"] / max(1, ws["wins"] + ws["losses"])
                if ratio >= 0.5:
                    line = (f"{name.upper()} rounds out the notable performances this turn with a "
                            f"{ws['wins']}-{ws['losses']} showing.  Not spectacular — but consistent "
                            f"fighters build records one turn at a time.")
                else:
                    line = (f"{name.upper()} finished the turn at {ws['wins']}-{ws['losses']}.  "
                            f"Losses at this level tend to concentrate the mind quickly in {arena}.")
                para4b_parts.append(line)
        if para4b_parts:
            paragraphs.append("  ".join(para4b_parts))

    # ==================================================================
    # PARAGRAPH 4c: FIGHT PACE & SPECTACLE
    # ==================================================================
    all_bouts = [b for b in card if b.result]
    if all_bouts:
        fight_times = [b.result.minutes_elapsed for b in all_bouts if hasattr(b.result, "minutes_elapsed") and b.result.minutes_elapsed]
        kills_this_turn = sum(1 for b in all_bouts if b.result.loser_died)
        total_fights = len(all_bouts)

        pace_parts = []

        if fight_times:
            avg_mins = sum(fight_times) / len(fight_times)
            if avg_mins <= 4:
                pace_parts.append(
                    f"This was a fast turn in {arena}.  Fights resolved quickly and with conviction — "
                    f"few debates, fewer prolonged engagements.  The crowd rarely had time to grow restless.")
            elif avg_mins >= 10:
                pace_parts.append(
                    f"The fights ran long this turn.  Endurance was tested across the card, "
                    f"and not every warrior answered the call.  A slow turn tends to favor patience over flash.")
            else:
                pace_parts.append(
                    f"Turn {turn_num} ran at a measured pace across the board.  No wild swings in duration — "
                    f"most fights found their conclusion at the expected moment, which tells its own story.")

        if total_fights > 0:
            kill_rate = kills_this_turn / total_fights
            if kills_this_turn == 0:
                pace_parts.append(
                    f"The Dark Arena went unclaimed this turn — every bout ended with a loser still breathing.  "
                    f"Rare in {arena}, and notable enough to record.")
            elif kill_rate >= 0.3:
                pace_parts.append(
                    f"{kills_this_turn} warriors did not walk away from their fight this turn.  "
                    f"A high toll for a single card.  Managers should study the results carefully before next turn's scheduling.")
            elif kills_this_turn >= 1:
                pace_parts.append(
                    f"The Dark Arena collected {kills_this_turn} this turn.  "
                    f"Every warrior still standing should note that the odds eventually balance.")

        if pace_parts:
            paragraphs.append("  ".join(pace_parts))

    # ==================================================================
    # PARAGRAPH 4d: TEAM PERFORMANCE SPREAD
    # ==================================================================
    if len(team_records) >= 2:
        spread_parts = []
        sorted_teams = sorted(team_records.items(), key=lambda x: (-x[1]["w"], x[1]["l"]))
        top2 = sorted_teams[:2]
        bottom2 = sorted_teams[-2:]

        if len(sorted_teams) >= 3:
            t1_name, t1_rec = top2[0]
            t2_name, t2_rec = top2[1]
            spread_parts.append(
                f"{t1_name.upper()} and {t2_name.upper()} led the table this turn "
                f"at {t1_rec['w']}-{t1_rec['l']}-{t1_rec['k']} and "
                f"{t2_rec['w']}-{t2_rec['l']}-{t2_rec['k']} respectively.  "
                f"The gap between the top teams and the rest was clear and deliberate.")

            b1_name, b1_rec = bottom2[-1]
            if b1_name not in [t1_name, t2_name] and b1_rec["l"] > b1_rec["w"]:
                spread_parts.append(
                    f"At the other end, {b1_name.upper()} finished the turn below the line.  "
                    f"A {b1_rec['w']}-{b1_rec['l']}-{b1_rec['k']} record in {arena} "
                    f"is not a disaster — but it requires a response, not an excuse.")

        if spread_parts:
            paragraphs.append("  ".join(spread_parts))

    # ==================================================================
    # PARAGRAPH 5 (CONDITIONAL): DEATHS
    # ==================================================================
    if deaths and len(deaths) > 0:
        para5_parts = []
        for d in deaths[:2]:  # Show up to 2 deaths
            d_record = f"{d.get('w', 0)}-{d.get('l', 0)}-{d.get('k', 0)}"
            ctx["warrior"] = d["name"].upper()
            ctx["record"] = d_record
            death_line = _pick_block(_BLK_DEATH, set(), ctx)
            para5_parts.append(death_line)
        
        para5 = "  ".join(para5_parts)
        paragraphs.append(para5)
    
    # ==================================================================
    # PARAGRAPH 6: CLOSING / PHILOSOPHICAL
    # ==================================================================
    outro = _pick_block(_BLK_OUTRO, set(), ctx)
    para_final = f"{outro}"
    paragraphs.append(para_final)

    # Join with double line breaks for readability
    article = "\n\n".join(paragraphs)
    return "\n\nArena Happenings\n\n" + article





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

