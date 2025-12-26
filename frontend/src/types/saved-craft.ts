import { CraftableItem } from './crafting'

/**
 * Represents a single crafting action (currency + omens used)
 */
export interface CraftAction {
  currency: string
  omens: string[]
}

/**
 * A snapshot of a crafting session - all the data needed to replay/share a craft
 */
export interface CraftSnapshot {
  initialItem: CraftableItem
  finalItem: CraftableItem
  history: string[]  // Step descriptions
  itemHistory: CraftableItem[]  // Item state at each step
  actionHistory: (CraftAction | null)[]  // Action for each step (null for manual edits)
  currencySpent: Record<string, number>  // Total currency spent
  currencySpentHistory: Record<string, number>[]  // Currency spent at each step
}

/**
 * A locally saved craft (stored in browser localStorage)
 */
export interface LocalCraft {
  id: string  // UUID
  name: string
  description?: string
  snapshot: CraftSnapshot
  createdAt: string  // ISO timestamp
  updatedAt: string  // ISO timestamp
}

/**
 * Status of a submitted craft
 */
export enum CraftStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
}

/**
 * A public craft from the database
 */
export interface PublicCraft {
  shortId: string
  name: string
  description?: string
  submitterName?: string

  // Craft data
  initialItem: CraftableItem
  finalItem: CraftableItem
  history: string[]
  itemHistory: CraftableItem[]
  actionHistory: (CraftAction | null)[]
  currencySpent: Record<string, number>
  currencySpentHistory: Record<string, number>[]

  // Status
  status: CraftStatus
  isOfficial: boolean
  isFeatured: boolean

  // Stats
  viewCount: number
  importCount: number

  // Timestamps
  createdAt: string
  reviewedAt?: string
}

/**
 * Lightweight craft info for listings
 */
export interface CraftListItem {
  shortId: string
  name: string
  description?: string
  submitterName?: string

  // Summary info
  baseName: string
  baseCategory: string
  totalCurrencySpent: number
  stepCount: number

  // Status
  status: CraftStatus
  isOfficial: boolean
  isFeatured: boolean

  // Stats
  viewCount: number
  importCount: number

  // Timestamps
  createdAt: string
}

/**
 * Paginated list response
 */
export interface CraftListResponse {
  items: CraftListItem[]
  total: number
  page: number
  pageSize: number
}

/**
 * Request to submit a craft for review
 */
export interface CraftSubmissionRequest {
  name: string
  description?: string
  submitterName?: string
  snapshot: CraftSnapshot
}
