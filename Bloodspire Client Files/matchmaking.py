# =============================================================================
# matchmaking.py — BLOODSPIRE Turn Matchmaking Engine
# =============================================================================
# Builds the list of fights for a turn:
#   1. Resolve blood challenges (highest priority).
#   2. Resolve player-issued challenges (Presence-weighted).
#   3. Match unmatched player warriors against rivals from the pool.
#      - Best-tier rival whose average stat is close to the player warrior's.
#   4. Fill any remaining unmatched slots with scaled peasants.
#
# Returns a list of ScheduledFight objects ready for CombatEngine.
# =============================================================================

import random
import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict

from warrior   import Warrior
from team      import Team, create_peasant_team, create_monster_team
from ai        import RivalManager, get_or_create_rivals, save_rivals
from combat    import run_fight, FightResult
from save      import save_team, save_fight_log


# ---------------------------------------------------------------------------
# SCHEDULED FIGHT DATACLASS
# ---------------------------------------------------------------------------

@dataclass
class ScheduledFight:
    """One fight bout scheduled for the current turn."""
    player_warrior  : Warrior
    opponent        : Warrior
    player_team     : Team
    opponent_team   : Team
    opponent_manager: str       # Display name for the narrative header
    fight_type      : str       # "challenge", "rivalry", "peasant", "blood_challenge"
    result          : Optional[FightResult] = None
    fight_id        : Optional[int]         = None


# ---------------------------------------------------------------------------
# WARRIOR STRENGTH RATING (for matchmaking)
# ---------------------------------------------------------------------------

def _warrior_rating(warrior: Warrior) -> float:
    """
    Numeric rating for matchmaking purposes.
    APPROX: weighted sum of stats + fight experience + skill total.
    """
    stat_score = (
        warrior.strength     * 1.5 +
        warrior.dexterity    * 1.5 +
        warrior.constitution * 1.2 +
        warrior.intelligence * 0.8 +
        warrior.presence     * 0.5 +
        warrior.size         * 1.0
    )
    experience_bonus = warrior.total_fights * 0.3
    skill_bonus      = sum(warrior.skills.values()) * 0.2
    return stat_score + experience_bonus + skill_bonus


# ---------------------------------------------------------------------------
# EXPERIENCE BRACKET HELPERS
# ---------------------------------------------------------------------------

ROOKIE_THRESHOLD = 5      # fights 0-5 → rookie bracket
BRACKET_UPPER    = 1.30   # can face someone with up to 30% MORE fights
BRACKET_LOWER    = 0.85   # can face someone with as few as 85% of own fights
CHALLENGE_FLOOR  = 0.90   # cannot challenge someone with <90% of own fights

def _in_bracket(player_fights: int, opponent_fights: int) -> bool:
    """
    Return True if the opponent's fight count falls within the player's
    experience bracket (±30%/15% window).
    Rookies (≤5 fights) only match other rookies or peasants.
    """
    if player_fights <= ROOKIE_THRESHOLD:
        return opponent_fights <= ROOKIE_THRESHOLD

    lower = int(player_fights * BRACKET_LOWER)
    upper = int(player_fights * BRACKET_UPPER)
    return lower <= opponent_fights <= upper


def _challenge_in_bracket(challenger_fights: int, target_fights: int) -> bool:
    """
    Challenges ignore the upper bracket limit (warriors can punch up freely),
    but bully-prevention applies: cannot challenge someone with fewer than
    90% of the challenger's fights.
    Blood challenges skip this check entirely.
    """
    if challenger_fights <= ROOKIE_THRESHOLD:
        return True   # rookies can challenge anyone
    floor = int(challenger_fights * CHALLENGE_FLOOR)
    return target_fights >= floor


def _team_avg_rating(team: Team) -> float:
    active = team.active_warriors
    if not active:
        return 0.0
    return sum(_warrior_rating(w) for w in active) / len(active)


# ---------------------------------------------------------------------------
# PRESENCE-BASED CHALLENGE RESOLUTION
# ---------------------------------------------------------------------------

def _challenge_succeeds(
    challenger_presence: int,
    target_presence    : int,
    is_blood_challenge : bool = False,
    is_champion_challenge: bool = False,
) -> bool:
    """
    Determine if a challenge goes through.
    Guide formula: base_chance + (PRE - opp_PRE) percent.
    Blood challenges have +20% bonus chance.
    Champion challenges have +25% bonus chance (almost guaranteed to succeed).

    APPROX base chance: 75% (increased for easier challenge acceptance).
    """
    # Champion challenges have very high success rate
    if is_champion_challenge:
        base   = 100   # Nearly guaranteed, but level adjustment still applies
        adj    = challenger_presence - target_presence
        chance = max(5, min(95, base + adj))
        return random.randint(1, 100) <= chance
    
    base   = 85 if is_blood_challenge else 75
    adj    = challenger_presence - target_presence
    chance = max(5, min(95, base + adj))
    return random.randint(1, 100) <= chance


# ---------------------------------------------------------------------------
# FIND BEST RIVAL OPPONENT FOR A PLAYER WARRIOR
# ---------------------------------------------------------------------------

def _find_rival_opponent(
    player_warrior : Warrior,
    rivals         : List[RivalManager],
    already_matched: set,          # rival_manager_id values already used this card
    global_used    : set = None,   # warrior names used across ALL cards this turn
) -> Optional[Tuple[Warrior, RivalManager]]:
    """
    Find the best-matched rival warrior for a player warrior.

    Preference:
      1. Rival whose average team rating is closest to the player warrior.
      2. Pick the individual warrior on that rival's team with the closest rating.
      3. Skip rivals already matched this turn.
      4. Skip individual warriors already scheduled globally this turn.
    """
    player_rating = _warrior_rating(player_warrior)
    player_fights = player_warrior.total_fights
    _used = global_used or set()

    def _available_warriors(rm):
        """Active warriors on this rival team not yet used globally."""
        return [w for w in rm.team.active_warriors if w.name not in _used]

    candidates = [
        rm for rm in rivals
        if rm.manager_id not in already_matched
        and any(_in_bracket(player_fights, w.total_fights)
                for w in _available_warriors(rm))
    ]

    # If bracket filtering leaves no candidates, relax to any available rival warrior
    if not candidates:
        candidates = [
            rm for rm in rivals
            if rm.manager_id not in already_matched
            and _available_warriors(rm)
        ]

    if not candidates:
        return None

    # Sort by closeness of team average rating (using only available warriors)
    candidates.sort(key=lambda rm: abs(
        sum(_warrior_rating(w) for w in _available_warriors(rm)) /
        max(1, len(_available_warriors(rm)))
        - player_rating
    ))

    # Walk candidates until we find one with available warriors
    for best_rival in candidates:
        avail = _available_warriors(best_rival)
        if not avail:
            continue
        in_bracket = [w for w in avail
                      if _in_bracket(player_warrior.total_fights, w.total_fights)]
        pool = in_bracket if in_bracket else avail
        pool.sort(key=lambda w: abs(_warrior_rating(w) - player_rating))
        return pool[0], best_rival

    return None


# ---------------------------------------------------------------------------
# MAIN MATCHMAKING FUNCTION
# ---------------------------------------------------------------------------

def _absorb_into_monsters(warrior: Warrior, player_team: Team):
    """
    A player warrior who kills a monster is absorbed into The Monsters.
    Their stats are boosted to reflect their new terrifying role, then they
    are removed from the player team (replacement arrives as normal).
    Spec: roughly 0.5% chance of this happening per monster fight.
    """
    from warrior import STAT_MAX
    import random as _r

    # Boost every stat toward monster territory
    boosts = {
        "strength"    : _r.randint(3, 6),
        "dexterity"   : _r.randint(2, 4),
        "constitution": _r.randint(3, 6),
        "intelligence": _r.randint(1, 3),
        "presence"    : _r.randint(2, 4),
        "size"        : _r.randint(2, 5),
    }
    for attr, boost in boosts.items():
        cur = getattr(warrior, attr)
        setattr(warrior, attr, min(STAT_MAX, cur + boost))

    # Give them master skills befitting a monster
    warrior.skills["parry"]     = max(warrior.skills.get("parry",    0), 7)
    warrior.skills["dodge"]     = max(warrior.skills.get("dodge",    0), 6)
    warrior.skills["initiative"]= max(warrior.skills.get("initiative",0), 7)

    warrior.recalculate_derived()

    # Remove from player team — kill_warrior issues a replacement
    player_team.kill_warrior(
        warrior,
        killed_by     = "The Monsters",
        killer_fights = 999,
    )


def build_fight_card(
    player_team  : Team,
    rivals       : List[RivalManager],
    champion_state: dict = None,
    global_used  : set = None,    # shared set of warrior names used across ALL teams this turn
) -> List[ScheduledFight]:
    """
    Build the complete fight card for the current turn.
    Returns a list of ScheduledFight objects.

    Steps:
      1. Monster challenges
      2. Blood challenges
      3. Champion / regular challenges
      4. Match remaining warriors against rivals
      5. Fill unmatched slots with peasants

    global_used is a mutable set shared across all team card builds in a turn.
    Warriors from either side of a fight are added to it so no warrior fights
    more than once per turn regardless of how many player teams are processing.
    """
    if champion_state is None:
        champion_state = {}
    if global_used is None:
        global_used = set()

    current_champion = champion_state.get("name", "")
    card          : List[ScheduledFight]  = []
    matched_players : set = set()         # player warrior names already scheduled this card
    matched_rivals  : set = set()         # rival manager IDs already used this card

    def _schedule(fight: ScheduledFight):
        """Add a fight to the card and mark both warriors as used globally."""
        card.append(fight)
        global_used.add(fight.player_warrior.name)
        if fight.fight_type not in ("monster", "peasant"):
            global_used.add(fight.opponent.name)

    active_players = player_team.active_warriors
    if not active_players:
        print("  No active warriors to schedule.")
        return card

    # ------------------------------------------------------------------
    # STEP 1: BLOOD CHALLENGES
    # ------------------------------------------------------------------
    for bc_challenger_name, bc_target_name in list(player_team.blood_challenges):
        # Find the challenger on the player's team
        challenger = player_team.warrior_by_name(bc_challenger_name or "")
        if challenger is None:
            # Allow any available warrior to carry the BC
            available = [w for w in active_players if w.name not in matched_players]
            if not available:
                continue
            challenger = random.choice(available)

        # Find the target in the rival pool
        player_mgr = getattr(player_team, "manager_name", "")
        target_warrior = None
        target_rival   = None
        for rm in rivals:
            if rm.manager_name == player_mgr:
                print(f"  Blood challenge target skipped: '{rm.team_name}' is managed by the same manager.")
                continue
            for w in rm.team.active_warriors:
                if w.name.lower() == (bc_target_name or "").lower():
                    if w.name in global_used:
                        print(f"  Blood challenge target '{w.name}' already fighting this turn. Skipping.")
                        break
                    target_warrior = w
                    target_rival   = rm
                    break
            if target_warrior:
                break

        if target_warrior is None:
            print(f"  Blood challenge target '{bc_target_name}' not found or already matched. Skipping.")
            continue

        succeeds = _challenge_succeeds(
            challenger.presence,
            target_warrior.presence,
            is_blood_challenge=True,
        )
        if succeeds:
            _schedule(ScheduledFight(
                player_warrior   = challenger,
                opponent         = target_warrior,
                player_team      = player_team,
                opponent_team    = target_rival.team,
                opponent_manager = target_rival.manager_name,
                fight_type       = "blood_challenge",
            ))
            matched_players.add(challenger.name)
            matched_rivals.add(target_rival.manager_id)
            print(f"  BLOOD CHALLENGE: {challenger.name} vs {target_warrior.name} — ACCEPTED")
        else:
            print(
                f"  Blood challenge {challenger.name} → {bc_target_name} "
                f"was REFUSED (Presence check failed)."
            )

    # ------------------------------------------------------------------
    # STEP 1b: MONSTER FIGHTS (want_monster_fight flag set by manager)
    # ------------------------------------------------------------------
    monster_team = None   # lazy-created once if needed
    for pw in list(active_players):
        if pw.name in matched_players:
            continue
        if not pw.want_monster_fight:
            continue
        if monster_team is None:
            monster_team = create_monster_team()
        import random as _rnd
        monster = _rnd.choice(monster_team.active_warriors)
        _schedule(ScheduledFight(
            player_warrior   = pw,
            opponent         = monster,
            player_team      = player_team,
            opponent_team    = monster_team,
            opponent_manager = "The Arena",
            fight_type       = "monster",
        ))
        matched_players.add(pw.name)
        print(f"  MONSTER FIGHT: {pw.name} vs {monster.name}")
        # Clear the flag so it doesn't persist to next turn
        pw.want_monster_fight = False

    # ------------------------------------------------------------------
    # STEP 1c: RETIREMENTS (want_retire flag)
    # ------------------------------------------------------------------
    for pw in list(active_players):
        if pw.name in matched_players:
            continue
        if not pw.want_retire:
            continue
        if not pw.can_retire:
            print(f"  RETIRE REJECTED: {pw.name} only has {pw.total_fights} fights (need 100).")
            pw.want_retire = False
            continue
        replacement = player_team.retire_warrior(pw)
        if replacement:
            print(f"  RETIREMENT: {pw.name} retires. {replacement.name} joins the team.")
        pw.want_retire = False
        matched_players.add(pw.name)   # retired warriors don't fight this turn

    # ------------------------------------------------------------------
    # STEP 2a: CHAMPION CHALLENGES (highest non-blood priority)
    # If current champion exists, collect all challengers and pick one
    # ------------------------------------------------------------------
    if current_champion:
        champion_warrior = None
        champion_rival   = None
        
        # Find the champion in the rival pool
        for rm in rivals:
            for w in rm.team.active_warriors:
                if w.name.lower() == current_champion.lower():
                    champion_warrior = w
                    champion_rival   = rm
                    break
            if champion_warrior:
                break
        
        if champion_warrior and champion_rival:
            # Collect all warriors wanting to challenge the champion
            champ_challengers = []
            for challenger_name, targets in player_team.challenges.items():
                if challenger_name in matched_players:
                    continue
                challenger = player_team.warrior_by_name(challenger_name)
                if challenger is None or not challenger.is_alive:
                    continue
                
                # Check if this challenger is targeting the champion (by exact name or manager)
                for target_name in targets:
                    if (target_name.lower() == current_champion.lower() or
                        target_name.lower() == champion_rival.manager_name.lower() or
                        target_name.lower() == champion_rival.team_name.lower()):
                        champ_challengers.append((challenger, challenger_name, target_name))
                        break
            
            # If there are champion challengers, pick the best one(s)
            if champ_challengers:
                if len(champ_challengers) == 1:
                    # Single challenger: nearly guaranteed success
                    challenger, chal_name, target_name = champ_challengers[0]
                    succeeds = _challenge_succeeds(
                        challenger.presence,
                        champion_warrior.presence,
                        is_blood_challenge=False,
                        is_champion_challenge=True,
                    )
                    if succeeds:
                        _schedule(ScheduledFight(
                            player_warrior   = challenger,
                            opponent         = champion_warrior,
                            player_team      = player_team,
                            opponent_team    = champion_rival.team,
                            opponent_manager = champion_rival.manager_name,
                            fight_type       = "challenge",
                        ))
                        matched_players.add(chal_name)
                        matched_rivals.add(champion_rival.manager_id)
                        print(f"  *** CHAMPION CHALLENGE ACCEPTED: {chal_name} challenges {current_champion} ***")
                    else:
                        print(f"  Champion challenge {chal_name} → {current_champion} REFUSED (rare presence failure).")
                else:
                    # Multiple challengers: rank by presence, recognition, arena stats
                    # Pick the one with highest priority
                    def _challenger_priority(entry):
                        challenger, _, _ = entry
                        # Primary: presence; secondary: recognition; tertiary: win ratio
                        presence = challenger.presence
                        recognition = getattr(challenger, "recognition", 0)
                        win_ratio = challenger.wins / max(1, challenger.total_fights)
                        return (-presence, -recognition, -win_ratio)

                    champ_challengers.sort(key=_challenger_priority)
                    challenger, chal_name, target_name = champ_challengers[0]

                    # Allow the selected challenger through with high success rate
                    succeeds = _challenge_succeeds(
                        challenger.presence,
                        champion_warrior.presence,
                        is_blood_challenge=False,
                        is_champion_challenge=True,
                    )
                    if succeeds:
                        _schedule(ScheduledFight(
                            player_warrior   = challenger,
                            opponent         = champion_warrior,
                            player_team      = player_team,
                            opponent_team    = champion_rival.team,
                            opponent_manager = champion_rival.manager_name,
                            fight_type       = "challenge",
                        ))
                        matched_players.add(chal_name)
                        matched_rivals.add(champion_rival.manager_id)
                        print(f"  *** CHAMPION CHALLENGE ACCEPTED: {chal_name} vs {current_champion} ***")
                        print(f"      ({len(champ_challengers)} warriors wanted the challenge; {chal_name} prevailed by presence/recognition)")
                    else:
                        print(f"  Champion challenge {chal_name} → {current_champion} REFUSED (rare presence failure).")

    # ------------------------------------------------------------------
    # STEP 2b: REGULAR PLAYER-ISSUED CHALLENGES
    # ------------------------------------------------------------------
    for challenger_name, targets in player_team.challenges.items():
        if challenger_name in matched_players:
            continue
        challenger = player_team.warrior_by_name(challenger_name)
        if challenger is None or not challenger.is_alive:
            continue

        for target_name in targets:
            # Skip if this is a champion challenge (already handled in STEP 2a)
            if current_champion and (
                target_name.lower() == current_champion.lower()
            ):
                continue
            
            # Try to find target in rival pool
            player_mgr     = getattr(player_team, "manager_name", "")
            target_warrior = None
            target_rival   = None

            for rm in rivals:
                if rm.manager_id in matched_rivals:
                    continue
                if rm.manager_name == player_mgr:
                    print(f"  Challenge '{challenger_name}' → '{target_name}' blocked: "
                          f"'{rm.team_name}' is managed by the same manager.")
                    continue
                # Match against manager name, team name, or warrior name
                if (target_name.lower() in rm.manager_name.lower()
                        or target_name.lower() in rm.team_name.lower()):
                    result = _find_rival_opponent(challenger, [rm], matched_rivals)
                    if result:
                        target_warrior, target_rival = result
                        break

                for w in rm.team.active_warriors:
                    if target_name.lower() in w.name.lower():
                        if w.name in global_used:
                            print(f"  Challenge target '{w.name}' already fighting this turn. Skipping.")
                            break
                        # Bully-prevention: cannot challenge someone too far below
                        if not _challenge_in_bracket(challenger.total_fights,
                                                     w.total_fights):
                            print(
                                f"  Challenge {challenger_name} → {w.name} "
                                f"REJECTED: target has too little experience "
                                f"({w.total_fights} fights vs "
                                f"{challenger.total_fights} needed)."
                            )
                            target_warrior = None
                            break
                        target_warrior = w
                        target_rival   = rm
                        break
                if target_warrior:
                    break

            if target_warrior is None:
                print(f"  Challenge target '{target_name}' not found or already matched.")
                continue

            succeeds = _challenge_succeeds(
                challenger.presence,
                target_warrior.presence,
                is_blood_challenge=False,
                is_champion_challenge=False,
            )
            if succeeds:
                _schedule(ScheduledFight(
                    player_warrior   = challenger,
                    opponent         = target_warrior,
                    player_team      = player_team,
                    opponent_team    = target_rival.team,
                    opponent_manager = target_rival.manager_name,
                    fight_type       = "challenge",
                ))
                matched_players.add(challenger_name)
                matched_rivals.add(target_rival.manager_id)
                print(f"  Challenge accepted: {challenger_name} vs {target_warrior.name}")
                break
            else:
                print(
                    f"  Challenge {challenger_name} → {target_name} "
                    f"REFUSED (Presence check failed)."
                )

    # ------------------------------------------------------------------
    # STEP 3: MATCH REMAINING WARRIORS AGAINST RIVALS
    # All warriors attempt rival matching first; peasants are only used
    # in Step 4 when no rival is available for a given warrior.
    # Rookies (≤5 fights) are matched against similarly inexperienced
    # rivals via _in_bracket(); the bracket relaxes if none are found.
    # ------------------------------------------------------------------
    remaining = [w for w in active_players if w.name not in matched_players]

    for player_warrior in remaining:
        result = _find_rival_opponent(player_warrior, rivals, matched_rivals, global_used)
        if result:
            opponent, rival_manager = result
            _schedule(ScheduledFight(
                player_warrior   = player_warrior,
                opponent         = opponent,
                player_team      = player_team,
                opponent_team    = rival_manager.team,
                opponent_manager = rival_manager.manager_name,
                fight_type       = "rivalry",
            ))
            matched_players.add(player_warrior.name)
            matched_rivals.add(rival_manager.manager_id)

    # ------------------------------------------------------------------
    # STEP 4: FILL UNMATCHED WITH PEASANTS
    # ------------------------------------------------------------------
    still_unmatched = [w for w in active_players if w.name not in matched_players]

    if still_unmatched:
        avg_fights = (
            sum(w.total_fights for w in still_unmatched) // len(still_unmatched)
        )
        peasant_team = create_peasant_team(target_fight_count=avg_fights)

        for player_warrior in still_unmatched:
            # Pick a random peasant from the scaled team
            peasants = peasant_team.active_warriors
            if not peasants:
                peasant_team = create_peasant_team(target_fight_count=avg_fights)
                peasants = peasant_team.active_warriors
            peasant = random.choice(peasants)

            _schedule(ScheduledFight(
                player_warrior   = player_warrior,
                opponent         = peasant,
                player_team      = player_team,
                opponent_team    = peasant_team,
                opponent_manager = "The Arena",
                fight_type       = "peasant",
            ))
            matched_players.add(player_warrior.name)

    print(f"\n  Fight card: {len(card)} bout(s) scheduled.")
    return card


# ---------------------------------------------------------------------------
# EXECUTE THE FIGHT CARD
# ---------------------------------------------------------------------------

def run_turn(
    player_team    : Team,
    rivals         : List[RivalManager],
    verbose        : bool = True,
    champion_state : dict = None,
    global_used    : set  = None,   # shared warrior-name set across all teams this turn
) -> List[ScheduledFight]:
    """Build and execute all fights for one turn.
    Returns the completed ScheduledFight list with results attached.
    Saves fight logs, updates records, triggers post-fight rival training.
    Marks fights against the current champion as 'champion' fight type.

    global_used is mutated in-place as fights are scheduled so callers
    running multiple teams can share it to prevent warriors fighting twice.
    """
    if champion_state is None:
        champion_state = {}
    if global_used is None:
        global_used = set()
    current_champion = champion_state.get("name", "")
    print(f"\n  === RUNNING TURN — {player_team.team_name} ===\n")
    print(f"  [run_turn start] archived_warriors={len(getattr(player_team,'archived_warriors',[]))}")

    card = build_fight_card(player_team, rivals,
                            champion_state=champion_state,
                            global_used=global_used)

    for i, bout in enumerate(card, 1):
        pw = bout.player_warrior
        ow = bout.opponent
        print(f"\n  [{i}/{len(card)}] {pw.name} ({player_team.team_name}) "
              f"vs {ow.name} ({bout.opponent_team.team_name}) [{bout.fight_type}]")
        print("  " + "-" * 60)

        result = run_fight(
            pw, ow,
            team_a_name      = player_team.team_name,
            team_b_name      = bout.opponent_team.team_name,
            manager_a_name   = player_team.manager_name,
            manager_b_name   = bout.opponent_manager,
            is_monster_fight = (bout.fight_type == "monster"),
        )
        bout.result = result

        # Inject scout-attendance flavor text if any manager is watching either warrior
        try:
            from save import get_all_scouted_warriors, current_turn as _ct
            # Scouts are stored at (turn - 1) because increment_turn() runs before fights.
            scouted = get_all_scouted_warriors(_ct() - 1)
            attending = set()
            for warrior in (pw, ow):
                for mgr in scouted.get(warrior.name, []):
                    attending.add(mgr)
            if attending:
                mgr_list = ", ".join(sorted(attending))
                scout_line = (
                    f"\n[A scout from {mgr_list}'s stable is in attendance, "
                    f"watching the proceedings with a keen eye.]\n"
                )
                result = result.__class__(
                    winner          = result.winner,
                    loser           = result.loser,
                    loser_died      = result.loser_died,
                    minutes_elapsed = result.minutes_elapsed,
                    narrative       = scout_line + result.narrative,
                    training_results= result.training_results,
                )
                bout.result = result
        except Exception:
            pass

        # Save fight log and capture fight_id for history
        fight_id = None
        try:
            log_path, fight_id = save_fight_log(
                result.narrative,
                player_team.team_name,
                bout.opponent_team.team_name,
            )
            bout.fight_id = fight_id
            if verbose:
                print(f"  Fight log saved: {log_path}")
        except IOError as e:
            print(f"  WARNING: Could not save fight log: {e}")

        # Record this fight in the player warrior's history and update popularity
        if result:
            pw_won    = result.winner and result.winner.name == pw.name
            pw_result = "win" if pw_won else "loss"
            pw.update_popularity(won=pw_won)
            pw.update_recognition(
                won=pw_won,
                killed_opponent=result.loser_died and pw_won,
                self_hp_pct=result.winner_hp_pct if pw_won else result.loser_hp_pct,
                opp_hp_pct=result.loser_hp_pct if pw_won else result.winner_hp_pct,
                self_knockdowns=result.winner_knockdowns if pw_won else result.loser_knockdowns,
                opp_knockdowns=result.loser_knockdowns if pw_won else result.winner_knockdowns,
                self_near_kills=result.winner_near_kills if pw_won else result.loser_near_kills,
                opp_near_kills=result.loser_near_kills if pw_won else result.winner_near_kills,
                minutes_elapsed=result.minutes_elapsed,
                max_minutes=60 if getattr(bout, "is_monster_fight", False) else 30,
                opponent_total_fights=ow.total_fights,
            )
            from save import current_turn
            # Determine fight type: if opponent is champion, mark as 'champion'  
            fight_type_for_record = "champion" if (current_champion and ow.name == current_champion) else bout.fight_type
            pw.fight_history.append({
                "turn"           : current_turn(),
                "opponent_name"  : ow.name,
                "opponent_race"  : ow.race.name,
                "opponent_team"  : bout.opponent_team.team_name,
                "result"         : pw_result,
                "minutes"        : result.minutes_elapsed,
                "fight_id"       : fight_id,
                "warrior_slain"  : result.loser_died and result.loser is pw,
                "opponent_slain" : result.loser_died and (result.winner is not None)
                                   and result.winner.name == pw.name,
                "fight_type"     : fight_type_for_record,
            })

            # Also record this fight in the opponent warrior's history so
            # scouting reports can load the fight log via fight_id.
            if fight_id and bout.fight_type not in ("monster", "peasant"):
                ow_result = "loss" if pw_won else "win"
                # Determine fight type: if player_warrior is champion, mark as 'champion'
                fight_type_for_opp = "champion" if (current_champion and pw.name == current_champion) else bout.fight_type
                ow.fight_history.append({
                    "turn"           : current_turn(),
                    "opponent_name"  : pw.name,
                    "opponent_race"  : pw.race.name if hasattr(pw.race, "name") else str(pw.race),
                    "opponent_team"  : player_team.team_name,
                    "result"         : ow_result,
                    "minutes"        : result.minutes_elapsed,
                    "fight_id"       : fight_id,
                    "warrior_slain"  : result.loser_died and result.loser is ow,
                    "opponent_slain" : result.loser_died and result.loser is pw,
                    "fight_type"     : fight_type_for_opp,
                })

        # Handle player warrior death
        if result.loser_died and result.loser is pw:
            print(f"  *** {pw.name} has been SLAIN! Replacement incoming. ***")
            player_team.kill_warrior(
                pw,
                killed_by     = ow.name,
                killer_fights = ow.total_fights,
            )

        # Handle opponent death
        if result.loser_died and result.loser is ow:
            if bout.fight_type == "monster":
                # The rarest event: player warrior slays a monster.
                # The warrior is absorbed into The Monsters with boosted stats.
                _absorb_into_monsters(pw, player_team)
                print(f"  !!! {pw.name} has SLAIN a monster and joins The Monsters! !!!")
            elif bout.fight_type == "peasant":
                pass   # Peasants have no persistent team — nothing to update
            else:
                bout.opponent_team.kill_warrior(ow)

        if verbose:
            if result.winner:
                outcome = "WON" if result.winner is pw else "LOST"
                print(f"  Result: {pw.name} {outcome} in {result.minutes_elapsed} minute(s)")
            else:
                print(f"  Result: DRAW after {result.minutes_elapsed} minute(s)")

    # Post-turn: rival teams train
    _rival_ids_used = {
        bout.opponent_team.team_id
        for bout in card
        if bout.fight_type in ("rivalry", "challenge", "blood_challenge")
    }
    for rm in rivals:
        if rm.manager_id in _rival_ids_used:
            rm.post_fight_update()

    # Clear challenges
    player_team.clear_challenges()
    player_team.blood_challenges.clear()

    # Increment turns_active for every living warrior on the team
    for w in player_team.active_warriors:
        w.turns_active = getattr(w, 'turns_active', 0) + 1

    # Save everything
    save_team(player_team)
    save_rivals(rivals)

    # Write turn logs (HTML + plain text matchmaking log)
    from save import write_turn_logs, save_newsletter, load_champion_state, save_champion_state, load_newsletter_voice
    turn = current_turn()
    write_turn_logs(turn, card, player_team.team_name)

    # Update team turn_history for last-5-turns newsletter column
    turn_w = sum(1 for b in card if b.result and b.result.winner
                 and b.result.winner.name == b.player_warrior.name)
    turn_l = len(card) - turn_w
    turn_k = sum(1 for b in card if b.result and b.result.loser_died
                 and b.result.winner and b.result.winner.name == b.player_warrior.name)
    player_team.turn_history.append({"turn": turn, "w": turn_w, "l": turn_l, "k": turn_k})
    save_team(player_team)

    # Generate newsletter — include AI rival teams, exclude Monsters/Peasants
    from newsletter import generate_newsletter, _update_champion
    import datetime as _dt
    processed_date = _dt.date.today().strftime("%m/%d/%Y")

    deaths_this_turn = []
    for b in card:
        if b.result and b.result.loser_died:
            loser = b.result.loser
            # Determine which team the loser belongs to
            if loser is b.player_warrior:
                loser_team = b.player_team
            else:
                loser_team = b.opponent_team
            
            deaths_this_turn.append({
                "name"    : loser.name,
                "team"    : loser_team.team_name,
                "w"       : loser.wins, "l": loser.losses, "k": loser.kills,
                "killed_by": b.result.winner.name,
            })

    # Build full team list: player team + AI rivals (skip Monsters/Peasants)
    _NPC = {"The Monsters", "The Peasants"}
    print(f"  [nl_prep] {player_team.team_name} archived_warriors={len(getattr(player_team,'archived_warriors',[]))}")
    all_teams_for_nl = [player_team]
    for rm in rivals:
        if hasattr(rm, "team") and rm.team.team_name not in _NPC:
            all_teams_for_nl.append(rm.team)

    champion_state = load_champion_state()

    # Detect if the reigning champion was defeated or didn't fight this turn
    _champ_beaten_by   = None
    _champ_beaten_team = None
    _cur_champ = champion_state.get("name", "")
    _champ_fought = False
    if _cur_champ:
        for _b in card:
            if not _b.result: continue
            _pw_won = _b.result.winner and _b.result.winner.name == _b.player_warrior.name
            _winner = _b.player_warrior if _pw_won else _b.opponent
            _loser  = _b.opponent       if _pw_won else _b.player_warrior
            _winner_team = (player_team.team_name if _pw_won
                            else _b.opponent_team.team_name)
            if _b.player_warrior.name == _cur_champ or _b.opponent.name == _cur_champ:
                _champ_fought = True
            if _loser.name == _cur_champ:
                _champ_beaten_by   = _winner.name
                _champ_beaten_team = _winner_team
                break
        # Champion forfeits title if they didn't fight this turn
        if _cur_champ and not _champ_fought and not _champ_beaten_by:
            print(f"  [champion] {_cur_champ} did not fight this turn — title vacated.")
            champion_state = {}

    champion_state = _update_champion(
        all_teams_for_nl, champion_state, deaths_this_turn,
        champion_beaten_by=_champ_beaten_by,
        champion_beaten_team=_champ_beaten_team,
    )
    save_champion_state(champion_state)

    voice = load_newsletter_voice()
    newsletter_text = generate_newsletter(
        turn_num       = turn,
        card           = card,
        teams          = all_teams_for_nl,
        deaths         = deaths_this_turn,
        champion_state = champion_state,
        voice          = voice,
        processed_date = processed_date,
    )
    save_newsletter(turn, newsletter_text)

    print(f"\n  Turn complete. {len(card)} fight(s) resolved.")
    return card


# ---------------------------------------------------------------------------
# TURN SUMMARY
# ---------------------------------------------------------------------------

def turn_summary(card: List[ScheduledFight], player_team_name: str) -> str:
    """Return a human-readable summary of fight results."""
    lines = [
        "",
        "=" * 62,
        f"  TURN RESULTS — {player_team_name.upper()}",
        "=" * 62,
    ]
    wins = losses = draws = 0

    for bout in card:
        pw = bout.player_warrior
        r  = bout.result
        if r is None:
            lines.append(f"  {pw.name:<20} — No result")
            continue

        if r.winner is pw:
            outcome = "WIN "
            wins   += 1
        elif r.winner is None:
            outcome = "DRAW"
            draws  += 1
        else:
            outcome = "LOSS"
            losses += 1

        died_note = " (SLAIN)" if (r.loser_died and r.loser is pw) else ""
        kill_note = " (KILLED OPPONENT)" if (r.loser_died and r.winner is pw) else ""

        opp_type = f"[{bout.fight_type}]"
        lines.append(
            f"  {pw.name:<20} {outcome}  vs {bout.opponent.name:<20} "
            f"{opp_type:<18}{died_note}{kill_note}"
        )

    lines += [
        "  " + "-" * 60,
        f"  Wins: {wins}   Losses: {losses}   Draws: {draws}",
        "=" * 62,
    ]
    return "\n".join(lines)
