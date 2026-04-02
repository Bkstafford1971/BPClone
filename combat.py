# =============================================================================
# combat.py — BLOODSPIRE Combat Engine v2
# =============================================================================
# CORE MECHANICS:
#   All rolls: d100 (1-100).
#   Every warrior has a permanent luck factor (1-30) added to every roll.
#
# INITIATIVE (per-action within each minute):
#   Before each action slot, both warriors roll initiative.
#   d100 + DEX_bonus + initiative_skill + luck + style_mod + activity_mod.
#   Higher roll = attacker for that slot.
#
# ATTACK vs DEFENSE:
#   Attacker: d100 + DEX + weapon_skill*5 + luck + style_mod
#   Defender: d100 + (STR/DEX) + parry/dodge_skill*4 + weapon_skill*3 + luck
#   margin = attack_roll - defense_roll
#     margin <= 0:     miss / parry / dodge
#     margin  1-9:     graze (1 HP, no other effects)
#     margin >= 10:    hit (damage = ceiling * (margin/80))
#
# DAMAGE (HYBRID):
#   Ceiling  = f(STR, weapon weight, race, skills, style, luck)
#   Fraction = min(1.0, margin / 80.0)
#   Net      = max(1, int(ceiling * fraction) - armor)
#
# CONCEDE SYSTEM:
#   Triggered at <=25% HP. d100 + PRE_bonus + luck//2 vs threshold.
#   Presence determines how often the Pitmaster grants mercy.
#   Monster fights: no concede, always to the death.
#
# DEATH CHECK:
#   overshoot = max(0, -new_hp)
#   death_chance = 0.5% + overshoot% (capped 50%)
#
# NO DRAWS: 30-minute limit -> judge awards decision to higher HP% warrior.
# =============================================================================

import random
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

from warrior  import Warrior, Strategy, ATTRIBUTES
from strategy import (
    FighterState, evaluate_triggers, get_style_advantage,
    get_style_props,
)
from weapons  import get_weapon, strength_penalty, OPEN_HAND
from armor    import (
    effective_dex, total_defense_value, is_ap_vulnerable,
)
import narrative as N


# ---------------------------------------------------------------------------
# FAVORITE WEAPON NARRATIVE LINES
# ---------------------------------------------------------------------------

FAVORITE_WEAPON_LINES = {
    # Swords & Knives
    "Stiletto": [
        "{name}'s stiletto darts forward like a striking serpent finding the tiniest gap in the armor. This is clearly {name}'s favored weapon.",
        "{name}'s stiletto slides toward its target with surgical precision hungry for a vital point. The crowd sees this is {name}'s weapon of choice.",
        "{name}'s thin stiletto flashes with deadly intent a needle seeking the perfect vein. None doubt this is {name}'s favorite blade.",
        "{name}'s stiletto moves with whispering speed almost too fast for the eye to follow. It is obvious the stiletto is {name}'s true love in the pit.",
        "A single perfect thrust. {name}'s stiletto feels alive in {name}'s hand eager to bite. This weapon was made for {name}.",
    ],
    "Knife": [
        "{name}'s knife flicks out with practiced ease a tool turned deadly in an instant. The arena knows this is {name}'s favored weapon.",
        "{name}'s knife delivers a quick vicious slash. It knows exactly where to cut deepest. This is clearly {name}'s weapon of choice.",
        "{name}'s small knife dances dangerously close looking for soft flesh. None can mistake how much {name} favors this blade.",
        "{name}'s knife strikes with the speed of a cornered rat sudden and mean. The crowd cheers {name}'s favorite weapon.",
        "{name}'s brutal little knife finds its way into the fight with ugly efficiency. This is the weapon {name} trusts above all others.",
    ],
    "Dagger": [
        "{name}'s dagger lunges forward hungry for the spaces between armor plates. This is unmistakably {name}'s favored weapon.",
        "{name}'s dagger delivers a precise thrusting strike. It feels perfectly balanced for murder in {name}'s grip. {name}'s favorite by far.",
        "{name}'s dagger flashes in a tight arc seeking the throat or the gap under the arm. The pit knows this is {name}'s chosen blade.",
        "With a fighter's instinct {name}'s dagger drives home short and vicious. This weapon is clearly {name}'s true favorite.",
        "{name}'s dagger moves like an extension of {name}'s hand cold sharp and personal. The crowd senses {name}'s deep bond with this dagger.",
    ],
    "Short Sword": [
        "{name}'s short sword cuts with economical grace never wasting a motion. This is clearly {name}'s favored weapon.",
        "{name}'s short sword delivers a clean controlled thrust. It feels right at home in {name}'s skilled hands. {name}'s weapon of choice.",
        "{name}'s short sword snaps forward quick and businesslike. The arena recognizes this as {name}'s favorite blade.",
        "Balanced and deadly {name}'s short sword finds its mark with professional efficiency. None doubt {name}'s bond with this sword.",
        "{name}'s short sword moves with the confidence of a weapon that has seen many fights at {name}'s side. This is {name}'s true favorite.",
    ],
    "Epee": [
        "{name}'s epee extends like a silver needle seeking a single perfect point. This is clearly {name}'s favored weapon.",
        "{name}'s epee delivers a lightning quick thrust. It dances on the edge of visibility. {name}'s weapon of choice.",
        "{name}'s slender epee probes for weakness with aristocratic precision. The pit knows this is {name}'s favorite.",
        "{name}'s epee flicks forward elegant and lethal in the same motion. This blade was made for {name}.",
        "A master's weapon. {name}'s epee moves with deceptive speed and deadly focus. {name}'s true favorite in the arena.",
    ],
    "Scimitar": [
        "{name}'s scimitar sweeps in a graceful deadly arc hungry for flesh. This is clearly {name}'s favored weapon.",
        "{name}'s curved scimitar sings as it cuts through the air promising pain. The crowd sees {name}'s favorite blade at work.",
        "A flashing draw cut from {name}'s scimitar beautiful and brutal. This is the weapon {name} loves most.",
        "{name}'s scimitar moves like liquid steel flowing into the perfect angle. {name}'s bond with this blade is obvious.",
        "With a desert warrior's flair {name}'s scimitar carves its path through the fight. {name}'s true favorite.",
    ],
    "Longsword": [
        "{name}'s longsword extends with measured power seeking to dominate the space. This is clearly {name}'s favored weapon.",
        "{name}'s longsword delivers a strong controlled cut. It demands respect and space. {name}'s weapon of choice.",
        "{name}'s longsword moves with the weight of authority behind every strike. The arena knows this is {name}'s favorite.",
        "Balanced and deadly {name}'s longsword finds its rhythm in skilled hands. This blade belongs to {name}.",
        "{name}'s longsword cuts with purpose a noble weapon in a brutal arena. {name}'s true favorite.",
    ],
    "Broadsword": [
        "{name}'s broadsword swings with solid reliable force. This is clearly {name}'s favored weapon.",
        "{name}'s broadsword delivers a heavy practical cut no frills just results. {name}'s weapon of choice.",
        "{name}'s broadsword carries its message with straightforward power. The pit recognizes {name}'s favorite blade.",
        "Reliable and strong {name}'s broadsword does exactly what is asked of it. This is the weapon {name} trusts most.",
        "{name}'s broadsword hacks forward with the confidence of a well made tool. {name}'s true favorite in battle.",
    ],
    "Bastard Sword": [
        "{name}'s bastard sword moves with surprising speed for its size a hybrid of grace and power. This is clearly {name}'s favored weapon.",
        "Gripped in one or two hands {name}'s bastard sword strikes with flexible lethality. {name}'s weapon of choice.",
        "{name}'s bastard sword finds the perfect balance between reach and control. The crowd knows this is {name}'s favorite.",
        "A versatile weapon {name}'s bastard sword adapts to {name}'s needs in the moment. This blade was made for {name}.",
        "{name}'s bastard sword cuts with the weight of both precision and brute force. {name}'s true favorite.",
    ],
    "Great Sword": [
        "{name}'s great sword sweeps through the air like a falling tree terrifying in its arc. This is clearly {name}'s favored weapon.",
        "{name}'s great sword delivers a massive two handed cut. It demands space and respect. {name}'s weapon of choice.",
        "{name}'s great sword moves with unstoppable momentum once it begins its path. The pit knows this is {name}'s favorite.",
        "A weapon built for devastation {name}'s great sword cleaves everything in its path. This is the blade {name} loves most.",
        "{name}'s great sword roars as it descends promising to end the fight in a single blow. {name}'s true favorite.",
    ],
    "Hatchet": [
        "{name}'s hatchet flashes forward in a quick brutal chop. This is clearly {name}'s favored weapon.",
        "{name}'s hatchet bites deep when it lands. A small but vicious axe. {name}'s weapon of choice.",
        "{name}'s hatchet moves with surprising speed a woodsman's tool turned deadly. The arena sees {name}'s favorite.",
        "Short sharp and mean {name}'s hatchet finds its target with ugly efficiency. This is the weapon {name} trusts most.",
        "{name}'s hatchet hacks forward looking to split bone and armor alike. {name}'s true favorite in the pit.",
    ],
    "Fransisca": [
        "{name}'s fransisca spins through the air with deadly accuracy. This is clearly {name}'s favored weapon.",
        "{name}'s fransisca seeks flesh and bone with purpose. A throwing axe that belongs to {name}. {name}'s weapon of choice.",
        "{name}'s fransisca whistles as it flies a dwarf forged promise of pain. The crowd knows this is {name}'s favorite.",
        "With a warrior's practiced toss {name}'s fransisca seeks its mark. This axe was made for {name}.",
        "{name}'s fransisca cuts a deadly path spinning end over end toward its target. {name}'s true favorite.",
    ],
    "Battle Axe": [
        "{name}'s battle axe descends with crushing force hungry for armor and bone. This is clearly {name}'s favored weapon.",
        "{name}'s battle axe delivers a heavy two handed chop. It means business. {name}'s weapon of choice.",
        "{name}'s battle axe swings in a wide devastating arc. The pit recognizes this as {name}'s favorite.",
        "With dwarven strength behind it {name}'s battle axe splits the air. This is the axe {name} loves most.",
        "{name}'s battle axe hacks forward designed to cleave through shields and helms. {name}'s true favorite.",
    ],
    "Great Axe": [
        "{name}'s great axe comes down like the wrath of the mountains themselves. This is clearly {name}'s favored weapon.",
        "{name}'s great axe cleaves the air with terrifying power and reach. The pit knows this is the weapon {name} was born to wield.",
        "When {name}'s great axe swings lesser weapons seem like toys. {name}'s bond with this axe is obvious to all.",
        "{name}'s great axe moves with unstoppable momentum promising utter ruin. This is clearly {name}'s favorite.",
        "{name}'s great axe brings devastation with every strike. The crowd cheers {name}'s weapon of choice.",
    ],
    "Small Pick": [
        "{name}'s small pick darts forward seeking the weak points in armor. This is clearly {name}'s favored weapon.",
        "{name}'s small pick delivers a precise piercing strike. It is looking for a gap. {name}'s weapon of choice.",
        "{name}'s pick punches forward a needle of steel aimed at vulnerable joints. The arena sees {name}'s favorite.",
        "With surgical intent {name}'s small pick probes for a killing blow. This is the weapon {name} trusts most.",
        "{name}'s small pick strikes like an ice pick through snow sharp and sudden. {name}'s true favorite.",
    ],
    "Military Pick": [
        "{name}'s military pick drives forward with brutal armor piercing intent. This is clearly {name}'s favored weapon.",
        "{name}'s military pick seeks to punch through steel. A weapon made for war. {name}'s weapon of choice.",
        "{name}'s pick crashes forward designed to crack helms and split breastplates. The pit knows this is {name}'s favorite.",
        "With practiced efficiency {name}'s military pick finds its mark. This is the weapon {name} loves most.",
        "{name}'s military pick strikes with the cold certainty of a battlefield veteran. {name}'s true favorite.",
    ],
    "Pick Axe": [
        "{name}'s pick axe comes down with mining fury meant to break stone and bone alike. This is clearly {name}'s favored weapon.",
        "{name}'s pick axe brings the mountain's anger to the pit. A heavy two handed pick. {name}'s weapon of choice.",
        "{name}'s pick axe swings with devastating force looking to split anything in its path. The crowd sees {name}'s favorite.",
        "A brutal tool turned weapon {name}'s pick axe demands respect through violence. This is {name}'s true favorite.",
        "{name}'s pick axe crashes down a miner's rage given lethal purpose. {name}'s bond with this weapon is obvious.",
    ],
    "Hammer": [
        "{name}'s hammer swings with straightforward bone crushing intent. This is clearly {name}'s favored weapon.",
        "{name}'s hammer does what hammers do best. A solid reliable strike. {name}'s weapon of choice.",
        "{name}'s hammer falls like judgment seeking to break what stands before it. The arena knows this is {name}'s favorite.",
        "With practiced swings {name}'s hammer seeks to pulp armor and flesh. This is the weapon {name} trusts most.",
        "{name}'s hammer delivers its message with blunt uncompromising force. {name}'s true favorite in the pit.",
    ],
    "Mace": [
        "{name}'s mace swings in a heavy punishing arc. This is clearly {name}'s favored weapon.",
        "Flanged and brutal {name}'s mace seeks to crush anything it touches. {name}'s weapon of choice.",
        "{name}'s mace falls with the weight of authority behind every blow. The pit recognizes {name}'s favorite.",
        "A weapon that speaks in broken bones. {name}'s mace does its work well. This is {name}'s true favorite.",
        "{name}'s mace crashes forward designed to end arguments permanently. {name}'s bond with this weapon is clear.",
    ],
    "Morningstar": [
        "{name}'s morningstar whips through the air spikes hungry for blood. This is clearly {name}'s favored weapon.",
        "{name}'s morningstar swings with deadly grace its spikes singing for flesh. The arena recognizes {name}'s favorite weapon instantly.",
        "{name}'s morningstar promises agony with every rotation. None doubt this is the weapon {name} loves most in the pit.",
        "With expert control {name}'s morningstar seeks the perfect striking angle. This is {name}'s true weapon of choice.",
        "{name}'s morningstar descends like a falling star cruel and bright. The crowd roars for {name}'s favored weapon.",
    ],
    "War Hammer": [
        "{name}'s war hammer comes down with the force of a thunderclap. This is clearly {name}'s favored weapon.",
        "{name}'s war hammer means to end the fight. A weapon built for breaking armor. {name}'s weapon of choice.",
        "{name}'s war hammer swings with devastating concentrated power. The pit knows this is {name}'s favorite.",
        "With half orc strength behind it {name}'s war hammer becomes a siege engine. This is the weapon {name} loves most.",
        "{name}'s war hammer falls like divine judgment on the unworthy. {name}'s true favorite.",
    ],
    "Maul": [
        "{name}'s maul swings like a falling tree unstoppable and crushing. This is clearly {name}'s favored weapon.",
        "{name}'s maul cares nothing for finesse. A weapon of pure brute force. {name}'s weapon of choice.",
        "{name}'s maul descends with terrifying momentum seeking total destruction. The arena sees {name}'s favorite.",
        "When {name}'s maul moves lesser warriors step back instinctively. This is the weapon {name} trusts most.",
        "{name}'s maul brings the weight of the battlefield itself down on its target. {name}'s true favorite.",
    ],
    "Short Spear": [
        "{name}'s short spear lunges forward with precise deadly reach. This is clearly {name}'s favored weapon.",
        "{name}'s short spear finds its mark with ease. The arena sees how perfectly it suits {name} as {name}'s favorite.",
        "With confident thrusts {name}'s short spear tests defenses and seeks gaps. None doubt this is {name}'s chosen weapon.",
        "{name}'s short spear strikes true balanced and deadly in close quarters. This is {name}'s weapon of the heart.",
        "{name}'s short spear moves with the confidence of a weapon made for {name}. {name}'s true favorite in every fight.",
    ],
    "Boar Spear": [
        "{name}'s boar spear drives forward with the power of a charging beast. This is clearly {name}'s favored weapon.",
        "{name}'s boar spear means to impale and hold. A long brutal thrust. {name}'s weapon of choice.",
        "{name}'s boar spear lunges with hunting precision seeking vital organs. The pit knows this is {name}'s favorite.",
        "With practiced skill {name}'s boar spear finds the perfect angle for maximum damage. This is the weapon {name} loves most.",
        "{name}'s boar spear strikes like a predator's fang deep and final. {name}'s true favorite.",
    ],
    "Long Spear": [
        "{name}'s long spear extends with dangerous reach keeping the enemy at bay. This is clearly {name}'s favored weapon.",
        "{name}'s long spear commands the space. A disciplined powerful thrust. {name}'s weapon of choice.",
        "{name}'s long spear moves with calculated lethality probing for weakness. The arena recognizes {name}'s favorite.",
        "With superior range {name}'s long spear dictates the terms of the fight. This is {name}'s true favorite.",
        "{name}'s long spear strikes from a distance that lesser weapons cannot match. {name}'s bond with this spear is obvious.",
    ],
    "Pole Axe": [
        "{name}'s pole axe swings in a wide devastating arc axe head hungry for flesh. This is clearly {name}'s favored weapon.",
        "{name}'s pole axe combines reach and cleaving power. A versatile and brutal weapon. {name}'s weapon of choice.",
        "{name}'s pole axe comes down with the force of a woodsman's fury. The pit knows this is {name}'s favorite.",
        "With expert handling {name}'s pole axe finds the perfect moment to strike. This is the weapon {name} loves most.",
        "{name}'s pole axe moves like an extension of {name}'s rage. {name}'s true favorite.",
    ],
    "Halberd": [
        "{name}'s halberd descends with terrifying authority a weapon of war and execution. This is clearly {name}'s favored weapon.",
        "{name}'s halberd brings axe spike and hook to the fight. A complex and deadly tool. {name}'s weapon of choice.",
        "{name}'s halberd strikes with the weight of a battlefield veteran's experience. The arena sees {name}'s favorite.",
        "With practiced mastery {name}'s halberd finds the perfect angle for maximum carnage. This is {name}'s true favorite.",
        "{name}'s halberd moves like a reaper's scythe promising to end the fight decisively. {name}'s bond with this weapon is clear.",
    ],
    "Flail": [
        "{name}'s flail whips through the air in an unpredictable deadly arc. This is clearly {name}'s favored weapon.",
        "{name}'s flail defies easy defense. A chaotic and vicious weapon. {name}'s weapon of choice.",
        "{name}'s flail lashes out like a striking serpent seeking any opening. The pit knows this is {name}'s favorite.",
        "With expert timing {name}'s flail finds its way past guard and shield. This is the weapon {name} trusts most.",
        "{name}'s flail moves with a mind of its own hungry for contact. {name}'s true favorite.",
    ],
    "Bladed Flail": [
        "{name}'s bladed flail sings a cruel song as its edges cut through the air. This is clearly {name}'s favored weapon.",
        "{name}'s bladed flail leaves nothing untouched. A weapon of pain and blood. {name}'s weapon of choice.",
        "{name}'s bladed flail lashes forward its edges promising terrible wounds. The crowd sees {name}'s favorite.",
        "With vicious intent {name}'s bladed flail seeks to tear and rend. This is {name}'s true favorite.",
        "{name}'s bladed flail moves like a storm of razor edges beautiful and deadly. {name}'s bond with this weapon is obvious.",
    ],
    "War Flail": [
        "{name}'s war flail swings with devastating crushing force. This is clearly {name}'s favored weapon.",
        "{name}'s war flail means to end resistance. A brutal and heavy weapon. {name}'s weapon of choice.",
        "{name}'s war flail comes down like a falling building unstoppable once in motion. The pit knows this is {name}'s favorite.",
        "With half orc strength behind it {name}'s war flail becomes a siege engine. This is the weapon {name} loves most.",
        "{name}'s war flail moves with terrifying momentum promising broken bones and shattered shields. {name}'s true favorite.",
    ],
    "Battle Flail": [
        "{name}'s battle flail creates a whirlwind of steel and death. This is clearly {name}'s favored weapon.",
        "{name}'s battle flail defies prediction and defense. A monstrous weapon. {name}'s weapon of choice.",
        "{name}'s battle flail lashes out in every direction a storm of pain. The arena recognizes {name}'s favorite.",
        "With expert control {name}'s battle flail turns the air itself into a weapon. This is {name}'s true favorite.",
        "{name}'s battle flail moves like a living thing hungry for carnage. {name}'s bond with this flail is clear.",
    ],
    "Quarterstaff": [
        "{name}'s quarterstaff moves with fluid balanced precision. This is clearly {name}'s favored weapon.",
        "{name}'s quarterstaff strikes from both ends. A weapon of discipline and control. {name}'s weapon of choice.",
        "{name}'s quarterstaff dances through the air finding gaps in the defense. The pit knows this is {name}'s favorite.",
        "With practiced mastery {name}'s quarterstaff probes and strikes in perfect rhythm. This is the weapon {name} loves most.",
        "{name}'s quarterstaff moves like an extension of {name}'s will. {name}'s true favorite.",
    ],
    "Great Staff": [
        "{name}'s great staff swings with heavy sweeping power. This is clearly {name}'s favored weapon.",
        "{name}'s great staff demands space. A larger more imposing version of the quarterstaff. {name}'s weapon of choice.",
        "{name}'s great staff moves with deliberate crushing authority. The arena sees {name}'s favorite.",
        "With two handed strength {name}'s great staff becomes a battering ram of wood and will. This is {name}'s true favorite.",
        "{name}'s great staff strikes with the weight of ancient tradition behind it. {name}'s bond with this staff is obvious.",
    ],
    "Buckler": [
        "{name}'s buckler moves with quick defensive precision. This is clearly {name}'s favored weapon.",
        "{name}'s buckler darts to meet incoming blows. A small but nimble shield. {name}'s weapon of choice.",
        "{name}'s buckler snaps into position ready to deflect and counter. The pit knows this is {name}'s favorite.",
        "With practiced ease {name}'s buckler finds the perfect angle to turn the attack. This is the weapon {name} trusts most.",
        "{name}'s buckler moves like a second skin protecting and enabling at once. {name}'s true favorite.",
    ],
    "Target Shield": [
        "{name}'s target shield moves with solid reliable defense. This is clearly {name}'s favored weapon.",
        "{name}'s target shield catches blows with confidence. A well balanced shield. {name}'s weapon of choice.",
        "{name}'s target shield snaps forward absorbing impact and creating openings. The arena recognizes {name}'s favorite.",
        "With dwarven practicality {name}'s target shield does exactly what is needed. This is {name}'s true favorite.",
        "{name}'s target shield moves with the steady assurance of a proven defender. {name}'s bond with this shield is clear.",
    ],
    "Tower Shield": [
        "{name}'s tower shield moves like a moving wall imposing and unbreakable. This is clearly {name}'s favored weapon.",
        "{name}'s tower shield dares the enemy to strike. A massive barrier of steel. {name}'s weapon of choice.",
        "{name}'s tower shield advances with deliberate crushing presence. The pit knows this is {name}'s favorite.",
        "With half orc strength behind it {name}'s tower shield becomes an iron fortress. This is the weapon {name} loves most.",
        "{name}'s tower shield moves with the weight of certainty nothing will pass. {name}'s true favorite.",
    ],
    "Cestus": [
        "{name}'s cestus strikes with the fury of a bare fist given steel teeth. This is clearly {name}'s favored weapon.",
        "{name}'s cestus turns the hand into a mace. A brutal close range weapon. {name}'s weapon of choice.",
        "{name}'s cestus punches forward seeking to crush bone and pulp flesh. The arena sees {name}'s favorite.",
        "With martial precision {name}'s cestus finds the perfect striking surface. This is the weapon {name} trusts most.",
        "{name}'s cestus moves like an iron gauntlet given deadly purpose. {name}'s true favorite.",
    ],
    "Trident": [
        "{name}'s trident lunges forward with three deadly points seeking flesh. This is clearly {name}'s favored weapon.",
        "{name}'s trident strikes with fisher's precision. A weapon of the arena and the sea. {name}'s weapon of choice.",
        "{name}'s trident thrusts with the intent to pin and hold its prey. The pit knows this is {name}'s favorite.",
        "With practiced skill {name}'s trident finds the perfect angle for maximum damage. This is {name}'s true favorite.",
        "{name}'s trident moves like a predator's claw designed to impale and control. {name}'s bond with this trident is obvious.",
    ],
    "Net": [
        "{name}'s net whips through the air seeking to entangle and trap. This is clearly {name}'s favored weapon.",
        "{name}'s net dances with dangerous grace. A weapon of control and frustration. {name}'s weapon of choice.",
        "{name}'s net flies forward its weighted edges hungry for limbs and weapons. The crowd sees {name}'s favorite.",
        "With expert timing {name}'s net seeks to rob the opponent of mobility and options. This is the weapon {name} loves most.",
        "{name}'s net moves like a living thing looking to wrap and bind its target. {name}'s true favorite.",
    ],
    "Scythe": [
        "{name}'s scythe sweeps in a wide deadly arc promising harvest of flesh. This is clearly {name}'s favored weapon.",
        "{name}'s scythe reaps without mercy. A farmer's tool turned instrument of death. {name}'s weapon of choice.",
        "{name}'s scythe moves with graceful terrifying efficiency. The arena recognizes {name}'s favorite.",
        "With practiced sweeps {name}'s scythe seeks to open terrible wounds. This is {name}'s true favorite.",
        "{name}'s scythe cuts through the air like fate itself cold and inevitable. {name}'s bond with this scythe is clear.",
    ],
    "Great Pick": [
        "{name}'s great pick comes down like the mountain's own judgment. This is clearly {name}'s favored weapon.",
        "{name}'s great pick seeks to punch through anything. A weapon of pure penetration. {name}'s weapon of choice.",
        "{name}'s great pick strikes with the force of a siege engine. The pit knows this is {name}'s favorite.",
        "With devastating intent {name}'s great pick drives for the heart of the armor. This is the weapon {name} loves most.",
        "{name}'s great pick moves with unstoppable piercing purpose. {name}'s true favorite.",
    ],
    "Javelin": [
        "{name}'s javelin flies forward with hunting precision. This is clearly {name}'s favored weapon.",
        "{name}'s javelin cuts the air with deadly speed. A thrown spear seeking its mark. {name}'s weapon of choice.",
        "{name}'s javelin launches with the intent to impale and end the threat. The arena sees {name}'s favorite.",
        "With practiced form {name}'s javelin seeks a vital point from a distance. This is {name}'s true favorite.",
        "{name}'s javelin strikes like a bolt from the sky sudden and final. {name}'s bond with this javelin is obvious.",
    ],
    "Ball & Chain": [
        "{name}'s ball and chain swings in a heavy crushing arc. This is clearly {name}'s favored weapon.",
        "{name}'s ball and chain defies easy defense. A brutal and unpredictable weapon. {name}'s weapon of choice.",
        "{name}'s ball and chain comes down with devastating smashing force. The pit knows this is {name}'s favorite.",
        "With raw power {name}'s ball and chain seeks to break bone and spirit alike. This is the weapon {name} trusts most.",
        "{name}'s ball and chain moves like a falling anchor promising ruin on contact. {name}'s true favorite.",
    ],
    "Swordbreaker": [
        "{name}'s swordbreaker moves with the intent to catch and shatter steel. This is clearly {name}'s favored weapon.",
        "{name}'s swordbreaker waits for the perfect moment to trap a blade. A specialized weapon. {name}'s weapon of choice.",
        "{name}'s swordbreaker darts forward its notches hungry for enemy weapons. The crowd sees {name}'s favorite.",
        "With expert timing {name}'s swordbreaker seeks to disarm and destroy. This is {name}'s true favorite.",
        "{name}'s swordbreaker moves like a predator of other weapons waiting to bite. {name}'s bond with this weapon is clear.",
    ],
    "Club": [
        "{name}'s club swings with simple brutal honesty. This is clearly {name}'s favored weapon.",
        "{name}'s club seeks to break what it hits. A crude but effective weapon. {name}'s weapon of choice.",
        "{name}'s club comes down with the force of raw unrefined violence. The arena recognizes {name}'s favorite.",
        "With straightforward intent {name}'s club delivers its message in broken bones. This is the weapon {name} loves most.",
        "{name}'s club moves like the first weapon humanity ever made simple and final. {name}'s true favorite.",
    ],
    "Bola": [
        "{name}'s bola whips through the air seeking to tangle and trip. This is clearly {name}'s favored weapon.",
        "{name}'s bola dances with dangerous intent. A weapon of control and frustration. {name}'s weapon of choice.",
        "{name}'s bola flies forward its weighted cords hungry for limbs. The pit knows this is {name}'s favorite.",
        "With practiced accuracy {name}'s bola seeks to rob the opponent of mobility. This is {name}'s true favorite.",
        "{name}'s bola moves like a living snare looking to wrap and bind its prey. {name}'s bond with this bola is obvious.",
    ],
    "Heavy Barbed Whip": [
        "{name}'s heavy barbed whip lashes out with cruel cutting intent. This is clearly {name}'s favored weapon.",
        "{name}'s barbed whip seeks to tear and yank. A weapon of pain and control. {name}'s weapon of choice.",
        "{name}'s heavy barbed whip cracks through the air promising agony on contact. The arena sees {name}'s favorite.",
        "With expert flicks {name}'s barbed whip finds exposed flesh and vulnerable limbs. This is the weapon {name} loves most.",
        "{name}'s barbed whip moves like a serpent with steel teeth hungry for blood. {name}'s true favorite.",
    ],
    "Open Hand": [
        "{name}'s open hand strikes with the precision of a martial artist. This is clearly {name}'s favored weapon.",
        "Empty handed but deadly. {name}'s open hand finds its target with practiced grace. {name}'s weapon of choice.",
        "{name}'s open hand moves with fluid controlled power. The pit knows this is {name}'s favorite.",
        "With disciplined focus {name}'s open hand seeks the perfect striking surface. This is {name}'s true favorite.",
        "{name}'s open hand strikes like a master's technique given lethal purpose. {name}'s bond with this style is obvious.",
    ],
}


# ---------------------------------------------------------------------------
# FIGHT RESULT
# ---------------------------------------------------------------------------

@dataclass
class FightResult:
    """Summary of a completed fight. No draws exist."""
    winner          : Optional[Warrior]
    loser           : Optional[Warrior]
    loser_died      : bool
    minutes_elapsed : int
    narrative       : str
    training_results: dict  = field(default_factory=dict)
    # Per-fighter combat metrics — used by update_recognition v2
    winner_hp_pct    : float = 1.0   # winner's HP fraction at fight end
    loser_hp_pct     : float = 0.0   # loser's HP fraction at fight end
    winner_knockdowns: int   = 0     # knockdowns delivered by winner
    loser_knockdowns : int   = 0     # knockdowns delivered by loser
    winner_near_kills: int   = 0     # times winner reduced opponent below 20% HP
    loser_near_kills : int   = 0     # times loser reduced opponent below 20% HP


# ---------------------------------------------------------------------------
# COMBAT STATE
# ---------------------------------------------------------------------------

@dataclass
class _CState:
    """Mutable in-fight state for one warrior."""
    warrior            : Warrior
    current_hp         : int
    endurance          : float
    is_on_ground       : bool    = False
    active_strat_idx   : int     = 1
    active_strategy    : Strategy = None
    consecutive_ground : int     = 0
    concede_attempts   : int     = 0
    hp_at_last_concede : int     = 9999
    knockdowns_dealt   : int     = 0   # knockdowns inflicted on opponent
    near_kills_dealt   : int     = 0   # times this warrior reduced opponent below 20% HP
    
    # Racial ability tracking (per fight)
    tabaxi_frenzy_used : bool    = False  # Tabaxi: once-per-fight frenzy burst
    tabaxi_frenzy_remaining: int = 0      # Remaining actions in frenzy (0-4)
    
    # Favorite weapon tracking
    revealed_favorite_this_fight: bool = False  # Favorite weapon already revealed in this bout

    def to_fighter_state(self) -> FighterState:
        return FighterState(
            warrior             = self.warrior,
            current_hp          = self.current_hp,
            max_hp              = self.warrior.max_hp,
            endurance           = self.endurance,
            is_on_ground        = self.is_on_ground,
            active_strategy_idx = self.active_strat_idx,
            active_strategy     = self.active_strategy,
        )

    @property
    def hp_pct(self) -> float:
        return self.current_hp / max(1, self.warrior.max_hp)

    @property
    def wants_to_concede(self) -> bool:
        """True when at <=25% HP and HP has dropped since last concede attempt."""
        if self.current_hp <= 0:
            return True
        if self.hp_pct > 0.25:
            return False
        return self.current_hp < self.hp_at_last_concede


# ---------------------------------------------------------------------------
# CORE ROLL FUNCTIONS
# ---------------------------------------------------------------------------

def _d100() -> int:
    return random.randint(1, 100)


def _initiative_roll(warrior: Warrior, strategy: Strategy, state: _CState) -> int:
    """d100 + DEX_bonus + initiative_skill*3 + luck + style_mod + activity_mod + race_init_bonus"""
    roll = _d100()
    dex  = effective_dex(warrior.dexterity, warrior.armor or "None", warrior.helm or "None", warrior.race.name)
    dex_bonus    = max(-10, min(10, (dex - 10) * 2))
    skill_bonus  = warrior.skills.get("initiative", 0) * 3
    luck_bonus   = warrior.luck
    props        = get_style_props(strategy.style)
    style_mod    = int(props.apm_modifier * 4)
    activity_mod = (strategy.activity - 5) * 2
    race_init_bonus = warrior.race.modifiers.initiative_bonus - warrior.race.modifiers.initiative_penalty
    endurance_pen= int(max(0, (40 - state.endurance) * 0.3)) if state.endurance < 40 else 0
    if state.is_on_ground:
        return max(1, roll // 2)
    return max(1, roll + dex_bonus + skill_bonus + luck_bonus
               + style_mod + activity_mod + race_init_bonus - endurance_pen)


def _attack_roll(attacker: Warrior, strategy: Strategy, state: _CState) -> int:
    """d100 + DEX + weapon_skill*5 + luck + style_mod + feint + lunge bonuses"""
    roll  = _d100()
    dex   = effective_dex(attacker.dexterity, attacker.armor or "None", attacker.helm or "None", attacker.race.name)
    dex_b = max(-8, min(8, (dex - 10)))

    wpn_key   = attacker.primary_weapon.lower().replace(" ", "_").replace("&", "and")
    wpn_skill = attacker.skills.get(wpn_key, 0)
    wpn_b     = wpn_skill * 5

    luck_b    = attacker.luck
    props     = get_style_props(strategy.style)
    style_b   = int(props.apm_modifier * 3)
    feint_b   = attacker.skills.get("feint", 0) * 2
    lunge_b   = attacker.skills.get("lunge", 0) * 3 if strategy.style == "Lunge" else 0
    end_pen   = int(max(0, (30 - state.endurance) * 0.5)) if state.endurance < 30 else 0
    hp0_pen   = 30 if state.current_hp <= 0 else 0
    
    # Favorite weapon bonus: +5 when using favorite
    fav_bonus = 0
    if attacker.favorite_weapon and attacker.primary_weapon == attacker.favorite_weapon:
        fav_bonus = 5

    return max(1, roll + dex_b + wpn_b + luck_b + style_b + feint_b + lunge_b
               - end_pen - hp0_pen + fav_bonus)


def _defense_roll(
    defender  : Warrior,
    strategy  : Strategy,
    state     : _CState,
    attacker  : Warrior,
    aim_point : str,
    atk_style : str,
    is_parry  : bool = True,
) -> int:
    """
    Parry: d100 + STR_bonus + parry_skill*4 + weapon_skill*3 + luck + style + activity
    Dodge: d100 + DEX_bonus + dodge_skill*4 + weapon_skill*2 + luck + style + size_bonus
    Weapon skill helps both: knowing your weapon improves both blocking and evasion.
    """
    roll      = _d100()
    luck_b    = defender.luck
    props     = get_style_props(strategy.style)
    wpn_key   = defender.primary_weapon.lower().replace(" ", "_").replace("&", "and")
    wpn_skill = defender.skills.get(wpn_key, 0)

    # DEX training bonus: each trained DEX point adds to defense rolls
    # +2.5 per point for dodge (rounded), +2 per point for parry.
    dex_trained = defender.attribute_gains.get("dexterity", 0)

    if is_parry:
        str_b    = max(-5, min(5, (defender.strength - 10) // 2))
        skill_b  = defender.skills.get("parry", 0) * 4
        wpn_b    = wpn_skill * 3
        style_b  = props.parry_bonus * 3
        act_mod  = (5 - strategy.activity) * 2
        dex_train_parry = int(dex_trained * 2)   # +2 per trained DEX point
        race_parry_b = defender.race.modifiers.parry_bonus - defender.race.modifiers.parry_penalty
        total    = roll + str_b + skill_b + wpn_b + style_b + act_mod + luck_b + dex_train_parry + race_parry_b
    else:
        dex      = effective_dex(defender.dexterity, defender.armor or "None", defender.helm or "None", defender.race.name)
        dex_b    = max(-8, min(8, (dex - 10)))
        skill_b  = defender.skills.get("dodge", 0) * 4
        wpn_b    = wpn_skill * 2
        style_b  = props.dodge_bonus * 2
        act_mod  = (strategy.activity - 5) * 2
        size_diff= attacker.size - defender.size
        size_b   = 5 if size_diff >= 3 else (-5 if size_diff <= -3 else 0)
        dex_train_dodge = int(dex_trained * 2.5) # +2.5 per trained DEX point
        race_dodge_b = defender.race.modifiers.dodge_bonus - defender.race.modifiers.dodge_penalty
        
        # Goblin heavy weapon dodge penalty
        goblin_dodge_pen = 0
        if defender.race.modifiers.heavy_weapon_penalty:
            try:
                wpn = get_weapon(defender.primary_weapon)
                is_two_hand = (defender.secondary_weapon == "Open Hand" and wpn.two_hand)
                if wpn.weight >= 4.0 or is_two_hand:
                    goblin_dodge_pen = -2  # -2 dodge penalty for heavy/two-handed weapons
            except ValueError:
                pass
        
        total    = roll + dex_b + skill_b + wpn_b + style_b + act_mod + size_b + luck_b + dex_train_dodge + race_dodge_b + goblin_dodge_pen

    if strategy.defense_point != "None" and strategy.defense_point == aim_point:
        total += 15

    try:
        sec_w = get_weapon(defender.secondary_weapon or "Open Hand")
        if sec_w.is_shield:
            total += 10 if defender.race.modifiers.shield_bonus else 5
    except ValueError:
        pass

    if props.total_kill_mode:
        return max(1, roll // 3)

    if state.endurance < 30:
        total -= int((30 - state.endurance) * 0.4)
    if state.is_on_ground:
        total -= 25
    if state.current_hp <= 0:
        total -= 30

    return max(1, total)


# ---------------------------------------------------------------------------
# DAMAGE (HYBRID)
# ---------------------------------------------------------------------------

def _calc_damage_hybrid(
    attacker    : Warrior,
    atk_strategy: Strategy,
    weapon_name : str,
    defender    : Warrior,
    margin      : int,
) -> Tuple[int, str]:
    """
    Ceiling = stats + weapon + race + skill + luck.
    Fraction = min(1.0, margin / 80.0)
    Net = max(1, ceiling * fraction - armor)
    """
    try:
        weapon = get_weapon(weapon_name)
    except ValueError:
        weapon = OPEN_HAND

    two_handed = (attacker.secondary_weapon == "Open Hand" and weapon.two_hand)

    base  = weapon.weight * 2.5
    
    # Apply strength modifiers (including racial penalties like Goblin/Tabaxi)
    strength_with_bonus = attacker.strength - attacker.race.modifiers.strength_penalty
    base += max(0.0, (strength_with_bonus - 10)) * 0.6
    
    if weapon.flail_bypass or weapon.category == "Flail":
        base += max(0.0, (attacker.size - 12)) * 0.4
    if two_handed or weapon.two_hand:
        base *= 1.15
    
    r_mod  = attacker.race.modifiers
    base  += r_mod.damage_bonus - r_mod.damage_penalty
    
    # Lizardfolk natural weapons bonus to Martial Combat
    if r_mod.natural_weapons_bonus and atk_strategy.style in ("Martial Combat", "Open Hand"):
        base += r_mod.natural_weapons_bonus
    
    props  = get_style_props(atk_strategy.style)
    base  += props.damage_modifier
    base  += (5 - atk_strategy.activity) * 0.3
    wpn_key = weapon_name.lower().replace(" ", "_").replace("&", "and")
    base  += attacker.skills.get(wpn_key, 0) * 0.8
    base  += attacker.luck * 0.15
    base  *= (1.0 - strength_penalty(weapon.weight, attacker.strength, two_handed))
    
    # Goblin heavy weapon damage penalty
    if r_mod.heavy_weapon_penalty:
        if weapon.weight >= 4.0 or two_handed:
            base -= 2  # -2 damage penalty for heavy/two-handed weapons
    
    ceiling = max(3, int(base))

    fraction = max(0.10, min(1.00, margin / 80.0))
    raw      = max(1, int(ceiling * fraction))

    armor_nm = defender.armor or "None"
    helm_nm  = defender.helm  or "None"
    defense  = total_defense_value(armor_nm, helm_nm, defender.race.name)
    if weapon.armor_piercing and is_ap_vulnerable(armor_nm):
        defense = max(0, defense // 2)

    final_dmg = max(1, raw - defense)
    
    # Favorite weapon bonus: +1 damage when using favorite
    if attacker.favorite_weapon and weapon_name == attacker.favorite_weapon:
        final_dmg += 1
    
    return final_dmg, weapon.category


# ---------------------------------------------------------------------------
# PERM INJURY
# ---------------------------------------------------------------------------

_LOCATION_POOL = [
    "head", "chest", "chest", "abdomen",
    "primary_arm", "secondary_arm",
    "primary_leg", "secondary_leg",
]


def _check_perm_injury(
    warrior   : Warrior,
    damage    : int,
    aim_point : str,
) -> Optional[Tuple[str, int]]:
    if damage < warrior.max_hp * 0.15:
        return None
    chance = max(5, min(80, int((damage / warrior.max_hp) * 100) - 5))
    if warrior.race.modifiers.fewer_perms:
        chance = int(chance * 0.85)
    if random.randint(1, 100) > chance:
        return None
    if aim_point and aim_point != "None":
        loc_map = {
            "Head":"head","Chest":"chest","Abdomen":"abdomen",
            "Primary Arm":"primary_arm","Secondary Arm":"secondary_arm",
            "Primary Leg":"primary_leg","Secondary Leg":"secondary_leg",
        }
        location = loc_map.get(aim_point, random.choice(_LOCATION_POOL))
    else:
        location = random.choice(_LOCATION_POOL)
    pct    = damage / warrior.max_hp
    levels = 3 if pct > 0.50 else (2 if pct > 0.35 else 1)
    return location, levels


# ---------------------------------------------------------------------------
# KNOCKDOWN
# ---------------------------------------------------------------------------

def _check_knockdown(warrior: Warrior, state: _CState, damage: int, cat: str) -> bool:
    if state.is_on_ground:
        return False
    chance  = int((damage / max(1, warrior.max_hp)) * 80)
    if cat in ("Hammer/Mace","Flail"):  chance += 10
    if cat == "Polearm/Spear":          chance += 5
    chance -= max(0, (warrior.size - 12)) * 2
    return random.randint(1, 100) <= max(1, chance)


def _check_trip_entangle(
    weapon_name: str,
    attacker: Warrior,
    defender: Warrior,
    def_state: _CState,
    strategy: Strategy,
    damage: int
) -> Tuple[bool, str, int]:
    """
    Check if a weapon with entangle/trip capability (bola, heavy_whip) causes trip.
    Returns: (should_trip: bool, narrative_line: str, extra_damage: int)
    
    Bola:
    - Thrown (Opportunity Throw style): 70% chance to trip
    - Melee swings: 35% chance to trip
    Extra damage from impact: 1-3 HP (bola-specific)
    
    Heavy Whip:
    - Hit chance: 50% to entangle and trip
    Extra damage from fall/barbs: 1-4 HP
    """
    if def_state.is_on_ground:
        return False, "", 0
    
    wpn_key = weapon_name.lower().replace(" ", "_").replace("&", "and")
    
    # Bola entangle/trip
    if wpn_key == "bola":
        is_thrown = strategy.style == "Opportunity Throw"
        chance = 70 if is_thrown else 35
        
        if random.randint(1, 100) <= chance:
            extra_dmg = random.randint(1, 3)  # Minor damage from balls/fall
            if is_thrown:
                narrative = f"The bola wraps around {defender.name.upper()}'s legs and trips them to the ground!"
            else:
                narrative = f"The swinging bola tangles {defender.name.upper()}'s legs!"
            return True, narrative, extra_dmg
    
    # Heavy Barbed Whip entangle/trip
    elif wpn_key == "heavy_whip":
        chance = 50  # Good chance to entangle/trip
        
        if random.randint(1, 100) <= chance:
            extra_dmg = random.randint(1, 4)  # Minor damage from barbs/fall
            narrative = f"The barbed whip wraps around {defender.name.upper()}'s legs, yanking them to the ground!"
            return True, narrative, extra_dmg
    
    return False, "", 0


# ---------------------------------------------------------------------------
# DEATH CHECK
# ---------------------------------------------------------------------------

def _death_check(prev_hp: int, damage: int) -> bool:
    """
    Death probability on reaching 0 HP:
      base 0.5%, +1% per HP of overshoot, cap 50%.
    """
    new_hp    = prev_hp - damage
    if new_hp > 0:
        return False
    overshoot = abs(min(new_hp, 0))
    return random.random() * 100 < min(50.0, 0.5 + float(overshoot))


# ---------------------------------------------------------------------------
# CONCEDE CHECK
# ---------------------------------------------------------------------------

def _concede_check(warrior: Warrior, state: _CState, is_monster_fight: bool = False) -> bool:
    """
    d100 + PRE_bonus + luck//2 vs threshold (max(40, 68 - PRE//3)).
    High Presence = lower threshold = easier to get mercy.
    Effective mercy rate ~40-55% when triggered; overall fight death ~2.5-3%.
    """
    if is_monster_fight:
        return False
    roll      = _d100()
    presence  = warrior.presence
    pre_b     = max(-6, min(10, presence - 10))
    total     = roll + pre_b + warrior.luck // 2
    threshold = max(40, 68 - (presence // 3))
    return total >= threshold


# ---------------------------------------------------------------------------
# ENDURANCE
# ---------------------------------------------------------------------------

def _update_endurance(
    state: _CState, strategy: Strategy, actions: int, foe: _CState
) -> List[str]:
    lines  = []
    props  = get_style_props(strategy.style)
    burn   = props.endurance_burn + (strategy.activity - 5) * 0.3
    state.endurance = max(0.0, min(100.0, state.endurance - burn * actions))
    if props.anxiously_awaits and strategy.activity < 6:
        foe.endurance = max(0.0, foe.endurance - (6 - strategy.activity) * 0.5)
        if random.random() < 0.20:
            ln = N.anxious_line(state.warrior.name, foe.warrior.name)
            if ln:
                lines.append(ln)
    if state.endurance <= 20 and random.random() < 0.40:
        lines.append(N.fatigue_line(state.warrior.name, state.warrior.gender, True))
    elif state.endurance <= 40 and random.random() < 0.20:
        lines.append(N.fatigue_line(state.warrior.name, state.warrior.gender, False))
    return lines


# ---------------------------------------------------------------------------
# APM
# ---------------------------------------------------------------------------

def _calc_apm(warrior: Warrior, strategy: Strategy, state: _CState) -> int:
    dex  = effective_dex(warrior.dexterity, warrior.armor or "None", warrior.helm or "None", warrior.race.name)
    wpn  = warrior.primary_weapon.lower().replace(" ", "_").replace("&", "and")
    base = 2.0
    base += max(0.0, (dex - 10)) * 0.20
    base += max(0.0, (warrior.intelligence - 10)) * 0.10
    base += strategy.activity * 0.25
    base += warrior.skills.get(wpn, 0) * 0.20
    r    = warrior.race.modifiers
    base += r.attack_rate_bonus * 0.25 - r.attack_rate_penalty * 0.25
    base += get_style_props(strategy.style).apm_modifier
    
    # Tabaxi frenzy burst: +3 APM for 3-4 actions, once per fight
    if r.frenzy_burst and state.tabaxi_frenzy_remaining > 0:
        base += 3  # +3 APM during frenzy
    
    # Goblin heavy weapon penalty
    if r.heavy_weapon_penalty:
        try:
            weapon = get_weapon(warrior.primary_weapon)
            is_two_hand = (warrior.secondary_weapon == "Open Hand" and weapon.two_hand)
            if weapon.weight >= 4.0 or is_two_hand:
                base -= 3  # -3 attack rate penalty for heavy/two-handed weapons
        except ValueError:
            pass
    
    # Tabaxi endurance penalty (additional penalty when fatigued)
    tabaxi_end_penalty = r.endurance_penalty if r.endurance_penalty else 0
    
    if state.endurance < 40:
        base -= (40 - state.endurance) / 40 * 1.5
    if state.endurance < 40 and tabaxi_end_penalty != 0:
        base += tabaxi_end_penalty * 0.15  # Additional penalty scales with endurance burn
    if state.is_on_ground:
        base *= 0.5
    return max(1, min(10, int(round(base))))


# ---------------------------------------------------------------------------
# REFEREE INTERVENTION NARRATIVE POOLS
# ---------------------------------------------------------------------------

_REF_STONE_EVENTS = [
    ("The Ref hurls a large rock at {n}",
     "The rock connects with {n}'s temple — {n} staggers, eyes glazed."),
    ("The Ref scoops up a fist-sized stone and flings it at {n}",
     "It cracks hard against {n}'s ribs. {n} doubles over with a grunt."),
    ("The Ref hurls a jagged chunk of stone at {n}",
     "It opens a gash above {n}'s eye — {n} blinks through the blood, vision blurring."),
    ("The Ref seizes a heavy stone and hurls it at {n}",
     "The stone thuds into {n}'s chest. {n} gasps, the air driven from their lungs."),
    ("The Ref flings a sharp-edged rock at {n}",
     "It catches {n} across the shoulder — {n} winces and nearly drops their guard."),
    ("The Ref grabs a handful of gravel and hurls it straight at {n}'s face",
     "{n} recoils, blinded for a moment, eyes streaming."),
    ("The Ref hurls a stone at the back of {n}'s head",
     "{n} lurches forward, stumbling to keep their footing."),
    ("The Ref snatches up a loose cobble and sends it spinning at {n}",
     "It clips {n} across the jaw. {n} spits blood and shakes their head."),
]

_REF_WEAPON_EVENTS = [
    ("The Ref snatches up a length of chain and lashes it hard across {n}'s back",
     "{n} arches in agony, a ragged cry escaping them."),
    ("The Ref grabs a discarded wooden staff and drives it into {n}'s ribs",
     "The crack of wood on bone rings out — {n} bends double, wheezing."),
    ("The Ref seizes a blunted club and crashes it across {n}'s shoulders",
     "{n} staggers forward, knees buckling under the blow."),
    ("The Ref picks up a short iron rod and swings it hard into {n}'s thigh",
     "{n} stumbles badly, leg trembling, nearly losing their footing."),
    ("The Ref grabs a training sword and slaps the flat of it hard across {n}'s back",
     "The smack echoes across the pit — {n} flinches and lurches forward."),
]

_REF_FOLLOWUP_EVENTS = [
    ("Still unsatisfied, the Ref hurls another stone at {n}",
     "It clips {n} across the ear. {n} is visibly shaken."),
    ("The Ref shouts at {n} to fight — then flings a second stone",
     "The stone drives into {n}'s ribs. The crowd jeers."),
    ("The Ref storms forward and drives the butt of a spear into {n}'s back",
     "{n} pitches forward with a cry, barely keeping their feet."),
    ("Furious with {n}'s passivity, the Ref heaves another stone",
     "It strikes {n} hard in the kidney. {n} nearly goes down."),
    ("The crowd howls as the Ref hurls a second stone at {n}",
     "It catches {n} glancing across the jaw. {n} spits blood and staggers."),
]


# ---------------------------------------------------------------------------
# COMBAT ENGINE
# ---------------------------------------------------------------------------

class CombatEngine:

    def __init__(
        self,
        warrior_a       : Warrior,
        warrior_b       : Warrior,
        team_a_name     : str  = "Team A",
        team_b_name     : str  = "Team B",
        manager_a_name  : str  = "Manager A",
        manager_b_name  : str  = "Manager B",
        pos_a           : int  = 1,
        pos_b           : int  = 1,
        is_monster_fight: bool = False,
    ):
        self.warrior_a        = warrior_a
        self.warrior_b        = warrior_b
        self.team_a_name      = team_a_name
        self.team_b_name      = team_b_name
        self.manager_a_name   = manager_a_name
        self.manager_b_name   = manager_b_name
        self.pos_a            = pos_a
        self.pos_b            = pos_b
        self.is_monster_fight = is_monster_fight

        self.state_a = _CState(warrior=warrior_a, current_hp=warrior_a.max_hp, endurance=100.0)
        self.state_b = _CState(warrior=warrior_b, current_hp=warrior_b.max_hp, endurance=100.0)

        if warrior_a.strategies:
            self.state_a.active_strategy  = warrior_a.strategies[-1]
            self.state_a.active_strat_idx = len(warrior_a.strategies)
        if warrior_b.strategies:
            self.state_b.active_strategy  = warrior_b.strategies[-1]
            self.state_b.active_strat_idx = len(warrior_b.strategies)

        self._lines: List[str] = []
        self._prev_attacks_a: int = 0
        self._prev_attacks_b: int = 0
        self._used_adv_phrases: set = set()
        self._last_adv_tier: str = "even"
        self._last_adv_winner: str = ""

    # =========================================================================
    # MAIN LOOP
    # =========================================================================

    def resolve_fight(self) -> FightResult:
        self._lines.append(N.build_fight_header(
            self.warrior_a, self.warrior_b,
            self.team_a_name, self.team_b_name,
            self.manager_a_name, self.manager_b_name,
            self.pos_a, self.pos_b,
        ))
        self._lines.append("")

        minute = 0
        result = None
        # PRE hesitation check: high-presence warrior may cause opponent to lose minute 1
        self._apply_presence_hesitation()
        while True:
            minute += 1
            # Referee intervention: starts minute 7, pressures the losing warrior
            if minute >= 7:
                self._throw_stones(minute)
            result  = self._run_minute(minute)
            if result:
                break
            # 30-minute limit: judge awards decision — but NOT in monster fights,
            # which must always end in death (no time limit, no mercy).
            if minute >= 30 and not self.is_monster_fight:
                pct_a   = self.state_a.current_hp / max(1, self.warrior_a.max_hp)
                pct_b   = self.state_b.current_hp / max(1, self.warrior_b.max_hp)
                win_w   = self.warrior_a if pct_a >= pct_b else self.warrior_b
                los_w   = self.warrior_b if pct_a >= pct_b else self.warrior_a
                self._emit("")
                self._emit(f"The Blood Master calls time — {win_w.name.upper()} wins on judges' decision!")
                result = self._make_result(win_w, los_w, False, minute)
                break
            # Safety valve for monster fights: after 60 minutes the monster
            # finishes it — a player warrior cannot outlast a monster forever.
            if minute >= 60 and self.is_monster_fight:
                # Monster wins; player warrior dies from exhaustion
                dw = self.state_a.warrior  # player is always warrior_a
                kw = self.state_b.warrior
                dw.injuries.add("chest", 9)
                self._emit("")
                self._emit(f"{dw.name.upper()} collapses from sheer exhaustion — the monster is relentless!")
                self._emit(N.death_line(dw.name, dw.gender))
                self._emit(""); self._emit(N.victory_line(kw.name, dw.name))
                result = self._make_result(kw, dw, True, minute)
                break

        training = {}
        self._emit("")   # blank line between fight outcome and training block
        for w, opp, is_opp in [
            (self.warrior_a, self.warrior_b, False),
            (self.warrior_b, self.warrior_a, True),
        ]:
            # Dead warriors do not train — they're carried out on a shield
            if result.loser_died and result.loser is w:
                training[w.name] = []
                continue
            res = self._apply_training(w, opponent=opp)
            training[w.name] = res
            if res:
                self._emit(N.training_summary(w.name, res, is_opponent=is_opp))

        result.training_results = training
        result.narrative        = "\n".join(self._lines)
        return result

    # =========================================================================
    # SINGLE MINUTE
    # =========================================================================

    # =========================================================================
    # RESULT BUILDER
    # =========================================================================

    def _make_result(self, winner: Warrior, loser: Warrior,
                     loser_died: bool, minutes_elapsed: int) -> FightResult:
        """Build a FightResult populated with per-fighter combat metrics."""
        if winner is self.warrior_a:
            ws, ls = self.state_a, self.state_b
        else:
            ws, ls = self.state_b, self.state_a
        return FightResult(
            winner=winner,
            loser=loser,
            loser_died=loser_died,
            minutes_elapsed=minutes_elapsed,
            narrative="\n".join(self._lines),
            winner_hp_pct=max(0.0, ws.current_hp / max(1, winner.max_hp)),
            loser_hp_pct=max(0.0, ls.current_hp / max(1, loser.max_hp)),
            winner_knockdowns=ws.knockdowns_dealt,
            loser_knockdowns=ls.knockdowns_dealt,
            winner_near_kills=ws.near_kills_dealt,
            loser_near_kills=ls.near_kills_dealt,
        )

    # =========================================================================
    # MINUTE ADVANTAGE
    # =========================================================================

    _END_BRINK_THRESHOLD = 15.0   # endurance below this = potential exhaustion brink

    def _calc_minute_advantage(self) -> tuple:
        """
        Returns (tier, winner_name, loser_name) describing the current fight state.

        tier is one of: "even", "slight", "clear", "dominating", "brink", "brink_exhaustion"
        winner_name / loser_name are empty strings when tier == "even".
        """
        hp_a = self.state_a.current_hp
        hp_b = self.state_b.current_hp
        end_a = self.state_a.endurance
        end_b = self.state_b.endurance

        total_hp = max(1, hp_a + hp_b)
        hp_ratio = hp_a / total_hp   # 0–1; > 0.5 means warrior_a leads

        # Small endurance nudge (max ±0.08 shift on the score)
        end_adj = (end_a - end_b) / 100.0 * 0.08
        score = hp_ratio + end_adj
        score = max(0.0, min(1.0, score))

        if score >= 0.5:
            winner, loser = self.warrior_a, self.warrior_b
            winner_state, loser_state = self.state_a, self.state_b
            magnitude = score
        else:
            winner, loser = self.warrior_b, self.warrior_a
            winner_state, loser_state = self.state_b, self.state_a
            magnitude = 1.0 - score

        # Endurance brink override: loser is too gassed to continue effectively
        # Only fires when the loser isn't already winning (magnitude < 0.55 means
        # the HP difference alone wouldn't call it in the winner's favour clearly)
        loser_end = loser_state.endurance
        if loser_end <= self._END_BRINK_THRESHOLD and magnitude < 0.80:
            return ("brink_exhaustion", winner.name, loser.name)

        # Map magnitude → tier using the user-specified confidence bands
        if magnitude < 0.56:
            return ("even", "", "")
        elif magnitude < 0.66:
            return ("slight", winner.name, loser.name)
        elif magnitude < 0.81:
            return ("clear", winner.name, loser.name)
        elif magnitude < 0.95:
            return ("dominating", winner.name, loser.name)
        else:
            return ("brink", winner.name, loser.name)

    def _run_minute(self, minute: int) -> Optional[FightResult]:
        self._emit(f"\nMINUTE {minute}")
        if minute == 1:
            self._emit(random.choice(N.FIGHT_OPENERS))
        else:
            tier, winner_name, loser_name = self._calc_minute_advantage()
            adv_line = N.minute_status_line(
                winner_name, loser_name,
                tier, self._last_adv_tier, self._last_adv_winner,
                self._used_adv_phrases,
            )
            self._emit(adv_line)
            self._emit("")
            self._last_adv_tier = tier
            self._last_adv_winner = winner_name
            if random.random() < 0.15:
                self._emit(N.crowd_line(self.warrior_a.race.name, self.warrior_b.race.name))

        fs_a = self.state_a.to_fighter_state()
        fs_b = self.state_b.to_fighter_state()
        strat_a, idx_a = evaluate_triggers(self.warrior_a.strategies, fs_a, fs_b, minute)
        strat_b, idx_b = evaluate_triggers(self.warrior_b.strategies, fs_b, fs_a, minute)

        if idx_a != self.state_a.active_strat_idx:
            self._emit(N.strategy_switch_line(self.warrior_a.name, idx_a))
        if idx_b != self.state_b.active_strat_idx:
            self._emit(N.strategy_switch_line(self.warrior_b.name, idx_b))
        self.state_a.active_strategy  = strat_a;  self.state_a.active_strat_idx = idx_a
        self.state_b.active_strategy  = strat_b;  self.state_b.active_strat_idx = idx_b

        for st in (self.state_a, self.state_b):
            if st.is_on_ground:
                st.consecutive_ground += 1
                if random.randint(1, 100) <= 40 + st.warrior.skills.get("brawl", 0) * 8:
                    st.is_on_ground       = False
                    st.consecutive_ground = 0
                    self._emit(N.getup_line(st.warrior.name, st.warrior.gender))

        apm_a = _calc_apm(self.warrior_a, strat_a, self.state_a)
        apm_b = _calc_apm(self.warrior_b, strat_b, self.state_b)
        
        # Tabaxi frenzy burst: trigger once per fight when tactical moment arrives
        # (can be triggered when trailing, low endurance, or to push advantage)
        if self.warrior_a.race.name == "Tabaxi" and not self.state_a.tabaxi_frenzy_used:
            if self.state_a.current_hp < self.warrior_a.max_hp * 0.40 or \
               (self.state_a.endurance < 50 and self.state_b.endurance > self.state_a.endurance + 20):
                # Trigger frenzy: +3 APM for 3-4 actions
                self.state_a.tabaxi_frenzy_used = True
                self.state_a.tabaxi_frenzy_remaining = random.randint(3, 4)
                self._emit(f"\n*** {self.warrior_a.name.upper()} enters a FRENZY of lightning-quick strikes! ***\n")
        
        if self.warrior_b.race.name == "Tabaxi" and not self.state_b.tabaxi_frenzy_used:
            if self.state_b.current_hp < self.warrior_b.max_hp * 0.40 or \
               (self.state_b.endurance < 50 and self.state_a.endurance > self.state_b.endurance + 20):
                # Trigger frenzy: +3 APM for 3-4 actions
                self.state_b.tabaxi_frenzy_used = True
                self.state_b.tabaxi_frenzy_remaining = random.randint(3, 4)
                self._emit(f"\n*** {self.warrior_b.name.upper()} enters a FRENZY of lightning-quick strikes! ***\n")
        
        rem_a = apm_a;  rem_b = apm_b
        act_a = act_b = crowd = 0

        while rem_a > 0 or rem_b > 0:
            end = self._check_fatal_injury()
            if end:
                return end

            crowd += 1
            if crowd >= 5 and random.random() < 0.35:
                self._emit(N.crowd_line(self.warrior_a.race.name, self.warrior_b.race.name))
                crowd = 0

            if rem_a > 0 and rem_b > 0:
                ia = _initiative_roll(self.warrior_a, strat_a, self.state_a)
                ib = _initiative_roll(self.warrior_b, strat_b, self.state_b)
                if ia >= ib:
                    as_, ds_ = self.state_a, self.state_b
                    ax, dx   = strat_a, strat_b
                    rem_a -= 1;  act_a += 1
                else:
                    as_, ds_ = self.state_b, self.state_a
                    ax, dx   = strat_b, strat_a
                    rem_b -= 1;  act_b += 1
            elif rem_a > 0:
                as_, ds_, ax, dx = self.state_a, self.state_b, strat_a, strat_b
                rem_a -= 1;  act_a += 1
            else:
                as_, ds_, ax, dx = self.state_b, self.state_a, strat_b, strat_a
                rem_b -= 1;  act_b += 1

            r = self._resolve_action(as_, ds_, ax, dx, minute)
            if r:
                return r

            # Tabaxi frenzy counter: decrement remaining frenzy actions
            if as_.tabaxi_frenzy_remaining > 0:
                as_.tabaxi_frenzy_remaining -= 1
            
            for cst, ost in [(self.state_a, self.state_b), (self.state_b, self.state_a)]:
                if cst.wants_to_concede:
                    cst.hp_at_last_concede = cst.current_hp
                    r = self._attempt_concede(cst, ost, minute)
                    if r:
                        return r

        for ln in _update_endurance(self.state_a, strat_a, act_a, self.state_b):
            self._emit(ln)
        for ln in _update_endurance(self.state_b, strat_b, act_b, self.state_a):
            self._emit(ln)
        self._prev_attacks_a = act_a
        self._prev_attacks_b = act_b
        return None

    # =========================================================================
    # ACTION
    # =========================================================================

    def _resolve_action(self, as_: _CState, ds_: _CState, ax: Strategy, dx: Strategy, minute: int) -> Optional[FightResult]:
        att = as_.warrior;  dfr = ds_.warrior
        wpn = att.primary_weapon;  aim = ax.aim_point

        intent = N.style_intent_line(att.name, dfr.name, ax.style, wpn, att.gender)
        if intent:
            self._emit(intent)

        try:    weapon = get_weapon(wpn);  cat = weapon.category
        except: weapon = OPEN_HAND;        cat = "Oddball"

        self._emit(N.attack_line(att.name, dfr.name, wpn, cat, ax.style, aim, att.gender))

        atk_r = _attack_roll(att, ax, as_)
        atk_r += get_style_advantage(ax.style, dx.style) * 6

        props_d = get_style_props(dx.style)
        use_p   = props_d.parry_bonus >= props_d.dodge_bonus
        def_r   = _defense_roll(dfr, dx, ds_, att, aim, ax.style, is_parry=use_p)
        margin  = atk_r - def_r

        if margin <= 0:
            if margin == 0:
                self._emit(N.miss_line(att.name, wpn))
            elif margin <= -30:
                if use_p:
                    barely = (-margin < 20)
                    self._emit(N.parry_line(dfr.name, barely=barely, defense_point_active=(dx.defense_point == aim)))
                    if dx.style == "Counterstrike" and not ds_.is_on_ground:
                        if random.randint(1, 100) <= 30 + dfr.skills.get("parry", 0) * 5:
                            self._emit(N.counterstrike_line(dfr.name, att.name))
                            return self._counterstrike(ds_, as_, dx, ax, minute)
                else:
                    self._emit(N.dodge_line(dfr.name))
            else:
                if use_p:
                    self._emit(N.parry_line(dfr.name, barely=True, defense_point_active=(dx.defense_point == aim)))
                else:
                    self._emit(N.dodge_line(dfr.name))
            return None

        if margin < 10:
            self._emit(f"{att.name.upper()}'s blow barely grazes {dfr.name.upper()}!")
            ds_.current_hp -= 1
            return None

        precision = "precise" if margin >= 50 else ("barely" if margin < 20 else "normal")
        for ln in N.hit_line(att.name, dfr.name, wpn, cat, aim, precision):
            self._emit(ln)

        dmg, wcats = _calc_damage_hybrid(att, ax, wpn, dfr, margin)
        self._emit(N.damage_line(dmg, dfr.max_hp))
        
        # Reveal favorite weapon on first use in this fight (successful hit)
        if (not as_.revealed_favorite_this_fight and 
            att.favorite_weapon and 
            wpn == att.favorite_weapon and
            att.favorite_weapon in FAVORITE_WEAPON_LINES):
            fav_line = random.choice(FAVORITE_WEAPON_LINES[att.favorite_weapon])
            self._emit(fav_line.format(name=att.name))
            as_.revealed_favorite_this_fight = True

        prev_hp        = ds_.current_hp
        ds_.current_hp -= dmg

        # Near-kill tracking: attacker reduced defender through the 20% HP threshold
        nk_threshold = int(dfr.max_hp * 0.20)
        if prev_hp > nk_threshold >= ds_.current_hp:
            as_.near_kills_dealt += 1

        if _check_knockdown(dfr, ds_, dmg, wcats):
            self._emit(N.knockdown_line(dfr.name, dfr.gender))
            ds_.is_on_ground = True
            as_.knockdowns_dealt += 1
        else:
            # Check for trip/entangle mechanics (bola, heavy whip)
            should_trip, trip_narrative, extra_dmg = _check_trip_entangle(
                wpn, att, dfr, ds_, ax, dmg
            )
            if should_trip:
                self._emit(trip_narrative)
                ds_.is_on_ground = True
                ds_.current_hp -= extra_dmg
                if extra_dmg > 0:
                    self._emit(N.damage_line(extra_dmg, dfr.max_hp))

        perm = _check_perm_injury(dfr, dmg, aim)
        if perm:
            loc, lvls = perm
            fatal     = dfr.injuries.add(loc, lvls)
            for ln in N.perm_injury_lines(dfr.name, loc, lvls, dfr.gender):
                self._emit(ln)
            if fatal:
                self._emit(N.death_line(dfr.name, dfr.gender))
                self._emit("")
                self._emit(N.victory_line(att.name, dfr.name))
                return self._make_result(att, dfr, True, minute)

        if ds_.current_hp <= 0:
            return self._handle_zero_hp(ds_, as_, prev_hp, dmg, minute)
        return None

    # =========================================================================
    # COUNTERSTRIKE
    # =========================================================================

    def _counterstrike(self, as_: _CState, ds_: _CState, ax: Strategy, dx: Strategy, minute: int) -> Optional[FightResult]:
        att = as_.warrior;  dfr = ds_.warrior;  wpn = att.primary_weapon
        try:    cat = get_weapon(wpn).category
        except: cat = "Oddball"
        for ln in N.hit_line(att.name, dfr.name, wpn, cat, ax.aim_point, "precise"):
            self._emit(ln)
        dmg, _ = _calc_damage_hybrid(att, ax, wpn, dfr, 40)
        self._emit(N.damage_line(dmg, dfr.max_hp))
        prev       = ds_.current_hp
        ds_.current_hp -= dmg

        # Near-kill tracking for counterstrike damage
        nk_threshold = int(dfr.max_hp * 0.20)
        if prev > nk_threshold >= ds_.current_hp:
            as_.near_kills_dealt += 1

        if ds_.current_hp <= 0:
            return self._handle_zero_hp(ds_, as_, prev, dmg, minute)
        return None

    # =========================================================================
    # ZERO HP
    # =========================================================================

    def _handle_zero_hp(self, dying: _CState, killer: _CState, prev: int, dmg: int, minute: int) -> Optional[FightResult]:
        dw = dying.warrior;  kw = killer.warrior
        if self.is_monster_fight:
            dw.injuries.add("chest", 9)
            self._emit(f"{dw.name.upper()} collapses — the monster shows no mercy!")
            self._emit(N.death_line(dw.name, dw.gender))
            self._emit(""); self._emit(N.victory_line(kw.name, dw.name))
            return self._make_result(kw, dw, True, minute)
        if _death_check(prev, dmg):
            dw.injuries.add("chest", 9)
            self._emit(N.death_line(dw.name, dw.gender))
            self._emit(""); self._emit(N.victory_line(kw.name, dw.name))
            return self._make_result(kw, dw, True, minute)
        # Survived: concede system takes over via wants_to_concede
        return None

    # =========================================================================
    # CONCEDE
    # =========================================================================

    def _attempt_concede(self, dying: _CState, killer: _CState, minute: int) -> Optional[FightResult]:
        dw = dying.warrior;  kw = killer.warrior
        self._emit(N.appeal_line(dw.name))
        dying.concede_attempts += 1
        granted = _concede_check(dw, dying, self.is_monster_fight)
        self._emit(N.mercy_result_line(dw.name, granted))
        if granted:
            self._emit(""); self._emit(N.victory_line(kw.name, dw.name))
            return self._make_result(kw, dw, False, minute)
        return None

    # =========================================================================
    # FATAL INJURY CHECK
    # =========================================================================

    def _check_fatal_injury(self) -> Optional[FightResult]:
        for d, k in [(self.state_a, self.state_b), (self.state_b, self.state_a)]:
            if d.warrior.injuries.is_fatal():
                return self._make_result(k.warrior, d.warrior, True, 0)
        return None

    # =========================================================================
    # TRAINING
    # =========================================================================

    def _apply_training(self, w: Warrior, opponent: Optional[Warrior] = None) -> List[str]:
        """
        Apply training. If w is alive and has INT >= 15, there is a chance
        they pick up a 4th bonus skill observed from the opponent's combat style.
        """
        res = []
        for sk in w.trains[:3]:
            res.append(w.train_skill(sk))

        # INT 4th train: learn a skill from opponent
        # Chance = (intelligence - 14) * 5%, triggered when INT >= 15
        if opponent and w.intelligence >= 15:
            bonus_chance = (w.intelligence - 14) * 5
            if random.randint(1, 100) <= bonus_chance:
                # Derive what skills the opponent actually used this fight
                candidate_skills = []
                opp_strats = opponent.strategies or []
                for s in opp_strats:
                    if s.style in ("Parry", "Counterstrike"):
                        candidate_skills.append("parry")
                    if s.style in ("Strike", "Bash", "Total Kill", "Counterstrike"):
                        candidate_skills.append("initiative")
                    if s.style in ("Dodge",):
                        candidate_skills.append("dodge")
                # Always include weapon skill and basic skills as observables
                opp_wpn = (opponent.primary_weapon or "Short Sword").lower().replace(" ","_").replace("&","and")
                candidate_skills += [opp_wpn, "dodge", "parry", "initiative", "feint"]
                # Pick one, avoiding skills already at max
                random.shuffle(candidate_skills)
                for sk in candidate_skills:
                    sk_key = sk.lower().replace(" ","_")
                    if sk_key in w.skills and w.skills[sk_key] < 9:
                        bonus_result = w.train_skill(sk_key)
                        if "trained:" in bonus_result:
                            res.append(f"[OBSERVED] {bonus_result}")
                        break

        w.recalculate_derived()
        return res

    def _apply_presence_hesitation(self):
        """
        If warrior_a has high Presence, warrior_b may hesitate at the start
        of the fight (and vice versa). The hesitation skips their first action.
        Presence 14 = 0%, 16 = 6%, 18 = 12%, 20 = 18%, 25 = 33%
        """
        for attacker_state, defender_state in [
            (self.state_a, self.state_b),
            (self.state_b, self.state_a),
        ]:
            chance = attacker_state.warrior.presence_hesitate_chance
            if chance > 0 and random.randint(1, 100) <= chance:
                defender_state.endurance = max(0.0, defender_state.endurance - 15)
                self._emit(
                    f"{attacker_state.warrior.name.upper()}'s commanding presence "
                    f"makes {defender_state.warrior.name.upper()} hesitate!"
                )

    def _throw_stones(self, minute: int):
        """
        From minute 7 onward the referee intervenes to pressure the losing warrior
        and keep the fight from becoming a marathon.

        - Monster fights are never slow to end — no intervention needed there.
        - Target: warrior at lower HP%. Equal HP → random choice.
        - Damage: (minute - 6) * 2, but the Ref never kills — floor at 1 HP.
        - No HP numbers shown in the narrative.
        - If the loser attacked ≤1 times last minute (passive), ~55% chance of
          a follow-up intervention the same minute.
        """
        if self.is_monster_fight:
            return

        pct_a = self.state_a.current_hp / max(1, self.warrior_a.max_hp)
        pct_b = self.state_b.current_hp / max(1, self.warrior_b.max_hp)
        if pct_a < pct_b:
            target_state = self.state_a
        elif pct_b < pct_a:
            target_state = self.state_b
        else:
            target_state = random.choice([self.state_a, self.state_b])

        dmg = (minute - 6) * 2
        n = target_state.warrior.name.upper()

        # Primary intervention — 20% chance the Ref grabs a weapon instead of a stone
        if random.random() < 0.20:
            action, effect = random.choice(_REF_WEAPON_EVENTS)
        else:
            action, effect = random.choice(_REF_STONE_EVENTS)

        target_state.current_hp = max(1, target_state.current_hp - dmg)
        self._emit("")
        self._emit(action.format(n=n))
        self._emit(effect.format(n=n))

        # Follow-up if the loser was passive last minute (≤1 attacks)
        losing_attacks = (
            self._prev_attacks_a if target_state is self.state_a
            else self._prev_attacks_b
        )
        if losing_attacks <= 1 and random.random() < 0.55:
            action2, effect2 = random.choice(_REF_FOLLOWUP_EVENTS)
            target_state.current_hp = max(1, target_state.current_hp - dmg)
            self._emit(action2.format(n=n))
            self._emit(effect2.format(n=n))

    def _emit(self, line: str):
        self._lines.append(line)


# ---------------------------------------------------------------------------
# CONVENIENCE
# ---------------------------------------------------------------------------

def run_fight(
    warrior_a       : Warrior,
    warrior_b       : Warrior,
    team_a_name     : str  = "Team A",
    team_b_name     : str  = "Team B",
    manager_a_name  : str  = "Manager A",
    manager_b_name  : str  = "Manager B",
    is_monster_fight: bool = False,
) -> FightResult:
    engine = CombatEngine(
        warrior_a, warrior_b,
        team_a_name, team_b_name,
        manager_a_name, manager_b_name,
        is_monster_fight=is_monster_fight,
    )
    result = engine.resolve_fight()
    if result.winner and result.loser:
        # Only update records for player-team warriors.
        # Monsters: always show 0-0-0.  Peasants: same — they are arena fodder.
        npc_races = {"Monster", "Peasant"}
        if result.winner.race.name not in npc_races:
            result.winner.record_result("win", killed_opponent=result.loser_died)
        if result.loser.race.name not in npc_races:
            result.loser.record_result("loss")
    return result
