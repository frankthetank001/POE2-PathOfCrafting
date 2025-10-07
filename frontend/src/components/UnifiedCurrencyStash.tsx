import React, { useState } from 'react'
import { Tooltip } from './Tooltip'
import { CurrencyTooltipWrapper } from './CurrencyTooltipWrapper'

interface UnifiedCurrencyStashProps {
  categorizedCurrencies: {
    orbs: { implemented: string[], disabled: string[] }
    essences: { implemented: string[], disabled: string[] }
    bones: { implemented: string[], disabled: string[] }
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
  searchFilter = () => true
}) => {
  const [essencesExpanded, setEssencesExpanded] = useState(false)

  const renderCurrencySlot = (currency: string, isImplemented: boolean, isAvailable: boolean) => {
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

  return (
    <div className="currency-stash-unified">
      {/* Stash Header */}
      <div className="currency-stash-header">
        <h4 className="stash-tab-title">🪙 Currency Stash</h4>
      </div>

      {/* New Grid Layout */}
      <div className="currency-new-grid">
        {/* Row 1: Abyssal Bones - Full Width */}
        <div className="currency-section bones-section">
          <div className="currency-section-header">Abyssal Bones</div>
          <div className="currency-section-content bones-grid">
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

        {/* Row 2: Middle Row - Special + Orbs on left, Omens on right */}
        <div className="currency-middle-row">
          {/* Left Column - Special and Orbs stacked */}
          <div className="currency-left-column">
            {/* Special Orbs */}
            <div className="currency-section special-section">
              <div className="currency-section-header">Special</div>
              <div className="currency-section-content">
                {['Orb of Alchemy', 'Vaal Orb', 'Divine Orb', 'Orb of Annulment', 'Orb of Fracturing'].filter(searchFilter).map((currency) => {
                  const isImplemented = categorizedCurrencies.orbs.implemented.includes(currency)
                  const isAvailable = availableCurrencies.includes(currency) && isImplemented
                  return renderCurrencySlot(currency, isImplemented, isAvailable)
                })}
              </div>
            </div>

            {/* Basic Orbs */}
            <div className="currency-section orbs-section">
              <div className="currency-section-header">Orbs</div>
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

          {/* Right Column - Omens */}
          {availableOmens.length > 0 && (
            <div className="currency-section omens-section">
              <div className="currency-section-header">Omens</div>
              <div className="currency-section-content omens-grid">
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
                ].filter(omen => availableOmens.includes(omen) && searchFilter(omen)).map((omen) => {
                  const isActive = selectedOmens.includes(omen)
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
                        className={`currency-slot omen-slot ${isActive ? 'omen-active' : ''}`}
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
          )}
        </div>

        {/* Row 3: Essences - Full Width, Collapsible */}
        <div className="currency-section essences-section">
          <div
            className="currency-section-header essences-header"
            onClick={() => setEssencesExpanded(!essencesExpanded)}
            style={{ cursor: 'pointer', userSelect: 'none' }}
          >
            <span>Essences {essencesExpanded ? '▼' : '▶'}</span>
          </div>
          {essencesExpanded && (
            <div className="currency-section-content essences-content">
              <div className="essence-three-column">
                {(() => {
                  // Group essences by type - only Greater and Perfect
                  const groupedEssences: Record<string, { greater: string | null, perfect: string | null }> = {}
                  const allEssences = [...categorizedCurrencies.essences.implemented, ...categorizedCurrencies.essences.disabled]

                  allEssences.filter(searchFilter).forEach(essence => {
                    // Skip Lesser and normal tier essences
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
                    if (!essence) return <div className="essence-slot-empty" />

                    const isAvailable = availableCurrencies.includes(essence)
                    return (
                      <Tooltip
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

                    return (
                      <div key={baseType} className="essence-pair">
                        {renderEssenceSlot(group.greater, 'essence-greater')}
                        {renderEssenceSlot(group.perfect, 'essence-perfect perfect-essence')}
                      </div>
                    )
                  }).filter(Boolean)

                  // Split into left and right columns
                  const midpoint = Math.ceil(normalEssencePairs.length / 2)
                  const leftEssences = normalEssencePairs.slice(0, midpoint)
                  const rightEssences = normalEssencePairs.slice(midpoint)

                  // Corrupted essences
                  const corruptedEssences = [
                    'Essence of Delirium', 'Essence of Horror', 'Essence of Hysteria', 'Essence of Insanity', 'Essence of the Abyss'
                  ]

                  const corruptedSlots = corruptedEssences.filter(essence =>
                    categorizedCurrencies.essences.implemented.includes(essence) || categorizedCurrencies.essences.disabled.includes(essence)
                  ).filter(searchFilter).map((essence) => {
                    const isImplemented = categorizedCurrencies.essences.implemented.includes(essence)
                    const isAvailable = availableCurrencies.includes(essence) && isImplemented
                    const additionalMechanics = !isImplemented
                      ? "Not implemented yet"
                      : isAvailable
                        ? "Double-click to apply"
                        : "Not available for this item"

                    return (
                      <Tooltip
                        key={essence}
                        content={
                          <CurrencyTooltipWrapper
                            currencyName={essence}
                            additionalMechanics={additionalMechanics}
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
                    <>
                      <div className="essence-normal-grid">
                        {normalEssencePairs}
                      </div>
                      <div className="essence-corrupted-column">
                        {corruptedSlots}
                      </div>
                    </>
                  )
                })()}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
