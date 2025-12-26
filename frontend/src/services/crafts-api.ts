import api from './api'
import {
  CraftSnapshot,
  CraftListResponse,
  CraftSubmissionRequest,
  PublicCraft,
  CraftListItem,
} from '@/types/saved-craft'

/**
 * Convert snake_case API response to camelCase frontend types
 */
function transformCraftListItem(item: any): CraftListItem {
  return {
    shortId: item.short_id,
    name: item.name,
    description: item.description,
    submitterName: item.submitter_name,
    baseName: item.base_name,
    baseCategory: item.base_category,
    totalCurrencySpent: item.total_currency_spent,
    stepCount: item.step_count,
    status: item.status,
    isOfficial: item.is_official,
    isFeatured: item.is_featured,
    viewCount: item.view_count,
    importCount: item.import_count,
    createdAt: item.created_at,
  }
}

function transformPublicCraft(data: any): PublicCraft {
  return {
    shortId: data.short_id,
    name: data.name,
    description: data.description,
    submitterName: data.submitter_name,
    initialItem: data.initial_item,
    finalItem: data.final_item,
    history: data.history,
    itemHistory: data.item_history,
    actionHistory: data.action_history,
    currencySpent: data.currency_spent,
    currencySpentHistory: data.currency_spent_history,
    status: data.status,
    isOfficial: data.is_official,
    isFeatured: data.is_featured,
    viewCount: data.view_count,
    importCount: data.import_count,
    createdAt: data.created_at,
    reviewedAt: data.reviewed_at,
  }
}

function transformListResponse(data: any): CraftListResponse {
  return {
    items: data.items.map(transformCraftListItem),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
  }
}

export interface ListCraftsParams {
  page?: number
  pageSize?: number
  search?: string
  baseCategory?: string
  featuredOnly?: boolean
}

/**
 * List approved public crafts
 */
async function listCrafts(params: ListCraftsParams = {}): Promise<CraftListResponse> {
  const response = await api.get('/crafts', {
    params: {
      page: params.page ?? 1,
      page_size: params.pageSize ?? 20,
      search: params.search,
      base_category: params.baseCategory,
      featured_only: params.featuredOnly ?? false,
    },
  })
  return transformListResponse(response.data)
}

/**
 * Get featured crafts
 */
async function getFeaturedCrafts(limit = 10): Promise<CraftListResponse> {
  const response = await api.get('/crafts/featured', { params: { limit } })
  return transformListResponse(response.data)
}

/**
 * Get a single craft by short ID
 */
async function getCraft(shortId: string): Promise<PublicCraft> {
  const response = await api.get(`/crafts/${shortId}`)
  return transformPublicCraft(response.data)
}

/**
 * Submit a craft for admin review
 */
async function submitCraft(request: CraftSubmissionRequest): Promise<{ shortId: string }> {
  const response = await api.post('/crafts/submit', {
    name: request.name,
    description: request.description,
    submitter_name: request.submitterName,
    initial_item: request.snapshot.initialItem,
    final_item: request.snapshot.finalItem,
    history: request.snapshot.history,
    item_history: request.snapshot.itemHistory,
    action_history: request.snapshot.actionHistory,
    currency_spent: request.snapshot.currencySpent,
    currency_spent_history: request.snapshot.currencySpentHistory,
  })
  return { shortId: response.data.short_id }
}

/**
 * Record that a craft was imported into the simulator
 */
async function recordImport(shortId: string): Promise<void> {
  await api.post(`/crafts/${shortId}/import`)
}

export const craftsApi = {
  listCrafts,
  getFeaturedCrafts,
  getCraft,
  submitCraft,
  recordImport,
}
