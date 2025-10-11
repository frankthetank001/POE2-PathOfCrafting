import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import BuildBrowser from './pages/BuildBrowser'
import GridCraftingSimulator from './pages/GridCraftingSimulator'
import './App.css'

// Version injected at build time from git tags
declare const __APP_VERSION__: string

function Navigation() {
  const location = useLocation()

  return (
    <nav className="nav">
      <div className="nav-container">
        <h1 className="nav-title">POE2 - Path of Crafting (beta) <span style={{ fontSize: '0.6em', opacity: 0.7 }}>v{__APP_VERSION__}</span></h1>
        <div className="nav-links">
          <Link to="/" className={`nav-link ${location.pathname === '/' ? 'nav-link-active' : ''}`}>
            Crafting Simulator
          </Link>
          <span className="nav-link-disabled" title="Coming soon">Build Browser</span>
        </div>
      </div>
    </nav>
  )
}

function App() {
  return (
    <Router>
      <div className="app">
        <Navigation />

        <main className="main">
          <Routes>
            <Route path="/" element={<GridCraftingSimulator />} />
            <Route path="/builds" element={<BuildBrowser />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App