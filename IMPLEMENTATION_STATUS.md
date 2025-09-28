# Implementation Status & Roadmap

## Current Status: **Functional MVP (30% Complete)**

### ✅ Completed (Core Engine)
- [x] Modular crafting engine architecture
- [x] Item state management system
- [x] 7 basic currencies (Normal tier only)
- [x] Weighted modifier selection
- [x] API endpoints for simulation
- [x] Frontend crafting simulator UI
- [x] Real-time item updates
- [x] Crafting history tracking

### ⚠️ Partially Complete
- [ ] **Modifier Database** - Only 9 sample mods (need 100s)
- [ ] **Currency Tiers** - Missing Greater & Perfect variants
- [ ] **Mod Weights** - Using placeholder values

### ❌ Not Implemented
- [ ] **Essences** - Guaranteed mod crafting
- [ ] **Omens** - Meta-crafting modifiers
- [ ] **Desecration** - Endgame crafting
- [ ] **Catalysts** - Jewelry quality
- [ ] **Recombinators** - Item merging
- [ ] **poe2db Scraper** - Real data source
- [ ] **Multi-step Planner** - Goal-based crafting paths
- [ ] **LLM Integration** - Natural language interface
- [ ] **Probability Calculator** - Expected cost analysis

---

## Priority 1: Currency Tiers (High Impact)

### Greater & Perfect Variants

**Implementation Plan:**

1. **Extend Currency Classes**
```python
class GreaterExaltedOrb(CraftingCurrency):
    def __init__(self) -> None:
        super().__init__("Greater Exalted Orb", "rare")
        self.min_mod_level = 35

    def apply(self, item, modifier_pool):
        # Filter mods: required_ilvl >= 35
        # Apply exalt logic with filtered pool
```

2. **Update ModifierPool Filtering**
```python
def roll_random_modifier(self, mod_type, item_category, item_level, min_mod_level=None):
    # Add min_mod_level filter
    if min_mod_level:
        eligible = [m for m in eligible if m.required_ilvl >= min_mod_level]
```

3. **Register in CurrencyFactory**
```python
_currencies = {
    "Orb of Transmutation": OrbOfTransmutation,
    "Greater Orb of Transmutation": GreaterOrbOfTransmutation,
    "Perfect Orb of Transmutation": PerfectOrbOfTransmutation,
    # ... etc for all currencies
}
```

**Effort:** ~4 hours
**Impact:** Makes crafting realistic for endgame items

---

## Priority 2: Real Modifier Database (Critical)

### Current: 9 Sample Mods
### Need: 200-500+ Real Mods

**Data Required Per Mod:**
- Name (e.g., "Healthy", "of the Drake")
- Type (prefix/suffix)
- Tier (T1-T7)
- Stat text ("+{} to maximum Life")
- Min/Max values
- Required item level
- **Weight** (spawn probability) - CRITICAL
- Applicable item types
- Mod group (only one per group)

**Sources:**
1. **poe2db.tw** - Scrape modifier tables
2. **RePoE** - Existing PoE1 data extractor (may work for PoE2)
3. **Manual curation** - Community data

**Implementation Plan:**
1. Build web scraper for poe2db
2. Parse HTML tables
3. Store in database
4. Load into ModifierPool at startup

**Effort:** ~8-12 hours
**Impact:** Enables realistic crafting simulations

---

## Priority 3: Essences (High Value)

### Guaranteed Modifier Crafting

**Types:**
- Regular Essences (add mod)
- Greater Essences (add mod + upgrade to Rare)
- Perfect Essences (higher tier mod)

**Implementation:**
```python
class EssenceOfTheBody(CraftingCurrency):
    def __init__(self, tier="regular"):
        super().__init__("Essence of the Body", "uncommon")
        self.guaranteed_mod_group = "life"
        self.tier = tier
        self.min_mod_tier = 3 if tier == "regular" else 2 if tier == "greater" else 1

    def apply(self, item, modifier_pool):
        # Force select life mod of appropriate tier
        life_mods = modifier_pool.get_mods_by_group("life")
        mod = [m for m in life_mods if m.tier <= self.min_mod_tier][0]
        # Apply mod
```

**Effort:** ~6 hours
**Impact:** Deterministic crafting strategies

---

## Priority 4: Multi-Step Planner

### Goal-Based Crafting Paths

**User Input:**
```
Start: White Sage's Robe (ilvl 70)
Goal: +80 Life, +30% Fire Res, +30% Cold Res
```

**Output:**
```
Step 1: Use Essence of the Body (Greater) → Life guaranteed
Step 2: Use Regal Orb → Upgrade to Rare, add random mod
Step 3: Use Greater Exalted Orb → Add mod (35%+ chance for resist)
Step 4: Use Greater Exalted Orb → Add mod
Step 5: Use Chaos Orb if bad mods
Expected Cost: 150 chaos equivalent
Success Probability: 15%
```

**Algorithm:**
- A* pathfinding through item states
- Evaluate cost vs probability
- Consider alternative strategies

**Effort:** ~10-15 hours
**Impact:** Core value proposition of the tool

---

## Priority 5: LLM Integration

### Natural Language Interface

**Features:**
- Parse user goals: "I want a life + resist chest"
- Explain strategies in plain English
- Suggest alternatives based on budget
- Answer questions: "Why use Essence instead of Alchemy?"

**Implementation:**
- Use Claude/GPT-4 for reasoning
- Ground with crafting engine calculations
- Validate suggestions against rules

**Effort:** ~6 hours
**Impact:** User-friendly experience

---

## Priority 6: Data Scraper

### poe2db.tw Web Scraper

**Components:**
1. **Modifier Scraper**
   - Parse mod tables
   - Extract weights
   - Store in database

2. **Currency Scraper**
   - Parse currency pages
   - Extract effects

3. **Base Item Scraper**
   - Parse item bases
   - Extract stats

**Tech Stack:**
- BeautifulSoup or Scrapy
- Respectful rate limiting
- Caching to avoid repeated scrapes

**Effort:** ~8-12 hours
**Impact:** Foundation for accurate simulation

---

## Effort Estimates

| Priority | Feature | Effort | Impact | Status |
|----------|---------|--------|--------|--------|
| P1 | Currency Tiers | 4h | High | Not Started |
| P2 | Real Mod Database | 8-12h | Critical | Not Started |
| P3 | Essences | 6h | High | Not Started |
| P4 | Multi-Step Planner | 10-15h | Critical | Not Started |
| P5 | LLM Integration | 6h | Medium | Not Started |
| P6 | poe2db Scraper | 8-12h | Critical | Not Started |

**Total Effort to 80% Complete:** ~40-55 hours

---

## What Works Right Now

The **current MVP** is fully functional for:
- Basic crafting experimentation
- Understanding currency mechanics
- Testing item state transitions
- Learning crafting workflows

**Limitations:**
- Small mod pool (not realistic)
- Only Normal-tier currencies
- No deterministic crafting (essences)
- No multi-step planning

**Best Use Cases:**
- Educational tool
- Proof of concept
- Architecture demonstration
- Foundation for full implementation