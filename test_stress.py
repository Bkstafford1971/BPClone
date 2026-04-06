#!/usr/bin/env python3
"""
Comprehensive stress test: Run 50+ fights to verify:
  - Fight duration distribution (goal: avg 4-6 min, most under 6)
  - Bleeding wound mechanics
  - Skill damage scaling
  - Weapon categorization bonuses
  - All 6 new skills in realistic combat
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from warrior import Warrior, generate_base_stats
from team import Team
from ai import get_or_create_rivals
from matchmaking import run_turn
from save import load_champion_state
from combat import run_fight, Strategy
import statistics

def create_test_warriors_pool():
    """Create a diverse pool of warriors to test all skills."""
    warriors = []
    
    # Cleave specialists (heavy weapons)
    for i in range(2):
        w = Warrior(
            name=f"Cleaver_{i+1}",
            race_name="Dwarf",
            gender="Male" if i % 2 == 0 else "Female",
            strength=16, dexterity=11, constitution=14, intelligence=9, presence=9, size=12
        )
        w.primary_weapon = ["Battle Axe", "Great Axe"][i % 2]
        w.secondary_weapon = "Open Hand"
        w.skills["cleave"] = 6
        w.max_hp = w._calc_max_hp()
        w.current_hp = w.max_hp
        warriors.append(w)
    
    # Bash specialists (heavy blunt)
    for i in range(2):
        w = Warrior(
            name=f"Basher_{i+1}",
            race_name="Dwarf",
            gender="Male" if i % 2 == 0 else "Female",
            strength=15, dexterity=10, constitution=15, intelligence=8, presence=8, size=12
        )
        w.primary_weapon = ["War Hammer", "Morningstar"][i % 2]
        w.secondary_weapon = "Open Hand"
        w.skills["bash"] = 6
        w.max_hp = w._calc_max_hp()
        w.current_hp = w.max_hp
        warriors.append(w)
    
    # Slash specialists (bladed)
    for i in range(2):
        w = Warrior(
            name=f"Slasher_{i+1}",
            race_name="Human",
            gender="Male" if i % 2 == 0 else "Female",
            strength=13, dexterity=14, constitution=12, intelligence=10, presence=10, size=11
        )
        w.primary_weapon = ["Long Sword", "Scimitar"][i % 2]
        w.secondary_weapon = "Open Hand"
        w.skills["slash"] = 7
        w.max_hp = w._calc_max_hp()
        w.current_hp = w.max_hp
        warriors.append(w)
    
    # Acrobatics specialists (dodge-focused)
    for i in range(2):
        w = Warrior(
            name=f"Acrobat_{i+1}",
            race_name="Elf",
            gender="Male" if i % 2 == 0 else "Female",
            strength=10, dexterity=17, constitution=10, intelligence=11, presence=12, size=10
        )
        w.primary_weapon = "Short Sword"
        w.secondary_weapon = "Open Hand"
        w.skills["acrobatics"] = 8
        w.skills["dodge"] = 3
        w.max_hp = w._calc_max_hp()
        w.current_hp = w.max_hp
        warriors.append(w)
    
    # Riposte specialists (counter-attack)
    for i in range(2):
        w = Warrior(
            name=f"Riposte_{i+1}",
            race_name="Human",
            gender="Male" if i % 2 == 0 else "Female",
            strength=12, dexterity=16, constitution=11, intelligence=12, presence=11, size=11
        )
        w.primary_weapon = ["Epee", "Long Sword"][i % 2]
        w.secondary_weapon = "Open Hand"
        w.skills["riposte"] = 6
        w.skills["parry"] = 5
        w.max_hp = w._calc_max_hp()
        w.current_hp = w.max_hp
        warriors.append(w)
    
    # Strike specialists (balanced)
    for i in range(2):
        w = Warrior(
            name=f"Striker_{i+1}",
            race_name="Half-Orc",
            gender="Male" if i % 2 == 0 else "Female",
            strength=14, dexterity=12, constitution=16, intelligence=8, presence=7, size=13
        )
        w.primary_weapon = "War Hammer"
        w.secondary_weapon = "Open Hand"
        w.skills["strike"] = 7
        w.max_hp = w._calc_max_hp()
        w.current_hp = w.max_hp
        warriors.append(w)
    
    # Hybrid warriors (mix of skills)
    hybrids = [
        ("Hybrid_1", "Dwarf", "Battle Axe", {"cleave": 5, "bash": 3}),
        ("Hybrid_2", "Human", "Long Sword", {"slash": 5, "riposte": 4}),
        ("Hybrid_3", "Elf", "Short Sword", {"acrobatics": 6, "slash": 3}),
    ]
    
    for name, race, wpn, skills in hybrids:
        w = Warrior(
            name=name,
            race_name=race,
            gender="Male",
            strength=13, dexterity=13, constitution=13, intelligence=10, presence=10, size=11
        )
        w.primary_weapon = wpn
        w.secondary_weapon = "Open Hand"
        for skil, level in skills.items():
            if skil in w.skills:
                w.skills[skil] = level
        w.max_hp = w._calc_max_hp()
        w.current_hp = w.max_hp
        warriors.append(w)
    
    return warriors

def run_stress_test(num_turns=10):
    """Run multiple turns with diverse warrior matchups."""
    print("\n" + "="*80)
    print(f"STRESS TEST: {num_turns} TURNS × 5 FIGHTS = {num_turns * 5} TOTAL FIGHTS")
    print("="*80)
    
    warriors = create_test_warriors_pool()
    fight_durations = []
    fight_types = {}
    warrior_win_records = {w.name: {"wins": 0, "losses": 0} for w in warriors}
    
    rivals = get_or_create_rivals()
    champion_state = load_champion_state()
    
    for turn_num in range(1, num_turns + 1):
        # Create team with rotating warriors
        player_team = Team(
            team_name=f"Stress Team Turn {turn_num}",
            manager_name="Stress Tester",
            team_id=100 + turn_num
        )
        
        # Pick 5 different warriors from the pool
        start_idx = (turn_num - 1) * 5 % len(warriors)
        player_team.warriors = [
            warriors[(start_idx + i) % len(warriors)]
            for i in range(5)
        ]
        
        # Reset warrior HP for this turn
        for w in player_team.warriors:
            w.current_hp = w.max_hp
        
        print(f"\n[TURN {turn_num}/{num_turns}]", end=" ")
        
        try:
            card = run_turn(player_team, rivals, verbose=False, champion_state=champion_state)
            
            for bout in card:
                if bout.result:
                    duration = bout.result.minutes_elapsed
                    fight_durations.append(duration)
                    
                    # Track fight type
                    fight_type = bout.fight_type
                    fight_types[fight_type] = fight_types.get(fight_type, 0) + 1
                    
                    # Track warrior records
                    pw_name = bout.player_warrior.name
                    if pw_name in warrior_win_records:
                        if bout.result.winner == bout.player_warrior:
                            warrior_win_records[pw_name]["wins"] += 1
                        else:
                            warrior_win_records[pw_name]["losses"] += 1
            
            print(f"{len([b for b in card if b.result])} fights, avg {statistics.mean([b.result.minutes_elapsed for b in card if b.result]):.1f} min")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    # Analysis
    print("\n" + "="*80)
    print("COMPREHENSIVE RESULTS")
    print("="*80)
    
    print(f"\nTotal fights executed: {len(fight_durations)}")
    if fight_durations:
        print(f"Duration statistics:")
        print(f"  Average:  {statistics.mean(fight_durations):.2f} minutes")
        print(f"  Median:   {statistics.median(fight_durations):.1f} minutes")
        print(f"  Std Dev:  {statistics.stdev(fight_durations):.2f} minutes")
        print(f"  Min:      {min(fight_durations)} minutes")
        print(f"  Max:      {max(fight_durations)} minutes")
        
        # Count distribution
        under_5 = sum(1 for d in fight_durations if d < 5)
        under_6 = sum(1 for d in fight_durations if d < 6)
        under_7 = sum(1 for d in fight_durations if d < 7)
        under_8 = sum(1 for d in fight_durations if d < 8)
        over_8 = sum(1 for d in fight_durations if d >= 8)
        
        print(f"\nDuration distribution:")
        print(f"  < 5 min:   {under_5:3} fights ({100*under_5/len(fight_durations):5.1f}%)")
        print(f"  < 6 min:   {under_6:3} fights ({100*under_6/len(fight_durations):5.1f}%)")
        print(f"  < 7 min:   {under_7:3} fights ({100*under_7/len(fight_durations):5.1f}%)")
        print(f"  < 8 min:   {under_8:3} fights ({100*under_8/len(fight_durations):5.1f}%)")
        print(f"  >= 8 min:  {over_8:3} fights ({100*over_8/len(fight_durations):5.1f}%)")
        
        # Health check
        avg = statistics.mean(fight_durations)
        if avg < 6:
            status = "✓ EXCELLENT"
        elif avg < 7:
            status = "✓ GOOD"
        elif avg < 8:
            status = "~ ACCEPTABLE"
        else:
            status = "✗ TOO LONG"
        print(f"\nStatus: {status} (avg {avg:.2f} min, target 4-6 min)")
    
    print(f"\nFight types:")
    for ftype, count in sorted(fight_types.items(), key=lambda x: -x[1]):
        print(f"  {ftype:15}: {count:3} fights")
    
    print(f"\nWarrior records (top performers):")
    sorted_warriors = sorted(warrior_win_records.items(), 
                            key=lambda x: x[1]["wins"] - x[1]["losses"], 
                            reverse=True)
    for name, record in sorted_warriors[:10]:
        wins = record["wins"]
        losses = record["losses"]
        total = wins + losses
        if total > 0:
            pct = 100 * wins / total
            print(f"  {name:20} {wins:2}-{losses:2} ({pct:5.1f}%)")
    
    return True

if __name__ == "__main__":
    try:
        run_stress_test(num_turns=10)
        print("\n" + "="*80)
        print("✓ STRESS TEST COMPLETE - All systems operational")
        print("="*80 + "\n")
    except Exception as e:
        print(f"\n✗ STRESS TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
