package com.bloodspire.persistence;

import com.bloodspire.model.Team;
import com.bloodspire.model.Warrior;

import java.io.*;
import java.nio.file.*;
import java.util.HashMap;
import java.util.Map;

/**
 * BLOODSPIRE Save & Load System
 * All data is stored as JSON files under the saves/ directory.
 */
public class SaveSystem {
    
    private final String baseDir;
    private final String savesDir;
    private final String teamsDir;
    private final String fightsDir;
    private final String logsDir;
    private final String gameStateFile;
    private final String scoutingFile;
    private final String monsterTeamFile;
    
    private Map<String, Object> gameState;
    
    public SaveSystem() {
        this.baseDir = System.getProperty("user.dir");
        this.savesDir = baseDir + File.separator + "saves";
        this.teamsDir = savesDir + File.separator + "teams";
        this.fightsDir = savesDir + File.separator + "fights";
        this.logsDir = savesDir + File.separator + "logs";
        this.gameStateFile = savesDir + File.separator + "game_state.json";
        this.scoutingFile = savesDir + File.separator + "scouting.json";
        this.monsterTeamFile = savesDir + File.separator + "monster_team.json";
        
        ensureDirs();
        loadGameState();
    }
    
    public SaveSystem(String customBaseDir) {
        this.baseDir = customBaseDir;
        this.savesDir = baseDir + File.separator + "saves";
        this.teamsDir = savesDir + File.separator + "teams";
        this.fightsDir = savesDir + File.separator + "fights";
        this.logsDir = savesDir + File.separator + "logs";
        this.gameStateFile = savesDir + File.separator + "game_state.json";
        this.scoutingFile = savesDir + File.separator + "scouting.json";
        this.monsterTeamFile = savesDir + File.separator + "monster_team.json";
        
        ensureDirs();
        loadGameState();
    }
    
    private void ensureDirs() {
        for (String path : new String[]{savesDir, teamsDir, fightsDir, logsDir}) {
            new File(path).mkdirs();
        }
    }
    
    private void loadGameState() {
        try {
            File file = new File(gameStateFile);
            if (file.exists()) {
                String content = Files.readString(file.toPath());
                gameState = JsonUtil.fromJson(content, Map.class);
            } else {
                gameState = new HashMap<>();
                gameState.put("next_team_id", 1);
                gameState.put("next_fight_id", 1);
                gameState.put("turn_number", 0);
                saveGameState();
            }
        } catch (IOException e) {
            System.err.println("ERROR: Could not load game state: " + e.getMessage());
            gameState = new HashMap<>();
            gameState.put("next_team_id", 1);
            gameState.put("next_fight_id", 1);
            gameState.put("turn_number", 0);
        }
    }
    
    private void saveGameState() {
        try {
            String json = JsonUtil.toJson(gameState);
            Files.writeString(Path.of(gameStateFile), json);
        } catch (IOException e) {
            System.err.println("ERROR: Could not save game state: " + e.getMessage());
        }
    }
    
    public synchronized int getNextTeamId() {
        int id = (int) gameState.getOrDefault("next_team_id", 1);
        gameState.put("next_team_id", id + 1);
        saveGameState();
        return id;
    }
    
    public synchronized int getNextFightId() {
        int id = (int) gameState.getOrDefault("next_fight_id", 1);
        gameState.put("next_fight_id", id + 1);
        saveGameState();
        return id;
    }
    
    public synchronized int getTurnNumber() {
        return (int) gameState.getOrDefault("turn_number", 0);
    }
    
    public synchronized void setTurnNumber(int turn) {
        gameState.put("turn_number", turn);
        saveGameState();
    }
    
    public void saveTeam(Team team) {
        ensureDirs();
        String filename = teamsDir + File.separator + "team_" + String.format("%04d", team.getTeamId()) + ".json";
        try {
            String json = JsonUtil.toJson(team.toMap());
            Files.writeString(Path.of(filename), json);
        } catch (IOException e) {
            System.err.println("ERROR: Could not save team " + team.getTeamName() + ": " + e.getMessage());
        }
    }
    
    public Team loadTeam(int teamId) {
        String filename = teamsDir + File.separator + "team_" + String.format("%04d", teamId) + ".json";
        try {
            File file = new File(filename);
            if (!file.exists()) return null;
            String content = Files.readString(file.toPath());
            Map<String, Object> data = JsonUtil.fromJson(content, Map.class);
            return Team.fromMap(data);
        } catch (IOException e) {
            System.err.println("ERROR: Could not load team " + teamId + ": " + e.getMessage());
            return null;
        }
    }
    
    public void saveFightLog(int fightId, String narrative) {
        ensureDirs();
        String filename = fightsDir + File.separator + "fight_" + String.format("%04d", fightId) + ".txt";
        try {
            Files.writeString(Path.of(filename), narrative);
        } catch (IOException e) {
            System.err.println("ERROR: Could not save fight log " + fightId + ": " + e.getMessage());
        }
    }
    
    public String loadFightLog(int fightId) {
        String filename = fightsDir + File.separator + "fight_" + String.format("%04d", fightId) + ".txt";
        try {
            File file = new File(filename);
            if (!file.exists()) return null;
            return Files.readString(file.toPath());
        } catch (IOException e) {
            System.err.println("ERROR: Could not load fight log " + fightId + ": " + e.getMessage());
            return null;
        }
    }
    
    public void saveMonsterTeam(Team team) {
        ensureDirs();
        try {
            String json = JsonUtil.toJson(team.toMap());
            Files.writeString(Path.of(monsterTeamFile), json);
        } catch (IOException e) {
            System.err.println("ERROR: Could not save monster team: " + e.getMessage());
        }
    }
    
    public Team loadMonsterTeam() {
        try {
            File file = new File(monsterTeamFile);
            if (!file.exists()) return null;
            String content = Files.readString(file.toPath());
            Map<String, Object> data = JsonUtil.fromJson(content, Map.class);
            return Team.fromMap(data);
        } catch (IOException e) {
            System.err.println("WARNING: Could not load monster team: " + e.getMessage());
            return null;
        }
    }
}
