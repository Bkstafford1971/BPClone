# =============================================================================
# weapons.py — Blood Pit Weapon Definitions
# =============================================================================
# Contains:
#   - Full weapon table (44 weapons, matching the 44 weapon skills)
#   - Strength requirement lookup
#   - Under-strength penalty calculation (proportional attack rate + damage)
#   - Special weapon rules (armor-piercing, flail bypass, MC-compatible, etc.)
#   - Charge attack eligibility (spears only)
#   - Two-hand handling
# =============================================================================

from dataclasses import dataclass, field
from typing import Optional, List


# ---------------------------------------------------------------------------
# STRENGTH → MAX CARRY WEIGHT TABLE
# Directly from the player's guide.
# ---------------------------------------------------------------------------

STRENGTH_CARRY_TABLE = [
    (3,  3,  0.0),
    (4,  6,  1.0),
    (7,  8,  2.0),
    (9,  11, 3.0),
    (12, 13, 4.0),
    (14, 16, 5.0),
    (17, 18, 6.0),
    (19, 21, 7.0),
    (22, 23, 8.0),
    (24, 25, 9.0),
]


def max_weapon_weight(strength: int) -> float:
    """
    Return the maximum weapon weight a warrior can wield one-handed
    based on their Strength.  Two-handed weapons get a +1 weight allowance
    (applied at equip time, not here).
    """
    for lo, hi, capacity in STRENGTH_CARRY_TABLE:
        if lo <= strength <= hi:
            return capacity
    return 0.0


def strength_penalty(weapon_weight: float, strength: int, two_handed: bool = False) -> float:
    """
    Calculate the under-strength penalty fraction (0.0 = no penalty, 1.0 = unusable).

    APPROX: The guide says under-strength warriors suffer proportional
    attack-rate and damage penalties. We model this as:

        effective_capacity = max_weapon_weight(strength) + (1.0 if two_handed else 0.0)
        if weapon_weight <= effective_capacity: penalty = 0.0
        else:
            overage = weapon_weight - effective_capacity
            penalty = min(1.0, overage / effective_capacity)

    So a warrior who is exactly 1 weight point over capacity suffers a
    penalty equal to (1 / their capacity), never exceeding 100%.

    Returns a float 0.0–1.0.  Callers multiply attack rate and damage by
    (1.0 - penalty).
    """
    capacity = max_weapon_weight(strength) + (1.0 if two_handed else 0.0)
    if weapon_weight <= capacity:
        return 0.0
    if capacity <= 0:
        return 1.0
    overage = weapon_weight - capacity
    return min(1.0, overage / capacity)


# ---------------------------------------------------------------------------
# WEAPON CATEGORIES
# ---------------------------------------------------------------------------

SWORD_KNIFE    = "Sword/Knife"
AXE_PICK       = "Axe/Pick"
HAMMER_MACE    = "Hammer/Mace"
POLEARM_SPEAR  = "Polearm/Spear"
FLAIL          = "Flail"
STAVE          = "Stave"
SHIELD         = "Shield"
ODDBALL        = "Oddball"

ALL_CATEGORIES = [
    SWORD_KNIFE, AXE_PICK, HAMMER_MACE, POLEARM_SPEAR,
    FLAIL, STAVE, SHIELD, ODDBALL,
]


# ---------------------------------------------------------------------------
# WEAPON DATACLASS
# ---------------------------------------------------------------------------

@dataclass
class Weapon:
    """
    A single weapon available in Blood Pit.

    skill_key:   Matches the key used in warrior.skills (snake_case).
    display:     Human-readable name as shown in fight narratives.
    weight:      From the weapon table. Compared against STR carry capacity.
    throwable:   Can be used with Opportunity Throw style.
    two_hand:    Designed for two hands (assign Open Hand to secondary).
                 Two-handed use grants +1 to effective STR carry capacity.
    category:    Weapon family. Determines narrative line pools and style bonuses.

    Special flags (all Boolean):
      armor_piercing   — Does extra damage vs Scale/Chain/Half-Plate/Plate.
                         Weapons: Stiletto, Scythe, Small Pick, Military Pick,
                                  Great Pick, Pick Axe.
      mc_compatible    — Can be used with Martial Combat style.
                         Weapons: Stiletto, Dagger, Knife, Quarterstaff,
                                  Net, Great Staff, Open Hand.
      flail_bypass     — Can wrap around shields and blocking weapons.
                         All Flails.
      charge_attack    — Gets the special spear charge attack based on Charge skill.
                         All Polearms/Spears except Cestus.
      can_disarm       — Has special disarm interaction. Net, Swordbreaker,
                         Scythe, Ball & Chain.
      can_sweep        — Has sweep interaction. Ball & Chain, all Flails.
      is_shield        — Is a shield (affects parry calculations differently).

    preferred_styles: Styles this weapon works especially well with.
                      Used by the AI strategy selector and narrative engine.
    weak_styles:      Styles this weapon actively works against.
    """

    skill_key       : str
    display         : str
    weight          : float
    throwable       : bool
    two_hand        : bool          # Designed for two hands
    category        : str

    # Special rules
    armor_piercing  : bool = False
    mc_compatible   : bool = False
    flail_bypass    : bool = False
    charge_attack   : bool = False
    can_disarm      : bool = False
    can_sweep       : bool = False
    is_shield       : bool = False

    # Style guidance (informational — used by AI and narrative engine)
    preferred_styles: List[str] = field(default_factory=list)
    weak_styles     : List[str] = field(default_factory=list)

    # Flavor notes from the player's guide (used to generate manager tips)
    notes           : str = ""

    @property
    def effective_one_hand_capacity_needed(self) -> float:
        """The strength capacity needed to wield this weapon one-handed."""
        return self.weight

    @property
    def effective_two_hand_capacity_needed(self) -> float:
        """The strength capacity needed to wield this weapon two-handed."""
        return max(0.0, self.weight - 1.0)

    def penalty_for(self, strength: int, two_handed: bool = False) -> float:
        """
        Shorthand: get the under-strength penalty for a given warrior STR.
        Returns 0.0–1.0 (0 = no penalty, 1 = completely ineffective).
        """
        return strength_penalty(self.weight, strength, two_handed)

    def can_wield(self, strength: int, two_handed: bool = False) -> bool:
        """
        True if the warrior can wield this weapon with no penalty.
        Does NOT block equipping — just indicates whether full effectiveness
        is available.
        """
        return self.penalty_for(strength, two_handed) == 0.0

    def __str__(self) -> str:
        flags = []
        if self.throwable:      flags.append("throw")
        if self.two_hand:       flags.append("2H")
        if self.armor_piercing: flags.append("AP")
        if self.flail_bypass:   flags.append("bypass")
        if self.charge_attack:  flags.append("charge")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        return f"{self.display} (wt:{self.weight}){flag_str}"


# ---------------------------------------------------------------------------
# SPECIAL OPEN HAND
# ---------------------------------------------------------------------------

OPEN_HAND = Weapon(
    skill_key        = "open_hand",
    display          = "Open Hand",
    weight           = 0.0,
    throwable        = False,
    two_hand         = False,
    category         = ODDBALL,
    mc_compatible    = True,
    notes            = (
        "Works surprisingly well in Strike and MC styles, but damage is "
        "anemic without high Brawl skill. Assign to secondary for two-handed use."
    ),
    preferred_styles = ["Strike", "Martial Combat"],
)


# ---------------------------------------------------------------------------
# ALL WEAPONS
# Full table — exactly 44 weapons matching the 44 weapon skills.
# Order mirrors the weapon table in the player's guide.
# ---------------------------------------------------------------------------

WEAPONS: dict[str, Weapon] = {

    # =========================================================================
    # SWORDS & KNIVES
    # =========================================================================

    "stiletto": Weapon(
        skill_key     = "stiletto",
        display       = "Stiletto",
        weight        = 1.0,
        throwable     = True,
        two_hand      = False,
        category      = SWORD_KNIFE,
        armor_piercing= True,
        mc_compatible = True,
        notes=(
            "Very high attack rate. Good for weak warriors against heavy armor. "
            "Ultimately does too little damage for high-level play. Halflings like it."
        ),
        preferred_styles=["Lunge", "Martial Combat", "Calculated Attack"],
        weak_styles   =["Bash", "Total Kill"],
    ),

    "knife": Weapon(
        skill_key     = "knife",
        display       = "Knife",
        weight        = 2.0,
        throwable     = True,
        two_hand      = False,
        category      = SWORD_KNIFE,
        mc_compatible = True,
        notes="Attack rate underwhelming for its size. Few warriors succeed with this.",
        preferred_styles=["Strike", "Lunge"],
    ),

    "dagger": Weapon(
        skill_key     = "dagger",
        display       = "Dagger",
        weight        = 2.3,
        throwable     = True,
        two_hand      = False,
        category      = SWORD_KNIFE,
        mc_compatible = True,
        notes=(
            "Very high attack rate. Good in the hands of Elves. Like all small "
            "weapons, insufficient damage at the high end."
        ),
        preferred_styles=["Lunge", "Wall of Steel", "Martial Combat"],
    ),

    "short_sword": Weapon(
        skill_key     = "short_sword",
        display       = "Short Sword",
        weight        = 3.0,
        throwable     = False,
        two_hand      = False,
        category      = SWORD_KNIFE,
        notes=(
            "One of the ultimate weapons. Effective with popular styles for almost "
            "any warrior. Dual Short Sword Elves in Wall of Steel remain top-tier. "
            "The 'Pocket Rocket' Halfling build with a single Short Sword is iconic."
        ),
        preferred_styles=["Wall of Steel", "Strike", "Lunge", "Counterstrike"],
    ),

    "epee": Weapon(
        skill_key     = "epee",
        display       = "Epee",
        weight        = 3.0,
        throwable     = False,
        two_hand      = False,
        category      = SWORD_KNIFE,
        can_disarm    = True,
        notes=(
            "Good attack rate. Decent at disarm. Same late-game damage problem "
            "as other light weapons. Effective in first 50 fights played right."
        ),
        preferred_styles=["Lunge", "Engage & Withdraw", "Sure Strike"],
        weak_styles   =["Bash", "Total Kill"],
    ),

    "scimitar": Weapon(
        skill_key     = "scimitar",
        display       = "Scimitar",
        weight        = 4.5,
        throwable     = False,
        two_hand      = False,
        category      = SWORD_KNIFE,
        notes=(
            "The natural weapon of the Elf. With proper Dexterity, attack rate "
            "is more than adequate. Damage in the mid range. Good all-around."
        ),
        preferred_styles=["Slash", "Lunge", "Wall of Steel"],
    ),

    "longsword": Weapon(
        skill_key     = "longsword",
        display       = "Long Sword",
        weight        = 3.2,
        throwable     = False,
        two_hand      = False,
        category      = SWORD_KNIFE,
        notes=(
            "Attack rate a little slower than expected. Damage low until skilled. "
            "Elves, Half-Elves, and Humans appear most effective."
        ),
        preferred_styles=["Strike", "Counterstrike", "Slash"],
    ),

    "broad_sword": Weapon(
        skill_key     = "broad_sword",
        display       = "Broad Sword",
        weight        = 5.0,
        throwable     = False,
        two_hand      = False,
        category      = SWORD_KNIFE,
        notes=(
            "Not bad, not great. Likes high Dexterity and Elves/Half-Elves. "
            "Needs a bit more than nominal Strength to fully utilize."
        ),
        preferred_styles=["Strike", "Slash", "Counterstrike"],
    ),

    "bastard_sword": Weapon(
        skill_key     = "bastard_sword",
        display       = "Bastard Sword",
        weight        = 6.5,
        throwable     = False,
        two_hand      = True,
        category      = SWORD_KNIFE,
        notes=(
            "High attack rate for a heavy weapon. Excellent with Slash. "
            "Lacks consistent high damage hits for its size. Half-Elves love it."
        ),
        preferred_styles=["Slash", "Strike", "Wall of Steel"],
    ),

    "great_sword": Weapon(
        skill_key     = "great_sword",
        display       = "Great Sword",
        weight        = 8.5,
        throwable     = False,
        two_hand      = True,
        category      = SWORD_KNIFE,
        notes=(
            "In the hands of Half-Orcs, incredible. Stat requirements are very "
            "high but well worth it."
        ),
        preferred_styles=["Slash", "Total Kill", "Bash"],
        weak_styles   =["Lunge", "Calculated Attack"],
    ),

    # =========================================================================
    # AXES & PICKS
    # =========================================================================

    "hatchet": Weapon(
        skill_key     = "hatchet",
        display       = "Hatchet",
        weight        = 2.8,
        throwable     = True,
        two_hand      = False,
        category      = AXE_PICK,
        notes="Light, fast, great early. Fails to deliver damage in later fights. Halflings like it.",
        preferred_styles=["Strike", "Wall of Steel", "Opportunity Throw"],
    ),

    "francisca": Weapon(
        skill_key     = "francisca",
        display       = "Fransisca",
        weight        = 3.8,
        throwable     = True,
        two_hand      = False,
        category      = AXE_PICK,
        notes="Consistently average for most. Dwarves can excel with it.",
        preferred_styles=["Strike", "Bash", "Opportunity Throw"],
    ),

    "battle_axe": Weapon(
        skill_key     = "battle_axe",
        display       = "Battle Axe",
        weight        = 7.5,
        throwable     = False,
        two_hand      = False,
        category      = AXE_PICK,
        notes=(
            "Decent damage but attack rate slightly too slow for top-tier. "
            "Good for Counterstrike users. Excellent for low-DEX, high-STR Dwarves."
        ),
        preferred_styles=["Counterstrike", "Bash", "Strike"],
        weak_styles   =["Wall of Steel"],
    ),

    "great_axe": Weapon(
        skill_key     = "great_axe",
        display       = "Great Axe",
        weight        = 9.0,
        throwable     = False,
        two_hand      = True,
        category      = AXE_PICK,
        notes=(
            "Like the Great Sword for Half-Orcs: can do staggering damage. "
            "Attack rate low due to size. Very high stat requirements."
        ),
        preferred_styles=["Bash", "Total Kill", "Slash"],
    ),

    "small_pick": Weapon(
        skill_key     = "small_pick",
        display       = "Small Pick",
        weight        = 3.2,
        throwable     = False,
        two_hand      = False,
        category      = AXE_PICK,
        armor_piercing= True,
        notes="Fast and effective early, starts becoming ineffective around fight 50. Humans and Halflings.",
        preferred_styles=["Lunge", "Calculated Attack", "Strike"],
    ),

    "military_pick": Weapon(
        skill_key     = "military_pick",
        display       = "Military Pick",
        weight        = 4.5,
        throwable     = False,
        two_hand      = False,
        category      = AXE_PICK,
        armor_piercing= True,
        notes=(
            "A Human favorite. Very effective in higher fights once opponents "
            "have graduated to Scale and above. Works in many popular styles."
        ),
        preferred_styles=["Calculated Attack", "Strike", "Lunge"],
    ),

    "pick_axe": Weapon(
        skill_key     = "pick_axe",
        display       = "Pick Axe",
        weight        = 6.8,
        throwable     = False,
        two_hand      = True,
        category      = AXE_PICK,
        armor_piercing= True,
        notes="New to the Pit. Insufficient data to characterize.",
        preferred_styles=["Bash", "Calculated Attack"],
    ),

    # =========================================================================
    # HAMMERS & MACES
    # =========================================================================

    "hammer": Weapon(
        skill_key     = "hammer",
        display       = "Hammer",
        weight        = 3.0,
        throwable     = True,
        two_hand      = False,
        category      = HAMMER_MACE,
        notes="Above-average damage and attack rate. Viability in late fights debated. Halflings and Humans.",
        preferred_styles=["Bash", "Strike", "Opportunity Throw"],
    ),

    "mace": Weapon(
        skill_key     = "mace",
        display       = "Mace",
        weight        = 4.0,
        throwable     = False,
        two_hand      = False,
        category      = HAMMER_MACE,
        notes="Terribly inconsistent. The Epee of the hammer family.",
        preferred_styles=["Bash", "Strike"],
    ),

    "morningstar": Weapon(
        skill_key     = "morningstar",
        display       = "Morningstar",
        weight        = 5.0,
        throwable     = False,
        two_hand      = False,
        category      = HAMMER_MACE,
        notes=(
            "One of the great weapons. Consistent high damage once minimums met. "
            "Effective for all races."
        ),
        preferred_styles=["Bash", "Strike", "Counterstrike"],
    ),

    "war_hammer": Weapon(
        skill_key     = "war_hammer",
        display       = "War Hammer",
        weight        = 5.0,
        throwable     = False,
        two_hand      = False,
        category      = HAMMER_MACE,
        notes=(
            "A Half-Orc favorite. Good weapon in the right hands. "
            "Requires 20+ Strength to truly 'sing'."
        ),
        preferred_styles=["Bash", "Total Kill", "Strike"],
    ),

    "maul": Weapon(
        skill_key     = "maul",
        display       = "Maul",
        weight        = 9.0,
        throwable     = False,
        two_hand      = True,
        category      = HAMMER_MACE,
        notes="Too slow to be effective; lacks the defenses to compensate. Requires very high Strength.",
        preferred_styles=["Total Kill", "Bash"],
        weak_styles   =["Wall of Steel", "Lunge"],
    ),

    # =========================================================================
    # POLEARMS & SPEARS
    # =========================================================================

    "boar_spear": Weapon(
        skill_key     = "boar_spear",
        display       = "Boar Spear",
        weight        = 4.0,
        throwable     = True,
        two_hand      = False,
        category      = POLEARM_SPEAR,
        charge_attack = True,
        notes=(
            "Arguably the best weapon in the game. Effective in Lunge, Wall of "
            "Steel, and Strike. Can throw. Use with a shield. "
            "Great attack rate and damage. Favored by all races."
        ),
        preferred_styles=["Lunge", "Wall of Steel", "Strike", "Opportunity Throw"],
    ),

    "long_spear": Weapon(
        skill_key     = "long_spear",
        display       = "Long Spear",
        weight        = 7.2,
        throwable     = False,
        two_hand      = True,
        category      = POLEARM_SPEAR,
        charge_attack = True,
        notes=(
            "Good in Half-Elves and some Half-Orcs. Same advantages as Boar Spear "
            "with more damage kick. Excels at 7+ APM."
        ),
        preferred_styles=["Lunge", "Strike", "Wall of Steel"],
    ),

    "pole_axe": Weapon(
        skill_key     = "pole_axe",
        display       = "Pole Axe",
        weight        = 8.0,
        throwable     = False,
        two_hand      = True,
        category      = POLEARM_SPEAR,
        charge_attack = True,
        notes=(
            "A Half-Elf favorite that underperforms for other races. "
            "Half-Orcs have had decent success with it."
        ),
        preferred_styles=["Strike", "Lunge", "Wall of Steel"],
    ),

    "halberd": Weapon(
        skill_key     = "halberd",
        display       = "Halberd",
        weight        = 9.5,
        throwable     = False,
        two_hand      = True,
        category      = POLEARM_SPEAR,
        charge_attack = True,
        notes=(
            "Tough to use but certain Half-Orcs devastate with it. "
            "Requires very high Strength. Also known to work with Engage & Withdraw."
        ),
        preferred_styles=["Total Kill", "Engage & Withdraw"],
    ),

    # =========================================================================
    # FLAILS
    # =========================================================================

    "flail": Weapon(
        skill_key     = "flail",
        display       = "Flail",
        weight        = 3.6,
        throwable     = False,
        two_hand      = False,
        category      = FLAIL,
        flail_bypass  = True,
        can_sweep     = True,
        notes=(
            "Unique: most of its damage is based on SIZE not STR. "
            "Elves like Flails; most races do well."
        ),
        preferred_styles=["Strike", "Wall of Steel", "Bash"],
    ),

    "bladed_flail": Weapon(
        skill_key     = "bladed_flail",
        display       = "Bladed Flail",
        weight        = 5.6,
        throwable     = False,
        two_hand      = False,
        category      = FLAIL,
        flail_bypass  = True,
        can_sweep     = True,
        notes=(
            "Halflings and Half-Orcs love it. Great damage against light armor; "
            "huge drop-off against Scale+. Hard to use as a top-tier late weapon."
        ),
        preferred_styles=["Bash", "Strike", "Wall of Steel"],
    ),

    "war_flail": Weapon(
        skill_key     = "war_flail",
        display       = "War Flail",
        weight        = 6.0,
        throwable     = False,
        two_hand      = False,
        category      = FLAIL,
        flail_bypass  = True,
        can_sweep     = True,
        notes="One of the best weapons in the game, especially for Half-Orcs. Damage tuned down slightly from original legendary status.",
        preferred_styles=["Total Kill", "Bash", "Strike"],
    ),

    "battle_flail": Weapon(
        skill_key     = "battle_flail",
        display       = "Battle Flail",
        weight        = 7.5,
        throwable     = False,
        two_hand      = True,
        category      = FLAIL,
        flail_bypass  = True,
        can_sweep     = True,
        notes=(
            "Half-Elf favorite (extra attack with it). Attack rate too low vs "
            "damage rate compared to War Flail. Half-Orcs also succeed."
        ),
        preferred_styles=["Bash", "Total Kill"],
        weak_styles   =["Lunge", "Calculated Attack"],
    ),

    # =========================================================================
    # STAVES
    # =========================================================================

    "quarterstaff": Weapon(
        skill_key     = "quarterstaff",
        display       = "Quarterstaff",
        weight        = 4.0,
        throwable     = False,
        two_hand      = True,
        category      = STAVE,
        mc_compatible = True,
        notes=(
            "A Halfling favorite. Good with Martial Combat. "
            "Currently underwhelming in the Pit."
        ),
        preferred_styles=["Martial Combat", "Strike", "Parry"],
    ),

    "great_staff": Weapon(
        skill_key     = "great_staff",
        display       = "Great Staff",
        weight        = 7.5,
        throwable     = False,
        two_hand      = True,
        category      = STAVE,
        mc_compatible = True,
        notes="Larger, heavier Quarterstaff. Attack rate lower than expected; too slow for reliable parry.",
        preferred_styles=["Martial Combat", "Strike"],
    ),

    # =========================================================================
    # SHIELDS
    # =========================================================================

    "buckler": Weapon(
        skill_key     = "buckler",
        display       = "Buckler",
        weight        = 3.2,
        throwable     = False,
        two_hand      = False,
        category      = SHIELD,
        is_shield     = True,
        notes="Fairly weak shield. Not really worth using.",
        preferred_styles=["Counterstrike", "Parry", "Defend"],
    ),

    "target_shield": Weapon(
        skill_key     = "target_shield",
        display       = "Target Shield",
        weight        = 5.2,
        throwable     = False,
        two_hand      = False,
        category      = SHIELD,
        is_shield     = True,
        notes="Current sweet-spot shield for Dwarves.",
        preferred_styles=["Counterstrike", "Parry", "Defend", "Wall of Steel"],
    ),

    "tower_shield": Weapon(
        skill_key     = "tower_shield",
        display       = "Tower Shield",
        weight        = 7.2,
        throwable     = False,
        two_hand      = False,
        category      = SHIELD,
        is_shield     = True,
        notes="Once legendary, now tuned. Only shield that helps against very skilled warriors. Half-Orcs prefer it.",
        preferred_styles=["Counterstrike", "Parry", "Defend"],
    ),

    # =========================================================================
    # ODDBALLS
    # =========================================================================

    "cestus": Weapon(
        skill_key     = "cestus",
        display       = "Cestus",
        weight        = 1.5,
        throwable     = False,
        two_hand      = False,
        category      = ODDBALL,
        mc_compatible = True,
        notes=(
            "Outside MC, underwhelming. Some Half-Elf Martial Artists get "
            "incredible damage with it. Cannot hold another weapon in that hand."
        ),
        preferred_styles=["Martial Combat"],
    ),

    "trident": Weapon(
        skill_key     = "trident",
        display       = "Trident",
        weight        = 4.3,
        throwable     = False,
        two_hand      = False,       # Needs 2H unless warrior is very strong
        category      = ODDBALL,
        charge_attack = True,        # Three-pronged pole — classified with spears
        notes=(
            "Once much stronger. Gets good results for Dwarves and Half-Elves. "
            "No longer competitive with Boar Spear."
        ),
        preferred_styles=["Lunge", "Strike"],
    ),

    "net": Weapon(
        skill_key     = "net",
        display       = "Net",
        weight        = 3.0,
        throwable     = False,
        two_hand      = False,
        category      = ODDBALL,
        mc_compatible = True,
        can_disarm    = True,
        notes=(
            "Specialty weapon. Success with Dwarves. Throws frustrating entangle "
            "attacks. Works with Sure Strike and Wall of Steel. Hit and miss."
        ),
        preferred_styles=["Sure Strike", "Wall of Steel"],
    ),

    "scythe": Weapon(
        skill_key     = "scythe",
        display       = "Scythe",
        weight        = 3.5,
        throwable     = False,
        two_hand      = False,
        category      = ODDBALL,
        armor_piercing= True,
        can_disarm    = True,
        notes=(
            "Sings in Elf hands. Armor-piercing blade. Can use Slash effectively. "
            "Devastating for almost any warrior except Half-Orcs."
        ),
        preferred_styles=["Slash", "Calculated Attack", "Lunge"],
    ),

    "great_pick": Weapon(
        skill_key     = "great_pick",
        display       = "Great Pick",
        weight        = 9.0,
        throwable     = False,
        two_hand      = True,
        category      = ODDBALL,
        armor_piercing= True,
        notes=(
            "In the right Half-Orc or Dwarf hands: unstoppable killing machine. "
            "Against light armor (CB or leather) it's like hitting with a wiffle bat."
        ),
        preferred_styles=["Total Kill", "Bash", "Calculated Attack"],
    ),

    "javelin": Weapon(
        skill_key     = "javelin",
        display       = "Javelin",
        weight        = 2.5,
        throwable     = True,
        two_hand      = False,
        category      = ODDBALL,
        charge_attack = True,
        notes=(
            "Great below 50 fights. Has many Boar Spear benefits at a higher "
            "attack rate. Halflings and Elves both like it."
        ),
        preferred_styles=["Lunge", "Opportunity Throw", "Strike"],
    ),

    "ball_and_chain": Weapon(
        skill_key     = "ball_and_chain",
        display       = "Ball & Chain",
        weight        = 8.5,
        throwable     = False,
        two_hand      = True,
        category      = ODDBALL,
        flail_bypass  = True,
        can_disarm    = True,
        can_sweep     = True,
        notes=(
            "Very high damage rate but very low attack rate. "
            "Can finish a fight in 2 hits — if you survive the 10 they land first."
        ),
        preferred_styles=["Total Kill", "Bash"],
        weak_styles   =["Wall of Steel", "Lunge"],
    ),

    "swordbreaker": Weapon(
        skill_key     = "swordbreaker",
        display       = "Swordbreaker",
        weight        = 3.2,
        throwable     = False,
        two_hand      = False,
        category      = ODDBALL,
        can_disarm    = True,
        notes=(
            "Best in off-hand vs bladed weapons. Lack of bladed weapons in the "
            "Pit limits its value. Very effective if you know your opponent uses blades."
        ),
        preferred_styles=["Counterstrike", "Decoy"],
    ),

    "open_hand": OPEN_HAND,
}


# ---------------------------------------------------------------------------
# LOOKUP HELPERS
# ---------------------------------------------------------------------------

def get_weapon(name: str) -> Weapon:
    """
    Retrieve a Weapon by display name or skill_key (case-insensitive).
    Raises ValueError if not found.
    """
    # Try skill_key first
    key = name.lower().replace(" ", "_").replace("&", "and")
    if key in WEAPONS:
        return WEAPONS[key]

    # Try display name match
    for w in WEAPONS.values():
        if w.display.lower() == name.lower():
            return w

    valid = [w.display for w in WEAPONS.values()]
    raise ValueError(
        f"Unknown weapon: '{name}'.\n"
        f"Valid weapons: {', '.join(sorted(valid))}"
    )


def throwable_weapons() -> List[Weapon]:
    """Return all weapons that can be thrown."""
    return [w for w in WEAPONS.values() if w.throwable]


def mc_weapons() -> List[Weapon]:
    """Return all weapons compatible with Martial Combat style."""
    return [w for w in WEAPONS.values() if w.mc_compatible]


def armor_piercing_weapons() -> List[Weapon]:
    """Return all armor-piercing weapons (extra damage vs Scale+)."""
    return [w for w in WEAPONS.values() if w.armor_piercing]


def spear_weapons() -> List[Weapon]:
    """Return all weapons that can use the charge attack."""
    return [w for w in WEAPONS.values() if w.charge_attack]


def list_weapons_by_category(category: str) -> List[Weapon]:
    """Return all weapons in a given category."""
    return [w for w in WEAPONS.values() if w.category == category]


def weapons_for_style(style: str) -> List[Weapon]:
    """Return weapons that list a style as preferred."""
    return [w for w in WEAPONS.values() if style in w.preferred_styles]
