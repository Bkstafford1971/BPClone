#!/usr/bin/env python3
# =============================================================================
# test_milestone4.py — Tests for ai.py, matchmaking.py, and a full auto-turn
# Run: python test_milestone4.py
# =============================================================================

import sys, os, shutil, json, random
sys.path.insert(0, ".")

# Patch save dirs to avoid polluting real saves
import save as save_module
TEST_SAVES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves", "_test_m4")
TEST_TEAMS  = os.path.join(TEST_SAVES, "teams")
TEST_FIGHTS = os.path.join(TEST_SAVES, "fights")
TEST_GS     = os.path.join(TEST_SAVES, "game_state.json")
os.makedirs(TEST_TEAMS,  exist_ok=True)
os.makedirs(TEST_FIGHTS, exist_ok=True)

_orig_teams  = save_module.TEAMS_DIR
_orig_fights = save_module.FIGHTS_DIR
_orig_gs     = save_module.GAME_STATE_FILE
save_module.TEAMS_DIR        = TEST_TEAMS
save_module.FIGHTS_DIR       = TEST_FIGHTS
save_module.GAME_STATE_FILE  = TEST_GS

# Also patch the rivals file
import ai as ai_module
ORIG_RIVALS_FILE = ai_module.RIVALS_FILE
TEST_RIVALS_FILE = os.path.join(TEST_SAVES, "rivals.json")
ai_module.RIVALS_FILE = TEST_RIVALS_FILE

from warrior      import Warrior, Strategy, create_warrior_ai
from team         import Team, TEAM_SIZE
from ai           import (
    RivalManager, get_or_create_rivals, save_rivals, load_rivals,
    assign_ai_gear, assign_ai_strategies, assign_ai_training,
    rival_summary, INITIAL_POOL_SIZE,
    _generate_warrior_name, _generate_manager_name, _generate_team_name,
)
from matchmaking  import (
    build_fight_card, run_turn, turn_summary,
    ScheduledFight, _warrior_rating,
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


print("\n=============================================")
print("  BLOOD PIT — MILESTONE 4 TESTS")
print("=============================================\n")

# ===========================================================================
print("[ ai.py — name generators ]")
mname = _generate_manager_name()
check(len(mname) > 0,          f"Manager name generated: '{mname}'")
tname = _generate_team_name()
check(len(tname) > 0,          f"Team name generated: '{tname}'")
wname = _generate_warrior_name()
check(len(wname) > 0,          f"Warrior name generated: '{wname}'")

# ===========================================================================
print("\n[ ai.py — gear assignment ]")
for race in ["Human","Half-Orc","Halfling","Dwarf","Half-Elf","Elf"]:
    w = create_warrior_ai(race_name=race)
    assign_ai_gear(w, tier=1)
    check(w.primary_weapon != "",    f"{race} tier-1: has primary weapon ({w.primary_weapon})")
    check(w.armor is not None,       f"{race} tier-1: has armor ({w.armor})")

    assign_ai_gear(w, tier=5)
    check(w.armor is not None,       f"{race} tier-5: has armor ({w.armor})")

# ===========================================================================
print("\n[ ai.py — strategy assignment ]")
for tier in range(1, 6):
    w = create_warrior_ai()
    assign_ai_strategies(w, tier=tier)
    check(len(w.strategies) >= 1,              f"Tier {tier}: at least 1 strategy")
    check(len(w.strategies) <= 6,              f"Tier {tier}: at most 6 strategies")
    check(w.strategies[-1].trigger == "Always",f"Tier {tier}: last strategy is Always")

# ===========================================================================
print("\n[ ai.py — RivalManager creation ]")
rm1 = RivalManager("Iron Warlord", "The Iron Fists", tier=1, manager_id=1)
check(len(rm1.team.warriors) == TEAM_SIZE,     "Rival team has 5 warriors")
check(rm1.tier == 1,                           "Tier set correctly")
check(rm1.fights_completed == 0,               "Starts at 0 fights")
check(all(w.strategies for w in rm1.team.active_warriors),
      "All rival warriors have strategies")
check(all(w.armor is not None for w in rm1.team.active_warriors),
      "All rival warriors have armor")

rm5 = RivalManager("The Grand Champion", "The Titans", tier=5, manager_id=2)
check(rm5.tier == 5, "Tier-5 rival created")
# Tier-5 warriors should have higher average stats
avg5 = sum(w.max_hp for w in rm5.team.active_warriors) / TEAM_SIZE
avg1 = sum(w.max_hp for w in rm1.team.active_warriors) / TEAM_SIZE
check(avg5 >= avg1, f"Tier-5 avg HP ({avg5:.0f}) >= Tier-1 ({avg1:.0f})")

# ===========================================================================
print("\n[ ai.py — post-fight update / training ]")
rm = RivalManager("Test Manager", "Test Team", tier=1, manager_id=3)
w0 = rm.team.warriors[0]
old_fights = rm.fights_completed
rm.post_fight_update()
check(rm.fights_completed == old_fights + 1, "fights_completed incremented")

# ===========================================================================
print("\n[ ai.py — rival pool save / load ]")
pool = [RivalManager(f"Mgr{i}", f"Team{i}", tier=1, manager_id=i+10) for i in range(3)]
save_rivals(pool)
check(os.path.exists(TEST_RIVALS_FILE), "rivals.json created")
loaded_pool = load_rivals()
check(len(loaded_pool) == 3,             "All 3 rivals loaded back")
check(loaded_pool[0].manager_name == "Mgr0", "First rival name preserved")

# get_or_create_rivals fills to INITIAL_POOL_SIZE
full_pool = get_or_create_rivals()
check(len(full_pool) >= INITIAL_POOL_SIZE, f"Pool filled to {INITIAL_POOL_SIZE} rivals")

# ===========================================================================
print("\n[ matchmaking.py — warrior rating ]")
weak  = create_warrior_ai()
weak.strength = 5; weak.dexterity = 5; weak.constitution = 5
strong= create_warrior_ai()
strong.strength = 18; strong.dexterity = 18; strong.constitution = 18
strong.total_fights = 50
check(_warrior_rating(strong) > _warrior_rating(weak),
      f"Strong warrior rates higher: {_warrior_rating(strong):.1f} > {_warrior_rating(weak):.1f}")

# ===========================================================================
print("\n[ matchmaking.py — build_fight_card ]")

# Create a simple player team
player_team = Team("Test Heroes", "Test Manager", team_id=999)
for i in range(TEAM_SIZE):
    w = create_warrior_ai()
    assign_ai_gear(w, tier=1)
    assign_ai_strategies(w, tier=1)
    assign_ai_training(w, tier=1)
    player_team.add_warrior(w)

rivals = get_or_create_rivals()
card   = build_fight_card(player_team, rivals)

check(len(card) == TEAM_SIZE,    f"Fight card has {TEAM_SIZE} bouts ({len(card)})")
check(all(b.player_warrior is not None for b in card), "All bouts have a player warrior")
check(all(b.opponent is not None for b in card),       "All bouts have an opponent")

# All player warriors should be unique per bout
pw_names = [b.player_warrior.name for b in card]
check(len(set(pw_names)) == len(pw_names), "No player warrior appears twice in the card")

# All fight types should be valid
valid_types = {"challenge", "rivalry", "peasant", "blood_challenge"}
check(all(b.fight_type in valid_types for b in card),  "All fight types are valid")

# With 8+ rivals and 5 player warriors, some should be rivalry matches
rivalry_bouts = [b for b in card if b.fight_type == "rivalry"]
check(len(rivalry_bouts) >= 1, f"At least 1 rivalry bout ({len(rivalry_bouts)})")

# ===========================================================================
print("\n[ Full automated turn — 5 fights end to end ]")

# Set random seed for reproducibility
random.seed(42)

# Build a fresh test team
auto_team = Team("Gladiators Eternal", "The Pit Master", team_id=998)
races = ["Human","Half-Orc","Halfling","Dwarf","Elf"]
for i, race in enumerate(races):
    w = create_warrior_ai(race_name=race)
    assign_ai_gear(w, tier=2)
    assign_ai_strategies(w, tier=2)
    w.trains = ["dodge", "constitution", w.primary_weapon.lower().replace(" ","_")]
    auto_team.add_warrior(w)

auto_rivals = get_or_create_rivals()

print(f"\n  Team: {auto_team.team_name}")
print(f"  Warriors: {', '.join(w.name for w in auto_team.active_warriors)}")
print(f"  Rivals: {len(auto_rivals)} managers in pool\n")

card = run_turn(auto_team, auto_rivals, verbose=False)

check(len(card) == TEAM_SIZE, f"All {TEAM_SIZE} warriors fought")
check(all(b.result is not None for b in card), "All bouts have results")

wins   = sum(1 for b in card if b.result and b.result.winner is b.player_warrior)
losses = sum(1 for b in card if b.result and b.result.winner is not b.player_warrior and b.result.winner)
draws  = sum(1 for b in card if b.result and b.result.winner is None)
check(wins + losses + draws == TEAM_SIZE, f"Win/loss/draw accounts for all bouts ({wins}W/{losses}L/{draws}D)")

# Check fight logs were written
from save import list_fight_logs
logs = list_fight_logs()
check(len(logs) >= TEAM_SIZE, f"Fight logs written: {len(logs)}")

# Print turn summary
print(turn_summary(card, auto_team.team_name))

# ===========================================================================
print("\n[ Serialization — rival survives save/load after turn ]")
save_rivals(auto_rivals)
reloaded = load_rivals()
check(len(reloaded) >= INITIAL_POOL_SIZE, "Rival pool reloads correctly after turn")
changed = [r for r in reloaded if r.fights_completed > 0]
check(len(changed) >= 1, f"At least 1 rival shows fights_completed > 0 ({len(changed)})")

# ===========================================================================
# Cleanup
shutil.rmtree(TEST_SAVES, ignore_errors=True)
save_module.TEAMS_DIR       = _orig_teams
save_module.FIGHTS_DIR      = _orig_fights
save_module.GAME_STATE_FILE = _orig_gs
ai_module.RIVALS_FILE       = ORIG_RIVALS_FILE

print("\n=============================================")
if errors == 0:
    print("  ALL TESTS PASSED")
else:
    print(f"  {errors} TEST(S) FAILED")
print("=============================================\n")
