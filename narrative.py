# =============================================================================
# narrative.py — Blood Pit Narrative Text Engine
# =============================================================================
# Generates all fight text: the side-by-side header, blow-by-blow lines,
# perm injury announcements, surrender/mercy text, crowd flavor, and the
# post-fight training summary.
#
# Design: templates for structure, pools for flavor.
# Each pool has 10-15 variants so fights feel different but recognizable.
# =============================================================================

import random
from typing import Optional
from warrior import Warrior, compare_stats

LINE_WIDTH = 76   # Total width of fight output


# ---------------------------------------------------------------------------
# POPULARITY DESCRIPTIONS
# ---------------------------------------------------------------------------

POPULARITY_DESCRIPTIONS = [
    (0,  10, "WIDELY REVILED"),
    (11, 20, "BOOED REGULARLY"),
    (21, 30, "GENERALLY DISLIKED"),
    (31, 40, "MOSTLY IGNORED"),
    (41, 50, "KNOWN TO THE CROWD"),
    (51, 60, "POPULAR WITH THE KIDS"),
    (61, 70, "WELL LIKED"),
    (71, 80, "A FAN FAVORITE"),
    (81, 90, "HAS HORDES OF ADORING FANS"),
    (91, 100, "A LEGENDARY HERO OF THE PIT"),
]


def popularity_desc(score: int) -> str:
    for lo, hi, desc in POPULARITY_DESCRIPTIONS:
        if lo <= score <= hi:
            return desc
    return "KNOWN TO THE CROWD"


# ---------------------------------------------------------------------------
# FIGHT HEADER
# ---------------------------------------------------------------------------

def _center_col(text: str, width: int) -> str:
    return text.center(width)


def _right_col(text: str, width: int) -> str:
    return text.rjust(width)


def _left_col(text: str, width: int) -> str:
    return text.ljust(width)


def build_fight_header(
    warrior_a : Warrior,
    warrior_b : Warrior,
    team_a_name   : str,
    team_b_name   : str,
    manager_a_name: str,
    manager_b_name: str,
    pos_a: int = 1,   # Position on team (1-5)
    pos_b: int = 1,
) -> str:
    """
    Generate the side-by-side fight header exactly like the sample in the guide.
    Left column = warrior A (home), right column = warrior B (away).
    Middle column = field labels.
    """
    COL = 22    # Width of each side column
    MID = 14    # Width of middle label column

    def row(left: str, label: str, right: str) -> str:
        l = left.upper().rjust(COL)
        m = label.upper().center(MID)
        r = right.upper().ljust(COL)
        return l + m + r

    h_ft_a, h_in_a = warrior_a.height_in // 12, warrior_a.height_in % 12
    h_ft_b, h_in_b = warrior_b.height_in // 12, warrior_b.height_in % 12

    pop_a = f"{warrior_a.popularity}-{popularity_desc(warrior_a.popularity)}"
    pop_b = f"{warrior_b.popularity}-{popularity_desc(warrior_b.popularity)}"

    lines = [
        " " * LINE_WIDTH,
        row(f"{warrior_a.name} ({pos_a})", "WARRIOR NAME", f"{warrior_b.name} ({pos_b})"),
        row(warrior_a.record_str, "RECORD", warrior_b.record_str),
        row(f"{team_a_name}", "TEAM NAME", f"{team_b_name}"),
        row(f"{manager_a_name}", "MANAGER NAME", f"{manager_b_name}"),
        row(
            f"{warrior_a.race.name} {warrior_a.gender}",
            "GENDER/RACE",
            f"{warrior_b.race.name} {warrior_b.gender}",
        ),
        " " * LINE_WIDTH,
    ]

    # Stat comparison rows
    stat_pairs = [
        ("strength", "dexterity", "constitution", "intelligence", "size"),
    ]
    for attr in ("strength", "dexterity", "constitution", "intelligence", "size"):
        val_a = warrior_a.get_attr(attr)
        val_b = warrior_b.get_attr(attr)
        arrow = compare_stats(val_a, val_b)
        desc_a = warrior_a.stat_desc(attr)
        desc_b = warrior_b.stat_desc(attr)
        lines.append(row(desc_a, arrow, desc_b))

    lines.append(" " * LINE_WIDTH)

    # Popularity, height, weight
    lines.append(row(pop_a, "POPULARITY", pop_b))
    lines.append(row(str(warrior_a.height_in), "HEIGHT (IN)", str(warrior_b.height_in)))
    lines.append(row(str(warrior_a.weight_lbs), "WEIGHT (LBS)", str(warrior_b.weight_lbs)))

    lines.append(" " * LINE_WIDTH)

    # Gear
    lines.append(row(warrior_a.armor or "NONE",           "ARMOR",       warrior_b.armor or "NONE"))
    lines.append(row(warrior_a.helm or "NONE",            "HELM",        warrior_b.helm or "NONE"))
    lines.append(row(warrior_a.primary_weapon,            "MAIN WEAPON", warrior_b.primary_weapon))
    lines.append(row(warrior_a.secondary_weapon,          "OFF WEAPON",  warrior_b.secondary_weapon))
    lines.append(row(warrior_a.backup_weapon or "NONE",   "SPARE WEAPON",warrior_b.backup_weapon or "NONE"))

    lines.append(" " * LINE_WIDTH)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# FIGHT OPENER LINES (first line of minute 1)
# ---------------------------------------------------------------------------

FIGHT_OPENERS = [
    "Dark clouds bode ill for the battle",
    "The crowd roars its bloodthirsty approval",
    "A hush falls over the arena",
    "The smell of blood and sawdust fills the air",
    "Thunder rumbles ominously in the distance",
    "The afternoon sun beats down on the bloodstained sand",
    "The crowd jeers as the combatants approach each other",
    "An eerie silence settles over the Blood Pit",
    "The torches flicker as a cold wind sweeps through the arena",
    "The Blood Master raises his fist — the fight begins!",
]


# ---------------------------------------------------------------------------
# STRATEGY SWITCH LINE
# ---------------------------------------------------------------------------

def strategy_switch_line(warrior_name: str, strat_idx: int) -> str:
    return f" * {warrior_name.upper()} switches to strategy {strat_idx}"


# ---------------------------------------------------------------------------
# STYLE INTENT LINES
# Appear before an attack (roughly 40% of the time).
# Template: "{name} {intent_phrase} with {pronoun} {weapon}"
# ---------------------------------------------------------------------------

STYLE_INTENT_POOLS: dict[str, list[str]] = {
    "Total Kill": [
        "{name} rampages onward, {weapon} starved for bloodshed",
        "{name} charges forward in a wild frenzy",
        "{name} drives suddenly forward, {weapon} whistling through the air",
        "{name} attacks in a berserker rage",
        "{name} hurls {himself} forward with reckless abandon",
    ],
    "Wall of Steel": [
        "{name} relentlessly presses forward with {his} {weapon}",
        "{name} creates a whirling wall of steel",
        "{name} attacks in a flurry of blows",
        "{name} hammers away with machine-like persistence",
    ],
    "Lunge": [
        "{name} darts forward, looking for an opening",
        "{name} probes for a weakness in {foe}'s defense",
        "{name} moves with quick, precise footwork",
        "{name} circles {foe}, waiting for the perfect moment",
    ],
    "Bash": [
        "{name} winds up for a crushing blow",
        "{name} drives forward with brute force",
        "{name} attempts to batter through {foe}'s defenses",
    ],
    "Slash": [
        "{name} draws back for a sweeping slash",
        "{name} lines up for a powerful drawing cut",
        "{name} seeks to open a telling wound",
    ],
    "Strike": [
        "{name} tries to hit the mighty {foe}",
        "{name} sizes up {foe} carefully",
        "{name} directs an attack toward {foe}",
        "{name} steps threateningly close to the {adj} {foe}",
    ],
    "Engage & Withdraw": [
        "{name} probes and retreats, looking for an opening",
        "{name} feints left and prepares to strike",
        "{name} dances away from {foe}'s reach",
    ],
    "Counterstrike": [
        "{name} waits patiently for {foe} to make a mistake",
        "{name} holds ground, watching {foe} like a hawk",
        "{name} anxiously awaits {foe}'s next move",
    ],
    "Decoy": [
        "{name} engages {foe}'s weapon with {his} off-hand",
        "{name} feints to draw {foe}'s attention",
        "{name} draws {foe} into an elaborate trap",
    ],
    "Sure Strike": [
        "{name} waits for absolutely the right moment",
        "{name} carefully prepares a deliberate strike",
        "{name} takes aim at {foe} with methodical precision",
    ],
    "Calculated Attack": [
        "{name} ruthlessly seeks wreckage with {his} {weapon}",
        "{name} calculates the perfect attack angle",
        "{name} studies {foe}'s armor for weak points",
    ],
    "Opportunity Throw": [
        "{name} hefts {his} {weapon} for a throw",
        "{name} lines up a ranged attack",
    ],
    "Martial Combat": [
        "{name} drops into a fighting crouch",
        "{name} circles {foe} with fluid martial grace",
        "{name} prepares to unleash a flurry of strikes",
    ],
    "Parry": [
        "{name} raises {his} {weapon} defensively",
        "{name} holds ground, focused entirely on defense",
    ],
    "Defend": [
        "{name} keeps {his} guard high",
        "{name} circles warily, waiting for an opening",
    ],
}

# Adjectives used in strike intent lines (matching the guide "stable", "mighty", etc.)
WARRIOR_ADJ_POOL = [
    "formidable", "powerful", "mighty", "relentless", "fierce",
    "dangerous", "capable", "tenacious", "stalwart", "fearsome",
]


def style_intent_line(
    warrior_name : str,
    foe_name     : str,
    style        : str,
    weapon_name  : str,
    gender       : str,
) -> Optional[str]:
    """
    Return a style intent line (or None, ~60% skip chance).
    """
    if random.random() < 0.55:
        return None

    pool = STYLE_INTENT_POOLS.get(style, STYLE_INTENT_POOLS["Strike"])
    template = random.choice(pool)
    pronoun  = "his" if gender == "Male" else "her"
    reflexive= "himself" if gender == "Male" else "herself"
    adj      = random.choice(WARRIOR_ADJ_POOL)

    line = template.format(
        name    = warrior_name.upper(),
        foe     = foe_name.upper(),
        weapon  = weapon_name.lower(),
        his     = pronoun,
        himself = reflexive,
        adj     = adj,
    )
    return line


# ---------------------------------------------------------------------------
# ATTACK LINES
# Format: "{attacker} tries to {verb} {defender}'s {location}"
# ---------------------------------------------------------------------------

# Aim-point display names
AIM_POINT_LABELS = {
    "Head"          : ["head", "skull", "helm", "throat", "face"],
    "Chest"         : ["chest", "rib cage", "torso", "sternum", "breast"],
    "Abdomen"       : ["abdomen", "midsection", "gut", "belly", "flank"],
    "Primary Arm"   : ["weapon arm", "primary arm", "sword arm"],
    "Secondary Arm" : ["shield arm", "secondary arm", "off arm", "left forearm"],
    "Primary Leg"   : ["primary leg", "lead leg", "front leg", "main leg"],
    "Secondary Leg" : ["trailing leg", "rear leg", "secondary leg"],
    "None"          : ["body", "midsection", "torso"],   # generic when no aim point
}

# Attack verbs by weapon category
ATTACK_VERBS: dict[str, list[str]] = {
    "Sword/Knife"  : ["slash", "cut", "hack", "slice", "drive a blow toward", "thrust at"],
    "Axe/Pick"     : ["chop at", "hack at", "cleave at", "swing at"],
    "Hammer/Mace"  : ["bash", "smash at", "bludgeon", "hammer at", "pound"],
    "Polearm/Spear": ["thrust at", "drive a blow toward", "jab at", "lunge at"],
    "Flail"        : ["lash out at", "whip at", "flail at", "swing at"],
    "Stave"        : ["strike at", "thrust at", "jab at", "swing at"],
    "Shield"       : ["bash", "slam into", "smash at"],
    "Oddball"      : ["strike at", "attack", "swing at", "lash out at"],
}

# Extra style-flavored attack verbs
STYLE_ATTACK_PREFIX: dict[str, list[str]] = {
    "Total Kill"       : ["tries to demolish", "savagely attacks", "hacks away at",
                          "makes an explosive assault on"],
    "Bash"             : ["tries to bash", "pounds at", "hammers"],
    "Slash"            : ["tries to slash", "draws a cut at", "rakes at"],
    "Lunge"            : ["lunges at", "makes a quick thrust at", "darts in and attacks"],
    "Calculated Attack": ["executes a downward strike at", "makes a precise attack on",
                          "targets the exposed", "aims a calculated blow at"],
    "Sure Strike"      : ["carefully aims at", "takes a measured swing at"],
    "Counterstrike"    : ["strikes quickly with", "counters with a blow at",
                          "retaliates against"],
    "Wall of Steel"    : ["attacks relentlessly at", "relentlessly targets"],
}


def attack_line(
    attacker_name : str,
    defender_name : str,
    weapon_name   : str,
    weapon_category: str,
    style         : str,
    aim_point     : str,
) -> str:
    """Generate the attack declaration line."""
    # Choose aim location string
    loc_pool = AIM_POINT_LABELS.get(aim_point, AIM_POINT_LABELS["None"])
    location = random.choice(loc_pool)

    # Choose verb — style-flavored first, then category default
    if style in STYLE_ATTACK_PREFIX and random.random() < 0.5:
        verb = random.choice(STYLE_ATTACK_PREFIX[style])
        return (
            f"{attacker_name.upper()} {verb} {defender_name.upper()}'s "
            f"{location} with {his_her_its(weapon_name)}"
        )
    else:
        cat_verbs = ATTACK_VERBS.get(weapon_category, ATTACK_VERBS["Oddball"])
        verb = random.choice(cat_verbs)
        return (
            f"{attacker_name.upper()} {verb} "
            f"{defender_name.upper()}'s {location}"
        )


def his_her_its(weapon_name: str) -> str:
    """Return 'his {weapon}' placeholder — used in attack line variants."""
    return f"{weapon_name.lower()}"


# ---------------------------------------------------------------------------
# HIT VERB LINES (weapon makes contact)
# Format: "{attacker}'s {weapon} {hit_verb} {defender}'s {hit_location}!"
# ---------------------------------------------------------------------------

HIT_VERBS: dict[str, list[str]] = {
    "Sword/Knife"  : ["bites into", "slices into", "cuts into", "finds"],
    "Axe/Pick"     : ["bites into", "chops into", "cleaves into", "punches into"],
    "Hammer/Mace"  : ["crashes into", "slams into", "smashes into", "crunches into"],
    "Polearm/Spear": ["drives into", "punches into", "thrusts into", "buries itself in"],
    "Flail"        : ["lashes into", "wraps around and cracks into", "crashes into",
                      "whips into"],
    "Stave"        : ["cracks into", "strikes", "slams into"],
    "Shield"       : ["slams into", "crashes into", "bashes into"],
    "Oddball"      : ["punches into", "cracks into", "finds", "hits"],
}

HIT_TARGETS = {
    "Head"    : ["headgear", "helm", "skull", "head", "temple"],
    "Chest"   : ["chest armor", "ribs", "breastplate", "torso", "chest"],
    "Abdomen" : ["midsection", "gut", "belly armor", "flank"],
    "Primary Arm"  : ["weapon arm", "sword arm", "armor on the arm"],
    "Secondary Arm": ["shield arm", "off arm", "forearm armor"],
    "Primary Leg"  : ["primary leg", "lead leg", "thigh"],
    "Secondary Leg": ["rear leg", "trailing leg"],
    "None"    : ["armor", "body", "torso"],
}

HIT_ANNOUNCEMENTS = [
    "{attacker}'s accuracy is rewarded!",
    "{attacker} finds the opening!",
    "The blow connects!",
    "{attacker} gets past {defender}'s guard!",
    "{attacker} barely gets past {defender}'s defenses!",
    "The {weapon} finds its mark!",
]


def hit_line(
    attacker_name : str,
    defender_name : str,
    weapon_name   : str,
    weapon_category: str,
    aim_point     : str,
    hit_precision : str = "normal",  # "precise", "normal", "barely"
) -> list[str]:
    """
    Return 1-2 lines describing a successful hit.
    hit_precision affects whether an announcement line precedes the hit.
    """
    lines = []

    # Announce the hit if it was a precise or barely-made blow
    if hit_precision == "precise" or random.random() < 0.25:
        ann = random.choice(HIT_ANNOUNCEMENTS).format(
            attacker=attacker_name.upper(),
            defender=defender_name.upper(),
            weapon  =weapon_name.lower(),
        )
        lines.append(ann)

    # The actual hit
    verb_pool = HIT_VERBS.get(weapon_category, HIT_VERBS["Oddball"])
    verb = random.choice(verb_pool)
    target_pool = HIT_TARGETS.get(aim_point, HIT_TARGETS["None"])
    target = random.choice(target_pool)
    lines.append(
        f"{attacker_name.upper()}'s {weapon_name.lower()} "
        f"{verb} {defender_name.upper()}'s {target}!"
    )
    return lines


# ---------------------------------------------------------------------------
# DAMAGE DESCRIPTION LINES
# ---------------------------------------------------------------------------

DAMAGE_LINES: dict[str, list[str]] = {
    "scratch": [
        "   Barely a scratch!",
        "   The blow glances harmlessly off!",
        "   Little damage results from the strike",
        "   The armor does its job admirably",
        "   The blow does almost nothing",
    ],
    "light": [
        "   A minor hit!",
        "   Some damage is done",
        "   A glancing blow!",
        "   The blow lands without full force",
        "   The armor absorbs most of it",
    ],
    "solid": [
        "   A solid blow has been struck!",
        "   The resulting crunch echoes through the Blood Pit!",
        "   A telling hit!",
        "   The blow has real authority behind it!",
        "   That one will leave a mark!",
    ],
    "heavy": [
        "   The blow lands with bone-breaking force!",
        "   A devastating strike!",
        "   That one hurt badly!",
        "   The crowd winces at the sound of that blow!",
        "   A powerful hit draws screams from the crowd!",
    ],
    "severe": [
        "   The wound delivers terrible agony!",
        "   Great gobs of gore gush from the gash!",
        "   The strike lands with flesh-splattering fury!",
        "   Blood sprays through the air!",
        "   An absolutely monstrous blow!",
    ],
}


def damage_line(damage: int, max_hp: int) -> str:
    """Return a damage description line based on damage as a fraction of max HP."""
    pct = damage / max(1, max_hp)
    if   pct < 0.05: tier = "scratch"
    elif pct < 0.12: tier = "light"
    elif pct < 0.22: tier = "solid"
    elif pct < 0.35: tier = "heavy"
    else:            tier = "severe"
    return random.choice(DAMAGE_LINES[tier])


# ---------------------------------------------------------------------------
# MISS LINES
# ---------------------------------------------------------------------------

MISS_LINES = [
    "{attacker} misses wildly",
    "{attacker}'s {weapon} cuts only air",
    "{attacker} fails to connect",
    "{attacker} swings and misses badly",
    "{attacker}'s attack goes wide",
    "{attacker} whiffs completely",
    "{attacker}'s aim is off — the blow finds nothing",
]


def miss_line(attacker_name: str, weapon_name: str) -> str:
    template = random.choice(MISS_LINES)
    return template.format(
        attacker=attacker_name.upper(),
        weapon  =weapon_name.lower(),
    )


# ---------------------------------------------------------------------------
# PARRY LINES
# ---------------------------------------------------------------------------

PARRY_LINES_SUCCESS = [
    "{defender} is ready for the strike, and deftly parries it!",
    "{defender} makes an extraordinary effort, and parries the strike!",
    "{defender}'s defenses are particularly strong!",
    "{defender} turns the blow aside with skill!",
    "{defender} catches the weapon and deflects it cleanly!",
    "{defender}'s guard holds firm!",
    "{defender} has a plan: don't get hit!",
]

PARRY_LINES_BARELY = [
    "{defender} barely gets the parry off!",
    "{defender} makes a desperate last-moment parry!",
    "{defender} just manages to deflect the blow!",
]

DEFENSE_POINT_LINES = [
    "{defender} is paying special attention to not being hit there!",
    "{defender}'s plan is not to get hit!",
    "{defender} has that area well covered!",
]


def parry_line(defender_name: str, barely: bool = False, defense_point_active: bool = False) -> str:
    if defense_point_active and random.random() < 0.5:
        return random.choice(DEFENSE_POINT_LINES).format(defender=defender_name.upper())
    if barely:
        return random.choice(PARRY_LINES_BARELY).format(defender=defender_name.upper())
    return random.choice(PARRY_LINES_SUCCESS).format(defender=defender_name.upper())


# ---------------------------------------------------------------------------
# DODGE LINES
# ---------------------------------------------------------------------------

DODGE_LINES = [
    "{defender} sidesteps the attack nimbly!",
    "{defender} twists out of the way!",
    "{defender} cartwheels away from the strike!",
    "{defender} ducks under the blow!",
    "{defender} moves just enough to avoid the hit!",
    "{defender} is not where the weapon expects!",
]


def dodge_line(defender_name: str) -> str:
    return random.choice(DODGE_LINES).format(defender=defender_name.upper())


# ---------------------------------------------------------------------------
# COUNTERSTRIKE LINE (special attack after a successful parry)
# ---------------------------------------------------------------------------

COUNTERSTRIKE_LINES = [
    "{attacker} seizes the opening and launches a counter-attack!",
    "{attacker} turns the parry into an immediate counter!",
    "{attacker}'s counter-strike catches {foe} completely off-guard!",
    "{attacker} makes {foe} pay for the reckless attack!",
]


def counterstrike_line(attacker_name: str, foe_name: str) -> str:
    return random.choice(COUNTERSTRIKE_LINES).format(
        attacker=attacker_name.upper(), foe=foe_name.upper()
    )


# ---------------------------------------------------------------------------
# GROUND / KNOCKDOWN LINES
# ---------------------------------------------------------------------------

KNOCKDOWN_LINES = [
    "{warrior} plummets downward with great speed!!",
    "{warrior} goes crashing to the ground!",
    "{warrior} is knocked off {his} feet!",
    "{warrior} stumbles and falls heavily!",
    "{warrior} crashes to the arena floor!",
]

GET_UP_LINES = [
    "{warrior} scrambles back to {his} feet",
    "{warrior} gets up, shaken but ready",
    "{warrior} staggers upright",
    "{warrior} rises from the dust, spitting blood",
]


def knockdown_line(warrior_name: str, gender: str) -> str:
    pronoun = "his" if gender == "Male" else "her"
    template = random.choice(KNOCKDOWN_LINES)
    return template.format(warrior=warrior_name.upper(), his=pronoun)


def getup_line(warrior_name: str, gender: str) -> str:
    pronoun = "his" if gender == "Male" else "her"
    template = random.choice(GET_UP_LINES)
    return template.format(warrior=warrior_name.upper(), his=pronoun)


# ---------------------------------------------------------------------------
# PERMANENT INJURY LINES
# ---------------------------------------------------------------------------

PERM_ANNOUNCEMENTS: dict[str, list[str]] = {
    "head"         : ["{w} has been permanently injured in the head!!!",
                      "{w}'s skull takes a terrible wound!!!"],
    "chest"        : ["{w} has been permanently injured in the chest!!!",
                      "{w}'s chest is grievously wounded!!!"],
    "abdomen"      : ["{w} has been permanently injured in the abdomen!!!",
                      "{w} takes a gut wound that won't heal!!!"],
    "primary_arm"  : ["{w} has been permanently injured in the weapon arm!!!",
                      "{w}'s sword arm is badly damaged!!!"],
    "secondary_arm": ["{w} has been permanently injured in the shield arm!!!"],
    "primary_leg"  : ["{w} has been permanently injured in the primary leg!!!",
                      "{w}'s main leg is shattered!!!"],
    "secondary_leg": ["{w} has been permanently injured in the secondary leg!!!"],
}

PERM_BLEEDING_LINES: dict[str, list[str]] = {
    "head"         : ["{w}'s head is bleeding badly!",     "{w}'s skull wound weeps blood!"],
    "chest"        : ["{w}'s chest wound bleeds freely!",  "{w} clutches at {his} chest!"],
    "abdomen"      : ["{w}'s belly wound is seeping!",     "{w} doubles over in pain!"],
    "primary_arm"  : ["{w}'s weapon arm is bleeding!",     "{w}'s arm trembles with pain!"],
    "secondary_arm": ["{w}'s off-arm bleeds steadily!"],
    "primary_leg"  : ["{w}'s main leg is bleeding!",       "{w}'s leg buckles!"],
    "secondary_leg": ["{w}'s leg is bleeding!"],
}

PERM_PAIN_LINES: dict[str, list[str]] = {
    "head"         : [
        "{w}'s vision swims from the head wound!!",
        "{w} staggers, seeing double from the blow to {his} head!!",
    ],
    "chest"        : [
        "{w} gasps for air, ribs grinding painfully!!",
        "{w}'s breathing becomes labored!!",
    ],
    "abdomen"      : [
        "{w} bends double, clutching {his} ruined gut!!",
        "{w} spits blood from the gut wound!!",
    ],
    "primary_arm"  : [
        "{w}'s weapon arm spasms in agony!!",
        "{w} nearly drops {his} weapon from the pain!!",
    ],
    "secondary_arm": [
        "{w}'s shield arm goes partially numb!!",
    ],
    "primary_leg"  : [
        "{w}'s leg spasms in pain, causing {him} to roll around in the dirt, wracked with extreme pain!!",
        "{w}'s leg gives way completely!!",
    ],
    "secondary_leg": [
        "{w}'s rear leg buckles violently!!",
    ],
}


def perm_injury_lines(warrior_name: str, location: str, level: int, gender: str) -> list[str]:
    """Return 3 lines for a permanent injury event."""
    pronoun  = "his"  if gender == "Male" else "her"
    him_her  = "him"  if gender == "Male" else "her"

    def fmt(pool: dict, key: str) -> str:
        return random.choice(pool.get(key, [f"{warrior_name.upper()} is gravely wounded!!!"])).format(
            w=warrior_name.upper(), his=pronoun, him=him_her
        )

    lines = [
        fmt(PERM_ANNOUNCEMENTS,  location),
        fmt(PERM_BLEEDING_LINES, location),
        fmt(PERM_PAIN_LINES,     location),
    ]
    return lines


# ---------------------------------------------------------------------------
# FATIGUE / ENDURANCE LINES
# ---------------------------------------------------------------------------

FATIGUE_LINES = [
    "{warrior}'s desire to win may not be enough",
    "{warrior} is visibly tiring",
    "{warrior} slows noticeably",
    "{warrior}'s movements are heavy with exhaustion",
]

VERY_TIRED_LINES = [
    "{warrior} is fighting with pure will power!",
    "{warrior} staggers forward on empty reserves!",
    "{warrior} can barely lift {his} weapon!",
    "{warrior} is running on fumes!",
]

ENDURANCE_DRAIN_LINES = [
    "{warrior} drains the fight out of {foe}",
    "{warrior}'s patient style wears on {foe}",
    "{warrior}'s relentless pressure tires {foe}",
]


def fatigue_line(warrior_name: str, gender: str, very_tired: bool = False) -> str:
    pronoun = "his" if gender == "Male" else "her"
    pool = VERY_TIRED_LINES if very_tired else FATIGUE_LINES
    return random.choice(pool).format(warrior=warrior_name.upper(), his=pronoun)


# ---------------------------------------------------------------------------
# SURRENDER / MERCY LINES
# ---------------------------------------------------------------------------

APPEAL_LINES = [
    "{warrior} appeals to the Blood Master for mercy!",
    "{warrior} raises a hand in surrender!",
    "{warrior} calls out for quarter!",
    "{warrior} can fight no more and begs for mercy!",
]

MERCY_GRANTED = [
    "The ref saves the pitiable {warrior}!",
    "The Blood Master shows mercy — {warrior} lives to fight another day!",
    "{warrior} is spared by the grace of the Blood Master!",
    "The crowd screams for blood, but the ref steps in!",
    "Mercy is granted — the fight is over!",
]

MERCY_DENIED = [
    "The Blood Master shows no mercy today!",
    "The crowd screams for blood — mercy is denied!",
    "{warrior} must fight on, or die trying!",
    "No quarter is given!",
]

DEATH_LINES = [
    "{warrior} has perished in the Blood Pit!!!",
    "{warrior} breathes {his} last on the arena floor!!!",
    "The {warrior} is dead. The crowd erupts!!!",
    "{warrior} falls, never to rise again!!!",
]

VICTORY_LINES = [
    "{winner} has won this affair of honor!",
    "{winner} stands victorious over the fallen {loser}!",
    "{winner} is declared the winner!",
    "The Blood Master raises {winner}'s arm in victory!",
    "{winner} roars in triumph over the defeated {loser}!",
]


def appeal_line(warrior_name: str) -> str:
    return random.choice(APPEAL_LINES).format(warrior=warrior_name.upper())


def mercy_result_line(warrior_name: str, granted: bool) -> str:
    pool = MERCY_GRANTED if granted else MERCY_DENIED
    return random.choice(pool).format(warrior=warrior_name.upper())


def death_line(warrior_name: str, gender: str) -> str:
    pronoun = "his" if gender == "Male" else "her"
    return random.choice(DEATH_LINES).format(warrior=warrior_name.upper(), his=pronoun)


def victory_line(winner_name: str, loser_name: str) -> str:
    return random.choice(VICTORY_LINES).format(
        winner=winner_name.upper(), loser=loser_name.upper()
    )


# ---------------------------------------------------------------------------
# CROWD FLAVOR LINES (random interjections between actions)
# These fire roughly once every 4-6 actions.
# ---------------------------------------------------------------------------

CROWD_LINES = [
    "The drummer loses control and tosses a drumstick away",
    "Arena guards hold back rioting fans!",
    "A spectator calls out, 'Give him what he deserves!'",
    "The crowd chants for blood!",
    "Someone in the upper rows throws a piece of bread",
    "A vendor drops his tray with a tremendous crash",
    "The crowd surges forward against the barriers!",
    "Whistles and jeers rain down from the stands!",
    "A dog runs loose in the upper tier!",
    "The pit bell rings early — it must be a mistake",
    "Three drunks in the cheap seats start a brawl",
    "The announcer's voice cracks with excitement",
    "A nobleman covers his eyes — then peeks through his fingers",
    "Children in the stands look away, then look back",
    "The smell of blood whips the crowd into a frenzy",
    "Half the crowd rises to their feet in anticipation!",
    "Money changes hands rapidly in the betting stands",
    "The torchbearers scramble to keep up with the action",
]

RACE_TAUNTS = {
    "Half-Orc" : [
        "A spectator calls out, 'Hey half-orc!  Grind me a pound!'",
        "Someone yells, 'Get a bath, you monster!'",
        "A child throws a cabbage at the Half-Orc",
    ],
    "Halfling" : [
        "A guard has to move to see around the Halfling",
        "The crowd strains to see the small warrior",
        "Someone yells, 'Watch out — there's a rat loose in the pit!'",
    ],
    "Dwarf"    : [
        "A drunk yells, 'Which one is the Dwarf?' — looking at the right one",
        "Someone throws coins at the Dwarf — a tradition, apparently",
    ],
    "Elf"      : [
        "The Elf fans in the crowd begin an unsettling melodic chant",
        "Someone boos the Elf, then sits very still hoping no one noticed",
    ],
}


def crowd_line(warrior_a_race: str = "", warrior_b_race: str = "") -> str:
    """Return a random crowd flavor line, occasionally race-specific."""
    if random.random() < 0.2:
        # Try a race taunt for one of the warriors
        race = random.choice([warrior_a_race, warrior_b_race])
        if race in RACE_TAUNTS:
            return random.choice(RACE_TAUNTS[race])
    return random.choice(CROWD_LINES)


# ---------------------------------------------------------------------------
# "ANXIOUSLY AWAITS" LINE (endurance drain effect, certain styles)
# ---------------------------------------------------------------------------

ANXIOUS_LINES = [
    "{warrior} circles {foe}, draining the will to fight",
    "{warrior} waits patiently — {foe}'s energy bleeds away",
    "{warrior} keeps pressure on {foe} without committing",
]


def anxious_line(warrior_name: str, foe_name: str) -> Optional[str]:
    """Only fires for styles with anxiously_awaits=True, ~20% chance."""
    if random.random() < 0.20:
        t = random.choice(ANXIOUS_LINES)
        return t.format(warrior=warrior_name.upper(), foe=foe_name.upper())
    return None


# ---------------------------------------------------------------------------
# POST-FIGHT TRAINING SUMMARY
# ---------------------------------------------------------------------------

def training_summary(warrior_name: str, results: list[str]) -> str:
    """Generate the post-fight training line shown at the end of the fight report."""
    if not results:
        return f"{warrior_name.upper()} did not train this turn"
    # Result strings look like: "War Flail trained: Level 0 → Level 1 (Novice)"
    # Extract just the skill name (everything before " trained:" or " trained")
    skills = []
    for r in results:
        # Strip the " trained: ..." suffix to get just the skill name
        name = r.split(" trained")[0].strip().lower()
        skills.append(name)
    return f"{warrior_name.upper()} has trained in {' and '.join(skills)}"
