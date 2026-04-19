package com.bloodspire.game;

import com.bloodspire.model.Warrior;
import com.bloodspire.model.Team;

/**
 * One fight bout scheduled for the current turn.
 */
public class ScheduledFight {
    private Warrior playerWarrior;
    private Warrior opponent;
    private Team playerTeam;
    private Team opponentTeam;
    private String opponentManager;  // Display name for the narrative header
    private String fightType;        // "challenge", "standard", "peasant", "blood_challenge"
    private FightResult result;
    private Integer fightId;
    private String challengerName;   // warrior name of who initiated the challenge
    
    public ScheduledFight(Warrior playerWarrior, Warrior opponent, Team playerTeam, 
                         Team opponentTeam, String opponentManager, String fightType) {
        this.playerWarrior = playerWarrior;
        this.opponent = opponent;
        this.playerTeam = playerTeam;
        this.opponentTeam = opponentTeam;
        this.opponentManager = opponentManager;
        this.fightType = fightType;
    }
    
    // Getters and Setters
    public Warrior getPlayerWarrior() { return playerWarrior; }
    public void setPlayerWarrior(Warrior playerWarrior) { this.playerWarrior = playerWarrior; }
    
    public Warrior getOpponent() { return opponent; }
    public void setOpponent(Warrior opponent) { this.opponent = opponent; }
    
    public Team getPlayerTeam() { return playerTeam; }
    public void setPlayerTeam(Team playerTeam) { this.playerTeam = playerTeam; }
    
    public Team getOpponentTeam() { return opponentTeam; }
    public void setOpponentTeam(Team opponentTeam) { this.opponentTeam = opponentTeam; }
    
    public String getOpponentManager() { return opponentManager; }
    public void setOpponentManager(String opponentManager) { this.opponentManager = opponentManager; }
    
    public String getFightType() { return fightType; }
    public void setFightType(String fightType) { this.fightType = fightType; }
    
    public FightResult getResult() { return result; }
    public void setResult(FightResult result) { this.result = result; }
    
    public Integer getFightId() { return fightId; }
    public void setFightId(Integer fightId) { this.fightId = fightId; }
    
    public String getChallengerName() { return challengerName; }
    public void setChallengerName(String challengerName) { this.challengerName = challengerName; }
}
