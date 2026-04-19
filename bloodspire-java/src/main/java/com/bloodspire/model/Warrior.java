package com.bloodspire.model;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Represents a single gladiator in BLOODSPIRE.
 * Mirrors the Python Warrior class functionality.
 */
public class Warrior {
    
    // =========================================================================
    // CONSTANTS (from warrior.py)
    // =========================================================================
    
    public static final int ROLLUP_POINTS = 16;
    public static final int ROLLUP_MAX_PER_STAT = 7;
    public static final int STAT_MIN = 3;
    public static final int STAT_MAX = 25;
    public static final int MAX_FIGHTS = 100;
    
    public static final List<String> ATTRIBUTES = List.of(
        "strength", "dexterity", "constitution",
        "intelligence", "presence", "size"
    );
    
    public static final List<String> INJURY_LOCATIONS = List.of(
        "head", "chest", "abdomen",
        "primary_arm", "secondary_arm",
        "primary_leg", "secondary_leg"
    );
    
    public static final Map<Integer, String> INJURY_DESCRIPTIONS = Map.ofEntries(
        Map.entry(0, "None"),
        Map.entry(1, "Annoying"),
        Map.entry(2, "Bothersome"),
        Map.entry(3, "Irritating"),
        Map.entry(4, "Troublesome"),
        Map.entry(5, "Painful"),
        Map.entry(6, "Dreadful"),
        Map.entry(7, "Incapacitating"),
        Map.entry(8, "Devastating"),
        Map.entry(9, "Fatal")
    );
    
    public static final List<String> TRIGGERS = List.of(
        "None",
        "Minute 1", "Minute 2", "Minute 3", "Minute 4", "Minute 5",
        "Minute 6", "Minute 7", "Minute 8", "Minute 9", "Minute 10",
        "You are very tired", "Your foe is very tired",
        "You are somewhat tired", "Your foe is somewhat tired",
        "You are slightly tired", "Your foe is slightly tired",
        "You have taken heavy damage", "Your foe has taken heavy damage",
        "You have taken medium damage", "Your foe has taken medium damage",
        "You have taken slight damage", "Your foe has taken slight damage",
        "You challenged your foe", "Your foe challenged you",
        "You blood challenged your foe", "Your foe blood challenged you",
        "You are on the ground", "Your foe is on the ground",
        "You are weaponless", "Your foe is weaponless",
        "You have no throwable weapons",
        "You have at least one throwable weapon",
        "You have exactly one throwable weapon",
        "You have exactly one weapon",
        "You have exactly 2 weapons",
        "You have more than 2 weapons",
        "Your foe is wearing light armor",
        "Your foe is wearing medium armor",
        "Your foe is wearing heavy armor",
        "Always (Default Loop)"
    );
    
    public static final List<String> FIGHTING_STYLES = List.of(
        "Total Kill", "Wall of Steel", "Lunge", "Bash", "Slash", "Strike",
        "Engage & Withdraw", "Counterstrike", "Decoy", "Sure Strike",
        "Calculated Attack", "Opportunity Throw", "Martial Combat", "Parry", "Defend"
    );
    
    public static final List<String> AIM_DEFENSE_POINTS = List.of(
        "None", "Head", "Chest", "Abdomen", "Primary Arm", "Secondary Arm",
        "Primary Leg", "Secondary Leg"
    );
    
    public static final List<String> NON_WEAPON_SKILLS = List.of(
        "dodge", "parry", "throw", "charge", "lunge",
        "disarm", "initiative", "feint", "brawl", "sweep",
        "cleave", "bash", "acrobatics", "riposte", "slash", "strike"
    );
    
    public static final List<String> WEAPON_SKILLS = List.of(
        "stiletto", "cestus", "knife", "dagger", "javelin", "hatchet",
        "short_sword", "epee", "hammer", "net", "small_pick", "buckler",
        "swordbreaker", "longsword", "scythe", "flail", "francisca", "mace",
        "short_spear", "boar_spear", "quarterstaff", "trident", "military_pick", "scimitar",
        "broad_sword", "morningstar", "war_hammer", "target_shield",
        "bladed_flail", "war_flail", "bastard_sword", "pick_axe", "long_spear",
        "tower_shield", "battle_axe", "battle_flail", "great_staff", "pole_axe",
        "great_sword", "ball_and_chain", "great_axe", "maul", "great_pick",
        "halberd", "open_hand"
    );
    
    public static final List<String> ALL_SKILLS;
    
    static {
        List<String> all = new ArrayList<>(NON_WEAPON_SKILLS);
        all.addAll(WEAPON_SKILLS);
        ALL_SKILLS = Collections.unmodifiableList(all);
    }
    
    public static final Map<Integer, String> SKILL_LEVEL_NAMES = Map.ofEntries(
        Map.entry(0, "No Skill"),
        Map.entry(1, "Novice"),
        Map.entry(2, "Some Skill"),
        Map.entry(3, "Skilled"),
        Map.entry(4, "Good Skill"),
        Map.entry(5, "Very Skilled"),
        Map.entry(6, "Excellent Skill"),
        Map.entry(7, "Expert Skill"),
        Map.entry(8, "Incredible Skill"),
        Map.entry(9, "Master Skill")
    );

    // =========================================================================
    // IDENTITY & CORE ATTRIBUTES
    // =========================================================================
    
    private String name;
    private Race race;
    private String gender;
    
    private int strength;
    private int dexterity;
    private int constitution;
    private int intelligence;
    private int presence;
    private int size;
    
    // =========================================================================
    // DERIVED STATS
    // =========================================================================
    
    private int maxHp;
    private int currentHp;
    private int currentEndurance;
    
    // =========================================================================
    // FIGHT RECORD
    // =========================================================================
    
    private int wins;
    private int losses;
    private int kills;
    private int monsterKills;
    private int totalFights;
    
    // =========================================================================
    // EQUIPMENT
    // =========================================================================
    
    private String armor;
    private String helm;
    private String primaryWeapon;
    private String secondaryWeapon;
    private String backupWeapon;
    
    // =========================================================================
    // STRATEGIES
    // =========================================================================
    
    private List<WarriorStrategy> strategies;
    
    // =========================================================================
    // TRAINING & SKILLS
    // =========================================================================
    
    private List<String> trains;
    private Map<String, Integer> skills;
    
    // =========================================================================
    // INJURIES
    // =========================================================================
    
    private PermanentInjuries injuries;
    
    // =========================================================================
    // FLAVOR & META
    // =========================================================================
    
    private String bloodCry;
    private Map<String, Integer> initialStats;
    private List<Map<String, Object>> fightHistory;
    private Map<String, Integer> attributeGains;
    private int luck;
    private int popularity;
    private int recognition;
    private int streak;
    private int turnsActive;
    
    // =========================================================================
    // FIGHT OPTIONS & STATE
    // =========================================================================
    
    private boolean wantMonsterFight;
    private boolean wantRetire;
    private List<String> avoidWarriors;
    private boolean isDead;
    private boolean ascendedToMonster;
    private String killedBy;
    private String favoriteWeapon;
    
    // =========================================================================
    // PHYSICAL MEASUREMENTS
    // =========================================================================
    
    private int heightIn;
    private int weightLbs;
    private int trainingWeightBonus;
    
    // =========================================================================
    // MESSAGE TRACKING
    // =========================================================================
    
    private Set<String> shownMaxMessages;

    // =========================================================================
    // CONSTRUCTORS
    // =========================================================================
    
    public Warrior(String name, String raceName, String gender,
                   int strength, int dexterity, int constitution,
                   int intelligence, int presence, int size) {
        this.name = name;
        this.race = Race.fromName(raceName);
        this.gender = gender;
        
        this.strength = strength;
        this.dexterity = dexterity;
        this.constitution = constitution;
        this.intelligence = intelligence;
        this.presence = presence;
        this.size = size;
        
        // Derived stats
        this.maxHp = calcMaxHp();
        this.currentHp = this.maxHp;
        this.currentEndurance = 100;
        
        // Fight record
        this.wins = 0;
        this.losses = 0;
        this.kills = 0;
        this.monsterKills = 0;
        this.totalFights = 0;
        
        // Equipment
        this.armor = null;
        this.helm = null;
        this.primaryWeapon = "Open Hand";
        this.secondaryWeapon = "Open Hand";
        this.backupWeapon = null;
        
        // Strategies - start with default "Always" strategy
        this.strategies = new ArrayList<>();
        this.strategies.add(new WarriorStrategy(
            "Always", "Strike", 5, "None", "Chest"
        ));
        
        // Training & Skills
        this.trains = new ArrayList<>();
        this.skills = new HashMap<>();
        for (String skill : ALL_SKILLS) {
            this.skills.put(skill, 0);
        }
        
        // Injuries
        this.injuries = new PermanentInjuries();
        
        // Flavor & Meta
        this.bloodCry = "";
        this.initialStats = new HashMap<>();
        this.initialStats.put("strength", strength);
        this.initialStats.put("dexterity", dexterity);
        this.initialStats.put("constitution", constitution);
        this.initialStats.put("intelligence", intelligence);
        this.initialStats.put("presence", presence);
        this.initialStats.put("size", size);
        this.fightHistory = new ArrayList<>();
        this.attributeGains = new HashMap<>();
        for (String attr : ATTRIBUTES) {
            this.attributeGains.put(attr, 0);
        }
        this.luck = 0;
        this.popularity = 0;
        this.recognition = 0;
        this.streak = 0;
        this.turnsActive = 0;
        
        // Fight Options & State
        this.wantMonsterFight = false;
        this.wantRetire = false;
        this.avoidWarriors = new ArrayList<>();
        this.isDead = false;
        this.ascendedToMonster = false;
        this.killedBy = "";
        this.favoriteWeapon = "";
        
        // Physical Measurements
        int[] measurements = calcMeasurements();
        this.heightIn = measurements[0];
        this.weightLbs = measurements[1];
        this.trainingWeightBonus = 0;
        
        // Message Tracking
        this.shownMaxMessages = new HashSet<>();
    }

    // =========================================================================
    // DERIVED STAT CALCULATIONS
    // =========================================================================

    private int calcMaxHp() {
        /**
         * HP Formula (from guide):
         *     Base HP = 2*SIZE + (CON * 1.5) + (STR * 0.5)
         *     Cap at 100.
         *     Add racial HP bonus (can be negative for Elves).
         */
        double base = (2 * size) + (constitution * 1.5) + (strength * 0.5);
        int racialBonus = race.getModifiers().getHpBonus();
        int total = (int)(base + racialBonus);
        return Math.max(1, Math.min(total, 100)); // Always at least 1 HP; never more than 100
    }

    private int[] calcMeasurements() {
        /**
         * Derive height (inches) and weight (lbs) from race + SIZE + gender.
         * 
         * HEIGHT:
         *   Each race has a male height range (min at SIZE 3, max at SIZE 25).
         *   SIZE is mapped linearly across that range.
         *   Females use 95% of the male range endpoints.
         * 
         * WEIGHT:
         *   Derived from height using a race-specific body-density factor.
         *   Dwarves have a much higher density than other races.
         *   Females use 92% of the male density factor.
         */
        
        // Height range table (inches, male) - keys match race names
        Map<String, int[]> heightRanges = Map.ofEntries(
            Map.entry("Halfling", new int[]{37, 61}),
            Map.entry("Elf", new int[]{56, 71}),
            Map.entry("Half-Elf", new int[]{60, 72}),
            Map.entry("Human", new int[]{62, 76}),
            Map.entry("Dwarf", new int[]{42, 62}),
            Map.entry("Half-Orc", new int[]{65, 90}),
            Map.entry("Monster", new int[]{72, 108}),
            Map.entry("Peasant", new int[]{62, 76})
        );

        // Weight density table (lbs = height_in^2 * factor, male)
        Map<String, Double> density = Map.ofEntries(
            Map.entry("Halfling", 0.0434),
            Map.entry("Elf", 0.0338),
            Map.entry("Half-Elf", 0.0354),
            Map.entry("Human", 0.0368),
            Map.entry("Dwarf", 0.0780),   // Notably heavier by proportion
            Map.entry("Half-Orc", 0.0462),
            Map.entry("Monster", 0.0420),
            Map.entry("Peasant", 0.0368)
        );

        String raceName = race.getName();
        int[] range = heightRanges.getOrDefault(raceName, new int[]{62, 76});
        int mnM = range[0];
        int mxM = range[1];

        // Female endpoints are 95% of male
        int mn, mx;
        if ("Female".equals(gender)) {
            mn = (int)(mnM * 0.95);
            mx = (int)(mxM * 0.95);
        } else {
            mn = mnM;
            mx = mxM;
        }

        // Linear interpolation: SIZE 3 = min, SIZE 25 = max
        double sizeT = Math.max(0.0, Math.min(1.0, (size - 3) / 22.0));
        int height = (int)(mn + sizeT * (mx - mn));

        // Weight from height using density factor
        double dens = density.getOrDefault(raceName, 0.0368);
        if ("Female".equals(gender)) {
            dens *= 0.92; // Slightly lighter frame
        }
        int weight = Math.max(30, (int)(height * height * dens));
        weight += trainingWeightBonus;

        return new int[]{height, weight};
    }

    public void recalculateDerived() {
        /**
         * Recalculate HP and measurements after stats change (e.g. after training).
         * Note: currentHp is NOT reset here — only maxHp changes.
         */
        int oldMax = maxHp;
        maxHp = calcMaxHp();

        // If max HP increased, current HP scales up proportionally
        if (maxHp > oldMax) {
            currentHp = Math.min(currentHp + (maxHp - oldMax), maxHp);
        }

        int[] measurements = calcMeasurements();
        heightIn = measurements[0];
        weightLbs = measurements[1];
    }

    // =========================================================================
    // STAT ACCESS
    // =========================================================================

    public int getAttr(String attrName) {
        return switch (attrName.toLowerCase()) {
            case "strength" -> strength;
            case "dexterity" -> dexterity;
            case "constitution" -> constitution;
            case "intelligence" -> intelligence;
            case "presence" -> presence;
            case "size" -> size;
            default -> 0;
        };
    }

    public void setAttr(String attrName, int value) {
        String attr = attrName.toLowerCase();
        if (ATTRIBUTES.contains(attr)) {
            int clamped = Math.max(STAT_MIN, Math.min(STAT_MAX, value));
            switch (attr) {
                case "strength" -> strength = clamped;
                case "dexterity" -> dexterity = clamped;
                case "constitution" -> constitution = clamped;
                case "intelligence" -> intelligence = clamped;
                case "presence" -> presence = clamped;
                case "size" -> size = clamped;
            }
            recalculateDerived();
        }
    }

    // =========================================================================
    // FIGHT RECORD
    // =========================================================================

    public String getRecordStr() {
        return String.format("%d-%d-%d", wins, losses, kills);
    }

    public void recordResult(String result, boolean killedOpponent) {
        result = result.toLowerCase().trim();
        if ("win".equals(result)) {
            wins++;
            if (killedOpponent) {
                kills++;
            }
            streak = Math.max(0, streak) + 1; // extend win streak
        } else if ("loss".equals(result)) {
            losses++;
            streak = Math.min(0, streak) - 1; // extend loss streak
        }
        totalFights++;
    }

    public boolean isRetirementEligible() {
        return totalFights >= MAX_FIGHTS;
    }

    // =========================================================================
    // GETTERS AND SETTERS
    // =========================================================================

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public Race getRace() { return race; }
    public String getGender() { return gender; }
    
    public int getStrength() { return strength; }
    public int getDexterity() { return dexterity; }
    public int getConstitution() { return constitution; }
    public int getIntelligence() { return intelligence; }
    public int getPresence() { return presence; }
    public int getSize() { return size; }
    
    public int getMaxHp() { return maxHp; }
    public int getCurrentHp() { return currentHp; }
    public void setCurrentHp(int currentHp) { this.currentHp = currentHp; }
    public int getCurrentEndurance() { return currentEndurance; }
    public void setCurrentEndurance(int currentEndurance) { this.currentEndurance = currentEndurance; }
    
    public int getWins() { return wins; }
    public int getLosses() { return losses; }
    public int getKills() { return kills; }
    public int getMonsterKills() { return monsterKills; }
    public int getTotalFights() { return totalFights; }
    
    public String getArmor() { return armor; }
    public void setArmor(String armor) { this.armor = armor; }
    public String getHelm() { return helm; }
    public void setHelm(String helm) { this.helm = helm; }
    public String getPrimaryWeapon() { return primaryWeapon; }
    public void setPrimaryWeapon(String primaryWeapon) { this.primaryWeapon = primaryWeapon; }
    public String getSecondaryWeapon() { return secondaryWeapon; }
    public void setSecondaryWeapon(String secondaryWeapon) { this.secondaryWeapon = secondaryWeapon; }
    public String getBackupWeapon() { return backupWeapon; }
    public void setBackupWeapon(String backupWeapon) { this.backupWeapon = backupWeapon; }
    
    public List<WarriorStrategy> getStrategies() { return strategies; }
    public void setStrategies(List<WarriorStrategy> strategies) { this.strategies = strategies; }
    
    public List<String> getTrains() { return trains; }
    public void setTrains(List<String> trains) { this.trains = trains; }
    public Map<String, Integer> getSkills() { return skills; }
    
    public PermanentInjuries getInjuries() { return injuries; }
    
    public String getBloodCry() { return bloodCry; }
    public void setBloodCry(String bloodCry) { this.bloodCry = bloodCry; }
    public Map<String, Integer> getInitialStats() { return initialStats; }
    public List<Map<String, Object>> getFightHistory() { return fightHistory; }
    public Map<String, Integer> getAttributeGains() { return attributeGains; }
    
    public int getLuck() { return luck; }
    public void setLuck(int luck) { this.luck = luck; }
    public int getPopularity() { return popularity; }
    public void setPopularity(int popularity) { this.popularity = popularity; }
    public int getRecognition() { return recognition; }
    public void setRecognition(int recognition) { this.recognition = recognition; }
    public int getStreak() { return streak; }
    public void setStreak(int streak) { this.streak = streak; }
    public int getTurnsActive() { return turnsActive; }
    public void setTurnsActive(int turnsActive) { this.turnsActive = turnsActive; }
    
    public boolean isWantMonsterFight() { return wantMonsterFight; }
    public void setWantMonsterFight(boolean wantMonsterFight) { this.wantMonsterFight = wantMonsterFight; }
    public boolean isWantRetire() { return wantRetire; }
    public void setWantRetire(boolean wantRetire) { this.wantRetire = wantRetire; }
    public List<String> getAvoidWarriors() { return avoidWarriors; }
    public void setAvoidWarriors(List<String> avoidWarriors) { this.avoidWarriors = avoidWarriors; }
    
    public boolean isAvoidingWarrior(String challengerName) {
        for (String w : avoidWarriors) {
            if (w != null && w.equalsIgnoreCase(challengerName)) {
                return true;
            }
        }
        return false;
    }
    
    public boolean isDead() { return isDead; }
    public void setDead(boolean dead) { isDead = dead; }
    public boolean isAscendedToMonster() { return ascendedToMonster; }
    public void setAscendedToMonster(boolean ascendedToMonster) { this.ascendedToMonster = ascendedToMonster; }
    public String getKilledBy() { return killedBy; }
    public void setKilledBy(String killedBy) { this.killedBy = killedBy; }
    public String getFavoriteWeapon() { return favoriteWeapon; }
    public void setFavoriteWeapon(String favoriteWeapon) { this.favoriteWeapon = favoriteWeapon; }
    
    public int getHeightIn() { return heightIn; }
    public int getWeightLbs() { return weightLbs; }
    public int getTrainingWeightBonus() { return trainingWeightBonus; }
    public void setTrainingWeightBonus(int trainingWeightBonus) { 
        this.trainingWeightBonus = trainingWeightBonus;
        this.weightLbs += trainingWeightBonus;
    }
    
    public Set<String> getShownMaxMessages() { return shownMaxMessages; }
}
