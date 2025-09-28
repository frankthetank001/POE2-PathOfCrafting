import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import ItemParser from './pages/ItemParser'
import BuildBrowser from './pages/BuildBrowser'
import CraftingSimulator from './pages/CraftingSimulator'
import GridCraftingSimulator from './pages/GridCraftingSimulator'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="nav">
          <div className="nav-container">
            <h1 className="nav-title">PoE2 AI TradeCraft</h1>
            <div className="nav-links">
              <Link to="/" className="nav-link">Crafting Simulator</Link>
              <Link to="/grid" className="nav-link">Grid Layout</Link>
              <Link to="/parser" className="nav-link">Item Parser</Link>
              <Link to="/builds" className="nav-link">Build Browser</Link>
            </div>
          </div>
        </nav>

        <main className="main">
          <Routes>
            <Route path="/" element={<CraftingSimulator />} />
            <Route path="/grid" element={<GridCraftingSimulator />} />
            <Route path="/parser" element={<ItemParser />} />
            <Route path="/builds" element={<BuildBrowser />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App