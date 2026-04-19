package com.bloodspire.model;

import java.util.*;

/**
 * Utility class for armor-related operations.
 * Contains all armor definitions and lookup helpers.
 */
public class ArmorUtil {
    
    // All armors stored in a map by name
    private static final Map<String, ArmorPiece> ARMORS = new LinkedHashMap<>();
    private static final Map<String, ArmorPiece> HELMS = new LinkedHashMap<>();
    
    // Static initializer to populate all armors
    static {
        // Body Armors
        putArmor(new ArmorPiece("none", 0.0, 0, false, false, 0, "No armor worn"));
        putArmor(new ArmorPiece("leather_jerkin", 2.0, 2, false, false, 0, "Light leather protection"));
        putArmor(new ArmorPiece("studded_leather", 3.5, 3, false, false, 1, "Reinforced leather with metal studs"));
        putArmor(new ArmorPiece("ring_mail", 5.0, 4, false, true, 2, "Metal rings sewn onto fabric"));
        putArmor(new ArmorPiece("chain_mail", 7.0, 5, false, true, 3, "Interlocking metal chains"));
        putArmor(new ArmorPiece("scale_mail", 8.0, 6, false, true, 3, "Overlapping metal scales"));
        putArmor(new ArmorPiece("plate_mail", 10.0, 7, false, true, 4, "Heavy plate armor"));
        putArmor(new ArmorPiece("full_plate", 12.0, 8, false, true, 5, "Complete plate coverage"));
        
        // Helms
        putHelm(new ArmorPiece("none", 0.0, 0, true, false, 0, "No helm worn"));
        putHelm(new ArmorPiece("leather_cap", 1.0, 1, true, false, 0, "Simple leather head protection"));
        putHelm(new ArmorPiece("steel_cap", 2.0, 2, true, false, 1, "Basic steel helm"));
        putHelm(new ArmorPiece("helm", 3.5, 3, true, true, 2, "Standard metal helm"));
        putHelm(new ArmorPiece("great_helm", 5.0, 4, true, true, 3, "Heavy full-coverage helm"));
    }
    
    private static void putArmor(ArmorPiece armor) {
        if (!armor.isHelm()) {
            ARMORS.put(armor.getName(), armor);
        }
    }
    
    private static void putHelm(ArmorPiece helm) {
        if (helm.isHelm()) {
            HELMS.put(helm.getName(), helm);
        }
    }
    
    /**
     * Get armor by name (case-insensitive).
     */
    public static ArmorPiece getArmorByName(String name) {
        if (name == null) return null;
        String normalizedName = name.toLowerCase().replace(" ", "_");
        
        // Try exact match first
        if (ARMORS.containsKey(normalizedName)) {
            return ARMORS.get(normalizedName);
        }
        
        // Try case-insensitive search
        for (ArmorPiece armor : ARMORS.values()) {
            if (armor.getName().equalsIgnoreCase(name) || 
                armor.getName().replace("_", " ").equalsIgnoreCase(name)) {
                return armor;
            }
        }
        
        // Return none if not found
        return ARMORS.get("none");
    }
    
    /**
     * Get helm by name (case-insensitive).
     */
    public static ArmorPiece getHelmByName(String name) {
        if (name == null) return null;
        String normalizedName = name.toLowerCase().replace(" ", "_");
        
        // Try exact match first
        if (HELMS.containsKey(normalizedName)) {
            return HELMS.get(normalizedName);
        }
        
        // Try case-insensitive search
        for (ArmorPiece helm : HELMS.values()) {
            if (helm.getName().equalsIgnoreCase(name) ||
                helm.getName().replace("_", " ").equalsIgnoreCase(name)) {
                return helm;
            }
        }
        
        // Return none if not found
        return HELMS.get("none");
    }
    
    /**
     * Get all body armors.
     */
    public static List<ArmorPiece> getAllArmors() {
        return new ArrayList<>(ARMORS.values());
    }
    
    /**
     * Get all helms.
     */
    public static List<ArmorPiece> getAllHelms() {
        return new ArrayList<>(HELMS.values());
    }
    
    /**
     * Get all armor pieces (both body and helm).
     */
    public static List<ArmorPiece> getAllArmorPieces() {
        List<ArmorPiece> all = new ArrayList<>();
        all.addAll(ARMORS.values());
        all.addAll(HELMS.values());
        return all;
    }
}
