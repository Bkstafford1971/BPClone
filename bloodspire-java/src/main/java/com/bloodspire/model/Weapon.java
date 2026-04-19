package com.bloodspire.model;

import java.util.*;

/**
 * Represents a weapon in the Bloodspire battle arena.
 * Mirrors the Weapon class from the Python implementation.
 */
public class Weapon {
    
    // Weapon categories (matching Python constants)
    public static final String SWORD_KNIFE = "Sword/Knife";
    public static final String AXE_PICK = "Axe/Pick";
    public static final String HAMMER_MACE = "Hammer/Mace";
    public static final String POLEARM_SPEAR = "Polearm/Spear";
    public static final String FLAIL = "Flail";
    public static final String STAVE = "Stave";
    public static final String SHIELD = "Shield";
    public static final String ODDBALL = "Oddball";
    
    public static final List<String> ALL_CATEGORIES = Arrays.asList(
        SWORD_KNIFE, AXE_PICK, HAMMER_MACE, POLEARM_SPEAR,
        FLAIL, STAVE, SHIELD, ODDBALL
    );
    
    // Instance fields
    private String skillKey;
    private String display;
    private double weight;
    private boolean throwable;
    private boolean twoHand;
    private String category;
    
    // Special rules flags
    private boolean armorPiercing;
    private boolean mcCompatible;
    private boolean flailBypass;
    private boolean chargeAttack;
    private boolean canDisarm;
    private boolean canSweep;
    private boolean isShield;
    
    // Style guidance
    private List<String> preferredStyles;
    private List<String> weakStyles;
    
    // Flavor notes
    private String notes;
    
    /**
     * Constructor with all parameters.
     */
    public Weapon(String skillKey, String display, double weight, boolean throwable,
                  boolean twoHand, String category) {
        this.skillKey = skillKey;
        this.display = display;
        this.weight = weight;
        this.throwable = throwable;
        this.twoHand = twoHand;
        this.category = category;
        this.armorPiercing = false;
        this.mcCompatible = false;
        this.flailBypass = false;
        this.chargeAttack = false;
        this.canDisarm = false;
        this.canSweep = false;
        this.isShield = false;
        this.preferredStyles = new ArrayList<>();
        this.weakStyles = new ArrayList<>();
        this.notes = "";
    }
    
    /**
     * Full constructor with all optional parameters.
     */
    public Weapon(String skillKey, String display, double weight, boolean throwable,
                  boolean twoHand, String category, boolean armorPiercing,
                  boolean mcCompatible, boolean flailBypass, boolean chargeAttack,
                  boolean canDisarm, boolean canSweep, boolean isShield,
                  List<String> preferredStyles, List<String> weakStyles, String notes) {
        this.skillKey = skillKey;
        this.display = display;
        this.weight = weight;
        this.throwable = throwable;
        this.twoHand = twoHand;
        this.category = category;
        this.armorPiercing = armorPiercing;
        this.mcCompatible = mcCompatible;
        this.flailBypass = flailBypass;
        this.chargeAttack = chargeAttack;
        this.canDisarm = canDisarm;
        this.canSweep = canSweep;
        this.isShield = isShield;
        this.preferredStyles = preferredStyles != null ? new ArrayList<>(preferredStyles) : new ArrayList<>();
        this.weakStyles = weakStyles != null ? new ArrayList<>(weakStyles) : new ArrayList<>();
        this.notes = notes != null ? notes : "";
    }
    
    // Getters
    public String getSkillKey() { return skillKey; }
    public String getName() { return display; }
    public String getDisplay() { return display; }
    public double getWeight() { return weight; }
    public boolean isThrowable() { return throwable; }
    public boolean isTwoHand() { return twoHand; }
    public String getCategory() { return category; }
    public boolean isArmorPiercing() { return armorPiercing; }
    public boolean isMcCompatible() { return mcCompatible; }
    public boolean isFlailBypass() { return flailBypass; }
    public boolean isChargeAttack() { return chargeAttack; }
    public boolean isCanDisarm() { return canDisarm; }
    public boolean isCanSweep() { return canSweep; }
    public boolean isShield() { return isShield; }
    public List<String> getPreferredStyles() { return new ArrayList<>(preferredStyles); }
    public List<String> getWeakStyles() { return new ArrayList<>(weakStyles); }
    public String getNotes() { return notes; }
    
    /**
     * The strength capacity needed to wield this weapon one-handed.
     */
    public double getEffectiveOneHandCapacityNeeded() {
        return this.weight;
    }
    
    /**
     * The strength capacity needed to wield this weapon two-handed.
     * Two-handed use grants +1 to effective STR carry capacity.
     */
    public double getEffectiveTwoHandCapacityNeeded() {
        return Math.max(0.0, this.weight - 1.0);
    }
    
    /**
     * Calculate the under-strength penalty fraction (0.0 = no penalty, 1.0 = unusable).
     * 
     * The guide says under-strength warriors suffer proportional
     * attack-rate and damage penalties. We model this as:
     * 
     * effective_capacity = max_weapon_weight(strength) + (1.0 if two_handed else 0.0)
     * if weapon_weight <= effective_capacity: penalty = 0.0
     * else:
     *     overage = weapon_weight - effective_capacity
     *     penalty = min(1.0, overage / effective_capacity)
     * 
     * So a warrior who is exactly 1 weight point over capacity suffers a
     * penalty equal to (1 / their capacity), never exceeding 100%.
     * 
     * Returns a float 0.0–1.0. Callers multiply attack rate and damage by
     * (1.0 - penalty).
     */
    public double penaltyFor(int strength, boolean twoHanded) {
        double capacity = WeaponsUtil.maxWeaponWeight(strength) + (twoHanded ? 1.0 : 0.0);
        if (this.weight <= capacity) {
            return 0.0;
        }
        if (capacity <= 0) {
            return 1.0;
        }
        double overage = this.weight - capacity;
        return Math.min(1.0, overage / capacity);
    }
    
    /**
     * True if the warrior can wield this weapon with no penalty.
     * Does NOT block equipping — just indicates whether full effectiveness
     * is available.
     */
    public boolean canWield(int strength, boolean twoHanded) {
        return this.penaltyFor(strength, twoHanded) == 0.0;
    }
    
    @Override
    public String toString() {
        List<String> flags = new ArrayList<>();
        if (throwable) flags.add("throw");
        if (twoHand) flags.add("2H");
        if (armorPiercing) flags.add("AP");
        if (flailBypass) flags.add("bypass");
        if (chargeAttack) flags.add("charge");
        
        String flagStr = flags.isEmpty() ? "" : " [" + String.join(", ", flags) + "]";
        return String.format("%s (wt:%.1f)%s", display, weight, flagStr);
    }
}
