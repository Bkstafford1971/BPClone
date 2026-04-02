# =============================================================================
# combat.py — BLOODSPIRE Combat Engine v2
# =============================================================================
# CORE MECHANICS:
#   All rolls: d100 (1-100).
#   Every warrior has a permanent luck factor (1-30) added to every roll.
#
# INITIATIVE (per-action within each minute):
#   Before each action slot, both warriors roll initiative.
#   d100 + DEX_bonus + initiative_skill + luck + style_mod + activity_mod.
#   Higher roll = attacker for that slot.
#
# ATTACK vs DEFENSE:
#   Attacker: d100 + DEX + weapon_skill*5 + luck + style_mod
#   Defender: d100 + (STR/DEX) + parry/dodge_skill*4 + weapon_skill*3 + luck
#   margin = attack_roll - defense_roll
#     margin <= 0:     miss / parry / dodge
#     margin  1-9:     graze (1 HP, no other effects)
#     margin >= 10:    hit (damage = ceiling * (margin/80))
#
# DAMAGE (HYBRID):
#   Ceiling  = f(STR, weapon weight, race, skills, style, luck)
#   Fraction = min(1.0, margin / 80.0)
#   Net      = max(1, int(ceiling * fraction) - armor)
#
# CONCEDE SYSTEM:
#   Triggered at <=25% HP. d100 + PRE_bonus + luck//2 vs threshold.
#   Presence determines how often the Pitmaster grants mercy.
#   Monster fights: no concede, always to the death.
#
# DEATH CHECK:
#   overshoot = max(0, -new_hp)
#   death_chance = 0.5% + overshoot% (capped 50%)
#
# NO DRAWS: 30-minute limit -> judge awards decision to higher HP% warrior.
# =============================================================================

import random
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

from warrior  import Warrior, Strategy, ATTRIBUTES
from strategy import (
    FighterState, evaluate_triggers, get_style_advantage,
    get_style_props,
)
from weapons  import get_weapon, strength_penalty, OPEN_HAND
from armor    import (
    effective_dex, total_defense_value, is_ap_vulnerable,
)
import narrative as N


# ---------------------------------------------------------------------------
# FIGHT RESULT
# ---------------------------------------------------------------------------

@dataclass
class FightResult:
    """Summary of a completed fight. No draws exist."""
    winner          : Optional[Warrior]
    loser           : Optional[Warrior]
    loser_died      : bool
    minutes_elapsed : int
    narrative       : str
    training_results: dict  = field(default_factory=dict)
    # Per-fighter combat metrics — used by update_recognition v2
    winner_hp_pct    : float = 1.0   # winner's HP fraction at fight end
    loser_hp_pct     : float = 0.0   # loser's HP fraction at fight end
    winner_knockdowns: int   = 0     # knockdowns delivered by winner
    loser_knockdowns : int   = 0     # knockdowns delivered by loser
    winner_near_kills: int   = 0     # times winner reduced opponent below 20% HP
    loser_near_kills : int   = 0     # times loser reduced opponent below 20% HP


# ---------------------------------------------------------------------------
# COMBAT STATE
# ---------------------------------------------------------------------------

@dataclass
class _CState:
    """Mutable in-fight state for one warrior."""
    warrior            : Warrior
    current_hp         : int
    endurance          : float
    is_on_ground       : bool    = False
    active_strat_idx   : int     = 1
    active_strategy    : Strategy = None
    consecutive_ground : int     = 0
    concede_attempts   : int     = 0
    hp_at_last_concede : int     = 9999
    knockdowns_dealt   : int     = 0   # knockdowns inflicted on opponent
    near_kills_dealt   : int     = 0   # times this warrior reduced opponent below 20% HP

    def to_fighter_state(self) -> FighterState:
        return FighterState(
            warrior             = self.warrior,
            current_hp          = self.current_hp,
            max_hp              = self.warrior.max_hp,
            endurance           = self.endurance,
            is_on_ground        = self.is_on_ground,
            active_strategy_idx = self.active_strat_idx,
            active_strategy     = self.active_strategy,
        )

    @property
    def hp_pct(self) -> float:
        return self.current_hp / max(1, self.warrior.max_hp)

    @property
    def wants_to_concede(self) -> bool:
        """True when at <=25% HP and HP has dropped since last concede attempt."""
        if self.current_hp <= 0:
            return True
        if self.hp_pct > 0.25:
            return False
        return self.current_hp < self.hp_at_last_concede


# ---------------------------------------------------------------------------
# CORE ROLL FUNCTIONS
# ---------------------------------------------------------------------------

def _d100() -> int:
    return random.randint(1, 100)


def _initiative_roll(warrior: Warrior, strategy: Strategy, state: _CState) -> int:
    """d100 + DEX_bonus + initiative_skill*3 + luck + style_mod + activity_mod"""
    roll = _d100()
    dex  = effective_dex(warrior.dexterity, warrior.armor or "None", warrior.helm or "None")
    dex_bonus    = max(-10, min(10, (dex - 10) * 2))
    skill_bonus  = warrior.skills.get("initiative", 0) * 3
    luck_bonus   = warrior.luck
    props        = get_style_props(strategy.style)
    style_mod    = int(props.apm_modifier * 4)
    activity_mod = (strategy.activity - 5) * 2
    endurance_pen= int(max(0, (40 - state.endurance) * 0.3)) if state.endurance < 40 else 0
    if state.is_on_ground:
        return max(1, roll // 2)
    return max(1, roll + dex_bonus + skill_bonus + luck_bonus
               + style_mod + activity_mod - endurance_pen)


def _attack_roll(attacker: Warrior, strategy: Strategy, state: _CState) -> int:
    """d100 + DEX + weapon_skill*5 + luck + style_mod + feint + lunge bonuses"""
    roll  = _d100()
    dex   = effective_dex(attacker.dexterity, attacker.armor or "None", attacker.helm or "None")
    dex_b = max(-8, min(8, (dex - 10)))

    wpn_key   = attacker.primary_weapon.lower().replace(" ", "_").replace("&", "and")
    wpn_skill = attacker.skills.get(wpn_key, 0)
    wpn_b     = wpn_skill * 5

    luck_b    = attacker.luck
    props     = get_style_props(strategy.style)
    style_b   = int(props.apm_modifier * 3)
    feint_b   = attacker.skills.get("feint", 0) * 2
    lunge_b   = attacker.skills.get("lunge", 0) * 3 if strategy.style == "Lunge" else 0
    end_pen   = int(max(0, (30 - state.endurance) * 0.5)) if state.endurance < 30 else 0
    hp0_pen   = 30 if state.current_hp <= 0 else 0

    return max(1, roll + dex_b + wpn_b + luck_b + style_b + feint_b + lunge_b
               - end_pen - hp0_pen)


def _defense_roll(
    defender  : Warrior,
    strategy  : Strategy,
    state     : _CState,
    attacker  : Warrior,
    aim_point : str,
    atk_style : str,
    is_parry  : bool = True,
) -> int:
    """
    Parry: d100 + STR_bonus + parry_skill*4 + weapon_skill*3 + luck + style + activity
    Dodge: d100 + DEX_bonus + dodge_skill*4 + weapon_skill*2 + luck + style + size_bonus
    Weapon skill helps both: knowing your weapon improves both blocking and evasion.
    """
    roll      = _d100()
    luck_b    = defender.luck
    props     = get_style_props(strategy.style)
    wpn_key   = defender.primary_weapon.lower().replace(" ", "_").replace("&", "and")
    wpn_skill = defender.skills.get(wpn_key, 0)

    # DEX training bonus: each trained DEX point adds to defense rolls
    # +2.5 per point for dodge (rounded), +2 per point for parry.
    dex_trained = defender.attribute_gains.get("dexterity", 0)

    if is_parry:
        str_b    = max(-5, min(5, (defender.strength - 10) // 2))
        skill_b  = defender.skills.get("parry", 0) * 4
        wpn_b    = wpn_skill * 3
        style_b  = props.parry_bonus * 3
        act_mod  = (5 - strategy.activity) * 2
        dex_train_parry = int(dex_trained * 2)   # +2 per trained DEX point
        total    = roll + str_b + skill_b + wpn_b + style_b + act_mod + luck_b + dex_train_parry
    else:
        dex      = effective_dex(defender.dexterity, defender.armor or "None", defender.helm or "None")
        dex_b    = max(-8, min(8, (dex - 10)))
        skill_b  = defender.skills.get("dodge", 0) * 4
        wpn_b    = wpn_skill * 2
        style_b  = props.dodge_bonus * 2
        act_mod  = (strategy.activity - 5) * 2
        size_diff= attacker.size - defender.size
        size_b   = 5 if size_diff >= 3 else (-5 if size_diff <= -3 else 0)
        dex_train_dodge = int(dex_trained * 2.5) # +2.5 per trained DEX point
        total    = roll + dex_b + skill_b + wpn_b + style_b + act_mod + size_b + luck_b + dex_train_dodge

    if strategy.defense_point != "None" and strategy.defense_point == aim_point:
        total += 15

    try:
        sec_w = get_weapon(defender.secondary_weapon or "Open Hand")
        if sec_w.is_shield:
            total += 10 if defender.race.modifiers.shield_bonus else 5
    except ValueError:
        pass

    if props.total_kill_mode:
        return max(1, roll // 3)

    if state.endurance < 30:
        total -= int((30 - state.endurance) * 0.4)
    if state.is_on_ground:
        total -= 25
    if state.current_hp <= 0:
        total -= 30

    return max(1, total)


# ---------------------------------------------------------------------------
# DAMAGE (HYBRID)
# ---------------------------------------------------------------------------

def _calc_damage_hybrid(
    attacker    : Warrior,
    atk_strategy: Strategy,
    weapon_name : str,
    defender    : Warrior,
    margin      : int,
) -> Tuple[int, str]:
    """
    Ceiling = stats + weapon + race + skill + luck.
    Fraction = min(1.0, margin / 80.0)
    Net = max(1, ceiling * fraction - armor)
    """
    try:
        weapon = get_weapon(weapon_name)
    except ValueError:
        weapon = OPEN_HAND

    two_handed = (attacker.secondary_weapon == "Open Hand" and weapon.two_hand)

    base  = weapon.weight * 2.5
    base += max(0.0, (attacker.strength - 10)) * 0.6
    if weapon.flail_bypass or weapon.category == "Flail":
        base += max(0.0, (attacker.size - 12)) * 0.4
    if two_handed or weapon.two_hand:
        base *= 1.15
    r_mod  = attacker.race.modifiers
    base  += r_mod.damage_bonus - r_mod.damage_penalty
    props  = get_style_props(atk_strategy.style)
    base  += props.damage_modifier
    base  += (5 - atk_strategy.activity) * 0.3
    wpn_key = weapon_name.lower().replace(" ", "_").replace("&", "and")
    base  += attacker.skills.get(wpn_key, 0) * 0.8
    base  += attacker.luck * 0.15
    base  *= (1.0 - strength_penalty(weapon.weight, attacker.strength, two_handed))
    ceiling = max(3, int(base))

    fraction = max(0.10, min(1.00, margin / 80.0))
    raw      = max(1, int(ceiling * fraction))

    armor_nm = defender.armor or "None"
    helm_nm  = defender.helm  or "None"
    defense  = total_defense_value(armor_nm, helm_nm)
    if weapon.armor_piercing and is_ap_vulnerable(armor_nm):
        defense = max(0, defense // 2)

    return max(1, raw - defense), weapon.category


# ---------------------------------------------------------------------------
# PERM INJURY
# ---------------------------------------------------------------------------

_LOCATION_POOL = [
    "head", "chest", "chest", "abdomen",
    "primary_arm", "secondary_arm",
    "primary_leg", "secondary_leg",
]


def _check_perm_injury(
    warrior   : Warrior,
    damage    : int,
    aim_point : str,
) -> Optional[Tuple[str, int]]:
    if damage < warrior.max_hp * 0.15:
        return None
    chance = max(5, min(80, int((damage / warrior.max_hp) * 100) - 5))
    if warrior.race.modifiers.fewer_perms:
        chance = int(chance * 0.85)
    if random.randint(1, 100) > chance:
        return None
    if aim_point and aim_point != "None":
        loc_map = {
            "Head":"head","Chest":"chest","Abdomen":"abdomen",
            "Primary Arm":"primary_arm","Secondary Arm":"secondary_arm",
            "Primary Leg":"primary_leg","Secondary Leg":"secondary_leg",
        }
        location = loc_map.get(aim_point, random.choice(_LOCATION_POOL))
    else:
        location = random.choice(_LOCATION_POOL)
    pct    = damage / warrior.max_hp
    levels = 3 if pct > 0.50 else (2 if pct > 0.35 else 1)
    return location, levels


# ---------------------------------------------------------------------------
# KNOCKDOWN
# ---------------------------------------------------------------------------

def _check_knockdown(warrior: Warrior, state: _CState, damage: int, cat: str) -> bool:
    if state.is_on_ground:
        return False
    chance  = int((damage / max(1, warrior.max_hp)) * 80)
    if cat in ("Hammer/Mace","Flail"):  chance += 10
    if cat == "Polearm/Spear":          chance += 5
    chance -= max(0, (warrior.size - 12)) * 2
    return random.randint(1, 100) <= max(1, chance)


# ---------------------------------------------------------------------------
# DEATH CHECK
# ---------------------------------------------------------------------------

def _death_check(prev_hp: int, damage: int) -> bool:
    """
    Death probability on reaching 0 HP:
      base 0.5%, +1% per HP of overshoot, cap 50%.
    """
    new_hp    = prev_hp - damage
    if new_hp > 0:
        return False
    overshoot = abs(min(new_hp, 0))
    return random.random() * 100 < min(50.0, 0.5 + float(overshoot))


# ---------------------------------------------------------------------------
# CONCEDE CHECK
# ---------------------------------------------------------------------------

def _concede_check(warrior: Warrior, state: _CState, is_monster_fight: bool = False) -> bool:
    """
    d100 + PRE_bonus + luck//2 vs threshold (max(40, 68 - PRE//3)).
    High Presence = lower threshold = easier to get mercy.
    Effective mercy rate ~40-55% when triggered; overall fight death ~2.5-3%.
    """
    if is_monster_fight:
        return False
    roll      = _d100()
    presence  = warrior.presence
    pre_b     = max(-6, min(10, presence - 10))
    total     = roll + pre_b + warrior.luck // 2
    threshold = max(40, 68 - (presence // 3))
    return total >= threshold


# ---------------------------------------------------------------------------
# ENDURANCE
# ---------------------------------------------------------------------------

def _update_endurance(
    state: _CState, strategy: Strategy, actions: int, foe: _CState
) -> List[str]:
    lines  = []
    props  = get_style_props(strategy.style)
    burn   = props.endurance_burn + (strategy.activity - 5) * 0.3
    state.endurance = max(0.0, min(100.0, state.endurance - burn * actions))
    if props.anxiously_awaits and strategy.activity < 6:
        foe.endurance = max(0.0, foe.endurance - (6 - strategy.activity) * 0.5)
        if random.random() < 0.20:
            ln = N.anxious_line(state.warrior.name, foe.warrior.name)
            if ln:
                lines.append(ln)
    if state.endurance <= 20 and random.random() < 0.40:
        lines.append(N.fatigue_line(state.warrior.name, state.warrior.gender, True))
    elif state.endurance <= 40 and random.random() < 0.20:
        lines.append(N.fatigue_line(state.warrior.name, state.warrior.gender, False))
    return lines


# ---------------------------------------------------------------------------
# APM
# ---------------------------------------------------------------------------

def _calc_apm(warrior: Warrior, strategy: Strategy, state: _CState) -> int:
    dex  = effective_dex(warrior.dexterity, warrior.armor or "None", warrior.helm or "None")
    wpn  = warrior.primary_weapon.lower().replace(" ", "_").replace("&", "and")
    base = 2.0
    base += max(0.0, (dex - 10)) * 0.20
    base += max(0.0, (warrior.intelligence - 10)) * 0.10
    base += strategy.activity * 0.25
    base += warrior.skills.get(wpn, 0) * 0.20
    r    = warrior.race.modifiers
    base += r.attack_rate_bonus * 0.25 - r.attack_rate_penalty * 0.25
    base += get_style_props(strategy.style).apm_modifier
    if state.endurance < 40:
        base -= (40 - state.endurance) / 40 * 1.5
    if state.is_on_ground:
        base *= 0.5
    return max(1, min(10, int(round(base))))


# ---------------------------------------------------------------------------
# REFEREE INTERVENTION NARRATIVE POOLS
# ---------------------------------------------------------------------------

_REF_STONE_EVENTS = [
    ("The Ref hurls a large rock at {n}",
     "The rock connects with {n}'s temple — {n} staggers, eyes glazed."),
    ("The Ref scoops up a fist-sized stone and flings it at {n}",
     "It cracks hard against {n}'s ribs. {n} doubles over with a grunt."),
    ("The Ref hurls a jagged chunk of stone at {n}",
     "It opens a gash above {n}'s eye — {n} blinks through the blood, vision blurring."),
    ("The Ref seizes a heavy stone and hurls it at {n}",
     "The stone thuds into {n}'s chest. {n} gasps, the air driven from their lungs."),
    ("The Ref flings a sharp-edged rock at {n}",
     "It catches {n} across the shoulder — {n} winces and nearly drops their guard."),
    ("The Ref grabs a handful of gravel and hurls it straight at {n}'s face",
     "{n} recoils, blinded for a moment, eyes streaming."),
    ("The Ref hurls a stone at the back of {n}'s head",
     "{n} lurches forward, stumbling to keep their footing."),
    ("The Ref snatches up a loose cobble and sends it spinning at {n}",
     "It clips {n} across the jaw. {n} spits blood and shakes their head."),
]

_REF_WEAPON_EVENTS = [
    ("The Ref snatches up a length of chain and lashes it hard across {n}'s back",
     "{n} arches in agony, a ragged cry escaping them."),
    ("The Ref grabs a discarded wooden staff and drives it into {n}'s ribs",
     "The crack of wood on bone rings out — {n} bends double, wheezing."),
    ("The Ref seizes a blunted club and crashes it across {n}'s shoulders",
     "{n} staggers forward, knees buckling under the blow."),
    ("The Ref picks up a short iron rod and swings it hard into {n}'s thigh",
     "{n} stumbles badly, leg trembling, nearly losing their footing."),
    ("The Ref grabs a training sword and slaps the flat of it hard across {n}'s back",
     "The smack echoes across the pit — {n} flinches and lurches forward."),
]

_REF_FOLLOWUP_EVENTS = [
    ("Still unsatisfied, the Ref hurls another stone at {n}",
     "It clips {n} across the ear. {n} is visibly shaken."),
    ("The Ref shouts at {n} to fight — then flings a second stone",
     "The stone drives into {n}'s ribs. The crowd jeers."),
    ("The Ref storms forward and drives the butt of a spear into {n}'s back",
     "{n} pitches forward with a cry, barely keeping their feet."),
    ("Furious with {n}'s passivity, the Ref heaves another stone",
     "It strikes {n} hard in the kidney. {n} nearly goes down."),
    ("The crowd howls as the Ref hurls a second stone at {n}",
     "It catches {n} glancing across the jaw. {n} spits blood and staggers."),
]


# ---------------------------------------------------------------------------
# COMBAT ENGINE
# ---------------------------------------------------------------------------

class CombatEngine:

    def __init__(
        self,
        warrior_a       : Warrior,
        warrior_b       : Warrior,
        team_a_name     : str  = "Team A",
        team_b_name     : str  = "Team B",
        manager_a_name  : str  = "Manager A",
        manager_b_name  : str  = "Manager B",
        pos_a           : int  = 1,
        pos_b           : int  = 1,
        is_monster_fight: bool = False,
    ):
        self.warrior_a        = warrior_a
        self.warrior_b        = warrior_b
        self.team_a_name      = team_a_name
        self.team_b_name      = team_b_name
        self.manager_a_name   = manager_a_name
        self.manager_b_name   = manager_b_name
        self.pos_a            = pos_a
        self.pos_b            = pos_b
        self.is_monster_fight = is_monster_fight

        self.state_a = _CState(warrior=warrior_a, current_hp=warrior_a.max_hp, endurance=100.0)
        self.state_b = _CState(warrior=warrior_b, current_hp=warrior_b.max_hp, endurance=100.0)

        if warrior_a.strategies:
            self.state_a.active_strategy  = warrior_a.strategies[-1]
            self.state_a.active_strat_idx = len(warrior_a.strategies)
        if warrior_b.strategies:
            self.state_b.active_strategy  = warrior_b.strategies[-1]
            self.state_b.active_strat_idx = len(warrior_b.strategies)

        self._lines: List[str] = []
        self._prev_attacks_a: int = 0
        self._prev_attacks_b: int = 0
        self._used_adv_phrases: set = set()
        self._last_adv_tier: str = "even"
        self._last_adv_winner: str = ""

    # =========================================================================
    # MAIN LOOP
    # =========================================================================

    def resolve_fight(self) -> FightResult:
        self._lines.append(N.build_fight_header(
            self.warrior_a, self.warrior_b,
            self.team_a_name, self.team_b_name,
            self.manager_a_name, self.manager_b_name,
            self.pos_a, self.pos_b,
        ))
        self._lines.append("")

        minute = 0
        result = None
        # PRE hesitation check: high-presence warrior may cause opponent to lose minute 1
        self._apply_presence_hesitation()
        while True:
            minute += 1
            # Referee intervention: starts minute 7, pressures the losing warrior
            if minute >= 7:
                self._throw_stones(minute)
            result  = self._run_minute(minute)
            if result:
                break
            # 30-minute limit: judge awards decision — but NOT in monster fights,
            # which must always end in death (no time limit, no mercy).
            if minute >= 30 and not self.is_monster_fight:
                pct_a   = self.state_a.current_hp / max(1, self.warrior_a.max_hp)
                pct_b   = self.state_b.current_hp / max(1, self.warrior_b.max_hp)
                win_w   = self.warrior_a if pct_a >= pct_b else self.warrior_b
                los_w   = self.warrior_b if pct_a >= pct_b else self.warrior_a
                self._emit("")
                self._emit(f"The Blood Master calls time — {win_w.name.upper()} wins on judges' decision!")
                result = self._make_result(win_w, los_w, False, minute)
                break
            # Safety valve for monster fights: after 60 minutes the monster
            # finishes it — a player warrior cannot outlast a monster forever.
            if minute >= 60 and self.is_monster_fight:
                # Monster wins; player warrior dies from exhaustion
                dw = self.state_a.warrior  # player is always warrior_a
                kw = self.state_b.warrior
                dw.injuries.add("chest", 9)
                self._emit("")
                self._emit(f"{dw.name.upper()} collapses from sheer exhaustion — the monster is relentless!")
                self._emit(N.death_line(dw.name, dw.gender))
                self._emit(""); self._emit(N.victory_line(kw.name, dw.name))
                result = self._make_result(kw, dw, True, minute)
                break

        training = {}
        self._emit("")   # blank line between fight outcome and training block
        for w, opp, is_opp in [
            (self.warrior_a, self.warrior_b, False),
            (self.warrior_b, self.warrior_a, True),
        ]:
            # Dead warriors do not train — they're carried out on a shield
            if result.loser_died and result.loser is w:
                training[w.name] = []
                continue
            res = self._apply_training(w, opponent=opp)
            training[w.name] = res
            if res:
                self._emit(N.training_summary(w.name, res, is_opponent=is_opp))

        result.training_results = training
        result.narrative        = "\n".join(self._lines)
        return result

    # =========================================================================
    # SINGLE MINUTE
    # =========================================================================

    # =========================================================================
    # RESULT BUILDER
    # =========================================================================

    def _make_result(self, winner: Warrior, loser: Warrior,
                     loser_died: bool, minutes_elapsed: int) -> FightResult:
        """Build a FightResult populated with per-fighter combat metrics."""
        if winner is self.warrior_a:
            ws, ls = self.state_a, self.state_b
        else:
            ws, ls = self.state_b, self.state_a
        return FightResult(
            winner=winner,
            loser=loser,
            loser_died=loser_died,
            minutes_elapsed=minutes_elapsed,
            narrative="\n".join(self._lines),
            winner_hp_pct=max(0.0, ws.current_hp / max(1, winner.max_hp)),
            loser_hp_pct=max(0.0, ls.current_hp / max(1, loser.max_hp)),
            winner_knockdowns=ws.knockdowns_dealt,
            loser_knockdowns=ls.knockdowns_dealt,
            winner_near_kills=ws.near_kills_dealt,
            loser_near_kills=ls.near_kills_dealt,
        )

    # =========================================================================
    # MINUTE ADVANTAGE
    # =========================================================================

    _END_BRINK_THRESHOLD = 15.0   # endurance below this = potential exhaustion brink

    def _calc_minute_advantage(self) -> tuple:
        """
        Returns (tier, winner_name, loser_name) describing the current fight state.

        tier is one of: "even", "slight", "clear", "dominating", "brink", "brink_exhaustion"
        winner_name / loser_name are empty strings when tier == "even".
        """
        hp_a = self.state_a.current_hp
        hp_b = self.state_b.current_hp
        end_a = self.state_a.endurance
        end_b = self.state_b.endurance

        total_hp = max(1, hp_a + hp_b)
        hp_ratio = hp_a / total_hp   # 0–1; > 0.5 means warrior_a leads

        # Small endurance nudge (max ±0.08 shift on the score)
        end_adj = (end_a - end_b) / 100.0 * 0.08
        score = hp_ratio + end_adj
        score = max(0.0, min(1.0, score))

        if score >= 0.5:
            winner, loser = self.warrior_a, self.warrior_b
            winner_state, loser_state = self.state_a, self.state_b
            magnitude = score
        else:
            winner, loser = self.warrior_b, self.warrior_a
            winner_state, loser_state = self.state_b, self.state_a
            magnitude = 1.0 - score

        # Endurance brink override: loser is too gassed to continue effectively
        # Only fires when the loser isn't already winning (magnitude < 0.55 means
        # the HP difference alone wouldn't call it in the winner's favour clearly)
        loser_end = loser_state.endurance
        if loser_end <= self._END_BRINK_THRESHOLD and magnitude < 0.80:
            return ("brink_exhaustion", winner.name, loser.name)

        # Map magnitude → tier using the user-specified confidence bands
        if magnitude < 0.56:
            return ("even", "", "")
        elif magnitude < 0.66:
            return ("slight", winner.name, loser.name)
        elif magnitude < 0.81:
            return ("clear", winner.name, loser.name)
        elif magnitude < 0.95:
            return ("dominating", winner.name, loser.name)
        else:
            return ("brink", winner.name, loser.name)

    def _run_minute(self, minute: int) -> Optional[FightResult]:
        self._emit(f"\nMINUTE {minute}")
        if minute == 1:
            self._emit(random.choice(N.FIGHT_OPENERS))
        else:
            tier, winner_name, loser_name = self._calc_minute_advantage()
            adv_line = N.minute_status_line(
                winner_name, loser_name,
                tier, self._last_adv_tier, self._last_adv_winner,
                self._used_adv_phrases,
            )
            self._emit(adv_line)
            self._last_adv_tier = tier
            self._last_adv_winner = winner_name
            if random.random() < 0.15:
                self._emit(N.crowd_line(self.warrior_a.race.name, self.warrior_b.race.name))

        fs_a = self.state_a.to_fighter_state()
        fs_b = self.state_b.to_fighter_state()
        strat_a, idx_a = evaluate_triggers(self.warrior_a.strategies, fs_a, fs_b, minute)
        strat_b, idx_b = evaluate_triggers(self.warrior_b.strategies, fs_b, fs_a, minute)

        if idx_a != self.state_a.active_strat_idx:
            self._emit(N.strategy_switch_line(self.warrior_a.name, idx_a))
        if idx_b != self.state_b.active_strat_idx:
            self._emit(N.strategy_switch_line(self.warrior_b.name, idx_b))
        self.state_a.active_strategy  = strat_a;  self.state_a.active_strat_idx = idx_a
        self.state_b.active_strategy  = strat_b;  self.state_b.active_strat_idx = idx_b

        for st in (self.state_a, self.state_b):
            if st.is_on_ground:
                st.consecutive_ground += 1
                if random.randint(1, 100) <= 40 + st.warrior.skills.get("brawl", 0) * 8:
                    st.is_on_ground       = False
                    st.consecutive_ground = 0
                    self._emit(N.getup_line(st.warrior.name, st.warrior.gender))

        apm_a = _calc_apm(self.warrior_a, strat_a, self.state_a)
        apm_b = _calc_apm(self.warrior_b, strat_b, self.state_b)
        rem_a = apm_a;  rem_b = apm_b
        act_a = act_b = crowd = 0

        while rem_a > 0 or rem_b > 0:
            end = self._check_fatal_injury()
            if end:
                return end

            crowd += 1
            if crowd >= 5 and random.random() < 0.35:
                self._emit(N.crowd_line(self.warrior_a.race.name, self.warrior_b.race.name))
                crowd = 0

            if rem_a > 0 and rem_b > 0:
                ia = _initiative_roll(self.warrior_a, strat_a, self.state_a)
                ib = _initiative_roll(self.warrior_b, strat_b, self.state_b)
                if ia >= ib:
                    as_, ds_ = self.state_a, self.state_b
                    ax, dx   = strat_a, strat_b
                    rem_a -= 1;  act_a += 1
                else:
                    as_, ds_ = self.state_b, self.state_a
                    ax, dx   = strat_b, strat_a
                    rem_b -= 1;  act_b += 1
            elif rem_a > 0:
                as_, ds_, ax, dx = self.state_a, self.state_b, strat_a, strat_b
                rem_a -= 1;  act_a += 1
            else:
                as_, ds_, ax, dx = self.state_b, self.state_a, strat_b, strat_a
                rem_b -= 1;  act_b += 1

            r = self._resolve_action(as_, ds_, ax, dx, minute)
            if r:
                return r

            for cst, ost in [(self.state_a, self.state_b), (self.state_b, self.state_a)]:
                if cst.wants_to_concede:
                    cst.hp_at_last_concede = cst.current_hp
                    r = self._attempt_concede(cst, ost, minute)
                    if r:
                        return r

        for ln in _update_endurance(self.state_a, strat_a, act_a, self.state_b):
            self._emit(ln)
        for ln in _update_endurance(self.state_b, strat_b, act_b, self.state_a):
            self._emit(ln)
        self._prev_attacks_a = act_a
        self._prev_attacks_b = act_b
        return None

    # =========================================================================
    # ACTION
    # =========================================================================

    def _resolve_action(self, as_: _CState, ds_: _CState, ax: Strategy, dx: Strategy, minute: int) -> Optional[FightResult]:
        att = as_.warrior;  dfr = ds_.warrior
        wpn = att.primary_weapon;  aim = ax.aim_point

        intent = N.style_intent_line(att.name, dfr.name, ax.style, wpn, att.gender)
        if intent:
            self._emit(intent)

        try:    weapon = get_weapon(wpn);  cat = weapon.category
        except: weapon = OPEN_HAND;        cat = "Oddball"

        self._emit(N.attack_line(att.name, dfr.name, wpn, cat, ax.style, aim, att.gender))

        atk_r = _attack_roll(att, ax, as_)
        atk_r += get_style_advantage(ax.style, dx.style) * 6

        props_d = get_style_props(dx.style)
        use_p   = props_d.parry_bonus >= props_d.dodge_bonus
        def_r   = _defense_roll(dfr, dx, ds_, att, aim, ax.style, is_parry=use_p)
        margin  = atk_r - def_r

        if margin <= 0:
            if margin == 0:
                self._emit(N.miss_line(att.name, wpn))
            elif margin <= -30:
                if use_p:
                    barely = (-margin < 20)
                    self._emit(N.parry_line(dfr.name, barely=barely, defense_point_active=(dx.defense_point == aim)))
                    if dx.style == "Counterstrike" and not ds_.is_on_ground:
                        if random.randint(1, 100) <= 30 + dfr.skills.get("parry", 0) * 5:
                            self._emit(N.counterstrike_line(dfr.name, att.name))
                            return self._counterstrike(ds_, as_, dx, ax, minute)
                else:
                    self._emit(N.dodge_line(dfr.name))
            else:
                if use_p:
                    self._emit(N.parry_line(dfr.name, barely=True, defense_point_active=(dx.defense_point == aim)))
                else:
                    self._emit(N.dodge_line(dfr.name))
            return None

        if margin < 10:
            self._emit(f"{att.name.upper()}'s blow barely grazes {dfr.name.upper()}!")
            ds_.current_hp -= 1
            return None

        precision = "precise" if margin >= 50 else ("barely" if margin < 20 else "normal")
        for ln in N.hit_line(att.name, dfr.name, wpn, cat, aim, precision):
            self._emit(ln)

        dmg, wcats = _calc_damage_hybrid(att, ax, wpn, dfr, margin)
        self._emit(N.damage_line(dmg, dfr.max_hp))

        prev_hp        = ds_.current_hp
        ds_.current_hp -= dmg

        # Near-kill tracking: attacker reduced defender through the 20% HP threshold
        nk_threshold = int(dfr.max_hp * 0.20)
        if prev_hp > nk_threshold >= ds_.current_hp:
            as_.near_kills_dealt += 1

        if _check_knockdown(dfr, ds_, dmg, wcats):
            self._emit(N.knockdown_line(dfr.name, dfr.gender))
            ds_.is_on_ground = True
            as_.knockdowns_dealt += 1

        perm = _check_perm_injury(dfr, dmg, aim)
        if perm:
            loc, lvls = perm
            fatal     = dfr.injuries.add(loc, lvls)
            for ln in N.perm_injury_lines(dfr.name, loc, lvls, dfr.gender):
                self._emit(ln)
            if fatal:
                self._emit(N.death_line(dfr.name, dfr.gender))
                self._emit("")
                self._emit(N.victory_line(att.name, dfr.name))
                return self._make_result(att, dfr, True, minute)

        if ds_.current_hp <= 0:
            return self._handle_zero_hp(ds_, as_, prev_hp, dmg, minute)
        return None

    # =========================================================================
    # COUNTERSTRIKE
    # =========================================================================

    def _counterstrike(self, as_: _CState, ds_: _CState, ax: Strategy, dx: Strategy, minute: int) -> Optional[FightResult]:
        att = as_.warrior;  dfr = ds_.warrior;  wpn = att.primary_weapon
        try:    cat = get_weapon(wpn).category
        except: cat = "Oddball"
        for ln in N.hit_line(att.name, dfr.name, wpn, cat, ax.aim_point, "precise"):
            self._emit(ln)
        dmg, _ = _calc_damage_hybrid(att, ax, wpn, dfr, 40)
        self._emit(N.damage_line(dmg, dfr.max_hp))
        prev       = ds_.current_hp
        ds_.current_hp -= dmg

        # Near-kill tracking for counterstrike damage
        nk_threshold = int(dfr.max_hp * 0.20)
        if prev > nk_threshold >= ds_.current_hp:
            as_.near_kills_dealt += 1

        if ds_.current_hp <= 0:
            return self._handle_zero_hp(ds_, as_, prev, dmg, minute)
        return None

    # =========================================================================
    # ZERO HP
    # =========================================================================

    def _handle_zero_hp(self, dying: _CState, killer: _CState, prev: int, dmg: int, minute: int) -> Optional[FightResult]:
        dw = dying.warrior;  kw = killer.warrior
        if self.is_monster_fight:
            dw.injuries.add("chest", 9)
            self._emit(f"{dw.name.upper()} collapses — the monster shows no mercy!")
            self._emit(N.death_line(dw.name, dw.gender))
            self._emit(""); self._emit(N.victory_line(kw.name, dw.name))
            return self._make_result(kw, dw, True, minute)
        if _death_check(prev, dmg):
            dw.injuries.add("chest", 9)
            self._emit(N.death_line(dw.name, dw.gender))
            self._emit(""); self._emit(N.victory_line(kw.name, dw.name))
            return self._make_result(kw, dw, True, minute)
        # Survived: concede system takes over via wants_to_concede
        return None

    # =========================================================================
    # CONCEDE
    # =========================================================================

    def _attempt_concede(self, dying: _CState, killer: _CState, minute: int) -> Optional[FightResult]:
        dw = dying.warrior;  kw = killer.warrior
        self._emit(N.appeal_line(dw.name))
        dying.concede_attempts += 1
        granted = _concede_check(dw, dying, self.is_monster_fight)
        self._emit(N.mercy_result_line(dw.name, granted))
        if granted:
            self._emit(""); self._emit(N.victory_line(kw.name, dw.name))
            return self._make_result(kw, dw, False, minute)
        return None

    # =========================================================================
    # FATAL INJURY CHECK
    # =========================================================================

    def _check_fatal_injury(self) -> Optional[FightResult]:
        for d, k in [(self.state_a, self.state_b), (self.state_b, self.state_a)]:
            if d.warrior.injuries.is_fatal():
                return self._make_result(k.warrior, d.warrior, True, 0)
        return None

    # =========================================================================
    # TRAINING
    # =========================================================================

    def _apply_training(self, w: Warrior, opponent: Optional[Warrior] = None) -> List[str]:
        """
        Apply training. If w is alive and has INT >= 15, there is a chance
        they pick up a 4th bonus skill observed from the opponent's combat style.
        """
        res = []
        for sk in w.trains[:3]:
            res.append(w.train_skill(sk))

        # INT 4th train: learn a skill from opponent
        # Chance = (intelligence - 14) * 5%, triggered when INT >= 15
        if opponent and w.intelligence >= 15:
            bonus_chance = (w.intelligence - 14) * 5
            if random.randint(1, 100) <= bonus_chance:
                # Derive what skills the opponent actually used this fight
                candidate_skills = []
                opp_strats = opponent.strategies or []
                for s in opp_strats:
                    if s.style in ("Parry", "Counterstrike"):
                        candidate_skills.append("parry")
                    if s.style in ("Strike", "Bash", "Total Kill", "Counterstrike"):
                        candidate_skills.append("initiative")
                    if s.style in ("Dodge",):
                        candidate_skills.append("dodge")
                # Always include weapon skill and basic skills as observables
                opp_wpn = (opponent.primary_weapon or "Short Sword").lower().replace(" ","_").replace("&","and")
                candidate_skills += [opp_wpn, "dodge", "parry", "initiative", "feint"]
                # Pick one, avoiding skills already at max
                random.shuffle(candidate_skills)
                for sk in candidate_skills:
                    sk_key = sk.lower().replace(" ","_")
                    if sk_key in w.skills and w.skills[sk_key] < 9:
                        bonus_result = w.train_skill(sk_key)
                        if "trained:" in bonus_result:
                            res.append(f"[OBSERVED] {bonus_result}")
                        break

        w.recalculate_derived()
        return res

    def _apply_presence_hesitation(self):
        """
        If warrior_a has high Presence, warrior_b may hesitate at the start
        of the fight (and vice versa). The hesitation skips their first action.
        Presence 14 = 0%, 16 = 6%, 18 = 12%, 20 = 18%, 25 = 33%
        """
        for attacker_state, defender_state in [
            (self.state_a, self.state_b),
            (self.state_b, self.state_a),
        ]:
            chance = attacker_state.warrior.presence_hesitate_chance
            if chance > 0 and random.randint(1, 100) <= chance:
                defender_state.endurance = max(0.0, defender_state.endurance - 15)
                self._emit(
                    f"{attacker_state.warrior.name.upper()}'s commanding presence "
                    f"makes {defender_state.warrior.name.upper()} hesitate!"
                )

    def _throw_stones(self, minute: int):
        """
        From minute 7 onward the referee intervenes to pressure the losing warrior
        and keep the fight from becoming a marathon.

        - Monster fights are never slow to end — no intervention needed there.
        - Target: warrior at lower HP%. Equal HP → random choice.
        - Damage: (minute - 6) * 2, but the Ref never kills — floor at 1 HP.
        - No HP numbers shown in the narrative.
        - If the loser attacked ≤1 times last minute (passive), ~55% chance of
          a follow-up intervention the same minute.
        """
        if self.is_monster_fight:
            return

        pct_a = self.state_a.current_hp / max(1, self.warrior_a.max_hp)
        pct_b = self.state_b.current_hp / max(1, self.warrior_b.max_hp)
        if pct_a < pct_b:
            target_state = self.state_a
        elif pct_b < pct_a:
            target_state = self.state_b
        else:
            target_state = random.choice([self.state_a, self.state_b])

        dmg = (minute - 6) * 2
        n = target_state.warrior.name.upper()

        # Primary intervention — 20% chance the Ref grabs a weapon instead of a stone
        if random.random() < 0.20:
            action, effect = random.choice(_REF_WEAPON_EVENTS)
        else:
            action, effect = random.choice(_REF_STONE_EVENTS)

        target_state.current_hp = max(1, target_state.current_hp - dmg)
        self._emit("")
        self._emit(action.format(n=n))
        self._emit(effect.format(n=n))

        # Follow-up if the loser was passive last minute (≤1 attacks)
        losing_attacks = (
            self._prev_attacks_a if target_state is self.state_a
            else self._prev_attacks_b
        )
        if losing_attacks <= 1 and random.random() < 0.55:
            action2, effect2 = random.choice(_REF_FOLLOWUP_EVENTS)
            target_state.current_hp = max(1, target_state.current_hp - dmg)
            self._emit(action2.format(n=n))
            self._emit(effect2.format(n=n))

    def _emit(self, line: str):
        self._lines.append(line)


# ---------------------------------------------------------------------------
# CONVENIENCE
# ---------------------------------------------------------------------------

def run_fight(
    warrior_a       : Warrior,
    warrior_b       : Warrior,
    team_a_name     : str  = "Team A",
    team_b_name     : str  = "Team B",
    manager_a_name  : str  = "Manager A",
    manager_b_name  : str  = "Manager B",
    is_monster_fight: bool = False,
) -> FightResult:
    engine = CombatEngine(
        warrior_a, warrior_b,
        team_a_name, team_b_name,
        manager_a_name, manager_b_name,
        is_monster_fight=is_monster_fight,
    )
    result = engine.resolve_fight()
    if result.winner and result.loser:
        # Only update records for player-team warriors.
        # Monsters: always show 0-0-0.  Peasants: same — they are arena fodder.
        npc_races = {"Monster", "Peasant"}
        if result.winner.race.name not in npc_races:
            result.winner.record_result("win", killed_opponent=result.loser_died)
        if result.loser.race.name not in npc_races:
            result.loser.record_result("loss")
    return result
