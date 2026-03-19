#!/usr/bin/env python3
# =============================================================================
# test_milestone3.py — Tests for strategy, narrative, combat, + sample fight
# Run: python test_milestone3.py
# =============================================================================

import sys
sys.path.insert(0, ".")

from warrior   import Warrior, Strategy
from strategy  import (
    FighterState, evaluate_triggers, get_style_advantage, get_style_props,
    STYLE_PROPERTIES,
)
from narrative import (
    build_fight_header, popularity_desc, damage_line,
    miss_line, parry_line, hit_line, knockdown_line, perm_injury_lines,
)
from combat    import CombatEngine, run_fight, _calc_apm, _calc_damage, _CState

PASS = "  ✓"
FAIL = "  ✗"
errors = 0


def check(condition, label):
    global errors
    if condition:
        print(f"{PASS}  {label}")
    else:
        print(f"{FAIL}  FAILED: {label}")
        errors += 1


print("\n=============================================")
print("  BLOOD PIT — MILESTONE 3 TESTS")
print("=============================================\n")

# =============================================================================
print("[ strategy.py — trigger evaluation ]")

# Build two simple warriors for trigger testing
def make_warrior(name, race="Human", **stats):
    defaults = dict(strength=12, dexterity=12, constitution=12,
                    intelligence=12, presence=12, size=12)
    defaults.update(stats)
    w = Warrior(name, race, "Male", **defaults)
    w.strategies = [
        Strategy(trigger="Minute 2",             style="Wall of Steel", activity=7, aim_point="Head",  defense_point="Chest"),
        Strategy(trigger="You are tired",        style="Parry",         activity=3, aim_point="None",  defense_point="Chest"),
        Strategy(trigger="Your foe is on the ground", style="Total Kill", activity=8, aim_point="Head", defense_point="None"),
        Strategy(trigger="Always",               style="Strike",        activity=5, aim_point="None",  defense_point="Chest"),
    ]
    return w

wa = make_warrior("Alpha")
wb = make_warrior("Beta")

def make_fs(w, hp=None, end=100.0, ground=False):
    hp = hp or w.max_hp
    st = FighterState(
        warrior=w, current_hp=hp, max_hp=w.max_hp,
        endurance=end, is_on_ground=ground,
        active_strategy_idx=1, active_strategy=w.strategies[0],
    )
    return st

# Minute 1 — "Always" should match (strategy 4)
fs_a = make_fs(wa)
fs_b = make_fs(wb)
strat, idx = evaluate_triggers(wa.strategies, fs_a, fs_b, minute=1)
check(strat.style == "Strike", f"Minute 1 → Always strategy → Strike (idx={idx})")
check(idx == 4,                f"Minute 1 → idx=4 (correct)")

# Minute 2 — "Minute 2" trigger fires (strategy 1)
strat2, idx2 = evaluate_triggers(wa.strategies, fs_a, fs_b, minute=2)
check(strat2.style == "Wall of Steel", f"Minute 2 → Wall of Steel trigger fires (idx={idx2})")
check(idx2 == 1, "Minute 2 → idx=1")

# "You are tired" fires at endurance=35
fs_tired = make_fs(wa, end=35.0)
strat3, idx3 = evaluate_triggers(wa.strategies, fs_tired, fs_b, minute=1)
check(strat3.style == "Parry", f"Tired (end=35) → Parry strategy fires (idx={idx3})")

# "Your foe is on the ground" fires when foe is down
fs_foe_down = make_fs(wb, ground=True)
strat4, idx4 = evaluate_triggers(wa.strategies, fs_a, fs_foe_down, minute=1)
check(strat4.style == "Total Kill", f"Foe on ground → Total Kill strategy fires (idx={idx4})")

# =============================================================================
print("\n[ strategy.py — style advantages ]")

# From the guide: Lunge counters WoS "incredibly well" → should be +2
check(get_style_advantage("Lunge", "Wall of Steel") == 2,
      "Lunge vs Wall of Steel = +2 (attacker advantage)")
check(get_style_advantage("Wall of Steel", "Lunge") == -2,
      "WoS vs Lunge = -2 (defender advantage)")
check(get_style_advantage("Strike", "Strike") == 0,
      "Strike vs Strike = 0 (neutral)")

# Style properties
tk_props = get_style_props("Total Kill")
check(tk_props.intimidate == True,            "Total Kill has intimidate flag")
check(tk_props.total_kill_mode == True,       "Total Kill has total_kill_mode flag")
check(tk_props.endurance_burn >= 6,           "Total Kill burns endurance hard")
check(tk_props.apm_modifier > 0,             "Total Kill positive APM modifier")

parry_props = get_style_props("Parry")
check(parry_props.endurance_burn < 0,         "Parry gains endurance (negative burn)")
check(parry_props.parry_bonus >= 5,           "Parry has big parry bonus")
check(parry_props.anxiously_awaits == False,  "Parry doesn't have anxiously awaits")

strike_props = get_style_props("Strike")
check(strike_props.anxiously_awaits == True,  "Strike has anxiously awaits")

check(len(STYLE_PROPERTIES) == 15, f"All 15 fighting styles defined ({len(STYLE_PROPERTIES)})")

# =============================================================================
print("\n[ narrative.py — text generation ]")

check(popularity_desc(51) == "POPULAR WITH THE KIDS",    "Popularity 51 → correct desc")
check(popularity_desc(82) == "HAS HORDES OF ADORING FANS", "Popularity 82 → correct desc")
check(popularity_desc(0)  == "WIDELY REVILED",           "Popularity 0 → correct desc")
check(popularity_desc(95) == "A LEGENDARY HERO OF THE PIT", "Popularity 95 → correct desc")

# Damage line tiers
w_test = Warrior("DmgTest","Human","Male",strength=12,dexterity=12,
                  constitution=12,intelligence=12,presence=12,size=12)
dl = damage_line(1, 60)
check(dl.startswith("   "), "Damage line starts with spaces (indented)")

hit_lines = hit_line("Gear Head", "Burly Bob", "Great Pick", "Oddball", "Head")
check(len(hit_lines) >= 1, "hit_line returns at least 1 line")
check(any("GEAR HEAD" in l or "BURLY BOB" in l for l in hit_lines),
      "hit_line contains warrior names")

ml = miss_line("Burly Bob", "War Flail")
check("BURLY BOB" in ml.upper(), "miss_line contains warrior name")

pl = parry_line("Gear Head", barely=False, defense_point_active=True)
check(len(pl) > 0, f"parry_line produced: {pl[:40]}")

kd = knockdown_line("Burly Bob", "Male")
check("BURLY BOB" in kd, "knockdown_line contains warrior name")

perm_lines = perm_injury_lines("Burly Bob", "primary_leg", 2, "Male")
check(len(perm_lines) == 3,   "perm_injury_lines returns 3 lines")
check("BURLY BOB" in perm_lines[0], "First perm line contains warrior name")
check("PRIMARY LEG" in perm_lines[0].upper() or "MAIN LEG" in perm_lines[0].upper(),
      f"First perm line mentions the location: {perm_lines[0]}")

# Fight header
w_a = Warrior("Burly Bob","Half-Orc","Male",
               strength=17,dexterity=9,constitution=14,
               intelligence=9,presence=8,size=14)
w_b = Warrior("Gear Head","Human","Male",
               strength=16,dexterity=19,constitution=15,
               intelligence=15,presence=12,size=9)
w_a.wins=24; w_a.losses=27; w_a.armor="Brigandine"; w_a.helm=None
w_a.primary_weapon="War Flail"; w_a.secondary_weapon="War Flail"
w_b.wins=37; w_b.losses=10; w_b.draws=9; w_b.armor="Cuir Boulli"
w_b.helm="Steel Cap"; w_b.primary_weapon="Great Pick"; w_b.secondary_weapon="Open Hand"
w_b.backup_weapon="Great Pick"

header = build_fight_header(w_a, w_b, "Eternal Champions", "The Head Hunters",
                            "The Keeper", "The Warlord")
check("BURLY BOB" in header, "Fight header contains warrior A name")
check("GEAR HEAD" in header, "Fight header contains warrior B name")
check("WAR FLAIL" in header, "Fight header contains weapon")
check("GREAT PICK" in header, "Fight header contains weapon B")
check("BRIGANDINE" in header, "Fight header contains armor")
check("RECORD" in header, "Fight header contains RECORD label")

# =============================================================================
print("\n[ combat.py — APM calculation ]")

def make_cs(warrior):
    s = _CState(warrior=warrior, current_hp=warrior.max_hp, endurance=100.0)
    s.active_strategy = warrior.strategies[0] if warrior.strategies else Strategy()
    return s

# High DEX warrior at high activity should have more APM than low DEX at low activity
high_dex = Warrior("Fast","Elf","Female",
                    strength=10,dexterity=19,constitution=10,
                    intelligence=14,presence=10,size=9)
high_dex.strategies = [Strategy(trigger="Always",style="Wall of Steel",activity=8)]
low_dex = Warrior("Slow","Half-Orc","Male",
                   strength=17,dexterity=9,constitution=14,
                   intelligence=9,presence=8,size=14)
low_dex.strategies = [Strategy(trigger="Always",style="Strike",activity=4)]

cs_fast = make_cs(high_dex)
cs_slow = make_cs(low_dex)

apm_fast = _calc_apm(high_dex, high_dex.strategies[0], cs_fast)
apm_slow = _calc_apm(low_dex,  low_dex.strategies[0],  cs_slow)
check(apm_fast > apm_slow, f"High-DEX Elf WoS ({apm_fast}) > Low-DEX Half-Orc Strike ({apm_slow})")
check(apm_fast >= 2, f"Fast warrior has at least 2 APM ({apm_fast})")
check(apm_slow >= 1, f"Slow warrior has at least 1 APM ({apm_slow})")

# Parry style should have low APM
parry_warrior = Warrior("Defender","Dwarf","Male",
                         strength=14,dexterity=12,constitution=15,
                         intelligence=10,presence=10,size=12)
parry_warrior.strategies = [Strategy(trigger="Always",style="Parry",activity=2)]
cs_parry = make_cs(parry_warrior)
apm_parry = _calc_apm(parry_warrior, parry_warrior.strategies[0], cs_parry)
check(apm_parry <= 2, f"Parry style has low APM ({apm_parry})")

# =============================================================================
print("\n[ combat.py — damage calculation ]")

def make_strat(style, activity=5):
    s = Strategy(trigger="Always", style=style, activity=activity)
    return s

attacker = Warrior("Striker","Half-Orc","Male",
                    strength=17,dexterity=10,constitution=14,
                    intelligence=9,presence=8,size=17)
attacker.armor="Brigandine"; attacker.primary_weapon="War Flail"

defender_light = Warrior("LightArmor","Human","Male",
                          strength=10,dexterity=12,constitution=10,
                          intelligence=12,presence=10,size=10)
defender_light.armor="Leather"

defender_heavy = Warrior("HeavyArmor","Dwarf","Male",
                          strength=14,dexterity=10,constitution=15,
                          intelligence=10,presence=10,size=12)
defender_heavy.armor="Full Plate"; defender_heavy.helm="Full Helm"

dmg_vs_light, _ = _calc_damage(attacker, make_strat("Total Kill", 8), "War Flail", defender_light)
dmg_vs_heavy, _ = _calc_damage(attacker, make_strat("Total Kill", 8), "War Flail", defender_heavy)
check(dmg_vs_light > 0,           f"Damage vs light armor > 0: {dmg_vs_light}")
check(dmg_vs_heavy > 0,           f"Damage vs heavy armor > 0: {dmg_vs_heavy}")
check(dmg_vs_light > dmg_vs_heavy,f"Light armor gets more damage ({dmg_vs_light}) than Heavy ({dmg_vs_heavy})")

# AP weapon vs AP-vulnerable armor
ap_attacker = Warrior("APUser","Human","Male",
                       strength=14,dexterity=14,constitution=12,
                       intelligence=12,presence=10,size=11)
ap_attacker.primary_weapon="Military Pick"

defender_chain = Warrior("Chain","Human","Male",
                          strength=14,dexterity=12,constitution=12,
                          intelligence=10,presence=10,size=12)
defender_chain.armor="Chain"
defender_leather = Warrior("Leather","Human","Male",
                            strength=10,dexterity=12,constitution=12,
                            intelligence=10,presence=10,size=12)
defender_leather.armor="Leather"

# Run multiple times to get average (due to randomness)
import statistics
ap_vs_chain   = [_calc_damage(ap_attacker, make_strat("Strike"), "Military Pick", defender_chain)[0] for _ in range(30)]
ap_vs_leather = [_calc_damage(ap_attacker, make_strat("Strike"), "Military Pick", defender_leather)[0] for _ in range(30)]
avg_chain   = statistics.mean(ap_vs_chain)
avg_leather = statistics.mean(ap_vs_leather)
check(avg_chain > avg_leather * 0.8,
      f"AP weapon vs Chain ({avg_chain:.1f}) not much less than vs Leather ({avg_leather:.1f}) — AP reduces armor")

# =============================================================================
print("\n")
print("=" * 62)
print("  FULL SAMPLE FIGHT: BURLY BOB vs GEAR HEAD")
print("=" * 62)
print()

# Recreate warriors close to the sample fight in the guide
bob = Warrior(
    "Burly Bob", "Half-Orc", "Male",
    strength=17, dexterity=9, constitution=14,
    intelligence=9, presence=8, size=14,
)
bob.armor="Brigandine"; bob.helm=None
bob.primary_weapon="War Flail"; bob.secondary_weapon="War Flail"
bob.backup_weapon=None
bob.popularity=51; bob.wins=24; bob.losses=27
bob.strategies = [
    Strategy(trigger="Always", style="Strike", activity=6,
             aim_point="Chest", defense_point="Chest"),
]
bob.trains = ["war_flail"]

gear = Warrior(
    "Gear Head", "Human", "Male",
    strength=16, dexterity=19, constitution=15,
    intelligence=15, presence=12, size=9,
)
gear.armor="Cuir Boulli"; gear.helm="Steel Cap"
gear.primary_weapon="Great Pick"; gear.secondary_weapon="Open Hand"
gear.backup_weapon="Great Pick"
gear.popularity=82; gear.wins=37; gear.losses=10; gear.draws=9
gear.strategies = [
    Strategy(trigger="Always", style="Calculated Attack", activity=7,
             aim_point="Head", defense_point="Chest"),
]
gear.trains = ["dodge", "dodge"]

result = run_fight(
    bob, gear,
    team_a_name="Eternal Champions", team_b_name="The Head Hunters",
    manager_a_name="The Keeper", manager_b_name="The Warlord",
)

print(result.narrative)

print()
print("=" * 62)
print("  FIGHT RESULT")
print("=" * 62)
if result.winner:
    print(f"  WINNER: {result.winner.name}")
    print(f"  LOSER:  {result.loser.name}")
    print(f"  DIED:   {result.loser_died}")
else:
    print("  RESULT: DRAW")
print(f"  DURATION: {result.minutes_elapsed} minute(s)")
if result.training_results:
    print("  TRAINING:")
    for name, results in result.training_results.items():
        for r in results:
            print(f"    {name}: {r}")

# =============================================================================
print()
print("=============================================")
if errors == 0:
    print("  ALL TESTS PASSED")
else:
    print(f"  {errors} TEST(S) FAILED")
print("=============================================\n")
