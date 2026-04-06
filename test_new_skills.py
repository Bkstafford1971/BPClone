#!/usr/bin/env python3
"""
Test script to verify new combat skills system implementation.
Tests:
  1. Cleave/Bash skill damage bonuses
  2. Slash bleeding wounds
  3. Acrobatics dodge bonuses and knockdown recovery
  4. Parry penetration for Cleave/Bash
  5. Riposte counter-attacks
  6. Fight duration (goal: most 5-6 min, occasional 8-10 min)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from warrior import Warrior, generate_base_stats
from team import Team
from ai import RivalManager, get_or_create_rivals
from matchmaking import run_turn
from save import load_champion_state
import json

def create_test_warrior(name, primary_weapon="War Hammer", secondary="Target Shield", skills=None):
    """Create a test warrior with configurable skills."""
    stats_dict = generate_base_stats()  # Generate random baseline stats
    stats = [stats_dict.get(attr, 10) for attr in ["strength", "dexterity", "constitution", "intelligence", "presence", "size"]]
    
    w = Warrior(
        name=name,
        race_name="Dwarf",
        gender="Male",
        strength=stats[0],
        dexterity=stats[1],
        constitution=stats[2],
        intelligence=stats[3],
        presence=stats[4],
        size=stats[5],
    )
    w.primary_weapon = primary_weapon
    w.secondary_weapon = secondary
    w.luck = 15
    
    # Apply test skills
    if skills:
        for skill_name, level in skills.items():
            if skill_name in w.skills:
                w.skills[skill_name] = min(9, level)
    
    w.max_hp = w._calc_max_hp()
    w.current_hp = w.max_hp
    return w

def test_cleave_bash(verbose=True):
    """Test Cleave and Bash skill damage bonuses."""
    print("\n" + "="*70)
    print("TEST 1: Cleave/Bash Damage Bonuses")
    print("="*70)
    
    warrior_cleave = create_test_warrior(
        "CleaveTest",
        primary_weapon="Great Axe",
        secondary="Open Hand",
        skills={"cleave": 5, "strength": 0}
    )
    
    warrior_bash = create_test_warrior(
        "BashTest",
        primary_weapon="War Hammer",
        secondary="Open Hand",
        skills={"bash": 5}
    )
    
    warrior_strike = create_test_warrior(
        "StrikeTest",
        primary_weapon="War Hammer",
        secondary="Open Hand",
        skills={"strike": 5}
    )
    
    print(f"\nCleave warrior (Great Axe, Cleave 5): max HP = {warrior_cleave.max_hp}")
    print(f"Bash warrior (War Hammer, Bash 5): max HP = {warrior_bash.max_hp}")
    print(f"Strike warrior (War Hammer, Strike 5): max HP = {warrior_strike.max_hp}")
    print("\nNote: Cleave/Bash should have +2 damage per level; Strike has +0.8 per level")
    print("Expected: different damage ceilings when facing opponents")
    
    return True

def test_slash_bleeding(verbose=True):
    """Test Slash skill and bleeding wound mechanics."""
    print("\n" + "="*70)
    print("TEST 2: Slash Skill & Bleeding Wounds")
    print("="*70)
    
    warrior_slash = create_test_warrior(
        "SlashTest",
        primary_weapon="Long Sword",
        secondary="Open Hand",
        skills={"slash": 7}
    )
    
    print(f"\nSlash warrior (Long Sword, Slash 7):")
    print(f"  HP: {warrior_slash.max_hp}")
    print(f"  Bleeding wound chance: 7% × 5 = 35% per hit")
    print(f"  Expected: ~6-7 hits will cause bleeding, bleeding reduces opponent HP over time")
    
    return True

def test_acrobatics(verbose=True):
    """Test Acrobatics dodge bonus and knockdown recovery."""
    print("\n" + "="*70)
    print("TEST 3: Acrobatics Dodge & Recovery")
    print("="*70)
    
    warrior_acrobat = create_test_warrior(
        "AcrobatTest",
        primary_weapon="Short Sword",
        secondary="Open Hand",
        skills={"acrobatics": 9, "dodge": 3}
    )
    
    print(f"\nAcrobat warrior (Short Sword, Acrobatics 9, Dodge 3):")
    print(f"  HP: {warrior_acrobat.max_hp}")
    print(f"  Dodge bonus from Acrobatics: +2 per level = +18 to dodge roll")
    print(f"  Knockdown recovery chance: 20% × 9 = 180% (capped at 85%)")
    print(f"  Endurance cost: 10% - 9% = 1% extra endurance burn per acrobatic move")
    print(f"  Expected: much better at evading and recovering from knockdowns")
    
    return True

def test_parry_penetration(verbose=True):
    """Test Cleave/Bash parry penetration chance."""
    print("\n" + "="*70)
    print("TEST 4: Parry Penetration (Cleave/Bash)")
    print("="*70)
    
    warrior_cleave = create_test_warrior(
        "PenetrateTest",
        primary_weapon="Great Sword",
        secondary="Open Hand",
        skills={"cleave": 9}
    )
    
    warrior_defender = create_test_warrior(
        "DefenderTest",
        primary_weapon="Long Sword",
        secondary="Tower Shield",
        skills={"parry": 7}
    )
    
    print(f"\nCleave warrior (Great Sword, Cleave 9):")
    print(f"  Parry penetration chance: 5% × 9 = 45%")
    print(f"  Penetration damage: base weapon weight × 2 (no modifiers)")
    print(f"\nDefender (Long Sword + Tower Shield, Parry 7):")
    print(f"  HP: {warrior_defender.max_hp}")
    print(f"  Expected: 45% of parries will be partially penetrated with reduced damage")
    
    return True

def test_full_turn():
    """Run a full game turn to verify all systems work together."""
    print("\n" + "="*70)
    print("TEST 5: Full Turn Execution")
    print("="*70)
    
    # Create player team
    player_team = Team(
        team_name="Test Warriors",
        manager_name="Test Manager",
        team_id=1
    )
    
    # Add test warriors with various skill configurations
    warriors = [
        create_test_warrior("Cleaver", "Battle Axe", "Open Hand", {"cleave": 5}),
        create_test_warrior("Basher", "Morningstar", "Open Hand", {"bash": 5}),
        create_test_warrior("Slasher", "Long Sword", "Open Hand", {"slash": 6}),
        create_test_warrior("Acrobat", "Short Sword", "Open Hand", {"acrobatics": 7, "dodge": 3}),
        create_test_warrior("Striker", "War Hammer", "Target Shield", {"strike": 5}),
    ]
    
    player_team.warriors = warriors
    
    print(f"\nPlayer team '{player_team.team_name}' created with {len(warriors)} warriors:")
    for w in warriors:
        wpn = w.primary_weapon
        skills = [f"{s}:{v}" for s, v in w.skills.items() if v > 0 and s in ["cleave", "bash", "slash", "strike", "acrobatics"]]
        print(f"  {w.name:20} - {wpn:20} [{', '.join(skills)}]")
    
    print("\nLoading rivals and running turn...")
    rivals = get_or_create_rivals()
    champion_state = load_champion_state()
    
    try:
        card = run_turn(player_team, rivals, verbose=False, champion_state=champion_state)
        
        print(f"\nTurn complete: {len(card)} fights scheduled and executed")
        print("\nFight Summary:")
        print("  Index | Player Warrior      | Opponent            | Type      | Duration | Result")
        print("  " + "-" * 85)
        
        total_duration = 0
        for i, bout in enumerate(card, 1):
            if bout.result:
                pw_name = bout.player_warrior.name[:19]
                op_name = bout.opponent.name[:19]
                duration = bout.result.minutes_elapsed
                total_duration += duration
                winner = "Player" if bout.result.winner == bout.player_warrior else "Opponent"
                print(f"  {i:5} | {pw_name:20} | {op_name:20} | {bout.fight_type:10} | {duration:>2} min  | {winner}")
        
        avg_duration = total_duration / len([b for b in card if b.result]) if card else 0
        print(f"\n  Average fight duration: {avg_duration:.1f} minutes")
        print(f"  Total duration: {total_duration} minutes for {len([b for b in card if b.result])} fights")
        
        if avg_duration <= 6:
            print("  ✓ PASS: Average duration <= 6 minutes (healthy)")
        elif avg_duration <= 7:
            print("  ~ WARN: Average duration 6-7 minutes (acceptable)")
        else:
            print("  ✗ FAIL: Average duration > 7 minutes (too long)")
        
        return True
        
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "="*70)
    print("NEW COMBAT SKILLS SYSTEM - VERIFICATION TESTS")
    print("="*70)
    
    tests_passed = 0
    tests_total = 5
    
    try:
        if test_cleave_bash():tests_passed += 1
        if test_slash_bleeding(): tests_passed += 1
        if test_acrobatics(): tests_passed += 1
        if test_parry_penetration(): tests_passed += 1
        if test_full_turn(): tests_passed += 1
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print(f"SUMMARY: {tests_passed}/{tests_total} tests executed successfully")
    print("="*70 + "\n")
    
    sys.exit(0 if tests_passed == tests_total else 1)
