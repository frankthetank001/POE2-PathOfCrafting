# Modifier Filtering Issue: PathOfBuilding vs Game Reality

## Problem Summary

Our crafting simulator uses PathOfBuilding-PoE2 data as the source of truth for modifiers, but there are discrepancies between what PathOfBuilding indicates is possible and what actually appears in-game. This leads to incorrect modifier availability in our simulator.

## Specific Example: Energy Shield Recharge Mods

### Game Reality (verified via poe2db.tw)
- **INT Body Armor**: ✅ Can roll "faster start of Energy Shield Recharge", ❌ Cannot roll "increased Energy Shield Recharge Rate"
- **INT Helmets/Gloves/Boots**: ❌ Cannot roll "faster start of Energy Shield Recharge", ✅ Can roll "increased Energy Shield Recharge Rate"

### PathOfBuilding Data
Both mod types show similar weight patterns that suggest they should be available on INT armor:

**Increased Energy Shield Recharge Rate (Tiers 1-4):**
```
weightKey = { "body_armour", "str_dex_int_armour", "str_int_armour", "dex_int_armour", "int_armour", "focus", "default" }
weightVal = { 0,             1,                   1,               1,               1,            1,       0 }
```

**Faster Start of Energy Shield Recharge:**
```
weightKey = { "helmet", "gloves", "boots", "shield", "str_dex_int_armour", "str_int_armour", "dex_int_armour", "int_armour", "default" }
weightVal = { 0,        0,        0,       0,        1,                   1,               1,               1,            0 }
```

## Current Workaround

We implemented a manual override system in `modifier_pool.py`:

```python
def _is_unique_only_mod_group(self, mod_group: Optional[str], item_category: str = "") -> bool:
    # Item-specific restrictions based on game knowledge
    if item_category in ['int_armour', 'str_armour', 'dex_armour', ...]:
        # Body armor cannot roll recharge rate mods (only helmet/gloves/boots can)
        body_armor_restricted = {'energyshieldregeneration'}
        if mod_group and mod_group.lower() in body_armor_restricted:
            return True
```

## Root Cause Analysis

### Potential Issues
1. **PathOfBuilding data is outdated** - Represents an older game version
2. **Category system mismatch** - Our interpretation of `int_armour` vs `body_armour` categories is incorrect
3. **Weight interpretation** - We don't properly handle complex weight interactions
4. **Missing data layers** - PathOfBuilding might have additional restriction mechanisms we're not parsing

### Weight System Complexity
The PathOfBuilding weight system is more complex than our current parsing handles:

- **Multiple categories per item**: An INT body armor might need to satisfy BOTH `body_armour` AND `int_armour` requirements
- **Slot-specific restrictions**: Same attribute type (INT) behaves differently on different slots (body vs helmet)
- **Version differences**: Higher tier mods show different weight patterns than lower tiers

## Impact on Simulator

### Current State
- **Manual overrides** maintain accuracy for known cases
- **Exact match with poe2db.tw** for tested scenarios (12 suffix groups for INT body armor)
- **Scalability concerns** - Each discovered discrepancy requires manual intervention

### Potential Future Issues
- **Other item types** may have similar unreported discrepancies
- **New game updates** could change mod availability
- **Maintenance burden** of tracking game vs PathOfBuilding differences

## Technical Solutions to Investigate

### Option 1: Enhanced Weight Parsing
Implement more sophisticated weight checking that considers:
- **Multi-category requirements** (item must satisfy ALL applicable categories)
- **Hierarchical category system** (body_armour + int_armour for INT body pieces)
- **Slot-specific overrides** built into the parsing logic

### Option 2: Alternative Data Sources
- **Direct game data mining** if available
- **poe2db.tw API integration** for validation
- **Community-maintained modifier databases**

### Option 3: Hybrid Approach
- **PathOfBuilding as primary source** for comprehensive coverage
- **Game knowledge database** for overrides and corrections
- **Automated discrepancy detection** comparing multiple sources

## Files Affected

### Core Files
- `backend/app/services/crafting/modifier_pool.py` - Filtering logic
- `Poe2-DB-Scraper/parse_pob_data.py` - Data parsing
- `backend/app/schemas/crafting.py` - Modifier model with `is_exclusive` field

### Data Files
- `backend/app/data/modifiers.json` - Final modifier database
- `Poe2-DB-Scraper/output/modifiers.json` - Parsed PathOfBuilding data

## Next Steps

### Short Term
1. **Document more cases** as they're discovered through user feedback
2. **Expand manual override system** to handle additional categories
3. **Add validation endpoints** to compare our data with known correct cases

### Long Term
1. **Research PathOfBuilding codebase** to understand intended weight logic
2. **Investigate game data extraction** for authoritative modifier sources
3. **Build automated testing** against known correct modifier sets

## Related Issues

### Energy Shield Mod Groups
- `energyshieldregeneration` - Recharge rate (helmets/gloves/boots only)
- `energyshielddelay` - Faster start (body armor + hybrids only)

### Other Potential Problem Areas
- **Weapon-specific mods** with complex category interactions
- **Attribute requirement variations** across item types
- **Essence/corruption exclusive modifiers** that may not be properly categorized

---

*Last Updated: 2025-01-25*
*Issue Status: Partially Resolved (workaround implemented)*