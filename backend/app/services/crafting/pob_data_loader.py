"""
POB Data Loader - Loads modifier and item data from pob-data.

Fetches data from GitHub at startup if not cached locally, then loads from
local cache for subsequent runs.

Data sources (from https://github.com/repoe-fork/pob-data):
- ModItem.json: Regular craftable prefixes/suffixes
- ModCorrupted.json: Corrupted implicit mods
- ModVeiled.json: Desecrated/abyss mods (boss-specific)
- Essence.json: Essence-to-mod mappings
- Bases/*.json: Item base definitions with tags
"""

import json
import os
import re
import httpx
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.schemas.crafting import (
    BaseItemInfo,
    EssenceInfo,
    EssenceItemEffect as EssenceItemEffectSchema,
    ItemModifier,
    ModType,
    StatRange,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

# Local cache path for pob-data files
POB_DATA_CACHE_PATH = Path(__file__).parent.parent.parent.parent / "source_data" / "pob-data"

# GitHub raw URLs for pob-data
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/repoe-fork/pob-data/master/pob-data/poe2"
GITHUB_API_BASE = "https://api.github.com/repos/repoe-fork/pob-data/contents/pob-data/poe2"

# Files to fetch
POB_DATA_FILES = ["ModItem.json", "ModCorrupted.json", "ModVeiled.json", "Essence.json"]


def ensure_pob_data_exists() -> Path:
    """Ensure pob-data files exist locally, fetching from GitHub if needed."""
    cache_path = POB_DATA_CACHE_PATH

    # Check if we need to fetch data
    needs_fetch = False
    if not cache_path.exists():
        needs_fetch = True
    else:
        # Check if essential files exist
        for filename in POB_DATA_FILES:
            if not (cache_path / filename).exists():
                needs_fetch = True
                break
        # Check if Bases directory exists and has files
        bases_dir = cache_path / "Bases"
        if not bases_dir.exists() or not list(bases_dir.glob("*.json")):
            needs_fetch = True

    if needs_fetch:
        logger.info("POB data not found locally, fetching from GitHub...")
        fetch_pob_data_from_github(cache_path)

    return cache_path


def fetch_pob_data_from_github(cache_path: Path) -> None:
    """Fetch pob-data files from GitHub."""
    # Create cache directories
    cache_path.mkdir(parents=True, exist_ok=True)
    bases_dir = cache_path / "Bases"
    bases_dir.mkdir(exist_ok=True)

    with httpx.Client(timeout=30.0) as client:
        # Fetch main JSON files
        for filename in POB_DATA_FILES:
            url = f"{GITHUB_RAW_BASE}/{filename}"
            logger.info(f"Fetching {filename}...")
            try:
                response = client.get(url)
                response.raise_for_status()

                file_path = cache_path / filename
                file_path.write_text(response.text, encoding="utf-8")
                logger.info(f"Saved {filename}")
            except Exception as e:
                logger.error(f"Failed to fetch {filename}: {e}")

        # Fetch Bases directory listing from GitHub API
        logger.info("Fetching Bases directory listing...")
        try:
            response = client.get(f"{GITHUB_API_BASE}/Bases")
            response.raise_for_status()
            files_list = response.json()

            # Fetch each base file
            for file_info in files_list:
                if file_info.get("name", "").endswith(".json"):
                    filename = file_info["name"]
                    download_url = file_info.get("download_url")
                    if download_url:
                        logger.info(f"Fetching Bases/{filename}...")
                        try:
                            file_response = client.get(download_url)
                            file_response.raise_for_status()

                            file_path = bases_dir / filename
                            file_path.write_text(file_response.text, encoding="utf-8")
                        except Exception as e:
                            logger.error(f"Failed to fetch Bases/{filename}: {e}")

            logger.info(f"Fetched {len(list(bases_dir.glob('*.json')))} base files")
        except Exception as e:
            logger.error(f"Failed to fetch Bases directory: {e}")

    logger.info("POB data fetch complete")


class POBDataLoader:
    """Loads and caches data from pob-data JSON files."""

    _instance: Optional["POBDataLoader"] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if POBDataLoader._initialized:
            return

        # Ensure pob-data exists (fetch if needed)
        self.pob_data_path = ensure_pob_data_exists()

        self._modifiers: List[ItemModifier] = []
        self._corrupted_mods: List[ItemModifier] = []
        self._desecrated_mods: List[ItemModifier] = []
        self._essence_mods: Dict[str, Dict[str, str]] = {}
        self._essences: Dict[str, EssenceInfo] = {}
        self._base_items: Dict[str, BaseItemInfo] = {}
        self._item_type_tags: Dict[str, List[str]] = {}
        self._mod_data: Dict[str, dict] = {}

        self._loaded = False
        POBDataLoader._initialized = True

    def load_all(self) -> None:
        """Load all data from pob-data files."""
        if self._loaded:
            return

        logger.info(f"Loading pob-data from: {self.pob_data_path}")

        # Load in order of dependency
        self._load_base_items()
        self._load_mod_item()
        self._load_mod_corrupted()
        self._load_mod_veiled()
        self._load_essences()

        # Renumber tiers so T1 = best (highest values)
        self._renumber_tiers_by_value()

        self._loaded = True
        logger.info(
            f"Loaded {len(self._modifiers)} regular mods, "
            f"{len(self._corrupted_mods)} corrupted mods, "
            f"{len(self._desecrated_mods)} desecrated mods, "
            f"{len(self._essences)} essences, "
            f"{len(self._base_items)} base items"
        )

    def reload(self) -> None:
        """Force reload all data."""
        self._modifiers = []
        self._corrupted_mods = []
        self._desecrated_mods = []
        self._essence_mods = {}
        self._essences = {}
        self._base_items = {}
        self._item_type_tags = {}
        self._mod_data = {}
        self._loaded = False
        self.load_all()

    def update_from_github(self) -> None:
        """Force update pob-data from GitHub and reload."""
        logger.info("Forcing update from GitHub...")
        fetch_pob_data_from_github(self.pob_data_path)
        self.reload()

    # =========================================================================
    # Data Loading Methods
    # =========================================================================

    def _load_base_items(self) -> None:
        """Load item bases from Bases/*.json files."""
        bases_dir = self.pob_data_path / "Bases"
        if not bases_dir.exists():
            logger.warning(f"Bases directory not found: {bases_dir}")
            return

        item_id = 1
        for json_file in bases_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    bases_data = json.load(f)

                for base_name, base_info in bases_data.items():
                    tags = base_info.get("tags", {})
                    tag_list = [tag for tag, enabled in tags.items() if enabled]
                    item_type = base_info.get("type", json_file.stem)

                    # Build item type -> tags mapping
                    if item_type not in self._item_type_tags:
                        self._item_type_tags[item_type] = tag_list.copy()
                    else:
                        for tag in tag_list:
                            if tag not in self._item_type_tags[item_type]:
                                self._item_type_tags[item_type].append(tag)

                    # Extract base stats
                    base_stats = {}
                    if "weapon" in base_info:
                        base_stats.update(base_info["weapon"])
                    if "armour" in base_info:
                        base_stats.update(base_info["armour"])

                    # Get required level and attributes
                    req = base_info.get("req", {})
                    if isinstance(req, dict):
                        required_level = req.get("level", 0)
                        required_str = req.get("str", 0)
                        required_dex = req.get("dex", 0)
                        required_int = req.get("int", 0)
                    else:
                        required_level = 0
                        required_str = 0
                        required_dex = 0
                        required_int = 0

                    # Build attribute requirements list
                    attr_reqs = []
                    if required_str > 0:
                        attr_reqs.append("str")
                    if required_dex > 0:
                        attr_reqs.append("dex")
                    if required_int > 0:
                        attr_reqs.append("int")

                    # Create implicit mod if present
                    implicit_mod = None
                    if "implicit" in base_info and base_info["implicit"]:
                        implicit_mod = ItemModifier(
                            name=f"{base_name} Implicit",
                            mod_type=ModType.IMPLICIT,
                            tier=1,
                            stat_text=base_info["implicit"],
                            stat_ranges=self._parse_stat_ranges(base_info["implicit"]),
                        )

                    # Determine category and slot from tags
                    category = self._determine_category(tag_list, item_type)
                    slot = self._determine_slot(tag_list, item_type, category)

                    self._base_items[base_name] = BaseItemInfo(
                        id=item_id,
                        name=base_name,
                        category=category,
                        subcategory=item_type,
                        base_stats=base_stats,
                        required_level=required_level,
                        implicit_mod=implicit_mod,
                    )

                    # Store extended info for item_bases.py compatibility
                    self._base_items[base_name]._slot = slot
                    self._base_items[base_name]._attribute_requirements = attr_reqs
                    self._base_items[base_name]._tags = tag_list

                    item_id += 1

            except Exception as e:
                logger.error(f"Error loading bases from {json_file}: {e}")

        logger.info(f"Loaded {len(self._base_items)} base items, {len(self._item_type_tags)} item types")

    def _load_mod_item(self) -> None:
        """Load regular mods from ModItem.json."""
        mod_file = self.pob_data_path / "ModItem.json"
        if not mod_file.exists():
            logger.error(f"ModItem.json not found: {mod_file}")
            return

        try:
            with open(mod_file, "r", encoding="utf-8") as f:
                mods_data = json.load(f)

            for mod_id, mod_info in mods_data.items():
                self._mod_data[mod_id] = mod_info
                modifier = self._convert_pob_mod_to_item_modifier(mod_id, mod_info)
                if modifier:
                    self._modifiers.append(modifier)

            logger.info(f"Loaded {len(self._modifiers)} regular modifiers")

        except Exception as e:
            logger.error(f"Error loading ModItem.json: {e}")

    def _load_mod_corrupted(self) -> None:
        """Load corrupted mods from ModCorrupted.json."""
        mod_file = self.pob_data_path / "ModCorrupted.json"
        if not mod_file.exists():
            logger.warning(f"ModCorrupted.json not found: {mod_file}")
            return

        try:
            with open(mod_file, "r", encoding="utf-8") as f:
                mods_data = json.load(f)

            for mod_id, mod_info in mods_data.items():
                self._mod_data[mod_id] = mod_info
                modifier = self._convert_pob_mod_to_item_modifier(
                    mod_id, mod_info, mod_type_override=ModType.IMPLICIT
                )
                if modifier:
                    modifier.tags = modifier.tags.copy()
                    modifier.tags.append("corrupted")
                    self._corrupted_mods.append(modifier)

            logger.info(f"Loaded {len(self._corrupted_mods)} corrupted modifiers")

        except Exception as e:
            logger.error(f"Error loading ModCorrupted.json: {e}")

    def _load_mod_veiled(self) -> None:
        """Load desecrated/abyss mods from ModVeiled.json."""
        mod_file = self.pob_data_path / "ModVeiled.json"
        if not mod_file.exists():
            logger.warning(f"ModVeiled.json not found: {mod_file}")
            return

        try:
            with open(mod_file, "r", encoding="utf-8") as f:
                mods_data = json.load(f)

            for mod_id, mod_info in mods_data.items():
                self._mod_data[mod_id] = mod_info
                # Preserve ranges for desecrated mods since they're guaranteed single-tier
                modifier = self._convert_pob_mod_to_item_modifier(
                    mod_id, mod_info, preserve_ranges=True
                )
                if modifier:
                    modifier.is_desecrated = True
                    modifier.tags = modifier.tags.copy()
                    modifier.tags.append("desecrated")
                    modifier.tags.append("desecrated_only")

                    # Tag with boss name (without _mod suffix)
                    mod_tags = mod_info.get("modTags", [])
                    boss_mapping = {
                        "amanamu_mod": "amanamu",
                        "kurgal_mod": "kurgal",
                        "ulaman_mod": "ulaman"
                    }
                    for old_tag, new_tag in boss_mapping.items():
                        if old_tag in mod_tags:
                            # Remove the _mod version if present, add clean version
                            if old_tag in modifier.tags:
                                modifier.tags.remove(old_tag)
                            if new_tag not in modifier.tags:
                                modifier.tags.append(new_tag)

                    self._desecrated_mods.append(modifier)

            logger.info(f"Loaded {len(self._desecrated_mods)} desecrated modifiers")

        except Exception as e:
            logger.error(f"Error loading ModVeiled.json: {e}")

    def _load_essences(self) -> None:
        """Load essence data from Essence.json."""
        essence_file = self.pob_data_path / "Essence.json"
        if not essence_file.exists():
            logger.warning(f"Essence.json not found: {essence_file}")
            return

        try:
            with open(essence_file, "r", encoding="utf-8") as f:
                essences_data = json.load(f)

            essence_id = 1
            for essence_path, essence_info in essences_data.items():
                name = essence_info.get("name", "Unknown Essence")
                essence_type = essence_info.get("type", "unknown")
                tier_level = essence_info.get("tierLevel", 1)
                mods = essence_info.get("mods", {})

                # Determine tier from name or tier_level
                tier = self._determine_essence_tier(name, tier_level)

                # Build item effects list
                item_effects = []
                effect_id = 1
                if isinstance(mods, dict):
                    for item_type, mod_id in mods.items():
                        mod_data = self._mod_data.get(mod_id)
                        if mod_data:
                            stat_text = mod_data.get("1", "")
                            mod_type_str = mod_data.get("type", "Prefix").lower()
                            value_min, value_max = self._extract_value_range(stat_text)

                            item_effects.append(EssenceItemEffectSchema(
                                id=effect_id,
                                essence_id=essence_id,
                                item_type=item_type,
                                modifier_type=mod_type_str if mod_type_str in ["prefix", "suffix"] else "prefix",
                                effect_text=stat_text,
                                value_min=value_min,
                                value_max=value_max,
                                mod_id=mod_id,  # Store direct reference to mod
                            ))
                            effect_id += 1

                self._essences[name] = EssenceInfo(
                    id=essence_id,
                    name=name,
                    essence_tier=tier,
                    essence_type=essence_type.lower(),
                    mechanic=self._determine_essence_mechanic(tier),
                    stack_size=10,
                    item_effects=item_effects,
                )

                if isinstance(mods, dict):
                    self._essence_mods[name] = mods

                essence_id += 1

            logger.info(f"Loaded {len(self._essences)} essences")

        except Exception as e:
            logger.error(f"Error loading Essence.json: {e}")

    # =========================================================================
    # Conversion Helpers
    # =========================================================================

    def _convert_pob_mod_to_item_modifier(
        self,
        mod_id: str,
        mod_info: dict,
        mod_type_override: Optional[ModType] = None,
        preserve_ranges: bool = False
    ) -> Optional[ItemModifier]:
        """Convert a pob-data mod entry to ItemModifier schema."""
        try:
            pob_type = mod_info.get("type", "Prefix")
            if mod_type_override:
                mod_type = mod_type_override
            elif pob_type == "Prefix":
                mod_type = ModType.PREFIX
            elif pob_type == "Suffix":
                mod_type = ModType.SUFFIX
            elif pob_type == "Corrupted":
                mod_type = ModType.IMPLICIT
            else:
                mod_type = ModType.PREFIX

            # Combine all stat lines (hybrid mods have multiple: "1", "2", "3", etc.)
            stat_lines = []
            for i in range(1, 10):  # Support up to 9 stats
                stat = mod_info.get(str(i))
                if stat:
                    stat_lines.append(stat)
                else:
                    break
            raw_stat_text = ", ".join(stat_lines) if stat_lines else ""
            stat_ranges = self._parse_stat_ranges(raw_stat_text)
            # Normalize stat_text by replacing range patterns with {} placeholders
            # e.g., "+(85-123) to Accuracy Rating" -> "+{} to Accuracy Rating"
            # For guaranteed mods (desecrated, essence-only), preserve the actual ranges
            if preserve_ranges:
                stat_text = raw_stat_text
            else:
                stat_text = self._normalize_stat_text(raw_stat_text)

            weight_key = mod_info.get("weightKey", [])
            weight_val = mod_info.get("weightVal", [])
            weight_conditions = None
            if weight_key and weight_val:
                weight_conditions = {
                    "weightKey": weight_key,
                    "weightVal": weight_val,
                }

            applicable_items = self._calculate_applicable_items(weight_key, weight_val)
            tier = self._extract_tier_from_id(mod_id)

            stat_min = stat_ranges[0].min if stat_ranges else None
            stat_max = stat_ranges[0].max if stat_ranges else None

            # Get mod group and base tags
            mod_group = mod_info.get("group")
            tags = mod_info.get("modTags", []).copy()

            # Special case: AbyssTargetMod (Mark of the Abyssal Lord) is essence-only
            # It can only be obtained through Essence of the Abyss
            if mod_group == "AbyssTargetMod":
                if "essence_only" not in tags:
                    tags.append("essence_only")
                if "essence_abyss" not in tags:
                    tags.append("essence_abyss")

            return ItemModifier(
                mod_id=mod_id,
                name=mod_info.get("affix", mod_id),
                mod_type=mod_type,
                tier=tier,
                stat_text=stat_text,
                stat_ranges=stat_ranges,
                stat_min=stat_min,
                stat_max=stat_max,
                required_ilvl=mod_info.get("level", 1),
                mod_group=mod_group,
                applicable_items=applicable_items,
                tags=tags,
                weight_conditions=weight_conditions,
                trade_hash=mod_info.get("tradeHash"),
                is_essence_only=mod_group == "AbyssTargetMod",
            )

        except Exception as e:
            logger.warning(f"Error converting mod {mod_id}: {e}")
            return None

    def _parse_stat_ranges(self, stat_text: str) -> List[StatRange]:
        """Parse stat ranges from stat text like 'Adds (3-4) to (5-8) Cold damage'."""
        ranges = []
        pattern = r'\((\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\)'
        matches = re.findall(pattern, stat_text)

        for match in matches:
            try:
                min_val = float(match[0])
                max_val = float(match[1])
                ranges.append(StatRange(min=min_val, max=max_val))
            except (ValueError, IndexError):
                pass

        return ranges

    def _normalize_stat_text(self, stat_text: str) -> str:
        """Normalize stat_text by replacing range patterns with {} placeholders.

        Converts pob-data format like '+(85-123) to Accuracy Rating'
        to placeholder format '+{} to Accuracy Rating' for pattern matching.
        """
        # Replace range patterns (X-Y) with {} placeholder
        pattern = r'\(\d+(?:\.\d+)?-\d+(?:\.\d+)?\)'
        return re.sub(pattern, '{}', stat_text)

    def _extract_value_range(self, stat_text: str) -> Tuple[Optional[float], Optional[float]]:
        """Extract first value range from stat text."""
        ranges = self._parse_stat_ranges(stat_text)
        if ranges:
            return ranges[0].min, ranges[0].max
        return None, None

    def _extract_tier_from_id(self, mod_id: str) -> int:
        """Extract tier number from mod ID (e.g., 'AddedColdDamage3' -> 3)."""
        match = re.search(r'(\d+)$', mod_id)
        if match:
            return int(match.group(1))
        return 1

    def _renumber_tiers_by_value(self) -> None:
        """
        Renumber tiers by stat values so T1 = highest values (best).

        Groups mods by (mod_group, mod_type) and sorts by stat_max descending.
        This matches POE convention where T1 = best tier with highest values.
        """
        # Process regular modifiers
        self._renumber_mod_list_tiers(self._modifiers)

        # Process corrupted mods
        self._renumber_mod_list_tiers(self._corrupted_mods)

        # Process desecrated mods
        self._renumber_mod_list_tiers(self._desecrated_mods)

        logger.info("Renumbered mod tiers (T1 = best)")

    def _renumber_mod_list_tiers(self, modifiers: List[ItemModifier]) -> None:
        """Renumber tiers for a list of modifiers."""
        # Group mods by (mod_group OR stat_text, mod_type)
        groups: Dict[tuple, List[ItemModifier]] = {}
        for mod in modifiers:
            # Use mod_group if available, otherwise fall back to stat_text
            group_key = mod.mod_group if mod.mod_group else mod.stat_text
            key = (group_key, mod.mod_type)
            if key not in groups:
                groups[key] = []
            groups[key].append(mod)

        # For each group, sort by stat_max descending and assign T1, T2, T3...
        for group_mods in groups.values():
            if len(group_mods) <= 1:
                # Single mod in group, assign T1
                if group_mods:
                    group_mods[0].tier = 1
                continue

            # Sort by stat_max descending (highest values first),
            # then by required_ilvl descending as tiebreaker
            sorted_mods = sorted(
                group_mods,
                key=lambda m: (
                    m.stat_max if m.stat_max is not None else 0,
                    m.required_ilvl  # Higher ilvl = better
                ),
                reverse=True
            )

            # Assign T1 to highest values, T2 to next, etc.
            for i, mod in enumerate(sorted_mods, start=1):
                mod.tier = i

    def _calculate_applicable_items(
        self,
        weight_key: List[str],
        weight_val: List[int]
    ) -> List[str]:
        """Calculate which item types a mod applies to based on weight conditions."""
        applicable = []
        for key, val in zip(weight_key, weight_val):
            if val > 0 and key != "default":
                applicable.append(key)
        return applicable

    def _determine_category(self, tags: List[str], item_type: str) -> str:
        """Determine item category from tags."""
        if "str_armour" in tags:
            return "str_armour"
        if "dex_armour" in tags:
            return "dex_armour"
        if "int_armour" in tags:
            return "int_armour"
        if "str_dex_armour" in tags:
            return "str_dex_armour"
        if "str_int_armour" in tags:
            return "str_int_armour"
        if "dex_int_armour" in tags:
            return "dex_int_armour"

        if "sword" in tags:
            return "sword"
        if "axe" in tags:
            return "axe"
        if "mace" in tags:
            return "mace"
        if "bow" in tags:
            return "bow"
        if "crossbow" in tags:
            return "crossbow"
        if "staff" in tags:
            return "staff"
        if "wand" in tags:
            return "wand"
        if "dagger" in tags:
            return "dagger"
        if "claw" in tags:
            return "claw"
        if "sceptre" in tags:
            return "sceptre"
        if "flail" in tags:
            return "flail"
        if "spear" in tags:
            return "spear"

        if "quiver" in tags:
            return "quiver"
        if "shield" in tags:
            return "shield"
        if "focus" in tags:
            return "focus"

        if "ring" in tags:
            return "ring"
        if "amulet" in tags:
            return "amulet"
        if "belt" in tags:
            return "belt"

        if "talisman" in tags:
            return "talisman"
        if "jewel" in tags:
            return "jewel"

        return item_type.lower().replace(" ", "_")

    def _determine_slot(self, tags: List[str], item_type: str, category: str) -> str:
        """Determine item slot from tags and type."""
        if "body_armour" in tags:
            return "body_armour"
        if "helmet" in tags:
            return "helmet"
        if "gloves" in tags:
            return "gloves"
        if "boots" in tags:
            return "boots"

        if "two_hand_weapon" in tags or "twohand" in tags:
            return "weapons - 2 hand"
        if "one_hand_weapon" in tags or "weapon" in tags:
            if "Two Hand" in item_type or "two_hand" in category:
                return "weapons - 2 hand"
            return "weapons - 1 hand"

        if "quiver" in tags or "shield" in tags or "focus" in tags:
            return "offhand"

        if category in ["ring", "amulet", "belt"]:
            return category

        if "jewel" in tags:
            return "jewel"

        return category

    def _determine_essence_tier(self, name: str, tier_level: int) -> str:
        """Determine essence tier from name."""
        name_lower = name.lower()
        if "lesser" in name_lower:
            return "lesser"
        elif "greater" in name_lower:
            return "greater"
        elif "perfect" in name_lower:
            return "perfect"
        elif any(x in name_lower for x in ["delirium", "horror", "hysteria", "insanity", "abyss"]):
            return "corrupted"
        else:
            return "normal"

    def _determine_essence_mechanic(self, tier: str) -> str:
        """Determine essence mechanic from tier.

        Per CRAFTING_SYSTEM_DESIGN.md:
        - Lesser, Normal, Greater: Upgrade Magic → Rare with guaranteed mod
        - Perfect, Corrupted: Remove random mod + add guaranteed mod on Rare
        """
        if tier in ["lesser", "normal", "greater"]:
            return "magic_to_rare"
        elif tier in ["perfect", "corrupted"]:
            return "remove_add_rare"
        return "magic_to_rare"

    # =========================================================================
    # Public Accessor Methods
    # =========================================================================

    def get_all_modifiers(self) -> List[ItemModifier]:
        """Get all regular craftable modifiers."""
        if not self._loaded:
            self.load_all()
        return self._modifiers

    def get_corrupted_modifiers(self) -> List[ItemModifier]:
        """Get all corrupted implicit modifiers."""
        if not self._loaded:
            self.load_all()
        return self._corrupted_mods

    def get_desecrated_modifiers(self) -> List[ItemModifier]:
        """Get all desecrated/abyss modifiers."""
        if not self._loaded:
            self.load_all()
        return self._desecrated_mods

    def get_all_modifiers_combined(self) -> List[ItemModifier]:
        """Get all modifiers including regular, corrupted, and desecrated."""
        if not self._loaded:
            self.load_all()
        return self._modifiers + self._corrupted_mods + self._desecrated_mods

    def get_essences(self) -> Dict[str, EssenceInfo]:
        """Get all essence definitions keyed by name."""
        if not self._loaded:
            self.load_all()
        return self._essences

    def get_essence_by_name(self, name: str) -> Optional[EssenceInfo]:
        """Get essence by display name."""
        if not self._loaded:
            self.load_all()
        return self._essences.get(name)

    def get_base_items(self) -> Dict[str, BaseItemInfo]:
        """Get all base item definitions."""
        if not self._loaded:
            self.load_all()
        return self._base_items

    def get_base_item(self, name: str) -> Optional[BaseItemInfo]:
        """Get base item by name."""
        if not self._loaded:
            self.load_all()
        return self._base_items.get(name)

    def get_item_type_tags(self, item_type: str) -> List[str]:
        """Get tags for a specific item type."""
        if not self._loaded:
            self.load_all()
        return self._item_type_tags.get(item_type, [])

    def get_mod_for_essence(self, essence_name: str, item_type: str) -> Optional[str]:
        """Get the mod ID that an essence grants for a specific item type."""
        if not self._loaded:
            self.load_all()
        essence_mods = self._essence_mods.get(essence_name, {})
        return essence_mods.get(item_type)

    def get_mod_data(self, mod_id: str) -> Optional[dict]:
        """Get raw mod data by ID (for looking up essence mod details)."""
        if not self._loaded:
            self.load_all()
        return self._mod_data.get(mod_id)

    def get_modifier_by_id(self, mod_id: str) -> Optional[ItemModifier]:
        """Get an ItemModifier by its mod ID (e.g., from Essence.json mods mapping).

        This is used for essence mods which have weightVal: [0] and aren't in the
        normal modifier pool, but are referenced directly by ID in Essence.json.
        """
        if not self._loaded:
            self.load_all()

        mod_data = self._mod_data.get(mod_id)
        if not mod_data:
            return None

        return self._convert_pob_mod_to_item_modifier(mod_id, mod_data)

    def get_modifiers_for_item_tags(self, item_tags: List[str]) -> List[ItemModifier]:
        """Get all modifiers that can roll on an item with given tags."""
        if not self._loaded:
            self.load_all()

        matching_mods = []
        for mod in self._modifiers:
            if self._mod_matches_tags(mod, item_tags):
                matching_mods.append(mod)

        return matching_mods

    def _mod_matches_tags(self, mod: ItemModifier, item_tags: List[str]) -> bool:
        """Check if a modifier can apply to an item with given tags."""
        if not mod.weight_conditions:
            return False

        weight_keys = mod.weight_conditions.get("weightKey", [])
        weight_vals = mod.weight_conditions.get("weightVal", [])

        for key, val in zip(weight_keys, weight_vals):
            if key in item_tags and val > 0:
                return True

        return False


# Singleton instance
_loader: Optional[POBDataLoader] = None


def get_pob_data_loader() -> POBDataLoader:
    """Get the singleton POB data loader instance."""
    global _loader
    if _loader is None:
        _loader = POBDataLoader()
    return _loader
