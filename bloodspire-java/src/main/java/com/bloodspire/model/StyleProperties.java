package com.bloodspire.model;

/**
 * Combat modifiers for a given fighting style.
 */
public class StyleProperties {
    private double apmModifier;      // Modifier to actions per minute
    private double damageModifier;   // Flat modifier to damage dealt
    private int parryBonus;          // Bonus to parry rolls (can be negative)
    private int dodgeBonus;          // Bonus to dodge rolls
    private double enduranceBurn;    // Endurance spent per action (negative = gain)
    private boolean intimidate;      // Chance to scare opponent
    private boolean anxiouslyAwaits; // Drains foe endurance when used
    private boolean totalKillMode;   // Ignores defenses, nearly no parry/dodge
    private final String notes;            // Description

    public StyleProperties(double apmModifier, double damageModifier, int parryBonus, 
                           int dodgeBonus, double enduranceBurn, boolean intimidate,
                           boolean anxiouslyAwaits, boolean totalKillMode, String notes) {
        this.apmModifier = apmModifier;
        this.damageModifier = damageModifier;
        this.parryBonus = parryBonus;
        this.dodgeBonus = dodgeBonus;
        this.enduranceBurn = enduranceBurn;
        this.intimidate = intimidate;
        this.anxiouslyAwaits = anxiouslyAwaits;
        this.totalKillMode = totalKillMode;
        this.notes = notes != null ? notes : "";
    }

    public double getApmModifier() { return apmModifier; }
    public double getDamageModifier() { return damageModifier; }
    public int getParryBonus() { return parryBonus; }
    public int getDodgeBonus() { return dodgeBonus; }
    public double getEnduranceBurn() { return enduranceBurn; }
    public boolean isIntimidate() { return intimidate; }
    public boolean isAnxiouslyAwaits() { return anxiouslyAwaits; }
    public boolean isTotalKillMode() { return totalKillMode; }
    public String getNotes() { return notes; }
    
    // Package-private setters for builder pattern
    void setParryBonus(int parryBonus) { this.parryBonus = parryBonus; }
    void setDodgeBonus(int dodgeBonus) { this.dodgeBonus = dodgeBonus; }
    void setApmModifier(double apmModifier) { this.apmModifier = apmModifier; }
    void setDamageModifier(double damageModifier) { this.damageModifier = damageModifier; }
    void setEnduranceBurn(double enduranceBurn) { this.enduranceBurn = enduranceBurn; }
    void setIntimidate(boolean intimidate) { this.intimidate = intimidate; }
    void setAnxiouslyAwaits(boolean anxiouslyAwaits) { this.anxiouslyAwaits = anxiouslyAwaits; }
    void setTotalKillMode(boolean totalKillMode) { this.totalKillMode = totalKillMode; }
}
