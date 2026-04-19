package com.bloodspire.model;

/**
 * One row in a warrior's strategy table.
 * A warrior may have up to 6 of these, read top-to-bottom each minute.
 */
public class WarriorStrategy {
    
    private String trigger;
    private String style;
    private int activity;
    private String aimPoint;
    private String defensePoint;
    
    public WarriorStrategy() {
        this("Always", "Strike", 5, "None", "Chest");
    }
    
    public WarriorStrategy(String trigger, String style, int activity, 
                          String aimPoint, String defensePoint) {
        this.trigger = trigger;
        this.style = style;
        this.activity = Math.max(0, Math.min(9, activity)); // Clamp 0-9
        this.aimPoint = aimPoint;
        this.defensePoint = defensePoint;
    }
    
    // Getters and Setters
    public String getTrigger() { return trigger; }
    public void setTrigger(String trigger) { this.trigger = trigger; }
    
    public String getStyle() { return style; }
    public void setStyle(String style) { this.style = style; }
    
    public int getActivity() { return activity; }
    public void setActivity(int activity) { 
        this.activity = Math.max(0, Math.min(9, activity));
    }
    
    public String getAimPoint() { return aimPoint; }
    public void setAimPoint(String aimPoint) { this.aimPoint = aimPoint; }
    
    public String getDefensePoint() { return defensePoint; }
    public void setDefensePoint(String defensePoint) { this.defensePoint = defensePoint; }
    
    /**
     * Format one strategy row for display.
     */
    public String display(String index) {
        return String.format(
            "  %-3s | %-32s | %-18s | Act:%d | Aim:%-14s | Def:%s",
            index, trigger, style, activity, aimPoint, defensePoint
        );
    }
}
