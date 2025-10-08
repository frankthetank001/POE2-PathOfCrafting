import { useState, useEffect } from 'react'
import { craftingApi } from '@/services/crafting-api'
import type { CraftableItem, ItemModifier } from '@/types/crafting'

interface AvailableModsPanelProps {
  item: CraftableItem
  collapsed?: boolean
}

export function AvailableModsPanel({ item, collapsed = false }: AvailableModsPanelProps) {
  const [availableMods, setAvailableMods] = useState<{
    prefixes: ItemModifier[]
    suffixes: ItemModifier[]
    total_prefixes: number
    total_suffixes: number
  }>({
    prefixes: [],
    suffixes: [],
    total_prefixes: 0,
    total_suffixes: 0,
  })
  const [loading, setLoading] = useState(false)
  const [ilvlFilter, setIlvlFilter] = useState<number | ''>('')
  const [searchFilter, setSearchFilter] = useState<string>('')

  useEffect(() => {
    if (item) {
      loadAvailableMods()
    }
  }, [item])

  const loadAvailableMods = async () => {
    setLoading(true)
    try {
      const mods = await craftingApi.getAvailableMods(item)
      setAvailableMods(mods)
    } catch (err) {
      console.error('Failed to load available mods:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatModText = (mod: ItemModifier): string => {
    const minValue = mod.stat_min || 0
    const maxValue = mod.stat_max || minValue

    if (mod.stat_text.includes('{}')) {
      if (minValue === maxValue) {
        return mod.stat_text.replace('{}', minValue.toString())
      } else {
        return mod.stat_text.replace('{}', `(${minValue}-${maxValue})`)
      }
    }
    return mod.stat_text
  }

  const filterMods = (mods: ItemModifier[]): ItemModifier[] => {
    return mods.filter(mod => {
      // Item level filter
      if (ilvlFilter !== '' && mod.required_ilvl && mod.required_ilvl > ilvlFilter) {
        return false
      }

      // Search filter
      if (searchFilter) {
        const search = searchFilter.toLowerCase()
        const formattedText = formatModText(mod).toLowerCase()
        const modName = mod.name.toLowerCase()
        const tags = (mod.tags || []).join(' ').toLowerCase()
        const tier = `t${mod.tier}`.toLowerCase()
        const ilvl = mod.required_ilvl ? `i${mod.required_ilvl}`.toLowerCase() : ''
        const modGroup = (mod.mod_group || '').toLowerCase()

        // Search across all fields
        if (!formattedText.includes(search) &&
            !modName.includes(search) &&
            !tags.includes(search) &&
            !tier.includes(search) &&
            !ilvl.includes(search) &&
            !modGroup.includes(search)) {
          return false
        }
      }

      return true
    })
  }

  const groupModsByGroup = (mods: ItemModifier[]): Record<string, ItemModifier[]> => {
    const grouped: Record<string, ItemModifier[]> = {}

    mods.forEach(mod => {
      const group = mod.mod_group || 'Other'
      if (!grouped[group]) {
        grouped[group] = []
      }
      grouped[group].push(mod)
    })

    // Sort groups by name, with "Other" last
    const sortedGroups: Record<string, ItemModifier[]> = {}
    Object.keys(grouped)
      .sort((a, b) => {
        if (a === 'Other') return 1
        if (b === 'Other') return -1
        return a.localeCompare(b)
      })
      .forEach(group => {
        sortedGroups[group] = grouped[group].sort((a, b) => a.tier - b.tier)
      })

    return sortedGroups
  }

  const isModUnavailable = (mod: ItemModifier): boolean => {
    return mod.required_ilvl ? mod.required_ilvl > item.item_level : false
  }

  if (collapsed) {
    return (
      <div className="available-mods-panel collapsed">
        <div className="mods-summary">
          <div className="mod-count">
            P: {availableMods.total_prefixes}
          </div>
          <div className="mod-count">
            S: {availableMods.total_suffixes}
          </div>
        </div>
      </div>
    )
  }

  const filteredPrefixes = filterMods(availableMods.prefixes)
  const filteredSuffixes = filterMods(availableMods.suffixes)
  const groupedPrefixes = groupModsByGroup(filteredPrefixes)
  const groupedSuffixes = groupModsByGroup(filteredSuffixes)

  return (
    <div className="available-mods-panel">
      {/* Filters */}
      <div className="mods-filters">
        <div className="filter-group">
          <label htmlFor="ilvl-filter">Max iLvl:</label>
          <input
            id="ilvl-filter"
            type="number"
            min="1"
            max="100"
            value={ilvlFilter}
            onChange={(e) => setIlvlFilter(e.target.value ? parseInt(e.target.value) : '')}
            placeholder={item.item_level.toString()}
          />
        </div>
        <div className="filter-group">
          <label htmlFor="search-filter">Search:</label>
          <input
            id="search-filter"
            type="text"
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            placeholder="Search mods..."
          />
        </div>
      </div>

      {/* Stats */}
      <div className="mods-stats">
        <div className="stat-item">
          <span>Prefixes:</span>
          <span>{filteredPrefixes.length} / {availableMods.total_prefixes}</span>
        </div>
        <div className="stat-item">
          <span>Suffixes:</span>
          <span>{filteredSuffixes.length} / {availableMods.total_suffixes}</span>
        </div>
      </div>

      {loading ? (
        <div className="loading">Loading available mods...</div>
      ) : (
        <div className="mods-columns">
          {/* Prefixes Column */}
          <div className="mods-column">
            <h4>Prefixes ({filteredPrefixes.length})</h4>
            <div className="mods-list">
              {Object.entries(groupedPrefixes).map(([groupName, mods]) => (
                <div key={groupName} className="mod-group">
                  {Object.keys(groupedPrefixes).length > 1 && (
                    <div className="mod-group-header">{groupName}</div>
                  )}
                  {mods.map((mod, index) => (
                    <div
                      key={`${mod.name}-${mod.tier}-${index}`}
                      className={`mod-item ${isModUnavailable(mod) ? 'unavailable' : ''}`}
                      title={`${mod.name} (Tier ${mod.tier})${mod.required_ilvl ? ` - Requires iLvl ${mod.required_ilvl}` : ''}`}
                    >
                      <div className="mod-text">{formatModText(mod)}</div>
                      <div className="mod-meta">
                        <span className="mod-tier">T{mod.tier}</span>
                        {mod.required_ilvl && (
                          <span className="mod-ilvl">i{mod.required_ilvl}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>

          {/* Suffixes Column */}
          <div className="mods-column">
            <h4>Suffixes ({filteredSuffixes.length})</h4>
            <div className="mods-list">
              {Object.entries(groupedSuffixes).map(([groupName, mods]) => (
                <div key={groupName} className="mod-group">
                  {Object.keys(groupedSuffixes).length > 1 && (
                    <div className="mod-group-header">{groupName}</div>
                  )}
                  {mods.map((mod, index) => (
                    <div
                      key={`${mod.name}-${mod.tier}-${index}`}
                      className={`mod-item ${isModUnavailable(mod) ? 'unavailable' : ''}`}
                      title={`${mod.name} (Tier ${mod.tier})${mod.required_ilvl ? ` - Requires iLvl ${mod.required_ilvl}` : ''}`}
                    >
                      <div className="mod-text">{formatModText(mod)}</div>
                      <div className="mod-meta">
                        <span className="mod-tier">T{mod.tier}</span>
                        {mod.required_ilvl && (
                          <span className="mod-ilvl">i{mod.required_ilvl}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}