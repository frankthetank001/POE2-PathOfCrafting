# PoE2 PathOfCrafting Knowledge Base

_A living, referenceable record of how Path of Exile 2 works, how this app models its crafting system, and how we retrieve and derive every piece of game/meta data. The goal: a future engineer or AI agent can act from these docs alone, without rediscovering any of it from scratch._

Keep this current. When you learn or change something durable about the mechanics, the data pipeline, or a hand-built dataset, update the relevant doc here in the same change.

---

## Index

| Doc | What it covers |
| --- | --- |
| [crafting-mechanics-0.5.md](./crafting-mechanics-0.5.md) | How this repo models PoE2 0.5 crafting: mod sources (plain / crafted / desecrated / fractured), affix slots, the single 0.5 "crafted" slot, currency families, and the engine mechanic class that implements each. Grounded in the backend code, not the wiki. |
| [data-retrieval.md](./data-retrieval.md) | Where every kind of data comes from and how to refresh it, with reproduction commands: pinned pob-data (mods/bases/essences/runes), the poe.ninja builds/meta artifact, and the wiki / in-game fallback for data not in pob-data. |
| [datasets/alloys.md](./datasets/alloys.md) | The hand-sourced Runic Alloy dataset (`backend/source_data/alloys.json`): why the alloy -> slot -> mod mapping had to be built by hand, the step-by-step sourcing process, the 13 alloys, and how it is validated. |

---

## How this is organised

Three kinds of knowledge live here, by directory level:

- **Game mechanics** - how PoE2 (as this app models it) actually behaves. See `crafting-mechanics-0.5.md`.
- **Data retrieval** - where data comes from and how to (re)fetch or (re)derive it. See `data-retrieval.md`.
- **Hand-derived datasets** (`datasets/`) - data that does NOT exist in our upstream sources and had to be authored by hand, anchored onto our own mod/base IDs. The first is `datasets/alloys.md`. **New hand-sourced datasets go under `datasets/`**, one doc per dataset, each documenting its source, sourcing process, committed artifact, and validation.

---

## Conventions for maintaining these docs

- **Cite source + date.** Every doc ends with a `**Source / last verified:** YYYY-MM-DD - ...` footer listing the exact files / upstream commits / web sources it was checked against. Update the date when you re-verify.
- **Include reproduction commands.** A future reader should be able to re-derive or re-fetch any value from the doc alone. Prefer runnable snippets (run from `backend/`) over prose.
- **Ground every claim in code or data.** Point at the real file, class, or JSON entry. Where the game and the code differ, document the code - these are implementation-truth docs.
- **Anchor web-sourced data onto our own IDs.** Never store loose web text as truth. Bind each sourced value to a real `mod_id` / base in our pool (verify it resolves via the loader) so it stays consistent with the crafting engine. If no matching ID exists, the source is suspect - re-check it, do not invent an ID.
- **Mark uncertainty as TODO, do not guess.** If something is unconfirmed or deferred, say so explicitly (as `datasets/alloys.md` does for its 3 deferred mods) rather than inventing a plausible answer.
- **No em-dashes, no decorative emojis.** Use a plain hyphen with spaces around it when separating clauses. Emojis only where they carry specific semantic meaning, never as section markers or decoration.

---

**Source / last verified:** 2026-06-12 - `docs/knowledge/crafting-mechanics-0.5.md`, `docs/knowledge/data-retrieval.md`, `docs/knowledge/datasets/alloys.md` (the three docs this index links), and the repo layout under `docs/knowledge/`.
