import re
from typing import List, Optional, Tuple

from app.core.logging import get_logger
from app.schemas.item import ItemMod, ItemRarity, ItemSocket, ParsedItem

logger = get_logger(__name__)

SECTION_SEPARATOR = "--------"


class ItemParser:
    @staticmethod
    def parse(item_text: str) -> ParsedItem:
        if not item_text or not item_text.strip():
            raise ValueError("Item text cannot be empty")

        sections = item_text.split(SECTION_SEPARATOR)
        sections = [s.strip() for s in sections if s.strip()]

        if len(sections) < 2:
            raise ValueError("Invalid item format: insufficient sections")

        rarity = ItemParser._parse_rarity(sections[0])
        name, base_type = ItemParser._parse_name_and_base(sections[0], rarity)

        item_level: Optional[int] = None
        quality: Optional[int] = None
        sockets: List[ItemSocket] = []
        requirements = {}
        implicits: List[ItemMod] = []
        explicits: List[ItemMod] = []
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

            if any("Sockets:" in line for line in lines):
                sockets = ItemParser._parse_sockets(section)

            if any("Requirements:" in line for line in lines):
                requirements = ItemParser._parse_requirements(section)

            if "Corrupted" in section:
                corrupted = True

            if i > 1 and not implicit_found:
                if ItemParser._looks_like_mods(lines):
                    implicits = ItemParser._parse_mods(section)
                    implicit_found = True

            elif implicit_found and ItemParser._looks_like_mods(lines):
                explicits = ItemParser._parse_mods(section)

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
            corrupted=corrupted,
            raw_text=item_text,
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
    def _parse_name_and_base(first_section: str, rarity: ItemRarity) -> Tuple[str, str]:
        lines = [line.strip() for line in first_section.split("\n") if line.strip()]

        rarity_line_idx = next(i for i, line in enumerate(lines) if line.startswith("Rarity:"))

        remaining_lines = lines[rarity_line_idx + 1 :]

        if rarity in [ItemRarity.RARE, ItemRarity.UNIQUE] and len(remaining_lines) >= 2:
            return remaining_lines[0], remaining_lines[1]
        elif len(remaining_lines) >= 1:
            return remaining_lines[0], remaining_lines[0]
        else:
            raise ValueError("Could not parse item name and base type")

    @staticmethod
    def _parse_item_level(section: str) -> Optional[int]:
        match = re.search(r"Item Level:\s*(\d+)", section)
        return int(match.group(1)) if match else None

    @staticmethod
    def _parse_quality(section: str) -> Optional[int]:
        match = re.search(r"Quality:\s*\+?(\d+)", section)
        return int(match.group(1)) if match else None

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
        mod_indicators = ["+", "increased", "reduced", "to", "%", "Adds"]
        return any(
            any(indicator in line for indicator in mod_indicators) for line in lines
        )

    @staticmethod
    def _parse_mods(section: str) -> List[ItemMod]:
        lines = [line.strip() for line in section.split("\n") if line.strip()]
        mods = []

        for line in lines:
            if line and not line.startswith("Requirements:"):
                values = re.findall(r"\d+(?:\.\d+)?", line)
                mods.append(ItemMod(text=line, values=values))

        return mods