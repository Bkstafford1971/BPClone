package com.bloodspire.engine;

import com.bloodspire.model.*;
import java.util.Random;
import java.util.List;
import java.util.ArrayList;

/**
 * Generates narrative text for combat events, injuries, and match outcomes.
 * Port of narrative.py
 */
public class NarrativeEngine {
    
    private final Random random = new Random();
    
    // Templates for various combat actions
    private static final String[] ATTACK_MISS_TEMPLATES = {
        "{attacker} swings wildly but misses {defender}!",
        "{attacker}'s attack slips past {defender}'s guard.",
        "{defender} easily dodges {attacker}'s clumsy strike.",
        "{attacker} overcommits and whiffs completely.",
        "The crowd boos as {attacker} fails to connect."
    };
    
    private static final String[] ATTACK_HIT_TEMPLATES = {
        "{attacker} lands a solid blow on {defender}!",
        "{weapon} crashes into {defender}'s {location}!",
        "{attacker} connects cleanly with {defender}.",
        "A brutal strike from {attacker} finds its mark!",
        "{defender} grunts as {attacker}'s weapon bites deep."
    };
    
    private static final String[] CRITICAL_HIT_TEMPLATES = {
        "CRITICAL HIT! {attacker} smashes {defender} with devastating force!",
        "A bone-crushing blow! {attacker} nearly knocks {defender} out!",
        "Perfect timing! {attacker}'s strike echoes through the arena!",
        "Blood flies as {attacker} lands a perfect critical hit!"
    };
    
    private static final String[] KNOCKDOWN_TEMPLATES = {
        "{defender} hits the dirt hard!",
        "Down goes {defender}!",
        "{attacker} sends {defender} sprawling!",
        "The crowd roars as {defender} is knocked off their feet!"
    };
    
    private static final String[] BLEED_TEMPLATES = {
        "Blood spurts from {defender}'s wound!",
        "{defender} is bleeding heavily!",
        "A deep gash opens up on {defender}!",
        "The cut is severe; {defender} is losing blood fast!"
    };
    
    private static final String[] STUN_TEMPLATES = {
        "{defender} looks dazed and confused!",
        "The blow leaves {defender} seeing stars!",
        "{defender} staggers, unable to focus!",
        "Stunned! {defender} can barely stand!"
    };

    public NarrativeEngine() {}

    /**
     * Generate narrative for a missed attack
     */
    public String generateMiss(Warrior attacker, Warrior defender, Weapon weapon) {
        String template = ATTACK_MISS_TEMPLATES[random.nextInt(ATTACK_MISS_TEMPLATES.length)];
        return formatTemplate(template, attacker, defender, weapon, null);
    }

    /**
     * Generate narrative for a successful hit
     */
    public String generateHit(Warrior attacker, Warrior defender, Weapon weapon, int damage, String location) {
        String template = ATTACK_HIT_TEMPLATES[random.nextInt(ATTACK_HIT_TEMPLATES.length)];
        return formatTemplate(template, attacker, defender, weapon, location) + 
               " Deals " + damage + " damage.";
    }

    /**
     * Generate narrative for a critical hit
     */
    public String generateCriticalHit(Warrior attacker, Warrior defender, Weapon weapon, int damage, String location) {
        String template = CRITICAL_HIT_TEMPLATES[random.nextInt(CRITICAL_HIT_TEMPLATES.length)];
        return formatTemplate(template, attacker, defender, weapon, location) + 
               " CRITICAL! Deals " + damage + " damage!";
    }

    /**
     * Generate narrative for a knockdown
     */
    public String generateKnockdown(Warrior victim, Warrior attacker) {
        String template = KNOCKDOWN_TEMPLATES[random.nextInt(KNOCKDOWN_TEMPLATES.length)];
        return formatTemplateSimple(template, victim.getName(), attacker != null ? attacker.getName() : "the fight");
    }

    /**
     * Generate narrative for bleeding
     */
    public String generateBleeding(Warrior victim) {
        String template = BLEED_TEMPLATES[random.nextInt(BLEED_TEMPLATES.length)];
        return formatTemplateSimple(template, victim.getName(), "");
    }

    /**
     * Generate narrative for stun
     */
    public String generateStun(Warrior victim) {
        String template = STUN_TEMPLATES[random.nextInt(STUN_TEMPLATES.length)];
        return formatTemplateSimple(template, victim.getName(), "");
    }

    /**
     * Generate narrative for a special move (e.g., Decoy, Calculated Attack)
     */
    public String generateSpecialMove(String moveName, Warrior user, Warrior target, boolean success) {
        if (moveName.equals("Decoy")) {
            if (success) {
                return user.getName() + " feints beautifully, drawing " + target.getName() + " into a trap!";
            } else {
                return user.getName() + " attempts a decoy, but " + target.getName() + " sees right through it!";
            }
        } else if (moveName.equals("Calculated Attack")) {
            if (success) {
                return user.getName() + " carefully analyzes " + target.getName() + "'s stance and strikes precisely!";
            } else {
                return user.getName() + " tries to calculate the perfect angle but hesitates too long!";
            }
        }
        return user.getName() + " attempts " + moveName + "!";
    }

    /**
     * Generate narrative for a wound/injury
     */
    public String generateWound(Warrior victim, String bodyPart, int severity) {
        String severityText = severity > 5 ? "severe" : (severity > 2 ? "moderate" : "minor");
        return victim.getName() + " suffers a " + severityText + " injury to their " + bodyPart + "!";
    }

    /**
     * Generate narrative for match start
     */
    public String generateMatchStart(Warrior w1, Warrior w2, String arenaName) {
        return "Welcome to " + arenaName + "! In this corner, " + w1.getFullName() + 
               "! And in this corner, " + w2.getFullName() + "! FIGHT!";
    }

    /**
     * Generate narrative for match end
     */
    public String generateMatchEnd(Warrior winner, Warrior loser, String method) {
        if (method.equals("KO")) {
            return winner.getName() + " stands victorious as " + loser.getName() + " lies unconscious!";
        } else if (method.equals("Concede")) {
            return winner.getName() + " wins as " + loser.getName() + " concedes defeat!";
        } else if (method.equals("Death")) {
            return "A fatal blow! " + loser.getName() + " has died in the arena. " + winner.getName() + " is the victor!";
        }
        return winner.getName() + " defeats " + loser.getName() + " by " + method + "!";
    }

    /**
     * Helper to format templates with warrior names and weapon info
     */
    private String formatTemplate(String template, Warrior attacker, Warrior defender, Weapon weapon, String location) {
        String result = template;
        result = result.replace("{attacker}", attacker.getName());
        result = result.replace("{defender}", defender.getName());
        result = result.replace("{weapon}", weapon != null ? weapon.getName() : "fist");
        result = result.replace("{location}", location != null ? location : "body");
        return result;
    }

    /**
     * Helper for simpler templates
     */
    private String formatTemplateSimple(String template, String name1, String name2) {
        String result = template;
        result = result.replace("{defender}", name1);
        result = result.replace("{victim}", name1);
        result = result.replace("{attacker}", name2);
        return result;
    }
    
    /**
     * Generate round summary
     */
    public String generateRoundSummary(int roundNum, Warrior w1, Warrior w2) {
        return "--- Round " + roundNum + " ---\n" + 
               w1.getName() + " (HP: " + w1.getCurrentHealth() + "/" + w1.getMaxHealth() + 
               ", Stamina: " + w1.getCurrentStamina() + ") vs " +
               w2.getName() + " (HP: " + w2.getCurrentHealth() + "/" + w2.getMaxHealth() + 
               ", Stamina: " + w2.getCurrentStamina() + ")";
    }
}
