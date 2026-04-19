package com.bloodspire.model;

import java.util.*;

/**
 * Racial modifiers applied to warriors in combat.
 * These are applied at combat time, not baked into base stats.
 */
public class RacialModifiers {
    // Hit Points
    private int hpBonus = 0;
    
    // Damage
    private int damageBonus = 0;
    private int damagePenalty = 0;
    
    // Attack Rate & Initiative
    private int attackRateBonus = 0;
    private int attackRatePenalty = 0;
    private int initiativeBonus = 0;
    
    // Attributes
    private int strengthPenalty = 0;
    
    // Defense
    private int dodgeBonus = 0;
    private int dodgePenalty = 0;
    private int parryBonus = 0;
    private int parryPenalty = 0;
    
    // Special Flags
    private boolean armorCapacityBonus = false;
    private boolean shieldBonus = false;
    private boolean dualWeaponBonus = false;
    private boolean martialCombatBonus = false;
    private boolean trainsStatsFaster = false;
    private boolean fewerPerms = false;
    private boolean biggerWeaponsBonus = false;
    
    // New Race Abilities
    private boolean thrownMastery = false;
    private boolean scavenger = false;
    private boolean heavyWeaponPenalty = false;
    private boolean counterstrikeMastery = false;
    private boolean tacticianEdge = false;
    private boolean naturalArmor = false;
    private boolean naturalWeaponBonus = false;
    private boolean acrobaticAdvantage = false;
    private boolean frenzyAbility = false;
    private boolean spearException = false;
    
    // Flavor / Soft Mechanics
    private List<String> preferredWeapons = new ArrayList<>();
    private List<String> weakWeapons = new ArrayList<>();
    private String favoredOpponents = "";
    private String disfavoredOpponents = "";
    
    // Constructors
    public RacialModifiers() {}
    
    public RacialModifiers(Builder builder) {
        this.hpBonus = builder.hpBonus;
        this.damageBonus = builder.damageBonus;
        this.damagePenalty = builder.damagePenalty;
        this.attackRateBonus = builder.attackRateBonus;
        this.attackRatePenalty = builder.attackRatePenalty;
        this.initiativeBonus = builder.initiativeBonus;
        this.strengthPenalty = builder.strengthPenalty;
        this.dodgeBonus = builder.dodgeBonus;
        this.dodgePenalty = builder.dodgePenalty;
        this.parryBonus = builder.parryBonus;
        this.parryPenalty = builder.parryPenalty;
        this.armorCapacityBonus = builder.armorCapacityBonus;
        this.shieldBonus = builder.shieldBonus;
        this.dualWeaponBonus = builder.dualWeaponBonus;
        this.martialCombatBonus = builder.martialCombatBonus;
        this.trainsStatsFaster = builder.trainsStatsFaster;
        this.fewerPerms = builder.fewerPerms;
        this.biggerWeaponsBonus = builder.biggerWeaponsBonus;
        this.thrownMastery = builder.thrownMastery;
        this.scavenger = builder.scavenger;
        this.heavyWeaponPenalty = builder.heavyWeaponPenalty;
        this.counterstrikeMastery = builder.counterstrikeMastery;
        this.tacticianEdge = builder.tacticianEdge;
        this.naturalArmor = builder.naturalArmor;
        this.naturalWeaponBonus = builder.naturalWeaponBonus;
        this.acrobaticAdvantage = builder.acrobaticAdvantage;
        this.frenzyAbility = builder.frenzyAbility;
        this.spearException = builder.spearException;
        this.preferredWeapons = new ArrayList<>(builder.preferredWeapons);
        this.weakWeapons = new ArrayList<>(builder.weakWeapons);
        this.favoredOpponents = builder.favoredOpponents;
        this.disfavoredOpponents = builder.disfavoredOpponents;
    }
    
    // Getters
    public int getHpBonus() { return hpBonus; }
    public int getDamageBonus() { return damageBonus; }
    public int getDamagePenalty() { return damagePenalty; }
    public int getAttackRateBonus() { return attackRateBonus; }
    public int getAttackRatePenalty() { return attackRatePenalty; }
    public int getInitiativeBonus() { return initiativeBonus; }
    public int getStrengthPenalty() { return strengthPenalty; }
    public int getDodgeBonus() { return dodgeBonus; }
    public int getDodgePenalty() { return dodgePenalty; }
    public int getParryBonus() { return parryBonus; }
    public int getParryPenalty() { return parryPenalty; }
    public boolean isArmorCapacityBonus() { return armorCapacityBonus; }
    public boolean isShieldBonus() { return shieldBonus; }
    public boolean isDualWeaponBonus() { return dualWeaponBonus; }
    public boolean isMartialCombatBonus() { return martialCombatBonus; }
    public boolean isTrainsStatsFaster() { return trainsStatsFaster; }
    public boolean isFewerPerms() { return fewerPerms; }
    public boolean isBiggerWeaponsBonus() { return biggerWeaponsBonus; }
    public boolean isThrownMastery() { return thrownMastery; }
    public boolean isScavenger() { return scavenger; }
    public boolean isHeavyWeaponPenalty() { return heavyWeaponPenalty; }
    public boolean isCounterstrikeMastery() { return counterstrikeMastery; }
    public boolean isTacticianEdge() { return tacticianEdge; }
    public boolean isNaturalArmor() { return naturalArmor; }
    public boolean isNaturalWeaponBonus() { return naturalWeaponBonus; }
    public boolean isAcrobaticAdvantage() { return acrobaticAdvantage; }
    public boolean isFrenzyAbility() { return frenzyAbility; }
    public boolean isSpearException() { return spearException; }
    public List<String> getPreferredWeapons() { return preferredWeapons; }
    public List<String> getWeakWeapons() { return weakWeapons; }
    public String getFavoredOpponents() { return favoredOpponents; }
    public String getDisfavoredOpponents() { return disfavoredOpponents; }
    
    // Builder pattern for clean construction
    public static class Builder {
        private int hpBonus = 0;
        private int damageBonus = 0;
        private int damagePenalty = 0;
        private int attackRateBonus = 0;
        private int attackRatePenalty = 0;
        private int initiativeBonus = 0;
        private int strengthPenalty = 0;
        private int dodgeBonus = 0;
        private int dodgePenalty = 0;
        private int parryBonus = 0;
        private int parryPenalty = 0;
        private boolean armorCapacityBonus = false;
        private boolean shieldBonus = false;
        private boolean dualWeaponBonus = false;
        private boolean martialCombatBonus = false;
        private boolean trainsStatsFaster = false;
        private boolean fewerPerms = false;
        private boolean biggerWeaponsBonus = false;
        private boolean thrownMastery = false;
        private boolean scavenger = false;
        private boolean heavyWeaponPenalty = false;
        private boolean counterstrikeMastery = false;
        private boolean tacticianEdge = false;
        private boolean naturalArmor = false;
        private boolean naturalWeaponBonus = false;
        private boolean acrobaticAdvantage = false;
        private boolean frenzyAbility = false;
        private boolean spearException = false;
        private List<String> preferredWeapons = new ArrayList<>();
        private List<String> weakWeapons = new ArrayList<>();
        private String favoredOpponents = "";
        private String disfavoredOpponents = "";
        
        public Builder hpBonus(int val) { this.hpBonus = val; return this; }
        public Builder damageBonus(int val) { this.damageBonus = val; return this; }
        public Builder damagePenalty(int val) { this.damagePenalty = val; return this; }
        public Builder attackRateBonus(int val) { this.attackRateBonus = val; return this; }
        public Builder attackRatePenalty(int val) { this.attackRatePenalty = val; return this; }
        public Builder initiativeBonus(int val) { this.initiativeBonus = val; return this; }
        public Builder strengthPenalty(int val) { this.strengthPenalty = val; return this; }
        public Builder dodgeBonus(int val) { this.dodgeBonus = val; return this; }
        public Builder dodgePenalty(int val) { this.dodgePenalty = val; return this; }
        public Builder parryBonus(int val) { this.parryBonus = val; return this; }
        public Builder parryPenalty(int val) { this.parryPenalty = val; return this; }
        public Builder armorCapacityBonus(boolean val) { this.armorCapacityBonus = val; return this; }
        public Builder shieldBonus(boolean val) { this.shieldBonus = val; return this; }
        public Builder dualWeaponBonus(boolean val) { this.dualWeaponBonus = val; return this; }
        public Builder martialCombatBonus(boolean val) { this.martialCombatBonus = val; return this; }
        public Builder trainsStatsFaster(boolean val) { this.trainsStatsFaster = val; return this; }
        public Builder fewerPerms(boolean val) { this.fewerPerms = val; return this; }
        public Builder biggerWeaponsBonus(boolean val) { this.biggerWeaponsBonus = val; return this; }
        public Builder thrownMastery(boolean val) { this.thrownMastery = val; return this; }
        public Builder scavenger(boolean val) { this.scavenger = val; return this; }
        public Builder heavyWeaponPenalty(boolean val) { this.heavyWeaponPenalty = val; return this; }
        public Builder counterstrikeMastery(boolean val) { this.counterstrikeMastery = val; return this; }
        public Builder tacticianEdge(boolean val) { this.tacticianEdge = val; return this; }
        public Builder naturalArmor(boolean val) { this.naturalArmor = val; return this; }
        public Builder naturalWeaponBonus(boolean val) { this.naturalWeaponBonus = val; return this; }
        public Builder acrobaticAdvantage(boolean val) { this.acrobaticAdvantage = val; return this; }
        public Builder frenzyAbility(boolean val) { this.frenzyAbility = val; return this; }
        public Builder spearException(boolean val) { this.spearException = val; return this; }
        public Builder preferredWeapons(List<String> val) { this.preferredWeapons = new ArrayList<>(val); return this; }
        public Builder weakWeapons(List<String> val) { this.weakWeapons = new ArrayList<>(val); return this; }
        public Builder favoredOpponents(String val) { this.favoredOpponents = val; return this; }
        public Builder disfavoredOpponents(String val) { this.disfavoredOpponents = val; return this; }
        
        public RacialModifiers build() { return new RacialModifiers(this); }
    }
}
