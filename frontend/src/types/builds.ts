// Types for the Popular Builds feature. Shapes mirror the backend /api/v1/builds
// responses exactly (snake_case), so no transform layer is needed.

export interface BuildsMeta {
  league: string
  league_slug: string
  snapshot_version: string
  scraped_at: string
  sample_size: number
  roster_size: number
  base_count: number
  mod_count: number
  bases_resolved: number
  disclaimer: string
}

export interface TrendingBase {
  base_name: string
  slot: string
  usage_count: number
  usage_pct: number
  rarity_mix: Record<string, number>
  common_skills: string[]
  category: string | null
  resolves_in_app: boolean
}

export interface TrendingMod {
  base_name: string
  slot: string
  mod_template: string
  mod_origin: string
  usage_count: number
  usage_pct: number
  resolved: boolean
  mod_group: string | null
  mod_type: string | null
  tier_count: number
  best_tier_seen: number | null
  modal_tier: number | null
  tier_distribution: Record<string, number>
}

export interface BaseDetail {
  base_name: string
  slot: string
  category: string | null
  resolves_in_app: boolean
  usage_count: number
  usage_pct: number
  rarity_mix: Record<string, number>
  common_skills: string[]
  mods: TrendingMod[]
}

export interface PricingTargetMod {
  stat_text: string
  value: number
  tier: number
  mod_type: string
  origin: string
  usage_pct: number
  trade_url?: string | null
}

export interface MarketInfo {
  chaos_floor?: number | null
  divine?: number | null
  exalted?: number | null
  num_listings?: number | null
  confidence?: string | null
  trade_url?: string | null
  error?: string | null
}

export interface MagicVariant {
  mods: string[] // [prefix_text, suffix_text]
  trade_url: string
}

export interface BasePricing {
  base_name: string
  resolved_name?: string | null
  category?: string | null
  slot?: string | null
  item_level?: number | null
  base_ilvl?: number | null
  trade_search_url?: string | null
  base_trade_url?: string | null
  magic_trade_url?: string | null
  target_mods: PricingTargetMod[]
  magic_mods: PricingTargetMod[]
  magic_variants: MagicVariant[]
  prefixes: number
  suffixes: number
  craftable: boolean
  priced: boolean
  market?: MarketInfo | null
  market_typical?: MarketInfo | null
  magic_market?: MarketInfo | null
  base_market?: MarketInfo | null
  verdict: string
  message?: string | null
  note?: string | null
}

// --- Builds browser (the per-build sample) -----------------------------------

export interface MainSkillBrief {
  name: string
  dps: number
}

export interface BuildsBrowserMeta {
  league: string
  league_slug: string
  snapshot_version: string
  scraped_at: string
  sample_size: number
  roster_size: number
  disclaimer: string
}

export interface BuildSummary {
  id: string
  character: string
  account: string
  level: number
  base_class: string | null
  ascendancy: string | null
  main_skill: MainSkillBrief | null
  life: number
  energy_shield: number
  ehp: number
  item_count: number
  notable_uniques: string[]
  poeninja_url: string
  has_pob: boolean
}

export interface BuildsListResponse {
  meta: BuildsBrowserMeta
  total: number
  builds: BuildSummary[]
  ascendancies: string[]
  skills: string[]
}

export interface BuildSkillFull {
  name: string
  dps: number
  supports: string[]
}

export interface ResolvedBuildMod {
  text: string
  origin: string // explicit | implicit | rune | crafted | fractured | desecrated | enchant
  values: number[]
  resolved: boolean
  mod_group: string | null
  mod_type: string | null // prefix | suffix | implicit
  tier: number | null
  mod_id: string | null
}

export interface ResolvedBuildItem {
  slot: string
  name: string | null
  base_type: string
  resolved_base: string | null
  category: string | null
  resolves_in_app: boolean
  rarity: string
  item_level: number
  icon: string | null
  corrupted: boolean
  runes: string[]
  mods: ResolvedBuildMod[]
}

export interface BuildDefenseFull {
  life: number
  energy_shield: number
  mana: number
  spirit: number
  ehp: number
  fire_res: number
  cold_res: number
  lightning_res: number
  chaos_res: number
}

export interface BuildDetail {
  id: string
  account: string
  character: string
  level: number
  base_class: string | null
  ascendancy: string | null
  main_skills: BuildSkillFull[]
  defense: BuildDefenseFull
  items: ResolvedBuildItem[]
  poeninja_url: string
  pob_export: string | null
  updated_utc: string
}

export interface ListBuildsParams {
  ascendancy?: string
  base_class?: string
  skill?: string
  q?: string
  limit?: number
  offset?: number
}
