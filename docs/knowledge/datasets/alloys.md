# Runic Alloy dataset (sourcing + mapping)

*The authoritative record of the `backend/source_data/alloys.json` dataset: what Runic Alloys are, why this mapping had to be built by hand, and the exact step-by-step process used to source it - so it can be reproduced and extended without rediscovery.*

## 1. What Runic Alloys are (PoE2 0.5)

A **Runic Alloy** is a crafting currency that is applied to a **RARE** item. Applying it:

1. Removes one random modifier from the item, then
2. Adds the alloy's **guaranteed CRAFTED modifier** for that item's equipment slot.

The added mod is the item's single **teal crafted mod** (max **1** crafted mod per item in 0.5). Each of the 13 alloys has a **different effect per equipment slot** - e.g. the same alloy gives one stat on Boots and a different stat on Gloves. There is no slot the dataset does not enumerate explicitly: an alloy can only be applied to slots it has an `item_effect` for.

Structurally this is **identical to a Perfect Essence** (the `remove_add_rare` mechanic). The only behavioural differences are:

- The added mod is flagged as a **crafted** mod (`is_crafted = True`, `is_essence_only = False`, tag `alloy_guaranteed`) rather than an essence-only mod.
- Alloys **only apply to Rare items**, and are rejected if the item already holds a crafted mod.

This is why, in code, `AlloyMechanic` subclasses `EssenceMechanic` (see `backend/app/services/crafting/mechanics.py` around line 2582) and reuses its per-slot matching + value rolling.

See also: [../crafting-mechanics-0.5.md](../crafting-mechanics-0.5.md) for the broader 0.5 mechanic set.

## 2. The data gap - why this dataset has to exist by hand

`pob-data` (`backend/source_data/pob-data/ModItem.json`) contains the **49 `Alloy*` EFFECT mods** - the actual stat lines an alloy can grant. What it does **not** contain is the currency grouping or item applicability. Concretely, verified against the committed `ModItem.json` (2549 total entries):

- **All 49 `Alloy*` mods have `weightKey: ['default']` with `weightVal: [0]`.** A zero weight means the mod has **no roll weight / no applicable item** anywhere in the data - it is never a naturally rollable mod, so the data carries no slot applicability for it.
- **`modTags` are STAT tags, not slot tags.** Across the 49 mods the tag union is `damage, ailment, attack, speed, caster_speed, caster, elemental_damage, elemental, fire, cold, lightning, resource, mana, runic_ward, minion, aura` - nothing that identifies Boots vs Gloves vs Helmet.
- **The `affix` field only splits prefix vs suffix, not the 13 currencies.** Distribution is exactly `Verisium` (13, all `type: Prefix`) and `of the Stars` (36, all `type: Suffix`). So `affix` cannot recover which of the 13 alloys a mod belongs to.
- **There is no Alloy / Currency file in `pob-data`** - even at the latest commit. The `pob-data` directory holds `ModItem.json`, `ModCorrupted.json`, `ModRunes.json`, `ModVeiled.json`, `Essence.json`, and `Bases/`; the closest is `Essence.json` (essences, not alloys). There is no `ModItemExclusive.json` in this checkout, so it contributes zero alloy entries.

Conclusion: the **alloy -> slot -> mod** mapping is **NOT derivable** from our data. It must be authored by hand and anchored back onto our real mod IDs.

A representative raw record (note the empty `modTags`, `weightKey: ['default']`, `weightVal: [0]`):

```json
"AlloySpiritOnBoots1": {
  "1": "+(10-15) to Spirit",
  "affix": "of the Stars",
  "group": "BaseSpirit",
  "level": 45,
  "modTags": [],
  "type": "Suffix",
  "weightKey": ["default"],
  "weightVal": [0]
}
```

## 3. The sourcing process (reproducible)

This is the process the repo owner asked to be captured. Each step is independently re-runnable.

**a. Enumerated the 49 `Alloy*` mods and confirmed none carry slot applicability.** Every field was inspected (`affix`, `weightKey`, `weightVal`, `modTags`, `group`, `type`, `level`, `tradeHashes`) plus a check that no `ModItemExclusive.json` exists. Repro:

```bash
cd backend
python -c "
import json, collections
d = json.load(open('source_data/pob-data/ModItem.json', encoding='utf-8'))
alloy = {k: v for k, v in d.items() if k.startswith('Alloy')}
print('Alloy* mods:', len(alloy))                                   # 49
print('all weightVal == [0]:', all(v.get('weightVal') == [0] for v in alloy.values()))
print('affix split:', collections.Counter(v['affix'] for v in alloy.values()))  # Verisium 13 / of the Stars 36
tags = collections.Counter(t for v in alloy.values() for t in v.get('modTags', []))
print('modTags union (stat tags, no slots):', dict(tags))
"
```

**b. Confirmed the mechanic from the official 0.5 patch notes + wiki.** Alloys = remove-random + add a guaranteed crafted-only mod, with a per-equipment-slot effect; **13** alloys total.

**c. Sourced the 13 alloys and their per-slot effects from the in-game item descriptions plus a community guide.** Example (Cyclonic Alloy): Body Armour = reduced Slowing Potency of Debuffs on You; Boots = increased Skill Effect Duration; Gloves = increased Duration of Damaging Ailments on Enemies; Helmet = increased Archon Buff duration. Community cross-reference: the u4n "list of alloy currency items" guide.

**d. ANCHORED on OUR mod IDs.** For each guide effect, the stat text was matched to a real `mod_id` in `ModItem.json` by normalising value ranges to `#` (e.g. `+(10-15) to Spirit` -> the `AlloySpiritOnBoots1` line). Every entry in the dataset is therefore a real mod that exists in our pool - the dataset never invents a stat.

**e. Validated coverage.** **46 of 49** effect mods are mapped across the 13 alloys (46 distinct `mod_id`s = 46 effect rows, all resolving in the pool). A test asserts every mapped `mod_id` resolves (see section 6). The remaining 3 are deliberately deferred (section 5).

## 4. The committed artifact: `backend/source_data/alloys.json`

A JSON **list** of 13 alloy objects. Each object has the shape:

```json
{
  "name": "Mystic Alloy",
  "currency_type": "alloy",
  "rarity": "currency",
  "stack_size": 10,
  "mechanic": "remove_add_rare_crafted",
  "item_effects": [
    {
      "item_type": "Boots",
      "mod_id": "AlloySpiritOnBoots1",
      "mod_type": "suffix",
      "effect_text": "+(10-15) to Spirit"
    }
  ]
}
```

- `name` - the in-game currency name.
- `item_effects` - one entry per equipment slot the alloy covers; `item_type` is the slot, `mod_id` is the anchored `ModItem.json` id, `mod_type` is `prefix`/`suffix`, `effect_text` is the human-readable stat with ranges.

### The 13 alloys and the slots each covers

(read directly from `alloys.json`)

| Alloy | Slots covered (`item_type`) |
| --- | --- |
| Runic Alloy | Amulet, Belt, Ring |
| Adaptive Alloy | Gloves, Staff, Wand |
| Protective Alloy | Belt, Shield, Weapon |
| Expansive Alloy | Body Armour, Boots, Gloves, Helmet |
| Swift Alloy | Belt, Gloves, Ring, Shield |
| Cyclonic Alloy | Body Armour, Boots, Gloves, Helmet |
| Prismatic Alloy | Caster Weapon, Gloves, Martial Weapon, Sceptre |
| Mystic Alloy | Boots, Caster Weapon, Gloves, Helmet, Quiver |
| Sovereign Alloy | Armour, Jewellery, Weapon |
| Celestial Alloy | Caster Weapon, Martial Weapon |
| Transcendent Alloy | Caster Weapon, Martial Weapon |
| The Runebinder's Alloy | Bow, Crossbow, Sceptre, Staff, Wand |
| The Runefather's Alloy | Mace, Spear, Talisman, Warstaff |

Note the broad meta-slots: Sovereign Alloy uses `Armour` / `Jewellery` / `Weapon` (category-level, not a single piece), and several alloys use `Caster Weapon` / `Martial Weapon` groupings rather than a specific base.

### How it is consumed

1. `backend/app/services/crafting/config_service.py` -> `_load_alloy_configs` reads `alloys.json` and builds an **`EssenceInfo`-shaped** config per alloy (`essence_type="alloy"`, `mechanic="remove_add_rare"`, each effect mapped to an `EssenceItemEffect` carrying `item_type` / `modifier_type` / `effect_text` / `mod_id`). This is keyed by alloy name in `_alloy_configs` and exposed via `get_alloy_config(name)` / `get_all_alloy_names()`.
2. `backend/app/services/crafting/unified_factory.py` -> `_create_alloy_mechanic` (dispatched when `config.currency_type == "alloy"`) builds an **`AlloyMechanic`** from that config.
3. `AlloyMechanic` (`backend/app/services/crafting/mechanics.py`) reuses `EssenceMechanic`'s slot matching + value rolling, then re-flags the result as the item's single teal crafted mod and restricts application to Rare items.
4. The simulator offers each alloy per slot (only for slots the alloy has an `item_effect` for).

## 5. The 3 deferred mods (not yet mapped)

These 3 of the 49 `Alloy*` mods are intentionally **not** in `alloys.json` yet. They are **alternate variants** that the community guide summary did not enumerate by slot, so their alloy + slot pairing is not yet confirmed. They are real mods in the pool; they are simply not wired to a currency entry.

| mod_id | Stat text | Affix | Note |
| --- | --- | --- | --- |
| `AlloyLocalWardIncreasePercent2` | `(31-40)% increased Runic Ward` | Prefix | Higher-roll sibling of the mapped `AlloyLocalWardIncreasePercent1` (`(24-30)% increased Runic Ward`), which is **Sovereign Alloy / Armour**. |
| `AlloyManaNearbyAllyAttackSpeedHybrid1` | `+(110-114) to maximum Mana \| Allies in your Presence have (4-8)% increased Attack Speed` | Prefix | Hybrid mana / presence attack-speed line. |
| `AlloySpiritPresenceAreaOfEffectHybrid1` | `(8-12)% increased Spirit \| (50-60)% increased Presence Area of Effect` | Suffix | Hybrid spirit / presence AoE line. |

> Note: the `ModItem.json` `'1'` field only stores the first stat of a hybrid mod; the full two-line text above was reconstructed from the `'1'` + `'2'` fields of each record.

### How to add a deferred mod

1. Find its alloy + slot in-game (which currency grants it, on which equipment slot).
2. Add one `item_effect` line to the relevant alloy object in `backend/source_data/alloys.json` using the existing shape (`item_type`, `mod_id`, `mod_type`, `effect_text`). If it is a brand-new alloy, add a new top-level object instead.
3. Run the test suite - `test_every_alloy_effect_resolves_to_a_real_mod` will confirm the `mod_id` resolves in the pool. Coverage then moves from 46/49 toward 49/49.

## 6. How to verify / extend

Tests live in `backend/tests/test_alloy_mechanics.py`. Key assertions:

- `test_alloy_configs_loaded` - exactly **13** alloy names load and each is a valid currency.
- `test_every_alloy_effect_resolves_to_a_real_mod` - every alloy's per-slot `mod_id` exists in the `pob-data` mod pool (this is the guard for sourcing step 3e and for newly added entries).
- `test_alloy_slot_applicability` - an alloy is only offered for slots it defines (Mystic has no Ring effect -> rejected on a ring; Runic Alloy has a Ring effect -> accepted).
- `test_only_one_crafted_mod_allowed` - a second alloy is rejected once the item holds a crafted mod.
- `test_alloys_only_apply_to_rare` - alloys are rejected on Magic items.

Run them:

```bash
cd backend
pytest tests/test_alloy_mechanics.py -v
```

**Canonical example:** applying **Mystic Alloy** to a rare **Boots** removes a random mod and adds `+(10-15) to Spirit` as a teal crafted **suffix** (`mod_id` `AlloySpiritOnBoots1`, tag `alloy_guaranteed`). In short: **"+10-15 Spirit on boots = Mystic Alloy."** This is exactly what `test_mystic_alloy_adds_crafted_spirit_on_boots` asserts.

Related docs: [../README.md](../README.md) | [../crafting-mechanics-0.5.md](../crafting-mechanics-0.5.md) | [../data-retrieval.md](../data-retrieval.md)

**Source / last verified:** 2026-06-12 - backend/source_data/alloys.json, backend/source_data/pob-data/ModItem.json (49 Alloy* mods), backend/app/services/crafting/config_service.py, backend/app/services/crafting/mechanics.py, backend/app/services/crafting/unified_factory.py, backend/tests/test_alloy_mechanics.py; PoE2 0.5 patch notes + wiki; u4n "list of alloy currency items" community guide.
