export enum ItemRarity {
  NORMAL = 'Normal',
  MAGIC = 'Magic',
  RARE = 'Rare',
  UNIQUE = 'Unique',
}

export interface ItemSocket {
  group: number
  attr?: string
}

export interface ItemMod {
  text: string
  values: string[]
}

export interface ParsedItem {
  rarity: ItemRarity
  name: string
  base_type: string
  item_level?: number
  quality?: number
  sockets: ItemSocket[]
  requirements: Record<string, number>
  implicits: ItemMod[]
  explicits: ItemMod[]
  corrupted: boolean
  identified: boolean
  raw_text: string
}

export interface ItemParseRequest {
  item_text: string
}

export interface ItemParseResponse {
  success: boolean
  item?: ParsedItem
  error?: string
}