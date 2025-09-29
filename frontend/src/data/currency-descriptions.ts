// Currency descriptions based on poe2db.tw/us/Crafting
// Last updated: 2025-09-28

export interface CurrencyDescription {
  name: string
  description: string
  mechanics?: string
  minimumModifierLevel?: number
}

export const CURRENCY_DESCRIPTIONS: Record<string, CurrencyDescription> = {
  // Basic Orbs - Verified from poe2db.tw
  "Orb of Transmutation": {
    name: "Orb of Transmutation",
    description: "Upgrades a Normal item to a Magic item with 1 modifier"
  },
  "Greater Orb of Transmutation": {
    name: "Greater Orb of Transmutation",
    description: "Upgrades a Normal item to a Magic item with 1 modifier",
    minimumModifierLevel: 35
  },
  "Perfect Orb of Transmutation": {
    name: "Perfect Orb of Transmutation",
    description: "Upgrades a Normal item to a Magic item with 1 modifier",
    minimumModifierLevel: 50
  },

  "Orb of Augmentation": {
    name: "Orb of Augmentation",
    description: "Augments a Magic item with a new random modifier"
  },
  "Greater Orb of Augmentation": {
    name: "Greater Orb of Augmentation",
    description: "Augments a Magic item with a new random modifier",
    minimumModifierLevel: 35
  },
  "Perfect Orb of Augmentation": {
    name: "Perfect Orb of Augmentation",
    description: "Augments a Magic item with a new random modifier",
    minimumModifierLevel: 50
  },

  "Orb of Alchemy": {
    name: "Orb of Alchemy",
    description: "Upgrades a Normal item to a Rare item with 4 modifiers"
  },

  "Regal Orb": {
    name: "Regal Orb",
    description: "Upgrades a Magic item to a Rare item, adding 1 modifier"
  },
  "Greater Regal Orb": {
    name: "Greater Regal Orb",
    description: "Upgrades a Magic item to a Rare item, adding 1 modifier",
    minimumModifierLevel: 35
  },
  "Perfect Regal Orb": {
    name: "Perfect Regal Orb",
    description: "Upgrades a Magic item to a Rare item, adding 1 modifier",
    minimumModifierLevel: 50
  },

  "Exalted Orb": {
    name: "Exalted Orb",
    description: "Augments a Rare item with a new random modifier"
  },
  "Greater Exalted Orb": {
    name: "Greater Exalted Orb",
    description: "Augments a Rare item with a new random modifier",
    minimumModifierLevel: 35
  },
  "Perfect Exalted Orb": {
    name: "Perfect Exalted Orb",
    description: "Augments a Rare item with a new random modifier",
    minimumModifierLevel: 50
  },

  "Chaos Orb": {
    name: "Chaos Orb",
    description: "Removes a random modifier and augments a Rare item with a new random modifier"
  },
  "Greater Chaos Orb": {
    name: "Greater Chaos Orb",
    description: "Removes a random modifier and augments a Rare item with a new random modifier",
    minimumModifierLevel: 35
  },
  "Perfect Chaos Orb": {
    name: "Perfect Chaos Orb",
    description: "Removes a random modifier and augments a Rare item with a new random modifier",
    minimumModifierLevel: 50
  },

  "Divine Orb": {
    name: "Divine Orb",
    description: "Randomises the numeric values of modifiers on an item"
  },

  "Orb of Annulment": {
    name: "Orb of Annulment",
    description: "Removes a random modifier from a Magic or Rare item"
  },

  "Orb of Chance": {
    name: "Orb of Chance",
    description: "Unpredictably either upgrades a Normal item to Unique rarity or destroys it"
  },

  // Essences - Complete accurate data from CRAFTING_SYSTEM_DESIGN.md

  // LESSER TIER ESSENCES
  "Lesser Essence of the Body": {
    name: "Lesser Essence of the Body",
    description: "Upgrades Magic → Rare with guaranteed Life modifier",
    mechanics: "Life:\n• Armour or Belt: +(30-39)\n• Jewellery: +(20-29)"
  },
  "Lesser Essence of the Mind": {
    name: "Lesser Essence of the Mind",
    description: "Upgrades Magic → Rare with guaranteed Mana modifier",
    mechanics: "Mana: +(25-34)\n• Belt, Boots, Gloves, Helmet or Jewellery"
  },
  "Lesser Essence of Enhancement": {
    name: "Lesser Essence of Enhancement",
    description: "Upgrades Magic → Rare with guaranteed Defence modifier",
    mechanics: "Defence: (27-42)% increased Armour, Evasion or Energy Shield\n• Armour only"
  },
  "Lesser Essence of Abrasion": {
    name: "Lesser Essence of Abrasion",
    description: "Upgrades Magic → Rare with guaranteed Physical Damage",
    mechanics: "Physical Damage:\n• One-Handed/Bow: (4-6) to (7-11)\n• Two-Handed/Crossbow: (5-8) to (10-15)"
  },
  "Lesser Essence of Flames": {
    name: "Lesser Essence of Flames",
    description: "Upgrades Magic → Rare with guaranteed Fire Damage",
    mechanics: "Fire Damage:\n• One-Handed/Bow: (4-6) to (7-10)\n• Two-Handed/Crossbow: (6-9) to (10-16)"
  },
  "Lesser Essence of Ice": {
    name: "Lesser Essence of Ice",
    description: "Upgrades Magic → Rare with guaranteed Cold Damage",
    mechanics: "Cold Damage:\n• One-Handed/Bow: (3-5) to (6-9)\n• Two-Handed/Crossbow: (5-8) to (9-14)"
  },
  "Lesser Essence of Electricity": {
    name: "Lesser Essence of Electricity",
    description: "Upgrades Magic → Rare with guaranteed Lightning Damage",
    mechanics: "Lightning Damage:\n• One-Handed/Bow: 1 to (13-19)\n• Two-Handed/Crossbow: (1-2) to (19-27)"
  },
  "Lesser Essence of Ruin": {
    name: "Lesser Essence of Ruin",
    description: "Upgrades Magic → Rare with guaranteed Chaos Resistance",
    mechanics: "Chaos Resistance: +(4-7)%\n• Armour, Belt or Jewellery"
  },
  "Lesser Essence of Battle": {
    name: "Lesser Essence of Battle",
    description: "Upgrades Magic → Rare with guaranteed Accuracy",
    mechanics: "Accuracy: +(61-84)\n• Martial Weapon only"
  },
  "Lesser Essence of Sorcery": {
    name: "Lesser Essence of Sorcery",
    description: "Upgrades Magic → Rare with guaranteed Spell Damage",
    mechanics: "Spell Damage:\n• Focus/Wand: (35-44)% increased\n• Staff: (50-64)% increased"
  },
  "Lesser Essence of Haste": {
    name: "Lesser Essence of Haste",
    description: "Upgrades Magic → Rare with guaranteed Attack Speed",
    mechanics: "Attack Speed: (11-13)% increased\n• Martial Weapon only"
  },
  "Lesser Essence of the Infinite": {
    name: "Lesser Essence of the Infinite",
    description: "Upgrades Magic → Rare with guaranteed Attribute",
    mechanics: "Attributes: +(9-12) to Strength, Dexterity or Intelligence\n• Any Equipment"
  },
  "Lesser Essence of Seeking": {
    name: "Lesser Essence of Seeking",
    description: "Upgrades Magic → Rare with guaranteed Critical",
    mechanics: "Critical:\n• Martial Weapon: +(1.51-2.1)% Hit Chance\n• Focus/Wand: (34-39)% increased for Spells\n• Staff: (50-59)% increased for Spells"
  },
  "Lesser Essence of Insulation": {
    name: "Lesser Essence of Insulation",
    description: "Upgrades Magic → Rare with guaranteed Fire Resistance",
    mechanics: "Fire Resistance: +(11-15)%\n• Armour, Belt or Jewellery"
  },
  "Lesser Essence of Thawing": {
    name: "Lesser Essence of Thawing",
    description: "Upgrades Magic → Rare with guaranteed Cold Resistance",
    mechanics: "Cold Resistance: +(11-15)%\n• Armour, Belt or Jewellery"
  },
  "Lesser Essence of Grounding": {
    name: "Lesser Essence of Grounding",
    description: "Upgrades Magic → Rare with guaranteed Lightning Resistance",
    mechanics: "Lightning Resistance: +(11-15)%\n• Armour, Belt or Jewellery"
  },
  "Lesser Essence of Alacrity": {
    name: "Lesser Essence of Alacrity",
    description: "Upgrades Magic → Rare with guaranteed Cast Speed",
    mechanics: "Cast Speed:\n• Focus/Wand: (13-16)% increased\n• Staff: (20-25)% increased"
  },
  "Lesser Essence of Opulence": {
    name: "Lesser Essence of Opulence",
    description: "Upgrades Magic → Rare with guaranteed Item Rarity",
    mechanics: "Item Rarity: (11-14)% increased\n• Boots, Gloves, Helmet or Jewellery"
  },
  "Lesser Essence of Command": {
    name: "Lesser Essence of Command",
    description: "Upgrades Magic → Rare with guaranteed Command modifier",
    mechanics: "Command: Allies deal (35-44)% increased Damage\n• Sceptre only"
  },
  "Lesser Essence of the Protector": {
    name: "Lesser Essence of the Protector",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Armour modifier",
    mechanics: "Adds Armour:\n• Body Armour: +(135-164)\n• Helmet/Gloves/Boots: +(45-54)\n• Shield: +(90-109)"
  },
  "Lesser Essence of Warding": {
    name: "Lesser Essence of Warding",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Energy Shield modifier",
    mechanics: "Adds Energy Shield:\n• Body Armour: +(27-32)\n• Helmet/Gloves/Boots: +(9-10)\n• Shield: +(18-21)"
  },

  // NORMAL TIER ESSENCES
  "Essence of the Body": {
    name: "Essence of the Body",
    description: "Upgrades Magic → Rare with guaranteed Life modifier",
    mechanics: "Life:\n• Belt, Body Armour, Helmet or Shield: +(85-99)\n• Amulet, Boots, Gloves or Ring: +(70-84)"
  },
  "Essence of the Mind": {
    name: "Essence of the Mind",
    description: "Upgrades Magic → Rare with guaranteed Mana modifier",
    mechanics: "Mana:\n• Belt, Boots, Gloves or Helmet: +(65-79)\n• Jewellery: +(80-89)"
  },
  "Essence of Enhancement": {
    name: "Essence of Enhancement",
    description: "Upgrades Magic → Rare with guaranteed Defence modifier",
    mechanics: "Defence: (56-67)% increased Armour, Evasion or Energy Shield\n• Armour only"
  },
  "Essence of Abrasion": {
    name: "Essence of Abrasion",
    description: "Upgrades Magic → Rare with guaranteed Physical Damage",
    mechanics: "Physical Damage:\n• One-Handed/Bow: (10-15) to (18-26)\n• Two-Handed/Crossbow: (14-21) to (25-37)"
  },
  "Essence of Flames": {
    name: "Essence of Flames",
    description: "Upgrades Magic → Rare with guaranteed Fire Damage",
    mechanics: "Fire Damage:\n• One-Handed/Bow: (20-24) to (32-37)\n• Two-Handed/Crossbow: (30-37) to (45-56)"
  },
  "Essence of Ice": {
    name: "Essence of Ice",
    description: "Upgrades Magic → Rare with guaranteed Cold Damage",
    mechanics: "Cold Damage:\n• One-Handed/Bow: (17-20) to (26-32)\n• Two-Handed/Crossbow: (25-30) to (38-46)"
  },
  "Essence of Electricity": {
    name: "Essence of Electricity",
    description: "Upgrades Magic → Rare with guaranteed Lightning Damage",
    mechanics: "Lightning Damage:\n• One-Handed/Bow: (1-3) to (55-60)\n• Two-Handed/Crossbow: (1-4) to (80-88)"
  },
  "Essence of Ruin": {
    name: "Essence of Ruin",
    description: "Upgrades Magic → Rare with guaranteed Chaos Resistance",
    mechanics: "Chaos Resistance: +(8-11)%\n• Armour, Belt or Jewellery"
  },
  "Essence of Battle": {
    name: "Essence of Battle",
    description: "Upgrades Magic → Rare with guaranteed Accuracy",
    mechanics: "Accuracy: +(124-167)\n• Martial Weapon only"
  },
  "Essence of Sorcery": {
    name: "Essence of Sorcery",
    description: "Upgrades Magic → Rare with guaranteed Spell Damage",
    mechanics: "Spell Damage:\n• Focus/Wand: (55-64)% increased\n• Staff: (80-94)% increased"
  },
  "Essence of Haste": {
    name: "Essence of Haste",
    description: "Upgrades Magic → Rare with guaranteed Attack Speed",
    mechanics: "Attack Speed: (17-19)% increased\n• Martial Weapon only"
  },
  "Essence of the Infinite": {
    name: "Essence of the Infinite",
    description: "Upgrades Magic → Rare with guaranteed Attribute",
    mechanics: "Attributes: +(17-20) to Strength, Dexterity or Intelligence\n• Any Equipment"
  },
  "Essence of Seeking": {
    name: "Essence of Seeking",
    description: "Upgrades Magic → Rare with guaranteed Critical",
    mechanics: "Critical:\n• Martial Weapon: +(2.11-2.7)% Hit Chance\n• Focus/Wand: (40-46)% increased for Spells\n• Staff: (60-69)% increased for Spells"
  },
  "Essence of Insulation": {
    name: "Essence of Insulation",
    description: "Upgrades Magic → Rare with guaranteed Fire Resistance",
    mechanics: "Fire Resistance: +(21-25)%\n• Armour, Belt or Jewellery"
  },
  "Essence of Thawing": {
    name: "Essence of Thawing",
    description: "Upgrades Magic → Rare with guaranteed Cold Resistance",
    mechanics: "Cold Resistance: +(21-25)%\n• Armour, Belt or Jewellery"
  },
  "Essence of Grounding": {
    name: "Essence of Grounding",
    description: "Upgrades Magic → Rare with guaranteed Lightning Resistance",
    mechanics: "Lightning Resistance: +(21-25)%\n• Armour, Belt or Jewellery"
  },
  "Essence of Alacrity": {
    name: "Essence of Alacrity",
    description: "Upgrades Magic → Rare with guaranteed Cast Speed",
    mechanics: "Cast Speed:\n• Focus/Wand: (17-20)% increased\n• Staff: (26-31)% increased"
  },
  "Essence of Opulence": {
    name: "Essence of Opulence",
    description: "Upgrades Magic → Rare with guaranteed Item Rarity",
    mechanics: "Item Rarity: (15-18)% increased\n• Boots, Gloves, Helmet or Jewellery"
  },
  "Essence of Command": {
    name: "Essence of Command",
    description: "Upgrades Magic → Rare with guaranteed Command modifier",
    mechanics: "Command: Allies deal (55-64)% increased Damage\n• Sceptre only"
  },
  "Essence of the Protector": {
    name: "Essence of the Protector",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Armour modifier",
    mechanics: "Adds Armour:\n• Body Armour: +(225-274)\n• Helmet/Gloves/Boots: +(75-89)\n• Shield: +(150-179)"
  },
  "Essence of Warding": {
    name: "Essence of Warding",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Energy Shield modifier",
    mechanics: "Adds Energy Shield:\n• Body Armour: +(45-54)\n• Helmet/Gloves/Boots: +(15-17)\n• Shield: +(30-35)"
  },

  // GREATER TIER ESSENCES
  "Greater Essence of the Body": {
    name: "Greater Essence of the Body",
    description: "Upgrades Magic → Rare with guaranteed Life modifier",
    mechanics: "Life:\n• Belt, Body Armour, Helmet or Shield: +(100-119)\n• Amulet, Boots or Gloves: +(85-99)"
  },
  "Greater Essence of the Mind": {
    name: "Greater Essence of the Mind",
    description: "Upgrades Magic → Rare with guaranteed Mana modifier",
    mechanics: "Mana:\n• Belt, Boots, Gloves or Helmet: +(80-89)\n• Jewellery: +(90-104)"
  },
  "Greater Essence of Enhancement": {
    name: "Greater Essence of Enhancement",
    description: "Upgrades Magic → Rare with guaranteed Defence modifier",
    mechanics: "Defence: (68-79)% increased Armour, Evasion or Energy Shield\n• Armour only"
  },
  "Greater Essence of Abrasion": {
    name: "Greater Essence of Abrasion",
    description: "Upgrades Magic → Rare with guaranteed Physical Damage",
    mechanics: "Physical Damage:\n• One-Handed/Bow: (16-24) to (28-42)\n• Two-Handed/Crossbow: (23-35) to (39-59)"
  },
  "Greater Essence of Flames": {
    name: "Greater Essence of Flames",
    description: "Upgrades Magic → Rare with guaranteed Fire Damage",
    mechanics: "Fire Damage:\n• One-Handed/Bow: (35-44) to (56-71)\n• Two-Handed/Crossbow: (56-70) to (84-107)"
  },
  "Greater Essence of Ice": {
    name: "Greater Essence of Ice",
    description: "Upgrades Magic → Rare with guaranteed Cold Damage",
    mechanics: "Cold Damage:\n• One-Handed/Bow: (31-38) to (47-59)\n• Two-Handed/Crossbow: (46-57) to (70-88)"
  },
  "Greater Essence of Electricity": {
    name: "Greater Essence of Electricity",
    description: "Upgrades Magic → Rare with guaranteed Lightning Damage",
    mechanics: "Lightning Damage:\n• One-Handed/Bow: (1-6) to (85-107)\n• Two-Handed/Crossbow: (1-8) to (128-162)"
  },
  "Greater Essence of Ruin": {
    name: "Greater Essence of Ruin",
    description: "Upgrades Magic → Rare with guaranteed Chaos Resistance",
    mechanics: "Chaos Resistance: +(16-19)%\n• Armour, Belt or Jewellery"
  },
  "Greater Essence of Battle": {
    name: "Greater Essence of Battle",
    description: "Upgrades Magic → Rare with guaranteed Accuracy",
    mechanics: "Accuracy: +(237-346)\n• Martial Weapon, Gloves or Quiver"
  },
  "Greater Essence of Sorcery": {
    name: "Greater Essence of Sorcery",
    description: "Upgrades Magic → Rare with guaranteed Spell Damage",
    mechanics: "Spell Damage:\n• Focus/Wand: (75-89)% increased\n• Staff: (110-129)% increased"
  },
  "Greater Essence of Haste": {
    name: "Greater Essence of Haste",
    description: "Upgrades Magic → Rare with guaranteed Attack Speed",
    mechanics: "Attack Speed: (23-25)% increased\n• Martial Weapon only"
  },
  "Greater Essence of the Infinite": {
    name: "Greater Essence of the Infinite",
    description: "Upgrades Magic → Rare with guaranteed Attribute",
    mechanics: "Attributes: +(25-27) to Strength, Dexterity or Intelligence\n• Any Equipment"
  },
  "Greater Essence of Seeking": {
    name: "Greater Essence of Seeking",
    description: "Upgrades Magic → Rare with guaranteed Critical",
    mechanics: "Critical:\n• Martial Weapon: +(3.11-3.8)% Hit Chance\n• Focus/Wand: (47-53)% increased for Spells\n• Staff: (70-79)% increased for Spells"
  },
  "Greater Essence of Insulation": {
    name: "Greater Essence of Insulation",
    description: "Upgrades Magic → Rare with guaranteed Fire Resistance",
    mechanics: "Fire Resistance: +(31-35)%\n• Armour, Belt or Jewellery"
  },
  "Greater Essence of Thawing": {
    name: "Greater Essence of Thawing",
    description: "Upgrades Magic → Rare with guaranteed Cold Resistance",
    mechanics: "Cold Resistance: +(31-35)%\n• Armour, Belt or Jewellery"
  },
  "Greater Essence of Grounding": {
    name: "Greater Essence of Grounding",
    description: "Upgrades Magic → Rare with guaranteed Lightning Resistance",
    mechanics: "Lightning Resistance: +(31-35)%\n• Armour, Belt or Jewellery"
  },
  "Greater Essence of Alacrity": {
    name: "Greater Essence of Alacrity",
    description: "Upgrades Magic → Rare with guaranteed Cast Speed",
    mechanics: "Cast Speed:\n• Focus/Wand: (25-28)% increased\n• Staff: (38-43)% increased"
  },
  "Greater Essence of Opulence": {
    name: "Greater Essence of Opulence",
    description: "Upgrades Magic → Rare with guaranteed Item Rarity",
    mechanics: "Item Rarity: (19-21)% increased\n• Boots, Gloves, Helmet or Jewellery"
  },
  "Greater Essence of Command": {
    name: "Greater Essence of Command",
    description: "Upgrades Magic → Rare with guaranteed Command modifier",
    mechanics: "Command: Allies deal (75-89)% increased Damage\n• Sceptre only"
  },
  "Greater Essence of the Protector": {
    name: "Greater Essence of the Protector",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Armour modifier",
    mechanics: "Adds Armour:\n• Body Armour: +(338-409)\n• Helmet/Gloves/Boots: +(113-136)\n• Shield: +(225-274)"
  },
  "Greater Essence of Warding": {
    name: "Greater Essence of Warding",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Energy Shield modifier",
    mechanics: "Adds Energy Shield:\n• Body Armour: +(68-81)\n• Helmet/Gloves/Boots: +(23-27)\n• Shield: +(45-54)"
  },

  // PERFECT TIER ESSENCES (Remove random mod + augment Rare)
  "Perfect Essence of the Body": {
    name: "Perfect Essence of the Body",
    description: "Removes random modifier and augments Rare with guaranteed highest-tier Life modifier",
    mechanics: "Life: (8-10)% increased maximum Life\n• Body Armour only"
  },
  "Perfect Essence of the Mind": {
    name: "Perfect Essence of the Mind",
    description: "Removes random modifier and augments Rare with guaranteed highest-tier Mana modifier",
    mechanics: "Mana: (4-6)% increased maximum Mana\n• Ring only"
  },
  "Perfect Essence of Enhancement": {
    name: "Perfect Essence of Enhancement",
    description: "Removes random modifier and augments Rare with guaranteed highest-tier Defence modifier",
    mechanics: "Defence: (20-30)% increased Global Defences\n• Amulet only"
  },
  "Perfect Essence of Abrasion": {
    name: "Perfect Essence of Abrasion",
    description: "Removes random modifier and augments Rare with guaranteed highest-tier Physical Damage",
    mechanics: "Physical Damage:\n• One-Handed/Bow: (15-20)% of Damage as Extra Physical\n• Two-Handed/Crossbow: (25-33)% of Damage as Extra Physical"
  },
  "Perfect Essence of Flames": {
    name: "Perfect Essence of Flames",
    description: "Removes random modifier and augments Rare with guaranteed highest-tier Fire Damage",
    mechanics: "Fire Damage:\n• One-Handed/Bow: (15-20)% of Damage as Extra Fire\n• Two-Handed/Crossbow: (25-33)% of Damage as Extra Fire"
  },
  "Perfect Essence of Ice": {
    name: "Perfect Essence of Ice",
    description: "Removes random modifier and augments Rare with guaranteed highest-tier Cold Damage",
    mechanics: "Cold Damage:\n• One-Handed/Bow: (15-20)% of Damage as Extra Cold\n• Two-Handed/Crossbow: (25-33)% of Damage as Extra Cold"
  },
  "Perfect Essence of Electricity": {
    name: "Perfect Essence of Electricity",
    description: "Removes random modifier and augments Rare with guaranteed highest-tier Lightning Damage",
    mechanics: "Lightning Damage:\n• One-Handed/Bow: (15-20)% of Damage as Extra Lightning\n• Two-Handed/Crossbow: (25-33)% of Damage as Extra Lightning"
  },
  "Perfect Essence of Ruin": {
    name: "Perfect Essence of Ruin",
    description: "Removes random modifier and augments Rare with guaranteed highest-tier Chaos Protection",
    mechanics: "Chaos Protection: (10-15)% of Physical Damage from Hits taken as Chaos Damage\n• Body Armour only"
  },
  "Perfect Essence of Battle": {
    name: "Perfect Essence of Battle",
    description: "Removes random modifier and augments Rare with guaranteed highest-tier Attack modifier",
    mechanics: "Attack Skills:\n• One-Handed/Bow: +4 to Level of all Attack Skills\n• Two-Handed/Crossbow: +6 to Level of all Attack Skills"
  },
  "Perfect Essence of Sorcery": {
    name: "Perfect Essence of Sorcery",
    description: "Removes random modifier and augments Rare with guaranteed highest-tier Spell modifier",
    mechanics: "Spell Skills:\n• Focus/Wand: +3 to Level of all Spell Skills\n• Staff: +5 to Level of all Spell Skills"
  },
  "Perfect Essence of Haste": {
    name: "Perfect Essence of Haste",
    description: "Removes random modifier and augments Rare with guaranteed highest-tier Attack Speed modifier",
    mechanics: "Onslaught: (20-25)% chance to gain Onslaught on Killing Hits\n• Martial Weapon only"
  },
  "Perfect Essence of the Infinite": {
    name: "Perfect Essence of the Infinite",
    description: "Removes random modifier and augments Rare with guaranteed highest-tier Attribute modifier",
    mechanics: "Attributes: (7-10)% increased Strength, Dexterity or Intelligence\n• Amulet only"
  },
  "Perfect Essence of Seeking": {
    name: "Perfect Essence of Seeking",
    description: "Removes random modifier and augments Rare with guaranteed highest-tier Critical Protection",
    mechanics: "Critical Protection: Hits against you have (40-50)% reduced Critical Damage Bonus\n• Body Armour only"
  },
  "Perfect Essence of Insulation": {
    name: "Perfect Essence of Insulation",
    description: "Removes random modifier and augments Rare with guaranteed highest-tier Fire Recovery",
    mechanics: "Fire Recovery: (26-30)% of Fire Damage taken Recouped as Life\n• Belt only"
  },
  "Perfect Essence of Thawing": {
    name: "Perfect Essence of Thawing",
    description: "Removes random modifier and augments Rare with guaranteed highest-tier Cold Recovery",
    mechanics: "Cold Recovery: (26-30)% of Cold Damage taken Recouped as Life\n• Helmet only"
  },
  "Perfect Essence of Grounding": {
    name: "Perfect Essence of Grounding",
    description: "Removes random modifier and augments Rare with guaranteed highest-tier Lightning Recovery",
    mechanics: "Lightning Recovery: (26-30)% of Lightning Damage taken Recouped as Life\n• Gloves only"
  },
  "Perfect Essence of Alacrity": {
    name: "Perfect Essence of Alacrity",
    description: "Removes random modifier and augments Rare with guaranteed highest-tier Mana Efficiency",
    mechanics: "Mana Efficiency:\n• Focus/Wand: (18-20)% increased Mana Cost Efficiency\n• Staff: (28-32)% increased Mana Cost Efficiency"
  },
  "Perfect Essence of Opulence": {
    name: "Perfect Essence of Opulence",
    description: "Removes random modifier and augments Rare with guaranteed highest-tier Gold Quantity",
    mechanics: "Gold Quantity: (10-15)% increased Quantity of Gold Dropped by Slain Enemies\n• Gloves only"
  },
  "Perfect Essence of Command": {
    name: "Perfect Essence of Command",
    description: "Removes random modifier and augments Rare with guaranteed highest-tier Aura modifier",
    mechanics: "Aura Skills: (15-20)% increased Magnitudes\n• Sceptre only"
  },
  "Perfect Essence of the Protector": {
    name: "Perfect Essence of the Protector",
    description: "Removes a random modifier, then upgrades to Rare adding guaranteed highest-tier Armour modifier"
  },
  "Perfect Essence of Warding": {
    name: "Perfect Essence of Warding",
    description: "Removes a random modifier, then upgrades to Rare adding guaranteed highest-tier Energy Shield modifier"
  },


  // CORRUPTED ESSENCES (Remove random mod + augment Rare with unique modifiers)
  "Essence of Hysteria": {
    name: "Essence of Hysteria",
    description: "Removes random modifier and augments Rare with guaranteed unique Hysteria modifier",
    mechanics: "Unique modifiers by item type:\n• Helmet: +1 to Level of all Minion Skills\n• Body Armour: (64-97) to (97-145) Physical Thorns damage\n• Gloves: (25-29)% increased Critical Damage Bonus\n• Boots: 30% increased Movement Speed\n• Ring: (50-59)% increased Mana Regeneration Rate\n• Amulet: (19-21)% of Damage taken Recouped as Life\n• Belt: +(254-304) to Stun Threshold\n• Shield: (20-24)% increased Block chance\n• Quiver: (43-50)% increased Damage with Bow Skills\n• Focus: (41-45)% increased Energy Shield Recharge Rate"
  },
  "Essence of Delirium": {
    name: "Essence of Delirium",
    description: "Removes random modifier and augments Rare with guaranteed unique Delirium modifier",
    mechanics: "Unique modifier:\n• Body Armour: Allocates a random Notable Passive Skill"
  },
  "Essence of Horror": {
    name: "Essence of Horror",
    description: "Removes random modifier and augments Rare with guaranteed unique Horror modifier",
    mechanics: "Unique modifier:\n• Gloves or Boots: 100% increased effect of Socketed Items"
  },
  "Essence of Insanity": {
    name: "Essence of Insanity",
    description: "Removes random modifier and augments Rare with guaranteed unique Insanity modifier",
    mechanics: "Unique modifier:\n• Belt: On Corruption, Item gains two Enchantments"
  },
  "Essence of the Abyss": {
    name: "Essence of the Abyss",
    description: "Removes random modifier and augments Rare with guaranteed unique Abyssal modifier",
    mechanics: "Unique modifier:\n• Any Equipment: Mark of the Abyssal Lord"
  },

  // Abyssal Bones - Desecration mechanics
  "Abyssal Jawbone": {
    name: "Abyssal Jawbone",
    description: "Desecration: Offers 3 offensive modifier choices from the Well of Souls",
    mechanics: "Targets damage modifiers. Removes 1 random modifier if item has 6 modifiers. Choose 1 of 3 options."
  },
  "Ancient Abyssal Jawbone": {
    name: "Ancient Abyssal Jawbone",
    description: "Desecration: Offers 3 high-tier offensive modifier choices from the Well of Souls",
    mechanics: "Targets damage modifiers (min ilvl 40). Removes 1 random modifier if item has 6 modifiers.",
    minimumModifierLevel: 40
  },
  "Abyssal Rib": {
    name: "Abyssal Rib",
    description: "Desecration: Offers 3 defensive modifier choices from the Well of Souls",
    mechanics: "Targets life/armor/evasion/ES modifiers. Removes 1 random modifier if item has 6 modifiers."
  },
  "Ancient Abyssal Rib": {
    name: "Ancient Abyssal Rib",
    description: "Desecration: Offers 3 high-tier defensive modifier choices from the Well of Souls",
    mechanics: "Targets defensive modifiers (min ilvl 40). Removes 1 random modifier if item has 6 modifiers.",
    minimumModifierLevel: 40
  },
  "Abyssal Collarbone": {
    name: "Abyssal Collarbone",
    description: "Desecration: Offers 3 resistance modifier choices from the Well of Souls",
    mechanics: "Targets resistance modifiers. Removes 1 random modifier if item has 6 modifiers."
  },
  "Ancient Abyssal Collarbone": {
    name: "Ancient Abyssal Collarbone",
    description: "Desecration: Offers 3 high-tier resistance modifier choices from the Well of Souls",
    mechanics: "Targets resistance modifiers (min ilvl 40). Removes 1 random modifier if item has 6 modifiers.",
    minimumModifierLevel: 40
  },
  "Abyssal Cranium": {
    name: "Abyssal Cranium",
    description: "Desecration: Offers 3 caster modifier choices from the Well of Souls",
    mechanics: "Targets mana/spell/cast modifiers. Removes 1 random modifier if item has 6 modifiers."
  },
  "Ancient Abyssal Cranium": {
    name: "Ancient Abyssal Cranium",
    description: "Desecration: Offers 3 high-tier caster modifier choices from the Well of Souls",
    mechanics: "Targets caster modifiers (min ilvl 40). Removes 1 random modifier if item has 6 modifiers.",
    minimumModifierLevel: 40
  },
  "Abyssal Vertebrae": {
    name: "Abyssal Vertebrae",
    description: "Desecration: Offers 3 attribute modifier choices from the Well of Souls",
    mechanics: "Targets str/dex/int modifiers. Removes 1 random modifier if item has 6 modifiers."
  },
  "Ancient Abyssal Vertebrae": {
    name: "Ancient Abyssal Vertebrae",
    description: "Desecration: Offers 3 high-tier attribute modifier choices from the Well of Souls",
    mechanics: "Targets attribute modifiers (min ilvl 40). Removes 1 random modifier if item has 6 modifiers.",
    minimumModifierLevel: 40
  }
}

export const OMEN_DESCRIPTIONS: Record<string, CurrencyDescription> = {
  // Accurate omen data from poe2db.tw
  "Omen of Whittling": {
    name: "Omen of Whittling",
    description: "Chaos Orb removes the lowest level modifier instead of random",
    mechanics: "Right-click to activate, consumed on next Chaos Orb use"
  },
  "Omen of Greater Exaltation": {
    name: "Omen of Greater Exaltation",
    description: "Exalted Orb adds 2 random modifiers instead of 1",
    mechanics: "Right-click to activate, consumed on next Exalted Orb use"
  },
  "Omen of Sinistral Exaltation": {
    name: "Omen of Sinistral Exaltation",
    description: "Exalted Orb adds a prefix modifier instead of random",
    mechanics: "Right-click to activate, consumed on next Exalted Orb use"
  },
  "Omen of Dextral Exaltation": {
    name: "Omen of Dextral Exaltation",
    description: "Exalted Orb adds a suffix modifier instead of random",
    mechanics: "Right-click to activate, consumed on next Exalted Orb use"
  },
  "Omen of Homogenising Exaltation": {
    name: "Omen of Homogenising Exaltation",
    description: "Exalted Orb adds a modifier of the same type as an existing modifier",
    mechanics: "Right-click to activate, consumed on next Exalted Orb use"
  },
  "Omen of Catalysing Exaltation": {
    name: "Omen of Catalysing Exaltation",
    description: "Exalted Orb consumes Catalyst Quality to increase modifier chance",
    mechanics: "Right-click to activate, consumed on next Exalted Orb use"
  },
  "Omen of Sinistral Erasure": {
    name: "Omen of Sinistral Erasure",
    description: "Chaos Orb removes only prefix modifiers",
    mechanics: "Right-click to activate, consumed on next Chaos Orb use"
  },
  "Omen of Dextral Erasure": {
    name: "Omen of Dextral Erasure",
    description: "Chaos Orb removes only suffix modifiers",
    mechanics: "Right-click to activate, consumed on next Chaos Orb use"
  },
  "Omen of Greater Annulment": {
    name: "Omen of Greater Annulment",
    description: "Orb of Annulment removes 2 random modifiers instead of 1",
    mechanics: "Right-click to activate, consumed on next Orb of Annulment use"
  },
  "Omen of Sinistral Annulment": {
    name: "Omen of Sinistral Annulment",
    description: "Orb of Annulment removes a prefix modifier instead of random",
    mechanics: "Right-click to activate, consumed on next Orb of Annulment use"
  },
  "Omen of Dextral Annulment": {
    name: "Omen of Dextral Annulment",
    description: "Orb of Annulment removes a suffix modifier instead of random",
    mechanics: "Right-click to activate, consumed on next Orb of Annulment use"
  },
  "Omen of Sinistral Coronation": {
    name: "Omen of Sinistral Coronation",
    description: "Regal Orb adds a prefix when upgrading Magic to Rare",
    mechanics: "Right-click to activate, consumed on next Regal Orb use"
  },
  "Omen of Dextral Coronation": {
    name: "Omen of Dextral Coronation",
    description: "Regal Orb adds a suffix when upgrading Magic to Rare",
    mechanics: "Right-click to activate, consumed on next Regal Orb use"
  },
  "Omen of Homogenising Coronation": {
    name: "Omen of Homogenising Coronation",
    description: "Regal Orb adds a modifier of the same type as an existing modifier",
    mechanics: "Right-click to activate, consumed on next Regal Orb use"
  },
  "Omen of Sinistral Alchemy": {
    name: "Omen of Sinistral Alchemy",
    description: "Orb of Alchemy creates item with only prefix modifiers",
    mechanics: "Right-click to activate, consumed on next Orb of Alchemy use"
  },
  "Omen of Dextral Alchemy": {
    name: "Omen of Dextral Alchemy",
    description: "Orb of Alchemy creates item with only suffix modifiers",
    mechanics: "Right-click to activate, consumed on next Orb of Alchemy use"
  },
  "Omen of Corruption": {
    name: "Omen of Corruption",
    description: "Vaal Orb removes the 'no change' outcome (guarantees corruption effect)",
    mechanics: "Right-click to activate, consumed on next Vaal Orb use"
  }
}

// Helper functions
export function getCurrencyDescription(currencyName: string): string {
  const currency = CURRENCY_DESCRIPTIONS[currencyName]
  if (!currency) return currencyName

  let description = currency.description
  if (currency.minimumModifierLevel) {
    description += ` (Min Modifier Level: ${currency.minimumModifierLevel})`
  }
  if (currency.mechanics) {
    description += `\n${currency.mechanics}`
  }

  return description
}

export function getOmenDescription(omenName: string): string {
  const omen = OMEN_DESCRIPTIONS[omenName]
  if (!omen) return omenName

  let description = omen.description
  if (omen.mechanics) {
    description += `\n${omen.mechanics}`
  }

  return description
}