package com.bloodspire.engine;

import com.bloodspire.model.*;
import com.bloodspire.narrative.NarrativeEngine;

import java.util.*;

/**
 * Complete combat engine implementing all fight mechanics from the Python version.
 * Handles initiative, attacks, defense, damage calculation, special mechanics,
 * wounds, knockdowns, and narrative generation.
 */
public class CombatEngine {
    
    // Combat constants
    private static final int KNOCKDOWN_STAMINA_COST = 15;
    private static final int KNOCKDOWN_INITIATIVE_PENALTY = -3;
    private static final int BLEED_DAMAGE_PER_TURN = 2;
    private static final int MAX_BLEED_STACKS = 3;
    
    private Random random;
    private NarrativeEngine narrativeEngine;
    
    public CombatEngine() {
        this.random = new Random();
        this.narrativeEngine = new NarrativeEngine();
    }
    
    public CombatEngine(long seed) {
        this.random = new Random(seed);
        this.narrativeEngine = new NarrativeEngine();
    }
    
    /**
     * Execute a complete fight between two warriors.
     * Returns a CombatResult with the outcome and narrative.
     */
    public CombatResult executeFight(Warrior warrior1, Warrior warrior2, boolean generateNarrative) {
        CombatState state = initializeCombat(warrior1, warrior2);
        List<String> narrative = new ArrayList<>();
        
        if (generateNarrative) {
            narrative.add(narrativeEngine.generateFightIntro(warrior1, warrior2));
        }
        
        int turnCount = 0;
        while (!state.isFinished && turnCount < 50) { // Safety limit
            turnCount++;
            CombatTurn turn = executeTurn(state);
            
            if (generateNarrative) {
                narrative.addAll(turn.narrative);
            }
            
            if (turn.knockout || turn.conceded || turn.fightEnded) {
                state.isFinished = true;
                state.winner = turn.winner;
                break;
            }
        }
        
        if (!state.isFinished) {
            // Time limit reached - judge decision
            state.winner = determineWinnerByStats(state);
            if (generateNarrative) {
                narrative.add(narrativeEngine.generateJudgeDecision(state.warrior1, state.warrior2, state.winner));
            }
        }
        
        return finalizeCombatResult(state, narrative);
    }
    
    private CombatState initializeCombat(Warrior w1, Warrior w2) {
        CombatState state = new CombatState();
        state.warrior1 = w1;
        state.warrior2 = w2;
        state.w1Health = w1.getHealth();
        state.w2Health = w2.getHealth();
        state.w1Stamina = w1.getStamina();
        state.w2Stamina = w2.getStamina();
        state.w1Initiative = calculateInitiative(w1);
        state.w2Initiative = calculateInitiative(w2);
        state.w1BleedStacks = 0;
        state.w2BleedStacks = 0;
        state.w1Knockdowns = 0;
        state.w2Knockdowns = 0;
        state.isFinished = false;
        state.winner = null;
        return state;
    }
    
    private int calculateInitiative(Warrior warrior) {
        int base = 10;
        int dexBonus = (warrior.getDexterity() - 10) / 2;
        
        // Style modifiers
        Strategy primaryStrategy = warrior.getStrategies().isEmpty() ? 
            new Strategy("Strike", "Short Sword", "Leather Armor") :
            warrior.getStrategies().get(0);
        
        String style = primaryStrategy.getStyle();
        StyleProperties props = FightingStyle.getStyleProperties(style);
        if (props != null) {
            base += props.getInitiativeBonus();
        }
        
        // Weapon weight penalty
        Weapon weapon = WeaponsUtil.getWeaponByName(primaryStrategy.getWeapon());
        if (weapon != null) {
            base -= weapon.getWeight() / 5;
        }
        
        // Race modifiers
        RacialModifiers racialMods = RacialModifiers.getModifiersForRace(warrior.getRace());
        base += racialMods.getInitiativeModifier();
        
        return base + dexBonus + random.nextInt(20);
    }
    
    private CombatTurn executeTurn(CombatState state) {
        CombatTurn turn = new CombatTurn();
        turn.narrative = new ArrayList<>();
        
        // Determine who goes first based on initiative
        Warrior attacker, defender;
        int attInitiative, defInitiative;
        boolean w1AttacksFirst = state.w1Initiative >= state.w2Initiative;
        
        if (w1AttacksFirst) {
            attacker = state.warrior1;
            defender = state.warrior2;
            attInitiative = state.w1Initiative;
            defInitiative = state.w2Initiative;
        } else {
            attacker = state.warrior2;
            defender = state.warrior1;
            attInitiative = state.w2Initiative;
            defInitiative = state.w1Initiative;
        }
        
        // Attacker's action
        AttackResult attackResult = executeAttack(attacker, defender, state);
        turn.narrative.addAll(attackResult.narrative);
        
        if (attackResult.targetDown) {
            turn.knockout = true;
            turn.winner = attacker;
            turn.fightEnded = true;
            return turn;
        }
        
        // Check for concede
        if (shouldConcede(defender, state)) {
            turn.conceded = true;
            turn.winner = attacker;
            turn.fightEnded = true;
            turn.narrative.add(narrativeEngine.generateConcedeNarrative(defender, attacker));
            return turn;
        }
        
        // Defender's counter-attack if still able
        if (!attackResult.attackerStunned) {
            AttackResult counterResult = executeAttack(defender, attacker, state);
            turn.narrative.addAll(counterResult.narrative);
            
            if (counterResult.targetDown) {
                turn.knockout = true;
                turn.winner = defender;
                turn.fightEnded = true;
            }
        }
        
        // End of turn cleanup
        endOfTurnCleanup(state);
        
        return turn;
    }
    
    private AttackResult executeAttack(Warrior attacker, Warrior defender, CombatState state) {
        AttackResult result = new AttackResult();
        result.narrative = new ArrayList<>();
        
        // Get attacker's strategy and weapons
        Strategy strategy = attacker.getStrategies().isEmpty() ?
            new Strategy("Strike", "Short Sword", "Leather Armor") :
            attacker.getStrategies().get(0);
        
        Weapon mainWeapon = WeaponsUtil.getWeaponByName(strategy.getWeapon());
        Weapon offhandWeapon = WeaponsUtil.getWeaponByName(strategy.getOffhandWeapon());
        
        // Calculate attack roll
        int attackRoll = calculateAttackRoll(attacker, strategy, mainWeapon);
        
        // Calculate defense roll
        int defenseRoll = calculateDefenseRoll(defender, strategy);
        
        // Determine hit/miss
        boolean hit = attackRoll >= defenseRoll;
        
        if (!hit) {
            result.narrative.add(narrativeEngine.generateMissNarrative(attacker, defender, attackRoll, defenseRoll));
            
            // Check for decoy feint success
            if ("Decoy".equals(strategy.getStyle())) {
                if (random.nextDouble() < 0.4) {
                    result.attackerStunned = true;
                    result.narrative.add(narrativeEngine.generateDecoyFeintSuccess(attacker, defender));
                }
            }
            return result;
        }
        
        // Hit landed - calculate damage
        int damage = calculateDamage(attacker, defender, strategy, mainWeapon, offhandWeapon);
        
        // Apply racial and style modifiers
        RacialModifiers racialMods = RacialModifiers.getModifiersForRace(attacker.getRace());
        damage += racialMods.getDamageModifier();
        
        // Critical hit check
        boolean isCritical = (attackRoll - defenseRoll) >= 10;
        if (isCritical) {
            damage = (int)(damage * 1.5);
            result.narrative.add(narrativeEngine.generateCriticalHitNarrative(attacker, defender));
        }
        
        // Apply damage to defender
        boolean isW1Defender = defender == state.warrior1;
        if (isW1Defender) {
            state.w1Health = Math.max(0, state.w1Health - damage);
            if (damage >= 5) {
                state.w1BleedStacks = Math.min(MAX_BLEED_STACKS, state.w1BleedStacks + 1);
            }
        } else {
            state.w2Health = Math.max(0, state.w2Health - damage);
            if (damage >= 5) {
                state.w2BleedStacks = Math.min(MAX_BLEED_STACKS, state.w2BleedStacks + 1);
            }
        }
        
        result.narrative.add(narrativeEngine.generateHitNarrative(attacker, defender, damage, 
            strategy.getStyle(), mainWeapon != null ? mainWeapon.getName() : "fists"));
        
        // Check for knockdown
        if (damage >= 8 && defender.getStamina() >= KNOCKDOWN_STAMINA_COST) {
            if (random.nextDouble() < 0.3) {
                defender.setStamina(defender.getStamina() - KNOCKDOWN_STAMINA_COST);
                if (isW1Defender) {
                    state.w1Knockdowns++;
                } else {
                    state.w2Knockdowns++;
                }
                result.narrative.add(narrativeEngine.generateKnockdownNarrative(defender));
            }
        }
        
        // Check if target is down
        if (state.w1Health <= 0 || state.w2Health <= 0) {
            result.targetDown = true;
        }
        
        return result;
    }
    
    private int calculateAttackRoll(Warrior warrior, Strategy strategy, Weapon weapon) {
        int base = 10;
        
        // Skill bonus based on style
        Map<String, Integer> skills = warrior.getSkills();
        String style = strategy.getStyle();
        int skillLevel = skills.getOrDefault(style.toLowerCase(), 0);
        base += skillLevel;
        
        // Stat bonus (STR for most, DEX for finesse styles)
        if ("Finesse".equals(style) || "Duelist".equals(style) || "Acrobat".equals(style)) {
            base += (warrior.getDexterity() - 10) / 2;
        } else {
            base += (warrior.getStrength() - 10) / 2;
        }
        
        // Weapon proficiency
        if (weapon != null) {
            String weaponSkill = weapon.getType().toLowerCase();
            int weaponSkillLevel = skills.getOrDefault(weaponSkill, 0);
            base += weaponSkillLevel / 2;
        }
        
        // Style modifier
        StyleProperties props = FightingStyle.getStyleProperties(style);
        if (props != null) {
            base += props.getParryBonus(); // Using parry as attack bonus proxy
        }
        
        // Fatigue penalty
        int fatiguePenalty = (100 - warrior.getStamina()) / 20;
        base -= fatiguePenalty;
        
        return base + random.nextInt(20);
    }
    
    private int calculateDefenseRoll(Warrior warrior, Strategy attackerStrategy) {
        int base = 10;
        
        // Dodge/parry based on defender's style
        Strategy defenderStrategy = warrior.getStrategies().isEmpty() ?
            new Strategy("Strike", "Short Sword", "Leather Armor") :
            warrior.getStrategies().get(0);
        
        String style = defenderStrategy.getStyle();
        StyleProperties props = FightingStyle.getStyleProperties(style);
        if (props != null) {
            base += props.getDodgeBonus();
        }
        
        // Dexterity bonus
        base += (warrior.getDexterity() - 10) / 2;
        
        // Shield bonus
        String offhand = defenderStrategy.getOffhandWeapon();
        if (offhand != null && !offhand.isEmpty() && !offhand.equals("None")) {
            Weapon shield = WeaponsUtil.getWeaponByName(offhand);
            if (shield != null && "Shield".equals(shield.getType())) {
                base += 3;
            }
        }
        
        // Armor bonus
        String armor = defenderStrategy.getArmor();
        if (armor != null && !armor.isEmpty()) {
            ArmorPiece armorPiece = ArmorPiece.fromName(armor);
            if (armorPiece != null) {
                base += armorPiece.getDefenseBonus();
            }
        }
        
        // Fatigue penalty
        int fatiguePenalty = (100 - warrior.getStamina()) / 20;
        base -= fatiguePenalty;
        
        return base + random.nextInt(20);
    }
    
    private int calculateDamage(Warrior attacker, Warrior defender, Strategy strategy, 
                                Weapon mainWeapon, Weapon offhandWeapon) {
        int baseDamage = 0;
        
        // Base weapon damage
        if (mainWeapon != null) {
            baseDamage = mainWeapon.getDamage();
        } else {
            baseDamage = 2; // Unarmed
        }
        
        // Strength bonus
        baseDamage += (attacker.getStrength() - 10) / 3;
        
        // Style-specific damage bonuses
        String style = strategy.getStyle();
        Map<String, Integer> skills = attacker.getSkills();
        
        switch (style.toLowerCase()) {
            case "cleave":
                baseDamage += skills.getOrDefault("cleave", 0);
                break;
            case "bash":
                baseDamage += skills.getOrDefault("bash", 0);
                break;
            case "slash":
                baseDamage += skills.getOrDefault("slash", 0);
                break;
            case "strike":
                baseDamage += skills.getOrDefault("strike", 0);
                break;
            case "open hand":
                baseDamage = skills.getOrDefault("open_hand", 0);
                break;
        }
        
        // Two-weapon fighting bonus
        if (offhandWeapon != null && !offhandWeapon.getName().equals("None")) {
            baseDamage += offhandWeapon.getDamage() / 2;
        }
        
        // Defender's armor reduction
        Strategy defStrategy = defender.getStrategies().isEmpty() ?
            new Strategy("Strike", "Short Sword", "Leather Armor") :
            defender.getStrategies().get(0);
        
        String armor = defStrategy.getArmor();
        if (armor != null && !armor.isEmpty()) {
            ArmorPiece armorPiece = ArmorPiece.fromName(armor);
            if (armorPiece != null) {
                baseDamage = Math.max(1, baseDamage - armorPiece.getDefenseBonus());
            }
        }
        
        return Math.max(1, baseDamage);
    }
    
    private boolean shouldConcede(Warrior warrior, CombatState state) {
        // Concede if health is very low and presence suggests mercy
        int health = (warrior == state.warrior1) ? state.w1Health : state.w2Health;
        
        if (health <= 3) {
            int presenceCheck = random.nextInt(20) + (warrior.getPresence() - 10) / 2;
            return presenceCheck < 8; // Low presence = more likely to concede
        }
        
        return health <= 0;
    }
    
    private void endOfTurnCleanup(CombatState state) {
        // Apply bleed damage
        if (state.w1BleedStacks > 0) {
            int bleedDamage = state.w1BleedStacks * BLEED_DAMAGE_PER_TURN;
            state.w1Health = Math.max(0, state.w1Health - bleedDamage);
            state.w1BleedStacks = Math.max(0, state.w1BleedStacks - 1);
        }
        
        if (state.w2BleedStacks > 0) {
            int bleedDamage = state.w2BleedStacks * BLEED_DAMAGE_PER_TURN;
            state.w2Health = Math.max(0, state.w2Health - bleedDamage);
            state.w2BleedStacks = Math.max(0, state.w2BleedStacks - 1);
        }
        
        // Stamina recovery
        state.warrior1.setStamina(Math.min(100, state.warrior1.getStamina() + 5));
        state.warrior2.setStamina(Math.min(100, state.warrior2.getStamina() + 5));
    }
    
    private Warrior determineWinnerByStats(Warrior w1, Warrior w2) {
        int w1Score = w1.getHealth() + w1.getStamina() / 2 + w1.getWins() * 10;
        int w2Score = w2.getHealth() + w2.getStamina() / 2 + w2.getWins() * 10;
        
        return w1Score >= w2Score ? w1 : w2;
    }
    
    private CombatResult finalizeCombatResult(CombatState state, List<String> narrative) {
        CombatResult result = new CombatResult();
        result.winner = state.winner;
        result.loser = (state.winner == state.warrior1) ? state.warrior2 : state.warrior1;
        result.narrative = narrative;
        result.w1FinalHealth = state.w1Health;
        result.w2FinalHealth = state.w2Health;
        result.turns = narrative.size();
        return result;
    }
    
    // Inner classes for combat state management
    
    private static class CombatState {
        Warrior warrior1;
        Warrior warrior2;
        int w1Health;
        int w2Health;
        int w1Stamina;
        int w2Stamina;
        int w1Initiative;
        int w2Initiative;
        int w1BleedStacks;
        int w2BleedStacks;
        int w1Knockdowns;
        int w2Knockdowns;
        boolean isFinished;
        Warrior winner;
    }
    
    private static class CombatTurn {
        List<String> narrative;
        boolean knockout;
        boolean conceded;
        boolean fightEnded;
        Warrior winner;
    }
    
    private static class AttackResult {
        List<String> narrative;
        boolean targetDown;
        boolean attackerStunned;
    }
}
