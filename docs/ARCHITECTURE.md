# Architecture Overview

This document provides a high-level overview of the POE2-PathOfCrafting system architecture.

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA SOURCES                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Path of Building 2     poe2db.tw        POE2 Trade API      poe.ninja     │
│  (Lua mod data)         (item bases)     (live listings)     (builds)      │
└────────┬────────────────────┬─────────────────┬──────────────────┬──────────┘
         │                    │                 │                  │
         ▼                    ▼                 │                  │
┌─────────────────────────────────────────┐     │                  │
│         Poe2-DB-Scraper (separate repo) │     │                  │
│  - parse_pob_data.py → ModItem.json     │     │                  │
│  - parse_bases.py → Bases/*.json        │     │                  │
└────────────────┬────────────────────────┘     │                  │
                 │ (manual copy to source_data) │                  │
                 ▼                              ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND (FastAPI)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  source_data/                    services/crafting/                          │
│  ├── pob-data/                   ├── pob_data_loader.py  ← loads mods       │
│  │   ├── ModItem.json            ├── modifier_pool.py    ← filters mods     │
│  │   ├── Essence.json            ├── mechanics.py        ← crafting logic   │
│  │   └── Bases/                  ├── simulator.py        ← orchestrator     │
│  ├── currency_configs.json       ├── unified_factory.py  ← creates mechs    │
│  ├── omens.json                  └── exclusion_service.py← mod conflicts    │
│  ├── desecration_bones.json                                                  │
│  └── weights.csv                 services/market/                            │
│                                  ├── trade_client.py     ← POE2 Trade API   │
│                                  ├── item_pricer.py      ← price estimation │
│                                  └── providers/poe2scout.py                  │
│                                                                              │
│  api/v1/                         services/                                   │
│  ├── crafting.py  ─────────────► item_parser.py    ← Ctrl+C item parsing   │
│  ├── market.py                   item_converter.py ← parser → CraftableItem│
│  └── items.py                                                                │
│                                                                              │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ REST API
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FRONTEND (React + TypeScript)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  pages/                          components/                                 │
│  ├── GridCraftingSimulator.tsx   ├── panels/                                │
│  ├── ItemParser.tsx              │   ├── ItemDisplayPanel.tsx               │
│  └── BuildBrowser.tsx            │   ├── CraftingControlsPanel.tsx          │
│                                  │   └── HistoryPanel.tsx                   │
│  services/                       ├── poe2/                                   │
│  ├── crafting-api.ts             │   ├── PoE2ItemFrame.tsx  ← item styling  │
│  └── market-api.ts               │   └── PoE2ModLine.tsx    ← mod display   │
│                                  └── UnifiedCurrencyStash.tsx               │
│  types/                                                                      │
│  └── crafting.ts  ← mirrors backend schemas                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Concepts

### 1. PoE2 UI Styling

The `components/poe2/` directory contains reusable components that mimic the in-game item display:

```
components/poe2/
├── PoE2ItemFrame.tsx    ← Item tooltip container with rarity-based styling
├── PoE2ItemFrame.css    ← Rarity colors, borders, backgrounds
├── PoE2ModLine.tsx      ← Single mod line with tier badge
├── PoE2ModLine.css      ← Prefix/suffix colors, fractured/desecrated styling
└── PoE2TradeListingPreview.tsx  ← Trade listing item preview
```

**PoE2ItemFrame**: Wraps item content with proper header, borders, and rarity styling.
```tsx
<PoE2ItemFrame rarity="rare" itemName="Doom Knuckle" itemBase="Expert Runic Gauntlets">
  <PoE2ModLine mod={lifeMod} />
  <PoE2ModLine mod={resistMod} />
</PoE2ItemFrame>
```

**PoE2ModLine**: Displays a single modifier with:
- Color coding: blue (prefix), green (suffix), cyan (implicit)
- Special states: fractured (gold), desecrated (purple), unrevealed (dim)
- Tier badge showing T1-T7
- Value substitution: replaces `#` with actual values

**Rarity colors** (matching in-game):
| Rarity | Color |
|--------|-------|
| Normal | White |
| Magic | Blue (#8888FF) |
| Rare | Yellow (#FFFF77) |
| Unique | Orange (#AF6025) |

### 2. Modifier System

**Modifiers (Mods)** are stat bonuses on items. Each mod has:
- `stat_text`: Display text with `#` placeholders (e.g., `"+# to Maximum Life"`)
- `mod_group`: Prevents stacking (only one mod per group on an item)
- `mod_type`: `prefix` or `suffix` (items have max 3 of each)
- `tier`: Quality level (T1 is best)
- `weight`: Spawn probability
- `applicable_items`: Which item types can roll this mod

**Data flow:**
```
POB Lua files → Scraper → ModItem.json → pob_data_loader.py → ModifierPool
```

### 3. Crafting Mechanics

Each currency/essence has a **Mechanic** class that implements:
- `can_apply(item)` → validation
- `apply(item, modifier_pool)` → execute craft

**Key mechanics:**
| Currency | Effect |
|----------|--------|
| Transmutation | Normal → Magic (1-2 mods) |
| Alchemy | Normal → Rare (4-6 mods) |
| Chaos | Reroll Rare item |
| Exalted | Add 1 mod to Rare |
| Annulment | Remove 1 random mod |
| Essence | Guarantee specific mod + random mods |

**Omens** wrap mechanics to modify behavior (e.g., "Omen of Sinistral" forces prefix removal).

### 4. Mod Exclusions

Some mods cannot appear together. Handled by:
- `exclusion_groups.json`: Patterns that conflict
- `ExclusionService`: Filters available mods based on existing mods

Example: Item with `+# to Strength` cannot also roll `+# to Strength and Dexterity`.

### 5. Item Parsing

Users paste items from game (Ctrl+C). Two formats:
- **Simple**: Just mod text
- **Detailed**: Includes tier ranges like `+111(85-123) to Accuracy`

`ItemParser` extracts mods → `ItemConverter` matches to database mods → `CraftableItem`

### 6. Price Estimation

```
CraftableItem → build trade query → POE2 Trade API → parse listings → statistics
```

Features:
- Mod matching with `#` placeholder normalization
- Hybrid mod detection (one mod with multiple stat lines)
- Pseudo stats (total resistances, etc.)
- Rarity from `frameType` field

## Data Files

| File | Purpose |
|------|---------|
| `ModItem.json` | All item mods from POB (650K+ lines) |
| `Essence.json` | Essence effects per item type |
| `currency_configs.json` | Currency mechanics configuration |
| `omens.json` | Omen effects and rules |
| `weights.csv` | Mod spawn weights per item category |
| `exclusion_groups.json` | Mod conflict patterns |

## Key Design Decisions

1. **No database**: All data loaded from JSON files at startup. Simpler deployment, faster iteration.

2. **POB as source of truth**: Path of Building's data is community-maintained and accurate.

3. **`#` placeholders**: Trade API uses `#` for numeric values. We normalize all stat text to this format.

4. **Mechanics as classes**: Each crafting currency is a class implementing a common interface. Easy to add new currencies.

5. **Separation of concerns**:
   - `ModifierPool`: What mods CAN roll
   - `Mechanic`: HOW crafting works
   - `Simulator`: Orchestrates the craft

## Common Tasks

### Adding a new currency
1. Add config to `currency_configs.json`
2. Create mechanic class in `mechanics.py` (or use existing)
3. Register in `unified_factory.py`

### Updating mod data
1. Run scraper in `Poe2-DB-Scraper` repo
2. Copy output to `backend/source_data/pob-data/`
3. Restart backend

### Debugging mod matching
- Check `stat_text` uses `#` not `{}`
- Verify `applicable_items` includes the item category
- Check `mod_group` conflicts in exclusion_groups.json
