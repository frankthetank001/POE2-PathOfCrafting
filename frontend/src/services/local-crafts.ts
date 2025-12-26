import { LocalCraft, CraftSnapshot } from '@/types/saved-craft'

const STORAGE_KEY = 'poe2-saved-crafts'
const MAX_CRAFTS = 50

/**
 * Generate a UUID for local crafts
 */
function generateId(): string {
  return crypto.randomUUID()
}

/**
 * Get all locally saved crafts from localStorage
 */
function getAll(): LocalCraft[] {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    if (!data) return []
    return JSON.parse(data) as LocalCraft[]
  } catch (error) {
    console.error('Failed to load local crafts:', error)
    return []
  }
}

/**
 * Save crafts array to localStorage
 */
function saveAll(crafts: LocalCraft[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(crafts))
  } catch (error) {
    console.error('Failed to save local crafts:', error)
    throw new Error('Failed to save craft. Storage may be full.')
  }
}

/**
 * Save a new craft locally
 * @throws Error if max crafts limit reached
 */
function save(name: string, snapshot: CraftSnapshot, description?: string): LocalCraft {
  const crafts = getAll()

  if (crafts.length >= MAX_CRAFTS) {
    throw new Error(`Maximum of ${MAX_CRAFTS} saved crafts reached. Please delete some crafts first.`)
  }

  const now = new Date().toISOString()
  const craft: LocalCraft = {
    id: generateId(),
    name,
    description,
    snapshot,
    createdAt: now,
    updatedAt: now,
  }

  crafts.unshift(craft)  // Add to beginning (most recent first)
  saveAll(crafts)

  return craft
}

/**
 * Update an existing local craft
 */
function update(id: string, updates: Partial<Pick<LocalCraft, 'name' | 'description' | 'snapshot'>>): LocalCraft | null {
  const crafts = getAll()
  const index = crafts.findIndex(c => c.id === id)

  if (index === -1) return null

  const craft = crafts[index]
  const updated: LocalCraft = {
    ...craft,
    ...updates,
    updatedAt: new Date().toISOString(),
  }

  crafts[index] = updated
  saveAll(crafts)

  return updated
}

/**
 * Get a single craft by ID
 */
function get(id: string): LocalCraft | null {
  const crafts = getAll()
  return crafts.find(c => c.id === id) || null
}

/**
 * Delete a craft by ID
 */
function remove(id: string): boolean {
  const crafts = getAll()
  const index = crafts.findIndex(c => c.id === id)

  if (index === -1) return false

  crafts.splice(index, 1)
  saveAll(crafts)

  return true
}

/**
 * Export a craft as a JSON string (for manual sharing)
 */
function exportCraft(id: string): string | null {
  const craft = get(id)
  if (!craft) return null

  // Create a shareable version without local metadata
  const shareable = {
    name: craft.name,
    description: craft.description,
    snapshot: craft.snapshot,
    exportedAt: new Date().toISOString(),
  }

  return JSON.stringify(shareable, null, 2)
}

/**
 * Import a craft from a JSON string
 */
function importCraft(json: string): LocalCraft {
  try {
    const data = JSON.parse(json)

    if (!data.name || !data.snapshot) {
      throw new Error('Invalid craft data: missing name or snapshot')
    }

    // Validate snapshot has required fields
    const snapshot = data.snapshot as CraftSnapshot
    if (!snapshot.initialItem || !snapshot.finalItem || !snapshot.history) {
      throw new Error('Invalid craft data: incomplete snapshot')
    }

    return save(data.name, snapshot, data.description)
  } catch (error) {
    if (error instanceof SyntaxError) {
      throw new Error('Invalid JSON format')
    }
    throw error
  }
}

/**
 * Get the count of saved crafts
 */
function count(): number {
  return getAll().length
}

/**
 * Check if storage limit is reached
 */
function isAtLimit(): boolean {
  return count() >= MAX_CRAFTS
}

/**
 * Clear all saved crafts (use with caution!)
 */
function clearAll(): void {
  localStorage.removeItem(STORAGE_KEY)
}

export const localCraftsService = {
  getAll,
  get,
  save,
  update,
  remove,
  exportCraft,
  importCraft,
  count,
  isAtLimit,
  clearAll,
  MAX_CRAFTS,
}
