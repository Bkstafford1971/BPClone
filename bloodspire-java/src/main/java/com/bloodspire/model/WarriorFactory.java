package com.bloodspire.model;

import java.util.*;

/**
 * Factory class for creating Warrior instances.
 * Contains AI rollup logic, base stat generation, and favorite weapon assignment.
 */
public class WarriorFactory {
    
    // Base stat generation constants
    private static final int BASE_STAT_MIN = 3;
    private static final int BASE_STAT_MAX = 21;
    private static final int BASE_STAT_TOTAL = 55;
    
    private static final Random RANDOM = new Random();
    
    /**
     * Create a fully formed AI warrior with procedurally generated stats.
     * Used for rival managers, replacement warriors, and scaled peasants.
     */
    public static Warrior createWarriorAI(String raceName, String name, String gender) {
        if (raceName == null) {
            List<String> races = Race.getPlayableRaces();
            raceName = races.get(RANDOM.nextInt(races.size()));
        }
        
        if (name == null) {
            name = "Fighter_" + (1000 + RANDOM.nextInt(9000));
        }
        
        if (gender == null) {
            gender = RANDOM.nextBoolean() ? "Male" : "Female";
        }
        
        Map<String, Integer> baseStats = generateBaseStats();
        Map<String, Integer> finalStats = aiRollup(baseStats, raceName);
        
        Warrior w = new Warrior(
            name, raceName, gender,
            finalStats.get("strength"),
            finalStats.get("dexterity"),
            finalStats.get("constitution"),
            finalStats.get("intelligence"),
            finalStats.get("presence"),
            finalStats.get("size")
        );
        
        w.setLuck(RANDOM.nextInt(30) + 1);
        assignFavoriteWeapon(w);
        
        return w;
    }
    
    public static Warrior createWarriorAI(String raceName, String gender) {
        return createWarriorAI(raceName, null, gender);
    }
    
    public static Warrior createWarriorAI() {
        return createWarriorAI(null, null, null);
    }
    
    /**
     * Generate 6 base stats that sum to exactly BASE_STAT_TOTAL (55),
     * with each individual stat in the range [BASE_STAT_MIN, BASE_STAT_MAX] (3-21).
     */
    private static Map<String, Integer> generateBaseStats() {
        int remaining = BASE_STAT_TOTAL - BASE_STAT_MIN * Warrior.ATTRIBUTES.size(); // = 37
        
        Map<String, Integer> stats = new LinkedHashMap<>();
        for (String attr : Warrior.ATTRIBUTES) {
            stats.put(attr, BASE_STAT_MIN);
        }
        
        while (remaining > 0) {
            List<String> available = new ArrayList<>();
            for (String attr : Warrior.ATTRIBUTES) {
                if (stats.get(attr) < BASE_STAT_MAX) {
                    available.add(attr);
                }
            }
            if (available.isEmpty()) break;
            
            String chosen = available.get(RANDOM.nextInt(available.size()));
            stats.put(chosen, stats.get(chosen) + 1);
            remaining--;
        }
        
        // Light shuffle: randomly redistribute small amounts between pairs
        List<String> attrs = new ArrayList<>(Warrior.ATTRIBUTES);
        for (int i = 0; i < 12; i++) {
            Collections.shuffle(attrs);
            String a = attrs.get(0);
            String b = attrs.get(1);
            int shift = RANDOM.nextInt(3) + 1;
            int canTake = stats.get(a) - BASE_STAT_MIN;
            int canGive = BASE_STAT_MAX - stats.get(b);
            int actual = Math.min(shift, Math.min(canTake, canGive));
            if (actual > 0) {
                stats.put(a, stats.get(a) - actual);
                stats.put(b, stats.get(b) + actual);
            }
        }
        
        return stats;
    }
    
    /**
     * Return the maximum points a player may add to a single attribute.
     */
    private static int maxAddable(Map<String, Integer> baseStats, String attr) {
        return Math.min(Warrior.ROLLUP_MAX_PER_STAT, 
                       Warrior.STAT_MAX - baseStats.getOrDefault(attr, BASE_STAT_MIN));
    }
    
    /**
     * Distribute 16 rollup points for an AI warrior, weighted by race preference.
     */
    private static Map<String, Integer> aiRollup(Map<String, Integer> baseStats, String raceName) {
        // Stat weight tables per race
        Map<String, Map<String, Integer>> raceWeights = Map.ofEntries(
            Map.entry("Human", Map.ofEntries(
                Map.entry("strength", 2), Map.entry("dexterity", 2), Map.entry("constitution", 3),
                Map.entry("intelligence", 2), Map.entry("presence", 2), Map.entry("size", 2)
            )),
            Map.entry("Half-Orc", Map.ofEntries(
                Map.entry("strength", 4), Map.entry("dexterity", 1), Map.entry("constitution", 2),
                Map.entry("intelligence", 1), Map.entry("presence", 1), Map.entry("size", 4)
            )),
            Map.entry("Halfling", Map.ofEntries(
                Map.entry("strength", 1), Map.entry("dexterity", 5), Map.entry("constitution", 2),
                Map.entry("intelligence", 2), Map.entry("presence", 2), Map.entry("size", 1)
            )),
            Map.entry("Dwarf", Map.ofEntries(
                Map.entry("strength", 3), Map.entry("dexterity", 2), Map.entry("constitution", 4),
                Map.entry("intelligence", 1), Map.entry("presence", 1), Map.entry("size", 2)
            )),
            Map.entry("Half-Elf", Map.ofEntries(
                Map.entry("strength", 2), Map.entry("dexterity", 3), Map.entry("constitution", 2),
                Map.entry("intelligence", 2), Map.entry("presence", 2), Map.entry("size", 2)
            )),
            Map.entry("Elf", Map.ofEntries(
                Map.entry("strength", 1), Map.entry("dexterity", 5), Map.entry("constitution", 2),
                Map.entry("intelligence", 2), Map.entry("presence", 2), Map.entry("size", 1)
            ))
        );
        
        Map<String, Integer> weights = raceWeights.getOrDefault(raceName, 
            Warrior.ATTRIBUTES.stream().collect(HashMap::new, (m, a) -> m.put(a, 2), HashMap::putAll));
        
        Map<String, Integer> additions = new LinkedHashMap<>();
        for (String attr : Warrior.ATTRIBUTES) {
            additions.put(attr, 0);
        }
        
        int remaining = Warrior.ROLLUP_POINTS;
        
        while (remaining > 0) {
            List<String> available = new ArrayList<>();
            for (String attr : Warrior.ATTRIBUTES) {
                if (additions.get(attr) < maxAddable(baseStats, attr)) {
                    available.add(attr);
                }
            }
            if (available.isEmpty()) break;
            
            // Weighted random selection
            List<Integer> statWeights = new ArrayList<>();
            for (String a : available) {
                statWeights.add(weights.getOrDefault(a, 1));
            }
            
            String chosen = weightedRandomChoice(available, statWeights);
            additions.put(chosen, additions.get(chosen) + 1);
            remaining--;
        }
        
        // Validate and return final stats
        return validateAdditions(baseStats, additions);
    }
    
    /**
     * Validate additions and return final stats.
     */
    private static Map<String, Integer> validateAdditions(
            Map<String, Integer> baseStats, Map<String, Integer> additions) {
        
        Map<String, Integer> result = new LinkedHashMap<>();
        for (String attr : Warrior.ATTRIBUTES) {
            int base = baseStats.getOrDefault(attr, BASE_STAT_MIN);
            int added = additions.getOrDefault(attr, 0);
            int finalVal = Math.max(Warrior.STAT_MIN, 
                          Math.min(Warrior.STAT_MAX, base + added));
            result.put(attr, finalVal);
        }
        return result;
    }
    
    /**
     * Select a random element from a list using weighted probabilities.
     */
    private static <T> T weightedRandomChoice(List<T> items, List<Integer> weights) {
        int totalWeight = weights.stream().mapToInt(Integer::intValue).sum();
        int random = RANDOM.nextInt(totalWeight);
        int cumulative = 0;
        
        for (int i = 0; i < items.size(); i++) {
            cumulative += weights.get(i);
            if (random < cumulative) {
                return items.get(i);
            }
        }
        return items.get(items.size() - 1); // Fallback
    }
    
    /**
     * Assign a favorite weapon to a warrior based on their race and stats.
     */
    public static void assignFavoriteWeapon(Warrior warrior) {
        String raceName = warrior.getRace().getName();
        int strVal = warrior.getStrength();
        int dexVal = warrior.getDexterity();
        
        // Define weapon pools per race
        Map<String, List<String>> raceWeapons = Map.ofEntries(
            Map.entry("Tabaxi", List.of("Dagger", "Short Sword", "Scimitar", "Hatchet", 
                                        "Javelin", "Stiletto", "Bola", "Heavy Barbed Whip")),
            Map.entry("Half-Orc", List.of("War Flail", "Great Axe", "Great Sword", "War Hammer",
                                          "Great Pick", "Battle Flail", "Maul")),
            Map.entry("Dwarf", List.of("Battle Axe", "War Hammer", "Boar Spear", "Long Spear",
                                       "Target Shield", "Halberd")),
            Map.entry("Elf", List.of("Dagger", "Short Sword", "Stiletto", "Javelin", "Epee", "Scimitar")),
            Map.entry("Halfling", List.of("Dagger", "Short Sword", "Hatchet", "Buckler", 
                                          "Open Hand", "Knife")),
            Map.entry("Human", List.of("Short Sword", "Military Pick", "Morning Star", 
                                       "Boar Spear", "War Hammer")),
            Map.entry("Goblin", List.of("Dagger", "Short Sword", "Hatchet", "Javelin", "Bola")),
            Map.entry("Gnome", List.of("Short Sword", "Longsword", "Hammer", "War Hammer", "Mace")),
            Map.entry("Lizardfolk", List.of("Short Spear", "Long Spear", "Trident", "War Hammer",
                                            "Battle Axe", "Open Hand"))
        );
        
        List<String> availableWeapons = raceWeapons.getOrDefault(raceName, raceWeapons.get("Human"));
        
        Set<String> lightWeapons = Set.of("Dagger", "Stiletto", "Knife", "Short Sword", "Javelin",
                                          "Epee", "Hatchet", "Buckler", "Bola", "Open Hand");
        Set<String> heavyWeapons = Set.of("Maul", "Great Axe", "War Flail", "Great Sword", "Great Pick",
                                          "Battle Flail", "War Hammer", "Long Spear", "Halberd");
        
        // Build weighted choices
        List<String> weapons = new ArrayList<>();
        List<Double> weights = new ArrayList<>();
        
        for (String weaponName : availableWeapons) {
            double weight = 1.0;
            
            if (lightWeapons.contains(weaponName)) {
                double dexBonus = Math.max(0, dexVal - 12) * 0.1;
                weight = 1.0 + dexBonus;
            }
            
            if (heavyWeapons.contains(weaponName)) {
                double strBonus = Math.max(0, strVal - 12) * 0.1;
                weight = 1.0 + strBonus;
            }
            
            weapons.add(weaponName);
            weights.add(weight);
        }
        
        if (!weapons.isEmpty()) {
            String favorite = weightedRandomChoiceDouble(weapons, weights);
            warrior.setFavoriteWeapon(favorite);
        } else {
            warrior.setFavoriteWeapon("Open Hand");
        }
    }
    
    /**
     * Select a random element from a list using weighted probabilities (double weights).
     */
    private static <T> T weightedRandomChoiceDouble(List<T> items, List<Double> weights) {
        double totalWeight = weights.stream().mapToDouble(Double::doubleValue).sum();
        double random = RANDOM.nextDouble() * totalWeight;
        double cumulative = 0.0;
        
        for (int i = 0; i < items.size(); i++) {
            cumulative += weights.get(i);
            if (random < cumulative) {
                return items.get(i);
            }
        }
        return items.get(items.size() - 1); // Fallback
    }
}
