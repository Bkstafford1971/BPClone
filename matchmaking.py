# =============================================================================
# matchmaking.py — Blood Pit Turn Matchmaking Engine
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
) -> bool:
    """
    Determine if a challenge goes through.
    Guide formula: base_chance + (PRE - opp_PRE) percent.
    Blood challenges have +20% bonus chance.

    APPROX base chance: 60%.
    """
    base   = 80 if is_blood_challenge else 60
    adj    = challenger_presence - target_presence
    chance = max(5, min(95, base + adj))
    return random.randint(1, 100) <= chance


# ---------------------------------------------------------------------------
# FIND BEST RIVAL OPPONENT FOR A PLAYER WARRIOR
# ---------------------------------------------------------------------------

def _find_rival_opponent(
    player_warrior : Warrior,
    rivals         : List[RivalManager],
    already_matched: set,          # rival_manager_id values already used
) -> Optional[Tuple[Warrior, RivalManager]]:
    """
    Find the best-matched rival warrior for a player warrior.

    Preference:
      1. Rival whose average team rating is closest to the player warrior.
      2. Pick the individual warrior on that rival's team with the closest rating.
      3. Skip rivals already matched this turn.
    """
    player_rating = _warrior_rating(player_warrior)

    player_fights = player_warrior.total_fights

    candidates = [
        rm for rm in rivals
        if rm.manager_id not in already_matched
        and rm.team.active_warriors
        # At least one warrior on this rival team falls within the bracket
        and any(_in_bracket(player_fights, w.total_fights)
                for w in rm.team.active_warriors)
    ]

    # If bracket filtering leaves no candidates, relax and use all rivals
    if not candidates:
        candidates = [
            rm for rm in rivals
            if rm.manager_id not in already_matched
            and rm.team.active_warriors
        ]

    if not candidates:
        return None

    # Sort by closeness of team average rating
    candidates.sort(key=lambda rm: abs(_team_avg_rating(rm.team) - player_rating))

    best_rival = candidates[0]

    # Pick closest individual warrior from that rival's team,
    # preferring within-bracket opponents first.
    rival_warriors = best_rival.team.active_warriors
    in_bracket = [w for w in rival_warriors
                  if _in_bracket(player_warrior.total_fights, w.total_fights)]
    pool = in_bracket if in_bracket else rival_warriors
    pool.sort(key=lambda w: abs(_warrior_rating(w) - player_rating))
    chosen = pool[0]

    return chosen, best_rival


# ---------------------------------------------------------------------------
# MAIN MATCHMAKING FUNCTION
# ---------------------------------------------------------------------------

def build_fight_card(
    player_team : Team,
    rivals      : List[RivalManager],
) -> List[ScheduledFight]:
    """
    Build the complete fight card for the current turn.
    Returns a list of ScheduledFight objects.

    Steps:
      1. Blood challenges (highest priority, skip if no pending BCs)
      2. Player-issued challenges
      3. Match remaining warriors against rivals
      4. Fill unmatched slots with peasants
    """
    card          : List[ScheduledFight]  = []
    matched_players : set = set()         # player warrior names already scheduled
    matched_rivals  : set = set()         # rival manager IDs already used

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
        target_warrior = None
        target_rival   = None
        for rm in rivals:
            for w in rm.team.active_warriors:
                if w.name.lower() == (bc_target_name or "").lower():
                    target_warrior = w
                    target_rival   = rm
                    break
            if target_warrior:
                break

        if target_warrior is None:
            print(f"  Blood challenge target '{bc_target_name}' not found. Skipping.")
            continue

        succeeds = _challenge_succeeds(
            challenger.presence,
            target_warrior.presence,
            is_blood_challenge=True,
        )
        if succeeds:
            card.append(ScheduledFight(
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
        card.append(ScheduledFight(
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
    # STEP 2: PLAYER-ISSUED CHALLENGES
    # ------------------------------------------------------------------
    for challenger_name, targets in player_team.challenges.items():
        if challenger_name in matched_players:
            continue
        challenger = player_team.warrior_by_name(challenger_name)
        if challenger is None or not challenger.is_alive:
            continue

        for target_name in targets:
            # Try to find target in rival pool
            target_warrior = None
            target_rival   = None

            for rm in rivals:
                if rm.manager_id in matched_rivals:
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
                print(f"  Challenge target '{target_name}' not found.")
                continue

            succeeds = _challenge_succeeds(
                challenger.presence,
                target_warrior.presence,
                is_blood_challenge=False,
            )
            if succeeds:
                card.append(ScheduledFight(
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
    # Rookies (≤5 fights) skip rival matching and go directly to peasants
    # ------------------------------------------------------------------
    remaining = [w for w in active_players if w.name not in matched_players]

    for player_warrior in remaining:
        # Rookies always fight peasants — they have no track record yet
        if player_warrior.total_fights <= ROOKIE_THRESHOLD:
            continue   # will be picked up in STEP 4 (peasants)

        result = _find_rival_opponent(player_warrior, rivals, matched_rivals)
        if result:
            opponent, rival_manager = result
            card.append(ScheduledFight(
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

            card.append(ScheduledFight(
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
    player_team  : Team,
    rivals       : List[RivalManager],
    verbose      : bool = True,
) -> List[ScheduledFight]:
    """
    Build and execute all fights for one turn.
    Returns the completed ScheduledFight list with results attached.
    Saves fight logs, updates records, triggers post-fight rival training.
    """
    print(f"\n  === RUNNING TURN — {player_team.team_name} ===\n")

    card = build_fight_card(player_team, rivals)

    for i, bout in enumerate(card, 1):
        pw = bout.player_warrior
        ow = bout.opponent
        print(f"\n  [{i}/{len(card)}] {pw.name} ({player_team.team_name}) "
              f"vs {ow.name} ({bout.opponent_team.team_name}) [{bout.fight_type}]")
        print("  " + "-" * 60)

        result = run_fight(
            pw, ow,
            team_a_name    = player_team.team_name,
            team_b_name    = bout.opponent_team.team_name,
            manager_a_name = player_team.manager_name,
            manager_b_name = bout.opponent_manager,
        )
        bout.result = result

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
            from save import current_turn
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
            })

        # Handle player warrior death
        if result.loser_died and result.loser is pw:
            print(f"  *** {pw.name} has been SLAIN! Replacement incoming. ***")
            player_team.kill_warrior(
                pw,
                killed_by     = ow.name,
                killer_fights = ow.total_fights,
            )

        # Handle opponent death (update rival team)
        if result.loser_died and result.loser is ow:
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
