# POE2 Item Price Estimation - Research Document

## Executive Summary

Item price estimation for POE2 involves querying the official trade API to find similar items and deriving value from market listings. The key challenge is **mod normalization** - converting specific mods into generalized search criteria that find comparable items without being too restrictive.

---

## 1. Trade API Overview

### POE2 vs POE1 API Endpoints

POE2 uses a **separate API namespace** (`trade2`) from POE1:

| Function | POE1 | POE2 |
|----------|------|------|
| Search | `/api/trade/search/{league}` | `/api/trade2/search/poe2/{league}` |
| Fetch | `/api/trade/fetch/{hashes}` | `/api/trade2/fetch/{hashes}` |
| Stats | `/api/trade/data/stats` | `/api/trade2/data/stats` |
| Items | `/api/trade/data/items` | `/api/trade2/data/items` |
| Leagues | `/api/trade/data/leagues` | `/api/trade2/data/leagues` |

### Current POE2 Leagues
- `Fate of the Vaal` (current challenge league)
- `HC Fate of the Vaal`
- `Standard` / `Hardcore`

### Rate Limits

GGG uses dynamic rate limits via response headers:
```
X-Rate-Limit-Policy: trade-search
X-Rate-Limit-Rules: ip,account
X-Rate-Limit-Ip: 12:4:60,45:12:300
```

Format: `requests:period_seconds:timeout_seconds`

---

## 2. Search Query Structure

### Basic Query Format

```json
{
  "query": {
    "status": {"option": "online"},
    "stats": [{
      "type": "and",
      "filters": [
        {"id": "pseudo.pseudo_total_life", "value": {"min": 50}},
        {"id": "pseudo.pseudo_total_elemental_resistance", "value": {"min": 60}}
      ]
    }],
    "filters": {
      "type_filters": {
        "filters": {
          "category": {"option": "armour.boots"}
        }
      }
    }
  },
  "sort": {"price": "asc"}
}
```

### Stat Filter Types

| Type | Purpose |
|------|---------|
| `and` | All filters must match |
| `not` | Exclude items matching these filters |
| `if` | Conditional filters |
| `count` | Match items with N of the specified mods |
| `weight` | Weighted sum scoring (advanced) |

### Weighted Sum Example

Weighted sum is powerful for finding "good enough" items across multiple stats:

```json
{
  "type": "weight",
  "filters": [
    {"id": "pseudo.pseudo_total_fire_resistance", "value": {"weight": 1}},
    {"id": "pseudo.pseudo_total_cold_resistance", "value": {"weight": 1}},
    {"id": "pseudo.pseudo_total_lightning_resistance", "value": {"weight": 1}}
  ],
  "value": {"min": 80}
}
```

This finds items where the **sum** of (fire + cold + lightning resistance) >= 80, regardless of which specific resistances are present.

---

## 3. POE2 Pseudo Mods (Complete List)

POE2 has **34 pseudo mods** for normalized searching. These combine values from all sources (explicit, implicit, enchant, etc):

### Resistances
```
pseudo.pseudo_total_fire_resistance        +#% total to Fire Resistance
pseudo.pseudo_total_cold_resistance        +#% total to Cold Resistance
pseudo.pseudo_total_lightning_resistance   +#% total to Lightning Resistance
pseudo.pseudo_total_elemental_resistance   +#% total Elemental Resistance
pseudo.pseudo_total_chaos_resistance       +#% total to Chaos Resistance
pseudo.pseudo_total_resistance             +#% total Resistance
pseudo.pseudo_count_elemental_resistances  # total Elemental Resistances
pseudo.pseudo_count_resistances            # total Resistances
pseudo.pseudo_total_all_elemental_resistances +#% total to all Elemental Resistances
```

### Attributes
```
pseudo.pseudo_total_strength       +# total to Strength
pseudo.pseudo_total_dexterity      +# total to Dexterity
pseudo.pseudo_total_intelligence   +# total to Intelligence
pseudo.pseudo_total_all_attributes +# total to all Attributes
pseudo.pseudo_total_attributes     +# total to Attributes
```

### Defenses
```
pseudo.pseudo_total_life                  +# total maximum Life
pseudo.pseudo_total_mana                  +# total maximum Mana
pseudo.pseudo_total_energy_shield         +# total maximum Energy Shield
pseudo.pseudo_increased_energy_shield     #% total increased maximum Energy Shield
pseudo.pseudo_increased_movement_speed    #% increased Movement Speed
```

### Mod Counts (for crafting potential)
```
pseudo.pseudo_number_of_prefix_mods       # Prefix Modifiers
pseudo.pseudo_number_of_suffix_mods       # Suffix Modifiers
pseudo.pseudo_number_of_affix_mods        # Modifiers
pseudo.pseudo_number_of_empty_prefix_mods # Empty Prefix Modifiers
pseudo.pseudo_number_of_empty_suffix_mods # Empty Suffix Modifiers
pseudo.pseudo_number_of_empty_affix_mods  # Empty Modifiers
pseudo.pseudo_number_of_fractured_mods    # Fractured Modifiers
```

### POE2 Specific (Desecrated)
```
pseudo.pseudo_number_of_desecrated_prefix_mods   # Desecrated Prefix Modifiers
pseudo.pseudo_number_of_desecrated_suffix_mods   # Desecrated Suffix Modifiers
pseudo.pseudo_number_of_desecrated_mods          # Desecrated Modifiers
pseudo.pseudo_number_of_unrevealed_prefix_mods   # Unrevealed Prefix Modifiers
pseudo.pseudo_number_of_unrevealed_suffix_mods   # Unrevealed Suffix Modifiers
pseudo.pseudo_number_of_unrevealed_mods          # Unrevealed Modifiers
```

---

## 4. Existing Tools & How They Work

### Exiled Exchange 2 (Open Source)
- **GitHub**: https://github.com/Kvan7/Exiled-Exchange-2
- **Tech Stack**: Electron, TypeScript, Vue, Python
- **Approach**: Reads item data from clipboard, generates trade queries, displays overlay
- Fork of Awakened PoE Trade for POE2

### Awakened PoE Trade (POE1, Reference)
- **GitHub**: https://github.com/SnosMe/awakened-poe-trade
- **Tech Stack**: Electron, TypeScript, Vue
- **Key Features**:
  - Parses item text from Ctrl+C
  - Groups related stats into pseudo mods
  - Auto-adjusts min values (slightly below actual roll)
  - Uses poeprices.info ML predictions for rares

### Xiletrade
- **GitHub**: https://github.com/maxensas/xiletrade
- **Tech Stack**: C#, WPF, .NET
- **Features**: Fast price checking, respects rate limits

### POE2K / POE2 Overlay
- Commercial/Overwolf apps
- "Smart percentage-based price checking" - broadens searches when exact matches don't exist
- Uses transparent overlay windows

---

## 5. Price Estimation Strategies

### Strategy 1: Direct Mod Matching (Basic)

Search for items with the exact mods on your item, with slightly relaxed values:

```python
def generate_basic_query(item):
    filters = []
    for mod in item.explicit_mods:
        # Use 80-90% of actual value as minimum
        min_val = mod.value * 0.85
        filters.append({
            "id": mod.trade_stat_id,
            "value": {"min": min_val}
        })
    return {"type": "and", "filters": filters}
```

**Pros**: Simple, finds exact comparables
**Cons**: Too restrictive, may return 0 results

### Strategy 2: Pseudo Mod Normalization (Recommended)

Convert specific mods to pseudo equivalents:

```python
# Instead of searching for:
#   +35% Fire Resistance
#   +28% Cold Resistance
#   +22% Lightning Resistance

# Search for:
#   +85% total Elemental Resistance (sum of all three)
```

**Mod Groupings**:
| Specific Mods | Pseudo Equivalent |
|--------------|-------------------|
| Fire + Cold + Lightning Res | `pseudo_total_elemental_resistance` |
| Str + Dex + Int | `pseudo_total_attributes` |
| +Life from all sources | `pseudo_total_life` |

### Strategy 3: Weighted Sum Scoring

For items with multiple valuable stats, use weighted search:

```python
def generate_weighted_query(item, weights):
    filters = []
    for mod in item.explicit_mods:
        if mod.category in weights:
            filters.append({
                "id": get_pseudo_id(mod),
                "value": {"weight": weights[mod.category]}
            })

    # Calculate target score (e.g., 70% of max possible)
    target_score = calculate_item_score(item, weights) * 0.7

    return {
        "type": "weight",
        "filters": filters,
        "value": {"min": target_score}
    }
```

### Strategy 4: Progressive Relaxation

Start with strict criteria and progressively relax until finding sufficient results:

```python
async def find_price(item):
    for strictness in [1.0, 0.9, 0.8, 0.7]:
        query = generate_query(item, strictness)
        results = await search_trade(query)

        if len(results) >= 5:
            return calculate_median_price(results)

    return None  # Unable to price
```

### Strategy 5: ML-Based Prediction

poeprices.info provides ML predictions for rare items:
- Analyzes mod combinations statistically
- Predicts based on historical sales data
- Used by Awakened PoE Trade as fallback

---

## 6. Implementation Considerations

### Rate Limiting

```python
class RateLimiter:
    def __init__(self):
        self.requests = []
        self.limit = 10  # requests per window
        self.window = 60  # seconds

    async def wait_if_needed(self):
        now = time.time()
        self.requests = [r for r in self.requests if now - r < self.window]

        if len(self.requests) >= self.limit:
            wait_time = self.requests[0] + self.window - now
            await asyncio.sleep(wait_time)

        self.requests.append(now)
```

### Caching

- Cache search results for identical queries
- TTL: 5-10 minutes (prices change slowly)
- Consider caching at mod-combination level

### Mod ID Mapping

Need to map our internal mod representation to trade API stat IDs:

```python
MOD_TO_TRADE_ID = {
    "# to maximum Life": "explicit.stat_3299347043",
    "#% to Fire Resistance": "explicit.stat_3372524247",
    # ... or use pseudo equivalents
}
```

The `/api/trade2/data/stats` endpoint provides the complete mapping.

---

## 7. Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Item Price Estimator                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Mod        │  │  Query      │  │  Price              │ │
│  │  Normalizer │──│  Builder    │──│  Calculator         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│         │                │                    │             │
│         ▼                ▼                    ▼             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Pseudo     │  │  Trade API  │  │  Statistics         │ │
│  │  Mapping    │  │  Client     │  │  (median, avg)      │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Caching & Rate Limiting                   │
└─────────────────────────────────────────────────────────────┘
```

### Components

1. **Mod Normalizer**: Converts item mods to pseudo equivalents
2. **Query Builder**: Generates trade API queries with relaxation
3. **Price Calculator**: Analyzes results, calculates statistics
4. **Trade API Client**: Handles requests, rate limiting, caching

---

## 8. Next Steps

1. **Build mod-to-pseudo mapping** from our mod database
2. **Implement Trade API client** with rate limiting
3. **Create query builder** with progressive relaxation
4. **Add price calculation** (median of first N results)
5. **Integrate with crafting simulator** UI

---

## 9. Resources

- [POE Trade Site](https://www.pathofexile.com/trade2/search/poe2/Fate%20of%20the%20Vaal)
- [Exiled Exchange 2](https://github.com/Kvan7/Exiled-Exchange-2)
- [Awakened PoE Trade](https://github.com/SnosMe/awakened-poe-trade)
- [Xiletrade](https://github.com/maxensas/xiletrade)
- [poeprices.info](https://poeprices.info/) - ML price predictions
