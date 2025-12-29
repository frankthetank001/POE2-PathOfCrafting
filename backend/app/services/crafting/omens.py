"""
Omen Data and Metadata

This module provides omen metadata for the API. The actual omen behavior
is implemented in OmenModifiedMechanic in mechanics.py.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass

# Re-export CATALYST_TAG_MAPPING from mechanics for backwards compatibility
from app.services.crafting.mechanics import CATALYST_TAG_MAPPING


@dataclass
class OmenMetadata:
    """Metadata about an omen for API responses."""
    name: str
    affected_currency: str
    forces_prefix: bool = False
    forces_suffix: bool = False
    required_tag: Optional[str] = None  # For boss-specific omens
    description: str = ""


# All omen metadata - this is the single source of truth
OMEN_METADATA: Dict[str, OmenMetadata] = {
    # Exaltation Omens
    "Omen of Greater Exaltation": OmenMetadata(
        name="Omen of Greater Exaltation",
        affected_currency="Exalted Orb",
        description="Adds TWO random modifiers instead of one"
    ),
    "Omen of Sinistral Exaltation": OmenMetadata(
        name="Omen of Sinistral Exaltation",
        affected_currency="Exalted Orb",
        forces_prefix=True,
        description="Forces addition of prefix modifier only"
    ),
    "Omen of Dextral Exaltation": OmenMetadata(
        name="Omen of Dextral Exaltation",
        affected_currency="Exalted Orb",
        forces_suffix=True,
        description="Forces addition of suffix modifier only"
    ),
    "Omen of Homogenising Exaltation": OmenMetadata(
        name="Omen of Homogenising Exaltation",
        affected_currency="Exalted Orb",
        description="Added modifier matches tags of existing modifiers"
    ),
    "Omen of Catalysing Exaltation": OmenMetadata(
        name="Omen of Catalysing Exaltation",
        affected_currency="Exalted Orb",
        description="Consumes catalyst quality to boost matching mod weights"
    ),

    # Coronation Omens (Regal)
    "Omen of Sinistral Coronation": OmenMetadata(
        name="Omen of Sinistral Coronation",
        affected_currency="Regal Orb",
        forces_prefix=True,
        description="Forces Regal to add prefix only"
    ),
    "Omen of Dextral Coronation": OmenMetadata(
        name="Omen of Dextral Coronation",
        affected_currency="Regal Orb",
        forces_suffix=True,
        description="Forces Regal to add suffix only"
    ),
    "Omen of Homogenising Coronation": OmenMetadata(
        name="Omen of Homogenising Coronation",
        affected_currency="Regal Orb",
        description="Added modifier matches tags of existing modifiers"
    ),

    # Chaos/Erasure Omens
    "Omen of Whittling": OmenMetadata(
        name="Omen of Whittling",
        affected_currency="Chaos Orb",
        description="Removes lowest level modifier"
    ),
    "Omen of Sinistral Erasure": OmenMetadata(
        name="Omen of Sinistral Erasure",
        affected_currency="Chaos Orb",
        forces_prefix=True,
        description="Removes only prefix modifiers"
    ),
    "Omen of Dextral Erasure": OmenMetadata(
        name="Omen of Dextral Erasure",
        affected_currency="Chaos Orb",
        forces_suffix=True,
        description="Removes only suffix modifiers"
    ),

    # Annulment Omens
    "Omen of Greater Annulment": OmenMetadata(
        name="Omen of Greater Annulment",
        affected_currency="Orb of Annulment",
        description="Removes TWO modifiers instead of one"
    ),
    "Omen of Sinistral Annulment": OmenMetadata(
        name="Omen of Sinistral Annulment",
        affected_currency="Orb of Annulment",
        forces_prefix=True,
        description="Removes only prefix modifiers"
    ),
    "Omen of Dextral Annulment": OmenMetadata(
        name="Omen of Dextral Annulment",
        affected_currency="Orb of Annulment",
        forces_suffix=True,
        description="Removes only suffix modifiers"
    ),

    # Alchemy Omens
    "Omen of Sinistral Alchemy": OmenMetadata(
        name="Omen of Sinistral Alchemy",
        affected_currency="Orb of Alchemy",
        forces_prefix=True,
        description="Results in maximum number of prefix modifiers (3P/1S)"
    ),
    "Omen of Dextral Alchemy": OmenMetadata(
        name="Omen of Dextral Alchemy",
        affected_currency="Orb of Alchemy",
        forces_suffix=True,
        description="Results in maximum number of suffix modifiers (1P/3S)"
    ),

    # Essence/Crystallisation Omens
    "Omen of Sinistral Crystallisation": OmenMetadata(
        name="Omen of Sinistral Crystallisation",
        affected_currency="Perfect Essence",
        forces_prefix=True,
        description="Removes only prefix modifiers when applying essence"
    ),
    "Omen of Dextral Crystallisation": OmenMetadata(
        name="Omen of Dextral Crystallisation",
        affected_currency="Perfect Essence",
        forces_suffix=True,
        description="Removes only suffix modifiers when applying essence"
    ),

    # Desecration/Necromancy Omens
    "Omen of Abyssal Echoes": OmenMetadata(
        name="Omen of Abyssal Echoes",
        affected_currency="Desecration",
        description="Can reroll desecrated options once when revealing"
    ),
    "Omen of Sinistral Necromancy": OmenMetadata(
        name="Omen of Sinistral Necromancy",
        affected_currency="Desecration",
        forces_prefix=True,
        description="Adds only prefix desecrated modifiers"
    ),
    "Omen of Dextral Necromancy": OmenMetadata(
        name="Omen of Dextral Necromancy",
        affected_currency="Desecration",
        forces_suffix=True,
        description="Adds only suffix desecrated modifiers"
    ),
    "Omen of the Sovereign": OmenMetadata(
        name="Omen of the Sovereign",
        affected_currency="Desecration",
        required_tag="ulaman",
        description="Guarantees random Ulaman modifier"
    ),
    "Omen of the Liege": OmenMetadata(
        name="Omen of the Liege",
        affected_currency="Desecration",
        required_tag="amanamu",
        description="Guarantees random Amanamu modifier"
    ),
    "Omen of the Blackblooded": OmenMetadata(
        name="Omen of the Blackblooded",
        affected_currency="Desecration",
        required_tag="kurgal",
        description="Guarantees random Kurgal modifier"
    ),
    "Omen of Putrefaction": OmenMetadata(
        name="Omen of Putrefaction",
        affected_currency="Desecration",
        description="Increases chance of higher-tier desecrated modifiers"
    ),
    "Omen of Light": OmenMetadata(
        name="Omen of Light",
        affected_currency="Orb of Annulment",
        description="Only removes desecrated modifiers"
    ),

    # Corruption Omen
    "Omen of Corruption": OmenMetadata(
        name="Omen of Corruption",
        affected_currency="Vaal Orb",
        description="Always results in change (removes 'no change' outcome)"
    ),
}


class OmenFactory:
    """Factory for accessing omen metadata."""

    @classmethod
    def create(cls, omen_name: str) -> Optional[OmenMetadata]:
        """Get omen metadata by name."""
        return OMEN_METADATA.get(omen_name)

    @classmethod
    def get_all_omens(cls) -> List[str]:
        """Get all available omen names."""
        return list(OMEN_METADATA.keys())

    @classmethod
    def get_omens_for_currency(cls, currency_name: str) -> List[str]:
        """Get all omens that can modify a specific currency."""
        applicable = []
        for name, meta in OMEN_METADATA.items():
            # Check if affected_currency matches (supports variants like "Perfect Exalted Orb")
            if meta.affected_currency in currency_name or meta.affected_currency == currency_name:
                applicable.append(name)
        return applicable
