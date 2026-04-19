package com.bloodspire.game;

import com.bloodspire.model.Warrior;
import com.bloodspire.model.Team;
import com.bloodspire.model.Race;

import java.util.*;
import java.util.stream.Collectors;

/**
 * BLOODSPIRE Turn Matchmaking Engine
 * Builds the list of fights for a turn:
 *   1. Resolve blood challenges (highest priority).
 *   2. Resolve player-issued challenges (Presence-weighted).
 *   3. Match unmatched player warriors against opponent teams.
 *   4. Fill any remaining unmatched slots with scaled peasants.
 */
public class Matchmaking {
    
    private static final int ROOKIE_THRESHOLD = 5;
    private static final double BRACKET_UPPER = 1.30;
    private static final double BRACKET_LOWER = 0.90;
    private static final double CHALLENGE_FLOOR = 0.90;
    private static final Set<String> FODDER_TEAMS = Set.of("The Monsters", "The Peasants");
    private static final Set<String> FODDER_RACES = Set.of("Monster", "Peasant");
    
    private final Random random = new Random();
    
    /**
     * Numeric rating for matchmaking purposes.
     * APPROX: weighted sum of stats + fight experience + skill total.
     */
    public double warriorRating(Warrior warrior) {
        double statScore = warrior.getStrength() * 1.5 +
                          warrior.getDexterity() * 1.5 +
                          warrior.getConstitution() * 1.2 +
                          warrior.getIntelligence() * 0.8 +
                          warrior.getPresence() * 0.5 +
                          warrior.getSize() * 1.0;
        double experienceBonus = warrior.getTotalFights() * 0.3;
        double skillBonus = warrior.getSkills().values().stream().mapToInt(Integer::intValue).sum() * 0.2;
        return statScore + experienceBonus + skillBonus;
    }
    
    /**
     * Return True if the opponent's fight count falls within the player's
     * experience bracket. Uses the same formula as the challenge range UI.
     */
    public boolean inBracket(int playerFights, int opponentFights) {
        int lower = (int)(playerFights * BRACKET_LOWER);
        int upper = (int)(playerFights * BRACKET_UPPER);
        return lower <= opponentFights && opponentFights <= upper;
    }
    
    /**
     * Challenges ignore the upper bracket limit (warriors can punch up freely),
     * but bully-prevention applies: cannot challenge someone with fewer than
     * 90% of the challenger's fights.
     * Blood challenges skip this check entirely.
     */
    public boolean challengeInBracket(int challengerFights, int targetFights) {
        if (challengerFights <= ROOKIE_THRESHOLD) {
            return true;  // rookies can challenge anyone
        }
        int floor = (int)(challengerFights * CHALLENGE_FLOOR);
        return targetFights >= floor;
    }
    
    /**
     * Calculate average rating for a team based on active warriors.
     */
    public double teamAvgRating(Team team) {
        List<Warrior> active = team.getActiveWarriors();
        if (active.isEmpty()) {
            return 0.0;
        }
        return active.stream().mapToDouble(this::warriorRating).average().orElse(0.0);
    }
    
    /**
     * Determine if a challenge goes through.
     * Guide formula: base_chance + (PRE - opp_PRE) percent.
     * Blood challenges have +20% bonus chance.
     * Champion challenges have +25% bonus chance (almost guaranteed to succeed).
     */
    public boolean challengeSucceeds(int challengerPresence, int targetPresence, 
                                    boolean isBloodChallenge, boolean isChampionChallenge) {
        // Champion challenges have very high success rate
        if (isChampionChallenge) {
            int base = 100;  // Nearly guaranteed, but level adjustment still applies
            int adj = challengerPresence - targetPresence;
            int chance = Math.max(5, Math.min(95, base + adj));
            return random.nextInt(100) + 1 <= chance;
        }
        
        int base = isBloodChallenge ? 85 : 75;
        int adj = challengerPresence - targetPresence;
        int chance = Math.max(5, Math.min(95, base + adj));
        return random.nextInt(100) + 1 <= chance;
    }
    
    /**
     * Check if target warrior or team can avoid the challenge.
     * Returns True if challenge is avoided (blocked), False if it proceeds.
     */
    public boolean attemptAvoidChallenge(Warrior targetWarrior, Team targetTeam,
                                        String challengerName, String challengerManager) {
        // Check warrior-specific avoidance (60-70% success)
        if (targetWarrior.isAvoidingWarrior(challengerName)) {
            int avoidChance = 60 + random.nextInt(11);  // 60-70
            int roll = random.nextInt(100) + 1;
            if (roll <= avoidChance) {
                return true;  // Challenge avoided
            }
        }
        
        // Check manager-level avoidance (25-30% success)
        if (targetTeam.isAvoidingManager(challengerManager)) {
            int avoidChance = 25 + random.nextInt(6);  // 25-30
            int roll = random.nextInt(100) + 1;
            if (roll <= avoidChance) {
                return true;  // Challenge avoided
            }
        }
        
        return false;  // Challenge proceeds
    }
    
    /**
     * Find the best-matched opponent warrior from all available teams.
     */
    public Map.Entry<Warrior, Team> findOpponent(Warrior playerWarrior, List<Team> opponentTeams,
                                                 Set<String> alreadyMatched, Set<String> globalUsed) {
        double playerRating = warriorRating(playerWarrior);
        int playerFights = playerWarrior.getTotalFights();
        Set<String> used = globalUsed != null ? globalUsed : new HashSet<>();
        
        // Filter available teams and warriors
        List<Team> candidates = opponentTeams.stream()
            .filter(t -> !alreadyMatched.contains(t.getTeamId()))
            .filter(t -> {
                List<Warrior> available = t.getActiveWarriors().stream()
                    .filter(w -> !used.contains(w.getName()))
                    .collect(Collectors.toList());
                return available.stream()
                    .anyMatch(w -> inBracket(playerFights, w.getTotalFights()));
            })
            .collect(Collectors.toList());
        
        if (candidates.isEmpty()) {
            return null;
        }
        
        // Sort by closeness of team average rating (using only available warriors)
        candidates.sort(Comparator.comparingDouble(t -> {
            List<Warrior> available = t.getActiveWarriors().stream()
                .filter(w -> !used.contains(w.getName()))
                .collect(Collectors.toList());
            if (available.isEmpty()) return Double.MAX_VALUE;
            double avgRating = available.stream().mapToDouble(this::warriorRating).average().orElse(0.0);
            return Math.abs(avgRating - playerRating);
        }));
        
        for (Team bestTeam : candidates) {
            List<Warrior> available = bestTeam.getActiveWarriors().stream()
                .filter(w -> !used.contains(w.getName()))
                .collect(Collectors.toList());
            if (available.isEmpty()) continue;
            
            List<Warrior> inBracket = available.stream()
                .filter(w -> inBracket(playerWarrior.getTotalFights(), w.getTotalFights()))
                .collect(Collectors.toList());
            
            List<Warrior> pool = inBracket.isEmpty() ? available : inBracket;
            pool.sort(Comparator.comparingDouble(w -> Math.abs(warriorRating(w) - playerRating)));
            
            if (!pool.isEmpty()) {
                return new AbstractMap.SimpleEntry<>(pool.get(0), bestTeam);
            }
        }
        
        return null;
    }
}
