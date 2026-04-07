# =============================================================================
# narrative.py — BLOODSPIRE Narrative Text Engine
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


def _warrior_report_block(w: Warrior) -> list:
    """
    Return prose description lines for one warrior: height, weight,
    popularity, armor, helm, and weapons. No strategy table.
    """
    h_ft = w.height_in // 12
    h_in = w.height_in % 12
    pronoun = "his" if w.gender == "Male" else "her"

    lines = []
    lines.append(f"{w.name.upper()} is {h_ft}'{h_in}\"")
    lines.append(f"{w.name.upper()} weighs {w.weight_lbs} lbs.")
    lines.append(f"{w.name.upper()} {popularity_desc(w.popularity).title()}.")

    armor_part = f"in {w.armor.upper()}" if w.armor else "unarmored"
    helm_part  = f"and will wear a {w.helm.upper()}" if w.helm else "and wears no helm"
    lines.append(f"{w.name.upper()} enters the arena {armor_part} {helm_part}.")

    main = w.primary_weapon.upper() if w.primary_weapon else "OPEN HAND"
    off  = w.secondary_weapon.upper() if w.secondary_weapon else None
    bak  = w.backup_weapon.upper() if w.backup_weapon else None

    if off and off.upper() != "OPEN HAND":
        lines.append(f"{w.name.upper()} fights using a {main} with an off-hand {off}.")
    else:
        lines.append(f"{w.name.upper()} fights using a {main}.")

    if bak and bak.upper() != "OPEN HAND":
        lines.append(f"{w.name.upper()} has a spare {bak} strapped to {pronoun} side.")

    return lines


def _strategy_table(w: Warrior) -> list:
    """Return the strategy table lines for the player warrior."""
    if not w.strategies:
        return []
    hdr = f"{'TRIGGER':<32}{'FIGHTING STYLE':<20}{'LEVEL':>5}  {'AIMING POINT':<16}{'DEFENSE POINT'}"
    sep = "-" * len(hdr)
    lines = ["", hdr, sep]
    for i, s in enumerate(w.strategies, 1):
        is_default = (not s.trigger) or s.trigger.lower() == "always"
        trig = "D: Always" if is_default else f"{i}: {s.trigger}"
        aim  = s.aim_point    if s.aim_point    else "None"
        dfe  = s.defense_point if s.defense_point else "None"
        sty  = s.style        if s.style        else "None"
        lines.append(f"{trig:<32}{sty:<20}{s.activity:>5}  {aim:<16}{dfe}")
    return lines


def build_fight_header(
    warrior_a : Warrior,
    warrior_b : Warrior,
    team_a_name   : str,
    team_b_name   : str,
    manager_a_name: str,
    manager_b_name: str,
    pos_a: int = 1,
    pos_b: int = 1,
) -> str:
    """
    Generate the fight header in report/narrative style.
    Layout:
      - Matchup / team / race header
      - Warrior A (player) prose block
      - Warrior B (opponent) prose block
      - Warrior A strategy table only (opponent strategies are hidden)
    """
    SEP = "=" * LINE_WIDTH

    lines = [SEP]

    # Matchup title
    left  = f"{warrior_a.name.upper()} ({warrior_a.record_str})"
    right = f"{warrior_b.name.upper()} ({warrior_b.record_str})"
    lines.append(f"{left}   vs   {right}")
    lines.append(f"{team_a_name.upper()} ({manager_a_name.upper()})"
                 + "   vs   " +
                 f"{team_b_name.upper()} ({manager_b_name.upper()})")
    lines.append(f"{warrior_a.race.name} {warrior_a.gender}"
                 + "   vs   " +
                 f"{warrior_b.race.name} {warrior_b.gender}")
    lines.append(SEP)
    lines.append("")

    # Player warrior prose
    lines.extend(_warrior_report_block(warrior_a))
    lines.append("")

    # Opponent warrior prose
    lines.extend(_warrior_report_block(warrior_b))
    lines.append("")

    # Player strategy table only
    lines.extend(_strategy_table(warrior_a))

    lines.append("")
    lines.append(SEP)
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
    "An eerie silence settles over the BLOODSPIRE",
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
    if random.random() < 0.30:
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

# Attack verbs by weapon category — third-person singular, complete phrases
ATTACK_VERBS: dict[str, list[str]] = {
    "Sword/Knife"  : ["slashes at", "cuts at", "hacks at", "slices at",
                      "drives a blow toward", "thrusts at"],
    "Axe/Pick"     : ["chops at", "hacks at", "cleaves at", "swings at"],
    "Hammer/Mace"  : ["bashes at", "smashes at", "bludgeons", "hammers at", "pounds at"],
    "Polearm/Spear": ["thrusts at", "drives a blow toward", "jabs at", "lunges at"],
    "Flail"        : ["lashes out at", "whips at", "flails at", "swings at"],
    "Stave"        : ["strikes at", "thrusts at", "jabs at", "swings at"],
    "Shield"       : ["bashes at", "slams into", "smashes at"],
    "Oddball"      : ["strikes at", "swings at", "lashes out at"],
}

# Lizardfolk-specific attack verbs when using Open Hand/Martial Combat
# Features claw rakes, tail sweeps, and powerful kicks
LIZARDFOLK_ATTACK_VERBS: dict[str, list[str]] = {
    "claw"  : ["rakes at", "slashes at with claws", "tears at", "rends at with razor claws"],
    "kick"  : ["kicks at", "stomps toward", "drives a powerful kick at", "lashes out with a kick toward"],
    "tail"  : ["sweeps at with tail", "lashes at with tail", "swings tail at", "brings tail around toward"],
}

# Extra style-flavored attack verbs — third-person singular
STYLE_ATTACK_PREFIX: dict[str, list[str]] = {
    "Total Kill"       : ["tries to demolish", "savagely attacks", "hacks away at",
                          "makes an explosive assault on"],
    "Bash"             : ["tries to bash", "pounds at", "hammers away at"],
    "Slash"            : ["tries to slash", "draws a cut at", "rakes at"],
    "Lunge"            : ["lunges at", "makes a quick thrust at", "darts in at"],
    "Calculated Attack": ["executes a downward strike at", "makes a precise attack on",
                          "aims a calculated blow at"],
    "Sure Strike"      : ["carefully aims at", "takes a measured swing at"],
    "Counterstrike"    : ["counters with a blow at", "retaliates against",
                          "fires back at"],
    "Wall of Steel"    : ["attacks relentlessly at", "relentlessly targets"],
}


def attack_line(
    attacker_name  : str,
    defender_name  : str,
    weapon_name    : str,
    weapon_category: str,
    style          : str,
    aim_point      : str,
    attacker_gender: str = "Male",
    attacker_race  : str = None,      # For Lizardfolk special handling
) -> str:
    """Generate the attack declaration line. Lizardfolk with Open Hand get special claw/tail/kick verbs."""
    loc_pool = AIM_POINT_LABELS.get(aim_point, AIM_POINT_LABELS["None"])
    location = random.choice(loc_pool)
    pronoun  = "his" if attacker_gender == "Male" else "her"

    # Lizardfolk with Open Hand use special descriptors
    if attacker_race == "Lizardfolk" and weapon_name == "Open Hand":
        attack_types = ["claw", "kick", "tail"]
        attack_type = random.choice(attack_types)
        
        verb_pool = LIZARDFOLK_ATTACK_VERBS.get(attack_type, LIZARDFOLK_ATTACK_VERBS["claw"])
        verb = random.choice(verb_pool)
        
        # Return without weapon mention since it's natural weapons
        return (
            f"{attacker_name.upper()} {verb} {defender_name.upper()}'s {location}!"
        )

    # Style-flavored variant — always ends with weapon reference
    if style in STYLE_ATTACK_PREFIX and random.random() < 0.5:
        verb = random.choice(STYLE_ATTACK_PREFIX[style])
        return (
            f"{attacker_name.upper()} {verb} {defender_name.upper()}'s "
            f"{location} with {pronoun} {weapon_name.lower()}"
        )
    else:
        # Category verb variant — weapon mentioned at the end
        cat_verbs = ATTACK_VERBS.get(weapon_category, ATTACK_VERBS["Oddball"])
        verb = random.choice(cat_verbs)
        return (
            f"{attacker_name.upper()} {verb} "
            f"{defender_name.upper()}'s {location} with {pronoun} {weapon_name.lower()}"
        )


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

# Lizardfolk-specific hit verbs when using claws, tail, or feet in martial combat
LIZARDFOLK_HIT_VERBS: dict[str, list[str]] = {
    "claw"  : ["rakes across", "shreds", "tears into", "slashes across", "rends"],
    "kick"  : ["crashes into", "smashes into", "crushes into", "drives into"],
    "tail"  : ["whips across", "lashes into", "sweeps across", "crashes into"],
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
    attacker_race : str = None,       # For Lizardfolk special handling
) -> list[str]:
    """
    Return 1-2 lines describing a successful hit.
    hit_precision affects whether an announcement line precedes the hit.
    If attacker is Lizardfolk using Open Hand, use claw/tail/kick descriptions.
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

    # Lizardfolk with Open Hand use special claw/tail/kick descriptions
    if attacker_race == "Lizardfolk" and weapon_name == "Open Hand":
        attack_types = ["claw", "kick", "tail"]
        attack_type = random.choice(attack_types)

        verb_pool = LIZARDFOLK_HIT_VERBS.get(attack_type, LIZARDFOLK_HIT_VERBS["claw"])
        verb = random.choice(verb_pool)
        target_pool = HIT_TARGETS.get(aim_point, HIT_TARGETS["None"])
        target = random.choice(target_pool)

        # Create attack type descriptor
        attack_desc = {
            "claw": "claws",
            "kick": "powerful kick",
            "tail": "lashing tail",
        }.get(attack_type, "claws")
        
        lines.append(
            f"{attacker_name.upper()}'s {attack_desc} "
            f"{verb} {defender_name.upper()}'s {target}!"
        )
    else:
        # Standard weapon-based hit description
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

DAMAGE_LINES: dict[str, dict[str, list[str]]] = {
    "Slashing": {
        "Heavy": [
            "   The blade carves a horrific canyon through flesh and muscle!",
            "   A terrible slash opens wide, spilling blood in sheets!",
            "   The edge shears through meat with savage force!",
            "   A gruesome flap of skin and muscle is laid open!",
            "   The strike slices deep, nearly severing the limb!",
            "   Blood erupts as the blade cuts a vital channel!",
            "   The slash leaves a ragged, gaping wound!",
            "   Flesh parts violently beneath the keen edge!",
            "   A horrific cut is torn across the warrior's torso!",
            "   The blade bites deep and opens the body!",
            "   A savage slash nearly takes the warrior's arm!",
            "   The strike opens a long, ghastly wound!",
            "   Blood sprays wildly from the deep slash!",
            "   The edge cleaves through muscle and sinew!",
            "   A brutal cut lays the warrior's side open!",
        ],
        "Medium": [
            "   The blade opens a deep, bleeding gash!",
            "   A clean slash draws a heavy flow of blood!",
            "   The weapon cuts a painful channel through flesh!",
            "   A long, weeping laceration is left behind!",
            "   The strike slices through skin and muscle!",
            "   Blood runs freely from the fresh cut!",
            "   The blade leaves a wide, angry wound!",
            "   A solid slash opens across the warrior's body!",
            "   The edge bites deep and draws crimson!",
            "   A painful cut is carved into the target!",
        ],
        "Light": [
            "   The blade merely kisses the skin!",
            "   A shallow cut appears along the surface!",
            "   The weapon skims across and draws a thin line!",
            "   Only a superficial slash is left behind!",
            "   The strike glances off, leaving a minor score!",
            "   A light cut wells up with a few drops of blood!",
            "   The edge scrapes across the skin!",
            "   A thin red line marks where the blade passed!",
            "   The slash is more sting than true damage!",
            "   Blood beads along a shallow graze!",
        ],
    },
    "Piercing": {
        "Heavy": [
            "   The point drives deep into the body with brutal force!",
            "   The weapon punches through flesh and out the other side!",
            "   A horrific puncture wound is torn through the warrior!",
            "   The strike impales the target with savage power!",
            "   The point sinks in and finds something vital!",
            "   A gaping hole is left where the weapon withdrew!",
            "   The thrust punches straight through armor and meat!",
            "   The warrior is skewered by the powerful strike!",
            "   Blood gushes from the deep puncture!",
            "   The point drives in with bone-cracking force!",
        ],
        "Medium": [
            "   The point sinks deep and draws a heavy flow!",
            "   A clean puncture wound is left behind!",
            "   The weapon drives in and comes out red!",
            "   Blood wells up from the deep stab!",
            "   The thrust punches through muscle and out again!",
            "   A painful hole is torn into the warrior's body!",
            "   The point finds meat and draws freely!",
            "   A solid stab opens a bleeding channel!",
            "   Blood flows steadily from the puncture!",
            "   The weapon sinks in and leaves a deep wound!",
        ],
        "Light": [
            "   The point merely pricks the skin!",
            "   A shallow puncture appears!",
            "   The weapon skims in and draws a thin bead of blood!",
            "   Only a minor stab wound is left behind!",
            "   The thrust glances off, leaving a small hole!",
            "   A light prick wells up with a few drops!",
            "   The point barely breaks the surface!",
            "   A superficial stab mark appears!",
            "   The weapon nicks the flesh and withdraws!",
            "   Blood beads from a shallow puncture!",
        ],
    },
    "Bludgeoning": {
        "Heavy": [
            "   The blow lands with bone-shattering force!",
            "   A sickening crunch echoes as bone breaks!",
            "   The strike caves in flesh and crushes what lies beneath!",
            "   The impact rattles the warrior's entire skeleton!",
            "   A devastating smash pulps muscle and bone!",
            "   The hit lands like a falling anvil!",
            "   Bone gives way with a horrible crack!",
            "   The warrior is smashed backward by the brutal force!",
            "   The blow turns the target area into a bloody ruin!",
            "   A crushing impact echoes across the arena!",
        ],
        "Medium": [
            "   The strike lands with heavy, punishing force!",
            "   A solid crunch is heard as the blow connects!",
            "   The hit drives the air from the warrior's lungs!",
            "   The weapon smashes into flesh with satisfying weight!",
            "   A painful bruise forms beneath the skin!",
            "   The blow rocks the warrior back on their heels!",
            "   The strike connects with meaty impact!",
            "   A heavy thud echoes as the weapon lands!",
            "   The hit leaves a deep, angry bruise!",
            "   The warrior staggers from the solid impact!",
        ],
        "Light": [
            "   The blow lands lightly, more sting than damage!",
            "   A dull thud is all that results!",
            "   The strike barely connects with force!",
            "   The hit is more jarring than damaging!",
            "   The weapon smacks against the body with little effect!",
            "   A light impact rocks the warrior slightly!",
            "   The blow stings but does little real harm!",
            "   The strike connects with minimal force!",
            "   A weak smack is all the warrior feels!",
            "   The hit lands with little more than a slap!",
        ],
    },
    "Cleaving": {
        "Heavy": [
            "   The strike cleaves through bone and muscle with terrifying force!",
            "   The blow splits the warrior wide open in a horrific wound!",
            "   The attack hacks deep into flesh, nearly severing the limb!",
            "   The weapon tears a gruesome channel through the body!",
            "   The strike cleaves violently through meat and bone!",
            "   A devastating chop lays the warrior's side open!",
            "   The blow cuts through the target with savage power!",
            "   The strike splits flesh and bone in a single brutal motion!",
            "   The weapon cleaves a massive, gaping wound!",
            "   The attack hacks through the warrior with bone-splitting force!",
            "   A horrific cleave nearly takes the limb!",
            "   The blow tears a ragged canyon through the body!",
            "   The strike cleaves with unstoppable momentum!",
            "   The weapon splits the warrior open with brutal efficiency!",
            "   A terrible cleaving wound is torn into the target!",
        ],
        "Medium": [
            "   The strike cleaves a deep, bleeding wound!",
            "   The blow hacks into flesh with solid force!",
            "   The attack cuts a wide, painful channel!",
            "   The weapon cleaves through muscle and draws heavy blood!",
            "   A powerful chop opens a long, weeping gash!",
            "   The strike cleaves deeply into the warrior!",
            "   The blow hacks a painful wound into the body!",
            "   The attack cleaves through skin and meat!",
            "   The weapon cuts a deep, angry furrow!",
            "   The strike cleaves with punishing weight!",
        ],
        "Light": [
            "   The strike merely grazes with a cleaving edge!",
            "   The blow skims across and leaves a shallow chop!",
            "   The attack nicks the warrior lightly!",
            "   The weapon glances off in a minor cleave!",
            "   A light chop scrapes across the surface!",
            "   The strike barely breaks the skin with its edge!",
            "   The blow lands as little more than a cleaving nick!",
            "   The attack skims across and draws a thin line!",
            "   The weapon kisses the flesh with a shallow chop!",
            "   The strike leaves only a superficial cleave!",
        ],
    },
    "Generic": {
        "Heavy": [
            "   The strike lands with devastating force!",
            "   A horrific wound is torn open by the blow!",
            "   The attack hits with bone-crushing power!",
            "   Blood erupts violently from the impact!",
            "   The blow caves in flesh and crushes what lies beneath!",
            "   A terrible wound is left in the wake of the strike!",
            "   The hit lands with savage, punishing force!",
            "   Blood sprays wildly as the blow connects!",
            "   The strike nearly folds the warrior in half!",
            "   A gruesome wound is carved into the body!",
        ],
        "Medium": [
            "   The strike lands with solid, painful force!",
            "   A deep wound is opened by the blow!",
            "   The attack connects heavily and draws blood!",
            "   The hit rocks the warrior back on their heels!",
            "   A painful wound is left in the wake of the strike!",
            "   Blood flows steadily from the fresh injury!",
            "   The blow lands with satisfying weight!",
            "   The strike opens a bleeding channel!",
            "   The attack hits hard enough to stagger!",
            "   A solid wound is carved into the warrior!",
        ],
        "Light": [
            "   The strike barely breaks the skin!",
            "   The blow glances off and draws a thin line!",
            "   The attack skims across the surface!",
            "   Only a superficial wound is left behind!",
            "   The hit stings more than it harms!",
            "   Blood beads up along a minor graze!",
            "   The strike lands lightly and is shrugged off!",
            "   A shallow cut appears on the skin!",
            "   The blow merely kisses the flesh!",
            "   The attack draws only a few drops of blood!",
        ],
    },
}

# Map weapon categories to damage types
_WEAPON_DAMAGE_TYPE: dict[str, str] = {
    "Sword/Knife":    "Slashing",
    "Axe/Pick":       "Cleaving",
    "Hammer/Mace":    "Bludgeoning",
    "Polearm/Spear":  "Piercing",
    "Flail":          "Bludgeoning",
    "Shield":         "Bludgeoning",
    "Oddball":        "Generic",
}


def damage_line(damage: int, max_hp: int, weapon_category: str = "Oddball") -> str:
    """Return a damage description line based on damage severity and weapon type."""
    pct = damage / max(1, max_hp)
    if   pct < 0.12: severity = "Light"
    elif pct < 0.30: severity = "Medium"
    else:            severity = "Heavy"

    dmg_type = _WEAPON_DAMAGE_TYPE.get(weapon_category, "Generic")
    pool = DAMAGE_LINES[dmg_type][severity]
    return random.choice(pool)


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
# DEFENSE INTENT LINES (defender's reaction shown before result is known)
# ---------------------------------------------------------------------------

DEFENSE_INTENT_PARRY = [
    "{defender} braces to meet the attack!",
    "{defender} raises {his} guard against the incoming blow!",
    "{defender} is ready for {his} opponent's move!",
    "{defender} eyes the incoming strike carefully!",
    "{defender} sets {his} feet and prepares to deflect!",
    "{defender} shifts weight, preparing to parry!",
    "{defender} tightens {his} grip and watches for the opening!",
    "{defender} reads the attack and reacts!",
    "{defender} commits to a solid defense!",
    "{defender} is eagerly defending!",
]

DEFENSE_INTENT_DODGE = [
    "{defender} is already moving!",
    "{defender} looks to slip the blow!",
    "{defender} watches for the angle of attack!",
    "{defender} plans to avoid being where the weapon lands!",
    "{defender} shifts {his} weight to dodge!",
    "{defender} keeps {his} feet light and ready!",
    "{defender}'s footwork is anticipating trouble!",
    "{defender} stays mobile, looking for the escape!",
    "{defender} isn't planning to stand still for this!",
    "{defender}'s plan is not to get hit!",
]


def defense_intent_line(defender_name: str, gender: str, uses_parry: bool) -> str:
    pronoun = "his" if gender == "Male" else "her"
    pool = DEFENSE_INTENT_PARRY if uses_parry else DEFENSE_INTENT_DODGE
    return random.choice(pool).format(defender=defender_name.upper(), his=pronoun)


# ---------------------------------------------------------------------------
# LOW HP STATUS COMMENTARY
# ---------------------------------------------------------------------------

_LOW_HP_TIER1 = [   # 30–50% HP remaining
    "{warrior} is showing signs of the punishment received!",
    "{warrior} is taking this fight on the chin!",
    "The damage is starting to add up for {warrior}!",
    "{warrior} is breathing harder now!",
    "{warrior} looks like {he} could use a moment to collect {himself}!",
]

_LOW_HP_TIER2 = [   # 15–30% HP remaining
    "{warrior} is in serious trouble!",
    "{warrior} is covered in blood — and not all of it is the opponent's!",
    "The crowd senses {warrior} is running out of options!",
    "{warrior} is surviving on determination alone at this point!",
    "{warrior} is desperately wounded and still fighting!",
    "{warrior} looks deathly pale!",
]

_LOW_HP_TIER3 = [   # below 15% HP remaining
    "{warrior} would make a corpse envious!",
    "{warrior} is drenched in blood!",
    "{warrior} is barely standing — sheer will is all that remains!",
    "The end is near for {warrior}!",
    "{warrior} staggers but somehow refuses to fall!",
    "{warrior} is one solid hit away from the Dark Arena!",
]


def low_hp_line(warrior_name: str, gender: str, hp_pct: float) -> Optional[str]:
    """Return a low-HP status line, or None if HP is above threshold / random skip."""
    pronoun  = "he" if gender == "Male" else "she"
    reflexive = "himself" if gender == "Male" else "herself"
    if hp_pct >= 0.50:
        return None
    if hp_pct >= 0.30:
        if random.random() > 0.30:   # fire ~30% of the time in this range
            return None
        pool = _LOW_HP_TIER1
    elif hp_pct >= 0.15:
        if random.random() > 0.50:
            return None
        pool = _LOW_HP_TIER2
    else:
        if random.random() > 0.70:
            return None
        pool = _LOW_HP_TIER3
    return random.choice(pool).format(
        warrior=warrior_name.upper(), he=pronoun, himself=reflexive
    )


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

    announcement = fmt(PERM_ANNOUNCEMENTS, location)
    lines = [
        f"*** {announcement} ***",   # bold-style marker for perm injury
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
    "{warrior} has perished in the BLOODSPIRE!!!",
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


# ---------------------------------------------------------------------------
# MINUTE STATUS LINE  (who is winning at each minute boundary)
# ---------------------------------------------------------------------------

_ADVAN_EVEN = [
    "Both warriors appear evenly matched, with neither willing to give ground.",
    "The fight remains dead even, neither combatant claiming a clear edge.",
    "At this point, the contest could still go either way.",
    "Neither warrior has managed to separate themselves from the other.",
    "The crowd watches closely as the fight remains finely balanced.",
    "So far, there is little to distinguish the two in this tightly contested battle.",
    "The momentum swings back and forth, with no clear leader emerging.",
    "Both gladiators continue to test each other, still searching for an opening.",
    "Despite several close calls, neither warrior has seized control.",
    "The margin between victory and defeat remains razor-thin.",
]

_ADVAN_EVEN_CONT = [   # used when tier unchanged from last minute
    "The fight remains stubbornly even, with neither warrior conceding ground.",
    "Nothing has changed — both combatants continue on level footing.",
    "The balance holds; neither fighter has found the breakthrough they need.",
]

_ADVAN_SLIGHT = [
    "{winner} appears to have a slight advantage.",
    "{winner} is beginning to edge ahead in the exchange.",
    "{winner} has started to gain the upper hand, though the fight remains close.",
    "Momentum seems to be slowly shifting toward {winner}.",
    "{winner} looks marginally sharper at this stage of the fight.",
    "While still competitive, {winner} seems just a step ahead.",
    "{winner} is finding more success, but the outcome is far from decided.",
    "The balance tips ever so slightly in favor of {winner}.",
    "It's a narrow lead, but {winner} may be starting to pull ahead.",
    "Small advantages are beginning to stack up for {winner}.",
]

_ADVAN_SLIGHT_CONT = [
    "{winner} continues to hold a narrow advantage.",
    "The slight edge remains with {winner}, though little has changed.",
    "{winner} maintains the lead, but nothing is decided yet.",
]

_ADVAN_CLEAR = [
    "{winner} is winning the fight.",
    "At this point, {winner} has seized control of the contest.",
    "{winner} now holds a clear advantage over their opponent.",
    "The fight has begun to tilt decisively in {winner}'s favor.",
    "{winner} is firmly in control of the action.",
    "It's becoming evident that {winner} has the upper hand.",
    "{winner} is dictating the pace and flow of the fight.",
    "The tide has clearly turned in favor of {winner}.",
    "The crowd responds as {winner} takes command of the fight.",
    "The advantage is unmistakable now, and it belongs to {winner}.",
]

_ADVAN_CLEAR_CONT = [
    "{winner} remains in control, pressing their advantage.",
    "The situation is unchanged — {winner} continues to dictate the fight.",
    "{winner} holds firm command of the contest.",
]

_ADVAN_DOMINATING = [
    "{winner} is dominating the fight.",
    "This has become a one-sided affair in favor of {winner}.",
    "{winner} is completely overwhelming their opponent.",
    "The gap between the two warriors is widening rapidly.",
    "{winner} is imposing their will with authority.",
    "This fight is slipping badly away from {loser}.",
    "{winner} is in full command, leaving little room for resistance.",
    "The contest has turned brutal, with {winner} firmly on top.",
    "Only a dramatic reversal could save {loser} now.",
    "{winner} is dismantling their opponent piece by piece.",
]

_ADVAN_DOMINATING_CONT = [
    "{winner} shows no sign of relenting — the onslaught continues.",
    "{loser} remains unable to slow {winner}'s dominance.",
    "{winner} stays firmly in control with no answer from {loser}.",
]

_ADVAN_BRINK = [
    "{loser} appears to be on the verge of defeat.",
    "This fight looks moments away from being decided.",
    "{winner} smells blood and presses the advantage.",
    "It's hard to see how {loser} survives much longer at this pace.",
    "Unless something changes quickly, this fight is all but over.",
    "{loser} is hanging on by sheer will alone.",
    "The end may be near as {winner} continues their assault.",
]

_ADVAN_BRINK_EXHAUSTION = [
    "{loser} is running on empty — their body is beginning to betray them.",
    "The effort has taken a severe toll on {loser}; they can barely keep pace.",
    "{loser} is visibly fading, their endurance all but spent.",
    "Exhaustion is closing in on {loser}, and {winner} senses the opening.",
    "{loser}'s legs are heavy, their arms slower — they cannot keep this up much longer.",
]

_ADVAN_SWING_TO = [
    "The fight has taken a surprising turn, with {winner} now pressing the advantage.",
    "After earlier struggles, {winner} has clawed their way back into control.",
    "A shift in momentum — {winner} has suddenly taken charge.",
    "The tide turns: {winner} seizes the upper hand after a close exchange.",
]


def minute_status_line(
    winner_name: str,
    loser_name: str,
    tier: str,
    prev_tier: str,
    prev_winner: str,
    used: set,
) -> str:
    """
    Return a fight-status line for the start of a minute.

    tier / prev_tier: one of "even", "slight", "clear", "dominating", "brink", "brink_exhaustion"
    winner_name / loser_name: the leading fighter (empty strings when tier == "even")
    prev_winner: the name of the winner last minute (empty string if none)
    used: mutable set of already-used lines this fight (updated in-place)
    """
    # Detect momentum swing: tier changed OR same tier but winner flipped
    swung = (tier != "even" and prev_tier != "even" and
             tier == prev_tier and prev_winner and prev_winner != winner_name)

    if swung:
        pool = _ADVAN_SWING_TO
    elif tier == prev_tier:
        # Unchanged — use softer continuation lines
        cont_map = {
            "even":            _ADVAN_EVEN_CONT,
            "slight":          _ADVAN_SLIGHT_CONT,
            "clear":           _ADVAN_CLEAR_CONT,
            "dominating":      _ADVAN_DOMINATING_CONT,
            "brink":           _ADVAN_BRINK,
            "brink_exhaustion": _ADVAN_BRINK_EXHAUSTION,
        }
        pool = cont_map.get(tier, _ADVAN_EVEN_CONT)
    else:
        main_map = {
            "even":            _ADVAN_EVEN,
            "slight":          _ADVAN_SLIGHT,
            "clear":           _ADVAN_CLEAR,
            "dominating":      _ADVAN_DOMINATING,
            "brink":           _ADVAN_BRINK,
            "brink_exhaustion": _ADVAN_BRINK_EXHAUSTION,
        }
        pool = main_map.get(tier, _ADVAN_EVEN)

    # Pick a line not used yet this fight; fall back to full pool if exhausted
    available = [l for l in pool if l not in used]
    if not available:
        available = list(pool)

    line = random.choice(available)
    used.add(line)

    return line.format(winner=winner_name.upper(), loser=loser_name.upper())


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


INTIMIDATE_LINES = [
    "{warrior}'s relentless assault is beginning to rattle {foe}!",
    "{foe} flinches under the ferocity of {warrior}'s onslaught!",
    "The sheer savagery of {warrior}'s assault wears on {foe}'s nerves!",
    "{warrior} presses forward with terrifying aggression — {foe} backs away!",
    "The crowd roars as {warrior}'s ferocity visibly shakes {foe}!",
    "{foe} struggles to keep composure under {warrior}'s relentless pressure!",
    "{warrior}'s wild fury is taking a psychological toll on {foe}!",
]


def intimidate_line(warrior_name: str, foe_name: str) -> Optional[str]:
    """Only fires for styles with intimidate=True at high activity, ~25% chance."""
    if random.random() < 0.25:
        t = random.choice(INTIMIDATE_LINES)
        return t.format(warrior=warrior_name.upper(), foe=foe_name.upper())
    return None


# ---------------------------------------------------------------------------
# POST-FIGHT TRAINING SUMMARY
# ---------------------------------------------------------------------------

_BASE_STATS = {"strength", "dexterity", "constitution", "intelligence", "presence", "size"}


def training_summary(warrior_name: str, results: list[str], is_opponent: bool = False) -> str:
    """
    Post-fight training summary.
      successes:  "<n> has trained in X and Y"
      none:       "<n> has trained in nothing"
      observed 4th train: appended as separate line

    is_opponent: When True, hide the specific skill/stat names — show "Skill" or
    "Stat" instead.  The one exception is the observed/learned bonus, which always
    names the actual skill (that is the whole point of the intelligence report).
    """
    if not results:
        return f"{warrior_name.upper()} has trained in nothing"

    trained  = []
    observed = []
    for r in results:
        if r.startswith("[OBSERVED]") and "trained:" in r:
            skill_name = r.split("[OBSERVED]")[1].split(" trained:")[0].strip().title()
            observed.append(skill_name)
        elif "trained:" in r:
            skill_name = r.split(" trained:")[0].strip()
            if is_opponent:
                trained.append("Stat" if skill_name.lower() in _BASE_STATS else "Skill")
            else:
                trained.append(skill_name.title())

    lines = []
    if trained:
        lines.append(f"{warrior_name.upper()} has trained in {' and '.join(trained)}")
    else:
        lines.append(f"{warrior_name.upper()} has trained in nothing")

    if observed:
        # Always reveal the actual skill — this is the scouting intelligence payoff
        for obs_skill in observed:
            lines.append(
                f"{warrior_name.upper()} observed and learned a {obs_skill} skill"
                f" from their opponent"
            )

    return "\n".join(lines)

