package com.bloodspire.model;

/**
 * Snapshot of one warrior's in-fight status at the start of a minute.
 * Passed to the trigger evaluator and to the narrative engine.
 */
public class FighterState {
    private final Warrior warrior;
    private final int currentHp;
    private final int maxHp;
    private final double endurance;      // 0.0 – 100.0
    private final boolean isOnGround;
    private final int activeStrategyIdx; // 1-indexed display number of the current strategy
    private final Strategy activeStrategy;

    public FighterState(Warrior warrior, int currentHp, int maxHp, double endurance,
                        boolean isOnGround, int activeStrategyIdx, Strategy activeStrategy) {
        this.warrior = warrior;
        this.currentHp = currentHp;
        this.maxHp = maxHp;
        this.endurance = endurance;
        this.isOnGround = isOnGround;
        this.activeStrategyIdx = activeStrategyIdx;
        this.activeStrategy = activeStrategy;
    }

    public Warrior getWarrior() { return warrior; }
    public int getCurrentHp() { return currentHp; }
    public int getMaxHp() { return maxHp; }
    public double getEndurance() { return endurance; }
    public boolean isOnGround() { return isOnGround; }
    public int getActiveStrategyIdx() { return activeStrategyIdx; }
    public Strategy getActiveStrategy() { return activeStrategy; }

    public int getHpLost() {
        return Math.max(0, maxHp - currentHp);
    }

    public double getHpLostPct() {
        /** Fraction of max HP that has been lost (0.0–1.0). */
        if (maxHp <= 0) {
            return 0.0;
        }
        return (double) getHpLost() / maxHp;
    }

    public boolean isVeryTired() {
        return endurance <= 20.0;
    }

    public boolean isSomewhatTired() {
        return endurance <= 40.0;
    }

    public boolean isSlightlyTired() {
        return endurance <= 60.0;
    }

    // Legacy alias kept for backwards compatibility with old saves
    public boolean isTired() {
        return isSlightlyTired();
    }
}
