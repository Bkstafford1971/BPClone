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
    
    /**
     * Alias for getDefenseValue() to match Python API
     */
    public int getDefenseBonus() {
        return defenseValue;
    }
    
    /**
     * Static lookup method to find armor by name (case-insensitive)
     * This would typically search a registry of all armor pieces.
     * For now, we'll return null or throw exception if not found.
     * In a full implementation, this would query ArmorUtil.ALL_ARMOR
     */
    public static ArmorPiece fromName(String name) {
        if (name == null || name.trim().isEmpty()) {
            return null;
        }
        // Search through known armor pieces
        for (ArmorPiece piece : ArmorUtil.getAllArmors()) {
            if (piece.getName().equalsIgnoreCase(name)) {
                return piece;
            }
        }
        return null;
    }
    
    @Override
    public String toString() {
        String kind = isHelm ? "Helm" : "Armor";
        String apFlag = apVulnerable ? " [AP-vuln]" : "";
        return String.format("%s (%s, wt:%.1f, def:%d)%s", 
                            name, kind, weight, defenseValue, apFlag);
    }
}
