package com.bloodspire.model;

/**
 * Enum representing the seven core stats in BLOODSPIRE.
 */
public enum Stat {
    STRENGTH("strength"),
    AGILITY("agility"),
    ENDURANCE("endurance"),
    INTELLIGENCE("intelligence"),
    WISDOM("wisdom"),
    CHARISMA("charisma"),
    PRESENCE("presence");
    
    private final String displayName;
    
    Stat(String displayName) {
        this.displayName = displayName;
    }
    
    public String getDisplayName() {
        return displayName;
    }
}
