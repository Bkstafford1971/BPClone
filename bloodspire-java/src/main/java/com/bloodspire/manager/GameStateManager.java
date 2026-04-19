package com.bloodspire.manager;

import com.bloodspire.model.*;
import com.bloodspire.engine.CombatEngine;
import com.bloodspire.engine.CombatResult;
import com.bloodspire.engine.NarrativeEngine;
import java.util.*;
import java.io.*;

/**
 * Manages the overall game state including seasons, teams, matches, and economy.
 * Port of game_state.py
 */
public class GameStateManager {
    
    private League league;
    private int currentWeek;
    private int maxWeeks;
    private List<Team> teams;
    private List<Warrior> freeAgents;
    private List<MatchResult> matchHistory;
    private CombatEngine combatEngine;
    private NarrativeEngine narrativeEngine;
    private Random random = new Random();
    
    public GameStateManager() {
        this.combatEngine = new CombatEngine();
        this.narrativeEngine = new NarrativeEngine();
        this.teams = new ArrayList<>();
        this.freeAgents = new ArrayList<>();
        this.matchHistory = new ArrayList<>();
        this.currentWeek = 1;
        this.maxWeeks = 20; // Default season length
    }
    
    /**
     * Create a new league
     */
    public void createLeague(String name, int numTeams) {
        league = new League(name);
        generateInitialTeams(numTeams);
        generateFreeAgentPool(20);
    }
    
    /**
     * Load an existing league
     */
    public boolean loadLeague(String filePath) throws IOException {
        // Implementation for loading from JSON/file
        return true;
    }
    
    /**
     * Save current league state
     */
    public void saveLeague(String filePath) throws IOException {
        // Implementation for saving to JSON/file
    }
    
    /**
     * Generate initial AI teams
     */
    private void generateInitialTeams(int count) {
        String[] teamNames = {"Blood Ravens", "Iron Skulls", "Crimson Blades", "Death Walkers",
                             "Shadow Fighters", "War Lords", "Battle Born", "Steel Titans"};
        
        for (int i = 0; i < count && i < teamNames.length; i++) {
            Team team = new Team(teamNames[i]);
            team.setBudget(50000); // Starting budget
            
            // Add initial warriors
            for (int j = 0; j < 4; j++) {
                Warrior warrior = createRandomWarrior();
                team.addWarrior(warrior);
            }
            
            teams.add(team);
        }
    }
    
    /**
     * Generate pool of free agent warriors
     */
    private void generateFreeAgentPool(int count) {
        freeAgents.clear();
        for (int i = 0; i < count; i++) {
            freeAgents.add(createRandomWarrior());
        }
    }
    
    /**
     * Create a random warrior for generation purposes
     */
    private Warrior createRandomWarrior() {
        Race race = Race.values()[random.nextInt(Race.values().length)];
        String firstName = generateRandomName();
        String lastName = generateRandomLastName();
        
        Warrior warrior = new Warrior(firstName, lastName, race);
        
        // Randomize stats slightly
        warrior.setStat(Stat.STRENGTH, 5 + random.nextInt(6));
        warrior.setStat(Stat.AGILITY, 5 + random.nextInt(6));
        warrior.setStat(Stat.ENDURANCE, 5 + random.nextInt(6));
        warrior.setStat(Stat.INTELLIGENCE, 3 + random.nextInt(5));
        warrior.setStat(Stat.WISDOM, 3 + random.nextInt(5));
        warrior.setStat(Stat.CHARISMA, 3 + random.nextInt(5));
        warrior.setStat(Stat.PRESENCE, 3 + random.nextInt(5));
        
        // Equip random weapon
        Weapon weapon = WeaponsUtil.getAllWeapons().get(random.nextInt(WeaponsUtil.getAllWeapons().size()));
        warrior.equipWeapon(weapon, Hand.MAIN);
        
        return warrior;
    }
    
    private String generateRandomName() {
        String[] names = {"Kael", "Thorin", "Zara", "Grok", "Lena", "Darius", "Nyx", "Ragnar", "Freya", "Magnus"};
        return names[random.nextInt(names.length)];
    }
    
    private String generateRandomLastName() {
        String[] names = {"Bloodaxe", "Ironfist", "Stormborn", "Deathbringer", "Skullcrusher", "Wolfheart"};
        return names[random.nextInt(names.length)];
    }
    
    /**
     * Advance to next week
     */
    public void advanceWeek() {
        currentWeek++;
        if (currentWeek > maxWeeks) {
            endSeason();
        }
    }
    
    /**
     * Schedule and execute matches for current week
     */
    public List<MatchResult> executeWeekMatches() {
        List<MatchResult> results = new ArrayList<>();
        
        // Simple round-robin pairing
        for (int i = 0; i < teams.size() - 1; i += 2) {
            Team team1 = teams.get(i);
            Team team2 = teams.get(i + 1);
            
            MatchResult result = simulateMatch(team1, team2);
            results.add(result);
            matchHistory.add(result);
        }
        
        return results;
    }
    
    /**
     * Simulate a match between two teams
     */
    public MatchResult simulateMatch(Team team1, Team team2) {
        // Select random fighters from each team
        Warrior fighter1 = team1.getWarriors().get(random.nextInt(team1.getWarriors().size()));
        Warrior fighter2 = team2.getWarriors().get(random.nextInt(team2.getWarriors().size()));
        
        // Clone fighters for simulation
        Warrior simFighter1 = fighter1.clone();
        Warrior simFighter2 = fighter2.clone();
        
        // Run combat simulation
        CombatResult combatResult = combatEngine.simulateFight(simFighter1, simFighter2, "Arena");
        
        MatchResult matchResult = new MatchResult(team1, team2, fighter1, fighter2, combatResult);
        
        // Update fighter stats based on result
        updateFighterStats(fighter1, combatResult);
        updateFighterStats(fighter2, combatResult);
        
        return matchResult;
    }
    
    /**
     * Update fighter stats after a match
     */
    private void updateFighterStats(Warrior warrior, CombatResult result) {
        if (result.getWinner() == warrior) {
            warrior.addExperience(50);
        } else {
            warrior.addExperience(20);
        }
        
        // Check for injuries
        if (result.getWounds() != null) {
            for (Wound wound : result.getWounds()) {
                if (wound.getWarrior() == warrior) {
                    warrior.applyWound(wound);
                }
            }
        }
    }
    
    /**
     * Hire a free agent
     */
    public boolean hireFreeAgent(Team team, Warrior warrior) {
        int cost = calculateWarriorCost(warrior);
        if (team.getBudget() >= cost && freeAgents.contains(warrior)) {
            team.setBudget(team.getBudget() - cost);
            team.addWarrior(warrior);
            freeAgents.remove(warrior);
            return true;
        }
        return false;
    }
    
    /**
     * Release a warrior from a team
     */
    public boolean releaseWarrior(Team team, Warrior warrior) {
        if (team.removeWarrior(warrior)) {
            freeAgents.add(warrior);
            return true;
        }
        return false;
    }
    
    /**
     * Train a warrior
     */
    public void trainWarrior(Warrior warrior, Stat stat) {
        int cost = 100;
        Team team = findTeamForWarrior(warrior);
        if (team != null && team.getBudget() >= cost) {
            team.setBudget(team.getBudget() - cost);
            warrior.improveStat(stat, 1);
        }
    }
    
    /**
     * Calculate warrior hiring cost
     */
    private int calculateWarriorCost(Warrior warrior) {
        int baseCost = 500;
        int totalStats = warrior.getTotalStats();
        return baseCost + (totalStats * 50);
    }
    
    /**
     * Find which team a warrior belongs to
     */
    private Team findTeamForWarrior(Warrior warrior) {
        for (Team team : teams) {
            if (team.getWarriors().contains(warrior)) {
                return team;
            }
        }
        return null;
    }
    
    /**
     * End the current season
     */
    public void endSeason() {
        // Determine champion
        Team champion = determineChampion();
        System.out.println("Season Champion: " + champion.getName());
        
        // Reset for new season or archive
        currentWeek = 1;
    }
    
    /**
     * Determine season champion based on match history
     */
    private Team determineChampion() {
        Map<Team, Integer> wins = new HashMap<>();
        for (MatchResult result : matchHistory) {
            Team winner = result.getWinnerTeam();
            wins.put(winner, wins.getOrDefault(winner, 0) + 1);
        }
        
        Team champion = null;
        int maxWins = 0;
        for (Map.Entry<Team, Integer> entry : wins.entrySet()) {
            if (entry.getValue() > maxWins) {
                maxWins = entry.getValue();
                champion = entry.getKey();
            }
        }
        return champion;
    }
    
    // Getters
    public League getLeague() { return league; }
    public int getCurrentWeek() { return currentWeek; }
    public List<Team> getTeams() { return teams; }
    public List<Warrior> getFreeAgents() { return freeAgents; }
    public List<MatchResult> getMatchHistory() { return matchHistory; }
    
    /**
     * Inner class for match results
     */
    public static class MatchResult {
        private Team team1;
        private Team team2;
        private Warrior fighter1;
        private Warrior fighter2;
        private CombatResult combatResult;
        
        public MatchResult(Team team1, Team team2, Warrior f1, Warrior f2, CombatResult result) {
            this.team1 = team1;
            this.team2 = team2;
            this.fighter1 = f1;
            this.fighter2 = f2;
            this.combatResult = result;
        }
        
        public Team getWinnerTeam() {
            if (combatResult.getWinner() == fighter1) return team1;
            return team2;
        }
        
        public Team getLoserTeam() {
            if (combatResult.getWinner() == fighter1) return team2;
            return team1;
        }
        
        public CombatResult getCombatResult() { return combatResult; }
    }
}
