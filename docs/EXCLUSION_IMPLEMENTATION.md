# Exclusion Groups Implementation Summary

## Overview
Implemented a comprehensive exclusion system to prevent conflicting modifiers from being added to items during crafting. The system uses pattern-based rules from `exclusion_groups.json` to automatically filter available mods.

## Backend Implementation

### 1. Exclusion Service (`backend/app/services/crafting/exclusion_service.py`)
**Purpose**: Core service for handling mod exclusion validation

**Key Features**:
- Loads exclusion rules from `exclusion_groups.json`
- Pattern matching using regex (handles `{}` placeholders for numeric values)
- Respects item-specific rules (e.g., wand-only, bow-only exclusions)
- Deduplicates conflicts from multiple matching rules

**Main Methods**:
```python
# Check if a mod can be added
can_add, reason = exclusion_service.can_add_mod(mod, existing_mods, item_category, mod_type)

# Get list of conflicting mods
conflicts = exclusion_service.get_conflicting_mods(mod, existing_mods, item_category, mod_type)

# Filter available mods to remove conflicts
filtered = exclusion_service.filter_available_mods(available_mods, existing_mods, item_category, mod_type)
```

### 2. Modifier Pool Integration (`backend/app/services/crafting/modifier_pool.py`)
**Changes Made**:
- Integrated exclusion service into `_filter_eligible_mods()`
- Integrated into `get_all_mods_for_category()` for UI display
- Automatically filters conflicting mods when:
  - Rolling random modifiers (Chaos Orb, Regal Orb, etc.)
  - Getting available mods for display

### 3. API Endpoint (`backend/app/api/v1/crafting.py`)
**New Endpoint**: `POST /api/v1/crafting/check-mod-conflicts`

**Request**:
```json
{
  "item": CraftableItem,
  "mod": ItemModifier,
  "mod_type": "prefix" | "suffix"
}
```

**Response**:
```json
{
  "can_add": true|false,
  "conflicts": [array of conflicting mods],
  "reason": "Conflicts with existing mod(s): '+30 to Strength and Dexterity'"
}
```

## Exclusion Rules (`backend/source_data/exclusion_groups.json`)

### Global Rules
Rules that apply to all item types (unless restricted by `applicable_items`):

1. **Hybrid Attributes**
   - `+Str and Dex` conflicts with `+Str and Int`
   - `+Dex and Int` conflicts with `+Int`

2. **Skill Gem Levels**
   - All skill level mods conflict with each other
   - Examples: Melee, Spell, Projectile, Minion, Attack, all Skills
   - Elemental-specific spell levels: Cold, Fire, Lightning, Physical, Chaos

3. **Flask Mechanics**
   - Recovery amount variations
   - Recovery rate vs instant recovery
   - Charge gain mechanics
   - Life vs Mana flask recovery rates
   - Life vs Mana charge generation

4. **Critical Modifiers**
   - Critical damage bonus variations
   - Critical hit chance variations

5. **Spell Damage**
   - Base spell damage vs variations (per Life, per Mana, with Life cost)
   - Invocated spells vs regular spell damage
   - Minion + spell damage hybrids

6. **Attack Speed**
   - Base attack speed vs companion variations

7. **Other Global Rules**
   - Dodge roll mods
   - Thorns damage types
   - Projectile damage variations
   - Maximum resistances
   - Parried debuff variations
   - Break armour mechanics
   - Hindered enemy damage increases
   - Combo recovery (Life vs Mana)

### Weapon-Specific Rules

**Wands**:
- Fire Damage vs Elemental Damage

**Bows**:
- "Fire 2 additional Arrows" vs "Fire an additional Arrow"

**Crossbows**:
- Reload mechanics (immediate vs speed)
- "Loads 2 additional bolts" vs "Loads an additional bolt"

**One-Handed Melee** (Flail, Axe, Sword):
- Extra damage as element (Cold/Fire/Lightning/Physical)

**Two-Handed Weapons** (Spear, Bow, Crossbow, Two-Hand Axe, Warstaff):
- Extra damage as element (Cold/Fire/Lightning/Physical)

**Maces**:
- Physical damage vs Physical damage with attack speed penalty

## Testing

### Unit Tests (`backend/tests/test_exclusion_service.py`)
Comprehensive test suite with **32 tests** covering:

**Test Categories**:
- `TestHybridAttributeExclusions` - 2 tests
- `TestSkillLevelExclusions` - 3 tests
- `TestWeaponSpecificExclusions` - 5 tests
- `TestFlaskExclusions` - 4 tests
- `TestCriticalModExclusions` - 2 tests
- `TestSpellDamageExclusions` - 3 tests
- `TestProjectileExclusions` - 2 tests
- `TestCanAddMod` - 2 tests
- `TestFilterAvailableMods` - 2 tests
- `TestPatternMatching` - 4 tests
- `TestComplexScenarios` - 3 tests

**Test Status**: ✅ All 32 tests passing

**Run Tests**:
```bash
cd backend
venv/Scripts/python -m pytest tests/test_exclusion_service.py -v
```

## How It Works

### Example 1: Hybrid Attributes
```python
# User has item with: "+30 to Strength and Dexterity"
# System automatically filters out:
# - "+25 to Strength and Intelligence"
# - Any other Str+Int hybrid mod
```

### Example 2: Wand-Specific
```python
# Wand with "25% increased Fire Damage"
# System filters out:
# - "(74-89)% increased Elemental Damage"
#
# But on an Amulet, both can coexist (rule doesn't apply)
```

### Example 3: Skill Levels
```python
# Item with "+2 to Level of all Melee Skills"
# System filters out:
# - "+1 to Level of all Spell Skills"
# - "+1 to Level of all Minion Skills"
# - "+1 to Level of all Skills"
# - Any other skill level mod
```

## Frontend Integration (TODO)

### Suggested Enhancements:

1. **Visual Indicators in Mod Browser**
   ```tsx
   // Show grayed-out mods with strikethrough
   <ModRow
     mod={mod}
     isExcluded={checkConflict(mod)}
     conflictReason="Conflicts with +2 Melee Skills"
   />
   ```

2. **Hover Tooltips**
   ```tsx
   <Tooltip content={
     `This mod cannot be added because it conflicts with:\n` +
     conflicts.map(c => `- ${c.stat_text}`).join('\n')
   }>
     <ModName className="text-gray-500">
       {mod.stat_text}
     </ModName>
   </Tooltip>
   ```

3. **Warning Before Manual Add**
   ```tsx
   if (!canAdd) {
     showConfirm({
       title: "Mod Conflict",
       message: reason,
       type: "error"
     });
   }
   ```

4. **Filter Options**
   ```tsx
   <Checkbox
     label="Hide conflicting mods"
     checked={hideConflicts}
     onChange={setHideConflicts}
   />
   ```

## Pattern Matching Details

### Placeholder Syntax:
- `{}` - Matches any numeric value or range
- `({}-{})` - Matches numeric ranges like (10-20)

### Examples:
```
Pattern: "+{} to Strength"
Matches: "+50 to Strength", "+30 to Strength"

Pattern: "({}-{})% increased Elemental Damage"
Matches: "(74-89)% increased Elemental Damage"

Pattern: "{} to {} Physical Thorns damage"
Matches: "5 to 10 Physical Thorns damage"
```

## Benefits

1. **Prevents Invalid Items**
   - No more impossible mod combinations
   - Matches actual game behavior

2. **Better User Experience**
   - Clear feedback on why mods can't be added
   - Automatic filtering of invalid options

3. **Accurate Crafting Simulation**
   - Simulations match real game mechanics
   - Predictable outcomes

4. **Maintainable**
   - Rules stored in JSON (easy to update)
   - Centralized exclusion logic
   - Well-tested with comprehensive test suite

## Adding New Exclusion Rules

To add a new exclusion rule, edit `backend/source_data/exclusion_groups.json`:

```json
{
  "description": "Your rule description",
  "applicable_items": ["wand", "sceptre"],  // Optional, applies to all if omitted
  "patterns": [
    "Pattern 1 with {} placeholders",
    "Pattern 2 with {} placeholders"
  ]
}
```

Then run the tests to ensure it works:
```bash
pytest tests/test_exclusion_service.py -v
```

## Files Modified/Created

### Created:
- `backend/app/services/crafting/exclusion_service.py`
- `backend/tests/test_exclusion_service.py`
- `EXCLUSION_IMPLEMENTATION.md` (this file)

### Modified:
- `backend/app/services/crafting/modifier_pool.py`
- `backend/app/api/v1/crafting.py`
- `backend/source_data/exclusion_groups.json`

## Performance

- Exclusion rules loaded once at startup
- Pattern matching uses compiled regex (fast)
- Deduplication prevents duplicate checks
- Minimal overhead during crafting simulation

## Future Enhancements

1. Add more exclusion rules as discovered
2. Frontend visual indicators
3. Mod suggestion system ("You might want X instead of Y")
4. Analytics on common conflicts
5. Rule verification tool (find items that violate rules)
