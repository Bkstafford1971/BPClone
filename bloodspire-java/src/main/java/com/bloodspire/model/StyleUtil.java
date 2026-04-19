package com.bloodspire.model;

import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.util.Arrays;

/**
 * Utility class for style-related properties and operations.
 */
public class StyleUtil {

    private static final Map<String, StyleProperties> STYLE_PROPERTIES = new HashMap<>();
    private static final Map<String, List<String>> STYLE_SKILL_SYNERGY = new HashMap<>();

    static {
        // Endurance burn philosophy:
        //   Every style costs something — no style gains endurance in combat.
        //   Aggressive styles burn fast (8-10/action). Defensive styles break even
        //   or cost a little (1-2/action). This ensures fights resolve within ~5-6
        //   minutes without the ref becoming the primary deciding factor.
        
        STYLE_PROPERTIES.put("Total Kill", new StyleProperties(
            1.5, 5.0, -8, -8, 10.0, true, false, true,
            "Berserk. High damage, nearly no defense. Burns out fast."
        ));
        STYLE_PROPERTIES.put("Wall of Steel", new StyleProperties(
            1.5, -2.0, 3, 0, 9.0, true, false, false,
            "High attack rate, damage penalty, very high endurance cost."
        ));
        STYLE_PROPERTIES.put("Lunge", new StyleProperties(
            0.5, -1.0, 0, 4, 6.0, false, false, false,
            "Good dodge bonus. Rhythm bursts. Moderate endurance cost."
        ));
        STYLE_PROPERTIES.put("Bash", new StyleProperties(
            -0.5, 3.0, -1, -2, 7.0, false, false, false,
            "Good damage. Poor defense. High endurance cost."
        ));
        STYLE_PROPERTIES.put("Slash", new StyleProperties(
            -1.5, 4.0, -2, -3, 5.0, false, false, false,
            "Special slash hits. Slow, poor defense."
        ));
        STYLE_PROPERTIES.put("Strike", new StyleProperties(
            0.0, 0.0, 0, 0, 2.0, false, true, false,
            "Average in all things. Low but real endurance cost."
        ));
        STYLE_PROPERTIES.put("Engage & Withdraw", new StyleProperties(
            -0.3, -1.0, 0, 5, 2.0, false, true, false,
            "Very high dodge. Low endurance cost."
        ));
        STYLE_PROPERTIES.put("Counterstrike", new StyleProperties(
            -1.5, 2.0, 2, 0, 3.5, false, true, false,
            "Low native APM; counters provide extra attacks."
        ));
        STYLE_PROPERTIES.put("Decoy", new StyleProperties(
            -0.5, 1.0, 3, -1, 5.0, false, false, false,
            "Negates defense point. Can block parry."
        ));
        STYLE_PROPERTIES.put("Sure Strike", new StyleProperties(
            -1.0, 0.0, 0, 0, 1.5, false, true, false,
            "Highest hit %. Slow. Low endurance cost."
        ));
        STYLE_PROPERTIES.put("Calculated Attack", new StyleProperties(
            -1.0, 2.0, 0, 0, 1.5, false, true, false,
            "Hits critical locations. Slow. Low endurance cost."
        ));
        STYLE_PROPERTIES.put("Opportunity Throw", new StyleProperties(
            0.0, 0.0, 0, 0, 3.0, false, false, false,
            "Uses thrown weapons. Switches style after throws exhausted."
        ));
        STYLE_PROPERTIES.put("Martial Combat", new StyleProperties(
            0.3, -2.0, 1, 2, 4.0, false, false, false,
            "Special brawl attacks. Kick, punch, sweep."
        ));
        STYLE_PROPERTIES.put("Parry", new StyleProperties(
            -2.5, -4.0, 6, 2, 1.0, false, false, false,
            "Purely defensive. Very low endurance cost."
        ));
        STYLE_PROPERTIES.put("Defend", new StyleProperties(
            -2.0, -3.0, 4, 2, 1.0, false, true, false,
            "Slightly more active than Parry. Still very defensive."
        ));

        // Lists the skills most important to each style. As a warrior trains these
        // skills, the natural flaws of the style are gradually reduced.
        // Used by the training advisor and post-fight skill suggestions.
        
        STYLE_SKILL_SYNERGY.put("Counterstrike", Arrays.asList("Parry", "Initiative", "Feint", "Riposte"));
        STYLE_SKILL_SYNERGY.put("Decoy", Arrays.asList("Feint", "Parry", "Acrobatics", "Riposte"));
        STYLE_SKILL_SYNERGY.put("Lunge", Arrays.asList("Lunge", "Initiative", "Dodge", "Charge"));
        STYLE_SKILL_SYNERGY.put("Wall of Steel", Arrays.asList("Initiative", "Parry", "Dodge", "Feint", "Riposte", "Strike"));
        STYLE_SKILL_SYNERGY.put("Martial Combat", Arrays.asList("Brawl", "Sweep", "Dodge", "Acrobatics", "Charge"));
        STYLE_SKILL_SYNERGY.put("Bash", Arrays.asList("Charge", "Bash", "Strike"));
        STYLE_SKILL_SYNERGY.put("Sure Strike", Arrays.asList("Feint", "Riposte", "Strike"));
        STYLE_SKILL_SYNERGY.put("Engage & Withdraw", Arrays.asList("Dodge", "Lunge", "Acrobatics", "Charge", "Riposte"));
        STYLE_SKILL_SYNERGY.put("Defend", Arrays.asList("Disarm", "Sweep", "Acrobatics"));
        STYLE_SKILL_SYNERGY.put("Slash", Arrays.asList("Slash", "Cleave", "Strike"));
        STYLE_SKILL_SYNERGY.put("Parry", Arrays.asList("Parry", "Riposte", "Disarm"));
        STYLE_SKILL_SYNERGY.put("Opportunity Throw", Arrays.asList("Throw", "Initiative", "Feint"));
        STYLE_SKILL_SYNERGY.put("Calculated Attack", Arrays.asList("Initiative", "Slash", "Strike", "Feint", "Riposte"));
        STYLE_SKILL_SYNERGY.put("Strike", Arrays.asList("Strike", "Initiative", "Bash", "Cleave", "Charge"));
        STYLE_SKILL_SYNERGY.put("Total Kill", Arrays.asList("Charge", "Bash", "Cleave", "Strike"));
    }

    /**
     * Return StyleProperties for a given style name, defaulting to Strike.
     */
    public static StyleProperties getStyleProps(String styleName) {
        return STYLE_PROPERTIES.getOrDefault(styleName, STYLE_PROPERTIES.get("Strike"));
    }

    /**
     * Get the skill synergy list for a given style.
     */
    public static List<String> getStyleSkillSynergy(String styleName) {
        return STYLE_SKILL_SYNERGY.getOrDefault(styleName, STYLE_SKILL_SYNERGY.get("Strike"));
    }

    /**
     * Check if a style exists.
     */
    public static boolean hasStyle(String styleName) {
        return STYLE_PROPERTIES.containsKey(styleName);
    }

    /**
     * Get all available style names.
     */
    public static java.util.Set<String> getAllStyles() {
        return STYLE_PROPERTIES.keySet();
    }
}
