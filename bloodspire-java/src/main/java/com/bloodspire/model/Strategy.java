package com.bloodspire.model;

/**
 * Represents the tactical strategy a warrior or team can adopt.
 * Mirrors the Python Strategy logic.
 */
public enum Strategy {
    ATTACK("Attack", "Focus on dealing maximum damage."),
    DEFEND("Defend", "Focus on reducing incoming damage."),
    SUPPORT("Support", "Focus on healing and aiding allies."),
    BALANCED("Balanced", "A mix of attack, defense, and support.");

    private final String displayName;
    private final String description;

    Strategy(String displayName, String description) {
        this.displayName = displayName;
        this.description = description;
    }

    public String getDisplayName() {
        return displayName;
    }

    public String getDescription() {
        return description;
    }
    
    /**
     * Helper to match string input to Enum, case-insensitive.
     */
    public static Strategy fromString(String text) {
        if (text != null) {
            for (Strategy s : Strategy.values()) {
                if (text.equalsIgnoreCase(s.name()) || text.equalsIgnoreCase(s.displayName)) {
                    return s;
                }
            }
        }
        throw new IllegalArgumentException("No strategy found with text: " + text);
    }
}
