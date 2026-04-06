# =============================================================================
# ai.py — BLOODSPIRE AI Rival Manager Pool
# =============================================================================
# Manages a persistent pool of AI rival managers whose teams grow in strength
# over time. Rivals train after each turn just like player warriors do.
# Pool is saved to saves/rivals.json.
#
# The pool starts with 8 rivals. Each rival has:
#   - A manager name and team name
#   - 5 warriors with race-appropriate stats, gear, and strategies
#   - A "difficulty tier" (1-5) that scales starting stats and training speed
# =============================================================================

import random
import json
import os
from typing import List, Optional, Dict

from warrior  import (
    Warrior, Strategy, create_warrior_ai, ATTRIBUTES,
    ROLLUP_POINTS, STAT_MIN, STAT_MAX, ALL_SKILLS, FIGHTING_STYLES,
)
from races    import list_playable_races
from weapons  import WEAPONS, list_weapons_by_category, get_weapon
from armor    import ARMOR_TIERS, HELM_TIERS, can_wear_armor
from team     import Team, TEAM_SIZE
from strategy import get_style_props


# ---------------------------------------------------------------------------
# SAVE PATH
# ---------------------------------------------------------------------------

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
RIVALS_FILE   = os.path.join(BASE_DIR, "saves", "rivals.json")
INITIAL_POOL_SIZE = 8


# ---------------------------------------------------------------------------
# RACE → PREFERRED WEAPON (for AI gear assignment)
# Derived from weapon guide notes and race descriptions.
# ---------------------------------------------------------------------------

RACE_WEAPON_PREFS: Dict[str, List[str]] = {
    "Human"   : ["Short Sword", "Military Pick", "Morningstar", "Boar Spear", "War Hammer"],
    "Half-Orc": ["War Flail", "Great Axe", "Great Sword", "War Hammer", "Great Pick"],
    "Halfling": ["Short Sword", "Hatchet", "Stiletto", "Javelin", "Bladed Flail"],
    "Dwarf"   : ["Battle Axe", "Morningstar", "War Hammer", "Boar Spear", "Target Shield"],
    "Half-Elf": ["Pole Axe", "Bastard Sword", "Battle Flail", "Long Sword", "Scythe"],
    "Elf"     : ["Short Sword", "Scimitar", "Scythe", "Dagger", "Javelin"],
    "Peasant" : ["Short Sword", "Boar Spear", "War Flail", "Morningstar"],
}

RACE_SECONDARY_PREFS: Dict[str, List[str]] = {
    "Human"   : ["Buckler", "Target Shield", "Open Hand"],
    "Half-Orc": ["Open Hand", "Tower Shield", "War Flail"],
    "Halfling": ["Buckler", "Open Hand", "Stiletto"],
    "Dwarf"   : ["Target Shield", "Tower Shield", "Buckler"],
    "Half-Elf": ["Open Hand", "Buckler"],
    "Elf"     : ["Open Hand", "Short Sword", "Dagger"],
    "Peasant" : ["Open Hand", "Buckler"],
}

# Race → best styles
RACE_STYLE_PREFS: Dict[str, List[str]] = {
    "Human"   : ["Strike", "Counterstrike", "Calculated Attack", "Sure Strike"],
    "Half-Orc": ["Total Kill", "Bash", "Strike", "Wall of Steel"],
    "Halfling": ["Lunge", "Engage & Withdraw", "Wall of Steel", "Martial Combat"],
    "Dwarf"   : ["Counterstrike", "Bash", "Parry", "Wall of Steel"],
    "Half-Elf": ["Slash", "Strike", "Lunge", "Wall of Steel"],
    "Elf"     : ["Wall of Steel", "Lunge", "Engage & Withdraw", "Slash"],
    "Peasant" : ["Strike", "Total Kill"],
}


# ---------------------------------------------------------------------------
# AI GEAR ASSIGNMENT
# ---------------------------------------------------------------------------

def assign_ai_gear(warrior: Warrior, tier: int = 1):
    """
    Equip an AI warrior with appropriate gear for their race and stats.
    tier 1 = new warrior (light gear)
    tier 5 = veteran (heavy gear)
    """
    race  = warrior.race.name
    is_dw = (race == "Dwarf")

    # --- Primary weapon ---
    prefs = RACE_WEAPON_PREFS.get(race, RACE_WEAPON_PREFS["Human"])
    primary = _best_wieldable_weapon(warrior, prefs)
    warrior.primary_weapon = primary

    # --- Secondary weapon ---
    sec_prefs = RACE_SECONDARY_PREFS.get(race, ["Open Hand"])
    secondary = _best_wieldable_weapon(warrior, sec_prefs, allow_open_hand=True)
    # If primary is two-handed, secondary must be open hand
    try:
        pw = get_weapon(primary)
        if pw.two_hand:
            secondary = "Open Hand"
    except ValueError:
        pass
    warrior.secondary_weapon = secondary

    # --- Armor (scale with tier) ---
    tier_idx     = min(tier - 1, len(ARMOR_TIERS) - 1)
    armor_choice = None
    for i in range(tier_idx, -1, -1):
        candidate = ARMOR_TIERS[i]
        allowed, _ = can_wear_armor(candidate, warrior.strength, is_dw)
        if allowed:
            armor_choice = candidate
            break
    warrior.armor = armor_choice or "Cloth"

    # --- Helm ---
    helm_tier_idx = min(tier - 1, len(HELM_TIERS) - 1)
    warrior.helm  = HELM_TIERS[helm_tier_idx]


def _best_wieldable_weapon(
    warrior: Warrior,
    prefs: List[str],
    allow_open_hand: bool = False,
) -> str:
    """
    From a preference list, return the first weapon the warrior can wield
    without a full penalty. Falls back to Open Hand.
    """
    from weapons import max_weapon_weight, strength_penalty
    for wpn_name in prefs:
        try:
            w = get_weapon(wpn_name)
            pen = strength_penalty(w.weight, warrior.strength, w.two_hand)
            if pen < 0.30:   # Allow up to 30% penalty — still functional
                return wpn_name
        except ValueError:
            continue
    return "Open Hand"


# ---------------------------------------------------------------------------
# AI STRATEGY ASSIGNMENT
# ---------------------------------------------------------------------------

def assign_ai_strategies(warrior: Warrior, tier: int = 1):
    """
    Assign a sensible strategy set based on race, weapon, and tier.
    Lower tier = simpler (fewer strategies).
    Higher tier = more complex (up to 6 strategies with nuanced triggers).
    """
    race     = warrior.race.name
    styles   = RACE_STYLE_PREFS.get(race, ["Strike", "Counterstrike"])
    main_style  = styles[0]
    backup_style= styles[1] if len(styles) > 1 else "Parry"

    strategies = []

    if tier >= 3:
        # Add a heavy damage trigger
        strategies.append(Strategy(
            trigger       = "You have taken heavy damage",
            style         = "Parry",
            activity      = 3,
            aim_point     = "None",
            defense_point = "Chest",
        ))

    if tier >= 2:
        # Add a foe-on-ground trigger
        strategies.append(Strategy(
            trigger       = "Your foe is on the ground",
            style         = main_style,
            activity      = min(9, 6 + tier),
            aim_point     = "Head",
            defense_point = "None",
        ))

    if tier >= 4:
        # Add a tired trigger
        strategies.append(Strategy(
            trigger       = "You are tired",
            style         = backup_style,
            activity      = 4,
            aim_point     = "None",
            defense_point = "Chest",
        ))

    # Always-on default strategy
    # Activity: lower tiers are less aggressive
    base_activity = min(9, 4 + tier)
    strategies.append(Strategy(
        trigger       = "Always",
        style         = main_style,
        activity      = base_activity,
        aim_point     = random.choice(["Head", "Chest", "None"]),
        defense_point = "Chest",
    ))

    warrior.strategies = strategies


# ---------------------------------------------------------------------------
# AI TRAINING SELECTION
# ---------------------------------------------------------------------------

def assign_ai_training(warrior: Warrior, tier: int = 1):
    """
    Choose up to 3 training targets for this warrior.
    Higher tier warriors invest in advanced skills.
    """
    race       = warrior.race.name
    weapon_key = warrior.primary_weapon.lower().replace(" ", "_").replace("&","and")
    trains     = []

    if tier == 1:
        # Beginners: train their primary weapon + constitution
        trains = [weapon_key, "constitution", weapon_key]
    elif tier == 2:
        trains = [weapon_key, weapon_key, "dodge"]
    elif tier == 3:
        trains = [weapon_key, "parry", "initiative"]
    elif tier == 4:
        trains = [weapon_key, "dodge", "parry"]
    else:
        # Veteran: advanced skills
        skill_pool = ["dodge", "parry", "initiative", "lunge", "feint", weapon_key]
        trains     = random.sample(skill_pool, min(3, len(skill_pool)))

    warrior.trains = trains[:3]


# ---------------------------------------------------------------------------
# RIVAL MANAGER
# ---------------------------------------------------------------------------

class RivalManager:
    """
    A persistent AI opponent with a full team that improves over time.

    tier: 1–5 (difficulty).
      tier 1 = fresh beginner team
      tier 5 = veteran champions
    fights_completed: how many turns this rival has participated in.
      Used to gradually improve the team.
    """

    def __init__(
        self,
        manager_name : str,
        team_name    : str,
        tier         : int = 1,
        manager_id   : int = 0,
    ):
        self.manager_name      = manager_name
        self.team_name         = team_name
        self.tier              = max(1, min(5, tier))
        self.manager_id        = manager_id
        self.fights_completed  = 0
        self.team              = self._build_team()

    def _build_team(self) -> Team:
        """Create the team with race-appropriate gear and strategies."""
        team = Team(
            team_name    = self.team_name,
            manager_name = self.manager_name,
            team_id      = self.manager_id,
        )

        races = list_playable_races()
        # Weight race selection toward interesting variety
        race_pool = races * 2   # All races possible

        for _ in range(TEAM_SIZE):
            race   = random.choice(race_pool)
            gender = random.choice(["Male", "Female"])

            # Tier-scaled stat budget
            # Tier 1: low base stats. Tier 5: near-max stats.
            base_range = (
                max(STAT_MIN, 5 + self.tier),
                min(STAT_MAX, 10 + self.tier * 2),
            )
            stats = {a: random.randint(*base_range) for a in ATTRIBUTES}

            w = Warrior(
                name         = _generate_warrior_name(),
                race_name    = race,
                gender       = gender,
                **stats,
            )

            assign_ai_gear(w, self.tier)
            assign_ai_strategies(w, self.tier)
            assign_ai_training(w, self.tier)

            team.add_warrior(w)

        return team

    def post_fight_update(self):
        """
        Called after each turn to apply training, replace dead warriors,
        and possibly promote the team to a higher tier.
        """
        self.fights_completed += 1

        for warrior in list(self.team.warriors):
            if warrior is None:
                continue
            if not warrior.is_alive:
                self.team.kill_warrior(warrior)
                continue

            # Apply training
            for skill in warrior.trains[:3]:
                warrior.train_skill(skill)
            warrior.recalculate_derived()

            # Re-assign strategies as warrior grows
            assign_ai_training(warrior, self.tier)
            assign_ai_strategies(warrior, self.tier)

        # Tier promotion every 10 fights (up to tier 5)
        if self.fights_completed % 10 == 0 and self.tier < 5:
            self.tier += 1
            # Re-equip team with better gear for new tier
            for w in self.team.warriors:
                if w:
                    assign_ai_gear(w, self.tier)

    def to_dict(self) -> dict:
        return {
            "manager_name"    : self.manager_name,
            "team_name"       : self.team_name,
            "tier"            : self.tier,
            "manager_id"      : self.manager_id,
            "fights_completed": self.fights_completed,
            "team"            : self.team.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RivalManager":
        rm = cls.__new__(cls)
        rm.manager_name      = data["manager_name"]
        rm.team_name         = data["team_name"]
        rm.tier              = data.get("tier", 1)
        rm.manager_id        = data.get("manager_id", 0)
        rm.fights_completed  = data.get("fights_completed", 0)
        from team import Team
        rm.team = Team.from_dict(data["team"])
        return rm

    def __repr__(self) -> str:
        w_count = len(self.team.active_warriors)
        return (
            f"RivalManager({self.manager_name!r}, "
            f"team={self.team_name!r}, tier={self.tier}, "
            f"fights={self.fights_completed}, warriors={w_count})"
        )


# ---------------------------------------------------------------------------
# NAME GENERATORS
# ---------------------------------------------------------------------------

_MANAGER_FIRST = [
    "The", "Dark", "Iron", "Blood", "Stone", "Swift", "Silent",
    "Mad", "Grim", "Bold", "Cruel", "Wise", "Old",
]
_MANAGER_LAST = [
    "Warlord", "Butcher", "Hammer", "Blade", "Fang", "Wolf",
    "Raven", "Shadow", "Baron", "Tyrant", "Champion", "Master",
    "Skull", "Hand", "Eye", "Fist", "Claw",
]
_TEAM_ADJECTIVES = [
    "Eternal", "Iron", "Crimson", "Black", "Savage", "Dread",
    "Burning", "Thunder", "Stone", "Grim", "Wild",
]
_TEAM_NOUNS = [
    "Champions", "Wolves", "Blades", "Hammers", "Ravens",
    "Crushers", "Slayers", "Fists", "Stalkers", "Reapers",
    "Fangs", "Shields",
]

_WARRIOR_PREFIXES = [
    "Grak", "Sven", "Mira", "Drok", "Zara", "Brul", "Kess",
    "Thor", "Nyx", "Borak", "Lira", "Fen", "Gara", "Wulf",
    "Tyra", "Orm", "Hela", "Bran", "Ryn", "Dex", "Skaa",
    "Vorn", "Petra", "Ulka", "Drak",
]
_WARRIOR_SUFFIXES = [
    "the Crusher", "Blackhand", "Ironhide", "Deathgrip",
    "Smasher", "the Bloody", "Bonesnap", "the Fearsome",
    "Stonefist", "the Relentless", "Skullcleave", "Redblade",
    "the Grim", "Sevenfinger", "the Unyielding",
]

_used_names: set = set()


def _generate_warrior_name() -> str:
    for _ in range(50):
        name = f"{random.choice(_WARRIOR_PREFIXES)} {random.choice(_WARRIOR_SUFFIXES)}"
        if name not in _used_names:
            _used_names.add(name)
            return name
    return f"Fighter_{random.randint(1000, 9999)}"


def _generate_manager_name() -> str:
    return f"{random.choice(_MANAGER_FIRST)} {random.choice(_MANAGER_LAST)}"


def _generate_team_name() -> str:
    return f"The {random.choice(_TEAM_ADJECTIVES)} {random.choice(_TEAM_NOUNS)}"


# ---------------------------------------------------------------------------
# RIVAL POOL SAVE / LOAD
# ---------------------------------------------------------------------------

def save_rivals(rivals: List[RivalManager]):
    """Persist the rival pool to disk."""
    os.makedirs(os.path.dirname(RIVALS_FILE), exist_ok=True)
    data = [r.to_dict() for r in rivals]
    with open(RIVALS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_rivals() -> List[RivalManager]:
    """Load the rival pool from disk. Returns empty list if no save exists."""
    if not os.path.exists(RIVALS_FILE):
        return []
    try:
        with open(RIVALS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [RivalManager.from_dict(d) for d in data]
    except Exception as e:
        print(f"  WARNING: Could not load rivals: {e}. Starting fresh.")
        return []


def get_or_create_rivals() -> List[RivalManager]:
    """
    Load the rival pool. If fewer than INITIAL_POOL_SIZE exist,
    generate new rivals to fill the pool.
    """
    rivals = load_rivals()

    while len(rivals) < INITIAL_POOL_SIZE:
        tier = random.choices(
            [1, 1, 1, 2, 2, 3],   # Most rivals start at tier 1-2
            weights=[30, 25, 20, 15, 7, 3],
            k=1,
        )[0]
        rm = RivalManager(
            manager_name = _generate_manager_name(),
            team_name    = _generate_team_name(),
            tier         = tier,
            manager_id   = len(rivals) + 100,
        )
        rivals.append(rm)

    return rivals


def rival_summary(rivals: List[RivalManager]) -> str:
    """Print a summary of the rival pool."""
    lines = ["  RIVAL MANAGER POOL", "  " + "=" * 50]
    for rm in rivals:
        active = len(rm.team.active_warriors)
        lines.append(
            f"  [{rm.manager_id:03d}] {rm.manager_name:<22} "
            f"Team: {rm.team_name:<28} "
            f"Tier:{rm.tier}  Fights:{rm.fights_completed}  Warriors:{active}"
        )
    return "\n".join(lines)
