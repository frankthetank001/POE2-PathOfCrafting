"""
Crafting system constants.

Global constants used across the crafting mechanics system.
"""

# Tags that are internal/system tags and should not affect homogenising matching
# These tags are used for filtering and organization but don't represent player-visible mod themes
HIDDEN_TAGS_FOR_HOMOGENISING = {
    'essence_only',      # Only available from essences
    'desecrated_only',   # Only available from desecration
    'drop',              # Can drop from monsters
    'resource',          # Resource-related (internal)
    'energy_shield',     # Defence type (too generic)
    'flat_life_regen',   # Specific mechanic tag (too specific)
    'armour',            # Defence type (too generic)
    'caster_damage',     # Damage category (too generic)
    'attack_damage',     # Damage category (too generic)
}
