package com.bloodspire.game;

import com.bloodspire.model.Warrior;
import java.util.HashMap;
import java.util.Map;

/**
 * Summary of a completed fight. No draws exist in Bloodspire.
 */
public class FightResult {
    private final Warrior winner;
    private final Warrior loser;
    private final boolean loserDied;
    private final int minutesElapsed;
    private final String narrative;
    private final Map<String, Object> trainingResults;
    
    // Per-fighter combat metrics, used by update_recognition v2
    private final double winnerHpPct;      // winner's HP fraction at fight end
    private final double loserHpPct;       // loser's HP fraction at fight end
    private final int winnerKnockdowns;    // knockdowns delivered by winner
    private final int loserKnockdowns;     // knockdowns delivered by loser
    private final int winnerNearKills;     // times winner reduced opponent below 20% HP
    private final int loserNearKills;      // times loser reduced opponent below 20% HP

    public FightResult(Warrior winner, Warrior loser, boolean loserDied, int minutesElapsed, 
                       String narrative) {
        this.winner = winner;
        this.loser = loser;
        this.loserDied = loserDied;
        this.minutesElapsed = minutesElapsed;
        this.narrative = narrative;
        this.trainingResults = new HashMap<>();
        this.winnerHpPct = 1.0;
        this.loserHpPct = 0.0;
        this.winnerKnockdowns = 0;
        this.loserKnockdowns = 0;
        this.winnerNearKills = 0;
        this.loserNearKills = 0;
    }

    public FightResult(Warrior winner, Warrior loser, boolean loserDied, int minutesElapsed,
                       String narrative, Map<String, Object> trainingResults,
                       double winnerHpPct, double loserHpPct, int winnerKnockdowns,
                       int loserKnockdowns, int winnerNearKills, int loserNearKills) {
        this.winner = winner;
        this.loser = loser;
        this.loserDied = loserDied;
        this.minutesElapsed = minutesElapsed;
        this.narrative = narrative;
        this.trainingResults = trainingResults != null ? trainingResults : new HashMap<>();
        this.winnerHpPct = winnerHpPct;
        this.loserHpPct = loserHpPct;
        this.winnerKnockdowns = winnerKnockdowns;
        this.loserKnockdowns = loserKnockdowns;
        this.winnerNearKills = winnerNearKills;
        this.loserNearKills = loserNearKills;
    }

    public Warrior getWinner() { return winner; }
    public Warrior getLoser() { return loser; }
    public boolean isLoserDied() { return loserDied; }
    public int getMinutesElapsed() { return minutesElapsed; }
    public String getNarrative() { return narrative; }
    public Map<String, Object> getTrainingResults() { return trainingResults; }
    public double getWinnerHpPct() { return winnerHpPct; }
    public double getLoserHpPct() { return loserHpPct; }
    public int getWinnerKnockdowns() { return winnerKnockdowns; }
    public int getLoserKnockdowns() { return loserKnockdowns; }
    public int getWinnerNearKills() { return winnerNearKills; }
    public int getLoserNearKills() { return loserNearKills; }
}
