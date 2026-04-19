package com.bloodspire.model;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Represents one manager's team of five warriors.
 * 
 * Key rules enforced here:
 *   - Roster is always exactly TEAM_SIZE (5) warriors.
 *   - Dead warriors are replaced immediately with fresh beginners.
 *   - Warriors who have fought 100 fights may be retired.
 *   - Up to 3 challenges may be issued per warrior per turn.
 *   - Blood challenges are available from any team member when a teammate
 *     is killed (killer must have 5+ fights).
 */
public class Team {
    
    public static final int TEAM_SIZE = 5;
    
    private String teamName;
    private String managerName;
    private int teamId;
    
    // Active roster — always TEAM_SIZE entries.
    private List<Warrior> warriors;
    
    // Record of warriors who have died or retired (for blood challenge tracking).
    private List<Map<String, Object>> fallenWarriors;
    
    // Blood challenges outstanding
    private List<Map<String, Object>> bloodChallenges;
    
    // Avoidance system: manager-level avoidances (max 2 slots)
    private List<String> avoidManagers;
    
    // Pending challenges: {warrior_name: [challenge_target, ...]}
    private Map<String, List<String>> challenges;
    
    // Archived warriors — dead warriors stored as stat snapshots after replacement
    private List<Map<String, Object>> archivedWarriors;
    
    // Pending replacement rollup bases: {slot_idx: base_stats_dict}
    private Map<Integer, Map<String, Object>> pendingReplacements;
    
    // Rolling turn history for last-5-turns newsletter column
    private List<Map<String, Object>> turnHistory;
    
    public Team(String teamName, String managerName, int teamId) {
        this.teamName = teamName;
        this.managerName = managerName;
        this.teamId = teamId;
        
        this.warriors = new ArrayList<>();
        this.fallenWarriors = new ArrayList<>();
        this.bloodChallenges = new ArrayList<>();
        this.avoidManagers = new ArrayList<>();
        this.challenges = new HashMap<>();
        this.archivedWarriors = new ArrayList<>();
        this.pendingReplacements = new HashMap<>();
        this.turnHistory = new ArrayList<>();
    }
    
    public Team(String teamName, String managerName) {
        this(teamName, managerName, 0);
    }
    
    // =========================================================================
    // ROSTER MANAGEMENT
    // =========================================================================
    
    public boolean addWarrior(Warrior warrior) {
        /**
         * Add a warrior to the team.
         * Returns true if added, false if the team is already full.
         */
        if (warriors.size() < TEAM_SIZE) {
            warriors.add(warrior);
            return true;
        }
        // Fill a null slot if one exists
        for (int i = 0; i < warriors.size(); i++) {
            if (warriors.get(i) == null) {
                warriors.set(i, warrior);
                return true;
            }
        }
        return false; // Team is full
    }
    
    public void fillRosterWithAI() {
        /**
         * Auto-fill any empty or null slots with AI-generated warriors.
         * Called during initial team creation and after replacement.
         */
        List<String> races = Race.getPlayableRaces();
        Random random = new Random();
        
        while (warriors.size() < TEAM_SIZE) {
            String race = races.get(random.nextInt(races.size()));
            String gender = random.nextBoolean() ? "Male" : "Female";
            Warrior w = WarriorFactory.createWarriorAI(race, gender);
            warriors.add(w);
        }
        
        // Replace any null slots too
        for (int i = 0; i < warriors.size(); i++) {
            if (warriors.get(i) == null) {
                String race = races.get(random.nextInt(races.size()));
                String gender = random.nextBoolean() ? "Male" : "Female";
                warriors.set(i, WarriorFactory.createWarriorAI(race, gender));
            }
        }
    }
    
    public Warrior warriorByName(String name) {
        /** Return a warrior by name (case-insensitive), or null. */
        for (Warrior w : warriors) {
            if (w != null && w.getName().equalsIgnoreCase(name)) {
                return w;
            }
        }
        return null;
    }
    
    public int warriorIndex(String name) {
        /** Return roster index for a warrior by name, or -1. */
        for (int i = 0; i < warriors.size(); i++) {
            Warrior w = warriors.get(i);
            if (w != null && w.getName().equalsIgnoreCase(name)) {
                return i;
            }
        }
        return -1;
    }
    
    public List<Warrior> getActiveWarriors() {
        /** Return living warriors only — excludes null slots and is_dead warriors. */
        return warriors.stream()
            .filter(w -> w != null && !w.isDead())
            .collect(Collectors.toList());
    }
    
    public boolean isFull() {
        return warriors.size() == TEAM_SIZE && 
               warriors.stream().allMatch(w -> w != null);
    }
    
    // =========================================================================
    // DEATH & REPLACEMENT
    // =========================================================================
    
    public int killWarrior(Warrior warrior, String killedBy, int killerFights) {
        /**
         * Mark a warrior as dead but keep them in their roster slot until the
         * player creates a replacement. Returns the slot index.
         */
        int idx = warriorIndex(warrior.getName());
        if (idx == -1) {
            throw new IllegalArgumentException(
                "Warrior '" + warrior.getName() + "' not found on team '" + teamName + "'.");
        }
        
        warrior.setDead(true);
        warrior.setKilledBy(killedBy);
        
        Map<String, Object> fallen = new HashMap<>();
        fallen.put("warrior_name", warrior.getName());
        fallen.put("killed_by", killedBy);
        fallen.put("killer_fights", killerFights);
        fallen.put("slot_idx", idx);
        fallenWarriors.add(fallen);
        
        if (killerFights >= 5) {
            Map<String, Object> bloodChallenge = new HashMap<>();
            bloodChallenge.put("dead_warrior_name", warrior.getName());
            bloodChallenge.put("target_name", killedBy);
            bloodChallenge.put("challenger_name", null);
            bloodChallenge.put("turns_remaining", 3);
            bloodChallenge.put("status", "active");
            bloodChallenges.add(bloodChallenge);
            
            System.out.println(
                "  *** BLOOD CHALLENGE available against '" + killedBy + 
                "' for the death of " + warrior.getName() + "! ***");
        }
        
        System.out.println(
            "  " + warrior.getName() + " has fallen. Replacement slot open at position " + idx + ".");
        return idx;
    }
    
    public boolean confirmReplacement(int slotIdx, Warrior newWarrior) {
        /**
         * Called when the player finishes building a replacement warrior.
         * Archives the dead warrior as a frozen snapshot, then places the new
         * warrior in the slot. Returns true on success.
         */
        if (slotIdx < 0 || slotIdx >= warriors.size()) {
            return false;
        }
        
        Warrior dead = warriors.get(slotIdx);
        if (dead == null || !dead.isDead()) {
            return false;
        }
        
        // Snapshot the dead warrior for the archives tab
        Map<String, Object> snapshot = warriorToDict(dead);
        snapshot.put("archived_killed_by", dead.getKilledBy());
        snapshot.put("archived_turns", dead.getTurnsActive());
        
        // Add formatted injuries text for display
        List<String> injuriesText = new ArrayList<>();
        Map<String, Integer> injuryData = dead.getInjuries().toDict();
        Map<Integer, String> injuryDescriptions = Map.ofEntries(
            Map.entry(0, "none"), Map.entry(1, "minor wound"), Map.entry(2, "bleeding wound"),
            Map.entry(3, "serious wound"), Map.entry(4, "deep wound"), Map.entry(5, "grave wound"),
            Map.entry(6, "critical wound"), Map.entry(7, "mortal wound"), 
            Map.entry(8, "near-fatal"), Map.entry(9, "fatal")
        );
        List<String> injuryLocations = PermanentInjuries.LOCATIONS;
        
        for (String loc : injuryLocations) {
            int level = injuryData.getOrDefault(loc, 0);
            if (level > 0) {
                String displayLoc = loc.replace("_", " ").substring(0, 1).toUpperCase() + 
                                   loc.replace("_", " ").substring(1);
                String displayLevel = injuryDescriptions.getOrDefault(level, "Level " + level);
                injuriesText.add(displayLoc + ": " + displayLevel);
            }
        }
        snapshot.put("injuries_text", injuriesText);
        
        // Add formatted skills text for display
        List<String> skillsText = new ArrayList<>();
        Map<String, Integer> skillsData = dead.getSkills();
        for (Map.Entry<String, Integer> entry : skillsData.entrySet()) {
            String skillName = entry.getKey();
            int level = entry.getValue();
            if (level > 0) {
                String displayName = skillName.replace("_", " ").substring(0, 1).toUpperCase() + 
                                    skillName.replace("_", " ").substring(1);
                skillsText.add(displayName + ": " + level);
            }
        }
        snapshot.put("skills_text", skillsText);
        
        archivedWarriors.add(snapshot);
        
        // Place the replacement
        warriors.set(slotIdx, newWarrior);
        pendingReplacements.remove(slotIdx);
        
        System.out.println(
            "  " + dead.getName() + " archived. " + newWarrior.getName() + " joins as replacement.");
        return true;
    }
    
    public Warrior retireWarrior(Warrior warrior) {
        /**
         * Retire a warrior who has reached 100 fights.
         * Returns the replacement, or null if the warrior is not eligible.
         */
        if (!warrior.isRetirementEligible()) {
            System.out.println(
                "  " + warrior.getName() + " is not eligible for retirement (" +
                warrior.getTotalFights() + " fights; need " + Warrior.MAX_FIGHTS + ").");
            return null;
        }
        
        int idx = warriorIndex(warrior.getName());
        if (idx == -1) {
            throw new IllegalArgumentException(
                "Warrior '" + warrior.getName() + "' not found on this team.");
        }
        
        System.out.println(
            "  " + warrior.getName() + " retires after " + warrior.getTotalFights() + 
            " fights (" + warrior.getRecordStr() + "). Immortalized in Shady Pines!");
        
        // Replacement (same as death, per guide)
        Random random = new Random();
        Warrior replacement = WarriorFactory.createWarriorAI();
        replacement.setName("Rookie_" + warrior.getName().substring(0, Math.min(4, warrior.getName().length())) + 
                           "_" + (10 + random.nextInt(90)));
        warriors.set(idx, replacement);
        return replacement;
    }
    
    // =========================================================================
    // CHALLENGES
    // =========================================================================
    
    public void addChallenge(String challengerName, String target) {
        /**
         * Add a challenge for a warrior (up to 3 per warrior per turn).
         * target is a manager name, team name, or individual warrior name.
         */
        challenges.putIfAbsent(challengerName, new ArrayList<>());
        List<String> existing = challenges.get(challengerName);
        
        if (existing.size() >= 3) {
            System.out.println("  " + challengerName + " already has 3 challenges queued.");
            return;
        }
        
        existing.add(target);
        System.out.println("  Challenge added: " + challengerName + " → " + target);
    }
    
    public void clearChallenges() {
        /** Clear all pending challenges (called after each turn is processed). */
        challenges.clear();
    }
    
    // =========================================================================
    // BLOOD CHALLENGE MANAGEMENT
    // =========================================================================
    
    public List<Map<String, Object>> getActiveBloodChallenges() {
        /**
         * Return list of blood challenges that are still active.
         * Active = status is 'active' AND turns_remaining > 0.
         */
        return bloodChallenges.stream()
            .filter(bc -> "active".equals(bc.get("status")) && 
                          (int)bc.get("turns_remaining") > 0)
            .collect(Collectors.toList());
    }
    
    public void decrementBloodChallengeTurns() {
        /** Decrement turns_remaining on all active blood challenges. */
        for (Map<String, Object> bc : bloodChallenges) {
            if ("active".equals(bc.get("status"))) {
                int turns = (int)bc.get("turns_remaining");
                if (turns > 0) {
                    bc.put("turns_remaining", turns - 1);
                }
            }
        }
    }
    
    public void assignBloodChallenger(String deadWarriorName, String challengerName) {
        /** Assign a specific warrior to carry out a blood challenge. */
        for (Map<String, Object> bc : bloodChallenges) {
            if (deadWarriorName.equals(bc.get("dead_warrior_name"))) {
                bc.put("challenger_name", challengerName);
                break;
            }
        }
    }
    
    public void markBloodChallengeAvenged(String deadWarriorName) {
        /** Mark a blood challenge as avenged. */
        for (Map<String, Object> bc : bloodChallenges) {
            if (deadWarriorName.equals(bc.get("dead_warrior_name"))) {
                bc.put("status", "avenged");
                break;
            }
        }
    }
    
    // =========================================================================
    // AVOIDANCE SYSTEM
    // =========================================================================
    
    public boolean addAvoidManager(String managerName) {
        /** Add a manager to avoid (max 2 slots). Returns true if added. */
        if (avoidManagers.size() >= 2) {
            return false;
        }
        if (!avoidManagers.contains(managerName)) {
            avoidManagers.add(managerName);
            return true;
        }
        return false;
    }
    
    public boolean removeAvoidManager(String managerName) {
        /** Remove a manager from the avoid list. */
        return avoidManagers.remove(managerName);
    }
    
    public List<String> getAvoidManagers() {
        return new ArrayList<>(avoidManagers);
    }
    
    public boolean isAvoidingManager(String challengerManager) {
        for (String m : avoidManagers) {
            if (m != null && m.equalsIgnoreCase(challengerManager)) {
                return true;
            }
        }
        return false;
    }
    
    // =========================================================================
    // UTILITY METHODS
    // =========================================================================
    
    private Map<String, Object> warriorToDict(Warrior w) {
        /** Convert a warrior to a dictionary snapshot. */
        Map<String, Object> dict = new HashMap<>();
        dict.put("name", w.getName());
        dict.put("race", w.getRace().getName());
        dict.put("gender", w.getGender());
        dict.put("strength", w.getStrength());
        dict.put("dexterity", w.getDexterity());
        dict.put("constitution", w.getConstitution());
        dict.put("intelligence", w.getIntelligence());
        dict.put("presence", w.getPresence());
        dict.put("size", w.getSize());
        dict.put("max_hp", w.getMaxHp());
        dict.put("wins", w.getWins());
        dict.put("losses", w.getLosses());
        dict.put("kills", w.getKills());
        dict.put("total_fights", w.getTotalFights());
        dict.put("armor", w.getArmor());
        dict.put("helm", w.getHelm());
        dict.put("primary_weapon", w.getPrimaryWeapon());
        dict.put("secondary_weapon", w.getSecondaryWeapon());
        dict.put("backup_weapon", w.getBackupWeapon());
        dict.put("skills", w.getSkills());
        dict.put("injuries", w.getInjuries().toDict());
        dict.put("luck", w.getLuck());
        dict.put("popularity", w.getPopularity());
        dict.put("recognition", w.getRecognition());
        dict.put("streak", w.getStreak());
        dict.put("favorite_weapon", w.getFavoriteWeapon());
        return dict;
    }
    
    // =========================================================================
    // GETTERS AND SETTERS
    // =========================================================================
    
    public String getTeamName() { return teamName; }
    public void setTeamName(String teamName) { this.teamName = teamName; }
    
    public String getManagerName() { return managerName; }
    public void setManagerName(String managerName) { this.managerName = managerName; }
    
    public int getTeamId() { return teamId; }
    public void setTeamId(int teamId) { this.teamId = teamId; }
    
    public List<Warrior> getWarriors() { return warriors; }
    public void setWarriors(List<Warrior> warriors) { this.warriors = warriors; }
    
    public List<Map<String, Object>> getFallenWarriors() { return fallenWarriors; }
    public List<Map<String, Object>> getBloodChallenges() { return bloodChallenges; }
    public List<Map<String, Object>> getArchivedWarriors() { return archivedWarriors; }
    public Map<Integer, Map<String, Object>> getPendingReplacements() { return pendingReplacements; }
    public List<Map<String, Object>> getTurnHistory() { return turnHistory; }
    public Map<String, List<String>> getChallenges() { return challenges; }
    
    // =========================================================================
    // SERIALIZATION
    // =========================================================================
    
    @SuppressWarnings("unchecked")
    public static Team fromMap(Map<String, Object> data) {
        String teamName = (String) data.get("team_name");
        String managerName = (String) data.get("manager_name");
        int teamId = (int) data.getOrDefault("team_id", 0);
        
        Team team = new Team(teamName, managerName, teamId);
        
        // Restore warriors
        List<Object> warriorsData = (List<Object>) data.get("warriors");
        if (warriorsData != null) {
            team.warriors.clear();
            for (Object wData : warriorsData) {
                if (wData instanceof Map) {
                    Warrior w = Warrior.fromMap((Map<String, Object>) wData);
                    team.warriors.add(w);
                } else {
                    team.warriors.add(null);
                }
            }
        }
        
        // Restore fallen warriors
        List<Object> fallenData = (List<Object>) data.get("fallen_warriors");
        if (fallenData != null) {
            team.fallenWarriors.clear();
            for (Object f : fallenData) {
                if (f instanceof Map) {
                    team.fallenWarriors.add((Map<String, Object>) f);
                }
            }
        }
        
        // Restore blood challenges
        List<Object> bloodData = (List<Object>) data.get("blood_challenges");
        if (bloodData != null) {
            team.bloodChallenges.clear();
            for (Object b : bloodData) {
                if (b instanceof Map) {
                    team.bloodChallenges.add((Map<String, Object>) b);
                }
            }
        }
        
        // Restore avoid managers
        List<Object> avoidData = (List<Object>) data.get("avoid_managers");
        if (avoidData != null) {
            team.avoidManagers.clear();
            for (Object a : avoidData) {
                if (a instanceof String) {
                    team.avoidManagers.add((String) a);
                }
            }
        }
        
        // Restore challenges
        Map<String, Object> challengesData = (Map<String, Object>) data.get("challenges");
        if (challengesData != null) {
            team.challenges.clear();
            for (Map.Entry<String, Object> entry : challengesData.entrySet()) {
                List<Object> targets = (List<Object>) entry.getValue();
                List<String> targetList = new ArrayList<>();
                for (Object t : targets) {
                    if (t instanceof String) {
                        targetList.add((String) t);
                    }
                }
                team.challenges.put(entry.getKey(), targetList);
            }
        }
        
        // Restore archived warriors
        List<Object> archivedData = (List<Object>) data.get("archived_warriors");
        if (archivedData != null) {
            team.archivedWarriors.clear();
            for (Object a : archivedData) {
                if (a instanceof Map) {
                    team.archivedWarriors.add((Map<String, Object>) a);
                }
            }
        }
        
        // Restore pending replacements
        Map<String, Object> pendingData = (Map<String, Object>) data.get("pending_replacements");
        if (pendingData != null) {
            team.pendingReplacements.clear();
            for (Map.Entry<String, Object> entry : pendingData.entrySet()) {
                try {
                    int slot = Integer.parseInt(entry.getKey());
                    team.pendingReplacements.put(slot, (Map<String, Object>) entry.getValue());
                } catch (NumberFormatException e) {
                    // Skip invalid keys
                }
            }
        }
        
        // Restore turn history
        List<Object> turnData = (List<Object>) data.get("turn_history");
        if (turnData != null) {
            team.turnHistory.clear();
            for (Object t : turnData) {
                if (t instanceof Map) {
                    team.turnHistory.add((Map<String, Object>) t);
                }
            }
        }
        
        return team;
    }
    
    public Map<String, Object> toMap() {
        Map<String, Object> data = new HashMap<>();
        data.put("team_name", teamName);
        data.put("manager_name", managerName);
        data.put("team_id", teamId);
        
        // Serialize warriors (handle nulls)
        List<Object> warriorsData = new ArrayList<>();
        for (Warrior w : warriors) {
            if (w != null) {
                warriorsData.add(w.toMap());
            } else {
                warriorsData.add(null);
            }
        }
        data.put("warriors", warriorsData);
        
        data.put("fallen_warriors", new ArrayList<>(fallenWarriors));
        data.put("blood_challenges", new ArrayList<>(bloodChallenges));
        data.put("avoid_managers", new ArrayList<>(avoidManagers));
        
        // Serialize challenges
        Map<String, Object> challengesData = new HashMap<>();
        for (Map.Entry<String, List<String>> entry : challenges.entrySet()) {
            challengesData.put(entry.getKey(), new ArrayList<>(entry.getValue()));
        }
        data.put("challenges", challengesData);
        
        data.put("archived_warriors", new ArrayList<>(archivedWarriors));
        
        // Serialize pending replacements
        Map<String, Object> pendingData = new HashMap<>();
        for (Map.Entry<Integer, Map<String, Object>> entry : pendingReplacements.entrySet()) {
            pendingData.put(String.valueOf(entry.getKey()), entry.getValue());
        }
        data.put("pending_replacements", pendingData);
        
        data.put("turn_history", new ArrayList<>(turnHistory));
        
        return data;
    }
}
