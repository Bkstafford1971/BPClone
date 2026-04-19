package com.bloodspire.model;

import java.util.*;

/**
 * Utility class for weapon-related operations.
 * Contains the strength carry weight table and weapon lookup helpers.
 */
public class WeaponsUtil {
    
    /**
     * Strength → Max Carry Weight Table
     * Directly from the player's guide.
     * Each tuple is (min_str, max_str, capacity)
     */
    private static final List<StrengthRange> STRENGTH_CARRY_TABLE = Arrays.asList(
        new StrengthRange(3,  3,  0.0),
        new StrengthRange(4,  6,  1.0),
        new StrengthRange(7,  8,  2.0),
        new StrengthRange(9,  11, 3.0),
        new StrengthRange(12, 13, 4.0),
        new StrengthRange(14, 16, 5.0),
        new StrengthRange(17, 18, 6.0),
        new StrengthRange(19, 21, 7.0),
        new StrengthRange(22, 23, 8.0),
        new StrengthRange(24, 25, 9.0)
    );
    
    /**
     * Return the maximum weapon weight a warrior can wield one-handed
     * based on their Strength. Two-handed weapons get a +1 weight allowance
     * (applied at equip time, not here).
     */
    public static double maxWeaponWeight(int strength) {
        for (StrengthRange range : STRENGTH_CARRY_TABLE) {
            if (strength >= range.minStr && strength <= range.maxStr) {
                return range.capacity;
            }
        }
        return 0.0;
    }
    
    /**
     * Calculate the under-strength penalty fraction (0.0 = no penalty, 1.0 = unusable).
     */
    public static double strengthPenalty(double weaponWeight, int strength, boolean twoHanded) {
        double capacity = maxWeaponWeight(strength) + (twoHanded ? 1.0 : 0.0);
        if (weaponWeight <= capacity) {
            return 0.0;
        }
        if (capacity <= 0) {
            return 1.0;
        }
        double overage = weaponWeight - capacity;
        return Math.min(1.0, overage / capacity);
    }
    
    /**
     * Get a weapon by name from the Weapons class.
     * Delegates to Weapons.getWeapon() for lookup.
     */
    public static Weapon getWeaponByName(String name) {
        return Weapons.getWeapon(name);
    }
    
    // Helper class for strength ranges
    private static class StrengthRange {
        final int minStr;
        final int maxStr;
        final double capacity;
        
        StrengthRange(int minStr, int maxStr, double capacity) {
            this.minStr = minStr;
            this.maxStr = maxStr;
            this.capacity = capacity;
        }
    }
}
