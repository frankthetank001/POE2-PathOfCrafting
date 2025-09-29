import React from 'react'
import { useCurrencyTooltip } from '@/hooks/useCurrencyTooltip'
import { CurrencyTooltip } from './Tooltip'

interface CurrencyTooltipWrapperProps {
  currencyName: string
  additionalMechanics?: string
}

export const CurrencyTooltipWrapper: React.FC<CurrencyTooltipWrapperProps> = ({
  currencyName,
  additionalMechanics
}) => {
  const { tooltipData, loading } = useCurrencyTooltip(currencyName)

  if (loading || !tooltipData) {
    return <CurrencyTooltip name={currencyName} description="Loading..." />
  }

  // Combine mechanics if additional mechanics are provided
  const combinedMechanics = additionalMechanics
    ? tooltipData.mechanics
      ? `${tooltipData.mechanics}\n\n${additionalMechanics}`
      : additionalMechanics
    : tooltipData.mechanics

  return (
    <CurrencyTooltip
      name={tooltipData.name}
      description={tooltipData.description}
      mechanics={combinedMechanics}
    />
  )
}