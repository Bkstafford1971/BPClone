package com.bloodspire.manager;

import com.bloodspire.model.Team;
import com.bloodspire.model.Warrior;
import com.bloodspire.model.Race;
import com.bloodspire.model.Weapon;
import com.bloodspire.model.Strategy;

import java.util.ArrayList;
import java.util.List;

/**
 * Manages the overall game state including league, teams, and progression
 */
public class GameStateManager {
    
    private String leagueName;
    private Team playerTeam;
    private List<Team> allTeams;
    private int currentWeek;
    private int playerGold;
    
    public GameStateManager(String leagueName) {
        this.leagueName = leagueName;
        this.allTeams = new ArrayList<>();
        this.currentWeek = 1;
        this.playerGold = 1000;
    }
    
    public void initializeNewLeague() {
        // Create player team
        this.playerTeam = new Team("Player Team", "Player Manager");
        allTeams.add(playerTeam);
        
        // Add some initial free agents or fighters
        // In full implementation, would generate proper roster
    }
    
    public String getLeagueName() {
        return leagueName;
    }
    
    public Team getPlayerTeam() {
        return playerTeam;
    }
    
    public List<Team> getAllTeams() {
        return allTeams;
    }
    
    public int getCurrentWeek() {
        return currentWeek;
    }
    
    public int getPlayerGold() {
        return playerGold;
    }
    
    public void setPlayerGold(int gold) {
        this.playerGold = gold;
    }
    
    public void advanceWeek() {
        this.currentWeek++;
    }
    
    public List<Warrior> getFreeAgents() {
        // Return list of available free agents
        List<Warrior> agents = new ArrayList<>();
        // In full implementation, would generate proper free agent pool
        return agents;
    }
    
    public boolean hireFighter(Warrior fighter, int cost) {
        if (playerGold >= cost && playerTeam.getFighters().size() < 8) {
            playerGold -= cost;
            playerTeam.addFighter(fighter);
            return true;
        }
        return false;
    }
    
    public boolean fireFighter(Warrior fighter) {
        return playerTeam.removeFighter(fighter);
    }
    
    public void trainFighter(Warrior fighter, String stat, int cost) {
        if (playerGold >= cost) {
            playerGold -= cost;
            // Apply training - in full implementation would modify stats
        }
    }
    
    public boolean canAfford(int cost) {
        return playerGold >= cost;
    }
}
