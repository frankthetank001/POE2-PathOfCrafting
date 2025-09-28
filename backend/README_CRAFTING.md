# Crafting Engine - Architecture Overview

## Modular Design

The crafting system is built with clean separation of concerns and modular components:

### 1. **Data Layer** (`app/models/`)
- `crafting.py` - SQLAlchemy database models
  - `BaseItem` - Item base types
  - `Modifier` - All prefix/suffix mods
  - `Currency` - Crafting currencies
  - `Essence` - Essence types
  - `CraftingProject` - Saved crafting plans

### 2. **Schema Layer** (`app/schemas/`)
- `crafting.py` - Pydantic models for validation
  - `CraftableItem` - Item state representation
  - `ItemModifier` - Individual mod representation
  - `CraftingStep` - Single crafting action
  - `CraftingPlan` - Full crafting strategy

### 3. **Service Layer** (`app/services/crafting/`)

#### **ItemStateManager** (`item_state.py`)
Manages item state and validates actions:
- `can_apply_currency()` - Check if currency can be used
- `add_modifier()` - Add mod to item
- `remove_modifier()` - Remove mod from item
- `upgrade_rarity()` - Change item rarity
- `get_open_affix_slots()` - Check available slots

#### **CraftingCurrency** (`currencies.py`)
Abstract base class with concrete implementations:
- `OrbOfTransmutation` - Normal → Magic
- `OrbOfAugmentation` - Add mod to Magic
- `OrbOfAlchemy` - Normal → Rare
- `RegalOrb` - Magic → Rare + add mod
- `ExaltedOrb` - Add mod to Rare
- `ChaosOrb` - Replace random mod
- `DivineOrb` - Reroll mod values

Each currency:
- Validates item state (`can_apply()`)
- Applies transformation (`apply()`)
- Returns success/failure + new item state

#### **ModifierPool** (`modifier_pool.py`)
Manages available modifiers and weighted selection:
- `roll_random_modifier()` - Weighted RNG mod selection
- `_filter_eligible_mods()` - Filter by ilvl, category, excluded groups
- `_weighted_random_choice()` - Probability-based selection
- `get_mods_by_group()` - Query mods by group
- `find_mod_by_name()` - Lookup specific mod

#### **CraftingSimulator** (`simulator.py`)
Orchestrates crafting operations:
- `simulate_currency()` - Apply currency to item
- `calculate_success_probability()` - Compute chance of hitting goal mod
- `get_available_currencies()` - List valid currencies for item state
- `_get_default_modifiers()` - Bootstrap with sample mod pool

### 4. **API Layer** (`app/api/v1/`)
- `crafting.py` - REST endpoints
  - `GET /crafting/currencies` - List all currencies
  - `POST /crafting/currencies/available-for-item` - Currencies for specific item
  - `POST /crafting/simulate` - Simulate currency application
  - `POST /crafting/probability` - Calculate success chance

---

## Design Principles

### ✅ Single Responsibility
- Each class has one clear purpose
- `ItemStateManager` = state validation
- `ModifierPool` = mod selection logic
- `CraftingCurrency` = currency behavior
- `CraftingSimulator` = orchestration

### ✅ Open/Closed Principle
- `CraftingCurrency` is abstract base class
- New currencies extend without modifying existing code
- `CurrencyFactory` handles creation

### ✅ Dependency Injection
- `CraftingSimulator` receives `ModifierPool` as dependency
- Easy to swap implementations for testing
- No hard-coded dependencies

### ✅ Immutability Where Possible
- Currency operations return new item states
- Original items aren't mutated (functional style)

### ✅ Type Safety
- Full Pydantic validation on all schemas
- Type hints throughout codebase
- MyPy compatible

---

## Usage Example

```python
from app.schemas.crafting import CraftableItem, ItemRarity
from app.services.crafting.simulator import CraftingSimulator

# Create a white base item
item = CraftableItem(
    base_name="Sage's Robe",
    base_category="body_armour",
    rarity=ItemRarity.NORMAL,
    item_level=50,
)

# Initialize simulator
simulator = CraftingSimulator()

# Simulate using Orb of Alchemy
result = simulator.simulate_currency(item, "Orb of Alchemy")

if result.success:
    print(f"Success! {result.message}")
    print(f"Result: {result.result_item.rarity}")
    print(f"Mods: {len(result.result_item.prefix_mods + result.result_item.suffix_mods)}")
else:
    print(f"Failed: {result.message}")
```

---

## Extension Points

### Adding New Currency
1. Create class extending `CraftingCurrency`
2. Implement `can_apply()` and `apply()` methods
3. Register in `CurrencyFactory._currencies`

```python
class VaalOrb(CraftingCurrency):
    def __init__(self) -> None:
        super().__init__("Vaal Orb", "rare")

    def can_apply(self, item: CraftableItem) -> tuple[bool, Optional[str]]:
        if item.corrupted:
            return False, "Already corrupted"
        return True, None

    def apply(self, item: CraftableItem, modifier_pool: ModifierPool) -> tuple[bool, str, CraftableItem]:
        # Corruption logic here
        pass
```

### Adding Essences
1. Extend `CraftingCurrency` with guaranteed mod logic
2. Reference essence mod from `ModifierPool`
3. Add special handling for "Greater" essences

### Adding Omens (Meta-crafting)
1. Create `OmenModifier` wrapper class
2. Modify currency behavior based on active omen
3. Apply omen effects in `CraftingSimulator`

---

## Testing Strategy

### Unit Tests
- Test each currency individually
- Mock `ModifierPool` for deterministic results
- Verify state transitions (Normal → Magic → Rare)
- Edge cases (full affix slots, wrong rarity, etc.)

### Integration Tests
- Test full crafting workflows
- Multi-step plans
- Probability calculations

### Property-Based Tests
- Use Hypothesis to test invariants
- Item state consistency
- Affix limits respected

---

## Next Steps

1. **Populate Modifier Pool** - Scrape poe2db for real mod data
2. **Add Essences** - Implement guaranteed mod crafting
3. **Crafting Planner** - Multi-step path finding
4. **LLM Integration** - Natural language goal parsing
5. **Frontend UI** - Visual crafting simulator

---

## Performance Considerations

- **Modifier Pool** - Load once at startup, cache in memory
- **Database** - Use for persistent storage, not real-time queries
- **Simulation Speed** - Pure Python logic, very fast (<1ms per simulation)
- **Bulk Simulations** - Can run 1000s of simulations for Monte Carlo probability

---

## File Structure
```
backend/app/
├── models/
│   └── crafting.py              # Database models
├── schemas/
│   └── crafting.py              # Pydantic schemas
├── services/
│   └── crafting/
│       ├── item_state.py        # Item state management
│       ├── currencies.py        # Currency implementations
│       ├── modifier_pool.py     # Mod selection logic
│       └── simulator.py         # Crafting orchestration
└── api/v1/
    └── crafting.py              # REST endpoints
```