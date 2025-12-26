import api from './api'
import { CraftListResponse, CraftListItem, PublicCraft } from '@/types/saved-craft'

function getAuthHeader(token: string) {
  return { Authorization: `Bearer ${token}` }
}

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

function transformListResponse(data: any): CraftListResponse {
  return {
    items: data.items.map(transformCraftListItem),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
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

export interface LoginResponse {
  accessToken: string
  tokenType: string
  expiresIn: number
}

export interface AdminUser {
  id: number
  username: string
  createdAt: string
  lastLogin: string | null
}

async function login(username: string, password: string): Promise<LoginResponse> {
  const response = await api.post('/admin/login', { username, password })
  return {
    accessToken: response.data.access_token,
    tokenType: response.data.token_type,
    expiresIn: response.data.expires_in,
  }
}

async function getMe(token: string): Promise<AdminUser> {
  const response = await api.get('/admin/me', {
    headers: getAuthHeader(token),
  })
  return {
    id: response.data.id,
    username: response.data.username,
    createdAt: response.data.created_at,
    lastLogin: response.data.last_login,
  }
}

async function listCrafts(
  token: string,
  params: { page?: number; pageSize?: number; status?: string } = {}
): Promise<CraftListResponse> {
  const response = await api.get('/admin/crafts', {
    headers: getAuthHeader(token),
    params: {
      page: params.page ?? 1,
      page_size: params.pageSize ?? 20,
      status: params.status,
    },
  })
  return transformListResponse(response.data)
}

async function getCraft(token: string, craftId: number): Promise<PublicCraft> {
  const response = await api.get(`/admin/crafts/${craftId}`, {
    headers: getAuthHeader(token),
  })
  return transformPublicCraft(response.data)
}

async function approveCraft(token: string, craftId: number): Promise<void> {
  await api.post(`/admin/crafts/${craftId}/approve`, {}, {
    headers: getAuthHeader(token),
  })
}

async function rejectCraft(token: string, craftId: number): Promise<void> {
  await api.post(`/admin/crafts/${craftId}/reject`, {}, {
    headers: getAuthHeader(token),
  })
}

async function toggleFeatured(token: string, craftId: number): Promise<boolean> {
  const response = await api.post(`/admin/crafts/${craftId}/feature`, {}, {
    headers: getAuthHeader(token),
  })
  return response.data.is_featured
}

async function deleteCraft(token: string, craftId: number): Promise<void> {
  await api.delete(`/admin/crafts/${craftId}`, {
    headers: getAuthHeader(token),
  })
}

export const adminApi = {
  login,
  getMe,
  listCrafts,
  getCraft,
  approveCraft,
  rejectCraft,
  toggleFeatured,
  deleteCraft,
}
