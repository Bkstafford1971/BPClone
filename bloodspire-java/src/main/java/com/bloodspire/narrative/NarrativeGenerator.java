package com.bloodspire.narrative;

import java.util.*;

public class NarrativeGenerator {
    
    private static final Random RANDOM = new Random();
    
    // Popular descriptions
    private static final List<String> POPULARITY_DESCRIPTIONS = Arrays.asList(
        "WIDELY REVILED", "BOOED REGULARLY", "GENERALLY DISLIKED", "MOSTLY IGNORED",
        "KNOWN TO THE CROWD", "POPULAR WITH THE KIDS", "WELL LIKED", "A FAN FAVORITE",
        "HAS HORDES OF ADORING FANS", "A LEGENDARY HERO OF THE PIT"
    );
    
    public static String getPopularityDescription(int score) {
        int index = Math.min(score / 10, POPULARITY_DESCRIPTIONS.size() - 1);
        return POPULARITY_DESCRIPTIONS.get(index);
    }
    
    // Style intent pools
    private static final Map<String, List<String>> STYLE_INTENT_POOLS = new HashMap<>();
    private static final Map<String, List<String>> AWKWARD_STYLE_INTENT_POOLS = new HashMap<>();
    
    static {
        initializeStylePools();
    }
    
    private static void initializeStylePools() {
        STYLE_INTENT_POOLS.put("Total Kill", Arrays.asList(
            "{name} rampages onward, {weapon} starved for bloodshed",
            "{name} charges forward in a wild frenzy",
            "{name} drives suddenly forward, {weapon} whistling through the air",
            "{name} attacks in a berserker rage",
            "{name} hurls {himself} forward with reckless abandon"
        ));
        
        STYLE_INTENT_POOLS.put("Wall of Steel", Arrays.asList(
            "{name} relentlessly presses forward with {his} {weapon}",
            "{name} creates a whirling wall of steel",
            "{name} attacks in a flurry of blows",
            "{name} hammers away with machine-like persistence"
        ));
        
        STYLE_INTENT_POOLS.put("Lunge", Arrays.asList(
            "{name} darts forward, looking for an opening",
            "{name} probes for a weakness in {foe}'s defense",
            "{name} moves with quick, precise footwork",
            "{name} circles {foe}, waiting for the perfect moment"
        ));
        
        STYLE_INTENT_POOLS.put("Bash", Arrays.asList(
            "{name} winds up for a crushing blow",
            "{name} drives forward with brute force",
            "{name} attempts to batter through {foe}'s defenses"
        ));
        
        STYLE_INTENT_POOLS.put("Slash", Arrays.asList(
            "{name} draws back for a sweeping slash",
            "{name} lines up for a powerful drawing cut",
            "{name} seeks to open a telling wound"
        ));
        
        STYLE_INTENT_POOLS.put("Strike", Arrays.asList(
            "{name} tries to hit the mighty {foe}",
            "{name} sizes up {foe} carefully",
            "{name} directs an attack toward {foe}",
            "{name} steps threateningly close to the {adj} {foe}"
        ));
        
        STYLE_INTENT_POOLS.put("Engage & Withdraw", Arrays.asList(
            "{name} probes and retreats, looking for an opening",
            "{name} feints left and prepares to strike",
            "{name} dances away from {foe}'s reach"
        ));
        
        STYLE_INTENT_POOLS.put("Counterstrike", Arrays.asList(
            "{name} waits patiently for {foe} to make a mistake",
            "{name} holds ground, watching {foe} like a hawk",
            "{name} anxiously awaits {foe}'s next move"
        ));
        
        STYLE_INTENT_POOLS.put("Decoy", Arrays.asList(
            "{name} engages {foe}'s weapon with {his} off-hand",
            "{name} feints to draw {foe}'s attention",
            "{name} draws {foe} into an elaborate trap"
        ));
        
        STYLE_INTENT_POOLS.put("Sure Strike", Arrays.asList(
            "{name} waits for absolutely the right moment",
            "{name} carefully prepares a deliberate strike",
            "{name} takes aim at {foe} with methodical precision"
        ));
        
        STYLE_INTENT_POOLS.put("Calculated Attack", Arrays.asList(
            "{name} ruthlessly seeks wreckage with {his} {weapon}",
            "{name} calculates the perfect attack angle",
            "{name} studies {foe}'s armor for weak points"
        ));
        
        STYLE_INTENT_POOLS.put("Opportunity Throw", Arrays.asList(
            "{name} hefts {his} {weapon} for a throw",
            "{name} lines up a ranged attack"
        ));
        
        STYLE_INTENT_POOLS.put("Martial Combat", Arrays.asList(
            "{name} drops into a fighting crouch",
            "{name} circles {foe} with fluid martial grace",
            "{name} prepares to unleash a flurry of strikes"
        ));
        
        STYLE_INTENT_POOLS.put("Parry", Arrays.asList(
            "{name} raises {his} {weapon} defensively",
            "{name} holds ground, focused entirely on defense"
        ));
        
        STYLE_INTENT_POOLS.put("Defend", Arrays.asList(
            "{name} keeps {his} guard high",
            "{name} circles warily, waiting for an opening"
        ));
        
        // Awkward style pools
        AWKWARD_STYLE_INTENT_POOLS.put("Bash", Arrays.asList(
            "{name} awkwardly attempts to bash with {his} {weapon}",
            "{name} struggles to use {his} {weapon} as a bludgeon",
            "{name} clumsily tries to bash with {his} dainty {weapon}",
            "{name} futilely attempts to smash with {his} {weapon}"
        ));
        
        AWKWARD_STYLE_INTENT_POOLS.put("Slash", Arrays.asList(
            "{name} awkwardly attempts to slash with {his} {weapon}",
            "{name} fumbles trying to slash with {his} {weapon}",
            "{name} awkwardly draws {his} {weapon} for a clumsy slash",
            "{name} tries unsuccessfully to slash with {his} stubby {weapon}"
        ));
        
        AWKWARD_STYLE_INTENT_POOLS.put("Cleave", Arrays.asList(
            "{name} struggles to cleave with {his} {weapon}",
            "{name} awkwardly attempts a clumsy cleaving motion",
            "{name} tries unsuccessfully to split through with {his} {weapon}"
        ));
        
        AWKWARD_STYLE_INTENT_POOLS.put("Wall of Steel", Arrays.asList(
            "{name} awkwardly flails {his} {weapon} in rapid-fire attempts",
            "{name} fumbles through a poorly-executed flurry with {his} {weapon}",
            "{name} clumsily hammers away with {his} {weapon}"
        ));
        
        AWKWARD_STYLE_INTENT_POOLS.put("Total Kill", Arrays.asList(
            "{name} rages forward clumsily with {his} {weapon}",
            "{name} charges in a clumsy fury with {his} {weapon}",
            "{name} desperately thrashes about with {his} {weapon}"
        ));
        
        AWKWARD_STYLE_INTENT_POOLS.put("Lunge", Arrays.asList(
            "{name} attempts an awkward, ineffective lunge with {his} {weapon}",
            "{name} stumbles forward with {his} {weapon}",
            "{name} fumbles a pathetic lunge attempt"
        ));
    }
    
    private static final List<String> WARRIOR_ADJ_POOL = Arrays.asList(
        "formidable", "powerful", "mighty", "relentless", "fierce",
        "dangerous", "capable", "tenacious", "stalwart", "fearsome"
    );
    
    public static String styleIntentLine(String warriorName, String foeName, String style, 
                                          String weaponName, String gender) {
        if (RANDOM.nextDouble() < 0.30) return null;
        
        List<String> pool = STYLE_INTENT_POOLS.getOrDefault(style, STYLE_INTENT_POOLS.get("Strike"));
        String template = pool.get(RANDOM.nextInt(pool.size()));
        String pronoun = "his".equals(gender) ? "his" : "her";
        String reflexive = "Male".equals(gender) ? "himself" : "herself";
        String adj = WARRIOR_ADJ_POOL.get(RANDOM.nextInt(WARRIOR_ADJ_POOL.size()));
        
        return template.replace("{name}", warriorName.toUpperCase())
                      .replace("{foe}", foeName.toUpperCase())
                      .replace("{weapon}", weaponName.toLowerCase())
                      .replace("{his}", pronoun)
                      .replace("{himself}", reflexive)
                      .replace("{adj}", adj);
    }
    
    public static String awkwardStyleIntentLine(String warriorName, String foeName, String style,
                                                 String weaponName, String gender) {
        List<String> pool = AWKWARD_STYLE_INTENT_POOLS.get(style);
        if (pool == null) {
            return styleIntentLine(warriorName, foeName, style, weaponName, gender);
        }
        
        String template = pool.get(RANDOM.nextInt(pool.size()));
        String pronoun = "Male".equals(gender) ? "his" : "her";
        
        return template.replace("{name}", warriorName.toUpperCase())
                      .replace("{foe}", foeName.toUpperCase())
                      .replace("{weapon}", weaponName.toLowerCase())
                      .replace("{his}", pronoun);
    }
    
    public static String attackLine(String attacker, String defender, String weapon, 
                                     String category, String style, String aimPoint,
                                     String gender, String race) {
        String[] verbs = {"strike", "hit", "attack", "swing at", "lunge at"};
        String verb = verbs[RANDOM.nextInt(verbs.length)];
        String location = aimPoint != null && !aimPoint.equals("None") ? aimPoint.toLowerCase() : "body";
        
        return String.format("%s %s %s's %s with %s!", 
            attacker.toUpperCase(), verb, defender.toUpperCase(), location, weapon.toUpperCase());
    }
    
    public static String defenseIntentLine(String defender, String gender, boolean usesParry) {
        String pronoun = "Male".equals(gender) ? "his" : "her";
        if (usesParry) {
            return String.format("%s raises %s weapon to parry!", defender.toUpperCase(), pronoun);
        } else {
            return String.format("%s prepares to dodge!", defender.toUpperCase());
        }
    }
    
    public static String decoyFeintLine(String attacker, String defender) {
        return String.format("%s feints brilliantly, catching %s off-balance!", 
            attacker.toUpperCase(), defender.toUpperCase());
    }
    
    public static String decoyFeintReadLine(String attacker, String defender) {
        return String.format("%s sees through %s's feint!", 
            defender.toUpperCase(), attacker.toUpperCase());
    }
    
    public static String calculatedProbeLine(String attacker, String defender) {
        return String.format("%s tests %s's defenses carefully.", 
            attacker.toUpperCase(), defender.toUpperCase());
    }
    
    public static String missLine(String attacker, String weapon) {
        return String.format("%s's %s attack misses wide!", 
            attacker.toUpperCase(), weapon.toUpperCase());
    }
    
    public static String parryLine(String defender, boolean barely, boolean targeted) {
        if (barely) {
            return String.format("%s barely parries the blow!", defender.toUpperCase());
        } else if (targeted) {
            return String.format("%s perfectly parries the aimed strike!", defender.toUpperCase());
        } else {
            return String.format("%s parries the attack!", defender.toUpperCase());
        }
    }
    
    public static String dodgeLine(String defender) {
        return String.format("%s dodges nimbly aside!", defender.toUpperCase());
    }
    
    public static String counterstrikeLine(String counterAttacker, String originalAttacker) {
        return String.format("%s launches a swift counterstrike against %s!", 
            counterAttacker.toUpperCase(), originalAttacker.toUpperCase());
    }
    
    public static String signatureLine(String warrior, String weapon) {
        return String.format("%s executes a masterful %s technique!", 
            warrior.toUpperCase(), weapon.toUpperCase());
    }
    
    public static String damageLine(String attacker, String defender, int damage, String location) {
        String locStr = location != null && !location.equals("None") ? location.toLowerCase() : "body";
        return String.format("%s hits %s for %d damage to the %s!", 
            attacker.toUpperCase(), defender.toUpperCase(), damage, locStr);
    }
    
    public static String bleedLine(String warrior) {
        return String.format("%s is bleeding heavily!", warrior.toUpperCase());
    }
    
    public static String knockdownLine(String warrior) {
        return String.format("%s crashes to the ground!", warrior.toUpperCase());
    }
    
    public static String standUpLine(String warrior) {
        return String.format("%s struggles back to %s feet!", 
            warrior.toUpperCase(), "his");
    }
    
    public static String victoryLine(String winner, String loser, boolean conceded) {
        if (conceded) {
            return String.format("%s forces %s to concede!", winner.toUpperCase(), loser.toUpperCase());
        } else {
            return String.format("%s defeats %s!", winner.toUpperCase(), loser.toUpperCase());
        }
    }
    
    public static String fatalityLine(String killer, String victim) {
        return String.format("%s has been slain by %s!", victim.toUpperCase(), killer.toUpperCase());
    }
    
    public static String crowdReaction(boolean positive) {
        if (positive) {
            String[] cheers = {"The crowd ROARS with approval!", "The audience erupts in cheers!", 
                              "Spectators leap to their feet!"};
            return cheers[RANDOM.nextInt(cheers.length)];
        } else {
            String[] boos = {"The crowd BOOS loudly!", "Disgusted murmurs ripple through the arena!",
                            "Spectators shake their heads in disappointment!"};
            return boos[RANDOM.nextInt(boos.length)];
        }
    }
}
