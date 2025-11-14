import React, { useState } from 'react'
import HotspotDashboard from './pages/HotspotDashboard'
import GovernanceView from './pages/GovernanceView'

function App() {
  const [currentView, setCurrentView] = useState('dashboard')

  return (
    <div className="app">
      <header className="header">
        <h1>Risk Intelligence Platform</h1>
        <p>Violent Extremism Hotspot Prediction with Privacy & Civil Rights Guardrails</p>
        <nav className="nav">
          <button
            className={currentView === 'dashboard' ? 'active' : ''}
            onClick={() => setCurrentView('dashboard')}
          >
            Hotspot Dashboard
          </button>
          <button
            className={currentView === 'governance' ? 'active' : ''}
            onClick={() => setCurrentView('governance')}
          >
            Governance
          </button>
        </nav>
      </header>
      
      <main className="main-content">
        {currentView === 'dashboard' && <HotspotDashboard />}
        {currentView === 'governance' && <GovernanceView />}
      </main>
    </div>
  )
}

export default App

