import re
from typing import List, Optional, Tuple

from app.core.logging import get_logger
from app.schemas.item import ItemMod, ItemRarity, ItemSocket, ParsedItem, ParsedRune

logger = get_logger(__name__)

SECTION_SEPARATOR = "--------"


class ItemParser:
    @staticmethod
    def parse(item_text: str) -> ParsedItem:
        if not item_text or not item_text.strip():
            raise ValueError("Item text cannot be empty")

        # Check if this is an alternative format (no separators, has tier prefixes like P1, S2)
        if SECTION_SEPARATOR not in item_text and ItemParser._is_alternative_format(item_text):
            return ItemParser._parse_alternative_format(item_text)

        sections = item_text.split(SECTION_SEPARATOR)
        sections = [s.strip() for s in sections if s.strip()]

        if len(sections) < 2:
            raise ValueError("Invalid item format: insufficient sections")

        rarity = ItemParser._parse_rarity(sections[0])
        name, base_type = ItemParser._parse_name_and_base(sections[0], sections[1] if len(sections) > 1 else None, rarity)

        item_level: Optional[int] = None
        quality: Optional[int] = None
        catalyst_type: Optional[str] = None
        catalyst_quality: Optional[int] = None
        sockets: List[ItemSocket] = []
        requirements = {}
        implicits: List[ItemMod] = []
        explicits: List[ItemMod] = []
        runes: List[ParsedRune] = []
        corrupted = False

        implicit_found = False

        for i, section in enumerate(sections[1:], start=1):
            lines = [line.strip() for line in section.split("\n") if line.strip()]

            if not lines:
                continue

            if any("Item Level:" in line for line in lines):
                item_level = ItemParser._parse_item_level(section)

            if any("Quality:" in line for line in lines):
                quality = ItemParser._parse_quality(section)
                # Also check for catalyst quality on jewelry
                cat_type, cat_qual = ItemParser._parse_catalyst_quality(section)
                if cat_type and cat_qual:
                    catalyst_type = cat_type
                    catalyst_quality = cat_qual

            if any("Sockets:" in line for line in lines):
                sockets = ItemParser._parse_sockets(section)

            if any("Requirements:" in line for line in lines):
                requirements = ItemParser._parse_requirements(section)

            if "Corrupted" in section:
                corrupted = True

            # Check for rune mods - lines ending with "(rune)" or "(bonded)"
            if any(line.endswith("(rune)") or line.endswith("(bonded)") for line in lines):
                parsed_rune = ItemParser._parse_rune_section(lines)
                if parsed_rune:
                    runes.append(parsed_rune)
                continue  # Skip further mod processing for this section

            # Check for mods in any section after the first (i > 0)
            # This allows mods to appear in section 1 (for items without properties)
            if i > 0 and ItemParser._looks_like_mods(lines):
                # Check if this section contains detailed mod format. A detailed header may
                # carry a source qualifier before the affix type, e.g.
                # "{ Desecrated Prefix Modifier ... }" or "{ Crafted Suffix Modifier ... }",
                # so allow an optional leading word.
                has_detailed_format = any(
                    re.search(r'\{\s*(?:\w+\s+)?(?:Prefix|Suffix)\s+Modifier', line)
                    for line in lines
                )

                # Check if section explicitly marks implicit mods
                has_implicit_marker = any(
                    re.search(r'\{\s*(?:\w+\s+)?Implicit\s+Modifier', line)
                    for line in lines
                )

                # If section has detailed format with both implicit and explicit markers,
                # parse all mods and split them by mod_type
                if has_detailed_format and has_implicit_marker:
                    all_mods = ItemParser._parse_mods(section)
                    for mod in all_mods:
                        if mod.mod_type == 'implicit':
                            implicits.append(mod)
                        else:
                            explicits.append(mod)
                    implicit_found = True
                elif has_implicit_marker or (not has_detailed_format and not implicit_found and "implicit" in section.lower()):
                    # Section has implicit marker OR contains "(implicit)" text
                    implicits.extend(ItemParser._parse_mods(section))
                    implicit_found = True
                elif has_detailed_format or not implicit_found:
                    # Detailed format OR first mod section without implicit markers = explicits
                    # (Most items don't have implicits, so default to explicits)
                    explicits.extend(ItemParser._parse_mods(section))
                    implicit_found = True  # Mark that we've seen the first mod section
                else:
                    # Second+ mod section = also explicits
                    explicits.extend(ItemParser._parse_mods(section))

        return ParsedItem(
            rarity=rarity,
            name=name,
            base_type=base_type,
            item_level=item_level,
            quality=quality,
            sockets=sockets,
            requirements=requirements,
            implicits=implicits,
            explicits=explicits,
            runes=runes,
            corrupted=corrupted,
            raw_text=item_text,
            catalyst_type=catalyst_type,
            catalyst_quality=catalyst_quality,
        )

    @staticmethod
    def _parse_rarity(first_section: str) -> ItemRarity:
        lines = first_section.split("\n")
        for line in lines:
            if line.startswith("Rarity:"):
                rarity_text = line.replace("Rarity:", "").strip()
                try:
                    return ItemRarity(rarity_text)
                except ValueError:
                    logger.warning(f"Unknown rarity: {rarity_text}, defaulting to Normal")
                    return ItemRarity.NORMAL

        raise ValueError("No rarity found in item text")

    @staticmethod
    def _parse_name_and_base(first_section: str, second_section: Optional[str], rarity: ItemRarity) -> Tuple[str, str]:
        lines = [line.strip() for line in first_section.split("\n") if line.strip()]

        rarity_line_idx = next(i for i, line in enumerate(lines) if line.startswith("Rarity:"))

        remaining_lines = lines[rarity_line_idx + 1 :]

        # Filter out warning/info messages that appear before the name
        # e.g., "You cannot use this item. Its stats will be ignored"
        remaining_lines = [
            line for line in remaining_lines
            if not line.startswith("You cannot use this item")
            and not line.startswith("This item will be")
        ]

        # If name/base not in first section, check second section
        # This handles items with warnings where name/base appear after a separator
        if len(remaining_lines) == 0 and second_section:
            second_lines = [line.strip() for line in second_section.split("\n") if line.strip()]
            # Second section should just be name and base (2 lines for rare/unique)
            if len(second_lines) >= 2:
                return second_lines[0], second_lines[1]
            elif len(second_lines) == 1:
                return second_lines[0], second_lines[0]

        if rarity in [ItemRarity.RARE, ItemRarity.UNIQUE] and len(remaining_lines) >= 2:
            return remaining_lines[0], remaining_lines[1]
        elif rarity == ItemRarity.MAGIC and len(remaining_lines) >= 1:
            # For Magic items, extract base from name like "Prefix Base of Suffix"
            full_name = remaining_lines[0]
            base_name = ItemParser._extract_base_from_magic_name(full_name)
            return full_name, base_name
        elif len(remaining_lines) >= 1:
            return remaining_lines[0], remaining_lines[0]
        else:
            raise ValueError("Could not parse item name and base type")

    @staticmethod
    def _extract_base_from_magic_name(name: str) -> str:
        """
        Extract base item name from Magic item format.
        Magic items: "Prefix Base of Suffix" or "Prefix Base" or "Base of Suffix"
        Examples: "Virile Vile Robe of the Troll" -> "Vile Robe"
        """
        # Remove "of ..." suffix pattern (everything after " of ")
        of_match = re.search(r'\s+of\s+', name)
        if of_match:
            name = name[:of_match.start()]

        # The base is usually the last 2 words (e.g., "Vile Robe", "Gold Amulet")
        words = name.split()

        if len(words) >= 2:
            # Take last 2 words as base
            return ' '.join(words[-2:])
        elif len(words) == 1:
            return words[0]

        return name

    @staticmethod
    def _parse_item_level(section: str) -> Optional[int]:
        match = re.search(r"Item Level:\s*(\d+)", section)
        return int(match.group(1)) if match else None

    @staticmethod
    def _parse_quality(section: str) -> Optional[int]:
        # Match regular quality (without parentheses) - e.g. "Quality: +20%"
        # Skip catalyst quality lines which have (xxx Modifiers) in them
        match = re.search(r"Quality:\s*\+?(\d+)%?(?!\s*\()", section)
        if match:
            return int(match.group(1))
        # Fallback - also check for plain "Quality: +20" without % and without catalyst
        match = re.search(r"Quality:\s*\+?(\d+)(?!\s*%?\s*\()", section)
        return int(match.group(1)) if match else None

    @staticmethod
    def _parse_catalyst_quality(section: str) -> Tuple[Optional[str], Optional[int]]:
        """Parse catalyst quality from jewelry items.

        Format: "Quality (Life Modifiers): +15%"
        Returns: (catalyst_type, quality) e.g. ("flesh", 15)
        """
        # Map display names to catalyst IDs
        catalyst_display_to_id = {
            "Life Modifiers": "flesh",
            "Mana Modifiers": "neural",
            "Defence Modifiers": "carapace",
            "Physical Damage Modifiers": "uul_netol",
            "Fire Damage Modifiers": "xoph",
            "Cold Damage Modifiers": "tul",
            "Lightning Damage Modifiers": "esh",
            "Chaos Damage Modifiers": "chayula",
            "Attack Modifiers": "reaver",
            "Caster Modifiers": "sibilant",
            "Speed Modifiers": "skittering",
            "Attribute Modifiers": "adaptive",
        }

        match = re.search(r"Quality\s*\(([^)]+)\):\s*\+?(\d+)%?", section)
        if match:
            display_name = match.group(1).strip()
            quality = int(match.group(2))
            catalyst_type = catalyst_display_to_id.get(display_name)
            return (catalyst_type, quality)
        return (None, None)

    @staticmethod
    def _parse_sockets(section: str) -> List[ItemSocket]:
        match = re.search(r"Sockets:\s*(.+)", section)
        if not match:
            return []

        socket_string = match.group(1)
        sockets = []
        group = 0

        for char in socket_string:
            if char == "-":
                continue
            elif char == " ":
                group += 1
            elif char in ["R", "G", "B", "W", "S", "A"]:
                sockets.append(ItemSocket(group=group, attr=char))

        return sockets

    @staticmethod
    def _parse_requirements(section: str) -> dict:
        requirements = {}
        lines = section.split("\n")

        for line in lines:
            if "Level:" in line:
                match = re.search(r"Level:\s*(\d+)", line)
                if match:
                    requirements["Level"] = int(match.group(1))

            if "Str:" in line or "Strength:" in line:
                match = re.search(r"(?:Str|Strength):\s*(\d+)", line)
                if match:
                    requirements["Strength"] = int(match.group(1))

            if "Dex:" in line or "Dexterity:" in line:
                match = re.search(r"(?:Dex|Dexterity):\s*(\d+)", line)
                if match:
                    requirements["Dexterity"] = int(match.group(1))

            if "Int:" in line or "Intelligence:" in line:
                match = re.search(r"(?:Int|Intelligence):\s*(\d+)", line)
                if match:
                    requirements["Intelligence"] = int(match.group(1))

        return requirements

    @staticmethod
    def _looks_like_mods(lines: List[str]) -> bool:
        # Property labels that should NOT be treated as mods
        property_labels = [
            "Quality:", "Physical Damage:", "Elemental Damage:", "Chaos Damage:",
            "Critical Hit Chance:", "Attacks per Second:", "Weapon Range:",
            "Armour:", "Evasion Rating:", "Energy Shield:", "Ward:",
            "Block:", "Spell Damage:", "Attack Damage:",
        ]

        # If most lines look like properties (Label: Value format), this is not a mod section
        property_count = sum(1 for line in lines if any(line.startswith(label) for label in property_labels))
        if property_count > 0 and property_count >= len(lines) * 0.5:
            return False

        mod_indicators = ["+", "increased", "reduced", "to", "%", "Adds", "Bears", "Grants", "Mark of"]

        # Check for detailed format: { [Qualifier ]Prefix/Suffix/Implicit Modifier "Name" (Tier: X) }
        detailed_format_pattern = r'\{\s*(?:\w+\s+)?(?:Prefix|Suffix|Implicit)\s+Modifier\s+"[^"]+"\s*(?:\(Tier:\s*\d+\))?'

        return any(
            any(indicator in line for indicator in mod_indicators) or
            re.search(detailed_format_pattern, line) for line in lines
        )

    @staticmethod
    def _parse_mods(section: str) -> List[ItemMod]:
        lines = [line.strip() for line in section.split("\n") if line.strip()]
        mods = []

        # Pattern to detect mod headers. The affix type may be preceded by a source qualifier
        # (Desecrated/Crafted/Fractured/...), e.g. "{ Crafted Suffix Modifier "..." }".
        header_pattern = re.compile(
            r'\{\s*(?:\w+\s+)?(?:Prefix|Suffix|Implicit)\s+Modifier\s+"[^"]+"\s*(?:\(Tier:\s*\d+\))?\s*(?:—\s*.+)?\s*\}'
        )

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line or line.startswith("Requirements:"):
                i += 1
                continue

            # Check if this line has detailed mod info format:
            #   { [Qualifier ]Prefix/Suffix/Implicit Modifier "Name" (Tier: X) — Tags }
            # The optional qualifier (Desecrated/Crafted/Fractured/...) names the mod's source.
            detailed_match = re.match(
                r'\{\s*(?:(\w+)\s+)?(Prefix|Suffix|Implicit)\s+Modifier\s+"([^"]+)"\s*(?:\(Tier:\s*(\d+)\))?\s*(?:—\s*(.+))?\s*\}',
                line
            )

            if detailed_match:
                qualifier = detailed_match.group(1)
                mod_type = detailed_match.group(2).lower()
                mod_name = detailed_match.group(3)
                tier_str = detailed_match.group(4)
                tier = int(tier_str) if tier_str else None
                tags_str = detailed_match.group(5) or ""
                tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

                # The qualifier (or a tag) names the mod's 0.5 source. These are mutually
                # exclusive: a mod is a plain explicit, or crafted, or desecrated, or fractured.
                qual = (qualifier or "").lower()
                is_desecrated = "desecrated" in tags_str.lower() or qual == "desecrated"
                is_crafted = qual == "crafted"
                is_fractured = qual == "fractured"

                # Collect ALL stat lines until next header or end
                i += 1
                stat_lines = []
                all_values = []
                while i < len(lines) and not header_pattern.match(lines[i]):
                    stat_line = lines[i]
                    # Check for (desecrated) suffix in stat line
                    if stat_line.endswith("(desecrated)"):
                        stat_line = stat_line[:-12].strip()
                        is_desecrated = True
                    # Strip tier range annotations like "160(155-169)" -> "160"
                    stat_line = re.sub(r'(\d+(?:\.\d+)?)\(\d+(?:\.\d+)?-\d+(?:\.\d+)?\)', r'\1', stat_line)
                    stat_lines.append(stat_line)
                    all_values.extend(re.findall(r"\d+(?:\.\d+)?", stat_line))
                    i += 1

                if stat_lines:
                    # Join stat lines with newline for hybrid mods
                    mods.append(ItemMod(
                        text="\n".join(stat_lines),
                        values=all_values,
                        mod_name=mod_name,
                        tier=tier,
                        mod_type=mod_type,
                        tags=tags,
                        is_desecrated=is_desecrated,
                        is_crafted=is_crafted,
                        is_fractured=is_fractured,
                    ))
            else:
                # Simple format without detailed info
                is_desecrated = False
                mod_text = line

                # Check for (desecrated) suffix
                if mod_text.endswith("(desecrated)"):
                    mod_text = mod_text[:-12].strip()
                    is_desecrated = True

                values = re.findall(r"\d+(?:\.\d+)?", mod_text)
                mods.append(ItemMod(text=mod_text, values=values, is_desecrated=is_desecrated))
                i += 1

        return mods

    @staticmethod
    def _parse_rune_section(lines: List[str]) -> Optional[ParsedRune]:
        """Parse a section containing rune mods (lines ending with (rune) or (bonded))"""
        rune_mods = []
        bonded_mods = []
        rune_name = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for rune header format: { Rune "Greater Iron Rune" }
            rune_header_match = re.match(r'\{\s*Rune\s+"([^"]+)"\s*\}', line)
            if rune_header_match:
                rune_name = rune_header_match.group(1)
                continue

            # Check for rune mod
            if line.endswith("(rune)"):
                mod_text = line[:-6].strip()  # Remove " (rune)" suffix
                rune_mods.append(mod_text)
            elif line.endswith("(bonded)"):
                mod_text = line[:-8].strip()  # Remove " (bonded)" suffix
                bonded_mods.append(mod_text)

        if rune_mods or bonded_mods:
            return ParsedRune(
                name=rune_name,
                mods=rune_mods,
                bonded_mods=bonded_mods
            )
        return None

    @staticmethod
    def _is_alternative_format(item_text: str) -> bool:
        """
        Detect if the item text is in the alternative format used by some tools.

        Format characteristics:
        - No "--------" separators
        - Has "Item Rarity:" instead of "Rarity:"
        - Has tier prefixes like P1, P2, S0, S1, S2 on their own lines before mods
        - May have "Tiering" section header
        """
        lines = [line.strip() for line in item_text.split("\n") if line.strip()]

        # Check for characteristic markers
        has_item_rarity = any("Item Rarity:" in line for line in lines)
        has_tier_prefix = any(re.match(r'^[PS]\d+$', line) for line in lines)
        has_tiering_header = any(line == "Tiering" for line in lines)

        return has_item_rarity or has_tier_prefix or has_tiering_header

    @staticmethod
    def _parse_alternative_format(item_text: str) -> ParsedItem:
        """
        Parse item text in the alternative format.

        Format example:
        ```
        Pandemonium March
        Sandsworn Sandals
        Boots
        Quality: +20%
        Energy Shield: 386
        Item Rarity: Rare
        Item Level: 80
        Requires Level: 75, 101 Int
        Tiering
        56% increased Armour, Evasion and Energy Shield
        Bonded: +32 to maximum Life
        P1
        97% increased Energy Shield
        S2
        +38% to Lightning Resistance
        ```
        """
        lines = [line.strip() for line in item_text.split("\n") if line.strip()]

        # Parse basic info
        name = lines[0] if len(lines) > 0 else "Unknown"
        base_type = lines[1] if len(lines) > 1 else "Unknown"

        # Initialize values
        rarity = ItemRarity.NORMAL
        item_level: Optional[int] = None
        quality: Optional[int] = None
        requirements = {}
        implicits: List[ItemMod] = []
        explicits: List[ItemMod] = []
        runes: List[ParsedRune] = []
        corrupted = False
        catalyst_type: Optional[str] = None
        catalyst_quality: Optional[int] = None

        # Track parsing state
        in_mods_section = False
        seen_tier_marker = False  # True after first P/S tier marker
        current_mod_type: Optional[str] = None  # 'prefix' or 'suffix'
        current_tier: Optional[int] = None
        rune_mods: List[str] = []
        bonded_mods: List[str] = []

        for line in lines[2:]:  # Skip name and base_type
            # Parse rarity
            if line.startswith("Item Rarity:"):
                rarity_text = line.replace("Item Rarity:", "").strip()
                try:
                    rarity = ItemRarity(rarity_text)
                except ValueError:
                    rarity = ItemRarity.NORMAL
                continue

            # Parse item level
            if line.startswith("Item Level:"):
                match = re.search(r"Item Level:\s*(\d+)", line)
                if match:
                    item_level = int(match.group(1))
                continue

            # Parse quality
            if line.startswith("Quality:") and "Modifiers" not in line:
                match = re.search(r"Quality:\s*\+?(\d+)", line)
                if match:
                    quality = int(match.group(1))
                continue

            # Parse requirements (format: "Requires Level: 75, 101 Int")
            if line.startswith("Requires Level:") or line.startswith("Requires:"):
                req_text = line.replace("Requires Level:", "").replace("Requires:", "").strip()
                # Parse level
                level_match = re.match(r"(\d+)", req_text)
                if level_match:
                    requirements["Level"] = int(level_match.group(1))
                # Parse attributes
                if "Str" in req_text:
                    str_match = re.search(r"(\d+)\s*Str", req_text)
                    if str_match:
                        requirements["Strength"] = int(str_match.group(1))
                if "Dex" in req_text:
                    dex_match = re.search(r"(\d+)\s*Dex", req_text)
                    if dex_match:
                        requirements["Dexterity"] = int(dex_match.group(1))
                if "Int" in req_text:
                    int_match = re.search(r"(\d+)\s*Int", req_text)
                    if int_match:
                        requirements["Intelligence"] = int(int_match.group(1))
                continue

            # Skip item class and stat lines
            if line in ["Boots", "Helmet", "Gloves", "Body Armour", "Belt", "Ring", "Amulet",
                        "One Hand Sword", "Two Hand Sword", "Bow", "Staff", "Wand", "Shield", "Quiver", "Focus"]:
                continue
            if any(line.startswith(stat) for stat in ["Armour:", "Evasion:", "Energy Shield:", "Ward:",
                                                       "Physical Damage:", "Elemental Damage:", "Critical Hit Chance:",
                                                       "Attacks per Second:", "Weapon Range:"]):
                continue

            # Tiering section header marks start of mods
            if line == "Tiering":
                in_mods_section = True
                continue

            # Check for tier prefix (P0, P1, P2, S0, S1, S2, etc.)
            tier_match = re.match(r'^([PS])(\d+)$', line)
            if tier_match:
                in_mods_section = True
                seen_tier_marker = True
                mod_letter = tier_match.group(1)
                current_mod_type = "prefix" if mod_letter == "P" else "suffix"
                current_tier = int(tier_match.group(2))
                continue

            # Check for corrupted
            if line == "Corrupted":
                corrupted = True
                continue

            # Parse bonded mods (from runes)
            if line.startswith("Bonded:"):
                mod_text = line.replace("Bonded:", "").strip()
                bonded_mods.append(mod_text)
                continue

            # If we're in mods section, parse as mod
            if in_mods_section:
                # Skip empty lines and non-mod lines
                if not line or line.startswith("Quality") or line.startswith("Item"):
                    continue

                # Check if this looks like a mod
                mod_indicators = ["+", "increased", "reduced", "Adds", "to ", "%", "Grants", "Bears"]
                if any(indicator in line for indicator in mod_indicators):
                    values = re.findall(r"\d+(?:\.\d+)?", line)

                    if current_mod_type:
                        # We have a tier marker, this is an explicit mod
                        mod = ItemMod(
                            text=line,
                            values=values,
                            mod_type=current_mod_type,
                            tier=current_tier
                        )
                        explicits.append(mod)
                        # Reset tier after consuming the mod
                        current_mod_type = None
                        current_tier = None
                    elif not seen_tier_marker:
                        # In mods section but before any tier markers = rune mod
                        rune_mods.append(line)
                    else:
                        # After tier markers but no current type = shouldn't happen
                        # Treat as explicit without type info
                        mod = ItemMod(text=line, values=values)
                        explicits.append(mod)

        # Create rune from rune mods and bonded mods if any
        if rune_mods or bonded_mods:
            runes.append(ParsedRune(
                name="Unknown Rune",
                mods=rune_mods,
                bonded_mods=bonded_mods
            ))

        return ParsedItem(
            rarity=rarity,
            name=name,
            base_type=base_type,
            item_level=item_level,
            quality=quality,
            sockets=[],
            requirements=requirements,
            implicits=implicits,
            explicits=explicits,
            runes=runes,
            corrupted=corrupted,
            raw_text=item_text,
            catalyst_type=catalyst_type,
            catalyst_quality=catalyst_quality,
        )