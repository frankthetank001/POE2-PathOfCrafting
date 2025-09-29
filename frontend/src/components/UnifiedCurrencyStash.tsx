import React from 'react'
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
}

export const UnifiedCurrencyStash: React.FC<UnifiedCurrencyStashProps> = ({
  categorizedCurrencies,
  availableCurrencies,
  availableOmens,
  selectedOmens,
  setSelectedOmens,
  handleCraft,
  getCurrencyIconUrl,
  getOmenIconUrl
}) => {
  return (
    <div className="currency-stash-unified">
      {/* Stash Header */}
      <div className="currency-stash-header">
        <h4 className="stash-tab-title">🪙 Currency Stash</h4>
      </div>

      {/* Main Currency Grid - Unified Layout */}
      <div className="currency-unified-grid">
        {/* Row 1: Abyssal Bones - Horizontal section at top */}
        <div className="currency-row bones-row">
          <div className="currency-row-label">Abyssal Bones</div>
          <div className="currency-icons-row">
            {[
              // Gnawed Bones (Max Item Level: 64)
              'Gnawed Jawbone', 'Gnawed Rib', 'Gnawed Collarbone',
              // Preserved Bones (Mid-tier)
              'Preserved Jawbone', 'Preserved Rib', 'Preserved Collarbone', 'Preserved Cranium', 'Preserved Vertebrae',
              // Ancient Bones (Min Modifier Level: 40)
              'Ancient Jawbone', 'Ancient Rib', 'Ancient Collarbone'
            ].map((currency) => {
              const isImplemented = categorizedCurrencies.bones.implemented.includes(currency)
              const isAvailable = availableCurrencies.includes(currency) && isImplemented
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
            })}
          </div>
        </div>

        {/* Row 2: Special Orbs */}
        <div className="currency-row special-row">
          <div className="currency-row-label">Special</div>
          <div className="currency-icons-row">
            {['Orb of Alchemy', 'Vaal Orb', 'Orb of Annulment', 'Orb of Fracturing', 'Divine Orb'].map((currency) => {
              const isImplemented = categorizedCurrencies.orbs.implemented.includes(currency)
              const isAvailable = availableCurrencies.includes(currency) && isImplemented
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
            })}
          </div>
        </div>

        {/* Row 3: Basic Orbs - Organized by Family */}
        <div className="currency-row orbs-row">
          <div className="currency-row-label">Orbs</div>
          <div className="currency-icons-row">
            {[
              ['Orb of Transmutation', 'Greater Orb of Transmutation', 'Perfect Orb of Transmutation'],
              ['Orb of Augmentation', 'Greater Orb of Augmentation', 'Perfect Orb of Augmentation'],
              ['Regal Orb', 'Greater Regal Orb', 'Perfect Regal Orb'],
              ['Chaos Orb', 'Greater Chaos Orb', 'Perfect Chaos Orb'],
              ['Exalted Orb', 'Greater Exalted Orb', 'Perfect Exalted Orb']
            ].map((family, familyIndex) => (
              <div key={familyIndex} className="currency-family">
                {family.map((currency) => {
                  const isImplemented = categorizedCurrencies.orbs.implemented.includes(currency)
                  const isAvailable = availableCurrencies.includes(currency) && isImplemented
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
                })}
              </div>
            ))}
          </div>
        </div>

        {/* Row 4: Omens - Compact Grid */}
        {availableOmens.length > 0 && (
          <div className="currency-row omens-row">
            <div className="currency-row-label">Omens</div>
            <div className="currency-icons-row omens-grid">
              {[
                'Omen of Greater Exaltation', 'Omen of Sinistral Exaltation', 'Omen of Dextral Exaltation',
                'Omen of Homogenising Exaltation', 'Omen of Catalysing Exaltation',
                'Omen of Sinistral Coronation', 'Omen of Dextral Coronation', 'Omen of Homogenising Coronation',
                'Omen of Whittling', 'Omen of Sinistral Erasure', 'Omen of Dextral Erasure',
                'Omen of Greater Annulment', 'Omen of Sinistral Annulment', 'Omen of Dextral Annulment',
                'Omen of Sinistral Alchemy', 'Omen of Dextral Alchemy', 'Omen of Corruption'
              ].filter(omen => availableOmens.includes(omen)).map((omen) => {
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

        {/* Row 5: Essences - Wider layout with corrupted essences */}
        <div className="currency-row essences-row">
          <div className="currency-row-label">Essences</div>
          <div className="essences-content">
            {/* Essences Section */}
            <div className="essences-section">
            <div className="essence-grid-clean">
              {(() => {
                // Group essences by type
                const groupedEssences: Record<string, { base: string[], perfect: string[] }> = {}
                const allEssences = [...categorizedCurrencies.essences.implemented, ...categorizedCurrencies.essences.disabled]

                allEssences.forEach(essence => {
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
                  else baseType = 'Other'

                  if (!groupedEssences[baseType]) {
                    groupedEssences[baseType] = { base: [], perfect: [] }
                  }

                  if (essence.includes('Perfect')) {
                    groupedEssences[baseType].perfect.push(essence)
                  } else {
                    groupedEssences[baseType].base.push(essence)
                  }
                })

                const allEssenceTypes = [
                  'Flames', 'Ice', 'Electricity', 'Abrasion', 'Sorcery',
                  'the Body', 'the Mind', 'Haste', 'Enhancement', 'Battle',
                  'Insulation', 'Thawing', 'Grounding', 'Command', 'Ruin',
                  'the Infinite', 'Alacrity', 'Seeking', 'Opulence'
                ]

                // Handle corrupted essences separately
                const corruptedEssences = [
                  'Essence of Delirium', 'Essence of Horror', 'Essence of Hysteria', 'Essence of Insanity', 'Essence of the Abyss'
                ]

                const normalEssencePairs = allEssenceTypes.map((baseType) => {
                  const group = groupedEssences[baseType]
                  if (!group || (group.base.length === 0 && group.perfect.length === 0)) return null

                  return (
                    <div key={baseType} className="essence-pair">
                      {/* Base essence group */}
                      {group.base.length > 0 && (
                        <Tooltip
                          content={
                            <CurrencyTooltipWrapper
                              currencyName={group.base[group.base.length - 1]}
                              additionalMechanics={
                                !availableCurrencies.includes(group.base[group.base.length - 1])
                                  ? "Not available for this item"
                                  : "Double-click to apply"
                              }
                            />
                          }
                          delay={0}
                          position="right"
                        >
                          <div
                            className={`currency-slot essence-base ${!availableCurrencies.includes(group.base[group.base.length - 1]) ? 'currency-disabled' : ''}`}
                            onClick={() => availableCurrencies.includes(group.base[group.base.length - 1]) && handleCraft(group.base[group.base.length - 1])}
                          >
                            <img
                              src={getCurrencyIconUrl(group.base[0])}
                              alt={`Essence of ${baseType}`}
                              className="currency-icon"
                              onError={(e) => {
                                (e.target as HTMLImageElement).src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
                              }}
                            />
                          </div>
                        </Tooltip>
                      )}
                      {/* Perfect essence */}
                      {group.perfect.length > 0 && (
                        <Tooltip
                          content={
                            <CurrencyTooltipWrapper
                              currencyName={group.perfect[0]}
                              additionalMechanics={
                                !availableCurrencies.includes(group.perfect[0])
                                  ? "Not available for this item"
                                  : "Double-click to apply"
                              }
                            />
                          }
                          delay={0}
                          position="right"
                        >
                          <div
                            className={`currency-slot essence-perfect ${!availableCurrencies.includes(group.perfect[0]) ? 'currency-disabled' : ''}`}
                            onClick={() => availableCurrencies.includes(group.perfect[0]) && handleCraft(group.perfect[0])}
                          >
                            <img
                              src={getCurrencyIconUrl(group.perfect[0])}
                              alt={`Perfect Essence of ${baseType}`}
                              className="currency-icon"
                              onError={(e) => {
                                (e.target as HTMLImageElement).src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
                              }}
                            />
                          </div>
                        </Tooltip>
                      )}
                    </div>
                  )
                }).filter(Boolean)

                // Add corrupted essences
                const corruptedEssencePairs = corruptedEssences.filter(essence =>
                  categorizedCurrencies.essences.implemented.includes(essence) || categorizedCurrencies.essences.disabled.includes(essence)
                ).map((essence) => {
                  const isImplemented = categorizedCurrencies.essences.implemented.includes(essence)
                  const isAvailable = availableCurrencies.includes(essence) && isImplemented
                  const additionalMechanics = !isImplemented
                    ? "Not implemented yet"
                    : isAvailable
                      ? "Double-click to apply"
                      : "Not available for this item"

                  return (
                    <div key={essence} className="essence-pair corrupted">
                      <Tooltip
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
                    </div>
                  )
                })

                return [...normalEssencePairs, ...corruptedEssencePairs]
              })()}
            </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}