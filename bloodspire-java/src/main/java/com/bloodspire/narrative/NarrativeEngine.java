package com.bloodspire.narrative;

import com.bloodspire.model.Warrior;
import java.util.Random;

/**
 * Generates narrative text for combat actions, hits, misses, wounds, and fight outcomes.
 * Ported from narrative.py to provide rich combat descriptions.
 */
public class NarrativeEngine {
    
    private Random random;
    
    // Action verbs for different styles
    private static final String[] CLEAVE_ACTIONS = {"cleaves", "hacks", "chops", "slashes"};
    private static final String[] BASH_ACTIONS = {"smashes", "crushes", "batters", "pounds"};
    private static final String[] SLASH_ACTIONS = {"slashes", "cuts", "gashes", "tears"};
    private static final String[] STRIKE_ACTIONS = {"strikes", "hits", "connects with", "lands on"};
    private static final String[] FINESSE_ACTIONS = {"flicks", "darts", "thrusts", "stabs"};
    private static final String[] OPEN_HAND_ACTIONS = {"punches", "slams", "drives fist into", "clubs"};
    
    // Hit location descriptions
    private static final String[] LOCATIONS = {
        "the head", "the shoulder", "the chest", "the arm", "the side",
        "the leg", "the abdomen", "the back", "the neck", "the face"
    };
    
    // Damage severity descriptions
    private static final String[] LIGHT_DAMAGE = {
        "a glancing blow", "a light wound", "a minor cut", "a scrape"
    };
    private static final String[] MODERATE_DAMAGE = {
        "a solid hit", "a deep cut", "a bruising blow", "a painful wound"
    };
    private static final String[] HEAVY_DAMAGE = {
        "a devastating strike", "a cruel gash", "a savage blow", "a terrible wound"
    };
    private static final String[] CRITICAL_DAMAGE = {
        "a crushing blow", "a bone-shattering hit", "a fatal-looking strike", "a gruesome injury"
    };
    
    public NarrativeEngine() {
        this.random = new Random();
    }
    
    public NarrativeEngine(long seed) {
        this.random = new Random(seed);
    }
    
    public String generateFightIntro(Warrior w1, Warrior w2) {
        return String.format("The fight begins! %s (%s) faces off against %s (%s).",
            w1.getName(), w1.getRace().getName(),
            w2.getName(), w2.getRace().getName());
    }
    
    public String generateMissNarrative(Warrior attacker, Warrior defender, int attackRoll, int defenseRoll) {
        String[] missPhrases = {
            "%s's attack whistles past %s!",
            "%s swings wildly but %s dodges easily!",
            "%s's strike is parried by %s!",
            "%s lunges but %s steps aside!",
            "%s's blow goes wide as %s ducks!"
        };
        String phrase = missPhrases[random.nextInt(missPhrases.length)];
        return String.format(phrase, attacker.getName(), defender.getName());
    }
    
    public String generateHitNarrative(Warrior attacker, Warrior defender, int damage, 
                                       String style, String weapon) {
        String action = getActionForStyle(style);
        String location = LOCATIONS[random.nextInt(LOCATIONS.length)];
        String damageDesc = getDamageDescription(damage);
        
        return String.format("%s %s %s with %s%s - %s!",
            attacker.getName(), action, location, 
            weapon.equals("fists") ? "their fists" : "their " + weapon,
            damage >= 8 ? " hard" : "",
            damageDesc);
    }
    
    public String generateCriticalHitNarrative(Warrior attacker, Warrior defender) {
        String[] critPhrases = {
            "CRITICAL HIT! %s lands a perfect strike on %s!",
            "DEVASTATING! %s's blow connects with brutal force!",
            "A MASTERFUL ATTACK! %s catches %s completely off-guard!",
            "BLOOD FLIES! %s delivers a crushing critical blow!"
        };
        String phrase = critPhrases[random.nextInt(critPhrases.length)];
        return String.format(phrase, attacker.getName(), defender.getName());
    }
    
    public String generateKnockdownNarrative(Warrior defender) {
        String[] knockdownPhrases = {
            "%s hits the ground hard!",
            "%s stumbles and falls!",
            "The blow sends %s sprawling!",
            "%s loses their footing and crashes down!"
        };
        String phrase = knockdownPhrases[random.nextInt(knockdownPhrases.length)];
        return String.format(phrase, defender.getName());
    }
    
    public String generateConcedeNarrative(Warrior conceding, Warrior winner) {
        return String.format("%s raises their hand in surrender! %s wins by concession!",
            conceding.getName(), winner.getName());
    }
    
    public String generateDecoyFeintSuccess(Warrior attacker, Warrior defender) {
        return String.format("%s feints brilliantly! %s is caught off-balance!",
            attacker.getName(), defender.getName());
    }
    
    public String generateJudgeDecision(Warrior w1, Warrior w2, Warrior winner) {
        if (winner == w1) {
            return String.format("The judges award the victory to %s after a close fight!", w1.getName());
        } else {
            return String.format("The judges award the victory to %s after a close fight!", w2.getName());
        }
    }
    
    public String generateWoundNarrative(Warrior wounded, String location, int severity) {
        String[] woundDescriptions = {
            "blood trickles from %s",
            "%s opens up with a nasty gash",
            "%s spurts blood",
            "a deep wound appears on %s"
        };
        String desc = woundDescriptions[Math.min(severity - 1, woundDescriptions.length - 1)];
        return String.format(desc, location);
    }
    
    public String generateBleedNarrative(Warrior warrior) {
        String[] bleedPhrases = {
            "%s is bleeding heavily!",
            "Blood pours from %s's wounds!",
            "%s can't stop the bleeding!",
            "The wound continues to bleed!"
        };
        String phrase = bleedPhrases[random.nextInt(bleedPhrases.length)];
        return String.format(phrase, warrior.getName());
    }
    
    public String generateStaminaDrainNarrative(Warrior warrior, int staminaLoss) {
        return String.format("%s is tiring visibly, losing %d stamina points.",
            warrior.getName(), staminaLoss);
    }
    
    public String generateEndOfFightNarrative(Warrior winner, Warrior loser, boolean knockout) {
        if (knockout) {
            return String.format("%s stands victorious over the unconscious form of %s!",
                winner.getName(), loser.getName());
        } else {
            return String.format("%s defeats %s in a hard-fought battle!",
                winner.getName(), loser.getName());
        }
    }
    
    private String getActionForStyle(String style) {
        if (style == null || style.isEmpty()) {
            return STRIKE_ACTIONS[random.nextInt(STRIKE_ACTIONS.length)];
        }
        
        switch (style.toLowerCase()) {
            case "cleave":
                return CLEAVE_ACTIONS[random.nextInt(CLEAVE_ACTIONS.length)];
            case "bash":
                return BASH_ACTIONS[random.nextInt(BASH_ACTIONS.length)];
            case "slash":
                return SLASH_ACTIONS[random.nextInt(SLASH_ACTIONS.length)];
            case "strike":
                return STRIKE_ACTIONS[random.nextInt(STRIKE_ACTIONS.length)];
            case "finesse":
            case "duelist":
            case "acrobat":
                return FINESSE_ACTIONS[random.nextInt(FINESSE_ACTIONS.length)];
            case "open hand":
                return OPEN_HAND_ACTIONS[random.nextInt(OPEN_HAND_ACTIONS.length)];
            default:
                return STRIKE_ACTIONS[random.nextInt(STRIKE_ACTIONS.length)];
        }
    }
    
    private String getDamageDescription(int damage) {
        if (damage <= 3) {
            return LIGHT_DAMAGE[random.nextInt(LIGHT_DAMAGE.length)];
        } else if (damage <= 7) {
            return MODERATE_DAMAGE[random.nextInt(MODERATE_DAMAGE.length)];
        } else if (damage <= 12) {
            return HEAVY_DAMAGE[random.nextInt(HEAVY_DAMAGE.length)];
        } else {
            return CRITICAL_DAMAGE[random.nextInt(CRITICAL_DAMAGE.length)];
        }
    }
}
