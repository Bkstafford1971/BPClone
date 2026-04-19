package com.bloodspire.model;

/**
 * Represents a league in BLOODSPIRE.
 */
public class League {
    private String name;
    private int seasonNumber;
    private int currentWeek;
    private int maxWeeks;
    
    public League(String name) {
        this.name = name;
        this.seasonNumber = 1;
        this.currentWeek = 1;
        this.maxWeeks = 20;
    }
    
    public String getName() {
        return name;
    }
    
    public void setName(String name) {
        this.name = name;
    }
    
    public int getSeasonNumber() {
        return seasonNumber;
    }
    
    public void setSeasonNumber(int seasonNumber) {
        this.seasonNumber = seasonNumber;
    }
    
    public int getCurrentWeek() {
        return currentWeek;
    }
    
    public void setCurrentWeek(int currentWeek) {
        this.currentWeek = currentWeek;
    }
    
    public int getMaxWeeks() {
        return maxWeeks;
    }
    
    public void setMaxWeeks(int maxWeeks) {
        this.maxWeeks = maxWeeks;
    }
}
