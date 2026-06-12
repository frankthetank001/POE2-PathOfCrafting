# Data Sources & Retrieval Recipes

_How we get and refresh each kind of game/meta data in this repo, with reproducible commands. If you need a value and don't know where it comes from, start here._

This is the authoritative "where does this data come from and how do I refresh it" reference. Every kind of data the crafting + builds features rely on is one of three sources:

1. **pob-data** - the mod / base / essence / rune pool (pinned GitHub snapshot).
2. **Builds / meta** - poe.ninja-derived usage stats (versioned artifact from the sibling scraper repo).
3. **Wiki / in-game fallback** - for data that is NOT in pob-data (e.g. the alloy currency mapping), hand-sourced and anchored onto our own mod IDs.

Sibling docs: [./README.md](./README.md) | [./crafting-mechanics-0.5.md](./crafting-mechanics-0.5.md) | [./datasets/alloys.md](./datasets/alloys.md)

---

## 1. pob-data (mods, bases, essences, runes)

The primary game-data pool: every craftable prefix/suffix, item base, essence, rune, and corrupted/desecrated implicit.

- **Upstream:** [github.com/repoe-fork/pob-data](https://github.com/repoe-fork/pob-data), under `pob-data/poe2/`.
- **Loader:** `backend/app/services/crafting/pob_data_loader.py`
- **Local cache:** `backend/source_data/pob-data/` (constant `POB_DATA_CACHE_PATH`).

### Why it is PINNED

The loader pins a fixed commit instead of tracking `master`:

```python
# backend/app/services/crafting/pob_data_loader.py
POB_DATA_REF = "ce289e6ec1765be4b88859dbe6a1df07b08b758e"  # repoe-fork/pob-data @ 2026-06-04 (0.5)
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/repoe-fork/pob-data/{POB_DATA_REF}/pob-data/poe2"
```

Upstream regenerates daily, which silently shifts exact mod/base counts and was breaking CI's mod-count tests (`backend/tests/test_mod_counts.py`). Pinning makes the data deterministic. The current pin is the PoE2 0.5 "Runes of Aldur" snapshot. Bump it **deliberately** (see [Bumping the pin](#bumping-the-pin)), not as a routine update.

### What each file holds

The loader fetches `POB_DATA_FILES` plus the `Bases/` directory listing. Current pinned snapshot counts (verified 2026-06-12):

| File | Contents | Entries (pinned) |
| --- | --- | --- |
| `ModItem.json` | Regular craftable prefixes/suffixes, AND the 49 `Alloy*` effect mods (the stat lines the alloy currencies grant - see caveat below) | 2549 |
| `ModVeiled.json` | Desecrated / abyss mods (boss-specific: amanamu, kurgal, ulaman) | 386 |
| `ModCorrupted.json` | Corrupted implicits | 127 |
| `ModRunes.json` | Rune mods, keyed `rune_name -> item_type -> {...}` | 283 |
| `Essence.json` | Essence definitions; `mods` maps `{item_type: mod_id}` into `ModItem.json` | 82 |
| `Bases/*.json` | Item bases + their `tags` (used to derive category/slot/applicability) | 29 files |

> The `Alloy*` mods in `ModItem.json` are the **stat effects** an alloy currency applies. They have `weightVal: [0]` (never roll randomly) and are referenced by ID. pob-data does NOT carry the alloy currency-to-slot mapping itself - see the [caveat](#caveat-alloys-are-not-fully-in-pob-data).

### Recipe A - query via the loader (preferred)

The loader is a singleton; `load_all()` is lazy (the public accessors call it if needed). Run from `backend/`:

```python
from app.services.crafting.pob_data_loader import get_pob_data_loader

loader = get_pob_data_loader()
loader.load_all()  # optional; accessors auto-load

mods = loader.get_all_modifiers()          # List[ItemModifier], regular craftable
essences = loader.get_essences()           # Dict[name -> EssenceInfo]
bases = loader.get_base_items()            # Dict[base_name -> BaseItemInfo]

# Resolve a single mod by its pob-data ID (e.g. one an Essence maps to):
mod = loader.get_modifier_by_id("AlloyAccuracyAttackSpeedHybrid1")
print(mod.stat_text if mod else "not found")
```

Other accessors on the loader: `get_corrupted_modifiers()`, `get_desecrated_modifiers()`, `get_all_modifiers_combined()`, `get_essence_by_name()`, `get_base_item()`, `get_mod_data(mod_id)` (raw dict), `get_mod_for_essence(essence_name, item_type)`, `get_all_runes()`, `get_rune_by_name()`, `get_modifiers_for_item_tags()`.

> Note: `get_all_modifiers()` returns the modifier pool with tiers RE-NUMBERED so T1 = best (highest values), and `stat_text` NORMALIZED to `#` placeholders (e.g. `+# to Accuracy Rating`). If you need the raw upstream text/ranges, use `get_mod_data(mod_id)` or read the JSON directly (Recipe B).

### Recipe B - raw JSON (no app deps)

When you just want the upstream values exactly as shipped, read the cached files directly. Run from `backend/`:

```python
import json

with open("source_data/pob-data/ModItem.json", encoding="utf-8") as f:
    mods = json.load(f)

# Each entry is keyed by mod_id; stat lines are numbered keys "1".."9".
alloys = [k for k in mods if k.startswith("Alloy")]
print(len(alloys), "alloy effect mods")  # -> 49
print(mods["AlloyAccuracyAttackSpeedHybrid1"]["1"])  # "+(327-427) to Accuracy Rating"
```

A pob-data mod entry looks like (fields the loader reads): `affix`, `group`, `level`, `modTags`, `type` (`Prefix`/`Suffix`/`Corrupted`), `weightKey`/`weightVal` (tag-conditioned spawn weights -> applicability), `tradeHash`, and numbered stat lines `"1"`, `"2"`, ... Essence entries carry `name`, `type`, `tierLevel`, and `mods` (a `{item_type: mod_id}` dict, e.g. `Essence of the Breach -> {"Amulet": "EssenceBreach", "Ring": "EssenceBreach"}`).

### Bumping the pin

When you intend to adopt newer game data:

1. Pick the target commit on `repoe-fork/pob-data` (use a specific SHA, never `master`).
2. Edit `POB_DATA_REF` in `backend/app/services/crafting/pob_data_loader.py` and update the trailing comment (date + game version).
3. Re-fetch the cache. Either delete `backend/source_data/pob-data/` and let startup auto-fetch, or force it in-process:

   ```python
   from app.services.crafting.pob_data_loader import get_pob_data_loader
   get_pob_data_loader().update_from_github()  # re-fetch all files + Bases/, then reload
   ```

4. **Re-baseline the count tests.** Exact mod counts WILL change. Run `cd backend && pytest tests/test_mod_counts.py` and update the `EXPECTED_MOD_COUNTS` (and any per-category) baselines in `backend/tests/test_mod_counts.py` to the new numbers. The existing comments in that file (e.g. `# re-baselined to current repoe-fork/pob-data (was 13)`) are the precedent - annotate each change the same way.
5. Sanity-check the alloy story still holds: `Alloy*` IDs your `datasets/alloys.md` references must still exist in `ModItem.json`. If upstream renamed any, re-anchor (see Section 3).

### Caveat: alloys are NOT fully in pob-data

pob-data contains the `Alloy*` **stat mods** (in `ModItem.json`) but NOT the alloy **currency definitions** nor the **item-applicability** (which currency applies which mod to which slot). This was checked against `ModItemExclusive.json` and every field on the alloy mod entries - the slot-to-mod mapping simply is not there. That mapping is **hand-sourced** from in-game item descriptions and lives in `backend/source_data/alloys.json` (a 13-entry list of currencies, each with `item_effects: [{item_type, mod_id, mod_type, effect_text}]`). See [./datasets/alloys.md](./datasets/alloys.md) for the full dataset doc and how it was built.

---

## 2. Builds / meta data (poe.ninja)

Popular-build usage stats: which bases and mods the meta actually runs, by slot.

- **Produced by:** the sibling **POE2-Builds-Scraper** repo (the volatile poe.ninja scrape lives entirely there; this app only consumes a versioned JSON artifact).
- **Loader:** `backend/app/services/builds/build_data_loader.py`
- **Models:** `backend/app/services/builds/models.py`
- **Local cache:** `backend/source_data/builds/` (`builds_artifact_dir` setting).
- **Config:** `backend/app/core/config.py` - `builds_artifact_url` (remote, `{slug}` templated), `builds_browser_url`, `builds_league_slug` (default `runesofaldur`).

Two artifacts per league slug:

| File | Loader fn | Model | What it is |
| --- | --- | --- | --- |
| `latest-<slug>.json` | `load_build_stats()` | `BuildStats` | Aggregate usage: `base_usage[]` (with `rarity_mix`, `usage_pct`) and `mod_usage[]` (with `mod_template`, `mod_origin`, `value_samples`) |
| `builds-<slug>.json` | `load_builds_artifact()` | `BuildsArtifact` | A representative SAMPLE of real builds (full per-build gear/skills/defenses/links) |

The loader tries the remote URL first (caches to disk on success) and falls back to the local cache. With no `builds_artifact_url` configured it reads the committed local files. Current local snapshot (`runesofaldur`): `sample_size: 100`, 258 `base_usage` rows, 3257 `mod_usage` rows.

Important: the aggregate's `mod_usage[].mod_template` is value-templated text (e.g. `#% increased Rarity of Items found`) with **no mod_id/tier** - the app resolves those against `ModItem.json` at query time. The per-build sample's `BuildItemMod.text` is markup-stripped but NOT templated (numbers intact).

### Recipe - load + query

Run from `backend/`:

```python
from app.services.builds.build_data_loader import load_build_stats, load_builds_artifact

stats = load_build_stats()          # BuildStats for settings.builds_league_slug, or None
if stats:
    print(stats.league, stats.sample_size)
    # Most-used bases by slot:
    top = sorted(stats.base_usage, key=lambda b: b.usage_count, reverse=True)[:5]
    for b in top:
        print(b.slot, b.base_name, b.usage_pct, b.rarity_mix)
    # Mods seen on a given base, with their origin (explicit/implicit/rune/crafted/...):
    for m in stats.mod_usage:
        if m.base_name == "Gold Amulet":
            print(m.mod_origin, m.mod_template, m.value_samples[:5])

sample = load_builds_artifact()     # BuildsArtifact (per-build sample), or None
if sample:
    b = sample.builds[0]
    print(b.character, b.ascendancy, b.level)
    for item in b.items:
        print(item.slot, item.rarity, item.base_type, len(item.mods))
```

Pass an explicit slug to either function to load a different league (`load_build_stats("some-slug")`).

---

## 3. Wiki / in-game fallback (data NOT in pob-data)

Some mechanics' data does not exist in pob-data at all. The canonical example is the **alloy currency -> slot -> mod mapping**: it only exists in the in-game item descriptions. For these, the source of truth is the in-game item text, mirrored by [poe2db.tw](https://poe2db.tw/us/), the PoE2 wiki, and community guides.

### Methodology (the reusable skill)

Do NOT trust web text blindly. The rule is **source structured, then anchor onto our own IDs**:

1. **Source** the structured data from a guide/wiki/poe2db (currency name, slot, granted stat text).
2. **Anchor** each granted stat to one of OUR real mod IDs by matching stat text -> `mod_id`. The mod you record MUST be a real entry in our pool (check it loads via `loader.get_modifier_by_id(mod_id)` or exists in `ModItem.json`). If no matching ID exists, the data is suspect - re-check the source or flag it, do not invent an ID.
3. **Validate** by loading: every `mod_id` you wrote down should resolve. A quick check from `backend/`:

   ```python
   import json
   from app.services.crafting.pob_data_loader import get_pob_data_loader
   loader = get_pob_data_loader()
   alloys = json.load(open("source_data/alloys.json", encoding="utf-8"))
   for currency in alloys:
       for eff in currency["item_effects"]:
           assert loader.get_modifier_by_id(eff["mod_id"]), f"missing {eff['mod_id']}"
   print("all alloy mod_ids resolve")
   ```

The worked example - alloy currencies anchored onto the 49 `Alloy*` mod IDs in `ModItem.json`, stored as `backend/source_data/alloys.json` - is documented in [./datasets/alloys.md](./datasets/alloys.md).

---

## 4. Conventions

- **Pin external data for determinism.** Track a fixed commit/version, never a moving `master`/`latest` branch, so counts and behavior are reproducible and CI is stable. (pob-data does this via `POB_DATA_REF`; the builds artifact via a versioned `snapshot_version`.)
- **Always cite source + date.** Every dataset / hand-sourced value records where it came from and when it was last verified (see the footer convention and the `datasets/` docs).
- **Always provide a reproduction command.** A future engineer/agent should be able to re-derive or re-fetch the data from this doc alone.
- **Prefer anchoring web-sourced data onto our own IDs.** Never store loose web text as truth; bind it to a real `mod_id`/base in our pool so it stays consistent with the crafting engine.

---

**Source / last verified:** 2026-06-12 - `backend/app/services/crafting/pob_data_loader.py` (POB_DATA_REF `ce289e6`), `backend/app/services/builds/build_data_loader.py`, `backend/app/services/builds/models.py`, `backend/app/core/config.py`, `backend/tests/test_mod_counts.py`, `backend/source_data/pob-data/` + `backend/source_data/builds/` + `backend/source_data/alloys.json` (PoE2 0.5 Runes of Aldur snapshot, 2026-06-04); upstream [repoe-fork/pob-data](https://github.com/repoe-fork/pob-data), poe.ninja via POE2-Builds-Scraper.
