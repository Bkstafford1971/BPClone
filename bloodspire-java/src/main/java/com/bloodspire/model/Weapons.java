package com.bloodspire.model;

import java.util.*;

/**
 * Contains all weapon definitions and lookup helpers.
 * Mirrors the WEAPONS dictionary and helper functions from weapons.py
 */
public class Weapons {
    
    // All weapons stored in a map by skill_key
    private static final Map<String, Weapon> WEAPONS = new LinkedHashMap<>();
    
    // Static initializer to populate all weapons
    static {
        
        // =========================================================================
        // OPEN HAND (special)
        // =========================================================================
        put(new Weapon(
            "open_hand", "Open Hand", 0.0, false, false, Weapon.ODDBALL,
            false, true, false, false, false, false, false,
            Arrays.asList("Strike", "Martial Combat"),
            null,
            "Works surprisingly well in Strike and MC styles, but damage is anemic without high Brawl skill. Assign to secondary for two-handed use."
        ));
        
        // =========================================================================
        // SWORDS & KNIVES
        // =========================================================================
        
        put(new Weapon(
            "stiletto", "Stiletto", 1.0, true, false, Weapon.SWORD_KNIFE,
            true, true, false, false, false, false, false,
            Arrays.asList("Lunge", "Martial Combat", "Calculated Attack"),
            Arrays.asList("Bash", "Total Kill"),
            "Very high attack rate. Good for weak warriors against heavy armor. Ultimately does too little damage for high-level play. Halflings like it."
        ));
        
        put(new Weapon(
            "knife", "Knife", 1.5, true, false, Weapon.SWORD_KNIFE,
            false, true, false, false, false, false, false,
            Arrays.asList("Strike", "Lunge"),
            null,
            "Attack rate underwhelming for its size. Few warriors succeed with this."
        ));
        
        put(new Weapon(
            "dagger", "Dagger", 2.0, true, false, Weapon.SWORD_KNIFE,
            false, true, false, false, false, false, false,
            Arrays.asList("Lunge", "Wall of Steel", "Martial Combat"),
            null,
            "Very high attack rate. Good in the hands of Elves. Like all small weapons, insufficient damage at the high end."
        ));
        
        put(new Weapon(
            "short_sword", "Short Sword", 3.0, false, false, Weapon.SWORD_KNIFE,
            false, false, false, false, false, false, false,
            Arrays.asList("Wall of Steel", "Strike", "Lunge", "Counterstrike"),
            null,
            "One of the ultimate weapons. Effective with popular styles for almost any warrior. Dual Short Sword Elves in Wall of Steel remain top-tier. The 'Pocket Rocket' Halfling build with a single Short Sword is iconic."
        ));
        
        put(new Weapon(
            "epee", "Epee", 3.0, false, false, Weapon.SWORD_KNIFE,
            false, false, false, false, true, false, false,
            Arrays.asList("Lunge", "Engage & Withdraw", "Sure Strike"),
            Arrays.asList("Bash", "Total Kill"),
            "Good attack rate. Decent at disarm. Same late-game damage problem as other light weapons. Effective in first 50 fights played right."
        ));
        
        put(new Weapon(
            "scimitar", "Scimitar", 3.5, false, false, Weapon.SWORD_KNIFE,
            false, false, false, false, false, false, false,
            Arrays.asList("Slash", "Lunge", "Wall of Steel"),
            null,
            "The natural weapon of the Elf. With proper Dexterity, attack rate is more than adequate. Damage in the mid range. Good all-around."
        ));
        
        put(new Weapon(
            "longsword", "Long Sword", 3.2, false, false, Weapon.SWORD_KNIFE,
            false, false, false, false, false, false, false,
            Arrays.asList("Strike", "Counterstrike", "Slash"),
            null,
            "Attack rate a little slower than expected. Damage low until skilled. Elves, Half-Elves, and Humans appear most effective."
        ));
        
        put(new Weapon(
            "broad_sword", "Broad Sword", 3.8, false, false, Weapon.SWORD_KNIFE,
            false, false, false, false, false, false, false,
            Arrays.asList("Strike", "Slash", "Counterstrike"),
            null,
            "Not bad, not great. Likes high Dexterity and Elves/Half-Elves. Needs a bit more than nominal Strength to fully utilize."
        ));
        
        put(new Weapon(
            "bastard_sword", "Bastard Sword", 4.8, false, true, Weapon.SWORD_KNIFE,
            false, false, false, false, false, false, false,
            Arrays.asList("Slash", "Strike", "Wall of Steel"),
            null,
            "High attack rate for a heavy weapon. Excellent with Slash. Lacks consistent high damage hits for its size. Half-Elves love it."
        ));
        
        put(new Weapon(
            "great_sword", "Great Sword", 6.8, false, true, Weapon.SWORD_KNIFE,
            false, false, false, false, false, false, false,
            Arrays.asList("Slash", "Total Kill", "Bash"),
            Arrays.asList("Lunge", "Calculated Attack"),
            "In the hands of Half-Orcs, incredible. Stat requirements are very high but well worth it."
        ));
        
        // =========================================================================
        // AXES & PICKS
        // =========================================================================
        
        put(new Weapon(
            "hatchet", "Hatchet", 1.8, true, false, Weapon.AXE_PICK,
            false, false, false, false, false, false, false,
            Arrays.asList("Strike", "Wall of Steel", "Opportunity Throw"),
            null,
            "Light, fast, great early. Fails to deliver damage in later fights. Halflings like it."
        ));
        
        put(new Weapon(
            "francisca", "Fransisca", 2.5, true, false, Weapon.AXE_PICK,
            false, false, false, false, false, false, false,
            Arrays.asList("Strike", "Bash", "Opportunity Throw"),
            null,
            "Consistently average for most. Dwarves can excel with it."
        ));
        
        put(new Weapon(
            "battle_axe", "Battle Axe", 4.5, false, false, Weapon.AXE_PICK,
            false, false, false, false, false, false, false,
            Arrays.asList("Counterstrike", "Bash", "Strike"),
            Arrays.asList("Wall of Steel"),
            "Decent damage but attack rate slightly too slow for top-tier. Good for Counterstrike users. Excellent for low-DEX, high-STR Dwarves."
        ));
        
        put(new Weapon(
            "great_axe", "Great Axe", 6.0, false, true, Weapon.AXE_PICK,
            false, false, false, false, false, false, false,
            Arrays.asList("Bash", "Total Kill", "Slash"),
            null,
            "Like the Great Sword for Half-Orcs: can do staggering damage. Attack rate low due to size. Very high stat requirements."
        ));
        
        put(new Weapon(
            "small_pick", "Small Pick", 2.8, false, false, Weapon.AXE_PICK,
            true, false, false, false, false, false, false,
            Arrays.asList("Lunge", "Calculated Attack", "Strike"),
            null,
            "Fast and effective early, starts becoming ineffective around fight 50. Humans and Halflings."
        ));
        
        put(new Weapon(
            "military_pick", "Military Pick", 3.5, false, false, Weapon.AXE_PICK,
            true, false, false, false, false, false, false,
            Arrays.asList("Calculated Attack", "Strike", "Lunge"),
            null,
            "A Human favorite. Very effective in higher fights once opponents have graduated to Scale and above. Works in many popular styles."
        ));
        
        put(new Weapon(
            "pick_axe", "Pick Axe", 4.8, false, true, Weapon.AXE_PICK,
            true, false, false, false, false, false, false,
            Arrays.asList("Bash", "Calculated Attack"),
            null,
            "New to the Pit. Insufficient data to characterize."
        ));
        
        // =========================================================================
        // HAMMERS & MACES
        // =========================================================================
        
        put(new Weapon(
            "hammer", "Hammer", 2.0, true, false, Weapon.HAMMER_MACE,
            false, false, false, false, false, false, false,
            Arrays.asList("Bash", "Strike", "Opportunity Throw"),
            null,
            "Above-average damage and attack rate. Viability in late fights debated. Halflings and Humans."
        ));
        
        put(new Weapon(
            "mace", "Mace", 3.0, false, false, Weapon.HAMMER_MACE,
            false, false, false, false, false, false, false,
            Arrays.asList("Bash", "Strike"),
            null,
            "Terribly inconsistent. The Epee of the hammer family."
        ));
        
        put(new Weapon(
            "morningstar", "Morningstar", 4.0, false, false, Weapon.HAMMER_MACE,
            false, false, false, false, false, false, false,
            Arrays.asList("Bash", "Strike", "Counterstrike"),
            null,
            "One of the great weapons. Consistent high damage once minimums met. Effective for all races."
        ));
        
        put(new Weapon(
            "war_hammer", "War Hammer", 4.5, false, false, Weapon.HAMMER_MACE,
            false, false, false, false, false, false, false,
            Arrays.asList("Bash", "Total Kill", "Strike"),
            null,
            "A Half-Orc favorite. Good weapon in the right hands. Requires 20+ Strength to truly 'sing'."
        ));
        
        put(new Weapon(
            "maul", "Maul", 7.5, false, true, Weapon.HAMMER_MACE,
            false, false, false, false, false, false, false,
            Arrays.asList("Total Kill", "Bash"),
            Arrays.asList("Wall of Steel", "Lunge"),
            "Too slow to be effective; lacks the defenses to compensate. Requires very high Strength."
        ));
        
        put(new Weapon(
            "club", "Club", 2.7, false, false, Weapon.HAMMER_MACE,
            false, false, false, false, false, false, false,
            Arrays.asList("Bash", "Strike"),
            null,
            "A simple length of heavy wood, sometimes reinforced with metal bands. Brutal and straightforward. Favored by dirty fighters and beginners alike."
        ));
        
        // =========================================================================
        // POLEARMS & SPEARS
        // =========================================================================
        
        put(new Weapon(
            "short_spear", "Short Spear", 3.0, true, false, Weapon.POLEARM_SPEAR,
            false, false, false, true, false, false, false,
            Arrays.asList("Lunge", "Wall of Steel", "Strike", "Opportunity Throw"),
            null,
            "Light and potent weapon. Effective in Lunge, Wall of Steel, and Strike. Can throw. Use with a shield. Great attack rate and average to above average damage. Favored by all races."
        ));
        
        put(new Weapon(
            "boar_spear", "Boar Spear", 3.8, true, false, Weapon.POLEARM_SPEAR,
            false, false, false, true, false, false, false,
            Arrays.asList("Lunge", "Wall of Steel", "Strike", "Opportunity Throw"),
            null,
            "Arguably the best weapon in the game. Effective in Lunge, Wall of Steel, and Strike. Can throw. Use with a shield. Great attack rate and damage. Favored by all races."
        ));
        
        put(new Weapon(
            "long_spear", "Long Spear", 4.2, false, true, Weapon.POLEARM_SPEAR,
            false, false, false, true, false, false, false,
            Arrays.asList("Lunge", "Strike", "Wall of Steel"),
            null,
            "Good in Half-Elves and some Half-Orcs. Same advantages as Boar Spear with more damage kick. Excels at 7+ APM."
        ));
        
        put(new Weapon(
            "pole_axe", "Pole Axe", 5.5, false, true, Weapon.POLEARM_SPEAR,
            false, false, false, true, false, false, false,
            Arrays.asList("Strike", "Lunge", "Wall of Steel"),
            null,
            "A Half-Elf favorite that underperforms for other races. Half-Orcs have had decent success with it."
        ));
        
        put(new Weapon(
            "halberd", "Halberd", 7.5, false, true, Weapon.POLEARM_SPEAR,
            false, false, false, true, false, false, false,
            Arrays.asList("Total Kill", "Engage & Withdraw"),
            null,
            "Tough to use but certain Half-Orcs devastate with it. Requires very high Strength. Also known to work with Engage & Withdraw."
        ));
        
        // =========================================================================
        // FLAILS
        // =========================================================================
        
        put(new Weapon(
            "flail", "Flail", 2.6, false, false, Weapon.FLAIL,
            false, false, true, false, false, true, false,
            Arrays.asList("Strike", "Wall of Steel", "Bash"),
            null,
            "Unique: most of its damage is based on SIZE not STR. Elves like Flails; most races do well."
        ));
        
        put(new Weapon(
            "bladed_flail", "Bladed Flail", 4.0, false, false, Weapon.FLAIL,
            false, false, true, false, false, true, false,
            Arrays.asList("Bash", "Strike", "Wall of Steel"),
            null,
            "Halflings and Half-Orcs love it. Great damage against light armor; huge drop-off against Scale+. Hard to use as a top-tier late weapon."
        ));
        
        put(new Weapon(
            "war_flail", "War Flail", 5.0, false, false, Weapon.FLAIL,
            false, false, true, false, false, true, false,
            Arrays.asList("Total Kill", "Bash", "Strike"),
            null,
            "One of the best weapons in the game, especially for Half-Orcs. Damage tuned down slightly from original legendary status."
        ));
        
        put(new Weapon(
            "battle_flail", "Battle Flail", 6.5, false, true, Weapon.FLAIL,
            false, false, true, false, false, true, false,
            Arrays.asList("Bash", "Total Kill"),
            Arrays.asList("Lunge", "Calculated Attack"),
            "Half-Elf favorite (extra attack with it). Attack rate too low vs damage rate compared to War Flail. Half-Orcs also succeed."
        ));
        
        // =========================================================================
        // STAVES
        // =========================================================================
        
        put(new Weapon(
            "quarterstaff", "Quarterstaff", 3.0, false, true, Weapon.STAVE,
            false, true, false, false, false, false, false,
            Arrays.asList("Martial Combat", "Strike", "Parry"),
            null,
            "A Halfling favorite. Good with Martial Combat. Currently underwhelming in the Pit."
        ));
        
        put(new Weapon(
            "great_staff", "Great Staff", 5.5, false, true, Weapon.STAVE,
            false, true, false, false, false, false, false,
            Arrays.asList("Martial Combat", "Strike"),
            null,
            "Larger, heavier Quarterstaff. Attack rate lower than expected; too slow for reliable parry."
        ));
        
        // =========================================================================
        // SHIELDS
        // =========================================================================
        
        put(new Weapon(
            "buckler", "Buckler", 2.2, false, false, Weapon.SHIELD,
            false, false, false, false, false, false, true,
            Arrays.asList("Counterstrike", "Parry", "Defend"),
            null,
            "Fairly weak shield. Not really worth using."
        ));
        
        put(new Weapon(
            "target_shield", "Target Shield", 4.2, false, false, Weapon.SHIELD,
            false, false, false, false, false, false, true,
            Arrays.asList("Counterstrike", "Parry", "Defend", "Wall of Steel"),
            null,
            "Current sweet-spot shield for Dwarves."
        ));
        
        put(new Weapon(
            "tower_shield", "Tower Shield", 5.5, false, false, Weapon.SHIELD,
            false, false, false, false, false, false, true,
            Arrays.asList("Counterstrike", "Parry", "Defend"),
            null,
            "Once legendary, now tuned. Only shield that helps against very skilled warriors. Half-Orcs prefer it."
        ));
        
        // =========================================================================
        // ODDBALLS
        // =========================================================================
        
        put(new Weapon(
            "cestus", "Cestus", 1.0, false, false, Weapon.ODDBALL,
            false, true, false, false, false, false, false,
            Arrays.asList("Martial Combat"),
            null,
            "Outside MC, underwhelming. Some Half-Elf Martial Artists get incredible damage with it. Cannot hold another weapon in that hand."
        ));
        
        put(new Weapon(
            "trident", "Trident", 4.3, false, false, Weapon.ODDBALL,
            false, false, false, true, false, false, false,
            Arrays.asList("Lunge", "Strike"),
            null,
            "Once much stronger. Gets good results for Dwarves and Half-Elves. No longer competitive with Boar Spear."
        ));
        
        put(new Weapon(
            "net", "Net", 2.5, false, false, Weapon.ODDBALL,
            false, true, false, false, true, false, false,
            Arrays.asList("Sure Strike", "Wall of Steel"),
            null,
            "Specialty weapon. Success with Dwarves. Throws frustrating entangle attacks. Works with Sure Strike and Wall of Steel. Hit and miss."
        ));
        
        put(new Weapon(
            "scythe", "Scythe", 3.5, false, false, Weapon.ODDBALL,
            true, false, false, false, true, false, false,
            Arrays.asList("Slash", "Calculated Attack", "Lunge"),
            null,
            "Sings in Elf hands. Armor-piercing blade. Can use Slash effectively. Devastating for almost any warrior except Half-Orcs."
        ));
        
        put(new Weapon(
            "great_pick", "Great Pick", 7.5, false, true, Weapon.ODDBALL,
            true, false, false, false, false, false, false,
            Arrays.asList("Total Kill", "Bash", "Calculated Attack"),
            null,
            "In the right Half-Orc or Dwarf hands: unstoppable killing machine. Against light armor (CB or leather) it's like hitting with a wiffle bat."
        ));
        
        put(new Weapon(
            "javelin", "Javelin", 2.5, true, false, Weapon.ODDBALL,
            false, false, false, true, false, false, false,
            Arrays.asList("Lunge", "Opportunity Throw", "Strike"),
            null,
            "Great below 50 fights. Has many Boar Spear benefits at a higher attack rate. Halflings and Elves both like it."
        ));
        
        put(new Weapon(
            "ball_and_chain", "Ball & Chain", 7.5, false, true, Weapon.ODDBALL,
            false, false, true, false, true, true, false,
            Arrays.asList("Total Kill", "Bash"),
            Arrays.asList("Wall of Steel", "Lunge"),
            "Very high damage rate but very low attack rate. Can finish a fight in 2 hits — if you survive the 10 they land first."
        ));
        
        put(new Weapon(
            "bola", "Bola", 3.1, true, false, Weapon.ODDBALL,
            false, false, false, false, false, false, false,
            Arrays.asList("Opportunity Throw", "Bash", "Strike"),
            null,
            "Weighted cords with heavy balls. Can be thrown to entangle legs and cause falls, or swung in melee like a crude flail. Deals only bludgeoning damage."
        ));
        
        put(new Weapon(
            "heavy_whip", "Heavy Barbed Whip", 2.1, false, false, Weapon.ODDBALL,
            false, false, false, false, false, false, false,
            Arrays.asList("Slash", "Engage & Withdraw"),
            null,
            "A long, heavy whip with barbs or hooks. Can lash to slash or wrap around limbs to trip an opponent. Deals a mix of blunt and slashing damage."
        ));
        
        put(new Weapon(
            "swordbreaker", "Swordbreaker", 2.6, false, false, Weapon.ODDBALL,
            false, false, false, false, true, false, false,
            Arrays.asList("Counterstrike", "Decoy"),
            null,
            "Best in off-hand vs bladed weapons. Lack of bladed weapons in the Pit limits its value. Very effective if you know your opponent uses blades."
        ));
    }
    
    // Helper method to add weapon to map
    private static void put(Weapon weapon) {
        WEAPONS.put(weapon.getSkillKey(), weapon);
    }
    
    /**
     * Retrieve a Weapon by skill_key (case-insensitive).
     * @param key the skill key or display name
     * @return the Weapon
     * @throws IllegalArgumentException if not found
     */
    public static Weapon getWeapon(String key) {
        if (key == null) {
            throw new IllegalArgumentException("Weapon key cannot be null");
        }
        
        // Try skill_key first (normalize)
        String normalizedKey = key.toLowerCase().replace(" ", "_").replace("&", "and");
        if (WEAPONS.containsKey(normalizedKey)) {
            return WEAPONS.get(normalizedKey);
        }
        
        // Try display name match
        for (Weapon w : WEAPONS.values()) {
            if (w.getDisplay().equalsIgnoreCase(key)) {
                return w;
            }
        }
        
        throw new IllegalArgumentException(
            "Unknown weapon: '" + key + "'. " +
            "Valid weapons: " + String.join(", ", getWeaponNames())
        );
    }
    
    /**
     * Get all weapons as an unmodifiable map.
     */
    public static Map<String, Weapon> getAllWeapons() {
        return Collections.unmodifiableMap(WEAPONS);
    }
    
    /**
     * Return all weapons that can be thrown.
     */
    public static List<Weapon> throwableWeapons() {
        List<Weapon> result = new ArrayList<>();
        for (Weapon w : WEAPONS.values()) {
            if (w.isThrowable()) {
                result.add(w);
            }
        }
        return result;
    }
    
    /**
     * Return all weapons compatible with Martial Combat style.
     */
    public static List<Weapon> mcWeapons() {
        List<Weapon> result = new ArrayList<>();
        for (Weapon w : WEAPONS.values()) {
            if (w.isMcCompatible()) {
                result.add(w);
            }
        }
        return result;
    }
    
    /**
     * Return all armor-piercing weapons (extra damage vs Scale+).
     */
    public static List<Weapon> armorPiercingWeapons() {
        List<Weapon> result = new ArrayList<>();
        for (Weapon w : WEAPONS.values()) {
            if (w.isArmorPiercing()) {
                result.add(w);
            }
        }
        return result;
    }
    
    /**
     * Return all weapons that can use the charge attack.
     */
    public static List<Weapon> spearWeapons() {
        List<Weapon> result = new ArrayList<>();
        for (Weapon w : WEAPONS.values()) {
            if (w.isChargeAttack()) {
                result.add(w);
            }
        }
        return result;
    }
    
    /**
     * Return all weapons in a given category.
     */
    public static List<Weapon> listWeaponsByCategory(String category) {
        List<Weapon> result = new ArrayList<>();
        for (Weapon w : WEAPONS.values()) {
            if (w.getCategory().equals(category)) {
                result.add(w);
            }
        }
        return result;
    }
    
    /**
     * Return weapons that list a style as preferred.
     */
    public static List<Weapon> weaponsForStyle(String style) {
        List<Weapon> result = new ArrayList<>();
        for (Weapon w : WEAPONS.values()) {
            if (w.getPreferredStyles().contains(style)) {
                result.add(w);
            }
        }
        return result;
    }
    
    /**
     * Get sorted list of all weapon names.
     */
    public static List<String> getWeaponNames() {
        List<String> names = new ArrayList<>();
        for (Weapon w : WEAPONS.values()) {
            names.add(w.getDisplay());
        }
        Collections.sort(names);
        return names;
    }
    
    /**
     * Get total number of weapons.
     */
    public static int getWeaponCount() {
        return WEAPONS.size();
    }
}
