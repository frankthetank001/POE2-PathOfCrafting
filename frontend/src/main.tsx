import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'

// PoE2 Fonts and Theme
import './assets/fonts.css'
import './assets/poe2-theme.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)