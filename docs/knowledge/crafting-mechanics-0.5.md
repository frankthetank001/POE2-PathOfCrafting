# PoE2 0.5 Crafting Mechanics (as this app models them)

_Authoritative, reproducible reference for how this repo models Path of Exile 2 0.5 crafting: mod sources, affix slots, the single "crafted" slot, and which engine class implements each currency family. Grounded in the actual backend code, not the game wiki._

This is the implementation-truth doc. Where the game and the code differ, this describes the code. Sibling docs: [./README.md](./README.md), [./data-retrieval.md](./data-retrieval.md), [./datasets/alloys.md](./datasets/alloys.md).

---

## 1. Mod sources and how copied item text labels them

When you Ctrl+C an item in-game with "advanced mod descriptions" on, each explicit/implicit mod is wrapped in a header line. The header optionally carries a **source qualifier word** before the affix type:

```
{ Prefix Modifier "Flaring" (Tier: 3) }            <- plain explicit
{ Crafted Suffix Modifier "of the Drake" }         <- crafted (0.5 single crafted slot)
{ Desecrated Prefix Modifier "Bonespire" }         <- desecrated (abyssal / bones)
{ Fractured Suffix Modifier "of the Ice" }         <- fractured (locked, cannot remove)
{ Implicit Modifier "..." }                         <- implicit (base line, not an affix)
```

A bare `{ Prefix Modifier ... }` / `{ Suffix Modifier ... }` / `{ Implicit Modifier ... }` is a **plain explicit/implicit** with no special source.

### Where the parser reads this

`backend/app/services/item_parser.py`, method `ItemParser._parse_mods`. The header regex allows an optional leading word (the qualifier) before the affix type:

```python
detailed_match = re.match(
    r'\{\s*(?:(\w+)\s+)?(Prefix|Suffix|Implicit)\s+Modifier\s+"([^"]+)"\s*(?:\(Tier:\s*(\d+)\))?\s*(?:—\s*(.+))?\s*\}',
    line
)
qualifier = detailed_match.group(1)        # "Crafted" / "Desecrated" / "Fractured" / None
...
qual = (qualifier or "").lower()
is_desecrated = "desecrated" in tags_str.lower() or qual == "desecrated"
is_crafted    = qual == "crafted"
is_fractured  = qual == "fractured"
```

Notes confirmed in code:
- The three flags are **mutually exclusive in practice** - a mod is plain, OR crafted, OR desecrated, OR fractured.
- `is_desecrated` can also be triggered by a trailing `(desecrated)` token on a stat line (legacy / simple format), not just the header qualifier.
- The detection regex for "is this a mod section at all" lives in `_looks_like_mods` and the section-router checks in `ItemParser.parse` (the `(?:\w+\s+)?` optional-qualifier group appears there too, so qualified headers are still recognised as mod sections).

These flags are stored on the parser's `ItemMod` schema (`backend/app/schemas/item.py`):

```python
class ItemMod(BaseModel):
    ...
    is_desecrated: bool = False
    is_crafted: bool = False    # 0.5: a single teal "crafted" mod (from essence/alloy)
    is_fractured: bool = False  # locked explicit (cannot be removed)
```

The crafting-engine modifier schema `ItemModifier` (`backend/app/schemas/crafting.py`) carries the same three plus extras:

```python
is_desecrated: bool = False   # green tint
is_fractured:  bool = False   # cannot be removed, orange/brown, displayed locked
is_crafted:    bool = False   # 0.5: the item's single crafted mod (essence/alloy); teal, max 1
is_unrevealed: bool = False   # unrevealed desecrated placeholder
is_essence_only: bool = False
```

---

## 2. Which sources occupy a real affix slot

A maxed Rare has **3 prefixes + 3 suffixes = 6 affixes** (`CraftableItem.max_prefixes` / `max_suffixes` return `3` for Rare, `1` for Magic, `0` for Normal in `backend/app/schemas/crafting.py`).

| Source | Occupies a prefix/suffix affix slot? | Where it lives |
| --- | --- | --- |
| explicit (plain) | Yes | `prefix_mods` / `suffix_mods` |
| crafted (essence/alloy in 0.5) | Yes | a prefix or suffix, flagged `is_crafted` |
| desecrated (bones) | Yes | a prefix or suffix, flagged `is_desecrated` |
| fractured | Yes | a prefix or suffix, flagged `is_fractured` (locked) |
| rune | No - it is a **socket** | `socketed_runes: List[SocketedRune]` |
| enchant | No - separate enchant line | (not in the affix lists) |
| implicit | No - the **base line** | `implicit_mods` |

So crafted, desecrated and fractured mods each consume one of the 6 affix slots. Runes, enchants and implicits do not.

`CraftableItem.total_explicit_mods = prefix_count + suffix_count` and `has_open_affix = can_add_prefix or can_add_suffix`. Unrevealed desecrated mods are stored as placeholders **inside** `prefix_mods`/`suffix_mods` (with `is_unrevealed=True`), so they count toward the affix totals.

---

## 3. Caps and display colours (0.5)

From the official 0.5 patch notes (pathofexile.com forum thread 3932540):

> "All crafted modifiers are now guaranteed, but items can only have **1 crafted modifier** at a time."

> "Desecrated modifiers no longer count as crafted modifiers, but items are limited to **1 Desecrated modifier**."

So the caps the engine enforces are:
- **At most 1 crafted mod** per item. Enforced in `AlloyMechanic.can_apply` (`mechanics.py`): `if any(getattr(m, "is_crafted", False) for m in item.prefix_mods + item.suffix_mods): return False, "Item already has a crafted modifier (only 1 allowed)"`.
- **At most 1 desecrated mod** per item. Enforced in `DesecrationMechanic.can_apply`: rejects if any existing mod has the `desecrated` / `desecrated_only` tag.
- **At most 1 fractured mod** per item, and fractured mods are **never removed** by Chaos/Annul. `FracturingMechanic.can_apply` rejects an item that already has a fractured mod; `ChaosMechanic`, `AnnulmentMechanic` filter `if not mod.is_fractured` before removing.

### Colours (from `frontend/src/assets/poe2-theme.css` and `frontend/src/components/poe2/PoE2ModLine.css`)

| Source | Colour | CSS token / value |
| --- | --- | --- |
| crafted | teal | `--poe2-mod-crafted: #2fd6c6` |
| desecrated | green | `#44ff88` (`.poe2-mod-line.desecrated`) |
| fractured | orange / brown (locked) | `--poe2-mod-fractured: #a38d6d` (stat lines `#d4a574`) |
| prefix / suffix (plain) | blue | `--poe2-mod-prefix` / `--poe2-mod-suffix: #8888ff` |
| implicit | muted blue | `--poe2-mod-implicit: #9999cc` |

> Note: some component CSS files use a stale fallback (e.g. `var(--poe2-mod-crafted, #b4b4ff)`); the canonical value is the `#2fd6c6` defined in `poe2-theme.css`. Fractured mods are rendered with a locked/border treatment, not just a colour.

---

## 4. Currency families and the engine mechanic that implements each

All mechanics derive from `CraftingMechanic` (ABC) in `backend/app/services/crafting/mechanics.py`, each exposing `can_apply(item)` and `apply(item, modifier_pool)`. They are looked up by class-name string through `MECHANIC_REGISTRY` (bottom of `mechanics.py`) and instantiated by `backend/app/services/crafting/unified_factory.py` based on `CurrencyConfigInfo.currency_type` / `mechanic_class`.

### Orbs (one class each, all in `mechanics.py`)

| Currency | Class | What it does |
| --- | --- | --- |
| Transmutation | `TransmutationMechanic` | Normal -> Magic, 1-2 mods |
| Augmentation | `AugmentationMechanic` | add 1 mod to a Magic item |
| Alchemy | `AlchemyMechanic` | Normal -> Rare with 4 mods |
| Regal | `RegalMechanic` | Magic -> Rare, add 1 mod |
| Chaos | `ChaosMechanic` | remove 1 (non-fractured) mod, add 1 of same type |
| Exalted | `ExaltedMechanic` | add 1 mod to a Rare with an open affix |
| Annulment | `AnnulmentMechanic` | remove 1 random (non-fractured) mod; becomes Magic if emptied |
| Divine | `DivineMechanic` | reroll values on all existing mods |
| Vaal | `VaalMechanic` | corrupt (simplified random outcome) |
| Chance | `ChanceMechanic` | upgrade a Normal item randomly (Unique path stubbed) |
| Fracturing | `FracturingMechanic` | fracture a random mod (Rare, needs 4+ mods, none already fractured) |
| Mirror | `MirrorMechanic` | deep-copy the item (mirrored copy) |
| Hinekora (Hinekora's Lock) | `HinekoraMechanic` | "foresee next currency" (returns success message, foresight not modelled) |

> Note: `ScouringMechanic` (Orb of Scouring: strip all mods -> Normal) exists as a class in `mechanics.py` but is **not** registered in `MECHANIC_REGISTRY`, so it is not reachable through the standard factory path. Treat it as code-present-but-unwired.

### Essences -> `EssenceMechanic`

`EssenceMechanic(config, essence_info)` reads `EssenceInfo.mechanic` and branches into one of two sub-mechanics:

- `magic_to_rare` (Lesser / Normal / Greater essences): require a **Magic** item, upgrade it to Rare and add one guaranteed mod.
- `remove_add_rare` (Perfect / Corrupted essences): require a **Rare** item with >=1 mod, remove one and add the guaranteed mod (forcing prefix/suffix removal if that side is full).

The guaranteed mod is resolved via `_create_guaranteed_modifier` using the per-slot effect's `mod_id` (preferred) or stat-text fallback, then values are rolled from `stat_ranges`. Essence-added mods feed the single 0.5 **crafted** slot in-game; in code the standard essence mod is flagged `is_essence_only=True` and tagged `essence_guaranteed` (see the alloy note below for how the crafted flag is set).

### Runic Alloys -> `AlloyMechanic` (subclass of `EssenceMechanic`)

`AlloyMechanic` is structurally a Perfect Essence (`remove_add_rare`): remove a random mod from a **Rare** item, add the alloy's guaranteed mod for that slot. The per-slot effects come from `backend/source_data/alloys.json`, shaped as essence `item_effects` so the essence slot-matching and value-rolling are reused. Two key differences, both in `mechanics.py`:

```python
# AlloyMechanic._create_guaranteed_modifier
mod.is_essence_only = False
mod.is_crafted = True   # this is the item's single teal crafted mod
mod.tags = [... drop "essence_guaranteed"/"essence_only" ...] + ["alloy_guaranteed"]
```

and `can_apply` enforces the **1-crafted-mod cap** (see section 3). So essences AND alloys both feed the single 0.5 "crafted" slot; in this codebase the alloy result is the one explicitly flagged `is_crafted=True`. See [./datasets/alloys.md](./datasets/alloys.md) for the alloy effect data.

### Desecration / bones -> `DesecrationMechanic`

`DesecrationMechanic(config)` adds an **unrevealed desecrated** modifier (placeholder with `is_unrevealed=True`, plus an `UnrevealedModifier` entry in `item.unrevealed_mods`) to a Rare, non-corrupted item. Config carries `bone_type` (gnawed / preserved / ancient) and `bone_part` (jawbone / rib / collarbone / cranium / vertebrae), which gate which item categories are valid. Enforces the 1-desecrated-mod cap. If the item has a Mark of the Abyssal Lord (`mod_group == "AbyssTargetMod"`), that mark is consumed and replaced with the unrevealed desecrated mod.

### Catalysts -> `CatalystMechanic`

`CatalystMechanic(config)` adds quality to **rings and amulets only** (not belts; `base_category in ['ring','amulet']`). `catalyst_type` (flesh / neural / carapace / uul_netol / xoph / tul / esh / chayula / reaver / sibilant / skittering / adaptive) selects which mod category the quality boosts. Quality roll: 85% +1%, 15% +2%, capped at `max_quality` (default 20). Switching catalyst type resets quality to 0.

### Omens -> `OmenModifiedMechanic` (wrapper)

Not a currency family of its own. `OmenModifiedMechanic(base_mechanic, omen_info)` wraps another mechanic (e.g. Exalted, Regal, Essence) to apply omen rules such as force-prefix / force-suffix / add-two. Built by `unified_factory._apply_omens`.

---

## 5. Where this lives in code

| File | Defines |
| --- | --- |
| `backend/app/services/crafting/mechanics.py` | `CraftingMechanic` base + every mechanic class + `MECHANIC_REGISTRY` (the class-name -> class map) |
| `backend/app/services/crafting/unified_factory.py` | builds the right mechanic from a `CurrencyConfigInfo` (routes essence -> `EssenceMechanic`, alloy -> `AlloyMechanic`, desecration -> `DesecrationMechanic`, else `MECHANIC_REGISTRY`); applies omen wrappers |
| `backend/app/services/crafting/config_service.py` | loads currency / essence / alloy / bone configs from `source_data/*.json` into the `*Info` schemas |
| `backend/app/schemas/crafting.py` | `ItemModifier` (with `is_crafted` / `is_desecrated` / `is_fractured` / `is_unrevealed`), `ModType` enum, `CraftableItem` (affix caps, `total_explicit_mods`, `has_open_affix`), `EssenceInfo`, `DesecrationBoneInfo`, `CurrencyConfigInfo` |
| `backend/app/schemas/item.py` | parser-side `ItemMod` (with `is_crafted` / `is_desecrated` / `is_fractured`) and `ParsedItem` |
| `backend/app/services/item_parser.py` | `ItemParser._parse_mods` reads the `{ <Qualifier> Prefix/Suffix/Implicit Modifier ... }` header and sets the source flags |
| `backend/source_data/alloys.json`, `catalysts.json`, `desecration_bones.json`, `omens.json`, `currency_configs.json` | the per-currency content the mechanics consume |
| `frontend/src/assets/poe2-theme.css`, `frontend/src/components/poe2/PoE2ModLine.css` | mod source colours (crafted teal, desecrated green, fractured brown/locked) |

### Reproduce: list every registered mechanic

```bash
cd backend
python -c "from app.services.crafting.mechanics import MECHANIC_REGISTRY; import json; print(json.dumps(sorted(MECHANIC_REGISTRY), indent=2))"
```

### Reproduce: parse a copied item and inspect source flags

```bash
cd backend
python -c "
from app.services.item_parser import ItemParser
txt = '''Rarity: Rare
Foo Bar
Sapphire Ring
--------
Item Level: 80
--------
{ Crafted Suffix Modifier \"of the Drake\" }
+25% to Fire Resistance
{ Desecrated Prefix Modifier \"Bonespire\" }
+40 to maximum Life
'''
item = ItemParser.parse(txt)
for m in item.explicits:
    print(m.mod_name, 'crafted=', m.is_crafted, 'desecrated=', m.is_desecrated, 'fractured=', m.is_fractured)
"
```

---

**Source / last verified:** 2026-06-12 - `backend/app/services/crafting/mechanics.py` (MECHANIC_REGISTRY, EssenceMechanic, AlloyMechanic, DesecrationMechanic, CatalystMechanic), `backend/app/schemas/crafting.py`, `backend/app/schemas/item.py`, `backend/app/services/item_parser.py`, `backend/app/services/crafting/unified_factory.py`, `frontend/src/assets/poe2-theme.css`, `frontend/src/components/poe2/PoE2ModLine.css`, PoE2 0.5 patch notes (pathofexile.com forum thread 3932540).
