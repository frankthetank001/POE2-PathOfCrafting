# PoE2 Crafting System Design

## Research Summary

### Item Modifier System

**Modifier Types:**
1. **Implicit Modifiers**
   - Built into base item type
   - Always present regardless of rarity
   - Cannot be changed by most currency (except Vaal Orb)
   - Example: Topaz Ring always has Lightning Resistance

2. **Explicit Modifiers**
   - Affixes added through crafting
   - Two types: **Prefixes** and **Suffixes**
   - Can be modified via crafting

**Modifier Limits by Rarity:**
- **Magic Items**: Max 2 explicit mods (1 prefix + 1 suffix)
- **Rare Items**: Max 6 explicit mods (3 prefixes + 3 suffixes)

**Prefix Types** (Defensive/Offensive):
- Flat or % increased armor, evasion, energy shield
- Maximum life, mana
- Flat or % physical/elemental/chaos damage

**Suffix Types** (Utility/Speed):
- Elemental & chaos resistances
- Attack speed, cast speed
- Critical strike chance/multiplier
- Attribute requirements

---

## Crafting Currencies & Methods

### Basic Currencies
1. **Orb of Transmutation**
   - Normal → Magic (adds 1-2 mods)
   - Cost: Common

2. **Orb of Augmentation**
   - Adds 1 mod to Magic item (if has room)
   - Cost: Common

3. **Orb of Alchemy**
   - Normal → Rare (adds 4-6 mods)
   - Cost: Uncommon (rarer in PoE2 than PoE1)

4. **Regal Orb**
   - Magic → Rare (keeps existing mods, adds 1 new)
   - Cost: Uncommon
   - Use Case: Preserve good Magic item mods

5. **Exalted Orb**
   - Adds 1 random mod to Rare item
   - Cost: Rare (more common in endgame)
   - Use Case: Fill empty affix slots

6. **Chaos Orb**
   - Replaces 1 random mod on Rare item
   - Cost: Rare
   - Use Case: Re-roll bad mods iteratively

7. **Divine Orb**
   - Randomizes numerical values of existing mods
   - Cost: Very Rare
   - Use Case: Perfect rolls on good mods

8. **Vaal Orb**
   - Unpredictably corrupts item (can brick or upgrade)
   - Cost: Rare
   - Use Case: High-risk/high-reward gambles

### Advanced Crafting Systems

#### Essences
- **Purpose**: Add specific guaranteed modifier to Magic item
- **Types**:
  - Regular Essences (add mod)
  - Greater Essences (add mod + upgrade Magic → Rare)
  - Perfect Essences (higher tier guaranteed mods)
- **Examples**:
  - Essence of the Body → Life mod
  - Essence of the Mind → Mana mod
  - Essence of Flame/Ice/Electricity → Elemental mods

#### Omens
- **Purpose**: Meta-craft - modify how currency orbs work
- **Use Case**: Change probability outcomes or behavior
- **Example**: Omen that makes Exalted Orb more likely to hit specific mod type

#### Desecration (PoE2 New Mechanic)
- **Purpose**: Special crafting method for endgame
- **Mechanism**: Adds "Desecrated Modifiers" (likely different mod pool)

#### Catalysts
- **Purpose**: Add Quality to jewelry (increases mod values)
- **Use Case**: Boost resistances or stats on rings/amulets

#### Soul Cores
- **Purpose**: Powerful socketed items (Rune replacements)
- **Use Case**: Add special modifiers via sockets

#### Recombinators
- **Purpose**: Merge modifiers from two items into one
- **Use Case**: Combine best mods from two items (RNG-based)

---

## Key PoE2 Differences from PoE1

1. **No Orb of Scouring** - Cannot fully wipe item clean anymore
2. **Sockets on Gems** - Not on gear (simplified gearing)
3. **No Chromatic Orbs** - Socket colors handled differently
4. **Essences changed** - No longer reforge Rares, only modify Magic
5. **Philosophy**: "Items cannot be reset or fully re-rolled anymore"

This means **iterative crafting** is key - you work with what you have, not reset endlessly.

---

## Crafting Workflow Example

### Goal: Craft high-life, high-resist chest armor

**Strategy 1: Essence Start (Guaranteed Life)**
1. Get white (Normal) base item
2. Use **Essence of the Body** → Magic item with Life mod
3. Use **Orb of Augmentation** → Add 2nd mod (hope for resist)
4. Use **Regal Orb** → Upgrade to Rare, add 3rd mod
5. Use **Exalted Orbs** → Fill remaining 3 slots
6. Use **Chaos Orbs** → Replace bad mods iteratively
7. Use **Divine Orb** → Perfect numerical rolls

**Strategy 2: Alchemy Gamble**
1. Get white base item
2. Use **Orb of Alchemy** → Rare with 4-6 random mods
3. Evaluate result:
   - Good mods? → Exalt to fill, Divine to perfect
   - Bad mods? → Chaos Orb to replace iteratively
   - Terrible? → Start over or use as-is

**Strategy 3: Recombinator Merge**
1. Craft two separate items with desired mods
2. Use **Recombinator** → Merge best mods from both
3. Pray to RNG gods

---

## Data Requirements for Crafting Engine

To build the crafting theory-craft tool, we need:

### 1. **Base Items Database**
- Item types (body armour, helmets, weapons, etc.)
- Base stats (armor, evasion, ES, damage, attack speed)
- Implicit modifiers for each base
- Item level requirements
- Attribute requirements (Str/Dex/Int)

### 2. **Modifier Database**
- All prefix mods with:
  - Mod name
  - Mod tier (T1, T2, etc.)
  - Stat ranges (min-max)
  - Item level requirement
  - Weight (spawn probability)
  - Applicable item types
- All suffix mods (same structure)
- Desecrated mods
- Essence-guaranteed mods

### 3. **Crafting Currency Rules**
- Each currency type
- What it does (function)
- Input requirements (item rarity, mod count)
- Output possibilities
- Cost (relative rarity)

### 4. **Essence Database**
- Essence types
- Guaranteed mods per essence
- Tier levels (regular, greater, perfect)
- Applicable item types

### 5. **Advanced Mechanics**
- Omen types and effects
- Catalyst types
- Soul Core modifiers
- Recombinator rules

---

## Crafting Engine Architecture

### Core Components:

1. **Item State Manager**
   - Track current item state (rarity, mods, ilvl)
   - Validate possible actions

2. **Crafting Simulator**
   - Apply currency to item
   - Calculate probabilities
   - Simulate random outcomes

3. **Path Finder**
   - Given: Start item + Goal item
   - Output: Optimal crafting steps
   - Consider: Cost, success rate, alternative routes

4. **Probability Calculator**
   - Weighted mod selection
   - Multi-step success rates
   - Expected cost calculations

5. **Strategy Recommender**
   - Analyze goal mods
   - Suggest: Essence vs Alchemy vs Transmute-Regal
   - Recommend: Budget vs deterministic vs gamble

---

## Database Schema (PostgreSQL)

```sql
-- Base item types
CREATE TABLE base_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),  -- weapon, armour, jewelry
    subcategory VARCHAR(100),  -- body_armour, helmet, ring, etc.
    implicit_mod_id INT REFERENCES modifiers(id),
    base_stats JSONB,  -- armor, evasion, damage, etc.
    required_level INT,
    required_str INT,
    required_dex INT,
    required_int INT
);

-- All modifiers (prefix + suffix)
CREATE TABLE modifiers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    mod_type VARCHAR(20),  -- prefix, suffix, implicit, desecrated
    tier INT,  -- T1 = best, T7 = worst
    stat_text TEXT,  -- Display text with ranges
    stat_min FLOAT,
    stat_max FLOAT,
    required_ilvl INT,
    weight INT,  -- Spawn probability weight
    mod_group VARCHAR(100),  -- e.g., "life", "fire_resist"
    applicable_items TEXT[]  -- Array of item categories
);

-- Crafting currencies
CREATE TABLE currencies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    function TEXT,
    rarity VARCHAR(50),  -- common, uncommon, rare, very_rare
    rules JSONB  -- Detailed behavior rules
);

-- Essences
CREATE TABLE essences (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    essence_type VARCHAR(50),  -- regular, greater, perfect
    guaranteed_mod_id INT REFERENCES modifiers(id),
    upgrades_to_rare BOOLEAN DEFAULT FALSE,
    applicable_items TEXT[]
);

-- Crafting steps (for saved projects)
CREATE TABLE crafting_projects (
    id SERIAL PRIMARY KEY,
    user_id INT,  -- Optional for saved projects
    start_item JSONB,
    goal_item JSONB,
    steps JSONB[],
    estimated_cost JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Next Steps

1. **Scrape poe2db.tw** for:
   - Base items
   - All modifiers (prefix/suffix) with weights
   - Essence list

2. **Build Crafting Engine** with:
   - Item state class
   - Currency application functions
   - Probability calculator

3. **Create UI** for:
   - Item input (paste or select base)
   - Goal definition (select desired mods)
   - Step-by-step crafting guide
   - Probability/cost display

4. **LLM Integration** for:
   - Natural language goal parsing ("I want a +life +resist chest")
   - Strategy explanations in plain English
   - Alternative suggestions

---

## MVP Scope

**Phase 1: Basic Crafting Sim**
- Parse pasted item
- Select 1-2 goal mods
- Show: Best currency to use next
- Display: Success probability

**Phase 2: Multi-Step Planner**
- Define full goal item (6 mods)
- Calculate full crafting path
- Show: Step-by-step guide
- Display: Total expected cost

**Phase 3: LLM-Assisted**
- Natural language input
- Explain reasoning for each step
- Suggest alternatives based on budget

**Phase 4: Advanced**
- Omens integration
- Recombinator planning
- Profit crafting mode (expected value vs cost)