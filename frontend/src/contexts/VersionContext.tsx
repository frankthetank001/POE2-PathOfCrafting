import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'

export type GameVersion = '0.3' | '0.4'

interface VersionContextType {
  gameVersion: GameVersion
  setGameVersion: (version: GameVersion) => void
}

const VersionContext = createContext<VersionContextType | undefined>(undefined)

const STORAGE_KEY = 'poe2-game-version'

export function VersionProvider({ children }: { children: ReactNode }) {
  const [gameVersion, setGameVersion] = useState<GameVersion>(() => {
    // Load from localStorage on init, default to latest version
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === '0.3' || stored === '0.4') {
      return stored
    }
    return '0.4'  // Default to latest version
  })

  useEffect(() => {
    // Persist to localStorage when changed
    localStorage.setItem(STORAGE_KEY, gameVersion)
  }, [gameVersion])

  return (
    <VersionContext.Provider value={{ gameVersion, setGameVersion }}>
      {children}
    </VersionContext.Provider>
  )
}

export function useGameVersion() {
  const context = useContext(VersionContext)
  if (context === undefined) {
    throw new Error('useGameVersion must be used within a VersionProvider')
  }
  return context
}

// Helper to check if a feature is available in current version
export function isFeatureAvailable(feature: string, version: GameVersion): boolean {
  const removedIn04 = [
    'Omen of Homogenising Exaltation',
    'Omen of Homogenising Coronation',
  ]

  if (version === '0.4' && removedIn04.includes(feature)) {
    return false
  }

  return true
}
