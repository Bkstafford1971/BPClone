package com.bloodspire.engine;

import com.bloodspire.model.*;
import com.bloodspire.narrative.NarrativeGenerator;

import java.util.*;

/**
 * CombatEngine - BLOODSPIRE Combat Engine v2
 */
public class CombatEngine {

    // Feature flags
    private static boolean showFavoriteWeapon = false;
    private static boolean showLuckFactor = false;
    private static boolean showMaxHp = false;

    public static void setShowFavoriteWeapon(boolean enabled) { showFavoriteWeapon = enabled; }
    public static void setShowLuckFactor(boolean enabled) { showLuckFactor = enabled; }
    public static void setShowMaxHp(boolean enabled) { showMaxHp = enabled; }

    // Weapon categorization
    private static final Set<String> CLEAVE_WEAPONS = new HashSet<>(Arrays.asList(
        "great_sword", "halberd", "great_axe", "battle_axe", "pole_axe",
        "bastard_sword", "scimitar", "scythe", "pick_axe"
    ));
    private static final Set<String> BASH_WEAPONS = new HashSet<>(Arrays.asList(
        "ball_and_chain", "club", "great_pick", "military_pick", "great_staff",
        "great_sword", "halberd", "hammer", "mace", "maul", "morningstar",
        "quarterstaff", "target_shield", "tower_shield", "war_hammer"
    ));
    private static final Set<String> SLASH_WEAPONS = new HashSet<>(Arrays.asList(
        "short_sword", "longsword", "broad_sword", "bastard_sword", "battle_axe",
        "great_axe", "hatchet", "francisca", "dagger", "epee", "knife",
        "scimitar", "scythe", "swordbreaker"
    ));
    private static final Set<String> OPEN_HAND_WEAPONS = new HashSet<>(Collections.singleton("open_hand"));

    private static final int DECOY_FEINT_PENALTY = 20;
    private static final int CA_PRECISION_DAMAGE_BONUS = 3;
    private static final double CA_PRECISION_ARMOR_BYPASS = 0.60;
    private static final int CA_PROBE_EMIT_CHANCE = 25;
    private static final double END_BRINK_THRESHOLD = 15.0;

    private static final String[][] REF_STONE_EVENTS = {
        {"The Ref hurls a large rock at {n}", "The rock connects with {n}'s temple, {n} staggers, eyes glazed."},
        {"The Ref scoops up a fist-sized stone and flings it at {n}", "It cracks hard against {n}'s ribs. {n} doubles over with a grunt."},
        {"The Ref hurls a jagged chunk of stone at {n}", "It opens a gash above {n}'s eye, {n} blinks through the blood, vision blurring."},
        {"The Ref seizes a heavy stone and hurls it at {n}", "The stone thuds into {n}'s chest. {n} gasps, the air driven from their lungs."},
        {"The Ref flings a sharp-edged rock at {n}", "It catches {n} across the shoulder, {n} winces and nearly drops their guard."},
        {"The Ref grabs a handful of gravel and hurls it straight at {n}'s face", "{n} recoils, blinded for a moment, eyes streaming."},
        {"The Ref hurls a stone at the back of {n}'s head", "{n} lurches forward, stumbling to keep their footing."},
        {"The Ref snatches up a loose cobble and sends it spinning at {n}", "It clips {n} across the jaw. {n} spits blood and shakes their head."}
    };

    private static final String[][] REF_WEAPON_EVENTS = {
        {"The Ref snatches up a length of chain and lashes it hard across {n}'s back", "{n} arches in agony, a ragged cry escaping them."},
        {"The Ref grabs a discarded wooden staff and drives it into {n}'s ribs", "The crack of wood on bone rings out, {n} bends double, wheezing."},
        {"The Ref seizes a blunted club and crashes it across {n}'s shoulders", "{n} staggers forward, knees buckling under the blow."},
        {"The Ref picks up a short iron rod and swings it hard into {n}'s thigh", "{n} stumbles badly, leg trembling, nearly losing their footing."},
        {"The Ref grabs a training sword and slaps the flat of it hard across {n}'s back", "The smack echoes across the pit, {n} flinches and lurches forward."}
    };

    private static final String[][] REF_FOLLOWUP_EVENTS = {
        {"Still unsatisfied, the Ref hurls another stone at {n}", "It clips {n} across the ear. {n} is visibly shaken."},
        {"The Ref shouts at {n} to fight, then flings a second stone", "The stone drives into {n}'s ribs. The crowd jeers."},
        {"The Ref storms forward and drives the butt of a spear into {n}'s back", "{n} pitches forward with a cry, barely keeping their feet."},
        {"Furious with {n}'s passivity, the Ref heaves another stone", "It strikes {n} hard in the kidney. {n} nearly goes down."},
        {"The crowd howls as the Ref hurls a second stone at {n}", "It catches {n} glancing across the jaw. {n} spits blood and staggers."}
    };

    private final Warrior warriorA, warriorB;
    private final String teamAName, teamBName, managerAName, managerBName;
    private final int posA, posB;
    private final boolean isMonsterFight;
    private final String challengerName;
    private final CombatState stateA, stateB;
    private final List<String> lines = new ArrayList<>();
    private int prevAttacksA = 0, prevAttacksB = 0;
    private final Set<String> usedAdvPhrases = new HashSet<>();
    private String lastAdvTier = "even", lastAdvWinner = "";

    private static class CombatState {
        final Warrior warrior;
        int currentHp;
        double endurance;
        boolean isOnGround = false;
        int activeStratIdx = 1;
        Strategy activeStrategy = null;
        int consecutiveGround = 0, concedeAttempts = 0, hpAtLastConcede = 9999;
        int knockdownsDealt = 0, nearKillsDealt = 0, bleedingWounds = 0;
        boolean usedFavoriteWeaponThisFight = false;

        CombatState(Warrior w, int hp, double end) { warrior = w; currentHp = hp; endurance = end; }

        FighterState toFighterState() {
            return new FighterState(warrior, currentHp, warrior.getMaxHp(), endurance, isOnGround, activeStratIdx, activeStrategy);
        }

        double getHpPct() { return currentHp / (double) Math.max(1, warrior.getMaxHp()); }

        boolean wantsToConcede() {
            if (currentHp <= 0) return true;
            return getHpPct() <= 0.25 && currentHp < hpAtLastConcede;
        }
    }

    public static class FightResult {
        public final Warrior winner, loser;
        public final boolean loserDied;
        public final int minutesElapsed;
        public String narrative;
        public Map<String, List<String>> trainingResults = new HashMap<>();
        public double winnerHpPct = 1.0, loserHpPct = 0.0;
        public int winnerKnockdowns = 0, loserKnockdowns = 0, winnerNearKills = 0, loserNearKills = 0;

        public FightResult(Warrior w, Warrior l, boolean d, int m) { winner = w; loser = l; loserDied = d; minutesElapsed = m; }
    }

    public CombatEngine(Warrior a, Warrior b, String ta, String tb, String ma, String mb, int pa, int pb, boolean mf, String cn) {
        warriorA = a; warriorB = b; teamAName = ta; teamBName = tb; managerAName = ma; managerBName = mb;
        posA = pa; posB = pb; isMonsterFight = mf; challengerName = cn;
        stateA = new CombatState(a, a.getMaxHp(), 100.0);
        stateB = new CombatState(b, b.getMaxHp(), 100.0);
        if (!a.getStrategies().isEmpty()) { stateA.activeStrategy = a.getStrategies().get(a.getStrategies().size()-1); stateA.activeStratIdx = a.getStrategies().size(); }
        if (!b.getStrategies().isEmpty()) { stateB.activeStrategy = b.getStrategies().get(b.getStrategies().size()-1); stateB.activeStratIdx = b.getStrategies().size(); }
    }

    public FightResult resolveFight() {
        lines.add(NarrativeGenerator.buildFightHeader(warriorA, warriorB, teamAName, teamBName, managerAName, managerBName, posA, posB, challengerName));
        lines.add("");
        applyPresenceHesitation();
        int minute = 0;
        FightResult result = null;
        while (true) {
            minute++;
            if (minute >= 9 && Math.random() < 0.40) throwStones(minute);
            result = runMinute(minute);
            if (result != null) break;
            if (minute >= 30 && !isMonsterFight) {
                double pctA = stateA.currentHp / (double) Math.max(1, warriorA.getMaxHp());
                double pctB = stateB.currentHp / (double) Math.max(1, warriorB.getMaxHp());
                Warrior win = pctA >= pctB ? warriorA : warriorB, los = pctA >= pctB ? warriorB : warriorA;
                emit(""); emit(win.getName().toUpperCase() + " wins on judges' decision!");
                result = makeResult(win, los, false, minute); break;
            }
            if (minute >= 60 && isMonsterFight) {
                Warrior dw = stateA.warrior, kw = stateB.warrior;
                dw.setDead(true);
                emit(""); emit(dw.getName().toUpperCase() + " collapses from sheer exhaustion!");
                emit(NarrativeGenerator.deathLine(dw.getName(), dw.getGender()));
                emit(""); emit(NarrativeGenerator.victoryLine(kw.getName(), dw.getName()));
                result = makeResult(kw, dw, true, minute); break;
            }
        }
        Map<String, List<String>> training = new HashMap<>();
        emit("");
        Object[] data = {{warriorA, warriorB}, {warriorB, warriorA}, {false, true}, {"warrior_a", "warrior_b"}};
        for (int i = 0; i < 2; i++) {
            Warrior w = (Warrior)((Object[])data[0])[i];
            Warrior opp = (Warrior)((Object[])data[1])[i];
            boolean isOpp = (boolean)((boolean[])data[2])[i];
            String pk = (String)((String[])data[3])[i];
            if (result.loserDied && result.loser == w) { training.put(pk, new ArrayList<>()); continue; }
            List<String> res = applyTraining(w, opp);
            training.put(pk, res);
            if (!res.isEmpty()) emit(NarrativeGenerator.trainingSummary(w.getName(), res, isOpp));
        }
        result.trainingResults = training;
        result.narrative = String.join("\n", lines);
        return result;
    }

    private FightResult makeResult(Warrior w, Warrior l, boolean d, int m) {
        CombatState ws = w == warriorA ? stateA : stateB, ls = w == warriorA ? stateB : stateA;
        FightResult r = new FightResult(w, l, d, m);
        r.narrative = String.join("\n", lines);
        r.winnerHpPct = Math.max(0.0, ws.currentHp / (double) Math.max(1, w.getMaxHp()));
        r.loserHpPct = Math.max(0.0, ls.currentHp / (double) Math.max(1, l.getMaxHp()));
        r.winnerKnockdowns = ws.knockdownsDealt; r.loserKnockdowns = ls.knockdownsDealt;
        r.winnerNearKills = ws.nearKillsDealt; r.loserNearKills = ls.nearKillsDealt;
        return r;
    }

    private String[] calcMinuteAdvantage() {
        int hpA = stateA.currentHp, hpB = stateB.currentHp;
        double endA = stateA.endurance, endB = stateB.endurance;
        double hpRatio = hpA / (double) Math.max(1, hpA + hpB);
        double score = Math.max(0.0, Math.min(1.0, hpRatio + (endA - endB) / 100.0 * 0.08));
        Warrior w, l; CombatState ws, ls; double mag;
        if (score >= 0.5) { w = warriorA; l = warriorB; ws = stateA; ls = stateB; mag = score; }
        else { w = warriorB; l = warriorA; ws = stateB; ls = stateA; mag = 1.0 - score; }
        if (ls.endurance <= END_BRINK_THRESHOLD && mag < 0.80) return new String[]{"brink_exhaustion", w.getName(), l.getName()};
        if (mag < 0.56) return new String[]{"even", "", ""};
        if (mag < 0.66) return new String[]{"slight", w.getName(), l.getName()};
        if (mag < 0.81) return new String[]{"clear", w.getName(), l.getName()};
        if (mag < 0.95) return new String[]{"dominating", w.getName(), l.getName()};
        return new String[]{"brink", w.getName(), l.getName()};
    }

    private FightResult runMinute(int minute) {
        emit("\nMINUTE " + minute);
        if (minute == 1) emit(NarrativeGenerator.FIGHT_OPENERS[new Random().nextInt(NarrativeGenerator.FIGHT_OPENERS.length)]);
        else {
            String[] adv = calcMinuteAdvantage();
            emit(NarrativeGenerator.minuteStatusLine(adv[1], adv[2], adv[0], lastAdvTier, lastAdvWinner, usedAdvPhrases));
            emit(""); lastAdvTier = adv[0]; lastAdvWinner = adv[1];
            if (Math.random() < 0.15) emit(NarrativeGenerator.crowdLine(warriorA.getRace().getName(), warriorB.getRace().getName()));
        }
        FighterState fsA = stateA.toFighterState(), fsB = stateB.toFighterState();
        StrategyResult srA = StrategyEvaluator.evaluateTriggers(warriorA.getStrategies(), fsA, fsB, minute);
        StrategyResult srB = StrategyEvaluator.evaluateTriggers(warriorB.getStrategies(), fsB, fsA, minute);
        if (srA.index != stateA.activeStratIdx) emit(NarrativeGenerator.strategySwitchLine(warriorA.getName(), srA.index));
        if (srB.index != stateB.activeStratIdx) emit(NarrativeGenerator.strategySwitchLine(warriorB.getName(), srB.index));
        stateA.activeStrategy = srA.strategy; stateA.activeStratIdx = srA.index;
        stateB.activeStrategy = srB.strategy; stateB.activeStratIdx = srB.index;
        for (CombatState st : Arrays.asList(stateA, stateB)) {
            if (st.isOnGround) {
                st.consecutiveGround++;
                int brawlRec = 40 + st.warrior.getSkills().getOrDefault("brawl", 0) * 8;
                int acroLvl = st.warrior.getSkills().getOrDefault("acrobatics", 0);
                int acroRec = acroLvl > 0 ? Math.min(85, acroLvl * 20) : 0;
                if (new Random().nextInt(100) < Math.max(brawlRec, acroRec)) {
                    st.isOnGround = false; st.consecutiveGround = 0;
                    emit(acroRec > brawlRec ? st.warrior.getName().toUpperCase() + " somersaults back to their feet!" : NarrativeGenerator.getupLine(st.warrior.getName(), st.warrior.getGender()));
                }
            }
        }
        int apmA = calcApm(warriorA, stateA.activeStrategy, stateA), apmB = calcApm(warriorB, stateB.activeStrategy, stateB);
        int remA = apmA, remB = apmB, actA = 0, actB = 0, crowd = 0;
        while (remA > 0 || remB > 0) {
            FightResult end = checkFatalInjury(); if (end != null) return end;
            if (++crowd >= 5 && Math.random() < 0.35) { emit(NarrativeGenerator.crowdLine(warriorA.getRace().getName(), warriorB.getRace().getName())); crowd = 0; }
            CombatState as_, ds_; Strategy ax, dx;
            if (remA > 0 && remB > 0) {
                int ia = initiativeRoll(warriorA, stateA.activeStrategy, stateA), ib = initiativeRoll(warriorB, stateB.activeStrategy, stateB);
                if (ia >= ib) { as_ = stateA; ds_ = stateB; ax = stateA.activeStrategy; dx = stateB.activeStrategy; remA--; actA++; }
                else { as_ = stateB; ds_ = stateA; ax = stateB.activeStrategy; dx = stateA.activeStrategy; remB--; actB++; }
            } else if (remA > 0) { as_ = stateA; ds_ = stateB; ax = stateA.activeStrategy; dx = stateB.activeStrategy; remA--; actA++; }
            else { as_ = stateB; ds_ = stateA; ax = stateB.activeStrategy; dx = stateA.activeStrategy; remB--; actB++; }
            FightResult r = resolveAction(as_, ds_, ax, dx, minute); if (r != null) return r;
            for (CombatState cst : Arrays.asList(stateA, stateB)) {
                CombatState ost = cst == stateA ? stateB : stateA;
                if (cst.wantsToConcede()) { cst.hpAtLastConcede = cst.currentHp; FightResult r2 = attemptConcede(cst, ost, minute); if (r2 != null) return r2; }
            }
        }
        for (String ln : updateEndurance(stateA, stateA.activeStrategy, actA, stateB)) emit(ln);
        for (String ln : updateEndurance(stateB, stateB.activeStrategy, actB, stateA)) emit(ln);
        prevAttacksA = actA; prevAttacksB = actB;
        return null;
    }

    private int d100() { return new Random().nextInt(100) + 1; }

    private int initiativeRoll(Warrior w, Strategy s, CombatState st) {
        int roll = d100();
        int dex = ArmorUtil.getEffectiveDexForRace(w.getDexterity(), w.getArmor()!=null?w.getArmor():"None", w.getHelm()!=null?w.getHelm():"None", w.getRace().getName());
        int dB = Math.max(-10, Math.min(10, (dex-10)*2));
        int sB = w.getSkills().getOrDefault("initiative", 0) * 3;
        int lB = w.getLuck();
        int rB = w.getRace().getModifiers().getInitiativeBonus();
        StyleProperties p = StyleUtil.getStyleProps(s.getStyle());
        int stM = (int)(p.apmModifier * 4);
        int aM = (s.getActivity()-5)*2;
        int eP = st.endurance < 40 ? (int)Math.max(0, (40-st.endurance)*0.3) : 0;
        return st.isOnGround ? Math.max(1, roll/2) : Math.max(1, roll+dB+sB+lB+rB+stM+aM-eP);
    }

    private int attackRoll(Warrior att, Strategy s, CombatState st) {
        int roll = d100();
        int dex = ArmorUtil.getEffectiveDexForRace(att.getDexterity(), att.getArmor()!=null?att.getArmor():"None", att.getHelm()!=null?att.getHelm():"None", att.getRace().getName());
        int dB = Math.max(-8, Math.min(8, dex-10));
        String wk = att.getPrimaryWeapon().toLowerCase().replace(" ","_").replace("&","and");
        int wB = att.getSkills().getOrDefault(wk, 0) * 5;
        int lB = att.getLuck();
        StyleProperties p = StyleUtil.getStyleProps(s.getStyle());
        int stB = (int)(p.apmModifier * 3);
        int fB = att.getSkills().getOrDefault("feint", 0) * 2;
        int luB = "Lunge".equals(s.getStyle()) ? att.getSkills().getOrDefault("lunge", 0) * 3 : 0;
        int eP = st.endurance < 30 ? (int)Math.max(0, (30-st.endurance)*0.5) : 0;
        int hP = st.currentHp <= 0 ? 30 : 0;
        int fav = (att.getFavoriteWeapon()!=null && att.getPrimaryWeapon().equals(att.getFavoriteWeapon())) ? 5 : 0;
        return Math.max(1, roll+dB+wB+lB+stB+fB+luB-eP-hP+fav);
    }

    private int defenseRoll(Warrior def, Strategy s, CombatState st, Warrior att, String aim, String atkStyle, boolean parry) {
        int roll = d100();
        int lB = def.getLuck();
        StyleProperties p = StyleUtil.getStyleProps(s.getStyle());
        String wk = def.getPrimaryWeapon().toLowerCase().replace(" ","_").replace("&","and");
        int wS = def.getSkills().getOrDefault(wk, 0);
        int dexT = def.getAttributeGains().getOrDefault("dexterity", 0);
        if (parry) {
            int sB = Math.max(-5, Math.min(5, (def.getStrength()-10)/2));
            int skB = def.getSkills().getOrDefault("parry", 0) * 4;
            int wB = wS * 3;
            int stB = p.parryBonus * 3;
            int aM = (5-s.getActivity())*2;
            int dTP = dexT * 2;
            int rPB = def.getRace().getModifiers().getParryBonus() * 3;
            int tot = roll+sB+skB+wB+stB+aM+lB+dTP+rPB;
            if (s.getDefensePoint()!=null && !"None".equals(s.getDefensePoint()) && s.getDefensePoint().equals(aim) && !"Decoy".equals(atkStyle)) tot += 15;
            try { Weapon sec = Weapons.getWeapon(def.getSecondaryWeapon()!=null?def.getSecondaryWeapon():"Open Hand"); if (sec.isShield()) tot += def.getRace().getModifiers().isShieldBonus()?10:5; } catch(Exception e){}
            if (p.totalKillMode) return Math.max(1, roll/3);
            if (st.endurance < 30) tot -= (int)((30-st.endurance)*0.4);
            if (st.isOnGround) tot -= 25;
            if (st.currentHp <= 0) tot -= 30;
            return Math.max(1, tot);
        } else {
            int dex = ArmorUtil.getEffectiveDexForRace(def.getDexterity(), def.getArmor()!=null?def.getArmor():"None", def.getHelm()!=null?def.getHelm():"None", def.getRace().getName());
            int dB = Math.max(-8, Math.min(8, dex-10));
            int skB = def.getSkills().getOrDefault("dodge", 0) * 4;
            int wB = wS * 2;
            int stB = p.dodgeBonus * 2;
            int aM = (s.getActivity()-5)*2;
            int szD = att.getSize()-def.getSize();
            int szB = szD>=3?5:(szD<=-3?-5:0);
            int dTD = (int)(dexT*2.5);
            int rDB = def.getRace().getModifiers().getDodgeBonus() * 2;
            int acr = def.getSkills().getOrDefault("acrobatics", 0);
            int acrB = acr > 0 ? acr*2 : 0;
            int tot = roll+dB+skB+wB+stB+aM+szB+lB+dTD+rDB+acrB;
            if (def.getRace().getModifiers().isHeavyWeaponPenalty()) {
                try { Weapon wp = Weapons.getWeapon(def.getPrimaryWeapon()); boolean two = "Open Hand".equals(def.getSecondaryWeapon()) && wp.isTwoHand(); boolean hvy = wp.getWeight()>=4.0||(wp.isTwoHand()&&two); if (hvy && !(def.getRace().getModifiers().isSpearException()&&"Polearm/Spear".equals(wp.getCategory()))) tot -= 10; } catch(Exception e){}
            }
            if (s.getDefensePoint()!=null && !"None".equals(s.getDefensePoint()) && s.getDefensePoint().equals(aim) && !"Decoy".equals(atkStyle)) tot += 15;
            try { Weapon sec = Weapons.getWeapon(def.getSecondaryWeapon()!=null?def.getSecondaryWeapon():"Open Hand"); if (sec.isShield()) tot += def.getRace().getModifiers().isShieldBonus()?10:5; } catch(Exception e){}
            if (p.totalKillMode) return Math.max(1, roll/3);
            if (st.endurance < 30) tot -= (int)((30-st.endurance)*0.4);
            if (st.isOnGround) tot -= 25;
            if (st.currentHp <= 0) tot -= 30;
            return Math.max(1, tot);
        }
    }

    private boolean attemptFeint(Warrior att, Warrior def, String dStyle) {
        if ("Counterstrike".equals(dStyle)) { int rc = 55+def.getSkills().getOrDefault("parry",0)*3; if (new Random().nextInt(100)+1 <= rc) return false; }
        int fs = att.getSkills().getOrDefault("feint", 0);
        int dB = Math.max(0, (att.getDexterity()-10)/2);
        int ch = Math.min(85, 25+fs*5+dB+att.getLuck()/3);
        return new Random().nextInt(100)+1 <= ch;
    }

    private boolean attemptPrecisionStrike(Warrior att, Warrior def, Weapon wp, String dStyle) {
        if (wp.getWeight()>=6.0 || (wp.getWeakStyles()!=null && wp.getWeakStyles().contains("Calculated Attack"))) return false;
        int wS = att.getSkills().getOrDefault(wp.getSkillKey(), 0);
        int dB = Math.max(0, (att.getDexterity()-10)/2);
        int ch = 20+wS*3+dB+att.getLuck()/3;
        if (wp.getWeight()>=4.5) ch -= 25; else if (wp.getWeight()>=3.5) ch -= 10;
        int bDS = Math.max(def.getSkills().getOrDefault("parry",0), def.getSkills().getOrDefault("dodge",0));
        ch -= bDS*4;
        if (Arrays.asList("Parry","Defend","Wall of Steel","Counterstrike").contains(dStyle)) ch -= 5;
        return new Random().nextInt(100)+1 <= Math.max(0, Math.min(75, ch));
    }

    private int[] calcDamageHybrid(Warrior att, Strategy aS, String wn, Warrior def, int margin, double precByp, double stylePen) {
        Weapon wp; try { wp = Weapons.getWeapon(wn); } catch(Exception e) { wp = Weapons.OPEN_HAND; }
        boolean two = "Open Hand".equals(att.getSecondaryWeapon()) && wp.isTwoHand();
        double base = wp.getWeight()*2.5 + Math.max(0.0, att.getStrength()-10)*0.6;
        if (wp.isFlailBypass()||"Flail".equals(wp.getCategory())) base += Math.max(0.0, att.getSize()-12)*0.4;
        if (two||wp.isTwoHand()) base *= 1.15;
        RacialModifiers rm = att.getRace().getModifiers();
        base += rm.getDamageBonus()-rm.getDamagePenalty();
        StyleProperties sp = StyleUtil.getStyleProps(aS.getStyle());
        base += sp.damageModifier + (5-aS.getActivity())*0.3;
        String wk = wn.toLowerCase().replace(" ","_").replace("&","and");
        base += att.getSkills().getOrDefault(wk,0)*0.8 + att.getLuck()*0.15;
        base *= (1.0-WeaponsUtil.strengthPenalty(wp.getWeight(), att.getStrength(), two));
        if (rm.isHeavyWeaponPenalty()) { boolean hvy = wp.getWeight()>=4.0||(wp.isTwoHand()&&two); if (hvy && !(rm.isSpearException()&&"Polearm/Spear".equals(wp.getCategory()))) base *= 0.8; }
        base *= stylePen;
        if (isCleaveWeapon(wk)) { int cl = att.getSkills().getOrDefault("cleave",0); if (cl>0) { base += cl*2.0; if (cl==9) base*=1.25; int dd = def.getSkills().getOrDefault("dodge",0); if (dd>5) base *= Math.max(0.5, 1.0-(dd-5)*0.10); } }
        if (isBashWeapon(wk)) { int bl = att.getSkills().getOrDefault("bash",0); if (bl>0) { base += bl*2.0; int dd = def.getSkills().getOrDefault("dodge",0); if (dd>5) base *= Math.max(0.5, 1.0-(dd-5)*0.10); } }
        if (isSlashWeapon(wk)) { int sl = att.getSkills().getOrDefault("slash",0); if (sl>0) { base += sl*1.0; if (def.getArmor()!=null && !Arrays.asList("None","Leather","Studded Leather","Boiled Leather").contains(def.getArmor())) base *= 0.85; int dp = def.getSkills().getOrDefault("parry",0); if (dp>=5) base *= Math.max(0.8, 1.0-(dp-4)*0.05); } }
        int strL = att.getSkills().getOrDefault("strike",0); if (strL>0) base += strL*0.8;
        if (isOpenHandWeapon(wk)) { int oh = att.getSkills().getOrDefault("open_hand",0); if (oh>0) { base += oh*2.0; if (oh==9) base*=1.20; int br = att.getSkills().getOrDefault("brawl",0); if (br>0) { base += br*0.5; if (br==9) base*=1.10; } } }
        int ceil = Math.max(3, (int)base);
        double frac = Math.max(0.10, Math.min(1.00, margin/55.0));
        int raw = Math.max(1, (int)(ceil*frac));
        if (att.getFavoriteWeapon()!=null && wn.equals(att.getFavoriteWeapon())) raw += 1;
        String an = def.getArmor()!=null?def.getArmor():"None", hn = def.getHelm()!=null?def.getHelm():"None";
        int dv = ArmorUtil.getEffectiveDefenseForRace(an, hn, def.getRace().getName());
        if (wp.isArmorPiercing() && ArmorUtil.isApVulnerable(an)) dv = Math.max(0, dv/2);
        if (precByp > 0.0) dv = Math.max(0, (int)(dv*(1.0-precByp)));
        return new int[]{Math.max(1, raw-dv), wp.getCategory()!=null?wp.getCategory().hashCode():0};
    }

    private boolean isCleaveWeapon(String k) { return CLEAVE_WEAPONS.contains(k); }
    private boolean isBashWeapon(String k) { return BASH_WEAPONS.contains(k); }
    private boolean isSlashWeapon(String k) { return SLASH_WEAPONS.contains(k); }
    private boolean isOpenHandWeapon(String k) { return OPEN_HAND_WEAPONS.contains(k); }

    private void emit(String line) { lines.add(line); }

    private FightResult checkFatalInjury() {
        if (stateA.warrior.getInjuries().isFatal()) return makeResult(stateB.warrior, stateA.warrior, true, 0);
        if (stateB.warrior.getInjuries().isFatal()) return makeResult(stateA.warrior, stateB.warrior, true, 0);
        return null;
    }

    // Stub methods - full implementation continues in next part
    private FightResult resolveAction(CombatState as_, CombatState ds_, Strategy ax, Strategy dx, int minute) { return null; }
    private void applyPresenceHesitation() {}
    private void throwStones(int minute) {}
    private List<String> updateEndurance(CombatState st, Strategy s, int acts, CombatState foe) { return new ArrayList<>(); }
    private int calcApm(Warrior w, Strategy s, CombatState st) { return 1; }
    private List<String> applyTraining(Warrior w, Warrior opp) { return new ArrayList<>(); }
    private FightResult attemptConcede(CombatState dy, CombatState kl, int min) { return null; }
    private String handleOpportunityThrowLoss(Warrior w, CombatState st) { return null; }
    private FightResult counterstrike(CombatState as_, CombatState ds_, Strategy ax, Strategy dx, int min) { return null; }
    private FightResult handleZeroHp(CombatState dy, CombatState kl, int prev, int dmg, int min) { return null; }
    private boolean checkEntangle(Warrior w, CombatState st, Weapon wp, boolean thrown) { return false; }
    private boolean checkKnockdown(Warrior w, CombatState st, int dmg, String cat) { return false; }
    private boolean checkPermInjury(Warrior w, int dmg, String aim) { return false; }
    private boolean deathCheck(int prev, int dmg) { return false; }
    private boolean concedeCheck(Warrior w, CombatState st) { return false; }
    private String getFavoriteWeaponFlavor(Warrior w, String wn, CombatState st) { return null; }
    private boolean checkWeaponStyleCompatibility(String wn, String style) {
        Weapon wp; try { wp = Weapons.getWeapon(wn); } catch(Exception e) { return true; }
        if (style.equals(wp.getWeakStyles()!=null?wp.getWeakStyles().contains(style):false)) return false;
        if (wp.getWeight()<2.5 && Arrays.asList("Bash","Total Kill").contains(style)) return false;
        if (wp.getWeight()>=4.0 && Arrays.asList("Lunge","Calculated Attack").contains(style)) return false;
        if (wp.getWeight()<2.0 && "Total Kill".equals(style)) return false;
        if (wp.isTwoHand() && "Wall of Steel".equals(style)) return false;
        return true;
    }

    private FightResult resolveAction(CombatState as_, CombatState ds_, Strategy ax, Strategy dx, int minute) {
        Warrior att = as_.warrior, dfr = ds_.warrior;
        String wpn = att.getPrimaryWeapon(), aim = ax.getAimPoint();
        boolean compat = checkWeaponStyleCompatibility(wpn, ax.getStyle());
        String intent = compat ? NarrativeGenerator.styleIntentLine(att.getName(), dfr.getName(), ax.getStyle(), wpn, att.getGender())
                               : NarrativeGenerator.awkwardStyleIntentLine(att.getName(), dfr.getName(), ax.getStyle(), wpn, att.getGender());
        if (intent != null) emit(intent);
        Weapon weapon; String cat; try { weapon = Weapons.getWeapon(wpn); cat = weapon.getCategory(); } catch(Exception e) { weapon = Weapons.OPEN_HAND; cat = "Oddball"; }
        emit(NarrativeGenerator.attackLine(att.getName(), dfr.getName(), wpn, cat, ax.getStyle(), aim, att.getGender(), att.getRace().getName()));
        if (Math.random() < 0.55) {
            StyleProperties pdx = StyleUtil.getStyleProps(dx.getStyle());
            boolean usesParry = pdx.parryBonus >= pdx.dodgeBonus;
            emit(NarrativeGenerator.defenseIntentLine(dfr.getName(), dfr.getGender(), usesParry));
        }
        String favFlavor = getFavoriteWeaponFlavor(att, wpn, as_);
        if (favFlavor != null) emit(favFlavor);
        int atkR = attackRoll(att, ax, as_);
        atkR += StyleUtil.getStyleAdvantage(ax.getStyle(), dx.getStyle()) * 6;
        if (!compat) atkR = (int)(atkR - 25 * (1.0 - (compat?1.0:0.6)));
        boolean decoyFeint = false;
        if ("Decoy".equals(ax.getStyle())) {
            if (attemptFeint(att, dfr, dx.getStyle())) { decoyFeint = true; emit(NarrativeGenerator.decoyFeintLine(att.getName(), dfr.getName())); }
            else if ("Counterstrike".equals(dx.getStyle())) emit(NarrativeGenerator.decoyFeintReadLine(att.getName(), dfr.getName()));
        }
        boolean caPrecision = false;
        if ("Calculated Attack".equals(ax.getStyle())) caPrecision = attemptPrecisionStrike(att, dfr, weapon, dx.getStyle());
        StyleProperties pd = StyleUtil.getStyleProps(dx.getStyle());
        boolean useP = pd.parryBonus >= pd.dodgeBonus;
        int defR = defenseRoll(dfr, dx, ds_, att, aim, ax.getStyle(), useP);
        if (decoyFeint) defR = Math.max(1, defR - DECOY_FEINT_PENALTY);
        int margin = atkR - defR;
        if (margin <= 0) {
            if ("Calculated Attack".equals(ax.getStyle()) && !caPrecision && new Random().nextInt(100)+1 <= CA_PROBE_EMIT_CHANCE)
                emit(NarrativeGenerator.calculatedProbeLine(att.getName(), dfr.getName()));
            if (margin == 0) emit(NarrativeGenerator.missLine(att.getName(), wpn));
            else if (margin <= -30) {
                if (useP) {
                    boolean barely = -margin < 20;
                    emit(NarrativeGenerator.parryLine(dfr.getName(), barely, dx.getDefensePoint()!=null && !dx.getDefensePoint().equals("None") && dx.getDefensePoint().equals(aim)));
                    // Cleave/Bash parry penetration
                    String wk = wpn.toLowerCase().replace(" ","_").replace("&","and");
                    int cl = isCleaveWeapon(wk)?att.getSkills().getOrDefault("cleave",0):0;
                    int bl = isBashWeapon(wk)?att.getSkills().getOrDefault("bash",0):0;
                    int penLvl = Math.max(cl, bl);
                    if (penLvl > 0 && new Random().nextInt(100)+1 <= penLvl*5) {
                        try {
                            Weapon wp = Weapons.getWeapon(wpn);
                            int baseDmg = (int)(wp.getWeight()*2.0);
                            ds_.currentHp -= baseDmg;
                            boolean isBash = bl >= cl;
                            String af = aim!=null?aim:"body";
                            String al = isBash ? "The powerful strike bashes through the parry, crushing into "+dfr.getName().capitalize()+"'s "+af+"!"
                                               : "The powerful strike cleaves through the parry, splitting into "+dfr.getName().capitalize()+"'s "+af+"!";
                            emit(al); return null;
                        } catch(Exception e){}
                    }
                    // Riposte counter-attack
                    int ripLvl = dfr.getSkills().getOrDefault("riposte", 0);
                    if (ripLvl > 0 && !ds_.isOnGround) {
                        int ripCh = 40 + ripLvl*5;
                        if (cl >= 3) ripCh = Math.max(5, ripCh - (cl-2)*15);
                        if (new Random().nextInt(100)+1 <= ripCh) {
                            emit(NarrativeGenerator.counterstrikeLine(dfr.getName(), att.getName()));
                            return counterstrike(ds_, as_, dx, ax, minute);
                        }
                    }
                    if ("Counterstrike".equals(dx.getStyle()) && !ds_.isOnGround && new Random().nextInt(100)+1 <= 30+dfr.getSkills().getOrDefault("parry",0)*5) {
                        emit(NarrativeGenerator.counterstrikeLine(dfr.getName(), att.getName()));
                        return counterstrike(ds_, as_, dx, ax, minute);
                    }
                } else emit(NarrativeGenerator.dodgeLine(dfr.getName()));
            } else emit(useP ? NarrativeGenerator.parryLine(dfr.getName(), true, dx.getDefensePoint()!=null && !dx.getDefensePoint().equals("None") && dx.getDefensePoint().equals(aim))
                             : NarrativeGenerator.dodgeLine(dfr.getName()));
            return null;
        }
        if (margin < 10) { emit(att.getName().toUpperCase()+"'s blow barely grazes "+dfr.getName().toUpperCase()+"!"); ds_.currentHp -= 1; return null; }
        String prec = margin >= 50 ? "precise" : (margin < 20 ? "barely" : "normal");
        String wkSig = wpn.toLowerCase().replace(" ","_").replace("&","and");
        int wpnSkillLvl = att.getSkills().getOrDefault(wkSig, 0);
        String sig = null;
        if (wpnSkillLvl >= 5 && Math.random() < 0.25 && !caPrecision) sig = NarrativeGenerator.signatureLine(att.getName(), wpn);
        if (caPrecision) emit(NarrativeGenerator.calculatedPrecisionLine(att.getName(), dfr.getName(), wpn, aim));
        else if (sig != null) emit(sig);
        else for (String ln : NarrativeGenerator.hitLine(att.getName(), dfr.getName(), wpn, cat, aim, prec, att.getRace().getName())) emit(ln);
        int[] dmgRes = calcDamageHybrid(att, ax, wpn, dfr, margin, caPrecision?CA_PRECISION_ARMOR_BYPASS:0.0, compat?1.0:0.6);
        int dmg = dmgRes[0];
        if (sig != null) dmg = Math.max(dmg, (int)(dfr.getMaxHp()*0.12));
        if (caPrecision) dmg += CA_PRECISION_DAMAGE_BONUS;
        emit(NarrativeGenerator.damageLine(dmg, dfr.getMaxHp(), cat));
        int prevHp = ds_.currentHp;
        ds_.currentHp -= dmg;
        // Bleeding from Slash
        String wkStd = wpn.toLowerCase().replace(" ","_").replace("&","and");
        if (isSlashWeapon(wkStd)) {
            int slLvl = att.getSkills().getOrDefault("slash", 0);
            if (slLvl > 0 && new Random().nextInt(100)+1 <= slLvl*5) ds_.bleedingWounds++;
        }
        if (ds_.bleedingWounds > 0 && new Random().nextInt(100)+1 <= 40) {
            int bleedDmg = Math.max(1, (int)(ds_.bleedingWounds*0.5));
            ds_.currentHp -= bleedDmg;
        }
        double hpPct = ds_.currentHp / (double)Math.max(1, dfr.getMaxHp());
        if (ds_.currentHp > 0) { String stLn = NarrativeGenerator.lowHpLine(dfr.getName(), dfr.getGender(), hpPct); if (stLn!=null) emit(stLn); }
        int nkThresh = (int)(dfr.getMaxHp()*0.20);
        if (prevHp > nkThresh && nkThresh >= ds_.currentHp) as_.nearKillsDealt++;
        if ("Opportunity Throw".equals(ax.getStyle())) {
            String wMsg = handleOpportunityThrowLoss(att, as_);
            if (wMsg != null) emit(wMsg);
        }
        boolean wasThrown = "Opportunity Throw".equals(ax.getStyle());
        try {
            boolean[] entRes = checkEntangle(dfr, ds_, weapon, wasThrown);
            if (entRes[0]) {
                emit(entRes[1] != null ? entRes[1] : "");
                ds_.isOnGround = true;
                as_.knockdownsDealt++;
                int fallDmg = new Random().nextInt(3)+1;
                ds_.currentHp -= fallDmg;
                emit(dfr.getName().toUpperCase()+" hits the ground hard!");
            }
        } catch(Exception e){}
        if (checkKnockdown(dfr, ds_, dmg, cat)) {
            emit(NarrativeGenerator.knockdownLine(dfr.getName(), dfr.getGender()));
            ds_.isOnGround = true;
            as_.knockdownsDealt++;
        }
        Object[] perm = checkPermInjury(dfr, dmg, aim);
        if (perm != null) {
            String loc = (String)perm[0];
            int lvls = (Integer)perm[1];
            boolean fatal = dfr.getInjuries().add(loc, lvls);
            for (String ln : NarrativeGenerator.permInjuryLines(dfr.getName(), loc, lvls, dfr.getGender())) emit(ln);
            if (fatal) {
                emit(NarrativeGenerator.deathLine(dfr.getName(), dfr.getGender()));
                emit(""); emit(NarrativeGenerator.victoryLine(att.getName(), dfr.getName()));
                return makeResult(att, dfr, true, minute);
            }
        }
        if (ds_.currentHp <= 0) return handleZeroHp(ds_, as_, prevHp, dmg, minute);
        return null;
    }

    private void applyPresenceHesitation() {
        for (CombatState[] pair : new CombatState[][]{{stateA, stateB}, {stateB, stateA}}) {
            CombatState attSt = pair[0], defSt = pair[1];
            int ch = attSt.warrior.getPresenceHesitateChance();
            if (ch > 0 && new Random().nextInt(100)+1 <= ch) {
                defSt.endurance = Math.max(0.0, defSt.endurance - 15);
                emit(attSt.warrior.getName().toUpperCase()+"'s commanding presence makes "+defSt.warrior.getName().toUpperCase()+" hesitate!");
            }
        }
    }

    private void throwStones(int minute) {
        if (isMonsterFight) return;
        double pctA = stateA.currentHp / (double)Math.max(1, warriorA.getMaxHp());
        double pctB = stateB.currentHp / (double)Math.max(1, warriorB.getMaxHp());
        Set<String> passiveStyles = new HashSet<>(Arrays.asList("Parry", "Defend"));
        double scoreA = prevAttacksA - (passiveStyles.contains(stateA.activeStrategy!=null?stateA.activeStrategy.getStyle():"Strike")?1.5:0) - Math.max(0.0, (pctA-0.60))*3;
        double scoreB = prevAttacksB - (passiveStyles.contains(stateB.activeStrategy!=null?stateB.activeStrategy.getStyle():"Strike")?1.5:0) - Math.max(0.0, (pctB-0.60))*3;
        CombatState target = scoreA < scoreB ? stateA : (scoreB < scoreA ? stateB : (pctA >= pctB ? stateA : stateB));
        int dmg = (minute-6)*2;
        String n = target.warrior.getName().toUpperCase();
        String[] ev = Math.random() < 0.20 ? REF_WEAPON_EVENTS[new Random().nextInt(REF_WEAPON_EVENTS.length)] : REF_STONE_EVENTS[new Random().nextInt(REF_STONE_EVENTS.length)];
        target.currentHp = Math.max(1, target.currentHp - dmg);
        emit(""); emit(ev[0].replace("{n}", n)); emit(ev[1].replace("{n}", n));
        int tAtt = target==stateA?prevAttacksA:prevAttacksB;
        if (tAtt <= 1 && Math.random() < 0.30) {
            String[] ev2 = REF_FOLLOWUP_EVENTS[new Random().nextInt(REF_FOLLOWUP_EVENTS.length)];
            target.currentHp = Math.max(1, target.currentHp - dmg);
            emit(ev2[0].replace("{n}", n)); emit(ev2[1].replace("{n}", n));
        }
    }

    private List<String> updateEndurance(CombatState st, Strategy s, int acts, CombatState foe) {
        List<String> res = new ArrayList<>();
        StyleProperties p = StyleUtil.getStyleProps(s.getStyle());
        double burn = p.enduranceBurn + (s.getActivity()-5)*0.3;
        int acroLvl = st.warrior.getSkills().getOrDefault("acrobatics", 0);
        if (acroLvl > 0 && Arrays.asList("Engage & Withdraw", "Lunge").contains(s.getStyle()))
            burn += Math.max(1, 10-acroLvl)*0.01;
        st.endurance = Math.max(0.0, Math.min(100.0, st.endurance - burn*acts));
        if (p.anxiouslyAwaits && s.getActivity() < 6) {
            foe.endurance = Math.max(0.0, foe.endurance - (6-s.getActivity())*0.5);
            if (Math.random() < 0.20) { String ln = NarrativeGenerator.anxiousLine(st.warrior.getName(), foe.warrior.getName()); if (ln!=null) res.add(ln); }
        }
        if (p.intimidate && s.getActivity() >= 5) {
            double drain = (s.getActivity()-4)*1.0;
            foe.endurance = Math.max(0.0, foe.endurance - drain);
            String ln = NarrativeGenerator.intimidateLine(st.warrior.getName(), foe.warrior.getName());
            if (ln!=null) res.add(ln);
        }
        if (st.endurance <= 20 && Math.random() < 0.40) res.add(NarrativeGenerator.fatigueLine(st.warrior.getName(), st.warrior.getGender(), true));
        else if (st.endurance <= 40 && Math.random() < 0.20) res.add(NarrativeGenerator.fatigueLine(st.warrior.getName(), st.warrior.getGender(), false));
        return res;
    }

    private int calcApm(Warrior w, Strategy s, CombatState st) {
        int dex = ArmorUtil.getEffectiveDexForRace(w.getDexterity(), w.getArmor()!=null?w.getArmor():"None", w.getHelm()!=null?w.getHelm():"None", w.getRace().getName());
        String wk = w.getPrimaryWeapon().toLowerCase().replace(" ","_").replace("&","and");
        double base = 3.0 + Math.max(0.0, dex-10)*0.20 + Math.max(0.0, w.getIntelligence()-10)*0.10 + s.getActivity()*0.25 + w.getSkills().getOrDefault(wk,0)*0.20;
        RacialModifiers rm = w.getRace().getModifiers();
        base += rm.getAttackRateBonus()*0.25 - rm.getAttackRatePenalty()*0.25;
        base += StyleUtil.getStyleProps(s.getStyle()).apmModifier;
        double armorPen = ArmorUtil.getArmorAttackRatePenaltyForRace(w.getArmor()!=null?w.getArmor():"None", w.getRace().getName());
        base -= armorPen*0.25;
        if (rm.isHeavyWeaponPenalty()) {
            try {
                Weapon wp = Weapons.getWeapon(w.getPrimaryWeapon());
                boolean two = "Open Hand".equals(w.getSecondaryWeapon()) && wp.isTwoHand();
                boolean hvy = wp.getWeight()>=4.0||(wp.isTwoHand()&&two);
                if (hvy && !(rm.isSpearException()&&"Polearm/Spear".equals(wp.getCategory()))) base -= 3*0.25;
            } catch(Exception e){}
        }
        if (st.endurance < 40) base -= (40-st.endurance)/40.0*1.5;
        if (st.isOnGround) base *= 0.5;
        return Math.max(1, Math.min(10, (int)Math.round(base)));
    }

    private List<String> applyTraining(Warrior w, Warrior opp) {
        w.resetTrainingSession();
        List<String> res = new ArrayList<>();
        for (String sk : w.getTrains().subList(0, Math.min(3, w.getTrains().size()))) {
            String msg = w.trainSkill(sk);
            if (msg != null && !msg.isEmpty()) res.add(msg);
        }
        if (opp != null && w.getIntelligence() >= 15) {
            int bonusCh = Math.max(3, (w.getIntelligence()-14)*4);
            if (new Random().nextInt(100)+1 <= bonusCh) {
                List<String> cands = new ArrayList<>();
                for (Strategy strat : opp.getStrategies()) {
                    if (Arrays.asList("Parry","Counterstrike").contains(strat.getStyle())) cands.add("parry");
                    if (Arrays.asList("Strike","Bash","Total Kill","Counterstrike").contains(strat.getStyle())) cands.add("initiative");
                    if ("Dodge".equals(strat.getStyle())) cands.add("dodge");
                }
                String oppWpn = (opp.getPrimaryWeapon()!=null?opp.getPrimaryWeapon():"Short Sword").toLowerCase().replace(" ","_").replace("&","and");
                cands.addAll(Arrays.asList(oppWpn, "dodge", "parry", "initiative", "feint"));
                Collections.shuffle(cands);
                for (String sk : cands) {
                    String skKey = sk.toLowerCase().replace(" ","_");
                    if (w.getSkills().containsKey(skKey)) {
                        String br = w.trainSkill(skKey);
                        if (br != null && !br.isEmpty()) res.add("[OBSERVED] "+br);
                        break;
                    }
                }
            }
        }
        w.recalculateDerived();
        return res;
    }

    private FightResult attemptConcede(CombatState dy, CombatState kl, int min) {
        Warrior dw = dy.warrior, kw = kl.warrior;
        emit(NarrativeGenerator.appealLine(dw.getName()));
        dy.concedeAttempts++;
        boolean granted = concedeCheck(dw, dy);
        emit(NarrativeGenerator.mercyResultLine(dw.getName(), granted));
        if (granted) { emit(""); emit(NarrativeGenerator.victoryLine(kw.getName(), dw.getName())); return makeResult(kw, dw, false, min); }
        return null;
    }

    private String handleOpportunityThrowLoss(Warrior w, CombatState st) {
        String curPri = w.getPrimaryWeapon();
        try {
            Weapon wp = Weapons.getWeapon(curPri);
            if ("empty_hand".equals(wp.getSkillKey())) return null;
        } catch(Exception e) { return null; }
        if (w.getBackupWeapon() != null && w.getBackupWeapon().equals(curPri)) {
            w.setPrimaryWeapon(w.getBackupWeapon());
            w.setBackupWeapon(null);
            return w.getName().toUpperCase()+" pulls "+w.getName().toLowerCase()+"'s backup "+curPri.toLowerCase()+"!";
        }
        if (w.getSecondaryWeapon() != null && !"Open Hand".equals(w.getSecondaryWeapon())) {
            w.setPrimaryWeapon(w.getSecondaryWeapon());
            return w.getName().toUpperCase()+" switches to "+w.getName().toLowerCase()+"'s "+w.getSecondaryWeapon().toLowerCase()+"!";
        }
        w.setPrimaryWeapon("Open Hand");
        return w.getName().toUpperCase()+" has no more throwables and resorts to martial combat!";
    }

    private FightResult counterstrike(CombatState as_, CombatState ds_, Strategy ax, Strategy dx, int min) {
        Warrior att = as_.warrior, dfr = ds_.warrior;
        String wpn = att.getPrimaryWeapon();
        boolean compat = checkWeaponStyleCompatibility(wpn, ax.getStyle());
        String cat; try { cat = Weapons.getWeapon(wpn).getCategory(); } catch(Exception e) { cat = "Oddball"; }
        for (String ln : NarrativeGenerator.hitLine(att.getName(), dfr.getName(), wpn, cat, ax.getAimPoint(), "precise", att.getRace().getName())) emit(ln);
        int[] dmgRes = calcDamageHybrid(att, ax, wpn, dfr, 40, 0.0, compat?1.0:0.6);
        int dmg = dmgRes[0];
        emit(NarrativeGenerator.damageLine(dmg, dfr.getMaxHp(), cat));
        int prev = ds_.currentHp;
        ds_.currentHp -= dmg;
        int nkThresh = (int)(dfr.getMaxHp()*0.20);
        if (prev > nkThresh && nkThresh >= ds_.currentHp) as_.nearKillsDealt++;
        if (ds_.currentHp <= 0) return handleZeroHp(ds_, as_, prev, dmg, min);
        return null;
    }

    private FightResult handleZeroHp(CombatState dy, CombatState kl, int prev, int dmg, int min) {
        Warrior dw = dy.warrior, kw = kl.warrior;
        if (isMonsterFight) {
            dw.setDead(true);
            emit(dw.getName().toUpperCase()+" collapses, the monster shows no mercy!");
            emit(NarrativeGenerator.deathLine(dw.getName(), dw.getGender()));
            emit(""); emit(NarrativeGenerator.victoryLine(kw.getName(), dw.getName()));
            return makeResult(kw, dw, true, min);
        }
        if (deathCheck(prev, dmg)) {
            dw.setDead(true);
            emit(NarrativeGenerator.deathLine(dw.getName(), dw.getGender()));
            emit(""); emit(NarrativeGenerator.victoryLine(kw.getName(), dw.getName()));
            return makeResult(kw, dw, true, min);
        }
        return null;
    }

    private boolean[] checkEntangle(Warrior w, CombatState st, Weapon wp, boolean thrown) {
        if (st.isOnGround) return new boolean[]{false, null};
        if ("bola".equals(wp.getSkillKey())) {
            if (thrown) {
                if (new Random().nextInt(100)+1 <= 70) return new boolean[]{true, "The bola wraps around "+w.getName().toUpperCase()+"'s legs and trips them to the ground!"};
            } else {
                if (new Random().nextInt(100)+1 <= 35) return new boolean[]{true, "The swinging bola tangles "+w.getName().toUpperCase()+"'s legs!"};
            }
        } else if ("heavy_whip".equals(wp.getSkillKey())) {
            if (new Random().nextInt(100)+1 <= 50) return new boolean[]{true, "The barbed whip wraps around "+w.getName().toUpperCase()+"'s legs, dragging them to the ground!"};
        }
        return new boolean[]{false, null};
    }

    private boolean checkKnockdown(Warrior w, CombatState st, int dmg, String cat) {
        if (st.isOnGround) return false;
        int ch = (int)((dmg / (double)Math.max(1, w.getMaxHp())) * 80);
        if (Arrays.asList("Hammer/Mace","Flail").contains(cat)) ch += 10;
        if ("Polearm/Spear".equals(cat)) ch += 5;
        ch -= Math.max(0, (w.getSize()-12))*2;
        return new Random().nextInt(100)+1 <= Math.max(1, ch);
    }

    private Object[] checkPermInjury(Warrior w, int dmg, String aim) {
        if (dmg < w.getMaxHp()*0.15) return null;
        int ch = Math.max(5, Math.min(80, (int)((dmg/(double)w.getMaxHp())*100)-5));
        if (w.getRace().getModifiers().isFewerPerms()) ch = (int)(ch*0.85);
        if (new Random().nextInt(100)+1 > ch) return null;
        String loc;
        if (aim != null && !"None".equals(aim)) {
            Map<String,String> lm = new HashMap<>();
            lm.put("Head","head"); lm.put("Chest","chest"); lm.put("Abdomen","abdomen");
            lm.put("Primary Arm","primary_arm"); lm.put("Secondary Arm","secondary_arm");
            lm.put("Primary Leg","primary_leg"); lm.put("Secondary Leg","secondary_leg");
            loc = lm.getOrDefault(aim, new String[]{"head","chest","chest","abdomen","primary_arm","secondary_arm","primary_leg","secondary_leg"}[new Random().nextInt(8)]);
        } else {
            String[] lp = {"head","chest","chest","abdomen","primary_arm","secondary_arm","primary_leg","secondary_leg"};
            loc = lp[new Random().nextInt(lp.length)];
        }
        double pct = dmg / (double)w.getMaxHp();
        int lvls = pct > 0.50 ? 3 : (pct > 0.35 ? 2 : 1);
        return new Object[]{loc, lvls};
    }

    private boolean deathCheck(int prevHp, int dmg) {
        int newHp = prevHp - dmg;
        if (newHp > 0) return false;
        int overshoot = Math.abs(Math.min(newHp, 0));
        return Math.random()*100 < Math.min(50.0, 0.5 + (float)overshoot);
    }

    private boolean concedeCheck(Warrior w, CombatState st) {
        if (isMonsterFight) return false;
        int roll = d100();
        int pre = w.getPresence();
        int preB = Math.max(-6, Math.min(10, pre-10));
        int tot = roll + preB + w.getLuck()/2;
        int thresh = Math.max(40, 68-(pre/3));
        return tot >= thresh;
    }

    private String getFavoriteWeaponFlavor(Warrior w, String wn, CombatState st) {
        if (!showFavoriteWeapon || w.getFavoriteWeapon()==null || !wn.equals(w.getFavoriteWeapon()) || st.usedFavoriteWeaponThisFight) return null;
        st.usedFavoriteWeaponThisFight = true;
        Map<String,List<String>> fwLines = Weapons.getFavoriteWeaponLines();
        List<String> lines = fwLines.get(wn);
        if (lines == null || lines.isEmpty()) return null;
        return lines.get(new Random().nextInt(lines.size())).replace("{name}", w.getName().toUpperCase());
    }

    public static FightResult runFight(Warrior a, Warrior b, String ta, String tb, String ma, String mb, boolean mf, String cn) {
        CombatEngine eng = new CombatEngine(a, b, ta, tb, ma, mb, 1, 1, mf, cn);
        FightResult r = eng.resolveFight();
        if (r.winner!=null && r.loser!=null) {
            Set<String> npc = new HashSet<>(Arrays.asList("Monster","Peasant"));
            if (!npc.contains(r.winner.getRace().getName())) r.winner.recordResult("win", r.loserDied);
            if (!npc.contains(r.loser.getRace().getName())) r.loser.recordResult("loss");
        }
        return r;
    }
}
