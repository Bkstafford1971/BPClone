#!/usr/bin/env python3
# =============================================================================
# test_milestone2.py — Smoke tests for weapons, armor, team, and save modules
# Run: python test_milestone2.py
# =============================================================================

import sys, os, shutil
sys.path.insert(0, ".")

from weapons import (
    get_weapon, WEAPONS, max_weapon_weight, strength_penalty,
    throwable_weapons, mc_weapons, armor_piercing_weapons,
    list_weapons_by_category, SWORD_KNIFE, POLEARM_SPEAR, FLAIL,
)
from armor import (
    get_armor, can_wear_armor, effective_dex, total_defense_value,
    is_ap_vulnerable, ARMOR_TIERS, HELM_TIERS,
)
from team  import Team, create_ai_team, create_peasant_team, create_monster_team, TEAM_SIZE
from save  import (
    save_team, load_team, load_all_teams, delete_team, list_saved_teams,
    save_fight_log, load_fight_log, list_fight_logs, load_game_state,
    print_save_status, TEAMS_DIR, FIGHTS_DIR,
)

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

print("\n==============================================")
print("  BLOOD PIT — MILESTONE 2 SMOKE TESTS")
print("==============================================\n")

# =============================================================================
print("[ weapons.py — Count & lookup ]")
check(len(WEAPONS) == 44, f"Exactly 44 weapons defined ({len(WEAPONS)})")

for name in ["Boar Spear", "War Flail", "Short Sword", "Great Pick",
             "Open Hand", "Net", "Swordbreaker", "Ball & Chain"]:
    try:
        w = get_weapon(name)
        check(w.display == name, f"get_weapon('{name}') found: {w.display}")
    except ValueError as e:
        check(False, f"get_weapon('{name}') raised: {e}")

# skill_key lookup
w = get_weapon("war_flail")
check(w.display == "War Flail", "Lookup by skill_key 'war_flail' works")

# =============================================================================
print("\n[ weapons.py — Special flags ]")
ap_weapons = [w.display for w in armor_piercing_weapons()]
for expected in ["Stiletto", "Scythe", "Small Pick", "Military Pick", "Great Pick", "Pick Axe"]:
    check(expected in ap_weapons, f"AP weapon: {expected}")

mc_list = [w.display for w in mc_weapons()]
for expected in ["Stiletto", "Dagger", "Knife", "Quarterstaff", "Net", "Great Staff", "Open Hand", "Cestus"]:
    check(expected in mc_list, f"MC-compatible: {expected}")

throw_list = [w.display for w in throwable_weapons()]
for expected in ["Stiletto", "Knife", "Dagger", "Hatchet", "Fransisca", "Hammer", "Boar Spear", "Javelin"]:
    check(expected in throw_list, f"Throwable: {expected}")

spear_names = [w.display for w in list_weapons_by_category(POLEARM_SPEAR)]
check("Boar Spear" in spear_names, "Boar Spear is in Polearm/Spear category")

flail_list = list_weapons_by_category(FLAIL)
for w in flail_list:
    check(w.flail_bypass, f"Flail '{w.display}' has bypass flag set")

# =============================================================================
print("\n[ weapons.py — Strength penalties ]")
# STR 14-16 → carry 5.0. War Flail weighs 6.0 → over by 1.
pen = strength_penalty(6.0, strength=14, two_handed=False)
check(pen > 0, f"STR 14 carrying Wt 6.0 → penalty={pen:.2f}")
check(pen < 1, f"STR 14 carrying Wt 6.0 → not 100% useless (pen={pen:.2f})")

# STR 17-18 → carry 6.0. War Flail weighs 6.0 → no penalty.
pen_none = strength_penalty(6.0, strength=17, two_handed=False)
check(pen_none == 0.0, f"STR 17 carrying Wt 6.0 → no penalty (pen={pen_none})")

# Two-handed gives +1.0 to capacity
pen_2h = strength_penalty(6.5, strength=14, two_handed=True)
# STR14 cap = 5.0 + 1.0 (2H) = 6.0. 6.5 over by 0.5 → small penalty
check(0 < pen_2h < pen, f"Two-handed reduces penalty: {pen_2h:.2f} < {pen:.2f}")

# Full penalty capped at 1.0
pen_cap = strength_penalty(20.0, strength=3, two_handed=False)
check(pen_cap == 1.0, f"Ridiculous over-weight → penalty capped at 1.0 ({pen_cap})")

# max_weapon_weight sanity
check(max_weapon_weight(17) == 6.0, "STR 17 → max weapon weight 6.0")
check(max_weapon_weight(9)  == 3.0, "STR 9 → max weapon weight 3.0")
check(max_weapon_weight(3)  == 0.0, "STR 3 → max weapon weight 0.0")

# =============================================================================
print("\n[ armor.py — Lookup ]")
check(get_armor("Full Plate").weight == 80.0, "Full Plate weight = 80.0")
check(get_armor("Steel Cap").is_helm,          "Steel Cap is a helm")
check(not get_armor("Chain").is_helm,          "Chain is NOT a helm")
check(get_armor("None").defense_value == 0,    "No armor = 0 defense")
check(len(ARMOR_TIERS) == 8,                   "8 body armor tiers")
check(len(HELM_TIERS)  == 5,                   "5 helm tiers")

# =============================================================================
print("\n[ armor.py — can_wear_armor ]")
# STR 17 → max armor ~50 lbs (from ARMOR_STR_TABLE). Chain = 44 lbs → OK.
allowed, msg = can_wear_armor("Chain", strength=17, is_dwarf=False)
check(allowed, f"STR 17 can wear Chain: {msg}")

# STR 9 → max armor ~20 lbs. Brigandine = 24 lbs → NOT OK.
allowed2, msg2 = can_wear_armor("Brigandine", strength=9, is_dwarf=False)
check(not allowed2, f"STR 9 cannot wear Brigandine: {msg2}")

# Dwarf tier-up: STR 9 still can't wear Scale (35 lbs), but can wear Brigandine (24).
allowed3, msg3 = can_wear_armor("Brigandine", strength=9, is_dwarf=True)
check(allowed3, f"Dwarf STR 9 CAN wear Brigandine (tier-up): {msg3}")

# Dwarf cannot jump TWO tiers
allowed4, msg4 = can_wear_armor("Scale", strength=9, is_dwarf=True)
check(not allowed4, f"Dwarf STR 9 CANNOT wear Scale (too many tiers): {msg4}")

# =============================================================================
print("\n[ armor.py — Defense & DEX ]")
check(total_defense_value("Chain", "Helm") == 9,     "Chain+Helm = 6+3 = 9 defense")
check(total_defense_value("None",  "None") == 0,     "No gear = 0 defense")
check(effective_dex(15, "Full Plate", "Full Helm") == max(1, 15-5-2),
      f"DEX 15 with Full Plate+Full Helm = {effective_dex(15,'Full Plate','Full Helm')}")
check(effective_dex(10, "Cloth", "None") == 10,      "Cloth with no helm = no DEX penalty")
check(is_ap_vulnerable("Chain"),                     "Chain is AP vulnerable")
check(not is_ap_vulnerable("Leather"),               "Leather is NOT AP vulnerable")
check(not is_ap_vulnerable("Brigandine"),            "Brigandine is NOT AP vulnerable")

# =============================================================================
print("\n[ team.py — Creation & roster ]")
team = create_ai_team(team_name="Eternal Champions", manager_name="The Keeper")
check(len(team.warriors)    == TEAM_SIZE, f"Team has {TEAM_SIZE} warriors")
check(all(w is not None for w in team.warriors), "No None slots in new team")
check(len(team.active_warriors) == TEAM_SIZE,   "All warriors active on new team")
check(team.is_full,                              "team.is_full == True")

w0 = team.warriors[0]
found = team.warrior_by_name(w0.name)
check(found is w0,               f"warrior_by_name('{w0.name}') found correctly")
check(team.warrior_index(w0.name) == 0, "warrior_index returns 0 for first warrior")

# =============================================================================
print("\n[ team.py — Death & replacement ]")
victim = team.warriors[0]
replacement = team.kill_warrior(victim, killed_by="Test Killer", killer_fights=10)
check(replacement is not None,               "Replacement warrior created")
check(team.warriors[0] is replacement,        "Replacement placed in correct slot")
check(len(team.warriors) == TEAM_SIZE,        "Team still has 5 warriors after death")
check(len(team.fallen_warriors) == 1,         "Fallen warrior logged")
check(len(team.blood_challenges) >= 1,        "Blood challenge queued (killer has 5+ fights)")

# Death with killer < 5 fights — no blood challenge
team2  = create_ai_team()
victim2 = team2.warriors[0]
bc_before = len(team2.blood_challenges)
team2.kill_warrior(victim2, killed_by="Newbie", killer_fights=3)
check(len(team2.blood_challenges) == bc_before, "No BC for killer with <5 fights")

# =============================================================================
print("\n[ team.py — Peasant & Monster teams ]")
peas = create_peasant_team(target_fight_count=10)
check(peas.team_name == "The Peasants",    "Peasant team name correct")
check(len(peas.warriors) == TEAM_SIZE,     "Peasant team has 5 warriors")

mons = create_monster_team()
check(mons.team_name == "The Monsters",    "Monster team name correct")
check(mons.warriors[0].max_hp == 100,      "Monster HP capped at 100 (max stats)")

# =============================================================================
print("\n[ team.py — Serialization ]")
original_team = create_ai_team(team_name="Test Team", manager_name="Test Manager")
original_team.warriors[0].wins = 7
data    = original_team.to_dict()
restored= Team.from_dict(data)
check(restored.team_name    == original_team.team_name,    "team_name round-trips")
check(restored.manager_name == original_team.manager_name, "manager_name round-trips")
check(len(restored.warriors) == TEAM_SIZE,                 "warrior count round-trips")
check(restored.warriors[0].wins == 7,                      "warrior wins round-trip")

# =============================================================================
print("\n[ save.py — Team save/load/delete ]")

# Use a temporary test directory to avoid polluting real saves
TEST_TEAMS_DIR  = os.path.join(TEAMS_DIR,  "_test")
TEST_FIGHTS_DIR = os.path.join(FIGHTS_DIR, "_test")
import save as save_module  # grab reference for patching

os.makedirs(TEST_TEAMS_DIR,  exist_ok=True)
os.makedirs(TEST_FIGHTS_DIR, exist_ok=True)

# Monkey-patch dirs for testing only
_orig_teams_dir  = save_module.TEAMS_DIR
_orig_fights_dir = save_module.FIGHTS_DIR
save_module.TEAMS_DIR  = TEST_TEAMS_DIR
save_module.FIGHTS_DIR = TEST_FIGHTS_DIR

try:
    test_team = create_ai_team(team_name="Save Test Team", manager_name="Tester")
    test_team.team_id = 9999   # Fixed ID to avoid touching real game_state.json

    path = save_team(test_team)
    check(os.path.exists(path), f"save_team created file: {os.path.basename(path)}")

    loaded = load_team(9999)
    check(loaded.team_name    == test_team.team_name,    "load_team: team_name matches")
    check(loaded.manager_name == test_team.manager_name, "load_team: manager_name matches")
    check(len(loaded.warriors)== TEAM_SIZE,               "load_team: warrior count matches")

    summaries = list_saved_teams()
    check(any(s["team_id"] == 9999 for s in summaries), "list_saved_teams finds test team")

    deleted = delete_team(9999)
    check(deleted,                        "delete_team returned True")
    check(not os.path.exists(path),       "delete_team removed the file")
    check(delete_team(9999) == False,     "delete_team returns False for missing file")

    # Fight log save/load
    sample_log = "MINUTE 1\nGear Head slashes at Burly Bob!\nBurly Bob takes 12 damage!\n"
    log_path = save_fight_log(sample_log, "Team A", "Team B")
    check(os.path.exists(log_path), f"save_fight_log created: {os.path.basename(log_path)}")

    logs = list_fight_logs()
    check(len(logs) >= 1, f"list_fight_logs returns {len(logs)} entry(ies)")

    fight_id = logs[0]["fight_id"]
    loaded_log = load_fight_log(fight_id)
    check("MINUTE 1" in loaded_log, "load_fight_log content contains 'MINUTE 1'")

finally:
    # Restore original dirs and clean up test dirs
    save_module.TEAMS_DIR  = _orig_teams_dir
    save_module.FIGHTS_DIR = _orig_fights_dir
    shutil.rmtree(TEST_TEAMS_DIR,  ignore_errors=True)
    shutil.rmtree(TEST_FIGHTS_DIR, ignore_errors=True)

# =============================================================================
print("\n[ Integration — full team save→load roundtrip with real save dir ]")
real_team = create_ai_team(team_name="Integration Test", manager_name="Dev")
real_team.warriors[0].armor = "Chain"
real_team.warriors[0].helm  = "Helm"
real_team.warriors[0].primary_weapon = "War Flail"
real_team.warriors[0].injuries.add("chest", 2)

path2   = save_team(real_team)
real_id = real_team.team_id
loaded2 = load_team(real_id)

check(loaded2.warriors[0].armor == "Chain",               "Integration: armor preserved")
check(loaded2.warriors[0].primary_weapon == "War Flail",  "Integration: weapon preserved")
check(loaded2.warriors[0].injuries.get("chest") == 2,     "Integration: injury preserved")

# Cleanup
delete_team(real_id)
check(not os.path.exists(path2), "Integration: cleanup successful")

# =============================================================================
print("\n==============================================")
if errors == 0:
    print(f"  ALL TESTS PASSED")
else:
    print(f"  {errors} TEST(S) FAILED")
print("==============================================\n")
