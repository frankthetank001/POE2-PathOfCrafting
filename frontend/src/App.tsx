import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import GridCraftingSimulator from './pages/GridCraftingSimulator'
import CraftLibrary from './pages/CraftLibrary'
import CraftDetail from './pages/CraftDetail'
import PopularBuilds from './pages/PopularBuilds'
import AdminLogin from './pages/AdminLogin'
import AdminDashboard from './pages/AdminDashboard'
import { VersionProvider, useGameVersion, GameVersion } from './contexts/VersionContext'
import { AdminProvider } from './contexts/AdminContext'
import './App.css'

// Version injected at build time from git tags
declare const __APP_VERSION__: string

// Patch notes for each version (changes from previous version)
const PATCH_NOTES: Record<GameVersion, { title: string; changes: string[] }> = {
  '0.5': {
    title: 'Patch 0.5 Changes (Runes of Aldur)',
    changes: [
      'Removed: Omen of Recombination',
      'Removed: Omen of Corruption',
      'Crafted modifiers: max 1 per item',
      'Desecrated modifiers: max 1 per item',
      'Essences: only 1 essence modifier per item',
      'Added: Verisium Runeforging + new runes',
    ],
  },
  '0.4': {
    title: 'Patch 0.4 Changes',
    changes: [
      'Removed: Omen of Homogenising Exaltation',
      'Removed: Omen of Homogenising Coronation',
    ],
  },
  '0.3': {
    title: 'Patch 0.3 (Baseline)',
    changes: [
      'Initial crafting system',
      'All Homogenising Omens available',
    ],
  },
}

function Navigation() {
  const location = useLocation()
  const { gameVersion, setGameVersion } = useGameVersion()
  const [showPatchNotes, setShowPatchNotes] = useState(false)

  return (
    <nav className="nav">
      <div className="nav-container">
        <h1 className="nav-title">POE2 - Path of Crafting (beta) <span style={{ fontSize: '0.6em', opacity: 0.7 }}>v{__APP_VERSION__}</span></h1>
        <div className="nav-links">
          <Link to="/" className={`nav-link ${location.pathname === '/' ? 'nav-link-active' : ''}`}>
            Crafting Simulator
          </Link>
          <Link to="/crafts" className={`nav-link ${location.pathname.startsWith('/craft') ? 'nav-link-active' : ''}`}>
            Craft Library
          </Link>
          <Link to="/builds" className={`nav-link ${location.pathname.startsWith('/builds') ? 'nav-link-active' : ''}`}>
            Popular Builds
          </Link>
          <div className="version-selector">
            <select
              className="version-select"
              value={gameVersion}
              onChange={(e) => setGameVersion(e.target.value as GameVersion)}
              title="Select PoE2 patch version"
            >
              <option value="0.5">Patch 0.5</option>
              <option value="0.4">Patch 0.4</option>
              <option value="0.3">Patch 0.3</option>
            </select>
            <button
              className="version-info-btn"
              onClick={() => setShowPatchNotes(!showPatchNotes)}
              title="View patch changes"
            >
              i
            </button>
            {showPatchNotes && (
              <div className="patch-notes-popup">
                <div className="patch-notes-header">
                  {PATCH_NOTES[gameVersion].title}
                  <button
                    className="patch-notes-close"
                    onClick={() => setShowPatchNotes(false)}
                  >
                    x
                  </button>
                </div>
                <ul className="patch-notes-list">
                  {PATCH_NOTES[gameVersion].changes.map((change, i) => (
                    <li key={i}>{change}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}

function App() {
  return (
    <VersionProvider>
      <AdminProvider>
        <Router>
          <Routes>
            {/* Admin routes - no main navigation */}
            <Route path="/admin/login" element={<AdminLogin />} />
            <Route path="/admin" element={<AdminDashboard />} />

            {/* Main app routes */}
            <Route path="/*" element={
              <div className="app">
                <Navigation />
                <main className="main">
                  <Routes>
                    <Route path="/" element={<GridCraftingSimulator />} />
                    <Route path="/crafts" element={<CraftLibrary />} />
                    <Route path="/craft/:shortId" element={<CraftDetail />} />
                    <Route path="/builds" element={<PopularBuilds />} />
                  </Routes>
                </main>
              </div>
            } />
          </Routes>
        </Router>
      </AdminProvider>
    </VersionProvider>
  )
}

export default App