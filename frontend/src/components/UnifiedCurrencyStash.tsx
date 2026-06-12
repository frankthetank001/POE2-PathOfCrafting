import React, { useState, useEffect } from 'react'
import { Tooltip } from './Tooltip'
import { CurrencyTooltipWrapper } from './CurrencyTooltipWrapper'
import { useGameVersion, isFeatureAvailable } from '../contexts/VersionContext'

const HIDE_UNAVAILABLE_KEY = 'currency-stash-hide-unavailable'
const ACTIVE_TAB_KEY = 'currency-stash-active-tab'

type CurrencyTab = 'orbs' | 'essences' | 'alloys' | 'bones' | 'catalysts'

interface UnifiedCurrencyStashProps {
  categorizedCurrencies: {
    orbs: { implemented: string[], disabled: string[] }
    essences: { implemented: string[], disabled: string[] }
    alloys: { implemented: string[], disabled: string[] }
    bones: { implemented: string[], disabled: string[] }
    catalysts: { implemented: string[], disabled: string[] }
  }
  availableCurrencies: string[]
  availableOmens: string[]
  selectedOmens: string[]
  setSelectedOmens: React.Dispatch<React.SetStateAction<string[]>>
  handleCraft: (currency: string) => void
  getCurrencyIconUrl: (currency: string) => string
  getOmenIconUrl: (omen: string) => string
  onCurrencyDragStart?: (currency: string) => void
  onCurrencyDragEnd?: () => void
  searchFilter?: (currencyName: string) => boolean
  isJewelry?: boolean // Whether current item is ring/amulet
}

export const UnifiedCurrencyStash: React.FC<UnifiedCurrencyStashProps> = ({
  categorizedCurrencies,
  availableCurrencies,
  availableOmens,
  selectedOmens,
  setSelectedOmens,
  handleCraft,
  getCurrencyIconUrl,
  getOmenIconUrl,
  onCurrencyDragStart,
  onCurrencyDragEnd,
  searchFilter = () => true,
  isJewelry = false
}) => {
  const { gameVersion } = useGameVersion()

  // Hide unavailable toggle with sessionStorage persistence
  const [hideUnavailable, setHideUnavailable] = useState(() => {
    const stored = sessionStorage.getItem(HIDE_UNAVAILABLE_KEY)
    return stored === 'true'
  })

  // Active tab with sessionStorage persistence
  const [activeTab, setActiveTab] = useState<CurrencyTab>(() => {
    const stored = sessionStorage.getItem(ACTIVE_TAB_KEY) as CurrencyTab
    return stored && ['orbs', 'essences', 'alloys', 'bones', 'catalysts'].includes(stored) ? stored : 'orbs'
  })

  useEffect(() => {
    sessionStorage.setItem(HIDE_UNAVAILABLE_KEY, String(hideUnavailable))
  }, [hideUnavailable])

  useEffect(() => {
    sessionStorage.setItem(ACTIVE_TAB_KEY, activeTab)
  }, [activeTab])

  // If on catalysts tab but not jewelry, switch to orbs
  useEffect(() => {
    if (activeTab === 'catalysts' && !isJewelry) {
      setActiveTab('orbs')
    }
  }, [isJewelry, activeTab])

  // Filter omens based on game version
  const versionFilteredOmens = availableOmens.filter(omen => isFeatureAvailable(omen, gameVersion))

  const renderCurrencySlot = (currency: string, isImplemented: boolean, isAvailable: boolean) => {
    if (hideUnavailable && !isAvailable) {
      return null
    }

    const additionalMechanics = !isImplemented
      ? "Not implemented yet"
      : isAvailable
        ? "Double-click to apply"
        : "Not available for this item"

    return (
      <Tooltip
        key={currency}
        content={
          <CurrencyTooltipWrapper
            currencyName={currency}
            additionalMechanics={additionalMechanics}
          />
        }
        delay={0}
        position="right"
      >
        <div
          className={`currency-slot ${!isAvailable ? 'currency-disabled' : ''}`}
          onClick={() => isAvailable && handleCraft(currency)}
          draggable={isAvailable}
          onDragStart={() => isAvailable && onCurrencyDragStart?.(currency)}
          onDragEnd={() => onCurrencyDragEnd?.()}
          style={{ cursor: isAvailable ? 'grab' : 'not-allowed' }}
        >
          <img
            src={getCurrencyIconUrl(currency)}
            alt={currency}
            className="currency-icon"
            onError={(e) => {
              (e.target as HTMLImageElement).src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
            }}
          />
        </div>
      </Tooltip>
    )
  }

  // Tab content renderers
  const renderOrbsTab = () => (
    <div className="tab-content-orbs">
      {/* Special Orbs */}
      <div className="currency-section special-section">
        <div className="currency-section-header">Special</div>
        <div className="currency-section-content currency-grid">
          {['Orb of Alchemy', 'Vaal Orb', 'Divine Orb', 'Orb of Annulment', 'Orb of Fracturing'].filter(searchFilter).map((currency) => {
            const isImplemented = categorizedCurrencies.orbs.implemented.includes(currency)
            const isAvailable = availableCurrencies.includes(currency) && isImplemented
            return renderCurrencySlot(currency, isImplemented, isAvailable)
          })}
        </div>
      </div>

      {/* Basic Orbs */}
      <div className="currency-section orbs-section">
        <div className="currency-section-header">Crafting Orbs</div>
        <div className="currency-section-content orbs-grid">
          {[
            ['Orb of Transmutation', 'Greater Orb of Transmutation', 'Perfect Orb of Transmutation'],
            ['Orb of Augmentation', 'Greater Orb of Augmentation', 'Perfect Orb of Augmentation'],
            ['Regal Orb', 'Greater Regal Orb', 'Perfect Regal Orb'],
            ['Chaos Orb', 'Greater Chaos Orb', 'Perfect Chaos Orb'],
            ['Exalted Orb', 'Greater Exalted Orb', 'Perfect Exalted Orb']
          ].map(family => family.filter(searchFilter)).filter(family => family.length > 0).map((family, familyIndex) => (
            <div key={familyIndex} className="currency-family">
              {family.map((currency) => {
                const isImplemented = categorizedCurrencies.orbs.implemented.includes(currency)
                const isAvailable = availableCurrencies.includes(currency) && isImplemented
                return renderCurrencySlot(currency, isImplemented, isAvailable)
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  const renderEssencesTab = () => {
    const groupedEssences: Record<string, { greater: string | null, perfect: string | null }> = {}
    const allEssences = [...categorizedCurrencies.essences.implemented, ...categorizedCurrencies.essences.disabled]

    allEssences.filter(searchFilter).forEach(essence => {
      if (!essence.includes('Greater') && !essence.includes('Perfect')) return

      let baseType = ''
      if (essence.includes('the Body')) baseType = 'the Body'
      else if (essence.includes('the Mind')) baseType = 'the Mind'
      else if (essence.includes('Enhancement')) baseType = 'Enhancement'
      else if (essence.includes('Flames')) baseType = 'Flames'
      else if (essence.includes('Insulation')) baseType = 'Insulation'
      else if (essence.includes('Ice')) baseType = 'Ice'
      else if (essence.includes('Thawing')) baseType = 'Thawing'
      else if (essence.includes('Electricity')) baseType = 'Electricity'
      else if (essence.includes('Grounding')) baseType = 'Grounding'
      else if (essence.includes('Ruin')) baseType = 'Ruin'
      else if (essence.includes('Command')) baseType = 'Command'
      else if (essence.includes('Abrasion')) baseType = 'Abrasion'
      else if (essence.includes('Sorcery')) baseType = 'Sorcery'
      else if (essence.includes('Haste')) baseType = 'Haste'
      else if (essence.includes('Alacrity')) baseType = 'Alacrity'
      else if (essence.includes('Seeking')) baseType = 'Seeking'
      else if (essence.includes('Battle')) baseType = 'Battle'
      else if (essence.includes('the Infinite')) baseType = 'the Infinite'
      else if (essence.includes('Opulence')) baseType = 'Opulence'
      else return

      if (!groupedEssences[baseType]) {
        groupedEssences[baseType] = { greater: null, perfect: null }
      }

      if (essence.includes('Perfect')) {
        groupedEssences[baseType].perfect = essence
      } else if (essence.includes('Greater')) {
        groupedEssences[baseType].greater = essence
      }
    })

    const allEssenceTypes = [
      'Flames', 'Ice', 'Electricity', 'Abrasion', 'Sorcery',
      'the Body', 'the Mind', 'Haste', 'Enhancement', 'Battle',
      'Insulation', 'Thawing', 'Grounding', 'Command', 'Ruin',
      'the Infinite', 'Alacrity', 'Seeking', 'Opulence'
    ]

    const renderEssenceSlot = (essence: string | null, className: string) => {
      if (!essence) return hideUnavailable ? null : <div className="essence-slot-empty" />

      const isAvailable = availableCurrencies.includes(essence)
      if (hideUnavailable && !isAvailable) {
        return null
      }
      return (
        <Tooltip
          key={essence}
          content={
            <CurrencyTooltipWrapper
              currencyName={essence}
              additionalMechanics={isAvailable ? "Double-click to apply" : "Not available for this item"}
            />
          }
          delay={0}
          position="right"
        >
          <div
            className={`currency-slot ${className} ${!isAvailable ? 'currency-disabled' : ''}`}
            onClick={() => isAvailable && handleCraft(essence)}
            draggable={isAvailable}
            onDragStart={() => isAvailable && onCurrencyDragStart?.(essence)}
            onDragEnd={() => onCurrencyDragEnd?.()}
            style={{ cursor: isAvailable ? 'grab' : 'not-allowed' }}
          >
            <img
              src={getCurrencyIconUrl(essence)}
              alt={essence}
              className="currency-icon"
              onError={(e) => {
                (e.target as HTMLImageElement).src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
              }}
            />
          </div>
        </Tooltip>
      )
    }

    const normalEssencePairs = allEssenceTypes.map((baseType) => {
      const group = groupedEssences[baseType]
      if (!group || (!group.greater && !group.perfect)) return null

      const greaterSlot = renderEssenceSlot(group.greater, 'essence-greater')
      const perfectSlot = renderEssenceSlot(group.perfect, 'essence-perfect perfect-essence')

      if (!greaterSlot && !perfectSlot) return null

      return (
        <div key={baseType} className="essence-pair">
          {greaterSlot}
          {perfectSlot}
        </div>
      )
    }).filter(Boolean)

    const corruptedEssences = [
      'Essence of Delirium', 'Essence of Horror', 'Essence of Hysteria', 'Essence of Insanity', 'Essence of the Abyss'
    ]

    const corruptedSlots = corruptedEssences.filter(essence =>
      categorizedCurrencies.essences.implemented.includes(essence) || categorizedCurrencies.essences.disabled.includes(essence)
    ).filter(searchFilter).map((essence) => {
      const isImplemented = categorizedCurrencies.essences.implemented.includes(essence)
      const isAvailable = availableCurrencies.includes(essence) && isImplemented

      if (hideUnavailable && !isAvailable) {
        return null
      }

      return (
        <Tooltip
          key={essence}
          content={
            <CurrencyTooltipWrapper
              currencyName={essence}
              additionalMechanics={!isImplemented ? "Not implemented yet" : isAvailable ? "Double-click to apply" : "Not available for this item"}
            />
          }
          delay={0}
          position="right"
        >
          <div
            className={`currency-slot essence-corrupted ${!isAvailable ? 'currency-disabled' : ''}`}
            onClick={() => isAvailable && handleCraft(essence)}
            draggable={isAvailable}
            onDragStart={() => isAvailable && onCurrencyDragStart?.(essence)}
            onDragEnd={() => onCurrencyDragEnd?.()}
            style={{ cursor: isAvailable ? 'grab' : 'not-allowed' }}
          >
            <img
              src={getCurrencyIconUrl(essence)}
              alt={essence}
              className="currency-icon"
              onError={(e) => {
                (e.target as HTMLImageElement).src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
              }}
            />
          </div>
        </Tooltip>
      )
    })

    return (
      <div className="tab-content-essences">
        <div className="essence-three-column">
          <div className="essence-normal-grid">
            {normalEssencePairs}
          </div>
          <div className="essence-corrupted-column">
            {corruptedSlots}
          </div>
        </div>
      </div>
    )
  }

  const renderBonesTab = () => (
    <div className="tab-content-bones">
      <div className="currency-section-content currency-grid">
        {[
          'Ancient Collarbone', 'Gnawed Collarbone', 'Preserved Collarbone',
          'Ancient Jawbone', 'Gnawed Jawbone', 'Preserved Jawbone',
          'Ancient Rib', 'Gnawed Rib', 'Preserved Rib',
          'Preserved Cranium', 'Preserved Vertebrae'
        ].filter(searchFilter).map((currency) => {
          const isImplemented = categorizedCurrencies.bones.implemented.includes(currency)
          const isAvailable = availableCurrencies.includes(currency) && isImplemented
          return renderCurrencySlot(currency, isImplemented, isAvailable)
        })}
      </div>
    </div>
  )

  const renderAlloysTab = () => (
    <div className="tab-content-alloys">
      <div className="currency-section-content currency-grid">
        {categorizedCurrencies.alloys.implemented.filter(searchFilter).map((alloy) => {
          const isAvailable = availableCurrencies.includes(alloy)
          return renderCurrencySlot(alloy, true, isAvailable)
        })}
      </div>
    </div>
  )

  const renderCatalystsTab = () => (
    <div className="tab-content-catalysts">
      <div className="currency-section-content currency-grid">
        {categorizedCurrencies.catalysts.implemented.filter(searchFilter).map((catalyst) => {
          const isAvailable = availableCurrencies.includes(catalyst)
          if (hideUnavailable && !isAvailable) return null
          return (
            <Tooltip
              key={catalyst}
              content={
                <CurrencyTooltipWrapper
                  currencyName={catalyst}
                  additionalMechanics={isAvailable ? "Double-click to apply" : "Only for rings and amulets"}
                />
              }
              delay={0}
              position="right"
            >
              <div
                className={`currency-slot catalyst-slot ${!isAvailable ? 'currency-disabled' : ''}`}
                onClick={() => isAvailable && handleCraft(catalyst)}
                draggable={isAvailable}
                onDragStart={() => isAvailable && onCurrencyDragStart?.(catalyst)}
                onDragEnd={() => onCurrencyDragEnd?.()}
                style={{ cursor: isAvailable ? 'grab' : 'not-allowed' }}
              >
                <img
                  src={getCurrencyIconUrl(catalyst)}
                  alt={catalyst}
                  className="currency-icon"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
                  }}
                />
              </div>
            </Tooltip>
          )
        })}
      </div>
    </div>
  )

  // Map omens to relevant tabs
  const getOmenRelevance = (omen: string): CurrencyTab[] => {
    if (omen.includes('Exaltation')) return ['orbs', 'catalysts'] // Catalysing is for catalysts too
    if (omen.includes('Coronation')) return ['orbs'] // Regal
    if (omen.includes('Erasure') || omen.includes('Whittling')) return ['orbs'] // Chaos
    if (omen.includes('Annulment')) return ['orbs']
    if (omen.includes('Alchemy')) return ['orbs']
    if (omen.includes('Crystallisation')) return ['essences']
    if (omen.includes('Necromancy') || omen.includes('Abyssal') ||
        omen.includes('Sovereign') || omen.includes('Liege') ||
        omen.includes('Blackblooded') || omen.includes('Putrefaction') ||
        omen.includes('Light')) return ['bones']
    if (omen.includes('Corruption')) return ['orbs'] // Vaal
    return ['orbs', 'essences', 'bones', 'catalysts'] // Default: relevant to all
  }

  const renderOmensSection = () => (
    <div className="currency-section omens-section">
      <div className="currency-section-header">Omens</div>
      <div className="currency-grid">
        {[
          // Exalted Omens
          'Omen of Greater Exaltation', 'Omen of Sinistral Exaltation', 'Omen of Dextral Exaltation',
          'Omen of Homogenising Exaltation', 'Omen of Catalysing Exaltation',
          // Regal Omens
          'Omen of Sinistral Coronation', 'Omen of Dextral Coronation', 'Omen of Homogenising Coronation',
          // Chaos Omens
          'Omen of Whittling', 'Omen of Sinistral Erasure', 'Omen of Dextral Erasure',
          // Annulment Omens
          'Omen of Greater Annulment', 'Omen of Sinistral Annulment', 'Omen of Dextral Annulment',
          // Alchemy Omens
          'Omen of Sinistral Alchemy', 'Omen of Dextral Alchemy',
          // Essence Omens
          'Omen of Sinistral Crystallisation', 'Omen of Dextral Crystallisation',
          // Desecration/Abyssal Omens
          'Omen of Abyssal Echoes', 'Omen of Sinistral Necromancy', 'Omen of Dextral Necromancy',
          'Omen of the Sovereign', 'Omen of the Liege', 'Omen of the Blackblooded',
          'Omen of Putrefaction', 'Omen of Light',
          // Corruption
          'Omen of Corruption'
        ].filter(omen => versionFilteredOmens.includes(omen) && searchFilter(omen)).map((omen) => {
          const isActive = selectedOmens.includes(omen)
          const relevantTabs = getOmenRelevance(omen)
          const isRelevant = relevantTabs.includes(activeTab)
          return (
            <Tooltip
              key={omen}
              content={
                <CurrencyTooltipWrapper
                  currencyName={omen}
                  additionalMechanics={isActive ? "Click to deselect" : "Click to select"}
                />
              }
              delay={0}
              position="right"
            >
              <div
                className={`currency-slot omen-slot ${isActive ? 'omen-active' : ''} ${!isRelevant ? 'omen-dimmed' : ''}`}
                onClick={() => {
                  setSelectedOmens(prev =>
                    prev.includes(omen)
                      ? prev.filter(o => o !== omen)
                      : [...prev, omen]
                  )
                }}
              >
                <img
                  src={getOmenIconUrl(omen)}
                  alt={omen}
                  className="currency-icon omen-icon"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
                  }}
                />
              </div>
            </Tooltip>
          )
        })}
      </div>
    </div>
  )

  return (
    <div className="currency-stash-unified currency-stash-tabbed">
      {/* Stash Header */}
      <div className="currency-stash-header">
        <h4 className="stash-tab-title">Currency Stash</h4>
        <label className="hide-unavailable-toggle">
          <input
            type="checkbox"
            checked={hideUnavailable}
            onChange={(e) => setHideUnavailable(e.target.checked)}
          />
          <span className="toggle-slider"></span>
          <span className="toggle-label">Hide unavailable</span>
        </label>
      </div>

      {/* Tab Buttons */}
      <div className="currency-tabs">
        <button
          className={`currency-tab ${activeTab === 'orbs' ? 'active' : ''}`}
          onClick={() => setActiveTab('orbs')}
        >
          Orbs
        </button>
        <button
          className={`currency-tab ${activeTab === 'essences' ? 'active' : ''}`}
          onClick={() => setActiveTab('essences')}
        >
          Essences
        </button>
        <button
          className={`currency-tab ${activeTab === 'alloys' ? 'active' : ''}`}
          onClick={() => setActiveTab('alloys')}
        >
          Alloys
        </button>
        <button
          className={`currency-tab ${activeTab === 'bones' ? 'active' : ''}`}
          onClick={() => setActiveTab('bones')}
        >
          Bones
        </button>
        {isJewelry && (
          <button
            className={`currency-tab ${activeTab === 'catalysts' ? 'active' : ''}`}
            onClick={() => setActiveTab('catalysts')}
          >
            Catalysts
          </button>
        )}
      </div>

      {/* Tab Content */}
      <div className="currency-tab-content">
        {activeTab === 'orbs' && renderOrbsTab()}
        {activeTab === 'essences' && renderEssencesTab()}
        {activeTab === 'alloys' && renderAlloysTab()}
        {activeTab === 'bones' && renderBonesTab()}
        {activeTab === 'catalysts' && isJewelry && renderCatalystsTab()}
      </div>

      {/* Omens - Always Visible */}
      {versionFilteredOmens.length > 0 && renderOmensSection()}
    </div>
  )
}
