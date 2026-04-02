# =============================================================================
# ai_league_teams.py — AI Manager Teams for League Play
# =============================================================================
import random, json, os
from typing import List, Optional

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
AI_TEAMS_FILE  = os.path.join(BASE_DIR, "saves", "league", "ai_teams.json")

# ---------------------------------------------------------------------------
# NAMED AI MANAGERS
# ---------------------------------------------------------------------------

AI_MANAGER_ROSTER = [
    # (manager_name, team_name, style, races, tier)
    ("Garrett Ironwill",   "The Iron Vanguard",    "balanced",   ["Human","Half-Orc"],      2),
    ("Madame Vexx",        "Vexx's Vicious",       "aggressive", ["Elf","Half-Elf"],         2),
    ("Big Rufus Craw",     "Craw's Crushers",      "berserker",  ["Half-Orc","Human"],       1),
    ("Sister Thornwall",   "The Thornwall Guard",  "defensive",  ["Dwarf","Human"],          3),
    ("Loquat the Wise",    "The Learned Fists",    "tactician",  ["Elf","Half-Elf","Human"], 3),
    ("Drago Splitskull",   "Splitskull Syndicate", "berserker",  ["Half-Orc","Human"],       1),
    ("Penny Briarwood",    "Briarwood Brawlers",   "balanced",   ["Halfling","Human"],       2),
    ("Count Aldren Voss",  "House Voss",           "tactician",  ["Human","Half-Elf"],       3),
    ("Wulfric the Grim",   "Grim's Reapers",       "aggressive", ["Human","Dwarf"],          2),
    ("Zara Quickblade",    "The Quickblades",      "aggressive", ["Elf","Halfling"],         2),
    ("Magistra Corvina",   "Corvina's Chosen",     "defensive",  ["Human","Dwarf"],          3),
    ("The Unnamed One",    "Shadows of the Pit",   "berserker",  ["Half-Orc","Elf"],         1),
    ("Snegg Ironbolts",    "The Sneaky Daggers",   "aggressive", ["Goblin","Halfling"],      2),
    ("Gnomester Tick",     "Ticktock's Tinkers",   "tactician",  ["Gnome","Human"],          3),
    ("K'rathis the Scaled", "The Scaled Predators", "balanced",   ["Lizardfolk","Human"],     2),
    ("Shadowpouncer Vale",  "Velvet Claws",        "aggressive", ["Tabaxi","Elf"],           2),
]

# ---------------------------------------------------------------------------
# WARRIOR NAME TABLES  — deep fantasy names by race and gender
# ---------------------------------------------------------------------------

_NAMES = {
    "Human": {
        "Male": [
            "Aldric","Brennan","Caelan","Dorian","Evander","Faolan","Garrett",
            "Hadrian","Idris","Jareth","Kaedric","Leoric","Malachar","Navar",
            "Orlan","Pendrath","Quillan","Rowan","Saoirse","Tybalt","Ulric",
            "Valorian","Wendell","Xavian","Yosef","Zarek","Aedan","Broderick",
            "Cormac","Dristan","Edwyn","Fenwick","Godric","Harwick","Ivar",
            "Joran","Kelric","Lorcan","Morden","Nereth","Osric","Peregrin",
            "Ragnar","Soren","Torben","Uther","Varian","Walric","Yorick","Zander",
            "Aldwin","Bram","Corvin","Daven","Eldric","Falric","Gareth",
        ],
        "Female": [
            "Aelwen","Brenna","Caelith","Dagna","Elara","Fionnuala","Gwendis",
            "Hessa","Isolde","Jocasta","Kaira","Lyonesse","Maelys","Nerissa",
            "Orlaith","Petra","Ravenna","Sabine","Thalassa","Ursula","Valeria",
            "Winifred","Xena","Ylva","Zara","Aeryn","Brigid","Calista","Deirdre",
            "Erevan","Fiamma","Gisela","Heloise","Imogen","Jessamine","Kestrel",
            "Liriel","Morrigan","Nessa","Ondine","Phaedra","Rosalind","Saoirse",
            "Thessaly","Undine","Viviane","Wynne","Yseult","Zenobia","Ardith",
            "Berwyn","Callindra","Dara","Elspeth","Faye","Glenna","Hawthorn",
        ],
    },
    "Elf": {
        "Male": [
            "Aeltharion","Caladwen","Daerith","Elarindë","Faendrel","Galadorn",
            "Halamar","Ilúvatar","Jaecaril","Kaeledrin","Lirathar","Maethoron",
            "Naerdúr","Orivandor","Paendriel","Raeventhar","Saelindor","Thalindorn",
            "Úravîn","Vaelthoron","Weladris","Xaelindor","Yarandir","Zaevîn",
            "Aerindel","Caelindorn","Darathorn","Elarindir","Faenvelindor","Galadril",
            "Halavorn","Ilindor","Jaelorin","Kaelindorn","Lúthindor","Maelindorn",
            "Naethoron","Orivindor","Pelindorn","Raevindor","Saelindorn","Thalindor",
            "Úravorn","Vaelindor","Welindorn","Xaelindorn","Yarandorn","Zaevindor",
        ],
        "Female": [
            "Aelindra","Caelithra","Daraveth","Erithiel","Faenarath","Galadriela",
            "Halawyn","Ilyandra","Jaelithra","Kaelindra","Liraveth","Maelindra",
            "Naerithiel","Orivaelith","Paenara","Raelindra","Saelithra","Thalindra",
            "Úraveth","Vaelindra","Welithra","Xaelindra","Yaraneth","Zaevithra",
            "Aelithra","Caelindra","Daravithra","Erithindra","Faenara","Galadra",
            "Halawindr","Ilindra","Jaelveth","Kaelithra","Liravindra","Maelithra",
            "Naerindra","Orivaelindra","Paelithra","Raelithra","Saelindra","Thalithra",
        ],
    },
    "Half-Elf": {
        "Male": [
            "Aeron","Brenniel","Caelen","Daran","Eladrin","Faelon","Garavel",
            "Haelon","Ilandor","Jaravel","Kaelon","Laran","Maeron","Naelon",
            "Oravel","Paeron","Raelon","Saeron","Taren","Uladon","Vaeron",
            "Waeron","Xaelon","Yalindor","Zaeron","Aethorn","Braelyn","Coravel",
            "Daelrin","Elavyn","Faelen","Garvel","Haelvyn","Ilandorn","Jaravel",
            "Kaelvyn","Loravel","Maelvyn","Naelvin","Oravel","Paelrin","Raelvin",
            "Saelthor","Tarendel","Uladon","Vaelorn","Waelindor","Xaelorn","Yalon",
        ],
        "Female": [
            "Aelara","Brayalin","Caelindra","Darawyn","Elawyn","Faelithra","Galwyn",
            "Haelith","Ilawyn","Jaravel","Kaelwyn","Lorawyn","Maelith","Naelwyn",
            "Orawyn","Paelith","Raelwyn","Saelith","Tarenwyn","Ulawyn","Vaelith",
            "Waelwyn","Xaelith","Yalawyn","Zaelith","Aelwyn","Braelith","Caelwyn",
            "Daraelith","Elaelwyn","Faelwyn","Galithra","Haelwyn","Ilaelith","Jaelwyn",
            "Kaelithra","Loraelwyn","Maelwyn","Naelithra","Oraelwyn","Paelwyn",
            "Raelithra","Saelwyn","Tarenelith","Ulaelwyn","Vaelwyn","Waelithra",
        ],
    },
    "Dwarf": {
        "Male": [
            "Baldrek","Cragmar","Durnok","Embrek","Fargrim","Grundar","Hordar",
            "Ironfist","Jarnok","Keldrek","Lornok","Margrim","Norgrim","Ovdrak",
            "Pargrim","Roldrek","Sornok","Thordak","Urgrim","Vordrak","Worgrim",
            "Xaldrek","Yordak","Zorgrim","Anvilmar","Boltrek","Copperhelm",
            "Deepstone","Emboldrek","Forgrim","Goldvein","Hammerfist","Ironvald",
            "Jadrak","Koboldrek","Lodemar","Moldrak","Nordak","Onyxfist","Peldrak",
            "Rockfist","Stoneback","Thunderforge","Underhelm","Vaultstone","Wardrek",
            "Xornak","Yearstone","Zornfist","Deepvein","Emberfist","Goldhelm",
        ],
        "Female": [
            "Baldra","Cragora","Durna","Embra","Fargra","Grundra","Hordra",
            "Ironlock","Jarna","Keldra","Lorna","Margra","Norgra","Ovdra",
            "Pargra","Roldra","Sorna","Thordra","Urgra","Vordra","Worgra",
            "Xaldra","Yordra","Zorgra","Anvilmere","Boldra","Copperlock",
            "Deepmere","Emboldra","Forgra","Goldvara","Hammerlock","Ironvara",
            "Jadra","Koboldra","Lodemere","Moldra","Nordra","Onyxlock","Peldra",
            "Rocklock","Stonedra","Thundermere","Undermere","Vaultstone","Wardra",
            "Xornara","Yearmere","Zornlock","Deepvara","Emberfist","Goldhera",
        ],
    },
    "Half-Orc": {
        "Male": [
            "Brak","Crusk","Drago","Furak","Grak","Hruun","Irok","Jurk",
            "Krusk","Lurk","Mrug","Nruuk","Orak","Prusk","Rruk","Skrag",
            "Thrusk","Urnak","Vruk","Wrusk","Xrak","Yruuk","Zrak","Grusk",
            "Ashrok","Bloodtusk","Crushfang","Darkgore","Embrak","Foulcry",
            "Grimtusk","Hawkrak","Ironjaw","Jawrak","Killrak","Lungrak",
            "Meatfist","Nightrak","Orcbreaker","Pugnrak","Razorfang","Skullsplit",
            "Throatcutter","Uglak","Vilerak","Warfang","Xgrak","Yarak","Zorrak",
            "Bonecrusher","Deathrak","Fleshrak","Gorrak","Hatrak","Ironrak",
        ],
        "Female": [
            "Brakka","Crukka","Drakka","Furka","Grakka","Hruka","Iroka","Jurka",
            "Kruska","Lurka","Mruka","Nruuka","Oraka","Pruska","Rruka","Skraga",
            "Thruska","Urnaka","Vruka","Wruska","Xraka","Yruuka","Zraka","Gruska",
            "Ashkra","Bloodmaw","Crushka","Darkgore","Embrakka","Foulka",
            "Grimka","Hawkrakka","Ironka","Jawka","Killka","Lungka",
            "Meatka","Nightka","Orcka","Pugnka","Razorka","Skullka",
            "Throatka","Uglaka","Vileka","Warfangka","Xgraka","Yaraka","Zoraka",
            "Boneka","Deathka","Fleshka","Goraka","Hatka","Ironka2",
        ],
    },
    "Halfling": {
        "Male": [
            "Alton","Beau","Corwin","Davy","Eldon","Finnan","Gareth","Harlow",
            "Idris","Jasper","Kelby","Lyle","Mace","Ned","Olbert","Perrin",
            "Quill","Remy","Sabin","Toby","Ubert","Vance","Wils","Xander",
            "Yarrow","Zeb","Adder","Birch","Cobble","Dill","Elder","Foxglove",
            "Gorse","Hemlock","Ivy","Juniper","Kelp","Lichen","Moss","Nettle",
            "Oak","Pine","Reed","Stone","Thistle","Wort","Bracken","Clover",
            "Daggon","Fern","Heather","Linden","Meadow","Nimble","Poplar",
        ],
        "Female": [
            "Ayla","Bree","Cora","Daisy","Ellie","Fern","Greta","Hana",
            "Ivy","Jessa","Kessa","Lena","Meda","Nell","Olla","Petra",
            "Quella","Rosie","Sassa","Tilda","Ula","Velta","Wella","Xenia",
            "Yarrow","Zinnia","Amber","Briar","Clover","Dew","Ember","Flora",
            "Goldie","Heather","Iris","Jasmine","Kindra","Lily","Marigold","Nettle",
            "Olive","Pansy","Rose","Sage","Thyme","Violet","Willow","Bramble",
            "Chrystal","Daffodil","Fennel","Gilia","Hollyhock","Larkspur","Mallow",
        ],
    },
    "Goblin": {
        "Male": [
            "Bograt","Cracktooth","Dribbles","Fizzwick","Gnarls","Hobgrin",
            "Jigglesnick","Klugrot","Lurch","Mumbleguts","Nicker","Ogglesnort",
            "Prickleface","Quirk","Ragtag","Snaggle","Twitchfinger","Ump",
            "Vortex","Weaselbite","Xyzzz","Yammer","Zazza","Ankler","Bungrat",
            "Crackle","Durbak","Eggwick","Fink","Giggles","Hinkson","Izzak",
            "Jitter","Klunk","Lumbag","Mumbak","Nuzzle","Oink","Pickle",
            "Quirker","Rattle","Snick","Trickle","Umble","Vex","Wiggler",
        ],
        "Female": [
            "Aggle","Bisket","Cackle","Dibble","Essie","Fizzle","Gigget",
            "Hickle","Idget","Jibble","Kickel","Lickle","Miggle","Nibble",
            "Oogle","Pickle","Quibble","Ribbon","Sickle","Tickle","Umble",
            "Vickle","Wiggle","Xickle","Yibble","Ziggle","Ample","Buckle",
            "Cribble","Dribble","Edgel","Fickle","Giggle","Hackle","Ickle",
            "Jiggle","Kiggle","Lattle","Moggle","Niggle","Oodle","Prickle",
            "Quibble","Rittle","Scribble","Ticklet","Uzzle","Vrittle","Wattle",
        ],
    },
    "Gnome": {
        "Male": [
            "Aldron","Brasswick","Cogsworth","Dinkledorf","Enormus","Fizzlebop",
            "Gadgetson","Hinckley","Ironfoot","Jubblewick","Kneematcher","Lodrick",
            "Metalsmith","Nozzlewig","Overton","Perpetuum","Quickspark","Ratchet",
            "Sprocket","Tinkertop","Umbrash","Velverton","Widgetson","Xanderbuck",
            "Yardworth","Zimmerson","Ashwick","Boltwick","Clockson","Dundersmith",
            "Epicson","Firkin","Gearwick","Hummingwick","Inchworth","Jobsworth",
            "Kindlebug","Lowinton","Metalwick","Noddertop","Owlerson","Potlewick",
        ],
        "Female": [
            "Alatrice","Bristlethorn","Copperglow","Dinkledame","Earnestine","Fizzleberta",
            "Gadgetina","Hinckley","Ironfoot","Justicia","Kindlewick","Lodrina",
            "Metalshire","Nozzlewing","Overlee","Perpetuine","Quicksilva","Ratchella",
            "Sprocketine","Tinkertree","Umbrella","Velvetwine","Widgetina","Xandra",
            "Yardbottom","Zimmerlina","Ashwicke","Boltina","Clockwin","Dundertop",
            "Epicine","Firkinella","Gearwin","Hummingtop","Inchley","Jobina",
            "Kindlebright","Lowin","Metaltine","Nodderlee","Owlette","Potlina",
        ],
    },
    "Lizardfolk": {
        "Male": [
            "Ssarask","Kzzarak","Thessak","Vvessik","Krrassik","Thissik","Vzzessik",
            "Rrassak","Sszarak","Krzzask","Thessik","Vrrassak","Kzzzash","Thrassik",
            "Vsszashi","Rzzhask","Szzarak","Krrash","Thessik","Vrrhash","Kzzhash",
            "Thrask","Vsshak","Rzzhak","Szzak","Krash","Thask","Vrash","Kzhak",
            "Tharak","Vshak","Rzhak","Szak","Krah","Tha","Vra","Kza",
            "Thaskan","Vrasskan","Krithan","Thesskan","Vrithak","Krissak","Thissak","Vrathak",
        ],
        "Female": [
            "Sssara","Kzzzara","Thessara","Vvvessa","Krrassa","Thissa","Vzzhessa",
            "Rrassa","Sszessa","Krrassa","Thessara","Vrassa","Kzzassa","Thrassa",
            "Vssha","Rzzassa","Szzara","Krassa","Thessa","Vrrassa","Kzzhassa",
            "Thassa","Vsshassa","Rzhassa","Szassa","Krassa","Thassa","Vrassa","Kzassa",
            "Tharassa","Vshassa","Rzhassa","Szassa","Krassa","Thassa","Vrassa","Kzassa",
            "Thassia","Vrassia","Krithra","Thessia","Vrithia","Krissa","Thissa","Vratha",
        ],
    },
    "Tabaxi": {
        "Male": [
            "Alder","Bladewing","Clawstrike","Duskpaw","Emberclaw","Fang",
            "Gideon","Hawkstrike","Ironpaw","Jadewhisker","Kingsmane","Lionclaw",
            "Moonwhisker","Nightstalker","Ocelot","Pantherfang","Quietstep","Razorpaw",
            "Shadowpounce","Tigerclaw","Understalker","Velvetpaw","Whiskerwind","Xeric",
            "Yelloweye","Zenith","Arzak","Blacktail","Crescent","Darkclaw","Echowing",
            "Firemane","Golden","Huntmaster","Ivory","Jaguarjaw","Killdark",
        ],
        "Female": [
            "Astraea","Blaze","Cinnamon","Dapple","Ebony","Felicity","Gold",
            "Henna","Iris","Jade","Kestrel","Luna","Midnight","Nyx",
            "Opal","Peony","Quicksilver","Ruby","Sienna","Topaz","Umber",
            "Velvet","Whisper","Xandra","Yarrow","Zephyr","Ashilotte","Bramble",
            "Cora","Dove","Evernice","Finch","Giselle","Hazel","Iris",
        ],
    },
}

# Fallback for any unlisted race
_NAMES["Monster"] = _NAMES["Half-Orc"]
_NAMES["Peasant"] = _NAMES["Human"]


def _pick_name(race: str, gender: str, used_names: set) -> str:
    """Pick a unique name from the table, falling back to Human if race unknown."""
    pool = _NAMES.get(race, _NAMES["Human"]).get(gender, _NAMES["Human"]["Male"])
    available = [n for n in pool if n not in used_names]
    if not available:
        # Exhaust the pool — add a numeric suffix
        base = random.choice(pool)
        suffix = sum(1 for n in used_names if n.startswith(base))
        return f"{base} {_roman(suffix+1)}"
    return random.choice(available)


def _roman(n: int) -> str:
    vals = [(10,"X"),(9,"IX"),(5,"V"),(4,"IV"),(1,"I")]
    result = ""
    for val,sym in vals:
        while n >= val:
            result += sym; n -= val
    return result


# ---------------------------------------------------------------------------
# STYLE CONFIG
# ---------------------------------------------------------------------------

_STYLE_STRATEGIES = {
    "aggressive": dict(style="Strike",       activity=7, aim_point="Head",  defense_point="None"),
    "berserker":  dict(style="Total Kill",   activity=9, aim_point="Head",  defense_point="None"),
    "defensive":  dict(style="Parry",        activity=3, aim_point="Chest", defense_point="Chest"),
    "balanced":   dict(style="Counterstrike",activity=5, aim_point="Chest", defense_point="Chest"),
    "tactician":  dict(style="Feint",        activity=4, aim_point="Chest", defense_point="Chest"),
}

_STYLE_WEAPONS = {
    "aggressive": ["Morningstar","Battle Axe","Great Sword"],
    "berserker":  ["Great Axe","War Flail","Great Sword"],
    "defensive":  ["Short Sword","Morningstar","Boar Spear"],
    "balanced":   ["Morningstar","Short Sword","Battle Axe"],
    "tactician":  ["Short Sword","Boar Spear","Morningstar"],
}

_STYLE_ARMOR = {
    "aggressive": "Brigandine",
    "berserker":  "Leather",
    "defensive":  "Full Plate",
    "balanced":   "Chain",
    "tactician":  "Cuir Boulli",
}


# ---------------------------------------------------------------------------
# WARRIOR BUILDER
# ---------------------------------------------------------------------------

def _build_ai_warrior(style: str, races: List[str], used_names: set) -> dict:
    import sys; sys.path.insert(0, BASE_DIR)
    from warrior import Warrior, generate_base_stats, Strategy, ai_rollup
    from races   import list_playable_races

    valid = list_playable_races()
    race  = random.choice([r for r in races if r in valid] or ["Human"])
    gender= random.choice(["Male","Female"])
    name  = _pick_name(race, gender, used_names)
    used_names.add(name)

    base  = generate_base_stats()
    final = ai_rollup(base, race)

    w = Warrior(name=name, race_name=race, gender=gender, **final)
    w.luck           = random.randint(1, 30)
    
    # Race-specific weapon selections
    base_weapons = _STYLE_WEAPONS[style]
    if race == "Goblin":
        # Goblins prefer light, thrown weapons and dirty-fighting tools
        w.primary_weapon = random.choice(["Short Sword","Dagger","Javelin","Hatchet","Stiletto","Bola","Club"])
    elif race == "Gnome":
        # Gnomes prefer swords and hammers
        w.primary_weapon = random.choice(["Short Sword","Hammer","Morningstar","Mace"])
    elif race == "Lizardfolk":
        # Lizardfolk favor martial combat and light-to-mid weapons
        w.primary_weapon = random.choice(["Open Hand","Dagger","Short Sword","Hammer"])
    elif race == "Tabaxi":
        # Tabaxi prefer speed-focused weapons and mobile tactics
        w.primary_weapon = random.choice(["Dagger","Short Sword","Scimitar","Stiletto","Bola","Heavy Barbed Whip"])
    else:
        w.primary_weapon = random.choice(base_weapons)
    
    # Race-specific armor selections
    base_armor = _STYLE_ARMOR[style]
    if race == "Goblin":
        # Goblins need light armor for speed
        w.armor = "Leather" if base_armor != "Cloth" else "Cloth"
    elif race == "Lizardfolk":
        # Lizardfolk keep light armor due to natural scales
        w.armor = "Cloth" if style != "defensive" else "Leather"
    elif race == "Tabaxi":
        # Tabaxi keep minimal armor for maximum agility
        w.armor = "Cloth" if style != "defensive" else "Leather"
    else:
        w.armor = base_armor

    # Race-specific style/strategy adjustments
    sp = _STYLE_STRATEGIES[style]
    if race == "Lizardfolk" and style not in ("berserker", "aggressive"):
        # Lizardfolk excel with Martial Combat
        sp = {"style": "Martial Combat", "activity": 5, "aim_point": "Chest", "defense_point": "Chest"}
    elif race == "Gnome" and style == "tactician":
        # Gnomes excel with Counterstrike
        sp = {"style": "Counterstrike", "activity": 5, "aim_point": "Chest", "defense_point": "Chest"}
    
    w.strategies = [Strategy(
        trigger=("Always"), style=sp["style"], activity=sp["activity"],
        aim_point=sp["aim_point"], defense_point=sp["defense_point"],
    )]

    # Race-specific training pools
    trains_pool = {
        "aggressive": ["strength","constitution","initiative"],
        "berserker":  ["strength","initiative"],
        "defensive":  ["constitution","parry","dodge"],
        "balanced":   ["strength","dexterity","dodge"],
        "tactician":  ["intelligence","dexterity","feint","dodge"],
    }.get(style, ["strength"])
    
    # Adjust training based on race
    if race == "Goblin":
        trains_pool = ["dexterity","initiative","dodge"]
    elif race == "Gnome":
        trains_pool = ["parry","counterstrike","dodge"]
    elif race == "Lizardfolk":
        trains_pool = ["constitution","martial_combat","dodge"]
    elif race == "Tabaxi":
        trains_pool = ["dexterity","dodge","initiative"]
    
    w.trains = random.sample(trains_pool, min(3, len(trains_pool)))

    return w.to_dict()


def build_ai_team(manager_idx: int, global_used_names: set = None) -> dict:
    name, team_name, style, races, tier = AI_MANAGER_ROSTER[manager_idx]
    manager_id  = f"ai_{manager_idx:02d}"
    used_names  = set(global_used_names) if global_used_names else set()
    warriors    = [_build_ai_warrior(style, races, used_names) for _ in range(5)]
    return {
        "manager_id"  : manager_id,
        "manager_name": name,
        "team_name"   : team_name,
        "team_id"     : 9000 + manager_idx,
        "warriors"    : warriors,
        "style"       : style,
        "tier"        : tier,
        "turn_history": [],
    }


# ---------------------------------------------------------------------------
# PERSISTENCE
# ---------------------------------------------------------------------------

def _ensure_dir():
    os.makedirs(os.path.dirname(AI_TEAMS_FILE), exist_ok=True)

def save_ai_teams(teams: List[dict]):
    _ensure_dir()
    with open(AI_TEAMS_FILE, "w", encoding="utf-8") as f:
        json.dump(teams, f, indent=2, default=str)

def load_ai_teams() -> List[dict]:
    if not os.path.exists(AI_TEAMS_FILE): return []
    try:
        with open(AI_TEAMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception: return []

def get_or_create_ai_teams() -> List[dict]:
    teams = load_ai_teams()
    if len(teams) >= len(AI_MANAGER_ROSTER):
        return teams
    # Collect names already in use across any loaded teams
    global_used_names = set()
    for t in teams:
        for w in t.get("warriors", []):
            if w and w.get("name"):
                global_used_names.add(w["name"])
    # Build any missing teams
    existing_ids = {t["manager_id"] for t in teams}
    for i in range(len(AI_MANAGER_ROSTER)):
        mid = f"ai_{i:02d}"
        if mid in existing_ids:
            continue
        team = build_ai_team(i, global_used_names)
        global_used_names.update(
            w["name"] for w in team.get("warriors", []) if w and w.get("name")
        )
        teams.append(team)
    save_ai_teams(teams)
    print(f"  Generated {len(teams)} AI league teams.")
    return teams


# ---------------------------------------------------------------------------
# POST-TURN: update records, handle deaths, replace dead warriors
# ---------------------------------------------------------------------------

def evolve_ai_teams(teams: List[dict], turn_results: dict) -> List[dict]:
    """
    After each turn:
    - Apply updated warrior state from turn results (records, fight history, deaths)
    - Replace dead warriors with fresh named recruits
    - Train surviving warriors
    """
    import sys; sys.path.insert(0, BASE_DIR)
    from warrior import Warrior

    for team in teams:
        mid = team["manager_id"]
        res = turn_results.get(mid, {})

        # Collect names already in use on this team (for replacement naming)
        used_names = {
            w["name"] for w in team.get("warriors", []) if w and w.get("name")
        }

        # If the turn result has an updated team snapshot, use it as the base
        result_team = res.get("team", {})
        if result_team and result_team.get("warriors"):
            updated = result_team["warriors"]
        else:
            updated = team.get("warriors", [])

        new_warriors = []
        style  = team.get("style", "balanced")
        races  = [w.get("race", "Human") for w in updated if w] or ["Human"]

        for wd in updated:
            if not wd:
                new_warriors.append(None)
                continue
            try:
                w = Warrior.from_dict(wd)
                if getattr(w, "is_dead", False):
                    # Archive the dead warrior before replacing (cumulative record)
                    snapshot = w.to_dict()
                    snapshot["archived_killed_by"] = getattr(w, "killed_by", "Unknown")
                    snapshot["archived_turns"]     = getattr(w, "turns_active", 0)
                    team.setdefault("archived_warriors", []).append(snapshot)
                    # Replace with a fresh named warrior
                    used_names.discard(w.name)
                    replacement = _build_ai_warrior(style, races, used_names)
                    used_names.add(replacement["name"])
                    print(f"  AI replacement: {w.name} ({team['team_name']}) → {replacement['name']}")
                    new_warriors.append(replacement)
                else:
                    # Train surviving warriors
                    for sk in w.trains[:3]:
                        try: w.train_skill(sk)
                        except Exception: pass
                    w.recalculate_derived()
                    new_warriors.append(w.to_dict())
            except Exception:
                new_warriors.append(wd)

        team["warriors"] = new_warriors

        # Update turn history on the team
        bouts = res.get("bouts", [])
        if bouts:
            w_count = sum(1 for b in bouts if b.get("result","") == "WIN")
            l_count = sum(1 for b in bouts if b.get("result","") == "LOSS")
            k_count = sum(1 for b in bouts if b.get("opponent_slain"))
            team.setdefault("turn_history", []).append({
                "turn": res.get("turn", 0),
                "w": w_count, "l": l_count, "k": k_count,
            })

    save_ai_teams(teams)
    return teams


# ---------------------------------------------------------------------------
# BUILD RivalManager-COMPATIBLE OBJECTS FROM AI TEAMS (for local matchmaking)
# ---------------------------------------------------------------------------

def ai_teams_as_rivals(ai_teams: List[dict]):
    """
    Convert AI team dicts into objects compatible with build_fight_card()'s
    rival list. Returns a list of lightweight rival objects.
    """
    import sys; sys.path.insert(0, BASE_DIR)
    from team import Team

    class _AIRival:
        """Minimal RivalManager-compatible wrapper for an AI team."""
        def __init__(self, mid, mname, team, tier=2):
            self.manager_id        = mid
            self.manager_name      = mname
            self.team_name         = team.team_name
            self.team              = team
            self.tier              = tier
            self.fights_completed  = 0

        def post_fight_update(self):
            pass   # AI rivals don't need local training updates

    rivals = []
    for at in ai_teams:
        try:
            team = Team.from_dict(at)
            if not team.active_warriors:
                continue
            rivals.append(_AIRival(
                mid   = at["manager_id"],
                mname = at["manager_name"],
                team  = team,
                tier  = at.get("tier", 2),
            ))
        except Exception as e:
            print(f"  WARNING: could not build rival from AI team {at.get('team_name','?')}: {e}")
    return rivals
