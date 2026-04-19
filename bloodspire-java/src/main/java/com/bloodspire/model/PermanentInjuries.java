package com.bloodspire.model;

import java.util.*;

/**
 * Tracks permanent injury levels for each of the 7 body locations.
 * Level 0 = no injury, Level 9 = fatal.
 */
public class PermanentInjuries {
    
    private int head;
    private int chest;
    private int abdomen;
    private int primaryArm;
    private int secondaryArm;
    private int primaryLeg;
    private int secondaryLeg;
    
    public static final List<String> LOCATIONS = List.of(
        "head", "chest", "abdomen",
        "primary_arm", "secondary_arm",
        "primary_leg", "secondary_leg"
    );
    
    public PermanentInjuries() {
        this.head = 0;
        this.chest = 0;
        this.abdomen = 0;
        this.primaryArm = 0;
        this.secondaryArm = 0;
        this.primaryLeg = 0;
        this.secondaryLeg = 0;
    }
    
    public int get(String location) {
        return switch (location.toLowerCase()) {
            case "head" -> head;
            case "chest" -> chest;
            case "abdomen" -> abdomen;
            case "primary_arm" -> primaryArm;
            case "secondary_arm" -> secondaryArm;
            case "primary_leg" -> primaryLeg;
            case "secondary_leg" -> secondaryLeg;
            default -> 0;
        };
    }
    
    /**
     * Add injury levels to a location.
     * Returns true if the warrior has been slain (any location reaches 9).
     */
    public boolean add(String location, int levels) {
        if (!LOCATIONS.contains(location.toLowerCase())) {
            throw new IllegalArgumentException("Invalid injury location: " + location);
        }
        
        int current = get(location);
        int newLevel = Math.min(9, current + levels);
        
        switch (location.toLowerCase()) {
            case "head" -> head = newLevel;
            case "chest" -> chest = newLevel;
            case "abdomen" -> abdomen = newLevel;
            case "primary_arm" -> primaryArm = newLevel;
            case "secondary_arm" -> secondaryArm = newLevel;
            case "primary_leg" -> primaryLeg = newLevel;
            case "secondary_leg" -> secondaryLeg = newLevel;
        }
        
        return newLevel >= 9;
    }
    
    public boolean isFatal() {
        return head >= 9 || chest >= 9 || abdomen >= 9 ||
               primaryArm >= 9 || secondaryArm >= 9 ||
               primaryLeg >= 9 || secondaryLeg >= 9;
    }
    
    public List<Map.Entry<String, Integer>> activeInjuries() {
        List<Map.Entry<String, Integer>> result = new ArrayList<>();
        for (String loc : LOCATIONS) {
            int level = get(loc);
            if (level > 0) {
                result.add(Map.entry(loc, level));
            }
        }
        return result;
    }
    
    public String summary() {
        List<Map.Entry<String, Integer>> active = activeInjuries();
        if (active.isEmpty()) {
            return "  No permanent injuries.";
        }
        
        StringBuilder sb = new StringBuilder();
        for (Map.Entry<String, Integer> entry : active) {
            String loc = entry.getKey();
            int level = entry.getValue();
            String desc = Warrior.INJURY_DESCRIPTIONS.get(level);
            String display = loc.replace("_", " ").substring(0, 1).toUpperCase() + 
                            loc.replace("_", " ").substring(1);
            sb.append(String.format("  %-16s Level %d — %s%n", display, level, desc));
        }
        return sb.toString().trim();
    }
    
    public Map<String, Integer> toDict() {
        Map<String, Integer> dict = new HashMap<>();
        for (String loc : LOCATIONS) {
            dict.put(loc, get(loc));
        }
        return dict;
    }
    
    public void fromDict(Map<String, Integer> data) {
        for (String loc : LOCATIONS) {
            int level = data.getOrDefault(loc, 0);
            switch (loc.toLowerCase()) {
                case "head" -> head = level;
                case "chest" -> chest = level;
                case "abdomen" -> abdomen = level;
                case "primary_arm" -> primaryArm = level;
                case "secondary_arm" -> secondaryArm = level;
                case "primary_leg" -> primaryLeg = level;
                case "secondary_leg" -> secondaryLeg = level;
            }
        }
    }
}
