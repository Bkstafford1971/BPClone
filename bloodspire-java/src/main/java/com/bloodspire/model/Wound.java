package com.bloodspire.model;

/**
 * Represents a wound or injury sustained by a warrior.
 */
public class Wound {
    private Warrior warrior;
    private String location;
    private int severity;
    private boolean isPermanent;
    
    public Wound(Warrior warrior, String location, int severity) {
        this.warrior = warrior;
        this.location = location;
        this.severity = severity;
        this.isPermanent = false;
    }
    
    public Warrior getWarrior() {
        return warrior;
    }
    
    public String getLocation() {
        return location;
    }
    
    public int getSeverity() {
        return severity;
    }
    
    public boolean isPermanent() {
        return isPermanent;
    }
    
    public void setPermanent(boolean permanent) {
        isPermanent = permanent;
    }
}
