PoE2 Crafting System Design - Complete Edition
==============================================

Research Summary
----------------

### Item Modifier System

**Modifier Types:**

1.  **Implicit Modifiers**
    -   Built into base item type
    -   Always present regardless of rarity
    -   Cannot be changed by most currency (except Vaal Orb)
    -   Example: Topaz Ring always has Lightning Resistance
2.  **Explicit Modifiers**
    -   Affixes added through crafting
    -   Two types: **Prefixes** and **Suffixes**
    -   Can be modified via crafting

**Modifier Limits by Rarity:**

-   **Magic Items**: Max 2 explicit mods (1 prefix + 1 suffix)
-   **Rare Items**: Max 6 explicit mods (3 prefixes + 3 suffixes)

**Prefix Types** (Defensive/Offensive):

-   Flat or % increased armor, evasion, energy shield
-   Maximum life, mana
-   Flat or % physical/elemental/chaos damage

**Suffix Types** (Utility/Speed):

-   Elemental & chaos resistances
-   Attack speed, cast speed
-   Critical strike chance/multiplier
-   Attribute requirements

* * * * *

Detailed Currency Mechanics
---------------------------

### Basic Currencies

#### Orb of Transmutation

-   **Function**: Upgrades Normal → Magic with 1 modifier
-   **Stack Size**: 40
-   **Tiers Available**:
    -   **Greater**: Minimum modifier level 55
    -   **Perfect**: Minimum modifier level 70
-   **Cost**: Common
-   **Note**: Can be obtained from Transmutation Shards (10 shards = 1 orb)

#### Orb of Augmentation

-   **Function**: Adds 1 modifier to Magic item (if has room)
-   **Stack Size**: 30
-   **Tiers Available**:
    -   **Greater**: Higher tier modifier
    -   **Perfect**: Highest tier modifier
-   **Cost**: Common

#### Orb of Alchemy

-   **Function**: Normal → Rare with 4 modifiers
-   **Cost**: Uncommon (much rarer in PoE2 than PoE1)
-   **Stack Size**: 10
-   **Note**: Cannot be obtained from shards in PoE2 (unlike PoE1)

#### Regal Orb

-   **Function**: Magic → Rare, keeps existing mods, adds 1 new
-   **Stack Size**: 20
-   **Tiers Available**:
    -   **Greater**: Higher tier added modifier
    -   **Perfect**: Highest tier added modifier
-   **Cost**: Uncommon
-   **Use Case**: Preserve good Magic item mods

#### Exalted Orb

-   **Function**: Adds 1 random modifier to Rare item
-   **Stack Size**: 20
-   **Tiers Available**:
    -   **Greater**: Higher tier modifier
    -   **Perfect**: Highest tier modifier
-   **Cost**: Rare (more common in endgame)
-   **Use Case**: Fill empty affix slots

#### Chaos Orb

-   **Function**: Removes 1 random modifier, then adds 1 random modifier to Rare item
-   **Stack Size**: 20
-   **Tiers Available**:
    -   **Greater**: Better modifier pools
    -   **Perfect**: Best modifier pools
-   **Cost**: Rare
-   **Use Case**: Iterative crafting (PoE2 change from full reroll)

#### Divine Orb

-   **Function**: Randomizes numerical values of existing modifiers
-   **Stack Size**: 10
-   **Cost**: Very Rare
-   **Use Case**: Perfect rolls on good mods

#### Vaal Orb

-   **Function**: Unpredictably corrupts item (can brick or upgrade)
-   **Stack Size**: 20
-   **Cost**: Rare
-   **Use Case**: High-risk/high-reward gambles

#### Orb of Annulment

-   **Function**: Removes 1 random modifier from Rare item
-   **Stack Size**: 20
-   **Cost**: Rare
-   **Use Case**: Remove bad mods before exalting

#### Orb of Chance

-   **Function**: Upgrades Normal item randomly (can become Unique)
-   **Stack Size**: 20
-   **Cost**: Uncommon
-   **Use Case**: Gambling for unique items

#### Mirror of Kalandra

-   **Function**: Creates a perfect copy of an item (mirrored items cannot be modified)
-   **Stack Size**: 1
-   **Cost**: Extremely Rare
-   **Use Case**: Duplicate perfect items

### New/Special Currencies

#### Hinekora's Lock

-   **Function**: Allows item to foresee the result of next currency used
-   **Stack Size**: 10
-   **Note**: Modifying item removes foresight ability

#### Fracturing Orb

-   **Function**: Fractures a random modifier on rare item (locks it permanently)
-   **Stack Size**: 20
-   **Requirement**: Item must have at least 4 modifiers

* * * * *

Complete Essence System (Accurate Data)
---------------------------------------

### Essence Tiers and Core Mechanics

**4 Tiers**: Lesser, Normal, Greater, and Perfect

**Critical Mechanics:**

-   **Lesser, Normal, Greater Essences**: Upgrade a Magic item to Rare, adding a guaranteed modifier
-   **Perfect Essences**: Remove a random modifier and augment a Rare item with a new guaranteed modifier
-   **Corrupted Essences**: Also remove a random modifier and augment a Rare item with a new guaranteed modifier

### Complete Essence List with All Effects

#### Lesser Essence of the Body

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Armour or Belt**: +(30-39) to maximum Life
-   **Jewellery**: +(20-29) to maximum Life

#### Essence of the Body

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Belt, Body Armour, Helmet or Shield**: +(85-99) to maximum Life
-   **Amulet, Boots, Gloves or Ring**: +(70-84) to maximum Life

#### Greater Essence of the Body

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Belt, Body Armour, Helmet or Shield**: +(100-119) to maximum Life
-   **Amulet, Boots or Gloves**: +(85-99) to maximum Life

#### Perfect Essence of the Body

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **Body Armour**: (8-10)% increased maximum Life

#### Lesser Essence of the Mind

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Belt, Boots, Gloves, Helmet or Jewellery**: +(25-34) to maximum Mana

#### Essence of the Mind

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Belt, Boots, Gloves or Helmet**: +(65-79) to maximum Mana
-   **Jewellery**: +(80-89) to maximum Mana

#### Greater Essence of the Mind

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Belt, Boots, Gloves or Helmet**: +(80-89) to maximum Mana
-   **Jewellery**: +(90-104) to maximum Mana

#### Perfect Essence of the Mind

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **Ring**: (4-6)% increased maximum Mana

#### Lesser Essence of Enhancement

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Armour**: (27-42)% increased Armour, Evasion or Energy Shield

#### Essence of Enhancement

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Armour**: (56-67)% increased Armour, Evasion or Energy Shield

#### Greater Essence of Enhancement

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Armour**: (68-79)% increased Armour, Evasion or Energy Shield

#### Perfect Essence of Enhancement

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **Amulet**: (20-30)% increased Global Defences

#### Lesser Essence of Abrasion

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **One Handed Melee Weapon or Bow**: Adds (4-6) to (7-11) Physical Damage
-   **Two Handed Melee Weapon or Crossbow**: Adds (5-8) to (10-15) Physical Damage

#### Essence of Abrasion

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **One Handed Melee Weapon or Bow**: Adds (10-15) to (18-26) Physical Damage
-   **Two Handed Melee Weapon or Crossbow**: Adds (14-21) to (25-37) Physical Damage

#### Greater Essence of Abrasion

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **One Handed Melee Weapon or Bow**: Adds (16-24) to (28-42) Physical Damage
-   **Two Handed Melee Weapon or Crossbow**: Adds (23-35) to (39-59) Physical Damage

#### Perfect Essence of Abrasion

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **One Handed Melee Weapon or Bow**: Gain (15-20)% of Damage as Extra Physical Damage
-   **Two Handed Melee Weapon or Crossbow**: Gain (25-33)% of Damage as Extra Physical Damage

#### Lesser Essence of Flames

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **One Handed Melee Weapon or Bow**: Adds (4-6) to (7-10) Fire Damage
-   **Two Handed Melee Weapon or Crossbow**: Adds (6-9) to (10-16) Fire Damage

#### Essence of Flames

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **One Handed Melee Weapon or Bow**: Adds (20-24) to (32-37) Fire Damage
-   **Two Handed Melee Weapon or Crossbow**: Adds (30-37) to (45-56) Fire Damage

#### Greater Essence of Flames

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **One Handed Melee Weapon or Bow**: Adds (35-44) to (56-71) Fire Damage
-   **Two Handed Melee Weapon or Crossbow**: Adds (56-70) to (84-107) Fire Damage

#### Perfect Essence of Flames

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **One Handed Melee Weapon or Bow**: Gain (15-20)% of Damage as Extra Fire Damage
-   **Two Handed Melee Weapon or Crossbow**: Gain (25-33)% of Damage as Extra Fire Damage

#### Lesser Essence of Ice

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **One Handed Melee Weapon or Bow**: Adds (3-5) to (6-9) Cold Damage
-   **Two Handed Melee Weapon or Crossbow**: Adds (5-8) to (9-14) Cold Damage

#### Essence of Ice

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **One Handed Melee Weapon or Bow**: Adds (17-20) to (26-32) Cold Damage
-   **Two Handed Melee Weapon or Crossbow**: Adds (25-30) to (38-46) Cold Damage

#### Greater Essence of Ice

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **One Handed Melee Weapon or Bow**: Adds (31-38) to (47-59) Cold Damage
-   **Two Handed Melee Weapon or Crossbow**: Adds (46-57) to (70-88) Cold Damage

#### Perfect Essence of Ice

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **One Handed Melee Weapon or Bow**: Gain (15-20)% of Damage as Extra Cold Damage
-   **Two Handed Melee Weapon or Crossbow**: Gain (25-33)% of Damage as Extra Cold Damage

#### Lesser Essence of Electricity

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **One Handed Melee Weapon or Bow**: Adds 1 to (13-19) Lightning Damage
-   **Two Handed Melee Weapon or Crossbow**: Adds (1-2) to (19-27) Lightning Damage

#### Essence of Electricity

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **One Handed Melee Weapon or Bow**: Adds (1-3) to (55-60) Lightning Damage
-   **Two Handed Melee Weapon or Crossbow**: Adds (1-4) to (80-88) Lightning Damage

#### Greater Essence of Electricity

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **One Handed Melee Weapon or Bow**: Adds (1-6) to (85-107) Lightning Damage
-   **Two Handed Melee Weapon or Crossbow**: Adds (1-8) to (128-162) Lightning Damage

#### Perfect Essence of Electricity

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **One Handed Melee Weapon or Bow**: Gain (15-20)% of Damage as Extra Lightning Damage
-   **Two Handed Melee Weapon or Crossbow**: Gain (25-33)% of Damage as Extra Lightning Damage

#### Lesser Essence of Ruin

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Armour, Belt or Jewellery**: +(4-7)% to Chaos Resistance

#### Essence of Ruin

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Armour, Belt or Jewellery**: +(8-11)% to Chaos Resistance

#### Greater Essence of Ruin

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Armour, Belt or Jewellery**: +(16-19)% to Chaos Resistance

#### Perfect Essence of Ruin

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **Body Armour**: (10-15)% of Physical Damage from Hits taken as Chaos Damage

#### Lesser Essence of Battle

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Martial Weapon**: +(61-84) to Accuracy Rating

#### Essence of Battle

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Martial Weapon**: +(124-167) to Accuracy Rating

#### Greater Essence of Battle

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Martial Weapon, Gloves or Quiver**: +(237-346) to Accuracy Rating

#### Perfect Essence of Battle

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **One Handed Melee Weapon or Bow**: +4 to Level of all Attack Skills
-   **Two Handed Melee Weapon or Crossbow**: +6 to Level of all Attack Skills

#### Lesser Essence of Sorcery

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Focus or Wand**: (35-44)% increased Spell Damage
-   **Staff**: (50-64)% increased Spell Damage

#### Essence of Sorcery

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Focus or Wand**: (55-64)% increased Spell Damage
-   **Staff**: (80-94)% increased Spell Damage

#### Greater Essence of Sorcery

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Focus or Wand**: (75-89)% increased Spell Damage
-   **Staff**: (110-129)% increased Spell Damage

#### Perfect Essence of Sorcery

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **Focus or Wand**: +3 to Level of all Spell Skills
-   **Staff**: +5 to Level of all Spell Skills

#### Lesser Essence of Haste

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Martial Weapon**: (11-13)% increased Attack Speed

#### Essence of Haste

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Martial Weapon**: (17-19)% increased Attack Speed

#### Greater Essence of Haste

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Martial Weapon**: (23-25)% increased Attack Speed

#### Perfect Essence of Haste

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **Martial Weapon**: (20-25)% chance to gain Onslaught on Killing Hits with this Weapon

#### Lesser Essence of the Infinite

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Equipment**: +(9-12) to Strength, Dexterity or Intelligence

#### Essence of the Infinite

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Equipment**: +(17-20) to Strength, Dexterity or Intelligence

#### Greater Essence of the Infinite

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Equipment**: +(25-27) to Strength, Dexterity or Intelligence

#### Perfect Essence of the Infinite

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **Amulet**: (7-10)% increased Strength, Dexterity or Intelligence

#### Lesser Essence of Seeking

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Martial Weapon**: +(1.51-2.1)% to Critical Hit Chance
-   **Focus or Wand**: (34-39)% increased Critical Hit Chance for Spells
-   **Staff**: (50-59)% increased Critical Hit Chance for Spells

#### Essence of Seeking

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Martial Weapon**: +(2.11-2.7)% to Critical Hit Chance
-   **Focus or Wand**: (40-46)% increased Critical Hit Chance for Spells
-   **Staff**: (60-69)% increased Critical Hit Chance for Spells

#### Greater Essence of Seeking

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Martial Weapon**: +(3.11-3.8)% to Critical Hit Chance
-   **Focus or Wand**: (47-53)% increased Critical Hit Chance for Spells
-   **Staff**: (70-79)% increased Critical Hit Chance for Spells

#### Perfect Essence of Seeking

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **Body Armour**: Hits against you have (40-50)% reduced Critical Damage Bonus

#### Lesser Essence of Insulation

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Armour, Belt or Jewellery**: +(11-15)% to Fire Resistance

#### Essence of Insulation

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Armour, Belt or Jewellery**: +(21-25)% to Fire Resistance

#### Greater Essence of Insulation

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Armour, Belt or Jewellery**: +(31-35)% to Fire Resistance

#### Perfect Essence of Insulation

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **Belt**: (26-30)% of Fire Damage taken Recouped as Life

#### Lesser Essence of Thawing

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Armour, Belt or Jewellery**: +(11-15)% to Cold Resistance

#### Essence of Thawing

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Armour, Belt or Jewellery**: +(21-25)% to Cold Resistance

#### Greater Essence of Thawing

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Armour, Belt or Jewellery**: +(31-35)% to Cold Resistance

#### Perfect Essence of Thawing

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **Helmet**: (26-30)% of Cold Damage taken Recouped as Life

#### Lesser Essence of Grounding

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Armour, Belt or Jewellery**: +(11-15)% to Lightning Resistance

#### Essence of Grounding

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Armour, Belt or Jewellery**: +(21-25)% to Lightning Resistance

#### Greater Essence of Grounding

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Armour, Belt or Jewellery**: +(31-35)% to Lightning Resistance

#### Perfect Essence of Grounding

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **Gloves**: (26-30)% of Lightning Damage taken Recouped as Life

#### Lesser Essence of Alacrity

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Focus or Wand**: (13-16)% increased Cast Speed
-   **Staff**: (20-25)% increased Cast Speed

#### Essence of Alacrity

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Focus or Wand**: (17-20)% increased Cast Speed
-   **Staff**: (26-31)% increased Cast Speed

#### Greater Essence of Alacrity

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Focus or Wand**: (25-28)% increased Cast Speed
-   **Staff**: (38-43)% increased Cast Speed

#### Perfect Essence of Alacrity

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **Focus or Wand**: (18-20)% increased Mana Cost Efficiency
-   **Staff**: (28-32)% increased Mana Cost Efficiency

#### Lesser Essence of Opulence

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Boots, Gloves, Helmet or Jewellery**: (11-14)% increased Rarity of Items found

#### Essence of Opulence

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Boots, Gloves, Helmet or Jewellery**: (15-18)% increased Rarity of Items found

#### Greater Essence of Opulence

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Boots, Gloves, Helmet or Jewellery**: (19-21)% increased Rarity of Items found

#### Perfect Essence of Opulence

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **Gloves**: (10-15)% increased Quantity of Gold Dropped by Slain Enemies

#### Lesser Essence of Command

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Sceptre**: Allies in your Presence deal (35-44)% increased Damage

#### Essence of Command

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Sceptre**: Allies in your Presence deal (55-64)% increased Damage

#### Greater Essence of Command

**Stack Size**: 10\
**Function**: Upgrades Magic → Rare with guaranteed modifier

-   **Sceptre**: Allies in your Presence deal (75-89)% increased Damage

#### Perfect Essence of Command

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **Sceptre**: Aura Skills have (15-20)% increased Magnitudes

### Corrupted Essences

#### Essence of Hysteria

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **Helmet**: +1 to Level of all Minion Skills
-   **Body Armour**: (64-97) to (97-145) Physical Thorns damage
-   **Gloves**: (25-29)% increased Critical Damage Bonus
-   **Boots**: 30% increased Movement Speed
-   **Ring**: (50-59)% increased Mana Regeneration Rate
-   **Amulet**: (19-21)% of Damage taken Recouped as Life
-   **Belt**: +(254-304) to Stun Threshold
-   **Shield**: (20-24)% increased Block chance
-   **Quiver**: (43-50)% increased Damage with Bow Skills
-   **Focus**: (41-45)% increased Energy Shield Recharge Rate

#### Essence of Delirium

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **Body Armour**: Allocates a random Notable Passive Skill

#### Essence of Horror

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **Gloves or Boots**: 100% increased effect of Socketed Items

#### Essence of Insanity

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **Belt**: On Corruption, Item gains two Enchantments

#### Essence of the Abyss

**Stack Size**: 10\
**Function**: Removes random modifier and augments Rare

-   **Equipment**: Mark of the Abyssal Lord

Complete Omen System
--------------------

### Crafting Omens

**Chaos Orb Modifiers:**

-   **Omen of Whittling**: Chaos Orb removes lowest level modifier
-   **Omen of Sinistral Erasure**: Chaos Orb removes only prefixes
-   **Omen of Dextral Erasure**: Chaos Orb removes only suffixes
-   **Omen of Chaotic Rarity**: Chaos Orb on Waystone adds Item Rarity mods
-   **Omen of Chaotic Quantity**: Chaos Orb on Waystone adds Pack Size mods
-   **Omen of Chaotic Monsters**: Chaos Orb on Waystone adds Rare/Magic monster mods

**Alchemy Orb Modifiers:**

-   **Omen of Sinistral Alchemy**: Results in maximum prefix modifiers
-   **Omen of Dextral Alchemy**: Results in maximum suffix modifiers

**Regal Orb Modifiers:**

-   **Omen of Sinistral Coronation**: Adds only prefix modifier
-   **Omen of Dextral Coronation**: Adds only suffix modifier
-   **Omen of Homogenising Coronation**: Adds modifier of same type as existing

**Exalted Orb Modifiers:**

-   **Omen of Greater Exaltation**: Adds TWO random modifiers
-   **Omen of Sinistral Exaltation**: Adds only prefix modifier
-   **Omen of Dextral Exaltation**: Adds only suffix modifier
-   **Omen of Homogenising Exaltation**: Adds modifier of same type as existing
-   **Omen of Catalysing Exaltation**: Special catalyst-based modifier

**Annulment Orb Modifiers:**

-   **Omen of Greater Annulment**: Removes TWO modifiers
-   **Omen of Sinistral Annulment**: Removes only prefixes
-   **Omen of Dextral Annulment**: Removes only suffixes
-   **Omen of Light**: Removes only Desecrated modifiers

**Other Currency Modifiers:**

-   **Omen of Corruption**: Vaal Orb always results in change
-   **Omen of Chance**: Orb of Chance doesn't destroy item on failure
-   **Omen of the Ancients**: Orb of Chance upgrades to random Unique of same class
-   **Omen of the Blessed**: Divine Orb only rerolls Implicit modifiers
-   **Omen of Recombination**: Makes Recombination Lucky
-   **Omen of Sanctification**: Unknown effect

**Essence Modifiers:**

-   **Omen of Dextral Crystallisation**: Perfect/Corrupted Essence removes only suffixes
-   **Omen of Sinistral Crystallisation**: Perfect/Corrupted Essence removes only prefixes

### Gameplay Omens

-   **Omen of Refreshment**: Fully recovers flask/charm charges at Low Life
-   **Omen of Resurgence**: Fully recovers Life/Mana/ES at Low Life
-   **Omen of Amelioration**: Prevents 75% of XP loss on death
-   **Omen of Gambling**: 50% chance for free Gamble purchase
-   **Omen of Bartering**: Vendor incorrectly assesses item value
-   **Omen of Answered Prayers**: Next Shrine grants additional effect
-   **Omen of Secret Compartments**: Next Strongbox is reopenable
-   **Omen of the Hunt**: Possessed monsters release Azmeri Spirits
-   **Omen of Reinforcements**: Rogue Exiles summon allies

* * * * *

Desecration System
------------------

### Core Mechanics

-   **Function**: Adds "Unrevealed Desecrated Modifier" to item
-   **Process**: Must reveal modifiers at Well of Souls
-   **Restriction**: Items with Desecrated mods cannot be desecrated again
-   **If Full**: Removes a random modifier when adding desecrated mod

### Bone Currencies (Desecration Items)

#### Gnawed Bones (Low-Level Desecration)
**Maximum Item Level**: 64
**Stack Size**: 20

-   **Gnawed Jawbone**: Desecrates a Rare Weapon or Quiver
-   **Gnawed Rib**: Desecrates a Rare Armour
-   **Gnawed Collarbone**: Desecrates a Rare Amulet, Ring or Belt

#### Preserved Bones (Mid-Level Desecration)
**Stack Size**: 20

-   **Preserved Jawbone**: Desecrates a Rare Weapon or Quiver
-   **Preserved Rib**: Desecrates a Rare Armour
-   **Preserved Collarbone**: Desecrates a Rare Amulet, Ring or Belt
-   **Preserved Cranium**: Desecrates a Rare Jewel
-   **Preserved Vertebrae**: Desecrates a Rare Waystone

#### Ancient Bones (High-Level Desecration)
**Minimum Modifier Level**: 40
**Stack Size**: 20

-   **Ancient Jawbone**: Desecrates a Rare Weapon or Quiver
-   **Ancient Rib**: Desecrates a Rare Armour
-   **Ancient Collarbone**: Desecrates a Rare Amulet, Ring or Belt

### Desecration Omens

#### Core Desecration Omens
**Stack Size**: 10

-   **Omen of Abyssal Echoes**: Can reroll desecrated options once when revealing
-   **Omen of Sinistral Necromancy**: Adds only prefix desecrated modifiers
-   **Omen of Dextral Necromancy**: Adds only suffix desecrated modifiers
-   **Omen of Light**: Removes only Desecrated modifiers (with Annulment)

#### Boss-Specific Omens
**Stack Size**: 10

-   **Omen of the Sovereign**: Guarantees random Ulaman modifier
-   **Omen of the Liege**: Guarantees random Amanamu modifier
-   **Omen of the Blackblooded**: Guarantees random Kurgal modifier

#### Special Desecration Omens
**Stack Size**: 10

-   **Omen of Putrefaction**: Replaces ALL mods with up to 6 Desecrated mods and corrupts

### Abyssal Eyes (Boss-Specific Items)

**Limited to**: 1 Abyssal Eye
**Requires**: Level 60

#### Ulaman's Gaze
-   **Helmets**: +1 to Accuracy Rating per 1 Item Evasion Rating on Equipped Helmet
-   **Gloves**: Critical Hit chance is Lucky against Parried enemies
-   **Body Armours**: Prevent +3% of Damage from Deflected Hits

#### Amanamu's Gaze
-   **Helmets**: Remove a Damaging Ailment when you use a Command Skill
-   **Body Armours**: +2 to Armour per 1 Spirit
-   **Boots**: 1% increased Movement Speed per 15 Spirit, up to a maximum of 40% (Other Modifiers to Movement Speed do not apply)

#### Kurgal's Gaze
-   **Helmets**: Increases and Reductions to Life Regeneration Rate also apply to Mana Regeneration Rate
-   **Gloves**: 40% increased effect of Arcane Surge on you
-   **Boots**: 15% increased Mana Cost Efficiency if you haven't Dodge Rolled Recently

#### Tecrod's Gaze
-   **Body Armours**: Regenerate 1.5% of maximum Life per second
-   **Gloves**: 25% increased Life Cost Efficiency
-   **Boots**: 10% increased Movement Speed when on Low Life

### Well of Souls Items

-   **Kulemak's Invitation**: Something awaits you in the Well.

### Desecrated Modifier Types

The Desecrated modifier pool includes extremely powerful endgame modifiers with unique effects not available through normal crafting, including:

-   **Abyssal-themed modifiers**: Lightless prefix with various damage/defense bonuses
-   **Boss-specific modifiers**: Ulaman (accuracy/evasion), Amanamu (spirit/command), Kurgal (life/mana synergy), Tecrod (life-based)
-   **Special hybrid modifiers**: Combining multiple stats in unique ways
-   **Unique mechanics**: Not found in regular mod pools (e.g., movement speed caps, spirit scaling)

* * * * *

Removed Currencies from PoE1
----------------------------

The following currencies were removed in PoE2:

-   **Portal Scroll** (replaced with waypoint system)
-   **Chromatic Orb** (socket colors on gems, not gear)
-   **Orb of Scouring** (cannot fully reset items)
-   **Orb of Alteration** (replaced by Chaos Orb behavior)
-   **Orb of Regret** (passive respec system changed)

* * * * *

Key PoE2 Philosophy Changes
---------------------------

1.  **No Full Reset**: Items cannot be completely wiped clean
2.  **Iterative Crafting**: Chaos Orbs now remove/add one mod at a time
3.  **Essence Rework**:
    -   Lesser/Normal/Greater work on Magic items to create Rares
    -   Perfect/Corrupted work on existing Rares (remove + add)
4.  **Omen System**: Meta-crafting through Ritual rewards
5.  **Desecration**: Endgame crafting with unique modifier pools
6.  **Currency Tiers**: Greater and Perfect versions of basic currencies

* * * * *

Advanced Crafting Examples
--------------------------

### High-Value Quiver Crafting

1.  Start with fractured T1 flat damage Visceral Quiver
2.  Chaos Orb for Projectile Speed
3.  **Omen of Dextral Exaltation** + **Exalted** → Add suffix
4.  **Omen of Dextral Crystallisation** + **Essence of Hysteria** → Add (43-50)% Bow Damage
5.  **Omen of Homogenising Exaltation** + **Perfect Exalted** → Add attack suffix

### Perfect Belt with Corrupted Enchants

1.  Start with good Magic belt
2.  **Essence of Insanity** → Rare with corruption modifier
3.  **Exalted Orbs** → Fill prefixes/suffixes
4.  **Vaal Orb** → Guaranteed two corrupted enchantments

### Endgame ES Gloves with Doubled Sockets

1.  Start with high ES Magic gloves
2.  **Essence of Horror** → Rare with 100% increased socket effect
3.  **Exalted Orbs** → Fill modifiers
4.  **Vaal Orb** → Attempt to get second socket (effectively 4x socket value)

### Movement Speed Boots

1.  Start with Magic boots
2.  **Essence of Hysteria** → Rare with 30% movement speed
3.  **Omen of Dextral Exaltation** + **Exalted** → Add resist suffixes
4.  Fill remaining slots

* * * * *

Database Schema
---------------

sql

```
-- Base item types
CREATE TABLE base_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    implicit_mod_id INT REFERENCES modifiers(id),
    base_stats JSONB,
    required_level INT,
    required_str INT,
    required_dex INT,
    required_int INT
);

-- All modifiers
CREATE TABLE modifiers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    mod_type VARCHAR(20), -- prefix, suffix, implicit, desecrated
    tier INT,
    stat_text TEXT,
    stat_min FLOAT,
    stat_max FLOAT,
    required_ilvl INT,
    weight INT,
    mod_group VARCHAR(100),
    applicable_items TEXT[]
);

-- Essences with complete details
CREATE TABLE essences (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    essence_tier VARCHAR(20), -- lesser, normal, greater, perfect, corrupted
    essence_type VARCHAR(50), -- body, mind, enhancement, etc.
    mechanic VARCHAR(50), -- magic_to_rare, remove_add_rare
    stack_size INT DEFAULT 10
);

-- Essence effects per item type
CREATE TABLE essence_item_effects (
    id SERIAL PRIMARY KEY,
    essence_id INT REFERENCES essences(id),
    item_type VARCHAR(100),
    modifier_type VARCHAR(20), -- prefix, suffix
    effect_text TEXT,
    value_min FLOAT,
    value_max FLOAT
);

-- Omens
CREATE TABLE omens (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    effect_description TEXT,
    affected_currency VARCHAR(100),
    stack_size INT DEFAULT 10
);

-- Bone currencies (desecration items)
CREATE TABLE bone_currencies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    bone_type VARCHAR(50), -- gnawed, preserved, ancient
    bone_part VARCHAR(50), -- jawbone, rib, collarbone, cranium, vertebrae
    target_item_types TEXT[], -- weapon, quiver, armour, jewellery, jewel, waystone
    stack_size INT DEFAULT 20,
    min_modifier_level INT,
    max_item_level INT,
    function_description TEXT
);

-- Abyssal Eyes (boss-specific items)
CREATE TABLE abyssal_eyes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    boss_name VARCHAR(50), -- ulaman, amanamu, kurgal, tecrod
    required_level INT DEFAULT 60,
    is_limited_to_one BOOLEAN DEFAULT TRUE
);

-- Abyssal Eye effects per item slot
CREATE TABLE abyssal_eye_effects (
    id SERIAL PRIMARY KEY,
    abyssal_eye_id INT REFERENCES abyssal_eyes(id),
    item_slot VARCHAR(50), -- helmet, body_armour, gloves, boots
    effect_text TEXT,
    special_mechanics TEXT -- for unique mechanics like movement speed caps
);

-- Desecrated modifiers
CREATE TABLE desecrated_modifiers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    mod_type VARCHAR(20),
    boss_type VARCHAR(50), -- ulaman, amanamu, kurgal, tecrod, abyssal
    stat_text TEXT,
    stat_min FLOAT,
    stat_max FLOAT,
    weight INT,
    applicable_items TEXT[],
    is_unique_mechanic BOOLEAN DEFAULT FALSE,
    special_rules TEXT -- for caps, interactions, etc.
);