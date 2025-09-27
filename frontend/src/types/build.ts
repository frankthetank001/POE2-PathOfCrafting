export interface League {
  name: string
  url: string
  displayName: string
  hardcore: boolean
  indexed: boolean
}

export interface LeaguesResponse {
  economyLeagues: League[]
  oldEconomyLeagues: League[]
  buildLeagues: League[]
  oldBuildLeagues: League[]
}

export interface BuildCharacter {
  name: string
  level: number
  class: string
  ascendancy?: string
}

export interface BuildItem {
  name: string
  type_line: string
  base_type: string
  rarity: string
  item_level?: number
  icon?: string
}

export interface BuildStats {
  life?: number
  energy_shield?: number
  mana?: number
  dps?: number
}

export interface Build {
  character: BuildCharacter
  items: Record<string, BuildItem>
  stats?: BuildStats
  main_skill?: string
}

export interface BuildsResponse {
  builds: Build[]
  total: number
  league: string
}