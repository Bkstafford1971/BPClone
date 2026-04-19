package com.bloodspire.model;

/**
 * Represents a single armor or helm option in Bloodspire.
 * Mirrors the ArmorPiece class from the Python implementation.
 */
public class ArmorPiece {
    
    private String name;
    private double weight;
    private int defenseValue;
    private boolean isHelm;
    private boolean apVulnerable;
    private int dexPenalty;
    private String notes;
    
    /**
     * Constructor for ArmorPiece.
     * 
     * @param name Display name as seen in fight headers
     * @param weight From the guide's armor table. Compared against STR capacity
     * @param defenseValue Damage reduction value (0-10 scale)
     * @param isHelm True for helms, False for body armor
     * @param apVulnerable True if extra-vulnerable to armor-piercing weapons
     * @param dexPenalty How much this armor slows a warrior down (0-5)
     * @param notes Flavor text from guide or derived analysis
     */
    public ArmorPiece(String name, double weight, int defenseValue, 
                      boolean isHelm, boolean apVulnerable, int dexPenalty, 
                      String notes) {
        this.name = name;
        this.weight = weight;
        this.defenseValue = defenseValue;
        this.isHelm = isHelm;
        this.apVulnerable = apVulnerable;
        this.dexPenalty = dexPenalty;
        this.notes = notes != null ? notes : "";
    }
    
    // Getters
    public String getName() { return name; }
    public double getWeight() { return weight; }
    public int getDefenseValue() { return defenseValue; }
    public boolean isHelm() { return isHelm; }
    public boolean isApVulnerable() { return apVulnerable; }
    public int getDexPenalty() { return dexPenalty; }
    public String getNotes() { return notes; }
    
    @Override
    public String toString() {
        String kind = isHelm ? "Helm" : "Armor";
        String apFlag = apVulnerable ? " [AP-vuln]" : "";
        return String.format("%s (%s, wt:%.1f, def:%d)%s", 
                            name, kind, weight, defenseValue, apFlag);
    }
}
