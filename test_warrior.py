#!/usr/bin/env python3
# =============================================================================
# test_warrior.py — Smoke tests for warrior.py and races.py
# Run: python test_warrior.py
# =============================================================================

import sys
sys.path.insert(0, ".")

from races  import list_playable_races, get_race
from warrior import (
    Warrior, create_warrior_ai, generate_base_stats, ai_rollup,
    validate_additions, get_stat_description, compare_stats,
    ATTRIBUTES, ROLLUP_POINTS, STAT_MIN, STAT_MAX
)

PASS = "  ✓"
FAIL = "  ✗"

errors = 0

def check(condition: bool, label: str):
    global errors
    if condition:
        print(f"{PASS}  {label}")
    else:
        print(f"{FAIL}  FAILED: {label}")
        errors += 1


# ---------------------------------------------------------------------------
print("\n========================================")
print("  BLOOD PIT — WARRIOR MODULE SMOKE TEST")
print("========================================\n")

# ---------------------------------------------------------------------------
print("[ Race system ]")
playable = list_playable_races()
check(len(playable) == 6, f"6 playable races found: {playable}")

all_races = ["Human","Half-Orc","Halfling","Dwarf","Half-Elf","Elf","Monster","Peasant"]
for r in all_races:
    race_obj = get_race(r)
    check(race_obj.name == r, f"Race '{r}' loads correctly")

# ---------------------------------------------------------------------------
print("\n[ Stat descriptions ]")
check(get_stat_description("strength", 17) == "Is of formidable strength",
      "STR 17 → 'Is of formidable strength'")
check(get_stat_description("strength", 3) == "Jelly-fish like",
      "STR 3 → 'Jelly-fish like'")
check(get_stat_description("dexterity", 19) == "Has swift movements",
      "DEX 19 → 'Has swift movements'")
check(get_stat_description("size", 9) == "Has a wiry frame",
      "SIZE 9 → 'Has a wiry frame'")
check(get_stat_description("constitution", 14) == "Has a tough constitution",
      "CON 14 → 'Has a tough constitution'")

# ---------------------------------------------------------------------------
print("\n[ compare_stats ]")
check(compare_stats(10, 10) == "   ", "Equal stats (10 vs 10) → '   '")
check(compare_stats(10, 12) == "   ", "Within-2 (10 vs 12) → '   '")
check(compare_stats(10, 13) == "-->", "3-gap: B wins (10 vs 13) → '-->'")
check(compare_stats(15, 10) == "<--", "3-gap: A wins (15 vs 10) → '<--'")

# ---------------------------------------------------------------------------
print("\n[ HP formula ]")
# Formula: 2*SIZE + CON*1.5 + STR*0.5 + racial_bonus, capped at 100

# Test: Human warrior with SIZE=15, CON=14, STR=12 → 30+21+6 = 57 HP
human = Warrior("TestHuman","Human","Male",
                strength=12, dexterity=10, constitution=14,
                intelligence=10, presence=10, size=15)
expected_hp = min(100, int(2*15 + 14*1.5 + 12*0.5 + 0))   # 0 = no Human HP bonus
check(human.max_hp == expected_hp, f"Human HP formula: {human.max_hp} == {expected_hp}")

# Test: Dwarf (+12 HP bonus) with SIZE=12, CON=15, STR=14
dwarf = Warrior("TestDwarf","Dwarf","Male",
                strength=14, dexterity=8, constitution=15,
                intelligence=8, presence=8, size=12)
expected_dwarf_hp = min(100, int(2*12 + 15*1.5 + 14*0.5 + 12))  # +12 racial
check(dwarf.max_hp == expected_dwarf_hp,
      f"Dwarf HP formula (with +12 racial bonus): {dwarf.max_hp} == {expected_dwarf_hp}")

# Test: Elf (-6 HP penalty) with SIZE=10, CON=12, STR=9
elf = Warrior("TestElf","Elf","Female",
              strength=9, dexterity=14, constitution=12,
              intelligence=12, presence=9, size=10)
expected_elf_hp = max(1, min(100, int(2*10 + 12*1.5 + 9*0.5 - 6)))  # -6 racial
check(elf.max_hp == expected_elf_hp,
      f"Elf HP formula (with -6 racial penalty): {elf.max_hp} == {expected_elf_hp}")

# Test: Cap at 100 — SIZE=25, CON=25, STR=25 → 50+37+12+8 = 107 → capped at 100
big = Warrior("TestBig","Half-Orc","Male",
              strength=25, dexterity=8, constitution=25,
              intelligence=6, presence=6, size=25)
check(big.max_hp == 100, f"HP capped at 100 (raw would be very high): max_hp={big.max_hp}")

# ---------------------------------------------------------------------------
print("\n[ Halfling measurements ]")
# Guide says Halflings are 33 inches tall. Verify our measurement formula.
halfling = Warrior("TinyTim","Halfling","Male",
                   strength=8, dexterity=14, constitution=10,
                   intelligence=10, presence=9, size=10)
check(halfling.height_in < 50, f"Halfling is short: {halfling.height_in}\" (should be ~30-40\")")
check(halfling.weight_lbs < 100, f"Halfling is light: {halfling.weight_lbs} lbs")

# ---------------------------------------------------------------------------
print("\n[ Roll-up system ]")
base = generate_base_stats()
check(all(5 <= v <= 10 for v in base.values()),
      f"Base stats in range 5-10: {base}")
check(len(base) == 6, "Base stats has all 6 attributes")

# Validate additions
good_additions = {"strength":3, "dexterity":3, "constitution":3,
                  "intelligence":2, "presence":2, "size":3}
check(sum(good_additions.values()) == ROLLUP_POINTS,
      f"Test additions sum to {ROLLUP_POINTS}")
try:
    final = validate_additions(base, good_additions)
    check(True, "validate_additions accepted valid point spread")
except ValueError as e:
    check(False, f"validate_additions REJECTED valid spread: {e}")

# Over-budget rejection
bad_additions = {"strength":7, "dexterity":7, "constitution":7,
                 "intelligence":2, "presence":2, "size":2}
try:
    validate_additions(base, bad_additions)
    check(False, "validate_additions should reject over-budget (27 pts)")
except ValueError:
    check(True, "validate_additions correctly rejects 27-pt allocation")

# Over-cap per stat
over_cap = {"strength":8, "dexterity":3, "constitution":3,
            "intelligence":1, "presence":1, "size":0}
try:
    validate_additions(base, over_cap)
    check(False, "validate_additions should reject >7 per stat")
except ValueError:
    check(True, "validate_additions correctly rejects >7 per stat (8 to strength)")

# ---------------------------------------------------------------------------
print("\n[ AI warrior creation ]")
for race in list_playable_races():
    ai_w = create_warrior_ai(race_name=race)
    check(ai_w.race.name == race, f"AI warrior race matches: {race}")
    check(STAT_MIN <= ai_w.strength <= STAT_MAX, f"{race}: STR in valid range ({ai_w.strength})")
    check(STAT_MIN <= ai_w.size <= STAT_MAX,     f"{race}: SIZE in valid range ({ai_w.size})")
    check(ai_w.max_hp >= 1,                      f"{race}: HP >= 1 ({ai_w.max_hp})")

# ---------------------------------------------------------------------------
print("\n[ Injury system ]")
w = create_warrior_ai()
check(not w.injuries.is_fatal(), "Fresh warrior: not fatal")
w.injuries.add("chest", 5)
check(w.injuries.get("chest") == 5, "Added 5 chest injury levels")
check(not w.injuries.is_fatal(), "Level 5 injury: not fatal")
killed = w.injuries.add("chest", 4)   # Takes it to 9
check(killed, "Adding 4 more to level-5 injury → fatal")
check(w.injuries.is_fatal(), "is_fatal() → True after level 9")

# ---------------------------------------------------------------------------
print("\n[ Serialization ]")
original = create_warrior_ai(race_name="Dwarf", name="TestSave")
original.wins  = 5
original.losses= 2
original.armor = "Chain"
original.injuries.add("primary_arm", 3)

import json
data      = original.to_dict()
json_str  = json.dumps(data)
restored  = Warrior.from_dict(json.loads(json_str))

check(restored.name     == original.name,     "Name survived serialization")
check(restored.race.name== original.race.name,"Race survived serialization")
check(restored.wins     == original.wins,     "Wins survived serialization")
check(restored.armor    == original.armor,    "Armor survived serialization")
check(
    restored.injuries.get("primary_arm") == original.injuries.get("primary_arm"),
    "Injury levels survived serialization"
)
check(restored.max_hp   == original.max_hp,   "Max HP recalculated correctly after load")

# ---------------------------------------------------------------------------
print("\n[ Sample stat block ]")
sample = Warrior(
    name         = "Burly Bob",
    race_name    = "Half-Orc",
    gender       = "Male",
    strength     = 17,
    dexterity    = 9,
    constitution = 14,
    intelligence = 9,
    presence     = 8,
    size         = 14,
)
sample.wins   = 24
sample.losses = 27
print()
print(sample.stat_block())

# ---------------------------------------------------------------------------
print("\n========================================")
if errors == 0:
    print(f"  ALL TESTS PASSED")
else:
    print(f"  {errors} TEST(S) FAILED")
print("========================================\n")
