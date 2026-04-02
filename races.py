# =============================================================================
# races.py — BLOODSPIRE Race Definitions
# =============================================================================
# Contains all 6 playable races and 2 NPC races with their modifiers.
#
# APPROXIMATION PHILOSOPHY (used throughout this file):
#   The guide uses qualitative language ("slight bonus", "very high damage bonus").
#   We convert these to numeric values using this scale:
#     "slight"    = ±1
#     "moderate"  = ±2
#     "large"     = ±3
#     "very high" = ±4
#     "major"     = ±5
#   All approximations are marked with "# APPROX:" in comments.
# =============================================================================

from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# RACIAL MODIFIER DATACLASS
# ---------------------------------------------------------------------------

@dataclass
class RacialModifiers:
    """
    Numeric combat modifiers applied to a warrior based on race.
    These are applied at combat time, not baked into base stats,
    so the raw stat values always reflect the warrior's true attributes.
    """

    # --- Hit Points ---
    hp_bonus: int = 0           # Flat bonus/penalty to max HP

    # --- Damage ---
    damage_bonus: int = 0       # Flat bonus to damage dealt per hit
    damage_penalty: int = 0     # Flat penalty to damage dealt per hit

    # --- Attack Rate ---
    # Stored as a modifier to "actions per minute" on a 0-100 internal scale.
    # APPROX: Each point ≈ roughly 0.1 attacks/minute at base dex.
    attack_rate_bonus: int = 0
    attack_rate_penalty: int = 0

    # --- Initiative ---
    initiative_bonus: int = 0   # Bonus to initiative rolls
    initiative_penalty: int = 0 # Penalty to initiative rolls

    # --- Defense ---
    dodge_bonus: int = 0
    dodge_penalty: int = 0
    parry_bonus: int = 0
    parry_penalty: int = 0

    # --- Special Flags (True/False abilities) ---
    armor_capacity_bonus: bool = False   # Dwarf: can carry heavier armor than STR alone allows
    shield_bonus: bool = False           # Dwarf: extra bonus when a shield is equipped
    dual_weapon_bonus: bool = False      # Elf: bonus when both hands hold weapons
    martial_combat_bonus: bool = False   # Halfling: extra MC effectiveness
    trains_stats_faster: bool = False    # Human: attributes improve more easily
    fewer_perms: bool = False            # Human: lower permanent injury chance
    bigger_weapons_bonus: bool = False   # Half-Elf: counts as 1 STR higher for weapon weight reqs

    # --- Strength Penalty ---
    strength_penalty: int = 0        # Additional STR penalty (e.g. Goblin -2, Tabaxi -2)

    # --- Goblin Special Abilities ---
    thrown_mastery: bool = False      # +2 to Opportunity Throw
    scavenger: bool = False           # High chance to pick up dropped weapons
    heavy_weapon_penalty: bool = False # Severe penalty for weapons >= 4.0 weight

    # --- Gnome Special Abilities ---
    counterstrike_bonus: bool = False # Bonus on ripostes and counter-attacks
    tactician_edge: bool = False      # Better vs aggressive, worse vs methodical

    # --- Lizardfolk Special Abilities ---
    natural_weapons_bonus: int = 0    # +X damage to Martial Combat / brawl styles
    natural_armor_scales: bool = False # Has natural armor (Scale equivalent)
    armor_layering_allowed: bool = False # Can layer armor with scaling rules

    # --- Tabaxi Special Abilities ---
    acrobatic_advantage: bool = False # Resist knockdowns, acrobatic maneuvers
    frenzy_burst: bool = False        # Once per fight: +3 APM for 3-4 actions
    endurance_penalty: int = 0        # Additional endurance penalty (e.g., Tabaxi -3)

    # --- Flavor / Soft Mechanics ---
    preferred_weapons: List[str] = field(default_factory=list)
    weak_weapons: List[str] = field(default_factory=list)
    favored_opponents: str = ""
    disfavored_opponents: str = ""


# ---------------------------------------------------------------------------
# RACE DATACLASS
# ---------------------------------------------------------------------------

@dataclass
class Race:
    """Defines a single race in BLOODSPIRE."""

    name: str
    is_playable: bool
    description: str
    modifiers: RacialModifiers

    # Physical baselines at average SIZE (12-13), male.
    # Female gets ~97% height, ~90% weight (guide mentions cosmetic differences).
    base_height_in: int    # inches
    base_weight_lbs: int   # pounds

    # Favored/weak enemy races — deliberately None here so discovery is gameplay.
    # The guide says: "discovering this is part of the fun for a new player."
    favored_enemy_race: Optional[str] = None
    weak_against_race: Optional[str] = None


# ---------------------------------------------------------------------------
# ALL RACE DEFINITIONS
# ---------------------------------------------------------------------------

RACES: dict[str, Race] = {

    # =========================================================================
    "Human": Race(
        name="Human",
        is_playable=True,
        description=(
            "The 'base' race — average in all areas, but supremely adaptable. "
            "Humans train attributes more easily than any other race and suffer "
            "fewer permanent injuries. They have no weapon preferences, making "
            "them viable with any fighting style."
        ),
        base_height_in=67,    # 5'7" male SIZE-12 midpoint (range 5'2"–6'4")
        base_weight_lbs=165,
        modifiers=RacialModifiers(
            # Guide: "Humans tend to train stats better and take fewer permanent injuries"
            trains_stats_faster=True,   # APPROX: +20% chance to gain extra train progress
            fewer_perms=True,           # APPROX: -15% base permanent injury chance
            preferred_weapons=[],       # No preference: "basically, they're average"
            favored_opponents="All races — Humans fight well against everyone.",
            disfavored_opponents="None in particular.",
        ),
    ),

    # =========================================================================
    "Half-Orc": Race(
        name="Half-Orc",
        is_playable=True,
        description=(
            "Brutes who rely on pure offense. Half-Orcs deal tremendous damage "
            "and take punishment well, but swing slowly and lack finesse. "
            "They come back from the brink of defeat with single devastating blows."
        ),
        base_height_in=75,    # 6'3" male SIZE-12 midpoint (range 5'5"–7'6")
        base_weight_lbs=259,
        modifiers=RacialModifiers(
            # Guide: "very high damage bonus" → APPROX: +4 flat damage per hit
            damage_bonus=4,
            # Guide: "moderate HP bonus"    → APPROX: +8 max HP
            hp_bonus=8,
            # Guide: "big attack rate penalty"   → APPROX: -3 on action scale
            attack_rate_penalty=3,
            # Guide: "slight dodge and parry penalties" → APPROX: -1 each
            dodge_penalty=1,
            parry_penalty=1,
            preferred_weapons=[
                "War Flail", "Great Axe", "Great Sword", "War Hammer",
                "Battle Flail", "Halberd", "Great Pick", "Tower Shield",
            ],
            favored_opponents="Very small opponents.",
            disfavored_opponents="Quick warriors with thrusting weapons and good dodge.",
        ),
    ),

    # =========================================================================
    "Halfling": Race(
        name="Halfling",
        is_playable=True,
        description=(
            "Infuriating to fight. At 33 inches tall, Halflings are nearly "
            "impossible to hit cleanly. They skitter, hop, and poke at blind spots. "
            "Devastating early, but their light frames limit damage output."
        ),
        base_height_in=46,    # 3'10" male SIZE-12 midpoint (range 3'1"–5'1")
        base_weight_lbs=49,
        modifiers=RacialModifiers(
            # Guide: "big dodge bonus"        → APPROX: +4
            dodge_bonus=4,
            # Guide: "large action rate bonus"→ APPROX: +3
            attack_rate_bonus=3,
            # Guide: "decent Martial Combat bonus"
            martial_combat_bonus=True,
            # Guide: "major damage penalty"   → APPROX: -4 (biggest penalty in game)
            damage_penalty=4,
            # Guide: "average parrying penalty" → APPROX: -2
            parry_penalty=2,
            preferred_weapons=[
                "Short Sword", "Stiletto", "Hatchet", "Quarterstaff",
                "Javelin", "Bladed Flail", "Hammer",
            ],
            weak_weapons=[
                "Maul", "Great Axe", "Great Sword", "Halberd",
                "Battle Flail", "Ball & Chain",
            ],
            favored_opponents="Most opponents — Halflings are balanced offensively and defensively.",
            disfavored_opponents="Warriors who specifically fight small opponents well (e.g. Dwarves).",
        ),
    ),

    # =========================================================================
    "Dwarf": Race(
        name="Dwarf",
        is_playable=True,
        description=(
            "The toughest warriors in the Pit. Dwarves absorb punishment, parry "
            "masterfully, and wear heavier armor than their size suggests. "
            "They are slow but hit with bone-crushing force."
        ),
        base_height_in=50,    # 4'2" male SIZE-12 midpoint (range 3'6"–5'2")
        base_weight_lbs=195,  # Dense — notably heavier than height implies
        modifiers=RacialModifiers(
            # Guide: "most HP in the game"      → APPROX: +12 HP
            hp_bonus=12,
            # Guide: "bonus to damage"          → APPROX: +2
            damage_bonus=2,
            # Guide: "bonus to Parry"           → APPROX: +3
            parry_bonus=3,
            # Guide: "slight penalty to attack rate" → APPROX: -1
            attack_rate_penalty=1,
            # Guide: "slight penalty to dodging" → APPROX: -1
            dodge_penalty=1,
            # Guide: "increased armor carrying capacity"
            armor_capacity_bonus=True,    # APPROX: counts as +3 STR for armor weight only
            # Guide: "bonus when using a shield"
            shield_bonus=True,            # APPROX: +2 effective parry when shield equipped
            preferred_weapons=[
                "Battle Axe", "Fransisca", "Great Axe", "Morningstar",
                "War Hammer", "Boar Spear", "Target Shield", "Net", "Trident",
            ],
            weak_weapons=["Halberd", "Pole Axe"],
            favored_opponents="Very small and very large opponents — Dwarves have something to prove against both.",
            disfavored_opponents="Mid-sized opponents with average stats.",
        ),
    ),

    # =========================================================================
    "Half-Elf": Race(
        name="Half-Elf",
        is_playable=True,
        description=(
            "Angry and capable. Thrown out of Elven society, Half-Elves entered "
            "the Pit to prove themselves. They favor bladed and thrown weapons, "
            "and can wield slightly larger weapons than their build suggests."
        ),
        base_height_in=64,    # 5'4" male SIZE-12 midpoint (range 5'0"–6'0")
        base_weight_lbs=144,
        modifiers=RacialModifiers(
            # Guide: "slight bonus to wielding bigger weapons"
            # APPROX: Treated as +1 effective STR for weapon weight requirements only.
            bigger_weapons_bonus=True,
            preferred_weapons=[
                "Pole Axe", "Bastard Sword", "Long Sword", "Scimitar",
                "Battle Flail", "Scythe", "Javelin", "Broadsword",
            ],
            weak_weapons=[],
            favored_opponents="Average, mid-tier opponents.",
            disfavored_opponents=(
                "Warriors who can take and dish out a lot of damage — "
                "Half-Elves share this weakness with most non-tanks."
            ),
        ),
    ),

    # =========================================================================
    "Elf": Race(
        name="Elf",
        is_playable=True,
        description=(
            "Elusive and fast. Veterans laughed when Elves entered the Pit with "
            "small blades — they stopped laughing quickly. Elves are masters of "
            "speed, dual-wielding, and thrown weapons. Fragile, but nearly untouchable."
        ),
        base_height_in=62,    # 5'2" male SIZE-12 midpoint (range 4'8"–5'11")
        base_weight_lbs=129,
        modifiers=RacialModifiers(
            # Guide: "slight dodge bonus"        → APPROX: +2
            dodge_bonus=2,
            # Guide: "bonus to attack rate"      → APPROX: +2
            attack_rate_bonus=2,
            # Guide: "slight HP penalty"         → APPROX: -6 (least HP in game)
            hp_bonus=-6,
            # Guide: "bonus when using dual weapons"
            dual_weapon_bonus=True,     # APPROX: +1 attack action when both hands armed
            preferred_weapons=[
                "Dagger", "Short Sword", "Scimitar", "Scythe", "Flail",
                "Javelin", "Stiletto", "Epee",
            ],
            favored_opponents="Light and medium opponents — small, fast weapons struggle vs heavy armor.",
            disfavored_opponents="Large, powerful opponents who can't be taken out with small weapons.",
        ),
    ),

    # =========================================================================
    "Goblin": Race(
        name="Goblin",
        is_playable=True,
        description=(
            "Small, vicious, opportunistic scavengers and dirty fighters. Fast and tricky "
            "with thrown weapons, but physically weak and struggle badly with heavy arms."
        ),
        base_height_in=42,    # 3'6" male SIZE-12 midpoint
        base_weight_lbs=48,
        modifiers=RacialModifiers(
            # Guide: "frantic and quick — highest action economy among small races"
            attack_rate_bonus=3,      # +3 APM bonus
            initiative_bonus=3,       # Strike first often
            dodge_bonus=2,            # Slippery and small
            damage_penalty=-3,        # Tiny frames = weak hits
            hp_bonus=-5,              # Extremely fragile
            strength_penalty=-2,      # Physically weak
            # Special Goblin abilities
            thrown_mastery=True,      # +2 bonus to Opportunity Throw
            scavenger=True,           # Notice dropped weapons
            heavy_weapon_penalty=True,# Severe penalty for heavy/two-handed
            preferred_weapons=[
                "Dagger", "Short Sword", "Hatchet", "Javelin", "Stiletto",
                "Bladed Flail", "Net",
            ],
            weak_weapons=[
                "Great Axe", "Battle Axe", "Great Sword", "Halberd",
                "Maul", "Great Pick", "Battle Flail",
            ],
            favored_opponents="Small-to-medium opponents; isolated warriors.",
            disfavored_opponents="Large, heavily-armored tanks who can ignore their tricks.",
        ),
    ),

    # =========================================================================
    "Gnome": Race(
        name="Gnome",
        is_playable=True,
        description=(
            "Small, surprisingly tough and crafty inventors. Gnomes are hardy for their size, "
            "learn quickly, and excel at turning an opponent's aggression against them through "
            "clever counterstrikes and ripostes."
        ),
        base_height_in=47,    # 3'11" male SIZE-12 midpoint
        base_weight_lbs=65,
        modifiers=RacialModifiers(
            # Guide: "remarkably durable for their small stature — tough little bastards"
            hp_bonus=7,               # +7 HP — solid constitution
            # Guide: "learn quickly" → ~18% faster training
            trains_stats_faster=True, # Similar to Human but slightly weaker
            dodge_bonus=1,            # Small and crafty
            parry_bonus=2,            # Naturally good at deflecting blows
            damage_penalty=-2,        # Hit lighter than bigger races
            attack_rate_penalty=-1,   # Careful, measured fighting
            # Special Gnome abilities
            counterstrike_bonus=True, # Exceptional at ripostes and counter-attacks
            tactician_edge=True,      # Better vs aggressive, weaker vs methodical
            preferred_weapons=[
                "Short Sword", "Long Sword", "Epee", "Bastard Sword",
                "Hammer", "Mace", "Morningstar", "War Hammer",
            ],
            weak_weapons=[
                "Great Axe", "Halberd", "Pole Axe", "Pike", "Lance",
            ],
            favored_opponents="Overly aggressive warriors (Total Kill, Bash, Wall of Steel, Berserker).",
            disfavored_opponents="Methodical, patient fighters (Sure Strike, Calculated Attack, Parry/Defend).",
        ),
    ),

    # =========================================================================
    "Lizardfolk": Race(
        name="Lizardfolk",
        is_playable=True,
        description=(
            "Savage reptilian predators. Tough, relentless fighters who rely on natural claws, "
            "powerful tail strikes, and kicks. Best Martial Combat users in the game."
        ),
        base_height_in=72,    # 6'0" male SIZE-12 midpoint
        base_weight_lbs=220,
        modifiers=RacialModifiers(
            # Guide: "tough, relentless"
            hp_bonus=9,               # Excellent durable brawler
            # Guide: "natural claws, tail, kicks" — Martial Combat strength
            natural_weapons_bonus=3,  # +3 damage to MC/brawl-style attacks
            dodge_bonus=1,            # Predatory grace
            attack_rate_penalty=-2,   # Cold-blooded — slower to accelerate
            # Special Lizardfolk abilities
            natural_armor_scales=True, # Natural armor (Scale equivalent, no penalty)
            armor_layering_allowed=True, # Can layer armor with special rules
            preferred_weapons=[
                "Open Hand", "Dagger", "Short Sword", "Stiletto",
                "Hammer", "Morning Star", "Flail",
            ],
            weak_weapons=[],
            favored_opponents="All — Lizardfolk are well-rounded brawlers.",
            disfavored_opponents="None in particular — they adapt well.",
        ),
    ),

    # =========================================================================
    "Tabaxi": Race(
        name="Tabaxi",
        is_playable=True,
        description=(
            "Lightning-quick, acrobatic feline warriors. Tabaxi are masters of speed, evasion, "
            "and fluid movement. They dart in and out of combat with daring acrobatics, but are "
            "fragile and tire quickly."
        ),
        base_height_in=63,    # 5'3" male SIZE-12 midpoint (tall for their build)
        base_weight_lbs=135,
        modifiers=RacialModifiers(
            # Guide: "best pure evasion in the game"
            dodge_bonus=4,            # Hardest to hit cleanly
            initiative_bonus=3,       # Frequently strike first
            # Guide: "enter a short Frenzy for +3 APM for 3-4 actions (once per fight)"
            # (handled specially in combat code)
            hp_bonus=-6,              # Light, agile build — cannot take punishment
            attack_rate_penalty=-1,   # Slightly baseline slower (before bursts)
            strength_penalty=-2,      # Not built for raw power
            endurance_penalty=-3,     # Tire faster in prolonged fights
            # Special Tabaxi abilities
            acrobatic_advantage=True, # Resist knockdowns, acrobatic maneuvers
            frenzy_burst=True,        # Once per fight: +3 APM for 3-4 actions
            preferred_weapons=[
                "Dagger", "Short Sword", "Epee", "Scimitar", "Hatchet",
                "Javelin", "Stiletto", "Quarterstaff",
            ],
            weak_weapons=[
                "Great Axe", "Great Sword", "Maul", "Halberd", "Battle Flail",
            ],
            favored_opponents="Slow, heavily-armored opponents they can dart around.",
            disfavored_opponents="Tanks with high damage output who can catch them.",
        ),
    ),

    # =========================================================================
    # NPC RACES — Not player-selectable
    # =========================================================================

    "Monster": Race(
        name="Monster",
        is_playable=False,
        description=(
            "Hideous creatures controlled by the game. Fighting a Monster is "
            "essentially a death sentence. Less than a dozen warriors in Pit history "
            "have survived — those few were absorbed into the Monster team."
        ),
        base_height_in=90,    # Enormous — can reach 9'+ at max SIZE
        base_weight_lbs=405,
        modifiers=RacialModifiers(
            # Monsters are intentionally overpowered — these are large fixed bonuses.
            hp_bonus=50,
            damage_bonus=10,
            attack_rate_bonus=5,
            parry_bonus=3,
            dodge_bonus=3,
        ),
    ),

    "Peasant": Race(
        name="Peasant",
        is_playable=False,
        description=(
            "Arena fillers. Peasants are scaled dynamically to the warrior they face "
            "by the matchmaking system. Named individuals: Klud the Bell-Ringer, "
            "Sally Strumpet, Peter the Poet, Fiona Fishwife, Beggar Barleycorn, "
            "Stu the Gravedigger, Gypsy Jezebel, Perceval the Prophet, "
            "Madman Muttermuck, Roger the Shrubber. Never truly eliminated."
        ),
        base_height_in=67,    # Human proportions
        base_weight_lbs=165,
        modifiers=RacialModifiers(),  # All zeros — Peasants are scaled in matchmaking
    ),
}


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def get_race(name: str) -> Race:
    """
    Retrieve a Race by name (case-insensitive).
    Raises ValueError if the name is not found.
    """
    for key, race in RACES.items():
        if key.lower() == name.lower():
            return race
    valid = ", ".join(RACES.keys())
    raise ValueError(f"Unknown race: '{name}'. Valid options: {valid}")


def list_playable_races() -> List[str]:
    """Return names of all player-selectable races."""
    return [name for name, race in RACES.items() if race.is_playable]


def list_all_races() -> List[str]:
    """Return names of all races including NPC races."""
    return list(RACES.keys())