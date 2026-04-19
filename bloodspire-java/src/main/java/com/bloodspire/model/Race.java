package com.bloodspire.model;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Defines a single race in BLOODSPIRE.
 */
public class Race {
    private final String name;
    private final boolean isPlayable;
    private final String description;
    private final RacialModifiers modifiers;
    
    // Physical baselines at average SIZE (12-13), male
    private final int baseHeightIn;    // inches
    private final int baseWeightLbs;   // pounds
    
    // Favored/weak enemy races
    private final String favoredEnemyRace;
    private final String weakAgainstRace;
    
    private Race(Builder builder) {
        this.name = builder.name;
        this.isPlayable = builder.isPlayable;
        this.description = builder.description;
        this.modifiers = builder.modifiers;
        this.baseHeightIn = builder.baseHeightIn;
        this.baseWeightLbs = builder.baseWeightLbs;
        this.favoredEnemyRace = builder.favoredEnemyRace;
        this.weakAgainstRace = builder.weakAgainstRace;
    }
    
    // Getters
    public String getName() { return name; }
    public boolean isPlayable() { return isPlayable; }
    public String getDescription() { return description; }
    public RacialModifiers getModifiers() { return modifiers; }
    public int getBaseHeightIn() { return baseHeightIn; }
    public int getBaseWeightLbs() { return baseWeightLbs; }
    public String getFavoredEnemyRace() { return favoredEnemyRace; }
    public String getWeakAgainstRace() { return weakAgainstRace; }
    
    // Builder pattern
    public static class Builder {
        private String name;
        private boolean isPlayable;
        private String description;
        private RacialModifiers modifiers;
        private int baseHeightIn;
        private int baseWeightLbs;
        private String favoredEnemyRace = null;
        private String weakAgainstRace = null;
        
        public Builder name(String val) { this.name = val; return this; }
        public Builder isPlayable(boolean val) { this.isPlayable = val; return this; }
        public Builder description(String val) { this.description = val; return this; }
        public Builder modifiers(RacialModifiers val) { this.modifiers = val; return this; }
        public Builder baseHeightIn(int val) { this.baseHeightIn = val; return this; }
        public Builder baseWeightLbs(int val) { this.baseWeightLbs = val; return this; }
        public Builder favoredEnemyRace(String val) { this.favoredEnemyRace = val; return this; }
        public Builder weakAgainstRace(String val) { this.weakAgainstRace = val; return this; }
        
        public Race build() { return new Race(this); }
    }
    
    // Static registry of all races
    private static final Map<String, Race> RACES = new LinkedHashMap<>();
    
    static {
        initializeRaces();
    }
    
    private static void initializeRaces() {
        // Human
        RACES.put("Human", new Race.Builder()
            .name("Human")
            .isPlayable(true)
            .description("The adaptable everyman. No extreme strengths or weaknesses, but supremely adaptable. Humans train attributes more easily and suffer fewer permanent injuries.")
            .baseHeightIn(67)
            .baseWeightLbs(165)
            .modifiers(new RacialModifiers.Builder()
                .trainsStatsFaster(true)
                .fewerPerms(true)
                .favoredOpponents("All races — Humans fight well against everyone.")
                .disfavoredOpponents("None in particular.")
                .build())
            .build());
        
        // Half-Orc
        RACES.put("Half-Orc", new Race.Builder()
            .name("Half-Orc")
            .isPlayable(true)
            .description("Pure brute force. Devastating damage and high durability, but slow, clumsy, and easy to outmaneuver.")
            .baseHeightIn(75)
            .baseWeightLbs(259)
            .modifiers(new RacialModifiers.Builder()
                .damageBonus(8)
                .hpBonus(6)
                .attackRatePenalty(4)
                .initiativeBonus(-3)
                .dodgePenalty(3)
                .parryPenalty(3)
                .preferredWeapons(Arrays.asList("War Flail", "Great Axe", "Great Sword", "War Hammer", "Battle Flail", "Halberd", "Great Pick", "Tower Shield"))
                .favoredOpponents("Very small opponents.")
                .disfavoredOpponents("Quick warriors with thrusting weapons and good dodge.")
                .build())
            .build());
        
        // Halfling
        RACES.put("Halfling", new Race.Builder()
            .name("Halfling")
            .isPlayable(true)
            .description("Infuriatingly hard to hit. Extremely fast and mobile, but extremely fragile with very light damage output.")
            .baseHeightIn(46)
            .baseWeightLbs(49)
            .modifiers(new RacialModifiers.Builder()
                .dodgeBonus(7)
                .attackRateBonus(4)
                .martialCombatBonus(true)
                .damagePenalty(6)
                .parryPenalty(3)
                .hpBonus(-6)
                .preferredWeapons(Arrays.asList("Short Sword", "Stiletto", "Hatchet", "Quarterstaff", "Javelin", "Bladed Flail", "Hammer"))
                .weakWeapons(Arrays.asList("Maul", "Great Axe", "Great Sword", "Halberd", "Battle Flail", "Ball & Chain"))
                .favoredOpponents("Most opponents — Halflings are balanced offensively and defensively.")
                .disfavoredOpponents("Warriors who specifically fight small opponents well (e.g. Dwarves).")
                .build())
            .build());
        
        // Dwarf
        RACES.put("Dwarf", new Race.Builder()
            .name("Dwarf")
            .isPlayable(true)
            .description("The ultimate tank. Absorbs massive punishment and parries masterfully, but very slow and poor at dodging.")
            .baseHeightIn(50)
            .baseWeightLbs(195)
            .modifiers(new RacialModifiers.Builder()
                .hpBonus(12)
                .damageBonus(3)
                .parryBonus(6)
                .armorCapacityBonus(true)
                .shieldBonus(true)
                .attackRatePenalty(3)
                .dodgePenalty(4)
                .preferredWeapons(Arrays.asList("Battle Axe", "Fransisca", "Great Axe", "Morningstar", "War Hammer", "Boar Spear", "Target Shield", "Net", "Trident"))
                .weakWeapons(Arrays.asList("Halberd", "Pole Axe"))
                .favoredOpponents("Very small and very large opponents — Dwarves have something to prove against both.")
                .disfavoredOpponents("Mid-sized opponents with average stats.")
                .build())
            .build());
        
        // Half-Elf
        RACES.put("Half-Elf", new Race.Builder()
            .name("Half-Elf")
            .isPlayable(true)
            .description("Versatile and capable. Slight edge in weapon handling with no major weaknesses or strengths.")
            .baseHeightIn(64)
            .baseWeightLbs(144)
            .modifiers(new RacialModifiers.Builder()
                .biggerWeaponsBonus(true)
                .attackRateBonus(1)
                .dodgeBonus(2)
                .damageBonus(1)
                .preferredWeapons(Arrays.asList("Pole Axe", "Bastard Sword", "Long Sword", "Scimitar", "Battle Flail", "Scythe", "Javelin", "Broadsword"))
                .favoredOpponents("Average, mid-tier opponents.")
                .disfavoredOpponents("Warriors who can take and dish out a lot of damage — Half-Elves share this weakness with most non-tanks.")
                .build())
            .build());
        
        // Elf
        RACES.put("Elf", new Race.Builder()
            .name("Elf")
            .isPlayable(true)
            .description("Elusive speed demons. Masters of dual-wielding and evasion, but extremely fragile.")
            .baseHeightIn(62)
            .baseWeightLbs(129)
            .modifiers(new RacialModifiers.Builder()
                .dodgeBonus(5)
                .attackRateBonus(5)
                .dualWeaponBonus(true)
                .hpBonus(-7)
                .damagePenalty(2)
                .preferredWeapons(Arrays.asList("Dagger", "Short Sword", "Scimitar", "Scythe", "Flail", "Javelin", "Stiletto", "Epee"))
                .favoredOpponents("Light and medium opponents — small, fast weapons struggle vs heavy armor.")
                .disfavoredOpponents("Large, powerful opponents who can't be taken out with small weapons.")
                .build())
            .build());
        
        // Goblin
        RACES.put("Goblin", new Race.Builder()
            .name("Goblin")
            .isPlayable(true)
            .description("Tiny dirty fighters. Extremely fast and tricky with thrown weapons, but very weak and fragile.")
            .baseHeightIn(42)
            .baseWeightLbs(48)
            .modifiers(new RacialModifiers.Builder()
                .attackRateBonus(5)
                .initiativeBonus(5)
                .dodgeBonus(4)
                .damagePenalty(6)
                .hpBonus(-7)
                .strengthPenalty(4)
                .thrownMastery(true)
                .scavenger(true)
                .heavyWeaponPenalty(true)
                .preferredWeapons(Arrays.asList("Dagger", "Stiletto", "Short Sword", "Hatchet", "Javelin", "Throwing Knife", "Blowgun", "Shortbow"))
                .weakWeapons(Arrays.asList("Great Axe", "Great Sword", "Halberd", "Battle Flail", "Great Pick", "War Flail", "Morning Star", "Maul"))
                .favoredOpponents("Slow, heavily armored opponents — Goblins can dart in and out.")
                .disfavoredOpponents("Other fast, evasive opponents. One solid hit usually ends them.")
                .build())
            .build());
        
        // Gnome
        RACES.put("Gnome", new Race.Builder()
            .name("Gnome")
            .isPlayable(true)
            .description("Small, surprisingly tough tacticians. Excel at counterstrikes and turning aggression against opponents.")
            .baseHeightIn(40)
            .baseWeightLbs(85)
            .modifiers(new RacialModifiers.Builder()
                .hpBonus(6)
                .trainsStatsFaster(true)
                .parryBonus(5)
                .counterstrikeMastery(true)
                .tacticianEdge(true)
                .damagePenalty(3)
                .attackRatePenalty(2)
                .preferredWeapons(Arrays.asList("Short Sword", "Long Sword", "Epee", "Bastard Sword", "Hammer", "Mace", "Morningstar", "War Hammer"))
                .weakWeapons(Arrays.asList("Great Axe", "Battle Axe", "Halberd", "Great Pick", "Boar Spear", "Pole Axe", "Pike"))
                .favoredOpponents("Aggressive warriors with high activity styles — Gnomes punish overcommitment.")
                .disfavoredOpponents("Methodical, patient fighters with low activity and careful tactics.")
                .build())
            .build());
        
        // Lizardfolk
        RACES.put("Lizardfolk", new Race.Builder()
            .name("Lizardfolk")
            .isPlayable(true)
            .description("Savage reptilian predators. Tough, relentless, with natural armor and weapons, but cold-blooded and slower to accelerate.")
            .baseHeightIn(72)
            .baseWeightLbs(240)
            .modifiers(new RacialModifiers.Builder()
                .hpBonus(9)
                .naturalWeaponBonus(true)
                .martialCombatBonus(true)
                .naturalArmor(true)
                .dodgeBonus(2)
                .attackRatePenalty(3)
                .preferredWeapons(Arrays.asList("Open Hand", "Dagger", "Stiletto", "Short Sword", "Hatchet", "Hammer", "Mace", "Quarterstaff"))
                .weakWeapons(Arrays.asList("Epee", "Rapier", "Long Sword"))
                .favoredOpponents("Most opponents — Lizardfolk are well-rounded tanks.")
                .disfavoredOpponents("None in particular, but heavy armor restricts their natural strengths.")
                .build())
            .build());
        
        // Tabaxi
        RACES.put("Tabaxi", new Race.Builder()
            .name("Tabaxi")
            .isPlayable(true)
            .description("Lightning-quick acrobatic felines. Best evasion in the game, but fragile and tire quickly in long fights.")
            .baseHeightIn(58)
            .baseWeightLbs(115)
            .modifiers(new RacialModifiers.Builder()
                .dodgeBonus(7)
                .initiativeBonus(5)
                .acrobaticAdvantage(true)
                .frenzyAbility(true)
                .hpBonus(-7)
                .strengthPenalty(3)
                .heavyWeaponPenalty(true)
                .preferredWeapons(Arrays.asList("Dagger", "Short Sword", "Scimitar", "Epee", "Stiletto", "Hatchet", "Javelin", "Scythe", "Spear"))
                .weakWeapons(Arrays.asList("Great Axe", "Great Sword", "Halberd", "Maul", "Battle Flail", "War Flail", "Ball & Chain", "Great Pick"))
                .favoredOpponents("Most opponents — Tabaxi are hard to hit and difficult to pin down.")
                .disfavoredOpponents("Heavy hitters and endurance grinders (Dwarf, Lizardfolk, Half-Orc).")
                .build())
            .build());
        
        // Monster (NPC)
        RACES.put("Monster", new Race.Builder()
            .name("Monster")
            .isPlayable(false)
            .description("Hideous creatures controlled by the game. Fighting a Monster is essentially a death sentence. Less than a dozen warriors in Pit history have survived — those few were absorbed into the Monster team.")
            .baseHeightIn(90)
            .baseWeightLbs(405)
            .modifiers(new RacialModifiers.Builder()
                .hpBonus(50)
                .damageBonus(10)
                .attackRateBonus(5)
                .parryBonus(3)
                .dodgeBonus(3)
                .build())
            .build());
        
        // Peasant (NPC)
        RACES.put("Peasant", new Race.Builder()
            .name("Peasant")
            .isPlayable(false)
            .description("Arena fillers. Peasants are scaled dynamically to the warrior they face by the matchmaking system. Named individuals: Klud the Bell-Ringer, Sally Strumpet, Peter the Poet, Fiona Fishwife, Beggar Barleycorn, Stu the Gravedigger, Gypsy Jezebel, Perceval the Prophet, Madman Muttermuck, Roger the Shrubber. Never truly eliminated.")
            .baseHeightIn(67)
            .baseWeightLbs(165)
            .modifiers(new RacialModifiers.Builder().build())
            .build());
    }
    
    /**
     * Retrieve a Race by name (case-insensitive).
     * @param name the race name
     * @return the Race object
     * @throws IllegalArgumentException if the name is not found
     */
    /**
     * Retrieve a Race by name (case-insensitive).
     * @param name the race name
     * @return the Race object
     * @throws IllegalArgumentException if the name is not found
     */
    public static Race getRace(String name) {
        if (name == null) {
            throw new IllegalArgumentException("Race name cannot be null");
        }
        for (Map.Entry<String, Race> entry : RACES.entrySet()) {
            if (entry.getKey().equalsIgnoreCase(name)) {
                return entry.getValue();
            }
        }
        String valid = String.join(", ", RACES.keySet());
        throw new IllegalArgumentException("Unknown race: '" + name + "'. Valid options: " + valid);
    }
    
    /**
     * Alias for getRace() - used by Warrior constructor.
     */
    public static Race fromName(String name) {
        return getRace(name);
    }

    /**
     * Return names of all player-selectable races.
     */
    public static List<String> listPlayableRaces() {
        return RACES.values().stream()
            .filter(Race::isPlayable)
            .map(Race::getName)
            .collect(Collectors.toList());
    }
    
    /**
     * Alias for listPlayableRaces() - used by Team and WarriorFactory.
     */
    public static List<String> getPlayableRaces() {
        return listPlayableRaces();
    }

    /**
     * Return names of all races including NPC races.
     */
    public static List<String> listAllRaces() {
        return new ArrayList<>(RACES.keySet());
    }

    /**
     * Get all races as a map.
     */
    public static Map<String, Race> getAllRaces() {
        return Collections.unmodifiableMap(RACES);
    }
}
