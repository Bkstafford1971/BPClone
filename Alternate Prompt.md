### Confirmation and immediate next step

Great — I’ll proceed. Below is the **full Game Design Document (GDD)** in implementation‑ready form (concise but complete), followed by the **first LLM prompt package** to implement the **Attribute & Derived Stat Library** (pure functions + unit tests + deterministic examples). I’ll start producing code from that prompt set as soon as you tell me to proceed.

> **Two lines from the original guide included verbatim:**  
> **“Blood Pit is a game of gladiatorial combat that is set in a fantasy world.”**  
> **“Blood Pit is a game of pure strategy and skill, where you will use your intellect and knowledge of tactics to outwit your opponents.”**

---

### Game Design Document Canonical Summary

#### Core design goals
- **Text‑based, turn‑based** gladiatorial combat where managers control teams of five warriors.  
- **Weekly turns**: managers upload strategy files; server matches, resolves fights, and returns blow‑by‑blow English narratives.  
- **Strategy over reflexes**: outcomes depend on attributes, skills, equipment, and strategy triggers.

#### Primary systems
- **Account & Manager** — create managers, teams (1–5 teams per manager), authentication, name moderation.  
- **Team & Warrior** — persistent warrior records; automatic replacement of dead warriors with beginners to keep teams at five.  
- **Turn Processor** — accepts uploads, queues matches, runs matches with deterministic RNG seed, stores results.  
- **Matchmaking** — supports duels, team fights, direct challenges, NPC assignment (Peasants, Monsters); Presence influences matching.  
- **Combat Engine** — attribute math, action economy, hit resolution, damage/armor, permanent injuries, special mechanics (surrender, scare).  
- **Narrative Generator** — event → templated English sentences with intensity tiers and synonyms.  
- **Admin Tools (Keeper)** — configure races, weapons, armor, edit records, run manual matches.  
- **Telemetry & Balancing** — per‑match logs, replay via stored seeds, analytics dashboards.

---

### Mechanics and Rules (Canonical Formulas and Tables)

#### Attributes and derived stats
- **Primary attributes**: **STR, DEX, CON, INT, PRES, SIZE**.  
- **HP formula (canonical)**:  
  \[
  \textbf{HP} = \min\big(100,\; 2\cdot\text{SIZE} + 1.5\cdot\text{CON} + 0.5\cdot\text{STR}\big)
  \]
- **Stat comparison rule**: values within **2** are equal; difference **≥3** gives advantage.

#### Action economy
- **APM (actions per minute)** baseline (tunable):  
  \[
  \text{APM} = \max\big(1,\; \lfloor 0.6\cdot\text{DEX} + 0.4\cdot\text{INT} - \text{ArmorPenalty} + \text{ActivityBonus}\rfloor\big)
  \]
- **ArmorPenalty**: derived from armor weight class; heavy armor reduces APM more.

#### Hit resolution and damage
- **Per action flow**: compute base hit chance → apply aiming modifiers → apply dodge/parry/style modifiers → RNG roll → on hit compute damage.  
- **Damage** = weapon_base + STR_modifier + SIZE_modifier − armor_effective.  
- **Armor penetration**: some weapons bypass a percentage of armor rating.

#### Permanent injuries
- **Body parts tracked**: head, chest, primary arm, off arm, primary leg, off leg.  
- **Perm levels**: 0–9 (9 = fatal). Each damaging hit has a chance to increase perm level based on damage severity and weapon type. Perms reduce related stats (e.g., leg perm reduces APM).

#### Special mechanics
- **Surrender**: frequency and success scale with **Presence**; approximate success factor \( \propto 23 + \frac{\text{PRES}}{1.5} \) percent in favorable contexts.  
- **Scare/Unnerve**: chance when opportunity arises roughly proportional to \( \big(\frac{\text{PRES} - \text{OppPRES}}{4}\big)^2\% \).  
- **Monsters**: extremely dangerous NPC fights; **Peasants**: scaled opponents to fill match slots.

---

### Races, Bonuses, and Preferred Weapons (Concise)

| **Race** | **Key bonuses** | **Preferred weapons** | **Notes** |
|---|---:|---|---|
| **Dwarf** | +Parry; +HP; +damage; +shield bonus; −attack rate, −dodge | Axes, war hammers, spears | Highest HP; heavy hitters |
| **Elf** | +Dodge; +dual‑weapon bonus; +attack rate; −HP | Small fast blades; thrown weapons | Finesse, speed |
| **Half‑Orc** | +Damage; +HP; −attack rate; −dodge/parry | Big bashing weapons | High raw damage |
| **Halfling** | +Dodge; +APM; +martial combat; −damage | Small light weapons | Extremely agile |
| **Human** | Balanced; trains stats better; fewer perms | None special | Versatile |
| **Half‑Elf** | Slight bonus with larger blades; thrown weapons | Swords, thrown | Hybrid traits |

*(Weapon/armor tables below are data‑driven and should be stored as JSON/YAML for easy tuning.)*

#### Example weapon table (fields)
- **id**, **name**, **type** (slash/pierce/blunt/pole), **min_STR**, **base_damage**, **armor_penetration**, **speed_modifier**, **two_handed_flag**, **special_flags** (throwable, shield_pierce).

#### Example armor table (fields)
- **id**, **name**, **armor_rating**, **weight_class** (light/medium/heavy), **dex_penalty**, **coverage** (head/chest/limbs), **special_flags**.

---

### Skills and Strategy System

**Skill categories** (examples to implement initially)
- **Combat**: Parry, Dodge, Aim, Lunge, Bash, Riposte.  
- **Weapon**: Swordsmanship, Axemanship, Polearms, Thrown Weapons, Flail.  
- **Tactical**: Feint, Charge, Hold Ground, Rally.  
- **Training mechanics**: per‑turn trains limited by caps; Intelligence speeds skill gain.

**Strategy sheet components**
- **Triggers**: minute, taken_damage, opponent_state, opponent_weapon, random, etc.  
- **Activity levels**: passive, cautious, normal, aggressive, berserk.  
- **Fighting styles**: slash, bash, lunge, wall_of_steel, total_kill, feint, dodge_focus.  
- **Aiming points**: head, chest, weapon_arm, leg, throat.  
- **Defense points**: head, chest, weapon_arm, legs.

---

### Data Schemas and Strategy Upload Format

**Strategy upload JSON** (canonical example shown earlier). Server validation rules:
- ≤6 strategies per warrior; priorities unique.  
- Trains within per‑turn caps; no more than +7 to one attribute at roll‑up.  
- Equipment meets minimums.

**Match record**
- Store **seed**, **participants**, **minute_logs** (structured events), **narrative_text**, **final_states** for replay.

---

### Narrative Generation Rules

- Combat engine emits **structured events** (attack_attempt, hit, parry, perm_injury, bleed, surrender_attempt, crowd_reaction).  
- Templating layer maps events to **multiple templates** per event type with intensity tiers (minor, solid, severe, catastrophic).  
- Keep a **synonym pool** for verbs and descriptors to avoid repetition.  
- Store narrative templates as data files for localization and tuning.

---

### LLM Prompt Package for Attribute and Derived Stat Library

**Goal:** produce a self‑contained module implementing attribute math and derived stat functions with unit tests and deterministic RNG usage where needed.

**Deliverables expected from the LLM**
1. **Code file** (Python 3.11) implementing:
   - `compute_hp(attrs: dict) -> int`
   - `compare_stats(a: int, b: int) -> Literal['equal','adv_a','adv_b']`
   - `compute_apm(dex: int, intel: int, armor_penalty: float, activity: str) -> int`
   - `stat_advantage_effects(attacker: dict, defender: dict) -> dict` (returns numeric modifiers for dodge/aim/parry)
2. **Unit tests** (pytest) covering normal and edge cases (deterministic).  
3. **Docstrings and type hints**.  
4. **A short README** block at top explaining tuning constants and where to change them.

**Prompt to give the LLM** (copy‑paste ready)
```
Title: Implement Attribute and Derived Stat Library

Spec:
- Implement a Python module `attributes.py` with the following functions:
  1. compute_hp(attrs: dict) -> int
     - attrs contains keys 'STR','DEX','CON','INT','PRES','SIZE' (ints).
     - Use canonical formula: HP = min(100, floor(2*SIZE + 1.5*CON + 0.5*STR))
     - Return integer HP.
  2. compare_stats(a: int, b: int) -> str
     - Return 'equal' if |a-b| <= 2, 'adv_a' if a-b >= 3, 'adv_b' if b-a >= 3.
  3. compute_apm(dex: int, intel: int, armor_penalty: float, activity: str) -> int
     - activity in {'passive','cautious','normal','aggressive','berserk'}.
     - Use formula: floor(0.6*dex + 0.4*intel - armor_penalty + activity_bonus)
     - activity_bonus mapping: passive= -1, cautious= -0.5, normal=0, aggressive= +0.5, berserk= +1
     - Ensure minimum APM = 1.
  4. stat_advantage_effects(attacker: dict, defender: dict) -> dict
     - attacker/defender have 'STR','DEX','CON','INT','PRES','SIZE'.
     - Return dict with numeric modifiers: {'dodge_pct':float,'aim_pct':float,'parry_pct':float}
     - Rules: if DEX diff >=3, attacker gets + (DEX_diff * 1.5)% aim and + (DEX_diff * 1.0)% dodge.
              if STR diff >=3, attacker gets + (STR_diff * 1.2)% parry and + (STR_diff * 0.8)% damage (damage not implemented here).
              PRES differences do not affect these three modifiers.
- Include constants at top for tuning (e.g., DEX_AIM_MULTIPLIER = 1.5).
- Use only standard library.

Tests:
- Provide pytest tests in `test_attributes.py` with at least 6 tests:
  1. HP formula edge cases (cap at 100).
  2. compare_stats returns 'equal' for diff 2 and 'adv_a' for diff 3.
  3. compute_apm returns >=1 and respects activity bonuses and armor penalty.
  4. stat_advantage_effects returns expected numeric modifiers for DEX and STR diffs.
  5. deterministic example: compute_hp and compute_apm for sample warrior.
  6. negative armor_penalty handled.

Style:
- Python 3.11, type hints, docstrings, small README header comment describing tuning constants.
- Return only code and tests in a single file or a zipped structure representation.

Determinism:
- No RNG required for these functions; tests must be deterministic.

Acceptance criteria:
- All tests pass under pytest.
- Functions are pure and side‑effect free.
```

**Example unit test cases to include** (the LLM should implement these)
- `compute_hp({'STR':10,'DEX':10,'CON':10,'INT':10,'PRES':10,'SIZE':12}) == floor(min(100, 2*12 + 1.5*10 + 0.5*10))`
- `compare_stats(10,12) == 'equal'` and `compare_stats(13,10) == 'adv_a'`
- `compute_apm(18,12,armor_penalty=2.0,'aggressive') >= 1`
- `stat_advantage_effects({'DEX':18,'STR':12,...},{'DEX':12,'STR':9,...})` yields dodge_pct > 0 and parry_pct > 0 per multipliers.

---

### Acceptance Criteria, Testing, and Next Steps

**Acceptance criteria for this milestone**
- The LLM produces `attributes.py` and `test_attributes.py`.  
- All tests pass in a clean environment (Python 3.11, pytest).  
- Code is documented and constants are clearly labeled for tuning.

**Next steps after attribute library**
1. Implement **Action Economy & Skill Math** module (LLM prompt ready).  
2. Implement **Combat Core** (deterministic `resolve_exchange` with seed).  
3. Implement **Style & Skill Handlers** and **Narrative Templating**.

**Timeline suggestion**
- **48 hours** to iterate on attribute module and tests until stable.  
- **1 week** to complete action economy and basic combat core prototype.

---

If you approve, I will:
- **(A)** Generate the `attributes.py` + `test_attributes.py` prompt output and then run the LLM to produce the code (I’ll deliver the code and tests for you to run), **or**  
- **(B)** Immediately ask the LLM to produce the code now and return the module and tests in the next message.

Which do you prefer — **A: I want to review the exact LLM prompt before it runs**, or **B: Run the prompt now and return the produced code and tests**?
