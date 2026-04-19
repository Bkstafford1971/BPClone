package com.bloodspire.model;

/**
 * One row in a warrior's strategy table.
 * A warrior may have up to 6 of these, read top-to-bottom each minute.
 * Mirrors the Python Strategy class from warrior.py.
 */
public class Strategy {
    private String trigger;        // e.g., "Always", "If HP < 50%", etc.
    private String style;          // e.g., "Strike", "Slash", "Bash", etc.
    private int activity;          // 0-9 scale
    private String aimPoint;       // target body location
    private String defensePoint;   // defended body location
    
    public Strategy() {
        this.trigger = "Always";
        this.style = "Strike";
        this.activity = 5;
        this.aimPoint = "None";
        this.defensePoint = "Chest";
    }
    
    public Strategy(String trigger, String style, int activity, String aimPoint, String defensePoint) {
        this.trigger = trigger != null ? trigger : "Always";
        this.style = style != null ? style : "Strike";
        this.activity = Math.max(0, Math.min(9, activity));  // Clamp 0-9
        this.aimPoint = aimPoint != null ? aimPoint : "None";
        this.defensePoint = defensePoint != null ? defensePoint : "Chest";
    }
    
    // Getters
    public String getTrigger() { return trigger; }
    public String getStyle() { return style; }
    public int getActivity() { return activity; }
    public String getAimPoint() { return aimPoint; }
    public String getDefensePoint() { return defensePoint; }
    
    // Aliases for combat engine compatibility
    public String getWeapon() { return "Short Sword"; } // Default weapon
    public String getOffhandWeapon() { return "None"; } // Default offhand
    
    // Setters
    public void setTrigger(String trigger) { this.trigger = trigger; }
    public void setStyle(String style) { this.style = style; }
    public void setActivity(int activity) { this.activity = Math.max(0, Math.min(9, activity)); }
    public void setAimPoint(String aimPoint) { this.aimPoint = aimPoint; }
    public void setDefensePoint(String defensePoint) { this.defensePoint = defensePoint; }
    
    /**
     * Convert to Map for JSON serialization.
     */
    public java.util.Map<String, Object> toMap() {
        java.util.Map<String, Object> map = new java.util.HashMap<>();
        map.put("trigger", trigger);
        map.put("style", style);
        map.put("activity", activity);
        map.put("aim_point", aimPoint);
        map.put("defense_point", defensePoint);
        return map;
    }
    
    /**
     * Create from Map (for JSON deserialization).
     */
    @SuppressWarnings("unchecked")
    public static Strategy fromMap(java.util.Map<String, Object> data) {
        return new Strategy(
            (String) data.getOrDefault("trigger", "Always"),
            (String) data.getOrDefault("style", "Strike"),
            ((Number) data.getOrDefault("activity", 5)).intValue(),
            (String) data.getOrDefault("aim_point", "None"),
            (String) data.getOrDefault("defense_point", "Chest")
        );
    }
    
    /**
     * Format one strategy row for display.
     */
    public String display(int index) {
        return String.format("  %d   | %-32s | %-18s | Act:%d | Aim:%-14s | Def:%s",
            index, trigger, style, activity, aimPoint, defensePoint);
    }
}
