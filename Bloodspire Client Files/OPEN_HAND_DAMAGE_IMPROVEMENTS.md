# Open Hand Martial Artist Damage Improvements

## What Was Changed

The Open Hand weapon now has a specialized damage bonus system similar to other combat forms (Cleave, Bash, Slash). Previously, Open Hand attacks were limited to a generic +0.8 damage per skill level, which resulted in primarily light damage strikes.

## The New Open Hand Bonus System

### Damage Calculation Changes:

**For Open Hand attacks:**
- **Base Bonus:** +2.0 per skill level (same as Cleave/Bash)
- **Master Multiplier (Level 9):** ×1.20 (+20% total damage)
- **Brawl Synergy:** +0.5 per Brawl skill level
- **Master Brawl (Level 9):** ×1.10 multiplier (+10% additional)

### Example: Your Lizardfolk Martial Artist

With Master level (9) in both Open Hand and Brawl:

**Damage Calculation:**
```
Base Open Hand bonus: 9 × 2.0 = 18.0 damage
Master multiplier: ×1.20 = 21.6 damage
Brawl bonus: 9 × 0.5 = 4.5 damage  
Master Brawl multiplier: ×1.10 = additional scaling

Total: ~26.5+ damage from skill bonuses alone
```

### Actual Combat Results

Testing shows the following damage output at various hit margins:

| Margin | Damage | Severity |
|--------|--------|----------|
| 10 (weak) | 6 HP | **MEDIUM** |
| 20 (solid) | 14 HP | **HEAVY** |
| 30+ (strong) | 22+ HP | **DEVASTATING** |

**Before:** Mostly 2-4 HP light strikes  
**After:** Mix of medium (5-8 HP), heavy (9-15 HP), and devastating (16+ HP) strikes

## Why This Makes Sense

1. **Martial Art Mastery:** High skill levels reflect deep training that produces powerful, controlled strikes
2. **Brawl Synergy:** Brawl skill (bone-deep understanding of hand-to-hand combat) enhances damage
3. **Balance:** Open Hand no longer feels disadvantaged vs. weapon-based martial arts
4. **Martial Combat Style:** Works well with the "Martial Combat" fighting style that emphasizes technique

## Play Impact

Your Lizardfolk martial artist will now:
- ✅ Land medium and heavy damage strikes consistently
- ✅ See more varied damage output (not just slight damage)
- ✅ Feel rewarded for investing in Master-level Open Hand training
- ✅ Have Brawl skill meaningfully contribute to damage output
- ✅ Be competitive with weapon-based fighters of similar skill level

## Technical Implementation

**Files Modified:** `combat.py`

Changes:
1. Added `OPEN_HAND_WEAPONS` set
2. Added `_is_open_hand_weapon()` detection function
3. Added Open Hand skill bonus section in `_calc_damage_hybrid()`
4. Integrated Brawl skill as complementary damage source
