import random
import json
import os
from typing import List, Optional

from app.schemas.crafting import ItemModifier, ModType
from app.services.crafting.exclusion_service import exclusion_service
from app.core.item_classification import (
    ALL_WEAPON_CATEGORIES,
    ONE_HANDED_WEAPONS,
    TWO_HANDED_WEAPONS,
    ALL_ARMOR_CATEGORIES,
    JEWELRY_CATEGORIES,
    CASTER_WEAPONS,
    ARMOR_DEFENSE_PATTERNS,
    POB_TO_DB_CATEGORY,
    classify_item,
)


def _get_item_slot(base_name: str) -> Optional[str]:
    """Get item slot from base name using item_bases module (no database)."""
    from app.schemas.item_bases import get_item_base_by_name
    base_item = get_item_base_by_name(base_name)
    if base_item:
        return base_item.slot
    return None


def _get_item_tags(item) -> List[str]:
    """
    Get item tags from the item's base.

    This includes the defense type (e.g., dex_int_armour) which is needed
    for weight key matching on armor pieces.
    """
    if not item or not hasattr(item, 'base_name'):
        return []

    # Try to get the base item info which has the actual category (defense type)
    try:
        from app.services.crafting.pob_data_loader import get_pob_data_loader
        loader = get_pob_data_loader()
        base_items = loader.get_base_items()
        base_info = base_items.get(item.base_name)

        if base_info:
            tags = []
            # The category field contains the defense type (e.g., dex_int_armour) or weapon
            # class (e.g., warstaff).
            if base_info.category:
                tags.append(base_info.category)
            # NOTE: we deliberately do NOT add base_info.subcategory. For weapons it is the
            # coarse pob "type" - "Staff" for BOTH quarterstaves and caster staves - which
            # wrongly stamped a "staff" tag onto quarterstaves and leaked caster spell mods onto
            # them. category + slot already cover everything weight-key matching needs.
            if hasattr(base_info, '_slot') and base_info._slot:
                tags.append(base_info._slot)
            # Add generic 'armour' tag if this is an armor piece
            if base_info.category in ALL_ARMOR_CATEGORIES:
                tags.append('armour')
            return list(set(tags))
    except Exception:
        pass

    return []


class ModifierPool:
    def __init__(self, modifiers: List[ItemModifier]) -> None:
        self.modifiers = modifiers
        # NOTE: Legacy exclusion groups code disabled - now using exclusion_service instead
        # self._exclusion_groups_config = self._load_exclusion_groups()
        # self._apply_exclusion_groups()  # Apply exclusion groups to all modifiers
        self._prefix_pool = [m for m in modifiers if m.mod_type == ModType.PREFIX]
        self._suffix_pool = [m for m in modifiers if m.mod_type == ModType.SUFFIX]
        self._exclusions = self._load_exclusions()

    def _load_exclusions(self) -> List[dict]:
        """Load modifier exclusions from JSON file."""
        try:
            # Go up from app/services/crafting to backend, then to source_data
            exclusions_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                "source_data",
                "modifier_exclusions.json"
            )
            if os.path.exists(exclusions_path):
                with open(exclusions_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load modifier exclusions: {e}")
        return []

    def _load_exclusion_groups(self) -> dict:
        """Load exclusion groups configuration from JSON file."""
        try:
            # Go up from app/services/crafting to backend, then to source_data
            groups_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                "source_data",
                "exclusion_groups.json"
            )
            if os.path.exists(groups_path):
                with open(groups_path, 'r') as f:
                    data = json.load(f)
                    return data.get("groups", {})
        except Exception as e:
            print(f"Warning: Could not load exclusion groups: {e}")
        return {}

    def _apply_exclusion_groups(self) -> None:
        """Apply exclusion group numbers to all modifiers based on matching rules."""
        if not self._exclusion_groups_config:
            return

        # Iterate through each modifier and check if it matches any exclusion group
        for mod in self.modifiers:
            for group_id, group_data in self._exclusion_groups_config.items():
                rules = group_data.get("rules", [])

                # Check if modifier matches any rule in this group
                for rule in rules:
                    match_type = rule.get("match_type")
                    pattern = rule.get("pattern")

                    if match_type == "mod_group" and mod.mod_group:
                        if mod.mod_group.lower() == pattern.lower():
                            mod.exclusion_group = int(group_id)
                            break  # Move to next modifier once matched
                    elif match_type == "stat_text":
                        if pattern in mod.stat_text:
                            mod.exclusion_group = int(group_id)
                            break  # Move to next modifier once matched

                # If we assigned a group, no need to check other groups
                if mod.exclusion_group is not None:
                    break

    def _apply_exclusions(self, mods: List[ItemModifier], item_slot: Optional[str]) -> List[ItemModifier]:
        """Apply exclusions based on item slot and modifier stat text."""
        if not item_slot or not self._exclusions:
            return mods

        filtered_mods = []
        for mod in mods:
            should_exclude = False
            for exclusion in self._exclusions:
                if exclusion["stat_text"] == mod.stat_text:
                    if item_slot in exclusion["exclude_from"]:
                        should_exclude = True
                        break
            if not should_exclude:
                filtered_mods.append(mod)

        return filtered_mods

    def roll_random_modifier(
        self,
        mod_type: str,
        item_category: str,
        item_level: int,
        excluded_groups: Optional[List[str]] = None,
        min_mod_level: Optional[int] = None,
        item=None,
    ) -> Optional[ItemModifier]:
        pool = self._prefix_pool if mod_type == "prefix" else self._suffix_pool

        # If item is provided, get excluded groups, tags, and patterns from item
        if item is not None:
            if excluded_groups is None:
                excluded_groups = self._get_excluded_groups_from_item(item)
            excluded_tags = self._get_excluded_tags_from_item(item, mod_type)
            excluded_patterns = self._get_excluded_patterns_from_item(item, mod_type)
        else:
            excluded_tags = []
            excluded_patterns = []

        eligible_mods = self._filter_eligible_mods(
            pool, item_category, item_level, excluded_groups or [], min_mod_level, excluded_tags=excluded_tags, excluded_patterns=excluded_patterns, exclude_desecrated=True, exclude_essence=True, item=item, mod_type=mod_type
        )

        if not eligible_mods:
            return None

        return self._weighted_random_choice(eligible_mods)

    def _filter_eligible_mods(
        self,
        pool: List[ItemModifier],
        item_category: str,
        item_level: int,
        excluded_groups: List[str],
        min_mod_level: Optional[int] = None,
        exclude_exclusive: bool = True,
        excluded_tags: Optional[List[str]] = None,
        excluded_patterns: Optional[List[str]] = None,
        exclude_desecrated: bool = True,
        exclude_essence: bool = False,
        item=None,
        mod_type: str = "prefix",  # Added to support exclusion service
    ) -> List[ItemModifier]:
        eligible = []

        # Get excluded exclusion groups from item if provided
        excluded_exclusion_groups = []
        if item is not None:
            excluded_exclusion_groups = self._get_excluded_exclusion_groups_from_item(item)

        for mod in pool:
            if mod.required_ilvl and mod.required_ilvl > item_level:
                continue

            if min_mod_level and mod.required_ilvl and mod.required_ilvl < min_mod_level:
                continue

            if mod.mod_group and mod.mod_group in excluded_groups:
                continue

            # Check exclusion group conflicts
            if mod.exclusion_group is not None and mod.exclusion_group in excluded_exclusion_groups:
                continue

            # Check for tag-based exclusions
            if excluded_tags and mod.tags:
                has_excluded_tag = any(tag in excluded_tags for tag in mod.tags)
                if has_excluded_tag:
                    continue

            # Check for pattern-based exclusions
            if excluded_patterns:
                has_excluded_pattern = any(pattern in mod.stat_text for pattern in excluded_patterns)
                if has_excluded_pattern:
                    continue

            if not mod.applicable_items:
                continue

            # Exclude desecrated-only mods unless specifically allowed (only for desecration mechanics)
            if exclude_desecrated and mod.tags and "desecrated_only" in mod.tags:
                continue

            # Exclude essence-only mods if requested
            if exclude_essence and mod.tags and "essence_only" in mod.tags:
                continue

            # Exclude mods marked as exclusive-only (unique items only), but allow essence-only mods
            if exclude_exclusive and mod.is_exclusive and "essence_only" not in mod.tags:
                continue

            # Manual override for known unique-only mod groups
            if exclude_exclusive and self._is_unique_only_mod_group(mod.mod_group, item_category):
                continue

            if not self._is_mod_applicable_to_category(mod, item_category, item):
                continue

            eligible.append(mod)

        # Apply pattern-based exclusion rules from exclusion_groups.json
        if item is not None:
            existing_mods = item.prefix_mods + item.suffix_mods
            eligible = exclusion_service.filter_available_mods(
                eligible, existing_mods, item_category, mod_type
            )

        return eligible

    def _weighted_random_choice(
        self, modifiers: List[ItemModifier]
    ) -> Optional[ItemModifier]:
        if not modifiers:
            return None

        # Filter out zero-weight modifiers (handle weight as int or str)
        weighted_mods = []
        for mod in modifiers:
            try:
                weight = int(mod.weight) if isinstance(mod.weight, str) else mod.weight
                if weight > 0:
                    weighted_mods.append(mod)
            except (ValueError, TypeError):
                # Skip mods with invalid weights
                continue

        if not weighted_mods:
            return None

        total_weight = sum(int(mod.weight) if isinstance(mod.weight, str) else mod.weight for mod in weighted_mods)

        if total_weight == 0:
            return None

        rand_value = random.uniform(0, total_weight)
        cumulative = 0

        for mod in weighted_mods:
            weight = int(mod.weight) if isinstance(mod.weight, str) else mod.weight
            cumulative += weight
            if rand_value <= cumulative:
                rolled_mod = mod.model_copy()

                # Roll values for hybrid modifiers (multiple stat ranges, rounded to integers)
                if rolled_mod.stat_ranges and len(rolled_mod.stat_ranges) > 0:
                    rolled_mod.current_values = [
                        round(random.uniform(stat_range.min, stat_range.max))
                        for stat_range in rolled_mod.stat_ranges
                    ]
                    # Set legacy current_value to first value for backwards compatibility
                    rolled_mod.current_value = rolled_mod.current_values[0]
                # Fall back to legacy single value for older mods
                elif rolled_mod.stat_min is not None and rolled_mod.stat_max is not None:
                    rolled_mod.current_value = round(random.uniform(
                        rolled_mod.stat_min, rolled_mod.stat_max
                    ))

                return rolled_mod

        # Fallback to last weighted modifier if we somehow didn't select one
        if weighted_mods:
            fallback_mod = weighted_mods[-1].model_copy()
            # Roll values for fallback mod too
            if fallback_mod.stat_ranges and len(fallback_mod.stat_ranges) > 0:
                fallback_mod.current_values = [
                    round(random.uniform(stat_range.min, stat_range.max))
                    for stat_range in fallback_mod.stat_ranges
                ]
                fallback_mod.current_value = fallback_mod.current_values[0]
            elif fallback_mod.stat_min is not None and fallback_mod.stat_max is not None:
                fallback_mod.current_value = round(random.uniform(
                    fallback_mod.stat_min, fallback_mod.stat_max
                ))
            return fallback_mod
        return None

    def _is_unique_only_mod_group(self, mod_group: Optional[str], item_category: str = "") -> bool:
        """Check if a mod group is known to be unique-only"""
        if not mod_group:
            return False

        # Known unique-only mod groups based on game knowledge
        unique_only_groups = {
            # Add unique-only groups here as discovered
        }

        # Item-specific restrictions based on game knowledge
        # These mods exist for some item types but not others
        if item_category in ALL_ARMOR_CATEGORIES or item_category == 'body_armour':
            # Body armor cannot roll recharge rate mods (only helmet/gloves/boots can)
            body_armor_restricted = {'energyshieldregeneration'}
            if mod_group and mod_group.lower() in body_armor_restricted:
                return True

        return mod_group.lower() in unique_only_groups

    def get_mods_by_group(self, group: str) -> List[ItemModifier]:
        return [m for m in self.modifiers if m.mod_group == group]

    def get_mods_by_type(self, mod_type: ModType) -> List[ItemModifier]:
        return [m for m in self.modifiers if m.mod_type == mod_type]

    def find_mod_by_name(self, name: str) -> Optional[ItemModifier]:
        for mod in self.modifiers:
            if mod.name.lower() == name.lower():
                return mod
        return None

    def find_mod_by_name_and_tier(self, name: str, tier: int) -> Optional[ItemModifier]:
        for mod in self.modifiers:
            if mod.name.lower() == name.lower() and mod.tier == tier:
                return mod
        return None

    def get_desecrated_only_mods(
        self,
        item_category: str,
        mod_type: str,
        item_level: int = None,
        item=None
    ) -> List[ItemModifier]:
        """Get modifiers that are marked as 'desecrated_only' - only available through desecration."""
        pool = self._prefix_pool if mod_type == "prefix" else self._suffix_pool

        desecrated_mods = []
        for mod in pool:
            # Only include mods marked as desecrated_only
            if not (mod.tags and "desecrated_only" in mod.tags):
                continue

            # Check item level requirements if specified
            if item_level and mod.required_ilvl and mod.required_ilvl > item_level:
                continue

            # Check if mod applies to this item category
            if not self._modifier_applies_to_item(mod, item) if item else not self._is_mod_applicable_to_category(mod, item_category):
                continue

            desecrated_mods.append(mod)

        return desecrated_mods

    def get_eligible_mods(
        self,
        item_category: str,
        item_level: int,
        mod_type: str,
        item=None,
        exclude_exclusive: bool = True,
        min_mod_level: int = None,
        exclude_desecrated: bool = True,
        exclude_essence: bool = False,
    ) -> List[ItemModifier]:
        pool = self._prefix_pool if mod_type == "prefix" else self._suffix_pool

        excluded_groups = []
        excluded_tags = []
        excluded_patterns = []
        if item:
            all_mods = item.prefix_mods + item.suffix_mods
            excluded_groups = [mod.mod_group for mod in all_mods if mod.mod_group]
            excluded_tags = self._get_excluded_tags_from_item(item, mod_type)
            excluded_patterns = self._get_excluded_patterns_from_item(item, mod_type)

        eligible = self._filter_eligible_mods(
            pool, item_category, item_level, excluded_groups, None, exclude_exclusive, excluded_tags, excluded_patterns, exclude_desecrated=exclude_desecrated, exclude_essence=exclude_essence, item=item, mod_type=mod_type
        )

        # Filter out mods that would conflict with existing mods via exclusion groups
        if item:
            existing_mods = item.prefix_mods + item.suffix_mods
            eligible = exclusion_service.filter_available_mods(
                eligible, existing_mods, item_category, mod_type
            )

        # Filter by min_mod_level if specified
        if min_mod_level is not None:
            eligible = [mod for mod in eligible if (mod.required_ilvl or 0) >= min_mod_level]

        # Get item slot for exclusions
        item_slot = None
        if item:
            item_slot = _get_item_slot(item.base_name)

        # Apply exclusions based on slot
        return self._apply_exclusions(eligible, item_slot)

    def get_all_mods_for_category(
        self,
        item_category: str,
        mod_type: str,
        item=None,
        exclude_exclusive: bool = True,
    ) -> List[ItemModifier]:
        """Get ALL mods for a category, regardless of item level (for display purposes)"""
        pool = self._prefix_pool if mod_type == "prefix" else self._suffix_pool

        excluded_groups = []
        excluded_tags = []
        excluded_exclusion_groups = []
        if item:
            all_mods = item.prefix_mods + item.suffix_mods
            excluded_groups = [mod.mod_group for mod in all_mods if mod.mod_group]
            excluded_tags = self._get_excluded_tags_from_item(item, mod_type)
            excluded_exclusion_groups = self._get_excluded_exclusion_groups_from_item(item)

        # Get excluded patterns if item is provided
        excluded_patterns = []
        if item:
            excluded_patterns = self._get_excluded_patterns_from_item(item, mod_type)

        eligible = []
        for mod in pool:
            if mod.mod_group and mod.mod_group in excluded_groups:
                continue

            # Check exclusion group conflicts
            if mod.exclusion_group is not None and mod.exclusion_group in excluded_exclusion_groups:
                continue

            # Check for tag-based exclusions
            if excluded_tags and mod.tags:
                has_excluded_tag = any(tag in excluded_tags for tag in mod.tags)
                if has_excluded_tag:
                    continue

            # Check for pattern-based exclusions
            if excluded_patterns:
                has_excluded_pattern = any(pattern in mod.stat_text for pattern in excluded_patterns)
                if has_excluded_pattern:
                    continue

            # Skip mods with empty applicable_items unless they're special essence-only mods
            if not mod.applicable_items and mod.mod_group != "AbyssTargetMod":
                continue

            if exclude_exclusive and mod.is_exclusive and "essence_only" not in mod.tags and "desecrated_only" not in mod.tags and "alloy_only" not in mod.tags:
                continue

            if exclude_exclusive and self._is_unique_only_mod_group(mod.mod_group, item_category):
                continue

            # Check if mod applies to this item category
            # For defence mods, be more specific based on mod group
            if not self._is_mod_applicable_to_category(mod, item_category, item):
                continue

            eligible.append(mod)

        # Apply pattern-based exclusion rules from exclusion_groups.json
        if item is not None:
            existing_mods = item.prefix_mods + item.suffix_mods
            eligible = exclusion_service.filter_available_mods(
                eligible, existing_mods, item_category, mod_type
            )

        # Get item slot for exclusions
        item_slot = None
        if item:
            item_slot = _get_item_slot(item.base_name)

        # Apply exclusions based on slot
        eligible = self._apply_exclusions(eligible, item_slot)

        # Deduplicate mods based on (stat_text, tier, mod_type, special_tag) to avoid duplicate entries
        # This handles cases where the same mod exists with different names or applicable_items lists
        # Prefer mods with specific weapon types over generic 'weapon' tag
        # Keep essence_only and desecrated_only mods separate even if they have the same stat_text
        seen_mods = {}
        for mod in eligible:
            # Use stat_text instead of name to catch mods with same effect but different names
            # (e.g., "of the Abyss" vs "Abyssal" both giving "Bears the Mark of the Abyssal Lord")
            # Include essence_only/desecrated_only in key to prevent deduplication between them
            special_tag = None
            if "essence_only" in mod.tags:
                special_tag = "essence_only"
            elif "desecrated_only" in mod.tags:
                special_tag = "desecrated_only"
            key = (mod.stat_text, mod.tier, mod.mod_type, special_tag)

            # If we haven't seen this mod yet, add it
            if key not in seen_mods:
                seen_mods[key] = mod
            else:
                # If we have seen it, prefer the more specific one (not using generic 'weapon' tag)
                existing_mod = seen_mods[key]
                has_generic_weapon = "weapon" in mod.applicable_items and not any(
                    w in mod.applicable_items for w in ALL_WEAPON_CATEGORIES
                )
                existing_has_generic = "weapon" in existing_mod.applicable_items and not any(
                    w in existing_mod.applicable_items for w in ALL_WEAPON_CATEGORIES
                )

                # Keep the more specific one (the one NOT using generic weapon tag)
                if has_generic_weapon and not existing_has_generic:
                    # Keep existing (it's more specific)
                    pass
                elif not has_generic_weapon and existing_has_generic:
                    # Replace with current (it's more specific)
                    seen_mods[key] = mod

        return list(seen_mods.values())

    def _get_item_elemental_exclusions(self, item) -> list:
        """
        Determine which elemental damage types should be excluded for this item.
        Based on the item's implicit skill (for staffs/wands/focuses).

        Returns list of exclusion tags like ["no_cold_spell_mods", "no_lightning_spell_mods"]
        """
        if not item:
            return []

        # Read implicit from JSON file (not in database model yet)
        import json
        import os

        # Get path to item bases JSON
        json_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "source_data",
            "generated_item_bases.json"
        )

        if not os.path.exists(json_path):
            return []

        try:
            with open(json_path, 'r') as f:
                bases = json.load(f)

            # Find base item
            base_item = next((b for b in bases if b.get('name') == item.base_name), None)
            if not base_item or not base_item.get('implicit'):
                return []

            implicit = base_item['implicit'].lower()
        except Exception:
            return []

        # Map implicit skills to their primary element
        fire_skills = ["firebolt", "solar orb", "flame wall", "magma barrier"]
        cold_skills = ["freezing shards", "heart of ice", "frost wall", "ice nova"]
        lightning_skills = ["lightning bolt", "spark", "storm wave", "enervating nova", "galvanic field"]
        chaos_skills = ["soulrend", "reap", "dark pact", "feast of flesh", "profane ritual",
                       "chaos bolt", "decompose", "wither", "exsanguinate", "bone blast"]
        physical_skills = ["bone storm", "boneshatter", "volatile dead"]

        # Determine item's element
        item_element = None
        if any(skill in implicit for skill in fire_skills):
            item_element = "fire"
        elif any(skill in implicit for skill in cold_skills):
            item_element = "cold"
        elif any(skill in implicit for skill in lightning_skills):
            item_element = "lightning"
        elif any(skill in implicit for skill in chaos_skills):
            item_element = "chaos"
        elif any(skill in implicit for skill in physical_skills):
            item_element = "physical"

        # Return exclusions for OTHER elements (not the item's own element)
        all_exclusions = {
            "fire": "no_fire_spell_mods",
            "cold": "no_cold_spell_mods",
            "lightning": "no_lightning_spell_mods",
            "chaos": "no_chaos_spell_mods",
            "physical": "no_physical_spell_mods"
        }

        if item_element:
            # Exclude all elements EXCEPT the item's own element
            return [tag for elem, tag in all_exclusions.items() if elem != item_element]

        return []

    def _item_matches_weight_key(self, weight_key: str, item_category: str, item_slot: str, item=None) -> bool:
        """
        Check if an item matches a specific weightKey string from PoB2.

        Args:
            weight_key: The weightKey string to check (e.g., "ranged", "two_hand_weapon", "bow")
            item_category: The item's category (e.g., "bow", "sword", "str_armour")
            item_slot: The item's slot (e.g., "weapons - 2 hand", "body_armour")
            item: Optional item instance for elemental exclusion checks

        Returns:
            True if the item matches this weightKey
        """
        # === Elemental Exclusion Tags ===
        # Check if weight_key is an elemental exclusion tag (no_fire_spell_mods, etc.)
        if weight_key.startswith("no_") and weight_key.endswith("_spell_mods"):
            exclusions = self._get_item_elemental_exclusions(item)
            return weight_key in exclusions

        # Use centralized classification system for all other checks
        # Get item tags from base - critical for armor defense type matching (e.g., dex_int_armour)
        item_tags = _get_item_tags(item) if item else None
        classification = classify_item(item_category, item_slot, tags=item_tags)
        return classification.matches_weight_key(weight_key)

    def _check_weight_condition(self, weight_conditions: dict, item_category: str, item_slot: str, item=None) -> bool:
        """
        Evaluate if a mod can spawn on an item using PoB2's weight system.

        Algorithm (FIRST MATCH WINS):
        1. Iterate through weightKey array in order
        2. Check if item matches each weight key
        3. On FIRST match, use corresponding weightVal
        4. Return True if weight > 0, False if weight = 0

        Args:
            weight_conditions: Dict with "weightKey" and "weightVal" arrays
            item_category: The item's category
            item_slot: The item's slot
            item: Optional item instance for elemental exclusion checks

        Returns:
            True if mod can spawn (weight > 0), False otherwise
        """
        return self._get_weight_for_item(weight_conditions, item_category, item_slot, item) > 0

    def _get_weight_for_item(self, weight_conditions: dict, item_category: str, item_slot: str, item=None) -> int:
        """
        Get the effective weight of a mod for a specific item.

        Algorithm (FIRST MATCH WINS):
        1. Iterate through weightKey array in order
        2. Check if item matches each weight key
        3. On FIRST match, return corresponding weightVal

        Args:
            weight_conditions: Dict with "weightKey" and "weightVal" arrays
            item_category: The item's category
            item_slot: The item's slot
            item: Optional item instance for elemental exclusion checks

        Returns:
            The weight value for this item, or 0 if no match
        """
        weight_keys = weight_conditions.get("weightKey", [])
        weight_vals = weight_conditions.get("weightVal", [])

        if not weight_keys or not weight_vals:
            return 0

        # Iterate in order - FIRST MATCH WINS
        for i, weight_key in enumerate(weight_keys):
            if self._item_matches_weight_key(weight_key, item_category, item_slot, item):
                # First match found - use this weight
                return weight_vals[i] if i < len(weight_vals) else 0

        # No match (shouldn't happen if "default" is always in weightKey)
        return 0

    def get_effective_weight(self, mod: ItemModifier, item) -> int:
        """
        Get the effective weight of a modifier for a specific item.

        Uses weights.csv (real game weights) if available, otherwise defaults to 100.
        Note: pob-data weightVal is just 1/0 (can/can't spawn), not actual weights.

        Args:
            mod: The modifier to check
            item: The item to check against

        Returns:
            The effective weight for this mod on this item
        """
        # Try to get weight from weights.csv (real game data)
        from app.services.crafting.weights_loader import get_weights_loader
        weights_loader = get_weights_loader()

        mod_type = "prefix" if mod.mod_type.value == "prefix" else "suffix"
        csv_weight = weights_loader.get_weight(
            item_category=item.base_category,
            mod_type=mod_type,
            stat_text=mod.stat_text,
            tier=mod.tier,
            item_tags=getattr(item, 'tags', None)
        )

        if csv_weight is not None:
            return csv_weight

        # Default fallback - we don't have real weight data for this mod
        return 100

    def _is_mod_applicable_to_category(self, mod: ItemModifier, item_category: str, item=None) -> bool:
        """Check if a mod is applicable to an item category"""

        # Get slot from item if available
        item_slot = None
        if item:
            # Determine slot from base_name if we have the item
            item_slot = _get_item_slot(item.base_name)

        # Special case: AbyssTargetMod (Mark of the Abyssal Lord) applies to any item
        # It has weight 0 and empty applicable_items but can be added via Essence of the Abyss
        if mod.mod_group == "AbyssTargetMod":
            return True

        # === Use weight system if available ===
        # If mod has weight_conditions, use PoB2's exact weight evaluation
        if mod.weight_conditions and item_slot:
            return self._check_weight_condition(mod.weight_conditions, item_category, item_slot, item)
        
        # === Fallback to old system for mods without weight_conditions ===
        # (essence-only, desecrated, or old data without weight info)
        
        # Check if category matches directly
        if item_category in mod.applicable_items:
            return True

        # Handle weapon type mapping based on slot
        # Mods use multiple patterns:
        # - "weapon" (generic, applies to ALL weapons)
        # - "one_hand_weapon" / "two_hand_weapon" (applies to all 1h or 2h weapons)
        # - specific types like "one_hand_sword", "two_hand_axe"
        if item_slot == "weapons - 1 hand":
            # Check generic weapon tag (applies to all weapons)
            if "weapon" in mod.applicable_items:
                return True

            # Map specific weapon types to one_hand_weapon
            if item_category in ONE_HANDED_WEAPONS:
                # Check generic one_hand_weapon tag
                if "one_hand_weapon" in mod.applicable_items:
                    return True
                # Check specific weapon type with underscore (e.g., "one_hand_sword")
                specific_type = f"one_hand_{item_category}"
                if specific_type in mod.applicable_items:
                    return True
            # Also check if the category is directly listed
            if item_category in mod.applicable_items:
                return True
        elif item_slot == "weapons - 2 hand":
            # Check generic weapon tag (applies to all weapons)
            if "weapon" in mod.applicable_items:
                return True

            # Map specific weapon types to two_hand_weapon
            if item_category in TWO_HANDED_WEAPONS:
                # Check generic two_hand_weapon tag
                if "two_hand_weapon" in mod.applicable_items:
                    return True
                # Check specific weapon type with underscore (e.g., "two_hand_sword")
                specific_type = f"two_hand_{item_category}"
                if specific_type in mod.applicable_items:
                    return True
            # Also check if the category is directly listed
            if item_category in mod.applicable_items:
                return True

        # Handle talismans - they use two-hand weapon mods
        if item_category == "talisman":
            # Check generic weapon and two_hand_weapon tags
            if "weapon" in mod.applicable_items:
                return True
            if "two_hand_weapon" in mod.applicable_items:
                return True
            # Check if talisman is directly listed
            if "talisman" in mod.applicable_items:
                return True

        # Handle "jewellery" category - expands to amulet, ring, belt
        if "jewellery" in mod.applicable_items:
            if item_slot in JEWELRY_CATEGORIES:
                return True

        # Check if slot matches (for slot-specific mods)
        # BUT for body_armour slot, need to check defence type filtering first
        if item_slot and item_slot in mod.applicable_items:
            # Special handling for body_armour slot: check defence type compatibility
            if item_slot == "body_armour" and item_category in ALL_ARMOR_CATEGORIES:
                # Check if this is a defence % mod (these are stat-specific)
                if "% increased" in mod.stat_text:
                    # Get expected defence patterns for this armour type from centralized config
                    expected_patterns = ARMOR_DEFENSE_PATTERNS.get(item_category, [])

                    # Check if the mod matches any expected pattern
                    for pattern in expected_patterns:
                        if pattern in mod.stat_text:
                            return True

                    # If it's a defence % mod but doesn't match, reject it
                    if any(def_type in mod.stat_text for def_type in ["Armour", "Evasion", "Energy Shield"]):
                        return False

                # Non-defence mods from body_armour apply to all armour types
                return True
            # For non-body_armour slots, slot match is sufficient
            return True

        # PathOfBuilding uses generic categories for universal mods
        if item_category in ALL_ARMOR_CATEGORIES:
            # "armour" is for universal mods (resistances, life, etc)
            if "armour" in mod.applicable_items:
                return True

        # Handle weapon category mapping (our detailed categories to PoB weapon types)
        # PoB uses generic weapon types (sword, axe, mace) without one/two-handed distinction
        # Use centralized POB_TO_DB_CATEGORY mapping, plus snake_case test variants
        extended_weapon_map = {
            **POB_TO_DB_CATEGORY,
            # Test category names (snake_case) - kept for backward compatibility
            "one_hand_sword": "sword",
            "one_hand_axe": "axe",
            "one_hand_mace": "mace",
            "claw": "claw",
            "two_hand_sword": "sword",
            "two_hand_axe": "axe",
            "two_hand_mace": "mace",
        }

        if item_category in extended_weapon_map:
            pob_weapon_type = extended_weapon_map[item_category]
            if pob_weapon_type in mod.applicable_items:
                return True

        return False

    def _modifier_applies_to_item(self, modifier: ItemModifier, item) -> bool:
        """Check if a modifier can be applied to a specific item instance."""
        return self._is_mod_applicable_to_category(modifier, item.base_category, item)

    def _get_excluded_groups_from_item(self, item) -> List[str]:
        """Build a list of excluded modifier groups from item's existing mods."""
        if not item:
            return []

        all_mods = item.prefix_mods + item.suffix_mods
        return [mod.mod_group for mod in all_mods if mod.mod_group]

    def _get_excluded_exclusion_groups_from_item(self, item) -> List[int]:
        """Build a list of excluded exclusion group IDs from item's existing mods."""
        if not item:
            return []

        all_mods = item.prefix_mods + item.suffix_mods
        return [mod.exclusion_group for mod in all_mods if mod.exclusion_group is not None]

    def _get_excluded_tags_from_item(self, item, mod_type: str) -> List[str]:
        """Build a list of excluded tags from item's existing mods of the same type."""
        if not item:
            return []

        # Only check mods of the same type (prefix vs suffix) for tag exclusion
        if mod_type == "prefix":
            existing_mods = item.prefix_mods
        else:
            existing_mods = item.suffix_mods

        # Define which tags are mutually exclusive within the same affix type
        EXCLUSIVE_TAGS = {
            'ailment',  # Only one ailment-related mod per affix type
            # Add other exclusive tags here as discovered
        }

        excluded_tags = set()
        for mod in existing_mods:
            if mod.tags:
                for tag in mod.tags:
                    if tag in EXCLUSIVE_TAGS:
                        excluded_tags.add(tag)

        return list(excluded_tags)

    def _get_excluded_patterns_from_item(self, item, mod_type: str) -> List[str]:
        """Build a list of excluded stat text patterns from item's existing mods."""
        if not item:
            return []

        # Only check mods of the same type (prefix vs suffix) for pattern exclusion
        if mod_type == "prefix":
            existing_mods = item.prefix_mods
        else:
            existing_mods = item.suffix_mods

        # Define mutually exclusive stat text patterns
        EXCLUSIVE_PATTERNS = [
            # Skill level mods are now handled by exclusion_group system (group 3)
            # Add other exclusive patterns here as discovered
        ]

        excluded_patterns = []
        for mod in existing_mods:
            for pattern in EXCLUSIVE_PATTERNS:
                if pattern in mod.stat_text:
                    excluded_patterns.append(pattern)
                    break  # Only need to add the pattern once

        return excluded_patterns

    def get_random_modifier_for_item(self, item) -> Optional[ItemModifier]:
        """Get a random modifier that can be applied to the given item."""
        # Determine available mod types
        available_types = []
        if item.can_add_prefix:
            available_types.append("prefix")
        if item.can_add_suffix:
            available_types.append("suffix")

        if not available_types:
            return None

        # Choose random type
        mod_type = random.choice(available_types)

        # Get excluded groups, tags, and patterns
        excluded_groups = self._get_excluded_groups_from_item(item)
        excluded_tags = self._get_excluded_tags_from_item(item, mod_type)
        excluded_patterns = self._get_excluded_patterns_from_item(item, mod_type)

        # Get eligible modifiers
        eligible_mods = self._filter_eligible_mods(
            self._prefix_pool if mod_type == "prefix" else self._suffix_pool,
            item.base_category,
            item.item_level,
            excluded_groups,
            None,  # min_mod_level
            True,  # exclude_exclusive
            excluded_tags,
            excluded_patterns,
            exclude_desecrated=True,
            exclude_essence=True,
            item=item
        )

        if not eligible_mods:
            return None

        return self._weighted_random_choice(eligible_mods)