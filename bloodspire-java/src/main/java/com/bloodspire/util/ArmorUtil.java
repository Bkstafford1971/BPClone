package com.bloodspire.util;

import com.bloodspire.model.ArmorPiece;
import java.util.*;

public class ArmorUtil {
    
    private static final Map<String, List<ArmorPiece>> ARMOR_BY_LOCATION = new HashMap<>();
    
    static {
        initializeArmorMap();
    }
    
    private static void initializeArmorMap() {
        // Initialize armor pieces by location
        // This is a simplified version - full implementation would have all armor pieces
        ARMOR_BY_LOCATION.put("head", Arrays.asList(
            new ArmorPiece("Leather Cap", 1, 0.5, "head"),
            new ArmorPiece("Chain Coif", 2, 1.5, "head"),
            new ArmorPiece("Steel Helm", 3, 2.5, "head")
        ));
        
        ARMOR_BY_LOCATION.put("chest", Arrays.asList(
            new ArmorPiece("Leather Vest", 2, 1.0, "chest"),
            new ArmorPiece("Chain Hauberk", 4, 3.0, "chest"),
            new ArmorPiece("Plate Cuirass", 6, 5.0, "chest")
        ));
        
        ARMOR_BY_LOCATION.put("arms", Arrays.asList(
            new ArmorPiece("Leather Bracers", 1, 0.3, "arms"),
            new ArmorPiece("Chain Vambraces", 2, 1.0, "arms"),
            new ArmorPiece("Plate Vambraces", 3, 2.0, "arms")
        ));
        
        ARMOR_BY_LOCATION.put("legs", Arrays.asList(
            new ArmorPiece("Leather Greaves", 1, 0.5, "legs"),
            new ArmorPiece("Chain Chausses", 3, 2.0, "legs"),
            new ArmorPiece("Plate Greaves", 4, 3.5, "legs")
        ));
    }
    
    public static List<ArmorPiece> getArmorForLocation(String location) {
        return ARMOR_BY_LOCATION.getOrDefault(location.toLowerCase(), new ArrayList<>());
    }
    
    public static Optional<ArmorPiece> findArmorByName(String name) {
        for (List<ArmorPiece> armors : ARMOR_BY_LOCATION.values()) {
            for (ArmorPiece armor : armors) {
                if (armor.getName().equalsIgnoreCase(name)) {
                    return Optional.of(armor);
                }
            }
        }
        return Optional.empty();
    }
    
    public static int getTotalArmorValue(List<ArmorPiece> equipped) {
        if (equipped == null) return 0;
        return equipped.stream().mapToInt(ArmorPiece::getProtection).sum();
    }
    
    public static double getTotalWeight(List<ArmorPiece> equipped) {
        if (equipped == null) return 0.0;
        return equipped.stream().mapToDouble(ArmorPiece::getWeight).sum();
    }
}
