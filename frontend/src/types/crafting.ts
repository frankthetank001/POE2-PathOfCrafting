export enum ItemRarity {
  NORMAL = 'Normal',
  MAGIC = 'Magic',
  RARE = 'Rare',
  UNIQUE = 'Unique',
}

export enum ModType {
  PREFIX = 'prefix',
  SUFFIX = 'suffix',
  IMPLICIT = 'implicit',
  DESECRATED = 'desecrated',
}

export interface ItemModifier {
  id?: number
  name: string
  mod_type: ModType
  tier: number
  stat_text: string
  stat_min?: number
  stat_max?: number
  current_value?: number
  required_ilvl?: number
  mod_group?: string
  tags?: string[]
}

export interface ItemBase {
  name: string
  category?: string
  attribute_requirements?: string[]
  default_ilvl: number
  description: string
  base_stats: Record<string, number>
}

export interface ItemBasesBySlot {
  [slot: string]: string[]  // Now just category names, not full ItemBase objects
}

export interface CraftableItem {
  base_name: string
  base_category: string
  rarity: ItemRarity
  item_level: number
  quality: number

  implicit_mods: ItemModifier[]
  prefix_mods: ItemModifier[]
  suffix_mods: ItemModifier[]

  corrupted: boolean
  base_stats: Record<string, number>
  calculated_stats: Record<string, number>
}

export interface CraftingSimulationRequest {
  item: CraftableItem
  currency_name: string
}

export interface CraftingSimulationResult {
  success: boolean
  result_item?: CraftableItem
  message: string
  probabilities?: Record<string, number>
}