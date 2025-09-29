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

  // Essences - Accurate data from poe2db.tw
  // Lesser Tier Essences
  "Lesser Essence of Flames": {
    name: "Lesser Essence of Flames",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Fire damage modifier",
    mechanics: "Adds Fire Damage:\n• One-Handed/Bow: (12-15) to (19-22)\n• Two-Handed/Crossbow: (18-22) to (27-34)"
  },
  "Lesser Essence of Ice": {
    name: "Lesser Essence of Ice",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Cold damage modifier",
    mechanics: "Adds Cold Damage:\n• One-Handed/Bow: (12-15) to (19-22)\n• Two-Handed/Crossbow: (18-22) to (27-34)"
  },
  "Lesser Essence of Electricity": {
    name: "Lesser Essence of Electricity",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Lightning damage modifier",
    mechanics: "Adds Lightning Damage:\n• One-Handed/Bow: (3-4) to (41-48)\n• Two-Handed/Crossbow: (4-5) to (60-71)"
  },
  "Lesser Essence of the Body": {
    name: "Lesser Essence of the Body",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Life modifier",
    mechanics: "Adds Life:\n• Body Armour/Helmet/Shield: +(45-54)\n• Amulet/Boots/Gloves: +(35-44)\n• Belt: +(55-69)"
  },
  "Lesser Essence of the Mind": {
    name: "Lesser Essence of the Mind",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Mana modifier",
    mechanics: "Adds +(25-34) to maximum Mana\nApplicable to: Belt, Boots, Gloves, Helmet, Jewellery"
  },
  "Lesser Essence of the Protector": {
    name: "Lesser Essence of the Protector",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Armour modifier",
    mechanics: "Adds Armour:\n• Body Armour: +(135-164)\n• Helmet/Gloves/Boots: +(45-54)\n• Shield: +(90-109)"
  },
  "Lesser Essence of Haste": {
    name: "Lesser Essence of Haste",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Evasion modifier",
    mechanics: "Adds Evasion Rating:\n• Body Armour: +(135-164)\n• Helmet/Gloves/Boots: +(45-54)\n• Shield: +(90-109)"
  },
  "Lesser Essence of Warding": {
    name: "Lesser Essence of Warding",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Energy Shield modifier",
    mechanics: "Adds Energy Shield:\n• Body Armour: +(27-32)\n• Helmet/Gloves/Boots: +(9-10)\n• Shield: +(18-21)"
  },

  // Standard Tier Essences
  "Essence of Flames": {
    name: "Essence of Flames",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Fire damage modifier",
    mechanics: "Adds Fire Damage:\n• One-Handed/Bow: (20-24) to (32-37)\n• Two-Handed/Crossbow: (30-37) to (45-56)"
  },
  "Essence of Ice": {
    name: "Essence of Ice",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Cold damage modifier",
    mechanics: "Adds Cold Damage:\n• One-Handed/Bow: (20-24) to (32-37)\n• Two-Handed/Crossbow: (30-37) to (45-56)"
  },
  "Essence of Electricity": {
    name: "Essence of Electricity",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Lightning damage modifier",
    mechanics: "Adds Lightning Damage:\n• One-Handed/Bow: (5-6) to (68-80)\n• Two-Handed/Crossbow: (7-9) to (101-118)"
  },
  "Essence of the Body": {
    name: "Essence of the Body",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Life modifier",
    mechanics: "Adds Life:\n• Body Armour/Helmet/Shield: +(75-89)\n• Amulet/Boots/Gloves: +(60-74)\n• Belt: +(90-109)"
  },
  "Essence of the Mind": {
    name: "Essence of the Mind",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Mana modifier",
    mechanics: "Adds +(40-54) to maximum Mana\nApplicable to: Belt, Boots, Gloves, Helmet, Jewellery"
  },
  "Essence of the Protector": {
    name: "Essence of the Protector",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Armour modifier",
    mechanics: "Adds Armour:\n• Body Armour: +(225-274)\n• Helmet/Gloves/Boots: +(75-89)\n• Shield: +(150-179)"
  },
  "Essence of Haste": {
    name: "Essence of Haste",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Evasion modifier",
    mechanics: "Adds Evasion Rating:\n• Body Armour: +(225-274)\n• Helmet/Gloves/Boots: +(75-89)\n• Shield: +(150-179)"
  },
  "Essence of Warding": {
    name: "Essence of Warding",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Energy Shield modifier",
    mechanics: "Adds Energy Shield:\n• Body Armour: +(45-54)\n• Helmet/Gloves/Boots: +(15-17)\n• Shield: +(30-35)"
  },

  // Greater Tier Essences
  "Greater Essence of Flames": {
    name: "Greater Essence of Flames",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Fire damage modifier",
    mechanics: "Adds Fire Damage:\n• One-Handed/Bow: (30-37) to (48-56)\n• Two-Handed/Crossbow: (45-55) to (68-84)"
  },
  "Greater Essence of Ice": {
    name: "Greater Essence of Ice",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Cold damage modifier",
    mechanics: "Adds Cold Damage:\n• One-Handed/Bow: (30-37) to (48-56)\n• Two-Handed/Crossbow: (45-55) to (68-84)"
  },
  "Greater Essence of Electricity": {
    name: "Greater Essence of Electricity",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Lightning damage modifier",
    mechanics: "Adds Lightning Damage:\n• One-Handed/Bow: (8-9) to (101-118)\n• Two-Handed/Crossbow: (11-14) to (151-177)"
  },
  "Greater Essence of the Body": {
    name: "Greater Essence of the Body",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Life modifier",
    mechanics: "Adds Life:\n• Body Armour/Helmet/Shield: +(100-119)\n• Amulet/Boots/Gloves: +(85-99)\n• Belt: +(120-144)"
  },
  "Greater Essence of the Mind": {
    name: "Greater Essence of the Mind",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Mana modifier",
    mechanics: "Adds +(65-79) to maximum Mana\nApplicable to: Belt, Boots, Gloves, Helmet, Jewellery"
  },
  "Greater Essence of the Protector": {
    name: "Greater Essence of the Protector",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Armour modifier",
    mechanics: "Adds Armour:\n• Body Armour: +(338-409)\n• Helmet/Gloves/Boots: +(113-136)\n• Shield: +(225-274)"
  },
  "Greater Essence of Haste": {
    name: "Greater Essence of Haste",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Evasion modifier",
    mechanics: "Adds Evasion Rating:\n• Body Armour: +(338-409)\n• Helmet/Gloves/Boots: +(113-136)\n• Shield: +(225-274)"
  },
  "Greater Essence of Warding": {
    name: "Greater Essence of Warding",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed Energy Shield modifier",
    mechanics: "Adds Energy Shield:\n• Body Armour: +(68-81)\n• Helmet/Gloves/Boots: +(23-27)\n• Shield: +(45-54)"
  },

  // Perfect Tier Essences
  "Perfect Essence of Flames": {
    name: "Perfect Essence of Flames",
    description: "Removes a random modifier, then upgrades to Rare adding guaranteed highest-tier Fire damage modifier"
  },
  "Perfect Essence of Ice": {
    name: "Perfect Essence of Ice",
    description: "Removes a random modifier, then upgrades to Rare adding guaranteed highest-tier Cold damage modifier"
  },
  "Perfect Essence of Electricity": {
    name: "Perfect Essence of Electricity",
    description: "Removes a random modifier, then upgrades to Rare adding guaranteed highest-tier Lightning damage modifier"
  },
  "Perfect Essence of the Body": {
    name: "Perfect Essence of the Body",
    description: "Removes a random modifier, then upgrades to Rare adding guaranteed highest-tier Life modifier"
  },
  "Perfect Essence of the Mind": {
    name: "Perfect Essence of the Mind",
    description: "Removes a random modifier, then upgrades to Rare adding guaranteed highest-tier Mana modifier"
  },
  "Perfect Essence of the Protector": {
    name: "Perfect Essence of the Protector",
    description: "Removes a random modifier, then upgrades to Rare adding guaranteed highest-tier Armour modifier"
  },
  "Perfect Essence of Haste": {
    name: "Perfect Essence of Haste",
    description: "Removes a random modifier, then upgrades to Rare adding guaranteed highest-tier Evasion modifier"
  },
  "Perfect Essence of Warding": {
    name: "Perfect Essence of Warding",
    description: "Removes a random modifier, then upgrades to Rare adding guaranteed highest-tier Energy Shield modifier"
  },


  // Corrupted Essences
  "Essence of Delirium": {
    name: "Essence of Delirium",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed unique Delirium modifier",
    mechanics: "Adds essence-only modifier not available through normal crafting"
  },
  "Essence of Horror": {
    name: "Essence of Horror",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed unique Horror modifier",
    mechanics: "Adds essence-only modifier not available through normal crafting"
  },
  "Essence of Hysteria": {
    name: "Essence of Hysteria",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed unique Hysteria modifier",
    mechanics: "Adds essence-only modifier not available through normal crafting"
  },
  "Essence of Insanity": {
    name: "Essence of Insanity",
    description: "Upgrades a Magic item to a Rare item, adding a guaranteed unique Insanity modifier",
    mechanics: "Adds essence-only modifier not available through normal crafting"
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