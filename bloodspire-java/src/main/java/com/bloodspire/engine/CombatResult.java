package com.bloodspire.engine;

import com.bloodspire.model.Warrior;
import com.bloodspire.model.Wound;
import java.util.List;
import java.util.ArrayList;

/**
 * Represents the result of a combat encounter.
 */
public class CombatResult {
    private Warrior winner;
    private Warrior loser;
    private String endMethod; // "KO", "Concede", "Death", etc.
    private List<Wound> wounds;
    private int rounds;
    private String lastActionNarrative;
    public List<String> narrative;
    public int w1FinalHealth;
    public int w2FinalHealth;
    public int turns;
    
    public CombatResult(Warrior winner, Warrior loser, String endMethod) {
        this.winner = winner;
        this.loser = loser;
        this.endMethod = endMethod;
        this.rounds = 0;
        this.narrative = new ArrayList<>();
        this.w1FinalHealth = 0;
        this.w2FinalHealth = 0;
        this.turns = 0;
    }
    
    public CombatResult() {
        this.narrative = new ArrayList<>();
    }
    
    public Warrior getWinner() {
        return winner;
    }
    
    public void setWinner(Warrior winner) {
        this.winner = winner;
    }
    
    public Warrior getLoser() {
        return loser;
    }
    
    public void setLoser(Warrior loser) {
        this.loser = loser;
    }
    
    public String getEndMethod() {
        return endMethod;
    }
    
    public void setEndMethod(String endMethod) {
        this.endMethod = endMethod;
    }
    
    public List<Wound> getWounds() {
        return wounds;
    }
    
    public void setWounds(List<Wound> wounds) {
        this.wounds = wounds;
    }
    
    public int getRounds() {
        return rounds;
    }
    
    public void setRounds(int rounds) {
        this.rounds = rounds;
    }
    
    public String getLastActionNarrative() {
        return lastActionNarrative;
    }
    
    public void setLastActionNarrative(String narrative) {
        this.lastActionNarrative = narrative;
    }
}
