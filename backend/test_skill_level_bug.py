"""Test that skill level mods are properly excluded"""

from app.services.crafting.simulator import CraftingSimulator
from app.schemas.crafting import CraftableItem, ItemRarity, ItemModifier, ModType

simulator = CraftingSimulator()

# Create an amulet with Spell Skills mod
item = CraftableItem(
    base_name="Wrought Iron Amulet",
    base_category="amulet",
    rarity=ItemRarity.MAGIC,
    item_level=82,
    quality=0,
    prefix_mods=[
        ItemModifier(
            name="SkillLevels9",
            mod_type=ModType.PREFIX,
            tier=1,
            stat_text="+2 to Level of all Spell Skills",
            stat_min=2,
            stat_max=2,
            current_value=2,
            mod_group="SkillLevels"
        )
    ],
    suffix_mods=[],
    unrevealed_mods=[],
    corrupted=False,
    base_stats={},
    calculated_stats={}
)

# Get available mods - should NOT include Melee Skills
available = simulator.modifier_pool.get_all_mods_for_category(
    category=item.base_category,
    mod_type="prefix",
    item_level=item.item_level,
    item=item  # Pass item for exclusion filtering
)

# Check for skill level mods
melee_mods = [m for m in available if "Melee Skills" in m.stat_text]
spell_mods = [m for m in available if "Spell Skills" in m.stat_text]
attack_mods = [m for m in available if "Attack Skills" in m.stat_text]

print(f"Melee skill mods found: {len(melee_mods)}")
print(f"Spell skill mods found: {len(spell_mods)}")
print(f"Attack skill mods found: {len(attack_mods)}")

if melee_mods:
    print("\n❌ BUG: Melee Skills mod should be excluded!")
    for m in melee_mods:
        print(f"  - {m.stat_text}")
else:
    print("\n✓ Melee Skills correctly excluded")

if spell_mods:
    print("\n❌ BUG: Spell Skills mod should be excluded (already on item)!")
    for m in spell_mods:
        print(f"  - {m.stat_text}")
else:
    print("\n✓ Spell Skills correctly excluded")
