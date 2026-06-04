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
